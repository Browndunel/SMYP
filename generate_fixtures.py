"""
Génère 7 fixtures de test déterministes dans dataset/output/test_fixtures/.

Chaque fixture produit :
  - un fichier document (PDF ou PNG ou JPG)
  - un JSON ground truth {nom_fixture}_ground_truth.json

Usage :
    python generate_fixtures.py
    make fixtures
"""
from __future__ import annotations

import json
import random
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
import pypdfium2 as pdfium
from PIL import Image, ImageFilter

# Graine fixe pour la reproductibilité (RIB aléatoire dans les fixtures)
random.seed(0)
np.random.seed(0)

from generators.facture import _build_pdf as _build_facture_pdf
from generators.attestation_urssaf import _build_pdf as _build_attestation_pdf
from utils.faker_helpers import generate_rib_data, generate_tva_intra

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

YONI_SIRET = "12345678901234"
OUTPUT_DIR = Path("dataset/output/test_fixtures")
DPI = 150

_YONI_FOURNISSEUR = {
    "nom": "Yoni SAS",
    "siret": YONI_SIRET,
    "adresse": "1 Rue de la Paix\n75001 Paris",
    "tva_intra": generate_tva_intra(YONI_SIRET),
}
_CLIENT_TEST = {
    "nom": "Client Test SARL",
    "siret": "98765432100012",
    "adresse": "10 Avenue Victor Hugo\n69001 Lyon",
}
_LINES_BASE = [
    {"description": "Développement logiciel", "quantite": 1, "pu_ht": 1000.00}
]
_DATE_EMISSION = date(2024, 1, 15)
_DATE_ECHEANCE = date(2024, 2, 14)

# RIB fixe (généré une fois avec seed=0)
_RIB_FIXTURE = generate_rib_data()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pdf_to_pil(pdf_bytes: bytes) -> Image.Image:
    """Convertit la première page du PDF en PIL Image."""
    pdf_doc = pdfium.PdfDocument(pdf_bytes)
    page = pdf_doc[0]
    bitmap = page.render(scale=DPI / 72)
    return bitmap.to_pil()


