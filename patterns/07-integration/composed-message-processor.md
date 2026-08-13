---
name: Composed Message Processor
slug: composed-message-processor
family: 07-integration
category: Enterprise Integration
aliases: [Scatter-Gather, Distribution-Aggregate, Split-Route-Aggregate]
first_described: "Hohpe, Woolf 2003"
maturity: canonical
related: [splitter, aggregator, content-based-router, pipes-and-filters, scatter-gather, saga]
incompatible_with: []
verified: 2026-08-02
---

# Composed Message Processor

## 1. Name, aliases, and lineage

The canonical name is Composed Message Processor. It appears in Gregor Hohpe and
Bobby Woolf, *Enterprise Integration Patterns. Designing, Building, and
Deploying Messaging Solutions*, Addison-Wesley, 2003, in the Message Routing
chapter, as a composite pattern built from three simpler ones. The pattern's
own online reference states the intent plainly, "The Composed Message
Processor splits the message up, routes the sub-messages to the appropriate
destinations and re-aggregates the responses back into a single message"
(https://www.enterpriseintegrationpatterns.com/patterns/messaging/DistributionAggregate.html,
verified 2026-08-02).

The book presents Composed Message Processor as the general answer to a
question that most integration authors run into independently. what do I do
when a single logical message actually needs several unrelated pieces of work
done to different parts of it, before I can call the message handled. The
pattern is explicitly a composition, not a primitive. it is built from
Splitter (decompose the composite message into addressable sub-messages),
Content-Based Router or a fixed set of destinations (send each sub-message to
the system that owns that piece of work), and Aggregator (collect the
responses and combine them into one outgoing message). The EIP catalog cross
references it directly against those three, plus Pipes and Filters as the
architectural style the whole flow sits inside.

**Scatter-Gather** is the name the pattern carries most often outside the EIP
book itself, and it is the name used almost universally in the cloud
architecture and service mesh literature written after 2010. Microsoft's own
Azure Architecture Center names the pattern Scatter-Gather and cites Hohpe and
Woolf directly as its origin. the two names describe the identical shape, a
fan-out to N destinations followed by a fan-in that waits on and merges the
responses. **Distribution-Aggregate** is the informal name used inside the EIP
site's own URL slug (`DistributionAggregate.html`) and occasionally in older
messaging-vendor documentation, again describing the same two-phase shape.
**Split-Route-Aggregate** is a descriptive label used in integration platform
tutorials (MuleSoft, Camel) that names the three constituent steps directly
rather than giving the composite a name of its own, not a name the original
book uses, but common enough in practitioner writing that a reader should
recognise it as this pattern.

A distinction worth making at the outset, because catalogs frequently blur it.
Composed Message Processor is a structural, request-shape pattern. it says
nothing about whether the fan-out branches run one after another or at the
same time, whether they are synchronous request-response calls or asynchronous
messages correlated later, or how long the aggregation window stays open. Those
are implementation decisions layered on top of the same three-part skeleton,
covered in dimension 8 below.

## 2. Problem and context

A message arrives that logically represents one unit of work, but different
parts of that unit of work belong to different, independent systems, and none
of those systems can process the whole message by itself.

The situation reads like this in a real integration. An order confirmation
needs a shipping cost from the logistics system, a tax calculation from the
finance system, and an inventory hold from the warehouse system, before the
order can be finalized. None of the three systems can answer the whole
question, each answers a slice of it, and the slices do not depend on each
other, only on the original order. The naive first attempt is a single
orchestrating method that calls the three systems one after another and
concatenates the results, and this is not wrong exactly, it is undifferentiated.
it conflates three separable concerns (how do I carve the
message into addressable pieces, where does each piece go, how do I know when
I have heard back from everyone and can proceed) into one procedural block
that nobody can test, reuse, or modify in isolation.

The context that makes Composed Message Processor the right frame, rather than
a synchronous fan-out for its own sake, has three parts.

- The sub-tasks are genuinely independent. none needs the output of another to
  begin, so there is no ordering constraint between them, only a shared
  starting point (the original message) and a shared ending point (the
  combined response).
- The set of destinations is a fixed, known partition of the work, decided at
  design time from the message's own structure (a purchase order has line
  items, a KYC check has three verification providers), not discovered
  dynamically from message content the way a Content-Based Router chooses a
  single destination from many candidates.
