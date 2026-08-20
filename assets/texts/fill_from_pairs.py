import json, sqlite3

DB = r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha.sqlite'
PAIRS = r'C:\Users\austr\bss\assets\texts\bss_all_pairs.json'

conn = sqlite3.connect(DB)
c = conn.cursor()

with open(PAIRS, encoding='utf-8') as f:
    all_pairs = json.load(f)

filled = 0
for sec_str, entries in all_pairs.items():
    sec_num = int(sec_str)
    for p in entries:
        if not p['sanskrit']:
            continue
        vnum = p['verse_num']
        ref = f"{sec_num}.{vnum}"
        
        c.execute("SELECT id, sanskrit_text FROM verses WHERE ref_display = ?", (ref,))
        row = c.fetchone()
        if row and not row[1]:
            # Fill it
            text = p['sanskrit'].strip()
            c.execute("UPDATE verses SET sanskrit_text = ? WHERE id = ?", (text, row[0]))
            print(f"Filled {ref}: {text[:80]}...")
            filled += 1

conn.commit()
print(f"\nFilled {filled} verses")

c.execute("SELECT COUNT(*) FROM verses WHERE sanskrit_text IS NOT NULL AND sanskrit_text != ''")
total = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM verses WHERE sanskrit_text IS NULL OR sanskrit_text = ''")
empty = c.fetchone()[0]
print(f"Final: {total} filled, {empty} empty, {total + empty} total")
conn.close()
