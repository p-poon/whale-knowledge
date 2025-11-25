"""Document selector service for AI-powered document suggestion."""

from typing import List, Dict, Any, Optional
import logging
from sqlalchemy import desc, func

from app.core.database import SessionLocal, Document
from app.core.pinecone_client import pinecone_client
from app.services.embeddings import get_embedding_generator
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


class DocumentSelectorService:
    """Service for selecting and suggesting documents for content generation."""

    def __init__(self):
        """Initialize document selector service."""
        self.embedding_generator = get_embedding_generator()

    async def suggest_documents(
        self,
        topic: str,
        content_type: str,
        max_documents: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Use AI to suggest relevant documents for a given topic.

        Args:
            topic: The topic for content generation
            content_type: Type of content (whitepaper, article, blog)
            max_documents: Maximum number of documents to suggest
            filters: Optional metadata filters (industry, author, etc.)

        Returns:
            List of suggested documents with relevance scores
        """
        logger.info(f"Suggesting documents for topic: {topic[:100]}")

        # Step 1: Get semantically similar documents using vector search
        query_embedding = await self.embedding_generator.embed(topic)

        # Build Pinecone filter if provided
        pinecone_filter = None
        if filters:
            pinecone_filter = self._build_pinecone_filter(filters)

        # Query Pinecone for top matches (get more than max_documents for filtering)
        pinecone_response = await pinecone_client.query(
            vector=query_embedding,
            top_k=max_documents * 3,  # Get 3x to have options after deduplication
            filter=pinecone_filter,
            include_metadata=True
        )

        # Step 2: Extract unique documents and their relevance scores
        doc_scores = {}  # document_id -> max_score
        doc_chunks = {}  # document_id -> chunk_count

        for match in pinecone_response.get("matches", []):
            try:
                chunk_id = match["id"]
                score = match["score"]

                # Extract document ID from chunk ID (format: doc_{doc_id}_chunk_{chunk_idx})
                doc_id = int(chunk_id.split("_")[1])

                # Track highest score for each document
                if doc_id not in doc_scores or score > doc_scores[doc_id]:
                    doc_scores[doc_id] = score

                # Count chunks per document
                doc_chunks[doc_id] = doc_chunks.get(doc_id, 0) + 1

            except (IndexError, ValueError) as e:
                logger.warning(f"Invalid chunk ID format: {chunk_id}: {e}")
                continue

        # Step 3: Fetch document metadata from database
        if not doc_scores:
            logger.warning(f"No documents found for topic: {topic[:100]}")
            return []

        db = SessionLocal()
        try:
            document_ids = list(doc_scores.keys())
            documents = db.query(Document).filter(
                Document.id.in_(document_ids),
                Document.status == "completed"
            ).all()

            # Step 4: Build suggested documents list
            suggested_docs = []
            for doc in documents:
                relevance_score = doc_scores[doc.id]
                chunks_found = doc_chunks[doc.id]

                suggested_docs.append({
                    "document_id": doc.id,
                    "filename": doc.filename,
                    "relevance_score": float(relevance_score),
                    "chunk_count": chunks_found,
                    "total_chunks": doc.chunk_count,
                    "industry": doc.industry,
                    "author": doc.author,
                    "source_type": doc.source_type,
                    "document_date": doc.document_date.isoformat() if doc.document_date else None,
                })

            # Sort by relevance score (descending)
            suggested_docs.sort(key=lambda x: x["relevance_score"], reverse=True)

            # Limit to max_documents
            suggested_docs = suggested_docs[:max_documents]

            # Step 5: Use LLM to add relevance explanations (optional but valuable)
            if suggested_docs:
                try:
                    suggested_docs = await self._add_relevance_explanations(
                        topic, content_type, suggested_docs
                    )
                except Exception as e:
                    logger.warning(f"Failed to add relevance explanations: {e}")
                    # Continue without explanations

            logger.info(f"Suggested {len(suggested_docs)} documents for topic")
            return suggested_docs

        finally:
            db.close()

    async def _add_relevance_explanations(
        self,
        topic: str,
        content_type: str,
        documents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Use LLM to generate relevance explanations for suggested documents.

        Args:
            topic: The generation topic
            content_type: Type of content
            documents: List of suggested documents

        Returns:
            Documents with added relevance_explanation field
        """
        # Create a prompt for the LLM
        doc_list = "\n".join([
            f"{i+1}. {doc['filename']} (Score: {doc['relevance_score']:.3f}, Industry: {doc.get('industry', 'N/A')})"
            for i, doc in enumerate(documents)
        ])

        prompt = f"""You are helping select relevant documents for content generation.

Topic: {topic}
Content Type: {content_type}

Here are the suggested documents:
{doc_list}

For each document, provide a brief (1-2 sentence) explanation of why it's relevant to the topic.
Format your response as a numbered list matching the documents above.

Keep explanations concise and specific to how the document relates to the topic."""

        try:
            result = await llm_service.generate(
                prompt=prompt,
                provider="anthropic",  # Use Claude for this analysis task
                model=None,  # Use default
                temperature=0.3,  # Lower temperature for more focused responses
                max_tokens=500
            )

            explanations_text = result["content"]

            # Parse explanations (simple line-by-line parsing)
            explanation_lines = [
                line.strip()
                for line in explanations_text.split("\n")
                if line.strip() and (line.strip()[0].isdigit() or line.strip().startswith("-"))
            ]

            # Add explanations to documents
            for i, doc in enumerate(documents):
                if i < len(explanation_lines):
                    # Remove numbering prefix
                    explanation = explanation_lines[i]
                    explanation = explanation.lstrip("0123456789.-) ").strip()
                    doc["relevance_explanation"] = explanation
                else:
                    doc["relevance_explanation"] = "Relevant to the topic based on content similarity."

        except Exception as e:
            logger.error(f"Failed to generate relevance explanations: {e}")
            # Add default explanations
            for doc in documents:
                doc["relevance_explanation"] = "Relevant to the topic based on content similarity."

        return documents

    def validate_document_ids(self, document_ids: List[int]) -> Dict[str, Any]:
        """
        Validate that document IDs exist and are ready for use.

        Args:
            document_ids: List of document IDs to validate

        Returns:
            Dict with:
                - valid: List of valid document IDs
                - invalid: List of invalid document IDs
                - documents: Dict mapping doc_id to document info
        """
        if not document_ids:
            return {
                "valid": [],
                "invalid": [],
                "documents": {}
            }

        db = SessionLocal()
        try:
            # Query for all documents
            documents = db.query(Document).filter(
                Document.id.in_(document_ids)
            ).all()

            found_ids = set()
            valid_docs = []
            doc_info = {}

            for doc in documents:
                found_ids.add(doc.id)

                # Only include completed documents
                if doc.status == "completed" and doc.chunk_count > 0:
                    valid_docs.append(doc.id)
                    doc_info[doc.id] = {
                        "id": doc.id,
                        "filename": doc.filename,
                        "chunk_count": doc.chunk_count,
                        "industry": doc.industry,
                        "author": doc.author,
                        "source_type": doc.source_type,
                    }

            # Find invalid IDs (not found or not completed)
            invalid_docs = [
                doc_id for doc_id in document_ids
                if doc_id not in valid_docs
            ]

            return {
                "valid": valid_docs,
                "invalid": invalid_docs,
                "documents": doc_info
            }

        finally:
            db.close()

    async def rank_by_relevance(
        self,
        topic: str,
        document_ids: List[int]
    ) -> List[Dict[str, Any]]:
        """
        Rank documents by relevance to a topic.

        Args:
            topic: The topic to rank against
            document_ids: List of document IDs to rank

        Returns:
            List of documents with relevance scores, sorted by score
        """
        if not document_ids:
            return []

        # Get query embedding
        query_embedding = await self.embedding_generator.embed(topic)

        # Query Pinecone for these specific documents
        # We'll filter by document_id in metadata
        doc_scores = {}
        doc_chunks = {}

        # Query multiple times with different filters (Pinecone limitation workaround)
        # In practice, we query broadly and filter results
        pinecone_response = await pinecone_client.query(
            vector=query_embedding,
            top_k=100,  # Get enough to cover all chunks from selected docs
            include_metadata=True
        )

        for match in pinecone_response.get("matches", []):
            try:
                chunk_id = match["id"]
                score = match["score"]
                doc_id = int(chunk_id.split("_")[1])

                # Only include scores for requested documents
                if doc_id not in document_ids:
                    continue

                # Track highest score for each document
                if doc_id not in doc_scores or score > doc_scores[doc_id]:
                    doc_scores[doc_id] = score

                doc_chunks[doc_id] = doc_chunks.get(doc_id, 0) + 1

            except (IndexError, ValueError):
                continue

        # Fetch document metadata
        db = SessionLocal()
        try:
            documents = db.query(Document).filter(
                Document.id.in_(document_ids),
                Document.status == "completed"
            ).all()

            ranked_docs = []
            for doc in documents:
                relevance_score = doc_scores.get(doc.id, 0.0)

                ranked_docs.append({
                    "document_id": doc.id,
                    "filename": doc.filename,
                    "relevance_score": float(relevance_score),
                    "chunk_count": doc_chunks.get(doc.id, 0),
                    "total_chunks": doc.chunk_count,
                    "industry": doc.industry,
                    "author": doc.author,
                })

            # Sort by relevance score (descending)
            ranked_docs.sort(key=lambda x: x["relevance_score"], reverse=True)

            return ranked_docs

        finally:
            db.close()

    async def get_document_context(
        self,
        document_ids: List[int],
        topic: str,
        max_chunks_per_doc: int = 10
    ) -> Dict[int, List[str]]:
        """
        Get relevant chunks from selected documents for a topic.

        Args:
            document_ids: List of document IDs to get context from
            topic: The topic to find relevant chunks for
            max_chunks_per_doc: Maximum chunks to retrieve per document

        Returns:
            Dict mapping document_id to list of relevant chunk texts
        """
        if not document_ids:
            return {}

        # Get query embedding
        query_embedding = await self.embedding_generator.embed(topic)

        # Query Pinecone for relevant chunks
        pinecone_response = await pinecone_client.query(
            vector=query_embedding,
            top_k=max_chunks_per_doc * len(document_ids),
            include_metadata=True
        )

        # Organize chunks by document
        doc_chunks = {}  # document_id -> list of (score, text) tuples

        for match in pinecone_response.get("matches", []):
            try:
                chunk_id = match["id"]
                score = match["score"]
                metadata = match.get("metadata", {})
                text = metadata.get("text", "")

                # Extract document ID
                doc_id = int(chunk_id.split("_")[1])

                # Only include chunks from requested documents
                if doc_id not in document_ids:
                    continue

                if doc_id not in doc_chunks:
                    doc_chunks[doc_id] = []

                doc_chunks[doc_id].append((score, text))

            except (IndexError, ValueError):
                continue

        # Sort chunks by score and limit per document
        result = {}
        for doc_id, chunks in doc_chunks.items():
            # Sort by score (descending)
            chunks.sort(key=lambda x: x[0], reverse=True)

            # Limit to max_chunks_per_doc
            chunks = chunks[:max_chunks_per_doc]

            # Extract just the text
            result[doc_id] = [text for score, text in chunks]

        return result

    def _build_pinecone_filter(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build Pinecone metadata filter from user filters.

        Args:
            filters: User-provided filters

        Returns:
            Pinecone filter dict
        """
        pinecone_filter = {}

        if "industry" in filters and filters["industry"]:
            pinecone_filter["industry"] = {"$eq": filters["industry"]}

        if "author" in filters and filters["author"]:
            pinecone_filter["author"] = {"$eq": filters["author"]}

        if "source_type" in filters and filters["source_type"]:
            pinecone_filter["source_type"] = {"$eq": filters["source_type"]}

        return pinecone_filter if pinecone_filter else None


# Global instance
document_selector_service = DocumentSelectorService()
