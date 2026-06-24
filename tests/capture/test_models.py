from capture.models import RenderedPage, ComputedStyleSnapshot, PageContent, DesignTokens

def test_rendered_page_json_roundtrip():
    p = RenderedPage(
        url="https://x.com/a", slug="a", title="A", html="<h1>A</h1>",
        computed=[ComputedStyleSnapshot(role="h1", selector="h1", styles={"color": "rgb(0,0,0)"})],
        assets=["https://x.com/i.png"], screenshot_path=None,
    )
    again = RenderedPage.from_dict(p.to_dict())
    assert again == p
    assert again.computed[0].role == "h1"

def test_design_tokens_defaults():
    t = DesignTokens(palette={"background": "#ffffff"}, fonts={"body": "Inter, sans-serif"},
                     spacing=[8, 16, 24], container_width=960, header_height=165, raw={})
    assert DesignTokens.from_dict(t.to_dict()) == t
