from typing import List, Dict, Any
import re
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class TextChunker:
    """Chunk text into smaller pieces for embedding."""

    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None
    ):
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap

    def chunk_text(
        self,
        text: str,
        metadata: Dict[str, Any] = None,
        method: str = "fixed"
    ) -> List[Dict[str, Any]]:
        """
        Chunk text into smaller pieces.

        Args:
            text: Input text to chunk
            metadata: Additional metadata to attach to chunks
            method: Chunking method ('fixed', 'sentence', 'paragraph')

        Returns:
            List of chunk dictionaries with content and metadata
        """
        if method == "fixed":
            return self._chunk_fixed_size(text, metadata)
        elif method == "sentence":
            return self._chunk_by_sentence(text, metadata)
        elif method == "paragraph":
            return self._chunk_by_paragraph(text, metadata)
        else:
            raise ValueError(f"Unknown chunking method: {method}")

    def _chunk_fixed_size(
        self,
        text: str,
        metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Chunk text into fixed-size pieces with overlap.

        Args:
            text: Input text
            metadata: Additional metadata

        Returns:
            List of chunks
        """
        chunks = []
        start = 0
        text_length = len(text)

        chunk_index = 0
        while start < text_length:
            end = start + self.chunk_size

            # Try to break at word boundary
            if end < text_length:
                # Look for space within overlap window
                space_pos = text.rfind(' ', end - 50, end)
                if space_pos != -1 and space_pos > start:
                    end = space_pos

            chunk_text = text[start:end].strip()

            if chunk_text:
                chunk = {
                    "content": chunk_text,
                    "chunk_index": chunk_index,
                    "start_char": start,
                    "end_char": end,
                    "metadata": metadata or {}
                }
                chunks.append(chunk)
                chunk_index += 1

            # Move start position with overlap
            start = end - self.chunk_overlap

        logger.info(f"Created {len(chunks)} fixed-size chunks")
        return chunks

    def _chunk_by_sentence(
        self,
        text: str,
        metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Chunk text by sentences, grouping to approximate chunk size.

        Args:
            text: Input text
            metadata: Additional metadata

        Returns:
            List of chunks
        """
        # Simple sentence splitting (can be improved with NLTK/spaCy)
        sentences = re.split(r'(?<=[.!?])\s+', text)

        chunks = []
        current_chunk = []
        current_length = 0
        chunk_index = 0

        for sentence in sentences:
            sentence_length = len(sentence)

            if current_length + sentence_length > self.chunk_size and current_chunk:
                # Create chunk from accumulated sentences
                chunk_text = ' '.join(current_chunk)
                chunk = {
                    "content": chunk_text,
                    "chunk_index": chunk_index,
                    "metadata": metadata or {}
                }
                chunks.append(chunk)
                chunk_index += 1

                # Start new chunk with overlap (keep last sentence if overlap allows)
                if self.chunk_overlap > 0 and len(current_chunk) > 1:
                    overlap_text = current_chunk[-1]
                    current_chunk = [overlap_text, sentence]
                    current_length = len(overlap_text) + sentence_length
                else:
                    current_chunk = [sentence]
                    current_length = sentence_length
            else:
                current_chunk.append(sentence)
                current_length += sentence_length

        # Add final chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunk = {
                "content": chunk_text,
                "chunk_index": chunk_index,
                "metadata": metadata or {}
            }
            chunks.append(chunk)

        logger.info(f"Created {len(chunks)} sentence-based chunks")
        return chunks

    def _chunk_by_paragraph(
        self,
        text: str,
        metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Chunk text by paragraphs.

        Args:
            text: Input text
            metadata: Additional metadata

        Returns:
            List of chunks
        """
        # Split by double newlines or more
        paragraphs = re.split(r'\n\s*\n', text)

        chunks = []
        chunk_index = 0

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            # If paragraph is too long, fall back to fixed-size chunking
            if len(paragraph) > self.chunk_size * 1.5:
                sub_chunks = self._chunk_fixed_size(paragraph, metadata)
                for sub_chunk in sub_chunks:
                    sub_chunk["chunk_index"] = chunk_index
                    chunks.append(sub_chunk)
                    chunk_index += 1
            else:
                chunk = {
                    "content": paragraph,
                    "chunk_index": chunk_index,
                    "metadata": metadata or {}
                }
                chunks.append(chunk)
                chunk_index += 1

        logger.info(f"Created {len(chunks)} paragraph-based chunks")
        return chunks


# Global chunker instance
def get_chunker() -> TextChunker:
    """Get text chunker instance."""
    return TextChunker()
