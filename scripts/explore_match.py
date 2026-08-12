# -*- coding: utf-8 -*-
import sqlite3, json, sys, re
from collections import Counter
sys.stdout.reconfigure(encoding="utf-8")

con = sqlite3.connect(r"assets/db/Bhavanasara-Sangraha_Hi.sqlite")
con.text_factory = lambda b: b.decode("utf-8", "replace")
cur = con.cursor()

# Build a skeleton key for DB devanagari text (NFKD, strip danda/space)
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

# Get DB verses with devanagari
rows = list(cur.execute(
    "SELECT id, original_text_devanagari, ref_display, book_id FROM verses WHERE original_text_devanagari IS NOT NULL AND original_text_devanagari<>''"))
print("DB verses with devanagari:", len(rows))

# Load structured scan
verses = json.load(open("scripts/hindi_structured_verses.json", encoding="utf-8"))
broken = json.load(open("scripts/hindi_structured_broken.json", encoding="utf-8"))
print("structured clean:", len(verses), "broken:", len(broken))

# map skeleton->count in structured (to dedup)
sk_to_num = Counter()
for v in verses + broken:
    sk = skeleton(v["text"])
    sk_to_num[sk] += 1

# how many DB devanagari texts match a structured verse?
matched = unmatched = 0
for rid, deva, ref, bid in rows:
    sk = skeleton(deva)
    if sk and sk in sk_to_num:
        matched += 1
    else:
        unmatched += 1
print(f"DB deva matched in structured: {matched}, unmatched: {unmatched}")

# check: do broken verses correspond to DB verses (with padded num)?
# DB verses per period: get refs
by_ref = Counter()
for v in verses:
    by_ref[(v["period"], v["num"])] += 1
print("\nstructured verse numbers per period (top):")
for (p, n), c in sorted(by_ref.items()):
    if c > 1:
        print("  dup:", p, n, c)
