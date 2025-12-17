# app/models/case.py
from typing import Optional
from pydantic import BaseModel
from .docs import (
    PassportData,
    VisaData,
    EmiratesIdData,
    SalaryCertificateData,
    BankStatementsData,
    PaySlipsData,
    EjariData,
    NationalIdData,
    ProofOfAddressData
)


class CaseData(BaseModel):
    passport: Optional[PassportData] = None
    visa: Optional[VisaData] = None
    emirates_id: Optional[EmiratesIdData] = None
    salary_certificate: Optional[SalaryCertificateData] = None
    bank_statements: Optional[BankStatementsData] = None
    pay_slips: Optional[PaySlipsData] = None
    ejari: Optional[EjariData] = None
    national_id: Optional[NationalIdData] = None
    proof_of_address: Optional[ProofOfAddressData] = None

    residency: Optional[str] = None   # "Resident" / "Non-Resident"
    employment: Optional[str] = None  # "Salaried" / "Self-Employed"
