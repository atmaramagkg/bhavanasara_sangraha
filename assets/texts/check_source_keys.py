import sqlite3

# Check source DBs for these translation keys
missing_keys = [
    'book.bhakti-rasamrta-sesa.author', 'book.bhakti-rasamrta-sesa.title',
    'book.dana-keli-cintamani.author', 'book.dana-keli-cintamani.title',
    'book.madhu-kelivalli.author', 'book.madhu-kelivalli.title',
    'book.stavamrta-lahari.author', 'book.stavamrta-lahari.title',
    'section.madhyahna_10.2.title', 'section.madhyahna_10.3.title',
    'section.madhyahna_3.3.title', 'section.madhyahna_4.2.title',
    'section.madhyahna_4.3.title', 'section.madhyahna_7.3.title',
    'section.madhyahna_9.2.title', 'section.madhyahna_9.3.title',
    'section.nishanta_1.5.title', 'section.nishanta_1.6.title',
    'section.nishanta_1.7.title', 'section.nishanta_2.5.title',
    'section.nishanta_2.6.title', 'section.nishanta_2.7.title',
    'section.nishanta_3.3.title', 'section.nishanta_3.4.title',
    'section.nishanta_3.5.title', 'section.nishanta_3.6.title',
    'section.pratah_2.2.title', 'section.pratah_2.3.title',
    'section.pratah_2.4.title', 'section.pratah_2.5.title',
]

for dbname, lang in [('Bhavanasara-Sangraha_En', 'EN'), ('Bhavanasara-Sangraha_Ru', 'RU')]:
    path = rf'C:\Users\austr\bss\assets\db\{dbname}.sqlite'
    try:
        conn = sqlite3.connect(path)
        c = conn.cursor()
        # Check what table structure
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in c.fetchall()]
        print(f"\n{lang} DB tables: {tables}")
        
        # Try translations or similar table
        for t in tables:
            c.execute(f"PRAGMA table_info({t})")
            cols = [r[1] for r in c.fetchall()]
            if 'translation_key' in cols or 'key' in cols:
                key_col = 'translation_key' if 'translation_key' in cols else 'key'
                c.execute(f"SELECT * FROM {t} WHERE {key_col} IN ({','.join(['?']*len(missing_keys))})", missing_keys)
                rows = c.fetchall()
                print(f"  {lang} table '{t}': found {len(rows)} of {len(missing_keys)} missing keys")
                for r in rows[:5]:
                    print(f"    {r}")
        
        # Also try to see what keys exist
        for t in tables:
            c.execute(f"PRAGMA table_info({t})")
            cols = [r[1] for r in c.fetchall()]
            if 'translation_key' in cols or 'key' in cols:
                key_col = 'translation_key' if 'translation_key' in cols else 'key'
                c.execute(f"SELECT DISTINCT {key_col} FROM {t} WHERE {key_col} LIKE 'book.%' OR {key_col} LIKE 'section.%'")
                keys = [r[0] for r in c.fetchall()]
                if keys:
                    print(f"  {lang} has {len(keys)} book/section keys:")
                    for k in keys:
                        print(f"    {k}")
        
        conn.close()
    except Exception as e:
        print(f"  Error: {e}")