- The caller, or the process that raised the original message, genuinely needs
  ONE combined answer back, not N independent ones. If the caller is happy to
  receive N separate replies and reconcile them itself, the composition is not
  earning its place and a plain fan-out without the re-aggregation step is
  simpler.

Hohpe and Woolf frame the pattern around exactly this last point. the
composition exists because the calling code, and the messaging infrastructure
around it, should be able to treat "ask three systems and combine their
answers" as one addressable operation with one request and one response, the
same way Pipes and Filters lets a chain of transformations be treated as one
filter from the outside.

## 3. Forces

- **Latency versus completeness.** Running the sub-tasks in parallel bounds
  the total wait to the slowest branch rather than the sum of all branches,
  but the aggregation step cannot produce a combined answer until it decides
  it has heard enough. A strict wait-for-all policy trades latency for
  completeness, a first-N-of-M or timeout-based policy trades completeness for
  latency. The pattern does not resolve this trade-off, it names the exact
  place in the flow where the trade-off has to be made explicit (the
  Aggregator's completion condition).
- **Coupling to destinations versus flexibility.** The Splitter and the
  routing step must know, at some level, how many pieces to make and where
  each piece goes. Hard-coding that knowledge keeps the flow simple to read
  but means adding a fourth verification provider requires touching the split
  logic. A configuration-driven or metadata-driven split decouples the count
  of destinations from the code, at the cost of a layer of indirection the
  next reader has to learn.
- **Statelessness versus correlation state.** Each split sub-message travels
  independently and may be processed on a different thread, process, or even
  machine than its siblings. The Aggregator therefore needs somewhere to hold
  partial results until the group is complete, which is state the rest of the
  pipeline otherwise does not need. Holding that state in memory is fast and
  simple but does not survive a crash mid-aggregation, holding it in durable
  storage survives a crash but adds a write and a read the in-memory version
  does not pay.
- **Partial-failure semantics.** With N independent branches, some may fail,
  time out, or return an error while others succeed. The pattern forces a
  decision about what a combined response means when it is not complete. is a
  missing branch a fatal error for the whole operation, a null field in an
  otherwise valid response, or a retryable gap. Composed Message Processor
  gives this decision a single home, the Aggregator's completion and
  reconciliation logic, rather than scattering it across every caller.
- **Operability and observability.** A single synchronous call is trivial to
  trace. a fan-out to N asynchronous branches followed by a fan-in is not,
  because a stuck or lost sub-message produces a symptom (the aggregation
  never completes, or completes with a gap) far from its cause (the branch
  that never replied). The pattern trades a simpler failure mode for a harder
  one to diagnose without deliberate correlation-id tracing (dimension 16).

## 4. Applicability and non-applicability

Reach for Composed Message Processor when.

- A logical unit of work genuinely decomposes into independent sub-tasks whose
  destinations are known and fixed at design time, and the caller wants one
  combined result rather than N separate ones.
- The sub-tasks can run in parallel with no ordering dependency between them,
  so composing them buys real latency reduction over doing them in sequence.
- The individual systems that own each sub-task are themselves black boxes you
  do not control, so the only place you can insert the combining logic is
  around the outside of the calls, not inside any one of them.
- You want the three concerns, splitting, routing, and combining, to be
  independently testable, replaceable, and reusable, rather than folded into
  one procedural method.
- You are already inside a messaging or workflow-orchestration substrate
  (a message broker, an integration platform, a workflow engine) that gives
  you Splitter and Aggregator building blocks for free, so composing them costs
  little beyond configuration.

Do NOT reach for it when.

- The sub-tasks have an ordering dependency, where one needs the output of
  another to proceed. That is a pipeline, described by Pipes and Filters or a
  plain sequential chain, and forcing it into a scatter-gather shape only adds
  a synchronization point that does nothing useful, since the branches cannot
  actually run concurrently.
- There is exactly one destination the message could go to, decided by
  inspecting the message's content. That is a Content-Based Router on its own,
  with no split and no aggregation required, and building the full composed
  processor around it is unjustified machinery for a single `if`.
- The caller is genuinely fine receiving each sub-response independently, with
  no need to see them combined. Forcing a synchronous or correlated
  aggregation onto callers who did not ask for one adds a failure mode (the
  aggregation getting stuck) that a set of independent fire-and-forget
  publishes would never have had.
- The sub-tasks are cheap enough, and few enough, that a single synchronous
  method calling them in sequence and returning a plain combined object is
  both correct and trivially understandable. Not every fan-out of two or three
  calls needs a named pattern and a durable correlation store around it. the
  pattern earns its place once the branch count, the latency of any branch, or
  the need for durable partial-failure handling makes ad hoc code brittle.
- The work is a stream with no natural end, where "wait for all N branches" has
  no meaning because N is not known in advance. Windowed stream aggregation is
  a related but distinct problem, usually solved with time- or count-based
  windowing rather than a fixed correlation set.
- Strong consistency across the sub-systems is required, where a partial
  failure must roll every branch back atomically. Composed Message Processor
  combines responses, it does not coordinate a distributed transaction. that
  need points instead to a Saga, discussed in dimension 13.

## 5. Structure

Composed Message Processor names five participants, three of which are
themselves named patterns reused here in a fixed arrangement.

- **Original Message.** The composite message that arrives at the processor,
  carrying all the data needed by every sub-task, plus enough identity
  (an order id, a correlation key) to tie the eventual combined response back
  to the request that produced it.
- **Splitter.** Decomposes the Original Message into a set of Sub-Messages,
  each carrying the slice of data one downstream destination needs, plus a
  shared correlation identifier that ties every sub-message from this split
  back to the same original request.
- **Router (or a fixed set of channels).** Delivers each Sub-Message to the
  system responsible for handling it. In the simplest case this is N
  fixed output channels, one per known destination, in a more dynamic case it
  is a Content-Based Router choosing among a larger set of candidate
  destinations per sub-message.
- **Recipient Systems.** The independent downstream systems, one or more per
  sub-message, that do the actual work and produce a Response Message for
  each Sub-Message they receive. These are outside the processor's own
  boundary and are treated as black boxes.
- **Aggregator.** Collects Response Messages sharing the same correlation
  identifier, holds partial state until its completion condition is met
  (all expected responses arrived, a timeout elapsed, or some other rule
  decided in advance), and emits a single Combined Response Message built by
  applying an aggregation strategy to the collected responses.

The processor as a whole is often wrapped so that, from outside, it looks like
a single addressable operation, an input channel that takes an Original
Message and an output channel that eventually produces exactly one Combined
Response Message, even though internally it fans out to N and back to 1.

## 6. ASCII structure diagram

```
                                Composed Message Processor
                       +--------------------------------------------------+
                       |                                                  |
   Original            |    +-----------+                                |
   Message  ---------->|--->| Splitter  |                                |
                       |    +-----------+                                |
                       |          |                                      |
                       |          v                                      |
                       |    +-----------------------------+              |
                       |    |  sub-message 1  ...  sub-N  |              |
                       |    +-----------------------------+              |
                       |      |        |        |                       |
                       |      v        v        v                       |
                       | +------+ +------+ +------+                      |
                       | |Route1| |Route2| |RouteN|  (fixed channels     |
                       | +------+ +------+ +------+   or a Router)       |
                       |      |        |        |                       |
                       +------|--------|--------|-----------------------+
                              v        v        v
                        +---------+ +---------+ +---------+
                        | System  | | System  | | System  |
                        |   A     | |   B     | |   N     |
                        +---------+ +---------+ +---------+
                              |        |        |
                              v        v        v
                       +------|--------|--------|-----------------------+
                       |    response 1 response 2  response N            |
                       |      \        |        /                       |
                       |       v       v       v                        |
                       |         +-------------+                        |
                       |         | Aggregator  |                        |
                       |         +-------------+                        |
                       |                |                               |
                       +----------------|-------------------------------+
                                         v
                                Combined Response
```

## 7. Dynamics

Two runtime shapes are both faithful to the pattern, which one a given
implementation uses is an implementation-variant decision (dimension 8), not
a change to the structural contract above.

```
Synchronous, request-driven flow (single thread orchestrates, branches run
concurrently, caller blocks until the combined response is ready)

  Caller          Splitter        Route/Send        Systems A..N     Aggregator
    |  request       |                |                  |               |
    |--------------->|                |                  |               |
    |                |-- split ------>|                  |               |
    |                |                |-- call A ------->|               |
    |                |                |-- call B ------->|               |
    |                |                |-- call N ------->|               |
    |                |                |<-- resp A -------|               |
    |                |                |<-- resp B -------|               |
    |                |                |<-- resp N -------|               |
    |                |                |----------------- combine ------->|
    |<----------------------------- combined response ---|               |
```

```
Asynchronous, message-driven flow (branches processed by independent
consumers, possibly on different nodes, correlated by a shared key)

  1. Splitter receives Original Message, assigns correlation-id C,
     publishes sub-message[1..N] each tagged with C, to N destination channels.
  2. Each Recipient System consumes its sub-message independently, at its own
     pace, and publishes a Response Message back, tagged with the same C.
  3. Aggregator subscribes to the response channel(s), keyed by correlation-id.
     For each arriving response it appends to the partial-result store for C.
  4. On every arrival, Aggregator evaluates its completion condition against
     the partial-result store for C.
       a. "all N expected responses present" then emit Combined Response,
          clear state for C.
       b. timeout elapsed since first response for C then emit Combined
          Response with whatever is present, mark missing branches, clear
          state for C.
  5. If neither condition is met, the Aggregator waits for the next arrival.
```

The asynchronous shape is the one that most exposes the pattern's real cost.
step 3 needs somewhere durable enough to survive between arrivals, which is
exactly the correlation state discussed under forces and under failure modes.

## 8. Implementation variants

- **Synchronous parallel fan-out.** The orchestrating code issues the N calls
  concurrently (a thread pool, `Promise.all`, `asyncio.gather`, a `WaitGroup`
  in Go) and blocks until all complete or a timeout fires, then combines the
  in-memory results directly. No message broker and no durable correlation
  state are needed, because the calling stack frame itself is the
  correlation context. This is the shape most application code reaches for
  first, and it is a fully faithful implementation of the pattern when the
  branch count is small and the caller is willing to hold a connection open
  for the duration.
- **Message-broker-mediated, correlation-id keyed.** Each sub-message and its
  eventual response carry a shared correlation identifier (often the EIP
  Correlation Identifier pattern), and a separate Aggregator component or
  broker-native aggregation feature (a JMS `Aggregator`, a Kafka Streams
  stateful transform, a Camel `AggregationStrategy`) accumulates responses
  keyed by that identifier in a store external to any single request's call
  stack. This is the shape required once branches may run on different
  processes, at different speeds, or after a broker-mediated delay, and it is
  the shape that survives a consumer crash mid-flight, because the partial
  state lives outside the consumer that crashed.
- **Workflow-engine orchestrated (Map / Parallel state).** Rather than hand
  writing the split, dispatch, and join, a workflow engine's built-in
  construct performs it declaratively. AWS Step Functions' `Map` state runs a
  set of workflow steps once per item in an input array, in either an Inline
  mode capped at 40 concurrent iterations sharing the parent's execution
  history, or a Distributed mode supporting up to 10,000 concurrent child
  workflow executions each with its own execution history
  (https://docs.aws.amazon.com/step-functions/latest/dg/amazon-states-language-map-state.html,
  verified 2026-08-02). Azure Logic Apps' `splitOn` trigger property debatches
  an incoming array and runs one workflow instance per item, restricted to
  triggers that both accept and return arrays such as Request, HTTP, and
  Service Bus
  (https://learn.microsoft.com/en-us/azure/logic-apps/logic-apps-workflow-actions-triggers,
  verified 2026-08-02).
- **Timeout-bounded partial aggregation.** The Aggregator's completion
  condition is not "all N present" but "all N present, or T seconds elapsed
  since the first response, whichever comes first", trading completeness for
  a latency bound. This variant requires the combined-response schema to be
  able to represent a missing branch (a null field, a per-branch status flag)
  rather than assuming every field is always populated.
- **Streaming split, bounded aggregation window.** For very large or unbounded
  composite inputs, the Splitter does not materialize the full set of
  sub-messages in memory before dispatch. Apache Camel's `split` EIP supports
  a streaming mode that processes the split expression's result on demand via
  an iterator rather than loading the entire source into memory first, at the
  cost of not knowing the total item count in advance
  (https://camel.apache.org/components/latest/eips/split-eip.html, verified
  2026-08-02). The corresponding Aggregator side then needs a windowing or
  count-based completion strategy rather than a fixed "wait for N".

## 9. Known production uses

- **Apache Camel's `split` EIP with an `AggregationStrategy`.** Camel
  implements Composed Message Processor directly as two composable EIP steps.
  the `split` processor divides a message into pieces using an expression
  (an XPath, a list, a delimiter), each piece is routed through the rest of
  the route, and an `AggregationStrategy` combines the split exchanges back
  into a single outgoing message, with the default strategy returning
  the original input if none is supplied
  (https://camel.apache.org/components/latest/eips/split-eip.html, verified
  2026-08-02).
- **AWS Step Functions' `Map` state.** Step Functions' Amazon States Language
  provides `Map` as a first-class state type that runs a set of workflow
  steps once per item in a dataset, with the iterations executing in
  parallel, and two processing modes (Inline, up to 40 concurrent iterations
  in the parent's history, and Distributed, up to 10,000 concurrent child
  workflow executions each with an independent execution history) chosen
  based on dataset size and required concurrency
  (https://docs.aws.amazon.com/step-functions/latest/dg/amazon-states-language-map-state.html,
  verified 2026-08-02).
- **Azure Logic Apps' Split On (debatch) trigger property.** The `splitOn`
  property on a trigger definition debatches an array from the trigger's
  response and runs one workflow instance per array item in parallel, and is
  restricted to trigger types that both accept and return arrays, such as
  Request, HTTP, Azure Service Bus, and Office Outlook 365
  (https://learn.microsoft.com/en-us/azure/logic-apps/logic-apps-workflow-actions-triggers,
  verified 2026-08-02).
- **Microsoft's Scatter-Gather cloud design pattern.** The Azure Architecture
  Center documents Scatter-Gather as a named cloud pattern for broadcasting a
  request to multiple services and aggregating the results, presenting it as
  the same shape the EIP catalog calls Composed Message Processor and citing
  Hohpe and Woolf as the pattern's origin (Microsoft Azure Architecture
  Center, Cloud Design Patterns catalog, Scatter-Gather pattern entry).

