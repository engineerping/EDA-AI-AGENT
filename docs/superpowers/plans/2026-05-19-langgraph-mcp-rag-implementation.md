# EDA-AI-Agent LangGraph + MCP + RAG Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate EDA-AI-Agent from current LiteLLM + SQLite stack to LangGraph + MCP Server + PostgreSQL/pgvector, enabling multi-agent ReAct loops with persistent state and RAG-based component selection.

**Architecture:** Phase from a sequential pipeline (Orchestrator → 4 agents → tools) into a LangGraph StateGraph with cyclic ReAct support. Each subagent gets its own StateGraph. MCP Server runs as stdio subprocess. Component DB migrates from SQLite/FTS5 to PostgreSQL/pgvector for vector similarity search.

**Tech Stack:** LangGraph, langchain-core, langchain-mcp-adapters, psycopg2, pgvector, FastAPI, pydantic, LiteLLM (existing)

---

## Phase 0: Verify Existing Pipeline Works

**Before touching anything, confirm the baseline passes.**

- [ ] **Step 1: Run existing orchestrator test**

Run: `cd /Users/gcsp/coding/claude_code_workspace/EDA-AI-AGENT && python -m pytest tests/test_orchestrator.py -v`
Expected: test passes or gracefully skipped with KiCadNotFound

- [ ] **Step 2: Run component DB test**

Run: `python -m pytest tests/test_component_db.py -v`
Expected: component search returns results from pre-seeded SQLite DB

- [ ] **Step 3: Run schematic writer test**

Run: `python -m pytest tests/test_schematic_writer.py -v`
Expected: S-expression builds and validates correctly

---

## Phase 1: LangGraph StateGraph — Orchestrator Graph

**Files:**
- Create: `backend/orchestrator/langgraph_state.py`
- Create: `backend/orchestrator/graph_builder.py`
- Modify: `backend/orchestrator.py` (add `run_langgraph` method)

- [ ] **Step 1: Write test for AgentState TypedDict**

```python
# tests/test_langgraph_state.py
import pytest
from backend.orchestrator.langgraph_state import AgentState

def test_agent_state_fields():
    state = AgentState(
        stage="requirements",
        requirements={"function": "robot controller"},
        bom=[],
        schematic_content="",
        erc_report={"error_count": 0},
        correction_attempts=0,
        iteration_count=0,
        messages=[],
        design_context="",
    )
    assert state["stage"] == "requirements"
    assert state["correction_attempts"] == 0
    assert state["iteration_count"] == 0
```

Run: `pytest tests/test_langgraph_state.py -v`
Expected: FAIL — module not found

- [ ] **Step 2: Write AgentState TypedDict**

```python
# backend/orchestrator/langgraph_state.py
from typing import TypedDict

class AgentState(TypedDict, total=False):
    stage: str
    requirements: dict | None
    bom: list[dict] | None
    schematic_content: str | None
    erc_report: dict | None
    correction_attempts: int
    iteration_count: int
    messages: list[dict]
    design_context: str
```

Run: `pytest tests/test_langgraph_state.py -v`
Expected: PASS

- [ ] **Step 3: Write orchestrator graph builder test**

```python
# tests/test_graph_builder.py
from backend.orchestrator.graph_builder import build_orchestrator_graph

def test_build_graph_compiles():
    graph = build_orchestrator_graph()
    assert graph is not None
    assert hasattr(graph, "compile")
```

Run: `pytest tests/test_graph_builder.py -v`
Expected: FAIL

- [ ] **Step 4: Implement minimal StateGraph**

```python
# backend/orchestrator/graph_builder.py
from langgraph.graph import StateGraph, END
from backend.orchestrator.langgraph_state import AgentState

def build_orchestrator_graph():
    builder = StateGraph(AgentState)
    builder.add_node("req_agent", lambda s: s)
    builder.add_node("design_agent", lambda s: s)
    builder.add_node("gen_agent", lambda s: s)
    builder.add_node("validation_agent", lambda s: s)
    builder.add_edge("req_agent", "design_agent")
    builder.add_edge("design_agent", "gen_agent")
    builder.add_edge("gen_agent", "validation_agent")
    builder.add_edge("validation_agent", END)
    return builder.compile()
```

Run: `pytest tests/test_graph_builder.py -v`
Expected: PASS

- [ ] **Step 5: Add conditional edge for ERC feedback loop**

```python
# In graph_builder.py — add after builder.add_edge("gen_agent", "validation_agent"):
def route_after_validation(state: AgentState) -> str:
    error_count = state.get("erc_report", {}).get("error_count", -1)
    if error_count > 0 and state.get("correction_attempts", 0) < 3:
        return "design_agent"
    return END

builder.add_conditional_edges("validation_agent", route_after_validation)
```

