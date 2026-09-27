# research

Research system for Claude Code. It keeps empirical research problem-first, prospective, traceable, and independently reviewed.

Scope: observational quantitative research, especially administrative data.

## Quick start

Run Claude Code from the root of a **Git repository** for the research project. Git history records commitment/run order; exposure outside that history must be disclosed separately.

Install the plugin from this repository:

```text
/plugin marketplace add enniolopes/research
/plugin install research@enniolopes
```

For the full phase-1 exploration workflow, also install the optional `explorer` skill from the skills marketplace:

```text
/plugin marketplace add enniolopes/skills
/plugin install explorer@enniolopes
```

Without `explorer`, the research system remains usable; the affected exploration is recorded as `NOT_VERIFIED` rather than invented.

Start a new research project:

```text
/research:scientific-method start <idea or question>
```

Then talk normally. For example:

```text
Explore alternative explanations.
Check whether the problem is actually present in the data.
I want to start the analysis.
This result looks strange; investigate it.
Write the results section.
Review the paper before submission.
```

For an existing research repository, invoke:

```text
/research:scientific-method
```

Useful explicit commands:

```text
/research:scientific-method status
/research:scientific-method review [manuscript]
```

You do **not** need to call `research-map`, `statistical-analysis`, `research-graph`, `explorer`, validators, or `reviewer-2` manually. The orchestrator uses them when needed.

## How it works

Research follows five rules:

1. **Problem first.** Formulate the question, explore alternatives, and try to make the empirical premise disappear before committing to expensive analysis.
2. **Commit before exposure.** Confirmatory choices that a result could influence are recorded and frozen before that result is seen.
3. **Evidence over narrative.** Executed code and inspected sources outrank memory, confidence, or explanation.
4. **Discovery is not confirmation.** Data used to generate a hypothesis do not independently confirm it.
5. **Claims need lineage and challenge.** Material claims trace back to evidence and face independent adversarial review before release.

The lifecycle remains:

```text
problem → literature → protocol → data → analysis → writing → review → publication
```

The system handles the gates and preflights internally. If valid work can proceed, it should proceed; if a required condition is missing, it becomes `BLOCKED` or `NOT_VERIFIED` rather than being invented.

## What the system records

| Artifact | Purpose |
|---|---|
| `RESEARCH.map` | Current research state and next action |
| `protocol.md` | Scientific question, hypotheses, estimands, and commitments |
| `analysis-plan.md` | Primary tests, assumptions, checks, fallbacks, and interpretation limits |
| `decisions.md` | Methodological decisions and revision conditions |
| `.research/runs/` | What was executed, on which inputs, under which frozen commits |
| `aggregates/` | Computed results |
| `.research/reviews/` | Independent review evidence |
| manuscript | Scientific communication |

The derived research graph is rebuildable and is not a second source of truth.

Construct and mechanism claims explicitly connect measures to interpretations and examine discriminating evidence against plausible alternatives. When evidence changes, revision preserves unaffected findings and reassesses surviving support. Third-party reviews distinguish reported, reconstructed and reproduced findings without demanding native plugin artifacts. Graph queries identify candidate dependencies; they do not decide scientific validity.

## What happens at important boundaries

- **Before a confirmatory fit:** the system checks the estimand, primary test, assumptions/checks/failure actions, dependence, freezes, registration, and data exposure.
- **After a frozen-plan change:** the idea must become `SPECIFICATION`, `EXPLORATORY`, `DEFERRED`, or an explicit `REOPEN`; silent rewrites are not allowed.
- **Before a material claim:** the result, run, planned test, checks, and interpretation boundary must support the wording.
- **Before citing a source as evidence:** the relevant source content must have been retrieved and read.
- **Before publication:** material claims need current independent review and no unresolved material failure.

## Research states

The initial problem can end as:

```text
SHOWN | NOT_SHOWN | INCONCLUSIVE
```

Hypotheses end as:

```text
CONFIRMED | REFUTED | INCONCLUSIVE | BLOCKED | NOT_VERIFIED
```

These are decisions under the recorded design and rules, not universal truth labels.

## Validation

The validator checks mechanical properties such as map integrity, prospective plan structure, Git ancestry, run provenance, claim lineage, data exposure, citations, and notebooks.

A validator `PASS` means only that coded invariants passed. It does **not** prove that the scientific design or interpretation is correct.

For debugging/power use:

```text
python3 <installed research-map>/scripts/validate_all.py RESEARCH.map --offline
```

## Explorer

`explorer` is installed separately and is used for structural divergence and hypothesis generation. If it is unavailable, the affected exploration is `NOT_VERIFIED`; the rest of `research` remains usable.

## Development evidence

Development evals and regression tests are maintained in the source skills monorepo; this repository contains the installable research runtime.
