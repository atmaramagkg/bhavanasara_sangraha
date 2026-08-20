import re, sqlite3

bss_file = r'C:\Users\austr\bss\assets\texts\BSS.txt'
db = r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha.sqlite'

with open(bss_file, 'r', encoding='utf-8') as f:
    bss_lines = f.readlines()

bss_line_ranges = {1: (460, 2315), 2: (2315, 7196), 3: (7196, 10234), 4: (10234, 23208),
                   5: (23208, 24389), 6: (24389, 25196), 7: (25196, 27236), 8: (27236, 30893)}

dev_to_int = {'०':0,'१':1,'२':2,'३':3,'४':4,'५':5,'६':6,'७':7,'८':8,'९':9}
def dev_to_num(s):
    r = 0
    for c in s:
        if c in dev_to_int: r = r*10+dev_to_int[c]
        else: return None
    return r

verse_positions = {}
for main_sec, (start, end) in bss_line_ranges.items():
    for i in range(start, min(end, len(bss_lines))):
        stripped = bss_lines[i].strip()
        if not stripped:
            continue
        for m in re.finditer(r'([०-९]{1,4})\s*[।॥|]+\s*$', stripped):
            vnum = dev_to_num(m.group(1))
            if vnum and 1 <= vnum <= 2000:
                pre = stripped[:m.start()].rstrip()
                if not pre.endswith('(') and not stripped.startswith('('):
                    key = (main_sec, vnum)
                    if key not in verse_positions:
                        verse_positions[key] = i

conn = sqlite3.connect(db)
c = conn.cursor()
c.execute("SELECT id, ref_display, transliteration FROM verses WHERE sanskrit_text IS NULL OR sanskrit_text = '' ORDER BY ref_display")
missing = c.fetchall()

found_updates = []

for vid, ref, translit in missing:
    parts = ref.split('.')
    main_sec = int(parts[0])
    verse_num = int(parts[1])
    
    before = None
    after = None
    for vnum in range(verse_num - 1, 0, -1):
        if (main_sec, vnum) in verse_positions:
            before = (vnum, verse_positions[(main_sec, vnum)])
            break
    for vnum in range(verse_num + 1, 2000):
        if (main_sec, vnum) in verse_positions:
            after = (vnum, verse_positions[(main_sec, vnum)])
            break
    
    if before is None or after is None:
        continue
    
    before_line = before[1]
    after_line = after[1]
    
    # Collect Sanskrit verse blocks between before and after
    # A block = consecutive Sanskrit lines ending with a danda-terminated line
    blocks = []
    current_block = []
    
    for j in range(before_line + 1, after_line):
        line = bss_lines[j].strip()
        if not line:
            if current_block:
                blocks.append(current_block)
                current_block = []
            continue
        # Skip Hindi commentary
        if line.startswith('(') or re.match(r'^\(\s*[०-९]', line):
            if current_block:
                blocks.append(current_block)
                current_block = []
            continue
        if 'श्रीश्री भावना सार' in line or 'अथ ' in line[:10]:
            if current_block:
                blocks.append(current_block)
                current_block = []
            continue
        # Check if this line contains dandas (Sanskrit indicator)
        if '।' in line or '॥' in line:
            current_block.append(line)
        elif current_block:
            # Continuation of previous Sanskrit block
            current_block.append(line)
    
    if current_block:
        blocks.append(current_block)
    
    # How many missing verses are between before[0] and after[0]?
    num_missing = verse_num - before[0] - 1  # missing verses between
    num_after_missing = after[0] - verse_num  # missing verses after this one
    
    # Find which block index corresponds to this verse
    # If there are N missing verses and M blocks, match by position
    total_missing_in_gap = after[0] - before[0] - 1
    
    if len(blocks) == 0:
        continue
    
    # Determine which block index this verse corresponds to
    # The missing verses are before[0]+1, before[0]+2, ..., after[0]-1
    # blocks[0] = verse before[0]+1, blocks[1] = verse before[0]+2, etc.
    idx = verse_num - before[0] - 1
    
    if idx < len(blocks):
        block = blocks[idx]
        verse_text = ' '.join(block)
        # Clean up verse number markers
        verse_text = re.sub(r'\s*[।॥|]+\s*[०-९]+\s*[।॥|]+\s*', '', verse_text)
        verse_text = re.sub(r'\s*[।॥|]+\s*$', '', verse_text).strip()
        if verse_text and len(verse_text) > 10:
            found_updates.append((vid, verse_text, ref))

print(f"Found {len(found_updates)}/{len(missing)} missing verses")

# Verify quality: check for duplicates
texts = {}
for vid, sk_text, ref in found_updates:
    snippet = sk_text[:60]
    if snippet not in texts:
        texts[snippet] = []
    texts[snippet].append(ref)

dupes = {k: v for k, v in texts.items() if len(v) > 1}
if dupes:
    print(f"\nWARNING: {len(dupes)} duplicate text groups:")
    for snippet, refs in dupes.items():
        print(f"  {snippet}... -> {refs}")

for vid, sk_text, ref in found_updates:
    c.execute("UPDATE verses SET sanskrit_text = ? WHERE id = ?", (sk_text, vid))

conn.commit()

c.execute("SELECT COUNT(*) FROM verses WHERE sanskrit_text IS NOT NULL AND sanskrit_text != ''")
after_count = c.fetchone()[0]
print(f"\nSanskrit coverage: {after_count}/3066 ({100*after_count/3066:.1f}%)")

c.execute("SELECT COUNT(*) FROM verses WHERE sanskrit_text IS NULL OR sanskrit_text = ''")
remaining = c.fetchone()[0]
print(f"Still missing: {remaining}")

if remaining > 0:
    c.execute("SELECT ref_display FROM verses WHERE sanskrit_text IS NULL OR sanskrit_text = '' ORDER BY ref_display")
    for (ref,) in c.fetchall():
        print(f"  {ref}")

conn.close()
