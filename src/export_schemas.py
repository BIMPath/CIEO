# -*- coding: utf-8 -*-
"""Write schemas/*.json from the single declaration in src/tableschema.py.

The published schemas are generated so they cannot drift from what the validator enforces.
The format is Frictionless Table Schema, which spreadsheet and data tools understand.

    python3 src/export_schemas.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from tableschema import TABLES                                        # noqa: E402

TYPE = {"str": "string", "enum": "string", "num": "number", "int": "integer",
        "bool": "boolean", "url": "string", "list": "string", "ref": "string"}

out_dir = os.path.join(ROOT, "schemas")
os.makedirs(out_dir, exist_ok=True)
index = []
for rel, spec in TABLES.items():
    fields = []
    for name, required, kind, extra in spec["fields"]:
        f = {"name": name, "type": TYPE[kind], "constraints": {"required": bool(required)}}
        if kind == "enum":
            f["constraints"]["enum"] = [e for e in extra if e != ""]
        if kind == "num" and extra:
            f["constraints"]["minimum"], f["constraints"]["maximum"] = extra
        if kind == "int" and extra:
            f["constraints"]["minimum"], f["constraints"]["maximum"] = extra
        if kind == "url":
            f["format"] = "uri"
        if kind == "list":
            f["cieo:separator"] = extra
        if kind == "ref":
            f["cieo:references"] = {"table": extra[0], "field": extra[1]}
        fields.append(f)
    doc = {"$schema": "https://specs.frictionlessdata.io/schemas/table-schema.json",
           "name": rel.replace("/", "-").replace(".csv", ""),
           "title": rel,
           "description": spec["doc"],
           "fields": fields}
    if spec.get("key"):
        doc["primaryKey"] = spec["key"]
    name = rel.replace("/", "-").replace(".csv", ".json")
    with open(os.path.join(out_dir, name), "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    index.append({"table": rel, "schema": f"schemas/{name}", "description": spec["doc"]})

with open(os.path.join(out_dir, "index.json"), "w", encoding="utf-8") as fh:
    json.dump({"cieo_version": "1.0", "tables": index}, fh, indent=2, ensure_ascii=False)
    fh.write("\n")
print(f"wrote {len(index)} schemas + index.json to {out_dir}")
