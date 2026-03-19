"""
Générateur de factures françaises (PDF + ground truth JSON).
"""
import random
import uuid
from datetime import date, timedelta

from fpdf import FPDF

from utils.faker_helpers import (
    generate_siret,
    generate_tva_intra,
    generate_rib_data,
    random_company_name,
    random_address,
)

# ---------------------------------------------------------------------------
# Helpers internes
# ---------------------------------------------------------------------------

_PRODUITS = [
    ("Développement logiciel", 500, 2000),
    ("Conseil en stratégie", 800, 3000),
    ("Maintenance informatique", 200, 800),
    ("Formation professionnelle", 300, 1500),
    ("Audit et expertise", 400, 2500),
    ("Prestation de service", 150, 600),
    ("Fournitures de bureau", 20, 200),
    ("Location matériel", 100, 500),
    ("Hébergement cloud", 50, 400),
    ("Rédaction de contenu", 100, 800),
]

_MENTIONS_LEGALES = (
    "En cas de retard de paiement, une pénalité de 3 fois le taux d'intérêt légal sera appliquée, "
    "ainsi qu'une indemnité forfaitaire pour frais de recouvrement de 40 EUR (art. L.441-10 C.com). "
    "Pas d'escompte pour paiement anticipé. TVA non applicable - art. 293B du CGI si applicable."
)


def _random_lines() -> list[dict]:
    """Génère 1 à 5 lignes de facturation aléatoires."""
    n = random.randint(1, 5)
    lines = []
    for _ in range(n):
        desc, low, high = random.choice(_PRODUITS)
        qty = random.randint(1, 10)
        pu_ht = round(random.uniform(low, high), 2)
        lines.append({"description": desc, "quantite": qty, "pu_ht": pu_ht})
    return lines


def _build_amounts(lines: list[dict], scenario: str) -> tuple[float, float, float]:
    """Calcule HT, TVA, TTC avec éventuelle anomalie."""
    ht = round(sum(l["quantite"] * l["pu_ht"] for l in lines), 2)
    tva_taux = 0.20
    tva_normal = round(ht * tva_taux, 2)

    if scenario in ("tva_incoherente", "falsifie"):
        # Taux erroné (entre 5 % et 15 %)
        wrong_rate = random.choice([0.05, 0.10, 0.055, 0.085, 0.15])
        tva_montant = round(ht * wrong_rate, 2)
    else:
        tva_montant = tva_normal

    ttc = round(ht + tva_montant, 2)
    return ht, tva_montant, ttc


# ---------------------------------------------------------------------------
# Génération PDF
# ---------------------------------------------------------------------------

def _build_pdf(
    doc_id: str,
    numero: str,
    date_emission: date,
    date_echeance: date,
    fournisseur: dict,
    client: dict,
    lines: list[dict],
    ht: float,
    tva: float,
    ttc: float,
    rib: dict,
) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(20, 20, 20)

    # --- En-tête fournisseur ---
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 10, "FACTURE", ln=True, align="C")
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(95, 6, fournisseur["nom"], ln=False)
    pdf.cell(95, 6, f"Facture N° : {numero}", ln=True, align="R")

    pdf.set_font("Helvetica", "", 9)
    for line in fournisseur["adresse"].split("\n"):
        pdf.cell(95, 5, line, ln=False)
        pdf.cell(95, 5, "", ln=True)

    pdf.set_font("Helvetica", "", 9)
    pdf.cell(95, 5, f"SIRET : {fournisseur['siret']}", ln=False)
    pdf.cell(95, 5, f"Date d'emission : {date_emission.strftime('%d/%m/%Y')}", ln=True, align="R")

    pdf.cell(95, 5, f"TVA : {fournisseur['tva_intra']}", ln=False)
    pdf.cell(95, 5, f"Date d'echeance : {date_echeance.strftime('%d/%m/%Y')}", ln=True, align="R")
    pdf.ln(6)

    # --- Client ---
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, "FACTURER A :", ln=True, fill=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, client["nom"], ln=True)
    for line in client["adresse"].split("\n"):
        pdf.cell(0, 5, line, ln=True)
    pdf.cell(0, 5, f"SIRET : {client['siret']}", ln=True)
    pdf.ln(6)

    # --- Tableau des lignes ---
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(50, 50, 120)
    pdf.set_text_color(255, 255, 255)
    col_w = [85, 20, 30, 35]
    headers = ["Description", "Qte", "PU HT (EUR)", "Total HT (EUR)"]
    for w, h in zip(col_w, headers):
        pdf.cell(w, 7, h, border=1, fill=True, align="C")
    pdf.ln()

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 9)
    fill = False
    for l in lines:
        total_ligne = round(l["quantite"] * l["pu_ht"], 2)
        pdf.set_fill_color(240, 245, 255) if fill else pdf.set_fill_color(255, 255, 255)
        pdf.cell(col_w[0], 6, l["description"], border=1, fill=True)
        pdf.cell(col_w[1], 6, str(l["quantite"]), border=1, align="C", fill=True)
        pdf.cell(col_w[2], 6, f"{l['pu_ht']:.2f}", border=1, align="R", fill=True)
        pdf.cell(col_w[3], 6, f"{total_ligne:.2f}", border=1, align="R", fill=True)
        pdf.ln()
        fill = not fill

    # --- Totaux ---
    pdf.ln(4)
    x_offset = 120
    pdf.set_font("Helvetica", "", 9)
    pdf.set_x(x_offset)
    pdf.cell(40, 6, "Sous-total HT :", border=0, align="R")
    pdf.cell(30, 6, f"{ht:.2f} EUR", border=1, align="R", ln=True)

    pdf.set_x(x_offset)
    pdf.cell(40, 6, "TVA 20 % :", border=0, align="R")
    pdf.cell(30, 6, f"{tva:.2f} EUR", border=1, align="R", ln=True)

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_x(x_offset)
    pdf.set_fill_color(50, 50, 120)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(40, 7, "TOTAL TTC :", border=0, align="R")
    pdf.cell(30, 7, f"{ttc:.2f} EUR", border=1, align="R", fill=True, ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(8)

    # --- RIB ---
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 6, "COORDONNEES BANCAIRES", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, f"Banque : {rib['banque']}", ln=True)
    pdf.cell(0, 5, f"IBAN : {rib['iban']}", ln=True)
    pdf.cell(0, 5, f"BIC : {rib['bic']}", ln=True)
    pdf.ln(6)

    # --- Mentions légales ---
    pdf.set_font("Helvetica", "I", 7)
    pdf.multi_cell(0, 4, _MENTIONS_LEGALES)

    return bytes(pdf.output())


