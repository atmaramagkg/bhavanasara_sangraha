import re, sqlite3

ocr_file = r'C:\Users\austr\bss\assets\texts\ocr_full.txt'
db = r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha.sqlite'

with open(ocr_file, 'r', encoding='utf-8') as f:
    ocr_text = f.read()

dev_to_int = {'०':0,'१':1,'२':2,'३':3,'४':4,'५':5,'६':6,'७':7,'८':8,'९':9}
def dev_to_num(s):
    r = 0
    for c in s:
        if c in dev_to_int: r = r*10+dev_to_int[c]
        else: return None
    return r

conn = sqlite3.connect(db)
c = conn.cursor()
c.execute("SELECT id, ref_display, transliteration FROM verses WHERE sanskrit_text IS NULL OR sanskrit_text = '' ORDER BY ref_display")
missing = c.fetchall()

print(f"Missing: {len(missing)}")

# OCR approach: cumulative verse numbering
# BSS.txt section boundaries in the original book
# OCR pages correspond to physical pages of the book
# Each OCR page has Devanagari text with verse numbers

# Parse OCR into pages
pages = {}
for m in re.finditer(r'===PAGE (PART\d+_\d+)\.png===\n(.*?)(?====PAGE |\Z)', ocr_text, re.DOTALL):
    pages[m.group(1)] = m.group(2)

# Extract all verse numbers from OCR pages (cumulative)
# OCR pages are in order: PART1_1 to PART1_350, PART2_1 to PART2_350
# So we can get cumulative verse numbering by scanning in page order
page_order = sorted(pages.keys())
print(f"OCR pages: {len(page_order)}")

# Build cumulative verse map from OCR
# Each page may have verse numbers. Track which main_section each belongs to.
# Section boundaries in BSS.txt: sec1=L460, sec2=L2315, sec3=L7196, sec4=L10234, sec5=L23208, sec6=L24389, sec7=L25196, sec8=L27236
# In the book, sections are: nishanta, pratah, purvahna, madhyahna, aparahna, sayam, pradosha, nakt

# For now, just search OCR for each missing verse's transliteration words
found = 0
for vid, ref, translit in missing:
    if not translit:
        continue
    
    parts = ref.split('.')
    main_sec = int(parts[0])
    verse_num = int(parts[1])
    
    # Search OCR for Sanskrit text matching this verse
    # Use the transliteration to find potential matches
    # Look for verse number markers in OCR
    dev_vnum = ''.join(chr(0x0966 + int(d)) for d in str(verse_num))
    
    # Search all OCR pages for this verse number
    for pname in page_order:
        page_text = pages[pname]
        if dev_vnum in page_text:
            # Found the verse number in OCR - extract surrounding Sanskrit text
            lines = page_text.split('\n')
            for i, line in enumerate(lines):
                if dev_vnum in line:
                    # Collect Sanskrit text around this line
                    verse_lines = []
                    for j in range(max(0, i-3), min(len(lines), i+1)):
                        l = lines[j].strip()
                        if l and ('।' in l or '॥' in l):
                            verse_lines.append(l)
                    if verse_lines:
                        verse_text = ' '.join(verse_lines)
                        verse_text = re.sub(r'\s*[।॥|]+\s*[०-९]+\s*[।॥|]+\s*', '', verse_text)
                        verse_text = re.sub(r'\s*[।॥|]+\s*$', '', verse_text).strip()
                        if verse_text and len(verse_text) > 10:
                            c.execute("UPDATE verses SET sanskrit_text = ? WHERE id = ?", (verse_text, vid))
                            found += 1
                            break
            break

print(f"OCR found: {found}")
conn.commit()

c.execute("SELECT COUNT(*) FROM verses WHERE sanskrit_text IS NOT NULL AND sanskrit_text != ''")
after = c.fetchone()[0]
print(f"Sanskrit coverage: {after}/3066 ({100*after/3066:.1f}%)")

c.execute("SELECT ref_display FROM verses WHERE sanskrit_text IS NULL OR sanskrit_text = '' ORDER BY ref_display")
remaining = [row[0] for row in c.fetchall()]
print(f"Still missing: {len(remaining)}")
for ref in remaining:
    print(f"  {ref}")

conn.close()
