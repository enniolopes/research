"""Release-package admission checks. Never submits or uploads a paper."""
from __future__ import annotations

import review
from contracts import ContractError, digest
from resources import fingerprint, frozen_bytes, resolve, safe_path, verify
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from supervision_state import Store


def evaluate(store: Store, record: dict) -> list[tuple[str, str]]:
    root = store.root
    outcomes = []
    covered_criteria = set()
    reviewed_documents = set()
    reviewed_claims = {}
    for rid in record["review_refs"]:
        candidate = store.records.get(rid)
        if not candidate or candidate["schema_version"] != "review@1":
            outcomes.append(("NOT_VERIFIED", f"release review missing: {rid}"))
            continue
        state, checks = store.state(rid)
        outcomes.extend(checks)
        if candidate["verdict"] != "PASS":
            outcomes.append(("FAIL" if candidate["verdict"] == "FAIL" else "NOT_VERIFIED", "release review is not PASS"))
        if state != "CURRENT":
            outcomes.append(("STALE" if state == "STALE" else "NOT_VERIFIED", f"release review {rid} is {state}"))
        for item in candidate["coverage"]["documents"]:
            reviewed_documents.add(digest(resolve(item, candidate, store.records)))
        for claim in candidate["claims"]:
            if claim["result"] == "adequate":
                reviewed_claims[claim["id"]] = (claim, candidate)
                covered_criteria.update(claim["criteria"])
    inventory = record["claim_inventory"]
    ids = [x["id"] for x in inventory]
    if len(set(ids)) != len(ids) or set(ids) != set(reviewed_claims):
        outcomes.append(("FAIL", "release inventory differs from reviewed material claims"))
    decisions = {}
    for rid in record["decision_refs"]:
        d = store.records.get(rid)
        if not d or d["schema_version"] != "decision@1":
            outcomes.append(("NOT_VERIFIED", f"release decision missing: {rid}"))
            continue
        state, checks = store.state(rid)
        outcomes.extend(checks)
        if state != "CURRENT" or d["disposition"] not in ("adopt", "retain", "narrow"):
            outcomes.append(("STALE" if state == "STALE" else "NOT_VERIFIED", f"release decision {rid} is not a current adoption"))
        decisions[d["target"]["id"]] = d
    for item in inventory:
        r = reviewed_claims.get(item["id"])
        d = decisions.get(item["id"])
        target = resolve(item["resource_ref"], record, store.records)
        if not r or not d or r[0]["text"] != item["text"] or d["target"]["text"] != item["text"]:
            outcomes.append(("FAIL", f"{item['id']}: release text lacks matching review and adoption"))
        elif resolve(r[0]["resource_ref"], r[1], store.records) != target or resolve(d["target"]["resource_ref"], d, store.records) != target:
            outcomes.append(("FAIL", f"{item['id']}: release/review/decision resource versions differ"))
    for rid, value in record["resources"].items():
        outcomes.append(verify(root, value))
        if value["kind"] == "restricted_external":
            outcomes.append(("NOT_VERIFIED", "restricted resource is not a byte-verified release package member"))
            continue
        if value["path"].startswith(".research/releases/"):
            outcomes.append(("FAIL", "release package cannot contain its own manifest as a fingerprinted member"))
        try:
            snapshot = frozen_bytes(root, record["snapshot_commit"], value["path"])
            current = safe_path(root, value["path"]).read_bytes()
            if fingerprint(snapshot) != value["sha256"] or fingerprint(current) != value["sha256"]:
                outcomes.append(("STALE", f"release bytes changed: {value['path']}"))
        except (ContractError, OSError) as exc:
            outcomes.append(("NOT_VERIFIED", str(exc)))
        if value["kind"] in ("manuscript", "render", "figure") and digest(value) not in reviewed_documents:
            outcomes.append(("NOT_VERIFIED", f"final product not inspected by review: {value['path']}"))
    if not any(v["kind"] in ("manuscript", "render") for v in record["resources"].values()):
        outcomes.append(("NOT_VERIFIED", "release has no manuscript/render"))
    outcomes.extend(store.references(record["target"]["reference_set"], "RELEASE", covered_criteria, current=True))
    for obligation in record["obligations"]:
        if obligation["materiality"] == "required" and obligation["status"] != "PASS":
            # V1 intentionally does not infer competence to waive requirements.
            outcomes.append((obligation["status"], f"undischarged release obligation: {obligation['id']}"))
    for rid in record["authority_refs"]:
        event = store.records.get(rid)
        if not event or rid not in store.committed or event.get("type") != "AUTHORITY_ATTESTED" or event["observation"] != "human_attested":
            outcomes.append(("NOT_VERIFIED", f"release authority unavailable: {rid}"))
    return outcomes


def inspect(root, rid: str) -> dict:
    from supervision_state import Store

    store = Store(root)
    record = store.records.get(rid)
    if not record or record["schema_version"] != "release@1":
        raise ContractError("release manifest not found")
    state, checks = store.state(rid)
    checks = [*store.issues, *checks]
    if state != "CURRENT":
        checks.append(("NOT_VERIFIED", f"release {rid} is {state}; current consolidation required"))
    return {"id": rid, "state": state, "checks": [{"status": s, "detail": d} for s, d in checks],
            "package": [v.get("path", v.get("source_uri")) for v in record["resources"].values()],
            "effect": "checked", "publishes_externally": False}
