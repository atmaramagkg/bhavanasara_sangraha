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

def is_sanskrit_verse_line(line):
    """Check if line contains actual Sanskrit verse marker (double danda with number)"""
    return bool(re.search(r'[०-९]{1,4}\s*।।', line)) or bool(re.search(r'।।\s*[०-९]{1,4}', line))

# Build verse positions using ONLY actual Sanskrit verse markers
verse_markers = {}  # (main_sec, verse_num) -> line_number
for main_sec, (start, end) in bss_line_ranges.items():
    for i in range(start, min(end, len(bss_lines))):
        stripped = bss_lines[i].strip()
        if not stripped:
            continue
        if not is_sanskrit_verse_line(stripped):
            continue
        # Extract verse number from marker
        m = re.search(r'([०-९]{1,4})\s*।।', stripped)
        if not m:
            m = re.search(r'।।\s*([०-९]{1,4})', stripped)
        if m:
            vnum = dev_to_num(m.group(1))
            if vnum and 1 <= vnum <= 2000:
                # Verify it's an actual verse line (not commentary)
                pre = stripped[:m.start()].rstrip()
                if not pre.endswith('(') and not stripped.startswith('('):
                    key = (main_sec, vnum)
                    if key not in verse_markers:
                        verse_markers[key] = i

# Print what we found for each section
for sec in range(1, 9):
    markers = sorted([(vn, ln) for (s, vn), ln in verse_markers.items() if s == sec], key=lambda x: x[1])
    if markers:
        print(f"Section {sec}: {len(markers)} markers, line range {markers[0][1]}-{markers[-1][1]}")
        print(f"  First 5: {[(v,l) for v,l in markers[:5]]}")
        print(f"  Last 5: {[(v,l) for v,l in markers[-5:]]}")

# Now check the 8 remaining
conn = sqlite3.connect(db)
c = conn.cursor()
remaining = [(3, 394), (3, 49), (4, 790), (4, 1093), (4, 1199), (4, 1269), (8, 289), (8, 297)]

for sec, vnum in remaining:
    print(f"\n=== {sec}.{vnum} ===")
    markers = sorted([(vn, ln) for (s, vn), ln in verse_markers.items() if s == sec], key=lambda x: x[1])
    
    # Find surrounding markers by line order
    before = None
    after = None
    for i, (vn, ln) in enumerate(markers):
        if ln < (before[1] if before else 999999) and vn < vnum:
            before = (vn, ln)
        if ln > (after[1] if after else 0) and vn > vnum:
            after = (vn, ln)
            break
    
    if before is None and after is None:
        # Try just by number
        for vn, ln in markers:
            if vn < vnum:
                if before is None or ln < before[1]:
                    before = (vn, ln)
            if vn > vnum:
                if after is None or ln < after[1]:
                    after = (vn, ln)
    
    print(f"  Markers in section: {len(markers)}")
    if before:
        print(f"  Before: {before[0]}@L{before[1]}")
    if after:
        print(f"  After: {after[0]}@L{after[1]}")
    
    if before and after and before[1] < after[1]:
        # Collect verse blocks between
        start_line = before[1]
        end_line = after[1]
        blocks = []
        current_block = []
        for j in range(start_line + 1, end_line):
            line = bss_lines[j].strip()
            if not line:
                if current_block:
                    blocks.append(' '.join(current_block))
                    current_block = []
                continue
            if line.startswith('(') or re.match(r'^\(\s*[०-९]', line):
                if current_block:
                    blocks.append(' '.join(current_block))
                    current_block = []
                continue
            if 'श्रीश्री भावना' in line or 'अथ ' in line[:10]:
                if current_block:
                    blocks.append(' '.join(current_block))
                    current_block = []
                continue
            if '।' in line or '॥' in line or (current_block and len(line) > 10):
                current_block.append(line)
        if current_block:
            blocks.append(' '.join(current_block))
        
        # Find missing verses between before[0] and after[0]
        c.execute("SELECT ref_display FROM verses WHERE (sanskrit_text IS NULL OR sanskrit_text = '') AND CAST(SUBSTR(ref_display, 1, INSTR(ref_display, '.') - 1) AS INTEGER) = ?", (sec,))
        all_missing = [row[0] for row in c.fetchall()]
        missing_between = sorted([r for r in all_missing 
                                  if before[0] < int(r.split('.')[1]) < after[0]],
                                 key=lambda x: int(x.split('.')[1]))
        
        print(f"  Blocks: {len(blocks)}, Missing between: {missing_between}")
        
        if blocks and missing_between and len(blocks) == len(missing_between):
            for i, ref in enumerate(missing_between):
                verse_text = blocks[i]
                verse_text = re.sub(r'\s*[।॥|]+\s*[०-९]+\s*[।॥|]+\s*', '', verse_text)
                verse_text = re.sub(r'\s*[।॥|]+\s*$', '', verse_text).strip()
                if verse_text and len(verse_text) > 10:
                    print(f"  -> {ref}: {verse_text[:100]}...")
                    c.execute("UPDATE verses SET sanskrit_text = ? WHERE ref_display = ?", (verse_text, ref))
        elif blocks and missing_between:
            print(f"  MISMATCH: {len(blocks)} blocks vs {len(missing_between)} missing - skipping positional match")

conn.commit()

c.execute("SELECT COUNT(*) FROM verses WHERE sanskrit_text IS NOT NULL AND sanskrit_text != ''")
after_count = c.fetchone()[0]
print(f"\nSanskrit coverage: {after_count}/3066 ({100*after_count/3066:.1f}%)")

c.execute("SELECT ref_display FROM verses WHERE sanskrit_text IS NULL OR sanskrit_text = '' ORDER BY ref_display")
remaining_final = [row[0] for row in c.fetchall()]
print(f"Still missing: {len(remaining_final)}")
for ref in remaining_final:
    print(f"  {ref}")

conn.close()
