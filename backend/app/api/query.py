from fastapi import APIRouter, HTTPException
from typing import Optional

from app.models.schemas import QueryRequest, QueryResponse
from app.services.retrieval import get_retrieval_service

router = APIRouter(prefix="/query", tags=["query"])


@router.post("/", response_model=QueryResponse)
async def query_knowledge_base(request: QueryRequest):
    """
    Query the knowledge base for relevant documents.

    This endpoint performs semantic search across all embedded documents
    and returns the most relevant chunks based on the query.
    """
    try:
        retrieval_service = get_retrieval_service()

        result = await retrieval_service.query(
            query_text=request.query,
            top_k=request.top_k,
            filters=request.filters
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.get("/test")
async def test_query(
    q: str,
    top_k: int = 5
):
    """Simple test endpoint for quick queries."""
    try:
        retrieval_service = get_retrieval_service()

        result = await retrieval_service.query(
            query_text=q,
            top_k=top_k
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")
