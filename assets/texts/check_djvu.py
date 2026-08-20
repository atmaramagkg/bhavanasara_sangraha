import re

dev_to_int = {'०':0,'१':1,'२':2,'३':3,'४':4,'५':5,'६':6,'७':7,'८':8,'९':9}
def num_to_dev(num):
    return ''.join('०१२३४५६७८९'[int(d)] for d in str(num))

def dev_to_num(s):
    r = 0
    for c in s:
        if c in dev_to_int: r = r*10+dev_to_int[c]
        else: return None
    return r

with open(r'C:\Users\austr\OneDrive\Documents\_Bhavanasara-Sangraha\Books\bhavana_sara_sangraha\bhavana_sara_sangraha_hindi_djvu.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"DJVU txt: {len(lines)} lines")

# Check total verse count - look for all verse number patterns
all_verses = {}
for i, line in enumerate(lines):
    stripped = line.strip()
    # Match ।।number।। or number। at end
    for m in re.finditer(r'([०-९]{1,4})\s*[।॥|]+\s*$', stripped):
        vnum = dev_to_num(m.group(1))
        if vnum and 1 <= vnum <= 1500:
            all_verses.setdefault(vnum, []).append(i)
    # Also match (number) pattern for commentary references
    for m in re.finditer(r'\(([०-९]{1,4})\)', stripped):
        vnum = dev_to_num(m.group(1))
        if vnum and 1 <= vnum <= 1500:
            all_verses.setdefault(vnum, []).append(i)

print(f"Unique verse numbers found: {len(all_verses)}")
print(f"Range: {min(all_verses.keys())} to {max(all_verses.keys())}")

# Check our target numbers
targets = {309, 384, 394, 429, 439, 529, 539, 549, 639, 649, 659, 749, 759, 769,
           859, 869, 879, 966, 967, 968, 969, 970, 971, 972, 973, 974,
           975, 976, 977, 978, 979, 980, 981, 982, 983, 984, 985, 986,
           987, 988, 989, 990, 1079, 1089, 1090, 1091, 1092, 1093, 1094,
           1095, 1096, 1097, 1098, 1099, 1189, 1190, 1191, 1192, 1193,
           1194, 1195, 1196, 1197, 1198, 1199, 1294, 1295, 1296, 1297,
           1298, 1299, 1309, 297, 298}

found = 0
not_found = 0
for num in sorted(targets):
    dev = num_to_dev(num)
    if num in all_verses:
        found += 1
        lns = all_verses[num]
        # Find the verse line (not commentary)
        for ln in lns:
            line = lines[ln].strip()
            if line.startswith('('):
                continue
            print(f"  FOUND {num} at line {ln}: {line[:150]}")
            break
    else:
        not_found += 1

print(f"\nFound: {found}, Not found: {not_found}")

# Show what's around the verse number ranges we're missing
# E.g., show what's between 965 and 991 in the DJVU file
print("\n=== Verse numbers around 966-990 ===")
for v in range(965, 992):
    if v in all_verses:
        for ln in all_verses[v]:
            line = lines[ln].strip()
            if not line.startswith('('):
                print(f"  {v}: [{ln}] {line[:120]}")
                break

# Also check: does this edition use different numbering?
# Look at section boundaries
print("\n=== Section markers ===")
for i, line in enumerate(lines):
    s = line.strip()
    if 'अथ ' in s and 'लीला' in s:
        print(f"  [{i}] {s[:120]}")
    elif 'संग्रहः' in s or 'संग्रह' in s:
        if 'इति' in s or 'अथ' in s:
            print(f"  [{i}] {s[:120]}")
