"""
Tests standalone du moteur de detection de fraude.
Utilise les entreprises du fichier mes_factures.csv.
Lance : python -m tests.test_real
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fraud_detector import detect


def test(name, payload):
    r = detect(payload)
    rules = [a["rule"] for a in r["anomalies"]]
    print(f"\n{'='*60}")
    print(f"{name}")
    print(f"  status={r['status']} | score={r['anomaly_score']} | confidence={r['confidence_score']}")
    print(f"  regles declenchees: {rules if rules else 'aucune'}")
    for a in r["anomalies"]:
        print(f"    [{a['rule']}] {a['severity']}: {a['description'][:80]}...")
    return r


# ============================================================
# TESTS REGLES INDIVIDUELLES (R1 a R7)
# ============================================================

test("R1 - SIRET different entre facture et URSSAF", {
    "file_id": "r1", "doc_type": "FACTURE",
    "ocr_confidence": 0.94, "classification_confidence": 0.89,
    "fields": {"siret": "44306184100047"},
    "related_docs": [
        {"doc_type": "ATTESTATION_URSSAF", "fields": {"siret": "10000000410009", "date_expiration": "2027-01-01"}},
    ]
})

test("R2 - Attestation URSSAF expiree", {
    "file_id": "r2", "doc_type": "FACTURE",
    "ocr_confidence": 0.94, "classification_confidence": 0.89,
    "fields": {"siret": "44306184100047"},
    "related_docs": [
        {"doc_type": "ATTESTATION_URSSAF", "fields": {"siret": "44306184100047", "date_expiration": "2020-06-01"}},
    ]
})

test("R3 - TVA 15% (taux non legal)", {
    "file_id": "r3", "doc_type": "FACTURE",
    "ocr_confidence": 0.94, "classification_confidence": 0.89,
    "fields": {"siret": "44306184100047", "montant_ht": 1000, "montant_ttc": 1150, "tva_rate": 15.0},
})

test("R4 - Calcul TTC incoherent (HT=1000 + TVA 20% devrait faire 1200, pas 1500)", {
    "file_id": "r4", "doc_type": "FACTURE",
    "ocr_confidence": 0.94, "classification_confidence": 0.89,
    "fields": {"siret": "44306184100047", "montant_ht": 1000, "montant_ttc": 1500, "tva_rate": 20.0},
})

test("R5 - IBAN trop court", {
    "file_id": "r5a", "doc_type": "FACTURE",
    "ocr_confidence": 0.94, "classification_confidence": 0.89,
    "fields": {"siret": "44306184100047", "iban": "FR76FAKE"},
})

test("R5 - IBAN checksum invalide", {
    "file_id": "r5b", "doc_type": "FACTURE",
    "ocr_confidence": 0.94, "classification_confidence": 0.89,
    "fields": {"siret": "44306184100047", "iban": "FR7699999999999999999999999"},
})

test("R6 - Date emission dans le futur", {
    "file_id": "r6", "doc_type": "FACTURE",
    "ocr_confidence": 0.94, "classification_confidence": 0.89,
    "fields": {"siret": "44306184100047", "date_emission": "2099-12-31"},
})

test("R7 - SIRET trop court (3 chiffres)", {
    "file_id": "r7a", "doc_type": "FACTURE",
    "ocr_confidence": 0.94, "classification_confidence": 0.89,
    "fields": {"siret": "123"},
})

test("R7 - SIRET 14 chiffres mais Luhn invalide", {
    "file_id": "r7b", "doc_type": "FACTURE",
    "ocr_confidence": 0.94, "classification_confidence": 0.89,
    "fields": {"siret": "99999999999999"},
})

# ============================================================
# CAS OK - Aucune anomalie attendue
# ============================================================

test("OK - Petit fournisseur (500-8k), facture 3000", {
    "file_id": "ok-1", "doc_type": "FACTURE",
    "ocr_confidence": 0.94, "classification_confidence": 0.89,
    "fields": {
        "siret": "44306184100047", "montant_ht": 3000,
        "montant_ttc": 3600, "tva_rate": 20.0, "date_emission": "2025-06-01",
        "iban": "FR7630006000011234567890189",
    },
    "related_docs": [
        {"doc_type": "ATTESTATION_URSSAF", "fields": {"siret": "44306184100047", "date_expiration": "2027-01-01"}},
        {"doc_type": "EXTRAIT_KBIS", "fields": {"siret": "44306184100047"}},
    ]
})

test("OK - BTP (20k-120k), facture 55000", {
    "file_id": "ok-2", "doc_type": "FACTURE",
    "ocr_confidence": 0.91, "classification_confidence": 0.88,
    "fields": {
        "siret": "32345678901234", "montant_ht": 55000,
        "montant_ttc": 66000, "tva_rate": 20.0, "date_emission": "2025-03-10",
    },
    "related_docs": [
        {"doc_type": "ATTESTATION_URSSAF", "fields": {"siret": "32345678901234", "date_expiration": "2027-06-01"}},
    ]
})

test("OK - Restauration (200-3k), facture 1200 TVA 10%", {
    "file_id": "ok-3", "doc_type": "FACTURE",
    "ocr_confidence": 0.95, "classification_confidence": 0.92,
    "fields": {
        "siret": "45678901234567", "montant_ht": 1200,
        "montant_ttc": 1320, "tva_rate": 10.0, "date_emission": "2025-09-15",
    },
})

# ============================================================
# ML - Montants anormaux par rapport au profil SIRET
# ============================================================

test("ML - Petit fournisseur (500-8k) envoie 80k", {
    "file_id": "ml-1", "doc_type": "FACTURE",
    "ocr_confidence": 0.94, "classification_confidence": 0.89,
    "fields": {
        "siret": "44306184100047", "montant_ht": 80000,
        "montant_ttc": 96000, "tva_rate": 20.0,
    },
})

test("ML - BTP (20k-120k) envoie 500", {
    "file_id": "ml-2", "doc_type": "FACTURE",
    "ocr_confidence": 0.91, "classification_confidence": 0.88,
    "fields": {
        "siret": "32345678901234", "montant_ht": 500,
        "montant_ttc": 600, "tva_rate": 20.0,
    },
})

test("ML - Restauration (200-3k) envoie 50k", {
    "file_id": "ml-3", "doc_type": "FACTURE",
    "ocr_confidence": 0.95, "classification_confidence": 0.92,
    "fields": {
        "siret": "45678901234567", "montant_ht": 50000,
        "montant_ttc": 55000, "tva_rate": 10.0,
    },
})

test("ML - Cabinet conseil (3k-25k) envoie 200k", {
    "file_id": "ml-4", "doc_type": "FACTURE",
    "ocr_confidence": 0.96, "classification_confidence": 0.90,
    "fields": {
        "siret": "56789012345678", "montant_ht": 200000,
        "montant_ttc": 240000, "tva_rate": 20.0,
    },
})

test("ML - Transport (1k-40k) envoie 300k", {
    "file_id": "ml-5", "doc_type": "FACTURE",
    "ocr_confidence": 0.90, "classification_confidence": 0.87,
    "fields": {
        "siret": "67890123456789", "montant_ht": 300000,
        "montant_ttc": 360000, "tva_rate": 20.0,
    },
})

test("ML - Nettoyage (800-5k) envoie 60k", {
    "file_id": "ml-6", "doc_type": "FACTURE",
    "ocr_confidence": 0.93, "classification_confidence": 0.89,
    "fields": {
        "siret": "89012345678901", "montant_ht": 60000,
        "montant_ttc": 72000, "tva_rate": 20.0,
    },
})

test("ML - Fournitures (50-2k) envoie 25k", {
    "file_id": "ml-7", "doc_type": "FACTURE",
    "ocr_confidence": 0.97, "classification_confidence": 0.93,
    "fields": {
        "siret": "78901234567890", "montant_ht": 25000,
        "montant_ttc": 30000, "tva_rate": 20.0,
    },
})

test("ML - Export (10k-100k) envoie 800k TVA 0%", {
    "file_id": "ml-8", "doc_type": "FACTURE",
    "ocr_confidence": 0.92, "classification_confidence": 0.88,
    "fields": {
        "siret": "11223344556677", "montant_ht": 800000,
        "montant_ttc": 800000, "tva_rate": 0.0,
    },
})

# ============================================================
# MIX - Regles metier + ML combines
# ============================================================

test("MIX - ML + R1 + R2 (montant anormal + SIRET diff + URSSAF expiree)", {
    "file_id": "mix-1", "doc_type": "FACTURE",
    "ocr_confidence": 0.88, "classification_confidence": 0.82,
    "fields": {
        "siret": "44306184100047", "montant_ht": 90000,
        "montant_ttc": 108000, "tva_rate": 20.0,
    },
    "related_docs": [
        {"doc_type": "ATTESTATION_URSSAF", "fields": {"siret": "10000000410009", "date_expiration": "2022-01-01"}},
    ]
})

test("MIX - ML + R3 + R4 (montant anormal + TVA illegale + TTC faux)", {
    "file_id": "mix-2", "doc_type": "FACTURE",
    "ocr_confidence": 0.93, "classification_confidence": 0.89,
    "fields": {
        "siret": "89012345678901", "montant_ht": 50000,
        "montant_ttc": 70000, "tva_rate": 15.0,
    },
})

test("MIX - ML + R5 + R6 (montant anormal + IBAN KO + date future)", {
    "file_id": "mix-3", "doc_type": "FACTURE",
    "ocr_confidence": 0.90, "classification_confidence": 0.85,
    "fields": {
        "siret": "45678901234567", "montant_ht": 40000,
        "montant_ttc": 44000, "tva_rate": 10.0,
        "iban": "FR76BIDON123", "date_emission": "2099-01-01",
    },
})

test("CHAOS - Toutes les regles R1+R2+R3+R4+R5+R6+R7+ML", {
    "file_id": "chaos", "doc_type": "FACTURE",
    "ocr_confidence": 0.40, "classification_confidence": 0.35,
    "fields": {
        "siret": "999", "montant_ht": 999999,
        "montant_ttc": 50000, "tva_rate": 13.0,
        "date_emission": "2099-01-01", "iban": "FR76FAKE",
    },
    "related_docs": [
        {"doc_type": "ATTESTATION_URSSAF", "fields": {"siret": "44306184100047", "date_expiration": "2019-01-01"}},
        {"doc_type": "EXTRAIT_KBIS", "fields": {"siret": "10000000410009"}},
    ]
})
