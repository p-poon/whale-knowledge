from pinecone import Pinecone, ServerlessSpec
from typing import List, Dict, Any, Optional
import logging
import time
from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.audit_service import get_audit_service

logger = logging.getLogger(__name__)


class PineconeClient:
    """Client for interacting with Pinecone vector database."""

    def __init__(self):
        self.pc = Pinecone(api_key=settings.pinecone_api_key)
        self.index_name = settings.pinecone_index_name
        self.dimension = settings.embedding_dimension
        self._index = None

    def initialize(self):
        """Initialize or get existing Pinecone index."""
        try:
            # Check if index exists
            existing_indexes = self.pc.list_indexes()

            if self.index_name not in [idx.name for idx in existing_indexes]:
                logger.info(f"Creating new Pinecone index: {self.index_name}")
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    )
                )

            self._index = self.pc.Index(self.index_name)
            logger.info(f"Connected to Pinecone index: {self.index_name}")

        except Exception as e:
            logger.error(f"Error initializing Pinecone: {e}")
            raise

    @property
    def index(self):
        """Get the Pinecone index."""
        if self._index is None:
            self.initialize()
        return self._index

    async def upsert_vectors(
        self,
        vectors: List[tuple],  # [(id, embedding, metadata), ...]
        namespace: str = "",
        db: Optional[Session] = None,
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Upsert vectors to Pinecone.

        Args:
            vectors: List of tuples (id, embedding, metadata)
            namespace: Optional namespace for multi-tenancy
            db: Database session for audit logging (optional)
            document_id: Document ID for tracking (optional)
            batch_size: Number of vectors to upsert in each batch (default: 100)

        Returns:
            Upsert response from Pinecone (last batch response)
        """
        start_time = time.time()
        audit_service = get_audit_service()
        status = "success"
        error_msg = None
        vector_count = len(vectors)
        last_response = {}

        try:
            # Process vectors in batches
            for i in range(0, vector_count, batch_size):
                batch = vectors[i : i + batch_size]
                logger.info(f"Upserting batch {i // batch_size + 1}: {len(batch)} vectors")
                
                last_response = self.index.upsert(
                    vectors=batch,
                    namespace=namespace
                )
            
            logger.info(f"Successfully upserted {vector_count} vectors to Pinecone in batches")

            # Log to audit table if db session provided
            if db:
                duration_ms = int((time.time() - start_time) * 1000)
                # Calculate write units (1 write unit = 1 vector upserted)
                write_units = vector_count

                audit_service.log_api_usage(
                    db=db,
                    service="pinecone",
                    operation="upsert",
                    status=status,
                    pinecone_operation="write",
                    pinecone_vector_count=vector_count,
                    pinecone_dimension=self.dimension,
                    pinecone_namespace=namespace if namespace else "default",
                    pinecone_write_units=write_units,
                    document_id=document_id,
                    duration_ms=duration_ms
                )

            return last_response
        except Exception as e:
            status = "failed"
            error_msg = str(e)
            logger.error(f"Error upserting vectors: {e}")

            # Log failure to audit
            if db:
                duration_ms = int((time.time() - start_time) * 1000)
                audit_service.log_api_usage(
                    db=db,
                    service="pinecone",
                    operation="upsert",
                    status=status,
                    pinecone_operation="write",
                    pinecone_vector_count=vector_count,
                    pinecone_dimension=self.dimension,
                    pinecone_namespace=namespace if namespace else "default",
                    error_message=error_msg,
                    document_id=document_id,
                    duration_ms=duration_ms
                )
            raise

    async def query(
        self,
        vector: List[float],
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
        namespace: str = "",
        include_metadata: bool = True,
        db: Optional[Session] = None,
        document_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Query Pinecone for similar vectors.

        Args:
            vector: Query embedding vector
            top_k: Number of results to return
            filter: Metadata filters
            namespace: Optional namespace
            include_metadata: Whether to include metadata in results
            db: Database session for audit logging (optional)
            document_id: Document ID for tracking (optional)

        Returns:
            Query results from Pinecone
        """
        start_time = time.time()
        audit_service = get_audit_service()
        status = "success"
        error_msg = None

        try:
            response = self.index.query(
                vector=vector,
                top_k=top_k,
                filter=filter,
                namespace=namespace,
                include_metadata=include_metadata,
                include_values=False
            )

            # Log to audit table if db session provided
            if db:
                duration_ms = int((time.time() - start_time) * 1000)
                # Calculate read units (1 read unit = top_k vectors queried)
                read_units = top_k
                actual_results = len(response.matches) if hasattr(response, 'matches') else 0

                audit_service.log_api_usage(
                    db=db,
                    service="pinecone",
                    operation="query",
                    status=status,
                    pinecone_operation="read",
                    pinecone_vector_count=actual_results,
                    pinecone_dimension=self.dimension,
                    pinecone_namespace=namespace if namespace else "default",
                    pinecone_read_units=read_units,
                    document_id=document_id,
                    duration_ms=duration_ms
                )

            return response
        except Exception as e:
            status = "failed"
            error_msg = str(e)
            logger.error(f"Error querying Pinecone: {e}")

            # Log failure to audit
            if db:
                duration_ms = int((time.time() - start_time) * 1000)
                audit_service.log_api_usage(
                    db=db,
                    service="pinecone",
                    operation="query",
                    status=status,
                    pinecone_operation="read",
                    pinecone_dimension=self.dimension,
                    pinecone_namespace=namespace if namespace else "default",
                    error_message=error_msg,
                    document_id=document_id,
                    duration_ms=duration_ms
                )
            raise

    async def delete_vectors(
        self,
        ids: List[str],
        namespace: str = ""
    ) -> Dict[str, Any]:
        """
        Delete vectors from Pinecone.

        Args:
            ids: List of vector IDs to delete
            namespace: Optional namespace

        Returns:
            Delete response from Pinecone
        """
        try:
            response = self.index.delete(
                ids=ids,
                namespace=namespace
            )
            logger.info(f"Deleted {len(ids)} vectors from Pinecone")
            return response
        except Exception as e:
            logger.error(f"Error deleting vectors: {e}")
            raise

    async def get_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        try:
            stats = self.index.describe_index_stats()
            # Convert Pinecone stats object to dictionary
            return {
                "dimension": stats.dimension,
                "index_fullness": stats.index_fullness,
                "total_vector_count": stats.total_vector_count,
                "namespaces": {
                    ns_name: {"vector_count": ns_stats.vector_count}
                    for ns_name, ns_stats in stats.namespaces.items()
                }
            }
        except Exception as e:
            logger.error(f"Error getting Pinecone stats: {e}")
            raise

    async def check_vectors_exist(
        self,
        ids: List[str],
        namespace: str = ""
    ) -> Dict[str, bool]:
        """
        Check if vectors exist in Pinecone.

        Args:
            ids: List of vector IDs to check
            namespace: Optional namespace

        Returns:
            Dictionary mapping vector IDs to existence boolean
        """
        try:
            result = {}
            # Pinecone doesn't have a direct "exists" check, so we fetch vectors
            # If a vector doesn't exist, it won't be in the response
            fetch_response = self.index.fetch(ids=ids, namespace=namespace)

            existing_ids = set(fetch_response.vectors.keys())
            for vector_id in ids:
                result[vector_id] = vector_id in existing_ids

            logger.info(f"Checked {len(ids)} vectors, {len(existing_ids)} exist")
            return result
        except Exception as e:
            logger.error(f"Error checking vector existence: {e}")
            raise

    async def fetch_vectors_by_filter(
        self,
        filter: Dict[str, Any],
        namespace: str = "",
        top_k: int = 10000
    ) -> List[str]:
        """
        Fetch vector IDs by metadata filter.

        Args:
            filter: Metadata filter (e.g., {"document_id": 123})
            namespace: Optional namespace
            top_k: Maximum number of IDs to return

        Returns:
            List of vector IDs matching the filter
        """
        try:
            # Query with a dummy vector to get IDs by filter
            # Use sparse query to avoid needing actual embeddings
            response = self.index.query(
                vector=[0.0] * self.dimension,
                filter=filter,
                namespace=namespace,
                top_k=top_k,
                include_metadata=False,
                include_values=False
            )

            vector_ids = [match.id for match in response.matches]
            logger.info(f"Found {len(vector_ids)} vectors matching filter")
            return vector_ids
        except Exception as e:
            logger.error(f"Error fetching vectors by filter: {e}")
            raise


# Global Pinecone client instance
pinecone_client = PineconeClient()
