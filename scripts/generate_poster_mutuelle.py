#!/usr/bin/env python3
"""Génère un visuel affiche 16:10 pour le post mutuelle (1280×800)."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "img" / "mutuelle-cinq-refus.jpg"
W, H = 1280, 800
BLUE = (47, 111, 224)
MAGENTA = (224, 51, 143)
BLACK = (5, 7, 12)
WHITE = (255, 255, 255)
MUTED = (180, 190, 205)

TITLE = "Cinq demandes de remboursement à la mutuelle."
SUB = "Cinq refus."


def radial(img: Image.Image, cx: float, cy: float, r: float, color: tuple[int, int, int, int]) -> None:
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    steps = 80
    for i in range(steps, 0, -1):
        t = i / steps
        alpha = int(color[3] * t * t)
        rad = r * t
        draw.ellipse((cx - rad, cy - rad, cx + rad, cy + rad), fill=(color[0], color[1], color[2], alpha))
    img.alpha_composite(overlay)


def main() -> None:
    img = Image.new("RGBA", (W, H), BLACK + (255,))
    radial(img, W * 0.08, H * 0.92, W * 0.55, (*BLUE, 140))
    radial(img, W * 0.92, H * 0.88, W * 0.5, (*MAGENTA, 120))

    draw = ImageDraw.Draw(img)
    font_path = ROOT / "assets" / "fonts" / "montserrat-latin.woff2"
    try:
        from fontTools.ttLib import TTFont  # noqa: F401 — optional
    except ImportError:
        pass
    # Pillow needs TTF; use DejaVu bold as fallback if Montserrat woff2 unavailable
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 52)
        sub_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72)
        tag_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
    except OSError:
        title_font = ImageFont.load_default()
        sub_font = title_font
        tag_font = title_font

    draw.text((W * 0.08, H * 0.12), "SÉBASTIEN MOT", font=tag_font, fill=MUTED)
    y = H * 0.28
    for line in [TITLE, SUB]:
        draw.text((W * 0.08, y), line.upper(), font=sub_font if line == SUB else title_font, fill=WHITE)
        y += 90 if line == TITLE else 100

    rgb = img.convert("RGB")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    rgb.save(OUT, "JPEG", quality=92, optimize=True)
    print(f"Wrote {OUT} ({W}x{H})")


if __name__ == "__main__":
    main()
