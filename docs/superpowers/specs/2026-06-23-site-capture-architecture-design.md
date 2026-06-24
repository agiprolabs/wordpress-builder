# Site Capture Architecture — Phase 1 Design Spec

- **Date:** 2026-06-23
- **Status:** Approved design, pre-implementation
- **Scope:** Phase 1 (Capture). Phase 2 (theme-swap redesign + hand-off) is a separate spec.
- **Validation fixture:** `armandgilbert.com` (the current reference clone).

---

## 1. Purpose & Context

We are building a platform for a web developer who is taking over a client account
from a previous developer **without any original source files**. The platform must:

1. **Capture** an existing live website into a fresh, developer-hosted WordPress
   install as a faithful, editable baseline ("clone any site reliably").
2. **Redesign** (Phase 2) by swapping the look while preserving the captured
   content, enabling seamless iteration from the old site to a new design.

This spec covers Phase 1 only.

### The problem with the current approach
The existing reference clone (`migrate_armand_gilbert.py` + `premium-mockup-styles.php`)
proved fidelity is achievable, but in a way that does **not generalize**:

- **Fidelity = ~1,450 lines of hand-authored, site-specific CSS** keyed on one body
  class. Every new site would mean another bespoke stylesheet.
- **Content is welded to the old design's markup** (`#left-area`, `#content-area`
  wrappers, inline divs baked into page content and templates), so there is no clean
  seam to apply a *new* design.
- **The migration drops content.** Investigation of `/get-started/` found the page
  title (`<h1 class="title">Get Started</h1>`) and intro copy were never captured —
  which is what made the form appear to collide with the header logo banner. The
  "header overlap" was a **content-fidelity gap masquerading as a CSS bug.**
- **Assets are partially remote** (header logo, menu background still load from the
  live domain despite a media import).
- The AI generator (`builder.py`/`generator.py`) produces *fresh* designed content
  from lead data (a ~370-line hardcoded `get_inner_pages_content`) — it does not
  build on the captured original at all.

## 2. Goals & Non-Goals

### Goals (Phase 1)
- Given a live URL, produce an **editable, visually-faithful WordPress baseline**.
- **Content captured 1:1** — every page's text, structure, images, and forms,
  verbatim, with **no old-theme presentation markup**.
- **Design auto-derived** from the original's computed styles into a generated FSE
  theme (`theme.json` + templates/parts) — "faithful enough," fully automated.
- **All assets localized** (no live-domain dependencies).
- A **fidelity verifier** that proves content matches exactly and design is close.
- The whole thing **generalizes** to arbitrary sites, validated on armand_gilbert.

### Non-Goals (Phase 1)
- Theme-swap / redesign UX and alternate-theme generation (Phase 2).
- Pixel-perfect, hand-tuned per-site reproduction (explicitly rejected: not automatable).
- Server-side reproduction of dynamic plugins (forms/sliders are captured as flagged
  placeholders, not functionally re-implemented).
- AI rewriting/paraphrasing of content (forbidden — breaks fidelity).

## 3. Core Decisions (locked during brainstorming)

1. **Content/design seam = WordPress-native.** Capture stores theme-agnostic semantic
   blocks; redesign swaps the FSE theme. Content unchanged, look changes.
2. **Fidelity bar = auto-derived faithful theme.** Content 1:1 deterministic; design
   derived from computed styles (palette/fonts/spacing/layout), not hand-tuned.
3. **Capture input = live site, headless render** (Playwright) for DOM + computed
   styles + assets. (No static-HTML-only fallback in Phase 1.)
4. **Extraction strategy = hybrid.** Content extraction is strictly deterministic and
   never passes through an LLM; the LLM/heuristics assist only the design layer.

## 4. The Seam: Site Capture Bundle

The theme-agnostic artifact that decouples content from design. It is the contract:
the capture pipeline produces it, the WP installer consumes it, and Phase 2 swaps the
`theme/` directory while keeping `pages/` + `media/` untouched.

