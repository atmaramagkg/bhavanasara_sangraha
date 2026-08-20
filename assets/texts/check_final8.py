import re

bss_file = r'C:\Users\austr\bss\assets\texts\BSS.txt'
ocr_file = r'C:\Users\austr\bss\assets\texts\ocr_full.txt'

with open(bss_file, 'r', encoding='utf-8') as f:
    bss_lines = f.readlines()
with open(ocr_file, 'r', encoding='utf-8') as f:
    ocr_text = f.read()

dev_to_int = {'०':0,'१':1,'२':2,'३':3,'४':4,'५':5,'६':6,'७':7,'८':8,'९':9}
def num_to_dev(num):
    return ''.join(chr(0x0966 + int(d)) for d in str(num))

remaining = [(3, 394), (3, 49), (4, 1093), (4, 1199), (4, 1269), (4, 790), (8, 289), (8, 297)]

# BSS.txt line ranges per section
bss_line_ranges = {1: (460, 2315), 2: (2315, 7196), 3: (7196, 10234), 4: (10234, 23208),
                   5: (23208, 24389), 6: (24389, 25196), 7: (25196, 27236), 8: (27236, 30893)}

for sec, vnum in remaining:
    dev = num_to_dev(vnum)
    print(f"\n=== {sec}.{vnum} ({dev}) ===")
    
    # Search BSS.txt
    start, end = bss_line_ranges.get(sec, (0, 0))
    found_bss = False
    for i in range(start, min(end, len(bss_lines))):
        if dev in bss_lines[i]:
            print(f"  BSS.txt line {i}: {bss_lines[i].strip()[:120]}")
            found_bss = True
    if not found_bss:
        print(f"  BSS.txt: NOT FOUND")
    
    # Search OCR
    found_ocr = False
    for m in re.finditer(r'===PAGE (PART\d+_\d+)\.png===\n(.*?)(?====PAGE |\Z)', ocr_text, re.DOTALL):
        if dev in m.group(2):
            # Get context
            idx = m.group(2).find(dev)
            start = max(0, idx - 100)
            end = min(len(m.group(2)), idx + 100)
            print(f"  OCR {m.group(1)}: ...{m.group(2)[start:end]}...")
            found_ocr = True
            break
    if not found_ocr:
        print(f"  OCR: NOT FOUND")
    
    # Also check: does the section have verse numbers that skip?
    # E.g., section 3 has verses but 394 might be beyond its range
    sec_nums = set()
    for i in range(start, min(end, len(bss_lines))):
        for m in re.finditer(r'([०-९]{1,4})\s*[।॥|]+\s*$', bss_lines[i].strip()):
            n = 0
            for c in m.group(1):
                if c in dev_to_int: n = n*10+dev_to_int[c]
                else: n = None; break
            if n and 1 <= n <= 2000:
                sec_nums.add(n)
    if sec_nums:
        print(f"  Section {sec} verse range: {min(sec_nums)}-{max(sec_nums)} ({len(sec_nums)} unique)")
        if vnum > max(sec_nums):
            print(f"  -> Verse {vnum} is BEYOND section range (max={max(sec_nums)})")
        elif vnum not in sec_nums:
            print(f"  -> Verse {vnum} is a GAP in numbering")