## 10. Consequences

**Positive.**

- Total latency for the whole operation is bounded by the slowest branch
  rather than the sum of all branches, because the sub-tasks run concurrently
  once the message has been split.
- The three concerns, splitting, routing, and aggregating, become
  independently testable and replaceable units, so a new destination is added
  by extending the split and route logic without touching the aggregation
  rule, and vice versa.
- The caller and the rest of the surrounding flow see a single request and a
  single response, so the internal fan-out is an implementation detail that
  can change (add a branch, change a branch's completion contribution)
  without changing the contract the rest of the system depends on.
- Partial-failure handling has one home, the Aggregator's completion and
  reconciliation logic, rather than being duplicated in every place that
  calls the recipient systems.

**Negative.**

- The Aggregator must hold correlation state for every in-flight composite
  request until it completes, which is state the individual recipient
  systems never needed to think about and which must itself be sized,
  monitored, and recovered on restart.
- A slow or lost response from a single branch can stall the entire combined
  response indefinitely unless a timeout or partial-completion policy is
  explicitly designed in, turning one flaky downstream system into an outage
  for every composite request that happens to route through it.
- Debugging a stuck aggregation requires correlating events across N
  independent branches, each potentially on a different node, which is
  strictly harder than tracing a single synchronous call chain and demands
  deliberate correlation-id propagation to be tractable at all.
- The combined response's schema has to account for the possibility that some
  branches never answered, which pushes complexity into every consumer of the
  combined response that would not exist if each branch's answer were simply
  used on its own.

## 11. Failure modes and misuse

- **Symptom.** The combined response never arrives, and no error is ever
  raised. **Cause.** The Aggregator's completion condition is "all N present"
  with no timeout, and one branch's recipient system silently drops the
  sub-message or never replies. **Fix.** Add an explicit timeout-based
  completion path, and alert on correlation entries that exceed it, rather
  than treating "all N present" as the only exit from the aggregation state.
- **Symptom.** Under load, the Aggregator's memory or storage grows without
  bound and eventually the process is killed. **Cause.** Correlation entries
  for completed or timed-out groups are never explicitly cleared from the
  partial-result store, so every request that ever entered the system leaves
  a permanent, growing footprint. **Fix.** Clear the correlation entry the
  moment its completion condition fires, whether that is full success or a
  timeout, and add a background sweep for entries that somehow escaped both.
- **Symptom.** Two different callers see two different combined results for
  what looks like the same correlation id. **Cause.** Correlation identifiers
  were generated with too little entropy or scope, or were reused across
  requests (a business key like an order number used directly, instead of a
  fresh id per split operation), so responses from an unrelated request are
  aggregated into the wrong group. **Fix.** Generate a fresh, sufficiently
  unique correlation id per split operation, distinct from any business
  identifier, even if the business identifier is also carried for
  traceability.
- **Symptom.** The system that should be fanning work out to independent
  branches is instead calling them one after another with no concurrency
  benefit, despite the code being organized as a Composed Message Processor.
  **Cause.** The branches were implemented as a sequential loop awaiting each
  call before starting the next, which preserves the structural shape of
  Splitter, Route, Aggregator but silently drops the concurrency the pattern
  exists to provide. **Fix.** Verify explicitly that the dispatch step issues
  all N calls before awaiting any of them, using the language's genuine
  concurrency primitive rather than a sequential await inside a loop.
- **Misuse.** Reaching for Composed Message Processor when the sub-tasks
  actually have an ordering dependency, then working around the dependency
  with ad hoc waits or polling inside the Aggregator. This is a sign the
  problem is a pipeline, not a fan-out, and should be restructured as
  Pipes and Filters instead of forcing it through this pattern's shape.
- **Misuse.** Using the pattern's aggregation step as a substitute for
  transactional consistency across the recipient systems, silently ignoring
  that a partial success (2 of 3 branches committed real side effects, one
  failed) leaves the underlying systems in a state the combined response does
  not reflect or repair. If the branches perform side effects that must be
  atomic across all of them, the correct pattern is a Saga with compensating
  actions, not a message aggregation.

## 12. Trade-off matrix

| Force | Composed Message Processor | Sequential Pipes and Filters | Content-Based Router alone | Distributed Saga |
|---|---|---|---|---|
| Latency for independent sub-tasks | Bounded by slowest branch, all run concurrently | Sum of every stage's latency, always | N or A, only one destination is chosen | Depends on saga step ordering, often sequential |
| Handles ordering dependencies between sub-tasks | No, assumes independence | Yes, that is its entire purpose | N or A | Yes, steps are explicitly ordered |
| Produces one combined response | Yes, by design | Yes, one final output after the chain | No, one response from the chosen destination | Not necessarily, saga tracks completion, not a merged payload |
| Needs correlation state held across calls | Yes, the Aggregator's partial-result store | No, state is only the value passed stage to stage | No | Yes, the saga's own state machine |
| Handles side-effect consistency across branches | No, combines data, not transactions | N or A, usually no side effects to coordinate across stages | N or A | Yes, that is its entire purpose, via compensation |
| Cost when only one destination is ever needed | Wasted split and aggregate machinery | N or A, wrong shape entirely | Correct minimal shape | Wrong shape, no compensation needed for one call |

## 13. Related and incompatible patterns

- **Splitter.** The first of the two constituent patterns. Composed Message
  Processor is meaningless without it, since there is nothing to route or
  aggregate until the original message has been decomposed.
- **Aggregator.** The second constituent pattern, and the one that carries
  most of the pattern's operational risk (correlation state, completion
  conditions, partial-failure handling), discussed at length above.
