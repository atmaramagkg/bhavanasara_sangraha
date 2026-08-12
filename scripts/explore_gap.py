# -*- coding: utf-8 -*-
import sqlite3, json, sys, unicodedata
sys.stdout.reconfigure(encoding="utf-8")

def skeleton(s):
    s = unicodedata.normalize("NFKC", s or "")
    out = []
    for ch in s:
        if "\u0900" <= ch <= "\u097F":
            out.append(ch)
        elif ch.isalnum():
            out.append(ch.lower())
    return "".join(out)

con = sqlite3.connect(r"assets/db/Bhavanasara-Sangraha_Hi.sqlite")
con.text_factory = lambda b: b.decode("utf-8", "replace")
cur = con.cursor()

# structured scan verses text skeletons (clean + broken)
all_v = json.load(open("scripts/hindi_structured_verses.json", encoding="utf-8"))
all_b = json.load(open("scripts/hindi_structured_broken.json", encoding="utf-8"))
scan_sks = set(skeleton(v["text"]) for v in all_v + all_b)

# 84 empty devanagari verses - check if they are represented in scan
empties = list(cur.execute("SELECT id, ref_display, translation_text FROM verses WHERE original_text_devanagari IS NULL OR trim(original_text_devanagari)=''"))
print(f"{len(empties)} empty-devanagari verses; checking if translation text appears in scan")
can_fill = 0
for rid, ref, trans in empties:
    # translation is Hindi prose; scan is Sanskrit padas - won't match directly.
    pass

# Are there verses where the ref is entirely absent from the scan (no devanagari available anywhere)?
# Check every DB verse's devanagari skeleton presence in scan
rows = list(cur.execute("SELECT id, ref_display, original_text_devanagari FROM verses"))
no_scan = []
for rid, ref, deva in rows:
    sk = skeleton(deva)
    if sk and sk not in scan_sks:
        no_scan.append((rid, ref))
print(f"\n{len(no_scan)} DB verses whose devanagari does NOT appear in structured scan (OCR gap):")
print("  ", no_scan[:40])
