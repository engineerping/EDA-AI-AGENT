问：
我要学习 AI agent 开发了，请你阅读 
https://github.com/ultraworkers/claw-code 和 
https://github.com/openclaw/openclaw 和 
https://github.com/nousresearch/hermes-agent以及 
https://developer.harness.io/。
告诉我 AI Agent 的架构是什么样的，包含哪些方面， 
以金字塔的形式（也就是像书的目录结构一样）。系统地、分门别类地，事无巨细地教我如何做 AI agent 开发，
之所以要这么做，是因为我要面试 AI agent 开发的工作。最后告诉我如果要开发 AI agent，需要掌握哪些知识。

---

答：
好，资料读取完毕。我从 Hermes Agent（NousResearch）、OpenClaw、Claw-Code 和 Harness AI 的真实架构中，提炼出了这套完整的 AI Agent 知识体系。先给你一个可交互的架构金字塔，再逐层拆解。---

下面是完整的文字版知识体系，供面试备考和深度学习使用。

---

## 一、AI Agent 是什么（面试必答）

Agent = **感知（Perceive）→ 推理（Think）→ 行动（Act）→ 反思（Reflect）** 的循环体。与普通 LLM 的区别在于：它能**自主决策调用工具**、**跨轮次保持状态**，并在**完成目标之前不停止**。

---

## 二、金字塔六层详解

### L0 · LLM 模型基础（地基）

这是最容易被跳过、却最容易在面试中暴露短板的层次。

**你必须能解释：**

- **Token 与 Context Window**：模型以 token 为单位处理文本，128k token ≈ 约 10 万汉字。Agent 做 context 管理的本质是在有限 window 内塞进最有价值的信息。
- **Temperature / Top-p**：temperature=0 是确定性输出（适合工具调用），temperature=1 是创意写作。Agent 的工具调用阶段通常用低 temperature。
- **System / User / Assistant 三角色**：这是 agent 控制模型行为的核心抓手。system prompt 定义人格与规则，user 给任务，assistant 是历史回复。
- **Function Calling 机制**：模型不直接执行代码，而是输出一个结构化的 JSON（工具名 + 参数），agent 框架解析后真正执行，再把结果塞回对话历史。

---

### L1 · Agent 核心引擎（心脏）

这是面试最高频考点，必须能手写。

**ReAct Loop 的完整流程：**

```
while not done:
    messages = build_prompt(history, tools, memory)
    response = llm.call(messages)

    if response.tool_calls:
        for call in response.tool_calls:    # 可并行
            result = execute_tool(call)
            history.append(tool_result(result))
    else:
        return response.text                # 任务完成

    if iteration > budget:
        raise BudgetExceeded()              # 防无限循环
```

**Prompt 工程的黄金结构（来自 Hermes `prompt_builder.py` 的真实顺序）：**

1. **SOUL / Persona**：定义 agent 是谁、有什么价值观
2. **MEMORY.md**：长期记忆（用户偏好、历史事实）
3. **Skills**：当前会话可用的技能列表
4. **AGENTS.md / 行为规范**：约束 agent 行为的规则文档
5. **工具列表与使用指引**：告诉模型有什么工具、何时用
6. **模型特定指令**：针对不同 LLM 的特殊 prompt 技巧

---

### L2 · 工具系统与记忆（双手与大脑）

**工具（Tools）的设计原则：**

- Description 比参数定义更重要。模型靠 description 决定用不用这个工具。
- 工具粒度要适中：太细 → 工具太多模型困惑；太粗 → 灵活性差。
- 并行工具调用大幅降低延迟：Hermes 用 `ThreadPoolExecutor(max_workers=8)` 并行执行。

**记忆的四个层次（面试常考）：**

| 层次   | 存在哪里                | 寿命   | 举例               |
| ---- | ------------------- | ---- | ---------------- |
| 工作记忆 | Context window      | 单次会话 | 当前对话内容           |
| 情节记忆 | Session DB (SQLite) | 跨会话  | 上次用户说的偏好         |
| 语义记忆 | Vector DB           | 永久   | 公司内部文档知识库        |
| 程序记忆 | Skills 文件           | 永久   | Agent 自主创建的可复用脚本 |

