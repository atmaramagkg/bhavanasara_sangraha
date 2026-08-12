# -*- coding: utf-8 -*-
import sqlite3, sys
sys.stdout.reconfigure(encoding="utf-8")
con = sqlite3.connect(r"assets/db/Bhavanasara-Sangraha_Hi.sqlite")
con.text_factory = lambda b: b.decode("utf-8", "replace")
cur = con.cursor()

print("== sections missing hindi_heading ==")
for r in cur.execute(
    """SELECT s.id, s.sort_order, s.title_key, COALESCE(t.translated_text,'?')
       FROM sections s
       LEFT JOIN translations t ON t.translation_key=s.title_key AND t.language_id=1
       WHERE s.hindi_heading IS NULL OR s.hindi_heading=''
       ORDER BY s.period_node_id, s.sort_order"""
):
    print(" ", r)

print("\n== sections WITH hindi_heading (sample) ==")
for r in cur.execute("SELECT id, sort_order, hindi_heading FROM sections WHERE hindi_heading<>'' LIMIT 5"):
    print(" ", r)
