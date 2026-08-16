# -*- coding: utf-8 -*-
"""Rebuild the Hindi reading-pane content from the full parsed BSS.txt.

Reads `bss_hindi_structured.json` (produced by parse_bss_hindi.py), rebuilds
the `sections` + `quotes` tables of the Hindi app database from the complete
Hindi text, and drops the old citation links (the "keep navigation, drop
verse links" decision). All scaffolding -- period_nodes, books, verses,
period translations, app_settings, languages, dandas -- is kept intact.

New sections are mapped onto the existing sub periods positionally: the k-th
new section of a main period gets the sub period of the old section sitting at
the same fraction of that main period, so the time-of-day sub-period bar and
the reading order keep working. The book's upasanghara (उपसंहार) is added as a
9th main period with a single sub period so its text stays readable; the
empty biographies region is skipped.

Dry run by default (prints the full plan). Pass --apply to write
`assets/db/Bhavanasara-Sangraha_Hi.sqlite` (a timestamped backup is made
first).
"""
import argparse
import json
import os
import re
import shutil
import sqlite3
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
STRUCTURED = os.path.join(ROOT, "bss_hindi_structured.json")
DB_PATH = os.path.join(ROOT, "assets", "db", "Bhavanasara-Sangraha_Hi.sqlite")
REPORT = os.path.join(ROOT, "bss_hindi_rebuild_report.json")

# structured-JSON region code -> DB main period code
REGION_TO_MAIN = {
    "nishanta": "nishanta",
    "pratah": "pratah",
    "purvahna": "purvahna",
    "madhyahna": "madhyahna",
    "aparahna": "aparahna",
    "sayahna": "sayahna",
    "pradosha": "pradosha",
    "nakta": "nisha",
    "upasanghara": "upasanghara",
    # "biographies" has 0 items in the current parse -- skipped.
}

HI_LANG_CODE = "hi"


def clean_quote_text(num, text):
    """Collapse whitespace and drop the leading '(n)' translation number."""
    t = re.sub(r"\s+", " ", text or "").strip()
    if num:
        m = re.match(r"^[\(\{\[\s]*" + re.escape(num) + r"[\)\}\]]?[\s]*", t)
        if m and len(m.group(0)) <= len(num) + 3:
            t = t[m.end():].strip(" -–—:")
    else:
        m = re.match(r"^[\(\{\[]\s*[&£©‰=:,\-–—.~]+\s*[\)\}\]]\s*", t)
        if m:
            t = t[m.end():].strip()
    return t


def group_items(region):
    """Group the region's items into sections by propagated heading.

    Items before the first heading (heading is None) form the leading
    "intro" section, titled after the region. Returns a list of
    {"title": str, "items": [item, ...]}.
    """
    headings = region.get("headings", [])
    groups = []
    for it in region.get("items", []):
        h = it.get("heading")
        title = headings[h] if h is not None else None
        if not groups or groups[-1]["title"] != title:
            groups.append({"title": title, "items": []})
        groups[-1]["items"].append(it)
    for g in groups:
        if g["title"] is None:
            g["title"] = region["name"]
    return groups


