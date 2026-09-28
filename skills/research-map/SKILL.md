---
name: research-map
description: Operational memory and mechanical validation across sessions for one research repository. Keeps a small RESEARCH.map pointing to authoritative artifacts, resumes state before work, updates on observable state changes, and composes structural and epistemic integrity checks for research 0.10. Normally invoked internally by scientific-method; direct modes remain available for debugging and power users.
when_to_use: Use internally at the start of an existing research session, after gate/hypothesis/registration/corrected-number changes, and before commits or release. Direct triggers include resume, status, validate, update the map, or initialize an existing research.
license: CC-BY-NC-4.0
metadata:
  version: 0.10.0
argument-hint: 'init|resume|update|validate [path to RESEARCH.map]'
---

# Research map

`RESEARCH.map` is the one-screen operational index of a research. It is not a second copy of protocol, analysis plan, results, lineage or history. The repository artifacts remain authoritative; the map says where they are and what state the research is in.

`scientific-method` normally invokes this skill automatically. Do not require the user to perform a session ritual manually.

## Map contract

The grammar and examples live in `reference/map-schema.md`; a blank map is `templates/RESEARCH.map`.

Fixed sections, in order:

| Section | Holds |
|---|---|
| `## Layout` | `protocol`, `decisions`, `aggregates`, `documents`, `notebooks`, `references`; optional disclosure `floor` |
| `## Question` | question pointer; `Problem:` state/brief; `Registration:` state |
| `## Hypotheses` | prediction, refutation, terminal state and pointer; keep the active portfolio intentionally small |
| `## Gates` | one row for 1A, 1B and phases 2–8; state plus evidence for every reached gate |
| `## Deferred` | post-freeze ideas not admitted, dated with entry condition |
| `## Last session` | dated state changes and exactly one `Next:` line |

Do not add analysis-plan contents, run manifests or graph edges to the map. `analysis-plan.md` is authoritative for analytic commitment; `.research/runs/` for executions; `research-graph` derives lineage.

## `init`

Build a map from an existing protocol and decision log. Fill only state that belongs in the map. Every gate starts `pending` and becomes `reached` only when the artifact the gate produces exists and the gate row points to it. Finish with `validate`.

## `resume`

Before the first research action in an existing repository, read the map and only the authoritative artifacts needed for the active question. Return one screen: question and permitted conclusion; decisive evidence and main limitation; next action and material blockers; last change. Then run the fast integrity subset `--only map,plan,runs,exposure`. Full validation is reserved for commits, review and publication. Do not imply a conclusion merely from a gate state.

A stale map never outranks current executable/source evidence. If map narrative conflicts with current code/data/artifacts, surface the contradiction, use verifiable current evidence and preserve the correction.

## `update`

Update only on observable events: gate state/evidence changed, hypothesis terminal state changed, registration changed, a material number was corrected, or a commit is about to record those changes. Keep `Gates`, `Hypotheses`, `Question` state and `Last session` synchronized with their authoritative artifacts; never copy result prose into the map. Run `validate` after the update.

## `validate`

Run the composed 0.10 validator:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/validate_all.py" RESEARCH.map --offline
```

Structural checks:

- `map` — minimal schema, pointers, distinct 1A/1B/2–8 gates, problem-before-protocol and state integrity;
- `numbers` — document and locally computed problem-brief numbers are present in committed aggregates at quoted precision (presence, not provenance);
- `decisions` — decision block IDs/order, supersession references and revision conditions; Git preserves the edit history, but this check does not prove block immutability;
- `disclosure` — no count cell below the map floor under documents;
- `citations` — bibliographic resolution; offline is `NOT_VERIFIED`;
- `notebooks` — no committed notebook outputs/execution counts.

The epistemic checks add:

- `plan` — stable H/E/T IDs, decision rules, assumptions/checks/failure actions, dependence and interpretation boundary;
- `runs` — append-only run receipts, result artifacts, confirmatory plan/execution freeze ancestry, and a freeze→run diff containing only declared outputs;
- `lineage` — material claim annotations resolve through result/run and hypothesis-deciding claims use the planned primary test;
- `exposure` — data whose observed content generated or selected a non-precommitted confirmatory choice are not silently reused as independent confirmatory or validation evidence. Triggering an already-frozen rule is not adaptive generation.

A check with nothing to examine reports `NOT_VERIFIED`, never `PASS`. Exit is nonzero on `FAIL`; `--strict` also treats `NOT_VERIFIED` as failure.

Use `--only` to isolate checks, for example:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/validate_all.py" RESEARCH.map --offline --only plan,runs,lineage,exposure
```

Mechanical `PASS` means only that those invariants passed. It never means the design, method or claim is scientifically true.

For a run with a recorded replay recipe, computational regeneration is a separate check:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/replay.py" RUN-4 --root .
```

It returns `EXACT`, `DRIFT`, `ERROR`, or `NOT_VERIFIED`. Replay is useful evidence, not a prerequisite for a scientifically valid run; restricted data, expensive computation or unavailable historical environments may legitimately remain `NOT_VERIFIED`.

## Boundaries

A number belongs in an aggregate; a scientific commitment in protocol/analysis plan; a methodological choice in the decision log; an execution in a run receipt; a claim in the manuscript. Lineage is derived on demand. The map only points to current state and next action.
