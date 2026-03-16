# Dégradation des scans

## Objectif

Simuler les artefacts visuels typiques d'un document numérisé : légère inclinaison, flou, bruit de capteur, compression JPEG d'un scanner bas de gamme.

## Pipeline de transformations

Les transformations sont appliquées **dans cet ordre fixe** pour chaque image :

```
Image PIL source (RGB)
    │
    ├── 1. Rotation légère
    ├── 2. Flou gaussien
    ├── 3. Bruit gaussien (numpy)
    ├── 4. Pixélisation (optionnelle)
    └── 5. Compression JPEG
         │
         └── Image dégradée (RGB)
```

## Les 3 niveaux

| Paramètre | `low` | `medium` | `high` |
|-----------|-------|----------|--------|
| Rotation | ±1° | ±2° | ±3° |
| Flou gaussien (radius) | 0 – 0.5 | 0.3 – 1.2 | 0.8 – 2.0 |
| Intensité bruit (px) | ±5 | ±18 | ±40 |
| Qualité JPEG | 82 – 90 % | 70 – 80 % | 55 – 68 % |
| Pixélisation (probabilité) | 0 % | 30 % | 60 % |
| Facteur de pixélisation | × 1 | × 2 | × 3 |

Tous les paramètres dans une plage sont tirés aléatoirement à chaque appel.

## Détail des transformations

### 1. Rotation (`_apply_rotation`)
Utilise `Image.rotate()` avec `expand=False` et un fond blanc `(255, 255, 255)` pour ne pas changer les dimensions de l'image.

### 2. Flou gaussien (`_apply_gaussian_blur`)
Applique `ImageFilter.GaussianBlur(radius)`. Ignoré si `radius ≤ 0`.

### 3. Bruit gaussien (`_apply_noise`)
Convertit l'image en tableau numpy `int16`, ajoute un bruit uniforme dans `[-intensity, +intensity]` sur tous les canaux, puis recoupe dans `[0, 255]`.

```python
arr = np.array(img).astype(np.int16)
noise = np.random.randint(-intensity, intensity + 1, arr.shape)
arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
```

### 4. Pixélisation (`_apply_pixelization`)
Downscale l'image par `factor` puis upscale en mode `NEAREST` pour créer un effet de pixels carrés visible.

```python
small = img.resize((w // factor, h // factor), Image.BOX)
return small.resize((w, h), Image.NEAREST)
```

### 5. Compression JPEG (`_apply_jpeg_compression`)
Encode l'image en JPEG dans un buffer mémoire puis relit depuis ce buffer. Simule la perte de qualité d'un scanner qui sauvegarde en JPEG.

## Usage

```python
from utils.degradation import degrade_image
from PIL import Image

img = Image.open("document.png")

low    = degrade_image(img, level="low")
medium = degrade_image(img, level="medium")
high   = degrade_image(img, level="high")
```

## Exemples visuels

| Niveau | Apparence typique |
|--------|-------------------|
| `low` | Légèrement incliné, compression imperceptible — scan de bonne qualité |
| `medium` | Légèrement flou, bruit visible à l'agrandissement, JPEG visible |
| `high` | Flou notable, bruit important, artefacts de blocs JPEG, possible pixélisation |
