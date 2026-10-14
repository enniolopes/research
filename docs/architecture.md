# Ownership and change boundaries

Research has one public interaction (`scientific-method`) and two different forms of state: authoritative project artifacts and disposable projections. Organize changes by the meaning they own, not by a new folder framework.

| Meaning | Owner | What consumers do |
|---|---|---|
| Scientific scope, creative exploration and consequential-action routing | `skills/scientific-method/SKILL.md` and entered phase reference | Route before a material action; keep ordinary interaction natural |
| Supervised lifecycle, role handoff and operational limits | `skills/research-map/reference/supervision.md` | Read when supervision is initialized; point here rather than duplicate the procedure |
| Mechanical contract shapes and rules fingerprint | `skills/research-map/scripts/contracts.py` | Import; exported schemas are generated and checked against this definition |
| Identified Git bytes and applicability | `resources.py`, shared `git_integrity.py` | Resolve, verify or report unavailable bytes; do not infer scientific adequacy |
| Cooperative operation effects, idempotency and crash visibility | `events.py` | Keep transient journal outside the worktree; commit authoritative events explicitly |
| Record loading, immutable-history integrity and decision state | `supervision_state.py` | Build a fresh Store for a new snapshot; never persist projected states as evidence |
| Bounded review applicability and package eligibility | `review.py`, `release.py` | Evaluate exact supplied evidence/coverage; ask a real reviewer for semantics |
| Command execution and admission orchestration | `supervise.py`, public `research.py` dispatcher | Compose existing checks and domain evaluators; emit truthful effects |
| Historical analytic and versioned decision navigation | `research-graph/scripts/graph.py`, `decision_graph.py` | Derive the appropriate view from authoritative records; report candidate consequences |

The same history predicate checks typed records and legacy RUN/EXEC/ASMT; restoration cannot hide committed mutation. Standalone import fallbacks preserve the existing script-loading interfaces.

Keep the existing script paths: they are referenced by installed skills, CI and users. The small dispatcher is the user-facing runtime entry; domain modules do not import CLI/orchestration. Release evaluation queries the Store for applicable review/adoption, while Store dispatches release state to that evaluator. This is a bounded query dependency, not a second store; lower-level contracts/resources/events/review/graph remain independent of orchestration. Review-resolution recursion detects cycles.

Scientific review and engineering verification have different owners. `reviewer-2` returns judgments without editing. The orchestrator persists its output and the actual provenance witness. Repository tests exercise deterministic mechanics; neither an engineering test pass nor a reviewer model's fluent answer establishes scientific truth.

## Verification near the change

- Contract/effect/applicability/admission changes: `python -m unittest discover -s tests -p test_supervision.py -v`.
- Instruction navigation or dependency direction: `python -m unittest discover -s tests -p test_instruction_topology.py -v`.
- Existing provenance/replay/legacy graph: their focused test files, then the full suite used by CI.

The path check validates operational file pointers in skills, phase references and agents against the installed layout. It does not judge natural-language instructions or model compliance. The dependency check keeps schema, byte verification, journal, review and graph primitives from importing orchestration. Do not replace scientific checks with these structural checks.

## Evolution criterion

A new abstraction, persistent state or host hook needs an observed failure it solves and a check that would reject the failure. Reduce copied procedure before adding new instruction layers. Preserve old empirical records; supersession closes a historical decision without erasing it or treating its retired state as missing evidence. A stale active judgment remains unresolved, and restoring bytes never erases a committed rewrite.

Immutable-history validation performs Git queries proportional to record/history size. Optimize it when measured cost becomes material, preserving mutation detection. Native agent adapters, scientific efficacy and real-agent UX require their own validation; the operational limits live in `../skills/research-map/reference/supervision.md`.
