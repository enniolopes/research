# User and integration interfaces

## User experience principle

The internal architecture must not become the user's workflow. The user should be able to start with a question and converse naturally with a single scientific system.

Public concepts should remain minimal:

- start/open research;
- status;
- map;
- review;
- natural-language scientific requests.

## Web cockpit

The first-party web UI should expose scientific state rather than infrastructure administration:

- current question/quest;
- active and rival hypotheses;
- strongest support/challenge;
- anomalies and open questions;
- next-best test and rationale;
- evidence and analyses;
- permitted/blocked claims;
- decisions and review;
- derived interactive map.

Agent counts, ontology details and queue internals should be diagnostics, not primary UX.

## Conversation

Conversation is the command surface. The user speaks in scientific language; Research Core performs routing and control. Good interruptions ask only for real human scientific/authority decisions, not permission for routine search, inspection or checks.

## CLI

The CLI should primarily handle local lifecycle and diagnostics, for example project initialization/opening, service start/stop, status, export and repair. Exact commands are deferred until the first vertical slice establishes the runtime shape.

## MCP

MCP is an integration protocol, not the system. External AI clients should call Research Core capabilities and resources through a thin MCP adapter. Scientific rules remain in Core so they cannot be bypassed by switching clients.

## HTTP/API

The first-party UI and automation use an API over the same Core application services. Avoid implementing a second scientific workflow in the frontend.