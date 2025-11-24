from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import base64
import tempfile
from pathlib import Path

from app.core.database import get_db, Document
from app.models.schemas import (
    DocumentResponse,
    DocumentList,
    WebScrapRequest,
)
from app.services.document_service import get_document_service

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload/pdf", response_model=DocumentResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    industry: Optional[str] = Form(None),
    author: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Upload and process a PDF document."""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    document_service = get_document_service()

    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_path = temp_file.name

    try:
        metadata = {
            "industry": industry,
            "author": author,
        }

        document = await document_service.process_pdf(
            db=db,
            file_path=temp_path,
            filename=file.filename,
            metadata=metadata
        )

        return document
    finally:
        # Clean up temp file
        Path(temp_path).unlink(missing_ok=True)


@router.post("/scrape", response_model=DocumentResponse)
async def scrape_url(
    request: WebScrapRequest,
    db: Session = Depends(get_db)
):
    """Scrape content from a URL and add to knowledge base."""
    document_service = get_document_service()

    metadata = {
        "industry": request.industry,
        "author": request.author,
    }

    document = await document_service.process_url(
        db=db,
        url=str(request.url),
        metadata=metadata
    )

    return document


@router.get("/", response_model=DocumentList)
async def list_documents(
    page: int = 1,
    page_size: int = 20,
    industry: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all documents with pagination and filters."""
    query = db.query(Document)

    # Apply filters
    if industry:
        query = query.filter(Document.industry == industry)
    if status:
        query = query.filter(Document.status == status)

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    documents = query.order_by(Document.created_at.desc()).offset(offset).limit(page_size).all()

    return {
        "documents": documents,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Get a single document by ID."""
    document = db.query(Document).filter(Document.id == document_id).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return document


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Delete a document from the knowledge base."""
    document_service = get_document_service()

    try:
        await document_service.delete_document(db, document_id)
        return {"message": "Document deleted successfully", "document_id": document_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}/content")
async def get_document_content(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Get the raw content of a document."""
    document = db.query(Document).filter(Document.id == document_id).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if not document.raw_content_path:
        raise HTTPException(status_code=404, detail="Content file not found")

    try:
        content_path = Path(document.raw_content_path)
        if not content_path.exists():
            raise HTTPException(status_code=404, detail="Content file not found")

        content = content_path.read_text(encoding="utf-8")
        return {
            "document_id": document_id,
            "filename": document.filename,
            "content": content
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
