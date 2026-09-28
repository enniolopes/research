# Semantic assessments

An assessment is a bounded semantic judgment over exact recorded inputs. It is evidence for later scientific reasoning; it is not a scientific transition, claim, decision, review verdict, or source of truth.

Use an assessment only when a recurring semantic question is narrow enough to have a stable answer space but is not mechanically decidable. Deterministic facts remain validators; open scientific integration remains with the scientific method, reviewer, or human authority.

## Contract

Committed assessments live under:

```text
.research/assessments/ASMT-<n>.json
```

The first committed form is immutable. If evidence, target, criterion, or judgment changes, create a new ASMT id.

Each assessment records the exact proposition and evidence text that were judged, plus an evaluator identity:

```json
{
  "id": "ASMT-1",
  "spec": "citation-entailment@1",
  "target": {
    "kind": "claim",
    "id": "C1",
    "text": "The intervention was associated with a lower observed rate."
  },
  "evidence": [
    {
      "source": "doi:10.x/example",
      "locator": "p. 14",
      "text": "Exact inspected passage supplied to the assessor.",
      "sha256": "<sha256 of evidence.text UTF-8 bytes>"
    }
  ],
  "answer": "SUPPORTS",
  "basis": "The passage reports the same population, exposure relation, and outcome direction.",
  "evaluator": {
    "backend": "claude",
    "model": "<actual evaluator identity>",
    "procedure": "assessor@1"
  }
}
```

The evidence digest binds the judgment to the exact text supplied to the assessor. It does not prove that the passage was copied correctly from the external source; ordinary CITE provenance still owns retrieval and source inspection.

Evaluator diagnostics may be added as extra fields. A model confidence or probability is operational metadata only and must never be interpreted as probability that the scientific claim is true.

## `citation-entailment@1`

Question:

> What relation does the inspected evidence have to the exact proposition, using only the supplied evidence text?

Answers:

- `SUPPORTS` — the supplied evidence directly supports the proposition within the proposition's stated scope;
- `CONTRADICTS` — the supplied evidence directly conflicts with the proposition;
- `INSUFFICIENT` — neither relation is licensed without missing context, an unstated bridge, or outside knowledge.

The assessor must abstain with `INSUFFICIENT` rather than repair an underspecified proposition or import facts not present in the supplied evidence.

## Authority

Assessments may inform CITE, CLAIM, or review. They never:

- replace retrieval and reading of a source;
- create source support by themselves;
- change a hypothesis state;
- admit a claim;
- override a validator failure;
- replace separate-context adversarial review.

A reviewer may agree, disagree, or ignore an assessment and should inspect the underlying evidence whenever the semantic relation is material.
