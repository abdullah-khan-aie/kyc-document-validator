import logging
from typing import Callable, Dict, Optional, Awaitable, Any
from app.db import get_supabase
from fastapi.encoders import jsonable_encoder

from app.extractors import (
    extract_bank_statements_from_text,
    extract_emirates_id_from_text,
    extract_passport_from_text,
    extract_salary_certificate_from_text,
    extract_visa_from_text,
    extract_pay_slips_from_text,
    extract_ejari_from_text,
    extract_national_id_from_text,
    extract_proof_of_address_from_text,

)
from app.models.case import CaseData
from app.models.docs import (
    BankStatementsData,
    EmiratesIdData,
    PassportData,
    SalaryCertificateData,
    VisaData,
    PaySlipsData,
    EjariData,
    NationalIdData,
    ProofOfAddressData
)
from app.models import InfoSheet
from app.ocr import extract_text_from_pdf
from app.validation import generate_case_validation_report, generate_document_validation_report
from app.core import observe, get_langfuse
from app.schemas import CrossDocumentsRequest
from pydantic import BaseModel
from app.core import get_settings

logger = logging.getLogger(__name__)

Extractor = Callable[[str, Optional[str]], Awaitable[object]]

DOCS = {
    "visa": VisaData,
    "passport": PassportData,
    "emirates_id": EmiratesIdData,
    "salary_certificate": SalaryCertificateData,
    "bank_statements": BankStatementsData,
    "payslips": PaySlipsData,
    "ejari": EjariData,
    "national_id": NationalIdData,
    "proof_of_address": ProofOfAddressData,
}

DOCUMENTS: Dict[str, Extractor] = {
    "passport": extract_passport_from_text,
    "visa": extract_visa_from_text,
    "emirates_id": extract_emirates_id_from_text,
    "salary_certificate": extract_salary_certificate_from_text,
    "bank_statements": extract_bank_statements_from_text,
    "payslips": extract_pay_slips_from_text,
    "ejari": extract_ejari_from_text,
    "national_id": extract_national_id_from_text,
    "proof_of_address": extract_proof_of_address_from_text,
}


async def _persist_raw_text(document_id: str, doc_name: str, text: str) -> None:
    """Save the raw OCR text as a JSON."""
    get_supabase().table('documents').update({
        'ocr_text': text
    }).eq('id', document_id).execute()


async def _persist_llm_response(document_id: str, doc_name: str, data: object) -> None:
    """Save the structured Pydantic model as a JSON."""
    if not isinstance(data, DOCS[doc_name]):
        return
    get_supabase().table('documents').update({
        'llm_response': jsonable_encoder(data)
    }).eq('id', document_id).execute()


async def _safe_extract(
        file_path: str,
        extractor: Extractor,
        document_id: str,
        doc_name: str,
        comments: Optional[str] = None
) -> tuple[object, dict]:
    text, page_count = await extract_text_from_pdf(file_path)

    if not text or not text.strip():
        raise ValueError("""We were unable to read the content of this document. 
                          Please ensure the file is clear and contains readable text.""")


    await _persist_raw_text(
        document_id=document_id,
        doc_name=doc_name,
        text=text
    )

    data, token_usage = await extractor(text, comments)
    await _persist_llm_response(
        document_id=document_id,
        doc_name=doc_name,
        data=data
    )

    metrics = {
        "ocr_pages": page_count,
        "llm_tokens": token_usage  # {'prompt_tokens': 100, 'completion_tokens': 50}
    }
    return data, metrics


def _create_case_data(
        extracted_docs: Dict[str, object],
        profile_type: Dict
) -> CaseData:
    """ Create a CaseData object from the extracted data """
    return CaseData(
        passport=extracted_docs.get("passport") if isinstance(extracted_docs.get("passport"), PassportData) else None,
        visa=extracted_docs.get("visa") if isinstance(extracted_docs.get("visa"), VisaData) else None,
        emirates_id=extracted_docs.get("emirates_id") if isinstance(extracted_docs.get("emirates_id"),
                                                                    EmiratesIdData) else None,
        salary_certificate=extracted_docs.get("salary_certificate") if isinstance(
            extracted_docs.get("salary_certificate"), SalaryCertificateData) else None,
        bank_statements=extracted_docs.get("bank_statements") if isinstance(extracted_docs.get("bank_statements"),
                                                                            BankStatementsData) else None,
        pay_slips=extracted_docs.get("payslips") if isinstance(extracted_docs.get("payslips"),
                                                                PaySlipsData) else None,
        ejari=extracted_docs.get("ejari") if isinstance(extracted_docs.get("ejari"), EjariData) else None,
        national_id=extracted_docs.get("national_id") if isinstance(extracted_docs.get("national_id"),NationalIdData) else None,
        proof_of_address=extracted_docs.get("proof_of_address") if isinstance(extracted_docs.get("proof_of_address"),ProofOfAddressData) else None,
        residency=profile_type['residency'],
        employment=profile_type['employment'],
    )

