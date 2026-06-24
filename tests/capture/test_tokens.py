# tests/capture/test_tokens.py
from capture.models import ComputedStyleSnapshot
from capture.design.tokens import derive_tokens, rgb_to_hex

def test_rgb_to_hex():
    assert rgb_to_hex("rgb(255, 255, 255)") == "#ffffff"
    assert rgb_to_hex("rgb(152,108,4)") == "#986c04"

def test_rgb_to_hex_edge_cases():
    assert rgb_to_hex("rgba(152,108,4,0.5)") == "#986c04"   # alpha ignored
    assert rgb_to_hex("") == ""
    assert rgb_to_hex("transparent") == ""
    assert rgb_to_hex("rgb(999,0,0)") == "#ff0000"          # clamped to 255

def test_derive_palette_and_fonts():
    snaps = [
        ComputedStyleSnapshot("body", "body", {"background-color": "rgb(255,255,255)",
            "color": "rgb(30,30,30)", "font-family": "Inter, sans-serif"}),
        ComputedStyleSnapshot("a", "a", {"color": "rgb(152,108,4)"}),
        ComputedStyleSnapshot("button", "button", {"background-color": "rgb(152,108,4)"}),
        ComputedStyleSnapshot("h1", "h1", {"font-family": "Outfit, sans-serif"}),
        ComputedStyleSnapshot("container", ".container", {"max-width": "960px"}),
        ComputedStyleSnapshot("header", "#header", {"height": "165px"}),
    ]
    t = derive_tokens(snaps)
    assert t.palette["background"] == "#ffffff"
    assert t.palette["text"] == "#1e1e1e"
    assert t.palette["link"] == "#986c04"
    assert t.palette["accent"] == "#986c04"
    assert t.fonts["body"].startswith("Inter")
    assert t.fonts["heading"].startswith("Outfit")
    assert t.container_width == 960
    assert t.header_height == 165
