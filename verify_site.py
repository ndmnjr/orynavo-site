"""Deterministic checks for the Orynavo static site."""
from __future__ import annotations

import re
import struct
import sys
import zlib
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).parent.resolve()
REQUIRED = {
    "index.html", "privacy.html", "404.html", "README.md", ".gitignore",
    "CNAME", "og-image.png", "favicon.ico", "favicon.svg",
    "apple-touch-icon.png", "email-signature-logo.png", "DESIGN.md",
    "brand/new-logo/Orynavo-logo.svg",
    "brand/identity/tools/generate_identity.py",
    "brand/identity/validation-report.json",
    "brand/identity/manifest-sha256.txt",
    "photonbid/index.html",
    "photonbid/assets/photonbid-logo.svg",
    "photonbid/assets/photonbid-explainer.mp4",
    "photonbid/assets/photonbid-explainer-poster.png",
    "photonbid/assets/photonbid-explainer.en.vtt",
}
PUBLIC_HTML = ("index.html", "privacy.html", "404.html", "photonbid/index.html")
HTML_FILES = [ROOT / name for name in PUBLIC_HTML]
FAVICON_SIZES = {(16, 16), (32, 32), (48, 48), (64, 64)}
SIGNATURE_SIZE = (320, 80)


class AuditParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tags: list[tuple[str, dict[str, str]]] = []
        self.ids: set[str] = set()
        self.links: list[str] = []
        self.titles = 0
        self.descriptions = 0
        self.og_titles = 0
        self.og_descriptions = 0
        self.favicons: list[dict[str, str]] = []
        self.h1s = 0
        self.mains = 0
        self.navs = 0
        self.images_missing_alt: list[str] = []
        self.reader_text: list[str] = []
        self._hidden_depth = 0

    def handle_starttag(self, tag: str, attrs_raw: list[tuple[str, str | None]]) -> None:
        attrs = {k: (v or "") for k, v in attrs_raw}
        self.tags.append((tag, attrs))
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])
        if tag == "title":
            self.titles += 1
        if tag == "meta" and attrs.get("name", "").lower() == "description" and attrs.get("content"):
            self.descriptions += 1
        if tag == "meta" and attrs.get("property", "").lower() == "og:title" and attrs.get("content"):
            self.og_titles += 1
        if tag == "meta" and attrs.get("property", "").lower() == "og:description" and attrs.get("content"):
            self.og_descriptions += 1
        if tag == "link" and "icon" in attrs.get("rel", "").lower() and attrs.get("href"):
            self.favicons.append(attrs)
        if tag == "h1":
            self.h1s += 1
        if tag == "main":
            self.mains += 1
        if tag == "nav":
            self.navs += 1
        if tag == "img" and "alt" not in attrs:
            self.images_missing_alt.append(attrs.get("src", "(unknown)"))
        if tag in {"style", "script", "template"}:
            self._hidden_depth += 1
        if tag == "meta" and (
            attrs.get("name", "").lower() == "description"
            or attrs.get("property", "").lower() in {"og:title", "og:description"}
        ):
            self.reader_text.append(attrs.get("content", ""))

    def handle_endtag(self, tag: str) -> None:
        if tag in {"style", "script", "template"}:
            self._hidden_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._hidden_depth and data.strip():
            self.reader_text.append(data)


def check(condition: bool, message: str, failures: list[str]) -> None:
    print(("PASS" if condition else "FAIL") + ": " + message)
    if not condition:
        failures.append(message)


def png_info(data: bytes) -> tuple[int, int, int]:
    """Validate a PNG's structure and compressed image payload."""
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("missing PNG signature")
    offset = 8
    width = height = color_type = None
    idat = bytearray()
    saw_iend = False
    while offset < len(data):
        if offset + 12 > len(data):
            raise ValueError("truncated PNG chunk")
        length = struct.unpack_from(">I", data, offset)[0]
        chunk_type = data[offset + 4:offset + 8]
        end = offset + 12 + length
        if end > len(data):
            raise ValueError("PNG chunk exceeds file size")
        payload = data[offset + 8:offset + 8 + length]
        expected_crc = struct.unpack_from(">I", data, offset + 8 + length)[0]
        if zlib.crc32(chunk_type + payload) & 0xFFFFFFFF != expected_crc:
            raise ValueError("PNG chunk CRC mismatch")
        if chunk_type == b"IHDR":
            if length != 13 or width is not None:
                raise ValueError("invalid PNG IHDR")
            width, height, bit_depth, color_type, compression, filtering, interlace = struct.unpack(">IIBBBBB", payload)
            if bit_depth != 8 or color_type not in (2, 6) or compression or filtering or interlace:
                raise ValueError("unsupported PNG encoding")
        elif chunk_type == b"IDAT":
            idat.extend(payload)
        elif chunk_type == b"IEND":
            if length:
                raise ValueError("invalid PNG IEND")
            saw_iend = True
            offset = end
            break
        offset = end
    if width is None or not idat or not saw_iend or offset != len(data):
        raise ValueError("incomplete PNG")
    channels = 4 if color_type == 6 else 3
    expected_bytes = height * (1 + width * channels)
    if len(zlib.decompress(bytes(idat))) != expected_bytes:
        raise ValueError("invalid PNG image payload length")
    return width, height, color_type


