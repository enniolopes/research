"""Read recorded native scientific state without executing a validator or opening data."""

import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

import contracts
import epistemic
from resources import git
import validate


def local_path(root, name):
    path = Path(name)
    if not path.parts or path.is_absolute() or ".." in path.parts:
        raise ValueError("invalid relative pointer")
    current = root
    for part in path.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("symlink in study pointer")
    return current


def permitted_origins(reader, root, names):
    for name in names:
        try:
            if not reader.permits(local_path(root, name.split("#", 1)[0])):
                break
        except ValueError:
            break
    else:
        return True
    reader.partial("Some native material was withheld under the study policy.")
    return False


def visible_entries(reader, root, entries, controlled):
    if not controlled:
        return entries
    result = []
    for entry in entries:
        excerpt = entry["text"] + "\n" + json.dumps(entry.get("details", {}), ensure_ascii=False)
        names = validate.pointers_in(excerpt.splitlines())
        for match in re.finditer(r"\]\(([^)\s]+)\)", excerpt):
            target = match[1]
            if not target.startswith("#") and "://" not in target:
                names.append(target)
        if permitted_origins(reader, root, names):
            result.append(entry)
    visible = {entry["selector"] for entry in result}
    for entry in result:
        entry["related"] = [target for target in entry["related"] if target in visible]
    return result


def source(reader, root, name):
    try:
        path = local_path(root, name)
        if not reader.permits(path):
            reader.partial("A native source is unavailable for this destination.")
            return None
        content = reader.read(path)
        return Source(root, path, content)
    except (OSError, ValueError):
        reader.partial("A native source could not be read.")
        return None


class Source:
    def __init__(self, root, path, content):
        self.name = path.relative_to(root).as_posix()
        self.version = hashlib.sha256(content).hexdigest()
        self.text = content.decode("utf-8-sig")
        self.lines = self.text.splitlines()
        self.study = hashlib.sha256(str(root).encode()).hexdigest()

    def entry(self, kind, label, locator, text, aliases=(), **details):
        identity = json.dumps([self.study, self.name, self.version, locator, kind])
        selector = "native:" + hashlib.sha256(identity.encode()).hexdigest()
        item = dict(selector=selector, kind=kind, label=label, aliases=list(aliases),
                    source=self.name, locator=locator, version=self.version, text=text,
                    related=[])
        if details:
            item["details"] = details
        return item


def sections(doc):
    """Keep occurrences and source positions. Empty sections still have a locator."""
    headings = [(i, len(m[1]), validate.slug(m[2]))
                for i, line in enumerate(doc.lines)
                if (m := re.match(r"^(#{1,6})\s+(.+?)\s*$", line))]
    for index, (i, level, anchor) in enumerate(headings):
        end = next((n for n, following, _ in headings[index + 1:] if following <= level),
                   len(doc.lines))
        yield i, anchor, doc.lines[i + 1:end]


METHOD_HEADINGS = {"method", "methods", "methodology", "design", "study-design", "research-design",
                   "método", "métodos", "metodologia", "desenho", "desenho-do-estudo"}


def method_entries(doc):
    for index, heading, lines in sections(doc):
        if heading in METHOD_HEADINGS:
            yield doc.entry("method", doc.lines[index].lstrip("# "), f"L{index + 1}",
                            "\n".join(lines).strip(), [f"{doc.name}#{heading}"], basis="current design")
    for index, line in enumerate(doc.lines, 1):
        match = re.match(r"^\s*(?:[-*]\s*)?\**(Methods?|Study design|Design|Métodos?|Desenho)\**:\s*(\S.*)", line, re.I)
        if match:
            yield doc.entry("method", match[1], f"L{index}", match[2], basis="current design")


def native_files(reader, root, names):
    """Only explicitly selected document sources; avoid directory symlinks and hidden trees."""
    seen = set()
    for name in names:
        try:
            initial = local_path(root, name)
        except ValueError:
            reader.partial("A native document pointer is unavailable.")
            continue
        pending = [initial]
        while pending:
            path = pending.pop()
            if path in seen:
                continue
            seen.add(path)
            if path.is_symlink() or any(p.startswith(".") for p in path.relative_to(root).parts):
                reader.partial("A native document pointer was omitted.")
            elif path.is_dir():
                try:
                    pending.extend(reversed(sorted(reader.watch_dir(path, "*"))))
                except OSError:
                    reader.partial("A native document directory is unavailable.")
            elif path.suffix.lower() in validate.DOC_SUFFIXES:
                doc = source(reader, root, path.relative_to(root))
                if doc:
                    yield doc
            elif path == initial and not path.exists():
                reader.partial("A declared native document source is unavailable.")


