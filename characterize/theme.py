from capture.design.tokens import derive_tokens
from capture.models import ComputedStyleSnapshot
from characterize.models import ThemeSpec

def build_theme_spec(snapshots: list[ComputedStyleSnapshot]) -> ThemeSpec:
    t = derive_tokens(snapshots)
    typography = {}
    if "body" in t.fonts: typography["body"] = {"family": t.fonts["body"]}
    if "heading" in t.fonts: typography["heading"] = {"family": t.fonts["heading"]}
    return ThemeSpec(palette=t.palette, typography=typography, spacing_scale=t.spacing,
                     layout={"container_width": f"{t.container_width}px", "breakpoints": []},
                     font_assets=[])
