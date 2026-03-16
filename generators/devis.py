"""
Générateur de devis français (PDF + ground truth JSON).
"""
import random
import uuid
from datetime import date, timedelta

from fpdf import FPDF

from utils.faker_helpers import (
    generate_siret,
    generate_tva_intra,
    random_company_name,
    random_address,
)

_PRESTATIONS = [
    ("Développement d'application web", 600, 2500),
    ("Refonte graphique site internet", 400, 1800),
    ("Audit de sécurité informatique", 800, 3500),
    ("Rédaction de cahier des charges", 300, 1200),
    ("Formation Python avancé", 400, 1600),
    ("Intégration API tierce", 500, 2000),
    ("Mise en place CI/CD", 300, 1400),
    ("Conseil en organisation", 700, 2800),
    ("Création de contenu marketing", 200, 900),
    ("Déploiement infrastructure cloud", 500, 2200),
]

_CONDITIONS = (
    "Devis etabli sur la base des informations fournies par le client. "
    "Toute modification du perimetre fera l'objet d'un avenant. "
    "Un acompte de 30 % est demande a la signature. "
    "Delai d'execution : 4 a 8 semaines apres reception de l'acompte."
)


def _random_lines() -> list[dict]:
    n = random.randint(1, 6)
    return [
        {
            "description": p[0],
            "quantite": random.randint(1, 8),
            "pu_ht": round(random.uniform(p[1], p[2]), 2),
        }
        for p in random.sample(_PRESTATIONS, n)
    ]


def _build_amounts(lines: list[dict], scenario: str) -> tuple[float, float, float]:
    ht = round(sum(l["quantite"] * l["pu_ht"] for l in lines), 2)
    if scenario in ("tva_incoherente", "falsifie"):
        wrong_rate = random.choice([0.05, 0.08, 0.12, 0.15])
        tva = round(ht * wrong_rate, 2)
    else:
        tva = round(ht * 0.20, 2)
    ttc = round(ht + tva, 2)
    return ht, tva, ttc


def _build_pdf(
    numero: str,
    date_emission: date,
    date_validite: date,
    fournisseur: dict,
    client: dict,
    lines: list[dict],
    ht: float,
    tva: float,
    ttc: float,
) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(20, 20, 20)

    # Titre
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 10, "DEVIS", ln=True, align="C")
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(255, 200, 0)
    validite_str = date_validite.strftime("%d/%m/%Y")
    pdf.cell(
        0, 7,
        f"Devis valable jusqu'au {validite_str}",
        ln=True, align="C", fill=True,
    )
    pdf.ln(4)

    # En-têtes fournisseur / numéro
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(95, 6, fournisseur["nom"], ln=False)
    pdf.cell(95, 6, f"Devis N° : {numero}", ln=True, align="R")

    pdf.set_font("Helvetica", "", 9)
    for line in fournisseur["adresse"].split("\n"):
        pdf.cell(95, 5, line, ln=False)
        pdf.cell(95, 5, "", ln=True)

    pdf.cell(95, 5, f"SIRET : {fournisseur['siret']}", ln=False)
    pdf.cell(95, 5, f"Date d'emission : {date_emission.strftime('%d/%m/%Y')}", ln=True, align="R")
    pdf.cell(95, 5, f"TVA : {fournisseur['tva_intra']}", ln=True)
    pdf.ln(6)

    # Client
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, "DEVIS ETABLI POUR :", ln=True, fill=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, client["nom"], ln=True)
    for line in client["adresse"].split("\n"):
        pdf.cell(0, 5, line, ln=True)
    pdf.cell(0, 5, f"SIRET : {client['siret']}", ln=True)
    pdf.ln(6)

    # Tableau
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(0, 100, 60)
    pdf.set_text_color(255, 255, 255)
    col_w = [85, 20, 30, 35]
    for w, h in zip(col_w, ["Description de la prestation", "Qte", "PU HT (EUR)", "Total HT (EUR)"]):
        pdf.cell(w, 7, h, border=1, fill=True, align="C")
    pdf.ln()

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 9)
    fill = False
    for l in lines:
        total_ligne = round(l["quantite"] * l["pu_ht"], 2)
        pdf.set_fill_color(235, 255, 235) if fill else pdf.set_fill_color(255, 255, 255)
        pdf.cell(col_w[0], 6, l["description"], border=1, fill=True)
        pdf.cell(col_w[1], 6, str(l["quantite"]), border=1, align="C", fill=True)
        pdf.cell(col_w[2], 6, f"{l['pu_ht']:.2f}", border=1, align="R", fill=True)
        pdf.cell(col_w[3], 6, f"{total_ligne:.2f}", border=1, align="R", fill=True)
        pdf.ln()
        fill = not fill

    # Totaux
    pdf.ln(4)
    x_offset = 120
    pdf.set_font("Helvetica", "", 9)
    pdf.set_x(x_offset)
    pdf.cell(40, 6, "Sous-total HT :", align="R")
    pdf.cell(30, 6, f"{ht:.2f} EUR", border=1, align="R", ln=True)

    pdf.set_x(x_offset)
    pdf.cell(40, 6, "TVA 20 % :", align="R")
    pdf.cell(30, 6, f"{tva:.2f} EUR", border=1, align="R", ln=True)

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_x(x_offset)
    pdf.set_fill_color(0, 100, 60)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(40, 7, "TOTAL TTC :", align="R")
    pdf.cell(30, 7, f"{ttc:.2f} EUR", border=1, align="R", fill=True, ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(8)

    # Conditions
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 6, "CONDITIONS GENERALES", ln=True)
    pdf.set_font("Helvetica", "I", 7)
    pdf.multi_cell(0, 4, _CONDITIONS)
    pdf.ln(4)

    # Signature
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(95, 6, "Bon pour accord :", ln=False)
    pdf.cell(95, 6, "Signature du prestataire :", ln=True)
    pdf.ln(12)
    pdf.cell(95, 6, "Date : ____________________", ln=False)
    pdf.cell(95, 6, "Date : ____________________", ln=True)

    return bytes(pdf.output())


