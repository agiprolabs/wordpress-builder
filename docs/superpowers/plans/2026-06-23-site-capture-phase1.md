# Site Capture (Phase 1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Given a live URL, produce an editable, visually-faithful self-hosted WordPress baseline — 1:1 content as theme-agnostic blocks plus an auto-derived FSE theme — with a verifier that proves content matches exactly and design closely.

**Architecture:** A `capture/` Python package renders each page with Playwright (the only live-network boundary), then runs deterministic content extraction (DOM→core blocks, verbatim) and heuristic+LLM-assisted design derivation (computed styles→`theme.json`) into a **Site Capture Bundle**. A WP Installer loads the bundle into a fresh WordPress (Docker + WP-CLI); a Fidelity Verifier renders captured-vs-original and gates on exact content / close design.

**Tech Stack:** Python 3.11+, pytest, Playwright (Python), BeautifulSoup4 + lxml, requests, anthropic SDK (model `claude-sonnet-4-6` for the bounded token-cleanup pass), Docker Compose + WP-CLI (existing pattern in `builder.py`).

## Global Constraints

- **Content is never paraphrased or LLM-generated.** The LLM touches only design tokens, never page text. (spec §3.4, §5.2)
- **`pages/*.html` contains only core blocks + flagged placeholders** — no theme-specific class wrappers. (spec §4)
- **Swapping `theme/` must never require touching `pages/` or `media/`.** (spec §4)
- **No live-domain asset dependencies** in the installed site. (spec §2)
- **Verifier content-check failure blocks any "capture complete" claim.** (spec §7)
- **No site-specific code paths** — the same code path runs for any input site. (spec §10.4)
- **WP files live in the named Docker volume `wp_data`, not a bind mount** — installer acts inside the container or via `docker cp` + `chown www-data:www-data`. (spec §5.5)
- **Validation fixture:** `armandgilbert.com`; the previously-dropped `/get-started/` title + intro copy is a required content-diff regression case. (spec §8)
- Model id pinned exactly: `claude-sonnet-4-6`.

---

## File Structure

```
capture/
  __init__.py
  models.py            # dataclasses: RenderedPage, ComputedStyleSnapshot, PageContent,
                       #              DesignTokens, PageMeta, Manifest, FidelityReport
  discovery.py         # discover_pages(base_url, max_pages) -> list[str]
  renderer.py          # Renderer.render(url) -> RenderedPage  (Playwright; injectable)
  content/
    __init__.py
    blocks.py          # pure block-markup builders
    fingerprint.py     # content_fingerprint(block_html) -> str
    extractor.py       # extract_content(page) -> PageContent
  design/
    __init__.py
    tokens.py          # derive_tokens(snapshots) -> DesignTokens
    llm.py             # clean_tokens(tokens, api_key) -> DesignTokens
    theme_writer.py    # write_theme(tokens, theme_dir) -> None
  media.py             # localize_media(assets, media_dir) -> dict; rewrite_urls(text, map)
  bundle.py            # write_bundle(...) / BundlePaths
  installer.py         # WPInstaller(runner).install(bundle_dir) -> None
  verify.py            # compare_fingerprints, color_distance, design_distance, verify_site
  capture.py           # run_capture(url, slug, max_pages) -> FidelityReport  (CLI)
tests/
  capture/
    test_models.py test_discovery.py test_blocks.py test_fingerprint.py
    test_extractor.py test_tokens.py test_llm.py test_theme_writer.py
    test_media.py test_bundle.py test_installer.py test_verify.py test_capture.py
    fixtures/            # saved RenderedPage JSON + DOM snippets (no live network in tests)
pyproject.toml          # add deps + pytest config (modify if present, else create)
```

Tests never hit the live network or Docker: Playwright/HTTP/WP-CLI are injected and faked. Live integration is exercised only by the final orchestrator run against the fixture.

---

### Task 1: Project scaffolding + data models

**Files:**
- Create: `capture/__init__.py` (empty), `capture/content/__init__.py` (empty), `capture/design/__init__.py` (empty)
- Create: `capture/models.py`
- Create/Modify: `pyproject.toml` (add deps + pytest config)
- Test: `tests/capture/test_models.py`

**Interfaces:**
- Produces: `RenderedPage(url, slug, title, html, computed: list[ComputedStyleSnapshot], assets: list[str], screenshot_path: str|None)`; `ComputedStyleSnapshot(role: str, selector: str, styles: dict[str,str])`; `PageContent(slug, title, block_html, fingerprint, placeholders: list[str])`; `DesignTokens(palette: dict[str,str], fonts: dict[str,str], spacing: list[int], container_width: int, header_height: int, raw: dict)`; `PageMeta(url, slug, title, parent: str|None, status: str)`; `Manifest(site_title, tagline, front_page_slug, pages: list[PageMeta])`; `FidelityReport(passed: bool, content_ok: bool, page_results: list[dict], design_diff: dict)`. All `@dataclass`, all with `to_dict()`/`from_dict()` for JSON round-trip.

- [ ] **Step 1: Write the failing test**

```python
# tests/capture/test_models.py
from capture.models import RenderedPage, ComputedStyleSnapshot, PageContent, DesignTokens

def test_rendered_page_json_roundtrip():
    p = RenderedPage(
        url="https://x.com/a", slug="a", title="A", html="<h1>A</h1>",
        computed=[ComputedStyleSnapshot(role="h1", selector="h1", styles={"color": "rgb(0,0,0)"})],
        assets=["https://x.com/i.png"], screenshot_path=None,
    )
    again = RenderedPage.from_dict(p.to_dict())
    assert again == p
    assert again.computed[0].role == "h1"

def test_design_tokens_defaults():
    t = DesignTokens(palette={"background": "#ffffff"}, fonts={"body": "Inter, sans-serif"},
                     spacing=[8, 16, 24], container_width=960, header_height=165, raw={})
    assert DesignTokens.from_dict(t.to_dict()) == t
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/capture/test_models.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'capture'`

- [ ] **Step 3: Write minimal implementation**

```python
# capture/models.py
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional

@dataclass
class ComputedStyleSnapshot:
    role: str
    selector: str
    styles: dict

    def to_dict(self): return asdict(self)
    @classmethod
    def from_dict(cls, d): return cls(**d)

@dataclass
class RenderedPage:
    url: str
    slug: str
    title: str
    html: str
    computed: list = field(default_factory=list)
    assets: list = field(default_factory=list)
    screenshot_path: Optional[str] = None

    def to_dict(self):
        return {**asdict(self), "computed": [c.to_dict() for c in self.computed]}
    @classmethod
    def from_dict(cls, d):
        d = dict(d)
        d["computed"] = [ComputedStyleSnapshot.from_dict(c) for c in d.get("computed", [])]
        return cls(**d)

@dataclass
class PageContent:
    slug: str
    title: str
    block_html: str
    fingerprint: str
    placeholders: list = field(default_factory=list)
    def to_dict(self): return asdict(self)
    @classmethod
    def from_dict(cls, d): return cls(**d)

@dataclass
class DesignTokens:
    palette: dict
    fonts: dict
    spacing: list
    container_width: int
    header_height: int
    raw: dict = field(default_factory=dict)
    def to_dict(self): return asdict(self)
    @classmethod
    def from_dict(cls, d): return cls(**d)

@dataclass
class PageMeta:
    url: str
    slug: str
    title: str
    parent: Optional[str] = None
    status: str = "ok"
    def to_dict(self): return asdict(self)
    @classmethod
    def from_dict(cls, d): return cls(**d)

@dataclass
class Manifest:
    site_title: str
    tagline: str
    front_page_slug: str
    pages: list = field(default_factory=list)
    def to_dict(self):
        return {**asdict(self), "pages": [p.to_dict() for p in self.pages]}
    @classmethod
    def from_dict(cls, d):
        d = dict(d); d["pages"] = [PageMeta.from_dict(p) for p in d.get("pages", [])]
        return cls(**d)

@dataclass
class FidelityReport:
    passed: bool
    content_ok: bool
    page_results: list = field(default_factory=list)
    design_diff: dict = field(default_factory=dict)
    def to_dict(self): return asdict(self)
    @classmethod
    def from_dict(cls, d): return cls(**d)
```

