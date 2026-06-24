# Phase A — Crawl-Source Characterizer Design Spec

- **Date:** 2026-06-24
- **Status:** Approved design, pre-implementation
- **Parent architecture:** `2026-06-24-characterize-rebuild-architecture-design.md`
- **Scope:** Phase A only — the **crawl source** emitting the markdown site spec. The backend-plugin
  source (Phase B) and rebuild targets (WordPress, React/Node/FastAPI) are separate specs.
- **Validation fixture:** `armandgilbert.com`.

---

## 1. Purpose

Transform the crawl-source capture output (Playwright render → DOM + computed styles + assets) into
the **markdown site spec** — the tech-agnostic convergence artifact that every rebuild target reads.
This makes the characterization the deliverable (not a WordPress install), and retargets the
existing extractor from WP-block output to a **neutral block model**.

## 2. The markdown spec (locked schema)

```
characterization/<site-slug>/
  site.md  design/theme.md  design/assets/
  pages/<page-slug>/{page.md, content.md, layout.md}
  components/<component>.md
  plugins/<plugin>.md
  backend/                       # Phase B (source A) only — absent in Phase A
  characterization.json
```

Every `.md` = **YAML frontmatter (machine)** + **prose/tables (human)**. Frontmatter schemas:

### site.md
```yaml
domain: armandgilbert.com
title: "Armand Gilbert Web Design IT & Marketing"
tagline: "..."
source: crawl                      # crawl | plugin
captured_at: <iso8601>
detected_stack: {cms: wordpress, theme: "DeepFocus", server: apache}
nav: [{label: Home, url: /, children: []}, {label: About, url: /about-us/}]
pages: [home, about-us, get-started, contact-us, faq]
plugins: [gravity-forms]
```
Body: business/site overview prose.

### design/theme.md
```yaml
palette: {background: "#ffffff", text: "#332b24", accent: "#986c04", link: "#986c04"}
typography:
  body: {family: "ColaborateThinRegular, sans-serif", base_size: 14px}
  heading: {family: "...", scale: [32,24,20,18]}
spacing_scale: [8,16,24,32]
layout: {container_width: 960px, breakpoints: [480,768,980]}
font_assets: [design/assets/colab-thin.woff]
```
Body: design-system prose (look & feel character).

### pages/<slug>/page.md
```yaml
url: /get-started/
slug: get-started
title: Get Started
parent: null
template: page                     # front-page | page | post | archive
status: published
content_ref: content.md
layout_ref: layout.md
```
Body: page-purpose summary.

### pages/<slug>/content.md
```yaml
slug: get-started
content_fingerprint: <sha256>      # normalized text+structure — guarantees 1:1 verification
blocks:
  - {type: heading, level: 1, text: "Get Started"}
  - {type: paragraph, text: "Call 760-632-8258 for a Free Web Site Consultation."}
  - {type: plugin, ref: plugins/gravity-forms.md, instance: form_1}
  - {type: image, asset: design/assets/x.png, alt: "..."}
```
Block taxonomy: **heading · paragraph · list · image · table · button · embed · plugin**.
Body: human-readable markdown render of the same content (verbatim text, never paraphrased).

### pages/<slug>/layout.md
```yaml
slug: get-started
grid:                              # nested grid tree (recursive)
  node: container
  layout: {display: flex, direction: column}
  children:
    - {node: component, ref: components/header.md}
    - node: container
      layout: {display: grid, columns: "1fr 300px", gap: 24px}
      children:
        - {node: content, area: main, blocks_ref: content.md}
        - {node: component, area: aside, ref: components/sidebar.md}
    - {node: component, ref: components/footer.md}
responsive:
  - {breakpoint: 768, override: {columns: "1fr"}}
```
`node ∈ {container, content, component}`. Containers carry CSS grid/flex `layout` + `children`;
leaves reference `content.md` blocks or a component. Body: layout prose.

### components/<x>.md
```yaml
name: header
appears_on: all                    # all | [slugs]
type: site-chrome                  # site-chrome | hero | sidebar | repeated-block
elements: [{type: logo, asset: design/assets/logo.png}, {type: nav, ref: site.md#nav}]
```
Body: component description.