- **Content-Based Router.** Used inside the routing step when the destination
  for a given sub-message is not fixed but chosen from several candidates
  based on the sub-message's own content. When the destinations are a fixed,
  small set known at design time, a plain set of output channels replaces the
  router entirely.
- **Pipes and Filters.** The architectural style the whole composed processor
  sits inside from the outside. the composed processor is itself one filter
  in a larger pipeline, even though internally it fans out and back in. it is
  also the pattern to reach for instead of Composed Message Processor when the
  sub-tasks actually have an ordering dependency.
- **Scatter-Gather.** Not a distinct pattern from this one, but the name most
  commonly used for the identical shape outside the original EIP catalog,
  particularly in cloud architecture and service mesh writing. A reader who
  learns one name should recognise the other as the same thing.
- **Saga.** Composes with, but is not interchangeable with, Composed Message
  Processor. A saga coordinates ordered steps with compensating actions to
  keep side effects consistent across independent systems, a Composed Message
  Processor collects independent, unordered results into one combined
  response with no transactional guarantee across branches. A workflow may
  legitimately contain a Composed Message Processor as one step inside a
  larger saga.
- **Correlation Identifier and Message Endpoint.** The two smaller EIP
  primitives that make the asynchronous variant of this pattern practical.
  every sub-message and response needs a Correlation Identifier so the
  Aggregator can group them, and each recipient system is addressed through
  its own Message Endpoint.