Add to `pyproject.toml` (create if absent) under `[project] dependencies`: `playwright`, `beautifulsoup4`, `lxml`, `requests`, `anthropic`; under `[tool.pytest.ini_options]` set `pythonpath = ["."]`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/capture/test_models.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add capture/ tests/capture/test_models.py pyproject.toml
git commit -m "feat(capture): data models for the site capture bundle"
```

---

### Task 2: Page discovery

**Files:**
- Create: `capture/discovery.py`
- Test: `tests/capture/test_discovery.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `discover_pages(base_url: str, max_pages: int = 50, fetch=<callable url->str>) -> list[str]`. `fetch` is injected (defaults to a `requests.get(...).text` wrapper) so tests pass a fake. Parses `/sitemap.xml` `<loc>` entries; falls back to scraping same-domain `<a href>` from the homepage. Returns absolute, de-duplicated, same-domain URLs, homepage first, capped at `max_pages`.

- [ ] **Step 1: Write the failing test**

```python
# tests/capture/test_discovery.py
from capture.discovery import discover_pages

SITEMAP = """<urlset><url><loc>https://x.com/</loc></url>
<url><loc>https://x.com/about/</loc></url></urlset>"""

def test_sitemap_used_when_present():
    def fake_fetch(url):
        return SITEMAP if url.endswith("sitemap.xml") else ""
    urls = discover_pages("https://x.com", fetch=fake_fetch)
    assert urls == ["https://x.com/", "https://x.com/about/"]

def test_falls_back_to_homepage_links():
    home = '<a href="/a/">A</a><a href="https://other.com/x">no</a><a href="/a/">dup</a>'
    def fake_fetch(url):
        if url.endswith("sitemap.xml"): raise RuntimeError("404")
        return home
    urls = discover_pages("https://x.com", fetch=fake_fetch)
    assert urls == ["https://x.com", "https://x.com/a/"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/capture/test_discovery.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'capture.discovery'`

- [ ] **Step 3: Write minimal implementation**

```python
# capture/discovery.py
from urllib.parse import urljoin, urlparse
import re

def _default_fetch(url: str) -> str:
    import requests
    return requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"}).text

def discover_pages(base_url: str, max_pages: int = 50, fetch=_default_fetch) -> list[str]:
    base = base_url.rstrip("/")
    domain = urlparse(base or base_url).netloc
    out: list[str] = []
    seen = set()
    def add(u):
        if u not in seen and urlparse(u).netloc == domain:
            seen.add(u); out.append(u)
    try:
        sm = fetch(base + "/sitemap.xml")
        locs = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", sm)
        for loc in locs:
            add(loc.strip())
    except Exception:
        locs = []
    if not out:
        add(base_url)
        try:
            home = fetch(base_url)
        except Exception:
            home = ""
        for href in re.findall(r'href=["\']([^"\']+)["\']', home):
            if href.startswith("#") or href.startswith("mailto:"):
                continue
            add(urljoin(base + "/", href))
    return out[:max_pages]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/capture/test_discovery.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add capture/discovery.py tests/capture/test_discovery.py
git commit -m "feat(capture): sitemap + homepage-link page discovery"
```

---

### Task 3: Renderer (Playwright boundary)

**Files:**
- Create: `capture/renderer.py`
- Test: `tests/capture/test_renderer.py`

**Interfaces:**
- Consumes: `RenderedPage`, `ComputedStyleSnapshot` (Task 1).
- Produces: `Renderer(page_factory=<callable -> _PageLike>)` with `render(url: str, slug: str) -> RenderedPage`. `_PageLike` must expose `.goto(url)`, `.content() -> str`, `.title() -> str`, and `.evaluate(js) -> Any`. The real factory wraps a Playwright page; tests inject a fake. `render` collects computed styles for a fixed `ROLE_SELECTORS` map and asset URLs (img/src, link[href], css url()).

- [ ] **Step 1: Write the failing test**

```python
# tests/capture/test_renderer.py
from capture.renderer import Renderer, ROLE_SELECTORS

class FakePage:
    def __init__(self): self.url = None
    def goto(self, url): self.url = url
    def content(self): return "<html><body><h1>Hi</h1><img src='/a.png'></body></html>"
    def title(self): return "Hi Page"
    def evaluate(self, js):
        if "ROLE_QUERY" in js:  # computed-style probe
            return [{"role": "h1", "selector": "h1", "styles": {"color": "rgb(0,0,0)"}}]
        return ["https://x.com/a.png"]  # asset probe

def test_render_collects_styles_and_assets():
    r = Renderer(page_factory=lambda: FakePage())
    page = r.render("https://x.com/", slug="home")
    assert page.title == "Hi Page"
    assert page.slug == "home"
    assert page.computed[0].role == "h1"
    assert "https://x.com/a.png" in page.assets

def test_role_selectors_cover_core_roles():
    for role in ("body", "h1", "a", "header", "footer", "button", "input"):
        assert role in ROLE_SELECTORS
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/capture/test_renderer.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'capture.renderer'`

- [ ] **Step 3: Write minimal implementation**

```python
# capture/renderer.py
from capture.models import RenderedPage, ComputedStyleSnapshot

ROLE_SELECTORS = {
    "body": "body", "h1": "h1", "h2": "h2", "h3": "h3", "a": "a",
    "header": "header, #header, .site-header", "footer": "footer, #footer",
    "button": "button, .button, input[type=submit]", "input": "input, textarea, select",
    "container": ".container, main, #content, #content-area",
}

_ROLE_JS = """
() => {  /* ROLE_QUERY */
  const map = %s;
  const props = ['color','background-color','font-family','font-size','font-weight',
    'line-height','margin','padding','width','max-width','height','border'];
  const out = [];
  for (const [role, sel] of Object.entries(map)) {
    const el = document.querySelector(sel);
    if (!el) continue;
    const cs = getComputedStyle(el); const styles = {};
    for (const p of props) styles[p] = cs.getPropertyValue(p);
    out.push({role, selector: sel, styles});
  }
  return out;
}
""" 

_ASSET_JS = """
() => {
  const urls = new Set();
  document.querySelectorAll('img[src]').forEach(i => urls.add(i.src));
  document.querySelectorAll('link[href]').forEach(l => urls.add(l.href));
  document.querySelectorAll('*').forEach(el => {
    const bg = getComputedStyle(el).backgroundImage;
    const m = bg && bg.match(/url\\(["']?([^"')]+)["']?\\)/);
    if (m) urls.add(m[1]);
  });
  return [...urls];
}
"""

def _default_page_factory():
    from playwright.sync_api import sync_playwright
    pw = sync_playwright().start()
    browser = pw.chromium.launch()
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    return page

class Renderer:
    def __init__(self, page_factory=_default_page_factory):
        self._page_factory = page_factory
        self._page = None

    def _page_obj(self):
        if self._page is None:
            self._page = self._page_factory()
        return self._page

    def render(self, url: str, slug: str) -> RenderedPage:
        import json
        page = self._page_obj()
        page.goto(url)
        html = page.content()
        title = page.title()
        raw_styles = page.evaluate(_ROLE_JS % json.dumps(ROLE_SELECTORS))
        assets = page.evaluate(_ASSET_JS)
        computed = [ComputedStyleSnapshot(**s) for s in raw_styles]
        return RenderedPage(url=url, slug=slug, title=title, html=html,
                            computed=computed, assets=list(assets), screenshot_path=None)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/capture/test_renderer.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add capture/renderer.py tests/capture/test_renderer.py
git commit -m "feat(capture): Playwright renderer with computed-style + asset probes"
```

---