def _write_gt(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _base_facture_gt(
    doc_name: str,
    siret_reel: str,
    montant_ht: float,
    tva: float,
    ttc: float,
    anomalies: list[str],
    extra: dict | None = None,
) -> dict:
    gt: dict = {
        "fixture": doc_name,
        "type": "facture",
        "scenario": "siret_incoherent" if "SIRET_INCOHERENT" in anomalies
                    else "tva_incoherente" if "TVA_INCOHERENTE" in anomalies
                    else "normal",
        "fournisseur": {
            "nom": "Yoni SAS",
            "siret": siret_reel,
            "adresse": "1 Rue de la Paix\n75001 Paris",
        },
        "client": {"nom": _CLIENT_TEST["nom"], "siret": _CLIENT_TEST["siret"]},
        "montant_ht": montant_ht,
        "tva_taux": 20,
        "tva_montant": tva,
        "montant_ttc": ttc,
        "date_emission": _DATE_EMISSION.isoformat(),
        "date_echeance": _DATE_ECHEANCE.isoformat(),
        "numero_document": "FAC-2024-0001",
        "coherent": len(anomalies) == 0,
        "anomalies": anomalies,
    }
    if extra:
        gt.update(extra)
    return gt


# ---------------------------------------------------------------------------
# Génération des 7 fixtures
# ---------------------------------------------------------------------------

def generate_fixtures(output_dir: Path = OUTPUT_DIR) -> None:
    """Génère les 7 fixtures dans output_dir. Idempotent."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # 1. facture_yoni_sas_propre.pdf  — nominal propre
    # ------------------------------------------------------------------
    name = "facture_yoni_sas_propre"
    pdf_bytes = _build_facture_pdf(
        doc_id="fixture-yoni-sas-propre",
        numero="FAC-2024-0001",
        date_emission=_DATE_EMISSION,
        date_echeance=_DATE_ECHEANCE,
        fournisseur=_YONI_FOURNISSEUR,
        client=_CLIENT_TEST,
        lines=_LINES_BASE,
        ht=1000.00,
        tva=200.00,
        ttc=1200.00,
        rib=_RIB_FIXTURE,
    )
    (output_dir / f"{name}.pdf").write_bytes(pdf_bytes)
    _write_gt(
        output_dir / f"{name}_ground_truth.json",
        _base_facture_gt(name, YONI_SIRET, 1000.00, 200.00, 1200.00, []),
    )

    # ------------------------------------------------------------------
    # 2. facture_scan_flou.png  — nominal + GaussianBlur radius=2
    # ------------------------------------------------------------------
    name = "facture_scan_flou"
    img = _pdf_to_pil(pdf_bytes)
    blurred = img.filter(ImageFilter.GaussianBlur(radius=2))
    blurred.save(output_dir / f"{name}.png", format="PNG")
    _write_gt(
        output_dir / f"{name}_ground_truth.json",
        {
            **_base_facture_gt(name, YONI_SIRET, 1000.00, 200.00, 1200.00, []),
            "degradation": "gaussian_blur_radius_2",
        },
    )

    # ------------------------------------------------------------------
    # 3. facture_rotated_15.jpg  — nominal + rotation 15°
    # ------------------------------------------------------------------
    name = "facture_rotated_15"
    rotated = img.rotate(-15, expand=True, fillcolor=(255, 255, 255))
    rotated.save(output_dir / f"{name}.jpg", format="JPEG", quality=90)
    _write_gt(
        output_dir / f"{name}_ground_truth.json",
        {
            **_base_facture_gt(name, YONI_SIRET, 1000.00, 200.00, 1200.00, []),
            "degradation": "rotation_15deg",
        },
    )

    # ------------------------------------------------------------------
    # 4. facture_siret_mismatch.pdf  — SIRET affiché ≠ SIRET réel
    # ------------------------------------------------------------------
    name = "facture_siret_mismatch"
    siret_affiche = "99999999999999"
    fournisseur_mismatch = {
        **_YONI_FOURNISSEUR,
        "siret": siret_affiche,
        "tva_intra": generate_tva_intra(siret_affiche),
    }
    pdf_mismatch = _build_facture_pdf(
        doc_id="fixture-siret-mismatch",
        numero="FAC-2024-0002",
        date_emission=_DATE_EMISSION,
        date_echeance=_DATE_ECHEANCE,
        fournisseur=fournisseur_mismatch,
        client=_CLIENT_TEST,
        lines=_LINES_BASE,
        ht=1000.00,
        tva=200.00,
        ttc=1200.00,
        rib=_RIB_FIXTURE,
    )
    (output_dir / f"{name}.pdf").write_bytes(pdf_mismatch)
    _write_gt(
        output_dir / f"{name}_ground_truth.json",
        {
            **_base_facture_gt(name, YONI_SIRET, 1000.00, 200.00, 1200.00, ["SIRET_INCOHERENT"]),
            "siret_attendu": YONI_SIRET,
            "siret_reel": siret_affiche,
            "numero_document": "FAC-2024-0002",
        },
    )

    # ------------------------------------------------------------------
    # 5. attestation_siret_different.pdf  — SIRET Yoni SAS ≠ affiché
    # ------------------------------------------------------------------
    name = "attestation_siret_different"
    siret_att = "88888888888888"
    date_em = date(2024, 1, 15)
    date_exp = date(2025, 1, 15)
    periode_debut = date(2024, 1, 1)
    pdf_att_mismatch = _build_attestation_pdf(
        numero="ATT-880001-01",
        raison_sociale="Yoni SAS",
        siret=siret_att,
        adresse="1 Rue de la Paix - 75001 Paris",
        code_naf="6201Z",
        date_emission=date_em,
        date_expiration=date_exp,
        periode_debut=periode_debut,
        periode_fin=date_em,
    )
    (output_dir / f"{name}.pdf").write_bytes(pdf_att_mismatch)
    _write_gt(
        output_dir / f"{name}_ground_truth.json",
        {
            "fixture": name,
            "type": "attestation_urssaf",
            "scenario": "siret_incoherent",
            "fournisseur": {"nom": "Yoni SAS", "siret": YONI_SIRET, "adresse": "1 Rue de la Paix\n75001 Paris"},
            "client": {"nom": "", "siret": ""},
            "montant_ht": 0.0,
            "tva_taux": 0,
            "tva_montant": 0.0,
            "montant_ttc": 0.0,
            "date_emission": date_em.isoformat(),
            "date_echeance": date_exp.isoformat(),
            "numero_document": "ATT-880001-01",
            "coherent": False,
            "anomalies": ["SIRET_INCOHERENT"],
            "siret_attendu": YONI_SIRET,
            "siret_reel": siret_att,
        },
    )

    # ------------------------------------------------------------------
    # 6. attestation_urssaf_expiree.pdf  — date expirée
    # ------------------------------------------------------------------
    name = "attestation_urssaf_expiree"
    date_em2 = date(2021, 6, 1)
    date_exp2 = date(2022, 1, 1)
    periode_debut2 = date(2021, 4, 1)
    pdf_att_exp = _build_attestation_pdf(
        numero="ATT-EXPIR-01",
        raison_sociale="Louise Corp",
        siret="55566677788899",
        adresse="5 Rue Louise - 13001 Marseille",
        code_naf="7022Z",
        date_emission=date_em2,
        date_expiration=date_exp2,
        periode_debut=periode_debut2,
        periode_fin=date_em2,
    )
    (output_dir / f"{name}.pdf").write_bytes(pdf_att_exp)
    _write_gt(
        output_dir / f"{name}_ground_truth.json",
        {
            "fixture": name,
            "type": "attestation_urssaf",
            "scenario": "date_expiree",
            "fournisseur": {"nom": "Louise Corp", "siret": "55566677788899", "adresse": "5 Rue Louise\n13001 Marseille"},
            "client": {"nom": "", "siret": ""},
            "montant_ht": 0.0,
            "tva_taux": 0,
            "tva_montant": 0.0,
            "montant_ttc": 0.0,
            "date_emission": date_em2.isoformat(),
            "date_echeance": date_exp2.isoformat(),
            "numero_document": "ATT-EXPIR-01",
            "coherent": False,
            "anomalies": ["DATE_EXPIREE"],
        },
    )

    # ------------------------------------------------------------------
    # 7. facture_tva_15pct.pdf  — TVA incohérente (15 % au lieu de 20 %)
    # ------------------------------------------------------------------
    name = "facture_tva_15pct"
    fournisseur_brawn = {
        "nom": "Brawn Dunel SARL",
        "siret": "11122233344455",
        "adresse": "8 Boulevard Brawn\n33000 Bordeaux",
        "tva_intra": generate_tva_intra("11122233344455"),
    }
    client_tva = {
        "nom": "Client Tva SASU",
        "siret": "66677788899900",
        "adresse": "3 Place du Marché\n31000 Toulouse",
    }
    pdf_tva = _build_facture_pdf(
        doc_id="fixture-tva-15pct",
        numero="FAC-2024-0003",
        date_emission=_DATE_EMISSION,
        date_echeance=_DATE_ECHEANCE,
        fournisseur=fournisseur_brawn,
        client=client_tva,
        lines=_LINES_BASE,
        ht=1000.00,
        tva=150.00,
        ttc=1150.00,
        rib=_RIB_FIXTURE,
    )
    (output_dir / f"{name}.pdf").write_bytes(pdf_tva)
    _write_gt(
        output_dir / f"{name}_ground_truth.json",
        {
            "fixture": name,
            "type": "facture",
            "scenario": "tva_incoherente",
            "fournisseur": {
                "nom": "Brawn Dunel SARL",
                "siret": "11122233344455",
                "adresse": "8 Boulevard Brawn\n33000 Bordeaux",
            },
            "client": {"nom": client_tva["nom"], "siret": client_tva["siret"]},
            "montant_ht": 1000.00,
            "tva_taux": 20,
            "tva_montant": 150.00,
            "montant_ttc": 1150.00,
            "date_emission": _DATE_EMISSION.isoformat(),
            "date_echeance": _DATE_ECHEANCE.isoformat(),
            "numero_document": "FAC-2024-0003",
            "coherent": False,
            "anomalies": ["TVA_INCOHERENTE"],
        },
    )

    print(f"\n{'='*55}")
    print(f"  Fixtures générées dans : {output_dir.resolve()}")
    files = sorted(output_dir.iterdir())
    docs = [f for f in files if not f.name.endswith("_ground_truth.json")]
    gts = [f for f in files if f.name.endswith("_ground_truth.json")]
    print(f"  Documents : {len(docs)}")
    print(f"  Ground truths : {len(gts)}")
    for f in docs:
        print(f"    {f.name}")
    print(f"{'='*55}\n")


# ---------------------------------------------------------------------------
# Point d'entrée CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    generate_fixtures()