def generate_devis(
    scenario: str,
    team_names: list[str] | None = None,
) -> tuple[bytes, dict]:
    doc_id = str(uuid.uuid4())
    numero = f"DEV-{random.randint(2020, 2025)}-{random.randint(1000, 9999)}"

    date_emission = date.today() - timedelta(days=random.randint(0, 60))

    # date_expiree : date de validité dans le passé
    if scenario in ("date_expiree", "falsifie"):
        date_validite = date_emission + timedelta(days=random.randint(1, 30))
        # S'assurer qu'elle est expirée
        if date_validite >= date.today():
            date_validite = date.today() - timedelta(days=random.randint(1, 60))
    else:
        date_validite = date_emission + timedelta(days=90)

    siret_fournisseur = generate_siret()
    siret_client = generate_siret()
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

    pdf_bytes = _build_pdf(
        numero, date_emission, date_validite,
        fournisseur, client, lines, ht, tva, ttc,
    )

    anomalies = []
    if siret_incoherent:
        anomalies.append("SIRET_INCOHERENT")
    if date_validite < date.today():
        anomalies.append("DATE_EXPIREE")
    tva_correcte = round(ht * 0.20, 2)
    if abs(tva - tva_correcte) > 0.01:
        anomalies.append("TVA_INCOHERENTE")

    ground_truth = {
        "id": doc_id,
        "type": "devis",
        "scenario": scenario,
        "fournisseur": {
            "nom": nom_fournisseur,
            "siret": siret_fournisseur,
            "adresse": adresse_fournisseur,
        },
        "client": {
            "nom": nom_client,
            "siret": siret_client,
        },
        "montant_ht": ht,
        "tva_taux": 20,
        "tva_montant": tva,
        "montant_ttc": ttc,
        "date_emission": date_emission.isoformat(),
        "date_echeance": date_validite.isoformat(),
        "numero_document": numero,
        "coherent": len(anomalies) == 0,
        "anomalies": anomalies,
    }

    if siret_incoherent:
        ground_truth["siret_attendu"] = siret_fournisseur
        ground_truth["siret_reel"] = siret_affiche

    return pdf_bytes, ground_truth
