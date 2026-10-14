# The data model

Six ideas. Everything else in CIEO follows from them.

## 1. A requirement does not carry its clause

"Workers shall wear head protection" is the same obligation everywhere. Which instrument
imposes it is not. So `core/requirements.csv` holds the obligation with no legal reference
at all, and a *clause binding* in a jurisdiction profile supplies the grounding.

This is the change that makes the catalogue portable, and it is also more truthful: the
original flat table asserted that an obligation and an Italian article were the same object,
which they are not.

## 2. A binding is a claim, and carries its own evidence

`prof:ClauseBinding` is reified rather than expressed as a direct property, because the
claim has provenance: who asserted it, against which published text, with what confidence,
on what date. A compliance finding that cites a clause is only as good as the binding
behind it, and CIEO refuses to pretend otherwise — `VERIFIED` requires a citable URL, and
a SHACL shape warns when a settled decision rests on a binding that is merely `PROPOSED`.

## 3. Requirements bind to generic stages, not to project phases

A requirement that says "applies during phase P3" is tied to the programme of the project it
was written for. A requirement that says "applies during earthworks" is not. So requirements
reference `core/work_stages.csv`, and each project's `phases.csv` declares which generic
stages its phases realise.

This is what makes an obligation switch on and off correctly: edge protection is live during
excavation, meaningless before it, and meaningless after backfill.

## 4. The evidence pattern decides what silence means

Seven patterns, and under two of them the same silence from the same detector means
opposite things. Under `PresenceOfRequired`, finding no barrier is evidence of
non-compliance. Under `VerifiedAbsence`, finding no worker inside an exclusion zone is
evidence of *compliance*. Applying one rule to every requirement is the mistake that makes
detection-driven compliance checking overclaim.

In both cases the conclusion is only licensed if the detector would have spoken had there
been something to speak about — which is what the rest of the framework computes.

## 5. Observability is measured, not assumed

Five numbers per target and viewpoint, computed against model geometry rather than read off
the image: coverage, occluded fraction, standoff, incidence angle, ground sample distance.
The image cannot report what fraction of a barrier fell outside its own frame, and it
certainly cannot report what fraction was hidden behind a spoil heap.

Those five, plus five published parameters per object class, give the probability that the
detector would have found the object had it been there.

## 6. Sufficiency gates the decision; it does not annotate it

Two questions, asked in order:

1. Could this evidence settle the question?
2. What does it say?

A SHACL constraint makes it structurally impossible to answer the second without having
answered the first. Abstention is a first-class outcome and must come with an instruction —
an abstention with no instruction leaves the inspector no better off than no system at all.

---

## How the pieces connect

```
core/requirements.csv ──────────┐
core/work_stages.csv  ──────────┤
core/object_classes.csv ────────┤
                                ├──→ src/build_kb.py ──→ build/<project>-kb.ttl
profiles/<j>/clause_bindings ───┤                              │
profiles/<j>/regulations.csv ───┤                              │
                                │                              ↓
projects/<p>/phases.csv ────────┤                     rules/inspection_rules.rq
projects/<p>/site.ttl ──────────┘                              │
                                                               ↓
unity/VisibilityBatchRunner.cs ──→ observation conditions ─→ src/sufficiency.py
your detector ───────────────────→ detections + explicit     │
                                   non-detections            ↓
                                                     shapes/cieo-shapes.ttl
                                                               │
                                                               ↓
                                                     src/decision.py → a state
```

Four states come out: `Compliant`, `NonCompliant`, `InsufficientEvidence`,
`RequiresHumanVerification`. Two more exist for items the system was never asked to settle:
`NotApplicable` and `OutOfAutomaticScope`.

## Ontology modules

| Module | Defines |
|---|---|
| `core` | Agents, places, assertions, the provenance spine, the unit-interval datatype. |
| `construction` | Project, phases, work zones, elements, equipment, workers. |
| `regulation` | Sources, clauses, conditions, thresholds, temporal validity of law. |
| `inspection` | Requirements, targets, items, the seven evidence patterns. |
| `observation` | Viewpoints, photographs, detections and **explicit non-detections**. |
| `evidence` | Observation conditions, calibrated detectability, evidence sufficiency. |
| `compliance` | Decision states, the rule that produced each, traceability records. |
| `profile` | Jurisdiction profiles, clause bindings, asset types, work stages. |
| `ifc-alignment` | The tie to ifcOWL. A mapping, not an equality — IFC wraps its identifiers. |
