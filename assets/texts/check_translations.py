import sqlite3

conn = sqlite3.connect(r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha.sqlite')
c = conn.cursor()

c.execute('SELECT COUNT(*) FROM translations')
print('Total:', c.fetchone()[0])

c.execute("SELECT COUNT(*) FROM translations WHERE (en IS NULL OR en = '') AND (ru IS NULL OR ru = '')")
print('Missing both EN+RU:', c.fetchone()[0])

c.execute("SELECT COUNT(*) FROM translations WHERE en IS NOT NULL AND en != ''")
print('Has EN:', c.fetchone()[0])

c.execute("SELECT COUNT(*) FROM translations WHERE ru IS NOT NULL AND ru != ''")
print('Has RU:', c.fetchone()[0])

c.execute("SELECT COUNT(*) FROM translations WHERE hi IS NOT NULL AND hi != ''")
print('Has HI:', c.fetchone()[0])

# Show the ones missing EN+RU
c.execute("SELECT id, translation_key, en, ru, hi FROM translations WHERE (en IS NULL OR en = '') AND (ru IS NULL OR ru = '') ORDER BY id")
rows = c.fetchall()
print(f'\nAll {len(rows)} rows missing both EN+RU:')
for r in rows:
    hi_preview = (r[4][:50] if r[4] else '') if r[4] else ''
    print(f'  {r[0]}\t{r[1]}\thi={hi_preview}')
