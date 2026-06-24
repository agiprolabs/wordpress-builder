import json
from capture.models import DesignTokens
from capture.design.llm import clean_tokens, MODEL

def _tokens():
    return DesignTokens(palette={"background": "#ffffff", "accent": "#986c04"},
                        fonts={"body": "Inter, sans-serif"}, spacing=[8, 16],
                        container_width=960, header_height=165, raw={})

class FakeClient:
    def __init__(self, payload): self._payload = payload; self.seen = None
    class _M:
        def __init__(self, outer): self._outer = outer
        def create(self, **kw):
            self._outer.seen = kw
            class R: pass
            r = R(); r.content = [type("B", (), {"text": self._outer._payload})]
            return r
    @property
    def messages(self): return FakeClient._M(self)

def test_none_client_is_passthrough():
    t = _tokens()
    assert clean_tokens(t, client=None) == t

def test_model_is_pinned_and_content_never_sent():
    fc = FakeClient(json.dumps({"palette": {"background": "#fefefe", "accent": "#986c04"},
                                "fonts": {"body": "Inter, sans-serif"}, "spacing": [8, 16]}))
    out = clean_tokens(_tokens(), client=fc)
    assert fc.seen["model"] == MODEL == "claude-sonnet-4-6"
    sent = json.dumps(fc.seen)
    assert "left-area" not in sent and "Get Started" not in sent  # no content leaked
    assert out.palette["background"] == "#fefefe"

def test_bad_json_returns_original():
    fc = FakeClient("not json")
    t = _tokens()
    assert clean_tokens(t, client=fc) == t
