# Getting Started

Get Whale Knowledge Base up and running in 5 minutes!

## Prerequisites

Before you begin, ensure you have:

- **Docker and Docker Compose** installed ([Get Docker](https://docs.docker.com/get-docker/))
- **Pinecone API key** ([Sign up free](https://www.pinecone.io/))
- (Optional) **Jina Reader API key** for web scraping ([Get key](https://jina.ai/))

## Quick Start

### Step 1: Get Your Pinecone API Key

1. Visit [Pinecone](https://www.pinecone.io/) and sign up for a free account
2. Create a new project in the Pinecone console
3. Navigate to "API Keys" and copy your API key
4. Note your environment (e.g., `us-west1-gcp`)

### Step 2: Clone and Configure

```bash
# Clone the repository
git clone https://github.com/your-org/whale-knowledge.git
cd whale-knowledge

# Copy the example environment file
cp .env.example .env
```

Edit `.env` and add your credentials:

```env
# Required: Pinecone Configuration
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENVIRONMENT=us-west1-gcp
PINECONE_INDEX_NAME=whale-knowledge

# Optional: Jina Reader for web scraping
JINA_API_KEY=your_jina_api_key_here

# Optional: Customize embedding model
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384
```

### Step 3: Start the Application

```bash
# Start all services with Docker Compose
docker-compose up -d
```

This command starts:
- **PostgreSQL** database (port 5432)
- **Backend API** (port 8000)
- **Frontend** web application (port 3000)

Wait 30-60 seconds for services to initialize and the embedding model to download (~90MB on first run).

### Step 4: Verify Installation

Check that all services are running:

```bash
# Check service status
docker-compose ps

# Check backend health
curl http://localhost:8000/stats/health
```

Expected health check response:
```json
{
  "status": "healthy",
  "database": "connected",
  "pinecone": "connected"
}
```

### Step 5: Access the Application

Open your browser and navigate to:

- **Frontend UI**: [http://localhost:3000](http://localhost:3000)
- **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Alternative API Docs**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Your First Document

### Upload a PDF

1. Navigate to [http://localhost:3000](http://localhost:3000)
2. Click the **"Upload PDF"** button
3. Select a PDF file from your computer
4. (Optional) Add metadata:
   - **Industry**: e.g., "Healthcare", "Technology", "Finance"
   - **Author**: Document author name
5. Click **"Upload PDF"**
6. Wait for processing - status will change to "completed"

### Scrape a Website

1. Click the **"Scrape URL"** button
2. Enter a URL, for example:
   - `https://en.wikipedia.org/wiki/Artificial_intelligence`
   - `https://docs.python.org/3/tutorial/`
   - Any article or documentation page
3. (Optional) Add metadata
4. Click **"Scrape URL"**
5. The content will be extracted and processed

## Your First Query

1. Click the **"Query"** tab
2. Type a question related to your uploaded documents:
   - "What is artificial intelligence?"
   - "Explain machine learning concepts"
   - "What are the main topics discussed?"
3. Press **"Query"** or hit Enter
4. View results ranked by semantic similarity
5. Click thumbs up 👍 or down 👎 to provide feedback

## Understanding Results

Each result shows:
- **Similarity Score**: 0.0 to 1.0 (higher is more relevant)
- **Document Source**: Which document the chunk came from
- **Metadata**: Industry, author, date
- **Content Preview**: The relevant text chunk

## View Statistics

Click the **"Stats"** tab to see:
- Total documents in your knowledge base
- Total chunks indexed
- Query count
- Storage usage
- Evaluation metrics

## Common Commands

```bash
# Start services
docker-compose up -d

# View logs (all services)
docker-compose logs -f

# View logs (specific service)
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build

# Restart a specific service
docker-compose restart backend
```

## Manual Setup (Without Docker)

If you prefer to run services manually:

### Backend Setup

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

# Start PostgreSQL (must be running separately)
# Update DATABASE_URL in .env to match your PostgreSQL config

# Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Set up environment
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Start development server
npm run dev
```

## Testing the API

### Upload a PDF via API

```bash
curl -X POST "http://localhost:8000/documents/upload/pdf" \
  -F "file=@/path/to/document.pdf" \
  -F "industry=Technology" \
  -F "author=John Doe"
```

### Query via API

```bash
curl -X POST "http://localhost:8000/query/" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is machine learning?",
    "top_k": 5
  }'
```

### List Documents

```bash
curl http://localhost:8000/documents/
```

### Get Statistics

```bash
curl http://localhost:8000/stats/
```

## Troubleshooting

### Services Won't Start

**Check if ports are in use:**
```bash
# Check frontend port
lsof -i :3000

# Check backend port
lsof -i :8000

# Check PostgreSQL port
lsof -i :5432
```

**Solution:** Stop other services using these ports or modify ports in `docker-compose.yml`.

### Can't Connect to Pinecone

**Verify your API key:**
```bash
cat .env | grep PINECONE_API_KEY
```

**Check health endpoint:**
```bash
curl http://localhost:8000/stats/health
```

**Common issues:**
- API key is incorrect or expired
- Pinecone environment doesn't match your account
- Firewall blocking outbound connections

### Database Connection Failed

**Check PostgreSQL is running:**
```bash
docker ps | grep postgres
```

**View PostgreSQL logs:**
```bash
docker logs whale-postgres
```

**Test database connection:**
```bash
docker exec -it whale-postgres psql -U whale_user -d whale_knowledge
```

### Embedding Model Download Slow

The first run downloads the embedding model (~90MB). This is normal and only happens once.

**Check download progress:**
```bash
docker logs -f whale-backend
```

**Pre-download the model:**
```bash
docker exec -it whale-backend python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
```

### Permission Denied Errors

On Linux, you may need to fix permissions:

```bash
sudo chown -R $USER:$USER .
```

### Port Already in Use

Modify ports in `docker-compose.yml`:

```yaml
services:
  frontend:
    ports:
      - "3001:3000"  # Change host port to 3001

  backend:
    ports:
      - "8001:8000"  # Change host port to 8001
```

Then update frontend `.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8001
```

## Next Steps

Now that you have Whale Knowledge Base running:

1. **Add more documents** to build your knowledge base
2. **Try the [MCP Integration](mcp-integration.md)** to use with Claude
3. **Explore the [API Reference](api-reference.md)** for programmatic access
4. **Review [Configuration](configuration.md)** to customize behavior
5. **Monitor the Evaluation Dashboard** to track retrieval quality

## Need Help?

- Check the [API Documentation](http://localhost:8000/docs)
- Review [Architecture](architecture.md) to understand the system
- Open an issue on [GitHub](https://github.com/your-org/whale-knowledge/issues)
- Read the full [README](../README.md)
