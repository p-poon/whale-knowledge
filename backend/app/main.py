from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.core.config import settings
from app.core.database import init_db
from app.core.pinecone_client import pinecone_client
from app.api import documents, query, evaluation, stats, audit, agent
from app.services.template_service import template_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Whale Knowledge Base API",
    description="RAG-based knowledge base with MCP server integration",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(documents.router)
app.include_router(query.router)
app.include_router(evaluation.router)
app.include_router(stats.router)
app.include_router(audit.router)
app.include_router(agent.router)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting Whale Knowledge Base API")

    # Initialize database
    logger.info("Initializing database...")
    init_db()

    # Initialize Pinecone
    logger.info("Initializing Pinecone...")
    pinecone_client.initialize()

    # Initialize default content templates
    logger.info("Initializing default templates...")
    template_service.initialize_default_templates()

    logger.info("Startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down Whale Knowledge Base API")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Whale Knowledge Base API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/ping")
async def ping():
    """Simple ping endpoint."""
    return {"message": "pong"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )
