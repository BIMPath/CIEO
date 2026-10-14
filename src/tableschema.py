# -*- coding: utf-8 -*-
"""The single declaration of what every CIEO table looks like.

The validator, the knowledge-base builder and the published JSON schemas all read this
file, so a column cannot be added in one place and forgotten in another.

Field spec: (name, required, kind, extra)
    kind   "str" | "enum" | "num" | "int" | "bool" | "url" | "list" | "ref"
    extra  for enum: the permitted values
           for num:  (lo, hi)
           for list: the separator
           for ref:  (table, column) that each item must resolve to
"""

PATTERNS = ["PresenceOfRequired", "SpatialCompleteness", "ComponentIntegrity",
            "VerifiedAbsence", "GeometricConformance", "DocumentaryConformance",
            "MaterialTestConformance"]
CHECKABILITY = ["AUTOMATIC", "ASSISTED", "MANUAL"]
TIERS = ["COARSE", "MEDIUM", "FINE", "NON_VISUAL"]
MODALITY = ["Visual", "Geometric", "Documentary", "MaterialTest"]
STATUS = ["VERIFIED", "PROPOSED", "UNMAPPED", "NOT_APPLICABLE"]
CONFIDENCE = ["HIGH", "MEDIUM", "LOW", "TO_VERIFY", ""]
BOOL = ["TRUE", "FALSE"]
PROFILE_STATUS = ["draft", "scaffold", "complete"]
SCOPE = ["supranational", "national", "subnational", "contractual"]

