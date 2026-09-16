# Instructions for AI engineering agents

This repository is intended to outlive any single chat session. Treat the repository as the memory.

## Before changing architecture

Read, in order:

1. `SYSTEM.md`
2. `docs/architecture.md`
3. the relevant domain document under `docs/`
4. relevant ADRs under `docs/decisions/`
5. `docs/evaluation.md` and `docs/roadmap.md`

Do not reconstruct system intent from model memory when repository artifacts answer the question.

## Non-negotiable engineering rules

- Do not make a database, graph, vector store, MCP server or model provider the scientific source of truth.
- Do not require users or AI researchers to maintain PROV/P-Plan/RDF manually.
- Do not persist chain-of-thought or every exploratory idea. Persist scientific commitments, evidence, observations, decisions, results and material rejected/deferred alternatives.
- Do not allow model prose to create a scientific result. Results require execution or identified external evidence.
- Do not let an agent directly promote its own proposal to established knowledge without the owning control transition.
- Do not treat validator success as scientific truth.
- Do not add a mandatory field/gate/agent because it makes the architecture look complete. Name the failure mechanism it prevents.
- Do not load the entire project state into every model call. Retrieve the smallest scientifically relevant context.
- Prefer deterministic checks and executable evidence to prompt rules when the rule can be enforced mechanically.
- Preserve creative freedom in exploration; enforce rigor at commitment, exposure, plan change, claim and release boundaries.

## Change discipline

A change that modifies a system invariant or boundary requires an ADR. A superseding ADR must state what prior decision it replaces and why new evidence justifies the change.

Implementation choices that do not alter system semantics may be changed without ADR, but should remain testable and replaceable.

## Development strategy

Build vertical slices that demonstrate scientific capability end to end. Avoid building all infrastructure layers independently before a scientific workflow can run.

Every slice should answer:

- What scientific capability is now possible?
- What failure is prevented?
- What evidence demonstrates that?
- What did the change add to model/context overhead?

## Evaluation rule

When a new control is proposed, add or identify an evaluation case that would fail without it. When a new autonomous capability is proposed, add an evaluation that demonstrates useful scientific work, not only API correctness.