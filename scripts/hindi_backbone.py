# -*- coding: utf-8 -*-
"""
Backbone apply: content-anchor + interpolate missing Hindi rows, displace wrong
attrib-only fills, null orphaned wrong fills, then regenerate quotes.quote_text.
Usage:
  python scripts/hindi_backbone.py            # dry-run report
  python scripts/hindi_backbone.py --apply    # write DB (after backup)
"""
import sqlite3, sys, json, os, re, difflib, shutil, importlib.util
from collections import defaultdict
sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("hal", os.path.join(ROOT, "hindi_db_align.py"))
hal = importlib.util.module_from_spec(spec); spec.loader.exec_module(hal)

HI_DB = os.path.join(ROOT, "..", "assets", "db", "Bhavanasara-Sangraha_Hi.sqlite")
APPLY = "--apply" in sys.argv

def has_deva(s):
    return any('\u0900' <= ch <= '\u097f' for ch in (s or ""))

def ratio(a, b):
    return difflib.SequenceMatcher(None, a, b).ratio()

def chkey(ch):
    m = re.match(r"(\d+)", str(ch))
    return int(m.group(1)) if m else None

con = sqlite3.connect(HI_DB)
cur = con.cursor()
dbrows = hal.load_db()
ocr = hal.load_ocr()

# ---- precompute per-rank window skeletons ----
MAXK = 25
win_skel = {}
for rank in range(8):
    sec = ocr.get(rank)
    if not sec: continue
    vsk = [hal.skeleton(v["text"]) for v in sec["verses"]]
    n = len(vsk)
    ws = {}
    for k in range(1, min(MAXK, n) + 1):
        ws[k] = ["".join(vsk[w:w + k]) for w in range(0, n - k + 1)]
    win_skel[rank] = ws

# ---- Phase 1: content anchors (sim>=0.5 candidates) ----
anchors = {}
for rank in range(8):
    sec = ocr.get(rank)
    if not sec: continue
    ws = win_skel[rank]
    n = len(sec["verses"])
    for r in dbrows.get(hal.PERIODS[rank], []):
        orig = cur.execute("SELECT original_text FROM verses WHERE id=?", (r["id"],)).fetchone()[0] or ""
        if not orig.strip() or not r["v1"]: continue
        v1, v2 = r["v1"], r["v2"] or r["v1"]
        klen = min(v2 - v1 + 1, MAXK)
        dev_sk = hal.skeleton(hal.to_devanagari(orig))
        best = None
        for k in range(max(1, klen - 1), min(klen + 3, MAXK) + 1):
            if k > n: continue
            row = ws[k]
            for w in range(0, len(row)):
                sc = ratio(dev_sk, row[w])
                if best is None or sc > best[0]:
                    best = (sc, w, k)
        if best is None or best[0] < 0.5: continue
        sc, w, k = best
        second = 0.0
        for ww in range(0, len(ws[k])):
            if ww == w: continue
            s2 = ratio(dev_sk, ws[k][ww])
            if s2 > second: second = s2
        uniq = (sc - second) / max(0.01, sc)
        anchors[r["id"]] = (rank, sc, w, k, uniq)

accepted = {}
used_windows = []
for rid in sorted(anchors, key=lambda r: anchors[r][1], reverse=True):
    rank, sc, w, k, uniq = anchors[rid]
    if sc < 0.55 or uniq < 0.15: continue
    if any(rank == ar and not (w + k - 1 < aw or aw + ak - 1 < w) for ar, aw, ak in used_windows):
        continue
    accepted[rid] = (rank, sc, w, k, uniq)
    used_windows.append((rank, w, k))

# ---- Phase 2: interpolation ----
filled = {}
for rank in range(8):
    for r in dbrows.get(hal.PERIODS[rank], []):
        t = cur.execute("SELECT translation_text FROM verses WHERE id=?", (r["id"],)).fetchone()[0]
        filled[r["id"]] = has_deva(t)

used = defaultdict(set)
for rid, (rank, sc, w, k, uniq) in accepted.items():
    for i in range(w, w + k): used[rank].add(i)