TABLES = {
    # ------------------------------------------------------------------ core
    "core/requirements.csv": dict(
        key="requirement_id",
        doc="What must be true on a construction site, independent of any legal system. "
            "The heart of the catalogue, and the file most contributors will extend.",
        fields=[
            ("requirement_id", True, "str", None),
            ("inspection_item", True, "str", None),
            ("requirement_statement", True, "str", None),
            ("expected_condition", True, "str", None),
            ("applies_to_asset_types", True, "list", ";"),
            ("stage_ref", True, "ref", ("core/work_stages.csv", "stage_id")),
            ("target_type", True, "str", None),
            ("target_ifc_class", False, "str", None),
            ("evidence_pattern", True, "enum", PATTERNS),
            ("required_classes", False, "list", ";"),
            ("prohibited_classes", False, "list", ";"),
            ("evidence_modality", True, "enum", MODALITY),
            ("checkability", True, "enum", CHECKABILITY),
            ("detectability_tier", True, "enum", TIERS),
            ("required_coverage", False, "num", (0.0, 1.0)),
            ("hold_point", True, "enum", BOOL),
            ("notes", False, "str", None),
        ]),
    "core/object_classes.csv": dict(
        key="class_id",
        doc="Everything the detector can be asked to look for, with the five physical "
            "parameters that decide whether it could have been seen.",
        fields=[
            ("class_id", True, "str", None),
            ("detector_label", True, "str", None),
            ("semantic_class", True, "str", None),
            ("char_dim_installed_m", True, "num", (0.0001, 100.0)),
            ("min_px_on_target", True, "int", (1, 512)),
            ("detectability_tier", True, "enum", TIERS[:3]),
            ("occlusion_sensitivity", True, "num", (0.0, 1.0)),
            ("self_occlusion_prior", True, "num", (0.0, 1.0)),
            ("base_recall_ref", True, "num", (0.0, 1.0)),
            ("parameter_source", False, "str", None),
            ("notes", False, "str", None),
        ]),
    "core/work_stages.csv": dict(
        key="stage_id",
        doc="Generic stages of construction. Requirements bind to these; projects map "
            "their own phases onto them.",
        fields=[
            ("stage_id", True, "str", None),
            ("stage_label", True, "str", None),
            ("typical_sequence", True, "int", (1, 99)),
            ("description", True, "str", None),
            ("notes", False, "str", None),
        ]),
    "core/asset_types.csv": dict(
        key="asset_type_id",
        doc="Kinds of works a requirement may be scoped to.",
        fields=[
            ("asset_type_id", True, "str", None),
            ("label", True, "str", None),
            ("description", True, "str", None),
            ("typical_stages", True, "list", ";"),
        ]),
    "core/jurisdictions.csv": dict(
        key="jurisdiction_id",
        doc="The legal systems for which a profile exists or is planned.",
        fields=[
            ("jurisdiction_id", True, "str", None),
            ("label", True, "str", None),
            ("iso_code", True, "str", None),
            ("scope", True, "enum", SCOPE),
            ("authority", True, "str", None),
            ("language", True, "str", None),
            ("profile_dir", True, "str", None),
            ("status", True, "enum", PROFILE_STATUS),
            ("notes", False, "str", None),
        ]),
    "core/evidence_patterns.csv": dict(
        key="pattern_id",
        doc="The seven ways a requirement can be settled, and what silence means under each.",
        fields=[
            ("pattern_id", True, "enum", PATTERNS),
            ("label", True, "str", None),
            ("requirement_assertion", True, "str", None),
            ("non_detection_meaning", True, "str", None),
            ("settleable_by_imagery", True, "enum", ["yes", "no"]),
        ]),
    "core/checkability_levels.csv": dict(
        key="level_id",
        doc="How much of a requirement the machine may settle alone.",
        fields=[("level_id", True, "enum", CHECKABILITY), ("label", True, "str", None),
                ("description", True, "str", None)]),
    "core/detectability_tiers.csv": dict(
        key="tier_id",
        doc="Shorthand for the pixel demand an object class implies.",
        fields=[("tier_id", True, "enum", TIERS), ("label", True, "str", None),
                ("description", True, "str", None)]),
    "core/decision_thresholds.csv": dict(
        key="parameter_id",
        doc="Every constant the reasoner is tuned with, in one file rather than in code.",
        fields=[
            ("parameter_id", True, "str", None),
            ("value", True, "num", (-100.0, 100.0)),
            ("symbol", False, "str", None),
            ("applies_to", True, "enum",
             ["sufficiency", "decision", "model", "detectability"]),
            ("description", True, "str", None),
        ]),
    # ------------------------------------------------------------------ profile
    "profile/regulations.csv": dict(
        key="regulation_id",
        doc="The instruments a profile draws on. One row per law, decree or standard.",
        fields=[
            ("regulation_id", True, "str", None),
            ("short_name", True, "str", None),
            ("full_title", True, "str", None),
            ("jurisdiction", True, "ref", ("core/jurisdictions.csv", "jurisdiction_id")),
            ("instrument_type", True, "str", None),
            ("domain", True, "str", None),
            ("in_force_from", False, "str", None),
            ("source_url", False, "url", None),
            ("notes", False, "str", None),
        ]),
    "profile/clause_bindings.csv": dict(
        key=None,
        doc="The claim that this jurisdiction grounds this requirement in this clause. "
            "The file that makes CIEO portable.",
        fields=[
            ("requirement_id", True, "ref", ("core/requirements.csv", "requirement_id")),
            ("regulation_id", False, "str", None),
            ("clause_reference", False, "str", None),
            ("binding_status", True, "enum", STATUS),
            ("confidence", False, "enum", CONFIDENCE),
            ("source_url", False, "url", None),
            ("note", False, "str", None),
        ]),
    # ------------------------------------------------------------------ project
    "project/phases.csv": dict(
        key="phase_id",
        doc="This project's actual programme, each phase declaring which generic stages "
            "it realises.",
        fields=[
            ("phase_id", True, "str", None),
            ("phase_label", True, "str", None),
            ("sequence", True, "int", (1, 999)),
            ("maps_to_stages", True, "list", ";"),
            ("description", True, "str", None),
            ("precedes", False, "list", ";"),
            ("active_targets", True, "list", ";"),
        ]),
}
