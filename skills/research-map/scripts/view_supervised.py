"""Read-only scientific views of supervised decisions and the reasons recorded for them."""
from __future__ import annotations

from dataclasses import dataclass
from glob import escape
from pathlib import Path

from contracts import ContractError, DIRECTORIES, digest, loads, validate
from events import RecoveryRequired
from resources import applicability, fingerprint, resolve, safe_path
from supervision_state import Store
import view_native


def _entry(selector, kind, label, source, *, aliases=(), text=None, **details):
    value = {"selector": selector, "kind": kind, "label": label, "source": source,
             "aliases": list(aliases), "related": [], "details": details}
    if "revision" in details:
        value["version"] = details["revision"]
    if details.get("locator"):
        value["locator"] = details["locator"]
    if text is not None:
        value["text"] = text
    return value


@dataclass
class ReadableRecords:
    """Visible source statements; incomplete inventory cannot establish supervisor state."""
    root: Path
    project: dict
    records: dict
    paths: dict


def _record_dependencies(record):
    """IDs whose content or authority contributes to fields projected from this record."""
    refs = list(record.get("references", record.get("reference_set", [])))
    refs.extend(record.get("judgments", []))
    if record["schema_version"] == "release@1":
        refs.extend(record["target"]["reference_set"])
        for key in ("decision_refs", "review_refs", "authority_refs"):
            refs.extend(record[key])
    for info in ("authority", "reviewer"):
        witness = record.get(info, {}).get("attestation_ref")
        if witness:
            refs.append(witness)
    if record.get("supersedes"):
        refs.append(record["supersedes"])
    for finding in record.get("findings", []):
        if finding.get("resolution_ref"):
            refs.append(finding["resolution_ref"])

    def foreign_refs(value):
        if isinstance(value, list):
            for item in value:
                yield from foreign_refs(item)
        elif isinstance(value, dict):
            if "record_id" in value and "resource_id" in value:
                yield value["record_id"]
            if isinstance(value.get("current_record"), str):
                yield value["current_record"]
            for item in value.values():
                yield from foreign_refs(item)

    return {ref.split("#", 1)[0] for ref in refs} | set(foreign_refs(record))


def _watch_runs(reader, root):
    for name in ("RESEARCH.map", "analysis-plan.md"):
        path = safe_path(root, name)
        if not reader.permits(path):
            raise PermissionError
        reader.watch_file(path)
    directory = root / ".research/runs"
    receipts = reader.watch_dir(directory, "*.json")
    if set(directory.glob("*.json")) != set(receipts):
        raise PermissionError
    for path in receipts:
        run = loads(reader.read(path))
        if not isinstance(run, dict):
            raise ContractError("invalid run receipt")
        for item in run.get("inputs", []):
            data_path = safe_path(root, item["path"])
            # check_runs only checks existence in the worktree, never raw input bytes.
            reader.watch_dir(data_path.parent, escape(data_path.name))
        for item in run.get("outputs", []):
            output = safe_path(root, item["artifact"])
            if not reader.permits(output):
                raise PermissionError
            reader.watch_file(output)


def _watch_record(reader, root, record, records, controlled):
    def inspect(raw, current):
        path = safe_path(root, raw)
        if not reader.permits(path):
            raise PermissionError
        if current:
            reader.watch_file(path)

    if record["schema_version"] == "review@1":
        inspect(record["report"]["path"], True)
        resource_refs = list(record["coverage"]["documents"])
        for claim in record["claims"]:
            resource_refs.extend([claim["resource_ref"], *claim["evidence"]])
        for check in record["checks"]:
            resource_refs.append(check["evidence_ref"])
        for ref in resource_refs:
            resolve(ref, record, records)
    if controlled and record["schema_version"] == "references@1":
        for criterion in record["criteria"]:
            path = safe_path(root, criterion["source"]["ref"].split("#", 1)[0])
            if not reader.permits(path) or path not in reader.watch_dir(path.parent, escape(path.name)) or not path.is_file():
                raise PermissionError
    for resource in record.get("resources", {}).values():
        if resource["kind"] == "restricted_external":
            if controlled:
                raise PermissionError
        else:
            inspect(resource["path"], record["schema_version"] == "release@1")
    bindings = list(record.get("dependencies", []))
    has_result = False
    if record["schema_version"] == "decision@1":
        resolve(record["rationale_ref"], record, records)
        bindings.append(record["target"])
        for route in record["basis"]["routes"]:
            bindings.extend(route["all_of"])
            for premise in route["all_of"]:
                value = resolve(premise["resource_ref"], record, records)
                has_result |= value["kind"] == "result"
    for binding in bindings:
        descriptor = resolve(binding["resource_ref"], record, records)
        if binding.get("binding") == "follow_current":
            raw = binding.get("current_path")
            if not raw:
                raw = descriptor.get("path")
            if raw:
                inspect(raw, True)
    return has_result