def premise_entries(reader, root, state, pointers):
    for pointer in pointers:
        name, _, anchor = pointer.partition("#")
        if Path(name).suffix.lower() not in validate.DOC_SUFFIXES:
            reader.partial("The problem brief must have a readable document source.")
            continue
        brief = source(reader, root, name)
        if not brief:
            continue
        blocks = [(i, body) for i, heading, body in sections(brief) if heading == anchor.lower()]
        if not anchor:
            blocks = [(0, brief.lines)]
        if not blocks:
            reader.partial("The problem brief section could not be located.")
        for i, lines in blocks:
            body = "\n".join(lines)
            fields = [validate.labelled_field(body, f) for f in validate.BRIEF_FIELDS]
            verdict = validate.VERDICT.search(body)
            if verdict and verdict[1].upper() != state:
                reader.partial("The map and the recorded problem brief verdict disagree.")
            yield brief.entry("finding", "Problem brief", f"L{i + 1}",
                              "\n".join(field for field in fields if field), [pointer],
                              basis="recorded problem brief", judgment=verdict[1] if verdict else "unavailable")


def question_entries(reader, root, doc, layout):
    rows = [(i, body) for i, key, body in sections(doc) if key == "question"]
    questions = []
    map_questions = []
    pointers = []
    for i, body in rows:
        for line_no, line in enumerate(body, i + 2):
            if match := validate.PROBLEM_LINE.fullmatch(line):
                yield doc.entry("finding", "Problem premise", f"L{line_no}", match[1],
                                ["problem"], basis="map-reported assessment", source_pointer=match[2].strip())
                if match[1] != "PENDING":
                    yield from premise_entries(reader, root, match[1], validate.pointers_in([match[2]]))
            elif line.strip() and not validate.REGISTRATION.fullmatch(line) and not line.lstrip().startswith("#"):
                map_questions.append(doc.entry("question", "Question in study map", f"L{line_no}", line,
                                               [f"{doc.name}#question"]))
                pointers.extend(validate.pointers_in([line]))
    choices = pointers or layout.get("protocol", [])
    indexed_methods = set()
    for pointer in dict.fromkeys(choices):
        name, _, anchor = pointer.partition("#")
        if Path(name).suffix.lower() not in validate.DOC_SUFFIXES:
            reader.partial("The protocol question requires a readable document source.")
            continue
        protocol = source(reader, root, name)
        if not protocol:
            continue
        if name not in indexed_methods:
            yield from method_entries(protocol)
            indexed_methods.add(name)
        for index, key, body in sections(protocol):
            if key == (anchor or "question").lower():
                statement = "\n".join(body).strip()
                questions.append(protocol.entry("question", "Protocol question", f"L{index + 1}", statement,
                                                ["question", f"{name}#{key}"],
                                                missing_labels=validate.labelled_field_gaps(statement, validate.PROBLEM_FIELDS)))
    if not questions:
        reader.partial("The protocol question could not be located.")
        for question in map_questions:
            question["aliases"].append("question")
    yield from questions
    yield from map_questions


def analysis_reached(text: str) -> bool:
    """Read the native analysis boundary from phase rows in the study map."""
    sections_by_name, order = validate.parse_sections(text)
    if order.count("Gates") != 1:
        return False
    phases = {}
    for row in sections_by_name["Gates"]:
        match = re.match(r"\s*\|\s*([5-8])\b[^|]*\|\s*([^|]*?)\s*\|", row)
        if match:
            phase, state = match.groups()
            if phase in phases or state.lower() not in validate.GATE_STATES:
                return False
            phases[phase] = state.lower()
    return "reached" in phases.values()


DEFERRED_LINE = re.compile(r"^\s*[-*]\s+(\d{4}-\d{2}-\d{2}):\s*(.+?)\s+[—-]\s*enters when:\s*(\S.*)$", re.I)


def map_facts(doc):
    for start, key, lines in sections(doc):
        for i, line in enumerate(lines, start + 2):
            if key == "last-session" and (m := re.match(r"\s*[-*]\s+Next:\s*(\S.*)", line, re.I)):
                yield doc.entry("next_action", "Next action", f"L{i}", m[1], ["next"])
            if key == "deferred" and (m := DEFERRED_LINE.match(line)):
                date, idea, condition = m.groups()
                yield doc.entry("deferred", "Deferred idea", f"L{i}", f"{idea} — enters when: {condition}",
                                basis="deferred after freeze", recorded_date=date, entry_condition=condition)
            if key != "hypotheses" or not line.strip().startswith("|"):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) == 5 and re.fullmatch(r"H\d+", cells[0], re.I):
                ident, prediction, refutation, state, pointer = cells
                yield doc.entry("hypothesis", ident, f"L{i}", prediction, [ident.upper()],
                                refutation=refutation, recorded_state=state, source_pointer=pointer, basis="research map")


