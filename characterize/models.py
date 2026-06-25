from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional

from capture.models import Block  # Block lives in capture layer; re-exported here

SPEC_VERSION = "1.0"

__all__ = [
    "Block", "GridNode", "PageSpec", "ThemeSpec", "ComponentSpec",
    "PluginSpec", "SiteSpec", "SiteCharacterization", "SPEC_VERSION",
]


@dataclass
class GridNode:
    node: str
    layout: Optional[dict] = None
    children: Optional[list] = None
    area: Optional[str] = None
    ref: Optional[str] = None
    blocks_ref: Optional[str] = None
    def to_dict(self):
        out = {"node": self.node}
        if self.layout is not None: out["layout"] = self.layout
        if self.area is not None: out["area"] = self.area
        if self.ref is not None: out["ref"] = self.ref
        if self.blocks_ref is not None: out["blocks_ref"] = self.blocks_ref
        if self.children is not None: out["children"] = [c.to_dict() for c in self.children]
        return out
    @classmethod
    def from_dict(cls, d):
        d = dict(d)
        ch = d.pop("children", None)
        node = cls(**d)
        if ch is not None: node.children = [cls.from_dict(c) for c in ch]
        return node


@dataclass
class PageSpec:
    url: str
    slug: str
    title: str
    parent: Optional[str]
    template: str
    status: str
    blocks: list = field(default_factory=list)
    grid: Optional[GridNode] = None
    fingerprint: str = ""
    def to_dict(self):
        return {"url": self.url, "slug": self.slug, "title": self.title, "parent": self.parent,
                "template": self.template, "status": self.status,
                "blocks": [b.to_frontmatter() for b in self.blocks],
                "grid": self.grid.to_dict() if self.grid else None,
                "fingerprint": self.fingerprint}
    @classmethod
    def from_dict(cls, d):
        d = dict(d)
        blocks = [Block.from_dict(b) for b in d.pop("blocks", [])]
        grid = d.pop("grid", None)
        grid = GridNode.from_dict(grid) if grid else None
        return cls(blocks=blocks, grid=grid, **d)


@dataclass
class ThemeSpec:
    palette: dict = field(default_factory=dict)
    typography: dict = field(default_factory=dict)
    spacing_scale: list = field(default_factory=list)
    layout: dict = field(default_factory=dict)
    font_assets: list = field(default_factory=list)
    def to_dict(self): return asdict(self)
    @classmethod
    def from_dict(cls, d): return cls(**d)


@dataclass
class ComponentSpec:
    name: str
    appears_on: object
    type: str
    elements: list = field(default_factory=list)
    def to_dict(self): return asdict(self)
    @classmethod
    def from_dict(cls, d): return cls(**d)


@dataclass
class PluginSpec:
    name: str
    slug: str
    source: str
    version: Optional[str]
    behavior: str
    instances: list = field(default_factory=list)
    data_ref: Optional[str] = None
    def to_dict(self): return asdict(self)
    @classmethod
    def from_dict(cls, d): return cls(**d)


@dataclass
class SiteSpec:
    domain: str
    title: str
    tagline: str
    source: str
    captured_at: str
    detected_stack: dict = field(default_factory=dict)
    nav: list = field(default_factory=list)
    pages: list = field(default_factory=list)
    plugins: list = field(default_factory=list)
    def to_dict(self): return asdict(self)
    @classmethod
    def from_dict(cls, d): return cls(**d)


@dataclass
class SiteCharacterization:
    site: SiteSpec
    theme: ThemeSpec
    pages: list = field(default_factory=list)
    components: list = field(default_factory=list)
    plugins: list = field(default_factory=list)
    def to_index(self):
        return {"spec_version": SPEC_VERSION, "site": self.site.to_dict(),
                "design": self.theme.to_dict(), "pages": [p.to_dict() for p in self.pages],
                "components": [c.to_dict() for c in self.components],
                "plugins": [p.to_dict() for p in self.plugins]}
    @classmethod
    def from_index(cls, idx):
        return cls(site=SiteSpec.from_dict(idx["site"]),
                   theme=ThemeSpec.from_dict(idx["design"]),
                   pages=[PageSpec.from_dict(p) for p in idx.get("pages", [])],
                   components=[ComponentSpec.from_dict(c) for c in idx.get("components", [])],
                   plugins=[PluginSpec.from_dict(p) for p in idx.get("plugins", [])])
