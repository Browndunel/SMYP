# Benchmark — Choix de la stack technique

## Contexte

L'objectif est de générer un dataset synthétique de documents administratifs français. Cela implique quatre besoins distincts :

1. **Générer des données** réalistes (noms, SIRET, montants, dates)
2. **Créer des PDFs** structurés à partir de ces données
3. **Convertir les PDFs en images** PNG
4. **Dégrader les images** pour simuler des scans de qualité variable

Chaque besoin a été évalué indépendamment avant de retenir la stack finale.

---

## Stack retenue

```
Faker  →  fpdf2  →  pdf2image  →  Pillow
 (1)        (2)         (3)          (4)
```

Quatre librairies Python, aucune dépendance externe côté code (seul `poppler` est requis au niveau système pour `pdf2image`).

---

## Évaluation par brique

### 1. Génération de données — `Faker`


| Librairie                  | Locale `fr_FR` | SIRET / IBAN             | Maintenance | Verdict      |
| -------------------------- | -------------- | ------------------------ | ----------- | ------------ |
| **Faker**                  | ✓              | partiel (helpers custom) | active      | ✅ retenu     |
| mimesis                    | ✓              | limité                   | active      | ✗            |
| SDV (Synthetic Data Vault) | ✗              | ✗                        | active      | ✗ trop lourd |


**Pourquoi Faker ?**
Faker est la référence Python pour les données synthétiques localisées. La locale `fr_FR` couvre noms, adresses, entreprises, numéros de téléphone. Les données spécifiques au droit français (SIRET 14 chiffres, IBAN FR27, TVA intracommunautaire) ont été implémentées en custom helpers au-dessus de Faker — ce qui prend moins de 50 lignes et donne un contrôle total sur les formules de calcul.

---

### 2. Génération de PDFs — `fpdf2`


| Librairie           | API Python native | Poids | Tableaux | UTF-8 | Verdict                 |
| ------------------- | ----------------- | ----- | -------- | ----- | ----------------------- |
| **fpdf2**           | ✓                 | léger | ✓        | ✓     | ✅ retenu                |
| ReportLab           | ✓                 | lourd | ✓        | ✓     | ✗ sur-dimensionné       |
| WeasyPrint          | HTML/CSS          | lourd | via CSS  | ✓     | ✗ dépendances système   |
| pdfkit              | HTML/CSS          | léger | via CSS  | ✓     | ✗ nécessite wkhtmltopdf |
| Jinja2 + WeasyPrint | HTML/CSS          | lourd | via CSS  | ✓     | ✗ deux outils           |


**Pourquoi fpdf2 ?**
`fpdf2` est le successeur maintenu de `fpdf`. Il génère des PDFs directement en Python sans passer par HTML/CSS ni nécessiter de binaire externe. L'API impérative (`cell`, `multi_cell`, `set_font`) est adaptée à des documents tabulaires comme des factures. ReportLab aurait été possible mais son API est plus verbeuse et la librairie pèse davantage pour un cas d'usage simple.

---

### 3. Conversion PDF → image — `pdf2image`


| Librairie          | Qualité rendu   | API simple | Dépendances       | Verdict                            |
| ------------------ | --------------- | ---------- | ----------------- | ---------------------------------- |
| **pdf2image**      | haute (poppler) | ✓          | poppler (système) | ✅ retenu                           |
| PyMuPDF (fitz)     | haute           | ✓          | binaire MuPDF     | ✗ licence AGPL                     |
| pdfplumber         | moyen           | ✓          | pdfminer          | ✗ pas de rendu image               |
| Wand (ImageMagick) | haute           | moyen      | ImageMagick       | ✗ politique de sécurité par défaut |


**Pourquoi pdf2image ?**
`pdf2image` s'appuie sur `pdftoppm` de poppler, qui est le moteur de rendu PDF le plus fidèle disponible en open source. L'API est minimaliste : `convert_from_bytes(pdf_bytes, dpi=150)` retourne directement une liste d'objets PIL. PyMuPDF aurait été une alternative solide techniquement mais son modèle de licence AGPL peut poser problème selon l'usage du dataset.

---

### 4. Dégradation d'image — `Pillow`


| Librairie    | Filtres | Numpy compatible | Poids | Verdict           |
| ------------ | ------- | ---------------- | ----- | ----------------- |
| **Pillow**   | ✓       | ✓                | léger | ✅ retenu          |
| OpenCV       | ✓       | ✓                | lourd | ✗ sur-dimensionné |
| scikit-image | ✓       | ✓                | lourd | ✗ sur-dimensionné |
| imageio      | limité  | ✓                | léger | ✗ pas de filtres  |


**Pourquoi Pillow ?**
Pillow est déjà une dépendance transitive de `pdf2image`. Il fournit nativement `GaussianBlur`, `Image.rotate()` et la compression JPEG par buffer. Pour le bruit, numpy complète Pillow avec une manipulation tableau rapide. OpenCV et scikit-image auraient été surdimensionnés pour des transformations aussi ciblées.

---

## Le workflow complet

```
┌─────────────────────────────────────────────────────────┐
│                       Faker (fr_FR)                      │
│  noms · SIRET · adresses · montants · dates · IBAN       │
└──────────────────────────┬──────────────────────────────┘
                           │ dict de données
                           ▼
┌─────────────────────────────────────────────────────────┐
│                         fpdf2                            │
│  mise en page · tableaux · couleurs · mentions légales   │
└──────────────────────────┬──────────────────────────────┘
                           │ bytes PDF
                           ▼
┌─────────────────────────────────────────────────────────┐
│               pdf2image + poppler                        │
│  rendu haute fidélité à 150 dpi → PIL Image (RGB)        │
└──────────────────────────┬──────────────────────────────┘
                           │ PIL Image
                           ▼
┌─────────────────────────────────────────────────────────┐
│                   Pillow + numpy                         │
│  rotation · flou gaussien · bruit · JPEG · pixélisation  │
│  × 3 niveaux : low / medium / high                       │
└──────────────────────────┬──────────────────────────────┘
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
        PNG dégradé              JSON ground truth
```

---

## Résumé


| Besoin               | Outil retenu   | Alternative écartée | Raison du choix                                   |
| -------------------- | -------------- | ------------------- | ------------------------------------------------- |
| Données synthétiques | Faker          | mimesis             | Locale fr_FR plus riche                           |
| Génération PDF       | fpdf2          | ReportLab           | API plus légère, pas de dépendance HTML           |
| PDF → image          | pdf2image      | PyMuPDF             | Licence open source permissive                    |
| Dégradation          | Pillow + numpy | OpenCV              | Déjà en dépendance, suffisant pour le cas d'usage |


La stack finale est **100 % Python**, installable en une commande (`pip install -r requirements.txt` + `brew install poppler`), et ne nécessite aucun service externe ni binaire propriétaire.