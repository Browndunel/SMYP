# Scénarios et anomalies

## Les 5 scénarios

### `normal`
Tous les champs sont cohérents entre eux. Le JSON retourne `"coherent": true` et `"anomalies": []`.

### `siret_incoherent`
Le SIRET affiché sur le document PDF est différent du SIRET réel de l'entreprise.
Le ground truth stocke les deux valeurs pour permettre la comparaison :

```json
{
  "coherent": false,
  "anomalies": ["SIRET_INCOHERENT"],
  "siret_attendu": "93406088356159",
  "siret_reel":    "51484656482366"
}
```

Le champ `fournisseur.siret` dans le JSON contient toujours le **SIRET réel** de référence.

### `date_expiree`
La date d'expiration du document est dans le passé.

- **Devis** : date de validité expirée (1 à 60 jours dans le passé)
- **Attestation URSSAF** : date d'expiration entre 1 et 24 mois dans le passé

Sur le PDF de l'attestation, la date expirée est affichée en rouge.

```json
{
  "coherent": false,
  "anomalies": ["DATE_EXPIREE"]
}
```

### `tva_incoherente`
Le montant de TVA affiché ne correspond pas au taux de 20 % appliqué. Un taux erroné est choisi parmi `[5%, 8%, 10%, 12%, 15%]`.

```json
{
  "montant_ht": 16348.70,
  "tva_taux": 20,
  "tva_montant": 2452.30,   ← calculé avec ~15% au lieu de 20%
  "montant_ttc": 18801.00,
  "coherent": false,
  "anomalies": ["TVA_INCOHERENTE"]
}
```

La TVA correcte théorique serait `16348.70 × 0.20 = 3269.74`.

### `falsifie`
Combinaison de plusieurs anomalies selon le type de document :

| Type               | Anomalies cumulées                          |
|--------------------|---------------------------------------------|
| facture            | SIRET_INCOHERENT + TVA_INCOHERENTE          |
| devis              | SIRET_INCOHERENT + DATE_EXPIREE + TVA_INCOHERENTE |
| attestation_urssaf | SIRET_INCOHERENT + DATE_EXPIREE             |
| kbis               | SIRET_INCOHERENT                            |
| rib                | IBAN_INCOHERENT (checksum altéré)           |

## Détection des anomalies

La détection est faite **à la génération**, pas après coup. Chaque générateur calcule le tableau `anomalies` en comparant les valeurs générées :

```python
# Exemple dans facture.py
anomalies = []
if siret_affiche != siret_fournisseur:
    anomalies.append("SIRET_INCOHERENT")
if abs(tva - round(ht * 0.20, 2)) > 0.01:
    anomalies.append("TVA_INCOHERENTE")
```

`"coherent": false` dès qu'`anomalies` est non vide.

## Distribution par défaut

```python
scenario_distribution = {
    "normal":           0.50,   # 50% de documents sains
    "siret_incoherent": 0.15,
    "date_expiree":     0.15,
    "tva_incoherente":  0.10,
    "falsifie":         0.10,
}
```

Le tirage est pondéré (`random.choices`) et indépendant pour chaque document. Les proportions effectives peuvent légèrement varier selon `n_per_type`.

## Comportement de fallback

Quand un scénario n'est pas supporté par un type de document, `_resolve_scenario()` le remplace silencieusement par le scénario le plus proche. Le ground truth JSON contient le scénario **effectivement appliqué** (après résolution), pas le scénario tiré initialement.

Exemple : `rib` + `siret_incoherent` → ground truth contient `"scenario": "falsifie"`.

La table de compatibilité complète est visible dans `docs/architecture.md` (section "Compatibilité des scénarios"). En résumé :

| Scénario tiré | rib | facture | attestation_urssaf | kbis |
|---------------|-----|---------|-------------------|------|
| `siret_incoherent` | → `falsifie` | ✓ | ✓ | ✓ |
| `date_expiree` | → `normal` | → `normal` | ✓ | → `normal` |
| `tva_incoherente` | → `normal` | ✓ | → `normal` | → `normal` |

Ce comportement est transparent pour les consommateurs du dataset : le champ `scenario` dans le JSON de ground truth reflète toujours ce qui a été réellement généré.
