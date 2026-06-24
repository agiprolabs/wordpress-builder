import json
from pathlib import Path
from characterize.models import Block

_BLOCK_TYPES = {"heading", "paragraph", "list", "image", "table", "button", "embed", "plugin"}

def load_index(bundle_dir) -> dict:
    return json.loads((Path(bundle_dir) / "characterization.json").read_text())

def validate_index(idx: dict) -> list:
    problems = []
    if not idx.get("spec_version"):
        problems.append("missing spec_version")
    for p in idx.get("pages", []):
        for key in ("slug", "template", "fingerprint"):
            if not p.get(key):
                problems.append(f"page missing {key}: {p.get('slug', '?')}")
        for b in p.get("blocks", []):
            if b.get("type") not in _BLOCK_TYPES:
                problems.append(f"unknown block type '{b.get('type')}' in {p.get('slug','?')}")
    return problems
