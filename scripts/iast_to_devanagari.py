# -*- coding: utf-8 -*-
"""Convert IAST Sanskrit to Devanagari.

Used to fill the Devanagari originals for verses that only carry the
transliteration (`verses.original_text`), and to remove the transliteration
from the Hindi edition so each verse shows only Devanagari + Hindi translation.

The converter is exported as `iast_to_devanagari(text)` so other scripts can
reuse it. Run directly for a quick round trip test:
  python scripts/iast_to_devanagari.py "aho 'tiramyaṃ pulinaṃ vayasyāḥ"

Algorithm:
  - NFC-normalize, then maximal-munch scan over a lookup of IAST letters
    (diphthongs and consonant digraphs before single consonants).
  - Emit standalone vowels, vowel signs (matras) after a consonant, the
    implicit 'a' after a consonant, and a virama (्) before any following
    consonant. Anusvara (ं), visarga (ः) and avagraha (ऽ) attach to the
    previous syllable and never trigger a virama.
"""
import sys

VOWEL = "aaiiuuruRReo".replace("", "")  # placeholder, never matched
_CONSONANTS = "kgjcjtdnpbmyrlvsh".replace("", "")

# IAST letter (NFC) -> Devanagari base char.
# Vowels used standalone; the same letters double as the vowel signs.
TABLE = {
    "a": "\u0905", "\u0101": "\u0906", "i": "\u0907", "\u012b": "\u0908",
    "u": "\u0909", "\u016b": "\u090a", "\u1e5b": "\u090b", "\u1e5d": "\u0960",
    "\u1e37": "\u090c", "\u1e39": "\u0961", "e": "\u090f", "o": "\u0913",
    "ai": "\u0910", "au": "\u0914",
    "k": "\u0915", "kh": "\u0916", "g": "\u0917", "gh": "\u0918",
    "\u1e45": "\u0919", "c": "\u091a", "ch": "\u091b", "j": "\u091c",
    "jh": "\u091d", "\u00f1": "\u091e", "\u1e6d": "\u091f",
    "\u1e6dh": "\u0920", "\u1e0d": "\u0921", "\u1e0dh": "\u0922",
    "\u1e47": "\u0923", "t": "\u0924", "th": "\u0925", "d": "\u0926",
    "dh": "\u0927", "n": "\u0928", "p": "\u092a", "ph": "\u092b",
    "b": "\u092c", "bh": "\u092d", "m": "\u092e", "y": "\u092f",
    "r": "\u0930", "l": "\u0932", "v": "\u0935", "\u015b": "\u0936",
    "\u1e63": "\u0937", "s": "\u0938", "h": "\u0939",
    "\u1e43": "\u0902",  # anusvara
    "\u1e25": "\u0903",  # visarga
    "'": "\u093d",       # avagraha
}

# Vowel signs (matras) when the vowel follows a consonant.
MATRA = {
    "\u0905": "", "\u0906": "\u093e", "\u0907": "\u093f", "\u0908": "\u0940",
    "\u0909": "\u0941", "\u090a": "\u0942", "\u090b": "\u0943",
    "\u0960": "\u0944", "\u090c": "\u0962", "\u0961": "\u0963",
    "\u090f": "\u0947", "\u0913": "\u094b", "\u0910": "\u0948",
    "\u0914": "\u094c",
}

VOWELS = set(MATRA)
VISARGA = "\u0903"
ANUSVARA = "\u0902"
AVAGRAHA = "\u093d"

# IAST letters that are consonants (digraphs included) -- anything not a
# vowel and not one of the standalone marks.
_MARKS = {ANUSVARA, VISARGA, AVAGRAHA}

_KEYS = sorted(TABLE, key=len, reverse=True)


def _is_consonant(ch):
    return ch not in VOWELS and ch not in _MARKS


def iast_to_devanagari(text):
    text = text.replace("-", "")  # compound marks are not written in Devanagari
    out = []
    prev = None  # previous token's Devanagari char
    prev_was_consonant = False
    i = 0
    n = len(text)
    while i < n:
        matched = None
        for key in _KEYS:
            if text.startswith(key, i):
                matched = key
                break
        if matched is None:
            # space / punctuation / digit -- pass through, and break the
            # "consonant needs a virama" chain.
            out.append(text[i])
            prev = text[i]
            prev_was_consonant = False
            i += 1
            continue

        ch = TABLE[matched]
        if ch in VOWELS:
            if prev_was_consonant:
                out.append(MATRA[ch])
            else:
                out.append(ch)
        elif ch == ANUSVARA or ch == VISARGA:
            # Attaches to the previous syllable; standalone if first.
            out.append(ch)
        elif ch == AVAGRAHA:
            out.append(ch)
        else:
            # consonant
            out.append(ch)
            # A virama is needed when the next IAST letter is a consonant,
            # or the word ends here (final consonant -> halant).
            j = i + len(matched)
            needs_virama = False
            if j < n:
                nxt = None
                for key in _KEYS:
                    if text.startswith(key, j):
                        nxt = key
                        break
                if nxt is not None:
                    nxt_ch = TABLE[nxt]
                    needs_virama = _is_consonant(nxt_ch)
                else:
                    # next char is not an IAST letter (space, punctuation, end)
                    needs_virama = True
            else:
                needs_virama = True
            if needs_virama:
                out.append("\u094d")  # virama
        prev = ch
        prev_was_consonant = ch not in VOWELS and ch not in _MARKS
        i += len(matched)
    return "".join(out)


def main():
    if len(sys.argv) > 1:
        sample = " ".join(sys.argv[1:])
        print(iast_to_devanagari(sample))
        return
    tests = [
        ("kṛṣṇa", "\u0915\u0943\u0937\u094d\u0923"),
        ("bhagavatam", "\u092d\u0917\u0935\u0924\u092e\u094d"),
        ("pulinaṃ", "\u092a\u0941\u0932\u093f\u0928\u0902"),
        ("vayasyāḥ", "\u0935\u092f\u0938\u094d\u092f\u093e\u0903"),
        ("aho 'tiramyaṃ", "\u0905\u0939\u094b \u093d\u0924\u093f\u0930\u092e\u094d\u092f\u0902"),
        ("śrī", "\u0936\u094d\u0930\u0940"),
        ("jñāna", "\u091c\u094d\u091e\u093e\u0928"),
        ("pratyūhāmarṣa", "\u092a\u094d\u0930\u0924\u094d\u092f\u0942\u0939\u093e\u092e\u0930\u094d\u0937"),
        ("kastūrikā", "\u0915\u0938\u094d\u0924\u0942\u0930\u093f\u0915\u093e"),
        ("rādhā-kṛṣṇa", "\u0930\u093e\u0927\u093e\u0915\u0943\u0937\u094d\u0923"),
    ]
    ok = True
    for src, expected in tests:
        got = iast_to_devanagari(src)
        status = "OK " if got == expected else "FAIL"
        if got != expected:
            ok = False
        print(f"{status} {src:24s} -> {got}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
