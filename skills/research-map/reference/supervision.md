# Scientific decision supervisor — experimental v1

The standard-library runtime adds deterministic admission to the existing empirical workflow. It does not replace scientific judgment. Existing projects remain compatible until `.research/project.json` is initialized; initialization does not migrate historical claims into adopted decisions.

## Action routing and ownership

Resolve plugin files relative to the installed skill directory; `--root` names the research project. Do not assume the plugin's scripts exist inside the project. The orchestrator owns intent and next action; this guide owns the supervised procedure; schemas/runtime own mechanical shapes and checks. Read only the phase and contract needed for the action.

| Boundary | Runtime operation | Role |
|---|---|---|
| Session continuation | `resume`, then the map's fast integrity subset including `supervision` | Orchestrator resumes current eligibility; incomplete operations require recovery |
| Confirmatory execution | `propose` → `run` for `FIT_CONFIRMATORY` | Orchestrator prepares frozen request; runtime executes/checks effects |
| Result admission | `import-execution`, ordinary RUN, `admit` for `ADMIT_RESULT` | Orchestrator preserves outputs and provenance before interpretation |
| Material claim adoption/revision | separate review → `propose`/`admit` for DEC | Reviewer judges; orchestrator persists; runtime admits |
| Scientific release | `propose`/`admit` for REL → commit → `release-inspect` | Orchestrator checks actual package; publication remains a separate authorized action |

The reviewer is read-only: supply artifact paths/commit, applicable REF criteria and review scope, not an argument for the author's preferred verdict. It returns the report and manifest; the orchestrator persists them without changing the judgment, computes the final report hash and validates the schema. Any correction affecting coverage or verdict returns to the reviewer. Obtain genuine operator/reviewer attestation separately; a manifest returned by a model does not prove context separation. `NOT_VERIFIED` remains visible when no supported witness exists.

Resolve mechanical omissions independently, batch related review and interrupt the user only for missing scientific judgment, authority or evidence the agent cannot supply. Report permitted conclusion, decisive evidence, limitation and next useful action; internal JSON stays behind the ordinary research interaction. Do not initialize or migrate an existing project's scientific decisions merely to clear a gate.

## Operator interface

Use the installed plugin's `skills/research-map/scripts/research.py` as the dispatcher:

```sh
python3 <research-map>/scripts/research.py supervise init --root .
# Commit .research/project.json before material actions.
python3 <research-map>/scripts/research.py supervise capabilities
python3 <research-map>/scripts/research.py supervise resume --root .
python3 <research-map>/scripts/research.py supervise propose --root . --request /tmp/action.json
python3 <research-map>/scripts/research.py supervise run --root . --request /tmp/action.json
python3 <research-map>/scripts/research.py supervise admit --root . --request /tmp/action.json
python3 <research-map>/scripts/research.py supervise validate --root . --strict
python3 <research-map>/scripts/research.py supervise release-inspect --root . --id REL-1
python3 <research-map>/scripts/research.py supervise graph --root .
python3 <research-map>/scripts/research.py validate RESEARCH.map --offline
```

Requests can arrive through stdin (`--request -`) so transport does not dirty an execution freeze. Request schemas live in `../schemas/`; Python `contracts` exports the same definitions, `CORE_VERSION` and `RULES_SHA256`. Use those constants rather than inventing a rules fingerprint. Resource descriptors bind a repository-relative regular file to a full Git revision and SHA-256 of its bytes; source snapshots also require URI and retrieval timestamp. `resources.resource()` constructs descriptors. IDs and all record fields are strict; unknown fields, duplicate JSON keys, non-finite numbers, invalid project IDs and fingerprints are rejected.

Responses separate `disposition` from `effect`: a successful check is not an execution; execution is not result admission; admission is not consolidation. Exit codes: 0 allowed, 1 unresolved gate, 2 invalid contract, 3 recovery required. Output is a single JSON object. Keep drafts, ideas and alternative explanations fluid; do not ask for approval merely to explore.

