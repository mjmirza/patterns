---
name: Scatter-Gather
slug: scatter-gather
family: 07-integration
category: Enterprise Integration Pattern
aliases: [Fan-Out/Fan-In, Parallel Broadcast Recipient List, Distribution Aggregate]
first_described: "Hohpe, Woolf, Enterprise Integration Patterns, 2003"
maturity: canonical
related: [recipient-list, aggregator, publish-subscribe-channel, correlation-identifier, message-sequence, dead-letter-channel, circuit-breaker]
incompatible_with: [point-to-point-channel]
verified: 2026-08-02
---

## 1. Name, aliases, and lineage

The canonical name is Scatter-Gather, defined by Gregor Hohpe and Bobby Woolf
in "Enterprise Integration Patterns. Designing, Building, and Deploying
Messaging Solutions" (Addison-Wesley, 2003), chapter 9, in the section on
Message Routing. The pattern's own page states its intent directly. broadcast
a message to multiple recipients and re-aggregate the responses back into a
single message (Hohpe and Woolf, verified at
https://www.enterpriseintegrationpatterns.com/patterns/messaging/BroadcastAggregate.html
on 2026-08-02, which is the pattern's living reference page and carries the
canonical structure diagram this entry's own diagram is redrawn from, not
copied from).

Outside the Enterprise Integration Patterns (EIP) literature the same shape is
called Fan-Out/Fan-In, a term with roots in electronics (a gate's fan-out is
the number of inputs it can drive) that migrated into distributed systems
literature to describe one request producing many parallel sub-requests whose
results converge again. The term appears with that meaning in AWS's own
reference architecture guidance for Step Functions, which documents a
"Fan-out message processing" pattern using an SQS queue and a Lambda function
to distribute work and a second Lambda to collect results (AWS Prescriptive
Guidance, "Fan-out message processing using Amazon SQS and AWS Lambda",
verified at
https://docs.aws.amazon.com/prescriptive-guidance/latest/patterns/fan-out-message-processing-using-amazon-sqs-and-aws-lambda.html
on 2026-08-02). Martin Fowler does not name the pattern directly in his own
catalog but it is treated as a specialization of the Recipient List pattern
combined with the Aggregator pattern, both catalogued in the same EIP book,
chapters 8 and 10 respectively.

A third name found in academic distributed-systems texts is Parallel
Broadcast Recipient List, used to distinguish it from a Recipient List whose
recipients are invoked sequentially. This entry treats Scatter-Gather,
Fan-Out/Fan-In, and Parallel Broadcast Recipient List as the same structural
idea described from three vantage points, messaging architecture (EIP),
serverless orchestration (AWS), and academic distributed computing.
Scatter-Gather is the name this entry uses throughout because it is the term
with the clearest, most stable, most cited primary source.

## 2. Problem and context

A caller needs an answer that no single system holds in full. The classic
motivating example from the EIP catalog itself is a purchase request that
must be priced by several competing suppliers, where the best price is only
knowable after every supplier has quoted (Hohpe and Woolf, EIP, chapter 9,
Broadcast Aggregate section). A travel-booking search that must check flight
availability across five airlines before showing results to a user is the
same shape. A fraud-detection system that must query a credit bureau, a
device-reputation service, and an internal risk model before approving a
transaction is the same shape again.

The problem context has three recurring properties. First, the answer
depends on querying multiple independent sources or independent replicas of
the same source, and no single one of them can substitute for the others.
Second, the sources can be queried in parallel because they do not depend on
each other's answers, which means the wall-clock cost of asking them one
at a time is wasted latency the system does not need to pay. Third, the
caller cannot proceed with a partial answer forever. At some point the system
must decide it has gathered enough responses, whether that means all of
them, a fixed subset, or whatever arrived before a deadline, and move on.

This differs from a plain Recipient List (Hohpe and Woolf, EIP, chapter 8),
which routes a single message to a computed list of recipients but does not
by itself specify that the results must be reassembled into one reply. It
also differs from Publish-Subscribe Channel (Hohpe and Woolf, EIP, chapter 6),
which is a topology for delivering a message to many interested subscribers
with no expectation that any of them replies at all, let alone that the
replies converge. Scatter-Gather is specifically the combination of parallel
broadcast on the way out and mandatory correlation and aggregation on the way
back.

## 3. Forces

Latency is the force the pattern exists to trade against everything else. A
sequential request to N recipients costs the sum of N latencies. A scattered
request costs roughly the maximum of the N latencies, plus the fixed
overhead of dispatch and aggregation. This is the whole reason to reach for
the pattern, and every other force below is a cost paid to obtain it.

Coupling rises on the aggregator side even as it may fall on the recipient
side. Each recipient can be entirely ignorant of the others, which is loose
coupling in one direction. But the aggregator must understand, for every
recipient it might scatter to, what a valid response looks like, how to
correlate it back to the original request, and what to do if that recipient
never answers. That knowledge is concentrated coupling, moved rather than
removed.

Consistency is sacrificed by construction. The gathered result reflects
whichever recipients answered inside the collection window, not necessarily
the true, up-to-date state of every recipient at a single instant. A stock
price scatter-gather across three exchanges answered eighty milliseconds
apart is not a snapshot of a single moment, it is a best-effort composite.
Systems that need linearizable consistency across sources should not reach
for this pattern.

