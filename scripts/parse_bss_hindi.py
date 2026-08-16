# -*- coding: utf-8 -*-
"""Parse BSS.txt (Hindi edition of Bhāvana-sāra-saṅgraha) into structured JSON.

The scanned/OCR'd book interleaves, for every numbered śloka:
  - a Sanskrit verse block (ending in a Devanagari marker like "।।n।।"), and
  - a numbered Hindi translation paragraph starting with "(n)".

It also carries per-page headers/footers ("अथ <lila> लीला (<page>) श्रीश्री
भावना सार संग्रहः" and the reversed form) and OCR debris that this script
removes. Printed section sub-headings (the book's own headings, e.g.
"मंजरी वर्ग का अपना प्रातःकृत्य एवं यावट का वर्णन") are detected and used
to group the ślokas.

Output:
  bss_hindi_structured.json  -- full structured document
  bss_hindi_summary.json     -- per-section counts for a quick review
"""
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

SRC = r"C:\Users\austr\OneDrive\Documents\_Bhavanasara-Sangraha\Books\Bhavanasara-Sangraha\BSS.txt"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT_JSON = os.path.join(HERE, "..", "bss_hindi_structured.json")
OUT_SUM = os.path.join(HERE, "..", "bss_hindi_summary.json")

DEV = "०१२३४५६७८९"
DEV_MAP = {c: str(i) for i, c in enumerate(DEV)}
DEV_NUM = "".join(DEV) + "0-9"

# Verified 1-indexed line boundaries of each region of BSS.txt.
REGIONS = [
    ("nishanta",    "निशान्त लीला",   1, 460,  2307),
    ("pratah",      "प्रातः लीला",    2, 2315, 6648),
    ("purvahna",    "पूर्वाह्न लीला", 3, 6658, 10205),
    ("madhyahna",   "मध्याह्न लीला",  4, 10234, 23199),
    ("aparahna",    "अपराह्न लीला",   5, 23208, 24377),
    ("sayahna",     "सायाह्न लीला",   6, 24389, 25189),
    ("pradosha",    "प्रदोष लीला",    7, 25196, 27210),
    ("nakta",       "नक्त लीला",      8, 27236, 30319),
    ("upasanghara", "उपसंहार",        9, 30320, 30569),
    ("biographies", "जीवन चरित्र",    10, 30569, 30893),
]

NONDVN = re.compile(r"[^\u0900-\u097f\s।॥|,;:()\-–—•.!?‘’“”'\"°~‰&%]")

HINDI_MARKERS = [
    "का", "की", "के", "में", "वर्णन", "एवं", "आदि", "उक्ति", "लीला", "सेवा",
    "दर्शन", "आयोजन", "मिलन", "गमन", "अभिसार", "विदा", "श्रवण", "वार्तालाप",
    "चर्चा", "विलास", "निन्दा", "शयन", "प्रसंग", "समाचार", "श्रृंगार",
    "प्रबोधन", "पाठ", "मूलसूत्र", "रास", "शोभा", "विरह", "उत्कठिता",
    "कथोपकथन", "प्रकार", "आक्षेप", "वेश", "अवस्था", "जगना", "सुमिरण",
    "आगमन", "यात्रा", "माधुरी", "आस्वादन", "विविध", "नियुक्त", "शाप",
    "क्रीडा", "उपासन", "स्नान", "वेषभूषा", "मल्लक्रीडा", "गृहगमन", "लौटना",
    "आयोजन", "उत्कंठिता", "परिहास", "वाक्य", "कुञ्ज", "कुंज", "प्रवेश",
    "रचना", "देह", "भाव", "प्रेम", "आनन्द", "मधुपान", "विहार", "गोष्ठ",
    "गौचारण", "तैय्यारी", "मूल", "सूत्र", "अनुवाद", "शुक", "सारिका",
    "स्मरण", "संग्रह", "भजन", "सखा", "मंजरी", "वर्ग", "यावट", "कलरव",
    "निद्रा", "प्रबोध", "सेवा-सामग्री", "उक्ति", "जगाना", "वर्णन",
]
HINDI_BOUND = re.compile(
    r"(?:^|[\s\-–—(])(?:"
    + "|".join(re.escape(m) for m in HINDI_MARKERS)
    + r")(?=[\s,।\-–—:()]|$)")

HINDI_FUNC = (
    "है", "हैं", "हैँ", "हैः", "और", "ओर", "के", "की", "का", "को", "में",
    "मेँ", "मे", "पर", "से", "तो", "यह", "ये", "वे", "जो", "नहीं", "नही",
    "हो", "कर", "था", "थी", "थे", "एवं", "आदि",
)

VERB_END = (
    "है", "हैं", "हैँ", "हो", "कर", "किया", "की", "दिया", "दी", "दीं",
    "था", "थी", "थे", "रहा", "रही", "रहे", "गया", "गयी", "गये", "हुआ",
    "हुई", "हुए", "होकर", "करके", "बताया", "बताई", "कहा", "कही", "कहीं",
    "बोली", "बोला", "बोलीं", "पूछा", "पूछी", "लगी", "लगे", "लगा",
)

