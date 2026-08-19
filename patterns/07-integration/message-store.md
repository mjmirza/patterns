---
name: Message Store
slug: message-store
family: 07-integration
category: Enterprise Integration
aliases: [Message Log, Message Journal, Audit Store]
first_described: "Hohpe, Woolf 2003"
maturity: canonical
related: [wire-tap, control-bus, message-history, claim-check, guaranteed-delivery]
incompatible_with: []
verified: 2026-08-02
---

# Message Store

## 1. Name, aliases, and lineage

The canonical name is Message Store. It is documented as an Enterprise
Integration Pattern in Gregor Hohpe and Bobby Woolf, *Enterprise Integration
Patterns. Designing, Building, and Deploying Messaging Solutions*,
Addison-Wesley, 2003, ISBN 0-321-20068-3, in the System Management section of
the book. The publisher's own reference site lists the section membership
directly, grouping eight patterns under the heading "Systems Mgmt.", naming
Control Bus, Detour, Wire Tap, Message History, Message Store, Smart Proxy,
Test Message, and Channel Purger
([enterpriseintegrationpatterns.com, System Management patterns index](https://www.enterpriseintegrationpatterns.com/patterns/messaging/),
verified 2026-08-02). The book places this section after Message Routing,
Message Transformation, and Messaging Endpoints, and opens it with a worked
scenario, the "Systems Management Example," built around a loan broker system,
before walking through the individual patterns one at a time
([enterpriseintegrationpatterns.com, book table of contents](https://www.enterpriseintegrationpatterns.com/toc.html),
verified 2026-08-02).

The problem statement on the pattern's own reference page is worth quoting
directly, because it is the sentence that separates this pattern from a
generic database write. "The architectural principle of loose coupling allows
for flexibility in the solution, but can make it difficult to gain insight
into the dynamic behavior of the integration solution."
([enterpriseintegrationpatterns.com, Message Store](https://www.enterpriseintegrationpatterns.com/patterns/messaging/MessageStore.html),
verified 2026-08-02). The pattern exists specifically because loose coupling,
the property the rest of the catalog spends most of its pages earning,
produces a system where no single component holds the full picture of what has
happened. The solution the page describes is to capture message data in a
central repository, fed by a duplicate copy of each message routed to a
secondary channel, so the capture happens without slowing or coupling to the
main flow. The page names two mechanisms for producing that duplicate copy, an
automatic capability of the messaging infrastructure or, more commonly, a
Wire Tap, and it states plainly that the secondary channel is meant to operate
fire-and-forget so the store's own performance cannot become the main flow's
performance problem.

The name is stable across implementations more than most patterns in the
catalog. Spring Integration's persistence abstraction is literally named
`MessageStore`, and its reference documentation states outright that the
interface "implements the Enterprise Integration Patterns (EIP) message store
pattern"
([docs.spring.io, Spring Integration Reference, Message Store](https://docs.spring.io/spring-integration/reference/message-store.html),
verified 2026-08-02), which is the strongest possible confirmation that the
canonical name survived into production tooling unchanged. Two informal terms
circulate in day-to-day engineering conversation for the same idea, message
log and message journal, and a third, audit store, is used when the emphasis
is on compliance rather than diagnosis. None of the three is a term of art
tied to a specific publication the way Message Store is, and this entry treats
them as working synonyms rather than sourced aliases, a distinction worth
naming plainly because a search for "message log" in a vendor's documentation
often turns up something closer to a transport-level delivery log than the
correlation-aware repository the EIP catalog describes.

## 2. Problem and context

A messaging system built well is, by design, hard to see into from any one
place. A message travels a Point-to-Point Channel or Publish-Subscribe
Channel, is picked up by a Message Endpoint, transformed, routed, split,
aggregated, and eventually lands somewhere, and at no point in that chain does
any single component hold a record of the full path end to end. That is exactly the
property loose coupling is meant to deliver, each component knows only its
own inputs and outputs. The cost of that property is that a question an
operator or a business analyst asks constantly, did message X ever reach
system Y, how long did order 42 take to clear the pipeline, which messages
touched the discount-calculation service today, has no component whose job it
is to answer.

The situation shows up first as an incident-response problem. A support ticket
says a customer's order never confirmed. Answering it means an engineer opens
a terminal, greps log files across however many services the message passed
through, tries to line up timestamps across clocks that may not be perfectly
synchronized, and reconstructs the path by hand. That reconstruction is slow
exactly when speed matters, and it does not scale past a handful of hops. The
same gap shows up a second time as a reporting problem once the system is
stable, when the business wants a dashboard of message volumes by type, by
partner, by hour, and nobody owns data that answers it because no component
in the loosely coupled design was ever asked to be a system of record for
"messages that passed through here."

The context in which Message Store is the right answer has three parts, each
of which the book's related patterns supply half of. First, the coupling must
genuinely be loose, meaning there is no existing choke point through which
every message already flows and could be inspected without a change. Second,
the question being answered is about the messaging traffic itself, its
existence, its timing, its routing, and its correlation, not about the
business state the messages cause downstream, which is a separate concern
covered by application-level persistence rather than this pattern. Third, the
answer needs to survive the individual messages that produced it, which is
what distinguishes this pattern from simply reading the current contents of a
queue, because a queue drains and a Message Store does not.

## 3. Forces

The pattern balances the following competing pressures, and states plainly
which side of each it favors.

- **Coupling to the main flow.** Strongly favored toward decoupling. The
  entire design of the pattern, a secondary channel fed by a Wire Tap, exists
  to keep the store's presence, performance, and even its outages invisible to
  the primary path. This is the one force the pattern is unwilling to trade
  away, because a store that can slow delivery defeats the reason it was
  built.
- **Latency added to delivery.** Close to zero when built as described. The
  secondary write happens off the critical path, so the honest cost sits
  elsewhere, in the write amplification on whatever infrastructure carries the
  tapped copy, not in the time a consumer waits for its message.
- **Storage cost and growth.** Sacrificed unless actively managed. A store fed
  continuously by production traffic grows without bound by default, and the
  pattern's own guidance, capture selected data rather than full message
  contents, is a direct response to this force rather than a stylistic
  preference.
- **Query flexibility and freshness.** Favored, and this is the pattern's
  actual payoff. A well-indexed store answers a "where has this correlation id
  been" question in milliseconds against a purpose-built schema, versus
  minutes of hand correlation against raw logs.
- **Consistency between the store and reality.** Sacrificed, honestly and by
  design in the canonical form. Because the tap is fire-and-forget, the store
  can lag the main flow, drop a record under a genuine infrastructure failure,
  or record a message that the main flow later fails to deliver. Treating the
  store as strongly consistent with delivery state is a misuse this entry
  returns to in dimension 11.
- **Operational visibility.** Strongly favored. This is the force the pattern
  exists to serve, at the direct expense of the consistency force above.
- **Team topology.** Favored for platform teams. A shared store owned by a
  platform or SRE team gives every product team the same diagnostic surface
  without each team building its own, at the cost of a shared dependency that
  now needs its own on-call ownership.
- **Data governance and privacy exposure.** Sacrificed unless the capture is
  scoped deliberately. Copying message data into a second repository outside
  the original channel's access boundary widens the attack surface and the
  compliance surface at the same time, covered in full in dimension 17.

A pattern that gave up nothing would not need a name. The price here is paid
mostly in storage discipline and in the temptation to treat a diagnostic
side-channel as if it were authoritative.

## 4. Applicability and non-applicability

Reach for Message Store when the following hold.

- Operators or analysts need to answer questions about message traffic, where
  has it been, how long did it take, how often does it happen, and no
  existing component in the flow is positioned to answer them without a
  design change.
- The messaging infrastructure is genuinely loosely coupled, so there is no
  single chokepoint that already sees every message and could be queried
  directly.
- The question is about the messages, their existence, routing, and timing,
  not about the business state those messages caused. A store of orders is
  application persistence. A store of the order messages that flowed through
  the integration layer is this pattern.
- Diagnostics and reporting must not be allowed to affect delivery reliability
  or latency, which is the case in essentially every production messaging
  system, and is why the fire-and-forget secondary channel is not an optional
  detail of the pattern but its central design decision.
- Compliance or contractual obligations require evidence that a message was
  sent or received, independent of whether the downstream business
  transaction it triggered eventually succeeded.

Do not reach for Message Store in the following cases, and the reason matters
more than the rule. This is the non-applicability list the pattern most often
ships without.

- **The system already has one chokepoint every message passes through.** A
  synchronous request-response gateway, a single API layer, or a monolith
  with one persistence layer already has a natural place to log message
  metadata as a side effect of existing code. Standing up a separate tap and
  store duplicates infrastructure that a single log statement in the existing
  chokepoint would replace.
- **The real need is exactly-once business state, not diagnostics.** If the
  goal is preventing a handler from running twice for the same message, the
  correct pattern is an idempotent receiver keyed by message id inside the
  business logic itself, not a side store that merely observes traffic. A
  Message Store answers "did this happen," it does not by itself prevent
  anything from happening twice.
- **The organization needs full replay-grade history to rebuild application
  state.** That is Event Sourcing's job, described by Martin Fowler as
  capturing all changes to application state as a sequence of events so state
  can be reconstructed by replay
  ([martinfowler.com, Event Sourcing, published 2005-12-12](https://martinfowler.com/eaaDev/EventSourcing.html),
  verified 2026-08-02). Message Store captures metadata about messages for
  diagnosis and reporting, not a complete, replayable log of every state
  transition, and treating the two as interchangeable is the single most
  damaging misuse this entry documents in dimension 11.
- **A distributed tracing system already covers the same ground.** Once an
  organization has adopted end-to-end tracing with correlation propagated
  across every hop, a bespoke Message Store answering "where has this message
  been" is often redundant with data the tracing backend already holds, and
  building a second system to answer the same question is waste rather than
  resilience.
- **The volume is too low to justify the operational cost.** A system
  handling dozens of messages a day can be diagnosed by reading the handful
  of log lines directly. The pattern earns its keep at a volume where manual
  correlation has already become painful, not before.
- **The traffic includes data that cannot leave its original system of
  record.** When regulatory or contractual constraints forbid a second copy of
  certain fields existing anywhere, the pattern's core mechanism, a duplicate
  copy routed to a second channel, is the wrong shape regardless of how
  carefully it is implemented, and the fix is to redesign what gets tapped,
  not to build the store anyway and lock it down after the fact.

## 5. Structure

Four participants, named by the role each plays rather than by a generic class
name.

- **Original Channel.** The Message Channel already carrying production
  traffic between the real sender and the real receiver. It is unaware the
  pattern exists, which is the whole point.
- **Tap.** The component that produces the duplicate copy. Most commonly a
  Wire Tap inserted into the Original Channel, occasionally a native
  capability of the messaging middleware itself when the platform exposes one.
  The tap's contract is fire-and-forget, its own failure or slowness must
  never be visible on the Original Channel.
- **Secondary Channel.** A dedicated Message Channel that exists only to carry
  the tapped copies to the store. Isolating it from the Original Channel is
  what makes the fire-and-forget guarantee enforceable, because back-pressure
  on the secondary channel has nowhere to propagate back to.
- **Message Store.** The repository itself, which receives entries from the
  Secondary Channel, persists selected fields from each, indexes them for the
  queries operators actually run, correlation id, channel, time range, status,
  and exposes a read path independent of the messaging system, usually a
  query API, a report, or a dashboard.

The relationships worth naming explicitly. The Original Channel has no
association with the Message Store at all in the canonical design, its only
relationship is with the Tap, and the Tap is the sole component that knows the
store exists. This one-way visibility is what keeps the pattern from becoming
a second point of failure for delivery, and it is the structural property most
implementations quietly abandon under time pressure, discussed in dimension 11.

## 6. ASCII structure diagram

```
                          Original Channel
        Sender  ------------------------------------->  Receiver
                          |
                          | duplicate copy (fire-and-forget)
                          v
                        [ Tap ]  (Wire Tap or native tap)
                          |
                          | Secondary Channel
                          v
                  +-------------------+
                  |   Message Store   |
                  |-------------------|
                  | selected fields   |
                  | correlation id    |
                  | channel, time     |
                  | status            |
                  +-------------------+
                          ^
                          | query
                          |
                 +-----------------+
                 | Operator report |
                 | or dashboard    |
                 +-----------------+

  The Original Channel has no dependency on the Tap or the Store.
  Only the Tap knows the Store exists. Delivery cannot be slowed
  by anything downstream of the dashed duplicate-copy path.
```

## 7. Dynamics

The runtime flow separates cleanly into two independent timelines that share
only their starting point. A sender puts a message on the Original Channel.
From that instant, the message's delivery to the real receiver and its
capture into the store proceed as two unrelated sequences, and neither one
should be able to observe or block the other.

```
Sender        Original Channel      Tap            Secondary Ch.   Store
  |                  |                |                  |           |
  |-- send(msg) ---->|                |                  |           |
  |                  |-- deliver ---->| (copy produced)   |           |
  |                  |                |-- record(meta) -->|          |
  |                  |                |     (async,       |          |
  |                  |                |      fire and     |          |
  |                  |                |      forget)      |          |
  |                  |-- to Receiver -------------------------------->|
  |                  |   (unaffected  |                  |           |
  |                  |   by Tap path) |                  |           |
  |                  |                |                  |-- write ->|
  |                  |                |                  |           |
Receiver                                                             Report
  gets message,                                                      queries
  Tap's outcome                                                      Store
  never reaches it                                                   later
```

Two timing properties are worth stating plainly because they are exactly the
properties the failure modes in dimension 11 violate. First, the write to the
Store can complete before, after, or never relative to the message reaching
the real Receiver, there is no ordering guarantee between the two paths in the
canonical design, which is why the Store must never be read as evidence that
delivery succeeded. Second, if the Secondary Channel or the Store is down, the
correct behavior is that entries queue, retry, or are dropped according to
whatever policy the Secondary Channel implements on its own, none of which is
visible on the Original Channel. A Tap implementation that throws back onto
the sender when the Store is unreachable has reintroduced the coupling the
pattern exists to avoid.

## 8. Implementation variants

**Metadata-only tap-fed store.** The canonical form as described by the book,
a Wire Tap captures selected fields, correlation id, message id, channel,
timestamp, and status, and writes them to a store that never holds the full
message body. This keeps storage growth bounded by field count rather than
payload size and is the safest default from a privacy standpoint, discussed
further in dimension 17.

**Full-payload capture.** Some implementations tap the complete message,
usually to support replay-driven debugging where an engineer needs to
re-inspect the exact bytes a service received. This trades the storage and
privacy discipline of the metadata-only form for debugging power, and is the
variant most likely to drift into unmanaged growth if adopted without an
explicit retention policy.

**In-memory development store.** Spring Integration's `SimpleMessageStore` is
this variant, an in-memory implementation intended for development and
low-volume scenarios rather than production persistence
([docs.spring.io, Spring Integration Reference, Message Store](https://docs.spring.io/spring-integration/reference/message-store.html),
verified 2026-08-02). It is the correct choice for local testing and the
wrong choice the moment the process can restart and lose the record without
anyone deciding that was acceptable.

**Relational-backed durable store.** Spring's `JdbcMessageStore` persists to
an RDBMS, giving the store the same durability and query tooling as the rest
of an organization's operational data, at the cost of write throughput
compared to a purpose-built log store
([docs.spring.io, Spring Integration Reference, Message Store](https://docs.spring.io/spring-integration/reference/message-store.html),
verified 2026-08-02).

**Key-value and document-backed stores.** The same framework ships
`RedisMessageStore`, `MongoDbMessageStore`, and `HazelcastMessageStore`
variants, trading relational query power for horizontal write scale and, in
Hazelcast's case, colocated in-memory access from the same cluster running the
integration flows
([docs.spring.io, Spring Integration Reference, Message Store](https://docs.spring.io/spring-integration/reference/message-store.html),
verified 2026-08-02).

**Managed, TTL-bounded object store.** MuleSoft's Object Store v2 is a general
key-value persistence service that CloudHub applications use to store data
and state across flows, and it applies retention automatically rather than
requiring the application to implement eviction. It supports a rolling
thirty-day time-to-live, where access during the last seven days of the
window extends the window by another thirty days, or a static time-to-live
depending on version, and enforces a hard maximum of thirty days from
creation regardless of access pattern
([docs.mulesoft.com, Object Store](https://docs.mulesoft.com/object-store/),
verified 2026-08-02). This is the variant that treats retention as a platform
guarantee rather than an application concern, which removes an entire class
of the unbounded-growth failure mode described in dimension 11 at the cost of
losing anything an operator did not query inside the window.

**Transactional outbox variant.** NServiceBus's Outbox writes the outgoing
message record into the same database transaction as the business data
change that produced it, rather than via an asynchronous tap after the fact,
and deduplicates by message id so a redelivered message is recognized rather
than reprocessed
([docs.particular.net, NServiceBus Outbox](https://docs.particular.net/nservicebus/outbox/),
verified 2026-08-02). This inverts the canonical structure's independence
between the store write and delivery, trading the fire-and-forget decoupling
force for a stronger consistency guarantee, an honest and named trade rather
than an accident, and it is why this entry treats the Outbox as a specialized
sibling of Message Store rather than the same pattern, covered further in
dimension 13.

**Sampling variant.** At volumes where capturing every message is
prohibitively expensive, some production stores capture a statistical
sample, one message in N, or every Nth second, sacrificing completeness for
a bounded write rate. This is a reasonable trade for trend reporting and a
dangerous one for anything an incident responder might rely on, because the
exact message they need is exactly the one likeliest to have been skipped.

**Read-model projection variant.** Rather than storing raw entries, the tap
feeds an incremental aggregation, current in-flight count by channel, running
totals by hour, directly into a queryable projection. This gives dashboards
constant-time reads at the cost of losing the ability to answer a question
the projection was not built to answer, the opposite trade from the raw-record
forms above.

## 9. Known production uses

**Spring Integration's `MessageStore` abstraction.** The framework's own
documentation states that the interface implements the EIP message store
pattern directly, and it is used by more than one internal component, not
only as a standalone diagnostic tap. A `QueueChannel` can be backed by a
`MessageStore` so buffered messages survive a restart, an Aggregator uses a
`MessageGroupStore`, a specialization of the interface, to persist the
partial groups of messages it is waiting to complete, a Delayer uses it to
persist messages waiting out their delay, and the Claim Check pattern uses
it to hold the payload a claim check ticket refers to
([docs.spring.io, Spring Integration Reference, Message Store](https://docs.spring.io/spring-integration/reference/message-store.html),
verified 2026-08-02). This is a real system generalizing the book's narrow
monitoring-store definition into a shared persistence abstraction reused by
several other patterns in the same catalog, which is the clearest evidence
available that the pattern's shape, not just its diagnostic intent, is
independently useful. The same documentation warns that only `Serializable`
message headers survive the default serialization path, and that framework
headers such as the reply channel and error channel are not serializable by
default and can lose their identity across a restart unless a
`HeaderChannelRegistry` converts them to string references first, a concrete,
sourced instance of the failure mode covered in dimension 11.

**MuleSoft Object Store v2.** CloudHub applications built on Mule use Object
Store v2 to persist data and state across batch processes, Mule components,
and applications, accessible either from within a running application or
through the Object Store REST API
([docs.mulesoft.com, Object Store](https://docs.mulesoft.com/object-store/),
verified 2026-08-02). The documentation does not use the Hohpe and Woolf
terminology directly, and Object Store is a general key-value service rather
than a component badged as an implementation of this specific EIP, but it is
the concrete infrastructure Mule flows reach for when they need exactly what
this pattern describes, per-message state keyed by an identifier, encrypted
to FIPS 140-2 compliant standards, transported over end-to-end TLS, with a
managed retention window rather than an application-owned eviction loop.

**NServiceBus Outbox.** Particular Software's messaging framework for .NET
persists identification data for every processed message alongside its
outgoing messages in the same database transaction as the business data
change that produced them, deduplicating by message id so a message retried
after a transient failure is recognized as already handled rather than
reprocessed a second time
([docs.particular.net, NServiceBus Outbox](https://docs.particular.net/nservicebus/outbox/),
verified 2026-08-02). It supports Azure Table, CosmosDB, DynamoDB, MongoDB,
NHibernate, RavenDB, and SQL Server as storage backends, and each backend
allows the retention duration and cleanup interval to be tuned independently.
This is named here as a specialized production instance rather than a direct
citation of the EIP term, because NServiceBus frames the feature around
exactly-once processing guarantees rather than diagnostics, which is exactly
the transactional-consistency trade documented as a distinct implementation
variant in dimension 8.

**The Enterprise Integration Patterns reference implementations.** The
pattern's own site documents Wire Tap as the mechanism most commonly used to
produce the duplicate copy the store consumes, and cross-references Control
Bus as the channel type typically used to carry administrative traffic
including monitoring data of this kind, and Message History as a related,
narrower mechanism that travels with the message rather than living in a
separate repository
([enterpriseintegrationpatterns.com, Message Store](https://www.enterpriseintegrationpatterns.com/patterns/messaging/MessageStore.html),
verified 2026-08-02). While the site itself is documentation rather than a
running system, it is cited here as the canonical description every one of
the implementations above independently converges on, which is itself
evidence the pattern names something real rather than an artifact of one
framework's design choices.

## 10. Consequences

Positive consequences.

- Diagnostic and reporting questions about message traffic get a
  purpose-built answer instead of ad hoc log correlation, turning a task that
  took an engineer minutes to hours into a query that takes milliseconds.
- The main flow's delivery latency and reliability are unaffected by the
  store's own performance, availability, or maintenance windows, when the
  fire-and-forget structure is respected.
- A shared store gives every team in an organization the same diagnostic
  surface without each team building and maintaining its own, which is the
  team-topology payoff named in dimension 3.
- The store is additive infrastructure. It can be introduced into an
  existing system, and removed from one, without touching the code of the
  components that produce and consume the messages themselves, covered in
  full in dimension 14.

Negative consequences.

- A second copy of message data now exists outside the access boundary of
  the original channel, which is a governance and security surface that did
  not exist before, covered in dimension 17.
- Storage grows continuously under production traffic and requires an
  explicit retention decision, not an assumption that someone will notice
  before it becomes a cost or compliance problem.
- The store's data can lag, miss, or duplicate relative to what actually
  happened on the main channel, because the write path is deliberately
  decoupled from delivery, and any consumer that forgets this and treats the
  store as authoritative inherits a subtle correctness bug.
- The pattern adds one more piece of infrastructure, a tap, a channel, and a
  store, each with its own operational ownership, monitoring, and failure
  modes, for a system that previously had none of the three.

## 11. Failure modes and misuse

**Symptom.** During an incident, two engineers query the store and get
contradictory answers about whether a business transaction completed.
**Cause.** The store, which was built and fed as a fire-and-forget
diagnostic side-channel, is being treated as an authoritative Event Store
capable of replaying and reconstructing application state, a role it was
never designed to fill. The two patterns share a superficial shape, a log of
things that happened, and that similarity is exactly what invites the
confusion.
**Fix.** Draw the boundary explicitly in documentation and access control,
the Message Store answers diagnostic and reporting questions, and if the
organization genuinely needs replay-grade state reconstruction, adopt Event
Sourcing with its own store as the actual system of record
([martinfowler.com, Event Sourcing](https://martinfowler.com/eaaDev/EventSourcing.html),
verified 2026-08-02), rather than stretching the diagnostic store to cover
both jobs.

**Symptom.** Delivery throughput on a channel degrades or stalls whenever
the store's database is slow, and the correlation is reproducible.
**Cause.** The tap was wired synchronously into the main path instead of
through a genuinely independent secondary channel, so the store's own
latency loads directly onto the critical path, exactly the coupling the
canonical design exists to prevent.
**Fix.** Reinstate the fire-and-forget contract, a Wire Tap or a
message-driven consumer reading from its own queue, so the store's slowness
has physically nowhere to propagate back to the sender.

**Symptom.** A managed store's billed storage size, or an on-premises
store's disk usage, grows continuously and is discovered only when a quota
or budget alert fires.
**Cause.** No retention policy was defined, the tap captures full message
payloads rather than the selected metadata the pattern describes, and no
eviction mechanism runs against the growing table.
**Fix.** Store only correlation-relevant fields by default, and apply an
explicit retention window, following the precedent set by MuleSoft's rolling
or static time-to-live model
([docs.mulesoft.com, Object Store](https://docs.mulesoft.com/object-store/),
verified 2026-08-02) or by periodically evicting message groups the way
Spring's `MessageGroupStore` APIs support.

**Symptom.** An audit report shows the same message recorded twice with two
different timestamps, and a business user assumes it means the message was
sent twice.
**Cause.** The Secondary Channel delivers at-least-once, which is normal,
but the write into the store is not idempotent, there is no unique
constraint on message id, so a redelivered tap entry inserts a second row
instead of being recognized as a duplicate.
**Fix.** Key the write on message id and make it an upsert rather than an
insert, the same design NServiceBus applies for its own deduplication
guarantee
([docs.particular.net, NServiceBus Outbox](https://docs.particular.net/nservicebus/outbox/),
verified 2026-08-02).

**Symptom.** A security or compliance review finds personal data inside the
store that nobody remembers deciding to put there.
**Cause.** The tap was configured once to capture the full message body "in
case it's useful later," and a schema change upstream later added a
customer-identifying field to that same payload, which then flowed silently
into the store with every subsequent message.
**Fix.** Enforce an explicit, reviewed allow-list of captured fields and
headers at the tap, and treat any schema change to the tapped message type
as an event that re-triggers a review of what the tap now captures.

**Symptom.** A query against the store during a live postmortem takes
minutes and eventually times out, at the exact moment its answer is most
needed.
**Cause.** The store was built as an append-only log with no index on the
fields operators actually query by, correlation id, channel, and time
range, which was invisible at low volume and only surfaced once production
traffic grew.
**Fix.** Index on the real query keys from the start, matching what
Spring's `JdbcMessageStore` and `MessageGroupStore` do by design, and for
very large groups use a streaming or lazy-load read path rather than
materializing the entire result set, a capability Spring added specifically
because eager loading of large groups measured a roughly ninety-three
percent slower read path than the streaming alternative in its own
reference documentation
([docs.spring.io, Spring Integration Reference, Message Store](https://docs.spring.io/spring-integration/reference/message-store.html),
verified 2026-08-02).

## 12. Trade-off matrix

The comparison below is against named alternatives that solve an adjacent
problem, not against a strawman of doing nothing.

| Force | Message Store | Wire Tap alone, no store | Message History | Claim Check | Event Sourcing |
|---|---|---|---|---|---|
| Coupling to main flow | Decoupled by design, async secondary channel | Decoupled, but produces no durable answer by itself | Zero external coupling, rides inside the message | Decoupled, but exists to defer payload transport, not diagnostics | Often becomes the primary write path, tightly coupled to the domain |
| Persistence and queryability | Durable, independently queryable across all messages | None, the tap alone has no memory | Ephemeral, exists only for the life of one message | Durable, but keyed for single-payload retrieval, not cross-message reporting | Durable and the authoritative source of truth for state |
| Cross-message correlation | Strong, purpose-built for it | None | Weak, only sees the one message's own path | None | Strong, but scoped to one aggregate's own event stream |
| Storage cost | Grows continuously, needs a retention policy | None | Negligible, a few bytes per message | Bounded by payload size and its own retention | Grows without bound by design, replay is the point |
| Operational overhead | One more owned system, tap plus channel plus store | Minimal, one interceptor | Minimal, a header field | Moderate, a store plus a claim check retrieval flow | High, requires snapshotting and replay tooling to stay usable |
| Fitness for exactly-once guarantees | Not designed for it, diagnostic only | Not applicable | Not applicable | Not applicable | Strong, when combined with idempotent projections |

## 13. Related and incompatible patterns

**Wire Tap.** The two are frequently confused because most Message Store
implementations use exactly one Wire Tap as their feed mechanism, but they
answer different questions. Wire Tap is the interception mechanism, how to
get a copy of this message without disturbing its delivery, and Message
Store is the destination and the query surface that copy feeds, what to do
with the copies once they exist. A Wire Tap with no store behind it produces
copies nobody can later ask a question of, and a Message Store fed by
anything other than a properly decoupled tap reintroduces exactly the
coupling risk documented in dimension 11.

**Control Bus.** The book positions Control Bus as the administrative channel
type typically used to carry monitoring and management traffic across a
distributed messaging system, and a Message Store's Secondary Channel is
often, though not necessarily, implemented as traffic on that same
administrative bus. The two compose naturally, the Control Bus is the
transport, the Message Store is one of the things riding on it, alongside
health checks and configuration commands that have nothing to do with
message capture.

**Message History.** The closer sibling by intent, both exist to answer what
happened to this message on its way through the system. The difference is
where the data lives. Message History accumulates a record of hops directly
inside the message itself, typically as a growing header, and travels with
it, ephemeral and local. Message Store externalizes the same kind of
information into a durable, independently queryable repository. A system can
use both together, Message History for a receiver to answer how a message
got to it without a lookup, and Message Store for an operator to answer how
a message got anywhere after the fact, and the two do not conflict because
they solve the question from opposite ends, the message's own perspective
versus an external observer's.

**Claim Check.** Both patterns route a copy or a token into a side channel
and persist it externally, and both trade payload visibility for a smaller
footprint on the main channel. The intents diverge sharply past that surface
similarity. Claim Check exists to move a large payload out of the main flow
temporarily and hand back a reference so the payload can be reclaimed later
by the same or a downstream component, it is a transport optimization.
Message Store exists to keep a permanent, queryable diagnostic record, it is
an observability mechanism, and it typically stores less data per message,
not more, than the original payload. Building a store that also serves as a
claim check backing store, as Spring's `MessageStore` interface does, is a
legitimate implementation choice, but conflating the two intents in a design
document produces a component nobody can reason about, because a
store-everything requirement for both retrieval and diagnostics inherits the
worst constraints of each.

**Transactional Outbox (NServiceBus's specialized instance).** Named
separately from the canonical pattern in dimension 8 because it inverts the
core structural decision, writing synchronously in the same transaction as
business data rather than asynchronously through a tap. It is compatible
with Message Store in the sense that both persist a record of a message, and
it is a distinct pattern in the sense that its consistency guarantee is
exactly the property the canonical Message Store deliberately does not
provide, so a team choosing between them should choose based on whether they
need diagnostic visibility, this pattern, or exactly-once delivery
guarantees, the outbox variant, and understand that picking one does not
substitute for the other.

**Guaranteed Delivery.** Not a competitor and not a substitute. Guaranteed
Delivery is concerned with the message actually arriving, persisting it at
each hop so a crash does not lose it. Message Store is concerned with
someone being able to ask, after the fact, whether it did. A system can have
perfect guaranteed delivery and zero diagnostic visibility, or the reverse,
and most production systems that mature past their first incident end up
wanting both.

**Incompatibilities.** No pattern in this catalog is structurally
incompatible with Message Store, because it is additive infrastructure that
observes traffic rather than participating in delivery. The closest thing to
an incompatibility is philosophical rather than structural, a system whose
architecture forbids any second copy of message data existing anywhere, a
real constraint in some regulated environments, rules out the pattern's core
mechanism regardless of implementation care, as noted in dimension 4.

## 14. Refactoring path in and out

Introducing the pattern into a system that does not yet have it follows a
sequence, each step independently valuable and independently revertible.

1. **Name the recurring question first.** The trigger is usually an incident
   retrospective or a recurring support escalation where the answer required
   grepping logs across services. Write down the exact question, "did message
   X reach system Y," "how long did correlation id Z take end to end," before
   choosing any implementation, because the answer determines what fields the
   tap needs to capture.
2. **Identify the minimal captured schema.** Resist capturing the full
   payload on the first pass. Message id, channel, correlation id, timestamp,
   and a status field cover the large majority of diagnostic questions, and
   starting narrow keeps the privacy and storage forces from dimension 3 in
   check from day one.
3. **Insert the tap without touching the producer or consumer.** In a
   framework that already models channels as first-class objects, this is
   often a configuration change rather than a code change, for example
   attaching a `message-store` reference to an existing Spring Integration
   `QueueChannel` or wrapping a channel with an interceptor rather than
   editing the components that send and receive on it
   ([docs.spring.io, Spring Integration Reference, Message Store](https://docs.spring.io/spring-integration/reference/message-store.html),
   verified 2026-08-02). Where no such framework support exists, add a Wire
   Tap as a new component in front of the existing channel rather than
   modifying the channel's own code.
4. **Choose a storage backend matched to the actual query pattern, not the
   biggest hammer available.** An in-memory store is correct for local
   development. A relational or document store is correct once the data
   must survive a restart and be queried by more than one field. A managed,
   TTL-bounded object store is correct when the team does not want to own
   retention logic at all.
5. **Build the read path deliberately.** Do not leave the store as a table
   only accessible by hand-written SQL. A small query API or dashboard is
   what makes the store actually get used, versus becoming a write-only
   system nobody remembers exists six months later.
6. **Add retention before volume becomes a problem, not after.** Set a TTL
   or eviction policy at the same time the store goes into production,
   following the precedent of a managed rolling window rather than waiting
   for a storage alert to force the decision under pressure.

Removing the pattern, when it has stopped earning its place, is close to the
reverse of step 3 and nothing else, precisely because the canonical structure
never let the store's presence leak into the producer or consumer's code.

1. **Confirm nothing downstream silently promoted the store to a system of
   record.** This is the one check that cannot be skipped, because the
   failure mode named first in dimension 11 is exactly a consumer that
   started treating the diagnostic store as authoritative. Search for any
   code or report that reads from the store to drive a business decision
   rather than a diagnostic one, and migrate that consumer to a proper
   source of truth before removing anything.
2. **Remove the tap, not the underlying channel type.** Detaching a
   `message-store` reference, or deleting a Wire Tap component, is a
   configuration-level change with no effect on delivery, because the
   Original Channel never had a dependency on the tap in the first place,
   per dimension 5.
3. **Archive or drop the store's data according to whatever retention or
   legal-hold obligation applies**, rather than deleting it reflexively,
   since an audit or compliance record may have already been built on top
   of data the store captured.

## 15. Testing and verification

Testing code that surrounds a Message Store splits cleanly into testing the
decoupling boundary and testing the store's own read and write behavior, and
conflating the two produces tests that pass for the wrong reason.

**Testing the fire-and-forget contract.** The property under test is that
the Original Channel's behavior is unaffected by the store's health. Write
a test double, a `RecordingMessageStore` that captures calls in memory with
no I/O, for asserting whether a message was recorded in ordinary unit
tests, and a second, fault-injecting double that throws or blocks on every
write, wired into an integration test that asserts message delivery on the
main channel completes successfully and within its normal latency budget
regardless. A test suite that only ever exercises the happy-path double has
not actually verified the decoupling the pattern exists to provide.

**Testing idempotency.** Replay the identical message, same message id,
twice through the tap and assert the store contains exactly one record
afterward, not two, which is the direct regression test for the
duplicate-write failure mode named in dimension 11. This test is cheap to
write and catches the most common defect in hand-rolled store
implementations, a plain insert where an upsert was required.

**Testing retention.** Inject a controllable clock rather than relying on
real elapsed time, write an entry, advance the clock past the configured
TTL, and assert the entry is gone on the next read or eviction pass. A
retention test that sleeps in real time for the actual TTL duration is both
slow and, past a certain window length, not something a CI pipeline can run
at all.

**Testing the query path.** Once the store exists, test it like an
ordinary repository, given a known set of writes, assert that a query by
correlation id, by channel, or by time range returns exactly the expected
records, no more and no fewer. This class of test is independent of the
messaging plumbing entirely and should not require a running broker or
channel to execute.

**What becomes harder to test.** Strict ordering between the tap's write
and the message's arrival at the real receiver is not guaranteed by the
canonical design, per dimension 7, so a test that asserts the store's
record always exists before, or always exists after, the receiver
processes the message is testing a property the pattern never promised,
and will be flaky by construction rather than by accident. The honest fix
is to test each path's own guarantees independently rather than asserting
an interleaving order across them.

## 16. Observability signals

A healthy Message Store is visible on its own dashboard, distinct from the
dashboard for the messaging system it observes, because conflating the two
hides exactly the kind of silent tap failure this pattern is meant to catch
for everything else.

- **Store write latency and error rate**, measured from the tap or the
  Secondary Channel's perspective, not the main channel's. A rising error
  rate here should page the team that owns the store, and must never be
  allowed to affect the main channel's own error budget.
- **Completeness ratio**, the count of messages seen on the Original Channel
  over a window compared to the count of records that landed in the store
  over the same window. A completeness ratio drifting below one hundred
  percent is the earliest, quietest signal that the tap is silently dropping
  entries, and it is invisible from the main channel's own metrics by
  design, which is why it needs its own alert rather than relying on
  someone noticing a gap during an incident.
- **Store lag**, the time between a message's send timestamp and its
  record's commit timestamp in the store, tracked as a distribution rather
  than a single average, since the tail is where an operator's trust in the
  store during an incident actually lives.
- **Storage growth rate and eviction rate**, tracked together so a
  retention policy's effectiveness is visible, a store whose growth rate
  exceeds its eviction rate is heading toward the unbounded-growth failure
  mode named in dimension 11 well before it becomes a budget or quota
  incident.
- **Query latency and query volume against the store itself**, since the
  store's entire reason for existing is to be queried, and a store nobody
  queries, or one whose queries are consistently slow, has quietly stopped
  earning the operational cost it carries.
- **Duplicate-record rate**, a direct measure of whether the idempotency
  guarantee named in dimension 8 and tested in dimension 15 is holding in
  production, distinct from and more actionable than the completeness ratio
  above.

## 17. Security and privacy implications

Persisting a copy of message traffic outside the original channel's access
boundary is, by definition, an expansion of the system's attack surface and
its data-governance surface at the same time, and the pattern's own guidance
to capture selected fields rather than full payloads is a direct response to
that fact rather than a performance optimization.

The store needs its own access control, separate from the Original
Channel's, because a Message Store aggregates cross-flow correlation data
that is not visible from inspecting any single channel in isolation, order
volumes by partner, timing patterns between two systems, the existence of a
business relationship inferable from correlation ids alone. An
unauthenticated or loosely authenticated query API onto the store is
therefore an information disclosure risk even when no individual message
field it stores is sensitive by itself, because the aggregate view can leak
business intelligence a single message never could.

When the store captures any part of the message payload rather than pure
metadata, it inherits the same data classification obligations the original
message carried, and it must be covered by whatever data retention and
right-to-erasure processes govern the source system. A field that a schema
change silently added to the tapped payload, the exact scenario in the
fifth failure mode of dimension 11, is a real, recurring way personal data
ends up somewhere a compliance review does not expect it. MuleSoft's Object
Store v2 addresses part of this surface directly at the infrastructure
level, applying encryption to FIPS 140-2 compliant standards and end-to-end
TLS in transit
([docs.mulesoft.com, Object Store](https://docs.mulesoft.com/object-store/),
verified 2026-08-02), which handles data at rest and in transit but does not
by itself constrain what an application chooses to put into the store,
which remains an application-level decision no infrastructure control can
make for the team.

The write path deserves the same append-only discipline an audit log
requires elsewhere in a system, because a store an operator or an attacker
can silently edit after the fact is worthless as evidence during an
investigation, regardless of how faithfully it captured events at write
time. Where the store is used to support compliance obligations, write
access should be restricted to the tap's own service identity, and any
operational process that needs to correct bad data should append a
correction record rather than mutate history in place, the same discipline
the Event Sourcing literature applies for the same reason, correcting
errors by appending a reversing event rather than editing the log
([martinfowler.com, Event Sourcing](https://martinfowler.com/eaaDev/EventSourcing.html),
verified 2026-08-02).

## Code examples

Three implementations below show three of the variants named in dimension 8,
an in-memory store wired behind a synchronous stand-in for a Wire Tap, a
transactional durable store backed by an embedded relational database
mirroring the JDBC variant, and a bounded, TTL-evicting store mirroring the
managed object store variant. Each is self-contained and was checked
against its own toolchain, TypeScript against `tsc --strict`, Python
against `py_compile`, and Go against `go vet`.

### TypeScript

```typescript
interface MessageRecord {
  readonly messageId: string;
  readonly channel: string;
  readonly correlationId: string | null;
  readonly capturedAt: number;
}

interface MessageStore {
  record(entry: MessageRecord): void;
  byCorrelationId(correlationId: string): MessageRecord[];
  since(timestampMs: number): MessageRecord[];
}

class InMemoryMessageStore implements MessageStore {
  private readonly entriesById = new Map<string, MessageRecord>();

  record(entry: MessageRecord): void {
    this.entriesById.set(entry.messageId, entry);
  }

  byCorrelationId(correlationId: string): MessageRecord[] {
    return [...this.entriesById.values()].filter(
      (e) => e.correlationId === correlationId
    );
  }

  since(timestampMs: number): MessageRecord[] {
    return [...this.entriesById.values()].filter(
      (e) => e.capturedAt >= timestampMs
    );
  }
}

class WireTappedChannel {
  constructor(
    private readonly store: MessageStore,
    private readonly deliver: (payload: string, correlationId: string) => void
  ) {}

  send(
    messageId: string,
    channel: string,
    correlationId: string,
    payload: string
  ): void {
    this.store.record({
      messageId,
      channel,
      correlationId,
      capturedAt: Date.now(),
    });
    this.deliver(payload, correlationId);
  }
}

const store = new InMemoryMessageStore();
const tapped = new WireTappedChannel(store, (payload) =>
  console.log("delivered", payload)
);
tapped.send("m-1", "orders.in", "order-42", "place order");
tapped.send("m-1", "orders.in", "order-42", "place order redelivery");
console.log(store.byCorrelationId("order-42").length);
```

The `entriesById` map keyed on `messageId` is the idempotency fix from
dimension 11, a redelivered tap entry overwrites rather than duplicates.

### Python

```python
import sqlite3
import time
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class MessageRecord:
    message_id: str
    channel: str
    correlation_id: Optional[str]
    captured_at: float


class SqliteMessageStore:
    def __init__(self, path: str = ":memory:") -> None:
        self._conn = sqlite3.connect(path)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS message_store (
                message_id TEXT PRIMARY KEY,
                channel TEXT NOT NULL,
                correlation_id TEXT,
                captured_at REAL NOT NULL
            )
            """
        )

    def record(self, entry: MessageRecord) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO message_store VALUES (?, ?, ?, ?)",
            (
                entry.message_id,
                entry.channel,
                entry.correlation_id,
                entry.captured_at,
            ),
        )
        self._conn.commit()

    def by_correlation_id(self, correlation_id: str) -> list[MessageRecord]:
        rows = self._conn.execute(
            "SELECT message_id, channel, correlation_id, captured_at "
            "FROM message_store WHERE correlation_id = ? ORDER BY captured_at",
            (correlation_id,),
        ).fetchall()
        return [MessageRecord(*row) for row in rows]


if __name__ == "__main__":
    store = SqliteMessageStore()
    store.record(MessageRecord("m-1", "orders.in", "order-42", time.time()))
    store.record(MessageRecord("m-2", "orders.in", "order-42", time.time()))
    print(len(store.by_correlation_id("order-42")))
```

`INSERT OR REPLACE` keyed on the primary key mirrors the same idempotency
fix, and demonstrates the transactional-write variant, each record is
committed durably before the call returns, matching the JDBC-backed shape
described in dimension 8 rather than the in-memory shape above.

### Go

```go
package main

import (
	"fmt"
	"sync"
	"time"
)

type MessageRecord struct {
	MessageID     string
	Channel       string
	CorrelationID string
	CapturedAt    time.Time
}

type BoundedMessageStore struct {
	mu      sync.Mutex
	entries map[string]MessageRecord
	ttl     time.Duration
}

func NewBoundedMessageStore(ttl time.Duration) *BoundedMessageStore {
	return &BoundedMessageStore{
		entries: make(map[string]MessageRecord),
		ttl:     ttl,
	}
}

func (s *BoundedMessageStore) Record(r MessageRecord) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.entries[r.MessageID] = r
}

func (s *BoundedMessageStore) Evict(now time.Time) int {
	s.mu.Lock()
	defer s.mu.Unlock()
	removed := 0
	for id, r := range s.entries {
		if now.Sub(r.CapturedAt) > s.ttl {
			delete(s.entries, id)
			removed++
		}
	}
	return removed
}

func (s *BoundedMessageStore) Count() int {
	s.mu.Lock()
	defer s.mu.Unlock()
	return len(s.entries)
}

func main() {
	store := NewBoundedMessageStore(30 * 24 * time.Hour)
	store.Record(MessageRecord{
		MessageID:     "m-1",
		Channel:       "orders.in",
		CorrelationID: "order-42",
		CapturedAt:    time.Now(),
	})
	fmt.Println("stored", store.Count())
	evicted := store.Evict(time.Now().Add(31 * 24 * time.Hour))
	fmt.Println("evicted", evicted)
}
```

The mutex-guarded map with an explicit TTL and an `Evict` pass mirrors the
retention discipline of MuleSoft's Object Store v2 in miniature, a bounded
window applied to every entry rather than left to an unmanaged table.

## 18. References

1. Gregor Hohpe, Bobby Woolf. *Enterprise Integration Patterns. Designing,
   Building, and Deploying Messaging Solutions*. Addison-Wesley, 2003.
   ISBN 0-321-20068-3. System Management section, the "Message Store" entry
   and the "Systems Management Example" that opens the section. Source of
   the pattern's canonical name, its solution structure, and its positioning
   relative to Control Bus, Wire Tap, and Message History.
2. Gregor Hohpe, Bobby Woolf. *EnterpriseIntegrationPatterns.com*, "Message
   Store".
   https://www.enterpriseintegrationpatterns.com/patterns/messaging/MessageStore.html
   Verified 2026-08-02. Source of the quoted problem statement and the
   description of the fire-and-forget secondary channel and Wire Tap feed
   mechanism.
3. Gregor Hohpe, Bobby Woolf. *EnterpriseIntegrationPatterns.com*, System
   Management patterns index.
   https://www.enterpriseintegrationpatterns.com/patterns/messaging/
   Verified 2026-08-02. Source of the eight-pattern grouping under "Systems
   Mgmt.".
4. Gregor Hohpe, Bobby Woolf. *EnterpriseIntegrationPatterns.com*, book
   table of contents. https://www.enterpriseintegrationpatterns.com/toc.html
   Verified 2026-08-02. Source of the section's position in the book
   relative to Message Routing, Message Transformation, and Messaging
   Endpoints, and the loan broker "Systems Management Example."
5. VMware Tanzu, Broadcom. *Spring Integration Reference Documentation*,
   "Message Store".
   https://docs.spring.io/spring-integration/reference/message-store.html
   Verified 2026-08-02. Source for the `MessageStore` and `MessageGroupStore`
   interfaces, their production use inside `QueueChannel`, Aggregator,
   Delayer, and Claim Check, the `SimpleMessageStore`, `JdbcMessageStore`,
   `RedisMessageStore`, `MongoDbMessageStore`, and `HazelcastMessageStore`
   implementations, the serialization limitation on non-serializable
   headers, the lazy-load and streaming read-path performance note, and the
   `LockRegistry` thread-safety mechanism.
6. Salesforce, MuleSoft. *MuleSoft Documentation*, "Object Store".
   https://docs.mulesoft.com/object-store/
   Verified 2026-08-02. Source for Object Store v2's purpose, its 10 MB
   per-value limit, unlimited entry count, FIPS 140-2 compliant encryption
   and end-to-end TLS, and its rolling and static time-to-live retention
   model.
7. Particular Software. *NServiceBus Documentation*, "Outbox".
   https://docs.particular.net/nservicebus/outbox/
   Verified 2026-08-02. Source for the transactional write of outgoing
   messages and deduplication records alongside business data, deduplication
   by `MessageId`, the two-phase receive-then-dispatch flow, and the list of
   supported storage backends.
8. Martin Fowler. "Event Sourcing." *martinfowler.com*, published
   2005-12-12. https://martinfowler.com/eaaDev/EventSourcing.html
   Verified 2026-08-02. Source for the Event Sourcing definition used in
   dimension 4's non-applicability list, dimension 11's misuse case,
   dimension 12's trade-off matrix, and the append-only correction
   discipline cited in dimension 17.
