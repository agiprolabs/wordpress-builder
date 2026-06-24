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

def test_close_releases_browser_and_pw():
    class FakeBrowser:
        def __init__(self):
            self.closed = False
        def close(self):
            self.closed = True

    class FakePW:
        def __init__(self):
            self.stopped = False
        def stop(self):
            self.stopped = True

    class FakePageWithHandles:
        def __init__(self):
            self.url = None
            self._browser = FakeBrowser()
            self._pw = FakePW()
        def goto(self, url): self.url = url
        def content(self): return "<html><body><h1>Hi</h1><img src='/a.png'></body></html>"
        def title(self): return "Hi Page"
        def evaluate(self, js):
            if "ROLE_QUERY" in js:
                return [{"role": "h1", "selector": "h1", "styles": {"color": "rgb(0,0,0)"}}]
            return ["https://x.com/a.png"]

    fake_page = FakePageWithHandles()
    r = Renderer(page_factory=lambda: fake_page)
    r.render("https://x.com/", slug="home")
    assert r._page is not None
    r.close()
    assert r._page is None
    assert fake_page._browser.closed
    assert fake_page._pw.stopped

def test_close_without_render_is_noop():
    r = Renderer(page_factory=lambda: None)
    r.close()  # Should not raise
    assert r._page is None
