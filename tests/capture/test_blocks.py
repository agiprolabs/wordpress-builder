from capture.content import blocks

def test_heading_block():
    assert blocks.heading_block(2, "Hi & Bye") == (
        '<!-- wp:heading {"level":2} -->\n'
        '<h2 class="wp-block-heading">Hi &amp; Bye</h2>\n'
        '<!-- /wp:heading -->'
    )

def test_paragraph_and_image():
    assert blocks.paragraph_block("a") == '<!-- wp:paragraph -->\n<p>a</p>\n<!-- /wp:paragraph -->'
    assert 'src="/x.png"' in blocks.image_block("/x.png", "alt")
    assert blocks.image_block("/x.png", "alt").startswith("<!-- wp:image")

def test_placeholder_block_is_flagged():
    out = blocks.placeholder_block("gravity-form")
    assert "CAPTURE-PLACEHOLDER: gravity-form" in out
    assert out.startswith("<!-- wp:html -->")
