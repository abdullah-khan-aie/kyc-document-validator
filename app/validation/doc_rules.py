from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel
from rapidfuzz import fuzz

from app.models.docs import (
    BankStatementsData,
    EjariData,
    EmiratesIdData,
    NationalIdData,
    PassportData,
    PaySlipsData,
    ProofOfAddressData,
    SalaryCertificateData,
    VisaData,
)


class ValidationIssue(BaseModel):
    rule_id: str
    severity: Literal["error", "warning"]
    message: str
    details: Dict[str, Any] = {}


def _issue(rule_id: str, message: str, severity: Literal["error", "warning"], **details: Any) -> ValidationIssue:
    return ValidationIssue(rule_id=rule_id, severity=severity, message=message, details=details)


def _text_missing(value: Optional[str]) -> bool:
    return value is None or not value.strip()


def _normalize_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    return value.strip().lower()


def ensure_document_present(
    doc: Optional[BaseModel],
    doc_name: str,
    required: bool,
) -> List[ValidationIssue]:
    if required and doc is None:
        return [
            _issue(
                rule_id=f"{doc_name}_missing",
                severity="error",
                message=f"{doc_name.replace('_', ' ').title()} is required but was not provided.",
            )
        ]
    return []


def validate_passport(passport: PassportData, name) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    today = date.today()

    if passport.is_passport:
        if _text_missing(passport.full_name):
            issues.append(
                _issue(
                    rule_id="missing_full_name",
                    severity="error",
                    message="Full name missing",
                )
            )
        elif (
            passport.full_name
            and name
            and fuzz.token_set_ratio(_normalize_text(name), _normalize_text(passport.full_name)) <= 90
        ):
            issues.append(
                _issue(rule_id="name_invalid", severity="error", message=f"This passport does not belong to {name}")
            )
            return issues

        if _text_missing(passport.passport_number):
            issues.append(
                _issue(
                    rule_id="missing_doc_number",
                    severity="error",
                    message="Passport number missing",
                )
            )

        if _text_missing(passport.issue_place):
            issues.append(
                _issue(
                    rule_id="missing_issue_place",
                    severity="error",
                    message="Place of issue missing",
                )
            )

        if _text_missing(passport.gender):
            issues.append(
                _issue(
                    rule_id="missing_gender",
                    severity="error",
                    message="Gender not specified",
                )
            )

        if not passport.country:
            issues.append(
                _issue(
                    rule_id="missing_country",
                    severity="error",
                    message="Country is missing",
                )
            )

        if passport.expiry_date and passport.expiry_date < today:
            issues.append(
                _issue(
                    rule_id="doc_expired",
                    severity="error",
                    message="Passport is expired",
                    passport_expiry=str(passport.expiry_date),
                )
            )

        if passport.issue_date and passport.issue_date >= passport.expiry_date:
            issues.append(
                _issue(
                    rule_id="invalid_date_range",
                    severity="error",
                    message="Issue date cannot be after expiry date",
                    issue_date=str(passport.issue_date),
                    expiry_date=str(passport.expiry_date),
                )
            )

        if passport.date_of_birth and passport.date_of_birth >= today:
            issues.append(
                _issue(
                    rule_id="invalid_dob",
                    severity="error",
                    message="Date of birth is in the future",
                    passport_dob=str(passport.date_of_birth),
                )
            )

        if passport.age and passport.age < 21:
            issues.append(
                _issue(
                    rule_id="age_restriction",
                    severity="error",
                    message="Holder is under 21 years old",
                    passport_age=str(passport.age),
                )
            )
    else:
        issues.append(
            _issue(
                rule_id="invalid_doc_type",
                severity="error",
                message="The document type is invalid",
            )
        )

    return issues


