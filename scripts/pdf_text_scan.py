# -*- coding: utf-8 -*-
"""Extract embedded text layer from the Hindi PDF and validate the verse rule."""
import os, sys, re, json
from collections import Counter
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\austr\bhavanasara_sangraha\scripts")
from hindi_structured_scan import (PADA2_ENDER, _fold, _norm_pada1, _split_pada1,
                                   LILA_ALIASES, HEADER_RE, HEADER_FALLBACK, code_for)

PDF = r"C:\Users\austr\OneDrive\Documents\_Bhavanasara-Sangraha\Books\Bhavanasara-Sangraha\bhavana_sara_sangraha_hindi_text.pdf"
OUT = r"C:\Users\austr\bhavanasara_sangraha\scripts\pdf_text"
os.makedirs(OUT, exist_ok=True)

def scan_lines(lines):
    verses, broken = [], []
    period = None
    prev = None
    for raw in lines:
        t = raw.strip()
        if not t:
            continue
        m = HEADER_RE.match(t) or HEADER_FALLBACK.search(t)
        if m:
            name = m.group("lila") if "lila" in m.groupdict() else m.group(1)
            code = code_for(name)
            if code:
                period = code
            continue
        folded = _fold(t)
        em = PADA2_ENDER.search(folded)
        if em:
            num = _to_num(em.group(1))
            ender_line = folded[:em.start()].rstrip(" ,")
            p1, pref = ("", "") if not prev else _split_pada1(_norm_pada1(prev))
            p1 = p1.strip()
            reason = None
            if not p1:
                reason = "no_pada1"
            elif not p1.endswith("।"):
                reason = "pada1_no_danda"
            rec = {"period": period, "num": num, "pada1": p1,
                   "pada2": (pref + " " + ender_line).strip(),
                   "text": (p1 + " " + pref + " " + ender_line).strip()}
            if reason:
                rec["reason"] = reason
                broken.append(rec)
            else:
                verses.append(rec)
            prev = None
        else:
            prev = t
    return verses, broken

_dmap = {ch: str(i) for i, ch in enumerate("०१२३४५६७८९")}
def _to_num(s):
    if not s:
        return None
    out = "".join(_dmap.get(c, c) for c in s.strip())
    try:
        return int(out)
    except ValueError:
        return None

import fitz
doc = fitz.open(PDF)
all_verses, all_broken = [], []
for n in range(1, doc.page_count + 1):
    t = doc[n - 1].get_text()
    page = f"PDF_{n}"
    fn = os.path.join(OUT, f"page_{n:03d}.txt")
    with open(fn, "w", encoding="utf-8") as f:
        f.write(t)
    v, b = scan_lines(t.splitlines())
    for rec in v:
        rec["page"] = page
    for rec in b:
        rec["page"] = page
    all_verses += v
    all_broken += b
doc.close()

print(f"PDF text: total clean verses: {len(all_verses)}  broken: {len(all_broken)}")
by_period = Counter()
for v in all_verses:
    by_period[v["period"]] += 1
by_broken = Counter(x["reason"] for x in all_broken)
print("broken reasons:", dict(by_broken))
print("\nby period: printed | clean | broken")
from hindi_structured_scan import TOC_VERSE_COUNTS
bper = Counter(x["period"] for x in all_broken)
for code, _ in LILA_ALIASES:
    print(f"  {code:12s} {TOC_VERSE_COUNTS.get(code,'-'):>6} | {by_period.get(code,0):>5} | {bper.get(code,0)}")

json.dump(all_verses, open(r"C:\Users\austr\bhavanasara_sangraha\scripts\pdf_structured_verses.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(all_broken, open(r"C:\Users\austr\bhavanasara_sangraha\scripts\pdf_structured_broken.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"\nwrote scripts/pdf_structured_verses.json and pdf_structured_broken.json")
print(f"wrote per-page text to {OUT}")
