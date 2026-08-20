---
name: Slowly Changing Dimensions
slug: slowly-changing-dimensions
family: 12-data-storage
category: Data and Storage
aliases: [SCD, SCD Type 2, Dimension Versioning, Historical Dimension Tracking]
first_described: "Ralph Kimball, The Data Warehouse Toolkit, 1996, expanded through Kimball Group Design Tips 1998 to 2013"
maturity: canonical
related: [data-vault, event-sourcing, temporal-tables, cqrs, medallion-architecture, change-data-capture]
incompatible_with: []
verified: 2026-08-02
---

# Slowly Changing Dimensions

## 1. Name, aliases, and lineage

The canonical name is Slowly Changing Dimensions, almost always shortened to
SCD in conversation and in code, as in "this is a Type 2 SCD" or "we snapshot
that table with SCD2 semantics." The name describes a fact about dimension
tables in a dimensional data warehouse rather than a single technique. a
customer's address, a product's category, an employee's manager, all of these
attributes are mostly stable but occasionally change, and a customer moving
house or a product being recategorized is a slow, low-frequency event compared
to the fact table rows that reference that customer or product thousands of
times a day. The pattern is a family of numbered techniques, Type 0 through
Type 7, each answering the same question differently. when a dimension
attribute changes, what happens to the historical fact rows that were
recorded when the old value was true.

