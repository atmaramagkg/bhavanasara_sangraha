import sqlite3, re

bss_file = r'C:\Users\austr\bss\assets\texts\BSS.txt'
db = r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha.sqlite'

with open(bss_file, 'r', encoding='utf-8') as f:
    bss_lines = f.readlines()

conn = sqlite3.connect(db)
c = conn.cursor()
c.execute("""SELECT ref_display, section_id FROM verses 
    WHERE sanskrit_text IS NULL OR sanskrit_text = '' ORDER BY ref_display""")
missing = c.fetchall()

# For section 4 verses (the bulk), look at the BSS.txt end of section
# Section 4 is lines 10234-23208
# The missing verses have high verse numbers (1079-1317)
# In BSS.txt, section 4 has 396 verses, so verse 1079 is way beyond

# Let's look at the last 200 lines of section 4 in BSS.txt
# to see what's there
print("=== BSS.txt section 4 last 100 lines (around where missing verses should be) ===")
sec4_lines = bss_lines[23100:23210]
for i, line in enumerate(sec4_lines):
    ln = 23100 + i
    stripped = line.strip()
    if stripped:
        print(f"[{ln}] {stripped[:120]}")

# Also check what's in BSS.txt around the end
print("\n\n=== BSS.txt lines around section boundary (4->5) ===")
for i in range(23180, 23230):
    if i < len(bss_lines):
        stripped = bss_lines[i].strip()
        if stripped:
            print(f"[{i}] {stripped[:120]}")

# Check the OCR for the same area
ocr_file = r'C:\Users\austr\bss\assets\texts\ocr_full.txt'
with open(ocr_file, 'r', encoding='utf-8') as f:
    ocr_text = f.read()

# Find OCR pages around the section 4->5 boundary
# Section 4 = madhyahna, section 5 = aparahna
# Look for aparahna header in OCR
for m in re.finditer(r'===PAGE (PART\d+_\d+)\.png===\n(.*?)(?====PAGE |\Z)', ocr_text, re.DOTALL):
    pname = m.group(1)
    pcontent = m.group(2)
    if 'अपराह्न' in pcontent or 'अपराह' in pcontent:
        print(f"\n=== OCR page {pname} (aparahna section start) ===")
        lines = pcontent.split('\n')
        for line in lines[:10]:
            print(f"  {line[:120]}")
        break

# Also look at OCR pages with high verse numbers (around 1000+)
print("\n=== OCR pages with verse numbers > 1000 ===")
dev_to_int = {'०':0,'१':1,'२':2,'३':3,'४':4,'५':5,'६':6,'७':7,'८':8,'९':9}
def dev_to_num(s):
    r = 0
    for c in s:
        if c in dev_to_int: r = r*10+dev_to_int[c]
        else: return None
    return r

for m in re.finditer(r'===PAGE (PART\d+_\d+)\.png===\n(.*?)(?====PAGE |\Z)', ocr_text, re.DOTALL):
    pname = m.group(1)
    pcontent = m.group(2)
    for vm in re.finditer(r'([०-९]{3,4})\s*[।॥|]+\s*$', pcontent, re.MULTILINE):
        vn = dev_to_num(vm.group(1))
        if vn and 1000 <= vn <= 1400:
            print(f"  {pname}: verse {vn}")
            # Show context
            idx = pcontent.find(vm.group(0))
            start = max(0, idx - 200)
            print(f"    ...{pcontent[start:idx+len(vm.group(0))][-150:]}...")
            break

conn.close()
