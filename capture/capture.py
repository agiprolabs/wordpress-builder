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
from capture.installer import WP_UPLOADS_URL

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
    close = getattr(renderer, "close", None)
    if callable(close):
        close()
    tokens = clean_tokens(derive_tokens(snaps), client=llm_client)
    front = metas[0].slug if metas else "home"
    manifest = Manifest(site_title=(pages[0].title if pages else slug),
                        tagline="", front_page_slug=front, pages=metas)
    bdir = write_bundle(out_root, slug, pages, manifest, tokens)
    bp = BundlePaths(bdir)
    write_theme(tokens, bp.theme)
    mapping = localize_media(all_assets, bp.media, url_prefix=WP_UPLOADS_URL)
    for pc in pages:
        f = bp.pages / f"{pc.slug}.html"
        f.write_text(rewrite_urls(f.read_text(), mapping))
    # also localize any source URLs embedded in the derived theme (e.g. CSS bg images)
    for tf in bp.theme.rglob("*"):
        if tf.is_file() and tf.suffix in (".css", ".json", ".html"):
            tf.write_text(rewrite_urls(tf.read_text(), mapping))
    return FidelityReport(passed=False, content_ok=False,
                          page_results=[{"slug": m.slug, "status": m.status} for m in metas],
                          design_diff={})

def main(argv=None):
    import json as _json
    argv = argv or sys.argv[1:]
    url = argv[0]
    slug = argv[1] if len(argv) > 1 else urlparse(url).netloc.replace(".", "-")
    from capture.renderer import Renderer
    from capture.discovery import discover_pages
    out_root = Path("capture-out")
    rep = run_capture(url, slug, out_root, renderer=Renderer(), discover=discover_pages)
    print(f"Captured {len(rep.page_results)} pages to capture-out/{slug}")

    # --- install + verify (best-effort; skipped gracefully if Docker is unavailable) ---
    bundle = out_root / slug
    try:
        from capture.installer import WPInstaller
        from capture.verify import verify_site

        WPInstaller().install(bundle)
        print(f"Installed bundle to local WordPress at http://localhost:8080/")

        # Re-render each captured page from localhost and from the original URL,
        # then build fingerprint dicts for verify_site.
        renderer = Renderer()
        try:
            orig_pages: dict = {}
            cap_pages: dict = {}
            orig_snaps: list = []
            cap_snaps: list = []

            bp = BundlePaths(bundle)
            man_data = _json.loads(bp.manifest.read_text())
            from capture.models import Manifest
            man = Manifest.from_dict(man_data)

            for meta in man.pages:
                # Render the original live URL
                try:
                    orig_rp = renderer.render(meta.url, meta.slug)
                    orig_pc = extract_content(orig_rp)
                    orig_pages[meta.slug] = orig_pc.fingerprint
                    orig_snaps.extend(orig_rp.computed)
                except Exception as exc:
                    print(f"  [warn] could not render original {meta.url}: {exc}")

                # Render the captured localhost equivalent
                local_url = f"http://localhost:8080/{meta.slug}/"
                try:
                    cap_rp = renderer.render(local_url, meta.slug)
                    cap_pc = extract_content(cap_rp)
                    cap_pages[meta.slug] = cap_pc.fingerprint
                    cap_snaps.extend(cap_rp.computed)
                except Exception as exc:
                    print(f"  [warn] could not render captured {local_url}: {exc}")

            orig_tokens = derive_tokens(orig_snaps)
            cap_tokens = derive_tokens(cap_snaps)

            report = verify_site(orig_pages, cap_pages, orig_tokens, cap_tokens)
            bp.report.write_text(_json.dumps(report.to_dict(), indent=2))
            status = "PASSED" if report.passed else "FAILED"
            print(f"Fidelity verification {status}. Report: {bp.report}")
        finally:
            close = getattr(renderer, "close", None)
            if callable(close):
                close()

    except Exception as exc:
        print(f"Install/verify skipped (Docker may not be available): {exc}")

if __name__ == "__main__":
    main()
