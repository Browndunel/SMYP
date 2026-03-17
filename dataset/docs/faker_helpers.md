# Génération de données françaises

## SIRET

```python
from utils.faker_helpers import generate_siret
siret = generate_siret()  # "37957367303678"
```

Génère 14 chiffres aléatoires (9 chiffres SIREN + 5 chiffres NIC). Les SIRET ne sont pas Luhn-validés — ils sont syntaxiquement corrects mais ne correspondent pas à des entreprises réelles.

## TVA intracommunautaire

```python
from utils.faker_helpers import generate_tva_intra
tva = generate_tva_intra(siret)  # "FR07379573673"
```

Format : `FR` + clé à 2 chiffres + 9 premiers chiffres du SIRET (= SIREN).
La clé est calculée par : `(12 + 3 × (SIREN mod 97)) mod 97`.

## RIB complet

```python
from utils.faker_helpers import generate_rib_data
rib = generate_rib_data()
```

Retourne un dictionnaire avec :

| Clé | Exemple | Description |
|-----|---------|-------------|
| `code_banque` | `"36358"` | 5 chiffres |
| `code_guichet` | `"56699"` | 5 chiffres |
| `numero_compte` | `"15646668639"` | 11 chiffres |
| `cle_rib` | `"67"` | 2 chiffres, formule modulo 97 |
| `iban` | `"FR76 3635 8566 9915 6466 8639 673"` | Formaté en groupes de 4 |
| `iban_raw` | `"FR7636358566991564668639673"` | 27 caractères bruts |
| `bic` | `"ZYUIFR8Q"` | 8 caractères |
| `banque` | `"Martin & Associés"` | Nom de banque fictif (faker) |

### Calcul de la clé RIB

Pour les comptes numériques :
```
clé = 97 - ((89 × code_banque + 15 × code_guichet + 3 × numéro_compte) mod 97)
```
Si le résultat vaut 97, la clé est 0.

### Calcul des chiffres de contrôle IBAN

Conformément à la norme ISO 13616 :
1. Construire `BBAN + "152700"` (F=15, R=27 en base numérique)
2. Calculer `98 - (int(chaîne) mod 97)`
3. Formater sur 2 chiffres

## BIC

```python
from utils.faker_helpers import generate_bic
bic = generate_bic()  # "ZYUIFR8Q"
```

4 lettres aléatoires + `FR` (code pays) + 2 caractères alphanumériques.

## Noms et adresses

```python
from utils.faker_helpers import random_company_name, random_address, random_person_name

random_company_name()                        # "Dupont Conseil SARL"
random_company_name(["Alice", "Bob"])        # "Alice Transport EURL"
random_address()                             # "12 rue de la Paix\n75001 Paris"
random_person_name()                         # "Jean-Pierre Martin"
random_person_name(["Alice", "Bob"])         # "Alice"
```

Les noms de société combinent aléatoirement : un nom de base + un secteur d'activité + une forme juridique.

Les secteurs disponibles : Conseil, Informatique, Services, BTP, Commerce, Industrie, Transport, Communication, Finance, Sécurité.

Les formes juridiques : SARL, SAS, EURL, SA, SASU, SNC.

## Noms d'équipe (Scénario S8)

```python
from utils.faker_helpers import TEAM_COMPANIES
```

`TEAM_COMPANIES` est une liste de 7 noms fixes représentant les entreprises de l'équipe projet :

```python
TEAM_COMPANIES = [
    "Yoni SAS",
    "Louise Corp",
    "Ludo & Associés",
    "Brawn Dunel SARL",
    "Eloic Services EURL",
    "Loan Conseil SAS",
    "Mathis & Co SARL",
]
```

### Utilisation dans `generate_dataset()`

```python
from utils.faker_helpers import TEAM_COMPANIES
generate_dataset(..., team_names=TEAM_COMPANIES)
```

Quand `team_names=TEAM_COMPANIES` est passé à `generate_dataset()`, **6 documents par type** (30 documents au total) utilisent ces noms en scénario `normal`. Cela permet d'inclure dans le dataset des documents dont les entreprises sont nommées d'après les membres de l'équipe.

Les noms sont passés à `random_company_name(team_names)` et `random_person_name(team_names)`, qui les utilisent comme base plutôt que de générer un nom aléatoire.