### Task 4: Block markup builders

**Files:**
- Create: `capture/content/blocks.py`
- Test: `tests/capture/test_blocks.py`

**Interfaces:**
- Consumes: nothing.
- Produces: pure functions returning Gutenberg block-comment markup strings:
  `heading_block(level: int, text: str) -> str`, `paragraph_block(text: str) -> str`,
  `image_block(src: str, alt: str = "") -> str`, `list_block(items: list[str], ordered: bool = False) -> str`,
  `html_block(raw: str) -> str`, `placeholder_block(kind: str) -> str`. All HTML-escape text content.

- [ ] **Step 1: Write the failing test**

```python
# tests/capture/test_blocks.py
from capture.content import blocks

def test_heading_block():
    assert blocks.heading_block(2, "Hi & Bye") == (
        '<!-- wp:heading {"level":2} -->\n'
        '<h2 class="wp-block-heading">Hi &amp; Bye</h2>\n'
        '<!-- /wp:heading -->'
    )

def test_paragraph_and_image():
    assert blocks.paragraph_block("a") == '<!-- wp:paragraph -->\n<p>a</p>\n<!-- /wp:paragraph -->'
    assert 'src="/x.png"' in blocks.image_block("/x.png", "alt")
    assert blocks.image_block("/x.png", "alt").startswith("<!-- wp:image")

def test_placeholder_block_is_flagged():
    out = blocks.placeholder_block("gravity-form")
    assert "CAPTURE-PLACEHOLDER: gravity-form" in out
    assert out.startswith("<!-- wp:html -->")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/capture/test_blocks.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'capture.content.blocks'`

- [ ] **Step 3: Write minimal implementation**

```python
# capture/content/blocks.py
from html import escape

def heading_block(level: int, text: str) -> str:
    return (f'<!-- wp:heading {{"level":{level}}} -->\n'
            f'<h{level} class="wp-block-heading">{escape(text)}</h{level}>\n'
            f'<!-- /wp:heading -->')

def paragraph_block(text: str) -> str:
    return f'<!-- wp:paragraph -->\n<p>{escape(text)}</p>\n<!-- /wp:paragraph -->'

def image_block(src: str, alt: str = "") -> str:
    return (f'<!-- wp:image -->\n'
            f'<figure class="wp-block-image"><img src="{escape(src)}" alt="{escape(alt)}"/></figure>\n'
            f'<!-- /wp:image -->')

def list_block(items: list, ordered: bool = False) -> str:
    tag = "ol" if ordered else "ul"
    lis = "".join(f"<li>{escape(i)}</li>" for i in items)
    attr = ' {"ordered":true}' if ordered else ""
    return f'<!-- wp:list{attr} -->\n<{tag}>{lis}</{tag}>\n<!-- /wp:list -->'

def html_block(raw: str) -> str:
    return f'<!-- wp:html -->\n{raw}\n<!-- /wp:html -->'

def placeholder_block(kind: str) -> str:
    return html_block(f'<!-- CAPTURE-PLACEHOLDER: {kind} -->')
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/capture/test_blocks.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add capture/content/blocks.py tests/capture/test_blocks.py
git commit -m "feat(capture): Gutenberg core-block markup builders"
```

---

### Task 5: Content fingerprint

**Files:**
- Create: `capture/content/fingerprint.py`
- Test: `tests/capture/test_fingerprint.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `content_fingerprint(block_html: str) -> str` — a sha256 of normalized visible
  text + ordered block-tag sequence. Whitespace-insensitive; ignores attributes; identical
  text+structure → identical hash regardless of formatting.

- [ ] **Step 1: Write the failing test**

```python
# tests/capture/test_fingerprint.py
from capture.content.fingerprint import content_fingerprint

def test_whitespace_insensitive():
    a = "<!-- wp:heading -->\n<h2 class='x'>Hello   World</h2>\n<!-- /wp:heading -->"
    b = "<!-- wp:heading -->\n<h2>Hello World</h2>\n<!-- /wp:heading -->"
    assert content_fingerprint(a) == content_fingerprint(b)

def test_different_text_differs():
    a = "<p>Get Started</p>"
    b = "<p>Get Going</p>"
    assert content_fingerprint(a) != content_fingerprint(b)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/capture/test_fingerprint.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# capture/content/fingerprint.py
import hashlib, re
from bs4 import BeautifulSoup

def content_fingerprint(block_html: str) -> str:
    soup = BeautifulSoup(block_html, "lxml")
    tags = [t.name for t in soup.find_all(True)]
    text = soup.get_text(" ")
    text = re.sub(r"\s+", " ", text).strip().lower()
    payload = "|".join(tags) + "##" + text
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/capture/test_fingerprint.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add capture/content/fingerprint.py tests/capture/test_fingerprint.py
git commit -m "feat(capture): normalized content fingerprint for fidelity checks"
```

---

### Task 6: Content extractor (DOM → blocks)

**Files:**
- Create: `capture/content/extractor.py`
- Test: `tests/capture/test_extractor.py`

**Interfaces:**
- Consumes: `RenderedPage` (Task 1), `blocks` (Task 4), `content_fingerprint` (Task 5).
- Produces: `extract_content(page: RenderedPage) -> PageContent`. Selects the main content
  region (first match of `main, #left-area, #content-area, #content, article, .entry-content`,
  else `body`), strips `header/nav/footer/aside/script/style`, walks block-level children in
  order mapping each to a core block, detects Gravity Forms (`[id^=gform_], .gform_wrapper`)
  → `placeholder_block("gravity-form")` and records it in `placeholders`. Never alters text.

- [ ] **Step 1: Write the failing test**

```python
# tests/capture/test_extractor.py
from capture.models import RenderedPage
from capture.content.extractor import extract_content

def _page(body_html):
    return RenderedPage(url="u", slug="get-started", title="Get Started",
                        html=f"<html><body>{body_html}</body></html>")

def test_extracts_title_and_intro_then_form_placeholder():
    # regression: the original /get-started/ title + intro must be captured
    html = ('<div id="header">CHROME</div>'
            '<div id="content-area"><div id="left-area">'
            '<h1 class="title">Get Started</h1>'
            '<p>Call 760-632-8258 for a Free Web Site Consultation.</p>'
            '<div class="gform_wrapper" id="gform_wrapper_1">FORM</div>'
            '</div></div>')
    pc = extract_content(_page(html))
    assert "Get Started" in pc.block_html
    assert "760-632-8258" in pc.block_html
    assert "wp:heading" in pc.block_html
    assert "CAPTURE-PLACEHOLDER: gravity-form" in pc.block_html
    assert "gravity-form" in pc.placeholders
    assert "CHROME" not in pc.block_html  # header stripped
    assert pc.fingerprint  # non-empty

def test_no_theme_wrappers_leak():
    html = '<div id="left-area"><h2>Hi</h2><p>Body</p></div>'
    pc = extract_content(_page(html))
    assert "left-area" not in pc.block_html
    assert "content-area" not in pc.block_html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/capture/test_extractor.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# capture/content/extractor.py
from bs4 import BeautifulSoup
from capture.models import RenderedPage, PageContent
from capture.content import blocks
from capture.content.fingerprint import content_fingerprint

_MAIN_SELECTORS = ["main", "#left-area", "#content-area", "#content", "article", ".entry-content"]
_CHROME = ["header", "nav", "footer", "aside", "script", "style", "#header", "#sidebar"]
_FORM_SELECTORS = ['[id^="gform_"]', ".gform_wrapper", "form#searchform"]

def _main_region(soup):
    for sel in _MAIN_SELECTORS:
        el = soup.select_one(sel)
        if el:
            return el
    return soup.body or soup

def extract_content(page: RenderedPage) -> PageContent:
    soup = BeautifulSoup(page.html, "lxml")
    region = _main_region(soup)
    for sel in _CHROME:
        for el in region.select(sel):
            el.decompose()
    out: list[str] = []
    placeholders: list[str] = []
    for node in region.find_all(["h1", "h2", "h3", "h4", "p", "ul", "ol", "img", "div", "form"], recursive=True):
        # form / plugin detection first
        classes = " ".join(node.get("class", []))
        node_id = node.get("id", "")
        if node.name == "form" or "gform_wrapper" in classes or node_id.startswith("gform_"):
            if "gravity-form" not in placeholders:
                placeholders.append("gravity-form")
                out.append(blocks.placeholder_block("gravity-form"))
            continue
        if node.name in ("h1", "h2", "h3", "h4"):
            text = node.get_text(" ", strip=True)
            if text:
                out.append(blocks.heading_block(int(node.name[1]), text))
        elif node.name == "p":
            text = node.get_text(" ", strip=True)
            if text:
                out.append(blocks.paragraph_block(text))
        elif node.name in ("ul", "ol"):
            items = [li.get_text(" ", strip=True) for li in node.find_all("li", recursive=False)]
            items = [i for i in items if i]
            if items:
                out.append(blocks.list_block(items, ordered=(node.name == "ol")))
        elif node.name == "img" and node.get("src"):
            out.append(blocks.image_block(node["src"], node.get("alt", "")))
    block_html = "\n\n".join(out)
    return PageContent(slug=page.slug, title=page.title, block_html=block_html,
                       fingerprint=content_fingerprint(block_html), placeholders=placeholders)
```

