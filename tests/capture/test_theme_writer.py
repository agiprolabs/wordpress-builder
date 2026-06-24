import json
from pathlib import Path
from capture.models import DesignTokens
from capture.design.theme_writer import write_theme

def test_writes_valid_theme_json_and_templates(tmp_path: Path):
    t = DesignTokens(palette={"background": "#ffffff", "text": "#1e1e1e", "accent": "#986c04"},
                     fonts={"body": "Inter, sans-serif", "heading": "Outfit, sans-serif"},
                     spacing=[8, 16, 24], container_width=960, header_height=165, raw={})
    write_theme(t, tmp_path)
    tj = json.loads((tmp_path / "theme.json").read_text())
    assert tj["version"] == 2
    slugs = {c["slug"] for c in tj["settings"]["color"]["palette"]}
    assert {"background", "text", "accent"} <= slugs
    assert tj["settings"]["layout"]["contentSize"] == "960px"
    assert (tmp_path / "templates" / "page.html").exists()
    assert (tmp_path / "parts" / "header.html").exists()
    assert (tmp_path / "style.css").read_text().startswith("/*")
