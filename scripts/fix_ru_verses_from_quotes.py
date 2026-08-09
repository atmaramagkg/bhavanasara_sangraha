# -*- coding: utf-8 -*-
"""
fix_ru_verses_from_quotes.py

Repairs the Russian database's `verses.translation_text` column, which currently
holds English text for most books while the `quotes` table holds the correct
Russian translations.

How the mapping works (verified against the English database):
  * Every `verses` row's `translation_text` exactly equals the `quote_text` of
    exactly one of the citations pointing at that verse (`citations.source_verse_id`).
  * The `citations` and `quotes` tables are structurally identical between the
    En and Ru databases (same ids; only `ref_display`/`quote_text` differ by
    language).

So for each verse we find the quote it was originally built from (by matching
the En verse text against En quote text), then copy that quote's Russian text
into the Ru verse.

Usage:
    python3 fix_ru_verses_from_quotes.py <ru.sqlite> <en.sqlite>
"""
import sqlite3
import sys


def main():
    if len(sys.argv) != 3:
        print("usage: fix_ru_verses_from_quotes.py <ru.sqlite> <en.sqlite>")
        sys.exit(1)

    ru_path, en_path = sys.argv[1], sys.argv[2]

    en = sqlite3.connect(en_path)
    ru = sqlite3.connect(ru_path)

    en_cur = en.cursor()
    ru_cur = ru.cursor()

    verses = en_cur.execute("SELECT id, translation_text FROM verses").fetchall()
    if len(verses) != en_cur.execute("SELECT COUNT(*) FROM verses").fetchone()[0]:
        raise SystemExit("inconsistent En verses count")

    updated = 0
    skipped = 0
    failures = []

    for verse_id, en_text in verses:
        en_text = en_text or ""
        # Find the quote whose text matches this verse in the En DB.
        matches = en_cur.execute(
            """
            SELECT c.quote_id
            FROM citations c
            JOIN quotes q ON q.id = c.quote_id
            WHERE c.source_verse_id = ? AND q.quote_text = ?
            """,
            (verse_id, en_text),
        ).fetchall()
        if len(matches) != 1:
            skipped += 1
            failures.append((verse_id, en_text[:60]))
            continue
        quote_id = matches[0][0]

        # Fetch the Russian text of that same quote from the Ru DB.
        ru_quotes = ru_cur.execute(
            "SELECT quote_text FROM quotes WHERE id = ?", (quote_id,)
        ).fetchall()
        if len(ru_quotes) != 1:
            skipped += 1
            failures.append((verse_id, en_text[:60]))
            continue
        ru_text = ru_quotes[0][0] or ""

        ru_cur.execute(
            "UPDATE verses SET translation_text = ? WHERE id = ?",
            (ru_text, verse_id),
        )
        updated += 1

    ru.commit()

    print(f"verses updated: {updated}")
    print(f"verses skipped: {skipped}")
    for f in failures:
        print("  skipped verse", f)

    en.close()
    ru.close()


if __name__ == "__main__":
    main()
