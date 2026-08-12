# -*- coding: utf-8 -*-
import sqlite3, sys
sys.stdout.reconfigure(encoding="utf-8")
con = sqlite3.connect(r"assets/db/Bhavanasara-Sangraha_Hi.sqlite")
con.text_factory = lambda b: b.decode("utf-8", "replace")
cur = con.cursor()
print("languages:", list(cur.execute("SELECT * FROM languages")))
print("translations count:", cur.execute("SELECT COUNT(*) FROM translations").fetchone()[0])
for x in cur.execute("SELECT translation_key, language_id, translated_text FROM translations WHERE translation_key LIKE 'section.purvahna_1.1%'"):
    print(x)
