# ADR 0010 — Implement a Minimum Scientific Loop before subsystem depth

**Status:** Accepted

## Context and drivers

The initial roadmap separated persistence, evidence and execution into sequential slices. Each could pass in isolation while failing to prove that the architectural boundaries compose into real scientific work. Building infrastructure first risks discovering semantic errors only after significant investment.

## Alternatives considered

- Implement persistence/world model first, then evidence, then execution and control.
- Build all infrastructure layers before scientific workflow.
- Implement the smallest end-to-end scientific loop first, then deepen each subsystem.

## Decision

The first runtime slice is a Minimum Scientific Loop spanning quest, real evidence, hypothesis, prospective test commitment, real execution/result, challenge/check, inference/claim admission or rejection, process restart, state reconstruction and `why` lineage.

## Properties favored

Early falsification of architecture, vertical value, integration evidence, constrained scope and avoidance of component-first overbuild.

## Costs / properties sacrificed

Each subsystem begins intentionally shallow; the first slice touches more boundaries than an isolated persistence prototype.

## Assumptions

A small empirical fixture can exercise the core semantics without requiring production search infrastructure, distributed scheduling or full UI.

## Enforcement

`docs/roadmap.md` Slice 1 and `docs/evaluation.md` Minimum Scientific Loop acceptance define completion. Infrastructure work not required by that loop is deferred unless it removes a demonstrated blocker.

## Evidence expected

A fresh process/session executes the loop end to end, reconstructs accepted state, explains claim lineage and survives projection deletion/stale-command tests with bounded implementation.

## Revise when

The slice cannot be made small enough to provide fast architecture feedback, or an isolated prerequisite is empirically shown to block any meaningful end-to-end implementation.

## Authority

Implementation/system architecture; changes require explicit architectural review.

## Consequences

The old standalone `Persistent Scientist` first milestone is superseded; persistence is proven as part of scientific behavior rather than as an infrastructure-only success.
