"""Deterministic checks for the Orynavo static site."""
from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).parent.resolve()
REQUIRED = {"index.html", "privacy.html", "404.html", "README.md", ".gitignore", "CNAME", "og-image.png"}
HTML_FILES = [ROOT / name for name in ("index.html", "privacy.html", "404.html")]


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
        self.favicons = 0
        self.h1s = 0
        self.mains = 0
        self.navs = 0
        self.images_missing_alt: list[str] = []

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
            self.favicons += 1
        if tag == "h1":
            self.h1s += 1
        if tag == "main":
            self.mains += 1
        if tag == "nav":
            self.navs += 1
        if tag == "img" and "alt" not in attrs:
            self.images_missing_alt.append(attrs.get("src", "(unknown)"))


def check(condition: bool, message: str, failures: list[str]) -> None:
    print(("PASS" if condition else "FAIL") + ": " + message)
    if not condition:
        failures.append(message)


def main() -> int:
    failures: list[str] = []
    existing = {p.name for p in ROOT.iterdir() if p.is_file()}
    check(REQUIRED <= existing, "all required files exist", failures)

    parsed: dict[Path, AuditParser] = {}
    contents: dict[Path, str] = {}
    for path in HTML_FILES:
        text = path.read_text(encoding="utf-8")
        contents[path] = text
        parser = AuditParser()
        parser.feed(text)
        parsed[path] = parser
        check(text.lstrip().lower().startswith("<!doctype html>"), f"{path.name}: HTML5 doctype", failures)
        check(parser.titles == 1, f"{path.name}: exactly one title", failures)
        check(parser.descriptions == 1, f"{path.name}: meta description", failures)
        check(parser.og_titles == 1 and parser.og_descriptions == 1, f"{path.name}: Open Graph title and description", failures)
        check(parser.favicons >= 1, f"{path.name}: favicon", failures)
        check(parser.h1s == 1, f"{path.name}: exactly one h1", failures)
        check(parser.mains == 1, f"{path.name}: main landmark", failures)
        check(parser.navs >= 1, f"{path.name}: navigation landmark", failures)
        check(not parser.images_missing_alt, f"{path.name}: every img has alt text", failures)
        check("@media(prefers-reduced-motion:reduce)" in text.replace(" ", ""), f"{path.name}: reduced-motion rule", failures)

    for source, parser in parsed.items():
        for href in parser.links:
            parts = urlsplit(href)
            if href.startswith("mailto:"):
                check(href == "mailto:hello@orynavo.com", f"{source.name}: published contact link is approved ({href})", failures)
                continue
            if href.startswith("tel:"):
                check(False, f"{source.name}: no unpublished telephone link ({href})", failures)
                continue
            if parts.scheme:
                check(parts.scheme == "https", f"{source.name}: external link uses HTTPS ({href})", failures)
                continue
            local_name = unquote(parts.path) or source.name
            target = (source.parent / local_name).resolve()
            check(target.is_file(), f"{source.name}: local link target exists ({href})", failures)
            if target in parsed and parts.fragment:
                check(parts.fragment in parsed[target].ids, f"{source.name}: fragment target exists ({href})", failures)

    index = contents[ROOT / "index.html"].lower()
    required_phrases = [
        "small digital products around", "real, repeated problems", "observe pain",
        "test willingness to pay", "build narrowly", "automate operations",
        "early research", "green-but-useless", "n8n", "no guarantee"
    ]
    for phrase in required_phrases:
        check(phrase in index, f"index.html: required message present ({phrase})", failures)

    privacy = contents[ROOT / "privacy.html"].lower()
    for phrase in ("no analytics", "cookies", "email contact", "it is not sold"):
        check(phrase in privacy, f"privacy.html: required disclosure present ({phrase})", failures)

    check((ROOT / "CNAME").read_text(encoding="utf-8").strip() == "orynavo.com", "CNAME: canonical domain is orynavo.com", failures)
    check("https://orynavo.com/" in index, "index.html: canonical Orynavo domain is present", failures)
    check("https://orynavo.com/privacy.html" in privacy, "privacy.html: canonical Orynavo domain is present", failures)
    check("mailto:hello@orynavo.com" in index, "index.html: approved contact mailbox is published", failures)
    check("mailto:hello@orynavo.com" in privacy, "privacy.html: approved contact mailbox is disclosed", failures)

    print(f"\\nSUMMARY: {len(failures)} failure(s), {sum(1 for _ in [])} warning(s)")
    if failures:
        print("Failures:")
        for failure in failures:
            print("- " + failure)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
