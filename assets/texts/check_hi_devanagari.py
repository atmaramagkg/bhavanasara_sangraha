import sqlite3

hi_db = r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha_Hi.sqlite'
conn = sqlite3.connect(hi_db)
c = conn.cursor()

# Check if original_text_devanagari is Sanskrit or Hindi
print('Samples of original_text_devanagari:')
for row in c.execute("""SELECT chapter, verse_start, ref_display, 
    SUBSTR(original_text_devanagari, 1, 100) as dev 
    FROM verses WHERE chapter = '1' AND verse_start = '5' LIMIT 5"""):
    print(f'  ch={row[0]} v={row[1]} ref={row[2]}: {row[3]}...')

# How many entries per chapter (1-8) with unique verse_start?
c.execute("""SELECT chapter, COUNT(DISTINCT verse_start) FROM verses 
    WHERE CAST(chapter AS INTEGER) BETWEEN 1 AND 8 
    GROUP BY chapter ORDER BY CAST(chapter AS INTEGER)""")
print('\nDistinct verse_starts per chapter:')
for row in c.fetchall():
    print(f'  ch {row[0]}: {row[1]} unique verse_starts')

# Check for duplicates (same chapter + verse_start)
c.execute("""SELECT chapter, verse_start, COUNT(*) FROM verses 
    WHERE CAST(chapter AS INTEGER) BETWEEN 1 AND 8 
    GROUP BY chapter, verse_start HAVING COUNT(*) > 1 LIMIT 10""")
print('\nDuplicate chapter+verse_start:')
for row in c.fetchall():
    print(f'  ch {row[0]}, v {row[1]}: {row[2]} entries')

# Also check source EN/RU DBs for Devanagari in the sections that are missing
en_db = r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha_En.sqlite'
conn2 = sqlite3.connect(en_db)
c2 = conn2.cursor()

# Which sections have most Devanagari from EN DB?
c2.execute("""SELECT 
    CAST(SUBSTR(ref_display, 1, INSTR(ref_display, '.') - 1) AS INTEGER) as sec,
    COUNT(*) FROM verses 
    WHERE original_text_devanagari IS NOT NULL AND original_text_devanagari != ''
    AND ref_display LIKE '%.%'
    GROUP BY sec ORDER BY sec""")
print('\nEN DB Devanagari per section:')
for row in c2.fetchall():
    print(f'  Section {row[0]}: {row[1]} entries')

conn.close()
conn2.close()
