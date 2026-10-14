# Contributing to CIEO

The most valuable thing you can add is a **jurisdiction profile**. It needs no code, no
ontology knowledge and no 3D model — one YAML file, two CSVs, and somebody who knows where
their country's construction obligations are written down.

Open an issue first, titled `profile: <country>`, so two people do not write the same one.

## Ground rules

**A binding you have not checked is `PROPOSED`.** Not `VERIFIED`. The whole framework exists
to stop a system asserting more than its evidence supports, and a clause mapping is evidence
like any other. `VERIFIED` means you opened the published instrument, read the clause, and
recorded the URL where you read it. The validator enforces the URL; your judgement enforces
the rest.

**An absent mapping is `UNMAPPED`, written down.** Do not delete the row. A profile that
covers eleven of thirty-seven requirements and says so is more useful than one that covers
eleven and looks complete.

**`NOT_APPLICABLE` is a real finding.** If you checked and your jurisdiction genuinely
imposes no equivalent obligation, say that. It is different from nobody having looked, and
the difference is interesting.

**Do not edit generated files.** `build/` is output. The CSVs under `data/` are
authoritative; change those and run the builder.

## Adding a profile

See [docs/authoring-a-profile.md](docs/authoring-a-profile.md) for the walkthrough. In
short:

```bash
mkdir -p data/profiles/xx
cp data/templates/profile.yaml        data/profiles/xx/
cp data/templates/regulations.csv     data/profiles/xx/
cp data/templates/clause_bindings.csv data/profiles/xx/
# add a row to data/core/jurisdictions.csv
python3 src/validate_data.py --profile xx
```

## Adding or changing a requirement

Requirements in `data/core/requirements.csv` must be **jurisdiction-neutral**. If a
statement only makes sense under one country's law, it belongs in that country's profile as
a project- or profile-level extension, not in the core.

Before adding one, check it is not already there under a different name. The catalogue is
small on purpose; a requirement that cannot be stated without naming a specific instrument
is usually two requirements.

## Changing object-class parameters

`data/core/object_classes.csv` carries five numbers per class that decide whether something
could have been seen. Changing them changes every absence conclusion downstream, so:

- say in `parameter_source` where the new value comes from;
- give the imagery and the conditions it was measured under in `notes`;
- open it as its own pull request, not bundled with other changes.

## Running the checks

```bash
python3 src/validate_data.py          # what CI runs
python3 src/export_schemas.py         # regenerate schemas/ if you changed a column
python3 src/build_kb.py --project via-alba-savigliano
```

CI runs the validator on every pull request and fails on any error. Warnings are advisory;
read them anyway, since most of them are telling you about a gap worth filling.

## Code

Standard library only in `src/validate_data.py`, `src/build_kb.py`, `src/tableschema.py` and
`src/ttl_tools.py` — the data layer has to run for a domain expert with nothing installed.
The reasoning modules may use `numpy` and `scipy`.
