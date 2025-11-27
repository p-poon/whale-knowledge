import asyncio
import logging
import os
from typing import Optional, Dict, Any, List

from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession
from mcp.types import CallToolResult, TextContent

from app.core.config import settings

logger = logging.getLogger(__name__)


class ConfluenceMCPClient:
    """Client for interacting with Confluence via MCP."""

    def __init__(self):
        self.command = settings.confluence_mcp_command
        self.args = settings.confluence_mcp_args
        self.env = os.environ.copy()
        
        # Add Confluence credentials to environment variables for the subprocess
        if settings.confluence_url:
            self.env["CONFLUENCE_URL"] = settings.confluence_url
        if settings.confluence_email:
            self.env["CONFLUENCE_EMAIL"] = settings.confluence_email
        if settings.confluence_api_token:
            self.env["CONFLUENCE_API_TOKEN"] = settings.confluence_api_token

    async def create_page(
        self, 
        title: str, 
        content: str, 
        space_key: Optional[str] = None,
        tags: Optional[List[str]] = None,
        file_path: Optional[str] = None
    ) -> Optional[str]:
        """
        Create a page in Confluence.
        
        Args:
            title: Page title
            content: Page content (storage format or markdown depending on server capability)
            space_key: Confluence space key
            tags: List of labels/tags to add
            
        Returns:
            URL of the created page or None if failed
        """
        if not all([settings.confluence_url, settings.confluence_email, settings.confluence_api_token]):
            missing = []
            if not settings.confluence_url: missing.append("CONFLUENCE_URL")
            if not settings.confluence_email: missing.append("CONFLUENCE_EMAIL")
            if not settings.confluence_api_token: missing.append("CONFLUENCE_API_TOKEN")
            logger.warning(f"Confluence credentials not configured. Missing: {', '.join(missing)}")
            return None

        if space_key is None:
            space_key = settings.confluence_space_key

        logger.info(f"Attempting to create Confluence page: {title} in space {space_key}")

        try:
            server_params = StdioServerParameters(
                command=self.command,
                args=self.args,
                env=self.env
            )
            
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    # List tools to debug/verify availability
                    tools = await session.list_tools()
                    tool_names = [t.name for t in tools.tools]
                    logger.debug(f"Available Confluence tools: {tool_names}")
                    
                    # Check if setup is needed
                    if "setup_confluence" in tool_names:
                         pass

                    # Convert content to Storage Format (XML)
                    # Basic conversion: escape HTML and wrap in paragraphs
                    # Note: A proper markdown-to-storage-format converter would be better
                    safe_content = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>")
                    storage_content = f"<p>{safe_content}</p>"
                    
                    if tags:
                        tag_str = ", ".join(tags)
                        storage_content += f"<p><strong>Tags:</strong> {tag_str}</p>"

                    # Helper to call create page
                    async def _call_create_page():
                        return await session.call_tool(
                            "create_page",
                            arguments={
                                "title": title,
                                "spaceKey": space_key,
                                "content": storage_content,
                            }
                        )

                    result: CallToolResult = await _call_create_page()

                    # Check for configuration error in result content (even if isError is False)
                    config_error = False
                    result_text = ""
                    for content_block in result.content:
                        if isinstance(content_block, TextContent):
                            result_text += content_block.text
                    
                    if result.isError or "No valid configuration found" in result_text or "setup_confluence" in result_text:
                        if "No valid configuration found" in result_text or "setup_confluence" in result_text:
                            config_error = True

                    # Handle configuration error
                    if config_error:
                        logger.info("Confluence MCP server not configured. Attempting to configure...")
                        setup_result = await session.call_tool(
                            "setup_confluence",
                            arguments={
                                "action": "setup",
                                "confluenceBaseUrl": settings.confluence_url,
                                "confluenceEmail": settings.confluence_email,
                                "confluenceApiToken": settings.confluence_api_token
                            }
                        )
                        if setup_result.isError:
                            logger.error(f"Failed to configure Confluence MCP server: {setup_result.content}")
                            return None
                        
                        # Retry creation
                        logger.info("Configuration successful. Retrying page creation...")
                        result = await _call_create_page()

                    if result.isError:
                        logger.error(f"Error creating Confluence page: {result.content}")
                        return None

                    # Extract URL from result
                    page_url = None
                    for content_block in result.content:
                        if isinstance(content_block, TextContent):
                            logger.info(f"Confluence page created: {content_block.text}")
                            page_url = content_block.text
                            break
                    
                    if not page_url:
                        page_url = "Page created (URL unknown)"

                    # Upload attachment if requested
                    if file_path:
                        # We need the Page ID to upload attachments.
                        # Since create_page tool might not return ID, we try to fetch it.
                        logger.info("Retrieving Page ID for attachment upload...")
                        # Wait a bit for indexing?
                        await asyncio.sleep(3) 
                        page_id = await self.get_page_id(title, space_key)
                        
                        if page_id:
                            logger.info(f"Found Page ID: {page_id}. Uploading attachment...")
                            await self.upload_attachment(page_id, file_path)
                        else:
                            logger.warning("Could not retrieve Page ID. Attachment upload skipped.")

                    return page_url

                    return "Page created (URL unknown)"

        except Exception as e:
            logger.error(f"Failed to create Confluence page: {e}")
            return None

    async def get_page_id(self, title: str, space_key: Optional[str] = None) -> Optional[str]:
        """
        Retrieve the Page ID for a given title using Confluence REST API.
        """
        import httpx
        import urllib.parse
        
        if space_key is None:
            space_key = settings.confluence_space_key
            
        # Escape double quotes in title for CQL
        safe_title = title.replace('"', '\\"')
        
        cql = f'title = "{safe_title}" AND space = "{space_key}"'
        encoded_cql = urllib.parse.quote(cql)
        
        url = f"{settings.confluence_url}/wiki/rest/api/content/search?cql={encoded_cql}&limit=1"
        
        # Remove /wiki if it's already in the base URL to avoid duplication
        if "/wiki/wiki" in url:
             url = url.replace("/wiki/wiki", "/wiki")
             
        auth = (settings.confluence_email, settings.confluence_api_token)
        
        for attempt in range(5):
            try:
                if attempt > 0:
                    await asyncio.sleep(2 * attempt)
                    
                logger.debug(f"Searching for page ID via REST API: {url} (Attempt {attempt+1})")
                
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        url,
                        auth=auth,
                        timeout=30.0
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if "results" in data and len(data["results"]) > 0:
                            page_id = data["results"][0]["id"]
                            logger.info(f"Found Page ID: {page_id} for title '{title}'")
                            return page_id
                        else:
                            logger.debug(f"No results found for title '{title}'")
                    else:
                        logger.error(f"Search failed. Status: {response.status_code}, Body: {response.text}")
                        
            except Exception as e:
                logger.error(f"Exception retrieving page ID (attempt {attempt+1}): {e}")
                
        return None

    async def upload_attachment(self, page_id: str, file_path: str) -> bool:
        """
        Upload an attachment to a Confluence page using the REST API.
        """
        import httpx
        
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return False
            
        url = f"{settings.confluence_url}/wiki/rest/api/content/{page_id}/child/attachment"
        
        # Remove /wiki if it's already in the base URL (handling user config variations)
        if "/wiki/wiki" in url:
             url = url.replace("/wiki/wiki", "/wiki")
        
        auth = (settings.confluence_email, settings.confluence_api_token)
        headers = {"X-Atlassian-Token": "nocheck"}
        
        filename = os.path.basename(file_path)
        
        try:
            async with httpx.AsyncClient() as client:
                with open(file_path, "rb") as f:
                    files = {"file": (filename, f)}
                    response = await client.post(
                        url, 
                        auth=auth, 
                        headers=headers, 
                        files=files,
                        timeout=30.0
                    )
                    
                if response.status_code == 200:
                    logger.info(f"Successfully uploaded attachment: {filename}")
                    return True
                else:
                    logger.error(f"Failed to upload attachment. Status: {response.status_code}, Body: {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Exception uploading attachment: {e}")
            return False

    async def delete_page(self, title: str, space_key: Optional[str] = None) -> bool:
        """
        Delete a Confluence page by title.
        """
        import httpx
        
        if space_key is None:
            space_key = settings.confluence_space_key

        logger.info(f"Attempting to delete Confluence page: {title} in space {space_key}")
        
        # Get Page ID
        page_id = await self.get_page_id(title, space_key)
        if not page_id:
            logger.warning(f"Page not found for deletion: {title}")
            return False
            
        url = f"{settings.confluence_url}/wiki/rest/api/content/{page_id}"
        
        # Remove /wiki if it's already in the base URL
        if "/wiki/wiki" in url:
             url = url.replace("/wiki/wiki", "/wiki")
        
        auth = (settings.confluence_email, settings.confluence_api_token)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    url, 
                    auth=auth, 
                    timeout=30.0
                )
                
                if response.status_code == 204:
                    logger.info(f"Successfully deleted page: {title} (ID: {page_id})")
                    return True
                elif response.status_code == 404:
                    logger.warning(f"Page already deleted or not found: {title}")
                    return True
                else:
                    logger.error(f"Failed to delete page. Status: {response.status_code}, Body: {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Exception deleting page: {e}")
            return False

# Global instance
_confluence_client = None

def get_confluence_client() -> ConfluenceMCPClient:
    global _confluence_client
    if _confluence_client is None:
        _confluence_client = ConfluenceMCPClient()
    return _confluence_client