Operability cost is real and often underestimated. A sequential call chain
fails in an obvious place, the call that threw. A scattered call fails in a
combinatorial space, which of N recipients responded, which timed out, which
returned malformed data, and whether the aggregation logic handled the
partial set correctly. Debugging a scatter-gather failure requires
correlating logs across every branch, which is why Correlation Identifier
(Hohpe and Woolf, EIP, chapter 10) is treated below as a near-mandatory
companion rather than an optional extra.

Cost, in the literal financial sense, multiplies by the fan-out factor.
Scattering a request to five paid APIs to answer one user query means paying
for five API calls per query rather than one, even for the recipients whose
answer the aggregator ultimately discards. This is a real design
constraint in systems that scatter to metered third-party services, and it
is one of the reasons the non-applicability list below includes cases where
the recipient set is large or the calls are expensive.

Team topology and cognitive load interact with the pattern less obviously
but persistently. Each recipient can, and often should, be owned by a
separate team, which is a genuine benefit under Conway's Law reasoning. the
airline-pricing team owns the airline adapter, the hotel-pricing team owns
the hotel adapter, and neither needs to understand the aggregator's
correlation logic. The cost is that the person debugging a bad aggregated
result at 3 a.m. must reason across all of those team boundaries at once,
which is a cognitive load the sequential alternative does not impose.

## 4. Applicability and non-applicability

Use Scatter-Gather when the request genuinely needs input from more than one
independent source and those sources can be queried without waiting on each
other. Use it when the aggregation logic to combine the results is itself
simple enough to reason about, such as best-price selection, majority vote,
or set union, because a scatter-gather whose aggregation step is more
complex than the scattering step has usually mis-modeled the problem. Use it
when a partial result is an acceptable outcome, meaning the system has a
defined policy for what to do if some recipients never answer, whether that
policy is proceed with whoever answered, or fail the whole request. Use
it when the recipient count is small and bounded, typically single digits to
low tens, because the pattern's overhead and failure-mode complexity both
grow with fan-out width.

Do not use Scatter-Gather when a single authoritative source already holds
the answer. Scattering to five replicas of the same database to be safe is
needless complexity that a simple Content-Based Router or a direct call
already solves more cheaply, and the EIP catalog's own commentary on
Recipient List warns against constructing a distribution list when a single
recipient would do (Hohpe and Woolf, EIP, chapter 8, Recipient List, related
patterns discussion). Do not use it when the recipients must see each
other's answers before responding, because that is a sequential dependency
the pattern's parallelism cannot honor. That shape belongs to a Pipes and
Filters chain or a saga, not a scatter-gather. Do not use it when the fan-out
count is large and unbounded, such as broadcasting to every tenant in a
multi-tenant system, because the tail latency of the slowest recipient sets
the pace for the whole operation and a single misbehaving recipient can
stall every request. That shape is better served by Publish-Subscribe
Channel with independent consumers that do not block a synchronous caller.
Do not use it when strict transactional consistency across the recipients is
required, because the pattern has no native mechanism to roll back a partial
scatter if one recipient's side effect must be undone when another recipient
fails. That is the domain of the Saga pattern and two-phase commit
protocols, not Scatter-Gather. Do not use it as a substitute for caching. If
the same five recipients are queried for the same input repeatedly,
memoizing the aggregate result is cheaper than re-scattering every time and
defeats the purpose of the pattern's stated benefit, which is latency
reduction on a genuinely novel request.

## 5. Structure

The pattern has three structural participants and one structural artifact
that ties them together.

The Requestor is the component that has a request needing input from
multiple sources. It does not know or care how many recipients exist or how
the request reaches them, it hands the request to the Distributor and later
receives one aggregated reply.

The Distributor, sometimes drawn as the scatter half of the pattern and
sometimes merged with the aggregator into a single logical component, takes
the incoming request, generates a correlation identifier for it, and sends a
copy of the request to each Recipient in the recipient set. The recipient
set can be statically configured or dynamically computed, in which case the
Distributor is itself built on top of the Recipient List pattern (Hohpe and
Woolf, EIP, chapter 8), which is precisely why Recipient List is listed as a
directly related pattern in dimension 13 below rather than merely a distant
cousin.

Each Recipient is an independent participant capable of processing the
request and producing a response asynchronously, without knowledge of the
other recipients. A Recipient may be a remote service, an internal
subsystem, or a local computation, the pattern is agnostic to what a
recipient actually is, only that it can accept the scattered message and
eventually produce a response carrying the same correlation identifier.

The Aggregator collects responses that carry the same correlation
identifier, applies a completion strategy to decide when it has gathered
enough of them, and reduces the collected set into a single aggregated
reply which it sends back to the Requestor. The Aggregator's internal
mechanics are the Aggregator pattern in full (Hohpe and Woolf, EIP,
chapter 10), and Scatter-Gather is frequently described in the literature as
Recipient List feeding an Aggregator, a composition explicit in the EIP
book's own pattern relationships.

## 6. ASCII structure diagram

