# Phase B1 — Crawl Quality + Screenshots Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the crawl-quality defects the real validation run exposed (chrome leaks, duplicate headings, noisy form-field inference, front-page mis-assignment) and add per-page **screenshots** as a layout reference — the prerequisites for Phase B's content-parity assertion and visual ground-truth.

**Architecture:** Targeted changes to the existing crawl pipeline: tighten the deterministic content extractor's chrome stripping + heading dedup; improve form-field inference (label `for`/`id` association + checkbox/radio grouping); anchor the front-page template to the homepage URL; capture a screenshot per page in the renderer and plumb it through `PageSpec` → writer into `pages/<slug>/screenshot.png` + `page.md` frontmatter.

**Tech Stack:** Python 3.12+, pytest, BeautifulSoup4 + lxml, Playwright (Python), existing `capture/` + `characterize/` modules. `uv` project; test command `uv run pytest`.

## Global Constraints

- **Content text stays VERBATIM** — chrome stripping removes only WP chrome (post-meta, theme-rendered page title), never real content. (spec §4, §9)
- **`content_fingerprint` stays comparable** between crawl and (future) backend — chrome stripping makes crawl content match clean `post_content`. (spec §8, §9)
- **Screenshots come from the headless render**, stored at `pages/<slug>/screenshot.png`, referenced in `page.md` frontmatter as `screenshot: screenshot.png`. (spec §2.5, §6)
- **Front-page = the page whose URL path is the site root** (`""`), not the first-discovered URL. (Phase A validation finding)
- **Best-effort heuristics** for chrome/form inference — crawl infers; exactness is Phase B's backend job. (spec §1)
- The existing `capture/` + `characterize/` suites must stay green (currently 70 passed, 2 skipped). Test command `uv run pytest`.

---

## File Structure

```
capture/content/extractor.py   # MODIFY: chrome strip post-meta/title + dedup consecutive identical headings
capture/renderer.py            # MODIFY: capture per-page screenshot -> RenderedPage.screenshot_path
characterize/plugins.py        # MODIFY: label for/id association + checkbox/radio grouping
characterize/models.py         # MODIFY: PageSpec gains screenshot_src (internal) ; page dict gains screenshot rel-ref
characterize/characterizer.py  # MODIFY: front-page anchored to homepage; pass screenshot dir; set screenshot_src
characterize/writer.py         # MODIFY: copy screenshot into page dir; add `screenshot` to page.md frontmatter
tests/capture/ , tests/characterize/   # tests per change
```

---

### Task 1: Strip WP chrome (post-meta) + dedup consecutive identical headings

**Files:**
- Modify: `capture/content/extractor.py`
- Test: `tests/characterize/test_extract_blocks.py` (append)

**Interfaces:**
- Consumes: `RenderedPage`, `Block` (existing).
- Produces: `extract_blocks(page) -> list[Block]` (unchanged signature). New behavior: WP post-meta
  selectors (`.post-meta, .entry-meta, .posted-on, .post-categories, .entry-footer`) added to the
  chrome-strip set; consecutive headings with identical (level, normalized-text) collapse to one.

- [ ] **Step 1: Write the failing test**

```python
# append to tests/characterize/test_extract_blocks.py
def test_strips_post_meta_and_dedups_title():
    html = ('<div id="left-area">'
            '<h1 class="title">Get Started</h1>'
            '<h1>Get Started</h1>'
            '<p class="post-meta">Posted in News</p>'
            '<p>Real intro copy.</p>'
            '</div>')
    blocks = extract_blocks(_page(html))
    texts = [(b.type, b.data.get("text")) for b in blocks]
    assert texts.count(("heading", "Get Started")) == 1   # duplicate title collapsed
    assert ("paragraph", "Posted in News") not in texts    # post-meta stripped
    assert ("paragraph", "Real intro copy.") in texts      # real content kept
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/characterize/test_extract_blocks.py::test_strips_post_meta_and_dedups_title -v`
Expected: FAIL (post-meta present and/or duplicate heading present)

