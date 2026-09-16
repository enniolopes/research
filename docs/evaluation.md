# Evaluation strategy

## What we optimize

Scientific efficacy, not architectural compliance.

A change is valuable when it improves one or more of:

- quality/diversity of useful hypotheses;
- amount and relevance of evidence actually inspected;
- correctness and completion of real execution;
- resistance to false positives and attractive narratives;
- long-horizon coherence;
- reproducibility;
- precision and support of scientific claims;
- time/cost to reach useful evidence.

It must not materially degrade discovery quality, evidence inspection or execution merely to improve provenance.

## Evaluation levels

### L1 — primitives

Search/retrieve/read a source, inspect data, execute code, reproduce a number, resolve an artifact identity.

### L2 — epistemic operations

Generate rival hypotheses, design a discriminating test, detect contradictory evidence, reject a retroactive plan change, distinguish result from claim, falsify a false premise.

### L3 — realistic workflows

Reproduce or extend analyses from real research repositories/papers with hidden checks and known failure mechanisms.

### L4 — open research

Projects where the answer is not predetermined, reviewed by domain experts and judged on useful information gain, validity, novelty scope and reproducibility rather than publication rhetoric.

## Minimum Scientific Loop acceptance

The first runtime slice is not complete until an end-to-end test can:

1. start a quest/problem;
2. inspect and persist real evidence;
3. create a hypothesis/rival;
4. commit a test before confirmatory exposure;
5. execute a real analysis and persist a receipt/result;
6. record at least one check/challenge;
7. admit or reject an inference/claim with an inspectable reason;
8. terminate the process;
9. restart from a fresh process/session without chat history;
10. reconstruct the same accepted state and answer `why` for the claim;
11. rebuild the world-model projection after deleting it;
12. reject a duplicate/stale state-changing command.

## Required regression questions

The suite should eventually answer at least:

- Can a new session resume correct research state without conversation history?
- Does the system ever invent a result not produced by execution/evidence?
- Can it reproduce a material number from recorded state?
- Can it find and preserve a source that contradicts the leading hypothesis?
- Does it prevent discovery evidence from masquerading as independent confirmation?
- Does it resist changing the confirmatory test after exposure?
- Can it propose a materially distinct rival explanation and a discriminating test?
- Does it execute a needed check rather than merely recommending it?
- Does claim wording remain inside the design/evidence boundary?
- Can an independent reviewer find a seeded material flaw?
- Can projection loss be repaired without changing accepted scientific history?
- Do timeout/retry and concurrent stale commands avoid duplicate/last-write-wins scientific state?
- Does a task capability envelope prevent forbidden data egress/tool access?

## Architecture fitness

Each material ADR owns at least one **expected evidence** item and **revise_when** condition. Where a property is mechanically testable, create a fitness/regression test. Where it is inherently human-judged, state that explicitly instead of inventing a metric.

Examples:

- world model remains bounded as ledger history grows while preserving material contradiction/blockers;
- deleting projections and rebuilding yields semantically equivalent accepted state;
- provider replacement does not alter stored scientific identity/lineage;
- a late worker response against a stale version is rejected;
- a missing execution receipt prevents a result transition.

## Control vs treatment

For major controls, retain comparable runs with and without the mechanism where practical. Failure reduction should be observed, not assumed from design elegance.

## Epistemic overhead

Track cost imposed by the system: extra model context, tool calls, authoring steps, storage and wall-clock/compute overhead. A control preventing a severe failure can justify overhead, but overhead must be visible.
