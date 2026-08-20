import re

bss_file = r'C:\Users\austr\bss\assets\texts\BSS.txt'
with open(bss_file, 'r', encoding='utf-8') as f:
    bss_lines = f.readlines()

bss_line_ranges = {3: (7196, 10234), 4: (10234, 23208), 8: (27236, 30893)}

dev_to_int = {'०':0,'१':1,'२':2,'३':3,'४':4,'५':5,'६':6,'७':7,'८':8,'९':9}
def num_to_dev(num):
    return ''.join(chr(0x0966 + int(d)) for d in str(num))

def dev_to_num(s):
    r = 0
    for c in s:
        if c in dev_to_int: r = r*10+dev_to_int[c]
        else: return None
    return r

# For each remaining gap verse, find surrounding numbered verses and show what's between
gaps = [(3, 49), (4, 790), (4, 1093), (4, 1199), (4, 1269), (8, 289)]

for sec, vnum in gaps:
    start, end = bss_line_ranges[sec]
    
    # Find all verse number positions in this section
    verse_lines = {}
    for i in range(start, min(end, len(bss_lines))):
        stripped = bss_lines[i].strip()
        if not stripped:
            continue
        for m in re.finditer(r'([०-९]{1,4})\s*[।॥|]+\s*$', stripped):
            n = dev_to_num(m.group(1))
            if n and 1 <= n <= 2000:
                pre = stripped[:m.start()].rstrip()
                if not pre.endswith('(') and not stripped.startswith('('):
                    if n not in verse_lines:
                        verse_lines[n] = i
    
    # Find surrounding
    before_num = None
    after_num = None
    for n in sorted(verse_lines.keys()):
        if n < vnum:
            before_num = n
        elif n > vnum and after_num is None:
            after_num = n
    
    print(f"\n=== {sec}.{vnum} (before={before_num}, after={after_num}) ===")
    if before_num and after_num:
        bl = verse_lines[before_num]
        al = verse_lines[after_num]
        print(f"  Lines {bl} to {al} ({al-bl} lines between)")
        for j in range(bl, min(al+1, len(bss_lines))):
            line = bss_lines[j].strip()
            if line:
                print(f"    [{j}] {line[:130]}")
