# Architecture

Understanding the Whale Knowledge Base system architecture.

## System Overview

Whale Knowledge Base is a modern, microservices-based RAG (Retrieval-Augmented Generation) system designed for scalability and extensibility.

```
┌─────────────────────────────────────────────────────────────┐
│                   Client Applications                        │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │   Web UI     │ │  AI Agents   │ │   REST API   │        │
│  │  (Next.js)   │ │    (MCP)     │ │   Clients    │        │
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘        │
└─────────┼────────────────┼────────────────┼────────────────┘
          │                │                │
          │ HTTP/REST      │ stdio (MCP)    │ HTTP/REST
          │                │                │
┌─────────▼────────────────▼────────────────▼────────────────┐
│                   Application Layer                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │               FastAPI Backend                        │   │
│  │                                                      │   │
│  │  ┌──────────────────────────────────────────────┐   │   │
│  │  │            API Endpoints                    │   │   │
│  │  │  • Documents  • Query  • Evaluation  • Stats │   │   │
│  │  └────────────┬─────────────────────────────────┘   │   │
│  │               │                                      │   │
│  │  ┌────────────▼─────────────────────────────────┐   │   │
│  │  │           Service Layer                      │   │   │
│  │  │  • DocumentService  • RetrievalService      │   │   │
│  │  │  • EmbeddingService  • EvaluationService    │   │   │
│  │  └────────────┬─────────────────────────────────┘   │   │
│  │               │                                      │   │
│  │  ┌────────────▼─────────────────────────────────┐   │   │
│  │  │         Core Services                        │   │   │
│  │  │  • PDF Processing  • Web Scraping           │   │   │
│  │  │  • Chunking  • Embeddings  • Vector Storage │   │   │
│  │  └──────────────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │               MCP Server                             │   │
│  │  Tools: query, add_document, list, delete            │   │
│  │  Resources: kb://stats, kb://config                  │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────┬──────────────┬──────────────┬─────────┘
                     │              │              │
                     │              │              │
┌────────────────────▼──────────────▼──────────────▼─────────┐
│                   Data Layer                                 │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │  PostgreSQL  │ │   Pinecone   │ │  Jina Reader │        │
│  │   Metadata   │ │    Vectors   │ │  Web Scraper │        │
│  │   Documents  │ │  Embeddings  │ │  (External)  │        │
│  │  Evaluations │ │   Indexes    │ │              │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### Frontend (Next.js)

**Technology:** Next.js 14 with App Router, TypeScript, Tailwind CSS

**Responsibilities:**
- User interface for document management
- Interactive query interface
- Real-time statistics dashboard
- Evaluation metrics visualization

**Key Files:**
- `src/app/page.tsx` - Main application page
- `src/components/DocumentUpload.tsx` - Document upload interface
- `src/components/ChatInterface.tsx` - Query interface
- `src/components/EvaluationDashboard.tsx` - Metrics visualization
- `src/lib/api.ts` - API client

**Communication:**
- REST API calls to backend
- SWR for data fetching and caching
- Real-time updates via polling

### Backend (FastAPI)

**Technology:** Python 3.11+, FastAPI, asyncio

**Responsibilities:**
- RESTful API endpoints
- Document processing orchestration
- Semantic search execution
- Evaluation metrics calculation
- MCP server implementation

#### API Endpoints Layer

Located in `backend/app/api/`

**documents.py** - Document management
- Upload PDF files
- Scrape URLs
- List documents
- Get document details
- Delete documents

**query.py** - Search functionality
- Semantic search execution
- Result ranking
- Metadata filtering

**evaluation.py** - Quality metrics
- Create evaluations
- Submit feedback
- Calculate precision/recall
- Aggregate metrics

**stats.py** - System statistics
- Document counts
- Query metrics
- Health checks
- Storage statistics

#### Service Layer

Located in `backend/app/services/`

**document_service.py** - Document orchestration
```python
class DocumentService:
    async def create_document(...)  # Create DB record
    async def process_pdf(...)      # Extract and chunk PDF
    async def process_url(...)      # Scrape and chunk URL
    async def store_embeddings(...) # Generate and store vectors
    async def delete_document(...)  # Remove doc and vectors
