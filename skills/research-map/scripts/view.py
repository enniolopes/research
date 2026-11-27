"""Offline, read-only projections of a study for a human or agent."""
from __future__ import annotations

import argparse
from collections import defaultdict, deque
from glob import escape
import hashlib
import json
from pathlib import Path
import sys

from contracts import ContractError, confirmatory_identity
from validate import DOC_SUFFIXES
import view_document
import view_native
import view_supervised
from view_reader import Reader, journal_entries


def connected(entries, start, downstream):
    """Follow only recorded relationships between exact occurrence selectors."""
    adjacency = defaultdict(list)
    for entry in entries:
        source = entry["selector"]
        for target in entry.get("related", []):
            if downstream:
                adjacency[source].append(target)
            else:
                adjacency[target].append(source)
    seen = {start}
    queue = deque([start])
    while queue:
        for target in adjacency[queue.popleft()]:
            if target not in seen:
                seen.add(target)
                queue.append(target)
    return seen


def summary(entry):
    keys = ("selector", "kind", "label", "source", "locator", "version", "aliases")
    result = {key: entry[key] for key in keys if key in entry}
    text = entry.get("text", "")
    if text:
        result["text"] = text if len(text) <= 300 else text[:299].rstrip() + "…"
    fields = ("basis", "binding", "state", "recorded_state", "disposition", "review", "verdict",
              "judgment", "support_status", "limits", "revision_conditions", "refutation", "missing_labels")
    details = entry.get("details", {})
    if retained := {key: details[key] for key in fields if details.get(key)}:
        result["details"] = retained
    return result


def overview(entries, has_inquiries=False):
    # Pointers keep the compact reading and the detailed entries in agreement.
    groups = [
        ("Question", {"question"}, "No explicit research question located."),
        ("Design and hypotheses", {"method", "hypothesis"}, "No explicit design or hypothesis located."),
        ("Claims and decisions", {"claim", "decision"}, "No conclusion located in the inspected material."),
        ("Assessment and uncertainty", {"uncertainty", "finding", "review"}, "No assessment or uncertainty located."),
        ("Next action", {"next_action"}, "No next action recorded in the inspected material."),
    ]
    result = []
    for title, kinds, gap in groups:
        members = [e for e in entries if e["kind"] in kinds]
        # Keep decisions relevant to work in progress ahead of closed history.
        members.sort(key=lambda e: e.get("details", {}).get("state") == "SUPERSEDED")
        selectors = [e["selector"] for e in members]
        covered_by_inquiry = has_inquiries and title in ("Question", "Next action")
        result.append({"title": title, "selectors": selectors, "gap": None if selectors or covered_by_inquiry else gap})
    return result


def explicit_source(reader, root, target, entries):
    """Identify an explicitly requested study document, including one without links."""
    prefix = "study-file:"
    if target.startswith(prefix):
        parts = target[len(prefix):].split(":", 1)
        if len(parts) != 2:
            return None
        name = parts[1]
    else:
        name = target
    path = Path(name)
    if (path.suffix.lower() not in DOC_SUFFIXES | {".pdf"} or path.is_absolute()
            or any(part.startswith(".") for part in path.parts)):
        return None
    full = root / path
    if not reader.permits(full):
        reader.partial("A requested source is unavailable for this audience.")
        return None
    if not reader.watch_dir(full.parent, escape(full.name)) or not full.is_file():
        return None
    version = hashlib.sha256(reader.read(full)).hexdigest()
    # The digest binds this file to this particular study and version.
    identity = hashlib.sha256(str(root).encode() + b"\0" + version.encode()).hexdigest()
    name = path.as_posix()
    selector = f"{prefix}{identity}:{name}"
    return {"selector": selector, "kind": "document", "label": name, "source": name,
            "version": version, "aliases": [name], "locator": "file",
            "details": {"basis": "explicitly inspected study file"},
            "related": [e["selector"] for e in entries if e["source"] == name and e.get("version") == version]}


