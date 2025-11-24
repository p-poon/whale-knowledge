import httpx
from typing import Dict, Any, Optional
import logging
import hashlib
import time
from pathlib import Path
from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.audit_service import get_audit_service

logger = logging.getLogger(__name__)


class JinaScraper:
    """Scrape web content using Jina Reader API."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.jina_api_key
        self.base_url = "https://r.jina.ai"

    async def scrape_url(
        self,
        url: str,
        db: Optional[Session] = None,
        document_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Scrape content from a URL using Jina Reader.

        Args:
            url: URL to scrape
            db: Database session for audit logging (optional)
            document_id: Document ID for tracking (optional)

        Returns:
            Dictionary with scraped content and metadata
        """
        start_time = time.time()
        audit_service = get_audit_service()
        status = "success"
        error_msg = None
        jina_url = f"{self.base_url}/{url}"

        try:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            # Jina Reader API endpoint
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(jina_url, headers=headers)
                response.raise_for_status()

                # Jina returns markdown-formatted text
                content = response.text

                # Calculate content hash
                content_hash = hashlib.sha256(content.encode()).hexdigest()

                # Extract metadata from headers if available
                metadata = {
                    "source_url": url,
                    "content_type": response.headers.get("content-type", ""),
                    "scraped_at": response.headers.get("date", ""),
                }

                result = {
                    "text": content,
                    "metadata": metadata,
                    "content_hash": content_hash
                }

                # Calculate metrics for audit logging
                input_chars = len(url)
                output_chars = len(content)
                estimated_tokens = (input_chars + output_chars) // 4  # Rough estimate

                # Extract rate limit and usage headers
                rate_limit_headers = {
                    key: value for key, value in response.headers.items()
                    if key.lower().startswith(('x-ratelimit', 'x-tokens', 'x-usage', 'x-request'))
                }

                logger.info(f"Successfully scraped URL: {url}")

                # Log to audit table if db session provided
                if db:
                    duration_ms = int((time.time() - start_time) * 1000)
                    audit_service.log_api_usage(
                        db=db,
                        service="jina",
                        operation="scrape",
                        status=status,
                        endpoint=jina_url,
                        jina_input_chars=input_chars,
                        jina_output_chars=output_chars,
                        jina_estimated_tokens=estimated_tokens,
                        jina_response_headers=rate_limit_headers if rate_limit_headers else None,
                        document_id=document_id,
                        duration_ms=duration_ms
                    )

                return result

        except httpx.HTTPStatusError as e:
            status = "failed"
            error_msg = f"HTTP error: {str(e)}"
            logger.error(f"HTTP error scraping {url}: {e}")

            # Log failure to audit
            if db:
                duration_ms = int((time.time() - start_time) * 1000)
                audit_service.log_api_usage(
                    db=db,
                    service="jina",
                    operation="scrape",
                    status=status,
                    endpoint=jina_url,
                    error_message=error_msg,
                    document_id=document_id,
                    duration_ms=duration_ms
                )
            raise
        except Exception as e:
            status = "failed"
            error_msg = str(e)
            logger.error(f"Error scraping {url}: {e}")

            # Log failure to audit
            if db:
                duration_ms = int((time.time() - start_time) * 1000)
                audit_service.log_api_usage(
                    db=db,
                    service="jina",
                    operation="scrape",
                    status=status,
                    endpoint=jina_url,
                    error_message=error_msg,
                    document_id=document_id,
                    duration_ms=duration_ms
                )
            raise

    async def scrape_and_save(
        self,
        url: str,
        output_path: str,
        metadata: Optional[Dict[str, Any]] = None,
        db: Optional[Session] = None,
        document_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Scrape URL and save as markdown file.

        Args:
            url: URL to scrape
            output_path: Path to save markdown file
            metadata: Optional additional metadata
            db: Database session for audit logging (optional)
            document_id: Document ID for tracking (optional)

        Returns:
            Dictionary with scrape results and file path
        """
        try:
            # Scrape content (with audit logging)
            result = await self.scrape_url(url, db=db, document_id=document_id)

            # Merge metadata
            all_metadata = {**result["metadata"], **(metadata or {})}

            # Save as markdown
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # Create markdown content with frontmatter
            content_parts = ["---"]
            for key, value in all_metadata.items():
                if value:
                    content_parts.append(f"{key}: {value}")
            content_parts.append("---")
            content_parts.append("")
            content_parts.append(result["text"])

            markdown_content = "\n".join(content_parts)
            output_file.write_text(markdown_content, encoding="utf-8")

            result["file_path"] = str(output_file)
            logger.info(f"Saved scraped content to: {output_path}")

            return result

        except Exception as e:
            logger.error(f"Error in scrape_and_save for {url}: {e}")
            raise


# Global Jina scraper instance
def get_jina_scraper() -> JinaScraper:
    """Get Jina scraper instance."""
    return JinaScraper()
