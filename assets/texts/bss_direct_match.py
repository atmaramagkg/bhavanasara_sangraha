import re, sqlite3

bss_file = r'C:\Users\austr\bss\assets\texts\BSS.txt'
db = r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha.sqlite'

with open(bss_file, 'r', encoding='utf-8') as f:
    bss_lines = f.readlines()

# BSS.txt section boundaries (from analysis)
bss_line_ranges = {1: (460, 2315), 2: (2315, 7196), 3: (7196, 10234), 4: (10234, 23208),
                   5: (23208, 24389), 6: (24389, 25196), 7: (25196, 27236), 8: (27236, 30893)}

# Extract ALL verse blocks from BSS.txt with their verse numbers
dev_to_int = {'०':0,'१':1,'२':2,'३':3,'४':4,'५':5,'६':6,'७':7,'८':8,'९':9}
def dev_to_num(s):
    r = 0
    for c in s:
        if c in dev_to_int: r = r*10+dev_to_int[c]
        else: return None
    return r

# Build a map of verse_number -> (main_section, sanskrit_text) from BSS.txt
# We know the section boundaries, so we know which section each line belongs to
bss_verses = {}  # (main_section, verse_num) -> text

for main_sec, (start, end) in bss_line_ranges.items():
    section_lines = bss_lines[start:end]
    
    # Collect Sanskrit blocks: lines ending with ।।number।।
    current_block = []
    for i, line in enumerate(section_lines):
        stripped = line.strip()
        
        # Check for verse number at end of line
        m = re.search(r'([०-९]{1,4})\s*[।॥|]+\s*$', stripped)
        if m:
            vnum = dev_to_num(m.group(1))
            if vnum and 1 <= vnum <= 2000:
                # Collect the verse (current line + preceding Sanskrit lines)
                verse_lines = []
                for j in range(max(0, i-3), i+1):
                    verse_lines.append(section_lines[j].strip())
                verse_text = ' '.join(l for l in verse_lines if l)
                # Clean up
                verse_text = re.sub(r'\s*[।॥|]+\s*[०-९]+\s*[।॥|]+\s*', '', verse_text)
                verse_text = verse_text.strip()
                if verse_text and len(verse_text) > 10:
                    key = (main_sec, vnum)
                    if key not in bss_verses:
                        bss_verses[key] = verse_text

print(f"Total verse blocks from BSS.txt: {len(bss_verses)}")

# Show verse number ranges per section
for sec in sorted(bss_line_ranges.keys()):
    nums = [v[1] for v in bss_verses.keys() if v[0] == sec]
    if nums:
        print(f"  Section {sec}: verse numbers {min(nums)}-{max(nums)} ({len(nums)} unique)")

# Now get missing verses from DB
conn = sqlite3.connect(db)
c = conn.cursor()
c.execute("""SELECT id, ref_display, transliteration FROM verses 
    WHERE sanskrit_text IS NULL OR sanskrit_text = '' ORDER BY ref_display""")
missing = c.fetchall()
print(f"\nMissing: {len(missing)}")

# For each missing verse, try to find it in BSS.txt by:
# 1. Same main section + verse number in BSS
# 2. If not found, search by transliteration keywords
found_updates = []

for vid, ref, translit in missing:
    main_sec, verse_num = ref.split('.')
    main_sec = int(main_sec)
    verse_num = int(verse_num)
    
    # Try direct match: same section, same verse number
    key = (main_sec, verse_num)
    if key in bss_verses:
        found_updates.append((vid, bss_verses[key], ref, 'direct'))
        continue
    
    # The verse numbers don't match between DB and BSS.txt for high numbers
    # Need to search by transliteration
    if not translit:
        continue
    
    # Get meaningful words from transliteration (skip short/common words)
    skip_words = {'ca', 'na', 'sa', 'hi', 'tu', 'eva', 'api', 'atha', 'tatra', 'yathā', 'iva', 'tataḥ', 'khalu', 'sā', 'taṁ', 'tām', 'tasya', 'asya', 'tat', 'te', 'tā', 'ke', 'kim', 'kā', 'kaḥ', 'yad', 'yat', 'yaḥ', 'yā', 'ye', 'yāḥ', 'me', 'te', 'naḥ', 'vaḥ', 'mayā', 'tvayā'}
    words = [w for w in translit.split() if len(w) > 4 and w.lower() not in skip_words]
    
    if len(words) < 2:
        continue
    
    # Search BSS.txt section for matching Sanskrit text
    # Use first 3 meaningful words as search query
    search_words = words[:3]
    
    best_match = None
    best_score = 0
    
    sec_start, sec_end = bss_line_ranges.get(main_sec, (0, 0))
    section_text = ''.join(bss_lines[sec_start:sec_end])
    
    # Search for the verse by checking if Sanskrit words appear near each other
    # This is approximate - we'll check word overlap
    for (bss_sec, bss_vnum), bss_text in bss_verses.items():
        if bss_sec != main_sec:
            continue
        
        # Check word overlap with transliteration
        # Convert BSS Devanagari to rough transliteration comparison
        # Simple: check if first search word appears in BSS text
        # (This won't work well for Devanagari vs roman)
        
        # Better: use the fact that the BSS.txt Hindi commentary quotes verse numbers
        # and the verse text is in Devanagari
        # We need a different approach...
        pass

print(f"\nDirect matches: {len(found_updates)}")

# Apply direct matches
for vid, sk_text, ref, method in found_updates:
    c.execute("UPDATE verses SET sanskrit_text = ? WHERE id = ?", (sk_text, vid))

conn.commit()

c.execute("SELECT COUNT(*) FROM verses WHERE sanskrit_text IS NOT NULL AND sanskrit_text != ''")
after = c.fetchone()[0]
print(f"Sanskrit coverage: {after}/3066 ({100*after//3066}%)")

conn.close()
