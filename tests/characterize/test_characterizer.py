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