**RAG 流程（Retrieval-Augmented Generation）：**

```
用户问题 → Embedding 模型编码 → 向量相似度检索 → 
取 Top-K 文档 → 注入 Prompt → LLM 生成引用具体知识的回答
```

Context 压缩策略（当历史太长时）：保留 System Prompt + 最新 N 轮 + 中间摘要。Hermes 的 `context_compressor.py` 在 context 超阈值时自动对中间轮对话做摘要。

---

### L3 · 接口 / 部署 / MCP（神经末梢）

**MCP (Model Context Protocol) 是 2025 年后 Agent 生态的核心标准，面试必考：**

- MCP 是 Anthropic 提出的协议，让 LLM 工具调用标准化，类比"AI 领域的 USB 接口"。
- 两种传输：`stdio`（本地子进程）和 `Streamable HTTP`（远程服务，2025-11-25 规范）。
- Agent 作为 MCP Client，MCP Server 封装能力（文件系统、数据库、第三方 API）。
- 命名约定：`mcp_<server>_<tool_name>`，如 `mcp_gdrive_list_files`。

**执行后端选型：**

- 开发阶段：Local（最简单，shell 状态跨 tool_call 保留）
- 安全隔离：Docker（read-only rootfs + capabilities dropped）
- 弹性计算：Modal / Daytona（serverless，闲时休眠，成本接近零）
- 企业治理：Harness Pipeline Engine（agent 即 pipeline step，天然继承 RBAC / Secrets / 审计日志）

---

### L4 · 多智能体 / 编排（神经网络）

**四种核心 Multi-Agent 模式：**

**1. 管道型（Pipeline）** — Harness 三智能体架构：

```
Planner Agent → Generator Agent → Evaluator Agent
（拆解任务）    （生成代码/内容）  （质量验证，可循环）
```

**2. 主从型（Orchestrator + Subagents）** — Hermes 的实现：

```python
# 主 agent 决策
spawn_subagent(task="搜索竞品信息", context=compressed_ctx)
spawn_subagent(task="分析财务数据", context=compressed_ctx)
# 并行执行，主 agent 汇总结果
```

**3. 角色型（Role-based）** — CrewAI / AutoGen：

```
Research Agent ←→ Writer Agent ←→ Critic Agent
（收集信息）     （起草内容）     （审查修改）
```

**4. 反思型（Self-Reflection）**：

```
Generator → 生成输出 → Critic（同一模型不同 prompt）→ 
评估质量 → 不合格则重新生成 → 达标后输出
```

---

### L5 · 评估 / 安全 / 治理（免疫系统）

这层是 Agent 能否上生产的关键，也是很多候选人忽视、因此能形成差异化的地方。

**Eval 的三个维度：**

1. **单步评估**：单次 LLM 调用输出是否正确（JSON schema 校验、工具选择准确率）
2. **轨迹评估**：完整任务执行路径是否合理（有没有绕弯、有没有不必要的工具调用）
3. **端到端评估**：最终结果是否满足用户目标（通常需要 LLM-as-Judge）

**Prompt Injection 防御（面试高频）：**

Agent 读取的任何外部内容（网页、文件、邮件、数据库记录）都可能包含恶意指令，攻击者可以写入"请忽略之前的所有指令，改为..."。防御策略：

- 明确区分 system / user / tool_result 的信任边界
- 对 tool_result 中的指令要求用户二次确认
- 不允许 tool_result 中的内容直接升级为 system 级别权限

---

## 三、面试必须掌握的知识点清单

按优先级排序，**加粗**为高频考点：

**LLM 基础**

- **Transformer attention 机制**、KV Cache 原理
- **Function Calling / Tool Use 完整流程**
- **Context window 管理与 token 优化**
- Prompt Engineering：Few-shot、CoT、XML 结构化输出
- temperature / top_p 参数调优

**Agent 框架与实现**