```
                          +------------------+
                          |    Requestor     |
                          +--------+---------+
                                   |
                          (1) single request
                                   |
                                   v
                          +------------------+
                          |   Distributor    |
                          |  (scatter half)  |
                          +--------+---------+
                                   |
              +--------------------+--------------------+
              |                    |                     |
       (2) copy w/     (2) copy w/           (2) copy w/
       correlation-id  correlation-id        correlation-id
              |                    |                     |
              v                    v                     v
     +----------------+  +----------------+  +----------------+
     |  Recipient A   |  |  Recipient B   |  |  Recipient C   |
     +-------+--------+  +-------+--------+  +-------+--------+
             |                    |                     |
      (3) response A       (3) response B        (3) response C
      w/ correlation-id    w/ correlation-id      w/ correlation-id
             |                    |                     |
             +--------------------+---------------------+
                                   |
                                   v
                          +------------------+
                          |    Aggregator    |
                          |  (gather half)   |
                          |  completion      |
                          |  strategy +      |
                          |  reduce fn       |
                          +--------+---------+
                                   |
                        (4) single aggregated
                              reply
                                   |
                                   v
                          +------------------+
                          |    Requestor     |
                          +------------------+
```

## 7. Dynamics

The runtime flow separates cleanly into a scatter phase and a gather phase,
joined by a correlation identifier that must be generated once, at scatter
time, and carried unchanged through every recipient's response.

```
Requestor          Distributor        Recipient A   Recipient B   Recipient C   Aggregator
   |                    |                   |             |             |            |
   |--- request ------->|                   |             |             |            |
   |                    | gen correlation-id=CID           |             |            |
   |                    |--- req[CID] ----->|             |             |            |
   |                    |--- req[CID] ------------------->|             |            |
   |                    |--- req[CID] --------------------------------->|            |
   |                    |                   |             |             |            |
   |                    |         (recipients process independently,   |            |
   |                    |          no ordering guarantee between them) |            |
   |                    |                   |             |             |            |
   |                    |                   |--- resp[CID,A] --------------------->  |
   |                    |                   |             |--- resp[CID,B] ------->  |
   |                    |                   |             |             |--- (timeout, no reply)
   |                    |                   |             |             |            |
   |                    |                   |             |             |    completion strategy,
   |                    |                   |             |             |    2 of 3 within window,
   |                    |                   |             |             |    proceed without C
   |                    |                   |             |             |            |
   |                    |                   |             |             |    reduce(A, B) -> result
   |<----------------------------------------------------------------------- result -|
   |                    |                   |             |             |            |
```

The critical property this diagram is drawn to show is that the Aggregator's
completion decision is a policy point, not an automatic property of the
message flow. Nothing in the messaging infrastructure tells the Aggregator
when it has enough responses, the Aggregator's completion strategy, one of
wait for all, wait for a fixed count, or wait until a deadline, is where the
pattern's central design decision lives, and it is the decision most often
under-specified in real implementations, which is why dimension 11 treats
an unbounded or absent completion strategy as the pattern's most common
failure mode.

## 8. Implementation variants

The synchronous fan-out-with-a-deadline variant runs the scatter calls as
concurrent futures or promises inside a single request-handling thread or
async task, then joins them with a bounded wait. This is the shape most
commonly implemented directly in application code without any messaging
middleware at all, using language-level concurrency primitives such as
`Promise.all` with a race against a timeout in JavaScript, `asyncio.gather`
with `asyncio.wait_for` in Python, or a `WaitGroup` combined with a `select`
over a timer channel in Go. It is the cheapest variant to implement and the
one this entry's working code demonstrates, because it requires no
infrastructure beyond the language runtime.

The message-broker variant, which is the shape the original EIP catalog
describes, sends the scattered messages onto a broker with each carrying a
correlation identifier and a reply-to address, and the Aggregator is a
long-lived consumer that correlates responses arriving asynchronously,
potentially over seconds or minutes rather than milliseconds. This is the
variant used when recipients are independently deployed services that may
be slow, may retry, or may be temporarily offline, and it typically depends
on the Correlation Identifier and Message Sequence patterns to let the
Aggregator know both which request a response belongs to and, if the
recipient set is known up front, how many responses to expect. Apache Camel
implements this variant directly as a first-class EIP component named
Scatter-Gather in its own documentation, described as a version of the
recipient list where you split a message and route them to a list of dynamic
recipients whose results are combined by an `AggregationStrategy` (Apache
Camel documentation, "Scatter Gather", verified at
https://camel.apache.org/components/4.22.x/eips/scatter-gather.html on
2026-08-13, which documents the recipients being sent to dynamically via a
recipient list expression and the reply reassembled with a strategy exactly
matching the Distributor and Aggregator participants above).

The serverless step-function variant, common in cloud architectures,
implements scatter as a Map state or a parallel Lambda invocation fan-out
and implements gather as a downstream Lambda or Step Functions Parallel
state that waits on all branches. AWS's own prescriptive guidance names this
exact composition, describing an architecture where a message is fanned out
to an SQS queue consumed by multiple Lambda workers and their results
fanned back in by a collector function, explicitly as a fan-out message
processing pattern (AWS Prescriptive Guidance, verified 2026-08-02, cited
above).

