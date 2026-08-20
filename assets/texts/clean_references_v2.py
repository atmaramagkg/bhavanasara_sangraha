import re, sqlite3

db = r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha.sqlite'
conn = sqlite3.connect(db)
c = conn.cursor()

c.execute("SELECT id, ref_display, sanskrit_text FROM verses WHERE sanskrit_text IS NOT NULL AND sanskrit_text != ''")
rows = c.fetchall()
print(f"Total: {len(rows)}")

cleaned = 0
damaged = 0

for vid, ref, text in rows:
    original = text

    # 1. Remove leading bracket reference: (गोवि० १५.८२८) etc
    text = re.sub(r'^\s*[\(（]\s*[^)]*[\)）]\s*[।॥]?\s*', '', text)

    # 2. Remove leading bare reference without opening paren: कृ० भा० १८१५) 
    text = re.sub(r'^\s*(?:गोवि(?:०)?|कृ०?\s*भा०?|दः\s*शा०?|कु०?\s*भा०?|का०?\s*भा०?|कृष्णा०?|लक्ष्मी|आ०|सा\.\s*च\.)\s*[०-९.,\s०-९]+\s*[)）}\।॥]?\s*', '', text)

    # 3. Remove leading number + close paren: १८१५) or २८२३)
    text = re.sub(r'^\s*[०-९]{2,4}\s*[)）}\।॥]\s*', '', text)

    # 4. Remove leading (number) patterns: (१०६६) or (१७०-७१)
    text = re.sub(r'^\s*[\(（]\s*[०-९\s,\-]+[)）]\s*', '', text)

    # 5. Remove leading number-range + paren: (१७०-७१) at start
    text = re.sub(r'^\s*[\(（]?\s*[०-९]+\s*[-–]\s*[०-९]+\s*[)）]?\s*', '', text)

    # Clean leading whitespace
    text = text.strip()

    if text != original:
        cleaned += 1
        # Check for damage: text should start with a proper Devanagari letter or known patterns
        if text and text[0] in 'ंःँ':
            damaged += 1
            print(f"  DAMAGED: {ref}: '{text[:60]}'")
        
        c.execute("UPDATE verses SET sanskrit_text = ? WHERE id = ?", (text, vid))

print(f"\nCleaned: {cleaned}")
print(f"Damaged (starts with anusvara/visarga): {damaged}")

conn.commit()

# Final check
c.execute("SELECT COUNT(*) FROM verses WHERE sanskrit_text IS NOT NULL AND sanskrit_text != ''")
print(f"Total with text: {c.fetchone()[0]}")

c.execute("SELECT COUNT(*) FROM verses WHERE sanskrit_text IS NOT NULL AND sanskrit_text != '' AND (sanskrit_text LIKE '(%' OR sanskrit_text LIKE '(%)")
print(f"Still starting with '(': {c.fetchone()[0]}")

c.execute("SELECT ref_display, sanskrit_text FROM verses WHERE sanskrit_text LIKE 'ं%' OR sanskrit_text LIKE 'ः%' OR sanskrit_text LIKE 'ँ%'")
for r in c.fetchall():
    print(f"  BAD START {r[0]}: {r[1][:80]}")

conn.close()
