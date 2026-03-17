# Fixtures de test

## But

Le script `generate_fixtures.py` produit **7 fixtures déterministes** conçues pour les tests unitaires et l'intégration continue. La graine fixe `seed=0` garantit que les PDFs et la structure du ground truth sont identiques à chaque exécution.

## Génération

```bash
make fixtures
# ou directement :
python generate_fixtures.py
```

## Répertoire de sortie

```
generated_dataset/output/test_fixtures/
├── facture_yoni_sas_propre.pdf
├── facture_scan_flou.png
├── facture_rotated_15.jpg
├── facture_siret_mismatch.pdf
├── attestation_siret_different.pdf
├── attestation_urssaf_expiree.pdf
├── facture_tva_15pct.pdf
└── *_ground_truth.json  (×7)
```

## Les 7 fixtures

| Fichier | Type | Scénario | Anomalie |
|---------|------|----------|----------|
| `facture_yoni_sas_propre.pdf` | facture | normal | — |
| `facture_scan_flou.png` | facture | normal | dégradation GaussianBlur r=2 |
| `facture_rotated_15.jpg` | facture | normal | rotation 15° |
| `facture_siret_mismatch.pdf` | facture | siret_incoherent | SIRET_INCOHERENT |
| `attestation_siret_different.pdf` | attestation_urssaf | siret_incoherent | SIRET_INCOHERENT |
| `attestation_urssaf_expiree.pdf` | attestation_urssaf | date_expiree | DATE_EXPIREE |
| `facture_tva_15pct.pdf` | facture | tva_incoherente | TVA_INCOHERENTE |

### Détail des fixtures

**1. `facture_yoni_sas_propre.pdf`** — Facture nominale sans anomalie. Fournisseur : Yoni SAS (SIRET `12345678901234`), montant HT 1 000 €, TVA 200 €, TTC 1 200 €.

**2. `facture_scan_flou.png`** — Même facture convertie en image PNG avec un filtre `GaussianBlur(radius=2)` simulant un scan dégradé. Ground truth identique à la fixture 1 avec champ `"degradation": "gaussian_blur_radius_2"`.

**3. `facture_rotated_15.jpg`** — Même facture en JPEG avec une rotation de −15° (fond blanc). Ground truth identique à la fixture 1 avec champ `"degradation": "rotation_15deg"`.

**4. `facture_siret_mismatch.pdf`** — Facture Yoni SAS dont le SIRET affiché (`99999999999999`) diffère du SIRET réel (`12345678901234`). Anomalie : `SIRET_INCOHERENT`.

**5. `attestation_siret_different.pdf`** — Attestation URSSAF de Yoni SAS dont le SIRET affiché (`88888888888888`) diffère du SIRET réel. Anomalie : `SIRET_INCOHERENT`.

**6. `attestation_urssaf_expiree.pdf`** — Attestation URSSAF Louise Corp avec date d'expiration `2022-01-01` (dans le passé). Anomalie : `DATE_EXPIREE`.

**7. `facture_tva_15pct.pdf`** — Facture Brawn Dunel SARL avec TVA de 150 € (15 %) au lieu de 200 € (20 %). Anomalie : `TVA_INCOHERENTE`.

## Différence avec le dataset principal

| Aspect | Dataset principal | Fixtures |
|--------|-------------------|----------|
| Valeurs | Aléatoires (seed configurable) | Fixes et connues |
| Assertions | Approximatives | Exactes (bit à bit) |
| Volume | 100+ documents | 7 documents |
| Dégradations PNG | Régénérées à chaque run | Régénérées à chaque run (seed=0) |
| Usage | Entraînement / évaluation ML | Tests unitaires / CI |

Les fixtures permettent des assertions exactes sur les valeurs numériques (ex. `montant_ttc == 1200.00`) et les codes d'anomalie, ce qui n'est pas garanti avec le dataset principal dont les valeurs varient selon la graine.
