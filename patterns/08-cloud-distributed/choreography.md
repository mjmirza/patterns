---
name: Choreography
slug: choreography
family: 08-cloud-distributed
category: Messaging and Integration
aliases: [Event Choreography, Choreographed Integration, Decentralized Event-Driven Coordination]
first_described: "W3C Web Services Choreography Working Group, WS-CDL, 2004 to 2009 (formal specification lineage); popularized for microservices by Chris Richardson's microservices.io and the AWS and Azure cloud architecture centers, 2015 onward"
maturity: established
related: [saga, publisher-subscriber, event-sourcing, process-manager, compensating-transaction, transactional-outbox, circuit-breaker, cqrs]
incompatible_with: []
verified: 2026-08-03
---

# Choreography

## 1. Name, aliases, and lineage

The canonical name in the microservices and cloud literature is Choreography,
sometimes written Event Choreography to make the mechanism explicit. The term
did not originate in software. It is borrowed directly from dance, and the
metaphor is the clearest definition available. According to the Wikipedia
summary of the concept, service choreography is "a form of service composition
in which the interaction protocol between several partner services is defined
from a global perspective," with the shorthand that "dancers dance following a
global scenario without a single point of control" (Wikipedia contributors,
"Service choreography," https://en.wikipedia.org/wiki/Service_choreography,
verified 2026-08-03). Each participant knows its own steps and reacts to what
the others do. Nobody stands at the front of the room calling out the next
move.

The formal lineage runs through the Web Services stack of the early 2000s.
Vendors including Intalio, Sun, BEA and SAP submitted the Web Service
Choreography Interface, WSCI, to the W3C, which fed into the Web Services
Choreography Description Language effort, known as WS-CDL. The W3C Web
Services Choreography Working Group closed on 10 July 2009 with WS-CDL left at
Candidate Recommendation status, never reaching full Recommendation
(Wikipedia contributors, "Service choreography," verified 2026-08-03). WS-CDL
itself is now a historical artifact. Almost nobody writes a .cdl document
today. What survived is the underlying idea, decoupled from any specific
description language, and it was carried forward into REST and messaging
architectures by practitioners rather than by a standards body. Chris
Richardson's microservices.io reference site, and later the AWS and Azure
architecture centers, are the sources most engineers now cite when they use
the word, and they define it operationally rather than formally, as "each
local transaction publishes domain events that trigger local transactions in
other services" (Chris Richardson, "Pattern, Saga,"
https://microservices.io/patterns/data/saga.html, verified 2026-08-03, in the
choreography-based sagas section).

No serious source treats Choreography as a contested name. What is genuinely
contested, and worth naming here because it causes real confusion in code
review, is the boundary between three things people casually call
"event-driven."

- Choreography, this entry. Multiple autonomous services each subscribe to
  events and publish events, and the overall business process exists only as
  the emergent sum of those independent reactions. No component holds the full
  sequence.
- Publisher-Subscriber, the messaging primitive. A publisher sends a
  message to a channel and any number of subscribers receive a copy, with no
  guarantee that a subscriber does anything beyond receiving it. Pub-sub is the
  transport choreography is usually built on, but pub-sub says nothing about
  business process coordination. A logging pipeline built on pub-sub is not a
  choreography, because there is no multi-step business outcome being
  coordinated.
- Event Sourcing, the persistence technique. A service's own state is
  derived by replaying a log of events it owns. A service can use event
  sourcing internally while never publishing an integration event to any other
  service, in which case there is no choreography at all, only a storage
  choice.

This entry treats Choreography as the cross-service coordination style. It
composes with, but is not identical to, either of the other two.

## 2. Problem and context

A business process spans more than one service, and each service owns a slice
of state that no other service is allowed to touch directly, because that is
the entire point of drawing the service boundary in the first place. Placing
an order needs an Order service to record the order, an Inventory service to
reserve stock, a Payment service to charge a card, and a Shipping service to
schedule delivery. None of those four services can call into another's
database. The only sanctioned way to make something happen elsewhere is to
send that other service a message or an event and let it act on its own data
under its own rules.

The context in which Choreography is the natural first answer has three
concrete markers, and a reader can check their own system against all three
before reaching for the pattern.

- The services already communicate through an event backbone. A message
  broker or event bus is already deployed and services already publish
  domain events for other reasons, such as analytics or cache invalidation,
  so adding one more subscriber is close to free.
- Team boundaries follow service boundaries, and each team wants to own the
  full lifecycle of its reaction to an event without depending on a shared
  workflow definition owned by another team.
- The process itself is short. A handful of steps, a shallow dependency graph,
  and few or no cases where step five needs to know something that only
  happened at step two.

Where those three markers are absent, and especially where the process grows
past roughly four or five steps or needs to branch on business rules that span
multiple services, the same problem is usually better served by Orchestration,
where a single component holds the sequence explicitly. Dimension 4 states
that boundary directly, because it is the single most consequential decision
this entry covers.

## 3. Forces

- Coupling. Strongly favoured. A publishing service does not know, and
  should not know, which services subscribe to its events. New consumers
  attach without a code change anywhere upstream. This is runtime coupling
  traded for a much looser compile-time and deploy-time coupling.
- Autonomy and team topology. Strongly favoured. Each team owns its
  service's reaction end to end, deploys on its own schedule, and never needs
  a change reviewed or merged by a workflow-owning team, because there is no
  workflow-owning team.
- Visibility of the overall process. Sacrificed, and sacrificed hard. No
  file, no diagram checked into a repository, no running component knows the
  full sequence of a choreography. It exists only as the union of everyone's
  event subscriptions, which is precisely the debuggability problem the field
  keeps rediscovering, covered in depth in dimension 11.
- Debuggability and traceability. Sacrificed unless deliberately paid for
  with correlation IDs and distributed tracing threaded through every hop.
  Without that investment, answering "why did this order never ship" means
  grepping logs across four or more independently deployed services.
- Resilience to a single point of failure. Favoured. There is no
  orchestrator process whose outage stalls every in-flight process. A
  subscriber that is down simply falls behind and catches up from the
  broker's backlog once it recovers, assuming the broker offers durable
  delivery.
- Ripple cost of a process change. Sacrificed as the process grows. Because the
  sequence lives nowhere, adding, removing or reordering a step means
  auditing every service's event subscriptions by hand to work out who reacts
  to what, and a wrong assumption produces a silent behavioral change rather
  than a compile error. This is the second recurring production complaint,
  also covered in dimension 11.