The saga-adjacent compensating variant adds a rollback branch to the gather
phase. If the completion strategy determines the aggregate cannot succeed,
for example a mandatory recipient never responded, the aggregator issues
compensating actions to the recipients that did respond, undoing whatever
side effect their response implied. This variant borrows directly from the
Saga pattern's compensating-transaction vocabulary and is used specifically
when recipients have side effects, such as reserving inventory or holding a
price quote, rather than being pure read queries.

## 9. Known production uses

Apache Camel ships Scatter-Gather as a documented, named enterprise
integration pattern component, implementing exactly the recipient-list-then-
aggregate structure this entry describes, configurable with a custom
`AggregationStrategy` bean for the reduce step (Apache Camel documentation,
"Scatter Gather EIP", verified at
https://camel.apache.org/components/4.22.x/eips/scatter-gather.html on
2026-08-13).

Spring Integration, the Spring Framework's messaging module, implements the
pattern as a first-class Java component named `ScatterGatherHandler`,
documented in the official Spring Integration reference manual under the
Scatter-Gather section, which states the component's job is to send an
input message to a Recipient List or Publish-Subscribe channel and wait for
replies to aggregate them, describing the two-phase process as scatter and
gather using that exact terminology (Spring Integration Reference Manual,
"Scatter-Gather", verified at
https://docs.spring.io/spring-integration/reference/scatter-gather.html on
2026-08-02).

AWS documents the fan-out message processing shape as a named reference
architecture in its Prescriptive Guidance catalog, specifically the pattern
of distributing messages to an SQS queue for parallel processing by Lambda
functions and aggregating results downstream, and the same catalog
separately documents AWS Step Functions' Parallel and Map states as the
managed-orchestration mechanism for the identical scatter phase inside a
state machine (AWS Prescriptive Guidance, "Fan-out message processing using
Amazon SQS and AWS Lambda", verified at
https://docs.aws.amazon.com/prescriptive-guidance/latest/patterns/fan-out-message-processing-using-amazon-sqs-and-aws-lambda.html
on 2026-08-02).

MuleSoft's Anypoint integration platform documents a Scatter-Gather routing
component with that exact name, described in its own reference
documentation as an element that routes a message to multiple targets
concurrently and gathers responses into a single message, with a
configurable timeout and an explicit note that the component fails the
overall route if a configured minimum number of targets do not respond in
time (MuleSoft Documentation, "Scatter-Gather", verified at
https://docs.mulesoft.com/mule-runtime/latest/scatter-gather-concept on
2026-08-02, describing the same completion-strategy concern raised as a
design force in dimension 3 of this entry).

## 10. Consequences

The primary positive consequence is latency proportional to the slowest
required recipient rather than to the sum of all recipients, which is the
pattern's entire reason to exist and is stated as such by every primary
source cited in dimension 9. A second positive consequence is that each
recipient can be developed, deployed, scaled, and owned independently, since
the only contract a recipient must honor is accepting the scattered request
shape and echoing the correlation identifier in its response, which lowers
the coordination cost between teams that would otherwise need to agree on a
single sequential call order. A third positive consequence is graceful
degradation when the completion strategy is a partial-quorum strategy. the
system can produce a useful, if incomplete, answer even when one recipient
is down, rather than the whole request failing the way a sequential chain
typically would on its first unavailable dependency.

The primary negative consequence is that the pattern converts one point of
failure into a distributed set of partial-failure states that the
aggregation logic must explicitly enumerate and handle, and an aggregator
written to assume every recipient always answers will silently produce
wrong or incomplete aggregates the first time a recipient is slow. A second
negative consequence is that resource cost multiplies with the fan-out
width. every scattered request consumes the compute, network, and possibly
the metered cost of every recipient in the fan-out set, even the recipients
whose answer is discarded by the reduce step, so the pattern trades latency
for a larger resource bill. A third negative consequence is that debugging
becomes inherently distributed-systems debugging. a wrong aggregate result
requires tracing which recipients answered, in what order, with what
latency, and how the completion strategy resolved, which is strictly harder
to reason about than a stack trace from a single failed sequential call. A
fourth negative consequence, specific to the message-broker variant, is
that the Aggregator becomes a stateful component holding partially-collected
correlation groups in memory or storage until they complete or time out,
which introduces a memory-management and cleanup concern absent from the
stateless synchronous variant.

## 11. Failure modes and misuse

The most common failure mode is an unbounded or absent completion strategy.
Symptom. a request that should return in milliseconds occasionally hangs for
minutes or forever. Cause. the aggregator was written to wait for all N
recipients with no timeout, and one recipient becomes permanently
unreachable, so the aggregator waits on a response that will never arrive.
Fix. give the completion strategy an explicit deadline in addition to, or
instead of, a full-quorum condition, and define what the aggregator returns
when the deadline passes with recipients still outstanding.

A second common failure mode is correlation identifier collision or loss.
Symptom. an aggregated result silently contains a response that belongs to a
different, earlier or concurrent request, producing a wrong answer with no
error raised. Cause. the correlation identifier is generated with
insufficient entropy, is reused across retries without being regenerated, or
a recipient's response accidentally omits or corrupts the identifier on the
return path, for example by an intermediate proxy that strips a header
carrying it. Fix. generate a cryptographically strong or monotonically
unique identifier per scatter operation, and add a validation step in the
aggregator that rejects any response whose correlation identifier does not
match an in-flight request rather than silently accepting it.

