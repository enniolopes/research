# ADR 0001 — Research Core is the product

**Status:** Accepted

## Decision

Build a persistent headless Research Core that owns scientific state, control and orchestration. Web, CLI, MCP and host-specific skills are clients/adapters.

## Rationale

If scientific logic lives inside a prompt, website or one LLM provider, changing the interface changes the method and long-horizon state is fragile. Core must survive model/client replacement.

## Consequences

- models are workers, not the database of record;
- UI/MCP cannot bypass scientific control;
- first vertical slices may expose only minimal interfaces while Core contracts stabilize.