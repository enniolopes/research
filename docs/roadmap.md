# Implementation roadmap

Build by vertical scientific slices. Do not implement infrastructure subsystems independently before proving an end-to-end scientific capability.

## Slice 0 — Foundation (this PR)

- system constitution;
- Research Protocol and authority matrix;
- control-plane/work-plane boundary;
- world-model projection contract;
- failure/concurrency/trust semantics;
- agent/execution/evidence/provenance contracts;
- evaluation strategy and ADRs.

Exit: a future engineering session can reconstruct system intent and critical semantics without this chat; no unresolved A2 decision blocks the first bounded implementation slice.

## Slice 1 — Minimum Scientific Loop

Goal: prove the architecture can do a small piece of science and survive process/session loss.

```text
start quest
 -> inspect one real evidence item
 -> form H1 (and rival when applicable)
 -> commit T1
 -> execute one real analysis
 -> produce R1
 -> record check/challenge
 -> admit or reject I1/C1
 -> stop process/session
 -> restart with no chat memory
 -> recover exact accepted state
 -> answer WHY C1 (or why it was rejected)
```

Use the smallest implementation capable of proving the semantic boundaries. SQLite + filesystem/Git is preferred unless evidence requires more. No web UI, distributed scheduler, graph database or multi-agent swarm is required.

Primary eval: `docs/evaluation.md#minimum-scientific-loop-acceptance`.

## Slice 2 — Evidence depth

Goal: make literature/external knowledge investigation robust.

Add source adapters, query decomposition, source lifecycle, proposition-level support/challenge, contradiction search, scoped precedent/novelty search and evidence-quality checks. Preserve Research Protocol semantics rather than creating a separate evidence truth system.

## Slice 3 — Execution and reproducibility depth

Goal: harden scientific computation.

Add isolated execution, environment/input/code identities, output hashing, worktrees/sandboxes, reproducibility reruns, richer checks and repair/reconciliation paths.

## Slice 4 — Scientific control completeness

Goal: enforce the full high-consequence transition set inherited from Research 0.8: exposure roles, freeze semantics, post-freeze plan-change routing, claim classes/boundaries where evaluations justify them, stale-evidence handling and release/review transitions.

## Slice 5 — Falsification

Goal: automatically challenge attractive results with applicable nulls/rivals, implementation checks and adversarial reanalysis, updating accepted state without narrative bias.

## Slice 6 — Adaptive discovery

Goal: use independent hypothesis/evidence branches, debate/evolution and next-best-test selection where valuable. Introduce concurrency only with the conflict/idempotency semantics already proven by earlier slices.

## Slice 7 — Semantic sidecar and research map

Compile PROV/P-Plan/research relations from authoritative artifacts, receipts and accepted events; expose trace/why/changed/argument/map. Mindmap remains an on-demand projection.

## Slice 8 — Product surfaces and distributed operation

Harden web cockpit, MCP/API/CLI, deployable PostgreSQL/object storage, background scheduler, remote/local execution planes and collaboration only as evidence from prior slices requires.

## Release discipline

A slice is not complete because its API exists. It is complete when its scientific evaluation passes, architecture fitness evidence is recorded, failure/recovery behavior is demonstrated for its scope, and the capability works end to end.
