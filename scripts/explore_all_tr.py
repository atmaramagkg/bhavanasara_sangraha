# -*- coding: utf-8 -*-
import sqlite3, sys
sys.stdout.reconfigure(encoding="utf-8")
con = sqlite3.connect(r"assets/db/Bhavanasara-Sangraha_Hi.sqlite")
con.text_factory = lambda b: b.decode("utf-8", "replace")
cur = con.cursor()

print("== all translations ==")
for r in cur.execute("SELECT language_id, translation_key, translated_text FROM translations ORDER BY language_id, translation_key"):
    print(" ", r)
