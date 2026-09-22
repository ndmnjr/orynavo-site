from __future__ import annotations

import hashlib
import io
import json
import math
import re
import shutil
import struct
import xml.etree.ElementTree as ET
from pathlib import Path

import cairosvg
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]
IDENTITY = ROOT / "brand" / "identity"
SOURCE = ROOT / "brand" / "new-logo" / "Orynavo-logo.svg"
DESIGN = ROOT / "DESIGN.md"

CLAY = "#c96442"
INK = "#141413"
PAPER = "#f5f4ed"
IVORY = "#faf9f5"
MUTED = "#5e5d59"
SOFT = "#e8e6dc"
LINE = "#d8d5ca"
CLAY_DARK = "#a94d30"
WHITE = "#ffffff"

for folder in ("logos", "symbol", "favicon", "email", "social", "review"):
    (IDENTITY / folder).mkdir(parents=True, exist_ok=True)

source_text = SOURCE.read_text(encoding="utf-8")
n = ET.fromstring(source_text)
ns = {"svg": "http://www.w3.org/2000/svg"}
symbol_path = n.find("svg:g[@id='symbol']/svg:path", ns).attrib["d"]
wordmark_path = n.find("svg:g[@id='wordmark']/svg:path", ns).attrib["d"]


def horizontal_svg(wordmark_fill: str, symbol_fill: str = CLAY) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1307" height="321" viewBox="0 0 1307 321" role="img" aria-labelledby="title desc">
  <title id="title">Orynavo</title>
  <desc id="desc">Orynavo logo with an open O and square module beside the Orynavo wordmark.</desc>
  <g id="symbol" fill="{symbol_fill}" fill-rule="evenodd"><path d="{symbol_path}"/></g>
  <g id="wordmark" fill="{wordmark_fill}" fill-rule="evenodd"><path d="{wordmark_path}"/></g>
</svg>
'''


def symbol_svg(fill: str = CLAY, title: str = "Orynavo symbol") -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="321" height="321" viewBox="0 0 321 321" role="img" aria-labelledby="title desc">
  <title id="title">{title}</title>
  <desc id="desc">Terracotta open O with a square module, the Orynavo symbol.</desc>
  <path fill="{fill}" fill-rule="evenodd" d="{symbol_path}"/>
</svg>
'''


def render_svg(svg: str, width: int, height: int) -> Image.Image:
    png = cairosvg.svg2png(bytestring=svg.encode("utf-8"), output_width=width, output_height=height)
    return Image.open(io.BytesIO(png)).convert("RGBA")


def save_png(im: Image.Image, path: Path) -> None:
    im.save(path, format="PNG", optimize=True)


