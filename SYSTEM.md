# Research system constitution

This document is the stable memory of the product. Implementation may change; these invariants require explicit architectural review and a superseding ADR.

## Mission

Build a scientific operating system that lets AI conduct rigorous, useful, long-horizon empirical research: formulate important questions, search and read evidence, generate and contrast hypotheses, execute code against identified data, falsify attractive explanations, update a persistent scientific model, and make only claims that are supported by inspectable lineage.

The objective is not to produce elegant schemas, papers, or plausible prose. The objective is to produce reliable scientific knowledge and useful uncertainty reduction.

## Scientific kernel

The behavioral kernel is:

```text
EXPLORE -> COMMIT -> EXECUTE -> JUSTIFY -> CHALLENGE
```

Five laws remain foundational:

1. **Evidence outranks narrative.** Inspected or executed evidence outranks memory, confidence and explanation.
2. **Commitment precedes exposure.** Consequential confirmatory choices are recorded before the result that could influence them.
3. **Discovery is not confirmation.** Evidence that generated or selected a hypothesis cannot silently become independent confirmation of it.
4. **Claims require lineage.** A material claim must trace through an explicit inference to identified result/source evidence and the design that licenses the inference.
5. **Material claims face an adversary.** The process that built a material claim is not sufficient to release it.

## Product invariants

### 1. Do science before describing science

When a proposition can be checked by search, inspection or execution, the system prefers doing that work over explaining what probably would happen.

### 2. Results are execution products

A scientific number or computed result is not created by model text. It is created by an execution against identified code, inputs and environment, with durable provenance.

### 3. Creativity is protected before commitment

Exploration may be divergent, speculative and structurally creative. The system becomes restrictive at consequence boundaries: commitment, result exposure, plan change, claim and publication. A novel post-result idea is not forbidden; it is routed honestly.

### 4. Artifacts are the scientific source of record

Human-readable, Git-versioned scientific artifacts and immutable execution evidence remain authoritative. Databases, indexes, graphs, embeddings and views are operational or derived state and must be rebuildable where practical.

### 5. The world model is not the ledger

The **scientific world model** is a compact active model of what is currently known, unknown, contested and worth testing next. The **scientific ledger** is the complete durable evidence and history. Do not put the whole ledger into model context.

### 6. Agents do not write truth directly

Agents produce candidate hypotheses, observations, evidence, analyses, critiques and proposed state transitions. The control system admits them into durable scientific state only under the relevant evidence and transition rules.

### 7. Model providers are replaceable

Research must not depend conceptually on one LLM vendor. Models are cognitive workers selected by task; the scientific state and rules belong to Research Core.

### 8. Semantic infrastructure is silent

PROV/P-Plan or any successor semantic model exists to improve provenance, interoperability and queries. The AI researcher and user do not perform semantic bookkeeping. If a semantic fact can be deterministically compiled from an artifact already needed for good science, it must be compiled.

### 9. Views are disposable

Mindmaps, argument maps, traces, dashboards and semantic graph serializations are projections of authoritative state. They are never parallel sources of truth.

### 10. Structure must earn its cost

Every new required field, artifact, gate, agent role or infrastructure component must prevent a concrete failure, unlock a necessary scientific capability, or materially reduce cognitive/operational cost. Architectural elegance alone is insufficient.

## Human authority boundary

Research may autonomously inspect, search, read, compute, reproduce, test, challenge and document. It must not invent human authority over scientific importance, ethics approval, authorship, institutional policy, venue decisions, or domain meaning that cannot be recovered from evidence.

Ask the human only for the smallest decision that changes the scientific objective, interpretation, authority or permitted action.

## Target system shape

```text
Human quest
    |
Scientific Orchestrator
    |
+---+-------------------------+
| Discovery | Evidence | Execution |
+---+-------------------------+
    |
Scientific World Model
    |
Next-best test <-> Control / Falsification
    |
Scientific Ledger
    |
Semantic compiler/index
    |
trace / map / argument / export
```

The public product may expose web, CLI, MCP and host-specific integrations. None of those is the scientific core.

## Anti-goals

Research is not:

- a paper generator;
- a graph-of-thought archive;
- a universal ontology of the world;
- a permanent swarm of agents;
- a significance-maximization engine;
- a system that scores its own confidence from model intuition;
- a system where passing validation means a claim is scientifically true;
- a system where infrastructure consumes more attention than evidence and execution.

## Success criterion

With equal or lower scientific effort, the system should make an AI more capable of producing relevant hypotheses, inspecting more useful evidence, executing correct analyses, detecting false explanations, preserving long-horizon coherence, reproducing results and making narrower, better-supported claims.

If provenance improves while discovery, execution or scientific quality worsens, the architecture has failed.