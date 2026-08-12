# -*- coding: utf-8 -*-
"""
Parse the 700 raw Hindi OCR pages into a clean structured corpus, recovering the
printed structure that hindi_ocr_full.json lost:

  - lila header line:      "अथ प्रात: लीला (४२) श्रीश्री भावना सार संग्रहः"
  - verse block:           Sanskrit padas ending in "।", final verse-ender "।।N।।"
  - attribution:           "(गोवि० ४८७४)" -> book-abbr + chapter.verse (dot often lost)
  - internal section title: "शुक-सारिका का प्रबोधन-प्रकार"
  - translation:           "(४) ..." paragraph whose (N) pairs by number with verse-end N

Output (scripts/hindi_corpus.json):
  { "lilas": [ { "code", "name", "book_page_start", "records": [
        {"t":"lila","page","book_page"},
        {"t":"title","text"},
        {"t":"verse","lines":[..],"end_num":N,"book_slug","attrib_num","page","seq"},
        {"t":"trans","num":N,"lines":[..]} ] } ] }

Usage:
  python scripts/hindi_corpus.py            # stats + review (no write)
  python scripts/hindi_corpus.py --apply    # write scripts/hindi_corpus.json
"""
import sys, re, json, os, glob, unicodedata
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.abspath(__file__))
TXT_DIR = os.environ.get("HINDI_TXT_DIR",
                         r"C:\Users\austr\AppData\Local\Temp\opencode\hindi\tess_450\txt")
OUT_JSON = os.path.join(ROOT, "hindi_corpus.json")
APPLY = "--apply" in sys.argv
DUMP_TITLES = "--dump-titles" in sys.argv

DEVA_DIGITS = "०१२३४५६७८९"
_dmap = {ch: str(i) for i, ch in enumerate(DEVA_DIGITS)}

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

# printed TOC verse counts (completeness cross-check)
TOC_VERSE_COUNTS = {"nishanta": 185, "pratah": 466, "purvahna": 388,
                    "madhyahna": 1317, "aparahna": 110, "sayahna": 99,
                    "pradosha": 214, "nisha": 268}

