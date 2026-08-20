import re, sqlite3

# The key insight: ref_display "X.Y" means main_section X, verse Y within that section
# BSS.txt uses cumulative verse numbers 1-3003 (or 1-3066 in transliteration)
# The OCR images also use cumulative numbers but they might differ

# Let's check: what does the transliteration file's verse numbering look like?
translit_file = r'C:\Users\austr\bss\assets\texts\sanskrit_transliteration.txt'
with open(translit_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find verse markers in transliteration
verse_nums = []
for line in lines:
    m = re.match(r'==(\d+)\.(\d+)==', line.strip())
    if m:
        verse_nums.append((int(m.group(1)), int(m.group(2))))

print(f"Transliteration: {len(verse_nums)} verses")
print(f"Main sections: {sorted(set(v[0] for v in verse_nums))}")
for ms in sorted(set(v[0] for v in verse_nums)):
    count = sum(1 for v in verse_nums if v[0] == ms)
    max_v = max(v[1] for v in verse_nums if v[0] == ms)
    print(f"  Section {ms}: {count} verses, max verse#={max_v}")

# Now check BSS.txt verse numbers per section
bss_file = r'C:\Users\austr\bss\assets\texts\BSS.txt'
with open(bss_file, 'r', encoding='utf-8') as f:
    bss_text = f.read()

# BSS.txt section boundaries (line numbers from earlier analysis)
# Sec1: L460, Sec2: L2315, Sec3: L7196, Sec4: L10234, Sec5: L23208, Sec6: L24389, Sec7: L25196, Sec8: L27236
bss_lines = bss_text.split('\n')
bss_sections = [
    (1, 460, 2315),
    (2, 2315, 7196),
    (3, 7196, 10234),
    (4, 10234, 23208),
    (5, 23208, 24389),
    (6, 24389, 25196),
    (7, 25196, 27236),
    (8, 27236, len(bss_lines)),
]

dev_to_int = {'०':0,'१':1,'२':2,'३':3,'४':4,'५':5,'६':6,'७':7,'८':8,'९':9}
def dev_to_num(s):
    r = 0
    for c in s:
        if c in dev_to_int: r = r*10+dev_to_int[c]
        else: return None
    return r

for sec_id, start, end in bss_sections:
    section_text = '\n'.join(bss_lines[start:end])
    nums = []
    for m in re.finditer(r'।।\s*([०-९]+)\s*।।', section_text):
        n = dev_to_num(m.group(1))
        if n: nums.append(n)
    if nums:
        print(f"\nBSS Sec{sec_id} (lines {start}-{end}): {len(nums)} verse numbers, range {min(nums)}-{max(nums)}")
    else:
        print(f"\nBSS Sec{sec_id} (lines {start}-{end}): 0 verse numbers found")

# Now check OCR verse numbers per section
ocr_file = r'C:\Users\austr\bss\assets\texts\ocr_full.txt'
with open(ocr_file, 'r', encoding='utf-8') as f:
    ocr_text = f.read()

# OCR pages don't map 1:1 to BSS.txt sections
# But we can try to find the section headers in OCR
print("\n\n=== OCR section headers ===")
for m in re.finditer(r'===PAGE (PART\d+_\d+)===\n(.*?)(?===PAGE|\Z)', ocr_text, re.DOTALL):
    page_name = m.group(1)
    page_content = m.group(2)[:200]
    # Look for section header
    for sh in re.finditer(r'(अथ\s+\S+\s+लीला)', page_content):
        print(f"  {page_name}: {sh.group(1)}")
        break
