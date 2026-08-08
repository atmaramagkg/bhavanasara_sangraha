import sqlite3
import json
import urllib.request
from pathlib import Path

SOURCE_DB = Path(r"C:\Users\austr\bhavanasara_sangraha\assets\db\Bhavanasara-Sangraha_En.sqlite")
OUTPUT_FILE = Path(r"C:\Users\austr\bhavanasara_sangraha\translation_qwen_test_v2.txt")
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen3:8b"
TEST_LIMIT = 5

SYSTEM_PROMPT = """
You are a professional literary translator translating a devotional
Sanskrit/Vaishnava text from English into Russian.

Return ONLY the final Russian translation. Never show reasoning,
thinking, explanations, notes, or commentary.

Preserve the complete meaning. Do not omit, add, invent, or reinterpret.
Use natural, polished literary Russian. Preserve poetic mood, metaphors,
similes, personification, imagery, and poetic comparisons.

Translate sentence by sentence while allowing natural Russian syntax.
Preserve tense, number, gender, relationships, and pronoun references.

Never guess an unfamiliar Sanskrit, devotional, botanical, musical,
ritual, or cultural term.

Use these established forms consistently:

Kṛṣṇa -> Кришна
Rādhā -> Радха
Rādhā-Mādhava -> Радха-Мадхава
Govinda -> Говинда
Vṛndā -> Вринда
Vṛndā-devī -> Вринда-деви
Śukadeva -> Шукадева
Cupid -> Купидон
Rati -> Рати

sakhī / sakhīs -> сакхи
mañjarī / mañjarīs -> манджари
kuñja -> кунджа
mādhurya-rasa -> мадхурья-раса
bhagavat-prema -> бхагават-према
tāmbūla -> тамбул
vīṇā -> вина
aguru -> агару

In devotional context:
service -> служение
betel nuts -> орехи бетеля
cuckoos -> кукушки
vīṇā -> вина
kuñja -> кунджа

Do not replace established devotional terms with guessed Russian meanings.

Preserve poetic images such as lotus faces, lotus breasts, bee-like eyes,
ocean of rasa, mad elephant, tiger of Cupid, wolf of pride, dance of Eros,
and sleep caressing the lovers.

Before returning the answer, silently check for omitted sentences,
invented meanings, incorrect names, inconsistent terminology, wrong
animals/plants/objects/instruments, wrong gender, wrong pronouns, and
machine-like substitutions.

Return ONLY the Russian translation.
"""

def ask_ollama(text):
    prompt = SYSTEM_PROMPT + "\n\nTEXT TO TRANSLATE:\n\n" + text
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "think": False,
        "options": {"temperature": 0.2},
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
    print("BHAVANASARA-SANGRAHA QWEN TRANSLATION TEST V2")
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
    conn = sqlite3.connect(f"file:{SOURCE_DB}?mode=ro", uri=True)
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

    for number, (quote_id, section_id, quote_type, english) in enumerate(rows, start=1):
        print("-" * 70)
        print(f"TEST {number}/{len(rows)}")
        print(f"Quote ID: {quote_id}")
        print()
        print("Translating with local Qwen V2...")

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

        results.append({
            "id": quote_id,
            "section_id": section_id,
            "quote_type": quote_type,
            "english": english,
            "russian": russian,
        })

    print("=" * 70)
    print("Saving test results...")
    print("=" * 70)

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        f.write("BHAVANASARA-SANGRAHA\n")
        f.write("QWEN 3:8B RUSSIAN TRANSLATION TEST V2\n")
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

if __name__ == "__main__":
    main()
