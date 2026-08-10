import sys, sqlite3
sys.stdout.reconfigure(encoding="utf-8")

DB = r"C:\Users\austr\bhavanasara_sangraha\assets\db\Bhavanasara-Sangraha_En.sqlite"
con = sqlite3.connect(DB)
cur = con.cursor()

BOOKS = {
    "caitanya-candramrta": "SELECT id FROM books WHERE slug=?",
    "bhakti-rasamrta-sindhu": "SELECT id FROM books WHERE slug=?",
    "krsna-bhavanamrta": "SELECT id FROM books WHERE slug=?",
}

def book_id(slug):
    return cur.execute("SELECT id FROM books WHERE slug=?", (slug,)).fetchone()[0]

NEW_VERSES = [
    (book_id("caitanya-candramrta"), None, "13", None, "13",
     "Śrī Gauracandra has strong shoulders like a lion, and His beautiful cheeks are decorated by a sweet smile. His transcendental body undergoes many astonishing r a s a m a y a transformations. His complexion is more beautiful than a blooming golden lotus, and His body is the meeting place of Rādhā and Mādhava. May that Lord Gaura be pleased with us."),
    (book_id("bhakti-rasamrta-sindhu"), "1.1", "4", None, "1.1.4",
     "I offer my humble obeisance unto the devotees of Śrī Gauracandra, who are like dolphins sporting in the ocean of bhakti-rasa. They have conquered their fear of the snare of death and care nothing for the river of mukti."),
    (book_id("krsna-bhavanamrta"), "1", "26", None, "1.26",
     "After first making certain that Rādhā and Kṛṣṇa were awake, Śrīmatī's kiṅkarīs without hesitation unfastened the door and with quiet, gentle steps entered the cottage."),
    (book_id("krsna-bhavanamrta"), "5", "28", None, "5.28",
     "O Rādhā! You have come a long way from Yāvaṭa and are almost at Nanda's palace. Have faith that the cherished desire of Your cātaka bird eyes will soon be realized."),
]

inserted = []
for bid, ch, vs, ve, ref, txt in NEW_VERSES:
    exists = cur.execute(
        "SELECT id FROM verses WHERE book_id=? AND ref_display=?", (bid, ref)).fetchone()
    if exists:
        print(f"SKIP (already present): book={bid} ref={ref} id={exists[0]}")
        inserted.append(exists[0])
        continue
    cur.execute(
        "INSERT INTO verses (book_id, chapter, verse_start, verse_end, ref_display, translation_text, sort_order) "
        "VALUES (?,?,?,?,?,?,0)",
        (bid, ch, vs, ve, ref, txt))
    inserted.append(cur.lastrowid)
    print(f"INSERTED verse id={cur.lastrowid} book={bid} ref={ref}")

v528 = cur.execute(
    "SELECT id FROM verses WHERE book_id=? AND ref_display='5.28'",
    (book_id("krsna-bhavanamrta"),)).fetchone()[0]

q160_text = cur.execute("SELECT quote_text FROM quotes WHERE id=160").fetchone()[0]
new_text = cur.execute("SELECT translation_text FROM verses WHERE id=?", (v528,)).fetchone()[0]
if q160_text.strip() != new_text.strip():
    print("WARNING: q160 text differs from new 5.28 verse text")
else:
    print("OK: new 5.28 verse text matches quote q160")

cit = cur.execute("SELECT source_verse_id, ref_display FROM citations WHERE id=156").fetchone()
print(f"citation 156 before: verse={cit[0]} ref={cit[1]!r}")
cur.execute("UPDATE citations SET source_verse_id=?, ref_display=? WHERE id=156",
            (v528, "Kṛṣṇa-bhāvanāmṛta 5.28"))
print(f"citation 156 after: verse={v528} ref='Kṛṣṇa-bhāvanāmṛta 5.28'")

con.commit()
print("\ncommitted.")
print("total verses now:", cur.execute("SELECT count(*) FROM verses").fetchone()[0])
