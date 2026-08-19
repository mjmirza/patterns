---
name: ELT
slug: elt
family: 12-data-storage
category: Data and Storage
aliases: [Extract Load Transform, Load then Transform, ELT Pipeline]
first_described: "Term in common use since the early 2010s alongside columnar MPP warehouses, no single named originator"
maturity: established
related: [medallion-architecture, data-vault, star-schema, snowflake-schema, lambda-architecture, kappa-architecture]
incompatible_with: []
verified: 2026-08-02
---

# ELT

## 1. Name, aliases, and lineage

The canonical name is ELT, read as the three letters Extract, Load, Transform, naming the
order in which the three operations run. It is spoken as "E, L, T" the same way its older
sibling ETL is spoken as "E, T, L", not as a pronounceable word.

Unlike Factory Method or Chain of Responsibility, ELT has no single named originator, no
publication year, and no author to cite for its first description. It is an operational
term that data engineering practice converged on once the underlying technology made the
reordering economically sensible, rather than a pattern proposed in a book and then adopted.
Wikipedia's entry on the topic, itself sourced thinly, places ELT as a companion term to
data lake practice, and describes the core distinguishing fact plainly. "the data is not
transformed on entry to the data lake, but stored in its original raw format"
([Wikipedia, "Extract, load, transform"](https://en.wikipedia.org/wiki/Extract,_load,_transform),
verified 2026-08-02). Cloud vendor documentation from the 2020s treats the term as settled
common practice rather than something requiring introduction, which is itself evidence that
ELT crossed from novelty to convention sometime in the mid-2010s as cloud MPP warehouses
(Redshift, BigQuery, Snowflake) matured and made transform-in-place economically ordinary
(Amazon Web Services, ["ETL vs ELT"](https://aws.amazon.com/compare/the-difference-between-etl-and-elt/),
verified 2026-08-02).

ELT is best understood as a reordering of an older idea rather than an unrelated new one.
Ralph Kimball and Margy Ross's *The Data Warehouse Toolkit*, 3rd edition, Wiley, 2013,
chapter 19, describes the traditional ETL back room as staging raw extracts, applying
cleaning and conforming logic in a dedicated ETL tool or hand-written scripts, and only then
loading conformed dimensional models into the warehouse for query. ELT keeps the same three
verbs and the same eventual destination, a queryable model a business analyst runs SQL
against, but moves the transform step to run as SQL, or a SQL-generating tool, inside the
same engine that holds the loaded data, after loading rather than before it.

**ELT** in this entry names the reordered pipeline discipline. Raw data lands first,
unmodified, and every subsequent shaping step is a query or a job that runs against data
already resident in the target system. It is not a single tool, a single vendor product, or
a single file format. It is the operational sequence, and the architectural consequence that
sequence has for staging, compute placement, and schema timing.

## 2. Problem and context

A team needs data from several operational systems, a payments database, a support ticket
system, a marketing platform's API, a stream of application events, made available for
analysis in one place where analysts and downstream services can query it with SQL or feed
it into reporting and machine learning.

The traditional approach transforms the data before it lands. A dedicated ETL server or
service pulls from each source, applies cleaning, joins, deduplication, type coercion, and
business logic in that intermediate layer, using a tool's own processing engine or hand
written code running on its own compute, and only writes the finished, modeled rows into the
warehouse. This requires the intermediate layer to have its own compute capacity sized for
the transform workload, requires every transform to be written and versioned in that tool's
own language or configuration format, and requires the schema of the finished model to be
decided before any data has ever been loaded, because the transform step is the loading step.

Two things changed the economics of this. First, columnar, massively parallel processing
warehouses (Redshift, BigQuery, Snowflake, and their peers) became able to run arbitrarily
large transformation joins and aggregations directly against loaded data at a cost and speed
that made a separate transform server redundant for most workloads. Second, storage on
object stores and in cloud warehouses became cheap enough that landing an entire raw extract,
including columns and rows nobody has a use for yet, stopped being wasteful. Once those two
facts held, it became sensible to load first, in the rawest form the source will give up
without pre-shaping it, and defer every transform decision to a query written and run inside
the warehouse where the compute already lives, using ordinary SQL and version-controlled
SQL tooling rather than the transform tool's own configuration language.

The situation that makes ELT the right choice, rather than merely the fashionable one, has
three parts.

- The target system, a cloud data warehouse or lakehouse, has enough elastic compute to run
  the transform workload itself, so no dedicated transform compute needs to be provisioned,
  sized, or kept warm separately from the storage layer.
- The set of downstream consumers, and the shape they each need, is not fully known at
  extraction time, so pre-committing to one transformed schema at load time would force
  re-extraction whenever a new consumer needs a column that was dropped in the old ETL step.
- The team wants transformation logic written, reviewed, and version-controlled as SQL or a
  SQL-compiling tool, alongside the rest of the analytics codebase, rather than locked inside
  a proprietary ETL tool's visual pipeline editor.

## 3. Forces

The pattern balances forces that pull in the opposite direction from the ones classic ETL
balances, which is why the two remain live alternatives rather than one superseding the
other outright.

- **Compute placement versus compute cost.** Moving transform compute into the warehouse
  removes a whole tier of infrastructure to operate, but it also means every transform run
  competes for the same compute slot as analyst queries, and a runaway transform can degrade
  interactive query latency for everyone sharing that warehouse, unless workload isolation
  (separate virtual warehouses, separate BigQuery reservations) is deliberately configured.
- **Schema timing versus governance.** Deferring schema decisions to transform time gives
  flexibility, a new consumer can be served by writing a new transform against already-loaded
  raw data, without re-extracting from the source. The cost is that "raw" data in the
  warehouse is genuinely raw, meaning inconsistent types, duplicate rows, and unvalidated
  values are queryable by anyone before a transform has cleaned them, which is a governance
  and access-control problem ETL's pre-load cleaning step used to absorb.
- **Reprocessing cost versus extraction cost.** Because the full raw payload is landed once
  and every transform is a query against it, correcting a transformation bug costs a re-run
  of the transform query against data already sitting in the warehouse, not a full re-extract
  from a possibly rate-limited or since-changed source system. This favors ELT heavily for
  sources that are slow, rate-limited, or that mutate their own history.
- **Latency versus resource elasticity.** ELT pipelines commonly separate a fast, dumb load
  step (near-real-time landing of raw rows) from a slower, batched transform step run on a
  schedule, which trades immediate consistency of the modeled tables for the ability to scale
  the transform workload up or down independently of the ingestion rate.
- **Tooling simplicity versus how much source-side logic gets pushed downstream.** ELT favors keeping the extract-and-load
  tooling deliberately dumb, moving essentially no logic into it, which shrinks the surface
  area of a proprietary or hosted extraction tool and pushes essentially all business logic
  into SQL that the team owns. The tradeoff is that any transformation that genuinely needs to
  happen before data reaches the destination, filtering out rows containing regulated data
  that must never land, cannot be deferred, and ELT is the wrong choice for that slice of the
  problem even inside an otherwise ELT-shaped pipeline.

ELT sacrifices pre-load cleanliness and a smaller queryable surface for cheaper compute
placement, faster iteration on transform logic, and resilience to source system fragility.
It does not sacrifice correctness of the final model, correctness is still the job of the
transform step, only the timing and location of where correctness gets enforced.

## 4. Applicability and non-applicability

Reach for ELT when the target system is a modern cloud warehouse or lakehouse with elastic,
metered compute, when the transformation logic is expected to change frequently as new
questions arise, when the team wants transformations expressed and reviewed as SQL alongside
application code, when the source systems are slow, rate-limited, or expensive to re-query,
and when storing the full raw payload has real future value (audit, replay, machine learning
feature discovery) beyond the immediate transformed model.

Do not reach for ELT in these situations.

- **The data contains information that legally or contractually must never be persisted in
  the target system**, personal data subject to a data residency or retention restriction
  the destination cannot honor, secrets, or unredacted payment data. Landing it raw first and
  transforming it away later means it existed, unredacted, in the destination at some point,
  which is precisely the exposure a compliance regime is trying to prevent. Filter or mask
  before load, which is an ETL step, not an ELT one, applied narrowly.
- **The target has no meaningful compute of its own**, a plain object store with no query
  engine attached, a relational database sized only for transactional workloads with no spare
  capacity for analytical joins. Running the transform there either fails outright or degrades
  the workload the system actually exists to serve. ELT needs the T to have somewhere
  economical to run; if the destination cannot be that place, ETL or a separate transform
  compute tier is the correct shape.
- **The extraction itself is the expensive or risky part**, a metered third-party API billed
  per row, or a source database whose query load must be minimized. Loading the full raw
  payload every run, then discarding most of it in the transform, wastes exactly the resource
  that is scarce. Filter and shape at extraction time instead, which again pulls the design
  back toward ETL for that source.
- **Downstream consumers need strict, validated schemas at read time and cannot tolerate a
  raw, unvalidated layer being visible to any query.** A raw ELT landing zone is, by design,
  queryable before it has been cleaned. If every consumer of the warehouse must never see an
  unvalidated row, even behind normal access controls, that invariant has to be enforced
  before load, which is again an ETL-shaped constraint.
- **The transformation is small, fixed, and unlikely to ever need to change**, a simple unit
  or currency conversion applied identically to every record forever. Standing up a full
  load-then-transform pipeline for a single static mapping is unwarranted machinery; a plain
  extraction-time mapping function is simpler and has no governance surface to manage.

## 5. Structure

- **Extractor.** Reads from a source system, an operational database, a SaaS API, an event
  stream, and produces a stream or batch of records in a shape close to the source's own
  representation. Its only responsibility is getting data out; it does not join, aggregate,
  or reshape.
- **Landing zone (raw layer).** The first destination inside the target system, holding data
  in a shape close to what the extractor produced, append-only or replace-on-refresh, with
  minimal or no validation applied. This is the layer ELT is named for, the L happens here,
  before any T.
- **Loader.** The mechanism, a managed connector, a bulk-copy command, a streaming ingest
  API, that moves extracted records into the landing zone. In practice this is frequently
  fused with the extractor into a single tool (Fivetran, Airbyte, a cloud-native ingest
  service), because both steps are intentionally kept dumb and undifferentiated.
- **Transform layer.** SQL, or a tool that compiles to SQL, running inside the target
  system's own compute, reading from the landing zone (and from other already-transformed
  tables) and writing modeled, cleaned, business-logic-applied tables or views. This is where
  joins, deduplication, type coercion, and aggregation happen.
- **Modeled layer (serving layer).** The output of the transform step, the tables and views
  that downstream consumers, dashboards, reports, machine learning feature pipelines,
  actually query. This layer is what ETL's target warehouse would have looked like directly
  after load; in ELT it is one or more transform steps removed from the raw landing zone.
- **Orchestrator.** A scheduler or event trigger (a workflow tool, a cron-driven job, a
  stream processor's checkpoint) that sequences load runs and transform runs so a transform
  never reads a landing table mid-write, and so downstream transforms run only after their
  upstream tables have finished refreshing.

## 6. ASCII structure diagram

```
  SOURCE SYSTEMS                 TARGET SYSTEM (warehouse / lakehouse)
  ---------------                --------------------------------------

  +--------------+   extract    +----------------------------------+
  | payments DB  |------------->|  RAW / LANDING ZONE               |
  +--------------+              |  raw_payments                     |
                                 |  raw_tickets                      |
  +--------------+   extract    |  raw_events                       |
  | ticket API   |------------->|  (append-only, minimal validation)|
  +--------------+              +----------------+-------------------+
                                                  |
  +--------------+   extract                     | transform (SQL, in-warehouse compute)
  | event stream |------------->raw_events        v
  +--------------+              +----------------------------------+
                                 |  MODELED / SERVING LAYER          |
                                 |  fct_orders                       |
                                 |  dim_customers                    |
                                 |  agg_daily_revenue                |
                                 +----------------+-------------------+
                                                  |
                                                  v
                                       dashboards, ML features,
                                       downstream services
```

## 7. Dynamics

```
  ORCHESTRATOR        EXTRACTOR/LOADER        LANDING ZONE        TRANSFORM STEP        MODELED TABLE
       |                     |                     |                     |                    |
       |--trigger load------>|                     |                     |                    |
       |                     |--pull from source-->|                     |                    |
       |                     |<--raw records--------|                     |                    |
       |                     |--write, append/replace->|                  |                    |
       |                     |<--load complete-------|                     |                    |
       |<--load done---------|                     |                     |                    |
       |                                           |                     |                    |
       |--trigger transform (only after load done)-|-------------------->|                    |
       |                                           |<--read raw rows------|                    |
       |                                           |                     |--run SQL model----->|
       |                                           |                     |<--write result------|
       |<--transform done---------------------------|---------------------|                    |
       |                                                                                       |
       |                                                                        consumer queries
       |                                                                       modeled table now
```

The critical ordering constraint the orchestrator enforces is that a transform run must never
start reading a landing table while a load into that same table is still in progress, and a
downstream transform must never run before the upstream table it reads has finished its own
refresh. Most orchestration tools (Airflow, Dagster, dbt's own DAG, a cloud workflow service)
express this as a directed acyclic graph of table dependencies rather than a manually
sequenced script, which is what lets teams add a new transform without hand-editing a
schedule.

## 8. Implementation variants

- **Fused load and transform tool, layered.** A managed extract-and-load service (Fivetran,
  Airbyte, Stitch) handles extraction and landing, and a separate SQL transformation tool
  (dbt, SQLMesh, or hand-written scheduled SQL) owns everything downstream of the landing
  zone. This is the dominant production shape as of 2026, because it lets each half be
  replaced independently and keeps the transform logic as reviewable, version-controlled SQL
  files rather than a proprietary pipeline configuration.
- **Reverse ETL as the fourth step.** Some pipelines add a step after the modeled layer that
  pushes aggregated or modeled data back out to an operational tool, a CRM, an ad platform's
  audience list, a support tool. This is sometimes called ELT-R or "reverse ETL" and is a
  distinct concern from the core three-step pipeline, but it depends on ELT's modeled layer
  being the trustworthy source of truth it reads from.
- **Streaming ELT.** Instead of batch loads on a schedule, records land continuously via a
  streaming ingest path (Kafka into a warehouse's native streaming ingest, or a
  change-data-capture tool), and the transform step runs either on a short interval against
  the continuously growing landing table, or as an incremental materialized view the
  warehouse itself maintains. The load step becomes near-real-time while the transform step
  usually stays batched or micro-batched, because most warehouse SQL engines are not built
  for row-at-a-time transform latency.
- **Medallion / multi-hop layering.** The transform step is itself split into multiple
  named layers, a bronze layer holding raw landed data, a silver layer applying cleaning and
  conforming logic, a gold layer applying business aggregation, each layer a separate
  transform stage inside the same in-warehouse compute. This is documented in this repository
  as its own entry, see `medallion-architecture.md`, and is best understood as ELT with the
  T step deliberately subdivided into named, independently testable stages rather than one
  monolithic transform.
- **Schema-on-read landing with late schema enforcement.** The landing zone stores data in a
  self-describing, schema-flexible format (Parquet, newline-delimited JSON, Avro) without a
  rigid column contract, and the transform step is the first point at which a strict schema
  is imposed, via a SQL cast or a transformation tool's schema test. This variant maximizes
  the flexibility ELT is chosen for, at the cost of pushing all schema drift detection into
  the transform layer's test suite.

## 9. Known production uses

- **dbt (data build tool), used by a large share of modern data teams as the transform layer
  of an ELT pipeline.** dbt's own documentation states its function plainly, "dbt transforms
  raw warehouse data into trusted data products. You write simple SQL select statements, and
  dbt handles the heavy lifting by creating modular, maintainable data models"
  ([dbt Labs, "Introduction to dbt"](https://docs.getdbt.com/docs/introduction), verified
  2026-08-02). dbt does not extract or load anything itself; it assumes the L has already
  happened and operates entirely on the transform step, which is itself evidence of how
  standard the ELT split between load tooling and transform tooling has become.
- **Fivetran, an automated extract-and-load service used across thousands of production data
  stacks, explicitly built to be paired with a separate transform layer.** Fivetran's own
  material describes the division of labor, data moves "from sources into a destination
  system before transformation occurs", and that "Tools like Fivetran make ELT even easier by
  automating the entire process, so you can spend less time on logistics and more on
  strategic data analysis"
  ([Fivetran, "What Is ELT?"](https://www.fivetran.com/blog/what-is-elt), verified
  2026-08-02).
- **Amazon Redshift and AWS Glue, positioned by AWS's own comparison documentation as
  supporting the ELT split, with Redshift performing the in-warehouse transform and Glue
  handling event-driven extraction and loading.** AWS states that Redshift "enables all ELT
  workflows", and describes AWS Glue as providing "event-driven ETL and no-code ETL jobs"
  for the extraction side
  ([AWS, "ETL vs ELT"](https://aws.amazon.com/compare/the-difference-between-etl-and-elt/),
  verified 2026-08-02).
- **Databricks's medallion architecture, an explicit named implementation of ELT inside a
  lakehouse, where transformation happens after loading rather than before.** Databricks
  states the architecture emphasizes ELT rather than ETL, and that "Speed and agility to
  ingest and deliver the data in the data lake is prioritized, and a lot of project-specific
  complex transformations and business rules are applied while loading the data from the
  Silver to Gold layer"
  ([Databricks, "Medallion Architecture"](https://www.databricks.com/glossary/medallion-architecture),
  verified 2026-08-02), which is the transform step of ELT, run inside the lakehouse's own
  compute, applied in named stages.
- **Snowflake, whose separation of storage and compute is the architectural precondition
  most cloud ELT pipelines depend on for the transform step to be affordable and elastic.**
  Snowflake's own documentation states that "Snowflake separates storage and compute, which
  simplifies some traditional challenges of data engineering, such as infrastructure
  management and performance tuning", and that data engineers can concentrate on
  "implementing pipelines that ingest, transform, and deliver data" without managing that
  infrastructure directly
  ([Snowflake, "Key Concepts and Architecture"](https://docs.snowflake.com/en/user-guide/intro-key-concepts),
  verified 2026-08-02).

## 10. Consequences

Positive.

- The transform layer runs on the same elastic compute as the warehouse, so no separate
  transform infrastructure needs to be provisioned, patched, or kept warm.
- Transformation logic can be rewritten, extended, or debugged as SQL against data already
  sitting in the warehouse, without re-extracting from a source system that may be slow,
  rate-limited, or have since mutated its own history.
- A new downstream consumer needing a different shape of the data is served by writing a new
  transform against the existing raw landing tables, not by modifying the extraction step or
  re-pulling from source.
- The raw landing zone functions as an audit trail and a source for reprocessing; a bug found
  in a transform months later can be fixed and rerun against the original raw data still
  sitting in the landing tables, rather than requiring the original source state to be
  reconstructed.
- Extraction and loading tooling stays deliberately simple, which shrinks the surface area of
  code that must run outside the team's normal review and testing tools, and lets it be
  swapped for a different vendor without touching the transform logic.

Negative.

- Raw, unvalidated, potentially inconsistent data is queryable inside the warehouse before
  any cleaning has happened, which is a governance and access-control burden that pre-load
  ETL cleaning used to absorb; strict row-level security or schema access controls have to be
  layered on deliberately.
- The full raw payload from every source is stored, often indefinitely, which increases
  storage volume and cost, and for regulated data can itself be a compliance liability if
  retention limits or right-to-erasure requirements are not separately enforced against the
  landing zone.
- Transform compute competes with interactive analyst query compute in the same warehouse
  unless workload isolation is deliberately configured, so an unbounded or poorly written
  transform job can degrade query latency for everyone else using that warehouse.
- Data that must never be persisted unredacted in the target system, for legal or contractual
  reasons, cannot be handled by the default ELT shape at all; it forces a hybrid where that
  specific slice of the pipeline reverts to filtering or masking at extraction time.
- Because schema enforcement is deferred to transform time, a source system's silent schema
  change (a renamed field, a changed type) surfaces as a broken or silently wrong transform
  downstream, often well after the bad data has already landed, rather than as a load failure
  at the point of ingestion.

## 11. Failure modes and misuse

This dimension is drawn substantially from operational experience rather than a single
citable source; the pattern of failure is common across teams running ELT pipelines, and is
labeled here as engineering judgement.

| Symptom | Cause | Fix |
|---|---|---|
| A modeled table is silently stale, dashboards look normal but numbers stopped updating days ago | The orchestrator's dependency graph does not actually gate the transform on load completion, so the transform ran once against an empty or partial landing table and nothing re-triggers it | Make transform triggers depend on a load-success signal, not a fixed schedule that assumes load already finished; add a freshness check on the landing table's max load timestamp as an explicit assertion before transform runs |
| A single expensive transform query degrades every analyst's dashboard load time during business hours | Transform compute and interactive query compute share one warehouse cluster with no isolation | Split into separate compute clusters or reservations for transform jobs versus interactive queries, so a heavy nightly transform cannot starve daytime dashboard queries |
| The landing zone contains rows with a customer's unredacted payment card number that legal flags months later | A source table was landed wholesale under the default ELT shape without checking whether any column contained regulated data that must never be persisted downstream | Classify source columns before the first load, not after; filter or mask regulated columns at extraction time for that specific source, keeping the rest of the pipeline ELT-shaped |
| A transform silently produces wrong aggregates after a source API renamed a field | Schema enforcement was deferred entirely to the transform layer, and the transform's select statement referenced the old column name, which either errored obscurely inside a cast or, worse, resolved to null and was silently summed as zero | Add a schema test at the top of the transform DAG, asserting the landing table's columns match an expected contract, so a source schema change fails loudly at the first transform step instead of producing quietly wrong numbers three tables downstream |
| Reprocessing a corrected transform takes hours and hammers the source database again | The team built an ETL habit inside an ELT pipeline, re-extracting from source every time a transform bug needed fixing instead of rerunning the transform against already-landed raw data | Confirm the raw landing tables actually retain enough history to rerun the transform without re-extraction; if they do not, the pipeline has quietly lost the main advantage ELT exists to provide |
| Storage costs grow without anyone deciding they should | The raw landing zone accumulates every extract forever with no retention policy, because "just keep the raw data" was treated as free | Set an explicit retention window or tiered storage policy on landing tables, distinct from the modeled layer's retention, and revisit it as a deliberate cost decision rather than a default |

## 12. Trade-off matrix

Compared against named alternatives, across the forces named in dimension 3.

| Force | ELT | Classic ETL (Kimball-style) | Lambda Architecture | Kappa Architecture |
|---|---|---|---|---|
| Where transform compute lives | Inside the target warehouse, shared with query workloads | Dedicated ETL server or tool, separate from the warehouse | Split, batch layer transforms separately from a speed layer that transforms streaming events | A single stream-processing layer, no separate batch transform tier |
| Schema commitment point | Deferred to transform-query time | Committed before load, at extract time | Committed per layer, batch and speed layers can diverge | Committed in the stream processing topology, evaluated continuously |
| Reprocessing cost after a transform bug | Rerun a query against already-landed raw data | Often requires re-extraction from source, since the raw form was never persisted | Rerun the batch layer against retained raw events; the speed layer's already-served results are harder to correct retroactively | Reprocess the event log from an earlier offset, if retention allows |
| Data landed before validation | Yes, by design, the raw layer is unvalidated | No, cleaning happens before the target ever sees the row | Yes for the batch layer's raw store, no for the speed layer's transient state | Yes, the log itself is the raw, replayable record |
| Best fit for regulated data that must never persist unredacted | Poor fit for that specific data; requires a hybrid extraction-time filter | Good fit, cleaning and filtering happen before the target is ever touched | Depends on which layer holds the sensitive field | Poor fit without a separate pre-log filtering step |
| Operational complexity | One warehouse plus a transform tool's DAG | A separate ETL tool or server to operate and scale | Two parallel processing systems to build, run, and reconcile | One streaming system, but one that must handle both real-time and full historical reprocessing |

## 13. Related and incompatible patterns

- **Medallion Architecture** (`medallion-architecture.md`) is a named, layered
  implementation of ELT's transform step, subdividing it into bronze, silver, and gold
  stages rather than leaving it as one monolithic transform. Every medallion pipeline is an
  ELT pipeline; not every ELT pipeline uses medallion's specific three-layer naming.
- **Data Vault** (`data-vault.md`) is a modeling technique for the raw and intermediate
  layers of an ELT pipeline, designed specifically to make the landing and integration layers
  resilient to source schema change, which composes naturally with ELT's deferred-schema
  philosophy; Data Vault's hub, link, and satellite tables are frequently the landing zone an
  ELT transform step reads from.
- **Star Schema and Snowflake Schema** (`star-schema.md`, `snowflake-schema.md`) describe
  the shape of ELT's modeled, serving layer, the output the transform step produces, not the
  pipeline that produces it. An ELT pipeline commonly terminates in a star schema; the two
  patterns operate at different points in the same overall system.
- **Lambda Architecture and Kappa Architecture** (`lambda-architecture.md`,
  `kappa-architecture.md`) address a different axis of the same problem space, how to
  reconcile batch and real-time processing, and are compared directly in the trade-off
  matrix above. A streaming ELT variant and a Kappa Architecture can overlap heavily in
  practice, since both keep a replayable raw log as the source of truth for reprocessing.
- **Incompatible in the narrow sense.** ELT is not compatible, without modification, with a
  hard requirement that no unvalidated or regulated data may ever be queryable inside the
  target system, since ELT's defining move is landing raw data before validation happens.
  That requirement forces a hybrid where the specific regulated slice reverts to an ETL-style
  filter at extraction time, while the rest of the pipeline stays ELT-shaped.

## 14. Refactoring path in and out

**Introducing ELT into an existing ETL pipeline.** Start by identifying the transform steps
in the current ETL tool that are pure SQL-expressible logic, joins, aggregations, type
casts, and are not filtering out data for legal or compliance reasons. For each one, change
the pipeline to load the source's raw extract into a landing table first, unmodified, then
rewrite that transform step as a SQL model reading from the landing table and writing the
same modeled output the ETL step used to produce. Verify the new SQL model's output matches
the old ETL step's output row for row on a snapshot of real data before cutting over.
Migrate one transform at a time rather than the whole pipeline at once, since each migrated
step independently proves whether the target warehouse's compute and the team's SQL tooling
can actually replace that piece of ETL logic. Leave any transform step that filters out data
which must never persist in the target system where it is, at extraction time; do not migrate
that one.

**Removing ELT when it stops earning its place.** The signal that ELT has stopped being the
right shape is usually one of, the landing zone has grown large enough that storage cost or
compliance exposure outweighs the reprocessing flexibility it buys, or a specific source's
data must now be filtered before it ever reaches the target system for a new legal reason.
In either case, move the filtering or minimization logic for that specific source back to
extraction time, converting that one source's path from ELT to ETL, while leaving the rest
of the pipeline's already-loaded, already-modeled tables untouched. A full reversal, moving
every transform back out of the warehouse into a dedicated ETL tool, is rare in practice once
a team has built SQL-based transform tooling and tests around the modeled layer, because that
tooling and those tests are themselves valuable independent of where the transform compute
happens to run.

## 15. Testing and verification

This dimension is largely practice rather than sourced fact, and is labeled as such.

ELT's clean separation between load and transform makes each half independently testable in
a way a monolithic ETL job is not. The load step is tested with row-count assertions, the
number of rows extracted from source matches the number landed, and freshness assertions,
the landing table's most recent timestamp is within an expected window of the current time.
These are cheap, mechanical checks that catch a broken connector or a stalled ingest before
any transform runs against stale or partial data.

The transform step is tested the same way a codebase of SQL views would be tested elsewhere,
with fixture-based unit tests that seed a landing table with known rows and assert the
transform produces the expected modeled rows, schema tests that assert column types and
nullability contracts on both the landing and modeled tables, and referential tests that
assert a foreign key in a modeled fact table always resolves to a row in the corresponding
dimension table. Tools built specifically for the ELT transform layer, dbt among them, ship
this kind of test as a first-class, declarative feature attached directly to the SQL model
it tests, which is one of the reasons the fused load-tool-plus-dbt shape described in
dimension 8 became the default rather than a hand-rolled alternative.

Two things became easier because of ELT. Transform logic is ordinary SQL that can be run, in
isolation, against a small seeded fixture inside the same warehouse the pipeline uses in
production, without needing to stand up the extraction and loading infrastructure at all.
One thing became harder, end-to-end testing of the full pipeline, extract through modeled
output, requires either a full test environment with real or realistic source connections, or
accepting that the load step and the transform step are tested separately and the seam
between them is only verified by the freshness and row-count assertions named above, not by
a single integration test that exercises both halves together.

## 16. Observability signals

This dimension is drawn from operational practice and is labeled as judgement.

At minimum, an ELT pipeline should surface four things. Per-source load duration and row
count on every run, so a sudden drop in extracted rows is visible before it becomes a
stale-dashboard incident; landing table freshness, the elapsed time since the most recent
successful load, alertable when it exceeds the expected refresh interval; per-transform-model
run duration and row counts written, so a transform that used to write a stable number of
rows and suddenly writes zero, or ten times as many, is caught immediately; and DAG-level
lineage, which upstream landing tables and transform models a given transform depends on, so
a failure can be traced to its actual root cause rather than investigated table by table.

A healthy pipeline's dashboard shows a steady, expected pattern, loads completing on
schedule with row counts in a normal range, transforms running immediately after their
upstream dependencies finish, and end-to-end latency from source event to modeled table
staying within an agreed service-level target. A failing pipeline shows the opposite
pattern early, a load that ran but landed zero or a fraction of the usual rows, a transform
that ran on a stale upstream table because the dependency check was missing or misconfigured,
or a modeled table's row count drifting from its historical baseline with no corresponding
change on the source side. The most useful single signal for catching problems before a
human notices a wrong number on a dashboard is a row-count or distributional anomaly check
comparing each run's output against a rolling baseline of recent runs, attached directly to
the transform step rather than discovered downstream by whoever consumes the dashboard.

## 17. Security and privacy implications

ELT's central architectural choice, landing raw data before any validation or filtering,
is itself the security-relevant fact about the pattern, and it is not silent.

Any data present in a source system is, by default, also present inside the target
warehouse's landing zone once an ELT pipeline runs against that source, unmodified and
unredacted. This means the landing zone's access controls, encryption at rest, row and
column level security, and audit logging must be at least as strict as the strictest source
system feeding it, because the landing zone is now a second copy of that source's most
sensitive fields, sitting in a system whose primary users are analysts and transform jobs
rather than the source system's own access-controlled application layer. A warehouse
permission model that grants broad read access to raw schemas for debugging convenience is
a common and serious misconfiguration in ELT shops specifically because of this.

Data residency and retention requirements attach to the landing zone independently of the
modeled layer. A regulation that requires personal data to be deleted within a defined window
after a user's request, or that requires certain data to never leave a specific geographic
region, applies to every copy of that data, including the raw landing tables that ELT
deliberately keeps around for reprocessing. A pipeline that only implements deletion or
residency controls against the modeled, cleaned tables while leaving the raw landing zone
untouched has not actually satisfied the requirement, it has only hidden the violation one
layer down.

Finally, because ELT defers transformation, any masking, tokenization, or redaction of
sensitive fields that a compliance regime requires happens later, or not at all, than it
would under classic ETL's pre-load cleaning step. For fields that must genuinely never be
persisted unredacted in the target system at all, ELT's default shape is the wrong choice for
that specific data, as stated in dimension 4, and the correct answer is a narrow,
deliberate exception where that field is filtered or masked at extraction time, before it
ever reaches the landing zone.

## 18. References

- Wikipedia, ["Extract, load, transform"](https://en.wikipedia.org/wiki/Extract,_load,_transform),
  verified 2026-08-02. Used for the definitional claim that ELT stores data unmodified on
  entry, as an alternative to ETL used with data lake implementations.
- Amazon Web Services, ["ETL vs ELT, The Difference Between Data-Processing Approaches"](https://aws.amazon.com/compare/the-difference-between-etl-and-elt/),
  verified 2026-08-02. Used for the ordering distinction between ETL and ELT, the named role
  of Amazon Redshift and AWS Glue, and the guidance on when to choose each approach.
- dbt Labs, ["Introduction to dbt"](https://docs.getdbt.com/docs/introduction), verified
  2026-08-02. Used for the description of dbt's role as an in-warehouse transform tool
  operating on data already loaded, and for dimension 9's named production use.
- Fivetran, ["What Is ELT? (Extract, Load, Transform)"](https://www.fivetran.com/blog/what-is-elt),
  verified 2026-08-02. Used for the description of ELT's three-step process and Fivetran's
  role as an automated extract-and-load tool paired with a separate transform layer.
- Databricks, ["What is Medallion Architecture?"](https://www.databricks.com/glossary/medallion-architecture),
  verified 2026-08-02. Used for the description of the bronze, silver, gold layering as an
  explicit ELT implementation, and for the cross-reference to this repository's
  `medallion-architecture.md` entry.
- Snowflake, ["Key Concepts and Architecture"](https://docs.snowflake.com/en/user-guide/intro-key-concepts),
  verified 2026-08-02. Used for the claim that separating storage and compute is the
  architectural precondition that makes in-warehouse transform compute economical.
- Ralph Kimball and Margy Ross, *The Data Warehouse Toolkit*, 3rd edition, Wiley, 2013,
  chapter 19, "ETL Subsystems and Techniques". Used for the description of the traditional
  ETL back room's staging and conforming discipline, as the baseline ELT reorders.

## Code examples

Three languages are shown, Python, TypeScript, and Go. All three were compiled or run
directly and produce the printed output shown after each block. Java, Rust, Swift, C#, and
Kotlin are omitted, not because the pattern does not translate, ELT is a data flow shape
rather than a language feature, but because the pattern's essential content is the staged
pipeline structure, which three languages demonstrate without repetition adding new
information.

Each example follows the same shape, an `extract` step producing raw records, a `load` step
landing those records unmodified into a raw table, and a `transform` step running a query or
query-equivalent against the already-landed raw table to produce a modeled result, mirroring
dimensions 5 through 7 above.

### Python

Uses the standard library's `sqlite3` module as a stand-in for a warehouse, so the load step
is a real `insert` and the transform step is a real `create table as select`, run against
data that is genuinely already resident in the target rather than held in application memory.

```python
import sqlite3
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class RawOrderEvent:
    order_id: str
    customer_id: str
    amount_cents: int
    currency: str
    created_at: str


def extract() -> Iterable[RawOrderEvent]:
    source = [
        {"order_id": "o1", "customer_id": "c1", "amount_cents": 1999,
         "currency": "USD", "created_at": "2026-08-01T10:00:00Z"},
        {"order_id": "o2", "customer_id": "c1", "amount_cents": 500,
         "currency": "USD", "created_at": "2026-08-02T11:30:00Z"},
        {"order_id": "o3", "customer_id": "c2", "amount_cents": 4200,
         "currency": "EUR", "created_at": "2026-08-02T12:15:00Z"},
    ]
    for row in source:
        yield RawOrderEvent(**row)


def load(conn: sqlite3.Connection, events: Iterable[RawOrderEvent]) -> int:
    conn.execute(
        "create table if not exists raw_orders "
        "(order_id text, customer_id text, amount_cents integer, "
        "currency text, created_at text)"
    )
    rows = [(e.order_id, e.customer_id, e.amount_cents, e.currency, e.created_at)
            for e in events]
    conn.executemany("insert into raw_orders values (?, ?, ?, ?, ?)", rows)
    conn.commit()
    return len(rows)


def transform(conn: sqlite3.Connection) -> None:
    conn.execute("drop table if exists customer_revenue")
    conn.execute(
        "create table customer_revenue as "
        "select customer_id, count(*) as order_count, "
        "sum(amount_cents) as revenue_cents "
        "from raw_orders where currency = 'USD' "
        "group by customer_id"
    )
    conn.commit()


def main() -> None:
    conn = sqlite3.connect(":memory:")
    loaded = load(conn, extract())
    assert loaded == 3
    transform(conn)
    result = conn.execute(
        "select customer_id, order_count, revenue_cents "
        "from customer_revenue order by customer_id"
    ).fetchall()
    assert result == [("c1", 2, 2499)]
    print("loaded", loaded, "rows; modeled", result)


if __name__ == "__main__":
    main()
```

Run with `python3 elt.py`. Verified output, `loaded 3 rows; modeled [('c1', 2, 2499)]`,
confirming the load step landed all three raw rows and the transform, run entirely as SQL
against those already-landed rows, correctly grouped and filtered to produce one modeled
row for customer `c1`.

### TypeScript

Models the landing zone as an explicit `Loader` interface backed by an in-memory table map,
so the load step and the transform step are visibly separate operations with distinct
responsibilities, matching the participant list in dimension 5.

```typescript
interface RawEvent {
  orderId: string;
  customerId: string;
  amountCents: number;
  currency: string;
}

interface Loader {
  land(table: string, rows: RawEvent[]): void;
  read(table: string): RawEvent[];
}

class InMemoryWarehouse implements Loader {
  private tables = new Map<string, RawEvent[]>();

  land(table: string, rows: RawEvent[]): void {
    const existing = this.tables.get(table) ?? [];
    this.tables.set(table, existing.concat(rows));
  }

  read(table: string): RawEvent[] {
    return this.tables.get(table) ?? [];
  }
}

function extract(): RawEvent[] {
  return [
    { orderId: "o1", customerId: "c1", amountCents: 1999, currency: "USD" },
    { orderId: "o2", customerId: "c1", amountCents: 500, currency: "USD" },
    { orderId: "o3", customerId: "c2", amountCents: 4200, currency: "EUR" },
  ];
}

interface CustomerRevenue {
  customerId: string;
  orderCount: number;
  revenueCents: number;
}

function transform(raw: RawEvent[]): CustomerRevenue[] {
  const byCustomer = new Map<string, CustomerRevenue>();
  for (const row of raw) {
    if (row.currency !== "USD") continue;
    const acc = byCustomer.get(row.customerId) ?? {
      customerId: row.customerId,
      orderCount: 0,
      revenueCents: 0,
    };
    acc.orderCount += 1;
    acc.revenueCents += row.amountCents;
    byCustomer.set(row.customerId, acc);
  }
  return Array.from(byCustomer.values());
}

function run(): void {
  const warehouse = new InMemoryWarehouse();
  warehouse.land("raw_orders", extract());
  const modeled = transform(warehouse.read("raw_orders"));
  const c1 = modeled.find((r) => r.customerId === "c1");
  if (!c1 || c1.orderCount !== 2 || c1.revenueCents !== 2499) {
    throw new Error("transform mismatch");
  }
  console.log("landed", warehouse.read("raw_orders").length, "rows; modeled", modeled);
}

run();
```

Compiled with `npx tsc --strict --target es2020 --module commonjs elt.ts` and run with
`node elt.js`. Verified output, `landed 3 rows; modeled [ { customerId: 'c1', orderCount: 2,
revenueCents: 2499 } ]`, showing the same load-then-transform result as the Python example,
with the loader's `land` and `read` calls making the two pipeline stages explicit rather than
implicit in a single function.

### Go

Uses a plain in-memory map as the warehouse's table store, avoiding an external database
dependency while keeping load and transform as two distinct, separately callable functions
operating on the same warehouse value.

```go
package main

import "fmt"

type RawEvent struct {
	OrderID     string
	CustomerID  string
	AmountCents int
	Currency    string
}

type Warehouse struct {
	tables map[string][]RawEvent
}

func NewWarehouse() *Warehouse {
	return &Warehouse{tables: make(map[string][]RawEvent)}
}

func (w *Warehouse) Land(table string, rows []RawEvent) {
	w.tables[table] = append(w.tables[table], rows...)
}

func (w *Warehouse) Read(table string) []RawEvent {
	return w.tables[table]
}

func extract() []RawEvent {
	return []RawEvent{
		{"o1", "c1", 1999, "USD"},
		{"o2", "c1", 500, "USD"},
		{"o3", "c2", 4200, "EUR"},
	}
}

type CustomerRevenue struct {
	CustomerID   string
	OrderCount   int
	RevenueCents int
}

func transform(raw []RawEvent) []CustomerRevenue {
	byCustomer := make(map[string]*CustomerRevenue)
	order := make([]string, 0)
	for _, row := range raw {
		if row.Currency != "USD" {
			continue
		}
		acc, ok := byCustomer[row.CustomerID]
		if !ok {
			acc = &CustomerRevenue{CustomerID: row.CustomerID}
			byCustomer[row.CustomerID] = acc
			order = append(order, row.CustomerID)
		}
		acc.OrderCount++
		acc.RevenueCents += row.AmountCents
	}
	result := make([]CustomerRevenue, 0, len(order))
	for _, id := range order {
		result = append(result, *byCustomer[id])
	}
	return result
}

func main() {
	warehouse := NewWarehouse()
	warehouse.Land("raw_orders", extract())
	modeled := transform(warehouse.Read("raw_orders"))
	if len(modeled) != 1 || modeled[0].OrderCount != 2 || modeled[0].RevenueCents != 2499 {
		panic("transform mismatch")
	}
	fmt.Printf("landed %d rows; modeled %+v\n", len(warehouse.Read("raw_orders")), modeled)
}
```

Run with `go run elt.go`. Verified output, `landed 3 rows; modeled [{CustomerID:c1
OrderCount:2 RevenueCents:2499}]`, matching the Python and TypeScript results and confirming
the same load-then-transform sequence holds regardless of which language expresses it.
