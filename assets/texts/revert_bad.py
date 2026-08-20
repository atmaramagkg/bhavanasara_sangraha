import sqlite3

db = r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha.sqlite'
conn = sqlite3.connect(db)
c = conn.cursor()

# These 70 verses were just written with bad bulk text - clear them
# (all the ones that were extracted with gap_extract.py)
c.execute("SELECT id, ref_display FROM verses WHERE sanskrit_text IS NOT NULL AND sanskrit_text != ''")
all_with_text = c.fetchall()

cleared = 0
for vid, ref in all_with_text:
    # Check if text looks like bulk gap text (multiple Sanskrit verse blocks concatenated)
    c.execute("SELECT sanskrit_text FROM verses WHERE id = ?", (vid,))
    text = c.fetchone()[0]
    
    # Heuristic: if text has more than 3 dandas, it's likely multi-verse bulk text
    danda_count = text.count('।') + text.count('॥')
    if danda_count > 4:
        # Also check: does it start with a Hindi word? (gap text often mixes Hindi)
        # Or does it have multiple verses worth of text (>500 chars)
        if len(text) > 500:
            c.execute("UPDATE verses SET sanskrit_text = NULL WHERE id = ?", (vid,))
            cleared += 1

conn.commit()

c.execute("SELECT COUNT(*) FROM verses WHERE sanskrit_text IS NOT NULL AND sanskrit_text != ''")
remaining = c.fetchone()[0]
print(f"Cleared {cleared} bad entries, {remaining} still have text")
conn.close()