### plugins/<x>.md
```yaml
name: Gravity Forms
slug: gravity-forms
source: inferred                   # exact | inferred (Phase A is always inferred)
version: null
behavior: "Multi-step form w/ validation + progress bar"
instances:
  - {id: form_1, title: "Web Design Questionnaire", pages: [get-started], steps: 4,
     fields: [{label: Name, type: name, required: true}, {label: Email, type: email, required: true}],
     submit: {action: /get-started/, method: post}}
data_ref: null                     # → backend/forms.md when source=exact (Phase B)
```
Body: behavioral description / re-implementation notes.

### characterization.json
Assembles every file's frontmatter into one machine index: `{spec_version, site, design, pages[]
{slug, page, content, layout}, components[], plugins[], backend?}`. The machine surface for rebuild
targets.

## 3. Components (new `characterize/` package)

1. **`characterize/models.py`** — dataclasses: `Block` (tagged union by `type`), `GridNode`,
   `PageSpec`, `SiteSpec`, `ComponentSpec`, `PluginSpec`, `SiteCharacterization`. Each with
   `to_frontmatter()` (YAML-able dict) and JSON round-trip.
2. **Retarget `content/extractor.py`** — emit `list[Block]` (neutral) instead of WP-block-comment
   strings. The block taxonomy above. `content_fingerprint` computed over the neutral blocks (stable
   text+type+order). **`content/blocks.py` (WP-block builders) moves to the WordPress rebuild target**
   — it is no longer part of capture.
3. **`characterize/layout.py`** — build the nested grid tree from the rendered DOM + computed styles:
   detect main content region, columns (flex/grid containers), and chrome regions → `GridNode` tree.
   Best-effort/heuristic for crawl source; records confidence.
4. **`characterize/components.py`** — detect cross-page repeated chrome (header/footer/nav/sidebar)
   by comparing DOM across pages → `ComponentSpec` files; pages reference them instead of inlining.
5. **`characterize/plugins.py`** — infer plugins from DOM signatures (e.g. `.gform_wrapper`,
   generator meta tags, known asset URLs) → `PluginSpec` with `source: inferred` + per-instance
   field extraction (form fields, steps, submit target).
6. **Reuse `design/tokens.py` + `design/llm.py`** — feed `design/theme.md` frontmatter (LLM may
   name/clean tokens + write the design-system prose; never touches content).
7. **Reuse `media.py`** — populate `design/assets/`, rewrite asset refs in blocks/theme to relative
   `design/assets/<name>` (spec-relative, not install-relative — rebuild targets remap).
8. **`characterize/writer.py`** — render the `SiteCharacterization` to the markdown tree
   (frontmatter + prose bodies) + `characterization.json`.
9. **`characterize/characterizer.py`** — orchestrator: discover → render → (extract neutral blocks +
   layout tree + components + plugins + design) → assemble `SiteCharacterization` → write tree.

## 4. Data flow

```
discovery → renderer → {DOM, computed styles, assets} per page
   ├─ extractor      → list[Block] + content_fingerprint   → content.md
   ├─ layout         → GridNode tree                        → layout.md
   ├─ components      → cross-page chrome                    → components/*.md
   ├─ plugins         → inferred PluginSpec + instances      → plugins/*.md
   ├─ tokens+llm      → design tokens + prose                → design/theme.md
   └─ media           → assets + ref rewrite                 → design/assets/
→ SiteCharacterization → writer → characterization/<slug>/ tree + characterization.json
```

## 5. Verification (Phase A)

- **Content 1:1:** `content_fingerprint` per page must match the original render's fingerprint
  (the regression fixture: `/get-started/` must capture the title + "760-632-8258" intro). Reuses the
  existing exact-content gate.
- **Spec round-trip:** re-loading `characterization.json` reconstructs the same `SiteCharacterization`
  (lossless frontmatter ↔ model).
- **Schema validity:** every `.md` frontmatter validates against its model.
- Design closeness is deferred to rebuild-target verifiers (a rebuilt site vs. original), not Phase A.

## 6. Non-goals (Phase A)
- Backend-plugin source / exact plugin data / `backend/` dir (Phase B).
- Any rebuild (WP or React) — the WP-block builders + installer are the WordPress *rebuild target*,
  specced separately.
- Pixel-perfect layout inference — the grid tree is best-effort from crawl; rebuild + verify closes
  the loop.

## 7. Open questions / deferred
- Confidence scoring + human-annotation hooks for low-confidence layout/plugin inference.
- Exact LLM prompt for design-system prose (bounded, design-only).
- `characterization.json` schema versioning policy.
