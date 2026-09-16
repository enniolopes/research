# Provenance and semantic sidecar

## Decision

Scientific artifacts remain operationally canonical. Semantic representations are compiled sidecars.

## Semantic layers

Use standards where they remove custom semantics:

- **PROV-O** for retrospective provenance: entities, activities, agents, use/generation/revision.
- **P-Plan** for prospective plan semantics: plans, steps, variables and correspondence between planned steps and actual activities.
- **Research profile** only for scientific concepts not adequately represented by those standards, such as hypothesis, estimand, assumption/check, scientific decision, inference/warrant, claim and review.

This is a conceptual/interop contract, not a requirement that runtime storage be RDF.

## Compilation rule

If `analysis-plan.md` already identifies a primary test `T1`, the AI must not separately maintain `T1 a p-plan:Step`. The compiler derives it.

If a run manifest identifies `RUN-17`, code/input/output and `T1`, the compiler derives activity/entity relations and step correspondence.

## Research graph

The semantic graph is an index. It should support queries such as:

```text
trace <claim>
why <entity>
changed <event/result>
argument <claim>
map <scope>
```

It must be rebuildable from authoritative artifacts plus accepted durable state.

## RO-Crate

RO-Crate / Workflow Run RO-Crate are candidate interchange/export profiles, not the core authoring model. Adopt them when they improve portability or reproducibility packaging without adding authoring burden.

## Ontology growth rule

Do not add a research-specific node/relation because it is intellectually appealing. Add it only when a required scientific query/control cannot be represented correctly with existing artifacts and standards, and the gap is demonstrated by an evaluation.