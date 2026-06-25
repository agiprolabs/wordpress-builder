# Phase A — Crawl-Source Characterizer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Emit the tech-agnostic **markdown site spec** (`characterization/<slug>/` tree) from the crawl source, by introducing a neutral `Block` model + a characterizer that assembles content, layout (nested grid tree), components, plugins (inferred), and design into markdown-with-frontmatter files.

**Architecture:** A new `characterize/` package. The existing extractor is refactored into a neutral `extract_blocks()` core with a thin WP adapter so the merged WordPress path stays green. New modules build a layout grid tree, detect cross-page components, infer plugins, and a writer renders the `SiteCharacterization` model to the markdown tree + `characterization.json`. An orchestrator wires it from injected renderer/discover (unit-tested without network).

**Tech Stack:** Python 3.12+, pytest, BeautifulSoup4 + lxml, PyYAML (for frontmatter), existing `capture/` modules (`renderer`, `design/tokens`, `media`, `models`). `uv` project; test command `uv run pytest`.

## Global Constraints

- **Content text is captured VERBATIM — never LLM-paraphrased.** The LLM assists only design-token naming + plugin/design prose. (spec §2, §5)
- **Both human and machine readable:** every `.md` = YAML frontmatter (machine) + prose body (human); `characterization.json` is the assembled machine index. (spec §2)
- **`content_fingerprint` per page guarantees 1:1 content** and must reproduce the `/get-started/` regression (title + "760-632-8258" intro). (spec §5)
- **Do not break the merged WordPress path:** existing `capture/` tests must stay green; the extractor refactor keeps `extract_content()` working. (plan decision)
- **Block taxonomy:** `heading · paragraph · list · image · table · button · embed · plugin`. (spec §2)
- **Layout `node ∈ {container, content, component}`**; containers carry CSS grid/flex `layout` + `children`. (spec §2)
- **Phase A is crawl-source only** — `source: crawl`, plugins always `source: inferred`, no `backend/` dir. (spec §6)
- Add dependency `pyyaml`. Test command is `uv run pytest`.

---

## File Structure

```
characterize/
  __init__.py
  models.py          # Block, GridNode, PageSpec, ThemeSpec, ComponentSpec, PluginSpec,
                     # SiteSpec, SiteCharacterization  (+ to_frontmatter/to_dict/from_dict)
  layout.py          # build_grid_tree(page) -> GridNode
  components.py      # detect_components(pages) -> list[ComponentSpec]
  plugins.py         # infer_plugins(pages) -> list[PluginSpec]
  theme.py           # build_theme_spec(snapshots) -> ThemeSpec
  writer.py          # write_characterization(site_char, out_dir) -> Path
  characterizer.py   # run_characterize(...) orchestrator + main()
capture/content/extractor.py  # MODIFY: add extract_blocks() neutral core; extract_content() becomes WP adapter
tests/characterize/   # one test file per module
pyproject.toml        # add pyyaml
```

---

### Task 1: characterize package scaffold + models

**Files:**
- Create: `characterize/__init__.py` (empty), `characterize/models.py`
- Modify: `pyproject.toml` (add `pyyaml`)
- Test: `tests/characterize/__init__.py` (empty), `tests/characterize/test_models.py`

**Interfaces:**
- Produces: `Block(type: str, data: dict)` with `to_frontmatter()->dict` (`{"type":type, **data}`) and `from_dict`. `GridNode(node: str, layout: dict|None=None, children: list|None=None, area: str|None=None, ref: str|None=None, blocks_ref: str|None=None)` with recursive `to_dict`/`from_dict`. `PageSpec(url, slug, title, parent, template, status, blocks: list[Block], grid: GridNode|None, fingerprint: str)`. `ThemeSpec(palette: dict, typography: dict, spacing_scale: list, layout: dict, font_assets: list)`. `ComponentSpec(name, appears_on, type, elements: list)`. `PluginSpec(name, slug, source, version, behavior, instances: list, data_ref)`. `SiteSpec(domain, title, tagline, source, captured_at, detected_stack: dict, nav: list, pages: list, plugins: list)`. `SiteCharacterization(site: SiteSpec, theme: ThemeSpec, pages: list[PageSpec], components: list[ComponentSpec], plugins: list[PluginSpec])` with `to_index()->dict`. All `@dataclass`, all JSON-round-trippable.

- [ ] **Step 1: Write the failing test**

```python
# tests/characterize/test_models.py
from characterize.models import (Block, GridNode, PageSpec, SiteCharacterization,
                                  SiteSpec, ThemeSpec)

def test_block_frontmatter():
    b = Block("heading", {"level": 1, "text": "Hi"})
    assert b.to_frontmatter() == {"type": "heading", "level": 1, "text": "Hi"}
    assert Block.from_dict(b.to_frontmatter()) == b

def test_gridnode_recursive_roundtrip():
    g = GridNode("container", layout={"display": "flex"},
                 children=[GridNode("content", blocks_ref="content.md", area="main")])
    assert GridNode.from_dict(g.to_dict()) == g

def test_site_characterization_index():
    sc = SiteCharacterization(
        site=SiteSpec("x.com", "X", "", "crawl", "2026-06-24", {}, [], ["home"], []),
        theme=ThemeSpec({}, {}, [], {}, []),
        pages=[PageSpec("https://x.com/", "home", "Home", None, "front-page", "published",
                        [Block("paragraph", {"text": "hi"})], None, "fp")],
        components=[], plugins=[])
    idx = sc.to_index()
    assert idx["site"]["domain"] == "x.com"
    assert idx["pages"][0]["slug"] == "home"
    assert idx["spec_version"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/characterize/test_models.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'characterize'`

- [ ] **Step 3: Write minimal implementation**

