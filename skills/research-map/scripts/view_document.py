"""Read a supplied manuscript and optional separate review without interpreting evidence.

A UTF-8 text review can bind to one manuscript with a first nonblank line
`Document-SHA256: <64 hex digits>`. The digest covers the exact manuscript
bytes. Further binding declarations make the target ambiguous.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

from epistemic import CLAIM
from validate import pointers_in, slug


HEADING = re.compile(r"^ {0,3}#{1,6}\s+(.+?)(?:\s+#+)?\s*$")
ANCHOR = re.compile(r"\s+\{#([\w.-]+)\}\s*$")
FIELD = re.compile(r"^\s*(?:[-*]\s+)?([^:]{1,60}):(.*)$")
BINDING = re.compile(r"Document-SHA256:\s*([0-9a-f]{64})", re.I)
PAGE = re.compile(r"^\s*(?:[-*]\s+)?(?:Page|Página|p\.)\s+(\d+)\s*[:—–-]", re.I)
DESTINATION = r"(?:<([^>\n]+)>|([^\s)>]+))"
INLINE_LINK = re.compile(r"\]\(\s*" + DESTINATION)
REFERENCE_LINK = re.compile(r"^ {0,3}\[([^\]]+)\]:\s*" + DESTINATION)
LABELS = {
    "question": ("research question", "question", "questão", "pergunta", "pergunta de pesquisa"),
    "claim": ("claim", "conclusion", "conclusions", "afirmação", "conclusão", "conclusões"),
    "method": ("method", "methods", "methodology", "design", "study design", "método", "métodos",
               "metodologia", "desenho", "desenho do estudo"),
    "hypothesis": ("hypothesis", "hypotheses", "hipótese", "hipóteses"),
    "uncertainty": ("uncertainty", "uncertainties", "main uncertainty", "decisive uncertainty",
                    "incerteza", "incertezas", "incerteza principal", "incerteza decisiva"),
    "next_action": ("next action", "next step", "próxima ação", "próximo passo"),
}
KINDS = {label: kind for kind, labels in LABELS.items() for label in labels}


def field_kind(label):
    if re.fullmatch(r"C\d+", label, re.I):
        return "claim"
    if re.fullmatch(r"H\d+", label, re.I):
        return "hypothesis"
    return KINDS.get(label.casefold())


class Source:
    def __init__(self, path, content, namespace):
        self.path = path
        self.name = path.name
        self.version = hashlib.sha256(content).hexdigest()
        origin = hashlib.sha256(os.fsencode(path.absolute())).hexdigest()
        self.prefix = f"{namespace}:{origin}:{self.version}"
        self.content = content

    def entry(self, kind, label, locator, *, text="", aliases=(), **details):
        return dict(kind=kind, label=label, source=self.name, version=self.version,
                    selector=f"{self.prefix}#{locator}", locator=locator,
                    aliases=list(aliases), related=[], text=text, details=details)

    def lines(self):
        if (Path(self.name).suffix.lower() == ".pdf" or self.content.startswith(b"%PDF-")
                or b"\0" in self.content):
            return None
        try:
            return self.content.decode("utf-8-sig").splitlines()
        except UnicodeDecodeError:
            return None


def read_source(reader, path, namespace):
    try:
        if reader.permits(path):
            return Source(path, reader.read(path), namespace)
    except OSError:
        pass
    reader.partial(f"The supplied {namespace} is unavailable for this read.")
    return None


def prose_lines(lines):
    """Mask fenced examples without moving original source line numbers."""
    fence = ""
    for line in lines:
        if marker := re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line):
            if not fence:
                fence = marker[1]
            elif marker[1].startswith(fence) and not marker[2].strip():
                fence = ""
            yield ""
            continue
        yield "" if fence else line


def visible_lines(reader, source, lines):
    """Clear recognized citation origins before deriving labels, excerpts or page aliases."""
    if reader.audience != "model" or not lines:
        return lines, False
    roots = reader.policy_roots(source.path)
    definitions = {}
    boundaries = {0, len(lines)}
    headings = [i for i, line in enumerate(lines) if HEADING.match(line)]
    boundaries.update(headings or [i for i, line in enumerate(lines)
                                   if (m := FIELD.match(line)) and field_kind(m[1].strip("*_ "))])
    for index, line in enumerate(lines):
        if definition := REFERENCE_LINK.match(line):
            label = " ".join(definition[1].split()).casefold()
            definitions.setdefault(label, []).append(definition[2] or definition[3])
            boundaries.update((index, index + 1))

    ordered = sorted(boundaries)
    filtered = list(lines)
    withheld = False
    for start, end in zip(ordered, ordered[1:]):
        block = lines[start:end]
        text = "\n".join(block)
        # A standalone document supplies no native receipt or verified result origin.
        unresolved = bool(roots and CLAIM.search(text))
        targets = [(m[1] or m[2], [source.path.parent]) for m in INLINE_LINK.finditer(text)]
        for label in re.findall(r"\[([^\]]+)\]", text):
            key = " ".join(label.split()).casefold()
            targets.extend((target, [source.path.parent]) for target in definitions.get(key, ()))
        targets.extend((name, roots or [source.path.parent]) for name in pointers_in(block))
        for target, bases in targets:
            try:
                uri = urlsplit(target)
                if uri.scheme and uri.scheme != "file":
                    continue
                path = unquote(uri.path)
                if path and not all(reader.permits(base / path) for base in bases):
                    unresolved = True
            except (OSError, ValueError):
                unresolved = True
        if unresolved:
            filtered[start:end] = [""] * (end - start)
            withheld = True
    if withheld:
        reader.partial("Documentary material with unresolved or restricted origins was withheld.")
    return filtered, withheld


def document_entries(source, lines):
    """Index explicit source structure. Source prose is never a reviewer verdict."""
    blocks = []
    for index, line in enumerate(lines):
        locator = f"L{index + 1}"
        if match := HEADING.match(line):
            heading = match[1].strip()
            explicit = ANCHOR.search(heading)
            title = heading[:explicit.start()].rstrip() if explicit else heading
            blocks.append((index, title, explicit[1] if explicit else slug(title), None))
        elif match := FIELD.match(line):
            raw_field, value = match.groups()
            field = raw_field.strip("*_ ")
            kind = field_kind(field)
            if kind and not (kind == "claim" and CLAIM.search(line)):
                # Markdown permits the colon inside or outside the emphasized label.
                emphasis = raw_field[:2]
                if emphasis in {"**", "__"} and not raw_field.endswith(emphasis):
                    value = value.removeprefix(emphasis)
                blocks.append((index, field, slug(field), value.strip() or None))
        for annotation in CLAIM.finditer(line):
            claim, _, result, decides = annotation.groups()
            excerpt = line[:annotation.start()].rsplit("-->", 1)[-1].strip()
            if not excerpt and index and "-->" not in lines[index - 1]:
                excerpt = lines[index - 1].strip()
            yield source.entry("claim", f"Author — {claim.upper()}", f"{locator}:{annotation.start() + 1}",
                               text=excerpt, aliases=[claim.upper()], basis="author annotation",
                               reported_result=result.upper(), reported_hypothesis=decides or None)
    for position, (index, title, anchor, value) in enumerate(blocks):
        end = blocks[position + 1][0] if position + 1 < len(blocks) else len(lines)
        text = value if value is not None else "\n".join(lines[index + 1:end]).strip()
        kind = field_kind(title) or "document"
        aliases = [f"{source.name}#{anchor}", anchor]
        if re.fullmatch(r"[CH]\d+", title, re.I) and title.upper() not in aliases:
            aliases.append(title.upper())
        yield source.entry(kind, f"Author — {title}", f"L{index + 1}", text=text,
                           aliases=aliases, basis="author-reported text")


def review_entry(reader, report, document):
    lines = report.lines()
    if not lines or not any(line.strip() for line in lines):
        reader.partial("The supplied review has no usable UTF-8 text.")
        return None
    first = next(i for i, line in enumerate(lines) if line.strip())
    declarations = [i for i, line in enumerate(lines) if line.strip().lower().startswith("document-sha256:")]
    match = BINDING.fullmatch(lines[first].strip())
    digest = match[1].lower() if match and declarations == [first] else None
    if digest == document.version:
        binding = "matched"
    elif digest:
        binding = "stale"
        reader.partial("The review identifies different document bytes.")
    else:
        binding = "unbound"
        reader.partial("The review does not identify a single verifiable document version.")
    if binding != "matched" and reader.audience == "model":
        # Quotations may originate in a different document with a different policy.
        reader.partial("Review excerpts were withheld because their document version could not be established.")
        return None
    start = first + 1 if digest else first
    cleared, _ = visible_lines(reader, report, lines[start:])
    body = "\n".join(cleared).strip()
    if not body:
        reader.partial("The review provides no assessment text.")
    pages = list(dict.fromkeys(match[1] for line in cleared if (match := PAGE.match(line))))
    aliases = [report.name]
    if binding == "matched":
        aliases.extend(f"{document.name}#page={page}" for page in pages)
    return report.entry("review", f"Reviewer report ({binding} document binding)", "report",
                        aliases=aliases, text=body, basis="external reviewer report",
                        binding=binding, scope="document", declared_document_sha256=digest,
                        reported_document_locators=[f"page {page}" for page in pages])


def collect(reader, document, review=None):
    document = Path(document)
    source = read_source(reader, document, "document")
    if source is None:
        # A permitted review can contain quotations copied from the withheld manuscript.
        return []
    item = source.entry("document", "External manuscript", "file", aliases=[source.name],
                        basis="supplied document bytes")
    entries = [item]
    lines = source.lines()
    withheld = False
    if lines is not None:
        cleared, withheld = visible_lines(reader, source, lines)
        lines = [line if allowed else "" for line, allowed in zip(prose_lines(lines), cleared)]
    if lines is None or not any(line.strip() for line in lines):
        reader.partial("Document text is unavailable; inspect the source for locators and passages.")
    else:
        excerpts = list(document_entries(source, lines))
        entries.extend(excerpts)
        item["related"].extend(e["selector"] for e in excerpts)
        if not excerpts:
            item["text"] = "\n".join(lines).strip()
    if review is None:
        item["details"]["review"] = "No separate review supplied."
        return entries
    if withheld:
        # A report about this manuscript can quote a withheld passage without repeating its citation.
        reader.partial("The supplied review may quote withheld manuscript material.")
        return entries
    review = Path(review)
    report = read_source(reader, review, "review")
    if report:
        if source.version == report.version:
            reader.partial("A review must be supplied as a separate document.")
        elif finding := review_entry(reader, report, source):
            entries.append(finding)
            if finding["details"]["binding"] == "matched":
                item["related"].append(finding["selector"])
                item["context"] = [finding["selector"]]
    return entries
