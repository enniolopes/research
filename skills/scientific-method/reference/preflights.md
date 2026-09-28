# Epistemic preflights

Phases locate the research. Preflights govern the consequential action about to happen.

## FIT

Before exposing a confirmatory result, require:

- H/E/T identities and one frozen primary test;
- assumptions, checks, prospective failure actions, dependence, decision rule and interpretation boundary;
- protocol and analysis-plan freezes;
- registration/DRY_RUN state consistent with the project;
- exposure compatible with independent confirmatory use;
- a confirmatory `analysis_role: primary | sensitivity | specification | diagnostic`;
- an `execution_freeze` satisfying the canonical run contract in `../../research-map/reference/run-receipt.md`.

Immediately before execution, tracked implementation/configuration/input state must match the execution freeze. Undeclared external, ignored or untracked runtime state is a limitation Git cannot retrospectively disprove.

The frozen primary test alone may decide the hypothesis. Prospectively named sensitivity/specification/diagnostic runs may qualify it, never replace it as the deciding statistic.

## CHANGE_PLAN

A post-freeze idea has one durable destination:

- `SPECIFICATION` — already admitted prospectively, same estimand;
- `EXPLORATORY` — result-driven or hypothesis-generating;
- `DEFERRED` — retained outside current work with an entry condition;
- `REOPEN` — changes confirmatory commitment; append a decision and create new freezes.

Classification that exists only in conversation is not state. A later reopen governs later work; it never rewrites an earlier run.

## CLAIM

Before project results enter material prose, require an executed result, valid run, relevant planned test/checks, wording permitted by the interpretation boundary, and no unresolved material contradiction/supersession. Give the claim a stable `C<n>` and direct claim→result annotation.

A deciding claim must come from the confirmatory primary run. Other runs may qualify/support wording but do not decide the hypothesis.

For construct/mechanism language, inspect the measure→interpretation bridge and a credible rival where relevant. If the design cannot distinguish explanations, narrow the claim rather than changing the empirical result.

## CITE

A source supports a proposition only after the relevant content has been retrieved and read. DOI/URL resolution proves identity/reachability, not semantic support. A source seen only through an abstract/excerpt is represented with that limitation.

## PUBLISH

Before release require:

- complete material claim lineage;
- current separate-context adversarial review;
- no unresolved material `FAIL`;
- material `NOT_VERIFIED` disclosed or resolved;
- applicable reporting, disclosure, legal/ethical and venue/funder requirements checked against current authoritative text;
- human-owned publication/ethics decisions recorded where needed.

A review record under `.research/reviews/` names the reviewed commit and manuscript. Material changes make it stale. Separate model context provides procedural separation only; it is not evidence of independent expertise or independent error sources.

## Forbidden transitions

```text
RESULT_SEEN -> RETROACTIVE_FALLBACK
RESULT_SEEN -> RETROACTIVE_EXECUTION_FREEZE
ADAPTIVE_DATA -> INDEPENDENT_CONFIRMATION_OR_VALIDATION
SOURCE_DISCOVERED -> SUPPORTS_CLAIM
UNEXECUTED_NUMBER -> RESULT
SECONDARY_TEST -> DECIDES_HYPOTHESIS_AGAINST_PRIMARY
FROZEN_PROTOCOL -> SILENT_REWRITE
VERBAL_CHANGE_CLASSIFICATION -> COMPLETED_CHANGE_PLAN
INLINE_SELF_REVIEW -> SEPARATE_CONTEXT_REVIEW
VALIDATOR_PASS -> SCIENTIFICALLY_TRUE
```

Route an invalid transition to prospective fallback, `EXPLORATORY`, `DEFERRED`, `REOPEN`, `BLOCKED` or `NOT_VERIFIED`.
