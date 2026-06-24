# characterize/characterizer.py
import logging
import sys
from pathlib import Path
from urllib.parse import urlparse
from capture.content.extractor import extract_blocks, fingerprint_blocks
from characterize.layout import build_grid_tree
from characterize.components import detect_components
from characterize.plugins import infer_plugins
from characterize.theme import build_theme_spec
from characterize.writer import write_characterization
from characterize.models import SiteCharacterization, SiteSpec, PageSpec

_log = logging.getLogger(__name__)

def _slug(url, i):
    p = urlparse(url).path.strip("/")
    return p.replace("/", "-") or ("home" if i == 0 else f"page-{i}")

def run_characterize(url, slug, out_root, max_pages=50, *, renderer, discover,
                     llm_client=None, captured_at="") -> Path:
    urls = discover(url, max_pages=max_pages)
    rendered, pages, snaps = [], [], []
    try:
        for i, u in enumerate(urls):
            ps = _slug(u, i)
            try:
                rp = renderer.render(u, ps)
            except Exception as e:
                _log.warning("characterize: skipping %s (render failed: %s)", u, e)
                continue
            rendered.append(rp)
            snaps.extend(rp.computed)
            blocks = extract_blocks(rp)
            pages.append(PageSpec(url=u, slug=ps, title=rp.title, parent=None,
                                  template=("front-page" if i == 0 else "page"), status="published",
                                  blocks=blocks, grid=build_grid_tree(rp), fingerprint=fingerprint_blocks(blocks)))
        components = detect_components(rendered)
        plugins = infer_plugins(rendered)
        theme = build_theme_spec(snaps)
        domain = urlparse(url).netloc
        site = SiteSpec(domain=domain, title=(pages[0].title if pages else slug), tagline="",
                        source="crawl", captured_at=captured_at, detected_stack={},
                        nav=[], pages=[p.slug for p in pages], plugins=[pl.slug for pl in plugins])
        sc = SiteCharacterization(site=site, theme=theme, pages=pages,
                                  components=components, plugins=plugins)
        out_dir = Path(out_root) / slug
        write_characterization(sc, out_dir)
        return out_dir
    finally:
        close = getattr(renderer, "close", None)
        if callable(close):
            close()

def main(argv=None):
    argv = argv or sys.argv[1:]
    url = argv[0]
    slug = argv[1] if len(argv) > 1 else urlparse(url).netloc.replace(".", "-")
    from capture.renderer import Renderer
    from capture.discovery import discover_pages
    out = run_characterize(url, slug, Path("characterization"), renderer=Renderer(), discover=discover_pages)
    print(f"Characterized to {out}")

if __name__ == "__main__":
    main()
