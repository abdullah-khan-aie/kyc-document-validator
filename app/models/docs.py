# pylint: disable=line-too-long
from datetime import date
from typing import Annotated, List, Literal, Optional

from pydantic import BaseModel, Field, computed_field, model_validator
from pydantic.json_schema import SkipJsonSchema
from pydantic_extra_types.country import CountryInfo


class PassportData(BaseModel):
    document_id: SkipJsonSchema[Optional[int]] = None
    is_passport: bool
    full_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    passport_number: Optional[str] = None
    nationality: Optional[str] = None
    gender: Optional[Literal["Male", "Female", "Other"]] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    issue_place: Optional[str] = None
    country: Optional[CountryInfo] = None

    @computed_field
    @property
    def age(self) -> int:
        today = date.today()
        if self.date_of_birth:
            return (
                today.year
                - self.date_of_birth.year
                - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
            )
        return 0


class VisaData(BaseModel):
    document_id: SkipJsonSchema[Optional[int]] = None
    is_visa: bool
    full_name: Optional[str] = None
    visa_number: Optional[str] = None
    passport_number_on_visa: Optional[str] = None
    employer_name: Optional[str] = None
    place_of_issue: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None

    @computed_field
    @property
    def years_since_in_uae(self) -> int:
        if self.issue_date:
            today = date.today()
            return (
                today.year
                - self.issue_date.year
                - ((today.month, today.day) < (self.issue_date.month, self.issue_date.day))
            )
        return -1


class EmiratesIdData(BaseModel):
    document_id: SkipJsonSchema[Optional[int]] = None
    is_emirates_id: bool
    full_name: Optional[str] = None
    emirates_id_number: Optional[str] = None
    date_of_birth: Optional[date] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    nationality: Optional[str] = None
    employer_name: Optional[str] = None
    place_of_issue: Optional[str] = None
    status: Optional[
        Annotated[Literal["Resident", "Non-Resident", "National"], Field(description="Status of the ID holder")]
    ] = None

    @model_validator(mode="after")
    def adjust_status_based_on_nationality(self):
        if self.nationality:
            if self.nationality.lower() == "dubai":
                self.status = "National"
            return self
        return self


class SalaryCertificateData(BaseModel):
    document_id: SkipJsonSchema[Optional[int]] = None
    is_salary_certificate: bool
    client_name_on_certificate: Optional[str] = None
    company_name: Optional[str] = None
    company_email: Optional[str] = None
    basic_salary: Optional[float] = None
    job_title: Optional[str] = None
    employment_type: Optional[
        Annotated[str, Field(description="The type of employment, can also be called as contract type")]
    ] = None
    employment_date: Optional[date] = None
    position: Optional[str] = None
    industry: Optional[str] = None
    office_address: Optional[
        Annotated[str, Field(description="The address of the company, relevant to employee's working place.")]
    ] = None
    monthly_incomes: Optional[Annotated[List[float], Field(description="List of all types of incomes mentioned.")]] = (
        None
    )
    joining_date: Optional[date] = None
    certificate_address: Optional[str] = None
    landline_number: Optional[str] = None
    certificate_issue_date: Optional[date] = None
    website: Optional[str] = None

    @computed_field
    @property
    def gross_monthly_income(self) -> float:
        gross_income = 0.0
        if self.monthly_incomes:
            for income in self.monthly_incomes:
                gross_income += income
        return gross_income

    @computed_field
    @property
    def domain(self) -> str:
        if self.website:
            return self.website.replace("https://", "").replace("http://", "").split("/")[0]
        return ""


class MonthlySalaryCredit(BaseModel):
    month: str  # "2024-01"
    amount: Optional[float] = None
    description: Optional[str] = None


class StatementPeriod(BaseModel):
    start_date: date
    end_date: date


