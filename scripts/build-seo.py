#!/usr/bin/env python3
"""Apply SEO tags to static pages and generate robots.txt + sitemap.xml."""

from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from seo import absolute_url, load_config, render_seo_head  # noqa: E402

SEO_MARKER_START = "<!-- seo:start -->"
SEO_MARKER_END = "<!-- seo:end -->"


def inject_seo(html_path: Path, seo_block: str) -> None:
    text = html_path.read_text(encoding="utf-8")
    pattern = re.compile(
        re.escape(SEO_MARKER_START) + r".*?" + re.escape(SEO_MARKER_END),
        re.DOTALL,
    )
    replacement = f"{SEO_MARKER_START}\n{seo_block}\n    {SEO_MARKER_END}"
    if not pattern.search(text):
        print(f"Skipping {html_path.name}: SEO markers not found")
        return
    html_path.write_text(pattern.sub(replacement, text, count=1), encoding="utf-8")
    print(f"Updated {html_path.relative_to(ROOT)}")


def write_robots(config: dict) -> None:
    sitemap_url = absolute_url(config, "/sitemap.xml")
    content = "\n".join(
        [
            "User-agent: *",
            "Allow: /",
            "",
            f"Sitemap: {sitemap_url}",
            "",
        ]
    )
    (ROOT / "robots.txt").write_text(content, encoding="utf-8")
    print("Wrote robots.txt")


def collect_urls(config: dict) -> list[tuple[str, str | None]]:
    urls: list[tuple[str, str | None]] = []
    for page in config["pages"].values():
        urls.append((absolute_url(config, page["path"]), None))

    posts_dir = ROOT / "posts"
    for md_path in sorted(posts_dir.glob("*.md")):
        slug = md_path.stem
        urls.append((absolute_url(config, f"/posts/{slug}.html"), None))

    return urls


def write_sitemap(config: dict) -> None:
    today = date.today().isoformat()
    urls = collect_urls(config)
    entries = []
    for url, lastmod in urls:
        mod = lastmod or today
        entries.extend(
            [
                "  <url>",
                f"    <loc>{url}</loc>",
                f"    <lastmod>{mod}</lastmod>",
                "  </url>",
            ]
        )

    content = "\n".join(
        [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
            *entries,
            "</urlset>",
            "",
        ]
    )
    (ROOT / "sitemap.xml").write_text(content, encoding="utf-8")
    print("Wrote sitemap.xml")


def main() -> None:
    config = load_config()

    page_map = {
        "index.html": ("index", "home"),
        "work.html": ("work", "work"),
        "writing.html": ("writing", "writing"),
    }

    for filename, (page_key, page_type) in page_map.items():
        page = config["pages"][page_key]
        seo_block = render_seo_head(
            config=config,
            title=page["title"],
            description=page["description"],
            path=page["path"],
            page_type=page_type,
            og_type=page.get("ogType", "website"),
            keywords=page.get("keywords"),
        )
        inject_seo(ROOT / filename, seo_block)

    write_robots(config)
    write_sitemap(config)


if __name__ == "__main__":
    main()
