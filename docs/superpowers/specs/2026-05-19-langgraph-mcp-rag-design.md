# EDA-AI-Agent — LangGraph + MCP + RAG 架构设计

**日期**: 2026-05-19
**版本**: v2.0
**状态**: 设计中

---

## 一、架构总览

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                    User (Chat)                                      │
│                         "我要一个 STM32F4 的机器人主控板"                              │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         Orchestrator StateGraph (LangGraph)                         │
│   ┌─────────────────────────────────────────────────────────────────────────────┐  │
│   │  ReAct Loop:  Thought → Action → Observation → 循环直到 ERC 通过                 │  │
│   │  State: {stage, requirements, bom, schematic_content, erc_errors, budget}     │  │
│   │  MemorySaver checkpointer — 跨迭代持久化状态                                    │  │
│   └─────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                     │
│   路由决策：                                                                       │
│     requirements stage  → Req Agent                                                 │
│     design stage        → Design Agent (+ RAG 查询)                                │
│     generation stage   → KiCad Gen Agent                                           │
│     validation stage   → Validation Agent                                          │
│     ERC 有错误         → 回到 design stage（最多 3 次修正）                            │
└──────────────────┬──────────────────────────────────────────┬──────────────────────┘
                   │                                          │
          ┌────────▼────────┐        ┌────────▼────────┐      ┌────────▼────────┐
          │   Req Agent     │        │  Design Agent   │      │  Validation     │
          │  (StateGraph)   │        │  (StateGraph)   │      │  Agent          │
          │  MemorySaver    │        │  MemorySaver    │      │  (StateGraph)   │
          │  + MCP Client   │        │  + MCP Client   │      │  + MCP Client   │
          └────────┬────────┘        └────────┬────────┘      └────────┬────────┘
                   │                          │                          │
          ┌────────▼──────────────────────────▼──────────────────────────▼────────┐
          │                     MCP Server (stdio 子进程)                          │
          │  ─────────────────────────────────────────────────────────────────── │
          │  工具清单：                                                             │
          │    compdb_search(query)  → pgvector 相似度检索                          │
          │    compdb_add(data)       → 写入 PostgreSQL + 生成 embedding                │
          │    kicad_erc(sch_path)   → KiCad CLI ERC 检查                          │
          │    kicad_generate_sch(bom) → 生成 .kicad_sch 文本                       │
          │    file_write(path, content)                                          │
          │    file_read(path)                                                     │
          └─────────────────────────────────┬────────────────────────────────────┘
                                            │
                    ┌───────────────────────┼───────────────────────┐
                    │                       │                       │
          ┌─────────▼─────────┐   ┌─────────▼─────────┐   ┌────────▼────────┐
          │  PostgreSQL +     │   │    KiCad CLI     │   │   文件系统       │
          │  pgvector (RDS)  │   │  (ERC / DRC)     │   │   (.kicad_sch)  │
          │  ─────────────── │   │                  │   │                 │
          │  components 表   │   │  kicad-cli sch   │   │   输出目录        │
          │  component_      │   │    erc           │   │                 │
          │    embeddings 表 │   │                  │   │                 │
          │  (pgvector 向量) │   │                  │   │                 │
          └───────────────────┘   └───────────────────┘   └─────────────────┘
```

---

## 二、LangGraph 集成详解

### 2.1 Orchestrator StateGraph（主循环）

```python
from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import MemorySaver

# 全局状态定义
class AgentState(TypedDict):
    stage: str                          # "requirements" | "design" | "generation" | "validation" | "done"
    requirements: dict                   # 需求文档
    bom: list[dict]                     # BOM 列表
    schematic_content: str              # .kicad_sch 文本
    erc_report: dict                   # ERC 检查结果
    correction_attempts: int           # ERC 修正次数（上限 3）
    iteration_count: int                # 总迭代次数（上限 20）
    messages: list[dict]                # 对话历史
    design_context: str                 # 设计上下文（含 RAG 检索结果）

