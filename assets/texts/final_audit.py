import sqlite3
db = r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha.sqlite'
conn = sqlite3.connect(db)
c = conn.cursor()

print("=== FINAL DATABASE AUDIT ===\n")

c.execute("SELECT COUNT(*) FROM verses")
total = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM verses WHERE transliteration IS NOT NULL AND transliteration != ''")
translit = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM verses WHERE sanskrit_text IS NOT NULL AND sanskrit_text != ''")
sanskrit = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM verses WHERE translation_hi IS NOT NULL AND translation_hi != ''")
hi_v = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM verses WHERE translation_en IS NOT NULL AND translation_en != ''")
en_v = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM verses WHERE translation_ru IS NOT NULL AND translation_ru != ''")
ru_v = c.fetchone()[0]
print(f"Verses: {total}")
print(f"  Transliteration: {translit} ({100*translit//total}%)")
print(f"  Sanskrit (Devanagari): {sanskrit} ({100*sanskrit//total}%)")
print(f"  Hindi: {hi_v} ({100*hi_v//total}%)")
print(f"  English: {en_v} ({100*en_v//total}%)")
print(f"  Russian: {ru_v} ({100*ru_v//total}%)")

print("\n--- Per-section verse counts ---")
c.execute("""SELECT section_id, COUNT(*) as total,
    SUM(CASE WHEN transliteration IS NOT NULL AND transliteration != '' THEN 1 ELSE 0 END) as has_translit,
    SUM(CASE WHEN sanskrit_text IS NOT NULL AND sanskrit_text != '' THEN 1 ELSE 0 END) as has_sanskrit,
    SUM(CASE WHEN translation_hi IS NOT NULL AND translation_hi != '' THEN 1 ELSE 0 END) as has_hi,
    SUM(CASE WHEN translation_en IS NOT NULL AND translation_en != '' THEN 1 ELSE 0 END) as has_en,
    SUM(CASE WHEN translation_ru IS NOT NULL AND translation_ru != '' THEN 1 ELSE 0 END) as has_ru
    FROM verses GROUP BY section_id ORDER BY section_id""")
for row in c.fetchall():
    print(f"  Sec{row[0]}: {row[1]}v | tr={row[2]} sk={row[3]} hi={row[4]} en={row[5]} ru={row[6]}")

print("\n--- Translations table ---")
c.execute("SELECT COUNT(*) FROM translations")
t_total = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM translations WHERE en IS NOT NULL AND en != ''")
t_en = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM translations WHERE ru IS NOT NULL AND ru != ''")
t_ru = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM translations WHERE hi IS NOT NULL AND hi != ''")
t_hi = c.fetchone()[0]
print(f"  Keys: {t_total} | EN: {t_en} | RU: {t_ru} | HI: {t_hi}")

c.execute("SELECT COUNT(*) FROM sub_periods")
sp = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM dandas")
d = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM period_nodes")
pn = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM sections")
sec = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM books")
books = c.fetchone()[0]
print(f"\n  Sections: {sec}")
print(f"  Sub-periods: {sp}")
print(f"  Dandas: {d}")
print(f"  Period nodes: {pn}")
print(f"  Books: {books}")

print("\n--- Sample verse (ID 1) ---")
c.execute("SELECT * FROM verses WHERE id = 1")
cols = [d[0] for d in c.description]
row = c.fetchone()
for col, val in zip(cols, row):
    display = str(val)[:100] if val else "NULL"
    print(f"  {col}: {display}")

print("\n--- Sample translation (id=1) ---")
c.execute("SELECT * FROM translations WHERE id = 1")
cols = [d[0] for d in c.description]
row = c.fetchone()
for col, val in zip(cols, row):
    display = str(val)[:80] if val else "NULL"
    print(f"  {col}: {display}")

conn.close()
print("\n=== AUDIT COMPLETE ===")
