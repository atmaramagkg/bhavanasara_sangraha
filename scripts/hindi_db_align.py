# -*- coding: utf-8 -*-
"""
Align Hindi OCR verses to the Bhavana-Sara-Sangraha compilation structure and
assemble, per DB verse row, the Hindi translation (translation_text) and the
Devanagari verse text (original_text_devanagari).

Reference sources
-----------------
  periods nishanta + pratah:  scripts/all_recs_full.json (clean per-verse
      English units with IAST Sanskrit + refs; content-based matching).
  periods purvahna..nisha:    DB verse rows (book, chapter, verse ranges)
      expanded to per-verse units; order + attribution-book matching.

Usage
-----
  python scripts/hindi_db_align.py            # dry-run report
  python scripts/hindi_db_align.py --apply    # write Bhavanasara-Sangraha_Hi.sqlite
"""
import sys, re, json, sqlite3, unicodedata, difflib, os
from collections import defaultdict, Counter

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.abspath(__file__))
HI_DB = os.path.join(ROOT, "..", "assets", "db", "Bhavanasara-Sangraha_Hi.sqlite")
OCR_JSON = os.path.join(ROOT, "hindi_ocr_full.json")
RECS_JSON = os.path.join(ROOT, "all_recs_full.json")
APPLY = "--apply" in sys.argv

LILA_KEYS = ["निशान्त", "प्रात", "पूर्वाह", "मध्याह", "अपराह", "सायाह", "प्रदोष", "नक्त"]
LILA_TO_RANK = {k: i for i, k in enumerate(LILA_KEYS)}
RECS_KEYS = ["Niśānta", "Prātar", "Pūrvāh", "Madhyāh", "Aparāh", "Sāyāh", "Pradoṣa", "Nakta"]
PERIODS = ["nishanta", "pratah", "purvahna", "madhyahna", "aparahna", "sayahna", "pradosha", "nisha"]
RANK_TO_PERIOD = {i: p for i, p in enumerate(PERIODS)}


# --------------------------------------------------------------------------
# IAST -> Devanagari
# --------------------------------------------------------------------------
VOWELS = {'a': 'अ', 'ā': 'आ', 'i': 'इ', 'ī': 'ई', 'u': 'उ', 'ū': 'ऊ',
          'ṛ': 'ऋ', 'ṝ': 'ॠ', 'ḷ': 'ऌ', 'ḹ': 'ॡ', 'e': 'ए', 'ai': 'ऐ',
          'o': 'ओ', 'au': 'औ'}
SIGNS = {'a': '', 'ā': 'ा', 'i': 'ि', 'ī': 'ी', 'u': 'ु', 'ū': 'ू',
         'ṛ': 'ृ', 'ṝ': 'ॄ', 'ḷ': 'ॢ', 'ḹ': 'ॣ', 'e': 'े', 'ai': 'ै',
         'o': 'ो', 'au': 'ौ'}
CONS = {'k': 'क', 'kh': 'ख', 'g': 'ग', 'gh': 'घ', 'ṅ': 'ङ', 'c': 'च',
        'ch': 'छ', 'j': 'ज', 'jh': 'झ', 'ñ': 'ञ', 'ṭ': 'ट', 'ṭh': 'ठ',
        'ḍ': 'ड', 'ḍh': 'ढ', 'ṇ': 'ण', 't': 'त', 'th': 'थ', 'd': 'द',
        'dh': 'ध', 'n': 'न', 'p': 'प', 'ph': 'फ', 'b': 'ब', 'bh': 'भ',
        'm': 'म', 'y': 'य', 'r': 'र', 'l': 'ल', 'v': 'व', 'ś': 'श',
        'ṣ': 'ष', 's': 'स', 'h': 'ह'}
_TOKS = [(k, 'c') for k in sorted(CONS, key=len, reverse=True)] + \
        [(k, 'v') for k in sorted(VOWELS, key=len, reverse=True)] + \
        [('ṃ', 'x'), ('ḥ', 'x')]
_TOKS.sort(key=lambda x: len(x[0]), reverse=True)
_TRE = re.compile("|".join(re.escape(k) for k, _ in _TOKS))
_TTYPE = dict(_TOKS)