- [ ] **Step 3: Write minimal implementation**

In `capture/content/extractor.py`, extend `_CHROME`:

```python
_CHROME = ["header", "nav", "footer", "aside", "script", "style", "#header", "#sidebar",
           ".post-meta", ".entry-meta", ".posted-on", ".post-categories", ".entry-footer"]
```

Add heading dedup in `_walk` — track the last emitted block and skip a heading identical to it:

```python
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
            text = child.get_text(" ", strip=True)
            if text:
                lvl = int(name[1])
                if out and out[-1].type == "heading" and out[-1].data.get("level") == lvl \
                        and out[-1].data.get("text", "").strip().lower() == text.strip().lower():
                    continue  # collapse consecutive identical heading
                out.append(Block("heading", {"level": lvl, "text": text}))
            continue
        if name == "p":
            text = child.get_text(" ", strip=True)
            if text:
                out.append(Block("paragraph", {"text": text}))
            continue
        if name in ("ul", "ol"):
            items = [li.get_text(" ", strip=True) for li in child.find_all("li", recursive=False)]
            items = [i for i in items if i]
            if items:
                out.append(Block("list", {"items": items, "ordered": name == "ol"}))
            continue
        if name == "img" and child.get("src"):
            out.append(Block("image", {"src": child["src"], "alt": child.get("alt", "")}))
            continue
        _walk(child, out, seen_plugin)
```

> The dedup only collapses *consecutive* identical headings (the theme-rendered page-title duplicating the content H1). Non-adjacent repeats (legitimately repeated headings) are preserved.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/characterize/test_extract_blocks.py tests/capture/ -v`
Expected: PASS (new test + all existing extractor/capture tests green)

- [ ] **Step 5: Commit**

```bash
git add capture/content/extractor.py tests/characterize/test_extract_blocks.py
git commit -m "fix(extractor): strip WP post-meta chrome; collapse duplicate page-title heading"
```

---

### Task 2: Anchor the front-page template to the homepage URL

**Files:**
- Modify: `characterize/characterizer.py`
- Test: `tests/characterize/test_characterizer.py` (append)

**Interfaces:**
- Consumes: `RenderedPage`, `PageSpec`.
- Produces: `_is_front_page(url: str) -> bool` (path strips to `""`); the page-template assignment uses
  it instead of `i == 0`. A page whose URL path is the site root gets `template="front-page"`; all
  others `"page"`. (If no page is the root, none is front-page.)

- [ ] **Step 1: Write the failing test**

```python
# append to tests/characterize/test_characterizer.py
def test_front_page_is_homepage_not_first(tmp_path):
    import json
    def mk(url, slug, body): 
        return RenderedPage(url=url, slug=slug, title=slug, html=f"<body><main>{body}</main></body>", computed=[], assets=[])
    pages = {"https://x.com/about/": mk("https://x.com/about/", "about", "<p>a</p>"),
             "https://x.com/": mk("https://x.com/", "home", "<p>h</p>")}
    out = run_characterize("https://x.com/", "site", tmp_path,
                           renderer=_renderer_for(pages),
                           discover=lambda u, max_pages: ["https://x.com/about/", "https://x.com/"])
    idx = json.loads((out / "characterization.json").read_text())
    by_slug = {p["slug"]: p for p in idx["pages"]}
    assert by_slug["home"]["template"] == "front-page"   # homepage, even though discovered 2nd
    assert by_slug["about"]["template"] == "page"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/characterize/test_characterizer.py::test_front_page_is_homepage_not_first -v`
Expected: FAIL (about — discovered first — wrongly gets front-page)

- [ ] **Step 3: Write minimal implementation**

In `characterize/characterizer.py`, add the helper and use it. Replace the per-page `template=`
expression inside the loop:

```python
def _is_front_page(url) -> bool:
    return urlparse(url).path.strip("/") == ""
