import re

bss_file = r'C:\Users\austr\bss\assets\texts\BSS.txt'
with open(bss_file, 'r', encoding='utf-8') as f:
    bss_lines = f.readlines()

dev_to_int = {'०':0,'१':1,'२':2,'३':3,'४':4,'५':5,'६':6,'७':7,'८':8,'९':9}
def dev_to_num(s):
    r = 0
    for c in s:
        if c in dev_to_int: r = r*10+dev_to_int[c]
        else: return None
    return r

# Search BSS.txt section 4 (lines 10234-23208) for ALL Devanagari verse numbers
# Let's see what we actually have vs what we're missing
target_nums = {428, 429, 439, 529, 539, 549, 639, 649, 659, 749, 759, 769,
               859, 869, 879, 966, 967, 968, 969, 970, 971, 972, 973, 974,
               975, 976, 977, 978, 979, 980, 981, 982, 983, 984, 985, 986,
               987, 988, 989, 990, 1079, 1089, 1090, 1091, 1092, 1093, 1094,
               1095, 1096, 1097, 1098, 1099, 1189, 1190, 1191, 1192, 1193,
               1194, 1195, 1196, 1197, 1198, 1199, 1294, 1295, 1296, 1297,
               1298, 1299, 1309}

found_in_bss = {}
not_found = set(target_nums)

for i in range(10234, min(23208, len(bss_lines))):
    stripped = bss_lines[i].strip()
    for m in re.finditer(r'([०-९]{1,4})\s*[।॥|]+\s*$', stripped):
        vnum = dev_to_num(m.group(1))
        if vnum in target_nums:
            # Show context
            pre = stripped[:m.start()].rstrip()
            context_start = max(0, i-3)
            context = []
            for j in range(context_start, min(i+1, len(bss_lines))):
                context.append(f"  [{j}] {bss_lines[j].rstrip()[:120]}")
            found_in_bss[vnum] = (i, stripped, '\n'.join(context))
            not_found.discard(vnum)

# Also search section 2 for 309, 384
for i in range(2315, min(7196, len(bss_lines))):
    stripped = bss_lines[i].strip()
    for m in re.finditer(r'([०-९]{1,4})\s*[।॥|]+\s*$', stripped):
        vnum = dev_to_num(m.group(1))
        if vnum in {309, 384}:
            context_start = max(0, i-3)
            context = []
            for j in range(context_start, min(i+1, len(bss_lines))):
                context.append(f"  [{j}] {bss_lines[j].rstrip()[:120]}")
            found_in_bss[vnum] = (i, stripped, '\n'.join(context))
            not_found.discard(vnum)

# Section 3 for 394
for i in range(7196, min(10234, len(bss_lines))):
    stripped = bss_lines[i].strip()
    for m in re.finditer(r'([०-९]{1,4})\s*[।॥|]+\s*$', stripped):
        vnum = dev_to_num(m.group(1))
        if vnum == 394:
            context_start = max(0, i-3)
            context = []
            for j in range(context_start, min(i+1, len(bss_lines))):
                context.append(f"  [{j}] {bss_lines[j].rstrip()[:120]}")
            found_in_bss[vnum] = (i, stripped, '\n'.join(context))
            not_found.discard(vnum)

# Section 8 for 297, 298
for i in range(27236, min(30893, len(bss_lines))):
    stripped = bss_lines[i].strip()
    for m in re.finditer(r'([०-९]{1,4})\s*[।॥|]+\s*$', stripped):
        vnum = dev_to_num(m.group(1))
        if vnum in {297, 298}:
            context_start = max(0, i-3)
            context = []
            for j in range(context_start, min(i+1, len(bss_lines))):
                context.append(f"  [{j}] {bss_lines[j].rstrip()[:120]}")
            found_in_bss[vnum] = (i, stripped, '\n'.join(context))
            not_found.discard(vnum)

print(f"Found in BSS.txt: {len(found_in_bss)}")
print(f"Not found: {len(not_found)} = {sorted(not_found)}")

# Show a few found examples
for vnum in sorted(found_in_bss.keys())[:5]:
    line_num, line_text, context = found_in_bss[vnum]
    print(f"\n=== Verse {vnum} at line {line_num} ===")
    print(context)

# Now: the issue is our extraction filter - these lines start with ( 
# which means they're commentary references that also contain verse numbers
# Let me check specifically what's at verse 428
print("\n\n=== Searching for ४२८ in BSS.txt section 4 ===")
target_dev = '४२८'
for i in range(10234, min(23208, len(bss_lines))):
    if target_dev in bss_lines[i]:
        for j in range(max(0, i-2), min(i+3, len(bss_lines))):
            print(f"  [{j}] {bss_lines[j].rstrip()[:120]}")
        print("  ---")
