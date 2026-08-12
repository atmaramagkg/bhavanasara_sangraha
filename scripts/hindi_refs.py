# -*- coding: utf-8 -*-
"""Rebuild `citations.ref_display` in the Hindi DB using Hindi book titles.

The Hindi edition currently shows transliterated English scripture names in
every citation ref (e.g. "Krsna-bhavanamrtam 1.1-9"). The Hindi translations
of the book titles already exist in `translations` (key = book.title_key,
language = 'hi'), and every verse keeps its own numeric ref in
`verses.ref_display` (e.g. "1.1-9"), so the citation ref can be rebuilt as
"<Hindi title> <numeric ref>" -- the same shape as the English ref, but in
Devanagari.

Usage:
  python scripts/hindi_refs.py            # report only
  python scripts/hindi_refs.py --apply    # write the DB (after backup)
"""
import shutil
import sqlite3
import sys

HI = r"C:\Users\austr\bhavanasara_sangraha\assets\db\Bhavanasara-Sangraha_Hi.sqlite"


def connect(p):
    c = sqlite3.connect(p)
    c.row_factory = sqlite3.Row
    c.text_factory = lambda b: b.decode("utf-8", "replace")
    return c


def main():
    apply = "--apply" in sys.argv

    shutil.copyfile(HI, HI + ".bak-hindi-refs")
    print("backup ->", HI + ".bak-hindi-refs")

    con = connect(HI)
    cur = con.cursor()

    before = cur.execute("SELECT COUNT(*) FROM citations").fetchone()[0]

    # verse numeric ref + the book's Hindi title per citation
    cur.execute(
        """
        SELECT c.id,
               t.translated_text AS hi_title,
               v.ref_display AS verse_ref
        FROM citations c
        JOIN books b ON b.id = c.source_book_id
        JOIN translations t
          ON t.translation_key = b.title_key
         AND t.language_id = (SELECT id FROM languages WHERE code = 'hi')
        JOIN verses v ON v.id = c.source_verse_id
        """
    )
    rows = cur.fetchall()
    assert len(rows) == before, "expected one row per citation"

    updates = 0
    for r in rows:
        new_ref = (r["hi_title"] + " " + r["verse_ref"]).strip()
        if apply:
            cur.execute(
                "UPDATE citations SET ref_display = ? WHERE id = ?",
                (new_ref, r["id"]),
            )
        updates += 1

    if apply:
        con.commit()

    devanagari = sum(
        1
        for r in cur.execute("SELECT ref_display FROM citations")
        if any("\u0900" <= ch <= "\u097f" for ch in r["ref_display"])
    )
    still_ascii = before - devanagari

    print(f"citations: {before} total, {updates} rewritten, "
          f"{still_ascii} without Devanagari")
    for r in cur.execute(
        "SELECT id, ref_display FROM citations ORDER BY id LIMIT 3"
    ):
        print("  sample:", r["ref_display"])
    con.close()


if __name__ == "__main__":
    main()
