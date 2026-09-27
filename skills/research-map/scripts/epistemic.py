#!/usr/bin/env python3
"""Mechanical epistemic checks for research 0.8. Standard library only."""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

EMPTY = {"", "-", "—", "none", "n/a", "na", "tbd", "?"}
H_HEADING = re.compile(r"^##\s+(H\d+)\s*$", re.M)
ASSUMPTION_ROW = re.compile(r"^\|\s*(A\d+)\s*\|\s*([^|]+?)\s*\|\s*(K\d+)\s*\|\s*([^|]+?)\s*\|\s*$", re.M)
CLAIM = re.compile(r"<!--\s*claim:(C\d+)\s+inference:(I\d+)\s+result:(R\d+)(?:\s+decides:(H\d+))?\s*-->", re.I)
COMMIT = re.compile(r"^[0-9a-f]{7,40}$", re.I)
RUN_MODES = {"confirmatory", "exploratory", "validation"}
ANALYSIS_ROLES = {"primary", "sensitivity", "specification", "diagnostic"}
DATA_ROLES = {"discovery", "confirmatory", "validation"}


@dataclass
class Result:
    name: str
    status: str = "PASS"
    summary: str = ""
    lines: list[str] = field(default_factory=list)

    def fail(self, line: str) -> None:
        self.status = "FAIL"
        self.lines.append(line)

    def unverified(self, summary: str) -> None:
        if self.status == "PASS":
            self.status = "NOT_VERIFIED"
        self.summary = summary


def field_value(body: str, name: str) -> str:
    match = re.search(r"^\s*" + re.escape(name) + r"\s*:\s*(.*?)\s*$", body, re.I | re.M)
    return match.group(1).strip() if match else ""


def h_blocks(text: str) -> list[tuple[str, str]]:
    matches = list(H_HEADING.finditer(text))
    out: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        out.append((match.group(1).upper(), text[match.end():end]))
    return out


def parse_layout(map_path: Path) -> dict[str, list[str]]:
    text = map_path.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"(?ms)^## Layout\s*$\n(.*?)(?=^## |\Z)", text)
    out: dict[str, list[str]] = {}
    if not match:
        return out
    for line in match.group(1).splitlines():
        item = re.match(r"^\s*[-*]\s*([a-z]+)\s*:\s*(.+)$", line)
        if item:
            out[item.group(1)] = [p.strip().strip("`") for p in item.group(2).split(",") if p.strip()]
    return out


def plan_entry(body: str) -> dict:
    generated = field_value(body, "Generated from")
    generated_ids = [] if generated.lower() in EMPTY else [x.upper() for x in re.findall(r"DATA\d+", generated, re.I)]
    assumptions = [
        {"id": assumption.upper(), "text": text.strip(), "check": check.upper(), "failure": failure.strip()}
        for assumption, text, check, failure in ASSUMPTION_ROW.findall(body)
    ]
    primary = field_value(body, "Primary test").upper()
    mentioned_tests = {x.upper() for x in re.findall(r"\bT\d+\b", body, re.I)}
    if primary:
        mentioned_tests.add(primary)
    return {
        "estimand": field_value(body, "Estimand").upper(),
        "primary_test": primary,
        "mode": field_value(body, "Mode").lower(),
        "generated_raw": generated,
        "generated_from": generated_ids,
        "dependence": field_value(body, "Dependence"),
        "may_claim": field_value(body, "May claim"),
        "may_not_claim": field_value(body, "May not claim"),
        "confirmed": field_value(body, "CONFIRMED when"),
        "refuted": field_value(body, "REFUTED when"),
        "inconclusive": field_value(body, "INCONCLUSIVE when"),
        "assumptions": assumptions,
        "tests": mentioned_tests,
    }


def parse_plan_text(text: str) -> dict[str, dict]:
    return {hypothesis: plan_entry(body) for hypothesis, body in h_blocks(text)}


def parse_plan(root: Path) -> tuple[dict[str, dict], str, str]:
    path = root / "analysis-plan.md"
    if not path.is_file():
        return {}, "", ""
    text = path.read_text(encoding="utf-8", errors="replace")
    return parse_plan_text(text), field_value(text, "Freeze"), text


def is_empty(value: str) -> bool:
    return value.strip().strip("*`").lower() in EMPTY


