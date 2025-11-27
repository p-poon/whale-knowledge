# MCP Integration Guide

Connect Whale Knowledge Base with AI agents using the Model Context Protocol (MCP).

## What is MCP?

Model Context Protocol (MCP) is a standard for connecting AI agents with external tools and data sources. The Whale Knowledge Base MCP server allows AI assistants like Claude to:

- Query your knowledge base
- Add documents from URLs
- List and manage documents
- Access system statistics

## Quick Setup with Claude Desktop

### Prerequisites

- Whale Knowledge Base running locally
- Claude Desktop app installed
- Python environment with dependencies installed

### Step 1: Configure Claude Desktop

Edit your Claude Desktop configuration file:

**macOS:**
```bash
nano ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**Windows:**
```bash
notepad %APPDATA%\Claude\claude_desktop_config.json
```

**Linux:**
```bash
nano ~/.config/Claude/claude_desktop_config.json
```

### Step 2: Add MCP Server Configuration

Add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "whale-knowledge": {
      "command": "/absolute/path/to/whale-knowledge/backend/venv/bin/python",
      "args": ["-m", "app.mcp_server"],
      "cwd": "/absolute/path/to/whale-knowledge/backend",
      "env": {
        "DATABASE_URL": "postgresql://whale_user:whale_pass@localhost:5432/whale_knowledge",
        "PINECONE_API_KEY": "your_pinecone_api_key",
        "PINECONE_ENVIRONMENT": "us-west1-gcp",
        "PINECONE_INDEX_NAME": "whale-knowledge",
        "EMBEDDING_MODEL": "sentence-transformers/all-MiniLM-L6-v2",
        "EMBEDDING_DIMENSION": "384",
        "PYTHONPATH": "/Users/phoebe.poon/whale-knowledge/whale-knowledge/backend",
      }
    }
  }
}
```

**Important:** Replace `/absolute/path/to/whale-knowledge/backend` with the actual absolute path on your system.

### Step 3: Restart Claude Desktop

Completely quit and restart Claude Desktop for the changes to take effect.

### Step 4: Test the Integration

In Claude Desktop, try these commands:

```
Use the whale-knowledge server to search for "artificial intelligence"
```

```
Add a document from https://example.com/article using the whale-knowledge server
```

```
List all documents in the whale-knowledge database
```

## Available MCP Tools

### 1. query_knowledge_base

Search the knowledge base using semantic similarity.

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| query | string | Yes | - | Search query text |
| top_k | integer | No | 5 | Number of results to return |
| filters | object | No | {} | Metadata filters (industry, author) |

**Example Usage:**

```
Use whale-knowledge to query: "What are the benefits of machine learning?"
```

```
Search whale-knowledge for healthcare-related documents about patient care
```

**Response Format:**

```json
{
  "results": [
    {
      "content": "Machine learning provides...",
      "score": 0.89,
      "document_title": "ML Guide",
      "metadata": {
        "industry": "Technology",
        "author": "John Doe"
      }
    }
  ],
  "query_time_ms": 156
}
```

### 2. add_document_from_url

Scrape and add a document from a URL.

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| url | string | Yes | - | URL to scrape |
| industry | string | No | null | Industry category |
| author | string | No | null | Content author |

**Example Usage:**

```
Add this article to whale-knowledge: https://example.com/article
```

```
Use whale-knowledge to add the Wikipedia page about AI with industry set to Technology
```

**Response Format:**

```json
{
  "document_id": 124,
  "title": "Article Title",
  "status": "completed",
  "chunk_count": 15
}
```

### 3. list_documents

List all documents in the knowledge base.

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| limit | integer | No | 10 | Maximum number of documents |
| industry | string | No | null | Filter by industry |

**Example Usage:**

```
Show me all documents in whale-knowledge
```

```
List healthcare documents from whale-knowledge
```

**Response Format:**

```json
{
  "documents": [
    {
      "id": 123,
      "title": "Document Title",
      "source_type": "pdf",
      "industry": "Healthcare",
      "author": "John Doe",
      "chunk_count": 25,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 150
}
```

### 4. delete_document

Delete a document from the knowledge base.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| document_id | integer | Yes | ID of document to delete |

**Example Usage:**

```
Delete document 123 from whale-knowledge
```

**Response Format:**

```json
{
  "message": "Document deleted successfully",
  "document_id": 123,
  "chunks_deleted": 25
}
```

## Available MCP Resources

Resources provide read-only access to system information.

### kb://stats

Get knowledge base statistics.

**Example Usage:**

```
Show me stats from whale-knowledge
```

**Response:**

```json
{
  "total_documents": 150,
  "total_chunks": 3450,
  "total_queries": 1500,
  "documents_by_industry": {
    "Technology": 80,
    "Healthcare": 45,
    "Finance": 25
  }
}
```

### kb://config

Get current configuration.

**Example Usage:**

```
What's the configuration of whale-knowledge?
```

**Response:**

```json
{
  "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
  "embedding_dimension": 384,
  "chunk_size": 512,
  "chunk_overlap": 50,
  "pinecone_index": "whale-knowledge"
}
```

## Testing the MCP Server

### Command Line Testing

Test the MCP server directly from the command line:

