from app.models.docs import EmiratesIdData
from .llm_client import extract_with_llm
from typing import Optional


async def extract_emirates_id_from_text(text: str, comments : Optional[str] = None) -> tuple[EmiratesIdData, dict]:
    return await extract_with_llm(
        doc_type="emirates_id",
        text=text,
        comments=comments,
        model_cls=EmiratesIdData
    )
