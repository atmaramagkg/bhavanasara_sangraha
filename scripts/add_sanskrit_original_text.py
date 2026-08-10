# -*- coding: utf-8 -*-
"""
Add Sanskrit original_text (IAST) to the En DB and its Cyrillic transliteration
to the Ru DB for every verse row the Bhavanasara compilation covers.

Source of truth: scripts/all_recs_full.json (594 verse units parsed from
"Bhavana sara sangraha Eng.txt": IAST Sanskrit + full translation + refs).

Mapping unit -> DB row: semantic best-match (primary) corroborated/overridden
by reference-based matching (with the known numbering offsets).

Run:
    python scripts/add_sanskrit_original_text.py            # dry-run review
    python scripts/add_sanskrit_original_text.py --apply    # write DBs
"""
import sys, re, json, sqlite3, unicodedata, os
from collections import defaultdict, Counter

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.abspath(__file__))
EN_DB = os.path.join(ROOT, "..", "assets", "db", "Bhavanasara-Sangraha_En.sqlite")
RU_DB = os.path.join(ROOT, "..", "assets", "db", "Bhavanasara-Sangraha_Ru.sqlite")
RECS = os.path.join(ROOT, "all_recs_full.json")
APPLY = "--apply" in sys.argv

# --------------------------------------------------------------------------
# IAST -> Cyrillic (Russian Indological / Bhaktivedanta-RU convention).
# Long vowels use combining macron (U+0304), retroflex/anusvara/visarga use
# combining dot below (U+0323) -- matches the example
#   "nānutṛpye juṣan yuṣmad" -> "на̄нутр̣пйе джушан йушмад"
# --------------------------------------------------------------------------
MACRON = "\u0304"
DOTBELOW = "\u0323"
DOTABOVE = "\u0307"
TILDE = "\u0303"

_CYR = {
    "a": "а", "ā": "а" + MACRON,
    "i": "и", "ī": "и" + MACRON,
    "u": "у", "ū": "у" + MACRON,
    "ṛ": "р" + DOTBELOW, "ṝ": "р" + DOTBELOW + MACRON,
    "ḷ": "л" + DOTBELOW, "ḹ": "л" + DOTBELOW + MACRON,
    "e": "е", "o": "о",
    "k": "к", "kh": "кх", "g": "г", "gh": "гх", "ṅ": "н" + DOTABOVE,
    "c": "ч", "ch": "чх", "j": "дж", "jh": "джх", "ñ": "н" + TILDE,
    "ṭ": "т" + DOTBELOW, "ṭh": "т" + DOTBELOW + "х",
    "ḍ": "д" + DOTBELOW, "ḍh": "д" + DOTBELOW + "х",
    "ṇ": "н" + DOTBELOW,
    "t": "т", "th": "тх", "d": "д", "dh": "дх", "n": "н",
    "p": "п", "ph": "пх", "b": "б", "bh": "бх", "m": "м",
    "y": "й", "r": "р", "l": "л", "v": "в",
    "ś": "ш", "ṣ": "ш", "s": "с", "h": "х",
    "ai": "аи", "au": "ау",
    "ṃ": "м" + DOTBELOW, "ḥ": "х" + DOTBELOW,
}

_CYR_RE = re.compile("|".join(sorted(_CYR, key=len, reverse=True)))

# Manual overrides for conflicts where the reference-based row is wrong and the
# semantic row matches the unit's content verbatim (verified by eye):
#   campu 1.2 -> row 485 (1.1-2 kuṅkuma-stained feet) not 610 (1.2 Vrajavāsīs)
#   campu 1.111,113 / 1.114 -> row 151 / 152 (Nandīśvara trees/lakes) not 339
#   alankara 5.71 -> row 81 (5.20 family honor) not 739 (5.71 torn clothes)
OVERRIDES = {
    ("ananda-vrndavana-campu", "3"): 485,
    ("ananda-vrndavana-campu", "272-273"): 151,
    ("ananda-vrndavana-campu", "274"): 152,
    ("alankara-kaustubha", "60"): 81,
}


def iast_to_cyrillic(text: str) -> str:
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    text = text.replace("'", "")
    text = text.replace("¬", "ṛ")
    out = []
    for ln in text.split("\n"):
        ln = _CYR_RE.sub(lambda m: _CYR[m.group(0)], ln)
        out.append(ln)
    return "\n".join(out)


