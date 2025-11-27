# API Reference

Complete reference for the Whale Knowledge Base REST API.

## Base URL

When running locally:
```
http://localhost:8000
```

## Interactive Documentation

The API includes auto-generated interactive documentation:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Authentication

Currently, the API does not require authentication. For production deployments, implement authentication using:
- API keys
- JWT tokens
- OAuth 2.0

See [Deployment Guide](deployment.md) for security best practices.

## Documents API

### Upload PDF

Upload a PDF document for processing and indexing.

**Endpoint:** `POST /documents/upload/pdf`

**Request:**
```bash
curl -X POST "http://localhost:8000/documents/upload/pdf" \
  -F "file=@document.pdf" \
  -F "industry=Healthcare" \
  -F "author=John Doe" \
  -F "chunk_size=512" \
  -F "chunk_overlap=50"
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| file | file | Yes | PDF file to upload |
| industry | string | No | Industry category (e.g., "Healthcare", "Tech") |
| author | string | No | Document author |
| chunk_size | integer | No | Characters per chunk (default: 512) |
| chunk_overlap | integer | No | Overlap between chunks (default: 50) |

**Response:** `200 OK`
```json
{
  "id": 123,
  "title": "document.pdf",
  "source_type": "pdf",
  "status": "processing",
  "industry": "Healthcare",
  "author": "John Doe",
  "created_at": "2024-01-15T10:30:00Z",
  "metadata": {}
}
```

### Scrape URL

Scrape and index content from a website URL.

**Endpoint:** `POST /documents/scrape`

**Request:**
```bash
curl -X POST "http://localhost:8000/documents/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/article",
    "industry": "Technology",
    "author": "Jane Smith",
    "chunk_size": 512,
    "chunk_overlap": 50
  }'
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| url | string | Yes | URL to scrape |
| industry | string | No | Industry category |
| author | string | No | Content author |
| chunk_size | integer | No | Characters per chunk (default: 512) |
| chunk_overlap | integer | No | Overlap between chunks (default: 50) |

**Response:** `200 OK`
```json
{
  "id": 124,
  "title": "Article Title",
  "source_type": "url",
  "source_url": "https://example.com/article",
  "status": "completed",
  "industry": "Technology",
  "author": "Jane Smith",
  "created_at": "2024-01-15T10:35:00Z",
  "chunk_count": 15,
  "metadata": {}
}
```

### List Documents

Retrieve a list of all documents with optional filtering.

**Endpoint:** `GET /documents/`

**Request:**
```bash
curl "http://localhost:8000/documents/?industry=Healthcare&limit=20&offset=0"
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| industry | string | No | Filter by industry |
| author | string | No | Filter by author |
| status | string | No | Filter by status (processing, completed, failed) |
| limit | integer | No | Number of results (default: 100) |
| offset | integer | No | Pagination offset (default: 0) |

**Response:** `200 OK`
```json
[
  {
    "id": 123,
    "title": "document.pdf",
    "source_type": "pdf",
    "status": "completed",
    "industry": "Healthcare",
    "author": "John Doe",
    "created_at": "2024-01-15T10:30:00Z",
    "chunk_count": 25
  },
  {
    "id": 124,
    "title": "Article Title",
    "source_type": "url",
    "status": "completed",
    "industry": "Technology",
    "author": "Jane Smith",
    "created_at": "2024-01-15T10:35:00Z",
    "chunk_count": 15
  }
]
```

### Get Document

Retrieve details for a specific document.

**Endpoint:** `GET /documents/{document_id}`

**Request:**
```bash
curl "http://localhost:8000/documents/123"
```

**Response:** `200 OK`
```json
{
  "id": 123,
  "title": "document.pdf",
  "source_type": "pdf",
  "source_url": null,
  "status": "completed",
  "industry": "Healthcare",
  "author": "John Doe",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:31:00Z",
  "chunk_count": 25,
  "metadata": {
    "file_size": 1024000,
    "page_count": 10
  }
}
```

### Delete Document

Delete a document and all its associated chunks.

**Endpoint:** `DELETE /documents/{document_id}`

**Request:**
```bash
curl -X DELETE "http://localhost:8000/documents/123"
```

**Response:** `200 OK`
```json
{
  "message": "Document deleted successfully",
  "document_id": 123,
  "chunks_deleted": 25
}
```

## Query API

### Query Knowledge Base

Search the knowledge base using semantic similarity.

**Endpoint:** `POST /query/`

**Request:**
```bash
curl -X POST "http://localhost:8000/query/" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the benefits of machine learning?",
    "top_k": 5,
    "filters": {
      "industry": "Technology"
    },
    "min_score": 0.7
  }'
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| query | string | Yes | Search query text |
| top_k | integer | No | Number of results (default: 5, max: 20) |
| filters | object | No | Metadata filters (industry, author) |
| min_score | float | No | Minimum similarity score (0.0-1.0) |

