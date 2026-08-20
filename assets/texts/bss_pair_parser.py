#!/usr/bin/env python3
"""
Bhavana-sara Sangraha OCR pairing tool.

Pairs Sanskrit verse blocks (ending in a ।।N।। / ॥N॥ - style marker) with
their numbered Hindi translation paragraphs "(N) ...", and attaches the
nearest citation in parentheses (e.g. "(गोवि. 1/10)", "(आ. 1/2)").

Designed to run chapter-by-chapter (lila-by-lila) because verse numbering
restarts at 1 for each of the 8 lila sections in this book.

Usage:
    python3 bss_pair_parser.py <input.txt> --start LINE --end LINE
"""
import re
import sys
import json
import argparse

DEVANAGARI_DIGITS = "०१२३४५६७८९"
DIGIT_MAP = {d: str(i) for i, d in enumerate(DEVANAGARI_DIGITS)}

# Recurring running headers/footers/watermarks to strip
NOISE_PATTERNS = [
    r"^\s*॥?\s*सङ्गणकसंस्करणं.*कृतम्‌?\s*॥?\s*$",
    r"^\s*श्रीश्री भावना सार संग्रहः?\s*.*$",
    r"^\s*निशान्त लीला\s*.*$",
]
NOISE_RE = [re.compile(p) for p in NOISE_PATTERNS]


def devanagari_to_int(s):
    s = s.strip()
    out = ""
    for ch in s:
        if ch in DIGIT_MAP:
            out += DIGIT_MAP[ch]
        elif ch.isdigit():
            out += ch
    return int(out) if out else None


def strip_noise(lines):
    cleaned = []
    for ln in lines:
        if any(r.match(ln.strip()) for r in NOISE_RE):
            continue
        cleaned.append(ln)
    return cleaned


VERSE_MARKER_RE = re.compile(r"[।॥]{1,2}\s*([०-९0-9]{1,4})\s*[।॥]{1,2}")
CITATION_RE = re.compile(r"\(([^()]{2,40}[०-९0-9][^()]{0,15})\)")
TRANSLATION_START_RE = re.compile(r"^\s*\(([०-९0-9]{1,4})\)\s*(.*)")


def looks_like_citation(paren_content):
    if len(paren_content) > 25:
        return False
    if not re.search(r"[०-९0-9]", paren_content):
        return False
    return True


def parse_section(raw_lines):
    lines = strip_noise(raw_lines)
    text = "\n".join(lines)

    verses = {}
    citations = {}
    translations = {}

    blocks = re.split(r"\n\s*\n", text)

    pending_sanskrit = []
    last_verse_num = None

    for block in blocks:
        block_stripped = block.strip()
        if not block_stripped:
            continue

        m = TRANSLATION_START_RE.match(block_stripped)
        if m:
            num = devanagari_to_int(m.group(1))
            body = m.group(2) + "\n" + "\n".join(block.split("\n")[1:])
            body = body.strip()
            cit = None
            citm = list(CITATION_RE.finditer(body))
            if citm:
                last = citm[-1]
                if looks_like_citation(last.group(1)) and last.end() > len(body) - 30:
                    cit = last.group(1).strip()
                    body = (body[: last.start()] + body[last.end():]).strip()
            if num is not None:
                translations[num] = body
                if cit:
                    citations.setdefault(num, cit)
            continue

        markers = list(VERSE_MARKER_RE.finditer(block_stripped))
        if markers:
            cursor = 0
            for i, m0 in enumerate(markers):
                num = devanagari_to_int(m0.group(1))
                verse_text = block_stripped[cursor: m0.start()].strip()
                next_start = markers[i + 1].start() if i + 1 < len(markers) else len(block_stripped)
                remainder = block_stripped[m0.end(): next_start].strip()
                cit = None
                citm = CITATION_RE.search(remainder)
                if citm and looks_like_citation(citm.group(1)):
                    cit = citm.group(1).strip()
                if num is not None and verse_text:
                    verses[num] = verse_text
                    if cit:
                        citations.setdefault(num, cit)
                    last_verse_num = num
                cursor = next_start
        else:
            if CITATION_RE.fullmatch(block_stripped) and last_verse_num is not None:
                cit = CITATION_RE.fullmatch(block_stripped).group(1).strip()
                citations.setdefault(last_verse_num, cit)

    all_nums = sorted(set(verses) | set(translations))
    numbered_pairs = []
    for n in all_nums:
        numbered_pairs.append({
            "verse_num": n,
            "sanskrit": verses.get(n),
            "hindi_translation": translations.get(n),
            "citation": citations.get(n),
        })

    verse_items = sorted(verses.items())
    trans_items = sorted(translations.items())
    positional_pairs = []
    for i in range(max(len(verse_items), len(trans_items))):
        v = verse_items[i] if i < len(verse_items) else (None, None)
        t = trans_items[i] if i < len(trans_items) else (None, None)
        positional_pairs.append({
            "position": i + 1,
            "verse_label": v[0],
            "sanskrit": v[1],
            "translation_label": t[0],
            "hindi_translation": t[1],
        })

    return numbered_pairs, positional_pairs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--start", type=int, default=1)
    ap.add_argument("--end", type=int, default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    with open(args.input, encoding="utf-8") as f:
        all_lines = f.readlines()

    end = args.end or len(all_lines)
    chunk = all_lines[args.start - 1: end]
    numbered_pairs, positional_pairs = parse_section(chunk)

    base = args.out or "bss_pairs_sample"
    with open(f"{base}_by_number.json", "w", encoding="utf-8") as f:
        json.dump(numbered_pairs, f, ensure_ascii=False, indent=2)
    with open(f"{base}_by_position.json", "w", encoding="utf-8") as f:
        json.dump(positional_pairs, f, ensure_ascii=False, indent=2)

    print(f"Number-matched: {len(numbered_pairs)} entries -> {base}_by_number.json")
    missing_v = [p["verse_num"] for p in numbered_pairs if not p["sanskrit"]]
    missing_t = [p["verse_num"] for p in numbered_pairs if not p["hindi_translation"]]
    if missing_v:
        print(f"  missing Sanskrit for verse#: {missing_v}")
    if missing_t:
        print(f"  missing Hindi for verse#: {missing_t}")

    print(f"Position-matched: {len(positional_pairs)} entries -> {base}_by_position.json")
    print(f"  (verses found: {sum(1 for p in positional_pairs if p['sanskrit'])}, "
          f"translations found: {sum(1 for p in positional_pairs if p['hindi_translation'])})")


if __name__ == "__main__":
    main()
