# -*- coding: utf-8 -*-
"""Backfill the English UI strings missing from the Russian DB.

The Ru DB only carries Russian UI text: its English rows (language_id = 1)
cover 116 keys, while the En DB has 471. Switching the Ru app to English
therefore shows raw keys (e.g. `section.nishanta_1.1.title`) for everything
missing. This copies every English row the En DB has that the Ru DB lacks.

Usage:
  python scripts/backfill_ru_english.py
"""
import shutil
import sqlite3

EN = r"C:\Users\austr\bhavanasara_sangraha\assets\db\Bhavanasara-Sangraha_En.sqlite"
RU = r"C:\Users\austr\bhavanasara_sangraha\assets\db\Bhavanasara-Sangraha_Ru.sqlite"


def main():
    shutil.copyfile(RU, RU + ".bak-ru-en-backfill")
    print("backup ->", RU + ".bak-ru-en-backfill")

    en = sqlite3.connect(EN)
    en_rows = en.execute(
        "SELECT translation_key, translated_text FROM translations "
        "WHERE language_id = 1"
    ).fetchall()
    en.close()

    ru = sqlite3.connect(RU)
    ru_cur = ru.cursor()
    ru_has = set(
        k for (k,) in ru_cur.execute(
            "SELECT translation_key FROM translations WHERE language_id = 1"
        )
    )

    inserts = [(k, v) for (k, v) in en_rows if k not in ru_has]
    ru_cur.executemany(
        "INSERT INTO translations (translation_key, language_id, "
        "translated_text) VALUES (?, 1, ?)",
        inserts,
    )
    ru.commit()

    now = ru_cur.execute(
        "SELECT COUNT(*) FROM translations WHERE language_id = 1"
    ).fetchone()[0]
    print(f"inserted {len(inserts)} English rows; Ru DB now has {now} English rows")
    ru.close()


if __name__ == "__main__":
    main()