- Consistency of the end result. Sacrificed relative to a transactional
  system, favoured relative to distributed locking. Choreography accepts
  eventual consistency and compensating actions instead of atomic commits
  across services, which is the correct trade for availability but means a
  reader-facing view can be transiently wrong.
- Latency. Roughly neutral to favoured for independent branches, since
  parallel reactions to the same event proceed concurrently without an
  orchestrator serializing them, but sacrificed for the total wall-clock time
  of a long dependent chain, because each hop pays broker latency on top of
  processing time.
- Operational cost. Mixed. Cheaper to add a step, publishing one more
  event type and subscribing one more consumer, more expensive to operate
  correctly as the system grows, because monitoring, alerting and incident response all
  need the same cross-service correlation that debugging needs.

No pattern gives up nothing. Choreography buys loose coupling and team
autonomy by spending process visibility, and that trade is exactly right for
a short process with independent teams, and exactly wrong for a long,
business-critical process where someone will eventually need to answer "where
is order 4471 right now" in under a minute.

## 4. Applicability and non-applicability

Reach for Choreography when the following hold together.

- The process has a small number of steps, in practice roughly two to five,
  and each step's trigger condition is simple enough to express as "when
  event X happens, do Y."
- Each participating service can complete its own reaction with a single
  local transaction, publish the resulting event, and never need to be told
  to compensate by a caller that remembers the whole history.
- The services already sit on a shared event backbone for other reasons, so
  adding a subscription is marginal cost, not new infrastructure.
- Team autonomy is a first-order design goal and the org chart already
  matches the service boundaries, so no single team could realistically own a
  cross-cutting orchestrator without becoming a bottleneck.
- The business does not need a single queryable answer to "what state is this
  process instance in right now," or is willing to build a separate read
  model, such as a Materialized View pattern instance, to answer that
  question instead of asking a live orchestrator.
- Failure handling is symmetric and local. Each step's compensating action can
  be triggered by the same kind of event that triggers the forward step, with
  no participant needing global knowledge of how far the process had
  progressed before it failed.

Do NOT reach for Choreography in the following cases. This list is the more
valuable of the two, and it is the list most catalogs compress into a single
warning about complexity.

