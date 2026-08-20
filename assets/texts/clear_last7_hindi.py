import sqlite3

db = r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha.sqlite'
conn = sqlite3.connect(db)
c = conn.cursor()

refs = ['1.99', '3.369', '4.593', '4.749', '4.1045', '4.1215', '8.169']

for ref in refs:
    c.execute("SELECT id, sanskrit_text FROM verses WHERE ref_display = ?", (ref,))
    row = c.fetchone()
    if row:
        vid, text = row
        print(f"{ref}: cleared ({len(text)} chars)")
        c.execute("UPDATE verses SET sanskrit_text = NULL WHERE id = ?", (vid,))

conn.commit()
c.execute("SELECT COUNT(*) FROM verses WHERE sanskrit_text IS NOT NULL AND sanskrit_text != ''")
total = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM verses WHERE sanskrit_text IS NULL OR sanskrit_text = ''")
empty = c.fetchone()[0]
print(f"\nFinal: {total} filled, {empty} empty, {total + empty} total")
conn.close()
