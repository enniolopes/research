# Phase 5 — Analysis

Run FIT immediately before any confirmatory result can be exposed. Invoke `statistical-analysis` to review the frozen plan; method selection starts from estimand/design, not a familiar model name.

Execution follows the canonical `../../research-map/reference/run-receipt.md` contract. Do not duplicate that schema here.

After freeze, EDA is limited to planned quality/assumption/diagnostic questions and prospective fallbacks. Unexpected patterns route to `EXPLORATORY`, `SENSITIVITY`, `DATA_PROBLEM`, `REOPEN` or `BLOCKED`; they do not silently rewrite the primary analysis.

The frozen primary test decides the confirmatory hypothesis under its recorded rule. Valid sensitivity/specification results qualify robustness and discordance is reported rather than used to select the favorable answer.

Exit when confirmatory runs have valid receipts, planned checks have consequences recorded, result artifacts are committed and each analyzed hypothesis has a terminal state.