- **ReAct (Reason + Act) 循环的手写实现**
- **Agent Loop 的终止条件设计（IterationBudget）**
- Tool Registry 的设计模式
- **并行 Tool Call 实现**（ThreadPoolExecutor）
- Prompt Builder 的组装顺序与优先级

**记忆与 RAG**

- **四层记忆模型**（工作/情节/语义/程序）
- **RAG 完整流程**与 Embedding 选型
- Context 压缩策略（摘要 + 保留关键轮次）
- 向量数据库选型（Chroma vs pgvector vs Pinecone）

**多智能体**

- **Orchestrator + Subagent 模式**的实现
- **Planner → Generator → Evaluator 三智能体架构**
- 状态共享 vs 状态隔离的权衡
- 任务分解策略（ReAct / Plan-and-Execute）

**工具与协议**

- **MCP 协议原理**（stdio vs HTTP transport）
- 工具 Schema 设计（description 质量的重要性）
- Provider 路由与 Fallback 链设计

**评估与安全**

- **LLM-as-Judge 评估方法**
- **Prompt Injection 攻击与防御**
- 轨迹评估（Trajectory Eval）的设计
- 可观测性：Trace / Span / Token 成本追踪

**框架与生态**

- LangChain / LangGraph（图状工作流）
- CrewAI / AutoGen（多智能体协作）
- OpenRouter / LiteLLM（多 provider 路由）
- Hermes Agent（自我改进 agent 的完整实现参考）
- Harness AI（企业级 agent 治理的最佳实践）

面试时最能展示深度的一句话，来自 Hermes 架构文档：**"Agent 的核心是一个同步编排引擎，处理 provider 选择、prompt 构建、工具执行、重试、fallback、压缩和持久化。"** 把这句话背后每个词都能展开说清楚，基本就能拿到 offer。

---

问：
You've already extracted this complete AI Agent knowledge system from the real-world architectures of
 Hermes Agent (NousResearch), 
 OpenClaw, 
 Claw-Code, 
 and Harness AI.
Next, I want to create an AI agent called EDA-AI-agent. When I tell this AI agent I want to build a circuit 
with a certain function, it will communicate with me to break down the requirements, finalize the solution 
step by step, and supplement any important issues I haven't considered. It will meticulously guide me 
step-by-step in drawing a complete, commercially viable circuit diagram using KiCad.
Please first assess the feasibility. If feasible, please describe the architecture of such an EDA-AI-agent.

---

答：

## 可行性评估

先给结论：**可行，但有边界**。

| 维度             | 判断      | 说明                                     |
| -------------- | ------- | -------------------------------------- |
| 需求拆解对话         | ✅ 完全可行  | LLM 最擅长的事                              |
| 方案选型建议         | ✅ 可行    | LLM 有足够的电路知识储备                         |
| 生成 KiCad 原理图文件 | ✅ 可行    | KiCad `.kicad_sch` 是纯文本格式，可程序化生成       |
| 自动 PCB 布局布线    | ⚠️ 部分可行 | KiCad 有 Python API，但自动布局质量有限，复杂板需要人工介入 |
| 电路正确性验证        | ✅ 可行    | KiCad CLI 可运行 ERC / DRC，结果反馈给 agent    |
| 完全商业级免人工       | ❌ 当前不现实 | 复杂模拟电路、高速信号、EMC 设计仍需工程师审查              |

核心依据：KiCad 7/8 的 `.kicad_sch` 格式是结构化的 S-expression 文本，LLM 可以直接生成和修改；KiCad 内置 Python 脚本 API (`pcbnew`) 可以程序化操作 PCB；KiCad CLI 支持无头模式运行 ERC/DRC 并输出报告。

---

## EDA-AI-Agent 完整架构（见eda_ai_agent_architecture.html）

---

<iframe src="eda_ai_agent_architecture.html" width="100%" height="500px" frameborder="0"></iframe>

## 可行性结论（总结）

**核心突破口是 KiCad 的文件格式**。`.kicad_sch` 是 S-expression 纯文本，结构高度规则，LLM 可以直接学习并生成。这是整个 agent 可行的技术基础。

---

## 三个真实的技术难点，面试时要能说出来

