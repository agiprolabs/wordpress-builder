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
