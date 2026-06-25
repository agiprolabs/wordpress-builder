# Phase B — Backend Source Adapter Design Spec

- **Date:** 2026-06-24
- **Status:** Approved design, pre-implementation
- **Parent architecture:** `2026-06-24-characterize-rebuild-architecture-design.md`
- **Sibling:** `2026-06-24-phase-a-characterizer-design.md` (crawl source — emits the same spec)
- **Scope:** the high-fidelity **backend** `CaptureSource` (WP plugin + Python adapter), a **golden
  mock WP** fixture, and a **backend-vs-crawl comparison harness**. Gravity Forms handler is deferred
  (paid); the first known-plugin handler targets a free form plugin (Fluent Forms).

---

## 1. Purpose

When the site owner can install our plugin (the "taking over an account" case), extract the **exact**
backend — real `post_content`, the media library, menus, options, the active theme, and other
plugins' data via a handler registry — and emit the **same markdown site spec** as the crawl path,
but richer. Validate it by running **both** ingestion paths against a controlled golden mock and
comparing. This proves the architecture's premise: same spec shape, backend more comprehensive,
crawl inferred.

## 2. Locked decisions

1. **Transport = WP plugin REST-JSON.** A PHP plugin exposes a structured JSON export. **The endpoint
   is user-definable in the plugin admin (any local or public IP/URL)**, supporting **pull** (Python
   fetches the WP REST route) and **push** (the plugin POSTs the export to a user-defined collector
   address — for firewalled/remote sites that can't accept inbound connections).
2. **Plugin handling = handler registry.** Known plugins → exact extractor; unknown → generic
   (`wp_options` + registered custom tables) + behavioral description. `source: exact | generic`.
3. **Validation fixture = golden mock WP** with a free form plugin (Fluent Forms) as the first known
   handler; GF deferred.
4. **Content parity is asserted on the static-text subset**, not wholesale — raw `post_content` does
   not expand shortcodes/dynamic/builder markup. Forms/dynamic regions compare via the plugin layer.
5. **Layout reference = screenshots** from the shared headless render (visual ground-truth, both paths).
6. **Page-builder content is a target** — content extraction parses Gutenberg blocks and **falls back
   to rendering-based extraction** for builder/classic/shortcode content.
7. **Media = whole library by default**, opt-*out* (de-select) in plugin admin; never opt-in.
   Ingestion discovers dynamic-content plugins so media is not wrongly pruned.
8. **Security:** plugin is **read-only**; token in **header** (not URL); **admin-capability** check;
   HTTPS-preferred; push target requires explicit admin confirmation.

## 3. The `sitecap-extractor` WordPress plugin (PHP)

Read-only. Admin settings page provides: a **generated token**, a **user-definable endpoint** (any
local/public IP/URL) used as the pull-allow origin and/or push target, a **transport mode** (pull |
push), and **media selection** (all by default, with opt-out de-selection).

- **Pull:** `GET /wp-json/sitecap/v1/export` — token in `X-Sitecap-Token` header; requires
  `manage_options`. Returns the JSON export (below).
- **Push:** on trigger, the plugin POSTs the same JSON to the configured endpoint.

**Export JSON shape:**
```jsonc
{
  "site": { "domain", "title", "tagline", "front_page_id", "permalink_structure" },
  "pages": [ { "id", "slug", "title", "parent", "template", "status", "post_content" } ],
  "posts": [ ... same shape ... ],
  "menus": [ { "name", "items": [...] } ],
  "media": [ { "id", "url", "alt", "mime", "meta", "selected": true } ],
  "theme": { "name", "is_block_theme", "theme_json"? },
  "plugins": {
    "active": [ { "slug", "name", "version" } ],
    "data": {
      "fluentform": { "source": "exact", "forms": [ { "id", "title", "fields": [ { "label", "type", "required", "options"? } ], "conditional_logic"? } ], "entries_count" },
      "<unknown>":  { "source": "generic", "options": {...}, "custom_tables": [...], "description" }
    }
  }
}
```

**Handler registry:** `register_handler(slug, callable)`; first handler = `fluentform` (exact). Unknown
active plugins → generic handler (their `wp_options` + custom tables they registered + a description).

**Dynamic-content discovery:** flag plugins known to serve rotating/dynamic media (sliders, galleries,
featured-content) in `plugins.data[...].dynamic_media: true` so the adapter retains their media and
characterizes the behavior.

## 4. The `BackendExtractor` Python adapter

`characterize/sources/backend.py` — a `CaptureSource` that fetches/loads the export JSON and builds a
`SiteCharacterization(source="plugin")` consumed by the **existing writer** (same markdown spec).

- **Content (shared strategy, reused by crawl too):**
  - Gutenberg `post_content` → parse block markup directly → neutral `Block` list (exact).
  - Classic/shortcode/page-builder `post_content` → **render the page** (shared headless renderer) and
    run the existing DOM `extract_blocks` (rendering fallback). Per-page choice based on content type.
  - `content_fingerprint` computed the same way → **comparable to crawl** on the static-text subset.
- **Plugins:** exact handler data → `PluginSpec(source="exact", fields w/ real types, conditional
  logic, entries summary)` + `data_ref` → `backend/<plugin>.md` (full definitions + entries). Generic
  handler data → `PluginSpec(source="generic", ...)` + `backend/<plugin>.md` (options/tables) + prose.
- **Media:** whole library (respecting plugin-side de-selection) → `localize_media` → `design/assets/`;
  attachment alt/meta preserved.
- **Theme:** FSE `theme_json` copied directly; else derive tokens via the shared render (Phase A deriver).
- **Screenshots & layout:** shared headless render captures per-page screenshots and computed styles
  → layout grid tree (Phase A builder) + screenshot reference.

## 5. Shared headless renderer (both paths)

The renderer is promoted to a **shared capture utility** used by crawl AND backend for: per-page
**screenshots** (layout ground-truth), **computed styles** (design tokens), and **content-fallback
rendering** (builder/classic pages). Backend mode = exact structured data (DB/plugins/media via the
plugin) **+** a render pass for visual/layout/builder-content.

## 6. Markdown spec additions (extends Phase A schema)

- `pages/<slug>/screenshot.png` — the render screenshot; referenced in `page.md` frontmatter
  (`screenshot: screenshot.png`) and usable by `layout.md` as visual ground-truth.
- `plugins/<slug>.md` frontmatter `source: exact | generic | inferred`; exact/generic carry
  `data_ref: backend/<slug>.md`.
- `backend/` dir (source-A only): `backend/<plugin>.md` (+ `data.json`) — exact form definitions +
  entries, or generic options/tables. `backend/menus.md`, `backend/options.md`.
- `site.md` frontmatter `source: plugin` (vs `crawl`); `dynamic_media_plugins: [...]`.

## 7. Golden mock WP + provisioning

A deterministic, repeatable Docker fixture (extends the existing compose). A WP-CLI provisioning
script builds: known pages/posts (**Gutenberg block content**, for clean content parity) + menus +
**Fluent Forms** installed with a real multi-field form rendered on a page. This is the "site of
record" both paths run against. (Distinct from the Phase-1 armand_gilbert static-HTML mock, which has
no real form plugin.)

