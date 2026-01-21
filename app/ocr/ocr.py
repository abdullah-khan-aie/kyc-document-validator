# app/ocr/ocr.py
from __future__ import annotations

# FOR MAC OS
import certifi

from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError
from azure.ai.documentintelligence.aio import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest, DocumentContentFormat, AnalyzeResult
from functools import lru_cache
from app.core import calculate_azure_costing, get_settings, observe, get_langfuse



@lru_cache(maxsize=1)
def _azure_ocr_client():
    """Returns a singleton instance of the Document Intelligence Client."""
    return DocumentIntelligenceClient(
        endpoint=get_settings().azure_doc_intel_endpoint.get_secret_value(),
        credential=AzureKeyCredential(key=get_settings().azure_doc_intel_key.get_secret_value()),
        connection_verify=certifi.where()
    )


@observe(as_type="generation", name="OCR")
async def _extract_with_azure_document_intelligence(file_path: str) -> tuple[str, int]:
    """
    Tries Azure AI Document Intelligence (Form Recognizer) first when credentials are present.
    Please update the price of OCR Model in settings, if model changed
    """
    try:
        poller = await _azure_ocr_client().begin_analyze_document(
            "prebuilt-layout",
            AnalyzeDocumentRequest(url_source=file_path),
            output_content_format=DocumentContentFormat.MARKDOWN,
        )
        response: AnalyzeResult = await poller.result()
        calculate_azure_costing(len(response.pages) if response.pages else 1)

    except HttpResponseError as error:
        if error.error.innererror.get("code", "").casefold() == "invalidcontent":
            get_langfuse().update_current_span(
                output=error.error.innererror.get("message", "")
            )
            raise ValueError(
                error.error.innererror.get("message", "")
            )
        elif error.error.innererror.get("code", "").casefold() == "unsupportedcontent":
            raise ValueError(
                error.error.innererror.get("message", "")
            )
        return "", 0
    return response.content, len(response.pages)


async def extract_text_from_pdf(file_path: str) -> tuple[str, int]:

    text, total_pages = await _extract_with_azure_document_intelligence(file_path)
    if text.strip():
        return text, total_pages

    return "", 0
