# capture/content/extractor.py
from bs4 import BeautifulSoup
from capture.models import RenderedPage, PageContent
from capture.content import blocks
from capture.content.fingerprint import content_fingerprint

_MAIN_SELECTORS = ["main", "#left-area", "#content-area", "#content", "article", ".entry-content"]
_CHROME = ["header", "nav", "footer", "aside", "script", "style", "#header", "#sidebar"]
_FORM_SELECTORS = ['[id^="gform_"]', ".gform_wrapper", "form#searchform"]

def _main_region(soup):
    for sel in _MAIN_SELECTORS:
        el = soup.select_one(sel)
        if el:
            return el
    return soup.body or soup

def extract_content(page: RenderedPage) -> PageContent:
    soup = BeautifulSoup(page.html, "lxml")
    region = _main_region(soup)
    for sel in _CHROME:
        for el in region.select(sel):
            el.decompose()
    out: list[str] = []
    placeholders: list[str] = []
    for node in region.find_all(["h1", "h2", "h3", "h4", "p", "ul", "ol", "img", "div", "form"], recursive=True):
        # form / plugin detection first
        classes = " ".join(node.get("class", []))
        node_id = node.get("id", "")
        if node.name == "form" or "gform_wrapper" in classes or node_id.startswith("gform_"):
            if "gravity-form" not in placeholders:
                placeholders.append("gravity-form")
                out.append(blocks.placeholder_block("gravity-form"))
            continue
        if node.name in ("h1", "h2", "h3", "h4"):
            text = node.get_text(" ", strip=True)
            if text:
                out.append(blocks.heading_block(int(node.name[1]), text))
        elif node.name == "p":
            text = node.get_text(" ", strip=True)
            if text:
                out.append(blocks.paragraph_block(text))
        elif node.name in ("ul", "ol"):
            items = [li.get_text(" ", strip=True) for li in node.find_all("li", recursive=False)]
            items = [i for i in items if i]
            if items:
                out.append(blocks.list_block(items, ordered=(node.name == "ol")))
        elif node.name == "img" and node.get("src"):
            out.append(blocks.image_block(node["src"], node.get("alt", "")))
    block_html = "\n\n".join(out)
    return PageContent(slug=page.slug, title=page.title, block_html=block_html,
                       fingerprint=content_fingerprint(block_html), placeholders=placeholders)
