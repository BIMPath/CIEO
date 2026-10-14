# Glossary

For readers who work in construction rather than in knowledge representation. Every term,
with the nearest thing you already use.

| Term | What it is | The nearest thing you know |
|---|---|---|
| Ontology | An agreed list of the things that may be talked about, their properties, and how they may be connected. | IFC. Or the standard schedule of items in a bill of quantities. |
| OWL | The language the agreed list is written in. | The EXPRESS language the IFC schema is written in. |
| Turtle, `.ttl` | The file format. Plain text, one fact per line. | A CSV, but for facts rather than rows. |
| Triple | One fact: *subject — relationship — object*. | One cell in a schedule, with its row and column heading. |
| Class | A kind of thing. | A family type in Revit. |
| Individual | One particular thing of that kind. | A placed instance, with its own GUID. |
| T-Box / A-Box | The definitions / the particular facts. | The schema / the model. |
| SPARQL | The query language. A CONSTRUCT query reads facts and writes new ones. | A formula filling a derived column. |
| SHACL | A set of refusals: constraints a record must satisfy. | A model-checking rule set, or form validation that will not let you submit a blank field. |
| ifcOWL | The IFC schema re-expressed in OWL. | The same model exported to a second format. |
| Knowledge graph | All of the above loaded together. | A federated model in one viewer. |
| Closed-world assumption | "Not in my records, therefore it does not exist." | Treating a blank on a snagging list as *nothing wrong there*. |
| Open-world assumption | "Not in my records, therefore I do not know." | Treating a blank on a snagging list as *not inspected*. |
| Recall | Of the things that were there, the share the detector found. | The hit rate of a non-destructive test. |
| Precision | Of the things reported, the share that were really there. | The false-alarm rate of the same test. |
| Prior / posterior | What you believed before looking / after. | Your expectation of honeycombing before you strip the formwork, and after. |
| Ground sample distance | How much real surface one pixel covers. | Scale, but per pixel. |
| Frustum | The pyramid of space a camera can see. | The cone of a site light. |
| Occlusion | Something standing between the camera and the thing. | A spoil heap in the way. |
| Self-occlusion | The object hidden by the assembly it belongs to. | A washer behind a torqued nut. |
| Evidence pattern | Which of seven burdens of proof a requirement carries. | The difference between *is it there* and *is the whole run continuous*. |
| Sufficiency | Whether the evidence could have settled the question at all. | Whether you actually got to walk that face. |
| Clause binding | The claim that this jurisdiction grounds this requirement in this clause. | The regulation column on an inspection checklist, with a note on who checked it. |
| Jurisdiction profile | A set of clause bindings for one legal system. | The national annex to a Eurocode. |
