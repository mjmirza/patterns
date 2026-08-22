<!-- freshness: 90d -->

# Catalog Comparison. The Single Source of Truth

This is the one place that records which other public pattern-catalog repos
this repository has been checked against, what was found, and what was done
about it. Every comparison is verified against the real, live source at the
time it was run, never recalled from memory. When a new comparison is done,
it is added here rather than left as a scattered chat claim.

## Method

Every comparison in this document followed the same discipline. fetch the
real pattern list from the source repo (its file tree, README, or index, via
`gh api` or a direct fetch, never guessed), check each entry against our own
real catalog (either the 797 published entries or the full published-plus-
queued set), and only report a gap once a direct, verifiable check confirmed
no match.

## Comparisons performed

### Round 1. nibzard/awesome-agentic-patterns, jayleaton/ai-patterns-monorepo, iluwatar/java-design-patterns

Verified. 14 patterns adopted from nibzard, 0 from jayleaton (a personal
learning monorepo, not a distinct catalog), 21 from iluwatar. 35 total,
queued into families 01, 04, 06, 15, 17. All 35 have since been authored and
published as of this comparison.

### Round 2. fravoll/solidity-patterns, munificent/game-programming-patterns, GoogleCloudPlatform/ml-design-patterns

64 patterns surveyed against the real 797-entry published catalog.
26 already covered by concept, 28 genuine gaps found.

Of the 28, 4 fit an existing family directly and are queued (see below).
The remaining 24 need one or more new top-level families to hold them
honestly, since they are a distinct domain rather than a variant of an
existing one:

- 5 smart-contract patterns (Checks-Effects-Interactions, Pull over Push,
  Oracle, Randomness, Upgradeable Proxy). Solidity-specific security and
  correctness patterns, source `fravoll/solidity-patterns`.
- 4 game-development patterns (Game Loop, Update Method, Type Object,
  Component/Entity-Component). Real-time simulation architecture, source
  `munificent/game-programming-patterns`. Note. three OTHER patterns from
  this same book (Data Locality, Dirty Flag, Object Pool) were already
  correctly queued under the existing `29-realtime-simulation` family before
  this round, so this book is already partially represented.
- 15 classical ML engineering patterns (Hashed Feature, Feature Cross,
  Multimodal Input, Reframing, Rebalancing, Transfer Learning, Hyperparameter
  Tuning, Continuous Model Evaluation, Feature Store, Explainable
  Predictions, Fairness Lens, Heuristic Benchmark, Windowed Inference,
  Neutral Class, Model Versioning). Source `GoogleCloudPlatform/ml-design-
  patterns`. This is a genuinely distinct sub-domain from family
  `17-ai-agentic`, confirmed by direct inspection of all 55 entries in that
  family, which are entirely LLM, agent, and RAG concerns (prompt chaining,
  routing, retrieval, guardrails) with zero classical training or MLOps
  content.

**Decision needed, not made here.** Whether to open one or more new families
for these 24 (a plausible split is a smart-contracts family, a
game-development family, and either extending `25-mlops` or reworking the
`17-ai-agentic`/`25-mlops` boundary for the classical-ML set) is a naming and
scope decision, the kind this repository's own scope note in
`docs/ENTRY-TEMPLATE.md` says should not be silently re-litigated by whoever
happens to be adding patterns that day. Recorded here as a live, open
decision rather than actioned unilaterally.

### Round 3. Sairyss/system-design-patterns, thedaviddias/ux-patterns-for-developers, alphagov/govuk-design-system

172 patterns surveyed.

Sairyss (46 surveyed, a single long-form article, not a discrete index).
26 already covered, 11 judged reasonably covered or too thin to warrant a
standalone entry, 9 genuine gaps. All 9 fit existing families directly and
are queued (see below).

thedaviddias (91 surveyed, a real per-widget UI/UX interaction and
accessibility catalog). 4 already covered by concept. The other 87 were
checked directly and confirmed as genuine gaps against the catalog, but are
NOT recommended for queuing. This repo's genre is widget and flow
implementation guidance (how a date picker or a login flow should behave for
keyboard and screen-reader users), a different abstraction level from every
one of this repository's 18 dimensions, including the existing
`13-frontend-ui` family, which is architecture-scoped (state management,
rendering strategy, component composition), not interaction-design-scoped.
Force-fitting them would blur the catalog's own scope rather than fill a
real gap in it. If a UI/UX interaction-pattern family is ever wanted as a
deliberate scope expansion, this repo names a solid starting list to draw
from, but that is a scope decision, not a missing-pattern finding.

alphagov/govuk-design-system (35 surveyed). Zero matches, and zero genuine
gaps recommended. This is UK government service content-design and form-
wording guidance (how to ask for a name or a National Insurance number, how
to structure a multi-step government service flow), not a software or
system-design pattern catalog at all. An even further genre mismatch than
thedaviddias. Recorded here so it is not re-surveyed under the mistaken
impression it was skipped.

## What is queued as of this document

19 patterns from rounds 2 and 3 fit an existing family directly and have
been added to `docs/AUTHORING-QUEUE.json`:

- `12-data-storage`. Data Locality (already present before this round,
  family `29-realtime-simulation`, listed here only to record the check),
  Database Federation, Denormalization, Byzantine Fault Tolerance,
  Distributed Hash Table.
- `04-principles-and-laws`. Dirty Flag (already present, family
  `29-realtime-simulation`, listed here only to record the check).
- `09-concurrency`. Object Pool (already present, family
  `29-realtime-simulation`, listed here only to record the check).
- `21-sre-operations`. Checkpoints.
- `08-cloud-distributed`. Load Balancing, Autoscaling.
- `06-enterprise-application-architecture`. Connection Pooling.
- `05-architectural`. Multi-Tenant Architecture.
- `19-api-design`. API and Schema Federation.

10 of these were newly added by this round. 3 (Data Locality, Dirty Flag,
Object Pool) were found, on checking, to already be queued under
`29-realtime-simulation` from an earlier pass, an important catch, since the
published-only comparison file used for rounds 2 and 3 could not see the
already-queued-but-unauthored set, and treating them as new would have
created a duplicate queue entry.

## What is deliberately not queued

- The 24 patterns needing a new family (smart-contracts, game-development,
  classical ML), pending the scope decision above.
- The 87 UX/interaction patterns from thedaviddias, genre mismatch with this
  catalog's architecture-pattern scope.
- The 35 content-design patterns from alphagov, genre mismatch, not a
  software pattern catalog.
- Roughly a dozen items across rounds 2 and 3 marked marginal or uncertain
  in the source research (Bytecode, Subclass Sandbox, Spatial Partition,
  String Equality Comparison, Tight Variable Packing, Memory Array
  Building, the low-level native-currency transfer pattern that overlaps two
  already-queued smart-contract patterns, Eternal Storage, Multilabel,
  Useful Overfitting, Repeatable Sampling, and a handful of Sairyss items
  too close to an existing entry). Not queued because the confidence bar
  for calling something a genuine gap was not met, not because they were
  overlooked.