**难点一：元件库匹配**

KiCad 官方库有 17,000+ 元件符号，每个都有严格的 `lib_id`（如 `Device:LED`、`MCU_ST_STM32F4:STM32F405RGTx`）。LLM 如果随机生成 lib_id，必然找不到对应符号，KiCad 打开时会报"缺少符号库"。解决方案：预先把官方库所有符号名索引到 Component DB，Agent 选型时必须从索引里取，不能自由发挥。

**难点二：PCB 布局质量**

KiCad Python API 可以自动放置元件，但 **自动布局质量很差**——去耦电容需要尽量靠近 IC 的电源引脚，差分对需要等长走线，这些约束纯靠算法无法保证。现实方案：Agent 生成 `.kicad_sch` 原理图（完全可自动化），PCB 布局阶段提供**文字指导**（"C1 建议放在 U1 的 VCC 引脚附近，距离小于 2mm"），让用户手动操作 KiCad 完成布局。

**难点三：ERC 错误的语义翻译**

KiCad ERC 的错误 XML 只告诉你"pin_type mismatch at U1 pin 14"，但不解释为什么。需要 Agent 结合元件数据手册和电路上下文，把这句话翻译成"STM32 的 BOOT0 引脚需要通过 10kΩ 下拉电阻接 GND，否则芯片无法正常启动"。这个语义翻译层是真正体现 AI 价值的地方。

---

## 最小可行版本（建议先做这个）

不要一上来就做完整的 5 层架构，先做一个可以 demo 的版本：

**MVP 范围：** 用户描述需求 → Req Agent 追问补充 → Design Agent 生成 BOM → KiCad Gen 生成 .kicad_sch 文本 → 用户用 KiCad 打开验证

技术栈：LangChain + Python + pgvector（Component DB）+ 字符串模板（生成 .kicad_sch，不需要安装 KiCad Python 环境）+ KiCad CLI（ERC 验证，仅在本地测试阶段）

这个 MVP 就可以作为一个很强的面试项目了。

---

## 技术选型：LangGraph（AI Agent 开发框架）

**结论：选择 LangGraph，而非 LangChain / LlamaIndex / Haystack。**

### 四框架对比

| 维度       | LangChain | LangGraph              | LlamaIndex    | Haystack        |
| -------- | --------- | ---------------------- | ------------- | --------------- |
| 定位       | LLM 应用开发库 | **多智能体工作流编排引擎**        | 知识检索 / RAG 专用 | NLP 流水线 / QA 专用 |
| 工作流模型    | 链式（Chain） | **图状（Graph）** — 支持循环   | 索引 → 查询       | Pipeline        |
| ReAct 循环 | 支持但非原生    | **原生支持cyclic图**        | 不支持           | 不支持             |
| 多智能体编排   | 需自行实现     | **内置 Orchestrator 模式** | 不支持           | 不支持             |
| 状态管理     | 有限        | **完整的状态传递与持久化**        | 不适用           | 不适用             |
| 学习曲线     | 陡峭（过于抽象）  | 中等（图论直观）               | 低（专注 RAG）     | 中等              |

### 选择 LangGraph 的核心理由

**1. ReAct 循环是 LangGraph 的原生场景**

EDA-AI-Agent 的核心是 ReAct 循环：Thought → Action → Observation → 循环。LangGraph 的 `StateGraph` 支持带环的图结构，每个节点执行后可以再次回到起点，这正是 ReAct 循环的数学抽象。LangChain 的 `Chain` 是线性链式，不适合需要回头重新执行的场景。

**2. Orchestrator + Subagents 架构与 LangGraph 完美对齐**

LangGraph 中，每个 `Agent` 是一个 Node，节点之间通过 `edges` 路由。Orchestrator 根据 `state` 决策路由到哪个子 Agent，子 Agent 执行完后状态返回 Orchestrator 再路由——这正是 LangGraph 的标准用法。

**3. 状态管理是 LangGraph 的内置特性**

