from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
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
