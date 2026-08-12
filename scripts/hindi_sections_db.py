# -*- coding: utf-8 -*-
"""Map the Hindi book's OCR-detected sections to DB quotes and persist them.

Two-stage mapping, both monotonic, using the printed attribution numbers as
anchors (identical on both sides since both parse the same raw text):

  Stage A  my-corpus (seq)  ->  OCR verse index
      anchor every my-corpus attrib record to the OCR verse that carries the
      same (book slug, printed num); interpolate verse records in between.

  Stage B  OCR verse index  ->  DB verse row
      replicate hindi_db_align's per-row alignment (content-based for the
      first two periods, attribution-book based for the rest).

Compose the two, then a section (first_seq..last_seq) owns every period quote
whose source verse maps into its row range; order = book order.

Usage:
  python scripts/hindi_sections_db.py             # dry-run report
  python scripts/hindi_sections_db.py --apply     # write hi_sections + hi_section_quotes
"""
import sys, re, json, sqlite3, os, shutil, time, difflib
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.abspath(__file__))
HI_DB = os.path.join(ROOT, "..", "assets", "db", "Bhavanasara-Sangraha_Hi.sqlite")
CORPUS = os.path.join(ROOT, "hindi_corpus.json")
SECTIONS = os.path.join(ROOT, "hindi_sections.json")
APPLY = "--apply" in sys.argv

sys.path.insert(0, ROOT)
import hindi_corpus as hc
import hindi_db_align as hal

PERIODS = hal.PERIODS


# --------------------------------------------------------------------------
# Stage A: my-corpus attribs -> OCR verse indices (exact slug+num anchors)
# --------------------------------------------------------------------------
def build_ocr_attrib_index(ocr):
    """per rank: (slug, num_str) -> ordered list of OCR verse indices."""
    idx = defaultdict(list)
    for rank, sec in ocr.items():
        for i, v in enumerate(sec["verses"]):
            a = v.get("attrib")
            if a:
                idx[(rank, a["abbr"], str(a["num"]))].append(i)
    return idx


def my_to_ocr_anchors(records, ocr, attrib_idx):
    """Ordered list of (my_seq, ocr_idx) anchors; each OCR attrib used once."""
    anchors = []
    used = defaultdict(set)  # (rank, slug, num) -> used ocr idx
    rank = None
    for rec in records:
        if rec["t"] == "attrib":
            slug = hc.abbr_to_slug(rec["abbr"])
            if slug is None:
                continue
            key = (rank, slug, str(rec["num"]))
            for i in attrib_idx.get(key, []):
                if i not in used[key]:
                    used[key].add(i)
                    anchors.append((rec["seq"], i))
                    break
        else:
            # infer rank lazily from the lila context set by caller
            pass
    anchors.sort()
    return anchors


def make_seq_to_ocr(anchors, n_ocr):
    """seq -> ocr_idx via piecewise linear interpolation (slope-extrapolated)."""
    if not anchors:
        return lambda s: min(max(int(s), 0), n_ocr - 1) if n_ocr else 0
    if len(anchors) == 1:
        row = anchors[0][1]
        return lambda s: row
    ls = [a[0] for a in anchors]
    lr = [a[1] for a in anchors]
    hd_m = 0.0
    if ls[1] > ls[0]:
        hd_m = max(0.0, (lr[1] - lr[0]) / (ls[1] - ls[0]))
    tl_m = 0.0
    if ls[-1] > ls[-2]:
        tl_m = max(0.0, (lr[-1] - lr[-2]) / (ls[-1] - ls[-2]))

    def f(s):
        if s < ls[0]:
            return max(0, min(n_ocr - 1, round(lr[0] - hd_m * (ls[0] - s))))
        if s > ls[-1]:
            return max(0, min(n_ocr - 1, round(lr[-1] + tl_m * (s - ls[-1]))))
        for k in range(1, len(ls)):
            if s <= ls[k]:
                s0, s1, r0, r1 = ls[k - 1], ls[k], lr[k - 1], lr[k]
                if s1 == s0:
                    return r1
                return r0 + round((r1 - r0) * (s - s0) / (s1 - s0))
        return lr[-1]
    return f


