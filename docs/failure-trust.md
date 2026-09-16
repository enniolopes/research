# Failure, concurrency and trust model

This document owns cross-cutting runtime semantics that can change scientific state if left implicit.

## Principle

Infrastructure failure must not silently become scientific evidence, duplicate scientific meaning, erase contradiction or bypass authority. The safe default is explicit `BLOCKED`, `NOT_VERIFIED`, conflict or retryable failure rather than plausible completion.

## Atomicity boundary

For a material transition that depends on an execution receipt or evidence record:

1. required durable evidence/receipt must already exist or be committed in the same protected operation;
2. the accepted control event is appended once;
3. projections may update afterward and are repairable.

A projection/UI failure after the event does not roll scientific history backward. An event may not reference evidence that was never durably written.

## Crash and retry

- Commands/tasks have stable IDs.
- Retry of the same logical operation reuses an idempotency key.
- A timeout is `unknown outcome` until the ledger is checked; never assume failure and repeat blindly.
- Late worker responses are validated against their target state/version before use.
- A partially executed scientific process cannot be upgraded to a result without a valid execution receipt.

## Concurrency

Scientific state changes use optimistic version preconditions or an equivalent deterministic conflict mechanism. Incompatible concurrent transitions do not resolve by arrival order.

Parallel tasks are allowed when their scientific dependencies, exposure rules and mutable resources do not conflict. Parallelism is a scheduling optimization, not evidence of epistemic independence.

## Staleness

Evidence, reviews and checks are target-bound. When code, data, plan or relevant accepted state changes, invalidate only the evidence whose subject/assumptions changed. A stale review cannot silently certify a changed claim.

## Duplicate meaning

Two workers may independently discover the same source, run or hypothesis. Deduplication is semantic and cautious:

- identical operation retry -> same logical operation;
- independently repeated execution -> distinct execution/replication evidence;
- equivalent hypothesis wording -> may point to one hypothesis only after explicit reconciliation;
- never merge merely because embeddings are similar.

## Recovery

Recovery order:

```text
verify authoritative artifacts / execution receipts / event log
 -> restore accepted current state
 -> rebuild projections
 -> reconcile in-flight tasks
 -> resume only tasks whose target and capability envelope remain valid
```

Repair tools may rebuild projections but may not fabricate missing authoritative evidence.

## Scientific Task capability envelope

Every task declares the minimum capabilities it needs, conceptually:

```yaml
data_read:
data_write:
filesystem:
network:
model_egress:
credentials:
execution:
tools:
budget:
```

The envelope is determined by Research Core/human policy, not by the worker. Tool availability does not grant permission.

## Data egress

Before information is sent to a remote model/search/tool, the adapter checks the task envelope and data classification. The system must be able to support cases such as:

- raw data remains local;
- only approved aggregates leave the machine;
- scholarly search has network access but no private dataset access;
- execution sandbox has dataset access but no network;
- credentials are injected only into the adapter/action that needs them and are never written into model context or scientific artifacts.

Exact classification policy is deployment-specific, but the enforcement boundary is architectural.

## Trust boundaries

Treat model output, web/source content and tool output as evidence/proposals with provenance, not executable authority. Execution of external/untrusted code occurs only under an explicit sandbox/trust decision appropriate to the risk.

## Failure outcomes

Runtime APIs should distinguish at least:

- rejected scientific transition;
- stale/conflict;
- blocked by authority/prerequisite;
- retryable infrastructure failure;
- unknown outcome requiring reconciliation;
- invalid execution/evidence receipt;
- not verified.

Do not encode these all as generic model/tool errors; the user and orchestrator need to know whether science changed.
