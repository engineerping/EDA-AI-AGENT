from __future__ import annotations
import uuid as _uuid

from backend.tools.component_db import lib_id_exists


class SchematicError(Exception):
    pass


def validate_sexp(text: str) -> bool:
    depth = 0
    for ch in text:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth < 0:
                return False
    return depth == 0


def _uid() -> str:
    return str(_uuid.uuid4())


def _esc(s: str) -> str:
    return s.replace('\\', '\\\\').replace('"', '\\"')


class SchematicWriter:
    def __init__(self, validate_lib_ids: bool = False):
        self._validate = validate_lib_ids
        self._symbols: list[dict] = []
        self._wires: list[tuple[float, float, float, float, str]] = []
        self._power_symbols: list[dict] = []

    def add_symbol(
        self,
        reference: str,
        lib_id: str,
        x: float,
        y: float,
        value: str,
        angle: float = 0.0,
    ) -> None:
        if self._validate and not lib_id_exists(lib_id):
            raise SchematicError(f"lib_id not found in component DB: {lib_id}")
        self._symbols.append(
            {"ref": reference, "lib_id": lib_id, "x": x, "y": y, "value": value, "angle": angle, "uuid": _uid()}
        )

    def add_wire(self, x1: float, y1: float, x2: float, y2: float) -> None:
        self._wires.append((x1, y1, x2, y2, _uid()))

    def add_power(self, net: str, x: float, y: float) -> None:
        lib_id = f"power:{net.upper()}"
        if self._validate and not lib_id_exists(lib_id):
            raise SchematicError(f"lib_id not found in component DB: {lib_id}")
        self._power_symbols.append({"lib_id": lib_id, "net": net, "x": x, "y": y, "uuid": _uid()})

    def build(self) -> str:
        lines: list[str] = [
            '(kicad_sch (version 20230121) (generator eda_ai_agent)',
            '  (paper "A4")',
            '  (lib_symbols)',
        ]
        for sym in self._symbols + self._power_symbols:
            ref = sym.get("ref", sym.get("net", "PWR"))
            val = sym.get("value", sym.get("net", ""))
            lib_id = sym["lib_id"]
            x, y = sym["x"], sym["y"]
            angle = sym.get("angle", 0.0)
            uid = sym["uuid"]
            lines += [
                f'  (symbol (lib_id "{_esc(lib_id)}") (at {x:.2f} {y:.2f} {angle:.0f}) (unit 1)',
                f'    (in_bom yes) (on_board yes)',
                f'    (uuid "{uid}")',
                f'    (property "Reference" "{_esc(ref)}" (at {x+2.54:.2f} {y-1.27:.2f} 0)',
                f'      (effects (font (size 1.27 1.27))))',
                f'    (property "Value" "{_esc(val)}" (at {x+2.54:.2f} {y+1.27:.2f} 0)',
                f'      (effects (font (size 1.27 1.27))))',
                f'  )',
            ]
        for (x1, y1, x2, y2, uid) in self._wires:
            lines += [
                f'  (wire (pts (xy {x1:.2f} {y1:.2f}) (xy {x2:.2f} {y2:.2f}))',
                f'    (stroke (width 0) (type default))',
                f'    (uuid "{uid}")',
                f'  )',
            ]
        lines.append(')')
        return "\n".join(lines)
