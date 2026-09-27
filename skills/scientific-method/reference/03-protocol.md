# Phase 3 — Protocol

Sources located 2026-09-10, not yet read at source.

**When this applies.** After the question and literature, before any confirmatory analysis
runs. Any change to hypotheses, tests, populations or thresholds reopens this phase — and
reopening has a price: the decision that admits something new says what leaves. A new idea
that is an alternative way of doing something already here becomes a specification-curve
dimension; one that is not goes to the map's `## Deferred` unless the trade is logged.

**What it requires.**

- Per hypothesis: a **prediction** and a **refutation condition**, and exactly **one
  primary test**. Secondary tests are named as secondary.
- **Separable stages.** If the outcome is produced by more than one administrative act
  (applying, being approved), ask whether the stages are separable and pre-specify the
  decomposition.
- **Assumptions → check → fallback** per model, written before fitting. A fallback chosen
  after seeing residuals is a forking path.
- **Equivalence bounds** fixed before any test that may claim "no effect".
- **Thresholds** (radii, cut-offs) carry a data-derived or literature-derived rationale; a
  round number is not a rationale.
- **Specification-curve dimensions.** Every analytic choice that could reasonably have gone
  another way — population definition, covariate set, functional form, threshold — is a
  dimension, not a footnote.
- **Identification.** For a causal claim from observational data, state the target trial
  and the assumptions (exchangeability, positivity, consistency) that stand in for
  randomisation; if they cannot be defended, the claim is associational and says so.
- **Registration.** The protocol is frozen and a registration text is derived from it.
  Until registration exists, confirmatory code runs only in `DRY_RUN` (outcome permuted).
  Descriptive results computed before registration are disclosed in it as prior
  observations.

**The error it prevents.** Postdiction presented as prediction; a rescued hypothesis; a
"no effect" claim without bounds; a specification chosen because it worked.

**Exit gate.** Protocol frozen; registration text derived; every hypothesis has prediction,
refutation, primary test; every model has its assumption table; bounds and dimensions
listed.

**Sources.** Nosek et al. 2018 (preregistration separates prediction from postdiction).
Lakens 2017 (equivalence bounds fixed in advance). Simonsohn, Simmons & Nelson 2020
(specification curve: enumerate, display, infer jointly). Simmons, Nelson & Simonsohn 2011
(undisclosed flexibility). Gelman & Loken 2014 (forking paths without intent). Hernán &
Robins, *Causal Inference: What If* (identification assumptions; target trial).
