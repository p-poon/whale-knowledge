import asyncio
import os
import logging
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

async def debug_search():
    # Configuration
    command = "npx"
    args = ["-y", "@aiondadotcom/mcp-confluence-server"]
    
    env = os.environ.copy()
    
    # Check credentials
    if not all([env.get("CONFLUENCE_URL"), env.get("CONFLUENCE_EMAIL"), env.get("CONFLUENCE_API_TOKEN")]):
        logger.error("Missing Confluence credentials in environment variables.")
        return

    title = "Doc: WEF_Artificial_Intelligences_Energy_Paradox_2025.pdf"
    space_key = env.get("CONFLUENCE_SPACE_KEY", "DS")
    
    logger.info(f"Searching for page: '{title}' in space '{space_key}'")

    server_params = StdioServerParameters(
        command=command,
        args=args,
        env=env
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # List tools to confirm connection
            tools = await session.list_tools()
            logger.info(f"Connected to MCP server. Available tools: {[t.name for t in tools.tools]}")

            # Escape title
            safe_title = title.replace('"', '\\"')
            query = f'title = "{safe_title}" AND space = "{space_key}"'
            
            logger.info(f"Executing CQL query: {query}")
            
            try:
                result = await session.call_tool(
                    "search_pages",
                    arguments={
                        "query": query,
                        "limit": 5
                    }
                )
                
                if result.isError:
                    logger.error(f"Tool execution failed: {result.content}")
                else:
                    logger.info("Tool execution successful.")
                    for content in result.content:
                        logger.info(f"Content Type: {content.type}")
                        if hasattr(content, "text"):
                            logger.info(f"Raw Content: {content.text}")
                            
            except Exception as e:
                logger.error(f"Error calling tool: {e}")

if __name__ == "__main__":
    asyncio.run(debug_search())
