import asyncio
import os
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession
from app.core.config import settings

# Mock settings if needed, or rely on env vars if config.py loads them
# We will manually set them from env vars for this script to be sure
CONFLUENCE_URL = os.environ.get("CONFLUENCE_URL")
CONFLUENCE_EMAIL = os.environ.get("CONFLUENCE_EMAIL")
CONFLUENCE_API_TOKEN = os.environ.get("CONFLUENCE_API_TOKEN")

async def main():
    if not all([CONFLUENCE_URL, CONFLUENCE_EMAIL, CONFLUENCE_API_TOKEN]):
        print("Error: Missing Confluence credentials in environment.")
        return

    command = "npx"
    args = ["-y", "@aiondadotcom/mcp-confluence-server"]
    env = os.environ.copy()
    
    print(f"Connecting to MCP server...")
    
    server_params = StdioServerParameters(
        command=command,
        args=args,
        env=env
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # 1. Setup
                print("Setting up connection...")
                setup_result = await session.call_tool(
                    "setup_confluence",
                    arguments={
                        "action": "setup",
                        "confluenceBaseUrl": CONFLUENCE_URL,
                        "confluenceEmail": CONFLUENCE_EMAIL,
                        "confluenceApiToken": CONFLUENCE_API_TOKEN
                    }
                )
                if setup_result.isError:
                    print(f"Setup failed: {setup_result.content}")
                    return
                print("Setup successful.")

                # 2. Create Page
                print("Creating test page...")
                result = await session.call_tool(
                    "create_page",
                    arguments={
                        "title": "MCP Test Page " + os.urandom(4).hex(),
                        "spaceKey": "DS", # Use the same space key as in the app
                        "content": "<p>This is a test page created via MCP script.</p>"
                    }
                )
                
                print(f"Is Error: {result.isError}")
                print("Content:")
                for block in result.content:
                    print(block.text[:500] + "..." if len(block.text) > 500 else block.text)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
