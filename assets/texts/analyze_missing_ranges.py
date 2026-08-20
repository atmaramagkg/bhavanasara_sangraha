import sqlite3

db = r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha.sqlite'
conn = sqlite3.connect(db)
c = conn.cursor()

# Get verses with and without sanskrit, with their ref_display
c.execute("SELECT id, section_id, sort_order, ref_display FROM verses ORDER BY section_id, sort_order")
all_verses = c.fetchall()

# Section to main period mapping (8 main periods mapped to 60 sub-periods)
# Sec1-30 = nishanta(1-30), pratah(31-42), purvahna(43-60), madhyahna(61-130), etc.
# But ref_display has format "X.Y" where X=main_section(1-8), Y=verse_within_section
# The main sections correspond to BSS.txt's 8 sangrahs

# BSS.txt has 8 sections with declared verse counts:
# Sec1: 185, Sec2: 200, Sec3: 366, Sec4: 396, Sec5: 399, Sec6: 455, Sec7: 370, Sec8: 268 (but translit has 298?)
# Total: 3003 declared, 3066 in transliteration

# Each PART image covers some pages of BSS.txt
# PART1 = first ~half, PART2 = second ~half

# Find which verse ranges are in each image by checking header info
# From test OCR: headers show verse numbers like "(२६)" "(८६)" etc.
# Let's map main section ranges to page numbers

# Actually, simpler: ref_display tells us main_section.verse_number
# Let's find the missing verses and their main sections

c.execute("""SELECT id, section_id, sort_order, ref_display 
    FROM verses 
    WHERE sanskrit_text IS NULL OR sanskrit_text = '' 
    ORDER BY ref_display""")
missing = c.fetchall()

# Extract main_section from ref_display (format "X.Y")
missing_by_main = {}
for v in missing:
    ref = v[3]  # e.g. "4.87"
    main_sec = int(ref.split('.')[0])
    verse_num = int(ref.split('.')[1])
    if main_sec not in missing_by_main:
        missing_by_main[main_sec] = []
    missing_by_main[main_sec].append((v[0], verse_num))

for ms in sorted(missing_by_main.keys()):
    verses = missing_by_main[ms]
    vnums = [v[1] for v in verses]
    print(f"Main section {ms}: {len(verses)} missing (verse #{min(vnums)}-{max(vnums)})")

# Now estimate which image pages these fall on
# Each page has ~5-8 verses. We need to figure out the mapping.
# From the BSS.txt line counts per section:
# Sec1: lines 460-2315 (1855 lines), 185 verses -> ~10 lines/verse -> ~185 pages at ~44 lines/page = ~42 pages
# But let's be more precise by using the OCR page headers

conn.close()
