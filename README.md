# Orynavo

Live site: https://orynavo.com/

A production-ready static site for Orynavo, an operator-led applied AI and operations consultancy.

## Files

- `index.html` — single-page public site
- `privacy.html` — plain-language privacy notice
- `404.html` — custom not-found page
- `favicon.ico` — multi-size browser icon (16, 32, 48, and 64px)
- `favicon.svg` and `apple-touch-icon.png` — modern browser and device icons
- `og-image.png` — 1200×630px Open Graph sharing image
- `email-signature-logo.png` — transparent 320×80px logo for 2× email rendering
- `brand/new-logo/Orynavo-logo.svg` — approved source artwork
- `brand/identity/` — generated identity system, usage guide, validation report, and integrity manifest
- `DESIGN.md` — machine-readable brand tokens and usage guidance
- `.gitignore` — local tooling exclusions

All CSS and JavaScript are embedded. Brand and Open Graph artwork is hosted from the site root. The public site has no runtime build step, tracking script, or external font request.

## Email signature logo

Use the hosted PNG at `https://orynavo.com/email-signature-logo.png`. It is a 320×80px transparent image designed to display at 160×40px for crisp 2× rendering:

```html
<img src="https://orynavo.com/email-signature-logo.png" width="160" height="40" alt="Orynavo">
```

Keep the `alt="Orynavo"` text so the brand remains available when images are blocked or to people using assistive technology. Do not use an empty alt attribute unless the same linked text appears immediately beside the image.

## Run locally

From this directory:

```bash
python -m http.server 4173 --bind 127.0.0.1
```

Then open `http://127.0.0.1:4173/`.

## Quality checks

Regenerate and validate the identity, lint the design specification, then run the deterministic site checker:

```bash
python brand/identity/tools/generate_identity.py
npx -y -p @google/design.md designmd lint DESIGN.md
python verify_site.py
```

The identity generator creates all derivatives and root aliases from the approved SVG source. The site checker validates required files, document metadata and landmarks, local links and fragment targets, image alternatives, HTTPS external links, required consultancy positioning, reduced-motion CSS, root asset integrity, the physical ICO structure and sizes, and the signature PNG dimensions.

With the local server running, use Chrome to check horizontal overflow and capture full-page screenshots at desktop and 390px widths:

```bash
python verify_visual.py
```

Screenshots are written to the ignored `screenshots/` directory.

## Deployment

GitHub Pages serves the `main` branch from the repository root. `orynavo.com` is the canonical domain and `404.html` handles not-found routes.
