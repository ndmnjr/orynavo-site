# Orynavo identity usage guide

This directory contains the approved Orynavo identity generated from `brand/new-logo/Orynavo-logo.svg`. The generator also publishes byte-identical favicon, Apple touch icon, Open Graph, and email-signature aliases at the site root.

## Core rule

The supplied symbol and wordmark paths are locked. Do not redraw, simplify, stretch, rotate, rearrange, or alter their proportions. Use the vector masters whenever the destination accepts SVG.

## Asset index

| Use | File |
|---|---|
| Primary horizontal logo, light surfaces | `logos/orynavo-horizontal-primary.svg` |
| Primary horizontal raster | `logos/orynavo-horizontal-primary.png` |
| Horizontal logo, dark surfaces | `logos/orynavo-horizontal-dark.svg` or `.png` |
| One-colour black logo | `logos/orynavo-horizontal-black.svg` or `.png` |
| One-colour white logo | `logos/orynavo-horizontal-white.svg` or `.png` |
| Square symbol | `symbol/orynavo-symbol.svg` |
| High-resolution square symbol | `symbol/orynavo-symbol-1024.png` |
| Browser favicon | `favicon/favicon.svg` and `favicon/favicon.ico` |
| Individual favicon sources | `favicon/favicon-16.png`, `-32.png`, `-48.png`, `-64.png` |
| Apple touch icon | `social/apple-touch-icon-180.png` |
| Email signature | `email/orynavo-email-signature-320x80.png` |
| Open Graph | `social/open-graph-1200x630.png` |
| YouTube avatar | `social/youtube-avatar-800x800.png` |
| YouTube banner | `social/youtube-banner-2560x1440.png` |
| Visual QA sheet | `review/orynavo-identity-contact-sheet.png` |
| Machine validation | `validation-report.json` |
| Integrity hashes | `manifest-sha256.txt` |

## Colour use

- Terracotta `#c96442`: fixed primary symbol colour and large graphic accent.
- Charcoal `#141413`: primary wordmark, body text, and dark field.
- Warm paper `#f5f4ed`: default light field.
- Dark terracotta `#a94d30`: small accent text on warm paper.
- Muted `#5e5d59`, soft `#e8e6dc`, line `#d8d5ca`, and ivory `#faf9f5`: restrained support colours.

Do not use terracotta for normal-size text on warm paper; use dark terracotta or charcoal for sufficient contrast. Do not add gradients.

## Clear space and minimum use

Keep at least one detached-square module of clear space around the horizontal logo. Use the symbol rather than the horizontal lockup below approximately 120px rendered width. For email, use the 320×80 PNG at a displayed size of 160×40px for crisp 2× rendering.

## Backgrounds

- On warm paper, ivory, white, or similarly light fields, use the primary logo.
- On charcoal or similarly dark fields, use the dark-background variant.
- Use monochrome black or white only where production is restricted to one colour.
- Never place the primary charcoal wordmark on a dark field.

## Platform notes

The Apple touch icon and YouTube avatar intentionally use an opaque warm-paper background for predictable platform rendering. The favicon and core logo PNGs retain transparency. The YouTube banner's important logo and phrase are entirely inside the central 1546×423px safe area.

## Supporting language

When channel artwork needs a descriptor, use only approved positioning-safe language such as:

- Independent product research
- Applied AI and operations

Do not invent slogans or add unsupported claims.

## Rebuild and verification

From the repository root:

```bash
python brand/identity/tools/generate_identity.py
npx -y -p @google/design.md designmd lint DESIGN.md
```

The generator parses the supplied SVG paths, writes all derivatives and public aliases, validates XML, image dimensions, alpha channels, ICO entries, contrast pairs, public alias integrity, and YouTube safe-area bounds, then records SHA-256 hashes.