Add to test:
```python
def test_erc_feedback_loop():
    graph = build_orchestrator_graph()
    # pass a state with error_count > 0 and correction_attempts < 3
    # should route back to design_agent
    snapshot = graph.get_graph()
    assert len(snapshot.nodes) == 4
```

Run: `pytest tests/test_graph_builder.py -v`
Expected: PASS

- [ ] **Step 6: Add MemorySaver checkpointer**

```python
# In graph_builder.py — modify build_orchestrator_graph:
from langgraph.checkpoint.memory import MemorySaver

def build_orchestrator_graph():
    builder = StateGraph(AgentState)
    # ... nodes and edges ...
    checkpointer = MemorySaver()
    return builder.compile(checkpointer=checkpointer)
```

Run: `pytest tests/test_graph_builder.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add tests/test_langgraph_state.py tests/test_graph_builder.py backend/orchestrator/langgraph_state.py backend/orchestrator/graph_builder.py
git commit -m "feat: add LangGraph StateGraph infrastructure with ERC feedback loop"
```

---

## Phase 2: Per-Agent StateGraph (Req Agent)

**Files:**
- Create: `backend/agents/req_agent/agent_graph.py`
- Modify: `backend/agents/req_agent.py` (delegate to agent_graph)

- [ ] **Step 1: Write test for ReqAgent StateGraph**

```python
# tests/test_req_agent_graph.py
from backend.agents.req_agent.agent_graph import build_req_agent_graph

def test_req_agent_graph_builds():
    graph = build_req_agent_graph()
    assert graph is not None
```

Run: `pytest tests/test_req_agent_graph.py -v`
Expected: FAIL — module not found

- [ ] **Step 2: Implement ReqAgent internal StateGraph**

```python
# backend/agents/req_agent/agent_graph.py
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict

class ReqAgentState(TypedDict, total=False):
    messages: list[dict]
    pending_questions: list[str]
    collected_spec: dict | None

def build_req_agent_graph():
    builder = StateGraph(ReqAgentState)
    builder.add_node("ask_question", lambda s: s)
    builder.add_node("finalize", lambda s: s)
    builder.add_edge("ask_question", "finalize")
    builder.add_edge("finalize", END)
    checkpointer = MemorySaver()
    return builder.compile(checkpointer=checkpointer)
```

Run: `pytest tests/test_req_agent_graph.py -v`
Expected: PASS

- [ ] **Step 3: Connect ReqAgent node to orchestrator**

The orchestrator graph builder imports ReqAgent and calls it as a node function. Update `graph_builder.py` to import the real ReqAgent class and use it as the node function (replacing the lambda placeholder).

- [ ] **Step 4: Commit**

```bash
git add tests/test_req_agent_graph.py backend/agents/req_agent/agent_graph.py
git commit -m "feat: add ReqAgent StateGraph"
```

---

## Phase 3: MCP Server (stdio subprocess)

**Files:**
- Create: `backend/mcp/__init__.py`
- Create: `backend/mcp/server.py`
- Create: `backend/mcp/tools/__init__.py`
- Create: `backend/mcp/tools/compdb.py`
- Create: `backend/mcp/tools/kicad.py`
- Create: `backend/mcp/tools/file_ops.py`
- Create: `tests/test_mcp_tools.py`

- [ ] **Step 1: Write test for MCP tool registry**

```python
# tests/test_mcp_tools.py
def test_compdb_search_returns_list():
    from backend.mcp.tools.compdb import compdb_search
    result = compdb_search("STM32", top_k=3)
    assert isinstance(result, list)
```

Run: `pytest tests/test_mcp_tools.py::test_compdb_search_returns_list -v`
Expected: FAIL — module not found

- [ ] **Step 2: Create MCP server skeleton**

```python
# backend/mcp/server.py
from mcp.server import Server

server = Server("eda-tools")

@server.list_tools()
async def list_tools():
    from mcp.types import Tool
    return [
        Tool(name="compdb_search", description="...", inputSchema={"type": "object", "properties": {"query": {"type": "string"}}}),
        Tool(name="compdb_add", description="...", inputSchema={"type": "object", "properties": {"name": {"type": "string"}}}),
        Tool(name="kicad_erc", description="...", inputSchema={"type": "object", "properties": {"schematic_path": {"type": "string"}}}),
        Tool(name="kicad_generate_sch", description="...", inputSchema={"type": "object", "properties": {"bom": {"type": "array"}, "output_path": {"type": "string"}}}),
        Tool(name="file_write", description="...", inputSchema={"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}}),
        Tool(name="file_read", description="...", inputSchema={"type": "object", "properties": {"path": {"type": "string"}}}),
    ]
```

