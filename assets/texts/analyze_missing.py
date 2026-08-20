import sqlite3

db = r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha.sqlite'
conn = sqlite3.connect(db)
c = conn.cursor()

# Show first/last 5 missing per section
c.execute("""SELECT ref_display FROM verses 
    WHERE sanskrit_text IS NULL OR sanskrit_text = '' 
    ORDER BY ref_display""")
missing = [row[0] for row in c.fetchall()]

from collections import defaultdict
by_sec = defaultdict(list)
for ref in missing:
    sec = int(ref.split('.')[0])
    vn = int(ref.split('.')[1])
    by_sec[sec].append(vn)

for sec in range(1, 9):
    if sec not in by_sec:
        continue
    nums = by_sec[sec]
    print(f'Section {sec}: {len(nums)} missing')
    if len(nums) <= 10:
        print(f'  All: {nums}')
    else:
        print(f'  First 5: {nums[:5]}')
        print(f'  Last 5: {nums[-5:]}')
    # Check if contiguous or scattered
    gaps = []
    for i in range(1, len(nums)):
        gaps.append(nums[i] - nums[i-1])
    max_gap = max(gaps) if gaps else 0
    print(f'  Max gap between missing: {max_gap}')

conn.close()