def ico_sizes(data: bytes) -> set[tuple[int, int]]:
    """Validate an ICO container and each embedded PNG image."""
    if len(data) < 6:
        raise ValueError("truncated ICO header")
    reserved, image_type, count = struct.unpack_from("<HHH", data)
    if reserved != 0 or image_type != 1 or count == 0:
        raise ValueError("invalid ICO header")
    table_end = 6 + count * 16
    if table_end > len(data):
        raise ValueError("truncated ICO directory")
    sizes: set[tuple[int, int]] = set()
    for index in range(count):
        width_byte, height_byte, _colors, entry_reserved, planes, bit_count, byte_count, offset = struct.unpack_from(
            "<BBBBHHII", data, 6 + index * 16
        )
        width, height = width_byte or 256, height_byte or 256
        if entry_reserved != 0 or planes != 1 or bit_count != 32:
            raise ValueError("invalid ICO directory entry")
        if offset < table_end or byte_count == 0 or offset + byte_count > len(data):
            raise ValueError("ICO image exceeds file size")
        embedded_width, embedded_height, color_type = png_info(data[offset:offset + byte_count])
        if (embedded_width, embedded_height) != (width, height) or color_type != 6:
            raise ValueError("ICO entry metadata mismatch")
        sizes.add((width, height))
    return sizes


