from bs4 import BeautifulSoup
from capture.models import RenderedPage, PageContent
from capture.content import blocks
from capture.content.fingerprint import content_fingerprint

_MAIN_SELECTORS = ["main", "#left-area", "#content-area", "#content", "article", ".entry-content"]
_CHROME = ["header", "nav", "footer", "aside", "script", "style", "#header", "#sidebar"]


def _main_region(soup):
    for sel in _MAIN_SELECTORS:
        el = soup.select_one(sel)
        if el:
            return el
    return soup.body or soup


def _is_form(node, classes, node_id):
    return node.name == "form" or "gform_wrapper" in classes or node_id.startswith("gform_")


def _walk(node, out, placeholders):
    for child in node.children:
        name = getattr(child, "name", None)
        if not name:
            continue  # NavigableString / comment
        classes = " ".join(child.get("class", []))
        node_id = child.get("id", "")
        if _is_form(child, classes, node_id):
            if "gravity-form" not in placeholders:
                placeholders.append("gravity-form")
                out.append(blocks.placeholder_block("gravity-form"))
            continue  # do not descend into a form
        if name in ("h1", "h2", "h3", "h4", "h5", "h6"):
            text = child.get_text(" ", strip=True)
            if text:
                out.append(blocks.heading_block(int(name[1]), text))
            continue
        if name == "p":
            text = child.get_text(" ", strip=True)
            if text:
                out.append(blocks.paragraph_block(text))
            continue
        if name in ("ul", "ol"):
            items = [li.get_text(" ", strip=True) for li in child.find_all("li", recursive=False)]
            items = [i for i in items if i]
            if items:
                out.append(blocks.list_block(items, ordered=(name == "ol")))
            continue  # handled wholesale; do not descend
        if name == "img" and child.get("src"):
            out.append(blocks.image_block(child["src"], child.get("alt", "")))
            continue
        # generic container (div/section/etc.) — descend to find content leaves
        _walk(child, out, placeholders)


def extract_content(page: RenderedPage) -> PageContent:
    soup = BeautifulSoup(page.html, "lxml")
    region = _main_region(soup)
    for sel in _CHROME:
        for el in region.select(sel):
            el.decompose()
    out: list[str] = []
    placeholders: list[str] = []
    _walk(region, out, placeholders)
    block_html = "\n\n".join(out)
    return PageContent(slug=page.slug, title=page.title, block_html=block_html,
                       fingerprint=content_fingerprint(block_html), placeholders=placeholders)
