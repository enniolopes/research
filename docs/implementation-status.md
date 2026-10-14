# Supervisor v1 implementation status

The accompanying design spec is the target architecture. This PR implements the cooperative CLI core, strict versioned records, exact-byte review applicability, derived dependency projection, irreversible supersession/withdrawal history, reference authority declarations, local execution journal and release-package admission. It integrates supervision into composed validation only for initialized projects, preserving the existing runtime and project format.

## Verification

The post-merge regression suite includes 35 supervisor tests, 42 legacy/runtime tests and two instruction-topology tests (79 total). It exercises strict contracts/schema export, candidate-versus-consolidated admission, fresh-process release inspection, manuscript staleness, pinned/live bindings, missing or incompatible review, negative-review withdrawal, active reference changes, reserved core rules, restricted evidence/refresh deadlines, provenance/run import, output boundaries, idempotency, interrupted operation handling, Git history divergence, worktree locks, unsafe paths, derived graph routes, and unreviewed renders. A successful test checks the stated scenario; it does not certify scientific validity or complete every broader acceptance scenario in the design spec.

The [post-merge review](post-merge-review.md) records the demonstrated defects, fixes, verification scope and runtime cost.

## Intentionally unverified or deferred

- Native Claude Code and Codex interception and isolated reviewer launch: no native adapter is claimed. Skills instruct agents to use the cooperative CLI; direct host bypass remains possible.
- Scientific efficacy and interface friction: no ablation study or representative user/agent benchmark has been performed.
- External identity/expertise authentication and exposure outside instrumented execution: declarations remain declarations.
- Full prospective-choice migration, remote execution backends, automatic competent waivers and restricted-data verification inside an authorized environment: not implemented here.
- Full-text discovery of every material claim: the reviewer supplies coverage; the runtime validates the manifest and inventory.

These limits are reflected in runtime capabilities and documented behavior. Acceptance scenarios concerning native host enforcement, human UX, empirical efficacy or externally unavailable evidence remain pending rather than being counted as passed unit tests.
