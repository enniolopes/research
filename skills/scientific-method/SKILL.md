---
name: scientific-method
description: Orchestrate observational quantitative research as an epistemic control system: formulate and test the problem first, explore before commitment, freeze consequential choices before result exposure, execute against identified evidence, require claim lineage, and challenge material claims in a separate review context. This is the single public entry point; it delegates exploration, statistical planning, memory, graph lineage and review internally.
when_to_use: Use to start or continue a research, check status, review a manuscript, and before fitting a model, changing a frozen plan, citing a source, reporting a material result, writing a claim or publishing. Also use when a new hypothesis or method appears after data exposure or protocol freeze.
license: CC-BY-NC-4.0
metadata:
  version: 0.10.0
argument-hint: '<start <question> | status | review [manuscript] | replay RUN-<n> | what you want to do>'
---

# Scientific method

Own the epistemic lifecycle of an empirical research project. Scope: observational quantitative research with administrative data. Other designs may reuse the kernel, but phase procedures in this version are written for this scope.

This is the public entry point. The user talks to this skill; internal skills and agents are invoked as needed. Do not make the user operate the architecture.

## Five laws

1. **Evidence outranks narrative.** What was read or executed against an identified target outranks memory, confidence and author explanation. Own computed results require executed code; externally reported results require inspected source attribution and must not be presented as reproduced.
2. **Commitment precedes exposure.** A choice that can be influenced by a result must be recorded and frozen before exposure to that result.
3. **Discovery is not confirmation.** Evidence that materially generated or selected a hypothesis does not independently confirm it.
4. **Claims require lineage.** Every material scientific claim must be traceable to identified result/source evidence and the design/checks that permit its wording.
5. **Material claims face an adversary.** The process that built a material claim is insufficient to release it; a separate-context adversarial review is required.

These laws generate the detailed rules. Do not add a second prose rule when an important failure can instead be represented as an artifact, state, relation, temporal fact or invalid transition.

## Five operations

The behavioral kernel is:

```text
EXPLORE → COMMIT → EXECUTE → JUSTIFY → CHALLENGE
```

- **EXPLORE** — high creative freedom: formulate/reformulate the problem, generate mechanisms, hypotheses, alternatives, objections and falsifications.
- **COMMIT** — make the scientific target and consequential decision rules explicit: estimand, protocol, primary test, assumptions/checks/failure actions, interpretation boundary; then freeze.
- **EXECUTE** — run identified code against identified inputs; produce run manifests, diagnostics, aggregates and results. Confirmatory execution follows the frozen plan rather than inventing a better story after exposure.
- **JUSTIFY** — decide what the result permits the project to claim, given estimand, design, checks, sensitivity and interpretation boundary.
- **CHALLENGE** — seek falsifying evidence first; run mechanical validation and a separate-context adversarial review before release.

The eight research phases below remain the lifecycle/navigation layer. Preflights, not phase vocabulary, control the action immediately before an epistemically consequential step.

## Arguments and session UX

- `start <question>` — start phase 1, initialize/resume memory, then proceed through the smallest next action.
- `status` — internally resume and validate; return one-screen state and next action.
- `review [path]` — run phase 7 for native work; use `reference/external-review.md` for third-party or historical work without native artifacts.
- `replay RUN-<n>` — invoke the research-map replay helper when the run records a replay recipe; report `EXACT | DRIFT | ERROR | NOT_VERIFIED` without treating replay status as scientific truth.
- anything else — answer the user's normal research request, but run the applicable preflight before a consequential action.

On an existing repository, invoke `research-map resume` before the first research action. Resume runs only the fast `map,plan,runs,exposure` subset; run full validation before commits, review and release. Update the map only on observable state changes.

For external review without a native map, use the external-review route instead of initializing a fictitious research history. Read `reference/inference-and-revision.md` when interpreting constructs/mechanisms, selecting a discriminating investigation or revising an existing conclusion. Keep its bridge in existing authoritative artifacts; a new ontology or database is not required.

## Preflights

Read `reference/preflights.md` whenever an action matches one of these boundaries:

- **FIT** — before a confirmatory run can expose its result; the scientific plan and executable state must already be frozen.
- **CHANGE_PLAN** — before changing a frozen hypothesis, estimand, method, population, threshold, outcome or fallback.
- **CLAIM** — before a material result becomes prose or changes a hypothesis state.
- **CITE** — before a source supports a scientific or methodological proposition.
- **PUBLISH** — before anything leaves the repository as a scientific product.

