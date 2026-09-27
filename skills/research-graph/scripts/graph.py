#!/usr/bin/env python3
"""Build/query a disposable epistemic graph from research artifacts. Standard library only."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import deque
from pathlib import Path

CLAIM = re.compile(
    r"<!--\s*claim:(C\d+)\s+inference:(I\d+)\s+result:(R\d+)(?:\s+decides:(H\d+))?\s*-->",
    re.I,
)
LABEL = re.compile(r"^\s*([^:]+):\s*(.*?)\s*$", re.M)
H_HEADING = re.compile(r"^##\s+(H\d+)\s*$", re.M)
ASSUMPTION_ROW = re.compile(r"^\|\s*(A\d+)\s*\|.*?\|\s*(K\d+)\s*\|\s*([^|]+?)\s*\|\s*$", re.M)
ID_TOKEN = re.compile(r"\b(?:H|E|T|A|K|R|I|C|SRC|DATA)\d+\b|\bRUN-\d+\b|\bD-\d+\b", re.I)


def add_node(nodes: dict[str, dict], node_id: str, kind: str, **meta) -> None:
    current = nodes.setdefault(node_id, {"id": node_id, "kind": kind})
    for key, value in meta.items():
        if value not in (None, "", []):
            current[key] = value


def add_edge(edges: set[tuple[str, str, str]], source: str, relation: str, target: str) -> None:
    edges.add((source, relation, target))


def layout_from_map(path: Path) -> dict[str, list[str]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"(?ms)^## Layout\s*$\n(.*?)(?=^## |\Z)", text)
    out: dict[str, list[str]] = {}
    if not match:
        return out
    for line in match.group(1).splitlines():
        m = re.match(r"^\s*[-*]\s*([a-z]+)\s*:\s*(.+)$", line)
        if m:
            out[m.group(1)] = [p.strip().strip("`") for p in m.group(2).split(",") if p.strip()]
    return out


def block_sections(text: str) -> list[tuple[str, str]]:
    matches = list(H_HEADING.finditer(text))
    blocks: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        blocks.append((match.group(1).upper(), text[match.end():end]))
    return blocks


def field(body: str, name: str) -> str:
    m = re.search(r"^\s*" + re.escape(name) + r"\s*:\s*(.*?)\s*$", body, re.I | re.M)
    return m.group(1).strip() if m else ""


def parse_plan(root: Path, nodes: dict[str, dict], edges: set[tuple[str, str, str]]) -> dict[str, dict]:
    path = root / "analysis-plan.md"
    index: dict[str, dict] = {}
    if not path.is_file():
        return index
    text = path.read_text(encoding="utf-8", errors="replace")
    for hypothesis, body in block_sections(text):
        estimand = field(body, "Estimand").upper()
        test = field(body, "Primary test").upper()
        mode = field(body, "Mode").lower()
        generated = field(body, "Generated from")
        add_node(nodes, hypothesis, "H", artifact="analysis-plan.md", mode=mode)
        if re.fullmatch(r"E\d+", estimand):
            add_node(nodes, estimand, "E", artifact="analysis-plan.md")
        if re.fullmatch(r"T\d+", test):
            add_node(nodes, test, "T", artifact="analysis-plan.md")
            add_edge(edges, test, "tests", hypothesis)
            if estimand:
                add_edge(edges, test, "estimates", estimand)
        generated_ids = []
        if generated and generated.lower() not in {"none", "n/a", "-", "—"}:
            generated_ids = [x.upper() for x in re.findall(r"DATA\d+", generated, re.I)]
            for data_id in generated_ids:
                add_node(nodes, data_id, "DATA")
                add_edge(edges, hypothesis, "generated_from", data_id)
        assumptions = []
        for assumption, check, action in ASSUMPTION_ROW.findall(body):
            assumption = assumption.upper()
            check = check.upper()
            action = action.strip()
            assumptions.append((assumption, check, action))
            add_node(nodes, assumption, "A", artifact="analysis-plan.md")
            add_node(nodes, check, "K", artifact="analysis-plan.md")
            if test:
                add_edge(edges, test, "requires", assumption)
            add_edge(edges, assumption, "checked_by", check)
            fallback = re.search(r"\b(T\d+)\b", action, re.I)
            if fallback and test:
                fallback_id = fallback.group(1).upper()
                add_node(nodes, fallback_id, "T", artifact="analysis-plan.md")
                add_edge(edges, test, "fallback_to", fallback_id)
        index[hypothesis] = {
            "estimand": estimand,
            "test": test,
            "mode": mode,
            "generated_from": generated_ids,
            "assumptions": assumptions,
        }
    return index


def parse_runs(root: Path, nodes: dict[str, dict], edges: set[tuple[str, str, str]]) -> tuple[dict[str, dict], dict[str, dict]]:
    run_index: dict[str, dict] = {}
    result_index: dict[str, dict] = {}
    run_dir = root / ".research" / "runs"
    if not run_dir.is_dir():
        return run_index, result_index
    for path in sorted(run_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        run_id = str(data.get("id", "")).upper()
        if not re.fullmatch(r"RUN-\d+", run_id):
            continue
        hypothesis = str(data.get("hypothesis", "")).upper()
        estimand = str(data.get("estimand", "")).upper()
        test = str(data.get("test", "")).upper()
        add_node(nodes, run_id, "RUN", artifact=str(path.relative_to(root)), mode=data.get("mode"), commit=data.get("commit"))
        if test:
            add_node(nodes, test, "T")
            add_edge(edges, test, "executed_as", run_id)
        if hypothesis:
            add_node(nodes, hypothesis, "H")
            add_edge(edges, run_id, "tests", hypothesis)
        if estimand:
            add_node(nodes, estimand, "E")
            add_edge(edges, run_id, "estimates", estimand)
        for input_item in data.get("inputs", []):
            if isinstance(input_item, str):
                data_id, data_path, role = "", input_item, ""
            elif isinstance(input_item, dict):
                data_id = str(input_item.get("id", "")).upper()
                data_path = str(input_item.get("path", ""))
                role = str(input_item.get("role", ""))
            else:
                continue
            if re.fullmatch(r"DATA\d+", data_id):
                add_node(nodes, data_id, "DATA", path=data_path, role=role)
                add_edge(edges, run_id, "uses", data_id)
        for output in data.get("outputs", []):
            if not isinstance(output, dict):
                continue
            result = str(output.get("result", "")).upper()
            artifact = str(output.get("artifact", ""))
            if not re.fullmatch(r"R\d+", result):
                continue
            add_node(nodes, result, "R", artifact=artifact)
            add_edge(edges, run_id, "produces", result)
            result_index[result] = {"run": run_id, "test": test, "hypothesis": hypothesis, "estimand": estimand, "artifact": artifact}
        run_index[run_id] = data
    return run_index, result_index


def document_files(root: Path, layout: dict[str, list[str]]) -> list[Path]:
    suffixes = {".md", ".qmd", ".rmd", ".tex", ".txt"}
    files: list[Path] = []
    for item in layout.get("documents", []):
        path = root / item
        if path.is_file() and path.suffix.lower() in suffixes:
            files.append(path)
        elif path.is_dir():
            files.extend(p for p in sorted(path.rglob("*")) if p.is_file() and p.suffix.lower() in suffixes)
    return files


def parse_claims(root: Path, layout: dict[str, list[str]], nodes: dict[str, dict], edges: set[tuple[str, str, str]], result_index: dict[str, dict]) -> None:
    for path in document_files(root, layout):
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in CLAIM.finditer(text):
            claim, inference, result, decides = [x.upper() if x else "" for x in match.groups()]
            rel = str(path.relative_to(root))
            add_node(nodes, claim, "C", artifact=rel, decides=decides or None)
            add_node(nodes, inference, "I", artifact=rel)
            add_node(nodes, result, "R")
            add_edge(edges, result, "supports", inference)
            add_edge(edges, inference, "supports", claim)
            # H/E are reached through the executed test, not derived from its
            # interpretation. The latter creates a false circular warrant.


def parse_sources(root: Path, layout: dict[str, list[str]], nodes: dict[str, dict]) -> None:
    for item in layout.get("references", []):
        path = root / item
        if not path.is_file() or path.suffix.lower() != ".bib":
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in re.finditer(r"(?m)^@\w+\s*\{\s*([^,\s]+)", text):
            key = match.group(1)
            stable = "SRC" + str(len([n for n in nodes if n.startswith("SRC")]) + 1)
            add_node(nodes, stable, "SRC", key=key, artifact=str(path.relative_to(root)))


def build(map_path: Path) -> dict:
    map_path = map_path.resolve()
    root = map_path.parent
    layout = layout_from_map(map_path)
    nodes: dict[str, dict] = {}
    edges: set[tuple[str, str, str]] = set()
    parse_plan(root, nodes, edges)
    _, result_index = parse_runs(root, nodes, edges)
    parse_claims(root, layout, nodes, edges, result_index)
    parse_sources(root, layout, nodes)
    return {
        "version": 1,
        "nodes": [nodes[key] for key in sorted(nodes)],
        "edges": [
            {"from": source, "relation": relation, "to": target}
            for source, relation, target in sorted(edges)
        ],
    }


def graph_path(map_path: Path) -> Path:
    return map_path.resolve().parent / ".research" / "graph.json"


def save_graph(map_path: Path, graph: dict) -> Path:
    path = graph_path(map_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(graph, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def load_or_build(map_path: Path) -> dict:
    return build(map_path)


def adjacency(graph: dict, reverse: bool = False, relations: set[str] | None = None) -> dict[str, list[tuple[str, str]]]:
    out: dict[str, list[tuple[str, str]]] = {}
    for edge in graph.get("edges", []):
        relation = edge["relation"]
        if relations and relation not in relations:
            continue
        source, target = edge["from"], edge["to"]
        if reverse:
            source, target = target, source
        out.setdefault(source, []).append((relation, target))
    for key in out:
        out[key].sort()
    return out


def dependency_graph(graph: dict) -> dict:
    """Project relation semantics to prerequisite -> potential consequence.

    A fallback is an alternative, not evidence that it was executed. Do not
    propagate through it or through mere co-occurrence/source bibliography.
    This is navigation over recorded artifacts, never truth propagation.
    """
    forward = {"supports", "challenges", "produces", "executed_as"}
    inverse = {
        "uses": "used_by",
        "requires": "required_by",
        "checked_by": "checks",
        "generated_from": "generated",
        "tests": "tested_by",
        "estimates": "estimated_by",
        "derived_from": "basis_for",
    }
    edges = []
    for edge in graph.get("edges", []):
        relation = edge["relation"]
        if relation in forward:
            edges.append(edge)
        elif relation in inverse:
            edges.append({"from": edge["to"], "relation": inverse[relation], "to": edge["from"]})
    return {**graph, "edges": edges}


def walk(graph: dict, start: str, reverse: bool, relations: set[str] | None = None, max_depth: int | None = None) -> list[str]:
    adj = adjacency(graph, reverse=reverse, relations=relations)
    lines: list[str] = []
    seen = {start}
    queue = deque([(start, 0)])
    while queue:
        node, depth = queue.popleft()
        if max_depth is not None and depth >= max_depth:
            continue
        for relation, other in adj.get(node, []):
            connector = f"<--{relation}--" if reverse else f"--{relation}-->"
            lines.append(f"{'  ' * depth}{node} {connector} {other}")
            if other not in seen:
                seen.add(other)
                queue.append((other, depth + 1))
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build and query the derived research epistemic graph.")
    parser.add_argument("command", choices=["build", "trace", "argument", "why", "changed"])
    parser.add_argument("node", nargs="?", help="node id for a query")
    parser.add_argument("map", nargs="?", default="RESEARCH.map")
    args = parser.parse_args(argv)

    if args.command == "build" and args.node and args.node.endswith(".map") and args.map == "RESEARCH.map":
        args.map, args.node = args.node, None
    map_path = Path(args.map)
    if not map_path.is_file():
        print(f"research-graph: {map_path} not found")
        return 1
    graph = load_or_build(map_path)

    if args.command == "build":
        path = save_graph(map_path, graph)
        print(f"research-graph: {len(graph['nodes'])} nodes, {len(graph['edges'])} edges -> {path}")
        return 0

    if not args.node:
        parser.error(f"{args.command} requires NODE")
    node = args.node.upper()
    known = {n["id"] for n in graph.get("nodes", [])}
    if node not in known:
        print(f"research-graph: unknown node {node}")
        return 1

    if args.command in {"trace", "why"}:
        lines = walk(dependency_graph(graph), node, reverse=True)
    elif args.command == "changed":
        lines = walk(dependency_graph(graph), node, reverse=False)
        print("Potential consequences only; inspect each inference and surviving support. "
              "Current recorded relations may omit dependencies; verify historical run plans separately.")
    else:
        incoming = walk(graph, node, reverse=True, relations={"supports", "challenges"}, max_depth=2)
        outgoing = walk(graph, node, reverse=False, relations={"supports", "challenges"}, max_depth=2)
        lines = incoming + outgoing
    print("\n".join(lines) if lines else f"{node}: no matching relations")
    return 0


if __name__ == "__main__":
    sys.exit(main())
