"""
Fonctions de dégradation d'image simulant des scans de mauvaise qualité.
Trois niveaux : low, medium, high.

Fonction séparée degrade_image_smartphone() pour simuler une photo prise
avec un smartphone (perspective, éclairage inégal, flou bords, bruit chromatique).
"""
import random
import io
import numpy as np
from PIL import Image, ImageFilter, ImageDraw


# ---------------------------------------------------------------------------
# Paramètres par niveau
# ---------------------------------------------------------------------------

_LEVEL_PARAMS = {
    "low": {
        "rotation_range": (-1.0, 1.0),
        "blur_radius": (0.0, 0.5),
        "noise_intensity": 5,
        "jpeg_quality": (82, 90),
        "pixelize_chance": 0.0,
        "pixelize_factor": 1,
    },
    "medium": {
        "rotation_range": (-2.0, 2.0),
        "blur_radius": (0.3, 1.2),
        "noise_intensity": 18,
        "jpeg_quality": (70, 80),
        "pixelize_chance": 0.3,
        "pixelize_factor": 2,
    },
    "high": {
        "rotation_range": (-3.0, 3.0),
        "blur_radius": (0.8, 2.0),
        "noise_intensity": 40,
        "jpeg_quality": (55, 68),
        "pixelize_chance": 0.6,
        "pixelize_factor": 3,
    },
}


# ---------------------------------------------------------------------------
# Transformations élémentaires
# ---------------------------------------------------------------------------

def _apply_rotation(img: Image.Image, angle: float) -> Image.Image:
    """Rotation légère avec fond blanc."""
    return img.rotate(angle, expand=False, fillcolor=(255, 255, 255))


def _apply_gaussian_blur(img: Image.Image, radius: float) -> Image.Image:
    if radius <= 0:
        return img
    return img.filter(ImageFilter.GaussianBlur(radius=radius))


def _apply_noise(img: Image.Image, intensity: int) -> Image.Image:
    """Ajoute du bruit gaussien sur les canaux RGB."""
    arr = np.array(img).astype(np.int16)
    noise = np.random.randint(-intensity, intensity + 1, arr.shape, dtype=np.int16)
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


def _apply_jpeg_compression(img: Image.Image, quality: int) -> Image.Image:
    """Simule la compression JPEG d'un scanner."""
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality, optimize=True)
    buf.seek(0)
    return Image.open(buf).copy()