## 14. Refactoring path in and out

**Introducing the pattern into code that does not have it.** Start from the
sequential version, a method that calls system A, then system B, then system
N, awaiting each before starting the next, and combines the results at the
end. First verify the calls genuinely have no ordering dependency between
them, since that check is the whole basis for the refactor being safe. Next,
change the dispatch to issue all N calls before awaiting any of them, using
the language's concurrency primitive (`Promise.all`, `asyncio.gather`, a
`sync.WaitGroup`), which alone captures most of the latency benefit with no
structural change otherwise. If the branches must run on different processes
or the composite request must survive a crash mid-flight, extract the
dispatch into an explicit Splitter that assigns a correlation id and publishes
to named channels, and extract the combination logic into an explicit
Aggregator that holds partial state keyed by that id and defines its own
completion condition, including an explicit timeout path. Only at this last
step does the code genuinely need a message broker or workflow engine
underneath it, the earlier steps are valid, complete implementations of the
pattern on their own.

**Removing the pattern when it stops earning its place.** If the recipient
systems have been consolidated so that one call now answers what used to take
N separate calls, or if the branch count has shrunk to one and stayed there,
collapse the split, route, and aggregate steps back into a single direct call
and delete the correlation state entirely, since an Aggregator holding state
for exactly one branch is pure overhead. If a downstream consumer turns out to
be fine receiving each branch's response independently and never actually
reads the combined response, remove the Aggregator and let each branch publish
directly to that consumer, which also removes the single-point stall risk
discussed in dimension 11.

