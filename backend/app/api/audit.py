"""API endpoints for usage auditing and cost tracking."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta

from app.core.database import get_db
from app.services.audit_service import get_audit_service
from app.models.schemas import (
    APIUsageAuditResponse,
    UsageStatsResponse,
    CostEstimate
)

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/usage-history", response_model=List[APIUsageAuditResponse])
async def get_usage_history(
    service: Optional[str] = Query(None, description="Filter by service (jina or pinecone)"),
    operation: Optional[str] = Query(None, description="Filter by operation (scrape, query, upsert, etc.)"),
    status: Optional[str] = Query(None, description="Filter by status (success, failed, timeout)"),
    document_id: Optional[int] = Query(None, description="Filter by document ID"),
    start_date: Optional[datetime] = Query(None, description="Filter from start date"),
    end_date: Optional[datetime] = Query(None, description="Filter to end date"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db)
):
    """
    Get detailed usage history with filtering and pagination.

    Returns a list of audit records with all tracked metrics.
    """
    audit_service = get_audit_service()
    records = audit_service.get_usage_history(
        db=db,
        service=service,
        operation=operation,
        status=status,
        document_id=document_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset
    )

    return [APIUsageAuditResponse.from_orm(record) for record in records]


@router.get("/usage-summary", response_model=UsageStatsResponse)
async def get_usage_summary(
    service: Optional[str] = Query(None, description="Filter by service (jina or pinecone)"),
    start_date: Optional[datetime] = Query(None, description="Filter from start date"),
    end_date: Optional[datetime] = Query(None, description="Filter to end date"),
    db: Session = Depends(get_db)
):
    """
    Get aggregated usage statistics grouped by service and operation.

    Returns summary metrics including:
    - Total API calls
    - Success/failure counts
    - JINA token usage
    - Pinecone read/write units
    - Average response times
    - Cost estimates
    """
    audit_service = get_audit_service()
    return audit_service.get_usage_summary(
        db=db,
        service=service,
        start_date=start_date,
        end_date=end_date
    )


@router.get("/cost-estimate", response_model=CostEstimate)
async def get_cost_estimate(
    start_date: Optional[datetime] = Query(None, description="Start date for cost calculation"),
    end_date: Optional[datetime] = Query(None, description="End date for cost calculation"),
    db: Session = Depends(get_db)
):
    """
    Calculate cost estimates based on API usage.

    Returns detailed cost breakdown for JINA and Pinecone services.
    Defaults to last 30 days if no date range provided.
    """
    audit_service = get_audit_service()
    return audit_service.get_cost_estimate(
        db=db,
        start_date=start_date,
        end_date=end_date
    )


@router.get("/daily-stats")
async def get_daily_stats(
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    service: Optional[str] = Query(None, description="Filter by service"),
    db: Session = Depends(get_db)
):
    """
    Get daily usage statistics for charting.

    Returns aggregated metrics grouped by date for time-series visualization.
    """
    from sqlalchemy import func, cast, Date
    from app.core.database import APIUsageAudit

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    query = db.query(
        cast(APIUsageAudit.created_at, Date).label('date'),
        APIUsageAudit.service,
        func.count(APIUsageAudit.id).label('total_calls'),
        func.sum(APIUsageAudit.jina_estimated_tokens).label('jina_tokens'),
        func.sum(APIUsageAudit.pinecone_read_units).label('read_units'),
        func.sum(APIUsageAudit.pinecone_write_units).label('write_units')
    ).filter(
        APIUsageAudit.created_at >= start_date,
        APIUsageAudit.created_at <= end_date
    )

    if service:
        query = query.filter(APIUsageAudit.service == service)

    query = query.group_by(
        cast(APIUsageAudit.created_at, Date),
        APIUsageAudit.service
    ).order_by(cast(APIUsageAudit.created_at, Date))

    results = query.all()

    # Format results
    daily_stats = []
    for row in results:
        daily_stats.append({
            "date": row.date.isoformat(),
            "service": row.service,
            "total_calls": row.total_calls,
            "jina_tokens": row.jina_tokens,
            "read_units": row.read_units,
            "write_units": row.write_units
        })

    return {
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "days": days
        },
        "data": daily_stats
    }


@router.get("/top-documents")
async def get_top_documents_by_usage(
    limit: int = Query(10, ge=1, le=100, description="Number of documents to return"),
    service: Optional[str] = Query(None, description="Filter by service"),
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    db: Session = Depends(get_db)
):
    """
    Get documents with highest API usage.

    Returns documents ranked by number of API calls.
    """
    from sqlalchemy import func
    from app.core.database import APIUsageAudit, Document

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    query = db.query(
        APIUsageAudit.document_id,
        Document.filename,
        func.count(APIUsageAudit.id).label('api_calls'),
        func.sum(APIUsageAudit.jina_estimated_tokens).label('jina_tokens'),
        func.sum(APIUsageAudit.pinecone_read_units).label('read_units'),
        func.sum(APIUsageAudit.pinecone_write_units).label('write_units')
    ).join(
        Document,
        APIUsageAudit.document_id == Document.id
    ).filter(
        APIUsageAudit.document_id.isnot(None),
        APIUsageAudit.created_at >= start_date,
        APIUsageAudit.created_at <= end_date
    )

    if service:
        query = query.filter(APIUsageAudit.service == service)

    query = query.group_by(
        APIUsageAudit.document_id,
        Document.filename
    ).order_by(
        func.count(APIUsageAudit.id).desc()
    ).limit(limit)

    results = query.all()

    return {
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "days": days
        },
        "documents": [
            {
                "document_id": row.document_id,
                "filename": row.filename,
                "api_calls": row.api_calls,
                "jina_tokens": row.jina_tokens,
                "read_units": row.read_units,
                "write_units": row.write_units
            }
            for row in results
        ]
    }
