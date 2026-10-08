#!/usr/bin/env python3
"""Génère le site statique sebastienmot.com dans dist/."""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import unicodedata
import xml.etree.ElementTree as ET
from datetime import date, datetime, timezone
from email.utils import format_datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from site_posts import sort_posts

ROOT = Path(__file__).parent
DIST = ROOT / "dist"
SITE_URL = os.environ.get("SITE_URL", "https://sebastienmot.com").rstrip("/")
SOURCE_LABEL = {"x": "X", "linkedin": "LinkedIn"}


def normalize_base_path(raw: str | None) -> str:
    if not raw or raw.strip() in ("/", ".", ""):
        return ""
    path = raw.strip().rstrip("/")
    if not path.startswith("/"):
        path = "/" + path
    return path


def site_href(base_path: str, path: str) -> str:
    if not path.startswith("/"):
        path = "/" + path
    return f"{base_path}{path}" if base_path else path


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


def fr_nbsp(text: str) -> str:
    """Espace insécable avant : ; ? ! » et après « (typographie française)."""
    if not text:
        return text
    text = re.sub(r"[ \u00a0]+([:;?!»])", "\u00a0\\1", str(text))
    return re.sub(r"«[ \u00a0]+", "«\u00a0", text)


def card_excerpt(body: str, limit: int = 260) -> str:
    """Extrait pour cartes : lignes conservées, lignes vides et liens seuls retirés."""
    lines = [ln.strip() for ln in body.split("\n")]
    lines = [ln for ln in lines if ln and not re.fullmatch(r"https?://\S+", ln)]
    text = "\n".join(lines)
    return text if len(text) <= limit else text[:limit].rstrip() + "…"


def assign_slugs(posts: list[dict]) -> list[dict]:
    seen: dict[str, int] = {}
    enriched = []
    for post in posts:
        title, body = split_post(post)
        base = slugify(title)
        n = seen.get(base, 0)
        seen[base] = n + 1
        slug = base if n == 0 else f"{base}-{n + 1}"
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
                "card_excerpt": card_excerpt(body),
                "figure": post.get("cover") if (
                    not post.get("image")
                    and post.get("cover")
                    and re.search(r"\d", str(post["cover"].get("big", "")))
                ) else None,
            }
        )
    return sort_posts(enriched)


def json_ld_script(data: dict) -> str:
    return (
        '<script type="application/ld+json">'
        + json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        + "</script>"
    )


REQUIRED_MAILTO = "mailto:seb@sebastienmot.com"
REQUIRED_EXTERNAL = (
    "https://x.com/sebastienmot",
    "https://www.linkedin.com/in/sebastienmot/",
    "https://nezo.finance",
)
ATTR_RE = re.compile(r"""(?:href|src)=["']([^"']+)["']""")


def resolve_internal_file(dist: Path, base_path: str, url: str) -> Path | None:
    if not url or url.startswith("#") or url.startswith(("mailto:", "tel:", "javascript:", "data:")):
        return None
    if url.startswith("http"):
        return None
    path = url.split("?", 1)[0].split("#", 1)[0]
    if base_path and path.startswith(base_path):
        path = path[len(base_path) :] or "/"
    rel = path.lstrip("/")
    if not rel:
        candidate = dist / "index.html"
        return candidate if candidate.is_file() else None
    direct = dist / rel
    if direct.is_file():
        return direct
    if direct.is_dir() and (direct / "index.html").is_file():
        return direct / "index.html"
    index_candidate = dist / rel / "index.html"
    if index_candidate.is_file():
        return index_candidate
    if rel.endswith("/"):
        index_candidate = dist / rel / "index.html"
        return index_candidate if index_candidate.is_file() else None
    return None


def _is_ci() -> bool:
    return os.environ.get("GITHUB_ACTIONS", "").lower() == "true"


