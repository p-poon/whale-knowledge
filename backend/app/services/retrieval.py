from typing import List, Dict, Any, Optional
import logging
import time

from app.core.pinecone_client import pinecone_client
from app.services.embeddings import get_embedding_generator
from app.core.database import SessionLocal
from app.core.database import Document

logger = logging.getLogger(__name__)


class RetrievalService:
    """Handle RAG retrieval from knowledge base."""

    def __init__(self):
        self.embedding_generator = get_embedding_generator()

    async def query(
        self,
        query_text: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Query the knowledge base.

        Args:
            query_text: Query string
            top_k: Number of results to return
            filters: Optional metadata filters

        Returns:
            Query results with chunks and metadata
        """
        start_time = time.time()

        try:
            # Generate query embedding
            query_embedding = await self.embedding_generator.embed(query_text)

            # Build Pinecone filters if provided
            pinecone_filter = None
            if filters:
                pinecone_filter = self._build_pinecone_filter(filters)

            # Query Pinecone
            pinecone_response = await pinecone_client.query(
                vector=query_embedding,
                top_k=top_k,
                filter=pinecone_filter,
                include_metadata=True
            )

            # Process results
            results = []
            db = SessionLocal()
            try:
                for match in pinecone_response.get("matches", []):
                    chunk_id = match["id"]
                    score = match["score"]
                    metadata = match.get("metadata", {})

                    # Extract document ID from chunk ID (format: doc_{doc_id}_chunk_{chunk_idx})
                    try:
                        doc_id = int(chunk_id.split("_")[1])
                    except (IndexError, ValueError):
                        logger.warning(f"Invalid chunk ID format: {chunk_id}")
                        continue

                    # Fetch document from database
                    document = db.query(Document).filter(Document.id == doc_id).first()
                    if not document:
                        continue

                    result = {
                        "document_id": doc_id,
                        "chunk_id": chunk_id,
                        "content": metadata.get("text", ""),
                        "score": float(score),
                        "metadata": {
                            "filename": document.filename,
                            "source_type": document.source_type,
                            "industry": document.industry,
                            "author": document.author,
                            "document_date": document.document_date.isoformat() if document.document_date else None,
                            "chunk_index": metadata.get("chunk_index", 0),
                        }
                    }
                    results.append(result)
            finally:
                db.close()

            processing_time = (time.time() - start_time) * 1000  # Convert to ms

            response = {
                "query": query_text,
                "results": results,
                "total_results": len(results),
                "processing_time_ms": processing_time
            }

            logger.info(f"Query completed in {processing_time:.2f}ms with {len(results)} results")
            return response

        except Exception as e:
            logger.error(f"Error in query: {e}")
            raise

    def _build_pinecone_filter(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build Pinecone filter from user filters.

        Args:
            filters: User-provided filters

        Returns:
            Pinecone-formatted filter
        """
        pinecone_filter = {}

        # Map common filter keys to Pinecone metadata fields
        filter_mapping = {
            "industry": "industry",
            "author": "author",
            "source_type": "source_type",
            "document_id": "document_id"
        }

        for key, value in filters.items():
            if key in filter_mapping:
                pinecone_filter[filter_mapping[key]] = value

        return pinecone_filter if pinecone_filter else None


# Global retrieval service instance
def get_retrieval_service() -> RetrievalService:
    """Get retrieval service instance."""
    return RetrievalService()
