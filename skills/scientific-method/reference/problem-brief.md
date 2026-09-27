# Problem brief — the artifact gate 1B produces

Sources located 2026-09-10, not yet read at source.

**When this applies.** After the problem statement (gate 1A) and before the protocol
freezes. Also whenever someone says "the problem is obvious": obvious is the state before
the brief, not a substitute for it.

**What it requires.** A descriptive study, designed and pre-registered as descriptive, whose
product is one file (`problem-brief.md`, pointed to from the map's `## Question` under
`Problem:`). Every number in it comes from executed code and exists in a committed aggregate
— `research-map validate` checks the file. Fields marked ★ are required and checked.

```markdown
# Problem brief — <research slug>

★ Construct: <the thing that is "too much" or "too little", in one sentence>; validated by:
  <the check that this measure measures it — external criterion, convergent measure, or
  the reason none was possible, stated as NOT_VERIFIED>
★ Population: <who, where, when — anchored in time>
★ Measure: <occurrence or summary — prevalence, rate, index, difference — and its unit>
★ Reference: <what makes the number a deficit or excess: threshold, comparison group,
  trend, or the counterfactual "if nothing is done">; fixed in D-<n> <before the magnitude
  was computed — or, when it was derived from the data: "data-informed: <how, from what>";
  a reference is dated by its decision, never by this sentence>
★ Magnitude: <the number, with interval, from `<aggregate file>`; the gap against the Reference>
  Distribution: <who and where it concentrates; the groups where it does not>
  Trend: <direction over the anchored window, with the source table>
  Current handling: <how it is addressed today, by whom, with what result and limits>
  Owner: <the decision that changes with the answer; evidence of past behaviour, not opinion>
★ Falsification: <what was tried to show there is no problem — measurement artifact,
  denominator, already declining, below threshold, selection — and what each attempt showed>
  Registered as descriptive: <URL/DOI and date, or "prior observations, disclosed in the
  registration text">
★ Verdict: SHOWN | NOT_SHOWN | INCONCLUSIVE — <one sentence why>
```

**The error it prevents.** The error of the third kind: a precise answer to a problem that
does not exist, is smaller than the threshold, is already resolving, or is an artifact of
how it was measured. And its opposites: an anecdote or a focusing event standing in for
magnitude; a construct quantified before it was validated; a description treated as free of
selection, measurement and missingness; a problem defined as the absence of the solution
someone already wants.

**Terminal states.** `SHOWN` — the gap against the Reference holds after falsification;
phase 3 may freeze. `NOT_SHOWN` — the research ends here or reformulates (gate 1A reopens);
this is a result, and cheaper than any other way of learning it. `INCONCLUSIVE` — the
data cannot decide; the brief says what data would, and the protocol does not freeze.

**Exit gate.** All ★ fields present; every number present in a committed aggregate; the
Reference names the decision that fixed it, and that decision's date precedes the
magnitude's notebook or the field says `data-informed`; `Verdict` is one of the three
states; the map's `Problem:` line carries the same state and its 1B row points here.

**Sources.** Lesko, Fox & Edwards 2022 (a descriptive question names population, outcome
and measure; descriptive studies need design and pre-registration). Fox et al. 2022
(descriptive work is not bias-free). Loeb et al. 2017 (phenomenon → constructs → measures →
patterns → audience). Bardach (deficit or excess, with magnitude; no solution inside the
definition). Kingdon (indicators, focusing events, feedback; data do not speak for
themselves). Kimball 1957; Mitroff & Featheringham 1974 (error of the third kind;
misplaced precision). Jacobs & Wallach 2021 (construct validity before quantification).
Shook, *Managing to Learn* (current condition measured with data before countermeasures).
Blank; Fitzpatrick, *The Mom Test* (owner evidence from past behaviour, never leading
questions).
