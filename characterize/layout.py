# characterize/layout.py
from bs4 import BeautifulSoup
from characterize.models import GridNode

def build_grid_tree(page) -> GridNode:
    soup = BeautifulSoup(page.html, "lxml")
    children = []
    if soup.select_one("header, #header, .site-header"):
        children.append(GridNode("component", ref="components/header.md"))
    has_sidebar = soup.select_one("#sidebar, aside") is not None
    if has_sidebar:
        row = GridNode("container", layout={"display": "grid", "columns": "1fr 300px", "gap": "24px"},
                       children=[GridNode("content", blocks_ref="content.md", area="main"),
                                 GridNode("component", ref="components/sidebar.md", area="aside")])
    else:
        row = GridNode("container", layout={"display": "grid", "columns": "1fr"},
                       children=[GridNode("content", blocks_ref="content.md", area="main")])
    children.append(row)
    if soup.select_one("footer, #footer, .site-footer"):
        children.append(GridNode("component", ref="components/footer.md"))
    return GridNode("container", layout={"display": "flex", "flex-direction": "column"}, children=children)