```
capture/<site-slug>/
  manifest.json        # ordered pages (url, slug, title, parent), nav menu(s),
                       # site title/tagline, front-page slug, per-page capture status
  pages/<slug>.html    # WordPress core-block markup, CONTENT ONLY, verbatim text.
                       # No theme wrappers. One file per captured page.
  media/               # every downloaded asset (images, fonts, css bg images),
                       # deduped, local relative paths
  theme/               # derived FSE theme
    theme.json         # palette, typography, spacing, layout widths (tokens)
    templates/         # index.html, page.html, front-page.html (structural layout)
    parts/             # header.html, footer.html
    styles/            # supplementary CSS for specifics not expressible as tokens
  design-tokens.json   # raw extracted tokens + provenance (audit trail)
  fidelity-report.json # content-diff (exact) + design-diff (closeness) + pass/fail
```

**Invariants:**
- `pages/*.html` contains only core blocks and flagged placeholders — never
  theme-specific class wrappers, never paraphrased text.
- Swapping `theme/` must never require touching `pages/` or `media/`.
- `manifest.json` is the single source of truth for site structure.

## 5. Components

Each component has one responsibility, a defined interface, and is independently
testable. Proposed home: `capture/` (this repo, alongside `builder.py`).

### 5.1 Renderer (`renderer.py`)
- **Job:** the only live-network boundary. Drive Playwright to load each page.
- **Input:** list of page URLs (from sitemap/crawl) + viewport config.
- **Output (per page):** rendered DOM (HTML), computed-style snapshots for a sampled
  set of elements (body, headings, links, containers, header/footer, buttons, inputs),
  full-page screenshot, and the list of network asset URLs requested.
- **Depends on:** Playwright. Nothing downstream touches the live network.
- **Notes:** retries + timeout per page; records failures without aborting the run.

### 5.2 Content Extractor (`content/`)
- **Job:** deterministic DOM → WordPress core-block markup.
- **Input:** rendered DOM for a page.
- **Output:** `pages/<slug>.html` (core blocks) + a **content fingerprint**
  (normalized text + block-structure hash) used by the verifier.
- **Mapping:** heading→`wp:heading`, paragraph→`wp:paragraph`, list→`wp:list`,
  image→`wp:image` (src rewritten to local), table→`wp:table`, links/buttons→
  `wp:buttons`, iframes/embeds→`wp:embed`/`wp:html`. Main-content region detection
  strips chrome (header/nav/footer/sidebar) — those become theme parts, not content.
- **Plugins/forms:** detect (e.g. Gravity Forms markers) → emit a flagged placeholder
  block (`wp:html` with a comment) recorded in the report. Not functionally rebuilt.
- **Hard rule:** never invokes an LLM; never alters text content.

### 5.3 Design Deriver (`design/`)
- **Job:** computed styles → token system + structural theme.
- **Input:** computed-style snapshots + screenshots across captured pages.
- **Output:** `theme.json`, `templates/`, `parts/`, `styles/`, `design-tokens.json`.
- **Derivation:** palette via color frequency + role inference (background/text/
  accent/link); typography via font-family stacks + size scale; spacing scale;
  container widths; header/footer structure reconstructed from chrome regions.
- **Bounded LLM pass:** only to clean/name/deduplicate tokens and resolve ambiguous
  semantic grouping. It sees tokens and structure, **never content text**. Its output
  is constrained (token JSON), validated, and never gates content.
- **The fuzzy layer:** verified by closeness, not exactness.

### 5.4 Media Localizer (`media.py`)
- **Job:** download every referenced asset and rewrite URLs to local relative paths.
- **Input:** asset URL list from the Renderer + references in blocks/theme.
- **Output:** populated `media/` (deduped) + a URL→local-path rewrite map applied to
  `pages/*.html` and `theme/`.
- **Fixes:** today's "logo/menu-bg still load from live domain" gap.

### 5.5 WP Installer (`installer.py`)
- **Job:** consume a Bundle and produce a running local WordPress site.
- **Steps:** DB reset → fresh WP install → register & activate derived theme → create
  pages from block markup (parent/child per manifest) → import media with correct
  ownership (`www-data:www-data`) → build nav menu(s) → set static front page.
