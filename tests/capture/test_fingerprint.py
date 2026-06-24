from capture.content.fingerprint import content_fingerprint

def test_whitespace_insensitive():
    a = "<!-- wp:heading -->\n<h2 class='x'>Hello   World</h2>\n<!-- /wp:heading -->"
    b = "<!-- wp:heading -->\n<h2>Hello World</h2>\n<!-- /wp:heading -->"
    assert content_fingerprint(a) == content_fingerprint(b)

def test_different_text_differs():
    a = "<p>Get Started</p>"
    b = "<p>Get Going</p>"
    assert content_fingerprint(a) != content_fingerprint(b)