## 15. Testing and verification

Test the three constituent parts in isolation before testing the composition.
The Splitter is tested as a pure function from one input message to a known
set of sub-messages, each carrying the correlation id and the correct slice
of data, with no network or broker involved. The Aggregator is tested with a
test double standing in for the recipient systems, feeding it a controlled
sequence of arriving responses (all N in order, all N out of order, N minus
one plus a timeout, a duplicate response for the same branch) and asserting
the exact combined response or completion decision each sequence should
produce, this is where most of the pattern's real complexity lives and where
most of the test budget should go. The routing step, when it is a fixed set of
channels, needs only a table test asserting each sub-message type reaches its
declared destination, when it is a Content-Based Router, it is tested the same
way that pattern is tested on its own.

For the composed whole, an end-to-end test should specifically include the
partial-failure cases that unit tests of the Aggregator alone can miss if the
wiring between components is wrong. one recipient system genuinely
unreachable, one recipient system responding after the timeout has already
fired, two composite requests in flight concurrently to confirm their
correlation state does not cross-contaminate. A test suite that only ever
exercises the all-N-succeed happy path has not tested the pattern, since the
happy path is the one case where a Composed Message Processor and a plain
sequential call produce identical externally visible behaviour.

## 16. Observability signals

Every sub-message and every response should carry, and every log line and
trace span should surface, the correlation id that ties them to the original
request, since that id is the only thing that lets an operator reconstruct
which branches belong to which stalled or slow composite request. A healthy
Aggregator's dashboard shows the number of in-flight correlation groups
staying roughly flat relative to incoming request rate times expected
completion time, and a completion-latency histogram concentrated well under
the configured timeout. An unhealthy one shows the in-flight-groups gauge
climbing without bound (a leak in clearing completed or timed-out entries, see
dimension 11), a growing count of groups that hit the timeout path rather than
the all-present path (a specific recipient system degrading), or a
completion-latency histogram with a long tail approaching the timeout value
(the timeout is masking a real upstream slowdown rather than genuinely
protecting against a hung branch). Per-destination metrics on the routing step,
count and latency broken down by which recipient system each sub-message went
to, isolate which branch is responsible for a degraded aggregation latency
without needing to inspect individual correlation groups.