# abbreviation key from the book's front matter (PART1_13) + OCR variants.
# canonical OCR string -> book slug
ABBR_MAP = {
    "अ०": "alankara-kaustubha", "प०": "padyavali",
    "आ०": "ananda-vrndavana-campu", "भर०": "bhakti-rasamrta-sindhu",
    "उ०": "ujjvala-nilamani", "मा०": "bhagavatam",
    "कर्णा०": "krsna-karnamrta", "कर्णा": "krsna-karnamrta",
    "भाग०": "brhad-bhagavatamrta", "भाग": "brhad-bhagavatamrta",
    "भा०": "bhagavatam", "भा": "bhagavatam", "भ०र": "bhakti-rasamrta-sindhu",
    "कृभा०": "krsna-bhavanamrta", "कृभा": "krsna-bhavanamrta",
    "कृ०भा": "krsna-bhavanamrta", "कु०भा": "krsna-bhavanamrta",
    "कू०भा": "krsna-bhavanamrta", "क०भा": "krsna-bhavanamrta",
    "कृष्णाभा": "krsna-bhavanamrta", "कृ० भा": "krsna-bhavanamrta",
    "कु० भा": "krsna-bhavanamrta", "कृभा०": "krsna-bhavanamrta",
    "कृष्णगणो०": "radha-krsna-ganoddesa-dipika", "कृष्णगणो": "radha-krsna-ganoddesa-dipika",
    "रति०": "govinda-rati-manjari", "रति": "govinda-rati-manjari",
    "कृष्णा०": "krsnahnika-kaumudi", "कृष्णा": "krsnahnika-kaumudi",
    "कष्णा": "krsnahnika-kaumudi", "कप्णा": "krsnahnika-kaumudi",
    "किष्णा": "krsnahnika-kaumudi", "रष्णा": "krsnahnika-kaumudi",
    "कृष्ण": "krsnahnika-kaumudi",
    "रा०": "radha-rasa-sudha-nidhi", "रा": "radha-rasa-sudha-nidhi",
    "क्र०": "krama-dipika", "ल०": "lalita-madhava", "ल": "lalita-madhava",
    "गी०": "gita-govinda", "गी": "gita-govinda", "गीत": "gita-govinda",
    "लह०": "stavamrta-lahari", "गोपा०": "gopala-campu",
    "गोपा": "gopala-campu", "गोपि": "gopala-campu",
    "वि०": "vidagdha-madhava", "वि": "vidagdha-madhava",
    "गोवि०": "govinda-lilamrta", "गोवि": "govinda-lilamrta",
    "गवि": "govinda-lilamrta", "गो०वि": "govinda-lilamrta",
    "गोदि": "govinda-lilamrta", "योवि": "govinda-lilamrta",
    "वृन्दा०": "vrndavana-mahimamrta", "वृन्दा": "vrndavana-mahimamrta",
    "ृन्दा": "vrndavana-mahimamrta",
    "चन्द्रा": "caitanya-candramrta", "चन्द्रो": "caitanya-candrodaya",
    "चन्द्रा०": "caitanya-candramrta",
    "ब्रज०": "vraja-riti-cintamani", "ब्रज": "vraja-riti-cintamani",
    "शेष०": "bhakti-rasamrta-sesa", "सं०": "sangita-madhava", "सं": "sangita-madhava",
    "चै": "caitanya-caritamrta-mahakavya", "चे": "caitanya-caritamrta-mahakavya",
    "चि": "caitanya-caritamrta-mahakavya",
    "साच": "sadhanamrta-candrika", "सा०च": "sadhanamrta-candrika",
    "ज०": "jagannatha-vallabha-nataka",
    "स्त०": "stavamala", "दा०": "dana-keli-kaumudi", "दा": "dana-keli-kaumudi",
    "स्तवा": "stavavali", "स्तवा०": "stavavali",
    "स्तवा०कुसुम": "stavavali-kusumanjali", "स्तवा०कसुम": "stavavali-kusumanjali",
    "रतवा०कुसुम": "stavavali-kusumanjali",
    "स्तवा०विलाप": "vilapa-kusumanjali",
    "स्त०कुज०भंग": "kunja-bhanga", "स्त०कुंजभंग०": "kunja-bhanga",
    "कुंजभंग": "kunja-bhanga", "मधघु०": "madhu-keli-valli",
    "भ०र०": "bhakti-rasamrta-sindhu", "म०र०": "bhakti-rasamrta-sindhu",
    "स्तं०स्वयं": "stavamala", "स्तं०स्व्यं": "stavamala",
    "स्तं०स्वयं०": "stavamala", "स्त०स्वयमुत": "stavamala",
    # single-token forms (after trailing-० rstrip) discovered in OCR
    "ज": "jagannatha-vallabha-nataka", "कु": "krsna-bhavanamrta",
    "क्र": "krama-dipika", "सं": "sangita-madhava",
    "म": "bhakti-rasamrta-sindhu", "म०र": "bhakti-rasamrta-sindhu",
    "प": "padyavali", "कुष्णा": "krsnahnika-kaumudi",
    "न्दा": "vrndavana-mahimamrta", "्ष्णा": "krsnahnika-kaumudi",
    "गावि": "govinda-lilamrta", "लह": "stavamrta-lahari",
    "स्तं": "stavamala", "कुभा": "krsna-bhavanamrta",
    # garbled multi-word forms (gopala-campu chapter 16 verse runs)
    "कु०मा": "gopala-campu", "कृ०मा": "gopala-campu",
    "स्त०कुंजभंग": "kunja-bhanga",
}
# abbrs handled with fuzzy prefix matching (map by first token)
ABBR_PREFIX = [
    ("गोवि", "govinda-lilamrta"), ("कु०भा", "krsna-bhavanamrta"),
    ("कृ०भा", "krsna-bhavanamrta"), ("कू०भा", "krsna-bhavanamrta"),
    ("कृष्णा", "krsnahnika-kaumudi"), ("कृभा", "krsna-bhavanamrta"),
    ("उ०", "ujjvala-nilamani"), ("भा०", "bhagavatam"),
    ("भाग", "brhad-bhagavatamrta"),
]

