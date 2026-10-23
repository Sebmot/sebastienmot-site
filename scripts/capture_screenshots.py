#!/usr/bin/env python3
"""Captures full-page screenshots for visual QA."""
from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "screenshots"
BASE = "http://127.0.0.1:8765"
PAGES = [
    ("home", "/"),
    ("posts", "/posts/"),
    ("post-sample", "/posts/carburant-a-121-le-plein-la-clause-que-beaucoup-d-entrepreneurs-oublient-dans-leurs-devis/"),
    ("404", "/404.html"),
]
VIEWPORTS = [
    ("desktop-1440", 1440, 900),
    ("laptop-1280", 1280, 800),
    ("mobile-390", 390, 844),
    ("mobile-430", 430, 932),
    ("mobile-360", 360, 780),
]


def main(prefix: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for vname, w, h in VIEWPORTS:
            context = browser.new_context(viewport={"width": w, "height": h})
            page = context.new_page()
            for slug, path in PAGES:
                page.goto(f"{BASE}{path}", wait_until="networkidle", timeout=60000)
                page.wait_for_timeout(400)
                page.evaluate(
                    """async () => {
                      const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
                      document.documentElement.classList.add('is-loaded');
                      const h = document.documentElement.scrollHeight;
                      for (let y = 0; y <= h; y += Math.max(400, window.innerHeight * 0.85)) {
                        window.scrollTo(0, y);
                        await sleep(80);
                      }
                      window.scrollTo(0, 0);
                      document.querySelectorAll('.sig-reveal').forEach((el) => el.classList.add('is-in'));
                      await sleep(350);
                    }"""
                )
                dest = OUT / f"{prefix}-{slug}-{vname}.png"
                page.screenshot(path=str(dest), full_page=True)
                print(dest)
            context.close()
        browser.close()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "after")
