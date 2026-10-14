# -*- coding: utf-8 -*-
"""Check every CSV in data/ against its declared schema and every cross-reference between them.

    python3 src/validate_data.py                # everything
    python3 src/validate_data.py --profile gb   # one profile
    python3 src/validate_data.py --coverage     # the coverage report only

Run it before you open a pull request; the CI workflow runs exactly this.

Nothing here needs a dependency. The point of a validator that only uses the standard
library is that anyone can run it, including the domain expert who edited the CSV.
"""
from __future__ import annotations

import argparse
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
sys.path.insert(0, HERE)
from tableschema import TABLES                                        # noqa: E402

RESET, RED, YEL, GRN, DIM = "\033[0m", "\033[31m", "\033[33m", "\033[32m", "\033[2m"
if not sys.stdout.isatty() or os.environ.get("NO_COLOR"):
    RESET = RED = YEL = GRN = DIM = ""

errors: list[str] = []
warnings: list[str] = []


def err(where, msg):
    errors.append(f"{where}: {msg}")


def warn(where, msg):
    warnings.append(f"{where}: {msg}")


def read(path):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        rdr = csv.DictReader(fh)
        return list(rdr), (rdr.fieldnames or [])


def check_table(path, spec, label, index):
    """Validate one file against one spec. `index` holds {table: {column: set(values)}}."""
    rows, header = read(path)
    names = [f[0] for f in spec["fields"]]
    if header != names:
        missing = [n for n in names if n not in header]
        extra = [h for h in header if h not in names]
        if missing:
            err(label, f"missing column(s): {', '.join(missing)}")
        if extra:
            warn(label, f"column(s) not in the schema, ignored: {', '.join(extra)}")
        if not missing and header != names:
            warn(label, "columns are in a different order from the schema")

    seen_keys = set()
    for n, row in enumerate(rows, 2):
        at = f"{label} line {n}"
        key = spec.get("key")
        if key:
            k = (row.get(key) or "").strip()
            if not k:
                err(at, f"empty {key}")
            elif k in seen_keys:
                err(at, f"duplicate {key} {k!r}")
            seen_keys.add(k)

        for fname, required, kind, extra in spec["fields"]:
            raw = (row.get(fname) or "").strip()
            if not raw:
                if required:
                    err(at, f"{fname} is required and empty")
                continue
            if kind == "enum" and raw not in extra:
                err(at, f"{fname}={raw!r} is not one of {', '.join(repr(e) for e in extra if e)}")
            elif kind in ("num", "int"):
                try:
                    v = float(raw) if kind == "num" else int(raw)
                except ValueError:
                    err(at, f"{fname}={raw!r} is not a {kind}")
                    continue
                if extra and not (extra[0] <= v <= extra[1]):
                    err(at, f"{fname}={v} is outside [{extra[0]}, {extra[1]}]")
            elif kind == "url" and not raw.startswith(("http://", "https://")):
                err(at, f"{fname}={raw!r} is not an http(s) URL")
            elif kind == "ref":
                tbl, col = extra
                pool = index.get(tbl, {}).get(col)
                if pool is not None and raw not in pool:
                    err(at, f"{fname}={raw!r} does not resolve to {tbl}:{col}")
    return rows


def build_index():
    idx = {}
    for rel in ("core/requirements.csv", "core/work_stages.csv", "core/asset_types.csv",
                "core/jurisdictions.csv", "core/object_classes.csv",
                "core/evidence_patterns.csv"):
        p = os.path.join(DATA, rel)
        if not os.path.exists(p):
            err(rel, "file is missing")
            continue
        rows, _ = read(p)
        idx[rel] = {c: {(r.get(c) or "").strip() for r in rows} for c in (rows[0] if rows else {})}
    return idx


