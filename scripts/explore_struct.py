# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
d = json.load(open("scripts/structured_verses.json", encoding="utf-8"))
print(type(d), len(d))
if isinstance(d, list):
    print(json.dumps(d[0], ensure_ascii=False, indent=1)[:2000])
elif isinstance(d, dict):
    print(list(d.keys())[:10])
    for k, v in list(d.items())[:3]:
        print(k, type(v), len(v) if hasattr(v, "__len__") else v)
