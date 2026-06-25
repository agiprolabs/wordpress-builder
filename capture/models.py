from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class ComputedStyleSnapshot:
    role: str
    selector: str
    styles: dict

    def to_dict(self): return asdict(self)
    @classmethod
    def from_dict(cls, d): return cls(**d)


@dataclass
class RenderedPage:
    url: str
    slug: str
    title: str
    html: str
    computed: list = field(default_factory=list)
    assets: list = field(default_factory=list)
    screenshot_path: Optional[str] = None

    def to_dict(self):
        return {**asdict(self), "computed": [c.to_dict() for c in self.computed]}
    @classmethod
    def from_dict(cls, d):
        d = dict(d)
        d["computed"] = [ComputedStyleSnapshot.from_dict(c) for c in d.get("computed", [])]
        return cls(**d)


@dataclass
class PageContent:
    slug: str
    title: str
    block_html: str
    fingerprint: str
    placeholders: list = field(default_factory=list)
    def to_dict(self): return asdict(self)
    @classmethod
    def from_dict(cls, d): return cls(**d)


@dataclass
class DesignTokens:
    palette: dict
    fonts: dict
    spacing: list
    container_width: int
    header_height: int
    raw: dict = field(default_factory=dict)
    def to_dict(self): return asdict(self)
    @classmethod
    def from_dict(cls, d): return cls(**d)


@dataclass
class PageMeta:
    url: str
    slug: str
    title: str
    parent: Optional[str] = None
    status: str = "ok"
    def to_dict(self): return asdict(self)
    @classmethod
    def from_dict(cls, d): return cls(**d)


@dataclass
class Manifest:
    site_title: str
    tagline: str
    front_page_slug: str
    pages: list = field(default_factory=list)
    def to_dict(self):
        return {**asdict(self), "pages": [p.to_dict() for p in self.pages]}
    @classmethod
    def from_dict(cls, d):
        d = dict(d); d["pages"] = [PageMeta.from_dict(p) for p in d.get("pages", [])]
        return cls(**d)


@dataclass
class FidelityReport:
    passed: bool
    content_ok: bool
    page_results: list = field(default_factory=list)
    design_diff: dict = field(default_factory=dict)
    def to_dict(self): return asdict(self)
    @classmethod
    def from_dict(cls, d): return cls(**d)


@dataclass
class Block:
    type: str
    data: dict = field(default_factory=dict)
    def to_frontmatter(self): return {"type": self.type, **self.data}
    @classmethod
    def from_dict(cls, d):
        d = dict(d); t = d.pop("type"); return cls(t, d)