## Lifecycle

1. Commit the project identity, prospective protocol/analysis plan, execution specification and applicable reference contracts. A REF contains criteria, scope, required/advisory materiality, and an explicit human authority declaration. New admission cannot silently select a superseded REF, omit an active required REF, or bypass a required criterion by selecting only another criterion from that REF. The reserved core cannot be weakened through a project contract.
2. Propose `FIT_CONFIRMATORY` with a committed immutable execution ID, H, scientific freezes, registration matching the project and current base commit. `none`/`DRY_RUN` cannot authorize confirmatory result exposure. `run` preserves the existing clean execution freeze and exactly-declared-output diff check. Local logs and the operation journal live under the worktree's Git metadata, not in the working tree. Successful execution still needs a RUN receipt and scientific checks.
3. Commit only declared outputs. `import-execution --id <operation UUID>` then imports execution events; commit these and the ordinary RUN receipt. `ADMIT_RESULT` checks existing provenance/exposure invariants; it does not endorse a scientific interpretation. Failed execution retains possible exposure and must not be automatically retried with the same operation ID.
4. Obtain a real separate review. Commit its report, typed REVIEW manifest and explicit separation attestation. The manifest binds exact claim formulations, inspected evidence and versions, applicable criteria, coverage, limitations and findings. Negative reviews are legitimate diagnostics; they cannot support an adoption or release, but can support a justified withdrawal. An ASMT does not substitute for REVIEW.
5. Propose/admit a DEC containing exact target formulation, supporting routes, review judgments, interpretation limits and revision conditions. Record and final event are committed together. Until the whole event membership is committed and consistent, the DEC remains `CANDIDATE`. Existing adopted targets require explicit supersession. Withdrawal never silently resurrects an earlier claim, even if files return to earlier bytes.
6. Admit a REL only after all material claims and actual package resources are covered by current positive review and current adopted decisions. Rendered PDF/figures need coverage of their own bytes; reviewing only the source manuscript cannot certify the render. `release-inspect` performs no publication. A changed package invalidates release eligibility. Inspection also checks repository integrity and refuses eligibility for a candidate manifest, even when its scientific dependencies otherwise pass.

Use `pinned` for explicitly historical evidence, `follow_current` when changes to the named current path should invalidate applicability, and `external_refresh` for evidence needing a renewed external inspection before its deadline. The graph is derived on demand and includes reference contracts and release dependencies. Conjunctive support routes remain explicit; shared declared origins warn about overlap without proving statistical dependence. Affected queries identify review candidates, not automatic scientific verdicts.

## Trust and recovery

The CLI enforces its own execution/admission path. Direct shell actions, exposure outside its journal, and agent actions bypassing the CLI are not observed or contained. Native Claude Code/Codex interception, network/model isolation and hostile-process containment are `NOT_VERIFIED` or unsupported. Never fabricate an attestation, human authority, independent reviewer or host context to pass a gate. `attest` records an explicit operator declaration under cooperative trust; it does not authenticate identity, expertise or independence.

Locks are shared across worktrees for the same project; journals are worktree-local and request-bound. Completed operations are idempotent. Incomplete operations, history divergence and conflicting successors require recovery. Inspect the journal and actual outputs before creating a new operation; do not delete a stale lock merely because its timestamp is old. Missing or restricted bytes remain `NOT_VERIFIED`; declarations cannot turn unavailable evidence into checked evidence. v1 rejects symlinks, including in-repository symlinks, conservatively.

## Current limits

`CHANGE_COMMITMENT` supports the explicit `REOPEN` route; other prospective migration routes remain under the existing workflow and are not silently authorized. Required release obligations without a positive result block release; no automatic waiver is implemented. The runtime checks recorded coverage and scientific judgments, not whether a reviewer actually found every material assertion in arbitrary prose. Empirical evidence of better scientific outcomes, native agent end-to-end interception and external reviewer authentication require separate validation.