## 17. Security and privacy implications

This dimension is partly engineering judgement rather than a sourced claim,
since the EIP catalog itself does not treat security as a dimension of the
pattern. Splitting a composite message multiplies the number of places a
sensitive field can appear, since data that lived in one message now lives in
N sub-messages, each potentially traveling to a different, independently
operated system, so the field-level access each recipient needs should be
reviewed at the point the Splitter decides what each sub-message carries,
rather than propagating the entire original message to every branch by
default. The Aggregator's correlation store is itself a data-at-rest surface
that did not exist before the pattern was introduced, since it necessarily
holds a combination of data from every branch until completion, and it should
be subject to the same retention and access controls as the most sensitive
field passing through any single branch, not the least sensitive one. A
timeout-based partial completion path that returns a combined response with
missing branches should be careful not to let the shape or presence of a
missing field leak information about a downstream system's availability or
internal state to a caller who should not be able to infer it. Finally,
because a stuck aggregation is an availability failure by construction
(dimension 11), an attacker who can cause one recipient system to stop
responding, without needing to compromise it, can degrade or deny the whole
composite operation unless a timeout and partial-completion policy is in
place, which is a denial-of-service consideration specific to this pattern's
shape rather than to the recipient systems individually.

## 18. References

- Gregor Hohpe, Bobby Woolf, *Enterprise Integration Patterns. Designing,
  Building, and Deploying Messaging Solutions*, Addison-Wesley, 2003, Message
  Routing chapter, Composed Message Processor.
