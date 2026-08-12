# -*- coding: utf-8 -*-
"""
hindi_ocr.py — OCR of the Bhavanasara-Sangraha Hindi edition, driven by the
Sanskrit verse-layout rule.

RULE (embedded via hindi_structured_scan.scan_lines):
  verse = TWO lines
    line 1 (pāda 1 + pāda 2): ends with a SINGLE danda  ।   (U+0964)
    line 2 (pāda 3 + pāda 4): ends with
          DOUBLE danda  +  verse number  +  DOUBLE danda   ।।N।।
    optionally followed by an inline attribution  (book-abbr N)
  Every verse that does NOT follow this rule was OCR-split at the wrong place.
  Such pages are re-OCRed (tesseract, alternative PSM / DPI) until a clean
  result is produced.  No Sanskrit line is silently dropped: verses that no
  source can recover are listed in hindi_ocr_remaining.json and the report.

Sources, best first (per page):
  1. embedded text layer of bhavana_sara_sangraha_hindi_text.pdf  (highest yield)
  2. existing tesseract OCR of tess_450/png                        (kept if clean)
  3. fresh tesseract re-OCR sweep (PSM 3/4/6 @ 450 dpi, PSM 3/6 @ 600/800 dpi)

Usage:
  python scripts/hindi_ocr.py            # dry-run: plan + report, no writes
  python scripts/hindi_ocr.py --fix      # write recovered text into the txt dir
"""
import os, sys, re, json, glob, subprocess
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hindi_structured_scan import scan_lines, TOC_VERSE_COUNTS, LILA_ALIASES

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.stdout.reconfigure(encoding="utf-8")

TESS = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
PDF = (r"C:\Users\austr\OneDrive\Documents\_Bhavanasara-Sangraha\Books"
       r"\Bhavanasara-Sangraha\bhavana_sara_sangraha_hindi_text.pdf")
TESS_TXT = r"C:\Users\austr\AppData\Local\Temp\opencode\hindi\tess_450\txt"
TESS_PNG = r"C:\Users\austr\AppData\Local\Temp\opencode\hindi\tess_450\png"
PDF_TXT = os.path.join(ROOT, "pdf_text")
OUT_REMAIN = os.path.join(ROOT, "hindi_ocr_remaining.json")
OUT_REPORT = os.path.join(ROOT, "hindi_ocr_report.txt")

N_PAGES = 700
PART_SPLIT = 350  # PDF pages 1..350 = PART1, 351..700 = PART2

# tesseract re-OCR configs, tried in order of reliability
SWEEP = [(450, 3), (450, 4), (450, 6), (600, 3), (600, 6), (800, 3)]


def part_page(n):
    return (f"PART1_{n}", n) if n <= PART_SPLIT else (f"PART2_{n - PART_SPLIT}", n)


def extract_pdf_text(force=False):
    """Cache the embedded PDF text layer as one file per page."""
    os.makedirs(PDF_TXT, exist_ok=True)
    import fitz
    doc = fitz.open(PDF)
    for n in range(1, doc.page_count + 1):
        out = os.path.join(PDF_TXT, f"page_{n:03d}.txt")
        if not force and os.path.exists(out):
            continue
        with open(out, "w", encoding="utf-8") as f:
            f.write(doc[n - 1].get_text())
    doc.close()


def load_pdf_text(n):
    try:
        return open(os.path.join(PDF_TXT, f"page_{n:03d}.txt"), encoding="utf-8").read()
    except OSError:
        return ""


def load_tess_text(page):
    try:
        return open(os.path.join(TESS_TXT, page + ".txt"), encoding="utf-8").read()
    except OSError:
        return ""


def validate(text, label):
    """Apply the verse rule; return (clean_records, broken_records)."""
    return scan_lines((label, ln) for ln in text.splitlines())


def ocr_png(png, psm):
    r = subprocess.run([TESS, png, "stdout", "-l", "hin", "--psm", str(psm)],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=120)
    return r.stdout


def ocr_pdf_page(n, dpi, psm, tmp):
    out = os.path.join(tmp, f"_hocr_{n}_{dpi}_{psm}.png")
    import fitz
    doc = fitz.open(PDF)
    pix = doc[n - 1].get_pixmap(dpi=dpi)
    pix.save(out)
    doc.close()
    try:
        r = subprocess.run([TESS, out, "stdout", "-l", "hin", "--psm", str(psm)],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=180)
        return r.stdout
    finally:
        try:
            os.remove(out)
        except OSError:
            pass


