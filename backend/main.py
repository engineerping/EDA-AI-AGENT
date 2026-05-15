from __future__ import annotations
import asyncio, json, uuid, logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path

from backend.config import load_config, save_config, sanitized_config, AgentConfig
from backend.db.scanner import scan_and_merge
from backend.orchestrator import Orchestrator, Session

import logging
import logging.config

# Uvicorn access log format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%H:%M:%S",
)
# Silence noisy third-party loggers
logging.getLogger("uvicorn.access").setLevel(logging.INFO)
logging.getLogger("uvicorn.error").setLevel(logging.INFO)
logging.getLogger("LiteLLM").setLevel(logging.WARNING)
log = logging.getLogger("eda-agent")


@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg = load_config()
    if cfg.db_last_scanned is None:
        log.info("First run — scanning KiCad library...")
        scan_and_merge()
        log.info("Library scan complete.")
    else:
        log.info("Starting EDA-AI-Agent backend.")
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
    log.info("Saving config: model=%s base_url=%s kicad_cli_path=%s",
             payload.get("model"), payload.get("base_url"), payload.get("kicad_cli_path"))
    cfg = load_config()
    for key in ("model", "api_key", "base_url", "kicad_cli_path"):
        if key in payload and payload[key] is not None:
            setattr(cfg, key, payload[key])
    from pydantic import ValidationError
    try:
        cfg = AgentConfig.model_validate(cfg.model_dump())
    except ValidationError as e:
        return JSONResponse({"error": str(e)}, status_code=422)
    save_config(cfg)
    log.info("Config saved successfully.")
    return JSONResponse({"status": "saved"})


@app.post("/api/rescan")
async def rescan():
    log.info("Re-scanning KiCad libraries...")
    added = scan_and_merge()
    log.info("Library scan complete: %d new symbols added.", added)
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
    log.info("[%s] WebSocket connected", session_id)

    async def send(msg: dict) -> None:
        await ws.send_json(msg)

    session = Session(session_id, send)
    _sessions[session_id] = session
    await ws.send_json({"type": "session_id", "session_id": session_id})
    log.info("[%s] Session created", session_id)

    orchestrator_task: asyncio.Task | None = None

    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                log.warning("[%s] Invalid JSON received", session_id)
                await ws.send_json({"type": "error", "message": "Invalid JSON"})
                continue

            msg_type = msg.get("type")
            if msg_type == "new_session":
                log.info("[%s] new_session — cancelling orchestrator", session_id)
                if orchestrator_task and not orchestrator_task.done():
                    orchestrator_task.cancel()
                    try:
                        await orchestrator_task
                    except asyncio.CancelledError:
                        pass
                orchestrator_task = None
                if session._tmp_dir_obj is not None:
                    session._tmp_dir_obj.cleanup()
                session = Session(session_id, send)
                _sessions[session_id] = session
                log.info("[%s] Session reset", session_id)

            elif msg_type == "user_message":
                log.info("[%s] user_message received (len=%d)", session_id, len(msg.get("content", "")))
                if orchestrator_task is None or orchestrator_task.done():
                    log.info("[%s] Starting orchestrator", session_id)
                    orchestrator_task = asyncio.create_task(
                        Orchestrator(session).run(msg["content"])
                    )
                else:
                    log.info("[%s] Passing user input to in-flight orchestrator", session_id)
                    await session.put_user_input(msg["content"])

    except WebSocketDisconnect:
        log.info("[%s] WebSocket disconnected", session_id)
    finally:
        log.info("[%s] Cleaning up session", session_id)
        _sessions.pop(session_id, None)
        if orchestrator_task and not orchestrator_task.done():
            orchestrator_task.cancel()
        if session._tmp_dir_obj is not None:
            session._tmp_dir_obj.cleanup()
        log.info("[%s] Session cleaned up", session_id)
