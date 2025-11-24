#!/usr/bin/env python3
"""
MCP Server for Whale Knowledge Base.

This server exposes the knowledge base as tools that can be called by AI agents.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.types import Tool, TextContent, Resource, EmbeddedResource
from mcp.server.stdio import stdio_server

from app.core.config import settings
from app.core.database import SessionLocal, init_db
from app.core.pinecone_client import pinecone_client
from app.services.retrieval import get_retrieval_service
from app.services.document_service import get_document_service
from app.models.schemas import SourceType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create MCP server
app = Server("whale-knowledge-base")


# Tool definitions
QUERY_KB_TOOL = Tool(
    name="query_knowledge_base",
    description="Search and retrieve documents from the whale knowledge base. Returns relevant document chunks based on semantic similarity.",
    inputSchema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query or question to find relevant documents"
            },
            "top_k": {
                "type": "integer",
                "description": "Number of results to return (default: 5, max: 50)",
                "default": 5
            },
            "filters": {
                "type": "object",
                "description": "Optional metadata filters (e.g., {'industry': 'healthcare', 'author': 'John'})",
                "properties": {
                    "industry": {"type": "string"},
                    "author": {"type": "string"},
                    "source_type": {"type": "string"}
                }
            }
        },
        "required": ["query"]
    }
)

ADD_DOCUMENT_TOOL = Tool(
    name="add_document_from_url",
    description="Scrape a web page and add it to the knowledge base using Jina Reader",
    inputSchema={
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The URL to scrape"
            },
            "industry": {
                "type": "string",
                "description": "Industry category for this document"
            },
            "author": {
                "type": "string",
                "description": "Author of the document"
            }
        },
        "required": ["url"]
    }
)

LIST_DOCUMENTS_TOOL = Tool(
    name="list_documents",
    description="List documents in the knowledge base with optional filters",
    inputSchema={
        "type": "object",
        "properties": {
            "limit": {
                "type": "integer",
                "description": "Maximum number of documents to return (default: 10)",
                "default": 10
            },
            "industry": {
                "type": "string",
                "description": "Filter by industry"
            },
            "status": {
                "type": "string",
                "description": "Filter by status (pending, processing, completed, error)"
            }
        }
    }
)

DELETE_DOCUMENT_TOOL = Tool(
    name="delete_document",
    description="Delete a document from the knowledge base",
    inputSchema={
        "type": "object",
        "properties": {
            "document_id": {
                "type": "integer",
                "description": "ID of the document to delete"
            }
        },
        "required": ["document_id"]
    }
)


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools."""
    return [
        QUERY_KB_TOOL,
        ADD_DOCUMENT_TOOL,
        LIST_DOCUMENTS_TOOL,
        DELETE_DOCUMENT_TOOL
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """Handle tool calls."""
    logger.info(f"Tool called: {name} with arguments: {arguments}")

    try:
        if name == "query_knowledge_base":
            return await handle_query_kb(arguments)
        elif name == "add_document_from_url":
            return await handle_add_document(arguments)
        elif name == "list_documents":
            return await handle_list_documents(arguments)
        elif name == "delete_document":
            return await handle_delete_document(arguments)
        else:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]
    except Exception as e:
        logger.error(f"Error handling tool {name}: {e}")
        return [TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]


