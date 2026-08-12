# -*- coding: utf-8 -*-
"""Copy the Devanagari original text from the Hindi DB into En/Ru.

The Hindi edition is the only one with the OCR'd Devanagari originals
(`verses.original_text_devanagari`, 654/777 verses). English and Russian have
the same verse rows keyed by (book_id, ref_display), so each empty En/Ru row
is filled from the matching Hindi verse. `original_text` (transliteration) is
left alone -- En/Ru already carry the same 223/219 rows as Hindi.

Usage:
  python scripts/copy_devanagari.py            # report only
  python scripts/copy_devanagari.py --apply    # write the DBs (after backup)
"""
import shutil
import sqlite3
import sys

EN = r"C:\Users\austr\bhavanasara_sangraha\assets\db\Bhavanasara-Sangraha_En.sqlite"
RU = r"C:\Users\austr\bhavanasara_sangraha\assets\db\Bhavanasara-Sangraha_Ru.sqlite"
HI = r"C:\Users\austr\bhavanasara_sangraha\assets\db\Bhavanasara-Sangraha_Hi.sqlite"


def connect(p):
    c = sqlite3.connect(p)
    c.row_factory = sqlite3.Row
    c.text_factory = lambda b: b.decode("utf-8", "replace")
    return c


def main():
    apply = "--apply" in sys.argv

    hi = connect(HI)
    hi_rows = hi.execute(
        "SELECT book_id, ref_display, original_text_devanagari FROM verses"
    ).fetchall()
    hi_map = {(r["book_id"], r["ref_display"]): r["original_text_devanagari"]
              for r in hi_rows}
    hi.close()

    for path in (EN, RU):
        shutil.copyfile(path, path + ".bak-devanagari")
        print("backup ->", path + ".bak-devanagari")

        con = connect(path)
        cur = con.cursor()
        verses = cur.execute(
            "SELECT id, book_id, ref_display, original_text_devanagari "
            "FROM verses"
        ).fetchall()

        gains = 0
        for v in verses:
            if v["original_text_devanagari"]:
                continue
            devanagari = hi_map.get((v["book_id"], v["ref_display"]), "")
            if not devanagari:
                continue
            if apply:
                cur.execute(
                    "UPDATE verses SET original_text_devanagari = ? WHERE id = ?",
                    (devanagari, v["id"]),
                )
            gains += 1

        if apply:
            con.commit()

        filled = cur.execute(
            "SELECT COUNT(*) FROM verses "
            "WHERE original_text_devanagari IS NOT NULL "
            "AND original_text_devanagari != ''"
        ).fetchone()[0]
        print(f"{path}: {gains} verses to copy, now {filled} filled")
        con.close()


if __name__ == "__main__":
    main()
