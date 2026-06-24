from characterize.models import (Block, GridNode, PageSpec, SiteCharacterization,
                                  SiteSpec, ThemeSpec)

def test_block_frontmatter():
    b = Block("heading", {"level": 1, "text": "Hi"})
    assert b.to_frontmatter() == {"type": "heading", "level": 1, "text": "Hi"}
    assert Block.from_dict(b.to_frontmatter()) == b

def test_gridnode_recursive_roundtrip():
    g = GridNode("container", layout={"display": "flex"},
                 children=[GridNode("content", blocks_ref="content.md", area="main")])
    assert GridNode.from_dict(g.to_dict()) == g

def test_site_characterization_index():
    sc = SiteCharacterization(
        site=SiteSpec("x.com", "X", "", "crawl", "2026-06-24", {}, [], ["home"], []),
        theme=ThemeSpec({}, {}, [], {}, []),
        pages=[PageSpec("https://x.com/", "home", "Home", None, "front-page", "published",
                        [Block("paragraph", {"text": "hi"})], None, "fp")],
        components=[], plugins=[])
    idx = sc.to_index()
    assert idx["site"]["domain"] == "x.com"
    assert idx["pages"][0]["slug"] == "home"
    assert idx["spec_version"]
