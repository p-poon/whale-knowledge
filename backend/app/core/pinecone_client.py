from pinecone import Pinecone, ServerlessSpec
from typing import List, Dict, Any, Optional
import logging

from app.core.config import settings

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
                        region="us-west-2"
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
        namespace: str = ""
    ) -> Dict[str, Any]:
        """
        Upsert vectors to Pinecone.

        Args:
            vectors: List of tuples (id, embedding, metadata)
            namespace: Optional namespace for multi-tenancy

        Returns:
            Upsert response from Pinecone
        """
        try:
            response = self.index.upsert(
                vectors=vectors,
                namespace=namespace
            )
            logger.info(f"Upserted {len(vectors)} vectors to Pinecone")
            return response
        except Exception as e:
            logger.error(f"Error upserting vectors: {e}")
            raise

    async def query(
        self,
        vector: List[float],
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
        namespace: str = "",
        include_metadata: bool = True
    ) -> Dict[str, Any]:
        """
        Query Pinecone for similar vectors.

        Args:
            vector: Query embedding vector
            top_k: Number of results to return
            filter: Metadata filters
            namespace: Optional namespace
            include_metadata: Whether to include metadata in results

        Returns:
            Query results from Pinecone
        """
        try:
            response = self.index.query(
                vector=vector,
                top_k=top_k,
                filter=filter,
                namespace=namespace,
                include_metadata=include_metadata,
                include_values=False
            )
            return response
        except Exception as e:
            logger.error(f"Error querying Pinecone: {e}")
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
            return stats
        except Exception as e:
            logger.error(f"Error getting Pinecone stats: {e}")
            raise


# Global Pinecone client instance
pinecone_client = PineconeClient()
