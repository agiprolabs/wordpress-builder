import json
from dataclasses import replace
from capture.models import DesignTokens

MODEL = "claude-sonnet-4-6"

_PROMPT = (
    "You are cleaning a website's design tokens. Given this JSON of palette, fonts, and "
    "spacing extracted from computed styles, return a JSON object with the SAME keys, "
    "normalizing near-duplicate colors, ensuring hex format, and ordering spacing ascending. "
    "Return ONLY JSON. Do not invent content. Input:\n"
)

def clean_tokens(tokens: DesignTokens, client=None) -> DesignTokens:
    if client is None:
        return tokens
    payload = {"palette": tokens.palette, "fonts": tokens.fonts, "spacing": tokens.spacing}
    try:
        resp = client.messages.create(
            model=MODEL, max_tokens=1024,
            messages=[{"role": "user", "content": _PROMPT + json.dumps(payload)}],
        )
        text = resp.content[0].text
        data = json.loads(text)
        if not isinstance(data.get("palette"), dict):
            return tokens
        return replace(tokens,
                       palette=data.get("palette", tokens.palette),
                       fonts=data.get("fonts", tokens.fonts),
                       spacing=data.get("spacing", tokens.spacing))
    except Exception:
        return tokens
