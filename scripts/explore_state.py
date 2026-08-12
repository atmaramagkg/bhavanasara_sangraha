# -*- coding: utf-8 -*-
import sqlite3, re, json, sys
sys.stdout.reconfigure(encoding="utf-8")

con = sqlite3.connect(r"assets/db/Bhavanasara-Sangraha_Hi.sqlite")
con.text_factory = lambda b: b.decode("utf-8", "replace")
cur = con.cursor()
print("tables:", [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'")])

latin = re.compile(r"[A-Za-z]")
for tbl, col in [("verses", "translation_text"), ("quotes", "quote_text")]:
    rows = list(cur.execute(f"SELECT id, {col} FROM {tbl}"))
    total = len(rows)
    latin_rows = [i for i, t in rows if latin.search(t or "")]
    empty = [i for i, t in rows if not (t or "").strip()]
    print(f"{tbl}: total={total}, latin={len(latin_rows)}, empty={len(empty)}")
    if latin_rows[:20]:
        print("  latin ids:", latin_rows[:20])
    if empty[:20]:
        print("  empty ids:", empty[:20])

# show the columns of verses and quotes
for tbl in ("verses", "quotes", "sections", "languages"):
    cols = [c[1] for c in cur.execute(f"PRAGMA table_info({tbl})")]
    print(f"\n{tbl} columns: {cols}")
    print("  sample count:", cur.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0])

# count sections missing hindi_heading
rows = list(cur.execute("SELECT id, hindi_heading, title_key FROM sections"))
missing = [r[0] for r in rows if not (r[1] or "").strip()]
print(f"\nsections: total={len(rows)}, missing hindi_heading={len(missing)}")
print("  missing ids:", missing[:40])