# --------------------------------------------------------------------------
# Sanskrit cleaning: drop annotation lines (uppercase or f/w/q/x letters),
# strip footnotes (digits), fix OCR '¬' -> 'ṛ', tidy hyphens.
# --------------------------------------------------------------------------
def clean_sanskrit(s: str) -> str:
    out = []
    for raw in s.split("\n"):
        ln = raw.replace("¬", "ṛ")
        ln = re.sub(r"\d+", "", ln)
        ln = ln.strip()
        if not ln:
            continue
        if re.search(r"[A-ZŚḶ]", ln):
            continue
        if re.search(r"[fFwWqQxX]", ln):
            continue
        out.append(ln)
    text = "\n".join(out)
    text = re.sub(r" *- *\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def num(x):
    try:
        return int(x)
    except (TypeError, ValueError):
        return None


def norm(s):
    s = unicodedata.normalize("NFKD", s or "")
    s = s.replace(MACRON, "").replace(DOTBELOW, "").replace(DOTABOVE, "").replace(TILDE, "")
    s = re.sub(r"[^a-z0-9 ]", " ", s.lower())
    return set(re.sub(r"\s+", " ", s).split())


def dice(a, b):
    if not a or not b:
        return 0.0
    return 2.0 * len(a & b) / (len(a) + len(b))


def main():
    recs = json.load(open(RECS, encoding="utf-8"))
    con = sqlite3.connect(EN_DB)
    slug_of = {r[0]: r[1] for r in con.execute("SELECT id, slug FROM books")}

    dbrows = []
    for rid, bid, ch, vs, ve, rd in con.execute(
            "SELECT id, book_id, chapter, verse_start, verse_end, ref_display FROM verses"):
        a, b = num(vs), num(ve)
        if b is None:
            b = a
        if a is not None and b is not None and a > b:
            a, b = b, a
        dbrows.append({"id": rid, "slug": slug_of.get(bid), "chapter": ch, "v1": a, "v2": b, "ref": rd})
    by_slug = defaultdict(list)
    for d in dbrows:
        by_slug[d["slug"]].append(d)

    text_of = {}
    for rid, txt in con.execute("SELECT id, translation_text FROM verses"):
        text_of[rid] = txt or ""
    for d in dbrows:
        d["toks"] = norm(text_of[d["id"]])
    con.close()

    def db_chapter(slug, src_ch, ref):
        """compilation chapter -> DB chapter (applies known numbering offsets)."""
        if src_ch is None:
            rl = (ref or "").lower()
            if slug == "ujjvala-nilamani":
                if "uddīpana" in rl:
                    return "10"
                if "sthāyībhāva" in rl:
                    return "14"
            return src_ch
        try:
            n = int(src_ch)
        except ValueError:
            return src_ch
        if slug == "ananda-vrndavana-campu":
            return str(n - 10) if n >= 10 else src_ch
        if slug == "vraja-riti-cintamani":
            return str(n - 1)
        return src_ch

    def ref_match(unit):
        slug = unit["slug"]
        dbch = db_chapter(slug, unit["chapter"], unit.get("ref"))
        v1, v2 = unit["v1"], unit["v2"] or unit["v1"]
        if v1 is None or dbch is None:
            return []
        best = []
        for d in by_slug.get(slug, []):
            if d["chapter"] != dbch or d["v1"] is None:
                continue
            if d["v1"] <= v2 and d["v2"] >= v1:
                best.append(d)
        if not best:
            return []
        best.sort(key=lambda d: (d["v2"] or 0) - (d["v1"] or 0))
        return best[:1]

    def sem_match(unit):
        toks = norm(unit.get("translation"))
        if not toks:
            return None, 0.0
        bs, bid = 0.0, None
        for d in by_slug.get(unit["slug"], []):
            s = dice(toks, d["toks"])
            if s > bs:
                bs, bid = s, d
        return bid, bs

    def chapters_agree(src_ch, row_ch):
        """For ref-less (sem-only) matches, reject cross-chapter guesses."""
        a, b = num(src_ch), num(row_ch)
        if a is None or b is None:
            return str(src_ch) == str(row_ch)
        return a == b

    assignments = []   # dicts: unit info + chosen row + confidence
    unassigned = []
    for unit in recs:
        if not (unit.get("slug") and unit.get("v1")):
            continue
        s = clean_sanskrit(unit.get("sanskrit", ""))
        if not s:
            continue
        r = ref_match(unit)
        b, score = sem_match(unit)
        rec = {"unit": unit["unit"], "slug": unit["slug"], "ref": unit.get("ref"),
               "ch": unit.get("chapter"), "v1": unit.get("v1"), "v2": unit.get("v2"),
               "sanskrit": s, "ref_row": r[0]["id"] if r else None, "sem_row": b["id"] if b else None,
               "score": score}
        forced = OVERRIDES.get((unit["slug"], unit["unit"]))
        if forced is not None:
            rec["row"], rec["conf"] = forced, "override"
            assignments.append(rec)
        elif r and b and r[0]["id"] == b["id"]:
            rec["row"], rec["conf"] = r[0]["id"], "ref+sem"
            assignments.append(rec)
        elif r:
            rec["row"], rec["conf"] = r[0]["id"], "ref"
            assignments.append(rec)
        elif b and score >= 0.30 and chapters_agree(unit["chapter"], b["chapter"]):
            rec["row"], rec["conf"] = b["id"], "sem"
            assignments.append(rec)
        else:
            rec["conf"] = "none"
            unassigned.append(rec)

    # group units per row, in verse order
    row_units = defaultdict(list)
    for a in assignments:
        row_units[a["row"]].append(a)
    for rid in row_units:
        row_units[rid].sort(key=lambda a: (str(a["ch"] or ""), a["v1"] or 0, a["v2"] or 0, a["unit"]))

    # Cyrillic conversion of the assembled Sanskrit (per row, in verse order)
    ru_text = {}
    for rid, units in row_units.items():
        ru_text[rid] = iast_to_cyrillic("\n\n".join(u["sanskrit"] for u in units))

    # ----------------------------------------------------------------------
    # Dry-run report
    # ----------------------------------------------------------------------
    print(f"total units: {len(recs)}")
    print(f"assigned to a DB row: {len(assignments)}   unassigned: {len(unassigned)}")
    print(f"DB rows receiving original_text: {len(row_units)}")
    bybook = defaultdict(lambda: [0, 0])
    for d in dbrows:
        bybook[d["slug"]][1] += 1
    for rid in row_units:
        for d in dbrows:
            if d["id"] == rid:
                bybook[d["slug"]][0] += 1
    print("\nper-book rows with Sanskrit:")
    for slug in sorted(bybook):
        got, tot = bybook[slug]
        if got:
            print(f"  {slug:<30} {got}/{tot}")
    print("\nconf distribution:")
    print("  ", dict(Counter(a["conf"] for a in assignments)))

    print("\nUNASSIGNED units (no Sanskrit placed):")
    for a in sorted(unassigned, key=lambda x: x["slug"]):
        print(f"  {a['slug']:<26} unit {a['unit']:<6} ref {a['ref']}")

    print("\nSEM-only assignments with score < 0.40 (review):")
    for a in sorted(assignments, key=lambda x: x["score"]):
        if a["conf"] == "sem" and a["score"] < 0.40:
            print(f"  {a['score']:.2f} {a['slug']:<24} unit {a['unit']:<6} -> row {a['row']}  ref={a['ref']}")

    print("\nconflict ref vs sem (used ref):")
    for a in assignments:
        if a["conf"] == "ref" and a["sem_row"] and a["sem_row"] != a["row"] and a["score"] >= 0.30:
            print(f"  unit {a['unit']} {a['slug']} ref={a['ref']} refrow={a['row']} semrow={a['sem_row']} score={a['score']:.2f}")

    # ----------------------------------------------------------------------
    # Apply
    # ----------------------------------------------------------------------
    if not APPLY:
        print("\n[dry-run] not writing. Re-run with --apply to write DBs.")
        return

    con = sqlite3.connect(EN_DB)
    cur = con.cursor()
    n = 0
    for rid, units in row_units.items():
        joined = "\n\n".join(u["sanskrit"] for u in units)
        cur.execute("UPDATE verses SET original_text=? WHERE id=?", (joined, rid))
        n += cur.rowcount
    con.commit()
    con.close()

    con = sqlite3.connect(RU_DB)
    cur = con.cursor()
    # id alignment: same ids share metadata for 773 rows
    en_ok = set(row_units.keys())
    ru_have = set(r[0] for r in cur.execute("SELECT id FROM verses"))
    shared = en_ok & ru_have
    m = 0
    for rid in shared:
        cur.execute("UPDATE verses SET original_text=? WHERE id=?", (ru_text[rid], rid))
        m += cur.rowcount
    con.commit()
    con.close()

    print(f"\nEn DB updated: {n} rows   Ru DB updated: {m} rows")
    print(f"En-only rows with Sanskrit not in Ru (no matching row): {sorted(en_ok - ru_have)}")


if __name__ == "__main__":
    main()
