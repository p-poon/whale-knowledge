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

    # LLM API Keys
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None

    # LLM Settings
    default_llm_provider: str = "anthropic"  # 'anthropic' or 'openai'
    default_llm_model: Optional[str] = None  # If None, use provider default
    anthropic_default_model: str = "claude-3-5-sonnet-20241022"
    openai_default_model: str = "gpt-4-turbo-preview"

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

    # LLM Pricing (per 1M tokens)
    anthropic_claude_35_sonnet_input_cost: float = 3.00  # $3 per 1M input tokens
    anthropic_claude_35_sonnet_output_cost: float = 15.00  # $15 per 1M output tokens
    openai_gpt4_turbo_input_cost: float = 10.00  # $10 per 1M input tokens
    openai_gpt4_turbo_output_cost: float = 30.00  # $30 per 1M output tokens
    openai_gpt35_turbo_input_cost: float = 0.50  # $0.50 per 1M input tokens
    openai_gpt35_turbo_output_cost: float = 1.50  # $1.50 per 1M output tokens

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
