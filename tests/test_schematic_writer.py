# tests/test_schematic_writer.py
import pytest
from backend.tools.schematic_writer import (
    SchematicWriter,
    validate_sexp,
    SchematicError,
)

def test_validate_balanced_parens():
    assert validate_sexp("(a (b c) (d e))") is True

def test_validate_unbalanced_parens():
    assert validate_sexp("(a (b c)") is False

def test_validate_unbalanced_extra_close():
    assert validate_sexp("(a b))") is False

def test_writer_builds_minimal_schematic():
    w = SchematicWriter()
    w.add_symbol("R1", "Device:R", x=100.0, y=100.0, value="10k")
    w.add_symbol("C1", "Device:C", x=120.0, y=100.0, value="100nF")
    content = w.build()
    assert "(kicad_sch" in content
    assert 'Device:R' in content
    assert 'Device:C' in content
    assert "R1" in content
    assert validate_sexp(content) is True

def test_writer_raises_on_invalid_lib_id(monkeypatch):
    import backend.tools.schematic_writer as sw_mod
    monkeypatch.setattr(sw_mod, "lib_id_exists", lambda _: False)
    w = SchematicWriter(validate_lib_ids=True)
    with pytest.raises(SchematicError, match="lib_id not found"):
        w.add_symbol("R1", "FakeLib:FakeChip", x=0.0, y=0.0, value="x")
