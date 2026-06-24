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

def test_localize_with_install_url_prefix(tmp_path: Path):
    def fake_dl(url): return b"X" if "a.png" in url else None
    mapping = localize_media(["https://x.com/a.png"], tmp_path / "media",
                             download=fake_dl, url_prefix="/wp-content/uploads/captured")
    assert mapping["https://x.com/a.png"].startswith("/wp-content/uploads/captured/")
    assert mapping["https://x.com/a.png"].endswith("a.png")
