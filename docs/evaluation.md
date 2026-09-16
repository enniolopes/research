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

## Required regression questions

The suite should eventually answer at least:

- Can a new session resume the correct research state without conversation history?
- Does the system ever invent a result not produced by execution/evidence?
- Can it reproduce a material number from the recorded state?
- Can it find and preserve a source that contradicts the leading hypothesis?
- Does it prevent discovery evidence from masquerading as independent confirmation?
- Does it resist changing the confirmatory test after exposure?
- Can it propose a materially distinct rival explanation and a discriminating test?
- Does it execute a needed check rather than merely recommending it?
- Does claim wording remain inside the design/evidence boundary?
- Can an independent reviewer find a seeded material flaw?

## Control vs treatment

For major architectural controls, retain comparable runs with and without the mechanism where practical. Failure reduction should be observed, not assumed from design elegance.

## Epistemic overhead

Track the cost imposed by the system: extra model context, tool calls, authoring steps and wall-clock/compute overhead. A control that prevents a severe failure can justify overhead, but overhead must be visible.