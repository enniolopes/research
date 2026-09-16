# Architecture decision records

Use an ADR for material decisions about semantics, state/consistency, ownership, boundaries, public contracts, repository topology/dependency direction, failure/operation, security/deployment or critical qualities.

ADRs are conditioned hypotheses, not monuments. They own why a decision exists and when reality should make us revisit it; domain documents own operational semantics.

## Template

```markdown
# ADR NNNN — Decision title

**Status:** Proposed | Accepted | Superseded | Rejected

## Context and drivers

## Alternatives considered

## Decision

## Properties favored

## Costs / properties sacrificed

## Assumptions

## Enforcement

## Evidence expected

## Revise when

## Authority

## Consequences
```

Do not manufacture alternatives after deciding. If constraints force one solution, state the forcing constraint.

Every accepted material ADR should identify evidence capable of challenging the decision. Mechanically testable properties should eventually gain an architecture fitness/regression check; inherently human-judged properties should say so explicitly.
