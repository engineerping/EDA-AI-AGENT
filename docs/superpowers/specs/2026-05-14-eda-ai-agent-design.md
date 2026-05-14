# EDA-AI-Agent Design Spec

**Date:** 2026-05-14  
**Status:** Approved

---

## 1. Problem & Goal

Users describe a circuit they want to build in plain language. EDA-AI-Agent guides them through requirements, selects real KiCad components, generates a valid `.kicad_sch` schematic file, runs ERC validation, and renders a live preview in the browser. Users bring their own LLM API key and can use any provider.

---

## 2. Platform

| Decision       | Choice                                                      |
| -------------- | ----------------------------------------------------------- |
| Deployment     | Local — runs on user's machine, accessed via browser        |
| Backend        | Python 3.11+ · FastAPI · Uvicorn                            |
| Frontend       | React (TypeScript) · Vite                                   |
| AI routing     | LiteLLM — any provider via model string + API key           |
| Config storage | `~/.eda-agent/config.json` — never sent to browser          |
| Future         | LangGraph state machine (deferred until pipeline is stable) |

---

## 3. System Architecture

```
Browser (React SPA @ localhost:5173)
    ↕ WebSocket (streaming) + REST
FastAPI Server (@ localhost:8000)
    └── Orchestrator
            ├── Req Agent
            ├── Design Agent
            ├── KiCad Gen Agent
            └── Validation Agent
                    ↕
            Tools Layer
                ├── Component DB (SQLite)
                ├── KiCad CLI (subprocess)
                └── LiteLLM Router
```

---

## 4. Project File Structure

```
EDA-AI-AGENT/
├── backend/
│   ├── main.py                  # FastAPI app, WebSocket endpoint
│   ├── orchestrator.py          # ReAct loop, session state, agent routing
│   ├── agents/
│   │   ├── base.py              # BaseAgent(system_prompt, tools, run())
│   │   ├── req_agent.py         # Requirement elicitation
│   │   ├── design_agent.py      # Component selection from DB
│   │   ├── kicad_gen_agent.py   # .kicad_sch S-expression generation
│   │   └── validation_agent.py  # ERC run + error translation
│   ├── tools/
│   │   ├── component_db.py      # SQLite lookup (fuzzy search by description)
│   │   ├── kicad_cli.py         # Subprocess wrapper: erc, export
│   │   └── schematic_writer.py  # Builds valid .kicad_sch S-expression
│   ├── db/
│   │   ├── components.db        # Bundled SQLite index (~17k symbols, ships with app)
│   │   └── scanner.py           # Scans user's KiCad install, merges into DB
│   └── config.py                # ~/.eda-agent/config.json read/write
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── ChatPanel.tsx        # Message list + input box + stage progress bar
│   │   │   ├── SchematicViewer.tsx  # KiCanvas WebGL embed
│   │   │   └── SettingsModal.tsx    # Provider / API key / KiCad path config
│   │   ├── hooks/
│   │   │   └── useAgentSocket.ts    # WebSocket connection + message stream
│   │   └── api/
│   │       └── client.ts            # REST calls (download schematic, read config)
│   ├── package.json
│   └── vite.config.ts               # Proxy /api and /ws to localhost:8000
├── kicad_symbols/               # Git submodule: official KiCad symbol library
├── docs/
│   └── superpowers/specs/
│       └── 2026-05-14-eda-ai-agent-design.md
└── pyproject.toml               # deps: fastapi, litellm, uvicorn, aiosqlite
```

---

## 5. Agent Pipeline

Each agent has: `system_prompt`, `tools: list[Tool]`, and `run(context) -> AgentResult`. Agents exit by calling their **finalize tool** — an explicit, unambiguous exit condition.

### 5.1 Session State

```python
@dataclass
class SessionState:
    requirements: dict | None = None   # set by Req Agent
    bom: list[Component] | None = None  # set by Design Agent
    schematic_path: str | None = None   # set by KiCad Gen Agent
    erc_report: ERCReport | None = None # set by Validation Agent
    iteration_count: int = 0
    correction_attempts: int = 0
```

### 5.2 Req Agent

- **Goal:** Extract a complete, unambiguous circuit specification.
- **Tools:** `ask_user(question: str)`, `finalize_requirements(spec: dict)`
- **Exit:** calls `finalize_requirements` → writes `session.requirements`
- **Behavior:** Asks one question at a time. Covers: function, input voltage, output voltage/current, form factor, cost sensitivity, any specific ICs preferred.

### 5.3 Design Agent

- **Goal:** Select a real, validated BOM from the Component DB.
- **Tools:** `search_components(query: str, category: str)`, `get_component_details(lib_id: str)`, `finalize_bom(components: list)`
- **Exit:** calls `finalize_bom` → writes `session.bom`
- **Constraint:** All `lib_id` values **must** exist in Component DB. Agent cannot invent `lib_id`s. Design Agent is re-invoked (max 3 times) if Validation Agent finds errors traceable to wrong component selection.

### 5.4 KiCad Gen Agent

- **Goal:** Generate a valid `.kicad_sch` S-expression file from the BOM.
- **Tools:** `get_component_pins(lib_id: str)`, `write_schematic(content: str)`
- **Exit:** calls `write_schematic` → writes `session.schematic_path`
- **Behavior:** Fetches pin data for each BOM component before placing symbols. Uses `schematic_writer.py` helper to ensure syntactically valid S-expression output.

### 5.5 Validation Agent

