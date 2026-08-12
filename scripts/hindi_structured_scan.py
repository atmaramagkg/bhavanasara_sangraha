# -*- coding: utf-8 -*-
"""
Structural Hindi verse scan enforcing the Sanskrit verse-layout rule.

RULE (the way Sanskrit verses are printed, extremely consistent):
  verse = TWO lines
    line 1 (pāda 1 + pāda 2): ends with a SINGLE danda  ।   (U+0964)
    line 2 (pāda 3 + pāda 4): ends with
          DOUBLE danda  +  verse number  +  DOUBLE danda   ।।N।।
    optionally followed by an inline attribution  (book-abbr N)
  Every Sanskrit verse that does NOT follow this rule was OCR-split at the
  wrong place and is flagged as broken (reason: pada1_no_danda / no_pada1).

Input:  the raw Hindi OCR pages (tess_450/txt), one text file per page.
Output: scripts/hindi_structured_verses.json  (clean verses only, two padas each)
        scripts/hindi_structured_broken.json  (verses that violate the rule)
        scripts/hindi_structured_report.txt  (per-period stats vs printed TOC)

Usage:
  python scripts/hindi_structured_scan.py
  (set HINDI_TXT_DIR to point at the OCR txt folder if not the default)
"""
import os, re, sys, json, glob
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.stdout.reconfigure(encoding="utf-8")

TXT_DIR = os.environ.get(
    "HINDI_TXT_DIR",
    r"C:\Users\austr\AppData\Local\Temp\opencode\hindi\tess_450\txt",
)
OUT_JSON = os.path.join(ROOT, "hindi_structured_verses.json")
OUT_BROKEN = os.path.join(ROOT, "hindi_structured_broken.json")
OUT_REPORT = os.path.join(ROOT, "hindi_structured_report.txt")

# ---- the rule, encoded as regexes ------------------------------------------
DEVA_DIGITS = "०१२३४५६७८९"
_dmap = {ch: str(i) for i, ch in enumerate(DEVA_DIGITS)}
NUM = r"[०-९0-9]{1,4}"                 # OCR mixes Devanagari and ASCII digits
DANDA = r"।"                            # U+0964 single danda
DDANDA = r"(?:।।|॥)"                    # double danda (both renderings occur)

# line 2 ender:  (double) danda + number + double danda   at end of line.
# OCR often collapses the leading double danda to a single one (। N ।।), may
# render dandas as ASCII pipes (| 1 ||), and may append an inline attribution
# (गोवि० २८४५) after the ender on the same line, so normalize dandas first and
# match the ender followed by an optional attribution and/or trailing noise.
def _fold(line):
    return line.replace("॥", "।।").replace("||", "।।").replace("|", "।")

# OCR often renders the pāda-1 single danda (U+0964) as an ASCII pipe, or at
# line end as ! ` or ?.  Sanskrit has none of those, so a line-ending one is a
# danda; normalize it.
_PADA1_ARTIFACTS = "!?`"
def _norm_pada1(line):
    s = _fold(line)
    if s and s[-1] in _PADA1_ARTIFACTS:
        s = s[:-1] + "।"
    return s

# When OCR merges two printed lines into one OCR line, the pāda-1 line ends up
# as  "...danda + start of pāda-2".  Split at the LAST danda: head is pāda-1,
# tail is the fragment of pāda-2 to prepend to the ender line.  If the tail is
# only punctuation noise (e.g. ". -"), drop it instead.
def _split_pada1(line):
    s = line.rstrip()
    idx = s.rfind("।")
    if idx == -1 or idx == len(s) - 1:
        return s, ""
    tail = s[idx + 1:].strip()
    if re.search(r"[\u0900-\u097f]", tail):
        return s[:idx + 1], tail
    return s[:idx + 1], ""

PADA2_ENDER = re.compile(
    r"(?:।\s*){1,3}([०-९0-9]{1,4})\s*।।"
    r"(?:\s*[\(\[]\s*[^\(\)\[\]]+\s*[\)\]])?\s*$"
)
# trailing OCR noise that may follow a verse ender on the same line
TAIL_NOISE = re.compile(r"[\)\.\.,;:'\"`\s]+$")

