"""Disposable, version-aware projection. Edges are declared dependencies."""
from __future__ import annotations

from collections import deque

from contracts import digest
from resources import resolve


def key(project, value):
    return digest({"project_id": project, "kind": value["kind"], "logical_id": value["logical_id"],
                   "revision": value.get("revision", value.get("version_label")), "path": value.get("path", value.get("source_uri"))})


def build(store):
    nodes = {}
    edges = []
    def res(ref, owner):
        v = resolve(ref, owner, store.records)
        k = key(owner["project_id"], v)
        nodes[k] = {"id": k, **v}
        return k
    for rid, record in store.records.items():
        nodes[rid] = {"id": rid, "kind": record["schema_version"], "state": store.state(rid)[0]}
        if record["schema_version"] == "decision@1":
            target = res(record["target"]["resource_ref"], record)
            edges.append({"from": target, "to": rid, "relation": "formulation", "binding": record["target"]["binding"]})
            for route in record["basis"]["routes"]:
                route_id = rid + "#" + route["id"]
                nodes[route_id] = {"id": route_id, "kind": "declared_conjunctive_route"}
                edges.append({"from": route_id, "to": rid, "relation": "alternative_route"})
                for b in route["all_of"]:
                    edges.append({"from": res(b["resource_ref"], record), "to": route_id,
                                  "relation": "requires", "binding": b["binding"]})
            for pointer in record["judgments"]:
                edges.append({"from": pointer.split("#")[0], "to": rid, "relation": "examined_by"})
            for origin in record["basis"]["origin_refs"]:
                nodes.setdefault(origin, {"id": origin, "kind": "declared_origin"})
                edges.append({"from": origin, "to": rid, "relation": "shared_origin"})
        if record["schema_version"] == "review@1":
            for b in record["dependencies"]:
                edges.append({"from": res(b["resource_ref"], record), "to": rid,
                              "relation": "examined_dependency", "binding": b["binding"]})
        if record["schema_version"] == "release@1":
            for ref in record["resources"]:
                edges.append({"from": res(ref, record), "to": rid, "relation": "package_member"})
            for dependency in record["decision_refs"] + record["review_refs"] + record["authority_refs"]:
                edges.append({"from": dependency, "to": rid, "relation": "release_requires"})
        references = record.get("references", record.get("reference_set", []))
        if record["schema_version"] == "release@1":
            references = record["target"]["reference_set"]
        for pointer in references:
            edges.append({"from": pointer.split("#")[0], "to": rid, "relation": "reference_contract"})
        if record.get("supersedes"):
            edges.append({"from": record["supersedes"], "to": rid, "relation": "supersedes"})
    return {"effect": "checked", "version": 1, "nodes": [nodes[k] for k in sorted(nodes)],
            "edges": sorted(edges, key=lambda e: (e["from"], e["to"], e["relation"])),
            "limit": "Recorded candidate consequences only; no scientific validity or independence inferred."}


def affected(graph, start):
    ids = {n["id"] for n in graph["nodes"]}
    if start not in ids:
        from contracts import ContractError
        raise ContractError("unknown versioned graph node")
    adj = {}
    for e in graph["edges"]:
        if e["relation"] != "supersedes":
            adj.setdefault(e["from"], []).append(e["to"])
    seen = {start}
    queue = deque([start])
    while queue:
        for other in adj.get(queue.popleft(), []):
            if other not in seen:
                seen.add(other)
                queue.append(other)
    return {"effect": "checked", "affected_candidates": sorted(seen - {start}), "limit": graph["limit"]}
