# Target architecture

## Product boundary

The product is a persistent **Research Core**, not an LLM, website or MCP server. LLMs are cognitive workers; the website is a cockpit; MCP/HTTP are integration boundaries.

```text
                         User
              +-----------+-----------+
              |           |           |
            Web UI       CLI      AI hosts/IDEs
              |           |           |
              +------ HTTP/MCP --------+
                          |
                    Research Core
      +-------------------+-------------------+
      | orchestrator | world model | control |
      | scheduler    | claims      | tasks   |
      +-------------------+-------------------+
                          |
       +------------------+------------------+
       |                  |                  |
  AI workers        Execution engine     Evidence engine
       |                  |                  |
       +------------------+------------------+
                          |
                   Scientific ledger
             Git + DB + artifacts + logs
                          |
                   Semantic compiler
                          |
              trace / map / argument / export
```

## Core responsibilities

Research Core owns:

- project identity and lifecycle;
- compact active world model;
- scientific task scheduling;
- control-state transitions and preflights;
- evidence and claim admission;
- execution registration;
- model/tool routing;
- durable event history;
- query interfaces for status, why, changed, trace and map.

It does not own scientific values that require human authority.

## Persistence

Initial target:

- **Git/filesystem**: scientific artifacts, code, decisions, plans, documents, reproducible aggregates.
- **PostgreSQL**: active world-model state, tasks, events, indexes, locks and operational relations in deployable mode.
- **SQLite**: acceptable embedded/local implementation behind the same persistence interface for early slices.
- **Object/filesystem storage**: large data, PDFs, logs and execution outputs.
- **Vector retrieval**: optional and initially implemented with the primary database when practical; it is an index, never truth.

No graph database is required until real query/performance evidence justifies one.

## Local-first, deployable later

The architecture should support a local daemon/service colocated with a research repository and later support server deployment. Sensitive data and execution should be able to remain local while model/search calls are brokered through controlled adapters.

## Model gateway

Models are selected by capability and task, not hard-coded identity. The gateway should eventually support at least:

- high-reasoning tasks;
- economical screening/ranking tasks;
- code-oriented work;
- long-context evidence synthesis.

Scientific state must remain stable when the provider changes.

## Scheduler

The scheduler may run independent tasks in parallel, but parallelism must preserve scientific dependency and exposure rules. More agents are not automatically more independent; independence comes from role, objective and information separation.

## Interfaces

- HTTP/API for first-party UI and automation.
- MCP for external AI clients and IDEs.
- CLI for local lifecycle, diagnostics and scripting.
- Web UI for world-model navigation, tasks, evidence, map and audit.

The interface contract should remain thin over Research Core rather than duplicating scientific logic.