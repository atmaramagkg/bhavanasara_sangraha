# -*- coding: utf-8 -*-
"""
Canonical book registry + alias table for Bhavanasara-Sangraha citation parsing.
Each canonical entry: slug -> (title, author)
ALIASES maps every raw spelling variant found in the source .docx to a canonical slug.
"""

CANONICAL_BOOKS = {
    # slug: (title, author)
    "bhagavatam": ("Śrīmad Bhāgavatam", "Śrīla Vyāsadeva"),
    "gopala-campu": ("Gopāla-campū", "Śrīla Jīva Gosvāmī"),
    "bhakti-rasamrta-sindhu": ("Bhakti-rasāmṛta-sindhu", "Śrīla Rūpa Gosvāmī"),
    "ujjvala-nilamani": ("Ujjvala-nīlamaṇi", "Śrīla Rūpa Gosvāmī"),
    "caitanya-caritamrta": ("Caitanya-caritāmṛta", "Śrīla Kṛṣṇadāsa Kavirāja Gosvāmī"),
    "brhad-bhagavatamrta": ("Bṛhad-bhāgavatāmṛta", "Śrīla Sanātana Gosvāmī"),
    "ananda-vrndavana-campu": ("Ānanda-vṛndāvana-campū", "Śrīla Kavi Karṇapūra"),
    "radha-rasa-sudha-nidhi": ("Rādhā-rasa-sudhā-nidhi", "Śrīla Prabodhānanda Sarasvatī"),
    "vidagdha-madhava": ("Vidagdha-mādhava", "Śrīla Rūpa Gosvāmī"),
    "lalita-madhava": ("Lalita-mādhava", "Śrīla Rūpa Gosvāmī"),
    "govinda-lilamrta": ("Govinda-līlāmṛta", "Śrīla Kṛṣṇadāsa Kavirāja Gosvāmī"),
    "krsna-bhavanamrta": ("Kṛṣṇa-bhāvanāmṛta", "Śrīla Viśvanātha Cakravartī Ṭhākura"),
    "krsnahnika-kaumudi": ("Kṛṣṇāhnika-kaumudī", "Śrīla Viśvanātha Cakravartī Ṭhākura"),
    "gita-govinda": ("Gīta-govinda", "Śrīla Jayadeva Gosvāmī"),
    "alankara-kaustubha": ("Alaṅkāra-kaustubha", "Śrīla Kavi Karṇapūra"),
    "padyavali": ("Padyāvalī", "Śrīla Rūpa Gosvāmī"),
    "vrndavana-mahimamrta": ("Vṛndāvana-mahimāmṛta", "Śrīla Prabodhānanda Sarasvatī"),
    # was a broken duplicate stub in the DB (id 33) - keep, just fill in translations
    "radha-krsna-ganoddesa-dipika": ("Rādhā-kṛṣṇa-gaṇoddeśa-dīpikā", "Śrīla Rūpa Gosvāmī"),

    # --- New books discovered while parsing the docx (not previously in DB) ---
    "caitanya-candrodaya": ("Caitanya-candrodaya", "Śrīla Kavi Karṇapūra"),
    "govinda-virudavali": ("Govinda-virudāvalī", "Śrīla Rūpa Gosvāmī"),
    "dana-keli-kaumudi": ("Dāna-keli-kaumudī", "Śrīla Rūpa Gosvāmī"),
    "govinda-rati-manjari": ("Śrī-govinda-rati-mañjarī", None),  # author unverified
    "stavamala": ("Stavamālā", "Śrīla Raghunātha dāsa Gosvāmī"),
    "stavavali": ("Stavāvalī", "Śrīla Raghunātha dāsa Gosvāmī"),
    "sangita-madhava": ("Saṅgīta-mādhava", "Śrī Govinda Kavirāja (Govinda dāsa)"),
    "kunja-bhanga": ("Kuñja-bhaṅga", None),  # author unverified
    "jagannatha-vallabha-nataka": ("Jagannātha-vallabha-nāṭaka", "Śrī Rāmānanda Rāya"),
    "krsna-karnamrta": ("Kṛṣṇa-karṇāmṛta", "Śrīla Bilvamaṅgala Ṭhākura (Līlāśuka)"),
    "sadhanamrta-candrika": ("Sādhanāmṛta-candrikā", "Śrī Siddha Kṛṣṇadāsa Bābājī"),
    "caitanya-candramrta": ("Caitanya-candrāmṛta", "Śrīla Prabodhānanda Sarasvatī"),
    "vilapa-kusumanjali": ("Vilāpa-kusumāñjali", "Śrīla Raghunātha dāsa Gosvāmī"),
    "vraja-riti-cintamani": ("Vraja-rīti-cintāmaṇi", "Śrīla Viśvanātha Cakravartī Ṭhākura"),
    "caitanya-carita": ("Caitanya-carita", "Śrīla Murāri Gupta"),
    "krama-dipika": ("Krama-dīpikā", "Śrī Keśava Kāśmīrī Bhaṭṭa"),
    "caitanya-caritamrta-mahakavya": ("Caitanya-caritāmṛta Mahākāvya", "Śrīla Kavi Karṇapūra"),
}

