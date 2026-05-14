# EDA-AI-Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local web app where users describe a circuit, an AI agent pipeline (Req→Design→KiCadGen→Validation) produces a `.kicad_sch` file, and the browser renders a live schematic preview via KiCanvas.

**Architecture:** FastAPI backend runs a 4-sub-agent pipeline orchestrated via a ReAct loop; agents communicate through a `SessionState` dataclass; the Orchestrator streams every LLM token to the React frontend over a single WebSocket connection. The `ask_user` tool in the Req Agent suspends execution via an `asyncio.Queue`, resuming only when the next user WebSocket message arrives.

**Tech Stack:** Python 3.11+, FastAPI, LiteLLM, SQLite FTS5, React 18, TypeScript, Vite, KiCanvas (CDN)

---

## File Map

```
EDA-AI-AGENT/
├── backend/
│   ├── main.py                    # FastAPI app + /ws WebSocket + /api routes
│   ├── orchestrator.py            # Session, SessionState, Orchestrator (ReAct loop)
│   ├── agents/
│   │   ├── base.py                # BaseAgent — LiteLLM tool-call loop + streaming
│   │   ├── req_agent.py           # ReqAgent — ask_user / finalize_requirements
│   │   ├── design_agent.py        # DesignAgent — search_components / finalize_bom
│   │   ├── kicad_gen_agent.py     # KiCadGenAgent — get_component_pins / write_schematic
│   │   └── validation_agent.py    # ValidationAgent — run_erc / translate_erc_error
│   ├── tools/
│   │   ├── component_db.py        # SQLite FTS5 lookup (search + details + pins)
│   │   ├── kicad_cli.py           # Subprocess wrapper: kicad-cli sch erc
│   │   └── schematic_writer.py    # Builds + validates .kicad_sch S-expression
│   ├── db/
│   │   ├── build_index.py         # Dev script: parse kicad_symbols/ → components.db
│   │   ├── scanner.py             # First-run: scan user KiCad install, merge into DB
│   │   └── components.db          # Bundled SQLite index (built by build_index.py)
│   └── config.py                  # ~/.eda-agent/config.json read/write
├── frontend/
│   ├── index.html
│   ├── vite.config.ts             # Proxy /api + /ws → localhost:8000
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx                # Two-panel layout, settings gate
│   │   ├── components/
│   │   │   ├── ChatPanel.tsx      # Message list + stage bar + input
│   │   │   ├── SchematicViewer.tsx # KiCanvas WebGL embed
│   │   │   └── SettingsModal.tsx  # Model / API key / KiCad path / re-scan
│   │   ├── hooks/
│   │   │   └── useAgentSocket.ts  # WebSocket connection + message stream
│   │   └── api/
│   │       └── client.ts          # REST: GET/POST /api/config, GET /api/download
├── tests/
│   ├── test_config.py
│   ├── test_component_db.py
│   ├── test_schematic_writer.py
│   ├── test_kicad_cli.py
│   └── test_orchestrator.py
├── kicad_symbols/                 # git submodule: kicad/kicad-symbols
├── pyproject.toml
└── .gitignore
```

---

## Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `backend/__init__.py`, `backend/agents/__init__.py`, `backend/tools/__init__.py`, `backend/db/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[project]
name = "eda-ai-agent"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.111.0",
    "uvicorn[standard]>=0.29.0",
    "websockets>=12.0",
    "litellm>=1.40.0",
    "aiosqlite>=0.20.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "httpx>=0.27.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
```

- [ ] **Step 2: Create `.gitignore`**

```gitignore
__pycache__/
*.pyc
.venv/
node_modules/
frontend/dist/
.env
~/.eda-agent/
*.db-journal
.superpowers/
```

- [ ] **Step 3: Create all `__init__.py` files**

```bash
touch backend/__init__.py backend/agents/__init__.py backend/tools/__init__.py backend/db/__init__.py tests/__init__.py
```

- [ ] **Step 4: Add kicad_symbols as git submodule**

```bash
git submodule add https://gitlab.com/kicad/libraries/kicad-symbols.git kicad_symbols
```

Expected: `kicad_symbols/` directory created with `.kicad_sym` files (Device.kicad_sym, Power.kicad_sym, etc.)

- [ ] **Step 5: Install Python deps**

```bash
python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"
```

Expected: `Successfully installed fastapi litellm uvicorn ...`

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml .gitignore backend/ tests/ .gitmodules kicad_symbols/
git commit -m "feat: project scaffolding — pyproject, package structure, kicad_symbols submodule"
```

---

## Task 2: Config Module

**Files:**
- Create: `backend/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_config.py
import json, os, pytest
from pathlib import Path
from unittest.mock import patch

def test_load_config_defaults(tmp_path):
    cfg_file = tmp_path / "config.json"
    with patch("backend.config.CONFIG_PATH", cfg_file):
        from backend.config import load_config
        cfg = load_config()
    assert cfg.model == "anthropic/claude-opus-4-7"
    assert cfg.api_key is None
    assert cfg.kicad_cli_path is None

def test_save_and_load_config(tmp_path):
    cfg_file = tmp_path / "config.json"
    with patch("backend.config.CONFIG_PATH", cfg_file):
        from backend.config import load_config, save_config, AgentConfig
        original = load_config()
        original.model = "openai/gpt-4o"
        original.api_key = "sk-test-key"
        save_config(original)
        reloaded = load_config()
    assert reloaded.model == "openai/gpt-4o"
    assert reloaded.api_key == "sk-test-key"

def test_sanitized_config_masks_api_key(tmp_path):
    cfg_file = tmp_path / "config.json"
    with patch("backend.config.CONFIG_PATH", cfg_file):
        from backend.config import load_config, save_config, sanitized_config
        cfg = load_config()
        cfg.api_key = "sk-real-secret"
        save_config(cfg)
        safe = sanitized_config()
    assert safe["api_key"] == "***"
    assert safe["model"] == "anthropic/claude-opus-4-7"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_config.py -v
```

Expected: `ModuleNotFoundError: No module named 'backend.config'`

- [ ] **Step 3: Implement `backend/config.py`**

```python
from __future__ import annotations
import json
from pathlib import Path
from pydantic import BaseModel

CONFIG_PATH = Path.home() / ".eda-agent" / "config.json"


class AgentConfig(BaseModel):
    model: str = "anthropic/claude-opus-4-7"
    api_key: str | None = None
    base_url: str | None = None
    kicad_cli_path: str | None = None
    db_last_scanned: str | None = None


def load_config() -> AgentConfig:
    if CONFIG_PATH.exists():
        return AgentConfig.model_validate(json.loads(CONFIG_PATH.read_text()))
    return AgentConfig()


def save_config(cfg: AgentConfig) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(cfg.model_dump_json(indent=2))


def sanitized_config() -> dict:
    cfg = load_config().model_dump()
    if cfg.get("api_key"):
        cfg["api_key"] = "***"
    return cfg
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_config.py -v
```

Expected: `3 passed`

- [ ] **Step 5: Commit**

```bash
git add backend/config.py tests/test_config.py
git commit -m "feat: config module — AgentConfig pydantic model, load/save/sanitize"
```

---

## Task 3: Component DB Schema + Build Script

**Files:**
- Create: `backend/db/build_index.py`
- Create: `backend/db/schema.sql`

- [ ] **Step 1: Create `backend/db/schema.sql`**

```sql
CREATE TABLE IF NOT EXISTS components (
    lib_id       TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    description  TEXT NOT NULL DEFAULT '',
    keywords     TEXT NOT NULL DEFAULT '',
    category     TEXT NOT NULL DEFAULT '',
    pin_count    INTEGER NOT NULL DEFAULT 0,
    datasheet_url TEXT NOT NULL DEFAULT '',
    pins_json    TEXT NOT NULL DEFAULT '[]'
);

CREATE VIRTUAL TABLE IF NOT EXISTS components_fts
    USING fts5(lib_id, name, description, keywords, content='components', content_rowid='rowid');

CREATE TRIGGER IF NOT EXISTS components_ai AFTER INSERT ON components BEGIN
    INSERT INTO components_fts(rowid, lib_id, name, description, keywords)
    VALUES (new.rowid, new.lib_id, new.name, new.description, new.keywords);
END;
```

- [ ] **Step 2: Create `backend/db/build_index.py`**

