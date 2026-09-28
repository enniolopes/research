# Problem brief

Gate 1B records the minimum evidence needed to decide whether the empirical premise motivating the research is established. It may rely on inspected external evidence or on local executed evidence.

```markdown
# Problem brief — <slug>

Construct: <what is claimed to be excessive/insufficient/present>
Population: <who, where, when>
Measure: <operational measure and unit>
Reference: <threshold/comparison/trend that makes the magnitude meaningful>; fixed in D-<n>
Basis: local — `aggregates/problem.csv`
# or: Basis: external — <DOI/URL>
Magnitude: <magnitude against the reference, with uncertainty where applicable>
Falsification: <what was checked that could have made the premise disappear>
Verdict: SHOWN | NOT_SHOWN | INCONCLUSIVE — <why>
```

For `Basis: local`, the pointer must resolve and numeric claims in the brief are checked against committed aggregates. For `Basis: external`, the cited content must pass CITE; the validator checks identity/reachability elsewhere but does not pretend semantic support is mechanical.

The Reference still names the decision that fixed how “problem” is judged. A reference chosen after observing the magnitude is disclosed as data-informed rather than presented as prospective.
