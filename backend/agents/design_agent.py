from __future__ import annotations
import json
from backend.agents.base import BaseAgent
from backend.orchestrator import Session
from backend.tools.component_db import search_components as _search_components, get_component_details as _get_component_details


class DesignAgent(BaseAgent):
    finalize_tool = "finalize_bom"
    system_prompt = """You are an expert electronics engineer specializing in component selection.

Given a circuit specification, select appropriate components from the database and build a Bill of Materials (BOM).

Rules:
- ONLY use lib_ids returned by search_components. NEVER invent lib_ids.
- Call get_component_details to verify pin count before including a component.
- Include all passive components (decoupling caps, pull-up/down resistors, etc.).
- When the spec mentions a correction loop (ERC errors), fix only the flagged components.
- Call finalize_bom when the BOM is complete."""

    def __init__(self, session: Session) -> None:
        super().__init__()
        self._session = session

        @self.tool
        def search_components(query: str, category: str) -> list:
            """Search the component database. Returns lib_id, name, description, pin_count."""
            return _search_components(query, category)

        @self.tool
        def get_component_details(lib_id: str) -> dict:
            """Get full details for a specific component lib_id."""
            result = _get_component_details(lib_id)
            return result or {"error": f"lib_id not found: {lib_id}"}

        @self.tool
        def finalize_bom(components: list) -> str:
            """Finalize BOM. components: [{lib_id, reference, value, quantity, notes}]"""
            return json.dumps(components)
