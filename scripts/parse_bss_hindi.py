# -*- coding: utf-8 -*-
"""Parse BSS.txt (Hindi edition of Bhāvana-sāra-saṅgraha) into structured JSON.

v3: pairs each Hindi translation paragraph with its Sanskrit verse block and
the printed source-book reference (e.g. "(गोवि० 1/10)"), cleaning the heavy OCR
garbage in both.

The scanned/OCR'd book interleaves, for every numbered śloka:
  - a Sanskrit verse block (ending in a Devanagari marker like "।।n।।"), which
    may carry the source reference either inline (after the marker, e.g.
    "।।४।। २० १८१८४)") or on the following standalone line ("(चन्द्रा° १३)"),
  - a numbered Hindi translation paragraph starting with "(n)".

Both sequences are numbered sequentially per region (1..N), so verse k pairs
with translation k; number cross-checking with positional fallback absorbs the
OCR noise.

References are cleaned: OCR variants of the abbreviations are normalised
(कु०/क० -> कृ०, मा० -> भा०, मर० -> भ्र०, गोपि० -> गोपा०, "°" -> "०") and the
chapter/verse digits are decoded ("८" as "/", separators "." , "।" "," ":" as
"/"). Each reference is mapped to a `books`-table slug where possible.

Output:
  bss_hindi_structured.json  -- full structured document (items carry
                               sanskrit, hindi, ref_display, book_slug)
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
    "हो", "कर", "था", "थी", "थे", "एवं", "आदि", "नही", "कि", "ही", "भी",
)
HINDI_FUNC_BOUND = re.compile(
    r"(?:^|[\s,।॥\-–—:(('\"])("
    + "|".join(sorted({re.escape(w) for w in HINDI_FUNC}, key=len, reverse=True))
    + r")(?=$|[\s,।॥\-–—:)\"'।])")

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

TRANSL_NUM = re.compile(
    r"^[\(\[\{]\s*(?:[&£=©‰%\-–—]*\s*)?"
    r"([" + DEV_NUM + r"]{1,5}(?:[-,–—]\s*[" + DEV_NUM + r"]{1,5})?|[&£=©‰र])\s*[\)\]\}]")
TRANSL_NUM2 = re.compile(
    r"^[" + DEV_NUM + r"]{1,5}\s*[\)\]\}]")
# translation openers whose number was completely garbled by the OCR
# (e.g. "&=)", "(=)", "&) ...") -- treat them as translation starts with
# unknown number (num=None), so they pair positionally.
TRANSL_GARB1 = re.compile(r"^[\(\[\{]\s*[&£=©‰%\-–—]+\s*[\)\]\}]")
TRANSL_GARB2 = re.compile(r"^[&£=©‰%\-–—]+\s*[\)\]\}]")

SHLOKA_MARKER = re.compile(
    r"[।॥]?\s*([०१२३४५६७८९]{1,5})\s*[।॥]")

# ---- abbreviations and their books --------------------------------------
# canonical abbreviation -> (books-table slug, display abbreviation)
ABBREV_BOOKS = {
    "अ०": ("alankara-kaustubha", "अ०"),
    "आ०": ("ananda-vrndavana-campu", "आ०"),
    "उ०": ("ujjvala-nilamani", "उ०"),
    "कर्णा०": ("krsna-karnamrta", "कर्णा०"),
    "कृ० भा०": ("krsna-bhavanamrta", "कृ० भा०"),
    "कृष्णगणो०": ("radha-krsna-ganoddesa-dipika", "कृष्णगणो०"),
    "कृष्णा०": ("krsnahnika-kaumudi", "कृष्णा०"),
    "क्र०": ("krama-dipika", "क्र०"),
    "गी०": ("gita-govinda", "गी०"),
    "गोपा०": ("gopala-campu", "गोपा०"),
    "गोवि०": ("govinda-lilamrta", "गोवि०"),
    "चन्द्रा०": ("caitanya-candramrta", "चन्द्रा०"),
    "चन्द्रो०": ("caitanya-candrodaya", "चन्द्रो०"),
    "चै०": ("caitanya-caritamrta-mahakavya", "चै०"),
    "ज०": ("jagannatha-vallabha-nataka", "ज०"),
    "दा०": ("dana-keli-kaumudi", "दा०"),
    "प०": ("padyavali", "प०"),
    "भ्र०": ("bhakti-rasamrta-sindhu", "भ्र०"),
    "भा०": ("bhagavatam", "भा०"),
    "भाग०": ("brhad-bhagavatamrta", "भाग०"),
    "मधु": ("madhu-kelivalli", "मधु"),
    "रति०": ("govinda-rati-manjari", "रति०"),
    "रा०": ("radha-rasa-sudha-nidhi", "रा०"),
    "ल०": ("lalita-madhava", "ल०"),
    "लह०": ("stavamrta-lahari", "लह०"),
    "वि०": ("vidagdha-madhava", "वि०"),
    "वृन्दा०": ("vrndavana-mahimamrta", "वृन्दा०"),
    "व्रज०": ("vraja-riti-cintamani", "व्रज०"),
    "शेष०": ("bhakti-rasamrta-sesa", "शेष०"),
    "सं०": ("sangita-madhava", "सं०"),
    "साच०": ("sadhanamrta-candrika", "साच०"),
    "स्त०": ("stavamala", "स्त०"),
    "स्तवा०": ("stavavali", "स्तवा०"),
    "कुसुम०": ("vilapa-kusumanjali", "कुसुम०"),
    "विलाप०": ("vilapa-kusumanjali", "विलाप०"),
    "चिन्ता०": ("dana-keli-cintamani", "चिन्ता०"),
    "स्वयं०": ("stavavali", "स्वयं०"),
}

# OCR variants that normalise to a canonical abbreviation (longest first).
# Every canonical abbreviation is a variant of itself so the trailing "०"
# (e.g. "चन्द्रा°" -> "चन्द्रा०") is consumed with the abbreviation and is not
# mistaken for a verse number.
ABBREV_NORMALIZE = [
    (a, a) for a in ABBREV_BOOKS
] + [
    ("कृ० भा०", "कृ० भा०"), ("कु० भा०", "कृ० भा०"), ("क० भा०", "कृ० भा०"),
    ("कृ भा०", "कृ० भा०"), ("कु भा०", "कृ० भा०"),
    ("कृ० भा", "कृ० भा०"), ("कु० भा", "कृ० भा०"), ("क० भा", "कृ० भा०"),
    ("मर०", "भ्र०"), ("मा०", "भा०"), ("गोपि०", "गोपा०"),
    ("गोपी", "गोपा०"), ("गोपा०", "गोपा०"), ("गोवि०", "गोवि०"),
    ("गोविन्द०", "गोवि०"), ("गो०", "गोवि०"),
    ("चन्द्रा", "चन्द्रा०"), ("चन्द्रो", "चन्द्रो०"),
    ("चै०", "चै०"), ("चे०", "चै०"), ("कृष्णा०", "कृष्णा०"),
    ("कृष्णाह्निक०", "कृष्णा०"), ("णा०", "कृष्णा०"),
    ("कृष्णगणो०", "कृष्णगणो०"), ("कृभा०", "कृ० भा०"),
    ("कर्णा०", "कर्णा०"), ("क्र०", "क्र०"), ("गी०", "गी०"),
    ("गीत०", "गी०"), ("ज०", "ज०"), ("जगन्नाथ०", "ज०"),
    ("दा०", "दा०"), ("दानकेलि०", "दा०"), ("प०", "प०"),
    ("भा०", "भा०"), ("भाग०", "भाग०"), ("वृहद०", "भाग०"),
    ("भ्र०", "भ्र०"), ("भक्तिरसामृत०", "भ्र०"),
    ("मधु०", "मधु"), ("मधु", "मधु"), ("रति०", "रति०"),
    ("रतिमंजरी", "रति०"), ("रा०", "रा०"), ("राधा०", "रा०"),
    ("र०", "रा०"), ("ल०", "ल०"), ("ललित०", "ल०"),
    ("लह०", "लह०"), ("वि०", "वि०"), ("विदग्ध०", "वि०"),
    ("वृन्दा०", "वृन्दा०"), ("वृन्दावन०", "वृन्दा०"), ("वृन्दा", "वृन्दा०"),
    ("व्रज०", "व्रज०"), ("व्रजरीति०", "व्रज०"), ("व्रज", "व्रज०"),
    ("ब्रज०", "व्रज०"), ("शेष०", "शेष०"), ("शेष", "शेष०"),
    ("सं०", "सं०"), ("संगीत०", "सं०"), ("साच०", "साच०"),
    ("साधनामृत०", "साच०"), ("सा० च०", "साच०"), ("सा०", "साच०"),
    ("स्त०", "स्त०"), ("स्तवमाला", "स्त०"), ("स्तवा०", "स्तवा०"),
    ("स्तवावलि०", "स्तवा०"), ("स्तवा", "स्तवा०"), ("स्तवावलिः", "स्तवा०"),
    ("कुसुम०", "कुसुम०"), ("कुसुमांजलि", "कुसुम०"),
    ("विलाप०", "विलाप०"), ("विलाप", "विलाप०"),
    ("चिन्ता०", "चिन्ता०"), ("चिन्तामणि", "चिन्ता०"), ("चिन्ता", "चिन्ता०"),
    ("स्वयं०", "स्वयं०"), ("स्वयं", "स्वयं०"),
    # "रा०" (राधा-रस-सुधा-निधि) OCR'd as "र०", and "र" misread as "२"
    ("र०", "रा०"), ("र ०", "रा०"), ("२०", "रा०"),
    # "कृ० भा०" occasionally prints as "कृभा०" or "कृ०भा०"
    ("कृभा०", "कृ० भा०"), ("कृ०भा०", "कृ० भा०"), ("कुभा०", "कृ० भा०"),
    # "कृ० मा०" = "कृ० भा०" (भ misread as म)
    ("कृ० मा०", "कृ० भा०"), ("कृ० मा", "कृ० भा०"), ("कृ मा०", "कृ० भा०"),
    ("कु० मा०", "कृ० भा०"),
    # "चि" short form of दानकेलि-चिन्तामणि
    ("चि", "चिन्ता०"),
]

def dev_to_int(s):
    return int("".join(DEV_MAP.get(c, c) for c in s))


def is_colophon(line):
    return bool(COLOPHON.search(line))


def is_translation_start(line):
    t = line.strip()
    return bool(TRANSL_NUM.match(t) or TRANSL_NUM2.match(t)
                or TRANSL_GARB1.match(t) or TRANSL_GARB2.match(t))


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
    if TRANSL_GARB1.match(t) or TRANSL_GARB2.match(t):
        return None
    return None


HINDI_VERB_END = (
    "है", "हैं", "हैँ", "हे", "था", "थी", "थे", "गया", "गये", "गयी",
    "रहा", "रही", "रहे", "लगा", "लगी", "लगे", "लगीं", "करते", "करती",
    "करता", "देखते", "देखती", "जाते", "जाता", "जाती", "होता", "होती",
    "होते", "हुए", "हुई", "हुआ", "सकता", "सकते", "सकती", "किया", "किये",
    "करें", "करे", "बना", "बनाते", "होकर", "करके", "बताया", "कहा", "कही",
    "पूछा", "बोली", "बोला", "बोलीं", "कहीं",
)

def _sanskrit_score(t):
    """Heuristic: higher = more likely a Sanskrit verse line.

    Hindi prose is penalised through its function words, its verb endings
    (है / था / रहा / लगीं / जाते ...), its chandrabindu (ँ) and its
    negation (नहीं). Sanskrit verse lines are typically compound-heavy,
    visarga/halant-final and free of Hindi morphology.
    """
    core = t.rstrip(" ।॥")
    s = 0
    if "॥" in t or "।।" in t or "ऽ" in t:
        s += 3
    if t.rstrip().endswith(("।", "॥")):
        s += 1
    if "ः" in t:
        s += 1
    if "्" in t:
        s += 1
    if core.endswith(SK_FINAL):
        s += 1
    if core.endswith(SK_VERB_LAST):
        s += 2
    if "ँ" in t:
        s -= 1
    if re.search(r"(?:नहीं|नही)", t):
        s -= 4
    if core.endswith(HINDI_VERB_END):
        s -= 4
    s -= len(HINDI_FUNC_BOUND.findall(t))
    return s


def is_sanskrit_line(t):
    if "।।" in t or "॥" in t or "ऽ" in t:
        return True
    return _sanskrit_score(t) >= 2


def clean_heading(t):
    return t.strip().strip(":-–— ()()[]{}&·.,;~").strip()


def is_heading(t):
    t = clean_heading(t)
    if not (4 <= len(t) <= 60):
        return False
    if re.search(r"[0-9०-९]", t):
        return False
    if "।" in t or "॥" in t or "ऽ" in t or "|" in t:
        return False
    if t.endswith("!"):
        return False
    if t.startswith("लीला "):
        return False
    if NONDVN.search(t):
        return False
    if "भावना" in t or "संग्रह" in t or "श्रीश्री" in t:
        return False
    if re.fullmatch(r"[\u0900-\u097f]+[\s\-–—]*लीला", t):
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


# ---- reference decoding --------------------------------------------------

def _clean_ref_text(raw):
    """Strip OCR junk around a reference line / inline tail."""
    t = raw.strip()
    # the "°" glyph is the ० of an abbreviation (चन्द्रा° -> चन्द्रा०); it can
    # also sit on top of a "०" that is already there (कु०° भा० -> कु० भा०), so
    # dropping it is safest -- the ०-variants then match in _extract_abbrev.
    t = t.replace("°", "").replace("‰", "")
    t = t.strip("|`'\"{}[]()।॥·,.…~&%$#@* ")
    t = re.sub(r"^[-–—=\s]+", "", t)
    t = re.sub(r"[-–—=\s]+$", "", t)
    # a stray "श" before the abbreviation is usually a garbled closing danda
    if t.startswith("श") and t[1:] and any(t[1:].startswith(v) for v, _ in ABBREV_NORMALIZE):
        t = t[1:]
    return t


def _extract_abbrev(text):
    """Return (canonical_abbrev, book_slug, rest) or (None, None, text)."""
    # longest-first against OCR-variant table
    for variant, canonical in sorted(ABBREV_NORMALIZE, key=lambda p: len(p[0]), reverse=True):
        if text.startswith(variant):
            slug, disp = ABBREV_BOOKS[canonical]
            return canonical, slug, text[len(variant):]
    return None, None, text


def _decode_ref_number(digits):
    """Decode the OCR'd chapter/verse number portion.

    The printed reference uses "/" as the chapter/verse separator, which the
    OCR reads as the Devanagari "८". A real digit 8 also prints as "८", so:

      - a trailing "८" (end of string) is a real 8 ("१८" verse 18 stays "१८")
      - "८८" at the very start is canto 8 + slash ("८८१८" -> ८/१८)
      - a run of n "८" is a slash followed by (n-1) real eights ("१८८" -> 1/8)
      - any remaining single "८" is the printed slash ("१८४" -> 1/4)

    Explicit separators "." "," ":" "।" "?" and stray spaces are noise.
    This reproduces the user's reference sample verbatim.
    """
    t = digits
    if t.endswith("८"):
        t = t[:-1] + "@8@"
    if t.startswith("८८"):
        t = "@8@/" + t[2:]
    t = re.sub(r"८{2,}", lambda m: "/" + "८" * (len(m.group(0)) - 1), t)
    t = re.sub(r"८", "/", t)
    t = re.sub(r"[.,।,:/।\s?~!%&*]+", "/", t)
    t = re.sub(r"/+", "/", t)
    t = t.replace("@8@", "८")
    return t.strip("/")


def decode_ref(raw):
    """Return dict(ref_display, book_slug) for a raw reference line."""
    t = _clean_ref_text(raw)
    if not t:
        return None
    if len(t) > 30:
        return None
    abbrev, slug, rest = _extract_abbrev(t)
    if abbrev is None:
        # maybe a numeric-only ref line (e.g. "(पद्धति से)" -> skip)
        if re.fullmatch(r"[\s\d०-९.,/।:-]+", t):
            return {"ref_display": t, "book_slug": None}
        return None
    rest = _decode_ref_number(rest.strip())
    disp = f"{abbrev} {rest}".strip() if rest else abbrev
    return {"ref_display": disp, "book_slug": slug}


def is_ref_line(line):
    """Whether a standalone line looks like a source reference."""
    t = line.strip()
    if not (3 <= len(t) <= 26):
        return False
    if not re.search(r"[०१२३४५६७८९0-9]", t):
        return False
    # a danda line is verse, not ref
    if "।" in t or "॥" in t:
        return False
    return decode_ref(t) is not None


def extract_marker(t):
    """Return (marker_number_str, text_before_marker, tail_after_marker)."""
    m = re.search(r"[।॥]\s*([०१२३४५६७८९]{1,5})\s*[।॥]", t)
    if m:
        start, end = m.span()
        before = t[:start].rstrip(" ।॥")
        tail = t[end:].strip()
        return m.group(1), before, tail
    m = re.search(r"([०१२३४५६७८९]{1,5})\s*[।॥]", t)
    if m:
        start, end = m.span()
        before = t[:start].rstrip(" ।॥")
        tail = t[end:].strip()
        return m.group(1), before, tail
    return None, t, ""


def clean_page_head(line):
    return PAGE_HEADER.sub("", line).strip()


# A full line that is just "<name> लीला" (plus optional OCR junk) is a running
# page header / region title, never content.
LILA_HEADER = re.compile(r"^[अ-हऀ-ः][\u0900-\u097f]*\s*लीला[\s0-9०-९&())\]]*$")
# page-number artifacts like "अ 6.11"
ARTIFACT_NUM = re.compile(r"^[अ-हऀ-ः]\s*[0-9०-९]")

def preprocess(lines):
    body = []
    for ln in lines:
        t = ln.rstrip("\n").strip()
        if not t:
            continue
        if is_colophon(t):
            continue
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
        if LILA_HEADER.fullmatch(t):
            continue
        if ARTIFACT_NUM.match(t):
            continue
        body.append(t)
    return body


def looks_like_heading_start(line):
    """A '(n) ...' line is a printed sub-heading when the text after the
    number is a short title (like '(१) श्रीगौरचन्द्र'), not a paragraph."""
    t = line.strip()
    m = TRANSL_NUM.match(t)
    if not m:
        return False
    inner = m.group(1)
    rest = t[m.end():].strip(" :-–—()")
    if not rest:
        return False
    if len(rest) > 40:
        return False
    if re.search(r"[०१२३४५६७८९0-9]", rest):
        return False
    if re.search(r"है|हैं|हैँ|हो|कर|का|की|के|में|मेँ|से|और|ओर|आदि|एवं", rest):
        return False
    if len(rest) <= 18:
        return True
    return False


def parse_region(lines, start, end, code, name, order):
    body = preprocess(lines[start - 1:end])

    # ---- pass 1: split into verse blocks, refs, headings, translations ----
    verses = []          # {marker, marker_int, text_lines, refs}
    paras = []           # {num, num_int, lines}
    headings = []        # list of heading texts
    heading_index = {}
    cur_heading = None

    def heading_idx(text):
        if text not in heading_index:
            heading_index[text] = len(headings)
            headings.append(text)
        return heading_index[text]

    cur_verse = None
    cur_para = None

    def finish_verse():
        nonlocal cur_verse
        if cur_verse is not None and cur_verse.get("text_lines"):
            verses.append(cur_verse)
        cur_verse = None

    def finish_para():
        nonlocal cur_para
        if cur_para is not None and cur_para.get("lines"):
            paras.append(cur_para)
        cur_para = None

    i = 0
    n = len(body)
    while i < n:
        ln = body[i]

        if is_translation_start(ln) and not looks_like_heading_start(ln):
            finish_verse()
            finish_para()
            cur_para = {
                "num": transl_number(ln),
                "num_int": None,
                "lines": [ln],
                "heading": heading_idx(cur_heading) if cur_heading else None,
            }
            num = cur_para["num"]
            if num:
                try:
                    cur_para["num_int"] = dev_to_int(num)
                except ValueError:
                    cur_para["num_int"] = None
            i += 1
            continue

        marker, before, tail = extract_marker(ln)
        if marker is not None:
            # a verse-end line ends (or starts) a verse block
            finish_para()
            if cur_verse is None:
                cur_verse = {
                    "marker": None,
                    "marker_int": None,
                    "text_lines": [],
                    "refs": [],
                    "heading": heading_idx(cur_heading) if cur_heading else None,
                }
            if before.strip():
                cur_verse["text_lines"].append(before.strip())
            cur_verse["marker"] = marker
            cur_verse["marker_int"] = dev_to_int(marker)
            finish_verse()
            if tail:
                r = decode_ref(tail)
                if r is not None and verses:
                    verses[-1]["refs"].append(r)
                elif r is not None:
                    pass
            i += 1
            continue

        if is_ref_line(ln):
            r = decode_ref(ln)
            if r is not None:
                if verses and cur_verse is None:
                    verses[-1]["refs"].append(r)
                elif cur_para is not None:
                    cur_para["lines"].append(ln)
                i += 1
                continue

        if is_heading(ln):
            cur_heading = clean_heading(ln)
            if cur_para is not None:
                finish_para()
            if cur_verse is not None:
                finish_verse()
            i += 1
            continue

        # plain line: verse continuation, paragraph continuation, or stray
        if cur_para is not None:
            if is_sanskrit_line(ln):
                # a verse chunk started again -- close the open paragraph
                finish_para()
            else:
                cur_para["lines"].append(ln)
                i += 1
                continue
        if cur_verse is not None:
            cur_verse["text_lines"].append(ln)
        elif is_sanskrit_line(ln):
            # stray Sanskrit before any marker (OCR dropped the marker)
            cur_verse = {
                "marker": None,
                "marker_int": None,
                "text_lines": [ln],
                "refs": [],
                "heading": heading_idx(cur_heading) if cur_heading else None,
            }
        # else: orphan non-Sanskrit line (noise) -- drop it
        i += 1

    finish_para()
    finish_verse()

    # ---- pass 2: pair translations with verses ----
    # Both sequences run 1..N in the same order. Use a two-pointer merge:
    # for each translation advance the verse pointer, matching by number when
    # both are known, positional otherwise.
    items = []
    vi = 0
    for para in paras:
        num_int = para["num_int"]
        best = None
        if num_int is not None:
            # look ahead for an exact number match (within a small window)
            look = min(vi + 8, len(verses))
            for k in range(vi, look):
                if verses[k].get("marker_int") == num_int:
                    best = k
                    break
        if best is None:
            best = vi
        verse = verses[best] if best < len(verses) else None
        vi = max(best + 1, vi)

        sanskrit = ""
        ref_display = None
        book_slug = None
        marker = None
        if verse is not None:
            sanskrit = "\n".join(verse["text_lines"])
            marker = verse.get("marker")
            if verse.get("refs"):
                r = verse["refs"][0]
                ref_display = r.get("ref_display")
                book_slug = r.get("book_slug")

        hindi = "\n".join(para["lines"])

        item = {
            "seq": len(items) + 1,
            "num": para["num"],
            "num_int": num_int,
            "hindi": hindi,
            "sanskrit": sanskrit or None,
            "sanskrit_marker": marker,
            "ref_display": ref_display,
            "book_slug": book_slug,
            "heading": para.get("heading"),
        }
        items.append(item)

    return {
        "code": code,
        "name": name,
        "order": order,
        "headings": headings,
        "items": items,
        "verse_count": len(verses),
        "para_count": len(paras),
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
        with_ref = sum(1 for it in items if it["ref_display"])
        with_book = sum(1 for it in items if it["book_slug"])
        with_sk = sum(1 for it in items if it["sanskrit"])
        marker_mismatch = 0
        marker_unknown = 0
        for it in items:
            if it["num_int"] is not None:
                if it["sanskrit_marker"] is None:
                    marker_unknown += 1
                elif int(it["sanskrit_marker"]) != it["num_int"]:
                    marker_mismatch += 1
        summary.append({
            "code": sec["code"],
            "name": sec["name"],
            "order": sec["order"],
            "headings": len(sec["headings"]),
            "verse_blocks": sec["verse_count"],
            "trans_paras": sec["para_count"],
            "items": len(items),
            "items_with_sanskrit": with_sk,
            "items_with_ref": with_ref,
            "items_with_book": with_book,
            "num_vs_marker_mismatch": marker_mismatch,
            "num_vs_marker_unknown": marker_unknown,
        })
    with open(OUT_SUM, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)
    for s in summary:
        print(s)


if __name__ == "__main__":
    main()