def check_plan(root: Path) -> tuple[Result, dict[str, dict], str]:
    result = Result("plan")
    index, freeze, text = parse_plan(root)
    path = root / "analysis-plan.md"
    if not path.is_file():
        result.unverified("no analysis-plan.md; required before an analysis fit")
        return result, index, freeze
    blocks = h_blocks(text)
    if not blocks:
        result.fail("analysis-plan.md: no `## H<n>` hypothesis blocks")
        return result, index, freeze
    block_ids = [hypothesis for hypothesis, _ in blocks]
    duplicates = sorted({item for item in block_ids if block_ids.count(item) > 1})
    for duplicate in duplicates:
        result.fail(f"analysis-plan.md: duplicate hypothesis block {duplicate}")

    for hypothesis, plan in index.items():
        label = f"analysis-plan.md:{hypothesis}"
        estimand = plan["estimand"]
        test = plan["primary_test"]
        if not re.fullmatch(r"E\d+", estimand):
            result.fail(f"{label}: `Estimand:` must be E<n>, not {estimand or 'missing'}")
        if not re.fullmatch(r"T\d+", test):
            result.fail(f"{label}: `Primary test:` must be T<n>, not {test or 'missing'}")
        if plan["mode"] not in {"confirmatory", "exploratory"}:
            result.fail(f"{label}: Mode must be confirmatory or exploratory")
        for key, display in [
            ("dependence", "Dependence"),
            ("may_claim", "May claim"),
            ("may_not_claim", "May not claim"),
            ("confirmed", "CONFIRMED when"),
            ("refuted", "REFUTED when"),
            ("inconclusive", "INCONCLUSIVE when"),
        ]:
            if is_empty(plan[key]):
                result.fail(f"{label}: `{display}:` is missing or unresolved")
        if not plan["assumptions"]:
            result.fail(f"{label}: no `A<n> | assumption | K<n> | failure action` row")
        seen_a: set[str] = set()
        seen_k: set[str] = set()
        for assumption in plan["assumptions"]:
            if assumption["id"] in seen_a:
                result.fail(f"{label}: duplicate assumption {assumption['id']}")
            if assumption["check"] in seen_k:
                result.fail(f"{label}: duplicate check {assumption['check']}")
            seen_a.add(assumption["id"])
            seen_k.add(assumption["check"])
            if is_empty(assumption["text"]):
                result.fail(f"{label}: {assumption['id']} has no assumption text")
            if is_empty(assumption["failure"]):
                result.fail(f"{label}: {assumption['check']} has no prospective failure action")
        generated_raw = plan["generated_raw"]
        if not generated_raw:
            result.fail(f"{label}: missing `Generated from: none | DATA<n>, ...`")
        elif generated_raw.lower() not in EMPTY and not plan["generated_from"]:
            result.fail(f"{label}: Generated from must use DATA<n> ids or `none`")

    freeze_state = freeze.strip().lower()
    if freeze_state not in {"none", "frozen"}:
        result.fail("analysis-plan.md: `Freeze:` must be `none` or `frozen`; commit identity belongs in run manifests")
    elif freeze_state == "none":
        result.unverified(f"{len(index)} hypothesis block(s); plan is not frozen yet")
    elif result.status == "PASS":
        result.summary = f"{len(index)} hypothesis block(s); freeze marker frozen"
    return result, index, freeze


def git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)


def git_available(root: Path) -> bool:
    try:
        return git(root, "rev-parse", "--is-inside-work-tree").returncode == 0
    except OSError:
        return False


def commit_exists(root: Path, ref: str) -> bool:
    return bool(COMMIT.fullmatch(ref)) and git(root, "cat-file", "-e", f"{ref}^{{commit}}").returncode == 0


def is_ancestor(root: Path, ancestor: str, descendant: str) -> bool:
    return git(root, "merge-base", "--is-ancestor", ancestor, descendant).returncode == 0


def show(root: Path, ref: str, path: str) -> str | None:
    result = git(root, "show", f"{ref}:{path}")
    return result.stdout if result.returncode == 0 else None


