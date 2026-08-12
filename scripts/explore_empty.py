# -*- coding: utf-8 -*-
import sqlite3, sys
sys.stdout.reconfigure(encoding="utf-8")
con = sqlite3.connect(r"assets/db/Bhavanasara-Sangraha_Hi.sqlite")
con.text_factory = lambda b: b.decode("utf-8", "replace")
cur = con.cursor()

# empty devanagari verses, grouped by book
print("== 84 empty-devanagari verses by book ==")
for r in cur.execute("""
    SELECT b.slug, COUNT(*) FROM verses v
    JOIN books b ON b.id = v.book_id
    WHERE v.original_text_devanagari IS NULL OR trim(v.original_text_devanagari)=''
    GROUP BY b.slug ORDER BY COUNT(*) DESC"""):
    print("  ", r)

# verses whose devanagari ends mid-sentence (truncated) - heuristic
import re
print("\n== sample truncated devanagari (ends with ' | ' or consonant) ==")
for r in cur.execute("SELECT id, original_text_devanagari, ref_display FROM verses WHERE original_text_devanagari LIKE '% |' OR original_text_devanagari LIKE '%्%|%' LIMIT 10"):
    print("  ", r[0], (r[1] or "")[:90])
