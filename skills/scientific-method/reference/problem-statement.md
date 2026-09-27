# Problem statement — the artifact gate 1A produces

Sources located 2026-09-10, not yet read at source.

**When this applies.** Gate 1A writes it; gate 1B (`reference/problem-brief.md`) then
demonstrates the problem it states; every later gate re-reads it and logs any change as a
decision. "Understanding the problem" is not time spent; it is this artifact, complete, and
then shown.

**What it requires.** One section in the protocol, pointed to from the map's `## Question`,
with these labelled fields. The seven marked ★ are checked by `research-map validate`.

```markdown
## Question
<one sentence, no jargon, that a reviewer outside the field understands>

★ Claim: descriptive | associational | causal — descriptive is a full claim, not a lesser
  one; if causal, the identification assumptions that stand in for randomisation
  (exchangeability, positivity, consistency)
★ Unit of analysis: <municipality | organisation | household | event>; every count and rate inherits it
★ Estimand: population <who, when>; exposure or contrast <A vs B>; outcome <variable, time>;
  intercurrent events <what can happen in between and how it is handled>; summary
  <difference, ratio, index>
  Target trial: <the randomised study that would answer this, in one paragraph; what the
  data can and cannot emulate of it>
★ Refutation: <the observation that would make the question wrong, not merely unanswered>
★ Objection: <the obvious reviewer objection — selection, reverse causation, ecological
  fallacy, measurement — and the phase that answers it>
  How it is done today: <conventional answers and their limits>
  What is new: <what this study adds; why it should work where others did not>
★ Who cares: <the decision or knowledge that changes with the answer; the person who owns it>
★ Non-goals: <what this study will not answer, so it is not asked to>
  Feasibility: <data access, expertise, time — the FINER check, in one line each>
  Success check: <what is observed at the midpoint and at the end if this worked>
  Considered and not adopted: <lineages from exploration, each in ## Deferred with its entry
  condition>
```

**The error it prevents.** A question that cannot fail; a "what" without a "for whom"; an
estimand discovered in the results section; a causal verb on an associational design; a
population that shifts between protocol and code; a study that answers a question nobody
asked. And the opposite error: definition as delay — the statement has a budget (phase 1's),
is revised at each gate rather than perfected before the first, and its revisions are
decisions with revision conditions, not silent rewrites.

**Exit gate.** All ★ fields present and specific enough that a stranger could compute the
estimand from the data; pointer in the map resolves; `validate` passes the `problem` check.

**Sources.** Einstein & Infeld 1938 (formulation is often more essential than solution).
Getzels & Csikszentmihalyi 1976 (problem finding predicted originality and later success).
Chi, Feltovich & Glaser 1981 (experts represent problems by principle, novices by surface).
Simon 1973 (ill-structured problems become tractable by structuring the representation).
Rittel & Webber 1973 (some problems are defined only together with their solution: hence
revision at each gate). Heilmeier (DARPA): what, how today, what is new, who cares, risks,
cost, time, success checks. ICH E9(R1) estimand attributes. Hernán & Robins 2016 (target
trial). Alvesson & Sandberg 2011 (problematisation over gap-spotting). Hulley et al.,
FINER. Passi & Barocas 2019 (problem formulation decides fairness and validity before any
model).
