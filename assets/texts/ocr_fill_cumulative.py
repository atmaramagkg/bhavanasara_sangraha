import re, sqlite3

ocr_file = r'C:\Users\austr\bss\assets\texts\ocr_full.txt'
db = r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha.sqlite'

with open(ocr_file, 'r', encoding='utf-8') as f:
    ocr_text = f.read()

parts = re.split(r'===PAGE (PART\d+_\d+)\.png===\n?', ocr_text)
page_texts = {}
for i in range(1, len(parts), 2):
    page_texts[parts[i]] = parts[i+1] if i+1 < len(parts) else ''

dev_to_int = {'०':0,'१':1,'२':2,'३':3,'४':4,'५':5,'६':6,'७':7,'८':8,'९':9}
def dev_to_num(s):
    r = 0
    for c in s:
        if c in dev_to_int: r = r*10+dev_to_int[c]
        else: return None
    return r

# Build global verse number -> (page, verse_text) mapping
all_verses = {}  # verse_num -> [(page, text)]
for pname in sorted(page_texts.keys(), key=lambda p: (p.split('_')[0], int(p.split('_')[1]))):
    pcontent = page_texts[pname]
    lines = pcontent.split('\n')
    for i, line in enumerate(lines):
        m = re.search(r'([०-९]{1,4})\s*[।॥|]+\s*$', line)
        if m:
            vnum = dev_to_num(m.group(1))
            if vnum and 1 <= vnum <= 2000:
                verse_lines = []
                for j in range(max(0, i-3), i+1):
                    verse_lines.append(lines[j].strip())
                verse_text = '\n'.join(l for l in verse_lines if l)
                if verse_text and len(verse_text) > 10:
                    if vnum not in all_verses:
                        all_verses[vnum] = []
                    all_verses[vnum].append((pname, verse_text))

print(f"Unique verse numbers in OCR: {len(all_verses)}")

# Get missing verses
conn = sqlite3.connect(db)
c = conn.cursor()
c.execute("""SELECT id, ref_display FROM verses 
    WHERE sanskrit_text IS NULL OR sanskrit_text = '' ORDER BY ref_display""")
missing = c.fetchall()

# ref_display maps to BSS.txt cumulative verse numbering
# BSS.txt section boundaries (cumulative):
# Sec1: 1-185, Sec2: 186-385, Sec3: 386-751, Sec4: 752-1147, 
# Sec5: 1148-1546, Sec6: 1547-2001, Sec7: 2002-2371, Sec8: 2372-2669
bss_cumulative = {1: (1, 185), 2: (186, 385), 3: (386, 751), 4: (752, 1147),
                  5: (1148, 1546), 6: (1547, 2001), 7: (2002, 2371), 8: (2372, 2669)}

found_updates = []
still_missing = []
for vid, ref in missing:
    main_sec, verse_num_in_sec = ref.split('.')
    main_sec = int(main_sec)
    verse_num_in_sec = int(verse_num_in_sec)
    
    # Compute cumulative verse number
    if main_sec in bss_cumulative:
        cum_start = bss_cumulative[main_sec][0]
        cum_num = cum_start + verse_num_in_sec - 1
    else:
        cum_num = verse_num_in_sec  # fallback
    
    if cum_num in all_verses:
        # Take the best version (longest)
        candidates = all_verses[cum_num]
        best = max(candidates, key=lambda x: len(x[1]))
        found_updates.append((vid, best[1], ref, cum_num))
    else:
        still_missing.append((vid, ref, cum_num))

print(f"Missing: {len(missing)}")
print(f"Found by cumulative numbering: {len(found_updates)}")
print(f"Still missing: {len(still_missing)}")

# Show some found
for vid, sk_text, ref, cum in found_updates[:5]:
    print(f"  Found {ref} (cum={cum}): {sk_text[:80]}...")

# Show some still missing
for vid, ref, cum in still_missing[:10]:
    print(f"  Still missing {ref} (cum={cum})")

# Apply updates
for vid, sk_text, ref, cum in found_updates:
    c.execute("UPDATE verses SET sanskrit_text = ? WHERE id = ?", (sk_text, vid))

conn.commit()

c.execute("SELECT COUNT(*) FROM verses WHERE sanskrit_text IS NOT NULL AND sanskrit_text != ''")
after = c.fetchone()[0]
print(f"\nSanskrit coverage: {after}/3066 ({100*after//3066}%)")

c.execute("""SELECT ref_display FROM verses 
    WHERE sanskrit_text IS NULL OR sanskrit_text = '' ORDER BY ref_display""")
remaining = c.fetchall()
print(f"Final missing: {len(remaining)}")

conn.close()
