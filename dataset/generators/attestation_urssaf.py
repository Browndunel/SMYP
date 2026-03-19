"""
Générateur d'attestations de vigilance URSSAF (PDF + ground truth JSON).
"""
import random
import uuid
from datetime import date, timedelta

from fpdf import FPDF

from utils.faker_helpers import (
    generate_siret,
    random_company_name,
    random_address,
)

_CODE_NAF = [
    "6201Z", "6202A", "7022Z", "4321A", "4619B",
    "8559A", "7112B", "4669B", "5610A", "7010Z",
]

_TEXTE_ATTESTATION = (
    "L'URSSAF certifie que l'entreprise citee ci-dessus est a jour de ses "
    "obligations declaratives et de paiement a l'egard de l'organisme de "
    "recouvrement des cotisations de securite sociale et des contributions "
    "sociales au {date}.\n\n"
    "Cette attestation est delivree sous reserve du paiement des cotisations "
    "et contributions correspondant aux periodes et remunerations non encore "
    "exigibles, et sous reserve que les renseignements fournis par le cotisant "
    "permettant l'etablissement des bulletins de paie soient conformes a la "
    "realite.\n\n"
    "Cette attestation est valable jusqu'au {expiration}."
)


def _build_pdf(
    numero: str,
    raison_sociale: str,
    siret: str,
    adresse: str,
    code_naf: str,
    date_emission: date,
    date_expiration: date,
    periode_debut: date,
    periode_fin: date,
) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(20, 20, 20)

    # En-tête URSSAF
    pdf.set_fill_color(0, 80, 160)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 14, "URSSAF", ln=True, align="C", fill=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 6, "Union de Recouvrement des cotisations de Securite Sociale et d'Allocations Familiales", ln=True, align="C", fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(6)

    # Titre document
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "ATTESTATION DE VIGILANCE", ln=True, align="C")
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, f"N° {numero}", ln=True, align="C")
    pdf.ln(6)

    # Informations entreprise
    pdf.set_fill_color(235, 240, 255)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, "INFORMATIONS SUR L'ENTREPRISE", ln=True, fill=True)
    pdf.ln(2)

    rows = [
        ("Raison sociale :", raison_sociale),
        ("SIRET :", siret),
        ("Adresse du siege :", adresse.replace("\n", " - ")),
        ("Code NAF :", code_naf),
    ]
    pdf.set_font("Helvetica", "", 9)
    for label, value in rows:
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(55, 6, label, ln=False)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 6, value, ln=True)
    pdf.ln(4)

    # Période couverte
    pdf.set_fill_color(235, 240, 255)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, "PERIODE COUVERTE", ln=True, fill=True)
    pdf.ln(2)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(55, 6, "Debut de periode :", ln=False)
    pdf.cell(0, 6, periode_debut.strftime("%d/%m/%Y"), ln=True)
    pdf.cell(55, 6, "Fin de periode :", ln=False)
    pdf.cell(0, 6, periode_fin.strftime("%d/%m/%Y"), ln=True)
    pdf.ln(4)

    # Dates de l'attestation
    pdf.set_fill_color(235, 240, 255)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, "VALIDITE DE L'ATTESTATION", ln=True, fill=True)
    pdf.ln(2)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(55, 6, "Date d'emission :", ln=False)
    pdf.cell(0, 6, date_emission.strftime("%d/%m/%Y"), ln=True)
    pdf.cell(55, 6, "Date d'expiration :", ln=False)

    # Mettre en rouge si date expirée
    if date_expiration < date.today():
        pdf.set_text_color(200, 0, 0)
    pdf.cell(0, 6, date_expiration.strftime("%d/%m/%Y"), ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(6)

    # Corps de l'attestation
    texte = _TEXTE_ATTESTATION.format(
        date=date_emission.strftime("%d/%m/%Y"),
        expiration=date_expiration.strftime("%d/%m/%Y"),
    )
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(0, 5, texte)
    pdf.ln(8)

    # Mention réglementaire
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(0, 160, 80)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 8, "ENTREPRISE A JOUR DE SES COTISATIONS", ln=True, align="C", fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(8)

    # Signature électronique
    pdf.set_font("Helvetica", "I", 8)
    pdf.cell(0, 5, "Document genere electroniquement - Signature numerique URSSAF", ln=True, align="R")
    pdf.cell(0, 5, f"Reference : {numero}", ln=True, align="R")

    return bytes(pdf.output())


def generate_attestation_urssaf(
    scenario: str,
    team_names: list[str] | None = None,
) -> tuple[bytes, dict]:
    doc_id = str(uuid.uuid4())
    numero = f"ATT-{random.randint(100000, 999999)}-{random.randint(10, 99)}"

    siret_reel = generate_siret()
    siret_incoherent = scenario in ("siret_incoherent", "falsifie")
    siret_affiche = generate_siret() if siret_incoherent else siret_reel

    raison_sociale = random_company_name(team_names)
    adresse = random_address()
    code_naf = random.choice(_CODE_NAF)

    date_emission = date.today() - timedelta(days=random.randint(0, 30))

    # date_expiree : expiration dans le passé (1 à 24 mois)
    if scenario in ("date_expiree", "falsifie"):
        mois_passes = random.randint(1, 24)
        date_expiration = date_emission - timedelta(days=mois_passes * 30)
        # S'assurer qu'elle est bien passée
        if date_expiration >= date.today():
            date_expiration = date.today() - timedelta(days=random.randint(30, 180))
    else:
        date_expiration = date_emission + timedelta(days=365)

    # Période couverte : trimestre courant
    periode_debut = date(date_emission.year, ((date_emission.month - 1) // 3) * 3 + 1, 1)
    periode_fin = date_emission

    pdf_bytes = _build_pdf(
        numero, raison_sociale, siret_affiche, adresse, code_naf,
        date_emission, date_expiration, periode_debut, periode_fin,
    )

    anomalies = []
    if siret_incoherent:
        anomalies.append("SIRET_INCOHERENT")
    if date_expiration < date.today():
        anomalies.append("DATE_EXPIREE")

    ground_truth = {
        "id": doc_id,
        "type": "attestation_urssaf",
        "scenario": scenario,
        "fournisseur": {
            "nom": raison_sociale,
            "siret": siret_reel,
            "adresse": adresse,
        },
        "client": {"nom": "", "siret": ""},
        "montant_ht": 0.0,
        "tva_rate": 0.0,
        "tva_montant": 0.0,
        "montant_ttc": 0.0,
        "date_emission": date_emission.isoformat(),
        "date_expiration": date_expiration.isoformat(),
        "numero_document": numero,
        "coherent": len(anomalies) == 0,
        "anomalies": anomalies,
    }

    if siret_incoherent:
        ground_truth["siret_attendu"] = siret_reel
        ground_truth["siret_reel"] = siret_affiche

    return pdf_bytes, ground_truth
