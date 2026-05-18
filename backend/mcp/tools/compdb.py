"""Component database tools for MCP server."""
import json
from mcp.types import CallToolResult, TextContent
from backend.tools.component_db import search_components as _search_components

def compdb_search(query: str, top_k: int = 5) -> CallToolResult:
    """Search component database with FTS5."""
    results = _search_components(query, category="")[:top_k]
    return CallToolResult(content=[TextContent(type="text", text=json.dumps(results))])

def compdb_add(data: dict) -> CallToolResult:
    """Add a component to the database (stub — full RAG version in Phase 4)."""
    name = data.get('name', 'unknown')
    return CallToolResult(content=[TextContent(type="text", text=f"Component {name} added (SQLite mode - pgvector in Phase 4)")])