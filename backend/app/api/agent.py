"""API endpoints for AI agent content generation."""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from typing import Optional, List
import asyncio
import json
import logging

from app.models.schemas import (
    GenerationRequest,
    GenerationJobResponse,
    GenerationJobStatus,
    GeneratedContentResponse,
    GeneratedContentList,
    GeneratedContentUpdate,
    DocumentSuggestRequest,
    DocumentSuggestResponse,
    SuggestedDocument,
    ContentTemplateCreate,
    ContentTemplateResponse,
    ContentTemplateList,
    ContentTemplateUpdate,
)
from app.services.content_generator import content_generator_service
from app.services.document_selector import document_selector_service
from app.services.template_service import template_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["AI Agent"])


@router.post("/generate", response_model=GenerationJobResponse)
async def start_content_generation(request: GenerationRequest):
    """
    Start an async content generation job.

    This endpoint creates a new content generation job that runs in the background.
    Use the returned job_id to check the generation status and retrieve the result.
    """
    try:
        job_id = await content_generator_service.start_generation(
            topic=request.topic,
            content_type=request.content_type.value,
            document_ids=request.document_ids,
            llm_provider=request.llm_provider.value,
            llm_model=request.llm_model,
            customization=request.customization.dict() if request.customization else None,
            template_id=request.template_id
        )

        return GenerationJobResponse(
            job_id=job_id,
            status="pending",
            message="Content generation job started successfully"
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to start generation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start generation: {str(e)}")


@router.get("/jobs/{job_id}", response_model=GenerationJobStatus)
async def get_job_status(job_id: str):
    """
    Get the current status of a generation job.

    Returns the job's current status, progress percentage, and result ID if completed.
    """
    status = content_generator_service.get_job_status(job_id)

    if not status:
        raise HTTPException(status_code=404, detail="Job not found")

    return GenerationJobStatus(**status)


@router.get("/jobs/{job_id}/stream")
async def stream_job_progress(job_id: str):
    """
    Stream generation job progress using Server-Sent Events (SSE).

    This endpoint streams real-time updates about the generation progress.
    The client should connect using an EventSource or similar SSE client.
    """
    async def event_generator():
        """Generate SSE events for job progress."""
        last_status = None

        # Stream updates until job is complete or failed
        for _ in range(300):  # Max 5 minutes (300 * 1 second)
            try:
                status = content_generator_service.get_job_status(job_id)

                if not status:
                    yield f"data: {json.dumps({'error': 'Job not found'})}\n\n"
                    break

                # Only send if status changed
                if status != last_status:
                    yield f"data: {json.dumps(status)}\n\n"
                    last_status = status

                # Stop streaming if job is complete or failed
                if status["status"] in ["completed", "failed"]:
                    break

                await asyncio.sleep(1)  # Poll every second

            except Exception as e:
                logger.error(f"Error streaming job progress: {e}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                break

        # Send final done event
        yield "data: {\"done\": true}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable proxy buffering
        }
    )


@router.get("/content/{content_id}", response_model=GeneratedContentResponse)
async def get_generated_content(
    content_id: int,
    include_sources: bool = Query(default=True, description="Include source documents")
):
    """
    Retrieve generated content by ID.

    Returns the full HTML content along with metadata and optionally source documents.
    """
    content = content_generator_service.get_generated_content(content_id, include_sources)

    if not content:
        raise HTTPException(status_code=404, detail="Content not found")

    return GeneratedContentResponse(**content)


@router.get("/content", response_model=GeneratedContentList)
async def list_generated_content(
    content_type: Optional[str] = Query(None, description="Filter by content type"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    List all generated content with pagination.

    Optionally filter by content type (whitepaper, article, blog).
    """
    try:
        result = content_generator_service.list_generated_content(
            content_type=content_type,
            limit=limit,
            offset=offset
        )

        return GeneratedContentList(**result)

    except Exception as e:
        logger.error(f"Failed to list content: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/content/{content_id}", response_model=GeneratedContentResponse)
async def update_generated_content(content_id: int, updates: GeneratedContentUpdate):
    """
    Update generated content metadata.

    Allows updating the title, status, or content of generated content.
    """
    # TODO: Implement content update functionality
    raise HTTPException(status_code=501, detail="Content update not yet implemented")


@router.delete("/content/{content_id}")
async def delete_generated_content(content_id: int):
    """
    Delete generated content.

    Permanently removes the generated content from the database.
    """
    # TODO: Implement content deletion
    raise HTTPException(status_code=501, detail="Content deletion not yet implemented")


@router.post("/suggest-documents", response_model=DocumentSuggestResponse)
async def suggest_documents(request: DocumentSuggestRequest):
    """
    Get AI-powered document suggestions for a topic.

    Uses semantic search and LLM analysis to suggest relevant documents
    from the knowledge base for content generation.
    """
    try:
        suggested_docs = await document_selector_service.suggest_documents(
            topic=request.topic,
            content_type=request.content_type.value,
            max_documents=request.max_documents
        )

        return DocumentSuggestResponse(
            topic=request.topic,
            suggested_documents=[SuggestedDocument(**doc) for doc in suggested_docs],
            total_found=len(suggested_docs)
        )

    except Exception as e:
        logger.error(f"Failed to suggest documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Template Management Endpoints

@router.get("/templates", response_model=ContentTemplateList)
async def list_templates(
    content_type: Optional[str] = Query(None, description="Filter by content type")
):
    """
    List all available content templates.

    Optionally filter by content type to see only relevant templates.
    """
    try:
        templates = template_service.list_templates(
            content_type=content_type,
            include_private=False
        )

        return ContentTemplateList(
            templates=[ContentTemplateResponse(**t) for t in templates],
            total=len(templates)
        )

    except Exception as e:
        logger.error(f"Failed to list templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/{template_id}", response_model=ContentTemplateResponse)
async def get_template(template_id: int):
    """
    Get a specific template by ID.

    Returns the full template structure including sections and configuration.
    """
    template = template_service.get_template(template_id)

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return ContentTemplateResponse(**template)


@router.post("/templates", response_model=ContentTemplateResponse)
async def create_template(request: ContentTemplateCreate):
    """
    Create a new custom content template.

    Allows users to define custom templates with specific sections and configurations.
    """
    try:
        template = template_service.create_template(
            name=request.name,
            content_type=request.content_type.value,
            template_structure=request.template_structure,
            description=request.description,
            is_public=request.is_public
        )

        return ContentTemplateResponse(**template)

    except Exception as e:
        logger.error(f"Failed to create template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/templates/{template_id}", response_model=ContentTemplateResponse)
async def update_template(template_id: int, updates: ContentTemplateUpdate):
    """
    Update an existing template.

    Note: Default templates cannot be updated.
    """
    try:
        template = template_service.update_template(
            template_id=template_id,
            name=updates.name,
            description=updates.description,
            template_structure=updates.template_structure,
            is_public=updates.is_public
        )

        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        return ContentTemplateResponse(**template)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/templates/{template_id}")
async def delete_template(template_id: int):
    """
    Delete a custom template.

    Note: Default templates cannot be deleted.
    """
    try:
        success = template_service.delete_template(template_id)

        if not success:
            raise HTTPException(status_code=404, detail="Template not found")

        return {"message": "Template deleted successfully"}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete template: {e}")
        raise HTTPException(status_code=500, detail=str(e))
