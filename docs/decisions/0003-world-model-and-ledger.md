# ADR 0003 — World model is a derived active projection

**Status:** Accepted

## Context and drivers

Long-horizon agents need a small current orientation, but the complete scientific history is too large/noisy for every model call. A mutable summary can drift or erase contradiction if treated as truth.

## Alternatives considered

- Load the complete ledger into each model context.
- Maintain the world model as an independently editable authoritative record.
- Derive/materialize a compact world model from accepted ledger state.

## Decision

Maintain a compact active world model as a **derived projection** of authoritative Scientific Ledger state. It may be materialized/cached for speed, but accepted scientific changes occur through Research Protocol transitions, not direct world-model mutation.

## Properties favored

Bounded context, long-horizon coherence, rebuildability, auditability and contradiction preservation.

## Costs / properties sacrificed

Projection logic must be deterministic enough to reconcile and may require explicit compression policies.

## Assumptions

A useful compact projection can preserve material uncertainties, contradictions, commitments and blockers while omitting recoverable detail.

## Enforcement

World-model write APIs are internal projection operations; worker/client APIs submit commands/proposals instead. A rebuild path must exist.

## Evidence expected

Deleting the materialized world model and rebuilding it from ledger state yields semantically equivalent orientation; ledger growth does not force unbounded default model context; material contradiction/blockers survive compression.

## Revise when

Projection cannot reliably preserve the minimum scientific state, rebuild cost becomes operationally unacceptable, or evidence shows a different memory hierarchy improves scientific efficacy without creating parallel truth.

## Authority

System architecture; changes require an A2 review and superseding ADR.

## Consequences

Omission from the world model never deletes historical evidence; retrieval remains task/query scoped.
