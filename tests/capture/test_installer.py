import json
from pathlib import Path
from capture.installer import WPInstaller

def _bundle(tmp_path):
    bdir = tmp_path / "site"; (bdir / "pages").mkdir(parents=True)
    (bdir / "theme").mkdir(); (bdir / "media").mkdir()
    (bdir / "pages" / "home.html").write_text("<p>hi</p>")
    (bdir / "manifest.json").write_text(json.dumps({
        "site_title": "S", "tagline": "t", "front_page_slug": "home",
        "pages": [{"url": "u", "slug": "home", "title": "Home", "parent": None, "status": "ok"}]}))
    return bdir

def test_install_sequences_wpcli_calls(tmp_path: Path):
    calls = []
    class R: returncode = 0; stdout = "42"
    def fake_runner(args): calls.append(args); return R()
    def fake_copier(src, dst): calls.append(["COPY", str(src), dst])
    WPInstaller(runner=fake_runner, copier=fake_copier).install(_bundle(tmp_path))
    flat = [" ".join(c) for c in calls]
    assert any("core install" in f for f in flat)
    assert any("theme activate" in f for f in flat)
    assert any("post create" in f for f in flat)
    assert any(f.startswith("COPY") for f in flat)
