# RESEARCH.map schema

`RESEARCH.map` is a small operational index. It has exactly six canonical sections, in this order:

1. `Layout`
2. `Question`
3. `Hypotheses`
4. `Gates`
5. `Deferred`
6. `Last session`

Historical corrections belong in Git/decisions, data provenance with the data, verification commands in project documentation, and unresolved methodological choices in the decision log or a blocked gate.

## Layout

Required pointers: `protocol`, `decisions`, `aggregates`, `documents`, `notebooks`, `references`. Optional `floor` is the minimum public count allowed under `documents`. Paths are repository-relative and may not escape the repository root.

## Question

Contains one question line pointing to the protocol problem statement, plus:

```text
Problem: PENDING
Registration: none
```

After gate 1B:

```text
Problem: SHOWN | NOT_SHOWN | INCONCLUSIVE → `problem-brief.md`
```

No phase 3+ gate may be reached unless the premise required by the protocol is `SHOWN`.

## Hypotheses

```markdown
| Id | Prediction | Refutation | State | Pointer |
|---|---|---|---|---|
| H1 | ... | ... | — | `protocol.md#h1` |
```

Terminal states: `CONFIRMED | REFUTED | INCONCLUSIVE | BLOCKED | NOT_VERIFIED`. Keep the active portfolio intentionally small; the validator does not impose an arbitrary numeric cap.

## Gates

Exactly one row each for `1A`, `1B`, and `2` through `8`. States are `pending | reached | blocked`. A reached gate points to the artifact/evidence it produced. A blocked gate names what or who blocks it.

## Deferred

Each retained post-freeze idea is durable:

```text
- YYYY-MM-DD: <idea> — enters when: <condition>
```

## Last session

At least one dated state-change line and exactly one useful next action:

```text
- YYYY-MM-DD: <what changed>
- Next: <one concrete step>
```

## Decision log

A decision is an append-only block:

```markdown
### D-<n> · YYYY-MM-DD · <title>
<decision>
Rationale: <basis>
Revision condition: <what would reopen it, or why it is not revisable>
```

After commit, revise only through a later decision with `Supersedes: D-<n>`.

## Numeric and disclosure checks

Numbers in `documents` and in a locally based problem brief must exist in committed CSV/TSV/JSON aggregates at the quoted precision unless a line carries `<!-- rm:ignore: <reason> -->`. Presence is not provenance.

When `floor` is set, every integer cell in Markdown/CSV/TSV tables under `documents` is checked. Cells that are not counts require an explicit ignore reason on the line.
