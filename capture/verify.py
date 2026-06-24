from capture.models import DesignTokens, FidelityReport
from capture.design.tokens import rgb_to_hex  # noqa: F401 (re-export for callers)

def compare_fingerprints(original: str, captured: str) -> bool:
    return original == captured

def color_distance(hex1: str, hex2: str) -> float:
    def rgb(h):
        h = h.lstrip("#")
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    (r1, g1, b1), (r2, g2, b2) = rgb(hex1), rgb(hex2)
    return ((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2) ** 0.5

def design_distance(orig: DesignTokens, cap: DesignTokens) -> dict:
    out = {}
    for role, hexv in orig.palette.items():
        if role in cap.palette:
            out[role] = color_distance(hexv, cap.palette[role])
    out["max"] = max([v for k, v in out.items() if k != "max"], default=0.0)
    return out

def verify_site(orig_pages, cap_pages, orig_tokens, cap_tokens, color_tol: float = 25.0) -> FidelityReport:
    results = []
    content_ok = True
    for slug, fp in orig_pages.items():
        ok = compare_fingerprints(fp, cap_pages.get(slug, ""))
        if not ok:
            content_ok = False
        results.append({"slug": slug, "ok": ok})
    design_diff = design_distance(orig_tokens, cap_tokens)
    design_diff["within_tolerance"] = design_diff.get("max", 0.0) <= color_tol
    return FidelityReport(passed=content_ok, content_ok=content_ok,
                          page_results=results, design_diff=design_diff)
