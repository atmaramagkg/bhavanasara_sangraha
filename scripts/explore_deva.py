# -*- coding: utf-8 -*-
import sqlite3, sys, re
sys.stdout.reconfigure(encoding="utf-8")
con = sqlite3.connect(r"assets/db/Bhavanasara-Sangraha_Hi.sqlite")
con.text_factory = lambda b: b.decode("utf-8", "replace")
cur = con.cursor()
rows = list(cur.execute("SELECT id, original_text_devanagari, original_text, ref_display FROM verses"))
empty = [r for r in rows if not (r[1] or "").strip()]
latin = [r for r in rows if re.search(r"[A-Za-z]", r[1] or "")]
print(f"verses total={len(rows)}, empty deva={len(empty)}, latin deva={len(latin)}")
print("sample deva rows:")
for r in rows[:5]:
    print("  ", r[0], (r[1] or "")[:80], "|", r[3])
