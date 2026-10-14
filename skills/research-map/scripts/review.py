"""Bounded review consistency, applicability and explicit separation witnesses."""
from __future__ import annotations

from contracts import ContractError
from resources import ancestor, applicability, fingerprint, first_commit, frozen_bytes, resolve, safe_path, verify


def ref_parts(raw: str) -> tuple[str, str]:
    parts = raw.split("#", 1)
    return parts[0], parts[1] if len(parts) > 1 else ""


def separation(record: dict, records: dict, committed: set[str]) -> tuple[str, str]:
    reviewer = record["reviewer"]
    if reviewer["separation"] == "not_verified":
        return "NOT_VERIFIED", "separate review context not attested"
    witness = records.get(reviewer.get("attestation_ref", ""))
    if not witness or witness["id"] not in committed or witness.get("type") != "REVIEW_ATTESTED":
        return "NOT_VERIFIED", "committed REVIEW_ATTESTED witness missing"
    if witness["subject"] != record["id"] or witness.get("identity") != reviewer["identity"]:
        return "FAIL", "review witness names a different review/reviewer"
    if reviewer["separation"] == "host_attested":
        if witness["observation"] != "instrumented" or not witness.get("context_id") or not witness.get("author_context_id"):
            return "NOT_VERIFIED", "host context witness incomplete"
        if witness["context_id"] == witness["author_context_id"]:
            return "FAIL", "author and reviewer contexts are identical"
    elif witness["observation"] != "human_attested":
        return "NOT_VERIFIED", "external reviewer requires an explicit human attestation"
    return "PASS", "separation attested under cooperative provenance; not independent expertise"


def consistency(record: dict) -> list[str]:
    issues = []
    claims = record["claims"]
    ids = [x["id"] for x in claims]
    if len(set(ids)) != len(ids) or set(ids) != set(record["coverage"]["claim_ids"]):
        issues.append("coverage and claim IDs do not match uniquely")
    material = [x for x in record["findings"] if x["materiality"] == "material"]
    if any(x["disposition"] == "resolved" and not x.get("resolution_ref") for x in material):
        issues.append("resolved material finding has no independent resolution reference")
    if record["verdict"] == "PASS":
        if any(x["result"] != "adequate" for x in claims):
            issues.append("PASS contradicts inadequate/insufficient claim")
        if not record["coverage"]["material_complete"] or record["coverage"]["unexamined"]:
            issues.append("PASS contradicts incomplete coverage")
        if any(x["disposition"] != "resolved" for x in material):
            issues.append("PASS hides unresolved material finding")
        if any(x["status"] != "PASS" for x in record["checks"]):
            issues.append("PASS hides unresolved review check")
    return issues


def evaluate(root, record: dict, records: dict, committed: set[str], path=None, require_adequacy=True, stack=()) -> list[tuple[str, str]]:
    if record["id"] in stack:
        return [("FAIL", "review resolution dependency cycle")]
    stack = (*stack, record["id"])
    results = [("FAIL", issue) for issue in consistency(record)]
    results.append(separation(record, records, committed))
    for value in record["resources"].values():
        if value.get("revision") and not ancestor(root, value["revision"], record["reviewed_commit"]):
            results.append(("FAIL", "review resource is newer than reviewed snapshot"))
    for binding in record["dependencies"]:
        results.append(applicability(root, binding, record, records))
    for item in record["coverage"]["documents"]:
        results.append(verify(root, resolve(item, record, records)))
    for claim in record["claims"]:
        target = resolve(claim["resource_ref"], record, records)
        status, why = verify(root, target)
        results.append((status, why))
        if status == "PASS":
            body = frozen_bytes(root, target["revision"], target["path"]).decode("utf-8", errors="replace")
            if claim["text"] not in body:
                results.append(("FAIL", f"{claim['id']}: exact claim text not in examined resource"))
        for evidence in claim["evidence"]:
            results.append(verify(root, resolve(evidence, record, records)))
        if require_adequacy and claim["result"] != "adequate":
            results.append(("FAIL" if claim["result"] == "inadequate" else "NOT_VERIFIED", f"{claim['id']}: {claim['result']}"))
    if path:
        initial = first_commit(root, path)
        if initial:
            try:
                report = frozen_bytes(root, initial, record["report"]["path"])
                if fingerprint(report) != record["report"]["sha256"]:
                    results.append(("FAIL", "review report fingerprint mismatch"))
                if safe_path(root, record["report"]["path"]).read_bytes() != report:
                    results.append(("STALE", "review report changed"))
            except (OSError, ContractError) as exc:
                results.append(("NOT_VERIFIED", str(exc)))
        else:
            try:
                if fingerprint(safe_path(root, record["report"]["path"]).read_bytes()) != record["report"]["sha256"]:
                    results.append(("FAIL", "pending report fingerprint mismatch"))
            except (OSError, ContractError) as exc:
                results.append(("NOT_VERIFIED", str(exc)))
    for finding in record["findings"]:
        if finding["materiality"] == "material" and finding["disposition"] == "resolved":
            rid, fid = ref_parts(finding["resolution_ref"])
            resolved = records.get(rid)
            if not resolved or rid not in committed or resolved.get("schema_version") != "review@1" or rid == record["id"]:
                results.append(("NOT_VERIFIED", "resolution requires a different committed review"))
            else:
                results.extend(evaluate(root, resolved, records, committed,
                                        path=f".research/reviews/{rid}.json", stack=stack))
                if resolved["verdict"] != "PASS" or not any(x["id"] == fid and x["result"] == "adequate" for x in resolved["claims"]):
                    results.append(("NOT_VERIFIED", "resolution not covered by adequate reviewed finding/claim"))
    if require_adequacy and record["verdict"] != "PASS":
        results.append((record["verdict"], "review verdict is not PASS"))
    return results
