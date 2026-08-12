# -*- coding: utf-8 -*-
"""Write the EN/RU subtitle translations for the Hindi section headings.

Each section with a `hindi_heading` gets a translation key of the same shape
as its title (`section.<pcode>.<n>.hindi_title`). The English translation goes
into the En DB; both the English and Russian ones go into the Ru DB. The Hindi
DB needs none -- the app falls back to the Devanagari heading there.

The Dart feed query resolves the key with a COALESCE:
    COALESCE(thead.translated_text, sec.hindi_heading)

Usage:
  python scripts/apply_hindi_heading_translations.py
"""
import json
import shutil
import sqlite3
import sys

EN = r"C:\Users\austr\bhavanasara_sangraha\assets\db\Bhavanasara-Sangraha_En.sqlite"
RU = r"C:\Users\austr\bhavanasara_sangraha\assets\db\Bhavanasara-Sangraha_Ru.sqlite"
TRANSLATIONS = (r"C:\Users\austr\bhavanasara_sangraha\scripts"
                r"\section_hindi_heading_translations.json")

sys.stdout.reconfigure(encoding="utf-8")


def connect(p):
    c = sqlite3.connect(p)
    c.row_factory = sqlite3.Row
    c.text_factory = lambda b: b.decode("utf-8", "replace")
    return c


def main():
    with open(TRANSLATIONS, encoding="utf-8") as f:
        table = json.load(f)

    heading_keys = set()
    rows_by_db = {}  # (db, lang_code) -> {translation_key: text}

    for path, languages in ((EN, ("en",)), (RU, ("en", "ru"))):
        con = connect(path)
        cur = con.cursor()
        rows = cur.execute(
            """
            SELECT s.id, p.code AS pcode, s.sort_order, s.hindi_heading
            FROM sections s
            JOIN period_nodes p ON p.id = s.period_node_id
            WHERE s.hindi_heading IS NOT NULL AND s.hindi_heading != ''
            """
        ).fetchall()

        missing = {r["hindi_heading"] for r in rows} - set(table)
        if missing:
            print("MISSING translations for headings:")
            for m in sorted(missing):
                print("  ", m)
            sys.exit(1)

        for lang in languages:
            lang_id = cur.execute(
                "SELECT id FROM languages WHERE code = ?", (lang,)
            ).fetchone()
            assert lang_id, f"{path} has no language {lang}"
            lang_id = lang_id["id"]

            for r in rows:
                key = (f"section.{r['pcode']}.{r['sort_order']}.hindi_title")
                heading_keys.add(key)
                rows_by_db.setdefault((path, lang_id), {})[key] = (
                    table[r["hindi_heading"]][lang]
                )
        con.close()

    for (path, lang_id), entries in rows_by_db.items():
        shutil.copyfile(path, path + ".bak-hindi-subtitles")
        print("backup ->", path + ".bak-hindi-subtitles")

        con = connect(path)
        cur = con.cursor()
        cur.execute(
            "DELETE FROM translations "
            "WHERE translation_key IN ({}) AND language_id = ?".format(
                ",".join("?" * len(entries))
            ),
            [*entries.keys(), lang_id],
        )
        cur.executemany(
            "INSERT INTO translations (translation_key, language_id, "
            "translated_text) VALUES (?, ?, ?)",
            [(k, lang_id, v) for k, v in entries.items()],
        )
        con.commit()

        count = cur.execute(
            "SELECT COUNT(*) FROM translations "
            "WHERE translation_key LIKE '%.hindi_title' AND language_id = ?",
            (lang_id,),
        ).fetchone()[0]
        print(f"{path} (language {lang_id}): {count} subtitle translations")
        con.close()

    print(f"{len(heading_keys)} section heading keys covered")


if __name__ == "__main__":
    main()
