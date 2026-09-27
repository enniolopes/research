# Phase 7 — Review

Sources located 2026-09-10, not yet read at source.

**When this applies.** Before submission, and on demand after any confirmatory run.

For third-party work without native artifacts, use `external-review.md` instead of reconstructing a fictitious native history. A report can be scientifically assessable without plugin-specific files.

**What it requires.**

- **Hand to the `research:reviewer-2` agent** with the brief exactly as its "Required
  brief" section lists it: protocol, decision log, manuscript, aggregates, notebooks,
  permitted read-only commands, and the checklist (STROBE; RECORD when the data are
  routinely collected). The reviewer does not inherit the author's reasoning. An inline
  self-review by the orchestrator is not an independent review.
- **Persist the returned review** under `.research/reviews/REVIEW-<n>.md`. Prepend the
  reviewed repository commit and manuscript path, then preserve the reviewer's returned
  `VERDICT / CLAIMS / FINDINGS / CHECKS RUN / NOT_VERIFIED / BASIS` content. The record is
  evidence that Phase 7 occurred; do not reconstruct one later from memory.
- **Freshness**: material manuscript/result changes after the recorded reviewed commit make
  the affected review stale. Re-run the independent reviewer before PUBLISH rather than
  treating the old verdict as current.
- **Reporting checklist**: STROBE for observational designs; RECORD in addition when the
  data are routinely collected administrative records (codes used, linkage, cleaning,
  access). Every item is answered or marked not applicable with a reason.
- **Every `FAIL` gets a response**: fixed (with the affected checks re-run) or rebutted in
  the decision log with rationale and revision condition.
- **Re-run affected checks** after any fix; a fix that changes a number reopens phase 6
  for the paragraphs that quote it.

If the separate reviewer capability cannot run, Phase 7 is `NOT_VERIFIED`; do not simulate
independence by reading the agent instructions or by having the authoring context review its
own work.

**The error it prevents.** A manuscript reviewed only by the person/process that wrote it;
a reviewer verdict that leaves no durable evidence; a stale review surviving material
changes; a checklist item skipped silently; a fix that changed a result nobody re-rendered.

**Exit gate.** A durable independent-review record for the current material manuscript/result
state with reviewer verdict `PASS`, or every `FAIL` has a logged response and the affected
checks have been re-run and re-reviewed where material.

**Sources.** von Elm et al. 2007 (STROBE). Benchimol et al. 2015 (RECORD). Munafò et al.
2017 (reporting, reproducibility and evaluation as levers of reliability).
