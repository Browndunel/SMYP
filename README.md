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
make help     # Liste les commandes disponibles
make clean    # Supprime le venv
make reset    # Supprime le venv + le dataset généré
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
    team_names=["Alice Martin", "Bob Dupont", "Claire Moreau"],
    seed=42,
)
```

## Sortie

```
dataset/
├── raw/            # PDFs originaux
├── scans/          # PNGs source + 3 niveaux de dégradation
├── ground_truth/   # JSON par document
└── dataset_summary.json
```

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
| [`docs/scenarios.md`](docs/scenarios.md) | Détail des 5 scénarios et logique de détection des anomalies |
| [`docs/ground_truth.md`](docs/ground_truth.md) | Schéma JSON complet, description de chaque champ |
| [`docs/degradation.md`](docs/degradation.md) | Pipeline de dégradation, paramètres par niveau |
| [`docs/faker_helpers.md`](docs/faker_helpers.md) | Formules SIRET, IBAN, TVA intra, helpers disponibles |