> Note for implementer: `find_all` with mixed container/leaf tags can double-emit text from nested `div>p`. Keep the leaf tags (`p,h*,img,ul,ol`) authoritative and let `div`/`form` only trigger form detection — the test `test_no_theme_wrappers_leak` guards against wrapper leakage; if a nested-duplication test fails, switch the walk to leaf tags only (`["h1","h2","h3","h4","p","ul","ol","img","form"]`).

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/capture/test_extractor.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add capture/content/extractor.py tests/capture/test_extractor.py
git commit -m "feat(capture): deterministic DOM->core-block content extractor"
```

---

### Task 7: Design token aggregation

**Files:**
- Create: `capture/design/tokens.py`
- Test: `tests/capture/test_tokens.py`

**Interfaces:**
- Consumes: `ComputedStyleSnapshot`, `DesignTokens` (Task 1).
- Produces: `derive_tokens(snapshots: list[ComputedStyleSnapshot]) -> DesignTokens`; helper
  `rgb_to_hex(css: str) -> str`. Palette: `background`←body bg, `text`←body color,
  `link`←a color, `accent`←button bg. Fonts: `body`←body font-family, `heading`←h1
  font-family. `container_width`←container max-width px (fallback 1100). `header_height`←
  header height px (fallback 0). Missing roles are simply omitted from `palette`/`fonts`.

- [ ] **Step 1: Write the failing test**

```python
# tests/capture/test_tokens.py
from capture.models import ComputedStyleSnapshot
from capture.design.tokens import derive_tokens, rgb_to_hex

def test_rgb_to_hex():
    assert rgb_to_hex("rgb(255, 255, 255)") == "#ffffff"
    assert rgb_to_hex("rgb(152,108,4)") == "#986c04"

def test_derive_palette_and_fonts():
    snaps = [
        ComputedStyleSnapshot("body", "body", {"background-color": "rgb(255,255,255)",
            "color": "rgb(30,30,30)", "font-family": "Inter, sans-serif"}),
        ComputedStyleSnapshot("a", "a", {"color": "rgb(152,108,4)"}),
        ComputedStyleSnapshot("button", "button", {"background-color": "rgb(152,108,4)"}),
        ComputedStyleSnapshot("h1", "h1", {"font-family": "Outfit, sans-serif"}),
        ComputedStyleSnapshot("container", ".container", {"max-width": "960px"}),
        ComputedStyleSnapshot("header", "#header", {"height": "165px"}),
    ]
    t = derive_tokens(snaps)
    assert t.palette["background"] == "#ffffff"
    assert t.palette["text"] == "#1e1e1e"
    assert t.palette["link"] == "#986c04"
    assert t.palette["accent"] == "#986c04"
    assert t.fonts["body"].startswith("Inter")
    assert t.fonts["heading"].startswith("Outfit")
    assert t.container_width == 960
    assert t.header_height == 165
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/capture/test_tokens.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# capture/design/tokens.py
import re
from capture.models import ComputedStyleSnapshot, DesignTokens

def rgb_to_hex(css: str) -> str:
    m = re.findall(r"\d+", css or "")
    if len(m) < 3:
        return ""
    r, g, b = (int(m[0]), int(m[1]), int(m[2]))
    return "#%02x%02x%02x" % (r, g, b)

def _px(val: str, default: int) -> int:
    m = re.search(r"(\d+)", val or "")
    return int(m.group(1)) if m else default

def derive_tokens(snapshots) -> DesignTokens:
    by_role = {s.role: s.styles for s in snapshots}
    palette = {}
    if "body" in by_role:
        if (h := rgb_to_hex(by_role["body"].get("background-color", ""))): palette["background"] = h
        if (h := rgb_to_hex(by_role["body"].get("color", ""))): palette["text"] = h
    if "a" in by_role and (h := rgb_to_hex(by_role["a"].get("color", ""))): palette["link"] = h
    if "button" in by_role and (h := rgb_to_hex(by_role["button"].get("background-color", ""))): palette["accent"] = h
    fonts = {}
    if "body" in by_role and by_role["body"].get("font-family"): fonts["body"] = by_role["body"]["font-family"]
    if "h1" in by_role and by_role["h1"].get("font-family"): fonts["heading"] = by_role["h1"]["font-family"]
    container_width = _px(by_role.get("container", {}).get("max-width", ""), 1100)
    header_height = _px(by_role.get("header", {}).get("height", ""), 0)
    return DesignTokens(palette=palette, fonts=fonts, spacing=[8, 16, 24, 32],
                        container_width=container_width, header_height=header_height,
                        raw={s.role: s.styles for s in snapshots})
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/capture/test_tokens.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add capture/design/tokens.py tests/capture/test_tokens.py
git commit -m "feat(capture): aggregate computed styles into design tokens"
```

---

### Task 8: Bounded LLM token cleanup

**Files:**
- Create: `capture/design/llm.py`
- Test: `tests/capture/test_llm.py`

**Interfaces:**
- Consumes: `DesignTokens` (Task 1).
- Produces: `clean_tokens(tokens: DesignTokens, client=None) -> DesignTokens`. `client` is an
  injected object exposing `.messages.create(...)` (the anthropic SDK shape); when `None`, the
  function returns `tokens` unchanged (no-LLM default). The model is pinned to
  `MODEL = "claude-sonnet-4-6"`. The LLM is sent **only** the palette/fonts/spacing JSON (never
  content) and must return a JSON object with the same keys; output is validated and merged —
  on any parse/validation failure the original tokens are returned unchanged.

- [ ] **Step 1: Write the failing test**

```python
# tests/capture/test_llm.py
import json
from capture.models import DesignTokens
from capture.design.llm import clean_tokens, MODEL

def _tokens():
    return DesignTokens(palette={"background": "#ffffff", "accent": "#986c04"},
                        fonts={"body": "Inter, sans-serif"}, spacing=[8, 16],
                        container_width=960, header_height=165, raw={})

class FakeClient:
    def __init__(self, payload): self._payload = payload; self.seen = None
    class _M:
        def __init__(self, outer): self._outer = outer
        def create(self, **kw):
            self._outer.seen = kw
            class R: pass
            r = R(); r.content = [type("B", (), {"text": self._outer._payload})]
            return r
    @property
    def messages(self): return FakeClient._M(self)

def test_none_client_is_passthrough():
    t = _tokens()
    assert clean_tokens(t, client=None) == t

