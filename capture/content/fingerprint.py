import hashlib, re
from bs4 import BeautifulSoup

def content_fingerprint(block_html: str) -> str:
    soup = BeautifulSoup(block_html, "lxml")
    tags = [t.name for t in soup.find_all(True)]
    text = soup.get_text(" ")
    text = re.sub(r"\s+", " ", text).strip().lower()
    payload = "|".join(tags) + "##" + text
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
