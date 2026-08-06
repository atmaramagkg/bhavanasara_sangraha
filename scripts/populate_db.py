# -*- coding: utf-8 -*-
"""
populate_db.py

Parses Bhavanasara-Sangraha.docx and (re)populates the sqlite database used by
the Lila Smarana Flutter app: sections, quotes, citations, verses, and the
`books` / `translations` rows needed to support them.

Usage:
    python3 populate_db.py <input.docx> <input.sqlite> <output.sqlite>

The script does NOT touch: languages, app_settings, period_nodes (these were
already complete / correct). It DOES rebuild: sections, quotes, citations,
verses, and adds/repairs rows in books + translations.

A plain-text report (citation_report.txt) is written next to the output db,
listing anything that needs a human's eyes: sections with zero quotes,
citations that couldn't be matched to a known book, and citations with
suspicious verse numbers (e.g. end < start).
"""
import sys
import re
import shutil
import sqlite3
import unicodedata
from collections import defaultdict

import docx

from book_map import CANONICAL_BOOKS, ALIASES, MERGE_DUPLICATES

TOP_HEADING = "Heading 1"
SUB_HEADING = "Heading 2"
LILA_HEADING = "Heading 3"

TIME_RANGE_RE = re.compile(
    r"\(?\s*(\d{1,2}):(\d{2})\s*([ap])\.?\s*m\.?\s*[—\-–]+\s*(\d{1,2}):(\d{2})\s*([ap])\.?\s*m\.?\s*\)?",
    re.IGNORECASE,
)


def to_24h(h, m, ap):
    h = int(h)
    m = int(m)
    ap = ap.lower()
    if ap == "a":
        if h == 12:
            h = 0
    else:
        if h != 12:
            h += 12
    return f"{h:02d}:{m:02d}"


def parse_time_range(text):
    m = TIME_RANGE_RE.search(text)
    if not m:
        return None
    h1, m1, ap1, h2, m2, ap2 = m.groups()
    return to_24h(h1, m1, ap1), to_24h(h2, m2, ap2)


