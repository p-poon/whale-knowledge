"""Service for tracking and analyzing API usage."""
import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, Integer

from app.core.database import APIUsageAudit
from app.core.config import settings
from app.models.schemas import (
    APIUsageAuditResponse,
    UsageSummary,
    UsageStatsResponse,
    CostEstimate
)

logger = logging.getLogger(__name__)


class AuditService:
    """Service for logging and analyzing API usage."""

    def log_api_usage(
        self,
        db: Session,
        service: str,
        operation: str,
        status: str = "success",
        endpoint: Optional[str] = None,
        # JINA fields
        jina_input_chars: Optional[int] = None,
        jina_output_chars: Optional[int] = None,
        jina_estimated_tokens: Optional[int] = None,
        jina_response_headers: Optional[Dict[str, Any]] = None,
        # Pinecone fields
        pinecone_operation: Optional[str] = None,
        pinecone_vector_count: Optional[int] = None,
        pinecone_dimension: Optional[int] = None,
        pinecone_namespace: Optional[str] = None,
        pinecone_read_units: Optional[int] = None,
        pinecone_write_units: Optional[int] = None,
        # Common fields
        document_id: Optional[int] = None,
        user_id: Optional[str] = None,
        error_message: Optional[str] = None,
        duration_ms: Optional[int] = None
    ) -> APIUsageAudit:
        """
        Log an API usage event to the audit table.

        Args:
            db: Database session
            service: Service name ('jina' or 'pinecone')
            operation: Operation name ('scrape', 'query', 'upsert', etc.)
            status: Operation status ('success', 'failed', 'timeout')
            ... (other fields as documented in APIUsageAudit model)

        Returns:
            The created audit record
        """
        try:
            audit_record = APIUsageAudit(
                request_id=str(uuid.uuid4()),
                service=service,
                operation=operation,
                status=status,
                endpoint=endpoint,
                # JINA
                jina_input_chars=jina_input_chars,
                jina_output_chars=jina_output_chars,
                jina_estimated_tokens=jina_estimated_tokens,
                jina_response_headers=jina_response_headers,
                # Pinecone
                pinecone_operation=pinecone_operation,
                pinecone_vector_count=pinecone_vector_count,
                pinecone_dimension=pinecone_dimension,
                pinecone_namespace=pinecone_namespace,
                pinecone_read_units=pinecone_read_units,
                pinecone_write_units=pinecone_write_units,
                # Common
                document_id=document_id,
                user_id=user_id,
                error_message=error_message,
                duration_ms=duration_ms
            )

            db.add(audit_record)
            db.commit()
            db.refresh(audit_record)

            logger.info(f"Logged {service} {operation} usage: request_id={audit_record.request_id}")
            return audit_record

        except Exception as e:
            logger.error(f"Failed to log API usage: {e}")
            db.rollback()
            # Don't raise - audit logging should not break the main flow
            return None

    def get_usage_history(
        self,
        db: Session,
        service: Optional[str] = None,
        operation: Optional[str] = None,
        status: Optional[str] = None,
        document_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[APIUsageAudit]:
        """
        Get detailed usage history with filters.

        Args:
            db: Database session
            service: Filter by service ('jina' or 'pinecone')
            operation: Filter by operation
            status: Filter by status
            document_id: Filter by document ID
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Max number of records
            offset: Offset for pagination

        Returns:
            List of audit records
        """
        query = db.query(APIUsageAudit)

        if service:
            query = query.filter(APIUsageAudit.service == service)
        if operation:
            query = query.filter(APIUsageAudit.operation == operation)
        if status:
            query = query.filter(APIUsageAudit.status == status)
        if document_id:
            query = query.filter(APIUsageAudit.document_id == document_id)
        if start_date:
            query = query.filter(APIUsageAudit.created_at >= start_date)
        if end_date:
            query = query.filter(APIUsageAudit.created_at <= end_date)

        query = query.order_by(APIUsageAudit.created_at.desc())
        query = query.offset(offset).limit(limit)

        return query.all()

    def get_usage_summary(
        self,
        db: Session,
        service: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> UsageStatsResponse:
        """
        Get aggregated usage statistics.

        Args:
            db: Database session
            service: Filter by service
            start_date: Filter by start date
            end_date: Filter by end date

        Returns:
            Aggregated usage statistics
        """
        query = db.query(APIUsageAudit)

        if service:
            query = query.filter(APIUsageAudit.service == service)
        if start_date:
            query = query.filter(APIUsageAudit.created_at >= start_date)
        if end_date:
            query = query.filter(APIUsageAudit.created_at <= end_date)

        # Get summaries grouped by service and operation
        summaries_query = db.query(
            APIUsageAudit.service,
            APIUsageAudit.operation,
            func.count(APIUsageAudit.id).label('total_calls'),
            func.sum(func.cast(APIUsageAudit.status == 'success', Integer)).label('successful_calls'),
            func.sum(func.cast(APIUsageAudit.status != 'success', Integer)).label('failed_calls'),
            # JINA aggregations
            func.sum(APIUsageAudit.jina_estimated_tokens).label('total_jina_tokens'),
            func.sum(APIUsageAudit.jina_input_chars).label('total_jina_input_chars'),
            func.sum(APIUsageAudit.jina_output_chars).label('total_jina_output_chars'),
            # Pinecone aggregations
            func.sum(APIUsageAudit.pinecone_vector_count).label('total_pinecone_vectors'),
            func.sum(APIUsageAudit.pinecone_read_units).label('total_read_units'),
            func.sum(APIUsageAudit.pinecone_write_units).label('total_write_units'),
            # Timing aggregations
            func.avg(APIUsageAudit.duration_ms).label('avg_duration_ms'),
            func.min(APIUsageAudit.duration_ms).label('min_duration_ms'),
            func.max(APIUsageAudit.duration_ms).label('max_duration_ms')
        ).group_by(
            APIUsageAudit.service,
            APIUsageAudit.operation
        )

        if service:
            summaries_query = summaries_query.filter(APIUsageAudit.service == service)
        if start_date:
            summaries_query = summaries_query.filter(APIUsageAudit.created_at >= start_date)
        if end_date:
            summaries_query = summaries_query.filter(APIUsageAudit.created_at <= end_date)

        results = summaries_query.all()

        summaries = []
        total_jina_cost = 0.0
        total_pinecone_cost = 0.0
        total_api_calls = 0

        for row in results:
            summary = UsageSummary(
                service=row.service,
                operation=row.operation,
                total_calls=row.total_calls or 0,
                successful_calls=row.successful_calls or 0,
                failed_calls=row.failed_calls or 0,
                total_jina_tokens=row.total_jina_tokens,
                total_jina_input_chars=row.total_jina_input_chars,
                total_jina_output_chars=row.total_jina_output_chars,
                total_pinecone_vectors=row.total_pinecone_vectors,
                total_read_units=row.total_read_units,
                total_write_units=row.total_write_units,
                avg_duration_ms=float(row.avg_duration_ms) if row.avg_duration_ms else None,
                min_duration_ms=row.min_duration_ms,
                max_duration_ms=row.max_duration_ms
            )
            summaries.append(summary)
            total_api_calls += row.total_calls or 0

            # Calculate costs
            if row.service == 'jina' and row.total_jina_tokens:
                total_jina_cost += (row.total_jina_tokens / 1000.0) * settings.jina_cost_per_1k_tokens

            if row.service == 'pinecone':
                if row.total_read_units:
                    total_pinecone_cost += row.total_read_units * settings.pinecone_read_unit_cost
                if row.total_write_units:
                    total_pinecone_cost += row.total_write_units * settings.pinecone_write_unit_cost

        return UsageStatsResponse(
            start_date=start_date,
            end_date=end_date,
            summaries=summaries,
            total_api_calls=total_api_calls,
            estimated_jina_cost=total_jina_cost if total_jina_cost > 0 else None,
            estimated_pinecone_cost=total_pinecone_cost if total_pinecone_cost > 0 else None,
            estimated_total_cost=total_jina_cost + total_pinecone_cost
        )

    def get_cost_estimate(
        self,
        db: Session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> CostEstimate:
        """
        Calculate cost estimates based on usage.

        Args:
            db: Database session
            start_date: Start date for calculation
            end_date: End date for calculation

        Returns:
            Cost estimate breakdown
        """
        # Default to last 30 days if no dates provided
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        query = db.query(APIUsageAudit).filter(
            APIUsageAudit.created_at >= start_date,
            APIUsageAudit.created_at <= end_date
        )

        # JINA costs
        jina_tokens = db.query(
            func.sum(APIUsageAudit.jina_estimated_tokens)
        ).filter(
            APIUsageAudit.service == 'jina',
            APIUsageAudit.created_at >= start_date,
            APIUsageAudit.created_at <= end_date
        ).scalar() or 0

        jina_cost = (jina_tokens / 1000.0) * settings.jina_cost_per_1k_tokens

        # Pinecone costs
        pinecone_reads = db.query(
            func.sum(APIUsageAudit.pinecone_read_units)
        ).filter(
            APIUsageAudit.service == 'pinecone',
            APIUsageAudit.created_at >= start_date,
            APIUsageAudit.created_at <= end_date
        ).scalar() or 0

        pinecone_writes = db.query(
            func.sum(APIUsageAudit.pinecone_write_units)
        ).filter(
            APIUsageAudit.service == 'pinecone',
            APIUsageAudit.created_at >= start_date,
            APIUsageAudit.created_at <= end_date
        ).scalar() or 0

        pinecone_read_cost = pinecone_reads * settings.pinecone_read_unit_cost
        pinecone_write_cost = pinecone_writes * settings.pinecone_write_unit_cost

        return CostEstimate(
            jina_tokens_used=jina_tokens,
            jina_cost=round(jina_cost, 4),
            pinecone_read_units=pinecone_reads,
            pinecone_write_units=pinecone_writes,
            pinecone_read_cost=round(pinecone_read_cost, 4),
            pinecone_write_cost=round(pinecone_write_cost, 4),
            total_cost=round(jina_cost + pinecone_read_cost + pinecone_write_cost, 4),
            period_start=start_date,
            period_end=end_date
        )


# Singleton instance
_audit_service = None

def get_audit_service() -> AuditService:
    """Get or create the audit service singleton."""
    global _audit_service
    if _audit_service is None:
        _audit_service = AuditService()
    return _audit_service
