import sqlite3

db = r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha.sqlite'
conn = sqlite3.connect(db)
c = conn.cursor()

c.execute("SELECT COUNT(*) FROM verses WHERE sanskrit_text LIKE '(' || '%'")
print(f"Still starting with '(': {c.fetchone()[0]}")

c.execute("SELECT ref_display, sanskrit_text FROM verses WHERE sanskrit_text LIKE 'ं%' OR sanskrit_text LIKE 'ः%' OR sanskrit_text LIKE 'ँ%'")
bad = c.fetchall()
print(f"Bad starts (anusvara/visarga): {len(bad)}")
for r in bad:
    print(f"  {r[0]}: {r[1][:80]}")

# Check for any remaining reference patterns
c.execute("""SELECT ref_display, sanskrit_text FROM verses 
    WHERE sanskrit_text GLOB '[०-९]*' AND sanskrit_text LIKE '%)%'""")
import re
refs_left = []
for r in c.fetchall():
    if re.match(r'^[०-९]+\s*[)।॥]', r[1]):
        refs_left.append(r)
print(f"\nStill starting with digit+close-paren: {len(refs_left)}")
for r in refs_left[:5]:
    print(f"  {r[0]}: {r[1][:100]}")

# Check for texts containing Hindi (not Sanskrit) in the verse
c.execute("SELECT ref_display, sanskrit_text FROM verses WHERE sanskrit_text LIKE '%के साथ%' OR sanskrit_text LIKE '%है% कर%' OR sanskrit_text LIKE '%शोभा पा रहे%'")
hindi_in_sanskrit = c.fetchall()
print(f"\nHindi text mixed into sanskrit_text: {len(hindi_in_sanskrit)}")
for r in hindi_in_sanskrit[:5]:
    print(f"  {r[0]}: {r[1][:120]}")

conn.close()