- Enterprise Integration Patterns, Composed Message Processor pattern page,
  https://www.enterpriseintegrationpatterns.com/patterns/messaging/DistributionAggregate.html,
  verified 2026-08-02.
- Apache Camel documentation, Split EIP,
  https://camel.apache.org/components/latest/eips/split-eip.html, verified
  2026-08-02.
- Amazon Web Services, AWS Step Functions Developer Guide, Map workflow
  state, https://docs.aws.amazon.com/step-functions/latest/dg/amazon-states-language-map-state.html,
  verified 2026-08-02.
- Microsoft, Azure Logic Apps documentation, workflow triggers and actions,
  Split On (debatch) property,
  https://learn.microsoft.com/en-us/azure/logic-apps/logic-apps-workflow-actions-triggers,
  verified 2026-08-02.
- Microsoft, Azure Architecture Center, Cloud Design Patterns catalog,
  Scatter-Gather pattern entry (attribution to Hohpe and Woolf noted in the
  pattern's own description).

## Code examples

### TypeScript

```typescript
type SubResponse = { source: string; value: number };

async function fetchFromA(): Promise<SubResponse> {
  return { source: "A", value: 10 };
}
async function fetchFromB(): Promise<SubResponse> {
  return { source: "B", value: 20 };
}
async function fetchFromN(): Promise<SubResponse> {
  return { source: "N", value: 30 };
}

async function composedProcessor(): Promise<number> {
  const results = await Promise.all([fetchFromA(), fetchFromB(), fetchFromN()]);
  return results.reduce((sum, r) => sum + r.value, 0);
}

composedProcessor().then((total) => console.log("combined", total));
```

### Python

```python
import asyncio


async def fetch_from_a():
    return {"source": "A", "value": 10}


async def fetch_from_b():
    return {"source": "B", "value": 20}


async def fetch_from_n():
    return {"source": "N", "value": 30}


async def composed_processor():
    results = await asyncio.gather(fetch_from_a(), fetch_from_b(), fetch_from_n())
    return sum(r["value"] for r in results)


if __name__ == "__main__":
    total = asyncio.run(composed_processor())
    print("combined", total)
```

### Go

```go
package main

import (
	"fmt"
	"sync"
)

type Response struct {
	Source string
	Value  int
}

func fetchFrom(source string, value int, out chan<- Response, wg *sync.WaitGroup) {
	defer wg.Done()
	out <- Response{Source: source, Value: value}
}

func composedProcessor() int {
	responses := make(chan Response, 3)
	var wg sync.WaitGroup
	wg.Add(3)
	go fetchFrom("A", 10, responses, &wg)
	go fetchFrom("B", 20, responses, &wg)
	go fetchFrom("N", 30, responses, &wg)

	go func() {
		wg.Wait()
		close(responses)
	}()

	total := 0
	for r := range responses {
		total += r.Value
	}
	return total
}

func main() {
	fmt.Println("combined", composedProcessor())
}
```

All three samples model the synchronous parallel fan-out variant from
dimension 8. dispatch all branches concurrently, then combine once every
branch has replied. Java and Rust were available on this machine but were not
used for this entry. the pattern's idiomatic shape in Java (an
`ExecutorService` with `CompletableFuture.allOf`) and in Rust (`tokio::join!`
or `futures::future::join_all`) is a close structural match to the Go and
TypeScript samples above with no distinct variant worth a fourth listing.