# ---------------------------------------------------------------------------
# Entrée publique
# ---------------------------------------------------------------------------

def generate_facture(
    scenario: str,
    team_names: list[str] | None = None,
) -> tuple[bytes, dict]:
    """
    Génère une facture PDF et son ground truth.

    Returns:
        (pdf_bytes, ground_truth_dict)
    """
    doc_id = str(uuid.uuid4())
    numero = f"FAC-{random.randint(2020, 2025)}-{random.randint(1000, 9999)}"

    date_emission = date.today() - timedelta(days=random.randint(0, 90))
    date_echeance = date_emission + timedelta(days=random.choice([30, 45, 60]))

    siret_fournisseur = generate_siret()
    siret_client = generate_siret()

    # Scénario SIRET incohérent : on stocke un SIRET "attendu" différent
    siret_incoherent = scenario in ("siret_incoherent", "falsifie")
    siret_affiche = generate_siret() if siret_incoherent else siret_fournisseur

    nom_fournisseur = random_company_name(team_names)
    nom_client = random_company_name(team_names)
    adresse_fournisseur = random_address()
    adresse_client = random_address()

    fournisseur = {
        "nom": nom_fournisseur,
        "siret": siret_affiche,
        "adresse": adresse_fournisseur,
        "tva_intra": generate_tva_intra(siret_affiche),
    }
    client = {
        "nom": nom_client,
        "siret": siret_client,
        "adresse": adresse_client,
    }

    lines = _random_lines()
    ht, tva, ttc = _build_amounts(lines, scenario)
    rib = generate_rib_data()

    pdf_bytes = _build_pdf(
        doc_id, numero, date_emission, date_echeance,
        fournisseur, client, lines, ht, tva, ttc, rib,
    )

    # --- Anomalies ---
    anomalies = []
    if siret_incoherent:
        anomalies.append("SIRET_INCOHERENT")
    tva_correcte = round(ht * 0.20, 2)
    if abs(tva - tva_correcte) > 0.01:
        anomalies.append("TVA_INCOHERENTE")

    ground_truth = {
        "id": doc_id,
        "type": "facture",
        "scenario": scenario,
        "fournisseur": {
            "nom": nom_fournisseur,
            "siret": siret_fournisseur,   # SIRET réel
            "adresse": adresse_fournisseur,
        },
        "client": {
            "nom": nom_client,
            "siret": siret_client,
        },
        "montant_ht": ht,
        "tva_rate": 20.0,
        "tva_montant": tva,
        "montant_ttc": ttc,
        "date_emission": date_emission.isoformat(),
        "date_expiration": date_echeance.isoformat(),
        "numero_document": numero,
        "coherent": len(anomalies) == 0,
        "anomalies": anomalies,
    }

    if siret_incoherent:
        ground_truth["siret_attendu"] = siret_fournisseur
        ground_truth["siret_reel"] = siret_affiche

    return pdf_bytes, ground_truth
