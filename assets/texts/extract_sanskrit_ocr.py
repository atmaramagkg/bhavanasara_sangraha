import re

ocr_file = r'C:\Users\austr\bss\assets\texts\ocr_full.txt'

with open(ocr_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Split on page markers - they include .png
parts = re.split(r'===PAGE (PART\d+_\d+\.png)===\n', content)
# parts[0] = before first marker, then alternating name/content
page_data = {}
for i in range(1, len(parts), 2):
    name = parts[i].replace('.png','')
    page_data[name] = parts[i+1].strip()

print(f"Total pages: {len(page_data)}")

# Now extract verse numbers from each page
def extract_verses_from_text(text):
    """Find all verse numbers in text (Devanagari or Arabic numerals)."""
    # Devanagari digits to int
    dev_to_int = {'०':0,'१':1,'२':2,'३':3,'४':4,'५':5,'६':6,'७':7,'८':8,'९':9}
    
    def dev_to_num(s):
        result = 0
        for c in s:
            if c in dev_to_int:
                result = result * 10 + dev_to_int[c]
            else:
                return None
        return result
    
    verses = []
    lines = text.split('\n')
    for line in lines:
        # Match Devanagari verse numbers: ॥१२३।। or ।।१२३।। or ॥ १२३ ॥
        for m in re.finditer(r'[॥।]{1,2}\s*([०-९]+)\s*[॥।]{1,2}', line):
            num = dev_to_num(m.group(1))
            if num:
                verses.append(num)
        # Also Arabic numerals: ॥123।।
        for m in re.finditer(r'[॥।]{1,2}\s*(\d+)\s*[॥।]{1,2}', line):
            verses.append(int(m.group(1)))
    
    return verses

# Build a map: verse_number -> list of pages where it appears
verse_to_pages = {}
for pname, ptext in sorted(page_data.items()):
    verses = extract_verses_from_text(ptext)
    for v in verses:
        if v not in verse_to_pages:
            verse_to_pages[v] = []
        verse_to_pages[v].append(pname)

print(f"Total unique verse numbers found: {len(verse_to_pages)}")
print(f"Max verse number: {max(verse_to_pages.keys()) if verse_to_pages else 0}")

# Now read the missing verses
db = r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha.sqlite'
import sqlite3
conn = sqlite3.connect(db)
c = conn.cursor()
c.execute("""SELECT id, ref_display FROM verses 
    WHERE sanskrit_text IS NULL OR sanskrit_text = ''""")
missing = c.fetchall()

# ref_display format: "X.Y" where X=main_section(1-8), Y=verse_within_section
# But verse numbers in images are cumulative across the whole book
# We need to figure out the cumulative verse number from ref_display

# BSS.txt section verse counts (from analysis):
# Sec1: 185, Sec2: 200, Sec3: 366, Sec4: 396, Sec5: 399, Sec6: 455, Sec7: 370, Sec8: 268 (but transliteration has 298)
bss_counts = {1:185, 2:200, 3:366, 4:396, 5:399, 6:455, 7:370, 8:268}

# Compute cumulative offset for each section
offset = {1:0}
for i in range(2, 9):
    offset[i] = offset[i-1] + bss_counts[i-1]

print(f"\nSection offsets: {offset}")

# For each missing verse, compute cumulative number and check if found in images
found_count = 0
not_found_count = 0
for verse_id, ref in missing:
    main_sec, verse_num = ref.split('.')
    main_sec = int(main_sec)
    verse_num = int(verse_num)
    cum_num = offset.get(main_sec, 0) + verse_num
    
    if cum_num in verse_to_pages:
        found_count += 1
    else:
        not_found_count += 1

print(f"\nMissing verses: {len(missing)}")
print(f"Found in OCR pages: {found_count}")
print(f"NOT found in OCR pages: {not_found_count}")
