import httpx
from typing import Dict, Any, Optional
import logging
import hashlib
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)


class JinaScraper:
    """Scrape web content using Jina Reader API."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.jina_api_key
        self.base_url = "https://r.jina.ai"

    async def scrape_url(self, url: str) -> Dict[str, Any]:
        """
        Scrape content from a URL using Jina Reader.

        Args:
            url: URL to scrape

        Returns:
            Dictionary with scraped content and metadata
        """
        try:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            # Jina Reader API endpoint
            jina_url = f"{self.base_url}/{url}"

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

                logger.info(f"Successfully scraped URL: {url}")
                return result

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error scraping {url}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            raise

    async def scrape_and_save(
        self,
        url: str,
        output_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Scrape URL and save as markdown file.

        Args:
            url: URL to scrape
            output_path: Path to save markdown file
            metadata: Optional additional metadata

        Returns:
            Dictionary with scrape results and file path
        """
        try:
            # Scrape content
            result = await self.scrape_url(url)

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
