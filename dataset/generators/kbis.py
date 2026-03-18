"""
Générateur d'extraits Kbis (PDF + ground truth JSON).
"""
import random
import uuid
from datetime import date, timedelta

from fpdf import FPDF

from utils.faker_helpers import (
    generate_siret,
    random_company_name,
    random_address,
    random_person_name,
)

_FORMES_JURIDIQUES = ["SARL", "SAS", "EURL", "SA", "SASU", "SNC"]
_CODES_APE = {
    "6201Z": "Programmation informatique",
    "6202A": "Conseil en systemes et logiciels informatiques",
    "7022Z": "Conseil pour les affaires et autres conseils de gestion",
    "4321A": "Travaux d'installation electrique dans tous locaux",
    "4619B": "Autres intermediaires du commerce en produits divers",
    "8559A": "Formation continue d'adultes",
    "7112B": "Ingenierie, etudes techniques",
    "6920Z": "Activites comptables",
    "6910Z": "Activites juridiques",
    "7311Z": "Activites des agences de publicite",
}
_GREFFES = [
    "Greffe du Tribunal de Commerce de Paris",
    "Greffe du Tribunal de Commerce de Lyon",
    "Greffe du Tribunal de Commerce de Marseille",
    "Greffe du Tribunal de Commerce de Bordeaux",
    "Greffe du Tribunal de Commerce de Nantes",
    "Greffe du Tribunal de Commerce de Toulouse",
    "Greffe du Tribunal de Commerce de Lille",
    "Greffe du Tribunal de Commerce de Strasbourg",
]


def _build_pdf(
    numero_rcs: str,
    raison_sociale: str,
    forme_juridique: str,
    siret: str,
    capital: int,
    date_immatriculation: date,
    adresse: str,
    code_ape: str,
    libelle_ape: str,
    dirigeant: str,
    greffe: str,
    date_extrait: date,
) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(20, 20, 20)

    # En-tête officiel
    pdf.set_fill_color(30, 50, 100)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "REGISTRE DU COMMERCE ET DES SOCIETES", ln=True, align="C", fill=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 6, greffe, ln=True, align="C", fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(4)

    # Titre
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "EXTRAIT Kbis", ln=True, align="C")
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, f"Extrait delivre le : {date_extrait.strftime('%d/%m/%Y')}", ln=True, align="C")
    pdf.ln(6)

    # Bloc identification
    pdf.set_fill_color(240, 242, 255)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "IDENTIFICATION DE LA PERSONNE MORALE", ln=True, fill=True)
    pdf.ln(2)

    rows = [
        ("Denomination sociale :", raison_sociale),
        ("Forme juridique :", forme_juridique),
        ("Capital social :", f"{capital:,} EUR".replace(",", " ")),
        ("SIRET :", siret),
        ("N° RCS :", numero_rcs),
        ("Date d'immatriculation :", date_immatriculation.strftime("%d/%m/%Y")),
        ("Activite principale (APE) :", f"{code_ape} - {libelle_ape}"),
    ]
    pdf.set_font("Helvetica", "", 9)
    for label, value in rows:
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(70, 6, label, ln=False)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 6, value, ln=True)
    pdf.ln(4)

    # Siège social
    pdf.set_fill_color(240, 242, 255)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "SIEGE SOCIAL", ln=True, fill=True)
    pdf.ln(2)
    pdf.set_font("Helvetica", "", 9)
    for line in adresse.split("\n"):
        pdf.cell(0, 5, line, ln=True)
    pdf.ln(4)

    # Dirigeant
    pdf.set_fill_color(240, 242, 255)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "DIRIGEANT(S)", ln=True, fill=True)
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 9)
    qualite = "Gérant" if forme_juridique in ("SARL", "EURL") else "Président"
    pdf.cell(40, 6, f"{qualite} :", ln=False)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 6, dirigeant, ln=True)
    pdf.ln(6)

    # Mentions obligatoires
    pdf.set_fill_color(255, 245, 200)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(
        0, 4,
        "Cet extrait est delivre conformement aux dispositions de l'article R.123-151 du Code de commerce. "
        "Il atteste de la situation juridique de la societe a la date de delivrance. "
        "Pour toute utilisation officielle, verifier la validite sur infogreffe.fr.",
        fill=True,
    )
    pdf.ln(4)

    # Cachet
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(0, 5, f"Delivre par : {greffe}", ln=True, align="R")
    pdf.cell(0, 5, f"Le : {date_extrait.strftime('%d/%m/%Y')}", ln=True, align="R")

    return bytes(pdf.output())


def generate_kbis(
    scenario: str,
    team_names: list[str] | None = None,
) -> tuple[bytes, dict]:
    doc_id = str(uuid.uuid4())

    siret_reel = generate_siret()
    siret_incoherent = scenario in ("siret_incoherent", "falsifie")
    siret_affiche = generate_siret() if siret_incoherent else siret_reel

    raison_sociale = random_company_name(team_names)
    forme_juridique = random.choice(_FORMES_JURIDIQUES)
    capital = random.choice([1000, 5000, 10000, 50000, 100000, 250000, 500000])
    adresse = random_address()
    code_ape, libelle_ape = random.choice(list(_CODES_APE.items()))
    dirigeant = random_person_name()
    greffe = random.choice(_GREFFES)

    date_extrait = date.today() - timedelta(days=random.randint(0, 30))
    date_immatriculation = date_extrait - timedelta(days=random.randint(365, 365 * 20))

    # Numéro RCS = ville + SIREN
    ville = greffe.split("de ")[-1][:3].upper()
    numero_rcs = f"{ville} {siret_affiche[:9]}"

    pdf_bytes = _build_pdf(
        numero_rcs, raison_sociale, forme_juridique, siret_affiche,
        capital, date_immatriculation, adresse, code_ape, libelle_ape,
        dirigeant, greffe, date_extrait,
    )

    anomalies = []
    if siret_incoherent:
        anomalies.append("SIRET_INCOHERENT")

    ground_truth = {
        "id": doc_id,
        "type": "kbis",
        "scenario": scenario,
        "fournisseur": {
            "nom": raison_sociale,
            "siret": siret_reel,
            "adresse": adresse,
        },
        "client": {"nom": "", "siret": ""},
        "montant_ht": 0.0,
        "tva_taux": 0,
        "tva_montant": 0.0,
        "montant_ttc": 0.0,
        "date_emission": date_extrait.isoformat(),
        "date_echeance": "",
        "numero_document": numero_rcs,
        "coherent": len(anomalies) == 0,
        "anomalies": anomalies,
        "forme_juridique": forme_juridique,
        "capital_social": capital,
        "code_ape": code_ape,
        "dirigeant": dirigeant,
    }

    if siret_incoherent:
        ground_truth["siret_attendu"] = siret_reel
        ground_truth["siret_reel"] = siret_affiche

    return pdf_bytes, ground_truth