LILA_HEADER_RE = re.compile(
    r"^\s*(?:अथ\s+)?(?P<lila>[\u0900-\u097f:]{2,14})\s*लीला\s*[\(\[]\s*(?P<page>[०-९\d]{1,4})\s*[\)\]]")
# fallback for garbled headers where "अथ X लीला" appears mid-line
HEADER_FALLBACK = re.compile(r"अथ\s+(?P<lila>[\u0900-\u097f:]{2,14})\s*लीला")
PAGE_ANYWHERE = re.compile(r"[\(\[]\s*([०-९\d]{1,4})\s*[\)\]]")
PAREN_RE = re.compile(r"[\(\{\[][^\)\}\]]*[\)\}\]]")
STRIP_RE = re.compile(r"[\s\.°॰^()|।'\`]")
CONS_RE = re.compile(r"[\u0915-\u0939\u0958-\u095F]")
TRANS_START_RE = re.compile(r"^\s*[\(\[]\s*(?P<num>[०-९\d]{1,4})\s*[\)\]]")
ENDNUM_RE = re.compile(r"।\s*।\s*(?P<n>[०-९\d]{1,3})\s*।\s*।\s*$")
ENDNUM_SINGLE_RE = re.compile(r"।\s*(?P<n>[०-९\d]{1,3})\s*।\s*$")


def extract_attrib(line):
    """Return (match_start, abbr, num_raw) for the rightmost attribution paren-group,
    or None. num is the trailing digit-run of the group; abbr is what precedes it."""
    last = None
    for m in PAREN_RE.finditer(line):
        last = m
    if last is None:
        return None
    m = last
    content = m.group(0)[1:-1].strip()
    mm = re.search(r"([०-९\d][०-९\d\.\,-]{0,15})$", content)
    if not mm:
        return None
    num_raw = mm.group(1).strip()
    abbr = content[:mm.start()].strip()
    if not CONS_RE.search(abbr):
        return None
    if abbr[0] in DEVA_DIGITS or abbr[0].isdigit():
        return None
    if not re.match(r"[\u0900-\u097f]", abbr):
        return None
    if "०" not in abbr and len(num_raw.strip(".,")) < 2:
        return None
    return m.start(), abbr, num_raw


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


def abbr_to_slug(abbr):
    a = STRIP_RE.sub("", abbr)
    for c in (a, a.rstrip("०")):
        if c in ABBR_MAP:
            return ABBR_MAP[c]
    for pre, slug in ABBR_PREFIX:
        if a.startswith(pre) or a.rstrip("०").startswith(pre):
            return slug
    for tok in re.split(r"\s+", abbr):
        t = STRIP_RE.sub("", tok)
        for c in (t, t.rstrip("०")):
            if c in ABBR_MAP:
                return ABBR_MAP[c]
    return None


def norm_devanagari(text):
    """Space/case/danda-insensitive Devanagari identity key (for dedup later)."""
    s = unicodedata.normalize("NFKC", text or "")
    out = []
    for ch in s:
        if "\u0900" <= ch <= "\u097F":
            out.append(ch)
        elif ch in "\u200c\u200d":
            continue
    return "".join(out)


def iter_pages():
    files = glob.glob(os.path.join(TXT_DIR, "*.txt"))
    def keyf(p):
        m1 = re.search(r"PART(\d)", os.path.basename(p))
        m2 = re.search(r"_(\d+)\.txt", os.path.basename(p))
        return (int(m1.group(1)), int(m2.group(1)))
    for p in sorted(files, key=keyf):
        yield os.path.basename(p), open(p, encoding="utf-8").read().splitlines()


