import json
import os
from capture.models import RenderedPage, ComputedStyleSnapshot

ROLE_SELECTORS = {
    "body": "body", "h1": "h1", "h2": "h2", "h3": "h3", "a": "a",
    "header": "header, #header, .site-header", "footer": "footer, #footer",
    "button": "button, .button, input[type=submit]", "input": "input, textarea, select",
    "container": ".container, main, #content, #content-area",
}

_ROLE_JS = """
() => {  /* ROLE_QUERY */
  const map = %s;
  const props = ['color','background-color','font-family','font-size','font-weight',
    'line-height','margin','padding','width','max-width','height','border'];
  const out = [];
  for (const [role, sel] of Object.entries(map)) {
    const el = document.querySelector(sel);
    if (!el) continue;
    const cs = getComputedStyle(el); const styles = {};
    for (const p of props) styles[p] = cs.getPropertyValue(p);
    out.push({role, selector: sel, styles});
  }
  return out;
}
"""

_ASSET_JS = """
() => {
  const urls = new Set();
  document.querySelectorAll('img[src]').forEach(i => urls.add(i.src));
  document.querySelectorAll('link[href]').forEach(l => urls.add(l.href));
  document.querySelectorAll('*').forEach(el => {
    const bg = getComputedStyle(el).backgroundImage;
    const m = bg && bg.match(/url\\(["']?([^"')]+)["']?\\)/);
    if (m) urls.add(m[1]);
  });
  return [...urls];
}
"""

def _default_page_factory():
    from playwright.sync_api import sync_playwright
    pw = sync_playwright().start()
    browser = pw.chromium.launch()
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    page._pw = pw
    page._browser = browser
    return page

class Renderer:
    def __init__(self, page_factory=_default_page_factory, screenshot_dir=None):
        self._page_factory = page_factory
        self._page = None
        self._screenshot_dir = screenshot_dir

    def _page_obj(self):
        if self._page is None:
            self._page = self._page_factory()
        return self._page

    def render(self, url: str, slug: str) -> RenderedPage:
        page = self._page_obj()
        page.goto(url)
        html = page.content()
        title = page.title()
        raw_styles = page.evaluate(_ROLE_JS % json.dumps(ROLE_SELECTORS))
        assets = page.evaluate(_ASSET_JS)
        computed = [ComputedStyleSnapshot(**s) for s in raw_styles]

        screenshot_path = None
        shot = getattr(page, "screenshot", None)
        if self._screenshot_dir and callable(shot):
            os.makedirs(self._screenshot_dir, exist_ok=True)
            screenshot_path = os.path.join(self._screenshot_dir, f"{slug}.png")
            try:
                shot(path=screenshot_path, full_page=True)
            except Exception:
                screenshot_path = None

        return RenderedPage(url=url, slug=slug, title=title, html=html,
                            computed=computed, assets=list(assets), screenshot_path=screenshot_path)

    def close(self):
        page = self._page
        if page is None:
            return
        browser = getattr(page, "_browser", None)
        pw = getattr(page, "_pw", None)
        if browser is not None:
            try: browser.close()
            except Exception: pass
        if pw is not None:
            try: pw.stop()
            except Exception: pass
        self._page = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
