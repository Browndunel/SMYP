# SMYP — ShareMeYourPaperasse

Plateforme de détection de fraude documentaire et de conformité fournisseur.
Analyse automatiquement les documents (factures, devis, attestations, KBIS, RIB…) et identifie les anomalies grâce à des règles métier et du machine learning.

## Architecture globale

```
Utilisateur
    │
    ▼
Frontend React (Vite) :3000
    │ POST /api/upload (JWT)
    ▼
Backend Express :5001
    ├──▶ OCR Service (FastAPI) :8001  →  texte + champs extraits
    ├──▶ Anomaly Service (FastAPI) :8000  →  score + anomalies
    ├──▶ MongoDB :27017  →  sauvegarde document
    ├──▶ MinIO :9000  →  stockage fichier brut (non bloquant)
    └──▶ Airflow :8080  →  trigger pipeline (non bloquant)
                │
                ├── t1_validate        valide le payload reçu
                ├── t2_store_mongodb   confirme en MongoDB
                └── t3_notify_frontend notifie le frontend

Frontend ◀── polling GET /api/pipeline/status/:file_id
```

---

## Stack technique

### Backend (`/backend`)
- **Runtime :** Node.js 20
- **Framework :** Express 5
- **Auth :** JWT (jsonwebtoken) + bcrypt
- **BDD :** MongoDB via Mongoose
- **Upload :** Multer (mémoire)
- **HTTP :** Axios
- **Validation :** Joi
- **Docs :** Swagger UI (`/api-docs`)
- **Stockage :** MinIO SDK

### Frontend (`/frontend`)
- **Framework :** React 18 + TypeScript
- **Build :** Vite
- **Router :** React Router v6
- **State :** Zustand (persist localStorage)
- **Style :** Tailwind CSS + Radix UI
- **Icônes :** Lucide React

### OCR Service (`/ocr`)
- **Language :** Python 3.11
- **Framework :** FastAPI + Uvicorn
- **OCR :** EasyOCR (FR + EN)
- **NER :** spaCy (`fr_core_news_sm`)
- **PDF :** pdf2image + poppler

### Anomaly Service (`/anomaly`)
- **Language :** Python 3.11
- **Framework :** FastAPI + Uvicorn
- **ML :** scikit-learn (IsolationForest)
- **Règles métier :** R1–R7 (voir ci-dessous)
- **Stockage :** MinIO (résultats curatés)

### Orchestration (`/airflow`)
- **Version :** Apache Airflow 2.8.0
- **Executor :** SequentialExecutor
- **DAGs :**
  - `smyp_main_pipeline` — pipeline principal (déclenché par upload)
  - `smyp_health_check` — health check toutes les 5 min

### Infrastructure
- **BDD :** MongoDB 7
- **Stockage objet :** MinIO (S3-compatible)
- **Conteneurisation :** Docker + Docker Compose

---

## Règles de détection de fraude (R1–R7)

| Règle | Vérification | Sévérité |
|-------|-------------|----------|
| **R1** | SIRET incohérent entre documents liés | FRAUDULEUX |
| **R2** | Attestation URSSAF expirée | FRAUDULEUX |
| **R3** | Taux de TVA invalide (seuls 0%, 5.5%, 10%, 20% légaux) | SUSPECT |
| **R4** | HT + TVA ≠ TTC (tolérance 0.02€) | SUSPECT |
| **R5** | Format IBAN invalide (27 chars FR, modulo 97) | SUSPECT |
| **R6** | Date d'émission dans le futur | SUSPECT |
| **R7** | Format SIRET invalide (14 chiffres, checksum Luhn) | FRAUDULEUX |

**Score d'anomalie :**
- Chaque règle FRAUDULEUX → +0.30
- Chaque règle SUSPECT → +0.12
- Score plafonné à 1.0

**Statut final :**
- `frauduleux` — au moins 1 règle FRAUDULEUX déclenchée
- `suspect` — uniquement des règles SUSPECT
- `OK` — aucune anomalie

---

## Structure du projet