def reocr_sweep(n, page, cur_clean, cur_broken, tmp):
    """Try tesseract configs; return the first rule-clean text that recovers at
    least the current clean verses (no loss) and shares at least one verse
    number with the current source (anchored)."""
    cur_nums = {r["num"] for r in cur_clean if r["num"] is not None}
    cur_count = len(cur_clean)
    if n <= PART_SPLIT:
        png = os.path.join(TESS_PNG, page + ".png")
        jobs = [("png", dpi, psm) for dpi, psm in SWEEP]
    else:
        jobs = [("pdf", dpi, psm) for dpi, psm in SWEEP]
    for kind, dpi, psm in jobs:
        try:
            text = ocr_png(png, psm) if kind == "png" else ocr_pdf_page(n, dpi, psm, tmp)
        except (subprocess.TimeoutExpired, OSError) as e:
            print(f"    sweep {kind} {dpi}dpi psm{psm} failed: {e}", flush=True)
            continue
        cl, br = validate(text, page)
        if not br and len(cl) >= cur_count and cl and (cur_nums & {r["num"] for r in cl}):
            return text, cl, br
    return None, [], []


def main():
    fix = "--fix" in sys.argv
    extract_pdf_text()
    tmp = r"C:\Users\austr\AppData\Local\Temp\opencode"

    stats = Counter()
    remaining = []
    plans = []

    with ThreadPoolExecutor(max_workers=6) as pool:
        futs = {}
        for n in range(1, N_PAGES + 1):
            futs[pool.submit(process_page, n, tmp)] = n
        for fut in as_completed(futs):
            n = futs[fut]
            try:
                plan = fut.result()
            except Exception as e:
                print(f"[page {n}] ERROR {e}", flush=True)
                continue
            plans.append(plan)
    plans.sort(key=lambda p: p[0])

    for n, page, status, adopted, cl, br in plans:
        stats[status] += 1
        for r in br:
            remaining.append(r)
        if fix and adopted is not None and status not in ("keep_tess", "blank"):
            with open(os.path.join(TESS_TXT, page + ".txt"), "w", encoding="utf-8") as f:
                f.write(adopted)

    # final corpus-wide scan of the txt dir
    fin_verses, fin_broken = scan_lines(
        ((os.path.basename(fp)), ln)
        for fp in sorted(glob.glob(os.path.join(TESS_TXT, "*.txt")))
        for ln in open(fp, encoding="utf-8")
    )

    # report
    lines = []
    lines.append(f"page outcomes: {dict(stats)}")
    lines.append(f"final scan over txt dir: clean={len(fin_verses)} broken={len(fin_broken)}")
    lines.append("")
    per = defaultdict(Counter)
    for v in fin_verses:
        per[v["period"]]["clean"] += 1
    for b in fin_broken:
        per[b["period"]][b["reason"]] += 1
    lines.append(f"{'period':12s} {'printed':>7s} {'clean':>6s} {'no_pada1':>9s} {'pada1_no_danda':>15s}")
    for code, _ in LILA_ALIASES:
        p = per.get(code, Counter())
        lines.append(f"{code:12s} {TOC_VERSE_COUNTS.get(code, '-'):>7} "
                     f"{p['clean']:6d} {p['no_pada1']:9d} {p['pada1_no_danda']:15d}")
    lines.append("")
    lines.append(f"remaining (unrecoverable) verses: {len(remaining)}")
    for r in sorted(remaining, key=lambda x: (x["page"], x["num"] or 0)):
        lines.append(f"  {r['page']:16s} num={r['num']} reason={r['reason']} "
                     f"pada1={r['pada1'][:45]!r}")

    report = "\n".join(lines)
    print(report)
    with open(OUT_REPORT, "w", encoding="utf-8") as f:
        f.write(report + "\n")
    with open(OUT_REMAIN, "w", encoding="utf-8") as f:
        json.dump(remaining, f, ensure_ascii=False, indent=1)
    print(f"\nwrote {OUT_REMAIN} and {OUT_REPORT}")


def process_page(n, tmp):
    page, _ = part_page(n)
    t_text = load_tess_text(page)
    p_text = load_pdf_text(n)
    t_cl, t_br = validate(t_text, page)
    p_cl, p_br = validate(p_text, page)

    # 1. already rule-clean in tesseract -> keep as-is
    if t_cl and not t_br:
        return n, page, "keep_tess", None, t_cl, t_br
    # 2. blank page in both sources
    if not t_cl and not t_br and not p_cl and not p_br:
        return n, page, "blank", None, [], []
    # 3. PDF text layer is clean -> adopt it
    if p_cl and not p_br:
        return n, page, "fixed_pdf", p_text, p_cl, p_br
    # 4. both have issues -> try re-OCR sweep
    best_t = (len(t_cl), t_cl, t_br, t_text)
    best_p = (len(p_cl), p_cl, p_br, p_text)
    cur_cl = max(best_t, best_p, key=lambda x: x[0])[1]
    cur_br = max(best_t, best_p, key=lambda x: x[0])[2]
    cur_text = max(best_t, best_p, key=lambda x: x[0])[3]
    cand = reocr_sweep(n, page, cur_cl, cur_br, tmp)
    if cand[0] is not None:
        text, cl, br = cand
        return n, page, "fixed_reocr", text, cl, br
    # 5. nothing recovers everything -> keep the better source, report the rest
    if len(p_cl) > len(t_cl):
        return n, page, "remaining", p_text, p_cl, p_br
    return n, page, "remaining", t_text, t_cl, t_br


if __name__ == "__main__":
    main()
