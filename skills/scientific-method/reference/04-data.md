# Phase 4 — Data

Sources located 2026-09-10, not yet read at source.

**When this applies.** Whenever an input enters the repository, two sources are joined, a
population is defined, or an aggregate leaves the analysis environment.

**What it requires.**

- **Provenance file per input**: origin, date of access, version or hash, licence, the
  notebook that reads it. Nothing is read from a path without a provenance entry.
- **Stable key** for every reconciliation between sources; where none exists, the matching
  rule is written down and its error measured.
- **Linkage table per step** (GUILD): records in, records matched, unmatched by reason,
  duplicates, and the expected effect of linkage error on results.
- **Population definitions** stated for every pool ("registered" includes or excludes
  withdrawn units?); each defensible alternative becomes a specification-curve dimension
  (a pool that silently includes withdrawn units is the classic error).
- **Construct validation** for any modelled or proxy measure adopted from outside, with a
  switch rule: what result would make you drop it.
- **Disclosure floor.** "Outside the analysis environment" is a place: anything under the
  map's `documents`, whoever writes it — a manuscript table, a linkage report a notebook
  saves next to the paper, a file this method produces. Every such table respects the
  `floor` the map's `Layout` sets (`validate` reads the cells); PII is dropped at the first
  step, and no identifiable row exists outside the cache.
- **Datasheet** for any dataset the research publishes: motivation, composition,
  collection, preprocessing, uses, distribution, maintenance.

**The error it prevents.** A pool that silently includes units it should not; a proxy
adopted without knowing what it measures; a count that cannot be traced to a file; a
published table that identifies a household.

**Exit gate.** Linkage report exists for every join; provenance exists for every input;
population definitions and their alternatives are in the protocol; no identifiable row
outside the cache.

**Sources.** Gilbert et al. 2018, GUILD (report linkage error at each step). Gebru et al.
2021 (datasheets). Wilkinson et al. 2016 (FAIR). Hundepool et al. 2012 (statistical
disclosure control: cell thresholds, suppression).
