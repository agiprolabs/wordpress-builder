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
