from bs4 import BeautifulSoup
from characterize.models import PluginSpec

def _form_fields(form):
    label_for = {}
    for lab in form.find_all("label"):
        if lab.get("for"):
            label_for[lab["for"]] = lab.get_text(" ", strip=True)

    def prev_label_in_form(inp):
        prev = inp.find_previous("label")
        if prev is not None and prev.find_parent("form") is form:
            return prev.get_text(" ", strip=True)
        return None

    def plain_label(inp):
        if inp.get("id") and inp["id"] in label_for:
            return label_for[inp["id"]]
        return prev_label_in_form(inp) or inp.get("name", "")

    def option_label(inp):
        if inp.get("id") and inp["id"] in label_for:
            return label_for[inp["id"]]
        nxt = inp.find_next(["input", "textarea", "select", "label"])
        if nxt is not None and nxt.name == "label" and nxt.find_parent("form") is form:
            return nxt.get_text(" ", strip=True)
        return prev_label_in_form(inp) or inp.get("name", "")

    fields = []
    group = None  # accumulates a checkbox/radio group keyed by (type, name)
    for inp in form.find_all(["input", "textarea", "select"]):
        itype = inp.get("type", inp.name)
        if itype in ("hidden", "submit", "button"):
            continue
        if itype in ("checkbox", "radio"):
            key = (itype, inp.get("name", ""))
            option = option_label(inp)
            if group and group["_key"] == key:
                group["options"].append(option)
            else:
                if group:
                    group.pop("_key"); fields.append(group)
                question = prev_label_in_form(inp) or inp.get("name", "")
                group = {"_key": key, "label": question, "type": itype, "options": [option]}
            continue
        if group:
            group.pop("_key"); fields.append(group); group = None
        fields.append({"label": plain_label(inp), "type": itype})
    if group:
        group.pop("_key"); fields.append(group)
    return fields

def infer_plugins(pages) -> list:
    instances = []
    for p in pages:
        soup = BeautifulSoup(p.html, "lxml")
        for form in soup.select('form[id^="gform_"], form.gform_wrapper'):
            fid = form.get("id", "gform")
            existing = next((i for i in instances if i["id"] == fid), None)
            if existing:
                if p.slug not in existing["pages"]:
                    existing["pages"].append(p.slug)
            else:
                instances.append({"id": fid, "pages": [p.slug], "fields": _form_fields(form)})
    if not instances:
        return []
    return [PluginSpec(name="Gravity Forms", slug="gravity-forms", source="inferred",
                       version=None, behavior="Form builder; renders forms with validation.",
                       instances=instances, data_ref=None)]
