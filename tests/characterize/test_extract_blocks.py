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

def test_fingerprint_sensitive_to_heading_and_list():
    base = extract_blocks(_page("<main><h2>Title</h2><ul><li>A</li><li>B</li></ul></main>"))
    diff_heading = extract_blocks(_page("<main><h2>Other</h2><ul><li>A</li><li>B</li></ul></main>"))
    diff_list = extract_blocks(_page("<main><h2>Title</h2><ul><li>A</li><li>C</li></ul></main>"))
    assert fingerprint_blocks(base) != fingerprint_blocks(diff_heading)
    assert fingerprint_blocks(base) != fingerprint_blocks(diff_list)

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
