# Execution engine

## Principle

Scientific results are products of identified execution, not model prose.

## Execution record

A material run should be able to reconstruct at least:

- project/research identity;
- run identity and role;
- governing frozen plan/test when applicable;
- code/commit identity;
- input identities/hashes and exposure roles;
- environment/runtime identity;
- exact command/entry point;
- randomness/seeds when applicable;
- exit status, stdout/stderr/log references;
- output identities/hashes;
- execution time and relevant resource metadata;
- result identities derived from the run.

## Isolation

Prefer isolated worktrees/sandboxes or equivalent execution boundaries so multiple workers cannot silently overwrite one another or mutate the evidence underlying another run.

## Reproducibility

For material computational findings, the system should eventually be able to rerun from committed artifacts in a fresh environment and compare material outputs. A result that cannot be reproduced under its declared conditions is not silently treated as verified.

## Safety and authority

The execution engine enforces allowed tools, filesystem/data boundaries, credentials, resource limits and network policy. The LLM does not bypass those controls.

## Relationship to Git

Git is the temporal evidence for plans, code and human-readable artifacts. The execution system records the exact repository state used. Database task state may be mutable; historical scientific execution identity must not be.