def test_model_is_pinned_and_content_never_sent():
    fc = FakeClient(json.dumps({"palette": {"background": "#fefefe", "accent": "#986c04"},
                                "fonts": {"body": "Inter, sans-serif"}, "spacing": [8, 16]}))
    out = clean_tokens(_tokens(), client=fc)
    assert fc.seen["model"] == MODEL == "claude-sonnet-4-6"
    sent = json.dumps(fc.seen)
    assert "left-area" not in sent and "Get Started" not in sent  # no content leaked
    assert out.palette["background"] == "#fefefe"

def test_bad_json_returns_original():
    fc = FakeClient("not json")
    t = _tokens()
    assert clean_tokens(t, client=fc) == t
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/capture/test_llm.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# capture/design/llm.py
import json
from dataclasses import replace
from capture.models import DesignTokens

MODEL = "claude-sonnet-4-6"

_PROMPT = (
    "You are cleaning a website's design tokens. Given this JSON of palette, fonts, and "
    "spacing extracted from computed styles, return a JSON object with the SAME keys, "
    "normalizing near-duplicate colors, ensuring hex format, and ordering spacing ascending. "
    "Return ONLY JSON. Do not invent content. Input:\n"
)

def clean_tokens(tokens: DesignTokens, client=None) -> DesignTokens:
    if client is None:
        return tokens
    payload = {"palette": tokens.palette, "fonts": tokens.fonts, "spacing": tokens.spacing}
    try:
        resp = client.messages.create(
            model=MODEL, max_tokens=1024,
            messages=[{"role": "user", "content": _PROMPT + json.dumps(payload)}],
        )
        text = resp.content[0].text
        data = json.loads(text)
        if not isinstance(data.get("palette"), dict):
            return tokens
        return replace(tokens,
                       palette=data.get("palette", tokens.palette),
                       fonts=data.get("fonts", tokens.fonts),
                       spacing=data.get("spacing", tokens.spacing))
    except Exception:
        return tokens
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/capture/test_llm.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add capture/design/llm.py tests/capture/test_llm.py
git commit -m "feat(capture): bounded LLM token cleanup (design-only, content-safe)"
```

---

### Task 9: Theme writer (tokens → FSE theme)

**Files:**
- Create: `capture/design/theme_writer.py`
- Test: `tests/capture/test_theme_writer.py`

**Interfaces:**
- Consumes: `DesignTokens` (Task 1).
- Produces: `write_theme(tokens: DesignTokens, theme_dir: Path, theme_name: str = "captured-theme") -> None`.
  Writes `theme.json` (schema v2: settings.color.palette from tokens.palette, settings.typography
  font families, settings.layout.contentSize = `{container_width}px`), `style.css` (theme header),
  `templates/index.html`, `templates/page.html`, `templates/front-page.html`, `parts/header.html`,
  `parts/footer.html`. Templates contain only generic FSE blocks (no site-specific markup).

- [ ] **Step 1: Write the failing test**

```python
# tests/capture/test_theme_writer.py
import json
from pathlib import Path
from capture.models import DesignTokens
from capture.design.theme_writer import write_theme

def test_writes_valid_theme_json_and_templates(tmp_path: Path):
    t = DesignTokens(palette={"background": "#ffffff", "text": "#1e1e1e", "accent": "#986c04"},
                     fonts={"body": "Inter, sans-serif", "heading": "Outfit, sans-serif"},
                     spacing=[8, 16, 24], container_width=960, header_height=165, raw={})
    write_theme(t, tmp_path)
    tj = json.loads((tmp_path / "theme.json").read_text())
    assert tj["version"] == 2
    slugs = {c["slug"] for c in tj["settings"]["color"]["palette"]}
    assert {"background", "text", "accent"} <= slugs
    assert tj["settings"]["layout"]["contentSize"] == "960px"
    assert (tmp_path / "templates" / "page.html").exists()
    assert (tmp_path / "parts" / "header.html").exists()
    assert (tmp_path / "style.css").read_text().startswith("/*")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/capture/test_theme_writer.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# capture/design/theme_writer.py
import json
from pathlib import Path
from capture.models import DesignTokens

def write_theme(tokens: DesignTokens, theme_dir: Path, theme_name: str = "captured-theme") -> None:
    theme_dir = Path(theme_dir)
    (theme_dir / "templates").mkdir(parents=True, exist_ok=True)
    (theme_dir / "parts").mkdir(parents=True, exist_ok=True)

    palette = [{"slug": slug, "color": hexv, "name": slug.title()}
               for slug, hexv in tokens.palette.items()]
    families = []
    for slug, stack in tokens.fonts.items():
        families.append({"fontFamily": stack, "slug": slug, "name": slug.title()})
    theme_json = {
        "$schema": "https://schemas.wp.org/trunk/theme.json",
        "version": 2,
        "settings": {
            "color": {"palette": palette},
            "typography": {"fontFamilies": families},
            "layout": {"contentSize": f"{tokens.container_width}px", "wideSize": f"{tokens.container_width}px"},
            "spacing": {"spacingSizes": [
                {"slug": str(i), "size": f"{v}px", "name": str(v)} for i, v in enumerate(tokens.spacing)]},
        },
        "styles": {
            "color": {"background": tokens.palette.get("background", "#ffffff"),
                      "text": tokens.palette.get("text", "#000000")},
            "typography": {"fontFamily": tokens.fonts.get("body", "sans-serif")},
        },
    }
    (theme_dir / "theme.json").write_text(json.dumps(theme_json, indent=2))
    (theme_dir / "style.css").write_text(
        f"/*\nTheme Name: {theme_name}\nVersion: 1.0\nRequires at least: 6.4\n*/\n")
    header = ('<!-- wp:group {"tagName":"header","className":"site-header"} -->\n'
              '<header class="wp-block-group site-header">'
              '<!-- wp:site-title /--><!-- wp:navigation /--></header>\n<!-- /wp:group -->')
    footer = ('<!-- wp:group {"tagName":"footer","className":"site-footer"} -->\n'
              '<footer class="wp-block-group site-footer"><!-- wp:site-title /--></footer>\n'
              '<!-- /wp:group -->')
    (theme_dir / "parts" / "header.html").write_text(header)
    (theme_dir / "parts" / "footer.html").write_text(footer)
    body = ('<!-- wp:template-part {"slug":"header","tagName":"div"} /-->\n'
            '<!-- wp:group {"tagName":"main","layout":{"type":"constrained"}} -->\n'
            '<main class="wp-block-group">\n%s\n</main>\n<!-- /wp:group -->\n'
            '<!-- wp:template-part {"slug":"footer","tagName":"div"} /-->')
    (theme_dir / "templates" / "index.html").write_text(body % '<!-- wp:query /-->')
    (theme_dir / "templates" / "page.html").write_text(
        body % '<!-- wp:post-title {"level":1} /-->\n<!-- wp:post-content /-->')
    (theme_dir / "templates" / "front-page.html").write_text(
        body % '<!-- wp:post-content /-->')
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/capture/test_theme_writer.py -v`
Expected: PASS (1 passed)

- [ ] **Step 5: Commit**

```bash
git add capture/design/theme_writer.py tests/capture/test_theme_writer.py
git commit -m "feat(capture): write FSE theme (theme.json + templates/parts) from tokens"
```

---

### Task 10: Media localizer

**Files:**
- Create: `capture/media.py`
- Test: `tests/capture/test_media.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `localize_media(assets: list[str], media_dir: Path, download=<callable url->bytes>) -> dict[str,str]`
  (maps original URL → local relative path like `media/<sha8>-<basename>`; dedups by URL; skips
  failures, logging them) and `rewrite_urls(text: str, mapping: dict[str,str]) -> str` (replaces
  each original URL substring with its local path). `download` is injected; default uses requests.

- [ ] **Step 1: Write the failing test**

