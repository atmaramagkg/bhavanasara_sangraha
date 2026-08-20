import sqlite3, re

db = r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha.sqlite'
conn = sqlite3.connect(db)
c = conn.cursor()

c.execute("""SELECT id, ref_display, transliteration, book_id FROM verses 
    WHERE sanskrit_text IS NULL OR sanskrit_text = '' ORDER BY ref_display""")
missing = c.fetchall()

print(f"Missing: {len(missing)}\n")

# Analyze patterns
# 1. Book distribution
book_ids = {}
for vid, ref, translit, book_id in missing:
    if book_id not in book_ids:
        book_ids[book_id] = []
    book_ids[book_id].append(ref)

# Get book names
c.execute("SELECT id, slug FROM books")
book_map = {row[0]: row[1] for row in c.fetchall()}

print("=== By book ===")
for bid, refs in sorted(book_ids.items(), key=lambda x: len(x[1]), reverse=True):
    name = book_map.get(bid, f"unknown({bid})")
    print(f"  {name}: {len(refs)} verses")

# 2. Section distribution
print("\n=== By main section ===")
sec_groups = {}
for vid, ref, translit, book_id in missing:
    ms = ref.split('.')[0]
    if ms not in sec_groups:
        sec_groups[ms] = []
    sec_groups[ms].append(ref)

for ms, refs in sorted(sec_groups.items()):
    print(f"  Section {ms}: {len(refs)} verses ({refs[0]}-{refs[-1]})")

# 3. Show transliteration text for first 10 missing verses
print("\n=== Sample transliterations ===")
for vid, ref, translit, book_id in missing[:10]:
    name = book_map.get(book_id, f"book_{book_id}")
    print(f"\n  {ref} ({name}):")
    if translit:
        lines = translit.split('\n')
        for line in lines[:4]:
            print(f"    {line[:100]}")

# 4. Check if these verses have counterparts in source DBs
en_db = r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha_En.sqlite'
hi_db = r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha_Hi.sqlite'
ru_db = r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha_Ru.sqlite'

for db_path, lang, table in [(en_db, 'EN', 'translations'), (hi_db, 'HI', 'translations'), (ru_db, 'RU', 'translations')]:
    try:
        c2 = sqlite3.connect(db_path)
        c2.execute(f"SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in c2.fetchall()]
        if table in tables:
            c2.execute(f"SELECT COUNT(*) FROM {table}")
            count = c2.fetchone()[0]
            print(f"\n  {lang} DB: {count} entries in {table}")
        c2.close()
    except Exception as e:
        print(f"\n  {lang} DB: error - {e}")

# 5. Check if any of these transliterations appear in the existing Sanskrit text of other verses
print("\n=== Checking transliteration uniqueness ===")
c.execute("SELECT id, ref_display, transliteration, sanskrit_text FROM verses WHERE transliteration IS NOT NULL AND transliteration != ''")
all_with_translit = c.fetchall()

# For each missing verse, check if its transliteration is similar to any existing verse
for vid, ref, translit, book_id in missing[:5]:
    if not translit:
        continue
    # Get first meaningful word
    words = [w for w in translit.split() if len(w) > 3]
    if not words:
        continue
    first_word = words[0]
    
    matches = 0
    for vid2, ref2, translit2, sk2 in all_with_translit:
        if vid2 == vid:
            continue
        if translit2 and first_word in translit2:
            matches += 1
    
    print(f"  {ref}: first word '{first_word}' found in {matches} other verses")

conn.close()