interp = {}
for rank in range(8):
    rows = dbrows.get(hal.PERIODS[rank], [])
    sec = ocr.get(rank)
    if not sec: continue
    n_ocr = len(sec["verses"])
    by_book_ch = defaultdict(list)
    for r in rows:
        by_book_ch[(r["slug"], chkey(r["chapter"]))].append(r)
    for (slug, c), lst in by_book_ch.items():
        lst.sort(key=lambda r: (r["v1"] or 0, r["v2"] or 0))
        verse_anchors = []
        for r in lst:
            if r["id"] not in accepted or r["v1"] is None: continue
            _, sc_, w_, k_, _ = accepted[r["id"]]
            v1, v2 = r["v1"], r["v2"] or r["v1"]
            for i, v in enumerate(range(v1, v2 + 1)):
                if w_ + i <= w_ + k_ - 1:
                    verse_anchors.append((v, w_ + i))
        verse_anchors.sort()
        for r in lst:
            if r["id"] in accepted or r["v1"] is None: continue
            v1, v2 = r["v1"], r["v2"] or r["v1"]
            prev_a = [a for a in verse_anchors if a[0] < v1]
            next_a = [a for a in verse_anchors if a[0] > v2]
            if prev_a and next_a:
                a_lo, a_hi = prev_a[-1]; b_lo, b_hi = next_a[0]
                start = a_hi + (v1 - a_lo); end = a_hi + (v2 - a_lo)
                mode = "both"
                gap_verses = b_lo - a_lo - 1; gap_ocr = b_hi - a_hi - 1
                conf = 1.0 - abs(gap_verses - gap_ocr) / max(1, gap_verses)
            elif prev_a:
                start = prev_a[-1][1] + (v1 - prev_a[-1][0]); end = prev_a[-1][1] + (v2 - prev_a[-1][0])
                mode = "prev"; conf = 0.4
            elif next_a:
                start = next_a[0][1] - (next_a[0][0] - v1); end = next_a[0][1] - (next_a[0][0] - v2)
                mode = "next"; conf = 0.4
            else:
                continue
            if start < 0 or end >= n_ocr or end < start or conf < 0.6: continue
            if any(i in used[rank] for i in range(start, end + 1)): continue
            interp[r["id"]] = (rank, start, end, mode, conf)
            for i in range(start, end + 1): used[rank].add(i)

# ---- assembly targets ----
assign = {}   # rid -> (rank, [ocr idxs])
for rid, (rank, sc, w, k, uniq) in accepted.items():
    assign[rid] = (rank, list(range(w, w + k)))
for rid, (rank, s, e, mode, conf) in interp.items():
    assign[rid] = (rank, list(range(s, e + 1)))

# ---- orphaned old fills (need aligner mirror to know old claims) ----
per_row = defaultdict(lambda: {"verses": []})
for rank in range(8):
    rows = dbrows.get(hal.RANK_TO_PERIOD[rank], [])
    sec = ocr.get(rank)
    if not sec: continue
    verses = sec["verses"]
    if rank < 2:
        units = hal.load_units().get(rank, [])
        pairs = hal.align(verses, units, lambda o, r: hal.sim(o["text"], r["dev"]))
        by_ref = defaultdict(list)
        for row in rows: by_ref[(row["slug"], row["chapter"])].append(row)
        def row_for_unit(u):
            cands = by_ref.get((u["slug"], u["chapter"]), [])
            hits = [r for r in cands if r["v1"] is not None and r["v1"] <= u["v2"] and r["v2"] >= u["v1"]]
            if not hits: return None
            hits.sort(key=lambda r: (r["v2"] or 0) - (r["v1"] or 0))
            return hits[0]
        for i, j, sc in pairs:
            r = row_for_unit(units[j])
            if r is not None:
                per_row[r["id"]]["verses"].append((rank, i, sc))
    else:
        refs = []
        for r in rows:
            for v in range(r["v1"] or 1, (r["v2"] or r["v1"] or 1) + 1):
                refs.append({"row": r, "slug": r["slug"], "v": v})
        def scorer(o, r):
            oa = o.get("attrib")
            if not oa or oa["abbr"] != r["slug"]: return 0.0
            ref_ch = hal.chnum(r["row"]["chapter"])
            if ref_ch is None: return 0.9
            r1 = r["row"]["v1"] or 0; r2 = r["row"]["v2"] or r1
            for (c, v) in hal.attrib_candidates(oa["num"]):
                if c == ref_ch and r1 <= v <= r2: return 1.0
            return 0.9
        pairs = hal.align(verses, refs, scorer, gap_m=0.4, gap_s=0.3)
        for i, j, sc in pairs:
            oa = verses[i].get("attrib")
            if oa and oa["abbr"] == refs[j]["slug"]:
                per_row[refs[j]["row"]["id"]]["verses"].append((rank, i, sc))
old_claims = {}
for rid, item in per_row.items():
    idxs = sorted(i for (r, i, sc) in item["verses"])
    if idxs:
        old_claims[rid] = (item["verses"][0][0], set(idxs))

claimed_now = defaultdict(set)
for rank, idxs in assign.values():
    for i in idxs: claimed_now[rank].add(i)