def select(entries, operation, target):
    if operation == "status":
        # Dependency nodes are available by following a claim's explanation.
        supporting = {"resource", "route", "references", "inquiry"}
        return "complete", [summary(e) for e in entries if e["kind"] not in supporting]
    matches = [entry for entry in entries if entry["selector"] == target]
    if not matches:
        matches = [entry for entry in entries if target in entry.get("aliases", [])]
    if not matches:
        return "not_found", []
    if len(matches) > 1:
        return "ambiguous", [summary(e) for e in matches]
    selected = matches[0]
    scope = connected(entries, selected["selector"], downstream=operation == "impact")
    if operation == "explain":
        # A review can address the whole manuscript without supporting each of its claims.
        context = {ref for e in entries if e["selector"] in scope for ref in e.get("context", [])}
        scope.update(context)
    return "complete", [selected, *(e for e in entries if e is not selected and e["selector"] in scope)]


def link_inquiry_executions(entries, journal_complete):
    inquiries = {}
    for entry in entries:
        if entry["kind"] == "inquiry" and (action := entry["details"]["recorded_action"]):
            inquiries[entry["label"], entry["version"], action["criterion"]] = entry
    for entry in entries:
        binding = entry.pop("inquiry_binding", None)
        if binding is None:
            continue
        inquiry = inquiries.get((binding["id"], binding["sha256"], binding["criterion"]))
        if not inquiry:
            continue
        entry["related"].append(inquiry["selector"])
        executions = inquiry["details"]["executions"]
        operation_id = entry["aliases"][0]
        if not any(execution["operation_id"] == operation_id for execution in executions):
            executions.append({"operation_id": operation_id, "state": entry["details"]["state"],
                               "source": "worktree_journal", "selector": entry["selector"]})
    histories = defaultdict(dict)
    for entry in inquiries.values():
        details = entry["details"]
        analysis = confirmatory_identity(details["recorded_action"].get("confirmatory"))
        if analysis:
            histories[analysis].update({e["operation_id"]: e for e in details["executions"]})
    for entry in inquiries.values():
        details = entry["details"]
        analysis = confirmatory_identity(details["recorded_action"].get("confirmatory"))
        if not analysis or details["next"]["state"] != "proposed":
            continue
        if histories.get(analysis):
            details["executions"] = list(histories[analysis].values())
            needs_recovery = any(execution["state"] != "executed" for execution in details["executions"])
            details["next"] = {"state": "recover_execution" if needs_recovery else "inspect_execution"}
        elif not journal_complete:
            details["next"] = {"state": "verify_execution"}


