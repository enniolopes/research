---
name: research-graph
description: Derive and query claim/result/run/test/data lineage from authoritative research artifacts. Internal navigation utility; it writes no source-of-truth or cache.
license: CC-BY-NC-4.0
metadata:
  version: 0.11.0
argument-hint: '<build | trace NODE | why NODE | changed NODE> [RESEARCH.map]'
---

# Research graph

This is a deterministic projection, not an artifact of record. Every query rebuilds from the current authoritative files; nothing is written to `.research/graph.json`.

The projection contains only identities it can actually derive:

`H` hypothesis · `E` estimand · `T` test · `A` assumption · `K` check · `DATA` input/exposure · `RUN` execution · `R` result · `C` claim.

Relations are limited to:

`estimates`, `tests`, `requires`, `checked_by`, `fallback_to`, `executed_as`, `uses`, `produces`, `supports`, `generated_from`.

Material claim annotations are:

```text
<!-- claim:C1 result:R1 -->
<!-- claim:C2 result:R2 decides:H1 -->
```

Legacy annotations containing `inference:I<n>` are accepted but the inference token is ignored; it never carried an independent artifact. Scientific adequacy of the bridge from result/design/checks to wording remains reviewer judgement.

Useful queries:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/graph.py" trace C1 RESEARCH.map
python3 "${CLAUDE_SKILL_DIR}/scripts/graph.py" why T1 RESEARCH.map
python3 "${CLAUDE_SKILL_DIR}/scripts/graph.py" changed DATA1 RESEARCH.map
```

`trace` walks a claim toward executed evidence and planned test. `why` walks prerequisites. `changed` reports candidate downstream consequences after a changed datum/result/assumption; it is navigation, never automatic invalidation.

The current analysis plan is not historical truth for old runs. Historical decisions use the run's recorded freezes and source inspection, not this projection.
