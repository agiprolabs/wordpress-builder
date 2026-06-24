from bs4 import BeautifulSoup
from characterize.models import PluginSpec

def _form_fields(form):
    fields = []
    for inp in form.find_all(["input", "textarea", "select"]):
        if inp.get("type") in ("hidden", "submit"):
            continue
        label = None
        lab = inp.find_previous("label")
        if lab: label = lab.get_text(" ", strip=True)
        fields.append({"label": label or inp.get("name", ""), "type": inp.get("type", inp.name)})
    return fields

def infer_plugins(pages) -> list:
    instances = []
    for p in pages:
        soup = BeautifulSoup(p.html, "lxml")
        for form in soup.select('form[id^="gform_"], form.gform_wrapper, .gform_wrapper form, .gform_wrapper'):
            fid = form.get("id", "gform")
            if not any(i["id"] == fid for i in instances):
                instances.append({"id": fid, "pages": [p.slug], "fields": _form_fields(form)})
    if not instances:
        return []
    return [PluginSpec(name="Gravity Forms", slug="gravity-forms", source="inferred",
                       version=None, behavior="Form builder; renders forms with validation.",
                       instances=instances, data_ref=None)]