def validate_visa(visa: VisaData, name) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    today = date.today()

    if visa.is_visa:
        if _text_missing(visa.full_name):
            issues.append(_issue(rule_id="visa_full_name_missing", severity="error", message="Full name missing"))
        elif (
            visa.full_name
            and name
            and fuzz.token_set_ratio(_normalize_text(visa.full_name), _normalize_text(name)) <= 90
        ):
            issues.append(
                _issue(rule_id="name_invalid", severity="error", message=f"This visa does not belong to {name}")
            )
            return issues

        if _text_missing(visa.visa_number):
            issues.append(_issue(rule_id="visa_number_missing", severity="error", message="Visa number missing"))

        if not visa.issue_date:
            issues.append(_issue(rule_id="visa_issue_date_missing", severity="error", message="Issue date missing"))

        if _text_missing(visa.place_of_issue):
            issues.append(
                _issue(rule_id="visa_place_of_issue_missing", severity="error", message="Place of issue missing")
            )

        if _text_missing(visa.passport_number_on_visa):
            issues.append(
                _issue(
                    rule_id="visa_passport_number_missing",
                    severity="error",
                    message="Passport reference number missing",
                )
            )

        if visa.expiry_date and visa.expiry_date < today:
            issues.append(
                _issue(
                    rule_id="visa_expired",
                    severity="error",
                    message="Visa is expired",
                    visa_expiry=str(visa.expiry_date),
                )
            )

        if visa.issue_date and visa.issue_date >= visa.expiry_date:
            issues.append(
                _issue(
                    rule_id="visa_issue_after_expiry",
                    severity="error",
                    message="Issue date is after expiry date",
                    issue_date=str(visa.issue_date),
                    expiry_date=str(visa.expiry_date),
                )
            )
    else:
        issues.append(
            _issue(
                rule_id="invalid_doc_type",
                severity="error",
                message="The document type is invalid",
            )
        )

    return issues


def validate_emirates_id(emirates_id: EmiratesIdData, name) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    today = date.today()

    if emirates_id.is_emirates_id:
        if _text_missing(emirates_id.full_name):
            issues.append(
                _issue(
                    rule_id="emirates_id_full_name_missing",
                    severity="error",
                    message="Full name missing",
                )
            )

        elif (
            emirates_id.full_name
            and name
            and fuzz.token_set_ratio(_normalize_text(emirates_id.full_name), _normalize_text(name)) <= 90
        ):
            issues.append(
                _issue(rule_id="name_invalid", severity="error", message=f"This emirates id does not belong to {name}")
            )
            return issues

        if _text_missing(emirates_id.emirates_id_number):
            issues.append(
                _issue(
                    rule_id="emirates_id_number_missing",
                    severity="error",
                    message="Emirates ID number missing",
                )
            )

        if _text_missing(emirates_id.nationality):
            issues.append(
                _issue(
                    rule_id="emirates_id_nationality_missing",
                    severity="error",
                    message="Nationality missing",
                )
            )

        if emirates_id.issue_date is None:
            issues.append(
                _issue(
                    rule_id="emirates_id_issue_date_missing",
                    severity="error",
                    message="Issue date missing",
                )
            )

        if _text_missing(emirates_id.place_of_issue):
            issues.append(
                _issue(
                    rule_id="emirates_id_place_of_issue_missing",
                    severity="warning",
                    message="Place of issue missing",
                )
            )

        if _text_missing(emirates_id.employer_name):
            issues.append(
                _issue(
                    rule_id="emirates_id_employer_missing",
                    severity="warning",
                    message="Employer name missing",
                )
            )

        if emirates_id.expiry_date and emirates_id.expiry_date < today:
            issues.append(
                _issue(
                    rule_id="emirates_id_expired",
                    severity="error",
                    message="Emirates ID is expired",
                    emirates_id_expiry=str(emirates_id.expiry_date),
                )
            )

        if emirates_id.issue_date and emirates_id.issue_date >= emirates_id.expiry_date:
            issues.append(
                _issue(
                    rule_id="emirates_id_issue_after_expiry",
                    severity="error",
                    message="Issue date is after expiry date",
                    issue_date=str(emirates_id.issue_date),
                    expiry_date=str(emirates_id.expiry_date),
                )
            )

        if emirates_id.date_of_birth and emirates_id.date_of_birth >= today:
            issues.append(
                _issue(
                    rule_id="emirates_id_dob_invalid",
                    severity="error",
                    message="Date of birth is in the future",
                    date_of_birth=str(emirates_id.date_of_birth),
                )
            )
    else:
        issues.append(
            _issue(
                rule_id="invalid_doc_type",
                severity="error",
                message="Document type is invalid",
            )
        )
    return issues


