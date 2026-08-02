---
name: Command Query Responsibility Segregation
slug: cqrs
family: 08-cloud-distributed
category: Data and Consistency
aliases: [CQRS, Command Query Responsibility Separation, Read Model Write Model Split]
first_described: "Greg Young 2010, extending Bertrand Meyer's Command Query Separation"
maturity: established
related: [event-sourcing, materialized-view, transactional-outbox, saga, event-driven-architecture, database-per-service, cache-aside]
incompatible_with: [shared-database]
verified: 2026-08-02
---

# Command Query Responsibility Segregation

## 1. Name, aliases, and lineage

The canonical name is Command Query Responsibility Segregation, almost always
written as CQRS. The pattern was named and developed by Greg Young, and Martin
Fowler credits him directly, opening his bliki entry with the statement that it
is a pattern he first heard described by Greg Young
([martinfowler.com/bliki/CQRS.html](https://martinfowler.com/bliki/CQRS.html),
verified 2026-08-02).

The lineage runs back one step further. Young's own collected writing states
that CQRS originated with Bertrand Meyer's Command Query Separation principle,
and he reproduces the CQS definition before explaining where the two part
company (Greg Young, *CQRS Documents*, 2010, chapter "Command and Query
Responsibility Segregation", section "Origins",
[cqrs.files.wordpress.com/2010/11/cqrs_documents.pdf](https://cqrs.files.wordpress.com/2010/11/cqrs_documents.pdf),
verified 2026-08-02). Meyer's principle is that a method either performs an
action or returns data, never both. Fowler attributes CQS to Meyer's book
*Object-Oriented Software Construction* and summarises it as queries returning a
result without changing observable state, and commands changing state without
returning a value
([martinfowler.com/bliki/CommandQuerySeparation.html](https://martinfowler.com/bliki/CommandQuerySeparation.html),
verified 2026-08-02).

The distinction between CQS and CQRS is the single most useful thing to fix in
your head before reading further, and Young states it plainly. CQS separates
*methods* on one object. CQRS separates the *object* itself into two, one
carrying the commands and one carrying the queries. In his own words from the
Origins section, the fundamental difference is that in CQRS objects are split
into two objects, one containing the commands and one containing the queries.
He also records that CQRS was for a long time discussed as CQS applied at a
higher level, and that after enough confusion between the two it was correctly
judged to be a different pattern.

Aliases in real use are thin, because the acronym stuck. Some teams say Command
Query Responsibility Separation, borrowing Meyer's noun by mistake. Some say
"read model write model split", which describes the common implementation rather
than the pattern. In the Domain-Driven Design community the pattern is usually
named alongside the Bounded Context it lives inside, since applying it globally
is the documented failure mode covered in dimension 4.

One naming hazard deserves its own line. A great deal of writing uses CQRS as
shorthand for "event sourcing plus message bus plus separate read database". That
bundle is a real architecture, and it is a common one, but it is not what the
pattern means. Young addressed this in a 2010 post titled "CQRS, Task Based UIs,
Event Sourcing agh!", published 2010-02-16, where he wrote that CQRS is not
eventual consistency, it is not eventing, it is not messaging, it is not having
separated models for reading and writing, nor is it using event sourcing. He
described it instead as the creation of two objects where there was previously
only one. The original post lived at codebetter.com and the text is preserved in
a public archive gist
([gist.github.com/meigwilym/025f08208b5640ad26bc410c8a83b10f](https://gist.github.com/meigwilym/025f08208b5640ad26bc410c8a83b10f),
verified 2026-08-02).

That sentence is worth reading twice, because it is the author of the pattern
telling you that the four things most people mean by CQRS are not CQRS. Those
four things are *enabled* by the split. They are not the split.

## 2. Problem and context

A single model is being asked to serve two jobs whose requirements have diverged,
and the model is losing on both.

The shape of it in a real codebase is recognisable without any pattern
vocabulary. There is one set of domain classes, mapped to one schema, used by
both the code that changes things and the code that displays things. Over a
couple of years the following accumulates.

The write path grows guards. An order cannot be cancelled after dispatch. A seat
cannot be double-allocated. A subscription cannot exceed its plan quota. These
rules need a small, tightly-scoped object graph loaded inside a transaction, and
they need that graph to be correct at the instant of the decision.

The read path grows joins. The order list screen needs the customer name, the
carrier, the last tracking event, a computed total, and a flag for whether a
refund is in flight. Those live in five tables. The query gets a sixth join for
the admin variant, and a seventh for the mobile variant. Somebody adds an index
to make the query fast, and the index slows the write path down. Somebody adds a
denormalised column, and now the write path has to keep it in sync.

The mapping layer grows lies. The domain object has private setters and
invariant-checking methods, so the read path cannot use it directly and maps it
to a DTO. But loading the full aggregate to render a list is expensive, so
somebody adds a lazy-loading strategy, which produces N+1 queries under load, so
somebody adds a fetch join, which pulls fields the screen does not need. Udi
Dahan named this friction directly, asking why domain objects are transformed to
DTOs to cross a wire and then transformed again into view model objects
([udidahan.com/2009/12/09/clarified-cqrs/](https://udidahan.com/2009/12/09/clarified-cqrs/),
published 2009-12-09, verified 2026-08-02).

The Azure Architecture Center describes the same accumulation as four named
problems with a single-model CRUD design. Data mismatch, where the read and
write representations genuinely differ. Lock contention, where parallel
operations on one dataset fight. Performance problems from query complexity and
data-access load. Security difficulty, because entities subject to both reads and
writes are hard to scope
([learn.microsoft.com/en-us/azure/architecture/patterns/cqrs](https://learn.microsoft.com/en-us/azure/architecture/patterns/cqrs),
verified 2026-08-02).

Young's own framing of the asymmetry is sharper and worth carrying. In the CQRS
chapter he lists the differing needs side by side. On consistency, the command
side is easier to build with consistent data than with the edge cases eventual
consistency introduces, while most systems can be eventually consistent on the
query side. On storage, the command side wants normalised data near third normal
form, while the query side wants denormalisation to cut joins. On scalability, in
most web systems the command side processes a small percentage of the total
traffic while the query side processes a very large percentage, often two or more
orders of magnitude more. He closes that list with the sentence that carries the
whole argument. It is not possible to create an optimal solution for searching,
reporting, and processing transactions using a single model (Greg Young, *CQRS
Documents*, 2010, chapter "Command and Query Responsibility Segregation").

There is a second problem, different in kind, that also lands on CQRS, and it
arrives from service decomposition rather than from model strain. Once each
service owns its own database, a query that needs data from three services can no
longer be a join. Chris Richardson states the problem in exactly those terms,
framing CQRS as the answer to how to implement a query that retrieves data from
multiple services in a microservice architecture
([microservices.io/patterns/data/cqrs.html](https://microservices.io/patterns/data/cqrs.html),
verified 2026-08-02). The answer is a read model that subscribes to events from
several services and maintains a joined view locally.

The context that makes CQRS the right answer, rather than a costly detour, has
these parts.

- The domain has real behaviour, not field assignment. If every command is
  "set these fields", the write model has nothing to protect and the split buys
  nothing.
- Read and write requirements have genuinely parted ways along at least one axis,
  whether scale, shape, latency, or availability. A difference in *feeling* is
  not enough. Measure it.
- The team can absorb the operational surface. Somebody has to own projection
  lag, rebuilds, and the staleness question in the UI.
- The scope is one bounded context, not the system. This is not optional, see
  dimension 4.

## 3. Forces

This dimension mixes sourced constraints with engineering judgement about which
pressure weighs heaviest. The judgement calls are labelled as such.

**Read scalability. Favoured, strongly.** Separate read models can be replicated,
sharded, and denormalised without the write path paying for it. AWS documents the
common combinations directly, including a NoSQL command side with an RDBMS query
side, and an RDBMS command side with reads routed to replicas
([docs.aws.amazon.com/prescriptive-guidance/latest/modernization-data-persistence/cqrs-pattern.html](https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-data-persistence/cqrs-pattern.html),
verified 2026-08-02).

**Consistency. Sacrificed, and this is the price.** Both Microsoft and AWS state
the same conclusion in plain language. The Azure page lists eventual consistency
as a problem to consider, noting that read data might not show the most recent
changes immediately and that detecting and handling scenarios where a user acts on
stale data requires careful consideration. AWS is blunter, marking it as an
Important callout that the pattern ordinarily results in eventual consistency
between the data stores. Note the boundary. The write model itself stays
strongly consistent inside its transaction. It is the *view* that lags.

**Write-side invariant clarity. Favoured.** Judgement, but well supported. Once
the write model no longer has to be a good query source, it can shrink to only
the state the invariant needs. That is the difference between an aggregate that
loads a customer with their thousand orders and one that loads a seat pool with a
count. The Microsoft guidance makes the corresponding point from the other
direction, that aggregate modelling adds complexity to query logic while
delivering no benefit for read-only queries
([learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/eshoponcontainers-cqrs-ddd-microservice](https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/eshoponcontainers-cqrs-ddd-microservice),
verified 2026-08-02).

**Cognitive load. Sacrificed.** Fowler is direct that CQRS is a large mental
step for everyone involved and should not be attempted unless the benefit
justifies the step. A new engineer must now learn that the thing they read is not
the thing they wrote, that the gap is bounded but nonzero, and that fixing a bug
in the view may mean a replay rather than an UPDATE.

**Operability. Sacrificed, in a way teams routinely underestimate.** Judgement
drawn from practice. A single model has one thing to watch. A split model has a
projector, a lag metric, a rebuild procedure, a poison-event policy, and a drift
detector. None of these is hard individually. Collectively they are a service.

**Cost. Mixed.** With separate stores you pay for two stores plus the transport
between them. Against that, the read store is frequently cheaper per query
because it answers without joins, and the write store can be provisioned small
because it carries a fraction of the traffic. Judgement, and stated as such. For
a read-heavy system past a certain size this trade is favourable, and below that
size it is not.

**Team topology. Favoured.** Microsoft lists separation of development concerns
as a reason to use the pattern, describing one team implementing the write-model
business logic while another develops the read model and the UI components. This
is real and is often the strongest argument in a large organisation.

**Availability. Favoured, conditionally.** If the read store is separate and the
write store is down, queries keep serving stale data instead of returning errors.
Whether that is a benefit depends entirely on the domain. For a catalogue it is
excellent. For a balance display before a transfer it is a hazard.

**Latency. Mixed and directional.** Query latency generally improves, because a
denormalised view avoids joins. The write-to-visible latency gets worse, by
exactly the projection lag. Systems that measure only the first number and
report a win are measuring half the change.

A pattern with no cost would be a feature of the database. The cost here is paid
in consistency and in the operational surface of the projection.

## 4. Applicability and non-applicability

### When to reach for it

- **Read and write load differ by an order of magnitude or more.** Young's own
  observation is that the query side often carries two or more orders of
  magnitude more traffic than the command side in web systems. That asymmetry is
  what makes independent scaling pay.
- **The read shape cannot be produced cheaply from the write shape.** A screen
  that needs six joins, a search index, a geospatial query, or a graph traversal
  over data stored relationally is a candidate.
- **A query must span services that own separate databases.** This is
  Richardson's framing, and the read model becomes the only place the join can
  legally happen.
- **The domain is genuinely complex on the write side.** Microsoft names
  task-based user interfaces and collaborative environments where several users
  modify the same data, noting that commands with enough granularity can prevent
  conflicts.
- **You are already event sourcing.** Here CQRS stops being optional. Young
  explains the mechanics. With an event-sourced store you cannot ask a query such
  as "give me all users whose first name is Greg", because there is no
  representation of current state, and with CQRS the only query the domain needs
  is get-by-id, which an event store supports. Richardson lists the same
  dependency, calling CQRS necessary in an event-sourced architecture.
- **Read and write have different availability or security requirements.** A
  public read API backed by its own store and a locked-down internal write path
  is easier to reason about than one model with row-level permissions doing both
  jobs.

### Non-applicability. When NOT to reach for it

This is the list that matters, and it is the one most catalogs leave out.

- **Do not apply it to the whole system.** Fowler states the constraint directly.
  CQRS should only be used on specific portions of a system, a Bounded Context in
  DDD terms, and not the system as a whole. Microsoft says the same thing under
  its own heading, "CQRS and DDD patterns are not top-level architectures",
  adding that forcing the same pattern everywhere leads to failure and that many
  subsystems are simpler and better implemented as plain CRUD services. A system
  described as "a CQRS architecture" has, in the terms of both sources, already
  gone wrong.
- **Do not use it when the domain is simple.** Microsoft's own "might not be
  suitable" list is two items long. The domain or business rules are simple, and
  a simple CRUD-style interface with basic data access is sufficient. If your
  commands are field assignments, stop here.
- **Do not use it to fix a slow query you have not tried to fix.** An index, a
  covering index, a materialised view inside the same database, or a query rewrite
  costs hours. A projection pipeline costs a quarter and then costs maintenance
  forever. Judgement, stated as such, but it follows from the cost side of
  dimension 3.
- **Do not use it where the user must read their own write synchronously and the
  domain forbids any workaround.** Financial confirmations, legal attestation
  flows, and anything where showing a stale value creates liability. It can be
  made to work with the techniques in dimension 8, but if none of them are
  acceptable, the pattern is the wrong tool.
- **Do not use it as a substitute for read replicas when replicas would do.**
  Covered in detail in dimension 12. If the only problem is read *volume* and the
  read *shape* is fine, a replica gives you most of the benefit for a fraction of
  the cost.
- **Do not use it when the team cannot own the projection.** If there is nobody
  to page when the projector falls behind, the pattern will silently degrade into
  a system serving hours-old data with no alarm. Judgement.
- **Do not adopt it to get event sourcing.** They are separable in both
  directions. You can do CQRS with two SQL tables and a trigger and no events at
  all. Young's own list of what CQRS is not includes event sourcing explicitly.
  If what you want is an audit log, build an audit log.
- **Do not apply it to reference data.** Currency codes, country lists, tax
  tables. There is no write model worth speaking of. A cache is the answer.
- **Do not use it where reads and writes are strongly coupled in the same
  interaction loop.** A spreadsheet-like editing surface, a collaborative
  whiteboard, or a wizard that reads back what it wrote on every step will fight
  the pattern the whole way. Judgement.

## 5. Structure

The pattern has five roles. Two of them are optional depending on the variant,
and saying which are which is most of what dimension 8 is about.

**Command.** A named, intent-carrying request to change state. Microsoft's
guidance is that commands should represent business tasks rather than low-level
data updates, giving "Book hotel room" against "Set ReservationStatus to
Reserved" as the contrast. A command is imperative, it is addressed to one
consistency boundary, and it can be rejected.

**Command Handler and Write Model.** The handler loads the write model, invokes
the behaviour, and persists. The write model holds only the state its invariants
need. In DDD terms this is the aggregate. Microsoft describes the write model as
carrying validation and domain logic and being optimised for transactional
integrity, and separately describes the aggregate as treating many domain objects
as a single unit for data changes.

**Query and Read Model.** A query returns data and changes nothing. Microsoft
states that queries never alter data and instead return DTOs presenting the
required data in a convenient format without domain logic, and that the read
model has no business logic or validation stack. This is the role people
under-build. The read model is not a thin wrapper over the write model. It is a
first-class artefact shaped by the screen or API that consumes it.

**Synchroniser.** Present only in the separate-store variant. It carries changes
from the write side to the read side. Microsoft describes the common form as the
write model publishing events when it updates the database, which the read model
consumes to refresh its data. The synchroniser is where the outbox, the change
feed, or the log tail lives.

**Projection.** The function from an event, or a change record, to a mutation of
the read model. A projection is where denormalisation actually happens, and it
carries its own version or offset so it can be resumed and rebuilt. Marten's
documentation describes projections as taking raw event data and aggregating it
into a form clients consume, and states that projections need rebuilding when the
code defining them changes in a way that requires events to be reapplied
([martendb.io/events/projections/](https://martendb.io/events/projections/),
verified 2026-08-02).

The relationships. The command handler depends on the write model and never on
the read model. The query handler depends on the read model and never on the
write model. Nothing on the query side may call into the write side, and the
write side may not query the read model to make a decision, because the read
model is stale by construction. That last constraint is the one violated most
often, and dimension 11 records what it looks like when it breaks.

## 6. ASCII structure diagram

```
                        +---------------------------+
   intent               |         Client            |            need
   (mutate)             +---------------------------+          (display)
       |                   |                     |                  |
       v                   v                     v                  v
+--------------+  Command  |                     |  Query   +---------------+
|   Command    |<----------+                     +--------->|     Query     |
|   Handler    |                                            |    Handler    |
+--------------+                                            +---------------+
       |                                                            |
       | load / save                                                | read only
       v                                                            v
+--------------+                                            +---------------+
|  Write Model |                                            |   Read Model  |
|  (aggregate) |                                            |  (projection) |
|              |                                            |               |
| invariants   |                                            | denormalised  |
| normalised   |                                            | per-screen    |
| small graph  |                                            | version/offset|
+--------------+                                            +---------------+
       |                                                            ^
       v                                                            |
+--------------+       +------------------+       +-----------------+
| Write Store  |------>|   Synchroniser   |------>|   Projection    |
| (SoR)        | change|  outbox / CDC /  | event | apply(event) ->  |
+--------------+ feed  |  event stream    |       | mutate view      |
                       +------------------+       +-----------------+

   Legend
   SoR          system of record, the only authority on current state
   Synchroniser present only in the separate-store variant
   ------>      data flow, never a call back in the reverse direction
```

The one-store variant is the same picture with the bottom row deleted and both
models pointing at the same database. That variant is real, it is what Microsoft
calls the foundational level of CQRS, and it is where most teams should start.

## 7. Dynamics

Two flows matter. The write-then-read race is the one that surprises people, so
it is drawn first.

```
Client        CmdHandler   WriteStore   Sync      Projector   ReadStore
  |               |            |         |            |           |
  |--Reserve----->|            |         |            |           |
  |               |--load----->|         |            |           |
  |               |<--state----|         |            |           |
  |               | check invariant      |            |           |
  |               |--append v=7--------->|            |           |
  |               |            |--emit-->|            |           |
  |<--Accepted----|            |         |            |           |
  |   {version 7} |            |         |            |           |
  |               |            |         |--event---->|           |
  |--Query------->|            |         |            |--upsert-->|
  |   (no token)  |            |         |            |           |
  |<--view v=6----|   STALE. the client sees its own write missing |
  |               |            |         |            |           |
  |               |            |         |            |  (t + lag) |
  |--Query------->|            |         |            |           |
  |   {min 7}     |            |         |            |           |
  |<--view v=7----|   CONSISTENT for this caller                   |
```

The window between "Accepted" and the view reaching version 7 is the projection
lag. It is not a bug. It is the thing you bought. The design question is what the
client does inside that window, and dimension 8 lists the four answers.

The rebuild flow is the second one, and it is the operation that makes the
pattern recoverable rather than fragile.

```
   projection code changes (new field, fixed bug, new screen)
                    |
                    v
   +-----------------------------------------------------+
   |  1. deploy new projector, DO NOT delete old view     |
   |  2. create view_v2 alongside view_v1                 |
   |  3. replay stream from offset 0 into view_v2         |
   |       |                                             |
   |       +--> catching up ... lag shrinking            |
   |  4. when view_v2 offset >= view_v1 offset, flip read |
   |     traffic to v2 (feature flag or alias swap)       |
   |  5. observe, then retire view_v1                     |
   +-----------------------------------------------------+

   Precondition. The source must be replayable. An event store is.
   A CDC feed with limited retention is only partly. A queue that
   dropped its messages after delivery is not, and a rebuild is
   then impossible without re-deriving from the write store.
```

That precondition is the sharpest practical difference between doing CQRS on top
of an event store and doing it on top of a message queue. Marten's documentation
covers the same operation, describing rebuilds run on demand through its daemon.

## 8. Implementation variants

### Variant A. Two models, one database

Both models live in one schema. Writes go through the domain model. Reads go
through a separate, thin data-access path, often hand-written SQL or a micro-ORM,
returning DTOs shaped for the screen.

Microsoft describes this as the foundational level of CQRS, and its own reference
application uses it. The eShopOnContainers ordering microservice is documented as
based on CQRS principles while using the simplest approach, separating queries
from commands and using the same database for both, with queries implemented in
Dapper against the same tables the domain model writes.

Trade. No eventual consistency at all, because there is one store and one
transaction. No synchroniser to operate. You still get the modelling win and the
mapping-layer win. You do not get independent scaling, and you do not get a
different storage technology per side. This is the variant most teams should
adopt first and many should stop at.

### Variant B. Separate stores, synchronised by events

The write model publishes events on commit. A projector consumes them and
maintains a read store, often a different technology. Microsoft describes this as
the advanced implementation and states plainly that when separate stores are used
you must keep both synchronised, and that because message brokers and databases
usually cannot be enlisted in one distributed transaction, consistency challenges
arise between updating the database and publishing events.

That last sentence is the transactional outbox problem, and it is not optional to
solve. The write and the publish must be atomic or you will lose events. The
named pattern is Transactional Outbox, in which the event is written to a table in
the same transaction as the state change and relayed afterwards
([microservices.io/patterns/data/transactional-outbox.html](https://microservices.io/patterns/data/transactional-outbox.html),
verified 2026-08-02).

Trade. Full independent scaling and per-side technology choice. Full eventual
consistency cost, plus an outbox, plus a relay, plus a rebuild story.

### Variant C. Change data capture instead of domain events

Rather than the application publishing events, a CDC tool tails the database
transaction log and emits change records. Debezium is the common implementation,
documented as capturing row-level changes and streaming them
([debezium.io/documentation/reference/stable/architecture.html](https://debezium.io/documentation/reference/stable/architecture.html),
verified 2026-08-02).

Trade. The write application needs no change at all, and there is no dual-write
problem because the log is the transaction. Against that, you get row deltas, not
business intent. A projector fed by CDC sees "column status changed from 2 to 3",
not "OrderDispatched". Reconstructing intent from column diffs is exactly the
coupling the pattern was meant to remove, and it ages badly when the write schema
is refactored. Judgement, and stated as such. CDC is excellent for populating
analytics and search read models, and poor for read models that need to express
domain meaning.

### Variant D. Event-sourced write side

The write store is an append-only event stream and current state is derived by
replay. Here CQRS is not a choice, it is a requirement, for the reason Young
gives about the absence of a current-state representation. The read models are
projections over the same stream, and they are fully rebuildable by construction.

Trade. The rebuild story is the best available and the audit trail is free.
Microsoft's own considerations for the combination are worth repeating. View
generation can consume considerable time and resources, and calculations spanning
long periods require examining all related events, which is why snapshots exist.
The Azure guidance recommends snapshotting entity state at intervals to avoid
reprocessing full history.

### Variant E. Read-your-own-writes strategies

This is a variant of the client contract rather than the storage, and it is the
part teams most often leave undesigned. Four workable answers.

1. **Version token.** The command returns the version it wrote. The client passes
   it as a minimum on the next query, and the query either waits briefly or
   reports staleness. This is what the code samples in this entry implement, and
   it is the most honest option because staleness becomes explicit data rather
   than a race.
2. **Read from the write model for the caller's own entity.** After booking,
   render the confirmation from the aggregate, not the projection. Everyone
   else's view is eventually consistent. Only the actor gets the strong read.
   Cheap and effective.
3. **Client-side optimistic apply.** The UI applies the change it knows it made
   and reconciles when the projection catches up. Standard in single-page
   applications, and it moves the problem into the client where a rollback is a
   UI concern.
4. **Do not show it at all.** Udi Dahan's suggestion is to stop returning the
   result, telling the user their request is accepted and confirmation follows.
   This sounds evasive and often is not. Many workflows are genuinely
   asynchronous and pretending otherwise is the actual lie.

### Variant F. Synchronous projection inside the write transaction

Marten calls these inline projections and documents them as executed at the time
of event capture in the same unit of work that persists the projected documents.
The read model updates atomically with the write.

Trade. No lag, no staleness, no read-your-writes problem. In exchange, the write
transaction now carries the projection cost, the two models cannot scale
independently, and a slow projection becomes a slow write. This is the halfway
house between variants A and B and it is underused.

### Language-shaped variants

In Go and Rust, where inheritance is not the organising tool, the write model
tends to be a struct with a method returning a slice or `Vec` of events, and the
projector a function over that slice. There is no framework and none is needed,
which is visible in the samples below.

In TypeScript the read model is frequently a plain type with no class at all,
because it has no behaviour to protect, while the write model keeps a class to
hold private state. The asymmetry in the code is the pattern, made visible.

In Python the same asymmetry appears as a frozen dataclass for events and the
view, against a mutable class for the aggregate.

### Code

The four samples below implement the same seat-allocation slice. The write model
enforces a capacity invariant and emits events. The projector maintains a
denormalised view with a version. The query reports staleness against a caller's
minimum version, which is variant E option 1. All four were compiled and run and
produce identical output.

Python. Run with `python3`.

```python
from dataclasses import dataclass, field


@dataclass(frozen=True)
class SeatReserved:
    pool_id: str
    user_id: str
    version: int


class SeatPool:
    """Write model. Holds only the state needed to enforce the invariant."""

    def __init__(self, pool_id: str, capacity: int) -> None:
        self.pool_id = pool_id
        self.capacity = capacity
        self.holders: set[str] = set()
        self.version = 0

    def reserve(self, user_id: str) -> list[SeatReserved]:
        if user_id in self.holders:
            return []
        if len(self.holders) >= self.capacity:
            raise ValueError("pool exhausted")
        self.version += 1
        self.holders.add(user_id)
        return [SeatReserved(self.pool_id, user_id, self.version)]


@dataclass
class SeatsView:
    """Read model. Denormalised, carries the version it has caught up to."""
    remaining: int
    holders: list[str] = field(default_factory=list)
    version: int = 0


class Projector:
    def __init__(self, capacity: int) -> None:
        self.view = SeatsView(remaining=capacity)

    def apply(self, event: SeatReserved) -> None:
        if event.version <= self.view.version:
            return
        self.view.holders.append(event.user_id)
        self.view.remaining -= 1
        self.view.version = event.version


def query(projector: Projector, min_version: int) -> tuple[SeatsView, bool]:
    """Returns the view plus whether it is stale for this caller's own write."""
    return projector.view, projector.view.version < min_version


if __name__ == "__main__":
    pool = SeatPool("ws-42", capacity=2)
    proj = Projector(capacity=2)

    events = pool.reserve("ada")
    view, stale = query(proj, min_version=events[-1].version)
    print("before projection", view.remaining, "stale", stale)

    for e in events:
        proj.apply(e)
    view, stale = query(proj, min_version=events[-1].version)
    print("after projection ", view.remaining, "stale", stale)

    for e in pool.reserve("grace"):
        proj.apply(e)
    print("holders", proj.view.holders, "remaining", proj.view.remaining)

    try:
        pool.reserve("linus")
    except ValueError as exc:
        print("write model rejected", exc)
```

TypeScript. Compiled with `tsc --strict --target ES2022`, run with `node`.

```typescript
type SeatReserved = {
  readonly kind: "SeatReserved";
  readonly poolId: string;
  readonly userId: string;
  readonly version: number;
};

class SeatPool {
  private readonly holders = new Set<string>();
  private version = 0;

  constructor(private readonly poolId: string, private readonly capacity: number) {}

  reserve(userId: string): SeatReserved[] {
    if (this.holders.has(userId)) return [];
    if (this.holders.size >= this.capacity) throw new Error("pool exhausted");
    this.version += 1;
    this.holders.add(userId);
    return [{ kind: "SeatReserved", poolId: this.poolId, userId, version: this.version }];
  }
}

type SeatsView = { remaining: number; holders: string[]; version: number };

class Projector {
  readonly view: SeatsView;

  constructor(capacity: number) {
    this.view = { remaining: capacity, holders: [], version: 0 };
  }

  apply(event: SeatReserved): void {
    if (event.version <= this.view.version) return;
    this.view.holders.push(event.userId);
    this.view.remaining -= 1;
    this.view.version = event.version;
  }
}

function query(p: Projector, minVersion: number): { view: SeatsView; stale: boolean } {
  return { view: p.view, stale: p.view.version < minVersion };
}

const pool = new SeatPool("ws-42", 2);
const proj = new Projector(2);

const events = pool.reserve("ada");
console.log("before projection", query(proj, events[0].version).stale);
events.forEach((e) => proj.apply(e));
console.log("after projection ", query(proj, events[0].version).stale);

pool.reserve("grace").forEach((e) => proj.apply(e));
console.log(proj.view.holders, proj.view.remaining);

try {
  pool.reserve("linus");
} catch (e) {
  console.log("write model rejected", (e as Error).message);
}
```

Go. Vetted with `go vet`, run with `go run`.

```go
package main

import (
	"errors"
	"fmt"
)

type SeatReserved struct {
	PoolID  string
	UserID  string
	Version int
}

// SeatPool is the write model. It holds only what the invariant needs.
type SeatPool struct {
	id       string
	capacity int
	holders  map[string]bool
	version  int
}

func NewSeatPool(id string, capacity int) *SeatPool {
	return &SeatPool{id: id, capacity: capacity, holders: map[string]bool{}}
}

func (p *SeatPool) Reserve(userID string) ([]SeatReserved, error) {
	if p.holders[userID] {
		return nil, nil
	}
	if len(p.holders) >= p.capacity {
		return nil, errors.New("pool exhausted")
	}
	p.version++
	p.holders[userID] = true
	return []SeatReserved{{p.id, userID, p.version}}, nil
}

// SeatsView is the read model, denormalised and versioned.
type SeatsView struct {
	Remaining int
	Holders   []string
	Version   int
}

type Projector struct{ View SeatsView }

func NewProjector(capacity int) *Projector {
	return &Projector{View: SeatsView{Remaining: capacity}}
}

func (pr *Projector) Apply(e SeatReserved) {
	if e.Version <= pr.View.Version {
		return
	}
	pr.View.Holders = append(pr.View.Holders, e.UserID)
	pr.View.Remaining--
	pr.View.Version = e.Version
}

func Query(pr *Projector, minVersion int) (SeatsView, bool) {
	return pr.View, pr.View.Version < minVersion
}

func main() {
	pool := NewSeatPool("ws-42", 2)
	proj := NewProjector(2)

	events, _ := pool.Reserve("ada")
	_, stale := Query(proj, events[0].Version)
	fmt.Println("before projection", stale)

	for _, e := range events {
		proj.Apply(e)
	}
	_, stale = Query(proj, events[0].Version)
	fmt.Println("after projection ", stale)

	next, _ := pool.Reserve("grace")
	for _, e := range next {
		proj.Apply(e)
	}
	fmt.Println(proj.View.Holders, proj.View.Remaining)

	if _, err := pool.Reserve("linus"); err != nil {
		fmt.Println("write model rejected", err)
	}
}
```

Rust. Compiled with `rustc -O` and run.

```rust
use std::collections::HashSet;

#[derive(Debug, Clone)]
struct SeatReserved {
    user_id: String,
    version: u64,
}

/// Write model. Owns the invariant, nothing else.
struct SeatPool {
    capacity: usize,
    holders: HashSet<String>,
    version: u64,
}

impl SeatPool {
    fn new(capacity: usize) -> Self {
        Self { capacity, holders: HashSet::new(), version: 0 }
    }

    fn reserve(&mut self, user_id: &str) -> Result<Vec<SeatReserved>, &'static str> {
        if self.holders.contains(user_id) {
            return Ok(vec![]);
        }
        if self.holders.len() >= self.capacity {
            return Err("pool exhausted");
        }
        self.version += 1;
        self.holders.insert(user_id.to_string());
        Ok(vec![SeatReserved { user_id: user_id.to_string(), version: self.version }])
    }
}

/// Read model. Denormalised, versioned, rebuildable from the event stream.
#[derive(Debug)]
struct SeatsView {
    remaining: usize,
    holders: Vec<String>,
    version: u64,
}

struct Projector {
    view: SeatsView,
}

impl Projector {
    fn new(capacity: usize) -> Self {
        Self { view: SeatsView { remaining: capacity, holders: vec![], version: 0 } }
    }

    fn apply(&mut self, e: &SeatReserved) {
        if e.version <= self.view.version {
            return;
        }
        self.view.holders.push(e.user_id.clone());
        self.view.remaining -= 1;
        self.view.version = e.version;
    }

    fn query(&self, min_version: u64) -> (&SeatsView, bool) {
        (&self.view, self.view.version < min_version)
    }
}

fn main() {
    let mut pool = SeatPool::new(2);
    let mut proj = Projector::new(2);

    let events = pool.reserve("ada").unwrap();
    println!("before projection {}", proj.query(events[0].version).1);

    for e in &events {
        proj.apply(e);
    }
    println!("after projection  {}", proj.query(events[0].version).1);

    for e in &pool.reserve("grace").unwrap() {
        proj.apply(e);
    }
    println!("{:?} {}", proj.view.holders, proj.view.remaining);

    match pool.reserve("linus") {
        Err(msg) => println!("write model rejected {}", msg),
        Ok(_) => unreachable!(),
    }
}
```

Java and C# are omitted here only because the pattern's Java and C# forms are
already represented by the framework citations in dimension 9, where Axon and
Marten show the idiomatic shape in production. No Java runtime was available on
the authoring machine to compile a sample, so none is shipped rather than
shipping an unverified one.

## 9. Known production uses

**Axon Framework.** The Axon Framework reference guide states that its purpose is
covering the capabilities the framework provides to help build applications based
on Domain-Driven Design, CQRS, and event sourcing. The framework models commands,
queries, and events as three distinct message types with separate dispatchers and
handlers, and adds subscription queries that continue to deliver updates for as
long as the subscription is active, which is a direct answer to the projection-lag
problem in the UI
([docs.axoniq.io/axon-framework-reference/4.11/](https://docs.axoniq.io/axon-framework-reference/4.11/),
verified 2026-08-02).

**Microsoft eShopOnContainers, ordering microservice.** Microsoft's .NET
microservices reference application documents its ordering microservice as based
on CQRS principles using the same database for both sides, with queries
implemented in Dapper independently of the DDD write model. It is a useful
citation precisely because it is the restrained variant, and because the same
document carries the warning that CQRS and DDD patterns are not top-level
architectures.

**Marten.** The Marten library for .NET on PostgreSQL implements CQRS read models
as projections over an event stream, documents inline projections executed in the
same unit of work as event capture, asynchronous projections executed by a
background process with eventual consistency, and on-demand rebuilds through a
daemon. It also states the distinction between a read model supplied to clients
and the write-side representation.

**Akka Projections.** The Akka Projections library lists Command Query
Responsibility Segregation as a primary use case and provides source providers
for events from Akka Persistence and changes from durable state, with offset
tracking across several backends and both at-least-once and exactly-once
processing modes
([doc.akka.io/libraries/akka-projection/current/index.html](https://doc.akka.io/libraries/akka-projection/current/index.html),
verified 2026-08-02). The offset-tracking and delivery-semantics surface is the
clearest published evidence that projection resumption is a first-class
production concern rather than an afterthought.

**AWS prescriptive guidance.** AWS documents CQRS as a supported data-persistence
pattern for modernisation, naming concrete store combinations including DynamoDB
on the command side streaming through Lambda into Aurora on the query side, and
RDS read replicas serving the query side of an all-relational deployment. The
same page carries the Important callout that the pattern ordinarily results in
eventual consistency between the stores.

## 10. Consequences

### Positive

- **Each side is optimised for its own job.** The write store can stay normalised
  and small. The read store can be denormalised to the shape the screen wants.
  Microsoft lists optimised data schemas as a benefit, with reads using a
  query-optimised schema and writes an update-optimised one.
- **Independent scaling.** Microsoft's benefit list opens with this, noting it
  can reduce lock contention and improve performance under load. In a system with
  a hundred-to-one read-write ratio you can put the write side on a small
  instance and scale the read side sideways.
- **Simpler queries.** With a materialised view in the read store, the
  application avoids complex joins entirely, which Microsoft lists explicitly.
- **Cleaner models on both sides.** The write side stops carrying query concerns
  and the read side stops carrying domain logic. Microsoft frames this as
  separation of concerns producing cleaner, more maintainable models.
- **Security scoping.** Separating reads and writes makes it possible to grant
  write permission only to the entities and operations that need it. Microsoft
  lists security as a benefit for exactly this reason, and dimension 17 takes it
  further.
- **New views are cheap once the machinery exists.** Judgement, but consistently
  observed. The first projection costs a quarter. The eighth costs a day, because
  the transport, the offset store, the rebuild tooling, and the alerting are
  already built.
- **Team autonomy.** Microsoft names separation of development concerns, with one
  team on the write-model business logic and another on the read model and UI.
- **Failure isolation.** Microsoft's "when to use" list includes system
  integration, noting that CQRS isolates failures and prevents a single component
  from affecting the entire system. A read side that keeps serving while the write
  side is down is a real availability gain when the domain permits it.

### Negative

- **Complexity, and Microsoft says so first.** Its considerations list opens by
  stating the core concept is straightforward but the pattern can add
  considerable complexity to the application design, particularly combined with
  event sourcing.
- **Eventual consistency is now a product decision, not an implementation
  detail.** Someone has to answer, per screen, what the user sees inside the lag
  window. Microsoft names both halves. Keeping the read store up to date is
  difficult, and detecting and handling users acting on stale data requires
  careful consideration.
- **Messaging failure modes arrive with the transport.** Microsoft notes that
  when messaging is used the system must account for message failures, duplicates,
  and retries. Every projector must be idempotent, and the samples in dimension 8
  implement that with a version guard for exactly this reason.
- **Code duplication.** Richardson lists code duplication among the drawbacks.
  The same concept now has two representations, and they drift.
- **Tooling stops helping.** Microsoft points out that scaffolding tools such as
  object-relational mappers cannot generate CQRS code from a database schema, so
  custom logic is required to bridge the two models. The productivity of the CRUD
  toolchain is a real thing you are giving up.
- **View generation can be expensive.** Microsoft's event-sourcing combination
  considerations state that generating materialised views can consume considerable
  time and resources, and that calculations over long periods require examining
  all related events, which is why snapshots are recommended.
- **Debugging spans two systems.** Judgement. "The number is wrong" now has at
  least four candidate causes. The command was rejected, the event was lost, the
  projection has a bug, or the projection is behind. Dimension 16 exists to make
  those four distinguishable.
- **Migration and schema change get harder.** Judgement. Changing a field means
  changing the write model, the event, every projection that reads it, and then
  rebuilding the views. A single-model system changes a column.

## 11. Failure modes and misuse

Written as symptom, cause, fix. The symptoms are drawn from practice and are
labelled as engineering judgement, while the underlying mechanics are sourced
where a source exists.

**Symptom.** A user completes an action, the confirmation screen shows the old
value, and support tickets say "it did not save". The value is correct if they
refresh a few seconds later.
**Cause.** Read-your-own-writes was never designed. The client queries the
projection immediately after the command returns and lands inside the lag window.
This is the failure Microsoft describes when it notes that read data might not
show the most recent changes immediately.
**Fix.** Pick one of the four strategies in dimension 8 variant E and apply it
consistently. The version-token approach is the most explicit. Do not "fix" it by
adding a sleep in the client, which converts a correctness bug into a latency bug
that reappears under load.

**Symptom.** Two users book the last seat. Both succeed. The read model shows
minus one available.
**Cause.** The write model made its decision by reading the projection. The
projection is stale by construction, so the invariant was checked against data
that was already wrong.
**Fix.** No decision on the command side may consult the read model. The write
model must load its own state inside the transaction and enforce the rule there.
This is the constraint stated in dimension 5, and it is the one most often
violated because reading the projection is so convenient.

**Symptom.** Projection lag rises steadily over hours, never recovers, and
restarting the projector fixes it until it happens again.
**Cause.** Either the projector cannot keep up with sustained write throughput,
or a single slow projection is blocking a shared pipeline.
**Fix.** Measure per-projection throughput separately. Split hot projections onto
their own consumer. If the projector genuinely cannot keep up, the read model is
doing work that belongs elsewhere, often an aggregation that should be
incremental rather than recomputed.

**Symptom.** One malformed event and the entire read model stops updating. Every
screen goes stale at once.
**Cause.** A poison event with no handling policy. The projector throws, retries,
throws again, and never advances its offset.
**Fix.** A dead-letter path plus an explicit decision per projection about
whether to skip or halt. Halting is sometimes correct, because skipping a
`PaymentCaptured` event silently corrupts a balance. The failure is having no
decision, not picking the wrong one.

**Symptom.** The read model and the write model disagree, permanently, and nobody
can say when they parted ways.
**Cause.** An event was lost between the database commit and the message
publication. This is the dual-write problem, and it is exactly what Microsoft
warns about when it states that message brokers and databases usually cannot be
enlisted in one distributed transaction.
**Fix.** Transactional Outbox or CDC, so the event is durable in the same
transaction as the state change. Add a periodic reconciliation job that compares
aggregate counts against the projection and alerts on drift, because the outbox
protects the publish and does not protect against projector bugs.

**Symptom.** The projection is duplicated because the transport delivered an
event twice, so a counter reads double.
**Cause.** At-least-once delivery with a non-idempotent projection. Microsoft
lists duplicates among the messaging problems the system must handle.
**Fix.** Make every projection idempotent. The version or offset guard in the
code samples is the minimal form. For counters, store the last applied offset with
the view and apply the guard atomically with the mutation.

**Symptom.** A change to a read model requires a two-day outage, or the team
refuses to change read models at all.
**Cause.** No rebuild capability. The source is a queue with no retention, or the
projection writes in place with no versioned view.
**Fix.** Build the blue-green rebuild in dimension 7 before you need it, and
prove it works by rebuilding a real projection in staging. Marten documents
on-demand rebuilds precisely because this is a routine operation, not an
emergency one.

**Symptom.** The whole system is described as "our CQRS architecture", the CRUD
services have command handlers wrapping single field updates, and new engineers
take a month to ship anything.
**Cause.** The pattern was applied system-wide instead of to one bounded context.
Both Fowler and Microsoft warn against this in the same terms, Fowler restricting
it to specific portions of a system and Microsoft stating that forcing the same
pattern everywhere leads to failure.
**Fix.** Retire the pattern where it does not earn its place, following dimension
14's removal path. Keep it where the read-write asymmetry is measurable.

**Symptom.** Command handlers named `UpdateOrderCommand` carrying a full entity
payload, with a projection that copies fields across one to one.
**Cause.** CRUD wearing the pattern's vocabulary. The commands carry no intent,
so the write model has no rules to enforce and the read model has nothing to
denormalise. Microsoft's guidance to model "Book hotel room" rather than "Set
ReservationStatus to Reserved" is aimed at this.
**Fix.** Either name the real business operations, or delete the ceremony and use
CRUD honestly. The ceremony without the intent is pure cost.

**Symptom.** A team adopts CQRS to get an audit trail, then discovers the event
stream is not replayable and the audit is incomplete.
**Cause.** Conflating CQRS with event sourcing. Young's list of what CQRS is not
includes event sourcing explicitly.
**Fix.** If the requirement is audit, build an audit log or adopt event sourcing
deliberately. The read-write split does not produce one as a side effect.

**Symptom.** Read model queries are fast in isolation and slow in production,
with the read store showing high write amplification.
**Cause.** One projection per screen, unbounded, so a single event fans out into
a dozen upserts. Judgement, but common in teams that discovered how cheap the
eighth projection is.
**Fix.** Treat projections as an inventory with an owner and a retirement policy.
An unused projection still costs write throughput on every event.

## 12. Trade-off matrix

Compared against named alternatives across the forces from dimension 3. Scores
are relative within this table and reflect engineering judgement informed by the
cited sources, not measurement.

| Force | CQRS, separate stores | CQRS, one store | Read replicas | Materialized View, same DB | Cache-Aside | Single CRUD model |
|---|---|---|---|---|---|---|
| Read scale headroom | Very high, independent tech | Same as write store | High, same schema | Same as write store | High, per-key only | Low |
| Read shape flexibility | Full, any schema or engine | Good, separate query path | None, identical schema | Good, DB-defined view | None, key-value only | Poor |
| Consistency | Eventual, lag is designed | Strong, one transaction | Eventual, replication lag | Strong or refresh-lag | Eventual, TTL-bound | Strong |
| Read-your-own-writes | Needs explicit strategy | Free | Needs primary routing | Free if synchronous | Needs invalidation | Free |
| Cross-service queries | Yes, the main reason | No | No | No | No | No |
| Write-side model clarity | High | High | Unchanged | Unchanged | Unchanged | Low as domain grows |
| Operational surface | Largest, projector plus outbox | Small | Small, managed by DB | Small | Medium, invalidation bugs | Smallest |
| Cost of the first change | Highest, weeks to a quarter | Low, days | Lowest, configuration | Low | Low | None |
| Cost of the tenth view | Low, machinery exists | Medium, more SQL | Not applicable | Medium, more views | Not applicable | High |
| Rebuild and repair story | Excellent if source replayable | Not needed | Automatic by the engine | Refresh the view | Flush the cache | Not needed |
| Failure isolation from write side | Yes | No | Partial | No | Partial | No |
| Team autonomy | High | Medium | None | None | None | None |

### CQRS against read replicas specifically

This comparison deserves its own paragraphs because it is where most CQRS
adoptions should stop and do not.

A read replica solves read *volume*. PostgreSQL streaming replication ships the
write-ahead log to standby servers that can serve read-only queries, and the
configuration is a server setting rather than an application change
([postgresql.org/docs/17/warm-standby.html](https://www.postgresql.org/docs/17/warm-standby.html),
verified 2026-08-02). AWS lists this as a legitimate way to implement the query
side of CQRS, describing writes going to the primary and reads routed to
replicas.

What a replica does not solve is read *shape*. The replica has the same schema as
the primary, so a query needing six joins still needs six joins. It cannot be a
document store, a search index, or a graph. It cannot pre-join across service
boundaries, because it only carries one database. And it comes with its own
eventual consistency, so it does not even buy back the strong-read property.

The decision reduces to two questions. If the answer to both is no, use replicas.

1. Does the read need a *different shape*, not merely more capacity?
2. Does the read need data from a store the write side does not own?

Judgement, stated as such. The majority of systems reaching for CQRS have a
volume problem and a query-tuning problem, both of which replicas and indexes
address at a fraction of the cost. Fowler's caution that most cases he
encountered were not good ones is consistent with this reading.

### CQRS against a materialized view in the same database

A materialized view is the same idea with the database doing the projection. It
denormalises, it can carry its own indexes, and it refreshes on a schedule or on
demand. Microsoft treats the materialized view as its own pattern and points at
it from the CQRS page as the mechanism for the read store's schema
([learn.microsoft.com/en-us/azure/architecture/patterns/materialized-view](https://learn.microsoft.com/en-us/azure/architecture/patterns/materialized-view),
verified 2026-08-02). The limits are that it lives inside one database, cannot
cross service boundaries, and refreshes at the granularity the engine supports
rather than per event. Reach for it first when both models are in one database.

## 13. Related and incompatible patterns

**Event Sourcing.** The relationship is asymmetric and this is the most
misunderstood pairing in the catalog. Event sourcing effectively requires CQRS,
because an event-sourced store has no current-state representation to query, and
Young's own explanation is that with CQRS the only query the domain needs is
get-by-id, which the event store supports. CQRS does not require event sourcing,
and Young's list of what CQRS is not includes it explicitly. Microsoft treats
them as separate patterns with a section on combining them, and warns that the
combination requires a different design approach that makes a successful
implementation harder. Adopt them independently and deliberately.

**Transactional Outbox.** A dependency, not an option, in the separate-store
variant. Without it the dual-write between database and broker will drop events
and the models will disagree permanently, which is the failure recorded in
dimension 11.

**Change Data Capture.** An alternative synchroniser to the outbox, with the
trade recorded in dimension 8 variant C. It removes the dual write at the cost of
carrying row deltas rather than business intent.

**Materialized View.** Composes directly. Microsoft's CQRS page names the
materialized view as what the read store can hold to avoid complex joins.

**Saga and Process Manager.** Composes. A saga coordinates a multi-step business
process by reacting to events and issuing commands, which is the same event
stream the projections consume. The distinction to hold is that a projection
mutates a view and never issues a command, while a saga issues commands and
should not own a view.

**Database-per-Service.** The pattern that creates the need for CQRS in a
microservice system, per Richardson's framing of cross-service queries. AWS lists
the same trigger, saying to consider CQRS if you implemented database-per-service
and want to join data across services.

**API Composition.** A direct competitor for the cross-service query problem.
Instead of maintaining a joined read model, the query fans out to each service and
joins in memory. Cheaper to build, no consistency lag, worse under load and
unable to sort or paginate across the combined set. Prefer composition first and
move to a read model when the fan-out becomes the bottleneck.

**Cache-Aside.** Frequently confused with CQRS by teams describing a cache as
their read model. A cache is keyed, has no independent schema, and is populated
lazily on miss. A read model is queryable, has its own schema, and is populated
eagerly by projection. If your "read model" cannot answer a query that was never
asked before, it is a cache.

**Command pattern, from the GoF catalog.** Shares the word and almost nothing
else. The GoF Command encapsulates a request as an object to support undo,
queueing, and logging within a process. The CQRS command is a message crossing a
process or model boundary carrying business intent. The overlap is real but
shallow, and treating a CQRS command as an in-process undoable operation produces
a confused design.

**Shared Database.** Actively incompatible in the separate-store variant. If two
services write the same tables, there is no single write model owning the
invariant and no sensible place for the projection to derive from. The pattern
assumes one owner per consistency boundary.

**Backend for Frontend.** Composes well and is often mistaken for CQRS. A BFF
shapes a response per client at request time. A read model shapes and stores the
data ahead of time. They stack, and a BFF can read from several read models.

## 14. Refactoring path in and out

### Introducing the pattern

The order matters, and the point of the sequence is that each step is
independently valuable and independently reversible. A team that stops after step
three has still improved the codebase.

1. **Measure the asymmetry before anything else.** Record the read-write ratio,
   the p99 of the three slowest queries, and how many of them are slow because of
   shape rather than volume. If the ratio is near one to one, or the slow queries
   are fixed by an index, stop. This step exists to prevent the adoption Fowler
   cautions against.
2. **Separate the query path in code, inside the same database.** Stop routing
   reads through the domain model. Write the query directly against the tables,
   return a DTO shaped for the screen, and delete the mapping chain. This is
   Microsoft's foundational variant and the eShopOnContainers approach with
   Dapper. No consistency change, no new infrastructure, immediate reduction in
   the write model's obligations.
3. **Name the commands after business operations.** Replace `UpdateOrder` with the
   real operations. The write model can now shrink to the state each operation's
   invariant needs. Cross reference the refactoring family, because this is
   Replace Method with Method Object applied at the service boundary, followed by
   Extract Class on the aggregate.
4. **Make the write model emit events.** Still no separate store. The aggregate
   returns a list of events alongside its state change, and they are persisted to
   an outbox table in the same transaction. Nothing consumes them yet. This step
   is where the outbox is proven correct while the cost of being wrong is zero.
5. **Add one projection, for one screen, into a separate store.** Choose the
   screen with the worst query and the highest tolerance for staleness. Build the
   projector, the offset store, the lag metric, and the rebuild before adding a
   second projection. Run it in shadow mode, serving from the old path while
   comparing outputs, until the two answers agree over a full business cycle.
6. **Cut read traffic over behind a flag, one screen at a time.** Keep the old
   query path deployable for at least one release. Design the read-your-own-writes
   strategy before the cutover, not after the first support ticket.
7. **Only then consider more projections, or event sourcing.** Both are separate
   decisions with their own justification, and neither is implied by the previous
   six steps.

### Removing the pattern

Removal is a real and under-documented operation. It becomes correct when the
read-write asymmetry that justified the split has gone, when the projection lag
causes more incidents than the query performance saved, or when the bounded
context has shrunk to CRUD.

1. **Prove the write store can serve the read shape.** Build the query against
   the write store and measure it under production-like load. If it cannot, the
   split is still earning its place and removal is premature.
2. **Serve reads from the write store behind a flag, in shadow first.** Compare
   the two answers on live traffic. Discrepancies here are usually projection bugs
   you were shipping without knowing.
3. **Flip read traffic, keep the projector running.** The projector is now
   producing an unused view, which is your rollback.
4. **Delete the projector, then the transport, then the read store.** In that
   order. Deleting the read store first removes the rollback.
5. **Keep or remove the command vocabulary independently.** Intent-carrying
   commands and a small write model are valuable with or without a separate read
   store. Removing CQRS does not mean returning to `UpdateOrder`. This is why
   step 2 of the introduction path is worth doing on its own.

## 15. Testing and verification

This dimension is practice rather than sourced claim, with the exception noted.

**What becomes easier.** The write model becomes the easiest thing in the system
to test. It has no query obligations, no ORM, and no database in the unit test.
The test takes the form of given a history, when a command, then these events or
this rejection. The samples in dimension 8 are written so this is possible,
because `reserve` returns events rather than persisting. Given-when-then over an
aggregate is a pure function test and runs in microseconds.

The projection is equally pure. Given a sequence of events, assert the resulting
view. Because the projector in the samples is idempotent by version guard, the
same test can be run twice over the same events and assert the view is unchanged,
which is the cheapest possible idempotency test and should be in every projection
suite.

**What becomes harder.** Anything spanning the seam. Three things need explicit
coverage that a single-model system gets for free.

*Contract between event and projection.* The write model emits an event, the
projection consumes it, and nothing in the type system connects them once they
cross a serialisation boundary. Test with a shared schema and a round-trip test
per event type, including forward compatibility, so an old projector survives a
new event with an added field.

*Convergence.* The property to assert is that after the transport quiesces, the
view equals the value derived from the full history. This is a property-based
test. Generate a random command sequence, apply it to the write model, feed the
events to the projector in a shuffled and duplicated order, and assert the final
view matches a reference projection over the ordered stream. This single test
catches ordering assumptions, non-idempotent handlers, and missing guards in one
shot.

*Behaviour inside the lag window.* The read-your-own-writes strategy is a
requirement and needs a test that pins it. Write the test so the projector is
deliberately not run, then assert the client-visible contract. Either the query
reports staleness, or the response comes from the write model, or the API returns
a 202 with a poll location. The samples make this testable by returning the
staleness flag as data.

**Test doubles that apply.** An in-memory event bus that can be told to duplicate,
reorder, and drop messages is the highest-value double in a CQRS codebase, because
those three faults are the ones Microsoft names as the messaging problems the
system must handle. A fake clock matters wherever the projection carries
time-derived fields. A stub offset store lets you test resumption from an
arbitrary point without a database.

**Integration level.** Test the outbox relay against a real database, because its
correctness depends on transaction semantics that no fake reproduces. Test the
rebuild in continuous integration on a small fixture stream, so the rebuild path
is exercised on every change rather than during an incident.

## 16. Observability signals

Practice, not sourced claim, except where a source is named.

**The single metric that matters most is projection lag,** and it should be
measured in two units, because they fail differently. Event lag is the count of
events between the head of the stream and the projector's offset. Time lag is the
wall-clock age of the last applied event. Event lag alone lies during a quiet
period, where zero pending events can coexist with a projector that died an hour
ago. Time lag alone lies during a burst. Alert on both.

**Per-projection, never aggregate.** One projection lagging while nine are
current is invisible in an average. Emit lag with the projection name as a label,
and alert per projection, because the tolerable lag for a search index and for an
account balance view are different numbers.

**A healthy instance on a dashboard.** Projection lag flat and low, ideally under
a second at p99 for a user-facing view. Command acceptance rate stable, with
rejections forming a small steady fraction rather than a spike. Outbox depth
oscillating near zero. Dead-letter count at zero. Rebuild age recent enough that
you know the rebuild still works.

**A failing instance.** Lag rising monotonically is the classic. Lag sawtoothing
between zero and a large number means the projector is restarting, so check for
crash loops rather than throughput. Outbox depth growing while projection lag
stays low means the relay is down and you are about to lose visibility entirely.
Dead-letter count above zero at any level is an alert, not a warning, because each
entry is a permanent mismatch until somebody acts.

**Trace across the seam.** The command's trace context must be carried on the
event and picked up by the projector. Without it the trace ends at the command
handler and the interesting half of the latency is invisible. The span to record
is command-accepted to view-updated, which is the number a product owner actually
cares about when they ask how long until the user sees it.

**Log the version on both sides.** Log the version the command wrote and the
version the query served. When a support ticket says the value was wrong, those
two numbers turn a debate into a subtraction.

**Reconciliation as a signal, not only a repair.** Run a periodic job that
recomputes a small number of aggregates from the write store and compares them to
the projection. Emit the drift count as a gauge. A nonzero value is a silent
correctness bug that no lag metric will ever show, because a projector with a
logic error is perfectly current and perfectly wrong.

**Subscription-query systems get an extra signal.** Where the framework pushes
updates to clients, as Axon's subscription queries do, track open subscription
count and update delivery failures. A client holding a subscription that stopped
receiving updates displays stale data indefinitely with no error anywhere.

## 17. Security and privacy implications

Analytical, and labelled as such where it is not sourced.

**The pattern closes one real attack surface.** Microsoft names security among the
benefits, on the grounds that separating reads and writes lets you grant write
permission only to the appropriate domain entities and operations, and notes in
its problem statement that managing security is harder when entities are subject
to both reads and writes. This is a genuine improvement. A read model can be
served by a process with a database role that holds no write grant at all. In the
separate-store variant the read store can be in a different network segment, and a
compromise of the public query API yields no write path.

**It opens a different one.** The read model is a denormalised copy, and copies
are where data-handling obligations get lost. Three concrete consequences.

*Deletion becomes multi-step.* Under GDPR Article 17 a deletion request must
reach every copy. A record deleted from the write store persists in every
projection until the deletion event is projected, and persists in the event stream
forever if the write side is event sourced. The mitigation is crypto-shredding,
storing personal data encrypted with a per-subject key and destroying the key,
which renders every copy including the immutable stream unreadable without
mutating it. This is analysis rather than a sourced claim, but it follows directly
from the append-only property Young describes in the "There is no Delete" section
of the CQRS Documents.

*Denormalisation defeats field-level access control.* If the write model
restricts a salary field by role, and a projection copies it into a view that a
broader audience queries, the restriction is gone. The projection is a
privilege-escalation path that no code review of the write model will catch.
Access control must be re-asserted at the read model, and the safest form is
projecting into separate views per audience rather than one view filtered at query
time.

*The event stream is a durable record of everything.* An event stream carries the
full history of changes, including values that were later corrected. A read model
shows the current state. A stream shows that the address was once a different
one, which may itself be sensitive. Treat the stream's access controls as at
least as strict as the write store's, not as a background implementation detail.

**Commands are a trust boundary and should be validated as one.** Udi Dahan draws
the distinction that validation states a context-independent fact about a command,
so either a command is valid or it is not. That check belongs at the edge, before
the write model runs. Because commands are frequently queued, an injected or
replayed command may execute long after the session that appears to have sent it
ended. Sign or bind commands to the authorising principal at enqueue time and
re-check authorisation at execution time, because the principal's rights may have
been revoked in between.

**Idempotency keys are a security control, not only a correctness one.** A replay
of a captured command message is a real attack against a queued command side. The
same deduplication that protects against at-least-once delivery protects against
deliberate replay, provided the key is bound to something the attacker cannot
freely regenerate.

**Where the pattern is silent.** CQRS says nothing about transport encryption,
authentication, secret management, or tenancy isolation. Those are orthogonal and
inventing a CQRS-specific concern for them would be dishonest. The pattern's real
security footprint is the copies it creates and the write grants it lets you
withhold.

## 18. References

1. Greg Young. *CQRS Documents*. 2010. Self-published collection, cqrsinfo.com.
   https://cqrs.files.wordpress.com/2010/11/cqrs_documents.pdf
   Verified 2026-08-02. Chapter "Command and Query Responsibility Segregation",
   sections "Origins", "The Query Side", "The Command Side". Chapter "CQRS and
   Event Sourcing". Chapter "Events as a Storage Mechanism", section "There is no
   Delete". Source for the CQS lineage, the two-object definition, the
   consistency, storage and scalability asymmetry list, and the event-sourcing
   dependency.
2. Greg Young. "CQRS, Task Based UIs, Event Sourcing agh!". Published 2010-02-16
   at codebetter.com. Archived text at
   https://gist.github.com/meigwilym/025f08208b5640ad26bc410c8a83b10f
   Verified 2026-08-02. Source for the statement that CQRS is not eventual
   consistency, eventing, messaging, separated read and write models, or event
   sourcing.
3. Martin Fowler. "CQRS". martinfowler.com bliki.
   https://martinfowler.com/bliki/CQRS.html
   Verified 2026-08-02. Source for the attribution to Greg Young, the warning
   that the pattern should not be attempted unless the benefit justifies the step,
   the caution that most encountered cases were not good ones, and the constraint
   that it applies to a Bounded Context rather than a whole system.
4. Martin Fowler. "CommandQuerySeparation". martinfowler.com bliki.
   https://martinfowler.com/bliki/CommandQuerySeparation.html
   Verified 2026-08-02. Source for the attribution of CQS to Bertrand Meyer's
   *Object-Oriented Software Construction* and the query and command definitions.
5. Microsoft. "CQRS Pattern". Azure Architecture Center. Page dated 2025-02-20.
   https://learn.microsoft.com/en-us/azure/architecture/patterns/cqrs
   Verified 2026-08-02. Source for the four single-model problems, the two
   implementation approaches, the benefits list, the problems and considerations
   list including eventual consistency and messaging duplicates, the when-to-use
   and might-not-be-suitable lists, and the event-sourcing combination
   considerations including snapshots.
6. Microsoft. "Applying CQRS and CQS approaches in a DDD microservice in
   eShopOnContainers". .NET Microservices Architecture for Containerized .NET
   Applications. Page dated 2021-01-13.
   https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/eshoponcontainers-cqrs-ddd-microservice
   Verified 2026-08-02. Source for the eShopOnContainers production use, the
   simplified same-database approach with Dapper, and the section "CQRS and DDD
   patterns are not top-level architectures".
7. Amazon Web Services. "CQRS pattern". AWS Prescriptive Guidance, Modernization
   Data Persistence.
   https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-data-persistence/cqrs-pattern.html
   Verified 2026-08-02. Source for the store combinations including DynamoDB to
   Aurora and RDS read replicas, the when-to-consider list, and the callout that
   the pattern ordinarily results in eventual consistency between the data stores.
8. Chris Richardson. "Command Query Responsibility Segregation (CQRS)", in the
   microservices pattern catalog at microservices.io.
   https://microservices.io/patterns/data/cqrs.html
   Verified 2026-08-02. Source for the cross-service query problem statement and
   the drawbacks list including replication lag and code duplication.
9. Chris Richardson. "Transactional outbox", in the microservices pattern catalog
   at microservices.io.
   https://microservices.io/patterns/data/transactional-outbox.html
   Verified 2026-08-02. Source for the outbox dependency in dimension 8 variant B.
10. Udi Dahan. "Clarified CQRS". Published 2009-12-09.
    https://udidahan.com/2009/12/09/clarified-cqrs/
    Verified 2026-08-02. Source for the staleness argument, the mapping-layer
    critique, the validation definition, and the acknowledge-then-confirm client
    strategy.
11. AxonIQ. *Axon Framework Reference Guide*, version 4.11.
    https://docs.axoniq.io/axon-framework-reference/4.11/
    Verified 2026-08-02. Source for the Axon production use, the three message
    types, and subscription queries.
12. JasperFx. *Marten documentation*, "Projections".
    https://martendb.io/events/projections/
    Verified 2026-08-02. Source for the Marten production use, inline against
    asynchronous projections, and on-demand rebuilds.
13. Lightbend. *Akka Projections documentation*, current version.
    https://doc.akka.io/libraries/akka-projection/current/index.html
    Verified 2026-08-02. Source for the Akka Projections production use, CQRS as a
    listed use case, offset tracking, and at-least-once against exactly-once
    processing.
14. Microsoft. "Materialized View pattern". Azure Architecture Center.
    https://learn.microsoft.com/en-us/azure/architecture/patterns/materialized-view
    Verified 2026-08-02. Source for the materialized view comparison in
    dimension 12.
15. PostgreSQL Global Development Group. *PostgreSQL 17 Documentation*, chapter
    "Log-Shipping Standby Servers".
    https://www.postgresql.org/docs/17/warm-standby.html
    Verified 2026-08-02. Source for streaming replication behaviour in the read
    replica comparison.
16. Debezium community. *Debezium Documentation*, "Debezium Architecture".
    https://debezium.io/documentation/reference/stable/architecture.html
    Verified 2026-08-02. Source for change data capture as a synchroniser in
    dimension 8 variant C.
17. Microsoft. "Event Sourcing pattern". Azure Architecture Center.
    https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing
    Verified 2026-08-02. Referenced for the separation of Event Sourcing from
    CQRS as distinct patterns.