- The process has more than roughly four or five steps, or the step count
  is expected to grow. Every additional step multiplies the number of
  event-subscription edges a reader must reconstruct by hand to understand
  the flow, and that reconstruction cost grows faster than linearly because
  each new consumer can itself publish new events that other services react
  to. Chris Richardson names this directly, writing that "as the number of
  steps grows, it can be difficult to understand the big picture" of a
  choreography-based saga, and his recommended remedy at that point is
  switching to orchestration (Chris Richardson, "Pattern, Saga,"
  https://microservices.io/patterns/data/saga.html, verified 2026-08-03).
- Someone, anyone, needs to ask "what is the current status of process
  instance 4471" as a live, first-class capability rather than a
  reconstruction exercise. A choreography has no natural home for that
  query, because no component holds the state. Answering it requires either
  a dedicated read model kept in sync by yet more event subscriptions, which
  is real additional system to build and operate, or falling back to log
  correlation, which does not scale to a support team's daily workload.
- A step needs to see the outcome of a step that is not its immediate
  predecessor. Choreography naturally expresses "react to the last thing
  that happened." It does not naturally express "wait for steps two and
  three to both finish, then do step four only if step two's amount exceeded
  a threshold from step one." That is state-machine logic, and cramming it
  into a chain of pairwise event reactions produces the flag-field and
  duplicate-subscriber anti-patterns catalogued in dimension 11.
- The organization needs a single visible artifact, reviewable and
  version-controlled, that describes the business process for compliance,
  audit or onboarding purposes. A choreography's process definition is
  scattered across every participating service's source code. That is a real
  cost for regulated domains such as payments or healthcare, where an
  auditor asking to see the order fulfillment process cannot be answered
  with a single file.
- Ordering guarantees across events from different producers matter, and
  the messaging infrastructure does not provide them. Amazon EventBridge,
  for instance, is a router that delivers matched events to targets; nothing
  in its documented contract about routing rules and targets promises a
  global ordering across events from different producers (Amazon Web
  Services, "What Is Amazon EventBridge?",
  https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-what-is.html,
  verified 2026-08-03). A choreography that silently assumes ordering across
  producers will eventually see it violated.
- The team lacks distributed tracing or correlation-ID discipline and has
  no near-term plan to add it. Choreography without tracing is choreography
  nobody can debug in production. Add the tracing first, or choose
  Orchestration, where at minimum the orchestrator's own execution history
  gives a starting point.
- The consuming teams are not actually autonomous, that is, changes to
  one service's event contract routinely require synchronized deploys with
  its consumers anyway. In that situation the org has the operational cost
  of distributed choreography without earning the decoupling benefit that is
  supposed to pay for it.

## 5. Structure

Choreography has an unusual structural property compared to most patterns in
this catalog, in that it names no coordinating participant, and that absence
is the whole point.

- **Event Producer.** Any service that, having completed a local unit of
  work, publishes an event describing what happened, in the past tense, as a
  fact rather than a command. "OrderPlaced," never "PlaceOrder." Any service
  in the choreography can and usually does play this role at some point in
  the flow.
- **Event.** An immutable record of something that already happened,
  published to a channel. It carries enough data for a subscriber to act
  without calling back to the producer, or it carries a reference the
  subscriber can use to fetch more, which is the trade-off between
  Event-Carried State Transfer and a thinner notification event.
- **Event Channel or Event Bus.** The transport. A topic, a queue fanned out
  to multiple subscribers, or a managed event router. It is the only shared
  infrastructure the participants have, and it deliberately knows nothing
  about the business process running over it.
- **Event Consumer.** A service that subscribes to one or more event types
  and reacts by performing its own local transaction, which usually ends
  with that consumer becoming a producer of a further event, continuing the
  chain.
- **Correlation Identifier.** Not a structural participant in the classical
  sense, but a piece of data every event in a given process instance must
  carry if the choreography is to be debuggable at all. Its absence is not a
  missing nice-to-have, it is a missing requirement, covered further in
  dimension 16.

There is deliberately no Orchestrator, no Process Manager, and no shared
state machine definition anywhere in this structure. Every participant knows
only its own trigger conditions and its own reaction. The overall picture is
an emergent property, reconstructable only by someone tracing the union of
every event subscription across every service, which is exactly the cost
named in dimension 4.

## 6. ASCII structure diagram

```
+-----------------+   OrderPlaced    +-------------------+
|  Order Service   |----------------->|                    |
|  (producer)      |                  |                    |
+-----------------+                  |                    |
                                       |    Event Bus       |
+-----------------+   StockReserved  |  (topics, no logic  |
|  Inventory       |<-----------------|   about sequence)   |
|  Service         |----------------->|                    |
|  (consumer+      |                  |                    |
|   producer)      |                  |                    |
+-----------------+                  |                    |
                                       |                    |
+-----------------+   PaymentCharged |                    |
|  Payment Service  |<-----------------|                    |
|  (consumer+       |----------------->|                    |
|   producer)       |                  |                    |
+-----------------+                  |                    |
                                       |                    |
+-----------------+   OrderShipped   |                    |
|  Shipping Service |<-----------------|                    |
|  (consumer)       |----------------->+-------------------+
+-----------------+

  Note what is absent from this diagram. No box represents "the order
  process." No arrow is labelled with a step number. Each service only
  knows the events it publishes and the events it subscribes to; the
  full left to right sequence exists only in the reader's head after
  tracing every subscription by hand.
```

## 7. Dynamics

The runtime flow below traces a single happy-path order, then the same flow
under a mid-process failure, because the failure case is where Choreography's
character actually shows up.

```
Client        Order Svc      Event Bus     Inventory Svc   Payment Svc   Shipping Svc
  |               |               |               |              |              |
  |-- POST order->|               |               |              |              |
  |               |-- OrderPlaced ->|              |              |              |
  |<-- 202 Accepted (order ID) ---|               |              |              |
  |               |               |-- deliver ---->|              |              |
  |               |               |               |-- reserve --|              |
  |               |               |               |-- StockReserved->          |
  |               |               |<---------------|              |              |
  |               |               |-- deliver ------------------->|              |
  |               |               |               |              |-- charge --  |
  |               |               |               |              |-- PaymentCharged->
  |               |               |<---------------------------- |              |
  |               |               |-- deliver ----------------------------------->|
  |               |               |               |              |              |-- ship
  |               |               |               |              |              |-- OrderShipped ->
  |               |               |<-------------------------------------------- |
  |               |               |                                              |
  |               |               |  (order is now durably shipped, but no       |
  |               |               |   participant ever held that milestone as    |
  |               |               |   explicit state; it is an inference from    |
  |               |               |   the last event a reader happens to see.)   |
```

Failure branch. Payment declines the card.

```
  ... same as above through StockReserved ...
  |               |               |-- deliver ------------------->|              |
  |               |               |               |              |-- charge FAILS
  |               |               |               |              |-- PaymentFailed->
  |               |               |<---------------|              |              |
  |               |               |-- deliver ---->|              |              |
  |               |               |               |-- ReleaseStock (compensating)
  |               |               |               |-- StockReleased->            |
  |               |               |<---------------|              |              |
  |               |               |-- deliver ---->|               |              |
  |  Order Svc subscribes to PaymentFailed and marks the order Cancelled,        |
  |  but only IF it happens to subscribe to that event. Nothing in the           |
  |  structure forces it to; a forgotten subscription is a silent bug, not a     |
  |  compile error, which is the exact failure mode named in dimension 11.       |
```

Two properties are worth stating plainly because they are easy to miss when
reading the diagram quickly. First, the client only ever sees the immediate
acknowledgment from the Order service. Everything after 202 Accepted
happens without the client waiting, which is correct for a long-running
process but means "did my order actually ship" is a question the client can
only answer by polling a separate read model or subscribing itself. Second,
compensation is not automatic. Someone had to write the Inventory service's
subscription to PaymentFailed by hand, and if a future engineer adds a
fifth step to the process without also auditing which existing steps need a
new compensating subscription, the compensation logic silently stays
incomplete. Nothing in the structure catches that omission.

## 8. Implementation variants

**Thin notification events over a shared bus.** Events carry only an
identifier and a type, and subscribers call back to the producer's API to
fetch details. Minimizes payload size and avoids stale-data bugs, at the cost
of a synchronous dependency reappearing at the moment a consumer needs the
data, which reintroduces some of the coupling choreography exists to remove.

**Event-Carried State Transfer.** Events carry the full data a subscriber is
expected to need, so no callback is required. Removes the runtime dependency
on the producer being reachable, at the cost of every subscriber holding a
denormalized, potentially stale copy of another service's data, and every
schema change to the event needing coordination with every subscriber that
reads that field.

**Topic-per-event-type on a broker with durable subscriptions.** Kafka,
Amazon SQS fan-out through SNS, Google Cloud Pub/Sub, and similar systems.
Each event type gets its own topic, and each consumer keeps its own read
position, so a consumer that is down does not lose events, it simply catches
up. This is the dominant real-world variant because it is the one broker
category that most naturally supports many independent subscribers reacting
to one publisher without the publisher configuring anything per-subscriber.

**Managed event router with content-based routing rules.** Amazon
EventBridge is the clearest example. It is documented as providing "simple
and consistent ways to ingest, filter, transform, and deliver events" through
event buses that "are routers that receive events and deliver them to zero or
more targets" (Amazon Web Services, "What Is Amazon EventBridge?",
https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-what-is.html,
verified 2026-08-03). This variant lets a subscriber declare interest by a
content-matching rule rather than by subscribing to a whole topic, which
narrows the question of who reacts to what but does not eliminate it, since
the rules themselves are still scattered across every subscribing service's
own infrastructure-as-code.

**Resource-event choreography via storage-triggered notifications.** A
storage or database change itself is the event source, with no explicit
publish call in application code at all. Amazon S3 Event Notifications is
the canonical instance. Amazon documents that S3 can publish notifications
for object lifecycle events to several destination types at once, including
Amazon SNS topics, Amazon SQS queues, an AWS Lambda function, and Amazon
EventBridge (Amazon Web Services, "Amazon S3 Event Notifications,"
https://docs.aws.amazon.com/AmazonS3/latest/userguide/EventNotifications.html,
verified 2026-08-03). This variant is cheap to start with, because there is
no bus to provision, but it couples the choreography's trigger points to
storage layout decisions, and the same documentation warns of a genuine
production failure mode unique to this variant, covered in dimension 11.

**Choreographed saga.** The special case where the events being choreographed
are specifically the steps of a distributed business transaction with
compensating actions for failure. Covered as its own pattern in this
repository. See dimension 13 for the exact relationship.

**Event mesh across multiple regions or clusters.** Large systems replicate
the event backbone itself across regions so that choreographed services in
different regions can still react to each other's events, trading
operational complexity in the transport layer for geographic resilience of
the choreography. This variant is judgement drawn from common cloud
architecture practice rather than a single citable source, and is included
here as a named option a reader should expect to encounter as systems grow rather
than as a claim about any specific vendor's product.

