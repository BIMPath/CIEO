# CIEO — Construction Inspection Evidence Ontology

**An ontology and reference implementation for construction inspection that knows the
difference between *we looked and it was not there* and *we could not see it*.**

[![validate](https://github.com/BIMPath/cieo/actions/workflows/validate.yml/badge.svg)](https://github.com/BIMPath/cieo/actions/workflows/validate.yml)
&nbsp;·&nbsp; Ontology and data: [CC BY 4.0](LICENSE) &nbsp;·&nbsp; Code: [MIT](LICENSE-CODE)
&nbsp;·&nbsp; 37 requirements · 29 object classes · 4 jurisdiction profiles

---

## The problem

Point a camera at a construction site, run a detector over the photographs, and ask whether
the excavation had edge protection. The detector reports no barrier. That means one of two
things, and the photograph cannot tell you which:

- there was no barrier, which is a safety violation; or
- there was a barrier and your photographs do not show it, because you walked the other
  side, or a spoil heap stood in the way, or you were too far back for it to register.

Every detection-driven compliance system resolves this by assuming the first. It reports a
violation whenever a camera happened to point the wrong way. In an inspection context that
is not a small inaccuracy — it is a false accusation of regulatory non-compliance, and it
is why these systems stay in the laboratory.

Your profession already draws this distinction everywhere else. A concrete cube test that
was never taken is not a failed test. A survey point you could not occupy is not a point
that moved. A pile the integrity-test head never reached is not a defective pile.

## What CIEO does

Before the system says anything about compliance, it answers a prior question: **could
these photographs have settled it?** It answers from geometry, not from the photographs.

The site is reconstructed in 3D, the camera positions are recovered into the same frame,
and each thing to be inspected is marked and chopped into a few hundred sample points. For
every photograph, every sample point is tested — was it in frame, and was anything in the
way? For the points that were visible, the standoff, the incidence angle and the ground
sample distance are recorded. From that geometry and five published parameters per object
class, CIEO computes the probability that the detector *would have* found the object had it
been there.

A SHACL constraint then does the part that matters: it makes it structurally impossible to
record a Compliant or NonCompliant verdict without a sufficiency assessment saying the
evidence was capable of settling it. Abstention is a first-class outcome, and it comes with
an instruction — usually *take one more photograph, from there*.

> The full reasoning is described in the accompanying publication. This repository is the
> ontology, the reference implementation and the data, maintained so that it can be used on
> any project in any country.

## What is in the box

| | |
|---|---|
| `ontology/` | 11 OWL 2 modules, aligned to ifcOWL. The vocabulary. |
| `data/core/` | 37 inspection requirements, 29 object classes, and the decision thresholds — **all jurisdiction-neutral**. |
| `data/profiles/` | One folder per legal system. Each maps requirements onto the clauses of that country's instruments. |
| `data/projects/` | One folder per site: its phases, its geometry, which profiles apply. |
| `rules/` | 10 SPARQL CONSTRUCT rules: requirement applicability, the pattern-specific decision rules, traceability. |
| `shapes/` | 20 SHACL shapes, including the gate the whole framework rests on. |
| `src/` | Validator, knowledge-base builder, detectability model, sufficiency assessor, decision engine. No required dependencies for the data layer. |
| `unity/` | Three C# scripts that do the visibility measurement inside a game engine. |

## Quick start

```bash
git clone https://github.com/BIMPath/cieo.git && cd cieo

python3 src/validate_data.py                              # check every CSV and cross-reference
python3 src/build_kb.py --project via-alba-savigliano     # compile a knowledge base
```

The validator needs nothing but Python 3.10+. It prints a coverage table and exits non-zero
on any error, which is exactly what the CI workflow does on every pull request.

---

## How it is organised, and why

The single design decision that makes CIEO portable is this: **a requirement no longer
carries its clause.**

"Workers shall wear head protection" is the same obligation in Turin, Manchester and
Denver. What differs is which instrument says so, and where. So the obligation lives in
`data/core/requirements.csv` with no legal reference at all, and a separate *clause
binding* ties it to one clause of one instrument inside one jurisdiction profile.

```
data/core/requirements.csv        IR-P1-003  "Workers shall wear helmet, vest and footwear"
                                             ComponentIntegrity · helmet;vest;boots · FINE
          │
          ├── profiles/it/   →  D.Lgs. 81/2008, Titolo III Capo II Art. 74-79
          ├── profiles/gb/   →  PPE at Work Regulations 1992, reg. 4
          └── profiles/us/   →  29 CFR 1926.95
```

Three layers, resolved in order. A **project** names the profiles it uses; bindings are
resolved from the project's own overlay first, then each profile in turn, and the first hit
wins — because that is the order in which obligations actually bite on a site:

```
project overlay   contract specification, site safety plan      precedence 0
      ↓
national profile  D.Lgs. 81/2008, CDM 2015, 29 CFR 1926         precedence 1
      ↓
supranational     EN, ISO, ETAG                                 precedence 2
```

A requirement that reaches the end of the chain unbound is **recorded as unmapped**, not
dropped. The same discipline the framework applies to unobserved evidence, applied to
itself: a gap you can count is worth more than a silence.

### Three states a binding can be in

| Status | Meaning |
|---|---|
| `VERIFIED` | Someone checked the clause against the published instrument and recorded where. Only these should be relied on where a finding will be cited to a regulator. |
| `PROPOSED` | Plausible, unchecked. Fine for analysis; not for citation. |
| `UNMAPPED` | Nobody has authored it. Stated explicitly so coverage is a number. |
| `NOT_APPLICABLE` | Checked, and this jurisdiction imposes no equivalent obligation. Different from unmapped, and the difference is worth recording. |

A binding is only `VERIFIED` when a reader can check it — the instrument or the binding must
carry a free, citable URL. The validator enforces that, which is why the Italian profile,
authored with care against real decrees, still reports mostly `PROPOSED`: the clauses are
right, but CEN and UNI standards are sold rather than published, so nobody can confirm them
from a link. That is an honest number, not a defect.

### Current coverage

| Profile | Verified | Proposed | Unmapped | Status |
|---|---:|---:|---:|---|
| `it` Italy | 9 | 14 | 14 | complete for the reference project |
| `eu` European Union | 0 | 12 | 25 | complete for the reference project |
| `gb` United Kingdom | 10 | 4 | 23 | **scaffold — contributions welcome** |
| `us` United States (federal) | 10 | 4 | 23 | **scaffold — contributions welcome** |

Composed, the reference project `via-alba-savigliano` resolves **37 of 37** requirements
through `project → it → eu`. The UK and US profiles carry the bindings that could be
verified against [legislation.gov.uk](https://www.legislation.gov.uk/uksi/2015/51/contents),
[osha.gov](https://www.osha.gov/laws-regs/regulations/standardnumber/1926) and
[ecfr.gov](https://www.ecfr.gov/current/title-29/subtitle-B/chapter-XVII/part-1926); the
rest are left unmapped rather than guessed.

---

## Using CIEO on your own site

**1 — Copy the project template.**

```bash
cp -r data/projects/_template data/projects/my-project
```

Edit `project.yaml`: the asset type (see `data/core/asset_types.csv`), the country, and the
profile chain. Edit `phases.csv` so each of your programme's phases declares which generic
work stages it realises. That mapping is what switches requirements on and off — edge
protection is a live obligation during earthworks and meaningless before and after.

**2 — Pick or write a jurisdiction profile.** If yours exists, name it in `project.yaml`.
If not, see [docs/authoring-a-profile.md](docs/authoring-a-profile.md); it is one YAML file
and two CSVs, and you do not have to map all 37 requirements to start.

**3 — Mark your inspection targets.** In Unity, attach `InspectionTargetMarker` to the
geometry and say how each target should be sampled — along a line, over a surface, or at a
set of fixings. Then run `VisibilityBatchRunner` over your registered photographs.

**4 — Validate and build.**

```bash
python3 src/validate_data.py
python3 src/build_kb.py --project my-project
python3 src/run_reasoning.py
```

### If your requirements differ

They will. `data/templates/requirements_extension.csv` is a blank requirements table with
the same columns; add your own rows and the validator will check them. Requirements scoped
to an asset type you are not building are skipped automatically, so a tunnel project never
evaluates a deck-waterproofing item.

---

## The data model in one table

| File | Rows | What one row is |
|---|---:|---|
| `core/requirements.csv` | 37 | An obligation, with the evidence pattern that fixes what silence means under it. |
| `core/object_classes.csv` | 29 | Something the detector can look for, with the five parameters that decide whether it could be seen. |
| `core/work_stages.csv` | 10 | A generic stage of construction, independent of any project's programme. |
| `core/asset_types.csv` | 7 | A kind of works a requirement may be scoped to. |
| `core/evidence_patterns.csv` | 7 | One of the seven ways a requirement can be settled. |
| `core/jurisdictions.csv` | 4 | A legal system with a profile. |
| `core/decision_thresholds.csv` | 14 | A constant the reasoner is tuned with — in data, not in code. |
| `profiles/<j>/regulations.csv` | — | An instrument: a law, decree or standard. |
| `profiles/<j>/clause_bindings.csv` | 37 | The claim that this jurisdiction grounds this requirement in this clause. |
| `projects/<p>/phases.csv` | — | A phase of this project, and the generic stages it realises. |

Machine-readable [Frictionless Table Schemas](https://specs.frictionlessdata.io/table-schema/)
for all of these are in `schemas/`, generated from the same declaration the validator reads,
so they cannot drift.

### The seven evidence patterns

The most important column in the catalogue. What a non-detection means depends entirely on
what kind of requirement it is — and under two of these, the same silence from the same
detector means opposite things.

| Pattern | Seeing nothing means | n |
|---|---|---:|
| Presence of required object | Either it is missing or you could not see it; the detectability calculation decides which. | 4 |
| Spatial completeness | Nothing at all about the part you did not look at. | 5 |
| Component integrity | The item is limited by the *worst* component, not the average. | 6 |
| Verified absence | Good news — but only in proportion to how sure you are you would have seen it. | 4 |
| Geometric conformance | Not answerable by object detection. | 7 |
| Documentary conformance | Not answerable from photographs. Steel grade is not a visual property. | 9 |
| Material-test conformance | Not answerable from photographs. | 2 |

---

## What CIEO does not do

Said plainly, because these are the first questions a reviewer asks.

- **It is not a detector.** Bring your own. CIEO consumes detections and, crucially, explicit
  non-detections; the reference implementation uses an open-vocabulary detector with no
  fine-tuning, deliberately.
- **The parameters in `object_classes.csv` are not measured on your site.** They are the
  published behaviour of detectors of that kind on classes of that kind. Recalibrate them
  against your own imagery before relying on an absence conclusion.
- **It does not read drawings or certificates.** Eighteen of the thirty-seven reference
  requirements are documentary, geometric or laboratory checks, and CIEO routes them to a
  person rather than pretending otherwise.
- **A profile is not legal advice.** A `VERIFIED` binding means someone checked a clause
  reference against a published text. It does not mean the obligation has been correctly
  interpreted for your contract, your site or your duty holder.
- **It will abstain, often.** On the reference project it settles two requirements and
  abstains or refers on seven. Whether that is better than a system that is wrong three
  times out of nine is a judgement for the organisation using it; CIEO puts both numbers on
  the table.

## Contributing

The most useful contribution is **a jurisdiction profile**. It needs no code, no ontology
knowledge and no 3D model — a YAML file, two CSVs, and somebody who knows where their
country's construction obligations are written down. Partial profiles are welcome and
expected; `UNMAPPED` is a legitimate state.

See [CONTRIBUTING.md](CONTRIBUTING.md) and
[docs/authoring-a-profile.md](docs/authoring-a-profile.md). Open an issue before starting a
profile so two people do not write the same one.

Also wanted: recalibrated object-class parameters from real site imagery, additional asset
types, and translations of the requirement statements.

## Citing

See [CITATION.cff](CITATION.cff). If you use a jurisdiction profile, cite its maintainer as
well — `maintainer` in each `profile.yaml`.

## Licence

Ontology, data and documentation: [CC BY 4.0](LICENSE). Source code:
[MIT](LICENSE-CODE). Use it, change it, sell what you build with it; say where it
came from.
