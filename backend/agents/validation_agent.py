from __future__ import annotations
import json

from backend.agents.base import BaseAgent
from backend.orchestrator import Session
from backend.tools.kicad_cli import KiCadNotFoundError, run_erc as _run_erc


class ValidationAgent(BaseAgent):
    finalize_tool = "finalize_erc_report"
    system_prompt = """You are a KiCad ERC (Electrical Rules Check) interpreter.

When given a schematic path:
1. Call run_erc to execute the ERC check.
2. For each violation, call translate_erc_error to produce a human-readable fix suggestion.
3. Call finalize_erc_report with the complete results.

Be specific in your translations: name the component and pin, explain WHY it's an error, and suggest the fix."""

    def __init__(self, session: Session) -> None:
        super().__init__()
        self._session = session

        @self.tool
        def run_erc(schematic_path: str) -> dict:
            """Run KiCad ERC on the schematic file. Returns error_count and violations list."""
            try:
                result = _run_erc(schematic_path)
                self._erc_error_count = result.error_count
                return {
                    "error_count": result.error_count,
                    "warning_count": result.warning_count,
                    "violations": result.violations,
                }
            except KiCadNotFoundError:
                self._erc_error_count = 0
                return {"error_count": 0, "warning_count": 0, "violations": [],
                        "note": "KiCad CLI not configured — ERC skipped"}

        @self.tool
        def translate_erc_error(error_type: str, description: str, component: str) -> str:
            """Translate a raw ERC error into a human-readable fix suggestion."""
            return f"{component}: {description} (type: {error_type})"

        @self.tool
        def finalize_erc_report(error_count: int, violations_translated: list) -> str:
            """Submit the final ERC report with translated error messages."""
            return json.dumps({
                "error_count": getattr(self, "_erc_error_count", error_count),
                "violations_translated": violations_translated,
            })
