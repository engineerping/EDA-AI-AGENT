"""File operations for MCP server."""
from mcp.types import CallToolResult

def file_write(path: str, content: str) -> str:
    with open(path, "w") as f:
        f.write(content)
    return f"Written {len(content)} bytes to {path}"

def file_read(path: str) -> str:
    with open(path, "r") as f:
        return f.read()