"""Shared SEO and social preview tag generation for the static site."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "site.config.json"


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def absolute_url(config: dict[str, Any], path: str) -> str:
    base = config["siteUrl"].rstrip("/")
    if path == "/":
        return f"{base}/"
    return f"{base}/{path.lstrip('/')}"


def absolute_image(config: dict[str, Any], image_path: str | None) -> str:
    path = image_path or config["defaultImage"]
    if path.startswith("http://") or path.startswith("https://"):
        return path
    return absolute_url(config, path)


def keywords_string(keywords: list[str]) -> str:
    return ", ".join(keywords)


def build_person_entity(config: dict[str, Any], *, person_id: str | None = None) -> dict[str, Any]:
    person = config["person"]
    site_url = absolute_url(config, "/")
    entity: dict[str, Any] = {
        "@type": "Person",
        "name": person["name"],
        "jobTitle": person["jobTitle"],
        "description": person["description"],
        "url": site_url,
        "image": absolute_image(config, None),
        "email": f"mailto:{person['email']}",
        "sameAs": person["sameAs"],
    }

    if person_id:
        entity["@id"] = person_id

    alternate_names = person.get("alternateName")
    if alternate_names:
        entity["alternateName"] = alternate_names

    location = person.get("location")
    if location:
        entity["address"] = {
            "@type": "PostalAddress",
            "addressLocality": location["locality"],
            "addressRegion": location.get("region", location["locality"]),
            "addressCountry": location["countryCode"],
        }
        entity["homeLocation"] = {
            "@type": "Place",
            "name": f"{location['locality']}, {location['country']}",
        }

    knows_about = person.get("knowsAbout")
    if knows_about:
        entity["knowsAbout"] = knows_about

    works_for = person.get("worksFor")
    if works_for:
        entity["worksFor"] = {
            "@type": "Organization",
            "name": works_for["name"],
            "url": works_for["url"],
        }

    member_of = person.get("memberOf")
    if member_of:
        entity["memberOf"] = [
            {
                "@type": "Organization",
                "name": org["name"],
                "url": org["url"],
            }
            for org in member_of
        ]

    return entity


def render_geo_meta(config: dict[str, Any]) -> list[str]:
    location = config["person"].get("location")
    if not location:
        return []

    region_code = location.get("regionCode")
    if not region_code and location.get("countryCode") and location.get("region"):
        region_code = f"{location['countryCode']}-{location['region'][:2].upper()}"
    elif region_code and location.get("countryCode"):
        region_code = f"{location['countryCode']}-{region_code}"

    lines = []
    if region_code:
        escaped_region = html.escape(region_code, quote=True)
        lines.append(f'    <meta name="geo.region" content="{escaped_region}" />')
    placename = f"{location['locality']}, {location['country']}"
    escaped_place = html.escape(placename, quote=True)
    lines.append(f'    <meta name="geo.placename" content="{escaped_place}" />')
    return lines


def render_json_ld(config: dict[str, Any], page_type: str, page: dict[str, Any]) -> str:
    person = config["person"]
    url = absolute_url(config, page["path"])
    image = absolute_image(config, page.get("image"))
    site_url = absolute_url(config, "/")
    person_id = f"{site_url}#person"

    if page_type == "post":
        schema = {
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "headline": page["title"],
            "description": page["description"],
            "url": url,
            "image": image,
            "author": {
                "@type": "Person",
                "name": person["name"],
                "url": site_url,
            },
            "publisher": {
                "@type": "Person",
                "name": person["name"],
                "url": site_url,
            },
            "mainEntityOfPage": url,
        }
        if page.get("datePublished"):
            schema["datePublished"] = page["datePublished"]
        if page.get("meta"):
            schema["keywords"] = page["meta"]
    elif page_type == "writing":
        schema = {
            "@context": "https://schema.org",
            "@type": "Blog",
            "name": f"Writing — {person['name']}",
            "description": page["description"],
            "url": url,
            "author": build_person_entity(config),
        }
    elif page_type == "work":
        schema = {
            "@context": "https://schema.org",
            "@type": "ProfilePage",
            "name": page["title"],
            "description": page["description"],
            "url": url,
            "mainEntity": build_person_entity(config, person_id=person_id),
        }
    else:
        schema = {
            "@context": "https://schema.org",
            "@graph": [
                {
                    "@type": "WebSite",
                    "@id": f"{site_url}#website",
                    "url": site_url,
                    "name": config["siteName"],
                    "description": person["description"],
                    "inLanguage": config["locale"].replace("_", "-"),
                    "publisher": {"@id": person_id},
                },
                build_person_entity(config, person_id=person_id),
            ],
        }

    payload = json.dumps(schema, ensure_ascii=False, indent=2)
    return f'    <script type="application/ld+json">\n{payload}\n    </script>'


def render_seo_head(
    *,
    config: dict[str, Any],
    title: str,
    description: str,
    path: str,
    page_type: str = "website",
    og_type: str = "website",
    keywords: list[str] | None = None,
    image: str | None = None,
    date_published: str | None = None,
    article_section: str | None = None,
) -> str:
    person = config["person"]
    canonical = absolute_url(config, path)
    image_url = absolute_image(config, image)
    keyword_list = keywords or person["keywords"]
    escaped_title = html.escape(title, quote=True)
    escaped_description = html.escape(description, quote=True)
    escaped_keywords = html.escape(keywords_string(keyword_list), quote=True)
    escaped_author = html.escape(person["name"], quote=True)
    escaped_site = html.escape(config["siteName"], quote=True)
    escaped_image = html.escape(image_url, quote=True)
    escaped_canonical = html.escape(canonical, quote=True)
    escaped_og_type = html.escape(og_type, quote=True)
    escaped_locale = html.escape(config["locale"], quote=True)
    escaped_twitter = html.escape(config["twitterHandle"], quote=True)

    lines = [
        f"    <title>{escaped_title}</title>",
        f'    <meta name="description" content="{escaped_description}" />',
        f'    <meta name="author" content="{escaped_author}" />',
        f'    <meta name="keywords" content="{escaped_keywords}" />',
        '    <meta name="robots" content="index, follow, max-image-preview:large" />',
        f'    <link rel="canonical" href="{escaped_canonical}" />',
    ]

    lines.extend(render_geo_meta(config))

    for profile_url in person["sameAs"]:
        lines.append(f'    <link rel="me" href="{html.escape(profile_url, quote=True)}" />')

    lines.extend(
        [
            f'    <meta property="og:type" content="{escaped_og_type}" />',
            f'    <meta property="og:site_name" content="{escaped_site}" />',
            f'    <meta property="og:locale" content="{escaped_locale}" />',
            f'    <meta property="og:title" content="{escaped_title}" />',
            f'    <meta property="og:description" content="{escaped_description}" />',
            f'    <meta property="og:url" content="{escaped_canonical}" />',
            f'    <meta property="og:image" content="{escaped_image}" />',
            f'    <meta property="og:image:alt" content="{escaped_author}" />',
            '    <meta name="twitter:card" content="summary_large_image" />',
            f'    <meta name="twitter:site" content="{escaped_twitter}" />',
            f'    <meta name="twitter:creator" content="{escaped_twitter}" />',
            f'    <meta name="twitter:title" content="{escaped_title}" />',
            f'    <meta name="twitter:description" content="{escaped_description}" />',
            f'    <meta name="twitter:image" content="{escaped_image}" />',
            f'    <meta name="twitter:image:alt" content="{escaped_author}" />',
        ]
    )

    if og_type == "profile":
        lines.append('    <meta property="profile:username" content="degoke" />')

    if page_type == "post":
        lines.append(f'    <meta property="article:author" content="{escaped_author}" />')
        if date_published:
            escaped_date = html.escape(date_published, quote=True)
            lines.append(f'    <meta property="article:published_time" content="{escaped_date}" />')
        if article_section:
            escaped_section = html.escape(article_section, quote=True)
            lines.append(f'    <meta property="article:section" content="{escaped_section}" />')

    page_meta = {
        "path": path,
        "title": title,
        "description": description,
        "image": image,
        "datePublished": date_published,
        "meta": article_section,
    }
    lines.append(render_json_ld(config, page_type, page_meta))

    return "\n".join(lines)
