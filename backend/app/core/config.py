from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "postgresql://whale_user:whale_pass@localhost:5432/whale_knowledge"

    # Pinecone
    pinecone_api_key: str
    pinecone_environment: str = "us-west1-gcp"
    pinecone_index_name: str = "whale-knowledge"

    # Jina Reader
    jina_api_key: Optional[str] = None

    # Embedding Model
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384

    # Chunking
    chunk_size: int = 512
    chunk_overlap: int = 50

    # File Watcher
    auto_process_enabled: bool = False
    watch_directory: str = "./documents"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]

    # API Usage Pricing (for cost estimation)
    jina_cost_per_1k_tokens: float = 0.00005  # $0.050 per 1M tokens 
    pinecone_read_unit_cost: float = 0.00004  # $0.04 per 1M read units
    pinecone_write_unit_cost: float = 0.0002  # $0.20 per 1M write units

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
