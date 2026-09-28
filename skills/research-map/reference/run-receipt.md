# Run receipt contract

`.research/runs/RUN-<n>.json` is an append-only receipt describing one material execution. It is evidence about a run commit, not part of that commit.

## Common fields

```json
{
  "id": "RUN-1",
  "mode": "confirmatory",
  "hypothesis": "H1",
  "estimand": "E1",
  "test": "T1",
  "commit": "<run-output commit>",
  "inputs": [{"id": "DATA1", "path": "data/input.csv", "role": "confirmatory"}],
  "outputs": [{"result": "R1", "artifact": "aggregates/r1.json"}]
}
```

`mode` for new runs is `confirmatory | exploratory`. Input role is `discovery | confirmatory | validation`. The validator also accepts historical `mode: validation` receipts and legacy `analysis_role` fields on non-confirmatory receipts so append-only history never requires rewriting; those fields confer no confirmatory authority.

Exploratory runs omit `analysis_role`; their receipt records what happened without certifying it against the current confirmatory plan.

## Confirmatory fields and order

Confirmatory receipts additionally require:

```json
{
  "analysis_role": "primary",
  "registration": "<recorded registration reference>",
  "protocol_freeze": "<commit>",
  "analysis_plan_freeze": "<commit>",
  "execution_freeze": "<commit>"
}
```

`analysis_role` is `primary | sensitivity | specification | diagnostic`.

Operational order:

1. freeze protocol and analysis plan;
2. ensure tracked implementation/configuration/declared inputs are clean and ready;
3. commit that state as `execution_freeze`;
4. execute without editing those tracked ingredients;
5. commit only declared output artifacts as `commit`;
6. write and commit the receipt referencing both hashes.

The validator requires scientific freezes ≤ execution freeze < run commit, inputs present at execution freeze, no confirmatory input/output path overlap, and only declared outputs changed across the execution boundary. Each declared output must cross that boundary. Artifact drift checks are byte-exact, including binary outputs.

The first committed version of a RUN receipt is authoritative. Corrections get new RUN/R identities.

## Replay

Optional:

```json
"replay": {
  "command": ["uv", "run", "--frozen", "python", "analysis/h1.py"],
  "environment": ["pyproject.toml", "uv.lock"]
}
```

Replay executes in a temporary detached Git worktree at `execution_freeze` and byte-compares declared outputs with the run commit. Status is `EXACT | DRIFT | ERROR | NOT_VERIFIED`.

`EXACT` proves regeneration under the available runtime; it does not prove scientific correctness. Git ancestry/diff also cannot prove that no ignored, untracked, external, secret or human-observed state influenced the original process. Those limits are disclosed rather than converted into false certainty.

Legacy committed receipts without `execution_freeze` remain historical and degrade this guarantee to `NOT_VERIFIED`; do not rewrite them.
