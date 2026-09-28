# Epistemic preflights

Phases describe where the research is. Preflights govern the action about to happen. Run the smallest applicable preflight before the action, regardless of phase.

## FIT

Before a confirmatory analysis can expose its result, require:

- hypothesis and estimand IDs;
- one recorded primary test;
- an `analysis-plan.md` block with assumptions, checks, failure actions, dependence and interpretation boundary;
- protocol and analysis-plan freezes that predate the run;
- registration/DRY_RUN state consistent with the protocol;
- data exposure compatible with confirmatory use;
- a run role: `primary | sensitivity | specification | diagnostic`;
- an `execution_freeze` commit at or after the protocol/analysis-plan freezes and strictly before the run commit, containing the executable implementation, configuration, declared inputs and repository-tracked environment recipe.

A `primary` confirmatory run executes the frozen primary test and may decide the hypothesis under the frozen decision rule. A confirmatory sensitivity/specification/diagnostic run must have its T<n> named in the frozen plan and may qualify/check the primary result, never replace it as the deciding test.

The run commit must contain the identified input paths and result artifact. Between `execution_freeze` and the run commit, only declared output artifacts may change, and each declared output must cross that boundary. The first committed version of a run receipt is append-only. Rewriting an old receipt or aggregate under the same RUN/R identity is historical drift, not an update; create a new run/result identity or restore the committed artifact.

A missing material condition blocks the fit. Do not satisfy a failed preflight with an explanation of what the missing artifact probably would have contained.

## CHANGE_PLAN

A post-freeze change is classified before editing the confirmatory plan:

- `SPECIFICATION` when it is a defensible alternative that preserves the same estimand **and was already admitted prospectively in the frozen plan**;
- `EXPLORATORY` when it is result-driven or hypothesis-generating;
- `DEFERRED` when it does not enter the current research;
- `REOPEN` when it changes the confirmatory scientific commitment. `REOPEN` requires a logged decision and a new freeze.

Classification is not complete when it exists only in the conversation. Before returning from the preflight, make the destination durable in the artifact that owns it:

- `SPECIFICATION` — reference the already-frozen T<n>/dimension; if executed, its run manifest uses `analysis_role: specification`;
- `EXPLORATORY` — if executed, record an exploratory run manifest; if retained but not executed, place it in `RESEARCH.map` `Deferred` as an exploratory candidate with its entry condition;
- `DEFERRED` — write it to `RESEARCH.map` `Deferred` with the condition that would admit/revisit it;
- `REOPEN` — append a methodological decision and create new protocol/analysis-plan freezes before subsequent confirmatory work.

A genuinely new post-freeze alternative cannot be relabeled `SPECIFICATION` to keep confirmatory status. A previous run remains judged against the plan commit frozen for that run. A reopen governs subsequent work; it does not rewrite historical provenance.

Silent rewrite and verbal-only routing are not states.

## CLAIM

Before a claim about this project's computed results enters prose, require an executed result, a valid run, the relevant planned test and checks, an interpretation boundary that permits the wording, and no unresolved supersession or material contradictory result. Give the claim a stable ID and a direct claim→result lineage annotation. A claim about externally reported findings follows CITE and the external-review route instead; never invent a local run for it.

For a construct or mechanism interpretation, inspect the bridge in `inference-and-revision.md`: observed result, measure/construct link, plausible rival and discriminating evidence. If the design cannot distinguish explanations, limit the attribution while preserving the observed result. After a correction, reassess affected support and record its disposition before reusing the claim; graph reachability alone neither proves nor refutes it.

A hypothesis-deciding claim must come from a confirmatory `primary` run executing that run's frozen primary test. Sensitivity, specification, diagnostic and exploratory results may support/qualify claims but do not decide the confirmatory hypothesis.

## CITE

A source may suggest a search while merely discovered. It supports a scientific or methodological proposition only after the relevant source content has been retrieved and read. DOI/URL resolution proves identity/reachability, not semantic support.

## PUBLISH

Before release, require material claims to have complete lineage and an independent adversarial review; no unresolved `FAIL`; material `NOT_VERIFIED` explicitly disclosed or resolved; reporting/disclosure requirements satisfied; and human-owned publication/ethics decisions present.

Independent review is evidenced by a durable `.research/reviews/REVIEW-<n>.md` record containing the reviewed repository commit, manuscript path and the returned reviewer verdict/findings. The record is written from an actual separate reviewer invocation (`research:reviewer-2` when available), not from the orchestrator reviewing its own work inline. If the independent reviewer capability cannot run, the review requirement is `NOT_VERIFIED`; do not simulate independence. A review record that predates material manuscript/result changes is stale and does not satisfy PUBLISH until the affected review is rerun.

## Forbidden transitions

The following transitions are invalid:

```text
RESULT_SEEN -> RETROACTIVE_FALLBACK
RESULT_SEEN -> RETROACTIVE_EXECUTION_FREEZE
DISCOVERY_DATA -> INDEPENDENT_CONFIRMATION_OF_DERIVED_HYPOTHESIS
SOURCE_DISCOVERED -> SUPPORTS_CLAIM
UNEXECUTED_NUMBER -> RESULT
SECONDARY_TEST -> DECIDES_HYPOTHESIS_AGAINST_PRIMARY
FROZEN_PROTOCOL -> SILENT_REWRITE
VERBAL_CHANGE_CLASSIFICATION -> COMPLETED_CHANGE_PLAN
INLINE_SELF_REVIEW -> INDEPENDENT_REVIEW
VALIDATOR_PASS -> SCIENTIFICALLY_TRUE
```

Route invalid transitions to a legitimate state: prospective fallback, `EXPLORATORY`, `DEFERRED`, `REOPEN`, `BLOCKED` or `NOT_VERIFIED`.
