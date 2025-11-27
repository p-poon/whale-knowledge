# Whale Knowledge Base

A production-ready RAG (Retrieval-Augmented Generation) knowledge base system with MCP (Model Context Protocol) server integration. Upload PDFs, scrape websites, and query your knowledge base using semantic search. Built for AI agents to access via MCP.

## Features

### Core Functionality
- **Document Processing**: Upload PDFs or scrape websites using Jina Reader API
- **Smart Chunking**: Multiple chunking strategies (fixed-size, sentence-based, paragraph-based)
- **Vector Search**: Semantic search powered by Pinecone and sentence-transformers
- **Metadata Tagging**: Organize documents by industry, author, and date
- **Auto-Refresh**: Configurable document refresh scheduling

### Evaluation System
- **Semantic Similarity Scoring**: Measure retrieval quality
- **User Feedback**: Thumbs up/down for query results
- **Automated Testing**: Ground truth Q&A pairs for precision/recall metrics
- **Dashboard**: Real-time metrics visualization

### MCP Server
- **AI Agent Integration**: Query knowledge base from Claude and other AI agents
- **Tool Exposure**: `query_knowledge_base`, `add_document_from_url`, `list_documents`, `delete_document`
- **Resource Access**: KB statistics and configuration

### AI Agent Content Generation ✨ NEW
- **LLM Integration**: Generate content using Anthropic Claude or OpenAI GPT models
- **Content Types**: Create white papers, articles, and blog posts
- **Document Selection**: AI-powered document suggestions or manual selection
- **Advanced Customization**: Control style, tone, audience, length, and structure
- **Template System**: Pre-built and custom templates for different content types
- **Cost Tracking**: Monitor LLM usage and estimated costs
- **Progress Streaming**: Real-time generation status updates via Server-Sent Events

### Frontend
- **Document Management**: Upload, view, filter, and delete documents
- **Chat Interface**: Interactive query interface with result highlighting
- **Evaluation Dashboard**: Visualize retrieval metrics and feedback
- **Real-time Updates**: Auto-refreshing stats and document lists
- **Content Generation Wizard**: Multi-step interface for creating content with AI
- **Content Library**: Browse and manage AI-generated content

## Tech Stack

### Backend
- **FastAPI**: High-performance async API framework
- **PostgreSQL**: Document metadata and evaluation storage
- **Pinecone**: Vector database for embeddings
- **Sentence Transformers**: Embedding generation (all-MiniLM-L6-v2)
- **PyPDF2**: PDF text extraction
- **Jina Reader API**: Web scraping to markdown
- **Anthropic Claude API**: LLM for content generation (Claude 3.5 Sonnet)
- **OpenAI API**: Alternative LLM provider (GPT-4, GPT-3.5)

### Frontend
- **Next.js 14**: React framework with App Router
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first styling
- **SWR**: Data fetching and caching
- **Recharts**: Metrics visualization