def _http_link_check_enabled() -> bool:
    if _is_ci():
        return False
    return os.environ.get("LINK_CHECK_HTTP", "").lower() in ("1", "true", "yes")


def verify_external_http(urls: tuple[str, ...], timeout_s: float = 5.0) -> None:
    """Vérification HTTP optionnelle (jamais en CI). Timeouts stricts."""
    if not _http_link_check_enabled():
        return
    from urllib.error import HTTPError, URLError
    from urllib.request import Request, urlopen

    errors: list[str] = []
    for url in urls:
        try:
            req = Request(url, method="HEAD")
            with urlopen(req, timeout=timeout_s) as resp:
                if resp.status >= 400:
                    errors.append(f"{url} → HTTP {resp.status}")
        except HTTPError as exc:
            if exc.code in (405, 403, 999):
                try:
                    with urlopen(Request(url), timeout=timeout_s) as resp:
                        if resp.status >= 400:
                            errors.append(f"{url} → HTTP {resp.status}")
                except (HTTPError, URLError, TimeoutError) as err:
                    errors.append(f"{url} → {err}")
            elif exc.code >= 400:
                errors.append(f"{url} → HTTP {exc.code}")
        except (URLError, TimeoutError) as exc:
            errors.append(f"{url} → {exc}")

    if errors:
        raise SystemExit("Vérification HTTP des liens externes échouée :\n  " + "\n  ".join(errors))


def verify_links(dist: Path, base_path: str, posts: list[dict]) -> None:
    """Internes : échec bloquant. Externes (présence dans le HTML) : avertissement en CI."""
    errors: list[str] = []
    warnings: list[str] = []
    html_files = sorted(dist.rglob("*.html"))
    combined = "".join(p.read_text(encoding="utf-8") for p in html_files)

    if REQUIRED_MAILTO not in combined:
        msg = f"Contact mailto manquant ({REQUIRED_MAILTO})"
        (warnings if _is_ci() else errors).append(msg)

    for ext in REQUIRED_EXTERNAL:
        if ext not in combined:
            msg = f"Lien externe attendu absent du HTML : {ext}"
            (warnings if _is_ci() else errors).append(msg)

    for p in posts:
        if p["url"] not in combined:
            msg = f"URL source absente du site : {p['url']}"
            (warnings if _is_ci() else errors).append(msg)

    for html_path in html_files:
        text = html_path.read_text(encoding="utf-8")
        for match in ATTR_RE.finditer(text):
            url = match.group(1)
            target = resolve_internal_file(dist, base_path, url)
            if target is None:
                continue
            if not target.is_file():
                errors.append(f"{html_path.relative_to(dist)}: 404 interne → {url}")

    for asset in (
        "assets/css/site.css",
        "assets/css/post.css",
        "assets/js/home.js",
        "assets/js/posts-sort.js",
        "assets/js/posts-archive.js",
    ):
        if not (dist / asset).is_file():
            errors.append(f"Asset manquant : {asset}")

    for w in warnings:
        print(f"AVERTISSEMENT lien (non bloquant en CI) : {w}")

    if errors:
        raise SystemExit("Vérification des liens échouée :\n  " + "\n  ".join(errors))

    http_urls = tuple(REQUIRED_EXTERNAL) + tuple(p["url"] for p in posts)
    verify_external_http(http_urls)


