import sqlite3

db = sqlite3.connect('C:/Users/austr/bss/assets/db/Bhavanasara-Sangraha.sqlite')
c = db.cursor()

print('=== ref_display samples ===')
for r in c.execute('SELECT id, ref_display, book_id, substr(sanskrit_text,1,30), translation_en != "" as has_en, translation_ru != "" as has_ru, translation_hi != "" as has_hi FROM verses LIMIT 15'):
    print(r)

print()
print('=== books table ===')
for r in c.execute('SELECT id, slug, title_key, author_key FROM books'):
    print(r)

print()
print('=== books with verse counts ===')
for r in c.execute('SELECT b.id, b.slug, b.title_key, COUNT(v.id) as cnt FROM books b LEFT JOIN verses v ON v.book_id = b.id GROUP BY b.id ORDER BY cnt DESC'):
    print(r)

print()
print('=== book translations ===')
rows = c.execute("SELECT translation_key, en, ru, hi FROM translations WHERE translation_key LIKE 'book_%' OR translation_key LIKE 'bss_%'").fetchall()
for r in rows[:20]:
    print(r[0], '|', r[1][:50] if r[1] else '', '|', r[2][:50] if r[2] else '', '|', r[3][:50] if r[3] else '')

print()
print('=== NULL book_id count ===')
r = c.execute('SELECT COUNT(*) FROM verses WHERE book_id IS NULL').fetchone()
print('NULL book_id:', r[0])

print()
print('=== empty translation_en count ===')
r = c.execute('SELECT COUNT(*) FROM verses WHERE translation_en = "" OR translation_en IS NULL').fetchone()
print('empty en:', r[0])

print()
print('=== refs without book name ===')
for r in c.execute('SELECT DISTINCT ref_display FROM verses WHERE ref_display NOT LIKE "% %" LIMIT 20'):
    print(r)

print()
print('=== distinct ref_display patterns (first 30) ===')
for r in c.execute('SELECT DISTINCT ref_display FROM verses ORDER BY ref_display LIMIT 30'):
    print(r)

print()
print('=== section verse counts ===')
for r in c.execute('SELECT section_id, COUNT(*) FROM verses GROUP BY section_id ORDER BY section_id'):
    print(r)

db.close()