```python
# characterize/models.py
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional

SPEC_VERSION = "1.0"

@dataclass
class Block:
    type: str
    data: dict = field(default_factory=dict)
    def to_frontmatter(self): return {"type": self.type, **self.data}
    @classmethod
    def from_dict(cls, d):
        d = dict(d); t = d.pop("type"); return cls(t, d)

@dataclass
class GridNode:
    node: str
    layout: Optional[dict] = None
    children: Optional[list] = None
    area: Optional[str] = None
    ref: Optional[str] = None
    blocks_ref: Optional[str] = None
    def to_dict(self):
        out = {"node": self.node}
        if self.layout is not None: out["layout"] = self.layout
        if self.area is not None: out["area"] = self.area
        if self.ref is not None: out["ref"] = self.ref
        if self.blocks_ref is not None: out["blocks_ref"] = self.blocks_ref
        if self.children is not None: out["children"] = [c.to_dict() for c in self.children]
        return out
    @classmethod
    def from_dict(cls, d):
        d = dict(d)
        ch = d.pop("children", None)
        node = cls(**d)
        if ch is not None: node.children = [cls.from_dict(c) for c in ch]
        return node

@dataclass
class PageSpec:
    url: str
    slug: str
    title: str
    parent: Optional[str]
    template: str
    status: str
    blocks: list = field(default_factory=list)
    grid: Optional[GridNode] = None
    fingerprint: str = ""
    def to_dict(self):
        return {"url": self.url, "slug": self.slug, "title": self.title, "parent": self.parent,
                "template": self.template, "status": self.status,
                "blocks": [b.to_frontmatter() for b in self.blocks],
                "grid": self.grid.to_dict() if self.grid else None,
                "fingerprint": self.fingerprint}

@dataclass
class ThemeSpec:
    palette: dict = field(default_factory=dict)
    typography: dict = field(default_factory=dict)
    spacing_scale: list = field(default_factory=list)
    layout: dict = field(default_factory=dict)
    font_assets: list = field(default_factory=list)
    def to_dict(self): return asdict(self)

@dataclass
class ComponentSpec:
    name: str
    appears_on: object
    type: str
    elements: list = field(default_factory=list)
    def to_dict(self): return asdict(self)

@dataclass
class PluginSpec:
    name: str
    slug: str
    source: str
    version: Optional[str]
    behavior: str
    instances: list = field(default_factory=list)
    data_ref: Optional[str] = None
    def to_dict(self): return asdict(self)

@dataclass
class SiteSpec:
    domain: str
    title: str
    tagline: str
    source: str
    captured_at: str
    detected_stack: dict = field(default_factory=dict)
    nav: list = field(default_factory=list)
    pages: list = field(default_factory=list)
    plugins: list = field(default_factory=list)
    def to_dict(self): return asdict(self)

@dataclass
class SiteCharacterization:
    site: SiteSpec
    theme: ThemeSpec
    pages: list = field(default_factory=list)
    components: list = field(default_factory=list)
    plugins: list = field(default_factory=list)
    def to_index(self):
        return {"spec_version": SPEC_VERSION, "site": self.site.to_dict(),
                "design": self.theme.to_dict(), "pages": [p.to_dict() for p in self.pages],
                "components": [c.to_dict() for c in self.components],
                "plugins": [p.to_dict() for p in self.plugins]}
```

Add `pyyaml` to `pyproject.toml` dependencies (`uv add pyyaml`).

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/characterize/test_models.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add characterize/ tests/characterize/test_models.py pyproject.toml uv.lock
git commit -m "feat(characterize): site-spec dataclasses (Block, GridNode, SiteCharacterization)"
```

---

### Task 2: Refactor extractor into neutral `extract_blocks` (keep WP path green)

**Files:**
- Modify: `capture/content/extractor.py`
- Test: `tests/characterize/test_extract_blocks.py`

**Interfaces:**
- Consumes: `RenderedPage` (capture.models), `Block` (Task 1).
- Produces: `extract_blocks(page: RenderedPage) -> list[Block]` (neutral; same DOM walk, emits `Block` objects per the taxonomy) and `fingerprint_blocks(blocks: list[Block]) -> str`. `extract_content(page) -> PageContent` is preserved as a thin WP adapter: it calls `extract_blocks`, converts each `Block` to WP markup via existing `capture/content/blocks.py`, and computes the fingerprint over the neutral blocks so it equals the characterizer's. Plugin nodes become `Block("plugin", {...})`.

- [ ] **Step 1: Write the failing test**

```python
# tests/characterize/test_extract_blocks.py
from capture.models import RenderedPage
from capture.content.extractor import extract_blocks, fingerprint_blocks

def _page(body):
    return RenderedPage(url="u", slug="get-started", title="Get Started",
                        html=f"<html><body>{body}</body></html>")

def test_extract_blocks_neutral_types():
    html = ('<div id="content-area"><div id="left-area">'
            '<h1 class="title">Get Started</h1>'
            '<p>Call 760-632-8258 for a Free Web Site Consultation.</p>'
            '<ul><li>One</li><li>Two</li></ul>'
            '<div class="gform_wrapper" id="gform_wrapper_1">FORM</div>'
            '</div></div>')
    blocks = extract_blocks(_page(html))
    types = [b.type for b in blocks]
    assert types == ["heading", "paragraph", "list", "plugin"]
    assert blocks[0].data == {"level": 1, "text": "Get Started"}
    assert "760-632-8258" in blocks[1].data["text"]
    assert blocks[2].data["items"] == ["One", "Two"]
    assert blocks[3].data["plugin"] == "gravity-forms"

