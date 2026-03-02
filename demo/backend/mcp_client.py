"""
MCP (Model Context Protocol) client helpers.

Connects to remote MCP servers via SSE or Streamable HTTP transport,
discovers their tools, and converts them to LangChain-compatible tools
for injection into the deep agent.
"""

from pydantic import create_model
from langchain_mcp_adapters.client import MultiServerMCPClient

# Type mapping from JSON Schema types to Python types
_JSON_TYPE_MAP = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
    "object": dict,
    "array": list,
}


async def discover_tools(url: str) -> list[dict]:
    """
    Connect to an MCP server, list its tools, and return metadata dicts.

    Each dict has: { name, description, inputSchema }
    Raises on connection failure.
    """
    transport = _guess_transport(url)
    connection = _make_connection(url, transport)

    client = MultiServerMCPClient({"server": connection})
    tools = await client.get_tools()

    result = []
    for t in tools:
        schema = getattr(t, "args_schema", None) or {}
        # v0.2: args_schema is already a dict; older versions may have .schema()
        if not isinstance(schema, dict) and hasattr(schema, "schema"):
            schema = schema.schema()
        elif not isinstance(schema, dict) and hasattr(schema, "model_json_schema"):
            schema = schema.model_json_schema()
        result.append({
            "name": t.name,
            "description": getattr(t, "description", "") or "",
            "inputSchema": schema if isinstance(schema, dict) else {},
        })
    return result


async def get_mcp_tools(urls: list[str]) -> tuple[MultiServerMCPClient, list]:
    """
    Connect to one or more MCP servers and return (client, tools).

    The caller MUST keep the client reference alive for the duration of the
    agent session (the MCP connections are held open).

    Returns:
        (client, tools) — client is the live MultiServerMCPClient,
                          tools is a list of LangChain tool objects.
    """
    connections: dict = {}
    for i, url in enumerate(urls):
        transport = _guess_transport(url)
        connections[f"mcp_{i}"] = _make_connection(url, transport)

    client = MultiServerMCPClient(connections)
    tools = await client.get_tools()

    # Fix: deepagents' PatchToolCallsMiddleware strips args from tools
    # whose args_schema is a plain dict (not a Pydantic model).
    # Convert dict schemas → Pydantic models so deepagents handles them properly.
    for tool in tools:
        if isinstance(tool.args_schema, dict):
            tool.args_schema = _dict_schema_to_pydantic(tool.name, tool.args_schema)

    print(f"[MCP] Connected to {len(urls)} server(s), got {len(tools)} tools")
    return client, tools


def _dict_schema_to_pydantic(tool_name: str, schema: dict):
    """Convert a JSON Schema dict into a Pydantic model class."""
    properties = schema.get("properties", {})
    required = set(schema.get("required", []))

    fields = {}
    for field_name, field_info in properties.items():
        json_type = field_info.get("type", "string")
        python_type = _JSON_TYPE_MAP.get(json_type, str)
        if field_name in required:
            fields[field_name] = (python_type, ...)  # required
        else:
            fields[field_name] = (python_type, None)  # optional with default None

    model_name = f"{tool_name}Args"
    return create_model(model_name, **fields)


def _guess_transport(url: str) -> str:
    """Guess the right MCP transport from the URL."""
    if "/sse" in url.lower():
        return "sse"
    return "streamable_http"


def _make_connection(url: str, transport: str) -> dict:
    """Build a typed connection dict for MultiServerMCPClient."""
    if transport == "sse":
        return {
            "transport": "sse",
            "url": url,
        }
    return {
        "transport": "streamable_http",
        "url": url,
    }
