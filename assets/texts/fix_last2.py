import sqlite3

db = r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha.sqlite'
conn = sqlite3.connect(db)
c = conn.cursor()

for ref in ['4.2', '7.173']:
    c.execute("SELECT id, sanskrit_text FROM verses WHERE ref_display = ?", (ref,))
    row = c.fetchone()
    if row:
        vid, text = row
        print(f"{ref}: {repr(text[:100])}")
        # Fix: remove leading } and digits
        import re
        text = re.sub(r'^[}\u093d\u096d0\u0966-\u096f\s#>]+', '', text)
        text = text.strip()
        # For 7.173, it's Hindi commentary - clear it
        if 'श्रीराधा' in text[:20] and ('भय' in text or 'करेगे' in text):
            text = ''
            print(f"  -> Cleared (Hindi commentary)")
        else:
            print(f"  -> Fixed: {text[:80]}")
        c.execute("UPDATE verses SET sanskrit_text = ? WHERE id = ?", (text, vid))

conn.commit()
conn.close()
