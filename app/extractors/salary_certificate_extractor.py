from app.models.docs import SalaryCertificateData
from .llm_client import extract_with_llm
from typing import Optional


async def extract_salary_certificate_from_text(text: str, comments : Optional[str] = None) -> tuple[SalaryCertificateData, dict]:
    return await extract_with_llm(
        doc_type="salary_certificate",
        text=text,
        comments=comments,
        model_cls=SalaryCertificateData
    )
