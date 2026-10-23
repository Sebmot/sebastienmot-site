#!/usr/bin/env python3
"""Full-page screenshots — docs/screenshots/final/ (1440 + 390)."""
from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "screenshots" / "final"
BASE = "http://127.0.0.1:8765"

PAGES = [
    ("home", "/"),
    ("posts", "/posts/"),
    ("article", "/posts/carburant-a-121-le-plein-la-clause-que-beaucoup-d-entrepreneurs-oublient-dans-leurs-devis/"),
    ("idees", "/#idees"),
    ("projets", "/#projets"),
    ("contact", "/#contact"),
    ("404", "/404.html"),
]

VIEWPORTS = [("1440", 1440, 900), ("390", 390, 844)]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for vname, w, h in VIEWPORTS:
            ctx = browser.new_context(viewport={"width": w, "height": h})
            page = ctx.new_page()
            for slug, url in PAGES:
                page.goto(f"{BASE}{url}", wait_until="networkidle", timeout=90000)
                page.wait_for_timeout(700)
                dest = OUT / f"{slug}-{vname}.png"
                page.screenshot(path=str(dest), full_page=True)
                print(dest)
            ctx.close()
        browser.close()


if __name__ == "__main__":
    main()
