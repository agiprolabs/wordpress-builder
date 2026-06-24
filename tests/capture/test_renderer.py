from capture.renderer import Renderer, ROLE_SELECTORS

class FakePage:
    def __init__(self): self.url = None
    def goto(self, url): self.url = url
    def content(self): return "<html><body><h1>Hi</h1><img src='/a.png'></body></html>"
    def title(self): return "Hi Page"
    def evaluate(self, js):
        if "ROLE_QUERY" in js:  # computed-style probe
            return [{"role": "h1", "selector": "h1", "styles": {"color": "rgb(0,0,0)"}}]
        return ["https://x.com/a.png"]  # asset probe

def test_render_collects_styles_and_assets():
    r = Renderer(page_factory=lambda: FakePage())
    page = r.render("https://x.com/", slug="home")
    assert page.title == "Hi Page"
    assert page.slug == "home"
    assert page.computed[0].role == "h1"
    assert "https://x.com/a.png" in page.assets

def test_role_selectors_cover_core_roles():
    for role in ("body", "h1", "a", "header", "footer", "button", "input"):
        assert role in ROLE_SELECTORS
