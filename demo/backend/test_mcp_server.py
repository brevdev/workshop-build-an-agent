"""
Tiny MCP server for testing.

Run with:
    python test_mcp_server.py

Then paste this URL in the Settings panel:
    http://localhost:8100/sse
"""

import uvicorn
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("test-tools")


@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b


@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers together."""
    return a * b


@mcp.tool()
def reverse_string(text: str) -> str:
    """Reverse a string."""
    return text[::-1]


@mcp.tool()
def word_count(text: str) -> dict:
    """Count words in a text and return statistics."""
    words = text.split()
    return {
        "word_count": len(words),
        "char_count": len(text),
        "unique_words": len(set(w.lower() for w in words)),
    }


# Get the ASGI/SSE app from FastMCP
app = mcp.sse_app()

if __name__ == "__main__":
    print("Starting test MCP server on http://localhost:8100/sse")
    uvicorn.run(app, host="127.0.0.1", port=8100)
