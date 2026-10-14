"""Strict, stdlib-only contracts for scientific decision supervision.

SCHEMAS is also exported as JSON Schema for tooling; it is the runtime source
of truth. Only the deliberately small subset implemented by check() is used.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from uuid import UUID

CORE_VERSION = "supervisor@1"
ACTIONS = ["FIT_CONFIRMATORY", "ADMIT_RESULT", "CHANGE_COMMITMENT", "ADOPT_CLAIM", "REVISE_DECISION", "RELEASE"]
CORE_RULES = {
    "CORE-PROSPECTIVE": "Scientific freezes precede result exposure.",
    "CORE-PROVENANCE": "Identified results bind to validated runs and bytes.",
    "CORE-EXPOSURE": "Discovery data are not independent confirmation.",
    "CORE-PRIMARY": "Only the frozen primary test decides H.",
    "CORE-REVIEW": "Material claims require applicable separate review.",
    "CORE-IDENTITY": "Versions and append-only history remain distinguishable.",
    "CORE-RELEASE": "Review covers the actual release package.",
}


class ContractError(ValueError):
    pass


def canonical(value: object) -> bytes:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ContractError(str(exc)) from exc


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def pairs(items):
    out = {}
    for key, value in items:
        if key in out:
            raise ContractError(f"duplicate JSON key: {key}")
        out[key] = value
    return out


def loads(raw: str) -> object:
    def invalid(value):
        raise ContractError(f"non-finite JSON number: {value}")
    try:
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)
    except (ValueError, TypeError) as exc:
        raise ContractError(str(exc)) from exc


def load(path: Path) -> dict:
    value = loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ContractError(f"{path}: expected JSON object")
    return value


def string(pattern=None, enum=None, fmt=None):
    result = {"type": "string", "minLength": 1}
    if pattern:
        result["pattern"] = pattern
    if enum:
        result["enum"] = enum
    if fmt:
        result["format"] = fmt
    return result


def array(item, minimum=0):
    return {"type": "array", "items": item, "minItems": minimum}


def obj(required, optional=None):
    properties = dict(required)
    properties.update(optional or {})
    properties["extensions"] = {"type": "object"}
    return {"type": "object", "properties": properties, "required": list(required), "additionalProperties": False}


S = string()
SHA = string(r"^[0-9a-f]{64}$")
COMMIT = string(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
TIME = string(fmt="date-time")
UUID_S = string(fmt="uuid")
NULL_ID = {"oneOf": [S, {"type": "null"}]}
REF = {"oneOf": [S, obj({"record_id": S, "resource_id": S})]}
BINDING = obj({"resource_ref": REF, "binding": string(enum=["pinned", "follow_current", "external_refresh"])}, {
    "current_path": S, "current_record": S, "refresh_rule": S, "refresh_at": TIME,
})
LOCAL_RESOURCE = obj({"kind": S, "logical_id": S, "path": S, "revision": COMMIT, "sha256": SHA}, {
    "locator": S, "origin_refs": array(S), "source_uri": S, "retrieved_at": TIME, "limitations": array(S),
})
RESTRICTED_RESOURCE = obj({"kind": string(enum=["restricted_external"]), "logical_id": S, "source_uri": S,
                           "version_label": S, "availability": string(enum=["restricted"]), "access_attestation_ref": S})
RESOURCE = {"oneOf": [LOCAL_RESOURCE, RESTRICTED_RESOURCE]}
RESOURCES = {"type": "object", "propertyNames": string(r"^RES-[A-Za-z0-9_-]+$"), "additionalProperties": RESOURCE}
AUTHORITY = obj({"kind": string(enum=["human", "host", "external"]), "identity": S}, {"attestation_ref": S})
CRITERION = obj({"id": S, "class": string(enum=["integrity", "scientific", "editorial", "exemplars", "style"]),
                "text": S, "applies_to": array(string(enum=ACTIONS), 1),
                "materiality": string(enum=["required", "advisory"]),
                "verification": string(enum=["mechanical", "bounded_assessment", "independent_review", "human"]),
                "source": obj({"kind": S, "ref": S})}, {"refresh_at": TIME})
TARGET = obj({"kind": S, "id": S, "text": S, "resource_ref": REF, "binding": string(enum=["pinned", "follow_current", "external_refresh"])},
             {"current_path": S, "current_record": S, "refresh_rule": S, "refresh_at": TIME, "decides": string(r"^H[0-9]+$")})
ROUTE = obj({"id": S, "all_of": array(BINDING, 1)})
STAMP = {"core_version": string(enum=[CORE_VERSION]), "rules_sha256": SHA}
CLAIM = obj({"id": string(r"^C[0-9]+$"), "text": S, "resource_ref": REF,
             "criteria": array(S, 1), "evidence": array(REF, 1),
             "routes": array(S), "result": string(enum=["adequate", "inadequate", "insufficient"]), "limits": array(S)})
FINDING = obj({"id": string(r"^F[0-9]+$"), "materiality": string(enum=["material", "nonmaterial"]), "target": S,
               "reason": S, "action": S, "disposition": string(enum=["open", "resolved", "deferred"])}, {"resolution_ref": S})
CHECK = obj({"id": S, "command": array(S, 1), "status": string(enum=["PASS", "FAIL", "NOT_VERIFIED"]), "evidence_ref": REF})
MEMBER = obj({"id": S, "path": S, "sha256": SHA})
OBLIGATION = obj({"id": S, "target": S, "status": string(enum=["PASS", "FAIL", "NOT_VERIFIED"]),
                  "materiality": string(enum=["required", "advisory"]),
                  "origin": string(enum=["core", "reference"]), "method": S, "basis": array(S)},
                 {"disposition_ref": S, "detail": S})

SCHEMAS = {
    "project@1": obj({"schema_version": string(enum=["project@1"]), "project_id": UUID_S, "created_at": TIME}),
    "references@1": obj({"schema_version": string(enum=["references@1"]), "id": string(r"^REF-[1-9][0-9]*$"),
                         "project_id": UUID_S, "supersedes": NULL_ID, "criteria": array(CRITERION, 1), "authority": AUTHORITY}),
    "decision@1": obj({"schema_version": string(enum=["decision@1"]), "id": string(r"^DEC-[1-9][0-9]*$"), "project_id": UUID_S,
                       **STAMP, "action": string(enum=["ADOPT_CLAIM", "REVISE_DECISION", "CHANGE_COMMITMENT"]), "target": TARGET,
                       "references": array(S, 1), "resources": RESOURCES, "basis": obj({"routes": array(ROUTE), "origin_refs": array(S)}),
                       "judgments": array(S), "rationale_ref": REF,
                       "disposition": string(enum=["adopt", "narrow", "retain", "withdraw", "defer", "reopen"]),
                       "limits": array(S), "supersedes": NULL_ID, "revision_conditions": array(S, 1)}),
    "review@1": obj({"schema_version": string(enum=["review@1"]), "id": string(r"^REVIEW-[1-9][0-9]*$"), "project_id": UUID_S,
                     **STAMP, "reviewed_commit": COMMIT, "resources": RESOURCES, "dependencies": array(BINDING, 1),
                     "reference_set": array(S, 1), "report": obj({"path": S, "sha256": SHA}),
                     "coverage": obj({"documents": array(REF, 1), "claim_ids": array(S), "unexamined": array(S),
                                      "limitations": array(S), "material_complete": {"type": "boolean"}}),
                     "claims": array(CLAIM), "findings": array(FINDING), "checks": array(CHECK),
                     "reviewer": obj({"backend": S, "identity": S, "procedure": S,
                                      "separation": string(enum=["host_attested", "external_reviewer_attested", "not_verified"])},
                                     {"attestation_ref": S}),
                     "verdict": string(enum=["PASS", "FAIL", "NOT_VERIFIED"])}),
    "event@1": obj({"schema_version": string(enum=["event@1"]), "id": string(r"^EVT-[0-9a-f-]{36}$"), "project_id": UUID_S,
                    "type": string(enum=["COMMITMENT_RECORDED", "EXECUTION_STARTED", "EXECUTION_COMPLETED", "EXPOSURE_RECORDED",
                                         "RESULT_ADMITTED", "DECISION_RECORDED", "REVIEW_RECORDED", "DEPENDENCY_CHANGED", "REOPEN_RECORDED",
                                         "RELEASE_ADMITTED", "AUTHORITY_ATTESTED", "REVIEW_ATTESTED"]),
                    "subject": S, "operation_id": UUID_S, "observation": string(enum=["instrumented", "human_attested", "agent_reported"]),
                    "origin": S, "observed_at": TIME, "recorded_at": TIME, "sequence": {"type": "integer", "minimum": 0},
                    "members": array(MEMBER)}, {"resources": array(REF), "identity": S, "context_id": S, "author_context_id": S,
                                               "method": S, "disclosure": S}),
    "release@1": obj({"schema_version": string(enum=["release@1"]), "id": string(r"^REL-[1-9][0-9]*$"), "project_id": UUID_S,
                      **STAMP, "snapshot_commit": COMMIT, "target": obj({"kind": S, "destination": S, "reference_set": array(S, 1)}),
                      "resources": RESOURCES, "claim_inventory": array(obj({"id": S, "text": S, "resource_ref": REF, "locator": S})),
                      "decision_refs": array(S), "review_refs": array(S, 1), "obligations": array(OBLIGATION),
                      "authority_refs": array(S), "created_at": TIME}),
    "action@1": obj({"schema_version": string(enum=["action@1"]), "operation_id": UUID_S, "project_id": UUID_S,
                     **STAMP, "action": string(enum=ACTIONS), "target": S, "base_commit": COMMIT,
                     "resources": RESOURCES, "bindings": array(BINDING)},
                    {"record": {"type": "object"}, "record_id": S, "execution_id": string(r"^EXEC-[1-9][0-9]*$"),
                     "hypothesis": string(r"^H[0-9]+$"), "protocol_freeze": COMMIT, "analysis_plan_freeze": COMMIT,
                     "registration": S, "reference_set": array(S), "route": string(enum=["SPECIFICATION", "EXPLORATORY", "DEFERRED", "REOPEN"]),
                     "evidence_refs": array(S)}),
}
RULES_SHA256 = digest({"version": CORE_VERSION, "rules": CORE_RULES, "schemas": SCHEMAS})
DIRECTORIES = {"references@1": "references", "decision@1": "decisions", "review@1": "reviews",
               "event@1": "events", "release@1": "releases"}


def check(value, schema, label="$", errors=None):
    errors = [] if errors is None else errors
    if "oneOf" in schema:
        matches = sum(not check(value, branch) for branch in schema["oneOf"])
        if matches != 1:
            errors.append(f"{label}: must match exactly one permitted shape")
        return errors
    kind = schema.get("type")
    valid = {"object": isinstance(value, dict), "array": isinstance(value, list), "string": isinstance(value, str),
             "integer": isinstance(value, int) and not isinstance(value, bool), "boolean": isinstance(value, bool),
             "null": value is None}.get(kind, True)
    if not valid:
        errors.append(f"{label}: expected {kind}")
        return errors
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{label}: unrecognized value {value!r}")
    if kind == "string":
        if len(value) < schema.get("minLength", 0) or not value.strip():
            errors.append(f"{label}: empty string")
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errors.append(f"{label}: invalid identifier/fingerprint")
        try:
            if schema.get("format") == "uuid":
                if str(UUID(value)) != value:
                    raise ValueError("not canonical UUID")
            if schema.get("format") == "date-time":
                dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
                if dt.utcoffset() is None or dt.utcoffset().total_seconds() != 0:
                    raise ValueError("UTC required")
        except ValueError:
            errors.append(f"{label}: invalid {schema.get('format')}")
    if kind == "integer" and value < schema.get("minimum", value):
        errors.append(f"{label}: below minimum")
    if kind == "array":
        if len(value) < schema.get("minItems", 0):
            errors.append(f"{label}: too few items")
        for index, item in enumerate(value):
            check(item, schema["items"], f"{label}[{index}]", errors)
    if kind == "object":
        props = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{label}.{key}: required")
        for key, item in value.items():
            if "propertyNames" in schema:
                check(key, schema["propertyNames"], label + " key", errors)
            if key in props:
                check(item, props[key], f"{label}.{key}", errors)
            elif schema.get("additionalProperties") is False:
                errors.append(f"{label}.{key}: unknown field")
            elif isinstance(schema.get("additionalProperties"), dict):
                check(item, schema["additionalProperties"], f"{label}.{key}", errors)
    return errors


def validate(data: dict) -> None:
    if not isinstance(data, dict):
        raise ContractError("expected JSON object")
    version = data.get("schema_version")
    if not isinstance(version, str):
        raise ContractError("schema_version must be a string")
    schema = SCHEMAS.get(version)
    if schema is None:
        raise ContractError("unknown schema_version")
    errors = check(data, schema)
    if data.get("core_version") and data.get("rules_sha256") != RULES_SHA256:
        errors.append("rules fingerprint does not match this core; inspect migration")
    if errors:
        raise ContractError("; ".join(errors))
    for value in data.get("resources", {}).values():
        if value.get("kind") == "source" and not (value.get("source_uri") and value.get("retrieved_at")):
            errors.append("source snapshot requires source_uri and retrieved_at")
    for binding in data.get("bindings", []) + data.get("dependencies", []):
        binding_errors(binding, errors)
    target = data.get("target")
    if isinstance(target, dict) and "binding" in target:
        binding_errors(target, errors)
    for route in data.get("basis", {}).get("routes", []):
        for binding in route.get("all_of", []):
            binding_errors(binding, errors)
    if errors:
        raise ContractError("; ".join(errors))


def binding_errors(binding, errors):
    if binding.get("binding") == "follow_current" and not (binding.get("current_path") or binding.get("current_record")):
        errors.append("follow_current requires current_path or current_record")
    if binding.get("binding") == "external_refresh" and not (binding.get("refresh_rule") and binding.get("refresh_at")):
        errors.append("external_refresh requires refresh_rule and refresh_at")


def schema_files() -> dict[str, dict]:
    return {name.replace("@", "-") + ".schema.json": {
        "$schema": "https://json-schema.org/draft/2020-12/schema", "title": name, **schema
    } for name, schema in SCHEMAS.items()}