```

**retrieval.py** - Search execution
```python
class RetrievalService:
    async def query(...)            # Semantic search
    async def rerank_results(...)   # Score adjustment
    async def filter_by_metadata(...) # Apply filters
```

**embeddings.py** - Vector generation
```python
class EmbeddingService:
    def __init__(model_name)        # Load model
    def encode(texts)               # Generate embeddings
    def encode_batch(texts)         # Batch processing
```

**evaluation.py** - Quality measurement
```python
class EvaluationService:
    def calculate_precision(...)    # Precision metric
    def calculate_recall(...)       # Recall metric
    def calculate_semantic_score(...) # Similarity score
    def aggregate_metrics(...)      # Overall metrics
```

**pdf_processor.py** - PDF handling
```python
class PDFProcessor:
    def extract_text(pdf_file)      # Extract text
    def extract_metadata(...)       # Get PDF metadata
    def validate_pdf(...)           # File validation
```

**jina_scraper.py** - Web scraping
```python
class JinaScraper:
    async def scrape_url(url)       # Fetch content
    def convert_to_markdown(...)    # Format conversion
    def extract_title(...)          # Get page title
```

**chunking.py** - Text segmentation
```python
class ChunkingService:
    def chunk_text(text, strategy)  # Split text
    def fixed_size_chunks(...)      # Fixed-size strategy
    def sentence_chunks(...)        # Sentence-based strategy
    def paragraph_chunks(...)       # Paragraph-based strategy
```

#### Core Layer

Located in `backend/app/core/`

**database.py** - Database connection
```python
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(...)
Base = declarative_base()

def get_db():  # Dependency injection
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**pinecone_client.py** - Vector database
```python
class PineconeClient:
    def __init__(api_key, environment)
    def get_index(index_name)
    def upsert_vectors(...)
    def query_vectors(...)
    def delete_vectors(...)
```

**config.py** - Configuration management
```python
class Settings(BaseSettings):
    database_url: str
    pinecone_api_key: str
    pinecone_environment: str
    pinecone_index_name: str
    embedding_model: str
    embedding_dimension: int
    chunk_size: int
    chunk_overlap: int
```

### MCP Server

**Technology:** Python MCP SDK

**Responsibilities:**
- Expose tools to AI agents
- Provide read-only resources
- Handle stdio communication
- Format responses for agents

**Tools Implemented:**
- `query_knowledge_base` - Search documents
- `add_document_from_url` - Add new content
- `list_documents` - Browse documents
- `delete_document` - Remove documents

**Resources Provided:**
- `kb://stats` - System statistics
- `kb://config` - Configuration details

**Communication:**
- stdio (standard input/output)
- JSON-RPC 2.0 protocol
- Structured tool schemas

### Data Layer

#### PostgreSQL

**Purpose:** Relational data storage

**Schema:**

**documents table:**
```sql
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    source_type VARCHAR(50),  -- 'pdf' or 'url'
    source_url TEXT,
    status VARCHAR(50),       -- 'processing', 'completed', 'failed'
    industry VARCHAR(100),
    author VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB
);
```

**chunks table:**
```sql
CREATE TABLE chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER,
    content TEXT,
    vector_id VARCHAR(255),   -- Pinecone vector ID
    created_at TIMESTAMP DEFAULT NOW()
);
```

