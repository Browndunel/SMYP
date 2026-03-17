"""
Fonctions de dégradation d'image simulant des scans de mauvaise qualité.
Trois niveaux : low, medium, high.
"""
import random
import io
import numpy as np
from PIL import Image, ImageFilter


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
