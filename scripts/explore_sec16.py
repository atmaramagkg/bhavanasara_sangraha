# -*- coding: utf-8 -*-
import sqlite3, sys
sys.stdout.reconfigure(encoding="utf-8")
con = sqlite3.connect(r"assets/db/Bhavanasara-Sangraha_Hi.sqlite")
con.text_factory = lambda b: b.decode("utf-8", "replace")
cur = con.cursor()

# Which sections have NO hindi_heading AND check if their title translation exists
print("== 16 sections missing hindi_heading: title translation? ==")
for r in cur.execute("""
    SELECT s.id, p.code, s.sort_order, s.title_key,
           (SELECT COUNT(*) FROM translations t WHERE t.translation_key=s.title_key AND t.language_id=2) AS has_hi_title
    FROM sections s JOIN period_nodes p ON p.id=s.period_node_id
    WHERE s.hindi_heading IS NULL OR s.hindi_heading=''
    ORDER BY p.sort_order, s.sort_order"""):
    print("  ", r)

# Count quotes per section for those
print("\n== quotes count per section (for the 16) ==")
for r in cur.execute("""
    SELECT s.id, COUNT(q.id) FROM sections s
    LEFT JOIN quotes q ON q.section_id=s.id
    WHERE s.hindi_heading IS NULL OR s.hindi_heading=''
    GROUP BY s.id ORDER BY s.id"""):
    print("  ", r)
