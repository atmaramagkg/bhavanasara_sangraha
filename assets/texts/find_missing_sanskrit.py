import sqlite3

db = r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha.sqlite'
conn = sqlite3.connect(db)
c = conn.cursor()

# Get all verses missing sanskrit_text
c.execute("""SELECT id, section_id, sort_order, ref_display, transliteration 
    FROM verses 
    WHERE sanskrit_text IS NULL OR sanskrit_text = '' 
    ORDER BY section_id, sort_order""")
missing = c.fetchall()

print(f"Total missing Sanskrit: {len(missing)}")
print()

# Group by section
sections = {}
for row in missing:
    sec = row[1]
    if sec not in sections:
        sections[sec] = []
    sections[sec].append(row)

for sec in sorted(sections.keys()):
    verses = sections[sec]
    print(f"Section {sec}: {len(verses)} missing")
    for v in verses[:3]:
        print(f"  ID={v[0]} sort={v[2]} ref={v[3]}")
    if len(verses) > 3:
        print(f"  ... and {len(verses)-3} more")
    print()

# Save full list
with open(r'C:\Users\austr\bss\assets\texts\missing_sanskrit.txt', 'w', encoding='utf-8') as f:
    for v in missing:
        f.write(f"{v[0]}\t{v[1]}\t{v[2]}\t{v[3]}\n")

print(f"Saved to missing_sanskrit.txt")

conn.close()