# 构建主图
builder = StateGraph(AgentState)
builder.add_node("req_agent", req_agent_node)
builder.add_node("design_agent", design_agent_node)
builder.add_node("gen_agent", gen_agent_node)
builder.add_node("validation_agent", validation_agent_node)

# 边路由规则
def route(state: AgentState) -> str:
    if state["stage"] == "requirements": return "req_agent"
    if state["stage"] == "design": return "design_agent"
    if state["stage"] == "generation": return "gen_agent"
    if state["stage"] == "validation": return "validation_agent"
    if state["stage"] == "done": return END

builder.add_edge("req_agent", "design_agent")
builder.add_edge("design_agent", "gen_agent")
builder.add_edge("gen_agent", "validation_agent")

# ERC 失败 → 回退到 design（最多 3 次）
def route_after_validation(state: AgentState) -> str:
    if state["erc_report"].get("error_count", -1) > 0:
        if state["correction_attempts"] < 3:
            return "design_agent"  # 循环回去修正
    return "done"

builder.add_conditional_edges("validation_agent", route_after_validation)

# 持久化 checkpoint
checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)
```

### 2.2 Subagent StateGraph（独立子图）

每个 Subagent 有自己的 `StateGraph` + `MemorySaver`，独立维护内部状态：

```python
# Design Agent 内部结构
design_builder = StateGraph(DesignSubState)

# 内部 ReAct 循环
design_builder.add_node("think", design_think_node)      # 分析需求，决定查询哪些元件
design_builder.add_node("action", design_action_node)     # 调用 MCP 工具（compdb_search）
design_builder.add_node("observe", design_observe_node)    # 处理检索结果

design_builder.add_edge("think", "action")
design_builder.add_edge("action", "observe")
design_builder.add_conditional_edges("observe", lambda s: "think" if s["needs_more_info"] else "generate_bom")

design_checkpointer = MemorySaver()
design_graph = design_builder.compile(checkpointer=design_checkpointer)
```

**为什么每个 Subagent 独立 StateGraph**：

- 各 Subagent 可独立调试、独立测试
- 状态隔离，内存占用可控
- 符合"麻雀虽小，五脏俱全"的生产级架构

### 2.3 状态传递流程

```
Orchestrator State (主图)
  ├── stage: "design"
  ├── requirements: {...}
  └── messages: [...]
          │
          │  调用 Subagent 时传递完整 state
          ▼
Design Agent StateGraph (子图)
  ├── 接收到 context = orchestrator_state
  ├── 内部 ReAct 循环：think → action（MCP调用）→ observe
  ├── RAG 查询结果写入 design_context
  └── 返回 bom + design_context 给 Orchestrator
          │
          │  Orchestrator 更新主 state
          ▼
Orchestrator State (更新后)
  ├── stage: "generation"
  ├── bom: [...]
  └── design_context: "推荐 STM32F405RGTx，因为..."
```

---

## 三、MCP Server 架构

### 3.1 进程模型

```
┌─────────────────────────────────┐
│   Main Process (FastAPI/Web)   │
│                                 │
│  ┌─────────────────────────┐   │
│  │  MCP Client (LangGraph) │   │
│  │  stdio 通信              │   │
│  └────────────┬────────────┘   │
└───────────────┼────────────────┘
                │ stdio (stdin/stdout)
    ┌───────────▼──────────────┐
    │    MCP Server (子进程)     │
    │  ───────────────────────  │
    │  Server("eda-tools")      │
    │    ├── list_tools()       │
    │    ├── call_tool(name,   │
    │    │       args)          │
    │    └── 工具注册表          │
    └───────────┬──────────────┘
                │
    ┌───────────┼───────────────┐
    │           │               │
    ▼           ▼               ▼
 compdb_    kicad_        file_
 search     erc          write
```

### 3.2 工具定义

```python
# mcp_server.py

