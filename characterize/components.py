from bs4 import BeautifulSoup
from characterize.models import ComponentSpec

_REGIONS = {"header": "header, #header, .site-header", "footer": "footer, #footer",
            "sidebar": "#sidebar, aside"}

def _region_text(html, sel):
    el = BeautifulSoup(html, "lxml").select_one(sel)
    return el.get_text(" ", strip=True) if el else None

def detect_components(pages) -> list[ComponentSpec]:
    out = []
    for name, sel in _REGIONS.items():
        texts = [_region_text(p.html, sel) for p in pages]
        present = [t for t in texts if t is not None]
        if present and len(present) == len(pages) and len(set(present)) == 1:
            out.append(ComponentSpec(name=name, appears_on="all", type="site-chrome", elements=[]))
    return out