# --------------------------------------------------------------------------
# Stage B: OCR verse index -> DB row index (replicate hindi_db_align)
# --------------------------------------------------------------------------
def load_db_rows():
    """per period: rows list + vid->index, in book order."""
    con = sqlite3.connect(HI_DB)
    cur = con.cursor()
    slug_of = {r[0]: r[1] for r in cur.execute("SELECT id, slug FROM books")}
    mains = [r for r in cur.execute(
        "SELECT id, code FROM period_nodes WHERE period_type='main' ORDER BY sort_order")]
    out = {}
    for pid, code in mains:
        q = """
        SELECT v.id, v.book_id, v.chapter, v.verse_start, v.verse_end, v.ref_display
        FROM sections s
        JOIN quotes q ON q.section_id = s.id
        JOIN citations c ON c.quote_id = q.id
        JOIN verses v ON v.id = c.source_verse_id
        JOIN period_nodes pn ON pn.id = s.period_node_id
        WHERE pn.parent_id = ?
        ORDER BY pn.sort_order, s.sort_order, q.sort_order, c.rowid
        """
        seen, rows, idx = set(), [], {}
        for vid, bid, ch, vs, ve, rd in cur.execute(q, (pid,)):
            if vid in seen:
                continue
            seen.add(vid)
            rows.append({"id": vid, "slug": slug_of.get(bid), "chapter": ch,
                         "v1": hal.num(vs), "v2": hal.num(ve) or hal.num(vs), "ref": rd})
            idx[vid] = len(rows) - 1
        out[code] = (rows, idx)
    con.close()
    return out


def ocr_to_row_mapping(ocr, dbrows):
    """per rank: dict ocr_idx -> db row index."""
    units = hal.load_units()
    mapping = {}
    for rank in range(8):
        period = PERIODS[rank]
        rows = dbrows.get(period)
        if not rows:
            continue
        (rows, idx) = rows
        sec = ocr.get(rank)
        if not sec:
            continue
        verses = sec["verses"]
        if rank < 2:
            refs = units.get(rank, [])
            def scorer(o, r):
                return hal.sim(o["text"], r["dev"])
            pairs = hal.align(verses, refs, scorer)
            by_ref = defaultdict(list)
            for ri, row in enumerate(rows):
                by_ref[(row["slug"], row["chapter"])].append(ri)
            for i, j, sc in pairs:
                u = refs[j]
                cands = by_ref.get((u["slug"], u["chapter"]), [])
                hits = [ri for ri in cands
                        if rows[ri]["v1"] is not None and rows[ri]["v1"] <= u["v2"]
                        and rows[ri]["v2"] >= u["v1"]]
                if not hits:
                    continue
                hits.sort(key=lambda ri: (rows[ri]["v2"] or 0) - (rows[ri]["v1"] or 0))
                mapping[(rank, i)] = hits[0]
        else:
            refs = []
            for ri, r in enumerate(rows):
                for v in range(r["v1"] or 1, (r["v2"] or r["v1"] or 1) + 1):
                    refs.append({"row": ri, "slug": r["slug"], "v": v,
                                 "chapter": r["chapter"], "v1": r["v1"], "v2": r["v2"]})
            def scorer(o, r):
                oa = o.get("attrib")
                if not oa or oa["abbr"] != r["slug"]:
                    return 0.0
                ref_ch = hal.chnum(r["chapter"])
                if ref_ch is None:
                    return 0.9
                for (c, v) in hal.attrib_candidates(oa["num"]):
                    if c == ref_ch and r["v1"] <= v <= (r["v2"] or r["v1"]):
                        return 1.0
                return 0.9
            pairs = hal.align(verses, refs, scorer, gap_m=0.4, gap_s=0.3)
            for i, j, sc in pairs:
                oa = verses[i].get("attrib")
                if not oa or oa["abbr"] != refs[j]["slug"]:
                    continue
                mapping[(rank, i)] = refs[j]["row"]
    return mapping