def _inventory(reader, root):
    """Pre-observe inputs of Store, which uses its own direct filesystem/Git APIs."""
    project_file = root / ".research/project.json"
    project = loads(reader.read(project_file))
    validate(project)
    if project["schema_version"] != "project@1":
        raise ContractError("invalid project record")
    controlled = reader.audience == "model" and reader.has_policy(project_file)
    records = {}
    paths = {}
    incomplete = False
    for schema, directory in DIRECTORIES.items():
        folder = root / ".research" / directory
        permitted = reader.watch_dir(folder, "*.json")
        if set(folder.glob("*.json")) != set(permitted):
            incomplete = True
        for path in permitted:
            try:
                value = loads(reader.read(path))
                validate(value)
                if (value["schema_version"] != schema or value["project_id"] != project["project_id"]
                        or value["id"] != path.stem):
                    raise ContractError("invalid record identity")
            except (ContractError, OSError, ValueError, UnicodeError):
                incomplete = True
                continue
            records[path.stem] = value
            paths[path.stem] = path.relative_to(root).as_posix()

    visible = dict(records)
    check_runs = False
    for rid, record in records.items():
        try:
            has_result = _watch_record(reader, root, record, records, controlled)
            # Run verification consults additional documents at historical revisions.
            if has_result and controlled:
                raise PermissionError
            check_runs |= has_result
        except (ContractError, OSError, KeyError, ValueError):
            del visible[rid]
            incomplete = True
    if incomplete:
        # Propagate omission through reviewers, referenced resources, authorities and successors.
        # Compute the fixed point before exposing any copied judgment or reason.
        while True:
            missing = [rid for rid, record in visible.items()
                       if _record_dependencies(record) - visible.keys()]
            if not missing:
                break
            for rid in missing:
                del visible[rid]
        reader.partial("Some supervised records or their evidence could not be inspected. Current authority is unverified.")
        return ReadableRecords(root, project, visible, paths)
    if check_runs:
        _watch_runs(reader, root)
    return Store(root, as_of=reader.as_of)


