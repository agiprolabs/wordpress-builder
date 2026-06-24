from capture.models import ComputedStyleSnapshot
from characterize.theme import build_theme_spec

def test_build_theme_spec_from_snapshots():
    snaps = [
        ComputedStyleSnapshot("body", "body", {"background-color": "rgb(255,255,255)",
            "color": "rgb(51,43,36)", "font-family": "Inter, sans-serif"}),
        ComputedStyleSnapshot("h1", "h1", {"font-family": "Outfit, sans-serif"}),
        ComputedStyleSnapshot("container", ".container", {"max-width": "960px"}),
    ]
    t = build_theme_spec(snaps)
    assert t.palette["background"] == "#ffffff"
    assert t.typography["body"]["family"].startswith("Inter")
    assert t.typography["heading"]["family"].startswith("Outfit")
    assert t.layout["container_width"] == "960px"
    assert isinstance(t.spacing_scale, list)
