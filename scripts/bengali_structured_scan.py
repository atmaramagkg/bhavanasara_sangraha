# -*- coding: utf-8 -*-
"""
Structural Bengali edition verse scan — same Sanskrit verse-layout rule as the
Hindi scan (hindi_structured_scan.py), applied to the Bengali OCR output.

RULE (logical, identical across editions):
  verse = TWO logical lines
    pāda-1 logical line: ends with a SINGLE danda
    pāda-2 logical line: ends with DOUBLE danda + verse number + DOUBLE danda
                         (॥N॥)
  Any Sanskrit verse that does NOT follow this rule was split at the wrong
  place and is flagged broken (reason: pada1_no_danda).

Edition differences (Bengali typesetting):
  * a logical line may WRAP across 1-2 physical OCR lines (verse = 2 OR 4
    physical lines; long words hyphenate at the break with a trailing '-'),
  * the single danda is OCR'd as the Bengali danda U+09F7 'ু' as well as the
    Devanagari danda U+0964 '।',
  * the closing danda run may appear as '॥', '।।', '।॥', '॥.', '॥N।', etc.,
  * the verse number may have stray interior whitespace or a stray trailing
    ASCII digit glued on (e.g. '॥ ৪ 1॥' for verse 4) — we take the first
    contiguous run of numerals,
  * attributions are printed on their OWN line right after the ॥N॥ ender,
    e.g. '( চন্0 ১৩)', '{(ভ০ 5২}', '( গোৰি0 ২।৩২)' — these are captured and
    attached to the verse, not mixed into the next verse.

Period is detected from the running page headers
  শ্রীশ্রীভাবনাসার-সংগ্রহঃ [ <lila>লীলা <page>
and the 'নিশান্ত-লীলা' section markers.

Input:  Bengali OCR pages (tess_450/txt), PART1_N.txt / PART2_N.txt.
Output: scripts/bengali_structured_verses.json  (clean verses)
        scripts/bengali_structured_broken.json  (rule violations)
        scripts/bengali_structured_report.txt   (per-period stats)

Usage:
  python scripts/bengali_structured_scan.py
  (set BENGALI_TXT_DIR to point at the OCR txt folder if not the default)
"""
import os, re, sys, json, glob
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.stdout.reconfigure(encoding="utf-8")

TXT_DIR = os.environ.get(
    "BENGALI_TXT_DIR",
    r"C:\Users\austr\OneDrive\Documents\_Bhavanasara-Sangraha\Books"
    r"\bhavana_sara_sangraha_bengali\tess_450\txt",
)
OUT_JSON = os.path.join(ROOT, "bengali_structured_verses.json")
OUT_BROKEN = os.path.join(ROOT, "bengali_structured_broken.json")
OUT_REPORT = os.path.join(ROOT, "bengali_structured_report.txt")

MAX_LOOKBACK = 6   # physical lines to search back from the ender for the danda

# ---- digits: Bengali (০-৯), Devanagari (०-९), ASCII (0-9) all occur ----------
_BENG = {ch: str(i) for i, ch in enumerate("০১২৩৪৫৬৭৮৯")}
_DEVA = {ch: str(i) for i, ch in enumerate("०१२३४५६७८९")}
# Bengali ০-৯ = U+09E6..U+09EF, Devanagari ०-९ = U+0966..U+096F
NUM_CLASS = r"[\u09E6-\u09EF\u0966-\u096F0-9]"


def _fold(line):
    return line.replace("॥", "।।").replace("||", "।।").replace("|", "।")


def _norm_num(s):
    """Take the first contiguous run of numerals (any script) from s."""
    if not s:
        return None
    runs = re.findall(NUM_CLASS + r"+", s)
    if not runs:
        return None
    out = []
    for ch in runs[0]:
        if ch in _BENG:
            out.append(_BENG[ch])
        elif ch in _DEVA:
            out.append(_DEVA[ch])
        elif ch.isdigit():
            out.append(ch)
    try:
        return int("".join(out))
    except ValueError:
        return None


# pāda-2 ender, applied to the FOLDED line: danda run, number (with stray
# interior whitespace / glued ASCII digit tolerated), closing danda run.
PADA2_ENDER = re.compile(
    r"(?:।\s*){1,3}(" + NUM_CLASS + r"{1,4}(?:\s*" + NUM_CLASS + r"){0,2})"
    r"\s*[।॥]+\s*$"
)

# standalone attribution-only line: short line, contains a numeral, ends with a
# closing bracket ('( কৃ ভা ১৪)', '{(ভ০ 5২}', '৫)').  Brackets may wrap each
# other, so we only test the shape (short + numeral + closing bracket).
def is_attr_line(nf):
    nf = nf.strip(" .\u200c")
    if not nf:
        return False
    if len(nf) > 45:
        return False
    if not re.search(NUM_CLASS, nf):
        return False
    return nf.endswith((")", "}", "]"))


