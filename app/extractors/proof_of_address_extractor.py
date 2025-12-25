from app.models.docs import ProofOfAddressData
from .llm_client import extract_with_llm
from typing import Optional


async def extract_proof_of_address_from_text(text: str, comments : Optional[str] = None) -> tuple[ProofOfAddressData, dict]:
    return await extract_with_llm(
        doc_type="proof_of_address",
        text=text,
        comments=comments,
        model_cls=ProofOfAddressData,
    )
