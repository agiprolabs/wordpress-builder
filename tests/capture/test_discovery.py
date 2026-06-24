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

def test_www_and_bare_domain_treated_same():
    # Sitemap uses www.x.com, but base_url is bare x.com
    sitemap_with_www = """<urlset><url><loc>https://www.x.com/</loc></url>
<url><loc>https://www.x.com/page/</loc></url></urlset>"""
    def fake_fetch(url):
        return sitemap_with_www if url.endswith("sitemap.xml") else ""
    urls = discover_pages("https://x.com", fetch=fake_fetch)
    assert urls == ["https://www.x.com/", "https://www.x.com/page/"]

def test_max_pages_cap():
    # Sitemap has 3 URLs but max_pages=2
    sitemap = """<urlset><url><loc>https://x.com/</loc></url>
<url><loc>https://x.com/a/</loc></url>
<url><loc>https://x.com/b/</loc></url></urlset>"""
    def fake_fetch(url):
        return sitemap if url.endswith("sitemap.xml") else ""
    urls = discover_pages("https://x.com", max_pages=2, fetch=fake_fetch)
    assert len(urls) == 2
    assert urls == ["https://x.com/", "https://x.com/a/"]

def test_sitemap_index_is_recursed_not_treated_as_pages():
    # WordPress core: /sitemap.xml is an INDEX whose <loc>s are sub-sitemap .xml files.
    INDEX = ("<sitemapindex><sitemap><loc>https://x.com/wp-sitemap-posts-page-1.xml</loc>"
             "</sitemap></sitemapindex>")
    SUB = ("<urlset><url><loc>https://x.com/</loc></url>"
           "<url><loc>https://x.com/about/</loc></url></urlset>")
    def fake_fetch(url):
        if url.endswith("wp-sitemap-posts-page-1.xml"): return SUB
        if url.endswith("sitemap.xml"): return INDEX
        return ""
    urls = discover_pages("https://x.com", fetch=fake_fetch)
    assert urls == ["https://x.com/", "https://x.com/about/"]
    assert all(not u.endswith(".xml") for u in urls)   # no sub-sitemap urls leak as pages

def test_xml_resource_urls_filtered_from_pages():
    SM = ("<urlset><url><loc>https://x.com/</loc></url>"
          "<url><loc>https://x.com/feed.xml</loc></url></urlset>")
    def fake_fetch(url):
        return SM if url.endswith("sitemap.xml") else ""
    urls = discover_pages("https://x.com", fetch=fake_fetch)
    assert "https://x.com/" in urls
    assert "https://x.com/feed.xml" not in urls