def _project(reader, store):
    project_id = store.project["project_id"]
    entries = {}
    by_record = {}

    for rid, record in sorted(store.records.items()):
        kind = record["schema_version"].split("@")[0]
        if kind not in {"decision", "review", "references", "release"}:
            continue
        source = store.paths[rid]
        revision = fingerprint(reader.read(store.root / source))
        selector = f"supervised:{project_id}:{revision}:{rid}"
        by_record[rid] = selector
        if isinstance(store, ReadableRecords):
            state, checks = "NOT_VERIFIED", []
        else:
            state, checks = store.state(rid)
            if store.issues and state == "CURRENT":
                state = "NOT_VERIFIED"
        entries[selector] = _entry(selector, kind, rid, source, aliases=[rid],
                                   state=state, revision=revision,
                                   checks=[{"status": s, "reason": t} for s, t in checks if s != "PASS"])

    def resource_selector(ref, record):
        descriptor = resolve(ref, record, store.records)
        revision = descriptor.get("revision", descriptor.get("version_label"))
        # Include the locator to distinguish occurrences within the same immutable file.
        identity = {key: descriptor.get(key) for key in
                    ("kind", "logical_id", "path", "revision", "sha256", "locator", "source_uri", "version_label")}
        selector = f"supervised:{project_id}:{digest(identity)}:resource"
        if selector not in entries:
            name = descriptor["logical_id"]
            path = descriptor.get("path", descriptor.get("source_uri", ""))
            entries[selector] = _entry(
                selector, "resource", name, path, aliases=[name, path],
                resource_kind=descriptor["kind"], revision=revision, locator=descriptor.get("locator"),
                sha256=descriptor.get("sha256"), availability=descriptor.get("availability", "recorded"),
            )
        return selector

    def edge(prereq, dependent):
        if dependent not in entries[prereq]["related"]:
            entries[prereq]["related"].append(dependent)

    for rid, selector in by_record.items():
        record = store.records[rid]
        node = entries[selector]
        details = node["details"]
        kind = node["kind"]
        if kind == "decision":
            target = record["target"]
            node["text"] = target["text"]
            node["aliases"].append(target["id"])
            rationale = resource_selector(record["rationale_ref"], record)
            formulation = resource_selector(target["resource_ref"], record)
            edge(rationale, selector)
            edge(formulation, selector)
            details.update(target=target["id"], formulation=formulation, rationale=rationale,
                           judgments=record["judgments"], limits=record["limits"],
                           revision_conditions=record["revision_conditions"], disposition=record["disposition"],
                           supersedes=record["supersedes"], predecessor=by_record.get(record["supersedes"]),
                           declared_origins=record["basis"]["origin_refs"], support_routes=[])
            for pointer in record["judgments"]:
                review_id = pointer.split("#", 1)[0]
                if review_id in by_record:
                    edge(by_record[review_id], selector)
            for position, route in enumerate(record["basis"]["routes"]):
                route_id = f"{selector}#route-{position + 1}"
                dependencies = []
                route_node = _entry(route_id, "route", route["id"], node["source"],
                                    aliases=[rid + "#" + route["id"]], dependencies=dependencies)
                entries[route_id] = route_node
                edge(route_id, selector)
                for binding in route["all_of"]:
                    resource = resource_selector(binding["resource_ref"], record)
                    if isinstance(store, ReadableRecords):
                        status, why = "NOT_VERIFIED", "Only recorded support is available in this partial inspection."
                    else:
                        status, why = applicability(store.root, binding, record, store.records, reader.as_of)
                    dependencies.append({"selector": resource, "binding": binding["binding"],
                                         "status": status, "reason": why})
                    edge(resource, route_id)
                statuses = {binding["status"] for binding in dependencies}
                status = next((s for s in ("FAIL", "STALE", "NOT_VERIFIED") if s in statuses),
                              "PASS" if dependencies else "NOT_VERIFIED")
                route_node["details"]["status"] = status
                details["support_routes"].append({"selector": route_id, "id": route["id"], "status": status})
            if len(record["basis"]["routes"]) > 1:
                details["route_scope"] = "Alternative routes require scientific review of surviving support and shared origins."
        elif kind == "review":
            details.update(verdict=record["verdict"], reviewed_commit=record["reviewed_commit"],
                           reviewer=record["reviewer"]["identity"], findings=record["findings"],
                           coverage=record["coverage"], claims=record["claims"])
            for binding in record["dependencies"]:
                edge(resource_selector(binding["resource_ref"], record), selector)
        elif kind == "release":
            for ref in record["resources"]:
                edge(resource_selector(ref, record), selector)
            for other in record["decision_refs"] + record["review_refs"]:
                if other in by_record:
                    edge(by_record[other], selector)
        elif kind == "references":
            details.update(criteria=record["criteria"], authority=record["authority"])
        refs = record.get("references", record.get("reference_set", []))
        if kind == "release":
            refs = record["target"]["reference_set"]
        for pointer in refs:
            reference_id = pointer.split("#", 1)[0]
            if reference_id in by_record:
                edge(by_record[reference_id], selector)
    return list(entries.values())


def collect(reader, root: Path):
    if not (root / ".research/project.json").exists():
        reader.watch_dir(root / ".research", "project.json")
        return []
    try:
        if getattr(reader, "operation", None) == "status":
            map_path = root / "RESEARCH.map"
            if map_path.exists() and not view_native.analysis_reached(reader.read(map_path).decode()):
                reader.partial("Pre-analysis status omits supervised judgments and outcomes until an analysis gate is reached.")
                return []
        store = _inventory(reader, root)
        if isinstance(store, Store) and store.issues:
            reader.partial("Supervised record integrity is incomplete; verify the project before relying on its judgments.")
        return _project(reader, store)
    except PermissionError:
        reader.partial("Some supervised evidence or its provenance is unavailable for this audience.")
    except RecoveryRequired:
        reader.partial("Supervised history requires recovery before a current assessment is available.")
    except (ContractError, OSError, UnicodeError, ValueError, KeyError, TypeError):
        reader.partial("Supervised records could not be verified; inspect the source records locally.")
    return []
