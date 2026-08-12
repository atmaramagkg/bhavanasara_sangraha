# -*- coding: utf-8 -*-
"""Curated EN-section -> Hindi-printed-heading mapping + DB application.

The Hindi edition (hi_sections, 62 OCR-detected printed headings) is coarser
than the translated book (129 sections), so the mapping is 1:1 only in places.
This script encodes a hand-curated assignment: EN section id -> hi_sections id
(None where the EN section precedes the first printed heading of its period).

Steps:
  1. writes scripts/section_hindi_heading_map.json  (sec_id -> heading text)
  2. adds `sections.hindi_heading` column to En/Ru/Hi DBs and fills it.
"""
import sys
import json
import sqlite3

EN = r"C:\Users\austr\bhavanasara_sangraha\assets\db\Bhavanasara-Sangraha_En.sqlite"
RU = r"C:\Users\austr\bhavanasara_sangraha\assets\db\Bhavanasara-Sangraha_Ru.sqlite"
HI = r"C:\Users\austr\bhavanasara_sangraha\assets\db\Bhavanasara-Sangraha_Hi.sqlite"
OUT = r"C:\Users\austr\bhavanasara_sangraha\scripts\section_hindi_heading_map.json"

sys.stdout.reconfigure(encoding="utf-8")

# sec_id -> hi_sections.id (None => no printed heading for that EN section)
CURATED = {
    # nishanta
    1: 2, 2: 2, 3: 2, 4: 2, 5: 2, 6: 3, 7: 3, 8: 4, 9: 5, 10: 6,
    # pratah
    11: 8, 12: 8, 13: 9, 14: 10, 15: 10, 16: 11, 17: 11, 18: 12,
    19: 13, 20: 13, 21: 14, 22: 15, 23: 16, 24: 16, 25: 17,
    26: 19, 27: 19, 28: 19, 29: 19, 30: 19, 31: 19, 32: 19, 33: 19, 34: 19,
    # purvahna
    35: None, 36: None, 37: None,
    38: 21, 39: 22, 40: 23, 41: 23, 42: 24, 43: 24, 44: 24,
    45: 25, 46: 26, 47: 27, 48: 27, 49: 27, 50: 27, 51: 27,
    # madhyahna
    52: None, 53: None, 54: None,
    55: 29, 56: 29, 57: 29, 58: 29, 59: 29, 60: 29,
    61: 30, 62: 30, 63: 31, 64: 31, 65: 32, 66: 32,
    67: 33, 68: 34, 69: 35, 70: 36, 71: 37, 72: 37, 73: 37, 74: 37,
    75: 37, 76: 37, 77: 37, 78: 37, 79: 38, 80: 38, 81: 39,
    82: 41, 83: 41, 84: 41, 85: 41, 86: 41, 87: 42, 88: 42,
    89: 45, 90: 45, 91: 45,
    # aparahna
    92: None, 93: None, 94: None, 95: 47, 96: 47,
    # sayahna (no printed headings detected in OCR)
    97: None, 98: None, 99: None, 100: None, 101: None, 102: None,
    # pradosha
    103: 50, 104: 50, 105: 50, 106: 51, 107: 51, 108: 51, 109: 51,
    110: 51, 111: 52, 112: 52, 113: 52, 114: 52, 115: 52,
    # nisha
    116: None, 117: 54, 118: 54, 119: 54, 120: 55, 121: 57, 122: 57,
    123: 57, 124: 59, 125: 60, 126: 61, 127: 61, 128: 62, 129: 62,
}


def connect(p):
    c = sqlite3.connect(p)
    c.row_factory = sqlite3.Row
    c.text_factory = lambda b: b.decode("utf-8", "replace")
    return c


def col_exists(cur, table, col):
    return any(r[1] == col for r in cur.execute(f"PRAGMA table_info({table})"))


def main():
    assert set(CURATED) == set(range(1, 130)), "CURATED must cover sec 1..129"
    hi = connect(HI)
    hs_text = dict(hi.execute("SELECT id, heading_clean FROM hi_sections"))
    for hs_id in CURATED.values():
        if hs_id is not None:
            assert hs_id in hs_text, f"unknown hi_sections id {hs_id}"
    hi.close()

    mapping = {sec_id: (hs_text[hs_id] if hs_id else None)
               for sec_id, hs_id in sorted(CURATED.items())}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=1)
    print("wrote", OUT)

    for path in (EN, RU, HI):
        con = connect(path)
        cur = con.cursor()
        if not col_exists(cur, "sections", "hindi_heading"):
            cur.execute("ALTER TABLE sections ADD COLUMN hindi_heading TEXT")
            print("added column", path)
        for sec_id, heading in mapping.items():
            cur.execute("UPDATE sections SET hindi_heading=? WHERE id=?",
                        (heading, sec_id))
        con.commit()
        filled = cur.execute(
            "SELECT COUNT(*) FROM sections WHERE hindi_heading IS NOT NULL AND hindi_heading != ''"
        ).fetchone()[0]
        print(f"  {path}: {filled}/129 sections have a Hindi heading")
        con.close()


if __name__ == "__main__":
    main()
