from __future__ import annotations
import asyncio, json, uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from backend.config import load_config, save_config, sanitized_config
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
