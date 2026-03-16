"""
Générateur de RIB (Relevé d'Identité Bancaire) français (PDF + ground truth JSON).
"""
import random
import uuid
from datetime import date

from fpdf import FPDF

from utils.faker_helpers import (
    generate_siret,
    generate_rib_data,
    random_company_name,
    random_person_name,
    random_address,
)

_MENTIONS = (
    "Ce document est confidentiel. Toute utilisation frauduleuse de ces "
    "coordonnees bancaires est passible de poursuites penales. "
    "Conserver ce document en lieu sur."
)


def _build_pdf(
    titulaire: str,
    adresse: str,
    rib: dict,
    date_edition: date,
) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(25, 25, 25)

    # En-tête banque
    pdf.set_fill_color(0, 60, 120)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 12, rib["banque"].upper(), ln=True, align="C", fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(6)

    # Titre
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "RELEVE D'IDENTITE BANCAIRE", ln=True, align="C")
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, f"Edite le : {date_edition.strftime('%d/%m/%Y')}", ln=True, align="C")
    pdf.ln(6)

    # Titulaire
    pdf.set_fill_color(235, 245, 255)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, "TITULAIRE DU COMPTE", ln=True, fill=True)
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(50, 6, "Nom / Raison sociale :", ln=False)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 6, titulaire, ln=True)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(50, 6, "Adresse :", ln=False)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 6, adresse.replace("\n", " - "), ln=True)
    pdf.ln(6)

    # Coordonnées bancaires
    pdf.set_fill_color(235, 245, 255)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, "COORDONNEES BANCAIRES", ln=True, fill=True)
    pdf.ln(2)

    rows = [
        ("Banque :", rib["banque"]),
        ("Code banque :", rib["code_banque"]),
        ("Code guichet :", rib["code_guichet"]),
        ("Numero de compte :", rib["numero_compte"]),
        ("Cle RIB :", rib["cle_rib"]),
    ]
    for label, value in rows:
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(55, 6, label, ln=False)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 6, value, ln=True)
    pdf.ln(4)

    # IBAN / BIC (encadré)
    pdf.set_draw_color(0, 60, 120)
    pdf.set_line_width(0.8)
    pdf.set_fill_color(245, 250, 255)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 8, "COORDONNEES INTERNATIONALES", ln=True, fill=True, border=1)

    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(25, 8, "IBAN :", border="LR", ln=False)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, rib["iban"], border="R", ln=True, align="C")

    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(25, 8, "BIC :", border="LRB", ln=False)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, rib["bic"], border="RB", ln=True, align="C")
    pdf.set_line_width(0.2)
    pdf.ln(6)

    # Représentation schématique du RIB
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(0, 5, "REPRESENTATION NORMALISEE DU RIB", ln=True)
    pdf.set_font("Helvetica", "", 7)
    pdf.set_fill_color(245, 245, 245)

    headers = ["Banque", "Guichet", "N° Compte", "Cle"]
    widths = [30, 30, 55, 25]
    for w, h in zip(widths, headers):
        pdf.cell(w, 6, h, border=1, align="C", fill=True)
    pdf.ln()
    values = [rib["code_banque"], rib["code_guichet"], rib["numero_compte"], rib["cle_rib"]]
    for w, v in zip(widths, values):
        pdf.cell(w, 7, v, border=1, align="C")
    pdf.ln(8)

    # Mentions
    pdf.set_font("Helvetica", "I", 7)
    pdf.multi_cell(0, 4, _MENTIONS)

    return bytes(pdf.output())


def generate_rib(
    scenario: str,
    team_names: list[str] | None = None,
) -> tuple[bytes, dict]:
    doc_id = str(uuid.uuid4())
    numero = f"RIB-{uuid.uuid4().hex[:8].upper()}"

    # Pour le RIB, le titulaire peut être une personne physique ou morale
    if random.random() < 0.5:
        titulaire = random_company_name(team_names)
        siret = generate_siret()
    else:
        titulaire = random_person_name(team_names)
        siret = ""

    adresse = random_address()
    rib = generate_rib_data()
    date_edition = date.today()

    # Scénario falsifié : on remplace l'IBAN par une valeur incohérente
    anomalies = []
    if scenario == "falsifie":
        # IBAN avec checksum incorrect
        raw = rib["iban_raw"]
        # Modifier 2 chiffres au milieu
        chars = list(raw)
        pos = random.randint(4, len(chars) - 3)
        chars[pos] = str((int(chars[pos]) + random.randint(1, 8)) % 10)
        rib = {**rib, "iban": " ".join("".join(chars)[i:i+4] for i in range(0, len(chars), 4))}
        anomalies.append("IBAN_INCOHERENT")

    pdf_bytes = _build_pdf(titulaire, adresse, rib, date_edition)

    ground_truth = {
        "id": doc_id,
        "type": "rib",
        "scenario": scenario,
        "fournisseur": {
            "nom": titulaire,
            "siret": siret,
            "adresse": adresse,
        },
        "client": {"nom": "", "siret": ""},
        "montant_ht": 0.0,
        "tva_taux": 0,
        "tva_montant": 0.0,
        "montant_ttc": 0.0,
        "date_emission": date_edition.isoformat(),
        "date_echeance": "",
        "numero_document": numero,
        "coherent": len(anomalies) == 0,
        "anomalies": anomalies,
        "iban": rib["iban"],
        "bic": rib["bic"],
    }

    return pdf_bytes, ground_truth
