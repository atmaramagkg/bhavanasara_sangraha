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

def num_to_dev(num):
    return ''.join(chr(0x0966 + int(d)) for d in str(num))

# Extract ALL verse positions (line numbers + verse numbers) from BSS.txt per section
verse_positions = {}  # (main_sec, verse_num) -> line_number

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

print(f"Total verse positions found: {len(verse_positions)}")

# For each missing verse, find the gap between surrounding verses
conn = sqlite3.connect(db)
c = conn.cursor()
c.execute("SELECT id, ref_display, transliteration FROM verses WHERE sanskrit_text IS NULL OR sanskrit_text = '' ORDER BY ref_display")
missing = c.fetchall()

found_updates = []

for vid, ref, translit in missing:
    parts = ref.split('.')
    main_sec = int(parts[0])
    verse_num = int(parts[1])
    
    # Find the verse position just before and just after this missing verse
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
        print(f"  CANNOT GAP: {ref} (before={before}, after={after})")
        continue
    
    # Extract text between before verse and after verse
    before_line = before[1]
    after_line = after[1]
    
    # The text between these lines should contain the missing verse(s)
    gap_text = ' '.join(bss_lines[j].strip() for j in range(before_line + 1, after_line) if bss_lines[j].strip())
    
    # Check how many verses are in this gap
    # Look for verse number markers in Hindi commentary: (number)
    commentary_nums = []
    for m in re.finditer(r'\(([०-९]{1,4})\)', gap_text):
        cn = dev_to_num(m.group(1))
        if cn:
            commentary_nums.append(cn)
    
    # Also count Sanskrit-looking lines (lines with dandas that aren't commentary)
    sk_lines = []
    for j in range(before_line + 1, after_line):
        line = bss_lines[j].strip()
        if not line:
            continue
        # Sanskrit verse lines: contain dandas and don't start with (
        if line.startswith('(') or re.match(r'^\(\s*[०-९]', line):
            continue
        if '।' in line or '॥' in line:
            sk_lines.append((j, line))
    
    # Show the gap for debugging
    if verse_num in [429, 966, 967, 1079, 1089]:
        print(f"\n=== GAP for {ref} (between {before[0]}@L{before_line} and {after[0]}@L{after_line}) ===")
        print(f"  Commentary nums found: {commentary_nums}")
        print(f"  Sanskrit lines: {len(sk_lines)}")
        for j, line in sk_lines:
            print(f"    [{j}] {line[:120]}")
        print(f"  Gap text preview: {gap_text[:300]}")
    
    # If there's exactly 1 Sanskrit block in the gap, it's our missing verse
    if len(sk_lines) >= 1:
        verse_text = ' '.join(line for _, line in sk_lines)
        verse_text = re.sub(r'\s*[।॥|]+\s*[०-९]+\s*[।॥|]+\s*', '', verse_text)
        verse_text = re.sub(r'\s*[।॥|]+\s*$', '', verse_text).strip()
        if verse_text and len(verse_text) > 10:
            found_updates.append((vid, verse_text, ref))

print(f"\nFound {len(found_updates)}/{len(missing)} missing verses by gap extraction")

for vid, sk_text, ref in found_updates:
    print(f"  {ref}: {sk_text[:80]}...")
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
