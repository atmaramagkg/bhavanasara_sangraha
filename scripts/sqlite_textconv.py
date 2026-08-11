# -*- coding: utf-8 -*-
"""Git textconv driver: render an SQLite DB as stable, sortable text so
`git diff` can show schema/data changes for .sqlite files."""
import sqlite3, sys


def main(path):
    sys.stdout.reconfigure(encoding="utf-8")
    con = sqlite3.connect(path)
    cur = con.cursor()
    tables = [r[0] for r in cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%' ORDER BY name")]
    for t in tables:
        try:
            cols = [c[1] for c in cur.execute(f'PRAGMA table_info("{t}")')]
        except sqlite3.Error:
            continue
        print(f"== table: {t} ==")
        if not cols:
            continue
        rows = cur.execute(f'SELECT * FROM "{t}"').fetchall()
        for r in sorted(rows, key=lambda r: [str(x) for x in r]):
            print(t, "|", " | ".join(str(x) if x is not None else "∅" for x in r))
    con.close()


if __name__ == "__main__":
    main(sys.argv[1])