class BankStatementsData(BaseModel):
    document_id: SkipJsonSchema[Optional[int]] = None
    is_bank_statement: bool
    account_holder_name: Optional[str] = None
    iban: Optional[
        Annotated[
            str,
            Field(
                description="If there are multiple accounts, IBAN should be of that account which is receiving salary"
            ),
        ]
    ] = None
    account_number: Optional[str] = None
    statement_periods: Optional[
        Annotated[
            List[StatementPeriod],
            Field(
                description="List of statement periods found in the document but in statements format of date can be this DD-MM-YYYY"
            ),
        ]
    ] = None
    monthly_salary_credits: Optional[List[MonthlySalaryCredit]] = None

    @computed_field
    @property
    def statement_start_date(self) -> Optional[date]:
        if self.statement_periods:
            return min(p.start_date for p in self.statement_periods)
        return None

    @computed_field
    @property
    def statement_end_date(self) -> Optional[date]:
        if self.statement_periods:
            return max(p.end_date for p in self.statement_periods)
        return None

    @computed_field
    @property
    def months_covered(self) -> int:
        if self.statement_periods:
            return len(self.statement_periods)
        return -1

    def get_recent_periods(self, limit: int) -> List[StatementPeriod]:
        """Returns the N most recent statement periods."""
        if not self.statement_periods:
            return []
        sorted_periods = sorted(self.statement_periods, key=lambda x: x.start_date, reverse=True)
        if sorted_periods[0].start_date.year == date.today().year and sorted_periods[0].start_date.month == date.today().month:
            sorted_periods = sorted_periods[1:]
        return sorted_periods[:limit]

    @computed_field
    @property
    def is_statement_period_consecutive(self) -> bool:
        """Checks continuity of ALL periods."""
        return self._check_continuity(self.statement_periods)

    def check_recent_continuity(self, limit: int) -> bool:
        """Checks continuity of only the RECENT N periods."""
        recent = self.get_recent_periods(limit)
        return self._check_continuity(recent)

    def _check_continuity(self, periods: Optional[List[StatementPeriod]]) -> bool:
        if not periods or len(periods) < 2:
            return True

        # Sort Ascending for gap check
        sorted_periods = sorted(periods, key=lambda x: x.start_date)

        for i in range(len(sorted_periods) - 1):
            current_date = sorted_periods[i].start_date
            next_date = sorted_periods[i + 1].start_date

            # Logic: (YearDiff * 12) + MonthDiff. Should be exactly 1.
            diff = (next_date.year - current_date.year) * 12 + (next_date.month - current_date.month)
            if diff != 1:
                return False
        return True


class EachMonthNetPay(BaseModel):
    month: Annotated[str, Field(description="The month and year in 'YYYY-MM' format (e.g., '2024-08')")]
    net_pay: float


class PaySlipsData(BaseModel):
    document_id: SkipJsonSchema[Optional[int]] = None
    is_payslip: bool
    full_name: Optional[str] = None
    net_pay: Optional[Annotated[List[EachMonthNetPay], Field(description="List of monthly net pays")]] = None

    @computed_field
    @property
    def sorted_net_pay(self) -> List[EachMonthNetPay]:
        if self.net_pay:
            return sorted(self.net_pay, key=lambda x: x.month)
        return []

    @computed_field
    @property
    def start_date(self) -> Optional[str]:
        if self.sorted_net_pay:
            return self.sorted_net_pay[0].month
        return None

    @computed_field
    @property
    def end_date(self) -> Optional[str]:
        if self.sorted_net_pay:
            return self.sorted_net_pay[-1].month
        return None

    @computed_field
    @property
    def months_covered(self) -> int:
        if self.net_pay:
            return len(self.net_pay)
        return -1


class EjariData(BaseModel):
    document_id: SkipJsonSchema[Optional[int]] = None
    is_ejari: bool
    full_name: Optional[str] = None
    expiry_date: Optional[date] = None


class Address(BaseModel):
    postal_code: Optional[str] = None
    building_house_number: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None


class ProofOfAddressData(BaseModel):
    document_id: SkipJsonSchema[Optional[int]] = None
    is_proof_of_address: bool
    full_name: Optional[str] = None
    address: Optional[Address] = None


class NationalIdData(BaseModel):
    document_id: SkipJsonSchema[Optional[int]] = None
    is_national_id: bool
    full_name: Optional[str] = None
    id_number: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    place_of_issue: Optional[str] = None
    date_of_birth: Optional[date] = None
