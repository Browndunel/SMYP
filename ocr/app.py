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

    clean_text = text.replace("\n", " ")

    # SIRET
    siret = re.search(r"(?:\d[\s]*){14}", clean_text)
    if siret:
        data["siret"] = re.sub(r"\s", "", siret.group())

    # IBAN
    iban = re.search(r"FR\d{2}(?:\s?\d{4}){5}", clean_text)
    if iban:
        data["iban"] = iban.group().replace(" ", "")

    # Dates
    date = re.search(r"\d{4}-\d{2}-\d{2}", clean_text)
    if date:
        data["date_emission"] = date.group()
    else:
        date = re.search(r"\d{2}/\d{2}/\d{4}", clean_text)
        if date:
            data["date_emission"] = date.group()

    # Montants
    amounts = re.findall(r"\d+[.,]\d{2}", clean_text)
    if amounts:
        data["montant_ttc"] = float(amounts[-1].replace(",", "."))
        data["montant_ht"] = float(amounts[0].replace(",", "."))

    # TVA
    tva = re.search(r"(20|10|5\.5|2\.1)\s?%", clean_text)
    if tva:
        data["tva_rate"] = float(tva.group().replace("%", ""))

    # Fournisseur via NLP
    doc = nlp(clean_text)
    for ent in doc.ents:
        if ent.label_ == "ORG":
            data["fournisseur"] = ent.text
            break

    return data

def run_ocr(file_path, content_type):
    text = ""

    if content_type == "application/pdf":
        images = convert_from_path(file_path)

        for img in images:
            img = img.convert("RGB")
            result = reader.readtext(np.array(img))
            text += " ".join([r[1] for r in result]) + "\n"
    else:
        result = reader.readtext(file_path)
        text = " ".join([r[1] for r in result])

    return text

@app.post("/ocr")
async def ocr(file: UploadFile = File(...)):

    file_id = str(uuid.uuid4())
    file_path = f"{UPLOAD_DIR}/{file.filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # OCR
    text = run_ocr(file_path, file.content_type)

    # Extraction
    fields = extract_fields(text)

    # Résultat final
    return {
        "file_id": file_id,
        "file_name": file.filename,
        "doc_type": "FACTURE",
        "ocr_confidence": 0.90,  # (mock pour l'instant)
        "classification_confidence": 0.85,  # (mock)
        "fields": {
            "siret": fields.get("siret"),
            "montant_ht": fields.get("montant_ht"),
            "montant_ttc": fields.get("montant_ttc"),
            "tva_rate": fields.get("tva_rate"),
            "date_emission": fields.get("date_emission"),
            "date_expiration": None,
            "iban": fields.get("iban"),
            "fournisseur": fields.get("fournisseur"),
        }
    }