- **Goal:** Run KiCad CLI ERC and translate errors to human-readable explanations.
- **Tools:** `run_erc(schematic_path: str)`, `translate_erc_error(error: str, context: str)`
- **Exit:** writes `session.erc_report`
- **Behavior:** If errors found, returns translated errors to Orchestrator. Orchestrator increments `correction_attempts` and re-routes to Design Agent if `correction_attempts < 3`. "3 attempts" means the full Design→Gen→Validation cycle may repeat up to 3 times after the initial pass (4 total ERC runs max). After 3 failed correction cycles, surfaces remaining errors to user.

### 5.6 Orchestrator

- Runs the top-level ReAct loop.
- Routes to the correct sub-agent based on `SessionState`.
- Streams all agent token output to browser via WebSocket.
- Enforces iteration budget: max 20 total LLM calls per session.
- On completion: sends `.kicad_sch` content, BOM table, and ERC summary to browser.

---

## 6. Component Database

| Source                  | Contents                                             | When built                                   |
| ----------------------- | ---------------------------------------------------- | -------------------------------------------- |
| Bundled `components.db` | ~17,000 official KiCad symbols                       | Ships with app (pre-built at dev time)       |
| User lib scan           | User's locally installed KiCad symbols + custom libs | On first launch, merged into `components.db` |

**Schema:**

```sql
CREATE TABLE components (
    lib_id TEXT PRIMARY KEY,   -- e.g. "Device:LED", "MCU_ST_STM32F4:STM32F405RGTx"
    name TEXT,
    description TEXT,
    keywords TEXT,
    category TEXT,
    pin_count INTEGER,
    datasheet_url TEXT
);
CREATE VIRTUAL TABLE components_fts USING fts5(lib_id, name, description, keywords);
```

**Lookup:** Design Agent searches via FTS5 full-text search on description + keywords. Returns top 5 matches with `lib_id`, `description`, and `pin_count` for agent to choose from.

---

## 7. KiCad Integration

- **KiCad CLI path:** configured in Settings, auto-detected on macOS/Linux/Windows.
- **ERC command:** `kicad-cli sch erc --output erc_report.json <schematic.kicad_sch>`
- **KiCanvas:** loaded via CDN `<script>` tag in the React app. Renders `.kicad_sch` content directly in a `<canvas>` element — no KiCad installation required for preview.
- **ERC output format:** JSON (KiCad 7+). Validation Agent parses errors and uses LLM to translate each error code + context into a human-readable fix suggestion.

---

## 8. Frontend

### 8.1 Layout

Two-panel layout:

- **Left (40%):** Chat panel — message stream, stage progress bar (Requirements → Design → Generation → Validation), input box.
- **Right (60%):** Schematic Viewer — KiCanvas embed, download buttons (`.kicad_sch`, `BOM.csv`), ERC status bar (error count, component count, net count).

Header: app name, active model name pill, settings gear icon.

### 8.2 WebSocket Protocol

```typescript
type PipelineStage = 'requirements' | 'design' | 'generation' | 'validation' | 'done'

// Server → Client messages
type ServerMessage =
  | { type: 'token'; content: string }           // streaming token
  | { type: 'stage'; stage: PipelineStage }       // stage transition
  | { type: 'schematic'; content: string }        // .kicad_sch file content
  | { type: 'bom'; items: BOMItem[] }             // BOM table data
  | { type: 'erc'; report: ERCReport }            // ERC results
  | { type: 'error'; message: string }            // agent error

// Client → Server messages
type ClientMessage =
  | { type: 'user_message'; content: string }
  | { type: 'new_session' }
```

### 8.3 Settings Modal

Fields:

1. **Model** — LiteLLM format string (e.g. `anthropic/claude-opus-4-7`, `openai/gpt-4o`, `ollama/llama3`)
2. **API Key** — stored in `~/.eda-agent/config.json`, masked in UI
3. **Base URL** — optional, for Ollama or custom OpenAI-compatible endpoints
4. **KiCad CLI Path** — with auto-detect button
5. **Component Library** — scan status + Re-scan button

---

## 9. Configuration

`~/.eda-agent/config.json`:

```json
{
  "model": "anthropic/claude-opus-4-7",
  "api_key": "sk-ant-...",
  "base_url": null,
  "kicad_cli_path": "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli",
  "db_last_scanned": "2026-05-14T10:00:00Z"
}
```

Config is read/written only by `backend/config.py`. The frontend reads a **sanitized** version (API key replaced with `"***"`) via `GET /api/config`. The frontend writes config via `POST /api/config` — the backend validates and writes the file.

---

## 10. Error Handling

| Scenario                          | Behavior                                                                         |
| --------------------------------- | -------------------------------------------------------------------------------- |
| No API key configured             | App shows settings modal on first launch                                         |
| LLM API error (rate limit / auth) | WebSocket sends `{ type: 'error' }`, user sees inline message                    |
| KiCad CLI not found               | Validation Agent skips ERC, notes "KiCad not configured" in ERC status bar       |
| ERC errors after 3 attempts       | Remaining errors surfaced to user with translation, schematic still downloadable |
| Hallucinated `lib_id`             | Design Agent `search_components` returns no match → agent must search again      |

---

## 11. Out of Scope (MVP)

- PCB layout / autorouting (post-MVP)
- Multi-session history / project save
- Collaborative editing
- Cloud hosting / SaaS
- LangGraph state machine (deferred until pipeline is stable)
- Custom symbol library creation
