# -*- coding: utf-8 -*-
"""Give the Hindi edition its Devanagari-only originals.

The Hindi app must show each verse as only two parts: the Devanagari original
and the Hindi translation. Two things stand in the way:

  1. 39 verses have only the IAST transliteration (`original_text`), no
     Devanagari. Those are converted with the IAST -> Devanagari converter
     and stored in `original_text_devanagari`.
  2. The IAST transliteration itself (223 verses) is shown between the
     Devanagari and the translation. It is cleared so the Hindi edition is
     Devanagari + Hindi only.

English/Russian databases keep their transliteration and gain the newly
converted Devanagari rows via scripts/copy_devanagari.py.

Usage:
  python scripts/hi_original_cleanup.py            # report only
  python scripts/hi_original_cleanup.py --apply    # write the DB (after backup)
"""
import shutil
import sqlite3
import sys

from iast_to_devanagari import iast_to_devanagari

HI = r"C:\Users\austr\bhavanasara_sangraha\assets\db\Bhavanasara-Sangraha_Hi.sqlite"


def main():
    apply = "--apply" in sys.argv
    sys.path.insert(0, __file__.rsplit("\\", 1)[0] if "\\" in __file__ else ".")

    shutil.copyfile(HI, HI + ".bak-hi-original-cleanup")
    print("backup ->", HI + ".bak-hi-original-cleanup")

    con = sqlite3.connect(HI)
    con.row_factory = sqlite3.Row
    con.text_factory = lambda b: b.decode("utf-8", "replace")
    cur = con.cursor()

    # 1. convert IAST -> Devanagari where Devanagari is missing
    rows = cur.execute(
        "SELECT id, original_text FROM verses "
        "WHERE original_text IS NOT NULL AND original_text != '' "
        "AND (original_text_devanagari IS NULL OR original_text_devanagari = '')"
    ).fetchall()
    converted = 0
    for r in rows:
        dv = iast_to_devanagari(r["original_text"]).strip()
        if not dv:
            continue
        if apply:
            cur.execute(
                "UPDATE verses SET original_text_devanagari = ? WHERE id = ?",
                (dv, r["id"]),
            )
        converted += 1

    # 2. clear the transliteration (Hindi edition shows Devanagari + Hindi only)
    if apply:
        cur.execute("UPDATE verses SET original_text = ''")

    if apply:
        con.commit()

    n_dev = cur.execute(
        "SELECT COUNT(*) FROM verses "
        "WHERE original_text_devanagari IS NOT NULL "
        "AND original_text_devanagari != ''"
    ).fetchone()[0]
    n_cleared = cur.execute(
        "SELECT COUNT(*) FROM verses "
        "WHERE original_text IS NULL OR original_text = ''"
    ).fetchone()[0]
    n_total = cur.execute("SELECT COUNT(*) FROM verses").fetchone()[0]
    print(f"converted IAST -> Devanagari: {converted}")
    print(f"verses with Devanagari: {n_dev}/{n_total}")
    print(f"verses without any transliteration: {n_cleared}/{n_total}")
    con.close()


if __name__ == "__main__":
    main()
