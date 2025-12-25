from app.models.docs import PassportData
from .llm_client import extract_with_llm
from typing import Optional

async def extract_passport_from_text(text: str, comments : Optional[str] = None) -> tuple[PassportData, dict]:
    return await extract_with_llm(
        doc_type="passport",
        text=text,
        comments=comments,
        model_cls=PassportData
    )
