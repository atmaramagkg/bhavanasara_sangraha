# -*- coding: utf-8 -*-
import sqlite3, json, sys
sys.stdout.reconfigure(encoding="utf-8")

con = sqlite3.connect(r"assets/db/Bhavanasara-Sangraha_Hi.sqlite")
con.text_factory = lambda b: b.decode("utf-8", "replace")
cur = con.cursor()

# Compare DB original_text_devanagari against structured scan by skeleton
import unicodedata
def skeleton(s):
    s = unicodedata.normalize("NFKC", s or "")
    out = []
    for ch in s:
        if "\u0900" <= ch <= "\u097F":
            out.append(ch)
        elif ch.isalnum():
            out.append(ch.lower())
    return "".join(out)

verses = json.load(open("scripts/hindi_structured_verses.json", encoding="utf-8"))
sk_map = {}
for v in verses:
    sk_map.setdefault(skeleton(v["text"]), []).append(v)

rows = list(cur.execute("SELECT id, original_text_devanagari, ref_display FROM verses WHERE original_text_devanagari IS NOT NULL AND original_text_devanagari<>''"))
found = notfound = 0
notfound_ids = []
for rid, deva, ref in rows:
    sk = skeleton(deva)
    if sk in sk_map:
        found += 1
    else:
        notfound += 1
        notfound_ids.append(rid)
print(f"DB devanagari matched in structured scan: {found}/{len(rows)}")
print("unmatched ids:", notfound_ids[:30])

# check empty devanagari verses - do they have refs?
empties = list(cur.execute("SELECT id, ref_display, book_id, translation_text FROM verses WHERE original_text_devanagari IS NULL OR trim(original_text_devanagari)=''"))
print(f"\n{len(empties)} empty devanagari verses:")
for r in empties[:20]:
    print("  ", r[0], r[1], "| trans:", (r[3] or "")[:50])
