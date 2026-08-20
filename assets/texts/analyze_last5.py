import re, sqlite3

db = r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha.sqlite'
ocr_file = r'C:\Users\austr\bss\assets\texts\ocr_full.txt'
bss_file = r'C:\Users\austr\bss\assets\texts\BSS.txt'

with open(ocr_file, 'r', encoding='utf-8') as f:
    ocr_text = f.read()
with open(bss_file, 'r', encoding='utf-8') as f:
    bss_lines = f.readlines()

conn = sqlite3.connect(db)
c = conn.cursor()

# For 4.1093: between verse 1088 and 1100, there are ~12 garbled verses
# Let's try to extract the right one by counting blocks between the correct surrounding verses
# After: 1100@L21157 (this is correctly numbered)
# Before: the verse just before 1088

# Actually, let me look for the verse with number 1088 in BSS.txt
# Line 21034-21035 shows verse १०८८
# Between 1088 and 1100 there should be verses 1089-1099

# The BSS.txt has garbled numbers: १०६०(should be १०९०), १०६१(should be १०९१)...
# We need the one that should be १०९३

# Let me find the correct positions
# 1088 is at L21035 (correctly numbered as १०८८)
# 1100 is at L21158 (correctly numbered as ११००)
# Between them are verses with garbled numbers

# Count the actual Sanskrit verse blocks between 1088 and 1100
# The garbled numbers tell us position: 1089 would be first after 1088

# From line 21035 (1088), find Sanskrit blocks before line 21158 (1100)
print("=== Scanning for Sanskrit blocks between 1088 and 1100 ===")
blocks = []
current_block = []
in_block = False
for j in range(21035, 21158):
    line = bss_lines[j].strip()
    if not line:
        if current_block:
            blocks.append((j - len(current_block), ' '.join(current_block)))
            current_block = []
        continue
    if line.startswith('('):
        if current_block:
            blocks.append((j - len(current_block), ' '.join(current_block)))
            current_block = []
        continue
    if 'श्रीश्री भावना' in line or ('अथ ' in line and 'लीला' in line):
        if current_block:
            blocks.append((j - len(current_block), ' '.join(current_block)))
            current_block = []
        continue
    # Check for verse marker (garbled or not)
    m = re.search(r'[०-९]{2,4}\s*।।', line)
    if m or '।' in line or '॥' in line or (current_block and len(line) > 10):
        current_block.append(line)
if current_block:
    blocks.append((j - len(current_block), ' '.join(current_block)))

print(f"Found {len(blocks)} blocks")
# Should be ~12 blocks for verses 1089-1100
# But 1088 and 1100 are already captured, so between them = 1089-1099 = 11 verses

# Let's see what we actually got
for i, (start_line, text) in enumerate(blocks[:15]):
    clean = re.sub(r'\s*[।॥|]+\s*[०-९]+\s*[।॥|]+\s*', '', text)
    clean = re.sub(r'\s*[।॥|]+\s*$', '', clean).strip()
    print(f"  Block {i} @L{start_line}: {clean[:120]}...")

# Now for 4.1199: between 1168 and 1200
print("\n=== Scanning for Sanskrit blocks between 1168 and 1200 ===")
# 1168@L22106-11, 1200@L22139-40
blocks2 = []
current_block = []
for j in range(22107, 22139):
    line = bss_lines[j].strip()
    if not line:
        if current_block:
            blocks2.append((j - len(current_block), ' '.join(current_block)))
            current_block = []
        continue
    if line.startswith('('):
        if current_block:
            blocks2.append((j - len(current_block), ' '.join(current_block)))
            current_block = []
        continue
    if 'श्रीश्री भावना' in line or ('अथ ' in line and 'लीला' in line):
        if current_block:
            blocks2.append((j - len(current_block), ' '.join(current_block)))
            current_block = []
        continue
    if '।' in line or '॥' in line or (current_block and len(line) > 10):
        current_block.append(line)
if current_block:
    blocks2.append((j - len(current_block), ' '.join(current_block)))

print(f"Found {len(blocks2)} blocks")
for i, (start_line, text) in enumerate(blocks2[:35]):
    clean = re.sub(r'\s*[।॥|]+\s*[०-९]+\s*[।॥|]+\s*', '', text)
    clean = re.sub(r'\s*[।॥|]+\s*$', '', clean).strip()
    print(f"  Block {i} @L{start_line}: {clean[:120]}...")

# Verses missing between 1168 and 1200:
c.execute("SELECT ref_display FROM verses WHERE (sanskrit_text IS NULL OR sanskrit_text = '') AND ref_display LIKE '4.%'")
missing_4 = sorted([row[0] for row in c.fetchall()], key=lambda x: int(x.split('.')[1]))
missing_in_gap = [r for r in missing_4 if 1168 < int(r.split('.')[1]) < 1200]
print(f"\nMissing between 1168 and 1200: {missing_in_gap}")

conn.close()
