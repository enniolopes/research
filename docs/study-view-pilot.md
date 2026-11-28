# When should Research expand addressable rationales?

This proposed pilot asks whether an agent makes better revision decisions when it can locate the exact argument that changed. Before running it, freeze the case manifest, answer keys, prompts, software versions, budgets and decision rules below. Keep the reserved cases out of development and rubric calibration.

## Cases and conditions

Before freezing the protocol, calibrate the end-to-end status request on development cases with a consequential correction, an irrelevant edit and loss of decisive evidence. Include decisions expressed in ordinary prose beyond a status preview. Repeat the same question in fresh sessions under fixed settings. For each answer, record the decisive evidence cited, which conclusions still have independent support, and the action or deferral attributed to the study. Define equivalent passages, conclusions and actions in the case rubric before the runs.

Within each case, compare every unordered pair of completed answers once. For each of the three criteria, report how many pairs gave equivalent answers out of all pairs compared. Also report how many pairs agreed on all three at once. For example, two answers that agree on the evidence and conclusion but prescribe different actions score 1/1, 1/1 and 0/1 by criterion and 0/1 overall. Score correctness and critical errors against the key for each attempt, since two answers can agree on the same mistake. Report missing or timed-out attempts as failures and exclude them from agreement. With fewer than two completed answers, report agreement as unavailable. Keep these runs separate from the reserved-case comparison below.

These repetitions assess consistency on the sampled tasks. A claim that the workflow improves revision decisions requires a comparison with another way of doing the same work. A claim about a second host requires observations on that host. [Mohammadi et al., §3.3](https://doi.org/10.1145/3711896.3736570) · [Salaudeen et al., §4](https://arxiv.org/abs/2505.10573v4)

Reserve 48 independent study cases spanning early projects, executed quantitative studies and incomplete external manuscripts. Each case supplies an original study and one update. Include numerical corrections, changes in a measure's meaning, new rival explanations and irrelevant edits. Include surviving independent support, shared assumptions and cases where the available evidence warrants deferral. A study and its update form one scoring unit.

Run every case in three fresh agent sessions, one per condition, in randomized order. Ask the same question about what changed, which conclusions survive and what to do next.

| Condition | Material the agent receives |
|---|---|
| A · Good summary | The existing plugin, the study files and an expert-prepared summary with the scientific facts and limitations. |
| B · Navigable sources | The same material with direct access to versioned source passages. |
| C · Addressable rationales | The same passages and rationale text as B, with direct locators for each recorded justification and its revision history. |

Hold the model version, settings, scientific instructions, source permissions, tools, token limit and wall-time limit fixed. Preserve the exact scientific content across conditions. Only the route to that content varies. Count a missing or timed-out answer as a failed case.

## Scoring and decision

Before exposure, two domain reviewers key each case with the necessary revisions, conclusions that can stand, acceptable next actions, and critical errors. A response passes when it makes every necessary revision, preserves supported conclusions, cites the relevant evidence, chooses a defensible next action with a reason and avoids every keyed critical error. Count missed revisions, unwarranted withdrawals, unsupported confirmations and unsuitable actions separately. Give two independent scorers randomly labeled answers with interface identifiers replaced by neutral source references. Record disagreements and adjudicate them before revealing the condition.

The primary contrast is the paired difference in pass rates, C minus B. Report both discordant counts and a 95% Newcombe paired-score interval for the difference. Report B minus A separately to describe the contribution of source navigation. Time the work to create and update the records in each condition, with preparation order counterbalanced. Record query inspection and rendering times separately.

The proposed minimum worthwhile gain is 10 percentage points and the equivalence margin is ±10 points. Expand C only if the interval lies entirely above +10 points, C introduces no critical error on a case B handled correctly, and median additional maintenance time over B is at most five minutes per study update. Prefer B if the interval lies below −10 points, or lies entirely within the equivalence margin and B costs less to maintain. A failed cost or critical-error gate defers expansion. Classify remaining outcomes as inconclusive.

## Human use

Evaluate researcher benefit in a separate comparison. Have researchers make and justify revision decisions on reserved cases, counterbalancing condition and order so each person sees a study only once. Score their decisions with the frozen rubric and record active minutes, requests for clarification and record-maintenance effort. Report these outcomes separately from agent performance and from expert ratings of agent answers.
