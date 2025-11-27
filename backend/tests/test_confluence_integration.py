import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.document_service import DocumentService
from app.models.schemas import SourceType

@pytest.mark.asyncio
async def test_process_pdf_calls_confluence_client():
    # Mock dependencies
    mock_db = MagicMock()
    mock_pdf_processor = MagicMock()
    mock_pdf_processor.extract_text_from_file.return_value = {
        "text": "Sample content",
        "content_hash": "hash123",
        "metadata": {}
    }
    
    # Mock Confluence client
    mock_confluence_client = AsyncMock()
    
    # Mock Pinecone client
    mock_pinecone_client = AsyncMock()
    mock_pinecone_client.fetch_vectors_by_filter.return_value = []
    mock_pinecone_client.upsert_vectors.return_value = None
    
    # Mock Embedding Generator
    mock_embedding_generator = AsyncMock()
    mock_embedding_generator.embed_batch.return_value = [[0.1] * 384] # Mock embedding vector

    # Mock Chunker
    mock_chunker = MagicMock()
    mock_chunker.chunk_text.return_value = [{"content": "Chunk 1"}]

    with patch("app.services.document_service.get_pdf_processor", return_value=mock_pdf_processor), \
         patch("app.services.document_service.get_confluence_client", return_value=mock_confluence_client), \
         patch("app.services.document_service.get_embedding_generator", return_value=mock_embedding_generator), \
         patch("app.services.document_service.get_chunker", return_value=mock_chunker), \
         patch("app.services.document_service.pinecone_client", mock_pinecone_client):
        
        service = DocumentService()
        # Bypass file system ops
        service.storage_dir = MagicMock()
        service.pdf_processor.save_as_markdown = MagicMock()
        
        # Mock database query to return None (no existing document)
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Call method
        await service.process_pdf(
            db=mock_db,
            file_path="test.pdf",
            filename="test.pdf",
            metadata={"industry": "Tech", "author": "Tester"},
            skip_existing=True
        )
        
        # Verify Confluence client was called
        mock_confluence_client.create_page.assert_called_once()
        call_args = mock_confluence_client.create_page.call_args[1]
        assert call_args["title"] == "Doc: test.pdf"
        assert "Tech" in call_args["tags"]
        assert "Tester" in call_args["tags"]

@pytest.mark.asyncio
async def test_process_url_calls_confluence_client():
    # Mock dependencies
    mock_db = MagicMock()
    mock_jina_scraper = AsyncMock()
    mock_jina_scraper.scrape_url.return_value = {
        "text": "Web content",
        "content_hash": "webhash123"
    }
    
    # Mock Confluence client
    mock_confluence_client = AsyncMock()
    
    # Mock Pinecone client
    mock_pinecone_client = AsyncMock()
    mock_pinecone_client.fetch_vectors_by_filter.return_value = []
    mock_pinecone_client.upsert_vectors.return_value = None
    
    # Mock Embedding Generator
    mock_embedding_generator = AsyncMock()
    mock_embedding_generator.embed_batch.return_value = [[0.1] * 384]

    # Mock Chunker
    mock_chunker = MagicMock()
    mock_chunker.chunk_text.return_value = [{"content": "Chunk 1"}]
    
    with patch("app.services.document_service.get_jina_scraper", return_value=mock_jina_scraper), \
         patch("app.services.document_service.get_confluence_client", return_value=mock_confluence_client), \
         patch("app.services.document_service.get_embedding_generator", return_value=mock_embedding_generator), \
         patch("app.services.document_service.get_chunker", return_value=mock_chunker), \
         patch("app.services.document_service.pinecone_client", mock_pinecone_client):
        
        service = DocumentService()
        # Bypass file system ops
        service.storage_dir = MagicMock()
        
        # Mock database query to return None (no existing document)
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Call method
        await service.process_url(
            db=mock_db,
            url="http://example.com",
            metadata={"industry": "Finance", "author": "Analyst"},
            skip_existing=True
        )
        
        # Verify Confluence client was called
        mock_confluence_client.create_page.assert_called_once()
        call_args = mock_confluence_client.create_page.call_args[1]
        assert call_args["title"] == "Web: http://example.com"
        assert "Finance" in call_args["tags"]
        assert "Analyst" in call_args["tags"]