SK_FINAL = ("म्", "ं", "ः", "त्", "न्", "स्", "क्", "द्", "र्", "ण्", "ल्",
            "ट्", "ड्", "ठ्", "छ्")

SK_VERB_LAST = ("प्राह", "पुनराह", "आह", "माह", "स्म", "उवाच", "अब्रवीत्")

PAGE_HEADER = re.compile(
    r"(?:श्रीश्री\s*भावना?\s*सार\s*संग्रह[ःस]?[^\n]{0,25}|"
    r"[^\n]{0,25}श्रीश्री\s*भावना?\s*सार\s*संग्रह[ःस]?)",
    re.IGNORECASE)
COLOPHON = re.compile(r"इति\s+.*(?:संग्रह|कृष्णदासेन)")
REF_LINE = re.compile(
    r"^\(?\s*[^\u0900-\u097f]*(?:०|भा|गोवि|कृ|आ|चन्द्रा|अ०|ल०|कु०|अ)[^\u0900-\u097f]*\)?$")
TRANSL_NUM = re.compile(
    r"^[\(\[\{]\s*(?:[&£=©‰%\-–—]*\s*)?"
    r"([" + DEV_NUM + r"]{1,5}(?:[-,–—]\s*[" + DEV_NUM + r"]{1,5})?|[&£=©‰र])\s*[\)\]\}]")
TRANSL_NUM2 = re.compile(
    r"^[" + DEV_NUM + r"]{1,5}\s*[\)\]\}]")
SHLOKA_MARKER = re.compile(
    r"(?:।।\s*|॥\s*|।\s*)?([" + DEV_NUM + r"]{1,5})(?:\s*।।|\s*॥|\.?।\s*।?|$)")


def dev_to_int(s):
    return int("".join(DEV_MAP.get(c, c) for c in s))


def is_colophon(line):
    return bool(COLOPHON.search(line))


def is_ref(line):
    t = line.strip()
    if len(t) > 28:
        return False
    if re.search(r"(०|भा०|गोवि|कृ०|आ०|चन्द्रा|अ०|ल०|कु०|कृष्णा|गो.)", t) and re.search(r"[0-9०-९]", t):
        return True
    return False


def is_translation_start(line):
    return bool(TRANSL_NUM.match(line.strip()) or TRANSL_NUM2.match(line.strip()))


def transl_number(line):
    t = line.strip()
    m = TRANSL_NUM.match(t)
    if m:
        inner = m.group(1).strip()
        if inner in ("र", "&", "£", "=", "©", "‰"):
            return None
        return inner
    m = TRANSL_NUM2.match(t)
    if m:
        return m.group(0).strip().rstrip(")]}")
    return None


def is_sanskrit_line(t):
    if "।।" in t or "॥" in t or "ऽ" in t:
        return True
    if re.search(r"।\s*[०१२३४५६७८९0-9]+\s*।", t):
        return True
    if re.search(r"[०१२३४५६७८९0-9]+\s*।\s*।?(\s*\(|$)", t):
        return True
    if t.endswith(("।", "॥", "।।")):
        fw = len(re.findall(r"|".join(HINDI_FUNC), t))
        if fw <= 2 and ("्" in t or "।" in t):
            return True
    return False


def clean_heading(t):
    return t.strip().strip(":-–— ()()[]{}&·.,;~").strip()


def is_heading(t):
    t = clean_heading(t)
    if not (4 <= len(t) <= 60):
        return False
    if re.search(r"[0-9०-९]", t):      # page numbers / headers
        return False
    if "।" in t or "॥" in t or "ऽ" in t or "|" in t:  # verse/end markers
        return False
    if t.endswith("!"):
        return False
    if t.startswith("लीला "):
        return False
    if NONDVN.search(t):
        return False
    if "भावना" in t or "संग्रह" in t or "श्रीश्री" in t:
        return False
    if re.fullmatch(r"[\u0900-\u097f]+[\s\-–—]*लीला", t):  # running page header
        return False
    if re.match(
        r"^(से|को|की|के|है|हैं|हैँ|ओर|और|एवं|में|मेँ|का|पर|तो|यह|ये|वे|जो|"
        r"तुम|तब|फिर|अब|ने|हो|कर|नहीं|नही|वह|मैं|मेरा|मेरे|इस|उस|उन|उन्ह|"
        r"जिस|जिन|वहीं|यहाँ|वहाँ|क्यों|क्यो)", t):
        return False
    words = [w for w in re.split(r"[\s,।\-–—]+", t) if w]
    if not words:
        return False
    if len(words) == 1:
        if len(t) < 6:
            return False
        if t.endswith(VERB_END) or t.endswith(SK_FINAL) or t.endswith(SK_VERB_LAST):
            return False
        return True
    last = words[-1]
    if last in VERB_END:
        return False
    if last in SK_VERB_LAST:
        return False
    if last.endswith(SK_FINAL):
        return False
    if HINDI_BOUND.search(t):
        return True
    if t.endswith((":", ":-")):
        return True
    return False


