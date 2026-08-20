import sqlite3, re

bss_file = r'C:\Users\austr\bss\assets\texts\BSS.txt'
ocr_file = r'C:\Users\austr\bss\assets\texts\ocr_full.txt'
db = r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha.sqlite'

# BSS.txt main section line ranges
bss_lines_ranges = {
    1: (460, 2315), 2: (2315, 7196), 3: (7196, 10234), 4: (10234, 23208),
    5: (23208, 24389), 6: (24389, 25196), 7: (25196, 27236), 8: (27236, 30893)
}

with open(bss_file, 'r', encoding='utf-8') as f:
    bss_all = f.readlines()

conn = sqlite3.connect(db)
c = conn.cursor()
c.execute("""SELECT id, section_id, sort_order, ref_display, transliteration 
    FROM verses 
    WHERE sanskrit_text IS NULL OR sanskrit_text = '' 
    ORDER BY section_id, sort_order LIMIT 10""")
missing = c.fetchall()
conn.close()

# Get first missing verse: ref=1.119
for v in missing:
    ref = v[3]
    main_sec, verse_num = ref.split('.')
    main_sec = int(main_sec)
    verse_num = int(verse_num)
    
    print(f"\n=== Verse ID={v[0]} ref={ref} (main_sec={main_sec} verse={verse_num}) ===")
    print(f"Translit: {v[4][:150] if v[4] else 'None'}")
    
    # Check BSS.txt - we need to find the line for this verse
    # The existing add_sanskrit_text.py used positional matching
    # Let's look at BSS.txt lines that have Devanagari verse-like text
    if main_sec in bss_lines_ranges:
        start, end = bss_lines_ranges[main_sec]
        section_lines = bss_all[start:end]
        print(f"BSS.txt section {main_sec}: lines {start}-{end} ({end-start} lines)")
        
        # Search for the verse number in this section
        verse_str = str(verse_num)
        dev_digits = '0123456789'
        dev_to_int = {'0':'०','1':'१','2':'२','3':'३','4':'४','5':'५','6':'६','7':'७','8':'८','9':'९'}
        dev_num = ''.join(dev_to_int.get(c, c) for c in verse_str)
        
        # Search for verse number pattern
        found = False
        for i, line in enumerate(section_lines):
            if dev_num in line and ('।।' in line or '॥' in line):
                print(f"  BSS line {start+i}: {line.strip()[:120]}")
                # Show context
                for j in range(max(0,i-2), min(len(section_lines), i+3)):
                    print(f"    [{start+j}] {section_lines[j].strip()[:120]}")
                found = True
                break
        
        if not found:
            # Try partial match
            for i, line in enumerate(section_lines):
                if dev_num in line:
                    print(f"  BSS partial match line {start+i}: {line.strip()[:120]}")
                    for j in range(max(0,i-1), min(len(section_lines), i+2)):
                        print(f"    [{start+j}] {section_lines[j].strip()[:120]}")
                    found = True
                    break
            
            if not found:
                print(f"  NOT FOUND in BSS.txt section {main_sec}")

print("\n\n=== Checking OCR output for same verses ===")
with open(ocr_file, 'r', encoding='utf-8') as f:
    ocr_text = f.read()

# Split into pages
pages = {}
for m in re.finditer(r'===PAGE (PART\d+_\d+)===\n(.*?)(?===PAGE |\Z)', ocr_text, re.DOTALL):
    pages[m.group(1)] = m.group(2)

print(f"OCR pages: {len(pages)}")

# For the first missing verse, search all pages
for v in missing[:3]:
    ref = v[3]
    translit = v[4] if v[4] else ""
    # Use first few words of transliteration to search
    words = translit.split()[:5]
    search_term = ' '.join(words)
    print(f"\nVerse {ref} (ID={v[0]}), searching for: {search_term[:60]}")
    
    for pname, pcontent in sorted(pages.items()):
        # Simple word overlap check
        if len(words) > 2:
            matches = sum(1 for w in words if w.lower() in pcontent.lower())
            if matches >= 2:
                print(f"  Found in {pname} ({matches} word matches)")
                # Show context
                for line in pcontent.split('\n')[:5]:
                    print(f"    {line[:120]}")
                break
