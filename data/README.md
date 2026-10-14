# `data/` — the content layer

Everything CIEO reasons over is here, as CSV. Not as RDF, and not in code. A construction
professional has to be able to open the checklist, argue with it and correct it without
meeting Turtle, and the moment the authoritative copy lives in a `.ttl` file that stops
being true.

`build/` holds generated RDF. It is output. Delete it whenever you like.

```
core/        jurisdiction-neutral, project-neutral  -- what must be true
profiles/    one folder per legal system            -- which clause says so
projects/    one folder per site                    -- where, when, what asset
templates/   blank copies with the right columns
```

## core/

| File | One row is |
|---|---|
| `requirements.csv` | An obligation, with the evidence pattern that fixes what silence means under it. **No legal reference** — that is the point. |
| `object_classes.csv` | Something a detector can be asked to find, with the five parameters that decide whether it could have been seen. |
| `work_stages.csv` | A generic stage of construction. Requirements bind to these, not to any project's phases. |
| `asset_types.csv` | A kind of works a requirement may be scoped to. |
| `evidence_patterns.csv` | One of the seven ways a requirement can be settled, and what a non-detection means under it. |
| `checkability_levels.csv` | AUTOMATIC, ASSISTED, MANUAL. |
| `detectability_tiers.csv` | COARSE, MEDIUM, FINE, NON_VISUAL. |
| `jurisdictions.csv` | A legal system for which a profile exists or is planned. |
| `decision_thresholds.csv` | Every constant the reasoner is tuned with. In data so it can be audited and changed without touching code. |

A note on `requirement_id`: the `Pn` in `IR-P3-008` is historical, from the reference
project's phase numbering. The authoritative link to a stage is the `stage_ref` column. The
ids were left alone so that every citation of them in the literature keeps working.

## profiles/

| File | One row is |
|---|---|
| `profile.yaml` | The profile itself: who maintains it, what it builds on, how complete it is. |
| `regulations.csv` | An instrument — a law, decree, standard or guideline. |
| `clause_bindings.csv` | The claim that this jurisdiction grounds this requirement in this clause, and how well checked that claim is. |

Profiles compose. `builds_on` in the YAML says which profile supplies what this one does
not override; a CEN member state builds on `eu`.

## projects/

| File | One row is |
|---|---|
| `project.yaml` | The asset type, the country, and the ordered list of profiles that apply. |
| `phases.csv` | A phase of this project's programme, declaring which generic stages it realises. |
| `regulations.csv` | A contract-level instrument: a specification, a site safety plan. |
| `clause_bindings.csv` | A binding that overrides the national and supranational profiles. |
| `site.ttl` | The site A-Box: the actual zones, elements and targets, with their IFC identities. |

`_template/` is a working skeleton. Copy it, do not edit it.

## Resolution order

For any requirement, a binding is looked for in this order, and the first hit wins:

```
projects/<p>/clause_bindings.csv        precedence 0   contract beats
profiles/<first in chain>/              precedence 1   national beats
profiles/<second in chain>/             precedence 2   supranational
```

Nothing found means the requirement is emitted carrying `prof:Unmapped`. It is not dropped.

## Editing

Edit the CSV, then:

```bash
python3 src/validate_data.py                           # must pass
python3 src/build_kb.py --project via-alba-savigliano  # regenerate
```

The validator checks types, enumerations, numeric ranges, every cross-reference between
tables, and a handful of rules the schema cannot express — a spatial-completeness
requirement with no required coverage, a non-visual requirement marked AUTOMATIC, a project
phase mapped to a stage that does not exist, a verified binding with nothing to verify it
against.

Machine-readable schemas for every table are in `../schemas/`, generated from the same
declaration the validator reads.
