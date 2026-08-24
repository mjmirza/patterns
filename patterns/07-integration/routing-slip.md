---
name: Routing Slip
slug: routing-slip
family: 07-integration
category: Integration
aliases: [Itinerary Pattern, Traveling Itinerary]
first_described: "Hohpe, Woolf 2003"
maturity: canonical
related: [pipes-and-filters, process-manager, saga, content-based-router, dynamic-router, message-router]
incompatible_with: []
verified: 2026-08-02
---

# Routing Slip

## 1. Name, aliases, and lineage

The canonical name is Routing Slip. It is catalogued in Gregor Hohpe and Bobby
Woolf, Enterprise Integration Patterns. Designing, Building, and Deploying
Messaging Solutions, Addison-Wesley, 2003, in the Message Routing chapter. The
pattern's own reference page states the problem as how to route a message
consecutively through a series of processing steps when the sequence of steps
is not known at design time and may vary for each message, and gives the
solution as attaching a routing slip to each message that lists the sequence
of steps, with a special router wrapping each processing component that reads
the slip and forwards the message to the next component named on it
([enterpriseintegrationpatterns.com, Routing Table page describing the
pattern](https://www.enterpriseintegrationpatterns.com/patterns/messaging/RoutingTable.html),
verified 2026-08-02).

The name comes directly from the paper artifact it mirrors. A physical routing
slip is a small form stapled to a document as it moves through an approval
chain in an office, each department signing off and forwarding it to the next
name on the list. The pattern borrows that image exactly. the slip is data
riding with the payload, not a separate control system that looks the payload
up.

Two aliases appear in practitioner writing rather than in the original
catalog. Itinerary Pattern is the term MassTransit's own documentation uses for
the ordered list of activities a routing slip carries, describing it as a
sequence of routing slip activities combined to form an itinerary
([masstransit.io, Routing Slip pattern
documentation](https://masstransit.io/documentation/patterns/routing-slip),
verified 2026-08-02, fetched via its current redirect target
masstransit.massient.com). Traveling Itinerary shows up informally in blog
writing about the same MassTransit feature and is not a name with independent
lineage, it restates the itinerary framing in different words.

The pattern is easy to conflate with two neighbors that solve a similar
problem differently, and naming the difference up front avoids the confusion
that dimension 4 returns to.

- **Routing Slip.** The path is computed once, attached to the message, and
  every hop reads the same static list.
- **Dynamic Router.** The path is recomputed at every hop from current
  conditions, and no list travels with the message. Camel's own documentation
  states this distinction plainly, that the Routing Slip computes the slip
  beforehand, it is only computed once, and on-the-fly recomputation at
  each step is the job of Dynamic Router instead ([camel.apache.org, Routing
  Slip EIP page](https://camel.apache.org/components/latest/eips/routingSlip-eip.html),
  verified 2026-08-02).
- **Process Manager / Saga.** A separate, out-of-band coordinator holds the
  state of a multi-step interaction and issues the next command, rather than
  the payload itself carrying the plan. See dimension 13 for how the two
  relate in practice, because the mature form of Routing Slip, the
  compensating transaction, is effectively a decentralized saga.

## 2. Problem and context

A message needs to pass through a chain of processing steps, and the exact
membership and order of that chain differs per message, per tenant, or per
business rule, rather than being fixed for the whole system.

The situation reads like this in an integration codebase. An order comes in
and, depending on its contents, must be validated, then perhaps enriched with
tax data for its jurisdiction, then reserved against inventory, then charged,
then shipped, and the exact sequence and the exact set of steps depends on the
order's country, its payment method, and whether it contains a
regulated item. A naive integration hardcodes this as a single long pipeline
with branches, or as a Content-Based Router with a growing pile of
if-then-else clauses at every junction. Both approaches put the decision logic
about the whole route inside every single processing component, and a new
variant of the route means touching every component that might sit on that
variant's path.

Routing Slip exists for exactly this situation. it moves the knowledge of the
whole route out of the individual processing steps and into a single
decision made once, near the start, and it moves that decision along with the
message rather than keeping it in a central table every step must consult.

The context that makes this the right pattern has three parts.

- The set and order of processing steps genuinely varies per message, not merely
  per deployment or per environment. If every message takes the same path, a
  Pipes and Filters chain is simpler and needs no slip at all.
- The processing steps are naturally separate, addressable components,
  services, actors, or activities, each of which can be invoked generically
  given only "here is the payload, here is what to do next," and the workflow
  is not that tightly coupled, where only a single monolithic function could ever
  express it.
- The itinerary can be computed once, cheaply, before the earliest hop, from
  information already available at that point. This is the assumption that
  breaks when routing decisions genuinely depend on the output of a step that
  has not run yet, at which point Dynamic Router is the honest tool.

Outside that context the pattern is unearned complexity, see dimension 4.

## 3. Forces

- **Coupling between steps.** Favoured. No processing step needs to know what
  came before it or what comes after, only how to do its own job and how to
  read and forward the slip. Adding a step means writing one component and
  inserting its name into the itineraries that need it, never editing an
  existing step.
- **Central routing table maintenance.** Favoured over Content-Based Router
  or a central orchestration table. There is no shared table every deployment
  must update in lockstep, because the routing decision is embedded per
  message at the moment it is made.
- **Message size and bandwidth.** Sacrificed. The itinerary, and in
  transactional variants the growing execution log and compensation data,
  travel with every hop of the payload. A long itinerary on a high-volume
  message stream is real bytes on the wire at every step, not once.
- **Consistency and atomicity across steps.** Genuinely hard, and the
  pattern in its basic form does nothing about it. The compensating variant
  described in dimension 8 exists specifically to buy this back at the cost
  of every step author writing an undo.
- **Operability and traceability.** Mixed. On one hand, the itinerary and the
  execution log sitting on the message are a complete, self-describing audit
  trail of exactly what happened to this one message, which is a genuine gain
  over a central router where the history has to be reconstructed from logs
  across many components. On the other hand, an operator who wants to know
  "what paths do messages currently take through this system" cannot read
  that off any single static artifact, because the answer is scattered across
  every itinerary ever computed.
- **Failure handling latency.** Sacrificed relative to a synchronous call
  chain. Detecting a failure at step four and unwinding steps one through
  three by sending compensating messages backward is slower and more
  complex than an in-process exception propagating up a call stack, but it
  works across process and network boundaries where a call stack cannot.
- **Team topology.** Favoured. The team that decides on an itinerary and the
  teams that own individual processing steps can work almost independently,
  as long as the message contract for "what a step receives and what it must
  return" is stable. This mirrors the coupling force above but is worth
  separating because it is a people cost, not only a code cost.

A pattern that paid nothing here would not be a pattern, it would be a free
lunch. The price is paid mainly in message weight and in the operational
difficulty of seeing the aggregate shape of traffic from any single place.

## 4. Applicability and non-applicability

Reach for Routing Slip when the following hold.

- The sequence of processing steps varies per message based on data already
  known at the point the message enters the system, and that variation is not
  merely a handful of fixed pipeline variants that could instead be modelled
  as separate static pipelines.
- The processing steps are naturally decoupled services, activities, or
  workers, invoked through a message channel or an RPC contract, rather than
  in-process function calls where a plain conditional would do the same job
  for free.
  It composes with Pipes and Filters, and MassTransit describes it as sitting
  above that foundation, an itinerary that a coordinator advances hop by hop
  ([masstransit.io, Routing Slip pattern
  documentation](https://masstransit.io/documentation/patterns/routing-slip),
  verified 2026-08-02).
- A multi-step business transaction spans several independently deployable
  services and must be undone in reverse order if a late step fails, and
  the system cannot rely on a two-phase commit or a distributed transaction
  coordinator across those services, which is the ordinary state of affairs
  once more than one datastore or vendor is involved.
- An audit trail of the exact steps a specific message took, in order, with
  timestamps, is a primary requirement rather than a nice-to-have derived
  from scattered logs.

Do NOT reach for Routing Slip in the following cases, and the reason is the
part worth internalising.

- **Every message takes the same fixed sequence of steps.** This is Pipes
  and Filters, plainly. A static pipeline configuration is simpler to read,
  simpler to test, and carries no per-message routing overhead. Adding a slip
  here is speculative generality dressed as flexibility nobody uses.
- **The next step must be decided from information only available after the
  previous step has already run.** A routing slip is computed once and is,
  by the Camel documentation's own framing, only computed once
  ([camel.apache.org, Routing Slip EIP
  page](https://camel.apache.org/components/latest/eips/routingSlip-eip.html),
  verified 2026-08-02). If the actual next hop depends on a value the
  previous step only produced, that is Dynamic Router's job, and forcing
  Routing Slip to do it means every step becomes a rewriting station that
  edits the remainder of the itinerary at runtime, which quietly turns the
  slip into an ad hoc dynamic router with none of that pattern's clarity.
- **All the steps run inside one process and one transaction boundary.** A
  routing slip solves a distributed, cross-process routing problem. Inside a
  single service with one database, a plain function calling other functions
  in sequence, wrapped in a normal local transaction, is simpler, faster, and
  gives real ACID guarantees a routing slip cannot.
- **The steps must run in parallel, not in sequence.** Routing Slip is a
  linear, one-hop-at-a-time pattern by design. Fan-out to several
  concurrent steps and fan back in is Scatter-Gather's job, and bolting a
  branching itinerary onto Routing Slip to fake parallelism produces a
  fragile, hand-rolled scheduler.
- **The number of steps and their order is small, fixed, and known at
  compile time, and the only variation is a boolean flag or two.** A short
  chain of conditionals inside one orchestrating function is more readable
  than externalising that decision into a data structure that has to be
  built, validated, and serialised.
- **Strong, synchronous consistency across the whole chain is a hard
  requirement and the participants share infrastructure that supports a real
  distributed transaction.** Where a proper two-phase commit is available and
  affordable, it gives stronger guarantees with less bespoke compensation
  code than a hand-rolled saga built on top of a routing slip.

## 5. Structure

Four participants, named by the role each plays in Hohpe and Woolf's own
vocabulary plus the roles that the transactional variant in dimension 8 adds.

- **Message.** The payload the business cares about, order data, a document,
  a job description. It is the thing being processed, and it is what the
  routing slip is attached to, not something the slip carries a copy of.
- **Routing Slip.** A list of processing step identifiers, in order, attached
  to the message as it travels. In its simplest form this is nothing more
  than an ordered list of addresses or endpoint names. In the transactional
  variant it also carries a growing log of which steps have completed, and
  any state variables the steps need to share.
- **Processing Step (Activity).** One unit of work. It reads the message and,
  where present, the itinerary's current variables, does its job, and hands
  the result onward. It does not know what step ran before it or what step
  runs after it by name, only that there is a next hop determined by
  whatever coordinates the slip.
- **Router (Itinerary Coordinator).** The infrastructure piece, sometimes a
  library, sometimes a lightweight service, that wraps each processing step,
  reads the current position on the slip, invokes the next step, and on
  return advances the position and forwards to the following step, or
  finalizes when the list is exhausted. In the transactional variant this
  coordinator is also the piece that, on a fault, walks the completed log
  backward and invokes the matching compensating action for each finished
  step ([masstransit.io, Routing Slip pattern
  documentation](https://masstransit.io/documentation/patterns/routing-slip),
  verified 2026-08-02).

Relationships. The Router depends on the Routing Slip's shape, never on any
particular Processing Step by name, that binding happens only through the
data the slip carries at runtime. Each Processing Step depends only on the
message contract it receives and returns, never on its neighbors. The
Routing Slip itself is pure data, it has no behaviour, which is what lets it
serialise cleanly onto a message bus.

## 6. ASCII structure diagram

```
+-----------------------------------------------------+
| Message                                             |
| payload: orderId, items, ...                        |
|                                                     |
| Routing Slip (attached)                             |
| itinerary: Validate, TaxCalc, Reserve, Charge, Ship |
| completed: []                                       |
| variables: {}                                       |
+-----------------------------------------------------+
           |
           v
+----------------------------------+
| Router / Coordinator             |
| reads itinerary, hop pointer = 0 |
+----------------------------------+
           v
+--------------------------------------+
| Processing Step: Validate (Activity) |
+--------------------------------------+
           | router advances slip, hop pointer = 1
           v
+--------------------------+
| Processing Step: TaxCalc |
+--------------------------+
           |
           | continues for Reserve, Charge, Ship
           v
+---------------------------+
| Finalize, itinerary empty |
+---------------------------+

Each box the message visits is generic. It knows only how
to read the slip's current hop and how to hand the
message to whatever the slip names as the next one. No
box hardcodes any other box's name.
```

## 7. Dynamics

The runtime flow has one property worth calling out before the diagram. the
itinerary is decided exactly once, near the start, and every subsequent hop
only reads and advances a position within that already-fixed list, it never
recomputes membership. This is what separates the flow from Dynamic Router,
where a fresh routing decision happens at every single hop.

```
Originator        Router/Coordinator      Step A (Validate)   Step B (Reserve)   Step C (Ship)
    |                     |                       |                   |                 |
    |-- build itinerary ->|                       |                   |                 |
    |   [A, B, C]          |                       |                   |                 |
    |                     |                       |                   |                 |
    |-- send(msg+slip) -->|                       |                   |                 |
    |                     |-- invoke(A, msg) ---->|                   |                 |
    |                     |                       |-- run Validate -->|                 |
    |                     |<-- result ------------|                   |                 |
    |                     |-- log A complete       |                   |                 |
    |                     |-- advance slip -> B    |                   |                 |
    |                     |-- invoke(B, msg) ------------------------>|                 |
    |                     |                       |                   |-- run Reserve ->|
    |                     |<-- result -------------------------------|                 |
    |                     |-- log B complete       |                   |                 |
    |                     |-- advance slip -> C    |                   |                 |
    |                     |-- invoke(C, msg) --------------------------------------------->|
    |                     |                       |                   |                 |-->
    |                     |<-- result --------------------------------------------------|
    |                     |-- log C complete       |                   |                 |
    |                     |-- itinerary empty       |                   |                 |
    |<-- finalize/notify -|                       |                   |                 |

  If Step B faults instead of completing, the coordinator walks the log
  backward and sends a compensate(A) message before finalising as failed.
```

Two timing notes. One, the router must persist, or at minimum durably queue,
the routing slip's current state between hops, because the whole point of the
pattern is that hops cross process and network boundaries where in-memory
state does not survive a crash. Second, when a step fails and compensation
runs, it runs in strict reverse order of completion, one at a time, which
means total unwind latency for a long itinerary can be significant, and that
latency needs to be visible in monitoring, see dimension 16.

## 8. Implementation variants

**Simple, non-transactional itinerary.** The slip is nothing more than an
ordered list of endpoint addresses. Each hop's router reads the list,
forwards to the head, and pops it. No compensation, no execution log. This is
the closest to the original 2003 catalog description and is the right choice
when the steps are idempotent, read-only, or individually recoverable by
other means, and a mid-chain failure only needs a retry of the whole message
rather than a coordinated undo.

**Compensating transaction variant.** The slip additionally carries a
compensation log, one entry per completed step, each entry naming the
compensating action for that step. On a fault, the coordinator invokes
compensations in reverse completion order. MassTransit's documentation
frames this directly as buying "the transactional guarantees previously only
available in ACID databases" across a distributed system that cannot use a
literal database transaction ([masstransit.io, Routing Slip pattern
documentation](https://masstransit.io/documentation/patterns/routing-slip),
verified 2026-08-02). This is the variant that most production frameworks
genuinely ship, because a routing slip with no failure story is rarely useful
past a demo.

**Header-encoded slip (message-bus native).** The itinerary lives in a
message header as a delimited string of endpoint URIs rather than in a
structured body field. Apache Camel implements exactly this shape, reading
the itinerary from a named header, splitting it on a configurable delimiter,
defaulting to a comma, and advancing an exchange property that tracks the
current endpoint as each hop completes ([camel.apache.org, Routing Slip EIP
page](https://camel.apache.org/components/latest/eips/routingSlip-eip.html),
verified 2026-08-02). This variant is cheap to bolt onto an existing
messaging fabric that already supports arbitrary headers, at the cost of a
less strongly typed itinerary than a dedicated body field gives.

**Fault-tolerant header variant with skip-on-invalid.** A refinement of the
header-encoded form where a malformed or unreachable endpoint on the list is
skipped and logged rather than aborting the whole chain. Camel exposes this
as the `ignoreInvalidEndpoints` option ([camel.apache.org, Routing Slip EIP
page](https://camel.apache.org/components/latest/eips/routingSlip-eip.html),
verified 2026-08-02). This is a pragmatic production concession, not part of
the original 2003 description, and it trades strict correctness for
resilience against a stale or partially wrong itinerary.

**Router-strategy variant.** Rather than a bare list, the slip references a
pluggable strategy object that the coordinator consults at each hop to decide
the exact next channel, which lets the itinerary carry a rule rather than a
literal address list while still being computed once, up front, from that
rule. Spring Integration documents Routing Slip alongside its other router
implementations in this shape ([docs.spring.io, Spring Integration reference,
Message Routing
chapter](https://docs.spring.io/spring-integration/reference/message-routing.html),
verified 2026-08-02). This variant sits closest to the boundary with Dynamic
Router, and the discipline that keeps it honestly a routing slip rather than
a disguised dynamic router is that the strategy's decision must depend only
on data already fixed when the slip was built, not on the live result of the
step that only ran.

**State-machine-backed itinerary.** The itinerary and its completion log are
persisted as rows in a durable state store, and the coordinator is a small
stateless worker that reads the current row, invokes the next step, and
writes the updated row, rather than holding position purely in message
transit. This variant is what most production Sagas genuinely look like once
Routing Slip is combined with a Process Manager for durability across
coordinator restarts, see dimension 13.

## 9. Known production uses

**MassTransit routing slip and itinerary.** MassTransit, a widely used .NET
message-based application framework, implements Routing Slip as a primary
feature. an ordered itinerary of activities, each supporting both an execute
step and a compensate step, coordinated through a routing slip message
contract that carries tracking identifiers, the itinerary, an execution log,
compensation data, and shared variables. Fault handling walks the completed
log backward invoking compensations. MassTransit documentation,
"Routing Slip", https://masstransit.io/documentation/patterns/routing-slip
verified 2026-08-02.

**Apache Camel Routing Slip EIP.** Apache Camel, a widely used open-source
integration framework, ships a native `routingSlip` DSL element implementing
the pattern directly against Hohpe and Woolf's catalog description, reading
the itinerary from a message header, splitting on a configurable delimiter,
and optionally skipping invalid endpoints. Apache Camel documentation,
"Routing Slip EIP",
https://camel.apache.org/components/latest/eips/routingSlip-eip.html
verified 2026-08-02.

**Spring Integration router family.** Spring Integration, the messaging
extension to the Spring Framework used broadly in Java enterprise
integration, documents Routing Slip as one of its router implementations
within its Message Routing chapter, alongside its other router types.
Spring Integration reference documentation, "Message Routing",
https://docs.spring.io/spring-integration/reference/message-routing.html
verified 2026-08-02, confirming the Routing Slip subsection is a published,
maintained part of the router family in the current reference (the deeper
subsection page returned a transient 404 on direct fetch during a live check,
therefore implementation-level detail beyond its listed presence in the router
family is not claimed here).

## 10. Consequences

Positive.

- New processing steps can be introduced, and new itineraries composed from
  existing steps, without editing any existing step's code, which is the
  Open Closed Principle applied to a distributed workflow.
- The full path a specific message took, in order, with timestamps, is
  reconstructible from the message itself rather than from correlating logs
  scattered across every service that might have touched it.
- Processing steps stay small, generic, and independently deployable, because
  none of them needs to know the shape of the whole workflow it participates
  in, only its own contract.
- Combined with a compensation log, the pattern gives a workable substitute
  for a distributed transaction across services and datastores that could
  never share a literal two-phase commit.
- The routing decision is made once, cheaply, near the entry point, rather
  than being recomputed and re-evaluated at every hop, which keeps individual
  steps fast and simple.

Negative.

- The itinerary, and in the transactional variant the growing execution and
  compensation log, add real bytes to every message on every hop, which
  matters at high volume or with a large step count.
- Compensation logic is extra code every step author must write and keep
  correct, and an untested or wrong compensating action is worse than none,
  because it can corrupt state that would otherwise have been left merely
  incomplete.
- The pattern gives no visibility, from any single static artifact, into the
  aggregate set of paths messages currently take through the system. that
  picture only exists as the union of every itinerary ever built, which
  makes system-wide impact analysis of a step change harder than it looks.
- A routing slip computed once cannot react to information a later step
  discovers, and a system that starts simple with Routing Slip and later
  needs genuinely dynamic, data-dependent routing either grows an
  uncomfortable rewriting hack or must migrate to Dynamic Router.
- Debugging a stuck or partially compensated itinerary in production requires
  reconstructing state from message history or a persisted log store, which
  is a genuinely harder debugging session than stepping through a local call
  stack.

## 11. Failure modes and misuse

**Silent partial completion.** Symptom. An order shows as reserved and
charged in one system's records but never shipped, and no error was ever
raised anywhere. Cause. A step consumed the message, updated its own state,
and then crashed or was redeployed before forwarding to the coordinator, and
nothing detected the missing forward hop. Fix. The coordinator must track
in-flight itineraries with a timeout and alert on a slip that has not
advanced within an expected window, never assume forward progress from
silence.

**Compensation that is not genuinely the inverse.** Symptom. After a
mid-chain fault, compensation runs without error, but a reconciliation report
weeks later shows inventory or ledger drift. Cause. The compensating action
for a step was written once, quickly, and never exercised against the same
edge cases as the forward action, most commonly a compensation that refunds a
flat amount rather than the amount genuinely charged, or that does not account
for a partial fulfillment. Fix. Every compensating action needs its own test
suite mirroring the forward action's, and a periodic reconciliation job that
does not trust the compensation log alone.

**Itinerary drift from stale computation.** Symptom. Messages built before a
deployment take a route through steps that have since been retired or
renamed, and fail at a hop nobody expects to still be reachable. Cause. The
itinerary was computed and attached at message creation time, and long-lived
messages, ones sitting in a retry queue or a dead-letter queue for hours or
days, carry a plan built against an older topology. Fix. Version the
itinerary format and the step address scheme, and give the coordinator a
translation table for retired step names, or refuse to resume a slip whose
itinerary version predates a breaking topology change, surfacing it for
manual review instead of silently misrouting it.

**Using Routing Slip where Dynamic Router was needed.** Symptom. Step
implementations start mutating the remaining itinerary in place, inserting
new hops based on their own output, and the "static" slip becomes an
undocumented, ad hoc rewriting protocol that only the current step authors
understand. Cause. A genuine need for data-dependent routing was bolted onto
a pattern designed around a fixed, pre-computed plan, because Routing Slip
was already in place and switching felt like a bigger change than it is.
Fix. Recognise the symptom early and migrate the affected hop to a Dynamic
Router decision, keeping the rest of the itinerary, which the Camel
documentation's own explicit distinction between the two patterns exists to
prevent in the earliest place ([camel.apache.org, Routing Slip EIP
page](https://camel.apache.org/components/latest/eips/routingSlip-eip.html),
verified 2026-08-02).

**Unbounded itinerary growth.** Symptom. Message size climbs steadily over a
system's lifetime, and old messages replayed from an archive are visibly
larger than recent ones for no business reason. Cause. Every new business
rule adds another optional step to every itinerary rather than composing
itineraries from a small set of named, versioned templates, and the average
itinerary length grows without bound as the business logic accretes. Fix.
Treat itinerary construction as its own piece of versioned, tested logic,
and periodically review whether steps that appear in nearly every itinerary
belong back in a fixed Pipes and Filters prefix instead.

**Duplicate execution on retry.** Symptom. A customer is charged twice for
one order after a transient network blip. Cause. The coordinator retried a
hop whose forward message had genuinely been delivered and processed, but
whose acknowledgment was lost, and the step being retried was not
idempotent. Fix. Every step invoked from a routing slip coordinator must be
idempotent with respect to the slip's tracking identifier, using that
identifier as a deduplication key, exactly as any at-least-once messaging
consumer must be.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Routing Slip | Dynamic Router | Content-Based Router | Process Manager / Saga (orchestrated) | Pipes and Filters (fixed pipeline) |
|---|---|---|---|---|---|
| Where the plan is decided | Once, up front, travels with the message | At every hop, freshly | Once per hop, from rules re-evaluated each time | Held centrally by a coordinator, not on the message | At design time, in configuration |
| Per-message flexibility | High, any itinerary a message needs | Highest, can react to live results | Medium, limited by the rule set at each hop | High, and can react to live results too | None, every message follows the same path |
| Coupling between steps | Very low | Very low | Low, but the router itself accumulates rules | Low between steps, but all steps couple to the coordinator's contract | Low, but the pipeline shape is shared config |
| Message payload weight | Grows with itinerary length and log | Small, no itinerary carried | Small | Small on the wire, state lives in the coordinator | Smallest, no routing metadata at all |
| Failure recovery story | Compensation log if the transactional variant is used, otherwise none built in | Not addressed by the pattern itself | Not addressed | Strong, the coordinator is the natural place to drive compensation | Not addressed |
| Central visibility of overall flow | Poor, scattered across itineraries | Poor, decided ad hoc every hop | Fair, rules live in one router | Good, the coordinator's state is the single source of truth | Best, the pipeline is one static artifact |
| Operational debugging | Good per-message, poor in aggregate | Hard, no artifact records the decision that was made | Fair | Good, coordinator state is queryable centrally | Best, behaviour is uniform across all messages |
| Cost to add a new step | Low, write the step, add it to relevant itineraries | Low, add a rule the router consults | Low, add a rule | Low, teach the coordinator a new transition | Medium, edit the shared pipeline config |

Reading of the table. Routing Slip wins when per-message variation is real but
knowable up front and the steps genuinely need to be decoupled across process
boundaries. Dynamic Router wins when the next hop depends on information the
system does not have until a prior step produces it. Process Manager wins
when a durable, centrally queryable, restartable coordinator matters more
than the self-describing convenience of state riding on the message.
Pipes and Filters wins whenever the honest answer is that every message
really does take the same path.

## 13. Related and incompatible patterns

- **Pipes and Filters.** The foundation Routing Slip is built on top of.
  MassTransit's own framing places the routing slip's activities as the
  filters and the coordinator as what threads a per-message pipe between
  them ([masstransit.io, Routing Slip pattern
  documentation](https://masstransit.io/documentation/patterns/routing-slip),
  verified 2026-08-02). Reach for plain Pipes and Filters at the outset, and only add
  a slip once the pipeline genuinely needs to vary per message.
- **Dynamic Router.** The sibling pattern for the case Routing Slip
  deliberately does not handle, routing decided fresh at every hop rather
  than once up front. The two are frequently confused, and Camel's
  documentation states the distinction as its own explicit note precisely
  because the confusion is common in practice ([camel.apache.org, Routing
  Slip EIP page](https://camel.apache.org/components/latest/eips/routingSlip-eip.html),
  verified 2026-08-02).
- **Process Manager and Saga.** The compensating-transaction variant of
  Routing Slip, described in dimension 8, is functionally a decentralized
  saga, the compensation plan travels with the message rather than being
  held by a separate coordinator process. A centrally-held Process Manager
  and a message-carried Routing Slip solve overlapping problems from
  opposite directions, and a system sometimes needs both, a Process Manager
  that decides which itinerary to build, handing off execution of that
  itinerary to a routing slip coordinator.
- **Content-Based Router.** A composable building block a routing slip's
  originator often uses to decide which itinerary to attach at the outset
  place, deciding a one-time branch at message creation rather than deciding
  routing at every subsequent hop.
- **Correlation Identifier.** Every routing slip needs one, a stable
  tracking identifier carried on the message, one the coordinator, logs, and
  any compensation logic can all agree which in-flight workflow instance a
  given hop belongs to.
- **Message Endpoint.** Each processing step named on the slip is, in
  Hohpe and Woolf's vocabulary, a message endpoint, the thing that connects
  an application to the messaging system, and the routing slip's list is
  simply a list of endpoints.
- **Two-Phase Commit / distributed transaction.** Conflicts in intent
  rather than in mechanism. Where a true distributed transaction coordinator
  is available and affordable across every participant, it gives stronger
  atomicity guarantees than a hand-written compensation log can, and reaching
  for Routing Slip's compensation variant when 2PC is genuinely on the table
  trades a stronger guarantee for a weaker, more code-heavy one for no gain.

## 14. Refactoring path in and out

Introducing the pattern into a system that currently hardcodes its workflow
as a chain of conditional calls.

1. Identify the orchestrating code, the function or service that currently
   decides, with if-else logic, which processing steps a given message must
   pass through and in what order.
2. Extract each branch's individual unit of work into its own named,
   independently invokable step, with a stable input and output contract,
   even before introducing any slip. Run the tests after each extraction.
3. Introduce the routing slip data structure, initially as nothing more than
   an ordered list of step identifiers, and have the orchestrating code build
   that list from the same conditional logic it already has, rather than
   inline-calling the steps.
4. Write the coordinator, the piece that reads the current position on the
   list, invokes the named step, and advances the position on return. Start
   this synchronously, in-process, to prove the mechanics before adding any
   network hop.
5. Move each step behind a real message channel or service boundary one at a
   time, verifying end-to-end behaviour after each move, and the system is
   never in a state where half the steps are local calls and half are remote
   with no clear seam.
6. Add the compensation log and per-step compensating actions only once a
   genuine cross-step failure has occurred, or is a known near-term risk,
   rather than speculatively writing undo logic for steps that may never
   need it, per the You Are Not Going To Need It discipline the refactoring
   family entries apply broadly.
7. Add the idempotency key and duplicate-detection discipline from dimension
   11 before the system carries production traffic, not after the earliest
   double-charge incident.

Removing the pattern when it stops earning its place. Signals that it should
go include an itinerary that has become identical across essentially every
message, or a system where every "variation" the slip once carried has since
collapsed to two or three well-known fixed shapes.

1. Enumerate the distinct itineraries genuinely observed in production over a
   representative window. If the count is small and stable, each distinct
   shape is a candidate for its own named, static pipeline.
2. Introduce a Content-Based Router at the entry point that picks one of
   those small number of named static pipelines, rather than building a
   fresh itinerary per message.
3. Migrate traffic to the new router incrementally, keeping the slip-based
   path live for any itinerary shape not yet covered by a static pipeline,
   which naturally shrinks over time as the enumerated shapes are ported.
4. Once every observed itinerary shape has a matching static pipeline, retire
   the coordinator and the slip data structure, and delete the per-message
   itinerary-construction logic, leaving each processing step in place since
   they remain useful as pipeline stages.

## 15. Testing and validation

Easier because of the pattern.

- Each processing step can be unit tested in complete isolation, given only
  its declared input contract, since it has no dependency on any other step
  or on the coordinator's internals.
- The coordinator itself can be tested against a small set of fake steps
  that record their invocation order, verifying the advance-on-success and
  compensate-on-fault logic without needing any real business step to exist.
- Because the itinerary is data, not code, a whole family of end-to-end test
  cases can be generated by constructing different itineraries over the same
  fixed set of test steps, rather than writing a new integration test per
  workflow variant.

Harder because of the pattern.

- End-to-end behaviour for a specific business scenario now depends on
  correctly reconstructing an entire itinerary as test fixture data, which
  is more setup than calling one orchestrating function directly.
- Compensation correctness genuinely requires forcing failures at every
  possible hop position and asserting the resulting state matches "as if the
  whole transaction never happened," which multiplies the number of failure
  scenarios that need explicit coverage by the itinerary length.
- Race conditions between a slow-to-acknowledge hop and a coordinator retry
  are difficult to reproduce deterministically in a unit test and usually
  need an integration test against the real messaging transport, or a
  fault-injection rig that can hold a hop open on demand.

Techniques that apply.

- **Fake step doubles that record invocation order and payload.** The
  primary technique for coordinator testing, a small in-memory step that
  appends its name to a shared list on invocation, letting a test assert the
  exact sequence the coordinator drove.
- **Forced-fault-at-each-position test matrix.** For the compensating
  variant, one test per possible failing step position, asserting that every
  step before the failure was compensated in strict reverse order and every
  step after it never ran.
- **Idempotency replay test.** Feed the coordinator the same hop-completion
  message twice and assert the downstream step observed exactly one
  business-level effect, directly testing the fix for the duplicate
  execution failure mode in dimension 11.
- **Itinerary schema and version compatibility test.** A test suite that
  builds an itinerary using an older recorded schema version and asserts the
  current coordinator either handles it correctly or rejects it explicitly,
  guarding against the itinerary drift failure mode in dimension 11.
- **Contract test per step.** Since steps are meant to be interchangeable
  components addressed generically by the coordinator, a shared contract
  test suite run against every concrete step implementation catches a step
  that silently violates the expected input or output shape.

## 16. Observability signals

The pattern's whole value proposition is a self-describing audit trail, and
observability is close to the point of the pattern rather than an
afterthought bolted on.

What to record.

- On every hop, a log line or trace span carrying the routing slip's
  tracking identifier, the current step name, the hop's outcome, and the
  elapsed time for that hop specifically.
- A counter of hops started and hops completed, labelled by step name, where a
  step that is silently swallowing messages without forwarding shows up as a
  started count that never matches its completed count.
- A histogram of end-to-end itinerary completion time, and separately a
  histogram of per-hop time, labelled by step name, where a single slow step
  buried inside a long itinerary is localisable without reading every
  service's own logs.
- For the compensating variant, a counter of compensations triggered,
  labelled by the step being compensated and by the reason the fault
  originated, and a separate counter of compensation failures, meaning a
  compensating action that itself threw.
- A gauge of in-flight itineraries currently sitting at each named step,
  which surfaces a stuck hop as an anomalous accumulation at one step rather
  than a generic backlog.

A healthy instance on a dashboard. Started and completed hop counts track
each other closely per step, with only the expected small in-flight
population between them. Per-hop latency is flat and consistent with each
step's own SLO. Compensation counters sit near zero, and when they do fire,
the compensation-failure counter stays at zero.

A failing instance. The in-flight gauge for one specific step climbs and
does not drain, which is the silent partial completion failure mode
localised precisely, that step is consuming messages and not forwarding
them. Or the compensation-triggered counter for a step spikes correlated
with a deployment, which points at a regression in that step's forward
logic. Or the compensation-failure counter goes above zero at all, which is
always an incident, an undo did not work and manual reconciliation is now
required. Or per-hop latency for one step develops a long tail while its
own service-level dashboards look normal, which usually means the queue or
transport between the coordinator and that step, not the step itself, is
the actual bottleneck.

## 17. Security and privacy implications

The pattern is not silent on security the way a purely structural pattern
can be, because the routing slip is data that travels across every service
boundary the itinerary touches, and that changes the threat model in three
concrete ways.

**Itinerary tampering.** Because the slip determines which service runs
next, a message whose slip can be modified in transit or by a compromised
intermediate step is a message an attacker can redirect through services it
was never meant to visit, potentially skipping a validation or
authorization step entirely by simply omitting it from a forged itinerary.
Where the transport does not already guarantee message integrity end to end,
the slip's itinerary and its tracking identifier should be signed or carried
inside a signed envelope, not trusted as plain, mutable data, and each step
should independently verify that a mandatory prior step, such as
authorization, genuinely appears completed in the execution log rather than
assuming order was respected.

**Sensitive data accumulation on the slip.** The transactional variant's
compensation data and shared variables are a natural place for developers to
stash whatever a later step or a later compensation might need, and that
convenience makes the slip a magnet for exactly the sensitive fields, a
customer's payment token, a full address, a government identifier, that
should have the narrowest possible blast radius. Every service the
itinerary touches, including ones that only forward the message without
using a given field, can now read that field, because it rides on the
message as a whole. Treat the slip's variable bag the same as any other
payload field for data classification purposes, minimise what it carries,
and prefer a reference or token the relevant step can dereference against
a properly access-controlled store over embedding the sensitive value
directly.

**Replay and denial of service through itinerary length.** An itinerary is,
in effect, a work order that an attacker who can construct or influence one
gets to write. An itinerary with steps that call the same expensive service
many times, or with an artificially long chain, is an amplification vector,
turning one inbound message into many multiples of downstream work. Bound
the maximum itinerary length the coordinator will accept, and reject a slip
whose step list contains repeated entries beyond a small, deliberately
allowed retry count, rather than trusting itinerary construction to always
be well-behaved, particularly wherever any part of the itinerary is built
from data an external caller influenced.

On broader privacy, the observability advice in dimension 16 recommends
logging the tracking identifier and step names on every hop. Where the
tracking identifier or a step name itself can be correlated back to a
specific customer, that logging stream inherits the same retention and
access-control obligations as any other system that stores customer
activity history.

## Code examples

Three languages chosen for how the pattern is genuinely built in each
technology stack. TypeScript shows a message-bus-flavoured coordinator with an
itinerary array and per-step handlers, the shape closest to how a Node
service bus library would expose it. Go shows the same coordination with
Go's idiomatic function-value steps and no inheritance hierarchy at all. Python
shows the compensating-transaction variant with an explicit undo stack,
closest to how a saga coordinator is commonly hand-rolled in Python
integration code. Java is omitted here because its idiomatic shape, an
interface `RoutingSlipActivity` with `execute` and `compensate` methods
implemented per step and invoked through a generic coordinator, is
identical in shape to the TypeScript example below with interfaces in
place of a discriminated function type, and repeating it would not show a
genuinely different idiom.

### TypeScript

```typescript
type StepResult = { data: Record<string, unknown> };
type Step = (data: Record<string, unknown>) => Promise<StepResult>;

interface RoutingSlip {
  trackingId: string;
  itinerary: string[];
  completed: string[];
}

class Coordinator {
  private steps = new Map<string, Step>();

  register(name: string, step: Step): void {
    this.steps.set(name, step);
  }

  async execute(slip: RoutingSlip, data: Record<string, unknown>): Promise<void> {
    while (slip.itinerary.length > 0) {
      const stepName = slip.itinerary[0];
      const step = this.steps.get(stepName);
      if (!step) {
        throw new Error(`unknown step: ${stepName}`);
      }
      const result = await step(data);
      data = result.data;
      slip.completed.push(stepName);
      slip.itinerary = slip.itinerary.slice(1);
    }
  }
}

const coordinator = new Coordinator();
coordinator.register("validate", async (d) => ({ data: { ...d, valid: true } }));
coordinator.register("reserve", async (d) => ({ data: { ...d, reserved: true } }));

const slip: RoutingSlip = {
  trackingId: "order-1001",
  itinerary: ["validate", "reserve"],
  completed: [],
};

coordinator.execute(slip, { orderId: "1001" }).then(() => {
  console.log(slip.completed);
});
```

### Go

```go
package main

import "fmt"

type StepFn func(data map[string]any) (map[string]any, error)

type RoutingSlip struct {
	TrackingID string
	Itinerary  []string
	Completed  []string
}

type Coordinator struct {
	steps map[string]StepFn
}

func NewCoordinator() *Coordinator {
	return &Coordinator{steps: make(map[string]StepFn)}
}

func (c *Coordinator) Register(name string, fn StepFn) {
	c.steps[name] = fn
}

func (c *Coordinator) Execute(slip *RoutingSlip, data map[string]any) (map[string]any, error) {
	for len(slip.Itinerary) > 0 {
		name := slip.Itinerary[0]
		step, ok := c.steps[name]
		if !ok {
			return nil, fmt.Errorf("unknown step: %s", name)
		}
		result, err := step(data)
		if err != nil {
			return nil, fmt.Errorf("step %s failed: %w", name, err)
		}
		data = result
		slip.Completed = append(slip.Completed, name)
		slip.Itinerary = slip.Itinerary[1:]
	}
	return data, nil
}

func main() {
	c := NewCoordinator()
	c.Register("validate", func(d map[string]any) (map[string]any, error) {
		d["valid"] = true
		return d, nil
	})
	c.Register("reserve", func(d map[string]any) (map[string]any, error) {
		d["reserved"] = true
		return d, nil
	})

	slip := &RoutingSlip{
		TrackingID: "order-1001",
		Itinerary:  []string{"validate", "reserve"},
	}
	out, err := c.Execute(slip, map[string]any{"orderId": "1001"})
	if err != nil {
		panic(err)
	}
	fmt.Println(slip.Completed, out)
}
```

### Python

The compensating-transaction variant, with an explicit undo stack executed
in reverse on fault, mirroring the shape described for MassTransit in
dimension 8.

```python
from dataclasses import dataclass, field


@dataclass
class Activity:
    name: str
    execute: callable
    compensate: callable


@dataclass
class RoutingSlip:
    tracking_id: str
    itinerary: list[Activity]
    completed: list[Activity] = field(default_factory=list)


class Coordinator:
    def run(self, slip: RoutingSlip, data: dict) -> dict:
        try:
            for activity in list(slip.itinerary):
                data = activity.execute(data)
                slip.completed.append(activity)
            return data
        except Exception:
            self._compensate(slip, data)
            raise

    def _compensate(self, slip: RoutingSlip, data: dict) -> None:
        for activity in reversed(slip.completed):
            activity.compensate(data)


def validate(data: dict) -> dict:
    data["valid"] = True
    return data


def undo_validate(data: dict) -> None:
    pass


def charge(data: dict) -> dict:
    if data.get("orderId") == "bad":
        raise RuntimeError("payment declined")
    data["charged"] = True
    return data


def undo_charge(data: dict) -> None:
    print(f"refunding order {data.get('orderId')}")


if __name__ == "__main__":
    coordinator = Coordinator()
    slip = RoutingSlip(
        tracking_id="order-1001",
        itinerary=[
            Activity("validate", validate, undo_validate),
            Activity("charge", charge, undo_charge),
        ],
    )
    result = coordinator.run(slip, {"orderId": "1001"})
    print(result)
```

## 18. References

1. Gregor Hohpe, Bobby Woolf. Enterprise Integration Patterns. Designing,
   Building, and Deploying Messaging Solutions. Addison-Wesley, 2003.
   ISBN 0-321-20068-3. Message Routing chapter, Routing Slip pattern. Source
   of the original name, the problem statement, and the router-plus-attached-
   list solution described in dimension 1 and dimension 2. Web summary
   consulted at https://www.enterpriseintegrationpatterns.com/patterns/messaging/RoutingTable.html
   verified 2026-08-02.
2. MassTransit documentation. "Routing Slip".
   https://masstransit.io/documentation/patterns/routing-slip
   verified 2026-08-02, fetched via current redirect target
   masstransit.massient.com. Source of the itinerary terminology, the
   execution and compensation log description in dimension 8, and the
   production use in dimension 9.
3. Apache Camel documentation. "Routing Slip EIP".
   https://camel.apache.org/components/latest/eips/routingSlip-eip.html
   verified 2026-08-02. Source of the header and delimiter mechanism, the
   ignoreInvalidEndpoints option, and the explicit distinction from Dynamic
   Router used across dimensions 1, 4, 8, 11, and 13.
4. Spring Integration reference documentation. "Message Routing".
   https://docs.spring.io/spring-integration/reference/message-routing.html
   verified 2026-08-02. Source confirming Routing Slip as a documented,
   maintained router implementation in Spring Integration, used in dimension
   9.