async def process_single_document(
        file_path: str,
        doc_name: str,
        document_id: str,
        profile_type: Dict,
        comments: Optional[str] = None) -> tuple[CaseData, Dict[str, str], dict]:

    """Process a single document in the pipeline."""

    extracted_docs: Dict[str, object] = {}
    extraction_errors: Dict[str, str] = {}
    metrics: dict = {}


    extractor = DOCUMENTS.get(doc_name)

    if not extractor:
        extraction_errors[doc_name] = (
            f"The document category '{doc_name}' is not recognized by our system. "
            "Please verify the document type."
        )
        return _create_case_data(extracted_docs, profile_type), extraction_errors, {}

    if not file_path:
        extraction_errors[doc_name] = (
        f"We could not locate the file uploaded for '{doc_name}'." 
        "Please try uploading the document again."
        )
    else:
        try:
            extracted_docs[doc_name], metrics = await _safe_extract(
                file_path=file_path,
                extractor=extractor,
                document_id=document_id,
                doc_name=doc_name,
                comments=comments
            )
        # This captures the message from _safe_extract
        except ValueError as exc:
            extraction_errors[doc_name] = str(exc)
        except Exception:
            extraction_errors[doc_name] = """
            An unexpected error occurred while processing this document. 
            Please contact support if the issue persists.
            """

    return _create_case_data(extracted_docs, profile_type), extraction_errors, metrics


def map_documents_to_application(docs: Dict[str, object], customer_name: str, mobile_number: str, email: str) -> InfoSheet:
    form = InfoSheet()

    # --- Passport Mapping ---
    passport = docs.get("passport")

    form.fullName = customer_name.lower()
    form.mobileNumber = mobile_number
    form.email = email.lower()

    if isinstance(passport, PassportData):
        form.gender = passport.gender if passport.gender else None
        if hasattr(passport, 'country') and hasattr(passport.country, 'short_name'):
            form.passportIssuingCountry = passport.country.short_name.lower() if passport.country else None

    # --- Visa Mapping ---
    visa = docs.get("visa")

    if isinstance(visa, VisaData):
        form.uaeResidencyStartDate = str(visa.issue_date) if visa.issue_date else None

    # --- Emirates ID Mapping ---
    eid = docs.get("emirates_id")

    if isinstance(eid, EmiratesIdData):
        form.statusInUAE = eid.status.lower() if eid.status else None

    # --- Salary Certificate Mapping ---
    salary = docs.get("salary_certificate")

    if isinstance(salary, SalaryCertificateData):
        form.companyName = salary.company_name.lower() if salary.company_name else None
        form.jobTitle = salary.position.lower() if salary.position else None
        form.employmentType = salary.employment_type.lower() if salary.employment_type else None
        form.companyIndustry = salary.industry.lower() if salary.industry else None
        form.companyWebsite = salary.website.lower() if salary.website else None
        form.monthlySalary = float(salary.gross_monthly_income) if salary.gross_monthly_income else None
        form.officeLandlineNumber = salary.landline_number.lower() if salary.landline_number else None
        form.hrEmail= salary.company_email.lower() if salary.company_email else None

    return form


async def process_documents(payload: CrossDocumentsRequest):
    read_docs: Dict[str, BaseModel] = {}
    extraction_errors: Dict[str, str] = {}
    for doc in payload.documents:
        if DOCS.get(doc.document_type) is not None and doc.llm_response is not None:
            read_docs[doc.document_type] = DOCS[doc.document_type].model_validate(doc.llm_response)
            read_docs[doc.document_type].document_id = doc.document_version_id
        elif doc.llm_response is not None:
            extraction_errors[doc.document_type] = (
                f"The document category '{doc.document_type}' is not recognized by our system. "
                "Please verify the document type."
            )

    report = generate_case_validation_report(_create_case_data(read_docs, profile_type={'residency': payload.residency, 'employment': payload.employment}))
    if extraction_errors:
        report['extraction_errors'] = extraction_errors

    (get_supabase()
     .table('applications')
     .update({
        "application_feedback": jsonable_encoder(report),
        "info_sheet":jsonable_encoder(map_documents_to_application(read_docs, payload.customer_name, payload.mobile_number, payload.email))
    })
     .eq("id", payload.application_id)
     .execute())

    return report

@observe()
async def run_pipeline(
        doc_name: str,
        file_path: str,
        document_id: str,
        name: str,
        profile_type: Dict,
        comments: Optional[str] = None
) -> dict[str, Any]:

    case, extraction_errors, metrics = await process_single_document(
        document_id=document_id,
        file_path=file_path,
        doc_name=doc_name,
        comments=comments,
        profile_type=profile_type,
    )

    get_langfuse().update_current_span(name=doc_name)
    report, document_span_id = generate_document_validation_report(case, name)

    report['span_id'] = document_span_id

    if extraction_errors:
        report["extraction_errors"] = extraction_errors

    if metrics:
        report["_meta"] = {
            "cost": (metrics["ocr_pages"]*get_settings().ocr_cost_per_page)
                    +
                    (metrics['llm_tokens']['prompt_tokens'] * get_settings().gpt_cost_input_per_token)
                    +
                    (metrics['llm_tokens']['completion_tokens'] * get_settings().gpt_cost_output_per_token)
            ,
            "usage": metrics
        }

    (get_supabase().table('documents')
     .update({
        "doc_feedback": jsonable_encoder(report),
    })
     .eq("id", document_id)
     .execute())

    return report
