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

def test_same_form_on_multiple_pages_accumulates_slugs():
    specs = infer_plugins([_p("get-started", FORM), _p("contact", FORM)])
    assert len(specs) == 1
    inst = specs[0].instances[0]
    assert inst["id"] == "gform_1"
    assert inst["pages"] == ["get-started", "contact"]

GROUPED = ('<form id="gform_9" class="gform_wrapper">'
           '<label for="i_name">Full Name</label><input id="i_name" type="text" name="name">'
           '<label>Interests</label>'
           '<input type="checkbox" name="interest[]" value="a"><label>Design</label>'
           '<input type="checkbox" name="interest[]" value="b"><label>SEO</label>'
           '</form>')

def test_label_for_id_and_checkbox_grouping():
    specs = infer_plugins([_p("contact", GROUPED)])
    fields = specs[0].instances[0]["fields"]
    name_field = [f for f in fields if f["type"] == "text"][0]
    assert name_field["label"] == "Full Name"          # matched via for/id, not a stray label
    cb = [f for f in fields if f["type"] == "checkbox"]
    assert len(cb) == 1                                 # ONE grouped checkbox field, not 2
    assert sorted(cb[0]["options"]) == ["Design", "SEO"]
