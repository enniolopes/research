# Exploratory analysis

EDA has two regimes and they are not interchangeable.

## Discovery EDA

Before a confirmatory commitment, use EDA to understand measurement, data support, population, missingness, dependence, temporal/spatial structure and plausible mechanisms. It may generate hypotheses. When an outcome-bearing dataset materially generated or selected a hypothesis, record that dataset as `Generated from:` for the hypothesis. The same data do not later become independent confirmation by adding a registration after exposure.

## Confirmatory-support EDA

After freeze, inspect only properties needed by the recorded analysis plan: data-quality checks, material assumptions, diagnostics, dependence and prospective fallback criteria. An unexpected result may create an exploratory analysis or trigger a protocol reopen; it does not silently choose a new confirmatory target.

## Required routing

Every material EDA finding is routed as one of:

- `NO_CHANGE` — the recorded plan still applies.
- `SPECIFICATION` — a defensible prospective alternative preserving the same estimand.
- `SENSITIVITY` — a robustness analysis that does not decide the primary hypothesis.
- `DATA_PROBLEM` — data quality or measurement threatens the planned analysis.
- `EXPLORATORY_ONLY` — useful finding discovered through exposure, not confirmatory evidence.
- `PROTOCOL_REOPEN` — the scientific commitment itself must change.
- `BLOCKED` — missing data/authority prevents a defensible next step.

Do not produce a gallery of plots. Every plot or diagnostic states the question it answers and the routing consequence of the observed result.
