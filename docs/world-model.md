# Scientific world model

## Purpose

The world model is the compact active projection needed for coherent reasoning across long projects. It is not the complete project history, not the semantic graph and not an independently editable source of truth.

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

Initial projection should stay small:

- quest / active problem;
- known findings with ledger evidence references;
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

## Projection rule

The world model is produced from accepted Research Protocol state and authoritative ledger references. Applications may cache/materialize it, but a direct write to the cache is not a scientific transition.

```text
authoritative artifacts + execution receipts + accepted control events
                              |
                              v
                       projection logic
                              |
                              v
                         world model
```

If the projection is deleted or corrupt, rebuild it from authoritative state. If reconstruction produces a different meaning from the cached model, authoritative state wins and the discrepancy is a defect to investigate.

## Three memory levels

### Working context

A still smaller task-scoped slice supplied to an orchestrator/worker. It contains only state relevant to the task and its controlled information set.

### Scientific ledger

Complete durable basis: scientific artifacts, execution evidence and accepted control events, plus referenced sources/outputs.

### Semantic/index layer

Derived relations and retrieval structures for trace, why, changed, map and argument. Loaded by query, not by default.

## Admission rule

Workers do not mutate accepted scientific belief or the world model directly. They submit typed observations/proposals with ledger references; Research Core validates the owning transition, appends the accepted event when appropriate, then updates projections.

## Compression rule

The world model is intentionally lossy. Omission may remove detail but may not reverse uncertainty, erase a material contradiction, erase a blocking commitment or rewrite history. Anything omitted remains recoverable from the ledger.