async def handle_query_kb(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle query_knowledge_base tool call."""
    query = arguments.get("query")
    top_k = arguments.get("top_k", 5)
    filters = arguments.get("filters")

    if not query:
        return [TextContent(type="text", text="Error: query parameter is required")]

    retrieval_service = get_retrieval_service()
    result = await retrieval_service.query(
        query_text=query,
        top_k=top_k,
        filters=filters
    )

    # Format results for Claude
    response_parts = [
        f"Query: {result['query']}",
        f"Found {result['total_results']} results in {result['processing_time_ms']:.2f}ms\n"
    ]

    for i, res in enumerate(result['results'], 1):
        response_parts.append(f"--- Result {i} (Score: {res['score']:.4f}) ---")
        response_parts.append(f"Document: {res['metadata']['filename']}")
        response_parts.append(f"Source: {res['metadata']['source_type']}")
        if res['metadata'].get('industry'):
            response_parts.append(f"Industry: {res['metadata']['industry']}")
        if res['metadata'].get('author'):
            response_parts.append(f"Author: {res['metadata']['author']}")
        response_parts.append(f"\nContent:\n{res['content']}\n")

    return [TextContent(
        type="text",
        text="\n".join(response_parts)
    )]


async def handle_add_document(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle add_document_from_url tool call."""
    url = arguments.get("url")

    if not url:
        return [TextContent(type="text", text="Error: url parameter is required")]

    db = SessionLocal()
    try:
        document_service = get_document_service()

        metadata = {
            "industry": arguments.get("industry"),
            "author": arguments.get("author"),
        }

        document = await document_service.process_url(
            db=db,
            url=url,
            metadata=metadata
        )

        return [TextContent(
            type="text",
            text=f"Successfully added document:\n"
                 f"- ID: {document.id}\n"
                 f"- URL: {url}\n"
                 f"- Status: {document.status}\n"
                 f"- Chunks: {document.chunk_count}"
        )]
    except Exception as e:
        return [TextContent(type="text", text=f"Error adding document: {str(e)}")]
    finally:
        db.close()


async def handle_list_documents(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle list_documents tool call."""
    from app.core.database import Document

    limit = arguments.get("limit", 10)
    industry = arguments.get("industry")
    status = arguments.get("status")

    db = SessionLocal()
    try:
        query = db.query(Document)

        if industry:
            query = query.filter(Document.industry == industry)
        if status:
            query = query.filter(Document.status == status)

        documents = query.order_by(Document.created_at.desc()).limit(limit).all()

        if not documents:
            return [TextContent(type="text", text="No documents found")]

        response_parts = [f"Found {len(documents)} documents:\n"]

        for doc in documents:
            response_parts.append(
                f"- ID: {doc.id} | {doc.filename} | {doc.source_type} | "
                f"Status: {doc.status} | Chunks: {doc.chunk_count} | "
                f"Created: {doc.created_at.strftime('%Y-%m-%d')}"
            )
            if doc.industry:
                response_parts.append(f"  Industry: {doc.industry}")
            if doc.author:
                response_parts.append(f"  Author: {doc.author}")

        return [TextContent(type="text", text="\n".join(response_parts))]
    finally:
        db.close()


async def handle_delete_document(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle delete_document tool call."""
    document_id = arguments.get("document_id")

    if not document_id:
        return [TextContent(type="text", text="Error: document_id parameter is required")]

    db = SessionLocal()
    try:
        document_service = get_document_service()
        await document_service.delete_document(db, document_id)

        return [TextContent(
            type="text",
            text=f"Successfully deleted document {document_id}"
        )]
    except ValueError as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error deleting document: {str(e)}")]
    finally:
        db.close()


@app.list_resources()
async def list_resources() -> List[Resource]:
    """List available resources."""
    return [
        Resource(
            uri="kb://stats",
            name="Knowledge Base Statistics",
            mimeType="application/json",
            description="Statistics about the knowledge base"
        ),
        Resource(
            uri="kb://config",
            name="Knowledge Base Configuration",
            mimeType="application/json",
            description="Current configuration settings"
        )
    ]


@app.read_resource()
async def read_resource(uri: str) -> str:
    """Read resource content."""
    from app.core.database import Document
    from sqlalchemy import func

    if uri == "kb://stats":
        db = SessionLocal()
        try:
            total_docs = db.query(func.count(Document.id)).scalar()
            total_chunks = db.query(func.sum(Document.chunk_count)).scalar() or 0

            stats = {
                "total_documents": total_docs,
                "total_chunks": int(total_chunks),
                "pinecone_index": settings.pinecone_index_name,
                "embedding_model": settings.embedding_model
            }

            return json.dumps(stats, indent=2)
        finally:
            db.close()

    elif uri == "kb://config":
        config = {
            "embedding_model": settings.embedding_model,
            "embedding_dimension": settings.embedding_dimension,
            "chunk_size": settings.chunk_size,
            "chunk_overlap": settings.chunk_overlap,
            "pinecone_index": settings.pinecone_index_name,
            "auto_process_enabled": settings.auto_process_enabled
        }

        return json.dumps(config, indent=2)

    return f"Unknown resource: {uri}"


async def main():
    """Run the MCP server."""
    logger.info("Starting Whale Knowledge Base MCP Server")

    # Initialize database
    init_db()

    # Initialize Pinecone
    pinecone_client.initialize()

    logger.info("MCP Server initialized, starting stdio transport")

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
