from typing import Callable, List
from datetime import date

from rapidfuzz import fuzz

from app.models.case import CaseData

from .doc_rules import ValidationIssue, _normalize_text


def passport_eid_dob_mismatch(case: CaseData) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    if not case.passport or not case.emirates_id:
        return issues

    if (
        case.passport.date_of_birth
        and case.emirates_id.date_of_birth
        and case.passport.date_of_birth != case.emirates_id.date_of_birth
    ):
        issues.append(
            ValidationIssue(
                rule_id="passport_eid_dob_mismatch",
                severity="error",
                message="Date of birth on Passport and Eid do not match.",
                details={
                    "passport_dob": str(case.passport.date_of_birth),
                    "eid_dob": str(case.emirates_id.date_of_birth),
                    "document_ids": [case.passport.document_id, case.emirates_id.document_id],
                },
            )
        )
    return issues


def passport_national_id_dob_mismatch(case: CaseData) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    if not case.passport or not case.national_id:
        return issues

    if (
        case.passport.date_of_birth
        and case.national_id.date_of_birth
        and case.passport.date_of_birth != case.national_id.date_of_birth
    ):
        issues.append(
            ValidationIssue(
                rule_id="passport_national_id_dob_mismatch",
                severity="error",
                message="Date of birth on Passport and National ID do not match.",
                details={
                    "passport_dob": str(case.passport.date_of_birth),
                    "national_id_doc": str(case.national_id.date_of_birth),
                    "document_ids": [case.passport.document_id, case.national_id.document_id],
                },
            )
        )
    return issues


def visa_salary_employer_mismatch(case: CaseData) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    if not case.visa or not case.salary_certificate:
        return issues

    if (
        case.visa.employer_name
        and case.salary_certificate.company_name
        and fuzz.token_set_ratio(
            _normalize_text(case.visa.employer_name), _normalize_text(case.salary_certificate.company_name)
        )
        < 90
    ):
        issues.append(
            ValidationIssue(
                rule_id="visa_salary_employer_mismatch",
                severity="warning",
                message="Employer on Visa does not match employer on Salary Certificate.",
                details={
                    "visa_employer": case.visa.employer_name,
                    "salary_certificate_employer": case.salary_certificate.company_name,
                    "document_ids": [case.visa.document_id, case.salary_certificate.document_id],
                },
            )
        )
    return issues


def name_inconsistent_across_docs(case: CaseData) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []

    potential_sources = {
        "emirates_id": (case.emirates_id.full_name, case.emirates_id) if case.emirates_id else None,
        "passport": (case.passport.full_name, case.passport) if case.passport else None,
        "visa": (case.visa.full_name, case.visa) if case.visa else None,
        "salary_certificate": (
            (case.salary_certificate.client_name_on_certificate, case.salary_certificate)
            if case.salary_certificate
            else None
        ),
        "bank_statements": (
            (case.bank_statements.account_holder_name, case.bank_statements) if case.bank_statements else None
        ),
        "pay_slips": (case.pay_slips.full_name, case.pay_slips) if case.pay_slips else None,
        "ejari": (case.ejari.full_name, case.ejari) if case.ejari else None,
        "national_id": (case.national_id.full_name, case.national_id) if case.national_id else None,
        "proof_of_address": (case.proof_of_address.full_name, case.proof_of_address) if case.proof_of_address else None,
    }

    valid_sources = {k: v for k, v in potential_sources.items() if v is not None and v[0] is not None}

    if len(valid_sources) > 1:
        names_list = [v[0] for v in valid_sources.values()]
        anchor_name = names_list[0]

        is_consistent = True
        for name in names_list[1:]:
            if fuzz.token_set_ratio(_normalize_text(anchor_name), _normalize_text(name)) < 90:
                is_consistent = False
                break

        if not is_consistent:
            name_sources = {k: v[0] for k, v in valid_sources.items()}
            document_ids = [v[1].document_id for v in valid_sources.values()]

            issues.append(
                ValidationIssue(
                    rule_id="name_inconsistent_across_docs",
                    severity="warning",
                    message="Client name is inconsistent across documents.",
                    details={
                        "name_sources": name_sources,
                        "document_ids": document_ids,
                    },
                )
            )
    return issues


def emirates_salary_employer_mismatch(case: CaseData) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    if not case.emirates_id or not case.salary_certificate:
        return issues

    if (
        case.emirates_id.employer_name
        and case.salary_certificate.company_name
        and fuzz.token_set_ratio(
            _normalize_text(case.emirates_id.employer_name), _normalize_text(case.salary_certificate.company_name)
        )
        < 90
    ):
        issues.append(
            ValidationIssue(
                rule_id="emirates_salary_employer_mismatch",
                severity="warning",
                message="Employer on Emirates ID does not match the salary certificate.",
                details={
                    "emirates_id_employer": case.emirates_id.employer_name,
                    "salary_certificate_employer": case.salary_certificate.company_name,
                    "document_ids": [case.emirates_id.document_id, case.salary_certificate.document_id],
                },
            )
        )
    return issues


