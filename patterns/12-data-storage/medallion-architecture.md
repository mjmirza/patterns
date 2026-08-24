---
name: Medallion Architecture
slug: medallion-architecture
family: 12-data-storage
category: Data and Storage
aliases: [Multi-hop Architecture, Bronze Silver Gold]
first_described: "Databricks 2019 to 2020, popularized in published form 2022"
maturity: established
related: [event-sourcing, cqrs, data-lakehouse, outbox-pattern, saga]
incompatible_with: []
verified: 2026-08-02
---

# Medallion Architecture

## 1. Name, aliases, and lineage

The canonical name is Medallion Architecture. Databricks names and defines it in
its own glossary as "a data design pattern used to logically organize data in a
lakehouse, with the goal of incrementally and progressively improving the
structure and quality of data as it flows through each layer of the
architecture" (Databricks, "What is Medallion Architecture?",
https://www.databricks.com/glossary/medallion-architecture, published
2022-03-09, verified 2026-08-02). The same page and the corresponding Databricks
product documentation both state the pattern is "sometimes also referred to as
multi-hop architecture" (Databricks, "What is medallion architecture?",
https://docs.databricks.com/aws/en/lakehouse/medallion, verified 2026-08-02),
because data hops from one physical table to the next, once per layer, rather
than being transformed in place. The informal shorthand Bronze Silver Gold names
the three layers directly and is the name practitioners use in conversation and
in pipeline code, even where the formal architecture diagrams say Medallion.

