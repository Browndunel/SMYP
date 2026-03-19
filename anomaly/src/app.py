"""
API REST du service de détection d'anomalies.
Expose un endpoint POST /validate qui prend les données OCR d'un document,
lance l'analyse (règles métier + ML) et renvoie le verdict.
Le résultat est aussi poussé sur MinIO dans le dossier curated/.
"""

import sys, io, json, csv
from pathlib import Path

# pour que les imports marchent même si on lance le fichier directement
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI
from pydantic import BaseModel
from fraud_detector import detect
from minio_client import client, BUCKET

# chemin vers le CSV d'entraînement (on y ajoute les factures clean)
CSV_PATH = Path(__file__).parent.parent / "data" / "mes_factures.csv"


app = FastAPI(
    title="Anomaly Service",
    description="Détection de fraude documentaire — règles R1-R7 + IsolationForest",
    version="1.0.0",
)


# --- Modèles Pydantic (validation auto des entrées/sorties) ---

class DocumentFields(BaseModel):
    """Champs qu'on peut recevoir de l'OCR. Tous optionnels vu que
    ça dépend du type de doc (une facture a un IBAN, pas un Kbis)."""
    siret: str | None = None
    siren: str | None = None
    fournisseur: str | None = None
    nom_entreprise: str | None = None
    nom_titulaire: str | None = None
    adresse: str | None = None
    iban: str | None = None
    bic: str | None = None
    montant_ht: float | None = None
    montant_ttc: float | None = None
    tva_rate: float | None = None
    date_emission: str | None = None
    date_expiration: str | None = None
    model_config = {"extra": "allow"}  # accepte les champs imprévus


class RelatedDocument(BaseModel):
    file_id: str | None = None
    doc_type: str
    fields: DocumentFields


class ValidateRequest(BaseModel):
    file_id: str
    file_name: str | None = None
    doc_type: str
    ocr_confidence: float = 1.0
    classification_confidence: float = 1.0
    fields: DocumentFields
    related_docs: list[RelatedDocument] = []


class AnomalyItem(BaseModel):
    rule: str
    description: str
    severity: str


class ValidateResponse(BaseModel):
    file_id: str
    status: str          # OK / suspect / frauduleux
    anomaly_score: float  # 0 à 1
    confidence_score: float
    anomalies: list[AnomalyItem]
    processing_time_ms: int


# --- Endpoints ---

@app.post("/validate", response_model=ValidateResponse)
async def validate(req: ValidateRequest):
    """Analyse un document, renvoie les anomalies et push sur MinIO."""
    result = detect(req.model_dump())

    # on stocke le résultat dans le bucket MinIO (dossier curated/)
    payload = json.dumps(result, ensure_ascii=False).encode("utf-8")
    key = f"curated/{result['file_id']}.json"
    client.put_object(BUCKET, key, io.BytesIO(payload), len(payload),
                      content_type="application/json")

    # si la facture est clean, on l'ajoute au CSV pour enrichir le modèle
    if result["status"] == "OK" and req.doc_type == "FACTURE":
        f = req.fields
        if f.siret and f.montant_ht is not None:
            with open(CSV_PATH, "a", newline="") as csvfile:
                csv.writer(csvfile).writerow([
                    f.siret, f.montant_ht,
                    f.montant_ttc or round(f.montant_ht * (1 + (f.tva_rate or 20.0) / 100), 2),
                    f.tva_rate or 20.0,
                    req.ocr_confidence,
                ])

    return result


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    print("Anomaly service → http://localhost:8002")
    print("Swagger         → http://localhost:8002/docs")
    uvicorn.run(app, host="0.0.0.0", port=8002)
