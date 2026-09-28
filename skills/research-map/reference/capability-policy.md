# Capability policy

A capability policy answers one narrow question before data crosses a boundary:

> Is this repository resource allowed to leave through this capability?

It does not decide scientific validity and does not by itself provide sandboxing. A policy decision is authorization evidence; physical enforcement is a separate property of the execution environment.

## Optional file

Projects that need explicit data-boundary controls may add:

```text
.research/policy.json
```

Projects without this file keep the previous Research behavior.

Version 1 deliberately supports only:

- resource classes: `public | restricted | derived | secret`;
- capabilities: `model_egress | network_egress`;
- resource selectors: an exact repository-relative path, or a prefix ending in `/**`.

No general glob language or precedence rules exist. Resource selectors may not overlap; ambiguity is a validation failure.

Example:

```json
{
  "version": 1,
  "resources": [
    {"match": "data/raw/**", "class": "restricted"},
    {"match": "aggregates/**", "class": "derived"}
  ],
  "rules": {
    "restricted": {
      "model_egress": false,
      "network_egress": false
    },
    "derived": {
      "model_egress": true,
      "network_egress": true
    }
  }
}
```

Every class referenced by a resource rule must explicitly declare both capabilities. Missing policy is not permission, and an unmatched resource is `UNDECLARED`, not implicitly allowed.

## Decisions

The deterministic policy helper returns:

```text
ALLOW
DENY
UNDECLARED
INVALID
```

For debugging or preflight use:

```bash
python3 <installed research-map>/scripts/policy.py validate --root .
python3 <installed research-map>/scripts/policy.py check data/raw/patients.csv model_egress --root .
```

`DENY` and `UNDECLARED` return nonzero. `INVALID` means the policy or requested path/capability is malformed.

## Enforcement boundary

A policy check and enforcement must never be conflated.

Examples:

```text
policy DENY + ordinary agent with unrestricted file/network tools
    = policy exists, but the host may still be able to violate it

policy DENY + isolated execution environment with the forbidden boundary removed
    = enforceable boundary
```

Until an execution backend can physically enforce a requested restriction, Research must not claim that the restriction was enforced. The execution contract records that distinction when such a backend is used.

Capability policy does not replace disclosure rules, exposure roles, ethics decisions, credentials policy, or scientific preflights. It only controls whether matched repository resources are authorized for the named egress boundary.
