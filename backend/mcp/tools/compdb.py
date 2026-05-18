"""Component database tools for MCP server."""
from backend.tools.component_db import search_components as _search_components

def compdb_search(query: str, top_k: int = 5) -> list:
    """Search component database with FTS5."""
    return _search_components(query, category="")[:top_k]

def compdb_add(data: dict) -> str:
    """Add a component to the database (stub — full RAG version in Phase 4)."""
    return f"Component {data.get('name', 'unknown')} added (SQLite mode — pgvector in Phase 4)"