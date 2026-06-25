# Personal Site

Simple static personal site for Adegoke Adewoye.

## Project layout

- `public/` — deployable site (HTML, CSS, images, built posts, robots.txt, sitemap.xml)
- `posts/*.md` — post source files (markdown)
- `scripts/` — build and SEO tooling
- `site.config.json` — site metadata and SEO config

## Pages

- `public/index.html` → Home
- `public/work.html` → Work, experience, and projects
- `public/writing.html` → Writing page
- `public/posts/*.html` → Individual posts (built from markdown)

## Edit content

Update these files directly:

- `public/index.html` for the home intro and social links
- `public/work.html` for work, experience, and projects
- `public/writing.html` for blog post titles and links
- `posts/*.md` for post content in markdown
- `public/images/portrait.png` is the portrait shown on the site. To re-process from a new photo, add a local-only `public/images/portrait-source.jpg` and run `python3 scripts/process-portrait.py`

### Adding or editing posts

1. Create or edit a markdown file in `posts/` with optional front matter:

```markdown
---
title: Post title
meta: Topics line
description: Short SEO description
---

# Post title

Your content here…
```

2. Build the HTML:

```bash
python3 -m pip install markdown
python3 scripts/build-posts.py
```

3. Add a link in `public/writing.html` pointing to `./posts/your-slug.html`.

Posts are plain static HTML — no JavaScript required at runtime. The build step only runs when you change markdown.

## Before you push

Run lint, format checks, and the build locally:

```bash
pip install -r requirements.txt
npm install
npm run check
```

To auto-fix formatting:

```bash
python3 -m ruff format scripts
npm run format
```

## Run locally

```bash
npm run serve
```

Then open `http://localhost:8080`.

## Deploy

### Cloudflare Pages

1. Push this folder to GitHub.
2. In Cloudflare Pages, create a new project from that repo.
3. Use these settings:
   - Framework preset: `None`
   - Build command: leave empty
   - Build output directory: `/public`
4. Add a build environment variable (Production and Preview):
   - Name: `SKIP_DEPENDENCY_INSTALL`
   - Value: `1`

Cloudflare auto-installs from `package.json` and `requirements.txt` when it finds them. This site is built locally with `npm run check` before push, so skip that step on deploy.

No build command is required on Cloudflare.

### GitHub Pages

GitHub Pages only publishes from `/` or `/docs` by default. Use Cloudflare Pages with `/public` as the output directory, or copy `public/` contents to a branch/folder GitHub can serve.