def validate_salary_certificate(salary_certificate: SalaryCertificateData, name) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    today = date.today()

    if salary_certificate.is_salary_certificate:
        if _text_missing(salary_certificate.client_name_on_certificate):
            issues.append(
                _issue(rule_id="salary_cert_client_name_missing", severity="error", message="Client name missing")
            )

        elif (
            salary_certificate.client_name_on_certificate
            and name
            and fuzz.token_set_ratio(
                _normalize_text(salary_certificate.client_name_on_certificate), _normalize_text(name)
            )
            <= 90
        ):
            issues.append(
                _issue(
                    rule_id="name_invalid",
                    severity="error",
                    message=f"This salary certificate does not belong to {name}",
                )
            )
            return issues

        if _text_missing(salary_certificate.company_name):
            issues.append(
                _issue(rule_id="salary_cert_company_name_missing", severity="error", message="Company name missing")
            )

        if _text_missing(salary_certificate.certificate_address):
            issues.append(
                _issue(rule_id="salary_cert_address_missing", severity="error", message="Certificate address missing")
            )

        if _text_missing(salary_certificate.landline_number):
            issues.append(
                _issue(rule_id="salary_cert_landline_missing", severity="error", message="Landline number missing")
            )

        if _text_missing(salary_certificate.website):
            issues.append(
                _issue(rule_id="salary_cert_website_missing", severity="warning", message="Company website missing")
            )

        if _text_missing(salary_certificate.company_email):
            issues.append(
                _issue(rule_id="salary_cert_email_missing", severity="warning", message="Company email missing")
            )

        if salary_certificate.basic_salary and salary_certificate.basic_salary <= 0:
            issues.append(
                _issue(
                    rule_id="salary_cert_basic_salary_invalid",
                    severity="error",
                    message="Basic salary is zero or negative",
                    basic_salary=salary_certificate.basic_salary,
                )
            )

        if salary_certificate.gross_monthly_income and salary_certificate.gross_monthly_income <= 0:
            issues.append(
                _issue(
                    rule_id="salary_cert_gross_income_missing",
                    severity="warning",
                    message="Gross monthly income calculation is zero (check allowances)",
                )
            )

        if salary_certificate.certificate_issue_date and salary_certificate.certificate_issue_date > today:
            issues.append(
                _issue(
                    rule_id="salary_cert_issue_future",
                    severity="error",
                    message="Issue date is in the future",
                    issue_date=str(salary_certificate.certificate_issue_date),
                )
            )

        if (
            today
            and salary_certificate.certificate_issue_date
            and today - salary_certificate.certificate_issue_date > timedelta(days=30)
        ):
            issues.append(
                _issue(
                    rule_id="salary_cert_outdated",
                    severity="error",
                    message="Certificate is older than 30 days",
                    issue_date=str(salary_certificate.certificate_issue_date),
                )
            )

        if salary_certificate.joining_date:
            if salary_certificate.joining_date > today:
                issues.append(
                    _issue(
                        rule_id="salary_cert_joining_future",
                        severity="error",
                        message="Joining date is in the future",
                        joining_date=str(salary_certificate.joining_date),
                    )
                )

            if salary_certificate.joining_date > salary_certificate.certificate_issue_date:
                issues.append(
                    _issue(
                        rule_id="salary_cert_joining_after_issue",
                        severity="error",
                        message="Joining date is after issue date",
                        joining_date=str(salary_certificate.joining_date),
                        issue_date=str(salary_certificate.certificate_issue_date),
                    )
                )
    else:
        issues.append(_issue(rule_id="invalid_doc_type", severity="error", message="Document type is invalid"))
    return issues