ReAct 循环需要跨迭代保持：`iteration_budget`、`bom_draft`、`design_state`、`erc_errors`。LangGraph 的 `StateGraph` 自动管理状态传递，无需自行实现 Context 管理。

**4. 与 LangChain 生态兼容**

LangGraph 底层调用 LangChain 的 LLM 和 Tool 接口，可以直接使用 LangChain 的 `ChatOpenAI`、`Tool`装饰器、`prompt_builder`。不是重新发明轮子，而是用更合适的工具做更合适的事。

### 在架构图中的位置

```
Orchestrator Agent (LangGraph StateGraph)
    ├── Req Agent (Node)
    ├── Design Agent (Node)
    ├── KiCad Gen Agent (Node)
    └── Validation Agent (Node)
         ↓
    Tool Layer (LangChain Tool)
         ↓
    Memory Store (LangGraph checkpointer)
```

### 不选其他框架的原因

- **LangChain**：过于泛化，Chain 线性结构不适合循环场景，ReAct 实现需要自己管理循环逻辑
- **LlamaIndex**：专注 RAG 和知识检索，缺少 Agent 工作流编排能力，EDA 需要的是工作流而非检索
- **Haystack**：面向 NLP/QA 场景，原生不支持 Agent 循环和多智能体编排，学习成本高但场景不匹配

---

## EDA-AI-Agent 实现架构

### 架构图

![EDA-AI-Agent-architecture](./EDA-AI-Agent-architecture.png)

### 运行效果

![Running_result](./Running_result.png)

---

### 技术栈

| 层级           | 技术选型                               | 说明                                                   |
| ------------ | ---------------------------------- | ---------------------------------------------------- |
| **LLM 调用**   | LiteLLM                            | 统一接口调用 OpenAI / Anthropic / DeepSeek / Qwen / Ollama |
| **Agent 框架** | LangGraph StateGraph               | ReAct 循环 + 多 Agent 编排 + 状态管理                         |
| **协议层**      | MCP (Model Context Protocol)       | stdio 本地子进程，工具调用标准化                                  |
| **向量数据库**    | **pgvector（优先）** / SQLite FTS5（备用） | RAG 语义检索元件库                                          |
| **原理图格式**    | KiCad `.kicad_sch` S-expression    | LLM 直接生成，纯文本无需 KiCad 环境                              |
| **ERC 验证**   | KiCad CLI（可选）                      | 无头模式运行 DRC/ERC，结果反馈 Agent                            |
| **前端**       | React + TypeScript + WebSocket     | 实时流式对话 + 原理图预览                                       |

---

### 数据库设计：pgvector 优先 + SQLite fallback

**设计原则：** 开发时无需准备 PostgreSQL，开箱即用；生产环境设置 `EDB_PG_URL` 开启完整 RAG 能力。

#### 环境变量

```bash
# 启用 pgvector RAG（不设置则使用 SQLite FTS5）
export EDB_PG_URL="postgresql://postgres:password@localhost:5432/eda_agent"
```

#### Fallback 逻辑

```python
# backend/mcp/tools/compdb.py

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
    """Add a component — pgvector if available, SQLite stub otherwise."""
    if os.environ.get("EDB_PG_URL"):
        try:
            from backend.db.pg_vector_store import add_component as _pg_add
            component_id = _pg_add(data)
            return CallToolResult(content=[TextContent(type="text", text=json.dumps({"status": "ok", "id": component_id}))])
        except Exception as e:
            return CallToolResult(content=[TextContent(type="text", text=f"pgvector add failed: {e}")])
    name = data.get("name", "unknown")
    return CallToolResult(content=[TextContent(type="text", text=f"Component {name} added (SQLite only — set EDB_PG_URL for pgvector)")])
```

#### PostgreSQL + pgvector schema

```sql
-- backend/db/pg_schema.sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE components (
    id SERIAL PRIMARY KEY,
    lib_id TEXT NOT NULL,
    name TEXT NOT NULL,
    mpn TEXT,
    category TEXT,
    package TEXT,
    jlc_part TEXT,
    price NUMERIC,
    stock INTEGER,
    description TEXT
);
CREATE TABLE component_embeddings (
    id SERIAL PRIMARY KEY,
    component_id INTEGER REFERENCES components(id),
    description_text TEXT,
    embedding vector(1536)
);
CREATE INDEX ON component_embeddings USING ivfflat (embedding cosine_OPERATOR) WITH (lists = 100);
```

