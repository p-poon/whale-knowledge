import asyncio
import os
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession

# Read from env vars directly
CONFLUENCE_URL = os.environ.get("CONFLUENCE_URL")
CONFLUENCE_EMAIL = os.environ.get("CONFLUENCE_EMAIL")
CONFLUENCE_API_TOKEN = os.environ.get("CONFLUENCE_API_TOKEN")

async def main():
    print(f"Checking configuration...")
    print(f"URL: {CONFLUENCE_URL}")
    print(f"Email: {CONFLUENCE_EMAIL}")
    print(f"Token: {'*' * 5 if CONFLUENCE_API_TOKEN else 'None'}")

    if not all([CONFLUENCE_URL, CONFLUENCE_EMAIL, CONFLUENCE_API_TOKEN]):
        print("Error: Missing environment variables.")
        return

    command = "npx"
    args = ["-y", "@aiondadotcom/mcp-confluence-server"]
    env = os.environ.copy()
    
    server_params = StdioServerParameters(
        command=command,
        args=args,
        env=env
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # 1. Try to setup (force update)
                print("\nAttempting setup...")
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
                    print(f"Setup Error: {setup_result.content}")
                else:
                    print(f"Setup Result: {setup_result.content}")

                # 2. List Spaces
                print("\nListing Spaces...")
                spaces_result = await session.call_tool("list_spaces", arguments={"limit": 5})
                
                if spaces_result.isError:
                    print(f"List Spaces Error: {spaces_result.content}")
                else:
                    print("Spaces found:")
                    for block in spaces_result.content:
                        print(block.text)

    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(main())
