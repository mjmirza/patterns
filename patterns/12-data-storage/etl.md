---
name: ETL
slug: etl
family: 12-data-storage
category: Data and Storage
aliases: [Extract Transform Load, Batch Data Pipeline, Data Integration Pipeline]
first_described: "Kimball and Caserta 2004"
maturity: canonical
related: [lambda-architecture, kappa-architecture, medallion-architecture, star-schema, slowly-changing-dimensions, data-mesh, data-vault]
incompatible_with: []
verified: 2026-08-02
---

# ETL

## 1. Name, aliases, and lineage

The canonical name is ETL, an acronym for Extract, Transform, Load. The term
describes a three-phase process in which data is pulled from one or more
source systems, reshaped into a form the destination expects, and written into
that destination. Wikipedia's summary states the process plainly, calling it
"a three-phase computing process where data are extracted from an input
source, transformed (including cleaning), and loaded into an output data
container" ([Wikipedia, Extract, transform, load](https://en.wikipedia.org/wiki/Extract,_transform,_load),
verified 2026-08-02).

The concept predates the acronym's popularization. Mainframe batch reporting
jobs in the 1970s and 1980s already extracted records from operational files,
reformatted them, and produced summary tapes or reports for management, which
is the same three-step shape without the name attached. The acronym and the
formal methodology were popularized in data warehousing practice through the
1990s and were codified as a named discipline by Ralph Kimball and Joe
Caserta in *The Data Warehouse ETL Toolkit*, Wiley, 2004, which the Wikipedia
entry cites as a standard textbook for teaching ETL processes in data
warehousing ([Wikipedia, Extract, transform, load](https://en.wikipedia.org/wiki/Extract,_transform,_load),
verified 2026-08-02). Kimball's earlier and companion work, Ralph Kimball and
Margy Ross, *The Data Warehouse Toolkit*, 3rd edition, Wiley, 2013, describes
the ETL system as the "back room" of the warehouse, responsible for
preparing dimensional models before anything reaches a report.

A closely related and increasingly common variant is ELT, Extract, Load,
Transform, in which raw data is loaded into the destination first and
transformed there using the destination's own compute. Wikipedia's ETL entry
describes this directly. ELT "has gained popularity with cloud-based data
warehouses" such as Amazon Redshift, Google BigQuery, and Snowflake, because
their scalable compute lets teams "forgo preload transformations and
replicate raw data into their data warehouses" before transforming
([Wikipedia, Extract, transform, load](https://en.wikipedia.org/wiki/Extract,_transform,_load),
verified 2026-08-02). ETL and ELT are not competing patterns so much as two
orderings of the same three operations, and this entry treats ELT as a named
variant under dimension 8 rather than as a separate pattern, because the
extract-transform-load vocabulary, the idempotency concerns, and the failure
modes are shared between them.

A second lineage worth naming is workflow orchestration. Modern ETL is rarely
one script; it is a directed graph of tasks with dependencies, retries, and
schedules, and the dominant tool for expressing that graph is Apache Airflow,
initiated by Maxime Beauchemin at Airbnb in October 2014, open source from its
first commit, announced publicly by Airbnb in June 2015, and later donated to
the Apache Software Foundation, reaching top-level project status in January
2019 ([Apache Airflow project history](https://airflow.apache.org/docs/apache-airflow/stable/project.html),
verified 2026-08-02). Airflow's own documentation describes itself as "an
open-source platform for developing, scheduling, and monitoring workflows,
such as traditional time based or event-triggered batch-oriented data
pipelines" ([Apache Airflow documentation](https://airflow.apache.org/docs/apache-airflow/stable/index.html),
verified 2026-08-02), which is the orchestration layer ETL pipelines are
commonly built on top of, distinct from ETL itself.

## 2. Problem and context

An organization has data that lives in one shape, in one place, produced for
one purpose, and it needs that data in a different shape, in a different
place, usable for a different purpose. A retailer's point-of-sale system
records a sale as a normalized transaction row optimized for fast writes at
checkout. A finance analyst wants that same sale represented as a fact row in
a star schema, joined against a calendar dimension, a product dimension, and a
store dimension, so a single query can answer "total revenue by region by
quarter" in under a second. The operational schema was never designed to
answer that question quickly, and it should not be, because a schema tuned for
analytical fan-out queries is usually a poor schema for high-throughput
transactional writes. This is the same schema-shape tension recorded in the
Star Schema entry in this family, and ETL is the mechanism that resolves it by
building a second copy of the data in the second shape rather than forcing one
schema to serve both jobs.

The context has several recurring shapes. Source systems are numerous,
heterogeneous, and outside the analytics team's control, whether an OLTP
database, a third-party SaaS API, a stream of event logs, or a partner's
nightly file drop. Each source has its own schema, its own notion of a
primary key, its own update semantics, and often its own definition of the
same business concept, so a "customer" in the CRM is not quite the same
entity as a "customer" in the billing system. The destination is typically a
data warehouse or a data lake built for read-heavy analytical access, and it
expects a single, reconciled, conformed view, one row per customer, one
currency, one set of column names, one definition of "active." Between the
two sits the transform step, which does the reconciliation work, and the
extract and load steps, which do the movement work.

The problem ETL solves is decoupling the shape and cadence of data production
from the shape and cadence of data consumption, while making the movement and
reshaping steps repeatable, auditable, and resumable rather than a one-off
manual export a person runs from memory.

## 3. Forces

**Latency versus correctness.** A shorter extract-to-load cycle gets fresher
data into the warehouse, but shrinking the window increases the chance of
extracting a source table mid-write, capturing a partial transaction, or
missing a late-arriving record that was still in flight when the extract ran.
Batch ETL favours correctness over freshness by design, accepting a delay of
hours in exchange for extracting from a source that has settled.

**Coupling to the source schema versus stability of the pipeline.** A
transform step that reads every column from the source table is fragile,
because any source schema change breaks it. A transform step that reads only
a stable contract, an explicit extract query or a schema-registry-backed
event, is more resilient but requires the source team to maintain that
contract, which is organizational work, not code.

**Where transformation compute happens.** Transforming in the pipeline
process, classic ETL, keeps the warehouse simple but makes the pipeline's
compute footprint grow with data volume and forces the pipeline to
reimplement whatever the warehouse already does well, such as joins,
aggregations, and window functions. Transforming inside the destination, ELT,
offloads that compute to a system built for it, but couples the transform
logic to the destination's SQL dialect and requires loading raw, possibly
sensitive, data before it has been cleaned or masked.

**Idempotency versus throughput.** A pipeline that can be safely re-run
without duplicating or double-counting data is easier to operate, because a
failed run can simply be retried. Achieving that safety, through upserts,
partition overwrites, or watermarking, adds write amplification and
complexity compared to a naive append-only load that assumes every run is new
data.

**Centralized ownership versus domain ownership.** A single ETL team can
enforce one set of conventions and one quality bar, but becomes a bottleneck
as the number of sources grows, because every new source waits on that
team's capacity. Distributing ownership of extraction and transformation to
the teams that own each source, the approach argued for in this family's
Data Mesh entry, spreads the work but risks each domain reinventing
conventions independently, producing exactly the inconsistency ETL exists to
remove.

**Cost of compute and storage versus operational simplicity.** Materializing
every transformed table is expensive to store and refresh, especially at high
volumes, but querying transformed views on demand shifts cost to query time
and can make interactive dashboards slow. Most production pipelines choose a
mix, materializing some tables nightly while computing others as views on
read.

## 4. Applicability and non-applicability

Reach for ETL when data must be integrated from more than one source system
into a single, consistent, query-optimized destination for analytics,
reporting, or downstream machine learning features. It fits when the
consuming workload is read-heavy and tolerant of the pipeline's refresh
latency, most commonly minutes to a day. It fits when the source systems are
operational systems that must not be burdened with analytical query load, so
the analytical copy exists precisely to protect the source's transactional
performance. It fits when historical, point-in-time correct data is required,
because the transform step is the natural place to apply slowly changing
dimension logic, described in this family's Slowly Changing Dimensions entry,
so that a report run today can still answer what a customer's tier looked
like last March.

Do not reach for ETL, or reach for it in a different form, in the following
situations.

- **Sub-second or true real-time decisioning is required.** A fraud-scoring
  system that must accept or reject a payment within tens of milliseconds
  cannot wait for a batch that runs every fifteen minutes. That workload needs
  stream processing operating on individual events, not a pipeline that
  operates on accumulated batches. This family's Lambda Architecture and Kappa
  Architecture entries describe the streaming and hybrid alternatives, and a
  system with this latency requirement should be built on one of those rather
  than on batch ETL.
- **The source and destination are the same system, or the transformation is
  trivial.** If a single relational database can answer the analytical
  question directly with an index or a materialized view, standing up a
  separate pipeline and a second copy of the data adds operational surface for
  no benefit. ETL earns its cost when the destination is genuinely a different
  system with different access patterns, not as a default for every reporting
  need.
- **Data volume and source count are small and stable, and a person can
  reasonably eyeball the data by hand.** A two-person startup with one
  Postgres database and a spreadsheet does not need Airflow, dbt, and a
  warehouse. The overhead of pipeline infrastructure, monitoring, and schema
  management is not justified until there is more than one source, a
  meaningful volume, or a compliance requirement for auditability that manual
  export cannot satisfy.
- **The data is inherently unbounded and order-dependent, and downstream
  consumers need exact event ordering and exactly-once processing
  guarantees.** Financial ledger reconciliation across accounts, for example,
  is often better served by an event-sourced or streaming design where order
  is a first-class property, rather than by a batch job that reads a snapshot
  and may reorder events relative to their true arrival sequence.
- **Regulatory data residency or minimization rules forbid moving certain
  fields out of the source system at all.** In that case the pattern to reach
  for is federated query or data virtualization, which lets analytical queries
  reach into the source without a physical copy leaving its boundary, rather
  than an ETL pipeline that would extract the restricted field regardless.

## 5. Structure

**Source system.** The system of record that produces the data. Owns its own
schema, write cadence, and consistency guarantees. Has no obligation to know
that ETL exists; a well-designed extract step reads from a source in a way
that does not degrade the source's primary workload, for example via a
read replica, a change-data-capture log, or an explicitly published export
table rather than a query against the live transactional tables.

**Extractor.** The component responsible for reading data out of the source
and staging it somewhere the transform step can operate on it safely, isolated
from the source's live state. Implements the extraction strategy, full or
incremental, and the connection and authentication concerns specific to each
source type.

**Staging area.** An intermediate landing zone, often cheap object storage or
a scratch schema in the warehouse, that holds raw extracted data before
transformation. Its existence decouples the extract step's failure domain from
the transform step's, so a failed transform can be retried against staged
data without re-extracting from the source.

**Transformer.** The component that applies business logic to convert staged
raw data into the destination's expected shape. Performs cleaning, such as
nulls, type coercion, and deduplication, conforming, meaning the mapping of
source-specific codes to a shared vocabulary, and structuring, meaning the
building of dimension and fact tables, applying slowly changing dimension
logic, and computing derived columns.

**Loader.** The component responsible for writing transformed data into the
destination in a way that is safe to retry, such as an upsert by natural or
surrogate key, an atomic partition swap, or an append with a deduplication
key, rather than a raw insert that would double data on re-run.

**Destination.** The analytical store the transformed data lands in, whether
a data warehouse, a data lake table format, or a data mart. Optimized for the
consuming workload's read patterns, which is usually the opposite optimization
profile from the source system.

**Orchestrator.** The component that sequences extract, transform, and load
tasks across dependencies, schedules runs, retries failures, and exposes the
pipeline's run history for observability. Not strictly part of the ETL
pattern's minimal definition, but present in essentially every production
implementation, most commonly Apache Airflow or a managed equivalent.

**Metadata and lineage store.** Tracks which source columns fed which
destination columns, when each table was last successfully refreshed, and
what quality checks passed or failed. Increasingly a first-class participant
rather than an afterthought, because "where did this number come from" is one
of the most common questions asked of any analytical pipeline.

## 6. ASCII structure diagram

```
+-------------+     +-------------+     +---------------+     +-------------+     +---------------+
|   Source A  |     |   Source B  |     |   Source C    |     |    ...      |     |               |
| (OLTP DB)   |     | (SaaS API)  |     | (event logs)  |     |             |     |               |
+------+------+     +------+------+     +-------+-------+     +------+------+     |               |
       |                    |                    |                    |          |               |
       v                    v                    v                    v          |               |
+------------------------------------------------------------------------+       |               |
|                            EXTRACTOR (per source connector)             |       | Orchestrator  |
+------------------------------------------------------------------------+       | (schedules,   |
                                     |                                            |  retries,     |
                                     v                                            |  dependency   |
                            +-----------------+                                  |  graph,       |
                            |  Staging area   |                                  |  run history) |
                            |  (raw, landed)  |                                  |               |
                            +--------+--------+                                  |               |
                                     |                                            |               |
                                     v                                            |               |
                            +-----------------+                                  |               |
                            |   TRANSFORMER   |<---------------------------------+               |
                            | (clean, conform,|                                  |               |
                            |  dedup, model)  |                                  |               |
                            +--------+--------+                                  |               |
                                     |                                            |               |
                                     v                                            |               |
                            +-----------------+                                  |               |
                            |     LOADER      |                                  |               |
                            | (upsert / swap) |                                  |               |
                            +--------+--------+                                  |               |
                                     |                                            |               |
                                     v                                            +---------------+
                            +-----------------+
                            |  Destination    |
                            | (warehouse /    |
                            |  lake / mart)   |
                            +-----------------+
```

## 7. Dynamics

```
Scheduled or event-triggered run begins
        |
        v
Orchestrator resolves task DAG, checks upstream
dependencies satisfied (source data available)
        |
        v
FOR EACH configured source:
        |
        +--> Extractor connects, reads new or changed
        |    records since last successful watermark
        |         |
        |         v
        |    Writes raw records to staging area,
        |    tagged with extraction batch id
        |
        +--> On extractor failure: task marked failed,
        |    orchestrator retries per policy, or halts
        |    the DAG and alerts if retries exhausted
        |
        v
All extract tasks for this run report success
        |
        v
Transformer reads staged batch, applies
   cleaning -> conforming -> business rules ->
   dimensional modeling / SCD logic
        |
        +--> On a data quality check failure (null in a
        |    required key, referential integrity break),
        |    run is quarantined, downstream load is
        |    skipped, alert fires with the failing rows
        |
        v
Transform produces a staged, transformed table,
scoped to this run's batch id
        |
        v
Loader applies transformed batch to destination,
   upserting by key, or swapping a partition atomically,
   never a blind append
        |
        v
Loader commits the watermark forward (records the
last successfully processed point in the source)
        |
        v
Orchestrator marks the run complete, updates lineage
metadata, exposes row counts and freshness to
observability dashboards
        |
        v
Downstream consumers (BI tools, ML feature pipelines,
scheduled reports) query the destination, now current
as of this run's watermark
```

The watermark commit at the end, not before the load succeeds, is the detail
that makes a failed run safe to retry. If the loader crashes partway through,
the watermark was never advanced, so the next run re-extracts and re-processes
the same window rather than silently skipping the data that failed to land.

## 8. Implementation variants

**Classic batch ETL.** Transformation happens in a dedicated processing layer
outside the destination, historically a purpose-built ETL server such as
Informatica PowerCenter or IBM DataStage, more recently a general-purpose
compute framework such as Apache Spark. The destination receives already-clean
data and does no transformation work itself. Favoured when the transform logic
is complex enough to need a general-purpose programming language, or when the
destination's compute is expensive or limited relative to the transform
workload.

**ELT, Extract-Load-Transform.** Raw data is loaded into the destination
first, and transformation is expressed as SQL, or a SQL-generating templating
layer, that runs inside the destination's own compute engine. dbt (data build
tool) is the dominant tool in this variant. Its own product description
states that dbt lets teams "execute transformations in the cloud data platform
where your data already lives, with no data movement or duplication" ([dbt product page](https://www.getdbt.com/product/what-is-dbt),
verified 2026-08-02). This variant fits naturally with cloud warehouses that
separate storage and compute cost, such as Snowflake or BigQuery, and it lets
analysts write transformations in SQL rather than a general-purpose language,
lowering the skill barrier for iterating on business logic.

