# SMYP Dataset — Documents administratifs français

Génère un dataset synthétique de documents PDF français (factures, devis, attestations URSSAF, Kbis, RIB) avec leurs versions scan dégradé et leurs ground truth JSON.

## Prérequis système

Aucune dépendance système requise. Tout s'installe via le venv Python.

## Installation

```bash
make install
```

Cette commande crée un environnement virtuel isolé dans `.venv/` et installe toutes les dépendances Python automatiquement.

## Lancement

```bash
make run
```

Génère 100 documents (20 par type) dans `dataset/` avec seed fixe.

## Autres commandes

```bash
make fixtures  # Génère les 7 fixtures de test déterministes
make help      # Liste les commandes disponibles
make clean     # Supprime le venv
make reset     # Supprime le venv + le dataset généré
```

## Lancement manuel (sans make)

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\activate
pip install -r requirements.txt
python generate_dataset.py
```

## Personnalisation

```python
from generate_dataset import generate_dataset
from utils.faker_helpers import TEAM_COMPANIES

# Dataset simple (structure à plat)
generate_dataset(
    output_dir="dataset",
    n_per_type=50,
    scenario_distribution={
        "normal": 0.50,
        "siret_incoherent": 0.15,
        "date_expiree": 0.15,
        "tva_incoherente": 0.10,
        "falsifie": 0.10,
    },
    degradation_levels=["low", "medium", "high"],
    team_names=TEAM_COMPANIES,   # 20 docs équipe inclus
    seed=42,
)

# Dataset avec split train/test stratifié
generate_dataset(
    output_dir="dataset",
    n_per_type=20,
    team_names=TEAM_COMPANIES,
    split={"train": 0.70, "test": 0.30},
    seed=42,
)
```

## Sortie

Structure à plat (défaut, `split=None`) :
```
dataset/
├── raw/            # PDFs originaux
├── scans/          # PNGs source + 3 niveaux de dégradation
├── ground_truth/   # JSON par document
├── labels.csv      # Métadonnées ML (1 ligne par document)
└── dataset_summary.json
```

Avec split train/test :
```
dataset/
├── train/
│   ├── raw/
│   ├── scans/
│   ├── ground_truth/
│   └── labels.csv
├── test/
│   ├── raw/
│   ├── scans/
│   ├── ground_truth/
│   └── labels.csv
├── labels.csv        # Global (train + test)
└── dataset_summary.json
```

Fixtures de test (`make fixtures`) :
```
dataset/output/test_fixtures/
├── facture_yoni_sas_propre.pdf
├── facture_scan_flou.png
├── facture_rotated_15.jpg
├── facture_siret_mismatch.pdf
├── attestation_siret_different.pdf
├── attestation_urssaf_expiree.pdf
├── facture_tva_15pct.pdf
└── *_ground_truth.json  (7 fichiers)
```

### labels.csv

Colonnes : `file_name, doc_type, is_fraud, anomaly_type, expected_siret, montant_ttc, tva_rate, date_expiration, degradation_level`

- 1 ligne par document (référence le PDF brut)
- `is_fraud=True` si anomalies non vides
- `anomaly_type` : codes séparés par `|` (ex : `SIRET_INCOHERENT|TVA_INCOHERENTE`)

Chaque document produit 5 fichiers :
```
{type}_{scenario}_{id[:8]}.pdf
{type}_{scenario}_{id[:8]}_original.png
{type}_{scenario}_{id[:8]}_low.png
{type}_{scenario}_{id[:8]}_medium.png
{type}_{scenario}_{id[:8]}_high.png
```

## Documentation détaillée

| Fichier | Contenu |
|---------|---------|
| [`docs/benchmark.md`](docs/benchmark.md) | Choix de la stack technique, comparatif des alternatives |
| [`docs/architecture.md`](docs/architecture.md) | Flux de génération, interface des modules, compatibilité scénarios |
| [`docs/fixtures.md`](docs/fixtures.md) | Description des 7 fixtures de test déterministes |
| [`docs/scenarios.md`](docs/scenarios.md) | Détail des 5 scénarios et logique de détection des anomalies |
| [`docs/ground_truth.md`](docs/ground_truth.md) | Schéma JSON complet, description de chaque champ |
| [`docs/degradation.md`](docs/degradation.md) | Pipeline de dégradation, paramètres par niveau |
| [`docs/faker_helpers.md`](docs/faker_helpers.md) | Formules SIRET, IBAN, TVA intra, helpers disponibles |