DANDA_END = ("\u0964", "\u09F7")

# parenthesized verse-number marker like '(৫৩)' / '(1२)' that OPENS the Bengali
# translation/commentary block printed after the Sanskrit verses on each page.
# The Sanskrit verses always come FIRST (proved book-wide: no ॥N॥ ender ever
# appears below the first such marker on a page), so the first long line with a
# parenthesized numeral marks the end of that page's Sanskrit block.
TMARK = re.compile(r"[\(\[][\s:]*" + NUM_CLASS + r"{1,3}[\s:.]?[\)\]]")

# leading inline attribution glued to the start of a pāda-1 line, e.g.
# '(কৃ ভা! ১1২৬ } ইতস্ততো ...' -> attribution + clean pāda-1
LEAD_ATTR = re.compile(
    r"^[\(\[\{][^\)\]\}]*" + NUM_CLASS + r"[^\)\]\}]*[\)\]\}][\s.~:;,]+"
)


def trim_translation(buf):
    """Drop the Bengali translation/commentary tail from buf at the marker.

    Only a trailing Sanskrit pāda-1 pair (one optional wrapped line + the danda
    line, both on the same page) may survive — that is the one thing that can
    legitimately span this point (a verse whose pāda-1 is on the page being
    left and whose pāda-2 + ender are on the next page).
    """
    if not buf:
        return []
    j = len(buf) - 1
    while j >= 0 and not buf[j][1].rstrip().endswith(DANDA_END):
        j -= 1
    if j < 0:
        return []
    if (j - 1 >= 0 and buf[j - 1][0] == buf[j][0]
            and len(buf[j - 1][1]) > 8 and not is_attr_line(buf[j - 1][1])):
        return buf[j - 1:j + 1]
    return buf[j:j + 1]

# lila (period) detection from running page headers + section markers
LILA_PATTERNS = [
    (r"নিশান্ত", "nishanta"),
    (r"প্রাত", "pratah"),
    (r"পূর্বাহ", "purvahna"),
    (r"মধ্যাহ", "madhyahna"),
    (r"অপরাহ", "aparahna"),
    (r"সায়াহ|সায়াহ্ন", "sayahna"),
    (r"প্রদোষ|প্রদেষ", "pradosha"),
    (r"নক্ত", "nisha"),
]
HEADER_LINE = re.compile(r"(ভাবনাসার|সংগ্রহ)")
# standalone section markers like  'নিশান্ত-লীলা' / 'অথ মধ্যাহ্ন-লীলা'
SECTION_MARK = re.compile(
    r"^(অথ\s*)?(নিশান্ত|প্রাত|পূর্বাহ|মধ্যাহ|অপরাহ|"
    r"সায়াহ|সায়াহ্ন|প্রদোষ|প্রদেষ|নক্ত)[-\s]*লীল"
)
# page colophon junk, e.g.  'শ্রীশ্রীগৌড়ীয়-গৌরব-গ্ৰন্থগুচ্ছঃ', 'গ্র্রীগৌরবিজয়তিতমাম্'
COLOPHON = re.compile(r"^(শ্রী|এশ্রী|গ্র্রী|এ্রী|এঞ্ী|শ্রীর)")

TOC_VERSE_COUNTS = {"nishanta": 185, "pratah": 466, "purvahna": 388,
                    "madhyahna": 1317, "aparahna": 110, "sayahna": 99,
                    "pradosha": 214, "nisha": 268}
LILA_ORDER = ["nishanta", "pratah", "purvahna", "madhyahna",
              "aparahna", "sayahna", "pradosha", "nisha"]


def lila_code(text):
    for pat, code in LILA_PATTERNS:
        if re.search(pat, text):
            return code
    return None


def iter_lines():
    files = sorted(glob.glob(os.path.join(TXT_DIR, "*.txt")),
                   key=lambda p: (int(re.search(r"PART(\d)", p).group(1)),
                                  int(re.search(r"_(\d+)\.txt", p).group(1))))
    for fp in files:
        page = os.path.basename(fp)
        for line in open(fp, encoding="utf-8"):
            yield page, line


