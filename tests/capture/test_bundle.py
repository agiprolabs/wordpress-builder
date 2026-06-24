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
