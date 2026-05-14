from __future__ import annotations
import json, sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "db" / "components.db"


def _connect() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def search_components(query: str, category: str = "") -> list[dict]:
    """FTS5 search. Returns top 8 matches with lib_id, name, description, pin_count."""
    con = _connect()
    try:
        fts_query = " OR ".join(f'"{t}"' for t in query.split() if t)
        if category:
            rows = con.execute(
                "SELECT c.lib_id, c.name, c.description, c.pin_count FROM components_fts f "
                "JOIN components c ON c.rowid = f.rowid "
                "WHERE components_fts MATCH ? AND c.category = ? LIMIT 8",
                (fts_query, category),
            ).fetchall()
        else:
            rows = con.execute(
                "SELECT c.lib_id, c.name, c.description, c.pin_count FROM components_fts f "
                "JOIN components c ON c.rowid = f.rowid "
                "WHERE components_fts MATCH ? LIMIT 8",
                (fts_query,),
            ).fetchall()
        return [dict(r) for r in rows]
    except sqlite3.OperationalError:
        return []
    finally:
        con.close()


def get_component_details(lib_id: str) -> dict | None:
    con = _connect()
    try:
        row = con.execute(
            "SELECT lib_id, name, description, keywords, category, pin_count, datasheet_url FROM components WHERE lib_id = ?",
            (lib_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        con.close()


def get_component_pins(lib_id: str) -> list[dict]:
    con = _connect()
    try:
        row = con.execute("SELECT pins_json FROM components WHERE lib_id = ?", (lib_id,)).fetchone()
        return json.loads(row["pins_json"]) if row else []
    finally:
        con.close()


def lib_id_exists(lib_id: str) -> bool:
    con = _connect()
    try:
        return con.execute("SELECT 1 FROM components WHERE lib_id = ?", (lib_id,)).fetchone() is not None
    finally:
        con.close()
