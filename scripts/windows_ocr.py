#!/usr/bin/env python3
"""Batch OCR of Devanagari scans using the built-in Windows OCR engine
(Windows.Media.Ocr), emitting Tesseract-compatible word-level TSV so the
existing verse_analyzer_v09.py pipeline can consume it unchanged.

Requires a Windows OCR language pack with Devanagari support (e.g. Hindi,
hi-IN). Without it the engine can only read the languages installed on
the machine (check OcrEngine.available_recognizer_languages).

Install (elevated PowerShell):
    Add-WindowsCapability -Online -Name Language.BasicFeatures~~~hi-IN~0.0.1.0
    Add-WindowsCapability -Online -Name Language.OCR~~~hi-IN~0.0.1.0

Usage:
    python windows_ocr.py --in DIR --out DIR [--lang hi-IN] [--page-prefix PART]
"""
import argparse
import asyncio
import sys
from pathlib import Path

from winrt.windows.graphics.imaging import BitmapDecoder
from winrt.windows.media.ocr import OcrEngine
from winrt.windows.storage import StorageFile
from winrt.windows.globalization import Language

# Same TSV schema Tesseract writes (level,page,block,par,line,word,
# left,top,width,height,conf,text). Windows OCR has no confidence value,
# so a word-level row is always level=5 and conf=100.
TSV_HEADER = (
    "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num"
    "\tleft\ttop\twidth\theight\tconf\ttext"
)


def make_engine(lang_tag):
    if lang_tag:
        return OcrEngine.try_create_from_language(Language(lang_tag))
    return OcrEngine.try_create_from_user_profile_languages()


async def ocr_page(path, engine):
    f = await StorageFile.get_file_from_path_async(str(path))
    stream = await f.open_read_async()
    decoder = await BitmapDecoder.create_async(stream)
    bitmap = await decoder.get_software_bitmap_async()
    return await engine.recognize_async(bitmap)


def page_number(name):
    try:
        return int(name.removesuffix(".png").rsplit("_", 1)[1])
    except (ValueError, IndexError):
        return 1


async def run(args):
    indir = Path(args.input)
    outdir = Path(args.output)
    outdir.mkdir(parents=True, exist_ok=True)

    engine = make_engine(args.lang)
    if not engine:
        tags = ", ".join(l.language_tag for l in OcrEngine.available_recognizer_languages)
        sys.exit(f"no OCR engine (requested lang={args.lang}); installed: {tags}")
    print(f"OCR engine language: {engine.recognizer_language.language_tag}")

    files = sorted(indir.glob("*.png"))
    if not files:
        sys.exit(f"no PNG files in {indir}")
    print(f"{len(files)} pages")

    for path in files:
        result = await ocr_page(path, engine)
        out = outdir / f"{path.stem}_sanhin.tsv"
        with out.open("w", encoding="utf-8") as fh:
            fh.write(TSV_HEADER + "\n")
            pn = page_number(path.name)
            for line_i, line in enumerate(result.lines, 1):
                for word_i, word in enumerate(line.words, 1):
                    r = word.bounding_rect
                    fh.write(
                        f"5\t{pn}\t1\t1\t{line_i}\t{word_i}\t"
                        f"{int(r.x)}\t{int(r.y)}\t{int(r.width)}\t{int(r.height)}\t"
                        f"100\t{word.text}\n"
                    )
        print(f"  {path.name} -> {out.name} ({len(result.text)} chars)")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", required=True, help="dir of hiscan PNGs")
    ap.add_argument("--output", required=True, help="dir for *_sanhin.tsv")
    ap.add_argument("--lang", default=None, help="OCR language tag, e.g. hi-IN")
    args = ap.parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
