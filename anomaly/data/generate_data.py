"""
Génère un fichier mes_factures.csv avec des milliers de factures réalistes.
"""

import csv
import random

random.seed(42)

OUTPUT = str(__import__("pathlib").Path(__file__).parent.parent / "data" / "mes_factures.csv")

ENTREPRISES = [
    ("44306184100047", 500, 8000, [20.0], 0.94, 150),
    ("10000000410009", 15000, 50000, [20.0], 0.92, 150),
    ("32345678901234", 20000, 120000, [20.0], 0.91, 150),
    ("45678901234567", 200, 3000, [5.5, 10.0], 0.95, 150),
    ("56789012345678", 3000, 25000, [20.0], 0.96, 150),
    ("67890123456789", 1000, 40000, [20.0], 0.90, 150),
    ("78901234567890", 50, 2000, [20.0, 5.5], 0.97, 150),
    ("89012345678901", 800, 5000, [20.0], 0.93, 150),
    ("90123456789012", 5000, 80000, [20.0], 0.94, 150),
    ("11223344556677", 10000, 100000, [0.0], 0.92, 150),
]

rows = []

for siret, m_min, m_max, tva_rates, ocr_mean, nb in ENTREPRISES:
    for _ in range(nb):
        montant_ht = round(random.uniform(m_min, m_max), 2)
        tva = random.choice(tva_rates)
        montant_ttc = round(montant_ht * (1 + tva / 100), 2)
        ocr = round(min(0.99, max(0.80, random.gauss(ocr_mean, 0.03))), 2)
        rows.append([siret, montant_ht, montant_ttc, tva, ocr])

for _ in range(1000):
    siret = str(random.randint(10000000000000, 99999999999999))
    montant_ht = round(random.uniform(100, 60000), 2)
    tva = random.choice([0.0, 5.5, 10.0, 20.0, 20.0, 20.0])
    montant_ttc = round(montant_ht * (1 + tva / 100), 2)
    ocr = round(min(0.99, max(0.80, random.gauss(0.93, 0.04))), 2)
    rows.append([siret, montant_ht, montant_ttc, tva, ocr])

random.shuffle(rows)

with open(OUTPUT, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["siret", "montant_ht", "montant_ttc", "tva_rate", "ocr_confidence"])
    writer.writerows(rows)

print(f"{len(rows)} factures générées dans {OUTPUT}")
