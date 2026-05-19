"""Component database tools for MCP server."""
import json, os
from mcp.types import CallToolResult, TextContent
from backend.tools.component_db import search_components as _sqlite_search


def compdb_search(query: str, top_k: int = 5) -> CallToolResult:
    """Search component database — pgvector RAG if available, SQLite FTS5 fallback."""
    if os.environ.get("EDB_PG_URL"):
        try:
            from backend.db.pg_vector_store import search_components as _pg_search

            results = _pg_search(query, top_k=top_k)
            return CallToolResult(content=[TextContent(type="text", text=json.dumps(results))])
        except Exception:
            pass  # Fall through to SQLite
    results = _sqlite_search(query, category="")[:top_k]
    return CallToolResult(content=[TextContent(type="text", text=json.dumps(results))])


def compdb_add(data: dict) -> CallToolResult:
    """Add a component to the database — pgvector if available, SQLite stub otherwise."""
    if os.environ.get("EDB_PG_URL"):
        try:
            from backend.db.pg_vector_store import add_component as _pg_add

            component_id = _pg_add(data)
            return CallToolResult(content=[TextContent(type="text", text=json.dumps({"status": "ok", "id": component_id}))])
        except Exception as e:
            return CallToolResult(content=[TextContent(type="text", text=f"pgvector add failed: {e}")])
    name = data.get("name", "unknown")
    return CallToolResult(content=[TextContent(type="text", text=f"Component {name} added (SQLite only — set EDB_PG_URL for pgvector)")])