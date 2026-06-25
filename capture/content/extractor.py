# capture/content/extractor.py
import hashlib, re
from bs4 import BeautifulSoup
from capture.models import RenderedPage, PageContent, Block
from capture.content import blocks as wp

_MAIN_SELECTORS = ["main", "#left-area", "#content-area", "#content", "article", ".entry-content"]
_CHROME = ["header", "nav", "footer", "aside", "script", "style", "#header", "#sidebar",
           ".post-meta", ".entry-meta", ".posted-on", ".post-categories", ".entry-footer"]

# Legacy WP-placeholder slug: existing capture tests assert singular "gravity-form".
# The neutral Block uses the canonical "gravity-forms". Remove this mapping once those
# tests are updated to the canonical slug.
_WP_PLUGIN_NAME = {
    "gravity-forms": "gravity-form",
}


def _main_region(soup):
    for sel in _MAIN_SELECTORS:
        el = soup.select_one(sel)
        if el:
            return el
    return soup.body or soup


def _is_form(node, classes, node_id):
    return node.name == "form" or "gform_wrapper" in classes or node_id.startswith("gform_")


def _walk(node, out, seen_plugin):
    for child in node.children:
        name = getattr(child, "name", None)
        if not name:
            continue
        classes = " ".join(child.get("class", []))
        node_id = child.get("id", "")
        if _is_form(child, classes, node_id):
            if not seen_plugin[0]:
                seen_plugin[0] = True
                out.append(Block("plugin", {"plugin": "gravity-forms", "ref": "plugins/gravity-forms.md"}))
            continue
        if name in ("h1", "h2", "h3", "h4", "h5", "h6"):
            text = child.get_text(" ", strip=True)
            if text:
                lvl = int(name[1])
                if out and out[-1].type == "heading" and out[-1].data.get("level") == lvl \
                        and out[-1].data.get("text", "").strip().lower() == text.strip().lower():
                    continue  # collapse consecutive identical heading
                out.append(Block("heading", {"level": lvl, "text": text}))
            continue
        if name == "p":
            t = child.get_text(" ", strip=True)
            if t:
                out.append(Block("paragraph", {"text": t}))
            continue
        if name in ("ul", "ol"):
            items = [li.get_text(" ", strip=True) for li in child.find_all("li", recursive=False)]
            items = [i for i in items if i]
            if items:
                out.append(Block("list", {"items": items, "ordered": name == "ol"}))
            continue
        if name == "img" and child.get("src"):
            out.append(Block("image", {"src": child["src"], "alt": child.get("alt", "")}))
            continue
        _walk(child, out, seen_plugin)


def extract_blocks(page: RenderedPage) -> list[Block]:
    soup = BeautifulSoup(page.html, "lxml")
    region = _main_region(soup)
    for sel in _CHROME:
        for el in region.select(sel):
            el.decompose()
    out, seen_plugin = [], [False]
    _walk(region, out, seen_plugin)
    return out


def fingerprint_blocks(blocks) -> str:
    parts = []
    for b in blocks:
        text = b.data.get("text", "") or " ".join(b.data.get("items", []) or [])
        text = re.sub(r"\s+", " ", text).strip().lower()
        parts.append(f"{b.type}:{text}")
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def _block_to_wp(b: Block) -> str:
    d = b.data
    if b.type == "heading":
        return wp.heading_block(d["level"], d["text"])
    if b.type == "paragraph":
        return wp.paragraph_block(d["text"])
    if b.type == "list":
        return wp.list_block(d["items"], d.get("ordered", False))
    if b.type == "image":
        return wp.image_block(d["src"], d.get("alt", ""))
    if b.type == "plugin":
        # Map neutral slug → legacy WP placeholder name for backward compatibility
        wp_name = _WP_PLUGIN_NAME.get(d.get("plugin", ""), d.get("plugin", "plugin"))
        return wp.placeholder_block(wp_name)
    return wp.html_block(d.get("html", ""))


def extract_content(page: RenderedPage) -> PageContent:
    blocks = extract_blocks(page)
    block_html = "\n\n".join(_block_to_wp(b) for b in blocks)
    # Map neutral plugin slugs to legacy WP placeholder names for placeholders list
    placeholders = [
        _WP_PLUGIN_NAME.get(b.data["plugin"], b.data["plugin"])
        for b in blocks if b.type == "plugin"
    ]
    return PageContent(slug=page.slug, title=page.title, block_html=block_html,
                       fingerprint=fingerprint_blocks(blocks), placeholders=placeholders)
