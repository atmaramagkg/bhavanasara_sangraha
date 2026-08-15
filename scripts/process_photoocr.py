import argparse, json, os, re, sys, glob

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

import hindi_corpus as hc
import hindi_structured_scan as hss

DEFAULT_SRC = r"C:\Users\austr\ocr_test\WinPhotosOCR\oneocr"


def page_num(path):
    m = re.search(r"_(\d+)\.txt$", os.path.basename(path))
    return int(m.group(1)) if m else 10 ** 9


def natural_key(path):
    m1 = re.search(r"PART(\d+)", os.path.basename(path))
    part = int(m1.group(1)) if m1 else 10 ** 9
    return (part, page_num(path))


def load_pages(src):
    pattern = re.compile(r"^PART\d+_\d+\.txt$")
    files = [fp for fp in glob.glob(os.path.join(src, "PART*.txt"))
             if pattern.match(os.path.basename(fp))]
    files = sorted(files, key=natural_key)
    pages = {}
    for fp in files:
        name = os.path.basename(fp)
        with open(fp, encoding="utf-8", errors="replace") as f:
            pages[name] = f.read().splitlines()
    return pages


def dedup_lines(lines):
    out = []
    prev = None
    for ln in lines:
        t = ln.strip()
        if t and t == prev:
            continue
        prev = t
        out.append(t)
    return out


def fold(s):
    return s.replace("॥", "।।").replace("||", "।।").replace("|", "।")


def write_text_dump(pages, out_prefix):
    parts = {}
    for name in sorted(pages, key=natural_key):
        m = re.match(r"PART(\d+)_(\d+)\.txt", name)
        part = "PART" + m.group(1)
        parts.setdefault(part, []).append((int(m.group(2)), name))
    for part, items in parts.items():
        path = f"{out_prefix}_{part}_text.txt"
        with open(path, "w", encoding="utf-8") as f:
            for page_no, name in sorted(items):
                f.write(f"\n[page {page_no}]\n")
                for ln in dedup_lines(pages[name]):
                    f.write(ln + "\n")
        yield part, path


ENDER_SPLIT = re.compile(r"((?:।\s*){1,4}[०-९\d]{1,4}\s*।\s*।)")
ENDER_NUM = re.compile(r"[०-९\d]{1,4}")
TRANS_START_RE = re.compile(r"^\s*[\(\[]\s*([०-९\d]{1,4})\s*[\)\]]")
ANUVAD_RE = re.compile(r"^\s*अनुवाद")
SKIP_HEADER_RE = re.compile(r"^\s*श्री(?:श्री)?\s*भावना\s*सार\s*संग्रह")
STANDALONE_PAREN = re.compile(r"^\s*[\(\[]\s*[०-९\d]{1,4}\s*[\)\]]\s*$")


def code_for(lila_name):
    n = lila_name.rstrip(":").strip()
    for code, aliases in hc.LILA_ALIASES:
        if n in aliases or any(n.startswith(a) for a in aliases):
            return code
    return None


def build_verse_groups(pages):
    """Group the OCR stream by verse: each verse record gets its Devanagari
    lines, the Hindi translation paragraph that follows it (numbered (N)), and
    the inline attribution.  'अनुवाद' markers are dropped; merged verses (two
    verse-enders on one OCR line) are split."""
    order = sorted(pages, key=natural_key)
    all_lines = [(name, ln) for name in order for ln in pages[name]]
    n = len(all_lines)

    def verse_soon(i, look=4):
        for j in range(i + 1, min(n, i + 1 + look)):
            if ENDER_SPLIT.search(fold(all_lines[j][1].strip())):
                return True
        return False

    lilas = []
    cur = None
    cur_verse = None
    mode = "verse"
    last = None
    trans_cur = None

    def open_lila(code, name):
        nonlocal cur, cur_verse, mode, last, trans_cur
        cur = {"code": code, "name": name, "verses": [], "translations": []}
        lilas.append(cur)
        cur_verse, mode, last, trans_cur = None, "verse", None, None

    def close_trans():
        nonlocal trans_cur
        if trans_cur is not None and "".join(trans_cur["lines"]).strip():
            cur["translations"].append(trans_cur)
        trans_cur = None

    def start_trans(num, page, rest):
        nonlocal trans_cur
        close_trans()
        trans_cur = {"num": num, "page": page, "lines": [rest]}

    for i, (page, raw) in enumerate(all_lines):
        t = fold(raw.strip())
        if not t:
            continue
        if SKIP_HEADER_RE.match(t) or STANDALONE_PAREN.match(t):
            continue

        m = hc.HEADER_BARE.match(t)
        if m:
            code = code_for(m.group("lila"))
            if code and verse_soon(i):
                if cur is not None and cur["code"] == code:
                    close_trans()
                    cur_verse, mode, last = None, "verse", None
                    continue
                open_lila(code, m.group("lila"))
                continue

        if ANUVAD_RE.match(t):
            close_trans()
            cur_verse, mode = None, "trans"
            continue

        if cur is None:
            continue

        if mode == "trans":
            if ENDER_SPLIT.search(t):
                mode = "verse"
            elif re.search(r"[\u0900-\u097f]", t):
                tm = TRANS_START_RE.match(t)
                if tm and t[tm.end():].strip():
                    start_trans(hc.to_ascii_num(tm.group(1)), page,
                                t[tm.end():].strip())
                elif trans_cur is not None:
                    trans_cur["lines"].append(t)
            continue

        tm = TRANS_START_RE.match(t)
        if tm and t[tm.end():].strip():
            mode = "trans"
            start_trans(hc.to_ascii_num(tm.group(1)), page, t[tm.end():].strip())
            continue

        if (t.startswith("(") and re.search(r"[\u0900-\u097f]", t)
                and len(t) < 60 and last is not None
                and not ENDER_SPLIT.search(t)):
            last["attrib"] = t
            continue

        pieces = ENDER_SPLIT.split(t)
        for k, piece in enumerate(pieces):
            if k % 2 == 1:
                num = hc.to_ascii_num(ENDER_NUM.search(piece).group())
                if cur_verse is None:
                    cur_verse = {"num": num, "lines": [], "page": page,
                                 "attrib": None}
                cur_verse["num"] = num
                cur["verses"].append(cur_verse)
                last = cur_verse
                cur_verse = None
            else:
                piece = piece.strip()
                if not piece:
                    continue
                if (cur_verse is None and last is not None
                        and piece.startswith("(")
                        and re.search(r"[\u0900-\u097f]", piece)
                        and last["attrib"] is None):
                    last["attrib"] = piece
                    continue
                if cur_verse is None:
                    cur_verse = {"num": None, "lines": [piece], "page": page,
                                 "attrib": None}
                else:
                    cur_verse["lines"].append(piece)

    close_trans()

    for l in lilas:
        trans_by_num = {}
        for tr in l["translations"]:
            trans_by_num.setdefault(tr["num"], []).append(" ".join(tr["lines"]))
        for v in l["verses"]:
            v["devanagari"] = " ".join(v["lines"])
            hs = trans_by_num.get(v["num"])
            v["hindi"] = hs[0] if hs else None
            v.pop("lines", None)
            v["english"] = None
    return lilas


