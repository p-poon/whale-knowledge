from PyPDF2 import PdfReader
from typing import Dict, Any, Optional
import io
import logging
import hashlib
from pathlib import Path

logger = logging.getLogger(__name__)


class PDFProcessor:
    """Process PDF documents and extract text."""

    @staticmethod
    def extract_text_from_file(file_path: str) -> Dict[str, Any]:
        """
        Extract text from a PDF file.

        Args:
            file_path: Path to PDF file

        Returns:
            Dictionary with extracted text and metadata
        """
        try:
            reader = PdfReader(file_path)

            # Extract metadata
            metadata = {}
            if reader.metadata:
                metadata = {
                    "title": reader.metadata.get("/Title", ""),
                    "author": reader.metadata.get("/Author", ""),
                    "subject": reader.metadata.get("/Subject", ""),
                    "creator": reader.metadata.get("/Creator", ""),
                }

            # Extract text from all pages
            text_parts = []
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                if text.strip():
                    text_parts.append(text)

            full_text = "\n\n".join(text_parts)

            # Calculate content hash
            content_hash = hashlib.sha256(full_text.encode()).hexdigest()

            result = {
                "text": full_text,
                "page_count": len(reader.pages),
                "metadata": metadata,
                "content_hash": content_hash
            }

            logger.info(f"Extracted text from PDF: {file_path} ({len(reader.pages)} pages)")
            return result

        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_path}: {e}")
            raise

    @staticmethod
    def extract_text_from_bytes(pdf_bytes: bytes) -> Dict[str, Any]:
        """
        Extract text from PDF bytes.

        Args:
            pdf_bytes: PDF file content as bytes

        Returns:
            Dictionary with extracted text and metadata
        """
        try:
            pdf_file = io.BytesIO(pdf_bytes)
            reader = PdfReader(pdf_file)

            # Extract metadata
            metadata = {}
            if reader.metadata:
                metadata = {
                    "title": reader.metadata.get("/Title", ""),
                    "author": reader.metadata.get("/Author", ""),
                    "subject": reader.metadata.get("/Subject", ""),
                    "creator": reader.metadata.get("/Creator", ""),
                }

            # Extract text from all pages
            text_parts = []
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                if text.strip():
                    text_parts.append(text)

            full_text = "\n\n".join(text_parts)

            # Calculate content hash
            content_hash = hashlib.sha256(full_text.encode()).hexdigest()

            result = {
                "text": full_text,
                "page_count": len(reader.pages),
                "metadata": metadata,
                "content_hash": content_hash
            }

            logger.info(f"Extracted text from PDF bytes ({len(reader.pages)} pages)")
            return result

        except Exception as e:
            logger.error(f"Error extracting text from PDF bytes: {e}")
            raise

    @staticmethod
    def save_as_markdown(
        text: str,
        output_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Save extracted text as markdown file.

        Args:
            text: Extracted text
            output_path: Path to save markdown file
            metadata: Optional metadata to include in frontmatter

        Returns:
            Path to saved markdown file
        """
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # Create markdown content with frontmatter
            content_parts = []

            if metadata:
                content_parts.append("---")
                for key, value in metadata.items():
                    if value:
                        content_parts.append(f"{key}: {value}")
                content_parts.append("---")
                content_parts.append("")

            content_parts.append(text)

            markdown_content = "\n".join(content_parts)

            # Write to file
            output_file.write_text(markdown_content, encoding="utf-8")

            logger.info(f"Saved markdown file: {output_path}")
            return str(output_file)

        except Exception as e:
            logger.error(f"Error saving markdown file {output_path}: {e}")
            raise


# Global PDF processor instance
def get_pdf_processor() -> PDFProcessor:
    """Get PDF processor instance."""
    return PDFProcessor()
