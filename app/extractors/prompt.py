from typing import Dict

PROMPT_TEMPLATES: Dict[str, str] = {
    "passport": (
        """
        CRITICAL CHECK!!!
        First check according to the OCR text, is the document passport?
        You are extracting data from a passport. Return JSON with:
        - full_name (string)
        - date_of_birth (YYYY-MM-DD)
        - passport_number (string)
        - nationality (string or null)
        - gender (string)
        - issue_date (YYYY-MM-DD or null)
        - expiry_date (YYYY-MM-DD)
        - issue_place (string) (description="It is the place of issue where the passport was issued or the organisation that issued it, it must be a city but it cannot be place of birth.")

        Rules:
        - full_name, date_of_birth, passport_number, and expiry_date MUST never be null. Use MRZ lines if needed.
        - Always emit ISO dates (YYYY-MM-DD).
        - Use the English transcription when multiple languages appear.
        - If password text has name in <<<[Name]>>> use this name this will be more accurate.
        Document text:
        {document_text}
        If there are some comments please take care of them:
        {comments}
        """
    ),
    "visa": (
        """
        CRITICAL CHECK!!!
        First check according to the OCR text, is the document visa?
        You are extracting data from a residence visa. Return JSON with:
        - full_name (string or null)
        - visa_number (string) (description= "File number is the visa number.")
        - passport_number_on_visa (string)
        - employer_name (string)
        - place_of_issue (string) description= "Visa place of issue must be the city where the visa was issued")
        - issue_date (YYYY-MM-DD)
        - expiry_date (YYYY-MM-DD)

        The fields full_name, passport_number_on_visa, employer_name, and expiry_date must always be provided (infer from context/MRZ if necessary). Use ISO dates.
        Document text:
        {document_text}
        If there are some comments please take care of them:
        {comments}
        """
    ),
    "emirates_id": (
        """
        CRITICAL CHECK!!!
        First check according to the OCR text, is the document emirates id?
        You are extracting data from an Emirates ID card. Return JSON with:
        - full_name (string)
        - emirates_id_number (string)
        - issue_date (YYYY-MM-DD)
        - expiry_date (YYYY-MM-DD)
        - employer_name (string or null)
        - place_of_issue (string)

        **Employer Name**: You have to correctly map the employer name to the field, you should correct identify the profession and employer name.
            - Example: Input "Doctor, Al-Arbiya School L.L.C " -> Output "(though process employer name will Al-Arbiya School L.L.C because Doctor is a profession"

        Use null when information is absent. Dates must be YYYY-MM-DD.
        Document text:
        {document_text}
        If there are some comments please take care of them:
        {comments}
        """
    ),
    "salary_certificate": (
        """
        CRITICAL CHECK!!!
        First check according to the OCR text, is the document salary certificate?
        Extract salary certificate details. Output JSON with:
        - client_name_on_certificate (string)
        - company_name (string)
        - company_email (string or null)
        - basic_salary (number)
        - employment_type (string) (description="The type of employment or contract type, e.g., Full-time, Permanent")
        - employment_date (YYYY-MM-DD)
        - position (string)
        - industry (string or null)
        - office_address (string) (description="The physical address of the company/office")
        - monthly_incomes (list of numbers) (description="List of all individual income components mentioned, e.g., housing allowance, transport, etc.")
        - joining_date (YYYY-MM-DD)
        - certificate_address (string)
        - landline_number (string)
        - certificate_issue_date (YYYY-MM-DD)
        - website (string or null)

        Instructions:
        - If salary appears in AED with currency symbols, convert to a number in AED.
        - Ensure all dates are in YYYY-MM-DD format.

        Document text:
        {document_text}
        If there are some comments please take care of them:
        {comments}
        """
    ),
    "bank_statements": (
        """
        CRITICAL CHECK!!!
        First check according to the OCR text, is the document bank statements?
        Extract the bank statements data from the raw ocr text:
        - account_holder_name (string)
        - iban (string) (description= "If there are multiple accounts, IBAN should be of that account which is receiving salary")
        - account_number (string)
        - statement_periods (description="List each individual month covered in the statement separately. For each month, provide start_date as the first day of the month and end_date as the last day of the month (format DD-MM-YYYY).")
        - monthly_salary_credits: List of array of objects {{ "month": "YYYY-MM", "amount": number or null, "description": string or null }} 
        Document text:
        {document_text}
        If there are some comments please take care of them:
        {comments}
    """
    ),
    "pay_slips": (
        """
        CRITICAL CHECK!!!
        First check according to the OCR text, is the document pay slips?
        Extract the payslips data from the raw ocr text:
        - full_name (string)
        - net_pays (list[Each Month Net Pay of Employee])
        - start_date (YYYY-MM) (description="The month and year in 'YYYY-MM' format (e.g., '2024-08'), start date from where the slips are starting")
        - end_date (YYYY-MM) (description="The month and year in 'YYYY-MM' format (e.g., '2024-08'), end date at where the slips are ending")

    Document text:
        {document_text}
    If there are some comments please take care of them:
        {comments}
    """
    ),
    "ejari": (
        """
        CRITICAL CHECK!!!
        First check according to the OCR text, is the document is ejari?
        Extract tenancy registration (Ejari) details. Output JSON with:
        - full_name (string) description="Tenant / client name on the Ejari"
        - expiry_date (YYYY-MM-DD)

        Instructions:
        - Keep dates in ISO format.
        - If multiple tenants are listed, return the primary client highlighted on the certificate.

        Document text:
        {document_text}
        If there are some comments please take care of them:
        {comments}
    """
    ),
    "national_id": (
        """
        CRITICAL CHECK!!!
        First check according to the OCR text, is the document national id?
        EMIRATE ID is not an national id.
        You are extracting data from a National ID card. Return JSON with:
        - full_name (string)
        - id_number (string)
        - date_of_birth (YYYY-MM-DD)
        - issue_date (YYYY-MM-DD or null)
        - expiry_date (YYYY-MM-DD)
        - place_of_issue (string)

        Rules:
        - full_name, date_of_birth, id_number, and expiry_date MUST never be null. Use MRZ lines if needed.
        - Always emit ISO dates (YYYY-MM-DD).
        - Use the English transcription when multiple languages appear.

        Document text:
        {document_text}
        If there are some comments please take care of them:
        {comments}
        """
    ),
    "proof_of_address": (
        """
        CRITICAL CHECK!!!
        First check according to the OCR text, is the document proof of address?
        You are extracting data from a Proof of Address document (e.g., Utility Bill, Tenancy). 
        BANK STATEMENT is not an proof of address except utility bill and tenancy contract!!!.
        Return JSON with:
        - full_name (string)
        - address (object) with the following fields:
             - postal_code (string or null)
             - building_house_number (string or null)
             - street (string or null)
             - city (string or null)
             - country (string or null)

        Instructions:
        - Attempt to parse the address into its components.
        - If the document is a utility bill or tenancy, focus on the account holder's address usually found at the top.

        Document text:
        {document_text}
        If there are some comments please take care of them:
        {comments}
        """
    ),
}

def get_prompt(doc_type: str) -> str:
    """Return a stripped prompt template for the given document type."""
    try:
        return PROMPT_TEMPLATES[doc_type].strip()
    except KeyError as exc:  # pragma: no cover - defensive guard
        raise ValueError(f"No LLM prompt template registered for {doc_type}.") from exc