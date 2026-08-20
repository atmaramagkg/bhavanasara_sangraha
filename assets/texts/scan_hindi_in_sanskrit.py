import re, sqlite3

db = r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha.sqlite'
conn = sqlite3.connect(db)
c = conn.cursor()

c.execute("SELECT ref_display, sanskrit_text FROM verses WHERE sanskrit_text IS NOT NULL AND sanskrit_text != ''")
rows = c.fetchall()
print(f"Scanning {len(rows)} verses for Hindi in sanskrit_text...\n")

# More comprehensive Hindi indicators
hindi_indicators = [
    # Hindi verbs/finals
    'हैं', 'है ', 'था ', 'थे ', 'गया', 'गयी', 'गई', 'किया', 'दिया',
    # Hindi postpositions
    'मेँ ', 'में ', 'से ', 'को ', 'पर ', 'के ', 'ने ', 'की ', 
    # Hindi verbs
    'करने', 'करते', 'करती', 'कर रहा', 'कर रही', 'कर रहे',
    'कहने', 'कहते', 'कहती', 'कहने लगे', 'कहने लगी',
    'लगे ', 'लगी ', 'लगीं',
    # Hindi descriptive words
    'शोभा', 'सुन्दर', 'सखियों', 'प्रियतम', 'प्रियतमा',
    'आनन्द', 'विलास', 'लीला',
    # Hindi structural
    'इसके पश्चात्', 'इस प्रकार', 'तदनन्तर', 'अतएव',
    'किन्तु', 'तथापि', 'अर्थात्',
    # Hindi sentence markers
    'ओर ', 'और ', 'किन्तु ', 'परन्तु ',
    # Hindi quotation style
    '"', '"',
    # OCR Hindi artifacts  
    'भय ', 'लज्जा', 'प्रेम', 'श्रृंगार',
]

# Sanskrit indicators (should NOT be in pure Sanskrit verse)
sanskrit_good = [
    'ः', 'ो', 'ौ', 'े', 'ै', 'ी', 'ू', 'ा', 'ि', 'उ', 'आ', 'इ',
    '्', 'ं', 'ँ',
]

hindi_candidates = []

for ref, text in rows:
    # Skip very short texts
    if len(text) < 20:
        continue
    
    hindi_score = 0
    matched_words = []
    
    for word in hindi_indicators:
        if word in text:
            hindi_score += 1
            matched_words.append(word)
    
    # Additional check: Hindi sentence structure
    # Sanskrit verses don't typically have patterns like "X का Y" or "X में Y"
    if re.search(r'[\u0900-\u097F]+ का [\u0900-\u097F]+', text):
        hindi_score += 2
        matched_words.append('का pattern')
    if re.search(r'[\u0900-\u097F]+ की [\u0900-\u097F]+', text):
        hindi_score += 2
        matched_words.append('की pattern')
    if re.search(r'[\u0900-\u097F]+ के [\u0900-\u097F]+', text):
        hindi_score += 2
        matched_words.append('के pattern')
    
    # Check for sentence-ending patterns typical of Hindi
    if re.search(r'है[।\s]', text):
        hindi_score += 3
        matched_words.append('है ending')
    if re.search(r'गय[ाी][।\s]', text):
        hindi_score += 3
        matched_words.append('गया ending')
    if re.search(r'दिय[ाी][।\s]', text):
        hindi_score += 3
        matched_words.append('दिया ending')
    
    # Sanskrit verses typically have specific patterns
    has_sanskrit_endings = bool(re.search(r'[ािीूेोैौंः]\s*[।॥]', text))
    has_hindi_endings = bool(re.search(r'है[।\s]|गय[ाी][।\s]|लिए[।\s]|करते[।\s]', text))
    
    if hindi_score >= 3:
        hindi_candidates.append((ref, text, hindi_score, matched_words))

# Sort by score descending
hindi_candidates.sort(key=lambda x: -x[2])

print(f"Found {len(hindi_candidates)} potential Hindi-in-Sanskrit cases:\n")
for ref, text, score, words in hindi_candidates:
    preview = text[:120].replace('\n', ' ')
    print(f"  {ref} (score={score}, words={words[:5]}): {preview}...")
    print()

conn.close()
