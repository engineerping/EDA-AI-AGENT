import json, pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from backend.tools.kicad_cli import run_erc, ERCResult, KiCadNotFoundError

MOCK_ERC_OUTPUT = json.dumps({
    "schematic": {"error_count": 1, "warning_count": 0},
    "sheets": [{"violations": [
        {"type": "pin_not_connected", "description": "Pin unconnected", "severity": "error",
         "items": [{"description": "U1 pin 14"}]}
    ]}]
})

def test_run_erc_no_kicad_raises():
    with patch("backend.tools.kicad_cli._find_kicad_cli", return_value=None):
        with pytest.raises(KiCadNotFoundError):
            run_erc("/fake/path.kicad_sch")

def test_run_erc_parses_violations(tmp_path):
    sch = tmp_path / "test.kicad_sch"
    sch.write_text("(kicad_sch)")

    def fake_run(cmd, **kwargs):
        out_path = Path(cmd[cmd.index("--output") + 1])
        out_path.write_text(MOCK_ERC_OUTPUT)
        m = MagicMock()
        m.returncode = 0
        return m

    with patch("backend.tools.kicad_cli._find_kicad_cli", return_value="/usr/bin/kicad-cli"), \
         patch("subprocess.run", side_effect=fake_run):
        result = run_erc(str(sch), output_dir=str(tmp_path))

    assert result.error_count == 1
    assert len(result.violations) == 1
    assert "pin_not_connected" in result.violations[0]["type"]

def test_run_erc_clean_schematic(tmp_path):
    sch = tmp_path / "clean.kicad_sch"
    sch.write_text("(kicad_sch)")
    clean_output = json.dumps({"schematic": {"error_count": 0, "warning_count": 0}, "sheets": []})

    def fake_run(cmd, **kwargs):
        out_path = Path(cmd[cmd.index("--output") + 1])
        out_path.write_text(clean_output)
        m = MagicMock(); m.returncode = 0; return m

    with patch("backend.tools.kicad_cli._find_kicad_cli", return_value="/usr/bin/kicad-cli"), \
         patch("subprocess.run", side_effect=fake_run):
        result = run_erc(str(sch), output_dir=str(tmp_path))

    assert result.error_count == 0
    assert result.is_clean
