# Target architecture

## Product boundary

The product is a persistent **Research Core**, not an LLM, website or MCP server. LLMs are cognitive workers; the website is a cockpit; MCP/HTTP/CLI are adapters.

The architectural center is the Research Protocol and the durable Scientific Ledger, not a particular database or agent framework.

## Control plane and work plane

```text
                         User / clients
                    Web · CLI · MCP · API
                              |
                    RESEARCH CONTROL PLANE
          +-------------------+------------------+
          | Research Protocol | admission/policy |
          | scheduler         | world projection |
          | task authority    | query services   |
          +-------------------+------------------+
                              |
             commands / tasks | observations / receipts
                              |
                    SCIENTIFIC WORK PLANE
        +---------------------+---------------------+
        | AI workers | Evidence engine | Execution |
        +---------------------+---------------------+
                              |
                      SCIENTIFIC LEDGER
          artifacts + execution evidence + events
                              |
                    projections / indexes
        world model · semantic graph · map · trace
```

The **Control Plane** decides which attempted changes may become accepted scientific state. The **Work Plane** performs bounded work that can generate evidence, execution receipts, critiques and proposals. Work-plane outputs do not become accepted state merely because a model produced them.

## Authority matrix

One meaning has one authority:

| Meaning | Authoritative representation | Derived/operational representations |
| --- | --- | --- |
| Protocols, plans, decisions, code, authored scientific commitments | Git-versioned scientific artifacts | DB metadata, semantic graph, UI |
| What actually executed and what it produced | immutable execution receipt + referenced immutable outputs/logs | run indexes, summaries, graph |
| Accepted control transition, exposure, approval, rejection, supersession, task outcome material to state | append-only control event log | current-state tables, world model, UI |
| Current active scientific orientation | derived world-model projection | prompt context, UI cards |
| Semantic/retrieval relations | compiled index | graph/vector engine |

The Scientific Ledger is the union of the first three authoritative classes. Storage technology may differ; semantic authority may not.

## Research Core responsibilities

Research Core owns:

- project and scientific entity identity;
- command validation and accepted state transitions under `research-protocol.md`;
- authority/capability envelopes;
- scientific task scheduling and dependency/exposure rules;
- evidence, result, inference and claim admission;
- execution registration and receipt validation;
- durable accepted-event history;
- world-model projection/reconciliation;
- query services for status, why, changed, trace and map;
- model/tool routing without giving providers authority over state.

It does not own scientific values that require human authority.

## State flow

```text
client/worker proposes command or observation
              |
              v
       validate identity, authority,
       target version and prerequisites
              |
        +-----+------+
        |            |
      reject       accept
                     |
       persist required evidence/receipt
                     |
          append accepted domain event
                     |
             update/rebuild projections
          world model / tasks / graph / UI
```

For a material transition, durable evidence must exist before or atomically with the accepted event that relies on it. A projection failure never invalidates the accepted ledger event; projections are repairable.

## Persistence

Initial implementation should minimize infrastructure while preserving semantic interfaces:

- **Git/filesystem** for scientific artifacts and code;
- **SQLite** is preferred for the first vertical slice for the control event log, projection tables, task metadata and locking/version checks;
- **filesystem/object storage** for immutable outputs, source files and larger logs;
- **PostgreSQL** is a deployable replacement when concurrency/operations justify it behind the same semantic contracts;
- **vector retrieval** is optional and derived;
- no graph database until query/performance evidence justifies one.

This is not a mandate to implement event-sourcing infrastructure. It is a semantic requirement that accepted control transitions be durably append-only and projections rebuildable.

## Local-first, deployable later

The same Control Plane contract should support:

- all-local operation;
- local control + local private execution + remote model/search adapters;
- deployed control plane + authorized local execution workers;
- later distributed workers without changing scientific semantics.

## Task, not persona, is the scheduling abstraction

The primary unit is a **Scientific Task** with role, goal, target state, permitted context/evidence, capability envelope, expected output type, stop condition and budget. A model/agent is selected to execute the task. Roles described in `agents.md` are epistemic functions, not permanent services.

## Dependency direction

Adapters -> application/control services -> protocol/domain model.

Work-plane adapters implement capabilities required by tasks and cannot import UI/MCP concerns into scientific semantics. Projections depend on accepted ledger state, never the reverse.

## Interfaces

- HTTP/API for first-party UI and automation;
- MCP for external AI clients and IDEs;
- CLI for local lifecycle, diagnostics, export and repair;
- Web UI for scientific orientation and audit.

Interfaces remain thin over Core so changing a client cannot bypass the Research Protocol.
