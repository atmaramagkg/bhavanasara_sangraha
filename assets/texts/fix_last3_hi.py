import sqlite3
db = r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha.sqlite'
conn = sqlite3.connect(db)
c = conn.cursor()
c.execute("UPDATE translations SET hi = 'लीला स्मरण' WHERE translation_key = 'app.title'")
c.execute("UPDATE translations SET hi = 'श्रील कवि कर्णपूर' WHERE translation_key = 'book.alankara-kaustubha.author'")
c.execute("UPDATE translations SET hi = 'अलङ्कार-कौस्तुभ' WHERE translation_key = 'book.alankara-kaustubha.title'")
conn.commit()

c.execute("SELECT COUNT(*) FROM translations WHERE hi IS NOT NULL AND hi != ''")
hi_count = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM translations")
total = c.fetchone()[0]
print(f"HI coverage: {hi_count}/{total}")
conn.close()
