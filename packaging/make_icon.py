"""
Genera el icono de la aplicación (ICO multirresolución) en ``resources/icons``.

El icono representa una curva característica del ítem sobre un fondo azul.

Uso:
    python packaging/make_icon.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SIZE = 512
BLUE = (42, 120, 214, 255)
WHITE = (255, 255, 255, 255)
ORANGE = (235, 104, 52, 255)


def draw_icon(size: int = SIZE, supersample: int = 4) -> Image.Image:
    """Dibuja el icono a mayor resolución y lo reduce (bordes suaves)."""
    big = size * supersample
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, big - 1, big - 1], radius=int(big * 0.2), fill=BLUE)
    m = big * 0.16
    x = np.linspace(-4, 4, 1200)
    y = 0.2 + 0.8 / (1 + np.exp(-1.6 * x))  # ICC 3PL (a=1.6, b=0, c=0.2)
    px = m + (x + 4) / 8 * (big - 2 * m)
    py = big - m - y * (big - 2 * m)
    base_w = big // 70
    d.line([(big * 0.14, big - m), (big * 0.86, big - m)], fill=(255, 255, 255, 140), width=base_w)
    rad = big / 44  # trazo redondo: discos a lo largo de la curva
    for cx, cy in zip(px, py):
        d.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], fill=WHITE)
    cx, cy = px[600], py[600]
    r2 = big * 0.058
    d.ellipse([cx - r2 - big / 120, cy - r2 - big / 120, cx + r2 + big / 120, cy + r2 + big / 120], fill=WHITE)
    d.ellipse([cx - r2, cy - r2, cx + r2, cy + r2], fill=ORANGE)
    return img.resize((size, size), Image.LANCZOS)


def main() -> None:
    out = ROOT / "resources" / "icons"
    out.mkdir(parents=True, exist_ok=True)
    img = draw_icon()
    img.save(out / "meritum_cat.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64),
                                                (128, 128), (256, 256)])
    print("Icono generado en", out)


if __name__ == "__main__":
    main()
