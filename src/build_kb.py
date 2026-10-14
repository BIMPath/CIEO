# -*- coding: utf-8 -*-
"""Compile the CSVs into one knowledge base, for one project in one set of jurisdictions.

    python3 src/build_kb.py --project via-alba-savigliano
    python3 src/build_kb.py --project my-project --out build/my-kb.ttl

Replaces the single-jurisdiction csv_to_rdf.py of the original release. The difference is
the binding chain: a requirement no longer carries its clause, so the builder resolves one
for it by walking the project's own bindings first, then each profile the project names, in
order, and stopping at the first that offers one. A requirement that reaches the end of the
chain with nothing is emitted anyway, carrying prof:Unmapped, because a requirement nobody
has grounded in law is a fact about the profile and should be visible in the graph rather
than quietly dropped from it.

The CSVs are authoritative. This file is generated. Edit the CSVs and run this again.
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")

PREFIXES = """\
@prefix kb:      <https://w3id.org/cieo/kb#> .
@prefix cieo:    <https://w3id.org/cieo/core#> .
@prefix cst:     <https://w3id.org/cieo/construction#> .
@prefix reg:     <https://w3id.org/cieo/regulation#> .
@prefix insp:    <https://w3id.org/cieo/inspection#> .
@prefix obs:     <https://w3id.org/cieo/observation#> .
@prefix evd:     <https://w3id.org/cieo/evidence#> .
@prefix cmp:     <https://w3id.org/cieo/compliance#> .
@prefix prof:    <https://w3id.org/cieo/profile#> .
@prefix owl:     <http://www.w3.org/2002/07/owl#> .
@prefix rdf:     <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs:    <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd:     <http://www.w3.org/2001/XMLSchema#> .
@prefix skos:    <http://www.w3.org/2004/02/skos/core#> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix prov:    <http://www.w3.org/ns/prov#> .
"""

PATTERN_MAP = {p: f"insp:{p}" for p in (
    "PresenceOfRequired", "SpatialCompleteness", "ComponentIntegrity", "VerifiedAbsence",
    "GeometricConformance", "DocumentaryConformance", "MaterialTestConformance")}
CHECKABILITY_MAP = {"AUTOMATIC": "insp:Automatic", "ASSISTED": "insp:Assisted",
                    "MANUAL": "insp:Manual"}
MODALITY_MAP = {"Visual": "insp:VisualModality", "Geometric": "insp:GeometricModality",
                "Documentary": "insp:DocumentaryModality",
                "MaterialTest": "insp:MaterialTestModality"}
STATUS_MAP = {"VERIFIED": "prof:Verified", "PROPOSED": "prof:Proposed",
              "UNMAPPED": "prof:Unmapped", "NOT_APPLICABLE": "prof:NotApplicable"}
CONFIDENCE_MAP = {"HIGH": "reg:VerifiedClause", "MEDIUM": "reg:ProbableClause",
                  "LOW": "reg:UnverifiedClause", "TO_VERIFY": "reg:UnverifiedClause"}
INSTRUMENT_MAP = {
    "LegislativeDecree": "reg:LegislativeDecree", "MinisterialDecree": "reg:MinisterialDecree",
    "Circular": "reg:Circular", "HarmonisedStandard": "reg:HarmonisedStandard",
    "NationalStandard": "reg:NationalStandard", "ProductStandard": "reg:ProductStandard",
    "ApprovalGuideline": "reg:ApprovalGuideline",
    "ContractSpecification": "reg:ContractSpecification", "SafetyPlan": "reg:ContractSpecification",
    "StatutoryInstrument": "reg:Regulation", "FederalRegulation": "reg:Regulation",
}


def slug(t):
    return re.sub(r"_+", "_", re.sub(r"[^A-Za-z0-9]+", "_", (t or "").strip())).strip("_")


def esc(t):
    return (t.replace("\\", "\\\\").replace('"', '\\"')
             .replace("\n", "\\n").replace("\r", "").replace("\t", "\\t"))


def lit(t, lang=None):
    return f'"{esc(t or "")}"' + (f"@{lang}" if lang else "")


def items(cell):
    return [x.strip() for x in (cell or "").split(";") if x.strip()]


def rd(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def yaml_scalars(path):
    """A deliberately tiny reader: the descriptors are flat on purpose."""
    out = {}
    for line in open(path, encoding="utf-8"):
        if ":" not in line or line.lstrip().startswith("#"):
            continue
        k, v = line.split(":", 1)
        if k != k.lstrip():
            continue
        v = v.split("#", 1)[0].strip()
        if v.startswith("[") or v.endswith("]"):
            out[k.strip()] = [x.strip() for x in v.strip("[]").split(",") if x.strip()]
        elif v and v != ">":
            out[k.strip()] = v.strip('"')
    return out


# ---------------------------------------------------------------------------- resolution
def resolve_bindings(project_dir, chain):
    """Project bindings first, then each profile in order. First hit wins."""
    sources = [("project", os.path.join(project_dir, "clause_bindings.csv"), 0)]
    sources += [(p, os.path.join(DATA, "profiles", p, "clause_bindings.csv"), i + 1)
                for i, p in enumerate(chain)]
    best, unresolved = {}, {}
    for src, path, prec in sources:
        for b in rd(path):
            rid, st = b["requirement_id"], b["binding_status"]
            if st in ("VERIFIED", "PROPOSED") and rid not in best:
                best[rid] = dict(b, _source=src, _precedence=prec)
            elif rid not in best:
                unresolved.setdefault(rid, dict(b, _source=src, _precedence=prec))
    return best, unresolved


def load_regulations(chain, project_dir):
    regs = {}
    for p in reversed(chain):
        for r in rd(os.path.join(DATA, "profiles", p, "regulations.csv")):
            regs[r["regulation_id"]] = dict(r, _profile=p)
    for r in rd(os.path.join(project_dir, "regulations.csv")):
        regs[r["regulation_id"]] = dict(r, _profile="project")
    return regs


# ---------------------------------------------------------------------------- emitters
def emit_profiles(chain, regs):
    out = ["\n" + "#" * 78, "# Jurisdiction profiles in force for this project", "#" * 78, ""]
    for i, p in enumerate(chain):
        meta = yaml_scalars(os.path.join(DATA, "profiles", p, "profile.yaml"))
        out += [f"kb:Profile_{slug(p)} a prof:JurisdictionProfile ;",
                f'    prof:profileId {lit(p)} ;',
                f'    rdfs:label {lit(meta.get("name", p), "en")} ;',
                f'    prof:profileStatus {lit(meta.get("status", "draft"))} ;',
                f'    prof:forJurisdiction reg:{meta.get("jurisdiction", "XX")} ;',
                f"    prof:precedence {i + 1} ."]
        for b in meta.get("builds_on", []) or []:
            out.append(f"kb:Profile_{slug(p)} prof:buildsOn kb:Profile_{slug(b)} .")
        out.append("")
    return out


def emit_stages_and_phases(stages, phases):
    out = ["\n" + "#" * 78, "# Generic work stages and this project's phases", "#" * 78, ""]
    for s in stages:
        out += [f'kb:{s["stage_id"]} a prof:WorkStage ;',
                f'    rdfs:label {lit(s["stage_label"], "en")} ;',
                f'    rdfs:comment {lit(s["description"], "en")} ;',
                f'    prof:stageSequence {s["typical_sequence"]} .', ""]
    for p in phases:
        out += [f'kb:{p["phase_id"]} a cst:ConstructionPhase ;',
                f'    rdfs:label {lit(p["phase_label"], "en")} ;',
                f'    rdfs:comment {lit(p["description"], "en")} ;',
                f'    cst:phaseSequence {p["sequence"]} ;']
        for s in items(p["maps_to_stages"]):
            out.append(f"    prof:realisesStage kb:{s} ;")
        for n in items(p.get("precedes", "")):
            out.append(f"    cst:phasePrecedes kb:{n} ;")
        out[-1] = out[-1].rstrip(" ;") + " ."
        out.append("")
    return out


def emit_regulations(regs):
    out = ["\n" + "#" * 78, "# Regulatory instruments", "#" * 78, ""]
    for rid in sorted(regs):
        r = regs[rid]
        cls = INSTRUMENT_MAP.get(r["instrument_type"], "reg:RegulatorySource")
        out += [f"kb:{slug(rid)} a {cls} ;",
                f'    reg:shortName {lit(r["short_name"])} ;',
                f'    reg:fullTitle {lit(r["full_title"])} ;',
                f'    reg:inJurisdiction reg:{r["jurisdiction"]} ;',
                f'    rdfs:label {lit(r["short_name"], "en")}']
        if r.get("source_url"):
            out[-1] += " ;"
            out.append(f'    dcterms:source <{r["source_url"]}>')
        if r.get("in_force_from"):
            out[-1] += " ;"
            out.append(f'    reg:inForceFrom "{r["in_force_from"]}"^^xsd:date')
        out[-1] += " ."
        out.append("")
    return out


def emit_object_classes(rows):
    out = ["\n" + "#" * 78,
           "# Detector object classes and the parameters that decide observability",
           "#" * 78, ""]
    iris = {}
    for r in rows:
        cid = f"Class_{slug(r['detector_label'])}"
        iris[r["detector_label"]] = f"kb:{cid}"
        out += [f"kb:{cid} a obs:ObjectClass ;",
                f'    skos:prefLabel {lit(r["semantic_class"], "en")} ;',
                f'    obs:detectorLabel {lit(r["detector_label"])} ;',
                f'    obs:charDimInstalled {float(r["char_dim_installed_m"]):.4f} ;',
                f'    obs:minPixelsOnTarget {r["min_px_on_target"]} ;',
                f'    obs:occlusionSensitivity {float(r["occlusion_sensitivity"]):.2f} ;',
                f'    obs:selfOcclusionPrior {float(r["self_occlusion_prior"]):.2f} ;',
                f'    obs:baseRecallRef {float(r["base_recall_ref"]):.2f}']
        if r.get("notes"):
            out[-1] += " ;"
            out.append(f'    rdfs:comment {lit(r["notes"], "en")}')
        out[-1] += " ."
        out.append("")
    for dup, canon in (("nuts", "nut"), ("bolt_dup", "bolt")):
        if dup in iris and canon in iris:
            out.append(f"{iris[dup]} obs:mergedInto {iris[canon]} .")
    out.append("")
    return out, iris


def emit_requirements(reqs, bindings, unresolved, iris, asset_type, phases, warn):
    out = ["\n" + "#" * 78, "# Inspection requirements and their clause bindings",
           "#" * 78, ""]
    clauses, seen = [], set()
    for r in reqs:
        rid = r["requirement_id"]
        assets = items(r["applies_to_asset_types"])
        if asset_type and assets != ["*"] and asset_type not in assets:
            continue
        node = f"kb:{slug(rid)}"
        out += [f"{node} a insp:InspectionRequirement ;",
                f"    insp:requirementId {lit(rid)} ;",
                f'    rdfs:label {lit(rid + " " + r["inspection_item"], "en")} ;',
                f'    insp:inspectionItemLabel {lit(r["inspection_item"])} ;',
                f'    insp:requirementStatement {lit(r["requirement_statement"])} ;',
                f'    insp:expectedCondition {lit(r["expected_condition"])} ;',
                f'    insp:hasEvidencePattern {PATTERN_MAP[r["evidence_pattern"]]} ;',
                f'    prof:appliesToStage kb:{r["stage_ref"]} ;',
                f'    insp:appliesToTargetType cst:{r["target_type"]} ;']
        # The stage is the portable link; the phase is this project's realisation of it.
        # Both are emitted, so the rules keep working on phases while the catalogue stays
        # free of any one project's programme.
        live = [p["phase_id"] for p in phases
                if r["stage_ref"] in items(p["maps_to_stages"])]
        for ph in live:
            out.append(f"    insp:appliesToPhase kb:{ph} ;")
        if not live:
            warn.append(f'{rid}: stage {r["stage_ref"]} is not realised by any phase of this '
                        f'project, so the requirement will never become live')
        for a in assets:
            if a != "*":
                out.append(f"    prof:appliesToAssetType kb:Asset_{slug(a)} ;")
        if r["checkability"] in CHECKABILITY_MAP:
            out.append(f'    insp:hasCheckability {CHECKABILITY_MAP[r["checkability"]]} ;')
        if r["evidence_modality"] in MODALITY_MAP:
            out.append(f'    insp:requiresModality {MODALITY_MAP[r["evidence_modality"]]} ;')
        for lab in items(r.get("required_classes")):
            if lab in iris:
                out.append(f"    insp:requiresObjectClass {iris[lab]} ;")
            else:
                warn.append(f"{rid}: required class {lab!r} is not in the detector vocabulary")
        for lab in items(r.get("prohibited_classes")):
            if lab in iris:
                out.append(f"    insp:prohibitsObjectClass {iris[lab]} ;")
            else:
                warn.append(f"{rid}: prohibited class {lab!r} is not in the vocabulary")
        if r.get("required_coverage"):
            out.append(f'    insp:requiredCoverage {r["required_coverage"]} ;')

        b = bindings.get(rid) or unresolved.get(rid)
        if b and b.get("regulation_id"):
            cid = f"Clause_{slug(b['regulation_id'])}_{slug(b['clause_reference'])[:40]}"
            if cid not in seen:
                seen.add(cid)
                conf = CONFIDENCE_MAP.get(b.get("confidence", ""), "reg:UnverifiedClause")
                clauses += [f"kb:{cid} a reg:RegulatoryClause ;",
                            f'    reg:clauseReference {lit(b["clause_reference"])} ;',
                            f"    reg:hasClauseConfidence {conf} .",
                            f'kb:{slug(b["regulation_id"])} reg:hasClause kb:{cid} .', ""]
            out.append(f"    insp:specifiedBy kb:{cid} ;")
        bid = f"kb:Binding_{slug(rid)}"
        out.append(f"    prof:hasBinding {bid} ;")
        if r.get("notes"):
            out.append(f'    rdfs:comment {lit(r["notes"], "en")} ;')
        out[-1] = out[-1].rstrip(" ;") + " ."

        st = STATUS_MAP.get((b or {}).get("binding_status", "UNMAPPED"), "prof:Unmapped")
        out += ["", f"{bid} a prof:ClauseBinding ;",
                f"    prof:bindsRequirement {node} ;",
                f"    prof:hasBindingStatus {st} ;",
                f'    prof:precedence {(b or {}).get("_precedence", 99)} ;',
                f'    dcterms:source {lit((b or {}).get("_source", "none"))}']
        if b and b.get("regulation_id"):
            out[-1] += " ;"
            out.append(f"    prof:bindsToClause kb:Clause_{slug(b['regulation_id'])}_"
                       f"{slug(b['clause_reference'])[:40]}")
        if b and b.get("source_url"):
            out[-1] += " ;"
            out.append(f'    prof:sourceUrl <{b["source_url"]}>')
        out[-1] += " ."
        out.append("")
        if not b or b.get("binding_status") in ("UNMAPPED", None):
            warn.append(f"{rid}: no clause binding in this profile chain")
    return clauses + out


def emit_assets(assets):
    out = ["\n" + "#" * 78, "# Asset types", "#" * 78, ""]
    for a in assets:
        out += [f'kb:Asset_{slug(a["asset_type_id"])} a prof:AssetType ;',
                f'    rdfs:label {lit(a["label"], "en")} ;',
                f'    rdfs:comment {lit(a["description"], "en")} .', ""]
    return out


# ---------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description="Compile a CIEO knowledge base for one project.")
    ap.add_argument("--project", required=True, help="a folder under data/projects/")
    ap.add_argument("--out", default=None, help="output .ttl (default build/<project>-kb.ttl)")
    ap.add_argument("--all-assets", action="store_true",
                    help="include requirements scoped to other asset types")
    args = ap.parse_args()

    pdir = os.path.join(DATA, "projects", args.project)
    if not os.path.isdir(pdir):
        sys.exit(f"no such project: {args.project}")
    meta = yaml_scalars(os.path.join(pdir, "project.yaml"))
    chain = meta.get("profiles", []) or []
    asset = None if args.all_assets else meta.get("asset_type")

    reqs = rd(os.path.join(DATA, "core", "requirements.csv"))
    stages = rd(os.path.join(DATA, "core", "work_stages.csv"))
    assets = rd(os.path.join(DATA, "core", "asset_types.csv"))
    classes = rd(os.path.join(DATA, "core", "object_classes.csv"))
    phases = rd(os.path.join(pdir, "phases.csv"))
    regs = load_regulations(chain, pdir)
    bindings, unresolved = resolve_bindings(pdir, chain)

    warn: list[str] = []
    cls_block, iris = emit_object_classes(classes)
    header = [PREFIXES, "", "<https://w3id.org/cieo/kb>", "    a owl:Ontology ;",
              f'    dcterms:title {lit("CIEO knowledge base — " + meta.get("name", args.project), "en")} ;',
              '    dcterms:description """Generated by src/build_kb.py from the CSVs under data/.',
              "",
              f"Project : {args.project}",
              f"Asset   : {meta.get('asset_type', 'any')}",
              f"Profiles: {' then '.join(['project'] + chain)}",
              "",
              "DO NOT EDIT. The CSVs are authoritative; edit those and run the builder again.",
              'Hand-editing this file is how the checklist a domain expert reviews and the graph',
              'the reasoner runs on stop being the same thing."""@en ;',
              f'    dcterms:created "{date.today().isoformat()}"^^xsd:date ;',
              "    owl:imports <https://w3id.org/cieo> , <https://w3id.org/cieo/profile> .", ""]

    body = (header + emit_profiles(chain, regs) + emit_assets(assets)
            + emit_stages_and_phases(stages, phases) + emit_regulations(regs) + cls_block
            + emit_requirements(reqs, bindings, unresolved, iris, asset, phases, warn))

    out = args.out or os.path.join(ROOT, "build", f"{args.project}-kb.ttl")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    text = "\n".join(body)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(text)

    n_v = sum(1 for b in bindings.values() if b["binding_status"] == "VERIFIED")
    print(f"wrote {out} ({len(text.splitlines())} lines)")
    print(f"  requirements emitted : {sum(1 for l in body if l.startswith('kb:IR'))}")
    print(f"  bindings resolved    : {len(bindings)}  ({n_v} verified)")
    print(f"  profile chain        : {' -> '.join(['project'] + chain)}")
    if warn:
        print(f"\n{len(warn)} coverage note(s) — findings to report, not bugs to hide:")
        for w in warn:
            print(f"  - {w}")


if __name__ == "__main__":
    main()