def fit_rgba(im: Image.Image, box: tuple[int, int], max_width: int, max_height: int) -> Image.Image:
    ratio = min(max_width / im.width, max_height / im.height)
    size = (max(1, round(im.width * ratio)), max(1, round(im.height * ratio)))
    resized = im.resize(size, Image.Resampling.LANCZOS)
    layer = Image.new("RGBA", box, (0, 0, 0, 0))
    layer.alpha_composite(resized, ((box[0] - size[0]) // 2, (box[1] - size[1]) // 2))
    return layer


def rgb(hex_color: str, alpha: int | None = None):
    value = hex_color.lstrip("#")
    out = tuple(int(value[i:i+2], 16) for i in (0, 2, 4))
    return out if alpha is None else out + (alpha,)


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size=size)


ARIAL = "C:/Windows/Fonts/arial.ttf"
ARIAL_BOLD = "C:/Windows/Fonts/arialbd.ttf"
GEORGIA = "C:/Windows/Fonts/georgia.ttf"

# Exact-geometry logo masters and transparent raster exports.
primary_svg = source_text
logo_variants = {
    "orynavo-horizontal-primary": primary_svg,
    "orynavo-horizontal-dark": horizontal_svg(PAPER),
    "orynavo-horizontal-black": horizontal_svg(INK, INK),
    "orynavo-horizontal-white": horizontal_svg(WHITE, WHITE),
}
for name, svg in logo_variants.items():
    svg_path = IDENTITY / "logos" / f"{name}.svg"
    if name == "orynavo-horizontal-primary":
        svg_path.write_bytes(SOURCE.read_bytes())
    else:
        svg_path.write_text(svg, encoding="utf-8", newline="\n")
    save_png(render_svg(svg, 1307, 321), IDENTITY / "logos" / f"{name}.png")

sym_svg = symbol_svg()
(IDENTITY / "symbol" / "orynavo-symbol.svg").write_text(sym_svg, encoding="utf-8")
symbol_1024 = render_svg(sym_svg, 1024, 1024)
save_png(symbol_1024, IDENTITY / "symbol" / "orynavo-symbol-1024.png")
(IDENTITY / "favicon" / "favicon.svg").write_text(sym_svg, encoding="utf-8")

# Pixel-size favicon sources and a PNG-compressed multi-entry ICO.
favicon_pngs = {}
for size in (16, 32, 48, 64):
    icon = render_svg(sym_svg, size, size)
    path = IDENTITY / "favicon" / f"favicon-{size}.png"
    save_png(icon, path)
    favicon_pngs[size] = icon
favicon_pngs[64].save(
    IDENTITY / "favicon" / "favicon.ico",
    format="ICO",
    sizes=[(16, 16), (32, 32), (48, 48), (64, 64)],
)
# Pillow writes zero in the ICO colour-plane field even for 32-bit images.
# Normalize each entry to the spec's single colour plane for strict clients.
ico_path = IDENTITY / "favicon" / "favicon.ico"
ico_data = bytearray(ico_path.read_bytes())
ico_count = struct.unpack_from("<H", ico_data, 4)[0]
for index in range(ico_count):
    struct.pack_into("<H", ico_data, 6 + index * 16 + 4, 1)
ico_path.write_bytes(ico_data)

# Email signature: transparent, exact 320 x 80, with practical clear space.
email_logo = fit_rgba(render_svg(primary_svg, 1307, 321), (320, 80), 304, 76)
save_png(email_logo, IDENTITY / "email" / "orynavo-email-signature-320x80.png")

# Apple touch icon uses an opaque warm-paper field for predictable iOS rendering.
apple = Image.new("RGBA", (180, 180), rgb(PAPER, 255))
apple_mark = render_svg(sym_svg, 132, 132)
apple.alpha_composite(apple_mark, (24, 24))
save_png(apple, IDENTITY / "social" / "apple-touch-icon-180.png")

# Open Graph: restrained editorial lockup with approved positioning phrase.
og = Image.new("RGB", (1200, 630), rgb(PAPER))
og_draw = ImageDraw.Draw(og)
og_logo = render_svg(primary_svg, 1307, 321)
og_logo = fit_rgba(og_logo, (600, 150), 600, 150)
og.paste(og_logo, (80, 158), og_logo)
og_draw.text((96, 362), "Applied AI and operational systems", font=font(GEORGIA, 42), fill=rgb(INK))
og_draw.line((96, 438, 540, 438), fill=rgb(INK), width=2)
og_draw.rectangle((1090, 0, 1200, 110), fill=rgb(CLAY))
save_png(og, IDENTITY / "social" / "open-graph-1200x630.png")

# YouTube avatar: symbol only; no wordmark at small circular crops.
avatar = Image.new("RGB", (800, 800), rgb(PAPER))
avatar_mark = render_svg(sym_svg, 560, 560)
avatar.paste(avatar_mark, (120, 120), avatar_mark)
save_png(avatar, IDENTITY / "social" / "youtube-avatar-800x800.png")

# YouTube banner. All important content stays in the 1546 x 423 central safe area.
banner = Image.new("RGB", (2560, 1440), rgb(INK))
bd = ImageDraw.Draw(banner)
bd.rectangle((0, 0, 2560, 20), fill=rgb(CLAY))
bd.rectangle((0, 1420, 2560, 1440), fill=rgb(CLAY))
banner_logo = render_svg(horizontal_svg(PAPER), 1307, 321)
banner_logo = fit_rgba(banner_logo, (940, 231), 940, 231)
# Safe area: x 507..2053, y 509..932. Lockup bounds: x 810..1750, y 564..795.
banner.paste(banner_logo, (810, 564), banner_logo)
bd.text((810, 825), "Applied AI and operations", font=font(ARIAL, 46), fill=rgb(SOFT))
save_png(banner, IDENTITY / "social" / "youtube-banner-2560x1440.png")


def checker(size: tuple[int, int], cell: int = 16) -> Image.Image:
    im = Image.new("RGB", size, (246, 245, 239))
    d = ImageDraw.Draw(im)
    for y in range(0, size[1], cell):
        for x in range(0, size[0], cell):
            if (x // cell + y // cell) % 2:
                d.rectangle((x, y, x + cell - 1, y + cell - 1), fill=(225, 223, 214))
    return im


def tile(canvas: Image.Image, xy: tuple[int, int], wh: tuple[int, int], title: str, art: Image.Image, bg: str | None = None):
    x, y = xy
    w, h = wh
    d = ImageDraw.Draw(canvas)
    d.rounded_rectangle((x, y, x+w, y+h), radius=18, fill=rgb(IVORY), outline=rgb(LINE), width=2)
    d.text((x+24, y+20), title, font=font(ARIAL_BOLD, 22), fill=rgb(INK))
    preview_box = (w-48, h-78)
    surface = Image.new("RGB", preview_box, rgb(bg) if bg else (255, 255, 255)) if bg else checker(preview_box)
    fitted = fit_rgba(art.convert("RGBA"), preview_box, preview_box[0]-40, preview_box[1]-32)
    surface.paste(fitted, (0, 0), fitted)
    canvas.paste(surface, (x+24, y+58))


sheet = Image.new("RGB", (1800, 1880), rgb(PAPER))
sd = ImageDraw.Draw(sheet)
sd.text((60, 44), "Orynavo identity asset system", font=font(GEORGIA, 52), fill=rgb(INK))
sd.text((62, 112), "Master geometry preserved · September 2026", font=font(ARIAL, 23), fill=rgb(MUTED))
tile(sheet, (60, 170), (810, 300), "Primary horizontal · transparent", render_svg(primary_svg, 1307, 321))
tile(sheet, (930, 170), (810, 300), "Dark-background variant", render_svg(horizontal_svg(PAPER), 1307, 321), INK)
tile(sheet, (60, 510), (520, 420), "Square symbol", symbol_1024)
tile(sheet, (640, 510), (520, 420), "Monochrome black", render_svg(horizontal_svg(INK, INK), 1307, 321))
tile(sheet, (1220, 510), (520, 420), "Monochrome white", render_svg(horizontal_svg(WHITE, WHITE), 1307, 321), INK)
tile(sheet, (60, 970), (810, 420), "Open Graph · 1200 × 630", og.convert("RGBA"))
tile(sheet, (930, 970), (810, 420), "YouTube banner · safe-area lockup", banner.convert("RGBA"))
tile(sheet, (60, 1430), (390, 300), "Favicon · 64px source", favicon_pngs[64])
tile(sheet, (490, 1430), (390, 300), "Apple touch · 180px", apple)
tile(sheet, (920, 1430), (390, 300), "YouTube avatar · 800px", avatar)
tile(sheet, (1350, 1430), (390, 300), "Email · 320 × 80", email_logo)
sd.text((60, 1818), "Palette", font=font(ARIAL_BOLD, 20), fill=rgb(INK))
for i, (label, color) in enumerate((("terracotta", CLAY), ("charcoal", INK), ("warm paper", PAPER), ("soft", SOFT))):
    x = 170 + i*320
    sd.rectangle((x, 1812, x+44, 1848), fill=rgb(color), outline=rgb(LINE))
    sd.text((x+58, 1816), f"{label}  {color}", font=font(ARIAL, 18), fill=rgb(INK))
save_png(sheet, IDENTITY / "review" / "orynavo-identity-contact-sheet.png")

# Publish the browser and sharing aliases used by the static site. Keeping
# these copies in the generator prevents the public root assets from drifting
# away from the reviewed identity files.
published_assets = {
    IDENTITY / "favicon" / "favicon.ico": ROOT / "favicon.ico",
    IDENTITY / "favicon" / "favicon.svg": ROOT / "favicon.svg",
    IDENTITY / "social" / "apple-touch-icon-180.png": ROOT / "apple-touch-icon.png",
    IDENTITY / "social" / "open-graph-1200x630.png": ROOT / "og-image.png",
    IDENTITY / "email" / "orynavo-email-signature-320x80.png": ROOT / "email-signature-logo.png",
}
for source, destination in published_assets.items():
    shutil.copyfile(source, destination)

# Deterministic validation.
def rel_luminance(hex_color: str) -> float:
    values = [int(hex_color[i:i+2], 16) / 255 for i in (1, 3, 5)]
    values = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in values]
    return 0.2126 * values[0] + 0.7152 * values[1] + 0.0722 * values[2]


def contrast(a: str, b: str) -> float:
    l1, l2 = sorted((rel_luminance(a), rel_luminance(b)), reverse=True)
    return (l1 + 0.05) / (l2 + 0.05)


def parse_ico(path: Path):
    data = path.read_bytes()
    reserved, kind, count = struct.unpack_from("<HHH", data, 0)
    entries = []
    for i in range(count):
        off = 6 + i * 16
        width, height, palette, _, planes, bpp, size, offset = struct.unpack_from("<BBBBHHII", data, off)
        payload = data[offset:offset+size]
        entries.append({
            "width": width or 256,
            "height": height or 256,
            "planes": planes,
            "bits_per_pixel": bpp,
            "png_compressed": payload.startswith(b"\x89PNG\r\n\x1a\n"),
        })
    return {"reserved": reserved, "type": kind, "count": count, "entries": entries}


checks = []
def add(name: str, passed: bool, details):
    checks.append({"name": name, "passed": bool(passed), "details": details})

for path in sorted(IDENTITY.rglob("*.svg")):
    try:
        root = ET.parse(path).getroot()
        add(f"svg-xml:{path.relative_to(ROOT).as_posix()}", root.tag.endswith("svg"), root.attrib)
    except Exception as exc:
        add(f"svg-xml:{path.relative_to(ROOT).as_posix()}", False, str(exc))

for path in sorted(IDENTITY.rglob("*.svg")):
    root = ET.parse(path).getroot()
    paths = [node.attrib.get("d") for node in root.iter() if node.tag.endswith("path")]
    expected_paths = [symbol_path] if path.name in {"favicon.svg", "orynavo-symbol.svg"} else [symbol_path, wordmark_path]
    add(
        f"locked-geometry:{path.relative_to(ROOT).as_posix()}",
        paths == expected_paths,
        {"path_count": len(paths), "matches_source": paths == expected_paths},
    )
add(
    "primary-svg-byte-identical-to-source",
    (IDENTITY / "logos" / "orynavo-horizontal-primary.svg").read_bytes() == SOURCE.read_bytes(),
    {"source": SOURCE.relative_to(ROOT).as_posix()},
)

expected = {
    "logos/orynavo-horizontal-primary.png": (1307, 321),
    "logos/orynavo-horizontal-dark.png": (1307, 321),
    "logos/orynavo-horizontal-black.png": (1307, 321),
    "logos/orynavo-horizontal-white.png": (1307, 321),
    "symbol/orynavo-symbol-1024.png": (1024, 1024),
    "email/orynavo-email-signature-320x80.png": (320, 80),
    "social/apple-touch-icon-180.png": (180, 180),
    "social/open-graph-1200x630.png": (1200, 630),
    "social/youtube-avatar-800x800.png": (800, 800),
    "social/youtube-banner-2560x1440.png": (2560, 1440),
    "review/orynavo-identity-contact-sheet.png": (1800, 1880),
}
for rel, dims in expected.items():
    with Image.open(IDENTITY / rel) as im:
        add(f"dimensions:{rel}", im.size == dims, {"actual": im.size, "expected": dims, "mode": im.mode})

for rel in (
    "logos/orynavo-horizontal-primary.png",
    "logos/orynavo-horizontal-dark.png",
    "logos/orynavo-horizontal-black.png",
    "logos/orynavo-horizontal-white.png",
    "symbol/orynavo-symbol-1024.png",
    "email/orynavo-email-signature-320x80.png",
):
    with Image.open(IDENTITY / rel) as im:
        alpha = im.getchannel("A") if "A" in im.getbands() else None
        extrema = alpha.getextrema() if alpha else (255, 255)
        add(f"transparency:{rel}", alpha is not None and extrema[0] == 0 and extrema[1] == 255, {"alpha_extrema": extrema})

ico = parse_ico(IDENTITY / "favicon" / "favicon.ico")
ico_sizes = [(e["width"], e["height"]) for e in ico["entries"]]
add("favicon-container", ico["reserved"] == 0 and ico["type"] == 1 and ico["count"] == 4 and all(e["planes"] == 1 for e in ico["entries"]), ico)
add("favicon-sizes", ico_sizes == [(16, 16), (32, 32), (48, 48), (64, 64)], ico_sizes)
add("favicon-png-entries", all(e["png_compressed"] for e in ico["entries"]), ico["entries"])

ratios = {
    "charcoal-on-paper": contrast(INK, PAPER),
    "muted-on-paper": contrast(MUTED, PAPER),
    "charcoal-on-terracotta": contrast(INK, CLAY),
    "paper-on-charcoal": contrast(PAPER, INK),
    "soft-on-charcoal": contrast(SOFT, INK),
}
add("contrast-aa", all(v >= 4.5 for v in ratios.values()), {k: round(v, 2) for k, v in ratios.items()})
add("youtube-safe-area", 810 >= 507 and 1750 <= 2053 and 564 >= 509 and 890 <= 932, {"safe_area": [507, 509, 2053, 932], "content_bounds": [810, 564, 1750, 890]})
for source, destination in published_assets.items():
    add(
        f"published-alias:{destination.name}",
        source.read_bytes() == destination.read_bytes(),
        {"source": source.relative_to(ROOT).as_posix(), "destination": destination.name},
    )

report = {
    "source_master": SOURCE.relative_to(ROOT).as_posix(),
    "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "passed": all(c["passed"] for c in checks),
    "checks": checks,
}
report_path = IDENTITY / "validation-report.json"
report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

hash_targets = sorted(
    [p for p in IDENTITY.rglob("*") if p.is_file() and p.name != "manifest-sha256.txt"]
    + [DESIGN, SOURCE]
    + list(published_assets.values()),
    key=lambda p: p.as_posix().lower(),
)
manifest = []
for path in hash_targets:
    manifest.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(ROOT).as_posix()}")
(IDENTITY / "manifest-sha256.txt").write_bytes(("\n".join(manifest) + "\n").encode("utf-8"))

print(json.dumps({"identity_dir": str(IDENTITY), "assets": len(hash_targets), "validation_passed": report["passed"], "checks": len(checks)}, indent=2))
if not report["passed"]:
    raise SystemExit(1)
