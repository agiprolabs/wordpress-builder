# capture/media.py
import hashlib
from pathlib import Path
from urllib.parse import urlparse

def _default_download(url: str):
    import requests
    r = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    return r.content

def localize_media(assets, media_dir, download=_default_download) -> dict:
    media_dir = Path(media_dir); media_dir.mkdir(parents=True, exist_ok=True)
    mapping: dict = {}
    for url in assets:
        if url in mapping or not url.startswith("http"):
            continue
        try:
            data = download(url)
            if not data:
                continue
        except Exception:
            continue
        base = Path(urlparse(url).path).name or "asset"
        sha8 = hashlib.sha256(url.encode()).hexdigest()[:8]
        name = f"{sha8}-{base}"
        (media_dir / name).write_bytes(data)
        mapping[url] = f"media/{name}"
    return mapping

def rewrite_urls(text: str, mapping: dict) -> str:
    for original, local in mapping.items():
        text = text.replace(original, local)
    return text