### Infrastructure
- **Docker**: Containerized deployment
- **MCP**: Model Context Protocol for AI agent integration

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Pinecone account and API key ([Get one here](https://www.pinecone.io/))
- (Optional) Jina Reader API key for web scraping

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd whale-knowledge
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your API keys:
   ```env
   PINECONE_API_KEY=your_pinecone_api_key
   PINECONE_ENVIRONMENT=us-west1-gcp
   PINECONE_INDEX_NAME=whale-knowledge
   JINA_API_KEY=your_jina_api_key  # Optional
   ```

3. **Start the application**
   ```bash
   docker-compose up -d
   ```

   This will start:
   - PostgreSQL (port 5432)
   - Backend API (port 8000)
   - Frontend (port 3000)

4. **Access the application**
   - Frontend: http://localhost:3000
   - API Docs: http://localhost:8000/docs
   - Health Check: http://localhost:8000/stats/health

### Manual Setup (Without Docker)

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
# (Migrations are auto-created on startup)

# Start the server
uvicorn app.main:app --reload
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Set up environment
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Start development server
npm run dev
```

## Usage

### 1. Upload Documents

**Via Web UI:**
- Navigate to the Documents tab
- Choose "Upload PDF" or "Scrape URL"
- Add metadata (industry, author)
- Click upload/scrape

**Via API:**
```bash
# Upload PDF
curl -X POST "http://localhost:8000/documents/upload/pdf" \
  -F "file=@document.pdf" \
  -F "industry=Healthcare" \
  -F "author=John Doe"

# Scrape URL
curl -X POST "http://localhost:8000/documents/scrape" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/article", "industry": "Tech"}'
```

### 2. Query Knowledge Base

**Via Web UI:**
- Navigate to the Query tab
- Type your question
- View ranked results with similarity scores
- Provide feedback (thumbs up/down)

**Via API:**
```bash
curl -X POST "http://localhost:8000/query/" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the benefits of RAG systems?",
    "top_k": 5,
    "filters": {"industry": "AI"}
  }'
```

### 3. Use MCP Server

#### Setup with Claude Desktop

1. **Configure MCP Server**

   Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or equivalent on your OS:

   ```json
   {
     "mcpServers": {
       "whale-knowledge": {
         "command": "python",
         "args": ["-m", "app.mcp_server"],
         "cwd": "/absolute/path/to/whale-knowledge/backend",
         "env": {
           "DATABASE_URL": "postgresql://whale_user:whale_pass@localhost:5432/whale_knowledge",
           "PINECONE_API_KEY": "your_pinecone_api_key",
           "PINECONE_ENVIRONMENT": "us-west1-gcp",
           "PINECONE_INDEX_NAME": "whale-knowledge"
         }
       }
     }
   }
   ```

2. **Restart Claude Desktop**

3. **Use in Claude**
   ```
   Use the whale-knowledge server to query: "What are best practices for RAG?"
   ```

#### Available MCP Tools

- **query_knowledge_base**: Search documents
  ```json
  {
    "query": "your question",
    "top_k": 5,
    "filters": {"industry": "Healthcare"}
  }
  ```

- **add_document_from_url**: Scrape and add web content
  ```json
  {
    "url": "https://example.com",
    "industry": "Tech",
    "author": "John Doe"
  }
  ```

- **list_documents**: View all documents
  ```json
  {
    "limit": 10,
    "industry": "Healthcare"
  }
  ```

- **delete_document**: Remove a document
  ```json
  {
    "document_id": 123
  }
  ```

### 4. Monitor Evaluation Metrics

Navigate to the Evaluation tab to view:
- Total queries processed
- Average precision and recall
- Semantic similarity scores
- User feedback rates
- Interactive charts

## Configuration

### Embedding Model

Change the embedding model in [backend/.env](backend/.env):
```env
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384
```

Supported models:
- `all-MiniLM-L6-v2` (384 dim, fast, default)
- `all-mpnet-base-v2` (768 dim, better quality)
- `multi-qa-mpnet-base-dot-v1` (768 dim, Q&A optimized)

### Chunking Strategy

Edit [backend/app/core/config.py](backend/app/core/config.py):
```python
chunk_size: int = 512  # Characters per chunk
chunk_overlap: int = 50  # Overlap between chunks
```

### Auto-Processing

Enable automatic PDF processing:
```env
AUTO_PROCESS_ENABLED=true
WATCH_DIRECTORY=./documents
```

Place PDFs in the watch directory for automatic ingestion.

## API Documentation

Full API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Key Endpoints

#### Documents
- `POST /documents/upload/pdf` - Upload PDF
- `POST /documents/scrape` - Scrape URL
- `GET /documents/` - List documents
- `GET /documents/{id}` - Get document
- `DELETE /documents/{id}` - Delete document

#### Query
- `POST /query/` - Query knowledge base
- `GET /query/test` - Quick test query

#### Evaluation
- `POST /evaluation/` - Create evaluation
- `POST /evaluation/feedback` - Submit feedback
- `GET /evaluation/metrics` - Get metrics
- `GET /evaluation/history` - Get history

#### Stats
- `GET /stats/` - Get statistics
- `GET /stats/health` - Health check

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                    │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │  Documents   │ │    Query     │ │  Evaluation  │        │
│  │     UI       │ │  Interface   │ │   Dashboard  │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTP/REST
┌────────────────────────────┴────────────────────────────────┐
│                     Backend (FastAPI)                        │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │   Document   │ │   Retrieval  │ │  Evaluation  │        │
│  │   Service    │ │   Service    │ │   Service    │        │
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘        │
│         │                 │                 │                 │
│  ┌──────▼─────────────────▼─────────────────▼───────┐       │
│  │           Core Services & Database                │       │
│  │  • PDF Processing  • Embeddings  • Chunking      │       │
│  └───────────────────────┬───────────────────────────┘       │
└────────────────────────────┴────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
   ┌────▼────┐          ┌────▼────┐         ┌────▼────┐
   │PostgreSQL│          │Pinecone │         │  Jina   │
   │Metadata │          │ Vectors │         │ Reader  │
   └─────────┘          └─────────┘         └─────────┘

┌─────────────────────────────────────────────────────────────┐
│                    MCP Server (stdio)                        │
│  Tools: query_knowledge_base, add_document, list, delete    │
│  Resources: kb://stats, kb://config                         │
└─────────────────────────────────────────────────────────────┘
                             │
                        AI Agents
                    (Claude, etc.)
```

## Development

### Project Structure

```
whale-knowledge/
├── backend/
│   ├── app/
│   │   ├── api/              # API endpoints
│   │   ├── core/             # Core config & clients
│   │   ├── models/           # Pydantic schemas
│   │   ├── services/         # Business logic
│   │   ├── main.py           # FastAPI app
│   │   └── mcp_server.py     # MCP server
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/              # Next.js pages
│   │   ├── components/       # React components
│   │   └── lib/              # API client
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

### Running Tests

```bash
# Backend tests (to be implemented)
cd backend
pytest

# Frontend tests (to be implemented)
cd frontend
npm test
```

### Adding New Features

1. **New Document Source**: Implement in `backend/app/services/`
2. **New Chunking Strategy**: Add to `backend/app/services/chunking.py`
3. **New MCP Tool**: Add to `backend/app/mcp_server.py`
4. **New UI Component**: Add to `frontend/src/components/`

## Troubleshooting

### Pinecone Connection Issues

```bash
# Check Pinecone status
curl -X GET "http://localhost:8000/stats/health"

# Verify API key
echo $PINECONE_API_KEY

# Check index exists
# Visit Pinecone console
```

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Test connection
docker exec -it whale-postgres psql -U whale_user -d whale_knowledge

# View logs
docker logs whale-postgres
```

### MCP Server Issues

```bash
# Test MCP server directly
cd backend
python -m app.mcp_server

# Check Claude Desktop logs
# macOS: ~/Library/Logs/Claude/
# Windows: %APPDATA%\Claude\logs\
```

### Embedding Model Download

First run will download the model (~90MB). This may take a few minutes:
```bash
# Check logs
docker logs whale-backend

# Pre-download model
docker exec -it whale-backend python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
```

## Performance Optimization

### For Large Document Collections

1. **Increase Pinecone pod size** (in Pinecone console)
2. **Use larger embedding model** for better quality
3. **Adjust chunk size** based on document types
4. **Enable connection pooling** (already configured)

### For High Query Volume

1. **Scale backend horizontally** (add more containers)
2. **Add Redis caching** for frequent queries
3. **Use CDN** for frontend assets
4. **Optimize Pinecone namespace** strategy

## Security Considerations

- **API Keys**: Never commit `.env` files
- **Rate Limiting**: Add rate limiting for production
- **Authentication**: Implement OAuth/JWT for production
- **CORS**: Restrict origins in production
- **Input Validation**: All inputs are validated with Pydantic

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## License

MIT License - see LICENSE file for details

## Documentation

### User Documentation
Complete user guides and API documentation available at [docs/](docs/):
- [Getting Started Guide](docs/getting-started.md) - Installation and setup
- [Quick Reference](docs/quick-reference.md) - Common operations
- [API Reference](docs/api-reference.md) - Complete API documentation
- [MCP Integration](docs/mcp-integration.md) - AI agent integration
- [Architecture](docs/architecture.md) - System design
- [Configuration](docs/configuration.md) - Configuration options
- [Deployment](docs/deployment.md) - Production deployment

**GitHub Pages**: https://your-username.github.io/whale-knowledge/

### Internal Developer Documentation
Implementation guides and technical details in [internal-dev-docs/](internal-dev-docs/):
- [Implementation Summary](internal-dev-docs/IMPLEMENTATION_SUMMARY.md) - Complete implementation overview
- [AI Agent Setup](internal-dev-docs/SETUP_AI_AGENT.md) - AI content generation feature
- [Document Viewer](internal-dev-docs/DOCUMENT_VIEWER.md) - Document viewer implementation
- [Usage Audit](internal-dev-docs/USAGE_AUDIT_IMPLEMENTATION.md) - API usage tracking
- [GitHub Pages Setup](internal-dev-docs/GITHUB_PAGES_SETUP.md) - Documentation deployment
- [Implementation Complete](internal-dev-docs/IMPLEMENTATION_COMPLETE.md) - AI feature completion

## Support

- **Issues**: [GitHub Issues](https://github.com/your-org/whale-knowledge/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/whale-knowledge/discussions)
- **API Documentation**: http://localhost:8000/docs (when running locally)

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Vector search by [Pinecone](https://www.pinecone.io/)
- Embeddings by [Sentence Transformers](https://www.sbert.net/)
- Web scraping by [Jina Reader](https://jina.ai/)
- MCP by [Anthropic](https://www.anthropic.com/)