def to_devanagari(text):
    text = text.replace('¬', 'ṛ').replace('’', "'").replace('‘', "'")
    toks, out, n = [], [], 0
    s = text
    while s:
        ch = s[0]
        if ch in ' \t\n.' or not (ch.isalnum() or ch in "āīūṛṝḷḹṃḥśṣṅñṭḍṇ"):
            toks.append((ch, 'p'))
            s = s[1:]
            continue
        if ch.isdigit():
            s = s[1:]
            continue
        m = _TRE.match(s)
        if m:
            toks.append((m.group(0), _TTYPE[m.group(0)]))
            s = s[m.end():]
        else:
            toks.append((ch, 'p'))
            s = s[1:]
    idx = 0
    while idx < len(toks):
        tok, typ = toks[idx]
        if typ == 'p':
            out.append(tok)
        elif typ == 'x':
            out.append('ं' if tok == 'ṃ' else 'ः')
        elif typ == 'v':
            out.append(VOWELS[tok])
        else:
            nxt = toks[idx + 1] if idx + 1 < len(toks) else None
            if nxt and nxt[1] == 'v':
                out.append(CONS[tok] + SIGNS[nxt[0]])
                idx += 1
            else:
                out.append(CONS[tok] + '्')
        idx += 1
    return "".join(out)


def skeleton(s):
    s = unicodedata.normalize("NFKC", s or "")
    out = []
    for ch in s:
        if "\u0900" <= ch <= "\u097F":
            cp = ord(ch)
            if 0x0900 <= cp <= 0x0912 or cp in (0x0913, 0x0914):
                out.append("v")
            elif 0x0915 <= cp <= 0x0939 or 0x0958 <= cp <= 0x095F:
                out.append(ch)
        elif ch.isalnum():
            out.append(ch.lower())
    return "".join(out)


def sim(a, b):
    A, B = skeleton(a), skeleton(b)
    if not A or not B:
        return 0.0
    return difflib.SequenceMatcher(None, A, B).ratio()


# --------------------------------------------------------------------------
# DP monotonic alignment
# --------------------------------------------------------------------------
def align(ocr, refs, scorer, gap_m=0.25, gap_s=0.25):
    """Best monotonic assignment ocr[i] -> refs[j]. Returns list of (i, j, score).
    gap_m penalizes a match with score s (net s - gap_m); gap_s penalizes skipping
    an ocr/ref. With gap_m > gap_s a zero-score match is avoided in favor of a skip."""
    n, m = len(ocr), len(refs)
    dp = [[0.0] * (m + 1) for _ in range(n + 1)]
    back = [[""] * (m + 1) for _ in range(n + 1)]
    sims = [[scorer(ocr[i], refs[j]) for j in range(m)] for i in range(n)]
    for i in range(1, n + 1):
        row_s = sims[i - 1]
        dpr, dpc = dp[i], dp[i - 1]
        for j in range(1, m + 1):
            best = max(
                (dpc[j - 1] + row_s[j - 1] - gap_m, "M"),
                (dpc[j] - gap_s, "U"),
                (dpr[j - 1] - gap_s, "R"),
                key=lambda t: t[0])
            dpr[j], back[i][j] = best
    i, j = n, m
    pairs = []
    while i > 0 and j > 0:
        b = back[i][j]
        if b == "M":
            pairs.append((i - 1, j - 1))
            i, j = i - 1, j - 1
        elif b == "U":
            i -= 1
        else:
            j -= 1
    pairs.reverse()
    return [(i, j, sims[i][j]) for i, j in pairs]


# --------------------------------------------------------------------------
# Load OCR
# --------------------------------------------------------------------------
def load_ocr():
    d = json.load(open(OCR_JSON, encoding="utf-8"))
    out = {}
    for s in d["sections"]:
        rank = None
        for k in LILA_KEYS:
            if k in s["lila"]:
                rank = LILA_TO_RANK[k]
                break
        if rank is None:
            continue
        out[rank] = s
    return out


# --------------------------------------------------------------------------
# Load DB structure: per main period, ordered verse rows
# --------------------------------------------------------------------------
def load_db():
    con = sqlite3.connect(HI_DB)
    cur = con.cursor()
    slug_of = {r[0]: r[1] for r in cur.execute("SELECT id, slug FROM books")}
    # main periods in order
    mains = [r for r in cur.execute(
        "SELECT id, code FROM period_nodes WHERE period_type='main' ORDER BY sort_order")]
    rows_by_period = defaultdict(list)
    for pid, code in mains:
        q = """
        SELECT v.id, v.book_id, v.chapter, v.verse_start, v.verse_end, v.ref_display,
               pn.parent_id
        FROM sections s
        JOIN quotes q ON q.section_id = s.id
        JOIN citations c ON c.quote_id = q.id
        JOIN verses v ON v.id = c.source_verse_id
        JOIN period_nodes pn ON pn.id = s.period_node_id
        WHERE pn.parent_id = ?
        ORDER BY pn.sort_order, s.sort_order, q.sort_order, c.rowid
        """
        seen = set()
        for vid, bid, ch, vs, ve, rd, _ in cur.execute(q, (pid,)):
            if vid in seen:
                continue
            seen.add(vid)
            rows_by_period[code].append({
                "id": vid, "slug": slug_of.get(bid), "chapter": ch,
                "v1": num(vs), "v2": num(ve) or num(vs),
                "ref": rd})
    # per (book, chapter) verse range over the whole verses table
    con.close()
    return rows_by_period


