# ADR 0007 — Put rigor at consequence boundaries

**Status:** Accepted

## Context and drivers

Continuous schema/checklist enforcement consumes model attention and can suppress useful exploration, while uncontrolled high-consequence transitions enable hindsight, p-hacking and unsupported claims.

## Alternatives considered

- Apply full control/schema discipline to every exploratory thought.
- Keep the entire workflow permissive and rely on review at the end.
- Preserve permissive exploration and enforce controls at consequence boundaries.

## Decision

Preserve broad creative freedom during exploration and impose mandatory controls at high-consequence boundaries: scientific commitment, confirmatory result exposure, post-freeze plan changes, material claims and release/review.

## Properties favored

Creative search, low epistemic overhead, explicit confirmatory integrity and inspectable transitions.

## Costs / properties sacrificed

The runtime must correctly classify/rout transitions and preserve generation/exposure provenance rather than using one uniform workflow.

## Assumptions

The dominant scientific harm comes from uncontrolled consequential transitions rather than speculative thoughts themselves; exploratory outputs can remain non-canonical until they matter.

## Enforcement

Research Protocol transition families and preflights govern consequence boundaries. A new mandatory control must name a failure mechanism and an evaluation.

## Evidence expected

Exploration quality/diversity does not materially regress versus a permissive baseline while seeded post-exposure plan changes and discovery-as-confirmation attempts are rejected/routed explicitly.

## Revise when

Evaluations show controls meaningfully suppress discovery, miss important failure boundaries, or impose overhead without reducing failure.

## Authority

Scientific/system architecture; changes require a superseding ADR.

## Consequences

Most exploratory thoughts never become durable protocol entities; post-result ideas remain allowed but cannot rewrite confirmatory history.
