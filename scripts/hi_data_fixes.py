# -*- coding: utf-8 -*-
"""Fill the last remaining English strings in the Hindi DB with authored Hindi
translations.

Sources of truth live in scripts/hi_translations.py:

  * VERSE_HI  - verses whose translation_text is still English (110 rows).
  * QUOTE_HI  - quotes whose quote_text is still English (140 rows).

Additionally, 18 verses have an *empty* translation_text; each of those is
linked to exactly one quote (via `citations`), so its translation is filled
from that quote's Hindi translation.

Usage:
  python scripts/hi_data_fixes.py             # dry-run report
  python scripts/hi_data_fixes.py --apply     # write DB (with backup)
"""
import sys, re, sqlite3, os, shutil

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.abspath(__file__))
HI_DB = os.path.join(ROOT, "..", "assets", "db", "Bhavanasara-Sangraha_Hi.sqlite")
APPLY = "--apply" in sys.argv

sys.path.insert(0, ROOT)
import hi_translations as tr

# Empty-translation verses -> the id of the single quote whose text is the
# source for their translation (verified against `citations`).
EMPTY_VERSE_QUOTE = {
    14: 14, 21: 21, 31: 31, 39: 39, 47: 47, 55: 55, 61: 61,
    79: 80, 80: 81, 118: 120, 150: 154, 153: 159, 159: 166,
    161: 168, 173: 180, 233: 243, 626: 649, 683: 707,
}

LATIN = re.compile(r"[A-Za-z]")


def latin_len(t):
    return len(LATIN.findall(t or ""))


def main():
    con = sqlite3.connect(HI_DB)
    con.text_factory = lambda b: b.decode("utf-8", "replace")
    cur = con.cursor()

    verses = list(cur.execute("SELECT id, translation_text FROM verses"))
    quotes = list(cur.execute("SELECT id, quote_text FROM quotes"))

    v_updates = []
    for vid, text in verses:
        t = text or ""
        if LATIN.search(t):
            if vid in tr.VERSE_HI:
                v_updates.append((tr.VERSE_HI[vid], vid))
            else:
                print(f"  ! verse {vid} has latin text but no VERSE_HI entry")
        elif not t.strip():
            qid = EMPTY_VERSE_QUOTE.get(vid)
            if qid is not None and qid in tr.QUOTE_HI:
                v_updates.append((tr.QUOTE_HI[qid], vid))
            elif qid is None:
                print(f"  ! verse {vid} empty translation, no known linked quote")

    q_updates = []
    for qid, text in quotes:
        t = text or ""
        if LATIN.search(t):
            if qid in tr.QUOTE_HI:
                q_updates.append((tr.QUOTE_HI[qid], qid))
            else:
                print(f"  ! quote {qid} has latin text but no QUOTE_HI entry")

    print(f"verse translation updates: {len(v_updates)}")
    print(f"quote text updates:        {len(q_updates)}")

    if not APPLY:
        print("\n[dry-run] not writing DB. Re-run with --apply.")
        return

    bak = HI_DB + ".bak"
    shutil.copyfile(HI_DB, bak)
    cur.executemany("UPDATE verses SET translation_text=? WHERE id=?", v_updates)
    cur.executemany("UPDATE quotes SET quote_text=? WHERE id=?", q_updates)
    con.commit()

    # verify no latin remains
    remaining_v = [i for i, t in cur.execute(
        "SELECT id, translation_text FROM verses") if latin_len(t)]
    remaining_q = [i for i, t in cur.execute(
        "SELECT id, quote_text FROM quotes") if latin_len(t)]
    con.close()
    print(f"\nHi DB updated ({len(v_updates)} verses, {len(q_updates)} quotes).")
    print(f"Backup: {bak}")
    print(f"Remaining latin verses: {len(remaining_v)} {remaining_v}")
    print(f"Remaining latin quotes: {len(remaining_q)} {remaining_q}")


if __name__ == "__main__":
    main()
