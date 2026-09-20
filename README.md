# Orynavo

Live site: https://orynavo.com/

A production-ready, static credibility site for Orynavo: an evidence-led umbrella for small, owner-light digital products.

## Files

- `index.html` — single-page public site
- `privacy.html` — plain-language privacy notice
- `404.html` — custom not-found page
- `favicon.ico` — multi-size browser icon (16, 32, 48, and 64px)
- `email-signature-logo.png` — transparent 320×80px logo for 2× email rendering
- `.gitignore` — local tooling exclusions

All CSS and JavaScript are embedded. Brand and open-graph artwork is hosted from the site root. There is no build step, dependency, tracking script, or external font request.

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

Run the deterministic checker:

```bash
python verify_site.py
```

The checker validates required files, document metadata and landmarks, local links and fragment targets, image alternatives, HTTPS external links, required messages, reduced-motion CSS, the physical ICO structure and sizes, and the signature PNG dimensions.

With the local server running, use Chrome to check horizontal overflow and capture full-page screenshots at desktop and 390px widths:

```bash
python verify_visual.py
```

Screenshots are written to the ignored `screenshots/` directory.

## Deployment

GitHub Pages serves the `main` branch from the repository root. `orynavo.com` is the canonical domain and `404.html` handles not-found routes.
