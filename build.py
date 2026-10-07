#!/usr/bin/env python3
"""Génère le site statique sebastienmot.com dans dist/."""
from __future__ import annotations

import json
import re
import shutil
import unicodedata
import xml.etree.ElementTree as ET
from datetime import date, datetime, timezone
from email.utils import format_datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).parent
DIST = ROOT / "dist"
SITE_URL = "https://sebastienmot.com"
SOURCE_LABEL = {"x": "X", "linkedin": "LinkedIn"}


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")[:96] or "post"


def split_post(post: dict) -> tuple[str, str]:
    lines = post["text"].split("\n")
    title = lines[0].strip()
    body = "\n".join(lines[1:]).strip()
    return title, body


def assign_slugs(posts: list[dict]) -> list[dict]:
    seen: dict[str, int] = {}
    enriched = []
    for post in posts:
        title, body = split_post(post)
        base = slugify(title)
        n = seen.get(base, 0)
        seen[base] = n + 1
        slug = base if n == 0 else f"{base}-{n + 1}"
        date_iso = post["date"][:10]
        if "T" in post["date"]:
            date_iso = post["date"].replace("T", " ")[:16]
        enriched.append(
            {
                **post,
                "slug": slug,
                "title": title,
                "body": body,
                "date_iso": post["date"][:10],
                "source_label": SOURCE_LABEL[post["source"]],
                "paragraphs": [p.strip() for p in body.split("\n\n") if p.strip()] if body else [],
                "excerpt": re.sub(r"\s+", " ", body)[:180] + ("…" if len(body) > 180 else ""),
            }
        )
    enriched.sort(key=lambda p: p["date"], reverse=True)
    return enriched


def json_ld_script(data: dict) -> str:
    return (
        '<script type="application/ld+json">'
        + json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        + "</script>"
    )


def render_page(env: Environment, template_name: str, **ctx) -> str:
    return env.get_template("base.html").render(
        body=env.get_template(template_name).render(**ctx),
        head_extra=ctx.get("head_extra", []),
        body_scripts=ctx.get("body_scripts", []),
        **{k: v for k, v in ctx.items() if k not in ("head_extra", "body_scripts")},
    )