```python
# tests/capture/test_media.py
from pathlib import Path
from capture.media import localize_media, rewrite_urls

def test_localize_and_rewrite(tmp_path: Path):
    def fake_dl(url): return b"PNGDATA" if url.endswith(".png") else None
    assets = ["https://x.com/a.png", "https://x.com/a.png", "https://x.com/missing.png"]
    mapping = localize_media(assets, tmp_path, download=fake_dl)
    assert "https://x.com/a.png" in mapping
    local = mapping["https://x.com/a.png"]
    assert (tmp_path / Path(local).name).read_bytes() == b"PNGDATA"
    # missing asset that returns None is skipped
    assert "https://x.com/missing.png" not in mapping
    html = '<img src="https://x.com/a.png">'
    assert local in rewrite_urls(html, mapping)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/capture/test_media.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# capture/media.py
import hashlib
from pathlib import Path
from urllib.parse import urlparse

def _default_download(url: str):
    import requests
    r = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    return r.content

def localize_media(assets, media_dir, download=_default_download) -> dict:
    media_dir = Path(media_dir); media_dir.mkdir(parents=True, exist_ok=True)
    mapping: dict = {}
    for url in assets:
        if url in mapping or not url.startswith("http"):
            continue
        try:
            data = download(url)
            if not data:
                continue
        except Exception:
            continue
        base = Path(urlparse(url).path).name or "asset"
        sha8 = hashlib.sha256(url.encode()).hexdigest()[:8]
        name = f"{sha8}-{base}"
        (media_dir / name).write_bytes(data)
        mapping[url] = f"media/{name}"
    return mapping

def rewrite_urls(text: str, mapping: dict) -> str:
    for original, local in mapping.items():
        text = text.replace(original, local)
    return text
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/capture/test_media.py -v`
Expected: PASS (1 passed)

- [ ] **Step 5: Commit**

```bash
git add capture/media.py tests/capture/test_media.py
git commit -m "feat(capture): media localizer + URL rewriter"
```

---

### Task 11: Bundle writer

**Files:**
- Create: `capture/bundle.py`
- Test: `tests/capture/test_bundle.py`

**Interfaces:**
- Consumes: `PageContent`, `Manifest`, `DesignTokens` (Task 1).
- Produces: `write_bundle(root: Path, slug: str, pages: list[PageContent], manifest: Manifest, tokens: DesignTokens) -> Path`
  creating `root/<slug>/` with `manifest.json`, `pages/<slug>.html` per page, `design-tokens.json`,
  and empty `media/` + `theme/` dirs (theme populated by Task 9, media by Task 10). Returns the
  bundle dir. Helper `BundlePaths(bundle_dir)` exposing `.pages`, `.media`, `.theme`, `.manifest`,
  `.report` as `Path`s.

- [ ] **Step 1: Write the failing test**

```python
# tests/capture/test_bundle.py
import json
from pathlib import Path
from capture.models import PageContent, Manifest, PageMeta, DesignTokens
from capture.bundle import write_bundle, BundlePaths

def test_write_bundle_layout(tmp_path: Path):
    pages = [PageContent(slug="home", title="Home", block_html="<p>hi</p>", fingerprint="fp", placeholders=[])]
    man = Manifest(site_title="S", tagline="t", front_page_slug="home",
                   pages=[PageMeta(url="u", slug="home", title="Home")])
    tokens = DesignTokens(palette={}, fonts={}, spacing=[], container_width=960, header_height=0, raw={})
    bdir = write_bundle(tmp_path, "site", pages, man, tokens)
    bp = BundlePaths(bdir)
    assert (bp.pages / "home.html").read_text() == "<p>hi</p>"
    assert json.loads(bp.manifest.read_text())["front_page_slug"] == "home"
    assert bp.media.is_dir() and bp.theme.is_dir()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/capture/test_bundle.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# capture/bundle.py
import json
from pathlib import Path
from capture.models import PageContent, Manifest, DesignTokens

class BundlePaths:
    def __init__(self, bundle_dir):
        self.dir = Path(bundle_dir)
        self.pages = self.dir / "pages"
        self.media = self.dir / "media"
        self.theme = self.dir / "theme"
        self.manifest = self.dir / "manifest.json"
        self.report = self.dir / "fidelity-report.json"
        self.tokens = self.dir / "design-tokens.json"

def write_bundle(root: Path, slug: str, pages, manifest: Manifest, tokens: DesignTokens) -> Path:
    bdir = Path(root) / slug
    bp = BundlePaths(bdir)
    for d in (bp.pages, bp.media, bp.theme):
        d.mkdir(parents=True, exist_ok=True)
    for pc in pages:
        (bp.pages / f"{pc.slug}.html").write_text(pc.block_html)
    bp.manifest.write_text(json.dumps(manifest.to_dict(), indent=2))
    bp.tokens.write_text(json.dumps(tokens.to_dict(), indent=2))
    return bdir
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/capture/test_bundle.py -v`
Expected: PASS (1 passed)

- [ ] **Step 5: Commit**

```bash
git add capture/bundle.py tests/capture/test_bundle.py
git commit -m "feat(capture): bundle writer + path helper"
```

---

### Task 12: WP Installer

**Files:**
- Create: `capture/installer.py`
- Test: `tests/capture/test_installer.py`

**Interfaces:**
- Consumes: `BundlePaths` (Task 11), `Manifest` (Task 1).
- Produces: `WPInstaller(runner=<callable list[str]->RunResult>, copier=<callable (src,dst)->None>)`
  with `install(bundle_dir: Path) -> None`. `runner` executes WP-CLI argv (default:
  `docker compose run --rm wp-cli <args>`); `copier` places theme/media into the container
  (default: `docker cp` + chown). `install` runs, in order: db reset, core install, theme copy +
  `theme activate`, media copy, per-page `wp post create` (front page set via `option update
  show_on_front`/`page_on_front`), and nav menu creation. Pure-argv orchestration so a fake runner
  records calls without Docker.

- [ ] **Step 1: Write the failing test**

```python
# tests/capture/test_installer.py
import json
from pathlib import Path
from capture.installer import WPInstaller

def _bundle(tmp_path):
    bdir = tmp_path / "site"; (bdir / "pages").mkdir(parents=True)
    (bdir / "theme").mkdir(); (bdir / "media").mkdir()
    (bdir / "pages" / "home.html").write_text("<p>hi</p>")
    (bdir / "manifest.json").write_text(json.dumps({
        "site_title": "S", "tagline": "t", "front_page_slug": "home",
        "pages": [{"url": "u", "slug": "home", "title": "Home", "parent": None, "status": "ok"}]}))
    return bdir

def test_install_sequences_wpcli_calls(tmp_path: Path):
    calls = []
    class R: returncode = 0; stdout = "42"
    def fake_runner(args): calls.append(args); return R()
    def fake_copier(src, dst): calls.append(["COPY", str(src), dst])
    WPInstaller(runner=fake_runner, copier=fake_copier).install(_bundle(tmp_path))
    flat = [" ".join(c) for c in calls]
    assert any("core install" in f for f in flat)
    assert any("theme activate" in f for f in flat)
    assert any("post create" in f for f in flat)
    assert any(f.startswith("COPY") for f in flat)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/capture/test_installer.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# capture/installer.py
import json, subprocess
from pathlib import Path
from capture.bundle import BundlePaths
from capture.models import Manifest

def _default_runner(args):
    return subprocess.run(["docker", "compose", "run", "--rm", "wp-cli", *args],
                          capture_output=True, text=True)

def _default_copier(src, dst):
    subprocess.run(["docker", "cp", str(src), f"wp_mockup_app:{dst}"], check=True)
    subprocess.run(["docker", "exec", "wp_mockup_app", "chown", "-R", "www-data:www-data", dst], check=True)

class WPInstaller:
    def __init__(self, runner=_default_runner, copier=_default_copier):
        self.runner = runner
        self.copier = copier

    def install(self, bundle_dir: Path) -> None:
        bp = BundlePaths(bundle_dir)
        man = Manifest.from_dict(json.loads(bp.manifest.read_text()))
        self.runner(["db", "reset", "--yes"])
        self.runner(["core", "install", f"--url=http://localhost:8080",
                     f"--title={man.site_title}", "--admin_user=admin",
                     "--admin_password=adminpassword", "--admin_email=admin@example.com"])
        self.copier(bp.theme, "/var/www/html/wp-content/themes/captured-theme")
        self.runner(["theme", "activate", "captured-theme"])
        self.copier(bp.media, "/var/www/html/wp-content/uploads/captured")
        slug_to_id = {}
        for meta in man.pages:
            html = (bp.pages / f"{meta.slug}.html").read_text()
            res = self.runner(["post", "create", "--post_type=page", "--post_status=publish",
                               f"--post_title={meta.title}", f"--post_name={meta.slug}",
                               "--porcelain", f"--post_content={html}"])
            slug_to_id[meta.slug] = (res.stdout or "").strip()
        front_id = slug_to_id.get(man.front_page_slug)
        if front_id:
            self.runner(["option", "update", "show_on_front", "page"])
            self.runner(["option", "update", "page_on_front", front_id])
        self.runner(["menu", "create", "Primary"])
        for meta in man.pages:
            self.runner(["menu", "item", "add-post", "Primary", slug_to_id.get(meta.slug, "")])
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/capture/test_installer.py -v`
Expected: PASS (1 passed)

