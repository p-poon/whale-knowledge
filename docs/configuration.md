# Configuration Reference

Complete configuration guide for Whale Knowledge Base.

## Environment Variables

### Required Configuration

#### Database

**DATABASE_URL**
- **Type:** String (Connection URL)
- **Required:** Yes
- **Default:** None
- **Example:** `postgresql://whale_user:whale_pass@localhost:5432/whale_knowledge`
- **Description:** PostgreSQL connection string

#### Pinecone

**PINECONE_API_KEY**
- **Type:** String
- **Required:** Yes
- **Default:** None
- **Example:** `a1b2c3d4-e5f6-7890-abcd-ef1234567890`
- **Description:** Your Pinecone API key from [Pinecone console](https://www.pinecone.io/)

**PINECONE_ENVIRONMENT**
- **Type:** String
- **Required:** Yes
- **Default:** None
- **Example:** `us-west1-gcp`
- **Description:** Pinecone environment/region
- **Options:** `us-west1-gcp`, `us-east1-gcp`, `eu-west1-gcp`, etc.

**PINECONE_INDEX_NAME**
- **Type:** String
- **Required:** Yes
- **Default:** None
- **Example:** `whale-knowledge`
- **Description:** Name of your Pinecone index

### Optional Configuration

#### Jina Reader (Web Scraping)

**JINA_API_KEY**
- **Type:** String
- **Required:** No
- **Default:** None
- **Example:** `jina_abc123xyz456`
- **Description:** API key for Jina Reader web scraping
- **Get Key:** [https://jina.ai/](https://jina.ai/)

#### Embedding Model

**EMBEDDING_MODEL**
- **Type:** String
- **Required:** No
- **Default:** `sentence-transformers/all-MiniLM-L6-v2`
- **Description:** Sentence Transformers model name
- **Options:**
  - `sentence-transformers/all-MiniLM-L6-v2` - Fast, 384 dimensions
  - `sentence-transformers/all-mpnet-base-v2` - Better quality, 768 dimensions
  - `sentence-transformers/multi-qa-mpnet-base-dot-v1` - Q&A optimized, 768 dimensions

**EMBEDDING_DIMENSION**
- **Type:** Integer
- **Required:** No (must match model)
- **Default:** `384`
- **Description:** Embedding vector dimension
- **Note:** Must match your chosen model's output dimension

#### Chunking

**CHUNK_SIZE**
- **Type:** Integer
- **Required:** No
- **Default:** `512`
- **Range:** 100-2000
- **Description:** Number of characters per chunk
- **Recommendation:**
  - Small (256-512): Better precision, more chunks
  - Large (1000-2000): More context, fewer chunks

**CHUNK_OVERLAP**
- **Type:** Integer
- **Required:** No
- **Default:** `50`
- **Range:** 0-500
- **Description:** Overlapping characters between chunks
- **Recommendation:** 10-20% of chunk size

**CHUNKING_STRATEGY**
- **Type:** String
- **Required:** No
- **Default:** `fixed`
- **Options:**
  - `fixed` - Fixed character count
  - `sentence` - Split by sentences
  - `paragraph` - Split by paragraphs
- **Description:** Method for splitting documents

#### Application

**LOG_LEVEL**
- **Type:** String
- **Required:** No
- **Default:** `info`
- **Options:** `debug`, `info`, `warning`, `error`, `critical`
- **Description:** Logging verbosity

**MAX_UPLOAD_SIZE_MB**
- **Type:** Integer
- **Required:** No
- **Default:** `50`
- **Description:** Maximum PDF file size in megabytes

**CORS_ORIGINS**
- **Type:** String (comma-separated)
- **Required:** No
- **Default:** `*`
- **Example:** `https://yourdomain.com,https://app.yourdomain.com`
- **Description:** Allowed CORS origins

**API_KEY**
- **Type:** String
- **Required:** No (recommended for production)
- **Default:** None
- **Description:** API authentication key
- **Note:** If set, all requests must include `X-API-Key` header

## Configuration Files

### Backend Configuration

**Location:** `backend/app/core/config.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    database_url: str

    # Pinecone
    pinecone_api_key: str
    pinecone_environment: str
    pinecone_index_name: str

    # Jina (optional)
    jina_api_key: str | None = None

    # Embedding
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384

    # Chunking
    chunk_size: int = 512
    chunk_overlap: int = 50
    chunking_strategy: str = "fixed"

    # Application
    log_level: str = "info"
    max_upload_size_mb: int = 50
    cors_origins: str = "*"
    api_key: str | None = None

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

### Frontend Configuration

**Location:** `frontend/.env.local`

```bash
# API endpoint
NEXT_PUBLIC_API_URL=http://localhost:8000

# Optional: API key for authentication
NEXT_PUBLIC_API_KEY=your_api_key_here
```

### Docker Configuration

**Location:** `.env`

```bash
# PostgreSQL
POSTGRES_USER=whale_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=whale_knowledge

# Database URL
DATABASE_URL=postgresql://whale_user:your_secure_password@postgres:5432/whale_knowledge

# Pinecone
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENVIRONMENT=us-west1-gcp
PINECONE_INDEX_NAME=whale-knowledge

# Optional: Jina Reader
JINA_API_KEY=your_jina_api_key

# Embedding Model
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384

# Chunking
CHUNK_SIZE=512
CHUNK_OVERLAP=50
CHUNKING_STRATEGY=fixed

# Application
LOG_LEVEL=info
MAX_UPLOAD_SIZE_MB=50
```

## Embedding Model Options

### Recommended Models

#### 1. all-MiniLM-L6-v2 (Default)

**Best For:** Fast queries, limited resources

```bash
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384
```

**Specs:**
- Dimension: 384
- Model size: ~90 MB
- Speed: Very fast
- Quality: Good for general use

**Pros:**
- Fastest inference
- Smallest model size
- Good for CPU-only systems

**Cons:**
- Lower quality than larger models

#### 2. all-mpnet-base-v2

**Best For:** Better quality, moderate resources

```bash
EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2
EMBEDDING_DIMENSION=768
```

**Specs:**
- Dimension: 768
- Model size: ~420 MB
- Speed: Moderate
- Quality: High

**Pros:**
- Better semantic understanding
- More accurate results
- Good balance of speed/quality

**Cons:**
- 2x larger vectors (more storage)
- Slower than MiniLM

#### 3. multi-qa-mpnet-base-dot-v1

**Best For:** Question-answering scenarios

```bash
EMBEDDING_MODEL=sentence-transformers/multi-qa-mpnet-base-dot-v1
EMBEDDING_DIMENSION=768
```

**Specs:**
- Dimension: 768
- Model size: ~420 MB
- Speed: Moderate
- Quality: Optimized for Q&A

**Pros:**
- Best for question-answer pairs
- High quality for queries

**Cons:**
- Larger storage requirements
- Optimized for specific use case

### Changing Models

**Important:** Changing the embedding model requires rebuilding all vectors.

```bash
# 1. Update configuration
EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2
EMBEDDING_DIMENSION=768

# 2. Delete existing Pinecone index
# (Via Pinecone console or API)

# 3. Create new index with correct dimension
# (Via Pinecone console or API)

# 4. Restart backend
docker-compose restart backend

# 5. Re-upload all documents
# (Or run migration script)
```

## Chunking Strategies

### Fixed Size (Default)

Best for general use, consistent chunk sizes.

```bash
CHUNKING_STRATEGY=fixed
CHUNK_SIZE=512
CHUNK_OVERLAP=50
```

**Example:**
```
Document: "This is a long document with many sentences..."

Chunk 1: "This is a long document with many sent..." (512 chars)
Chunk 2: "...many sentences. The topic continues..." (512 chars, 50 char overlap)
```

### Sentence-Based

Best for maintaining sentence boundaries.

```bash
CHUNKING_STRATEGY=sentence
CHUNK_SIZE=5  # Number of sentences per chunk
CHUNK_OVERLAP=1  # Number of overlapping sentences
```

**Example:**
```
Document: "First sentence. Second sentence. Third sentence. Fourth sentence."

Chunk 1: "First sentence. Second sentence. Third sentence. Fourth sentence. Fifth sentence."
Chunk 2: "Fifth sentence. Sixth sentence. Seventh sentence. Eighth sentence. Ninth sentence."
```

### Paragraph-Based

Best for documents with clear paragraph structure.

```bash
CHUNKING_STRATEGY=paragraph
CHUNK_SIZE=2  # Number of paragraphs per chunk
CHUNK_OVERLAP=0  # Usually no overlap needed
```

**Example:**
```
Document with paragraphs separated by \n\n

Chunk 1: "Paragraph 1...\n\nParagraph 2..."
Chunk 2: "Paragraph 3...\n\nParagraph 4..."
```

## Performance Tuning

### Query Performance

**Increase top_k limit:**
```python
# backend/app/api/query.py
@app.post("/query/")
async def query(
    query: str,
    top_k: int = Query(default=5, le=50)  # Increase from 20 to 50
):
    pass
```

**Enable result caching:**
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_query(query: str, top_k: int):
    return retrieval_service.query(query, top_k)
```

### Database Performance

**Connection pooling:**
```python
# backend/app/core/database.py
engine = create_engine(
    DATABASE_URL,
    pool_size=20,        # Default: 5
    max_overflow=40,     # Default: 10
    pool_pre_ping=True,  # Check connections before use
    pool_recycle=3600    # Recycle connections after 1 hour
)
```

**Query optimization:**
```sql
-- Add indexes for common queries
CREATE INDEX idx_documents_industry ON documents(industry);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_created_at ON documents(created_at DESC);
CREATE INDEX idx_chunks_document_id ON chunks(document_id);
```

### Embedding Generation

**Batch processing:**
```python
# backend/app/services/embeddings.py
class EmbeddingService:
    def encode_batch(self, texts: List[str], batch_size: int = 32):
        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            embeddings.extend(self.model.encode(batch))
        return embeddings
```

**GPU acceleration:**
```python
# Requires PyTorch with CUDA
import torch

class EmbeddingService:
    def __init__(self):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = SentenceTransformer(model_name, device=device)
```

## Security Configuration

### API Authentication

**Enable API key authentication:**

```bash
# .env
API_KEY=your_secure_random_key_here
```

```python
# backend/app/main.py
from fastapi import Depends, Header, HTTPException

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_api_key

# Protect endpoints
@app.post("/query/", dependencies=[Depends(verify_api_key)])
async def query(request: QueryRequest):
    pass
```

### CORS Configuration

**Restrict origins:**

```bash
# .env
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

```python
# backend/app/main.py
from fastapi.middleware.cors import CORSMiddleware

origins = settings.cors_origins.split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)
```

### Rate Limiting

**Add rate limiting:**

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/query/")
@limiter.limit("10/minute")
async def query(request: Request, query: QueryRequest):
    pass
```

## Logging Configuration

### Python Logging

**Configure logging levels:**

```python
# backend/app/main.py
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
```

### Structured Logging

**Use JSON logging:**

```python
import json
import logging

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
        }
        return json.dumps(log_data)

handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logger.addHandler(handler)
```

## Monitoring Configuration

### Health Checks

**Custom health check:**

```python
# backend/app/api/stats.py
@app.get("/stats/health")
async def health_check():
    health = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

    # Check database
    try:
        db.execute("SELECT 1")
        health["database"] = "connected"
    except Exception as e:
        health["database"] = f"error: {str(e)}"
        health["status"] = "unhealthy"

    # Check Pinecone
    try:
        pinecone_client.describe_index()
        health["pinecone"] = "connected"
    except Exception as e:
        health["pinecone"] = f"error: {str(e)}"
        health["status"] = "unhealthy"

    # Check embedding model
    try:
        embedding_service.encode(["test"])
        health["embedding_model"] = "loaded"
    except Exception as e:
        health["embedding_model"] = f"error: {str(e)}"
        health["status"] = "unhealthy"

    status_code = 200 if health["status"] == "healthy" else 503
    return JSONResponse(content=health, status_code=status_code)
```

### Metrics Endpoint

**Expose Prometheus metrics:**

```python
from prometheus_client import Counter, Histogram, generate_latest

# Metrics
query_counter = Counter('query_total', 'Total queries')
query_duration = Histogram('query_duration_seconds', 'Query duration')

@app.post("/query/")
async def query(request: QueryRequest):
    query_counter.inc()

    with query_duration.time():
        results = await retrieval_service.query(request.query)

    return results

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type="text/plain")
```

## Example Configurations

### Development

```bash
# .env.development
DATABASE_URL=postgresql://whale_user:whale_pass@localhost:5432/whale_knowledge
PINECONE_API_KEY=your_dev_key
PINECONE_ENVIRONMENT=us-west1-gcp
PINECONE_INDEX_NAME=whale-knowledge-dev
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384
CHUNK_SIZE=512
CHUNK_OVERLAP=50
LOG_LEVEL=debug
CORS_ORIGINS=*
```

### Staging

```bash
# .env.staging
DATABASE_URL=postgresql://whale_user:secure_pass@staging-db:5432/whale_knowledge
PINECONE_API_KEY=your_staging_key
PINECONE_ENVIRONMENT=us-west1-gcp
PINECONE_INDEX_NAME=whale-knowledge-staging
EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2
EMBEDDING_DIMENSION=768
CHUNK_SIZE=512
CHUNK_OVERLAP=50
LOG_LEVEL=info
CORS_ORIGINS=https://staging.yourdomain.com
API_KEY=staging_api_key
```

### Production

```bash
# .env.production
DATABASE_URL=postgresql://whale_user:strong_pass@prod-db:5432/whale_knowledge
PINECONE_API_KEY=your_prod_key
PINECONE_ENVIRONMENT=us-west1-gcp
PINECONE_INDEX_NAME=whale-knowledge-prod
EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2
EMBEDDING_DIMENSION=768
CHUNK_SIZE=512
CHUNK_OVERLAP=50
LOG_LEVEL=info
MAX_UPLOAD_SIZE_MB=100
CORS_ORIGINS=https://yourdomain.com
API_KEY=production_api_key
```

## Troubleshooting Configuration

### Check Current Configuration

```python
# Python script to check config
from backend.app.core.config import settings

print(f"Database URL: {settings.database_url}")
print(f"Pinecone Index: {settings.pinecone_index_name}")
print(f"Embedding Model: {settings.embedding_model}")
print(f"Chunk Size: {settings.chunk_size}")
```

### Validate Configuration

```bash
# Run validation script
python -m backend.app.core.validate_config
```

### Common Issues

**Issue:** Model dimension mismatch
```
Error: Pinecone index dimension (384) doesn't match model dimension (768)
```

**Solution:** Ensure `EMBEDDING_DIMENSION` matches your model:
- all-MiniLM-L6-v2: 384
- all-mpnet-base-v2: 768

**Issue:** Database connection failed
```
Error: could not connect to server: Connection refused
```

**Solution:** Check `DATABASE_URL` and ensure PostgreSQL is running.

**Issue:** Pinecone authentication failed
```
Error: Invalid API key
```

**Solution:** Verify `PINECONE_API_KEY` is correct and active.

## Next Steps

- Review [Architecture](architecture.md) to understand how configuration affects the system
- See [Deployment](deployment.md) for production configuration examples
- Check [API Reference](api-reference.md) for API-specific configuration
- Read [Getting Started](getting-started.md) for basic setup
