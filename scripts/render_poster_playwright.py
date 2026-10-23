#!/usr/bin/env python3
"""Rendu affiche 1280×800 avec Montserrat (navigateur)."""
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "scripts" / "poster-mutuelle.html"
OUT = ROOT / "img" / "mutuelle-cinq-refus.jpg"


def main() -> None:
    url = HTML.as_uri()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto(url, wait_until="networkidle")
        page.wait_for_timeout(300)
        page.screenshot(path=str(OUT), type="jpeg", quality=92)
        browser.close()
    print(OUT)


if __name__ == "__main__":
    main()
