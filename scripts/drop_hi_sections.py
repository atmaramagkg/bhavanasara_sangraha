# -*- coding: utf-8 -*-
"""Drop the orphaned OCR structure tables from the Hindi DB.

`hi_sections` and `hi_section_quotes` held the OCR-detected printed headings
and their quotes for the removed "Hindi structure" screens. Nothing reads them
anymore; both are regenerable from scripts/build_hi_sections.py if ever needed.

Usage:
  python scripts/drop_hi_sections.py
"""
import shutil
import sqlite3
import sys

HI = r"C:\Users\austr\bhavanasara_sangraha\assets\db\Bhavanasara-Sangraha_Hi.sqlite"


def main():
    shutil.copyfile(HI, HI + ".bak-drop-hi-sections")
    print("backup ->", HI + ".bak-drop-hi-sections")

    con = sqlite3.connect(HI)
    cur = con.cursor()
    for table in ("hi_section_quotes", "hi_sections"):
        exists = cur.execute(
            "SELECT COUNT(*) FROM sqlite_master "
            "WHERE type = 'table' AND name = ?",
            (table,),
        ).fetchone()[0]
        if exists:
            cur.execute(f"DROP TABLE {table}")
            print("dropped", table)
        else:
            print("absent (already dropped):", table)
    con.commit()
    con.close()


if __name__ == "__main__":
    main()
