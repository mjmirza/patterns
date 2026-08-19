---
name: Data Vault
slug: data-vault
family: 12-data-storage
category: Data and Storage
aliases: [Data Vault Modeling, Data Vault 2.0, Hub-Link-Satellite Modeling]
first_described: "Dan Linstedt, conceived in the 1990s, published 2000, Data Vault 2.0 published 2013"
maturity: established
related: [medallion-architecture, event-sourcing, cqrs, outbox-pattern, saga, repository]
incompatible_with: []
verified: 2026-08-02
---

# Data Vault

## 1. Name, aliases, and lineage

The canonical name is Data Vault, also written Data Vault Modeling or, for the
current revision, Data Vault 2.0. Dan Linstedt conceived the technique in the
1990s while working on data warehouse designs for United States government and
defense systems, and released the method publicly in the year 2000 under the
name he originally called a common foundational warehouse architecture before
settling on Data Vault ([Wikipedia, Data vault modeling](https://en.wikipedia.org/wiki/Data_vault_modeling),
verified 2026-08-02). The revised specification, Data Vault 2.0, was published
around 2013 and folds in a development methodology drawing on CMMI and Six
Sigma practice, an architecture that adds a persistent staging area and
downstream data marts, and an updated modeling notation that replaces
sequential surrogate keys with hash keys so that hub, link, and satellite rows
can be generated independently on parallel systems without a shared identity
sequence ([Wikipedia, Data vault modeling](https://en.wikipedia.org/wiki/Data_vault_modeling),
verified 2026-08-02).

The pattern is not part of the Gang of Four catalog and did not emerge from
object-oriented design literature. It belongs to the data warehousing and data
engineering tradition, sitting alongside star schema (Ralph Kimball) and
normalized third normal form modeling (Bill Inmon) as a third named approach
to structuring an enterprise data warehouse. Where Kimball optimizes for query
performance against a known set of business questions and Inmon optimizes for
a single normalized source of truth, Data Vault optimizes for something
neither of those two addresses directly, the warehouse surviving unplanned
change in its source systems without a redesign, while keeping a complete,
auditable record of everything that was ever loaded.

Three terms are used almost interchangeably in casual conversation and should
not be.

- **Data Vault Modeling.** The hub, link, satellite schema shape alone.
- **Data Vault Methodology.** The surrounding development process, iterative,
  automation-driven, agile-adjacent.
- **Data Vault Architecture.** The layered system that places Data Vault
  modeling in a specific position between raw staging and the business-facing
  presentation layer.

This entry is primarily about the modeling shape. Dimension 8 covers the
architecture and methodology layers where they change how the pattern is
applied.

## 2. Problem and context

An enterprise data warehouse ingests data from many source systems, an ERP,
a CRM, a billing platform, several SaaS tools connected through an API, and
often at least one legacy mainframe feed that nobody currently at the company
fully understands. Two things are true about this situation and both get
worse as the company grows.

The first is that the source systems change on their own schedule, not the
warehouse team's schedule. A vendor renames a field, a business unit adds a
new customer type, a company is acquired and its CRM is bolted onto the
existing pipeline with different field names for the same concepts. A
warehouse modeled as a single normalized schema (Inmon-style third normal
form) or as denormalized star schemas (Kimball-style) tends to require a
redesign of existing tables when this happens, because both approaches encode
business rules and relationships directly into the table structure at design
time. A field rename in the source can mean an ALTER TABLE, a backfill, and a
re-point of every downstream report that referenced the old column.

The second is that regulated industries, banking, insurance, healthcare, and
government among them, need to answer an auditor's question that a
dimensional warehouse is not built to answer cleanly. What value did this
attribute hold in the source system, loaded by which process, on which date,
and has it ever been retroactively corrected. A star schema that overwrites a
dimension row on update (a Type 1 slowly changing dimension) has already
destroyed the answer. A star schema using Type 2 slowly changing dimensions
preserves history but ties it to the specific dimension's structure, which
still changes when a business rule changes.

Data Vault's context is the layer that sits directly downstream of raw source
extracts and upstream of any business-facing model. Its job is to receive
whatever a source system sends, verbatim and unfiltered, in a shape flexible
enough that adding a new source or a new attribute is an additive change, a
new table or a new column, never a redesign of an existing one. The
dimensional or third normal form model that answers actual business questions
is built as a separate, disposable layer on top of the vault, and can be
rebuilt from the vault at any time because the vault has never discarded
anything it received.

## 3. Forces

Data Vault deliberately trades one set of properties for another, and stating
which side of each trade it lands on is more informative than a generic
description of the pattern.

- **Auditability against query convenience.** Every value ever loaded is
  retained with its load date and its originating record source, satisfying
  strict audit requirements. In exchange, answering a simple business
  question such as a customer's current address requires joining a hub to
  its satellite and filtering to the latest load date, work that a Kimball
  dimension does with a single row lookup. Data Vault accepts slower, more
  verbose queries at the vault layer in exchange for the audit trail, and
  pushes the convenient query shape to a downstream mart built for that
  purpose.
- **Schema stability against schema simplicity.** The hub, link, satellite
  split means a new source attribute is a new column on an existing
  satellite or an entirely new satellite table, never a structural change to
  a hub or a link. This is the pattern's central selling point. The cost is
  that the vault itself contains many more tables than an equivalent
  dimensional model for the same business domain, because every attribute
  grouping that changes at its own rate becomes its own satellite.
- **Parallel load throughput against key simplicity.** Data Vault 2.0's hash
  keys, a deterministic hash of the business key, let independent ETL jobs
  compute the same key for the same business entity without coordinating
  through a shared sequence generator, which is what makes massively
  parallel loading practical on distributed compute. The cost is a wider key
  (typically a 16 or 32 byte hash versus a 4 or 8 byte integer), more storage,
  and the practical risk of a hash algorithm change across a platform
  migration silently breaking key continuity.
- **Coupling to the business key against coupling to the schema.** A hub is
  defined by its business key alone, and the physical schema of any one
  source system is irrelevant to it. This decouples the vault from any
  single source's internal representation. The cost is that identifying the
  correct business key, the value that genuinely and stably identifies the
  entity across every system that will ever feed the vault, is a business
  analysis problem, not a technical one, and a wrong choice here is
  expensive to unwind later because every link and satellite in the vault
  references it.
- **Team topology.** Data Vault's additive-only modeling style suits a large
  team where different squads own different source integrations and load
  independently, because a new source rarely touches another team's tables.
  A three person team building a warehouse for a single product has little
  need for this property and pays the dimension-count cost without a
  matching benefit, which is the recurring reason small teams reject the
  pattern.

## 4. Applicability and non-applicability

Reach for Data Vault when the organization runs many source systems that each
change independently, when regulation requires proving exactly what data was
received and when, when the warehouse team is large enough that isolated,
parallel loading of new sources is a real operational need, or when the
business rules used to interpret raw data are expected to change faster than
the warehouse team wants to re-architect the storage layer underneath them.

Do not reach for Data Vault in these situations, and the reasons matter more
than the list.

- **A single source system, or very few, with a stable schema.** The core
  benefit, isolating the warehouse from independent source-system churn,
  does not apply when there is effectively one source. The hub, link,
  satellite split adds joins and table count with no corresponding payoff,
  and a simpler star schema or even a well-indexed operational data store
  answers the same questions faster to build and faster to query.
- **A small team building a first warehouse.** Data Vault's value compounds
  with organizational scale, more sources, more teams, more regulatory
  pressure. A two or three person team building version one of a company's
  first warehouse will spend real time hand-building satellites and hash-key
  logic for a change-tolerance property they do not yet need, when the
  actual near-term risk is delivering nothing before the business loses
  patience. This is the single most common misapplication reported in
  practitioner writing on the pattern ([VaultSpeed, The Bull Case for Data
  Vault](https://www.vaultspeed.com/blog/the-bull-case-for-data-vault),
  verified 2026-08-02, which argues the pattern earns its cost specifically
  at multi-source, multi-team scale and not below it).
- **Reporting and analytics needing sub-second interactive queries directly
  against the modeled layer.** The raw vault is not meant to be queried by
  end users or BI tools directly. If there is no appetite or budget for the
  downstream mart layer that turns vault tables into a query-friendly star
  schema, the organization gets the vault's costs (join-heavy queries, wide
  hash keys) with none of its query-side benefit, because the convenient
  layer that is supposed to sit on top was never built.
- **Data with no genuine business key.** Event streams, telemetry, and log
  data are usually better served by an append-only fact table or an
  event-sourced store (see the event-sourcing entry) because they typically
  lack a stable natural business key that would identify a recurring hub
  entity. Forcing such data into hub, link, satellite shape produces hubs
  keyed on an arbitrary surrogate that carries none of the pattern's
  auditability benefit.
- **A domain where source systems genuinely do not change.** Some regulated
  systems of record, a country's national ID registry for example, change
  their schema on a timescale measured in decades. Paying the Data Vault
  tax for change tolerance against a source that essentially never changes
  buys nothing.

## 5. Structure

Data Vault modeling defines exactly three core table types, plus one
supporting structure introduced in Data Vault 2.0 for many-to-many
relationships with their own descriptive attributes.

- **Hub.** Stores one row per unique instance of a core business concept,
  identified by its business key exactly as the business would recognize it,
  for example a customer number, an order number, a product SKU. A hub row
  never changes once inserted, it holds the business key, a hash key derived
  from that business key, a load date recording when this business key was
  first seen, and a record source identifying which system first supplied
  it. A hub never stores descriptive attributes.
- **Link.** Stores one row per unique combination of business keys
  representing a relationship or a transaction between two or more hubs, for
  example a customer placing an order links the Customer hub to the Order
  hub. A link's own key is a hash of the participating hub keys together,
  so the same combination of business keys always produces the same link
  row regardless of which load process inserts it. Links are also
  append-only and hold no descriptive attributes beyond the relationship
  itself, load date, and record source.
- **Satellite.** Stores the descriptive, time-varying attributes that belong
  to a hub or a link, plus a load date and a record source for each version
  of those attributes. A satellite is the only place in the model where
  history of change is tracked, a new row is appended whenever the source
  supplies a changed value for the same hub or link key, and the previous
  row is left untouched. A single hub or link commonly has several
  satellites, split along rate-of-change or source-system lines, for
  example a Customer hub might have one satellite for demographic
  attributes sourced from the CRM and a separate satellite for credit
  attributes sourced from the finance system, because those two attribute
  groups arrive from different systems on different schedules.
- **PIT (Point-In-Time) table, Data Vault 2.0 addition.** A denormalized
  helper table that pre-joins a hub to its associated satellites' most
  recent load dates as of a given snapshot moment, built purely to speed up
  the query that would otherwise require finding the latest row in every
  satellite independently. A PIT is disposable and rebuildable from the
  underlying vault at any time, it is never a system of record.
- **Bridge table, Data Vault 2.0 addition.** A similar disposable,
  rebuildable helper that pre-computes commonly needed multi-hop
  relationships across several links, avoiding a deep join chain at query
  time in the downstream mart layer.

Participants in a typical loading pipeline.

- **Staging Area.** Receives raw extracts unchanged from the source.
- **Raw Vault loader.** Computes hash keys and inserts new hub, link, and
  satellite rows, never updating or deleting an existing row.
- **Business Vault, optional.** Applies business rules or calculated
  attributes on top of the raw vault while still preserving append-only
  history.
- **Information Mart.** Typically a Kimball-style star schema, generated
  from the vault for consumption by BI tools and end users.

## 6. ASCII structure diagram

```
+-----------------------------------------------------------------+
|                         RAW VAULT LAYER                         |
|                                                                   |
|   +------------------+                 +------------------+     |
|   |   HUB: CUSTOMER  |                 |   HUB: ORDER     |     |
|   |------------------|                 |------------------|     |
|   | customer_hk (PK) |                 | order_hk (PK)    |     |
|   | customer_bk      |                 | order_bk         |     |
|   | load_date        |                 | load_date        |     |
|   | record_source    |                 | record_source    |     |
|   +--------+---------+                 +--------+---------+     |
|            |                                    |                |
|            | 1                                  | 1              |
|            |                                    |                |
|   +--------v---------+     +---------------------v-------+       |
|   | SAT: CUST_DEMOG   |     | LINK: CUST_PLACES_ORDER      |       |
|   |-------------------|     |-------------------------------|      |
|   | customer_hk (FK)  |     | link_hk (PK)                  |      |
|   | load_date  (PK)   |     | customer_hk (FK)              |      |
|   | name              |     | order_hk    (FK)              |      |
|   | address           |     | load_date                     |      |
|   | record_source     |     | record_source                 |      |
|   +-------------------+     +---------------+----------------+      |
|                                              |                       |
|   +-------------------+                     | 1                     |
|   | SAT: CUST_CREDIT   |         +-----------v-----------+           |
|   |--------------------|         | SAT: ORDER_STATUS      |           |
|   | customer_hk (FK)   |         |-------------------------|          |
|   | load_date   (PK)   |         | link_hk    (FK)         |          |
|   | credit_score       |         | load_date  (PK)         |          |
|   | record_source      |         | status                 |          |
|   +--------------------+         | record_source          |          |
|                                   +-------------------------+          |
+-----------------------------------------------------------------+
      hub rows. insert-only, one row per unique business key
      satellite rows. insert-only, one row per (key, load_date)
      link rows. insert-only, one row per unique key combination
```

## 7. Dynamics

Loading Data Vault follows a strict order at ingest time because links and
satellites reference hub hash keys, and the load must never fail on a
foreign key it has not yet inserted.

```
SOURCE SYSTEM EXTRACT
      |
      v
STAGE  (raw copy of source rows, unchanged, tagged with load_date
        and record_source at the moment of extraction)
      |
      v
HASH KEY COMPUTATION
      customer_hk = HASH(business_key)         one per hub
      link_hk     = HASH(hub_key_1 + hub_key_2 + ...)  one per link
      |
      v
HUB LOAD  (parallel, independent per hub)
      IF customer_hk NOT IN hub_customer THEN
          INSERT new hub row (first-seen business key)
      ELSE
          no-op, hub already knows this business key
      |
      v
LINK LOAD  (parallel, independent per link, after referenced hubs exist)
      IF link_hk NOT IN link_places_order THEN
          INSERT new link row (first-seen relationship)
      ELSE
          no-op, relationship already recorded
      |
      v
SATELLITE LOAD  (parallel, independent per satellite,
                 after the referenced hub or link exists)
      compute hash_diff = HASH(all descriptive attributes)
      IF hash_diff differs from the most recent satellite row
         for this hub_hk THEN
          INSERT new satellite row with today's load_date
      ELSE
          no-op, nothing changed since the last load
      |
      v
RAW VAULT NOW HOLDS THE FULL, APPEND-ONLY HISTORY
      |
      v
BUSINESS VAULT (optional)     INFORMATION MART (rebuilt, disposable)
   apply business rules,          join hubs, links, latest satellite
   still append-only              rows into a star schema for BI
```

The critical property visible in this flow is that hub, link, and satellite
loads for different business keys have no dependency on one another and can
run concurrently, which is exactly what a hash-key-based design was built to
enable, and every step is idempotent. Re-running the same extract twice
inserts nothing new the second time, because both the existence check on the
hub and link keys and the hash_diff comparison on satellites are naturally
deduplicating.

## 8. Implementation variants

- **Sequential surrogate keys (Data Vault 1.0 style).** The original
  formulation used an auto-incrementing integer as the hub's surrogate key
  instead of a hash. This is simpler to reason about and smaller on disk,
  but it forces every hub load through a single sequence generator, which
  becomes a coordination bottleneck the moment loading needs to happen from
  more than one process or more than one region concurrently. Most
  greenfield implementations since roughly the mid 2010s use hash keys
  instead, following the Data Vault 2.0 revision, specifically to remove
  this bottleneck ([Wikipedia, Data vault
  modeling](https://en.wikipedia.org/wiki/Data_vault_modeling), verified
  2026-08-02).
- **Hash keys (Data Vault 2.0 style).** A deterministic hash function, MD5
  and SHA-1 are both common in practice despite neither being a
  cryptographically strong choice for this purpose, applied to the
  concatenated, normalized business key. This lets independent processes
  compute identical keys without coordination. The practical failure mode
  is a change in how the business key is normalized before hashing (a
  trailing space trimmed on one load and not another, a case difference)
  producing two different hashes for what should be the same entity, which
  silently creates a duplicate hub row rather than raising an error.
- **Multi-active satellites.** A satellite variant for attributes that can
  have more than one simultaneous valid value for the same hub, for example
  a customer with several concurrently valid phone numbers. The satellite's
  key extends beyond hub key and load date to include a discriminator
  column identifying which of the concurrent values a given row represents.
- **Point-In-Time and Bridge tables as a materialized query acceleration
  layer.** These are not part of the core three table model but are
  standard in the Data Vault 2.0 architecture specifically because raw
  vault queries that need the latest attributes as of some date require a
  correlated subquery or window function per satellite, which does not
  scale well against a satellite with a long history. PIT tables precompute
  this join.
- **Automation-tool-generated Data Vault.** In practice, most production
  Data Vault warehouses are not hand-written SQL. Tools such as WhereScape,
  VaultSpeed, and the open-source dbt package AutomateDV (formerly
  dbtvault) generate the hub, link, and satellite DDL and load logic from a
  metadata specification of business keys and attribute groupings, because
  the amount of nearly identical boilerplate SQL across dozens or hundreds
  of hubs and satellites in a real warehouse makes hand-authoring
  error-prone and slow ([AutomateDV on GitHub](https://github.com/Datavault-UK/automate-dv),
  verified 2026-08-02).
- **Data Vault on a lakehouse.** Modern implementations increasingly build
  the vault directly on lakehouse storage (Delta Lake, Apache Iceberg) as
  the Silver layer of a medallion architecture, rather than on a
  traditional relational data warehouse, specifically because
  append-only, insert-heavy vault loading maps naturally onto a lakehouse's
  ACID table formats and because the vault's raw, unopinionated shape suits
  the medallion pattern's Silver layer, which exists to hold cleaned but
  not-yet-business-modeled data ([Databricks, What is a Data
  Vault?](https://www.databricks.com/blog/what-is-data-vault), verified
  2026-08-02).

## 9. Known production uses

- **FinWise Bank**, a US bank, built its enterprise data warehouse on Data
  Vault 2.0 using WhereScape's automation toolchain (WhereScape 3D for
  modeling, WhereScape RED for automation, WhereScape Data Vault Express for
  object generation). The bank reports using custom satellite types
  specifically to isolate and track PII and PCI-classified attributes
  separately from other descriptive data, and used the vault's built-in
  source-to-target lineage to support audit trackback requirements. The
  case study reports the warehouse was delivered in three months against an
  eighteen-month estimate for a manually built equivalent ([WhereScape,
  FinWise Bank case
  study](https://www.wherescape.com/case-studies/finwise-bank/), verified
  2026-08-02).
- **Databricks** documents Data Vault as a recommended and supported
  modeling pattern for the Silver layer of its medallion lakehouse
  architecture, stating it handles volumes up to petabyte scale and is
  suited to ETL code generation, and specifically recommending it as the
  layer that simplifies downstream Gold layer star schema construction by
  handling surrogate and natural key management once, upstream of the marts
  ([Databricks, What is a Data
  Vault?](https://www.databricks.com/blog/what-is-data-vault), verified
  2026-08-02).
- **AutomateDV** (formerly dbtvault), an open-source dbt package maintained
  by the consultancy Datavault, generates and executes the hub, link, and
  satellite load SQL for a Data Vault 2.0 warehouse from a metadata
  specification supplied to dbt macros. The project's own documentation
  states it moved from being a low-cost entry point for prototyping and
  proof-of-concept work to being used in production at both small and large
  enterprise scale, running on top of dbt's execution and dependency
  management ([AutomateDV on GitHub](https://github.com/Datavault-UK/automate-dv),
  verified 2026-08-02).

## 10. Consequences

Positive consequences.

- Adding a new source system, or a new attribute from an existing one, is
  purely additive, a new satellite table or a new satellite column, never a
  redesign of an existing hub or link.
- Every value ever loaded is retained with its load date and record source,
  which directly satisfies audit and regulatory traceability requirements
  that a Type 1 slowly changing dimension cannot answer at all and a Type 2
  slowly changing dimension answers only within the scope of that one
  dimension's own change tracking.
- Hash-key-based loading removes the shared-sequence bottleneck, letting
  independent teams load independent sources in parallel with no
  coordination required at load time.
- The raw vault is naturally idempotent to re-load. Replaying the same
  extract twice inserts nothing new the second time, which makes recovery
  from a failed or partial load operationally simple compared to a model
  where an UPDATE could be applied twice with different effect.
- Business rules can change, or be entirely reinterpreted, without
  reloading history, because the raw vault stores facts as received, not
  facts as currently interpreted. The interpretation lives in the
  disposable business vault and mart layers, which are rebuilt, not the raw
  vault, which is never rebuilt.

Negative consequences.

- Table count and join depth are substantially higher than an equivalent
  Kimball star schema for the same business domain, and a query against the
  raw vault answering a simple business question typically requires several
  joins plus a most-recent-row filter per satellite, which is why a
  separate, disposable mart layer is treated as mandatory rather than
  optional in practice.
- Hash keys are wider than sequential integer surrogate keys, increasing
  storage and index size, and a change in the hashing or normalization
  logic across a platform migration can silently produce duplicate hub rows
  for what is really the same business key, a failure mode that does not
  raise an error and can go unnoticed for a long time.
- Correctly identifying business keys is a business-analysis exercise, not
  a technical one, and getting it wrong is expensive. Every link and
  satellite in the vault references the hub's key, so a business key that
  turns out not to be stable (a customer ID that gets reissued, for
  example) requires a structural rework of everything downstream of that
  hub.
- The pattern's benefits scale with organizational size and source-system
  count. Below a certain scale the additional table count, join complexity,
  and hashing logic are pure overhead with no offsetting benefit, which is
  the most commonly cited reason small teams reject the pattern after
  evaluating it ([VaultSpeed, The Bull Case for Data
  Vault](https://www.vaultspeed.com/blog/the-bull-case-for-data-vault),
  verified 2026-08-02).
- Storage grows monotonically and without bound by design, since nothing is
  ever updated or deleted in the raw vault. This is intentional but is a
  real operational cost that has to be planned for, particularly for
  satellites attached to high-change-frequency attributes.

## 11. Failure modes and misuse

**Symptom.** Two rows in the same hub table with different hash keys but the
same real-world business identity, for example one customer appearing as two
separate hub rows.
**Cause.** The business key normalization applied before hashing differs
between two load processes, commonly a trailing whitespace difference, a
case-sensitivity difference, or a change in the hashing algorithm's input
encoding across a platform migration, producing two different hashes for
what should be the identical key.
**Fix.** Normalize the business key with a single, versioned, shared
function used by every loader, never inline logic duplicated per pipeline,
and add a data-quality check comparing distinct hub hash key counts against
distinct normalized business key counts on every load. A mismatch is the
early signal, well before it surfaces as a business-visible duplicate
customer.

**Symptom.** Satellite tables growing far faster than expected, with the
warehouse's storage bill rising noticeably month over month even though the
number of distinct entities is roughly stable.
**Cause.** A satellite is receiving a full snapshot of every attribute on
every load cycle instead of only changed attributes, so hash_diff never
matches the previous row even when nothing actually changed, most often
because a volatile, low-value field (a last-synced-at timestamp coming
straight from the source system) was included in the satellite's hash_diff
computation.
**Fix.** Split volatile, purely technical fields into their own satellite,
separate from the attributes an auditor or analyst actually cares about, so
that a change in a sync timestamp does not force a new row in the satellite
carrying the attributes that actually describe the business entity, and
audit which columns feed the hash_diff calculation whenever satellite
growth looks disproportionate.

**Symptom.** A query against a hub and its satellites returning several rows
per business key when the caller expected exactly one row representing
current state.
**Cause.** The query queried the raw vault directly instead of a materialized
current-state view or a Point-In-Time table, and did not filter to the most
recent load_date per hub key, which is an easy step to omit because the raw
vault has no notion of current built into its structure by design.
**Fix.** Build and use PIT tables, or an equivalent windowed most-recent-row
view, for any consumer that wants current state. Never let an analyst-facing
tool query raw satellites directly without that filter, and treat a raw
vault query returning multiple rows per key as expected, correct behavior
rather than a bug to patch around ad hoc.

**Symptom.** A new source integration takes weeks of modeling work instead
of the near-immediate, additive change the pattern promises.
**Cause.** The team modeled hubs around a specific source system's schema
rather than around the business's own concept of the entity, so a new
source that represents the same business concept differently (a different
attribute set, a different key format) cannot map cleanly onto the existing
hub and instead triggers a redesign.
**Fix.** Model hubs strictly around business concepts and business keys as
the business itself would define them, independent of any single source
system's representation, and treat a hub redesign triggered by adding a new
source as a signal that the original hub boundary was drawn around a
system, not around a concept.

**Symptom.** Team adopts Data Vault for a first warehouse with one or two
source systems, then abandons it after several months, citing excessive
complexity for the size of the problem.
**Cause.** Misapplication per dimension 4. The pattern's core benefit,
tolerance for independent multi-source, multi-team change, was never needed
at that scale, so the team paid the full modeling and tooling cost for a
property with no matching payoff.
**Fix.** This is a decision-time fix, not a code-time fix. Evaluate source
count, team count, and audit requirements against dimension 4's
applicability list before adopting the pattern, not after building the
first several hubs.

## 12. Trade-off matrix

| Force | Data Vault | Kimball star schema | Third normal form (Inmon) | Event sourcing |
|---|---|---|---|---|
| Tolerance to source-system schema change | High, additive by design | Low, dimension redesign often required | Medium, normalized model absorbs some change but relationships are fixed at design time | High for the events themselves, but downstream read models still need rebuilding |
| Query convenience for end users | Low directly, requires a mart layer | High, purpose-built for BI tools | Medium, requires joins across normalized tables | Low directly, requires projected read models |
| Audit and historical traceability | High, every value retained with load date and source | Medium, only if Type 2 slowly changing dimensions are used consistently | Low to medium, depends on whether history is modeled explicitly | High, the event log is the history |
| Parallel, uncoordinated multi-source loading | High, hash keys remove sequence bottlenecks | Low, dimension surrogate keys are typically sequence-generated | Low to medium | High, events are independently appendable |
| Storage cost | High, wide hash keys and unbounded satellite growth | Medium | Medium to low | High, full event history retained |
| Build and query complexity for a small, single-source system | Poor fit, high overhead | Good fit | Good fit | Poor fit unless the domain is genuinely event-driven |
| Regulatory suitability (banking, insurance, healthcare) | Strong, purpose-built for this | Weak unless heavily supplemented | Moderate | Strong for the audit log, weak for reporting without a mart |

## 13. Related and incompatible patterns

**Medallion architecture.** Data Vault composes directly with the medallion
pattern's Bronze, Silver, Gold layering. The raw vault typically occupies the
Silver layer, receiving cleaned but not yet business-modeled data from
Bronze, with the Gold layer built as the disposable, rebuildable mart layer
described in dimension 5 ([Databricks, What is a Data
Vault?](https://www.databricks.com/blog/what-is-data-vault), verified
2026-08-02, describes this pairing explicitly).

**Event sourcing.** Both patterns share the append-only, never-update-in-place
philosophy, and both treat history as a first-class citizen rather than an
afterthought. They differ in what they append. Event sourcing appends
domain events describing state transitions in an operational system, while
Data Vault appends snapshots of attribute state as received from source
extracts. A system using event sourcing operationally can feed Data Vault as
one of several sources, with the vault's record source column tracking that
provenance.

**CQRS.** The disposable, rebuildable mart layer that sits on top of a Data
Vault is conceptually the same idea as a CQRS read model, a purpose-built
projection derived from an authoritative append-only store, kept separate
from that store, and rebuildable from it at will.

**Outbox pattern.** Not directly related to Data Vault's modeling shape, but
frequently found upstream of it in the pipeline. An outbox reliably captures
change events from an operational database for downstream consumption, and
Data Vault is a plausible destination for those events once they reach the
warehouse's staging area.

**Repository pattern.** Superficially similar in that both provide a
consistent access point over storage, but they operate at entirely different
scales and for different purposes. A repository abstracts persistence for a
single aggregate in an operational application, while Data Vault is a
warehouse-wide modeling strategy for integrating many sources. Treating a
Data Vault hub as if it were a repository's backing table, expecting
update-in-place semantics, is a category error that produces the duplicate
key failure mode described in dimension 11.

**Kimball star schema and Inmon third normal form.** These are not
compatible layers to be combined with Data Vault at the same layer of the
architecture, they are alternative approaches to the same modeling problem.
In practice, star schema is very commonly used together with Data Vault, but
as the downstream mart layer built from the vault, not as a replacement for
the vault's own hub, link, satellite structure.

## 14. Refactoring path in and out

Introducing Data Vault into an existing warehouse that currently uses a
single dimensional model, step by step.

1. Identify the core business entities the organization actually cares
   about, independent of any current table structure, and for each one
   identify its true, stable business key exactly as the business would
   define it. This is the highest-risk step and deserves the most time. A
   wrong business key choice is expensive to correct later.
2. Stand up a staging area that captures raw extracts from each source
   system unchanged, tagged with a load timestamp and a record source
   identifier, if one does not already exist.
3. Build hub tables for the identified business entities, loaded from
   staging, with hash keys computed from the normalized business key.
4. Build link tables for the relationships between hubs that the business
   actually needs to track, with hash keys computed from the participating
   hub keys.
5. Build satellite tables for descriptive attributes, splitting by
   rate-of-change and by source system rather than lumping everything for
   one hub into a single satellite.
6. Point the existing dimensional model's ETL at the new vault instead of
   directly at source systems, so the existing reports keep working
   unchanged while the vault becomes the new single point of truth
   underneath them.
7. Migrate remaining source integrations onto the vault one at a time,
   verifying at each step that the existing dimensional mart's output is
   unchanged, since the mart is disposable and rebuildable but the
   downstream report consumers are not.

Removing Data Vault from a system where it no longer earns its cost, most
commonly when a warehouse has consolidated to one or two stable sources and
the organization has shrunk or simplified, follows a different path.

1. Confirm the applicability list in dimension 4 genuinely no longer holds.
   Removing Data Vault is a one-way trip in practice because the audit
   history accumulated in the vault's satellites has no equivalent
   representation in a simpler schema, so the historical trail is lost
   unless it is archived separately first.
2. Archive the raw vault's full history to cold storage before any removal,
   satisfying any residual audit or regulatory retention requirement
   independent of the live warehouse.
3. Rebuild the existing marts to source directly from the remaining source
   systems, or from the archived vault snapshot, rather than from the live
   vault.
4. Decommission the hub, link, satellite loading pipeline only after the
   marts have been running successfully against the new source for a full
   audit or reporting cycle, so a rollback path exists if a downstream
   consumer depended on vault behavior nobody had documented.

## 15. Testing and verification

Data Vault's insert-only, hash-key-based design makes several classes of
testing genuinely easier than testing an update-in-place dimensional model,
and makes one class of testing, business key correctness, genuinely harder,
because it cannot be verified purely technically.

Idempotency testing is straightforward, since re-running the same load twice
and asserting row counts are identical the second time directly verifies the
append-only, hash-diff-based deduplication described in dimension 7.
Referential integrity testing is also simplified, since hubs, links, and
satellites are never updated after insert, so a foreign key that was valid
at insert time stays valid forever, removing an entire class of
update-order race conditions that a mutable schema has to guard against.

Verifying that the chosen business key is actually correct and stable
cannot be automated as a unit test, because correctness depends on business
semantics the code has no way to check, for example whether a given
company's customer IDs are ever reused after a customer is deleted. This
has to be verified through domain expert review before the hub is built,
not after.

Practical testing techniques used against production Data Vault
implementations.

- **Hash key collision and consistency tests.** Feed the same business key
  through the normalization and hashing function twice, in two different
  process contexts, and assert identical hash output, catching the
  normalization-drift failure mode from dimension 11 before it reaches
  production.
- **Row count reconciliation between staging and hub.** Assert that the
  count of distinct normalized business keys in a staging batch equals the
  count of new hub rows inserted from it. A mismatch indicates either
  duplicate hashing or a business key that was not as unique as assumed.
- **Satellite hash_diff idempotency tests.** Load the identical staging
  batch twice and assert zero new satellite rows on the second load, the
  most direct test of the append-only correctness property and usually the
  first regression test written against a new satellite.
- **Referential completeness tests.** Assert that every link row's
  referenced hub keys exist in their respective hub tables before the link
  load runs, catching an out-of-order load (a link loaded before its hub)
  rather than allowing a dangling reference to persist silently.
- **dbt-based test suites.** Tools such as AutomateDV ship with generated
  dbt tests covering exactly these categories (uniqueness of hub business
  keys, referential integrity of link hash keys, not-null constraints on
  load date and record source) as a byproduct of the code generation
  approach, because the same metadata that generates the load SQL also
  generates the corresponding assertions ([AutomateDV on
  GitHub](https://github.com/Datavault-UK/automate-dv), verified
  2026-08-02).

## 16. Observability signals

What to log or measure so a Data Vault pipeline's health is visible.

- **Row insertion rate per hub, link, and satellite, per load cycle.** A
  healthy pattern shows hub and link insertion rates tapering off over time
  as the population of distinct entities and relationships stabilizes,
  while satellite insertion rates track the genuine rate of attribute
  change in the business. A hub insertion rate that never tapers, staying
  proportional to total record count rather than distinct entity count, is
  the earliest visible sign of the hash-key duplication failure mode from
  dimension 11.
- **Hash key collision counter.** An explicit check comparing distinct
  business key count to distinct hash key count on every hub load,
  surfaced as a metric rather than only as a test, since normalization
  drift can be introduced by a change months after the original tests were
  written and passed.
- **Satellite hash_diff hit rate.** The proportion of staged rows for a
  given hub or link that produce a new satellite row versus a no-op. A
  sudden, sustained jump toward one hundred percent for a previously stable
  satellite is the signature of the volatile-field-included-in-hash_diff
  failure mode from dimension 11.
- **Load latency per layer.** Time from staging arrival to hub load
  completion, and separately from hub load completion to satellite load
  completion, since the dependency ordering in dimension 7 means a slow hub
  load directly delays every downstream satellite and link that references
  it.
- **Referential orphan count.** A periodic check for link rows whose
  referenced hub hash key does not exist in the hub table, which should
  always be zero given the load ordering in dimension 7. A nonzero count
  indicates a load ran out of order or a hub load partially failed without
  the link load noticing.
- **Mart rebuild duration and freshness.** Since the information mart layer
  is disposable and rebuilt from the vault rather than incrementally
  maintained in some implementations, its rebuild time and the staleness
  window between a vault load and the mart reflecting it are direct,
  business-visible signals of whether the vault is delivering on its
  promise of being the reliable source the mart can always be regenerated
  from.

## 17. Security and privacy implications

Data Vault's append-only, never-delete-in-place design creates a specific and
well-documented tension with privacy regulation that mandates deletion, most
notably the right to erasure under GDPR and comparable regimes elsewhere.
Because a satellite's entire purpose is to retain every historical value a
business key has ever held, a naive implementation makes true deletion of a
specific individual's data structurally difficult without either destroying
the audit trail for every other entity sharing the same tables or building
deletion logic that contradicts the pattern's core insert-only guarantee.

Production implementations handle this in one of two ways, both requiring
deliberate design rather than arising automatically from the pattern.
Encryption-based erasure stores personally identifiable attributes in a
satellite encrypted with a per-entity key, and effectively deletes the data
by discarding the key rather than the row, leaving an unreadable but
structurally intact historical record that satisfies both the audit
requirement and the erasure requirement. Tombstone satellites explicitly
mark a hub as subject to erasure with a dedicated satellite row, and every
downstream mart-building process is required to honor that tombstone by
excluding the entity's other satellite history from any generated output,
while the raw history remains physically present for a defined retention
window before a genuine physical purge. This paragraph is engineering
judgement about common erasure strategies, not a claim traceable to a single
cited source.

The FinWise Bank case referenced in dimension 9 illustrates the positive
side of this same tension. The bank's use of dedicated, custom satellite
types specifically to isolate PII and PCI-classified attributes from other
descriptive data is exactly the structural separation that makes either
erasure strategy above tractable, since sensitive attributes needing special
handling are not commingled in a satellite with attributes that carry no
such requirement ([WhereScape, FinWise Bank case
study](https://www.wherescape.com/case-studies/finwise-bank/), verified
2026-08-02).

Beyond erasure, the record source and load date columns present on every
hub, link, and satellite row are themselves a security-relevant audit
surface. Because they trace every value back to the specific load process
and moment that introduced it, they are frequently the first place a
security or compliance investigation looks when establishing how a
specific incorrect or unauthorized value entered the warehouse, which is a
direct benefit of the pattern's design rather than an incidental one. This
observation is engineering judgement drawn from the pattern's stated audit
purpose rather than a claim traceable to a specific source.

## 18. References

- Wikipedia, "Data vault modeling", https://en.wikipedia.org/wiki/Data_vault_modeling, verified 2026-08-02.
- Databricks, "What is a Data Vault?", https://www.databricks.com/blog/what-is-data-vault, verified 2026-08-02.
- WhereScape, "FinWise Bank" case study, https://www.wherescape.com/case-studies/finwise-bank/, verified 2026-08-02.
- VaultSpeed, "The Bull Case for Data Vault", https://www.vaultspeed.com/blog/the-bull-case-for-data-vault, verified 2026-08-02.
- Datavault-UK, "automate-dv" repository, https://github.com/Datavault-UK/automate-dv, verified 2026-08-02.

## Code examples

Each sample implements the same minimal in-memory hub and satellite loader
directly from dimension 7's dynamics. hash the normalized business key into a
hub row that only ever inserts once, then load a satellite row only when the
computed hash_diff of its attributes differs from the most recent row for
that hub key. All three samples were compiled or run against the exact
toolchain versions listed in the template's availability table.

TypeScript, checked with `tsc --noEmit --strict` against Node type
definitions.

```typescript
import { createHash } from "crypto";

interface HubRow {
  hashKey: string;
  businessKey: string;
  loadDate: string;
  recordSource: string;
}

interface SatelliteRow {
  hashKey: string;
  loadDate: string;
  hashDiff: string;
  attributes: Record<string, string>;
  recordSource: string;
}

function normalizeBusinessKey(raw: string): string {
  return raw.trim().toUpperCase();
}

function hashKeyFor(businessKey: string): string {
  return createHash("sha256").update(normalizeBusinessKey(businessKey)).digest("hex");
}

function hashDiffFor(attributes: Record<string, string>): string {
  const ordered = Object.keys(attributes)
    .sort()
    .map((k) => `${k}=${attributes[k]}`)
    .join("|");
  return createHash("sha256").update(ordered).digest("hex");
}

class HubLoader {
  private rows = new Map<string, HubRow>();

  load(businessKey: string, loadDate: string, recordSource: string): HubRow {
    const hk = hashKeyFor(businessKey);
    const existing = this.rows.get(hk);
    if (existing) {
      return existing;
    }
    const row: HubRow = { hashKey: hk, businessKey: normalizeBusinessKey(businessKey), loadDate, recordSource };
    this.rows.set(hk, row);
    return row;
  }

  count(): number {
    return this.rows.size;
  }
}

class SatelliteLoader {
  private rows: SatelliteRow[] = [];

  load(hashKey: string, loadDate: string, attributes: Record<string, string>, recordSource: string): boolean {
    const diff = hashDiffFor(attributes);
    const latest = [...this.rows]
      .filter((r) => r.hashKey === hashKey)
      .sort((a, b) => (a.loadDate < b.loadDate ? 1 : -1))[0];
    if (latest && latest.hashDiff === diff) {
      return false;
    }
    this.rows.push({ hashKey, loadDate, hashDiff: diff, attributes, recordSource });
    return true;
  }

  count(): number {
    return this.rows.length;
  }
}

function main(): void {
  const hubs = new HubLoader();
  const sats = new SatelliteLoader();

  const a = hubs.load("cust-001", "2026-01-01", "crm");
  const b = hubs.load("CUST-001 ", "2026-01-02", "crm");
  console.assert(a.hashKey === b.hashKey, "normalized business key must collide onto one hub row");
  console.assert(hubs.count() === 1, "hub row count must stay at one for the same business key");

  const inserted1 = sats.load(a.hashKey, "2026-01-01", { name: "Ada", city: "Berlin" }, "crm");
  const inserted2 = sats.load(a.hashKey, "2026-01-02", { name: "Ada", city: "Berlin" }, "crm");
  const inserted3 = sats.load(a.hashKey, "2026-01-03", { name: "Ada", city: "Munich" }, "crm");
  console.assert(inserted1 === true, "first satellite load must insert");
  console.assert(inserted2 === false, "unchanged attributes must not insert a duplicate satellite row");
  console.assert(inserted3 === true, "a changed attribute must insert a new satellite row");
  console.assert(sats.count() === 2, "exactly two satellite rows expected after one real change");

  console.log("hub rows:", hubs.count(), "satellite rows:", sats.count());
}

main();
```

Python, checked with `python3 -m py_compile` and run directly.

```python
import hashlib
from dataclasses import dataclass


def normalize_business_key(raw: str) -> str:
    return raw.strip().upper()


def hash_key_for(business_key: str) -> str:
    return hashlib.sha256(normalize_business_key(business_key).encode()).hexdigest()


def hash_diff_for(attributes: dict) -> str:
    ordered = "|".join(f"{k}={attributes[k]}" for k in sorted(attributes))
    return hashlib.sha256(ordered.encode()).hexdigest()


@dataclass
class HubRow:
    hash_key: str
    business_key: str
    load_date: str
    record_source: str


@dataclass
class SatelliteRow:
    hash_key: str
    load_date: str
    hash_diff: str
    attributes: dict
    record_source: str


class HubLoader:
    def __init__(self) -> None:
        self._rows: dict[str, HubRow] = {}

    def load(self, business_key: str, load_date: str, record_source: str) -> HubRow:
        hk = hash_key_for(business_key)
        existing = self._rows.get(hk)
        if existing is not None:
            return existing
        row = HubRow(hk, normalize_business_key(business_key), load_date, record_source)
        self._rows[hk] = row
        return row

    def count(self) -> int:
        return len(self._rows)


class SatelliteLoader:
    def __init__(self) -> None:
        self._rows: list[SatelliteRow] = []

    def load(self, hash_key: str, load_date: str, attributes: dict, record_source: str) -> bool:
        diff = hash_diff_for(attributes)
        matches = [r for r in self._rows if r.hash_key == hash_key]
        latest = max(matches, key=lambda r: r.load_date, default=None)
        if latest is not None and latest.hash_diff == diff:
            return False
        self._rows.append(SatelliteRow(hash_key, load_date, diff, attributes, record_source))
        return True

    def count(self) -> int:
        return len(self._rows)


def main() -> None:
    hubs = HubLoader()
    sats = SatelliteLoader()

    a = hubs.load("cust-001", "2026-01-01", "crm")
    b = hubs.load("CUST-001 ", "2026-01-02", "crm")
    assert a.hash_key == b.hash_key, "normalized business key must collide onto one hub row"
    assert hubs.count() == 1, "hub row count must stay at one for the same business key"

    inserted1 = sats.load(a.hash_key, "2026-01-01", {"name": "Ada", "city": "Berlin"}, "crm")
    inserted2 = sats.load(a.hash_key, "2026-01-02", {"name": "Ada", "city": "Berlin"}, "crm")
    inserted3 = sats.load(a.hash_key, "2026-01-03", {"name": "Ada", "city": "Munich"}, "crm")
    assert inserted1 is True, "first satellite load must insert"
    assert inserted2 is False, "unchanged attributes must not insert a duplicate satellite row"
    assert inserted3 is True, "a changed attribute must insert a new satellite row"
    assert sats.count() == 2, "exactly two satellite rows expected after one real change"

    print("hub rows:", hubs.count(), "satellite rows:", sats.count())


if __name__ == "__main__":
    main()
```

Go, checked with `go vet` and run directly.

```go
package main

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"sort"
	"strings"
)

func normalizeBusinessKey(raw string) string {
	return strings.ToUpper(strings.TrimSpace(raw))
}

func hashKeyFor(businessKey string) string {
	sum := sha256.Sum256([]byte(normalizeBusinessKey(businessKey)))
	return hex.EncodeToString(sum[:])
}

func hashDiffFor(attributes map[string]string) string {
	keys := make([]string, 0, len(attributes))
	for k := range attributes {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	parts := make([]string, 0, len(keys))
	for _, k := range keys {
		parts = append(parts, k+"="+attributes[k])
	}
	sum := sha256.Sum256([]byte(strings.Join(parts, "|")))
	return hex.EncodeToString(sum[:])
}

type hubRow struct {
	hashKey      string
	businessKey  string
	loadDate     string
	recordSource string
}

type satelliteRow struct {
	hashKey      string
	loadDate     string
	hashDiff     string
	attributes   map[string]string
	recordSource string
}

type hubLoader struct {
	rows map[string]hubRow
}

func newHubLoader() *hubLoader {
	return &hubLoader{rows: make(map[string]hubRow)}
}

func (h *hubLoader) load(businessKey, loadDate, recordSource string) hubRow {
	hk := hashKeyFor(businessKey)
	if existing, ok := h.rows[hk]; ok {
		return existing
	}
	row := hubRow{hk, normalizeBusinessKey(businessKey), loadDate, recordSource}
	h.rows[hk] = row
	return row
}

func (h *hubLoader) count() int {
	return len(h.rows)
}

type satelliteLoader struct {
	rows []satelliteRow
}

func (s *satelliteLoader) load(hashKey, loadDate string, attributes map[string]string, recordSource string) bool {
	diff := hashDiffFor(attributes)
	var latest *satelliteRow
	for i := range s.rows {
		r := &s.rows[i]
		if r.hashKey != hashKey {
			continue
		}
		if latest == nil || r.loadDate > latest.loadDate {
			latest = r
		}
	}
	if latest != nil && latest.hashDiff == diff {
		return false
	}
	s.rows = append(s.rows, satelliteRow{hashKey, loadDate, diff, attributes, recordSource})
	return true
}

func (s *satelliteLoader) count() int {
	return len(s.rows)
}

func main() {
	hubs := newHubLoader()
	sats := &satelliteLoader{}

	a := hubs.load("cust-001", "2026-01-01", "crm")
	b := hubs.load("CUST-001 ", "2026-01-02", "crm")
	if a.hashKey != b.hashKey {
		panic("normalized business key must collide onto one hub row")
	}
	if hubs.count() != 1 {
		panic("hub row count must stay at one for the same business key")
	}

	inserted1 := sats.load(a.hashKey, "2026-01-01", map[string]string{"name": "Ada", "city": "Berlin"}, "crm")
	inserted2 := sats.load(a.hashKey, "2026-01-02", map[string]string{"name": "Ada", "city": "Berlin"}, "crm")
	inserted3 := sats.load(a.hashKey, "2026-01-03", map[string]string{"name": "Ada", "city": "Munich"}, "crm")
	if !inserted1 || inserted2 || !inserted3 {
		panic("satellite insert/no-op behavior did not match expectations")
	}
	if sats.count() != 2 {
		panic("exactly two satellite rows expected after one real change")
	}

	fmt.Println("hub rows:", hubs.count(), "satellite rows:", sats.count())
}
```

Java and Kotlin are omitted deliberately. The pattern's substance is a
warehouse-level modeling and loading discipline, not an object-oriented
class structure, and it translates identically into any language with a
hashing primitive and a map. Three languages already demonstrate that the
loader logic is language-agnostic; a fourth or fifth port would repeat the
same twenty lines with different syntax and add no new information about
the pattern itself.
