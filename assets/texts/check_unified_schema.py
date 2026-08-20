import sqlite3
conn = sqlite3.connect(r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha.sqlite')
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [r[0] for r in c.fetchall()]
print("Tables:", tables)
for t in tables:
    c.execute(f"PRAGMA table_info({t})")
    cols = [(r[1], r[2]) for r in c.fetchall()]
    c.execute(f"SELECT COUNT(*) FROM {t}")
    count = c.fetchone()[0]
    print(f"\n{t} ({count} rows):")
    for name, typ in cols:
        print(f"  {name} {typ}")
    c.execute(f"SELECT * FROM {t} LIMIT 3")
    for r in c.fetchall():
        print(f"  > {r}")
conn.close()