**evaluations table:**
```sql
CREATE TABLE evaluations (
    id SERIAL PRIMARY KEY,
    query TEXT,
    expected_doc_ids INTEGER[],
    retrieved_doc_ids INTEGER[],
    precision FLOAT,
    recall FLOAT,
    avg_semantic_score FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**feedback table:**
```sql
CREATE TABLE feedback (
    id SERIAL PRIMARY KEY,
    query TEXT,
    document_id INTEGER REFERENCES documents(id),
    feedback VARCHAR(20),     -- 'positive' or 'negative'
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### Pinecone

**Purpose:** Vector similarity search

**Index Configuration:**
- Dimension: 384 (for all-MiniLM-L6-v2)
- Metric: Cosine similarity
- Pod type: Serverless or p1.x1 (starter)

**Vector Metadata:**
```json
{
  "document_id": 123,
  "chunk_index": 0,
  "title": "Document Title",
  "industry": "Healthcare",
  "author": "John Doe",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Query Example:**
```python
results = index.query(
    vector=query_embedding,
    top_k=5,
    include_metadata=True,
    filter={"industry": "Healthcare"}
)
```

#### Jina Reader API

**Purpose:** Web content extraction

**Endpoint:** `https://r.jina.ai/`

**Usage:**
```python
url = f"https://r.jina.ai/{target_url}"
response = requests.get(url, headers={"Authorization": f"Bearer {api_key}"})
markdown_content = response.text
```

**Features:**
- Converts HTML to clean markdown
- Removes ads and navigation
- Extracts main content
- Preserves structure

## Data Flow

### Document Upload Flow

```
1. User uploads PDF
   ↓
2. API endpoint receives file
   ↓
3. DocumentService creates DB record (status: 'processing')
   ↓
4. PDFProcessor extracts text
   ↓
5. ChunkingService splits into chunks
   ↓
6. EmbeddingService generates vectors
   ↓
7. PineconeClient stores vectors with metadata
   ↓
8. DocumentService updates DB (status: 'completed')
   ↓
9. Frontend receives success response
```

### URL Scraping Flow

```
1. User provides URL
   ↓
2. API endpoint receives request
   ↓
3. DocumentService creates DB record (status: 'processing')
   ↓
4. JinaScraper fetches content
   ↓
5. Content converted to markdown
   ↓
6. ChunkingService splits into chunks
   ↓
7. EmbeddingService generates vectors
   ↓
8. PineconeClient stores vectors with metadata
   ↓
9. DocumentService updates DB (status: 'completed')
   ↓
10. Frontend receives success response
```

### Query Flow

```
1. User enters query
   ↓
2. API endpoint receives request
   ↓
3. EmbeddingService generates query vector
   ↓
4. RetrievalService queries Pinecone
   ↓
5. Pinecone returns similar vectors with metadata
   ↓
6. RetrievalService fetches chunk content from DB
   ↓
7. Results ranked by similarity score
   ↓
8. Metadata filters applied
   ↓
9. Frontend displays results
```

### MCP Query Flow

```
1. AI agent sends query via MCP
   ↓
2. MCP server receives tool call
   ↓
3. Server invokes query_knowledge_base tool
   ↓
4. Same flow as regular query
   ↓
5. Results formatted for AI agent
   ↓
6. MCP server returns structured response
   ↓
7. AI agent processes and presents to user
```

## Scalability Considerations

### Horizontal Scaling

**Backend:**
- Stateless design allows multiple instances
- Load balancer distributes requests
- Each instance connects to shared DB and Pinecone

**Database:**
- PostgreSQL read replicas for queries
- Connection pooling (SQLAlchemy)
- Prepared statements

**Pinecone:**
- Automatically scales with serverless
- Or increase pod size/replicas

### Vertical Scaling

**Backend:**
- Increase CPU for embedding generation
- More memory for larger models
- SSD for faster file processing

**Database:**
- More memory for caching
- Faster storage for queries
- Increase connection limit

### Caching Strategy

**Embedding Cache:**
```python
# Cache frequently used embeddings
embedding_cache = {}

def get_embedding(text):
    if text in embedding_cache:
        return embedding_cache[text]
    embedding = model.encode(text)
    embedding_cache[text] = embedding
    return embedding
```

**Query Results Cache:**
```python
# Cache common queries with TTL
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_query(query, top_k):
    return retrieve_documents(query, top_k)
```

**Database Query Cache:**
- PostgreSQL query cache
- Application-level caching with Redis

## Performance Optimization

### Backend Optimization

**Async/Await:**
```python
# Concurrent document processing
async def process_multiple_documents(files):
    tasks = [process_document(f) for f in files]
    return await asyncio.gather(*tasks)
```

**Batch Processing:**
```python
# Batch embedding generation
embeddings = embedding_service.encode_batch(
    texts, batch_size=32
)
```

**Connection Pooling:**
```python
# Reuse database connections
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40
)
```

### Frontend Optimization

**Code Splitting:**
```javascript
// Lazy load components
const EvaluationDashboard = dynamic(
  () => import('./EvaluationDashboard'),
  { ssr: false }
)
```

**Data Caching:**
```javascript
// SWR for efficient data fetching
const { data, error } = useSWR('/api/documents', fetcher, {
  revalidateOnFocus: false,
  dedupingInterval: 10000
})
```

**Image Optimization:**
```javascript
// Next.js Image component
<Image src="/logo.png" width={200} height={50} />
```

## Security Architecture

### API Security

**Input Validation:**
- Pydantic models for type safety
- File size limits
- Content type validation

**Rate Limiting:**
```python
# Add rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request, call_next):
    # Implement rate limiting logic
    return await call_next(request)
```

**CORS:**
```python
# Restrict origins in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)
```

### Data Security

**Database:**
- Encrypted connections (SSL)
- Password hashing
- Parameterized queries (SQL injection prevention)

**API Keys:**
- Environment variables only
- Never commit to git
- Rotate regularly

**Vector Metadata:**
- No sensitive data in metadata
- Sanitize before storage
- Access controls

## Monitoring and Observability

### Logging

```python
import logging

logger = logging.getLogger(__name__)

@app.post("/query/")
async def query(request: QueryRequest):
    logger.info(f"Query received: {request.query}")
    # Process query
    logger.info(f"Query completed in {elapsed}ms")
```

### Metrics

**Track:**
- Query latency
- Document processing time
- Error rates
- Cache hit rates
- Database connection pool usage

**Tools:**
- Prometheus for metrics collection
- Grafana for visualization
- Sentry for error tracking

### Health Checks

```python
@app.get("/stats/health")
async def health_check():
    return {
        "status": "healthy",
        "database": check_db_connection(),
        "pinecone": check_pinecone_connection(),
        "embedding_model": check_model_loaded()
    }
```

## Technology Choices

### Why FastAPI?

- High performance (async/await)
- Auto-generated OpenAPI docs
- Pydantic validation
- Modern Python features
- Easy testing

### Why Pinecone?

- Fully managed vector database
- High performance similarity search
- Metadata filtering
- Scalable infrastructure
- Simple API

### Why PostgreSQL?

- Reliable relational database
- JSONB for flexible metadata
- Full-text search capabilities
- Strong consistency
- Proven at scale

### Why Next.js?

- Server-side rendering
- File-based routing
- API routes
- Image optimization
- Modern React features

### Why Sentence Transformers?

- Pre-trained models
- Easy to use
- Good quality embeddings
- CPU-friendly
- Multiple model options

## Extension Points

### Adding New Document Sources

1. Create processor in `services/`
2. Add API endpoint in `api/documents.py`
3. Update `DocumentService` to handle new type
4. Add UI component

### Custom Embedding Models

1. Update `EMBEDDING_MODEL` in config
2. Update `EMBEDDING_DIMENSION`
3. Recreate Pinecone index
4. Rebuild embeddings

### Additional MCP Tools

1. Define tool schema in `mcp_server.py`
2. Implement tool handler
3. Add to tool list
4. Document usage

### New Chunking Strategies

1. Add method to `ChunkingService`
2. Update API to accept strategy parameter
3. Add tests
4. Document strategy

## Next Steps

- Review [Configuration](configuration.md) for customization options
- See [Deployment](deployment.md) for production setup
- Check [API Reference](api-reference.md) for endpoint details
- Read [MCP Integration](mcp-integration.md) for AI agent setup
