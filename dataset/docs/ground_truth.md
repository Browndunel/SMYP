# Format du ground truth JSON

## Schéma complet

```json
{
  "id": "409db9b4-3c54-43a8-8e39-38accb4d2ed2",
  "type": "facture",
  "scenario": "tva_incoherente",

  "fournisseur": {
    "nom": "Claire Moreau Transport SAS",
    "siret": "93406088356159",
    "adresse": "74 avenue Laporte\n68501 Carpentier-sur-Salmon"
  },
  "client": {
    "nom": "Alice Martin Commerce SASU",
    "siret": "51484656482366"
  },

  "montant_ht": 16348.70,
  "tva_taux": 20,
  "tva_montant": 2452.30,
  "montant_ttc": 18801.00,

  "date_emission": "2026-03-02",
  "date_echeance": "2026-04-16",
  "numero_document": "FAC-2024-9379",

  "coherent": false,
  "anomalies": ["TVA_INCOHERENTE"],

  "fichiers": {
    "pdf": "facture_tva_incoherente_409db9b4.pdf",
    "png_original": "facture_tva_incoherente_409db9b4_original.png",
    "png_scans": {
      "low":        "facture_tva_incoherente_409db9b4_low.png",
      "medium":     "facture_tva_incoherente_409db9b4_medium.png",
      "high":       "facture_tva_incoherente_409db9b4_high.png",
      "smartphone": "facture_tva_incoherente_409db9b4_smartphone.jpg"
    }
  }
}
```

## Description des champs

| Champ | Type | Description |
|-------|------|-------------|
| `id` | string (UUID4) | Identifiant unique du document |
| `type` | enum | `facture` \| `devis` \| `attestation_urssaf` \| `kbis` \| `rib` |
| `scenario` | enum | Scénario effectivement appliqué (peut différer du tirage si incompatible) |
| `fournisseur.siret` | string (14 chiffres) | SIRET **réel** de référence, même en cas d'anomalie |
| `montant_ht` | float | Sous-total hors taxes |
| `tva_taux` | int | Taux de TVA de référence (toujours 20 pour les documents commerciaux) |
| `tva_montant` | float | Montant TVA affiché sur le document (peut être erroné) |
| `montant_ttc` | float | Total toutes taxes comprises (`ht + tva_montant`) |
| `date_emission` | string (ISO 8601) | Date de création du document |
| `date_echeance` | string (ISO 8601) | Date limite de paiement / validité / expiration |
| `coherent` | bool | `false` dès qu'au moins une anomalie est détectée |
| `anomalies` | list[string] | Liste des codes d'anomalie détectés |
| `fichiers` | object | Noms des fichiers associés (relatifs à leur dossier) |

## Codes d'anomalie

| Code | Description |
|------|-------------|
| `SIRET_INCOHERENT` | Le SIRET affiché sur le PDF diffère du SIRET réel |
| `DATE_EXPIREE` | La date d'expiration ou de validité est dans le passé |
| `TVA_INCOHERENTE` | Le montant TVA ne correspond pas à `ht × 0.20` |
| `IBAN_INCOHERENT` | Le checksum IBAN est invalide (RIB falsifié) |

## Champs spécifiques par type

### `siret_incoherent` et `falsifie`
Deux champs supplémentaires sont ajoutés pour faciliter l'évaluation :
```json
{
  "siret_attendu": "93406088356159",
  "siret_reel":    "51484656482366"
}
```

### `kbis`
Champs additionnels spécifiques à l'extrait Kbis :
```json
{
  "forme_juridique": "SARL",
  "capital_social": 10000,
  "code_ape": "6201Z",
  "dirigeant": "Alice Martin"
}
```

### `rib`
Champs additionnels spécifiques au RIB :
```json
{
  "iban": "FR76 1234 5678 9012 3456 7890 123",
  "bic": "BNPAFRPP"
}
```

## Documents sans données financières

Pour `attestation_urssaf`, `kbis` et `rib`, les champs financiers sont neutres :
```json
{
  "montant_ht": 0.0,
  "tva_taux": 0,
  "tva_montant": 0.0,
  "montant_ttc": 0.0
}
```

## `labels.csv`

Fichier CSV généré à la racine du dataset (et dans chaque sous-dossier train/test si split activé). Contient une ligne par document.

| Colonne | Type | Description |
|---------|------|-------------|
| `file_name` | string | Nom du PDF (relatif à `raw/`) |
| `doc_type` | enum | Type de document (`facture`, `devis`, `attestation_urssaf`, `kbis`, `rib`) |
| `is_fraud` | bool | `True` si `anomalies` est non vide |
| `anomaly_type` | string | Codes d'anomalie séparés par `\|`, vide si cohérent (ex. `SIRET_INCOHERENT\|TVA_INCOHERENTE`) |
| `expected_siret` | string | SIRET réel de référence (toujours celui du fournisseur) |
| `montant_ttc` | float | Montant TTC ; `0.0` pour attestation, kbis et rib |
| `tva_rate` | int | Taux TVA de référence ; `0` pour attestation, kbis et rib |
| `date_expiration` | string ISO | Date d'expiration ou de validité ; vide si non applicable |
| `degradation_level` | string | Toujours `"none"` (les PNG dégradés sont dans `scans/`, pas dans `raw/`) |

## `scenarios.json`

Fichier JSON généré à la racine du dataset décrivant le catalogue des scénarios utilisés lors de la génération.

```json
{
  "generated_at": "2026-03-16T14:30:00",
  "doc_types": ["facture", "devis", "attestation_urssaf", "kbis", "rib"],
  "scenario_distribution_used": {
    "normal":           0.50,
    "siret_incoherent": 0.15,
    "date_expiree":     0.15,
    "tva_incoherente":  0.10,
    "falsifie":         0.10
  },
  "scenarios": [
    {
      "name": "normal",
      "description": "Tous les champs sont cohérents",
      "anomalies": []
    },
    ...
  ]
}
```

## `dataset_summary.json`

Fichier récapitulatif généré à la racine du dataset :

```json
{
  "generated_at": "2026-03-16T14:30:00",
  "seed": 42,
  "n_per_type": 20,
  "total_documents": 100,
  "scenario_distribution": { ... },
  "degradation_levels": ["low", "medium", "high"],
  "team_names": ["Alice Martin", "Bob Dupont"],
  "stats_par_type": {
    "facture": { "total": 20, "coherent": 13, "incoherent": 7 },
    ...
  },
  "documents": [ ... ]   ← entrée résumée pour chaque document
}
```
