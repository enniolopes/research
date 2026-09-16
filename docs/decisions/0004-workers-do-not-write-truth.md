# ADR 0004 — Workers propose; Research Control Plane admits

**Status:** Accepted

## Context and drivers

Generative workers are useful for hypothesis generation, evidence extraction and analysis but are probabilistic and rhetorically persuasive. Letting a worker both generate and establish its own output makes scientific controls dependent on prompt compliance.

## Alternatives considered

- Workers mutate authoritative state directly.
- One orchestrator model decides and writes all state.
- Workers return typed outputs; deterministic/control services validate the transition and authority.

## Decision

Workers return typed proposals, observations, evidence references, execution references, critiques or blockers. The **Research Control Plane** alone admits/rejects changes to accepted scientific state under the Research Protocol.

## Properties favored

Provider independence, enforceable scientific gates, auditability, adversarial independence and reduced narrative-to-truth failure.

## Costs / properties sacrificed

Additional transition/admission code and typed boundaries between cognitive work and accepted state.

## Assumptions

Most material scientific transitions have sufficient deterministic prerequisites/authority checks to separate generation from admission even when scientific judgment remains partly model/human mediated.

## Enforcement

Worker credentials/interfaces cannot directly append accepted events. Accepted events require validated commands and referenced durable evidence/receipts. Human-judged decisions are explicit authority inputs.

## Evidence expected

Seeded worker outputs containing unsupported/persuasive claims fail admission; replacing a model provider does not alter scientific state contracts; adversarial workers can challenge state without rewriting history.

## Revise when

The separation prevents necessary scientific judgment that cannot be represented as an explicit decision/authority transition, or creates measured overhead greater than its observed failure reduction.

## Authority

System architecture; changes require an A2 review and superseding ADR.

## Consequences

Worker APIs need explicit output types and evidence references; state transition code becomes a critical correctness/audit surface.