## 8. Comparison harness (the validation)

Opt-in integration (`RUN_INTEGRATION=1`). Runs **both** paths against the golden mock and asserts:
- **Structure parity:** identical page-slug set + plugin-slug set.
- **Content parity (static-text subset):** per page, the static-text portion of crawl vs backend
  `content_fingerprint` matches (dynamic/plugin blocks excluded).
- **Layout reference:** both produce a screenshot per page (visual ground-truth recorded).
- **Backend ⊃ crawl on plugins:** backend form = `source: exact` with real field types + entries;
  crawl form = `source: inferred`. The harness computes an **inference-accuracy score** (fraction of
  field types/labels crawl matched against backend ground truth) — quantifying the gap the Phase-A
  validation exposed.

## 9. Prerequisite — crawl chrome-stripping fix (enables §8 content parity)

The Phase-A real run showed crawl currently captures WP `"Posted in"` post-meta + a duplicate
page-title `<h1>` as content. Backend `post_content` is clean. So content parity cannot pass until
crawl chrome-stripping is fixed. **First implementation step:** fix the crawl extractor's chrome
stripping (post-meta, duplicate title) — the comparison harness drives and verifies it.

## 10. Testing & scope

- **Plugin (PHP):** thin; validated by the golden-mock integration. Focused PHP unit only where logic
  warrants (handler registry, token check).
- **Adapter (Python):** unit-tested with a **captured fake JSON export** (no live WP) — content
  mapping, plugin mapping, media, source="plugin".
- **Harness:** opt-in integration against the golden mock.
- **In scope:** plugin + adapter + golden mock + comparison + screenshots + the crawl chrome fix.
- **Initial-target / extensible (not full in Phase B):** page-builder-specific parsers (rendering
  fallback covers them functionally now), dynamic-media-plugin discovery (registry hook + Fluent
  Forms/known sliders first), GF handler (deferred, paid).

## 11. Open questions / deferred
- Exact field-type vocabulary mapping (Fluent Forms types → spec field types) — pinned at planning.
- Push-mode delivery format (raw POST vs multipart with media) — pinned at planning; default raw JSON,
  media by URL.
- Inference-accuracy scoring formula thresholds — calibrated against the golden mock.
- GF handler + page-builder-specific parsers — separate follow-on specs.
