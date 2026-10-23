#!/usr/bin/env python3
"""QA captures PR#6 : home + posts, scroll puis pleine page."""
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parents[1] / "docs" / "screenshots" / "final"
BASE = "http://127.0.0.1:8765"


def capture(page, slug: str, path: str, vname: str) -> None:
    page.goto(f"{BASE}{path}", wait_until="networkidle", timeout=90000)
    page.wait_for_timeout(500)
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(400)
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(300)
    page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
    page.wait_for_timeout(400)
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(500)
    dest = OUT / f"{slug}-{vname}.png"
    page.screenshot(path=str(dest), full_page=True)
    print(dest)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for vname, w, h in [("1440", 1440, 900), ("390", 390, 844)]:
            ctx = browser.new_context(viewport={"width": w, "height": h})
            page = ctx.new_page()
            capture(page, "home", "/", vname)
            capture(page, "posts", "/posts/", vname)
            ctx.close()
        browser.close()


if __name__ == "__main__":
    main()
