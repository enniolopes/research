# Phase 6 — Writing

Sources located 2026-09-10, not yet read at source.

**When this applies.** Any prose that will leave the repository: manuscript, abstract,
registration text, slides, e-mail summarising results.

**What it requires.**

- **Argument before prose.** Write the claims, the reasons and the evidence for each as a
  list; then write paragraphs. One finding per paragraph.
- **Every number with an interval and a source table.** The manuscript renders from
  committed aggregates only; a number typed by hand is a claim, not a result. A number the
  map's `validate` reports has three exits: its aggregate is committed, or the line is
  marked `<!-- rm:ignore: <reason> -->` because it is not a result (a law's number, a
  funder's figure), or it leaves the text — and leaving changes what the document claims,
  so it is said in the report line, never done quietly to pass the check.
- **Every variable defined as its source defines it**, with the common misreading named
  (a variable labelled "without X" that is in fact a counterfactual simulation on the same
  units, not a different population, will be read as the population unless you say so).
- **Figure-level provenance.** Each figure names the notebook and the aggregate that
  produced it; the reviewer will check figure ↔ code ↔ data agreement.
- **Limitations stated, not discovered.** The limitations section is written from the
  protocol's known assumptions and the analysis's `NOT_VERIFIED` rows, before any reviewer
  finds them.
- **Reader structure.** Put the familiar at the start of the sentence and the new at the
  end; keep subject and verb close; one idea per sentence.
- **Projections, not editions.** Abstract, registration, slides and e-mails are generated
  from the protocol and the manuscript; they are never edited into disagreement with them.

**The error it prevents.** A number in the text that the code no longer produces; a
variable read the wrong way by a colleague; a limitation the reviewer finds first; an
abstract that drifts from the paper.

**Exit gate.** The manuscript renders from committed aggregates; every figure has
provenance; every variable has its definition and misreading; limitations section exists.

**Sources.** Gopen & Swan 1990 (reader expectations: topic and stress positions). Schimel
2012 (story structure). Heard 2016 (clarity, revision, responding to review). Booth et al.
2016 (claims, reasons, evidence, objections).
