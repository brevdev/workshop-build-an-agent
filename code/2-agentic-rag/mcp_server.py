import os
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.requests import Request
from tavily import TavilyClient
import mcp.types as types

# 1. Initialize Server Logic
mcp_server = Server("tavily-sse")

if not os.environ.get("TAVILY_API_KEY"):
    raise ValueError("TAVILY_API_KEY environment variable is required")

tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

# 2. Define Tools (Same as before)
@mcp_server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="tavily_search",
            description="Search the web for current information",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        )
    ]

@mcp_server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name != "tavily_search":
        raise ValueError(f"Unknown tool: {name}")

    try:
        query = arguments.get("query")
        # Added print for debugging so you can see it working in the server terminal
        print(f"Executing search for: {query}") 
        
        response = tavily.search(query=query, max_results=5, search_depth="advanced")
        
        formatted_results = []
        for r in response.get("results", []):
            formatted_results.append(
                f"Title: {r.get('title')}\nURL: {r.get('url')}\nContent: {r.get('content')}"
            )

        return [types.TextContent(type="text", text="\n---\n".join(formatted_results))]
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]

# 3. Set up SSE Transport with Starlette
sse = SseServerTransport("/messages/")

async def handle_sse(request: Request):
    """Handle the initial connection handshake."""
    async with sse.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await mcp_server.run(
            streams[0], streams[1], mcp_server.create_initialization_options()
        )

app = Starlette(
    routes=[
        Route("/sse", endpoint=handle_sse),
        Mount("/messages/", app=sse.handle_post_message), # Use Mount, not Route
    ]
)