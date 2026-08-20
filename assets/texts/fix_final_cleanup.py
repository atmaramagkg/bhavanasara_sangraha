import re, sqlite3

db = r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha.sqlite'
conn = sqlite3.connect(db)
c = conn.cursor()

c.execute("SELECT id, ref_display, sanskrit_text FROM verses WHERE sanskrit_text GLOB '[0-9]*'")
# This won't work for Devanagari digits - use LIKE approach
c.execute("SELECT id, ref_display, sanskrit_text FROM verses WHERE sanskrit_text IS NOT NULL AND sanskrit_text != ''")
all_rows = c.fetchall()

digit_rows = []
for vid, ref, text in all_rows:
    if text and text[0] in '\u0966\u0967\u0968\u0969\u096a\u096b\u096c\u096d\u096e\u096f':
        digit_rows.append((vid, ref, text))

print(f"Starting with Devanagari digits: {len(digit_rows)}")

for vid, ref, text in digit_rows:
    original = text
    # Pattern: 7,8121) or 10,8144) - comma-separated digits + close-paren
    text = re.sub(r'^[\u0966-\u096f,.\s]+\s*[)\u093d\u096d\u0964\u0965]', '', text)
    # Pattern: 5 (reference) - digit then bracketed reference
    text = re.sub(r'^[\u0966-\u096f]+\s*\([^)]*\)\s*[\u0964\u0965]?\s*', '', text)
    # Pattern: 4852 followed by Sanskrit - long number + close-paren or space
    text = re.sub(r'^[\u0966-\u096f]+\s*[\u093d\u096d\u0964\u0965]\s*', '', text)
    # Pattern: bare digits followed by space and Sanskrit
    text = re.sub(r'^[\u0966-\u096f]{3,}\s+', '', text)
    text = text.strip()
    if text != original:
        print(f"  {ref}: '{original[:50]}' -> '{text[:50]}'")
        c.execute("UPDATE verses SET sanskrit_text = ? WHERE id = ?", (text, vid))

conn.commit()

# Final verification
c.execute("SELECT COUNT(*) FROM verses WHERE sanskrit_text IS NOT NULL AND sanskrit_text != ''")
total = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM verses WHERE sanskrit_text IS NULL OR sanskrit_text = ''")
empty = c.fetchone()[0]
print(f"\nFinal: {total} with text, {empty} empty, {total + empty} total")

# Check for remaining issues
c.execute("SELECT ref_display, sanskrit_text FROM verses WHERE sanskrit_text IS NOT NULL AND sanskrit_text != ''")
remaining_issues = 0
for vid, ref, text in c.fetchall():
    if not text:
        continue
    # Starts with digit
    if text[0] in '\u0966\u0967\u0968\u0969\u096a\u096b\u096c\u096d\u096e\u096f':
        remaining_issues += 1
        print(f"  DIGIT: {ref}: {text[:80]}")
    # Starts with (
    elif text.startswith('('):
        remaining_issues += 1
        print(f"  PAREN: {ref}: {text[:80]}")
    # Starts with anusvara/visarga
    elif text[0] in '\u0902\u0903\u0901':
        remaining_issues += 1
        print(f"  MARK: {ref}: {text[:80]}")

print(f"\nRemaining issues: {remaining_issues}")
conn.close()
