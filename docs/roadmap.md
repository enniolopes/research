# Implementation roadmap

Build by vertical scientific slices. Do not implement every infrastructure subsystem independently before proving an end-to-end capability.

## Slice 0 — Foundation (this PR)

- system constitution;
- architectural boundaries;
- scientific/world-model definitions;
- agent/execution/evidence/provenance contracts;
- evaluation strategy;
- ADRs.

Exit: a future engineering session can reconstruct intent from the repository without this chat.

## Slice 1 — Persistent Scientist

Goal: prove long-horizon memory.

```text
init/open project
 -> create quest/problem
 -> persist minimal world model + event history
 -> close process/session
 -> reopen later
 -> return scientifically correct status and next action
```

Keep infrastructure minimal. Embedded persistence is acceptable if interfaces allow later deployment storage.

Primary eval: resume from a fresh AI session with no chat memory and preserve known/unknown/hypotheses/commitments/blockers correctly.

## Slice 2 — Evidence Scientist

Goal: ground scientific propositions in inspected sources.

Implement evidence tasks, source lifecycle, proposition-level support/challenge, contradiction and precedent search through replaceable source adapters.

## Slice 3 — Execution Scientist

Goal: make computed results execution products.

Implement isolated execution, run manifests, input/code/environment identities, outputs and basic reproducibility.

## Slice 4 — Scientific Control

Goal: enforce the high-consequence transitions from the research 0.8 baseline: commitment/freeze, exposure roles, plan-change routing, claim admission and invalid transitions.

## Slice 5 — Falsification

Goal: automatically challenge attractive results with applicable nulls/rivals and update the world model without narrative bias.

## Slice 6 — Adaptive discovery

Goal: use independent hypothesis/evidence branches, debate/evolution when valuable, and next-best-test selection without making multi-agent overhead permanent.

## Slice 7 — Semantic sidecar and research map

Compile PROV/P-Plan/research relations from existing artifacts and accepted state; expose trace/why/changed/argument/map. Mindmap is an on-demand projection.

## Slice 8 — Product surfaces and distributed operation

Harden web cockpit, MCP/API/CLI, deployable PostgreSQL/object storage, background scheduler and remote/local execution modes as evidence from prior slices requires.

## Release discipline

A slice is not complete because its API exists. It is complete when the corresponding scientific evaluation passes and the capability is demonstrable end to end.