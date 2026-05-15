<div align="center">

# EDA-AI-Agent

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Node](https://img.shields.io/badge/Node-22-339933?logo=nodedotjs&logoColor=white)](https://nodejs.org/)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-6-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![LiteLLM](https://img.shields.io/badge/LiteLLM-1.40+-404040?logo=lightning&logoColor=white)](https://www.litellm.ai/)
[![KiCad](https://img.shields.io/badge/KiCad-7/8-000000?logo=kicad&logoColor=white)](https://www.kicad.org/)

[中文](README.md) · English

---

> Describe your circuit in natural language — AI analyzes requirements through multi-turn dialogue, automatically selects components, generates a .kicad_sch formatted schematic text file, then validates it via kicad-cli. The final schematic is previewed directly in the browser and can also be opened in the KiCad software.
For more on KiCad, the most popular open-source EDA (Electronic Design Automation) software, see https://www.kicad.org/.

</div>

---

Feasibility Assessment
Bottom line up front: Yes — with boundaries.

Dimension	Verdict	Detail
Requirements clarification	✅ Fully feasible	LLM's strongest use case
Component selection	✅ Feasible	LLM has deep circuit knowledge
Generating KiCad schematic files	✅ Feasible	.kicad_sch is plain-text S-expression — directly programmable
Auto PCB layout & routing	⚠️ Partially feasible	KiCad has Python API, but auto-layout quality is limited; complex boards need human review
Circuit correctness validation	✅ Feasible	KiCad CLI runs ERC/DRC headlessly and returns reports for agent feedback
Fully commercial-grade, no human review	❌ Not yet realistic	Complex analog, high-speed signals, and EMC design still require an engineer's eye
The core breakthrough is KiCad's file format. .kicad_sch is plain-text S-expression — highly structured and directly learnable and generatable by LLMs. This is the technical foundation that makes the entire agent feasible. KiCad 7/8's .kicad_sch format is structured S-expression text that LLMs can directly generate and modify; KiCad has a built-in Python scripting API (pcbnew) for programmatic PCB operations; and KiCad CLI supports headless ERC/DRC execution with machine-readable output.

---

## How It Works

```
You describe the circuit
    ↓
Requirements Agent        → Multi-turn clarification, structured output
    ↓
Design Agent              → Component selection from local KiCad library, outputs BOM
    ↓
Schematic Generator        → Generates a .kicad_sch formatted text file 
    ↓
ERC Validation Agent       → Runs KiCad CLI checks, auto-corrects up to 3 times
    ↓
Browser preview + download
```

Every agent calls a LLM you configure — OpenAI, Anthropic, DeepSeek, Qwen, and more.

---

## Srchitecture

![EDA-AI-Agent-architecture](./EDA-AI-Agent-architecture.png)

---

## Requirements

### macOS

```bash
# Python 3.12
brew install python@3.12

# Node.js 22 LTS
brew install node@22

# KiCad (optional, needed for ERC)
brew install --cask kicad
```

### Linux (Ubuntu / Debian)

```bash
# Python 3.12
sudo apt update
sudo apt install python3.12 python3.12-venv python3.12-pip

# Node.js 22 LTS
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs

# KiCad (optional)
sudo apt install kicad
```

### Windows

1. **Python 3.12** — Download: [python.org/downloads](https://www.python.org/downloads/) — check **"Add Python to PATH"** during install

2. **Node.js 22 LTS** — Download: [nodejs.org](https://nodejs.org/)

3. **KiCad (optional)** — Download: [kicad.org/download](https://www.kicad.org/download/)

4. Use **Windows Terminal** or **PowerShell** for the commands below.

> KiCad is optional. Without it, ERC is skipped and schematics are still generated and previewed normally.

---

## Quick Start

### 1. Clone the project

```bash
git clone https://github.com/your-org/eda-ai-agent.git
cd eda-ai-agent
```

### 2. Install backend dependencies

```bash
pip3.12 install -e .
```

### 3. Install frontend dependencies

```bash
cd frontend
npm install
cd ..
```

### 4. Start the backend (terminal 1)

```bash
uvicorn backend.main:app --reload --access-log
```

Backend runs at `http://localhost:8000`. Request logs are printed to this terminal in real time.

### 5. Start the frontend (terminal 2)

```bash
cd frontend
npm run dev
```

Frontend runs at `http://localhost:5173` — open it in your browser.

### Stop the services

Press `Ctrl+C` in each terminal running the backend and frontend.

### Viewing logs

Two log streams from the backend:

**Application logs (custom structured output)**

After starting the backend, you'll see real-time entries for:
- WebSocket connect / disconnect
- Each pipeline stage entry and completion
- LLM call counts, ERC results, correction attempts
- Session creation and cleanup

**HTTP access logs (`--access-log` flag enabled above)**

```
127.0.0.1:12345 - "GET /api/config HTTP/1.1" 200
127.0.0.1:23456 - "POST /api/config HTTP/1.1" 200
127.0.0.1:34567 - "POST /api/rescan HTTP/1.1" 200
```

**Persist logs to file (for background runs)**

```bash
nohup uvicorn backend.main:app --reload --access-log > backend.log 2>&1 &
tail -f backend.log
```

---

## Configure Your API Key

Open the app in the browser, click **⚙ Settings** in the top-right corner:

| Field | Description |
|---|---|
| **Model** | Pick from the dropdown list, or type any LiteLLM-format model name |
| **API Key** | Your model's API key (e.g., from the DeepSeek platform) |
| **Base URL** | Only needed for Ollama or custom endpoints, e.g. `http://localhost:11434` |
| **KiCad CLI Path** | Leave empty for auto-detect; if not found ERC is skipped automatically |

Click **Save Settings**.

> **Security:** Your API key is stored locally at `~/.eda-agent/config.json`. It is never sent to any server outside your LLM provider and is never included in the project code.

### Model Examples

```
# DeepSeek
deepseek/deepseek-chat
deepseek/deepseek-reasoner

# Anthropic
anthropic/claude-opus-4-latest
anthropic/claude-sonnet-4-latest

# OpenAI
openai/gpt-4o
openai/o3-mini

# Qwen (requires DashScope key)
tongyi/qwen-plus
tongyi/qwen-max

# Local Ollama (set Base URL to http://localhost:11434)
ollama/qwen2.5
ollama/deepseek-r1
```

---

## Design Your First Circuit

Type a natural-language description in the input box, for example:

> Design a NE555-based 1kHz square wave oscillator that drives an LED

> Design a 5V to 3.3V LDO regulator circuit with 500mA output

> Design an I2C temperature/humidity sensor interface circuit using the SHT31, 3.3V supply

1. The agent will confirm requirements, select components, and generate the schematic — all streamed live in the left panel
2. The right panel renders the schematic preview automatically (powered by [KiCanvas](https://kicanvas.org))
3. Click **↓ .kicad_sch** to download and open the file in KiCad for further editing
4. Click **↓ BOM.csv** to download the bill of materials

---

## Component Library

The project ships with KiCad's official symbol library indexed in SQLite. If you have custom KiCad libraries on your machine, go to Settings → **Re-scan Libraries** to merge them in.

---

## For Developers

### Run tests

```bash
pip3.12 install -e ".[dev]"
python3.12 -m pytest tests/ -v
```

### Project structure

```
backend/
  main.py              FastAPI app + WebSocket handler
  orchestrator.py      Pipeline coordinator + Session management
  agents/
    req_agent.py       Requirements analysis Agent
    design_agent.py    Circuit design Agent
    kicad_gen_agent.py Schematic generation Agent
    validation_agent.py ERC validation Agent
  tools/
    component_db.py   SQLite FTS5 component lookup
    kicad_cli.py      KiCad CLI wrapper
  config.py            Config read/write (~/.eda-agent/config.json)

frontend/
  src/
    components/       React components
    hooks/            useAgentSocket (WebSocket + state)
    api/              REST API client
```