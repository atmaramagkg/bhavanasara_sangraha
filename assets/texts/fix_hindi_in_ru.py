import sqlite3, re

db = r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha.sqlite'
conn = sqlite3.connect(db)
c = conn.cursor()

# Find entries with Devanagari in ru column
devanagari_re = re.compile(r'[\u0900-\u097F]')

c.execute("SELECT id, translation_key, en, ru, hi FROM translations")
bad = []
good_ru = 0
for row in c.fetchall():
    rid, key, en, ru, hi = row
    if ru and devanagari_re.search(ru):
        bad.append((rid, key, en, ru, hi))
    elif ru:
        good_ru += 1

print(f'Entries with Devanagari in ru column: {len(bad)}')
print(f'Entries with actual Russian in ru column: {good_ru}')

# Move Devanagari from ru to hi
for rid, key, en, ru, hi in bad:
    print(f'\n  id={rid} {key}')
    print(f'    en={en!r}')
    print(f'    ru={ru!r} -> moving to hi')
    c.execute("UPDATE translations SET hi = ?, ru = NULL WHERE id = ?", (ru, rid))

conn.commit()

# Verify
c.execute("SELECT COUNT(*) FROM translations WHERE ru IS NOT NULL AND ru != ''")
ru_count = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM translations WHERE hi IS NOT NULL AND hi != ''")
hi_count = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM translations WHERE en IS NOT NULL AND en != ''")
en_count = c.fetchone()[0]

print(f'\nAfter fix:')
print(f'  EN: {en_count}')
print(f'  RU: {ru_count}')
print(f'  HI: {hi_count}')

# Check which ru entries still have no content
c.execute("SELECT COUNT(*) FROM translations WHERE (ru IS NULL OR ru = '') AND (en IS NULL OR en = '')")
both_empty = c.fetchone()[0]
print(f'  Both en and ru empty: {both_empty}')

# Show the 30 fixed entries
print('\nFixed entries (now in hi column):')
c.execute("SELECT id, translation_key, en, ru, hi FROM translations WHERE hi IS NOT NULL AND hi != ''")
for row in c.fetchall():
    print(f'  id={row[0]} {row[1]}: hi={row[4][:60]}')

conn.close()
