import sqlite3

hi_db = r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha_Hi.sqlite'
UNIFIED_DB = r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha.sqlite'

# Extract from HI DB: for each (chapter, verse_start), take the first entry's devanagari text
conn_hi = sqlite3.connect(hi_db)
c_hi = conn_hi.cursor()

hi_mapping = {}  # {(section, verse_num): devanagari_text}
for row in c_hi.execute("""SELECT chapter, verse_start, original_text_devanagari 
    FROM verses WHERE original_text_devanagari IS NOT NULL AND original_text_devanagari != ''
    AND chapter != '' ORDER BY id"""):
    ch, vstart, dev = row
    # Parse section from chapter
    try:
        sec = int(ch.split('.')[0])
    except:
        continue
    if sec < 1 or sec > 8:
        continue
    try:
        vn = int(vstart)
    except:
        continue
    if vn < 1:
        continue
    key = (sec, vn)
    if key not in hi_mapping:
        hi_mapping[key] = dev.strip()

conn_hi.close()
print(f'HI DB: {len(hi_mapping)} unique (section, verse) mappings')

# Show per section
for sec in range(1, 9):
    cnt = sum(1 for k in hi_mapping if k[0] == sec)
    print(f'  Section {sec}: {cnt} entries')

# Now apply to unified DB - only fill empty sanskrit_text
conn = sqlite3.connect(UNIFIED_DB)
c = conn.cursor()

c.execute("SELECT COUNT(*) FROM verses WHERE sanskrit_text IS NOT NULL AND sanskrit_text != ''")
before = c.fetchone()[0]

updated = 0
for (sec, vn), text in sorted(hi_mapping.items()):
    ref = f'{sec}.{vn}'
    c.execute("SELECT sanskrit_text FROM verses WHERE ref_display = ?", (ref,))
    row = c.fetchone()
    if row and row[0]:
        continue
    c.execute("UPDATE verses SET sanskrit_text = ? WHERE ref_display = ?", (text, ref))
    if c.rowcount > 0:
        updated += 1

conn.commit()

c.execute("SELECT COUNT(*) FROM verses WHERE sanskrit_text IS NOT NULL AND sanskrit_text != ''")
after = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM verses")
total = c.fetchone()[0]

print(f'\nBefore: {before}/{total}')
print(f'New from HI DB: {updated}')
print(f'After: {after}/{total} ({after*100//total}%)')

# Remaining gaps
c.execute("SELECT ref_display FROM verses WHERE sanskrit_text IS NULL OR sanskrit_text = '' ORDER BY ref_display")
missing = [row[0] for row in c.fetchall()]
from collections import Counter
sec_counts = Counter(int(r.split('.')[0]) for r in missing)
print(f'\nStill missing: {len(missing)} verses')
for sec in range(1, 9):
    if sec in sec_counts:
        print(f'  Section {sec}: {sec_counts[sec]}')

conn.close()
print('\nDone.')
