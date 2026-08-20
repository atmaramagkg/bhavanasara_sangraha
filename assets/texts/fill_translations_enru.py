import sqlite3

db = r'C:\Users\austr\bss\assets\db\Bhavanasara-Sangraha.sqlite'
conn = sqlite3.connect(db)
c = conn.cursor()

# Book metadata - standard IAST transliterations and English/Russian names
book_translations = {
    'book.bhakti-rasamrta-sesa.author': {
        'en': 'Sri Jiva Goswami',
        'ru': u'\u0421\u0440\u0438 \u0414\u0436\u0438\u0432\u0430 \u0413\u043e\u0441\u0432\u0430\u043c\u0438',
    },
    'book.bhakti-rasamrta-sesa.title': {
        'en': 'Bhakti-rasamrta-sesa',
        'ru': u'\u0411\u0445\u0430\u043a\u0442\u0438-\u0440\u0430\u0441\u0430\u043c\u0440\u0442\u0430-\u0448\u0435\u0448',
    },
    'book.dana-keli-cintamani.title': {
        'en': 'Dana-keli-cintamani',
        'ru': u'\u0414\u0430\u043d\u0430-\u043a\u0435\u043b\u0438-\u0447\u0438\u043d\u0442\u0430\u043c\u0430\u043d\u0438',
    },
    'book.dana-keli-cintamani.author': {
        'en': 'Sri Raghunatha Dasa Goswami',
        'ru': u'\u0421\u0440\u0438 \u0420\u0430\u0433\u0445\u0443\u043d\u0430\u0442\u0445\u0430 \u0414\u0430\u0441\u0430 \u0413\u043e\u0441\u0432\u0430\u043c\u0438',
    },
    'book.madhu-kelivalli.title': {
        'en': 'Madhu-kelivalli',
        'ru': u'\u041c\u0430\u0434\u0445\u0443-\u043a\u0435\u043b\u0438\u0432\u0430\u043b\u043b\u0438',
    },
    'book.madhu-kelivalli.author': {
        'en': 'Sri Govardhana Bhatta Goswami',
        'ru': u'\u0421\u0440\u0438 \u0413\u043e\u0432\u0430\u0440\u0434\u0445\u0430\u043d\u0430 \u0411\u0445\u0430\u0442\u0442\u0430 \u0413\u043e\u0441\u0432\u0430\u043c\u0438',
    },
    'book.stavamrta-lahari.title': {
        'en': 'Stavamrta-lahari',
        'ru': u'\u0421\u0442\u0430\u0432\u0430\u043c\u0440\u0442\u0430-\u043b\u0430\u0445\u0430\u0440\u0438',
    },
    'book.stavamrta-lahari.author': {
        'en': 'Sri Raghunatha Dasa Goswami',
        'ru': u'\u0421\u0440\u0438 \u0420\u0430\u0433\u0445\u0443\u043d\u0430\u0442\u0445\u0430 \u0414\u0430\u0441\u0430 \u0413\u043e\u0441\u0432\u0430\u043c\u0438',
    },
}