A third failure mode is memory or state leak in the aggregator holding
partial groups. Symptom. aggregator memory usage grows steadily over the
service's uptime, eventually causing out-of-memory restarts. Cause. the
aggregator retains a data structure per in-flight correlation group and
never removes the group after the completion strategy fires, or never
removes a group that times out without ever completing. Fix. treat group
eviction as mandatory on both the success path and the timeout path, and
consider a bounded time-to-live store, such as a cache with expiration,
rather than an unbounded map keyed by correlation identifier.

A fourth failure mode is thundering-herd overload, which is really a
misuse rather than an intrinsic defect. using Scatter-Gather to broadcast a
request to a large, dynamically growing recipient set, such as every
microservice in a service mesh, treats the pattern as a general-purpose
broadcast mechanism rather than a bounded, small-fan-out query pattern.
Symptom. a single incoming request produces a spike of outbound calls
proportional to the size of the whole system rather than to the size of a
fixed, small recipient set, and the tail latency of the single slowest
recipient in that large set sets the pace for every request. Fix. bound the
recipient set explicitly and, if genuine broadcast to a large or unbounded
audience is required, reach for Publish-Subscribe Channel with independent,
non-blocking consumers instead, per the non-applicability list in dimension 4.

A fifth failure mode is silently discarding partial-failure information in
the reduce step. Symptom. callers of the aggregated result cannot tell
whether the returned value represents a complete answer from all recipients
or a partial answer from a subset, because the reduce function returns a
plain value with no metadata about which recipients contributed. Cause. the
aggregation logic was written to optimize for the happy path and the return
type was never extended to carry partial-success information. Fix. make the
aggregated reply carry, at minimum, the set of recipients whose response
contributed and the set that did not, so downstream consumers can make an
informed decision about how much to trust the result.

## 12. Trade-off matrix

| Force | Scatter-Gather | Recipient List (sequential) | Publish-Subscribe Channel | Saga (orchestrated) |
|---|---|---|---|---|
| Latency for N sources | Roughly max of N latencies plus aggregation overhead | Sum of N latencies | Not applicable, no synchronous reply expected | Sum of step latencies plus compensation overhead if triggered |
| Coupling to recipient count | Aggregator must know completion policy for the fixed set | Caller iterates the list directly, no separate aggregator | Publisher decoupled entirely from subscriber count | Orchestrator explicitly sequences and depends on each step |
| Consistency of result | Best-effort composite across independent, possibly skewed-in-time responses | Same skew risk but caller sees results one at a time as they arrive | No unified result at all, each subscriber acts independently | Strong ordering guarantee per step, weaker across the whole saga unless compensated |
| Failure handling | Partial-result tolerance via completion strategy, or full failure on missing mandatory recipient | First failing recipient can halt the sequence unless caller explicitly continues past it | A failing subscriber does not affect the publisher or other subscribers | Explicit compensating transactions undo prior successful steps on failure |
| Resource cost | Pays for every recipient in the fan-out even if discarded | Pays for recipients in order, can short-circuit and stop early once satisfied | Pays only for whichever subscribers are actually subscribed | Pays for each step executed plus each compensation if triggered |
| Best fit | Small, bounded set of independent sources queried in parallel for one converged answer | Small set where sequential is acceptable or where early-exit on first good answer is wanted | Large or unbounded audience with no expectation of a converged reply | Multi-step business transaction spanning services with side effects needing rollback |

## 13. Related and incompatible patterns

Recipient List (Hohpe and Woolf, EIP, chapter 8) is the direct structural
parent of the scatter half of this pattern. A Scatter-Gather's Distributor
is, in the majority of documented implementations including Apache Camel's,
literally built as a Recipient List whose recipients are invoked
concurrently rather than sequentially. Aggregator (Hohpe and Woolf, EIP,
chapter 10) is the direct structural parent of the gather half. everything
this entry says about completion strategies and correlation-based grouping
is inherited from the Aggregator pattern in full, and a reader implementing
the gather half should read the Aggregator entry for the deeper mechanics
of completion strategies, which Scatter-Gather only summarizes.

Correlation Identifier (Hohpe and Woolf, EIP, chapter 10) is a near-mandatory
companion, because without a way to tie a scattered response back to the
originating request and the sibling responses in its group, the aggregator
has no way to know which responses belong together, particularly under
concurrent load where multiple scatter operations are in flight at once.

Message Sequence (Hohpe and Woolf, EIP, chapter 10) composes with
Scatter-Gather when the recipient set size is known at scatter time. tagging
each scattered message with a sequence number and the total count lets the
aggregator's completion strategy detect that all expected responses were
received deterministically rather than relying purely on a timeout.

Dead Letter Channel (Hohpe and Woolf, EIP, chapter 4) composes with the
message-broker variant to capture responses that arrive after the
aggregator has already given up on their correlation group, which would
otherwise be silently dropped, turning a potential silent-loss failure mode
into an observable one.

