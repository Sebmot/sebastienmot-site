"""Utilitaires partagés pour posts.json (build + scripts)."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parent
POSTS_PATH = ROOT / "posts.json"


def sort_posts(posts: list[dict]) -> list[dict]:
    """Épinglés en premier, puis plus récents en premier."""
    pinned = sorted([p for p in posts if p.get("pinned")], key=lambda p: p["date"], reverse=True)
    rest = sorted([p for p in posts if not p.get("pinned")], key=lambda p: p["date"], reverse=True)
    return pinned + rest


def load_posts() -> dict:
    return json.loads(POSTS_PATH.read_text(encoding="utf-8"))


def save_posts(data: dict) -> None:
    POSTS_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
    )


def dedupe_by_url(posts: list[dict]) -> list[dict]:
    seen: set[str] = set()
    out: list[dict] = []
    for p in posts:
        url = p.get("url", "").strip()
        if not url or url in seen:
            continue
        seen.add(url)
        out.append(p)
    return out


def normalize_post_entry(entry: dict) -> dict:
    return {
        "source": entry["source"],
        "date": entry["date"],
        "dateLabel": entry.get("dateLabel") or entry["date"][:10],
        "url": entry["url"].strip(),
        "image": entry.get("image"),
        "pinned": bool(entry.get("pinned", False)),
        "featured": bool(entry.get("featured", False)),
        "text": entry["text"].strip(),
        "cover": entry.get("cover"),
    }