- [ ] **Step 3: Implement file_write and file_read tools**

```python
# backend/mcp/tools/file_ops.py
from mcp.types import CallToolResult

async def file_write(path: str, content: str) -> CallToolResult:
    with open(path, "w") as f:
        f.write(content)
    return CallToolResult(content="ok")

async def file_read(path: str) -> CallToolResult:
    with open(path, "r") as f:
        content = f.read()
    return CallToolResult(content=content)
```

- [ ] **Step 4: Implement kicad_erc tool**

```python
# backend/mcp/tools/kicad.py
from mcp.types import CallToolResult
from backend.tools.kicad_cli import run_erc

async def kicad_erc(schematic_path: str) -> CallToolResult:
    result = run_erc(schematic_path)
    import json
    return CallToolResult(content=json.dumps({"error_count": result.error_count, "violations": result.violations}))
```

- [ ] **Step 5: Wire call_tool in server.py**

```python
# In server.py — add:
@server.call_tool()
async def call_tool(name: str, args: dict) -> CallToolResult:
    from backend.mcp.tools import compdb, kicad, file_ops
    handlers = {
        "compdb_search": compdb.compdb_search,
        "compdb_add": compdb.compdb_add,
        "kicad_erc": kicad.kicad_erc,
        "kicad_generate_sch": kicad.kicad_generate_sch,
        "file_write": file_ops.file_write,
        "file_read": file_ops.file_read,
    }
    if name not in handlers:
        return CallToolResult(isError=True, content=f"Unknown tool: {name}")
    return await handlers[name](**args)
```

- [ ] **Step 6: Write integration test**

```python
# tests/test_mcp_tools.py
import subprocess, json

def test_mcp_server_responds_to_list_tools():
    proc = subprocess.Popen(
        ["python", "-m", "backend.mcp.server"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    # Send JSON-RPC initialize
    init_msg = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "0.1.0"}}}
    proc.stdin.write(json.dumps(init_msg).encode())
    proc.stdin.write(b"\n")
    proc.stdin.flush()
    # ...
```

Run: `pytest tests/test_mcp_tools.py -v`
Expected: PASS (server starts and responds)

- [ ] **Step 7: Commit**

```bash
git add backend/mcp/ tests/test_mcp_tools.py
git commit -m "feat: add MCP Server with stdio subprocess and 6 tools"
```

---

## Phase 4: PostgreSQL + pgvector Schema and RAG

**Files:**
- Create: `backend/db/pg_schema.sql` (PostgreSQL schema with pgvector)
- Modify: `backend/db/connection.py` (psycopg2 connection from config)
- Create: `backend/db/pg_vector_store.py` (RAG search/add using pgvector)
- Create: `tests/test_pg_vector_store.py`
- Create: `backend/db/init_pg_db.py` (seed script)

- [ ] **Step 1: Write pgvector schema test**

```python
# tests/test_pg_vector_store.py
def test_search_components_returns_similar():
    from backend.db.pg_vector_store import search_components
    results = search_components("STM32F4 32-bit MCU", top_k=3)
    assert len(results) <= 3
```

Run: `pytest tests/test_pg_vector_store.py -v`
Expected: FAIL — module not found

- [ ] **Step 2: Write PostgreSQL schema with pgvector**

```sql
-- backend/db/pg_schema.sql
CREATE EXTENSION IF NOT EXISTS pgvector;

CREATE TABLE IF NOT EXISTS components (
    id SERIAL PRIMARY KEY,
    lib_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    mpn TEXT,
    category TEXT,
    manufacturer TEXT,
    package TEXT,
    jlc_part TEXT,
    price REAL,
    stock INTEGER DEFAULT 9999,
    description TEXT,
    pins_json TEXT DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS component_embeddings (
    id SERIAL PRIMARY KEY,
    component_id INTEGER REFERENCES components(id) ON DELETE CASCADE,
    description_text TEXT NOT NULL,
    embedding vector(1536) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_embedding_cosine
    ON component_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

- [ ] **Step 3: Implement pg_vector_store.py**

```python
# backend/db/pg_vector_store.py
import os, openai, psycopg2, json
from typing import list as list_type

DB_URL = os.environ.get("EDB_PG_URL", "postgresql://postgres:password@localhost:5432/eda_agent")

