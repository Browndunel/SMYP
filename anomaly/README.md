# Anomaly Service — Détection de fraude documentaire

Microservice de détection de fraude par analyse de documents fournisseurs (factures, devis, attestations, etc.).
Combine des **règles métier déterministes** (R1-R7) et un **modèle ML** (IsolationForest) pour scorer les anomalies.

## Architecture

```
├── src/                  # Code source
│   ├── app.py            # API FastAPI (POST /validate, GET /health)
│   ├── fraud_detector.py # Moteur de règles R1-R7 + appel ML
│   ├── ml_detector.py    # Charge model.pkl et fait l'inférence IsolationForest
│   ├── train.py          # Entraîne le modèle et génère model.pkl
│   └── generate_data.py  # Génère des données d'entraînement fictives (dev)
├── tests/                # Tests
│   └── test_real.py      # Tests standalone sans serveur (dev)
├── data/                 # Données
│   └── mes_factures.csv  # Données d'entraînement (dev)
├── models/               # Modèles ML
│   └── model.pkl         # Modèle sérialisé (généré par train.py)
├── README.md
└── requirements.txt
```

## Installation

```bash
pip install fastapi uvicorn scikit-learn
```

## Démarrage rapide

```bash
# 1. Générer les données d'entraînement (optionnel, pour le dev)
python -m src.generate_data

# 2. Entraîner le modèle
python -m src.train                              # données par défaut
python -m src.train --data data/mes_factures.csv  # données custom

# 3. Lancer le service
python -m src.app
```

Le service tourne sur `http://localhost:8000`.
La doc Swagger est dispo sur `http://localhost:8000/docs`.

## Endpoints

### POST /validate

Analyse un document et ses documents liés, retourne les anomalies détectées.

**Entrée :**

```json
{
  "file_id": "uuid-v4",
  "file_name": "facture_001.pdf",
  "doc_type": "FACTURE",
  "ocr_confidence": 0.94,
  "classification_confidence": 0.89,
  "fields": {
    "siret": "44306184100047",
    "montant_ht": 1000.00,
    "montant_ttc": 1200.00,
    "tva_rate": 20.0,
    "date_emission": "2024-01-15",
    "iban": "FR7630006000011234567890189",
    "fournisseur": "Mon Fournisseur SAS"
  },
  "related_docs": [
    {
      "file_id": "uuid-urssaf",
      "doc_type": "ATTESTATION_URSSAF",
      "fields": {
        "siret": "44306184100047",
        "date_expiration": "2027-01-01"
      }
    }
  ]
}
```

**Types de documents supportés :** `FACTURE`, `DEVIS`, `ATTESTATION_SIRET`, `ATTESTATION_URSSAF`, `EXTRAIT_KBIS`, `RIB`

**Sortie :**

```json
{
  "file_id": "uuid-v4",
  "status": "suspect",
  "anomaly_score": 0.42,
  "confidence_score": 0.73,
  "anomalies": [
    { "rule": "R1", "description": "SIRET incohérent : FACTURE=123... / URSSAF=456...", "severity": "high" },
    { "rule": "ML", "description": "Montant anormal détecté par IsolationForest", "severity": "medium" }
  ],
  "processing_time_ms": 12
}
```

- `status` : `OK` | `suspect` | `frauduleux`
- `anomaly_score` : entre 0 et 1 (somme pondérée des anomalies)
- `confidence_score` : confiance globale (OCR × classification × pénalité anomalies)
- `severity` : `high` (FRAUDULEUX) | `medium` (SUSPECT)

### GET /health

Healthcheck. Retourne `{"status": "ok"}`.

## Règles métier (R1-R7)

| # | Règle | Condition d'alerte | Sévérité |
|---|-------|--------------------|----------|
| R1 | SIRET cohérent entre documents | SIRET ≠ entre 2 docs du même fournisseur | high |
| R2 | Date expiration URSSAF valide | date_expiration < aujourd'hui | high |
| R3 | TVA cohérente avec taux légaux | Taux ∉ {0%, 5.5%, 10%, 20%} | medium |
| R4 | Calcul HT + TVA = TTC | Écart > 0.02€ | medium |
| R5 | IBAN format valide | Longueur ≠ 27 (FR) ou checksum modulo 97 invalide | medium |
| R6 | Date émission ≤ aujourd'hui | date_emission > aujourd'hui | medium |
| R7 | SIRET format valide | Pas 14 chiffres ou checksum Luhn invalide | high |

## Modèle ML (IsolationForest)

En plus des règles déterministes, un modèle IsolationForest détecte les **patterns statistiquement anormaux** sur 4 features :

- `montant_ht` — montant hors taxe
- `montant_ttc` — montant TTC
- `tva_rate` — taux de TVA
- `ocr_confidence` — confiance de l'OCR

Le modèle est entraîné **par SIRET** quand il y a assez d'historique (≥ 5 factures), sinon il utilise un **modèle global**. Ça permet de détecter qu'un fournisseur qui facture habituellement entre 1k€ et 8k€ envoie soudainement une facture de 80k€.

### Entraînement

```bash
# Avec les données par défaut (hardcodées)
python train.py

# Avec un CSV de données réelles
python train.py --data mes_factures.csv
```

**Format CSV attendu :**

```csv
siret,montant_ht,montant_ttc,tva_rate,ocr_confidence
44306184100047,3000,3600,20.0,0.94
44306184100047,5000,6000,20.0,0.92
10000000410009,20000,24000,20.0,0.91
```

Ne mettre que des factures **légitimes** dans le CSV. Le modèle apprend ce qui est "normal" et flag tout ce qui sort de la distribution.

### Génération de données de test

```bash
python -m src.generate_data  # crée data/mes_factures.csv avec ~2500 factures
```

Génère 150 factures par entreprise (10 profils différents) + 1000 factures d'entreprises sans historique.

## Tests

### Standalone (sans serveur)

```bash
python -m tests.test_real
```

Teste toutes les règles R1-R7, le ML, et des combinaisons.

### Via l'API (serveur lancé)

```powershell
# PowerShell
(Invoke-RestMethod -Uri http://localhost:8000/validate -Method POST -ContentType "application/json" -Body '{"file_id":"test-chaos","doc_type":"FACTURE","ocr_confidence":0.40,"classification_confidence":0.35,"fields":{"siret":"999","montant_ht":999999,"montant_ttc":50000,"tva_rate":13.0,"date_emission":"2013-01-01","iban":"FR76FAKE"},"related_docs":[{"doc_type":"ATTESTATION_URSSAF","fields":{"siret":"44306184100047","date_expiration":"2019-01-01"}},{"doc_type":"EXTRAIT_KBIS","fields":{"siret":"10000000410009"}}]}' | ConvertTo-Json -Depth 10).Content
```

## Scoring

Le `anomaly_score` est calculé comme la somme pondérée des anomalies :

- Chaque anomalie `high` (FRAUDULEUX) ajoute **0.30**
- Chaque anomalie `medium` (SUSPECT) ajoute **0.12**
- Plafonné à **1.0**

Le `status` final :

- `frauduleux` → au moins une anomalie `high`
- `suspect` → que des anomalies `medium`
- `OK` → aucune anomalie

## Stack technique

- **FastAPI** — API REST async
- **scikit-learn** — IsolationForest pour la détection d'anomalies
- **Pydantic** — validation des entrées/sorties
- **pickle** — sérialisation du modèle ML
