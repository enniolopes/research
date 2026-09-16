# Evidence engine

## Mission

Convert questions about existing knowledge into inspected evidence rather than model recollection.

## Pipeline

```text
question/proposition
 -> query decomposition
 -> source discovery
 -> retrieve
 -> read relevant primary content
 -> extract proposition-level evidence
 -> record support/challenge/uncertainty
 -> contradiction search
 -> precedent/novelty search when required
 -> update scientific state through control
```

## Source states

Identity/reachability is not semantic support. A useful lifecycle is conceptually:

```text
DISCOVERED -> RETRIEVED -> READ -> USED_FOR_CLAIM -> REVIEWED
```

Do not require these labels in user-facing workflow unless they prevent an observed failure.

## Evidence record

A material evidence item should identify:

- source identity;
- the proposition being evaluated;
- inspected location/content reference;
- whether it supports, challenges or is neutral/ambiguous;
- scope and population relevant to the proposition;
- extraction agent/task and time;
- uncertainty/limitations that matter for use.

## Novelty

A novelty claim means no relevant precedent was found under a stated search scope and stopping rule. It never means the model does not remember a precedent.

## Retrieval discipline

The evidence engine should favor primary sources for scientific/methodological support where feasible and should preserve contradictory evidence rather than summarize it away.