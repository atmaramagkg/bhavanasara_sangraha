# -*- coding: utf-8 -*-
"""
Add Sanskrit original_text to the 17 bhagavatam (Śrīmad-Bhāgavatam) verse rows
that the Bhavanasara compilation does not cover.

Source: scripts/bhagavatam_proposal.json (content-verified IAST, built from
vedabase.io per-verse pages + sanskritdocuments ITX where vedabase pages are
missing, with the recension-numbering offsets resolved by content match).

Writes IAST to the En DB and Cyrillic (Russian Bhaktivedanta convention) to
the Ru DB, matching the format used by add_sanskrit_original_text.py.
Also fixes row 232's wrong ref label (10.13.1 -> 10.13.11).

Run:
    python scripts/add_bhagavatam_sanskrit.py            # dry-run review
    python scripts/add_bhagavatam_sanskrit.py --apply    # write DBs
"""
import sys, re, json, sqlite3, shutil, os, importlib.util

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.abspath(__file__))
EN_DB = os.path.join(ROOT, "..", "assets", "db", "Bhavanasara-Sangraha_En.sqlite")
RU_DB = os.path.join(ROOT, "..", "assets", "db", "Bhavanasara-Sangraha_Ru.sqlite")
PROP = os.path.join(ROOT, "bhagavatam_proposal.json")
APPLY = "--apply" in sys.argv

# reuse iast_to_cyrillic from the main script
spec = importlib.util.spec_from_file_location("add_sk", os.path.join(ROOT, "add_sanskrit_original_text.py"))
add = importlib.util.module_from_spec(spec)
spec.loader.exec_module(add)

FIX_REF = {232: ("10.13.11", "11", None)}   # row -> (ref_display, verse_start, verse_end)

def main():
    prop = json.load(open(PROP, encoding="utf-8"))
    rows = sorted(int(r) for r in prop)
    print(f"proposal covers {len(rows)} rows: {rows}")

    if not APPLY:
        print("dry-run (pass --apply to write)")
    for rid in rows:
        p = prop[str(rid)]
        mode = "WILL-WRITE"
        print(f"  id={rid:<4} ref={p['db_ref']:<11} -> {p['label']:<12} verses={p['verses']} [{mode}]")

    if not APPLY:
        return

    for label, db in (("En", EN_DB), ("Ru", RU_DB)):
        bak = db.replace(".sqlite", f"_before_bhagavatam.sqlite")
        shutil.copy2(db, bak)
        print(f"backed up {label} DB -> {os.path.basename(bak)}")

    for db in (EN_DB, RU_DB):
        con = sqlite3.connect(db)
        cur = con.cursor()
        for rid in rows:
            p = prop[str(rid)]
            text = p["iast"] if db == EN_DB else p["cyrillic"]
            cur.execute("UPDATE verses SET original_text=? WHERE id=?", (text, rid))
        for rid, (ref, vstart, vend) in FIX_REF.items():
            cur.execute("UPDATE verses SET ref_display=?, verse_start=?, verse_end=? WHERE id=?",
                        (ref, vstart, vend, rid))
        con.commit()
        n = cur.rowcount if False else sum(1 for _ in rows)
        print(f"updated {db} ({n} rows)")
        con.close()

    # verify
    for label, db in (("En", EN_DB), ("Ru", RU_DB)):
        con = sqlite3.connect(db)
        total = sum(1 for r in rows if con.execute("SELECT original_text FROM verses WHERE id=?", (r,)).fetchone()[0])
        con.close()
        print(f"  {label}: {total}/{len(rows)} rows now have original_text")

if __name__ == "__main__":
    main()
