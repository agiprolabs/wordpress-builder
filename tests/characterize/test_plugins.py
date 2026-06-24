from capture.models import RenderedPage
from characterize.plugins import infer_plugins

FORM = ('<form id="gform_1" class="gform_wrapper">'
        '<label>Name</label><input type="text" name="n">'
        '<label>Email</label><input type="email" name="e">'
        '</form>')

def _p(slug, body):
    return RenderedPage(url="/"+slug, slug=slug, title=slug, html=f"<html><body>{body}</body></html>")

def test_infers_gravity_forms_with_fields():
    specs = infer_plugins([_p("get-started", FORM), _p("about", "<p>x</p>")])
    assert len(specs) == 1
    gf = specs[0]
    assert gf.slug == "gravity-forms" and gf.source == "inferred"
    inst = gf.instances[0]
    assert inst["id"] == "gform_1"
    assert inst["pages"] == ["get-started"]
    labels = [f["label"] for f in inst["fields"]]
    assert labels == ["Name", "Email"]
    assert inst["fields"][1]["type"] == "email"

def test_no_forms_no_plugins():
    assert infer_plugins([_p("home", "<p>nothing</p>")]) == []
