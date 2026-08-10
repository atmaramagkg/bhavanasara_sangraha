import sys, re, json, sqlite3
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')

EN = r"C:\Users\austr\bhavanasara_sangraha\assets\db\Bhavanasara-Sangraha_En.sqlite"
RU = r"C:\Users\austr\bhavanasara_sangraha\assets\db\Bhavanasara-Sangraha_Ru.sqlite"

def connect(p):
    c = sqlite3.connect(p)
    c.row_factory = sqlite3.Row
    return c

en, ru = connect(EN), connect(RU)

print("=" * 60)
print("A. SOURCE-COMPILATION vs EN DB (verse sweep, reuse all_recs_full.json)")
print("=" * 60)
recs = json.load(open(r'C:\Users\austr\AppData\Local\Temp\opencode\all_recs_full.json', encoding='utf-8'))
recs = [r for r in recs if r['slug'] and r['num']]
slug_to_id = {r[0]: r[1] for r in en.execute('SELECT slug, id FROM books')}

def intv(s):
    try:
        return int(s)
    except (TypeError, ValueError):
        return None

rows = en.execute('SELECT id, book_id, chapter, verse_start, verse_end, translation_text FROM verses').fetchall()
dbrows = []
for rid, bid, ch, vs, ve, txt in rows:
    a, b = intv(vs), intv(ve)
    if b is None:
        b = a
    if a is not None and b is not None and b < a:
        a, b = b, a
    dbrows.append({'id': rid, 'book_id': bid, 'chapter': ch, 'v1': a, 'v2': b, 'text': txt or ''})

def norm_en(s):
    s = re.sub(r'[^a-z0-9 ]', ' ', s.lower())
    return re.sub(r'\s+', ' ', s).strip()

def in_db(r):
    bid = slug_to_id.get(r['slug'])
    if bid is None:
        return 'NO_BOOK'
    for d in dbrows:
        if d['book_id'] != bid or d['chapter'] != r['chapter']:
            continue
        if d['v1'] is None or r['v1'] is None:
            continue
        if r['v2'] is not None:
            if not (d['v1'] <= r['v2'] and d['v2'] >= r['v1']):
                continue
        else:
            if not (d['v1'] <= r['v1'] <= d['v2']):
                continue
        return d['id']
    return None

def best_similar(r):
    bid = slug_to_id.get(r['slug'])
    if bid is None:
        return None, 0.0
    t = norm_en(r['translation'])
    words = set(t.split())
    if not t or not words:
        return None, 0.0
    best, best_score = None, 0.0
    for d in dbrows:
        if d['book_id'] != bid or not d['text']:
            continue
        dw = set(norm_en(d['text']).split())
        if not dw:
            continue
        score = 2.0 * len(words & dw) / (len(words) + len(dw))
        if score > best_score:
            best, best_score = d['id'], score
    return best, best_score

missing = []
for r in recs:
    did = in_db(r)
    if did is not None:
        continue
    sim_id, sim_score = best_similar(r)
    missing.append({**r, 'db_id': did, 'sim_id': sim_id, 'sim_score': round(sim_score, 3)})

known_dup = [m for m in missing if m['sim_score'] >= 0.45]
other = [m for m in missing if m['sim_score'] < 0.45]
print(f"source units with refs: {len(recs)}")
print(f"not found by chapter/verse: {len(missing)}")
print(f"  -> likely duplicates (similar translation): {len(known_dup)}")
print(f"  -> STILL POTENTIALLY MISSING (low similarity): {len(other)}")
for m in other:
    print("   ", m['section'][:6], m['unit'], m['slug'], m['ref'], round(m['sim_score'], 3))

print()
print("=" * 60)
print("B. EN DB INTERNAL CONSISTENCY")
print("=" * 60)
q_no_cit = en.execute("SELECT count(*) FROM quotes q LEFT JOIN citations c ON c.quote_id=q.id WHERE c.id IS NULL").fetchone()[0]
cit_bad_q = en.execute("SELECT count(*) FROM citations c LEFT JOIN quotes q ON q.id=c.quote_id WHERE q.id IS NULL").fetchone()[0]
cit_bad_v = en.execute("SELECT count(*) FROM citations c LEFT JOIN verses v ON v.id=c.source_verse_id WHERE c.source_verse_id IS NOT NULL AND v.id IS NULL").fetchone()[0]
print(f"quotes with NO citation: {q_no_cit}")
print(f"citations referencing missing quote: {cit_bad_q}")
print(f"citations referencing missing verse: {cit_bad_v}")
dup_qt = en.execute("SELECT count(*) FROM (SELECT quote_text FROM quotes GROUP BY quote_text HAVING count(*)>1)").fetchone()[0]
print(f"duplicate quote_texts (exact): {dup_qt}")
dup_cit = en.execute("SELECT count(*) FROM (SELECT quote_id, source_verse_id FROM citations GROUP BY quote_id, source_verse_id HAVING count(*)>1)").fetchone()[0]
print(f"duplicate (quote,verse) citations: {dup_cit}")
nq = en.execute("SELECT count(*) FROM quotes").fetchone()[0]
nc = en.execute("SELECT count(*) FROM citations").fetchone()[0]
print(f"quotes={nq} citations={nc}")

print()
print("=" * 60)
print("C. EN vs RU CONSISTENCY")
print("=" * 60)
for t in ['books', 'sections', 'period_nodes', 'verses', 'quotes', 'citations', 'dandas']:
    try:
        e = en.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
        r = ru.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
        mark = "" if e == r else "   <-- DIFF"
        print(f"{t:<14} En={e:<5} Ru={r:<5}{mark}")
    except Exception as ex:
        print(f"{t:<14} ERROR {ex}")

print("Ru verses missing vs En (same book+ref):")
everses = set((b, ch, vs) for b, ch, vs in en.execute(
    "SELECT b.slug, v.chapter, v.verse_start FROM verses v JOIN books b ON b.id=v.book_id").fetchall())
rverses = set((b, ch, vs) for b, ch, vs in ru.execute(
    "SELECT b.slug, v.chapter, v.verse_start FROM verses v JOIN books b ON b.id=v.book_id").fetchall())
en_only = everses - rverses
ru_only = rverses - everses
print(f"  verses in En only: {len(en_only)}")
for x in sorted(en_only):
    print("   ", x)
print(f"  verses in Ru only: {len(ru_only)}")
for x in sorted(ru_only)[:20]:
    print("   ", x)

print()
print("=" * 60)
print("D. BOOK COVERAGE")
print("=" * 60)
db_slugs = {r[0] for r in en.execute('SELECT slug FROM books')}
used_slugs = {r['slug'] for r in recs}
print(f"DB books: {len(db_slugs)}")
print(f"slugs cited by source units: {len(used_slugs)}")
unused_db = sorted(db_slugs - used_slugs)
print(f"DB books never cited by source units: {len(unused_db)}")
for s in unused_db:
    cnt = en.execute("SELECT count(*) FROM verses WHERE book_id=(SELECT id FROM books WHERE slug=?)", (s,)).fetchone()[0]
    print(f"   {s} ({cnt} verses)")

print()
print("D2. per-book verse counts (En) vs expected from source")
src_counts = Counter(r['slug'] for r in recs)
for slug in sorted(src_counts):
    cnt = en.execute("SELECT count(*) FROM verses WHERE book_id=(SELECT id FROM books WHERE slug=?)", (slug,)).fetchone()[0]
    exp = src_counts[slug]
    mark = "" if cnt >= exp else "   <-- En has FEWER rows than source units"
    print(f"   {slug:<34} source_units={exp:<4} en_verses={cnt:<4}{mark}")
