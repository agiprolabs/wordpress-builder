# tests/capture/test_media.py
from pathlib import Path
from capture.media import localize_media, rewrite_urls

def test_localize_and_rewrite(tmp_path: Path):
    def fake_dl(url): return b"PNGDATA" if "a.png" in url else None
    media_dir = tmp_path / "media"                       # realistic: <bundle>/media
    assets = ["https://x.com/a.png", "https://x.com/a.png", "https://x.com/missing.png"]
    mapping = localize_media(assets, media_dir, download=fake_dl)
    assert "https://x.com/a.png" in mapping
    local = mapping["https://x.com/a.png"]               # e.g. "media/<sha8>-a.png"
    # `local` is relative to the bundle root; media_dir == tmp_path/"media"
    assert (tmp_path / local).read_bytes() == b"PNGDATA"
    assert "https://x.com/missing.png" not in mapping
    html = '<img src="https://x.com/a.png">'
    assert local in rewrite_urls(html, mapping)
