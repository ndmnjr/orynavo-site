# Orynavo

Live site: https://orynavo.com/

A production-ready, static credibility site for Orynavo: an evidence-led umbrella for small, owner-light digital products.

## Files

- `index.html` — single-page public site
- `privacy.html` — plain-language privacy notice
- `404.html` — custom not-found page
- `.gitignore` — local tooling exclusions

All CSS, JavaScript, icons, and open-graph artwork are embedded. There is no build step, dependency, tracking script, or external font request.

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

The checker validates required files, document metadata and landmarks, local links and fragment targets, image alternatives, HTTPS external links, required messages, and reduced-motion CSS.

With the local server running, use Chrome to check horizontal overflow and capture full-page screenshots at desktop and 390px widths:

```bash
python verify_visual.py
```

Screenshots are written to the ignored `screenshots/` directory.

## Deployment

GitHub Pages serves the `main` branch from the repository root. `orynavo.com` is the canonical domain and `404.html` handles not-found routes.