def _apply_pixelization(img: Image.Image, factor: int) -> Image.Image:
    """Flou par pixélisation (downscale puis upscale)."""
    if factor <= 1:
        return img
    w, h = img.size
    small = img.resize((w // factor, h // factor), Image.BOX)
    return small.resize((w, h), Image.NEAREST)


def _apply_perspective(img: Image.Image, strength: float = 0.05) -> Image.Image:
    """Déforme l'image en trapèze pour simuler une prise de vue en angle."""
    w, h = img.size
    dx = int(w * strength)
    dy = int(h * strength * 0.5)
    src = [0, 0, w, 0, w, h, 0, h]
    dst = [
        random.randint(0, dx),      random.randint(0, dy),
        w - random.randint(0, dx),  random.randint(0, dy),
        w - random.randint(0, dx),  h - random.randint(0, dy),
        random.randint(0, dx),      h - random.randint(0, dy),
    ]
    coeffs = _perspective_coeffs(dst, src)
    return img.transform((w, h), Image.PERSPECTIVE, coeffs, Image.BICUBIC,
                         fillcolor=(255, 255, 255))


def _perspective_coeffs(pa: list, pb: list) -> list:
    """Calcule les 8 coefficients de transformation perspective (pa → pb)."""
    matrix = []
    for p1, p2 in zip(pa[::2], pa[1::2]):
        matrix.append([p1, p2, 1, 0, 0, 0, 0, 0])
        matrix.append([0, 0, 0, p1, p2, 1, 0, 0])
    for i, (p1, p2) in enumerate(zip(pb[::2], pb[1::2])):
        matrix[2 * i][6]     = -p1 * pb[2 * i]
        matrix[2 * i][7]     = -p1 * pb[2 * i + 1]
        matrix[2 * i + 1][6] = -p2 * pb[2 * i]
        matrix[2 * i + 1][7] = -p2 * pb[2 * i + 1]
    A = np.array(matrix, dtype=np.float64)
    b = np.array(pb, dtype=np.float64)
    return list(np.linalg.solve(A, b))


def _apply_lighting_gradient(img: Image.Image) -> Image.Image:
    """Simule un éclairage inégal : vignettage sombre + hotspot lumineux."""
    w, h = img.size
    arr = np.array(img).astype(np.float32)

    Y, X = np.ogrid[:h, :w]
    cx, cy = w / 2, h / 2
    dist = np.sqrt(((X - cx) / cx) ** 2 + ((Y - cy) / cy) ** 2)
    vignette = 1.0 - np.clip(dist * 0.4, 0, 0.35)

    hx = random.uniform(0.2, 0.8) * w
    hy = random.uniform(0.1, 0.5) * h
    spot_dist = np.sqrt(((X - hx) / (w * 0.4)) ** 2 + ((Y - hy) / (h * 0.4)) ** 2)
    hotspot = np.clip(1.0 - spot_dist * 0.6, 0, 0.15)

    mask = (vignette + hotspot)[..., np.newaxis]
    arr = np.clip(arr * (0.85 + mask * 0.3), 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


def _apply_edge_blur(img: Image.Image, strength: float = 2.5) -> Image.Image:
    """Flou plus fort sur les bords, net au centre (mise au point smartphone)."""
    w, h = img.size
    blurred = img.filter(ImageFilter.GaussianBlur(radius=strength))

    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    margin_x, margin_y = int(w * 0.25), int(h * 0.25)
    draw.ellipse([margin_x, margin_y, w - margin_x, h - margin_y], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=min(w, h) * 0.12))

    return Image.composite(img, blurred, mask)


def _apply_chromatic_noise(img: Image.Image, intensity: int = 25) -> Image.Image:
    """Bruit chromatique (canaux R/G/B indépendants) typique capteur smartphone."""
    arr = np.array(img).astype(np.int16)
    for c in range(3):
        noise = np.random.randint(-intensity, intensity + 1, arr[:, :, c].shape, dtype=np.int16)
        arr[:, :, c] = np.clip(arr[:, :, c] + noise, 0, 255)
    return Image.fromarray(arr.astype(np.uint8))


# ---------------------------------------------------------------------------
# Fonction principale
# ---------------------------------------------------------------------------

def degrade_image(img: Image.Image, level: str = "medium") -> Image.Image:
    """
    Applique une combinaison de dégradations simulant un scan.

    Args:
        img:   Image PIL source (RGB).
        level: Niveau de dégradation parmi 'low', 'medium', 'high'.

    Returns:
        Image PIL dégradée (RGB).
    """
    if level not in _LEVEL_PARAMS:
        raise ValueError(f"Niveau inconnu : {level!r}. Choisir parmi {list(_LEVEL_PARAMS)}")

    p = _LEVEL_PARAMS[level]

    if img.mode != "RGB":
        img = img.convert("RGB")

    # 1. Rotation
    angle = random.uniform(*p["rotation_range"])
    img = _apply_rotation(img, angle)

    # 2. Flou gaussien
    blur_radius = random.uniform(*p["blur_radius"])
    img = _apply_gaussian_blur(img, blur_radius)

    # 3. Bruit
    img = _apply_noise(img, p["noise_intensity"])

    # 4. Pixélisation (optionnelle)
    if random.random() < p["pixelize_chance"]:
        img = _apply_pixelization(img, p["pixelize_factor"])

    # 5. Compression JPEG
    quality = random.randint(*p["jpeg_quality"])
    img = _apply_jpeg_compression(img, quality)

    return img


def degrade_image_smartphone(img: Image.Image) -> Image.Image:
    """
    Simule une photo prise avec un smartphone de qualité moyenne.

    Effets appliqués :
    - Rotation ±5°–15° (document posé en angle)
    - Déformation perspective légère (prise de vue non frontale)
    - Éclairage inégal : vignettage + hotspot
    - Flou de mise au point sur les bords
    - Bruit chromatique (capteur CMOS)
    - Compression JPEG agressive

    Returns:
        Image PIL dégradée (RGB).
    """
    if img.mode != "RGB":
        img = img.convert("RGB")

    # 1. Rotation plus prononcée qu'un scan
    angle = random.uniform(5, 15) * random.choice([-1, 1])
    img = _apply_rotation(img, angle)

    # 2. Perspective (déformation trapézoïdale)
    strength = random.uniform(0.03, 0.08)
    img = _apply_perspective(img, strength)

    # 3. Éclairage inégal
    img = _apply_lighting_gradient(img)

    # 4. Flou bords (mise au point centrale)
    edge_blur = random.uniform(1.5, 3.5)
    img = _apply_edge_blur(img, edge_blur)

    # 5. Bruit chromatique capteur
    noise_intensity = random.randint(15, 35)
    img = _apply_chromatic_noise(img, noise_intensity)

    # 6. Compression JPEG smartphone (qualité variable)
    quality = random.randint(60, 82)
    img = _apply_jpeg_compression(img, quality)

    return img
