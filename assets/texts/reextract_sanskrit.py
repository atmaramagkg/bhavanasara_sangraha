import re, sqlite3

bss_file = r'C:\Users\austr\bss\assets\texts\BSS.txt'
db = r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha.sqlite'

with open(bss_file, 'r', encoding='utf-8') as f:
    bss_lines = f.readlines()

dev_to_int = {'०':0,'१':1,'२':2,'३':3,'४':4,'५':5,'६':6,'७':7,'८':8,'९':9}
def dev_to_num(s):
    r = 0
    for c in s:
        if c in dev_to_int: r = r*10+dev_to_int[c]
        else: return None
    return r

# Step 1: Find section headers in BSS.txt
# Sections are: "अथ निशान्त लीला", "अथ प्रातः लीला", etc.
section_headers = []
section_names = ['निशान्त', 'प्रातः', 'पूर्वाह्न', 'मध्याह्न', 'अपराह्न', 'सायाह्न', 'प्रदोष', 'निशा']
for i, line in enumerate(bss_lines):
    for name in section_names:
        if name in line and 'लीला' in line:
            section_headers.append((i, name))
            break

print("BSS.txt section headers:")
for ln, name in section_headers:
    print(f"  Line {ln}: {name}")

# Step 2: Extract all verses with verse numbers from BSS.txt
# Each verse has: preceding Sanskrit lines + verse number marker
# Pattern: one or more lines of Devanagari + line ending with ।।number।। or similar
verses_found = {}  # (main_section_name, verse_num) -> sanskrit_text

# Determine which section each line belongs to
def get_section_for_line(line_num):
    current_section = None
    for ln, name in section_headers:
        if ln <= line_num:
            current_section = name
        else:
            break
    return current_section

# Map section names to main section numbers
section_name_to_num = {
    'निशान्त': 1,
    'प्रातः': 2,
    'पूर्वाह्न': 3,
    'मध्याह्न': 4,
    'अपराह्न': 5,
    'सायाह्न': 6,
    'प्रदोष': 7,
    'निशा': 8,
}

# Scan BSS.txt for verse number markers
verse_pattern = re.compile(r'([०-९]+)\s*[।।|।|॥]')
sans_lines = []

for i, line in enumerate(bss_lines):
    line_stripped = line.strip()
    if not line_stripped:
        if sans_lines:
            # Check if the last collected lines form a verse
            # (the verse number would be on the last line or previous lines)
            pass
        sans_lines = []
        continue
    
    m = verse_pattern.search(line_stripped)
    if m:
        verse_num = dev_to_num(m.group(1))
        if verse_num and 1 <= verse_num <= 2000:
            # Collect preceding Devanagari lines as Sanskrit
            sec_name = get_section_for_line(i)
            sec_num = section_name_to_num.get(sec_name)
            if sec_num:
                key = (sec_num, verse_num)
                # Collect Sanskrit from current line (the verse line itself)
                # And from preceding lines that look like Sanskrit
                verse_text_lines = []
                # Include current line up to the verse number marker
                verse_text_lines.append(line_stripped)
                
                # Look back for preceding verse lines
                for j in range(i-1, max(0, i-6), -1):
                    prev = bss_lines[j].strip()
                    if not prev:
                        break
                    # Skip Hindi commentary lines (contain common Hindi chars/patterns)
                    if re.search(r'[\(（]', prev) and re.search(r'[०-९]+\)', prev):
                        break  # This is a source reference line like (गोवि० १८६४)
                    if re.search(r'^[\(（]', prev):
                        break
                    if prev.startswith('//') or prev.startswith('#'):
                        break
                    verse_text_lines.insert(0, prev)
                
                # Clean up: take only the Sanskrit portion
                full_text = ' '.join(verse_text_lines)
                # Remove verse number markers for clean text
                clean = re.sub(r'\s*[।॥|]+\s*[०-९]+\s*[।॥|]+\s*', '', full_text)
                clean = clean.strip()
                if clean and len(clean) > 10:
                    verses_found[key] = clean

print(f"\nTotal verses extracted from BSS.txt: {len(verses_found)}")

# Step 3: Read current DB and find missing verses
conn = sqlite3.connect(db)
c = conn.cursor()
c.execute("""SELECT id, ref_display, sanskrit_text FROM verses ORDER BY id""")
all_verses = c.fetchall()

missing_before = 0
found_in_bss = 0
still_missing = 0
updates = []

for vid, ref, sk_text in all_verses:
    if sk_text and sk_text.strip():
        continue
    missing_before += 1
    
    main_sec, verse_num = ref.split('.')
    main_sec = int(main_sec)
    verse_num = int(verse_num)
    
    key = (main_sec, verse_num)
    if key in verses_found:
        found_in_bss += 1
        updates.append((vid, verses_found[key]))
    else:
        still_missing += 1

print(f"\nMissing before: {missing_before}")
print(f"Found in BSS.txt (new): {found_in_bss}")
print(f"Still missing: {still_missing}")

# Step 4: Apply updates
for vid, sk_text in updates:
    c.execute("UPDATE verses SET sanskrit_text = ? WHERE id = ?", (sk_text, vid))

conn.commit()

# Verify
c.execute("SELECT COUNT(*) FROM verses WHERE sanskrit_text IS NOT NULL AND sanskrit_text != ''")
after = c.fetchone()[0]
print(f"\nSanskrit coverage after: {after}/3066 ({100*after//3066}%)")

# Show remaining missing by section
c.execute("""SELECT section_id, COUNT(*) FROM verses 
    WHERE sanskrit_text IS NULL OR sanskrit_text = '' 
    GROUP BY section_id ORDER BY section_id""")
print("\nRemaining missing by section:")
for sec, cnt in c.fetchall():
    print(f"  Section {sec}: {cnt} missing")

# Show some samples of what was added
print("\nSamples of newly added Sanskrit:")
for vid, sk_text in updates[:5]:
    c.execute("SELECT ref_display FROM verses WHERE id = ?", (vid,))
    ref = c.fetchone()[0]
    print(f"  {ref}: {sk_text[:100]}...")

conn.close()
