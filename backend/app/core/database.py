from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, JSON, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import AsyncGenerator
import asyncpg

from app.core.config import settings

# SQLAlchemy setup
SQLALCHEMY_DATABASE_URL = settings.database_url

engine = create_engine(SQLALCHEMY_DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://"))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class Document(Base):
    """Document metadata stored in PostgreSQL."""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    content_hash = Column(String, unique=True, index=True)
    source_type = Column(String, nullable=False)  # 'pdf', 'web', 'markdown'
    source_url = Column(String, nullable=True)

    # Metadata/Tagging
    industry = Column(String, nullable=True, index=True)
    author = Column(String, nullable=True, index=True)
    document_date = Column(DateTime, nullable=True)

    # Content
    raw_content_path = Column(String, nullable=True)  # Path to markdown file
    chunk_count = Column(Integer, default=0)

    # Processing status
    status = Column(String, default="pending")  # pending, processing, completed, error
    error_message = Column(Text, nullable=True)

    # Pinecone vectors
    vector_ids = Column(JSON, nullable=True)  # List of Pinecone vector IDs

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    last_refreshed_at = Column(DateTime, nullable=True)

    # Settings
    auto_refresh = Column(Boolean, default=False)
    refresh_interval_days = Column(Integer, default=30)


class EvaluationResult(Base):
    """Evaluation results for retrieval quality."""
    __tablename__ = "evaluation_results"

    id = Column(Integer, primary_key=True, index=True)
    query = Column(Text, nullable=False)
    retrieved_doc_ids = Column(JSON, nullable=False)  # List of document IDs

    # Metrics
    semantic_similarity = Column(JSON, nullable=True)  # Dict of scores
    user_feedback = Column(String, nullable=True)  # 'positive', 'negative', None

    # Ground truth (for automated eval)
    expected_doc_ids = Column(JSON, nullable=True)
    precision = Column(JSON, nullable=True)
    recall = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())


class ProcessingJob(Base):
    """Track document processing jobs."""
    __tablename__ = "processing_jobs"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, nullable=True)
    job_type = Column(String, nullable=False)  # 'ingest', 'refresh', 'reindex'
    status = Column(String, default="queued")  # queued, running, completed, failed

    progress = Column(Integer, default=0)  # 0-100
    message = Column(Text, nullable=True)

    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class APIUsageAudit(Base):
    """Track API usage for JINA and Pinecone services."""
    __tablename__ = "api_usage_audit"

    id = Column(Integer, primary_key=True, index=True)

    # Service identification
    service = Column(String, nullable=False, index=True)  # 'jina', 'pinecone', 'anthropic', 'openai'
    operation = Column(String, nullable=False, index=True)  # 'scrape', 'query', 'upsert', 'delete', 'llm_generation'

    # Request details
    request_id = Column(String, unique=True, index=True)  # UUID for tracking
    endpoint = Column(String, nullable=True)  # API endpoint called

    # Usage metrics - JINA
    jina_input_chars = Column(Integer, nullable=True)
    jina_output_chars = Column(Integer, nullable=True)
    jina_estimated_tokens = Column(Integer, nullable=True)
    jina_response_headers = Column(JSON, nullable=True)  # Store all headers

    # Usage metrics - Pinecone
    pinecone_operation = Column(String, nullable=True)  # 'read', 'write', 'delete'
    pinecone_vector_count = Column(Integer, nullable=True)
    pinecone_dimension = Column(Integer, nullable=True)
    pinecone_namespace = Column(String, nullable=True)
    pinecone_read_units = Column(Integer, nullable=True)  # Estimated
    pinecone_write_units = Column(Integer, nullable=True)  # Estimated

    # Usage metrics - LLM (Anthropic/OpenAI)
    llm_provider = Column(String, nullable=True)  # 'anthropic', 'openai'
    llm_model = Column(String, nullable=True)  # Model name
    llm_input_tokens = Column(Integer, nullable=True)
    llm_output_tokens = Column(Integer, nullable=True)
    llm_total_tokens = Column(Integer, nullable=True)
    llm_cost_estimate = Column(Float, nullable=True)  # Estimated cost in USD

    # Associated entities
    document_id = Column(Integer, nullable=True, index=True)
    generated_content_id = Column(Integer, nullable=True, index=True)
    user_id = Column(String, nullable=True, index=True)  # For future multi-user

    # Status and timing
    status = Column(String, default="success")  # success, failed, timeout
    error_message = Column(Text, nullable=True)
    duration_ms = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), index=True)


