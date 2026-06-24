# tests/capture/test_discovery.py
from capture.discovery import discover_pages

SITEMAP = """<urlset><url><loc>https://x.com/</loc></url>
<url><loc>https://x.com/about/</loc></url></urlset>"""

def test_sitemap_used_when_present():
    def fake_fetch(url):
        return SITEMAP if url.endswith("sitemap.xml") else ""
    urls = discover_pages("https://x.com", fetch=fake_fetch)
    assert urls == ["https://x.com/", "https://x.com/about/"]

def test_falls_back_to_homepage_links():
    home = '<a href="/a/">A</a><a href="https://other.com/x">no</a><a href="/a/">dup</a>'
    def fake_fetch(url):
        if url.endswith("sitemap.xml"): raise RuntimeError("404")
        return home
    urls = discover_pages("https://x.com", fetch=fake_fetch)
    assert urls == ["https://x.com", "https://x.com/a/"]
