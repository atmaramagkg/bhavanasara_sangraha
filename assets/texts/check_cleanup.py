import re, sqlite3

db = r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha.sqlite'
conn = sqlite3.connect(db)
c = conn.cursor()

c.execute("SELECT id, ref_display, sanskrit_text FROM verses WHERE sanskrit_text IS NOT NULL AND sanskrit_text != ''")
rows = c.fetchall()

# Check for remaining bracket references at start
bracket_start = 0
digit_close_paren = 0
ref_fragments = []

for vid, ref, text in rows:
    # Still starts with (
    if text.startswith('(') or text.startswith('（'):
        bracket_start += 1
        if bracket_start <= 5:
            ref_fragments.append(f"  {ref}: {text[:120]}")
    # Starts with Devanagari digit followed by )
    elif re.match(r'^[०-९]+\s*[)।॥]', text):
        digit_close_paren += 1
        if digit_close_paren <= 5:
            ref_fragments.append(f"  {ref}: {text[:120]}")
    # Starts with ref fragment like "कृ० भा०"
    elif re.match(r'^(?:गोवि|कृ०|दः|कु०|का०|कृष्णा०)', text):
        ref_fragments.append(f"  {ref}: {text[:120]}")
        bracket_start += 1

print(f"Still starting with '(': {bracket_start}")
print(f"Starting with digit+close-paren: {digit_close_paren}")
print(f"\nSamples:")
for f in ref_fragments:
    print(f)

# Also check for verses where the text was over-trimmed (starts mid-word)
over_trimmed = 0
for vid, ref, text in rows:
    if text and text[0] in 'ंःँोौेैीीूूेाािउआइए':
        over_trimmed += 1
        if over_trimmed <= 5:
            print(f"  OVER-TRIMMED {ref}: {text[:120]}")
print(f"\nOver-trimmed (starts with dependent vowel/marks): {over_trimmed}")

conn.close()
