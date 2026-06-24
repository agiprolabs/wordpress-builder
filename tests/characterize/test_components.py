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

def test_skips_region_with_differing_text():
    # header present on BOTH pages but with DIFFERENT content -> not a shared component
    pages = [_p("home", '<div id="header">WELCOME HOME</div><main>a</main>'),
             _p("about", '<div id="header">ABOUT US</div><main>b</main>')]
    assert "header" not in {c.name for c in detect_components(pages)}
