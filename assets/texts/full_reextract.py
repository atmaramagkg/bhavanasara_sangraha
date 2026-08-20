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

# ============================================================
# STEP 1: Extract all verse blocks from BSS.txt by verse number markers
# ============================================================
print("STEP 1: Extracting verse blocks from BSS.txt by verse number markers...")
bss_verses = {}
for main_sec, (start, end) in bss_line_ranges.items():
    section_lines = bss_lines[start:end]
    n = len(section_lines)
    for i in range(n):
        stripped = section_lines[i].strip()
        if not stripped:
            continue
        if stripped.startswith('(') or re.match(r'^\(\s*[०-९]', stripped):
            continue
        
        # Try multiple patterns for verse number at end of line
        vnum = None
        for pat in [r'([०-९]{1,4})\s*[।॥|]+\s*$', r'[।॥|]\s+([०-९]{1,4})\s*$', r'\s([०-९]{1,4})\s*$']:
            m = re.search(pat, stripped)
            if m:
                vnum = dev_to_num(m.group(1))
                if vnum and 1 <= vnum <= 2000:
                    break
                vnum = None
        
        if not vnum:
            continue
        
        # Collect verse lines looking backwards
        verse_lines = []
        current = re.sub(r'[।॥|]?\s*[०-९]{1,4}\s*[।॥|]?\s*$', '', stripped).strip()
        current = re.sub(r'\s*[।॥|]+\s*$', '', current).strip()
        if current:
            verse_lines.append(current)
        
        for j in range(i-1, max(-1, i-5), -1):
            prev = section_lines[j].strip()
            if not prev:
                break
            if prev.startswith('(') or re.match(r'^\(\s*[०-९]', prev):
                break
            if 'श्रीश्री भावना सार' in prev or 'अथ ' in prev[:10] or prev.startswith('#'):
                break
            has_own_num = False
            for pat in [r'([०-९]{1,4})\s*[।॥|]+\s*$', r'[।॥|]\s+([०-९]{1,4})\s*$', r'\s([०-९]{1,4})\s*$']:
                if re.search(pat, prev):
                    has_own_num = True
                    break
            if has_own_num:
                break
            verse_lines.insert(0, prev)
        
        verse_text = ' '.join(verse_lines).strip()
        verse_text = re.sub(r'\s*[।॥|]+\s*$', '', verse_text).strip()
        
        if verse_text and len(verse_text) > 5:
            key = (main_sec, vnum)
            if key not in bss_verses:
                bss_verses[key] = verse_text

print(f"  Found {len(bss_verses)} verse blocks")

# ============================================================
# STEP 2: Build verse positions map (for gap extraction)
# ============================================================
print("STEP 2: Building verse positions map...")
verse_positions = {}
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

# ============================================================
# STEP 3: Update DB - verse-number matches first, then gap extraction
# ============================================================
print("STEP 3: Updating DB...")
conn = sqlite3.connect(db)
c = conn.cursor()

c.execute("SELECT id, ref_display FROM verses WHERE sanskrit_text IS NULL OR sanskrit_text = ''")
missing = {row[1]: row[0] for row in c.fetchall()}
print(f"  Missing: {len(missing)}")

# First pass: verse-number matches
updated = 0
for ref, vid in list(missing.items()):
    parts = ref.split('.')
    main_sec = int(parts[0])
    verse_num = int(parts[1])
    key = (main_sec, verse_num)
    if key in bss_verses:
        c.execute("UPDATE verses SET sanskrit_text = ? WHERE id = ?", (bss_verses[key], vid))
        del missing[ref]
        updated += 1

print(f"  Verse-number matches: {updated}")

# Second pass: gap extraction for remaining
gap_found = 0
for ref, vid in list(missing.items()):
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
    
    # Collect Sanskrit blocks between before and after
    blocks = []
    current_block = []
    for j in range(before[1] + 1, after[1]):
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
    
    if not blocks:
        continue
    
    idx = verse_num - before[0] - 1
    if 0 <= idx < len(blocks):
        verse_text = blocks[idx]
        verse_text = re.sub(r'\s*[।॥|]+\s*[०-९]+\s*[।॥|]+\s*', '', verse_text)
        verse_text = re.sub(r'\s*[।॥|]+\s*$', '', verse_text).strip()
        if verse_text and len(verse_text) > 10:
            c.execute("UPDATE verses SET sanskrit_text = ? WHERE id = ?", (verse_text, vid))
            del missing[ref]
            gap_found += 1

print(f"  Gap extraction: {gap_found}")

conn.commit()

c.execute("SELECT COUNT(*) FROM verses WHERE sanskrit_text IS NOT NULL AND sanskrit_text != ''")
after = c.fetchone()[0]
print(f"\nSanskrit coverage: {after}/3066 ({100*after/3066:.1f}%)")

c.execute("SELECT COUNT(*) FROM verses WHERE sanskrit_text IS NULL OR sanskrit_text = ''")
remaining = c.fetchone()[0]
print(f"Still missing: {remaining}")

if remaining > 0:
    c.execute("SELECT ref_display FROM verses WHERE sanskrit_text IS NULL OR sanskrit_text = '' ORDER BY ref_display")
    for (ref,) in c.fetchall():
        print(f"  {ref}")

conn.close()
