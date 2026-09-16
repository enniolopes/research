# Agent roles

Agents are task-scoped scientific workers created by Research Core. They are not permanent chat personas and do not own authoritative state.

## Candidate roles

### Discovery / hypothesis scientist

Generates structurally distinct mechanisms, hypotheses, rival explanations, anomalies and discriminating tests. Optimizes diversity and usefulness under evidence constraints.

### Evidence scientist

Searches literature and other authorized evidence sources, retrieves primary material, reads proposition-relevant content, records support/challenge and performs contradiction/precedent search.

### Methodologist / statistician

Clarifies estimand, design, dependence, missingness, identification, assumptions, checks, decision rules and interpretation boundaries.

### Execution scientist

Inspects data/code, proposes executable analyses, runs only through the execution engine, and reports outputs with provenance.

### Falsifier / null scientist

Attempts to destroy attractive findings through alternative explanations, implementation checks, null models and adversarial reanalysis. Its objective is not to help the originating hypothesis.

### Independent reviewer

Audits claims and scientific products from a separate information/role context. It does not edit the work it reviews and does not substitute for deterministic validation.

## Independence

Multiple workers using the same model are not independent merely because there are several calls. Create independence through:

- distinct objective functions;
- controlled information sets;
- separate execution when useful;
- explicit adversarial roles;
- hiding persuasive generator rationale from the falsifier/reviewer when it is not evidence.

## Task contract

A task should specify:

- goal;
- role;
- permitted evidence/context;
- tools/capabilities;
- scientific constraints;
- expected output type;
- stop condition;
- resource/compute budget when material.

Worker output should be typed as proposal, observation, evidence, artifact, result reference, critique or blocker rather than free-form truth.

## Adaptive compute

Use one worker for well-specified work. Expand search/debate only when uncertainty, importance, novelty or decision consequence justifies additional compute.