from mcp.server import Server
from mcp.types import Tool, CallToolResult

server = Server("eda-tools")

# ─────────────────────────────────────────────────────────────
# 工具清单（每个工具都是一个 async 函数）
# ─────────────────────────────────────────────────────────────

async def compdb_search(query: str, top_k: int = 5) -> CallToolResult:
    """
    RAG 检索：查询元件数据库
    - 输入: query (自然语言，如 "STM32F4 32-bit MCU")
    - 过程: Embedding → pgvector 相似度检索
    - 输出: Top-K 匹配的元件列表（含型号/封装/价格/JLC编号）
    """
    from backend.db.vector_store import search_components
    results = await search_components(query, top_k=top_k)
    return {"tools": results}

async def compdb_add(component_data: dict) -> CallToolResult:
    """
    添加元件到数据库（用于扩展 Component DB）
    - 输入: {name, category, package, jlc_part, price, description}
    - 过程: 生成 embedding → 写入 SQLite + pgvector
    - 输出: 确认信息
    """
    from backend.db.vector_store import add_component
    result = await add_component(component_data)
    return {"status": "ok", "id": result}

async def kicad_erc(schematic_path: str) -> CallToolResult:
    """
    调用 KiCad CLI 执行 ERC 检查
    - 输入: .kicad_sch 文件路径
    - 过程: subprocess 调用 kicad-cli sch erc
    - 输出: ERC 报告（JSON 格式，含 error_count 和错误列表）
    """
    from backend.tools.kicad_cli import run_erc
    report = await run_erc(schematic_path)
    return report

async def kicad_generate_sch(bom: list[dict], output_path: str) -> CallToolResult:
    """
    生成 KiCad 原理图文件
    - 输入: BOM 列表 + 输出路径
    - 过程: 字符串模板生成 S-expression 格式 .kicad_sch
    - 输出: 文件写入确认
    """
    from backend.tools.sch_generator import generate_schematic
    content = generate_schematic(bom)
    with open(output_path, "w") as f:
        f.write(content)
    return {"status": "ok", "path": output_path, "size": len(content)}

async def file_write(path: str, content: str) -> CallToolResult:
    """写文件工具"""
    with open(path, "w") as f:
        f.write(content)
    return {"status": "ok", "path": path}

async def file_read(path: str) -> CallToolResult:
    """读文件工具"""
    with open(path, "r") as f:
        content = f.read()
    return {"content": content}

# ─────────────────────────────────────────────────────────────
# MCP Server 注册
# ─────────────────────────────────────────────────────────────