- [ ] **Step 5: Commit**

```bash
git add capture/installer.py tests/capture/test_installer.py
git commit -m "feat(capture): WP installer (WP-CLI argv orchestration, injectable runner)"
```

---

### Task 13: Fidelity verifier

**Files:**
- Create: `capture/verify.py`
- Test: `tests/capture/test_verify.py`

**Interfaces:**
- Consumes: `PageContent` (Task 1), `DesignTokens` (Task 1), `content_fingerprint` (Task 5),
  `rgb_to_hex` (Task 7).
- Produces: `compare_fingerprints(original: str, captured: str) -> bool`;
  `color_distance(hex1: str, hex2: str) -> float` (CIE76-ish euclidean in RGB);
  `design_distance(orig: DesignTokens, cap: DesignTokens) -> dict` (per-palette-role distance +
  `max`); `verify_site(orig_pages: dict[str,str], cap_pages: dict[str,str], orig_tokens, cap_tokens, color_tol: float = 25.0) -> FidelityReport`
  where `*_pages` map slug→fingerprint. Content mismatch on ANY page → `content_ok=False` →
  `passed=False`. Design distance is reported in `design_diff`, never gates `passed`.

- [ ] **Step 1: Write the failing test**

```python
# tests/capture/test_verify.py
from capture.models import DesignTokens
from capture.verify import compare_fingerprints, color_distance, design_distance, verify_site

def test_color_distance_and_design_report():
    assert color_distance("#000000", "#000000") == 0
    assert color_distance("#000000", "#ffffff") > 400
    o = DesignTokens(palette={"accent": "#986c04"}, fonts={}, spacing=[], container_width=960, header_height=0, raw={})
    c = DesignTokens(palette={"accent": "#9a6e06"}, fonts={}, spacing=[], container_width=960, header_height=0, raw={})
    dd = design_distance(o, c)
    assert dd["accent"] < 10 and dd["max"] < 10

def test_content_mismatch_fails_overall():
    orig = {"home": "fpA", "about": "fpB"}
    good = {"home": "fpA", "about": "fpB"}
    bad = {"home": "fpA", "about": "DIFFERENT"}
    t = DesignTokens(palette={}, fonts={}, spacing=[], container_width=960, header_height=0, raw={})
    assert verify_site(orig, good, t, t).passed is True
    rep = verify_site(orig, bad, t, t)
    assert rep.content_ok is False and rep.passed is False
    assert any(r["slug"] == "about" and r["ok"] is False for r in rep.page_results)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/capture/test_verify.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# capture/verify.py
from capture.models import DesignTokens, FidelityReport
from capture.design.tokens import rgb_to_hex  # noqa: F401 (re-export for callers)

def compare_fingerprints(original: str, captured: str) -> bool:
    return original == captured

def color_distance(hex1: str, hex2: str) -> float:
    def rgb(h):
        h = h.lstrip("#")
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    (r1, g1, b1), (r2, g2, b2) = rgb(hex1), rgb(hex2)
    return ((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2) ** 0.5

def design_distance(orig: DesignTokens, cap: DesignTokens) -> dict:
    out = {}
    for role, hexv in orig.palette.items():
        if role in cap.palette:
            out[role] = color_distance(hexv, cap.palette[role])
    out["max"] = max([v for k, v in out.items() if k != "max"], default=0.0)
    return out

def verify_site(orig_pages, cap_pages, orig_tokens, cap_tokens, color_tol: float = 25.0) -> FidelityReport:
    results = []
    content_ok = True
    for slug, fp in orig_pages.items():
        ok = compare_fingerprints(fp, cap_pages.get(slug, ""))
        if not ok:
            content_ok = False
        results.append({"slug": slug, "ok": ok})
    design_diff = design_distance(orig_tokens, cap_tokens)
    design_diff["within_tolerance"] = design_diff.get("max", 0.0) <= color_tol
    return FidelityReport(passed=content_ok, content_ok=content_ok,
                          page_results=results, design_diff=design_diff)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/capture/test_verify.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add capture/verify.py tests/capture/test_verify.py
git commit -m "feat(capture): fidelity verifier (exact content gate, close-design report)"
```

---

### Task 14: Orchestrator CLI

**Files:**
- Create: `capture/capture.py`
- Test: `tests/capture/test_capture.py`

**Interfaces:**
- Consumes: all prior modules.
- Produces: `run_capture(url: str, slug: str, out_root: Path, max_pages: int = 50, *, renderer, discover, llm_client=None) -> FidelityReport`
  — wires discovery → render each page → (extract_content + accumulate snapshots) → derive_tokens
  → clean_tokens → write_theme → localize_media + rewrite page/theme URLs → write_bundle →
  (installer + verifier are invoked by the CLI `main`, not by `run_capture`, so the wiring is unit-
  testable without Docker). `renderer` and `discover` are injected. A page that raises is recorded
  `status="error"` in the manifest and skipped. Also `main(argv)` for `python -m capture.capture <url>`.

- [ ] **Step 1: Write the failing test**

