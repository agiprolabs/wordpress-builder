from characterize.models import (Block, GridNode, PageSpec, ComponentSpec, PluginSpec,
                                  SiteCharacterization, SiteSpec, ThemeSpec)

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

def test_page_spec_roundtrip():
    from characterize.models import PageSpec
    p = PageSpec("https://x.com/", "home", "Home", None, "front-page", "published",
                 [Block("heading", {"level": 1, "text": "Hi"})],
                 GridNode("container", layout={"display": "flex"}), "fp")
    assert PageSpec.from_dict(p.to_dict()).to_dict() == p.to_dict()

def test_site_characterization_index_roundtrip():
    sc = SiteCharacterization(
        site=SiteSpec("x.com", "X", "", "crawl", "2026-06-24", {}, [], ["home"], []),
        theme=ThemeSpec({"background": "#fff"}, {}, [8], {"container_width": "960px"}, []),
        pages=[PageSpec("https://x.com/", "home", "Home", None, "front-page", "published",
                        [Block("paragraph", {"text": "hi"})], GridNode("container"), "fp")],
        components=[], plugins=[])
    assert SiteCharacterization.from_index(sc.to_index()).to_index() == sc.to_index()
