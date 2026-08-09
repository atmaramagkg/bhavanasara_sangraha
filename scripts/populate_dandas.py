# -*- coding: utf-8 -*-
"""
populate_dandas.py

Adds the 60-danda ("ghatikā") table to the bundled sqlite databases and the
English translations for each danda's short description.

The 60 dandas are 24-minute divisions of the day, grouped under the 8 main
periods already present in `period_nodes`. The description text comes from the
"60 dandas 24.txt" source file (24-hour format).

Usage:
    python3 populate_dandas.py <input.sqlite> [<input.sqlite> ...]
"""
import sqlite3
import sys

MAIN_PERIOD_BY_DANDA = {
    # danda number -> main period id (period_nodes.id)
    1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1,          # Niśānta 03:36-06:00
    7: 2, 8: 2, 9: 2, 10: 2, 11: 2, 12: 2,      # Prātaḥ 06:00-08:24
    13: 3, 14: 3, 15: 3, 16: 3, 17: 3, 18: 3,   # Pūrvāhna 08:24-10:48
    19: 4, 20: 4, 21: 4, 22: 4, 23: 4, 24: 4,
    25: 4, 26: 4, 27: 4, 28: 4, 29: 4, 30: 4,   # Madhyāhna 10:48-15:36
    31: 5, 32: 5, 33: 5, 34: 5, 35: 5, 36: 5,   # Aparāhna 15:36-18:00
    37: 6, 38: 6, 39: 6, 40: 6, 41: 6, 42: 6,   # Sāyaṁ 18:00-20:24
    43: 7, 44: 7, 45: 7, 46: 7, 47: 7, 48: 7,   # Pradoṣa 20:24-22:48
    49: 8, 50: 8, 51: 8, 52: 8, 53: 8, 54: 8,
    55: 8, 56: 8, 57: 8, 58: 8, 59: 8, 60: 8,   # Nakta 22:48-03:36
}

# (start, end) in 24h format, each danda spans 24 minutes starting 03:36.
DANDA_TIMES = [
    ("03:36", "04:00"), ("04:00", "04:24"), ("04:24", "04:48"), ("04:48", "05:12"),
    ("05:12", "05:36"), ("05:36", "06:00"), ("06:00", "06:24"), ("06:24", "06:48"),
    ("06:48", "07:12"), ("07:12", "07:36"), ("07:36", "08:00"), ("08:00", "08:24"),
    ("08:24", "08:48"), ("08:48", "09:12"), ("09:12", "09:36"), ("09:36", "10:00"),
    ("10:00", "10:24"), ("10:24", "10:48"), ("10:48", "11:12"), ("11:12", "11:36"),
    ("11:36", "12:00"), ("12:00", "12:24"), ("12:24", "12:48"), ("12:48", "13:12"),
    ("13:12", "13:36"), ("13:36", "14:00"), ("14:00", "14:24"), ("14:24", "14:48"),
    ("14:48", "15:12"), ("15:12", "15:36"), ("15:36", "16:00"), ("16:00", "16:24"),
    ("16:24", "16:48"), ("16:48", "17:12"), ("17:12", "17:36"), ("17:36", "18:00"),
    ("18:00", "18:24"), ("18:24", "18:48"), ("18:48", "19:12"), ("19:12", "19:36"),
    ("19:36", "20:00"), ("20:00", "20:24"), ("20:24", "20:48"), ("20:48", "21:12"),
    ("21:12", "21:36"), ("21:36", "22:00"), ("22:00", "22:24"), ("22:24", "22:48"),
    ("22:48", "23:12"), ("23:12", "23:36"), ("23:36", "00:00"), ("00:00", "00:24"),
    ("00:24", "00:48"), ("00:48", "01:12"), ("01:12", "01:36"), ("01:36", "02:00"),
    ("02:00", "02:24"), ("02:24", "02:48"), ("02:48", "03:12"), ("03:12", "03:36"),
]

