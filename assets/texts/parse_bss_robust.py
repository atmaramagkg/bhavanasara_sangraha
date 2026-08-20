import re
import sqlite3

# 1. Expanded Abbreviation Mapping
abbr_map = {
    'गोवि०': 'श्रीगोविन्द लीलामृतम्', 'कृष्णा०': 'श्रीकृष्णाह्निक कौमुदी',
    'आ०': 'आनन्द वृन्दावन चम्पूः', 'उ०': 'उज्ज्वल नीलमणिः',
    'कु० भा०': 'श्रीकृष्ण भावनामृतम्', 'कृ० भा०': 'श्रीकृष्ण भावनामृतम्',
    'क० भा०': 'श्रीकृष्ण भावनामृतम्', 'भा०': 'श्रीमद्भागवतम्',
    'रा०': 'श्रीराधासुधानिधिः', 'प०': 'पद्यावली', 'ल': 'ललित माधव नाटकम्',
    'गी०': 'गीत गोविन्दम्', 'गोपा०': 'श्रीगोपाल चम्पूः', 'वि०': 'विदग्ध माधवनाटकम्',
    'वृन्दा०': 'वृन्दावन महिमामृतम्', 'मर०': 'भक्ति रसामृत सिन्धुः',
    'कर्णा०': 'श्रीकृष्ण कर्णामृतम्', 'भाग०': 'वृहद् भागवतामृतम्',
    'मधु': 'मधु केलिवल्ली', 'रति०': 'श्रीगोविन्द रतिमंजरी', 'क्र०': 'क्रम दीपिका',
    'लह०': 'स्तवामृत लहरी', 'गोपि०': 'गोपीचन्द्रिका', 'चन्द्रो०': 'चन्द्रोदय',
    'सा० च०': 'साहित्य चन्द्रिका', 'स्तं० स्वयं०': 'स्तोत्रमाला', 'अ०': 'अलंकार कौस्तुभ'
}

def devanagari_to_int(d_str):
    return int(re.sub(r'[\u0966-\u096F]', lambda x: str(ord(x.group()) - 2406), d_str))

def int_to_devanagari(num):
    devanagari_digits = "०१२३४५६७८९"
    return "".join(devanagari_digits[int(d)] for d in str(num))

def expand_ref(ref_str):
    match = re.search(r'([^\d,]+)\s*([\u0966-\u096F,]+)', ref_str)
    if match:
        abbr = match.group(1).strip()
        num_str = match.group(2).replace(',', '')
        try:
            num_int = devanagari_to_int(num_str)
            return f"{abbr_map.get(abbr, abbr)} {num_int}"
        except ValueError:
            return ref_str
    return ref_str

def format_sanskrit_text(raw_text, verse_num_int):
    """Formats the Sanskrit text into a clean 2-line verse with proper dandas."""
    text = raw_text.strip().replace('|', '।')
    text = re.sub(r'[।॥]+\s*[\u0966-\u096F0-9]+\s*[।॥]+\s*$', '', text).strip()
    text = re.sub(r'[।॥]+\s*$', '', text).strip()
    
    split_index = text.find('।')
    if split_index != -1:
        line1 = text[:split_index+1].strip()
        line2 = text[split_index+1:].strip()
        line2 = re.sub(r'^[।॥\s]+', '', line2).strip()
        line2 = re.sub(r'[।॥]+\s*[\u0966-\u096F0-9]+\s*[।॥]+\s*$', '', line2).strip()
        line2 = re.sub(r'[।॥]+\s*$', '', line2).strip()
        
        dev_num = int_to_devanagari(verse_num_int)
        return f"{line1}\n{line2}॥{dev_num}॥"
    else:
        dev_num = int_to_devanagari(verse_num_int)
        return f"{text}\n॥{dev_num}॥"

# 2. Read the text
with open('BSS.txt', 'r', encoding='utf-8') as f:
    text = f.read()

section_names = [
    "निशान्त लीला", "प्रातः लीला", "पूर्वाह्न लीला", "मध्याह्न लीला", 
    "अपराह्न लीला", "सायाहन लीला", "प्रदोष लीला", "नक्त लीला"
]

flexible_names = [
    r"निशान्त\s*लीला", r"प्रातः लीला", r"पूर्वाह[न्]?\s*लीला", r"मध्याह[न्]?\s*लीला",
    r"अपराह[न्]?\s*लीला", r"सायाह[न]?\s*लीला", r"प्रदोष\s*लीला", r"नक्त\s*लीला"
]

section_boundaries = []
for i, pattern in enumerate(flexible_names):
    matches = list(re.finditer(pattern, text))
    valid_matches = [m for m in matches if m.start() > 15000]
    if valid_matches:
        section_boundaries.append((valid_matches[0].start(), section_names[i]))

section_boundaries.sort(key=lambda x: x[0])
section_boundaries.append((len(text), "END"))

# 3. Setup SQLite Database
db_name = 'BSS_database.db'
# Delete existing DB to start fresh
import os
if os.path.exists(db_name):
    os.remove(db_name)

conn = sqlite3.connect(db_name)
cursor = conn.cursor()

# Create table
cursor.execute('''
    CREATE TABLE bss_verses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        distinctive_mark TEXT,
        main_section TEXT,
        subsection TEXT,
        verse_number INTEGER,
        sanskrit_text TEXT,
        hindi_translation TEXT,
        reference_expanded TEXT
    )
''')

rows_to_insert = []

# 4. Extract and Format Verses
for i in range(len(section_boundaries) - 1):
    start_pos, sec_name = section_boundaries[i]
    end_pos = section_boundaries[i+1][0]
    
    section_text = text[start_pos:end_pos]
    hindi_markers = list(re.finditer(r'\(\s*([\u0966-\u096F]+)\s*\)', section_text))
    
    for j, marker in enumerate(hindi_markers):
        verse_num_dev = marker.group(1)
        verse_num_int = devanagari_to_int(verse_num_dev)
        
        prev_end = hindi_markers[j-1].end() if j > 0 else 0
        current_start = marker.start()
        current_end = marker.end()
        next_start = hindi_markers[j+1].start() if j+1 < len(hindi_markers) else len(section_text)
        
        pre_text = section_text[prev_end:current_start].strip()
        hindi_text = section_text[current_end:next_start].strip()
        
        ref_match = re.search(r'\(\s*([^)]+)\s*\)', pre_text)
        sanskrit_raw = pre_text
        ref_expanded = ""
        
        if ref_match:
            ref_str = ref_match.group(1)
            ref_expanded = expand_ref(ref_str)
            sanskrit_raw = pre_text.replace(ref_match.group(0), "").strip()
        
        sanskrit_formatted = format_sanskrit_text(sanskrit_raw, verse_num_int)
        hindi_text = re.sub(r'\s+', ' ', hindi_text)
        
        if len(sanskrit_raw) > 10 or len(hindi_text) > 10:
            rows_to_insert.append((
                f"[{sec_name} - {verse_num_int}]",
                sec_name,
                "", # subsection
                verse_num_int,
                sanskrit_formatted,
                hindi_text,
                ref_expanded
            ))

# 5. Insert into Database
cursor.executemany('''
    INSERT INTO bss_verses (distinctive_mark, main_section, subsection, verse_number, sanskrit_text, hindi_translation, reference_expanded)
    VALUES (?, ?, ?, ?, ?, ?, ?)
''', rows_to_insert)

conn.commit()
conn.close()

print(f"✅ Successfully created SQLite database: {db_name}")
print(f"✅ Inserted {len(rows_to_insert)} verses with perfectly formatted 2-line Sanskrit text.")