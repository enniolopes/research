"""Authoritative record loading, append-only checks and disposable state projection."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import epistemic
import review
from contracts import ContractError, DIRECTORIES, load, validate
from events import RecoveryRequired, check_anchor
from resources import applicability, ancestor, committed_unchanged, fingerprint, first_commit, frozen_bytes, git, resolve, verify


@dataclass
class Result:
    name: str = "supervision"
    status: str = "PASS"
    summary: str = ""
    lines: list[str] = field(default_factory=list)

    def add(self, status, detail):
        if status == "FAIL":
            self.status = "FAIL"
        elif status in ("NOT_VERIFIED", "STALE") and self.status != "FAIL":
            self.status = "NOT_VERIFIED"
        if status != "PASS":
            self.lines.append(detail)


class Store:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.records: dict[str, dict] = {}
        self.paths: dict[str, str] = {}
        self.committed: set[str] = set()
        self.issues: list[tuple[str, str]] = []
        self.project = None
        project_path = root / ".research/project.json"
        if project_path.exists():
            self.project = load(project_path)
            validate(self.project)
            status, why = committed_unchanged(root, ".research/project.json")
            if status != "PASS":
                self.issues.append((status, why))
        for schema, directory in DIRECTORIES.items():
            for path in sorted((root / ".research" / directory).glob("*.json")):
                relative = path.relative_to(root).as_posix()
                try:
                    data = load(path)
                    validate(data)
                    if data["schema_version"] != schema or path.stem != data["id"]:
                        raise ContractError(f"{relative}: filename/schema/ID mismatch")
                    if not self.project or data["project_id"] != self.project["project_id"]:
                        raise ContractError(f"{relative}: project identity mismatch")
                    if data["id"] in self.records:
                        raise ContractError("duplicate record ID")
                    self.records[data["id"]] = data
                    self.paths[data["id"]] = relative
                    status, why = committed_unchanged(root, relative)
                    if status == "PASS":
                        self.committed.add(data["id"])
                    else:
                        self.issues.append((status, why))
                except (OSError, ContractError) as exc:
                    self.issues.append(("FAIL", str(exc)))
        self._history()
        self._relationships()
        self._cache: dict[str, tuple[str, list[tuple[str, str]]]] = {}

    def _history(self):
        try:
            check_anchor(self.root)
            directories = [f".research/{x}/" for x in DIRECTORIES.values()]
            added = git(self.root, "log", "--format=", "--name-only", "--diff-filter=A", "HEAD", "--", *directories).decode().splitlines()
            for path in sorted(set(x for x in added if x.endswith(".json"))):
                if not (self.root / path).is_file():
                    self.issues.append(("FAIL", f"committed record deleted/renamed: {path}"))
        except RecoveryRequired:
            raise
        except ContractError as exc:
            self.issues.append(("NOT_VERIFIED", str(exc)))

    def _relationships(self):
        for rid, record in self.records.items():
            other = record.get("supersedes")
            if other:
                if other not in self.records or self.records[other]["schema_version"] != record["schema_version"]:
                    self.issues.append(("FAIL", f"{rid}: missing/incompatible supersession target"))
                seen = {rid}
                while other in self.records:
                    if other in seen:
                        self.issues.append(("FAIL", f"{rid}: supersession cycle"))
                        break
                    seen.add(other)
                    other = self.records[other].get("supersedes")
            if record["schema_version"] == "references@1":
                ids = [c["id"] for c in record["criteria"]]
                if len(ids) != len(set(ids)) or any(x.startswith("CORE-") for x in ids):
                    self.issues.append(("FAIL", f"{rid}: duplicate/reserved criterion ID"))
            if record["schema_version"] == "review@1":
                self.issues.extend(("FAIL", f"{rid}: {x}") for x in review.consistency(record))
            for res in record.get("resources", {}).values():
                if res.get("path") == self.paths[rid]:
                    self.issues.append(("FAIL", f"{rid}: self-dependent resource"))
                if rid in self.committed and res.get("revision"):
                    try:
                        if not ancestor(self.root, res["revision"], first_commit(self.root, self.paths[rid])):
                            self.issues.append(("FAIL", f"{rid}: evidence does not precede its record"))
                    except ContractError as exc:
                        self.issues.append(("FAIL", str(exc)))

    def consolidated(self, rid: str) -> bool:
        if rid not in self.committed:
            return False
        path = self.paths[rid]
        actual = fingerprint((self.root / path).read_bytes())
        for eid in self.committed:
            e = self.records[eid]
            if e["schema_version"] != "event@1" or e["type"] not in ("RESULT_ADMITTED", "DECISION_RECORDED", "RELEASE_ADMITTED"):
                continue
            if e["observation"] != "instrumented" or e["origin"] != "research-cli":
                continue
            expected = "RELEASE_ADMITTED" if self.records[rid]["schema_version"] == "release@1" else "DECISION_RECORDED"
            if e["type"] != expected or e["subject"] != rid:
                continue
            members = e["members"]
            if not any(m["id"] == rid and m["path"] == path and m["sha256"] == actual for m in members):
                continue
            event_commit = first_commit(self.root, self.paths[eid])
            okay = bool(members)
            for m in members:
                data = self.records.get(m["id"])
                if not data or m["id"] not in self.committed or self.paths[m["id"]] != m["path"]:
                    okay = False
                    break
                if fingerprint((self.root / m["path"]).read_bytes()) != m["sha256"]:
                    okay = False
                    break
                if not ancestor(self.root, first_commit(self.root, m["path"]), event_commit):
                    okay = False
                    break
            if okay:
                return True
        return False

    def references(self, refs, action: str, covered=None, current=False) -> list[tuple[str, str]]:
        results = []
        if current:
            selected = {review.ref_parts(raw)[0] for raw in refs}
            all_refs = {rid: r for rid, r in self.records.items() if r["schema_version"] == "references@1" and rid in self.committed}
            superseded = {r["supersedes"] for r in all_refs.values() if r["supersedes"]}
            for rid, r in all_refs.items():
                if rid not in superseded and any(c["materiality"] == "required" and action in c["applies_to"] for c in r["criteria"]) and rid not in selected:
                    results.append(("NOT_VERIFIED", f"active project reference missing: {rid}"))
            if selected & superseded:
                results.append(("FAIL", "new action selected a superseded reference contract"))
        for raw in refs:
            rid, cid = review.ref_parts(raw)
            ref = self.records.get(rid)
            if not ref or rid not in self.committed or ref["schema_version"] != "references@1":
                results.append(("NOT_VERIFIED", f"reference contract unavailable: {raw}"))
                continue
            authority = ref["authority"]
            witness = self.records.get(authority.get("attestation_ref", ""))
            if not witness or witness["id"] not in self.committed or witness.get("type") != "AUTHORITY_ATTESTED" or witness["subject"] != rid or witness.get("identity") != authority["identity"] or witness["observation"] != "human_attested":
                results.append(("NOT_VERIFIED", f"human reference authority not attested: {rid}"))
            candidates = [c for c in ref["criteria"] if (not cid or c["id"] == cid)]
            if not candidates:
                results.append(("FAIL", f"criterion does not exist: {raw}"))
            for c in candidates:
                if c.get("refresh_at"):
                    from datetime import datetime, timezone
                    if datetime.now(timezone.utc) >= datetime.fromisoformat(c["refresh_at"].replace("Z", "+00:00")):
                        results.append(("NOT_VERIFIED", f"criterion requires renewed inspection: {rid}#{c['id']}"))
                key = rid + "#" + c["id"]
                if action not in c["applies_to"] or c["materiality"] == "advisory":
                    continue
                if key not in (covered or set()):
                    results.append(("NOT_VERIFIED", f"required criterion not adjudicated: {key}"))
        return results

    def scientific_result(self, value: dict, decides=None) -> list[tuple[str, str]]:
        if value["kind"] != "result":
            return []
        map_path = self.root / "RESEARCH.map"
        if not map_path.exists():
            return [("NOT_VERIFIED", "result provenance requires RESEARCH.map")]
        result, runs, index = epistemic.check_runs(self.root, map_path)
        outcomes = [(result.status, "; ".join(result.lines) or result.summary)]
        plan, _, _ = epistemic.parse_plan(self.root)
        exposed = epistemic.check_exposure(plan, runs)
        outcomes.append((exposed.status, "; ".join(exposed.lines) or exposed.summary))
        lineage = index.get(value["logical_id"])
        if not lineage or lineage["artifact"] != value["path"]:
            outcomes.append(("FAIL", "result resource has no matching RUN output"))
        elif runs[lineage["run"]]["commit"] != value["revision"]:
            outcomes.append(("FAIL", "result resource must bind the actual run-output commit"))
        if decides:
            if not lineage or lineage["hypothesis"] != decides or lineage["mode"] != "confirmatory" or lineage["analysis_role"] != "primary" or lineage["test"] != lineage["frozen_primary_test"]:
                outcomes.append(("FAIL", "only the frozen confirmatory primary result can decide H"))
        return outcomes

    def decision_checks(self, record: dict, stack=(), enforce_current_refs=False) -> list[tuple[str, str]]:
        results = []
        target = record["target"]
        target_binding = {k: v for k, v in target.items() if k in ("resource_ref", "binding", "current_path", "current_record", "refresh_rule", "refresh_at")}
        results.append(applicability(self.root, target_binding, record, self.records))
        tr = resolve(target["resource_ref"], record, self.records)
        if tr["kind"] != "restricted_external":
            text = frozen_bytes(self.root, tr["revision"], tr["path"]).decode(errors="replace")
            if target["text"] not in text:
                results.append(("FAIL", "exact target formulation absent from referenced resource"))
        results.append(verify(self.root, resolve(record["rationale_ref"], record, self.records)))
        has_evidence = False
        for route in record["basis"]["routes"]:
            for binding in route["all_of"]:
                value = resolve(binding["resource_ref"], record, self.records)
                results.append(applicability(self.root, binding, record, self.records))
                has_evidence |= value["kind"] in ("result", "source", "restricted_external")
                results.extend(self.scientific_result(value, target.get("decides")))
        if record["disposition"] in ("adopt", "narrow", "retain") and not has_evidence:
            results.append(("NOT_VERIFIED", "material adoption has no declared result/source evidence"))
        covered = set()
        adequate = False
        contraction = record["disposition"] in ("withdraw", "defer", "reopen")
        for pointer in record["judgments"]:
            rid, cid = review.ref_parts(pointer)
            r = self.records.get(rid)
            if not r or r["schema_version"] != "review@1":
                results.append(("NOT_VERIFIED", f"not a review judgment: {pointer}"))
                continue
            state, reasons = self.state(rid, stack)
            results.extend(reasons)
            if state != "CURRENT":
                results.append(("STALE" if state == "STALE" else "NOT_VERIFIED", f"review {rid} is {state}"))
            match = next((c for c in r["claims"] if c["id"] == (cid or target["id"])), None)
            if match and match["id"] == target["id"] and match["text"] == target["text"] and (match["result"] == "adequate" or contraction):
                adequate = (state == "CURRENT" and (r["verdict"] == "PASS" or contraction)) or adequate
                covered.update(match["criteria"])
                target_review = resolve(match["resource_ref"], r, self.records)
                if target_review != tr:
                    results.append(("FAIL", "review and decision target different resource versions"))
                # Compare canonical dictionaries without assuming they are hashable.
                from contracts import digest
                witnessed = {digest(resolve(ref, r, self.records)) for ref in match["evidence"]}
                for route in record["basis"]["routes"]:
                    for b in route["all_of"]:
                        if digest(resolve(b["resource_ref"], record, self.records)) not in witnessed:
                            results.append(("NOT_VERIFIED", "review does not cover a declared support dependency"))
        if not adequate:
            results.append(("NOT_VERIFIED", "material adoption lacks applicable adequate separate review"))
        results.extend(self.references(record["references"], record["action"], covered, current=enforce_current_refs))
        if target.get("decides") and not any(resolve(b["resource_ref"], record, self.records)["kind"] == "result" for j in record["basis"]["routes"] for b in j["all_of"]):
            results.append(("FAIL", "hypothesis decision requires a primary result"))
        prior = record.get("supersedes")
        if prior:
            old = self.records.get(prior)
            if not old or prior not in self.committed or old["schema_version"] != "decision@1" or old["target"]["id"] != target["id"]:
                results.append(("FAIL", "decision supersession target missing or incompatible"))
        if enforce_current_refs:
            for rid, old in self.records.items():
                if old["schema_version"] == "decision@1" and old["target"]["id"] == target["id"] and self.consolidated(rid):
                    if not any(x.get("supersedes") == rid and self.consolidated(x["id"]) for x in self.records.values()) and prior != rid:
                        results.append(("FAIL", "new decision must explicitly supersede the existing adopted target"))
        return results

    def state(self, rid: str, stack=()) -> tuple[str, list[tuple[str, str]]]:
        if rid in stack:
            raise ContractError("judgment dependency cycle")
        if rid in self._cache:
            return self._cache[rid]
        record = self.records[rid]
        successors = [r for r in self.records.values() if r.get("supersedes") == rid and self.consolidated(r["id"])]
        if len(successors) > 1:
            raise RecoveryRequired(f"conflicting successors of {rid}")
        if successors:
            # Consolidated replacement is irreversible history. Staleness of a
            # later judgment must never silently resurrect an earlier claim.
            successor = successors[0]
            return ("WITHDRAWN" if successor.get("disposition") == "withdraw" else "SUPERSEDED", [])
        checks = []
        if record["schema_version"] == "review@1":
            checks = review.evaluate(self.root, record, self.records, self.committed, self.paths[rid], require_adequacy=False)
        elif record["schema_version"] == "decision@1":
            checks = self.decision_checks(record, (*stack, rid))
        elif record["schema_version"] == "release@1":
            from release import evaluate
            checks = evaluate(self, record)
        else:
            for value in record.get("resources", {}).values():
                checks.append(verify(self.root, value))
        state = "CURRENT"
        if rid not in self.committed or (record["schema_version"] in ("decision@1", "release@1") and not self.consolidated(rid)):
            state = "CANDIDATE"
        elif any(s in ("STALE", "FAIL") for s, _ in checks):
            state = "STALE"
        elif any(s == "NOT_VERIFIED" for s, _ in checks):
            state = "NOT_VERIFIED"
        if record.get("disposition") == "withdraw" and state == "CURRENT":
            state = "WITHDRAWN"
        self._cache[rid] = state, checks
        return state, checks


def check_supervision(root: Path) -> Result:
    result = Result()
    try:
        store = Store(root)
        if not store.project:
            result.add("NOT_VERIFIED", "no .research/project.json; supervision not initialized")
        for status, why in store.issues:
            result.add(status, why)
        for rid, record in store.records.items():
            state, checks = store.state(rid)
            for status, why in checks:
                result.add(status, f"{rid}: {why}")
            if state != "CURRENT":
                result.add("NOT_VERIFIED", f"{rid}: {state}")
        result.summary = f"{len(store.records)} supervision record(s); process integrity only"
    except (ContractError, OSError) as exc:
        result.add("FAIL", str(exc))
    return result