def main() -> int:
    failures: list[str] = []
    check(all((ROOT / name).is_file() for name in REQUIRED), "all required files exist", failures)

    parsed: dict[Path, AuditParser] = {}
    contents: dict[Path, str] = {}
    for path in HTML_FILES:
        page_name = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8")
        contents[path] = text
        parser = AuditParser()
        parser.feed(text)
        parsed[path] = parser
        check(text.lstrip().lower().startswith("<!doctype html>"), f"{page_name}: HTML5 doctype", failures)
        check(parser.titles == 1, f"{page_name}: exactly one title", failures)
        check(parser.descriptions == 1, f"{page_name}: meta description", failures)
        check(parser.og_titles == 1 and parser.og_descriptions == 1, f"{page_name}: Open Graph title and description", failures)
        expected_icons = [
            {"rel": "icon", "type": "image/x-icon", "href": "/favicon.ico"},
            {"rel": "icon", "type": "image/svg+xml", "href": "/favicon.svg"},
            {"rel": "apple-touch-icon", "href": "/apple-touch-icon.png"},
        ]
        check(parser.favicons == expected_icons, f"{page_name}: ICO, SVG, and Apple touch icons", failures)
        check(parser.h1s == 1, f"{page_name}: exactly one h1", failures)
        check(parser.mains == 1, f"{page_name}: main landmark", failures)
        if page_name == "photonbid/index.html":
            check(parser.navs == 0, f"{page_name}: no empty navigation landmark", failures)
        else:
            check(parser.navs >= 1, f"{page_name}: navigation landmark", failures)
        check(not parser.images_missing_alt, f"{page_name}: every img has alt text", failures)
        check("@media(prefers-reduced-motion:reduce)" in text.replace(" ", ""), f"{page_name}: reduced-motion rule", failures)
        reader_copy = " ".join(parser.reader_text)
        for forbidden, label in (("\u2013", "en dash"), ("\u2014", "em dash"), ("--", "double hyphen")):
            check(forbidden not in reader_copy, f"{page_name}: reader-facing copy has no {label}", failures)

    for source, parser in parsed.items():
        for href in parser.links:
            parts = urlsplit(href)
            if href.startswith("mailto:"):
                approved_mailboxes = {"hello@orynavo.com", "research@orynavo.com"}
                check(parts.path in approved_mailboxes, f"{source.relative_to(ROOT).as_posix()}: published contact link is approved ({href})", failures)
                continue
            if href.startswith("tel:"):
                check(False, f"{source.name}: no unpublished telephone link ({href})", failures)
                continue
            if parts.scheme:
                check(parts.scheme == "https", f"{source.name}: external link uses HTTPS ({href})", failures)
                continue
            local_name = unquote(parts.path)
            if local_name.startswith("/"):
                target = ROOT / local_name.lstrip("/")
                if target == ROOT:
                    target = ROOT / "index.html"
                target = target.resolve()
            else:
                local_name = local_name or source.name
                target = (source.parent / local_name).resolve()
            if target.is_dir():
                target = target / "index.html"
            check(target.is_file(), f"{source.name}: local link target exists ({href})", failures)
            if target in parsed and parts.fragment:
                check(parts.fragment in parsed[target].ids, f"{source.name}: fragment target exists ({href})", failures)

    index = contents[ROOT / "index.html"].lower()
    required_phrases = [
        "applied ai and operations consultancy", "operational complexity",
        "decisions your team can trust", "applied ai and agents",
        "operational and decision systems", "telecom and asset lifecycle insight",
        "validation and prototyping", "proof before scale",
        "research project, not a released product", "guaranteed outcomes"
    ]
    for phrase in required_phrases:
        check(phrase in index, f"index.html: required message present ({phrase})", failures)

    privacy = contents[ROOT / "privacy.html"].lower()
    for phrase in ("no analytics", "cookies", "when you send an email", "it is not sold"):
        check(phrase in privacy, f"privacy.html: required disclosure present ({phrase})", failures)

    photonbid = contents[ROOT / "photonbid/index.html"].lower()
    for phrase in (
        "official european tenders", "actual catalogue", "quoted evidence",
        "possible product match", "disqualifying requirements",
        "official notice always takes precedence",
    ):
        check(phrase in photonbid, f"photonbid/index.html: required message present ({phrase})", failures)
    check("<video" in photonbid and " controls" in photonbid, "photonbid/index.html: accessible video controls present", failures)
    check(not re.search(r"<video[^>]*\sautoplay(?:\s|=|>)", photonbid), "photonbid/index.html: video does not autoplay", failures)
    check('preload="metadata"' in photonbid and "playsinline" in photonbid, "photonbid/index.html: restrained video loading and inline playback", failures)
    check('kind="captions"' in photonbid and 'srclang="en"' in photonbid, "photonbid/index.html: English captions present", failures)
    check("youtube" not in photonbid and "vimeo" not in photonbid, "photonbid/index.html: no third party video host", failures)
    check((ROOT / "photonbid/assets/photonbid-explainer.mp4").stat().st_size > 1_000_000, "PhotonBid explainer has a nontrivial media payload", failures)

    check((ROOT / "CNAME").read_text(encoding="utf-8").strip() == "orynavo.com", "CNAME: canonical domain is orynavo.com", failures)
    check("https://orynavo.com/" in index, "index.html: canonical Orynavo domain is present", failures)
    check("https://orynavo.com/privacy.html" in privacy, "privacy.html: canonical Orynavo domain is present", failures)
    check("mailto:hello@orynavo.com" in index, "index.html: approved contact mailbox is published", failures)
    check("mailto:hello@orynavo.com" in privacy, "privacy.html: approved contact mailbox is disclosed", failures)
    check("mailto:research@orynavo.com" in privacy, "privacy.html: research contact mailbox is disclosed", failures)

    try:
        actual_favicon_sizes = ico_sizes((ROOT / "favicon.ico").read_bytes())
        check(actual_favicon_sizes == FAVICON_SIZES, "favicon.ico: valid 32-bit ICO with 16/32/48/64px PNG images", failures)
    except (OSError, ValueError, struct.error, zlib.error) as error:
        check(False, f"favicon.ico: physically valid ({error})", failures)

    try:
        signature_width, signature_height, signature_color_type = png_info((ROOT / "email-signature-logo.png").read_bytes())
        check(
            (signature_width, signature_height) == SIGNATURE_SIZE and signature_color_type == 6,
            "email-signature-logo.png: valid 320x80 RGBA PNG",
            failures,
        )
    except (OSError, ValueError, struct.error, zlib.error) as error:
        check(False, f"email-signature-logo.png: physically valid ({error})", failures)

    public_aliases = {
        "favicon.ico": "brand/identity/favicon/favicon.ico",
        "favicon.svg": "brand/identity/favicon/favicon.svg",
        "apple-touch-icon.png": "brand/identity/social/apple-touch-icon-180.png",
        "og-image.png": "brand/identity/social/open-graph-1200x630.png",
        "email-signature-logo.png": "brand/identity/email/orynavo-email-signature-320x80.png",
    }
    for public_name, identity_name in public_aliases.items():
        check(
            (ROOT / public_name).read_bytes() == (ROOT / identity_name).read_bytes(),
            f"{public_name}: matches generated identity asset ({identity_name})",
            failures,
        )

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    check("https://orynavo.com/email-signature-logo.png" in readme, "README.md: hosted signature asset URL", failures)
    check('alt="Orynavo"' in readme and 'width="160" height="40"' in readme, "README.md: accessible signature image usage", failures)

    print(f"\\nSUMMARY: {len(failures)} failure(s), {sum(1 for _ in [])} warning(s)")
    if failures:
        print("Failures:")
        for failure in failures:
            print("- " + failure)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
