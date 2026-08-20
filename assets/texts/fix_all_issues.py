import re, sqlite3

db = r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha.sqlite'
bss_file = r'C:\Users\austr\bss\assets\texts\BSS.txt'
ocr_file = r'C:\Users\austr\bss\assets\texts\ocr_full.txt'

with open(bss_file, 'r', encoding='utf-8') as f:
    bss_lines = f.readlines()
with open(ocr_file, 'r', encoding='utf-8') as f:
    ocr_text = f.read()

conn = sqlite3.connect(db)
c = conn.cursor()

# === 1. Fix 6 damaged verses (lost first word) ===
damaged_refs = ['1.15', '3.116', '3.342', '4.733', '4.1131', '8.209']
print("=== Fixing 6 damaged verses ===")
for ref in damaged_refs:
    c.execute("SELECT id, ref_display, sanskrit_text FROM verses WHERE ref_display = ?", (ref,))
    row = c.fetchone()
    if not row:
        continue
    vid, _, text = row
    print(f"  {ref}: current='{text[:60]}...'")
    
    # Search BSS.txt for the verse by looking at surrounding context
    # Use the transliteration to help identify
    c.execute("SELECT transliteration FROM verses WHERE ref_display = ?", (ref,))
    trow = c.fetchone()
    translit = trow[0] if trow else ''
    
    # The damaged text minus the missing prefix - search in BSS.txt
    damaged_part = text[:20]  # first 20 chars of current (damaged) text
    
    # Search BSS.txt for this pattern
    found = False
    for i, line in enumerate(bss_lines):
        if damaged_part[:10] in line:
            # Found potential match - collect full verse block
            # Go back to find the start
            start = i
            for j in range(i, max(i-5, 0), -1):
                l = bss_lines[j].strip()
                if not l or l.startswith('('):
                    start = j + 1
                    break
                start = j
            
            # Collect forward
            verse_lines = []
            for j in range(start, min(start + 5, len(bss_lines))):
                l = bss_lines[j].strip()
                if not l:
                    break
                verse_lines.append(l)
            
            full_text = ' '.join(verse_lines)
            full_text = re.sub(r'\s*[।॥|]+\s*[०-९]+\s*[।॥|]+\s*', '', full_text)
            full_text = re.sub(r'\s*[।॥|]+\s*$', '', full_text).strip()
            
            if full_text and len(full_text) > 20:
                print(f"  FOUND in BSS.txt: '{full_text[:80]}...'")
                c.execute("UPDATE verses SET sanskrit_text = ? WHERE id = ?", (full_text, vid))
                found = True
                break
    
    if not found:
        print(f"  NOT FOUND - trying OCR")
        # Search OCR
        for m in re.finditer(r'===PAGE (PART\d+_\d+)\.png===\n(.*?)(?====PAGE |\Z)', ocr_text, re.DOTALL):
            page = m.group(2)
            if damaged_part[:10] in page:
                idx = page.find(damaged_part[:10])
                start = max(0, idx - 200)
                snippet = page[start:idx+300]
                print(f"  OCR {m.group(1)}: ...{snippet[:120]}...")
                break

conn.commit()

# === 2. Clean remaining digit+close-paren references ===
print("\n=== Cleaning remaining reference patterns ===")
c.execute("SELECT id, ref_display, sanskrit_text FROM verses WHERE sanskrit_text GLOB '[०-९]*'")
rows = c.fetchall()
cleaned2 = 0
for vid, ref, text in rows:
    original = text
    # Remove leading digits (any length) + close paren
    text = re.sub(r'^[०-९]+\s*[)）}\।॥]\s*', '', text)
    # Remove leading (digits-range) patterns  
    text = re.sub(r'^[\(（]?\s*[०-९]+\.?[०-९]*\s*[-–]\s*[०-९]+\.?[०-९]*\s*[)）]?\s*', '', text)
    # Remove leading standalone digits followed by close paren
    text = re.sub(r'^[०-९\s.०-९]+\s*[)）}\।॥]\s*', '', text)
    text = text.strip()
    if text != original:
        cleaned2 += 1
        c.execute("UPDATE verses SET sanskrit_text = ? WHERE id = ?", (text, vid))
print(f"Cleaned: {cleaned2}")

# === 3. Clear Hindi text wrongly assigned as Sanskrit ===
print("\n=== Clearing Hindi text from sanskrit_text ===")
c.execute("SELECT id, ref_display, sanskrit_text FROM verses WHERE sanskrit_text IS NOT NULL AND sanskrit_text != ''")
all_rows = c.fetchall()
cleared = 0
hindi_patterns = [
    'है', 'हें', 'लिए', 'में', 'के साथ', 'की है', 'शोभा पा रहे', 'करने',
    'कर रहा', 'दिया', 'सोच रहा', 'अवस्था', 'देखो', 'क्यों', 'किसके',
    'लगीं', 'लगे', 'कहने लगी', 'कहने लगे', 'प्रकार', 'इसके पश्चात',
]
for vid, ref, text in all_rows:
    # Check if text is predominantly Hindi (Devanagari + Hindi grammar words)
    hindi_word_count = sum(1 for w in hindi_patterns if w in text)
    if hindi_word_count >= 3:
        # This is Hindi commentary, not Sanskrit verse
        print(f"  CLEARING {ref}: '{text[:80]}...'")
        c.execute("UPDATE verses SET sanskrit_text = '' WHERE id = ?", (vid,))
        cleared += 1
print(f"Cleared: {cleared}")

# Also check remaining issues
print("\n=== Final check ===")
c.execute("SELECT ref_display, sanskrit_text FROM verses WHERE sanskrit_text LIKE 'ं%' OR sanskrit_text LIKE 'ः%' OR sanskrit_text LIKE 'ँ%'")
bad = c.fetchall()
print(f"Bad starts: {len(bad)}")
for r in bad:
    print(f"  {r[0]}: {r[1][:80]}")

c.execute("SELECT ref_display FROM verses WHERE sanskrit_text GLOB '[०-९]*'")
remaining_digits = [r[0] for r in c.fetchall()]
print(f"Still starting with digits: {len(remaining_digits)}")
for r in remaining_digits[:5]:
    c.execute("SELECT sanskrit_text FROM verses WHERE ref_display = ?", (r,))
    t = c.fetchone()[0]
    print(f"  {r}: {t[:100]}")

c.execute("SELECT COUNT(*) FROM verses WHERE sanskrit_text IS NOT NULL AND sanskrit_text != ''")
print(f"Total with text: {c.fetchone()[0]}")

conn.commit()
conn.close()