def extract_shloka_num(t):
    """Return the Devanagari number string encoded in a shloka marker, if any."""
    m = re.search(r"(?:।।\s*|॥\s*|।\s*)([०१२३४५६७८९]{1,5})(?:\s*।\s*।?|\s*॥|$)", t)
    if m:
        return m.group(1)
    m = re.search(r"([०१२३४५६७८९]{1,5})\s*।।", t)
    if m:
        return m.group(1)
    return None


def clean_page_head(line):
    return PAGE_HEADER.sub("", line).strip()


def preprocess(lines):
    body = []
    for ln in lines:
        t = ln.rstrip("\n").strip()
        if not t:
            continue
        if is_colophon(t):
            continue
        if is_ref(t):
            continue
        # page header / footer: contains book-title fragment together with lila
        if re.search(r"भावना?\s*सार\s*संग्रह", t):
            t2 = clean_page_head(t)
            if not t2 or re.fullmatch(r"[\s\-–—_=~%‰&\.*#0-9०१२३४५६७८९()\[\]{}]+", t2):
                continue
            t = t2
        if re.fullmatch(r"[\s\-–—_=~%‰&\.*#0-9०१२३४५६७८९]+", t):
            continue
        if re.fullmatch(r"[अ-हऀ-ः]+", t) and len(t) <= 4:
            continue
        if re.search(r"श्रीश्री\s*गौरांग", t):
            continue
        body.append(t)
    return body


def parse_region(lines, start, end, code, name, order):
    body = preprocess(lines[start - 1:end])

    # ---- split into translation paragraphs and gaps ----
    paragraphs = []          # list of [line, line, ...]; first line = (n)
    gaps = []                # lines before each paragraph
    cur_gap = []
    i = 0
    while i < len(body):
        if is_translation_start(body[i]):
            para = [body[i]]
            j = i + 1
            while j < len(body) and not is_translation_start(body[j]):
                para.append(body[j])
                j += 1
            paragraphs.append(para)
            gaps.append(cur_gap)
            cur_gap = []
            i = j
        else:
            cur_gap.append(body[i])
            i += 1
    gaps.append(cur_gap)

    # ---- assemble items ----
    items = []
    heading_order = []
    heading_index = {}       # text -> index
    current_heading = None   # most recent heading propagates to later items

    def heading_idx(text):
        if text not in heading_index:
            heading_index[text] = len(heading_order)
            heading_order.append(text)
        return heading_index[text]

    for pi, para in enumerate(paragraphs):
        # cut Hindi paragraph at the first Sanskrit-looking continuation line
        cut = None
        for k in range(1, len(para)):
            if is_sanskrit_line(para[k]):
                cut = k
                break
        hindi = para[:1] + (para[1:cut] if cut is not None else para[1:])
        tail = para[cut:] if cut is not None else []

        gap_lines = gaps[pi] + tail
        sanskrit_lines = []
        for ln in gap_lines:
            if is_heading(ln):
                current_heading = clean_heading(ln)
            else:
                sanskrit_lines.append(ln)

        item = {
            "seq": pi + 1,
            "num": transl_number(para[0]),
            "num_int": None,
            "hindi": "\n".join(hindi),
            "sanskrit": "\n".join(sanskrit_lines) or None,
            "sanskrit_marker": None,
            "heading": heading_idx(current_heading) if current_heading else None,
        }
        n = item["num"]
        if n:
            try:
                item["num_int"] = dev_to_int(n)
            except ValueError:
                item["num_int"] = None
        mk = extract_shloka_num(item["sanskrit"] or "")
        if mk:
            item["sanskrit_marker"] = mk
        items.append(item)

    # trailing gap (after last paragraph)
    trailing = gaps[-1]
    for ln in trailing:
        if is_heading(ln):
            heading_idx(ln)
        # else drop (OCR debris / end matter)

    return {
        "code": code,
        "name": name,
        "order": order,
        "headings": heading_order,
        "items": items,
    }


def main():
    txt = open(SRC, "rb").read().decode("utf-8-sig")
    lines = txt.split("\n")
    sections = [parse_region(lines, s, e, c, n, o) for c, n, o, s, e in REGIONS]

    doc = {
        "source": "BSS.txt",
        "title": "भावना-सार-संग्रह (हिन्दी अनुवाद)",
        "sections": sections,
    }
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)

    summary = []
    for sec in sections:
        items = sec["items"]
        summary.append({
            "code": sec["code"],
            "name": sec["name"],
            "order": sec["order"],
            "headings": len(sec["headings"]),
            "items": len(items),
            "items_no_num": sum(1 for it in items if not it["num"]),
            "items_with_sanskrit": sum(1 for it in items if it["sanskrit"]),
            "markers_found": sum(1 for it in items if it["sanskrit_marker"]),
        })
    with open(OUT_SUM, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)
    for s in summary:
        print(s)


if __name__ == "__main__":
    main()
