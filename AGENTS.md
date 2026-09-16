# Instructions for AI engineering agents

This repository is intended to outlive any single chat session. Treat the repository as the memory.

## Before changing architecture or material runtime behavior

Read, in order:

1. `SYSTEM.md`
2. `docs/research-protocol.md`
3. `docs/architecture.md`
4. the relevant domain document under `docs/`
5. relevant ADRs under `docs/decisions/`
6. `docs/failure-trust.md`, `docs/evaluation.md` and `docs/roadmap.md`

Do not reconstruct system intent from model memory when repository artifacts answer the question.

## Document ownership

Avoid parallel prose truth:

- `SYSTEM.md` owns stable invariants;
- `docs/research-protocol.md` owns scientific state/command/event/admission semantics;
- domain docs own local operational contracts;
- `docs/architecture.md` owns boundaries, responsibilities and dependency direction;
- ADRs own why a material decision exists, assumptions, evidence expected and revision conditions;
- `docs/roadmap.md` owns sequence, not semantics.

Reference the owner instead of restating a rule unless local context requires a short summary.

## Non-negotiable engineering rules

- Preserve one authority per meaning. Do not make a projection, vector store, semantic graph, model response, MCP server or UI authoritative scientific state.
- Do not force Git to represent ephemeral orchestration state; use the correct Scientific Ledger authority for the meaning.
- Do not require users or AI researchers to maintain PROV/P-Plan/RDF manually.
- Do not persist chain-of-thought or every exploratory idea. Persist scientific commitments, evidence, observations, decisions, results and material rejected/deferred alternatives.
- Do not allow model prose to create a scientific result. Results require identified execution or identified external evidence.
- Workers return typed proposals/observations/evidence; only the Control Plane admits accepted state through the Research Protocol.
- Do not mutate the world model as independent truth; update accepted state, then project/reconcile the world model.
- Do not treat validator success as scientific truth.
- Do not add a mandatory field/gate/agent because architecture looks more complete. Name the failure mechanism it prevents.
- Do not load the whole project into every model call. Retrieve the smallest scientifically relevant context.
- Prefer deterministic checks and executable evidence to prompt rules when mechanically decidable.
- Preserve creative freedom in exploration; enforce rigor at commitment, exposure, plan change, claim and release boundaries.
- Commands that may retry must have identity/idempotency semantics; accepted transitions must reject stale target versions rather than silently race.
- Every task gets an explicit capability envelope for data, network, tools, credentials and model egress. Tool availability is not authorization.

## Change discipline

A change modifying a system invariant, semantic authority, state transition, trust boundary or material boundary requires an ADR. A superseding ADR states what it replaces and what evidence justifies revision.

Implementation choices that do not alter semantics may change without ADR but remain testable and replaceable.

## Development strategy

Build vertical slices demonstrating scientific capability end to end. The first slice is the Minimum Scientific Loop in `docs/roadmap.md`, not an infrastructure-only persistence milestone.

Every slice answers:

- What scientific capability is now possible?
- What failure is prevented?
- What evidence demonstrates that?
- What did the change add to model/context/runtime overhead?
- Which architecture assumption did reality support or challenge?

## Evaluation rule

For each material architecture decision, define either a falsifiable fitness test or explicitly human-judged property. A control is justified by observed failure reduction, not design elegance.