**Response:** `200 OK`
```json
{
  "query": "What are the benefits of machine learning?",
  "results": [
    {
      "chunk_id": "doc-123-chunk-5",
      "document_id": 123,
      "document_title": "ML Guide",
      "score": 0.89,
      "content": "Machine learning provides numerous benefits including automated pattern recognition...",
      "metadata": {
        "industry": "Technology",
        "author": "John Doe",
        "page": 5
      }
    },
    {
      "chunk_id": "doc-124-chunk-3",
      "document_id": 124,
      "document_title": "AI Handbook",
      "score": 0.82,
      "content": "The advantages of ML systems include improved accuracy, scalability...",
      "metadata": {
        "industry": "Technology",
        "author": "Jane Smith"
      }
    }
  ],
  "query_time_ms": 156
}
```

### Test Query

Quick test endpoint with a pre-defined query.

**Endpoint:** `GET /query/test`

**Request:**
```bash
curl "http://localhost:8000/query/test"
```

**Response:** `200 OK`
```json
{
  "query": "test query",
  "results": [...],
  "query_time_ms": 120
}
```

## Evaluation API

### Create Evaluation

Create a new evaluation record with ground truth for testing.

**Endpoint:** `POST /evaluation/`

**Request:**
```bash
curl -X POST "http://localhost:8000/evaluation/" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is machine learning?",
    "expected_doc_ids": [123, 124],
    "retrieved_doc_ids": [123, 124, 125],
    "semantic_scores": [0.89, 0.82, 0.75]
  }'
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| query | string | Yes | Search query |
| expected_doc_ids | array | Yes | Expected document IDs (ground truth) |
| retrieved_doc_ids | array | Yes | Actually retrieved document IDs |
| semantic_scores | array | Yes | Similarity scores for retrieved docs |

**Response:** `200 OK`
```json
{
  "evaluation_id": 456,
  "precision": 0.67,
  "recall": 1.0,
  "avg_semantic_score": 0.82,
  "created_at": "2024-01-15T11:00:00Z"
}
```

### Submit Feedback

Submit user feedback (thumbs up/down) for a query result.

**Endpoint:** `POST /evaluation/feedback`

**Request:**
```bash
curl -X POST "http://localhost:8000/evaluation/feedback" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is machine learning?",
    "document_id": 123,
    "feedback": "positive"
  }'
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| query | string | Yes | Original search query |
| document_id | integer | Yes | Document that received feedback |
| feedback | string | Yes | "positive" or "negative" |

**Response:** `200 OK`
```json
{
  "message": "Feedback recorded",
  "feedback_id": 789
}
```

### Get Metrics

Retrieve aggregated evaluation metrics.

**Endpoint:** `GET /evaluation/metrics`

