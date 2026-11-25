# Inquiry state

Use an inquiry when a study needs to carry a scientific decision across sessions. Its identifier, such as `Q1`, stays with the question. Each assessment round gets a fresh `INQ-n` in `.research/inquiries/`. The [schema](../schemas/inquiry-1.schema.json) specifies the complete record. Inquiry records are optional in projects with initialized supervision.

## Record the next decision

1. Choose the question and write why the answer matters. Use `stage: planning` while specifying the question, design or criteria prospectively. Use `stage: assessment` when interpreting evidence. The existing protocol, exposure and registration checks establish whether a commitment was prospective.
2. Write a small set of material criteria. For each, enter the desired condition, assessment, and reason. Use `unassessed` when a judgment is missing, `unmet` when a gap remains, `met` when the condition is satisfied, and `limited` when a documented limitation bounds the answer. A satisfied conclusion criterion cites the exact supervised decision that supports it.
3. Bind the question, design and other material sources using the existing versioned resource and binding shapes. Use `follow_current` when a change should prompt reassessment and `pinned` when the historical version is material. Declare the origins of prose and copied evidence so that the view can apply the study's access policy.
4. Choose a pending criterion and record the proposed action and expected observable signal. Use `decide_scope` when the remaining issue is whether a narrower question meets the user's purpose. Leave the action empty when all criteria are met or have documented limits. Attribute the round to its actual assessor and commit it.

A criterion and action for a study of visit reminders could read:

```json
{
  "criterion": {
    "id": "coverage",
    "dimension": "design",
    "desired": "Separate changes in reminders from changes in transport.",
    "assessment": "unmet",
    "reason": "Both interventions changed in the same period.",
    "decision_refs": []
  },
  "next_action": {
    "criterion": "coverage",
    "kind": "investigate",
    "action": "Look for clinics where only the reminders changed.",
    "expected_signal": "Find clinics with unchanged transport and comparable prior trends."
  }
}
```

## Observe the effect

Use `view status --root . --audience model` to recover the criterion, proposed action and signal. `view explain Q1` retrieves the active round and its supporting records. `view explain INQ-1` retrieves that exact round. When the view requires verification or reassessment, inspect the changed input before using the previously recorded proposal.

Run consequential actions by the existing [supervised procedure](supervision.md#action-routing-and-ownership). An inquiry describes the proposed action and its rationale. Its authorization and effects come from the protocol and supervisor. The responsible researcher decides material scope and stopping choices.

Once the action yields material information, append a round with the same question ID and the preceding round in `supersedes`. In an assessment, cite the observed versioned resource in `observation` and bind it in `dependencies`. State what the observation changed, preserve surviving support, and reference a new supervised decision if you revise a material conclusion. The next read shows the successor and can still explain its predecessor. An unfinished draft remains a candidate until committed.

The view recalculates on each query. Its record checks establish version, chronology and applicability within the inspected sources. The assessor remains responsible for relevance, validity, study design, conclusion scope and the adequacy of any limitation.
