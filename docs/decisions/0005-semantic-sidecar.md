# ADR 0005 — PROV/P-Plan as semantic sidecar

**Status:** Accepted

## Decision

Use PROV-O and P-Plan as the conceptual basis for execution/prospective provenance, plus a minimal Research profile for scientific semantics, but compile this model from ordinary research artifacts rather than making users/agents author it directly.

## Rationale

The standards reduce reinvention of plan/execution semantics, while manual ontology bookkeeping would compete with scientific work.

## Consequences

- runtime storage need not be RDF;
- semantic graph is derived/indexed state;
- research-specific ontology grows only from demonstrated scientific/control needs.