```bash
cd backend
source venv/bin/activate  # or: venv\Scripts\activate on Windows

# Start the MCP server
python -m app.mcp_server
```

The server communicates via stdio. Send JSON-RPC requests:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list"
}
```

### Debugging

Enable debug logging:

```bash
# Set debug environment variable
export MCP_DEBUG=1
python -m app.mcp_server
```

Check Claude Desktop logs:

**macOS:**
```bash
tail -f ~/Library/Logs/Claude/mcp*.log
```

**Windows:**
```bash
type %APPDATA%\Claude\logs\mcp*.log
```

## Example Workflows

### Research Assistant

```
I'm researching machine learning.
1. Search whale-knowledge for "machine learning fundamentals"
2. Then search for "neural networks"
3. Summarize the key concepts from both searches
```

### Document Management

```
1. List all technology documents in whale-knowledge
2. For each document, tell me the title and author
3. If any are outdated (before 2023), suggest which to delete
```

### Knowledge Base Building

```
I'm building a knowledge base about AI.
1. Add these three articles to whale-knowledge:
   - https://example.com/intro-to-ai
   - https://example.com/deep-learning
   - https://example.com/nlp-basics
2. After they're added, search for "neural networks" to verify
```

### Content Discovery

```
1. Show me whale-knowledge stats
2. Query for "healthcare best practices"
3. From the results, what are the top 3 most relevant documents?
```

## Integration with Other AI Agents

### Using the MCP Server with Custom Agents

The MCP server can be integrated with any AI agent that supports MCP:

```python
from mcp.client import Client

# Connect to MCP server
client = Client()
await client.connect_stdio("python", ["-m", "app.mcp_server"],
                          cwd="/path/to/backend")

# Query knowledge base
result = await client.call_tool("query_knowledge_base", {
    "query": "machine learning",
    "top_k": 5
})
```

### Environment Variables

Required environment variables for the MCP server:

```bash
DATABASE_URL=postgresql://whale_user:whale_pass@localhost:5432/whale_knowledge
PINECONE_API_KEY=your_api_key
PINECONE_ENVIRONMENT=us-west1-gcp
PINECONE_INDEX_NAME=whale-knowledge
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384
```

## Troubleshooting

### MCP Server Won't Start

**Check Python environment:**
```bash
which python
python --version
python -c "import app.mcp_server"
```

**Verify dependencies:**
```bash
pip list | grep -E "(fastapi|pinecone|sentence-transformers|psycopg2)"
```

**Check environment variables:**
```bash
env | grep -E "(DATABASE_URL|PINECONE)"
```

### Connection Refused

**Ensure database is running:**
```bash
docker ps | grep postgres
```

**Test database connection:**
```bash
psql $DATABASE_URL
```

**Test Pinecone connection:**
```python
from pinecone import Pinecone
pc = Pinecone(api_key="your_key")
pc.list_indexes()
```

### Claude Can't Find the Server

**Verify configuration path:**
- Ensure `cwd` is an absolute path
- Check that `app.mcp_server` exists in that directory
- Verify Python path is correct

**Check Claude Desktop logs:**
```bash
# macOS
cat ~/Library/Logs/Claude/mcp-server-whale-knowledge.log

# Look for error messages
```

**Restart Claude Desktop:**
- Completely quit the app (Cmd+Q on macOS)
- Wait a few seconds
- Restart

### Tools Not Showing Up

**Verify MCP server is running:**
```bash
ps aux | grep mcp_server
```

**Check Claude Desktop status:**
Look for the MCP icon in Claude Desktop's interface. It should show "whale-knowledge" as connected.

**Inspect tool list:**
In Claude, try: "What MCP servers are available?"

### Slow Response Times

**Check query performance:**
```bash
curl -X POST "http://localhost:8000/query/" \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "top_k": 5}'
```

**Monitor Pinecone latency:**
Check Pinecone console for query performance metrics.

**Optimize embedding model:**
Consider using a smaller model for faster queries:
```env
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384
```

## Security Considerations

### Production Deployment

For production MCP servers:

1. **Use secure connections:**
   - Run over HTTPS
   - Use VPN or SSH tunnels
   - Implement authentication

2. **Restrict access:**
   - Whitelist IP addresses
   - Use API keys
   - Implement rate limiting

3. **Protect credentials:**
   - Store API keys securely
   - Use environment variables
   - Never commit credentials

4. **Monitor usage:**
   - Log all requests
   - Track query patterns
   - Alert on anomalies

### Example Secure Configuration

```json
{
  "mcpServers": {
    "whale-knowledge": {
      "command": "python",
      "args": ["-m", "app.mcp_server"],
      "cwd": "/path/to/backend",
      "env": {
        "DATABASE_URL": "${DATABASE_URL}",
        "PINECONE_API_KEY": "${PINECONE_API_KEY}",
        "MCP_AUTH_TOKEN": "${MCP_AUTH_TOKEN}"
      }
    }
  }
}
```

## Next Steps

- Review [API Reference](api-reference.md) for detailed endpoint documentation
- Check [Architecture](architecture.md) to understand the MCP server design
- See [Deployment](deployment.md) for production deployment strategies
- Explore [Configuration](configuration.md) for customization options