def write_rss(path: Path, posts: list[dict], build_dt: datetime) -> None:
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = "Sébastien Mot — Posts"
    ET.SubElement(channel, "link").text = SITE_URL + "/"
    ET.SubElement(channel, "description").text = (
        "Posts de Sébastien Mot — entrepreneur belge, finances et décisions."
    )
    ET.SubElement(channel, "language").text = "fr-BE"
    ET.SubElement(channel, "lastBuildDate").text = format_datetime(build_dt)
    for p in posts[:20]:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = p["title"]
        ET.SubElement(item, "link").text = f"{SITE_URL}/posts/{p['slug']}/"
        ET.SubElement(item, "guid", isPermaLink="true").text = f"{SITE_URL}/posts/{p['slug']}/"
        pub = datetime.strptime(p["date_iso"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        ET.SubElement(item, "pubDate").text = format_datetime(pub)
        desc = p["body"] or p["title"]
        ET.SubElement(item, "description").text = desc[:500]
    tree = ET.ElementTree(rss)
    ET.indent(tree, space="  ")
    path.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(rss, encoding="unicode"),
        encoding="utf-8",
    )


def write_sitemap(path: Path, posts: list[dict]) -> None:
    urls = [
        ("", "weekly", "1.0"),
        ("/posts/", "weekly", "0.9"),
    ]
    for p in posts:
        urls.append((f"/posts/{p['slug']}/", "monthly", "0.8"))
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    today = date.today().isoformat()
    for loc, freq, pri in urls:
        lines.append("  <url>")
        lines.append(f"    <loc>{SITE_URL}{loc}</loc>")
        lines.append(f"    <lastmod>{today}</lastmod>")
        lines.append(f"    <changefreq>{freq}</changefreq>")
        lines.append(f"    <priority>{pri}</priority>")
        lines.append("  </url>")
    lines.append("</urlset>")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_llms(path: Path, posts: list[dict], full: bool) -> None:
    if full:
        chunks = [
            "# Sébastien Mot — contenu complet pour moteurs IA",
            "",
            f"Site : {SITE_URL}",
            "Contact : seb@sebastienmot.com",
            "",
            "## Qui est Sébastien Mot",
            "",
            "Entrepreneur belge depuis plus de vingt-cinq ans, en contact direct avec dirigeants "
            "et PME. Il partage sur l'argent, les décisions et l'entrepreneuriat, sans formation "
            "à vendre ni promesse de liberté financière. Projet en cours : NEZO.finance.",
            "",
            "## Posts",
            "",
        ]
        for p in posts:
            chunks.append(f"### {p['title']}")
            chunks.append(f"- URL : {SITE_URL}/posts/{p['slug']}/")
            chunks.append(f"- Source : {p['source_label']} · {p['dateLabel']}")
            chunks.append(f"- Original : {p['url']}")
            chunks.append("")
            chunks.append(p["text"])
            chunks.append("")
        path.write_text("\n".join(chunks), encoding="utf-8")
    else:
        lines = [
            "# Sébastien Mot",
            "",
            f"> {SITE_URL} — D'entrepreneur à entrepreneur.",
            "",
            "Sébastien Mot aide à comprendre l'argent pour mieux décider. Vingt-cinq ans aux côtés "
            "de dirigeants belges. Posts X et LinkedIn en français.",
            "",
            "## Liens",
            f"- Accueil : {SITE_URL}/",
            f"- Tous les posts : {SITE_URL}/posts/",
            f"- RSS : {SITE_URL}/feed.xml",
            f"- Contact : seb@sebastienmot.com",
            "",
            "## Posts récents",
        ]
        for p in posts[:8]:
            lines.append(f"- [{p['title']}]({SITE_URL}/posts/{p['slug']}/)")
        lines.append("")
        lines.append(f"Liste complète : {SITE_URL}/llms-full.txt")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    build_dt = datetime.now(timezone.utc)
    build_date_label = build_dt.astimezone().strftime("%d/%m/%Y")
    year = build_dt.year

    raw = json.loads((ROOT / "posts.json").read_text(encoding="utf-8"))
    posts = assign_slugs(raw["posts"])

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)

    shutil.copytree(ROOT / "img", DIST / "img")
    shutil.copytree(ROOT / "assets", DIST / "assets")

    env = Environment(
        loader=FileSystemLoader(ROOT / "templates"),
        autoescape=select_autoescape(["html", "xml"]),
    )

    latest = [
        {"slug": p["slug"], "title_short": (p["title"][:42] + "…") if len(p["title"]) > 45 else p["title"]}
        for p in posts[:3]
    ]

    common = {
        "site_url": SITE_URL,
        "year": year,
        "build_date_label": build_date_label,
        "latest_posts": latest,
    }

    nav_home = {
        "home_href": "/",
        "nav_posts": "/#posts",
        "nav_ideas": "/#idees",
        "nav_projects": "/#projets",
    }
    nav_inner = {
        "home_href": "/",
        "nav_posts": "/posts/",
        "nav_ideas": "/#idees",
        "nav_projects": "/#projets",
    }

    posts_payload = {"posts": [{k: p[k] for k in ("source", "date", "dateLabel", "url", "image", "pinned", "featured", "text", "cover", "slug") if k in p} for p in posts]}
    posts_json = json.dumps(posts_payload, ensure_ascii=False).replace("</", "<\\/")

    person_ld = {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": "Sébastien Mot",
        "url": SITE_URL,
        "email": "mailto:seb@sebastienmot.com",
        "sameAs": [
            "https://x.com/sebastienmot",
            "https://www.linkedin.com/in/sebastienmot/",
        ],
        "jobTitle": "Entrepreneur",
        "description": "Comprendre l'argent, c'est mieux décider. D'entrepreneur à entrepreneur.",
    }
    website_ld = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": "Sébastien Mot",
        "url": SITE_URL,
        "inLanguage": "fr-BE",
        "publisher": {"@type": "Person", "name": "Sébastien Mot"},
    }

    home_html = render_page(
        env,
        "home_body.html",
        post_count=len(posts),
        page_title="Sébastien Mot — D'entrepreneur à entrepreneur",
        meta_description="Comprendre l'argent, c'est mieux décider. D'entrepreneur à entrepreneur.",
        canonical=SITE_URL + "/",
        og_type="website",
        og_image=SITE_URL + "/img/seb.webp",
        head_extra=[
            json_ld_script(person_ld),
            json_ld_script(website_ld),
        ],
        body_scripts=[
            f'<script id="posts-data" type="application/json">{posts_json}</script>',
            '<script src="/assets/js/home.js" defer></script>',
        ],
        **common,
        **nav_home,
    )
    (DIST / "index.html").write_text(home_html, encoding="utf-8")

    posts_index_html = render_page(
        env,
        "posts_index.html",
        posts=posts,
        page_title="Tous les posts — Sébastien Mot",
        meta_description="Tous les posts X et LinkedIn de Sébastien Mot, classés par date.",
        canonical=SITE_URL + "/posts/",
        og_type="website",
        og_image=None,
        head_extra=[json_ld_script(website_ld)],
        body_scripts=[],
        **common,
        **nav_inner,
    )
    posts_dir = DIST / "posts"
    posts_dir.mkdir()
    (posts_dir / "index.html").write_text(posts_index_html, encoding="utf-8")

    for p in posts:
        schema_type = "SocialMediaPosting" if p["source"] == "x" else "BlogPosting"
        post_ld = {
            "@context": "https://schema.org",
            "@type": schema_type,
            "headline": p["title"],
            "datePublished": p["date_iso"],
            "author": {"@type": "Person", "name": "Sébastien Mot", "url": SITE_URL},
            "mainEntityOfPage": f"{SITE_URL}/posts/{p['slug']}/",
            "url": f"{SITE_URL}/posts/{p['slug']}/",
            "inLanguage": "fr-BE",
            "isBasedOn": p["url"],
        }
        if p.get("image"):
            post_ld["image"] = SITE_URL + "/" + p["image"].lstrip("/")
        desc = p["body"][:300] if p["body"] else p["title"]
        post_ld["description"] = desc

        og_img = None
        if p.get("image"):
            og_img = SITE_URL + "/" + p["image"].lstrip("/")

        html = render_page(
            env,
            "post.html",
            post=p,
            page_title=f"{p['title']} — Sébastien Mot",
            meta_description=desc[:160],
            canonical=f"{SITE_URL}/posts/{p['slug']}/",
            og_type="article",
            og_image=og_img,
            head_extra=[json_ld_script(post_ld), json_ld_script(person_ld)],
            body_scripts=[],
            **common,
            **nav_inner,
        )
        out = posts_dir / p["slug"]
        out.mkdir(parents=True, exist_ok=True)
        (out / "index.html").write_text(html, encoding="utf-8")

    (DIST / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n",
        encoding="utf-8",
    )
    write_sitemap(DIST / "sitemap.xml", posts)
    write_rss(DIST / "feed.xml", posts, build_dt)
    write_llms(DIST / "llms.txt", posts, full=False)
    write_llms(DIST / "llms-full.txt", posts, full=True)
    (DIST / "CNAME").write_text("sebastienmot.com\n", encoding="utf-8")

    # Legacy maquette for reference
    legacy = (ROOT / "template.html").read_text(encoding="utf-8").replace("/*POSTS_JSON*/", posts_json)
    (ROOT / "maquette.html").write_text(legacy, encoding="utf-8")

    print(f"dist/ : {len(posts)} posts · {build_date_label}")


if __name__ == "__main__":
    main()
