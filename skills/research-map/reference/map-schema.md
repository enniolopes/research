# RESEARCH.map — grammar

Markdown. Sections are `## ` headings in this exact order; `validate` fails on a missing
required section or a misordered one. Six sections are **required** — the state no other
file in the repository holds. Four are **optional**, validated when present, and hold only
what no file named in `Layout` already says: if the README or the protocol says it, point,
never copy. Pointers are backticked repository-relative paths, optionally with `#anchor`;
every pointer must resolve. Tables are GitHub-flavoured Markdown.

| Section | Required | Holds |
|---|---|---|
| `## Layout` | yes | where things are; the disclosure `floor` |
| `## Question` | yes | the question, `Problem:` state, `Registration:` |
| `## Hypotheses` | yes | one row each; at most three without a terminal state |
| `## Gates` | yes | one row per phase; every `reached` names its evidence |
| `## Facts that were once wrong` | no | the wrong value, the right one, the notebook that produces it |
| `## Provenance` | no | inputs the README or protocol do not already list |
| `## Verification` | no | commands, when no Makefile or README holds them |
| `## Open decisions` | no | undecided items not already a `blocked` gate row |
| `## Deferred` | yes | ideas that appeared after the freeze and were not admitted |
| `## Last session` | yes | a dated line per change and one `Next:` line |

```markdown
# RESEARCH.map — 2027-programme-coverage

## Layout
- protocol: research/2027-programme-coverage/protocol.md
- decisions: research/2027-programme-coverage/decisions.md
- aggregates: research/2027-programme-coverage/aggregates/
- documents: research/2027-programme-coverage/paper/
- notebooks: research/2027-programme-coverage/notebooks/
- references: research/2027-programme-coverage/references.bib
- floor: 5

## Question
Does enrolment in programme P concentrate service units toward the areas of greatest need N,
relative to the distribution inherited before P? → `research/2027-programme-coverage/protocol.md#question`
Problem: SHOWN → `research/2027-programme-coverage/problem-brief.md`
Registration: https://registry.example/record/12345, 2027-03-02

## Hypotheses
| Id | Prediction | Refutation | State | Pointer |
|---|---|---|---|---|
| H1 | C_after − C_before < 0 (P concentrates toward need) | interval includes 0 or sign > 0 under the primary test | INCONCLUSIVE | `research/2027-programme-coverage/protocol.md#h1` |

## Gates
| Phase | State | Blocked by | Evidence |
|---|---|---|---|
| 1A Problem — formulate | reached | | `research/2027-programme-coverage/decisions.md#d-3` |
| 1B Problem — demonstrate | reached | | `research/2027-programme-coverage/problem-brief.md` |
| 2 Literature | reached | | `research/2027-programme-coverage/references.bib` |
| 3 Protocol | reached | | `research/2027-programme-coverage/protocol.md#freeze` |
| 4 Data | reached | | `research/2027-programme-coverage/aggregates/linkage_report.csv` |
| 5 Analysis | pending | | |
| 6 Writing | pending | | |
| 7 Review | pending | | |
| 8 Publication | blocked | ethics approval — PI | |

## Facts that were once wrong
| Was | Is | Produced by |
|---|---|---|
| 1,204 service units | 1,377 | `research/2027-programme-coverage/notebooks/01_reconcile.ipynb` |

## Deferred
- 2027-03-01: spatial lag model as an alternative to the cluster bootstrap — enters when: H1 has a terminal state and the dependence check is reported

## Last session
- 2027-03-01: reconciled registry; 1,377 units (was 1,204); D-9..D-12 logged.
- Next: run 03_models in DRY_RUN; list the count model's assumptions before fitting (phase 5).
```

## Rules `validate` applies

- `Layout` keys are exactly `protocol`, `decisions`, `aggregates`, `documents`,
  `notebooks`, `references`; values are comma-separated paths that must exist. The optional
  `floor: <n>` is the minimum cell size for anything under `documents` (check `disclosure`).
  Keep the protocol out of `documents`: its design parameters (bounds, alpha, power) exist
  before any aggregate by construction.
- `Question` carries `Registration: none` or `Registration: <URL or DOI>, <date>`; while it
  is `none`, confirmatory code is `DRY_RUN`.
- The `Question` pointer leads to the protocol's problem statement: the section at that
  anchor must carry the labelled fields `Claim`, `Unit of analysis`, `Estimand`,
  `Refutation`, `Objection`, `Who cares`, `Non-goals` (scientific-method,
  `reference/problem-statement.md`). A label is read up to its colon: `**Estimand:**` and
  `★ Estimand:` pass, `**Estimand.**` does not.
- `Question` carries `Problem: PENDING | SHOWN | NOT_SHOWN | INCONCLUSIVE → `<brief>``. Unless
  `PENDING`, the brief file must exist and carry `Construct`, `Population`, `Measure`,
  `Reference`, `Magnitude`, `Falsification`, `Verdict` (scientific-method,
  `reference/problem-brief.md`); its `Verdict` must equal the map's state; its `Reference`
  names the decision `D-<n>` that fixed it, and that block must exist in the log; its
  numbers are checked against the aggregates like any document. No gate from phase 3 on may
  be `reached` while the problem is not `SHOWN`.
- Backticks are reserved for pointers: a repository-relative path (with `/` or a known
  suffix), optionally with `#anchor`. A backticked number or symbol is not a pointer.
