# Document Validation

This repo does automated checks for validating KYC documents of any nationality, including passport, visa, Emirates ID, national ID, salary certificates, bank statements, payslips, Ejari tenancy certificates and proof of address.  
It reads each customer's documents from Supabase, runs OCR with Azure AI Document Intelligence, turns the text into structured data with the OpenAI API, validates each document, runs cross-document consistency rules, and saves a consolidated validation report back to Supabase.

## How the pieces fit together

```
Supabase `documents` table (blob_path per document)
        │
        ▼
 OCR layer (app/ocr/ocr.py – Azure Document Intelligence, prebuilt-layout → Markdown)
        │
        ▼
 LLM extractors (app/extractors/*.py → Pydantic models in app/models/docs.py)
        │
        ▼
 Case bundle (app/models/case.py – CaseData)
        │
        ├─► Per-document validators (app/validation/doc_rules.py)   → POST /validate/document
        │
        └─► Cross-document validators (app/validation/cross_rules.py) → POST /validate/documents
                │
                ▼
        Report + info sheet saved to Supabase
```

## Repository layout

```
app/
  api/            # FastAPI routes (/api/v1/validate/...)
  core/           # Settings, Langfuse observability, Slack cost alerts
  db/             # Supabase client
  models/         # Pydantic models for individual docs, CaseData and InfoSheet
  ocr/            # Azure Document Intelligence client
  extractors/     # OpenAI structured-output parsers turning OCR text into models
  schemas/        # Request bodies
  services/       # Pipeline: OCR → extract → validate → persist
  validation/     # Document + cross-document rule engines and report builder
```

### Models (`app/models`)
* `docs.py` defines PassportData, VisaData, EmiratesIdData, NationalIdData, SalaryCertificateData, MonthlySalaryCredit, BankStatementsData, PaySlipsData, EjariData and ProofOfAddressData. Fields cover everything referenced in the matrix (names, IDs, dates, salary amounts, IBAN, etc.).
* `case.py` bundles the optional document models plus basic context (`residency`, `employment`).
* `info_sheet.py` defines the InfoSheet filled from the extracted documents and saved with the application.

### Validation (`app/validation`)
* `doc_rules.py` holds the `ValidationIssue` schema and per-document validation helpers:
  - Passport / Visa / Emirates ID / National ID: name matches the customer (fuzzy match), expiry in the future, DOB sanity, presence checks, age 21+.
  - Salary certificate: issued within 30 days, salary > 0, joining date sanity.
  - Bank statements: covers up to last month, consecutive months, statement period sanity, salary credits present.
  - Payslips, Ejari and proof of address: name and presence checks.
* `cross_rules.py` implements the cross-document rules:
  - `passport_eid_dob_mismatch`
  - `passport_national_id_dob_mismatch`
  - `visa_passport_number_mismatch`
  - `visa_salary_employer_mismatch`
  - `emirates_salary_employer_mismatch`
  - `emirates_visa_employer_mismatch`
  - `name_inconsistent_across_docs`
  - `age_checker_mismatch`
  - `bank_statements_salary_certificate_salary_mismatch` (±10% tolerance).
* `__init__.py` orchestrates validations and returns the JSON-like report returned by the API.

### OCR (`app/ocr/ocr.py`)
Every document is read with Azure AI Document Intelligence using the `prebuilt-layout` model, and the output comes back as Markdown so tables in bank statements and payslips keep their structure. The file is passed by URL (`blob_path`), so it must be reachable by Azure.  
If the document is empty or unreadable, Azure's error message is returned in the report under `extraction_errors`.

In the Azure portal, open your *Document Intelligence* resource → **Keys and Endpoint**, then copy the `Endpoint` URL and one of the `Keys` into `.env`.

### Extractors (`app/extractors`)
Each module delegates to the OpenAI API (via `app/extractors/llm_client.py`) and uses structured outputs to turn OCR text straight into the Pydantic model:
* `passport_extractor.py`
* `visa_extractor.py`
* `emirates_id_extractor.py`
* `national_id_extractor.py`
* `salary_certificate_extractor.py`
* `bank_statements_extractor.py`
* `pay_slips_extractor.py`
* `ejari_extractor.py`
* `proof_of_address_extractor.py`

The shared system prompt lives in `app/core/config.py`. `OPENAI_MODEL` defaults to `gpt-5.1`.

### Observability and costing (`app/core`)
* Every request is traced in Langfuse (OCR pages and LLM tokens per document). Set `ENABLE_OBSERVABILITY=false` to turn it off.
* Each document report has a `_meta.cost` built from `OCR_COST_PER_PAGE`, `GPT_COST_INPUT_PER_TOKEN` and `GPT_COST_OUTPUT_PER_TOKEN`. Update these when the OCR or GPT model changes.
* When one customer's total cost goes over `CUSTOMER_COST_THRESHOLD` (default $1), a cost alert is posted to Slack with a button linking to the Langfuse trace.

## Setup

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```
uv sync
```

Create a `.env` file in the project root:
```
OPENAI_API_KEY=
OPENAI_MODEL=gpt-5.1
AZURE_DOC_INTEL_ENDPOINT=https://<your-resource>.cognitiveservices.azure.com/
AZURE_DOC_INTEL_KEY=
AZURE_DOC_INTEL_MODEL_ID=prebuilt-layout
SUPABASE_URL=
SUPABASE_KEY=
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
LANGFUSE_BASE_URL=
SLACK_BOT_TOKEN=
SLACK_CHANNEL_ID=
ENVIRONMENT=dev
```

Supabase needs two tables:
* `documents`: `id`, `application_id`, `doc_name`, `blob_path`, plus `ocr_text`, `llm_response`, `doc_feedback` written by the pipeline.
* `applications`: `id`, plus `application_feedback` and `info_sheet` written by the cross-document check.

`doc_name` must be one of `passport`, `visa`, `emirates_id`, `national_id`, `salary_certificate`, `bank_statements`, `payslips`, `ejari`, `proof_of_address`.

## Usage

Run the API:
```
uv run uvicorn app.main:app --reload
```

Interactive docs are at `http://localhost:8000/docs`, and `document_validation.http` has ready-made requests.

1. `POST /api/v1/validate/document` – runs OCR, extraction and per-document validation for every document of the application.
   ```json
   {
     "name": "John Doe",
     "application_id": "10",
     "residency": "resident",
     "employment": "salaried"
   }
   ```
2. `POST /api/v1/validate/documents` – runs the cross-document rules on the saved extractions and fills the info sheet.
   ```json
   {
     "application_id": "10",
     "residency": "resident",
     "employment": "salaried",
     "customer_name": "John Doe",
     "mobile_number": "+971500000000",
     "email": "john.doe@email.com"
   }
   ```

`residency` is `resident` or `non-resident`, and `employment` is currently `salaried` only.

With this overview, you should be able to trace how a document travels through OCR → extractors → models → validators and how the final case report is produced.
