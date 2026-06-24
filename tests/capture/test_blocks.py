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

def test_image_block_alt_and_close():
    out = blocks.image_block("/x.png", "alt")
    assert 'alt="alt"' in out
    assert out.endswith("<!-- /wp:image -->")
    # alt is HTML-escaped
    assert 'alt="&lt;script&gt;"' in blocks.image_block("/x.png", "<script>")

def test_list_block_unordered_ordered_escape_empty():
    assert blocks.list_block(["a", "b"]) == (
        '<!-- wp:list -->\n<ul><li>a</li><li>b</li></ul>\n<!-- /wp:list -->'
    )
    assert blocks.list_block(["a"], ordered=True) == (
        '<!-- wp:list {"ordered":true} -->\n<ol><li>a</li></ol>\n<!-- /wp:list -->'
    )
    # items are HTML-escaped
    assert "<li>&lt;b&gt;</li>" in blocks.list_block(["<b>"])
    # empty list still produces a valid (empty) ul
    assert "<ul></ul>" in blocks.list_block([])
