# Research system constitution

This document owns the stable product invariants. Domain documents define operational semantics; ADRs explain material decisions and revision conditions. Implementation may change, but an invariant here requires explicit architectural review and a superseding ADR.

## Mission

Build a scientific operating system that lets AI conduct rigorous, useful, long-horizon empirical research: formulate important questions, search and read evidence, generate and contrast hypotheses, execute code against identified data, falsify attractive explanations, update a persistent scientific model, and make only claims supported by inspectable lineage.

The objective is not elegant schemas, papers or plausible prose. The objective is reliable scientific knowledge and useful uncertainty reduction.

## Scientific kernel

```text
EXPLORE -> COMMIT -> EXECUTE -> JUSTIFY -> CHALLENGE
```

Five laws are foundational:

1. **Evidence outranks narrative.** Inspected or executed evidence outranks memory, confidence and explanation.
2. **Commitment precedes exposure.** Consequential confirmatory choices are recorded before the result that could influence them.
3. **Discovery is not confirmation.** Evidence that generated or selected a hypothesis cannot silently become independent confirmation of it.
4. **Claims require lineage.** A material claim traces through an explicit inference to identified result/source evidence and the design that licenses the inference.
5. **Material claims face an adversary.** The process that built a material claim is not sufficient to release it.

## Product invariants

### 1. Do science before describing science

When a proposition can be checked by search, inspection or execution, prefer doing that work over explaining what probably would happen.

### 2. Results are evidence products

A scientific number or computed result is not created by model text. It is created by identified execution or identified external evidence with durable provenance.

### 3. Creativity is protected before commitment

Exploration may be divergent, speculative and structurally creative. Restriction concentrates at consequence boundaries: commitment, result exposure, plan change, claim and publication. A post-result idea is allowed but routed honestly.

### 4. One authority per scientific meaning

The **Scientific Ledger** is the durable basis of scientific state, but it is not one storage mechanism. Authority is assigned by meaning:

- Git-versioned scientific artifacts own human-readable plans, protocols, decisions, code and authored scientific commitments;
- immutable execution evidence owns what actually ran and what it produced;
- the append-only control event log owns accepted state transitions, exposures, approvals, rejections, supersessions and task outcomes that matter to scientific state.

No database convenience, projection or model narrative may become a second authority for the same meaning.

### 5. The world model is a projection, not the ledger

The **scientific world model** is a compact active projection of what is currently known, unknown, contested and worth testing next. It is rebuilt or reconciled from accepted ledger state and never becomes an independently editable source of scientific truth.

### 6. Workers propose; control admits

Workers produce candidate hypotheses, observations, evidence, analyses, critiques and proposed transitions. The Research Control Plane validates and durably admits or rejects state transitions under the Research Protocol. A worker does not promote its own narrative to accepted state.

### 7. Model providers are replaceable

Models are cognitive workers selected by task. Scientific identity, state and control rules belong to Research Core and must survive provider replacement.

### 8. Semantic infrastructure is silent

PROV/P-Plan or successors improve provenance, interoperability and queries. Users and AI researchers do not maintain semantic bookkeeping. Semantic facts deterministically inferable from required scientific artifacts or events are compiled.

### 9. Views are disposable

Mindmaps, argument maps, traces, dashboards, vector indexes and semantic graph serializations are projections. They can be rebuilt and are never parallel truth.

### 10. Structure must earn its cost

Every required field, artifact, gate, agent role or infrastructure component must prevent a concrete failure, unlock a necessary scientific capability or materially reduce cognitive/operational cost. Architectural elegance alone is insufficient.

### 11. Failure semantics are scientific semantics

Retry, concurrency, crash recovery, stale evidence, duplicate work, partial execution and data-egress controls must not be left to accidental infrastructure behavior when they can alter scientific state. Commands and accepted events are target-bound, version-aware and idempotent where repetition is possible.

## Human authority boundary

Research may autonomously inspect, search, read, compute, reproduce, test, challenge and document within its capability envelope. It must not invent authority over scientific importance, ethics approval, authorship, institutional policy, risk acceptance, venue decisions, sensitive-data release or domain meaning that cannot be recovered from evidence.

Ask the human only for the smallest decision that changes scientific objective, interpretation, authority, risk acceptance or permitted action.

## System shape

```text
Human / clients
      |
RESEARCH CONTROL PLANE
  Research Protocol
  admission + authority
  scheduler + world-model projection
      |
      +-----------------------+
      |                       |
SCIENTIFIC WORK PLANE     SCIENTIFIC LEDGER
 workers/tools             artifacts
 evidence/search           execution evidence
 execution                 control event log
      |                       |
      +-----------+-----------+
                  |
          accepted events/state
                  |
       projections and indexes
 world model / map / trace / argument
```

Web, CLI, MCP and host-specific skills are adapters. None is the scientific core.

## Anti-goals

Research is not:

- a paper generator;
- a graph-of-thought archive;
- a universal ontology;
- a permanent swarm of agents;
- a significance-maximization engine;
- a system that invents confidence scores from model intuition;
- a system where passing validation means a claim is scientifically true;
- a system where Git is forced to behave like a transactional queue;
- a system where infrastructure consumes more attention than evidence and execution.

## Success criterion

With equal or lower scientific effort, Research should make an AI more capable of producing relevant hypotheses, inspecting useful evidence, executing correct analyses, detecting false explanations, preserving long-horizon coherence, reproducing results and making narrower, better-supported claims.

If provenance or architecture improves while discovery, execution or scientific quality worsens, the architecture has failed.