def classify(lila, page, line, prev_blank, next_blank, in_trans, pending_verse, cur_trans, recs, seq):
    """classify/emit records for one stripped line. returns (seq, in_trans, cur_trans)."""
    # 1. lila header
    m = LILA_HEADER_RE.match(line)
    if m:
        if pending_verse:
            recs.append({"t": "verse", "lines": pending_verse[:], "end_num": None,
                         "page": page, "seq": seq})
            seq += 1
            pending_verse[:] = []
        if cur_trans:
            cur_trans["seq"] = seq
            recs.append(cur_trans)
            seq += 1
            cur_trans = None
        return seq, False, cur_trans
    # 2. attribution
    if "(" in line or "{" in line or "[" in line:
        ex = extract_attrib(line)
        if ex:
            start, abbr, num_raw = ex
            if start > 0:
                # verse text precedes the inline attribution
                pending_verse.append(line[:start].strip())
            slug = abbr_to_slug(abbr)
            rec = {"t": "attrib", "raw": line.strip(), "abbr": abbr,
                   "abbr_slug": slug, "num_raw": num_raw,
                   "num": to_ascii_num(num_raw), "page": page}
            if pending_verse:
                recs.append({"t": "verse", "lines": pending_verse[:],
                             "end_num": None, "page": page, "seq": seq})
                seq += 1
                pending_verse[:] = []
            rec["seq"] = seq
            recs.append(rec)
            seq += 1
            if cur_trans:
                cur_trans["seq"] = seq
                recs.append(cur_trans)
                seq += 1
                cur_trans = None
            return seq, False, cur_trans
    # 3. translation paragraph start
    m = TRANS_START_RE.match(line)
    if m:
        n = to_ascii_num(m.group("num"))
        if pending_verse:
            recs.append({"t": "verse", "lines": pending_verse[:], "end_num": None,
                         "page": page, "seq": seq})
            seq += 1
            pending_verse[:] = []
        if cur_trans:
            cur_trans["seq"] = seq
            recs.append(cur_trans)
            seq += 1
        cur_trans = {"t": "trans", "num": n, "lines": [], "page": page, "seq": None}
        rest = line[m.end():].strip()
        if rest and CONS_RE.search(rest):
            cur_trans["lines"].append(rest)
        return seq, True, cur_trans
    # 4. section title (short, no danda, flanked by blanks, not starting with digit/paren).
    #    when inside a translation paragraph only a strong heading (ends :-/:) may steal the
    #    line; weak candidates are treated as translation prose.
    STRONG_HEAD = line.rstrip().endswith((":-", ":"))
    if (CONS_RE.search(line) and "।" not in line and "|" not in line
            and "ऽ" not in line
            and 6 <= len(line) <= 60
            and not line[0].isdigit()
            and not line.endswith(",")
            and re.match(r"[\u0900-\u097f]", line)
            and (prev_blank or next_blank)
            and (STRONG_HEAD or not in_trans)
            and line.count(" ") <= 9):
        if pending_verse:
            recs.append({"t": "verse", "lines": pending_verse[:], "end_num": None,
                         "page": page, "seq": seq})
            seq += 1
            pending_verse[:] = []
        if cur_trans:
            cur_trans["seq"] = seq
            recs.append(cur_trans)
            seq += 1
            cur_trans = None
        recs.append({"t": "title", "text": line.strip(), "page": page, "seq": seq})
        seq += 1
        return seq, False, cur_trans
    # 5. other text
    txt = line.strip("। .|")
    if not txt:
        return seq, in_trans, cur_trans
    if in_trans and cur_trans is not None:
        cur_trans["lines"].append(line.strip())
    else:
        pending_verse.append(line.strip())
    return seq, in_trans, cur_trans


