---
name: research-graph
description: Build and query the derived epistemic graph of a research repository. Reconstructs hypothesis, estimand, test, data exposure, run, result, inference, claim and source lineage from authoritative artifacts; the graph is a disposable index, never a second source of truth. Use internally for claim preflight, adversarial review, trace/argument views, and questions such as why a result exists or what it changed.
license: CC-BY-NC-4.0
metadata:
  version: 0.9.0
argument-hint: '<build | trace NODE | argument CLAIM | why NODE | changed NODE> [RESEARCH.map]'
---

# Research graph

The repository artifacts are authoritative. The graph only stores identity and relations that can be reconstructed from them. Never repair an inconsistency by editing the generated graph; repair the source artifact and rebuild.

Node kinds in this version are limited to:

`H` hypothesis · `E` estimand · `T` test · `A` assumption · `K` check · `D` decision · `DATA` dataset/exposure · `RUN` execution · `R` result · `I` inference/warrant · `C` claim · `SRC` source.

Relations are limited to:

`estimates`, `tests`, `requires`, `checked_by`, `fallback_to`, `executed_as`, `uses`, `produces`, `derived_from`, `supports`, `challenges`, `supersedes`, `appears_in`, `generated_from`.

Run:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/graph.py" build RESEARCH.map
```

The generated `.research/graph.json` is a cache and may be deleted. Build it before review or a lineage query when source artifacts changed.

Queries:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/graph.py" trace C1 RESEARCH.map
python3 "${CLAUDE_SKILL_DIR}/scripts/graph.py" argument C1 RESEARCH.map
python3 "${CLAUDE_SKILL_DIR}/scripts/graph.py" why T1 RESEARCH.map
python3 "${CLAUDE_SKILL_DIR}/scripts/graph.py" changed RUN-001 RESEARCH.map
```

`trace` returns the claim's path toward executed evidence and plan. `argument` shows support/challenge neighbors. `why` walks prerequisites; `changed` follows relation direction semantically (a dataset is used by a run; an assumption is required by a test) to report potential consequences. Fallback alternatives are not executed dependencies. Queries traverse all reachable recorded dependencies with cycle protection.

The projection reads the current plan and run metadata; it does not reconstruct each historical frozen plan. Verify that plan before a historical claim decision. A bibliography node alone does not link a source to a claim; unrecorded dependencies require source inspection. Views are navigation aids, not evidence or automatic invalidation. After changes inspect surviving support, record the disposition in authoritative artifacts and refresh affected review; never propagate falsity just because one supporting path was challenged.

## Claim annotation

Material manuscript claims use a compact source annotation:

```text
<!-- claim:C1 inference:I1 result:R1 -->
```

A hypothesis-deciding claim also states:

```text
<!-- claim:C2 inference:I2 result:R2 decides:H1 -->
```

The result's run supplies the test, hypothesis and estimand. The inference node represents the public warrant from result + design + checks to wording; its semantic adequacy is reviewed adversarially, not mechanically proven.

## Exposure

An analysis-plan hypothesis may state `Generated from: DATA1, DATA2`. Run manifests identify input datasets and their epistemic roles. The graph records both `generated_from` and `uses`; the validator rejects independent-confirmation claims that reuse the same discovery dataset in a confirmatory run.