def main():
    ap = argparse.ArgumentParser(description="Validate the CIEO data tree.")
    ap.add_argument("--profile", help="validate only this profile id")
    ap.add_argument("--coverage", action="store_true", help="print the coverage report only")
    args = ap.parse_args()

    idx = build_index()

    # ---------------------------------------------------------------- core
    if not args.coverage:
        for rel, spec in TABLES.items():
            if not rel.startswith("core/"):
                continue
            p = os.path.join(DATA, rel)
            if os.path.exists(p):
                check_table(p, spec, rel, idx)
            else:
                err(rel, "file is missing")

    reqs, _ = read(os.path.join(DATA, "core", "requirements.csv"))
    req_ids = [r["requirement_id"] for r in reqs]
    labels = {(r.get("detector_label") or "").strip()
              for r in read(os.path.join(DATA, "core", "object_classes.csv"))[0]}
    assets = idx["core/asset_types.csv"]["asset_type_id"]

    # requirement-level cross checks the plain schema cannot express
    if not args.coverage:
        for r in reqs:
            at = f"core/requirements.csv {r['requirement_id']}"
            for a in [x.strip() for x in r["applies_to_asset_types"].split(";") if x.strip()]:
                if a != "*" and a not in assets:
                    err(at, f"applies_to_asset_types {a!r} is not an asset type")
            for col in ("required_classes", "prohibited_classes"):
                for c in [x.strip() for x in (r.get(col) or "").split(";") if x.strip()]:
                    if c not in labels:
                        warn(at, f"{col} {c!r} is not in the detector vocabulary "
                                 f"(a coverage gap, not necessarily a mistake)")
            if r["evidence_pattern"] == "SpatialCompleteness" and not r["required_coverage"]:
                err(at, "a spatial-completeness requirement must state required_coverage")
            if r["detectability_tier"] == "NON_VISUAL" and r["checkability"] == "AUTOMATIC":
                err(at, "non-visual requirements cannot be AUTOMATIC")

    # ---------------------------------------------------------------- profiles
    pdir = os.path.join(DATA, "profiles")
    profiles = sorted(d for d in os.listdir(pdir)
                      if os.path.isdir(os.path.join(pdir, d)) and not d.startswith("_"))
    if args.profile:
        if args.profile not in profiles:
            print(f"{RED}no such profile: {args.profile}{RESET}  (have: {', '.join(profiles)})")
            return 2
        profiles = [args.profile]

    report = []
    for pid in profiles:
        d = os.path.join(pdir, pid)
        regs, _ = read(os.path.join(d, "regulations.csv"))
        reg_ids = {r["regulation_id"] for r in regs}
        reg_url = {r["regulation_id"]: (r.get("source_url") or "").strip() for r in regs}
        if not args.coverage:
            check_table(os.path.join(d, "regulations.csv"),
                        TABLES["profile/regulations.csv"], f"profiles/{pid}/regulations.csv", idx)
            check_table(os.path.join(d, "clause_bindings.csv"),
                        TABLES["profile/clause_bindings.csv"],
                        f"profiles/{pid}/clause_bindings.csv", idx)
        binds, _ = read(os.path.join(d, "clause_bindings.csv"))

        counts = {"VERIFIED": 0, "PROPOSED": 0, "UNMAPPED": 0, "NOT_APPLICABLE": 0}
        bound = set()
        for n, b in enumerate(binds, 2):
            at = f"profiles/{pid}/clause_bindings.csv line {n}"
            st = b["binding_status"]
            counts[st] = counts.get(st, 0) + 1
            bound.add(b["requirement_id"])
            if st in ("VERIFIED", "PROPOSED"):
                if not b["regulation_id"]:
                    err(at, f"a {st} binding must name a regulation")
                elif b["regulation_id"] not in reg_ids:
                    err(at, f"regulation_id {b['regulation_id']!r} is not in this profile's "
                            f"regulations.csv")
                if not b["clause_reference"]:
                    err(at, f"a {st} binding must give a clause reference")
            if (st == "VERIFIED" and not args.coverage
                    and not b["source_url"] and not reg_url.get(b["regulation_id"])):
                err(at, "a VERIFIED binding needs a citable source: put a source_url on the "
                        "binding, or on the instrument in regulations.csv")
            if st in ("UNMAPPED", "NOT_APPLICABLE") and b["regulation_id"]:
                err(at, f"a {st} binding must not name a regulation")

        for rid in req_ids:
            if rid not in bound:
                warn(f"profiles/{pid}", f"{rid} has no row at all; add an UNMAPPED row so "
                                        f"the gap is countable")
        report.append((pid, counts, len(req_ids)))

    # ---------------------------------------------------------------- projects
    jdir = os.path.join(DATA, "projects")
    if os.path.isdir(jdir) and not args.coverage:
        stages = idx["core/work_stages.csv"]["stage_id"]
        for proj in sorted(os.listdir(jdir)):
            pp = os.path.join(jdir, proj)
            ph = os.path.join(pp, "phases.csv")
            if proj.startswith("_") or not os.path.isdir(pp) or not os.path.exists(ph):
                continue
            rows = check_table(ph, TABLES["project/phases.csv"],
                               f"projects/{proj}/phases.csv", idx)
            ids = {r["phase_id"] for r in rows}
            for n, r in enumerate(rows, 2):
                at = f"projects/{proj}/phases.csv line {n}"
                for s in [x.strip() for x in r["maps_to_stages"].split(";") if x.strip()]:
                    if s not in stages:
                        err(at, f"maps_to_stages {s!r} is not a stage in core/work_stages.csv")
                for s in [x.strip() for x in (r.get("precedes") or "").split(";") if x.strip()]:
                    if s not in ids:
                        err(at, f"precedes {s!r} is not a phase of this project")
            covered = {s for r in rows for s in r["maps_to_stages"].split(";") if s.strip()}
            unreachable = [r["requirement_id"] for r in reqs if r["stage_ref"] not in covered]
            if unreachable:
                warn(f"projects/{proj}", f"{len(unreachable)} requirement(s) bind to a stage "
                                         f"this project has no phase for; they will never be "
                                         f"evaluated")

    # ---------------------------------------------------------------- resolved coverage
    resolved = []
    if os.path.isdir(jdir):
        for proj in sorted(os.listdir(jdir)):
            pp = os.path.join(jdir, proj)
            cfg = os.path.join(pp, "project.yaml")
            if proj.startswith("_") or not os.path.isdir(pp) or not os.path.exists(cfg):
                continue
            chain = []
            for line in open(cfg, encoding="utf-8"):
                if line.strip().startswith("profiles:"):
                    val = line.split(":", 1)[1].split("#", 1)[0].strip().strip("[]")
                    chain = [x.strip() for x in val.split(",") if x.strip()]
                    break
            best = {}
            order = [("project", os.path.join(pp, "clause_bindings.csv"))] + \
                    [(c, os.path.join(pdir, c, "clause_bindings.csv")) for c in chain]
            for src, path in order:
                if not os.path.exists(path):
                    continue
                for b in read(path)[0]:
                    st = b["binding_status"]
                    if st in ("VERIFIED", "PROPOSED") and b["requirement_id"] not in best:
                        best[b["requirement_id"]] = (src, st)
            nv = sum(1 for v in best.values() if v[1] == "VERIFIED")
            resolved.append((proj, chain, nv, len(best) - nv, len(req_ids) - len(best),
                             len(req_ids)))

    # ---------------------------------------------------------------- output
    print()
    print(f"{'profile':<10}{'verified':>10}{'proposed':>10}{'unmapped':>10}{'coverage':>11}")
    print("-" * 51)
    for pid, c, total in report:
        cov = (c["VERIFIED"] + c["PROPOSED"]) / total if total else 0
        tone = GRN if cov > 0.9 else (YEL if cov > 0.3 else RED)
        print(f"{pid:<10}{c['VERIFIED']:>10}{c['PROPOSED']:>10}{c['UNMAPPED']:>10}"
              f"{tone}{cov:>10.0%}{RESET}")
    print()

    if resolved:
        print("resolved per project (project bindings first, then the profile chain)")
        print(f"{'project':<26}{'chain':<14}{'verified':>9}{'proposed':>10}"
              f"{'unmapped':>10}{'coverage':>11}")
        print("-" * 80)
        for proj, chain, nv, np_, nu, total in resolved:
            cov = (nv + np_) / total if total else 0
            tone = GRN if cov > 0.9 else (YEL if cov > 0.3 else RED)
            print(f"{proj[:25]:<26}{'+'.join(chain)[:13]:<14}{nv:>9}{np_:>10}{nu:>10}"
                  f"{tone}{cov:>10.0%}{RESET}")
        print()

    for w in warnings:
        print(f"{YEL}warning{RESET}  {w}")
    for e in errors:
        print(f"{RED}error{RESET}    {e}")

    print()
    if errors:
        print(f"{RED}FAILED{RESET}  {len(errors)} error(s), {len(warnings)} warning(s)")
        return 1
    print(f"{GRN}OK{RESET}      {len(req_ids)} requirements, {len(report)} profile(s), "
          f"{len(warnings)} warning(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
