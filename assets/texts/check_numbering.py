import sqlite3

db = r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha.sqlite'
conn = sqlite3.connect(db)
c = conn.cursor()

# What are the actual verse numbers in DB for section 4?
c.execute("""SELECT ref_display, verse_number, sanskrit_text IS NOT NULL AND sanskrit_text != '' as has_sk
    FROM verses WHERE main_section = 4 ORDER BY verse_number""")
rows = c.fetchall()
print(f"Section 4 in DB: {len(rows)} verses")
print(f"Verse number range: {rows[0][1]} to {rows[-1][1]}")
print(f"First 10: {[r[0] for r in rows[:10]]}")
print(f"Last 10: {[r[0] for r in rows[-10:]]}")
print(f"Missing ones:")
for ref, vn, has_sk in rows:
    if not has_sk:
        print(f"  {ref} (verse_number={vn})")

# What does the transliteration file look like for section 4?
print("\n--- Transliteration file section 4 verse numbers ---")
# Read first 5 lines and last 5 lines of section 4
with open(r'C:\Users\austr\bss\assets\texts\sanskrit_transliteration.txt', 'r', encoding='utf-8') as f:
    content = f.read()

import re
# Find all verse markers
markers = list(re.finditer(r'---VERSE (\d+) (\d+\.(\d+))---', content))
sec4 = [(int(m.group(1)), m.group(2), int(m.group(3))) for m in markers if m.group(2).startswith('4.')]
print(f"Transliteration section 4: {len(sec4)} verses")
if sec4:
    print(f"First: {sec4[0]}")
    print(f"Last: {sec4[-1]}")
    print(f"Verse numbers (3rd field): {sec4[0][2]} to {sec4[-1][2]}")

# Show the specific missing verse numbers
c.execute("""SELECT verse_number, ref_display FROM verses 
    WHERE main_section = 4 AND (sanskrit_text IS NULL OR sanskrit_text = '')""")
missing = c.fetchall()
print(f"\nMissing in sec4: {len(missing)}")
for vn, ref in missing:
    print(f"  {ref} (verse_number={vn})")

conn.close()
