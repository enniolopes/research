# Research

A scientific operating system for AI-assisted empirical research.

Research is not a chatbot and not an ontology-first product. It is a persistent scientific control system that coordinates models, tools, evidence, execution, memory and adversarial review so that an AI can do real research over long horizons without silently turning speculation into evidence.

The public experience should remain simple: start with a research question, talk naturally, inspect status or the map when useful, and ask for review. Internally, the system owns scientific state transitions, execution provenance, control gates and durable memory.

## Status

This repository is at the architecture/foundation stage. Before runtime implementation, the architecture defines the **Research Protocol**: authoritative meanings, scientific commands/events, admission rules, failure/recovery semantics and the boundary between the control plane and scientific work plane.

The first implementation target is a **Minimum Scientific Loop**: start a real question, inspect evidence, form a hypothesis, commit and execute a test, challenge the result, admit or refuse a claim, restart from a fresh session, and recover the exact scientific state and lineage.

## Read first

- [`SYSTEM.md`](SYSTEM.md) — system constitution and invariants.
- [`AGENTS.md`](AGENTS.md) — rules for AI agents modifying this repository.
- [`docs/research-protocol.md`](docs/research-protocol.md) — semantic state, commands, events and admission contract.
- [`docs/architecture.md`](docs/architecture.md) — control/work planes, ownership and persistence boundaries.
- [`docs/scientific-model.md`](docs/scientific-model.md) — scientific behavior and control model.
- [`docs/failure-trust.md`](docs/failure-trust.md) — failure, concurrency, authority and data-egress semantics.
- [`docs/evaluation.md`](docs/evaluation.md) — scientific and architecture fitness evaluation.
- [`docs/roadmap.md`](docs/roadmap.md) — implementation sequence by vertical slices.
- [`docs/decisions/`](docs/decisions/) — architectural decision records.

## Baseline

The behavioral/scientific baseline is the `research` system v0.8.0 from `enniolopes/skills`. At project inception the repository was observed at commit `55072ae54384a9adca3f25b3f20336507e511de2`; the `scientific-method/SKILL.md` blob used during design was `1be34224d3b97035802baed5cebf7cd86bfbbe52`.

This repository turns those principles into a persistent runtime; it does not discard them.
