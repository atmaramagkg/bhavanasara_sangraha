import sqlite3, re

db_path = r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha.sqlite'
conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute("SELECT ref_display, transliteration, book_id FROM verses WHERE sanskrit_text IS NULL OR sanskrit_text = '' ORDER BY ref_display")
missing = c.fetchall()

print(f'Missing {len(missing)} verses:')
for ref, tr, bid in missing:
    words = tr.split()[:8] if tr else []
    print(f'  {ref} book={bid}: {" ".join(words)}...')
conn.close()
