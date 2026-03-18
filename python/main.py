from fastapi import FastAPI, UploadFile, File
import easyocr
from pdf2image import convert_from_path
import spacy
from PIL import Image
import shutil
import os
import numpy as np

app = FastAPI()

# Charger les modèles
reader = easyocr.Reader(['fr', 'en'])
nlp = spacy.load("fr_core_news_sm")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.get("/")
def root():
    return {"message": "OCR API running"}


@app.post("/ocr")
async def read_image(file: UploadFile = File(...)):

    file_path = f"{UPLOAD_DIR}/{file.filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    all_text = ""

    print("FILENAME:", file.filename)

    if file.content_type == "application/pdf":
        print("PDF DETECTED")

        images = convert_from_path(file_path)
        print('images:', images)

        for img in images:
            print('img:', img)
            img = img.convert("RGB")  # normalisation
            img_array = np.array(img)
            ocr_result = reader.readtext(img_array) 

            # transformer en texte
            page_text = " ".join([r[1] for r in ocr_result])
            all_text += page_text + "\n"

    else:
        print("IMAGE DETECTED")

        ocr_result = reader.readtext(file_path)

        all_text = " ".join([r[1] for r in ocr_result])

    print("TEXT:", all_text)

    # ✅ spaCy reçoit du TEXTE (string)
    doc = nlp(all_text)

    entities = []
    for ent in doc.ents:
        entities.append({
            "text": ent.text,
            "label": ent.label_
        })

    return {
        "filename": file.filename,
        "text": all_text,
        "entities": entities
    }