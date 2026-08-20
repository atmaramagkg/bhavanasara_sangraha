import sqlite3

conn = sqlite3.connect(r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha.sqlite')
c = conn.cursor()
c.execute("SELECT COUNT(*) FROM verses WHERE sanskrit_text IS NOT NULL AND sanskrit_text != ''")
total = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM verses WHERE sanskrit_text IS NULL OR sanskrit_text = ''")
empty = c.fetchone()[0]
print(f"Sanskrit: {total} filled, {empty} empty")

c.execute("SELECT ref_display, sanskrit_text FROM verses WHERE sanskrit_text IS NOT NULL AND sanskrit_text != ''")
issues = 0
for ref, text in c.fetchall():
    bad_start = text[0] in '()}\u0902\u0903\u0901' or text[0] in '\u0966\u0967\u0968\u0969\u096a\u096b\u096c\u096d\u096e\u096f'
    if bad_start:
        issues += 1
        print(f"  {ref}: {text[:60]}")
print(f"Issues: {issues}")

c.execute("SELECT COUNT(*) FROM translations WHERE (en IS NULL OR en = '') AND (ru IS NULL OR ru = '')")
print(f"Translations missing EN+RU: {c.fetchone()[0]}")

conn.close()
