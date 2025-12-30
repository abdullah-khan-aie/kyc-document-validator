from pydantic import BaseModel
from typing import Any, List, Literal


class CrossDocumentValidationRequest(BaseModel):
    application_id: str
    residency: Literal["resident", "non-resident"]
    employment: Literal["salaried"]
    customer_name: str
    mobile_number: str
    email: str


class DocumentValidationRequest(BaseModel):
    name: str
    application_id: str
    residency: Literal["resident", "non-resident"]
    employment: Literal["salaried"]


class DocumentEntry(BaseModel):
    document_version_id: int
    document_type: str
    llm_response: Any


class CrossDocumentsRequest(BaseModel):
    application_id: int
    documents: List[DocumentEntry]
    residency: Literal["resident", "non-resident"]
    employment: Literal["salaried"]
    customer_name: str
    mobile_number: str
    email: str