def ocr_to_row_backbone(ocr, dbrows):
    """OCR verse index -> DB row index, mirroring hindi_backbone's Phase 1+2
    content-anchor + interpolation mapping (the mapping that actually filled
    the DB rows' Hindi content)."""
    con = sqlite3.connect(HI_DB)
    cur = con.cursor()
    MAXK = 25

    def ratio(a, b):
        return difflib.SequenceMatcher(None, a, b).ratio()

    def chkey(ch):
        m = re.match(r"(\d+)", str(ch))
        return int(m.group(1)) if m else None

    win_skel = {}
    for rank in range(8):
        sec = ocr.get(rank)
        if not sec:
            continue
        vsk = [hal.skeleton(v["text"]) for v in sec["verses"]]
        n = len(vsk)
        ws = {}
        for k in range(1, min(MAXK, n) + 1):
            ws[k] = ["".join(vsk[w:w + k]) for w in range(0, n - k + 1)]
        win_skel[rank] = ws

    # per-rank window length lists for the Phase-1 length prefilter
    win_len = {}
    for rank, ws in win_skel.items():
        win_len[rank] = {k: [len(s) for s in lst] for k, lst in ws.items()}

    anchors = {}
    for rank in range(8):
        sec = ocr.get(rank)
        if not sec:
            continue
        ws = win_skel[rank]
        wl = win_len[rank]
        n = len(sec["verses"])
        rows, _ = dbrows.get(PERIODS[rank], ([], {}))
        for ri, r in enumerate(rows):
            orig = cur.execute("SELECT original_text FROM verses WHERE id=?", (r["id"],)).fetchone()[0] or ""
            if not orig.strip() or not r["v1"]:
                continue
            v1, v2 = r["v1"], r["v2"] or r["v1"]
            klen = min(v2 - v1 + 1, MAXK)
            dev_sk = hal.skeleton(hal.to_devanagari(orig))
            dlen = len(dev_sk)
            best = None
            for k in range(max(1, klen - 1), min(klen + 3, MAXK) + 1):
                if k > n:
                    continue
                row = ws[k]
                lens = wl[k]
                for w in range(0, len(row)):
                    if abs(lens[w] - dlen) > 0.35 * max(1, dlen):
                        continue
                    sc = ratio(dev_sk, row[w])
                    if best is None or sc > best[0]:
                        best = (sc, w, k)
            if best is None or best[0] < 0.5:
                continue
            sc, w, k = best
            second = 0.0
            for ww in range(0, len(ws[k])):
                if ww == w:
                    continue
                if abs(wl[k][ww] - dlen) > 0.35 * max(1, dlen):
                    continue
                s2 = ratio(dev_sk, ws[k][ww])
                if s2 > second:
                    second = s2
            uniq = (sc - second) / max(0.01, sc)
            anchors[r["id"]] = (rank, sc, w, k, uniq)

    accepted = {}
    used_windows = []
    for rid in sorted(anchors, key=lambda r: anchors[r][1], reverse=True):
        rank, sc, w, k, uniq = anchors[rid]
        if sc < 0.55 or uniq < 0.15:
            continue
        if any(rank == ar and not (w + k - 1 < aw or aw + ak - 1 < w)
               for ar, aw, ak in used_windows):
            continue
        accepted[rid] = (rank, sc, w, k, uniq)
        used_windows.append((rank, w, k))

    used = defaultdict(set)
    for rid, (rank, sc, w, k, uniq) in accepted.items():
        for i in range(w, w + k):
            used[rank].add(i)

    interp = {}
    for rank in range(8):
        rows, _ = dbrows.get(PERIODS[rank], ([], {}))
        sec = ocr.get(rank)
        if not sec:
            continue
        n_ocr = len(sec["verses"])
        by_book_ch = defaultdict(list)
        for r in rows:
            by_book_ch[(r["slug"], chkey(r["chapter"]))].append(r)
        for (slug, c), lst in by_book_ch.items():
            lst.sort(key=lambda r: (r["v1"] or 0, r["v2"] or 0))
            verse_anchors = []
            for r in lst:
                if r["v1"] is None:
                    continue
                acc = accepted.get(r["id"])
                if acc is None:
                    continue
                _, sc_, w_, k_, _ = acc
                v1, v2 = r["v1"], r["v2"] or r["v1"]
                for i, v in enumerate(range(v1, v2 + 1)):
                    if w_ + i <= w_ + k_ - 1:
                        verse_anchors.append((v, w_ + i))
            verse_anchors.sort()
            for r in lst:
                if r["id"] in accepted or r["v1"] is None:
                    continue
                v1, v2 = r["v1"], r["v2"] or r["v1"]
                prev_a = [a for a in verse_anchors if a[0] < v1]
                next_a = [a for a in verse_anchors if a[0] > v2]
                if prev_a and next_a:
                    a_lo, a_hi = prev_a[-1]
                    b_lo, b_hi = next_a[0]
                    start = a_hi + (v1 - a_lo)
                    end = a_hi + (v2 - a_lo)
                    gap_verses = b_lo - a_lo - 1
                    gap_ocr = b_hi - a_hi - 1
                    conf = 1.0 - abs(gap_verses - gap_ocr) / max(1, gap_verses)
                elif prev_a:
                    start = prev_a[-1][1] + (v1 - prev_a[-1][0])
                    end = prev_a[-1][1] + (v2 - prev_a[-1][0])
                    conf = 0.4
                elif next_a:
                    start = next_a[0][1] - (next_a[0][0] - v1)
                    end = next_a[0][1] - (next_a[0][0] - v2)
                    conf = 0.4
                else:
                    continue
                if start < 0 or end >= n_ocr or end < start or conf < 0.6:
                    continue
                if any(i in used[rank] for i in range(start, end + 1)):
                    continue
                interp[r["id"]] = (rank, start, end)
                for i in range(start, end + 1):
                    used[rank].add(i)
    con.close()

    # map verse id -> row index per period
    id_to_row = {}
    for period, (rows, idx) in dbrows.items():
        for ri, r in enumerate(rows):
            id_to_row[r["id"]] = (period, ri)
    mapping = {}
    for rid, (rank, sc, w, k, uniq) in accepted.items():
        if id_to_row.get(rid, (None, None))[0] == PERIODS[rank]:
            for i in range(w, w + k):
                mapping[(rank, i)] = id_to_row[rid][1]
    for rid, (rank, start, end) in interp.items():
        if id_to_row.get(rid, (None, None))[0] == PERIODS[rank]:
            for i in range(start, end + 1):
                mapping[(rank, i)] = id_to_row[rid][1]
    return mapping