def emirates_visa_employer_mismatch(case: CaseData) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    if not case.emirates_id or not case.visa:
        return issues

    if (
        case.emirates_id.employer_name
        and case.visa.employer_name
        and fuzz.token_set_ratio(
            _normalize_text(case.emirates_id.employer_name), _normalize_text(case.visa.employer_name)
        )
        < 90
    ):
        issues.append(
            ValidationIssue(
                rule_id="emirates_visa_employer_mismatch",
                severity="warning",
                message="Employer on Emirates ID does not match the visa.",
                details={
                    "emirates_id_employer": case.emirates_id.employer_name,
                    "visa_employer": case.visa.employer_name,
                    "document_ids": [case.visa.document_id, case.emirates_id.document_id],
                },
            )
        )
    return issues


def visa_passport_number_mismatch(case: CaseData) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    if not case.passport or not case.visa:
        return issues

    if case.passport.passport_number and case.visa.passport_number_on_visa:

        passport_number = _normalize_text(case.passport.passport_number)
        passport_number_on_visa = _normalize_text(case.visa.passport_number_on_visa)

        if passport_number and passport_number_on_visa and passport_number != passport_number_on_visa:
            issues.append(
                ValidationIssue(
                    rule_id="visa_passport_number_mismatch",
                    severity="warning",
                    message="Passport number on Visa does not match the Passport number.",
                    details={
                        "passport_number": case.passport.passport_number,
                        "passport_number_on_visa": case.visa.passport_number_on_visa,
                        "document_ids": [case.passport.document_id, case.visa.document_id],
                    },
                )
            )
    return issues


def age_checker_mismatch(case: CaseData) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []

    if not case.passport:
        return issues

    if case.employment:
        if case.employment == "salaried":
            if case.passport.age and case.passport.age > 65:
                issues.append(
                    ValidationIssue(
                        rule_id="age_checker_mismatch",
                        severity="error",
                        message=f"Age cannot be greater than 65 years old for {case.employment}.",
                        details={
                            "employment": case.employment,
                            "age": case.passport.age,
                            "document_ids": [case.passport.document_id],
                        },
                    )
                )
        if case.employment == "self_employed":
            if case.passport.age and case.passport.age > 70:
                issues.append(
                    ValidationIssue(
                        rule_id="age_checker_mismatch",
                        severity="error",
                        message=f"Age cannot be greater than 70 for {case.employment}.",
                        details={
                            "employment": case.employment,
                            "age": case.passport.age,
                            "document_ids": [case.passport.document_id],
                        },
                    )
                )

    return issues


def bank_statements_salary_certificate_salary_mismatch(case: CaseData) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []

    if not case.salary_certificate or not case.bank_statements:
        return issues

    if case.salary_certificate.gross_monthly_income and case.bank_statements.monthly_salary_credits:
        cert_income = case.salary_certificate.gross_monthly_income
        salary_credits = case.bank_statements.monthly_salary_credits

        sorted_credits = sorted(salary_credits, key=lambda x: x.month, reverse=True)

        if sorted_credits and sorted_credits[0].month == date.today().strftime("%Y-%m"):
            sorted_credits = sorted_credits[1:]

        recent_credits = sorted_credits[:12] if case.residency == "non-resident" else sorted_credits[:6]

        valid_amounts = [c.amount for c in recent_credits if c.amount is not None]

        if not cert_income or not valid_amounts:
            return issues

        avg_bank_salary = sum(valid_amounts) / len(valid_amounts)

        tolerance = 0.10
        diff = abs(avg_bank_salary - cert_income)
        threshold = max(avg_bank_salary, cert_income) * tolerance

        if diff > threshold:
            issues.append(
                ValidationIssue(
                    rule_id="bank_statements_salary_certificate_salary_mismatch",
                    severity="warning",
                    message="Average bank salary credits do not match Salary Certificate income (±10%).",
                    details={
                        "salary_certificate_income": cert_income,
                        "average_bank_credit": round(avg_bank_salary, 2),
                        "difference": round(diff, 2),
                        "document_ids": [case.bank_statements.document_id, case.salary_certificate.document_id],
                    },
                )
            )
    return issues


CrossRule = Callable[[CaseData], List[ValidationIssue]]

CROSS_DOC_RULES: List[CrossRule] = [
    passport_eid_dob_mismatch,
    visa_salary_employer_mismatch,
    emirates_salary_employer_mismatch,
    emirates_visa_employer_mismatch,
    visa_passport_number_mismatch,
    name_inconsistent_across_docs,
    age_checker_mismatch,
    bank_statements_salary_certificate_salary_mismatch,
]


def get_cross_document_rules(type_of_person: tuple) -> List[CrossRule]:
    residency, employment = type_of_person
    if (residency.lower(), employment.lower()) == ("resident", "salaried") or (
        residency.lower(),
        employment.lower(),
    ) == ("non-resident", "salaried"):
        return CROSS_DOC_RULES
    return []