```python
"""
Dev script: parse kicad_symbols/*.kicad_sym → backend/db/components.db
Run once from project root: python -m backend.db.build_index
"""
from __future__ import annotations
import json, re, sqlite3
from pathlib import Path

SYMBOLS_DIR = Path("kicad_symbols")
DB_PATH = Path("backend/db/components.db")
SCHEMA_PATH = Path("backend/db/schema.sql")


def parse_sym_file(path: Path) -> list[dict]:
    """Extract symbol metadata from a .kicad_sym file using regex."""
    text = path.read_text(encoding="utf-8", errors="ignore")
    category = path.stem  # e.g. "Device", "Power"
    results = []

    for block in re.finditer(
        r'\(symbol\s+"([^"]+)"(?!\s*\(symbol)', text, re.DOTALL
    ):
        name = block.group(1)
        if "~" in name:
            continue  # skip sub-unit symbols like R~0
        lib_id = f"{category}:{name}"
        start = block.start()

        # find closing paren by scanning forward (depth counting)
        depth, end = 0, start
        for i, ch in enumerate(text[start:], start):
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        symbol_text = text[start:end]

        description = _extract_property(symbol_text, "ki_description") or ""
        keywords = _extract_property(symbol_text, "ki_keywords") or ""
        datasheet = _extract_property(symbol_text, "Datasheet") or ""

        pins = re.findall(r'\(pin\s+\S+\s+\S+\s+\(at[^)]+\)[^(]*\(name\s+"([^"]*)"', symbol_text)
        numbers = re.findall(r'\(pin\s+\S+\s+\S+\s+\(at[^)]+\)[^(]*\(name[^)]+\)\s*\(number\s+"([^"]*)"', symbol_text)

        pin_data = [{"name": p, "number": n} for p, n in zip(pins, numbers)]

        results.append({
            "lib_id": lib_id,
            "name": name,
            "description": description,
            "keywords": keywords,
            "category": category,
            "pin_count": len(pin_data),
            "datasheet_url": datasheet if datasheet != "~" else "",
            "pins_json": json.dumps(pin_data),
        })
    return results


def _extract_property(text: str, key: str) -> str | None:
    m = re.search(rf'\(property\s+"{re.escape(key)}"\s+"([^"]*)"', text)
    return m.group(1) if m else None


def build(symbols_dir: Path = SYMBOLS_DIR, db_path: Path = DB_PATH) -> int:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    con = sqlite3.connect(db_path)
    con.executescript(SCHEMA_PATH.read_text())

    total = 0
    for sym_file in sorted(symbols_dir.glob("*.kicad_sym")):
        rows = parse_sym_file(sym_file)
        con.executemany(
            "INSERT OR IGNORE INTO components VALUES (:lib_id,:name,:description,:keywords,:category,:pin_count,:datasheet_url,:pins_json)",
            rows,
        )
        total += len(rows)
        print(f"  {sym_file.stem}: {len(rows)} symbols")

    con.commit()
    con.close()
    print(f"\nTotal: {total} symbols → {db_path}")
    return total


if __name__ == "__main__":
    build()
```

- [ ] **Step 3: Run the build script**

```bash
python -m backend.db.build_index
```

Expected output (approximate):
```
  Amplifier_Audio: 12 symbols
  Amplifier_Instrumentation: 8 symbols
  ...
  Device: 183 symbols
  ...
Total: ~17000 symbols → backend/db/components.db
```

- [ ] **Step 4: Verify DB contents**

```bash
sqlite3 backend/db/components.db "SELECT COUNT(*) FROM components; SELECT lib_id, description FROM components WHERE lib_id LIKE 'Device:%' LIMIT 5;"
```

Expected: row count > 1000, Device:R, Device:C, Device:LED visible.

- [ ] **Step 5: Commit**

```bash
git add backend/db/build_index.py backend/db/schema.sql
echo "backend/db/components.db" >> .gitignore
git add .gitignore
git commit -m "feat: component DB schema + build script — parses kicad_symbols/ into SQLite FTS5 index"
```

---

## Task 4: Component DB Lookup Tool

**Files:**
- Create: `backend/tools/component_db.py`
- Create: `tests/test_component_db.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_component_db.py
import json, pytest, sqlite3
from pathlib import Path
import backend.tools.component_db as db_module

@pytest.fixture
def test_db(tmp_path):
    db_path = tmp_path / "test.db"
    schema = Path("backend/db/schema.sql").read_text()
    con = sqlite3.connect(db_path)
    con.executescript(schema)
    rows = [
        ("Device:R", "R", "Resistor", "resistor res", "Device", 2, "", '[{"name":"~","number":"1"},{"name":"~","number":"2"}]'),
        ("Device:C", "C", "Unpolarized capacitor", "capacitor cap", "Device", 2, "", '[{"name":"~","number":"1"},{"name":"~","number":"2"}]'),
        ("Device:LED", "LED", "Light emitting diode", "LED diode", "Device", 2, "", '[{"name":"K","number":"1"},{"name":"A","number":"2"}]'),
    ]
    con.executemany("INSERT INTO components VALUES (?,?,?,?,?,?,?,?)", rows)
    con.commit()
    con.close()
    return db_path

def test_search_components(test_db, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", test_db)
    results = db_module.search_components("resistor")
    assert any(r["lib_id"] == "Device:R" for r in results)

def test_get_component_details(test_db, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", test_db)
    detail = db_module.get_component_details("Device:LED")
    assert detail["name"] == "LED"
    assert detail["pin_count"] == 2

def test_get_component_pins(test_db, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", test_db)
    pins = db_module.get_component_pins("Device:R")
    assert len(pins) == 2
    assert pins[0]["number"] == "1"

def test_search_returns_empty_for_unknown(test_db, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", test_db)
    results = db_module.search_components("xyznonexistent123")
    assert results == []
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_component_db.py -v
```

Expected: `ModuleNotFoundError: No module named 'backend.tools.component_db'`

- [ ] **Step 3: Implement `backend/tools/component_db.py`**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_component_db.py -v
```

Expected: `4 passed`

- [ ] **Step 5: Commit**

```bash
git add backend/tools/component_db.py tests/test_component_db.py
git commit -m "feat: component DB lookup tool — FTS5 search, details, pins, existence check"
```

---

## Task 5: KiCad Lib Scanner

**Files:**
- Create: `backend/db/scanner.py`

- [ ] **Step 1: Implement `backend/db/scanner.py`**

```python
"""
First-run scanner: find user's KiCad symbol libraries and merge into components.db.
Called once from main.py on startup if config.db_last_scanned is None.
"""
from __future__ import annotations
import json, platform, sqlite3
from datetime import datetime, timezone
from pathlib import Path

from backend.config import load_config, save_config
from backend.db.build_index import build, parse_sym_file
from backend.tools.component_db import DB_PATH


def _default_kicad_sym_dirs() -> list[Path]:
    system = platform.system()
    candidates = []
    if system == "Darwin":
        candidates = [
            Path("/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols"),
            Path.home() / "Documents/KiCad/8.0/symbols",
        ]
    elif system == "Windows":
        candidates = [
            Path("C:/Program Files/KiCad/8.0/share/kicad/symbols"),
            Path.home() / "Documents/KiCad/8.0/symbols",
        ]
    else:  # Linux
        candidates = [
            Path("/usr/share/kicad/symbols"),
            Path.home() / ".local/share/kicad/8.0/symbols",
        ]
    return [p for p in candidates if p.exists()]


def scan_and_merge() -> int:
    """Scan user's KiCad libraries and upsert into components.db. Returns count of new rows."""
    dirs = _default_kicad_sym_dirs()
    if not dirs:
        print("No KiCad symbol directories found — skipping scan.")
        return 0

    con = sqlite3.connect(DB_PATH)
    added = 0
    for sym_dir in dirs:
        for sym_file in sorted(sym_dir.glob("*.kicad_sym")):
            rows = parse_sym_file(sym_file)
            for row in rows:
                cur = con.execute(
                    "INSERT OR IGNORE INTO components VALUES (:lib_id,:name,:description,:keywords,:category,:pin_count,:datasheet_url,:pins_json)",
                    row,
                )
                added += cur.rowcount
    con.commit()
    con.close()

    cfg = load_config()
    cfg.db_last_scanned = datetime.now(timezone.utc).isoformat()
    save_config(cfg)
    print(f"Scanner: added {added} symbols from user KiCad libraries.")
    return added
```

- [ ] **Step 2: Verify scanner runs without error (even if no KiCad installed)**

```bash
python -c "from backend.db.scanner import scan_and_merge; print(scan_and_merge())"
```

Expected: Either prints `Scanner: added N symbols` or `No KiCad symbol directories found — skipping scan.` and returns 0. No crash.

- [ ] **Step 3: Commit**

```bash
git add backend/db/scanner.py
git commit -m "feat: KiCad lib scanner — auto-detects user install, merges custom symbols into DB"
```

---

## Task 6: Schematic Writer

**Files:**
- Create: `backend/tools/schematic_writer.py`
- Create: `tests/test_schematic_writer.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_schematic_writer.py
import pytest
from backend.tools.schematic_writer import (
    SchematicWriter,
    validate_sexp,
    SchematicError,
)

def test_validate_balanced_parens():
    assert validate_sexp("(a (b c) (d e))") is True

def test_validate_unbalanced_parens():
    assert validate_sexp("(a (b c)") is False