def scan():
    verses = []
    broken = []
    period = None
    buf = []          # (page, folded_line) physical lines since last verse
    verse_start = 0   # index into buf where the current verse's lines begin
    lines = list(iter_lines())   # materialized so we can consume attributions
    i = 0
    n = len(lines)

    while i < n:
        page, raw = lines[i]
        t = raw.strip()
        if not t:
            i += 1
            continue
        # running page header -> update period, skip line
        if HEADER_LINE.search(t):
            code = lila_code(t)
            if code:
                period = code
            i += 1
            continue
        # standalone 'X-লীলা' section marker -> update period, reset verse buf
        if SECTION_MARK.match(t):
            code = lila_code(t)
            if code:
                period = code
            buf = []
            verse_start = 0
            i += 1
            continue
        # chapter heading like 'প্রথম-সংগ্ৰহঃ' / 'দ্বিতীয়-সংগ্ৰহঃ'
        if re.match(r"^(প্রথম|দ্বিতীয়)[-\s]*সংগ্ৰহ[ঃখ]?$", t):
            i += 1
            continue
        # page colophon junk -> skip line
        if COLOPHON.match(t) and len(t) < 70:
            i += 1
            continue
        folded = _fold(t)
        em = PADA2_ENDER.search(folded)
        if em:
            num = _norm_num(em.group(1))
            # locate the pāda-1 line: the single danda is on the physical line
            # immediately before the ender (2-line verse) or two lines before it
            # (4-line verse).  The danda line plus at most ONE wrapped line above
            # it is the whole pāda-1, so pāda-1/pāda-2 stay strictly bounded and
            # never absorb translation/commentary or attribution lines.
            d_idx = None
            for j in range(len(buf) - 1, max(-1, len(buf) - 3), -1):
                if j < 0:
                    break
                if buf[j][1].rstrip().endswith(("\u0964", "\u09F7")):
                    d_idx = j
                    break
            if d_idx is not None and d_idx < verse_start:
                d_idx = None
            p1_lines = ([ln for _, ln in buf[max(verse_start, d_idx - 1):d_idx + 1]]
                        if d_idx is not None else [])
            p2_lines = ([ln for _, ln in buf[d_idx + 1:]]
                        if d_idx is not None else [ln for _, ln in buf[verse_start:]])
            pada1 = " ".join(l.rstrip(" .") for l in p1_lines)
            pada2_raw = " ".join(l.rstrip(" .") for l in p2_lines) + " " + folded
            pada2 = re.sub(
                r"(?:।\s*){1,3}" + NUM_CLASS + r"(?:\s*" + NUM_CLASS + r"){0,2}\s*[।॥]+\s*$",
                "", pada2_raw)
            pada2 = pada2.strip(" ,()[]।॥.")
            reason = None
            if d_idx is None:
                reason = "pada1_no_danda"
            rec = {"period": period, "num": num, "pada1": pada1,
                   "pada2": pada2, "attr": None, "page": page,
                   "text": pada1 + " " + pada2}
            if reason:
                rec["reason"] = reason
                broken.append(rec)
            else:
                verses.append(rec)
            buf = []
            verse_start = 0
            # consume attribution lines that follow the ender on their own line
            i += 1
            while i < n:
                nt = lines[i][1].strip()
                if not nt:
                    i += 1
                    continue
                nf = _fold(nt)
                if is_attr_line(nf):
                    rec["attr"] = nf.strip(" .\u200c")
                    i += 1
                    continue
                break
            continue
        else:
            if len(buf) >= 100:
                buf.pop(0)
                verse_start = max(0, verse_start - 1)
            buf.append((page, folded))
            i += 1
    return verses, broken


def main():
    verses, broken = scan()
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(verses, f, ensure_ascii=False, indent=1)
    with open(OUT_BROKEN, "w", encoding="utf-8") as f:
        json.dump(broken, f, ensure_ascii=False, indent=1)

    per = defaultdict(Counter)
    for v in verses:
        per[v["period"]]["clean"] += 1
    for b in broken:
        per[b["period"]][b["reason"]] += 1

    lines = []
    lines.append(f"total clean verses recovered: {len(verses)}")
    lines.append(f"total broken (rule violated):  {len(broken)}")
    lines.append("")
    lines.append(f"{'period':12s} {'printed':>7s} {'clean':>6s} {'pada1_no_danda':>15s}")
    for code in LILA_ORDER:
        p = per.get(code, Counter())
        lines.append(f"{code:12s} {TOC_VERSE_COUNTS.get(code,'-'):>7} "
                     f"{p['clean']:6d} {p['pada1_no_danda']:15d}")
    report = "\n".join(lines)
    with open(OUT_REPORT, "w", encoding="utf-8") as f:
        f.write(report + "\n")
    print(report)
    print(f"\nwrote {OUT_JSON}")
    print(f"wrote {OUT_BROKEN}")
    print(f"wrote {OUT_REPORT}")


if __name__ == "__main__":
    main()
