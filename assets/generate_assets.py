"""Generate crisp monochrome Lucide-style icons and the MiniSort application icon.

All icons follow the strict black-and-white design language of MiniSort.
Drawn at 4x resolution and downsampled with LANCZOS for sharp anti-aliased strokes.
"""

from __future__ import annotations

import math
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw

ASSETS_DIR = Path(__file__).resolve().parent
ICONS_DIR = ASSETS_DIR / "icons"
IMAGES_DIR = ASSETS_DIR / "images"

SCALE = 4
BASE_SIZE = 24
CANVAS = BASE_SIZE * SCALE
STROKE = int(2.0 * SCALE)


def _new_canvas() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def _p(x: float, y: float) -> tuple[float, float]:
    return (x * SCALE, y * SCALE)


def _line(d: ImageDraw.ImageDraw, pts: list[tuple[float, float]], color: tuple[int, int, int, int], width: int = STROKE) -> None:
    scaled = [_p(x, y) for x, y in pts]
    d.line(scaled, fill=color, width=width, joint="curve")
    # Rounded endcaps
    r = width / 2.0
    for sx, sy in (scaled[0], scaled[-1]):
        d.ellipse((sx - r, sy - r, sx + r, sy + r), fill=color)


def _rrect(d: ImageDraw.ImageDraw, x0: float, y0: float, x1: float, y1: float, radius: float, color: tuple[int, int, int, int], width: int = STROKE) -> None:
    d.rounded_rectangle(
        (_p(x0, y0), _p(x1, y1)),
        radius=radius * SCALE,
        outline=color,
        width=width,
    )


def _draw_dashboard(d: ImageDraw.ImageDraw, c: tuple[int, int, int, int]) -> None:
    _rrect(d, 3, 3, 10, 11, 1.5, c)
    _rrect(d, 14, 3, 21, 8, 1.5, c)
    _rrect(d, 14, 12, 21, 21, 1.5, c)
    _rrect(d, 3, 15, 10, 21, 1.5, c)


def _draw_sort(d: ImageDraw.ImageDraw, c: tuple[int, int, int, int]) -> None:
    # Up-down arrows (ArrowUpDown)
    _line(d, [(7, 4), (7, 20)], c)
    _line(d, [(4, 7), (7, 4), (10, 7)], c)
    _line(d, [(17, 20), (17, 4)], c)
    _line(d, [(14, 17), (17, 20), (20, 17)], c)


def _draw_filter(d: ImageDraw.ImageDraw, c: tuple[int, int, int, int]) -> None:
    pts = [(3, 4), (21, 4), (14, 12.5), (14, 19), (10, 21), (10, 12.5), (3, 4)]
    _line(d, pts, c)


def _draw_clean(d: ImageDraw.ImageDraw, c: tuple[int, int, int, int]) -> None:
    # Sparkles / wand clean icon
    _line(d, [(12, 3), (14, 10), (21, 12), (14, 14), (12, 21), (10, 14), (3, 12), (10, 10), (12, 3)], c)
    _line(d, [(18.5, 4), (18.5, 7)], c, int(1.6 * SCALE))
    _line(d, [(17, 5.5), (20, 5.5)], c, int(1.6 * SCALE))


def _draw_stats(d: ImageDraw.ImageDraw, c: tuple[int, int, int, int]) -> None:
    _line(d, [(4, 20), (20, 20)], c)
    _rrect(d, 5, 12, 8.5, 20, 1, c)
    _rrect(d, 10.25, 5, 13.75, 20, 1, c)
    _rrect(d, 15.5, 9, 19, 20, 1, c)


def _draw_recent(d: ImageDraw.ImageDraw, c: tuple[int, int, int, int]) -> None:
    d.ellipse((_p(3, 3), _p(21, 21)), outline=c, width=STROKE)
    _line(d, [(12, 7), (12, 12), (16, 14)], c)


def _draw_settings(d: ImageDraw.ImageDraw, c: tuple[int, int, int, int]) -> None:
    # Minimalist sliders icon (clean Lucide SlidersHorizontal)
    _line(d, [(4, 6), (20, 6)], c)
    _line(d, [(4, 12), (20, 12)], c)
    _line(d, [(4, 18), (20, 18)], c)
    for cx, cy in ((9, 6), (16, 12), (10, 18)):
        d.ellipse((_p(cx - 2.3, cy - 2.3), _p(cx + 2.3, cy + 2.3)), fill=(255, 255, 255, 0), outline=c, width=STROKE)
        # Solid inner dot for crispness
        d.ellipse((_p(cx - 1.4, cy - 1.4), _p(cx + 1.4, cy + 1.4)), fill=c)


def _draw_about(d: ImageDraw.ImageDraw, c: tuple[int, int, int, int]) -> None:
    d.ellipse((_p(3, 3), _p(21, 21)), outline=c, width=STROKE)
    _line(d, [(12, 11), (12, 16.5)], c)
    d.ellipse((_p(11, 7.2), _p(13, 9.2)), fill=c)


