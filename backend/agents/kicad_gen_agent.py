from __future__ import annotations
import json, tempfile
from pathlib import Path

from backend.agents.base import BaseAgent
from backend.orchestrator import Session
from backend.tools.component_db import get_component_pins as _get_component_pins
from backend.tools.schematic_writer import SchematicWriter, validate_sexp


class KiCadGenAgent(BaseAgent):
    finalize_tool = "write_schematic"
    system_prompt = """You are a KiCad schematic generation expert.

Given a BOM, generate a valid KiCad 7 .kicad_sch S-expression file.

Steps:
1. Call get_component_pins for each component to learn its pin numbers and names.
2. Use write_schematic with the complete file content.

The .kicad_sch format:
- Starts with: (kicad_sch (version 20230121) (generator eda_ai_agent)
- Each symbol: (symbol (lib_id "X:Y") (at X Y 0) (unit 1) (in_bom yes) (on_board yes) (uuid "...") (property "Reference" "R1" ...) (property "Value" "10k" ...))
- Wires: (wire (pts (xy X1 Y1) (xy X2 Y2)) (stroke (width 0) (type default)) (uuid "..."))
- Ends with: )

Place components on a grid of 2.54mm steps. Reference designators: R1,R2... C1,C2... U1,U2...
Connect power pins to VCC/GND power symbols."""

    def __init__(self, session: Session) -> None:
        super().__init__()
        self._session = session
        if session._tmp_dir_obj is None:
            session._tmp_dir_obj = tempfile.TemporaryDirectory(prefix="eda_sch_")
        self._tmp_dir = session._tmp_dir_obj.name

        @self.tool
        def get_component_pins(lib_id: str) -> list:
            """Get pin data for a component. Returns [{name, number}]."""
            return _get_component_pins(lib_id)

        @self.tool
        def write_schematic(content: str) -> str:
            """Write the .kicad_sch content to disk. Returns file path."""
            if not validate_sexp(content):
                return "Error: unbalanced parentheses in schematic content"
            path = Path(self._tmp_dir) / "output.kicad_sch"
            path.write_text(content, encoding="utf-8")
            self._session.state.schematic_path = str(path)
            return str(path)
