"""KiCad tools for MCP server."""
import json
from pathlib import Path
from backend.tools.kicad_cli import run_erc
from backend.tools.schematic_writer import SchematicWriter

def kicad_erc(schematic_path: str) -> str:
    """Run KiCad ERC on a schematic file."""
    result = run_erc(schematic_path)
    return json.dumps({
        "error_count": result.error_count,
        "warning_count": result.warning_count,
        "violations": result.violations,
    })

def kicad_generate_sch(bom: list, output_path: str) -> str:
    """Generate a .kicad_sch file from a BOM."""
    writer = SchematicWriter()
    # Apply BOM items to writer...
    content = writer.build()
    with open(output_path, "w") as f:
        f.write(content)
    return f"Generated schematic: {len(content)} bytes at {output_path}"