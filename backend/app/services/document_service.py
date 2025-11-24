from typing import List, Dict, Any, Optional
import logging
import hashlib
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.database import Document, ProcessingJob
from app.core.pinecone_client import pinecone_client
from app.services.embeddings import get_embedding_generator
from app.services.chunking import get_chunker
from app.services.pdf_processor import get_pdf_processor
from app.services.jina_scraper import get_jina_scraper
from app.models.schemas import SourceType

logger = logging.getLogger(__name__)


class DocumentService:
    """Service for document management and processing."""

    def __init__(self):
        self.embedding_generator = get_embedding_generator()
        self.chunker = get_chunker()
        self.pdf_processor = get_pdf_processor()
        self.jina_scraper = get_jina_scraper()
        self.storage_dir = Path("./storage/documents")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    async def process_pdf(
        self,
        db: Session,
        file_path: str,
        filename: str,
        metadata: Dict[str, Any],
        skip_existing: bool = True
    ) -> Document:
        """
        Process a PDF file and add to knowledge base.

        Args:
            db: Database session
            file_path: Path to PDF file
            filename: Original filename
            metadata: Document metadata (industry, author, etc.)
            skip_existing: If True, skip vector creation if vectors already exist for this document

        Returns:
            Created Document object
        """
        try:
            # Extract text from PDF
            pdf_result = self.pdf_processor.extract_text_from_file(file_path)
            text = pdf_result["text"]
            content_hash = pdf_result["content_hash"]

            # Check if document already exists
            existing = db.query(Document).filter(
                Document.content_hash == content_hash
            ).first()
            if existing:
                logger.info(f"Document with hash {content_hash} already exists")
                return existing

            # Save as markdown
            markdown_path = self.storage_dir / f"{content_hash}.md"
            self.pdf_processor.save_as_markdown(
                text=text,
                output_path=str(markdown_path),
                metadata=pdf_result["metadata"]
            )

            # Create document record
            document = Document(
                filename=filename,
                content_hash=content_hash,
                source_type=SourceType.PDF.value,
                industry=metadata.get("industry"),
                author=metadata.get("author") or pdf_result["metadata"].get("author"),
                document_date=metadata.get("document_date"),
                raw_content_path=str(markdown_path),
                status="processing"
            )
            db.add(document)
            db.commit()
            db.refresh(document)

            # Create processing job
            job = ProcessingJob(
                document_id=document.id,
                job_type="ingest",
                status="running"
            )
            db.add(job)
            db.commit()

            # Process and embed chunks
            await self._process_and_embed(db, document, text, skip_existing)

            # Update job status
            job.status = "completed"
            job.completed_at = datetime.utcnow()
            job.progress = 100
            db.commit()

            logger.info(f"Successfully processed PDF: {filename}")
            return document

        except Exception as e:
            logger.error(f"Error processing PDF {filename}: {e}")
            if document:
                document.status = "error"
                document.error_message = str(e)
                db.commit()
            raise

    async def process_url(
        self,
        db: Session,
        url: str,
        metadata: Dict[str, Any],
        skip_existing: bool = True
    ) -> Document:
        """
        Scrape URL and add to knowledge base.

        Args:
            db: Database session
            url: URL to scrape
            metadata: Document metadata
            skip_existing: If True, skip vector creation if vectors already exist for this document

        Returns:
            Created Document object
        """
        try:
            # Scrape content
            scrape_result = await self.jina_scraper.scrape_url(url)
            text = scrape_result["text"]
            content_hash = scrape_result["content_hash"]

            # Check if document already exists
            existing = db.query(Document).filter(
                Document.content_hash == content_hash
            ).first()
            if existing:
                logger.info(f"Document with hash {content_hash} already exists")
                return existing

            # Save as markdown
            markdown_path = self.storage_dir / f"{content_hash}.md"
            await self.jina_scraper.scrape_and_save(
                url=url,
                output_path=str(markdown_path),
                metadata=metadata
            )

            # Create document record
            document = Document(
                filename=url,
                content_hash=content_hash,
                source_type=SourceType.WEB.value,
                source_url=url,
                industry=metadata.get("industry"),
                author=metadata.get("author"),
                document_date=metadata.get("document_date"),
                raw_content_path=str(markdown_path),
                status="processing"
            )
            db.add(document)
            db.commit()
            db.refresh(document)

            # Process and embed chunks
            await self._process_and_embed(db, document, text, skip_existing)

            logger.info(f"Successfully processed URL: {url}")
            return document

        except Exception as e:
            logger.error(f"Error processing URL {url}: {e}")
            if document:
                document.status = "error"
                document.error_message = str(e)
                db.commit()
            raise

    async def _process_and_embed(
        self,
        db: Session,
        document: Document,
        text: str,
        skip_existing: bool = True
    ):
        """
        Chunk text, generate embeddings, and store in Pinecone.

        Args:
            db: Database session
            document: Document object
            text: Document text content
            skip_existing: If True, skip upserting vectors that already exist in Pinecone
        """
        try:
            # Check if vectors already exist for this document
            existing_vector_ids = await pinecone_client.fetch_vectors_by_filter(
                filter={"document_id": document.id}
            )

            if existing_vector_ids:
                if skip_existing:
                    logger.info(
                        f"Document {document.id} already has {len(existing_vector_ids)} "
                        f"vectors in Pinecone. Skipping vector creation."
                    )
                    document.status = "completed"
                    document.chunk_count = len(existing_vector_ids)
                    document.vector_ids = existing_vector_ids
                    db.commit()
                    return
                else:
                    logger.info(
                        f"Document {document.id} has {len(existing_vector_ids)} existing vectors. "
                        f"Will update with new vectors."
                    )
                    # Delete existing vectors before creating new ones
                    await pinecone_client.delete_vectors(existing_vector_ids)

            # Create document metadata for chunks
            doc_metadata = {
                "document_id": document.id,
                "filename": document.filename,
                "source_type": document.source_type,
                "industry": document.industry,
                "author": document.author,
            }

            # Chunk text
            chunks = self.chunker.chunk_text(text, metadata=doc_metadata)

            if not chunks:
                logger.warning(f"No chunks created for document {document.id}")
                document.status = "completed"
                document.chunk_count = 0
                db.commit()
                return

            # Generate embeddings for all chunks
            chunk_texts = [chunk["content"] for chunk in chunks]
            embeddings = await self.embedding_generator.embed_batch(chunk_texts)

            # Prepare vectors for Pinecone
            vectors = []
            vector_ids = []

            for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                vector_id = f"doc_{document.id}_chunk_{idx}"
                vector_ids.append(vector_id)

                vector_metadata = {
                    "text": chunk["content"],
                    "chunk_index": idx,
                    "document_id": document.id,
                    "filename": document.filename,
                    "source_type": document.source_type,
                }

                if document.industry:
                    vector_metadata["industry"] = document.industry
                if document.author:
                    vector_metadata["author"] = document.author

                vectors.append((vector_id, embedding, vector_metadata))

            # Upsert to Pinecone
            await pinecone_client.upsert_vectors(vectors)

            # Update document record
            document.status = "completed"
            document.chunk_count = len(chunks)
            document.vector_ids = vector_ids
            db.commit()

            logger.info(f"Embedded {len(chunks)} chunks for document {document.id}")

        except Exception as e:
            logger.error(f"Error processing chunks for document {document.id}: {e}")
            document.status = "error"
            document.error_message = str(e)
            db.commit()
            raise

    async def delete_document(self, db: Session, document_id: int):
        """
        Delete document and its vectors from knowledge base.

        Args:
            db: Database session
            document_id: Document ID to delete
        """
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                raise ValueError(f"Document {document_id} not found")

            # Delete vectors from Pinecone
            if document.vector_ids:
                await pinecone_client.delete_vectors(document.vector_ids)

            # Delete markdown file
            if document.raw_content_path:
                markdown_path = Path(document.raw_content_path)
                if markdown_path.exists():
                    markdown_path.unlink()

            # Delete document record
            db.delete(document)
            db.commit()

            logger.info(f"Deleted document {document_id}")

        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {e}")
            raise


# Global document service instance
def get_document_service() -> DocumentService:
    """Get document service instance."""
    return DocumentService()