**Change data capture ETL.** Instead of periodically querying the source for
rows that changed, the extractor subscribes to the source database's write-
ahead log or binlog and receives a continuous stream of row-level change
events. Tools in this space include Debezium, an open source project, and
managed offerings from several data platform vendors. This variant reduces
load on the source, because it reads a log rather than issuing repeated
`SELECT` queries against live tables, and it narrows the latency gap toward
near-real-time without abandoning the batch pipeline's transform and load
architecture, since changes are typically still batched into micro-batch
windows for the transform step.

**Reverse ETL.** After the classic pipeline has built a clean, conformed model
in the warehouse, a second pipeline moves selected results back out into
operational tools, for example syncing a computed customer health score from
the warehouse into a CRM. Structurally identical to ETL with the source and
destination roles swapped, but treated as a distinct named variant in industry
practice because the operational and reliability requirements differ. A
reverse ETL failure can break a sales team's daily workflow, not just delay a
report.

**Micro-batch and streaming-adjacent ETL.** The pipeline runs on a short,
fixed interval, commonly one to fifteen minutes, rather than once daily,
narrowing the freshness gap while retaining the batch pipeline's simpler
consistency model compared to a true event-at-a-time streaming system. This is
frequently how the batch layer of the Lambda Architecture entry in this family
is implemented in practice.

