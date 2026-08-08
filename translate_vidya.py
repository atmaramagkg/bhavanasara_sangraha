import sqlite3
import shutil
import time
from pathlib import Path
from deep_translator import GoogleTranslator

PROJECT_DIR = Path(r"C:\Users\austr\bhavanasara_sangraha")

SOURCE_DB = PROJECT_DIR / "assets" / "db" / "Bhavanasara-Sangraha_En.sqlite"
TARGET_DB = PROJECT_DIR / "assets" / "db" / "Bhavanasara-Sangraha_Ru_TEST.sqlite"

TEST_LIMIT = 5
REQUEST_DELAY = 0.5
MAX_RETRIES = 3

GLOSSARY = {
    "Rādhā-Mādhava": "Радха-Мадхава",
    "Rādhā-Govinda": "Радха-Говинда",
    "Rādhā": "Радха",
    "Kṛṣṇa": "Кришна",
    "Govinda": "Говинда",
    "Vṛndā-devī": "Вринда-деви",
    "Vṛndā": "Вринда",
    "Śukadeva": "Шукадева",
    "Dakṣa": "Дакша",
    "Rati": "Рати",
    "sakhīs": "сакхи",
    "sakhī": "сакхи",
    "mañjarīs": "манджари",
    "mañjarī": "манджари",
    "kuñjas": "кунджи",
    "kuñja": "кунджа",
    "mādhurya-rasa": "мадхурья-раса",
    "rasa": "раса",
    "tāmbūla": "тамбула",
    "aguru": "агуру",
    "gopīs": "гопи",
    "gopī": "гопи",
    "bhagavat-prema": "бхагават-према",
    "vīṇā": "вина",
    "Vraja": "Враджа"
}

def protect_terms(text):
    protected = {}
    counter = 0

    for term in sorted(GLOSSARY, key=len, reverse=True):
        if term in text:
            marker = f"ZXQTERM{counter}QXZ"
            text = text.replace(term, marker)
            protected[marker] = GLOSSARY[term]
            counter += 1

    return text, protected

def restore_terms(text, protected):
    for marker, replacement in protected.items():
        text = text.replace(marker, replacement)
    return text

def translate_text(translator, text):
    if not text or not text.strip():
        return text

    protected_text, protected = protect_terms(text)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            result = translator.translate(protected_text)

            if result and result.strip():
                return restore_terms(result, protected)

        except Exception as error:
            print(
                f"Translation error "
                f"(attempt {attempt}/{MAX_RETRIES}): {error}"
            )

            if attempt < MAX_RETRIES:
                time.sleep(2)

    print("Translation failed. Original text preserved.")
    return text

def create_test_database():
    if not SOURCE_DB.exists():
        raise FileNotFoundError(
            f"Source database not found:\n{SOURCE_DB}"
        )

    if TARGET_DB.exists():
        TARGET_DB.unlink()

    print()
    print("Creating test database:")
    print(TARGET_DB)

    shutil.copy2(SOURCE_DB, TARGET_DB)

def translate_test_quotes():
    translator = GoogleTranslator(
        source="en",
        target="ru"
    )

    conn = sqlite3.connect(TARGET_DB)
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

    print()
    print("=" * 70)
    print("BHAVANASARA-SANGRAHA TRANSLATION TEST")
    print("=" * 70)
    print()
    print(f"Found {len(rows)} quote records.")
    print()

    for number, row in enumerate(rows, start=1):
        quote_id, section_id, quote_type, english_text = row

        print("=" * 70)
        print(f"RECORD {number}/{len(rows)}")
        print(f"Quote ID:   {quote_id}")
        print(f"Section ID: {section_id}")
        print(f"Type:       {quote_type}")
        print("=" * 70)

        print()
        print("ENGLISH:")
        print(english_text)

        print()
        print("RUSSIAN:")

        russian_text = translate_text(
            translator,
            english_text
        )

        print(russian_text)

        cursor.execute(
            """
            UPDATE quotes
            SET quote_text = ?
            WHERE id = ?
            """,
            (russian_text, quote_id)
        )

        conn.commit()
        time.sleep(REQUEST_DELAY)

        print()

    conn.close()

    print("=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
    print()
    print("Test database:")
    print(TARGET_DB)
    print()
    print("English database was NOT modified.")
    print("Only quotes.quote_text was changed in the TEST copy.")

def main():
    print("=" * 70)
    print("BHAVANASARA-SANGRAHA RUSSIAN TRANSLATION TEST")
    print("=" * 70)

    print()
    print("Source:")
    print(SOURCE_DB)

    print()
    print("Target:")
    print(TARGET_DB)

    print()
    print("The English database will NOT be modified.")

    create_test_database()
    translate_test_quotes()

if __name__ == "__main__":
    main()