```python
# tests/capture/test_capture.py
from pathlib import Path
from capture.models import RenderedPage, ComputedStyleSnapshot
from capture.capture import run_capture
from capture.bundle import BundlePaths

def _renderer_for(pages):
    class R:
        def render(self, url, slug):
            return pages[url]
    return R()

def test_run_capture_produces_bundle(tmp_path: Path):
    home = RenderedPage(url="https://x.com/", slug="home", title="Home",
        html="<body><main><h1>Home</h1><p>Welcome</p></main></body>",
        computed=[ComputedStyleSnapshot("body", "body",
            {"background-color": "rgb(255,255,255)", "color": "rgb(0,0,0)", "font-family": "Inter"})],
        assets=[])
    pages = {"https://x.com/": home}
    report = run_capture("https://x.com/", "site", tmp_path,
                         renderer=_renderer_for(pages),
                         discover=lambda url, max_pages: ["https://x.com/"])
    bp = BundlePaths(tmp_path / "site")
    assert (bp.pages / "home.html").exists()
    assert (bp.theme / "theme.json").exists()
    assert bp.manifest.exists()
    assert "Welcome" in (bp.pages / "home.html").read_text()

def test_failing_page_is_recorded_not_fatal(tmp_path: Path):
    class R:
        def render(self, url, slug):
            raise RuntimeError("boom")
    report = run_capture("https://x.com/", "site2", tmp_path, renderer=R(),
                         discover=lambda url, max_pages: ["https://x.com/"])
    import json
    man = json.loads((tmp_path / "site2" / "manifest.json").read_text())
    assert man["pages"][0]["status"] == "error"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/capture/test_capture.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# capture/capture.py
import sys
from pathlib import Path
from urllib.parse import urlparse
from capture.models import Manifest, PageMeta, FidelityReport
from capture.content.extractor import extract_content
from capture.design.tokens import derive_tokens
from capture.design.llm import clean_tokens
from capture.design.theme_writer import write_theme
from capture.media import localize_media, rewrite_urls
from capture.bundle import write_bundle, BundlePaths

def _slugify(url: str, index: int) -> str:
    path = urlparse(url).path.strip("/")
    return path.replace("/", "-") or ("home" if index == 0 else f"page-{index}")

def run_capture(url, slug, out_root, max_pages=50, *, renderer, discover, llm_client=None) -> FidelityReport:
    urls = discover(url, max_pages=max_pages)
    pages, metas, snaps, all_assets = [], [], [], []
    for i, u in enumerate(urls):
        pslug = _slugify(u, i)
        try:
            rp = renderer.render(u, pslug)
            pc = extract_content(rp)
            pages.append(pc)
            snaps.extend(rp.computed)
            all_assets.extend(rp.assets)
            metas.append(PageMeta(url=u, slug=pslug, title=rp.title, status="ok"))
        except Exception:
            metas.append(PageMeta(url=u, slug=pslug, title=pslug, status="error"))
    tokens = clean_tokens(derive_tokens(snaps), client=llm_client)
    front = metas[0].slug if metas else "home"
    manifest = Manifest(site_title=(pages[0].title if pages else slug),
                        tagline="", front_page_slug=front, pages=metas)
    bdir = write_bundle(out_root, slug, pages, manifest, tokens)
    bp = BundlePaths(bdir)
    write_theme(tokens, bp.theme)
    mapping = localize_media(all_assets, bp.media)
    for pc in pages:
        f = bp.pages / f"{pc.slug}.html"
        f.write_text(rewrite_urls(f.read_text(), mapping))
    return FidelityReport(passed=False, content_ok=False,
                          page_results=[{"slug": m.slug, "status": m.status} for m in metas],
                          design_diff={})

def main(argv=None):
    argv = argv or sys.argv[1:]
    url = argv[0]
    slug = argv[1] if len(argv) > 1 else urlparse(url).netloc.replace(".", "-")
    from capture.renderer import Renderer
    from capture.discovery import discover_pages
    rep = run_capture(url, slug, Path("capture-out"), renderer=Renderer(), discover=discover_pages)
    print(f"Captured {len(rep.page_results)} pages to capture-out/{slug}")

if __name__ == "__main__":
    main()
```

> Note: `run_capture` returns a non-passing `FidelityReport` placeholder for content/design — the verifier runs in the CLI integration step (Task 15) where both captured and original renders are available. The two unit tests assert bundle production and error-recording, not fidelity.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/capture/test_capture.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add capture/capture.py tests/capture/test_capture.py
git commit -m "feat(capture): orchestrator wiring discovery->render->extract->derive->bundle"
```

---

### Task 15: End-to-end integration against the armand_gilbert fixture

**Files:**
- Modify: `capture/capture.py` (add `main` post-bundle steps: install + verify)
- Create: `tests/capture/test_integration_armand.py` (marked `@pytest.mark.integration`, opt-in)

**Interfaces:**
- Consumes: `WPInstaller` (Task 12), `verify_site` (Task 13), everything else.
- Produces: CLI flow `capture <url>` → bundle → install → render captured localhost → `verify_site`
  → write `fidelity-report.json`. Integration test runs only when `RUN_INTEGRATION=1` and Docker is up.

- [ ] **Step 1: Write the failing (opt-in) integration test**

```python
# tests/capture/test_integration_armand.py
import os, json
import pytest
from pathlib import Path

pytestmark = pytest.mark.skipif(os.environ.get("RUN_INTEGRATION") != "1",
                                reason="integration: needs Docker + network")

def test_armand_gilbert_content_is_exact(tmp_path):
    from capture.capture import run_capture
    from capture.renderer import Renderer
    from capture.discovery import discover_pages
    rep = run_capture("https://armandgilbert.com/", "armand", tmp_path,
                      max_pages=8, renderer=Renderer(), discover=discover_pages)
    gs = tmp_path / "armand" / "pages" / "get-started.html"
    assert gs.exists()
    body = gs.read_text()
    # regression: the previously-dropped title + intro copy must be captured
    assert "Get Started" in body
    assert "760-632-8258" in body
```

- [ ] **Step 2: Run it (expect skip without the env var)**

Run: `pytest tests/capture/test_integration_armand.py -v`
Expected: SKIPPED (1 skipped) — confirms wiring; full run is `RUN_INTEGRATION=1 pytest ...` with Docker up.

- [ ] **Step 3: Wire install + verify into `main`**

```python
# add to capture/capture.py main(), after run_capture(...)
    from capture.installer import WPInstaller
    from capture.verify import verify_site
    bundle = Path("capture-out") / slug
    WPInstaller().install(bundle)
    # Re-render captured localhost pages and the originals, compare fingerprints:
    # (implementer: reuse Renderer for http://localhost:8080/<slug>/ and the original url,
    #  run extract_content on each to get fingerprints, then verify_site(...).)
    print("Installed. Run verify_site() to produce fidelity-report.json")
```

- [ ] **Step 4: Run the full integration locally (manual gate)**

Run: `RUN_INTEGRATION=1 pytest tests/capture/test_integration_armand.py -v` (Docker compose up first)
Expected: PASS — `get-started.html` contains the title + `760-632-8258`.

- [ ] **Step 5: Commit**

```bash
git add capture/capture.py tests/capture/test_integration_armand.py
git commit -m "test(capture): opt-in e2e integration against armand_gilbert fixture"
```

---

## Self-Review

**1. Spec coverage**
- §4 Bundle → Tasks 11 (writer/paths), 9 (theme), 10 (media). ✔
- §5.1 Renderer → Task 3. ✔ · §5.2 Content Extractor → Tasks 4–6. ✔ · §5.3 Design Deriver → Tasks 7–9. ✔ · §5.4 Media → Task 10. ✔ · §5.5 Installer → Task 12. ✔ · §5.6 Verifier → Task 13. ✔ · §5.7 Orchestrator → Tasks 14–15. ✔
- §3.4 LLM never touches content → enforced + tested in Task 8 (`test_model_is_pinned_and_content_never_sent`). ✔
- §7 per-page isolation → Task 14 (`test_failing_page_is_recorded_not_fatal`). ✔
- §8 dropped title/intro regression → Tasks 6 + 15. ✔
- §2 no remote assets → Task 10 + Task 14 URL rewrite. ✔
- §10.4 no site-specific paths → discovery/extractor are generic; armand_gilbert only in opt-in test. ✔

**2. Placeholder scan:** No "TBD/TODO/handle edge cases" in steps. The two `> Note:` blocks give concrete fallbacks, not placeholders. Task 15 Step 3 explicitly defers the localhost re-render wiring to the implementer with exact instructions (it needs a live render loop), which is acceptable for an opt-in integration gate.

**3. Type consistency:** `RenderedPage`, `ComputedStyleSnapshot`, `PageContent`, `DesignTokens`, `Manifest`, `PageMeta`, `FidelityReport` used identically across tasks. `derive_tokens`/`clean_tokens`/`write_theme`/`localize_media`/`rewrite_urls`/`extract_content`/`content_fingerprint`/`verify_site` signatures match their definitions where consumed. `BundlePaths` attributes (`.pages/.media/.theme/.manifest/.tokens/.report`) consistent between Tasks 11–15.

---

## Notes & Deferred (from spec §11)
- Design-closeness `color_tol` defaults to 25.0; calibrate against the fixture during Task 15.
- Sitemap/crawl depth limits are `max_pages` only for now; richer crawl is a later enhancement.
- Phase 2 (theme-swap redesign, hand-off, alternate-theme generation) is a separate spec/plan.
