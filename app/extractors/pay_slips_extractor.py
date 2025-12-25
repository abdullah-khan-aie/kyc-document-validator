from app.models.docs import PaySlipsData
from .llm_client import extract_with_llm
from typing import Optional

async def extract_pay_slips_from_text(text: str, comments : Optional[str] = None) -> tuple[PaySlipsData, dict]:
    return await extract_with_llm(
        doc_type="pay_slips",
        text=text,
        comments=comments,
        model_cls=PaySlipsData
    )