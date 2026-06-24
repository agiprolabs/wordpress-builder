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

def test_renderer_closed_after_run(tmp_path):
    closed = []
    class R:
        def render(self, url, slug):
            return RenderedPage(url=url, slug=slug, title="T",
                                html="<main><p>x</p></main>", computed=[], assets=[])
        def close(self):
            closed.append(True)
    run_capture("https://x.com/", "site_close", tmp_path,
                renderer=R(), discover=lambda url, max_pages: ["https://x.com/"])
    assert closed == [True]
