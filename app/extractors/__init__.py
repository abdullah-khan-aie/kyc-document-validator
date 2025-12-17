from .passport_extractor import extract_passport_from_text
from .visa_extractor import extract_visa_from_text
from .emirates_id_extractor import extract_emirates_id_from_text
from .salary_certificate_extractor import extract_salary_certificate_from_text
from .bank_statements_extractor import extract_bank_statements_from_text
from .pay_slips_extractor import extract_pay_slips_from_text
from .ejari_extractor import extract_ejari_from_text
from .national_id_extractor import extract_national_id_from_text
from .proof_of_address_extractor import extract_proof_of_address_from_text

__all__ = [
    "extract_passport_from_text",
    "extract_visa_from_text",
    "extract_emirates_id_from_text",
    "extract_salary_certificate_from_text",
    "extract_bank_statements_from_text",
    "extract_pay_slips_from_text",
    "extract_ejari_from_text",
    "extract_national_id_from_text",
    "extract_proof_of_address_from_text"
]
