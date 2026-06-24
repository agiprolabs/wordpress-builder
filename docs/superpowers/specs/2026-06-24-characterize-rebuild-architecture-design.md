# Characterize → Rebuild Architecture (north-star design)

- **Date:** 2026-06-24
- **Status:** Approved architecture; supersedes the linear "Site Capture (Phase 1)" framing in
  `2026-06-23-site-capture-architecture-design.md`. That earlier spec's components are **not
  discarded** — they are reclassified below (§7).
- **Validation fixture:** `armandgilbert.com` (WordPress / DeepFocus).

---

## 1. Purpose & the corrected model

A developer takes over a client's site with **no original source files**. The platform must
(1) **characterize** the existing site into a tech-agnostic, human- and machine-readable
specification, then (2) **rebuild** it on a target stack — a fresh self-hosted WordPress, or a
modern React/Node/FastAPI app — preserving the look, feel, content, and functionality.

The earlier design drew **one linear pipeline** ending in a WordPress install. That was wrong on
two counts, corrected here:

1. **Capture has two *alternative*, access-gated source adapters — not pipeline stages.** When the
   site owner can install our **WordPress plugin**, we extract the backend directly (rich, exact).
   Otherwise we **crawl** the public site (derived, lower-fidelity). The plugin path **supplants**
   the crawl-based content extraction wholesale — it does not chain after it.
2. **The deliverable is a markdown-documented site spec, not a WordPress install.** WordPress
   install is just *one rebuild target*. Capture ends at the spec.

## 2. Two layers

```
CHARACTERIZE  (access-gated source  →  ONE markdown site spec)
   ├─ source A: WP backend plugin   — rich: real content, theme, DB, plugin data/config
   └─ source B: crawl / headless    — derived: content + computed-style design + inferred structure
        the plugin path SUPPLANTS source B's content extraction when available
   →  characterization/<site-slug>/  (the convergence artifact, §4)

REBUILD  (target-specific, separately forked; reads ONLY the spec)
   ├─ target: new WordPress         — FSE theme + content + plugins
   └─ target: React/Node/FastAPI    — preserve look/feel, re-implement behavior
```

**Invariants:**
- Both sources emit the **same spec shape**, differing only in richness/fidelity.
- Every rebuild target reads **only** the spec — never the live site, never the other layer.
- The spec is the single source of truth and the single convergence point.

## 3. Capture sources (access-gated)

### 3.1 Source A — WordPress backend plugin (high fidelity)
Installed by the site owner. Reads `wp_posts`/`postmeta` (real `post_content`), the media library,
menus, `wp_options`, the active theme, and **other plugins' data/config/tables** (e.g. Gravity
Forms definitions + entries). Produces exact content and exact plugin characterization.

### 3.2 Source B — crawl / headless (general fallback)
Playwright renders each page → deterministic content extraction + computed-style design derivation
+ asset capture. Plugins can only be **inferred** (detected + behaviorally described), not read.

**Selection:** owner-plugin when available; else crawl. The orchestrator picks per access; output
shape is identical.

## 4. The convergence artifact — markdown site spec

Each `.md` carries **YAML frontmatter (machine-consumable)** + **prose/tables (human-readable)** —
satisfying "both human documentation and machine-consumable" simultaneously.

```
characterization/<site-slug>/
  site.md                 # fm: {domain,title,tagline,detected_stack,plugins[],nav[]} + overview prose
  design/
    theme.md              # fm: design tokens — palette roles, font stacks, spacing scale,
    assets/               #     container widths, breakpoints — + prose design system
  pages/<page-slug>/
    page.md               # fm: {url,title,slug,parent,template,status}
    content.md            # verbatim text as markdown + ordered semantic-blocks list (in fm)
    layout.md             # regions/columns/sections, ordering, responsive notes
  components/             # cross-page reusable pieces
    <component>.md        # header, footer, sidebar, hero, …
  plugins/<plugin>.md     # fm: {name,version?,source: exact|inferred,data_ref?} + behavioral description
  backend/                # source-A only: forms.md, menus.md, options.md (+ data.json dumps)
  characterization.json   # machine index: assembles pointers + structured data across the whole tree
```

- **Human surface:** read any `.md`.
- **Machine surface:** the frontmatter of each file + the assembled `characterization.json`.
- **Content fidelity:** content text is captured **verbatim**, never LLM-paraphrased (carried over
  from the prior spec's hard rule). The LLM may assist design-token naming and plugin *description*
  only — never content.

## 5. Plugin characterization

For every detected plugin: identify it, then record EITHER
- **exact** — config + data, when source A (or a known plugin) gives it, OR
- **inferred** — a behavioral description of what it does (e.g. "multi-step quote form posting to
  /get-started, 4 steps, fields …") when only crawl data exists.
This lets a rebuild target reproduce the plugin exactly *or* re-implement its behavior.

## 6. Rebuild targets (separate forks; consume the spec only)

- **WordPress target:** spec → FSE theme (`theme.json` + templates) + page content (blocks) +
  plugin install/config. Reuses the prior spec's installer + theme-writer, **re-homed here**.
- **React/Node/FastAPI target:** spec → component tree + styling preserving look/feel + a backend
  re-implementing captured functionality (forms, data). Later fork.
- Each target has its own fidelity verifier (render target vs. spec/original).

## 7. Reclassification of the prior "Phase 1" build (15 tasks, branch `feat/site-capture-phase1`)

- **Keep as crawl-source capture components:** `discovery`, `renderer`, `content/extractor`
  (but retarget its output from WP blocks → neutral structured content for the spec),
  `design/tokens` + `design/llm` + `design/theme_writer` (deriver feeds `design/theme.md`),
  `media` localizer, `verify` (becomes a rebuild-target verifier).
- **Re-home as the WordPress *rebuild* target:** `installer` (+ `theme_writer`'s WP output, the
  WP-block `bundle` format). These are NOT capture.
- **Net-new work:** the **characterizer** (neutral content/design → markdown spec tree),
  **plugin characterization**, the **backend-plugin source adapter**, and the **rebuild-target
  abstraction** (so WP and React targets both consume the spec).

The prior `Site Capture Bundle` (WP-block `pages/*.html` + `theme.json`) is reinterpreted as a
**WordPress-rebuild-target artifact derived from the spec**, not the spec itself.

## 8. Sequencing

1. **This doc** — corrected architecture (done).
2. **Phase A — Characterize via crawl source:** characterizer emits the §4 tree from the existing
   extractor/deriver output; plugin *inference*. Validated on armand_gilbert (crawl).
3. **Phase B — Backend-plugin source adapter:** same tree, exact plugin data. Validated on a
   controlled WP instance we install the plugin on.
4. **Rebuild — WordPress target:** re-home installer/theme-writer to read the spec → WP. (This is
   what proves round-trip on armand_gilbert.)
5. **Rebuild — React/Node/FastAPI target:** later fork.

## 9. Open questions / deferred
- Exact frontmatter schemas per file type — pinned during Phase A planning.
- `characterization.json` assembly format — pinned during Phase A planning.
- How much plugin behavior is auto-inferable from crawl vs. needs human annotation — explored on
  the fixture.
- The prior branch's deferred items (run_capture placeholder report, minor test gaps) fold into the
  re-homing work in step 4.