**Request:**
```bash
curl "http://localhost:8000/evaluation/metrics?days=30"
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| days | integer | No | Number of days to include (default: 30) |

**Response:** `200 OK`
```json
{
  "total_queries": 1500,
  "avg_precision": 0.78,
  "avg_recall": 0.85,
  "avg_semantic_score": 0.82,
  "positive_feedback_rate": 0.72,
  "negative_feedback_rate": 0.15,
  "no_feedback_rate": 0.13
}
```

### Get Evaluation History

Retrieve evaluation history with optional filtering.

**Endpoint:** `GET /evaluation/history`

**Request:**
```bash
curl "http://localhost:8000/evaluation/history?limit=50"
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| limit | integer | No | Number of results (default: 100) |
| offset | integer | No | Pagination offset (default: 0) |

**Response:** `200 OK`
```json
[
  {
    "id": 456,
    "query": "What is machine learning?",
    "precision": 0.67,
    "recall": 1.0,
    "avg_semantic_score": 0.82,
    "created_at": "2024-01-15T11:00:00Z"
  }
]
```

## Stats API

### Get Statistics

Retrieve system-wide statistics.

**Endpoint:** `GET /stats/`

**Request:**
```bash
curl "http://localhost:8000/stats/"
```

**Response:** `200 OK`
```json
{
  "total_documents": 150,
  "total_chunks": 3450,
  "total_queries": 1500,
  "avg_query_time_ms": 145,
  "total_storage_mb": 256,
  "documents_by_industry": {
    "Technology": 80,
    "Healthcare": 45,
    "Finance": 25
  },
  "documents_by_status": {
    "completed": 145,
    "processing": 3,
    "failed": 2
  }
}
```

### Health Check

Check system health and connectivity.

**Endpoint:** `GET /stats/health`

**Request:**
```bash
curl "http://localhost:8000/stats/health"
```

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "database": "connected",
  "pinecone": "connected",
  "embedding_model": "loaded",
  "version": "1.0.0",
  "uptime_seconds": 3600
}
```

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request

Invalid request parameters.

```json
{
  "detail": "Invalid query parameter: top_k must be between 1 and 20"
}
```

### 404 Not Found

Resource not found.

```json
{
  "detail": "Document with id 999 not found"
}
```

### 422 Unprocessable Entity

Validation error.

```json
{
  "detail": [
    {
      "loc": ["body", "query"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 500 Internal Server Error

Server error.

```json
{
  "detail": "Internal server error occurred"
}
```

## Rate Limiting

Currently, no rate limiting is enforced. For production deployments, implement rate limiting using:
- Nginx
- API Gateway
- FastAPI middleware

Recommended limits:
- 100 requests per minute per IP
- 1000 requests per hour per user

## CORS

Cross-Origin Resource Sharing (CORS) is configured to allow all origins in development. For production, restrict to specific domains:

```python
# backend/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Webhooks

Webhook support for document processing events (coming soon):

- `document.created`
- `document.completed`
- `document.failed`
- `query.executed`

## SDK Examples

### Python

```python
import requests

# Upload PDF
with open('document.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/documents/upload/pdf',
        files={'file': f},
        data={'industry': 'Healthcare'}
    )
    document = response.json()

# Query
response = requests.post(
    'http://localhost:8000/query/',
    json={
        'query': 'What is machine learning?',
        'top_k': 5
    }
)
results = response.json()
```

### JavaScript/TypeScript

```javascript
// Upload PDF
const formData = new FormData();
formData.append('file', file);
formData.append('industry', 'Healthcare');

const response = await fetch('http://localhost:8000/documents/upload/pdf', {
  method: 'POST',
  body: formData
});
const document = await response.json();

// Query
const response = await fetch('http://localhost:8000/query/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: 'What is machine learning?',
    top_k: 5
  })
});
const results = await response.json();
```

### cURL

```bash
# Upload PDF
curl -X POST "http://localhost:8000/documents/upload/pdf" \
  -F "file=@document.pdf" \
  -F "industry=Healthcare"

# Query
curl -X POST "http://localhost:8000/query/" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is machine learning?", "top_k": 5}'
```

## Next Steps

- Try the [Interactive API Docs](http://localhost:8000/docs)
- Learn about [MCP Integration](mcp-integration.md)
- Review [Architecture](architecture.md)
- Check [Configuration](configuration.md) options
