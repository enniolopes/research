# ADR 0003 — Separate world model from scientific ledger

**Status:** Accepted

## Decision

Maintain a compact active scientific world model separate from the complete durable ledger.

## Rationale

Long-horizon agents need persistent orientation, but loading full history into every context creates noise and cost. A small active state supports reasoning while the ledger preserves auditability.

## Consequences

- world-model entries reference ledger evidence;
- omission from the active model cannot delete historical evidence;
- retrieval is query/task scoped.