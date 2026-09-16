# ADR 0008 — Separate Research Control Plane from Scientific Work Plane

**Status:** Accepted

## Context and drivers

Research must combine probabilistic models, external evidence, code execution and potentially private data without allowing tool/model behavior to define scientific state or authorization. Local/private execution and later distributed deployment should share the same scientific semantics.

## Alternatives considered

- Let each agent/service own its workflow state and scientific mutations.
- Put all work and control inside one monolithic model loop.
- Separate state admission/authority from bounded scientific work.

## Decision

Define a **Research Control Plane** owning Research Protocol transitions, authority, scheduling semantics, accepted events and projections; define a **Scientific Work Plane** containing AI workers, evidence retrieval, execution and external tools that return bounded outputs/receipts.

## Properties favored

Scientific control independent of model behavior, local/cloud flexibility, explicit trust boundaries, testability and replaceable workers.

## Costs / properties sacrificed

More explicit contracts between task execution and state admission; work cannot mutate accepted state by convenience.

## Assumptions

The control semantics are stable across local/deployed execution and can remain substantially smaller than the work capabilities.

## Enforcement

Dependency direction prevents work adapters from directly owning accepted-event persistence. Scientific Tasks carry capability envelopes; interfaces cannot bypass admission services.

## Evidence expected

The same Minimum Scientific Loop works with a fake/local worker and a model-backed worker; forbidden capability/egress requests are blocked before work; work-plane failure leaves accepted state coherent.

## Revise when

The boundary creates unavoidable distributed consistency complexity greater than the failures it prevents, or a required scientific capability cannot be expressed as bounded work plus explicit admission.

## Authority

System architecture; changes require an A2 review and superseding ADR.

## Consequences

Models become replaceable task executors rather than architectural owners; deployment can move work without changing scientific rules.
