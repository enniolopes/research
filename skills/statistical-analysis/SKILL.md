---
name: statistical-analysis
description: Turn a research estimand and design into an inspectable analysis strategy before fitting. Defines data-exploration boundaries, dependence, missingness, assumptions, checks, fallbacks, sensitivity and interpretation limits for observational quantitative research. Use internally from scientific-method when an analysis plan is created or revised; it proposes methods but never changes a frozen confirmatory commitment silently.
license: CC-BY-NC-4.0
metadata:
  version: 0.8.0
argument-hint: '<plan | eda | review-plan> [path]'
---

# Statistical analysis

Own the route from a scientific estimand to an analysis strategy. Do not start from a model name. Start from the quantity the research is trying to learn and the design that can identify it.

The sequence is fixed:

```text
QUESTION → CLAIM TYPE → ESTIMAND → IDENTIFICATION / DESIGN → DATA STRUCTURE
→ DEPENDENCE → ESTIMATOR → INFERENCE → DIAGNOSTICS → SENSITIVITY → INTERPRETATION
```

Read only the references needed for the current decision:

- `reference/estimands.md` before selecting an estimator or when two methods answer different questions.
- `reference/exploratory-analysis.md` before examining outcome-bearing data outside a frozen confirmatory run.
- `reference/dependence.md` before defining intervals, resampling or repeated/spatial/clustered inference.
- `reference/missingness.md` whenever missingness can change the target population, estimand or identification.

## Authority boundary

You may propose candidate methods, diagnostics and sensitivity analyses. You may not silently change the estimand, population, exposure, outcome, primary test, threshold or confirmatory fallback after exposure to a result. A choice that changes the scientific question returns to `scientific-method` as `REOPEN`; a defensible alternative that preserves the same estimand is a prospective specification dimension; a result-driven new idea is `EXPLORATORY`.

Method knowledge is advisory until its primary source has been read for the condition being encoded. A plausible method remembered by the model is a candidate, not a rule.

## `plan`

Read the protocol and current `analysis-plan.md`. For each open hypothesis:

1. identify its estimand and claim type;
2. state the identification/design assumptions that connect observed data to that estimand;
3. characterize unit, time, exposure/outcome support and dependence;
4. propose one primary test and explain why it estimates the estimand;
5. write each material assumption as `A<n> → K<n> → failure action` before fitting;
6. name sensitivity analyses and only the specification dimensions that are scientifically defensible, preserve the same estimand and could materially change inference;
7. state `May claim` and `May not claim` boundaries;
8. leave substantive alternatives unresolved when they answer different questions; that is a human/protocol decision, not model selection.

A complete confirmatory block is ready to freeze; it is not frozen by prose alone.

## `eda`

Exploratory data analysis answers whether the observed data-generating structure is compatible with the question and plan. Inspect, when relevant: population actually observed, unit and time structure, measurement, missingness, support/overlap, dependence, distribution, zeros, outliers/influence, linkage, spatial/temporal structure and heterogeneity.

Every material finding ends in exactly one routing consequence:

`NO_CHANGE | SPECIFICATION | SENSITIVITY | DATA_PROBLEM | EXPLORATORY_ONLY | PROTOCOL_REOPEN | BLOCKED`.

Discovery EDA may generate hypotheses, but the data that generated them are recorded as exposure. Confirmatory-support EDA after freeze is restricted to planned quality checks, assumptions, diagnostics and prospective fallbacks. It cannot redefine the target because the observed outcome made another target attractive.

## `review-plan`

Attack the plan before execution. Look first for: estimator/estimand mismatch; unacknowledged dependence; identification assumptions that have no observable implication or sensitivity plan; missingness changing the target population; a diagnostic with no predeclared consequence; a fallback that changes the estimand; specification dimensions that are merely a search space; and interpretation language stronger than the design supports.

Return `PASS`, `FAIL` or `NOT_VERIFIED`, followed by the smallest change that resolves each finding. A structurally complete plan can still be scientifically wrong; mechanical validation never substitutes for this review.
