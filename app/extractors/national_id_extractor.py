from app.models.docs import NationalIdData
from .llm_client import extract_with_llm
from typing import Optional


async def extract_national_id_from_text(text: str, comments : Optional[str] = None) -> tuple[NationalIdData, dict]:
    return await extract_with_llm(
        doc_type="national_id",
        text=text,
        comments=comments,
        model_cls=NationalIdData,
    )
