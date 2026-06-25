from pathlib import Path
from characterize.loader import load_index, validate_index
from characterize.models import SiteCharacterization, SiteSpec, ThemeSpec, PageSpec, Block, GridNode
from characterize.writer import write_characterization

def test_written_index_validates(tmp_path: Path):
    sc = SiteCharacterization(
        site=SiteSpec("x.com","X","","crawl","2026-06-24",{},[],["home"],[]),
        theme=ThemeSpec(), pages=[PageSpec("https://x.com/","home","Home",None,"front-page",
                                           "published",[Block("paragraph",{"text":"hi"})],
                                           GridNode("container"), "fp")],
        components=[], plugins=[])
    out = write_characterization(sc, tmp_path)
    idx = load_index(out)
    assert validate_index(idx) == []

def test_validate_flags_bad_block_type(tmp_path: Path):
    idx = {"spec_version": "1.0", "site": {}, "design": {},
           "pages": [{"slug": "p", "template": "page", "fingerprint": "x",
                      "blocks": [{"type": "bogus"}]}], "components": [], "plugins": []}
    problems = validate_index(idx)
    assert any("bogus" in p for p in problems)
