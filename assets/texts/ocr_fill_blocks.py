import re, sqlite3

ocr_file = r'C:\Users\austr\bss\assets\texts\ocr_full.txt'
db = r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha.sqlite'

with open(ocr_file, 'r', encoding='utf-8') as f:
    ocr_text = f.read()

parts = re.split(r'===PAGE (PART\d+_\d+)\.png===\n?', ocr_text)
page_texts = {}
for i in range(1, len(parts), 2):
    page_texts[parts[i]] = parts[i+1] if i+1 < len(parts) else ''

dev_to_int = {'०':0,'१':1,'२':2,'३':3,'४':4,'५':5,'६':6,'७':7,'८':8,'९':9}
def dev_to_num(s):
    r = 0
    for c in s:
        if c in dev_to_int: r = r*10+dev_to_int[c]
        else: return None
    return r

# Build verse text blocks from OCR - all Devanagari lines grouped between blank lines
all_blocks = []  # (page, verse_num_or_none, full_text)
page_list = sorted(page_texts.keys(), key=lambda p: (p.split('_')[0], int(p.split('_')[1])))

for pname in page_list:
    pcontent = page_texts[pname]
    lines = pcontent.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # Skip empty lines and header lines
        if not line or 'भावना सार संग्रह' in line or 'श्रीश्री' in line[:5]:
            i += 1
            continue
        
        # Check if this line or nearby lines contain Sanskrit content
        # Sanskrit lines typically have: |, ||, इ, and specific patterns
        # Collect a block of Devanagari text until blank/header line
        block_lines = []
        verse_num = None
        while i < len(lines):
            l = lines[i].strip()
            if not l:
                i += 1
                break
            if 'श्रीश्री' in l or 'भावना सार संग्रह' in l:
                i += 1
                break
            block_lines.append(l)
            # Check for verse number
            vm = re.search(r'([०-९]{1,4})\s*[।॥|]+\s*$', l)
            if vm:
                vn = dev_to_num(vm.group(1))
                if vn and 1 <= vn <= 2000:
                    verse_num = vn
            # Hindi commentary lines start with ( and contain explanations
            if re.match(r'^[\(]', l) or re.match(r'^\d+\)', l):
                i += 1
                break
            i += 1
        
        if block_lines:
            text = '\n'.join(block_lines)
            # Only keep if it looks like Sanskrit (has danda markers or specific patterns)
            if re.search(r'[॥।|]', text) and len(text) > 20:
                all_blocks.append((pname, verse_num, text))

print(f"OCR text blocks: {len(all_blocks)}")

# Get missing verses  
conn = sqlite3.connect(db)
c = conn.cursor()
c.execute("""SELECT id, ref_display FROM verses 
    WHERE sanskrit_text IS NULL OR sanskrit_text = '' ORDER BY ref_display""")
missing = c.fetchall()

bss_cumulative = {1: (1, 185), 2: (186, 385), 3: (386, 751), 4: (752, 1147),
                  5: (1148, 1546), 6: (1547, 2001), 7: (2002, 2371), 8: (2372, 2669)}

found_updates = []
still_missing = []
for vid, ref in missing:
    main_sec, verse_num_in_sec = ref.split('.')
    main_sec = int(main_sec)
    verse_num_in_sec = int(verse_num_in_sec)
    
    if main_sec in bss_cumulative:
        cum_num = bss_cumulative[main_sec][0] + verse_num_in_sec - 1
    else:
        cum_num = verse_num_in_sec
    
    # Try exact verse number match
    found = False
    for pname, vnum, text in all_blocks:
        if vnum == cum_num:
            found_updates.append((vid, text, ref, cum_num, 'exact'))
            found = True
            break
    
    if not found:
        still_missing.append((vid, ref, cum_num))

print(f"Found by exact match: {len(found_updates)}")
print(f"Still missing: {len(still_missing)}")

# Show remaining missing
for vid, ref, cum in still_missing[:10]:
    print(f"  Missing {ref} (cum={cum})")

# Apply
for vid, sk_text, ref, cum, method in found_updates:
    c.execute("UPDATE verses SET sanskrit_text = ? WHERE id = ?", (sk_text, vid))

conn.commit()

c.execute("SELECT COUNT(*) FROM verses WHERE sanskrit_text IS NOT NULL AND sanskrit_text != ''")
after = c.fetchone()[0]
print(f"\nSanskrit coverage: {after}/3066 ({100*after//3066}%)")

c.execute("""SELECT ref_display FROM verses 
    WHERE sanskrit_text IS NULL OR sanskrit_text = '' ORDER BY ref_display""")
remaining = c.fetchall()
print(f"Final missing: {len(remaining)}")

conn.close()
