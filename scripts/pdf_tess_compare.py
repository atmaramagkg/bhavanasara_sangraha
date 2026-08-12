# -*- coding: utf-8 -*-
"""Per-page conformance: PDF-text source vs tesseract source; find pages both clean vs one."""
import os, sys, re, glob, json
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\austr\bhavanasara_sangraha\scripts")
from hindi_structured_scan import (PADA2_ENDER, _fold, _norm_pada1, _split_pada1,
                                   HEADER_RE, HEADER_FALLBACK, code_for)
from pdf_text_scan import scan_lines  # returns (verses, broken)

PDFTXT = r"C:\Users\austr\bhavanasara_sangraha\scripts\pdf_text"
TESS_TXT = r"C:\Users\austr\AppData\Local\Temp\opencode\hindi\tess_450\txt"

def page_scan(text):
    v, b = scan_lines(text.splitlines())
    return v, b

def part_page(pdfno):
    if pdfno <= 350:
        return f"PART1_{pdfno}", pdfno
    return f"PART2_{pdfno - 350}", pdfno

pdf_clean = {}   # pdfno -> clean verses
pdf_broken = {}  # pdfno -> broken verses
tess_clean = {}
tess_broken = {}

for n in range(1, 701):
    pdf = open(os.path.join(PDFTXT, f"page_{n:03d}.txt"), encoding="utf-8").read()
    pv, pb = page_scan(pdf)
    pdf_clean[n] = pv
    pdf_broken[n] = pb
    part, pno = part_page(n)
    tess = open(os.path.join(TESS_TXT, f"{part}.txt"), encoding="utf-8").read()
    tv, tb = page_scan(tess)
    tess_clean[n] = tv
    tess_broken[n] = tb

both_clean = [n for n in range(1, 701) if not pdf_broken[n] and not tess_broken[n]]
pdf_only_clean = [n for n in range(1, 701) if not pdf_broken[n] and tess_broken[n]]
tess_only_clean = [n for n in range(1, 701) if pdf_broken[n] and not tess_broken[n]]
both_broken = [n for n in range(1, 701) if pdf_broken[n] and tess_broken[n]]
empty_pdf = [n for n in range(1, 701) if not pdf_clean[n] and not pdf_broken[n]]

print(f"pages BOTH clean:       {len(both_clean)}")
print(f"pages PDF-clean only:   {len(pdf_only_clean)}")
print(f"pages TESS-clean only:  {len(tess_only_clean)}")
print(f"pages BOTH broken:      {len(both_broken)}")
print(f"pages with no verses in PDF text: {len(empty_pdf)}")

print("\nTESS-clean-only (PDF broken, tesseract txt clean) - adopt tesseract page:")
for n in sorted(tess_only_clean):
    part, pno = part_page(n)
    print(f"  PDF_{n} / {part}")

print("\nBOTH broken - need re-OCR:")
for n in sorted(both_broken):
    part, pno = part_page(n)
    pb = [x['num'] for x in pdf_broken[n]]
    tb = [x['num'] for x in tess_broken[n]]
    print(f"  PDF_{n} / {part}  pdf_broken={pb} tess_broken={tb}")

json.dump({"both_clean": both_clean, "pdf_only_clean": pdf_only_clean,
           "tess_only_clean": tess_only_clean, "both_broken": both_broken},
          open(r"C:\Users\austr\bhavanasara_sangraha\scripts\page_compare.json", "w"), indent=1)
print("\nwrote scripts/page_compare.json")