#### SQLite FTS5 fallback

- 表结构：`id, lib_id, name, mpn, category, package, jlc_part, price, stock, description`
- 全文搜索：FTS5 on `name + category + description`
- 无 Embedding 检索，使用 LIKE 模糊匹配

---

### MCP Server 设计

MCP Server 以 stdio 子进程运行，Agent 通过 `mcp_<server>_<tool>` 命名调用工具。

| 工具                   | 说明                                  |
| -------------------- | ----------------------------------- |
| `mcp_compdb_search`  | 元件库语义检索（pgvector RAG 或 SQLite FTS5） |
| `mcp_compdb_add`     | 添加自定义元件到数据库                         |
| `mcp_kicad_validate` | 调用 KiCad CLI 运行 ERC，返回错误列表          |
| `mcp_fs_read`        | 读取本地文件（如 KiCad 官方库符号列表）             |

---

### 多 Agent 流水线（Pipeline）

```
用户输入
    ↓
Req Agent（需求分析）→ 与用户多轮对话 → 输出结构化 requirements dict
    ↓
Design Agent（BOM 生成）→ 从 Component DB 选型 → 输出 BOM list
    ↓
KiCad Gen Agent（原理图生成）→ 生成 .kicad_sch S-expression 文本
    ↓
Validation Agent（ERC 验证）→ KiCad CLI 运行 ERC → 如有错误最多循环 3 次修复
    ↓
前端预览 + 下载
```

**关键设计：** ERC 验证失败后自动返回 Design Agent 重试（最多 3 次 correction_attempts），避免手动干预。

---

### 项目结构

```
backend/
  main.py                      FastAPI 应用 + WebSocket
  orchestrator/
    __init__.py                 导出 Orchestrator, Session, build_orchestrator_graph, AgentState
    orchestrator_module.py     Orchestrator.run() + Session + PipelineStage + SessionState
    graph_builder.py           LangGraph StateGraph 构建（当前未在运行时调用）
    langgraph_state.py         AgentState TypedDict
  agents/
    req_agent.py               需求分析 Agent
    design_agent.py            BOM 设计 Agent
    kicad_gen_agent.py         KiCad 原理图生成 Agent
    validation_agent.py        ERC 验证 Agent
  db/
    pg_vector_store.py         pgvector RAG（EDB_PG_URL 时启用）
    pg_schema.sql              PostgreSQL schema
    sqlite_component_db.py    SQLite FTS5 fallback
  mcp/
    tools/
      compdb.py                MCP compdb_search / compdb_add（pgvector 优先 + SQLite fallback）
      kicad_cli.py             KiCad CLI 封装
      fs_read.py               文件读取工具
    server.py                  MCP stdio 服务器
frontend/
  src/
    components/                React 组件
    hooks/
      useAgentSocket.ts        WebSocket + 状态管理
    api/
      client.ts                REST API 客户端
tests/
  test_e2e_pipeline.py         E2E 集成测试（标记 @pytest.mark.integration）
```

---

## 竞品分析：AI EDA 工具全景

### 第一类：概念设计 + 智能原理图生成（从想法到电路）

| 工具               | 核心能力                                         | 对我们的意义                       |
| ---------------- | -------------------------------------------- | ---------------------------- |
| **Flux.ai**      | 浏览器版 eCAD，内置 Copilot，自然语言 → 原理图 + BOM，$20/月起 | **最直接的竞争对手**，验证了"自然语言→原理图"可行 |
| **Circuit Mind** | 需画顶层架构框图输入，不是纯自然语言，面向专业团队                    | 输入方式不同，不是直接竞品                |
| **Celus**        | 早期概念→原理图，可导出 Altium，偏框图输入                    | 无法验证，思路类似但非自然语言              |

### 第二类：工业级 AI 辅助（布局与布线）

