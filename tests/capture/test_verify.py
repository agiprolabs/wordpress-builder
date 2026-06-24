from capture.models import DesignTokens
from capture.verify import compare_fingerprints, color_distance, design_distance, verify_site

def test_color_distance_and_design_report():
    assert color_distance("#000000", "#000000") == 0
    assert color_distance("#000000", "#ffffff") > 440   # 255*sqrt(3) ≈ 441.67
    o = DesignTokens(palette={"accent": "#986c04"}, fonts={}, spacing=[], container_width=960, header_height=0, raw={})
    c = DesignTokens(palette={"accent": "#9a6e06"}, fonts={}, spacing=[], container_width=960, header_height=0, raw={})
    dd = design_distance(o, c)
    assert dd["accent"] < 10 and dd["max"] < 10

def test_content_mismatch_fails_overall():
    orig = {"home": "fpA", "about": "fpB"}
    good = {"home": "fpA", "about": "fpB"}
    bad = {"home": "fpA", "about": "DIFFERENT"}
    t = DesignTokens(palette={}, fonts={}, spacing=[], container_width=960, header_height=0, raw={})
    assert verify_site(orig, good, t, t).passed is True
    rep = verify_site(orig, bad, t, t)
    assert rep.content_ok is False and rep.passed is False
    assert any(r["slug"] == "about" and r["ok"] is False for r in rep.page_results)

def test_missing_page_fails_content():
    orig = {"home": "fpA", "about": "fpB"}
    missing = {"home": "fpA"}  # "about" absent from captured
    t = DesignTokens(palette={}, fonts={}, spacing=[], container_width=960, header_height=0, raw={})
    rep = verify_site(orig, missing, t, t)
    assert rep.content_ok is False and rep.passed is False
    assert any(r["slug"] == "about" and r["ok"] is False for r in rep.page_results)
