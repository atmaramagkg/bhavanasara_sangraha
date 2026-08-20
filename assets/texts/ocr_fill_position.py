import sqlite3, re, unicodedata

bss_file = r'C:\Users\austr\bss\assets\texts\BSS.txt'
db = r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha.sqlite'

with open(bss_file, 'r', encoding='utf-8') as f:
    bss_text = f.read()
    bss_lines = bss_text.split('\n')

conn = sqlite3.connect(db)
c = conn.cursor()
c.execute("""SELECT id, ref_display, transliteration, sanskrit_text FROM verses 
    WHERE sanskrit_text IS NULL OR sanskrit_text = '' ORDER BY ref_display""")
missing = c.fetchall()

print(f"Missing: {len(missing)}")

# For each missing verse, search BSS.txt using transliteration keywords
# The transliteration gives us Sanskrit words we can match against Devanagari

# Build a Devanagari-to-roman mapping for common words
# Instead, use a simpler approach: for each missing verse, 
# look at BSS.txt lines near where we'd expect it

# BSS.txt section boundaries by cumulative verse count from transliteration
bss_cumulative = {1: (1, 185), 2: (186, 385), 3: (386, 751), 4: (752, 1147),
                  5: (1148, 1546), 6: (1547, 2001), 7: (2002, 2371), 8: (2372, 2669)}

# BSS.txt line boundaries
bss_line_ranges = {1: (460, 2315), 2: (2315, 7196), 3: (7196, 10234), 4: (10234, 23208),
                   5: (23208, 24389), 6: (24389, 25196), 7: (25196, 27236), 8: (27236, 30893)}

# Verse count per BSS section
bss_sec_counts = {1: 185, 2: 200, 3: 366, 4: 396, 5: 399, 6: 455, 7: 370, 8: 268}

# For each missing verse, find approximate line in BSS.txt
found_updates = []

for vid, ref, translit, sk in missing:
    main_sec, verse_num = ref.split('.')
    main_sec = int(main_sec)
    verse_num = int(verse_num)
    
    if main_sec not in bss_line_ranges:
        continue
    
    bss_start, bss_end = bss_line_ranges[main_sec]
    sec_len = bss_end - bss_start
    total_verses = bss_sec_counts.get(main_sec, 185)
    
    # Estimate line position
    approx_line = bss_start + int((verse_num / total_verses) * sec_len)
    
    # Search in a window around the estimated position
    window = max(50, sec_len // 20)  # at least 50 lines
    search_start = max(bss_start, approx_line - window)
    search_end = min(bss_end, approx_line + window)
    
    # Collect all Sanskrit blocks in this window
    candidates = []
    current_block = []
    for i in range(search_start, search_end):
        line = bss_lines[i].strip()
        if not line:
            if current_block:
                block_text = ' '.join(current_block)
                if len(block_text) > 20 and re.search(r'[।॥]', block_text):
                    candidates.append((i, block_text))
                current_block = []
        else:
            # Skip Hindi commentary
            if re.match(r'^[\(]', line) or re.match(r'^\d+[\)\.]', line):
                continue
            if 'गोवि' in line or 'कृष्णा' in line[:5] or 'भा०' in line:
                continue
            current_block.append(line)
    
    if candidates:
        # We found Sanskrit blocks near the expected position
        # The verse_num-th block should be our verse
        if verse_num <= len(candidates):
            chosen = candidates[verse_num - 1][1]
        else:
            # Take the closest one
            idx = min(verse_num - 1, len(candidates) - 1)
            chosen = candidates[idx][1]
        
        found_updates.append((vid, chosen, ref))

print(f"Found by position search: {len(found_updates)}")

# Show samples
for vid, sk_text, ref in found_updates[:5]:
    print(f"  {ref}: {sk_text[:100]}...")

# Apply
for vid, sk_text, ref in found_updates:
    c.execute("UPDATE verses SET sanskrit_text = ? WHERE id = ?", (sk_text, vid))

conn.commit()

c.execute("SELECT COUNT(*) FROM verses WHERE sanskrit_text IS NOT NULL AND sanskrit_text != ''")
after = c.fetchone()[0]
print(f"\nSanskrit coverage: {after}/3066 ({100*after//3066}%)")

c.execute("""SELECT ref_display FROM verses 
    WHERE sanskrit_text IS NULL OR sanskrit_text = '' ORDER BY ref_display""")
remaining = c.fetchall()
print(f"Still missing: {len(remaining)}")
for r in remaining:
    print(f"  {r[0]}")

conn.close()