```

In the render loop, change the `PageSpec(...)` `template=` argument from
`("front-page" if i == 0 else "page")` to `("front-page" if _is_front_page(u) else "page")`.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/characterize/test_characterizer.py -v`
Expected: PASS (new test + existing characterizer tests green)

- [ ] **Step 5: Commit**

```bash
git add characterize/characterizer.py tests/characterize/test_characterizer.py
git commit -m "fix(characterize): front-page template anchored to homepage URL, not discovery order"
```

---

### Task 3: Improve form-field inference — label `for`/`id` association + checkbox/radio grouping

**Files:**
- Modify: `characterize/plugins.py`
- Test: `tests/characterize/test_plugins.py` (append)

**Interfaces:**
- Consumes: `RenderedPage`, `PluginSpec`.
- Produces: `infer_plugins(pages) -> list[PluginSpec]` (unchanged signature). New `_form_fields(form)`
  behavior: associate a label to its input by `<label for=id>` ↔ `input id`, falling back to the
  nearest preceding label; collapse consecutive checkbox/radio inputs that share a group `name` into
  ONE field `{label, type: checkbox|radio, options: [...]}` instead of one field per option.

- [ ] **Step 1: Write the failing test**

```python
# append to tests/characterize/test_plugins.py
GROUPED = ('<form id="gform_9" class="gform_wrapper">'
           '<label for="i_name">Full Name</label><input id="i_name" type="text" name="name">'
           '<label>Interests</label>'
           '<input type="checkbox" name="interest[]" value="a"><label>Design</label>'
           '<input type="checkbox" name="interest[]" value="b"><label>SEO</label>'
           '</form>')

def test_label_for_id_and_checkbox_grouping():
    specs = infer_plugins([_p("contact", GROUPED)])
    fields = specs[0].instances[0]["fields"]
    name_field = [f for f in fields if f["type"] == "text"][0]
    assert name_field["label"] == "Full Name"          # matched via for/id, not a stray label
    cb = [f for f in fields if f["type"] == "checkbox"]
    assert len(cb) == 1                                 # ONE grouped checkbox field, not 2
    assert sorted(cb[0]["options"]) == ["Design", "SEO"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/characterize/test_plugins.py::test_label_for_id_and_checkbox_grouping -v`
Expected: FAIL (checkboxes emitted as separate fields; label association off)

- [ ] **Step 3: Write minimal implementation**

Replace `_form_fields` in `characterize/plugins.py`:

```python
def _form_fields(form):
    # map <label for=ID> -> text for precise association
    label_for = {}
    for lab in form.find_all("label"):
        if lab.get("for"):
            label_for[lab["for"]] = lab.get_text(" ", strip=True)

    def label_of(inp):
        if inp.get("id") and inp["id"] in label_for:
            return label_for[inp["id"]]
        prev = inp.find_previous("label")
        return prev.get_text(" ", strip=True) if prev else inp.get("name", "")

    fields = []
    group = None  # accumulates a checkbox/radio group keyed by (type, name)
    for inp in form.find_all(["input", "textarea", "select"]):
        itype = inp.get("type", inp.name)
        if itype in ("hidden", "submit", "button"):
            continue
        if itype in ("checkbox", "radio"):
            key = (itype, inp.get("name", ""))
            option = label_of(inp)
            if group and group["_key"] == key:
                group["options"].append(option)
            else:
                # close previous group, start a new one labelled by the question preceding it
                if group:
                    group.pop("_key"); fields.append(group)
                question = None
                q = inp.find_previous("label")
                # the group's question is the label BEFORE the first option's own label
                prev_label = q.find_previous("label") if q else None
                question = (prev_label.get_text(" ", strip=True) if prev_label else
                            (q.get_text(" ", strip=True) if q else inp.get("name", "")))
                group = {"_key": key, "label": question, "type": itype, "options": [option]}
            continue
        if group:
            group.pop("_key"); fields.append(group); group = None
        fields.append({"label": label_of(inp), "type": itype})
    if group:
        group.pop("_key"); fields.append(group)
    return fields
```

