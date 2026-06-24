# wordpress-builder — Site Cloning Skill & Operational Notes

Living document for reliably cloning a legacy website into a local WordPress FSE
mockup, then handing it off for redesign. Captured while recreating
`https://armandgilbert.com` (DeepFocus theme) as the reference 1:1 clone.

---

## 1. Stack & how a mockup is assembled

- **Source theme:** legacy site runs Elegant Themes **DeepFocus** (classic theme,
  `#header` / `#logo` / `#menu` / `#left-area` / `#sidebar` markup).
- **Target:** a block (FSE) theme `custom-theme/premium-fse-theme` + a Must-Use
  plugin `premium-mockup-styles.php` that carries ALL the 1:1 CSS, scoped by a
  body class `vertical-<slug>` (here `vertical-armand_gilbert`).
- **Containers** (`docker-compose.yml`): `wp_mockup_app` (wordpress:latest, :8080),
  `wp_mockup_db` (mysql:8.0). Generator: `prospector/wp-mockup-generator/generator.py`.

## 2. ⚠️ Deploy workflow (the #1 gotcha)

WordPress files live in a **named Docker volume `wp_data`, NOT a bind mount.**
Editing files in this repo does **not** change the running site. You must copy in:

```bash
# mu-plugin (all the CSS overrides)
docker cp premium-mockup-styles.php \
  wp_mockup_app:/var/www/html/wp-content/mu-plugins/premium-mockup-styles.php
# theme templates/parts
docker cp custom-theme/premium-fse-theme/templates/page.html \
  wp_mockup_app:/var/www/html/wp-content/themes/premium-fse-theme/templates/page.html
docker exec wp_mockup_app chown -R www-data:www-data /var/www/html/wp-content
```

Verify with `grep -c "<marker>"` inside the container. Then hard-reload the page.

## 3. CSS override pattern

Add rules at the **end** of the `<style>` block in `premium-mockup-styles.php`
(last in source order) scoped to `body.vertical-<slug>`. Beware **blanket rules**
that leak: a global `form label { text-transform:uppercase }` was uppercasing
every Gravity Forms label/sublabel. Always scope and out-specify.

## 4. DeepFocus header geometry (armand_gilbert)

- `#header`: 960×165, the visible header band.
- `#logo`: **absolute, top:0, 947×480, z-index 10** — a tall "dual-logo" banner PNG
  (`header-dual-logo3.png`): logo on top, "Free Consultation / phone / email" promo
  below. It deliberately overflows the 165px header by 315px.
- `#menu`: absolute, top:111, 960×55, nav background image.
- Subpage content (`#left-area` / `#sidebar`) sits in `#content-area` and must
  begin **below the ~480px banner** to avoid being covered.

## 5. ✅ Task 1 — Gravity Forms 1:1 (DONE)

Added a scoped GF block (search `Gravity Forms 1:1` in the mu-plugin). Fixed:
- `.gform_fields` → 12-col grid; killed theme `list-style` bullets on `li.gfield`.
- `.gform-grid-row` flex → First/Last, City/State, ZIP/Country side-by-side.
- Labels mixed-case bold + small gray sublabels (undid uppercase leak).
- Blue filled `.gf_progressbar_percentage` via `.percentbar_25/50/75/100` widths.
- `.gsection_title` gray/thin; plain multi-step Next/Prev buttons.
Verified in-browser against the live form (`/get-started/`).

## 6. 🔑 Key finding — "header overlap" is a CONTENT-FIDELITY gap, not CSS

The form appeared to collide with the logo banner. Root cause is NOT layout:

- **Original** `/get-started/`: `.entry` contains, above the form — an
  `<h1 class="title">Get Started</h1>`, a promo block ("Call 760-632-8258 for a
  Free Web Site Consultation…"), and an intro paragraph. That ~242px of real
  content pushes the form to `top:521`, clearing the 480px banner.
- **Clone:** the migration **dropped the page title and all intro copy**, so the
  form starts at `top:279` — under the banner.

A CSS push-down would hide the symptom while leaving the page genuinely missing
its title + copy (not truly 1:1). Partial fix applied: `page.html` now renders
`wp:post-title` (general, correct for every subpage). **Full fix requires the
migration to capture full page `post_content`** (title + body), which is a
pipeline-level concern, not a per-site stylesheet patch.

## 7. Generalization gaps (for the capture → redesign platform)

These block "clone any site reliably," not just this one:
1. **Fidelity = hand-authored per-site CSS.** ~1,450 lines keyed on one body class.
   Does not scale to N sites; no clean seam to swap a *new* design over captured content.
2. **Migration drops content** (page titles, intro/body copy) — see §6.
3. **Assets partially remote.** Header logo + menu bg still load from
   `armandgilbert.com` (not localized), despite the media import.
4. **Templates incomplete.** `page.html` lacked a title block; subpage structure
   assumes DeepFocus-specific wrappers.

**Implication:** a generalized pipeline should separate (a) a theme-agnostic
**capture** layer (content + structure + assets → blocks/templates, verifiable 1:1)
from (b) an interchangeable **design** layer applied over captured content.

## 8. Verification workflow

Use Playwright to compare local vs original: element screenshots of the same
selector, and `getComputedStyle` diffs (position, font, color, grid). Measure
`getBoundingClientRect().top` to catch layout/clearance regressions.

## Open / TODO
- [ ] Task 2: nav submenu + search icon styling
- [ ] Task 3: FAQ accordions/tabs JS + toggle styling
- [ ] Task 4: sidebar alignment (borders, separators, widget margins)
- [ ] Restore dropped page content (title + intro) via migration, not CSS
- [ ] Localize remaining remote assets (logo, menu bg)