def load_runs(root: Path) -> tuple[list[tuple[Path, dict]], list[str]]:
    runs: list[tuple[Path, dict]] = []
    errors: list[str] = []
    run_dir = root / ".research" / "runs"
    if not run_dir.is_dir():
        return runs, errors
    for path in sorted(run_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{path.relative_to(root)}: invalid JSON ({exc})")
            continue
        if not isinstance(data, dict):
            errors.append(f"{path.relative_to(root)}: JSON root must be an object")
            continue
        runs.append((path, data))
    return runs, errors


def check_runs(root: Path, map_path: Path, plan: dict[str, dict]) -> tuple[Result, dict[str, dict], dict[str, dict]]:
    result = Result("runs")
    runs, parse_errors = load_runs(root)
    for error in parse_errors:
        result.fail(error)
    if not runs:
        if result.status != "FAIL":
            result.unverified("no .research/runs/*.json manifests")
        return result, {}, {}

    layout = parse_layout(map_path)
    protocol = (layout.get("protocol") or ["protocol.md"])[0]
    have_git = git_available(root)
    run_index: dict[str, dict] = {}
    result_index: dict[str, dict] = {}
    seen_results: set[str] = set()
    temporal_unverified = 0

    for path, data in runs:
        rel = str(path.relative_to(root))
        run_id = str(data.get("id", "")).upper()
        if not re.fullmatch(r"RUN-\d+", run_id):
            result.fail(f"{rel}: id must be RUN-<n>")
            continue
        if run_id in run_index:
            result.fail(f"{rel}: duplicate run id {run_id}")

        mode = str(data.get("mode", "")).lower()
        analysis_role = str(data.get("analysis_role", "")).lower()
        if mode not in RUN_MODES:
            result.fail(f"{rel}: mode must be one of {sorted(RUN_MODES)}")
        if analysis_role not in ANALYSIS_ROLES:
            result.fail(f"{rel}: analysis_role must be one of {sorted(ANALYSIS_ROLES)}")

        hypothesis = str(data.get("hypothesis", "")).upper()
        estimand = str(data.get("estimand", "")).upper()
        test = str(data.get("test", "")).upper()
        if not re.fullmatch(r"H\d+", hypothesis):
            result.fail(f"{rel}: hypothesis must be H<n>")
        if not re.fullmatch(r"E\d+", estimand):
            result.fail(f"{rel}: estimand must be E<n>")
        if not re.fullmatch(r"T\d+", test):
            result.fail(f"{rel}: test must be T<n>")

        commit = str(data.get("commit", ""))
        protocol_freeze = str(data.get("protocol_freeze", ""))
        plan_freeze = str(data.get("analysis_plan_freeze", ""))
        registration = str(data.get("registration", "")).strip()
        frozen_primary = ""
        frozen_generated: list[str] = []
        frozen_tests: set[str] = set()
        temporal_ready = False

        if mode == "confirmatory":
            if registration.lower() in EMPTY:
                result.fail(f"{rel}: confirmatory run requires a recorded registration reference")
            for label, ref in [("commit", commit), ("protocol_freeze", protocol_freeze), ("analysis_plan_freeze", plan_freeze)]:
                if not COMMIT.fullmatch(ref):
                    result.fail(f"{rel}: confirmatory {label} must be a git commit id")
            if have_git and all(COMMIT.fullmatch(value) for value in (commit, protocol_freeze, plan_freeze)):
                missing = [ref for ref in (commit, protocol_freeze, plan_freeze) if not commit_exists(root, ref)]
                for ref in missing:
                    result.fail(f"{rel}: git commit {ref} does not exist")
                if not missing:
                    temporal_ready = True
                    if not is_ancestor(root, protocol_freeze, commit):
                        result.fail(f"{rel}: protocol freeze {protocol_freeze} does not predate run commit {commit}")
                    if not is_ancestor(root, plan_freeze, commit):
                        result.fail(f"{rel}: analysis-plan freeze {plan_freeze} does not predate run commit {commit}")
                    frozen_plan = show(root, plan_freeze, "analysis-plan.md")
                    if frozen_plan is None:
                        result.fail(f"{rel}: analysis-plan.md does not exist at freeze {plan_freeze}")
                    else:
                        frozen_index = parse_plan_text(frozen_plan)
                        if hypothesis not in frozen_index:
                            result.fail(f"{rel}: {hypothesis} did not exist in the frozen analysis plan")
                        else:
                            frozen_entry = frozen_index[hypothesis]
                            frozen_primary = frozen_entry["primary_test"]
                            frozen_generated = list(frozen_entry["generated_from"])
                            frozen_tests = frozen_entry["tests"]
                            if frozen_entry["mode"] != "confirmatory":
                                result.fail(f"{rel}: {hypothesis} was not confirmatory at analysis-plan freeze {plan_freeze}")
                            if estimand != frozen_entry["estimand"]:
                                result.fail(f"{rel}: estimand {estimand} disagrees with frozen {hypothesis} estimand {frozen_entry['estimand']}")
                            if analysis_role == "primary" and test != frozen_primary:
                                result.fail(f"{rel}: primary run uses {test}, but frozen primary test is {frozen_primary or 'missing'}")
                            elif analysis_role != "primary" and test not in frozen_tests:
                                result.fail(f"{rel}: {analysis_role} test {test} was not named in {hypothesis}'s frozen analysis plan")
                    frozen_protocol = show(root, protocol_freeze, protocol)
                    if frozen_protocol is None:
                        result.fail(f"{rel}: protocol `{protocol}` does not exist at freeze {protocol_freeze}")
                    elif hypothesis not in frozen_protocol:
                        result.fail(f"{rel}: {hypothesis} is not identifiable in frozen protocol `{protocol}`")
            elif not have_git:
                temporal_unverified += 1
                result.lines.append(f"{rel}: git unavailable/not a work tree; temporal ancestry NOT_VERIFIED")
        else:
            current_entry = plan.get(hypothesis)
            if current_entry is None:
                result.fail(f"{rel}: non-confirmatory run references {hypothesis}, which is not in current analysis-plan.md")
            elif estimand != current_entry["estimand"]:
                result.fail(f"{rel}: estimand {estimand} disagrees with current {hypothesis} plan ({current_entry['estimand']})")
            if have_git and COMMIT.fullmatch(commit) and commit_exists(root, commit):
                temporal_ready = True

        run_record = dict(data)
        run_record["_frozen_primary_test"] = frozen_primary
        run_record["_frozen_generated_from"] = frozen_generated
        run_index[run_id] = run_record

        inputs = data.get("inputs", [])
        if not isinstance(inputs, list):
            result.fail(f"{rel}: inputs must be a list")
            inputs = []
        for item in inputs:
            if not isinstance(item, dict):
                result.fail(f"{rel}: each input must be an object with id/path/role")
                continue
            data_id = str(item.get("id", "")).upper()
            data_path = str(item.get("path", ""))
            role = str(item.get("role", "")).lower()
            if not re.fullmatch(r"DATA\d+", data_id):
                result.fail(f"{rel}: input id must be DATA<n>")
            if not data_path:
                result.fail(f"{rel}: input {data_id or '?'} has no path")
            elif not (root / data_path).exists():
                result.fail(f"{rel}: input {data_id or '?'} path `{data_path}` does not exist")
            if role not in DATA_ROLES:
                result.fail(f"{rel}: input {data_id or '?'} role must be one of {sorted(DATA_ROLES)}")
            if temporal_ready and data_path and show(root, commit, data_path) is None:
                result.fail(f"{rel}: input {data_id or '?'} `{data_path}` did not exist at run commit {commit}")

        outputs = data.get("outputs", [])
        if not isinstance(outputs, list) or not outputs:
            result.fail(f"{rel}: outputs must be a non-empty list")
            outputs = []
        for item in outputs:
            if not isinstance(item, dict):
                result.fail(f"{rel}: each output must be an object with result/artifact")
                continue
            result_id = str(item.get("result", "")).upper()
            artifact = str(item.get("artifact", ""))
            if not re.fullmatch(r"R\d+", result_id):
                result.fail(f"{rel}: result id must be R<n>")
                continue
            if result_id in seen_results:
                result.fail(f"{rel}: duplicate result id {result_id}")
            seen_results.add(result_id)
            current_artifact = root / artifact if artifact else None
            if current_artifact is None or not current_artifact.is_file():
                result.fail(f"{rel}: {result_id} artifact `{artifact or 'missing'}` does not exist")
            if temporal_ready and artifact:
                frozen_artifact = show(root, commit, artifact)
                if frozen_artifact is None:
                    result.fail(f"{rel}: {result_id} artifact `{artifact}` did not exist at run commit {commit}")
                elif current_artifact is not None and current_artifact.is_file():
                    current_text = current_artifact.read_text(encoding="utf-8", errors="replace")
                    if current_text != frozen_artifact:
                        result.fail(f"{rel}: {result_id} artifact `{artifact}` drifted after run commit {commit}; create a new result/run id or restore the committed result")
            result_index[result_id] = {
                "run": run_id,
                "test": test,
                "hypothesis": hypothesis,
                "estimand": estimand,
                "artifact": artifact,
                "mode": mode,
                "analysis_role": analysis_role,
                "frozen_primary_test": frozen_primary,
                "analysis_plan_freeze": plan_freeze,
            }

    if result.status == "PASS" and temporal_unverified:
        result.unverified(f"{len(runs)} run(s); {temporal_unverified} temporal check(s) NOT_VERIFIED")
    elif result.status == "PASS":
        result.summary = f"{len(runs)} run(s), {len(result_index)} result(s)"
    return result, run_index, result_index


def iter_documents(root: Path, map_path: Path) -> list[Path]:
    layout = parse_layout(map_path)
    suffixes = {".md", ".qmd", ".rmd", ".tex", ".txt"}
    files: list[Path] = []
    for item in layout.get("documents", []):
        path = root / item
        if path.is_file() and path.suffix.lower() in suffixes:
            files.append(path)
        elif path.is_dir():
            files.extend(p for p in sorted(path.rglob("*")) if p.is_file() and p.suffix.lower() in suffixes)
    return files


def check_lineage(root: Path, map_path: Path, plan: dict[str, dict], result_index: dict[str, dict]) -> Result:
    result = Result("lineage")
    annotations = []
    seen_claims: set[str] = set()
    seen_inferences: set[str] = set()
    for path in iter_documents(root, map_path):
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in CLAIM.finditer(text):
            claim, inference, result_id, decides = [value.upper() if value else "" for value in match.groups()]
            label = f"{path.relative_to(root)}:{claim}"
            annotations.append((label, claim, inference, result_id, decides))
            if claim in seen_claims:
                result.fail(f"{label}: duplicate claim id {claim}")
            if inference in seen_inferences:
                result.fail(f"{label}: duplicate inference id {inference}")
            seen_claims.add(claim)
            seen_inferences.add(inference)
            lineage = result_index.get(result_id)
            if lineage is None:
                result.fail(f"{label}: result {result_id} has no run manifest lineage")
                continue
            if decides:
                if lineage["hypothesis"] != decides:
                    result.fail(f"{label}: {result_id} belongs to {lineage['hypothesis']}, not deciding hypothesis {decides}")
                elif lineage["mode"] != "confirmatory":
                    result.fail(f"{label}: {result_id} comes from a {lineage['mode']} run and cannot decide confirmatory hypothesis {decides}")
                elif lineage["analysis_role"] != "primary":
                    result.fail(f"{label}: {result_id} is a {lineage['analysis_role']} result; only the frozen primary analysis may decide {decides}")
                elif not lineage["frozen_primary_test"]:
                    result.fail(f"{label}: frozen primary test for {decides} is not verifiable from the run lineage")
                elif lineage["test"] != lineage["frozen_primary_test"]:
                    result.fail(f"{label}: {result_id} comes from {lineage['test']}, but the frozen primary test was {lineage['frozen_primary_test']}")
    if not annotations:
        result.unverified("no material claim annotations found under documents")
    elif result.status == "PASS":
        result.summary = f"{len(annotations)} material claim lineage annotation(s)"
    return result


def check_exposure(plan: dict[str, dict], runs: dict[str, dict]) -> Result:
    result = Result("exposure")
    checked = 0
    unverifiable = 0
    for run_id, run in runs.items():
        if str(run.get("mode", "")).lower() != "confirmatory":
            continue
        hypothesis = str(run.get("hypothesis", "")).upper()
        generated = set(run.get("_frozen_generated_from", []))
        if not generated and hypothesis in plan:
            # Best-effort fallback when temporal plan recovery was unavailable. The runs check
            # already marks temporal provenance NOT_VERIFIED in that case.
            generated = set(plan[hypothesis].get("generated_from", []))
            if generated and not run.get("_frozen_primary_test"):
                unverifiable += 1
        if not generated:
            continue
        confirmatory_inputs = {
            str(inp.get("id", "")).upper()
            for inp in run.get("inputs", [])
            if isinstance(inp, dict) and str(inp.get("role", "")).lower() == "confirmatory"
        }
        overlap = generated & confirmatory_inputs
        checked += 1
        if overlap:
            result.fail(f"{run_id}: {hypothesis} was generated from {', '.join(sorted(overlap))} and reuses the same data as independent confirmatory evidence")
    if not plan and not runs:
        result.unverified("no analysis plan or runs; exposure cannot be checked")
    elif result.status == "PASS" and unverifiable:
        result.unverified(f"{checked} comparison(s); {unverifiable} relied on current rather than frozen exposure state")
    elif result.status == "PASS":
        result.summary = f"{checked} discovery/confirmatory overlap comparison(s)"
    return result


def run(map_path: Path, root: Path, only: set[str] | None = None) -> list[Result]:
    plan_result, plan, _ = check_plan(root)
    run_result, runs, result_index = check_runs(root, map_path, plan)
    checks = {
        "plan": plan_result,
        "runs": run_result,
        "lineage": check_lineage(root, map_path, plan, result_index),
        "exposure": check_exposure(plan, runs),
    }
    return [checks[name] for name in ("plan", "runs", "lineage", "exposure") if only is None or name in only]
