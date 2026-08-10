import sys, sqlite3
sys.stdout.reconfigure(encoding="utf-8")

DB = sys.argv[1] if len(sys.argv) > 1 else \
    r"C:\Users\austr\bhavanasara_sangraha\assets\db\Bhavanasara-Sangraha_En.sqlite"

# (verse_id, chapter, verse_start, verse_end, ref_display)
FIXES = [
    (171,  "3",   "84",  "112", "3.84-112"),     # was 3.84-12  (source: covers 3.85-112)
    (93,   "2",   "8",   "11",  "2.8-11"),       # was 2.8-1    (source: covers 2.9-2.11)
    (139,  "4",   "109", "110", "4.109-110"),    # was 4.109-10 (source: covers 4.110)
    (19,   "1",   "10",  "11",  "1.10-11"),      # was 1.10-1   (source: unit 1.11)
    (39,   "1",   "17",  "23",  "1.17-23"),      # was 1.17-21  (source: covers 1.22-1.23)
    (73,   "1",   "217", "222", "1.217-222"),    # was 1.17-222 (source: units 11.217-11.222)
    (436,  "14",  "105", "112", "14.105-112"),   # was 14.105-12 (last verse of ch14; X-12 -> X-112)
    (512,  "16",  "109", "110", "16.109-110"),   # was 16.109-10 (last verse of ch16; X-10 -> X-110)
    (650,  "20",  "57",  "61",  "20.57-61"),     # was 20.57-6  (ch20 feeding episode = 57-61, next 62-76)
    (685,  "22",  "6",   "11",  "22.6-11"),      # was 22.6-1   (X-1 -> X-11)
    (705,  "20",  "95",  "112", "20.95-112"),    # was 20.95-12 (X-12 -> X-112)
    (311,  None,  "8",   "11",  "8-11"),         # was 8-1      (stavavali; X-1 -> X-11, next 12-23)
]

con = sqlite3.connect(DB)
cur = con.cursor()

for vid, ch, vs, ve, ref in FIXES:
    before = cur.execute(
        "SELECT book_id, chapter, verse_start, verse_end, ref_display FROM verses WHERE id=?",
        (vid,)).fetchone()
    cur.execute(
        "UPDATE verses SET chapter=?, verse_start=?, verse_end=?, ref_display=? WHERE id=?",
        (ch, vs, ve, ref, vid))
    after = cur.execute(
        "SELECT book_id, chapter, verse_start, verse_end, ref_display FROM verses WHERE id=?",
        (vid,)).fetchone()
    print(f"v{vid}: {before[1]!r} {before[2]}..{before[3]} {before[4]!r}  ->  "
          f"{after[1]!r} {after[2]}..{after[3]} {after[4]!r}")

# --- also repair citations.ref_display for citations pointing at fixed verses ---
for vid, ch, vs, ve, ref in FIXES:
    old_ref = {
        171: "3.84-12", 93: "2.8-1", 139: "4.109-10", 19: "1.10-1", 39: "1.17-21",
        73: "1.17-222", 436: "14.105-12", 512: "16.109-10", 650: "20.57-6",
        685: "22.6-1", 705: "20.95-12", 311: "8-1",
    }[vid]
    for (cid, cit_ref,) in cur.execute(
            "SELECT id, ref_display FROM citations WHERE source_verse_id=?", (vid,)).fetchall():
        if not cit_ref or not cit_ref.endswith(old_ref):
            print(f"  citation {cid}: ref {cit_ref!r} does not end with {old_ref!r}, left unchanged")
            continue
        new_cit_ref = cit_ref[: -len(old_ref)] + ref
        cur.execute("UPDATE citations SET ref_display=? WHERE id=?", (new_cit_ref, cid))
        print(f"  citation {cid}: {cit_ref!r} -> {new_cit_ref!r}")

con.commit()
print("\ncommitted.")

print("\nany remaining malformed (verse_start > verse_end):",
      cur.execute("SELECT count(*) FROM verses WHERE verse_start IS NOT NULL AND verse_end IS NOT NULL "
                  "AND verse_start > verse_end").fetchone()[0])
print("any remaining duplicate (book,chapter,verse_start):",
      cur.execute("SELECT count(*) FROM (SELECT book_id, chapter, verse_start FROM verses "
                  "GROUP BY book_id, chapter, verse_start HAVING count(*)>1)").fetchone()[0])
