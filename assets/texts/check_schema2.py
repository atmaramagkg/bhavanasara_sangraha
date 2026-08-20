import sqlite3

conn = sqlite3.connect(r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha.sqlite')
c = conn.cursor()

c.execute('PRAGMA table_info(sections)')
print('SECTIONS schema:', c.fetchall())
c.execute('SELECT * FROM sections LIMIT 5')
for r in c.fetchall():
    print(' ', r)

c.execute('SELECT ref_display, section_id FROM verses WHERE ref_display LIKE "4.%" LIMIT 10')
print('\nVerse ref_display -> section_id mapping:')
for r in c.fetchall():
    print(' ', r)

c.execute("SELECT ref_display FROM verses WHERE (sanskrit_text IS NULL OR sanskrit_text = '') ORDER BY ref_display")
print('\nAll missing:')
for r in c.fetchall():
    print(' ', r[0])

conn.close()