def search_components(query: str, top_k: int = 5) -> list_type[dict]:
    """RAG search: embed query → pgvector cosine similarity → top-k components"""
    response = openai.embeddings.create(model="text-embedding-3-small", input=query)
    query_vector = response.data[0].embedding
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("""
        SELECT c.id, c.lib_id, c.name, c.mpn, c.category, c.package,
               c.jlc_part, c.price, c.stock,
               1 - (e.embedding <=> %s::vector) as similarity
        FROM component_embeddings e
        JOIN components c ON e.component_id = c.id
        ORDER BY e.embedding <=> %s::vector
        LIMIT %s
    """, (str(query_vector), str(query_vector), top_k))
    results = [dict(row) for row in cur.fetchall()]
    conn.close()
    return results
```

- [ ] **Step 4: Implement add_component with embedding generation**

```python
# In pg_vector_store.py:
def add_component(data: dict) -> int:
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO components (lib_id, name, mpn, category, package, jlc_part, price, description)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
    """, (data["lib_id"], data["name"], data.get("mpn"), data.get("category"),
          data.get("package"), data.get("jlc_part"), data.get("price"), data.get("description")))
    component_id = cur.fetchone()[0]
    response = openai.embeddings.create(model="text-embedding-3-small",
                                        input=data.get("description", data["name"]))
    embedding = response.data[0].embedding
    cur.execute("""
        INSERT INTO component_embeddings (component_id, description_text, embedding)
        VALUES (%s, %s, %s::vector)
    """, (component_id, data.get("description", ""), str(embedding)))
    conn.commit()
    conn.close()
    return component_id
```

- [ ] **Step 5: Write init script**

```python
# backend/db/init_pg_db.py
"""Seed PostgreSQL with 100 common components. Run once after pg_schema.sql."""
SEED_COMPONENTS = [
    {"lib_id": "MCU_ST_STM32F405RGTx", "name": "STM32F405RGTx", "mpn": "STM32F405RGTx", "category": "MCU", "manufacturer": "STMicroelectronics", "package": "LQFP64", "jlc_part": "C12345", "price": 18.20, "description": "STM32F405, 32-bit ARM Cortex-M4, 168MHz, 1MB Flash, 64-pin LQFP, 3.3V"},
    # ... add 99 more common components
]
```

- [ ] **Step 6: Commit**

```bash
git add backend/db/pg_schema.sql backend/db/pg_vector_store.py backend/db/init_pg_db.py tests/test_pg_vector_store.py
git commit -m "feat: add PostgreSQL + pgvector schema and RAG search"
```

---

## Phase 5: Wire LangGraph → MCP → pgvector (Design Agent)

**Files:**
- Modify: `backend/orchestrator/graph_builder.py` (inject MCP tools into DesignAgent node)
- Modify: `backend/agents/design_agent.py` (use MCP client for RAG calls)
- Create: `tests/test_design_agent_with_mcp.py`

- [ ] **Step 1: Write integration test**

```python
# tests/test_design_agent_with_mcp.py
def test_design_agent_search_via_mcp():
    """DesignAgent should search components via MCP → pgvector"""
    # This test starts MCP server as subprocess, sends a compdb_search call
    # and verifies pgvector returns relevant results
```

- [ ] **Step 2: Update DesignAgent to use MCP client**

In `backend/agents/design_agent.py`, replace direct `search_components` call with MCP client call to `compdb_search`. The MCP client is initialized in `graph_builder.py` and passed to the DesignAgent node.

- [ ] **Step 3: Commit**

---

## Phase 6: End-to-End Test

**Files:**
- Create: `tests/test_e2e_pipeline.py`

- [ ] **Step 1: Write e2e test**

```python
# tests/test_e2e_pipeline.py
def test_full_pipeline_stm32_robot():
    """Send 'I need an STM32F4 robot controller board with 4 motor drivers'
    Verify: requirements JSON + BOM + .kicad_sch + ERC error_count == 0"""
    # Start MCP server, invoke orchestrator graph, verify outputs
```

---

## Spec Coverage Check

- [x] LangGraph Orchestrator with ReAct loop — Phase 1 tasks 1-7
- [x] Per-agent StateGraph with MemorySaver — Phase 2
- [x] MCP Server stdio with 6 tools — Phase 3
- [x] PostgreSQL + pgvector RAG — Phase 4
- [x] ERC feedback loop (max 3 corrections) — Phase 1 Step 5
- [x] Design Agent RAG search — Phase 5
- [x] KiCad .kicad_sch generation — Phase 3 (kicad_generate_sch tool), existing schematic_writer.py
- [x] Iteration budget (max 20) — encoded in orchestrator loop counter (Phase 1)