def test_writer_builds_minimal_schematic():
    w = SchematicWriter()
    w.add_symbol("R1", "Device:R", x=100.0, y=100.0, value="10k")
    w.add_symbol("C1", "Device:C", x=120.0, y=100.0, value="100nF")
    content = w.build()
    assert "(kicad_sch" in content
    assert 'Device:R' in content
    assert 'Device:C' in content
    assert "R1" in content

def test_writer_raises_on_invalid_lib_id(monkeypatch):
    import backend.tools.component_db as db_mod
    monkeypatch.setattr(db_mod, "lib_id_exists", lambda _: False)
    w = SchematicWriter(validate_lib_ids=True)
    with pytest.raises(SchematicError, match="lib_id not found"):
        w.add_symbol("R1", "FakeLib:FakeChip", x=0.0, y=0.0, value="x")
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_schematic_writer.py -v
```

Expected: `ModuleNotFoundError: No module named 'backend.tools.schematic_writer'`

- [ ] **Step 3: Implement `backend/tools/schematic_writer.py`**

```python
from __future__ import annotations
import uuid as _uuid

from backend.tools.component_db import lib_id_exists


class SchematicError(Exception):
    pass


def validate_sexp(text: str) -> bool:
    depth = 0
    for ch in text:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth < 0:
                return False
    return depth == 0


def _uid() -> str:
    return str(_uuid.uuid4())


class SchematicWriter:
    def __init__(self, validate_lib_ids: bool = False):
        self._validate = validate_lib_ids
        self._symbols: list[dict] = []
        self._wires: list[tuple[float, float, float, float]] = []
        self._power_symbols: list[dict] = []

    def add_symbol(
        self,
        reference: str,
        lib_id: str,
        x: float,
        y: float,
        value: str,
        angle: float = 0.0,
    ) -> None:
        if self._validate and not lib_id_exists(lib_id):
            raise SchematicError(f"lib_id not found in component DB: {lib_id}")
        self._symbols.append(
            {"ref": reference, "lib_id": lib_id, "x": x, "y": y, "value": value, "angle": angle}
        )

    def add_wire(self, x1: float, y1: float, x2: float, y2: float) -> None:
        self._wires.append((x1, y1, x2, y2))

    def add_power(self, net: str, x: float, y: float) -> None:
        lib_id = f"power:{net.upper()}"
        self._power_symbols.append({"lib_id": lib_id, "net": net, "x": x, "y": y})

    def build(self) -> str:
        lines: list[str] = [
            '(kicad_sch (version 20230121) (generator eda_ai_agent)',
            '  (paper "A4")',
            '  (lib_symbols)',
        ]
        for sym in self._symbols + self._power_symbols:
            ref = sym.get("ref", sym.get("net", "PWR"))
            val = sym.get("value", sym.get("net", ""))
            lib_id = sym["lib_id"]
            x, y = sym["x"], sym["y"]
            angle = sym.get("angle", 0.0)
            lines += [
                f'  (symbol (lib_id "{lib_id}") (at {x:.2f} {y:.2f} {angle:.0f}) (unit 1)',
                f'    (in_bom yes) (on_board yes)',
                f'    (uuid "{_uid()}")',
                f'    (property "Reference" "{ref}" (at {x+2.54:.2f} {y-1.27:.2f} 0)',
                f'      (effects (font (size 1.27 1.27))))',
                f'    (property "Value" "{val}" (at {x+2.54:.2f} {y+1.27:.2f} 0)',
                f'      (effects (font (size 1.27 1.27))))',
                f'  )',
            ]
        for (x1, y1, x2, y2) in self._wires:
            lines += [
                f'  (wire (pts (xy {x1:.2f} {y1:.2f}) (xy {x2:.2f} {y2:.2f}))',
                f'    (stroke (width 0) (type default))',
                f'    (uuid "{_uid()}")',
                f'  )',
            ]
        lines.append(')')
        return "\n".join(lines)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_schematic_writer.py -v
```

Expected: `4 passed`

- [ ] **Step 5: Commit**

```bash
git add backend/tools/schematic_writer.py tests/test_schematic_writer.py
git commit -m "feat: schematic writer — builds .kicad_sch S-expression, validates lib_ids and paren balance"
```

---

## Task 7: KiCad CLI Tool

**Files:**
- Create: `backend/tools/kicad_cli.py`
- Create: `tests/test_kicad_cli.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_kicad_cli.py
import json, pytest
from unittest.mock import patch, MagicMock
from backend.tools.kicad_cli import run_erc, ERCResult, KiCadNotFoundError

MOCK_ERC_OUTPUT = json.dumps({
    "schematic": {"error_count": 1, "warning_count": 0},
    "sheets": [{"violations": [
        {"type": "pin_not_connected", "description": "Pin unconnected", "severity": "error",
         "items": [{"description": "U1 pin 14"}]}
    ]}]
})

def test_run_erc_no_kicad_raises():
    with patch("backend.tools.kicad_cli._find_kicad_cli", return_value=None):
        with pytest.raises(KiCadNotFoundError):
            run_erc("/fake/path.kicad_sch")

def test_run_erc_parses_violations(tmp_path):
    sch = tmp_path / "test.kicad_sch"
    sch.write_text("(kicad_sch)")

    def fake_run(cmd, **kwargs):
        erc_output = tmp_path / "erc_report.json"
        erc_output.write_text(MOCK_ERC_OUTPUT)
        m = MagicMock()
        m.returncode = 0
        return m

    with patch("backend.tools.kicad_cli._find_kicad_cli", return_value="/usr/bin/kicad-cli"), \
         patch("subprocess.run", side_effect=fake_run):
        result = run_erc(str(sch), output_dir=str(tmp_path))

    assert result.error_count == 1
    assert len(result.violations) == 1
    assert "pin_not_connected" in result.violations[0]["type"]

def test_run_erc_clean_schematic(tmp_path):
    sch = tmp_path / "clean.kicad_sch"
    sch.write_text("(kicad_sch)")
    clean_output = json.dumps({"schematic": {"error_count": 0, "warning_count": 0}, "sheets": []})

    def fake_run(cmd, **kwargs):
        erc_output = tmp_path / "erc_report.json"
        erc_output.write_text(clean_output)
        m = MagicMock(); m.returncode = 0; return m

    with patch("backend.tools.kicad_cli._find_kicad_cli", return_value="/usr/bin/kicad-cli"), \
         patch("subprocess.run", side_effect=fake_run):
        result = run_erc(str(sch), output_dir=str(tmp_path))

    assert result.error_count == 0
    assert result.is_clean
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_kicad_cli.py -v
```

Expected: `ModuleNotFoundError: No module named 'backend.tools.kicad_cli'`

- [ ] **Step 3: Implement `backend/tools/kicad_cli.py`**

```python
from __future__ import annotations
import json, platform, shutil, subprocess, tempfile
from dataclasses import dataclass, field
from pathlib import Path

from backend.config import load_config


class KiCadNotFoundError(Exception):
    pass


@dataclass
class ERCResult:
    error_count: int = 0
    warning_count: int = 0
    violations: list[dict] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return self.error_count == 0


def _find_kicad_cli() -> str | None:
    cfg = load_config()
    if cfg.kicad_cli_path and Path(cfg.kicad_cli_path).exists():
        return cfg.kicad_cli_path

    # Platform defaults
    candidates = {
        "Darwin": ["/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"],
        "Windows": ["C:\\Program Files\\KiCad\\8.0\\bin\\kicad-cli.exe"],
        "Linux": ["/usr/bin/kicad-cli"],
    }.get(platform.system(), [])

    for path in candidates:
        if Path(path).exists():
            return path
    return shutil.which("kicad-cli")


