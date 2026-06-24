# capture/design/tokens.py
import re
from capture.models import ComputedStyleSnapshot, DesignTokens

def rgb_to_hex(css: str) -> str:
    m = re.findall(r"\d+", css or "")
    if len(m) < 3:
        return ""
    r, g, b = (min(255, max(0, int(m[i]))) for i in (0, 1, 2))
    return "#%02x%02x%02x" % (r, g, b)

def _px(val: str, default: int) -> int:
    m = re.search(r"(\d+)", val or "")
    return int(m.group(1)) if m else default

def derive_tokens(snapshots) -> DesignTokens:
    by_role = {s.role: s.styles for s in snapshots}
    palette = {}
    if "body" in by_role:
        if (h := rgb_to_hex(by_role["body"].get("background-color", ""))): palette["background"] = h
        if (h := rgb_to_hex(by_role["body"].get("color", ""))): palette["text"] = h
    if "a" in by_role and (h := rgb_to_hex(by_role["a"].get("color", ""))): palette["link"] = h
    if "button" in by_role and (h := rgb_to_hex(by_role["button"].get("background-color", ""))): palette["accent"] = h
    fonts = {}
    if "body" in by_role and by_role["body"].get("font-family"): fonts["body"] = by_role["body"]["font-family"]
    if "h1" in by_role and by_role["h1"].get("font-family"): fonts["heading"] = by_role["h1"]["font-family"]
    container_width = _px(by_role.get("container", {}).get("max-width", ""), 1100)
    header_height = _px(by_role.get("header", {}).get("height", ""), 0)
    return DesignTokens(palette=palette, fonts=fonts, spacing=[8, 16, 24, 32],
                        container_width=container_width, header_height=header_height,
                        raw={s.role: s.styles for s in snapshots})