def validate_bank_statements(
    bank_statements: BankStatementsData, residency: Optional[str], employment: Optional[str], name
) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []

    today = date.today()

    residency_normalized = (residency or "").strip().lower()
    employment_normalized = (employment or "").strip().lower()

    if bank_statements.is_bank_statement:
        if _text_missing(bank_statements.account_holder_name):
            issues.append(
                _issue(rule_id="bank_stmt_holder_missing", severity="error", message="Account holder name missing")
            )

        elif (
            bank_statements.account_holder_name
            and name
            and fuzz.token_set_ratio(_normalize_text(bank_statements.account_holder_name), _normalize_text(name)) <= 90
        ):
            issues.append(
                _issue(
                    rule_id="name_invalid", severity="error", message=f"These bank statements does not belong to {name}"
                )
            )
            return issues

        if _text_missing(bank_statements.iban):
            issues.append(_issue(rule_id="bank_stmt_iban_missing", severity="error", message="IBAN missing"))

        if _text_missing(bank_statements.account_number):
            issues.append(
                _issue(rule_id="bank_stmt_acc_number_missing", severity="error", message="Account number missing")
            )

        if bank_statements.statement_start_date is None or bank_statements.statement_end_date is None:
            issues.append(
                _issue(rule_id="bank_stmt_dates_missing", severity="error", message="Statement period dates missing")
            )
        else:
            if bank_statements.statement_end_date:
                first_day_this_month = today.replace(day=1)
                cutoff_date = first_day_this_month - relativedelta(months=1)

                if bank_statements.statement_end_date < cutoff_date:
                    issues.append(_issue(
                        rule_id="bank_stmt_outdated",
                        severity="error",
                        message=f"Bank statement is outdated. It must cover up to {(today - relativedelta(months=1)).strftime('%B %Y')}.",
                        statement_end_date=str(bank_statements.statement_end_date)
                    ))
                    return issues
            else:
                return issues

            if bank_statements.statement_end_date <= bank_statements.statement_start_date:
                issues.append(
                    _issue(
                        rule_id="bank_stmt_invalid_period",
                        severity="warning",
                        message="End date precedes start date",
                        statement_start=str(bank_statements.statement_start_date),
                        statement_end=str(bank_statements.statement_end_date),
                    )
                )

        required_months = 12 if residency_normalized == "non-resident" else 6

        if not bank_statements.check_recent_continuity(required_months):
            issues.append(
                _issue(
                    rule_id="bank_stmt_gaps_detected",
                    severity="error",
                    message="Statement months are not consecutive (gaps detected in recent history)",
                )
            )

        if len(bank_statements.get_recent_periods(required_months)) < required_months:
            issues.append(
                _issue(
                    rule_id="bank_stmt_insufficient_history",
                    severity="error",
                    message=(
                        f"Insufficient history ({len(bank_statements.get_recent_periods(required_months))} " f"of {required_months} months found)"
                    ),
                    months_found=len(bank_statements.get_recent_periods(required_months)),
                    months_required=required_months,
                )
            )

        all_salary_credits = bank_statements.monthly_salary_credits or []

        sorted_credits = sorted(all_salary_credits, key=lambda x: x.month, reverse=True)

        if sorted_credits and sorted_credits[0].month == today.strftime("%Y-%m"):
            sorted_credits = sorted_credits[1:]

        recent_credits = sorted_credits[:required_months]

        if not recent_credits:
            is_self_employed = employment_normalized == "self-employed"

            issues.append(
                _issue(
                    rule_id="bank_stmt_no_salary_credits",
                    severity="warning" if is_self_employed else "error",
                    message="No regular salary credits detected",
                )
            )
        else:
            for credit in recent_credits:
                if not credit.amount:
                    issues.append(
                        _issue(
                            rule_id="bank_stmt_credit_amount_missing",
                            severity="warning",
                            message=f"Salary amount missing for {credit.month}",
                            month=credit.month,
                        )
                    )
    else:
        issues.append(_issue(rule_id="invalid_doc_type", severity="error", message="Invalid document type"))
    return issues