Circuit Breaker, a resilience pattern used widely in production practice
though not part of the original 2003 EIP catalog, composes naturally with
individual recipients in the scatter set. wrapping each recipient call in
its own circuit breaker prevents one persistently failing recipient from
repeatedly consuming the aggregator's full timeout budget on every
subsequent request, converting a slow failure into a fast, known failure.

Publish-Subscribe Channel (Hohpe and Woolf, EIP, chapter 6) is related by
proximity but is not a composition partner in the usual sense. it is the
pattern to reach for instead of Scatter-Gather when the recipient set is
large, unbounded, or does not need to produce a converged synchronous reply,
as covered in dimension 4's non-applicability list.

Point-to-Point Channel (Hohpe and Woolf, EIP, chapter 6) is listed as
incompatible in the frontmatter in the specific sense that the scatter half
of this pattern requires a channel topology capable of delivering one
logical message to multiple independent recipients, which a strict
point-to-point channel, defined in the EIP catalog as guaranteeing exactly
one consumer receives any given message, structurally cannot provide without
being paired with a separate fan-out mechanism in front of it. Using a pure
point-to-point channel as the scatter mechanism means only one recipient
ever sees the message, which defeats the pattern entirely.

## 14. Refactoring path in and out

Introducing Scatter-Gather into code that currently calls N sources
sequentially begins by identifying that the sequential calls have no data
dependency on each other, which is a precondition, not a nice-to-have. If
call two reads a value produced by call one, the refactor is invalid until
that dependency is removed or restructured. Once independence is confirmed,
the first step is to convert the sequential calls into concurrent ones using
the language's native concurrency primitive, wrapping the sequential loop of
awaited calls into a fan-out of unawaited calls collected afterward, which
alone captures most of the latency benefit even before introducing an
explicit correlation identifier or a formal aggregator abstraction. The
second step is to add an explicit timeout to the join operation, because a
concurrent fan-out with no timeout has simply moved the risk of an
unbounded wait from N sequential points to one parallel point rather than
removing it. The third step is to make the completion strategy explicit as
a first-class piece of logic, separated from the individual recipient calls,
so that a future recipient can be added to the fan-out without every caller
of the aggregator needing to know about the change. The fourth step, needed
only once recipients are independently deployed services rather than
in-process calls, is to introduce a genuine correlation identifier carried
through the wire protocol, at which point the refactor has arrived at the
full message-broker variant described in dimension 8.

Removing Scatter-Gather when it stops earning its place typically happens
for one of two reasons. The first is that the recipient set has collapsed to
effectively one meaningful source, with the others having become vestigial
or redundant over the system's evolution, in which case the refactor is to
delete the distributor and aggregator entirely and call the remaining
recipient directly, which is a straightforward simplification once it is
noticed, though it is frequently not noticed because the scatter-gather
machinery keeps working correctly even when fanning out to a recipient set
of one. The second reason is that the aggregation logic has grown more
complex than the scattering it serves, often because business rules for
combining results accreted over time into something closer to a rules
engine than a simple reduce function, in which case the healthier refactor
is usually not to remove the pattern but to extract the aggregation logic
into its own explicitly named and independently tested component, keeping
the scatter-gather shape but making its most complex part legible on its
own terms.

## 15. Testing and verification

Testing Scatter-Gather requires testing three concerns separately, the
scatter mechanism, the individual recipient contracts, and the aggregation
logic, because conflating them into one end-to-end test makes failures hard
to localize and makes the test itself slow and flaky under real network
conditions. The scatter mechanism is tested by verifying that a request
produces exactly one outbound call per configured recipient, that each
outbound call carries the same correlation identifier, and that the
mechanism does not block on any individual recipient before dispatching to
the next, which is most directly verified with fake or mock recipients whose
response latency is injected as a test parameter.

The aggregation logic is the most valuable part of the system to test in
isolation, and it is also the easiest, because the reduce and completion-
strategy functions can and should be pure functions taking a list or stream
of responses and a deadline as input and returning an aggregated result as
output, with no dependency on real network calls at all. Test doubles for
this layer are simply hand-constructed response lists representing every
combination the completion strategy must handle. all recipients responding
in time, a subset responding in time with the rest missing, zero recipients
responding before the deadline, a duplicate response for the same
correlation identifier arriving twice, which should be idempotently ignored
or explicitly rejected rather than silently double-counted, and a response
carrying an unrecognized correlation identifier, which should be rejected
rather than accepted into an unrelated group.

Testing what is hardest about the pattern, namely the interaction between
real recipient latency variance and the completion strategy's deadline,
benefits from property-based or randomized latency injection. generate
recipient response times from a distribution with a long tail, run the
scatter-gather operation repeatedly, and assert the invariant that the
aggregator's total wall-clock time never exceeds the configured deadline by
more than the fixed dispatch and reduce overhead, which surfaces a
mis-implemented deadline before it reaches production. Integration tests
against real recipients, where feasible, should specifically include a
recipient deliberately configured to be slow or unreachable, because that
is the exact condition dimension 11's most common failure mode arises from,
and a test suite that only exercises the all-recipients-succeed path will
never catch it.

## 16. Observability signals