```
SMYP/
├── backend/                  # API Express
│   ├── src/
│   │   ├── controllers/      # Logique des endpoints
│   │   ├── models/           # Schémas MongoDB
│   │   ├── routes/           # Définition des routes
│   │   ├── services/         # OCR, Anomaly, MinIO, Airflow
│   │   ├── middlewares/      # Auth JWT, validation
│   │   └── utils/            # JWT, bcrypt helpers
│   ├── index.js
│   └── Dockerfile
├── frontend/                 # App React + TypeScript
│   ├── src/
│   │   ├── pages/            # Landing, Dashboard, Conformité
│   │   ├── components/       # UI (cards, modals, dropzone…)
│   │   ├── hooks/            # useAuth, useDocuments, useUpload
│   │   ├── services/         # Clients API
│   │   └── store/            # Zustand (auth, documents)
│   └── Dockerfile
├── ocr/                      # Service OCR Python
│   ├── app.py
│   └── Dockerfile
├── anomaly/                  # Service détection anomalies
│   ├── src/
│   │   ├── app.py
│   │   ├── fraud_detector.py # Règles R1-R7
│   │   ├── ml_detector.py    # IsolationForest
│   │   └── minio_client.py
│   ├── models/model.pkl
│   └── Dockerfile
├── airflow/
│   └── dags/
│       ├── smyp_main_pipeline.py
│       └── smyp_health_check.py
├── docker-compose.yml
├── .env                      # Variables d'environnement (à créer)
└── .env.example
```

---

## Lancer le projet

### Prérequis
- Docker + Docker Compose
- Node.js 20 (pour le frontend en dev local)

### 1. Configuration

```bash
cp .env.example .env
# Remplir les valeurs dans .env
```

### 2. Démarrage des services

```bash
# Lancer tous les services backend
docker-compose up --build -d mongodb backend ocr-service anomaly-service airflow

# Frontend en développement local
cd frontend && npm install && npm run dev
```

### 3. Vérification

```bash
curl http://localhost:5001/health    # Backend
curl http://localhost:8000/health    # OCR
curl http://localhost:8002/health    # Anomaly
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 (dev) |
| Backend API | http://localhost:5001 |
| Swagger UI | http://localhost:5001/api-docs |
| OCR Service | http://localhost:8000 |
| Anomaly Service | http://localhost:8002 |
| Airflow UI | http://localhost:8080 (admin / admin) |
| MongoDB | mongodb://localhost:27017 |

---

## API — Endpoints principaux

### Authentification
| Méthode | Route | Description |
|---------|-------|-------------|
| `POST` | `/api/sign-up` | Créer un compte |
| `POST` | `/api/sign-in` | Se connecter (retourne JWT) |

### Documents
| Méthode | Route | Auth | Description |
|---------|-------|------|-------------|
| `POST` | `/api/upload` | ✅ | Uploader un document (déclenche le pipeline) |
| `GET` | `/api/documents` | ✅ | Lister les documents de l'utilisateur |
| `DELETE` | `/api/documents/:id` | ✅ | Supprimer un document |
| `PUT` | `/api/documents/:id` | ✅ | Modifier un document |

### Pipeline
| Méthode | Route | Description |
|---------|-------|-------------|
| `GET` | `/api/pipeline/status/:file_id` | Suivre la progression du pipeline |
| `POST` | `/api/internal/store` | (Airflow) Confirmer le stockage MongoDB |

### OCR Service
| Méthode | Route | Description |
|---------|-------|-------------|
| `POST` | `/ocr` | Extraire texte et champs d'un document |
| `GET` | `/health` | Health check |

### Anomaly Service
| Méthode | Route | Description |
|---------|-------|-------------|
| `POST` | `/validate` | Analyser un document pour détecter les anomalies |
| `GET` | `/health` | Health check |

---

## Types de documents supportés

- `facture` — Facture fournisseur
- `devis` — Devis
- `attestation_urssaf` — Attestation de vigilance URSSAF
- `kbis` — Extrait Kbis
- `rib` — Relevé d'Identité Bancaire
- `autre` — Document non classifié

---

## Pipeline Airflow — `smyp_main_pipeline`

Déclenché automatiquement après chaque upload réussi.

```
t1_validate        → Vérifie le payload (file_id, status, anomalies…)
       │
t2_store_mongodb   → POST /api/internal/store (met à jour MongoDB)
       │
t3_notify_frontend → POST /api/pipeline/status (progress: 100%)
```

Le frontend poll `GET /api/pipeline/status/:file_id` jusqu'à `progress: 100`.
