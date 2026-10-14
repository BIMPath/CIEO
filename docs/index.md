---
title: CIEO
---

# CIEO — Construction Inspection Evidence Ontology

**An ontology and reference implementation for construction inspection that knows the
difference between *we looked and it was not there* and *we could not see it*.**

Point a camera at a site, run a detector, and ask whether the excavation had edge
protection. The detector reports no barrier. That means either there was none — a
violation — or there was one and your photographs do not show it. The photograph cannot
tell you which, and every detection-driven compliance system resolves the ambiguity by
assuming the first.

CIEO measures its way out. The site is reconstructed in 3D with the camera positions in the
same frame; each inspection target is sampled; every sample is tested for frustum
containment and occlusion. From that geometry CIEO computes whether the detector *would
have* seen the object had it been there, and a SHACL constraint makes it structurally
impossible to record a verdict without that answer.

## Start here

- **[README](https://github.com/BIMPath/cieo#readme)** — what it is, quick start, current coverage
- **[The data model](data-model.md)** — six ideas everything else follows from
- **[Authoring a jurisdiction profile](authoring-a-profile.md)** — the most useful way to contribute
- **[Glossary](glossary.md)** — every term, with the nearest thing from construction practice

## Portable by construction

A requirement does not carry its clause. "Workers shall wear head protection" is the same
obligation in Turin, Manchester and Denver; what differs is which instrument says so.
Obligations live in a jurisdiction-neutral core; the legal grounding comes from pluggable
profiles that compose, contract over national over supranational.

| Profile | Verified | Proposed | Unmapped |
|---|---:|---:|---:|
| `it` Italy | 9 | 14 | 14 |
| `eu` European Union | 0 | 12 | 25 |
| `gb` United Kingdom | 10 | 4 | 23 |
| `us` United States (federal) | 10 | 4 | 23 |

A profile is one YAML file and two CSVs. No code, no ontology knowledge, no 3D model.
[Contributions welcome](https://github.com/BIMPath/cieo/blob/main/CONTRIBUTING.md).

## Licence

Ontology, data and documentation under CC BY 4.0; code under MIT.
