# capture/discovery.py
from urllib.parse import urljoin, urlparse
import re

def _norm_domain(netloc: str) -> str:
    return netloc.lower().removeprefix("www.")

def _default_fetch(url: str) -> str:
    import requests
    return requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"}).text

def discover_pages(base_url: str, max_pages: int = 50, fetch=_default_fetch) -> list[str]:
    domain = _norm_domain(urlparse(base_url).netloc)
    out: list[str] = []
    seen = set()
    def add(u):
        if u not in seen and _norm_domain(urlparse(u).netloc) == domain:
            seen.add(u); out.append(u)
    try:
        sm = fetch(base_url.rstrip("/") + "/sitemap.xml")
        locs = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", sm)
        for loc in locs:
            add(loc.strip())
    except Exception:
        locs = []
    if not out:
        add(base_url)
        try:
            home = fetch(base_url)
        except Exception:
            home = ""
        for href in re.findall(r'href=["\']([^"\']+)["\']', home):
            if href.startswith("#") or href.startswith("mailto:"):
                continue
            add(urljoin(base_url.rstrip("/") + "/", href))
    return out[:max_pages]