# The 60 short descriptions, danda 1..60 (24-hour source file).
DANDA_DESCRIPTIONS = [
    "These few sakhīs relish the blessed vision of the Divine Couple sleeping in a tight embrace.",
    "During this rest period, They meet in dreams and enjoy limitless loving pastimes together.",
    "He awakens, sees Her beauty, is aroused... but She arises and a ferocious love-battle ensues.",
    "They sleep again as the birds awaken and sing; now the sakhīs rise and come to Their grove.",
    "Daybreak approaching, Rūpa Mañjarī enters and awakens sleepy Rādhā by grasping Her feet.",
    "Holding hands They exit, and separate as sakhīs console and return Them to Their homes.",
    "Rādhā and Kṛṣṇa are awakened in Their respective homes by Their superiors.",
    "Kṛṣṇa goes to milk the cows, then to the Yamunā; She washes, dresses and goes to Yamunā.",
    "They sport in the water together, then are dried and dressed by the sakhīs.",
    "The sakhīs feed Rādhā-Śyāma, then all quickly return home. (Other days They bathe at home.)",
    "Yaśodā sends Kuṇḍalatā to fetch Rādhā to cook; She gets permission from Jaṭilā and departs.",
    "She walks with Her friends to Nandagrām and experiences various Kṛṣṇa-related ecstasies.",
    "Rādhā is affectionately received by Yaśodā and enters the kitchen to cook with Rohiṇī.",
    "Kṛṣṇa bathes, dresses and takes breakfast with His friends, then they wash and rest briefly.",
    "Rādhā and Her friends shyly honor Kṛṣṇa's remnants, then they wash and rest briefly.",
    "Kṛṣṇa dresses for pasturing the cows; Yaśodā makes Him bow at Rādhā's feet.",
    "Kṛṣṇa and friends depart for the forest as all the people see Him off; She returns home.",
    "Rādhā and Her friends prepare to worship the Sun-god; then She gets permission and leaves.",
    "Rādhā leaves the articles of worship at Sūrya's temple and anxiously goes to Rādhā-kuṇḍa.",
    "After briefly playing with His friends, Kṛṣṇa slips away and also goes to Rādhā-kuṇḍa.",
    "Arriving on the bank, He secretly observes Her beauty and becomes very agitated with love.",
    "She beholds His beauty and asks Her friends if He is a cloud; or Cupid personified, etc.",
    "An argument ensues over the supposed proprietorship of the forest; Lalitā chastises Him.",
    "Blissful swing pastimes, flute-stealing, colored water-squirting fun, forest wandering.",
    "Rādhā and Kṛṣṇa enter a grove and sport amorous pastimes; He expands to meet all sakhīs.",
    "The maidservants assemble items and worship Them when They come out of the grove.",
    "Served by Their friends, They begin water-sports, dressing, forest-feasting and dice-gambling.",
    "They enjoy the sport of drinking intoxicating honey-wine; indescribably wild activities ensue.",
    "More water-sports, then dry clothes; They listen to the parrots' recitations and then rest.",
    "They sit upon a jeweled throne and make jokes, but become sad as it is time to return home.",
    "Rādhā goes to Sūrya's temple; Kṛṣṇa meets His friends and also goes to Sūrya's temple.",
    "Kṛṣṇa disguised as the pūjārī conducts the bogus worship ceremony with prankish jokes.",
    "She returns home and rests, and He rejoins His cowherd boyfriends and plays many games.",
    "Kṛṣṇa heads to Vraja with the cows, passing Rādhā's residence; She then dresses and cooks.",
    "All the townspeople come out to greet Kṛṣṇa; Rādhā exchanges longing glances with Him.",
    "Kṛṣṇa goes to milk the cows, but instead has a snack with Rādhā; then He milks the cows.",
    "Yaśodā & Rohiṇī do Kṛṣṇa-Balarāma's ārati; Rādhā does ārati and sends edibles.",
    "Nanda comes home, fondles Kṛṣṇa and supervises the carrying of hundreds of milk pots.",
    "Nanda, Kṛṣṇa and Balarāma honor the evening meal; Yaśodā serves edibles sent by Rādhā.",
    "More eating fun; they finish and wash as Yaśodā sends remnants to Rādhā via Dhaniṣṭhā.",
    "Kṛṣṇa hears of plans for a secret meeting later; Dhaniṣṭhā brings prasāda to Rādhā and friends.",
    "Kṛṣṇa rests after eating, then goes to Nanda's auditorium; Rādhā finishes eating and rests.",
    "Kṛṣṇa enjoys watching performances and recitations, then Yaśodā calls Him to bed.",
    "After briefly resting, He sneaks out in great longing and goes to the assigned meeting grove.",
    "Rādhā gets up, washes and dresses nicely, then anxiously sends a messenger to Vṛndā.",
    "Assisted by the messenger, Rādhā leaves with Her sakhīs to rendezvous with Him.",
    "She reaches the grove on the bank of the Yamunā and waits inside; Kṛṣṇa comes near.",
    "He arrives and enters; now all become ecstatic, and They wander about the forest singing.",
    "The sakhīs fan Them as They sit in each other's laps and discuss confidential love-topics.",
    "They give the order to begin dancing, and all join in by singing and playing instruments.",
    "The rāsa-dance blossoms with circular formations, amazing movements and profuse music.",
    "They rest briefly and are dressed with cooling flowers, then soothed with refreshments.",
    "Reclining love-amusements, honey-wine, Yamunā water-sports, fresh dress, snack and rest.",
    "He and She give up all shyness and act out all Their amorous desires, face-to-face.",
    "They leave the grove to rest briefly, then re-enter where He adorns Her with ornaments.",
    "She orders Him to go from grove to grove visiting each and every one of Her sakhīs.",
    "He happily returns to Her grove; seeing Her dozing, He sneaks in and playfully assails Her.",
    "She is startled; They again fulfill Their desires, then drink honey-wine and rest some more.",
    "The sakhīs now enter and gently massage Their feet as They drift off to blissful repose.",
    "In the dead of night, some girls go to rest in their own groves, while some remain watching.",
]


def main():
    if len(sys.argv) < 2:
        print("usage: populate_dandas.py <input.sqlite> [<input.sqlite> ...]")
        sys.exit(1)

    for db_path in sys.argv[1:]:
        con = sqlite3.connect(db_path)
        cur = con.cursor()

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS dandas (
                id INTEGER PRIMARY KEY,
                main_period_id INTEGER NOT NULL REFERENCES period_nodes(id),
                sort_order INTEGER NOT NULL,
                time_start TEXT,
                time_end TEXT,
                description_key TEXT
            )
            """
        )

        cur.execute("DELETE FROM dandas")
        cur.execute("DELETE FROM translations WHERE translation_key LIKE 'period.danda.%'")

        for n in range(1, 61):
            start, end = DANDA_TIMES[n - 1]
            key = f"period.danda.{n}.desc"
            cur.execute(
                """
                INSERT INTO dandas
                    (id, main_period_id, sort_order, time_start, time_end, description_key)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (n, MAIN_PERIOD_BY_DANDA[n], n, start, end, key),
            )
            cur.execute(
                "INSERT INTO translations (language_id, translation_key, translated_text) VALUES (1, ?, ?)",
                (key, DANDA_DESCRIPTIONS[n - 1]),
            )

        con.commit()
        n_dandas = cur.execute("SELECT COUNT(*) FROM dandas").fetchone()[0]
        con.close()
        print(f"{db_path}: {n_dandas} dandas inserted")


if __name__ == "__main__":
    main()
