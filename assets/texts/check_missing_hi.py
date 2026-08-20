import sqlite3
db = r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha.sqlite'
conn = sqlite3.connect(db)
c = conn.cursor()
c.execute("SELECT translation_key, en FROM translations WHERE hi IS NULL OR hi = ''")
rows = c.fetchall()
for row in rows:
    print(f"{row[0]}: {row[1]}")
print(f"\nTotal missing: {len(rows)}")
conn.close()
