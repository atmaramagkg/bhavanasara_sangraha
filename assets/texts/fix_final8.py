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

# For the remaining 8 missing verses, manually examine and extract
remaining = [
    (3, 394),   # Beyond section range
    (3, 49),    # Gap with inverted lines
    (4, 790),   # Gap 788->801, garbled numbers
    (4, 1093),  # Gap 1088->1100, garbled numbers
    (4, 1199),  # Gap 1188->1200, garbled numbers
    (4, 1269),  # Gap 1268->1270, inverted lines
    (8, 289),   # Gap 288->296, inverted lines
    (8, 297),   # Beyond section range
]

# Build all verse positions across all sections
verse_positions = {}  # (main_sec, verse_num) -> line_number
for main_sec, (start, end) in bss_line_ranges.items():
    for i in range(start, min(end, len(bss_lines))):
        stripped = bss_lines[i].strip()
        if not stripped:
            continue
        for pat in [r'([०-९]{1,4})\s*[।॥|]+\s*$', r'[।॥|]\s+([०-९]{1,4})\s*$', r'\s([०-९]{1,4})\s*$']:
            m = re.search(pat, stripped)
            if m:
                vnum = dev_to_num(m.group(1))
                if vnum and 1 <= vnum <= 2000:
                    pre = stripped[:m.start()].rstrip()
                    if not pre.endswith('(') and not stripped.startswith('('):
                        key = (main_sec, vnum)
                        if key not in verse_positions:
                            verse_positions[key] = i
                    break

conn = sqlite3.connect(db)
c = conn.cursor()

for sec, vnum in remaining:
    print(f"\n=== {sec}.{vnum} ===")
    
    # Find ALL verse positions in this section, sorted by line number
    sec_verses = sorted(
        [(vn, ln) for (s, vn), ln in verse_positions.items() if s == sec],
        key=lambda x: x[1]
    )
    
    if not sec_verses:
        print("  No verse positions found in section")
        continue
    
    # Find the verse before and after by LINE ORDER (not number)
    before = None
    after = None
    for i, (vn, ln) in enumerate(sec_verses):
        if vn == vnum:
            print(f"  Verse {vn} IS in BSS.txt at line {ln}!")
            # Extract it directly
            line = bss_lines[ln].strip()
            verse_lines = [line]
            for j in range(ln-1, max(ln-5, sec_verses[i-1][1] if i > 0 else 0), -1):
                prev = bss_lines[j].strip()
                if not prev or prev.startswith('(') or re.match(r'^\(\s*[०-९]', prev):
                    break
                verse_lines.insert(0, prev)
            verse_text = ' '.join(verse_lines)
            verse_text = re.sub(r'\s*[।॥|]+\s*[०-९]+\s*[।॥|]+\s*', '', verse_text)
            verse_text = re.sub(r'\s*[।॥|]+\s*$', '', verse_text).strip()
            print(f"  Text: {verse_text[:120]}...")
            c.execute("UPDATE verses SET sanskrit_text = ? WHERE ref_display = ?", (verse_text, f"{sec}.{vnum}"))
            break
    
        # Check if this verse number is before vnum (by number) and line is before
        if vn < vnum:
            before = (vn, ln)
        if vn > vnum and after is None:
            after = (vn, ln)
    
    if before is None or after is None:
        print(f"  Cannot find surrounding verses: before={before}, after={after}")
        continue
    
    print(f"  Before: {before[0]}@L{before[1]}, After: {after[0]}@L{after[1]}")
    
    # Collect Sanskrit blocks between before and after LINE positions
    start_line = before[1]
    end_line = after[1]
    
    if start_line >= end_line:
        print(f"  Inverted line order! start={start_line} >= end={end_line}")
        # This means the verse ordering is wrong - skip
        continue
    
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
        if 'श्रीश्री भावना सार' in line or 'अथ ' in line[:10] or line.startswith('#'):
            if current_block:
                blocks.append(' '.join(current_block))
                current_block = []
            continue
        if '।' in line or '॥' in line or (current_block and len(line) > 10):
            current_block.append(line)
    if current_block:
        blocks.append(' '.join(current_block))
    
    # How many missing verses between before[0] and after[0]?
    # Count ALL verse numbers that exist in DB between before[0] and after[0]
    c.execute("SELECT ref_display FROM verses WHERE main_section = ? AND sanskrit_text IS NULL OR (sanskrit_text = '' AND main_section = ?)", (sec, sec))
    missing_in_section = [row[0] for row in c.fetchall()]
    missing_between = [r for r in missing_in_section 
                       if before[0] < int(r.split('.')[1]) < after[0]]
    
    print(f"  Blocks: {len(blocks)}, Missing between: {len(missing_between)} = {missing_between}")
    
    if not missing_between:
        continue
    
    # Match blocks to missing verses by position
    for i, ref in enumerate(sorted(missing_between)):
        vn = int(ref.split('.')[1])
        if i < len(blocks):
            verse_text = blocks[i]
            verse_text = re.sub(r'\s*[।॥|]+\s*[०-९]+\s*[।॥|]+\s*', '', verse_text)
            verse_text = re.sub(r'\s*[।॥|]+\s*$', '', verse_text).strip()
            if verse_text and len(verse_text) > 10:
                print(f"  {ref}: {verse_text[:100]}...")
                c.execute("UPDATE verses SET sanskrit_text = ? WHERE ref_display = ?", (verse_text, ref))

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
