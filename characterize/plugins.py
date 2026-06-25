from bs4 import BeautifulSoup
from characterize.models import PluginSpec

def _form_fields(form):
    # map <label for=ID> -> text for precise association
    label_for = {}
    for lab in form.find_all("label"):
        if lab.get("for"):
            label_for[lab["for"]] = lab.get_text(" ", strip=True)

    def label_of(inp):
        if inp.get("id") and inp["id"] in label_for:
            return label_for[inp["id"]]
        prev = inp.find_previous("label")
        return prev.get_text(" ", strip=True) if prev else inp.get("name", "")

    fields = []
    group = None  # accumulates a checkbox/radio group keyed by (type, name)
    for inp in form.find_all(["input", "textarea", "select"]):
        itype = inp.get("type", inp.name)
        if itype in ("hidden", "submit", "button"):
            continue
        if itype in ("checkbox", "radio"):
            key = (itype, inp.get("name", ""))
            # option label may follow the input (common pattern); fall back to preceding label
            nxt = inp.find_next("label")
            option = nxt.get_text(" ", strip=True) if nxt else label_of(inp)
            if group and group["_key"] == key:
                group["options"].append(option)
            else:
                # close previous group, start a new one labelled by the question preceding it
                if group:
                    group.pop("_key"); fields.append(group)
                question = None
                q = inp.find_previous("label")
                # the group's question is the label BEFORE the first option's own label
                prev_label = q.find_previous("label") if q else None
                question = (prev_label.get_text(" ", strip=True) if prev_label else
                            (q.get_text(" ", strip=True) if q else inp.get("name", "")))
                group = {"_key": key, "label": question, "type": itype, "options": [option]}
            continue
        if group:
            group.pop("_key"); fields.append(group); group = None
        fields.append({"label": label_of(inp), "type": itype})
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