def claim_entries(doc):
    for match in epistemic.CLAIM.finditer(doc.text):
        claim, _, result, decides = match.groups()
        line_start = doc.text.rfind("\n", 0, match.start()) + 1
        line = doc.text.count("\n", 0, match.start()) + 1
        prefix = doc.text[line_start:match.start()].rsplit("-->", 1)[-1].strip()
        if not prefix and line > 1:
            prefix = doc.lines[line - 2].strip()
        yield doc.entry("claim", claim.upper(), f"L{line}:{match.start() - line_start + 1}",
                        prefix, [claim.upper()], result=result.upper(),
                        decides=decides.upper() if decides else None, basis="manuscript annotation")


def receipt_inputs(receipt, run, downstream):
    """An input occurrence refers to the historical receipt; never read its current values."""
    inputs = run.get("inputs")
    if not isinstance(inputs, list):
        return
    for i, item in enumerate(inputs):
        if isinstance(item, str):
            item = {"path": item}
        if not isinstance(item, dict) or not isinstance(item.get("path"), str) or not item["path"]:
            continue
        name = item["path"]
        aliases = [name]
        if isinstance(item.get("id"), str) and re.fullmatch(r"DATA\d+", item["id"]):
            aliases.append(item["id"])
        resource = receipt.entry("resource", aliases[-1], f"/inputs/{i}", "Input named in the run receipt.",
                                 aliases, recorded_path=name, role=item.get("role"), run_commit=run.get("commit"))
        resource["related"].append(downstream)
        yield resource


def frozen_hypothesis(reader, root, freeze, hypothesis):
    """Read ordinary Git blob bytes, without checkout filters, replacements or network."""
    if not isinstance(freeze, str) or not epistemic.COMMIT.fullmatch(freeze):
        return None
    name = "analysis-plan.md"
    if not reader.permits(root / name):
        reader.partial("A frozen plan is unavailable for this destination.")
        return None
    options = ("--no-replace-objects", "--no-lazy-fetch")
    try:
        if Path(git(root, *options, "rev-parse", "--show-toplevel").decode().strip()).resolve() != root.resolve():
            raise ValueError("study is not the repository root")
        commit = git(root, *options, "rev-parse", "--verify", f"{freeze}^{{commit}}").decode().strip()
        tree = git(root, *options, "ls-tree", "-z", commit, "--", name)
        regular = re.fullmatch(rb"100(?:644|755) blob ([0-9a-f]{40,64})\tanalysis-plan\.md\x00", tree)
        if not regular:
            raise ValueError("missing regular plan")
        content = git(root, *options, "cat-file", "blob", regular[1].decode())
        doc = Source(root, root / name, content)
    except (OSError, ValueError):
        reader.partial("The run's frozen analysis plan could not be inspected.")
        return None
    matches = [(index, body) for index, key, body in sections(doc) if key == hypothesis.lower()]
    if len(matches) != 1:
        reader.partial("A unique hypothesis section could not be located in the frozen plan.")
        return None
    index, lines = matches[0]
    text = "\n".join(lines).strip()
    limits = {label: value for label in ("May claim", "May not claim")
              if (value := epistemic.field_value(text, label))}
    locator = f"{commit}:L{index + 1}"
    return doc.entry("method", f"Frozen plan for {hypothesis}", locator, text, [f"{hypothesis}@{commit}"],
                     basis="frozen plan cited by run receipt", revision=commit, hypothesis=hypothesis,
                     mode=epistemic.field_value(text, "Mode"), limits=limits)


