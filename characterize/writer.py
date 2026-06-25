import json, yaml
from pathlib import Path

def _md(frontmatter: dict, title: str, body: str) -> str:
    fm = yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True).strip()
    return f"---\n{fm}\n---\n\n# {title}\n\n{body}\n"

def _blocks_prose(blocks) -> str:
    lines = []
    for b in blocks:
        d = b.data
        if b.type == "heading": lines.append(("#" * d["level"]) + " " + d["text"])
        elif b.type == "paragraph": lines.append(d["text"])
        elif b.type == "list": lines += [f"- {i}" for i in d.get("items", [])]
        elif b.type == "image": lines.append(f"![{d.get('alt','')}]({d.get('src','')})")
        elif b.type == "plugin": lines.append(f"[plugin: {d.get('plugin','')} → {d.get('ref','')}]")
        lines.append("")
    return "\n".join(lines).strip()

def write_characterization(sc, out_dir) -> Path:
    out = Path(out_dir)
    (out / "design").mkdir(parents=True, exist_ok=True)
    (out / "components").mkdir(parents=True, exist_ok=True)
    (out / "plugins").mkdir(exist_ok=True)
    (out / "site.md").write_text(_md(sc.site.to_dict(), sc.site.title, sc.site.tagline or "Site overview."))
    (out / "design" / "theme.md").write_text(_md(sc.theme.to_dict(), "Design System", "Derived design tokens."))
    for p in sc.pages:
        pdir = out / "pages" / p.slug
        pdir.mkdir(parents=True, exist_ok=True)
        page_fm = {"url": p.url, "slug": p.slug, "title": p.title, "parent": p.parent,
                   "template": p.template, "status": p.status,
                   "content_ref": "content.md", "layout_ref": "layout.md"}
        (pdir / "page.md").write_text(_md(page_fm, p.title, f"Page: {p.title}."))
        content_fm = {"slug": p.slug, "content_fingerprint": p.fingerprint,
                      "blocks": [b.to_frontmatter() for b in p.blocks]}
        (pdir / "content.md").write_text(_md(content_fm, p.title, _blocks_prose(p.blocks)))
        layout_fm = {"slug": p.slug, "grid": p.grid.to_dict() if p.grid else None, "responsive": []}
        (pdir / "layout.md").write_text(_md(layout_fm, f"Layout — {p.title}", "Layout structure."))
    for c in sc.components:
        (out / "components" / f"{c.name}.md").write_text(_md(c.to_dict(), c.name, f"{c.name} component."))
    for pl in sc.plugins:
        (out / "plugins" / f"{pl.slug}.md").write_text(_md(pl.to_dict(), pl.name, pl.behavior or ""))
    (out / "characterization.json").write_text(json.dumps(sc.to_index(), indent=2))
    return out