def positional_subs(new_count, old_sub_seq):
    """Distribute new_count sections across the sub periods contiguously.

    Section i (of new_count) is assigned to sub number `i * k // new_count`,
    i.e. each sub period gets a contiguous run of sections sized as evenly as
    possible. This keeps the narrative reading order intact, makes every sub
    period (that can be filled) show content, and stays reasonably aligned
    with the sub periods' time ranges.
    """
    if new_count <= 0:
        return []
    k = len(old_sub_seq)
    if k == 0:
        return [None] * new_count
    return [min(i * k // new_count, k - 1) for i in range(new_count)]


def load_scaffolding(db_path):
    """Read everything we need from the existing Hindi DB (read-only)."""
    db = sqlite3.connect(db_path)
    try:
        cur = db.cursor()

        lang_ids = {}
        for r in cur.execute("SELECT id, code FROM languages"):
            lang_ids[r[1]] = r[0]

        # code -> (id, period_type, sort_order, name_key)
        nodes = {}
        for r in cur.execute(
            "SELECT id, parent_id, code, period_type, sort_order, name_key "
            "FROM period_nodes ORDER BY sort_order, id"
        ):
            nodes[r[2]] = {
                "id": r[0], "parent_id": r[1], "code": r[2],
                "period_type": r[3], "sort_order": r[4], "name_key": r[5],
            }

        # main code -> ordered list of sub period ids (by sort order)
        sub_ids = {}
        for r in cur.execute(
            "SELECT pm.code, ps.id AS sub_id "
            "FROM period_nodes ps "
            "JOIN period_nodes pm ON pm.id = ps.parent_id "
            "WHERE ps.period_type = 'sub' "
            "ORDER BY pm.sort_order, ps.sort_order"
        ):
            sub_ids.setdefault(r[0], []).append(r[1])

        # per-main old counts for the report
        old_counts = {}
        for r in cur.execute(
            "SELECT pm.code, COUNT(DISTINCT sec.id), COUNT(DISTINCT q.id) "
            "FROM period_nodes pm "
            "LEFT JOIN period_nodes ps ON ps.parent_id = pm.id AND ps.period_type='sub' "
            "LEFT JOIN sections sec ON sec.period_node_id = ps.id "
            "LEFT JOIN quotes q ON q.section_id = sec.id "
            "WHERE pm.period_type='main' "
            "GROUP BY pm.code ORDER BY pm.sort_order"
        ):
            old_counts[r[0]] = {"sections": r[1], "quotes": r[2]}

        return {
            "lang_ids": lang_ids,
            "nodes": nodes,
            "sub_ids": sub_ids,
            "old_counts": old_counts,
        }
    finally:
        db.close()


def build_plan(doc, scaffold):
    """Return ordered plan entries and per-main new counts."""
    nodes = scaffold["nodes"]
    sub_ids = scaffold["sub_ids"]

    plan = []          # one dict per section, in reading order
    for region in doc["sections"]:
        code = region["code"]
        main_code = REGION_TO_MAIN.get(code)
        if main_code is None or not region.get("items"):
            continue

        groups = group_items(region)
        main_subs = sub_ids.get(main_code, [])

        if main_subs:
            subs = positional_subs(len(groups), main_subs)
        else:
            subs = [None] * len(groups)   # upasanghara: sub created later

        for g, sub_idx in zip(groups, subs):
            plan.append({
                "main_code": main_code,
                "sub_id": main_subs[sub_idx] if sub_idx is not None else None,
                "title": g["title"],
                "items": g["items"],
            })
    return plan


def write_db(plan, scaffold, db_path):
    """Rebuild sections/quotes/citations in db_path (already backed up)."""
    nodes = scaffold["nodes"]
    lang_ids = scaffold["lang_ids"]
    hi_id = lang_ids.get(HI_LANG_CODE, 2)

    db = sqlite3.connect(db_path)
    try:
        cur = db.cursor()
        cur.execute("BEGIN")

        # 1) clear the old content tables (FK-safe order)
        cur.execute("DELETE FROM citations")
        cur.execute("DELETE FROM quotes")
        cur.execute("DELETE FROM sections")
        cur.execute("DELETE FROM translations WHERE translation_key LIKE 'section.%'")

        # 2) create the upasanghara main period + sub period if missing
        upa_sub_id = None
        if "upasanghara" not in nodes:
            cur.execute(
                "INSERT INTO period_nodes "
                "(parent_id, code, period_type, time_start, time_end, sort_order, name_key) "
                "VALUES (NULL, 'upasanghara', 'main', '', '', 9, 'period.upasanghara.name')"
            )
            upa_main_id = cur.lastrowid
            cur.execute(
                "INSERT INTO period_nodes "
                "(parent_id, code, period_type, time_start, time_end, sort_order, name_key) "
                "VALUES (?, 'upasanghara_1', 'sub', '', '', 1, "
                "'period_node.upasanghara_1.name')",
                (upa_main_id,),
            )
            upa_sub_id = cur.lastrowid
            nodes["upasanghara"] = {
                "id": upa_main_id, "period_type": "main",
                "sort_order": 9, "name_key": "period.upasanghara.name",
            }
            nodes["upasanghara_1"] = {
                "id": upa_sub_id, "parent_id": upa_main_id, "period_type": "sub",
                "sort_order": 1, "name_key": "period_node.upasanghara_1.name",
            }
            for key, text in (
                ("period.upasanghara.name", "उपसंहार"),
                ("period_node.upasanghara_1.name", "उपसंहार"),
            ):
                cur.execute(
                    "INSERT OR IGNORE INTO translations (language_id, translation_key, translated_text) "
                    "VALUES (?, ?, ?)", (hi_id, key, text))

        # 3) insert sections + quotes in reading order
        new_counts = {}
        for entry in plan:
            main_code = entry["main_code"]
            sub_id = entry["sub_id"]
            if sub_id is None:
                sub_id = upa_sub_id
            sub_code = next(
                (k for k, v in nodes.items() if v["id"] == sub_id and v["period_type"] == "sub"),
                None,
            )

            # sort_order within the sub period
            key = (main_code, sub_id)
            counter = new_counts.setdefault(key, {"sections": 0, "quotes": 0})
            counter["sections"] += 1
            sort_in_sub = counter["sections"]

            title_key = f"section.{sub_code}.{sort_in_sub}.title"
            cur.execute(
                "INSERT INTO sections (period_node_id, sort_order, title_key, hindi_heading) "
                "VALUES (?, ?, ?, '')", (sub_id, sort_in_sub, title_key)
            )
            section_id = cur.lastrowid
            cur.execute(
                "INSERT OR REPLACE INTO translations (language_id, translation_key, translated_text) "
                "VALUES (?, ?, ?)", (hi_id, title_key, entry["title"])
            )

            for i, item in enumerate(entry["items"], start=1):
                text = clean_quote_text(item.get("num"), item.get("hindi"))
                cur.execute(
                    "INSERT INTO quotes (section_id, quote_type, quote_text, sort_order) "
                    "VALUES (?, 'quote', ?, ?)", (section_id, text, i)
                )
                counter["quotes"] += 1

        # 4) collapse per-main totals for the report
        main_totals = {}
        for (main_code, _sub_id), c in new_counts.items():
            t = main_totals.setdefault(main_code, {"sections": 0, "quotes": 0})
            t["sections"] += c["sections"]
            t["quotes"] += c["quotes"]

        db.commit()
        return main_totals
    finally:
        db.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true",
                    help="write the rebuilt database (default: dry-run plan only)")
    args = ap.parse_args()

    doc = json.load(open(STRUCTURED, encoding="utf-8"))
    scaffold = load_scaffolding(DB_PATH)
    plan = build_plan(doc, scaffold)

    total_quotes = sum(len(e["items"]) for e in plan)
    total_sections = len(plan)

    print(f"Structured source: {STRUCTURED}")
    print(f"Target DB:         {DB_PATH}  ({'DRY RUN' if not args.apply else 'APPLY'})")
    print()

    # report: per main period
    new_main = {}
    for e in plan:
        new_main.setdefault(e["main_code"], 0)
        new_main[e["main_code"]] += 1
    print(f"{'main':12s} {'old_sec':>7s} {'new_sec':>7s} {'old_q':>6s} {'new_q':>6s}")
    mains = [k for k in new_main if k in scaffold["old_counts"]] + \
            [k for k in new_main if k not in scaffold["old_counts"]]
    for code in mains:
        old = scaffold["old_counts"].get(code, {"sections": 0, "quotes": 0})
        new_q = sum(len(e["items"]) for e in plan if e["main_code"] == code)
        print(f"{code:12s} {old['sections']:7d} {new_main[code]:7d} "
              f"{old['quotes']:6d} {new_q:6d}")
    old_all_sec = sum(v["sections"] for v in scaffold["old_counts"].values())
    old_all_q = sum(v["quotes"] for v in scaffold["old_counts"].values())
    print(f"{'TOTAL':12s} {old_all_sec:7d} {total_sections:7d} {old_all_q:6d} {total_quotes:6d}")

    # section-by-section plan
    print()
    for e in plan:
        preview = clean_quote_text(e["items"][0].get("num"), e["items"][0].get("hindi"))
        print(f"  [{e['main_code']}] {e['title']} "
              f"({len(e['items'])} quotes)")
        print(f"        e.g. {preview[:90]}")

    report_data = {
        "source": STRUCTURED,
        "per_main": [
            {
                "main": code,
                "old_sections": scaffold["old_counts"].get(code, {}).get("sections", 0),
                "new_sections": new_main[code],
                "old_quotes": scaffold["old_counts"].get(code, {}).get("quotes", 0),
                "new_quotes": sum(len(e["items"]) for e in plan if e["main_code"] == code),
            }
            for code in mains
        ],
        "totals": {"sections": total_sections, "quotes": total_quotes},
    }
    with open(REPORT, "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    print(f"\nReport written to {REPORT}")

    if not args.apply:
        print("\nDry run only. Re-run with --apply to write the database.")
        return

    backup = DB_PATH + ".bak-" + datetime.now().strftime("%Y%m%d-%H%M%S")
    shutil.copy2(DB_PATH, backup)
    print(f"\nBackup written to {backup}")

    main_totals = write_db(plan, scaffold, DB_PATH)
    print("Database rebuilt.")
    for code, t in main_totals.items():
        print(f"  {code}: {t['sections']} sections, {t['quotes']} quotes")


if __name__ == "__main__":
    main()