The single most valuable metric to emit is per-recipient response latency,
tagged by recipient identity, because the pattern's entire performance
characteristic depends on the slowest recipient in the set, and without
per-recipient breakdown an operator sees only an aggregate latency number
that cannot distinguish a persistently slow recipient A from an
occasionally timing out recipient B from a slow aggregation reduce function
itself. A closely related metric is per-recipient response rate, meaning the
fraction of scatter operations in which that recipient's response arrives
before the completion deadline, because a recipient whose response rate
degrades from ninety-nine percent to eighty percent is a leading indicator
of a problem worth paging on before it becomes a full outage.

The completion-strategy outcome should be logged or emitted as a metric on
every scatter-gather operation, distinguishing between a full-quorum
completion, a partial completion under a defined threshold, and a deadline
expiry with an unacceptable subset of responses, because these three
outcomes have materially different implications for the quality of the
result the requestor received, and treating them identically in monitoring
hides real degradation behind a metric that only measures whether the
operation eventually returned something.

Correlation identifiers should be included in every log line touching a
scattered request or its responses, at both the distributor and the
recipients and the aggregator, so that a single trace can be reconstructed
across every participant for any given operation. this is precisely what
makes distributed tracing systems, whose spans are correlated by trace
identifiers conceptually equivalent to the pattern's own correlation
identifier, a natural fit for instrumenting Scatter-Gather, and several of
the production systems cited in dimension 9, including Spring Integration's
messaging infrastructure, integrate with standard distributed tracing
propagation for exactly this reason. A healthy scatter-gather subsystem on
a dashboard shows tight, low-variance recipient latency distributions and a
completion-outcome metric dominated by full-quorum completions. a failing
one shows a widening latency distribution for one or more recipients, a
rising share of partial or deadline-expiry completions, and a growing count
of aggregator-side in-flight correlation groups if the message-broker
variant's state is also being monitored, which is itself the leading
indicator of the memory-leak failure mode described in dimension 11.

## 17. Security and privacy implications

Scattering a single request to multiple recipients multiplies the number of
systems that receive a copy of that request's data, which is a data-minimization
concern whenever the request carries personal or sensitive information. A
request containing a customer's full profile, scattered to five pricing
recipients each of which only needs a subset of that data to compute its
quote, has needlessly exposed the full profile to every recipient rather
than the minimum each one actually requires, and the correct mitigation is
to construct a recipient-specific projection of the request rather than
broadcasting the full original payload verbatim to every recipient.

The aggregator itself becomes a point where responses from multiple
sources are combined, and if those sources are not equally trusted, the
aggregator's reduce logic is a place where a malicious or compromised
recipient could attempt to influence the aggregated result, for example a
compromised pricing recipient in a best-price selection scatter-gather
returning an artificially low price to win selection and later fail to
honor it. Systems scattering to third-party or less-trusted recipients
should validate individual responses for plausibility before including
them in the reduce step rather than trusting every response that carries a
correctly matching correlation identifier.

The correlation identifier itself, while primarily a routing concern, can
become an information-leakage vector if it is constructed from or embeds
sensitive data, such as a customer identifier directly used as the
correlation identifier without any additional randomness, because that
identifier is then visible to every recipient and to any intermediary
observing the scattered traffic. A correlation identifier should be an
opaque, request-scoped token with no exploitable semantic content, generated
independently of any identifier that itself carries sensitive meaning.

Where recipients are external, third-party services, the fan-out widens
the blast radius of a credential or API-key compromise, because a scatter
operation typically holds a live credential for every recipient
simultaneously in the requesting process, and a memory-disclosure
vulnerability in the aggregator process would expose credentials for every
recipient at once rather than for a single downstream dependency, which is
a reason to prefer per-recipient scoped credentials with the narrowest
possible permission set over a single broad credential reused across the
whole recipient set.

## 18. References

Hohpe, Gregor, and Bobby Woolf. "Enterprise Integration Patterns. Designing,
Building, and Deploying Messaging Solutions." Addison-Wesley, 2003. Chapter
8, Recipient List. Chapter 9, Message Routing, Broadcast Aggregate /
Scatter-Gather section. Chapter 10, Aggregator and Correlation Identifier
and Message Sequence.

Hohpe, Gregor, and Bobby Woolf. "Broadcast-Aggregate." Enterprise
Integration Patterns companion site.
https://www.enterpriseintegrationpatterns.com/patterns/messaging/BroadcastAggregate.html
Verified 2026-08-02.

Apache Camel Documentation. "Scatter Gather EIP."
https://camel.apache.org/components/4.22.x/eips/scatter-gather.html
Verified 2026-08-13.

Spring Integration Reference Manual. "Scatter-Gather."
https://docs.spring.io/spring-integration/reference/scatter-gather.html
Verified 2026-08-02.

AWS Prescriptive Guidance. "Fan-out message processing using Amazon SQS and
AWS Lambda."
https://docs.aws.amazon.com/prescriptive-guidance/latest/patterns/fan-out-message-processing-using-amazon-sqs-and-aws-lambda.html
Verified 2026-08-02.

MuleSoft Documentation. "Scatter-Gather."
https://docs.mulesoft.com/mule-runtime/latest/scatter-gather-concept
Verified 2026-08-02.

