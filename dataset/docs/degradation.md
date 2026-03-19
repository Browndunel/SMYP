# Dégradation des images

Deux fonctions disponibles dans `utils/degradation.py`.

## `degrade_image(img, level)` — scan

Simule un document numérisé. Trois niveaux : `low`, `medium`, `high`.


| Paramètre                  | `low`     | `medium`  | `high`    |
| -------------------------- | --------- | --------- | --------- |
| Rotation                   | ±1°       | ±2°       | ±3°       |
| Flou gaussien (radius)     | 0 – 0.5   | 0.3 – 1.2 | 0.8 – 2.0 |
| Intensité bruit (px)       | ±5        | ±18       | ±40       |
| Qualité JPEG               | 82 – 90 % | 70 – 80 % | 55 – 68 % |
| Pixélisation (probabilité) | 0 %       | 30 %      | 60 %      |


## `degrade_image_smartphone(img)` — photo smartphone

Simule une photo prise avec un smartphone. Paramètres fixes (valeurs aléatoires dans les plages).


| Transformation                | Plage                      |
| ----------------------------- | -------------------------- |
| Rotation                      | ±5° – ±15°                 |
| Perspective (trapèze)         | 3 – 8 % de la largeur      |
| Vignettage + hotspot          | bords −35 %, hotspot +15 % |
| Flou bords (radius)           | 1.5 – 3.5 px               |
| Bruit chromatique (par canal) | ±15 – ±35 px               |
| Qualité JPEG                  | 60 – 82 %                  |


