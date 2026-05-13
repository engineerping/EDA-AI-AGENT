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