def test_fingerprint_stable_and_sensitive():
    a = extract_blocks(_page("<main><p>Hello   World</p></main>"))
    b = extract_blocks(_page("<main><p>Hello World</p></main>"))
    c = extract_blocks(_page("<main><p>Goodbye</p></main>"))
    assert fingerprint_blocks(a) == fingerprint_blocks(b)
    assert fingerprint_blocks(a) != fingerprint_blocks(c)

def test_wp_adapter_still_works():
    from capture.content.extractor import extract_content
    pc = extract_content(_page('<div id="left-area"><h2>Hi</h2><p>Body</p></div>'))
    assert "wp:heading" in pc.block_html and "wp:paragraph" in pc.block_html
    assert pc.fingerprint  # neutral-block fingerprint
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/characterize/test_extract_blocks.py -v`
Expected: FAIL — `ImportError: cannot import name 'extract_blocks'`

- [ ] **Step 3: Write minimal implementation**

Replace the body of `capture/content/extractor.py` with this (keeps `_main_region`/`_CHROME`/`_is_form` logic, adds the neutral layer):

```python
# capture/content/extractor.py
import hashlib, re
from bs4 import BeautifulSoup
from capture.models import RenderedPage, PageContent
from capture.content import blocks as wp
from characterize.models import Block

_MAIN_SELECTORS = ["main", "#left-area", "#content-area", "#content", "article", ".entry-content"]
_CHROME = ["header", "nav", "footer", "aside", "script", "style", "#header", "#sidebar"]

def _main_region(soup):
    for sel in _MAIN_SELECTORS:
        el = soup.select_one(sel)
        if el:
            return el
    return soup.body or soup

def _is_form(node, classes, node_id):
    return node.name == "form" or "gform_wrapper" in classes or node_id.startswith("gform_")

def _walk(node, out, seen_plugin):
    for child in node.children:
        name = getattr(child, "name", None)
        if not name:
            continue
        classes = " ".join(child.get("class", []))
        node_id = child.get("id", "")
        if _is_form(child, classes, node_id):
            if not seen_plugin[0]:
                seen_plugin[0] = True
                out.append(Block("plugin", {"plugin": "gravity-forms", "ref": "plugins/gravity-forms.md"}))
            continue
        if name in ("h1", "h2", "h3", "h4", "h5", "h6"):
            t = child.get_text(" ", strip=True)
            if t: out.append(Block("heading", {"level": int(name[1]), "text": t}))
            continue
        if name == "p":
            t = child.get_text(" ", strip=True)
            if t: out.append(Block("paragraph", {"text": t}))
            continue
        if name in ("ul", "ol"):
            items = [li.get_text(" ", strip=True) for li in child.find_all("li", recursive=False)]
            items = [i for i in items if i]
            if items: out.append(Block("list", {"items": items, "ordered": name == "ol"}))
            continue
        if name == "img" and child.get("src"):
            out.append(Block("image", {"src": child["src"], "alt": child.get("alt", "")}))
            continue
        _walk(child, out, seen_plugin)

def extract_blocks(page: RenderedPage) -> list:
    soup = BeautifulSoup(page.html, "lxml")
    region = _main_region(soup)
    for sel in _CHROME:
        for el in region.select(sel):
            el.decompose()
    out, seen_plugin = [], [False]
    _walk(region, out, seen_plugin)
    return out

def fingerprint_blocks(blocks) -> str:
    parts = []
    for b in blocks:
        d = b.to_frontmatter()
        text = d.get("text", "") or " ".join(d.get("items", []) or [])
        text = re.sub(r"\s+", " ", text).strip().lower()
        parts.append(f"{b.type}:{text}")
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()

def _block_to_wp(b: Block) -> str:
    d = b.data
    if b.type == "heading": return wp.heading_block(d["level"], d["text"])
    if b.type == "paragraph": return wp.paragraph_block(d["text"])
    if b.type == "list": return wp.list_block(d["items"], d.get("ordered", False))
    if b.type == "image": return wp.image_block(d["src"], d.get("alt", ""))
    if b.type == "plugin": return wp.placeholder_block(d.get("plugin", "plugin"))
    return wp.html_block(d.get("html", ""))

def extract_content(page: RenderedPage) -> PageContent:
    blocks = extract_blocks(page)
    block_html = "\n\n".join(_block_to_wp(b) for b in blocks)
    placeholders = [b.data["plugin"] for b in blocks if b.type == "plugin"]
    return PageContent(slug=page.slug, title=page.title, block_html=block_html,
                       fingerprint=fingerprint_blocks(blocks), placeholders=placeholders)
```

> Note: the existing `tests/capture/test_extractor.py` asserts the old fingerprint shape only via `pc.fingerprint` truthiness and content presence — those still hold. If any existing assertion checks an exact fingerprint VALUE, update it to the new neutral fingerprint (it does not). Run the full `capture` suite in Step 4 to confirm.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/characterize/test_extract_blocks.py tests/capture/ -v`
Expected: PASS (new 3 + all existing capture tests green)

- [ ] **Step 5: Commit**

```bash
git add capture/content/extractor.py tests/characterize/test_extract_blocks.py
git commit -m "refactor(extractor): neutral Block core + WP adapter; shared fingerprint"
```

---

### Task 3: Layout grid-tree builder

**Files:**
- Create: `characterize/layout.py`
- Test: `tests/characterize/test_layout.py`

