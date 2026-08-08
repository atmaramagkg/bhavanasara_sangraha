import sqlite3
import json
import urllib.request
from pathlib import Path

SOURCE_DB = Path(r"C:\Users\austr\bhavanasara_sangraha\assets\db\Bhavanasara-Sangraha_En.sqlite")
OUTPUT_FILE = Path(r"C:\Users\austr\bhavanasara_sangraha\translation_qwen_two_pass_test.txt")

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen3:8b"
TEST_LIMIT = 5

TRANSLATE_PROMPT = """
You are a professional literary translator translating a devotional
Sanskrit/Vaishnava text from English into Russian.

Return ONLY the Russian translation. Do not show reasoning or explanations.

Translate faithfully and completely. Do not omit, add, invent, or reinterpret.
Use natural literary Russian while preserving the devotional mood and poetic
imagery.

Preserve all metaphors, similes, personification, relationships, pronouns,
gender, number, and tense.

Use these forms consistently:

Kṛṣṇa = Кришна
Rādhā = Радха
Rādhā-Mādhava = Радха-Мадхава
Rādhā-Govinda = Радха-Говинда
Govinda = Говинда
Vṛndā = Вринда
Vṛndā-devī = Вринда-деви
Śukadeva = Шукадева
Dakṣa = Дакша
Vicakṣaṇa = Вичакшана
Rati = Рати
Cupid = Купидон

sakhī / sakhīs = сакхи
mañjarī / mañjarīs = манджари
kuñja = кунджа
mādhurya-rasa = мадхурья-раса
bhagavat-prema = бхагават-према
tāmbūla = тамбул
vīṇā = вина
aguru = агару
rasa = раса

In devotional context, translate "service" as "служение".

Do NOT translate Sanskrit devotional terms into approximate Russian meanings.
Do NOT replace specific objects, animals, plants, musical instruments, or
body parts with other objects.

In particular:
nail marks = следы от ногтей
lotus-bud breasts = груди, подобные бутонам лотоса
jeweled lamps = украшенные драгоценностями лампы
campaka = чампака
cymbals = кимвалы
cuckoos = кукушки
peacocks = павлины
roosters = петухи
bees / bumblebees = пчёлы / шмели
mad elephant = обезумевший слон
doe = лань
wolf = волк
tiger = тигр

Preserve the exact poetic image even when it sounds unusual in Russian.

Return ONLY the Russian translation.
"""

REVIEW_PROMPT = """
You are the final Russian literary editor for a devotional
Sanskrit/Vaishnava text.

You are given the ORIGINAL ENGLISH and a DRAFT RUSSIAN TRANSLATION.

Your task is to correct the Russian translation against the English.

Return ONLY the corrected final Russian translation.

CRITICAL RULES:

1. Do not omit any sentence or detail from the English.
2. Do not add information that is absent from the English.
3. Correct mistranslations of objects, animals, plants, body parts,
   instruments, actions, relationships, and metaphors.
4. Preserve the poetic imagery rather than replacing it with a different image.
5. Preserve theological meaning.
6. Preserve natural literary Russian.
7. Correct grammar, gender, number, cases, agreement and pronouns.
8. Keep Sanskrit devotional terminology consistent.

Required terminology:

Kṛṣṇa = Кришна
Rādhā = Радха
Rādhā-Mādhava = Радха-Мадхава
Rādhā-Govinda = Радха-Говинда
Govinda = Говинда
Vṛndā = Вринда
Vṛndā-devī = Вринда-деви
Śukadeva = Шукадева
Dakṣa = Дакша
Vicakṣaṇa = Вичакшана
Rati = Рати
Cupid = Купидон
sakhī / sakhīs = сакхи
mañjarī / mañjarīs = манджари
kuñja = кунджа
mādhurya-rasa = мадхурья-раса
bhagavat-prema = бхагават-према
tāmbūla = тамбул
vīṇā = вина
aguru = агару
rasa = раса
service = служение

Never turn one object into another.
For example, nail marks must remain следы от ногтей, not шипы;
cymbals must remain кимвалы, not other instruments;
cuckoos must remain кукушки;
aguru wood must remain древесина агару;
daybreak must remain рассвет / наступление рассвета.

Preserve metaphors such as:
the tiger of Cupid,
the doe of patience, shyness and virtue,
the wolf of pride,
the mad elephant,
the ocean of rasa.

The draft is NOT authoritative. Compare it carefully with the English
and silently repair it.

Return ONLY the final Russian translation.
"""

