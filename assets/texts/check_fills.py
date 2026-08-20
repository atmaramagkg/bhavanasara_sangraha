import json, sqlite3

DB = r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha.sqlite'
PAIRS = r'C:\Users\austr\bss\assets\texts\bss_all_pairs.json'

conn = sqlite3.connect(DB)
c = conn.cursor()
c.execute("SELECT section_id, ref_display, sanskrit_text FROM verses")
db_empty = {}
for sec_id, ref, text in c.fetchall():
    if not text:
        parts = ref.split('.')
        main_sec = int(parts[0])
        vnum = int(parts[1])
        db_empty[(main_sec, vnum)] = ref

with open(PAIRS, encoding='utf-8') as f:
    all_pairs = json.load(f)

# Map section number (1-8) to pairs
for sec_str, entries in all_pairs.items():
    sec_num = int(sec_str)
    for p in entries:
        if p['sanskrit']:
            key = (sec_num, p['verse_num'])
            if key in db_empty:
                print(f"FILLABLE: {db_empty[key]}")
                print(f"  Sanskrit from BSS.txt: {p['sanskrit'][:120]}...")
                print(f"  Hindi: {(p['hindi_translation'] or '')[:120]}...")
                print(f"  Citation: {p['citation']}")

print(f"\nAll empty DB verses ({len(db_empty)}):")
for (sec, vnum), ref in sorted(db_empty.items()):
    print(f"  {ref}")

conn.close()