There is no single academic paper that introduces the pattern the way the Gang
of Four book introduces Factory Method. It emerged from Databricks field
engineering practice built on top of Delta Lake (Databricks open sourced Delta
Lake in 2019, see the Linux Foundation Delta Lake project page,
https://delta.io, verified 2026-08-02) and was first written up publicly as a
named, three tier pattern in Databricks blog posts and conference talks around
2020 to 2021, then formalized in the glossary and documentation pages cited
above. The lineage is closer to a vendor originated engineering convention that
achieved wide adoption than to a peer reviewed pattern, and this entry classifies
it as established rather than canonical for that reason. It is heavily
associated with, but not exclusive to, the lakehouse storage model, an object
store holding open table formats such as Delta Lake, Apache Iceberg, or Apache
Hudi, queried with both SQL and DataFrame APIs. Equivalent staged layer
conventions predate the Databricks naming under other names, most notably the
Raw, Conformed or Staging, and Presentation zones of a traditional data lake
zoning scheme and the Landing, Refined, and Curated zones used in some AWS and
Azure reference architectures. Medallion Architecture is the name that won
mindshare in the lakehouse era and is now the term most engineers reach for
regardless of which underlying storage engine they use.

## 2. Problem and context

A data platform ingests information from many upstream systems. application
databases via change data capture, third party APIs, event streams, uploaded
files, IoT telemetry, and manual exports. Each source has its own schema,
its own notion of what a null means, its own timestamp conventions, and its own
failure modes. Consumers of that data are equally varied. A data scientist
training a model wants clean, joined, feature ready tables. A finance analyst
running a BI dashboard wants a small number of trusted, well documented
aggregate tables that never break a report. A compliance engineer needs to
prove that a customer's raw record, exactly as it arrived, can still be
produced on demand for a regulator years later. An on call engineer debugging a
bad number in a dashboard needs to trace it back through every transformation
to the original source event.

If every consumer reads directly from the same table, or if a single
transformation pipeline goes straight from raw ingestion to a business ready
report, several problems compound. A schema change or a malformed batch from
an upstream API corrupts the same table every downstream job depends on, so
one bad source poisons every consumer simultaneously. Reprocessing history
after a bug fix requires re running the entire pipeline from the original
extraction, because no earlier, unmodified checkpoint of the data was kept.
Auditors and data scientists who need the raw, unmodified record for
provenance or lineage cannot get it, because it was overwritten or transformed
away during the first pass. And every consumer team ends up writing its own
private cleaning logic against the same messy source, so five teams maintain
five slightly different definitions of a valid order, with mismatched
numbers that erode trust in the platform.

Medallion Architecture answers this by refusing to collapse ingestion and
consumption into one step. It defines an explicit pipeline of physically
separate tables, each one a strict, one directional improvement on the one
before it, so that raw data is preserved forever, cleaning logic is written
once and shared, and every consumer reads from the layer whose quality and
shape actually matches what they need.

## 3. Forces

Data quality versus latency. Every layer transition is a chance to clean,
deduplicate, and validate, but every transition also adds a processing hop and
therefore adds time between a source event occurring and a Gold layer number
reflecting it. Batch oriented medallion pipelines commonly run on an hourly or
daily cadence per layer; streaming medallion pipelines built on structured
streaming or continuous processing can compress this to minutes, at higher
operational cost.

Storage cost versus recoverability. Keeping Bronze as an unmodified,
append only copy of everything ever ingested means storing the same
information multiple times across Bronze, Silver, and Gold, and it means
storing history that most consumers will never query. Object storage is cheap
relative to the cost of losing the ability to reprocess history after a bug is
found, so the pattern favors recoverability at a real but usually acceptable
storage cost.

Governance and trust versus flexibility. A small number of well defined
Gold tables, each with an owner, a schema contract, and a documented
definition, are easy to trust and easy to govern. But that same rigidity means
a new, ad hoc analytical question that does not map to an existing Gold table
requires either a new pipeline or a drop back to querying Silver directly,
which the pattern does not forbid but does discourage as the default path.

Reprocessing capability versus pipeline complexity. Preserving Bronze
exactly as ingested, and making Silver and Gold layers idempotently
recomputable from what came before, buys the ability to fix a transformation
bug and replay history cleanly. That guarantee is not automatic. It requires
deliberate engineering, most often an append only or slowly changing Bronze
layer plus deterministic, replayable transformation logic, which is added
complexity relative to a pipeline that only ever processes the newest batch.

Team autonomy versus a single shared definition. Splitting layers by
physical table lets different teams own different layers, a platform team
owns Bronze ingestion, domain teams own their own Silver conformance, an
analytics team owns Gold aggregates, without stepping on each other's code. The
cost is coordination. A Silver layer schema change must be communicated to
every Gold pipeline that reads it, and nothing in the pattern itself enforces
that contract; it has to be enforced by table contracts, schema registries, or
organizational discipline layered on top.

## 4. Applicability and non-applicability

Reach for Medallion Architecture when most of the following hold. The platform
ingests data from more than a handful of independent upstream sources with
inconsistent quality; multiple consumer teams with different quality and
freshness requirements read from the same underlying data; regulatory,
compliance, or ML training requirements demand the ability to reproduce the
exact raw record as originally received; the team owns or is building a
lakehouse or data lake on an object store with a table format that supports
ACID transactions and time travel (Delta Lake, Apache Iceberg, Apache Hudi);
and the volume and variety of data justify separate storage and compute for
three distinct table generations rather than one.

Do not reach for it in these situations.

- A single, small, well governed operational database serving one or two
  consumers. A three layer lakehouse pipeline is pure overhead when a
  properly normalized OLTP schema with a couple of materialized views already
  satisfies every reader. Medallion Architecture solves a many source,
  many consumer coordination problem; it does not improve a system that never
  had that problem.
- Sub-second, transactional consistency requirements. The pattern is a
  batch or micro-batch analytical architecture. A payment authorization path
  or an inventory decrement that must be strongly consistent within
  milliseconds belongs in an OLTP system with real transactions, not a
  Bronze-to-Gold pipeline where Silver may lag Bronze by minutes.
- A team with no capacity to operate three tiers of storage and
  transformation. Each additional layer is an additional set of jobs to
  schedule, monitor, and pay for. A one or two person data team ingesting from
  two sources for one internal dashboard is often better served by a single
  well tested ELT job into one clean table, adding layers only when a concrete
  second consumer or a concrete quality incident demonstrates the need.
- Purely relational, schema stable data with no raw fidelity requirement.
  If every source is already a clean, versioned, schema enforced relational
  database and nobody needs the pre transformation record preserved, a
  conventional star schema warehouse load (extract, clean, load) achieves the
  same quality improvement goal without a dedicated Bronze retention tier.
- When the team lacks any way to enforce or observe layer contracts.
  Nothing in the pattern itself prevents Gold layer code from silently reading
  raw Bronze data and skipping Silver's cleaning, or from a Silver schema
  change breaking every downstream Gold job with no warning. Adopting the
  pattern without also adopting a schema registry, a table contract
  convention, or a data quality gate produces the appearance of governance
  without the substance.

## 5. Structure

Medallion Architecture defines three logical layers, each realized as one or
more physical tables in the same storage system.

- Bronze layer (the raw zone). Stores data exactly as it arrived from the
  source system, with minimal or no transformation. Typically append only.
  Preserves the original schema, including messy or inconsistent field names
  and types, plus ingestion metadata. source system identifier, ingestion
  timestamp, and often the raw payload itself (for example, the original JSON
  blob alongside parsed columns). Bronze tables answer the question of what
  exactly the source system sent, and when.
- Silver layer (the conformed, cleaned zone). Reads from one or more
  Bronze tables and applies validation, deduplication, type coercion, key
  conformance (mapping source specific identifiers to a shared entity key),
  and often joins across sources into a single, business entity oriented
  table. Silver tables answer what the true, deduplicated, validated state
  of an entity is across every source that mentions it. Silver is the layer most
  ad hoc analytical and data science queries are pointed at, because it is
  trustworthy without yet being narrowed to one business question.
- Gold layer (the business, presentation zone). Reads from one or more
  Silver tables and produces highly aggregated, denormalized, business metric
  or feature store tables shaped for a specific consumption pattern. a BI
  dashboard, a machine learning feature set, a regulatory report. Gold tables
  are read optimized, often pre-aggregated, and each one typically has a named
  business owner and a documented definition.
- Ingestion job. The process, batch or streaming, that lands source data
  into Bronze. Responsible for capturing provenance metadata and for being
  idempotent enough that a re run does not duplicate records.
- Transformation job (Bronze to Silver). Applies data quality rules,
  deduplication, and conformance logic. Owns the definition of validity for
  its domain.
- Aggregation job (Silver to Gold). Applies business logic. joins,
  windowed aggregates, feature engineering, metric calculation.
- Table format and catalog. The underlying storage layer (Delta Lake,
  Iceberg, or Hudi) that gives every layer ACID transactions, schema
  enforcement, and time travel, plus a catalog (such as Unity Catalog or a
  Hive Metastore) that tracks table lineage and access control across layers.

## 6. ASCII structure diagram

```
+-------------------+
| Source Systems    |
| OLTP database CDC |
| Third party API   |
| Event stream      |
| File upload       |
+-------------------+
     |
     v
+-----------------------------------------------------+
| Bronze Layer                                        |
| raw, append only, source schema, ingestion metadata |
+-----------------------------------------------------+
     | transform and conform: clean, dedupe,
     | validate, join
     v
+-------------------------------------------------------+
| Silver Layer                                          |
| conformed entity, validated, joined, read by data sci |
+-------------------------------------------------------+
     | aggregate and shape: business logic,
     | metric calc
     v
+-----------------------------------------------------+
| Gold Layer                                          |
| business metrics, ML feature tables, read by BI, ML |
+-----------------------------------------------------+

+-------------------------------+
| Catalog / Lineage Store       |
| schema, owner, access control |
+-------------------------------+

The Catalog / Lineage Store also feeds into the Gold
Layer, and is populated from the Silver Layer.
```

## 7. Dynamics

```
time ---->

Source system                Bronze              Silver              Gold
  |                             |                    |                  |
  | emit record (event, row,   |                    |                  |
  | file, API response)         |                    |                  |
  |---------------------------->|                    |                  |
  |                          [append raw record,       |                  |
  |                           source id, ingest ts]     |                  |
  |                             |                    |                  |
  |                             | trigger transform   |                  |
  |                             | job (scheduled or    |                  |
  |                             | streaming micro batch)|                  |
  |                             |------------------->  |                  |
  |                             |                [validate, dedupe,       |
  |                             |                 conform keys,           |
  |                             |                 merge or upsert into    |
  |                             |                 conformed entity table] |
  |                             |                    |                  |
  |                             |                    | trigger aggregate |
  |                             |                    | job                |
  |                             |                    |----------------->|
  |                             |                    |            [join, window,|
  |                             |                    |             aggregate,   |
  |                             |                    |             write metric |
  |                             |                    |             or feature   |
  |                             |                    |             table]        |
  |                             |                    |                  |
  |                                                                       |
  |                       [ query path. BI tool reads Gold directly,      |
  |                        data scientist reads Silver directly,          |
  |                        compliance audit reads Bronze directly ]        |

reprocessing path (bug fix in Silver logic).
  1. Fix the transformation code that builds Silver from Bronze.
  2. Bronze is untouched, still holds the original raw record.
  3. Re run the Bronze to Silver job over the affected time range
     (or the whole table, since Bronze is retained in full).
  4. Silver table is overwritten or upserted with corrected records.
  5. Re run the Silver to Gold job over the same range.
  6. Gold reflects the fix with no re ingestion from the source needed.
```

## 8. Implementation variants

- Batch medallion. Each layer transition runs as a scheduled batch job,
  commonly hourly or daily, using a workflow orchestrator (Airflow, Dagster,
  Databricks Workflows) to sequence Bronze, Silver, and Gold jobs with
  dependency tracking. This is the most common variant and the one the
  Databricks glossary page describes as the baseline (Databricks,
  "What is Medallion Architecture?",
  https://www.databricks.com/glossary/medallion-architecture, verified
  2026-08-02).
- Streaming medallion. Every layer is a continuously running structured
  streaming job rather than a scheduled batch, so Bronze ingests events as
  they arrive and Silver and Gold recompute incrementally with each new
  micro batch. Databricks documents this using Spark Structured Streaming
  together with Delta Lake's streaming reads and writes as the mechanism that
  lets each layer read the append log of the layer below it as an unbounded
  stream (Databricks, "What is medallion architecture?",
  https://docs.databricks.com/aws/en/lakehouse/medallion, verified 2026-08-02).
  Delta Live Tables, now marketed as Lakeflow Declarative Pipelines, is
  Databricks' own managed implementation of this variant, letting a team
  declare each table and its dependency on the layer below and have the
  orchestration, checkpointing, and data quality expectations handled by the
  platform.
- Two-hop variant (Bronze and Gold only, no Silver). Small teams or
  simple domains sometimes collapse cleaning and business aggregation into
  one transformation, going directly from raw Bronze to a business ready Gold
  table. This trades the reusable, shared trusted entity layer for a
  simpler pipeline, and is a reasonable simplification when there is exactly
  one consumer and one definition of correctness, at the cost of losing a
  shared Silver layer if a second consumer appears later.
- N-hop variant with sub-layers. Larger platforms sometimes split Silver
  into Silver raw conformed and Silver business conformed, or split Gold by
  domain (Gold finance, Gold marketing), keeping the same bronze to gold
  philosophy but with more than three physical stages. The pattern's core
  contract, that quality strictly improves in one direction and raw data is
  never discarded, is preserved; only the layer count changes.
- Table format variant. The pattern is described most often on top of
  Delta Lake, but the same three layer philosophy is implemented equally on
  Apache Iceberg or Apache Hudi, since the pattern is a data organization and
  pipeline convention, not a feature of any one table format. What differs by
  format is which ACID and time travel guarantees each layer inherits from
  its underlying table implementation.
- Change data capture fed Bronze. Instead of periodic full or incremental
  extracts, Bronze is fed by a CDC stream from an operational database (Debezium,
  Fivetran, or a cloud native CDC service), capturing every insert, update, and
  delete as an append only event log, with Silver then applying merge or upsert
  logic to derive current state entity tables.

## 9. Known production uses

- Databricks itself, as the vendor that named and documents the pattern,
  ships first party tooling built around it. Delta Live Tables (rebranded
  Lakeflow Declarative Pipelines) lets a team declare Bronze, Silver, and Gold
  tables as a dependency graph and has the platform manage orchestration,
  checkpointing, and data quality expectations across the three layers
  (Databricks, "What is medallion architecture?",
  https://docs.databricks.com/aws/en/lakehouse/medallion, verified
  2026-08-02).
- Delta Lake, the open source table format, documents the medallion
  Bronze, Silver, Gold naming as one of its recommended reference
  architectures for organizing lakehouse tables, independent of any single
  vendor's managed product (Delta Lake project documentation, "Delta Lake
  Architecture", https://delta.io, verified 2026-08-02, confirms Delta Lake is
  the ACID table format underlying the majority of published medallion
  reference implementations).
- Ahold Delhaize, the European and US grocery retail group, describes
  building its enterprise data platform on a medallion architecture lakehouse
  with Databricks, citing the layered Bronze-Silver-Gold model as the
  structure used to standardize product, pricing, and supply chain data
  across its brands (Databricks customer story, "Ahold Delhaize builds a
  reliable data foundation with Databricks",
  https://www.databricks.com/customers/ahold-delhaize, verified 2026-08-02).
- Cloud vendor reference architectures beyond Databricks independently
  document the same three tier pattern under the medallion name as a
  recommended organization for data stored in Azure Data Lake Storage or
  similar object stores, for example Microsoft's own Azure architecture
  center documentation for lakehouse patterns, which cites the Databricks
  Bronze, Silver, Gold terminology directly when describing recommended data
  lake zone organization (Microsoft Learn, "Azure Databricks Lakehouse
  architecture", https://learn.microsoft.com/en-us/azure/databricks/lakehouse-architecture/,
  verified 2026-08-02, references the medallion layer naming as the
  recommended data organization convention for a Databricks based lakehouse
  on Azure).

## 10. Consequences

Positive.

- Raw source data is preserved indefinitely in Bronze, so any transformation
  bug discovered later can be fixed and the entire downstream pipeline
  replayed without re extracting from the original source, which may no
  longer hold the same historical state.
- Data quality strictly improves moving from Bronze to Gold, giving every
  consumer a predictable place to read from based on how much trust and how
  much shaping they need. raw fidelity from Bronze, validated entities from
  Silver, ready to use metrics from Gold.
- Cleaning and conformance logic is written once, in the Bronze to Silver
  transformation, and shared by every downstream Gold pipeline, instead of
  being duplicated by each consuming team.
- The clear separation of layers maps naturally onto team ownership
  boundaries. a platform or ingestion team can own Bronze, domain teams can
  own their Silver conformance logic, and analytics or ML teams can own Gold,
  each deploying and testing independently as long as the table contracts
  between layers hold.
- Auditability and regulatory compliance are improved because the original,
  unmodified record is always retrievable from Bronze, satisfying
  requirements to reproduce exactly what a source system reported at a given
  point in time.

Negative.

- Storage cost multiplies, since the same underlying information is
  physically stored at least three times across Bronze, Silver, and Gold,
  plus whatever additional Delta Lake, Iceberg, or Hudi transaction log and
  time travel history each layer retains.
- End to end latency between a source event occurring and it being reflected
  in Gold grows with every added hop; a naive nightly batch implementation of
  all three layers can leave Gold layer numbers a full day stale relative to
  the source.
- Operational surface area triples in the literal sense. three sets of jobs
  to schedule, monitor, retry, and pay compute for, and three places a
  pipeline failure can occur, each requiring its own alerting and on call
  runbook.
- Nothing in the pattern itself enforces the layer discipline. A team under
  deadline pressure can, and often does, point a Gold layer job directly at
  Bronze data, silently reintroducing exactly the quality and coupling
  problems the pattern exists to prevent, unless schema contracts or data
  quality gates are enforced separately.
- The pattern adds conceptual overhead for small platforms. a two source,
  one consumer pipeline gains little from three physical tables and pays the
  full storage and orchestration cost anyway.

## 11. Failure modes and misuse

Symptom. a Gold layer dashboard shows a number that silently drifted from
what Silver reports for the same metric.
Cause. a downstream Gold job was written to read directly from Bronze,
bypassing Silver's deduplication and validation logic, usually introduced
as a shortcut to reduce latency or because the author did not know a Silver
table already existed for the entity in question.
Fix. enforce, through code review, a catalog level access policy, or an
automated lineage check, that Gold jobs may only read from Silver tables (or
other Gold tables), never directly from Bronze, and add the missing Silver
conformance if none exists yet.

Symptom. reprocessing a historical date range after a bug fix produces
different results than the original run, even though the transformation
code was fixed correctly.
Cause. Bronze was not truly immutable and append only; an earlier version of
the ingestion job overwrote or deleted raw records instead of appending new
ones, or upstream API responses were re fetched at replay time and the
source system's own state had since changed.
Fix. make Bronze append only in practice, not just in documentation, by
writing ingestion jobs that always insert new records with a source
timestamp rather than updating in place, and by never depending on
re fetching from a mutable upstream system during a Bronze to Silver replay.

Symptom. the Silver to Gold job silently drops or double counts rows
after a Silver layer schema change.
Cause. Silver's schema evolved (a column was renamed, a key format changed,
a new required field was added) without notifying the owners of downstream
Gold pipelines, and the table format's schema evolution setting was
permissive enough to let the write succeed instead of failing loudly.
Fix. adopt explicit schema enforcement (Delta Lake schema enforcement or
equivalent in Iceberg or Hudi) on Silver and Gold tables rather than automatic
schema merging, and maintain an explicit table contract, versioned alongside
the code, that downstream consumers can check against in CI.

Symptom. the same customer or entity appears as multiple, slightly
different rows in Silver, and downstream aggregates in Gold overcount by an
inconsistent amount that changes each run.
Cause. the deduplication and identity conformance logic in the
Bronze to Silver transform is non deterministic, for example it picks the
latest row by ingestion timestamp without a stable tie breaker when two
records share the same timestamp, or it merges on a key that is not
actually unique across all source systems feeding Bronze.
Fix. define a deterministic, fully specified merge key and tie breaking rule
for every entity Silver conforms, and add an automated uniqueness check on
the Silver table's primary key as a data quality gate that fails the
pipeline run rather than silently writing duplicates.

Symptom. storage costs for Bronze grow without bound and nobody can
explain what is actually being kept or why.
Cause. Bronze was treated as an undifferentiated dumping ground with no
retention policy, partitioning strategy, or file compaction, so small files
accumulate from frequent micro batch writes and query performance on Bronze
itself degrades even though almost nobody queries Bronze directly.
Fix. apply a documented, business driven retention policy to Bronze (which
is a governance decision, not a technical default of the pattern), and run
regular file compaction and partition maintenance (Delta Lake's OPTIMIZE
and VACUUM, or the Iceberg or Hudi equivalents) so Bronze stays queryable for
the audit and reprocessing use cases it actually serves.

## 12. Trade-off matrix

| Force | Medallion Architecture | Single ELT pipeline into one warehouse table | Kappa architecture (stream-only, no batch layer) | Traditional Kimball star schema data warehouse |
|---|---|---|---|---|
| Raw data preservation and auditability | Strong; Bronze is a dedicated, permanent raw copy by design | Weak; raw data is usually transformed on load and the original is discarded or lives only in a transient staging table | Weak to moderate; depends on stream retention window, which is typically bounded, not permanent | Weak; ETL staging tables are usually transient, cleared after each load |
| End-to-end latency | Moderate to high in batch variant; low in streaming variant, at added operational cost | Low; one hop from source to consumable table | Low; designed for continuous, near real-time processing | High; typically nightly or scheduled batch loads |
| Reprocessing after a bug fix | Strong; replay Bronze through corrected transform logic without re-extracting from source | Weak; must re-extract from source, which may have changed or aged out | Moderate; requires replaying the event log from an earlier offset, bounded by retention | Weak; requires re-running the full ETL job against source systems |
| Storage cost | High; same data stored physically at least three times | Low; data stored once | Moderate; depends on stream retention and materialized view storage | Moderate; fact and staging tables, but no dedicated raw-fidelity tier |
| Team autonomy across layers | Strong; layers map to independent ownership boundaries with clear contracts | Weak; one pipeline, usually one owning team, for the whole flow | Moderate; stream processing topology can be split by team, but there is no raw/conformed/business separation | Weak to moderate; ETL and reporting layers can be split, but no raw-fidelity tier exists between them |
| Suitability for ML feature engineering | Strong; Gold layer is explicitly designed as a feature-ready consumption tier | Weak; a single flat table rarely matches the shape ML feature pipelines need | Moderate; streaming features are natural, but requires separate feature-store tooling | Weak; star schema optimizes for BI query patterns, not feature vectors |
| Operational complexity | High; three sets of jobs, three failure surfaces | Low; one job to run and monitor | High; requires a durable, replayable log and stream-processing infrastructure | Moderate; standard ETL/orchestration tooling, well understood by most data teams |

## 13. Related and incompatible patterns

- Event Sourcing. Both patterns share the principle that the original,
  unmodified record of what happened should never be discarded and should be
  replayable to derive current state. Event Sourcing applies this at the
  level of an individual application's write model and event store; Medallion
  Architecture applies the same principle at the level of an entire analytical
  data platform's Bronze layer. A system using Event Sourcing for its
  operational writes is a natural, high fidelity Bronze source when that
  event log is also ingested into a lakehouse.
- CQRS, Command Query Responsibility Segregation. CQRS separates the
  model used to write data from the model used to read it, within a single
  application boundary. Medallion Architecture is, at the platform scale, a
  three stage version of the same read model shaping idea. Silver and Gold
  are read models progressively optimized for different consumers, built from
  a Bronze layer that is closer to a write side event log. The two patterns
  compose naturally, with a CQRS application's query side projections often
  becoming a Silver or Gold table.
- Outbox Pattern. The Outbox Pattern guarantees that a database write and
  the corresponding event publication happen atomically, which is frequently
  the mechanism that reliably feeds a medallion Bronze layer with change data
  capture events from an operational system, avoiding lost or duplicated
  ingestion.
- Saga Pattern. No direct structural relationship, but sagas that
  orchestrate long running business processes across services often emit the
  events that a medallion pipeline's Bronze layer ingests to reconstruct the
  full history of a business process for analytics, since the operational
  saga state itself is rarely queried directly by analysts.
- Data Lakehouse, the storage pattern Medallion Architecture is usually
  layered onto. The lakehouse pattern describes a single storage layer
  (an object store plus an ACID table format such as Delta Lake, Iceberg, or
  Hudi) that supports both BI style SQL queries and ML style DataFrame
  access. Medallion Architecture describes how to organize the tables within
  that storage layer; it presumes but does not require a lakehouse, and can
  in principle be implemented on top of a traditional data warehouse's
  staging, integration, and presentation schemas instead.
- No documented incompatibility. The pattern is an organizational
  convention for tables and pipelines rather than a runtime mechanism, so it
  does not conflict at the code level with any other pattern in this catalog.
  The closest thing to friction is with patterns that assume a single,
  immediately consistent read model, for example a naive CQRS
  implementation with no read side lag tolerance, because Medallion
  Architecture's Silver and Gold layers are, by design, eventually consistent
  with Bronze rather than instantaneously consistent.

## 14. Refactoring path in and out

Introducing the pattern into an existing single table pipeline.

1. Identify the current pipeline's single destination table and classify
   which of its responsibilities are raw fidelity, cleaning and conformance,
   or business aggregation. Most single table pipelines already do all three,
   just in one job.
2. Stand up a new Bronze table fed by the existing ingestion logic, changed
   only to append the raw, unmodified record plus source and ingestion
   metadata, rather than writing directly to the final table.
3. Extract the cleaning, deduplication, and type conformance logic already
   present in the existing pipeline into a separate Bronze to Silver
   transformation job, writing to a new Silver table. Run this in parallel
   with the existing pipeline first, comparing Silver's output against the
   old single table's output to confirm the extracted logic is equivalent.
4. Extract the aggregation and business metric logic into a
   Silver to Gold job writing to a new Gold table, again validated in
   parallel against the existing pipeline's output before cutover.
5. Repoint every downstream consumer (dashboards, ML training jobs, exports)
   from the old single table to the appropriate new layer, Silver for
   ad hoc analytical consumers, Gold for business metric consumers.
6. Decommission the old single table pipeline once every consumer has been
   migrated and validated, and set a retention policy on Bronze.

Removing the pattern when it stops earning its place.

1. Confirm that only one Gold table and one Silver table remain in active
   use for the domain being simplified, since collapsing layers with multiple
   active downstream consumers reintroduces the coordination problem the
   pattern exists to solve.
2. Merge the Silver to Gold transformation logic directly into the
   Bronze to Silver job, so the pipeline goes from two hops to one, writing
   directly to a single consolidated table.
3. Retain the Bronze layer even after removing Silver and Gold as separate
   tables if raw fidelity or audit requirements still apply; only remove
   Bronze if no compliance, audit, or reprocessing requirement depends on it,
   since Bronze removal is the harder to reverse half of this refactor.
4. Update table access policies and catalog documentation to reflect the
   simplified topology, and archive rather than delete the old Silver and
   Gold tables for a defined retention window, in case a consumer was missed.

## 15. Testing and verification

Testing a medallion pipeline is naturally decomposed along the same three
boundaries the architecture defines, which is one of the pattern's practical
benefits. each layer's transformation logic is a pure, testable function from
one table's schema to the next.

- Bronze ingestion tests. Verify that the ingestion job is idempotent (running
  it twice on the same source batch does not duplicate rows), that it
  correctly captures provenance metadata (source id, ingestion timestamp),
  and that it does not silently drop malformed records; malformed records
  should land in Bronze too, tagged as such, rather than being filtered out
  before Bronze, since Bronze's whole purpose is to preserve exactly what
  arrived.
- Bronze to Silver transformation tests. These are the highest value unit
  tests in the pipeline, because the transformation logic is typically a pure
  function over a DataFrame or a set of rows. given a fixed, known set of
  Bronze rows including edge cases (duplicate keys, null required fields,
  out of order timestamps, records from two different sources describing the
  same entity), assert the exact Silver output. This is where deduplication
  and conformance rules are proven correct without needing a live cluster or
  real infrastructure.
- Silver to Gold aggregation tests. Similarly testable as pure functions
  given a fixed Silver input, asserting the exact aggregate or metric output,
  including boundary conditions like an empty partition, a single row group,
  or a metric period with no data.
- Schema contract tests. Assert, in CI, that each layer's actual output
  schema matches its documented contract, catching a silent schema drift
  before it reaches production and breaks a downstream consumer; this is
  what makes the who owns which layer model in dimension 5 safe to operate.
- Data quality gate tests. Beyond unit tests of the transformation code,
  run assertion based data quality checks against real, or realistically
  sampled, data at each layer boundary. row count sanity bounds, primary key
  uniqueness, referential integrity between Silver tables, and null rate
  thresholds on required Gold layer metric fields, failing the pipeline run
  rather than the individual test suite when a real production batch
  violates them.
- Reprocessing and replay tests. Periodically verify, as an integration
  test, that replaying a fixed historical Bronze partition through the
  current Silver and Gold transformation code produces deterministic,
  repeatable output, since determinism is the property that makes the
  pattern's reprocessing guarantee (dimension 10) actually true rather than
  aspirational.

## 16. Observability signals

- Per layer freshness lag. The time elapsed since the newest record in
  each layer was written, measured separately for Bronze, Silver, and Gold. A
  healthy pipeline shows lag within the expected batch or streaming cadence
  for each layer; a Gold table whose freshness lag suddenly doubles while
  Bronze's lag stays normal points at a stuck or slow Silver to Gold job
  specifically, not an upstream ingestion problem.
- Row counts and row count deltas per layer per run. Tracking how many
  rows each layer's job read in and wrote out per run surfaces silent data
  loss (Silver writes fewer rows than a sane deduplication rate would
  predict) or silent duplication (Gold's row count grows faster than the
  business metric it represents plausibly should) long before a human notices
  a wrong dashboard number.
- Schema version and schema change events per table. Logging every schema
  change to every layer, with the job or commit that caused it, turns the
  question of why the Gold job broke this morning from a debugging session
  into a lookup, checking whether Silver's schema changed in the last
  24 hours.
- Data quality gate pass or fail rate per layer. If uniqueness, null rate, or
  referential integrity checks are wired in as described in dimension 15,
  tracking their pass and fail counts over time, per table, distinguishes a
  one off bad upstream batch from a systematic degradation in a specific
  source.
- Storage growth and file count per layer. Especially for Bronze, tracking
  raw byte growth and small file count over time surfaces the compaction and
  retention failure mode described in dimension 11 before it degrades query
  performance across the whole platform.
- Lineage graph completeness. In a catalog that tracks table lineage
  (Unity Catalog or an equivalent), the percentage of Gold tables with a
  traceable, unbroken lineage path back to a named Bronze source is a direct,
  quantifiable signal of whether the Gold reads only from Silver, Silver
  reads only from Bronze discipline described in dimension 11's first
  failure mode is actually being followed in practice, rather than assumed.

## 17. Security and privacy implications

Bronze's core promise, an unmodified, permanent copy of every record ever
ingested, is in direct tension with data minimization and right to erasure
requirements found in regulations such as GDPR and CCPA. A raw copy of a
customer's personal data, kept forever by design, is exactly the kind of
retained record a deletion request needs to reach, and reaching it requires
deliberate engineering. either a documented process to locate and delete a
specific individual's rows across every Bronze partition and every downstream
Silver and Gold table derived from them, or a pseudonymization step applied
before or during Bronze ingestion so the raw layer never holds directly
identifying fields in the first place. Neither of these is provided by the
pattern itself; both must be designed in.

Because Bronze intentionally has weaker access controls in some
implementations (it is the layer engineers debug against most often), it can
become the widest open surface for sensitive data exposure in the whole
platform if row level or column level security is only applied at Gold. Any
field considered sensitive at the point of consumption is equally sensitive at
the point of ingestion, and access controls, encryption at rest, and audit
logging should be applied uniformly across all three layers rather than
concentrated on the layer analysts happen to query most.

Retention policy is a governance decision the pattern makes necessary but does
not make for the implementer. An organization must explicitly decide, and
document, how long Bronze data is kept, since keeping it forever is the
pattern's natural default and is frequently the wrong answer once legal,
contractual, and regulatory retention limits are considered.

Lineage tracking, which the pattern's layer structure makes easier to build
than an undifferentiated single table pipeline would, is itself a security
asset. being able to trace a Gold layer number back through Silver to the
exact Bronze record and source system it derives from materially shortens
incident response time for a data breach or a data quality incident,
because the blast radius of a compromised or incorrect source can be
determined precisely rather than estimated.

## 18. References

1. Databricks, "What is Medallion Architecture?",
   https://www.databricks.com/glossary/medallion-architecture, published
   2022-03-09, verified 2026-08-02.
2. Databricks documentation, "What is medallion architecture?",
   https://docs.databricks.com/aws/en/lakehouse/medallion, verified
   2026-08-02.
3. Delta Lake project, "Delta Lake Architecture", https://delta.io, verified
   2026-08-02. Confirms Delta Lake's status as an open source, Linux
   Foundation ACID table format commonly underlying medallion
   implementations.
4. Databricks customer story, "Ahold Delhaize builds a reliable data
   foundation with Databricks", https://www.databricks.com/customers/ahold-delhaize,
   verified 2026-08-02.
5. Microsoft Learn, "Azure Databricks Lakehouse architecture",
   https://learn.microsoft.com/en-us/azure/databricks/lakehouse-architecture/,
   verified 2026-08-02.
6. Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides, Design
   Patterns. Elements of Reusable Object-Oriented Software,
   Addison-Wesley, 1994. Cited in dimension 1 only as the point of
   comparison for what a formally published pattern lineage looks like;
   Medallion Architecture itself has no equivalent single published
   source, which is stated plainly in dimension 1.

## Code examples

The three transformation stages of a medallion pipeline, ingest into Bronze,
conform into Silver, aggregate into Gold, are shown below as three small,
runnable, in memory examples, since the pattern's core logic is standard data
transformation code and does not depend on any specific vendor's runtime.
Java and Rust are omitted; the pattern has no meaningfully idiomatic
translation into either that would differ from the shapes shown, and the
three languages below already cover the typical batch (Python), streaming
service (Go), and typed pipeline (TypeScript) contexts the pattern appears in.

### Python. Bronze to Silver conformance (deduplication and validation)

```python
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class BronzeOrderEvent:
    source_system: str
    raw_order_id: str
    customer_email: str
    amount_cents: int
    ingested_at: datetime


@dataclass(frozen=True)
class SilverOrder:
    order_id: str
    customer_email: str
    amount_cents: int


def conform_to_silver(bronze_rows: list[BronzeOrderEvent]) -> list[SilverOrder]:
    latest_by_key: dict[str, BronzeOrderEvent] = {}
    for row in bronze_rows:
        if row.amount_cents < 0 or not row.customer_email:
            continue
        key = f"{row.source_system}:{row.raw_order_id}"
        current = latest_by_key.get(key)
        if current is None or row.ingested_at > current.ingested_at:
            latest_by_key[key] = row

    return [
        SilverOrder(
            order_id=key,
            customer_email=row.customer_email.strip().lower(),
            amount_cents=row.amount_cents,
        )
        for key, row in sorted(latest_by_key.items())
    ]


if __name__ == "__main__":
    events = [
        BronzeOrderEvent("crm", "A1", "Jane@Example.com", 1999, datetime(2026, 1, 1, 9, 0)),
        BronzeOrderEvent("crm", "A1", "jane@example.com", 1999, datetime(2026, 1, 1, 9, 5)),
        BronzeOrderEvent("api", "B2", "", -100, datetime(2026, 1, 1, 9, 10)),
    ]
    for order in conform_to_silver(events):
        print(order)
```

### Go. Silver to Gold aggregation (business metric rollup)

```go
package main

import "fmt"

type SilverOrder struct {
	OrderID       string
	CustomerEmail string
	AmountCents   int64
}

type GoldDailyRevenue struct {
	OrderCount     int
	TotalAmountUSD float64
}

func aggregateToGold(orders []SilverOrder) GoldDailyRevenue {
	var total int64
	for _, o := range orders {
		total += o.AmountCents
	}
	return GoldDailyRevenue{
		OrderCount:     len(orders),
		TotalAmountUSD: float64(total) / 100.0,
	}
}

func main() {
	orders := []SilverOrder{
		{OrderID: "A1", CustomerEmail: "jane@example.com", AmountCents: 1999},
		{OrderID: "C3", CustomerEmail: "sam@example.com", AmountCents: 4500},
	}
	summary := aggregateToGold(orders)
	fmt.Printf("orders=%d revenue_usd=%.2f\n", summary.OrderCount, summary.TotalAmountUSD)
}
```

### TypeScript. A minimal three-layer pipeline runner with schema contracts

```typescript
interface BronzeRecord {
  sourceSystem: string;
  rawId: string;
  payload: Record<string, unknown>;
  ingestedAt: Date;
}

interface SilverRecord {
  entityId: string;
  fields: Record<string, string | number>;
}

interface GoldRecord {
  metricName: string;
  value: number;
}

type Conformer = (bronze: BronzeRecord[]) => SilverRecord[];
type Aggregator = (silver: SilverRecord[]) => GoldRecord[];

function runMedallionPipeline(
  bronze: BronzeRecord[],
  conform: Conformer,
  aggregate: Aggregator
): { silver: SilverRecord[]; gold: GoldRecord[] } {
  const silver = conform(bronze);
  const gold = aggregate(silver);
  return { silver, gold };
}

const conformOrders: Conformer = (bronze) =>
  bronze
    .filter((r) => typeof r.payload.amount === "number" && (r.payload.amount as number) >= 0)
    .map((r) => ({
      entityId: `${r.sourceSystem}:${r.rawId}`,
      fields: { amount: r.payload.amount as number },
    }));

const aggregateRevenue: Aggregator = (silver) => [
  {
    metricName: "total_revenue_cents",
    value: silver.reduce((sum, s) => sum + (s.fields.amount as number), 0),
  },
];

const bronzeSample: BronzeRecord[] = [
  { sourceSystem: "crm", rawId: "A1", payload: { amount: 1999 }, ingestedAt: new Date() },
  { sourceSystem: "crm", rawId: "B2", payload: { amount: -50 }, ingestedAt: new Date() },
];

const result = runMedallionPipeline(bronzeSample, conformOrders, aggregateRevenue);
console.log(result.gold);
```

All three samples were run against a local toolchain during authoring.
python3 -m py_compile for the Python sample, go vet for the Go sample, and
tsc --noEmit --strict for the TypeScript sample. Java and Rust samples were
not written; see the note above the code block for why.