def _draw_upload(d: ImageDraw.ImageDraw, c: tuple[int, int, int, int]) -> None:
    _line(d, [(12, 15), (12, 4)], c)
    _line(d, [(7.5, 8.5), (12, 4), (16.5, 8.5)], c)
    _line(d, [(4, 15), (4, 19), (20, 19), (20, 15)], c)


def _draw_export(d: ImageDraw.ImageDraw, c: tuple[int, int, int, int]) -> None:
    _line(d, [(12, 4), (12, 15)], c)
    _line(d, [(7.5, 10.5), (12, 15), (16.5, 10.5)], c)
    _line(d, [(4, 15), (4, 19), (20, 19), (20, 15)], c)


def _draw_table(d: ImageDraw.ImageDraw, c: tuple[int, int, int, int]) -> None:
    _rrect(d, 3, 4, 21, 20, 2, c)
    _line(d, [(3, 9.5), (21, 9.5)], c)
    _line(d, [(3, 14.5), (21, 14.5)], c)
    _line(d, [(9.5, 9.5), (9.5, 20)], c)


def _draw_compare(d: ImageDraw.ImageDraw, c: tuple[int, int, int, int]) -> None:
    _rrect(d, 3, 4, 10.5, 20, 1.5, c)
    _rrect(d, 13.5, 4, 21, 20, 1.5, c)
    _line(d, [(5.5, 9), (8, 9)], c, int(1.6 * SCALE))
    _line(d, [(5.5, 13), (8, 13)], c, int(1.6 * SCALE))
    _line(d, [(16, 9), (18.5, 9)], c, int(1.6 * SCALE))
    _line(d, [(16, 13), (18.5, 13)], c, int(1.6 * SCALE))


def _draw_undo(d: ImageDraw.ImageDraw, c: tuple[int, int, int, int]) -> None:
    _line(d, [(4, 9), (9, 4)], c)
    _line(d, [(4, 9), (9, 14)], c)
    _line(d, [(4, 9), (15, 9)], c)
    d.arc((_p(10, 9), _p(20, 19)), start=-90, end=90, fill=c, width=STROKE)
    _line(d, [(15, 19), (9, 19)], c)


def _draw_redo(d: ImageDraw.ImageDraw, c: tuple[int, int, int, int]) -> None:
    _line(d, [(20, 9), (15, 4)], c)
    _line(d, [(20, 9), (15, 14)], c)
    _line(d, [(20, 9), (9, 9)], c)
    d.arc((_p(4, 9), _p(14, 19)), start=90, end=270, fill=c, width=STROKE)
    _line(d, [(9, 19), (15, 19)], c)


def _draw_file(d: ImageDraw.ImageDraw, c: tuple[int, int, int, int]) -> None:
    _line(d, [(6, 3), (14, 3), (19, 8), (19, 21), (6, 21), (6, 3)], c)
    _line(d, [(14, 3), (14, 8), (19, 8)], c)
    _line(d, [(9, 13), (16, 13)], c, int(1.6 * SCALE))
    _line(d, [(9, 16.5), (14, 16.5)], c, int(1.6 * SCALE))


def _draw_folder(d: ImageDraw.ImageDraw, c: tuple[int, int, int, int]) -> None:
    _line(d, [(3, 6), (9.5, 6), (11.5, 8.5), (21, 8.5), (21, 19), (3, 19), (3, 6)], c)


def _draw_trash(d: ImageDraw.ImageDraw, c: tuple[int, int, int, int]) -> None:
    _line(d, [(4, 6), (20, 6)], c)
    _line(d, [(9, 6), (9, 4), (15, 4), (15, 6)], c)
    _line(d, [(6, 6), (7, 20), (17, 20), (18, 6)], c)
    _line(d, [(10, 10), (10, 16)], c, int(1.6 * SCALE))
    _line(d, [(14, 10), (14, 16)], c, int(1.6 * SCALE))


def _draw_plus(d: ImageDraw.ImageDraw, c: tuple[int, int, int, int]) -> None:
    _line(d, [(12, 5), (12, 19)], c)
    _line(d, [(5, 12), (19, 12)], c)


def _draw_check(d: ImageDraw.ImageDraw, c: tuple[int, int, int, int]) -> None:
    _line(d, [(4.5, 12.5), (9.5, 17.5), (19.5, 6.5)], c)


def _draw_warning(d: ImageDraw.ImageDraw, c: tuple[int, int, int, int]) -> None:
    _line(d, [(12, 3.5), (21, 19.5), (3, 19.5), (12, 3.5)], c)
    _line(d, [(12, 9.5), (12, 14)], c)
    d.ellipse((_p(11, 16), _p(13, 18)), fill=c)


