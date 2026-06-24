# capture/discovery.py
from urllib.parse import urljoin, urlparse
import re

def _norm_domain(netloc: str) -> str:
    return netloc.lower().removeprefix("www.")

def _default_fetch(url: str) -> str:
    import requests
    return requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"}).text

def _is_page_url(u: str) -> bool:
    # exclude sitemaps/feeds and other non-HTML resources
    return not u.lower().split("?")[0].rstrip("/").endswith(".xml")

def _locs(xml: str) -> list[str]:
    return [l.strip() for l in re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", xml)]

def discover_pages(base_url: str, max_pages: int = 50, fetch=_default_fetch) -> list[str]:
    domain = _norm_domain(urlparse(base_url).netloc)
    base = base_url.rstrip("/")
    out: list[str] = []
    seen = set()
    def add(u):
        if u not in seen and _norm_domain(urlparse(u).netloc) == domain and _is_page_url(u):
            seen.add(u); out.append(u)
    # Try common sitemap locations. WordPress core serves a sitemap INDEX at
    # /wp-sitemap.xml whose <loc> entries are sub-sitemaps, not pages — recurse one level.
    for sm_url in (base + "/sitemap.xml", base + "/wp-sitemap.xml"):
        try:
            locs = _locs(fetch(sm_url))
        except Exception:
            continue
        for loc in locs:
            if loc.lower().split("?")[0].endswith(".xml"):   # sub-sitemap -> recurse
                try:
                    for sub in _locs(fetch(loc)):
                        add(sub)
                except Exception:
                    continue
            else:
                add(loc)
        if out:
            break
    if not out:
        add(base_url)
        try:
            home = fetch(base_url)
        except Exception:
            home = ""
        for href in re.findall(r'href=["\']([^"\']+)["\']', home):
            if href.startswith("#") or href.startswith("mailto:"):
                continue
            add(urljoin(base + "/", href))
    return out[:max_pages]
