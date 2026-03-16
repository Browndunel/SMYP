# Architecture du projet

## Vue d'ensemble

```
dataset_generator/
├── generate_dataset.py      # Orchestrateur principal
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
    └── _process_document(doc_type, scenario)
            │
            ├── generators/<type>.py → (pdf_bytes, ground_truth)
            │       ├── Tirage des données fake (faker_helpers)
            │       ├── Application du scénario (anomalies)
            │       └── Construction du PDF (fpdf2)
            │
            ├── PdfDocument().render()  → PIL Image  (pypdfium2)
            │
            ├── degrade_image(img, level)  × 3 niveaux
            │
            └── Sauvegarde
                    ├── raw/{nom}.pdf
                    ├── scans/{nom}_original.png
                    ├── scans/{nom}_{low,medium,high}.png
                    └── ground_truth/{nom}.json
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

La graine `seed` initialise à la fois `random.seed()` et `numpy.random.seed()` avant toute génération. Avec la même graine et les mêmes paramètres, le dataset produit est identique bit à bit.