def fix_linebreak_hyphens(text):
    # Collapses artifacts like "Kṛṣṇāhnika- kaumudī" -> "Kṛṣṇāhnika-kaumudī"
    # and "Govinda-\nlīlāmṛta" (joined across paragraphs) similarly.
    text = re.sub(r"(\w)-\s+(\w)", r"\1-\2", text)
    # "10.13. 1" -> "10.13.1"  (stray space after a decimal point)
    text = re.sub(r"(\d)\.\s+(\d)", r"\1.\2", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# Build one big alternation, longest alias first so e.g. "Kṛṣṇa-bhāvanāmṛtam"
# is preferred over any shorter accidental prefix match.
_ALIAS_KEYS = sorted(ALIASES.keys(), key=len, reverse=True)
_ALIAS_ALT = "|".join(re.escape(a) for a in _ALIAS_KEYS)
NUM_RE = r"\d+(?:\s*\.\s*\d+)*(?:\s*[-\u2013\u2014]\s*\d+[a-zA-Z]?)?(?:\s*,\s*\d+(?:\s*\.\s*\d+)*(?:\s*[-\u2013\u2014]\s*\d+)?)*"
CITATION_RE = re.compile(rf"(?P<book>{_ALIAS_ALT})\s+(?P<num>{NUM_RE})\s*\.?\s*$")

# Fallback: recognise the small number of period-range headers that are NOT
# styled as "Heading 2" in the source docx (plain paragraphs like
# "Madhyāhna-līlā (11:12 a.m.—11:36 a.m.)" with no "=P:" prefix).
PERIOD_NAME_RE = re.compile(
    r"^[A-ZĀĪŚṚṆṬḌṄÑṢḤ][\wĀĪŪṚḶṄÑṬḌṆŚṢḤāīūṛḷṅñṭḍṇśṣḥ\-]*$"
)

MAIN_PERIOD_KEYWORDS = {
    "nishanta": "niśānta",
    "pratah": "prātaḥ",
    "purvahna": "pūrvāhna",
    "madhyahna": "madhyāhna",
    "aparahna": "aparāhna",
    "sayahna": "sāyāhna",
    "pradosha": "pradoṣa",
    "nisha": "niśa",
}


def guess_main_period_code(text):
    low = text.lower()
    for code, kw in MAIN_PERIOD_KEYWORDS.items():
        if kw in low or kw.replace("ā", "a").replace("ḥ", "").replace("ṣ", "s") in low:
            return code
    return None


def looks_like_bare_period_heading(text):
    """Detects a stray, un-styled sub-period header hiding in the body text."""
    tr = parse_time_range(text)
    if not tr:
        return None
    without = TIME_RANGE_RE.sub("", text).strip(" -")
    if 0 < len(without) <= 25 and PERIOD_NAME_RE.match(without.split()[0]):
        return tr
    return None
# Looser fallback: unknown/garbled book name + trailing number. Used only to
# detect "there's probably a citation here we can't parse" for the report.
FALLBACK_CITATION_RE = re.compile(r"[A-ZĀĪŪṚḶṄÑṬḌṆŚṢḤṀṂ][^\d]{2,60}\d[\d.\-\u2013\u2014, ]*$")


def extract_citation(paragraph_text):
    """Returns (clean_text, book_slug, ref_display_raw, num_raw) or (text, None, None, None)."""
    text = fix_linebreak_hyphens(paragraph_text)
    m = CITATION_RE.search(text)
    if m:
        book_alias = m.group("book")
        num_raw = re.sub(r"\s+", "", m.group("num"))
        slug = ALIASES[book_alias]
        clean = text[: m.start()].rstrip()
        ref_display_raw = f"{book_alias} {num_raw}"
        return clean, slug, ref_display_raw, num_raw
    return text, None, None, None


def parse_verse_ref(num_raw):
    """
    '1.1-9'      -> chapter='1', verse_start='1', verse_end='9'
    '1.36'       -> chapter='1', verse_start='36', verse_end=None
    '2.6.50-52'  -> chapter='2.6', verse_start='50', verse_end='52'
    '5'          -> chapter=None, verse_start='5', verse_end=None
    """
    num_raw = num_raw.strip()
    # split off a trailing range like "50-52" (only the *last* dotted segment)
    parts = num_raw.split(".")
    last = parts[-1]
    rm = re.match(r"^(\d+)(?:[-\u2013\u2014](\d+))?$", last)
    if not rm:
        return None, num_raw, None  # unparseable tail, leave as-is
    verse_start, verse_end = rm.group(1), rm.group(2)
    chapter = ".".join(parts[:-1]) if len(parts) > 1 else None
    return chapter, verse_start, verse_end


def collect_book_ids(cur):
    cur.execute("select slug, id from books")
    return {slug: bid for slug, bid in cur.fetchall()}


def ensure_books(cur):
    """Insert any canonical books missing from the DB, fix translations,
    merge known duplicate stub rows into their canonical counterpart."""
    slug_to_id = collect_book_ids(cur)

    # 1) merge duplicate stub rows created by the earlier broken run
    for old_slug, canon_slug in MERGE_DUPLICATES.items():
        if old_slug in slug_to_id and canon_slug in slug_to_id:
            old_id = slug_to_id[old_slug]
            canon_id = slug_to_id[canon_slug]
            cur.execute(
                "update citations set source_book_id=? where source_book_id=?",
                (canon_id, old_id),
            )
            cur.execute(
                "update verses set book_id=? where book_id=?", (canon_id, old_id)
            )
            cur.execute("delete from books where id=?", (old_id,))
            del slug_to_id[old_slug]

    # 2) insert any canonical book not yet present
    for slug, (title, author) in CANONICAL_BOOKS.items():
        if slug in slug_to_id:
            continue
        cur.execute(
            "insert into books (slug, title_key, author_key) values (?,?,?)",
            (slug, f"book.{slug}.title", f"book.{slug}.author"),
        )
        slug_to_id[slug] = cur.lastrowid

    # 3) make sure every canonical book has title/author translations
    cur.execute("select translation_key from translations where translation_key like 'book.%'")
    have = {r[0] for r in cur.fetchall()}
    for slug, (title, author) in CANONICAL_BOOKS.items():
        tkey = f"book.{slug}.title"
        akey = f"book.{slug}.author"
        if tkey not in have:
            cur.execute(
                "insert into translations (language_id, translation_key, translated_text) values (1,?,?)",
                (tkey, title),
            )
        if akey not in have and author:
            cur.execute(
                "insert into translations (language_id, translation_key, translated_text) values (1,?,?)",
                (akey, author),
            )
    return collect_book_ids(cur)


def load_period_nodes(cur):
    cur.execute(
        "select id, parent_id, period_type, time_start, time_end, code from period_nodes"
    )
    mains = {}
    mains_by_code = {}
    subs = {}
    codes_by_id = {}
    for pid, parent_id, ptype, t_start, t_end, code in cur.fetchall():
        codes_by_id[pid] = code
        if ptype == "main":
            mains[(t_start, t_end)] = pid
            mains_by_code[code] = pid
        else:
            subs[(parent_id, t_start, t_end)] = pid
    return mains, mains_by_code, subs, codes_by_id


def wipe_content_tables(cur):
    cur.execute("delete from citations")
    cur.execute("delete from quotes")
    cur.execute("delete from sections")
    cur.execute("delete from verses")
    cur.execute("delete from translations where translation_key like 'section.%'")


def main():
    if len(sys.argv) != 4:
        print("usage: populate_db.py <input.docx> <input.sqlite> <output.sqlite>")
        sys.exit(1)
    docx_path, in_db, out_db = sys.argv[1:4]

    shutil.copyfile(in_db, out_db)
    con = sqlite3.connect(out_db)
    cur = con.cursor()

    slug_to_id = ensure_books(cur)
    main_periods, main_periods_by_code, sub_periods, codes_by_id = load_period_nodes(cur)
    wipe_content_tables(cur)

    report = defaultdict(list)

    d = docx.Document(docx_path)
    paras = d.paragraphs

    # locate the 8 "+A:" range boundaries automatically
    a_indices = [
        i for i, p in enumerate(paras)
        if p.style.name == TOP_HEADING and parse_time_range(p.text)
    ]
    if not a_indices:
        print("ERROR: could not find any top-level '+A:' time-range headings")
        sys.exit(1)
    start, end = a_indices[0], len(paras)
    # stop at the first Heading 1 after the last A block that has no time range
    for i in range(a_indices[-1] + 1, len(paras)):
        if paras[i].style.name == TOP_HEADING:
            end = i
            break

    current_main_id = None
    current_sub_id = None
    current_period_node_id = None
    current_section_id = None
    section_sort = defaultdict(int)   # per period_node_id
    quote_sort = defaultdict(int)     # per section_id

    n_sections = 0
    n_quotes = 0
    n_citations = 0
    verse_cache = {}  # (book_id, ref_display) -> verse_id

    buffer_paragraphs = []

    def flush_quote():
        nonlocal n_quotes, n_citations
        if not buffer_paragraphs or current_section_id is None:
            buffer_paragraphs.clear()
            return
        joined_raw = "\n".join(buffer_paragraphs)
        last = buffer_paragraphs[-1]
        clean_last, slug, ref_display_raw, num_raw = extract_citation(last)
        quote_text = "\n".join(buffer_paragraphs[:-1] + [clean_last]).strip()
        if not quote_text:
            buffer_paragraphs.clear()
            return

        quote_sort[current_section_id] += 1
        cur.execute(
            "insert into quotes (section_id, quote_type, quote_text, sort_order) values (?,?,?,?)",
            (current_section_id, "quote", quote_text, quote_sort[current_section_id]),
        )
        quote_id = cur.lastrowid
        n_quotes += 1

        if slug is None:
            report["unparsed_citations"].append(
                f"section_id={current_section_id} quote_id={quote_id}: {last[-100:]!r}"
            )
            buffer_paragraphs.clear()
            return

        book_id = slug_to_id[slug]
        chapter, verse_start, verse_end = parse_verse_ref(num_raw)
        if verse_start and verse_end and verse_end.isdigit() and int(verse_end) < int(verse_start):
            report["suspicious_verse_numbers"].append(
                f"quote_id={quote_id} book={slug} ref={num_raw}"
            )
        ref_display_num = num_raw  # e.g. "1.1-9" -- for the verses table (per book)

        vkey = (book_id, ref_display_num)
        verse_id = verse_cache.get(vkey)
        if verse_id is None:
            cur.execute(
                "select id from verses where book_id=? and ref_display=?",
                (book_id, ref_display_num),
            )
            row = cur.fetchone()
            if row:
                verse_id = row[0]
            else:
                cur.execute(
                    """insert into verses
                       (book_id, chapter, verse_start, verse_end, ref_display, translation_text, sort_order)
                       values (?,?,?,?,?,?,?)""",
                    (book_id, chapter, verse_start, verse_end, ref_display_num,
                     quote_text, 0),
                )
                verse_id = cur.lastrowid
            verse_cache[vkey] = verse_id

        cur.execute(
            """insert into citations
               (quote_id, source_book_id, source_verse_id, ref_display, confidence)
               values (?,?,?,?,?)""",
            (quote_id, book_id, verse_id, ref_display_raw, "exact"),
        )
        n_citations += 1
        buffer_paragraphs.clear()

    for i in range(start, end):
        p = paras[i]
        style = p.style.name
        text = p.text.strip()

        if style == TOP_HEADING:
            tr = parse_time_range(text)
            flush_quote()
            if tr and tr in main_periods:
                current_main_id = main_periods[tr]
                current_sub_id = None
                current_period_node_id = current_main_id
            else:
                code = guess_main_period_code(text)
                if code and code in main_periods_by_code:
                    current_main_id = main_periods_by_code[code]
                    current_sub_id = None
                    current_period_node_id = current_main_id
                    report["main_headings_matched_by_name_not_time"].append(
                        f"line {i}: {text!r}"
                    )
                else:
                    report["unmatched_main_headings"].append(f"line {i}: {text!r}")
            continue

        if style == SUB_HEADING:
            tr = parse_time_range(text)
            flush_quote()
            if tr and current_main_id is not None and (current_main_id, *tr) in sub_periods:
                current_sub_id = sub_periods[(current_main_id, *tr)]
                current_period_node_id = current_sub_id
            else:
                report["unmatched_sub_headings"].append(f"line {i}: {text!r}")
                current_sub_id = None
                current_period_node_id = current_main_id
            continue

        if style == LILA_HEADING:
            flush_quote()
            title = re.sub(r"^-\s*L\s*:\s*", "", text).strip()
            if current_period_node_id is None:
                report["orphan_lila_headings"].append(f"line {i}: {text!r}")
                current_section_id = None
                continue
            section_sort[current_period_node_id] += 1
            cur.execute(
                "insert into sections (period_node_id, sort_order, title_key) values (?,?,?)",
                (current_period_node_id, section_sort[current_period_node_id], title),
            )
            current_section_id = cur.lastrowid
            n_sections += 1
            # give every section its own translation row using the literal title text
            pcode = codes_by_id.get(current_period_node_id, str(current_period_node_id))
            key = f"section.{pcode}.{section_sort[current_period_node_id]}.title"
            cur.execute(
                "update sections set title_key=? where id=?", (key, current_section_id)
            )
            cur.execute(
                "insert into translations (language_id, translation_key, translated_text) values (1,?,?)",
                (key, title),
            )
            continue

        # body content
        if style in ("Body Text", "Normal"):
            if not text:
                continue  # blank paragraph is just spacing, not a hard separator

            # a handful of sub-period headers in the source docx were never
            # styled as "Heading 2" -- catch them here before treating the
            # paragraph as quote content.
            bare_tr = looks_like_bare_period_heading(text)
            if bare_tr is not None:
                flush_quote()
                if current_main_id is not None and (current_main_id, *bare_tr) in sub_periods:
                    current_sub_id = sub_periods[(current_main_id, *bare_tr)]
                    current_period_node_id = current_sub_id
                    report["sub_headings_recovered_from_body_text"].append(
                        f"line {i}: {text!r}"
                    )
                else:
                    report["unmatched_sub_headings"].append(f"line {i}: {text!r}")
                continue

            buffer_paragraphs.append(text)
            # a paragraph that ends in a recognised citation closes the quote
            _, slug, _, _ = extract_citation(text)
            if slug is not None:
                flush_quote()
            continue

    flush_quote()

    # sections that ended up with zero quotes are worth a human glance
    cur.execute(
        "select s.id, s.title_key from sections s left join quotes q on q.section_id=s.id where q.id is null"
    )
    for sid, title in cur.fetchall():
        report["empty_sections"].append(f"section_id={sid}: {title!r}")

    con.commit()

    with open(out_db.rsplit(".", 1)[0] + "_citation_report.txt", "w", encoding="utf-8") as f:
        f.write(f"sections created: {n_sections}\n")
        f.write(f"quotes created:   {n_quotes}\n")
        f.write(f"citations created:{n_citations}\n\n")
        for k, items in report.items():
            f.write(f"=== {k} ({len(items)}) ===\n")
            for it in items:
                f.write(it + "\n")
            f.write("\n")

    print(f"sections={n_sections} quotes={n_quotes} citations={n_citations}")
    for k, items in report.items():
        print(f"{k}: {len(items)}")

    con.close()


if __name__ == "__main__":
    main()