# lila header:  "अथ निशान्त लीला (१७)"  or  "श्रीश्री भावना सार संग्रहः (१७) अथ निशान्त लीला"
LILA_ALIASES = [
    ("nishanta", ["निशान्त"]),
    ("pratah", ["प्रात", "प्रात:"]),
    ("purvahna", ["पूर्वाह", "पूर्वाह्न"]),
    ("madhyahna", ["मध्याह", "मध्याह्न"]),
    ("aparahna", ["अपराह", "अपराह्न"]),
    ("sayahna", ["सायाह", "सायाह्न"]),
    ("pradosha", ["प्रदोष"]),
    ("nisha", ["नक्त"]),
]
HEADER_RE = re.compile(
    r"^\s*(?:अथ\s+)?(?P<lila>[\u0900-\u097f:]{2,14})\s*लीला"
)
HEADER_FALLBACK = re.compile(r"अथ\s+([\u0900-\u097f]{2,14})\s*लीला")

# printed verse counts per period (from the book's own table of contents)
TOC_VERSE_COUNTS = {"nishanta": 185, "pratah": 466, "purvahna": 388,
                    "madhyahna": 1317, "aparahna": 110, "sayahna": 99,
                    "pradosha": 214, "nisha": 268}


def to_ascii_num(s):
    if not s:
        return None
    out = []
    for ch in s.strip():
        if ch in _dmap:
            out.append(_dmap[ch])
        elif ch.isdigit():
            out.append(ch)
    try:
        return int("".join(out))
    except ValueError:
        return None


def code_for(lila_name):
    n = lila_name.rstrip(":").strip()
    for code, aliases in LILA_ALIASES:
        if n in aliases or any(n.startswith(a) for a in aliases):
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


def scan_lines(lines):
    """Apply the verse-layout rule to an iterable of (page_label, raw_line).
    Returns (verses, broken).  verses/broken are dicts with pada1, pada2, text,
    period, num, page (plus 'reason' when broken).  Period is tracked across the
    whole stream via lila headers, so this works per-page or per-corpus."""
    verses = []
    broken = []
    period = None
    prev_text = None

    for page, raw in lines:
        t = raw.strip()
        if not t:
            continue
        # lila header -> switch period
        m = HEADER_RE.match(t) or HEADER_FALLBACK.search(t)
        if m:
            name = m.group("lila") if "lila" in m.groupdict() else m.group(1)
            code = code_for(name)
            if code:
                period = code
            continue
        # does this line end like a proper pāda-2 (।।N।।) ?
        folded = _fold(t)
        em = PADA2_ENDER.search(folded)
        if em:
            num = to_ascii_num(em.group(1))
            ender_line = folded[:em.start()].rstrip(" ,")
            ender_line = TAIL_NOISE.sub("", ender_line)
            pada1, pada2_prefix = "", ""
            if prev_text:
                pada1, pada2_prefix = _split_pada1(_norm_pada1(prev_text))
                pada1 = pada1.strip()
            reason = None
            if not pada1:
                reason = "no_pada1"
            elif not pada1.endswith("।"):
                reason = "pada1_no_danda"
            pada2 = (pada2_prefix + " " + ender_line).strip()
            pada2 = TAIL_NOISE.sub("", pada2)
            rec = {"period": period, "num": num, "pada1": pada1,
                   "pada2": pada2, "page": page,
                   "text": pada1 + " " + pada2}
            if reason:
                rec["reason"] = reason
                broken.append(rec)
            else:
                verses.append(rec)
            prev_text = None
        else:
            prev_text = t

    return verses, broken


def scan():
    verses = []
    broken = []
    return scan_lines(iter_lines())


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
    lines.append(f"{'period':12s} {'printed':>7s} {'clean':>6s} {'no_pada1':>9s} {'pada1_no_danda':>15s}")
    for code, _ in LILA_ALIASES:
        p = per.get(code, Counter())
        lines.append(f"{code:12s} {TOC_VERSE_COUNTS.get(code,'-'):>7} "
                     f"{p['clean']:6d} {p['no_pada1']:9d} {p['pada1_no_danda']:15d}")
    report = "\n".join(lines)
    with open(OUT_REPORT, "w", encoding="utf-8") as f:
        f.write(report + "\n")
    print(report)
    print(f"\nwrote {OUT_JSON}")
    print(f"wrote {OUT_BROKEN}")
    print(f"wrote {OUT_REPORT}")


if __name__ == "__main__":
    main()
