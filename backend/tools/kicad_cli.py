from __future__ import annotations
import json, platform, shutil, subprocess, tempfile
from dataclasses import dataclass, field
from pathlib import Path

from backend.config import load_config


class KiCadNotFoundError(Exception):
    pass


@dataclass
class ERCResult:
    error_count: int = 0
    warning_count: int = 0
    violations: list[dict] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return self.error_count == 0


def _find_kicad_cli() -> str | None:
    cfg = load_config()
    if cfg.kicad_cli_path and Path(cfg.kicad_cli_path).exists():
        return cfg.kicad_cli_path

    candidates = {
        "Darwin": ["/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"],
        "Windows": ["C:\\Program Files\\KiCad\\8.0\\bin\\kicad-cli.exe"],
        "Linux": ["/usr/bin/kicad-cli"],
    }.get(platform.system(), [])

    for path in candidates:
        if Path(path).exists():
            return path
    return shutil.which("kicad-cli")


def run_erc(schematic_path: str, output_dir: str | None = None) -> ERCResult:
    cli = _find_kicad_cli()
    if not cli:
        raise KiCadNotFoundError(
            "kicad-cli not found. Set kicad_cli_path in Settings or install KiCad."
        )

    with tempfile.TemporaryDirectory() as tmp:
        out_dir = output_dir or tmp
        erc_file = Path(out_dir) / "erc_report.json"
        try:
            subprocess.run(
                [cli, "sch", "erc", "--output", str(erc_file), schematic_path],
                capture_output=True, text=True, check=False,
            )
        except OSError as exc:
            raise KiCadNotFoundError(f"Failed to launch kicad-cli at {cli!r}: {exc}") from exc
        if not erc_file.exists():
            return ERCResult()
        try:
            data = json.loads(erc_file.read_text())
        except json.JSONDecodeError as exc:
            raise ValueError(f"ERC report JSON is malformed: {erc_file}") from exc

    sch_info = data.get("schematic", {})
    violations = [
        v
        for sheet in data.get("sheets", [])
        for v in sheet.get("violations", [])
    ]
    return ERCResult(
        error_count=sch_info.get("error_count", 0),
        warning_count=sch_info.get("warning_count", 0),
        violations=violations,
    )
