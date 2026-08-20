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

# Extract verse blocks from BSS.txt
# Strategy: find Devanagari verse number markers ।।number।। at end of lines
# Then collect the Sanskrit text (usually 2 lines before + current line)
bss_verses = {}

for main_sec, (start, end) in bss_line_ranges.items():
    section_lines = bss_lines[start:end]
    n = len(section_lines)
    
    for i in range(n):
        stripped = section_lines[i].strip()
        if not stripped:
            continue
        
        # Check for verse number at end: ।।१०७९।। or १०७९ ।।
        m = re.search(r'([०-९]{1,4})\s*[।॥|]+\s*$', stripped)
        if not m:
            continue
        
        vnum = dev_to_num(m.group(1))
        if not vnum or vnum < 1 or vnum > 2000:
            continue
        
        # Check if the line itself looks like a Sanskrit verse (contains Devanagari + danda)
        # vs Hindi commentary (which also has verse numbers in parentheses)
        # Sanskrit verse lines typically have no parentheses around verse number
        # and contain lots of dandas and Sanskrit-looking text
        
        # Check: is the verse number preceded by ।। (verse marker) vs (number) (commentary reference)?
        pre_text = stripped[:m.start()].rstrip()
        
        # Hindi commentary lines have format: (१२३४) Hindi text
        # Sanskrit verse lines have format: ...text।।१२३४।।
        if pre_text.endswith('(') or stripped.startswith('('):
            # This is a commentary reference, not a verse
            continue
        
        # Collect verse: look backwards for Sanskrit text
        verse_lines = []
        # Current line (remove verse number marker)
        current = re.sub(r'[०-९]+\s*[।॥|]+\s*$', '', stripped).strip()
        current = re.sub(r'\s*[।॥|]+\s*$', '', current).strip()
        if current:
            verse_lines.append(current)
        
        # Look backwards for Sanskrit verse lines (up to 4 lines)
        for j in range(i-1, max(-1, i-5), -1):
            prev = section_lines[j].strip()
            if not prev:
                break
            # Stop if we hit a Hindi commentary line or a verse number reference
            if prev.startswith('(') or re.match(r'^\(\s*[०-९]', prev):
                break
            # Stop if we hit a section header or page header
            if 'श्रीश्री भावना सार' in prev or 'अथ ' in prev or prev.startswith('#'):
                break
            # Check if it's a Sanskrit-looking line (contains dandas, transliteration markers)
            verse_lines.insert(0, prev)
        
        verse_text = ' '.join(verse_lines).strip()
        # Clean trailing verse number markers
        verse_text = re.sub(r'\s*[।॥|]+\s*$', '', verse_text).strip()
        verse_text = re.sub(r'\s*[।॥|]+\s*[०-९]+\s*[।॥|]+\s*$', '', verse_text).strip()
        
        if verse_text and len(verse_text) > 5:
            key = (main_sec, vnum)
            if key not in bss_verses:
                bss_verses[key] = verse_text

print(f"Extracted {len(bss_verses)} verse blocks from BSS.txt")

# Show per-section counts
for sec in sorted(bss_line_ranges.keys()):
    nums = [v[1] for v in bss_verses.keys() if v[0] == sec]
    if nums:
        print(f"  Section {sec}: {len(nums)} verses (range {min(nums)}-{max(nums)})")

# Now get missing verses from DB
conn = sqlite3.connect(db)
c = conn.cursor()
c.execute("""SELECT id, ref_display, transliteration FROM verses 
    WHERE sanskrit_text IS NULL OR sanskrit_text = '' ORDER BY ref_display""")
missing = c.fetchall()

print(f"\nMissing: {len(missing)}")
found_updates = []

for vid, ref, translit in missing:
    parts = ref.split('.')
    main_sec = int(parts[0])
    verse_num = int(parts[1])
    
    key = (main_sec, verse_num)
    if key in bss_verses:
        found_updates.append((vid, bss_verses[key], ref))
    else:
        print(f"  NOT FOUND: {ref} (main_sec={main_sec}, verse_num={verse_num})")

print(f"\nFound: {len(found_updates)}/{len(missing)}")

for vid, sk_text, ref in found_updates:
    c.execute("UPDATE verses SET sanskrit_text = ? WHERE id = ?", (sk_text, vid))

conn.commit()

c.execute("SELECT COUNT(*) FROM verses WHERE sanskrit_text IS NOT NULL AND sanskrit_text != ''")
after = c.fetchone()[0]
print(f"Sanskrit coverage: {after}/3066 ({100*after/3066:.1f}%)")

conn.close()