def query(args):
    for _ in range(2):
        reader = Reader(args.audience)
        reader.operation = args.operation
        entries = []
        revision = None
        if args.document is not None:
            entries = view_document.collect(reader, args.document, args.review)
        else:
            root = args.root
            if not root.is_dir():
                raise ValueError("Study directory unavailable.")
            revision = reader.watch_git(root)
            maps = reader.watch_dir(root, "RESEARCH.map")
            projects = reader.watch_dir(root / ".research", "project.json")
            if maps:
                entries.extend(view_native.collect(reader, root))
            if projects:
                entries.extend(view_supervised.collect(reader, root, target=args.target))
                entries.extend(journal_entries(reader, root))
                link_inquiry_executions(entries, reader.journal_complete)
            if not (maps or projects):
                reports = [] if reader.issues else reader.watch_dir(root, view_document.REVIEW_FILENAME)
                if reports:
                    entries.extend(view_document.collect(reader, reports[0], trace_citations=True))
                else:
                    reader.partial("No readable study map, supervision records or RESEARCH-REVIEW.md. For a manuscript use --document.")
            if args.target and (args.operation == "impact" or args.target.startswith("study-file:")):
                if not any(args.target == e["selector"] or args.target in e.get("aliases", []) for e in entries):
                    if item := explicit_source(reader, root, args.target, entries):
                        entries.append(item)
        if reader.stable():
            status, items = select(entries, args.operation, args.target)
            # Lack of access or incomplete enumeration cannot prove a record absent.
            if reader.issues and status == "not_found":
                status = "partial"
            break
    else:
        status, items = "partial", []
        entries = []
        reader.issues.clear()
        reader.partial("Inputs changed during both read attempts. Repeat the query.")
        revision = None

    if status == "complete" and reader.issues:
        status = "partial"
    inquiries = [
        {"selector": e["selector"], "source": e["source"], **e["details"]}
        for e in entries if e["kind"] == "inquiry" and e["details"]["question_id"] in e["aliases"]
    ] if args.operation == "status" else []
    result = {
        "schema_version": "research-view@1",
        "operation": args.operation,
        "status": status,
        "snapshot": {"input": "document" if args.document else "study",
                     "revision": revision, "evaluated_at": reader.as_of.isoformat(),
                     "id": reader.snapshot_id() if status != "partial" or items or inquiries else None},
        "entries": items,
        "issues": list(dict.fromkeys(reader.issues)),
    }
    if args.operation != "status":
        result["target"] = items[0]["selector"] if items and status != "ambiguous" else None
    if args.operation == "impact":
        result["coverage"] = "Only declared links within inspected material. Review candidate consequences."
        if status == "complete":
            result["impact"] = "candidates" if len(items) > 1 else "no_declared_dependents"
    elif args.operation == "explain":
        result["coverage"] = "Recorded grounds in inspected material. Missing judgments require assessment."
    else:
        result["coverage"] = "Recorded study overview. Use explain with a selector to inspect its grounds."
        result["inquiries"] = inquiries
        result["overview"] = overview(items, has_inquiries=bool(inquiries))
    return result


def status_lines(report):
    lines = []
    indexed = {e["selector"]: e for e in report["entries"]}
    groups = [(g["title"], g["selectors"], g["gap"]) for g in report["overview"]]
    shown = {key for _, selectors, _ in groups for key in selectors}
    others = [key for key in indexed if key not in shown]
    if others:
        groups.append(("Other records", others, None))
    for title, selectors, gap in groups:
        if not selectors and not gap:
            continue
        lines.extend(["", f"## {title}", ""])
        if gap:
            lines.append(gap)
        for i, key in enumerate(selectors):
            if i == 2:
                lines.extend(["", f"<details><summary>{len(selectors) - i} more records</summary>", ""])
            item = indexed[key]
            qualifiers = ", ".join(f"{k.replace('_', ' ')}: {display(v)}"
                                   for k, v in item.get("details", {}).items())
            heading = f"- **{item['label']}**"
            if qualifiers:
                heading += f" ({qualifiers})"
            text = " ".join(item.get("text", "").split())
            if text:
                heading += " — " + text
            location = item["source"]
            if item.get("locator"):
                location += "#" + item["locator"]
            lines.extend([heading, f"  Source: {location}"])
        if len(selectors) > 2:
            lines.extend(["", "</details>"])
    if indexed:
        lines.extend(["", "<details><summary>Sources and selectors for explain</summary>", ""])
        for key, item in indexed.items():
            location = item["source"] + ("#" + item["locator"] if item.get("locator") else "")
            version = f" @ {item['version']}" if item.get("version") else ""
            aliases = ", ".join(item.get("aliases", []))
            lines.extend([f"- {item['kind']} · {location}{version} · {aliases}", f"  `{key}`"])
        lines.extend(["", "</details>"])
    return lines


