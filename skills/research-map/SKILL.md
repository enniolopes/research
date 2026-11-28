---
name: research-map
description: Operational memory and mechanical validation across sessions for one research repository. Keeps a small RESEARCH.map pointing to authoritative artifacts, resumes state before work, updates on observable state changes, and composes structural and epistemic integrity checks for research 0.11. Normally invoked internally by scientific-method; direct modes remain available for debugging and power users.
when_to_use: Use internally at the start of an existing research session, after gate/hypothesis/registration/corrected-number changes, and before commits or release. Direct triggers include resume, status, validate, update the map, or initialize an existing research.
license: CC-BY-NC-4.0
metadata:
  version: 0.11.1
argument-hint: 'status|init|resume|update|validate [path to study]'
---

# Research map

`RESEARCH.map` is the one-screen operational index of a research. It is not a second copy of protocol, analysis plan, results, lineage or history. The repository artifacts remain authoritative; the map says where they are and what state the research is in.

`scientific-method` normally invokes this skill automatically. Do not require the user to perform a session ritual manually.

- `status` — call `view status --root . --audience model` directly, including for the first request in a study. Explanation and impact requests use the corresponding view with the same audience. [Study views](#study-views)

## Map contract

The grammar and examples live in `reference/map-schema.md`; a blank map is `templates/RESEARCH.map`.

Fixed sections, in order:

| Section | Holds |
|---|---|
| `## Layout` | `protocol`, `decisions`, `aggregates`, `documents`, `notebooks`, `references`; optional disclosure `floor` |
| `## Question` | question pointer; `Problem:` state/brief; `Registration:` state |
| `## Hypotheses` | prediction, refutation, terminal state and pointer; keep the active portfolio intentionally small |
| `## Gates` | one row for 1A, 1B and phases 2–8; state plus evidence for every reached gate |
| `## Deferred` | ideas set aside during exploration or after freeze, dated with entry condition |
| `## Last session` | dated state changes and exactly one `Next:` line |

Do not add analysis-plan contents, run manifests or graph edges to the map. `analysis-plan.md` is authoritative for analytic commitment; `.research/runs/` for executions; `research-graph` derives lineage.

## `init`

Build a map from an existing protocol and decision log. Fill only state that belongs in the map. Every gate starts `pending` and becomes `reached` only when the artifact the gate produces exists and the gate row points to it. Finish with `validate`.

## `resume`

Use this mode when resuming active research work. Consult the map and the authoritative artifacts permitted for the action, phase and audience. Return the question, permitted conclusion, decisive evidence, main limitation, next action, material blockers and last change. Run the fast integrity subset `--only map,plan,runs,exposure`. Full validation is reserved for commits, native review and publication. Do not imply a conclusion merely from a gate state.

A stale map never outranks current executable/source evidence. If map narrative conflicts with current code/data/artifacts, surface the contradiction, use verifiable current evidence and preserve the correction.

## Study views

From the study directory, use the installed dispatcher to inspect recorded material offline. In the commands below, set `RESEARCH_MAP_DIR` to the absolute parent directory of this installed `SKILL.md`. Resolve it from the skill path supplied by your host. In Claude Code you can use `RESEARCH_MAP_DIR="${CLAUDE_SKILL_DIR}"` while this skill is active. Keep the study as the working directory. For any output sent to a model, select `--audience model` in either format. Use `--audience local` for direct human inspection. Apply the study's [capability policy](reference/capability-policy.md) to sources and quoted material.

For status, explanation and impact, answer solely from the view, including when coverage is partial or a source is unsupported. The view applies source permissions and phase boundaries. Opening the map, manuscripts or results separately, invoking operational resume or running validators to complete the answer can expose blinded or restricted outcomes.

```bash
python3 "${RESEARCH_MAP_DIR}/scripts/research.py" view status --root . --audience model
python3 "${RESEARCH_MAP_DIR}/scripts/research.py" view explain C1 --root . --audience model --format json
```

The status field describes query coverage. A scientific judgment needs a source, scope and author. Use the selector from the response when a short ID identifies several occurrences. For a changed study resource, pass its selector to `view impact` with the same root and audience. Inspect the reported support paths, remaining evidence and coverage before recording a revised judgment. A newly discovered dependency may need to be recorded first.

For a standalone manuscript, use `view status --document FILE --audience model` or `view explain SELECTOR --document FILE --audience model`. The dispatcher reads UTF-8 text directly. An optional `--review REPORT` supplies a separate text review whose first nonblank line is `Document-SHA256: <64 hex digits>` for the exact manuscript bytes. Distinguish what the author reported, what the reviewer reconstructed and what a recorded execution reproduced. A missing judgment is a gap. When the user requests an assessment, follow the appropriate study or [external review procedure](../scientific-method/reference/external-review.md). For a PDF review, inspect authorized pages and cite their locations.

## `update`

Update only on observable events: gate state/evidence changed, hypothesis terminal state changed, registration changed, a material number was corrected, or a commit is about to record those changes. Keep `Gates`, `Hypotheses`, `Question` state and `Last session` synchronized with their authoritative artifacts; never copy result prose into the map. Run `validate` after the update.

## `validate`

Run the composed 0.11 validator:

```bash
python3 "${RESEARCH_MAP_DIR}/scripts/validate_all.py" RESEARCH.map --offline
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

When `.research/assessments/` exists, full validation also checks `assessments`: schema, versioned answer domain, exact evidence-text digest and append-only history. When `.research/executions/` exists, it checks `executions`: prospective command/resource/output contracts and append-only history. When `.research/policy.json` exists, it checks `policy`: unambiguous repository-relative resource selectors and explicit egress decisions. Projects without these optional artifacts keep the previous validation behavior.

A check with nothing to examine reports `NOT_VERIFIED`, never `PASS`. Exit is nonzero on `FAIL`; `--strict` also treats `NOT_VERIFIED` as failure.

Use `--only` to isolate checks, for example:

```bash
python3 "${RESEARCH_MAP_DIR}/scripts/validate_all.py" RESEARCH.map --offline --only plan,runs,lineage,exposure
```

Mechanical `PASS` means only that those invariants passed. It never means the design, method or claim is scientifically true.

For a run with a recorded replay recipe, computational regeneration is a separate check:

```bash
python3 "${RESEARCH_MAP_DIR}/scripts/replay.py" RUN-4 --root .
```

It returns `EXACT`, `DRIFT`, `ERROR`, or `NOT_VERIFIED`. Replay is useful evidence, not a prerequisite for a scientifically valid run; restricted data, expensive computation or unavailable historical environments may legitimately remain `NOT_VERIFIED`.

## Boundaries

A number belongs in an aggregate; a scientific commitment in protocol/analysis plan; a methodological choice in the decision log; an execution in a run receipt; a claim in the manuscript. Lineage is derived on demand. The map only points to current state and next action.

## Versioned decision supervision (opt-in)

The runtime and schemas belong to this skill. In initialized projects, read `reference/supervision.md`; the public runtime dispatcher is `scripts/research.py`. Resume also calls `supervise resume` to expose changed eligibility and unfinished operations; include `supervision` in the fast validation subset. Full validation automatically includes it when project identity exists. Preserve the distinction between historical, pending and current state when updating the map.
