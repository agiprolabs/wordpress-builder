import json
from pathlib import Path
from capture.models import PageContent, Manifest, DesignTokens

class BundlePaths:
    def __init__(self, bundle_dir):
        self.dir = Path(bundle_dir)
        self.pages = self.dir / "pages"
        self.media = self.dir / "media"
        self.theme = self.dir / "theme"
        self.manifest = self.dir / "manifest.json"
        self.report = self.dir / "fidelity-report.json"
        self.tokens = self.dir / "design-tokens.json"

def write_bundle(root: Path, slug: str, pages, manifest: Manifest, tokens: DesignTokens) -> Path:
    bdir = Path(root) / slug
    bp = BundlePaths(bdir)
    for d in (bp.pages, bp.media, bp.theme):
        d.mkdir(parents=True, exist_ok=True)
    for pc in pages:
        (bp.pages / f"{pc.slug}.html").write_text(pc.block_html)
    bp.manifest.write_text(json.dumps(manifest.to_dict(), indent=2))
    bp.tokens.write_text(json.dumps(tokens.to_dict(), indent=2))
    return bdir
