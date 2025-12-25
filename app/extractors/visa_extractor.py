from app.models.docs import VisaData
from .llm_client import extract_with_llm
from typing import Optional


async def extract_visa_from_text(text: str, comments : Optional[str] = None) -> tuple[VisaData, dict]:
    return await extract_with_llm(
        doc_type="visa",
        text=text,
        comments=comments,
        model_cls=VisaData
    )
