import json, yaml
from pathlib import Path
from characterize.models import (SiteCharacterization, SiteSpec, ThemeSpec, PageSpec,
                                  Block, GridNode, PluginSpec)
from characterize.writer import write_characterization

def _sc():
    page = PageSpec("https://x.com/get-started/", "get-started", "Get Started", None, "page",
                    "published", [Block("heading", {"level": 1, "text": "Get Started"}),
                                  Block("paragraph", {"text": "Call 760-632-8258."})],
                    GridNode("container", layout={"display": "flex"}), "fp1")
    return SiteCharacterization(
        site=SiteSpec("x.com", "X", "t", "crawl", "2026-06-24", {"cms": "wordpress"},
                      [], ["get-started"], ["gravity-forms"]),
        theme=ThemeSpec({"background": "#fff"}, {}, [8, 16], {"container_width": "960px"}, []),
        pages=[page], components=[],
        plugins=[PluginSpec("Gravity Forms", "gravity-forms", "inferred", None, "Forms", [], None)])

def _frontmatter(text):
    lines = text.splitlines()
    i = lines.index("---")
    j = lines.index("---", i + 1)
    return yaml.safe_load("\n".join(lines[i + 1:j]))

def test_writes_tree_and_index(tmp_path: Path):
    out = write_characterization(_sc(), tmp_path)
    content = (out / "pages" / "get-started" / "content.md").read_text()
    assert content.startswith("---")
    fm = yaml.safe_load(content.split("---")[1])
    assert fm["blocks"][0] == {"type": "heading", "level": 1, "text": "Get Started"}
    assert "760-632-8258" in content                       # verbatim in prose body too
    assert (out / "design" / "theme.md").exists()
    assert (out / "plugins" / "gravity-forms.md").exists()
    idx = json.loads((out / "characterization.json").read_text())
    assert idx["spec_version"] and idx["pages"][0]["slug"] == "get-started"

def test_page_and_layout_md_written(tmp_path: Path):
    out = write_characterization(_sc(), tmp_path)
    assert (out / "pages" / "get-started" / "page.md").exists()
    assert (out / "pages" / "get-started" / "layout.md").exists()

def test_dashes_in_content_preserved_verbatim(tmp_path: Path):
    from characterize.models import (SiteCharacterization, SiteSpec, ThemeSpec, PageSpec, Block, GridNode)
    page = PageSpec("https://x.com/", "p", "P", None, "page", "published",
                    [Block("paragraph", {"text": "intro --- more"}), Block("paragraph", {"text": "---"})],
                    GridNode("container"), "fp")
    sc = SiteCharacterization(site=SiteSpec("x.com", "X", "", "crawl", "d", {}, [], ["p"], []),
                              theme=ThemeSpec(), pages=[page], components=[], plugins=[])
    out = write_characterization(sc, tmp_path)
    content = (out / "pages" / "p" / "content.md").read_text()
    fm = _frontmatter(content)                      # robust line-based parse still works
    texts = [b.get("text") for b in fm["blocks"]]
    assert "intro --- more" in texts and "---" in texts    # verbatim in frontmatter
    assert "intro --- more" in content                      # verbatim in prose body
