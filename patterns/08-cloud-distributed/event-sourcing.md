---
name: Event Sourcing
slug: event-sourcing
family: 08-cloud-distributed
category: Data and Persistence
aliases: [Event Log as System of Record, Event Store, Append-Only State]
first_described: "Fowler 2005, Young 2010"
maturity: established
related: [cqrs, saga, outbox, materialized-view, snapshot, memento, command]
incompatible_with: []
verified: 2026-08-02
---

# Event Sourcing

## 1. Name, aliases, and lineage

The canonical name is Event Sourcing. Martin Fowler published the entry under
that name on 12 December 2005 in his enterprise application architecture
patterns collection, stating the intent as capturing all changes to application
state as a sequence of events
([martinfowler.com/eaaDev/EventSourcing.html](https://martinfowler.com/eaaDev/EventSourcing.html),
verified 2026-08-02). Fowler notes on the page that the writeup remains in draft
form, which matters for lineage. The pattern was named there but its full
working shape was worked out afterwards by practitioners.

The second foundational text is Greg Young's *CQRS Documents*, self-published
November 2010, which contains the sections "Events as a Mechanism for Storage",
"There is no Delete", "Rolling Snapshots" and "Building an Event Storage"
([cqrs.wordpress.com/wp-content/uploads/2010/11/cqrs_documents.pdf](https://cqrs.wordpress.com/wp-content/uploads/2010/11/cqrs_documents.pdf),
verified 2026-08-02). Young defines a domain event as something that has
happened in the past and requires event names to be past-tense verbs, giving
`CustomerRelocated`, `CargoShipped` and `InventoryLossageRecorded` as examples
(page 26 of that document). That naming convention has stuck, and it is one of
the few parts of the pattern with an unambiguous origin.

Aliases in real use vary by community rather than by meaning.

- **Event Store** names the storage component, and is often used loosely for the
  whole approach.
- **Append-only state** or **immutable log** is how the same idea is described
  in database and stream-processing circles, where the log came first and the
  application pattern arrived later.
- **Accumulate and retract**, in Datomic's terminology, is the same model
  expressed as facts rather than as domain events. Datomic's documentation
  describes information as accumulating over time, with change represented by
  accumulating the new rather than modifying or removing the old, and a database
  value as a point-in-time immutable value
  ([docs.datomic.com/whatis/data-model.html](https://docs.datomic.com/whatis/data-model.html),
  verified 2026-08-02).

Three things are called Event Sourcing in day-to-day speech and conflating them
produces most of the bad advice about the pattern.

- **Event Sourcing proper.** The event log is the system of record. Current
  state exists nowhere authoritative. Any state a query touches is derived and
  can be thrown away and rebuilt. Microsoft's Azure Architecture Center states
  the same, that the events persist in an event store that serves as the system
  of record about the current state of the data
  ([learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing),
  verified 2026-08-02).
- **Event-driven architecture.** Components communicate by publishing and
  reacting to messages. Nothing is said about where state lives. A service can
  publish events all day and still store a mutable row per order.
- **An audit log beside a mutable table.** The table is the truth, the log is a
  side record written for compliance. If the two disagree, the table wins. That
  is not this pattern, and dimension 12 treats it as a named alternative rather
  than a degenerate case.

The single test that separates them. Delete every derived table and every cache.
If the system can be rebuilt correctly from what remains, it is event sourced.
If something was lost, the log was never the source of truth.

## 2. Problem and context

A system needs to answer questions about how it reached its current state, and
the storage model it uses has already destroyed the answer.

The situation reads like this in a codebase. There is a table with a `status`
column and an `updated_at` timestamp. A support ticket arrives asking why a
particular order was refunded twice. The table shows one row, one status, one
timestamp. The sequence of decisions that produced it is gone, overwritten by
the last `UPDATE`. Somebody adds a `history` table. Six months later a second
question arrives that the history table does not have the columns to answer,
because the history table was designed to answer the first question. A third
table appears. Now three writers must be kept in agreement, and none of them is
authoritative.

A second, independent pressure produces the same conclusion from a different
direction. Under concurrent load, read-modify-write against a row taken with a
lock becomes the bottleneck. Microsoft's writeup names write contention
explicitly, because updates require read-modify-write cycles with row-level
locking, so concurrent writes to the same entity degrade under load
([learn.microsoft.com](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing),
verified 2026-08-02). An append does not contend the same way.

The context in which the pattern earns its cost has four parts, and the pattern
is a liability when any of them is missing.

- **History has business value in itself.** Somebody outside engineering wants
  to ask questions of the past, and those questions are not known in advance.
  This is the part that cannot be retrofitted. If a request for last quarter's
  intermediate states arrives after the system was built on mutable rows, the
  data does not exist and no amount of engineering will recover it.
- **The domain has real events.** Domain experts already speak in past-tense
  verbs. A shipment was dispatched, a policy lapsed, a seat was reserved. If
  they speak in nouns and fields, the event model will be invented by developers
  and will read as a change log rather than as a domain.
- **State is small enough per entity, or bounded.** A stream that grows without
  bound turns rehydration into a scan. Some designs bound it naturally, an order
  ends, a policy year closes. Some do not, a user account lives forever.
- **The team can carry the operational shape.** Eventual consistency between
  the log and every read model is not optional in this pattern. It is the shape.

The strongest published warning about the context comes from Microsoft, which
states plainly that event sourcing is a complex pattern with real trade-offs,
is costly to migrate to or from, and that for most systems and most parts of a
system traditional data management is sufficient
([learn.microsoft.com](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing),
verified 2026-08-02). That sentence is on the vendor's own pattern page, which
is unusual and worth weighting accordingly.

## 3. Forces

This dimension is engineering judgement about which pressure wins. The
underlying mechanics are sourced above and below. The weighting is reasoning.

- **Auditability.** Favoured, more strongly than any other pattern in this
  family. The audit record is not a parallel artifact that can drift, it is the
  same bytes the application reads to make decisions. Nothing can be true in the
  system and absent from the log.
- **Write throughput and contention.** Favoured. Appends do not take a row lock
  to read-modify-write, and Microsoft attributes the write-throughput gain to
  exactly that
  ([learn.microsoft.com](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing),
  verified 2026-08-02). The gain is real but bounded, because the write path
  still needs an ordering guarantee per stream.
- **Read latency and query flexibility.** Sacrificed hard, and this is the cost
  people underestimate. There is no ad-hoc query over an event store. Microsoft
  states that the only data extractable is a stream of events by identifier, and
  that current state is determined only by replaying. Every question a reader
  wants to ask must be anticipated and built as a projection, or answered by an
  offline scan.
- **Consistency.** Sacrificed. Read models are eventually consistent by
  construction. A user who performs a write and immediately reads may not see
  their own change, and the interface has to be designed knowing that.
- **Coupling.** Split, and this is subtle. Coupling between the write side and
  the read side drops to near zero, because a new read model is built by
  replaying an existing log with no coordination. Coupling to the event schema
  rises sharply, because every event ever written is now a permanent public
  interface that some future code must still be able to read. The pattern trades
  runtime coupling for temporal coupling.
- **Operability.** Sacrificed. Debugging gains a great deal, because the exact
  input sequence that produced a bug is on disk and replayable. Routine
  operations lose, because there is no row to inspect, no `UPDATE` to correct a
  mistake, and no obvious answer to "the projection is wrong, what now".
- **Cost.** Storage grows without a natural limit and is never freed by normal
  operation. Compute is spent replaying. Against that, the storage is sequential
  and compresses well, and LMAX's design is built on exactly that observation,
  treating sequential disk writes as cheap
  ([martinfowler.com/articles/lmax.html](https://martinfowler.com/articles/lmax.html),
  verified 2026-08-02).
- **Cognitive load.** Sacrificed, permanently and for every future joiner. A new
  developer cannot open a table and see the state. They must know which events
  exist, which projection answers which question, and which version of an event
  they are looking at.
- **Team topology.** Favoured for a team that owns a bounded context outright.
  Sacrificed where an event schema crosses a team boundary, because that schema
  then needs the discipline of a public API with none of the tooling.

The pattern's defining trade is history and write-side simplicity paid for with
read-side complexity and permanent schema obligation.

## 4. Applicability and non-applicability

Reach for Event Sourcing when the following hold.

- The history of change is itself the product or a regulatory obligation.
  Ledgers, trading systems, insurance policy lifecycles, clinical records,
  anything with a statutory retention duty.
- Questions about the past are open-ended and will keep arriving. A projection
  built next year from an existing log is cheap. A history table missing a
  column is not.
- Reversal must be modelled, not erased. Young's treatment of deletion, a
  reversal transaction that leaves a trail showing the object had been in that
  state at a given time, is the behaviour a ledger needs
  ([CQRS Documents](https://cqrs.wordpress.com/wp-content/uploads/2010/11/cqrs_documents.pdf),
  page 31, verified 2026-08-02).
- Write contention on a small number of hot entities is the actual measured
  bottleneck, and appends with optimistic concurrency relieve it.
- Debugging depends on reproducing an exact input sequence. LMAX's business
  logic processor is derivable entirely by processing its input events, which is
  what makes a production incident replayable offline
  ([martinfowler.com/articles/lmax.html](https://martinfowler.com/articles/lmax.html),
  verified 2026-08-02).
- Several downstream consumers need the same change stream and will keep being
  added.

### Non-applicability

Do not reach for Event Sourcing in the following cases. This list is the more
useful half.

- **Plain CRUD with no history requirement.** Microsoft names this first among
  the cases where the pattern does not suit, because the operational overhead of
  an event store is not repaid when the only requirement is current-state reads
  and writes ([learn.microsoft.com](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing),
  verified 2026-08-02).
- **Reference and lookup data.** Country codes, tax bands, product catalogues.
  The data is close to static and the change history has no consumer.
- **Prototypes and short-lived systems.** The investment lands in event design
  and schema evolution, and neither pays back before the system is retired.
- **Read-your-own-write is a hard requirement.** If a user must see their change
  reflected immediately in every view, eventual consistency between log and
  projection fights the requirement on every screen. Workarounds exist, reading
  from the write model or serving an optimistic local view, and each is a cost.
- **The team has no event-driven experience and no time to acquire it.**
  Microsoft names inexperience as a case where the pattern should not be used,
  because adopting it without the groundwork raises the risk of anti-patterns
  that are costly to reverse.
- **The domain has no events, only fields.** If the only honest event name is
  `RecordUpdated`, the log carries no more meaning than the table it replaced,
  and every cost has been paid for nothing. Microsoft draws the same distinction
  between an event recording that two seats were reserved and one recording that
  remaining seats changed to 42, calling the state-focused form a change log
  with no business meaning.
- **The whole system, uniformly.** The pattern is not all or nothing. Applying
  it to a payment ledger while leaving user profile management as CRUD is the
  documented recommendation, not a compromise.
- **Personal data cannot be separated from event payloads and erasure requests
  are expected.** See dimension 17. This is a design constraint to settle before
  the first event is written, not after.
- **Unbounded streams with hot rehydration and no archival plan.** A per-user
  activity stream that lives ten years and is replayed on every login will grow
  until it is the outage.

## 5. Structure

The participants, each named for the role it plays.

- **Event.** An immutable record of something that has happened, named as a
  past-tense verb, carrying the data needed to describe that occurrence and
  nothing about how it should be handled. It has an identity, a stream position,
  and a schema version.
- **Stream.** The ordered sequence of events for one entity. KurrentDB's
  documentation describes events as logically organised into streams, with one
  stream per entity as the usual shape
  ([docs.kurrent.io](https://docs.kurrent.io/server/v25.0/features/streams.html),
  verified 2026-08-02). The stream is the unit of ordering and of concurrency
  control, and it is the reason the design partitions naturally by entity.
- **Event Store.** The append-only durable log. It offers two operations that
  matter, read a stream from a position, and append to a stream at an expected
  version. Everything else it offers is convenience.
- **Aggregate, or decision model.** The in-memory object rebuilt from a stream
  that holds the invariants. It has two distinct halves that must not be
  confused. An `apply` half that mutates in-memory state from an event and can
  never fail or decide anything, and a `decide` half that takes a command,
  checks invariants against current in-memory state, and returns new events
  without mutating anything.
- **Command Handler.** Loads the stream, rehydrates the aggregate, calls the
  decide half, and appends the resulting events at the version it read. Owns the
  retry on concurrency conflict.
- **Projection, or read model.** A consumer that folds events into a shape built
  for one query. It is derived, disposable, and rebuildable. Microsoft calls
  these materialized views and describes them as read-only projections optimised
  for querying.
- **Snapshot.** A cached serialisation of aggregate state at a stream position,
  used to shorten rehydration. Not a participant in the model, an optimisation
  over it. See dimension 8.
- **Upcaster.** A transformation applied on read that converts an event written
  under an older schema into the shape current code expects. Axon Framework
  models this as a chain, where each upcaster converts from one revision to the
  next and the output of one is the input of the next
  ([docs.axoniq.io](https://docs.axoniq.io/axon-framework-reference/4.11/events/event-versioning/),
  verified 2026-08-02).
- **Gateway.** The boundary that talks to the outside world. Fowler is explicit
  that the domain logic should never care about the context in which events are
  being run, and that the gateway decides whether to send an external message
  ([martinfowler.com/eaaDev/EventSourcing.html](https://martinfowler.com/eaaDev/EventSourcing.html),
  verified 2026-08-02). Without this separation, replaying a log re-sends every
  email the system ever sent.

The relationship that carries the pattern. The Event Store points at the
Aggregate only through replay, never by reference. The Projection depends on the
Event, never on the Aggregate. Nothing depends on a Projection except queries.

## 6. Structure diagram

```
                        write path
  +---------+   command   +-----------------+
  | Client  |------------>| Command Handler |
  +---------+             +--------+--------+
       ^                           |
       |                    1. read stream
       |                    3. append at expected version
       |                           v
       |                  +--------------------+
       |                  |    EVENT STORE     |   append-only
       |                  |  (source of truth) |   never updated
       |                  +--------------------+
       |                     |    ^        |
       |          2. replay  |    |        | publish / poll
       |                     v    | (opt.) v
       |            +-------------+--+   +-----------------+
       |            |   Aggregate    |   |   Projection    |
       |            |  decide+apply  |   |   (read model)  |
       |            +----------------+   +--------+--------+
       |                     ^                    |
       |                     | shortcut           | derived, disposable
       |            +--------+-------+            v
       |            |    Snapshot    |   +-----------------+
       |            | (optimisation) |   |  Query Store    |
       |            +----------------+   +--------+--------+
       |                                          |
       +------------------------------------------+
                        read path (eventually consistent)

  Upcaster sits on every read out of the EVENT STORE.
  Gateway (not shown) guards all outbound effects so replay is safe.
```

## 7. Dynamics

Two flows matter. A command that succeeds against a contended stream, and a
projection rebuild.

```
Command flow with optimistic concurrency

Client      Handler        EventStore      Aggregate     Projection
  |            |                |               |             |
  |--reserve-->|                |               |             |
  |            |--read("s-7")-->|               |             |
  |            |<--[e1,e2,e3]---|               |             |
  |            |------------ replay ----------->|             |
  |            |          (apply e1,e2,e3, version=3)         |
  |            |--decide(reserve 2)------------>|             |
  |            |<--[SeatsReserved(2)]-----------|             |
  |            |                |               |             |
  |            |--append("s-7", expected=3, [e4])-->          |
  |            |                |                             |
  |            |     CASE A: stream still at 3                |
  |            |<--ok, now 4----|                             |
  |<--202------|                |----- publish e4 ----------->|
  |            |                |                        fold into view
  |            |                |                             |
  |            |     CASE B: another writer appended e4'      |
  |            |<--conflict-----|  (stream is at 4)           |
  |            |                |                             |
  |            |--read("s-7")-->|   retry from the top:       |
  |            |<--[e1..e4']----|   re-decide against the     |
  |            |                |   state that actually won   |
```

The retry is a re-decision, never a re-append of the same event. That
distinction is the whole safety argument. The aggregate re-evaluates the
invariant against the state that actually won, so a seat that was taken in
between is seen. Microsoft describes the same mechanism, an event store
rejecting an append if the stream changed since it was read, after which the
handler reloads, re-evaluates and retries
([learn.microsoft.com](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing),
verified 2026-08-02).

```
Projection rebuild, the operation that makes the log the truth

  t0   projection v1 serving queries, at position 9,412,880
  t1   deploy projection v2 code, new empty store, position 0
  t2   v2 replays from position 0 --------------------------+
       upcasters normalise every old event shape on the way  |
  t3   v2 reaches 9,412,880, then catches the live tail      |
  t4   flip reads from v1 to v2, delete v1 entirely          |
  t5   nothing was lost, because v1 held no truth  <---------+

  The same sequence with the log as an audit side-record
  instead of the source of truth is impossible at t2,
  because the data the new view needs was never written.
```

## 8. Implementation variants

**Aggregate-per-stream with optimistic concurrency.** The default. One stream
per entity, appends carry the expected version, conflicts retry. Cost, the
consistency boundary equals the aggregate boundary, so any invariant spanning
two entities needs a Saga. Benefit, appends never take a lock and the store
partitions by entity identifier without further thought.

**Purpose-built event store versus a relational table.** Microsoft frames the
choice cleanly. A purpose-built store gives stream-by-entity reads, optimistic
concurrency and snapshots as built-ins, while a relational database is familiar
and available everywhere but requires building those behaviours
([learn.microsoft.com](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing),
verified 2026-08-02). Marten takes the relational route explicitly, as a .NET
library that turns PostgreSQL into both a document store and an event store
([martendb.io/events/versioning.html](https://martendb.io/events/versioning.html),
verified 2026-08-02). Engineering judgement, a single-node Postgres table with a
unique index on `(stream_id, version)` gives correct optimistic concurrency in
about thirty lines and is the right first move for most teams, because it keeps
the operational surface at one database.

**Message broker as the store, which is usually a mistake.** Kafka's own
use-cases page states that event sourcing is a style where state changes are
logged as a time-ordered sequence of records, and that Kafka's capacity for
storing large volumes of log data suits it as a backend for such applications
([kafka.apache.org/uses](https://kafka.apache.org/uses), verified 2026-08-02).
Microsoft's page contradicts the naive reading of that directly, warning against
confusing an event store with a stream message broker, because brokers such as
Kafka lack per-entity stream queries and optimistic concurrency, and work as a
distribution layer rather than as a substitute for an event store
([learn.microsoft.com](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing),
verified 2026-08-02). Both statements are accurate and they are not in conflict.
Kafka stores a log durably. It does not give you a read-my-entity-then-append-if-unchanged
operation, and that operation is where correctness lives. The working shape is
an event store for the write path plus a broker for fan-out.

**Snapshots.** Young defines a rolling snapshot as a denormalisation of the
current state of an aggregate at a point in time, representing the state when
all events to that point have been replayed, and describes it as a heuristic to
prevent loading the full history
([CQRS Documents](https://cqrs.wordpress.com/wp-content/uploads/2010/11/cqrs_documents.pdf),
page 33, verified 2026-08-02). Microsoft states the constraint that follows
directly, that snapshots are an optimisation rather than a replacement for the
event stream, the stream remains the source of truth, and snapshots can be
regenerated from it at any time
([learn.microsoft.com](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing),
verified 2026-08-02). The operational rule that falls out of those two
statements is testable and belongs in CI. Delete every snapshot, replay from
zero, and assert the state is identical. The Go sample below does exactly that.
A codebase where that test fails has smuggled truth into a snapshot, and the log
has quietly stopped being the source of record.

**Schema evolution, which is the hardest long-term problem.** Nothing else in
this pattern still costs money in year five. Greg Young wrote a whole book on
this one dimension, *Versioning in an Event Sourced System*, covering weak
schema, double write, negotiation, copy and replace, changing stream boundaries
and aggregate redesign
([leanpub.com/esversioning](https://leanpub.com/esversioning), verified
2026-08-02). Four strategies, in ascending order of cost and descending order of
preference.

1. **Weak schema, or tolerant reading.** Consumers ignore unknown fields and
   supply defaults for absent ones. Microsoft describes this as handling
   additive non-breaking changes such as an optional field without transforming
   stored events. This covers the majority of real changes and costs nothing at
   read time. Adopt it before the first event ships, because retrofitting a
   strict deserialiser into tolerance means auditing every consumer.
2. **Explicit versioning.** A revision identifier travels in the envelope or in
   the type name. Axon supplies four `RevisionResolver` implementations for
   this, reading an annotation, a `serialVersionUID`, a fixed value, or the
   Maven artifact version
   ([docs.axoniq.io](https://docs.axoniq.io/axon-framework-reference/4.11/events/event-versioning/),
   verified 2026-08-02). The Maven-artifact variant is a trap worth naming.
   Binding an event revision to a build version means a release that changed no
   events still produces a revision bump, and the upcaster chain grows for
   nothing.
3. **Upcasting on read.** The stored bytes never change, a chain of functions
   normalises them to current shape at deserialisation. Axon's `Upcaster` works
   over a `Stream<IntermediateEventRepresentation>` rather than over one event
   at a time, which is what makes one-to-many and many-to-one transformations
   possible, with `SingleEventUpcaster` and `EventMultiUpcaster` as the base
   classes. Marten offers the same idea against either the old CLR type or raw
   JSON. The cost is cumulative and permanent. Every chain link is code that
   must be kept alive, tested, and understood by somebody who never saw the
   schema it converts from.
4. **In-place migration, copy and replace.** Rewrite the stored events.
   Microsoft calls this a last resort because it breaks immutability and
   undermines the audit trail. The honest version is a copy-and-replace into a
   new stream with the old one retained, which preserves the audit record at the
   cost of storage and of a cutover.

**Correction over mutation.** Marten's documentation puts the philosophy
plainly, that the best strategy is not to change past data but to compensate for
mistakes ([martendb.io](https://martendb.io/events/versioning.html), verified
2026-08-02). Young's reversal transaction is the same move
([CQRS Documents](https://cqrs.wordpress.com/wp-content/uploads/2010/11/cqrs_documents.pdf),
page 31, verified 2026-08-02). This is also how the business already works. An
accountant does not erase a wrong entry, they post a correcting one.

### Code

Python, the aggregate, replay, and optimistic concurrency. Run with `python3`.

```python
from dataclasses import dataclass, field
from typing import Iterable


class ConcurrencyError(Exception):
    pass


@dataclass(frozen=True)
class Event:
    type: str
    data: dict


@dataclass
class Account:
    id: str
    balance: int = 0
    closed: bool = False
    version: int = 0

    def apply(self, e: Event) -> None:
        if e.type == "Opened":
            self.balance = e.data["opening"]
        elif e.type == "Deposited":
            self.balance += e.data["amount"]
        elif e.type == "Withdrawn":
            self.balance -= e.data["amount"]
        elif e.type == "Closed":
            self.closed = True
        self.version += 1

    def withdraw(self, amount: int) -> list[Event]:
        if self.closed:
            raise ValueError("account closed")
        if amount > self.balance:
            raise ValueError("insufficient funds")
        return [Event("Withdrawn", {"amount": amount})]


def rehydrate(account_id: str, events: Iterable[Event]) -> Account:
    acc = Account(account_id)
    for e in events:
        acc.apply(e)
    return acc


@dataclass
class Store:
    streams: dict[str, list[Event]] = field(default_factory=dict)

    def read(self, sid: str) -> list[Event]:
        return list(self.streams.get(sid, []))

    def append(self, sid: str, expected: int, new: list[Event]) -> None:
        cur = self.streams.setdefault(sid, [])
        if len(cur) != expected:
            raise ConcurrencyError(f"expected {expected}, stream at {len(cur)}")
        cur.extend(new)


if __name__ == "__main__":
    store = Store()
    store.append("acc-1", 0, [Event("Opened", {"opening": 100})])

    acc = rehydrate("acc-1", store.read("acc-1"))
    store.append("acc-1", acc.version, acc.withdraw(30))

    print(rehydrate("acc-1", store.read("acc-1")))

    stale = rehydrate("acc-1", [Event("Opened", {"opening": 100})])
    try:
        store.append("acc-1", stale.version, [Event("Withdrawn", {"amount": 90})])
    except ConcurrencyError as err:
        print("rejected:", err)
```

Note the split. `apply` decides nothing and cannot fail, `withdraw` decides and
never mutates. Keeping those apart is what allows replay of ten million events
without re-running a single business rule.

TypeScript, an upcaster chain. Compiled with `tsc --strict --target es2020`.

```typescript
type Stored = { type: string; version: number; data: Record<string, unknown> };

type Upcaster = (e: Stored) => Stored;

const upcasters: Record<string, Upcaster[]> = {
  Withdrawn: [
    // v1 stored a bare number of cents. v2 names the currency.
    (e) => ({ ...e, version: 2, data: { ...e.data, currency: "EUR" } }),
    // v3 splits the flat amount into a money object.
    (e) => ({
      type: e.type,
      version: 3,
      data: {
        money: { amount: e.data.amount, currency: e.data.currency },
        ...(e.data.reason ? { reason: e.data.reason } : {}),
      },
    }),
  ],
};

function upcast(e: Stored): Stored {
  const chain = upcasters[e.type] ?? [];
  let out = e;
  for (let i = out.version - 1; i < chain.length; i++) out = chain[i](out);
  return out;
}

const stream: Stored[] = [
  { type: "Withdrawn", version: 1, data: { amount: 30 } },
  { type: "Withdrawn", version: 2, data: { amount: 40, currency: "USD" } },
  { type: "Withdrawn", version: 3, data: { money: { amount: 5, currency: "GBP" } } },
];

for (const e of stream) console.log(JSON.stringify(upcast(e)));
```

Every event leaves the chain at v3 regardless of the version it entered at, so
application code sees one shape. The `v1` default of EUR is a decision that can
never be revisited once it ships, which is the reason to prefer the tolerant
reader when the change is merely additive.

Go, a snapshot that provably carries no truth. Run with `go run`.

```go
package main

import "fmt"

type Event struct {
	Type   string
	Amount int
}

type Cart struct {
	Total   int
	Items   int
	Version int
}

func (c *Cart) Apply(e Event) {
	switch e.Type {
	case "ItemAdded":
		c.Items++
		c.Total += e.Amount
	case "ItemRemoved":
		c.Items--
		c.Total -= e.Amount
	}
	c.Version++
}

type Snapshot struct {
	State   Cart
	Version int
}

type Store struct {
	events []Event
	snap   *Snapshot
	every  int
}

func (s *Store) Append(e Event) {
	s.events = append(s.events, e)
	if len(s.events)%s.every == 0 {
		s.snap = &Snapshot{State: s.Load(), Version: len(s.events)}
	}
}

// Load replays from the snapshot when one exists, otherwise from zero.
// Deleting every snapshot must not change the result.
func (s *Store) Load() Cart {
	c := Cart{}
	from := 0
	if s.snap != nil {
		c = s.snap.State
		from = s.snap.Version
	}
	for _, e := range s.events[from:] {
		c.Apply(e)
	}
	return c
}

func main() {
	s := &Store{every: 3}
	for i := 1; i <= 7; i++ {
		s.Append(Event{"ItemAdded", i * 10})
	}
	s.Append(Event{"ItemRemoved", 10})

	withSnap := s.Load()
	s.snap = nil
	fromZero := s.Load()

	fmt.Printf("with snapshot %+v\n", withSnap)
	fmt.Printf("from zero     %+v\n", fromZero)
	fmt.Println("equivalent:", withSnap == fromZero)
}
```

The final comparison is the property to assert in CI. When it stops holding, a
snapshot has become authoritative and the log is no longer the record.

Rust, crypto-shredding as a sketch. Compiled with `rustc -O`. The XOR stands in
for a real authenticated cipher and is not usable as written.

```rust
use std::collections::HashMap;

// Crypto-shredding sketch. The event keeps its shape, the payload is
// unreadable once the subject key is dropped.
struct KeyVault {
    keys: HashMap<String, u8>,
}

impl KeyVault {
    fn new() -> Self {
        KeyVault { keys: HashMap::new() }
    }
    fn key_for(&mut self, subject: &str) -> u8 {
        let next = (self.keys.len() as u8) + 7;
        *self.keys.entry(subject.to_string()).or_insert(next)
    }
    fn shred(&mut self, subject: &str) {
        self.keys.remove(subject);
    }
    fn get(&self, subject: &str) -> Option<u8> {
        self.keys.get(subject).copied()
    }
}

fn xor(bytes: &[u8], key: u8) -> Vec<u8> {
    bytes.iter().map(|b| b ^ key).collect()
}

struct Event {
    kind: &'static str,
    subject: String,
    sealed: Vec<u8>,
}

fn seal(vault: &mut KeyVault, kind: &'static str, subject: &str, pii: &str) -> Event {
    let key = vault.key_for(subject);
    Event { kind, subject: subject.to_string(), sealed: xor(pii.as_bytes(), key) }
}

fn open(vault: &KeyVault, e: &Event) -> Option<String> {
    let key = vault.get(&e.subject)?;
    String::from_utf8(xor(&e.sealed, key)).ok()
}

fn main() {
    let mut vault = KeyVault::new();
    let log = vec![
        seal(&mut vault, "CustomerRegistered", "cust-1", "ada@example.test"),
        seal(&mut vault, "AddressChanged", "cust-1", "12 Mill Lane"),
        seal(&mut vault, "CustomerRegistered", "cust-2", "linus@example.test"),
    ];

    for e in &log {
        println!("{} {} -> {:?}", e.kind, e.subject, open(&vault, e));
    }

    vault.shred("cust-1");
    println!("after erasure request for cust-1");
    for e in &log {
        println!("{} {} -> {:?}", e.kind, e.subject, open(&vault, e));
    }
}
```

The stream positions, the event types and the causal ordering survive the shred.
Only the payload becomes unreadable. That property is what makes the technique
compatible with a log at all, and dimension 17 covers where it stops working.

## 9. Known production uses

**LMAX Exchange.** The business logic processor holds all state in memory and
its current state is entirely derivable by processing the input events, which
are journalled to durable storage by streaming writes. A full restart, including
JVM start, loading a recent snapshot and replaying a day of journals, takes
under a minute, and the processor is reported at six million orders per second
on a single thread on a commodity Nehalem-based server
([martinfowler.com/articles/lmax.html](https://martinfowler.com/articles/lmax.html),
verified 2026-08-02). LMAX is the strongest published counter-argument to the
belief that event sourcing is slow.

**KurrentDB, formerly EventStoreDB.** A database purpose-built for event
storage, organising events into streams, with one stream per entity as the usual
shape. Its documentation is also the clearest statement of the immutability
constraint, that events cannot be selectively deleted from the middle of a
stream, only truncated or hard-deleted via a tombstone
([docs.kurrent.io](https://docs.kurrent.io/server/v25.0/features/streams.html),
verified 2026-08-02).

**Axon Framework.** A JVM framework whose event versioning documentation states
that event stores are read and append-only data sources, and which ships the
upcaster chain, four revision resolvers, and the single and multi upcaster base
classes described in dimension 8
([docs.axoniq.io](https://docs.axoniq.io/axon-framework-reference/4.11/events/event-versioning/),
verified 2026-08-02).

**Marten.** A .NET library making PostgreSQL serve as both document database and
event store, with event type name mapping, upcasting against old CLR types or
raw JSON, and archiving to keep streams manageable
([martendb.io](https://martendb.io/events/versioning.html), verified
2026-08-02). It is the reference case for the relational-store variant.

**Amazon Web Services prescriptive guidance.** AWS documents event sourcing as a
named pattern, implemented with either Kinesis Data Streams as a centralised
event store persisting to S3, or EventBridge with an event archive that supports
replay for reprocessing through a replay queue
([docs.aws.amazon.com](https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-data-persistence/service-per-team.html),
verified 2026-08-02). The same page states that adopting event sourcing across
microservices obliges the Saga pattern for cross-service consistency.

**Datomic.** The immutable-fact expression of the same model. A database value
is a point-in-time immutable value, information accumulates, and CRUD is
replaced by assert, read, accumulate, retract, where existing datoms never
change and a retraction states that an assertion no longer holds from a later
point without altering the original
([docs.datomic.com](https://docs.datomic.com/whatis/data-model.html), verified
2026-08-02).

**Apache Kafka.** Named by its own project as a backend for event-sourced
applications, on the basis of its capacity for storing large volumes of log
data, and separately as an external commit log for distributed systems with log
compaction supporting that use
([kafka.apache.org/uses](https://kafka.apache.org/uses), verified 2026-08-02).
Read alongside the Microsoft warning quoted in dimension 8.

## 10. Consequences

The costs below are matters of degree and the weighting is engineering
judgement. The mechanisms are sourced above.

### Positive

- The audit record cannot drift from behaviour, because it is the same data the
  application reads to decide.
- Any question about the past that the events can answer is answerable later,
  including questions nobody thought to ask when the system was built.
- A new read model is a replay, requiring no migration, no backfill script and
  no coordination with the write side.
- Production bugs are reproducible offline by replaying the exact input
  sequence, which is what makes LMAX's model debuggable at six million orders
  per second.
- Write contention drops, because appends do not perform a locked
  read-modify-write.
- The store partitions by entity identifier with no further design, since each
  entity's stream is independent.
- Temporal queries, as-of reconstruction and what-if analysis become ordinary
  rather than special projects.
- Integration is cheap in one direction. A new consumer subscribes and catches
  up from position zero without asking permission.

### Negative

- Query flexibility collapses. Every question needs a projection built in
  advance, or an offline scan.
- Eventual consistency is structural. Every screen that reads after a write
  needs a designed answer.
- Storage grows monotonically and is never freed by ordinary operation.
- Schema obligation is permanent. An event written today constrains code written
  in ten years.
- Two failure surfaces exist where CRUD had one, the log and every projection,
  and projections drift silently.
- Onboarding cost is real and recurring. There is no table to read.
- Migration away is expensive, which Microsoft names directly as costly to
  migrate to or from, with the pattern constraining future design decisions once
  adopted ([learn.microsoft.com](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing),
  verified 2026-08-02).
- Deletion is a design problem rather than a `DELETE`, covered in dimension 17.
- Idempotency becomes a requirement rather than a nicety, because delivery to
  consumers is at-least-once in the usual case.

## 11. Failure modes and misuse

Symptoms are drawn from practice and are engineering judgement. The mechanisms
they arise from are sourced above.

**Symptom.** Replaying the log in a test environment sends real emails, charges
real cards, or calls a partner API.
**Cause.** Side effects live in the aggregate's `apply` path rather than behind a
gateway, so replay re-executes them. Fowler's separation of gateway from domain
logic exists precisely for this
([martinfowler.com/eaaDev/EventSourcing.html](https://martinfowler.com/eaaDev/EventSourcing.html),
verified 2026-08-02).
**Fix.** Make `apply` a pure state fold with no I/O of any kind. Route every
outbound effect through a gateway that a replay runner can switch off. Test it
by replaying production events into a sandbox with egress blocked, and treating
any outbound attempt as a failing test.

**Symptom.** A deploy fails to start because deserialising an event from 2023
throws, and the aggregate cannot be loaded at all.
**Cause.** A strict deserialiser meets a field that was removed or renamed. The
weak-schema discipline was never adopted, so the first breaking change is a
production outage rather than a defaulted field.
**Fix.** Tolerant reading from the first release, then an upcaster for the shapes
already in the store. Add a CI job that deserialises a fixture corpus containing
one instance of every event version ever written. The corpus only grows.

**Symptom.** The projection shows a balance that is wrong by exactly one
transaction, intermittently, and rebuilding it fixes the number.
**Cause.** A non-idempotent projection handler processing an at-least-once
delivery twice, or once in each of two consumer instances. Microsoft names the
same case, where a duplicated reservation event must result in only one
decrement, and warns that without idempotency projections drift from the event
stream ([learn.microsoft.com](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing),
verified 2026-08-02).
**Fix.** Store the last processed position per projection in the same
transaction as the projection write, and skip anything at or below it. Alert on
the drift rather than on the duplicate, because the duplicate is normal.

**Symptom.** One customer's page takes eleven seconds to load and the rest take
forty milliseconds.
**Cause.** An unbounded stream. That customer has four hundred thousand events
and rehydration is a scan. The snapshot interval was tuned against the median
stream.
**Fix.** Snapshot by stream length rather than on a fixed schedule, and treat a
stream past a threshold as a modelling defect rather than a tuning problem.
Close and open a new stream at a natural boundary, a billing period, a policy
year. Marten's documentation points at archiving and temporal modelling for the
same reason ([martendb.io](https://martendb.io/events/versioning.html), verified
2026-08-02).

**Symptom.** A snapshot is deleted during an incident and the rebuilt state
differs from what the application had been serving.
**Cause.** State reached the snapshot that was never derived from events, most
often a field added to the snapshot serialiser and never to an event. The
snapshot silently became a second source of truth.
**Fix.** The replay-equivalence assertion from the Go sample, run in CI on every
aggregate. Version snapshots separately from events and discard every snapshot
on an aggregate code change, since regenerating them is cheap and trusting a
stale one is not.

**Symptom.** Event names in the log are `OrderUpdated`, `OrderUpdated`,
`OrderUpdated`, each carrying a full object.
**Cause.** CRUD was written with an append-only store underneath it. Every cost
of the pattern was paid and no history was captured, because the diff between
two full snapshots does not recover intent. Microsoft's distinction between
recording two seats reserved and recording remaining seats changed to 42 is the
same failure.
**Fix.** Rename events after the business decision, not after the field that
moved. If no such name exists, this domain does not want the pattern, and
dimension 4 applies.

**Symptom.** An invariant spanning two aggregates is violated under load, for
example stock going negative across two warehouses.
**Cause.** Optimistic concurrency guards one stream. It says nothing about two.
**Fix.** Either redraw the aggregate boundary so the invariant sits inside one
stream, or accept eventual consistency and add a Saga with a compensating
action. AWS states the obligation directly, that using event sourcing across
microservices requires deploying the Saga pattern to maintain consistency
([docs.aws.amazon.com](https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-data-persistence/service-per-team.html),
verified 2026-08-02).

**Symptom.** Handling one event produces another that triggers the first, and
throughput collapses with no error in the logs.
**Cause.** A cycle between handlers. Microsoft names circular logic as a
consideration, where processing one event requires creating new events and the
sequence can loop indefinitely.
**Fix.** Carry a causation identifier and a hop count on every event, and drop or
alert past a bound. Draw the handler graph in review and require it to be
acyclic.

**Symptom.** A legal request to erase a person's data arrives and there is no
mechanism, so the ticket is closed by deleting a projection row while the
payload stays in the log.
**Cause.** The tension in dimension 17 was not designed for. KurrentDB's
documentation is explicit that events cannot be selectively deleted from the
middle of a stream
([docs.kurrent.io](https://docs.kurrent.io/server/v25.0/features/streams.html),
verified 2026-08-02).
**Fix.** Dimension 17. The decision belongs before the first event, not after
the first request.

## 12. Trade-off matrix

Alternatives are named patterns, each in production use.

| Force | Event Sourcing | CRUD with mutable rows | Audit log beside CRUD | Change Data Capture (Debezium) | Temporal or bitemporal tables |
|---|---|---|---|---|---|
| Source of truth | The log | The row | The row, log is secondary | The row, log is derived from the DB WAL | The row plus its version history |
| Captures intent | Yes, event names carry the decision | No | Partly, whatever the writer chose to record | No, row deltas only | No, value changes only |
| Rebuild state from scratch | Yes, by definition | No | No, log is incomplete by construction | No, the log starts where CDC was turned on | Within the retention window |
| New read model without migration | Replay, no coordination | Backfill script | Backfill script | Replay from broker retention | Query the history table |
| Ad-hoc query | Poor, needs a projection | Excellent, SQL | Excellent on the row, poor on the log | Excellent on the source DB | Good, with temporal predicates |
| Write contention | Low, appends | High under hot rows | High, plus a second write | Same as the underlying CRUD | Same as CRUD plus history insert |
| Consistency of reads | Eventual for projections | Immediate | Immediate | Eventual downstream | Immediate |
| Log and state can disagree | Impossible | Not applicable | Yes, the common defect | No, log is machine-generated | No |
| Schema obligation | Permanent, every version forever | Migration and forget | Migration and forget | Follows the table schema | Follows the table schema |
| Erasure of personal data | Hard, see dimension 17 | `DELETE` | `DELETE` in two places | Follows the source delete, plus a tombstone | `DELETE` plus history purge |
| Operational surface | Store plus every projection | One database | One database | Database plus connector plus broker | One database |
| Onboarding cost | High | Low | Low | Medium | Medium |

Two rows deserve elaboration.

**Against the audit log.** The row that decides it is "log and state can
disagree". A hand-written audit log is a second write by the same developer who
wrote the first, and it fails silently the day somebody adds a code path that
updates the row and forgets the log. Nothing detects it, because nothing reads
the log to make a decision. In Event Sourcing that failure is not expressible.
The cost of that guarantee is every other row in the table.

**Against Change Data Capture.** These solve different problems and are often
posed as competitors. Debezium describes itself as a low-latency data streaming
platform for change data capture, with connectors monitoring an upstream
database server, capturing row-level changes and recording them to Kafka topics,
where only committed changes are visible
([github.com/debezium/debezium README](https://raw.githubusercontent.com/debezium/debezium/main/README.md),
verified 2026-08-02). That is a stream of row deltas produced by the database,
not a record of intent produced by the domain. CDC tells you that
`orders.status` went from `PENDING` to `CANCELLED`. It cannot tell you whether
the customer cancelled, the fraud engine blocked it, or an operator corrected a
mistake, because the database never knew. CDC is the correct answer when a
system already exists on mutable rows and downstream consumers need its changes.
It is the wrong answer when the reason for the change is the thing being asked
for. The two also compose, with CDC used as the Outbox delivery mechanism for a
service that is internally event sourced.

## 13. Related and incompatible patterns

**CQRS.** The closest relation and the one most often assumed to be mandatory.
It is not. CQRS separates the write model from the read model. Event Sourcing
determines what the write model persists. Each works without the other. In
practice they arrive together because once the write side stores events, the
read side has nothing to query and needs its own model, which is CQRS. AWS
states the pairing as usual rather than required
([docs.aws.amazon.com](https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-data-persistence/service-per-team.html),
verified 2026-08-02).

**Saga, or process manager.** Required, not optional, the moment an invariant
crosses an aggregate. Optimistic concurrency covers exactly one stream, so
consistency across two is a coordination problem, and AWS names Saga as an
obligation when the pattern spans microservices.

**Materialized View.** The read side. Microsoft describes projections in exactly
those terms, read-only projections of the event store optimised for querying
([learn.microsoft.com](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing),
verified 2026-08-02).

**Transactional Outbox.** Solves a problem Event Sourcing does not. Appending an
event and publishing it to a broker are two operations against two systems.
Either the store is also the broker, or an outbox makes the pair atomic.

**Memento.** The Gang of Four ancestor of the snapshot. Memento captures state
for later restoration without breaking encapsulation, which is what a snapshot
does, with the difference that a Memento is the record and a snapshot is a
cache over a record that lives elsewhere.

**Command.** Every write enters as a command and leaves as events. The naming
distinction is load bearing. Commands are imperative and refusable,
`ReserveSeats`. Events are past tense and not refusable, `SeatsReserved`.

**Retroactive Event, Fowler.** The companion pattern for correcting the past by
inserting an event at a historical position and recomputing forwards. It is the
formal alternative to the reversal transaction, and it is the point at which the
audit story becomes complicated enough to need its own design review.

**Conflicts rather than composes.** Event Sourcing sits badly with patterns that
assume a mutable current row. An ORM with change tracking and dirty-checking
fights it directly, because the ORM's model of persistence is the diff between a
loaded object and a saved one, which is the model this pattern replaces. Using
both usually produces an event log written as a side effect of an ORM save,
which is the audit-log alternative wearing the wrong name. Optimistic locking on
a row is likewise redundant, since the expected-version append already provides
it at the stream level.

## 14. Refactoring path in and out

### In, without a rewrite

The reason to work incrementally is that Microsoft's warning about migration
cost cuts both ways. Committing the whole system in one step is the expensive
mistake.

1. **Pick one aggregate that already has history value.** A ledger, an order
   lifecycle, a policy. Not the user profile.
2. **Name the events with a domain expert before writing code.** If the names
   come out as `Created`, `Updated`, `Deleted`, stop. The domain is not ready and
   dimension 4's non-applicability list applies.
3. **Write events beside the existing table, with the table still authoritative.**
   Nothing reads the events yet. This costs a double write and buys a real event
   stream to examine before anything depends on it.
4. **Build one projection from the events and compare it against the table
   continuously.** Alert on any mismatch. Every mismatch is a missing event or a
   missed code path. This is the step that finds the write path nobody
   remembered.
5. **Flip the read for one query to the projection.** The table is still the
   truth. Reverting is a config change.
6. **Flip the write. The aggregate now rehydrates from events and appends with
   an expected version.** The table becomes a projection, which is usually the
   right resting place. It keeps SQL available for reporting.
7. **Backfill a synthetic origin event per entity** carrying the state at
   cutover, named honestly, `MigratedFromLegacy`. Never pretend the history
   before cutover exists.
8. **Add the schema-evolution machinery before the second event version, not
   after.** Tolerant deserialisation, a version field, a fixture corpus in CI.

Steps 3 through 5 are reversible at any point. Step 6 is where the cost is
committed.

### Out, when it stops earning its place

Exit is possible and is usually cheaper than the entry, because the log contains
everything a state-based model needs.

1. Build the state-based schema as one more projection and run it in parallel.
2. Move reads to it, one query at a time.
3. Move writes to it, keeping the event append as a secondary write. The system
   is now the audit-log alternative from dimension 12, which is a legitimate
   destination.
4. Retain the historical log read-only, in cold storage. Deleting it destroys
   the thing that was paid for, and retention duties may forbid it anyway.
5. Retire the projection machinery last.

The honest signals that exit is right. No new projection has been built in a
year, meaning the flexibility is not being used. Every event is `XUpdated`,
meaning intent was never captured. The team maintaining upcasters no longer
includes anyone who understands the schemas being converted.

## 15. Testing and verification

Practice, not a sourced claim, other than the given-when-then style which
Microsoft names directly as suiting event-sourced systems, setting up past
events, issuing a command and asserting on the events produced
([learn.microsoft.com](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing),
verified 2026-08-02).

**Easier because of the pattern.**

- Business rules test with no database, no broker and no container. Given a list
  of prior events, when a command, then a list of expected events. The Python
  sample's `withdraw` needs no test double at all.
- Assertions are on events rather than on final state, which catches the case
  where the right number was reached for the wrong reason.
- Production bugs become fixtures. Copy the offending stream, replay it, watch
  the test fail, fix, watch it pass.

**Harder because of the pattern.**

- Projection correctness needs integration tests with a real store, since the
  interesting failures are ordering, duplication and position tracking.
- Schema evolution needs the growing fixture corpus described in dimension 11.
  Skipping it means the first breaking change is discovered in production.
- Eventual consistency makes whole-path integration tests flaky unless they wait
  on the projection position rather than on a timer. Polling until the
  projection reaches the append position is deterministic. `sleep(200)` is not.

**Techniques worth naming.**

- **Replay equivalence.** Rebuild every projection from zero in CI on a sample
  corpus and diff against the incrementally built version. A mismatch means a
  handler is not a pure fold.
- **Snapshot equivalence.** The Go sample's final assertion, per aggregate.
- **Upcaster round trip.** Every stored version deserialises, and the result
  equals what current code would have written for the same decision.
- **Idempotency by construction.** Feed each projection its own event stream
  twice and assert the state is unchanged.
- **Property-based replay.** Generate command sequences, apply them, replay the
  resulting events, and assert the rehydrated state matches the state reached
  directly. This finds `apply` methods that quietly depend on wall-clock time or
  on a random value.

## 16. Observability signals

Practice, not a sourced claim.

**Measure.**

- **Projection lag**, as store head position minus projection position, per
  projection. The single most useful number in an event-sourced system. It maps
  directly to how stale a user's screen is.
- **Append conflict rate**, as rejected appends over attempted appends, per
  stream type. A low steady rate is healthy and shows concurrency control
  working. A spike means a hot aggregate or a retry storm.
- **Rehydration cost**, as events replayed per command, at p50 and p99. The p99
  is where the unbounded stream from dimension 11 shows up long before it causes
  an outage.
- **Stream length distribution.** Alert on the maximum, not the mean.
- **Events appended per second by type.** A type that stops appearing is often a
  broken deploy rather than a quiet week.
- **Upcaster hit counts by source version.** When a version reaches zero across
  a full replay window, that chain link can be retired. Without this number,
  upcasters accumulate forever because nobody can prove one is unused.
- **Duplicate suppression count** per projection. Should be non-zero. Zero
  usually means the check is not wired up rather than that delivery is exactly
  once.

**Log and trace.**

- Carry `event_id`, `stream_id`, `stream_version`, `correlation_id` and
  `causation_id` on every event, and put them on the trace span. Causation makes
  the handler graph reconstructable from telemetry, which is the fastest route
  to the circular-logic failure in dimension 11.
- Log the expected version on every conflict, not only the fact of the conflict.
- Log projection rebuilds as deliberate events with start, position and end.

**A healthy dashboard.** Lag flat and under a second. Conflict rate low and
steady. p99 rehydration flat as the system ages, because snapshots and stream
bounds are working.

**A failing one.** Lag rising monotonically, which means a consumer is dead or
poisoned. Conflict rate climbing with throughput flat, which means a retry storm
on one aggregate. p99 rehydration rising month over month, which means streams
are unbounded and the outage is scheduled rather than possible.

## 17. Security and privacy implications

**What the pattern closes.** Tamper evidence improves markedly. An append-only
store with per-stream versioning makes silent modification hard, since altering
history means rewriting positions that projections and snapshots reference.
Attribution improves, because every change carries the command and actor that
caused it rather than a final value with an `updated_by` column. Insider misuse
becomes visible, since a privileged actor cannot quietly correct a row.

**What the pattern opens.** Every event is retained forever by default, so a
field added carelessly is retained carelessly forever. In a mutable system a
mistaken write is overwritten by the next one. Here it is permanent. Access
control also becomes coarse. Row-level security over a table is well understood.
Stream-level authorisation over an append-only log with projections that
aggregate across streams is not, and the projection is where a leak appears,
because it is the thing built for convenient querying.

**The erasure tension, stated precisely.** GDPR Article 17 grants a data subject
the right to erasure on grounds including withdrawal of consent, data no longer
being necessary for the purpose, and unlawful processing, subject to the Article
17(3) exemptions covering legal obligations, public-interest archiving,
scientific or historical research, and the establishment or defence of legal
claims ([gdpr-info.eu/art-17-gdpr](https://gdpr-info.eu/art-17-gdpr/), verified
2026-08-02). Against that, KurrentDB's documentation states that events cannot
be selectively deleted from the middle of a stream, only truncated or hard
deleted via a tombstone
([docs.kurrent.io](https://docs.kurrent.io/server/v25.0/features/streams.html),
verified 2026-08-02). Truncation removes everything before a position, including
other people's data. That is the conflict, and it is architectural rather than a
matter of tooling.

Three responses, in descending order of preference.

**Keep personal data out of the log.** Store a stable pseudonymous subject
identifier in events and hold the personal data in a separate mutable store
keyed by it. Erasure deletes from that store and the event stream stays intact
with a dangling reference. Microsoft names this as the common approach,
referencing personal data by identifier so deletion happens independently of the
event stream ([learn.microsoft.com](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing),
verified 2026-08-02). This is the answer when it is available. Its limit is that
some events are personal data by their nature. A `PregnancyRecorded` event is
special-category data regardless of which store the name sits in, and the
subject identifier plus timestamp plus stream is itself personal data under a
strict reading.

**Crypto-shredding.** Encrypt per-subject payloads under a per-subject key, and
delete the key on an erasure request. Microsoft describes it in those terms,
noting it adds encryption overhead on every read and write and requires strong
key management. It is the same technique NIST classifies as Cryptographic Erase,
sanitising the encryption key rather than the storage locations holding the
ciphertext, leaving only ciphertext behind and preventing read access
([NIST SP 800-88 Rev. 1](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-88r1.pdf),
section 2.6, verified 2026-08-02).

**The limits of crypto-shredding, which are the part most write-ups omit.** NIST
states the preconditions directly. Cryptographic Erase should not be used where
encryption was enabled after sensitive data was already stored without prior
sanitisation, or where it is unknown whether sensitive data was stored before
encryption. It should be considered only where all data intended for erasure was
encrypted prior to storage including virtualised copies, where the key locations
are known and can themselves be sanitised, and where all copies of the
encryption keys can be sanitised (NIST SP 800-88 Rev. 1, sections 2.6.1 and
2.6.2, verified 2026-08-02). Translated to an event-sourced system, four
concrete failure conditions follow.

1. Events written before per-subject encryption was introduced are plaintext and
   are not reachable by shredding. Retrofitting is a rewrite of history.
2. Every backup, replica, snapshot and downstream projection that captured
   plaintext, or that captured a decrypted value, is outside the key's reach. A
   projection that stores a decrypted email address survives the shred intact.
   This is the most common real defect.
3. A copy of the key in a secondary vault, a disaster-recovery region, or an
   engineer's local workstation defeats the deletion, since NIST requires all
   copies of the key to be sanitised.
4. Metadata is not encrypted and is often personal data on its own. That a
   subject identifier existed, when, and how often, remains legible after the
   shred, as the Rust sample demonstrates.

A further limit is legal rather than technical, and worth stating as such.
Whether a regulator accepts key destruction as erasure under Article 17 rather
than as pseudonymisation is a legal question that engineering cannot settle.
Article 17(3) also means erasure is not absolute. A financial ledger under a
statutory retention duty may fall within the legal-obligation exemption, which
is a legal determination, not an architectural one.

**Where this pattern is silent.** It says nothing about transport security,
authentication, or authorisation of commands. Those are the responsibility of
the surrounding architecture and are unaffected by the choice of storage model.

## 18. References

1. Martin Fowler. "Event Sourcing". Development of Further Patterns of
   Enterprise Application Architecture, 12 December 2005.
   https://martinfowler.com/eaaDev/EventSourcing.html
   Verified 2026-08-02. Source for the pattern name, the intent, rebuilding
   state by re-running the log, the snapshot remark, and the gateway separation
   for external effects.
2. Greg Young. *CQRS Documents*. Self-published, November 2010.
   https://cqrs.wordpress.com/wp-content/uploads/2010/11/cqrs_documents.pdf
   Verified 2026-08-02. Source for the past-tense event naming convention with
   the `CustomerRelocated` and `CargoShipped` examples (page 26), the reversal
   transaction and "There is no Delete" (page 31), and the rolling snapshot
   defined as a heuristic (page 33).
3. Gregory Young. *Versioning in an Event Sourced System*. Leanpub, 2017
   edition. https://leanpub.com/esversioning
   Verified 2026-08-02. Source for the schema-evolution topic list, including
   weak schema, double write, negotiation, copy and replace, and changing stream
   boundaries.
4. Microsoft. "Event Sourcing pattern". Azure Architecture Center, page dated
   2026-03-27.
   https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing
   Verified 2026-08-02. Source for the event store as system of record, write
   contention, materialized views, the four versioning strategies, snapshots as
   an optimisation rather than a replacement, the broker-is-not-an-event-store
   warning, idempotency, circular logic, given-when-then testing, and the
   personal-data and crypto-shredding guidance.
5. Martin Fowler. "The LMAX Architecture", 12 July 2011.
   https://martinfowler.com/articles/lmax.html
   Verified 2026-08-02. Source for the LMAX production use, state derivable from
   input events, journalling, the sub-minute restart from snapshot plus a day of
   journals, and the six million orders per second figure.
6. Kurrent. "Event streams". KurrentDB server documentation v25.0.
   https://docs.kurrent.io/server/v25.0/features/streams.html
   Verified 2026-08-02. Source for one stream per entity, and the statement that
   events cannot be selectively deleted from the middle of a stream.
7. AxonIQ. "Event Versioning". Axon Framework Reference 4.11.
   https://docs.axoniq.io/axon-framework-reference/4.11/events/event-versioning/
   Verified 2026-08-02. Source for event stores as read and append-only, the
   upcaster chain semantics, the four `RevisionResolver` implementations, and
   `SingleEventUpcaster` and `EventMultiUpcaster`.
8. JasperFx. "Event Versioning". Marten documentation.
   https://martendb.io/events/versioning.html
   Verified 2026-08-02. Source for Marten as a .NET library over PostgreSQL,
   compensation over changing past data, event type name mapping, and upcasting
   against old CLR types or raw JSON.
9. Amazon Web Services. "Event sourcing pattern". AWS Prescriptive Guidance,
   Modernizing data persistence.
   https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-data-persistence/service-per-team.html
   Verified 2026-08-02. Source for the Kinesis and EventBridge implementations,
   archive and replay, and the statement that Saga is required for cross-service
   consistency.
10. Cognitect. "Data Model". Datomic documentation.
    https://docs.datomic.com/whatis/data-model.html
    Verified 2026-08-02. Source for the immutable point-in-time database value,
    accumulation rather than modification, and assert, read, accumulate, retract.
11. Apache Software Foundation. "Use cases". Apache Kafka documentation.
    https://kafka.apache.org/uses
    Verified 2026-08-02. Source for Kafka's own statement on event sourcing as a
    use case and on the commit-log use with log compaction.
12. Debezium project. README. Debezium repository, main branch.
    https://raw.githubusercontent.com/debezium/debezium/main/README.md
    Verified 2026-08-02. Source for the CDC description, connectors monitoring an
    upstream database and recording row-level changes to Kafka topics, and only
    committed changes being visible.
13. European Union. Regulation (EU) 2016/679 (GDPR), Article 17, Right to
    erasure. https://gdpr-info.eu/art-17-gdpr/
    Verified 2026-08-02. Source for the Article 17(1) grounds and the Article
    17(3) exemptions.
14. Richard Kissel, Andrew Regenscheid, Matthew Scholl, Kevin Stine.
    *Guidelines for Media Sanitization*. NIST Special Publication 800-88
    Revision 1, December 2014.
    https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-88r1.pdf
    Verified 2026-08-02. Source for the Cryptographic Erase definition in
    section 2.6, and for the preconditions and prohibitions in sections 2.6.1
    and 2.6.2.
