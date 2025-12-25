from app.models.docs import BankStatementsData
from .llm_client import extract_with_llm
from typing import Optional


async def extract_bank_statements_from_text(text: str, comments : Optional[str] = None) -> tuple[BankStatementsData, dict]:
    return await extract_with_llm(
        doc_type="bank_statements",
        text=text,
        comments=comments,
        model_cls=BankStatementsData
    )
