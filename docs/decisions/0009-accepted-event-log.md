# ADR 0009 — Accepted control transitions are append-only events

**Status:** Accepted

## Context and drivers

Research needs exact history for admission, exposure, supersession, crash recovery and `why/changed` queries. Mutable current-state rows alone lose causal history; storing every orchestration detail in Git is inappropriate.

## Alternatives considered

- Store only mutable current state.
- Commit every transition as a Git artifact.
- Record accepted material control transitions in an append-only event log and derive current projections.

## Decision

Every accepted Research Protocol transition produces an append-only durable domain event referencing its command, prior/new state version, targets, authority basis and required evidence/receipts. Current state/world model/task views are projections.

This is a semantic pattern, not a commitment to a specialized event-sourcing framework or broker.

## Properties favored

Auditability, recovery, causal trace, deterministic conflict detection and rebuildable projections.

## Costs / properties sacrificed

Projection/replay logic and event schema evolution become critical implementation concerns.

## Assumptions

The volume is manageable in ordinary local SQL initially; accepted material transitions are sufficiently discrete to record without logging chain-of-thought or every tool action.

## Enforcement

State-changing admission occurs transactionally with event append/version advance. Projection writes cannot substitute for an event. Events are immutable; correction uses a superseding/new event.

## Evidence expected

Projection deletion/rebuild preserves accepted state; retry does not duplicate accepted meaning; stale concurrent commands conflict; crash tests cannot produce admitted state without a corresponding event.

## Revise when

Replay/schema evolution becomes disproportionate, accepted transitions cannot be defined with stable semantics, or another mechanism provides equivalent audit/recovery with lower measured cost.

## Authority

System architecture; changes require an A2 review and superseding ADR.

## Consequences

Current-state storage is disposable/repairable. Event identity/versioning become part of the Research Protocol.