@server.list_tools()
async def list_tools() -> list[Tool]:
    """返回所有可用工具的 schema（MCP 协议要求）"""
    return [
        Tool(
            name="compdb_search",
            description="搜索电子元件数据库，支持自然语言查询，返回匹配的元件型号/封装/价格/JLC编号",
            inputSchema={"type": "object", "properties": {"query": {"type": "string"}, "top_k": {"type": "integer"}}}
        ),
        Tool(
            name="compdb_add",
            description="向元件数据库添加新元件（需提供完整参数）",
            inputSchema={"type": "object", "properties": {"name": {}, "category": {}, "package": {}, "jlc_part": {}, "price": {}, "description": {}}}
        ),
        Tool(
            name="kicad_erc",
            description="对 KiCad 原理图执行电气规则检查（ERC），返回错误列表和修复建议",
            inputSchema={"type": "object", "properties": {"schematic_path": {"type": "string"}}}
        ),
        Tool(
            name="kicad_generate_sch",
            description="根据 BOM 生成 KiCad .kicad_sch 原理图文件（S-expression 格式）",
            inputSchema={"type": "object", "properties": {"bom": {"type": "array"}, "output_path": {"type": "string"}}}
        ),
        Tool(
            name="file_write",
            description="写入文本文件",
            inputSchema={"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}}
        ),
        Tool(
            name="file_read",
            description="读取文本文件",
            inputSchema={"type": "object", "properties": {"path": {"type": "string"}}}
        ),
    ]

@server.call_tool()
async def call_tool(name: str, args: dict) -> CallToolResult:
    """工具调用入口（MCP Client 发来的请求在这里处理）"""
    handlers = {
        "compdb_search": compdb_search,
        "compdb_add": compdb_add,
        "kicad_erc": kicad_erc,
        "kicad_generate_sch": kicad_generate_sch,
        "file_write": file_write,
        "file_read": file_read,
    }
    if name not in handlers:
        return {"error": f"Unknown tool: {name}"}
    return await handlers[name](**args)
```

### 3.3 与 LangGraph 的连接

```python
# backend/orchestrator/langgraph_setup.py

from langgraph.prebuilt import ToolNode
from langchain_mcp_adapters.client import MCPClient

# 启动 MCP Server 作为子进程
import subprocess

mcp_process = subprocess.Popen(
    ["python", "-m", "backend.mcp.server"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)

# MCP Client 连接
mcp_client = MCPClient(stdio_process=mcp_process)

# 将 MCP 工具绑定到 LangGraph node
tools = mcp_client.get_tools()

# 每个 Subagent 的 node 使用这些 tools
design_agent_node = ToolNode(tools)  # tools 自动路由到 MCP Server
```

---

## 四、RAG + SQLite/pgvector 详解

### 4.1 数据库架构

```sql
-- 文件：backend/db/component_db.sqlite (SQLite + pgvector)

-- 元件基础信息表
CREATE TABLE components (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,              -- "STM32F405RGTx"
    mpn TEXT,                         -- 制造商型号 "STM32F405RGTx"
    category TEXT,                    -- "MCU" | "POWER" | "DRIVER" | "SENSOR"
    manufacturer TEXT,                -- "STMicroelectronics"
    package TEXT,                     -- "LQFP64"
    jlc_part TEXT,                    -- "C12345"（嘉立创 SMT 编号）
    price REAL,                       -- 18.20
    stock INTEGER DEFAULT 9999,
    description TEXT,                 -- 原始描述文本（用于生成 embedding）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 向量嵌入表（pgvector）
CREATE TABLE component_embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    component_id INTEGER REFERENCES components(id) ON DELETE CASCADE,
    description_text TEXT NOT NULL,   -- "STM32F405, 32-bit ARM Cortex-M4, 168MHz, 1MB Flash, 64-pin LQFP, 3.3V"
    embedding vector(1536) NOT NULL,  -- OpenAI text-embedding-3-small: 1536 维
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 向量相似度检索（pgvector 索引）
CREATE INDEX idx_embedding_cosine ON component_embeddings 
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- 全文搜索辅助索引（SQLite FTS5）
CREATE VIRTUAL TABLE components_fts USING fts5(
    name, mpn, category, description,
    content='components',
    content_rowid='id'
);
```

### 4.2 RAG 检索流程

```python
# backend/db/vector_store.py

import openai
import psycopg2
import json

DB_URL = "postgresql://user:pass@your-rds-host:5432/eda_agent"

async def search_components(query: str, top_k: int = 5) -> list[dict]:
    """
    RAG 检索流程：
    1. 用户 query → Embedding 模型编码为向量
    2. pgvector 余弦相似度检索 Top-K
    3. 返回匹配元件的完整信息
    """
    # Step 1: Embedding
    response = openai.embeddings.create(
        model="text-embedding-3-small",
        input=query
    )
    query_vector = response.data[0].embedding  # list[1536]

    # Step 2: 向量检索（pgvector 余弦相似度）
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.id, c.name, c.mpn, c.category, c.package,
               c.jlc_part, c.price, c.stock,
               1 - (e.embedding <=> %s::vector) as similarity
        FROM component_embeddings e
        JOIN components c ON e.component_id = c.id
        ORDER BY e.embedding <=> %s::vector
        LIMIT %s
    """, (str(query_vector), str(query_vector), top_k))

    results = []
    for row in cursor.fetchall():
        results.append({
            "id": row[0],
            "name": row[1],
            "mpn": row[2],
            "category": row[3],
            "package": row[4],
            "jlc_part": row[5],
            "price": row[6],
            "stock": row[7],
            "similarity": row[8]
        })

    conn.close()
    return results

async def add_component(data: dict) -> int:
    """
    添加元件到数据库：
    1. 写入 components 表
    2. 生成 description 的 embedding
    3. 写入 component_embeddings 表
    """
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()

    # 写入基础信息
    cursor.execute("""
        INSERT INTO components (name, mpn, category, package, jlc_part, price, description)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (data["name"], data["mpn"], data["category"], data["package"],
          data.get("jlc_part"), data.get("price"), data.get("description")))

    component_id = cursor.fetchone()[0]

    # 生成 embedding
    response = openai.embeddings.create(
        model="text-embedding-3-small",
        input=data.get("description", data["name"])
    )
    embedding = response.data[0].embedding

    # 写入向量（pgvector 需要 ::vector 强制类型转换）
    cursor.execute("""
        INSERT INTO component_embeddings (component_id, description_text, embedding)
        VALUES (%s, %s, %s::vector)
    """, (component_id, data.get("description", ""), str(embedding)))

    conn.commit()
    conn.close()
    return component_id
```

### 4.3 Embedding 与 RAG 在 Agent 中的使用

```python
# Design Agent 调用 RAG 示例

async def design_think_node(state: DesignSubState):
    """Design Agent 的 Think 节点：分析需求，决定是否需要 RAG 查询"""
    requirements_text = state["requirements_text"]

    # 让 LLM 判断：需要查哪些类型的元件
    decision_prompt = f"""
    根据以下需求，分析需要查询哪些元件：
    {requirements_text}

    输出格式：
    - 元件类型（如：MCU、电源IC、电机驱动）
    - 查询关键词（如："STM32F4 MCU", "5V to 3.3V LDO"）
    """
    response = llm.invoke(decision_prompt)
    query_plan = json.loads(response.content)

    return {"query_plan": query_plan, "needs_rag": True}
```

---

## 五、文件结构

```
EDA-AI-AGENT/
├── backend/
│   ├── __init__.py
│   ├── config.py                    # 配置（API key、路径等）
│   ├── main.py                      # FastAPI 入口
│   │
│   ├── orchestrator/
│   │   ├── __init__.py
│   │   ├── state.py                 # AgentState / DesignSubState 定义
│   │   ├── orchestrator_graph.py    # Orchestrator StateGraph 构建
│   │   └── nodes.py                 # 各节点实现（req_agent_node 等）
│   │
│   ├── agents/                      # 各 Subagent
│   │   ├── __init__.py
│   │   ├── req_agent/
│   │   │   ├── __init__.py
│   │   │   ├── agent_graph.py       # ReqAgent StateGraph
│   │   │   └── prompts.py           # Prompt 模板
│   │   ├── design_agent/
│   │   │   ├── __init__.py
│   │   │   ├── agent_graph.py       # DesignAgent StateGraph（含 RAG 调用）
│   │   │   └── prompts.py
│   │   ├── kicad_gen_agent/
│   │   │   ├── __init__.py
│   │   │   ├── agent_graph.py
│   │   │   └── prompts.py
│   │   └── validation_agent/
│   │       ├── __init__.py
│   │       ├── agent_graph.py
│   │       └── prompts.py
│   │
│   ├── mcp/
│   │   ├── __init__.py
│   │   ├── server.py                # MCP Server 主进程（stdio 模式）
│   │   └── tools/                   # 各工具实现
│   │       ├── __init__.py
│   │       ├── compdb.py            # compdb_search / compdb_add
│   │       ├── kicad.py             # kicad_erc / kicad_generate_sch
│   │       └── file_ops.py          # file_write / file_read
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── schema.sql              # PostgreSQL 表结构（含 pgvector）
│   │   ├── vector_store.py         # RAG 检索 / 添加实现（psycopg2）
│   │   ├── init_db.py              # 数据库初始化脚本（预置元件数据）
│   │   └── connection.py           # psycopg2 连接管理（从 config 读取 RDS URL）
│   │   └── component_db.sqlite      # 删除（改用 PostgreSQL）
│   │
│   └── tools/
│       ├── __init__.py
│       ├── kicad_cli.py             # KiCad CLI 封装
│       └── sch_generator.py         # .kicad_sch 文本生成器
│
├── docs/superpowers/specs/
│   └── 2026-05-19-langgraph-mcp-rag-design.md  ← 本文档
│
└── tests/
    ├── test_orchestrator.py
    ├── test_design_agent.py
    ├── test_mcp_tools.py
    └── test_rag.py
```

---

## 六、实现顺序（建议）

### Phase 1：LangGraph 基础（不涉及工具和 RAG）

1. 定义 `AgentState` 数据结构
2. 实现 Orchestrator `StateGraph`（不含工具调用，只做路由）
3. 实现 4 个 Subagent 的简单 node（无 ReAct 循环，纯函数）
4. 让整个 pipeline 能跑通（数据能从一个 stage 流到下一个）

### Phase 2：引入 MCP Server

1. 实现 `backend/mcp/server.py`（6 个工具）
2. Subagent 通过 ToolNode 连接 MCP Server
3. 验证 stdio 通信正常

### Phase 3：引入 RAG

1. 在 RDS PostgreSQL 上执行 `CREATE EXTENSION pgvector;`
2. 实现 `backend/db/schema.sql`（PostgreSQL 表结构，含 pgvector 列）+ `vector_store.py`（psycopg2）
3. 运行 `init_db.py` 预置 100 个常见元件（含 description embedding）
4. DesignAgent 的 node 中加入 RAG 检索调用
5. 验证 pgvector 检索返回正确结果

### Phase 4：完善 ReAct 循环

1. Subagent 从简单 node 升级为内部 StateGraph（think/action/obverse 节点）
2. 加入 MemorySaver checkpointer
3. 加入 iteration budget 和错误处理

---

## 七、技术选型依据（面试用）

| 选择                            | 理由                                                                                   |
| ----------------------------- | ------------------------------------------------------------------------------------ |
| **LangGraph 而非 LangChain**    | LangGraph 的 cyclic 图结构天然支持 ReAct 循环；LangChain 的 Chain 是线性链，不适合需要回退的场景                |
| **MCP Server（stdio）**         | 工具协议标准化是行业趋势（Anthropic 2025），stdio 模式适合本地进程间通信，无需额外网络服务                              |
| **PostgreSQL + pgvector**     | SQLite 不支持 pgvector，需第三方扩展；直接用 RDS PostgreSQL 启用 `CREATE EXTENSION pgvector`，零额外运维成本 |
| **每个 Subagent 独立 StateGraph** | 关注点分离，各 agent 可独立开发/测试；符合"多智能体各司其职"的生产级架构                                            |
| **MemorySaver checkpointer**  | LangGraph 内置，支持跨迭代状态持久化，无需额外 Redis                                                   |

---

## 八、已知约束与边界

1. **PostgreSQL + pgvector 启用**：在 RDS PostgreSQL 上执行 `CREATE EXTENSION pgvector;` 即可使用向量检索功能。
2. **KiCad Python API**：生成 .kicad_sch 两种方式都可以，先用字符串模板（最简单），后续再迁移到 pcbnew API。
3. **MCP Server 子进程管理**：main.py 启动时负责管理 MCP server 子进程的生命周期，需要处理 graceful shutdown。
4. **pgvector 向量维度**：`text-embedding-3-small` 输出 1536 维，创建向量列时需指定 `vector(1536)`。