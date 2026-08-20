import sqlite3

db = r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha.sqlite'
conn = sqlite3.connect(db)
c = conn.cursor()

c.execute("SELECT id, translation_key, en, ru, hi FROM translations ORDER BY id")
rows = c.fetchall()

print(f"Total: {len(rows)} entries")
print(f"With HI: {sum(1 for r in rows if r[4])}")
print(f"Without HI: {sum(1 for r in rows if not r[4])}")
print()

# Show all entries needing translation
for row in rows:
    rid, key, en, ru, hi = row
    if not hi:
        print(f"id={rid} {key}")
        print(f"  EN: {en}")
        print(f"  RU: {ru}")

conn.close()
