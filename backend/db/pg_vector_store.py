"""RAG search using PostgreSQL + pgvector."""
from __future__ import annotations
import os, json, openai
from backend.db.connection import get_cursor

DB_URL = os.environ.get("EDB_PG_URL", "postgresql://postgres:password@localhost:5432/eda_agent")

def search_components(query: str, top_k: int = 5) -> list[dict]:
    """RAG search: embed query → pgvector cosine similarity → top-k components."""
    response = openai.embeddings.create(model="text-embedding-3-small", input=query)
    query_vector = response.data[0].embedding

    with get_cursor() as cur:
        cur.execute("""
            SELECT c.id, c.lib_id, c.name, c.mpn, c.category, c.package,
                   c.jlc_part, c.price, c.stock,
                   1 - (e.embedding <=> %s::vector) as similarity
            FROM component_embeddings e
            JOIN components c ON e.component_id = c.id
            ORDER BY e.embedding <=> %s::vector
            LIMIT %s
        """, (str(query_vector), str(query_vector), top_k))
        columns = [desc[0] for desc in cur.description]
        results = [dict(zip(columns, row)) for row in cur.fetchall()]
    return results

def add_component(data: dict) -> int:
    """Add component with embedding generation."""
    with get_cursor() as cur:
        cur.execute("""
            INSERT INTO components (lib_id, name, mpn, category, package, jlc_part, price, description)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
        """, (data["lib_id"], data["name"], data.get("mpn"), data.get("category"),
              data.get("package"), data.get("jlc_part"), data.get("price"), data.get("description")))
        component_id = cur.fetchone()[0]

        response = openai.embeddings.create(
            model="text-embedding-3-small",
            input=data.get("description", data["name"]))
        embedding = response.data[0].embedding

        cur.execute("""
            INSERT INTO component_embeddings (component_id, description_text, embedding)
            VALUES (%s, %s, %s::vector)
        """, (component_id, data.get("description", ""), str(embedding)))
    return component_id