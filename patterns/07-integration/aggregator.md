---
name: Aggregator
slug: aggregator
family: 07-integration
category: Enterprise Integration
aliases: [Message Aggregator, Correlating Aggregator]
first_described: "Hohpe, Woolf 2003"
maturity: canonical
related: [correlation-identifier, message-sequence, splitter, scatter-gather, composed-message-processor, dead-letter-channel]
incompatible_with: []
verified: 2026-08-02
---

# Aggregator

## 1. Name, aliases, and lineage

The canonical name is Aggregator. It is one of the routing patterns in Gregor
Hohpe and Bobby Woolf, *Enterprise Integration Patterns. Designing, Building,
and Deploying Messaging Solutions*, Addison-Wesley, 2003, in the chapter on
Message Routing. The pattern's own reference page states the problem it
answers as "How do we combine the results of individual, but related messages
so that they can be processed as a whole?" and gives the solution as "Use a
stateful filter, an Aggregator, to collect and store individual messages until
a complete set of related messages has been received. Then, the Aggregator
publishes a single message distilled from the individual messages"
([enterpriseintegrationpatterns.com, Aggregator](https://www.enterpriseintegrationpatterns.com/patterns/messaging/Aggregator.html),
verified 2026-08-02).

The book calls it a stateful filter on purpose, because it sits in the same
family as Message Filter and Content-Based Router but, unlike either, it holds
state across more than one message. Every mainstream messaging framework that
implements it keeps the same name. Apache Camel calls it the Aggregator EIP
and ships an `aggregate` DSL step. Spring Integration calls it the Aggregator
and ships an `AggregatingMessageHandler`. MuleSoft, NServiceBus, and MassTransit
each describe the same shape, either directly as an aggregator or under a
"correlated saga," because a saga that waits for several messages before
proceeding is an Aggregator with a persistence layer bolted on in effect.
The alias Message Aggregator is used interchangeably with the bare name in
vendor documentation. The alias Correlating Aggregator is used in a smaller
set of sources to stress that correlation is the first of the pattern's three
required decisions, covered in dimension 5.

There is no real naming dispute here. Where confusion happens in
practice is between Aggregator and Composed Message Processor, covered in
dimension 13, and between Aggregator and a plain reduce or fold over a
collection, covered in dimension 4.

## 2. Problem and context

A system receives several messages that only make sense together, and no
single message carries enough information to act on. A price quoting service
asks three suppliers for a price and cannot answer the customer until it has
heard from all three, or has waited long enough to decide it will not hear
from a fourth. A claims processor splits a batch of a thousand line items,
farms each one out for independent validation, and cannot mark the batch
complete until every line item has reported back, or until enough have
reported back that the remainder are written off as failed. An order
fulfilment system fires a message when payment clears and a separate message
when the warehouse confirms stock, and the shipping step must wait for both
before it can run, because shipping on payment alone risks shipping stock
that is not there, and shipping on stock confirmation alone risks shipping
before payment clears.

In every one of these the naive first attempt is a shared mutable structure
protected by a lock, checked and mutated by whichever message handler runs
next. That works until two things happen that always happen. First, the
handlers are horizontally scaled, so the shared structure needs to live
somewhere both instances can see it, which turns a lock into a distributed
lock. Second, one of the expected messages never shows up, because a supplier
is down or a warehouse system drops a message, and the ad hoc structure has no
answer for what to do with a claim that waits forever.

The context in which the pattern earns its place has three properties at
once. The individual messages are legitimately independent, each one is
produced by a different upstream step or a different external party, so
correlating them at the source is not possible. The completeness of the set
is not always the same fixed count, it can be a count known in advance from a
Message Sequence header, a count discovered dynamically, or a business rule
about "enough," see dimension 5. And a partial or late-arriving set has real
business consequences, so the completeness decision itself needs to be a
first-class, testable, observable piece of logic rather than an incidental
side effect of whichever handler happens to run last.

## 3. Forces

- **Consistency versus availability.** Favours consistency of the assembled
  result at the direct cost of availability of any answer at all while the
  set is incomplete. A caller who needs a partial answer before the set
  completes cannot be served by an Aggregator alone, they need a
  Composed Message Processor with explicit partial-result semantics instead,
  see dimension 13.
- **Latency.** Sacrificed by construction. The Aggregator's whole job is to
  wait, so the end to end latency of the aggregated result is bounded below
  by the slowest expected contributor, or by the completion timeout if one is
  configured. A caller sensitive to tail latency from one slow upstream needs
  the timeout tuned deliberately, not left at a framework default.
- **State and durability.** Sacrificed compared to a stateless router. The
  Aggregator must persist partial correlation groups somewhere that survives
  a process restart, or a crash mid-collection silently loses every partially
  assembled set. Spring Integration's own documentation frames this
  explicitly, calling the component stateful and requiring a `MessageStore`
  to hold messages "until a complete group is ready for aggregation"
  ([docs.spring.io, Aggregator](https://docs.spring.io/spring-integration/reference/aggregator.html),
  verified 2026-08-02).
- **Memory and cost bound.** Sacrificed against an unbounded correlation key
  space. Every correlation key that has received at least one message but not
  yet completed occupies memory or storage until it completes or expires, so
  an attacker or a bug that mints correlation keys without bound is a
  resource exhaustion vector, covered further in dimension 17.
- **Operability.** Favoured over the ad hoc shared-state alternative, because
  the completeness decision, the correlation key, and the expiry policy are
  each named, testable, and observable independently, rather than scattered
  across whichever handler happened to run last, see dimension 16.
- **Simplicity of the individual producers.** Favoured. Each upstream
  producer stays completely unaware that its message is one of a set, it
  only emits a message with a correlation identifier attached. All of the
  coordination complexity concentrates in one place instead of being
  replicated into every producer.

## 4. Applicability and non-applicability

Reach for an Aggregator when messages genuinely originate independently and
must be combined before downstream logic can proceed, when the completeness
condition is itself a piece of business logic worth naming and testing
separately from the combining logic, when partial or late-arriving sets have
real consequences that need an explicit, observable decision rather than a
silent drop, and when the correlating messages travel over a broker or
transport that does not itself provide ordering or joining, which is most of
them.

Do NOT reach for an Aggregator in the following situations.

- **A single request-reply round trip with one response.** There is nothing
  to aggregate. Use a plain synchronous call or a Request-Reply channel pair.
  An Aggregator configured for exactly one expected message is an Aggregator
  in name only and adds a persistence dependency for zero benefit.
- **An in-process collection already held in memory in one thread.**
  `Stream.reduce`, `functools.reduce`, LINQ `Aggregate`, or a plain fold over
  a list already do this correctly, cheaply, and without a persistence layer.
  Reach for the messaging pattern only once the individual items genuinely
  arrive as separate messages, from separate producers, at separate times.
- **A known, fixed set of futures or promises that can simply be awaited
  together in one process.** `Promise.all`, a Go `sync.WaitGroup`, or Java's
  `CompletableFuture.allOf` solve the in-process fan-out case without a
  stateful message store, a correlation key, or an expiry policy. The
  Aggregator earns its cost specifically when the fan-out crosses a process,
  a broker, or a durability boundary that a language-level future cannot
  span.
- **A running, continuously-updated total over an unbounded stream with no
  completeness condition, such as a rolling metric.** That is a streaming
  windowed aggregation, a related but distinct shape, see dimension 13. An
  Aggregator's group has a start and an end; a streaming window has neither
  in the same sense.
- **Ordered messages from a single producer where only the latest matters.**
  That is Message Expiration or simple overwrite semantics, not aggregation,
  because there is no combining logic and no completeness decision to make.
- **A workaround for a design that should have sent one message in the first
  place.** If every producer that feeds the Aggregator is under your control
  and the split into multiple messages exists only because of how the
  pattern was implemented rather than because the data genuinely originates
  separately, fix the upstream instead of coordinating the fragments
  downstream.

## 5. Structure

An Aggregator has four participants, and the pattern's own documentation is
explicit that the middle two are independently pluggable decisions rather
than one blended piece of logic.

- **Correlation.** Determines which incoming messages belong to the same
  logical set. Almost always implemented as a Correlation Identifier, a
  header value shared by every message in the set. The reference definition
  states this as the first of three required parameters, "Correlation
  determining which incoming messages belong together"
  ([enterpriseintegrationpatterns.com, Aggregator](https://www.enterpriseintegrationpatterns.com/patterns/messaging/Aggregator.html),
  verified 2026-08-02). Spring Integration's default correlation strategy
  reads a header it calls `CORRELATION_ID`, grouping "messages with the same
  `IntegrationMessageHeaderAccessor.CORRELATION_ID`"
  ([docs.spring.io, Aggregator](https://docs.spring.io/spring-integration/reference/aggregator.html),
  verified 2026-08-02).
- **Completeness condition (release strategy).** Decides when a correlated
  group has everything it needs to be combined and released downstream. The
  three common shapes, all named explicitly in Apache Camel's Aggregate EIP
  reference, are a fixed count known in advance, "Number of messages
  aggregated before the aggregation is complete"; an inactivity timeout,
  "Time that an aggregated exchange should be inactive before its complete
  (timeout)"; and an arbitrary predicate, "A predicate to indicate when an
  aggregated exchange is complete"
  ([camel.apache.org, Aggregate EIP](https://camel.apache.org/components/next/eips/aggregate-eip.html),
  verified 2026-08-02). Spring Integration's default release strategy
  releases a group "when all messages included in a sequence are present,
  based on the `IntegrationMessageHeaderAccessor.SEQUENCE_SIZE` header"
  ([docs.spring.io, Aggregator](https://docs.spring.io/spring-integration/reference/aggregator.html),
  verified 2026-08-02), which is the fixed-count shape driven by a
  Message Sequence header rather than a hardcoded number.
- **Aggregation algorithm (combining strategy).** Defines how the individual
  messages in a completed group fold into the single outgoing message. Apache
  Camel calls this the `AggregationStrategy` and states it is required,
  describing its job as merging "each incoming exchange with the existing
  already merged exchanges," with an explicit performance warning that the
  strategy should mutate and return one of the two input exchanges rather
  than allocate a new one, "favor returning the old exchange whenever
  possible"
  ([camel.apache.org, Aggregate EIP](https://camel.apache.org/components/next/eips/aggregate-eip.html),
  verified 2026-08-02).
- **Group store.** The durable or in-memory structure holding partially
  assembled groups between arrivals. Spring Integration names this the
  `MessageGroupStore`, delegating all state management of a `MessageGroup`
  to it, and documents that the store "accumulates state information in
  `MessageGroups` while waiting for a release strategy to be triggered, and
  that event might not ever happen," which is exactly why the store also
  exposes expiry callbacks to clean up groups that never complete
  ([docs.spring.io, Aggregator](https://docs.spring.io/spring-integration/reference/aggregator.html),
  verified 2026-08-02).

## 6. ASCII structure diagram

```
                       correlation key = "order-4471"
                                  |
   Producer A ---msg(cid=4471)-->|
   Producer B ---msg(cid=4471)-->+---> [ Group Store ]
   Producer C ---msg(cid=4471)-->|         |     |
                                  |         |     |
                          [Correlation]  [Completeness
                           Strategy]      Condition]
                                  |         |
                                  v         v
                          groups incoming  size N reached?
                          message into     timeout elapsed?
                          the right group  predicate true?
                                            |
                                       yes  |
                                            v
                                  [ Aggregation Algorithm ]
                                  folds every message in the
                                  completed group into one
                                            |
                                            v
                                  ---> single outgoing message
                                       (group discarded from store)
```

## 7. Dynamics

```
Producer A         Producer B         Producer C         Aggregator            Downstream
    |                   |                   |                  |                     |
    |--- msg(cid=4471, seq 1/3) ----------->|                  |
    |                   |                   |     correlate(4471) -> new group
    |                   |                   |     check completeness: 1 of 3, wait
    |                   |--- msg(cid=4471, seq 2/3) ---------->|
    |                   |                   |     correlate(4471) -> existing group
    |                   |                   |     check completeness: 2 of 3, wait
    |                   |                   |--- msg(cid=4471, seq 3/3) ----------->
    |                   |                   |     correlate(4471) -> existing group
    |                   |                   |     check completeness: 3 of 3, release
    |                   |                   |     aggregate(msg1, msg2, msg3) -> result
    |                   |                   |                  |--- result(cid=4471) ---->
    |                   |                   |     group 4471 removed from store

Late arrival, past timeout:

    |--- msg(cid=9002, seq 1/2) ----------->|
    |                   |                   |     correlate(9002) -> new group
    |                   |                   |     completion timeout fires before seq 2/2
    |                   |                   |     release partial group as-is, OR
    |                   |                   |     route to a dead letter / discard channel
    |                   |     (msg with cid=9002, seq 2/2, never arrives, or arrives
    |                   |      after expiry and is routed to a discard handler)
```

## 8. Implementation variants

- **Count-based, sequence-driven.** The producer that fans out the original
  message stamps every fragment with a Message Sequence header carrying a
  total count, and the Aggregator releases a group the instant it has seen
  that many messages for a correlation key. This is Spring Integration's
  default `SimpleSequenceSizeReleaseStrategy`
  ([docs.spring.io, Aggregator](https://docs.spring.io/spring-integration/reference/aggregator.html),
  verified 2026-08-02), and the natural pairing with Splitter, since the
  splitter is the component that knows the total count and can stamp it.
- **Timeout-based, inactivity-driven.** No fixed count is known in advance,
  so the group releases whichever messages it has once a period of silence
  elapses. Apache Camel's `completionTimeout` implements exactly this
  ([camel.apache.org, Aggregate EIP](https://camel.apache.org/components/next/eips/aggregate-eip.html),
  verified 2026-08-02). This variant must decide, as a separate policy
  question, whether a timeout-released partial group is treated as a valid
  best-effort result or as a failure to route to a Dead Letter Channel; the
  framework does not decide this for you.
- **Predicate-driven, business-rule completion.** The completeness condition
  is an arbitrary function over the accumulated group, for example release
  once at least two of three price quotes are in and either five seconds
  have passed or all three are in, whichever comes first. Camel's
  `completionPredicate`
  ([camel.apache.org, Aggregate EIP](https://camel.apache.org/components/next/eips/aggregate-eip.html),
  verified 2026-08-02) and Spring Integration's `ReleaseStrategy` interface,
  a single `canRelease(MessageGroup group)` method
  ([docs.spring.io, Aggregator](https://docs.spring.io/spring-integration/reference/aggregator.html),
  verified 2026-08-02), both exist to let this be a first-class, unit
  testable object rather than an inline conditional.
- **Saga-based, durable, long-running correlation.** Where the collection
  window spans minutes, hours, or days rather than seconds, and where crash
  recovery matters more than throughput, the Aggregator's group store becomes
  a persisted saga instance keyed by a correlation property. NServiceBus
  documents this shape directly, stating "Correlation is needed in order to
  find existing saga instances based on data in the incoming message," and
  frames the saga as stateful by nature because "Any process that involves
  multiple network calls (or messages sent and received) has an interim
  state"
  ([docs.particular.net, Sagas](https://docs.particular.net/nservicebus/sagas/),
  verified 2026-08-02). The saga variant trades the lighter in-memory or
  cache-backed group store of the messaging-framework variants for a
  database-backed correlation table with its own transactional guarantees.
- **Language-idiomatic, in-process substitutes.** Where the fan-out and the
  join both live in one process and one language runtime, an actual message
  broker and group store are unnecessary ceremony. `Promise.all` in
  JavaScript, `asyncio.gather` in Python, `CompletableFuture.allOf` in Java,
  and a `sync.WaitGroup` in Go each implement the count-based completeness
  condition with the runtime's own concurrency primitives instead of a
  Correlation Identifier and a persisted group. These are not the Aggregator
  pattern in the Hohpe and Woolf sense, they solve the same shape of problem
  one level down, entirely inside a single process boundary, see dimension 4.

## 9. Known production uses

- **Apache Camel, the Aggregate EIP.** Camel ships `aggregate` as a first
  class DSL step with `correlationExpression`, `completionSize`,
  `completionTimeout`, `completionPredicate`, and a required
  `AggregationStrategy`, used across production Camel routes for the
  supplier-quote and batch-line-item shapes described in dimension 2
  ([camel.apache.org, Aggregate EIP](https://camel.apache.org/components/next/eips/aggregate-eip.html),
  verified 2026-08-02).
- **Spring Integration, the Aggregator component.** Spring Integration ships
  `AggregatingMessageHandler` with a pluggable `CorrelationStrategy`,
  `ReleaseStrategy`, `MessageGroupProcessor`, and `MessageGroupStore`,
  documented as the mirror image of its Splitter component and used
  throughout Spring-based enterprise integration deployments to recombine
  split or fanned-out message flows
  ([docs.spring.io, Aggregator](https://docs.spring.io/spring-integration/reference/aggregator.html),
  verified 2026-08-02).
- **NServiceBus sagas, correlation-based aggregation.** NServiceBus documents
  saga instances located by a correlation property extracted from incoming
  messages, holding interim state across multiple message arrivals before a
  business decision is made, which is the durable, long-running variant of
  the pattern described in dimension 8
  ([docs.particular.net, Sagas](https://docs.particular.net/nservicebus/sagas/),
  verified 2026-08-02).

## 10. Consequences

Positive.

- Producers stay simple and unaware of each other, all coordination
  concentrates in one named, testable component.
- The completeness decision becomes an explicit, unit-testable policy object
  instead of an incidental side effect buried in whichever handler runs last.
- Combining logic (dimension 5, aggregation algorithm) is isolated from
  correlation and completeness, so each of the three concerns can be changed
  independently without touching the other two.
- Partial and late-arriving sets have a defined, observable outcome rather
  than a silent hang or a leaked in-memory structure, provided the expiry and
  discard paths are actually wired, see dimension 11.

Negative.

- Introduces a stateful component and a persistence or in-memory store where
  none existed before, which is a new failure mode, a new thing to size, and
  a new thing to back up or replicate.
- Adds latency to the end to end flow equal to at least the slowest expected
  contributor, and up to the full completion timeout for a group that never
  completes.
- The correlation key space is an attacker-controllable or bug-controllable
  resource consumption vector if it is not bounded, see dimension 17.
- Debugging a missing or late aggregated result requires tracing backward
  through the group store to find which of the correlated messages never
  arrived, which is materially harder than tracing a single linear message
  flow, see dimension 16.
- A poorly chosen aggregation algorithm that is not associative or not
  commutative produces a result that depends on arrival order, which is a
  subtle correctness bug that only shows up under network jitter or replay.

## 11. Failure modes and misuse

- **Symptom.** Memory or storage for the group store grows without bound over
  time, eventually causing out-of-memory errors or storage exhaustion.
  **Cause.** Groups that never reach their completeness condition are never
  expired, because no timeout or expiry callback was configured, only the
  happy-path completion condition was implemented.
  **Fix.** Always pair a completeness condition with an expiry policy.
  Spring Integration's `MessageGroupStore` exposes expiry callback
  registration precisely so that groups whose "event might not ever happen"
  are still cleaned up
  ([docs.spring.io, Aggregator](https://docs.spring.io/spring-integration/reference/aggregator.html),
  verified 2026-08-02); Camel's `completionTimeout` serves the same role.
  Route expired, incomplete groups to a Dead Letter Channel rather than
  silently dropping them, so the missing contributor is visible.

- **Symptom.** Two contributor messages for the same logical event are
  silently merged into two different groups, or one contributor's message is
  never matched to its group at all, and the aggregated result is either
  duplicated or perpetually short one message.
  **Cause.** The correlation key is not actually unique per logical set, or
  is derived inconsistently across producers, for example one producer
  stamps a business order id and another stamps a generated request id for
  the same logical order.
  **Fix.** Fix the correlation key at the producer boundary, never in the
  Aggregator. Write a contract test asserting every producer that feeds a
  given Aggregator emits the same correlation value for the same logical
  event, before the aggregation logic is trusted at all.

- **Symptom.** The aggregated result is correct on a quiet system and wrong
  under load or after a redeploy that reorders in-flight messages.
  **Cause.** The aggregation algorithm is order-dependent, for example it
  concatenates a list in arrival order and downstream code assumes a
  specific business ordering, rather than being written to be commutative
  over its inputs.
  **Fix.** Design the aggregation algorithm to be independent of arrival
  order, or explicitly sort the group's contents by a business timestamp or
  sequence number inside the algorithm before combining, never rely on
  transport-level arrival order.

- **Symptom.** Two instances of a horizontally scaled Aggregator each believe
  they own the same correlation group and both release it, producing two
  outgoing aggregated messages for one logical set.
  **Cause.** The group store is instance-local, in-memory, and not shared or
  partitioned consistently across instances, so a message routed to instance
  A completes a group that instance B also believes it is tracking.
  **Fix.** Back the group store with a shared, consistent store, a database,
  a distributed cache with appropriate consistency guarantees, or partition
  correlation keys deterministically across instances, for example by hashing
  the correlation key to a fixed instance, matching the same partitioning
  discipline used for a Partitioned Consumer.

- **Symptom.** A single malicious or buggy producer causes unbounded resource
  growth by sending messages with a fresh, never-repeating correlation key on
  every call.
  **Cause.** No bound exists on the number of distinct open correlation
  groups the store will accept, so each new key creates a new never-to-be-
  completed group.
  **Fix.** Cap the number of concurrently open groups, reject or rate limit
  new correlation keys past that cap, and alert on the open-group count
  approaching the cap, see dimension 17.

## 12. Trade-off matrix

| Force | Aggregator | Splitter alone (no rejoin) | In-process `Promise.all` / `WaitGroup` | Scatter-Gather |
|---|---|---|---|---|
| Crosses process or broker boundary | Yes, this is its purpose | Yes, but never rejoins | No, single process only | Yes |
| Requires a durable or in-memory group store | Yes | No | No, held on the call stack | Usually yes |
| Handles a dynamically discovered completion count | Yes, via predicate or timeout | Not applicable | Awkward, count must be known before the call starts | Yes |
| Built-in timeout and partial-result policy | Yes, explicit and pluggable | Not applicable | Manual, must be hand-rolled per call | Yes |
| Best fit when the request itself initiates the fan-out and waits synchronously | Poor fit, Aggregator is async and decoupled from the requester | Not applicable | Good fit | Good fit, it is the request-initiated variant |
| Best fit when contributors arrive independently over time from different, unrelated producers | Best fit | Not applicable | Poor fit, requires all contributors reachable from one call site | Poor fit |

## 13. Related and incompatible patterns

- **Correlation Identifier.** Almost always the mechanism the Aggregator uses
  to group messages, dimension 5's first participant. An Aggregator without
  a well-designed Correlation Identifier strategy cannot function correctly,
  see the correlation-key failure mode in dimension 11.
- **Message Sequence.** Frequently paired with the count-based completeness
  variant in dimension 8, where the sequence header supplies the total count
  the Aggregator waits for. A Splitter that fans a message out typically
  stamps the Message Sequence header the paired Aggregator later consumes.
- **Splitter.** The structural inverse. A Splitter fans one message into many;
  an Aggregator folds many back into one. The two are frequently deployed as
  a matched pair around a parallel processing step, split, process each
  fragment independently, aggregate.
- **Scatter-Gather.** A composed pattern that pairs a Recipient List, which
  actively sends the same request to multiple recipients, with an Aggregator,
  which then collects and combines the responses. Scatter-Gather is
  request-initiated and typically synchronous from the caller's perspective;
  a plain Aggregator is reactive and asynchronous, simply waiting for
  whatever independently produced messages arrive, without itself having
  sent anything to trigger them. Every Scatter-Gather implementation
  contains an Aggregator, but not every Aggregator is part of a
  Scatter-Gather.
- **Composed Message Processor.** A closely related but distinct pattern
  that also combines results from multiple sub-messages, but is explicitly
  designed around returning a coherent partial result to the original
  caller even before every sub-message has completed, tracking each
  sub-task's status individually. An Aggregator's default semantics are
  all-or-nothing at the completeness condition; a Composed Message Processor
  is designed for graceful partial completion as its normal case, not its
  failure case.
- **Windowed stream aggregation.** A related but distinct shape from
  streaming systems, where a continuously arriving, unbounded stream is
  aggregated over sliding or tumbling time windows with no discrete
  completeness condition, only a window boundary. The Aggregator pattern's
  group has a definite start and end tied to a specific correlation key; a
  streaming window has neither in the same sense, and the two should not be
  conflated even though both fold multiple inputs into one output.
- **Dead Letter Channel.** The correct destination for a group that expires
  incomplete, per the fix in dimension 11's first failure mode, rather than
  silently discarding it.
- **Incompatible with.** Nothing in this catalog is structurally incompatible
  with an Aggregator; it composes with routing patterns rather than
  conflicting with them.

## 14. Refactoring path in and out

Introducing an Aggregator into code that currently coordinates multiple
messages with an ad hoc shared, locked structure proceeds in stages.

1. Identify every place a handler reads or writes the shared coordination
   structure, and name the correlation key each handler uses to find its
   entry, even if that key is currently implicit, for example an order id
   embedded in a message body rather than a header.
2. Extract the correlation logic into its own named function or strategy
   object, and add a test asserting every existing producer path yields the
   same correlation value for the same logical event, per the fix in
   dimension 11.
3. Extract the completeness check, currently likely an inline `if` inside
   whichever handler happens to run last, into its own named, independently
   testable policy object, choosing the count, timeout, or predicate shape
   from dimension 8 that matches the actual business rule.
4. Extract the combining logic into its own named function, and verify it is
   order-independent by writing a test that feeds it the same inputs in
   multiple orders and asserts an identical result.
5. Replace the ad hoc shared structure with a real group store, in-process
   for a single-instance deployment, or backed by a shared cache or database
   once the component is horizontally scaled, and wire an expiry policy from
   day one, not as a later addition.
6. Route expired, incomplete groups to an explicit discard or Dead Letter
   Channel destination, and add monitoring on the open-group count per
   dimension 16, before considering the migration complete.

Removing an Aggregator that has outlived its purpose, typically because
the fan-out it was rejoining has been eliminated or collapsed into a single
producer, proceeds in the reverse order. Confirm the completeness condition
now always evaluates to a single-message group, in which case the aggregation
algorithm degenerates to an identity function and the Aggregator adds pure
latency and storage cost for zero remaining benefit. Replace the Aggregator
step with a direct pass-through, delete the group store, and delete the
correlation and completeness policy objects only after confirming, via the
production monitoring built in dimension 16, that no group has held more
than one message across a full observation window that includes peak load.

## 15. Testing and verification

What becomes easy because of the pattern. Because dimension 5 splits
correlation, completeness, and combining into three independent objects,
each one is a pure function or a small stateful policy that can be unit
tested in complete isolation from any messaging infrastructure. A
completeness policy test feeds it a sequence of partial groups and asserts
exactly when `canRelease` or the equivalent returns true. A combining
algorithm test feeds it a fixed set of messages in every permutation and
asserts an identical output, directly verifying the order-independence
property from dimension 11.

What becomes harder. Integration-level testing of the full Aggregator now
requires exercising timing behaviour, specifically the completion timeout
path and the expiry path, which are, by nature, about the absence of a
message rather than its presence. Use a controllable clock or a test double
for the group store's expiry mechanism rather than sleeping the real
duration of the timeout in a test suite; a test that actually sleeps for a
production-configured timeout value is both slow and a reliable source of
flaky CI runs under load.

Specific techniques that apply. Contract tests between every producer and
the Aggregator asserting correlation key consistency, per dimension 14 step
2. Property-based tests on the combining algorithm generating random orderings
and asserting a stable result. Fault-injection tests that simulate one
contributor never arriving, verifying the group correctly expires and routes
to the discard channel rather than hanging the test process. A load test
that opens far more concurrent correlation groups than the expected steady
state, verifying the resource bound from dimension 17's fix actually holds
rather than only being asserted in configuration.

## 16. Observability signals

A healthy Aggregator's dashboard shows a bounded, roughly steady count of
currently open, incomplete correlation groups, a completion latency
distribution whose tail is explained by the slowest legitimate contributor
rather than by lost messages, and a near-zero or fully explained rate of
groups reaching their expiry timeout.

Log and trace, per completed group, the correlation key, the number of
messages the group actually received against the number it expected if a
count was known in advance, the wall clock time from group creation to
release, and which of size, timeout, or predicate triggered the release.
Log, per expired or discarded group, the correlation key and exactly which
expected contributor never arrived, if that is knowable, so the missing
upstream producer can be identified without manual log archaeology.

Measure and alert on the count of currently open groups approaching any
configured cap, the rate of groups expiring incomplete as a fraction of
total groups, which should be near zero on a healthy system and is the
single clearest signal that an upstream producer is failing or a
correlation key mismatch has been introduced, and the completion latency
p99, since a rising p99 with a stable p50 usually indicates one specific
slow or intermittently failing contributor rather than a systemic issue.

A failing instance shows a monotonically growing open-group count, which is
the direct symptom of the memory-exhaustion failure mode in dimension 11,
and should trigger paging well before the underlying process actually runs
out of memory or storage.

## 17. Security and privacy implications

The correlation key space is a resource-consumption attack surface. Any
external actor who can influence the correlation key of a message that
reaches the Aggregator, directly or indirectly, can open new correlation
groups at will. Without the bound and rate limit described in dimension 11's
fix, this is a straightforward denial of service vector against the group
store's memory or storage. Treat the correlation key the same way an
API design treats any client-influenced value used as a cache or storage
key, with an explicit cap on how many distinct correlation keys the system will accept.

The group store itself is a place where fragments of otherwise separate
messages sit together in memory or on disk, potentially for the full
duration of a completion timeout. Where the individual messages carry
personal data, the aggregated group is a concentration point that did not
exist before the Aggregator was introduced, and it should be covered by the
same data retention, encryption at rest, and access control policy as any
other store holding that class of data, not treated as transient plumbing
exempt from the policy. An expired, incomplete group that is routed to a
Dead Letter Channel per dimension 11 carries the same sensitivity as the
completed group would have and needs the same handling, not a lower bar
because it never reached its intended destination.

Where the completeness predicate itself is derived from message content
rather than purely from a count or a clock, validate that content the same
way any other externally supplied input is validated before it is evaluated
as a condition, since a completeness predicate that can be tricked into
firing early is a way to force a premature, incomplete aggregated result
into downstream business logic that assumed completeness had genuinely been
reached.

## 18. References

- Gregor Hohpe and Bobby Woolf, *Enterprise Integration Patterns. Designing,
  Building, and Deploying Messaging Solutions*, Addison-Wesley, 2003, Message
  Routing chapter, the Aggregator pattern.
- [Enterprise Integration Patterns, Aggregator](https://www.enterpriseintegrationpatterns.com/patterns/messaging/Aggregator.html), verified 2026-08-02.
- [Apache Camel, Aggregate EIP](https://camel.apache.org/components/next/eips/aggregate-eip.html), verified 2026-08-02.
- [Spring Integration Reference, Aggregator](https://docs.spring.io/spring-integration/reference/aggregator.html), verified 2026-08-02.
- [Particular Software, NServiceBus Sagas](https://docs.particular.net/nservicebus/sagas/), verified 2026-08-02.

## Code examples

### TypeScript, count and timeout based, in-memory group store

```typescript
type Group = { messages: unknown[]; expected?: number; timer?: NodeJS.Timeout };

class Aggregator {
  private groups = new Map<string, Group>();

  constructor(
    private completionTimeoutMs: number,
    private onRelease: (key: string, messages: unknown[]) => void,
    private onExpire: (key: string, messages: unknown[]) => void,
  ) {}

  accept(correlationKey: string, message: unknown, expectedCount?: number): void {
    let group = this.groups.get(correlationKey);
    if (!group) {
      group = { messages: [], expected: expectedCount };
      this.groups.set(correlationKey, group);
    }
    group.messages.push(message);

    if (group.timer) clearTimeout(group.timer);
    group.timer = setTimeout(() => this.expire(correlationKey), this.completionTimeoutMs);

    if (group.expected !== undefined && group.messages.length >= group.expected) {
      this.release(correlationKey);
    }
  }

  private release(correlationKey: string): void {
    const group = this.groups.get(correlationKey);
    if (!group) return;
    if (group.timer) clearTimeout(group.timer);
    this.groups.delete(correlationKey);
    this.onRelease(correlationKey, group.messages);
  }

  private expire(correlationKey: string): void {
    const group = this.groups.get(correlationKey);
    if (!group) return;
    this.groups.delete(correlationKey);
    this.onExpire(correlationKey, group.messages);
  }

  openGroupCount(): number {
    return this.groups.size;
  }
}
```

### Python, predicate based release strategy as a first-class object

```python
import time
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class Group:
    messages: list = field(default_factory=list)
    created_at: float = field(default_factory=time.monotonic)


class Aggregator:
    def __init__(
        self,
        release_predicate: Callable[[Group], bool],
        combine: Callable[[list], object],
        expiry_seconds: float,
    ):
        self._groups: dict[str, Group] = {}
        self._release_predicate = release_predicate
        self._combine = combine
        self._expiry_seconds = expiry_seconds

    def accept(self, correlation_key: str, message: object) -> object | None:
        self._expire_stale()
        group = self._groups.setdefault(correlation_key, Group())
        group.messages.append(message)
        if self._release_predicate(group):
            del self._groups[correlation_key]
            return self._combine(group.messages)
        return None

    def _expire_stale(self) -> None:
        now = time.monotonic()
        expired = [
            key
            for key, group in self._groups.items()
            if now - group.created_at > self._expiry_seconds
        ]
        for key in expired:
            del self._groups[key]

    def open_group_count(self) -> int:
        return len(self._groups)


def at_least_two_of_three(group: Group) -> bool:
    return len(group.messages) >= 2


def combine_quotes(messages: list) -> object:
    return {"lowest_quote": min(m["price"] for m in messages), "quotes_used": len(messages)}


if __name__ == "__main__":
    agg = Aggregator(at_least_two_of_three, combine_quotes, expiry_seconds=5.0)
    print(agg.accept("order-4471", {"price": 100}))
    result = agg.accept("order-4471", {"price": 92})
    print(result)
    assert result == {"lowest_quote": 92, "quotes_used": 2}
```

### Go, count based, mutex protected, correlation key expiry

```go
package main

import (
	"fmt"
	"sync"
	"time"
)

type group struct {
	messages []interface{}
	expected int
	created  time.Time
}

type Aggregator struct {
	mu     sync.Mutex
	groups map[string]*group
	expiry time.Duration
}

func NewAggregator(expiry time.Duration) *Aggregator {
	return &Aggregator{groups: make(map[string]*group), expiry: expiry}
}

func (a *Aggregator) Accept(key string, msg interface{}, expected int) ([]interface{}, bool) {
	a.mu.Lock()
	defer a.mu.Unlock()

	g, ok := a.groups[key]
	if !ok {
		g = &group{expected: expected, created: time.Now()}
		a.groups[key] = g
	}
	g.messages = append(g.messages, msg)

	if len(g.messages) >= g.expected {
		delete(a.groups, key)
		return g.messages, true
	}
	return nil, false
}

func (a *Aggregator) ExpireStale() int {
	a.mu.Lock()
	defer a.mu.Unlock()

	now := time.Now()
	expired := 0
	for key, g := range a.groups {
		if now.Sub(g.created) > a.expiry {
			delete(a.groups, key)
			expired++
		}
	}
	return expired
}

func (a *Aggregator) OpenGroupCount() int {
	a.mu.Lock()
	defer a.mu.Unlock()
	return len(a.groups)
}

func main() {
	agg := NewAggregator(2 * time.Second)
	if _, done := agg.Accept("order-4471", "quote-a", 2); done {
		fmt.Println("released too early")
	}
	messages, done := agg.Accept("order-4471", "quote-b", 2)
	if !done {
		panic("expected group to release")
	}
	fmt.Printf("released group: %v\n", messages)
	fmt.Printf("open groups after release: %d\n", agg.OpenGroupCount())
}
```