def ocr_to_row_containment(ocr, dbrows):
    """OCR verse index -> DB row index via skeleton containment: a row's
    original_text_devanagari is the join of its OCR verses, so the inverse
    recovers the exact (rank, ocr_idx) -> row mapping from the DB itself."""
    con = sqlite3.connect(HI_DB)
    cur = con.cursor()
    mapping = {}
    for rank in range(8):
        rows, _ = dbrows.get(PERIODS[rank], ([], {}))
        sec = ocr.get(rank)
        if not sec:
            continue
        vsk = [hal.skeleton(v["text"]) for v in sec["verses"]]
        for ri, r in enumerate(rows):
            d = cur.execute("SELECT original_text_devanagari FROM verses WHERE id=?",
                            (r["id"],)).fetchone()[0]
            if not d:
                continue
            dsk = hal.skeleton(d)
            for i, s in enumerate(vsk):
                if s and s in dsk:
                    mapping[(rank, i)] = ri
    con.close()
    return mapping


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------
def main():
    t0 = time.time()
    corpus = json.load(open(CORPUS, encoding="utf-8"))
    sections = json.load(open(SECTIONS, encoding="utf-8"))
    ocr = hal.load_ocr()
    dbrows = load_db_rows()
    attrib_idx = build_ocr_attrib_index(ocr)
    ROWMAP_CACHE = os.path.join(ROOT, "hindi_ocr_row_map.json")
    if os.path.exists(ROWMAP_CACHE):
        row_mapping = {(int(k.split(":")[0]), int(k.split(":")[1])): v
                       for k, v in json.load(open(ROWMAP_CACHE, encoding="utf-8")).items()}
    else:
        row_mapping = {}
        for fn in (ocr_to_row_mapping, ocr_to_row_backbone, ocr_to_row_containment):
            row_mapping.update(fn(ocr, dbrows))
        json.dump({f"{r}:{i}": v for (r, i), v in row_mapping.items()},
                  open(ROWMAP_CACHE, "w", encoding="utf-8"), ensure_ascii=False)

    # period quotes in book order
    con = sqlite3.connect(HI_DB)
    cur = con.cursor()
    q_period = defaultdict(list)
    for pid, code in [r for r in cur.execute(
            "SELECT id, code FROM period_nodes WHERE period_type='main' ORDER BY sort_order")]:
        q = """
        SELECT DISTINCT q.id, v.id
        FROM sections s
        JOIN quotes q ON q.section_id = s.id
        JOIN citations c ON c.quote_id = q.id
        JOIN verses v ON v.id = c.source_verse_id
        JOIN period_nodes pn ON pn.id = s.period_node_id
        WHERE pn.parent_id = ?
        """
        for qid, vid in cur.execute(q, (pid,)):
            q_period[code].append((qid, vid))
    trans_of = dict(cur.execute("SELECT id, translation_text FROM verses"))
    con.close()

    per_section = {}
    report = []
    all_quotes = set()
    assigned = set()
    n_anchors = 0
    qids_by_sec = defaultdict(list)

    for l in corpus["lilas"]:
        code = l["code"]
        rank = PERIODS.index(code)
        rows, idx = dbrows.get(code, (None, None))
        if rows is None:
            report.append((code, "(no db rows)", 0, 0, "-"))
            continue
        records = l["records"]

        # anchors (inject rank into the walk)
        anchors = []
        used = defaultdict(set)
        for rec in records:
            if rec["t"] == "attrib":
                slug = hc.abbr_to_slug(rec["abbr"])
                if slug is None:
                    continue
                key = (rank, slug, str(rec["num"]))
                for i in attrib_idx.get(key, []):
                    if i not in used[key]:
                        used[key].add(i)
                        anchors.append((rec["seq"], i))
                        break
        anchors.sort()
        n_anchors += len(anchors)
        f = make_seq_to_ocr(anchors, len(ocr[rank]["verses"]))

        secs = [x for x in sections if x["code"] == code][0]["sections"]

        # seq -> db row index (forward/backward fill so every verse record maps)
        seq_to_row = {}
        verse_records = [r for r in records if r["t"] == "verse"]
        for r in verse_records:
            oi = f(r["seq"])
            row_idx = row_mapping.get((rank, oi))
            if row_idx is not None:
                seq_to_row[r["seq"]] = row_idx
        prev = None
        for r in verse_records:
            if r["seq"] in seq_to_row:
                prev = seq_to_row[r["seq"]]
            elif prev is not None:
                seq_to_row[r["seq"]] = prev
        nxt = None
        for r in reversed(verse_records):
            if r["seq"] in seq_to_row:
                nxt = seq_to_row[r["seq"]]
            elif nxt is not None:
                seq_to_row[r["seq"]] = nxt

        # invert: row index -> [min_seq, max_seq] so a quote's row maps back to
        # a seq position. Unreached rows get a seq midpoint interpolated from
        # the nearest reached rows (row order == book order == seq order).
        row_seq = defaultdict(lambda: [10**9, -1])
        for s, ri in seq_to_row.items():
            row_seq[ri][0] = min(row_seq[ri][0], s)
            row_seq[ri][1] = max(row_seq[ri][1], s)
        reached = sorted(row_seq)
        for qid, vid in q_period.get(code, []):
            if vid not in idx:
                continue
            ri = idx[vid]
            if ri in row_seq:
                a, b = row_seq[ri]
                mid = (a + b) / 2
            else:
                lo_i = max((i for i in range(len(reached)) if reached[i] <= ri), default=None)
                hi_i = min((i for i in range(len(reached)) if reached[i] >= ri), default=None)
                if lo_i is not None and hi_i is not None and reached[lo_i] != reached[hi_i]:
                    mid = (row_seq[reached[lo_i]][1] + row_seq[reached[hi_i]][0]) / 2
                elif lo_i is not None:
                    a, b = row_seq[reached[lo_i]]
                    mid = (a + b) / 2
                elif hi_i is not None:
                    a, b = row_seq[reached[hi_i]]
                    mid = (a + b) / 2
                else:
                    continue
            target = None
            for s in secs:
                if s["first_seq"] <= mid <= s["last_seq"]:
                    target = s
                    break
            if target is not None and (code, qid) not in assigned and trans_of.get(vid):
                qids_by_sec[(code, target["heading"])].append(qid)
                assigned.add((code, qid))

        for s in secs:
            qids = qids_by_sec[(code, s["heading"])]
            per_section[(code, s["heading"])] = qids
            all_quotes.update((code, q) for q, _ in q_period.get(code, []))
            report.append((code, s["heading"], s["verses"], len(qids), s["page"]))

    print("== per-section mapping ==")
    for code, heading, nv, nq, page in report:
        print(f"  {code:<10} v={nv:<3} q={nq:<3} p={page} | {heading[:70]}")
    print()
    print(f"anchors: {n_anchors}   quotes assigned: {len(assigned)} / {len(all_quotes)} "
          f"({100*len(assigned)/max(1,len(all_quotes)):.1f}%)  elapsed {time.time()-t0:.1f}s")

    dump = os.path.join(ROOT, "hi_section_quotes.json")
    json.dump({f"{code}|{heading}": qids
               for (code, heading), qids in per_section.items()},
              open(dump, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"dumped {dump}")

    if not APPLY:
        print("\n[dry-run] not writing DB. Re-run with --apply.")
        return

    # ---- write ----
    bak = HI_DB + ".bak"
    shutil.copyfile(HI_DB, bak)
    con = sqlite3.connect(HI_DB)
    cur = con.cursor()
    cur.execute("DROP TABLE IF EXISTS hi_sections")
    cur.execute("DROP TABLE IF EXISTS hi_section_quotes")
    cur.execute("""
        CREATE TABLE hi_sections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            main_period TEXT NOT NULL,
            sort_order INTEGER NOT NULL,
            heading TEXT NOT NULL,
            heading_clean TEXT NOT NULL,
            page INTEGER,
            n_verses INTEGER NOT NULL DEFAULT 0,
            n_quotes INTEGER NOT NULL DEFAULT 0,
            first_seq INTEGER,
            last_seq INTEGER,
            first_page INTEGER,
            last_page INTEGER
        )""")
    cur.execute("""
        CREATE TABLE hi_section_quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            section_id INTEGER NOT NULL,
            quote_id INTEGER NOT NULL,
            sort_order INTEGER NOT NULL
        )""")
    cur.execute("CREATE INDEX idx_hisq_section ON hi_section_quotes(section_id)")
    n_sec = n_q = 0
    for l in corpus["lilas"]:
        code = l["code"]
        rank = PERIODS.index(code)
        rows, idx = dbrows.get(code, (None, None))
        if rows is None:
            continue
        secs = [x for x in sections if x["code"] == code][0]["sections"]
        for so, s in enumerate(secs):
            heading = s["heading"]
            clean = heading.strip().strip("\u200c\u200d. ।:-")
            qids = per_section[(code, heading)]
            cur.execute(
                "INSERT INTO hi_sections (main_period, sort_order, heading, heading_clean,"
                " page, n_verses, n_quotes, first_seq, last_seq, first_page, last_page)"
                " VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (code, so, heading, clean, s["page"], s["verses"], len(qids),
                 s["first_seq"], s["last_seq"], s["page"], s["last_page"]))
            sid = cur.lastrowid
            for qo, qid in enumerate(qids):
                cur.execute("INSERT INTO hi_section_quotes (section_id, quote_id, sort_order)"
                            " VALUES (?,?,?)", (sid, qid, qo))
                n_q += 1
            n_sec += 1
    con.commit()
    con.close()
    print(f"\nHi DB updated: {n_sec} sections, {n_q} section-quote links. Backup: {bak}")


if __name__ == "__main__":
    main()
