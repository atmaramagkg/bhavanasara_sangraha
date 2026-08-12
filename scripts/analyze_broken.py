# -*- coding: utf-8 -*-
import json, sys
from collections import Counter
sys.stdout.reconfigure(encoding="utf-8")

b = json.load(open("scripts/hindi_structured_broken.json", encoding="utf-8"))
print("total broken:", len(b))

# How many pada1 lines end with a pipe (which _fold normalizes to danda)?
pipe_end = sum(1 for x in b if x["pada1"].rstrip().endswith("|"))
danda_end = sum(1 for x in b if x["pada1"].rstrip().endswith("।"))
both = sum(1 for x in b if x["pada1"].rstrip().endswith(("|", "।")))
print(f"pada1 ends with '|'  : {pipe_end}")
print(f"pada1 ends with '।'  : {danda_end}")
print(f"pada1 ends with '|' or '।': {both}")

# what do the others end with?
tail = Counter()
for x in b:
    t = x["pada1"].rstrip()
    if not t.endswith(("|", "।")):
        tail[t[-3:] if len(t) >= 3 else t]
for x in b:
    t = x["pada1"].rstrip()
    if not t.endswith(("|", "।")):
        tail[t[-2:]] += 1
print("\npada1 endings that are NOT danda-like (top 20):")
for k, c in tail.most_common(20):
    print(f"  {k!r}: {c}")

# pada1 with no trailing punctuation at all
no_punct = sum(1 for x in b if x["pada1"].rstrip() and not x["pada1"].rstrip()[-1] in "।।|,;:")
print("pada1 ending in a bare consonant/other:", no_punct)

# Check the p2 lines of broken - do they contain danda+num+danda?
import re
DANDA = "।"
DDANDA = r"(?:।।|॥)"
NUM = r"[०-९0-9]{1,4}"
PADA2_ENDER = re.compile(
    r"(?:।\s*){1,3}([०-९0-9]{1,4})\s*।।"
    r"(?:\s*[\(\[]\s*[^\(\)\[\]]+\s*[\)\]])?\s*$"
)
def _fold(line):
    return line.replace("॥", "।।").replace("||", "।।").replace("|", "।")

for i in [0, 1, 2, 3, 4, 5, 6, 7]:
    x = b[i]
    print(f"\n--- broken[{i}] num={x['num']} page={x['page']}")
    print("  pada1:", x["pada1"][:80])
    print("  pada2:", x["pada2"][:80])
