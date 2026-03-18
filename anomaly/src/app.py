"""
Webservice FastAPI pour la détection de fraude documentaire.
POST /validate -> analyse et retourne les anomalies.
GET /health -> healthcheck
GET /docs -> documentation Swagger auto-générée par FastAPI
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import io
import json

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fraud_detector import detect
from minio_client import client, BUCKET

app = FastAPI(
    title="Anomaly Service",
    description="Détection de fraude documentaire - Règles R1-R7 + ML",
    version="1.0.0",
)


class DocumentFields(BaseModel):
    """Champs extraits par l'OCR/NER, tous optionnels car ça dépend du type de doc."""
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

    model_config = {"extra": "allow"}


class RelatedDocument(BaseModel):
    """Un document lié au document principal (ex: attestation URSSAF liée à une facture)."""
    file_id: str | None = None
    doc_type: str
    fields: DocumentFields


class ValidateRequest(BaseModel):
    """Payload d'entrée pour POST /validate."""
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
    """Format de sortie, compatible avec ce qu'attend Airflow pour écrire en MongoDB."""
    file_id: str
    status: str
    anomaly_score: float
    confidence_score: float
    anomalies: list[AnomalyItem]
    processing_time_ms: int


@app.post("/validate", response_model=ValidateResponse)
async def validate(req: ValidateRequest):
    payload = req.model_dump()
    result = detect(payload)

    # Push le résultat dans smyp-curated
    data = json.dumps(result, ensure_ascii=False).encode("utf-8")
    object_name = f"curated/{result['file_id']}.json"
    client.put_object(BUCKET, object_name, io.BytesIO(data), len(data), content_type="application/json")

    return result


@app.get("/health")
async def health():
    """Healthcheck pour vérifier que le service tourne."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    print("Anomaly service running on http://localhost:8000")
    print("Swagger UI: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