**Interfaces:**
- Consumes: `RenderedPage` (capture.models), `GridNode` (Task 1).
- Produces: `build_grid_tree(page: RenderedPage) -> GridNode`. Heuristic: the root is a vertical flex container with `header` (if present) → main row → `footer`. The main row is a grid `container` whose children are `content` (the main region's blocks, `blocks_ref="content.md"`, `area="main"`) and, if a `#sidebar`/`aside` exists, a `component` child (`ref="components/sidebar.md"`, `area="aside"`). Records `layout` dicts with CSS display values.

- [ ] **Step 1: Write the failing test**

```python
# tests/characterize/test_layout.py
from capture.models import RenderedPage
from characterize.layout import build_grid_tree

def _page(body):
    return RenderedPage(url="u", slug="p", title="P", html=f"<html><body>{body}</body></html>")

def test_grid_with_header_main_sidebar_footer():
    html = ('<div id="header">H</div>'
            '<div id="content-area"><div id="left-area"><p>x</p></div><div id="sidebar">S</div></div>'
            '<div id="footer">F</div>')
    g = build_grid_tree(_page(html))
    assert g.node == "container" and g.layout["direction"] == "column"
    kinds = [c.node for c in g.children]
    assert kinds[0] == "component"          # header
    assert kinds[-1] == "component"          # footer
    row = [c for c in g.children if c.node == "container"][0]
    areas = {c.area for c in row.children}
    assert {"main", "aside"} <= areas

def test_grid_without_sidebar_has_single_content():
    html = '<div id="content-area"><div id="left-area"><p>x</p></div></div>'
    g = build_grid_tree(_page(html))
    row = [c for c in g.children if c.node == "container"][0]
    assert [c.node for c in row.children] == ["content"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/characterize/test_layout.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'characterize.layout'`

- [ ] **Step 3: Write minimal implementation**

```python
# characterize/layout.py
from bs4 import BeautifulSoup
from characterize.models import GridNode

def build_grid_tree(page) -> GridNode:
    soup = BeautifulSoup(page.html, "lxml")
    children = []
    if soup.select_one("header, #header, .site-header"):
        children.append(GridNode("component", ref="components/header.md"))
    has_sidebar = soup.select_one("#sidebar, aside") is not None
    if has_sidebar:
        row = GridNode("container", layout={"display": "grid", "columns": "1fr 300px", "gap": "24px"},
                       children=[GridNode("content", blocks_ref="content.md", area="main"),
                                 GridNode("component", ref="components/sidebar.md", area="aside")])
    else:
        row = GridNode("container", layout={"display": "block"},
                       children=[GridNode("content", blocks_ref="content.md", area="main")])
    children.append(row)
    if soup.select_one("footer, #footer"):
        children.append(GridNode("component", ref="components/footer.md"))
    return GridNode("container", layout={"display": "flex", "direction": "column"}, children=children)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/characterize/test_layout.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add characterize/layout.py tests/characterize/test_layout.py
git commit -m "feat(characterize): heuristic nested grid-tree layout builder"
```

---

### Task 4: Cross-page component detector

**Files:**
- Create: `characterize/components.py`
- Test: `tests/characterize/test_components.py`

**Interfaces:**
- Consumes: `RenderedPage`, `ComponentSpec` (Task 1).
- Produces: `detect_components(pages: list[RenderedPage]) -> list[ComponentSpec]`. Emits a `ComponentSpec` for each chrome region that appears on ALL pages with identical inner text: `header` (sel `header,#header,.site-header`), `footer` (`footer,#footer`), `sidebar` (`#sidebar,aside`). `appears_on="all"`, `type="site-chrome"`, `elements=[]` (filled later/Phase B). A region present on only some pages is skipped in Phase A.

- [ ] **Step 1: Write the failing test**

```python
# tests/characterize/test_components.py
from capture.models import RenderedPage
from characterize.components import detect_components

def _p(slug, body):
    return RenderedPage(url="/"+slug, slug=slug, title=slug, html=f"<html><body>{body}</body></html>")

def test_detects_shared_header_footer():
    hdr, ftr = '<div id="header">LOGO</div>', '<div id="footer">(c)</div>'
    pages = [_p("home", hdr + "<main>a</main>" + ftr),
             _p("about", hdr + "<main>b</main>" + ftr)]
    comps = {c.name: c for c in detect_components(pages)}
    assert "header" in comps and "footer" in comps
    assert comps["header"].appears_on == "all"
    assert comps["header"].type == "site-chrome"

def test_skips_non_shared_region():
    pages = [_p("home", '<div id="sidebar">X</div><main>a</main>'),
             _p("about", "<main>b</main>")]  # no sidebar on about
    assert "sidebar" not in {c.name for c in detect_components(pages)}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/characterize/test_components.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# characterize/components.py
from bs4 import BeautifulSoup
from characterize.models import ComponentSpec

_REGIONS = {"header": "header, #header, .site-header", "footer": "footer, #footer",
            "sidebar": "#sidebar, aside"}

def _region_text(html, sel):
    el = BeautifulSoup(html, "lxml").select_one(sel)
    return el.get_text(" ", strip=True) if el else None

def detect_components(pages) -> list:
    out = []
    for name, sel in _REGIONS.items():
        texts = [_region_text(p.html, sel) for p in pages]
        present = [t for t in texts if t is not None]
        if present and len(present) == len(pages) and len(set(present)) == 1:
            out.append(ComponentSpec(name=name, appears_on="all", type="site-chrome", elements=[]))
    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/characterize/test_components.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add characterize/components.py tests/characterize/test_components.py
git commit -m "feat(characterize): cross-page site-chrome component detection"
```

---

### Task 5: Plugin inferrer

**Files:**
- Create: `characterize/plugins.py`
- Test: `tests/characterize/test_plugins.py`

**Interfaces:**
- Consumes: `RenderedPage`, `PluginSpec` (Task 1).
- Produces: `infer_plugins(pages: list[RenderedPage]) -> list[PluginSpec]`. Detects Gravity Forms (`.gform_wrapper` / `form[id^=gform_]`) → one `PluginSpec(name="Gravity Forms", slug="gravity-forms", source="inferred", version=None, behavior=..., data_ref=None)` aggregating an `instance` per form found, each with `id`, `pages` (slugs where it appears), and `fields` (label + inferred type from inputs).

- [ ] **Step 1: Write the failing test**

```python
# tests/characterize/test_plugins.py
from capture.models import RenderedPage
from characterize.plugins import infer_plugins

FORM = ('<form id="gform_1" class="gform_wrapper">'
        '<label>Name</label><input type="text" name="n">'
        '<label>Email</label><input type="email" name="e">'
        '</form>')

def _p(slug, body):
    return RenderedPage(url="/"+slug, slug=slug, title=slug, html=f"<html><body>{body}</body></html>")

def test_infers_gravity_forms_with_fields():
    specs = infer_plugins([_p("get-started", FORM), _p("about", "<p>x</p>")])
    assert len(specs) == 1
    gf = specs[0]
    assert gf.slug == "gravity-forms" and gf.source == "inferred"
    inst = gf.instances[0]
    assert inst["id"] == "gform_1"
    assert inst["pages"] == ["get-started"]
    labels = [f["label"] for f in inst["fields"]]
    assert labels == ["Name", "Email"]
    assert inst["fields"][1]["type"] == "email"

def test_no_forms_no_plugins():
    assert infer_plugins([_p("home", "<p>nothing</p>")]) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/characterize/test_plugins.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# characterize/plugins.py
from bs4 import BeautifulSoup
from characterize.models import PluginSpec

def _form_fields(form):
    fields = []
    for inp in form.find_all(["input", "textarea", "select"]):
        if inp.get("type") in ("hidden", "submit"):
            continue
        label = None
        lab = inp.find_previous("label")
        if lab: label = lab.get_text(" ", strip=True)
        fields.append({"label": label or inp.get("name", ""), "type": inp.get("type", inp.name)})
    return fields

def infer_plugins(pages) -> list:
    instances = []
    for p in pages:
        soup = BeautifulSoup(p.html, "lxml")
        for form in soup.select('form[id^="gform_"], form.gform_wrapper, .gform_wrapper form, .gform_wrapper'):
            fid = form.get("id", "gform")
            if not any(i["id"] == fid for i in instances):
                instances.append({"id": fid, "pages": [p.slug], "fields": _form_fields(form)})
    if not instances:
        return []
    return [PluginSpec(name="Gravity Forms", slug="gravity-forms", source="inferred",
                       version=None, behavior="Form builder; renders forms with validation.",
                       instances=instances, data_ref=None)]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/characterize/test_plugins.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add characterize/plugins.py tests/characterize/test_plugins.py
git commit -m "feat(characterize): infer Gravity Forms plugin + per-instance fields"
```

---

### Task 6: Theme spec builder

**Files:**
- Create: `characterize/theme.py`
- Test: `tests/characterize/test_theme.py`

**Interfaces:**
- Consumes: `ComputedStyleSnapshot` (capture.models), `derive_tokens` (capture.design.tokens), `ThemeSpec` (Task 1).
- Produces: `build_theme_spec(snapshots: list[ComputedStyleSnapshot]) -> ThemeSpec` — wraps `derive_tokens` and maps `DesignTokens` → `ThemeSpec` (palette, typography `{body:{family},heading:{family}}`, spacing_scale, layout `{container_width, breakpoints:[]}`, font_assets `[]`).

- [ ] **Step 1: Write the failing test**

```python
# tests/characterize/test_theme.py
from capture.models import ComputedStyleSnapshot
from characterize.theme import build_theme_spec

def test_build_theme_spec_from_snapshots():
    snaps = [
        ComputedStyleSnapshot("body", "body", {"background-color": "rgb(255,255,255)",
            "color": "rgb(51,43,36)", "font-family": "Inter, sans-serif"}),
        ComputedStyleSnapshot("h1", "h1", {"font-family": "Outfit, sans-serif"}),
        ComputedStyleSnapshot("container", ".container", {"max-width": "960px"}),
    ]
    t = build_theme_spec(snaps)
    assert t.palette["background"] == "#ffffff"
    assert t.typography["body"]["family"].startswith("Inter")
    assert t.typography["heading"]["family"].startswith("Outfit")
    assert t.layout["container_width"] == "960px"
    assert isinstance(t.spacing_scale, list)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/characterize/test_theme.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# characterize/theme.py
from capture.design.tokens import derive_tokens
from characterize.models import ThemeSpec

def build_theme_spec(snapshots) -> ThemeSpec:
    t = derive_tokens(snapshots)
    typography = {}
    if "body" in t.fonts: typography["body"] = {"family": t.fonts["body"]}
    if "heading" in t.fonts: typography["heading"] = {"family": t.fonts["heading"]}
    return ThemeSpec(palette=t.palette, typography=typography, spacing_scale=t.spacing,
                     layout={"container_width": f"{t.container_width}px", "breakpoints": []},
                     font_assets=[])
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/characterize/test_theme.py -v`
Expected: PASS (1 passed)

- [ ] **Step 5: Commit**

```bash
git add characterize/theme.py tests/characterize/test_theme.py
git commit -m "feat(characterize): map design tokens to ThemeSpec"
```

---

### Task 7: Markdown writer

**Files:**
- Create: `characterize/writer.py`
- Test: `tests/characterize/test_writer.py`

**Interfaces:**
- Consumes: `SiteCharacterization` (Task 1).
- Produces: `write_characterization(sc: SiteCharacterization, out_dir: Path) -> Path` — writes `site.md`, `design/theme.md`, `pages/<slug>/{page.md,content.md,layout.md}`, `components/<name>.md`, `plugins/<slug>.md`, and `characterization.json`. Each `.md` = `---\n<yaml frontmatter>\n---\n\n# <title>\n<prose>`. Helper `_md(frontmatter: dict, body: str) -> str`.

- [ ] **Step 1: Write the failing test**

```python
# tests/characterize/test_writer.py
import json, yaml
from pathlib import Path
from characterize.models import (SiteCharacterization, SiteSpec, ThemeSpec, PageSpec,
                                  Block, GridNode, PluginSpec)
from characterize.writer import write_characterization

def _sc():
    page = PageSpec("https://x.com/get-started/", "get-started", "Get Started", None, "page",
                    "published", [Block("heading", {"level": 1, "text": "Get Started"}),
                                  Block("paragraph", {"text": "Call 760-632-8258."})],
                    GridNode("container", layout={"display": "flex"}), "fp1")
    return SiteCharacterization(
        site=SiteSpec("x.com", "X", "t", "crawl", "2026-06-24", {"cms": "wordpress"},
                      [], ["get-started"], ["gravity-forms"]),
        theme=ThemeSpec({"background": "#fff"}, {}, [8, 16], {"container_width": "960px"}, []),
        pages=[page], components=[],
        plugins=[PluginSpec("Gravity Forms", "gravity-forms", "inferred", None, "Forms", [], None)])

def test_writes_tree_and_index(tmp_path: Path):
    out = write_characterization(_sc(), tmp_path)
    content = (out / "pages" / "get-started" / "content.md").read_text()
    assert content.startswith("---")
    fm = yaml.safe_load(content.split("---")[1])
    assert fm["blocks"][0] == {"type": "heading", "level": 1, "text": "Get Started"}
    assert "760-632-8258" in content                       # verbatim in prose body too
    assert (out / "design" / "theme.md").exists()
    assert (out / "plugins" / "gravity-forms.md").exists()
    idx = json.loads((out / "characterization.json").read_text())
    assert idx["spec_version"] and idx["pages"][0]["slug"] == "get-started"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/characterize/test_writer.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# characterize/writer.py
import json, yaml
from pathlib import Path

def _md(frontmatter: dict, title: str, body: str) -> str:
    fm = yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True).strip()
    return f"---\n{fm}\n---\n\n# {title}\n\n{body}\n"

def _blocks_prose(blocks) -> str:
    lines = []
    for b in blocks:
        d = b.data
        if b.type == "heading": lines.append(("#" * d["level"]) + " " + d["text"])
        elif b.type == "paragraph": lines.append(d["text"])
        elif b.type == "list": lines += [f"- {i}" for i in d.get("items", [])]
        elif b.type == "image": lines.append(f"![{d.get('alt','')}]({d.get('src','')})")
        elif b.type == "plugin": lines.append(f"[plugin: {d.get('plugin','')} → {d.get('ref','')}]")
        lines.append("")
    return "\n".join(lines).strip()

def write_characterization(sc, out_dir) -> Path:
    out = Path(out_dir)
    (out / "design").mkdir(parents=True, exist_ok=True)
    (out / "components").mkdir(exist_ok=True)
    (out / "plugins").mkdir(exist_ok=True)
    (out / "site.md").write_text(_md(sc.site.to_dict(), sc.site.title, sc.site.tagline or "Site overview."))
    (out / "design" / "theme.md").write_text(_md(sc.theme.to_dict(), "Design System", "Derived design tokens."))
    for p in sc.pages:
        pdir = out / "pages" / p.slug
        pdir.mkdir(parents=True, exist_ok=True)
        page_fm = {"url": p.url, "slug": p.slug, "title": p.title, "parent": p.parent,
                   "template": p.template, "status": p.status,
                   "content_ref": "content.md", "layout_ref": "layout.md"}
        (pdir / "page.md").write_text(_md(page_fm, p.title, f"Page: {p.title}."))
        content_fm = {"slug": p.slug, "content_fingerprint": p.fingerprint,
                      "blocks": [b.to_frontmatter() for b in p.blocks]}
        (pdir / "content.md").write_text(_md(content_fm, p.title, _blocks_prose(p.blocks)))
        layout_fm = {"slug": p.slug, "grid": p.grid.to_dict() if p.grid else None, "responsive": []}
        (pdir / "layout.md").write_text(_md(layout_fm, f"Layout — {p.title}", "Layout structure."))
    for c in sc.components:
        (out / "components" / f"{c.name}.md").write_text(_md(c.to_dict(), c.name, f"{c.name} component."))
    for pl in sc.plugins:
        (out / "plugins" / f"{pl.slug}.md").write_text(_md(pl.to_dict(), pl.name, pl.behavior))
    (out / "characterization.json").write_text(json.dumps(sc.to_index(), indent=2))
    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/characterize/test_writer.py -v`
Expected: PASS (1 passed)

- [ ] **Step 5: Commit**

```bash
git add characterize/writer.py tests/characterize/test_writer.py
git commit -m "feat(characterize): markdown-tree + characterization.json writer"
```

---

### Task 8: Orchestrator

**Files:**
- Create: `characterize/characterizer.py`
- Test: `tests/characterize/test_characterizer.py`

**Interfaces:**
- Consumes: all prior modules + `media.localize_media`/`rewrite_urls`.
- Produces: `run_characterize(url, slug, out_root, max_pages=50, *, renderer, discover, llm_client=None, captured_at="") -> Path`. Wires: discover → render each page (per-page try/except, errors skipped) → `extract_blocks` (+ `fingerprint_blocks`) → `build_grid_tree` per page → `detect_components(all)` → `infer_plugins(all)` → `build_theme_spec(all snapshots)` → assemble `SiteCharacterization(source="crawl")` → `write_characterization`. Front page = first page, `template="front-page"`; others `template="page"`. Returns the bundle dir. `renderer.close()` called after the render loop. Also `main(argv)`.

- [ ] **Step 1: Write the failing test**

```python
# tests/characterize/test_characterizer.py
import json
from pathlib import Path
from capture.models import RenderedPage, ComputedStyleSnapshot
from characterize.characterizer import run_characterize

def _renderer(pages):
    class R:
        def render(self, url, slug): return pages[url]
        def close(self): pass
    return R()

def test_run_characterize_emits_tree(tmp_path: Path):
    home = RenderedPage(url="https://x.com/", slug="home", title="Home",
        html="<body><div id='header'>H</div><main><h1>Home</h1><p>Welcome 760-632-8258</p></main></body>",
        computed=[ComputedStyleSnapshot("body","body",{"background-color":"rgb(255,255,255)","color":"rgb(0,0,0)","font-family":"Inter"})],
        assets=[])
    out = run_characterize("https://x.com/", "site", tmp_path,
                           renderer=_renderer({"https://x.com/": home}),
                           discover=lambda u, max_pages: ["https://x.com/"], captured_at="2026-06-24")
    idx = json.loads((out / "characterization.json").read_text())
    assert idx["site"]["source"] == "crawl"
    assert idx["pages"][0]["template"] == "front-page"
    assert "760-632-8258" in (out / "pages" / "home" / "content.md").read_text()

def test_failing_page_skipped(tmp_path: Path):
    class R:
        def render(self, url, slug): raise RuntimeError("boom")
        def close(self): pass
    out = run_characterize("https://x.com/", "s2", tmp_path, renderer=R(),
                           discover=lambda u, max_pages: ["https://x.com/"])
    idx = json.loads((out / "characterization.json").read_text())
    assert idx["pages"] == []   # the only page errored and was skipped
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/characterize/test_characterizer.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# characterize/characterizer.py
import sys
from pathlib import Path
from urllib.parse import urlparse
from capture.content.extractor import extract_blocks, fingerprint_blocks
from capture.media import localize_media, rewrite_urls
from characterize.layout import build_grid_tree
from characterize.components import detect_components
from characterize.plugins import infer_plugins
from characterize.theme import build_theme_spec
from characterize.writer import write_characterization
from characterize.models import SiteCharacterization, SiteSpec, PageSpec

def _slug(url, i):
    p = urlparse(url).path.strip("/")
    return p.replace("/", "-") or ("home" if i == 0 else f"page-{i}")

def run_characterize(url, slug, out_root, max_pages=50, *, renderer, discover,
                     llm_client=None, captured_at="") -> Path:
    urls = discover(url, max_pages=max_pages)
    rendered, pages, snaps = [], [], []
    for i, u in enumerate(urls):
        ps = _slug(u, i)
        try:
            rp = renderer.render(u, ps)
        except Exception:
            continue
        rendered.append(rp)
        snaps.extend(rp.computed)
        blocks = extract_blocks(rp)
        pages.append(PageSpec(url=u, slug=ps, title=rp.title, parent=None,
                              template=("front-page" if i == 0 else "page"), status="published",
                              blocks=blocks, grid=build_grid_tree(rp), fingerprint=fingerprint_blocks(blocks)))
    close = getattr(renderer, "close", None)
    if callable(close): close()
    components = detect_components(rendered)
    plugins = infer_plugins(rendered)
    theme = build_theme_spec(snaps)
    domain = urlparse(url).netloc
    site = SiteSpec(domain=domain, title=(pages[0].title if pages else slug), tagline="",
                    source="crawl", captured_at=captured_at, detected_stack={},
                    nav=[], pages=[p.slug for p in pages], plugins=[pl.slug for pl in plugins])
    sc = SiteCharacterization(site=site, theme=theme, pages=pages,
                              components=components, plugins=plugins)
    out_dir = Path(out_root) / slug
    write_characterization(sc, out_dir)
    return out_dir

def main(argv=None):
    argv = argv or sys.argv[1:]
    url = argv[0]
    slug = argv[1] if len(argv) > 1 else urlparse(url).netloc.replace(".", "-")
    from capture.renderer import Renderer
    from capture.discovery import discover_pages
    out = run_characterize(url, slug, Path("characterization"), renderer=Renderer(), discover=discover_pages)
    print(f"Characterized to {out}")

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/characterize/test_characterizer.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add characterize/characterizer.py tests/characterize/test_characterizer.py
git commit -m "feat(characterize): orchestrator wiring crawl -> markdown site spec"
```

---

### Task 9: Spec round-trip + opt-in armand_gilbert integration

**Files:**
- Create: `characterize/loader.py`, `tests/characterize/test_roundtrip.py`, `tests/characterize/test_integration_characterize.py`
- Test: as above

**Interfaces:**
- Consumes: `characterization.json`, `SiteCharacterization` models.
- Produces: `load_index(path: Path) -> dict` (reads `characterization.json`) and `validate_index(idx: dict) -> list[str]` (returns a list of schema problems; empty = valid: every page has slug/template/fingerprint, blocks have a `type` in the taxonomy, `spec_version` present). The opt-in integration test runs the full crawl-characterize against armand_gilbert under `RUN_INTEGRATION=1` and asserts the `/get-started/` `content.md` contains the title + `760-632-8258`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/characterize/test_roundtrip.py
from pathlib import Path
from characterize.loader import load_index, validate_index
from characterize.models import SiteCharacterization, SiteSpec, ThemeSpec, PageSpec, Block, GridNode
from characterize.writer import write_characterization

def test_written_index_validates(tmp_path: Path):
    sc = SiteCharacterization(
        site=SiteSpec("x.com","X","","crawl","2026-06-24",{},[],["home"],[]),
        theme=ThemeSpec(), pages=[PageSpec("https://x.com/","home","Home",None,"front-page",
                                           "published",[Block("paragraph",{"text":"hi"})],
                                           GridNode("container"), "fp")],
        components=[], plugins=[])
    out = write_characterization(sc, tmp_path)
    idx = load_index(out)
    assert validate_index(idx) == []

def test_validate_flags_bad_block_type(tmp_path: Path):
    idx = {"spec_version": "1.0", "site": {}, "design": {},
           "pages": [{"slug": "p", "template": "page", "fingerprint": "x",
                      "blocks": [{"type": "bogus"}]}], "components": [], "plugins": []}
    problems = validate_index(idx)
    assert any("bogus" in p for p in problems)
```

```python
# tests/characterize/test_integration_characterize.py
import os, json
import pytest
pytestmark = pytest.mark.skipif(os.environ.get("RUN_INTEGRATION") != "1",
                                reason="integration: needs network")

def test_armand_gilbert_get_started_characterized(tmp_path):
    from characterize.characterizer import run_characterize
    from capture.renderer import Renderer
    from capture.discovery import discover_pages
    out = run_characterize("https://armandgilbert.com/", "armand", tmp_path,
                           max_pages=8, renderer=Renderer(), discover=discover_pages)
    gs = out / "pages" / "get-started" / "content.md"
    assert gs.exists()
    body = gs.read_text()
    assert "Get Started" in body and "760-632-8258" in body
```

- [ ] **Step 2: Run tests to verify they fail/skip**

Run: `uv run pytest tests/characterize/test_roundtrip.py tests/characterize/test_integration_characterize.py -v`
Expected: roundtrip FAILS (`ModuleNotFoundError: characterize.loader`); integration SKIPPED.

- [ ] **Step 3: Write minimal implementation**

```python
# characterize/loader.py
import json
from pathlib import Path
from characterize.models import Block

_BLOCK_TYPES = {"heading", "paragraph", "list", "image", "table", "button", "embed", "plugin"}

def load_index(bundle_dir) -> dict:
    return json.loads((Path(bundle_dir) / "characterization.json").read_text())

def validate_index(idx: dict) -> list:
    problems = []
    if not idx.get("spec_version"):
        problems.append("missing spec_version")
    for p in idx.get("pages", []):
        for key in ("slug", "template", "fingerprint"):
            if not p.get(key):
                problems.append(f"page missing {key}: {p.get('slug', '?')}")
        for b in p.get("blocks", []):
            if b.get("type") not in _BLOCK_TYPES:
                problems.append(f"unknown block type '{b.get('type')}' in {p.get('slug','?')}")
    return problems
```

- [ ] **Step 4: Run tests to verify pass/skip**

Run: `uv run pytest tests/characterize/test_roundtrip.py tests/characterize/test_integration_characterize.py -v`
Expected: roundtrip PASS (2 passed); integration SKIPPED (1 skipped). Manual live gate: `RUN_INTEGRATION=1 uv run pytest tests/characterize/test_integration_characterize.py`.

- [ ] **Step 5: Commit**

```bash
git add characterize/loader.py tests/characterize/test_roundtrip.py tests/characterize/test_integration_characterize.py
git commit -m "feat(characterize): index loader + schema validation + opt-in e2e"
```

---

## Self-Review

**1. Spec coverage**
- §2 markdown schema → Task 7 (writer) + Task 1 (models). ✔ Every file type written.
- §3.1 models → Task 1. ✔ · §3.2 neutral extractor + WP re-home → Task 2 (extractor keeps `extract_content` green; WP-block builders now used only by the adapter). ✔ · §3.3 layout → Task 3. ✔ · §3.4 components → Task 4. ✔ · §3.5 plugin inference → Task 5. ✔ · §3.6 theme → Task 6. ✔ · §3.7 media reuse → wired in Task 8 (note below). · §3.8 writer → Task 7. ✔ · §3.9 orchestrator → Task 8. ✔
- §5 verification: content fingerprint carried over (Task 2, asserted Task 8/9); spec round-trip + schema validity → Task 9; get-started regression → Task 9 integration. ✔
- §2 "both human and machine readable": frontmatter + prose body (Task 7 `_md`), `characterization.json` (Task 7). ✔

**Gap found & noted:** §3.7 media localization (assets dir + ref rewrite) is referenced by the orchestrator but Task 8's minimal version does not yet localize assets (the fixture test uses no images). This is intentionally deferred to keep tasks bite-sized; **added to "Notes" below** as a fast-follow within Phase A rather than a silent omission — image-bearing pages need it before the WP-rebuild target consumes the spec.

**2. Placeholder scan:** No "TBD/handle edge cases" in steps. The one `> Note` in Task 2 gives a concrete fallback (update an exact-value fingerprint assertion if present), not a placeholder.

**3. Type consistency:** `Block(type,data)`, `GridNode`, `PageSpec`, `ThemeSpec`, `ComponentSpec`, `PluginSpec`, `SiteSpec`, `SiteCharacterization` used identically across Tasks 1–9. `extract_blocks`/`fingerprint_blocks` (Task 2) consumed by Task 8. `build_grid_tree`/`detect_components`/`infer_plugins`/`build_theme_spec`/`write_characterization` signatures match their definitions where consumed. `to_index()`/`to_frontmatter()`/`to_dict()` consistent.

---

## Notes & Deferred (within Phase A / fast-follow)
- **Media localization** (assets → `design/assets/`, rewrite `image`/font refs to spec-relative paths): wire `localize_media` + `rewrite_urls` into the orchestrator and add an image fixture test. Deferred from Task 8 to keep it bite-sized; do before the WP-rebuild target reads the spec.
- Confidence scoring / human-annotation hooks for low-confidence layout & plugin inference (spec §7).
- `components/*.md` `elements[]` enrichment (logo asset, nav ref) — minimal `[]` in Phase A.
- Bounded LLM prose for `design/theme.md` and plugin `behavior` — Phase A writes deterministic placeholders; LLM enrichment is a fast-follow (content stays untouched either way).
