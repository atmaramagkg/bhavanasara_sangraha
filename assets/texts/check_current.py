import sqlite3

db = r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha.sqlite'
conn = sqlite3.connect(db)
c = conn.cursor()

c.execute("SELECT COUNT(*) FROM verses WHERE sanskrit_text IS NOT NULL AND sanskrit_text != ''")
print(f"Current Sanskrit coverage: {c.fetchone()[0]}/3066")

c.execute("SELECT COUNT(*) FROM verses WHERE sanskrit_text IS NULL OR sanskrit_text = ''")
print(f"Missing: {c.fetchone()[0]}")

# Show what's missing now - is it the original 75 + extra cleared ones?
c.execute("SELECT ref_display FROM verses WHERE sanskrit_text IS NULL OR sanskrit_text = '' ORDER BY ref_display")
missing = [row[0] for row in c.fetchall()]

# Show distribution by main section
from collections import Counter
sec_counts = Counter(ref.split('.')[0] for ref in missing)
print(f"\nMissing by section: {dict(sec_counts)}")

# Show first/last few
print(f"\nFirst 20 missing: {missing[:20]}")
print(f"Last 20 missing: {missing[-20:]}")

# Count how many are in expected gaps vs unexpected
# The original 73 missing were: specific verse numbers
# New missing should be the reverted 735 - 70 = 665 extra ones
print(f"\nTotal missing: {len(missing)}")

conn.close()
