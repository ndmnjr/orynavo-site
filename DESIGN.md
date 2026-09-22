---
version: alpha
name: Orynavo
description: Restrained editorial identity for independent product research, combining a terracotta modular symbol with charcoal typography on warm paper.
colors:
  primary: "#c96442"
  secondary: "#141413"
  tertiary: "#a94d30"
  neutral: "#f5f4ed"
  ivory: "#faf9f5"
  muted: "#5e5d59"
  soft: "#e8e6dc"
  line: "#d8d5ca"
typography:
  display:
    fontFamily: Georgia, "Times New Roman", serif
    fontSize: 6rem
    fontWeight: 500
    lineHeight: 1
    letterSpacing: "-0.04em"
  heading:
    fontFamily: Georgia, "Times New Roman", serif
    fontSize: 2.5rem
    fontWeight: 500
    lineHeight: 1.15
    letterSpacing: "-0.02em"
  body:
    fontFamily: Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif
    fontSize: 1rem
    fontWeight: 400
    lineHeight: 1.6
    letterSpacing: "0em"
  label:
    fontFamily: Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif
    fontSize: 0.76rem
    fontWeight: 700
    lineHeight: 1.3
    letterSpacing: "0.13em"
rounded:
  sm: 6px
  md: 9px
  lg: 18px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 48px
  xxl: 96px
components:
  page:
    backgroundColor: "{colors.neutral}"
    textColor: "{colors.secondary}"
    typography: "{typography.body}"
  page-inverse:
    backgroundColor: "{colors.secondary}"
    textColor: "{colors.neutral}"
    typography: "{typography.body}"
  panel:
    backgroundColor: "{colors.ivory}"
    textColor: "{colors.secondary}"
    rounded: "{rounded.lg}"
    padding: "{spacing.lg}"
  supporting-copy:
    backgroundColor: "{colors.neutral}"
    textColor: "{colors.muted}"
    typography: "{typography.body}"
  inverse-supporting-copy:
    backgroundColor: "{colors.secondary}"
    textColor: "{colors.soft}"
    typography: "{typography.body}"
  brand-mark:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.secondary}"
    rounded: "{rounded.sm}"
  eyebrow:
    backgroundColor: "{colors.neutral}"
    textColor: "{colors.tertiary}"
    typography: "{typography.label}"
  divider:
    backgroundColor: "{colors.line}"
    textColor: "{colors.secondary}"
    height: 1px
  button-primary:
    backgroundColor: "{colors.secondary}"
    textColor: "{colors.neutral}"
    rounded: "{rounded.md}"
    padding: "{spacing.md}"
  button-primary-hover:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.secondary}"
    rounded: "{rounded.md}"
    padding: "{spacing.md}"
---

## Overview

Orynavo is an evidence-led umbrella for small, owner-light digital products. The identity should feel independent, exact, calm, and operationally credible. The open O and square module are the primary recognition device; their path geometry must never be redrawn, simplified, stretched, or rearranged.

Use an editorial hierarchy rather than a generic software aesthetic: generous whitespace, decisive type scale, thin rules, and one controlled accent. Do not use gradients, glass effects, invented claims, or decorative technology imagery.

## Colors

- **Terracotta / primary (`#c96442`):** The fixed symbol colour and a restrained accent for large marks, graphic fields, and non-text emphasis.
- **Charcoal / secondary (`#141413`):** Wordmark, primary text, and dark surfaces.
- **Dark terracotta / tertiary (`#a94d30`):** Accessible accent for small text such as eyebrows on warm paper.
- **Warm paper / neutral (`#f5f4ed`):** Default brand background.
- **Ivory (`#faf9f5`):** Raised or inset light surfaces.
- **Muted (`#5e5d59`):** Supporting copy on warm paper.
- **Soft (`#e8e6dc`):** Supporting copy and rules on charcoal.
- **Line (`#d8d5ca`):** Quiet dividers on light surfaces.

Terracotta is a recognition colour, not the default small-text colour. For normal-size text on warm paper, use dark terracotta, muted, or charcoal. Use charcoal text on terracotta fields and warm paper or soft text on charcoal fields.

## Typography

The supplied logo wordmark is outlined artwork and must not be recreated with a font. For communications and product surfaces, use Georgia for display and editorial headings. Use Inter where available, then the declared system sans-serif stack, for body copy, navigation, labels, and controls. Keep weights restrained; hierarchy should come primarily from scale, spacing, and alignment.

Uppercase labels use the `label` token and should remain short. Do not set paragraphs, slogans, or product names in all caps.

## Layout

Use a maximum content width near 1180px for web surfaces and a baseline spacing rhythm derived from 8px. Prefer asymmetric editorial compositions with clear alignment over repeated equal cards. Give the logo clear space of at least one square-module width on every side.

The YouTube banner's important lockup must remain inside the central 1546×423px safe area (`x=507–2053`, `y=509–932`) of the 2560×1440px canvas. Social avatars use the symbol only so the mark survives circular cropping.

## Elevation & Depth

The identity is predominantly flat. Separate surfaces with whitespace, tonal changes, or a one-pixel line before adding shadow. Do not use glassmorphism, glow, bevel, or gradient depth. If a product interface requires elevation, keep shadows neutral, low-opacity, and subordinate to the content hierarchy.

## Shapes

The open O and detached square are locked geometry. Preserve the supplied 1307×321 horizontal viewBox and the 321×321 symbol coordinate system. Do not alter the aperture, module size, curvature, proportions, or relationship between symbol and wordmark.

Interface corners may use the defined 6px, 9px, and 18px radii. Do not place the logo inside a pill, badge, or arbitrary container unless a platform requires an app-icon field.

## Components

- **Primary horizontal logo:** Terracotta symbol and charcoal wordmark on transparent or light backgrounds.
- **Dark-background logo:** Terracotta symbol and warm-paper wordmark on charcoal or comparably dark backgrounds.
- **Symbol:** Use alone for favicons, avatars, and square platform icons.
- **Monochrome marks:** Black for one-colour light-background reproduction; white for one-colour dark-background reproduction.
- **Eyebrow labels:** Dark terracotta on warm paper; short, uppercase, and widely tracked.
- **Primary actions:** Charcoal on warm paper. Terracotta may be used for hover or large-area emphasis with charcoal text.

Use only approved positioning-safe phrases when a channel requires supporting text, including “Independent product research” and “Applied AI and operations.”

## Do's and Don'ts

**Do**

- Use the supplied vector paths as the source of truth.
- Keep the logo transparent unless a platform requires an opaque canvas.
- Use warm paper and charcoal as the dominant fields.
- Check contrast whenever text crosses a coloured field.
- Use the symbol alone where the full wordmark would become too small.

**Don't**

- Do not distort, rotate, crop through, outline, shadow, or rebuild the mark.
- Do not recolour the primary symbol away from terracotta.
- Do not use gradients or an expanded rainbow palette.
- Do not invent slogans, performance claims, or broad category claims.
- Publish derivatives only through the identity generator so the reviewed master geometry and public aliases stay synchronized.
