#!/usr/bin/env python3
"""Replace the portrait studio backdrop with the site background color."""

from __future__ import annotations

import sys
from collections import deque
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
# Local-only raw photo (gitignored). Writes the committed site asset.
SRC = ROOT / "images" / "portrait-source.jpg"
DST = ROOT / "images" / "portrait.png"

# Must match --bg in styles.css
SITE_BG = (240, 238, 230)  # #f0eee6
TOP_CROP_RATIO = 0.11  # trim empty studio space above the head
STEP_THRESH = 16
EDGE_LUMINANCE = 130
ORPHAN_MAX_AREA = 12000
FRINGE_LUMINANCE = 118
FRINGE_CHROMA = 34


def color_distance(a: tuple[int, int, int], b: tuple[int, int, int]) -> int:
    return sum(abs(a[i] - b[i]) for i in range(3))


def luminance(rgb: tuple[int, int, int]) -> float:
    r, g, b = rgb
    return 0.299 * r + 0.587 * g + 0.114 * b


def chroma(rgb: tuple[int, int, int]) -> int:
    return max(rgb) - min(rgb)


def is_backdrop_like(rgb: tuple[int, int, int], *, relaxed: bool = False) -> bool:
    lum = luminance(rgb)
    sat = chroma(rgb)
    if relaxed:
        return lum >= 160 and sat <= 22
    return lum >= EDGE_LUMINANCE and sat <= 28


def is_fringe_pixel(rgb: tuple[int, int, int]) -> bool:
    lum = luminance(rgb)
    sat = chroma(rgb)
    return lum >= FRINGE_LUMINANCE and sat <= FRINGE_CHROMA


def flood_background_mask(img: Image.Image) -> set[tuple[int, int]]:
    px = img.load()
    w, h = img.size
    background: set[tuple[int, int]] = set()
    queue: deque[tuple[int, int]] = deque()

    for x in range(w):
        for y in (0, h - 1):
            if is_backdrop_like(px[x, y]):
                queue.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            if is_backdrop_like(px[x, y]):
                queue.append((x, y))

    while queue:
        x, y = queue.popleft()
        if (x, y) in background:
            continue

        current = px[x, y]
        if not is_backdrop_like(current, relaxed=True) and (x, y) not in background:
            if luminance(current) < EDGE_LUMINANCE - 25 or chroma(current) > 32:
                continue

        background.add((x, y))

        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if nx < 0 or nx >= w or ny < 0 or ny >= h:
                continue
            if (nx, ny) in background:
                continue
            if color_distance(current, px[nx, ny]) <= STEP_THRESH:
                queue.append((nx, ny))

    return background


def fill_orphan_backdrops(
    img: Image.Image, background: set[tuple[int, int]]
) -> set[tuple[int, int]]:
    px = img.load()
    w, h = img.size
    visited = set(background)
    added: set[tuple[int, int]] = set()

    for x in range(w):
        for y in range(h):
            if (x, y) in visited:
                continue
            if not is_backdrop_like(px[x, y], relaxed=True):
                continue

            queue: deque[tuple[int, int]] = deque([(x, y)])
            component: set[tuple[int, int]] = set()

            while queue:
                cx, cy = queue.popleft()
                if (cx, cy) in visited:
                    continue
                color = px[cx, cy]
                if not is_backdrop_like(color, relaxed=True):
                    continue

                visited.add((cx, cy))
                component.add((cx, cy))

                for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
                    if 0 <= nx < w and 0 <= ny < h:
                        queue.append((nx, ny))

            if component and len(component) <= ORPHAN_MAX_AREA:
                added.update(component)

    return background | added


def remove_backdrop_fringe(
    img: Image.Image, background: set[tuple[int, int]]
) -> set[tuple[int, int]]:
    px = img.load()
    w, h = img.size
    expanded = set(background)

    for x, y in background:
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if nx < 0 or nx >= w or ny < 0 or ny >= h:
                continue
            if (nx, ny) in expanded:
                continue
            if is_fringe_pixel(px[nx, ny]):
                expanded.add((nx, ny))

    return expanded


def replace_background(img: Image.Image, background: set[tuple[int, int]]) -> Image.Image:
    result = img.copy()
    px = result.load()
    for x, y in background:
        px[x, y] = SITE_BG
    return result


def crop_top(img: Image.Image) -> Image.Image:
    w, h = img.size
    crop = int(h * TOP_CROP_RATIO)
    if crop <= 0:
        return img
    return img.crop((0, crop, w, h))


def process_portrait(src: Path = SRC, dst: Path = DST) -> None:
    img = Image.open(src).convert("RGB")
    background = flood_background_mask(img)
    background = fill_orphan_backdrops(img, background)
    background = remove_backdrop_fringe(img, background)
    result = replace_background(img, background)
    result = crop_top(result)
    result.save(dst, optimize=True)
    print(f"Wrote {dst} ({len(background)} backdrop pixels, cropped {TOP_CROP_RATIO:.0%} from top)")


if __name__ == "__main__":
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else SRC
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else DST
    process_portrait(src, dst)
