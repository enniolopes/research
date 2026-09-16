# Research Protocol

## Purpose

The Research Protocol is the semantic contract of Research Core. It defines what scientific state means, who may propose or admit a change, which durable evidence a transition requires, and how the same research remains coherent across models, retries, crashes and interfaces.

It is deliberately smaller than the complete scientific method and smaller than the future ontology. It should be implementable with ordinary types, transactions and append-only records.

## Core distinction

```text
work produces observations/evidence/receipts/proposals
                    |
                    v
             control validates
                    |
                    v
        accepted scientific transition
                    |
                    v
              durable event
```

A worker output is not accepted scientific state until an owning transition admits it.

## Primary entities

Initial runtime semantics should use only entities required to support the minimum scientific loop:

- **Quest / Problem** — the question and relevant scope the research is trying to resolve.
- **Hypothesis** — a testable candidate explanation/prediction with epistemic status.
- **Decision / Commitment** — a consequential scientific choice and its authority/timing.
- **Test / Plan** — prospective operation, target, rules and interpretation boundary.
- **Evidence** — inspected external or empirical support/challenge tied to a proposition and source.
- **Execution** — identified activity performed against identified code/inputs/environment.
- **Result** — observation produced by a valid execution or identified external source; not yet an interpretation.
- **Check** — observation about an assumption, implementation, robustness or validity condition.
- **Inference** — warrant connecting results/evidence/design/checks to an interpretation.
- **Claim** — material statement admitted within an inference/evidence boundary.
- **Review / Challenge** — adversarial assessment that may challenge but does not silently rewrite history.
- **Scientific Task** — bounded requested work with capabilities, target and expected output.

Add a new entity class only when a required control/query cannot be represented without it and an evaluation demonstrates the gap.

## Identity

Every durable entity has a stable project-scoped ID. Every command and task has an operation ID. Every accepted transition records the target project state version it was validated against.

Identities are machine handles; user-facing interfaces may use natural names.

## Epistemic status

Do not collapse distinct states into a universal confidence score. Initial statuses may differ by entity but must preserve at least:

- proposed/open;
- committed where commitment is meaningful;
- supported/challenged without implying truth;
- admitted/rejected when a control decision exists;
- superseded/invalidated/stale without deleting history;
- blocked/not-verified when evidence is insufficient.

Exact enums belong to implementation contracts once the Minimum Scientific Loop supplies concrete transition cases.

## Command contract

A command that can alter accepted state contains conceptually:

```yaml
command_id:
project_id:
command_type:
target_ids:
expected_state_version:
authority:
inputs_or_evidence_refs:
idempotency_key:
requested_by:
```

Not every field must be hand-authored or user-visible. The runtime supplies deterministic fields where possible.

## Accepted event contract

An accepted state transition emits one durable domain event containing enough identity to audit/replay the transition:

```yaml
event_id:
project_id:
event_type:
command_id:
prior_state_version:
new_state_version:
target_ids:
evidence_or_receipt_refs:
authority_basis:
recorded_at:
```

An event says that Research Core admitted a transition. It does not claim universal scientific truth.

## Initial transition families

The first implementation should prove these semantic families end to end:

```text
QuestStarted
EvidenceInspected
HypothesisProposed
TestCommitted
ExecutionRegistered
ResultProduced
CheckRecorded
InferenceAdmitted | InferenceRejected
ClaimAdmitted | ClaimRejected
ChallengeRecorded
EntitySuperseded
```

Names may change during implementation; the semantic distinctions may not be silently merged.

## Example confirmatory path

```text
H1 OPEN
 + CommitTest(T1)
 + valid plan/authority
 -> TestCommitted(H1,T1,freeze)

T1 COMMITTED
 + valid execution receipt RUN1
 -> ExecutionRegistered(RUN1,T1)
 -> ResultProduced(R1,RUN1)

R1
 + design + checks + explicit warrant
 -> InferenceAdmitted(I1)

I1
 + claim boundary satisfied
 -> ClaimAdmitted(C1)

C1
 + independent challenge
 -> ChallengeRecorded(review,C1)
```

A failed check, stale target, invalid run, prohibited exposure or insufficient warrant rejects/blocks the relevant transition rather than being summarized away.

## Admission rules

1. **Evidence first.** A transition that depends on observed/executed evidence references durable evidence/receipts.
2. **Target binding.** Evidence and verification are valid only for the identified target/state they observed; drift invalidates only affected uses.
3. **Commitment before exposure.** Confirmatory choices that could be biased by the result are committed before exposure.
4. **Discovery is not independent confirmation.** Generation/selection provenance is preserved so the same data cannot silently play an independent role.
5. **Result is not inference.** Correct execution may still license weak or no interpretation.
6. **Inference is not claim release.** Claim class/scope and review may impose additional gates.
7. **No silent rewrite.** Post-freeze change routes to prospective specification, explicit exploration, deferred work or reopen/supersession.
8. **Workers do not self-admit.** Generator identity never provides admission authority.
9. **Human-owned authority remains explicit.** Ethics, material risk acceptance, scientific objective changes and analogous decisions are not inferred from tool availability.

## Concurrency and idempotency

Commands that may retry are idempotent by operation/idempotency identity. A state-changing command carries an expected project/version precondition. If the accepted state has advanced incompatibly, the command returns a stale/conflict outcome and must be re-evaluated; last-write-wins is forbidden for scientific transitions.

Duplicate work may exist, but duplicate accepted meaning must be detected or explicitly represented as independent replication rather than accidental duplication.

## Projection rule

The control event log and referenced authoritative artifacts/receipts can rebuild current accepted state. The world model, task status tables, map, graph and vector indexes are projections. A projection can be dropped and rebuilt without changing scientific history.

## Version 0 completion criterion

The protocol is sufficient for initial implementation when a fresh process can reconstruct a Minimum Scientific Loop, explain `why` a claim is or is not admitted, detect stale/duplicate commands, and recover after projection loss without inventing state.