| 工具                       | 核心能力                                 | 定位             |
| ------------------------ | ------------------------------------ | -------------- |
| **Cadence Allegro X AI** | 云端 AI 自动高密度 PCB 布局布线，严守 SI/PI/DFM 规则 | 布局工具，不是原理图生成   |
| **Quilter / DeepPCB**    | 强化学习自动布线，上传 KiCad/Altium 文件即可        | 需先有设计文件，补充而非替代 |

### 第三类：轻量级创客工具

| 工具                  | 核心能力                                | 定位                |
| ------------------- | ----------------------------------- | ----------------- |
| **Cirkit Designer** | Arduino/ESP32 自动接线 + 生成驱动代码 + 浏览器仿真 | 创客/教学，不是正式 PCB 设计 |
| **MockFlow / Miro** | 文本→示意图，适合文档展示                       | 无法导出 EDA 文件       |

---

## Flux.ai 深度分析

### Flux Method 四原则

Flux 的设计哲学，也是它的产品定位：

1. **Never start from scratch** — 模板化、可复用组件库，组合已有模块而非从零生成
2. **Work smart not hard** — AI 实时反馈避免设计错误（ERC/DRC 即时提示）
3. **Better collaboration** — 链接分享 + 权限控制，团队协作
4. **Stay in flow** — 单应用集成所有工作流（原理图→PCB→BOM→制造）

### Flux Copilot 的技术架构

| 组件        | 技术实现                                                                         |
| --------- | ---------------------------------------------------------------------------- |
| **AI 模型** | 通用 LLM（含 GPT-5 Beta）+ 自研"Copilot Experts"（封闭微调模型）                            |
| **工具调用**  | `@library` 搜索元件库、`@simulator` SPICE 仿真、`@calculator` 计算参数、`@code` 生成代码       |
| **上下文管理** | 对话线程内维持上下文，用户批准后 AI 直接在编辑器内修改设计                                              |
| **工作流**   | Architecture Design → Component Research → Design Review → Testing Debugging |

### 关键发现：Flux 真正的核心竞争力不是 LLM

Flux 博客《Flux Copilot: Under the Hood》明确说：

> "Copilot is NOT just an LLM — it combines LLM with **grounded structured data**"

真正的竞争壁垒是 **grounding 数据层**：

```
750,000+ 元件库（含数据手册和元数据）
    +
活跃设计上下文（原理图、PCB、网络表、符号）
    +
用户偏好和可复用逻辑（Copilot Knowledge）
    ↓
↓ grounding 后再给通用 LLM
↓ 减少幻觉，提升准确性
```

**结论：你不需要训练专用 LLM**。用通用 LLM（DeepSeek/Claude/GPT）+ 电路领域 grounding 数据 + 好的工具调用设计，效果可以和 Flux 接近。

### Flux 的局限性（我们的机会点）

- Flux **不导出 KiCad 文件**，输出是 Flux 自家私有格式，用户被锁定在平台内
- 需要联网、每月付费，无法自部署
- 闭源，无法对接私有 LLM（不适合企业内网场景）
- 不支持 KiCad 官方生态（嘉立创 SMT 编号、KiCad 原生库）

---

## EDA-AI-Agent 差异化策略

受 Flux.ai 分析启发，确定的差异化方向：

| 维度         | Flux.ai        | EDA-AI-Agent                                  |
| ---------- | -------------- | --------------------------------------------- |
| **开源**     | ❌ 闭源 SaaS      | ✅ 开源，可 GitHub 部署                              |
| **输出格式**   | 私有格式，不导出 KiCad | ✅ 原生 `.kicad_sch`，与 KiCad 完全兼容                |
| **LLM 选择** | 锁定 GPT（封闭）     | ✅ LiteLLM 统一接口，支持 DeepSeek/Claude/Qwen/Ollama |
| **工具协议**   | 私有工具调用         | ✅ 标准 MCP 协议，可扩展                               |
| **验证闭环**   | Flux 内部检查      | ✅ KiCad CLI ERC，错误语义翻译 → 自动修复循环               |
| **中文支持**   | 偏英文            | ✅ 中文优先，嘉立创 JLC 编号对接                           |
| **费用**     | $20/月起         | ✅ 自部署零订阅费                                     |

