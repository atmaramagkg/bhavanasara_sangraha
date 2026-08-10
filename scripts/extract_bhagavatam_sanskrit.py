# -*- coding: utf-8 -*-
"""
Extract specific Śrīmad-Bhāgavatam verses from sanskritdocuments.org's
ITRANS file (doc_purana/bhagpur-10a.itx, public-domain Sanskrit text)
and convert them to IAST for the bhagavatam DB rows.

Usage:  python scripts/extract_bhagavatam_sanskrit.py
Writes: scripts/bhagavatam_verses.json  (chapter -> verse_no -> IAST text)
"""
import sys, re, json, os
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.abspath(__file__))
ITX = r"C:\Users\austr\AppData\Local\Temp\opencode\bhagpur-10a.itx"
OUT = os.path.join(ROOT, "bhagavatam_verses.json")

# verses wanted: chapter -> set of verse numbers (matches DB ref_display)
WANT = {
    9: {3},
    13: {1, 5, 6, 7, 8, 9},
    15: {3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 42},
    18: {7, 8, 16, 19, 20, 21, 22, 23, 24},
    29: {43, 44, 45, 46},
    33: {2, 6, 7, 9, 10},
    35: {1},  # vedabase 10.35.2 == sanskritdocuments 10.35.1 (flute verse)
}

CH_RE = re.compile(r"\\section\{\.\.\s*\S+?\.adhyAyaH\s*(?:\\?-\s*)?(\d+)\s*\.\.\}")

def main():
    lines = open(ITX, encoding="utf-8").read().splitlines()
    chapters = {}   # ch -> list of raw verse lines
    cur = None
    for ln in lines:
        if ln.startswith("\\section"):
            m = CH_RE.search(ln)
            if m:
                cur = int(m.group(1))
                chapters.setdefault(cur, [])
            continue
        if ln.startswith("%") or ln.startswith("\\") or not ln.strip():
            continue
        if cur is None:
            continue
        chapters[cur].append(ln)

    out = {}
    for ch, verses in WANT.items():
        raw = chapters.get(ch)
        if raw is None:
            print(f"!! chapter {ch} not found in ITX")
            continue
        parsed = parse_verses(raw)
        found = set(parsed)
        missing = verses - found
        if missing:
            print(f"!! chapter {ch} missing verses: {sorted(missing)}")
        out[ch] = {v: transliterate(parsed[v], sanscript.ITRANS, sanscript.IAST)
                   for v in sorted(verses) if v in parsed}

    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    n = sum(len(v) for v in out.values())
    print(f"wrote {OUT}: {n} verses across {len(out)} chapters")
    for ch in sorted(out):
        print(f"  ch {ch}: {sorted(out[ch])}")

def parse_verses(raw_lines):
    """Join lines, split on '|| N ||' markers, return {verse_no: itrans_text}."""
    text = "\n".join(raw_lines)
    text = re.sub(r"\-\\\s*\n", "", text)      # line-continuation hyphen
    text = re.sub(r"\\-\n", "", text)
    text = text.replace("##", "")
    # split into verses by trailing markers
    parts = re.split(r"\|\|\s*(\d+)\s*\|\|", text)
    # parts: [pre, 1, body1, 2, body2, ...]
    verses = {}
    for i in range(1, len(parts) - 1, 2):
        num = int(parts[i])
        body = parts[i + 1].strip()
        if not body:
            continue
        body = re.sub(r"\s*\n\s*", " ", body)
        body = re.sub(r"\s+", " ", body)
        verses[num] = body
    return verses

if __name__ == "__main__":
    main()
