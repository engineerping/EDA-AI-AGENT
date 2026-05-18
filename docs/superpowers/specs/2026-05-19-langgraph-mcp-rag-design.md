# EDA-AI-Agent — LangGraph + MCP + RAG 架构设计

**日期**: 2026-05-19
**版本**: v2.0
**状态**: 设计中

---

## 一、架构总览

<html>
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --c-gray:#e8e8e8;
  --c-purple:#ede7f6;
  --c-teal:#e0f2f1;
  --c-amber:#fff3e0;
  --c-green:#e8f5e9;
  --c-red:#ffebee;
  --t:#546e7a;
  --b:#37474f;
}
body{font-family:system-ui,-apple-system,sans-serif;background:#fafafa;padding:20px}
.diagram{padding:20px;max-width:900px;margin:0 auto}
.info-box{background:white;border:1px solid #e0e0e0;border-radius:8px;padding:16px 20px;margin-top:16px}
.info-title{font-size:14px;font-weight:600;color:#1a1a1a;margin-bottom:8px}
.info-body{font-size:12px;color:#666;line-height:1.6}
.tag{display:inline-block;font-size:10px;padding:2px 8px;border-radius:10px;margin:4px 4px 0 0;background:#f5f5f5;color:#888;font-weight:500}
.th{fill:#1a1a1a;font-size:13px;font-weight:600}
.ts{fill:#555;font-size:10px}
.th-sm{fill:#1a1a1a;font-size:11px;font-weight:600}
.ts-sm{fill:#666;font-size:9px}
.c-gray rect,.c-gray{fill:var(--c-gray);stroke:#bdbdbd}
.c-purple rect,.c-purple{fill:var(--c-purple);stroke:#9575cd}
.c-teal rect,.c-teal{fill:var(--c-teal);stroke:#4db6ac}
.c-amber rect,.c-amber{fill:var(--c-amber);stroke:#ffb74d}
.c-green rect,.c-green{fill:var(--c-green);stroke:#a5d6a7}
.c-red rect,.c-red{fill:var(--c-red);stroke:#ef9a9a}
.node{stroke-width:0.5;cursor:pointer}
.hint{font-size:11px;color:#999;text-align:center;margin-bottom:12px}
.c-label{font-size:9px;fill:#888}
</style>

<p class="hint">点击任意组件查看详情</p>

<svg width="100%" viewBox="0 0 900 580" role="img">
<title>EDA-AI-Agent LangGraph + MCP + RAG 架构图</title>
<defs>
  <marker id="ar" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
    <path d="M2 1L8 5L2 9" fill="none" stroke="context-stroke" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
  </marker>
  <marker id="ar2" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
    <path d="M2 1L8 5L2 9" fill="none" stroke="#ef9a9a" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
  </marker>
</defs>

<!-- User -->

<g class="node c-gray" onclick="show('user')">
  <rect x="320" y="20" width="260" height="48" rx="8"/>
  <text class="th" x="450" y="42" text-anchor="middle">User (Chat)</text>
  <text class="ts" x="450" y="58" text-anchor="middle">"我要一个 STM32F4 机器人主控板"</text>
</g>

<!-- Arrow User→Orch -->

<line x1="450" y1="68" x2="450" y2="92" stroke="var(--t)" stroke-width="1" marker-end="url(#ar)"/>

<!-- Orchestrator -->

<g class="node c-purple" onclick="show('orch')">
  <rect x="60" y="95" width="780" height="70" rx="8"/>
  <text class="th" x="450" y="115" text-anchor="middle">Orchestrator StateGraph (LangGraph)</text>
  <text class="ts" x="450" y="132" text-anchor="middle">ReAct Loop: Thought → Action → Observation → 循环直到 ERC 通过</text>
  <text class="ts" x="450" y="148" text-anchor="middle">State: {stage, requirements, bom, schematic_content, erc_errors, budget} · MemorySaver checkpointer</text>
</g>

<!-- Fan arrows Orch→4 Agents -->

<line x1="450" y1="165" x2="150" y2="198" stroke="var(--t)" stroke-width="0.8" marker-end="url(#ar)"/>
<line x1="450" y1="165" x2="340" y2="198" stroke="var(--t)" stroke-width="0.8" marker-end="url(#ar)"/>
<line x1="450" y1="165" x2="530" y2="198" stroke="var(--t)" stroke-width="0.8" marker-end="url(#ar)"/>
<line x1="450" y1="165" x2="720" y2="198" stroke="var(--t)" stroke-width="0.8" marker-end="url(#ar)"/>

<!-- 4 Sub-agents -->

<g class="node c-teal" onclick="show('req')">
  <rect x="75" y="200" width="150" height="60" rx="8"/>
  <text class="th-sm" x="150" y="220" text-anchor="middle">Req Agent</text>
  <text class="ts-sm" x="150" y="236" text-anchor="middle">StateGraph + MemorySaver</text>
  <text class="ts-sm" x="150" y="250" text-anchor="middle">+ MCP Client</text>
</g>

<g class="node c-teal" onclick="show('design')">
  <rect x="265" y="200" width="150" height="60" rx="8"/>
  <text class="th-sm" x="340" y="220" text-anchor="middle">Design Agent</text>
  <text class="ts-sm" x="340" y="236" text-anchor="middle">StateGraph + MemorySaver</text>
  <text class="ts-sm" x="340" y="250" text-anchor="middle">+ MCP Client + RAG</text>
</g>

<g class="node c-teal" onclick="show('gen')">
  <rect x="455" y="200" width="150" height="60" rx="8"/>
  <text class="th-sm" x="530" y="220" text-anchor="middle">KiCad Gen Agent</text>
  <text class="ts-sm" x="530" y="236" text-anchor="middle">StateGraph + MemorySaver</text>
  <text class="ts-sm" x="530" y="250" text-anchor="middle">+ MCP Client</text>
</g>

<g class="node c-teal" onclick="show('valid')">
  <rect x="645" y="200" width="150" height="60" rx="8"/>
  <text class="th-sm" x="720" y="220" text-anchor="middle">Validation Agent</text>
  <text class="ts-sm" x="720" y="236" text-anchor="middle">StateGraph + MemorySaver</text>
  <text class="ts-sm" x="720" y="250" text-anchor="middle">+ MCP Client</text>
</g>

<!-- Arrows agents→MCP Server -->

<line x1="150" y1="260" x2="280" y2="310" stroke="var(--t)" stroke-width="0.8" marker-end="url(#ar)"/>
<line x1="340" y1="260" x2="340" y2="310" stroke="var(--t)" stroke-width="0.8" marker-end="url(#ar)"/>
<line x1="530" y1="260" x2="400" y2="310" stroke="var(--t)" stroke-width="0.8" marker-end="url(#ar)"/>
<line x1="720" y1="260" x2="560" y2="310" stroke="var(--t)" stroke-width="0.8" marker-end="url(#ar)"/>

<!-- MCP Server -->

<g class="node c-amber" onclick="show('mcp')">
  <rect x="180" y="315" width="540" height="95" rx="8"/>
  <text class="th" x="450" y="338" text-anchor="middle">MCP Server (stdio 子进程)</text>
  <line x1="200" y1="350" x2="700" y2="350" stroke="#e0e0e0" stroke-width="0.5"/>
  <text class="ts-sm" x="215" y="368">工具清单：</text>
  <text class="ts-sm" x="215" y="383">compdb_search(query) → pgvector 相似度检索</text>
  <text class="ts-sm" x="215" y="396">compdb_add(data) → 写入 PostgreSQL + 生成 embedding</text>
  <text class="ts-sm" x="215" y="409">kicad_erc(sch_path) → KiCad CLI ERC 检查</text>
  <text class="ts-sm" x="450" y="383">kicad_generate_sch(bom) → 生成 .kicad_sch 文本</text>
  <text class="ts-sm" x="450" y="396">file_write(path, content)</text>
  <text class="ts-sm" x="450" y="409">file_read(path)</text>
</g>

<!-- Arrows MCP→3 bottom boxes -->

<line x1="280" y1="410" x2="160" y2="450" stroke="var(--t)" stroke-width="0.8" marker-end="url(#ar)"/>
<line x1="400" y1="410" x2="390" y2="450" stroke="var(--t)" stroke-width="0.8" marker-end="url(#ar)"/>
<line x1="560" y1="410" x2="620" y2="450" stroke="var(--t)" stroke-width="0.8" marker-end="url(#ar)"/>

<!-- 3 bottom layers -->

<g class="node c-green" onclick="show('postgres')">
  <rect x="60" y="455" width="200" height="90" rx="8"/>
  <text class="th-sm" x="160" y="475" text-anchor="middle">PostgreSQL + pgvector (RDS)</text>
  <line x1="75" y1="488" x2="245" y2="488" stroke="#e0e0e0" stroke-width="0.5"/>
  <text class="ts-sm" x="80" y="502">components 表</text>
  <text class="ts-sm" x="80" y="515">component_embeddings 表</text>
  <text class="ts-sm" x="80" y="528">(pgvector 向量 1536维)</text>
  <text class="ts-sm" x="80" y="541">CREATE EXTENSION pgvector</text>
</g>

<g class="node c-amber" onclick="show('kicadcli')">
  <rect x="290" y="455" width="200" height="90" rx="8"/>
  <text class="th-sm" x="390" y="475" text-anchor="middle">KiCad CLI (ERC / DRC)</text>
  <line x1="305" y1="488" x2="475" y2="488" stroke="#e0e0e0" stroke-width="0.5"/>
  <text class="ts-sm" x="310" y="502">kicad-cli sch erc</text>
  <text class="ts-sm" x="310" y="515">kicad-cli pcb drc</text>
  <text class="ts-sm" x="310" y="528">headless 模式</text>
  <text class="ts-sm" x="310" y="541">输出 XML 报告</text>
</g>

<g class="node c-gray" onclick="show('filesystem')">
  <rect x="520" y="455" width="200" height="90" rx="8"/>
  <text class="th-sm" x="620" y="475" text-anchor="middle">文件系统</text>
  <line x1="535" y1="488" x2="705" y2="488" stroke="#e0e0e0" stroke-width="0.5"/>
  <text class="ts-sm" x="540" y="502">.kicad_sch (S-expression)</text>
  <text class="ts-sm" x="540" y="515">BOM CSV</text>
  <text class="ts-sm" x="540" y="528">ERC Report</text>
  <text class="ts-sm" x="540" y="541">输出目录</text>
</g>

<!-- Feedback loop: Validation → back to Design (ERC errors) -->

<path d="M795 240 L830 240 L830 395 L795 395" fill="none" stroke="#ef9a9a" stroke-width="1.2" stroke-dasharray="4 3" marker-end="url(#ar2)"/>
<text class="ts-sm" x="800" y="318" fill="#ef9a9a">ERC 错误</text>
<text class="ts-sm" x="800" y="332" fill="#ef9a9a">回退修正</text>
<text class="ts-sm" x="800" y="346" fill="#ef9a9a">(最多 3 次)</text>

<!-- Memory store label -->

<rect x="65" y="295" width="80" height="22" rx="5" fill="none" stroke="var(--b)" stroke-width="0.5" stroke-dasharray="3 2" opacity="0.5"/>
<text class="ts-sm" x="105" y="310" text-anchor="middle" opacity="0.7">MemoryStore</text>

<!-- RAG label -->

<rect x="285" y="295" width="110" height="22" rx="5" fill="none" stroke="#4db6ac" stroke-width="0.8" opacity="0.7"/>
<text class="ts-sm" x="340" y="310" text-anchor="middle" fill="#4db6ac">RAG 检索</text>

</svg>

<div class="info-box" id="info-box">
  <div class="info-title">EDA-AI-Agent — LangGraph + MCP + RAG 架构</div>
  <div class="info-body">六层架构：用户对话 → Orchestrator (LangGraph StateGraph) → 四个专用子智能体 → MCP Server → 三个后端（PostgreSQL/pgvector 存储、KiCad CLI 执行 ERC、文件系统输出）。ERC 错误时触发反馈循环（最多修正 3 次）。点击任意组件查看实现细节。</div>
</div>

<script>
const D = {
  user:{
    t:'User (Chat) — 用户对话层',
    b:'用户以自然语言描述电路需求（例："我需要一个机器人主控板，STM32F4，带 4 路电机驱动、IMU 接口、USB 通信"）。Agent 会主动追问遗漏的约束：工作电压范围、最大电流、封装偏好（SMD/THT）、是否贴片打样（嘉立创）、预算上限。',
    tags:['Multi-turn Dialog','Structured Output']
  },
  orch:{
    t:'Orchestrator StateGraph — LangGraph 主循环',
    b:'核心 ReAct 循环：接收需求 → Thought（判断下一步）→ Action（调用子 agent）→ Observation（收集结果）→ 循环直到 ERC 通过。\n① 维护全局设计状态（需求文档 + BOM 草稿 + 当前方案版本）\n② 路由到正确的子 agent\n③ 管理 iteration budget（最多 20 轮，防无限循环）\n④ ERC 错误时触发修复循环（最多 3 次修正）\n⑤ MemorySaver checkpointer 跨迭代持久化状态。',
    tags:['LangGraph','ReAct','StateGraph','MemorySaver','Iteration Budget']
  },
  req:{
    t:'Req Agent — 需求拆解',
    b:'系统性地将模糊需求转换为结构化规格。内部有独立 StateGraph + MemorySaver，支持 ReAct 内部循环。输出 JSON 格式需求文档，未确认项标注 TBD。',
    tags:['StateGraph','MemorySaver','ReAct','JSON Schema']
  },
  design:{
    t:'Design Agent — 电路设计与选型（RAG）',
    b:'根据需求文档选择最优电路拓扑。从 PostgreSQL + pgvector 检索元器件（RAG），生成完整 BOM 并标注选型理由。内部 StateGraph 支持 think/action/observe 循环，MemorySaver 持久化中间状态。',
    tags:['RAG','pgvector','StateGraph','MemorySaver','BOM Generation']
  },
  gen:{
    t:'KiCad Gen Agent — 原理图生成',
    b:'将 BOM + 连接关系转换为 KiCad .kicad_sch 文件（S-expression 格式）。通过 MCP 调用 kicad_generate_sch 工具，写入文件系统。内部 StateGraph 管理生成状态。',
    tags:['S-expression','.kicad_sch','MCP','StateGraph']
  },
  valid:{
    t:'Validation Agent — ERC/DRC 验证',
    b:'调用 KiCad CLI 在 headless 模式运行 ERC。解析 XML 报告，将错误翻译为中文并给出修复方案。错误时通过反馈循环回到 Design Agent 重新修正（最多 3 次）。',
    tags:['ERC','KiCad CLI','XML','Feedback Loop','StateGraph']
  },
  mcp:{
    t:'MCP Server — 工具协议层（stdio 子进程）',
    b:'MCP (Model Context Protocol) 是 Anthropic 提出的工具调用标准协议。EDA-AI-Agent 中 MCP Server 以子进程运行，通过 stdio 与 LangGraph 通信。\n\n工具清单：\n• compdb_search — RAG 检索元件（PostgreSQL + pgvector）\n• compdb_add — 添加元件到数据库\n• kicad_erc — 调用 KiCad CLI 执行 ERC\n• kicad_generate_sch — 生成 .kicad_sch 文件\n• file_write / file_read — 文件操作',
    tags:['MCP','stdio','Model Context Protocol','Tool Protocol']
  },
  postgres:{
    t:'PostgreSQL + pgvector — 元件知识库',
    b:'存储元器件的结构化数据 + 向量嵌入。\n\n表结构：\n• components — 元件基础信息（型号/封装/价格/JLC编号）\n• component_embeddings — description 向量（text-embedding-3-small, 1536维）\n\nRAG 流程：用户 query → Embedding → pgvector 余弦相似度检索 → Top-K → 注入 prompt\n\n启用方式：在 RDS PostgreSQL 上执行 CREATE EXTENSION pgvector;',
    tags:['pgvector','RDS PostgreSQL','RAG','text-embedding','Cosine Similarity']
  },
  kicadcli:{
    t:'KiCad CLI — 无头模式自动化',
    b:'KiCad 7+ 提供完整 CLI，支持无 GUI 运行。\n• kicad-cli sch erc — ERC 检查，输出 XML 报告\n• kicad-cli pcb drc — PCB DRC 检查\n• kicad-cli sch export --format pdf — 导出 PDF\n\nEDA-AI-Agent 通过 subprocess 调用，捕获 stdout/stderr，解析 XML 错误列表。',
    tags:['KiCad CLI 7+','subprocess','ERC','DRC','headless']
  },
  filesystem:{
    t:'文件系统 — 输出层',
    b'EDA-AI-Agent 输出的文件：\n• .kicad_sch — KiCad 原理图（S-expression 文本，可 Git 版本控制）\n• BOM CSV — 物料清单（可直接用于嘉立创下单）\n• ERC Report — 错误列表与修复指南',
    tags:['S-expression','KiCad 7/8','Git-friendly','BOM CSV']
  }
};

function show(key){
  const d=D[key];
  if(!d) return;
  const tags=d.tags.map(t=>`<span class="tag">${t}</span>`).join('');
  document.getElementById('info-box').innerHTML=`<div class="info-title">${d.t}</div><div class="info-body" style="white-space:pre-line">${d.b}</div><div>${tags}</div>`;
}
</script>

</html>

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