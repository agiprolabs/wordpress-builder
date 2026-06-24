# capture/media.py
import hashlib
import logging
from pathlib import Path
from urllib.parse import urlparse

_log = logging.getLogger(__name__)

def _default_download(url: str):
    import requests
    r = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    return r.content

def localize_media(assets, media_dir, download=_default_download, url_prefix="media") -> dict:
    media_dir = Path(media_dir); media_dir.mkdir(parents=True, exist_ok=True)
    mapping: dict = {}
    for url in assets:
        if url in mapping or not url.startswith("http"):
            continue
        try:
            data = download(url)
            if not data:
                _log.warning("media: skipping %s (empty/None download)", url)
                continue
        except Exception as e:
            _log.warning("media: skipping %s (download failed: %s)", url, e)
            continue
        base = Path(urlparse(url).path).name or "asset"
        sha8 = hashlib.sha256(url.encode()).hexdigest()[:8]
        name = f"{sha8}-{base}"
        (media_dir / name).write_bytes(data)
        mapping[url] = f"{url_prefix.rstrip('/')}/{name}"
    return mapping

def rewrite_urls(text: str, mapping: dict) -> str:
    for original, local in mapping.items():
        text = text.replace(original, local)
    return text
