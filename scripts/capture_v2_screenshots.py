#!/usr/bin/env python3
"""Full-page & section screenshots for v2 redesign QA."""
from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "screenshots" / "v2"
BASE = "http://127.0.0.1:8765"

FULL_PAGES = [
    ("home", "/"),
    ("posts", "/posts/"),
    ("article", "/posts/carburant-a-121-le-plein-la-clause-que-beaucoup-d-entrepreneurs-oublient-dans-leurs-devis/"),
    ("404", "/404.html"),
]

SECTIONS = [
    ("idees", "#idees"),
    ("projets", "#projets"),
    ("contact", "#contact"),
]

VIEWPORTS = [
    ("1440", 1440, 900),
    ("390", 390, 844),
]


def shot(page, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(path), full_page=True)
    print(path)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for vname, w, h in VIEWPORTS:
            ctx = browser.new_context(viewport={"width": w, "height": h})
            page = ctx.new_page()
            for slug, url in FULL_PAGES:
                page.goto(f"{BASE}{url}", wait_until="networkidle", timeout=90000)
                page.wait_for_timeout(600)
                shot(page, OUT / f"{slug}-{vname}.png")
            page.goto(f"{BASE}/", wait_until="networkidle", timeout=90000)
            for slug, hash_id in SECTIONS:
                page.evaluate(f"document.querySelector('{hash_id}')?.scrollIntoView({{block:'start'}})")
                page.wait_for_timeout(500)
                el = page.locator(hash_id)
                shot(page, OUT / f"{slug}-{vname}.png")
            ctx.close()
        browser.close()


if __name__ == "__main__":
    main()
