import asyncio
import os
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession

async def main():
    command = "npx"
    args = ["-y", "@aiondadotcom/mcp-confluence-server"]
    env = os.environ.copy()
    
    print(f"Connecting to MCP server: {command} {' '.join(args)}")
    
    server_params = StdioServerParameters(
        command=command,
        args=args,
        env=env
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                tools = await session.list_tools()
                print("\nAvailable Tools:")
                for tool in tools.tools:
                    print(f"- {tool.name}: {tool.description}")
                    print(f"  Schema: {tool.inputSchema}")
                    print("-" * 40)
                    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