def parse_all():
    lilas = []          # list of dicts
    cur = None          # current lila dict
    seq = 0
    pending_verse = []
    cur_trans = None
    in_trans = False
    counters = Counter()

    for fname, lines in iter_pages():
        n = len(lines)
        for i, raw in enumerate(lines):
            line = raw.strip()
            if not line:
                continue
            prev_blank = (i == 0) or not lines[i - 1].strip()
            next_blank = (i == n - 1) or not lines[i + 1].strip()
            # detect lila header before generic classify. the book prints
            # "अथ X लीला (N)" on *every* page, so the real boundary signal is the
            # lila name/code changing; a same-code header is just a page marker.
            m = LILA_HEADER_RE.match(line)
            if m is None and "लीला" in line:
                m = HEADER_FALLBACK.search(line)
            if m:
                code = None
                for c, aliases in LILA_ALIASES:
                    if any(a in m.group("lila") for a in aliases):
                        code = c
                        break
                if code:
                    d = m.groupdict()
                    bpage = d.get("page")
                    if bpage:
                        bpage = to_ascii_num(bpage)
                    else:
                        pm = PAGE_ANYWHERE.search(line)
                        bpage = to_ascii_num(pm.group(1)) if pm else None
                    if cur is not None and code == cur["code"]:
                        # running page header -> update page number only
                        if bpage:
                            cur["book_page"] = bpage
                        continue
                    if cur is not None and pending_verse:
                        cur["records"].append({"t": "verse", "lines": pending_verse[:],
                                               "end_num": None, "page": fname, "seq": seq})
                        seq += 1
                        pending_verse[:] = []
                    if cur is not None and cur_trans:
                        cur_trans["seq"] = seq
                        cur["records"].append(cur_trans)
                        seq += 1
                    cur_trans = None
                    cur = {"code": code, "name": m.group("lila"),
                           "book_page": bpage,
                           "records": []}
                    lilas.append(cur)
                    in_trans = False
                    continue
            # not a lila header -> generic classify against current lila
            if cur is None:
                continue  # front matter
            seq, in_trans, cur_trans = classify(
                cur, fname, line, prev_blank, next_blank, in_trans,
                pending_verse, cur_trans, cur["records"], seq)
            counters["lines"] += 1

    if pending_verse:
        cur["records"].append({"t": "verse", "lines": pending_verse[:],
                               "end_num": None, "page": fname, "seq": seq})
    if cur_trans:
        cur_trans["seq"] = seq
        cur["records"].append(cur_trans)

    # second pass: attach end_num to verse records, detect inline attribs already done
    for l in lilas:
        for r in l["records"]:
            if r["t"] == "verse":
                for ln in reversed(r["lines"]):
                    m = ENDNUM_RE.search(ln)
                    if m:
                        r["end_num"] = to_ascii_num(m.group("n"))
                        r["lines"][-1] = ENDNUM_RE.sub("", ln).strip()
                        break
                    m2 = ENDNUM_SINGLE_RE.search(ln)
                    if m2:
                        r["end_num"] = to_ascii_num(m2.group("n"))
                        r["lines"][-1] = ENDNUM_SINGLE_RE.sub("", ln).strip()
                        break
                r["text"] = " ".join(r["lines"])
                r["norm"] = norm_devanagari(r["text"])
    return lilas, counters


def main():
    lilas, counters = parse_all()
    tot_verses = tot_attrib = tot_trans = tot_title = 0
    print("== corpus per lila ==")
    for l in lilas:
        vs = [r for r in l["records"] if r["t"] == "verse"]
        at = [r for r in l["records"] if r["t"] == "attrib"]
        tr = [r for r in l["records"] if r["t"] == "trans"]
        ti = [r for r in l["records"] if r["t"] == "title"]
        tot_verses += len(vs); tot_attrib += len(at); tot_trans += len(tr); tot_title += len(ti)
        toc = TOC_VERSE_COUNTS.get(l["code"], "?")
        print(f"  {l['code']:<10} p{str(l['book_page']):>4}  verses={len(vs):<5} "
              f"attrib={len(at):<5} trans={len(tr):<5} titles={len(ti):<3}  TOC_verses={toc}")
    print(f"  TOTAL    verses={tot_verses} attrib={tot_attrib} trans={tot_trans} titles={tot_title}")

    slug_c = Counter()
    for l in lilas:
        for r in l["records"]:
            if r["t"] == "attrib" and r.get("abbr_slug"):
                slug_c[r["abbr_slug"]] += 1
    print("\n== attrib book distribution ==")
    for slug, c in slug_c.most_common():
        print(f"  {slug:<30} {c}")
    unk = [r for l in lilas for r in l["records"]
           if r["t"] == "attrib" and not r.get("abbr_slug")]
    print(f"\nunresolved abbrs: {len(unk)}")
    for r in unk[:30]:
        print("   ", r["raw"])

    if DUMP_TITLES:
        print("\n== all section titles ==")
        for l in lilas:
            for r in l["records"]:
                if r["t"] == "title":
                    print(f"  {l['code']:<10} {r['page']:<14} {r['text']}")

    if APPLY:
        json.dump({"lilas": lilas}, open(OUT_JSON, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print(f"\nwrote {OUT_JSON}")


if __name__ == "__main__":
    main()
