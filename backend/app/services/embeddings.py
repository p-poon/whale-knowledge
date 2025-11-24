from sentence_transformers import SentenceTransformer
from typing import List
import logging
import asyncio
from functools import lru_cache

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Generate embeddings for text using sentence transformers."""

    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.embedding_model
        self._model = None
        logger.info(f"Initializing embedding generator with model: {self.model_name}")

    @property
    def model(self):
        """Lazy load the model."""
        if self._model is None:
            self._model = SentenceTransformer(self.model_name)
            logger.info(f"Loaded embedding model: {self.model_name}")
        return self._model

    async def embed(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Input text to embed

        Returns:
            List of floats representing the embedding
        """
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None,
                lambda: self.model.encode(text, convert_to_tensor=False)
            )
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    async def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing

        Returns:
            List of embeddings
        """
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None,
                lambda: self.model.encode(
                    texts,
                    batch_size=batch_size,
                    convert_to_tensor=False,
                    show_progress_bar=len(texts) > 100
                )
            )
            return [emb.tolist() for emb in embeddings]
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            raise

    def get_dimension(self) -> int:
        """Get the dimension of the embeddings."""
        return self.model.get_sentence_embedding_dimension()


# Global embedding generator instance
@lru_cache()
def get_embedding_generator() -> EmbeddingGenerator:
    """Get or create embedding generator singleton."""
    return EmbeddingGenerator()
