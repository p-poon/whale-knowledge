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


# API Usage Audit Schemas
class ServiceType(str, Enum):
    """Service type for API usage audit."""
    JINA = "jina"
    PINECONE = "pinecone"
    ANTHROPIC = "anthropic"
    OPENAI = "openai"


class AuditStatus(str, Enum):
    """Status for API usage audit."""
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"


class APIUsageAuditResponse(BaseModel):
    """Schema for API usage audit response."""
    id: int
    service: str
    operation: str
    request_id: str

    # JINA metrics
    jina_input_chars: Optional[int] = None
    jina_output_chars: Optional[int] = None
    jina_estimated_tokens: Optional[int] = None
    jina_response_headers: Optional[Dict[str, Any]] = None

    # Pinecone metrics
    pinecone_operation: Optional[str] = None
    pinecone_vector_count: Optional[int] = None
    pinecone_dimension: Optional[int] = None
    pinecone_namespace: Optional[str] = None
    pinecone_read_units: Optional[int] = None
    pinecone_write_units: Optional[int] = None

    # Associated entities
    document_id: Optional[int] = None
    user_id: Optional[str] = None

    # Status
    status: str
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UsageSummary(BaseModel):
    """Schema for aggregated usage summary."""
    service: str
    operation: str
    total_calls: int
    successful_calls: int
    failed_calls: int

    # JINA totals
    total_jina_tokens: Optional[int] = None
    total_jina_input_chars: Optional[int] = None
    total_jina_output_chars: Optional[int] = None

    # Pinecone totals
    total_pinecone_vectors: Optional[int] = None
    total_read_units: Optional[int] = None
    total_write_units: Optional[int] = None

    # Timing
    avg_duration_ms: Optional[float] = None
    min_duration_ms: Optional[int] = None
    max_duration_ms: Optional[int] = None


class UsageStatsResponse(BaseModel):
    """Schema for overall usage statistics."""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    summaries: List[UsageSummary]
    total_api_calls: int

    # Cost estimates
    estimated_jina_cost: Optional[float] = None
    estimated_pinecone_cost: Optional[float] = None
    estimated_total_cost: Optional[float] = None


class CostEstimate(BaseModel):
    """Schema for cost estimation."""
    jina_tokens_used: int
    jina_cost: float
    pinecone_read_units: int
    pinecone_write_units: int
    pinecone_read_cost: float
    pinecone_write_cost: float
    total_cost: float
    period_start: datetime
    period_end: datetime


# AI Agent Content Generation Schemas
class ContentType(str, Enum):
    """Type of content to generate."""
    WHITEPAPER = "whitepaper"
    ARTICLE = "article"
    BLOG = "blog"


class LLMProvider(str, Enum):
    """LLM provider for content generation."""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"


class GenerationStatus(str, Enum):
    """Status of content generation job."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class GenerationCustomization(BaseModel):
    """Customization options for content generation."""
    style: Optional[str] = "professional"  # formal, conversational, technical, professional
    tone: Optional[str] = "neutral"  # neutral, enthusiastic, analytical, authoritative
    audience: Optional[str] = "general"  # executives, technical, general, academic
    length: Optional[str] = "medium"  # short, medium, long
    target_word_count: Optional[int] = None
    sections: Optional[List[str]] = None  # Custom section names
    citation_style: Optional[str] = "inline"  # inline, footnotes, references
    include_executive_summary: Optional[bool] = True
    include_conclusion: Optional[bool] = True
    include_references: Optional[bool] = True


class GenerationRequest(BaseModel):
    """Request to generate content."""
    topic: str = Field(..., min_length=10, max_length=2000)
    content_type: ContentType
    document_ids: List[int] = Field(..., min_items=1)  # Selected documents to use
    llm_provider: LLMProvider = LLMProvider.ANTHROPIC
    llm_model: Optional[str] = None  # If None, use default for provider
    customization: Optional[GenerationCustomization] = GenerationCustomization()
    template_id: Optional[int] = None  # Optional template to use


class GenerationJobResponse(BaseModel):
    """Response after creating a generation job."""
    job_id: str
    status: str
    message: str

    class Config:
        from_attributes = True


class GenerationJobStatus(BaseModel):
    """Status of a generation job."""
    job_id: str
    status: str
    progress_percent: int
    current_step: Optional[str]
    result_id: Optional[int]
    error_message: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class GeneratedContentResponse(BaseModel):
    """Response with generated content."""
    id: int
    title: str
    content_type: str
    content_html: str
    content_markdown: Optional[str]
    topic: str
    llm_provider: str
    llm_model: str
    generation_params: Optional[Dict[str, Any]]
    status: str
    token_usage: Optional[Dict[str, Any]]
    cost_estimate: Optional[float]
    created_at: datetime
    updated_at: datetime
    source_documents: Optional[List[Dict[str, Any]]] = None

    class Config:
        from_attributes = True


class GeneratedContentList(BaseModel):
    """Paginated list of generated content."""
    content: List[GeneratedContentResponse]
    total: int
    page: int
    page_size: int


class GeneratedContentUpdate(BaseModel):
    """Update generated content."""
    title: Optional[str] = None
    status: Optional[str] = None
    content_html: Optional[str] = None
    content_markdown: Optional[str] = None


class DocumentSuggestRequest(BaseModel):
    """Request for AI-suggested documents."""
    topic: str = Field(..., min_length=10, max_length=2000)
    content_type: ContentType
    max_documents: int = Field(default=5, ge=1, le=20)


class SuggestedDocument(BaseModel):
    """A suggested document with relevance score."""
    document_id: int
    filename: str
    relevance_score: float
    relevance_explanation: Optional[str]
    chunk_count: int
    industry: Optional[str]
    author: Optional[str]


class DocumentSuggestResponse(BaseModel):
    """Response with suggested documents."""
    topic: str
    suggested_documents: List[SuggestedDocument]
    total_found: int


class ContentTemplateCreate(BaseModel):
    """Schema for creating a content template."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    content_type: ContentType
    template_structure: Dict[str, Any]
    is_public: bool = True


class ContentTemplateResponse(BaseModel):
    """Response with content template."""
    id: int
    name: str
    description: Optional[str]
    content_type: str
    template_structure: Dict[str, Any]
    is_default: bool
    is_public: bool
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ContentTemplateList(BaseModel):
    """List of content templates."""
    templates: List[ContentTemplateResponse]
    total: int


class ContentTemplateUpdate(BaseModel):
    """Update content template."""
    name: Optional[str] = None
    description: Optional[str] = None
    template_structure: Optional[Dict[str, Any]] = None
    is_public: Optional[bool] = None