Ralph Kimball introduced the foundational Type 1, Type 2, and Type 3
techniques in his 1996 book with Laura Reeves, Warren Thornthwaite, and
Margy Ross, and refined the vocabulary across the Kimball Group's published
Design Tips through the 2000s and 2010s. The third edition of Kimball and
Ross's book, The Data Warehouse Toolkit (subtitled The Definitive Guide to
Dimensional Modeling), published in 2013, consolidated all seven numbered
types (0 through 7) into one chapter, Chapter 2, in the section "Dealing
with Slowly Changing Dimension Attributes" (Ralph Kimball and Margy Ross,
The Data Warehouse Toolkit, 3rd edition, Wiley, 2013, Chapter 2, verified
2026-08-02 via the publisher's table of contents at
[Wiley](https://www.wiley.com/en-us/The+Data+Warehouse+Toolkit:+The+Definitive+Guide+to+Dimensional+Modeling,+3rd+Edition-p-9781118530801)).
The original Type 1 through Type 3 vocabulary appeared earlier, in a
dedicated Kimball Group article that Ralph Kimball himself authored and
that the Kimball Group republished with a 2008-09-22 date stamp, describing
Type 1 as overwriting the changed value, Type 2 as adding a new dimension
row with surrogate keys and administrative date and flag columns, and Type
3 as adding an alternate column to hold a second, simultaneously valid
interpretation of the attribute (Ralph Kimball, "Slowly Changing
Dimensions," Kimball Group, published 2008-09-22, verified 2026-08-02,
[kimballgroup.com/2008/09/slowly-changing-dimensions](https://www.kimballgroup.com/2008/09/slowly-changing-dimensions/)).

The later types, 0, 4, 5, 6, and 7, were formalized in a single Kimball
Group design tip authored by Margy Ross and published 2013-02-05. Type 0
retains the original value forever and never changes it, appropriate for a
durable identifier such as an original credit score or a date of birth.
Type 4 splits a volatile, frequently-queried attribute into a separate
mini-dimension table so the base dimension stays narrow. Type 5 adds a
Type 1 reference to the current mini-dimension row inside the base
dimension, so a query against current attributes never has to join the
fact table to the mini-dimension. Type 6 merges Type 1, Type 2, and Type 3
in a single dimension row, tracking history in new rows the Type 2 way
while also keeping a current-value column that is overwritten across every
historical row for that entity the Type 1 way. Type 7 achieves the same
dual current-or-historical query capability as Type 6 without ever
overwriting a historical attribute, by carrying two separate foreign keys
in the fact table, one pointing at the Type 2 historical row and one
pointing at the durable natural key or a dedicated "current row" surrogate
key (Margy Ross, "Design Tip #152, Slowly Changing Dimension Types 0, 4,
5, 6 and 7," Kimball Group, published 2013-02-05, verified 2026-08-02,
[kimballgroup.com/2013/02/design-tip-152](https://www.kimballgroup.com/2013/02/design-tip-152-slowly-changing-dimension-types-0-4-5-6-7/)).

One further naming detail is worth being precise about because it is
widely repeated with varying confidence. secondary sources report that the
name "Type 6" itself, rather than the underlying technique, was coined
informally by Ralph Kimball in a conversation with Stephen Pace of the
vendor Kalido, as a pun on the arithmetic 1 + 2 + 3 = 6, and that Kimball's
own published name for the technique in The Data Warehouse Toolkit is the
more descriptive "Unpredictable Changes with Single-Version Overlay." This
naming anecdote is treated as unverified oral history rather than a sourced
fact, and is included here only as color, not as a claim to rely on.

## 2. Problem and context

A dimensional data warehouse separates numeric, frequently-recorded facts
(an order line, a sensor reading, a page view) from the descriptive
dimensions those facts are analyzed by (a customer, a product, a store, a
salesperson). Facts are typically append-only and effectively immutable once
recorded. dimensions are not. A customer's mailing address changes when they
move. A product's category changes when the merchandising team reorganizes
the catalog. An employee's manager changes on every promotion or
reorganization. A store's region changes when franchise territories are
redrawn. None of these changes happen often for any single row, hence
"slowly", but across a dimension with millions of rows some fraction of the
table is always in the middle of changing, and the changes never stop
happening across the life of the warehouse.

The problem this pattern exists to solve is what happens to the fact rows
that were recorded under the old value once the dimension attribute
changes. If the warehouse simply updates the dimension row in place, every
historical fact that joins to that dimension row is silently reinterpreted
under the new value, which corrupts historical reporting. A sales report
for the fiscal quarter three years ago, when a particular product still sat
in the "Electronics" category before a reorganization moved it to
"Home Appliances", would retroactively show that quarter's electronics
revenue as smaller than it actually was, purely because the report re-runs
today against today's dimension state. The context in which this problem
arises is specifically the star schema and snowflake schema modeling
approach where dimension tables are joined to fact tables by a foreign key,
because the join is what silently reinterprets history. an operational
system that simply stores the current address on the customer row, with no
notion of historical fact rows joining against it, does not have this
problem in the same way, because it has no facts recorded against a
point-in-time version of that address in the first place.

## 3. Forces

**Historical accuracy versus storage and query cost.** Preserving every
past version of every dimension attribute (the Type 2 answer) is the most
accurate approach for historical reporting, but it multiplies the row count
of the dimension, which multiplies index size, join cost, and the surface
area a query has to filter correctly to avoid double-counting an entity
that now has several historical rows.

**Query simplicity versus query power.** Type 1 (overwrite) keeps every
dimension query trivially simple, one row per entity, no effective-date
filtering, no "as of" logic to get wrong. Type 2 buys the ability to answer
"as of" questions and reproduce historical reports exactly, at the cost of
every analyst and every BI tool query needing to reason correctly about
which row is current and which date range a fact belongs to.

**Write-path complexity versus read-path complexity.** Type 2 pushes
complexity into the write path, the ETL or ELT job that has to detect a
change, close out the old row's validity window, and insert a new row with
a fresh surrogate key, ideally inside one transaction so a partial write
never leaves two rows simultaneously marked current. Type 1 pushes almost
no complexity into either path. Type 6 and Type 7 push complexity into both
paths at once, because they need Type 2's write-side row versioning and
still need read-side logic to pick between the historical and current
columns depending on what the query is asking.

**Fidelity to the source system versus independence from it.** A
timestamp-based change-detection strategy trusts the source system's own
"updated at" column, which is cheap to compute but only as reliable as
that column, and misses changes the source system does not stamp. A
column-comparison strategy is independent of the source's own bookkeeping
but is more expensive to compute and brittle when the source's schema
changes underneath it, because a newly-added or dropped column silently
changes what "changed" means.

**Reversibility of the decision.** Choosing Type 1 for an attribute is
close to irreversible in the sense that once history has been overwritten,
there is no way to reconstruct it from the warehouse alone, only from
upstream source-system audit logs if those exist and were retained.
Choosing Type 2 is comparatively reversible, a Type 2 dimension can always
be collapsed down to a Type 1 view later by taking only the current row per
entity, but a Type 1 dimension can never be un-collapsed into Type 2 after
the fact.

## 4. Applicability and non-applicability

Reach for Slowly Changing Dimensions, and specifically for Type 2, when:

- Historical fact rows must remain accurate under the dimension attribute
  values that were true at the time the fact was recorded, and a
  regulator, an auditor, or a finance team will re-run a report from a
  past period and expect the same numbers every time.
- The business genuinely asks "as of" questions. what was this customer's
  segment when they placed this order, what was this employee's manager
  when this expense was approved, what territory was this store assigned
  to on this date.
- The dimension attribute changes with low but nonzero frequency relative
  to the fact volume, so the extra dimension rows Type 2 produces stay a
  small fraction of total warehouse storage.
- Data lineage or compliance requirements (financial audit trails, clinical
  trial data, insurance underwriting history) require a durable, queryable
  record of what an attribute's value was at every point in time, not just
  the current value.

Do NOT reach for full Type 2 tracking when:

- The attribute genuinely never changes for the life of the entity, such as
  a date of birth or an original signup channel. Type 0 (retain original)
  is simpler and correct, and applying Type 2 machinery to an attribute
  that never changes is pure overhead with zero benefit.
- Nobody in the business has ever asked, and nobody plans to ask, an "as
  of" historical question about this specific attribute. If every report
  that touches the attribute only ever wants the current value, Type 1 is
  correct, and adding Type 2's effective-dating machinery is solving a
  problem the business does not have.
- The attribute changes at high frequency relative to how often it is
  actually queried historically, for example a "last login timestamp" or a
  frequently-recomputed derived score. these are usually better modeled as
  facts, or as a Type 4 mini-dimension, than as a Type 2 attribute on the
  base dimension, because versioning them the Type 2 way would balloon row
  count for a value nobody reconstructs historically anyway.
- The system is operational rather than analytical, meaning the primary
  read pattern is "give me this customer's current record for a
  transaction I am processing right now," not "give me a historical
  report." An OLTP system with this need is usually better served by
  bitemporal or event-sourced modeling at the application layer (see the
  Related patterns dimension) than by importing dimensional-warehouse SCD
  vocabulary into a service's primary datastore.
- The team lacks the operational discipline to run the change-detection job
  reliably on every load. A partially-run Type 2 process, where some
  changes get versioned and others silently overwrite, is worse than a
  consistently-applied Type 1, because it produces data that looks
  historically accurate but is not, and nobody can tell which rows to
  trust.

## 5. Structure

The participants below describe a Type 2 dimension, the most structurally
rich of the seven types and the one every other numbered type is a
variation or simplification of.

**Natural key.** The identifier the source system uses for the entity, for
example a customer ID from a CRM or an employee ID from an HR system. Many
rows in the Type 2 dimension table share the same natural key, one per
historical version.

**Surrogate key.** A warehouse-generated identifier, usually an integer or
a hash, unique to each individual row (each version) in the dimension
table. This, never the natural key, is what fact tables carry as their
foreign key, precisely so a fact row can point at the specific historical
version of the dimension that was true when the fact occurred.

**Type 2 attributes.** The columns that are tracked historically. a
customer's segment, a product's category, an employee's manager. Each
change to one of these produces a new dimension row.

**Type 1 attributes (when present).** Columns on the same dimension row
that are simply overwritten in place regardless of history, for example a
customer's phone number, when the business has decided that attribute does
not need historical tracking even though it lives on the same physical
table as attributes that do.

**Effective date range (`effective_from`, `effective_to`).** Two date or
timestamp columns bounding the period during which this particular version
of the row was the current, correct version.

**Current-row flag.** A boolean column, commonly named `is_current`, that
makes "give me the current version of every entity" a simple filter instead
of a subquery finding the maximum effective date per natural key. This
column is redundant with the effective date range in principle, `is_current`
is true exactly when `effective_to` is null or a sentinel far-future date,
but it is kept because it is cheaper to index and query directly.

**Change-detection mechanism.** The upstream process, whether a
timestamp-comparison, a full row hash comparison, or a change-data-capture
stream, that decides whether an incoming source row represents a genuine
change to a tracked attribute, and therefore whether a new dimension row is
required.

**Mini-dimension (Type 4 and Type 5 only).** A separate, narrower
dimension table holding only the volatile, frequently-changing attributes,
joined to the fact table (Type 4) or referenced by a Type 1 pointer from
the base dimension (Type 5), so the base dimension does not balloon in row
count from attributes that change far more often than the rest of the
entity's data.

## 6. ASCII structure diagram

```
                     +--------------------------------------------+
                     |         DIM_CUSTOMER  (Type 2 dimension)   |
                     +--------------------------------------------+
                     | customer_sk (PK, surrogate key)             |
                     | customer_id (natural key, from source)      |
                     | name                                        |  <- Type 1 (overwritten)
                     | segment                                     |  <- Type 2 (versioned)
                     | region                                      |  <- Type 2 (versioned)
                     | effective_from                              |
                     | effective_to                                |
                     | is_current                                  |
                     +--------------------------------------------+

  natural key 1042 has three physical rows over time.

  sk=501  customer_id=1042  segment=Bronze  eff[2023-01-01, 2024-03-14)  is_current=false
  sk=734  customer_id=1042  segment=Silver  eff[2024-03-14, 2025-09-02)  is_current=false
  sk=910  customer_id=1042  segment=Gold    eff[2025-09-02, 9999-12-31] is_current=true

                     +--------------------------------------------+
                     |              FACT_ORDER                    |
                     +--------------------------------------------+
                     | order_id                                    |
                     | order_date                                  |
                     | customer_sk (FK -> DIM_CUSTOMER.customer_sk) |---> points at sk=501 or 734
                     | amount                                      |     depending on WHEN the
                     +--------------------------------------------+     order happened, never
                                                                         at the natural key alone
```

## 7. Dynamics

```
  incoming source row for natural key K, attribute values (a', b')
             |
             v
  +---------------------------+
  | look up CURRENT dim row   |
  | for natural key K         |
  | (WHERE is_current = true) |
  +---------------------------+
             |
       found a current row? --- no ---> INSERT new row
             |                            surrogate key = new
            yes                           effective_from = load date
             |                            effective_to   = far future
             v                            is_current = true
  +---------------------------------+
  | compare tracked (Type 2)        |
  | attributes. a == a' and b == b' |
  +---------------------------------+
             |
        equal? ---- yes ----> no change. optionally UPDATE
             |                any Type 1 columns in place,
             no                leave the row's version alone.
             |
             v
  +--------------------------------------------+
  | BEGIN TRANSACTION                           |
  |  UPDATE current row.                        |
  |     effective_to = load date                |
  |     is_current = false                      |
  |  INSERT new row.                            |
  |     surrogate key = new                     |
  |     natural key = K, attrs = (a', b')        |
  |     effective_from = load date               |
  |     effective_to = far future                |
  |     is_current = true                        |
  | COMMIT                                       |
  +--------------------------------------------+
             |
             v
  new fact rows loaded AFTER this point join
  to the NEW surrogate key. fact rows loaded
  BEFORE this point still point at the OLD
  surrogate key and are never rewritten.
```

The transaction boundary in the middle of this flow is the detail most
implementations get wrong under concurrency, discussed further in
dimensions 11 and 15. closing the old row and opening the new row must be
atomic, or a reader querying at exactly the wrong moment sees either zero
current rows or two current rows for the same natural key.

## 8. Implementation variants

**Hand-written SQL MERGE / UPSERT with explicit versioning logic.** The
classic approach. a stored procedure or a scheduled SQL script runs the
compare-and-branch logic from dimension 7 directly, usually as a single
`MERGE` statement (SQL Server, Oracle, Snowflake, BigQuery) or an
equivalent multi-statement transaction (PostgreSQL, MySQL, which lack a
standard `MERGE`). This is the lowest-abstraction variant, fully
transparent, and the one every other variant below is compiling down to.

**ETL/ELT tool built-in SCD components.** Commercial and open-source data
integration tools ship a purpose-built "Slowly Changing Dimension" or
"History" transformation that implements the compare-and-branch logic
behind a configuration surface rather than hand-written SQL. Informatica
PowerCenter's SCD wizard and Microsoft SQL Server Integration Services'
Slowly Changing Dimension transformation are long-standing examples of this
variant, and both explicitly support configuring individual columns as
Type 1 (overwrite) or Type 2 (historical) within the same wizard, matching
the mixed-attribute structure described in dimension 5.

**Analytics-engineering framework snapshots.** dbt implements Type 2
tracking as a first-class object type, a "snapshot," configured
declaratively in YAML rather than written as procedural SQL. dbt computes
whether a row has changed using one of two pluggable strategies, a
`timestamp` strategy that trusts a source `updated_at` column, or a `check`
strategy that compares a named list of columns row by row when no reliable
timestamp exists, and on every run it automatically manages the
`dbt_valid_from`, `dbt_valid_to`, and `dbt_scd_id` administrative columns
that correspond to this pattern's effective-date range and surrogate key
(dbt Labs, "Add snapshots to your DAG," dbt Docs, verified 2026-08-02,
[docs.getdbt.com/docs/build/snapshots](https://docs.getdbt.com/docs/build/snapshots)).

**Change-data-capture-driven pipelines.** Instead of comparing a full
current source extract against the warehouse's current dimension row (a
snapshot comparison), a CDC-driven variant subscribes to the source
database's own change stream (a Debezium connector reading a database's
write-ahead log, or a warehouse-native mechanism such as a Snowflake
stream, which records row-level insert, update, and delete events as an
`INSERT`/`DELETE` pair per change) and applies each change event as it
arrives rather than batch-comparing entire tables (Snowflake
Documentation, "Introduction to streams," verified 2026-08-02,
[docs.snowflake.com/en/user-guide/streams-intro](https://docs.snowflake.com/en/user-guide/streams-intro)).
This variant trades batch-window latency for near-real-time dimension
freshness, at the cost of needing the source system to expose a reliable
change stream in the first place.

**Managed ingestion tool history modes.** Fivetran's History Mode is a
sync-level toggle rather than a downstream transformation. it inserts a new
destination row on every source-side insert, update, or delete rather than
overwriting the destination row in place, and adds three system columns,
`_fivetran_start`, `_fivetran_end`, and `_fivetran_active`, whose roles map
directly onto this pattern's effective-date range and current-row flag
(Fivetran, "History mode," Fivetran Documentation, verified 2026-08-02,
[fivetran.com/docs/core-concepts/sync-modes/history-mode](https://fivetran.com/docs/core-concepts/sync-modes/history-mode)).

**Native pipeline SCD support in lakehouse platforms.** Databricks
Lakeflow declarative pipelines expose an `AUTO CDC ... INTO` construct with
native, documented support for applying both Type 1 and Type 2 semantics
directly from a change feed into a Delta table, without the pipeline author
hand-writing the branch-and-version logic from dimension 7 (Databricks
Documentation, "Use MERGE INTO," verified 2026-08-02,
[docs.databricks.com/aws/en/delta/merge](https://docs.databricks.com/aws/en/delta/merge)).

**Language-idiomatic in-memory variant.** Outside of a warehouse entirely, a
small service or a data pipeline written in a general-purpose language can
implement the same versioning discipline against an in-memory or key-value
store, appending a new immutable version record per entity rather than
mutating a single current record. This is structurally identical to Type 2,
only the storage engine is not a SQL warehouse table, and it is the variant
demonstrated in the code examples for this entry.

## 9. Known production uses

1. **dbt Labs, dbt snapshots.** dbt, used by thousands of data teams,
   ships snapshots as a documented, first-class feature specifically to
   give any table backed by dbt Type 2 historical tracking, with the
   `timestamp` and `check` change-detection strategies described in
   dimension 8 (dbt Labs, "Add snapshots to your DAG," verified
   2026-08-02, [docs.getdbt.com/docs/build/snapshots](https://docs.getdbt.com/docs/build/snapshots)).
2. **Fivetran, History Mode.** Fivetran is a widely deployed managed data
   ingestion product. its History Mode feature is described in Fivetran's
   own documentation as implementing "Slowly Changing Dimension (SCD)
   Type 2" tracking at the connector-sync level, adding the
   `_fivetran_start`, `_fivetran_end`, and `_fivetran_active` columns
   (Fivetran Documentation, "History mode," verified 2026-08-02,
   [fivetran.com/docs/core-concepts/sync-modes/history-mode](https://fivetran.com/docs/core-concepts/sync-modes/history-mode)).
3. **Databricks Lakeflow declarative pipelines.** Databricks' own
   documentation states that Lakeflow pipelines have native support for
   tracking and applying SCD Type 1 and Type 2 through an `AUTO CDC ...
   INTO` construct, making SCD handling a supported first-class pipeline
   primitive on the Databricks lakehouse platform rather than something
   every customer hand-rolls (Databricks Documentation, "Use MERGE INTO,"
   verified 2026-08-02, [docs.databricks.com/aws/en/delta/merge](https://docs.databricks.com/aws/en/delta/merge)).
4. **Microsoft SQL Server Integration Services (SSIS).** SSIS has shipped
   a dedicated Slowly Changing Dimension transformation as part of its
   toolbox since early releases of the product, with a wizard that
   explicitly walks the developer through classifying each dimension
   column as a "Changing Attribute" (Type 1) or a "Historical Attribute"
   (Type 2), evidence that the pattern was standard enough by the
   mid-2000s to warrant first-party tooling in a mainstream commercial
   ETL product (Microsoft Learn, "Historical Attribute Options," verified
   2026-08-02, [learn.microsoft.com/previous-versions/sql/sql-server-2008/ms187958](https://learn.microsoft.com/cs-cz/previous-versions/sql/sql-server-2008/ms187958(v=sql.100))).

## 10. Consequences

Positive.

- Historical reports reproduce exactly, because a fact row's join target
  encodes the dimension state that was true when the fact occurred, not
  today's dimension state.
- "As of" and point-in-time analysis (what was true on this date) becomes
  a straightforward filter on the effective-date range rather than an
  unanswerable question, because the historical values still physically
  exist in the table.
- The dimension itself becomes an audit trail. every change, and the exact
  window of time during which the old value was in force, is queryable
  without a separate audit log system.
- The pattern is additive to write volume but never destructive. an
  incorrect or reverted business decision (a category change that gets
  undone) produces a new row rather than losing the record that the change
  ever happened.

Negative.

- Row count and storage grow, potentially significantly, in proportion to
  how often tracked attributes change and how long the warehouse retains
  history, and every index and every join against the dimension pays that
  growth's cost on every query.
- Every query author, and every BI tool's semantic layer, must correctly
  filter to `is_current = true` (or the equivalent effective-date
  comparison) for "current state" questions, and must correctly join facts
  to the surrogate key rather than the natural key for "as of" questions.
  getting either wrong silently double-counts an entity that has multiple
  historical rows.
- The write path gains real complexity and a real correctness hazard, the
  close-old-row-then-open-new-row sequence must be atomic (dimension 11),
  and the change-detection logic itself (timestamp trust versus full-row
  comparison) has to be chosen deliberately and can silently miss changes
  if chosen carelessly.
- Slowly changing dimensions answer "what was true when the fact
  happened," which is a narrower question than "what is the full audit
  history of every change to this entity, including changes nobody ever
  joined a fact against." A true bitemporal or event-sourced model answers
  the broader question, at correspondingly higher modeling and query cost
  (see dimension 13).

## 11. Failure modes and misuse

**Symptom.** Two rows for the same natural key both show `is_current =
true`, and a report that joins facts to the dimension by natural key
instead of surrogate key silently double-counts that entity, inflating a
revenue total or a headcount without any error being raised.
**Cause.** The close-old-row and open-new-row steps in dimension 7 ran as
two separate, non-atomic statements, and either a concurrent load process
interleaved with the same natural key, or the job crashed between the
`UPDATE` and the `INSERT`.
**Fix.** Wrap the version transition in a single transaction (or a single
`MERGE`), and add a deferred or immediate unique constraint on
`(natural_key) WHERE is_current` (a partial unique index in PostgreSQL, or
an equivalent filtered index) so the database itself refuses to ever
persist two current rows for one natural key, turning a silent data
corruption into a loud constraint violation at load time.

**Symptom.** A historical report that used to be stable now returns
different numbers every time it is re-run, even for a date range far in
the past that should never change.
**Cause.** The dimension was implemented as Type 1 (overwrite) for an
attribute the business actually needed Type 2 tracking on, or a supposedly
Type 2 pipeline has a bug where the change-detection step is comparing the
wrong columns and treating a genuine change as a no-op, leaving the old row
in place and simply updating it instead of versioning it.
**Fix.** Re-classify the attribute against dimension 4's applicability
criteria with the actual business stakeholders, not by engineering
assumption, and if Type 2 tracking is required going forward, be explicit
that all history predating the fix cannot be reconstructed unless an
upstream audit trail exists to backfill from.

**Symptom.** The dimension's effective-date ranges have gaps or overlaps
for a natural key, some periods of time have zero current rows and other
periods have two, discovered only when an analyst tries to join a fact
from a specific date and gets no match or duplicate matches.
**Cause.** A late-arriving or out-of-order source extract was loaded, and
the effective-date logic computed `effective_from` and `effective_to`
relative to load time rather than relative to the source system's own
change time, so a batch processed out of chronological order corrupted the
sequencing of an entity's version history.
**Fix.** Prefer, where the source provides it, a source-side change
timestamp for computing effective dates rather than the warehouse's own
load timestamp, and add a validation step, run after every load, that
asserts effective-date ranges are contiguous and non-overlapping per
natural key, failing the load loudly rather than letting a gap silently
ship to production dashboards.

**Symptom.** A change-detection job that compares full source rows to the
current dimension row starts silently treating every incoming row as
unchanged, and new dimension versions stop being created even though the
business genuinely changed data upstream.
**Cause.** A `check`-strategy comparison was configured against an
explicit list of columns, and the source system added, renamed, or
reordered a column, so the comparison is now silently comparing the wrong
pair of values, or a `SELECT *`-based comparison started including a
volatile, irrelevant column (a source-side `last_synced_at` stamp) that now
changes on every extract, making the job think every row changed on every
load, which is the opposite failure and just as damaging, it explodes
dimension row count.
**Fix.** Pin the compared column list explicitly and review it whenever
the source schema changes, rather than comparing `SELECT *`, and add a
regression test (dimension 15) that fails when the configured compared
columns drift from the set of columns the business actually classified as
Type 2 in dimension 4's applicability review.

## 12. Trade-off matrix

| Force | SCD Type 1 (overwrite) | SCD Type 2 (add row) | Event Sourcing | Bitemporal Tables |
|---|---|---|---|---|
| Historical fact accuracy | Lost on overwrite | Preserved exactly as of fact time | Preserved, fully reconstructible from events | Preserved, queryable on two independent time axes |
| Storage growth per change | None, row count constant | One new row per change | One new event per change, plus projections | Two date ranges per row, similar growth to Type 2 |
| Query complexity for "current state" | Trivial, one row per entity | Filter on is_current or max effective date | Requires replaying or reading a materialized projection | Filter on both valid-time and transaction-time "now" |
| Query complexity for "as of" questions | Not answerable at all | Effective-date range filter, moderate | Replay events up to a point in time, or use a snapshot | Filter valid-time range, moderate to high |
| Correction of a past mistake (a bad load) | Overwrites the mistake in place, cannot distinguish it from a real change | Adds a new row, mistake and correction both visible in history | New corrective event, full audit trail of the correction itself | Distinguishes valid-time correction from transaction-time correction |
| Write-path complexity | Lowest | Moderate, atomicity-sensitive | Highest, requires an event store and projection logic | High, two independent date-range writes per change |
| Fits naturally in | A dimensional data warehouse with no historical reporting need | A dimensional data warehouse with historical reporting need | An operational system whose primary need is the change history itself | A regulated system needing both "what we believed" and "what was true" |

## 13. Related and incompatible patterns

**Data Vault.** Data Vault's satellite tables implement a technique
structurally close to a Type 2 dimension, each satellite row carries a
load timestamp and holds one version of a set of attributes for a hub or
link, functioning as history-preserving storage the same way a Type 2
dimension does. Data Vault differs by separating identity (hubs),
relationships (links), and descriptive attributes (satellites) into
distinct table types at the modeling layer, whereas Type 2 SCD keeps
identity and attributes together in a single wide dimension row. A data
warehouse can, and commonly does, use Data Vault as its integration layer
and derive Type 2 dimensions from it for the presentation layer that
business intelligence tools query against.

**Event Sourcing.** Event Sourcing captures every state change as an
immutable, ordered event and derives current or historical state by
replaying events, rather than storing a materialized "before" and "after"
row directly. A Type 2 dimension can be understood as one specific,
denormalized, warehouse-optimized projection that an event-sourced system
could in principle produce, but Type 2 SCD is typically populated by
comparing periodic extracts or a CDC stream against the previous state, not
by replaying a canonical, append-only event log the way event sourcing
does. the two compose well when an operational system is event-sourced and
a downstream warehouse consumes that event stream to build Type 2
dimensions.

**Temporal Tables (bitemporal modeling).** Bitemporal tables generalize
Type 2 SCD's single effective-date range into two independent time axes,
valid time (when a fact was true in the real world) and transaction time
(when the system recorded that fact). A Type 2 dimension typically only
tracks one of these, usually conflating "when the change happened" with
"when we found out about it." A system that needs to distinguish a
retroactive correction (we learned today that a value was actually
different starting last month) from a genuine change (the value changed
today) needs bitemporal modeling, not plain Type 2 SCD.

**Change Data Capture.** CDC is frequently the upstream input that feeds a
Type 2 dimension's change-detection step, as described in dimension 8. CDC
answers "what changed in the source," Type 2 SCD answers "how do we store
that change so historical facts stay correct." they compose directly and
are commonly implemented together, not as alternatives to each other.

**CQRS.** In a CQRS system, the write model may hold only current state,
while a Type 2-style read model can be built as one of potentially several
query-side projections, giving historical reporting capability without
requiring the write side to carry versioning complexity.

**Incompatible with, or in tension with, plain Type 1 dimensions on the
same attribute.** A single attribute cannot simultaneously be Type 1 and
Type 2 on the same physical column without becoming a distinct pattern
(Type 6, which is exactly the "both at once" resolution, at the structural
cost described in dimension 5 and 10). Choosing Type 1 for an attribute
that later turns out to need historical tracking is not merely a design
change, it is a data-loss event for everything already overwritten, and is
why the applicability review in dimension 4 belongs at design time, before
any production data has been through a Type 1 pipeline.

## 14. Refactoring path in and out

**Introducing Type 2 tracking into an existing Type 1 dimension.**

1. Confirm with business stakeholders, using the applicability criteria in
   dimension 4, exactly which columns need historical tracking and which
   can remain Type 1 on the same row. resist the temptation to make every
   column Type 2 by default, it is not free.
2. Add the structural columns from dimension 5 to the existing table, a
   new surrogate key column (if the table was previously keyed only by the
   natural key), `effective_from`, `effective_to`, and `is_current`.
3. Backfill every existing row with `effective_from` set to the earliest
   known load date (or a deliberately chosen "beginning of history"
   sentinel if the true start date is unknown) and `is_current = true`,
   since a freshly-migrated table by definition has no prior versions yet.
4. Repoint every existing fact table's foreign key from the natural key to
   the new surrogate key, if it was not already using a surrogate key. this
   step is the highest-risk part of the migration and should run inside a
   maintenance window with the fact tables' foreign key constraints
   temporarily relaxed and re-validated afterward.
5. Replace the load job's `UPDATE`-in-place logic with the
   compare-and-branch logic from dimension 7, gated behind a feature flag
   or a shadow-run period where both the old and new logic run in
   parallel and their output is diffed before cutting over.
6. Add the load-time validation described in dimension 11 (no two current
   rows per natural key, no gaps or overlaps in effective-date ranges)
   before removing the shadow-run safety net.

**Removing Type 2 tracking, collapsing back to Type 1.**

1. Confirm the business genuinely no longer needs historical reporting on
   the affected attributes, this is rare in practice, because once "as of"
   reporting exists, stakeholders tend to keep relying on it even after the
   original driving requirement fades.
2. Build a Type 1 view or materialized table that selects only the current
   row (`WHERE is_current = true`) per natural key, and repoint any
   consumer that only ever needed current state at that view rather than
   deleting the underlying Type 2 history, so the option to go back is
   preserved.
3. Only physically drop the historical rows and the effective-date columns
   after a retention period long enough that no compliance, audit, or
   finance requirement still needs them, and after confirming no fact rows
   still reference the surrogate keys of the rows being dropped.

## 15. Testing and verification

What Type 2 SCD makes easy to test. the change-detection function itself
(given an old row and a new source row, does it correctly decide "changed"
or "unchanged") is a pure function with no database dependency, and is
straightforward to unit test with table-driven cases covering exact
matches, single-column changes, multi-column changes, and null-handling
edge cases. Because history is preserved rather than overwritten, a test
can also assert against past states directly, load a fixed sequence of
source snapshots, then assert the dimension table's full historical row
set matches an expected fixture, rather than only asserting against final
current state.

What becomes harder to test. the end-to-end atomicity of the version
transition (dimension 7's transaction) is a concurrency property, not a
pure-function property, and needs an integration-level test that
deliberately runs two concurrent load attempts against the same natural key
and asserts the database's constraint (the partial unique index from
dimension 11) rejects the loser rather than silently producing two current
rows. This class of test is easy to skip because it rarely fails on a
developer's laptop with a single-threaded test suite, and only surfaces in
production under real concurrent load, which is exactly why it belongs in
the test suite deliberately rather than being discovered operationally.

Recommended technique. property-based testing is a strong fit for the
effective-date invariants specifically, generate a random sequence of
changes for a natural key with random timestamps, run them through the
versioning logic, and assert as a property (not a single example) that the
resulting effective-date ranges are always contiguous, always
non-overlapping, and always have exactly one row with `is_current = true`
at the end of the sequence, regardless of how many changes or what values
were generated.

## 16. Observability signals

A healthy Type 2 dimension shows a small, roughly steady rate of new-row
insertion per load cycle relative to the total dimension size, proportional
to the real-world rate of change in the tracked attributes, tracked as a
metric such as `scd_new_versions_per_load` broken out by dimension table
and, where feasible, by which specific attribute triggered the change. A
sudden spike in that metric on an otherwise unremarkable day is the primary
early-warning signal for the "comparing the wrong columns" failure mode in
dimension 11, where an irrelevant volatile column starts triggering false
change detection. A sudden drop to near-zero new versions, especially
immediately following an upstream schema change, is the mirror-image signal
for the opposite failure, the comparison silently going stale and stopping
detecting real changes.

Log, at minimum, one structured record per load run carrying the count of
rows evaluated, the count of rows correctly classified as unchanged, the
count of new versions created, the count of brand-new natural keys
inserted for the first time, and the count of any validation failures
(duplicate current rows found, effective-date gaps or overlaps found)
described in dimension 11's fixes. Alert on any nonzero validation-failure
count immediately, because that count crossing zero means the invariant
this whole pattern depends on, exactly one current row per natural key at
all times, has already been violated in production.

A dashboard for a Type 2 dimension in a healthy state shows. dimension row
count growing slowly and roughly linearly over long time windows rather
than in sudden jumps, the ratio of distinct natural keys to total rows
staying stable or declining slowly (indicating a steady per-entity change
rate rather than a runaway one), and zero validation failures across the
observable history of the load job.

## 17. Security and privacy implications

Slowly Changing Dimensions materially increase the personal-data retention
surface of a system whenever the tracked attributes include personal
information, a customer's address, a customer's segment derived from
behavioral data, an employee's role or manager. Where Type 1 overwriting
would have naturally aged out an old value the moment a new one arrived,
Type 2 tracking deliberately retains every historical value forever by
default, which directly increases exposure under data-minimization
principles found in privacy regulation such as the EU's GDPR (the
regulation's general data-minimization and storage-limitation principles,
not a claim about any specific numbered article, since this entry is not a
legal reference and the exact article numbers are outside its scope).
A right-to-erasure or right-to-be-forgotten request against a Type 2
dimension is genuinely harder to satisfy correctly than against a Type 1
dimension, because satisfying it may mean deleting or anonymizing rows
across an entity's entire version history, not just its current row, and
any fact table that still holds surrogate-key references into the deleted
rows needs a deliberate policy (anonymize the historical dimension row in
place while keeping its surrogate key intact, versus deleting it and
accepting an orphaned foreign key on old facts).

Where personal data is tracked with Type 2 semantics, apply an explicit,
bounded retention policy on the historical rows rather than retaining every
version indefinitely by default, and consider whether the specific
attribute genuinely needs person-level historical tracking at all, versus
whether an aggregated or anonymized historical signal (a monthly segment
distribution, rather than a per-customer segment history) would satisfy
the actual reporting need at meaningfully lower privacy risk. This entry
does not have a further security-specific implication beyond the
data-retention concern above, a Type 2 dimension does not itself introduce
a new authentication, authorization, or injection attack surface distinct
from any other database table.

## 18. References

1. Ralph Kimball, "Slowly Changing Dimensions," Kimball Group, published
   2008-09-22, verified 2026-08-02.
   https://www.kimballgroup.com/2008/09/slowly-changing-dimensions/
2. Margy Ross, "Design Tip #152, Slowly Changing Dimension Types 0, 4, 5,
   6 and 7," Kimball Group, published 2013-02-05, verified 2026-08-02.
   https://www.kimballgroup.com/2013/02/design-tip-152-slowly-changing-dimension-types-0-4-5-6-7/
3. Ralph Kimball and Margy Ross, The Data Warehouse Toolkit (subtitled The
   Definitive Guide to Dimensional Modeling), 3rd edition, Wiley, 2013,
   Chapter 2, "Kimball Dimensional Modeling Techniques Overview," section
   "Dealing with Slowly Changing Dimension Attributes." Table of contents
   verified 2026-08-02.
   https://www.wiley.com/en-us/The+Data+Warehouse+Toolkit:+The+Definitive+Guide+to+Dimensional+Modeling,+3rd+Edition-p-9781118530801
4. dbt Labs, "Add snapshots to your DAG," dbt Docs, verified 2026-08-02.
   https://docs.getdbt.com/docs/build/snapshots
5. Fivetran, "History mode," Fivetran Documentation, verified 2026-08-02.
   https://fivetran.com/docs/core-concepts/sync-modes/history-mode
6. Databricks Documentation, "Use MERGE INTO," verified 2026-08-02.
   https://docs.databricks.com/aws/en/delta/merge
7. Snowflake Documentation, "Introduction to streams," verified
   2026-08-02.
   https://docs.snowflake.com/en/user-guide/streams-intro
8. Microsoft Learn, "Historical Attribute Options (Slowly Changing
   Dimension Wizard)," SQL Server 2008 documentation archive, verified
   2026-08-02.
   https://learn.microsoft.com/cs-cz/previous-versions/sql/sql-server-2008/ms187958(v=sql.100)
9. Wikipedia contributors, "Slowly changing dimension," Wikipedia, cited
   for the plain-language summary of Types 0 through 7 and cross-checked
   against sources 1 and 2 above rather than relied on alone, verified
   2026-08-02.
   https://en.wikipedia.org/wiki/Slowly_changing_dimension

## Code examples

The three examples below all implement the same scenario. a customer
dimension tracked with Type 2 semantics, versioning a `segment` attribute
in memory. Each example applies a source change, closes the previous
current version, opens a new current version, and demonstrates an "as of"
historical query alongside a "current state" query. Java is omitted per the
Available toolchains note in the entry template, no working JVM was present
in this environment to compile against.

### TypeScript

```typescript
interface CustomerVersion {
  surrogateKey: number;
  customerId: string;
  segment: string;
  effectiveFrom: Date;
  effectiveTo: Date;
  isCurrent: boolean;
}

class CustomerDimension {
  private rows: CustomerVersion[] = [];
  private nextKey = 1;

  applyChange(customerId: string, segment: string, at: Date): void {
    const current = this.rows.find(
      (r) => r.customerId === customerId && r.isCurrent
    );

    if (current && current.segment === segment) {
      return;
    }

    if (current) {
      current.effectiveTo = at;
      current.isCurrent = false;
    }

    this.rows.push({
      surrogateKey: this.nextKey++,
      customerId,
      segment,
      effectiveFrom: at,
      effectiveTo: new Date("9999-12-31"),
      isCurrent: true,
    });
  }

  currentRow(customerId: string): CustomerVersion | undefined {
    return this.rows.find((r) => r.customerId === customerId && r.isCurrent);
  }

  asOf(customerId: string, when: Date): CustomerVersion | undefined {
    return this.rows.find(
      (r) =>
        r.customerId === customerId &&
        r.effectiveFrom <= when &&
        when < r.effectiveTo
    );
  }
}

function main(): void {
  const dim = new CustomerDimension();
  dim.applyChange("C-1042", "Bronze", new Date("2023-01-01"));
  dim.applyChange("C-1042", "Silver", new Date("2024-03-14"));
  dim.applyChange("C-1042", "Gold", new Date("2025-09-02"));

  const current = dim.currentRow("C-1042");
  const historical = dim.asOf("C-1042", new Date("2023-06-01"));

  console.log(`current segment: ${current?.segment}`);
  console.log(`segment as of 2023-06-01: ${historical?.segment}`);

  if (current?.segment !== "Gold") {
    throw new Error("expected current segment to be Gold");
  }
  if (historical?.segment !== "Bronze") {
    throw new Error("expected historical segment to be Bronze");
  }
}

main();
```

### Python

```python
from dataclasses import dataclass
from datetime import date


@dataclass
class CustomerVersion:
    surrogate_key: int
    customer_id: str
    segment: str
    effective_from: date
    effective_to: date
    is_current: bool


class CustomerDimension:
    def __init__(self) -> None:
        self._rows: list[CustomerVersion] = []
        self._next_key = 1

    def apply_change(self, customer_id: str, segment: str, at: date) -> None:
        current = self._current_row(customer_id)

        if current is not None and current.segment == segment:
            return

        if current is not None:
            current.effective_to = at
            current.is_current = False

        self._rows.append(
            CustomerVersion(
                surrogate_key=self._next_key,
                customer_id=customer_id,
                segment=segment,
                effective_from=at,
                effective_to=date(9999, 12, 31),
                is_current=True,
            )
        )
        self._next_key += 1

    def _current_row(self, customer_id: str) -> CustomerVersion | None:
        for row in self._rows:
            if row.customer_id == customer_id and row.is_current:
                return row
        return None

    def as_of(self, customer_id: str, when: date) -> CustomerVersion | None:
        for row in self._rows:
            if (
                row.customer_id == customer_id
                and row.effective_from <= when < row.effective_to
            ):
                return row
        return None


def main() -> None:
    dim = CustomerDimension()
    dim.apply_change("C-1042", "Bronze", date(2023, 1, 1))
    dim.apply_change("C-1042", "Silver", date(2024, 3, 14))
    dim.apply_change("C-1042", "Gold", date(2025, 9, 2))

    current = dim._current_row("C-1042")
    historical = dim.as_of("C-1042", date(2023, 6, 1))

    assert current is not None and current.segment == "Gold"
    assert historical is not None and historical.segment == "Bronze"

    print(f"current segment: {current.segment}")
    print(f"segment as of 2023-06-01: {historical.segment}")


if __name__ == "__main__":
    main()
```

### Go

```go
package main

import (
	"fmt"
	"time"
)

type CustomerVersion struct {
	SurrogateKey  int
	CustomerID    string
	Segment       string
	EffectiveFrom time.Time
	EffectiveTo   time.Time
	IsCurrent     bool
}

type CustomerDimension struct {
	rows    []*CustomerVersion
	nextKey int
}

func NewCustomerDimension() *CustomerDimension {
	return &CustomerDimension{nextKey: 1}
}

var farFuture = time.Date(9999, 12, 31, 0, 0, 0, 0, time.UTC)

func (d *CustomerDimension) ApplyChange(customerID, segment string, at time.Time) {
	current := d.currentRow(customerID)

	if current != nil && current.Segment == segment {
		return
	}

	if current != nil {
		current.EffectiveTo = at
		current.IsCurrent = false
	}

	d.rows = append(d.rows, &CustomerVersion{
		SurrogateKey:  d.nextKey,
		CustomerID:    customerID,
		Segment:       segment,
		EffectiveFrom: at,
		EffectiveTo:   farFuture,
		IsCurrent:     true,
	})
	d.nextKey++
}

func (d *CustomerDimension) currentRow(customerID string) *CustomerVersion {
	for _, r := range d.rows {
		if r.CustomerID == customerID && r.IsCurrent {
			return r
		}
	}
	return nil
}

func (d *CustomerDimension) AsOf(customerID string, when time.Time) *CustomerVersion {
	for _, r := range d.rows {
		if r.CustomerID == customerID &&
			!when.Before(r.EffectiveFrom) &&
			when.Before(r.EffectiveTo) {
			return r
		}
	}
	return nil
}

func main() {
	dim := NewCustomerDimension()
	dim.ApplyChange("C-1042", "Bronze", time.Date(2023, 1, 1, 0, 0, 0, 0, time.UTC))
	dim.ApplyChange("C-1042", "Silver", time.Date(2024, 3, 14, 0, 0, 0, 0, time.UTC))
	dim.ApplyChange("C-1042", "Gold", time.Date(2025, 9, 2, 0, 0, 0, 0, time.UTC))

	current := dim.currentRow("C-1042")
	historical := dim.AsOf("C-1042", time.Date(2023, 6, 1, 0, 0, 0, 0, time.UTC))

	if current == nil || current.Segment != "Gold" {
		panic("expected current segment to be Gold")
	}
	if historical == nil || historical.Segment != "Bronze" {
		panic("expected historical segment to be Bronze")
	}

	fmt.Printf("current segment: %s\n", current.Segment)
	fmt.Printf("segment as of 2023-06-01: %s\n", historical.Segment)
}
```

### Rust

```rust
use std::collections::HashMap;

#[derive(Debug, Clone)]
struct CustomerVersion {
    surrogate_key: u64,
    customer_id: String,
    segment: String,
    effective_from: i64,
    effective_to: i64,
    is_current: bool,
}

const FAR_FUTURE: i64 = i64::MAX;

struct CustomerDimension {
    rows: Vec<CustomerVersion>,
    next_key: u64,
}

impl CustomerDimension {
    fn new() -> Self {
        CustomerDimension { rows: Vec::new(), next_key: 1 }
    }

    fn apply_change(&mut self, customer_id: &str, segment: &str, at: i64) {
        let current_idx = self
            .rows
            .iter()
            .position(|r| r.customer_id == customer_id && r.is_current);

        if let Some(idx) = current_idx {
            if self.rows[idx].segment == segment {
                return;
            }
            self.rows[idx].effective_to = at;
            self.rows[idx].is_current = false;
        }

        self.rows.push(CustomerVersion {
            surrogate_key: self.next_key,
            customer_id: customer_id.to_string(),
            segment: segment.to_string(),
            effective_from: at,
            effective_to: FAR_FUTURE,
            is_current: true,
        });
        self.next_key += 1;
    }

    fn current_row(&self, customer_id: &str) -> Option<&CustomerVersion> {
        self.rows
            .iter()
            .find(|r| r.customer_id == customer_id && r.is_current)
    }

    fn as_of(&self, customer_id: &str, when: i64) -> Option<&CustomerVersion> {
        self.rows.iter().find(|r| {
            r.customer_id == customer_id
                && r.effective_from <= when
                && when < r.effective_to
        })
    }
}

fn main() {
    let mut dim = CustomerDimension::new();
    dim.apply_change("C-1042", "Bronze", 20230101);
    dim.apply_change("C-1042", "Silver", 20240314);
    dim.apply_change("C-1042", "Gold", 20250902);

    let current = dim.current_row("C-1042").expect("current row must exist");
    let historical = dim
        .as_of("C-1042", 20230601)
        .expect("historical row must exist");

    assert_eq!(current.segment, "Gold");
    assert_eq!(historical.segment, "Bronze");

    println!("current segment: {}", current.segment);
    println!("segment as of 2023-06-01: {}", historical.segment);

    let _ = HashMap::<String, u64>::new();
}
```
