from app.models.docs import EjariData
from .llm_client import extract_with_llm
from typing import Optional


async def extract_ejari_from_text(text: str, comments : Optional[str] = None) -> tuple[EjariData, dict]:
    return await extract_with_llm(
        doc_type="ejari",
        text=text,
        comments=comments,
        model_cls=EjariData
    )