def validate_payslips(payslips: PaySlipsData, name) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []

    if payslips.is_payslip:
        if _text_missing(payslips.full_name):
            issues.append(_issue(rule_id="payslips_full_name_missing", severity="error", message="Full name missing"))

        elif (
            payslips.full_name
            and name
            and fuzz.token_set_ratio(_normalize_text(payslips.full_name), _normalize_text(name)) <= 90
        ):
            issues.append(
                _issue(rule_id="name_invalid", severity="error", message=f"This payslip does not belong to {name}")
            )
            return issues

        if not payslips.net_pay:
            issues.append(
                _issue(rule_id="payslips_data_missing", severity="error", message="No payslip data extracted")
            )
            return issues

        try:
            if payslips.start_date and payslips.end_date:
                start_dt = datetime.strptime(payslips.start_date, "%Y-%m").date()
                end_dt = datetime.strptime(payslips.end_date, "%Y-%m").date()
                expected_count = (end_dt.year - start_dt.year) * 12 + (end_dt.month - start_dt.month) + 1

                if payslips.months_covered < expected_count:
                    issues.append(
                        _issue(
                            rule_id="payslips_gap_detected",
                            severity="warning",
                            message="Missing months detected (gap in history)",
                            months_found=payslips.months_covered,
                            months_expected=expected_count,
                        )
                    )
                elif payslips.months_covered > expected_count:
                    issues.append(
                        _issue(
                            rule_id="payslips_duplicates_detected",
                            severity="warning",
                            message="Duplicate payslips detected for the same month",
                        )
                    )

        except ValueError:
            issues.append(
                _issue(
                    rule_id="payslips_date_format_error",
                    severity="error",
                    message="Invalid date format detected in payslips (expected YYYY-MM)",
                )
            )

        if payslips.months_covered and payslips.months_covered < 6:
            issues.append(
                _issue(
                    rule_id="payslips_insufficient_history",
                    severity="warning",
                    message=f"Insufficient pay history ({payslips.months_covered} of 6 months)",
                )
            )

        if payslips.net_pay:
            for entry in payslips.net_pay:
                if entry.net_pay <= 0:
                    issues.append(
                        _issue(
                            rule_id="payslips_zero_pay",
                            severity="warning",
                            message=f"Net pay is zero or negative for {entry.month}",
                            month=entry.month,
                        )
                    )
    else:
        issues.append(_issue(rule_id="invalid_doc_type", severity="error", message="Invalid document type"))
    return issues


def validate_ejari(ejari: EjariData, name) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    today = date.today()
    if ejari.is_ejari:
        if _text_missing(ejari.full_name):
            issues.append(
                _issue(
                    rule_id="ejari_full_name_missing",
                    severity="error",
                    message="Tenant full name missing",
                )
            )
        elif (
            ejari.full_name
            and name
            and fuzz.token_set_ratio(_normalize_text(ejari.full_name), _normalize_text(name)) <= 90
        ):
            issues.append(
                _issue(rule_id="name_invalid", severity="error", message=f"This ejari does not belong to {name}")
            )
            return issues

        if ejari.expiry_date and ejari.expiry_date < today:
            issues.append(
                _issue(
                    rule_id="ejari_expired",
                    severity="error",
                    message="Ejari contract is expired",
                    expiry_date=str(ejari.expiry_date),
                )
            )
    else:
        issues.append(_issue(rule_id="invalid_doc_type", severity="error", message="Invalid document type"))
    return issues


