---
name: Event-Carried State Transfer
slug: event-carried-state-transfer
family: 05-architectural
category: Architectural
aliases: [Data Change Events, Event-Carried State, ECST]
first_described: "Martin Fowler 2017"
maturity: established
related: [event-notification, event-sourcing, cqrs, materialized-view, saga, publish-subscribe, change-data-capture]
incompatible_with: []
verified: 2026-08-02
---

# Event-Carried State Transfer

## 1. Name, aliases, and lineage

The canonical name is Event-Carried State Transfer, coined and defined by Martin
Fowler in the article "What do you mean by Event-Driven", published on
martinfowler.com on 7 February 2017. Fowler's own words describe it as a
pattern that "shows up when you want to update clients of a system in such a
way that they don't need to contact the source system in order to do further
work"
([Martin Fowler, "What do you mean by Event-Driven", martinfowler.com, 7 February 2017](https://martinfowler.com/articles/201701-event-driven.html),
verified 2026-08-02). The article illustrates the idea with a customer
management system that, on every change to a customer record, publishes an
event containing the full changed fields, so every downstream system that
cares about customer data can keep its own local copy current without ever
calling back into the customer service.

The name did not exist as a fixed term before that article. Practitioners had
been building the mechanism for a decade under other labels, most commonly
Data Change Events inside message-driven integration writing, and the acronym
ECST is a later community shorthand that appears in conference talks and blog
posts discussing Fowler's taxonomy, never in the original text itself. The
pattern is also frequently, and imprecisely, folded into general discussion of
Change Data Capture, a mechanism, not a design pattern in Fowler's sense, that
is one of the most common ways to produce the events this pattern consumes.
Change Data Capture is the plumbing that reads a database transaction log.
Event-Carried State Transfer is the architectural decision about what the
resulting events should contain and who is allowed to depend on the source
system afterward. The two are related but distinct, and conflating them is a
recurring source of confusion in team discussions, addressed further under
Dimension 13.

Fowler places the pattern as one of four things people mean when they say
"event-driven", alongside Event Notification, Event Sourcing, and CQRS. He is
explicit that these are frequently confused with one another and that a single
system commonly uses more than one of them at once. Event-Carried State
Transfer is defined in direct contrast to Event Notification. A notification
event carries the minimum information needed to say that something happened,
often just an identifier, while a state-transfer event carries enough of the
actual data that the receiver never needs to call the source system to find
out what changed.

## 2. Problem and context

A system grows a second consumer that needs data owned by a first system. The
straightforward first move is for the second system to call the first
system's API whenever it needs current data. This works while there is one
consumer and traffic is light. It stops working as more consumers appear.

The concrete failure mode looks like this. A pricing service, a search index,
a recommendation engine, and a fraud-detection service all need to know the
current state of every product in a catalog. Each of them, built the
straightforward way, calls the catalog service's `GET /products/{id}`
endpoint whenever it needs fresh data, and polls on a schedule to catch
changes it was not told about. The catalog service, originally sized to serve
a storefront's read traffic, now serves four to ten times as many requests,
most of them redundant lookups of records that have not changed since the
last poll. Every new consumer that appears makes the catalog service a
larger single point of failure. If it is slow or down, four systems degrade
instead of one, and the catalog team now has to reason about SLAs it never
agreed to when it built the service. This is the exact problem behind
Fowler's original customer management example, and it is the same shape as
what motivated Change Data Capture and log-based integration platforms such
as those built at LinkedIn and the Debezium project, discussed under
Dimension 9.

Event-Carried State Transfer addresses this by inverting the direction of
data flow. Instead of consumers reaching in and pulling state on demand, the
owning system pushes a copy of the changed state out, in an event, at the
moment the change happens. Each consumer keeps its own local, denormalized
copy of exactly the fields it needs, updates that copy when a new event
arrives, and never issues a synchronous call to the source system to answer
an ordinary read. The context in which this pattern belongs is specifically
a system with multiple independent consumers of the same evolving data,
where read availability and read latency for those consumers matters more
than perfect real-time consistency with the source, and where the
organization can tolerate eventual consistency measured in the propagation
delay of the event pipeline, commonly milliseconds to low seconds, but never
zero.

## 3. Forces

**Coupling versus autonomy.** A synchronous request-response integration
couples the consumer's uptime to the provider's uptime at read time. Every
consumer call is a small distributed transaction across a network boundary
that must succeed for the consumer to do its job. Event-carried state
transfer trades this temporal coupling for a looser coupling. The consumer
depends on the event schema and the delivery guarantee of the transport, not
on the provider's availability at the moment of read. This is the dominant
force the pattern exists to relieve, and it is also its steepest cost,
because schema coupling across many independent consumers is genuinely
harder to change than a single service's internal contract.

**Latency and read scalability versus data freshness.** Reads served from a
local materialized copy are as fast as the local store allows, typically
single-digit milliseconds, and scale horizontally with the number of
consumer replicas rather than with the load on a shared source. The price is
that every consumer's copy lags the source by the propagation delay of the
event pipeline. The pattern favors read latency and read scalability over
strict freshness, and states plainly that any system choosing it accepts
eventual consistency as the default, not the exception.

**Consistency guarantees versus payload size and bandwidth.** Carrying full
state in every event means every event is larger than a bare notification,
and the events must be ordered correctly per entity or the receiver can apply
an update out of sequence and end up with a stale field that never gets
corrected. Systems that need this pattern at scale invest specifically in
per-key ordering, a Kafka partition keyed by entity id is the standard
mechanism, and in idempotent, order-tolerant application logic on the
consumer side, discussed further under Dimension 8 and Dimension 11.

**Operability and team topology.** A synchronous API has one observable
failure surface. the API call itself times out or errors, and the caller
knows immediately. An event-carried integration has a distributed failure
surface, a lagging consumer, a poison-pill event that a consumer cannot
apply, a schema change the producer shipped without a compatibility check, or
a broker partition that silently delays delivery. This pattern shifts
operational burden from keeping the read path fast onto keeping the
pipeline observable and the schema disciplined, and it changes team
topology, because the producing team must now think about every downstream
schema consumer before changing a field, in a way a private internal API
never required.

**Storage cost versus query independence.** Every consumer that wants a local
copy pays storage cost proportional to the entities it cares about,
multiplied by the number of consumers. A shared catalog service pays storage
once. This pattern trades one shared, disk-cheap store for many duplicated,
independently-queryable stores, and the trade is favorable exactly when the
independence, availability, and latency gains outweigh the duplicated
storage, which for most services holding megabytes to low gigabytes of
reference data is a favorable trade, and for services holding terabytes of
mutable state is not.

## 4. Applicability and non-applicability

Reach for Event-Carried State Transfer when.

- Two or more independent systems need the same evolving data and each
  benefits from having it locally available for fast, autonomous reads,
  as in Fowler's original customer-record example and the New York Times
  publishing pipeline described under Dimension 9.
- The source system's read traffic from downstream consumers is a scaling
  or availability risk that the team wants to remove, and eventual
  consistency of a few milliseconds to a few seconds is acceptable to the
  business.
- Consumers need to keep working, at reduced but non-zero capability, when
  the source system is degraded or unreachable, because they hold their own
  copy of the data they need for reads.
- The data volume per changed entity is small to moderate, a customer
  record, an order, a product listing, so carrying the full state in the
  event does not create unmanageably large messages.
- The organization already runs, or is willing to run, an ordered,
  at-least-once delivery transport, a log-based broker such as Kafka or an
  equivalent, because the pattern's correctness depends on ordered,
  reliable delivery per entity.

Do not reach for it when.

- There is exactly one consumer of the data and no plan for a second one.
  A direct call, or even a simple cache with a short TTL in front of the
  source's API, solves the same problem with a fraction of the operational
  surface, and adding an event pipeline here is pure premature investment.
- The consumer needs strongly consistent, read-your-writes data at the
  moment of the read, such as a payment authorization check that cannot
  tolerate a stale balance. Event-carried state transfer is fundamentally an
  eventually consistent mechanism. A system that needs linearizable reads
  belongs on a synchronous path or inside the same transactional boundary as
  the source of truth, not behind an asynchronous event feed.
- The changed entity's full state is large, bulk binary content, large
  documents, wide analytical rows, because carrying complete state in every
  event then means shipping that large payload on every change, which
  strains the broker and every consumer's storage. A reference-style event
  that carries only an identifier and a fetch-on-demand link, closer to
  Event Notification, Dimension 13, is usually the better fit there.
- The team cannot commit to schema discipline. Every consumer materializes
  its own copy from the event's shape, so an uncoordinated, breaking schema
  change on the producer side corrupts every consumer's read model
  simultaneously and silently. A team that has not stood up a schema
  registry with compatibility enforcement, or an equivalent versioning
  discipline, will find this pattern actively harmful regardless of how
  attractive the decoupling looks on a whiteboard.
- The domain genuinely needs a full, replayable history of every state
  transition as the system of record, not just the current materialized
  state. That is the job of Event Sourcing, Dimension 13, a related but
  distinct pattern. Treating event-carried state transfer's events as an
  audit log invites subtle correctness bugs, because the pattern is only
  obligated to deliver the current state reliably, not to retain or replay
  every historical event forever.

## 5. Structure

- **Source system (Producer / System of Record).** Owns the authoritative
  data for an entity type. On every state-changing operation, it constructs
  and publishes an event carrying the entity's changed state, in addition to,
  not instead of, persisting the change in its own store.
- **Event.** A message with an identifiable entity key, a version or
  sequence indicator, and a payload containing the entity's current state,
  or at minimum every field a reasonable consumer needs to avoid a callback.
  The event is a value, immutable once published.
- **Event channel / broker.** The transport that delivers events from
  producer to consumers, in order per entity key, at least once. A
  log-based broker, Kafka, Pulsar, or a cloud equivalent such as AWS
  Kinesis or Cloudflare Queues, is the dominant implementation choice
  because it provides durable, replayable, per-key-ordered delivery, but
  the structural role is transport, not any specific product.
- **Consumer(s).** Independent systems, each owning its own local
  materialized store shaped for its own query needs. Each consumer applies
  incoming events to update its local copy and answers its own reads
  entirely from that local copy, without calling the source system.
- **Materialized read model (per consumer).** The local, denormalized store
  a consumer maintains from the event stream. It is a projection, not a
  transactional record of truth. The source system remains the system of
  record, and the read model can always, in principle, be rebuilt by
  replaying the event history from the beginning if the transport retains
  it.
- **Schema contract.** The shared, versioned definition of what an event's
  payload looks like, which every producer and every consumer of that event
  type depends on. This is a structural participant in its own right because
  its evolution rules, see Dimension 8 and Dimension 11, are what keeps the
  whole structure from collapsing under change.

## 6. ASCII structure diagram

```
                         +------------------------+
                         |   Source System        |
                         |   (System of Record)    |
                         |                          |
                         |  own datastore  <---+    |
                         |        |             |    |
                         |    state change      |    |
                         |        v             |    |
                         |  event constructor   |    |
                         +----------|-----------+    |
                                    |                 |
                                    v                 |
                         +------------------------+   |
                         |     Event Channel       |   |
                         |  (ordered per entity     |   |
                         |   key, durable, at-      |   |
                         |   least-once delivery)   |   |
                         +--+----------+----------+-+
                            |          |          |
              (fan out, one event, many independent readers)
                            |          |          |
                v           v          v           v
      +-------------+ +-------------+ +-------------+
      | Consumer A   | | Consumer B   | | Consumer C   |
      | own store    | | own store    | | own store    |
      | (search idx) | | (cache/read  | | (fraud check |
      |              | |  model)      | |  model)      |
      +-------------+ +-------------+ +-------------+
      Consumer reads never call the Source System.
      Each consumer answers reads from its own local copy.
```

## 7. Dynamics

```
Producer                Broker                 Consumer A          Consumer B
   |                       |                       |                   |
   | 1. write to own store |                       |                   |
   |---------------------->|                       |                   |
   |                       |                       |                   |
   | 2. publish event      |                       |                   |
   |  (key=entity#42,      |                       |                   |
   |   v=7, full state)    |                       |                   |
   |---------------------->|                       |                   |
   |                       | 3a. deliver, in order  |                   |
   |                       |     for key=entity#42  |                   |
   |                       |---------------------->|                   |
   |                       | 3b. deliver, in order  |                   |
   |                       |     for key=entity#42                      |
   |                       |------------------------------------------->|
   |                       |                       |                   |
   |                       |                       | 4a. apply to local |
   |                       |                       |     read model     |
   |                       |                       |     (idempotent,   |
   |                       |                       |      version-gated)|
   |                       |                       |                   |
   |                       |                       |                   | 4b. apply to
   |                       |                       |                   |     local read
   |                       |                       |                   |     model
   |                       |                       |                   |
   | ...time passes, some later client asks Consumer A to read entity#42
   |                       |                       |                   |
   |         Consumer A answers entirely from its own local store.
   |         No call back to Producer happens on this read path.
```

The two properties that make the dynamics correct rather than merely
convenient are per-key ordering, event 3a for a given entity key must arrive
at each consumer in the same relative order the producer emitted them, and
idempotent, version-gated application at step 4, a consumer that reapplies an
already-seen or out-of-order event must not corrupt its local state.
Delivery is normally at-least-once, so duplicate delivery of the same event
is an expected, not exceptional, condition the consumer's apply logic must
handle by comparing the incoming version against the version already stored
and discarding anything not strictly newer.

## 8. Implementation variants

**Full-state event (delta-free).** Every event carries the complete current
state of the entity, regardless of which fields changed. This is the
simplest consumer logic, replace the whole local record on receipt, and the
easiest to reason about for correctness, at the cost of larger message size
and more bandwidth for entities that change frequently but only in small
ways. This is the shape Fowler's original article describes.

**Delta event with periodic full snapshot.** Events carry only the fields
that changed, reducing message size, and the producer periodically emits a
full snapshot event, or the transport retains a compacted log with the
latest full state per key, as Kafka's log compaction does, so a consumer
that missed history, or that is bootstrapping fresh, can catch up without
replaying every incremental delta from the beginning of time. This variant
trades simplicity for bandwidth efficiency and is common where entities
change at high frequency, order status transitions, inventory counters.

**Change Data Capture-derived events.** Rather than the source application
explicitly constructing and publishing an event in its own code, a CDC tool,
Debezium is the dominant open-source example, tails the source database's
transaction log and emits an event automatically for every committed row
change, with a structured payload containing the before and after row
images. This variant decouples event production from the application code
entirely, meaning the application does not need to remember to publish, but
it also means the event schema is derived from the database schema rather
than designed as a public contract, which is a frequently underestimated
source of coupling problems discussed under Dimension 11.

**Outbox-pattern event publication.** To avoid the classic dual-write
problem, where a service commits a database write and then crashes before
publishing the corresponding event, or the reverse order, the producer
writes both the state change and a row representing the pending event into
the same local database transaction, and a separate relay process, which may
itself be a CDC connector reading the outbox table, reliably publishes the
event afterward. This variant is the standard, correctness-preserving way to
implement the pattern's producer side when the producer already owns a
transactional database, and it is frequently paired with Change
Data Capture as the relay mechanism.

**Compacted-topic materialization (Kafka Streams KTable style).** The
consumer treats the event stream as a changelog and builds a local table
keyed by entity id directly from the stream, using the transport's own log
compaction to retain only the latest event per key. This is less a separate
implementation of the pattern than a specific, well-supported way to build
the consumer-side materialized read model described under Dimension 5, and
it is the mechanism behind Kafka Streams' `KTable` abstraction.

## 9. Known production uses

**The New York Times, "Publishing with Apache Kafka at The New York Times".**
The Times rebuilt its content publishing pipeline around a Kafka-backed log
they call the Monolog. Every system that creates or edits content writes to
the log, and a "denormalized log" assembles complete, fully-formed content
bundles so that downstream consumers, including their Elasticsearch-backed
search index, "can just pick this message off the log, reorganize the assets
into the desired shape, and push to the index" without calling back to the
originating content systems. The article contrasts this directly with their
earlier API-based architecture, in which "every system that needed access to
content had to know all these different APIs and their idiosyncrasies", the
exact synchronous-coupling problem this pattern targets
([Boerge Svingen, "Publishing with Apache Kafka at The New York Times", Confluent blog, 6 September 2017](https://www.confluent.io/blog/publishing-apache-kafka-new-york-times/),
verified 2026-08-02).

**LinkedIn Databus.** Databus is a change-data-capture pipeline LinkedIn built
and open-sourced to propagate database changes to downstream consumers at low
latency. Its relay component "fetches committed changes from the source
database and stores the events in a high performance log store", and it
"delivers change events grouped in transactions, in source commit order" so
that consumers "pull the change stream from the Relay or Bootstrap and
process the change events" rather than querying the source database
directly, with a separate Bootstrap service available for consumers that need
a full initial state snapshot before following the incremental stream
([LinkedIn Engineering, "Open-sourcing Databus, LinkedIn's low latency change data capture system", engineering.linkedin.com, 26 February 2013](https://engineering.linkedin.com/data-replication/open-sourcing-databus-linkedins-low-latency-change-data-capture-system),
verified 2026-08-02).

**Debezium.** Debezium is an open-source change-data-capture platform, built
on Kafka Connect, that "reads database transaction logs directly and
produces change events to Kafka topics", capturing inserts, updates, and
deletes with complete before-and-after row images so that "downstream
systems consume structured change events from Kafka topics" instead of
querying the source database
([Factor House, "The Complete Guide to Kafka Change Data Capture (CDC)", factorhouse.io, 8 May 2026](https://factorhouse.io/articles/kafka-cdc-change-data-capture/),
verified 2026-08-02). Debezium is one of the most widely adopted mechanisms
for producing the full-state events this pattern requires, and it underlies
the CDC-derived implementation variant described in Dimension 8.

## 10. Consequences

Positive.

- Consumers get low-latency, highly available reads served entirely from
  local storage, with no request-time dependency on the source system's
  uptime or performance.
- The source system is protected from an unbounded number of downstream
  read-heavy consumers, because each new consumer subscribes to the same
  event stream rather than adding load to a shared query endpoint.
- Consumers can shape their local store however best suits their own access
  patterns, a search index, a key-value cache, a graph, a columnar analytics
  table, independent of how the producer models the data internally, which
  gives each team a real architectural choice a shared synchronous API
  rarely allows.
- A consumer that goes offline can catch up by replaying the event stream
  from where it left off, given a retaining transport such as Kafka, rather
  than needing the source system to expose a bulk backfill API.
- The overall system tolerates partial failure better. A slow or
  unavailable source system degrades event freshness for consumers, not
  consumer read availability itself, because consumers keep serving from
  their last known-good local copy.

Negative.

- Every consumer accepts eventual consistency, and reasoning about how
  stale a read can be becomes a real, ongoing operational concern rather
  than a theoretical one, especially under broker backpressure or a slow
  consumer.
- The event schema becomes a long-lived, cross-team public contract the
  moment a second consumer exists, and every field the producer wants to
  rename, remove, or reshape now requires coordinated, backward-compatible
  evolution across every subscriber, which is materially harder than
  changing a private internal API.
- Storage cost multiplies with the number of consumers, each holding its own
  copy of the data it cares about, which for high-cardinality or
  high-volume entities can become a real budget line rather than a rounding
  error.
- Debugging becomes distributed. A wrong read in Consumer A might trace back
  to a bug in the producer's event construction, a schema mismatch, a
  broker-level delivery delay, or a bug in Consumer A's own apply logic, and
  finding which one requires end-to-end tracing across a boundary that a
  synchronous call stack would have made visible in one trace.
- The producer takes on new responsibility it did not have before. It must
  guarantee that every committed state change is eventually published as an
  event, exactly the dual-write problem the outbox pattern, Dimension 8,
  exists to solve, and a producer that skips this discipline will silently
  desynchronize its consumers over time.

## 11. Failure modes and misuse

**The dual-write gap.** Symptom, consumers are missing updates that
definitely happened in the source system, and the gap grows over time or
appears correlated with the producer's deploys or restarts. Cause, the
producer writes to its own database and separately calls the message broker
in application code, and the two operations are not atomic. A crash,
timeout, or unhandled exception between the two leaves the database updated
but the event unpublished, or, less commonly, the event published for a
transaction that later rolls back. Fix, adopt the transactional outbox
pattern, writing the pending event into the same database transaction as the
state change, and use a separate, reliable relay, frequently a CDC connector
reading the outbox table itself, to publish it, so publication is derived
from a committed fact rather than a second, independent side effect.

**Schema drift breaking a downstream consumer silently.** Symptom, one
consumer's read model quietly stops updating, or starts throwing
deserialization errors, some time after an apparently unrelated deploy on
the producer side. Cause, the producer changed a field's type, renamed a
field, or removed a field the consumer's apply logic depended on, without
checking who else consumes that event type, because nothing in a
point-to-point synchronous world trained the team to think about
subscribers they cannot see. Fix, put a schema registry or an equivalent
compatibility gate in front of every event topic that enforces backward,
and where feasible forward, compatibility at publish time, so an
incompatible change fails at the producer's CI pipeline instead of at an
unrelated consumer's runtime months later.

**Out-of-order application corrupting the read model.** Symptom, a
consumer's local record for a given entity intermittently reverts to an
older value, then jumps forward again, with no corresponding change on the
producer side. This is often first noticed as flaky test failures or a
customer-reported stale field that self-corrects on the next update. Cause,
events for the same entity key were partitioned or delivered without a
strict per-key ordering guarantee, a common mistake is partitioning by a
random or round-robin key instead of the entity id, so a newer event and an
older event race and the consumer applies whichever one physically arrives
last, not whichever is logically latest. Fix, partition and route by the
entity key so all events for one entity are strictly ordered on one
partition, and make the consumer's apply logic version-gated, compare an
included version or timestamp before overwriting, discard anything not
strictly newer, so even an occasional reordering at the infrastructure level
cannot silently corrupt state.

**Treating the event stream as a durable system of record.** Symptom, a team
discovers, usually during an incident, that it cannot answer what an
entity's state was a month ago, because the event topic's retention window
already expired, even though the team believed the events were their audit
trail. Cause, confusing event-carried state transfer, which only promises
current-state propagation and is free to expire old events once every
consumer has caught up, with Event Sourcing, which is specifically designed
to retain the full event history as the system of record and to support
replay from the beginning of time. Fix, if a durable, replayable audit trail
is actually required, adopt Event Sourcing deliberately for that entity and
size the retention and storage accordingly, rather than assuming a
state-transfer topic is doing that job by accident.

**Payload bloat from carrying unbounded or unrelated data.** Symptom, broker
throughput or storage cost grows out of proportion to the actual rate of
meaningful business change, and consumers start falling behind during peak
load. Cause, the event payload grew to include large embedded fields, binary
blobs, deeply nested unrelated aggregates, full object graphs, because it
was easier to add a field to an existing well-understood event than to
design a second event type. Fix, keep the event payload scoped to the
fields a reasonable consumer actually needs to avoid a callback, reference
large or rarely-needed content by identifier or URL for on-demand fetch
instead of inlining it, and treat a growing event payload as a design smell
worth a review, not a free addition.

## 12. Trade-off matrix

| Force | Event-Carried State Transfer | Event Notification | Synchronous request-response | Event Sourcing |
|---|---|---|---|---|
| Consumer read latency | Very low, served from local copy | Not applicable alone, requires a follow-up call | Bound by source system's live latency | Low if read model is precomputed, otherwise requires replay |
| Coupling to source uptime | None at read time, only at ingest time | Loose for the notification itself, but the follow-up call reintroduces tight coupling | Tight, every read depends on source availability | None at read time |
| Data freshness | Eventually consistent, lag equals pipeline delay | Depends entirely on the follow-up call's timing | Strongly consistent as of the call | Eventually consistent for projections, strongly consistent for the event log itself |
| Payload size per message | Larger, carries meaningful state | Minimal, an id and a type | Request-scoped, not applicable | Varies, one event per state transition, not one per full snapshot |
| Storage cost | Multiplied by number of consumers | Low, no state is retained by the pattern itself | Single shared store | Full history retained, potentially large, plus per-consumer projections |
| History and audit | Not guaranteed, depends on transport retention | Not provided | Not provided | Core guarantee, full replayable history |
| Schema coupling risk | High, event schema is a long-lived public contract | Low, minimal payload shape | Low, API contract is easier to version privately | High, event schema plus every projection's logic |
| Best suited for | Multiple independent consumers needing fast, autonomous reads | Triggering a workflow step without transferring data | Read-your-writes, transactional correctness needs | Domains needing full auditability and time-travel |

## 13. Related and incompatible patterns

**Event Notification.** The sibling pattern Fowler defines alongside this
one in the same article. Event Notification carries the minimum information
needed to say something happened, typically an identifier and a type, and
expects an interested consumer to call back to the source system if it needs
detail. Event-Carried State Transfer is the deliberate choice to carry
enough data in the event itself that the callback is never needed. Many
real systems mix the two, a lightweight notification for workflow triggers
paired with a fuller state-transfer event for consumers building local read
models, and a team benefits from being explicit about which event type is
which, because conflating them leads to either bloated notification events
or under-provisioned state-transfer ones.

**Event Sourcing.** Frequently confused with this pattern because both
involve publishing events, but they answer different questions. Event
Sourcing makes the sequence of events the authoritative system of record for
an entity, with current state derived by replaying history. Event-Carried
State Transfer makes no such claim. The source system's own store remains
the system of record, and the events are a mechanism for distributing
current state, not a durable historical ledger. A system can use Event
Sourcing internally and expose Event-Carried State Transfer events
externally as a projection of that sourced state, which is a common and
sound combination, but treating the external state-transfer stream as if it
had Event Sourcing's replay-from-genesis guarantee is the misuse described
under Dimension 11.

**CQRS (Command Query Responsibility Segregation).** A natural structural
partner. CQRS separates the write model from the read model within a single
bounded context. Event-Carried State Transfer is one of the standard
mechanisms for propagating the write side's changes out to build the read
side's materialized views, whether those views live inside the same service
or, more commonly in a distributed system, inside separate downstream
consumer services entirely.

**Change Data Capture.** A mechanism, not a design pattern in Fowler's
sense, that is one of the most common ways to produce state-transfer events
without changing application code, by tailing a database's transaction log.
CDC-derived events are the implementation variant described in Dimension 8,
and tools such as Debezium, Dimension 9, exist specifically to bridge a
database's internal change stream into this pattern's event channel.

**Transactional Outbox.** A companion pattern that solves this pattern's
dual-write correctness problem, Dimension 11, by writing the pending event
into the same local transaction as the state change, then relaying it
separately. A production-grade implementation of this pattern's producer
side very commonly includes the Outbox pattern as a load-bearing component,
not an optional extra.

**Saga.** A pattern for coordinating a multi-step, multi-service business
transaction using a sequence of local transactions and compensating actions.
Sagas frequently use Event Notification, and occasionally state-transfer
events, as the trigger mechanism between steps, but a saga is orchestrating
a workflow across services, a fundamentally different concern from this
pattern's job of keeping independent read models current.

**Publish-Subscribe.** The underlying messaging pattern this architecture is
built on top of. Publish-Subscribe describes the mechanics of fan-out
delivery from one producer to many independent subscribers. Event-Carried
State Transfer is a specific policy decision about what to put in the
message and why, layered on top of that general mechanism.

No pattern in this list is structurally incompatible with Event-Carried
State Transfer. The genuine conflicts are conceptual rather than structural,
using this pattern's events as if they were Event Sourcing's durable log, or
treating its eventual consistency as if it offered Synchronous
request-response's strong consistency, and both of those are misuses rather
than pattern incompatibilities, and both are covered in Dimension 11.

## 14. Refactoring path in and out

Introducing the pattern into a system that currently exposes only a
synchronous read API.

1. Identify the concrete pain, enumerate the current callers of the source
   system's read endpoints and confirm there are genuinely multiple
   independent consumers, or a credible near-term plan for more than one.
   If there is exactly one consumer today with no second one planned soon,
   stop here. This refactor is not yet earning its cost, Dimension 4.
2. Design the event schema as a first-class, versioned public contract,
   scoped to the fields a reasonable consumer needs, before writing any
   publishing code. Put it behind a schema registry or an equivalent
   compatibility check from day one, not as an afterthought once a second
   consumer exists.
3. Add event publication to the producer using the transactional outbox
   pattern, write the event payload into an outbox table in the same
   database transaction as the state change, and stand up a relay, a
   dedicated worker, or a CDC connector reading the outbox table, to
   publish reliably from that table onto the chosen event channel.
4. Stand up the first consumer's materialized read model, keyed by the
   entity id, applying incoming events with version-gated,
   idempotent apply logic so duplicate or replayed delivery cannot corrupt
   it. Backfill the consumer's initial state either by replaying retained
   history on the topic or by a one-time bulk export from the source
   system, then switch the consumer to live event application going
   forward.
5. Redirect the consumer's reads from the source system's API to its own
   local read model, and only then, once verified correct under real
   traffic, decommission or scale down the corresponding source-system
   endpoint capacity that existed solely to serve that consumer.
6. Repeat the last two steps for each additional consumer, each with its
   own independently shaped local store, without changing the producer or
   the event schema for each new subscriber.

Removing the pattern from a system where it has stopped earning its place,
most commonly because the number of consumers has shrunk back to one, or the
freshness requirement tightened to the point that eventual consistency is no
longer acceptable.

1. Confirm the actual current consumer count and freshness requirement. Do
   not remove the pattern on the assumption that it is no longer needed
   without checking who still depends on the event stream.
2. For the specific reads that now need strong consistency, add a
   synchronous path back to the source system for those reads only, rather
   than dismantling the whole event pipeline, since other consumers may
   still legitimately depend on it.
3. If truly no consumer remains, deprecate the event topic on a published
   timeline, stop new publication once every subscriber has migrated off,
   and retire the outbox relay and schema registry entries for that event
   type last, after confirming zero remaining consumer lag on the topic.

## 15. Testing and verification

Testing an event-carried state transfer integration splits cleanly into
producer-side and consumer-side concerns, plus a contract layer between
them.

On the producer side, unit tests verify that a given state change produces
an event with the correct payload shape and the correct entity key, without
touching a real broker. The event construction logic is a pure function of
the state change and should be tested as one. Integration tests, run
against a real or embedded broker, Kafka has a well-supported embedded
test-cluster mode, a simple in-memory channel suffices for less mature
transports, verify that a committed database transaction reliably produces
exactly one corresponding published event, specifically exercising the
dual-write failure mode from Dimension 11 by simulating a crash between the
database commit and the relay's publish step and confirming the outbox
mechanism recovers correctly on restart.

On the consumer side, unit tests verify the apply function. Given an
existing local record and an incoming event, does the resulting record match
expectations, including the version-gating logic that must discard an
event whose version is not strictly newer than what is already stored. This
is the single highest-value test in the whole integration, because it is
where the out-of-order-corruption failure mode from Dimension 11 is
actually caught before it reaches production. A deliberate test that feeds
events out of order and asserts the local record still converges to the
correct final state is worth writing explicitly, not left to chance.

Schema compatibility is tested independently of both producer and consumer
logic, as a contract test that runs in CI against the schema registry, or
an equivalent compatibility checker, whenever either side proposes a change
to the event schema, so an incompatible change is caught at review time
rather than discovered by a downstream team's on-call engineer.

End-to-end verification, run in a staging environment against a real
transport, confirms the full pipeline. A state change on the producer is
observably reflected in a consumer's local read model within an expected
latency bound, and this test doubles as the mechanism for establishing and
monitoring the freshness SLA discussed under Dimension 16.

## 16. Observability signals

A healthy instance of this pattern shows steady, low, and bounded consumer
lag, the difference between the offset, or timestamp, of the latest event
published by the producer and the offset each consumer has applied, tracked
per consumer, staying within a known and alerted-on threshold rather than
growing unboundedly. This is the single most important metric, because it is
the direct, quantitative measure of the eventual-consistency window every
consumer's reads are subject to at any given moment.

Beyond consumer lag, a well-instrumented deployment tracks the rate of
events published per entity type, watched for sudden drops that would
indicate the dual-write gap from Dimension 11. It tracks the rate of events
a consumer fails to apply, deserialization errors, schema mismatches, or
application-logic exceptions, which should be near zero in steady state
and alerted on immediately when it is not, since a rising error rate here is
the earliest observable sign of schema drift. It tracks the age of the
oldest unprocessed item in any dead-letter or retry queue a consumer
maintains for events it could not apply, and, on the producer side, the
delay between a database transaction committing and the corresponding
outbox row being relayed, which surfaces relay backlog before it becomes
visible as consumer lag.

Distributed tracing that propagates a correlation identifier from the
originating state change, through the outbox row, through the broker
message, into each consumer's apply operation, is what turns a debugging
session for a stale-data report in Consumer A from a multi-team
investigation into a single trace lookup, and is worth the instrumentation
investment specifically because this pattern otherwise fragments the
causal chain across process and team boundaries that a synchronous call
stack would have kept together automatically.

## 17. Security and privacy implications

Every consumer of a state-transfer event receives a durable, locally-stored
copy of the data in the event, which means the event's payload is, in
effect, replicated to every subscriber's storage and access-control regime,
not just the source system's. A field that would never be exposed through a
carefully access-controlled API endpoint can leak broadly if it is
carelessly included in a state-transfer event that a wide set of internal
services subscribe to, because the event, once published, is no longer
protected by whatever authorization check gated the original API. Producers
publishing personal or otherwise sensitive data through this pattern need
to apply the same data-minimization discipline to the event schema that
they would apply to any external API response, deliberately choosing which
fields are necessary for consumers and omitting fields that are not, rather
than defaulting to a full internal object dump because it was convenient.

Broker-level access control matters accordingly. Topic-level authorization,
who may produce to and who may subscribe to a given event topic, becomes
the primary access-control boundary for the data those events carry, and it
needs the same rigor as an API's authentication and authorization layer,
including periodic review of which services actually still consume a given
topic, since a decommissioned consumer that retains subscription access is
a lingering, easily-overlooked exposure.

Retention and deletion obligations, such as those arising from data-subject
erasure requests under privacy regulation, are harder to satisfy in this
pattern than in a synchronous API, because a piece of personal data that has
already been distributed via events may now exist in every consumer's
locally materialized store, not just the source system. A design that needs
to support enforceable deletion should publish an explicit tombstone or
deletion event that every consumer's apply logic is contractually required
to honor by removing the corresponding local record, and should track which
consumers have acknowledged the tombstone, rather than assuming deleting the
record at the source is sufficient once the data has already propagated
outward.

## 18. References

- Martin Fowler, "What do you mean by Event-Driven", martinfowler.com,
  published 7 February 2017. https://martinfowler.com/articles/201701-event-driven.html.
  Verified 2026-08-02. Primary source for the pattern's name, definition, and
  its contrast with Event Notification, Event Sourcing, and CQRS.
- Boerge Svingen, "Publishing with Apache Kafka at The New York Times",
  Confluent blog, 6 September 2017. https://www.confluent.io/blog/publishing-apache-kafka-new-york-times/.
  Verified 2026-08-02. Source for the New York Times production use.
- LinkedIn Engineering, "Open-sourcing Databus, LinkedIn's low latency change
  data capture system", engineering.linkedin.com, 26 February 2013.
  https://engineering.linkedin.com/data-replication/open-sourcing-databus-linkedins-low-latency-change-data-capture-system.
  Verified 2026-08-02. Source for the LinkedIn Databus production use.
- Factor House, "The Complete Guide to Kafka Change Data Capture (CDC)",
  factorhouse.io, 8 May 2026. https://factorhouse.io/articles/kafka-cdc-change-data-capture/.
  Verified 2026-08-02. Source for the Debezium production use and the
  Change Data Capture implementation variant.

## Code examples

The three examples below model the same scenario. An order service, the
producer, publishes a full-state event whenever an order changes, and an
inventory-facing consumer maintains its own local, materialized copy of
order state without ever calling back to the order service, applying events
idempotently by discarding anything not strictly newer than what it already
holds.

### TypeScript

```typescript
type OrderEvent = {
  entityId: string;
  version: number;
  status: "placed" | "paid" | "shipped";
  total: number;
};

class OrderReadModel {
  private store = new Map<string, OrderEvent>();

  apply(event: OrderEvent): void {
    const current = this.store.get(event.entityId);
    if (current && current.version >= event.version) {
      return;
    }
    this.store.set(event.entityId, event);
  }

  read(entityId: string): OrderEvent | undefined {
    return this.store.get(entityId);
  }
}

function publish(bus: OrderReadModel[], event: OrderEvent): void {
  for (const consumer of bus) {
    consumer.apply(event);
  }
}

const consumerA = new OrderReadModel();
const consumerB = new OrderReadModel();

publish([consumerA, consumerB], {
  entityId: "order-42",
  version: 1,
  status: "placed",
  total: 59.0,
});
publish([consumerA, consumerB], {
  entityId: "order-42",
  version: 2,
  status: "paid",
  total: 59.0,
});
publish([consumerA, consumerB], {
  entityId: "order-42",
  version: 1,
  status: "placed",
  total: 59.0,
});

console.log(consumerA.read("order-42"));
console.log(consumerB.read("order-42"));
```

### Python

```python
from dataclasses import dataclass


@dataclass
class OrderEvent:
    entity_id: str
    version: int
    status: str
    total: float


class OrderReadModel:
    def __init__(self):
        self._store: dict[str, OrderEvent] = {}

    def apply(self, event: OrderEvent) -> None:
        current = self._store.get(event.entity_id)
        if current is not None and current.version >= event.version:
            return
        self._store[event.entity_id] = event

    def read(self, entity_id: str) -> OrderEvent | None:
        return self._store.get(entity_id)


def publish(consumers: list[OrderReadModel], event: OrderEvent) -> None:
    for consumer in consumers:
        consumer.apply(event)


if __name__ == "__main__":
    consumer_a = OrderReadModel()
    consumer_b = OrderReadModel()

    publish([consumer_a, consumer_b],
            OrderEvent("order-42", 1, "placed", 59.0))
    publish([consumer_a, consumer_b],
            OrderEvent("order-42", 2, "paid", 59.0))
    publish([consumer_a, consumer_b],
            OrderEvent("order-42", 1, "placed", 59.0))

    print(consumer_a.read("order-42"))
    print(consumer_b.read("order-42"))
```

### Go

```go
package main

import "fmt"

type OrderEvent struct {
	EntityID string
	Version  int
	Status   string
	Total    float64
}

type OrderReadModel struct {
	store map[string]OrderEvent
}

func NewOrderReadModel() *OrderReadModel {
	return &OrderReadModel{store: make(map[string]OrderEvent)}
}

func (m *OrderReadModel) Apply(event OrderEvent) {
	current, ok := m.store[event.EntityID]
	if ok && current.Version >= event.Version {
		return
	}
	m.store[event.EntityID] = event
}

func (m *OrderReadModel) Read(entityID string) (OrderEvent, bool) {
	event, ok := m.store[entityID]
	return event, ok
}

func publish(consumers []*OrderReadModel, event OrderEvent) {
	for _, c := range consumers {
		c.Apply(event)
	}
}

func main() {
	consumerA := NewOrderReadModel()
	consumerB := NewOrderReadModel()
	consumers := []*OrderReadModel{consumerA, consumerB}

	publish(consumers, OrderEvent{"order-42", 1, "placed", 59.0})
	publish(consumers, OrderEvent{"order-42", 2, "paid", 59.0})
	publish(consumers, OrderEvent{"order-42", 1, "placed", 59.0})

	a, _ := consumerA.Read("order-42")
	b, _ := consumerB.Read("order-42")
	fmt.Println(a)
	fmt.Println(b)
}
```

All three samples were run locally. The TypeScript sample was compiled with
`npx tsc` and executed with `node`, the Python sample was executed with
`python3`, and the Go sample was executed with `go run`. Each prints the
order in its `paid`, version 2 state for both consumers, confirming the
version-gated apply logic correctly ignored the later, out-of-order
redelivery of the version 1 event. Java, Rust, C#, and Kotlin samples were
not written. The pattern's structural idea, a keyed, version-gated apply of
a full-state message, is language-agnostic and does not require a fourth or
fifth language to demonstrate, and the three languages above cover a
dynamically-typed style, a statically-typed garbage-collected style, and a
statically-typed server-oriented style.
