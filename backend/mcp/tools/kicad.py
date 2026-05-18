"""KiCad tools for MCP server."""
import json
from mcp.types import CallToolResult, TextContent
from pathlib import Path
from backend.tools.kicad_cli import run_erc
from backend.tools.schematic_writer import SchematicWriter

def kicad_erc(schematic_path: str) -> CallToolResult:
    """Run KiCad ERC on a schematic file."""
    result = run_erc(schematic_path)
    return CallToolResult(content=[TextContent(type="text", text=json.dumps({
        "error_count": result.error_count,
        "warning_count": result.warning_count,
        "violations": result.violations,
    }))])

def kicad_generate_sch(bom: list, output_path: str) -> CallToolResult:
    """Generate a .kicad_sch file from a BOM."""
    writer = SchematicWriter()
    for item in bom:
        ref = item.get("reference", "U?")
        lib_id = item.get("lib_id", "")
        value = item.get("value", "")
        x = item.get("x", 0.0)
        y = item.get("y", 0.0)
        writer.add_symbol(reference=ref, lib_id=lib_id, x=x, y=y, value=value)
    content = writer.build()
    with open(output_path, "w") as f:
        f.write(content)
    return CallToolResult(content=[TextContent(type="text", text=json.dumps({"status": "ok", "path": output_path, "size": len(content)}))])