from typing import Any, Callable, Dict, List

from app.models.case import CaseData
from app.core import get_langfuse

from .cross_rules import get_cross_document_rules
from .doc_rules import (
    ValidationIssue,
    ensure_document_present,
    validate_bank_statements,
    validate_emirates_id,
    validate_passport,
    validate_salary_certificate,
    validate_visa,
    validate_payslips,
    validate_ejari,
    validate_national_id,
    validate_proof_of_address,
)


DocumentValidator = Callable[..., List[ValidationIssue]]


GCC_NATIONALITIES = {
    "united arab emirates",
    "uae",
    "saudi arabia",
    "kingdom of saudi arabia",
    "kuwait",
    "bahrain",
    "oman",
    "sultanate of oman",
    "qatar",
}

def _document_required(case: CaseData, doc_name: str) -> bool:
    normalized_residency = (case.residency or "").strip().lower()
    if normalized_residency == "resident":
        if doc_name in {"passport", "visa", "emirates_id", "bank_statements", "salary_certificate", "pay_slips"}:
            return True
    elif normalized_residency == "non-resident":
        if doc_name in {"passport", "national_id", "bank_statements", "salary_certificate", "pay_slips"}:
            return True
    return False


def run_document_validations(case: CaseData, name) -> Dict[str, List[ValidationIssue]]:
    validators: Dict[str, DocumentValidator] = {
        "passport": validate_passport,
        "visa": validate_visa,
        "emirates_id": validate_emirates_id,
        "salary_certificate": validate_salary_certificate,
        "bank_statements": lambda bank, n: validate_bank_statements(bank, case.residency, case.employment, n),
        "pay_slips": validate_payslips,
        "ejari": validate_ejari,
        "national_id": validate_national_id,
        "proof_of_address": validate_proof_of_address,
    }

    results: Dict[str, List[ValidationIssue]] = {}
    for doc_name, validator in validators.items():
        doc_value = getattr(case, doc_name)
        issues: List[ValidationIssue] = []
        if doc_value is not None:
            issues.extend(validator(doc_value, name))
            results[doc_name] = issues
    return results

def run_cross_document_validation(case: CaseData) -> List[ValidationIssue]:
    all_issues: List[ValidationIssue] = []
    for doc_name in case.__pydantic_fields__.keys():
        doc_value = getattr(case, doc_name)
        required = _document_required(case, doc_name)
        all_issues.extend(ensure_document_present(doc_value, doc_name, required)) # Passport is missing
    for rule in get_cross_document_rules((case.residency, case.employment)):
        all_issues.extend(rule(case))
    return all_issues

def generate_document_validation_report(case: CaseData, name) -> Dict[str, Any]:
    document_issues = run_document_validations(case, name)
    documents_section: Dict[str, Any] = {}
    for doc_name, issues in document_issues.items():
        doc_value = getattr(case, doc_name)
        get_langfuse().score_current_span(
            name=f"AI : {doc_name}", value="PASSED" if not issues else "FAILED"
        )
        documents_section[doc_name] = {
            "extracted_data": doc_value.model_dump() if doc_value else None,
            "issues": [issue.model_dump() for issue in issues],
            "status": "PASSED" if not issues else "FAILED",
        }
    return {
        "case_context": {
            "residency": case.residency,
            "employment": case.employment,
        },
        "documents": documents_section,
    }, get_langfuse().get_current_observation_id()



def generate_case_validation_report(case: CaseData) -> Dict[str, Any]:
    cross_doc_issues = run_cross_document_validation(case)
    return {
        "case_context": {
            "residency": case.residency,
            "employment": case.employment,
        },
        "cross_document_issues": [issue.model_dump() for issue in cross_doc_issues],
    }
