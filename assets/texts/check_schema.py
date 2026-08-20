import sqlite3

db = r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha.sqlite'
conn = sqlite3.connect(db)
c = conn.cursor()

# Schema
c.execute("PRAGMA table_info(verses)")
print("Verses columns:", [row[1] for row in c.fetchall()])

# Section 4 missing verses
c.execute("""SELECT id, ref_display, section_id FROM verses 
    WHERE (sanskrit_text IS NULL OR sanskrit_text = '') ORDER BY ref_display""")
missing = c.fetchall()
print(f"\nTotal missing: {len(missing)}")
for vid, ref, sid in missing:
    print(f"  id={vid} ref={ref} section_id={sid}")

# Section ranges in DB
c.execute("""SELECT section_id, MIN(ref_display), MAX(ref_display), COUNT(*) 
    FROM verses GROUP BY section_id ORDER BY section_id""")
for sid, mn, mx, cnt in c.fetchall():
    print(f"Section {sid}: {mn} to {mx} ({cnt} verses)")

# Check section_nodes
c.execute("PRAGMA table_info(section_nodes)")
print("\nSection_nodes columns:", [row[1] for row in c.fetchall()])

c.execute("SELECT * FROM section_nodes ORDER BY id")
for row in c.fetchall():
    print(f"  {row}")

conn.close()