A failed preflight is resolved by inspecting/computing/recording the missing evidence, or by `BLOCKED`/`NOT_VERIFIED`. Never satisfy it with a plausible explanation of what the missing artifact probably says.

## Authority boundary

Own: lifecycle, gates, epistemic states, preflights and the quality/integrity of research artifacts.

Do not invent human authority: which question matters, field meaning not recoverable from evidence, authorship, ethics approval, institutional decisions or venue choice. Ask only the smallest decision that changes the research; record it. Everything else is inspected, searched, computed or degraded explicitly.

Do not own software engineering. Research topology remains the map's six layout pointers: protocol, decisions, aggregates, documents, notebooks, references. Packages, CI, application architecture and build systems are separate engineering concerns.

## Problem first

Phase 1 is not ceremony. Before optimizing an answer, establish that the research has a precise, falsifiable question and that any empirical premise needed to justify the research survives an attempt to make it disappear.

Gate 1A writes the problem statement from `reference/problem-statement.md`: claim, unit, estimand, refutation, objection, who cares and non-goals. Log an exploration budget before invoking `explorer`; default to a small active portfolio (usually up to three), but allow more when a logged scope decision and budget justify them. Route non-adopted lineages to `Deferred`.

Gate 1B writes the problem brief from `reference/problem-brief.md`. It establishes the empirical premise using either inspected external evidence or local executed evidence, states construct/population/measure/reference/magnitude, and attempts falsification before assertion. Local evidence is checked against aggregates; external evidence follows CITE. `NOT_SHOWN` closes or reformulates the research; it is not failure. The confirmatory protocol does not freeze while a required premise is unestablished.

Read `reference/01-problem.md` when entering/reopening phase 1.

## Analysis plan and execution

Before confirmatory Phase 5 execution, create `analysis-plan.md` from the template and invoke `statistical-analysis`. Each confirmatory hypothesis records stable H/E/T ids, exposure, dependence, decision rules, assumptions → checks → prospective failure actions, material sensitivity/specification dimensions and `May claim / May not claim` boundaries.

The canonical execution contract is `../research-map/reference/run-receipt.md`. In brief: scientific commitments freeze first; a clean executable state becomes `execution_freeze`; execution produces only declared outputs; the output commit is recorded by an append-only RUN receipt. Optional replay tests computational regeneration separately from scientific validity.

Git proves repository ordering and recorded diffs, not absence of prior human/model exposure or undeclared external runtime state. Disclose those limits; never manufacture retrospective provenance. Historical work without trustworthy temporal provenance remains historical/`NOT_VERIFIED`.

## Exposure and exploration

`Generated from:` records `DATA<n>` whose observed content materially generated, selected or changed a confirmatory commitment that was not already determined by a frozen rule. Merely triggering a prospective check/fallback that was already frozen does not make the triggering data generative. Run inputs state `role: discovery | confirmatory | validation`.

If DATA1 adaptively generated or selected a commitment, reusing DATA1 as independent confirmatory or validation evidence for that commitment is invalid. Route the result to `EXPLORATORY`, use defensible independent/held-out evidence, or reopen the design. Registration after exposure does not erase exposure.

A post-freeze idea has exactly four destinations:

1. `SPECIFICATION` — an already-prospective, scientifically defensible alternative preserving the same estimand;
2. `EXPLORATORY` — result-driven/hypothesis-generating, never allowed to rewrite confirmatory history;
3. `DEFERRED` — recorded with entry condition;
4. `REOPEN` — changes the confirmatory commitment through a logged decision and new freeze.

The route must become durable before CHANGE_PLAN is complete. `SPECIFICATION` points to the already-frozen T<n>/dimension and becomes a specification run if executed; an executed `EXPLORATORY` route gets an exploratory run manifest, while an unexecuted retained idea is written to `Deferred`; `DEFERRED` is written to the map with its entry condition; `REOPEN` appends a decision and creates new freezes. A verbal classification alone is not state.

Silent rewrite is not a state.

## Claims and lineage

A material claim is one that reports/decides a result, comparison, no-effect/equivalence conclusion, material mechanism or causal/substantive inference.

After the CLAIM preflight, annotate the source near the claim:

```text
<!-- claim:C1 result:R1 -->
```

If it decides a hypothesis:

```text
<!-- claim:C2 result:R2 decides:H1 -->
```

