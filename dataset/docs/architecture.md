# Architecture du projet

## Vue d'ensemble

```
dataset_generator/
├── generate_dataset.py      # Orchestrateur principal
├── generate_fixtures.py     # Génère 7 fixtures de test déterministes
├── generators/              # Un fichier par type de document
│   ├── facture.py
│   ├── devis.py
│   ├── attestation_urssaf.py
│   ├── kbis.py
│   └── rib.py
└── utils/
    ├── faker_helpers.py     # Génération de données françaises (SIRET, IBAN…)
    └── degradation.py       # Dégradation d'image Pillow
```

## Flux de génération

Pour chaque document, le pipeline suit ces étapes :

```
generate_dataset()
    │
    ├── Phase 1 : Planification des assignments (type, scenario, team_names)
    │       └── 6 docs/type avec team_names si activé (scénario S8)
    │
    ├── Phase 2 : Split stratifié (si split fourni)
    │       └── Grouper par (type, scenario) → floor(n × ratio) pour train
    │
    ├── Phase 3 : Création arborescence
    │       ├── split=None  → generated_dataset/raw/, scans/, ground_truth/
    │       └── split set   → generated_dataset/train/{raw,scans,ground_truth}/
    │                          generated_dataset/test/{raw,scans,ground_truth}/
    │
    ├── Phase 4 : Génération des documents
    │   └── _process_document(doc_type, scenario)
    │           ├── generators/<type>.py → (pdf_bytes, ground_truth)
    │           ├── PdfDocument().render()  → PIL Image  (pypdfium2)
    │           ├── degrade_image(img, level)  × 3 niveaux
    │           └── Sauvegarde dans le bon sous-dossier (train/ ou test/ ou racine)
    │
    ├── Phase 5 : labels.csv
    │       └── 1 ligne par document dans chaque répertoire concerné
    │
    └── Phase 6 : scenarios.json + dataset_summary.json (stats globales + train/test si split)
```

### Structure de sortie avec split

```
generated_dataset/
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
├── labels.csv           # global
├── scenarios.json       # catalogue des scénarios
└── dataset_summary.json

generated_dataset/output/test_fixtures/   ← make fixtures
├── facture_yoni_sas_propre.pdf
├── facture_scan_flou.png
├── facture_rotated_15.jpg
├── facture_siret_mismatch.pdf
├── attestation_siret_different.pdf
├── attestation_urssaf_expiree.pdf
├── facture_tva_15pct.pdf
└── *_ground_truth.json (×7)
```

## Interface des générateurs

Chaque générateur expose une seule fonction publique :

```python
def generate_<type>(
    scenario: str,
    team_names: list[str] | None = None,
) -> tuple[bytes, dict]:
    ...
```

- **Entrée** : le scénario à appliquer, les noms d'équipe optionnels
- **Sortie** : les octets du PDF + le dictionnaire ground truth complet

## Compatibilité des scénarios

Certains scénarios ne s'appliquent pas à tous les types. La table de compatibilité est définie dans `generate_dataset.py` :

| Type               | siret_incoherent | date_expiree | tva_incoherente |
|--------------------|:---:|:---:|:---:|
| facture            | ✓ | — (→ normal) | ✓ |
| devis              | ✓ | ✓ | ✓ |
| attestation_urssaf | ✓ | ✓ | — (→ normal) |
| kbis               | ✓ | — (→ normal) | — (→ normal) |
| rib                | — (→ falsifie) | — (→ normal) | — (→ normal) |

`falsifie` cumule les anomalies supportées par chaque type.

## Reproductibilité

La graine `seed` initialise à la fois `random.seed()` et `numpy.random.seed()` avant toute génération.

Avec la même graine et les mêmes paramètres, le dataset produit est identique bit à bit :

- PDFs générés : identiques ✓
- Ground truth JSON : identiques ✓
- PNG dégradés (low/medium/high) : identiques avec la même graine ✓
