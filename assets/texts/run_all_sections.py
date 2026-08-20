import json
import sqlite3
import sys
sys.path.insert(0, r'C:\Users\austr\bss\assets\texts')
from bss_pair_parser import parse_section

BSS = r'C:\Users\austr\bss\assets\texts\BSS.txt'
DB = r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha.sqlite'

with open(BSS, encoding='utf-8') as f:
    all_lines = f.readlines()

sections = [
    (1, 2314),
    (2315, 7195),
    (7196, 10233),
    (10234, 23207),
    (23208, 24388),
    (24389, 25195),
    (25196, 27235),
    (27236, len(all_lines)),
]

conn = sqlite3.connect(DB)
c = conn.cursor()

c.execute("SELECT section_id, ref_display, sanskrit_text FROM verses")
db_verses = {}
db_empty = {}
for sec_id, ref, text in c.fetchall():
    parts = ref.split('.')
    vnum = int(parts[1])
    db_verses[(sec_id, vnum)] = text
    if not text:
        db_empty[(sec_id, vnum)] = True

c.execute("SELECT section_id, COUNT(*) FROM verses GROUP BY section_id ORDER BY section_id")
db_counts = dict(c.fetchall())
print("DB verse counts:", db_counts)
print(f"DB empty verses: {len(db_empty)}")

total_fillable = 0
for i, (start, end) in enumerate(sections):
    sec_num = i + 1
    chunk = all_lines[start - 1: end]
    numbered, positional = parse_section(chunk)
    
    expected_max = db_counts.get(sec_num, 0) + 10
    valid = [p for p in numbered if p['verse_num'] <= expected_max]
    
    sanskrit_found = sum(1 for p in valid if p['sanskrit'])
    hindi_found = sum(1 for p in valid if p['hindi_translation'])
    citations = sum(1 for p in valid if p['citation'])
    
    fillable = 0
    for p in valid:
        if p['sanskrit']:
            key = (sec_num, p['verse_num'])
            if key in db_empty:
                fillable += 1
    
    total_fillable += fillable
    print(f"Sec {sec_num}: {len(valid)} entries, {sanskrit_found} SK, {hindi_found} HI, {citations} cites, {fillable} fillable")

print(f"\nTotal fillable empty verses: {total_fillable}")

# Save all section results for later use
all_results = {}
for i, (start, end) in enumerate(sections):
    sec_num = i + 1
    chunk = all_lines[start - 1: end]
    numbered, positional = parse_section(chunk)
    expected_max = db_counts.get(sec_num, 0) + 10
    valid = [p for p in numbered if p['verse_num'] <= expected_max]
    all_results[sec_num] = valid

with open(r'C:\Users\austr\bss\assets\texts\bss_all_pairs.json', 'w', encoding='utf-8') as f:
    json.dump(all_results, f, ensure_ascii=False, indent=2)

print(f"\nSaved to bss_all_pairs.json")
conn.close()
