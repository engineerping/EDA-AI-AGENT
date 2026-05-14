from __future__ import annotations
import asyncio, json
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from enum import Enum

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
            on_token=lambda t: asyncio.create_task(s.emit_token(t)),
        )
        s.state.iteration_count += 1
        s.state.requirements = json.loads(req_result) if req_result.strip().startswith("{") else {"description": req_result}

        # --- Stage 2: Design ---
        await s.emit_stage(PipelineStage.DESIGN)
        while s.state.correction_attempts <= 3:
            if s.state.iteration_count >= 20:
                await s.send({"type": "error", "message": "Iteration budget exceeded (20 LLM calls)."})
                return
            design_agent = DesignAgent(session=s)
            bom_result = await design_agent.run(
                messages=[{"role": "user", "content": json.dumps(s.state.requirements)}],
                on_token=lambda t: asyncio.create_task(s.emit_token(t)),
            )
            s.state.iteration_count += 1
            s.state.bom = json.loads(bom_result) if bom_result.strip().startswith("[") else []

            # --- Stage 3: KiCad Generation ---
            await s.emit_stage(PipelineStage.GENERATION)
            gen_agent = KiCadGenAgent(session=s)
            sch_result = await gen_agent.run(
                messages=[{"role": "user", "content": json.dumps(s.state.bom)}],
                on_token=lambda t: asyncio.create_task(s.emit_token(t)),
            )
            s.state.iteration_count += 1
            s.state.schematic_content = sch_result

            # --- Stage 4: Validation ---
            await s.emit_stage(PipelineStage.VALIDATION)
            val_agent = ValidationAgent(session=s)
            erc_result = await val_agent.run(
                messages=[{"role": "user", "content": sch_result}],
                on_token=lambda t: asyncio.create_task(s.emit_token(t)),
            )
            s.state.iteration_count += 1
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
