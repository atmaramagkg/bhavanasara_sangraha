import re, sqlite3

db = r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha.sqlite'
conn = sqlite3.connect(db)
c = conn.cursor()

c.execute("SELECT ref_display, sanskrit_text FROM verses WHERE sanskrit_text IS NOT NULL AND sanskrit_text != ''")
rows = c.fetchall()

# Hindi-only indicators (NOT found in Sanskrit)
hindi_only = [
    r'है[।\s]',           # Hindi copula
    r'हैं[।\s]',
    r'था[।\s]',
    r'गय[ाी][।\s]',
    r'दिय[ाी][।\s]',
    r'करने',
    r'करते ह',
    r'करती ह',
    r'कर रहा',
    r'कर रही',
    r'कहने लगे',
    r'कहने लगी',
    r'इसके पश्चात',
    r'इस प्रकार',
    r'अतएव',
    r'अर्थात',
    r'सोच रहा',
    r'मानों',
    r'क्यों',
    r'आप ',
    r'तुम्हारे',
    r'तुम ',
    r'उनके',
    r'उनकी',
    r'लिये',
    r'वाले',
    r'लेकिन',
    r'ओर ',
    r'किसके',
    r'सकता',
    r'रही है',
    r'रहा है',
    r'रहे है',
    r'किया है',
    r'दिया था',
    r'करती हुई',
    r'करते हुए',
    r'हो गया',
    r'हो गयी',
    r'हो गई',
    r'कर लिया',
    r'देखकर',
    r'सुनकर',
    r'करके',
    r'लगीं',
]

hindi_entries = []
sanskrit_with_common = []

for ref, text in rows:
    if len(text) < 20:
        continue
    
    hindi_hits = []
    for pat in hindi_only:
        if re.search(pat, text):
            hindi_hits.append(pat)
    
    if len(hindi_hits) >= 3:
        # Check if it's genuinely Hindi or Sanskrit with common words
        # Genuine Hindi: has sentence structure like "X को Y", Hindi verbs
        # Sanskrit: compound words, visarga endings, specific meter
        
        has_hindi_verb = any(re.search(p, text) for p in [
            r'है[।\s]', r'हैं[।\s]', r'रहा है', r'रही है', r'रहे है',
            r'गय[ाी][।\s]', r'दिय[ाी][।\s]', r'किया है',
            r'करती हुई', r'करते हुए', r'कर रहा', r'कर रही',
        ])
        
        has_sanskrit_structure = bool(re.search(r'[ािीूेोैौंः्]\s*[।॥]', text))
        has_hindi_postpositions = bool(re.search(r'[\u0900-\u097F]+ को [\u0900-\u097F]+', text))
        
        if has_hindi_verb and has_hindi_postpositions:
            hindi_entries.append((ref, text, hindi_hits))
        elif has_hindi_verb and len(hindi_hits) >= 4:
            hindi_entries.append((ref, text, hindi_hits))
        else:
            sanskrit_with_common.append((ref, text, hindi_hits))

print(f"=== CONFIRMED HINDI in sanskrit_text: {len(hindi_entries)} ===\n")
for ref, text, hits in hindi_entries:
    preview = text[:120].replace('\n', ' ')
    print(f"  {ref} ({len(hits)} hits): {preview}...")
    print()

print(f"\n=== FALSE POSITIVES (Sanskrit with common words): {len(sanskrit_with_common)} ===")
print(f"  (Not Hindi - just contains common Devanagari sequences)\n")

# Summary
print(f"\nSUMMARY:")
print(f"  Total verses with sanskrit_text: {len(rows)}")
print(f"  Confirmed Hindi entries: {len(hindi_entries)}")
print(f"  False positives: {len(sanskrit_with_common)}")

conn.close()