def num(x):
    try:
        return int(x)
    except (TypeError, ValueError):
        return None


def attrib_candidates(numstr):
    """Candidate (chapter, verse) parses for a possibly-corrupted attrib number.
    The printed chapter-verse separator (a dot) is often OCR'd as 8/6/0/9."""
    if not numstr:
        return set()
    digs = [d for d in str(numstr) if d.isdigit()]
    if not digs:
        return set()
    out = set()
    s = "".join(digs)
    def add(t):
        for vlen in (1, 2, 3):
            if len(t) > vlen:
                v = int(t[-vlen:])
                ch = int(t[:-vlen])
                out.add((ch, v))
    add(s)
    for i in range(len(s)):
        add(s[:i] + s[i + 1:])
    if len(digs) == 2:
        out.add((int(digs[0]), int(digs[1])))
    return out


def chnum(ch):
    if ch is None:
        return None
    m = re.match(r"(\d+)", str(ch))
    return int(m.group(1)) if m else None


# --------------------------------------------------------------------------
# References
# --------------------------------------------------------------------------
def load_units():
    recs = json.load(open(RECS_JSON, encoding="utf-8"))
    units = {}
    for r in recs:
        sec = r["section"]
        rank = None
        for k in RECS_KEYS:
            if k in sec:
                rank = RECS_KEYS.index(k)
                break
        if rank is None or rank >= 2:
            continue
        v1 = num(str(r.get("v1", "")).split("-")[0])
        if not v1:
            continue
        units.setdefault(rank, []).append({
            "unit": r["unit"], "slug": r["slug"], "chapter": r.get("chapter"),
            "v1": v1, "v2": num(r.get("v2")) or v1,
            "ref": r.get("ref", ""),
            "dev": to_devanagari(r.get("sanskrit", "")),
        })
    for rank in units:
        units[rank].sort(key=lambda u: (u["v1"], u["v2"]))
    return units


# --------------------------------------------------------------------------
# OCR helpers
# --------------------------------------------------------------------------
def pair_translations(sec):
    """Pair each translation to its verse by num (both share the printed number)."""
    verses = sec["verses"]
    trans = sec["translations"]
    by_num = defaultdict(list)
    for idx, v in enumerate(verses):
        if v.get("num") is not None:
            by_num[v["num"]].append(idx)
    assigned = [None] * len(trans)
    used = set()
    for t_idx, t in enumerate(trans):
        tn = t.get("num")
        if tn is not None and by_num.get(tn):
            cand = [i for i in by_num[tn] if i not in used]
            if cand:
                assigned[t_idx] = cand[0]
                used.add(cand[0])
                continue
    # fallback fill: assign unassigned translations to next unmatched verse in order
    v_iter = [i for i in range(len(verses)) if i not in used]
    v_iter.sort()
    k = 0
    for t_idx in range(len(trans)):
        if assigned[t_idx] is None:
            if k < len(v_iter):
                assigned[t_idx] = v_iter[k]
                used.add(v_iter[k])
                k += 1
    return assigned


