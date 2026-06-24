# tests/capture/test_integration_armand.py
import os
import pytest
from pathlib import Path

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_INTEGRATION") != "1",
    reason="integration: needs Docker + network",
)


def test_armand_gilbert_content_is_exact(tmp_path):
    from capture.capture import run_capture
    from capture.renderer import Renderer
    from capture.discovery import discover_pages

    rep = run_capture(
        "https://armandgilbert.com/",
        "armand",
        tmp_path,
        max_pages=8,
        renderer=Renderer(),
        discover=discover_pages,
    )
    gs = tmp_path / "armand" / "pages" / "get-started.html"
    assert gs.exists()
    body = gs.read_text()
    # regression: the previously-dropped title + intro copy must be captured
    assert "Get Started" in body
    assert "760-632-8258" in body
