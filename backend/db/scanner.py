"""
First-run scanner: find user's KiCad symbol libraries and merge into components.db.
Called once from main.py on startup if config.db_last_scanned is None.
"""
from __future__ import annotations
import json, platform, sqlite3
from datetime import datetime, timezone
from pathlib import Path

from backend.config import load_config, save_config
from backend.db.build_index import parse_sym_file
from backend.tools.component_db import DB_PATH


def _default_kicad_sym_dirs() -> list[Path]:
    system = platform.system()
    candidates = []
    if system == "Darwin":
        candidates = [
            Path("/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols"),
            Path.home() / "Documents/KiCad/8.0/symbols",
        ]
    elif system == "Windows":
        candidates = [
            Path("C:/Program Files/KiCad/8.0/share/kicad/symbols"),
            Path.home() / "Documents/KiCad/8.0/symbols",
        ]
    else:  # Linux
        candidates = [
            Path("/usr/share/kicad/symbols"),
            Path.home() / ".local/share/kicad/8.0/symbols",
        ]
    return [p for p in candidates if p.exists()]


def scan_and_merge() -> int:
    """Scan user's KiCad libraries and upsert into components.db. Returns count of new rows."""
    dirs = _default_kicad_sym_dirs()
    if not dirs:
        print("No KiCad symbol directories found — skipping scan.")
        return 0

    con = sqlite3.connect(DB_PATH)
    added = 0
    try:
        for sym_dir in dirs:
            # KiCad 10: directory-per-library format
            symdir_dirs = list(sym_dir.glob("*.kicad_symdir"))
            if symdir_dirs:
                for lib_dir in sorted(symdir_dirs):
                    for sym_file in sorted(lib_dir.glob("*.kicad_sym")):
                        try:
                            row = parse_sym_file(sym_file)
                            if row is not None:
                                cur = con.execute(
                                    "INSERT OR IGNORE INTO components VALUES (:lib_id,:name,:description,:keywords,:category,:pin_count,:datasheet_url,:pins_json)",
                                    row,
                                )
                                added += cur.rowcount
                        except Exception as e:
                            print(f"Scanner: skipping {sym_file.name}: {e}")
            else:
                # KiCad 8.x flat-library format — parse_sym_file doesn't support it
                print(f"Scanner: {sym_dir} uses KiCad 8.x flat format — skipping (not supported)")
        con.commit()
    finally:
        con.close()

    cfg = load_config()
    cfg.db_last_scanned = datetime.now(timezone.utc).isoformat()
    save_config(cfg)
    print(f"Scanner: added {added} symbols from user KiCad libraries.")
    return added