ICON_DRAWERS = {
    "dashboard": _draw_dashboard,
    "sort": _draw_sort,
    "filter": _draw_filter,
    "clean": _draw_clean,
    "stats": _draw_stats,
    "recent": _draw_recent,
    "settings": _draw_settings,
    "about": _draw_about,
    "upload": _draw_upload,
    "export": _draw_export,
    "table": _draw_table,
    "compare": _draw_compare,
    "undo": _draw_undo,
    "redo": _draw_redo,
    "file": _draw_file,
    "folder": _draw_folder,
    "trash": _draw_trash,
    "plus": _draw_plus,
    "check": _draw_check,
    "warning": _draw_warning,
}


def generate_icons() -> None:
    ICONS_DIR.mkdir(parents=True, exist_ok=True)
    variants = {
        "dark": (17, 17, 17, 255),
        "light": (255, 255, 255, 255),
        "muted": (115, 115, 115, 255),
    }
    for name, drawer in ICON_DRAWERS.items():
        for variant, rgba in variants.items():
            img, draw = _new_canvas()
            drawer(draw, rgba)
            resized = img.resize((36, 36), Image.Resampling.LANCZOS)
            resized.save(ICONS_DIR / f"{name}_{variant}.png")


def generate_app_icon() -> None:
    """Create the MiniSort app icon (.png and multi-res .ico) from minisort_source.jpg if available."""
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    ico_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    source_logo = IMAGES_DIR / "minisort_source.jpg"
    if source_logo.exists():
        im = Image.open(source_logo).convert("RGBA")
        bg = Image.new("RGB", im.size, (255, 255, 255))
        diff = ImageChops.difference(im.convert("RGB"), bg)
        gray = diff.convert("L").point(lambda p: 255 if p > 12 else 0)
        bbox = gray.getbbox()
        cropped = im.crop(bbox) if bbox else im

        size = 512
        canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        mask = Image.new("L", (size, size), 0)
        mdraw = ImageDraw.Draw(mask)
        pad = 12
        mdraw.rounded_rectangle((pad, pad, size - pad, size - pad), radius=92, fill=255)

        tile = Image.new("RGBA", (size, size), (255, 255, 255, 255))
        inner_max = size - 72
        cw, ch = cropped.size
        scale = min(inner_max / cw, inner_max / ch)
        nw, nh = int(round(cw * scale)), int(round(ch * scale))
        resized = cropped.resize((nw, nh), Image.Resampling.LANCZOS)
        tile.paste(resized, ((size - nw) // 2, (size - nh) // 2), resized)

        canvas.paste(tile, (0, 0), mask)
        bdraw = ImageDraw.Draw(canvas)
        bdraw.rounded_rectangle((pad, pad, size - pad, size - pad), radius=92, outline=(220, 220, 220, 255), width=4)
        canvas.save(IMAGES_DIR / "minisort.png")
        canvas.save(IMAGES_DIR / "minisort.ico", format="ICO", sizes=ico_sizes)
        return

    size = 512
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # Rounded pure-black square background
    pad = 24
    d.rounded_rectangle(
        (pad, pad, size - pad, size - pad),
        radius=96,
        fill=(17, 17, 17, 255),
    )

    # Minimalist white spreadsheet grid + ascending sort bars motif
    white = (255, 255, 255, 255)
    soft_grey = (205, 205, 205, 255)

    # Left side: 3 neatly sorted horizontal rows (increasing lengths)
    bar_x = 108
    bar_h = 34
    d.rounded_rectangle((bar_x, 148, bar_x + 116, 148 + bar_h), radius=14, fill=soft_grey)
    d.rounded_rectangle((bar_x, 238, bar_x + 162, 238 + bar_h), radius=14, fill=white)
    d.rounded_rectangle((bar_x, 328, bar_x + 210, 328 + bar_h), radius=14, fill=white)

    # Right side: crisp vertical sort arrow
    ax = 376
    top_y = 148
    bot_y = 362
    lw = 26
    d.line([(ax, top_y), (ax, bot_y)], fill=white, width=lw)
    # Arrowhead pointing down (sorted descending/order indicator) & top cap
    d.line([(ax - 44, top_y + 44), (ax, top_y), (ax + 44, top_y + 44)], fill=white, width=lw, joint="curve")
    r = lw // 2
    for px, py in ((ax - 44, top_y + 44), (ax + 44, top_y + 44), (ax, bot_y), (ax, top_y)):
        d.ellipse((px - r, py - r, px + r, py + r), fill=white)

    # Save master PNG
    png_256 = img.resize((256, 256), Image.Resampling.LANCZOS)
    png_256.save(IMAGES_DIR / "minisort.png")

    # Save multi-resolution ICO for Windows taskbar, explorer, PyInstaller, and Inno Setup
    ico_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(IMAGES_DIR / "minisort.ico", format="ICO", sizes=ico_sizes)


def main() -> None:
    generate_icons()
    generate_app_icon()
    print(f"Generated {len(ICON_DRAWERS) * 3} icons and MiniSort app icons.")


if __name__ == "__main__":
    main()
