#!/usr/bin/env python3
"""Build static post HTML from markdown files in posts/*.md.

Requires: pip install markdown

Each markdown file should start with optional YAML front matter:

---
title: Post title
meta: Topics line
description: Meta description for SEO
date: 2026-06-01
image: /images/post-cover.jpg
---
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import markdown
except ImportError:
    print("Install markdown first: pip install markdown")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
POSTS_DIR = ROOT / "posts"
POSTS_OUT = PUBLIC / "posts"
sys.path.insert(0, str(ROOT / "scripts"))

from seo import load_config, render_seo_head  # noqa: E402

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <!-- seo:start -->
{seo}
    <!-- seo:end -->
    <link rel="stylesheet" href="../styles.css?v=25" />
  </head>
  <body>
    <main class="page">
      <header class="masthead">
        <p class="name">Adegoke Adewoye</p>
        <nav class="site-nav" aria-label="Primary">
          <a href="../index.html">Home</a>
          <a href="../work.html">Work</a>
          <a href="../writing.html" aria-current="page">Writing</a>
        </nav>
      </header>

      <nav class="post-nav" aria-label="Post navigation">
        <a class="post-back" href="../writing.html">
          <svg class="post-back-icon" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M15 18l-6-6 6-6" />
          </svg>
          <span class="post-back-label">Back to posts</span>
        </a>
      </nav>

      <article class="post">
        <header class="post-header">
          <p class="post-meta">{meta}</p>
          <h1 class="post-title">{title}</h1>
        </header>
        <div class="post-content">
{content}
        </div>
      </article>
    </main>
  </body>
</html>
"""


def parse_front_matter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text

    match = re.match(r"---\n(.*?)\n---\n?", text, re.DOTALL)
    if not match:
        return {}, text

    meta: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip()

    body = text[match.end() :]
    return meta, body.lstrip("\n")


def strip_leading_h1(text: str) -> str:
    return re.sub(r"^#\s+.+\n+", "", text, count=1)


def indent_html(html: str, spaces: int = 10) -> str:
    prefix = " " * spaces
    return "\n".join(prefix + line if line else line for line in html.splitlines())


def build_post(md_path: Path, config: dict) -> None:
    raw = md_path.read_text(encoding="utf-8")
    front_matter, body = parse_front_matter(raw)
    body = strip_leading_h1(body)

    slug = md_path.stem
    title = front_matter.get("title", slug.replace("-", " ").title())
    meta = front_matter.get("meta", "")
    description = front_matter.get("description", f"Writing by Adegoke Adewoye — {title}.")
    date_published = front_matter.get("date")
    image = front_matter.get("image")
    page_title = f"{title} — Adegoke Adewoye"

    seo = render_seo_head(
        config=config,
        title=page_title,
        description=description,
        path=f"/posts/{slug}.html",
        page_type="post",
        og_type="article",
        keywords=[
            k for k in [title, meta, "Adegoke Adewoye", "backend engineering", "healthtech"] if k
        ],
        image=image,
        date_published=date_published,
        article_section=meta or None,
    )

    content_html = indent_html(markdown.markdown(body, extensions=["smarty", "sane_lists"]))

    html_path = POSTS_OUT / f"{slug}.html"
    POSTS_OUT.mkdir(parents=True, exist_ok=True)
    html_path.write_text(
        TEMPLATE.format(
            seo=seo,
            title=title,
            meta=meta,
            content=content_html,
        ),
        encoding="utf-8",
    )
    print(f"Built {html_path.relative_to(ROOT)}")


def main() -> None:
    config = load_config()
    md_files = sorted(POSTS_DIR.glob("*.md"))
    if not md_files:
        print("No markdown posts found in posts/")
    else:
        for md_path in md_files:
            build_post(md_path, config)

    import subprocess

    portrait_source = PUBLIC / "images" / "portrait-source.jpg"
    portrait_script = ROOT / "scripts" / "process-portrait.py"
    if portrait_source.exists() and portrait_script.exists():
        subprocess.run([sys.executable, str(portrait_script)], check=True)

    subprocess.run([sys.executable, str(ROOT / "scripts" / "build-seo.py")], check=True)


if __name__ == "__main__":
    main()