def receipt_entries(reader, root, controlled):
    try:
        directory = local_path(root, ".research/runs")
    except ValueError:
        reader.partial("Native run receipts are unavailable.")
        return
    frozen = {}
    for path in sorted(reader.watch_dir(directory, "*.json")):
        if not re.fullmatch(r"RUN-\d+\.json", path.name, re.I):
            continue
        receipt = source(reader, root, path.relative_to(root))
        if not receipt:
            continue
        try:
            run = contracts.loads(receipt.text)
            if not isinstance(run, dict) or run.get("id") != path.stem or not isinstance(run.get("outputs"), list):
                raise ValueError
        except (contracts.ContractError, ValueError):
            reader.partial("A native run receipt is malformed.")
            continue
        if controlled:
            inputs = run.get("inputs")
            if not isinstance(inputs, list):
                reader.partial("A receipt does not identify its input origins.")
                continue
            input_paths = [item.get("path") if isinstance(item, dict) else item for item in inputs]
            output_paths = [item.get("artifact") if isinstance(item, dict) else None for item in run["outputs"]]
            origins = input_paths + output_paths
            if not all(isinstance(name, str) and name for name in origins):
                reader.partial("A receipt does not identify all required origins.")
                continue
            if not permitted_origins(reader, root, origins):
                continue
        history = {key: run[key] for key in ("id", "test", "hypothesis", "estimand", "mode",
                   "analysis_role", "analysis_plan_freeze", "protocol_freeze", "commit")
                   if isinstance(run.get(key), str)}
        receipt_entry = receipt.entry("run", run["id"], "/id", "Recorded run receipt.", [run["id"]], run=history)
        yield receipt_entry
        freeze, hypothesis = run.get("analysis_plan_freeze"), run.get("hypothesis")
        if isinstance(freeze, str) and isinstance(hypothesis, str) and re.fullmatch(r"H\d+", hypothesis):
            key = (freeze, hypothesis)
            if key not in frozen:
                frozen[key] = frozen_hypothesis(reader, root, freeze, hypothesis)
                if frozen[key]:
                    yield frozen[key]
            if frozen[key]:
                frozen[key]["related"].append(receipt_entry["selector"])
            else:
                receipt_entry["details"]["plan_status"] = "frozen hypothesis unavailable"
        else:
            receipt_entry["details"]["plan_status"] = "no frozen hypothesis identified by the receipt"
        yield from receipt_inputs(receipt, run, receipt_entry["selector"])
        for i, output in enumerate(run["outputs"]):
            if not isinstance(output, dict) or not isinstance(output.get("result"), str):
                reader.partial("A native result reference is malformed.")
                continue
            ident = output["result"]
            if re.fullmatch(r"R\d+", ident):
                artifact = output.get("artifact")
                aliases = [ident, artifact] if isinstance(artifact, str) and artifact else [ident]
                item = receipt.entry("result", ident, f"/outputs/{i}", "Output recorded in a run receipt.",
                                     aliases, run=history, basis="receipt; outcome bytes not inspected")
                receipt_entry["related"].append(item["selector"])
                yield item


def collect(reader, root):
    root = Path(root).absolute()
    doc = source(reader, root, "RESEARCH.map")
    if not doc:
        return []
    parts, _ = validate.parse_sections(doc.text)
    layout = validate.parse_layout(parts.get("Layout", []))
    entries = list(question_entries(reader, root, doc, layout))
    entries.extend(map_facts(doc))
    controlled = getattr(reader, "audience", "local") == "model" and reader.has_policy(root)
    plan_name = "analysis-plan.md"
    if reader.watch_dir(root, plan_name):
        plan = source(reader, root, plan_name)
        if plan:
            entries.extend(method_entries(plan))
            for i, key, body in sections(plan):
                if re.fullmatch(r"h\d+", key):
                    entries.append(plan.entry("hypothesis", key.upper(), f"L{i + 1}",
                                              "\n".join(body).strip(), [key.upper()],
                                              basis="current analysis plan"))
    for decisions in native_files(reader, root, layout.get("decisions", [])):
        for i, _, body in sections(decisions):
            if match := validate.DECISION_START.match(decisions.lines[i]):
                ident = "D-" + match[1]
                entries.append(decisions.entry("finding", ident, f"L{i + 1}", "\n".join(body).strip(),
                                               [ident], basis="recorded decision"))
    # Never open manuscript outcomes or result artifacts to fill an early status report.
    if not analysis_reached(doc.text):
        return visible_entries(reader, root, entries, controlled)
    results = list(receipt_entries(reader, root, controlled))
    by_result = defaultdict(list)
    for result in results:
        if result["kind"] == "result":
            by_result[result["label"]].append(result)
    entries.extend(results)
    for manuscript in native_files(reader, root, layout.get("documents", [])):
        for claim in claim_entries(manuscript):
            matches = by_result[claim["details"]["result"]]
            if controlled and len(matches) != 1:
                reader.partial("A claim's result origins could not be cleared for this destination.")
                continue
            if len(matches) == 1:
                matches[0]["related"].append(claim["selector"])
                claim["details"]["receipt"] = matches[0]["selector"]
            else:
                claim["details"]["support_status"] = "ambiguous" if matches else "receipt unavailable"
            entries.append(claim)
    return visible_entries(reader, root, entries, controlled)
