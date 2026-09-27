# Phase 5 — Analysis

Sources in this phase are methodological policy only after the relevant primary source has been read. Method-specific rules belong in source-read method cards; this phase owns the invariant structure.

**When this applies.** You are about to fit a model, compute/report an inferential statistic, compare material results, or turn a run into a hypothesis state.

**Entry preflight.** Run FIT before any confirmatory result can be exposed. A confirmatory run is blocked until `analysis-plan.md` contains, for the affected hypothesis: estimand, one primary test, dependence, decision rule, assumptions → checks → prospective failure actions, sensitivity/specification dimensions and interpretation boundary; protocol and plan freezes predate the run; registration/DRY_RUN state is valid; and exposure permits confirmatory use.

Invoke `statistical-analysis` on the plan before freeze. Method selection starts from estimand/design, not outcome type or a familiar model name.

**Execution.** Every material run writes a run manifest with the run commit, freezes, hypothesis/estimand/test IDs, typed data inputs and result artifacts. Every empirical statement that can be computed is computed; do not substitute qualitative model judgement for an executable diagnostic.

**EDA boundary.** Discovery EDA may generate hypotheses and records the data that generated them. After freeze, EDA is restricted to planned data-quality/assumption/diagnostic questions and prospective fallbacks. An unexpected pattern routes to `EXPLORATORY`, `SENSITIVITY`, `DATA_PROBLEM`, `PROTOCOL_REOPEN` or `BLOCKED`; it never silently rewrites the primary analysis.

**Discordance.** Report material disagreement between valid analyses. The pre-specified primary test decides the confirmatory hypothesis state. Sensitivity/specification results qualify robustness; they do not select the most favorable answer.

**Interpretation.** Use `May claim` / `May not claim` from the analysis plan. A result becomes a material claim only after CLAIM preflight and lineage annotation. `CONFIRMED`, `REFUTED` and `INCONCLUSIVE` are states under the recorded decision rule, not universal truth labels.

**The errors this prevents.** Fallbacks invented after residuals; estimator/estimand mismatch; independence assumed by convenience; a hypothesis discovered and confirmed on the same exposed data; specification search used to rescue a null; a result with no temporal provenance; and prose stronger than the design permits.

**Exit gate.** The analysis plan is frozen; each confirmatory result has a valid run manifest; every pre-specified check has a recorded result/consequence; every hypothesis is in a terminal state; every reported number exists in a committed aggregate; and material claims have lineage ready for review.
