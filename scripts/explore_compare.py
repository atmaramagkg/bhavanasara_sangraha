# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding="utf-8")

def load(p):
    return json.load(open(p, encoding="utf-8"))

a = load("scripts/hindi_structured_verses.json")
b = load("scripts/structured_verses.json")
print("hindi_structured_verses.json:", len(a))
print("structured_verses.json:", len(b))

# compare by (period, num)
def key(v):
    return (v.get("period"), v.get("num"))
ka = {key(v): v for v in a}
kb = {key(v): v for v in b}
print("keys only in hindi_structured:", len(set(ka) - set(kb)))
print("keys only in structured:", len(set(kb) - set(ka)))

# check periods in structured_verses.json
from collections import Counter
print("periods in structured_verses.json:", dict(Counter(v.get('period') for v in b)))

# are texts identical where keys overlap?
same = diff = 0
for k in set(ka) & set(kb):
    if ka[k]["text"] == kb[k]["text"]:
        same += 1
    else:
        diff += 1
print(f"overlap same text: {same}, diff text: {diff}")

# check bengali keys
c = load("scripts/bengali_structured_verses.json")
print("\nbengali_structured_verses.json:", len(c))
print("periods:", dict(Counter(v.get('period') for v in c)))