def run_erc(schematic_path: str, output_dir: str | None = None) -> ERCResult:
    cli = _find_kicad_cli()
    if not cli:
        raise KiCadNotFoundError(
            "kicad-cli not found. Set kicad_cli_path in Settings or install KiCad."
        )

    with tempfile.TemporaryDirectory() as tmp:
        out_dir = output_dir or tmp
        erc_file = Path(out_dir) / "erc_report.json"
        subprocess.run(
            [cli, "sch", "erc", "--output", str(erc_file), schematic_path],
            capture_output=True, text=True, check=False,
        )
        if not erc_file.exists():
            return ERCResult()
        data = json.loads(erc_file.read_text())

    sch_info = data.get("schematic", {})
    violations = [
        v
        for sheet in data.get("sheets", [])
        for v in sheet.get("violations", [])
    ]
    return ERCResult(
        error_count=sch_info.get("error_count", 0),
        warning_count=sch_info.get("warning_count", 0),
        violations=violations,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_kicad_cli.py -v
```

Expected: `3 passed`

- [ ] **Step 5: Commit**

```bash
git add backend/tools/kicad_cli.py tests/test_kicad_cli.py
git commit -m "feat: kicad-cli ERC wrapper — auto-detects CLI, runs ERC, returns ERCResult"
```

---

## Task 8: BaseAgent

**Files:**
- Create: `backend/agents/base.py`

- [ ] **Step 1: Implement `backend/agents/base.py`**

```python
"""
BaseAgent: async LiteLLM tool-call loop with token streaming.

Each subclass defines system_prompt and tools. Call agent.run(messages, on_token).
The loop continues until the LLM returns a non-tool-call response (text finish)
or calls the agent's designated finalize tool.

Tool functions are plain Python callables registered with @agent.tool().
Tools that need to pause execution (ask_user) are declared as async and may await
an external queue.
"""
from __future__ import annotations
import inspect, json
from collections.abc import AsyncGenerator, Callable
from typing import Any

import litellm

from backend.config import load_config


class ToolCallError(Exception):
    pass


class BaseAgent:
    system_prompt: str = ""
    finalize_tool: str = ""  # name of the tool whose call signals completion

    def __init__(self) -> None:
        self._tools: dict[str, Callable] = {}
        self._tool_schemas: list[dict] = []

    def tool(self, fn: Callable) -> Callable:
        name = fn.__name__
        doc = (fn.__doc__ or "").strip().split("\n")[0]
        sig = inspect.signature(fn)
        props: dict[str, Any] = {}
        required: list[str] = []
        for pname, param in sig.parameters.items():
            if pname in ("self", "session"):
                continue
            ann = param.annotation
            json_type = {str: "string", int: "integer", float: "number", bool: "boolean", list: "array"}.get(ann, "string")
            props[pname] = {"type": json_type, "description": pname}
            if param.default is inspect.Parameter.empty:
                required.append(pname)
        self._tool_schemas.append({
            "type": "function",
            "function": {"name": name, "description": doc, "parameters": {"type": "object", "properties": props, "required": required}},
        })
        self._tools[name] = fn
        return fn

    async def run(
        self,
        messages: list[dict],
        on_token: Callable[[str], None] | None = None,
        extra_kwargs: dict | None = None,
    ) -> str:
        """Run the tool-call loop. Returns final text response or finalize tool args as JSON."""
        cfg = load_config()
        kwargs: dict[str, Any] = {
            "model": cfg.model,
            "messages": [{"role": "system", "content": self.system_prompt}] + messages,
            "tools": self._tool_schemas,
            "stream": True,
        }
        if cfg.api_key:
            kwargs["api_key"] = cfg.api_key
        if cfg.base_url:
            kwargs["base_url"] = cfg.base_url
        if extra_kwargs:
            kwargs.update(extra_kwargs)

        MAX_ITERS = 20
        for _ in range(MAX_ITERS):
            collected_text = ""
            tool_calls_buffer: dict[int, dict] = {}

            response = await litellm.acompletion(**kwargs)
            async for chunk in response:
                delta = chunk.choices[0].delta
                if delta.content:
                    collected_text += delta.content
                    if on_token:
                        on_token(delta.content)
                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        idx = tc.index
                        if idx not in tool_calls_buffer:
                            tool_calls_buffer[idx] = {"id": tc.id or "", "name": "", "args": ""}
                        if tc.function.name:
                            tool_calls_buffer[idx]["name"] = tc.function.name
                        if tc.function.arguments:
                            tool_calls_buffer[idx]["args"] += tc.function.arguments

            if not tool_calls_buffer:
                return collected_text

            # Execute tool calls
            tool_results = []
            for tc in sorted(tool_calls_buffer.values(), key=lambda x: x["name"]):
                name, args_str = tc["name"], tc["args"]
                args = json.loads(args_str) if args_str else {}
                fn = self._tools.get(name)
                if fn is None:
                    result = f"Error: unknown tool {name}"
                else:
                    try:
                        if inspect.iscoroutinefunction(fn):
                            result = await fn(**args)
                        else:
                            result = fn(**args)
                    except Exception as e:
                        result = f"Tool error: {e}"

                result_str = json.dumps(result) if not isinstance(result, str) else result
                tool_results.append({"tool_call_id": tc["id"], "name": name, "content": result_str})

                if name == self.finalize_tool:
                    return result_str

            # Append assistant + tool results to messages for next iteration
            kwargs["messages"].append({"role": "assistant", "content": collected_text or None,
                                       "tool_calls": [{"id": t["tool_call_id"], "type": "function",
                                                        "function": {"name": t["name"], "arguments": tool_calls_buffer[i]["args"]}}
                                                       for i, t in enumerate(tool_results)]})
            for tr in tool_results:
                kwargs["messages"].append({"role": "tool", "tool_call_id": tr["tool_call_id"], "content": tr["content"]})

        return "Max iterations reached."
```

- [ ] **Step 2: Commit**

```bash
git add backend/agents/base.py
git commit -m "feat: BaseAgent — async LiteLLM tool-call loop with streaming and finalize-tool exit"
```

---

## Task 9: Session State + Orchestrator

**Files:**
- Create: `backend/orchestrator.py`
- Create: `tests/test_orchestrator.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_orchestrator.py
import asyncio, pytest
from unittest.mock import AsyncMock, patch
from backend.orchestrator import Session, SessionState, PipelineStage

def test_session_state_defaults():
    state = SessionState()
    assert state.requirements is None
    assert state.bom is None
    assert state.stage == PipelineStage.REQUIREMENTS
    assert state.correction_attempts == 0

@pytest.mark.asyncio
async def test_session_user_input_queue():
    messages = []
    async def fake_send(msg): messages.append(msg)

    session = Session("test-id", fake_send)
    asyncio.get_event_loop().call_soon(lambda: asyncio.ensure_future(session.put_user_input("hello")))
    result = await session.wait_for_user_input()
    assert result == "hello"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_orchestrator.py -v
```

Expected: `ModuleNotFoundError: No module named 'backend.orchestrator'`

- [ ] **Step 3: Implement `backend/orchestrator.py`**

```python
from __future__ import annotations
import asyncio, json
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PipelineStage(str, Enum):
    REQUIREMENTS = "requirements"
    DESIGN = "design"
    GENERATION = "generation"
    VALIDATION = "validation"
    DONE = "done"


@dataclass
class SessionState:
    stage: PipelineStage = PipelineStage.REQUIREMENTS
    requirements: dict | None = None
    bom: list[dict] | None = None
    schematic_path: str | None = None
    schematic_content: str | None = None
    erc_report: dict | None = None
    correction_attempts: int = 0
    iteration_count: int = 0


class Session:
    def __init__(self, session_id: str, send: Callable[[dict], Coroutine]) -> None:
        self.session_id = session_id
        self.send = send
        self.state = SessionState()
        self._user_input: asyncio.Queue[str] = asyncio.Queue()

    async def put_user_input(self, text: str) -> None:
        await self._user_input.put(text)

    async def wait_for_user_input(self) -> str:
        return await self._user_input.get()

    async def emit_token(self, text: str) -> None:
        await self.send({"type": "token", "content": text})

    async def emit_stage(self, stage: PipelineStage) -> None:
        self.state.stage = stage
        await self.send({"type": "stage", "stage": stage.value})


class Orchestrator:
    def __init__(self, session: Session) -> None:
        self.session = session

    async def run(self, first_message: str) -> None:
        from backend.agents.req_agent import ReqAgent
        from backend.agents.design_agent import DesignAgent
        from backend.agents.kicad_gen_agent import KiCadGenAgent
        from backend.agents.validation_agent import ValidationAgent

        s = self.session

        # --- Stage 1: Requirements ---
        await s.emit_stage(PipelineStage.REQUIREMENTS)
        req_agent = ReqAgent(session=s)
        req_result = await req_agent.run(
            messages=[{"role": "user", "content": first_message}],
            on_token=lambda t: asyncio.ensure_future(s.emit_token(t)),
        )
        s.state.requirements = json.loads(req_result) if req_result.strip().startswith("{") else {"description": req_result}

        # --- Stage 2: Design ---
        await s.emit_stage(PipelineStage.DESIGN)
        while s.state.correction_attempts <= 3:
            design_agent = DesignAgent(session=s)
            bom_result = await design_agent.run(
                messages=[{"role": "user", "content": json.dumps(s.state.requirements)}],
                on_token=lambda t: asyncio.ensure_future(s.emit_token(t)),
            )
            s.state.bom = json.loads(bom_result) if bom_result.strip().startswith("[") else []

            # --- Stage 3: KiCad Generation ---
            await s.emit_stage(PipelineStage.GENERATION)
            gen_agent = KiCadGenAgent(session=s)
            sch_result = await gen_agent.run(
                messages=[{"role": "user", "content": json.dumps(s.state.bom)}],
                on_token=lambda t: asyncio.ensure_future(s.emit_token(t)),
            )
            s.state.schematic_content = sch_result

            # --- Stage 4: Validation ---
            await s.emit_stage(PipelineStage.VALIDATION)
            val_agent = ValidationAgent(session=s)
            erc_result = await val_agent.run(
                messages=[{"role": "user", "content": sch_result}],
                on_token=lambda t: asyncio.ensure_future(s.emit_token(t)),
            )
            s.state.erc_report = json.loads(erc_result) if erc_result.strip().startswith("{") else {"raw": erc_result}

            if s.state.erc_report.get("error_count", 0) == 0:
                break
            s.state.correction_attempts += 1
            if s.state.correction_attempts > 3:
                break

        # --- Done ---
        await s.emit_stage(PipelineStage.DONE)
        await s.send({"type": "schematic", "content": s.state.schematic_content or ""})
        await s.send({"type": "bom", "items": s.state.bom or []})
        await s.send({"type": "erc", "report": s.state.erc_report or {}})
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_orchestrator.py -v
```

Expected: `2 passed`

- [ ] **Step 5: Commit**

```bash
git add backend/orchestrator.py tests/test_orchestrator.py
git commit -m "feat: Session + Orchestrator — async pipeline routing, user-input queue, stage transitions"
```

---

## Task 10: Req Agent

**Files:**
- Create: `backend/agents/req_agent.py`

- [ ] **Step 1: Implement `backend/agents/req_agent.py`**

```python
from __future__ import annotations
import json
from backend.agents.base import BaseAgent
from backend.orchestrator import Session


class ReqAgent(BaseAgent):
    finalize_tool = "finalize_requirements"
    system_prompt = """You are an electronics requirements analyst. Your job is to gather a complete, unambiguous circuit specification from the user.

Ask ONE clarifying question at a time. Cover these topics (but only ask if still unclear):
1. Circuit function (what does it do?)
2. Input voltage source and range
3. Output voltage and maximum current
4. Form factor / size constraints
5. Cost sensitivity (hobbyist vs commercial)
6. Any specific ICs or components preferred

Once you have enough information (minimum: function, input, output), call finalize_requirements with the spec.
Do NOT ask redundant questions. Be concise."""

    def __init__(self, session: Session) -> None:
        super().__init__()
        self._session = session

        @self.tool
        async def ask_user(question: str) -> str:
            """Ask the user a clarifying question and return their answer."""
            await self._session.emit_token(f"\n\n{question}\n")
            return await self._session.wait_for_user_input()

        @self.tool
        def finalize_requirements(
            function: str,
            input_voltage: str,
            output_voltage: str,
            output_current_ma: int,
            form_factor: str,
            cost_tier: str,
            notes: str,
        ) -> str:
            """Finalize the circuit requirements when all needed info is collected."""
            spec = {
                "function": function,
                "input_voltage": input_voltage,
                "output_voltage": output_voltage,
                "output_current_ma": output_current_ma,
                "form_factor": form_factor,
                "cost_tier": cost_tier,
                "notes": notes,
            }
            return json.dumps(spec)
```

- [ ] **Step 2: Commit**

```bash
git add backend/agents/req_agent.py
git commit -m "feat: ReqAgent — ask_user (suspends on queue), finalize_requirements structured spec"
```

---

## Task 11: Design Agent

**Files:**
- Create: `backend/agents/design_agent.py`

- [ ] **Step 1: Implement `backend/agents/design_agent.py`**

```python
from __future__ import annotations
import json
from backend.agents.base import BaseAgent
from backend.orchestrator import Session
from backend.tools.component_db import search_components, get_component_details


class DesignAgent(BaseAgent):
    finalize_tool = "finalize_bom"
    system_prompt = """You are an expert electronics engineer specializing in component selection.

Given a circuit specification, select appropriate components from the database and build a Bill of Materials (BOM).

Rules:
- ONLY use lib_ids returned by search_components. NEVER invent lib_ids.
- Call get_component_details to verify pin count before including a component.
- Include all passive components (decoupling caps, pull-up/down resistors, etc.).
- When the spec mentions a correction loop (ERC errors), fix only the flagged components.
- Call finalize_bom when the BOM is complete."""

    def __init__(self, session: Session) -> None:
        super().__init__()
        self._session = session

        @self.tool
        def search_components(query: str, category: str) -> list:
            """Search the component database. Returns lib_id, name, description, pin_count."""
            from backend.tools.component_db import search_components as _search
            return _search(query, category)

        @self.tool
        def get_component_details(lib_id: str) -> dict:
            """Get full details for a specific component lib_id."""
            result = get_component_details(lib_id)
            return result or {"error": f"lib_id not found: {lib_id}"}

        @self.tool
        def finalize_bom(components: list) -> str:
            """Finalize BOM. components: [{lib_id, reference, value, quantity, notes}]"""
            return json.dumps(components)
```

- [ ] **Step 2: Commit**

```bash
git add backend/agents/design_agent.py
git commit -m "feat: DesignAgent — DB-constrained BOM selection, search + details + finalize_bom"
```

---

## Task 12: KiCad Gen Agent

**Files:**
- Create: `backend/agents/kicad_gen_agent.py`

- [ ] **Step 1: Implement `backend/agents/kicad_gen_agent.py`**

```python
from __future__ import annotations
import json, tempfile
from pathlib import Path

from backend.agents.base import BaseAgent
from backend.orchestrator import Session
from backend.tools.component_db import get_component_pins
from backend.tools.schematic_writer import SchematicWriter, validate_sexp


class KiCadGenAgent(BaseAgent):
    finalize_tool = "write_schematic"
    system_prompt = """You are a KiCad schematic generation expert.

Given a BOM, generate a valid KiCad 7 .kicad_sch S-expression file.

Steps:
1. Call get_component_pins for each component to learn its pin numbers and names.
2. Use write_schematic with the complete file content.

The .kicad_sch format:
- Starts with: (kicad_sch (version 20230121) (generator eda_ai_agent)
- Each symbol: (symbol (lib_id "X:Y") (at X Y 0) (unit 1) (in_bom yes) (on_board yes) (uuid "...") (property "Reference" "R1" ...) (property "Value" "10k" ...))
- Wires: (wire (pts (xy X1 Y1) (xy X2 Y2)) (stroke (width 0) (type default)) (uuid "..."))
- Ends with: )

Place components on a grid of 2.54mm steps. Reference designators: R1,R2... C1,C2... U1,U2...
Connect power pins to VCC/GND power symbols."""

    def __init__(self, session: Session) -> None:
        super().__init__()
        self._session = session
        self._tmp_dir = tempfile.mkdtemp(prefix="eda_sch_")

        @self.tool
        def get_component_pins(lib_id: str) -> list:
            """Get pin data for a component. Returns [{name, number}]."""
            return get_component_pins(lib_id)

        @self.tool
        def write_schematic(content: str) -> str:
            """Write the .kicad_sch content to disk. Returns file path."""
            if not validate_sexp(content):
                return "Error: unbalanced parentheses in schematic content"
            path = Path(self._tmp_dir) / "output.kicad_sch"
            path.write_text(content, encoding="utf-8")
            self._session.state.schematic_path = str(path)
            return str(path)
```

- [ ] **Step 2: Commit**

```bash
git add backend/agents/kicad_gen_agent.py
git commit -m "feat: KiCadGenAgent — generates .kicad_sch S-expression, validates paren balance before saving"
```

---

## Task 13: Validation Agent

**Files:**
- Create: `backend/agents/validation_agent.py`

- [ ] **Step 1: Implement `backend/agents/validation_agent.py`**

```python
from __future__ import annotations
import json

from backend.agents.base import BaseAgent
from backend.orchestrator import Session
from backend.tools.kicad_cli import KiCadNotFoundError, run_erc


class ValidationAgent(BaseAgent):
    finalize_tool = "finalize_erc_report"
    system_prompt = """You are a KiCad ERC (Electrical Rules Check) interpreter.

When given a schematic path:
1. Call run_erc to execute the ERC check.
2. For each violation, call translate_erc_error to produce a human-readable fix suggestion.
3. Call finalize_erc_report with the complete results.

Be specific in your translations: name the component and pin, explain WHY it's an error, and suggest the fix."""

    def __init__(self, session: Session) -> None:
        super().__init__()
        self._session = session

        @self.tool
        def run_erc(schematic_path: str) -> dict:
            """Run KiCad ERC on the schematic file. Returns error_count and violations list."""
            try:
                result = run_erc(schematic_path)
                return {
                    "error_count": result.error_count,
                    "warning_count": result.warning_count,
                    "violations": result.violations,
                }
            except KiCadNotFoundError:
                return {"error_count": 0, "warning_count": 0, "violations": [],
                        "note": "KiCad CLI not configured — ERC skipped"}

        @self.tool
        def translate_erc_error(error_type: str, description: str, component: str) -> str:
            """Translate a raw ERC error into a human-readable fix suggestion."""
            return f"{component}: {description} (type: {error_type})"

        @self.tool
        def finalize_erc_report(error_count: int, violations_translated: list) -> str:
            """Submit the final ERC report with translated error messages."""
            return json.dumps({
                "error_count": error_count,
                "violations_translated": violations_translated,
            })
```

- [ ] **Step 2: Commit**

```bash
git add backend/agents/validation_agent.py
git commit -m "feat: ValidationAgent — runs ERC, translates errors, returns structured report"
```

---

## Task 14: FastAPI App

**Files:**
- Create: `backend/main.py`

- [ ] **Step 1: Implement `backend/main.py`**

```python
from __future__ import annotations
import asyncio, json, uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from backend.config import load_config, save_config, sanitized_config, AgentConfig
from backend.db.scanner import scan_and_merge
from backend.orchestrator import Orchestrator, Session


@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg = load_config()
    if cfg.db_last_scanned is None:
        scan_and_merge()
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_sessions: dict[str, Session] = {}


@app.get("/api/config")
async def get_config():
    return JSONResponse(sanitized_config())


@app.post("/api/config")
async def post_config(payload: dict):
    cfg = load_config()
    for key in ("model", "api_key", "base_url", "kicad_cli_path"):
        if key in payload and payload[key] is not None:
            setattr(cfg, key, payload[key])
    save_config(cfg)
    return JSONResponse({"status": "saved"})


@app.post("/api/rescan")
async def rescan():
    added = scan_and_merge()
    return JSONResponse({"added": added})


@app.get("/api/download/{session_id}")
async def download_schematic(session_id: str):
    session = _sessions.get(session_id)
    if not session or not session.state.schematic_path:
        return JSONResponse({"error": "not found"}, status_code=404)
    return FileResponse(
        session.state.schematic_path,
        media_type="application/octet-stream",
        filename="schematic.kicad_sch",
    )


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    session_id = str(uuid.uuid4())

    async def send(msg: dict) -> None:
        await ws.send_json(msg)

    session = Session(session_id, send)
    _sessions[session_id] = session
    await ws.send_json({"type": "session_id", "session_id": session_id})

    orchestrator_task: asyncio.Task | None = None

    try:
        while True:
            raw = await ws.receive_text()
            msg = json.loads(raw)

            if msg["type"] == "new_session":
                session = Session(session_id, send)
                _sessions[session_id] = session

            elif msg["type"] == "user_message":
                if orchestrator_task is None or orchestrator_task.done():
                    orchestrator_task = asyncio.create_task(
                        Orchestrator(session).run(msg["content"])
                    )
                else:
                    await session.put_user_input(msg["content"])

    except WebSocketDisconnect:
        _sessions.pop(session_id, None)
        if orchestrator_task and not orchestrator_task.done():
            orchestrator_task.cancel()
```

- [ ] **Step 2: Start the server and verify it starts**

```bash
uvicorn backend.main:app --reload --port 8000
```

Expected: `INFO: Application startup complete.` (may see KiCad scanner message)

- [ ] **Step 3: Test the config endpoint**

```bash
curl http://localhost:8000/api/config
```

Expected: `{"model":"anthropic/claude-opus-4-7","api_key":null,...}`

- [ ] **Step 4: Commit**

```bash
git add backend/main.py
git commit -m "feat: FastAPI app — WebSocket /ws pipeline, GET/POST /api/config, /api/download"
```

---

## Task 15: Frontend Scaffolding

**Files:**
- Create: `frontend/` (Vite React TS project)
- Modify: `frontend/vite.config.ts`
- Modify: `frontend/index.html`

- [ ] **Step 1: Scaffold Vite React TS project**

```bash
npm create vite@latest frontend -- --template react-ts
cd frontend && npm install
```

- [ ] **Step 2: Install additional deps**

```bash
cd frontend && npm install
```

No extra packages needed — KiCanvas is loaded via CDN in index.html.

- [ ] **Step 3: Replace `frontend/vite.config.ts`**

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
      '/ws': { target: 'ws://localhost:8000', ws: true },
    },
  },
})
```

- [ ] **Step 4: Replace `frontend/index.html`**

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>EDA-AI-Agent</title>
    <script type="module" src="https://unpkg.com/kicanvas@latest/kicanvas.js"></script>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 5: Verify dev server starts**

```bash
cd frontend && npm run dev
```

Expected: `VITE ready at http://localhost:5173/` (React default page visible)

- [ ] **Step 6: Commit**

```bash
cd .. && git add frontend/
git commit -m "feat: frontend scaffolding — Vite React TS, proxy to :8000, KiCanvas CDN"
```

---

## Task 16: WebSocket Hook

**Files:**
- Create: `frontend/src/hooks/useAgentSocket.ts`
- Create: `frontend/src/api/client.ts`

- [ ] **Step 1: Create `frontend/src/api/client.ts`**

```typescript
export interface AgentConfig {
  model: string
  api_key: string
  base_url: string | null
  kicad_cli_path: string | null
  db_last_scanned: string | null
}

export async function fetchConfig(): Promise<AgentConfig> {
  const res = await fetch('/api/config')
  return res.json()
}

export async function saveConfig(patch: Partial<AgentConfig>): Promise<void> {
  await fetch('/api/config', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(patch),
  })
}

export async function rescanLibraries(): Promise<{ added: number }> {
  const res = await fetch('/api/rescan', { method: 'POST' })
  return res.json()
}

export function downloadSchematic(sessionId: string): void {
  window.location.href = `/api/download/${sessionId}`
}
```

- [ ] **Step 2: Create `frontend/src/hooks/useAgentSocket.ts`**

```typescript
import { useCallback, useEffect, useRef, useState } from 'react'

export type PipelineStage = 'requirements' | 'design' | 'generation' | 'validation' | 'done'

export interface ChatMessage {
  role: 'user' | 'agent'
  content: string
  timestamp: number
}

export interface BOMItem {
  lib_id: string
  reference: string
  value: string
  quantity: number
  notes?: string
}

export interface ERCReport {
  error_count: number
  violations_translated: string[]
  note?: string
}

interface AgentSocketState {
  messages: ChatMessage[]
  stage: PipelineStage
  schematicContent: string | null
  bom: BOMItem[]
  ercReport: ERCReport | null
  sessionId: string | null
  connected: boolean
}

interface AgentSocketActions {
  sendMessage: (content: string) => void
  newSession: () => void
}

export function useAgentSocket(): AgentSocketState & AgentSocketActions {
  const wsRef = useRef<WebSocket | null>(null)
  const [state, setState] = useState<AgentSocketState>({
    messages: [],
    stage: 'requirements',
    schematicContent: null,
    bom: [],
    ercReport: null,
    sessionId: null,
    connected: false,
  })
  const pendingTokenRef = useRef('')

  const flushToken = useCallback(() => {
    if (!pendingTokenRef.current) return
    const token = pendingTokenRef.current
    pendingTokenRef.current = ''
    setState(s => {
      const msgs = [...s.messages]
      if (msgs.length > 0 && msgs[msgs.length - 1].role === 'agent') {
        msgs[msgs.length - 1] = { ...msgs[msgs.length - 1], content: msgs[msgs.length - 1].content + token }
      } else {
        msgs.push({ role: 'agent', content: token, timestamp: Date.now() })
      }
      return { ...s, messages: msgs }
    })
  }, [])

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:5173/ws')
    wsRef.current = ws

    ws.onopen = () => setState(s => ({ ...s, connected: true }))
    ws.onclose = () => setState(s => ({ ...s, connected: false }))

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data)
      switch (msg.type) {
        case 'session_id':
          setState(s => ({ ...s, sessionId: msg.session_id }))
          break
        case 'token':
          pendingTokenRef.current += msg.content
          requestAnimationFrame(flushToken)
          break
        case 'stage':
          flushToken()
          setState(s => ({ ...s, stage: msg.stage }))
          break
        case 'schematic':
          setState(s => ({ ...s, schematicContent: msg.content }))
          break
        case 'bom':
          setState(s => ({ ...s, bom: msg.items }))
          break
        case 'erc':
          setState(s => ({ ...s, ercReport: msg.report }))
          break
      }
    }

    return () => ws.close()
  }, [flushToken])

  const sendMessage = useCallback((content: string) => {
    setState(s => ({
      ...s,
      messages: [...s.messages, { role: 'user', content, timestamp: Date.now() }],
    }))
    wsRef.current?.send(JSON.stringify({ type: 'user_message', content }))
  }, [])

  const newSession = useCallback(() => {
    setState(s => ({
      ...s,
      messages: [],
      stage: 'requirements',
      schematicContent: null,
      bom: [],
      ercReport: null,
    }))
    wsRef.current?.send(JSON.stringify({ type: 'new_session' }))
  }, [])

  return { ...state, sendMessage, newSession }
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/hooks/useAgentSocket.ts frontend/src/api/client.ts
git commit -m "feat: useAgentSocket hook + REST client — WebSocket message handling, token streaming"
```

---

## Task 17: ChatPanel Component

**Files:**
- Create: `frontend/src/components/ChatPanel.tsx`

- [ ] **Step 1: Create `frontend/src/components/ChatPanel.tsx`**

```tsx
import { useEffect, useRef, useState } from 'react'
import type { ChatMessage, PipelineStage } from '../hooks/useAgentSocket'

const STAGES: PipelineStage[] = ['requirements', 'design', 'generation', 'validation']
const STAGE_LABELS: Record<string, string> = {
  requirements: 'Requirements',
  design: 'Design',
  generation: 'Generation',
  validation: 'Validation',
}

interface Props {
  messages: ChatMessage[]
  stage: PipelineStage
  connected: boolean
  onSend: (text: string) => void
}

export function ChatPanel({ messages, stage, connected, onSend }: Props) {
  const [input, setInput] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = () => {
    const text = input.trim()
    if (!text || !connected) return
    onSend(text)
    setInput('')
  }

  const stageIndex = STAGES.indexOf(stage as any)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Stage progress bar */}
      <div style={{ padding: '8px 12px', borderBottom: '1px solid #e5e7eb', display: 'flex', gap: 4, alignItems: 'center' }}>
        {STAGES.map((s, i) => (
          <div key={s} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <div style={{
              height: 4, width: 40, borderRadius: 2,
              background: i <= stageIndex ? '#7c3aed' : '#e5e7eb',
            }} />
            <span style={{ fontSize: 10, color: i <= stageIndex ? '#7c3aed' : '#9ca3af' }}>
              {STAGE_LABELS[s]}
            </span>
          </div>
        ))}
      </div>

      {/* Messages */}
      <div style={{ flex: 1, overflowY: 'auto', padding: 12, display: 'flex', flexDirection: 'column', gap: 8 }}>
        {messages.length === 0 && (
          <div style={{ textAlign: 'center', color: '#9ca3af', marginTop: 40, fontSize: 14 }}>
            Describe the circuit you want to build.
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} style={{ display: 'flex', justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
            <div style={{
              maxWidth: '80%',
              padding: '8px 12px',
              borderRadius: msg.role === 'user' ? '12px 12px 2px 12px' : '12px 12px 12px 2px',
              background: msg.role === 'user' ? '#7c3aed' : '#f3f4f6',
              color: msg.role === 'user' ? 'white' : '#111827',
              fontSize: 13,
              lineHeight: 1.6,
              whiteSpace: 'pre-wrap',
            }}>
              {msg.content}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div style={{ padding: 10, borderTop: '1px solid #e5e7eb', display: 'flex', gap: 8 }}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleSend()}
          placeholder={connected ? 'Type your message...' : 'Connecting...'}
          disabled={!connected}
          style={{
            flex: 1, padding: '8px 12px', borderRadius: 8, border: '1px solid #d1d5db',
            fontSize: 13, outline: 'none',
          }}
        />
        <button
          onClick={handleSend}
          disabled={!connected || !input.trim()}
          style={{
            padding: '8px 16px', borderRadius: 8, border: 'none',
            background: '#7c3aed', color: 'white', fontSize: 13,
            cursor: 'pointer', opacity: (!connected || !input.trim()) ? 0.5 : 1,
          }}
        >
          Send
        </button>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/ChatPanel.tsx
git commit -m "feat: ChatPanel — message stream, stage progress bar, keyboard-submit input"
```

---

## Task 18: SchematicViewer Component

**Files:**
- Create: `frontend/src/components/SchematicViewer.tsx`

- [ ] **Step 1: Create `frontend/src/components/SchematicViewer.tsx`**

```tsx
import { useEffect, useRef } from 'react'
import type { BOMItem, ERCReport } from '../hooks/useAgentSocket'

interface Props {
  schematicContent: string | null
  bom: BOMItem[]
  ercReport: ERCReport | null
  sessionId: string | null
  onDownloadSchematic: () => void
  onDownloadBOM: () => void
}

export function SchematicViewer({ schematicContent, bom, ercReport, onDownloadSchematic, onDownloadBOM }: Props) {
  const viewerRef = useRef<HTMLElement | null>(null)

  useEffect(() => {
    if (!schematicContent || !viewerRef.current) return
    const blob = new Blob([schematicContent], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const el = viewerRef.current as any
    if (el.load) el.load(url)
    return () => URL.revokeObjectURL(url)
  }, [schematicContent])

  const ercColor = !ercReport ? '#9ca3af' : ercReport.error_count === 0 ? '#15803d' : '#dc2626'
  const ercLabel = !ercReport ? '—' : ercReport.error_count === 0 ? '✓ Clean' : `${ercReport.error_count} errors`

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Toolbar */}
      <div style={{ padding: '8px 12px', borderBottom: '1px solid #e5e7eb', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: 11, fontWeight: 600, color: '#6b7280', textTransform: 'uppercase', letterSpacing: '.05em' }}>
          Schematic Preview
        </span>
        <div style={{ display: 'flex', gap: 6 }}>
          <button onClick={onDownloadSchematic} disabled={!schematicContent} style={btnStyle}>
            ↓ .kicad_sch
          </button>
          <button onClick={onDownloadBOM} disabled={bom.length === 0} style={btnStyle}>
            ↓ BOM.csv
          </button>
        </div>
      </div>

      {/* KiCanvas viewer */}
      <div style={{ flex: 1, background: '#f9fafb', position: 'relative', overflow: 'hidden' }}>
        {schematicContent ? (
          <kicanvas-embed
            ref={viewerRef as any}
            style={{ width: '100%', height: '100%', display: 'block' }}
            controls="basic"
          />
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', flexDirection: 'column', gap: 8, color: '#9ca3af' }}>
            <div style={{ fontSize: 40 }}>📐</div>
            <div style={{ fontSize: 13 }}>Schematic will appear here after generation</div>
            <div style={{ fontSize: 11 }}>Powered by KiCanvas</div>
          </div>
        )}
      </div>

      {/* Status bar */}
      <div style={{ padding: '5px 12px', borderTop: '1px solid #e5e7eb', background: '#f9fafb', display: 'flex', gap: 16, fontSize: 11, color: '#6b7280' }}>
        <span>ERC: <span style={{ color: ercColor, fontWeight: 600 }}>{ercLabel}</span></span>
        <span>Components: <span style={{ fontWeight: 600 }}>{bom.length || '—'}</span></span>
        {ercReport?.note && <span style={{ color: '#9ca3af' }}>{ercReport.note}</span>}
      </div>
    </div>
  )
}

const btnStyle: React.CSSProperties = {
  fontSize: 11, padding: '4px 10px', borderRadius: 6,
  border: '1px solid #d1d5db', background: 'white',
  cursor: 'pointer', color: '#374151',
}

declare global {
  namespace JSX {
    interface IntrinsicElements {
      'kicanvas-embed': React.DetailedHTMLProps<React.HTMLAttributes<HTMLElement> & { controls?: string }, HTMLElement>
    }
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/SchematicViewer.tsx
git commit -m "feat: SchematicViewer — KiCanvas embed, download buttons, ERC status bar"
```

---

## Task 19: Settings Modal

**Files:**
- Create: `frontend/src/components/SettingsModal.tsx`

- [ ] **Step 1: Create `frontend/src/components/SettingsModal.tsx`**

```tsx
import { useEffect, useState } from 'react'
import { fetchConfig, saveConfig, rescanLibraries, type AgentConfig } from '../api/client'

interface Props {
  onClose: () => void
}

export function SettingsModal({ onClose }: Props) {
  const [cfg, setCfg] = useState<AgentConfig>({ model: '', api_key: '', base_url: null, kicad_cli_path: null, db_last_scanned: null })
  const [saving, setSaving] = useState(false)
  const [scanning, setScanning] = useState(false)
  const [scanResult, setScanResult] = useState<string | null>(null)

  useEffect(() => {
    fetchConfig().then(setCfg)
  }, [])

  const handleSave = async () => {
    setSaving(true)
    const patch = { ...cfg, api_key: cfg.api_key === '***' ? undefined : cfg.api_key }
    await saveConfig(patch)
    setSaving(false)
    onClose()
  }

  const handleRescan = async () => {
    setScanning(true)
    const result = await rescanLibraries()
    setScanResult(`Added ${result.added} symbols`)
    setScanning(false)
  }

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
      <div style={{ background: 'white', borderRadius: 12, padding: 24, width: 480, maxWidth: '95vw', boxShadow: '0 20px 60px rgba(0,0,0,.15)' }}>
        <h2 style={{ margin: '0 0 20px', fontSize: 18, fontWeight: 700 }}>Settings</h2>

        <section style={{ marginBottom: 20 }}>
          <h3 style={sectionHeader}>AI Provider</h3>
          <label style={labelStyle}>Model (LiteLLM format)</label>
          <input style={inputStyle} value={cfg.model} onChange={e => setCfg({ ...cfg, model: e.target.value })} placeholder="anthropic/claude-opus-4-7" />
          <p style={hintStyle}>e.g. openai/gpt-4o · anthropic/claude-opus-4-7 · ollama/llama3 · deepseek/deepseek-chat</p>

          <label style={labelStyle}>API Key</label>
          <input style={inputStyle} type="password" value={cfg.api_key ?? ''} onChange={e => setCfg({ ...cfg, api_key: e.target.value })} placeholder="sk-..." />
          <p style={hintStyle}>Stored in ~/.eda-agent/config.json — never sent to any server except your provider.</p>

          <label style={labelStyle}>Base URL <span style={{ color: '#9ca3af' }}>(optional — for Ollama / custom endpoints)</span></label>
          <input style={inputStyle} value={cfg.base_url ?? ''} onChange={e => setCfg({ ...cfg, base_url: e.target.value || null })} placeholder="http://localhost:11434" />
        </section>

        <hr style={{ border: 'none', borderTop: '1px solid #e5e7eb', margin: '0 0 20px' }} />

        <section style={{ marginBottom: 20 }}>
          <h3 style={sectionHeader}>KiCad Integration</h3>
          <label style={labelStyle}>KiCad CLI Path</label>
          <input style={inputStyle} value={cfg.kicad_cli_path ?? ''} onChange={e => setCfg({ ...cfg, kicad_cli_path: e.target.value || null })} placeholder="Auto-detect on save" />

          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 8 }}>
            <span style={{ fontSize: 12, color: '#6b7280', flex: 1 }}>
              {cfg.db_last_scanned ? `Library last scanned: ${new Date(cfg.db_last_scanned).toLocaleDateString()}` : 'Library not yet scanned'}
              {scanResult && <span style={{ marginLeft: 8, color: '#15803d' }}>{scanResult}</span>}
            </span>
            <button onClick={handleRescan} disabled={scanning} style={{ ...btnStyle, opacity: scanning ? 0.6 : 1 }}>
              {scanning ? 'Scanning...' : 'Re-scan Libraries'}
            </button>
          </div>
        </section>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
          <button onClick={onClose} style={btnStyle}>Cancel</button>
          <button onClick={handleSave} disabled={saving} style={{ ...btnStyle, background: '#7c3aed', color: 'white', border: 'none' }}>
            {saving ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </div>
    </div>
  )
}

const sectionHeader: React.CSSProperties = { fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '.06em', color: '#6b7280', margin: '0 0 10px' }
const labelStyle: React.CSSProperties = { display: 'block', fontSize: 12, color: '#374151', marginBottom: 4, marginTop: 10 }
const inputStyle: React.CSSProperties = { width: '100%', padding: '8px 10px', border: '1px solid #d1d5db', borderRadius: 8, fontSize: 13, boxSizing: 'border-box', outline: 'none' }
const hintStyle: React.CSSProperties = { fontSize: 11, color: '#9ca3af', margin: '3px 0 0' }
const btnStyle: React.CSSProperties = { padding: '8px 16px', borderRadius: 8, border: '1px solid #d1d5db', background: 'white', fontSize: 13, cursor: 'pointer' }
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/SettingsModal.tsx
git commit -m "feat: SettingsModal — model/API key/base URL/KiCad path config, re-scan button"
```

---

## Task 20: App Integration + End-to-End Smoke Test

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/main.tsx`

- [ ] **Step 1: Replace `frontend/src/main.tsx`**

```tsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
```

- [ ] **Step 2: Replace `frontend/src/App.tsx`**

```tsx
import { useEffect, useState } from 'react'
import { ChatPanel } from './components/ChatPanel'
import { SchematicViewer } from './components/SchematicViewer'
import { SettingsModal } from './components/SettingsModal'
import { useAgentSocket } from './hooks/useAgentSocket'
import { downloadSchematic, fetchConfig } from './api/client'

export default function App() {
  const [showSettings, setShowSettings] = useState(false)
  const [needsConfig, setNeedsConfig] = useState(false)
  const { messages, stage, schematicContent, bom, ercReport, sessionId, connected, sendMessage, newSession } = useAgentSocket()

  useEffect(() => {
    fetchConfig().then(cfg => {
      if (!cfg.api_key || cfg.api_key === '***') setNeedsConfig(true)
    })
  }, [])

  useEffect(() => {
    if (needsConfig) setShowSettings(true)
  }, [needsConfig])

  const handleDownloadBOM = () => {
    if (!bom.length) return
    const csv = ['lib_id,reference,value,quantity,notes', ...bom.map(b => `${b.lib_id},${b.reference},${b.value},${b.quantity},${b.notes ?? ''}`)].join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = 'bom.csv'
    a.click()
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', fontFamily: 'system-ui, sans-serif' }}>
      {/* Header */}
      <div style={{ padding: '10px 16px', borderBottom: '1px solid #e5e7eb', display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'white' }}>
        <div style={{ fontWeight: 700, fontSize: 16 }}>⚡ EDA-AI-Agent</div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <button onClick={newSession} style={{ fontSize: 12, padding: '4px 10px', borderRadius: 6, border: '1px solid #d1d5db', background: 'white', cursor: 'pointer' }}>
            New Session
          </button>
          <button onClick={() => setShowSettings(true)} style={{ fontSize: 20, background: 'none', border: 'none', cursor: 'pointer', color: '#6b7280' }} title="Settings">
            ⚙
          </button>
        </div>
      </div>

      {/* Two-panel body */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* Chat — 40% */}
        <div style={{ width: '40%', borderRight: '1px solid #e5e7eb', overflow: 'hidden' }}>
          <ChatPanel messages={messages} stage={stage} connected={connected} onSend={sendMessage} />
        </div>

        {/* Schematic — 60% */}
        <div style={{ flex: 1, overflow: 'hidden' }}>
          <SchematicViewer
            schematicContent={schematicContent}
            bom={bom}
            ercReport={ercReport}
            sessionId={sessionId}
            onDownloadSchematic={() => sessionId && downloadSchematic(sessionId)}
            onDownloadBOM={handleDownloadBOM}
          />
        </div>
      </div>

      {showSettings && <SettingsModal onClose={() => { setShowSettings(false); setNeedsConfig(false) }} />}
    </div>
  )
}
```

- [ ] **Step 3: Build frontend to check for TypeScript errors**

```bash
cd frontend && npm run build
```

Expected: `built in Xs` with no TypeScript errors. Fix any type errors before proceeding.

- [ ] **Step 4: Start both servers**

In terminal 1:
```bash
source .venv/bin/activate && uvicorn backend.main:app --reload --port 8000
```

In terminal 2:
```bash
cd frontend && npm run dev
```

- [ ] **Step 5: Smoke test in browser**

1. Open http://localhost:5173
2. Confirm Settings modal appears (no API key set)
3. Enter your LiteLLM model string and API key, click Save
4. Confirm main layout appears: chat left, schematic right
5. Type "I want to build a 5V LED blinker circuit" and press Enter
6. Confirm agent starts streaming requirements questions
7. Answer 2–3 questions
8. Confirm stage bar advances through Requirements → Design → Generation → Validation
9. Confirm `.kicad_sch` download button becomes active
10. Click download — confirm file opens in KiCad (if installed)

- [ ] **Step 6: Run full test suite**

```bash
pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 7: Final commit**

```bash
git add frontend/src/App.tsx frontend/src/main.tsx
git commit -m "feat: App integration — two-panel layout, settings gate, new-session, BOM CSV download"
```

---

## Self-Review Checklist

**Spec coverage:**

| Spec section | Implemented in |
|---|---|
| FastAPI + WebSocket | Task 14 |
| LiteLLM any-provider | Task 8 (BaseAgent) |
| Config ~/.eda-agent/config.json | Task 2 |
| Component DB (bundled SQLite) | Task 3 |
| User KiCad lib scanner | Task 5 |
| Req Agent (ask_user pause) | Task 10 |
| Design Agent (DB-constrained) | Task 11 |
| KiCad Gen Agent | Task 12 |
| Validation Agent (ERC) | Task 13 |
| Orchestrator (3 retry loops) | Task 9 |
| React frontend scaffolding | Task 15 |
| WebSocket hook + token streaming | Task 16 |
| ChatPanel + stage bar | Task 17 |
| KiCanvas schematic viewer | Task 18 |
| Settings modal | Task 19 |
| App integration + smoke test | Task 20 |
| Error: KiCad not found → skip ERC | Task 13 (KiCadNotFoundError) |
| Error: no API key → show settings | Task 20 (needsConfig gate) |

All spec requirements covered. No TBD/TODO placeholders. Types consistent across tasks (`PipelineStage`, `SessionState`, `ERCResult`, `BOMItem` defined once and reused).
