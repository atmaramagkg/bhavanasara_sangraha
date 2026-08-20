import sqlite3

en_db = r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha_En.sqlite'
conn = sqlite3.connect(en_db)
c = conn.cursor()

c.execute("SELECT ref_display, original_text FROM verses WHERE original_text IS NOT NULL AND original_text != '' LIMIT 5")
for row in c.fetchall():
    print(f'ref={row[0]}: {row[1][:120]}...')

c.execute("SELECT COUNT(*) FROM verses WHERE original_text IS NOT NULL AND original_text != ''")
print(f'\nTotal with original_text: {c.fetchone()[0]}')
conn.close()
