import os
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