def verify_html_output(dist: Path) -> None:
    """Échoue si du HTML de gabarit a été double-échappé dans les pages."""
    bad_markers = ("&lt;main", "&lt;section", "&lt;article")
    errors: list[str] = []
    for path in sorted(dist.rglob("*.html")):
        text = path.read_text(encoding="utf-8")
        for marker in bad_markers:
            if marker in text:
                errors.append(f"{path.relative_to(dist)}: {marker}")
        if '<main id="main"' not in text:
            errors.append(f"{path.relative_to(dist)}: balise <main> absente")
        if path.name == "index.html" and 'class="site-footer"' in text:
            if 'class="footer-legal"' not in text or "Mis à jour le" not in text:
                errors.append(f"{path.relative_to(dist)}: pied de page incomplet (date de mise à jour)")
    if errors:
        raise SystemExit("HTML échappé ou invalide dans dist/:\n  " + "\n  ".join(errors))


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
            "Entrepreneur belge depuis plus de 25 ans, en contact direct avec dirigeants "
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
            "Sébastien Mot aide à comprendre l'argent pour mieux décider. 25 ans aux côtés "
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Génère le site statique dans dist/")
    parser.add_argument(
        "--base-path",
        default=os.environ.get("BASE_PATH", ""),
        help="Préfixe des URLs internes (ex. /sebastienmot-site pour GitHub Pages projet)",
    )
    parser.add_argument(
        "--write-cname",
        action="store_true",
        default=os.environ.get("WRITE_CNAME", "").lower() in ("1", "true", "yes"),
        help="Écrire dist/CNAME (domaine personnalisé). Désactivé par défaut.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    # Domaine personnalisé : un fichier CNAME à la racine du dépôt active le mode
    # domaine (URLs à la racine + dist/CNAME), quel que soit BASE_PATH du workflow.
    cname_file = ROOT / "CNAME"
    custom_domain = cname_file.read_text(encoding="utf-8").strip() if cname_file.exists() else ""
    if custom_domain:
        args.base_path = ""
        args.write_cname = True
    base_path = normalize_base_path(args.base_path)
    href = lambda path: site_href(base_path, path)  # noqa: E731

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
    (DIST / ".nojekyll").write_text("", encoding="utf-8")

    env = Environment(
        loader=FileSystemLoader(ROOT / "templates"),
        autoescape=select_autoescape(["html", "xml"]),
    )
    env.globals["href"] = href
    env.filters["fr"] = fr_nbsp
    env.globals["base_path"] = base_path

    common = {
        "site_url": SITE_URL,
        "year": year,
        "build_date_label": build_date_label,
        "build_date_iso": build_dt.astimezone().strftime("%Y-%m-%d"),
        "base_path": base_path,
        "href": href,
    }

    nav_home = {
        "home_href": href("/"),
        "nav_posts": href("/") + "#posts",
        "nav_ideas": href("/") + "#idees",
        "nav_projects": href("/") + "#projets",
    }
    nav_inner = {
        "home_href": href("/"),
        "nav_posts": href("/posts/"),
        "nav_ideas": href("/") + "#idees",
        "nav_projects": href("/") + "#projets",
    }

    posts_payload = {
        "posts": [
            {
                k: p[k]
                for k in (
                    "source",
                    "date",
                    "dateLabel",
                    "url",
                    "image",
                    "pinned",
                    "featured",
                    "text",
                    "cover",
                    "slug",
                )
                if k in p
            }
            for p in posts
        ]
    }
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
            f'<script src="{href("/assets/js/posts-sort.js")}" defer></script>',
            f'<script src="{href("/assets/js/home.js")}" defer></script>',
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
        body_scripts=[
            f'<script id="posts-data" type="application/json">{posts_json}</script>',
            f'<script src="{href("/assets/js/posts-sort.js")}" defer></script>',
            f'<script src="{href("/assets/js/posts-archive.js")}" defer></script>',
        ],
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

    if args.write_cname:
        (DIST / "CNAME").write_text(f"{custom_domain or 'sebastienmot.com'}\n", encoding="utf-8")

    verify_html_output(DIST)
    verify_links(DIST, base_path, posts)

    legacy = (ROOT / "template.html").read_text(encoding="utf-8").replace("/*POSTS_JSON*/", posts_json)
    (ROOT / "maquette.html").write_text(legacy, encoding="utf-8")

    base_label = base_path or "/"
    print(f"dist/ : {len(posts)} posts · base_path={base_label} · CNAME={'oui' if args.write_cname else 'non'}")


if __name__ == "__main__":
    main()
