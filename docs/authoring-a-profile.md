# Authoring a jurisdiction profile

A profile says where, in your country's law, each of CIEO's requirements is written down.
It is one YAML file and two CSVs. You need no code, no ontology knowledge and no 3D model —
you need to know where your construction obligations live, and you need to be willing to
write `UNMAPPED` when you do not.

Budget about two hours for a first useful profile covering the safety requirements, and
rather longer if you intend to map the documentary and material-test items, which tend to
be scattered across product standards.

---

## 1. Claim it

Open an issue titled `profile: <country>`. Two people writing the Dutch profile in parallel
helps nobody.

## 2. Create the folder

```bash
mkdir -p data/profiles/nl
cp data/templates/profile.yaml        data/profiles/nl/
cp data/templates/regulations.csv     data/profiles/nl/
cp data/templates/clause_bindings.csv data/profiles/nl/
```

Use the lower-case ISO 3166-1 alpha-2 code where one applies. Supranational bodies get a
short name: `eu`.

Add one row to `data/core/jurisdictions.csv`:

```csv
NL,Netherlands,NLD,national,Inspectie SZW,nl,profiles/nl,draft,"Arbowet and Arbobesluit; Bouwbesluit for structural items."
```

## 3. Fill in `profile.yaml`

```yaml
profile_id: nl
name: Netherlands
jurisdiction: NL
language: nl
status: draft                 # draft -> scaffold -> complete
cieo_version: "1.0"
description: >
  Dutch occupational safety law (Arbowet, Arbobesluit) and the Bouwbesluit, for bridge and
  building works. Product conformity is left to the EU profile.
builds_on: ["eu"]             # a CEN member state almost always builds on eu
maintainer: Your Name <you@example.org>
```

`builds_on` matters. If you are in a CEN member state, say `["eu"]` and do not re-map the
EN standards — the EU profile already carries them, and a project naming `[nl, eu]` picks
them up automatically.

## 4. List your instruments

`regulations.csv`, one row per law, decree or standard:

```csv
regulation_id,short_name,full_title,jurisdiction,instrument_type,domain,in_force_from,source_url,notes
REG-NL-ARBOBESLUIT,Arbobesluit,"Arbeidsomstandighedenbesluit",NL,GovernmentDecree,OccupationalSafety,1997-07-01,https://wetten.overheid.nl/BWBR0008498,
```

- `regulation_id` — your own stable key. Prefix with `REG-<JUR>-` so it cannot collide.
- `source_url` — **the single most valuable column**. A free, citable location for the
  text. Without one here or on the individual binding, no binding against this instrument
  can be `VERIFIED`, and the validator will say so.
- `instrument_type` — free text; `LegislativeDecree`, `StatutoryInstrument`,
  `FederalRegulation`, `HarmonisedStandard`, `NationalStandard`, `ProductStandard`,
  `ContractSpecification` are already understood by the knowledge-base builder. Anything
  else falls back to a generic regulatory source, which is fine.

## 5. Bind the requirements

`clause_bindings.csv`, one row per requirement. **Start with a row for every one of the 37**
marked `UNMAPPED`, then fill them in as you go. The validator will tell you if you miss one.

```csv
requirement_id,regulation_id,clause_reference,binding_status,confidence,source_url,note
IR-P1-003,REG-NL-ARBOBESLUIT,"Artikel 8.1-8.3",VERIFIED,HIGH,https://wetten.overheid.nl/BWBR0008498#Hoofdstuk8,
IR-P4-025,,,UNMAPPED,,,"Lifting is in the Arbobesluit somewhere; not yet located."
```

Read `data/core/requirements.csv` alongside. The `requirement_statement` column is written
to be jurisdiction-neutral on purpose — your job is to find the clause that imposes *that*
obligation, not a clause that mentions the same objects.

### Which status to use

| | |
|---|---|
| `VERIFIED` | You opened the published instrument, read the clause, and the URL in `source_url` (here or on the instrument) is where you read it. |
| `PROPOSED` | You are fairly sure, and you have not checked the text. Most first-pass work is this. |
| `UNMAPPED` | Nobody has looked yet. The default. |
| `NOT_APPLICABLE` | You looked, and your jurisdiction imposes no equivalent obligation. Say why in `note` — this is a genuinely interesting finding. |

Do not promote a binding to `VERIFIED` because you are confident. Confidence is what the
separate `confidence` column is for. `VERIFIED` is a claim about evidence, and this project
is about not overclaiming from evidence.

### When nothing fits

Three situations, three different answers:

- **The obligation exists but is split across several clauses.** Add several rows for the
  same `requirement_id`; the builder uses the first, and the others are recorded.
- **Your law imposes an obligation CIEO has no requirement for.** Add it to
  `data/core/requirements.csv` *if it is jurisdiction-neutral once stated* — most safety
  obligations are. If it only makes sense under your law, keep it in a project overlay.
- **Your jurisdiction genuinely has no equivalent.** `NOT_APPLICABLE`, with a note.

## 6. Check it

```bash
python3 src/validate_data.py --profile nl
```

You will get a coverage line and a list of errors and warnings. Errors must be fixed;
warnings are usually telling you about a gap worth filling. Then make a project that uses
it and see the composition work:

```bash
python3 src/build_kb.py --project my-project
```

## 7. Open the pull request

Include in the description: what the profile covers, what it deliberately does not, and how
you verified the bindings you marked `VERIFIED`. Set `status` honestly —

- `draft` — you are still working
- `scaffold` — a usable subset, most requirements unmapped
- `complete` — every requirement has a binding or a reasoned `NOT_APPLICABLE`

---

## A worked fragment

Requirement `IR-P3-008`, edge protection at an excavation, in four jurisdictions. Same
obligation, four different places in four legal systems — which is the whole argument for
separating the two:

| Profile | Instrument | Clause | Status |
|---|---|---|---|
| `it` | D.Lgs. 81/2008 | Art. 118 comma 3; Allegato XVIII punto 4 | PROPOSED |
| `gb` | CDM 2015 | Regulation 22 — Excavations | VERIFIED |
| `us` | 29 CFR 1926 | 1926.501 — Duty to have fall protection | VERIFIED |
| `eu` | — | — | UNMAPPED (occupational safety is a member-state competence) |

The last row is not a gap in the work. It is the correct answer, and recording it is how a
reader learns that EU-level law is not where this obligation lives.
