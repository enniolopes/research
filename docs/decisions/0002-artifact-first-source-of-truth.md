# ADR 0002 — One authority per scientific meaning

**Status:** Accepted

## Context and drivers

Research needs human-auditable, diffable scientific commitments while also recording runtime facts that do not naturally belong in Git, such as accepted transitions, exposures and execution outcomes. Treating either Git or a mutable operational database as universal truth creates an inappropriate coupling or parallel truth.

## Alternatives considered

- Git/filesystem is authoritative for every kind of state.
- Database is authoritative for every kind of state.
- Multiple stores may independently represent the same meaning.
- Assign one authoritative representation per meaning under a unified Scientific Ledger.

## Decision

Use a unified **Scientific Ledger** with one authority per meaning:

- Git-versioned artifacts: protocols, plans, decisions, code and authored scientific commitments;
- immutable execution receipts/outputs: what actually ran and what it produced;
- append-only accepted control events: material transitions, exposure, approvals, rejections, supersessions and task outcomes affecting scientific state.

World models, current-state tables, graphs, embeddings and UI are projections/indexes.

## Properties favored

Auditability, reconstructability, correct state ownership, inspectability, local-first operation and freedom to rebuild indexes.

## Costs / properties sacrificed

The system must reconcile references across multiple persistence forms and cannot answer every query from one storage primitive.

## Assumptions

Scientific artifacts remain valuable human/audit surfaces; runtime transition facts need transactional durability; the number of authoritative classes can remain small.

## Enforcement

Protocol/domain types identify which authority owns each record. Projection code never writes back scientific meaning without a validated command. Architecture tests should reject a new second authority for an existing meaning.

## Evidence expected

The Minimum Scientific Loop can delete/rebuild projections and recover identical accepted meaning from authoritative ledger records. A crash between work completion and admission cannot produce a claim/result without its durable receipt/event.

## Revise when

A required scientific meaning cannot be assigned unambiguously to one authority; cross-store atomicity makes correct operation impractical; or evidence shows one authority class is unnecessary/redundant.

## Authority

System architecture; changes require an A2 review and superseding ADR.

## Consequences

Git is not forced to act as a transactional queue, and a database is not allowed to replace inspectable scientific artifacts or immutable execution evidence.
