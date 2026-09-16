# Scientific world model

## Purpose

The world model is the compact active scientific state needed for coherent reasoning across long projects. It is not the complete project history and not a dump of the semantic graph.

It should answer quickly:

- What are we trying to resolve?
- What do we currently know and why?
- What remains uncertain or contradicted?
- Which hypotheses are live, weakened, deferred or closed?
- What anomaly is currently unexplained?
- What commitments constrain the next action?
- What is the highest-value next test?
- What claims are currently permitted or forbidden?

## Minimal conceptual fields

Initial implementation should stay small:

- quest / active problem;
- known findings with evidence references;
- open questions;
- active hypotheses and rivals;
- strongest support and strongest challenge per active hypothesis;
- unexplained anomalies;
- current commitments;
- pending tests;
- recommended next test with rationale;
- permitted/forbidden material claims;
- blockers.

Do not add fields merely to mirror an ontology.

## Three memory levels

### Working model

Small context supplied to the orchestrator/worker. It should contain only the state relevant to the current task.

### Scientific ledger

Complete durable record: protocols, plans, decisions, sources, inspected evidence, data identities, runs, results, checks, claims and reviews.

### Semantic/index layer

Derived relations and retrieval structures used for queries such as trace, why, changed, map and argument. Loaded by query, not by default.

## Admission rule

Workers do not mutate accepted scientific belief directly. They submit typed observations/proposals with evidence references. Research Core validates the owning transition and then updates the active model and durable records.

This boundary prevents a persuasive generator from treating its own narrative as established state.

## Compression rule

The world model is a lossy operational projection. Anything omitted from it must remain recoverable from the ledger. Compression may remove detail but may not reverse uncertainty, erase material contradiction or rewrite history.