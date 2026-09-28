# Execution spec and local runner

An ExecutionSpec is a prospective declaration of one execution boundary. It exists before execution and says what command is intended to run, which committed repository files are declared inputs/environment, which files may be produced, and which egress capabilities are requested.

It is not a run receipt. A spec records intent; a RUN receipt records what actually happened.

## Artifact

Committed specs live under:

```text
.research/executions/EXEC-<n>.json
```

Example:

```json
{
  "id": "EXEC-1",
  "command": ["python", "analysis/h1.py"],
  "inputs": ["data/input.csv"],
  "outputs": ["aggregates/r1.json"],
  "environment": ["analysis/h1.py"],
  "capabilities": {
    "network_egress": false,
    "model_egress": false
  }
}
```

The first committed form is immutable. Change the command, resources, outputs, or capabilities by creating a new EXEC id.

Paths are exact repository-relative paths. Outputs must be non-empty and cannot also be inputs/environment. Commands are argv lists; the runner does not invoke a shell.

## Local runner

For executions that opt into this contract:

```bash
python3 <installed research-map>/scripts/execute.py validate --root .
python3 <installed research-map>/scripts/execute.py run EXEC-1 --root .
```

The local backend requires a completely clean Git work tree, including no untracked files. It then:

1. validates the spec;
2. requires the spec, inputs, and environment files to be committed at HEAD;
3. treats HEAD as the proposed `execution_freeze`;
4. checks the optional capability policy;
5. executes the argv directly;
6. verifies afterward that the only changed/untracked paths are exactly the declared outputs;
7. reports the freeze and output paths for the normal commit + RUN-receipt flow.

The runner does not create commits, rewrite files after failure, or fabricate a receipt.

## Enforcement honesty

The local backend provides an integrity boundary, not a confidentiality sandbox.

It can verify the repository diff after execution. It cannot prove that the process did not read another local file, use the network, send data to a remote model, or observe undeclared external state.

Therefore, when a capability policy forbids model/network egress for a declared input/environment resource and the spec says that egress is not requested, the local backend returns `NOT_ENFORCEABLE` instead of executing. A future isolated backend may satisfy that contract by physically removing the forbidden boundary.

Without a capability policy, local execution remains available for compatibility, but its outcome explicitly reports model/network egress as `not_enforced`.

## RUN binding

A RUN receipt may optionally include:

```json
"execution_spec": "EXEC-1"
```

When present, the recorded `execution_freeze` must contain that spec. The frozen spec's declared inputs and outputs must match the RUN receipt, and the execution-freeze → run-commit diff is enforced for that run.

This extends the execution boundary to exploratory runs that explicitly use an ExecutionSpec. Existing receipts without `execution_spec` retain their historical semantics.
