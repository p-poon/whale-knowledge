# Whale Knowledge Base Documentation

Welcome to the Whale Knowledge Base documentation! This is a production-ready RAG (Retrieval-Augmented Generation) system with MCP server integration for AI agents.

## What is Whale Knowledge Base?

Whale Knowledge Base is a powerful document management and semantic search system that allows you to:

- **Upload and process documents** from PDFs and websites
- **Search semantically** using AI-powered embeddings
- **Integrate with AI agents** via Model Context Protocol (MCP)
- **Monitor quality** with built-in evaluation metrics
- **Scale easily** with cloud-native architecture

## Quick Links

- [Getting Started](getting-started.md) - Install and run in 5 minutes
- [Quick Reference](quick-reference.md) - Fast reference for common operations
- [API Reference](api-reference.md) - Complete API documentation
- [MCP Integration](mcp-integration.md) - Connect with Claude and other AI agents
- [Architecture](architecture.md) - System design and components
- [Configuration](configuration.md) - Customize your deployment
- [Deployment](deployment.md) - Production deployment guide

## Key Features

### Document Processing
- PDF upload and text extraction
- Web scraping with Jina Reader API
- Multiple chunking strategies (fixed-size, sentence, paragraph)
- Automatic metadata extraction

### Semantic Search
- Vector embeddings with Sentence Transformers
- Pinecone vector database integration
- Metadata filtering by industry, author, date
- Configurable result ranking

### Evaluation System
- Semantic similarity scoring
- User feedback collection (thumbs up/down)
- Precision and recall metrics
- Real-time dashboard visualization

### MCP Server
- Query knowledge base from AI agents
- Add documents programmatically
- List and manage documents
- Access system statistics

### Modern Tech Stack

**Backend:**
- FastAPI for high-performance APIs
- PostgreSQL for metadata storage
- Pinecone for vector search
- Sentence Transformers for embeddings

**Frontend:**
- Next.js 14 with App Router
- TypeScript for type safety
- Tailwind CSS for styling
- Real-time updates with SWR

## Use Cases

### Personal Knowledge Management
Build your own searchable knowledge base from PDFs, articles, and research papers.

### Enterprise Document Search
Enable semantic search across company documentation, policies, and internal wikis.

### AI Agent Integration
Give AI assistants like Claude access to your knowledge base for enhanced responses.

### Research Assistant
Query across multiple documents to find relevant information and citations.

### Customer Support
Search through product documentation and FAQs to answer customer questions.

## Architecture Overview

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Next.js   │────▶│   FastAPI   │────▶│  Pinecone   │
│  Frontend   │     │   Backend   │     │   Vectors   │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                    ┌──────┴──────┐
                    ▼             ▼
              ┌──────────┐  ┌──────────┐
              │PostgreSQL│  │   Jina   │
              │ Metadata │  │  Reader  │
              └──────────┘  └──────────┘
```

## Getting Help

- **Documentation Issues**: [Open an issue](https://github.com/your-org/whale-knowledge/issues)
- **Questions**: [GitHub Discussions](https://github.com/your-org/whale-knowledge/discussions)
- **API Reference**: http://localhost:8000/docs (when running locally)

## Next Steps

Ready to get started? Follow our [Getting Started Guide](getting-started.md) to have the system running in minutes!
