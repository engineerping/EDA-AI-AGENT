"""File operations for MCP server."""
from mcp.types import CallToolResult, TextContent

def file_write(path: str, content: str) -> CallToolResult:
    with open(path, "w") as f:
        f.write(content)
    return CallToolResult(content=[TextContent(type="text", text=f"Written {len(content)} bytes to {path}")])

def file_read(path: str) -> CallToolResult:
    with open(path, "r") as f:
        content = f.read()
    return CallToolResult(content=[TextContent(type="text", text=content)])