# Books that existed in the DB as broken/blank duplicate stubs — merge INTO the canonical slug
# old_slug -> canonical_slug  (citations get repointed, duplicate book row removed)
MERGE_DUPLICATES = {
    "srimad-bhagavatam": "bhagavatam",
    "lalita-madhava-nataka": "lalita-madhava",
}

# raw text (exactly as it appears at the end of a quote paragraph, AFTER hyphen-linebreak
# cleanup) -> canonical slug. Longest/most specific strings should be listed; matching
# picks the longest alias that fits at the end of the string.
ALIASES = {
    "Govinda-līlāmṛta": "govinda-lilamrta",
    "Govinda-līlāmrta": "govinda-lilamrta",
    "Govinda-līlāmrṭa": "govinda-lilamrta",
    "Govinda-līlāmṛtam": "govinda-lilamrta",

    "Kṛṣṇa-bhāvanāmṛta": "krsna-bhavanamrta",
    "Kṛṣṇa-bhāvanāmṛtam": "krsna-bhavanamrta",
    "Kṛṣṇa-bhāvanāmṛtaṁ": "krsna-bhavanamrta",

    "Kṛṣṇāhnika-kaumudī": "krsnahnika-kaumudi",
    "Kṛṣṇāhnika-kaumudi": "krsnahnika-kaumudi",
    "Kṛṣnāhnika-kaumudī": "krsnahnika-kaumudi",

    "Ānanda-vṛndāvana-campū": "ananda-vrndavana-campu",
    "Ānanda-vṛndāvana-campu": "ananda-vrndavana-campu",
    "Ānanda-vṛndavāna-campū": "ananda-vrndavana-campu",
    "Ānanda-vṛndāvana Campu": "ananda-vrndavana-campu",

    "Ujjvala-nīlamaṇi": "ujjvala-nilamani",

    "Alaṅkāra-kaustubha": "alankara-kaustubha",
    "Alaṅkāra-kaustubhaḥ": "alankara-kaustubha",

    "SB": "bhagavatam",

    "Lalita-mādhava": "lalita-madhava",
    "Lalita-mādhava-nāṭaka": "lalita-madhava",

    "Rādhā-rasa-sudhā-nidhi": "radha-rasa-sudha-nidhi",

    "Bhakti-rasāmṛta-sindhu": "bhakti-rasamrta-sindhu",

    "Vidagdha-mādhava": "vidagdha-madhava",

    "Padyāvalī": "padyavali",

    "Caitanya-candrodaya": "caitanya-candrodaya",
    "Caitanya-candrodaya-nāṭakam": "caitanya-candrodaya",

    "Govinda-virudāvalī": "govinda-virudavali",

    "Dāna-keli-kaumudī": "dana-keli-kaumudi",

    "Śrī-govinda-rati-mañjarī": "govinda-rati-manjari",

    "Gopāla-pūrva-campū": "gopala-campu",

    "Bṛhad-bhāgavatāmṛta": "brhad-bhagavatamrta",
    "Bṛhad-bhāgavatāmṛtaṁ": "brhad-bhagavatamrta",

    "Vṛndāvana-mahimāmrṭa": "vrndavana-mahimamrta",
    "Vṛndāvana-mahimāmṛtam": "vrndavana-mahimamrta",
    "Vrṇdāvana-mahimāmṛtam": "vrndavana-mahimamrta",
    "Vṛndāvana-mahimāmṛta": "vrndavana-mahimamrta",

    "Gīta-govinda": "gita-govinda",

    "Stavamālā, svayam utprekṣita-līlā": "stavamala",
    "Stava-mālā, gītāvalī": "stavamala",

    "Stavāvali, kusuma-keli": "stavavali",

    "Saṅgīta-mādhava": "sangita-madhava",

    "Kuñja-bhaṅga": "kunja-bhanga",

    "Jagannātha-vallabha-nāṭaka": "jagannatha-vallabha-nataka",
    "Jagannātha-vallabha": "jagannatha-vallabha-nataka",

    "Kṛṣṇa-karṇāmṛta": "krsna-karnamrta",

    "Sādhanāmṛta-candrikā": "sadhanamrta-candrika",
    "Sādhanāmṛta-candrika": "sadhanamrta-candrika",
    "Sāadhanāmṛta-candrika": "sadhanamrta-candrika",

    "Caitanya-candrāmṛta": "caitanya-candramrta",

    "Rādhā-kṛṣṇa-gaṇoddeṣa-dīpikā": "radha-krsna-ganoddesa-dipika",

    "Vilāpa-kusumāñjali": "vilapa-kusumanjali",

    "Vraja-rīti-cintāmaṇi": "vraja-riti-cintamani",

    "Caitanya-carita": "caitanya-carita",

    "Krama-dīpikā": "krama-dipika",

    "Caitanya-caritāmṛta-mahā-kāvyaṁ": "caitanya-caritamrta-mahakavya",
    "Caitanya-caritāmṛta-mahā-kāvyam": "caitanya-caritamrta-mahakavya",
}
