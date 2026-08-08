import sqlite3
import json
import urllib.request
from pathlib import Path

# ============================================================
# BHAVANASARA-SANGRAHA
# Local Qwen Russian Translation Test
#
# SAFETY:
# - English database is READ ONLY.
# - No database is modified.
# - Only 5 quote records are translated.
# - Results are saved to a separate TXT file.
# ============================================================

SOURCE_DB = Path(
    r"C:\Users\austr\bhavanasara_sangraha\assets\db\Bhavanasara-Sangraha_En.sqlite"
)

OUTPUT_FILE = Path(
    r"C:\Users\austr\bhavanasara_sangraha\translation_qwen_test.txt"
)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen3:8b"
TEST_LIMIT = 5

SYSTEM_PROMPT = """
You are translating a devotional Sanskrit/Vaishnava text from English into Russian.

Return ONLY the Russian translation.
Do NOT show your reasoning.
Do NOT explain your choices.
Do NOT add comments before or after the translation.

Translation requirements:

1. Preserve the theological meaning exactly.
2. Use natural, literary Russian.
3. Preserve Sanskrit devotional names and terms rather than mechanically
   translating them.
4. Use consistent Russian transliteration for names.
5. Preserve gender, number, relationships and pronouns.
6. Do not invent meanings that are not present in the English.
7. "service" in a devotional context should normally be rendered as
   "служение", not "обряд".
8. "sakhī" / "sakhīs" should be rendered consistently as
   "сакхи" according to Russian grammatical context.
9. "mañjarī" / "mañjarīs" should be rendered consistently as
   "манджари" according to Russian grammatical context.
10. Kṛṣṇa should be written "Кришна" and Rādhā as "Радха".
11. Do not translate technical devotional terms such as rasa,
    mādhurya-rasa, kuñja, tāmbūla, etc. unless the context clearly
    requires an explanation.
12. Preserve poetic imagery.
13. Do not simplify or omit sentences.
"""


def ask_ollama(text):
    prompt = SYSTEM_PROMPT + "\n\nTEXT TO TRANSLATE:\n\n" + text

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "think": False,
    }

    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    request = urllib.request.Request(
        OLLAMA_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=600) as response:
        result = json.loads(response.read().decode("utf-8"))

    return result.get("response", "").strip()


def main():
    print("=" * 70)
    print("BHAVANASARA-SANGRAHA QWEN TRANSLATION TEST")
    print("=" * 70)
    print()
    print("Source:")
    print(SOURCE_DB)
    print()
    print("Model:")
    print(MODEL)
    print()
    print("The English database will NOT be modified.")
    print()

    if not SOURCE_DB.exists():
        print("ERROR: Source database not found.")
        return

    print("Opening database...")

    conn = sqlite3.connect(
        f"file:{SOURCE_DB}?mode=ro",
        uri=True,
    )
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, section_id, quote_type, quote_text
        FROM quotes
        WHERE quote_text IS NOT NULL
          AND TRIM(quote_text) != ''
        ORDER BY id
        LIMIT ?
        """,
        (TEST_LIMIT,),
    )

    rows = cursor.fetchall()
    conn.close()

    print(f"Found {len(rows)} quote records.")
    print()

    if not rows:
        print("No quote records found.")
        return

    results = []

    for number, (quote_id, section_id, quote_type, english) in enumerate(
        rows,
        start=1,
    ):
        print("-" * 70)
        print(f"TEST {number}/{len(rows)}")
        print(f"Quote ID: {quote_id}")
        print()
        print("Translating with local Qwen...")

        try:
            russian = ask_ollama(english)
        except Exception as error:
            print()
            print("ERROR communicating with Ollama:")
            print(error)
            print()
            continue

        print()
        print("RUSSIAN:")
        print(russian)
        print()

        results.append(
            {
                "id": quote_id,
                "section_id": section_id,
                "quote_type": quote_type,
                "english": english,
                "russian": russian,
            }
        )

    print("=" * 70)
    print("Saving test results...")
    print("=" * 70)

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        f.write("BHAVANASARA-SANGRAHA\n")
        f.write("QWEN 3:8B RUSSIAN TRANSLATION TEST\n")
        f.write("=" * 70 + "\n\n")

        for number, result in enumerate(results, start=1):
            f.write(f"TEST {number}\n")
            f.write(f"Quote ID: {result['id']}\n")
            f.write(f"Section ID: {result['section_id']}\n")
            f.write(f"Quote type: {result['quote_type']}\n\n")

            f.write("ENGLISH:\n")
            f.write(result["english"])
            f.write("\n\n")

            f.write("RUSSIAN:\n")
            f.write(result["russian"])
            f.write("\n\n")

            f.write("=" * 70 + "\n\n")

    print()
    print("DONE.")
    print()
    print("English database was NOT modified.")
    print()
    print("Results:")
    print(OUTPUT_FILE)
    print()


if __name__ == "__main__":
    main()