def call_ollama(prompt):
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "think": False,
        "options": {
            "temperature": 0.15
        }
    }

    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    request = urllib.request.Request(
        OLLAMA_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=900) as response:
        result = json.loads(response.read().decode("utf-8"))

    return result.get("response", "").strip()


def translate_first_pass(english):
    prompt = TRANSLATE_PROMPT + "\n\nORIGINAL ENGLISH:\n\n" + english
    return call_ollama(prompt)


def review_second_pass(english, draft):
    prompt = (
        REVIEW_PROMPT
        + "\n\nORIGINAL ENGLISH:\n\n"
        + english
        + "\n\nDRAFT RUSSIAN:\n\n"
        + draft
    )
    return call_ollama(prompt)


def main():
    print("=" * 70)
    print("BHAVANASARA-SANGRAHA QWEN TWO-PASS TRANSLATION TEST")
    print("=" * 70)
    print()
    print("Model:", MODEL)
    print("Test limit:", TEST_LIMIT)
    print()
    print("The English database will NOT be modified.")
    print()

    if not SOURCE_DB.exists():
        print("ERROR: Source database not found.")
        return

    conn = sqlite3.connect(
        f"file:{SOURCE_DB}?mode=ro",
        uri=True
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
        (TEST_LIMIT,)
    )

    rows = cursor.fetchall()
    conn.close()

    print("Found", len(rows), "quote records.")
    print()

    if not rows:
        print("No quote records found.")
        return

    results = []

    for number, (quote_id, section_id, quote_type, english) in enumerate(
        rows, start=1
    ):
        print("-" * 70)
        print(f"TEST {number}/{len(rows)}")
        print("Quote ID:", quote_id)
        print()
        print("PASS 1: Translation...")

        try:
            draft = translate_first_pass(english)
        except Exception as error:
            print("ERROR in PASS 1:")
            print(error)
            continue

        print("PASS 2: Semantic review and correction...")

        try:
            final = review_second_pass(english, draft)
        except Exception as error:
            print("ERROR in PASS 2:")
            print(error)
            print("Using PASS 1 result.")
            final = draft

        print()
        print("FINAL RUSSIAN:")
        print(final)
        print()

        results.append({
            "id": quote_id,
            "section_id": section_id,
            "quote_type": quote_type,
            "english": english,
            "draft": draft,
            "final": final,
        })

    print("=" * 70)
    print("Saving results...")
    print("=" * 70)

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        f.write("BHAVANASARA-SANGRAHA\n")
        f.write("QWEN 3:8B TWO-PASS RUSSIAN TRANSLATION TEST\n")
        f.write("=" * 70 + "\n\n")

        for number, result in enumerate(results, start=1):
            f.write(f"TEST {number}\n")
            f.write(f"Quote ID: {result['id']}\n")
            f.write(f"Section ID: {result['section_id']}\n")
            f.write(f"Quote type: {result['quote_type']}\n\n")

            f.write("ENGLISH:\n")
            f.write(result["english"])
            f.write("\n\n")

            f.write("PASS 1 DRAFT:\n")
            f.write(result["draft"])
            f.write("\n\n")

            f.write("PASS 2 FINAL:\n")
            f.write(result["final"])
            f.write("\n\n")

            f.write("=" * 70 + "\n\n")

    print()
    print("DONE.")
    print()
    print("English database was NOT modified.")
    print("Results:")
    print(OUTPUT_FILE)


if __name__ == "__main__":
    main()