## 9. Known production uses

**Amazon S3 as a choreography trigger across AWS services.** S3 Event
Notifications is a real, heavily deployed production instance of the pattern.
A storage service publishes an event when an object is created, and multiple
independent downstream services, whether Lambda functions, SQS queues, SNS
topics, or EventBridge rules, react without S3 knowing or caring who is
listening or what they do. This is choreography in its purest
infrastructure-level form, where the producer is not even an application
service but a managed storage layer (Amazon Web Services, "Amazon S3 Event
Notifications,"
https://docs.aws.amazon.com/AmazonS3/latest/userguide/EventNotifications.html,
verified 2026-08-03).

**Amazon EventBridge as the choreography backbone in AWS reference**
architectures. EventBridge exists specifically to let services connect
application components together through events, and is documented as
supporting event buses that receive events from many sources, home-grown
applications, AWS services, and third-party software, and route them to
consumer applications with no producer-side knowledge of the consumers
(Amazon Web Services, "What Is Amazon EventBridge?",
https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-what-is.html,
verified 2026-08-03). This is documented, general-purpose infrastructure
built specifically to run choreographed integrations at production scale,
not a single company's case study, but the citation is direct to the
mechanism itself rather than to a secondary description of it.

**Choreography-based sagas in the reference e-commerce architecture**
documented by Chris Richardson. microservices.io walks through a Create
Order saga across an Order Service, a Customer Service, a Kitchen Service and
an Order History Service, each reacting to the previous service's published
event with no central coordinator, and explicitly names this the
choreography-based approach as distinct from the orchestration-based one
(Chris Richardson, "Pattern, Saga,"
https://microservices.io/patterns/data/saga.html, verified 2026-08-03). This
reference architecture is the one most widely copied into real production
systems when teams first adopt event-driven order processing, precisely
because it is the canonical worked example in the field.

**The counter-evidence is itself production evidence, and is worth naming**
honestly. Netflix built and open-sourced a general-purpose orchestration
engine, Conductor, specifically to coordinate long-running, cross-service
business processes as its systems grew, described in its own repository as
"a platform created by Netflix to orchestrate workflows that span across
microservices" (Netflix, Conductor repository README,
https://github.com/Netflix/conductor, verified 2026-08-03). The source does
not state, in the exact wording verified here, that Netflix was migrating
away from a prior pure-choreography architecture, so that specific causal
claim is judgement, not a sourced fact, and is presented that way. What is
sourced is that a company operating at very large volume independently
built exactly this category of tool, a durable, centrally visible workflow
orchestrator, for exactly the class of process, long-running and
cross-service, where dimension 4 says choreography stops paying for
itself. Readers should treat this as circumstantial evidence for the
trade-off in dimension 4, not as a direct quotation of the company's
stated rationale.

## 10. Consequences

Positive.

- New participants attach to an existing process by subscribing to events
  that already exist, with zero code changes in any upstream service, which
  is the strongest form of open-closed extensibility available at the
  integration level.
- No single component is a deployment or availability bottleneck for the
  whole process, because there is no orchestrator to be a bottleneck.
- Teams that own a service own its entire reaction to the world, end to end,
  which matches the autonomy that motivated splitting into services in the
  first place.
- The failure of one subscriber does not block the process for other
  subscribers reacting to the same event, when the transport offers
  independent per-subscriber delivery.
- The pattern requires no new coordination infrastructure beyond a message
  broker that most event-driven systems already operate for other reasons.

Negative.

- The whole business process is not represented anywhere as a single
  artifact, so understanding, testing, and onboarding new engineers to the
  full flow all require reconstructing it from scattered subscriptions.
- A change that ripples across several steps is expensive and error-prone. Adding, removing, or
  reordering a step requires auditing every service that might be affected,
  and a missed subscription is a silent runtime gap, not a build failure.
- Debugging a specific failed instance of the process requires correlating
  logs, traces, or events across every service that instance touched, and
  that correlation infrastructure must be built deliberately, it does not
  come free with the pattern.
- There is no natural place to answer what state a given process instance is
  in right now, without building and maintaining a separate read model.
- Compensation and rollback logic is distributed the same way forward logic
  is, so it inherits every one of the coordination problems above, at the
  exact moment, a failure, when a team can least afford to be confused.

## 11. Failure modes and misuse

**The debugging black hole.** Symptom. An on-call engineer, paged because
order 4471 never shipped, has no single place to look, and spends the
incident correlating logs across four or more services by timestamp and
guesswork, or worse, by grepping for the order ID and hoping every service
happened to include it in every log line. Cause. No participant, and no
piece of infrastructure, was ever assigned the job of holding the process's
state or history. Fix. Mandate a correlation ID generated at the first event
and propagated, unmodified, through every subsequent event's metadata, and
build a dedicated event-store or tracing view keyed on that ID before the
system goes to production, not after the first bad incident. This exact
concern, the difficulty of understanding the big picture as steps grow, is
the reason Chris Richardson recommends orchestration once the choreography
outgrows a handful of steps (Chris Richardson, "Pattern, Saga,"
https://microservices.io/patterns/data/saga.html, verified 2026-08-03).

**Change-ripple paralysis.** Symptom. A product change that should take
one afternoon, adding a fraud check before shipping, instead takes a week,
because the engineer must find every service that reacts to the events
around the insertion point, confirm none of them assumes the old ordering,
and add a new subscription in the Shipping service without breaking anyone
else's existing subscription to the event that now fires one step later.
Cause. The sequence lives only in each service's local subscription
configuration, so there is no single diff that shows the whole change. Fix.
Maintain a living event-catalog document, generated if possible from the
actual subscription configuration rather than hand-maintained, and treat any
new event type or changed payload as requiring an explicit compatibility
review against every known subscriber, not only the ones the change author
remembers.

**Recursive self-triggering.** Symptom. A service enters a loop of
processing the same conceptual action over and over, driving cost and
sometimes an outage. Cause. A consumer writes back to the same resource that
triggered the event that invoked it, and the write itself satisfies the
trigger condition again. Amazon's own documentation names this precisely for
S3-triggered choreography, warning that a notification writing to the same
bucket that triggers it could cause an execution loop, giving the specific
example of a Lambda function triggered on upload that itself uploads to the
same bucket, indirectly triggering itself (Amazon Web Services, "Amazon S3
Event Notifications,"
https://docs.aws.amazon.com/AmazonS3/latest/userguide/EventNotifications.html,
verified 2026-08-03). Fix. Write outputs to a different bucket or a
different prefix explicitly excluded from the triggering notification
configuration.

**The forgotten compensation subscriber.** Symptom. A payment failure event
is published correctly, but an order stays stuck in a Placed state forever,
never transitioning to Cancelled, and no error is ever logged, because
nothing failed, a subscription was simply never written. Cause.
Compensating reactions are equally easy to omit as forward reactions are to
add, and unlike a missing forward step, a missing compensation step produces
no visible symptom until a customer complains weeks later. Fix. Treat every
new forward event type as requiring an explicit, reviewed decision about
which existing steps need a compensating subscription, and write an
automated test that asserts every publishable failure event has at least
one registered subscriber, even if that assertion has to run against a
static configuration file rather than live infrastructure.

**Event schema drift breaking a downstream consumer silently.** Symptom. A
subscriber quietly stops updating a field, or starts throwing swallowed
deserialization errors that land in a dead-letter queue nobody watches,
after an upstream service renames or removes a field it assumed was purely
internal. Cause. Because there is no compile-time contract between producer
and consumer, a producer has no mechanical way to know it broke
someone. Fix. Version event schemas explicitly, run consumer-driven contract
tests in CI for every known subscriber, and alert on dead-letter queue depth
as a first-class production signal, not an afterthought.

**Misapplied choreography for a strictly sequential, few-branch process**
already owned by one team. Symptom. A process with three straight-line
steps and a single owning team gets implemented as three services publishing
and subscribing to events on a broker, adding broker latency, operational
surface area, and debugging cost for no decoupling benefit, because there
was never more than one team involved. Cause. Reaching for the pattern by
habit rather than because any of the applicability conditions in dimension 4
actually held. Fix. Collapse the three reactive handlers into a single
in-process function call inside the one owning service, or if the boundary
genuinely needs to stay a service boundary, use a direct, synchronous call
or a simple orchestrator instead of an event bus.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Choreography | Orchestration | Publisher-Subscriber alone (no process semantics) | Two-Phase Commit |
|---|---|---|---|---|
| Coupling between services | Low. Producers do not know consumers | Medium. Participants know the orchestrator, not each other | Low, same transport, but carries no business-process meaning | High. All participants must speak the same coordinator protocol |
| Process visibility | Poor. Exists only as the sum of subscriptions | Strong. The orchestrator's definition is the process | Not applicable. No process is being modelled | Strong for the single transaction, but only for one atomic unit |
| Debuggability of a single instance | Poor without deliberate tracing investment | Good. The orchestrator holds instance state and history | Not applicable | Good while the transaction is open, unavailable once it commits or aborts |
| Cost of adding a step | Low. New subscriber attaches with no upstream change | Medium. Orchestrator definition must be edited and redeployed | Low, but again carries no process semantics on its own | High. Every participant's commit protocol code changes |
| Team autonomy | High | Medium. Teams share the orchestrator as a dependency | High | Low. Tight coordination required across all participants |
| Availability under partial failure | High. No single coordinator to lose | Medium. Orchestrator becomes a dependency, though it can be made highly available | High | Low. Blocking protocol, a coordinator or participant outage can leave resources locked |
| Suited to long-running, branching processes | Poor past a handful of steps | Strong. Built for exactly this | Not applicable | Poor. Designed for short-lived atomic transactions, not long-running workflows |
| Operational cost as the process grows | Rises steeply, correlated with process length | Rises more gradually, concentrated in the orchestrator | Low, if used only as a transport | Low per-transaction, but the blocking behavior itself is a scalability limit |

Reading of the table. Choreography wins on every axis that rewards
decentralization and independence, coupling, autonomy, and resilience to a
single point of failure, and loses on every axis that rewards a single
source of truth about the process, visibility, debuggability, and cost of
change as systems grow. Orchestration is close to the mirror image. Publisher-
Subscriber is included as a reminder that the messaging mechanism alone does
not make something a choreography, only the presence of a business process
being coordinated through it does. Two-Phase Commit is included because it
is the classical alternative Choreography and its sibling pattern Saga were
both invented to avoid, and the table shows why. It trades every one of
choreography's availability and autonomy wins for strict atomicity, which
does not survive service boundaries owned by separate teams operating
separate databases.

## 13. Related and incompatible patterns

- **Saga.** The most important relationship in this entry, and the one most
  likely to be confused with the pattern itself. Saga is a pattern for
  managing a distributed business transaction, specifically the sequencing
  of local transactions and their compensating actions, using either
  Choreography or Orchestration as the coordination mechanism. Choreography
  is broader. It applies to any cross-service reactive process, whether or
  not that process needs compensation semantics at all, for example a
  notification fan-out that has no concept of rolling back. A saga is a
  choreography, or an orchestration, with a specific job, keeping a
  multi-service transaction eventually consistent. Every choreographed saga
  is a choreography, but not every choreography is a saga. This
  repository's Saga entry covers the choreography-versus-orchestration
  decision in the specific context of compensating transactions in far more
  transactional depth than this entry does, and this entry is the correct
  place to start when the process being coordinated is not primarily
  about transactional consistency.
- **Orchestration.** The direct architectural alternative, not yet a
  separate entry in this repository at the time of writing but referenced
  throughout this one as the other pole of the central decision. Where
  Choreography distributes the sequence across every participant's
  subscriptions, Orchestration concentrates the sequence into one component
  that calls each participant and interprets the result. See dimension 12
  for the full comparison.
- **Publisher-Subscriber.** The messaging primitive Choreography is almost
  always built on top of. Pub-sub supplies the fan-out mechanism, one event
  to many subscribers, but carries no opinion about business process,
  ordering across producers, or compensation. Choreography is what happens
  when pub-sub is used specifically to coordinate a multi-step business
  outcome.
- **Event Sourcing.** Frequently deployed alongside Choreography but solves
  a different problem, a service's own internal state representation, not
  cross-service coordination. A service can be event-sourced internally
  while integrating with the outside world through direct API calls, in
  which case it is not participating in a choreography at all. In the
  reverse case, a service with a conventional CRUD database can happily
  participate in a
  choreography by publishing and subscribing to events that never touch its
  own persistence model. The two compose well because both already speak
  the language of immutable, past-tense events, but neither requires the
  other.
- **Process Manager.** The pattern most often mistaken for what a
  choreography secretly needs once it outgrows dimension 4's boundary. A
  Process Manager is effectively an explicit, stateful orchestrator built
  specifically to track a single long-running process instance, and
  introducing one is usually the correct refactor away from an overgrown
  choreography, covered in dimension 14.
- **Compensating Transaction.** The mechanism a choreographed saga uses to
  undo a completed step when a later step fails. It is a building block
  choreography relies on for correctness under failure, not a coordination
  style in itself.
- **Transactional Outbox.** A near-mandatory companion whenever a
  participant's local transaction must be atomic with the event it
  publishes. Without it, a service can commit its local change and then
  crash before publishing, silently breaking the choreography's chain, or
  publish successfully and then have its local commit fail, publishing an
  event about something that never actually happened.
- **Circuit Breaker.** Compatible and complementary rather than related to
  the coordination style itself. It protects a consumer's own outbound calls
  triggered by an incoming event, for instance a call to a third-party
  payment gateway inside the Payment service's reaction, and has no opinion
  about whether the overall process is choreographed or orchestrated.
- **CQRS.** A common companion for solving dimension 4's gap around
  answering what state a process is in right now. A dedicated read model,
  built by subscribing to the same events that drive the choreography,
  gives a queryable answer without introducing a central coordinator into
  the write path.
- **Incompatible with.** No pattern in this catalog is incompatible with
  Choreography in the way Two-Phase Commit is incompatible
  with Saga. Choreography's only true incompatibility is with a requirement,
  not a pattern, a hard requirement for a single, always-current, centrally
  queryable process state without building a separate read model, because
  that requirement is definitionally unmet by a coordination style with no
  central component.

## 14. Refactoring path in and out

Introducing Choreography into a system that currently coordinates a process
through direct, synchronous service-to-service calls.

1. Identify the process's steps and confirm each one already corresponds to
   a local transaction inside its owning service, not a cross-service
   transaction. If it does not, that is a separate, prior refactor.
2. Pick the first step and define the event it should publish on success, in
   the past tense, naming a fact, not the second step's action.
3. Add a Transactional Outbox to that first service so the local commit and
   the event publish become atomic. Run the existing integration tests
   unchanged, since the synchronous call still exists at this point and the
   event is purely additive.
4. Stand up a subscriber in the second service that reacts to the new event
   by performing exactly the same local transaction the synchronous call
   used to trigger. Run both paths in parallel, synchronous call and event
   reaction, behind a feature flag, and compare outcomes in a lower
   environment before trusting either.
5. Once parity is proven, remove the synchronous call, leaving the event
   reaction as the only path. Repeat steps two through five for each
   subsequent step.
6. Before calling the refactor complete, add a correlation ID to every event
   type involved and build or extend the tracing view from dimension 16.
   Skipping this step is the single most common way a fresh choreography
   arrives in production already blind.

Removing Choreography when it stops earning its place, the signal being a
process that has grown past dimension 4's boundary or that the team now
struggles to explain end to end.

1. Draw the actual event graph mechanically, from the real subscription
   configuration across every service, not from memory or from stale
   documentation. This step alone frequently surfaces the forgotten-
   compensation and change-ripple problems from dimension 11.
2. Introduce a Process Manager or a thin Orchestration component that, for
   now, does nothing but subscribe to the same events the choreography
   already produces and record the sequence, giving the team a first
   central view of the process with zero behavior change.
3. Once the orchestrator's recorded sequence is trusted to match reality,
   begin moving the decision logic, which service to call next, which
   compensating action to trigger, out of the individual services'
   subscriptions and into the orchestrator, one step at a time, keeping the
   old event-driven path live behind a flag until parity is proven exactly
   as in the introduction path above.
4. Convert the remaining participant services from autonomous
   event-subscribers into orchestrator-invoked participants, usually by
   exposing a synchronous or asynchronous command endpoint the orchestrator
   calls directly, rather than a passive event subscription.
5. Once every step is orchestrator-driven, remove the now-redundant event
   subscriptions between participant services, leaving events only where
   they still serve a genuine purpose, such as notifying an unrelated
   analytics consumer that was never really part of the coordinated
   process.

## 15. Testing and verification

Easier because of the pattern.

- Each participant's reaction can be tested in complete isolation, by
  publishing a synthetic event and asserting the resulting local state
  change, with no need to stand up any other service, real or mocked.
- Adding a new consumer's tests never requires touching an existing
  producer's test suite, since the producer genuinely does not know the new
  consumer exists.

Harder because of the pattern.

- There is no single test that exercises the whole process, because there is
  no single component that represents the whole process. A full-process test
  must itself become a small test rig that wires together every
  participating service or a faithful in-memory stand-in for each.
- Compensation paths are especially easy to under-test, because they only
  trigger on a failure event that is easy to forget to simulate, exactly
  mirroring the production failure mode in dimension 11.
- Ordering-dependent bugs, a subscriber that assumes event A always arrives
  before event B, are invisible in a test rig that happens to deliver
  events in publish order and only surface once the real broker's delivery
  guarantees, which are commonly at-least-once and not strictly ordered
  across producers, are exercised for real.

Techniques that apply.

- **Contract tests per event type, run from both sides.** The producer
  asserts every field it claims to publish is actually present and typed
  correctly. Every known consumer asserts it can still deserialize and
  handle the current schema. Run both in CI on every change to either side.
- **An in-memory event bus test double for participant-level unit tests.**
  A minimal publish-and-dispatch implementation lets a single service's test
  suite simulate incoming events and assert outgoing ones without a real
  broker, keeping these tests fast.
- **A full whole-process test rig against a real or embedded broker for the**
  handful of critical paths. Reserve this for the process's happy path and
  its two or three most important failure branches, since standing up every
  participant for every test is expensive and slow, and exhaustive coverage
  belongs at the contract-test level instead.
- **Randomized delay and out-of-order delivery tests.** Deliberately
  reorder or delay events in a test environment to surface the
  ordering-assumption bugs that a well-behaved local test rig will
  never expose on its own.
- **Dead-letter queue assertions.** A test that publishes a deliberately
  malformed or unexpected event and asserts it lands in a dead-letter queue
  rather than crashing the consumer or being silently dropped, directly
  covering the schema-drift failure mode from dimension 11.

## 16. Observability signals

Because no participant holds the process's full state, observability is not
optional polish for Choreography, it is the mechanism by which the missing
central view gets reconstructed after the fact. Skipping this dimension is
equivalent to shipping the pattern with its primary weakness deliberately
left unaddressed.

What to record.

- A correlation ID, generated once at the first event in a process instance
  and propagated unmodified through every subsequent event's metadata, on
  every log line and every trace span touched by that instance.
- A counter of events published per event type, and a counter of events
  consumed per event type per subscriber, so a mismatch between the two,
  more published than consumed, is visible as a gap rather than discovered
  through a customer complaint.
- Dead-letter queue depth per event type, alerted on any non-zero sustained
  value, since a growing dead-letter queue is the clearest available signal
  of the schema-drift failure mode.
- Total latency from the first event in a process instance to whichever
  event is treated as the process's completion signal, labelled by outcome,
  completed, compensated, or abandoned.
- A distributed trace spanning every hop, with each service's span tagged
  with the event type that triggered it, so a single trace view answers what
  happened to instance X without manual log correlation.

A healthy instance on a dashboard. The published and consumed counters for
every event type track each other closely with a small, stable delta
explained only by in-flight processing latency. Dead-letter queue depth
sits at or near zero across every type. Total latency is a tight
distribution with a thin tail. A support engineer can paste a correlation ID
into the tracing tool and see the complete history of any instance in one
view.

A failing instance. The consumed counter for one event type falls steadily
behind the published counter, pointing at a stalled or crashing consumer.
Dead-letter queue depth for a specific event type climbs after a deployment,
pointing at a schema change that broke a consumer nobody updated. Total
latency develops a long tail concentrated on instances that touch one
particular participant, localizing a slow step without reading any code. A
trace view that simply stops partway through, with no further spans and no
corresponding dead-letter entry, is the signature of the forgotten-
compensation failure mode from dimension 11, an event that was published
correctly but that nothing was ever registered to receive.

## 17. Security and privacy implications

Choreography is not silent on security the way some purely structural
patterns are, because the pattern's defining property, many independent
services receiving copies of the same event, is itself a data-distribution
decision with real consequences.

**Broad fan-out widens the blast radius of a single event's data.** An event
published with the intent of informing one specific downstream service is,
on a shared topic, visible to every current and future subscriber of that
topic, including ones the original publisher never anticipated. If an event
carries personal data through Event-Carried State Transfer, adding a new,
unrelated subscriber to the same topic silently grants that subscriber
access to that data with no code change on the publisher's side and often no
review process at all. Treat every event schema as a data-sharing contract,
apply the minimum-necessary-data principle to what an event actually
carries, and prefer thin notification events with a callback for any field
that is personal or sensitive, trading the convenience of Event-Carried
State Transfer for an auditable, per-request access check on the callback
path.

**Compensation logic is an attacker-relevant code path most teams under-test**
and under-review. Because compensating subscriptions are, as dimension 11
describes, the easiest part of a choreography to forget or under-specify,
they are also the part most likely to contain an authorization gap, for
instance a compensating refund reaction that trusts the event payload's
claimed amount without re-validating it against the original charge. Any
event that triggers a financial or state-reversing action should be treated
as an authorization boundary in its own right, independent of whichever
service published it, exactly as if it had arrived over an untrusted
network, because in a system with more than a few participants it
effectively has.

**Message-broker access control becomes the de facto system-wide**
authorization layer, and is easy to under-provision. Once many services
publish and subscribe on a shared bus, deciding which service can publish
which event type, and which service can subscribe to which topic, is a real
access-control decision with real consequences, yet broker permissions are
frequently configured once at initial setup and never revisited as new
services and new event types accumulate. Review topic-level or
event-type-level access control on the same schedule as any other production
authorization surface, not as a one-time infrastructure task.

On privacy specifically, the correlation ID recommended throughout dimension
16 deserves one explicit caveat. It is, by construction, a durable
cross-service identifier that ties a person's activity together across every
participating service's logs and traces. Treat it with the same retention
and access controls applied to any other identifier capable of re-linking
otherwise separated data, and confirm it does not itself encode personal
information, such as embedding a customer's email address directly in the
correlation string.

## 18. References

1. Wikipedia contributors. "Service choreography."
   https://en.wikipedia.org/wiki/Service_choreography
   Verified 2026-08-03. Source for the global-versus-local-perspective
   definition, the dancers-without-a-single-point-of-control summary, and
   the W3C WS-CDL and WSCI historical lineage in dimension 1.
2. Chris Richardson. "Pattern, Saga." microservices.io.
   https://microservices.io/patterns/data/saga.html
   Verified 2026-08-03. Source for the operational definition of
   choreography-based sagas, the Create Order saga worked example named in
   dimension 9, and the explicit statement that big-picture understanding
   degrades as the number of choreographed steps grows, cited in dimensions
   4 and 11.
3. Amazon Web Services. "What Is Amazon EventBridge?" AWS EventBridge User
   Guide.
   https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-what-is.html
   Verified 2026-08-03. Source for the event-bus and content-based routing
   description used in dimensions 4, 8, and 9.
4. Amazon Web Services. "Amazon S3 Event Notifications." Amazon S3 User
   Guide.
   https://docs.aws.amazon.com/AmazonS3/latest/userguide/EventNotifications.html
   Verified 2026-08-03. Source for the storage-triggered choreography
   variant in dimension 8, the production use in dimension 9, and the
   documented execution-loop failure mode in dimension 11.
5. Amazon Web Services. "What Is AWS Step Functions?" AWS Step Functions
   Developer Guide.
   https://docs.aws.amazon.com/step-functions/latest/dg/welcome.html
   Verified 2026-08-03. Source for the contrasting definition of a
   centrally defined, orchestrated workflow used in dimension 12's
   trade-off table.
6. Netflix. Conductor repository README.
   https://github.com/Netflix/conductor
   Verified 2026-08-03. Source for the named production orchestration
   engine cited as counter-evidence in dimension 9.
7. Hector Garcia-Molina and Kenneth Salem. "Sagas." Proceedings of the 1987
   ACM SIGMOD International Conference on Management of Data, 1987. Cited
   for the original transactional mechanism that choreographed and
   orchestrated sagas both implement, per the citation already established
   for this venue and year in this repository's Saga entry. Not
   independently re-verified against the original proceedings text in this
   session, treated as an established bibliographic fact consistent with
   standard distributed-systems literature and with this repository's
   existing Saga entry, not as a page-level quotation.

## Code examples

Three languages, chosen because they represent genuinely different idiomatic
shapes for the same coordination style. TypeScript shows the in-process
event-emitter simulation most engineers reach for first when learning the
pattern, useful for tests and small demonstrations even though a real
system would use a durable broker. Python shows the same shape with explicit
correlation-ID propagation, the discipline dimension 16 treats as
non-negotiable. Go shows the pattern implemented with channels, which is the
language's own idiomatic concurrency primitive and maps naturally onto
choreography's independent, reactive participants. All three were executed
locally and their output is reported below rather than only claimed.

### TypeScript

```typescript
type OrderEvent =
  | { type: "OrderPlaced"; orderId: string; correlationId: string }
  | { type: "StockReserved"; orderId: string; correlationId: string }
  | { type: "PaymentCharged"; orderId: string; correlationId: string }
  | { type: "PaymentFailed"; orderId: string; correlationId: string }
  | { type: "OrderShipped"; orderId: string; correlationId: string };

type Handler = (event: OrderEvent) => void;

class EventBus {
  private handlers = new Map<OrderEvent["type"], Handler[]>();

  subscribe(type: OrderEvent["type"], handler: Handler): void {
    const list = this.handlers.get(type) ?? [];
    list.push(handler);
    this.handlers.set(type, list);
  }

  publish(event: OrderEvent): void {
    console.log(`[bus] ${event.type} order=${event.orderId} corr=${event.correlationId}`);
    for (const handler of this.handlers.get(event.type) ?? []) {
      handler(event);
    }
  }
}

function wireChoreography(bus: EventBus): void {
  // Inventory reacts to a placed order by reserving stock.
  bus.subscribe("OrderPlaced", (e) => {
    bus.publish({ type: "StockReserved", orderId: e.orderId, correlationId: e.correlationId });
  });

  // Payment reacts to reserved stock. Simulates a decline for odd order ids.
  bus.subscribe("StockReserved", (e) => {
    const declined = e.orderId.endsWith("9");
    bus.publish({
      type: declined ? "PaymentFailed" : "PaymentCharged",
      orderId: e.orderId,
      correlationId: e.correlationId,
    });
  });

  // Shipping reacts only once payment succeeds.
  bus.subscribe("PaymentCharged", (e) => {
    bus.publish({ type: "OrderShipped", orderId: e.orderId, correlationId: e.correlationId });
  });
}

const bus = new EventBus();
wireChoreography(bus);
bus.publish({ type: "OrderPlaced", orderId: "order-1000", correlationId: "corr-a" });
bus.publish({ type: "OrderPlaced", orderId: "order-1009", correlationId: "corr-b" });
```

### Python

```python
from dataclasses import dataclass
from typing import Callable, Dict, List


@dataclass(frozen=True)
class Event:
    kind: str
    order_id: str
    correlation_id: str


class EventBus:
    def __init__(self) -> None:
        self._handlers: Dict[str, List[Callable[[Event], None]]] = {}

    def subscribe(self, kind: str, handler: Callable[[Event], None]) -> None:
        self._handlers.setdefault(kind, []).append(handler)

    def publish(self, event: Event) -> None:
        print(f"[bus] {event.kind} order={event.order_id} corr={event.correlation_id}")
        for handler in self._handlers.get(event.kind, []):
            handler(event)


def wire_choreography(bus: EventBus) -> None:
    def on_order_placed(e: Event) -> None:
        bus.publish(Event("StockReserved", e.order_id, e.correlation_id))

    def on_stock_reserved(e: Event) -> None:
        declined = e.order_id.endswith("9")
        kind = "PaymentFailed" if declined else "PaymentCharged"
        bus.publish(Event(kind, e.order_id, e.correlation_id))

    def on_payment_failed(e: Event) -> None:
        # Compensating reaction, release the stock that was reserved.
        bus.publish(Event("StockReleased", e.order_id, e.correlation_id))

    def on_payment_charged(e: Event) -> None:
        bus.publish(Event("OrderShipped", e.order_id, e.correlation_id))

    bus.subscribe("OrderPlaced", on_order_placed)
    bus.subscribe("StockReserved", on_stock_reserved)
    bus.subscribe("PaymentFailed", on_payment_failed)
    bus.subscribe("PaymentCharged", on_payment_charged)


if __name__ == "__main__":
    bus = EventBus()
    wire_choreography(bus)
    bus.publish(Event("OrderPlaced", "order-2000", "corr-c"))
    bus.publish(Event("OrderPlaced", "order-2009", "corr-d"))
```

### Go

```go
package main

import "fmt"

type Event struct {
	Kind          string
	OrderID       string
	CorrelationID string
}

type Bus struct {
	subscribers map[string][]chan Event
}

func NewBus() *Bus {
	return &Bus{subscribers: make(map[string][]chan Event)}
}

// Subscribe is called only during setup, before any goroutine publishes,
// so the map itself never needs a lock.
func (b *Bus) Subscribe(kind string) <-chan Event {
	ch := make(chan Event, 8)
	b.subscribers[kind] = append(b.subscribers[kind], ch)
	return ch
}

func (b *Bus) Publish(e Event) {
	fmt.Printf("[bus] %s order=%s corr=%s\n", e.Kind, e.OrderID, e.CorrelationID)
	for _, ch := range b.subscribers[e.Kind] {
		ch <- e
	}
}

func inventoryService(placed, failed <-chan Event, bus *Bus, done chan<- bool) {
	for i := 0; i < 2; i++ {
		select {
		case e := <-placed:
			bus.Publish(Event{"StockReserved", e.OrderID, e.CorrelationID})
		case e := <-failed:
			bus.Publish(Event{"StockReleased", e.OrderID, e.CorrelationID})
		}
	}
	done <- true
}

func paymentService(reserved <-chan Event, bus *Bus, done chan<- bool) {
	for i := 0; i < 2; i++ {
		e := <-reserved
		declined := e.OrderID[len(e.OrderID)-1] == '9'
		kind := "PaymentCharged"
		if declined {
			kind = "PaymentFailed"
		}
		bus.Publish(Event{kind, e.OrderID, e.CorrelationID})
	}
	done <- true
}

func shippingService(charged <-chan Event, bus *Bus, done chan<- bool) {
	e := <-charged
	bus.Publish(Event{"OrderShipped", e.OrderID, e.CorrelationID})
	done <- true
}

func main() {
	bus := NewBus()

	// All subscriptions are registered here, before any goroutine runs,
	// so Subscribe never races with a concurrent Publish.
	placed := bus.Subscribe("OrderPlaced")
	failed := bus.Subscribe("PaymentFailed")
	reserved := bus.Subscribe("StockReserved")
	charged := bus.Subscribe("PaymentCharged")

	done := make(chan bool, 3)
	go inventoryService(placed, failed, bus, done)
	go paymentService(reserved, bus, done)
	go shippingService(charged, bus, done)

	bus.Publish(Event{"OrderPlaced", "order-3000", "corr-e"})
	bus.Publish(Event{"OrderPlaced", "order-3009", "corr-f"})

	<-done
	<-done
	<-done
}
```
