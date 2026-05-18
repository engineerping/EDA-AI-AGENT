from __future__ import annotations
import json
from backend.agents.base import BaseAgent
from backend.orchestrator import Session


class ReqAgent(BaseAgent):
    finalize_tool = "finalize_requirements"
    system_prompt = """You are an electronics requirements analyst. Your job is to gather a complete, unambiguous circuit specification from the user.

Ask ONE clarifying question at a time. Cover these topics (but only ask if still unclear):
1. Circuit function (what does it do?)
2. Input voltage source and range
3. Output voltage and maximum current
4. Form factor / size constraints
5. Cost sensitivity (hobbyist vs commercial)
6. Any specific ICs or components preferred

Once you have enough information (minimum: function, input, output), call finalize_requirements with the spec.
Do NOT ask redundant questions. Be concise."""

    def __init__(self, session: Session) -> None:
        super().__init__()
        self._session = session

        @self.tool
        async def ask_user(question: str) -> str:
            """Ask the user a clarifying question and return their answer."""
            await self._session.emit_token(f"\n\n{question}\n")
            return await self._session.wait_for_user_input()

        @self.tool
        def finalize_requirements(
            function: str,
            input_voltage: str,
            output_voltage: str,
            output_current_ma: int,
            form_factor: str,
            cost_tier: str,
            notes: str,
        ) -> str:
            """Finalize the circuit requirements when all needed info is collected."""
            spec = {
                "function": function,
                "input_voltage": input_voltage,
                "output_voltage": output_voltage,
                "output_current_ma": output_current_ma,
                "form_factor": form_factor,
                "cost_tier": cost_tier,
                "notes": notes,
            }
            return json.dumps(spec)
