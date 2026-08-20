import re, sqlite3

db = r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha.sqlite'
conn = sqlite3.connect(db)
c = conn.cursor()

c.execute("SELECT id, ref_display, sanskrit_text FROM verses WHERE sanskrit_text IS NOT NULL AND sanskrit_text != ''")
rows = c.fetchall()
print(f"Total verses with sanskrit_text: {len(rows)}")

# Find patterns: brackets at the beginning of sanskrit_text
# Common patterns: (गोवि० १५.८२८), (कृ० भा० १५.८५), (दः शा० ४८२३६), etc.
bracket_pattern = re.compile(r'^\s*[\(（]\s*[^)]*\)\s*[।॥]?\s*')
# Also: leading reference lines like "गोवि० १५.८२८)" at start
ref_pattern = re.compile(r'^\s*[\(（]?\s*(?:गोवि|कृ०|दः|कु०|का०|कृष्णा०|लक्ष्मी)\s*[\)।॥\s०-९.]+\s*')

# Show examples of texts with brackets
count = 0
for vid, ref, text in rows:
    if text.startswith('(') or text.startswith('（'):
        count += 1
        if count <= 10:
            print(f"  {ref}: {text[:120]}")
print(f"\nTexts starting with '(': {count}")

# Also check for lines that start with reference-like content
count2 = 0
for vid, ref, text in rows:
    first_line = text.split('\n')[0] if '\n' in text else text[:100]
    if ref_pattern.match(first_line):
        count2 += 1
        if count2 <= 10:
            print(f"  REF {ref}: {text[:120]}")
print(f"Texts with reference pattern: {count2}")

# Now clean: remove leading bracket references
cleaned = 0
samples = []
for vid, ref, text in rows:
    original = text
    
    # Remove leading bracket references
    # Pattern 1: entire text starts with (reference)
    text = re.sub(r'^\s*[\(（][^)]*[\)）]\s*[।॥]?\s*', '', text)
    
    # Pattern 2: first line is just a reference like "गोवि० १५.८२८)"
    text = re.sub(r'^\s*[\(（]?\s*(?:गोवि(?:०)?|कृ०?\s*भा०?|दः\s*शा०?|कु०?\s*भा०?|का०?\s*भा०?|कृष्णा०?|लक्ष्मी)\s*[）\)]*\s*[।॥]?\s*', '', text)
    
    # Pattern 3: leading number in brackets like (१०६६) or (७८५)
    text = re.sub(r'^\s*[\(（]\s*[०-९]+\s*[\)）]\s*', '', text)
    
    # Clean up leading whitespace
    text = text.strip()
    
    if text != original:
        cleaned += 1
        if len(samples) < 10:
            samples.append((ref, original[:100], text[:100]))
        c.execute("UPDATE verses SET sanskrit_text = ? WHERE id = ?", (text, vid))

print(f"\nCleaned {cleaned} verses")
print("\nSample changes:")
for ref, before, after in samples:
    print(f"  {ref}:")
    print(f"    BEFORE: {before}")
    print(f"    AFTER:  {after}")

conn.commit()
conn.close()
