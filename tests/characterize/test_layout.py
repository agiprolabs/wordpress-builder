# tests/characterize/test_layout.py
from capture.models import RenderedPage
from characterize.layout import build_grid_tree

def _page(body):
    return RenderedPage(url="u", slug="p", title="P", html=f"<html><body>{body}</body></html>")

def test_grid_with_header_main_sidebar_footer():
    html = ('<div id="header">H</div>'
            '<div id="content-area"><div id="left-area"><p>x</p></div><div id="sidebar">S</div></div>'
            '<div id="footer">F</div>')
    g = build_grid_tree(_page(html))
    assert g.node == "container" and g.layout["direction"] == "column"
    kinds = [c.node for c in g.children]
    assert kinds[0] == "component"          # header
    assert kinds[-1] == "component"          # footer
    row = [c for c in g.children if c.node == "container"][0]
    areas = {c.area for c in row.children}
    assert {"main", "aside"} <= areas

def test_grid_without_sidebar_has_single_content():
    html = '<div id="content-area"><div id="left-area"><p>x</p></div></div>'
    g = build_grid_tree(_page(html))
    row = [c for c in g.children if c.node == "container"][0]
    assert [c.node for c in row.children] == ["content"]
