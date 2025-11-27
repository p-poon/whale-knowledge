# Quick Reference

Fast reference for common operations in Whale Knowledge Base.

## Table of Contents

- [Installation](#installation)
- [API Endpoints](#api-endpoints)
- [Docker Commands](#docker-commands)
- [Configuration](#configuration)
- [MCP Commands](#mcp-commands)
- [Database Operations](#database-operations)
- [Troubleshooting](#troubleshooting)

## Installation

### Docker (Recommended)

```bash
# Clone and setup
git clone https://github.com/your-org/whale-knowledge.git
cd whale-knowledge
cp .env.example .env
# Edit .env with your API keys

# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### Manual Setup

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

## API Endpoints

### Documents

```bash
# Upload PDF
curl -X POST "http://localhost:8000/documents/upload/pdf" \
  -F "file=@document.pdf" \
  -F "industry=Technology"

# Scrape URL
curl -X POST "http://localhost:8000/documents/scrape" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "industry": "Tech"}'

# List documents
curl "http://localhost:8000/documents/"

# Get document
curl "http://localhost:8000/documents/123"

# Delete document
curl -X DELETE "http://localhost:8000/documents/123"
```

### Query

```bash
# Basic query
curl -X POST "http://localhost:8000/query/" \
  -H "Content-Type: application/json" \
  -d '{"query": "machine learning", "top_k": 5}'

# Query with filters
curl -X POST "http://localhost:8000/query/" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning",
    "top_k": 5,
    "filters": {"industry": "Technology"},
    "min_score": 0.7
  }'
```

### Stats

```bash
# Get statistics
curl "http://localhost:8000/stats/"

# Health check
curl "http://localhost:8000/stats/health"
```

### Evaluation

```bash
# Submit feedback
curl -X POST "http://localhost:8000/evaluation/feedback" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning",
    "document_id": 123,
    "feedback": "positive"
  }'

# Get metrics
curl "http://localhost:8000/evaluation/metrics"
```

## Docker Commands

### Basic Operations

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart services
docker-compose restart

# Rebuild and start
docker-compose up -d --build

# View logs (all services)
docker-compose logs -f

# View logs (specific service)
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

### Service Management

```bash
# Start specific service
docker-compose up -d backend

# Stop specific service
docker-compose stop backend

# Restart specific service
docker-compose restart backend

# Remove containers (keeps volumes)
docker-compose down

# Remove containers and volumes
docker-compose down -v
```

### Debugging

```bash
# Execute command in container
docker exec -it whale-backend bash
docker exec -it whale-frontend sh
docker exec -it whale-postgres psql -U whale_user whale_knowledge

# Check container status
docker ps
docker-compose ps

# View container resources
docker stats

# Inspect container
docker inspect whale-backend
```

## Configuration

### Environment Variables

```bash
# Required
DATABASE_URL=postgresql://whale_user:pass@localhost:5432/whale_knowledge
PINECONE_API_KEY=your_key
PINECONE_ENVIRONMENT=us-west1-gcp
PINECONE_INDEX_NAME=whale-knowledge

# Optional
JINA_API_KEY=your_jina_key
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384
CHUNK_SIZE=512
CHUNK_OVERLAP=50
LOG_LEVEL=info
```

### Embedding Models

```bash
# Fast (default)
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384

# Better quality
EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2
EMBEDDING_DIMENSION=768

# Q&A optimized
EMBEDDING_MODEL=sentence-transformers/multi-qa-mpnet-base-dot-v1
EMBEDDING_DIMENSION=768
```

## MCP Commands

### Setup

```bash
# macOS configuration location
~/Library/Application Support/Claude/claude_desktop_config.json

# Add MCP server
{
  "mcpServers": {
    "whale-knowledge": {
      "command": "python",
      "args": ["-m", "app.mcp_server"],
      "cwd": "/path/to/whale-knowledge/backend",
      "env": {
        "DATABASE_URL": "postgresql://...",
        "PINECONE_API_KEY": "..."
      }
    }
  }
}
```

### Usage in Claude

```
# Query knowledge base
Use whale-knowledge to search for "artificial intelligence"

# Add document
Add https://example.com/article to whale-knowledge

# List documents
Show me all documents in whale-knowledge

# Delete document
Delete document 123 from whale-knowledge
```

### Testing

```bash
# Test MCP server
cd backend
python -m app.mcp_server

# Check Claude Desktop logs (macOS)
tail -f ~/Library/Logs/Claude/mcp*.log
```

## Database Operations

### PostgreSQL

```bash
# Connect to database
docker exec -it whale-postgres psql -U whale_user whale_knowledge

# List tables
\dt

# View documents
SELECT id, title, status, industry FROM documents;

# View chunks
SELECT document_id, COUNT(*) FROM chunks GROUP BY document_id;

# View evaluations
SELECT * FROM evaluations ORDER BY created_at DESC LIMIT 10;
```

### Backup

```bash
# Backup database
docker exec whale-postgres pg_dump -U whale_user whale_knowledge > backup.sql

# Restore database
docker exec -i whale-postgres psql -U whale_user whale_knowledge < backup.sql

# Backup with compression
docker exec whale-postgres pg_dump -U whale_user whale_knowledge | gzip > backup.sql.gz

# Restore from compressed backup
gunzip -c backup.sql.gz | docker exec -i whale-postgres psql -U whale_user whale_knowledge
```

### Maintenance

```bash
# Vacuum database
docker exec whale-postgres vacuumdb -U whale_user -d whale_knowledge -z

# Reindex
docker exec whale-postgres reindexdb -U whale_user whale_knowledge

# Check database size
docker exec whale-postgres psql -U whale_user whale_knowledge -c "
  SELECT pg_size_pretty(pg_database_size('whale_knowledge'));
"
```

## Troubleshooting

### Services Won't Start

```bash
# Check ports
lsof -i :3000  # Frontend
lsof -i :8000  # Backend
lsof -i :5432  # PostgreSQL

# View detailed logs
docker-compose logs --tail=100 backend
docker-compose logs --tail=100 postgres

# Check Docker resources
docker system df
docker system prune  # Clean up unused resources
```

### Database Connection Issues

```bash
# Test connection
docker exec whale-postgres pg_isready -U whale_user

# Check PostgreSQL logs
docker logs whale-postgres

# Verify environment variables
docker exec whale-backend env | grep DATABASE_URL

# Restart database
docker-compose restart postgres
```

### Pinecone Issues

```bash
# Test Pinecone connection
curl -X GET "http://localhost:8000/stats/health"

# Check API key
echo $PINECONE_API_KEY

# Verify in Python
docker exec whale-backend python -c "
from pinecone import Pinecone
pc = Pinecone(api_key='your_key')
print(pc.list_indexes())
"
```

### Performance Issues

```bash
# Check container resources
docker stats

# View slow queries (PostgreSQL)
docker exec whale-postgres psql -U whale_user whale_knowledge -c "
  SELECT query, calls, total_time, mean_time
  FROM pg_stat_statements
  ORDER BY total_time DESC
  LIMIT 10;
"

# Clear embedding cache
docker exec whale-backend rm -rf /root/.cache/torch/sentence_transformers/
docker-compose restart backend
```

### Frontend Issues

```bash
# Check frontend logs
docker logs whale-frontend

# Rebuild frontend
docker-compose up -d --build frontend

# Clear browser cache
# Chrome: Ctrl+Shift+R (Cmd+Shift+R on Mac)

# Check API connection
curl http://localhost:8000/stats/health
```

## Python API Client

### Installation

```bash
pip install requests
```

### Usage

```python
import requests

# Upload PDF
with open('document.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/documents/upload/pdf',
        files={'file': f},
        data={'industry': 'Technology'}
    )
    print(response.json())

# Query
response = requests.post(
    'http://localhost:8000/query/',
    json={'query': 'machine learning', 'top_k': 5}
)
results = response.json()
for result in results['results']:
    print(f"Score: {result['score']:.2f} - {result['content'][:100]}...")

# List documents
response = requests.get('http://localhost:8000/documents/')
documents = response.json()
for doc in documents:
    print(f"{doc['id']}: {doc['title']} ({doc['status']})")

# Delete document
response = requests.delete('http://localhost:8000/documents/123')
print(response.json())
```

## JavaScript API Client

### Installation

```bash
npm install node-fetch
# or for browser: use fetch API
```

### Usage

```javascript
// Upload PDF (Node.js)
const FormData = require('form-data');
const fs = require('fs');

const formData = new FormData();
formData.append('file', fs.createReadStream('document.pdf'));
formData.append('industry', 'Technology');

const response = await fetch('http://localhost:8000/documents/upload/pdf', {
  method: 'POST',
  body: formData
});
const document = await response.json();

// Query
const response = await fetch('http://localhost:8000/query/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query: 'machine learning', top_k: 5 })
});
const results = await response.json();

// List documents
const response = await fetch('http://localhost:8000/documents/');
const documents = await response.json();

// Delete document
const response = await fetch('http://localhost:8000/documents/123', {
  method: 'DELETE'
});
```

## Useful Links

- **API Docs:** http://localhost:8000/docs
- **Frontend:** http://localhost:3000
- **Health Check:** http://localhost:8000/stats/health
- **Pinecone Console:** https://app.pinecone.io/
- **GitHub Repository:** https://github.com/your-org/whale-knowledge

## Getting Help

- [Full Documentation](index.md)
- [Getting Started Guide](getting-started.md)
- [API Reference](api-reference.md)
- [Configuration Guide](configuration.md)
- [GitHub Issues](https://github.com/your-org/whale-knowledge/issues)
