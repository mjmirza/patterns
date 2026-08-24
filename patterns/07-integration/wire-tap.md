---
name: Wire Tap
slug: wire-tap
family: 07-integration
category: Enterprise Integration
aliases: [Message Tap, Channel Tap, Passive Interceptor]
first_described: "Hohpe, Woolf 2003"
maturity: canonical
related: [content-enricher, recipient-list, message-filter, control-bus, dead-letter-channel]
incompatible_with: []
verified: 2026-08-02
---

# Wire Tap

## 1. Name, aliases, and lineage

The canonical name is Wire Tap. It is documented as an Enterprise Integration
Pattern in Gregor Hohpe and Bobby Woolf, *Enterprise Integration Patterns.
Designing, Building, and Deploying Messaging Solutions*, Addison-Wesley, 2003,
in the Message Routing chapter, under the entry titled "Wire Tap"
([enterpriseintegrationpatterns.com/patterns/messaging/WireTap.html](https://www.enterpriseintegrationpatterns.com/patterns/messaging/WireTap.html),
verified 2026-08-02). The book's own solution statement is quoted directly on
that page. "Insert a simple Recipient List into the channel that publishes
each incoming message to the main channel and a secondary channel." Hohpe and
Woolf take the name from the literal, physical practice of wire tapping a
telephone or telegraph line, splicing a second circuit onto an existing one so
a listener can hear the traffic without breaking the original circuit.

The pattern is a specialization of Recipient List (also Hohpe and Woolf, same
chapter), fixed to exactly two static recipients, the original destination and
a monitoring destination, applied to every message with no filter, or gated
by a simple predicate. Framework implementations use two other names for the
same idea. Spring Integration calls its implementation a Wire Tap, configured
as a channel interceptor rather than a routing step, documented in the Spring
Integration Reference under Message Channel configuration
([docs.spring.io/spring-integration/reference/channel/configuration.html](https://docs.spring.io/spring-integration/reference/channel/configuration.html),
verified 2026-08-02). Apache Camel calls it the Wire Tap EIP, implemented as an
enterprise integration pattern element in its routing DSL rather than as an
interceptor bolted onto a channel object
([camel.apache.org/components/next/eips/wireTap-eip.html](https://camel.apache.org/components/next/eips/wireTap-eip.html),
verified 2026-08-02). Both frameworks keep the name Wire Tap, so there is no
real naming clash in the surrounding tooling the way there is for, say, Simple
Factory versus Factory Method.

Message Tap and Channel Tap appear as informal synonyms in vendor
documentation and blog writing for the same construct, always describing a
passive copy of message traffic sent to a second destination. Passive
Interceptor is used occasionally to distinguish Wire Tap from an active
interceptor that can veto, transform, or delay the message, since a correctly
built Wire Tap does neither.

## 2. Problem and context

A message flows from a producer, through a channel, to a consumer, and the
system needs visibility into that traffic for a purpose that has nothing to do
with the business logic the consumer performs. The visibility need is one or
more of, monitoring live throughput and latency, auditing every message for
compliance or dispute resolution, debugging a route in a running system
without attaching a debugger to the production process, feeding a downstream
analytics or fraud detection pipeline, or replaying traffic into a staging
environment to reproduce a bug.

The naive answer is to change the consumer, add a logging call, an audit
write, or a forwarding call at the top of the handler. That naive answer
couples an operational concern to business code, and it means every consumer
that needs monitoring has to be edited and redeployed, and every consumer that
is added later has to remember to include the same boilerplate. It also means
the monitoring code runs inside the consumer's transaction and failure domain.
A slow or broken audit sink can now break or slow the actual business
processing, which is precisely backwards, since the business processing is
what the system exists to do and the audit is a secondary concern about the
business processing.

The context in which Wire Tap is reached for is a message-based architecture,
a message queue, an event bus, or a routing engine such as Camel, where
messages already flow through addressable channels rather than through direct
method calls. The pattern is not natural outside that context. In a plain
synchronous call stack the equivalent problem is usually solved with
structured logging, a decorator, or an observability agent instrumenting the
call, not with a literal second recipient, because there is no channel object
to intercept.

## 3. Forces

The pattern balances five competing pressures.

**Fidelity against performance.** A tap that copies the message deeply and
serializes it before forwarding gives the observer a faithful, immutable
snapshot, at the cost of CPU and allocation on every message. A tap that
forwards a reference to the same object risks the observer or the primary
consumer mutating shared state, and risks a slow observer holding a reference
that prevents garbage collection of a large payload. Camel's own
implementation documents this trade-off directly, stating that the tap "won't
do a deep clone" of the exchange by default and that a deep copy needs an
explicit `onPrepare` processor
([camel.apache.org/components/next/eips/wireTap-eip.html](https://camel.apache.org/components/next/eips/wireTap-eip.html),
verified 2026-08-02).

**Isolation against latency.** Sending the tapped copy synchronously, in the
same thread and transaction as the primary send, guarantees the tap observed
exactly what happened and in what order, but it makes the primary path
dependent on the tap channel's availability and speed. Sending it
asynchronously, on a separate thread or through a separate broker connection,
protects the primary path but introduces the possibility that the tap never
arrives, arrives out of order, or arrives after the primary consumer has
already acted. Camel's `executorService` option and Spring Integration's
async-channel wiring exist specifically to make this trade-off an explicit,
per-tap configuration choice rather than an implicit default.

**Coverage against noise.** A tap with no filter applied to every message
gives complete visibility and a complete audit trail, at the cost of doubling
traffic volume on the observed channel and generating a large amount of data
that may never be read. A gated tap, filtered by a predicate or a selector
expression, reduces volume but reduces coverage, and a predicate written to
catch "the interesting messages" is only as good as the operator's prediction
of what interesting will turn out to mean during the next incident, which is
exactly the moment the predicate is usually wrong.

**Transparency against operability.** The pattern's entire value proposition
is that the tapped observer is invisible to the two endpoints of the primary
route, neither producer nor consumer is aware the tap exists or changes
behavior because of it. That same invisibility is an operability risk. a tap
silently added to a channel and forgotten becomes an undocumented dependency,
a secondary consumer of production data that nobody remembers exists, until
someone tries to decommission or reroute the channel and discovers a tap was
depending on it.

**Cost against retention.** The volume a full-fidelity tap with no filter
generates has to land somewhere, and audit or compliance requirements often
demand retention measured in months or years, not days. The forces above
about fidelity and coverage feed directly into a storage and retention cost
that the pattern description itself is silent about, and that the operator
has to size deliberately.

## 4. Applicability and non-applicability

Reach for Wire Tap when all of the following hold.

- The system already routes messages through addressable channels, so a
  second recipient can be attached without changing how the primary consumer
  is written or deployed.
- The observation need is passive. the tap must never be allowed to change
  the outcome of the primary route, veto a message, or delay it beyond a
  bound the business can tolerate.
- The observing consumer and the primary consumer have genuinely independent
  failure domains, so a crash or slowdown in the observer must never be
  allowed to propagate back into the primary path.
- The requirement is audit, monitoring, debugging, or feeding a secondary
  analytics pipeline, not correcting, enriching, or validating the message,
  which are jobs for Content Enricher, Content Filter, or a genuine validating
  consumer instead.

Do NOT reach for Wire Tap in these cases.

- **The observer needs to change the message before it reaches the primary
  consumer.** Wire Tap is defined as passive. a component that must add,
  strip, or correct fields belongs on the primary route itself, most often as
  a Content Enricher or Content Filter, not on a tapped side channel that the
  primary consumer never sees.
- **The observer needs to block or reject a message.** That is Message Filter
  or a validating gateway on the primary channel. Building rejection logic
  into a wire tap turns an observation mechanism into a routing decision that
  half the system, the tap consumer, can see and half, anyone reading the
  primary route's code, cannot, which is a maintainability trap.
- **There is no messaging channel to intercept.** In a request or reply web
  service call with no broker, the equivalent problem is usually better
  solved with structured request logging middleware or a service mesh sidecar
  proxy, which is architecturally closer to a network-level tap than a
  message-routing tap and does not require introducing a broker only to gain
  observability.
- **The volume is high and the tap has no filter and uses synchronous
  delivery.** A synchronous tap with no filter on a very high-throughput
  channel can double the load on that channel and couple its latency to the
  tap sink's latency, which defeats the isolation the pattern promises unless
  the tap is made asynchronous, sampled, or both.
- **Exactly-once, ordered delivery to the tap sink is a hard requirement.**
  The pattern as described by Hohpe and Woolf, and as implemented by Camel and
  Spring Integration by default, is best-effort. a tap consumer that requires
  guaranteed, ordered delivery needs Guaranteed Delivery and Resequencer
  wired explicitly onto the tap channel, which is additional machinery the
  base pattern does not provide.

## 5. Structure

Three participants.

- **Source channel.** The existing channel carrying messages from a producer
  toward a primary consumer, before and after the tap is inserted. The tap
  must not change this channel's contract, its message format, its ordering
  guarantee, or its delivery semantics as observed by the primary consumer.
- **Wire Tap.** The interception point spliced onto the source channel. It
  receives every message, or every message matching a selector, that would
  have flowed to the primary consumer anyway, forwards the original,
  unmodified message onward to the primary consumer exactly as before, and
  additionally forwards a copy, or a reference, of the same message to the
  secondary channel. In shape it is a two-recipient Recipient List with
  one recipient fixed to whatever the original destination already was.
- **Secondary channel and tap consumer.** A separate channel, with its own
  consumer, that exists purely to observe. Common tap consumers are a logging
  adapter, an audit-trail writer, a metrics aggregator, or a message store
  used for later replay. The tap consumer has no ability to affect the
  primary route and, correctly built, the primary consumer has no way to
  detect that a tap is attached at all.

## 6. ASCII structure diagram

```
  Producer
     |
     v
  +-------------------+
  |  Source Channel    |
  +---------+----------+
            |
            v
  +---------------------------+
  |        Wire Tap           |
  |  (fixed Recipient List)   |
  +------------+--------------+
               |
       +-------+-------+
       |               |
       v               v
+-------------+  +-------------------+
| Primary     |  | Secondary Channel |
| Consumer    |  | (audit / metrics  |
| (unchanged) |  |  / debug sink)    |
+-------------+  +-------------------+
                          |
                          v
                  +---------------+
                  | Tap Consumer  |
                  | (log, DB, ES) |
                  +---------------+
```

## 7. Dynamics

```
Producer         Source Channel    Wire Tap        Primary Consumer   Tap Consumer
   |                    |              |                   |               |
   |--send(msg)-------->|              |                   |               |
   |                    |--forward---->|                   |               |
   |                    |              |--copy(msg)------->|               |
   |                    |              |   [unchanged,     |               |
   |                    |              |    same order]    |               |
   |                    |              |--tap(copy)---------------------->|
   |                    |              |   [async or sync, |               |
   |                    |              |    best effort]   |               |
   |                    |              |                   |--process()    |
   |                    |              |                   |   (unaware    |
   |                    |              |                   |    of tap)    |
```

The critical property of the timeline is that the arrow into Primary Consumer
and the arrow into Tap Consumer both originate at the same point, the Wire
Tap, and neither arrow blocks the other under a correctly built tap. If the
tap send is made synchronous and on the same thread as the primary send, the
diagram still holds, but the two arrows become sequential rather than
concurrent, which reintroduces the latency coupling described in dimension 3.
A Wire Tap that reverses the order, sending to the tap consumer first and only
forwarding to the primary consumer after the tap send returns successfully,
has stopped being a Wire Tap and has become a synchronous audit gate, a
different and much stronger pattern with its own consequences, since the
primary route now depends on the tap channel being up.

## 8. Implementation variants

**Interceptor on an existing channel object.** The tap is registered as a
decorator or listener on the channel abstraction itself, so nothing about the
route's declared topology changes, only the channel's runtime behavior. This
is Spring Integration's approach. a `wire-tap` element nested inside a
channel's `interceptors` block, or the fluent `.wireTap(...)` call on a
`MessageChannel` builder in Java configuration
([docs.spring.io/spring-integration/reference/channel/configuration.html](https://docs.spring.io/spring-integration/reference/channel/configuration.html),
verified 2026-08-02). The advantage is that the tap can be added or removed
without touching the route definition that already exists. the disadvantage
is that the tap becomes invisible in a reading of the route's own
configuration, and only becomes visible by reading the channel's
configuration separately, which is exactly the forgotten dependency risk
named under Forces.

**First-class routing step in a DSL.** The tap is written as an explicit line
in the route definition itself, alongside other routing calls. This is
Camel's approach, `wireTap("direct-auditSink")` placed inline in the route
builder, with `copy`, `dynamicUri`, and `executorService` as first-class
options on that line
([camel.apache.org/components/next/eips/wireTap-eip.html](https://camel.apache.org/components/next/eips/wireTap-eip.html),
verified 2026-08-02). The advantage is that the tap is visible to anyone
reading the route. the disadvantage is that changing which channels are
tapped requires a route change and redeploy, unless the destination is made
dynamic.

**Selector-gated conditional tap.** Rather than tap every message, the tap is
wired with a predicate, a `MessageSelector` bean reference or a boolean SpEL
selector expression, so only messages matching a condition are forwarded to
the secondary channel. This directly implements the coverage-against-noise
trade-off from dimension 3 as a configuration knob rather than a hardcoded
choice.

**Global or pattern-matched tap.** Spring Integration additionally supports a
top-level `wire-tap` element that attaches to every channel whose name
matches a given wildcard pattern, rather than requiring one tap declaration
per channel. This is a bulk-application variant useful for turning on broad
diagnostic tracing across a whole application during an incident, then
removing it afterward.

**Sidecar or network-level tap.** Outside message-broker frameworks, the same
structural idea is realized without any application code change, by
mirroring traffic at the infrastructure layer, a service mesh sidecar proxy
mirroring a percentage of requests to a shadow endpoint, or a network TAP or
SPAN port copying packets to an analysis appliance. This variant sits at the
edge of the pattern's scope, discussed further in dimension 9, and trades
application-level message semantics for zero code coupling.

## 9. Known production uses

**Apache Camel's Wire Tap EIP.** Camel implements Wire Tap as a built-in
routing element, `wireTap(String uri)`, available in every Camel route
regardless of the underlying transport. Documented options include `copy`
(default true, copies the Exchange before tapping), `dynamicUri` (evaluate the
destination with the Simple expression language per message), and
`executorService` (route the tapped Exchange through a dedicated thread pool
so it does not compete with the primary route's threads)
([camel.apache.org/components/next/eips/wireTap-eip.html](https://camel.apache.org/components/next/eips/wireTap-eip.html),
verified 2026-08-02).

**Spring Integration's wire-tap channel interceptor.** Spring Integration
ships Wire Tap as a first-class `ChannelInterceptor` implementation,
configurable per channel through the `wire-tap` XML element or the
`.wireTap(...)` method on the Java DSL channel builder, with optional
`selector` or selector expression filtering and optional async delivery to
the tapped channel
([docs.spring.io/spring-integration/reference/channel/configuration.html](https://docs.spring.io/spring-integration/reference/channel/configuration.html),
verified 2026-08-02). Spring Integration's own documentation names debugging,
auditing, including sending audit messages to a separate channel from within
an existing transaction, and logging as the primary use cases, matching the
motivation described in dimension 2 of this entry.

**Hohpe and Woolf's own worked description, cited across enterprise
integration literature and framework documentation.** The pattern's canonical
description on enterpriseintegrationpatterns.com is the reference every major
integration framework's own documentation, including Camel's and Spring
Integration's, points back to when introducing their respective Wire Tap
implementations
([enterpriseintegrationpatterns.com/patterns/messaging/WireTap.html](https://www.enterpriseintegrationpatterns.com/patterns/messaging/WireTap.html),
verified 2026-08-02). Because Camel and Spring Integration are two
independently maintained, widely deployed open-source integration frameworks
that both implement the pattern under its original name with compatible
semantics, the agreement itself is evidence that Wire Tap names a real,
recurring need in production messaging systems rather than an academic
construct.

## 10. Consequences

Positive.

- The primary route's code and configuration are untouched by adding or
  removing a tap, so observability can be turned on, adjusted, or turned off
  without a change to business logic and, in the interceptor variant,
  sometimes without a redeploy of the route at all.
- A single tap implementation, a logger, an audit writer, a metrics
  collector, can be reused across every channel that needs the same kind of
  observation, rather than being copy-pasted into each consumer.
- Correctly built as fire-and-forget, a tap failure or slowdown is isolated
  from the primary path, so observability tooling cannot become an outage
  cause for the business flow it is watching.
- The tap consumer sees exactly the same message the primary consumer sees,
  which makes it a faithful source for reproducing a bug, replaying traffic
  into a test environment, or reconstructing what happened during an
  incident.

Negative.

- A tap with no filter doubles message volume on the tapped channel and
  shifts a real, sometimes substantial, storage and processing cost onto
  whatever backs the secondary channel, a cost the pattern description itself
  does not size for the implementer.
- A tap added silently, especially in the interceptor variant where it lives
  outside the route definition, becomes an undocumented consumer of the
  channel. it is invisible to anyone reading the route, and it can be broken
  by a channel refactor nobody realized had a hidden dependent.
- If the tap send is implemented synchronously and on the same thread as the
  primary send, which is Spring Integration's own stated default behavior
  unless the target channel is asynchronous, the primary path's latency and
  availability become coupled to the tap sink's latency and availability,
  which is the opposite of the isolation the pattern is usually adopted to
  get.
- Because the default is a shallow copy of the Exchange rather than a deep
  clone, as Camel's documentation states plainly, a tap consumer or the
  primary consumer that mutates a shared mutable payload can produce
  observably different data on the two paths, undermining the audit
  fidelity the pattern exists to provide.
- Tapped traffic, especially in an audit context, frequently contains the
  same sensitive data as the primary message, so the tap multiplies the
  system's data-handling surface area without automatically inheriting the
  primary path's access controls, retention policy, or encryption.

## 11. Failure modes and misuse

**Symptom.** The primary consumer's p99 latency rises noticeably right after
a new tap is added to its channel, with no change to the consumer's own code.
**Cause.** The tap was wired synchronously, on the same thread as the primary
delivery, and the tap sink, commonly a database write or a remote logging
service, is slower than the channel's normal delivery path. **Fix.** Move the
tapped delivery onto a dedicated thread pool or asynchronous channel, matching
Camel's `executorService` option or Spring Integration's async-channel wiring,
so the tap send genuinely happens off the primary path's critical path.

**Symptom.** During an incident, an operator disables or reroutes a channel
that appears in no route diagram, and a completely unrelated audit dashboard
or compliance report silently stops updating, discovered days or weeks later.
**Cause.** A wire tap was configured as a channel interceptor, invisible in
the route's own declared configuration, and nobody documented that the
channel had a tap attached. **Fix.** Treat every tap as a first-class,
documented dependency of the channel it observes. prefer the DSL-visible
variant, an explicit `wireTap(...)` step in the route, over the hidden
interceptor variant wherever the framework offers both, and maintain an
inventory of active taps as part of the system's operational documentation.

**Symptom.** The audit log and the primary consumer's processed record
disagree about the content of a specific field for the same message, and the
disagreement is intermittent, not consistent.
**Cause.** The tap forwarded a shallow copy or a bare reference to a mutable
payload object, and either the primary consumer or the tap consumer mutated
that shared object in place before the other side read it, a straightforward
race condition once the two consumers run concurrently on separate threads.
**Fix.** Configure a genuine deep copy at the tap point, Camel's `onPrepare`
processor is documented for exactly this, or, as a stronger alternative, make
the message payload immutable at the point where it enters the channel, so no
shared mutable state can exist for either consumer to race on.

**Symptom.** A message that later turns out to have been dropped, corrupted,
or delayed on the primary path shows nothing unusual in the tap's audit
trail, so the audit trail cannot be trusted to explain the incident.
**Cause.** Someone assumed the tap provides guaranteed, ordered delivery
equivalent to the primary channel's own delivery guarantee, when the tap as
built used a best-effort, fire-and-forget send with no retry and no
persistence. **Fix.** Decide the tap's delivery guarantee explicitly and
document it next to the tap's configuration. if the audit use case genuinely
needs guaranteed delivery, compose the tap with Guaranteed Delivery on the
secondary channel rather than assuming Wire Tap alone provides it.

**Symptom.** A well-intentioned engineer extends the tap consumer to reject or
retry the message back onto the primary channel when the audit write fails,
and now an audit sink outage causes the primary business flow to stall or
retry storms.
**Cause.** The tap stopped being passive. it was given the ability to affect
the primary route's outcome, which is the single property Wire Tap is
supposed to guarantee it does not have. **Fix.** Keep the tap consumer's
failure handling entirely local to the secondary channel, its own dead letter
channel, its own retry policy, with zero code path that can propagate a
failure or a decision back to the primary consumer.

## 12. Trade-off matrix

| Concern | Wire Tap | Recipient List (general) | Content Enricher | Service mesh traffic mirroring |
|---|---|---|---|---|
| Changes the message on the primary path | Never, by definition | Never on any recipient | Yes, adds data before forwarding | Never, operates below the application |
| Number of destinations | Exactly two, one fixed as the original | Arbitrary, computed per message | One, the enriched onward path | Primary plus a percentage-sampled mirror |
| Requires application code changes | Small, one interceptor or route line | Yes, a routing rule to write and maintain | Yes, a lookup and merge step to write | No, configured at the infrastructure layer |
| Coupling to message broker abstractions | Tight, needs a channel to splice onto | Tight, same requirement | Tight, same requirement | Loose, works over raw network traffic |
| Typical primary use | Passive observation, audit, debug | Active fan-out to multiple real consumers | Filling in missing data the consumer needs | Shadow testing, canary comparison |
| Failure isolation from primary path | Strong when async, weak when sync | Depends per recipient, not guaranteed by the pattern | Enrichment failure blocks the primary path by design | Strong, mirroring cannot affect the primary request |

## 13. Related and incompatible patterns

**Recipient List.** Wire Tap is, in shape, a fixed, two-recipient
specialization of Recipient List. where Recipient List computes an arbitrary
set of real, participating destinations for a message, Wire Tap has exactly
two destinations and one of them, the observer, is understood by every reader
of the pattern to be non-participating, passive, and disposable without
affecting the business outcome. Recognizing this relationship prevents the
common mistake of building a general Recipient List and calling it a Wire Tap
once someone adds a monitoring destination to the list.

**Content Enricher.** Both patterns intercept a message mid-flight and add a
side effect. they diverge on whether the primary path's message is allowed to
change. Content Enricher's entire purpose is to change what the primary
consumer receives. Wire Tap's entire purpose is to guarantee the primary
consumer receives exactly what it would have received anyway. A component
that starts as a Wire Tap and grows a "we can add one more field while we are
here" feature has become a Content Enricher wearing a Wire Tap's name, and
that drift is worth catching in review.

**Message Filter.** A Wire Tap is frequently combined with a Message Filter on
its secondary channel, so only messages matching a condition, an error
status, a specific message type, a sampled percentage, reach the tap
consumer, addressing the coverage-against-noise force from dimension 3
without touching the primary path at all.

**Control Bus.** Where the Control Bus pattern exposes management operations
over the messaging system itself, starting a route, stopping a route,
querying a metric, a Wire Tap attached to a Control Bus channel is a natural
way to audit every administrative command issued against a running
integration system, a common compliance requirement in regulated
environments.

**Dead Letter Channel.** The two patterns solve unrelated problems, delivery
failure versus passive observation, but they are frequently composed. a Wire
Tap's own secondary delivery can fail, and wiring a Dead Letter Channel behind
the tap sink prevents a failed audit delivery from being silently lost, which
matters directly for the guaranteed-delivery failure mode in dimension 11.

**Incompatible with itself when made stateful.** There is no other named
pattern this entry marks as incompatible by shape, but a Wire Tap that
accumulates state across messages, a running counter, a window aggregation,
stops being a Wire Tap in the strict sense and becomes an Aggregator sitting
on a tapped channel. That is a legitimate design, but it should be named and
reasoned about as an Aggregator, because it inherits Aggregator's ordering,
completeness, and timeout concerns, which a stateless tap never has to think
about.

## 14. Refactoring path in and out

**Introducing a Wire Tap into an existing route.** Start from a channel with
exactly one consumer and no tap. First, decide the delivery guarantee the tap
needs, before writing any code, because retrofitting that decision after the
tap is already carrying traffic is far more disruptive than deciding it up
front. Second, add the tap as an explicit step, in the DSL-visible variant
where the framework offers one, rather than as a hidden interceptor, so the
new dependency is documented by construction. Third, wire the tap's delivery
asynchronously from the start, even if the initial tap consumer is fast,
because the tap consumer's performance characteristics are exactly the kind
of detail that changes later without anyone revisiting the tap configuration.
Fourth, add a selector or filter if the volume is high enough that a tap with
no filter would create a real storage or processing cost, per dimension 3.
Fifth, verify in a staging environment that disabling the tap consumer
entirely, simulating its outage, produces zero observable change on the
primary path, which is the direct test of whether the tap is genuinely
passive.

**Removing a Wire Tap that has stopped earning its place.** A tap earns
removal when its consumer has had no read traffic, no dashboard views, no
alert firings, and no query activity for a defined window, commonly measured
in months for audit sinks with a retention requirement, and shorter for
ad-hoc debugging taps that were only ever meant to be temporary. Before
removing, confirm the tap has no undocumented downstream dependent, precisely
the risk named under Consequences and Failure Modes, by checking access logs
or query history on the tap consumer's storage, not merely by asking around.
Remove the tap configuration itself first and leave the tap consumer's data
in place for the remainder of its retention window, rather than tearing both
down in the same change, so a mistaken removal can be reversed by re-adding
the tap without having also lost historical data.

## 15. Testing and verification

Testing code that has a Wire Tap attached is easier in one specific respect
and harder in one specific respect. It is easier because the primary
consumer's tests need no change at all. a correctly built tap is invisible to
the primary consumer's behavior, so any existing test suite for that
consumer should pass unmodified with the tap attached or detached, and that
invariant is itself a useful automated test, run the primary consumer's full
existing test suite twice, once with the tap wired to a real, in-memory or
mocked, secondary channel and once with the tap entirely absent, and assert
identical outcomes both times.

It is harder because the tap's own two properties, that it delivers a
faithful copy and that it never blocks or alters the primary delivery, both
need dedicated tests that a typical unit test for the primary consumer would
never exercise. A copy-fidelity test sends a message with a known payload
through the tapped channel and asserts the tap consumer received a value
equal to, and for mutable payloads distinct in identity from, what the
primary consumer received. An isolation test replaces the tap consumer with a
double that raises an exception, or blocks indefinitely, on every message,
and asserts that the primary consumer still completes successfully and within
its normal latency bound. a Wire Tap implementation that fails this second
test has a latent production incident waiting inside it, exactly the
synchronous-coupling failure mode from dimension 11.

Integration tests should verify the async delivery path specifically, since
async delivery is where ordering and delivery guarantees actually get tested.
send a burst of messages faster than the tap consumer can process them and
assert the primary path's throughput is unaffected while the tap consumer
either keeps pace on its own queue or, if it falls behind, does so without
back-pressuring the primary channel.

## 16. Observability signals

The tap itself needs to be observable, since a tap that silently stops
tapping defeats the entire reason it was added and, per dimension 11, can go
unnoticed for a long time. The signals worth tracking are, the count of
messages seen on the source channel versus the count delivered to the tap
consumer, which should track together within an expected ratio if a selector
is in use, and diverge sharply, a clear alert condition, if the tap has
silently stopped forwarding while the primary channel keeps flowing normally.
The queue depth or backlog on the tap's async delivery path, if one is used,
since a growing backlog is the earliest sign that the tap consumer cannot
keep up and that either the isolation is about to be tested for real or the
audit trail is about to develop a gap. The latency added to the primary send
by the tap, which should be effectively zero for an async tap and should be
tracked explicitly as a metric so a regression to synchronous behavior, an
easy accidental configuration change, is caught before it shows up as a
general latency incident with an obscure root cause. And the error rate on
the tap consumer's own delivery, tracked separately from the primary
consumer's error rate, since the two failure domains are supposed to be
independent and a dashboard that conflates them defeats the purpose of
separating them in the first place.

A healthy tap, on a dashboard, looks like a near-constant ratio between
source-channel volume and tap-consumer volume, near-zero added latency on the
primary path, and a tap-consumer error rate that moves independently of the
primary consumer's error rate. A failing tap looks like either a growing gap
between source volume and tap volume with no corresponding selector change,
or a latency series on the primary path that starts correlating with the tap
consumer's own reported latency, which is the direct symptom of the
synchronous-coupling failure mode.

## 17. Security and privacy implications

A Wire Tap, by construction, sends a copy of the same data the primary
consumer sees to a second destination, so it directly and mechanically
enlarges the system's data-handling surface area. Every piece of personal,
financial, or otherwise regulated data present in a tapped message is now
present in two places, the primary consumer's storage and the tap consumer's
storage, and the tap destination inherits none of the primary path's access
controls, encryption, or retention policy automatically. this has to be
configured deliberately on the tap sink, and it is frequently forgotten
precisely because the tap was added as an operational afterthought rather
than as a first-class part of the system's data flow diagram.

The naming itself, borrowed from telephone wiretapping, is a useful prompt
for the implementer to ask the same question a real wiretap raises. who is
authorized to read this traffic, under what legal or contractual basis, and
for how long. An audit or compliance tap in particular needs its retention
period defined explicitly, since audit data is frequently subject to both a
minimum retention requirement, for dispute resolution or regulatory
compliance, and a maximum retention requirement, under data minimization
obligations in regimes such as the EU's GDPR, and those two requirements have
to be reconciled by the person configuring the tap sink, not left as a
default the storage backend happened to ship with.

Access to the tap's configuration itself is a privilege worth guarding
separately from access to the primary route's configuration, since the
ability to attach a new, silent, passive tap to a production channel carrying
sensitive traffic is functionally the ability to exfiltrate that traffic
without the primary consumer, or its operators, having any visibility into
the fact that a new observer now exists. Framework-level audit logging of who
added or modified a tap configuration, not merely audit logging of the
tapped traffic itself, is worth treating as a requirement in any system where
the tapped channels carry sensitive data.

## 18. References

1. Gregor Hohpe and Bobby Woolf, *Enterprise Integration Patterns. Designing,
   Building, and Deploying Messaging Solutions*, Addison-Wesley, 2003, Message
   Routing chapter, "Wire Tap" entry. Companion web page,
   [enterpriseintegrationpatterns.com/patterns/messaging/WireTap.html](https://www.enterpriseintegrationpatterns.com/patterns/messaging/WireTap.html),
   verified 2026-08-02.
2. Apache Camel documentation, "Wire Tap EIP",
   [camel.apache.org/components/next/eips/wireTap-eip.html](https://camel.apache.org/components/next/eips/wireTap-eip.html),
   verified 2026-08-02.
3. Spring Integration Reference Documentation, "Configuring a Message Channel"
   (wire tap interceptor section),
   [docs.spring.io/spring-integration/reference/channel/configuration.html](https://docs.spring.io/spring-integration/reference/channel/configuration.html),
   verified 2026-08-02.

## Code examples

Three languages, chosen for how differently each expresses the same shape.
TypeScript shows the plain synchronous-to-asynchronous handoff with a
selector and a shallow copy of the message. Python shows the same idea with a
dedicated worker thread and a queue, plus a genuine deep copy rather than a
shallow one, matching the fidelity trade-off from dimension 3. Go shows the
non-blocking, drop-if-behind variant using a buffered channel and a select
with a default case, the idiomatic Go way to express "do not let a slow
observer stall the sender."

### TypeScript

```typescript
type Message = { id: number; payload: string };
type Consumer = (msg: Message) => void;

class Channel {
  private consumers: Consumer[] = [];
  subscribe(consumer: Consumer): void {
    this.consumers.push(consumer);
  }
  publish(msg: Message): void {
    for (const consumer of this.consumers) {
      consumer(msg);
    }
  }
}

function wireTap(
  source: Channel,
  tapConsumer: Consumer,
  selector: (msg: Message) => boolean = () => true
): void {
  source.subscribe((msg) => {
    if (!selector(msg)) {
      return;
    }
    const snapshot: Message = { ...msg };
    setTimeout(() => tapConsumer(snapshot), 0);
  });
}

const primary = new Channel();
const auditLog: Message[] = [];

primary.subscribe((msg) => {
  console.log(`primary consumer handled #${msg.id}: ${msg.payload}`);
});

wireTap(
  primary,
  (msg) => {
    auditLog.push(msg);
  },
  (msg) => msg.payload.startsWith("order")
);

primary.publish({ id: 1, payload: "order:created" });
primary.publish({ id: 2, payload: "heartbeat" });

setTimeout(() => {
  console.log("audit log size:", auditLog.length);
}, 0);
```

Compiled with `tsc --target ES2020 --lib ES2020,DOM --strict` and run with
`node`. Output confirms both messages reach the primary consumer while only
the message whose payload starts with `order` reaches the tap.

### Python

```python
import copy
import queue
import threading
from dataclasses import dataclass, field
from typing import Callable, List


@dataclass
class Message:
    id: int
    payload: dict = field(default_factory=dict)


class Channel:
    def __init__(self) -> None:
        self._consumers: List[Callable[[Message], None]] = []

    def subscribe(self, consumer: Callable[[Message], None]) -> None:
        self._consumers.append(consumer)

    def publish(self, msg: Message) -> None:
        for consumer in self._consumers:
            consumer(msg)


def wire_tap(source: Channel, tap_queue: "queue.Queue", selector=lambda m: True) -> None:
    def on_message(msg: Message) -> None:
        if selector(msg):
            tap_queue.put(copy.deepcopy(msg))
    source.subscribe(on_message)


def tap_consumer(tap_queue: "queue.Queue", sink: List[Message]) -> None:
    while True:
        msg = tap_queue.get()
        if msg is None:
            tap_queue.task_done()
            break
        sink.append(msg)
        tap_queue.task_done()


def main() -> None:
    primary = Channel()
    audit_sink: List[Message] = []
    tap_queue: "queue.Queue" = queue.Queue()

    primary.subscribe(lambda msg: print(f"primary consumer handled #{msg.id}: {msg.payload}"))
    wire_tap(primary, tap_queue, selector=lambda m: m.payload.get("type") == "order")

    worker = threading.Thread(target=tap_consumer, args=(tap_queue, audit_sink), daemon=True)
    worker.start()

    primary.publish(Message(id=1, payload={"type": "order", "amount": 42}))
    primary.publish(Message(id=2, payload={"type": "heartbeat"}))

    tap_queue.join()
    tap_queue.put(None)
    worker.join()

    print("audit sink size:", len(audit_sink))


if __name__ == "__main__":
    main()
```

Run with `python3`. The tap consumer runs on its own thread, backed by a
`queue.Queue`, and receives a `copy.deepcopy` of the message rather than the
same object the primary consumer received, closing the shared-mutable-state
failure mode from dimension 11.

### Go

```go
package main

import (
	"fmt"
	"strings"
	"sync"
)

type Message struct {
	ID      int
	Payload string
}

type Channel struct {
	consumers []func(Message)
}

func (c *Channel) Subscribe(consumer func(Message)) {
	c.consumers = append(c.consumers, consumer)
}

func (c *Channel) Publish(msg Message) {
	for _, consumer := range c.consumers {
		consumer(msg)
	}
}

func WireTap(source *Channel, tap chan<- Message, selector func(Message) bool) {
	source.Subscribe(func(msg Message) {
		if !selector(msg) {
			return
		}
		select {
		case tap <- msg:
		default:
			// The tap consumer is behind. Drop rather than block the primary path.
		}
	})
}

func main() {
	primary := &Channel{}
	tapChan := make(chan Message, 16)
	var auditLog []Message
	var wg sync.WaitGroup

	primary.Subscribe(func(msg Message) {
		fmt.Printf("primary consumer handled #%d: %s\n", msg.ID, msg.Payload)
	})

	WireTap(primary, tapChan, func(msg Message) bool {
		return strings.HasPrefix(msg.Payload, "order")
	})

	wg.Add(1)
	go func() {
		defer wg.Done()
		for msg := range tapChan {
			auditLog = append(auditLog, msg)
		}
	}()

	primary.Publish(Message{ID: 1, Payload: "order:created"})
	primary.Publish(Message{ID: 2, Payload: "heartbeat"})
	close(tapChan)
	wg.Wait()

	fmt.Println("audit log size:", len(auditLog))
}
```

Run with `go run`. The buffered channel plus the `select` with a `default`
case is the idiomatic Go shape for the isolation-against-latency force from
dimension 3. a full tap channel drops the tapped message rather than blocking
the goroutine that is about to call the primary consumer.

Java, Rust, and Swift are omitted here for space. the shape in each is a
straightforward translation of the Go or TypeScript version, an interface or
protocol for the channel abstraction, a bounded queue or channel for the tap,
and the same selector-then-copy-then-forward sequence.
