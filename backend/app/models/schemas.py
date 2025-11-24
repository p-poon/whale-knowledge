from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class SourceType(str, Enum):
    """Source type for documents."""
    PDF = "pdf"
    WEB = "web"
    MARKDOWN = "markdown"


class DocumentStatus(str, Enum):
    """Processing status for documents."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"


class JobStatus(str, Enum):
    """Status for processing jobs."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentCreate(BaseModel):
    """Schema for creating a new document."""
    filename: str
    source_type: SourceType
    source_url: Optional[str] = None
    industry: Optional[str] = None
    author: Optional[str] = None
    document_date: Optional[datetime] = None
    auto_refresh: bool = False
    refresh_interval_days: int = 30


class DocumentUpload(BaseModel):
    """Schema for document upload with content."""
    filename: str
    content: str  # Base64 encoded for PDFs, or raw text
    source_type: SourceType
    industry: Optional[str] = None
    author: Optional[str] = None
    document_date: Optional[datetime] = None


class WebScrapRequest(BaseModel):
    """Schema for web scraping request."""
    url: HttpUrl
    industry: Optional[str] = None
    author: Optional[str] = None
    save_as_markdown: bool = True
    skip_existing: bool = True


class DocumentResponse(BaseModel):
    """Schema for document response."""
    id: int
    filename: str
    source_type: str
    source_url: Optional[str]
    industry: Optional[str]
    author: Optional[str]
    document_date: Optional[datetime]
    status: str
    chunk_count: int
    created_at: datetime
    updated_at: datetime
    last_refreshed_at: Optional[datetime]

    class Config:
        from_attributes = True


class DocumentList(BaseModel):
    """Schema for paginated document list."""
    documents: List[DocumentResponse]
    total: int
    page: int
    page_size: int


class ChunkResponse(BaseModel):
    """Schema for document chunk."""
    chunk_id: str
    document_id: int
    content: str
    chunk_index: int
    metadata: Dict[str, Any]


class QueryRequest(BaseModel):
    """Schema for knowledge base query."""
    query: str = Field(..., min_length=1, max_length=10000)
    top_k: int = Field(default=5, ge=1, le=50)
    filters: Optional[Dict[str, Any]] = None
    include_metadata: bool = True


class QueryResult(BaseModel):
    """Schema for a single query result."""
    document_id: int
    chunk_id: str
    content: str
    score: float
    metadata: Dict[str, Any]


class QueryResponse(BaseModel):
    """Schema for query response."""
    query: str
    results: List[QueryResult]
    total_results: int
    processing_time_ms: float


class EvaluationCreate(BaseModel):
    """Schema for creating evaluation result."""
    query: str
    retrieved_doc_ids: List[int]
    user_feedback: Optional[str] = None  # 'positive', 'negative'
    expected_doc_ids: Optional[List[int]] = None


class EvaluationResponse(BaseModel):
    """Schema for evaluation result."""
    id: int
    query: str
    retrieved_doc_ids: List[int]
    semantic_similarity: Optional[Dict[str, float]]
    user_feedback: Optional[str]
    precision: Optional[float]
    recall: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


class EvaluationMetrics(BaseModel):
    """Schema for aggregated evaluation metrics."""
    total_queries: int
    avg_precision: Optional[float]
    avg_recall: Optional[float]
    avg_semantic_similarity: Optional[float]
    positive_feedback_rate: Optional[float]
    negative_feedback_rate: Optional[float]


class ProcessingJobResponse(BaseModel):
    """Schema for processing job."""
    id: int
    document_id: Optional[int]
    job_type: str
    status: str
    progress: int
    message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class RefreshRequest(BaseModel):
    """Schema for document refresh request."""
    document_ids: List[int]


class SettingsUpdate(BaseModel):
    """Schema for updating application settings."""
    auto_process_enabled: Optional[bool] = None
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None


class HealthResponse(BaseModel):
    """Schema for health check response."""
    status: str
    database: str
    pinecone: str
    embedding_model: str


class StatsResponse(BaseModel):
    """Schema for knowledge base statistics."""
    total_documents: int
    total_chunks: int
    documents_by_status: Dict[str, int]
    documents_by_industry: Dict[str, int]
    pinecone_stats: Dict[str, Any]
