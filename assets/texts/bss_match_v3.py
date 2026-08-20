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

# Patterns for verse numbers in BSS.txt:
# 1. text।।४२८।।  (double danda wrapped)
# 2. text। ४२८    (single danda + space + number at end)
# 3. text ।।४२८।। (space before double danda)
# 4. text ४२८     (just number at end after space)
verse_num_patterns = [
    r'([०-९]{1,4})\s*[।॥|]+\s*$',           # number then danda
    r'[।॥|]\s+([०-९]{1,4})\s*$',            # danda then number (with space)
    r'\s([०-९]{1,4})\s*$',                    # space then number at end
]

bss_verses = {}

for main_sec, (start, end) in bss_line_ranges.items():
    section_lines = bss_lines[start:end]
    n = len(section_lines)
    
    for i in range(n):
        stripped = section_lines[i].strip()
        if not stripped:
            continue
        
        # Skip Hindi commentary lines: start with (number) or contain Hindi text patterns
        if re.match(r'^\(\s*[०-९]', stripped):
            continue
        # Skip section headers
        if 'अथ ' in stripped[:10] or 'श्रीश्री भावना सार' in stripped:
            continue
        
        # Try all patterns
        vnum = None
        m_end = None
        for pat in verse_num_patterns:
            m = re.search(pat, stripped)
            if m:
                vnum = dev_to_num(m.group(1))
                m_end = m.end()
                break
        
        if not vnum or vnum < 1 or vnum > 2000:
            continue
        
        # Check that the verse number is not inside parentheses (commentary reference)
        pre = stripped[:m.start()] if m else stripped
        if '(' in pre[pre.rfind(')'):] if ')' in pre else False:
            continue
        if stripped.startswith('('):
            continue
        
        # Collect verse: look backwards for Sanskrit text
        verse_lines = []
        # Current line - remove verse number and trailing markers
        current = re.sub(r'[।॥|]?\s*[०-९]{1,4}\s*[।॥|]?\s*$', '', stripped).strip()
        current = re.sub(r'\s*[।॥|]+\s*$', '', current).strip()
        if current:
            verse_lines.append(current)
        
        # Look backwards for Sanskrit verse lines
        for j in range(i-1, max(-1, i-5), -1):
            prev = section_lines[j].strip()
            if not prev:
                break
            if prev.startswith('(') or re.match(r'^\(\s*[०-९]', prev):
                break
            if 'श्रीश्री भावना सार' in prev or 'अथ ' in prev[:10] or prev.startswith('#'):
                break
            # Check if it already has a verse number (would be different verse)
            has_own_num = False
            for pat in verse_num_patterns:
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

print(f"Extracted {len(bss_verses)} verse blocks from BSS.txt")
for sec in sorted(bss_line_ranges.keys()):
    nums = [v[1] for v in bss_verses.keys() if v[0] == sec]
    if nums:
        print(f"  Section {sec}: {len(nums)} verses (range {min(nums)}-{max(nums)})")

# Check specific missing verses
target_nums = {428, 429, 439, 529, 539, 549, 639, 649, 659, 749, 759, 769,
               859, 869, 879, 966, 967, 968, 969, 970, 971, 972, 973, 974,
               975, 976, 977, 978, 979, 980, 981, 982, 983, 984, 985, 986,
               987, 988, 989, 990, 1079, 1089, 1090, 1091, 1092, 1093, 1094,
               1095, 1096, 1097, 1098, 1099, 1189, 1190, 1191, 1192, 1193,
               1194, 1195, 1196, 1197, 1198, 1199, 1294, 1295, 1296, 1297,
               1298, 1299, 1309}

found_count = 0
for num in sorted(target_nums):
    if (4, num) in bss_verses:
        found_count += 1
    else:
        print(f"  Still missing: 4.{num}")

for sec, nums_list in [(2, [309, 384]), (3, [394]), (8, [297, 298])]:
    for num in nums_list:
        if (sec, num) in bss_verses:
            found_count += 1
        else:
            print(f"  Still missing: {sec}.{num}")

print(f"\nFound {found_count}/75 target verses")

# Now update DB
conn = sqlite3.connect(db)
c = conn.cursor()
c.execute("""SELECT id, ref_display FROM verses 
    WHERE sanskrit_text IS NULL OR sanskrit_text = '' ORDER BY ref_display""")
missing = c.fetchall()

updated = 0
for vid, ref in missing:
    parts = ref.split('.')
    main_sec = int(parts[0])
    verse_num = int(parts[1])
    key = (main_sec, verse_num)
    if key in bss_verses:
        c.execute("UPDATE verses SET sanskrit_text = ? WHERE id = ?", (bss_verses[key], vid))
        updated += 1

conn.commit()
print(f"Updated {updated} verses")

c.execute("SELECT COUNT(*) FROM verses WHERE sanskrit_text IS NOT NULL AND sanskrit_text != ''")
after = c.fetchone()[0]
print(f"Sanskrit coverage: {after}/3066 ({100*after/3066:.1f}%)")

c.execute("SELECT COUNT(*) FROM verses WHERE sanskrit_text IS NULL OR sanskrit_text = ''")
remaining = c.fetchone()[0]
print(f"Still missing: {remaining}")

if remaining > 0:
    c.execute("""SELECT ref_display FROM verses 
        WHERE sanskrit_text IS NULL OR sanskrit_text = '' ORDER BY ref_display""")
    for (ref,) in c.fetchall():
        print(f"  {ref}")

conn.close()
