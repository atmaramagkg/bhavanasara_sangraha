import re, sqlite3

ocr_file = r'C:\Users\austr\bss\assets\texts\ocr_full.txt'
db = r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha.sqlite'

with open(ocr_file, 'r', encoding='utf-8') as f:
    ocr_text = f.read()

# Split using page markers
parts = re.split(r'===PAGE (PART\d+_\d+)\.png===\n?', ocr_text)
page_texts = {}
for i in range(1, len(parts), 2):
    page_texts[parts[i]] = parts[i+1] if i+1 < len(parts) else ''

print(f"OCR pages: {len(page_texts)}")

dev_to_int = {'०':0,'१':1,'२':2,'३':3,'४':4,'५':5,'६':6,'७':7,'८':8,'९':9}
def dev_to_num(s):
    r = 0
    for c in s:
        if c in dev_to_int: r = r*10+dev_to_int[c]
        else: return None
    return r

# Detect section from each page header
all_pages = sorted(page_texts.keys(), key=lambda p: (p.split('_')[0], int(p.split('_')[1])))

current_section = None
page_section_map = {}
section_names = ['निशान्त', 'प्रातः', 'पूर्वाह्न', 'मध्याह्न', 'अपराह्न', 'सायाह्न', 'प्रदोष', 'निशा']
for pname in all_pages:
    pcontent = page_texts[pname]
    for sn in section_names:
        if sn in pcontent and 'लीला' in pcontent:
            current_section = sn
            break
    page_section_map[pname] = current_section

from collections import Counter
print(f"Sections found: {dict(Counter(page_section_map.values()))}")

# Extract verse numbers from each page
page_verses = {}  # pname -> [(verse_num, verse_text)]
for pname in all_pages:
    pcontent = page_texts[pname]
    lines = pcontent.split('\n')
    for i, line in enumerate(lines):
        m = re.search(r'([०-९]{1,4})\s*[।॥|]+\s*$', line)
        if m:
            vnum = dev_to_num(m.group(1))
            if vnum and 1 <= vnum <= 2000:
                verse_lines = []
                for j in range(max(0, i-3), i+1):
                    verse_lines.append(lines[j].strip())
                verse_text = '\n'.join(l for l in verse_lines if l)
                if verse_text and len(verse_text) > 10:
                    if pname not in page_verses:
                        page_verses[pname] = []
                    page_verses[pname].append((vnum, verse_text))

total_verses = sum(len(v) for v in page_verses.values())
print(f"Total verse markers in OCR: {total_verses}")

# Get remaining missing verses
conn = sqlite3.connect(db)
c = conn.cursor()
c.execute("""SELECT id, ref_display FROM verses 
    WHERE sanskrit_text IS NULL OR sanskrit_text = '' ORDER BY ref_display""")
missing = c.fetchall()
print(f"Missing: {len(missing)}")

ref_to_section_name = {1:'निशान्त', 2:'प्रातः', 3:'पूर्वाह्न', 4:'मध्याह्न', 
                       5:'अपराह्न', 6:'सायाह्न', 7:'प्रदोष', 8:'निशा'}

found_updates = []
for vid, ref in missing:
    main_sec, verse_num = ref.split('.')
    main_sec = int(main_sec)
    verse_num = int(verse_num)
    sec_name = ref_to_section_name.get(main_sec)
    if not sec_name:
        continue
    
    for pname in all_pages:
        if page_section_map.get(pname) != sec_name:
            continue
        if pname in page_verses:
            for vnum, vtext in page_verses[pname]:
                if vnum == verse_num:
                    found_updates.append((vid, vtext, ref))
                    break
            if any(u[0] == vid for u in found_updates):
                break

print(f"Found in OCR: {len(found_updates)}")

for vid, sk_text, ref in found_updates:
    c.execute("UPDATE verses SET sanskrit_text = ? WHERE id = ?", (sk_text, vid))

conn.commit()

c.execute("SELECT COUNT(*) FROM verses WHERE sanskrit_text IS NOT NULL AND sanskrit_text != ''")
after = c.fetchone()[0]
print(f"\nSanskrit coverage: {after}/3066 ({100*after//3066}%)")

c.execute("""SELECT ref_display FROM verses 
    WHERE sanskrit_text IS NULL OR sanskrit_text = '' ORDER BY ref_display""")
remaining = c.fetchall()
print(f"Still missing: {len(remaining)}")
for r in remaining[:15]:
    print(f"  {r[0]}")

conn.close()
