# Personal Site

Simple static personal site for Adegoke Adewoye.

## Pages

- `index.html` -> Home
- `work.html` -> Work, experience, and projects
- `writing.html` -> Writing page
- `posts/*.html` -> Individual posts (built from markdown)

## Edit content

Update these files directly:

- `index.html` for the home intro and social links
- `work.html` for work, experience, and projects
- `writing.html` for blog post titles and links
- `posts/*.md` for post content in markdown
- `images/portrait.png` is the portrait shown on the site. To re-process from a new photo, add a local-only `images/portrait-source.jpg` and run `python3 scripts/process-portrait.py`

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

3. Add a link in `writing.html` pointing to `./posts/your-slug.html`.

Posts are plain static HTML — no JavaScript required at runtime. The build step only runs when you change markdown.

## Run locally

Because this is a plain static site, you can open `index.html` directly in a
browser, or run a tiny local server:

```bash
python3 -m http.server 8080
```

Then open `http://localhost:8080`.

## Deploy

### Cloudflare Pages

1. Push this folder to GitHub.
2. In Cloudflare Pages, create a new project from that repo.
3. Use these settings:
   - Framework preset: `None`
   - Build command: leave empty
   - Build output directory: `/`

### GitHub Pages

1. Push this folder to a GitHub repo.
2. In GitHub, open `Settings -> Pages`.
3. Set the source to deploy from your default branch and the `/ (root)` folder.

No build step is required.