## Code examples

### TypeScript

```typescript
type Recipient<T> = (requestId: string) => Promise<T>;

interface ScatterResult<T> {
  fulfilled: T[];
  missingRecipients: number;
}

async function scatterGather<T>(
  requestId: string,
  recipients: Recipient<T>[],
  deadlineMs: number
): Promise<ScatterResult<T>> {
  const settled = await Promise.race([
    Promise.allSettled(recipients.map((r) => r(requestId))),
    new Promise<PromiseSettledResult<T>[]>((resolve) =>
      setTimeout(
        () => resolve(recipients.map(() => ({ status: "rejected", reason: "deadline" } as PromiseSettledResult<T>))),
        deadlineMs
      )
    ),
  ]);

  const fulfilled: T[] = [];
  for (const outcome of settled) {
    if (outcome.status === "fulfilled") fulfilled.push(outcome.value);
  }
  return { fulfilled, missingRecipients: recipients.length - fulfilled.length };
}

async function main() {
  const priceQuote =
    (name: string, ms: number, price: number): Recipient<number> =>
    async () => {
      await new Promise((r) => setTimeout(r, ms));
      return price;
    };

  const recipients = [priceQuote("A", 20, 105), priceQuote("B", 40, 98), priceQuote("C", 500, 90)];
  const result = await scatterGather("req-1", recipients, 100);
  const best = Math.min(...result.fulfilled);
  console.log(`fulfilled=${result.fulfilled.length} missing=${result.missingRecipients} best=${best}`);
}

main();
```

### Python

```python
import asyncio
import time


async def scatter_gather(request_id: str, recipients, deadline: float):
    tasks = [asyncio.create_task(r(request_id)) for r in recipients]
    done, pending = await asyncio.wait(tasks, timeout=deadline)
    for task in pending:
        task.cancel()
    fulfilled = [t.result() for t in done if not t.cancelled() and t.exception() is None]
    return fulfilled, len(recipients) - len(fulfilled)


def price_quote(name: str, delay: float, price: float):
    async def call(request_id: str):
        await asyncio.sleep(delay)
        return price
    return call


async def main():
    recipients = [
        price_quote("A", 0.02, 105),
        price_quote("B", 0.04, 98),
        price_quote("C", 0.5, 90),
    ]
    start = time.monotonic()
    fulfilled, missing = await scatter_gather("req-1", recipients, deadline=0.1)
    elapsed = time.monotonic() - start
    best = min(fulfilled) if fulfilled else None
    print(f"fulfilled={len(fulfilled)} missing={missing} best={best} elapsed={elapsed:.3f}s")


asyncio.run(main())
```

### Go

```go
package main

import (
	"context"
	"fmt"
	"time"
)

type response struct {
	name  string
	price float64
	ok    bool
}

func recipient(name string, delay time.Duration, price float64) func(ctx context.Context, out chan<- response) {
	return func(ctx context.Context, out chan<- response) {
		select {
		case <-time.After(delay):
			out <- response{name: name, price: price, ok: true}
		case <-ctx.Done():
			out <- response{name: name, ok: false}
		}
	}
}

func scatterGather(requestID string, recipients []func(context.Context, chan<- response), deadline time.Duration) ([]response, int) {
	ctx, cancel := context.WithTimeout(context.Background(), deadline)
	defer cancel()

	out := make(chan response, len(recipients))
	for _, r := range recipients {
		go r(ctx, out)
	}

	var fulfilled []response
	for i := 0; i < len(recipients); i++ {
		resp := <-out
		if resp.ok {
			fulfilled = append(fulfilled, resp)
		}
	}
	return fulfilled, len(recipients) - len(fulfilled)
}

func main() {
	recipients := []func(context.Context, chan<- response){
		recipient("A", 20*time.Millisecond, 105),
		recipient("B", 40*time.Millisecond, 98),
		recipient("C", 500*time.Millisecond, 90),
	}
	fulfilled, missing := scatterGather("req-1", recipients, 100*time.Millisecond)

	best := 0.0
	for i, r := range fulfilled {
		if i == 0 || r.price < best {
			best = r.price
		}
	}
	fmt.Printf("fulfilled=%d missing=%d best=%.0f\n", len(fulfilled), missing, best)
}
```

## Language coverage note

TypeScript, Python, and Go each show the synchronous fan-out-with-a-deadline
variant from dimension 8, chosen because that is the variant where the
pattern's structure translates most directly into each language's native
concurrency primitives without requiring a messaging broker as scaffolding.
Java and Rust are omitted from the working examples in this entry not
because the pattern does not translate, since both languages have well
established concurrency primitives, `CompletableFuture` combined with
`orTimeout` in Java, and `tokio::select!` combined with `tokio::time::timeout`
in Rust, that express the same shape, but because three languages already
demonstrate the pattern's core mechanics across three materially different
concurrency models. JavaScript's single-threaded event loop with
`Promise.allSettled`, Python's cooperative `asyncio` event loop with
`asyncio.wait`, and Go's goroutine-and-channel model with a context
deadline, and a fourth or fifth language would repeat rather than add to
that coverage.