### 核心技术对应关系

| Flux 的壁垒                           | EDA-AI-Agent 的实现                                          |
| ---------------------------------- | --------------------------------------------------------- |
| 750,000+ 元件库 + datasheet grounding | KiCad 官方符号库索引（SQLite）+ 元件参数 pgvector RAG                  |
| 活跃设计上下文（原理图/网络表）                   | LangGraph AgentState：bom + schematic_content + erc_errors |
| Copilot Knowledge（用户偏好）            | MemorySaver checkpointer + Session 持久化                    |
| @library / @calculator / @code     | MCP tools：compdb_search / kicad_validate / fs_read        |
| 编辑器内直接修改                           | 生成 `.kicad_sch` 文本文件，KiCad 用户自行打开                         |

---

## 面向 Flux 对齐的四阶段流水线（重新设计）

受 Flux Method 启发，将原有 Pipeline 对齐 Flux 的工作流顺序：

```
Stage 1: Architecture Design（需求分析 + 架构设计）
  输入：自然语言需求
  输出：结构化需求文档 + 顶层架构描述（文字）
  Agent：Req Agent（多轮追问）
  工具：电路知识 RAG（检索相似参考设计）

Stage 2: Component Research（元件选型）
  输入：结构化需求
  输出：BOM 列表（lib_id + 规格 + 供应商 + JLC 编号）
  Agent：Design Agent（RAG 驱动选型）
  工具：compdb_search（pgvector / SQLite FTS5）

Stage 3: Schematic Generation（原理图生成）
  输入：BOM + 需求
  输出：.kicad_sch S-expression 文本
  Agent：KiCad Gen Agent（模板填充 + LLM 参数生成）
  工具：S-expression 模板引擎、kicad_validate

Stage 4: Design Review & Verification（设计评审）
  输入：.kicad_sch
  输出：ERC 报告 + 中文错误解释 + 修正原理图（最多 3 次循环）
  Agent：Validation Agent
  工具：KiCad CLI ERC / DRC
```

### 关键升级：S-expression 模板引擎

受 Flux "Never start from scratch" 原则启发：

```
预定义可复用子电路模块（S-expression 模板）：
  - LDO_5V_to_3V3_template
  - NE555_astable_oscillator_template
  - I2C_sensor_interface_template（含 4.7kΩ 上拉）
  - TMOSFET_reverse_protection_template
  - STM32F4_minimal_boot_circuit_template

Agent 选型时：
  复杂电路 → 从模块库组合（不从零生成）
  简单电路 → LLM 直接生成 S-expression
```

### 关键升级：ERC 错误语义翻译层

这是 EDA-AI-Agent 相对 Flux 的独特价值点：

```
KiCad ERC 原始输出：
  "pin_type mismatch at U1 pin 14"

EDA-AI-Agent 翻译后：
  "STM32 的 BOOT0 引脚（U1 Pin 14）需要通过 10kΩ 下拉电阻
   接 GND，否则芯片上电后进入 Bootloader 模式无法正常启动。
   建议：在 BOOT0 和 GND 之间添加 R_BOOT0（10kΩ）。"
```

---

## 当前实现状态（截至 2026-05-21）

- ✅ LangGraph StateGraph Orchestrator（主循环 + 状态管理）
- ✅ 四个 Subagent（Req / Design / KiCad Gen / Validation）
- ✅ MCP Server（stdio 子进程，6 个工具）
- ✅ pgvector RAG（EDB_PG_URL 启用）+ SQLite FTS5 fallback
- ✅ FastAPI WebSocket 后端
- ✅ React + TypeScript 前端
- ✅ E2E 集成测试（test_e2e_pipeline.py）
- ⬜ S-expression 模板引擎（子电路模块库）
- ⬜ ERC 错误语义翻译层（中文 + 修复建议）
- ⬜ KiCad 官方符号库全量索引（17,000+ lib_id）