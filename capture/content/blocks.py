from html import escape

def heading_block(level: int, text: str) -> str:
    return (f'<!-- wp:heading {{"level":{level}}} -->\n'
            f'<h{level} class="wp-block-heading">{escape(text)}</h{level}>\n'
            f'<!-- /wp:heading -->')

def paragraph_block(text: str) -> str:
    return f'<!-- wp:paragraph -->\n<p>{escape(text)}</p>\n<!-- /wp:paragraph -->'

def image_block(src: str, alt: str = "") -> str:
    return (f'<!-- wp:image -->\n'
            f'<figure class="wp-block-image"><img src="{escape(src)}" alt="{escape(alt)}"/></figure>\n'
            f'<!-- /wp:image -->')

def list_block(items: list, ordered: bool = False) -> str:
    tag = "ol" if ordered else "ul"
    lis = "".join(f"<li>{escape(i)}</li>" for i in items)
    attr = ' {"ordered":true}' if ordered else ""
    return f'<!-- wp:list{attr} -->\n<{tag}>{lis}</{tag}>\n<!-- /wp:list -->'

def html_block(raw: str) -> str:
    return f'<!-- wp:html -->\n{raw}\n<!-- /wp:html -->'

def placeholder_block(kind: str) -> str:
    return html_block(f'<!-- CAPTURE-PLACEHOLDER: {kind} -->')
