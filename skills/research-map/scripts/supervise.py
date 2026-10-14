#!/usr/bin/env python3
"""Cooperative decision supervisor and stdlib CLI; no scientific truth oracle."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

import epistemic
import execute
import policy
import release
import review
from contracts import CORE_RULES, CORE_VERSION, DIRECTORIES, RULES_SHA256, ContractError, canonical, digest, load, loads, schema_files, validate
from events import ProjectLock, RecoveryRequired, anchor, atomic, begin, check_anchor, event, finish, git_dir, journal, now, runtime, unfinished
from resources import ancestor, applicability, fingerprint, frozen_bytes, git, head, safe_path
from supervision_state import Store, check_supervision

CAPABILITIES = {"backend": "cooperative_local_cli", "pre_execution_interception": "cli_only", "blocks_cli_execution": True,
                "observes_external_exposure": False, "native_claude_code": "NOT_VERIFIED", "native_codex": "NOT_VERIFIED",
                "network_isolation": False, "model_isolation": False, "adversarial_filesystem_containment": False}


def response(checks, effect="checked", **extra):
    obligations = []
    for index, item in enumerate(checks):
        status, detail = item
        obligations.append({"id": f"CHECK-{index + 1}", "target": extra.get("target", "project"), "status": status,
                            "materiality": "required", "origin": "core", "method": "mechanical_or_recorded_judgment", "basis": [], "detail": detail})
    if any(s == "FAIL" for s, _ in checks):
        disposition = "BLOCK"
    elif any(s in ("STALE", "NOT_VERIFIED") for s, _ in checks):
        disposition = "REQUIRE_JUDGMENT" if any("review" in d or "adjudicat" in d or "authority" in d for s, d in checks if s != "PASS") else "REQUIRE_EVIDENCE"
    else:
        disposition = "ALLOW"
    return {"disposition": disposition, "effect": effect, "obligations": obligations,
            "verified_basis": [d for s, d in checks if s == "PASS"],
            "allowed_routes": [] if disposition == "ALLOW" else ["RESOLVE_OBLIGATION", "CONTINUE_INDEPENDENT_WORK", "EXPLORE_WITH_DISCLOSURE"],
            "capability_limits": CAPABILITIES, **extra}


def initialize(root: Path) -> dict:
    path = root / ".research/project.json"
    if path.exists():
        value = load(path)
        validate(value)
        return value
    git(root, "rev-parse", "--is-inside-work-tree")
    value = {"schema_version": "project@1", "project_id": str(uuid4()), "created_at": now()}
    atomic(path, value)
    return value


def fit_checks(store: Store, request: dict) -> list[tuple[str, str]]:
    root = store.root
    checks = []
    if not request.get("execution_id"):
        return [("NOT_VERIFIED", "prospective execution_id required for supervised FIT")]
    found = execute.load_spec(root, request["execution_id"])
    if not found:
        return [("NOT_VERIFIED", "execution spec not found")]
    spec_path, spec = found
    spec_result, _ = execute.validate_spec(spec, filename=spec_path.relative_to(root).as_posix())
    checks.append((spec_result.status, "; ".join(spec_result.lines) or "execution spec valid"))
    before = execute.changed_paths(root)
    checks.append(("FAIL" if before else "PASS", "execution worktree must be clean" if before else "execution worktree clean"))
    h = request.get("hypothesis")
    plan_result, plans, frozen = epistemic.check_plan(root)
    checks.append((plan_result.status, "; ".join(plan_result.lines) or plan_result.summary))
    entry = plans.get(h)
    if not entry or entry["mode"] != "confirmatory" or frozen.lower() not in ("frozen", "yes", "true"):
        checks.append(("FAIL", "hypothesis and plan must be confirmatory and frozen"))
    for field, path in (("protocol_freeze", "protocol.md"), ("analysis_plan_freeze", "analysis-plan.md")):
        revision = request.get(field)
        if not revision:
            checks.append(("NOT_VERIFIED", f"{field} missing before exposure"))
            continue
        try:
            if not ancestor(root, revision, request["base_commit"]):
                checks.append(("FAIL", f"{field} does not precede execution freeze"))
            old = frozen_bytes(root, revision, path)
            if old != safe_path(root, path).read_bytes():
                checks.append(("FAIL", f"{path} differs from its scientific freeze"))
            if path == "protocol.md" and h and h not in old.decode(errors="replace"):
                checks.append(("FAIL", "hypothesis not identifiable in frozen protocol"))
        except (OSError, ContractError) as exc:
            checks.append(("NOT_VERIFIED", str(exc)))
    if not request.get("registration"):
        checks.append(("NOT_VERIFIED", "registration/disclosed DRY_RUN state required"))
    map_path = root / "RESEARCH.map"
    if not map_path.exists():
        checks.append(("NOT_VERIFIED", "RESEARCH.map missing"))
    else:
        run_check, runs, _ = epistemic.check_runs(root, map_path)
        if runs or run_check.status == "FAIL":
            checks.append((run_check.status, "; ".join(run_check.lines) or run_check.summary))
        exposure = epistemic.check_exposure(plans, runs)
        if runs or exposure.status == "FAIL":
            checks.append((exposure.status, "; ".join(exposure.lines) or exposure.summary))
    if entry:
        # Conservative prospective guard: data selected adaptively cannot be
        # reused by merely changing IDs or having no historical run yet.
        for data_id in entry["generated_from"]:
            checks.append(("NOT_VERIFIED", f"adaptive exposure {data_id}: independent input evidence required before FIT"))
        for e in store.records.values():
            if e.get("type") == "EXPOSURE_RECORDED" and e["subject"] == h:
                checks.append(("NOT_VERIFIED", "recorded exposure requires design review before confirmatory FIT"))
    for resource_path in spec.get("inputs", []) + spec.get("environment", []):
        try:
            frozen_bytes(root, request["base_commit"], resource_path)
        except ContractError as exc:
            checks.append(("FAIL", str(exc)))
    authorization, why = execute.policy_preflight(root, spec)
    checks.append(("PASS" if authorization == "ALLOW" else "FAIL", why))
    return checks


def propose(root: Path, request: dict) -> dict:
    validate(request)
    if request["schema_version"] != "action@1":
        raise ContractError("expected action@1")
    store = Store(root)
    if not store.project or store.project["project_id"] != request["project_id"]:
        raise ContractError("project identity unavailable/mismatch")
    if request["base_commit"] != head(root):
        raise RecoveryRequired("request snapshot is obsolete")
    checks = list(store.issues)
    for binding in request["bindings"]:
        checks.append(applicability(root, binding, request, store.records))
    action = request["action"]
    if action == "FIT_CONFIRMATORY":
        checks.extend(fit_checks(store, request))
    elif action == "ADMIT_RESULT":
        checked, runs, index = epistemic.check_runs(root, root / "RESEARCH.map")
        checks.append((checked.status, "; ".join(checked.lines) or checked.summary))
        plan, _, _ = epistemic.parse_plan(root)
        exposed = epistemic.check_exposure(plan, runs)
        checks.append((exposed.status, "; ".join(exposed.lines) or exposed.summary))
        if request["target"] not in index:
            checks.append(("NOT_VERIFIED", "target result has no valid run lineage"))
    else:
        record = request.get("record")
        if not record:
            checks.append(("NOT_VERIFIED", "material decision/release record required"))
        else:
            validate(record)
            if record["project_id"] != request["project_id"]:
                raise ContractError("record/project mismatch")
            expected = "release@1" if action == "RELEASE" else "decision@1"
            if record["schema_version"] != expected:
                raise ContractError("record schema does not match action")
            if record["id"] in store.records:
                raise ContractError("new admission requires an unused record ID")
            if action != "RELEASE" and record["action"] != action:
                raise ContractError("record action does not match proposal")
            if action == "CHANGE_COMMITMENT":
                if not request.get("route"):
                    checks.append(("NOT_VERIFIED", "durable post-freeze route required"))
                if request.get("route") in ("SPECIFICATION", "EXPLORATORY", "DEFERRED"):
                    checks.append(("NOT_VERIFIED", "use existing prospective routing contract; new confirmatory authority not granted"))
                if request.get("route") == "REOPEN" and record["disposition"] != "reopen":
                    checks.append(("FAIL", "REOPEN requires a reopen decision"))
            checks.extend(release.evaluate(store, record) if action == "RELEASE" else store.decision_checks(record, enforce_current_refs=True))
    return response(checks, target=request["target"])


def run(root: Path, request: dict) -> dict:
    validate(request)
    if request["action"] != "FIT_CONFIRMATORY":
        raise ContractError("run only supports FIT_CONFIRMATORY; other code remains exploratory")
    with ProjectLock(root, request["project_id"], request["operation_id"]):
        path, cached = journal(root, request)
        if cached:
            return {**cached["result"], "cached": True}
        result = propose(root, request)
        if result["disposition"] != "ALLOW":
            return result
        anchor(root)
        entry = begin(path, request, "EXECUTION_STARTED")
        found = execute.load_spec(root, request["execution_id"])
        _, spec = found
        # Execute directly after all preflights. Preserve the existing local
        # integrity and policy contracts, but keep logs out of JSON stdout.
        try:
            with (path.parent / "stdout.bin").open("wb") as stdout, (path.parent / "stderr.bin").open("wb") as stderr:
                outcome = subprocess.run(spec["command"], cwd=root, stdout=stdout, stderr=stderr)
        except OSError as exc:
            failed = response([("FAIL", f"execution failed: {exc}")], effect="executed")
            finish(path, entry, failed, exposure="possible")
            return failed
        changed = execute.changed_paths(root)
        declared = set(spec["outputs"])
        checks = []
        if outcome.returncode:
            checks.append(("FAIL", f"command exited {outcome.returncode}"))
        if changed is None or changed != declared:
            checks.append(("FAIL", "execution changed paths outside the exact declared output boundary"))
        outputs = {}
        for p in declared:
            try:
                outputs[p] = fingerprint(safe_path(root, p).read_bytes())
            except (OSError, ContractError) as exc:
                checks.append(("FAIL", str(exc)))
        if head(root) != request["base_commit"]:
            checks.append(("FAIL", "HEAD changed during execution"))
        result = response(checks, effect="executed", target=request["target"],
                          execution_freeze=request["base_commit"], outputs=outputs,
                          next="Commit only declared outputs, then write/commit RUN; admit result separately.",
                          exposure="result may have been observed; failure does not erase exposure")
        finish(path, entry, result, outputs=outputs, execution_freeze=request["base_commit"], returncode=outcome.returncode)
        return result


def admit(root: Path, request: dict) -> dict:
    validate(request)
    with ProjectLock(root, request["project_id"], request["operation_id"]):
        path, cached = journal(root, request)
        if cached:
            return {**cached["result"], "cached": True}
        result = propose(root, request)
        if result["disposition"] != "ALLOW":
            return result
        if request["action"] == "FIT_CONFIRMATORY":
            raise ContractError("FIT must use run, not admit")
        entry = begin(path, request, "ADMISSION_STARTED")
        store = Store(root)
        members = []
        if request["action"] != "ADMIT_RESULT":
            record = request["record"]
            directory = DIRECTORIES[record["schema_version"]]
            rel = f".research/{directory}/{record['id']}.json"
            member = {"id": record["id"], "path": rel, "sha256": fingerprint(canonical(record) + b"\n")}
            members.append(member)
            final_type = "RELEASE_ADMITTED" if request["action"] == "RELEASE" else "DECISION_RECORDED"
        else:
            final_type = "RESULT_ADMITTED"
            record = None
        marker = event(request["project_id"], request["operation_id"], final_type,
                       record["id"] if record else request["target"], members,
                       sequence=max((e.get("sequence", -1) for e in store.records.values()), default=-1) + 1)
        validate(marker)
        if head(root) != request["base_commit"]:
            raise RecoveryRequired("snapshot changed before admission write")
        for b in request["bindings"]:
            if applicability(root, b, request, store.records)[0] != "PASS":
                raise RecoveryRequired("binding changed before admission write")
        if record:
            # Recheck full current dependency closure, not just the request's
            # optional transport bindings, immediately before publication.
            current = propose(root, request)
            if current["disposition"] != "ALLOW":
                raise RecoveryRequired("decision dependencies changed before admission write")
            atomic(root / members[0]["path"], record)
        atomic(root / ".research/events" / (marker["id"] + ".json"), marker)
        result = {**result, "effect": "admitted", "consolidated": False, "event_id": marker["id"],
                  "next": "Commit the admitted record and event together; until then the record is CANDIDATE."}
        finish(path, entry, result, members=members, event_id=marker["id"])
        anchor(root)
        return result


def import_execution(root: Path, operation_id: str) -> dict:
    project = load(root / ".research/project.json")
    with ProjectLock(root, project["project_id"], operation_id):
        path = runtime(root) / operation_id / "operation.json"
        entry = load(path)
        if entry.get("request", {}).get("action") != "FIT_CONFIRMATORY" or not entry.get("result") or entry["result"]["disposition"] != "ALLOW":
            raise RecoveryRequired("only completed successful execution can be imported; failures require inspection")
        if entry.get("imported_events"):
            return {"effect": "checked", "event_ids": entry["imported_events"], "cached": True}
        changed = git(root, "diff", "--name-only", entry["execution_freeze"], head(root)).decode().splitlines()
        if set(changed) != set(entry["outputs"]):
            raise ContractError("import requires an output-only run commit before receipts/metadata")
        for p, sha in entry["outputs"].items():
            if fingerprint(frozen_bytes(root, head(root), p)) != sha:
                raise ContractError("run commit differs from observed outputs")
        ids = []
        for kind, observed in (("EXECUTION_STARTED", entry["observed_at"]), ("EXECUTION_COMPLETED", entry["completed_at"])):
            e = event(project["project_id"], operation_id, kind, entry["request"]["target"], observed_at=observed,
                      sequence=len(ids))
            atomic(root / ".research/events" / (e["id"] + ".json"), e)
            ids.append(e["id"])
        atomic(path, {**entry, "imported_events": ids, "run_commit": head(root)})
        return {"effect": "admitted", "event_ids": ids, "consolidated": False}


def attest(root: Path, subject: str, identity: str, kind: str, disclosure: str) -> dict:
    """Explicit CLI attestation, not an automatic claim of host isolation.

    Caller owns the assertion; this cooperative record never proves human
    identity. The skill requires this to be supplied by the user/reviewer.
    """
    project = load(root / ".research/project.json")
    operation_id = str(uuid4())
    with ProjectLock(root, project["project_id"], operation_id):
        e = event(project["project_id"], operation_id, kind, subject,
                  observation="human_attested", origin="explicit-cli-attestation", identity=identity,
                  method="declared_by_operator", disclosure=disclosure)
        validate(e)
        atomic(root / ".research/events" / (e["id"] + ".json"), e)
        return {"effect": "admitted", "attestation_ref": e["id"], "consolidated": False,
                "limit": "Explicit declaration under cooperative trust; identity/expertise not authenticated."}


def exit_code(result):
    if result.get("disposition") == "RECOVER":
        return 3
    return 1 if result.get("disposition") in ("BLOCK", "REQUIRE_EVIDENCE", "REQUIRE_JUDGMENT") else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["init", "propose", "run", "admit", "resume", "validate", "import-execution", "attest", "release-inspect", "graph", "schemas", "capabilities"])
    parser.add_argument("--root", default=".")
    parser.add_argument("--request", help="JSON path or - for stdin; keep transport outside the execution worktree")
    parser.add_argument("--id")
    parser.add_argument("--identity")
    parser.add_argument("--kind", choices=["AUTHORITY_ATTESTED", "REVIEW_ATTESTED"])
    parser.add_argument("--disclosure")
    parser.add_argument("--output")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    try:
        if args.command == "init":
            result = {"effect": "admitted", "project": initialize(root), "next": "Commit project identity before execution."}
        elif args.command in ("propose", "run", "admit"):
            if not args.request:
                raise ContractError("--request is required")
            request = loads(sys.stdin.read()) if args.request == "-" else load(Path(args.request))
            result = {"propose": propose, "run": run, "admit": admit}[args.command](root, request)
        elif args.command == "resume":
            store = Store(root)
            result = {"effect": "checked", "states": {rid: store.state(rid)[0] for rid in store.records},
                      "issues": store.issues, "unfinished": unfinished(root), "capabilities": CAPABILITIES}
            if result["unfinished"]:
                result["disposition"] = "RECOVER"
        elif args.command == "validate":
            check = check_supervision(root)
            result = {"effect": "checked", "status": check.status, "summary": check.summary, "issues": check.lines}
            result["disposition"] = "BLOCK" if check.status == "FAIL" else "REQUIRE_EVIDENCE" if args.strict and check.status == "NOT_VERIFIED" else "ALLOW"
        elif args.command == "import-execution":
            if not args.id:
                raise ContractError("--id operation UUID required")
            from uuid import UUID
            if str(UUID(args.id)) != args.id:
                raise ContractError("invalid operation UUID")
            result = import_execution(root, args.id)
        elif args.command == "attest":
            if not all((args.id, args.identity, args.kind, args.disclosure)):
                raise ContractError("attest requires --id, --identity, --kind and --disclosure")
            result = attest(root, args.id, args.identity, args.kind, args.disclosure)
        elif args.command == "release-inspect":
            result = release.inspect(root, args.id)
            result["disposition"] = response([(x["status"], x["detail"]) for x in result["checks"]])["disposition"]
        elif args.command == "graph":
            from decision_graph import build, affected
            graph = build(Store(root))
            result = affected(graph, args.id) if args.id else graph
        elif args.command == "schemas":
            if not args.output:
                raise ContractError("--output directory required")
            for name, schema in schema_files().items():
                atomic(Path(args.output) / name, schema)
            result = {"effect": "admitted", "schemas": list(schema_files())}
        else:
            result = {"effect": "checked", **CAPABILITIES}
        print(canonical(result).decode())
        return exit_code(result)
    except RecoveryRequired as exc:
        print(canonical({"disposition": "RECOVER", "effect": "checked", "error": str(exc)}).decode())
        return 3
    except (ContractError, OSError, KeyError, ValueError) as exc:
        print(canonical({"disposition": "BLOCK", "effect": "checked", "error": str(exc), "contract_invalid": True}).decode())
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