> Heuristic, per spec: the group's question label is the label preceding the first option's own
> label. Exactness (real field config) is Phase B's backend job; this just makes crawl inference
> meaningfully comparable.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/characterize/test_plugins.py -v`
Expected: PASS (new test + existing plugin tests green — note: the existing `test_infers_gravity_forms_with_fields` uses simple text/email inputs with adjacent labels, still handled by the `label_of` fallback)

- [ ] **Step 5: Commit**

```bash
git add characterize/plugins.py tests/characterize/test_plugins.py
git commit -m "fix(characterize): form fields via label for/id; group checkbox/radio options"
```

---

### Task 4: Capture a per-page screenshot in the renderer

**Files:**
- Modify: `capture/renderer.py`
- Test: `tests/capture/test_renderer.py` (append)

**Interfaces:**
- Consumes: `RenderedPage`.
- Produces: `Renderer(page_factory=..., screenshot_dir: str|None = None)`. When `screenshot_dir` is set
  AND the page object supports `.screenshot(path=...)`, `render(url, slug)` writes
  `<screenshot_dir>/<slug>.png` and sets `RenderedPage.screenshot_path` to that path; otherwise
  `screenshot_path` stays `None`. Fakes without `.screenshot` are unaffected.

- [ ] **Step 1: Write the failing test**

```python
# append to tests/capture/test_renderer.py
def test_render_writes_screenshot(tmp_path):
    shots = []
    class ShotPage(FakePage):
        def screenshot(self, path=None, **kw): shots.append(path); open(path, "wb").write(b"PNG")
    r = Renderer(page_factory=lambda: ShotPage(), screenshot_dir=str(tmp_path))
    page = r.render("https://x.com/", slug="home")
    assert page.screenshot_path == str(tmp_path / "home.png")
    assert (tmp_path / "home.png").exists()

def test_render_without_screenshot_dir_is_none():
    r = Renderer(page_factory=lambda: FakePage())   # FakePage has no .screenshot
    page = r.render("https://x.com/", slug="home")
    assert page.screenshot_path is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/capture/test_renderer.py::test_render_writes_screenshot -v`
Expected: FAIL (`Renderer` has no `screenshot_dir` param)

- [ ] **Step 3: Write minimal implementation**

In `capture/renderer.py`, add the constructor param and the screenshot step in `render`:

```python
    def __init__(self, page_factory=_default_page_factory, screenshot_dir=None):
        self._page_factory = page_factory
        self._page = None
        self._screenshot_dir = screenshot_dir
```

In `render`, after computing `assets` and before constructing `RenderedPage`, add:

```python
        import os
        screenshot_path = None
        shot = getattr(page, "screenshot", None)
        if self._screenshot_dir and callable(shot):
            os.makedirs(self._screenshot_dir, exist_ok=True)
            screenshot_path = os.path.join(self._screenshot_dir, f"{slug}.png")
            try:
                shot(path=screenshot_path, full_page=True)
            except Exception:
                screenshot_path = None
```

and pass `screenshot_path=screenshot_path` into the returned `RenderedPage(...)`.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/capture/test_renderer.py -v`
Expected: PASS (2 new + existing renderer tests green)

- [ ] **Step 5: Commit**

```bash
git add capture/renderer.py tests/capture/test_renderer.py
git commit -m "feat(renderer): capture per-page screenshot to screenshot_dir"
```

---

### Task 5: Plumb the screenshot into the spec (PageSpec → characterizer → writer)

**Files:**
- Modify: `characterize/models.py`, `characterize/characterizer.py`, `characterize/writer.py`
- Test: `tests/characterize/test_writer.py` (append), `tests/characterize/test_characterizer.py` (append)

