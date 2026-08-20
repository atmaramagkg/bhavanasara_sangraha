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

def extract_verse_marker(line):
    """Extract verse number from a line with double-danda marker."""
    m = re.search(r'([०-९]{1,4})\s*।।', line)
    if not m:
        m = re.search(r'।।\s*([०-९]{1,4})', line)
    if m:
        return dev_to_num(m.group(1))
    return None

# Build verse markers per section
verse_markers = {}  # {sec: [(vnum, line), ...]} sorted by line
for main_sec, (start, end) in bss_line_ranges.items():
    markers = []
    for i in range(start, min(end, len(bss_lines))):
        stripped = bss_lines[i].strip()
        if not stripped:
            continue
        vnum = extract_verse_marker(stripped)
        if vnum and 1 <= vnum <= 2000:
            pre = stripped[:stripped.find(str(vnum)) if str(vnum) in stripped else 0].rstrip()
            if not stripped.startswith('('):
                markers.append((vnum, i))
    verse_markers[main_sec] = markers

conn = sqlite3.connect(db)
c = conn.cursor()
remaining = [(3, 394), (3, 49), (4, 790), (4, 1093), (4, 1199), (4, 1269), (8, 289), (8, 297)]

for sec, vnum in remaining:
    print(f"\n=== {sec}.{vnum} ===")
    markers = verse_markers.get(sec, [])
    if not markers:
        print("  No markers!")
        continue
    
    # Find surrounding markers: the closest marker by line number
    # BEFORE: marker with highest line that has vn < vnum
    # AFTER: marker with lowest line that has vn > vnum
    before = None
    after = None
    for vn, ln in markers:
        if vn < vnum:
            if before is None or ln > before[1]:
                before = (vn, ln)
        elif vn > vnum:
            if after is None or ln < after[1]:
                after = (vn, ln)
    
    if before:
        print(f"  Before: {before[0]}@L{before[1]}")
    if after:
        print(f"  After: {after[0]}@L{after[1]}")
    
    if not before or not after:
        print("  Cannot find surrounding markers!")
        continue
    
    if before[1] >= after[1]:
        print(f"  Inverted! before@L{before[1]} >= after@L{after[1]}")
        continue
    
    # Collect Sanskrit blocks between before and after by LINE
    blocks = []
    current_block = []
    for j in range(before[1] + 1, after[1]):
        line = bss_lines[j].strip()
        if not line:
            if current_block:
                blocks.append(' '.join(current_block))
                current_block = []
            continue
        if line.startswith('('):
            if current_block:
                blocks.append(' '.join(current_block))
                current_block = []
            continue
        if 'श्रीश्री भावना' in line or ('अथ ' in line and 'लीला' in line):
            if current_block:
                blocks.append(' '.join(current_block))
                current_block = []
            continue
        if '।' in line or '॥' in line or (current_block and len(line) > 10):
            current_block.append(line)
    if current_block:
        blocks.append(' '.join(current_block))
    
    # Find missing verses between before[0] and after[0]
    c.execute("SELECT ref_display FROM verses WHERE (sanskrit_text IS NULL OR sanskrit_text = '')")
    all_missing = [row[0] for row in c.fetchall()]
    missing_between = sorted(
        [r for r in all_missing 
         if r.startswith(f"{sec}.") and before[0] < int(r.split('.')[1]) < after[0]],
        key=lambda x: int(x.split('.')[1])
    )
    
    print(f"  Blocks: {len(blocks)}, Missing: {missing_between}")
    
    # Show block previews
    for i, b in enumerate(blocks[:3]):
        clean = re.sub(r'\s*[।॥|]+\s*[०-९]+\s*[।॥|]+\s*', '', b)
        clean = re.sub(r'\s*[।॥|]+\s*$', '', clean).strip()
        print(f"  Block {i}: {clean[:120]}...")
    
    if blocks and missing_between and len(blocks) == len(missing_between):
        for i, ref in enumerate(missing_between):
            verse_text = blocks[i]
            verse_text = re.sub(r'\s*[।॥|]+\s*[०-९]+\s*[।॥|]+\s*', '', verse_text)
            verse_text = re.sub(r'\s*[।॥|]+\s*$', '', verse_text).strip()
            if verse_text and len(verse_text) > 10:
                print(f"  -> {ref}: {verse_text[:100]}...")
                c.execute("UPDATE verses SET sanskrit_text = ? WHERE ref_display = ?", (verse_text, ref))
    elif missing_between:
        print(f"  MISMATCH - can't auto-assign")

conn.commit()
c.execute("SELECT COUNT(*) FROM verses WHERE sanskrit_text IS NOT NULL AND sanskrit_text != ''")
print(f"\nSanskrit coverage: {c.fetchone()[0]}/3066")
c.execute("SELECT ref_display FROM verses WHERE sanskrit_text IS NULL OR sanskrit_text = '' ORDER BY ref_display")
remaining_final = [row[0] for row in c.fetchall()]
print(f"Still missing: {len(remaining_final)}")
for ref in remaining_final:
    print(f"  {ref}")
conn.close()
