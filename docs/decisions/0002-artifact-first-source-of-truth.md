# ADR 0002 — Artifact-first scientific source of record

**Status:** Accepted

## Decision

Keep human-readable, Git-versioned scientific artifacts and immutable execution evidence authoritative. Operational databases and graphs are indexes/state machines around them, not replacements for them.

## Rationale

Artifacts are inspectable, diffable, reproducible and independent of a running service. They preserve scientific history and allow external audit.

## Consequences

- important scientific state changes must have durable evidence;
- derived indexes should be rebuildable;
- database convenience must not make repository evidence optional.