- `Gates` has one row per phase, all eight; states are `reached`, `pending` or `blocked`.
  A `blocked` row names who or what blocks it in `Blocked by`. A `reached` row names in
  `Evidence` the artifact the gate produces — a pointer that resolves, or a DOI/URL — so a
  gate is reached by its artifact, never by the word.
- `Hypotheses` states are `CONFIRMED`, `REFUTED`, `INCONCLUSIVE`, `BLOCKED`,
  `NOT_VERIFIED`, or `—` before analysis. At most three rows may be `—`; a fourth is a
  scope failure until a logged decision names what leaves for it to enter.
- Every row in `Facts that were once wrong` has a `Produced by` pointer that resolves.
- `Deferred` holds what appeared after the protocol froze and was not admitted: each item
  `- YYYY-MM-DD: <idea> — enters when: <condition>`. It is the destination for a new method,
  concept or front that would otherwise open a parallel line of work; nothing leaves it
  except by a logged decision that reopens phase 3 or by becoming the next research.
- `Last session` has at least one dated line (`- YYYY-MM-DD: …`) and one `Next:` line.

## Decision log grammar (`decisions`)

Each decision is a block: a heading with id, date and title, then the rationale and the
revision condition. The title is what `resume` reads aloud.

```markdown
### D-11 · 2027-02-28 · cluster bootstrap over regions
Report the spatial dependence statistic alongside every interval.
Rationale: outcome is spatially clustered (dependence statistic 0.31, p < 0.001, notebook 03).
Revision condition: a dependence check on the final sample shows the statistic within the null band.
```

A block starts only at a heading (`### D-<n>`) or a bold id (`**D-<n>**`, `- **D-<n>**`);
a bare `D-<n>` in running text is a cross-reference, and `| D-<n> |` in a table row is not
a block — `validate` counts such rows and reports the check `NOT_VERIFIED`, since a row
cannot carry a revision condition. `validate` requires `Revision condition:` (or `Revise
when:`) with a value in every block (`—` or `none` is empty; a decision that cannot be
reopened says so in words), and ids unique and increasing in file order.

The log is append-only from the commit onward: a block not yet committed is a draft and may
be rewritten; a committed block is changed only by a later block carrying
`Supersedes: D-<k>`, which `validate` checks names an earlier block. Git history is the
check of append-only itself.

## Numbers rule (`documents` ↔ `aggregates`)

A number in a document is *present* when some numeric value in an aggregate file (`.csv`,
`.tsv`, `.json`) rounds to it at the quoted precision. Presence is not provenance: the check
reports what is absent from every aggregate; a number that is present still needs its
source table in the text (phase 6). Signs count: `-0.31` in the text matches only a negative value in the aggregates, so a
flipped sign is reported; a hyphen between two numbers (`0.55-0.67`) is a range, not a sign. Thousands separators (`1,377`, `1.377`) and decimal commas (`0,61`) are
normalised; a token ambiguous between pt-BR thousands and three decimals (`1.377`) matches
on either reading, and a leading zero (`0.125`) is never read as thousands.

Ignored by default: integers below 20; four-digit years 1900–2100; identifiers glued to a
letter (`D-37`, `H1`, `F10`); the number of a legal instrument (`Lei 14.628`, `Decreto nº
11.936`, `Directive 2016/679`, `Act 1.234`); thresholds after `p`, `alpha` or `α` and an
inequality (`p < 0.001`); labels after Section/Seção/§, Table/Tabela, Figure/Fig./Figura,
Eq., p./pp.; confidence levels (`95% CI`, `95% IC`); numbers inside ``` or ~~~ fences; the
span of a URL or DOI (the rest of the line is still checked); a line carrying
`<!-- rm:ignore: <reason> -->`. The marker needs its reason: a bare `<!-- rm:ignore -->`
is reported, and the check's summary counts the markers, so a document that earns its pass
by markers shows it. Aggregate files are read cell by cell (`, ; tab |` delimiters), JSON by
value. Everything else must be present or is reported with file and line. Manuscripts in
`.docx`/`.pdf` are out of scope; render to Markdown or `.qmd` first.

## Disclosure rule (`documents` ↔ `floor`)

Anything under `documents` is outside the analysis environment — including a table the
agent itself writes there. When `Layout` carries `floor: <n>`, every Markdown table and
every `.csv`/`.tsv` under `documents` is read cell by cell, first column excluded (it labels
the row); an integer cell between 1 and n−1 is reported with file and line. A cell that is
not a count (a rank, a model number) takes `<!-- rm:ignore: <reason> -->` on its line.
Without `floor`, the check is `NOT_VERIFIED`, never `PASS`.