def inquiry_lines(inquiries):
    lines = []
    messages = {
        "closed": "All recorded criteria are met or have a documented limitation.",
        "reassess": "Reassess the inquiry against the changed evidence before using its recorded action.",
        "verify": "Verify the inquiry and its supporting records before using its recorded action.",
        "inspect_execution": "Inspect the recorded execution and its outputs before choosing the next action.",
        "recover_execution": "Inspect the failed or unfinished execution and possible exposure before retrying.",
        "verify_execution": "Confirm the execution history with an authorized operator before proceeding.",
    }
    for inquiry in inquiries:
        lines.extend(["", f"## {inquiry['question_id']} · {inquiry['question']}", "",
                      inquiry["importance"], "", f"Recorded by {inquiry['assessed_by']}.",
                      f"Source: {inquiry['source']} · `{inquiry['selector']}`", ""])
        for criterion in inquiry["criteria"]:
            validity = "" if criterion["applicable"] else " · applicability unverified"
            lines.append(f"- **{criterion['dimension']} · {criterion['assessment']}{validity}** "
                         f"— {criterion['reason']} Desired condition: {criterion['desired']}")
        if inquiry["observation"]:
            lines.extend(["", f"Last observation — {inquiry['observation']['text']}"])
        step = inquiry["next"]
        if step["state"] == "proposed":
            lines.extend(["", f"**Proposed action** — {step['action']}",
                          f"**Expected signal** — {step['expected_signal']}"])
        else:
            lines.extend(["", messages[step["state"]]])
            for execution in inquiry["executions"]:
                lines.append(f"- {execution['operation_id']} · {execution['state']} · {execution['source']}")
            for check in inquiry["checks"]:
                lines.append(f"- {check['reason']}")
    return lines


def markdown(report):
    lines = [f"# Research {report['operation']}", "", f"**{report['status']}**", "", report["coverage"]]
    if report.get("impact") == "no_declared_dependents":
        lines.extend(["", "No declared dependents found in the inspected material."])
    snapshot = report["snapshot"]
    lines.extend(["", f"Evaluated at {snapshot['evaluated_at']} ({snapshot['input']})."])
    if snapshot["revision"]:
        lines.append(f"Git revision: `{snapshot['revision']}`")
    if snapshot["id"]:
        lines.append(f"Snapshot: `{snapshot['id']}`")
    if report["operation"] == "status":
        lines.extend(inquiry_lines(report["inquiries"]))
        lines.extend(status_lines(report))
    else:
        lines.extend(detail_lines(report["entries"]))
    if report["issues"]:
        lines.extend(["", "## Pending", "", *(f"- {message}" for message in report["issues"])])
    return "\n".join(lines)


def detail_lines(entries):
    lines = []
    for entry in entries:
        lines.extend(["", f"## {entry['label']}", "", f"`{entry['selector']}`"])
        for key, value in entry.items():
            if key in ("selector", "label") or value is None or value == []:
                continue
            if key == "text":
                lines.extend(["", str(value)])
            elif key == "details" and isinstance(value, dict):
                for field, detail in value.items():
                    lines.append(f"- {field}: {display(detail)}")
            else:
                lines.append(f"- {key}: {display(value)}")
    return lines


def display(value):
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("status", "explain", "impact"))
    parser.add_argument("target", nargs="?")
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--root", type=Path)
    inputs.add_argument("--document", type=Path)
    parser.add_argument("--review", type=Path)
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--audience", choices=("local", "model"), default="local")
    args = parser.parse_args(argv)
    if (args.operation == "status") != (args.target is None):
        parser.error("explain and impact require a target; status takes no target")
    if args.review and not args.document:
        parser.error("--review requires --document")
    if args.document and args.operation == "impact":
        parser.error("impact requires --root")
    for name in ("root", "document", "review"):
        path = getattr(args, name)
        if path is not None:
            setattr(args, name, path.absolute())
    try:
        report = query(args)
    except (OSError, ValueError, ContractError) as exc:
        message = "Input unavailable or invalid." if args.audience == "model" else str(exc)
        print(message, file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False) if args.format == "json" else markdown(report))
    return 1 if report["status"] in ("ambiguous", "not_found") else 0
