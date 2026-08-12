# -*- coding: utf-8 -*-
"""Extract the Hindi book's section structure from the corpus (review mode).

Groups each lila's records into sections at every accepted heading, and
prints the resulting skeleton (heading + page + verse count) for review.

Usage:
  python scripts/build_hi_sections.py              # review listing
  python scripts/build_hi_sections.py --json OUT   # also dump sections json
"""
import sys, re, json, os

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.abspath(__file__))
CORPUS = os.path.join(ROOT, "hindi_corpus.json")
ARGS = set(sys.argv[1:])

HINDI_MARKERS = [
    "का", "की", "के", "में", "वर्णन", "एवं", "आदि", "उक्ति", "लीला", "सेवा",
    "दर्शन", "आयोजन", "मिलन", "गमन", "अभिसार", "विदा", "श्रवण", "वार्तालाप",
    "चर्चा", "विलास", "निन्दा", "शयन", "प्रसंग", "समाचार", "श्रृंगार",
    "प्रबोधन", "पाठ", "मूलसूत्र", "रास", "शोभा", "विरह", "उत्कठिता",
    "कथोपकथन", "प्रकार", "आक्षेप", "वेश", "अवस्था", "जगना", "सुमिरण",
    "आगमन", "यात्रा", "माधुरी", "आस्वादन", "विविध", "नियुक्त", "शाप",
    "क्रीडा", "उपासन", "स्नान", "वेषभूषा", "मल्लक्रीडा", "गृहगमन", "लौटना",
    "आयोजन", "उत्कंठिता", "परिहास", "वाक्य", "कुञ्ज", "कुंज", "प्रवेश",
    "रचना", "सेवा", "देह", "भाव", "प्रेम", "आनन्द", "मधुपान", "विहार",
]
VERB_ENDINGS = [
    "बोली", "बोला", "बोलीं", "कहा", "कही", "कहीं", "कहने", "लगी", "लगे",
    "लगा", "लगीं", "दिया", "दी", "दीं", "कर", "करो", "करें", "किया", "की",
    "होगा", "होगी", "हो", "है", "हैं", "हैँ", "था", "थी", "थे", "रहा", "रही",
    "रहे", "गया", "गयी", "गये", "सकता", "सकती", "सकते", "पड़ा", "पड़ी",
    "आये", "आई", "जाओ", "जाती", "जाते", "चाहिए", "सकूँ", "मिलेगा", "मिले",
    "हुआ", "हुई", "हुए", "ग्रहण", "निकला", "निकली", "पहुँच", "बताया",
    "बताई", "देखा", "देखी", "देखकर", "सुनकर", "करते", "करती", "बना",
    "बनाया", "आता", "आती", "आते", "जाता", "जाती", "जाते",
]
HINDI_STRONG_END = (":-", ":")
NONDVN = re.compile(r"[^\u0900-\u097f\s।|,;:()\-–—•.!?]")
VI = re.compile(r"्")
SK_FINAL = ("म्", "ं", "ः", "त्", "न्", "स्", "क्", "द्", "र्", "ण्", "ल्", "ट्",
            "ड्", "ठ्", "छ्")
HINDI_BOUND = re.compile(
    "(" + "|".join(HINDI_MARKERS) + r")(?=[\s,।\-–—:()]|$)")


def clean(t):
    return t.strip().strip("\u200c\u200d. ।")


def is_heading(text):
    t = clean(text)
    if not (5 <= len(t) <= 70):
        return False
    if "(" in t or ")" in t:
        return False
    if NONDVN.search(t):
        return False
    if "भावना सार संग्रह" in t or "योगपीठ" in t or re.match(r"^(अथ|इति|अति)\s", t):
        return False
    if "।" in t or "|" in t or "ऽ" in t:
        return False
    if t.endswith((",", ";", "?", "!", "॥")):
        return False
    base = re.sub(r"[:\-–—]+$", "", t).strip()
    if not base:
        return False
    words = [w for w in re.split(r"[\s,।\-–—]+", base) if w]
    single = len(words) == 1
    if single and not (t.endswith(":-") and len(words[0]) >= 5):
        return False
    last = words[-1]
    if last in VERB_ENDINGS:
        return False
    if last.endswith(SK_FINAL) or last.endswith("ां"):
        return False
    if sum(len(w) <= 2 for w in words) >= 2 and not HINDI_BOUND.search(base):
        return False
    if HINDI_BOUND.search(base):
        return True
    return t.endswith(HINDI_STRONG_END) and (single or len(words) >= 2)


def main():
    corpus = json.load(open(CORPUS, encoding="utf-8"))
    out = []
    for l in corpus["lilas"]:
        code = l["code"]
        recs = l["records"]
        sections = []          # {heading, page, n_verse, n_attrib, first_seq, last_seq}
        cur = {"heading": None, "page": None, "verses": 0, "attribs": 0,
               "first_seq": None, "last_seq": None, "last_page": None}
        for r in recs:
            if r["t"] == "title" and is_heading(r["text"]):
                if cur["verses"] or cur["attribs"]:
                    sections.append(cur)
                cur = {"heading": r["text"], "page": r["page"], "verses": 0,
                       "attribs": 0, "first_seq": r["seq"], "last_seq": r["seq"],
                       "last_page": r["page"]}
                continue
            if cur["first_seq"] is None:
                cur["first_seq"] = r["seq"]
                cur["page"] = r["page"]
            cur["last_seq"] = r["seq"]
            cur["last_page"] = r["page"]
            if cur["heading"] is None:
                cur["heading"] = "(intro)"
            if r["t"] == "verse":
                cur["verses"] += 1
            elif r["t"] == "attrib":
                cur["attribs"] += 1
        if cur["verses"] or cur["attribs"]:
            sections.append(cur)
        out.append({"code": code, "sections": sections})
        print(f"==== {code:<10} sections={len(sections)}")
        for s in sections:
            print(f"   p{str(s['page'])[7:]:<8} v={s['verses']:<3} a={s['attribs']:<3} "
                  f"| {s['heading'][:75]}")
        print()
    jout = os.path.join(ROOT, "hindi_sections.json")
    for a in ARGS:
        if a.startswith("--json="):
            jout = a.split("=", 1)[1]
    if "--json" in ARGS or "--all" in ARGS:
        json.dump(out, open(jout, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("wrote", jout)


if __name__ == "__main__":
    main()
