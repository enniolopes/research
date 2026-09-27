#!/usr/bin/env python3
"""research-map validate — mechanical checks of a research repository against its RESEARCH.map.

    python validate.py [RESEARCH.map] [--root DIR] [--offline] [--strict] [--min-int 20] [--only map,numbers,...]

Run it from where the capability is installed; the consuming repository carries no copy.

Checks (each PASS / FAIL / NOT_VERIFIED, with the offending lines):
  map        required sections present, all sections ordered; pointers resolve; all eight gates with
             valid states, every `reached` gate naming its evidence (a pointer or a DOI/URL);
             at most three hypotheses without a terminal state;
             Registration line present; the Question pointer leads to a problem statement with its
             seven fields; the Problem line carries a state and, unless PENDING, a problem brief with
             its seven fields, a matching Verdict and a Reference that names the decision (D-<n>) that
             fixed it; no phase >= 3 is reached before Problem is SHOWN;
             every fact-once-wrong names a producing notebook;
             every Deferred item is dated and names its entry condition;
             Last session has a dated line and a Next line
  numbers    every number quoted in the documents and in the problem brief is present in some
             committed aggregate at the quoted precision (presence, not provenance); every
             `rm:ignore` marker carries a reason
  decisions  every D-<n> block has a non-empty revision condition; ids unique and increasing;
             `Supersedes: D-<k>` names an earlier block; decision ids that live in table rows are
             counted and reported as not checked
  disclosure no table cell under `documents` holds a count below the Layout `floor`
  citations  every reference resolves (Crossref, then doi.org; NOT_VERIFIED with --offline or when
             the network refuses the check)
  notebooks  no committed notebook carries outputs or execution counts

A check with nothing to examine reports NOT_VERIFIED, never PASS. Exit 1 on any FAIL; with
--strict also on NOT_VERIFIED. Standard library only. The grammar is reference/map-schema.md.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

# Section order. The six required ones are the state no other file holds; the four optional ones
# are validated when present and hold only what no file in Layout already says.
SECTIONS = [
    "Layout", "Question", "Hypotheses", "Gates", "Facts that were once wrong",
    "Provenance", "Verification", "Open decisions", "Deferred", "Last session",
]
REQUIRED_SECTIONS = ["Layout", "Question", "Hypotheses", "Gates", "Deferred", "Last session"]
LAYOUT_KEYS = ["protocol", "decisions", "aggregates", "documents", "notebooks", "references"]
LAYOUT_OPTIONAL = {"floor"}  # minimum cell size for anything under `documents`; an integer
PHASES = ["1", "2", "3", "4", "5", "6", "7", "8"]
GATE_STATES = {"reached", "pending", "blocked"}
HYPOTHESIS_STATES = {"CONFIRMED", "REFUTED", "INCONCLUSIVE", "BLOCKED", "NOT_VERIFIED", "—", "-"}
OPEN_HYPOTHESES = {"—", "-"}
OPEN_HYPOTHESES_CAP = 3
# `<!-- rm:ignore: <reason> -->` exempts a line from the numbers check; the reason is required.
IGNORE_MARK = re.compile(r"<!--\s*rm:ignore(?::\s*(\S[^>]*?))?\s*-->")
DOC_SUFFIXES = {".md", ".qmd", ".rmd", ".tex", ".txt"}
TABLE_SUFFIXES = {".md", ".qmd", ".rmd", ".csv", ".tsv"}
AGGREGATE_SUFFIXES = {".csv", ".tsv", ".json"}
POINTER_SUFFIXES = (".md", ".qmd", ".ipynb", ".csv", ".tsv", ".json", ".bib", ".py", ".R", ".txt", ".yaml", ".yml")

# A number token; the sign is read separately (sign_before) so that -0.31 is checked with its sign
# and D-37 is an identifier, not a number.
NUMBER = re.compile(r"(?<![\w.,])(\d{1,3}(?:[.,]\d{3})+(?:[.,]\d+)?|\d+(?:[.,]\d+)?)(?![\w])")
URL_OR_DOI = re.compile(r"https?://\S+|\b10\.\d{4,9}/\S+", re.I)
# Not results: a p-value or alpha threshold, and labels of sections, tables, figures, pages.
THRESHOLD_BEFORE = re.compile(r"(?:\bp|\balpha|α)\s*[<>≤≥=]\s*$", re.I)
LABEL_BEFORE = re.compile(r"(?:\bsections?|\bsec\.|§|\bse[çc][aã]o|\btables?|\btabelas?|\bfig(?:ures?|\.)?|\bfiguras?|\beq\.|\bp\.|\bpp\.)\s*$", re.I)
# A legal instrument's number is an identifier: `Lei 14.628`, `Portaria GM nº 12`, `Directive 2016/679`.
LEGAL_BEFORE = re.compile(
    r"\b(?:Lei|Decreto(?:-Lei)?|Portaria|Resolu[çc][ãa]o|Instru[çc][ãa]o Normativa|Medida Provis[óo]ria|"
    r"Emenda Constitucional|Law|Act|Directive|Regulation|Ordinance|Bill)\b[^\d\n.;:]{0,24}$", re.I)
CONFIDENCE_AFTER = re.compile(r"\s?%\s?(?:CI|IC)\b")
DOI = re.compile(r"\b(10\.\d{4,9}/[^\s\"'<>{}]+)")
DECISION_START = re.compile(r"^(?:#{1,6}\s+|[-*]\s+\*\*|\*\*)D-(\d+)\b", re.M)
DECISION_ROW = re.compile(r"^\s*\|\s*\**D-(\d+)\b", re.M)  # a decision written as a table row: not a block
REVISION = re.compile(r"^\s*(?:[-*]\s*)?(?:\*\*)?(?:Revision condition|Revise when)(?:\*\*)?\s*:\**\s*(.*)$", re.I | re.M)
EMPTY_VALUES = {"", "—", "-", "–", "none", "n/a", "na", "tbd", "?"}
SUPERSEDES = re.compile(r"^\s*(?:[-*]\s*)?\**Supersedes\**\s*:\**\s*D-(\d+)", re.I | re.M)
DECISION_REF = re.compile(r"\bD-(\d+)\b")
REGISTRATION = re.compile(r"^\s*(?:[-*]\s*)?\**Registration\**\s*:\s*(\S.*)$", re.I | re.M)
# The problem statement the Question pointer leads to must carry these labelled fields
# (scientific-method, reference/problem-statement.md).
PROBLEM_FIELDS = ["Claim", "Unit of analysis", "Estimand", "Refutation", "Objection", "Who cares", "Non-goals"]
# Gate 1B: the Question section carries `Problem: <state> → `<brief file[#anchor]>``; the brief
# (reference/problem-brief.md) carries these fields and a Verdict equal to the map's state.
PROBLEM_STATES = {"PENDING", "SHOWN", "NOT_SHOWN", "INCONCLUSIVE"}
PROBLEM_LINE = re.compile(r"^\s*(?:[-*]\s*)?\**Problem\**\s*:\**\s*(PENDING|SHOWN|NOT_SHOWN|INCONCLUSIVE)\b(.*)$", re.M)
BRIEF_FIELDS = ["Construct", "Population", "Measure", "Reference", "Magnitude", "Falsification", "Verdict"]
VERDICT = re.compile(r"^\s*(?:[-*]\s*)?(?:★\s*)?\**Verdict\**\s*:\**\s*(SHOWN|NOT_SHOWN|INCONCLUSIVE)\b", re.I | re.M)
# A deferred idea carries the date it appeared and the condition under which it would enter.
DEFERRED_ITEM = re.compile(r"^\s*[-*]\s*\d{4}-\d{2}-\d{2}:\s*.+\s[—-]\s*enters when:\s*\S.*$")
NETWORK_REFUSED = {401, 403, 405, 429}


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


# --- map ---------------------------------------------------------------------------------
def parse_sections(text: str) -> tuple[dict[str, list[str]], list[str]]:
    sections: dict[str, list[str]] = {}
    order: list[str] = []
    current = None
    for line in text.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            order.append(current)
            sections[current] = []
        elif current is not None:
            sections[current].append(line)
    return sections, order


def parse_layout(lines: list[str]) -> dict[str, list[str]]:
    layout: dict[str, list[str]] = {}
    for line in lines:
        match = re.match(r"^\s*[-*]\s*([a-z]+)\s*:\s*(.+)$", line)
        if match:
            layout[match.group(1)] = [p.strip().strip("`") for p in match.group(2).split(",") if p.strip()]
    return layout


def table_rows(lines: list[str]) -> list[list[str]]:
    rows = []
    for line in lines:
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-+:?", c) for c in cells if c):
            continue
        rows.append(cells)
    return rows[1:] if rows else []  # drop header


def pointers_in(lines: list[str]) -> list[str]:
    found = []
    for line in lines:
        for token in re.findall(r"`([^`\n]+)`", line):
            if " " in token:
                continue
            path = token.split("#")[0]
            if "/" in path or path.endswith(POINTER_SUFFIXES):
                found.append(token)
    return found


def slug(heading: str) -> str:
    text = re.sub(r"[^\w\s-]", "", heading.strip().lower())
    return re.sub(r"\s+", "-", text)


def section_at(path: Path, anchor: str) -> str | None:
    """Body of the section whose heading slugs to `anchor`, up to the next heading of the same or higher level."""
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    start, level = None, 0
    for i, line in enumerate(lines):
        match = re.match(r"^(#{1,6})\s+(.*)$", line)
        if not match:
            continue
        if start is None:
            if slug(match.group(2)) == anchor.lower():
                start, level = i, len(match.group(1))
        elif len(match.group(1)) <= level:
            return "\n".join(lines[start + 1:i])
    return "\n".join(lines[start + 1:]) if start is not None else None


def labelled_field_gaps(body: str, fields: list[str]) -> list[str]:
    return [
        f for f in fields
        if not re.search(r"^\s*(?:[-*]\s*)?(?:★\s*)?\**" + re.escape(f) + r"\**\s*:", body, re.I | re.M)
    ]


def decision_ids(root: Path, layout: dict[str, list[str]]) -> set[int] | None:
    """Ids of every decision block in the log; None when no log file exists (Layout reports that)."""
    files = iter_files(root, layout.get("decisions", []), DOC_SUFFIXES)
    if not files:
        return None
    ids: set[int] = set()
    for file in files:
        ids.update(int(m.group(1)) for m in DECISION_START.finditer(file.read_text(encoding="utf-8", errors="replace")))
    return ids


def labelled_field(body: str, label: str) -> str:
    """The text of one labelled field, continuation lines included, up to the next labelled field."""
    lines = body.splitlines()
    start = next((i for i, l in enumerate(lines)
                  if re.match(r"^\s*(?:[-*]\s*)?(?:★\s*)?\**" + re.escape(label) + r"\**\s*:", l, re.I)), None)
    if start is None:
        return ""
    out = [lines[start]]
    for line in lines[start + 1:]:
        if re.match(r"^\s*(?:[-*]\s*)?(?:★\s*)?\**[A-Z][\w ]{1,30}\**\s*:", line):
            break
        out.append(line)
    return "\n".join(out)


def check_problem_brief(result: Result, root: Path, question_lines: list[str], layout: dict[str, list[str]]) -> str | None:
    """Gate 1B in the map: the Problem line, and the brief it points to. Returns the brief path when there is one."""
    match = PROBLEM_LINE.search("\n".join(question_lines))
    if not match:
        result.fail("Question: missing `Problem: PENDING | SHOWN | NOT_SHOWN | INCONCLUSIVE → `<problem-brief.md>`` (gate 1B)")
        return None
    state, rest = match.group(1), match.group(2)
    pointers = pointers_in([rest])
    if state == "PENDING":
        return pointers[0].split("#")[0] if pointers else None
    if not pointers:
        result.fail(f"Question: Problem is {state} but names no problem brief")
        return None
    path, _, anchor = pointers[0].partition("#")
    if not (root / path).is_file():
        return None  # the pointer check reports it
    body = section_at(root / path, anchor) if anchor else (root / path).read_text(encoding="utf-8", errors="replace")
    if body is None:
        result.fail(f"Question: problem brief `{pointers[0]}` has no heading for anchor #{anchor}")
        return path
    missing = labelled_field_gaps(body, BRIEF_FIELDS)
    if missing:
        result.fail(f"Question: problem brief `{path}` lacks the field(s) {', '.join(missing)} (scientific-method reference/problem-brief.md)")
    verdict = VERDICT.search(body)
    if verdict and verdict.group(1).upper() != state:
        result.fail(f"Question: Problem is {state} in the map but the brief's Verdict is {verdict.group(1).upper()}")
    # The Reference names the decision that fixed it, so "fixed beforehand" can be read against a date.
    if "Reference" not in missing:
        refs = {int(m) for m in DECISION_REF.findall(labelled_field(body, "Reference"))}
        known = decision_ids(root, layout)
        if not refs:
            result.fail(f"Question: problem brief `{path}` Reference names no decision (D-<n>) that fixed it — a reference is dated by its decision, not by the sentence")
        elif known is not None and not refs & known:
            result.fail(f"Question: problem brief `{path}` Reference cites {', '.join(f'D-{r}' for r in sorted(refs))}, not a block in the decision log")
    return path


def problem_statement_gaps(root: Path, pointer: str) -> list[str]:
    """Why the problem statement behind the Question pointer is incomplete; empty when complete."""
    path, _, anchor = pointer.partition("#")
    if not anchor or not (root / path).is_file():
        return []  # no anchor, or a missing file: the pointer check reports the latter
    body = section_at(root / path, anchor)
    if body is None:
        return [f"has no heading for anchor #{anchor}"]
    missing = labelled_field_gaps(body, PROBLEM_FIELDS)
    if missing:
        return ["lacks the field(s) " + ", ".join(missing) + " (scientific-method reference/problem-statement.md)"]
    return []


def check_map(text: str, root: Path) -> tuple[Result, dict[str, list[str]]]:
    result = Result("map")
    sections, order = parse_sections(text)
    present = [s for s in order if s in SECTIONS]
    for name in REQUIRED_SECTIONS:
        if name not in sections:
            result.fail(f"missing section '## {name}'")
    if present != [s for s in SECTIONS if s in sections]:
        result.fail("sections out of order; order: " + " → ".join(SECTIONS))

    layout = parse_layout(sections.get("Layout", []))
    for key in LAYOUT_KEYS:
        if key not in layout:
            result.fail(f"Layout: missing key '{key}'")
        else:
            for path in layout[key]:
                if not (root / path).exists():
                    result.fail(f"Layout: {key} → {path} does not exist")
    if "floor" in layout and not (len(layout["floor"]) == 1 and layout["floor"][0].isdigit() and int(layout["floor"][0]) > 1):
        result.fail(f"Layout: floor must be one integer above 1 (the minimum cell size), not {', '.join(layout['floor'])!r}")

    pointer_count = 0
    for name, lines in sections.items():
        if name in {"Layout", "Verification"}:
            continue
        for pointer in pointers_in(lines):
            pointer_count += 1
            target = pointer.split("#")[0]
            if target and not (root / target).exists():
                result.fail(f"{name}: pointer `{pointer}` does not resolve")

    question = "\n".join(sections.get("Question", []))
    if not REGISTRATION.search(question):
        result.fail("Question: missing `Registration: none | <URL or DOI, date>` — confirmatory code stays DRY_RUN while it is none")
    question_lines = sections.get("Question", [])
    problem_match = PROBLEM_LINE.search("\n".join(question_lines))
    problem_state = problem_match.group(1) if problem_match else None
    brief_pointer = pointers_in([problem_match.group(2)]) if problem_match else []
    for pointer in pointers_in(question_lines):
        if pointer in brief_pointer:
            continue
        for gap in problem_statement_gaps(root, pointer):
            result.fail(f"Question: problem statement at `{pointer}` {gap}")
    brief_path = check_problem_brief(result, root, question_lines, layout)
    if brief_path:
        layout["_brief"] = [brief_path]

    seen_phases: set[str] = set()
    for row in table_rows(sections.get("Gates", [])):
        if len(row) < 2:
            continue
        phase = row[0].strip()[:1]
        seen_phases.add(phase)
        state = row[1].lower()
        if state not in GATE_STATES:
            result.fail(f"Gates: '{row[0]}' has state '{row[1]}' (valid: {sorted(GATE_STATES)})")
        elif state == "blocked" and (len(row) < 3 or not row[2]):
            result.fail(f"Gates: '{row[0]}' is blocked but names nobody in 'Blocked by'")
        elif state == "reached":
            evidence = row[3] if len(row) > 3 else ""
            if not (pointers_in([evidence]) or URL_OR_DOI.search(evidence)):
                result.fail(f"Gates: '{row[0]}' is reached but names no evidence — the fourth column points at the artifact the gate produces (or its DOI/URL); a gate is reached by its artifact, not by the word")
    missing_phases = [p for p in PHASES if p not in seen_phases]
    if "Gates" in sections and missing_phases:
        result.fail(f"Gates: one row per phase; missing phase(s) {', '.join(missing_phases)}")
    for row in table_rows(sections.get("Gates", [])):
        if len(row) >= 2 and row[0].strip()[:1] in set(PHASES[2:]) and row[1].lower() == "reached" and problem_state != "SHOWN":
            result.fail(f"Gates: '{row[0]}' is reached but Problem is {problem_state or 'missing'}; the protocol does not freeze before the problem is SHOWN")
            break

    hypotheses = table_rows(sections.get("Hypotheses", []))
    for row in hypotheses:
        if len(row) >= 4 and row[3] not in HYPOTHESIS_STATES:
            result.fail(f"Hypotheses: '{row[0]}' has state '{row[3]}' (valid: {sorted(HYPOTHESIS_STATES - {'-'})})")
    open_count = sum(1 for row in hypotheses if len(row) >= 4 and row[3] in OPEN_HYPOTHESES)
    if open_count > OPEN_HYPOTHESES_CAP:
        result.fail(f"Hypotheses: {open_count} without a terminal state; the cap is {OPEN_HYPOTHESES_CAP} — a fourth enters only by a logged decision (D-<n>) that names what leaves, and what leaves goes to ## Deferred")

    for row in table_rows(sections.get("Facts that were once wrong", [])):
        if len(row) < 3 or not pointers_in([row[2]]):
            result.fail(f"Facts that were once wrong: '{row[0] if row else '?'}' has no producing notebook pointer")

    for line in sections.get("Deferred", []):
        if line.strip().startswith(("-", "*")) and not DEFERRED_ITEM.match(line):
            result.fail(f"Deferred: `{line.strip()[:60]}` must read `- YYYY-MM-DD: <idea> — enters when: <condition>`")

    last = sections.get("Last session", [])
    if not any(re.match(r"^\s*[-*]\s*\d{4}-\d{2}-\d{2}", l) for l in last):
        result.fail("Last session: no dated line (`- YYYY-MM-DD: ...`)")
    if not any(re.search(r"\bNext:", l) for l in last):
        result.fail("Last session: no `Next:` line")

    result.summary = f"{len(present)}/{len(SECTIONS)} sections, {pointer_count} pointers"
    return result, layout


# --- numbers -----------------------------------------------------------------------------
def interpretations(token: str) -> list[tuple[float, int]]:
    """All (value, decimals) readings of a token: 1,377 · 1.377 · 1,234.56 · 1.234,56 · 0,61 · 0.61.

    `1.377` is thousands in pt-BR and three decimals in English; both readings are returned and a
    match on either counts. A leading zero (`0.125`, `0,613`) is never thousands.
    """
    grouped = re.fullmatch(r"(\d{1,3})((?:[.,]\d{3})+)", token)
    if grouped:
        readings = []
        if not token.startswith("0"):
            readings.append((float(re.sub(r"[.,]", "", token)), 0))
        if grouped.group(2).count(".") + grouped.group(2).count(",") == 1:
            readings.append((float(token.replace(",", ".")), 3))
        return readings
    match = re.fullmatch(r"(\d{1,3}(?:[.,]\d{3})+)([.,])(\d+)", token)
    if match:
        integer = re.sub(r"[.,]", "", match.group(1))
        return [(float(f"{integer}.{match.group(3)}"), len(match.group(3)))]
    match = re.fullmatch(r"(\d+)[.,](\d+)", token)
    if match:
        return [(float(f"{match.group(1)}.{match.group(2)}"), len(match.group(2)))]
    return [(float(token), 0)]


def iter_files(root: Path, paths: list[str], suffixes: set[str]) -> list[Path]:
    files: list[Path] = []
    for p in paths:
        path = root / p
        if path.is_file() and path.suffix.lower() in suffixes:
            files.append(path)
        elif path.is_dir():
            files.extend(f for f in sorted(path.rglob("*")) if f.is_file() and f.suffix.lower() in suffixes)
    return files


def aggregate_values(files: list[Path]) -> list[float]:
    values: list[float] = []

    def walk(obj) -> None:
        if isinstance(obj, bool):
            return
        if isinstance(obj, (int, float)):
            values.append(float(obj))
        elif isinstance(obj, str):
            for token in NUMBER.findall(obj):
                values.extend(v for v, _ in interpretations(token))
        elif isinstance(obj, dict):
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for v in obj:
                walk(v)

    for file in files:
        text = file.read_text(encoding="utf-8", errors="replace")
        if file.suffix.lower() == ".json":
            try:
                walk(json.loads(text))
                continue
            except json.JSONDecodeError:
                pass
        # Delimited text: one cell at a time, so a value after a comma is still a value.
        for line in text.splitlines():
            for cell in re.split(r"[,;\t|]", line):
                cell = cell.strip().strip('"\'')
                if re.fullmatch(r"[-−]?\d[\d.,]*", cell):
                    sign = -1.0 if cell[0] in "-−" else 1.0
                    values.extend(sign * v for v, _ in interpretations(cell.lstrip("-−")))
    return values


class Matcher:
    def __init__(self, values: list[float]):
        self.values = values
        self.cache: dict[int, set[float]] = {}

    def rounded(self, decimals: int) -> set[float]:
        if decimals not in self.cache:
            self.cache[decimals] = {round(v, decimals) for v in self.values}
        return self.cache[decimals]

    def has(self, value: float, decimals: int) -> bool:
        return round(value, decimals) in self.rounded(decimals)


def sign_before(before: str) -> float:
    """-1 when a minus sign immediately precedes the number and is not a range dash between two numbers."""
    if before.endswith(("-", "−")) and not before[:-1].rstrip().endswith(tuple("0123456789")):
        return -1.0
    return 1.0


def is_identifier(line: str, start: int) -> bool:
    """`D-37`, `H-1`, `F10`: a letter (optionally with a hyphen) glued to the digits is a name, not a number."""
    return bool(re.search(r"[A-Za-z]-?$", line[:start]))


def check_numbers(root: Path, layout: dict[str, list[str]], min_int: int) -> Result:
    result = Result("numbers")
    documents = iter_files(root, layout.get("documents", []) + layout.get("_brief", []), DOC_SUFFIXES)
    aggregates = iter_files(root, layout.get("aggregates", []), AGGREGATE_SUFFIXES)
    if not documents or not aggregates:
        result.unverified(f"nothing to check: {len(documents)} document(s), {len(aggregates)} aggregate file(s) in Layout")
        return result
    matcher = Matcher(aggregate_values(aggregates))
    checked = 0
    markers = 0
    for doc in documents:
        fenced = False
        for lineno, raw in enumerate(doc.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if re.match(r"\s*(```|~~~)", raw):
                fenced = not fenced
                continue
            if fenced or raw.lstrip().startswith("#"):
                continue
            marker = IGNORE_MARK.search(raw)
            if marker:
                markers += 1
                if not marker.group(1):
                    result.fail(f"{doc.relative_to(root)}:{lineno}  rm:ignore without a reason — write `<!-- rm:ignore: <why this number has no aggregate> -->`")
                continue
            line = URL_OR_DOI.sub(" ", raw)
            for match in NUMBER.finditer(line):
                token = match.group(1)
                before = line[:match.start()]
                if is_identifier(line, match.start()):
                    continue
                readings = interpretations(token)
                if all(d == 0 and (v < min_int or (len(token) == 4 and 1900 <= v <= 2100)) for v, d in readings):
                    continue
                if THRESHOLD_BEFORE.search(before.rstrip("-−") if before.endswith(("-", "−")) else before) or LABEL_BEFORE.search(before) or LEGAL_BEFORE.search(before):
                    continue
                if CONFIDENCE_AFTER.match(line[match.end():]):
                    continue
                checked += 1
                sign = sign_before(before)
                percent = line[match.end():match.end() + 1] == "%"
                if any(matcher.has(sign * v, d) or (percent and matcher.has(sign * v / 100, d + 2)) for v, d in readings):
                    continue
                result.fail(f"{doc.relative_to(root)}:{lineno}  {token}")
    result.summary = (f"{checked} numbers in {len(documents)} document(s) against {len(aggregates)} aggregate file(s); "
                      f"{markers} rm:ignore marker(s)")
    return result


# --- disclosure --------------------------------------------------------------------------
def check_disclosure(root: Path, layout: dict[str, list[str]]) -> Result:
    """Anything under `documents` is outside the analysis environment: no count cell below the floor."""
    result = Result("disclosure")
    floor = layout.get("floor", [""])[0]
    if not floor.isdigit():
        result.unverified("no `floor: <n>` in Layout — the disclosure floor is not checked")
        return result
    floor_value = int(floor)
    files = iter_files(root, layout.get("documents", []), TABLE_SUFFIXES)
    if not files:
        result.unverified("nothing to check: no tables under documents")
        return result
    cells = 0
    for file in files:
        delimited = file.suffix.lower() in {".csv", ".tsv"}
        fenced = False
        for lineno, raw in enumerate(file.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if not delimited:
                if re.match(r"\s*(```|~~~)", raw):
                    fenced = not fenced
                    continue
                if fenced or not raw.lstrip().startswith("|") or IGNORE_MARK.search(raw):
                    continue
                row = [c.strip() for c in raw.strip().strip("|").split("|")]
            else:
                if IGNORE_MARK.search(raw):
                    continue
                row = [c.strip().strip('"\'') for c in re.split(r"[,;\t]", raw)]
            for cell in row[1:]:  # the first column labels the row
                if re.fullmatch(r"\d+", cell):
                    cells += 1
                    if 0 < int(cell) < floor_value:
                        result.fail(f"{file.relative_to(root)}:{lineno}  cell {cell} is below the floor of {floor_value}")
    result.summary = f"{cells} integer cell(s) in {len(files)} file(s) against floor {floor_value}"
    return result


# --- decisions ---------------------------------------------------------------------------
def check_decisions(root: Path, layout: dict[str, list[str]]) -> Result:
    result = Result("decisions")
    files = iter_files(root, layout.get("decisions", []), DOC_SUFFIXES)
    if not files:
        result.unverified("nothing to check: no decisions file in Layout")
        return result
    total = 0
    rows = 0
    for file in files:
        text = file.read_text(encoding="utf-8", errors="replace")
        rows += len(DECISION_ROW.findall(text))
        starts = list(DECISION_START.finditer(text))
        previous = 0
        seen: set[int] = set()
        for i, start in enumerate(starts):
            total += 1
            number = int(start.group(1))
            end = starts[i + 1].start() if i + 1 < len(starts) else len(text)
            block = text[start.start():end]
            label = f"{file.relative_to(root)}: D-{number}"
            if number in seen:
                result.fail(f"{label} appears twice")
            if number < previous:
                result.fail(f"{label} is out of order (after D-{previous}); the log is append-only")
            seen.add(number)
            previous = max(previous, number)
            revision = REVISION.search(block)
            if not revision:
                result.fail(f"{label} has no `Revision condition:`")
            elif revision.group(1).strip().strip("*").lower() in EMPTY_VALUES:
                result.fail(f"{label} has an empty `Revision condition:` — name the observation that would reopen it, or the decision is not revisable and says so")
            superseded = SUPERSEDES.search(block)
            if superseded and int(superseded.group(1)) not in seen - {number}:
                result.fail(f"{label} supersedes D-{superseded.group(1)}, which is not an earlier block in the log")
    if total == 0:
        result.unverified(f"nothing to check: no `### D-<n>` blocks in {len(files)} file(s)"
                          + (f"; {rows} decision id(s) live in table rows and were not checked" if rows else ""))
        return result
    result.summary = f"{total} decision block(s) in {len(files)} file(s)"
    if rows:
        result.unverified(f"{result.summary}; {rows} decision id(s) live in table rows, where a revision condition cannot be checked")
    return result


# --- citations ---------------------------------------------------------------------------
def probe(url: str, timeout: float = 10.0) -> tuple[str, int]:
    """('ok'|'refused'|'missing'|'unreachable', http status or 0)."""
    request = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "research-map-validate"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return ("ok", response.status)
    except urllib.error.HTTPError as exc:
        if exc.code < 400:
            return ("ok", exc.code)
        if exc.code in NETWORK_REFUSED:
            return ("refused", exc.code)
        return ("missing", exc.code)
    except (urllib.error.URLError, TimeoutError, OSError):
        return ("unreachable", 0)


def resolve_doi(doi: str) -> tuple[str, str]:
    """Crossref record first (the verifier phase 2 names), doi.org as fallback."""
    for url in (f"https://api.crossref.org/works/{doi}", f"https://doi.org/{doi}"):
        status, code = probe(url)
        if status == "ok":
            return ("ok", url)
        if status == "missing" and url.startswith("https://doi.org"):
            return ("missing", f"{url} (http {code})")
    return ("unverified", f"network refused or unreachable for {doi}")


def bib_entries(text: str) -> list[tuple[str, str, str]]:
    """(kind, key, body) for every bibliographic entry; @comment/@string/@preamble are skipped."""
    entries = []
    for chunk in re.split(r"(?m)^@", text)[1:]:
        head = re.match(r"(\w+)\s*\{\s*([^,\s]*)", chunk)
        if not head or head.group(1).lower() in {"comment", "string", "preamble"}:
            continue
        entries.append((head.group(1).lower(), head.group(2) or "?", chunk))
    return entries


def check_citations(root: Path, layout: dict[str, list[str]], offline: bool) -> Result:
    result = Result("citations")
    files = [root / p for p in layout.get("references", []) if (root / p).is_file()]
    if not files:
        result.unverified("nothing to check: no references file in Layout")
        return result
    dois: list[tuple[str, str]] = []
    urls: list[tuple[str, str]] = []
    sourced = 0
    for file in files:
        text = file.read_text(encoding="utf-8", errors="replace")
        rel = str(file.relative_to(root))
        if file.suffix.lower() == ".bib":
            for kind, key, body in bib_entries(text):
                doi = re.search(r"\bdoi\s*=\s*[{\"]\s*(?:https?://doi\.org/)?([^}\"\s]+)", body, re.I)
                url = re.search(r"\burl\s*=\s*[{\"]\s*([^}\"\s]+)", body, re.I)
                isbn = re.search(r"\bisbn\s*=\s*[{\"]\s*([^}\"\s]+)", body, re.I)
                if doi:
                    dois.append((f"{rel}:{key}", doi.group(1)))
                elif url:
                    urls.append((f"{rel}:{key}", url.group(1)))
                elif isbn and kind in {"book", "inbook", "incollection", "manual", "techreport"}:
                    sourced += 1  # a book is identified by its ISBN; nothing to resolve online
                else:
                    result.fail(f"{rel}: entry {key} has no doi, url or isbn")
        else:
            for doi in DOI.findall(text):
                dois.append((rel, doi.rstrip(".,;)")))
    targets = len(dois) + len(urls)
    if offline:
        result.unverified(f"{targets} target(s) not resolved (--offline); {sourced} book(s) by ISBN")
        return result
    unverified = 0
    for label, doi in dois:
        status, detail = resolve_doi(doi)
        if status == "missing":
            result.fail(f"{label}  {detail}")
        elif status == "unverified":
            unverified += 1
            result.lines.append(f"{label}  {detail}")
    for label, url in urls:
        status, code = probe(url)
        if status == "missing":
            result.fail(f"{label}  {url}  http {code}")
        elif status != "ok":
            unverified += 1
            result.lines.append(f"{label}  {url}  {status}")
    if unverified:
        result.unverified(f"{targets} target(s), {unverified} not verifiable from here; {sourced} book(s) by ISBN")
    else:
        result.summary = f"{targets} target(s) resolved; {sourced} book(s) by ISBN"
    return result


# --- notebooks ---------------------------------------------------------------------------
def check_notebooks(root: Path, layout: dict[str, list[str]]) -> Result:
    result = Result("notebooks")
    files = iter_files(root, layout.get("notebooks", []), {".ipynb"})
    if not files:
        result.unverified("nothing to check: no notebooks in Layout")
        return result
    for file in files:
        try:
            notebook = json.loads(file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            result.fail(f"{file.relative_to(root)}: invalid JSON ({exc})")
            continue
        for index, cell in enumerate(notebook.get("cells", [])):
            if cell.get("cell_type") != "code":
                continue
            if cell.get("outputs") or cell.get("execution_count") is not None:
                result.fail(f"{file.relative_to(root)}: cell {index} has outputs or an execution count; clear before committing")
    result.summary = f"{len(files)} notebook(s)"
    return result


# --- run ---------------------------------------------------------------------------------
def run(map_path: Path, root: Path, offline: bool, min_int: int, only: set[str] | None) -> list[Result]:
    text = map_path.read_text(encoding="utf-8")
    map_result, layout = check_map(text, root)
    results = [map_result]
    checks = {
        "numbers": lambda: check_numbers(root, layout, min_int),
        "decisions": lambda: check_decisions(root, layout),
        "disclosure": lambda: check_disclosure(root, layout),
        "citations": lambda: check_citations(root, layout, offline),
        "notebooks": lambda: check_notebooks(root, layout),
    }
    for name, check in checks.items():
        if only is None or name in only:
            results.append(check())
    if only is not None and "map" not in only:
        results = results[1:]
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a research repository against its RESEARCH.map.")
    parser.add_argument("map", nargs="?", default="RESEARCH.map")
    parser.add_argument("--root", help="repository root (default: the map's directory)")
    parser.add_argument("--offline", action="store_true", help="do not resolve citations; report NOT_VERIFIED")
    parser.add_argument("--strict", action="store_true", help="exit 1 on NOT_VERIFIED too")
    parser.add_argument("--min-int", type=int, default=20, help="integers below this are not checked (default 20)")
    parser.add_argument("--only", help="comma-separated subset: map,numbers,decisions,disclosure,citations,notebooks")
    args = parser.parse_args(argv)

    map_path = Path(args.map).resolve()
    if not map_path.is_file():
        print(f"research-map validate: {map_path} not found")
        return 1
    root = Path(args.root).resolve() if args.root else map_path.parent
    only = set(args.only.split(",")) if args.only else None
    results = run(map_path, root, args.offline, args.min_int, only)

    print(f"research-map validate — {root}")
    for r in results:
        print(f"{r.name:<11}{r.status:<14}{r.summary}")
        for line in r.lines:
            print(f"  {line}")
    failed = any(r.status == "FAIL" for r in results)
    unverified = any(r.status == "NOT_VERIFIED" for r in results)
    verdict = "FAIL" if failed else ("NOT_VERIFIED" if unverified else "PASS")
    print(f"RESULT {verdict}")
    return 1 if failed or (args.strict and unverified) else 0


if __name__ == "__main__":
    sys.exit(main())
