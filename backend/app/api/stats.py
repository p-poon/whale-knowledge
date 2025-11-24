from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, text

from app.core.database import get_db, Document
from app.core.pinecone_client import pinecone_client
from app.models.schemas import StatsResponse, HealthResponse
from app.core.config import settings

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """Check health of all services."""
    try:
        # Check database
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    # Check Pinecone
    try:
        await pinecone_client.get_stats()
        pinecone_status = "healthy"
    except Exception as e:
        pinecone_status = f"unhealthy: {str(e)}"

    overall_status = "healthy" if db_status == "healthy" and pinecone_status == "healthy" else "degraded"

    return {
        "status": overall_status,
        "database": db_status,
        "pinecone": pinecone_status,
        "embedding_model": settings.embedding_model
    }


@router.get("/", response_model=StatsResponse)
async def get_stats(db: Session = Depends(get_db)):
    """Get knowledge base statistics."""
    try:
        # Total documents
        total_documents = db.query(func.count(Document.id)).scalar()

        # Total chunks
        total_chunks = db.query(func.sum(Document.chunk_count)).scalar() or 0

        # Documents by status
        status_counts = db.query(
            Document.status,
            func.count(Document.id)
        ).group_by(Document.status).all()

        documents_by_status = {status: count for status, count in status_counts}

        # Documents by industry
        industry_counts = db.query(
            Document.industry,
            func.count(Document.id)
        ).filter(Document.industry.isnot(None)).group_by(Document.industry).all()

        documents_by_industry = {industry: count for industry, count in industry_counts}

        # Pinecone stats
        try:
            pinecone_stats = await pinecone_client.get_stats()
        except Exception as e:
            pinecone_stats = {"error": str(e)}

        return {
            "total_documents": total_documents,
            "total_chunks": int(total_chunks),
            "documents_by_status": documents_by_status,
            "documents_by_industry": documents_by_industry,
            "pinecone_stats": pinecone_stats
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")
