from fastapi import FastAPI, UploadFile, File
import easyocr
from pdf2image import convert_from_path
import spacy
import shutil
import os
import numpy as np
import re
import uuid

app = FastAPI()

reader = easyocr.Reader(['fr', 'en'])
nlp = spacy.load("fr_core_news_sm")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def extract_fields(text):
    data = {}
    score = 0

    clean_text = text.replace("\n", " ")

    # SIRET
    siret = re.search(r"(?:\d[\s]*){14}", clean_text)
    if siret:
        data["siret"] = re.sub(r"\s", "", siret.group())
        score += 0.1

    # SIREN
    siren = re.search(r"(?:\d[\s]*){9}", clean_text)
    if siren:
        data["siren"] = re.sub(r"\s", "", siren.group())
        score += 0.1

    # IBAN
    iban = re.search(r"FR\d{2}(?:\s?\d{4}){5}", clean_text)
    if iban:
        data["iban"] = iban.group().replace(" ", "")
        score += 0.1

    # BIC
    bic = re.search(r"[A-Z]{6}[A-Z0-9]{2}(?:[A-Z0-9]{3})?", clean_text)
    if bic:
        data["bic"] = bic.group()
        score += 0.1

    # Nom entreprise
    nomEntreprise = re.search(r"(?i)Société\s*:\s*([A-Za-z0-9\s]+)", clean_text)
    if nomEntreprise:
        data["nom_entreprise"] = nomEntreprise.group(1).strip()
        score += 0.1

    # Nom Titulaire
    nomTitulaire = re.search(r"(?i)Titulaire\s*:\s*([A-Za-z0-9\s]+)", clean_text)
    if nomTitulaire:
        data["nom_titulaire"] = nomTitulaire.group(1).strip()
        score += 0.1

    # Adresse
    adresse = re.search(r"(?i)Adresse\s*:\s*([A-Za-z0-9\s,]+)", clean_text)
    if adresse:
        data["adresse"] = adresse.group(1).strip()
        score += 0.05

    # Date émission
    date = re.search(r"\d{4}-\d{2}-\d{2}", clean_text)
    if date:
        data["date_emission"] = date.group()
        score += 0.05

    else:
        date = re.search(r"\d{2}/\d{2}/\d{4}", clean_text)
        if date:
            data["date_emission"] = date.group()
            score += 0.05

    # Date expiration
    date_exp = re.search(r"(?i)Date\s*exp\s*:\s*(\d{4}-\d{2}-\d{2})", clean_text)
    if date_exp:
        data["date_expiration"] = date_exp.group(1)
        score += 0.05

    # Montants
    amounts = re.findall(r"\d+[.,]\d{2}", clean_text)
    if amounts:
        data["montant_ttc"] = float(amounts[-1].replace(",", "."))
        data["montant_ht"] = float(amounts[0].replace(",", "."))
        score += 0.1

    # TVA
    tva = re.search(r"(20|10|5\.5|2\.1)\s?%", clean_text)
    if tva:
        data["tva_rate"] = float(tva.group().replace("%", ""))
        score += 0.05

    # Fournisseur
    doc = nlp(clean_text)
    for ent in doc.ents:
        if ent.label_ == "ORG":
            data["fournisseur"] = ent.text
            score += 0.5
            break

    data["classification_confidence"] = score

    return data

def run_ocr(file_path, content_type):
    text = ""
    confidences = []

    if content_type == "application/pdf":
        images = convert_from_path(file_path)

        for img in images:
            img = img.convert("RGB")
            result = reader.readtext(np.array(img))

            for r in result:
                text += r[1] + " "
                confidences.append(r[2])

    else:
        result = reader.readtext(file_path)

        for r in result:
            text += r[1] + " "
            confidences.append(r[2])

    ocr_conf = sum(confidences) / len(confidences) if confidences else 0

    return text, ocr_conf

@app.post("/ocr")
async def ocr(file: UploadFile = File(...)):

    file_id = str(uuid.uuid4())
    file_path = f"{UPLOAD_DIR}/{file.filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # OCR
    text, ocr_conf = run_ocr(file_path, file.content_type)

    # Extraction
    fields = extract_fields(text)

    # Résultat final
    return {
        "file_id": file_id,
        "file_name": file.filename,
        "ocr_confidence": ocr_conf,
        "classification_confidence": fields.get("classification_confidence", 0),
        "fields": {
            "siret": fields.get("siret"),
            "siren": fields.get("siren"),
            "montant_ht": fields.get("montant_ht"),
            "montant_ttc": fields.get("montant_ttc"),
            "tva_rate": fields.get("tva_rate"),
            "date_emission": fields.get("date_emission"),
            "date_expiration": fields.get("date_expiration"),
            "iban": fields.get("iban"),
            "bic": fields.get("bic"),
            "nom_entreprise": fields.get("nom_entreprise"),
            "nom_titulaire": fields.get("nom_titulaire"),
            "adresse": fields.get("adresse"),
            "fournisseur": fields.get("fournisseur"),
            "additionalProp1": {},
        }
    }