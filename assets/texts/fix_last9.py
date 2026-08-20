import re, sqlite3

db = r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha.sqlite'
conn = sqlite3.connect(db)
c = conn.cursor()

issues = [
    (4, 2), (4, 186), (4, 701), (4, 809), (4, 881),
    (4, 1022), (5, 9), (7, 173), (8, 18),
]

for sec, vnum in issues:
    ref = f"{sec}.{vnum}"
    c.execute("SELECT id, sanskrit_text FROM verses WHERE ref_display = ?", (ref,))
    row = c.fetchone()
    if not row:
        continue
    vid, text = row
    original = text
    
    # Remove opening bracket + any content up to closing bracket/brace/pipe
    text = re.sub(r'^[\(（]\s*[^)}\u093d\u096d\u0964\u0965]*[)}\u093d\u096d\u0964\u0965]\s*', '', text)
    # Remove leading digits with various separators
    text = re.sub(r'^[\u0966-\u096f\s.,#>]+\s*', '', text)
    # Remove leading digits.digits pattern like 11.836
    text = re.sub(r'^[\u0966-\u096f]+.[\u0966-\u096f]+\s+', '', text)
    text = text.strip()
    
    if text != original:
        print(f"  {ref}: '{original[:60]}' -> '{text[:60]}'")
        c.execute("UPDATE verses SET sanskrit_text = ? WHERE id = ?", (text, vid))
    else:
        print(f"  {ref}: UNCHANGED '{text[:80]}'")

conn.commit()

# Final check
issues_remaining = 0
c.execute("SELECT ref_display, sanskrit_text FROM verses WHERE sanskrit_text IS NOT NULL AND sanskrit_text != ''")
for ref, text in c.fetchall():
    if text[0] in '\u0966\u0967\u0968\u0969\u096a\u096b\u096c\u096d\u096e\u096f':
        issues_remaining += 1
        print(f"  DIGIT: {ref}: {text[:60]}")
    elif text.startswith('('):
        issues_remaining += 1
        print(f"  PAREN: {ref}: {text[:60]}")
    elif text[0] in '\u0902\u0903\u0901':
        issues_remaining += 1
        print(f"  MARK: {ref}: {text[:60]}")
print(f"Issues remaining: {issues_remaining}")

c.execute("SELECT COUNT(*) FROM verses WHERE sanskrit_text IS NOT NULL AND sanskrit_text != ''")
total = c.fetchone()[0]
print(f"Total with text: {total}/3066")

conn.close()
