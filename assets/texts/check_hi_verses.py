import sqlite3
db = r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha.sqlite'
conn = sqlite3.connect(db)
c = conn.cursor()
c.execute("SELECT COUNT(*) FROM verses WHERE translation_hi IS NOT NULL AND translation_hi != ''")
hi = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM verses")
total = c.fetchone()[0]
print(f'verses.translation_hi: {hi}/{total} ({hi*100//total}%)')
print()
for sec in range(1, 9):
    c.execute("SELECT COUNT(*), SUM(CASE WHEN translation_hi IS NOT NULL AND translation_hi != '' THEN 1 ELSE 0 END) FROM verses WHERE ref_display LIKE ? || '.%'", (str(sec),))
    r = c.fetchone()
    print(f'  Sec {sec}: {r[1]}/{r[0]}')
conn.close()