- **Generalizes:** the install/media/menu logic currently hardcoded in
  `migrate_armand_gilbert.py` and `builder.py`, reading the Bundle instead of one site.
- **Deploy note:** WP files live in the **named Docker volume `wp_data`, not a bind
  mount** — the installer operates inside the container (or `docker cp` + chown).

### 5.6 Fidelity Verifier (`verify.py`)
- **Job:** prove the captured site matches the original.
- **Method:** render captured (localhost) vs original (live) via Playwright.
- **Content check — EXACT:** per page, normalized visible text + block structure must
  match the original's content fingerprint. Any diff = **failure** (gates "done").
- **Design check — CLOSENESS:** palette ΔE, font-family match, and key layout metrics
  (container widths, header height, font scale) within tolerance. **Reported, not
  gated.**
- **Output:** `fidelity-report.json` + overall pass/fail.

### 5.7 Orchestrator (`capture.py`)
- **Job:** CLI entry point. `capture <url> [--slug] [--max-pages N]`.
- **Flow:** discover pages (sitemap/crawl) → Renderer → (Content Extractor + Design
  Deriver) → Media Localizer → write Bundle → WP Installer → Fidelity Verifier → report.
- **Isolation:** per-page failures are logged and skipped, never fatal to the run.

## 6. Data Flow

```
sitemap/crawl ─▶ Renderer ─▶ {DOM, computed styles, screenshots, asset list}
                                │
        ┌───────────────────────┼────────────────────────┐
        ▼                       ▼                         ▼
 Content Extractor        Design Deriver           Media Localizer
   pages/*.html            theme/ + tokens            media/ + rewrite map
        └───────────────────────┴────────────────────────┘
                                │
                          Site Capture Bundle
                                │
                          WP Installer ─▶ running local WP
                                │
                        Fidelity Verifier ─▶ fidelity-report.json (pass/fail)
```

## 7. Error Handling & Robustness
- Per-page try/catch; a failed page is recorded in `manifest.json` and the run continues.
- Renderer: retries + timeouts; missing assets recorded, not fatal.
- Plugin-dependent content → explicit flagged placeholders in the report (honest, not
  silent truncation).
- Verifier content-check failure **blocks any "capture complete" claim.**

## 8. Testing & Verification
- **Golden fixture:** armand_gilbert. Capture must reproduce all pages; content-diff
  exact; design-diff within tolerance.
- **Unit tests:** per extractor mapping (DOM snippet → expected block markup); per
  design-derivation rule (computed-style sample → expected token).
- **Integration test:** the Fidelity Verifier itself, run against the fixture.
- **Regression guard:** the dropped-title/intro bug becomes a specific content-diff
  test case (the original `/get-started/` must capture title + promo + intro copy).

## 9. Relationship to Existing Code
- `migrate_armand_gilbert.py` → install/media/menu steps generalize into **WP
  Installer**; bespoke per-site logic retired once the verifier passes on the fixture.
- `builder.py` / `generator.py` (AI generation, `get_inner_pages_content`) → **not used
  in capture**; repurposed in Phase 2 as an alternate-theme "design provider."
- `premium-mockup-styles.php` (hand-tuned armand_gilbert CSS) → **reference target**
  for the Design Deriver: the quality bar its automated output should approach.
- `SKILL.md` (wordpress-builder) → operational notes (deploy workflow, header geometry,
  findings) feed the Installer and Deriver implementations.

## 10. Success Criteria
1. `capture <armandgilbert-url>` runs end-to-end and produces a complete Bundle.
2. The installed local site renders every captured page with **zero remote-asset
   dependencies**.
3. Fidelity report: **content-diff exact** on all pages (incl. previously-dropped
   title/intro copy); design-diff within tolerance.
4. No site-specific code paths in the pipeline — the same code path would run for a
   different input site.

## 11. Open Questions / Deferred
- Page discovery details (sitemap vs crawl depth/limits) — resolved at planning time.
- Exact design-closeness tolerances — calibrated against the fixture during implementation.
- Phase 2 (theme-swap, hand-off, alternate-theme generation) — separate spec.
