import asyncio
import os
import logging
import httpx
import urllib.parse
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

async def cleanup_page(title_part: str):
    # Configuration
    confluence_url = os.environ.get("CONFLUENCE_URL")
    email = os.environ.get("CONFLUENCE_EMAIL")
    api_token = os.environ.get("CONFLUENCE_API_TOKEN")
    space_key = os.environ.get("CONFLUENCE_SPACE_KEY", "DS")

    if not all([confluence_url, email, api_token]):
        logger.error("Missing Confluence credentials.")
        return

    auth = (email, api_token)
    
    auth = (email, api_token)
    
    # Construct CQL
    if title_part:
        cql = f'title ~ "{title_part}" AND space = "{space_key}"'
        logger.info(f"Searching for pages matching '{title_part}' in space '{space_key}'...")
    else:
        cql = f'space = "{space_key}" order by created desc'
        logger.info(f"Listing recent pages in space '{space_key}'...")
        
    encoded_cql = urllib.parse.quote(cql)
    
    search_url = f"{confluence_url}/wiki/rest/api/content/search?cql={encoded_cql}&limit=20"
    if "/wiki/wiki" in search_url:
        search_url = search_url.replace("/wiki/wiki", "/wiki")

    async with httpx.AsyncClient() as client:
        response = await client.get(search_url, auth=auth)
        
        if response.status_code != 200:
            logger.error(f"Search failed: {response.status_code} {response.text}")
            return

        data = response.json()
        results = data.get("results", [])
        
        if not results:
            logger.info("No pages found.")
            return

        logger.info(f"Found {len(results)} pages:")
        for page in results:
            logger.info(f" - ID: {page['id']}, Title: {page['title']}")

        # Delete pages
        for page in results:
            page_id = page['id']
            page_title = page['title']
            
            delete_url = f"{confluence_url}/wiki/rest/api/content/{page_id}"
            if "/wiki/wiki" in delete_url:
                delete_url = delete_url.replace("/wiki/wiki", "/wiki")
                
            logger.info(f"Deleting page: {page_title} (ID: {page_id})...")
            del_response = await client.delete(delete_url, auth=auth)
            
            if del_response.status_code == 204:
                logger.info("Successfully deleted.")
            else:
                logger.error(f"Failed to delete: {del_response.status_code}")

if __name__ == "__main__":
    import sys
    title_part = ""
    if len(sys.argv) > 1:
        title_part = sys.argv[1]
        
    asyncio.run(cleanup_page(title_part))
