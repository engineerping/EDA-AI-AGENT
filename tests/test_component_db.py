# tests/test_component_db.py
import json, pytest, sqlite3
from pathlib import Path
import backend.tools.component_db as db_module

@pytest.fixture
def test_db(tmp_path):
    db_path = tmp_path / "test.db"
    schema = Path("backend/db/schema.sql").read_text()
    con = sqlite3.connect(db_path)
    con.executescript(schema)
    rows = [
        ("Device:R", "R", "Resistor", "resistor res", "Device", 2, "", '[{"name":"~","number":"1"},{"name":"~","number":"2"}]'),
        ("Device:C", "C", "Unpolarized capacitor", "capacitor cap", "Device", 2, "", '[{"name":"~","number":"1"},{"name":"~","number":"2"}]'),
        ("Device:LED", "LED", "Light emitting diode", "LED diode", "Device", 2, "", '[{"name":"K","number":"1"},{"name":"A","number":"2"}]'),
    ]
    con.executemany("INSERT INTO components VALUES (?,?,?,?,?,?,?,?)", rows)
    con.commit()
    con.close()
    return db_path

def test_search_components(test_db, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", test_db)
    results = db_module.search_components("resistor")
    assert any(r["lib_id"] == "Device:R" for r in results)

def test_get_component_details(test_db, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", test_db)
    detail = db_module.get_component_details("Device:LED")
    assert detail["name"] == "LED"
    assert detail["pin_count"] == 2

def test_get_component_pins(test_db, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", test_db)
    pins = db_module.get_component_pins("Device:R")
    assert len(pins) == 2
    assert pins[0]["number"] == "1"

def test_search_returns_empty_for_unknown(test_db, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", test_db)
    results = db_module.search_components("xyznonexistent123")
    assert results == []