class GeneratedContent(Base):
    """Store AI-generated content (white papers, articles, blogs)."""
    __tablename__ = "generated_content"

    id = Column(Integer, primary_key=True, index=True)

    # Content details
    title = Column(String, nullable=False)
    content_type = Column(String, nullable=False, index=True)  # 'whitepaper', 'article', 'blog'
    content_html = Column(Text, nullable=False)  # HTML formatted content
    content_markdown = Column(Text, nullable=True)  # Markdown version (optional)

    # Generation details
    topic = Column(Text, nullable=False)  # Original topic/prompt
    llm_provider = Column(String, nullable=False)  # 'anthropic', 'openai'
    llm_model = Column(String, nullable=False)  # Model name used
    generation_params = Column(JSON, nullable=True)  # Store customization settings

    # Metadata
    status = Column(String, default="completed")  # completed, draft, archived
    token_usage = Column(JSON, nullable=True)  # {input_tokens, output_tokens, total_tokens}
    cost_estimate = Column(Float, nullable=True)  # Estimated generation cost in USD

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    source_documents = relationship("GenerationSourceDocument", back_populates="generated_content", cascade="all, delete-orphan")


class GenerationJob(Base):
    """Track async content generation jobs."""
    __tablename__ = "generation_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, unique=True, index=True, nullable=False)  # UUID for tracking

    # Job details
    topic = Column(Text, nullable=False)
    content_type = Column(String, nullable=False)  # 'whitepaper', 'article', 'blog'
    status = Column(String, default="pending", index=True)  # pending, processing, completed, failed
    progress_percent = Column(Integer, default=0)  # 0-100
    current_step = Column(String, nullable=True)  # Current generation step description

    # Generation configuration
    llm_provider = Column(String, nullable=False)
    llm_model = Column(String, nullable=False)
    generation_params = Column(JSON, nullable=True)
    selected_document_ids = Column(JSON, nullable=True)  # List of document IDs to use

    # Result
    result_id = Column(Integer, ForeignKey("generated_content.id"), nullable=True)  # Link to generated content
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)


class ContentTemplate(Base):
    """Store custom content templates."""
    __tablename__ = "content_templates"

    id = Column(Integer, primary_key=True, index=True)

    # Template details
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    content_type = Column(String, nullable=False, index=True)  # 'whitepaper', 'article', 'blog'

    # Template structure (JSON defining sections, prompts, etc.)
    template_structure = Column(JSON, nullable=False)
    # Example: {
    #   "sections": [
    #     {"name": "Executive Summary", "prompt": "...", "max_words": 200},
    #     {"name": "Introduction", "prompt": "...", "max_words": 500}
    #   ],
    #   "style": "formal",
    #   "citation_style": "inline"
    # }

    # Metadata
    is_default = Column(Boolean, default=False)  # System default template
    is_public = Column(Boolean, default=True)  # Available to all users (future)
    created_by = Column(String, nullable=True)  # User ID (future)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class GenerationSourceDocument(Base):
    """Many-to-many relationship between generated content and source documents."""
    __tablename__ = "generation_source_documents"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    generation_id = Column(Integer, ForeignKey("generated_content.id"), nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)

    # Relevance score for this document
    relevance_score = Column(Float, nullable=True)
    chunks_used = Column(Integer, nullable=True)  # Number of chunks from this document used

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    generated_content = relationship("GeneratedContent", back_populates="source_documents")


# Database initialization
def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Async PostgreSQL connection pool
_pool = None

async def get_pool():
    """Get or create asyncpg connection pool."""
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            settings.database_url,
            min_size=5,
            max_size=20
        )
    return _pool


async def close_pool():
    """Close database connection pool."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