def write_verses_text(lilas, out_prefix):
    parts = {}
    for l in lilas:
        for v in l["verses"]:
            m = re.match(r"PART(\d+)", v["page"])
            part = "PART" + m.group(1)
            parts.setdefault(part, []).append((v, l["name"]))
    for part, items in parts.items():
        path = f"{out_prefix}_{part}_verses.txt"
        with open(path, "w", encoding="utf-8") as f:
            for v, lila_name in items:
                f.write(f"{lila_name}  [{v['page']}]  verse {v['num']}\n")
                f.write(v["devanagari"] + "\n")
                if v["hindi"]:
                    f.write("हि: " + v["hindi"] + "\n")
                if v["attrib"]:
                    f.write("स्रोत: " + v["attrib"] + "\n")
                f.write("\n")
        yield part, path


def main():
    ap = argparse.ArgumentParser(
        description="Process PhotoOCR per-page text into corpus, verse groups, "
                    "and structured verses")
    ap.add_argument("--src", default=DEFAULT_SRC)
    ap.add_argument("--out-prefix", default=os.path.join(ROOT, "photoocr"))
    args = ap.parse_args()

    pages = load_pages(args.src)
    if not pages:
        print(f"no PART*.txt found in {args.src}")
        return
    print(f"pages found: {len(pages)}")

    hc.TXT_DIR = args.src
    lilas, counters = hc.parse_all()

    for l in lilas:
        l["records"] = [r for r in l["records"]
                        if not (r["t"] == "title" and ANUVAD_RE.match(r["text"]))]

    verses, broken = hss.scan_lines(
        (name, ln)
        for name in sorted(pages, key=natural_key)
        for ln in pages[name]
    )

    groups = build_verse_groups(pages)

    for part, path in write_text_dump(pages, args.out_prefix):
        print(f"wrote {path}")
    for part, path in write_verses_text(groups, args.out_prefix):
        print(f"wrote {path}")

    corpus_path = f"{args.out_prefix}_corpus.json"
    json.dump({"lilas": lilas}, open(corpus_path, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"wrote {corpus_path}")

    groups_path = f"{args.out_prefix}_verses.json"
    json.dump({"lilas": groups}, open(groups_path, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"wrote {groups_path}")

    verses_path = f"{args.out_prefix}_structured_verses.json"
    json.dump(verses, open(verses_path, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"wrote {verses_path}")

    broken_path = f"{args.out_prefix}_structured_broken.json"
    json.dump(broken, open(broken_path, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"wrote {broken_path}")

    print(f"\n== corpus per lila ==")
    tot_v = tot_t = 0
    for l in lilas:
        vs = [r for r in l["records"] if r["t"] == "verse"]
        tr = [r for r in l["records"] if r["t"] == "trans"]
        tot_v += len(vs); tot_t += len(tr)
        print(f"  {l['code']:<10} p{str(l['book_page']):>4}  verses={len(vs):<5} "
              f"trans={len(tr):<5}  TOC_verses={hss.TOC_VERSE_COUNTS.get(l['code'], '?')}")
    print(f"  TOTAL verses={tot_v} trans={tot_t}")

    print(f"\n== grouped verses (per lila) ==")
    tot_g = 0
    for l in groups:
        w = sum(1 for v in l["verses"] if v["hindi"])
        tot_g += len(l["verses"])
        print(f"  {l['code']:<10} verses={len(l['verses']):<5} "
              f"with_hindi={w:<5}  TOC_verses={hss.TOC_VERSE_COUNTS.get(l['code'], '?')}")
    print(f"  TOTAL grouped verses={tot_g}")


if __name__ == "__main__":
    main()
