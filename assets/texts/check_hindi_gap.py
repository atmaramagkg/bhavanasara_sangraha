import json, sqlite3

DB = r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha.sqlite'
PAIRS = r'C:\Users\austr\bss\assets\texts\bss_all_pairs.json'

conn = sqlite3.connect(DB)
c = conn.cursor()

with open(PAIRS, encoding='utf-8') as f:
    all_pairs = json.load(f)

missing_hindi = 0
for sec_str, entries in all_pairs.items():
    sec_num = int(sec_str)
    for p in entries:
        if not p['hindi_translation']:
            continue
        vnum = p['verse_num']
        ref = f"{sec_num}.{vnum}"
        
        c.execute("SELECT id, translation_hi FROM verses WHERE ref_display = ?", (ref,))
        row = c.fetchone()
        if row and not row[1]:
            missing_hindi += 1
            print(f"  Missing Hindi: {ref}")

print(f"\nTotal missing Hindi translations that BSS.txt has: {missing_hindi}")

# Also check citations
c.execute("SELECT translation_key FROM translations")
existing_keys = set(row[0] for row in c.fetchall())

cite_count = 0
new_cite_count = 0
for sec_str, entries in all_pairs.items():
    for p in entries:
        if p['citation']:
            cite_count += 1

print(f"Total citations found: {cite_count}")
print(f"Translations table keys: {len(existing_keys)}")
conn.close()
