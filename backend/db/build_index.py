"""
Dev script: parse kicad_symbols/**/*.kicad_sym → backend/db/components.db

KiCad 10 uses a "directory-per-library" format:
  kicad_symbols/<LibName>.kicad_symdir/<ComponentName>.kicad_sym

Each .kicad_sym file contains exactly one symbol definition.
Category is derived from the .kicad_symdir directory name.
lib_id is "<Category>:<ComponentName>" (e.g. "Device:R").

Run once from project root: python -m backend.db.build_index
"""
from __future__ import annotations
import json, re, sqlite3
from pathlib import Path

SYMBOLS_DIR = Path("kicad_symbols")
DB_PATH = Path("backend/db/components.db")
SCHEMA_PATH = Path("backend/db/schema.sql")


def parse_sym_file(path: Path) -> dict | None:
    """
    Extract symbol metadata from a single-symbol .kicad_sym file.

    KiCad 10 format: each file contains one top-level (kicad_symbol_lib ...)
    with one (symbol "<name>" ...) inside it.
    Properties use (property "Description" ...), (property "ki_keywords" ...),
    (property "Datasheet" ...).
    Pins live inside sub-symbols like (symbol "R_1_1" ...).
    """
    # Category comes from the parent directory, e.g. "Device.kicad_symdir" → "Device"
    category = path.parent.name.removesuffix(".kicad_symdir")
    # Component name is the file stem, e.g. "R.kicad_sym" → "R"
    name = path.stem
    lib_id = f"{category}:{name}"

    text = path.read_text(encoding="utf-8", errors="ignore")

    description = _extract_property(text, "Description") or ""
    keywords = _extract_property(text, "ki_keywords") or ""
    datasheet = _extract_property(text, "Datasheet") or ""
    if datasheet in ("~", ""):
        datasheet = ""

    # Extract pins: in KiCad 10 single-symbol files, (name "...") and (number "...")
    # only appear inside (pin ...) blocks (the top-level pin_names/pin_numbers
    # directives don't use quoted strings).  They appear in pairs and in order,
    # so a simple parallel findall is safe and avoids multi-level paren matching.
    pin_names = re.findall(r'\(name\s+"([^"]*)"', text)
    pin_numbers = re.findall(r'\(number\s+"([^"]*)"', text)

    pin_data = [{"name": p, "number": n} for p, n in zip(pin_names, pin_numbers)]

    return {
        "lib_id": lib_id,
        "name": name,
        "description": description,
        "keywords": keywords,
        "category": category,
        "pin_count": len(pin_data),
        "datasheet_url": datasheet,
        "pins_json": json.dumps(pin_data),
    }


def _extract_property(text: str, key: str) -> str | None:
    """Extract the value of a KiCad property by name."""
    m = re.search(rf'\(property\s+"{re.escape(key)}"\s+"([^"]*)"', text)
    return m.group(1) if m else None


def build(symbols_dir: Path = SYMBOLS_DIR, db_path: Path = DB_PATH) -> int:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    con = sqlite3.connect(db_path)
    con.executescript(SCHEMA_PATH.read_text())

    total = 0
    # KiCad 10: libraries are directories named *.kicad_symdir
    for lib_dir in sorted(symbols_dir.glob("*.kicad_symdir")):
        sym_files = sorted(lib_dir.glob("*.kicad_sym"))
        rows = []
        for sym_file in sym_files:
            row = parse_sym_file(sym_file)
            if row is not None:
                rows.append(row)

        if rows:
            con.executemany(
                "INSERT OR IGNORE INTO components VALUES "
                "(:lib_id,:name,:description,:keywords,:category,:pin_count,:datasheet_url,:pins_json)",
                rows,
            )
            total += len(rows)
            print(f"  {lib_dir.name.removesuffix('.kicad_symdir')}: {len(rows)} symbols")

    con.commit()
    con.close()
    print(f"\nTotal: {total} symbols → {db_path}")
    return total


if __name__ == "__main__":
    build()