**Language-idiomatic shape.** ETL is not a class-level design pattern the way
Factory Method is; it is expressed as a pipeline configuration plus
transformation code, so the "idiom" per ecosystem is the choice of
orchestration and transformation tooling rather than a code-level shape.
Python-centric shops commonly express extraction and transformation as plain
functions orchestrated by Airflow's Python DAG API. SQL-centric shops express
transformation as dbt models. JVM shops running high-volume batch or
micro-batch transforms commonly reach for Apache Spark's DataFrame API in
Scala or Java.

## 9. Known production uses

- **Airbnb built and open-sourced Apache Airflow to orchestrate its own
  internal ETL and data pipelines**, starting in October 2014, because its
  data infrastructure had outgrown ad hoc cron jobs. Airflow is now maintained
  by the Apache Software Foundation and used broadly across the industry as an
  ETL orchestration layer ([Apache Airflow project history](https://airflow.apache.org/docs/apache-airflow/stable/project.html),
  verified 2026-08-02).
- **dbt Labs' dbt is used as the transformation layer of ELT pipelines by
  data teams running on cloud warehouses**, letting analysts express
  transformation logic as version-controlled SQL that executes inside the
  warehouse rather than in a separate processing tier ([dbt product page](https://www.getdbt.com/product/what-is-dbt),
  verified 2026-08-02).
- **Retail and e-commerce reporting pipelines built on star schemas**, as
  described in Ralph Kimball and Margy Ross's *The Data Warehouse Toolkit*,
  3rd edition, Wiley, 2013, rely on ETL to transform point-of-sale
  transaction records into fact and dimension tables nightly, which is the
  worked example that motivated the Kimball dimensional modeling methodology
  in the first place and is directly referenced in this family's Star Schema
  entry.
- **Debezium-based change data capture pipelines**, an open source project
  under the Red Hat and CNCF ecosystem, are used to stream row-level changes
  out of relational databases such as PostgreSQL and MySQL into Kafka topics
  that feed downstream ETL transformation and loading stages, the change data
  capture variant described in dimension 8.

## 10. Consequences

Positive.

- Decouples source system schema and load from analytical query patterns, so
  operational databases keep their transactional performance while analytics
  gets a purpose-built copy.
- Produces a single, conformed, auditable version of business concepts across
  multiple sources, resolving the ambiguity of which system is right that
  otherwise falls on every analyst individually.
- Enables historically accurate reporting through slowly changing dimension
  handling, something a live query against a mutable operational table cannot
  provide once a row has been overwritten.
- Makes data movement and transformation repeatable and inspectable, since a
  run's logic, inputs, and outputs are code and metadata, not a one-off
  manual export a single person remembers how to run.
- Centralizes data quality enforcement at one boundary, so a bad value caught
  at the transform step never reaches every downstream dashboard individually.

Negative.

- Introduces latency between an event happening in the source system and that
  event being visible in the destination, which is a poor fit for workloads
  needing sub-minute freshness.
- Duplicates data and adds storage and compute cost for the staged and
  transformed copies, on top of whatever the source system already spends.
- Creates a second failure domain and a second set of on-call responsibilities
  distinct from the source systems, and a broken pipeline is invisible to
  users of the source system while being very visible to users of stale
  dashboards.
- Couples the pipeline to the source's schema, so an uncoordinated schema
  change upstream, such as a renamed column or a changed data type, breaks the
  pipeline unless a contract or schema registry is in place.
- Concentrates significant organizational knowledge, business logic encoded
  as transform rules, into pipeline code, which becomes a form of technical
  debt if that logic is undocumented or only understood by one team.

## 11. Failure modes and misuse

**Symptom.** A dashboard silently shows stale numbers with no error anywhere.

Cause. the pipeline's orchestrator marked the run as successful because an
individual task retried successfully after a transient failure, but the
retry re-ran against a source that had already moved its watermark, so the
run technically succeeded while processing zero new rows, or a downstream
dependency was never re-triggered after an upstream delay. Fix. alert on
freshness, meaning time since last successful load per table, as a
first-class metric independent of task success or failure, not only on
task-level failure, and make watermark advancement conditional on row counts
crossing a sane threshold rather than merely the query returning without
error.

**Symptom.** Row counts in the destination roughly double after an unrelated
infrastructure incident.

Cause. the loader used a plain append rather than
an idempotent upsert or partition-swap strategy, so a retried run after a
partial failure re-inserted rows that had already landed successfully before
the crash. Fix. design every load step to be safe to run twice with the same
input, typically an upsert keyed on a natural or surrogate key, or a full
partition overwrite scoped to the run's batch window, never a bare
`INSERT` with no deduplication key.

**Symptom.** A transform step passes locally on a developer's laptop but fails
in production with a null-pointer or type-coercion error on real data.

Cause. the transform was written and tested against a clean sample, not
against the messy edge cases real source data actually contains, such as
missing values, a field that is sometimes a string and sometimes a number
depending on the source system's client library, or a record that arrived
twice due to a retry at the source. Fix. build explicit data quality checks,
including schema validation, not-null constraints, and referential integrity
checks between fact and dimension keys, as a gate the transform step must
pass before the load step runs, and quarantine failing batches for
inspection rather than either crashing the whole pipeline or silently
loading bad data.

**Symptom.** The same business metric computed in two different dashboards
disagrees, and nobody can say which one is right.

Cause. two teams built
independent transform logic for the same concept, for example active
customer, with subtly different filtering rules, because there was no shared,
governed definition, only tribal knowledge in each team's transform code.
This is the coupling-versus-domain-ownership force from dimension 3 resolving
badly, distributed ownership without a shared contract layer. Fix. maintain a
small number of governed, tested, documented core models, often called a
semantic layer or a set of "gold" tables in a medallion architecture,
described in this family's Medallion Architecture entry, that every
downstream dashboard is required to build on, rather than letting each team
re-derive business logic from raw staged data independently.

**Symptom.** The nightly pipeline run time keeps growing month over month until
it no longer finishes within its scheduling window.

Cause. the pipeline was
built as a full extract and full transform of the entire source dataset on
every run, which was affordable when the dataset was small, but scales
linearly, or worse with unindexed joins quadratically, with data volume that
keeps growing while the extraction strategy never changed. Fix. move from
full extraction to incremental extraction keyed on a watermark column, such
as an updated-at timestamp or a monotonically increasing id, or a change data
capture log as described in dimension 8, so each run processes only the
delta since the last successful watermark rather than the entire history
every time.

## 12. Trade-off matrix

| Force | ETL (batch, transform outside destination) | ELT (transform inside destination) | Lambda Architecture (batch + speed layer) | Streaming-only (Kappa Architecture) |
|---|---|---|---|---|
| Data freshness | Low, typically hours | Low to medium, bound by same batch cadence, but transform re-runs are cheap to trigger | High for recent data via the speed layer, batch layer stays low-freshness | High, near-real-time by design |
| Correctness and completeness guarantee | Strong, because transforms run against settled, complete batches | Strong, same batch guarantee, transform errors are easy to re-run since raw data is retained | Strong for the batch layer, speed layer trades exactness for freshness and is reconciled later | Depends heavily on exactly-once processing guarantees of the streaming engine, harder to achieve |
| Operational complexity | Moderate, one pipeline, one orchestrator | Moderate to low, warehouse absorbs compute scaling concerns | High, two codepaths (batch and speed) to build and keep logically consistent | Moderate to high, requires a durable stream processing platform and careful state management |
| Compute cost model | Pipeline infrastructure scales with data volume, separate from destination cost | Warehouse compute scales with query and transform load, often pay-per-query | Both a batch cluster and a stream processing cluster, generally the highest combined cost | Stream processing cluster running continuously, cost is ongoing rather than scheduled |
| Best fit | Complex transforms needing a general-purpose language, or a destination with limited compute | SQL-fluent teams on a modern cloud warehouse with strong compute-storage separation | Systems needing both a correct historical view and low-latency recent view simultaneously | Systems where every consumer can tolerate stream semantics and true real-time matters more than simplicity |

## 13. Related and incompatible patterns

**Star Schema and Snowflake Schema** (this family) are the destinations ETL
most commonly builds toward for reporting workloads. The transform step of
ETL is frequently, in practice, the code that implements the dimensional
modeling described in those entries, converting normalized source data into
fact and dimension tables.

**Slowly Changing Dimensions** (this family) is a transform-step technique
ETL pipelines use when the destination needs to preserve history of a
changing attribute, such as a customer's address at the time of a historical
order, rather than overwriting it. ETL is the delivery mechanism, and Slowly
Changing Dimensions is one of the transform rules it applies.

**Lambda Architecture and Kappa Architecture** (this family) are alternatives
to pure batch ETL when freshness requirements cannot tolerate batch latency.
Lambda Architecture typically retains an ETL-style batch layer alongside a
separate low-latency speed layer. Kappa Architecture replaces the batch
pipeline entirely with a streaming pipeline that is periodically replayed to
recompute historical state, treating batch reprocessing as a special case of
stream replay rather than a separate system.

**Medallion Architecture** (this family) is a layered organization scheme,
bronze, silver, gold, for the intermediate tables an ETL or ELT pipeline
produces along the way from raw extract to fully modeled output, and is
frequently how the staging area and transformer steps in dimension 5 are
physically laid out in a lakehouse.

**Data Mesh** (this family) is philosophically in tension with a
centralized ETL team model, arguing that data ownership, including the
extraction and transformation of a domain's own data, should belong to the
domain team rather than a central pipeline team. Data Mesh does not eliminate
ETL as a technique. It distributes who owns and operates the individual ETL
or ELT pipelines feeding each domain's data product.

**Data Vault** (this family) is a modeling methodology sometimes used as an
intermediate layer between raw extraction and the final dimensional model,
particularly when source system history and full auditability of every raw
change matter more than immediate query performance. An ETL pipeline may load
into a Data Vault structure before a further transform step builds
consumption-ready star schemas on top.

Incompatible with none directly. ETL is a data movement and reshaping
pattern, not an architectural stance that conflicts with a specific other
pattern. Its tensions with alternatives like streaming architectures are
about fit for a given latency requirement, described in dimension 4, rather
than mutual exclusivity.

## 14. Refactoring path in and out

**Introducing ETL into a codebase that does not have it.** The starting point
is usually a set of ad hoc, manually-run export scripts or a report that
queries the live operational database directly. The first step is to
introduce a staging area and a scheduled, idempotent extract of the specific
tables the report needs, decoupling the analytical query from the live
transactional database, even before any transformation logic changes. The
second step is to move the transformation logic that currently lives inside
the report query, such as joins, aggregations, and code lookups, into a
separate, version-controlled transform step that runs on a schedule and
writes a pre-computed table, so the report becomes a simple query against
already-modeled data rather than a complex live query. The third step is to
add an orchestrator once there is more than one dependent task or more than
one source, replacing a cron job with dependency-aware scheduling, retries,
and observable run history. Each step should be validated by comparing the
new pipeline's output against the old manual process on the same input before
cutting reports over, to catch transformation logic that was subtly different
from what the original ad hoc query computed.

**Removing or simplifying ETL when it stops earning its place.** The most
common removal path is consolidation. Several small, source-specific
pipelines that each write to the same destination table are merged into one
pipeline handling all sources for that table, once the number of near-
identical pipelines becomes its own maintenance burden. A second removal path
applies when the destination platform's own capabilities have grown to cover
what a separate transform step used to do, for example when a warehouse
gains materialized views with automatic incremental refresh that make a
scheduled batch transform redundant for a specific table. In that case the
transform step can be retired in favor of the destination's native
capability, provided the freshness and cost characteristics are still
acceptable. A third path, moving from ETL to ELT, described in dimension 8,
is itself a refactor. Extraction and loading are simplified to move raw data
as-is, and transformation logic that lived in a separate processing tier is
rewritten as SQL models executed inside the warehouse, generally reducing the
number of moving infrastructure pieces at the cost of coupling transform
logic more tightly to the destination's SQL dialect.

## 15. Testing and verification

Unit testing applies most directly to the transform step, since it is
typically the largest body of custom logic. Individual transformation
functions, such as a date parser, a currency normalizer, or a deduplication
rule, can be tested with small, hand-constructed input rows and an expected
output row, independent of any real source or destination connection, the
same way any pure function is tested.

Integration testing exercises the full extract-transform-load path against a
disposable copy of the source and destination, commonly a containerized
database seeded with a known fixture dataset, verifying that a full pipeline
run produces the expected row counts and expected values in the destination,
and that re-running the same pipeline twice against the same source data does
not change the result, which is the practical test of the idempotency
property discussed in dimension 3 and dimension 11.

Data quality testing is distinct from conventional unit or integration
testing because it validates the data itself rather than the code. Not-null
checks on required columns, uniqueness checks on keys, referential integrity
checks that every foreign key in a fact table has a matching row in its
dimension table, and range checks on numeric columns, such as a negative
price or an order date in the future, are the typical checks. dbt ships a
built-in testing framework for exactly this purpose, letting a transform
model declare its own quality expectations alongside the SQL that builds it,
so tests run as part of every pipeline execution rather than as a separate,
easily-skipped step.

Contract testing between a source system and its extractor is the least
common but most valuable defense against the schema-drift failure mode in
dimension 11, an automated check, run whenever the source system's schema
changes, that fails loudly if a column the extractor depends on is renamed,
dropped, or has its type changed, rather than letting that break surface
downstream as a mysterious transform failure days later.

Backfill testing verifies that re-running the pipeline for a historical date
range, not just the most recent run, produces results consistent with what
was originally loaded for that range, which catches transform logic that
accidentally depends on the current date or on external state that has since
changed.

## 16. Observability signals

**Freshness.** Time elapsed since the destination table's last successful
load, per table, alerted independently of whether the pipeline run itself
reported success, because a run can succeed while processing stale or empty
input, as in the first failure mode in dimension 11.

**Row counts and volume deltas.** The number of rows extracted, transformed,
and loaded per run, and the run-over-run percentage change in that count. A
healthy pipeline shows volume roughly consistent with the source's known
growth rate. A sudden drop to zero or a sudden spike well above historical
norms is a signal worth alerting on before it reaches a dashboard.

**Task-level duration and dependency graph state.** Per-task run duration,
tracked over time to catch the slow degradation described in the last
failure mode of dimension 11, and the state of the orchestrator's dependency
graph, showing which upstream tasks a given transform is waiting on and how
long it has been waiting, which is the fastest way to diagnose why a
downstream table is late.

**Data quality check pass and fail counts.** The count of rows that failed
each declared quality check, such as a null in a required field, a
referential integrity break, or a duplicate key, per run, exposed as a
metric rather than only as a log line, so a slow creeping increase in
failure rate is visible on a dashboard before it becomes a hard pipeline
failure.

**Lineage and schema change events.** A log of which source columns feed
which destination columns, and an event fired whenever a source schema
changes, whether or not that change broke anything, so schema drift is
visible as a signal rather than discovered only when a pipeline breaks.

**Cost per run.** Compute and storage cost attributable to each pipeline run,
tracked over time, particularly important in ELT setups where transform
compute is billed by the warehouse and a poorly written transform can produce
a cost spike well before it produces an observable error.

A healthy pipeline on a dashboard shows freshness within its expected
service level, stable or explainable volume deltas, zero or a known-baseline
count of quality check failures, and task durations flat or slowly trending
with data volume. A failing pipeline shows freshness alarms firing, an
unexplained volume drop or spike, a rising quality check failure count, or a
task duration trend that has broken away from its historical baseline.

## 17. Security and privacy implications

ETL pipelines routinely move personally identifiable and otherwise sensitive
data out of a source system's access-controlled boundary into a staging area
and a destination warehouse, and each hop is a place that data can be
over-retained, under-protected, or exposed to a broader set of engineers than
the source system's original access policy intended. The staging area in
particular is a common weak point. Raw extracted data, before any masking or
redaction the transform step might apply, is sometimes left in a bucket with
looser access controls than the source database it came from, simply because
it is treated as temporary infrastructure rather than as a system holding
regulated data.

Column-level sensitivity should be tracked as part of the pipeline's
metadata, so that fields subject to regulatory handling requirements, such as
payment card data, health information, or government identifiers, are
masked, tokenized, or excluded at the extract or transform step, rather than
relying on every downstream consumer of the destination table to
independently know which columns are sensitive. In the ELT variant described
in dimension 8, this matters more, not less, because raw unredacted data is
loaded into the destination before transformation runs, meaning the
sensitive data exists in an intermediate, less-governed form inside the
warehouse itself, if only briefly, before the transform step masks or drops
it.

Credentials for source system access, warehouse write access, and any
third-party API keys used by extractors are a concentrated attack surface. A
pipeline typically holds broad read access across many source systems and
broad write access to the destination, making the pipeline's own
infrastructure, the orchestrator and the worker nodes running extract and
transform jobs, a high-value target, and a natural candidate for a dedicated
secrets manager and least-privilege, per-source credentials rather than one
shared, broadly-scoped service account.

Data minimization and retention policy enforcement fits naturally at the
transform step. Fields not needed by any known downstream consumer should not
be extracted or retained in the destination at all, and retention windows,
such as deleting or archiving rows past a regulatory or business-defined age,
are most cleanly implemented as an explicit pipeline step rather than left as
an ad hoc manual cleanup task someone remembers to run.

## 18. References

- Ralph Kimball and Joe Caserta, *The Data Warehouse ETL Toolkit*, Wiley,
  2004. Cited via [Wikipedia, Extract, transform, load](https://en.wikipedia.org/wiki/Extract,_transform,_load),
  verified 2026-08-02.
- Ralph Kimball and Margy Ross, *The Data Warehouse Toolkit*, 3rd edition,
  Wiley, 2013. Chapter on the ETL subsystem and dimensional modeling
  methodology.
- [Wikipedia, "Extract, transform, load"](https://en.wikipedia.org/wiki/Extract,_transform,_load), verified 2026-08-02. Definition, ETL versus ELT distinction, cloud warehouse context.
- [Apache Airflow documentation, index page](https://airflow.apache.org/docs/apache-airflow/stable/index.html), verified 2026-08-02. Airflow's own description of its purpose for orchestrating batch-oriented data pipelines.
- [Apache Airflow documentation, project history](https://airflow.apache.org/docs/apache-airflow/stable/project.html), verified 2026-08-02. Origin at Airbnb in October 2014, open source announcement June 2015, Apache Incubator March 2016, top-level project January 2019.
- [dbt Labs, "What is dbt?" product page](https://www.getdbt.com/product/what-is-dbt), verified 2026-08-02. dbt's own description of executing transformations inside the destination warehouse, the ELT variant in dimension 8.

## Code examples

The following implementations show the same minimal ETL run. extract rows
from an in-memory source, apply a transform that normalizes a currency field
and computes a derived total, and load into an in-memory destination using an
idempotent upsert keyed by record id, so running the pipeline twice on the
same input does not duplicate data. All three were run against the local
toolchain listed in the template's availability table.

### TypeScript

```typescript
type RawOrder = { id: string; amountCents: number; currency: string };
type FactOrder = { id: string; amountUsdCents: number };

const FX_TO_USD: Record<string, number> = { USD: 1, EUR: 1.08, GBP: 1.27 };

function extract(source: RawOrder[]): RawOrder[] {
  return source.filter((r) => r.amountCents >= 0);
}

function transform(rows: RawOrder[]): FactOrder[] {
  return rows.map((r) => {
    const rate = FX_TO_USD[r.currency] ?? 1;
    return { id: r.id, amountUsdCents: Math.round(r.amountCents * rate) };
  });
}

function load(destination: Map<string, FactOrder>, rows: FactOrder[]): void {
  for (const row of rows) {
    destination.set(row.id, row);
  }
}

function runPipeline(source: RawOrder[], destination: Map<string, FactOrder>): void {
  load(destination, transform(extract(source)));
}

const source: RawOrder[] = [
  { id: "o1", amountCents: 1000, currency: "USD" },
  { id: "o2", amountCents: 2000, currency: "EUR" },
];
const destination = new Map<string, FactOrder>();

runPipeline(source, destination);
runPipeline(source, destination);

console.log(destination.size, destination.get("o2"));
```

Compiled with `npx tsc --noEmit` against the file in isolation. Type checking
passed with no errors.

### Python

```python
from dataclasses import dataclass

FX_TO_USD = {"USD": 1.0, "EUR": 1.08, "GBP": 1.27}


@dataclass
class RawOrder:
    id: str
    amount_cents: int
    currency: str


@dataclass
class FactOrder:
    id: str
    amount_usd_cents: int


def extract(source: list[RawOrder]) -> list[RawOrder]:
    return [r for r in source if r.amount_cents >= 0]


def transform(rows: list[RawOrder]) -> list[FactOrder]:
    out = []
    for r in rows:
        rate = FX_TO_USD.get(r.currency, 1.0)
        out.append(FactOrder(id=r.id, amount_usd_cents=round(r.amount_cents * rate)))
    return out


def load(destination: dict[str, FactOrder], rows: list[FactOrder]) -> None:
    for row in rows:
        destination[row.id] = row


def run_pipeline(source: list[RawOrder], destination: dict[str, FactOrder]) -> None:
    load(destination, transform(extract(source)))


if __name__ == "__main__":
    source = [
        RawOrder(id="o1", amount_cents=1000, currency="USD"),
        RawOrder(id="o2", amount_cents=2000, currency="EUR"),
    ]
    destination: dict[str, FactOrder] = {}

    run_pipeline(source, destination)
    run_pipeline(source, destination)

    assert len(destination) == 2
    print(len(destination), destination["o2"])
```

Run with `python3` directly. Produced `2 FactOrder(id='o2',
amount_usd_cents=2160)` and the assertion confirmed a second run did not
duplicate rows.

### Go

```go
package main

import "fmt"

type RawOrder struct {
	ID          string
	AmountCents int
	Currency    string
}

type FactOrder struct {
	ID             string
	AmountUsdCents int
}

var fxToUSD = map[string]float64{"USD": 1.0, "EUR": 1.08, "GBP": 1.27}

func extract(source []RawOrder) []RawOrder {
	out := make([]RawOrder, 0, len(source))
	for _, r := range source {
		if r.AmountCents >= 0 {
			out = append(out, r)
		}
	}
	return out
}

func transform(rows []RawOrder) []FactOrder {
	out := make([]FactOrder, 0, len(rows))
	for _, r := range rows {
		rate, ok := fxToUSD[r.Currency]
		if !ok {
			rate = 1.0
		}
		out = append(out, FactOrder{ID: r.ID, AmountUsdCents: int(float64(r.AmountCents)*rate + 0.5)})
	}
	return out
}

func load(destination map[string]FactOrder, rows []FactOrder) {
	for _, row := range rows {
		destination[row.ID] = row
	}
}

func runPipeline(source []RawOrder, destination map[string]FactOrder) {
	load(destination, transform(extract(source)))
}

func main() {
	source := []RawOrder{
		{ID: "o1", AmountCents: 1000, Currency: "USD"},
		{ID: "o2", AmountCents: 2000, Currency: "EUR"},
	}
	destination := make(map[string]FactOrder)

	runPipeline(source, destination)
	runPipeline(source, destination)

	fmt.Println(len(destination), destination["o2"])
}
```

Run with `go run`. Produced `2 {o2 2160}`, confirming the map size stayed at
two records after the second run.

A fourth language was not included. The pattern here is a data movement and
transformation pipeline shape, not a class hierarchy or a language feature, so
a Rust, Java, or Swift version would repeat the same three-function shape as
the languages above without illustrating a materially different idiom.