def main():
    ocr = load_ocr()
    units = load_units()
    dbrows = load_db()
    print(f"periods: {len(dbrows)}   OCR lilas: {sorted(ocr)}   units: {sorted(units)}")

    con = None
    if APPLY:
        con = sqlite3.connect(HI_DB)

    per_row = defaultdict(lambda: {"verses": []})
    stats = {}
    verse_lookup = {}  # (rank, i) -> (verse, translation-or-None)

    for rank in range(8):
        period = RANK_TO_PERIOD[rank]
        rows = dbrows.get(period, [])
        sec = ocr.get(rank)
        if not sec:
            print(f"[{period}] no OCR data")
            continue
        verses = sec["verses"]
        assigned = pair_translations(sec)
        trans = sec["translations"]
        trans_of_verse = {v: t for t, v in enumerate(assigned) if v is not None}
        for i, v in enumerate(verses):
            t = trans[trans_of_verse[i]] if i in trans_of_verse else None
            verse_lookup[(rank, i)] = (v, t)
        stats[period] = {"verses": len(verses), "trans": len(trans),
                         "paired": sum(1 for a in assigned if a is not None)}

        if rank < 2:
            # ---- content-based alignment to English units ----
            refs = units.get(rank, [])
            def scorer(o, r):
                return sim(o["text"], r["dev"])
            pairs = align(verses, refs, scorer)
            # unit -> db row
            by_ref = defaultdict(list)
            for row in rows:
                by_ref[(row["slug"], row["chapter"])].append(row)
            def row_for_unit(u):
                cands = by_ref.get((u["slug"], u["chapter"]), [])
                hits = [r for r in cands
                        if r["v1"] is not None and r["v1"] <= u["v2"] and r["v2"] >= u["v1"]]
                if not hits:
                    return None
                hits.sort(key=lambda r: (r["v2"] or 0) - (r["v1"] or 0))
                return hits[0]
            matched = 0
            for i, j, sc in pairs:
                u = refs[j]
                r = row_for_unit(u)
                if r is None:
                    continue
                matched += 1
                per_row[r["id"]]["verses"].append((rank, i, sc))
            stats[period]["matched_units"] = len(pairs)
            stats[period]["matched_rows"] = matched
        else:
            # ---- order + attribution-book alignment to expanded DB rows ----
            refs = []
            for r in rows:
                for v in range(r["v1"] or 1, (r["v2"] or r["v1"] or 1) + 1):
                    refs.append({"row": r, "slug": r["slug"], "v": v})
            def scorer(o, r):
                oa = o.get("attrib")
                if not oa or oa["abbr"] != r["slug"]:
                    return 0.0
                ref_ch = chnum(r["row"]["chapter"])
                if ref_ch is None:
                    return 0.9
                r1 = r["row"]["v1"] or 0
                r2 = r["row"]["v2"] or r1
                for (c, v) in attrib_candidates(oa["num"]):
                    if c == ref_ch and r1 <= v <= r2:
                        return 1.0
                return 0.9
            pairs = align(verses, refs, scorer, gap_m=0.4, gap_s=0.3)
            # keep only book-correct pairs; a book mismatch means the DB
            # period lacks that verse (partial data), so never write it
            # to a wrong row
            kept = []
            for i, j, sc in pairs:
                oa = verses[i].get("attrib")
                if not oa or oa["abbr"] != refs[j]["slug"]:
                    continue
                kept.append((i, j, sc))
            pairs = kept
            stats[period]["pairs"] = len(pairs)
            matched = 0
            for i, j, sc in pairs:
                rid = refs[j]["row"]["id"]
                matched += 1
                per_row[rid]["verses"].append((rank, i, sc))
            stats[period]["matched"] = matched

    # ----------------------------------------------------------------------
    # Assemble + report
    # ----------------------------------------------------------------------
    print("\n== alignment summary ==")
    for rank in range(8):
        period = RANK_TO_PERIOD[rank]
        st = stats.get(period)
        if not st:
            continue
        rows = dbrows.get(period, [])
        got = sum(1 for r in rows if per_row.get(r["id"]))
        print(f"  {period:<11} ocr={st['verses']:<4} trans={st['trans']:<4} "
              f"paired={st['paired']:<4} rows={len(rows):<3} rows_filled={got}"
              + (f"  pairs={st['pairs']}" if st.get("pairs") is not None else
                 f"  units={st.get('matched_units','-')} rows={st.get('matched_rows','-')}"))

    unaligned = []
    for rank, sec in ocr.items():
        if rank >= 2:
            continue
        refs = units.get(rank, [])
        if not refs:
            continue
        # list units with no OCR match for the report
        pass

    if not APPLY:
        print("\n[dry-run] not writing DB. Re-run with --apply to write.")
        return

    cur = con.cursor()
    n = 0
    n_hi = 0
    for rid, item in per_row.items():
        item["verses"].sort(key=lambda x: (x[0], x[1]))
        cur.execute("SELECT 1 FROM verses WHERE id=?", (rid,))
        if not cur.fetchone():
            continue
        hi_parts, deva_parts = [], []
        for rank, i, sc in item["verses"]:
            v, t = verse_lookup.get((rank, i), (None, None))
            if t is not None:
                hi_parts.append(t["text"])
            if v is not None:
                deva_parts.append(v["text"])
        hi_text = " ".join(hi_parts).strip() or None
        deva_text = " ".join(deva_parts).strip() or None
        if hi_text:
            n_hi += 1
        cur.execute("UPDATE verses SET translation_text=?, original_text_devanagari=? WHERE id=?",
                    (hi_text, deva_text, rid))
        n += 1
    con.commit()
    con.close()
    print(f"\nHi DB updated: {n} rows ({n_hi} with Hindi text)")


if __name__ == "__main__":
    main()