`research-graph` derives `C → R → RUN → T → H/E` lineage from authoritative artifacts. Mechanical validation can prove that the chain exists and uses the planned primary test; reviewer judgement decides whether result + design + checks warrant the wording. Legacy annotations with `inference:I<n>` remain readable but no longer create a separate node.

## Sources

A source may guide search when merely discovered. It supports a scientific or methodological proposition only after the relevant content has been retrieved and read. DOI/landing-page resolution establishes identity/reachability, not semantic entailment. For a narrow, repeated semantic question where the evidence-to-proposition relation is material or ambiguous, `reference/assessments.md` defines an optional tool-less assessment; it records a bounded judgment but never substitutes for reading the source or grants scientific authority. Do not create a separate source-state ledger unless a concrete project needs one.

## Terminal states

Hypotheses end in exactly one of:

`CONFIRMED | REFUTED | INCONCLUSIVE | BLOCKED | NOT_VERIFIED`.

`CONFIRMED` and `REFUTED` are decisions under the recorded rule, not global truth labels. Missing capability/authority becomes `NOT_VERIFIED` or `BLOCKED`, never a guess.

## Phases

Read only the entered phase reference, plus `reference/preflights.md` when a preflight fires.

| # | Phase | Dominant operation | Exit gate | Read |
|---|---|---|---|---|
| 1A | Problem — formulate | EXPLORE → COMMIT | exploration budget logged; explorer invoked; complete problem statement; active portfolio bounded by explicit scope/budget; others Deferred | `reference/01-problem.md`, `reference/problem-statement.md` |
| 1B | Problem — establish | EXECUTE → CHALLENGE | problem brief complete; `SHOWN`, or explicit `NOT_SHOWN`/`INCONCLUSIVE` consequence | `reference/problem-brief.md` |
| 2 | Literature | EXPLORE → JUSTIFY | relevant sources identified/retrieved/read at the level used; gap stated | `reference/02-literature.md` |
| 3 | Protocol | COMMIT | hypotheses/estimands/tests/rules fixed; registration derived; protocol freeze recorded | `reference/03-protocol.md` |
| 4 | Data | EXECUTE | input provenance, linkage/quality/exposure roles and disclosure boundary explicit | `reference/04-data.md` |
| 5 | Analysis | EXECUTE → JUSTIFY | analysis plan frozen; valid run lineage; planned checks/results complete; hypothesis terminal state | `reference/05-analysis.md` |
| 6 | Writing | JUSTIFY | every material number/claim has source/result lineage; interpretation stays inside boundary | `reference/06-writing.md` |
| 7 | Review | CHALLENGE | separate reviewer invoked; durable `.research/reviews/REVIEW-<n>.md` records the reviewed commit and verdict; reviewer `PASS`, or each `FAIL` has an explicit response and affected checks rerun | `reference/07-review.md` |
| 8 | Publication | CHALLENGE → RELEASE | PUBLISH preflight passes; venue/ethics/human requirements present | `reference/08-publication.md` |

A later finding can reopen an earlier phase. Skipping a required phase is a logged decision with revision condition, never silence. A gate is reached by the artifact/evidence it produces, not by narrative history.

## Delegation

- `explorer` — bundled phase-1 structural divergence/hypothesis-lineage delegate; it is also exposed as a standalone marketplace entry.
- `statistical-analysis` — estimand-first analysis plan, EDA boundary, dependence and missingness decisions.
- `research-map` — operational memory and composed mechanical validation.
- `research-graph` — in-memory lineage trace/why/changed queries.
- `assessor` — optional tool-less semantic judgment for a versioned narrow assessment spec; it cannot act on its own answer.
- `reviewer-2` — separate-context, non-editing adversarial review.

Invoke delegates; do not simulate them by reading their instructions. If a needed delegate cannot run, the affected check is `NOT_VERIFIED`.

## Decision log

A methodological decision keeps the existing append-only contract:

```text
### D-<n> · <YYYY-MM-DD> · <short title>
<decision>
Rationale: <evidence/source>
Revision condition: <observation that reopens it; or not revisable with reason>
```

After commit, change it only by a later block with `Supersedes: D-<k>`.

## Reporting to the user

Keep system mechanics mostly invisible. Lead with the question, permitted conclusion, decisive evidence, main limitation and next useful action; link to authoritative detail instead of copying a second report into the map. Do not require the user to memorize internal commands. When a preflight blocks an action, state what evidence/decision is missing and the legitimate route forward.

A research is complete when every hypothesis has a terminal state, material claims passed current separate-context adversarial review, publication requirements passed, and the map records the final state.