def validate_proof_of_address(proof_of_address: ProofOfAddressData, name):
    issues: List[ValidationIssue] = []

    if proof_of_address.is_proof_of_address:
        if _text_missing(proof_of_address.full_name):
            issues.append(_issue(rule_id="name_is_missing", severity="error", message="Full name missing"))

        elif (
            proof_of_address.full_name
            and name
            and fuzz.token_set_ratio(_normalize_text(proof_of_address.full_name), _normalize_text(name)) <= 90
        ):
            issues.append(
                _issue(
                    rule_id="name_invalid", severity="error", message=f"This proof of address does not belong to {name}"
                )
            )
            return issues

        if not proof_of_address.address.street:
            issues.append(_issue(rule_id="street_missing", severity="error", message="Street missing"))
        if not proof_of_address.address.city:
            issues.append(_issue(rule_id="city_missing", severity="error", message="City missing"))
        if not proof_of_address.address.postal_code:
            issues.append(_issue(rule_id="postal_code_missing", severity="error", message="Postal code missing"))
        if not proof_of_address.address.country:
            issues.append(_issue(rule_id="country_missing", severity="error", message="Country missing"))
        if not proof_of_address.address.building_house_number:
            issues.append(
                _issue(
                    rule_id="building_house_number_missing",
                    severity="error",
                    message="Building or house number missing",
                )
            )
        if not proof_of_address:
            issues.append(_issue(rule_id="address_missing", severity="error", message="Address missing"))
    else:
        issues.append(_issue(rule_id="invalid_doc_type", severity="error", message="Invalid document type"))
    return issues


def validate_national_id(national_id: NationalIdData, name):
    issues: List[ValidationIssue] = []
    today = date.today()

    if national_id.is_national_id:
        if _text_missing(national_id.full_name):
            issues.append(_issue(rule_id="full_name_is_missing", severity="error", message="Full name missing"))

        elif (
            national_id.full_name
            and name
            and fuzz.token_set_ratio(_normalize_text(national_id.full_name), _normalize_text(name)) <= 90
        ):
            issues.append(
                _issue(rule_id="name_invalid", severity="error", message=f"This national id does not belong to {name}")
            )
            return issues

        if _text_missing(national_id.id_number):
            issues.append(_issue(rule_id="id_number_missing", severity="error", message="ID number missing"))
        if national_id.issue_date is None:
            issues.append(_issue(rule_id="issue_date_missing", severity="error", message="Issue date missing"))
        if national_id.expiry_date is None:
            issues.append(_issue(rule_id="expiry_date_missing", severity="error", message="Expiry date missing"))
        if _text_missing(national_id.place_of_issue):
            issues.append(_issue(rule_id="place_of_issue_missing", severity="error", message="Place of issue missing"))
        if national_id.date_of_birth is None:
            issues.append(_issue(rule_id="date_of_birth_missing", severity="error", message="Date of birth missing"))
        if national_id.expiry_date and national_id.expiry_date < today:
            issues.append(
                _issue(
                    rule_id="doc_expired",
                    severity="error",
                    message="Passport is expired",
                    passport_expiry=str(national_id.expiry_date),
                )
            )

        if national_id.issue_date and national_id.issue_date >= national_id.expiry_date:
            issues.append(
                _issue(
                    rule_id="invalid_date_range",
                    severity="error",
                    message="Issue date cannot be after expiry date",
                    issue_date=str(national_id.issue_date),
                    expiry_date=str(national_id.expiry_date),
                )
            )

        if national_id.date_of_birth and national_id.date_of_birth >= today:
            issues.append(
                _issue(
                    rule_id="invalid_dob",
                    severity="error",
                    message="Date of birth is in the future",
                    passport_dob=str(national_id.date_of_birth),
                )
            )
    else:
        issues.append(_issue(rule_id="invalid_doc_type", severity="error", message="Invalid document type"))

    return issues