orphans = []
for rid, (orank, oidxs) in old_claims.items():
    if rid in assign: continue
    if not filled.get(rid): continue
    stolen = [i for i in oidxs if i in claimed_now.get(orank, set())]
    if stolen and len(stolen) == len(oidxs):
        orphans.append(rid)

# ---- report ----
new_fills = [rid for rid in assign if not filled.get(rid)]
changed = [rid for rid in assign
           if filled.get(rid) and rid in old_claims and old_claims[rid][0] == assign[rid][0]
           and set(old_claims[rid][1]) != set(assign[rid][1])]
print(f"content anchors: {len(accepted)}   interpolation: {len(interp)}")
print(f"newly filled: {len(new_fills)}   changed: {len(changed)}   orphaned (will null): {len(orphans)}")
remaining = [rid for rank in range(8) for r in dbrows.get(hal.PERIODS[rank], [])
             if not filled.get(r["id"]) and r["id"] not in assign]
print(f"still missing after: {len(remaining)}")

if not APPLY:
    print("\n[dry-run] not writing. Re-run with --apply.")
    sys.exit(0)

# ---- backup ----
bak = HI_DB + ".bak-backbone-before"
if not os.path.exists(bak):
    shutil.copy2(HI_DB, bak)
    print(f"backup -> {bak}")

# ---- write ----
per_rank_trans = {}
for rank in range(8):
    sec = ocr.get(rank)
    if not sec: continue
    assigned = hal.pair_translations(sec)
    per_rank_trans[rank] = assigned

n_written = 0
n_nulled = 0
for rid, (rank, idxs) in assign.items():
    sec = ocr[rank]
    trans = per_rank_trans[rank]
    hi_parts, deva_parts = [], []
    for i in idxs:
        t = trans[i]
        if t is not None:
            hi_parts.append(sec["translations"][t]["text"])
        deva_parts.append(sec["verses"][i]["text"])
    hi_text = " ".join(hi_parts).strip() or None
    deva_text = " ".join(deva_parts).strip() or None
    cur.execute("UPDATE verses SET translation_text=?, original_text_devanagari=? WHERE id=?",
                (hi_text, deva_text, rid))
    n_written += 1
for rid in orphans:
    cur.execute("UPDATE verses SET translation_text=NULL, original_text_devanagari=NULL WHERE id=?", (rid,))
    n_nulled += 1
con.commit()
print(f"written: {n_written}   nulled: {n_nulled}")

# ---- regenerate quotes.quote_text ----
q = """
SELECT q.id FROM quotes q
JOIN citations c ON c.quote_id = q.id
GROUP BY q.id
ORDER BY q.id
"""
def verse_hindi(vid):
    row = cur.execute("SELECT translation_text FROM verses WHERE id=?", (vid,)).fetchone()
    return row[0] if row and row[0] else None

n_updated = 0
quote_verses = defaultdict(list)
for qid, vid in cur.execute("""
    SELECT q.id, c.source_verse_id FROM quotes q
    JOIN citations c ON c.quote_id = q.id
    JOIN quotes q2 ON q2.id = q.id
    ORDER BY q.id, c.rowid"""):
    quote_verses[qid].append(vid)

for qid, vids in quote_verses.items():
    parts = [h for h in (verse_hindi(v) for v in vids) if h]
    if not parts:
        en_bak = HI_DB + ".bak-en-quotes"
        if os.path.exists(en_bak):
            ec = sqlite3.connect(en_bak)
            row = ec.execute("SELECT quote_text FROM quotes WHERE id=?", (qid,)).fetchone()
            ec.close()
            if row and row[0]:
                cur.execute("UPDATE quotes SET quote_text=? WHERE id=?", (row[0], qid))
                n_updated += 1
        continue
    new_text = " ".join(parts).strip()
    cur.execute("SELECT quote_text FROM quotes WHERE id=?", (qid,))
    old = cur.fetchone()[0] or ""
    if new_text and new_text != old:
        cur.execute("UPDATE quotes SET quote_text=? WHERE id=?", (new_text, qid))
        n_updated += 1
con.commit()
print(f"quote_text updated: {n_updated}")

# final counts
hi_rows = cur.execute(
    "SELECT COUNT(*) FROM verses WHERE translation_text IS NOT NULL AND translation_text != ''").fetchone()[0]
hi_quotes = cur.execute(
    "SELECT COUNT(*) FROM quotes WHERE quote_text IS NOT NULL AND quote_text != ''").fetchone()[0]
deva_rows = cur.execute(
    "SELECT COUNT(*) FROM verses WHERE original_text_devanagari IS NOT NULL AND original_text_devanagari != ''").fetchone()[0]
print(f"\nfinal: {hi_rows}/777 verse Hindi, {deva_rows} devanagari, {hi_quotes} quotes Hindi")
con.close()
