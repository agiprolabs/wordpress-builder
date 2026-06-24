# tests/capture/test_media.py
from pathlib import Path
from capture.media import localize_media, rewrite_urls

def test_localize_and_rewrite(tmp_path: Path):
    def fake_dl(url): return b"PNGDATA" if "a.png" in url else None
    assets = ["https://x.com/a.png", "https://x.com/a.png", "https://x.com/missing.png"]
    mapping = localize_media(assets, tmp_path, download=fake_dl)
    assert "https://x.com/a.png" in mapping
    local = mapping["https://x.com/a.png"]
    assert (tmp_path / Path(local).name).read_bytes() == b"PNGDATA"
    # missing asset that returns None is skipped
    assert "https://x.com/missing.png" not in mapping
    html = '<img src="https://x.com/a.png">'
    assert local in rewrite_urls(html, mapping)
