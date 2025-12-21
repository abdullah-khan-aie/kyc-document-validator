from typing import Optional
from pydantic import BaseModel


class InfoSheet(BaseModel):

    # =====================
    # [1] Personal Information
    # =====================
    fullName: Optional[str] = None
    gender: Optional[str] = None
    email: Optional[str] = None
    mobileNumber: Optional[str] = None
    whatsapp: Optional[bool] = None
    whatsappNumber: Optional[str] = None
    passportIssuingCountry: Optional[str] = None
    maritalStatus: Optional[str] = None
    numberOfDependents: Optional[int] = None
    mothersMaidenName: Optional[str] = None
    statusInUAE: Optional[str] = None
    uaeResidencyStartDate: Optional[str] = None
    applicationType: Optional[str] = None

    # =====================
    # [2] UAE Address
    # =====================
    livingArrangementStatus: Optional[str] = None
    flatVillaNumber: Optional[str] = None
    buildingVillaName: Optional[str] = None
    streetLocation: Optional[str] = None
    nearestLandmark: Optional[str] = None
    uaePOBox: Optional[str] = None
    emirate: Optional[str] = None
    currentAddressStartDate: Optional[str] = None

    # =====================
    # [3] Home Country Address
    # =====================
    homeFlatVillaNumber: Optional[str] = None
    homeBuildingVillaName: Optional[str] = None
    homeStreetLocation: Optional[str] = None
    homeNearestLandmark: Optional[str] = None
    postalZipCode: Optional[str] = None
    homeCity: Optional[str] = None
    homeCountry: Optional[str] = None
    homeCountryContactNumber: Optional[str] = None

    # =====================
    # [4] References
    # =====================
    uaeReference1Name: Optional[str] = None
    uaeReference1Phone: Optional[str] = None
    uaeReference2Name: Optional[str] = None
    uaeReference2Phone: Optional[str] = None
    homeReference1Name: Optional[str] = None
    homeReference1Phone: Optional[str] = None
    homeReference2Name: Optional[str] = None
    homeReference2Phone: Optional[str] = None

    # =====================
    # [5] Employment Information
    # =====================
    employmentType: Optional[str] = None
    companyName: Optional[str] = None
    companyIndustry: Optional[str] = None
    jobTitle: Optional[str] = None
    monthlySalary: Optional[float] = None
    workEmail: Optional[str] = None
    officeAddress: Optional[str] = None
    officeLandlineNumber: Optional[str] = None
    companySize: Optional[str] = None
    hrEmail: Optional[str] = None
    companyWebsite: Optional[str] = None

    # =====================
    # [6] Credit & Loans
    # =====================
    hasCreditCard: Optional[str] = None
    numberOfCreditCards: Optional[int] = None
    creditCardIssuingBank1: Optional[str] = None
    totalCreditLimit: Optional[float] = None

    hasCarLoan: Optional[bool] = None
    numberOfCarLoans: Optional[int] = None
    carLoanIssuingBank: Optional[str] = None
    carLoanMonthlyInstallment: Optional[float] = None

    hasPersonalLoan: Optional[bool] = None
    hasMortgage: Optional[bool] = None