**Interfaces:**
- Consumes: `PageSpec`, `write_characterization`, `run_characterize`.
- Produces: `PageSpec` gains `screenshot_src: str|None = None` (absolute source path; NOT serialized
  into `to_dict`). `write_characterization` copies `screenshot_src` → `pages/<slug>/screenshot.png` and
  adds `screenshot: screenshot.png` to `page.md` frontmatter when present. `run_characterize` accepts
  `screenshot_dir` (passed to `Renderer`) and sets each `PageSpec.screenshot_src = rp.screenshot_path`.

- [ ] **Step 1: Write the failing test**

```python
# append to tests/characterize/test_writer.py
def test_screenshot_copied_and_referenced(tmp_path: Path):
    from characterize.models import (SiteCharacterization, SiteSpec, ThemeSpec, PageSpec, Block, GridNode)
    src = tmp_path / "src.png"; src.write_bytes(b"PNG")
    page = PageSpec("https://x.com/", "home", "Home", None, "front-page", "published",
                    [Block("paragraph", {"text": "hi"})], GridNode("container"), "fp")
    page.screenshot_src = str(src)
    sc = SiteCharacterization(site=SiteSpec("x.com","X","","crawl","d",{},[],["home"],[]),
                              theme=ThemeSpec(), pages=[page], components=[], plugins=[])
    out = write_characterization(sc, tmp_path / "bundle")
    assert (out / "pages" / "home" / "screenshot.png").read_bytes() == b"PNG"
    pm = (out / "pages" / "home" / "page.md").read_text()
    assert "screenshot: screenshot.png" in pm
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/characterize/test_writer.py::test_screenshot_copied_and_referenced -v`
Expected: FAIL (`PageSpec` has no `screenshot_src`; writer doesn't copy/reference)

- [ ] **Step 3: Write minimal implementation**

In `characterize/models.py`, add the field to `PageSpec` (after `fingerprint`):

```python
    screenshot_src: Optional[str] = None   # absolute source path; copied by the writer, not serialized
```

(Leave `to_dict`/`from_dict` unchanged so it is not emitted into `characterization.json`.)

In `characterize/writer.py`, inside the per-page loop, after writing `page.md`'s base content, change
the `page.md` write to include the screenshot ref and copy the file:

```python
        import shutil
        page_fm = {"url": p.url, "slug": p.slug, "title": p.title, "parent": p.parent,
                   "template": p.template, "status": p.status,
                   "content_ref": "content.md", "layout_ref": "layout.md"}
        if getattr(p, "screenshot_src", None):
            page_fm["screenshot"] = "screenshot.png"
            shutil.copyfile(p.screenshot_src, pdir / "screenshot.png")
        (pdir / "page.md").write_text(_md(page_fm, p.title, f"Page: {p.title}."))
```

In `characterize/characterizer.py`, add a `screenshot_dir=None` keyword to `run_characterize`, pass it
to the `Renderer` used in `main()` (and accept an injected renderer in tests as before), and set
`screenshot_src` when building each `PageSpec`: add `, screenshot_src=getattr(rp, "screenshot_path", None)`
to the `PageSpec(...)` construction. (No behavior change when the injected renderer returns
`screenshot_path=None`.)

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/characterize/test_writer.py tests/characterize/test_characterizer.py -v`
Expected: PASS (new writer test + existing tests green)

- [ ] **Step 5: Commit**

```bash
git add characterize/models.py characterize/writer.py characterize/characterizer.py tests/characterize/
git commit -m "feat(characterize): copy per-page screenshot into spec + page.md reference"
```

---

### Task 6: Opt-in re-validation against the local WP mock

**Files:**
- Create: `tests/characterize/test_integration_crawl_quality.py`
- Test: as above (opt-in; skips by default)

**Interfaces:**
- Consumes: `run_characterize`, `Renderer`, `discover_pages`.
- Produces: an opt-in (`RUN_INTEGRATION=1`) integration that characterizes `http://localhost:8080/`
  into a temp dir (with a `screenshot_dir`) and asserts the Task-1/4 fixes hold on the real mock: no
  `"Posted in"` text in any `content.md`, a `screenshot.png` exists for at least one page, and the
  homepage page has `template: front-page`.

- [ ] **Step 1: Write the opt-in integration test**

```python
# tests/characterize/test_integration_crawl_quality.py
import os, json
import pytest
pytestmark = pytest.mark.skipif(os.environ.get("RUN_INTEGRATION") != "1",
                                reason="integration: needs the local WP mock + browser")

def test_crawl_quality_on_local_mock(tmp_path):
    from characterize.characterizer import run_characterize
    from capture.renderer import Renderer
    from capture.discovery import discover_pages
    out = run_characterize("http://localhost:8080/", "localmock", tmp_path, max_pages=25,
                           renderer=Renderer(screenshot_dir=str(tmp_path / "shots")),
                           discover=discover_pages, captured_at="2026-06-24")
    contents = list((out / "pages").rglob("content.md"))
    assert contents, "no pages characterized"
    assert all("Posted in" not in p.read_text() for p in contents)        # chrome stripped
    assert list((out).rglob("screenshot.png"))                            # screenshots present
    idx = json.loads((out / "characterization.json").read_text())
    fronts = [p for p in idx["pages"] if p["template"] == "front-page"]
    assert all(p["slug"] in ("home", "") or p["url"].rstrip("/").endswith(":8080")
               for p in fronts)  # front-page is the homepage
```

- [ ] **Step 2: Run it (expect skip without the env var)**

Run: `uv run pytest tests/characterize/test_integration_crawl_quality.py -v`
Expected: SKIPPED (1 skipped). Live gate: `RUN_INTEGRATION=1 uv run pytest tests/characterize/test_integration_crawl_quality.py` with the WP mock up.

- [ ] **Step 3: (no implementation — this is a validation gate)**

The prior tasks implement the behavior; this task only adds the opt-in gate. If the live run fails,
file the gap against the relevant task rather than weakening the assertion.

- [ ] **Step 4: Run the full suite**

Run: `uv run pytest -q`
Expected: all prior green + 3 skips total (the two existing opt-in integrations + this one).

- [ ] **Step 5: Commit**

```bash
git add tests/characterize/test_integration_crawl_quality.py
git commit -m "test(characterize): opt-in re-validation of crawl-quality fixes on local mock"
```

---

## Self-Review

**1. Spec coverage (against Phase B spec §9, §2.5, §6 + Phase A validation backlog):**
- Chrome-stripping (spec §9) → Task 1. ✔ · Duplicate-heading (validation backlog) → Task 1. ✔
- Front-page anchoring (validation backlog) → Task 2. ✔
- Form-field inference quality (validation backlog) → Task 3. ✔
- Screenshots from render (spec §2.5, §5) → Task 4 (capture) + Task 5 (spec wiring). ✔
- `page.md` `screenshot:` frontmatter + `pages/<slug>/screenshot.png` (spec §6) → Task 5. ✔
- Re-validation on the real mock → Task 6 (opt-in). ✔
- NOTE: the *shared-renderer-for-backend* + *content-fallback rendering* (spec §5) belong to Plan B2
  (backend), not B1 — B1 only adds screenshot capture to the existing renderer. Flagged, not omitted.

**2. Placeholder scan:** No "TBD/handle edge cases" in steps. (Fixed a stray self-correction note in
Task 4's Files line — target is `tests/capture/test_renderer.py`.)

**3. Type consistency:** `Block`, `RenderedPage` (`.screenshot_path`), `PageSpec` (`+screenshot_src`),
`Renderer(screenshot_dir=)`, `run_characterize(..., screenshot_dir=)`, `write_characterization` used
consistently. `_form_fields` returns dicts with `label`/`type` (+ `options` for groups) consumed by
`infer_plugins` unchanged.

---

## Notes & Deferred (to Plan B2)
- Shared-renderer promotion + content-fallback rendering for page-builder/classic content (spec §5,§6).
- The PHP `sitecap-extractor` plugin, the `BackendExtractor` adapter, the golden mock, and the
  comparison harness (spec §3,§4,§7,§8).
