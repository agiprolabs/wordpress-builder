# capture/capture.py
import sys
from pathlib import Path
from urllib.parse import urlparse
from capture.models import Manifest, PageMeta, FidelityReport
from capture.content.extractor import extract_content
from capture.design.tokens import derive_tokens
from capture.design.llm import clean_tokens
from capture.design.theme_writer import write_theme
from capture.media import localize_media, rewrite_urls
from capture.bundle import write_bundle, BundlePaths

def _slugify(url: str, index: int) -> str:
    path = urlparse(url).path.strip("/")
    return path.replace("/", "-") or ("home" if index == 0 else f"page-{index}")

def run_capture(url, slug, out_root, max_pages=50, *, renderer, discover, llm_client=None) -> FidelityReport:
    urls = discover(url, max_pages=max_pages)
    pages, metas, snaps, all_assets = [], [], [], []
    for i, u in enumerate(urls):
        pslug = _slugify(u, i)
        try:
            rp = renderer.render(u, pslug)
            pc = extract_content(rp)
            pages.append(pc)
            snaps.extend(rp.computed)
            all_assets.extend(rp.assets)
            metas.append(PageMeta(url=u, slug=pslug, title=rp.title, status="ok"))
        except Exception:
            metas.append(PageMeta(url=u, slug=pslug, title=pslug, status="error"))
    tokens = clean_tokens(derive_tokens(snaps), client=llm_client)
    front = metas[0].slug if metas else "home"
    manifest = Manifest(site_title=(pages[0].title if pages else slug),
                        tagline="", front_page_slug=front, pages=metas)
    bdir = write_bundle(out_root, slug, pages, manifest, tokens)
    bp = BundlePaths(bdir)
    write_theme(tokens, bp.theme)
    mapping = localize_media(all_assets, bp.media)
    for pc in pages:
        f = bp.pages / f"{pc.slug}.html"
        f.write_text(rewrite_urls(f.read_text(), mapping))
    return FidelityReport(passed=False, content_ok=False,
                          page_results=[{"slug": m.slug, "status": m.status} for m in metas],
                          design_diff={})

def main(argv=None):
    argv = argv or sys.argv[1:]
    url = argv[0]
    slug = argv[1] if len(argv) > 1 else urlparse(url).netloc.replace(".", "-")
    from capture.renderer import Renderer
    from capture.discovery import discover_pages
    rep = run_capture(url, slug, Path("capture-out"), renderer=Renderer(), discover=discover_pages)
    print(f"Captured {len(rep.page_results)} pages to capture-out/{slug}")

if __name__ == "__main__":
    main()
