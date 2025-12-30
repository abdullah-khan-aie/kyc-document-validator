from fastapi import APIRouter
from app.services import run_pipeline, process_documents
from app.schemas import DocumentValidationRequest, CrossDocumentValidationRequest
from app.db import get_supabase
from app.core import observe, get_langfuse, slack_post_message, get_settings
from app.schemas import DocumentEntry, CrossDocumentsRequest
import asyncio

router = APIRouter()

@router.post("/document")
@observe(name='Documents')
async def validate_document(request: DocumentValidationRequest):
    """
    Validate the given document.

    Args:
        request.document_id (str): The document to be validated.

    Returns:
        dict: Validation result.
    """

    get_langfuse().update_current_trace(
        name=f"Validation: App {request.application_id}",
    )

    docs = get_supabase().table('documents').select('id, doc_name, blob_path').eq('application_id', request.application_id).execute()
    tasks = []
    for doc in docs.data:
        task = run_pipeline(
            document_id=doc['id'],
            doc_name=doc['doc_name'].lower(),
            file_path=doc['blob_path'],
            name= request.name,
            profile_type={
                'residency': request.residency,
                'employment': request.employment,
            },
        )
        tasks.append(task)
    reports= await asyncio.gather(*tasks)
    get_langfuse().update_current_span(
        output=reports,
    )
    per_customer_cost = 0

    for report in reports:
        cost = (
                report
                .get("_meta", {})
                .get("cost", 0.0)
        )
        per_customer_cost += cost

    cost_diff = per_customer_cost - get_settings().customer_cost_threshold

    if per_customer_cost > 1.0:
        await slack_post_message(
            trace_link=get_langfuse().get_trace_url(),
            msg=(
                f"*Customer Name:* {request.name}\n"
                f"*Threshold:* ${get_settings().customer_cost_threshold}\n"
                f"*Cost Used by Customer:* ${per_customer_cost}\n"
                f"*Exceeded Customer Cost:* ${per_customer_cost:.4f} > ${get_settings().customer_cost_threshold} (Diff: ${cost_diff:.4f})"
            )
        )

    return reports

@router.post("/documents")
async def validate_documents(request: CrossDocumentValidationRequest):
    docs = get_supabase().table('documents').select('id, doc_name, llm_response').eq('application_id', request.application_id).execute()
    formatted_documents = [
        DocumentEntry(
            document_version_id=item['id'],
            document_type=item['doc_name'],
            llm_response=item['llm_response']
        )
        for item in docs.data
    ]
    cross = CrossDocumentsRequest(
        application_id=int(request.application_id),
        documents=formatted_documents,
        residency=request.residency,
        employment=request.employment,
        customer_name=request.customer_name,
        email=request.email,
        mobile_number=request.mobile_number,
    )
    report = await process_documents(cross)
    return report