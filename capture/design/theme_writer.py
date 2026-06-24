import json
from pathlib import Path
from capture.models import DesignTokens

def write_theme(tokens: DesignTokens, theme_dir: Path, theme_name: str = "captured-theme") -> None:
    theme_dir = Path(theme_dir)
    (theme_dir / "templates").mkdir(parents=True, exist_ok=True)
    (theme_dir / "parts").mkdir(parents=True, exist_ok=True)

    palette = [{"slug": slug, "color": hexv, "name": slug.title()}
               for slug, hexv in tokens.palette.items()]
    families = []
    for slug, stack in tokens.fonts.items():
        families.append({"fontFamily": stack, "slug": slug, "name": slug.title()})
    theme_json = {
        "$schema": "https://schemas.wp.org/trunk/theme.json",
        "version": 2,
        "settings": {
            "color": {"palette": palette},
            "typography": {"fontFamilies": families},
            "layout": {"contentSize": f"{tokens.container_width}px", "wideSize": f"{tokens.container_width}px"},
            "spacing": {"spacingSizes": [
                {"slug": str(i), "size": f"{v}px", "name": str(v)} for i, v in enumerate(tokens.spacing)]},
        },
        "styles": {
            "color": {"background": tokens.palette.get("background", "#ffffff"),
                      "text": tokens.palette.get("text", "#000000")},
            "typography": {"fontFamily": tokens.fonts.get("body", "sans-serif")},
        },
    }
    (theme_dir / "theme.json").write_text(json.dumps(theme_json, indent=2))
    (theme_dir / "style.css").write_text(
        f"/*\nTheme Name: {theme_name}\nVersion: 1.0\nRequires at least: 6.4\n*/\n")
    header = ('<!-- wp:group {"tagName":"header","className":"site-header"} -->\n'
              '<header class="wp-block-group site-header">'
              '<!-- wp:site-title /--><!-- wp:navigation /--></header>\n<!-- /wp:group -->')
    footer = ('<!-- wp:group {"tagName":"footer","className":"site-footer"} -->\n'
              '<footer class="wp-block-group site-footer"><!-- wp:site-title /--></footer>\n'
              '<!-- /wp:group -->')
    (theme_dir / "parts" / "header.html").write_text(header)
    (theme_dir / "parts" / "footer.html").write_text(footer)
    body = ('<!-- wp:template-part {"slug":"header","tagName":"div"} /-->\n'
            '<!-- wp:group {"tagName":"main","layout":{"type":"constrained"}} -->\n'
            '<main class="wp-block-group">\n%s\n</main>\n<!-- /wp:group -->\n'
            '<!-- wp:template-part {"slug":"footer","tagName":"div"} /-->')
    (theme_dir / "templates" / "index.html").write_text(body % '<!-- wp:query /-->')
    (theme_dir / "templates" / "page.html").write_text(
        body % '<!-- wp:post-title {"level":1} /-->\n<!-- wp:post-content /-->')
    (theme_dir / "templates" / "front-page.html").write_text(
        body % '<!-- wp:post-content /-->')
