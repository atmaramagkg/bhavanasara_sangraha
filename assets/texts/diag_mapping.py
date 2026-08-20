import sqlite3

old_db = sqlite3.connect('C:/Users/austr/bss/assets/db/Bhavanasara-Sangraha_En.sqlite')
old = old_db.cursor()
new_db = sqlite3.connect('C:/Users/austr/bss/assets/db/Bhavanasara-Sangraha.sqlite')
new = new_db.cursor()

print("=== Old DB tables ===")
for r in old.execute("SELECT name FROM sqlite_master WHERE type='table'"):
    print(r[0])

print("\n=== Old verses table schema ===")
for r in old.execute("PRAGMA table_info(verses)"):
    print(r)

print("\n=== Old quotes table schema ===")
for r in old.execute("PRAGMA table_info(quotes)"):
    print(r)

print("\n=== Old citations table schema ===")
for r in old.execute("PRAGMA table_info(citations)"):
    print(r)

print("\n=== Old verses count ===")
r = old.execute("SELECT COUNT(*) FROM verses").fetchone()
print("verses:", r[0])
r = old.execute("SELECT COUNT(*) FROM quotes").fetchone()
print("quotes:", r[0])
r = old.execute("SELECT COUNT(*) FROM citations").fetchone()
print("citations:", r[0])

print("\n=== Old verse samples (with book_id) ===")
for r in old.execute("SELECT id, book_id, book_verse FROM verses LIMIT 10"):
    print(r)

print("\n=== Old citation samples ===")
for r in old.execute("SELECT quote_id, verse_id FROM citations LIMIT 10"):
    print(r)

print("\n=== Old quote samples ===")
for r in old.execute("SELECT id, ref_display FROM quotes LIMIT 10"):
    print(r)

print("\n=== ID overlap check ===")
old_quote_ids = set(r[0] for r in old.execute("SELECT id FROM quotes"))
new_verse_ids = set(r[0] for r in new.execute("SELECT id FROM verses"))
overlap = old_quote_ids & new_verse_ids
print(f"Old quotes: {len(old_quote_ids)}, New verses: {len(new_verse_ids)}, Overlap: {len(overlap)}")

print("\n=== Max IDs ===")
print("Old quote max:", max(old_quote_ids))
print("New verse max:", max(new_verse_ids))

old_db.close()
new_db.close()
