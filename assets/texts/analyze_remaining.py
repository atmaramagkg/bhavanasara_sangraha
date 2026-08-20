import sqlite3

db = r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha.sqlite'
conn = sqlite3.connect(db)
c = conn.cursor()

# BSS.txt declares per section
bss_sec_counts = {1: 185, 2: 200, 3: 366, 4: 396, 5: 399, 6: 455, 7: 370, 8: 268}

c.execute("""SELECT ref_display FROM verses 
    WHERE sanskrit_text IS NULL OR sanskrit_text = '' ORDER BY ref_display""")
remaining = c.fetchall()

bss_coverable = 0
bss_impossible = 0
for (ref,) in remaining:
    main_sec, verse_num = ref.split('.')
    main_sec = int(main_sec)
    verse_num = int(verse_num)
    max_in_bss = bss_sec_counts.get(main_sec, 0)
    if verse_num > max_in_bss:
        bss_impossible += 1
    else:
        bss_coverable += 1

print(f"Remaining: {len(remaining)}")
print(f"  Beyond BSS.txt coverage: {bss_impossible}")
print(f"  Within BSS.txt coverage (but not found): {bss_coverable}")

# Show the coverable ones
c.execute("""SELECT id, ref_display FROM verses 
    WHERE sanskrit_text IS NULL OR sanskrit_text = '' ORDER BY ref_display""")
for vid, ref in c.fetchall():
    main_sec, verse_num = ref.split('.')
    main_sec = int(main_sec)
    verse_num = int(verse_num)
    max_in_bss = bss_sec_counts.get(main_sec, 0)
    if verse_num <= max_in_bss:
        print(f"  Coverable: {ref} (section {main_sec} has {max_in_bss} BSS verses)")

conn.close()
