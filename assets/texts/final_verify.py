import sqlite3

db = r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha.sqlite'
conn = sqlite3.connect(db)
c = conn.cursor()

c.execute("SELECT COUNT(*) FROM verses WHERE sanskrit_text IS NOT NULL AND sanskrit_text != ''")
total = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM verses WHERE sanskrit_text IS NULL OR sanskrit_text = ''")
empty = c.fetchone()[0]
print(f"Sanskrit text: {total} filled, {empty} empty, {total + empty} total")

# Check for remaining issues
issues = 0
c.execute("SELECT ref_display, sanskrit_text FROM verses WHERE sanskrit_text IS NOT NULL AND sanskrit_text != ''")
for ref, text in c.fetchall():
    if text[0] in '\u0966\u0967\u0968\u0969\u096a\u096b\u096c\u096d\u096e\u096f':
        issues += 1
        print(f"  DIGIT: {ref}: {text[:60]}")
    elif text.startswith('('):
        issues += 1
        print(f"  PAREN: {ref}: {text[:60]}")
    elif text[0] in '\u0902\u0903\u0901':
        issues += 1
        print(f"  MARK: {ref}: {text[:60]}")
print(f"Remaining issues: {issues}")

# Check translations table
c.execute("SELECT COUNT(*) FROM translations WHERE (en IS NULL OR en = '') AND (ru IS NULL OR ru = '')")
t_empty = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM translations")
t_total = c.fetchone()[0]
print(f"\nTranslations: {t_total} total, {t_empty} missing EN+RU")

conn.close()