# Section sub-titles - these are Hindi descriptions that need translation
section_translations = {
    'section.madhyahna_10.2.title': {
        'en': 'Comparison of the incomparably sweet pair of thighs',
        'ru': u'\u0421\u0440\u0430\u0432\u043d\u0435\u043d\u0438\u0435 \u043d\u0435\u0441\u0440\u0430\u0432\u043d\u0438\u043c\u044b\u0445 \u0441\u043b\u0430\u0434\u043a\u0438\u0445 \u0431\u0435\u0434\u0440\u0430',
    },
    'section.madhyahna_10.3.title': {
        'en': 'To what can the face be compared?',
        'ru': u'\u0421 \u0447\u0435\u043c \u043c\u043e\u0436\u043d\u043e \u0441\u0440\u0430\u0432\u043d\u0438\u0442\u044c \u043b\u0438\u0446\u043e?',
    },
    'section.madhyahna_3.3.title': {
        'en': "Krishna's entry into the kunja and various pastimes",
        'ru': u'\u0412\u0445\u043e\u0434 \u041a\u0440\u0438\u0448\u043d\u044b \u0432 \u043a\u0443\u043d\u0434\u044e \u0438 \u0440\u0430\u0437\u043b\u0438\u0447\u043d\u044b\u0435 \u0443\u0432\u0435\u0441\u044b',
    },
    'section.madhyahna_4.2.title': {
        'en': 'Description of service during the six seasons',
        'ru': u'\u041e\u043f\u0438\u0441\u0430\u043d\u0438\u0435 \u0441\u043b\u0443\u0436\u0435\u043d\u0438\u044f \u0432 \u0448\u0435\u0441\u0442\u0438 \u0432\u0440\u0435\u043c\u0435\u043d \u0433\u043e\u0434\u0430',
    },
    'section.madhyahna_4.3.title': {
        'en': 'Description of the beauty of Vrindavana',
        'ru': u'\u041e\u043f\u0438\u0441\u0430\u043d\u0438\u0435 \u043a\u0440\u0430\u0441\u043e\u0442\u044b \u0412\u0440\u0438\u043d\u0434\u0430\u0432\u0430\u043d\u0430',
    },
    'section.madhyahna_7.3.title': {
        'en': 'Honey-drinking pastime in Lalitananda-kunja',
        'ru': u'\u041f\u043e\u0441\u0442\u0443\u043f\u043e\u043a \u0441\u043e\u0441\u0442\u043e\u044f\u043d\u0438\u044f \u043c\u0435\u0434\u043e\u0432\u0430\u044f \u0432 \u041b\u0430\u043b\u0438\u0442\u0430\u043d\u0430\u043d\u0434\u0430-\u043a\u0443\u043d\u0434\u0435',
    },
    'section.madhyahna_9.2.title': {
        'en': 'Efforts are made, but who can count her qualities?',
        'ru': u'\u0421\u0442\u0430\u0440\u0430\u044e\u0442\u0441\u044f \u0441\u0442\u0430\u0440\u0430\u0442\u044c\u0441\u044f, \u043d\u043e \u043a\u0442\u043e \u043c\u043e\u0436\u0435\u0442 \u043f\u043e\u0441\u0447\u0438\u0442\u0430\u0442\u044c \u0435\u0435 \u043a\u0430\u0447\u0435\u0441\u0442\u0432\u0430?',
    },
    'section.madhyahna_9.3.title': {
        'en': 'Description of the beauty of Sri Radha',
        'ru': u'\u041e\u043f\u0438\u0441\u0430\u043d\u0438\u0435 \u043a\u0440\u0430\u0441\u043e\u0442\u044b \u0428\u0440\u0438 \u0420\u0430\u0434\u0445\u0438',
    },
    'section.nishanta_1.5.title': {
        'en': "The couple's tasting of amorous sweetness and pastimes",
        'ru': u'\u0412\u043a\u0443\u0441\u0430\u043d\u0438\u0435 \u043f\u0430\u0440\u043e\u0439 \u044d\u0440\u043e\u0442\u0438\u0447\u0435\u0441\u043a\u043e\u0439 \u0441\u043b\u0430\u0434\u043e\u0441\u0442\u0438 \u0438 \u0443\u0432\u0435\u0441\u043e\u0432',
    },
    'section.nishanta_1.6.title': {
        'en': 'Absorbed in serving the Lord',
        'ru': u'\u041f\u043e\u0433\u0440\u0443\u0436\u0435\u043d\u0438\u0435 \u0413\u043e\u0441\u043f\u043e\u0434\u0443',
    },
    'section.nishanta_1.7.title': {
        'en': "Sri Radha adorns Krishna, who is engaged in her decoration, with the attitude of a lover",
        'ru': u'\u0428\u0440\u0438 \u0420\u0430\u0434\u0445\u0430 \u0443\u043a\u0440\u0430\u0448\u0430\u0435\u0442 \u041a\u0440\u0438\u0448\u043d\u0443, \u0437\u0430\u043d\u044f\u0442\u043e\u0433\u043e \u0435\u0451 \u0443\u043a\u0440\u0430\u0448\u0435\u043d\u0438\u0435\u043c, \u043b\u044e\u0431\u043e\u0432\u043d\u044b\u043c \u0432\u043e\u0441\u0442\u043e\u0440\u0433\u043e\u043c',
    },
    'section.nishanta_2.5.title': {
        'en': "Sakhis' immediate vision of beauty through the lattice windows and its description",
        'ru': u'\u041d\u0435\u043c\u0435\u0434\u043b\u0435\u043d\u043d\u043e\u0435 \u0432\u0438\u0434\u0435\u043d\u0438\u0435 \u043a\u0440\u0430\u0441\u043e\u0442\u044b \u0447\u0435\u0440\u0435\u0437 \u0440\u0435\u0448\u0435\u0442\u043a\u0443 \u0438 \u0435\u0451 \u043e\u043f\u0438\u0441\u0430\u043d\u0438\u0435',
    },
    'section.nishanta_2.6.title': {
        'en': 'Awakening from sleep by birdsong and description of the immediate state',
        'ru': u'\u041f\u0440\u043e\u0431\u0443\u0436\u0434\u0435\u043d\u0438\u0435 \u043e\u0442 \u0441\u043d\u0430 \u043f\u0435\u043d\u0438\u0435\u043c \u043f\u0442\u0438\u0446 \u0438 \u043e\u043f\u0438\u0441\u0430\u043d\u0438\u0435 \u043d\u0435\u043c\u0435\u0434\u043b\u0435\u043d\u043d\u043e\u0433\u043e \u0441\u043e\u0441\u0442\u043e\u044f\u043d\u0438\u044f',
    },
    'section.nishanta_2.7.title': {
        'en': "The bed of union and the sakhis' supreme bliss at Sri Radha's limbs' vision",
        'ru': u'\u041a\u0440\u043e\u0432\u0430\u0442\u044c \u0441\u043e\u0435\u0434\u0438\u043d\u0435\u043d\u0438\u044f \u0438 \u0432\u0435\u0440\u0445\u043e\u0432\u043d\u0435\u0439\u0448\u0438\u0439 \u0430\u043d\u0430\u043d\u0434 \u0441\u0430\u043a\u0438 \u043e\u0442 \u0432\u0438\u0434\u0435\u043d\u0438\u044f \u0447\u043b\u0435\u043d\u043e\u0432 \u0428\u0440\u0438 \u0420\u0430\u0434\u0445\u0438',
    },
    'section.nishanta_3.3.title': {
        'en': "Lalita's censure of dawn and Krishna's description of the morning",
        'ru': u'\u041f\u043e\u0440\u0438\u0446\u0430\u043d\u0438\u0435 \u041b\u0430\u043b\u0438\u0442\u043e\u0439 \u0440\u0430\u0441\u0441\u0432\u0435\u0442\u0430 \u0438 \u043e\u043f\u0438\u0441\u0430\u043d\u0438\u0435 \u0443\u0442\u0440\u0430 \u0443\u0441\u0442\u0430\u043c\u0438 \u041a\u0440\u0438\u0448\u043d\u044b',
    },
    'section.nishanta_3.4.title': {
        'en': 'Departure home with forgotten purpose and recitation of verses by the maid servant',
        'ru': u'\u0423\u0445\u043e\u0434 \u0434\u043e\u043c\u043e\u0439 \u0441 \u0437\u0430\u0431\u044b\u0442\u044b\u043c \u043d\u0430\u043c\u0435\u0440\u0435\u043d\u0438\u0435\u043c \u0438 \u0447\u0442\u0435\u043d\u0438\u0435 \u0441\u0442\u0438\u0445\u043e\u0432 \u0441\u043b\u0443\u0436\u0430\u043d\u043a\u043e\u0439',
    },
    'section.nishanta_3.5.title': {
        'en': 'The manner of the couple\'s return home',
        'ru': u'\u041a\u0430\u043a \u043f\u0430\u0440\u0430 \u0432\u043e\u0437\u0432\u0440\u0430\u0449\u0430\u043b\u0430\u0441\u044c \u0434\u043e\u043c\u043e\u0439',
    },
    'section.nishanta_3.6.title': {
        'en': "Sri Radha's reproach and rest",
        'ru': u'\u0423\u043f\u0440\u0435\u043a \u0428\u0440\u0438 \u0420\u0430\u0434\u0445\u0438 \u0438 \u043e\u0442\u0434\u044b\u0445',
    },
    'section.pratah_2.2.title': {
        'en': "Krishna's cowherding pastime and confidential conversation",
        'ru': u'\u041f\u043e\u0441\u0442\u0443\u043f\u043e\u043a \u0432\u044b\u043f\u0430\u0441\u0430\u043d\u0438\u044f \u043a\u043e\u0440\u043e\u0432 \u041a\u0440\u0438\u0448\u043d\u044b \u0438 \u0442\u0430\u0439\u043d\u044b\u0439 \u0440\u0430\u0437\u0433\u043e\u0432\u043e\u0440',
    },
    'section.pratah_2.3.title': {
        'en': 'Arrival at the entrance of the palace',
        'ru': u'\u041f\u0440\u0438\u0431\u044b\u0442\u0438\u0435 \u043a \u0432\u0445\u043e\u0434\u0443 \u0434\u0432\u043e\u0440\u0446\u0430 \u0434\u0432\u043e\u0440\u0446\u0430',
    },
    'section.pratah_2.4.title': {
        'en': "Sri Radha's immediate state and Shyamala's departure home",
        'ru': u'\u0421\u043e\u0441\u0442\u043e\u044f\u043d\u0438\u0435 \u0428\u0440\u0438 \u0420\u0430\u0434\u0445\u0438 \u0438 \u0443\u0445\u043e\u0434 \u0428\u044f\u043c\u0430\u043b\u044b \u0434\u043e\u043c\u043e\u0439',
    },
    'section.pratah_2.5.title': {
        'en': 'Sri Radhika\'s tooth-bathing and other pastimes',
        'ru': u'\u0427\u0438\u0441\u0442\u043a\u0430 \u0437\u0443\u0431\u043e\u0432 \u0428\u0440\u0438 \u0420\u0430\u0434\u0445\u0438\u043a\u0438 \u0438 \u0434\u0440\u0443\u0433\u0438\u0435 \u043f\u043e\u0441\u0442\u0443\u043f\u043a\u0438',
    },
}

updated = 0
for key, vals in {**book_translations, **section_translations}.items():
    c.execute("UPDATE translations SET en = ?, ru = ? WHERE translation_key = ? AND (en IS NULL OR en = '') AND (ru IS NULL OR ru = '')",
              (vals['en'], vals['ru'], key))
    if c.rowcount > 0:
        updated += 1
        print(f"  Updated: {key}")

print(f"\nUpdated {updated} rows")

conn.commit()

# Verify
c.execute("SELECT COUNT(*) FROM translations WHERE (en IS NULL OR en = '') AND (ru IS NULL OR ru = '')")
remaining = c.fetchone()[0]
print(f"Still missing EN+RU: {remaining}")

c.execute("SELECT id, translation_key, en, ru, hi FROM translations WHERE (en IS NULL OR en = '') AND (ru IS NULL OR ru = '')")
for r in c.fetchall():
    print(f"  {r[0]}: {r[1]}")

conn.close()
