#!/usr/bin/env python3
"""Ajoute ou met à jour un post dans posts.json (déduplication par URL, tri automatique)."""
from __future__ import annotations

import argparse
import hashlib
import mimetypes
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from site_posts import dedupe_by_url, load_posts, normalize_post_entry, save_posts, sort_posts  # noqa: E402

IMG_DIR = ROOT / "img"


def download_image(url: str) -> str:
    req = Request(url, headers={"User-Agent": "sebastienmot-site-add-post/1.0"})
    with urlopen(req, timeout=60) as resp:
        data = resp.read()
        ctype = resp.headers.get("Content-Type", "")
    ext = mimetypes.guess_extension(ctype.split(";")[0].strip()) or Path(urlparse(url).path).suffix
    if ext in (".jpe", ".jpeg"):
        ext = ".jpg"
    if not ext:
        ext = ".png"
    name = hashlib.sha256(data).hexdigest()[:16] + ext
    path = IMG_DIR / name
    path.write_bytes(data)
    return f"img/{name}"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Ajouter un post à posts.json")
    p.add_argument("--source", required=True, choices=["x", "linkedin"])
    p.add_argument("--url", required=True, help="URL canonique du post (clé de déduplication)")
    p.add_argument("--date", required=True, help="Date ISO (AAAA-MM-JJ ou avec heure)")
    p.add_argument("--date-label", dest="date_label", help="Libellé affiché (sinon --date)")
    p.add_argument("--text", required=True, help="Texte intégral (1re ligne = titre)")
    p.add_argument("--text-file", type=Path, help="Lire le texte depuis un fichier")
    p.add_argument("--image", help="Chemin img/ existant")
    p.add_argument("--image-url", help="Télécharger une image vers img/")
    p.add_argument("--pinned", action="store_true")
    p.add_argument("--featured", action="store_true")
    p.add_argument("--replace", action="store_true", help="Remplacer l'entrée existante avec la même URL")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    text = args.text_file.read_text(encoding="utf-8").strip() if args.text_file else args.text.strip()
    if not text:
        raise SystemExit("Le texte du post est vide.")

    image = args.image
    if args.image_url:
        print(f"Téléchargement image : {args.image_url}")
        image = download_image(args.image_url)

    entry = normalize_post_entry(
        {
            "source": args.source,
            "date": args.date,
            "dateLabel": args.date_label or args.date[:10],
            "url": args.url,
            "image": image,
            "pinned": args.pinned,
            "featured": args.featured,
            "text": text,
            "cover": None,
        }
    )

    data = load_posts()
    posts = data.get("posts", [])
    existing_idx = next((i for i, p in enumerate(posts) if p.get("url", "").strip() == entry["url"]), None)

    if existing_idx is not None:
        if not args.replace:
            print(f"Post déjà présent (URL) : {entry['url']}", file=sys.stderr)
            sys.exit(1)
        posts[existing_idx] = entry
        print(f"Mise à jour du post #{existing_idx + 1}")
    else:
        posts.append(entry)
        print("Nouveau post ajouté")

    if entry["featured"]:
        for p in posts:
            if p.get("url", "").strip() != entry["url"] and p.get("featured"):
                p["featured"] = False

    posts = dedupe_by_url(posts)
    posts = sort_posts(posts)
    data["posts"] = posts
    save_posts(data)
    print(f"posts.json : {len(posts)} posts · tri OK")


if __name__ == "__main__":
    main()
