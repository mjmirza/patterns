---
name: Dynamic Router
slug: dynamic-router
family: 07-integration
category: Integration
aliases: [Self-Configuring Router, Iterative Router, Recipient-Registering Router]
first_described: "Hohpe, Woolf 2003"
maturity: canonical
related: [content-based-router, routing-slip, recipient-list, publish-subscribe-channel, service-locator, circuit-breaker]
incompatible_with: []
verified: 2026-08-02
---

# Dynamic Router

## 1. Name, aliases, and lineage

The canonical name is Dynamic Router. It is described in Gregor Hohpe and Bobby
Woolf, *Enterprise Integration Patterns. Designing, Building, and Deploying
Messaging Solutions*, Addison-Wesley, 2003, in the Message Router chapter of the
patterns catalog. The book's own companion site states the problem the pattern
answers as how to avoid the dependency of the router on all possible
destinations while maintaining its efficiency, and gives the solution as a
Router that can self-configure based on special configuration messages from
participating destinations (Gregor Hohpe and Bobby Woolf,
[Dynamic Router](https://www.enterpriseintegrationpatterns.com/patterns/messaging/DynamicRouter.html),
verified 2026-08-02). In that original telling, destinations announce
themselves over a control channel, tell the router what conditions they can
handle, and the router builds its rule base from those announcements rather
than from a hardcoded list a developer maintains.

That is the book's meaning, and it is worth stating plainly because the name has
drifted since 2003 and now covers two genuinely different mechanisms in
practice, both defensible, and a reader who only knows one will misread code
that implements the other.

- **Self-configuring router, the 2003 book sense.** The router is a passive
  rule store. Destinations push their own routing preferences into it at
  startup or on change, over a dedicated control channel, and the router
  matches incoming messages against that accumulated rule set. The router
  never asks a destination anything at message-routing time. It only asks once,
  at registration time, and then routes from memory.
- **Iteratively evaluated router, the integration-framework sense.** The
  router calls an expression, a bean, or a function once per hop, and that
  call returns the next destination or `null` to stop. Apache Camel's own
  reference documentation for its `dynamicRouter` EIP states the expression is
  called iteratively until it returns null to indicate the end of routing, and
  that expressions must guarantee a null return to avoid an infinite loop
  (Apache Software Foundation,
  [Dynamic Router EIP](https://camel.apache.org/components/latest/eips/dynamicRouter-eip.html),
  verified 2026-08-02). This shape is closer to a routing slip that is
  computed on demand, one hop at a time, rather than a slip attached to the
  message up front. Spring Integration ships the same idea under the identical
  name, listing Dynamic Routers as a distinct topic in its router
  documentation, separate from its static Header Value Router and Payload
  Type Router (VMware Tanzu,
  [Router documentation index](https://docs.spring.io/spring-integration/reference/router.html),
  verified 2026-08-02).

Both mechanisms share the property the name promises, that the set of possible
destinations is not compiled into the router. Both differ from a plain
Content-Based Router, whose destination logic is fixed code shipped with the
router and only the message data varies. This entry covers both senses,
because production code answering to the name Dynamic Router is built both
ways, and treats the difference as the load-bearing fact a reader needs before
touching either implementation.

A separate but related usage exists in cloud infrastructure. control-plane
systems that push routing configuration to a data-plane proxy at runtime,
without restarting it. Envoy's Route Discovery Service is the clearest named
instance of this, and it is covered in dimension 9 as a third variant, because
it satisfies the same forces, avoiding coupling the router to a fixed
destination list while keeping routing current without a redeploy, through yet
a third mechanism, a push-based control plane rather than a pull-based
expression or a registration channel.

## 2. Problem and context

A message-routing component in a system needs to send a message onward, and the
set of places it might send that message to is not fixed at the time the
router is built, deployed, or even started. Three concrete situations produce
this problem.

The first is a growing plugin or partner ecosystem. A payment gateway starts
with three downstream processors. A year later it has eleven, added by
different teams on different schedules, and a Content-Based Router with an
`if` chain naming all eleven means every new processor requires editing and
redeploying the router itself, the one component every processor depends on
staying stable.

The second is a workflow whose next step depends on the outcome of the current
step, not on a value known when the message was created. A document approval
process might need zero, one, or three more approvers depending on what the
first approver decides, or on a dollar threshold discovered mid-flow. A static
Routing Slip written before the message enters the pipeline cannot express
that the third hop should be decided after seeing the result of the second
hop. Something has to be consulted again at each step.

The third is infrastructure whose destination set changes constantly and
independently of the code that owns routing, such as autoscaled service
instances, canary and blue-green deployments where the split percentage moves
hourly, or a service mesh where every sidecar proxy needs the current set of
upstream endpoints without a binary restart.

The pattern applies to any of these when the destination set changes on a
timescale shorter than a deployment, and where hardcoding every branch inside
the router itself would make the router the bottleneck for every future change
to what it routes toward.

## 3. Forces

- **Coupling.** Favoured. The router's compiled code depends on an expression,
  a lookup interface, or a control-plane API, never on the concrete set of
  destinations.
- **Freshness versus efficiency.** This is the pattern's own stated trade in
  the EIP book, and it is the central tension. Re-evaluating routing rules
  cheaply, on every message, against a store that is itself cheap to update,
  is exactly what the pattern buys. Getting that balance wrong in either
  direction breaks the pattern. caching too aggressively serves stale routes,
  and re-deriving the full rule set on every message defeats the efficiency
  half of the book's own problem statement.
- **Operability.** Sacrificed by default, recoverable with discipline. Because
  the destination set is not in source control, a production incident caused
  by a bad registration or a bad expression evaluation is invisible to a code
  reviewer. It only shows up in a route history log, which the pattern must
  therefore be built to keep.
- **Consistency during rollout.** Sacrificed. Because registration or route
  push happens over a live channel rather than through a deployment, there is
  a window where different router instances, or the same router instance at
  different points in time, can hold different rule sets. A message routed
  one way and a different way a second later is not a bug in a dynamic
  router, it is the router doing its job, and every consumer of its output
  must be built to tolerate that.
- **Latency.** Mildly sacrificed for the expression-based variant, since an
  extra function call or lookup happens per hop rather than per message.
  Close to neutral for the control-plane-push variant, since the proxy holds
  the current route table in memory and consults it exactly as fast as a
  static one, the cost is paid asynchronously on the control plane's own
  update path rather than on the message's hot path.
- **Trust.** Sacrificed in the self-registering variant specifically. The
  router now accepts routing instructions from the very components it is
  meant to be routing to, which inverts the usual direction of authority and
  opens the registration channel as an attack surface, covered fully in
  dimension 17.
- **Team topology.** Favoured. A destination team can add, remove, or change
  its own routing eligibility without a change request against the team that
  owns the router.

## 4. Applicability and non-applicability

Reach for a Dynamic Router when the following hold.

- The set of destinations changes on a timescale shorter than the router's own
  deployment cycle, so hardcoding it would make routine additions require a
  router redeploy.
- The next hop genuinely cannot be known until the current hop's result is in
  hand, so a routing decision precomputed before the message enters the
  pipeline, a static Routing Slip or a fixed Recipient List, cannot express it.
- Destinations are numerous, added by independent teams, or come and go with
  infrastructure lifecycle such as autoscaling or plugin install and
  uninstall, so a central Content-Based Router would become a shared
  bottleneck for unrelated teams' changes.
- The system already has, or can afford to build, a reliable channel for
  destinations or an operator to communicate current routing state to the
  router, whether that is a registration protocol, a config store, or a
  control-plane push API.

Do NOT reach for a Dynamic Router in these cases, and the reason is the point.

- **The destination set is genuinely fixed and small.** Three payment
  processors that were integrated once, five years ago, and have never
  changed since, do not need a self-configuring rule base. A Content-Based
  Router with three named branches is simpler to read, simpler to test, and
  has no registration channel to secure. Dynamic Router here is speculative
  flexibility paid for daily in indirection.
- **The routing decision is knowable at message-creation time and does not
  depend on downstream results.** That is a Routing Slip, computed once,
  attached to the message, and cheaper to trace because the whole path is
  visible by reading the message header rather than by replaying evaluation
  logic.
- **The system cannot tolerate routing decisions that differ between two
  messages sent one second apart.** Financial settlement batches and
  anything requiring bit-for-bit reproducible routing across a reprocessing
  run are the wrong home for a router whose rules can change mid-run. Pin the
  rule set for the batch, or use a versioned, immutable Routing Table instead.
- **There is no trustworthy channel for destinations to announce themselves,
  and building one is not worth it for this system's actual rate of change.**
  A self-registering router with no authentication on its registration
  channel is worse than a static one, because a hostile or buggy participant
  can redirect traffic meant for someone else. Build the trust boundary
  first, or do not build this pattern yet.
- **A simpler pattern already solves the actual problem.** If every message
  should go to every current subscriber, that is Publish-Subscribe Channel,
  not routing. If the next step is really running a fixed pipeline of
  filters, that is a Pipes and Filters composition, not a router evaluated
  per hop.

## 5. Structure

Two structural shapes correspond to the two mechanisms named in dimension 1.
Both share a Router participant and Destinations, and differ in how the
routing knowledge reaches the Router.

Self-registering shape.

- **Router.** Holds a mutable rule base keyed by matchable conditions. Exposes
  a routing operation consumed by every incoming message, and a registration
  operation consumed only by destinations.
- **Destination.** A message consumer that, at startup or on a capability
  change, sends a registration message over the control channel describing
  what it can handle.
- **Control Channel.** A separate channel from the data channel, carrying only
  registration and deregistration traffic. Its integrity is the pattern's
  central risk, covered in dimension 17.
- **Rule Base.** The Router's internal store, indexed for fast match at
  message time. Not itself a separate deployable, but worth naming because
  its persistence, staleness policy, and eviction rules are the part that
  fails in production.

Iteratively evaluated shape.

- **Router.** Holds no rule base of its own. On each message, it invokes a
  Routing Function once per hop and forwards the message to whatever
  destination that function returns.
- **Routing Function.** A method, bean, lambda, or external call that,
  given the message and its accumulated routing history, returns the next
  destination or a sentinel meaning stop. This is the seam the whole
  pattern turns on. it may consult a database, a feature flag service, or
  pure in-memory state, and the router does not care which.
- **Routing History.** State carried alongside the message, or held by the
  router keyed by message identity, recording which hops have already been
  taken, so the Routing Function can make the next decision and so an
  operator can reconstruct the actual path afterward.
- **Destination.** A message consumer with no special obligation toward the
  router, unlike the self-registering shape where destinations must speak the
  registration protocol.

## 6. ASCII structure diagram

```
Self-registering shape

  +--------------+  register(conditions)   +-----------------+
  | Destination A|------------------------>|                  |
  +--------------+                         |                  |
                                            |     Router       |
  +--------------+  register(conditions)   |  (rule base held |
  | Destination B|------------------------>|   in memory)     |
  +--------------+                         |                  |
                                            +---------+--------+
                    message                          |
  Producer -------------------------------------------> match against rule base
                                            +---------+--------+
                                                       |
                                        route to A, B, or neither
                                                       v
                                    +--------------+       +--------------+
                                    | Destination A|       | Destination B|
                                    +--------------+       +--------------+


Iteratively evaluated shape

  Producer --> message --> +------------------+
                            |     Router       |
                            +------------------+
                                     |
                                     |  call routingFunction(msg, history)
                                     v
                            +------------------+
                            | Routing Function |----> returns Destination 1
                            +------------------+
                                     |
                             forward to Destination 1, append to history
                                     |
                                     v
                            +------------------+
                            |     Router       |  (message returns for hop 2)
                            +------------------+
                                     |
                                     |  call routingFunction(msg, history)
                                     v
                            +------------------+
                            | Routing Function |----> returns null
                            +------------------+
                                     |
                                     v
                              routing complete
```

## 7. Dynamics

Self-registering shape. Registration and routing are two independent flows
that share only the rule base as state.

```
Destination A       Router (rule base)        Destination B       Producer
     |                     |                        |                 |
     |-- register(cond) -->|                        |                 |
     |                     |-- stores rule A ------->|                 |
     |                     |                        |                 |
     |                     |<-- register(cond) -----|                 |
     |                     |-- stores rule B         |                 |
     |                     |                        |                 |
     |                     |<------------------------------------- message
     |                     |-- match against rule base                |
     |                     |-- (matches rule A only)                  |
     |<-- forward message -|                        |                 |
     |                     |                        |                 |
```

Iteratively evaluated shape. One message, three hops, then completion.

```
Producer          Router              RoutingFunction         Dest1   Dest2   Dest3
   |                |                        |                  |       |       |
   |-- message ---->|                        |                  |       |       |
   |                |-- eval(msg, []) ------>|                  |       |       |
   |                |<-- Dest1 --------------|                  |       |       |
   |                |-- forward ------------------------------->|       |       |
   |                |                        |                  |-------|       |
   |                |<-- msg returns for next hop, history=[1] -|       |       |
   |                |-- eval(msg, [1]) ----->|                  |       |       |
   |                |<-- Dest2 --------------|                  |       |       |
   |                |-- forward --------------------------------------->|       |
   |                |<-- msg returns, history=[1,2] -------------------|       |
   |                |-- eval(msg, [1,2]) --->|                  |       |       |
   |                |<-- Dest3 --------------|                  |       |       |
   |                |-- forward ---------------------------------------------->|
   |                |<-- msg returns, history=[1,2,3] ------------------------|
   |                |-- eval(msg, [1,2,3]) ->|                  |       |       |
   |                |<-- null ---------------|                  |       |       |
   |-- routing complete, history=[1,2,3] returned to caller ----|       |       |
```

The eval-and-loop shape has a real termination risk that the self-registering
shape does not. Camel's own documentation warns explicitly that the
expression must be written to guarantee a null return, because an expression
that always returns a destination routes forever (Apache Software Foundation,
[Dynamic Router EIP](https://camel.apache.org/components/latest/eips/dynamicRouter-eip.html),
verified 2026-08-02). A hop counter with a hard ceiling, checked by the router
rather than trusted to the function, is the practical mitigation, covered in
dimension 11.

## 8. Implementation variants

**Registration over a message channel, the book's own shape.** Destinations
publish a small announcement message to a well-known control topic on
startup and on any capability change, and unpublish, or send a
time-to-live-bearing heartbeat, on shutdown. The router subscribes to that
topic and maintains its rule base in memory, rebuilt from a durable log on
restart so a router crash does not silently forget every registered
destination.

**Registration over a synchronous API.** Instead of a message channel,
destinations call a `register(pattern, endpoint)` RPC on the router directly.
Simpler to reason about for a small number of long-lived destinations, weaker
under partition because a destination that cannot reach the router at startup
never gets a chance to retry via replay the way a durable topic allows.

**Iterative expression, evaluated per hop, in-process.** The shape Camel and
Spring Integration both ship under the Dynamic Router name. The routing
function lives in the same process as the router and is typically a plain
method, a Spring bean, or a lambda, making it cheap to call and easy to unit
test in isolation from the messaging infrastructure.

**Iterative expression backed by an external decision service.** The same
per-hop-evaluation shape, but the function call is a network call to a rules
engine, a feature-flag service, or a workflow orchestrator. This trades
in-process simplicity for centralised, auditable, hot-updatable decision
logic, at the cost of a network round trip on every hop and a new failure
mode, the routing decision itself becoming unavailable.

**Routing table pulled from a config store.** Neither destinations nor a
per-hop function decide. Instead the router periodically polls, or is pushed
to by, an external config store such as etcd, Consul, a database table, or a
feature flag platform, holding the current rule set. This decouples the
router from both the message flow and any single destination's
availability, and is the shape most operations teams choose when they want a
human-editable rule set rather than one destinations edit themselves.

**Control-plane push to many router instances, xDS style.** A dedicated
control plane computes the desired routing configuration and pushes it to
every data-plane router instance over a streaming API, without those router
instances ever restarting. Envoy's Route Discovery Service is the named
reference implementation of this shape, and it is covered as a production
use in dimension 9 rather than repeated here, because the mechanism, push
rather than pull, and to many router replicas at once rather than one, is
different enough from the three variants above to be its own category rather
than a detail of them.

**Language note.** None of these variants require inheritance or a class
hierarchy. In every language with first-class functions, the routing
function variant is naturally a value, a closure, or an interface with one
method, never a subclass hierarchy the way a naive port of the GoF-era
pattern catalog might suggest. Go, TypeScript, and Python all express the
iterative-expression variant as a function value held by the router, shown
below under Code examples.

## 9. Known production uses

**Apache Camel's `dynamicRouter` EIP.** Camel implements the iterative
expression variant directly as a first-class DSL construct,
`.dynamicRouter(method(SlipBean.class, "slip"))`, where the named method is
called once per hop and must return `null` to terminate routing. The
reference documentation states this explicitly and warns that a state that
must persist across calls should be stored on the message Exchange rather
than in a Camel route's instance field, because a route definition is shared
across concurrent in-flight exchanges (Apache Software Foundation,
[Dynamic Router EIP](https://camel.apache.org/components/latest/eips/dynamicRouter-eip.html),
verified 2026-08-02).

**Spring Integration's Dynamic Router.** Spring Integration ships a router
family that includes a distinct Dynamic Router alongside its static Header
Value Router and Payload Type Router, documented as a separate topic in the
framework's routing reference (VMware Tanzu,
[Spring Integration Router documentation index](https://docs.spring.io/spring-integration/reference/router.html),
verified 2026-08-02), confirming the pattern is a named, first-class citizen
of a widely used enterprise integration framework and not merely a technique
described in the 2003 book.

**Envoy's Route Discovery Service, RDS, as consumed by Istio.** Envoy's own
architecture documentation describes RDS as the mechanism by which Envoy can
discover the entire route configuration for an HTTP connection manager
filter at runtime, with the route table gracefully swapped in without
affecting existing requests (verified live 2026-08-02 against Envoy's
dynamic configuration overview). Istio's control plane, istiod, is a named
production consumer of this mechanism at scale. Istio's own architecture
documentation states that istiod converts high level routing rules that
control traffic behavior into Envoy-specific configurations, and propagates
them to the sidecars at runtime (Istio project,
[Istio architecture, deployment model](https://istio.io/latest/docs/ops/deployment/architecture/),
verified 2026-08-02). Every Envoy sidecar in an Istio mesh is a Dynamic
Router in the control-plane-push sense of dimension 8. its destination set,
the current set of healthy service endpoints and the current traffic-split
percentages for a canary rollout, changes continuously without any Envoy
process ever being restarted.

**Enterprise Service Bus rule-base routers, the book's own named context.**
The 2003 book itself frames the pattern as the answer used by message
brokers and enterprise service buses that must route to a destination set
maintained by the destinations themselves rather than by the bus operator,
and gives the self-registering shape as the canonical realisation of that
context (Gregor Hohpe and Bobby Woolf,
[Dynamic Router](https://www.enterpriseintegrationpatterns.com/patterns/messaging/DynamicRouter.html),
verified 2026-08-02). This is listed as a fourth, distinct production
lineage because it predates, and is architecturally different from, both the
Camel and Spring in-process expression variant and the Envoy and Istio
control-plane variant, even though all three answer to the same pattern
name.

## 10. Consequences

Positive.

- New destinations are added, and old ones retired, without a change to the
  router's own deployed code, which keeps the router stable while everything
  around it changes.
- Routing decisions can depend on information only available mid-flow, the
  result of hop one, which a precomputed Routing Slip or Recipient List
  cannot express.
- In the control-plane-push variant, thousands of proxy instances stay
  routing-correct without a coordinated restart, which is the property that
  makes canary and blue-green traffic shifting operationally viable at scale.
- The routing logic for who is currently eligible moves out of a single
  team's codebase and closer to the party who actually knows the answer,
  whether that is the destination itself or an operator editing a config
  store.

Negative.

- The routing decision is no longer visible by reading the source code of the
  router. It requires reading the current rule base, the current
  registration log, or a captured routing-history trace, which means a
  routing bug review always starts by asking what the rule base contained
  at the time rather than what the code says.
- Registration or control-plane channels are new infrastructure the router
  did not need before, and every one of them is a new thing that can be down,
  slow, poisoned, or replayed maliciously, covered fully in dimension 17.
- Two messages processed a second apart can legitimately take different
  paths, which breaks any assumption of deterministic reprocessing and
  complicates root-cause analysis of an incident that only happened for a
  few minutes.
- The iterative-expression variant risks infinite routing loops if the
  expression's termination condition is wrong, a failure mode a static
  Routing Slip structurally cannot have, because a slip has a fixed, finite
  list to begin with.
- Testing requires either a live rule base, a fake control channel, or a
  scripted sequence of Routing Function return values, which is more setup
  than testing a Content-Based Router's fixed `if` branches.

## 11. Failure modes and misuse

**The expression that never returns null.** Symptom. A single message drives
the router into a hot loop, CPU on the routing worker pins at 100 percent,
and the message's routing-history list grows without bound until the process
runs out of memory. Cause. The Routing Function has a code path with no
termination case, often introduced when a new hop type is added and the
else-return-null branch is forgotten. Fix. The router itself enforces a
hard hop ceiling independent of the expression, and any message that hits
the ceiling is dead-lettered with its full routing history attached rather
than silently dropped or silently continued.

**Stale rule base after a destination crash.** Symptom. Messages continue
being routed to a destination that has been down for twenty minutes, and
those messages are lost or endlessly retried, discovered only when a
downstream SLA alert fires. Cause. A self-registering router with no
deregistration path and no heartbeat expiry, so once registered, always
registered. Fix. Registrations carry a time-to-live and destinations must
re-announce periodically, or the control channel carries an explicit
deregistration on graceful shutdown paired with a liveness probe the router
runs itself for the ungraceful case.

**Unbounded rule base growth.** Symptom. Router memory climbs steadily over
weeks with no corresponding growth in actual traffic, eventually forcing a
restart. Cause. Ephemeral destinations, workers spun up per job and torn
down, register and are never explicitly removed, only expiring on a
heartbeat timeout set too generously or not enforced at all. Fix. A bounded
rule base with active eviction, and a metric on rule-base size specifically
so this trend is visible before it becomes an incident, see dimension 16.

**Split-brain rule bases across router replicas.** Symptom. The same message
type routes to destination A from one router instance and destination B
from another, and support tickets describe intermittent, unreproducible
behaviour. Cause. Multiple router replicas each hold an independently built
rule base, and registration messages are not reliably delivered to every
replica, often because the control channel is a point-to-point queue rather
than a broadcast topic. Fix. Registration must go over a fan-out channel
every replica consumes, or the rule base must live in a shared, consistent
store all replicas read from rather than in each replica's own memory.

**Confused for a Service Locator, and blamed for its problems.** Symptom. A
code reviewer flags hidden dependency and hard to trace against a
Dynamic Router used correctly for its stated purpose. Cause. Genuine
overlap, since both patterns resolve where a request should go outside the
calling code. The distinguishing fact, worth stating so the review lands
correctly, is that a Dynamic Router routes a message that is already in
flight and whose destination changes per message, while a Service Locator
resolves a single dependency reference once per lookup, usually for a
caller's own use, not for forwarding a message onward. Fix. Not a code fix,
a naming and review-culture fix. cite the distinction explicitly in the
pattern's own documentation comment so future reviewers do not re-litigate
it.

**Trusting a destination's self-reported routing conditions unchecked.**
Symptom. One destination silently receives traffic meant for another,
discovered by a customer complaint rather than by monitoring. Cause. The
registration channel accepted an announcement claiming a routing condition
the destination had no authority to claim, most often a wildcard or an
overly broad match pattern. Fix. Validate registered patterns against an
allowlist scoped to what that destination's credentials permit, covered
fully in dimension 17.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Dynamic Router | Content-Based Router | Routing Slip | Recipient List | Envoy-style control-plane push |
|---|---|---|---|---|---|
| Coupling to destination set | None. Destinations register or are looked up | High. Destinations named in router code | None at route time. Full path precomputed | Medium. Recipients resolved per message but usually from a known scheme | None. Data plane has no destination knowledge, control plane owns it |
| Adapts mid-flow to a prior hop's result | Yes, that is its purpose in the iterative variant | No, decides once against message content | No, path is fixed before the first hop | No, list is resolved once, typically up front | Not applicable, this variant routes single hops, not multi-hop pipelines |
| New destination added without router code change | Yes | No, requires an edit | No, requires an edit to slip-generation logic | Often, if resolved from a directory | Yes, via control-plane config, no data-plane redeploy |
| Determinism, same input always same route | No, by design | Yes | Yes, path is fixed at creation | Depends on the recipient resolution source | No, by design, that is the point |
| Auditability from source code alone | Poor, must inspect live state | Good, branches are in the diff | Good, path is visible on the message | Fair | Poor, must inspect the control plane's current config |
| Infinite-loop risk | Real, in the iterative variant, mitigated by a hop ceiling | None | None | None | None |
| Operational cost of the extra channel | New registration or control-plane infrastructure required | None | None | None, usually reuses an existing directory | Substantial, a full control plane such as istiod or an xDS server |
| Best fit | Growing or infrastructure-driven destination sets, per-hop decisions | Small, stable, content-driven branching | Known multi-step path decided up front | Broadcast-like fan-out to a resolved group | Many proxy replicas needing coordinated, hot-updatable routing |

Reading of the table. Dynamic Router wins wherever the set of possible
destinations is itself a moving target, whether that movement comes from
business logic, such as a new partner integrating, or from infrastructure,
such as an autoscaler adding a pod. Content-Based Router wins when the
destination set is small and stable and the only thing that varies is the
message. Routing Slip wins when the whole path is knowable before the first
hop. Recipient List wins for fan-out. the control-plane-push shape wins
specifically at the scale of many proxy replicas that must stay coordinated
without individual redeploys, a scale where a per-instance registration
channel would itself become the bottleneck.

## 13. Related and incompatible patterns

- **Content-Based Router.** The nearest sibling and the one most often
  confused with it. Content-Based Router branches on message content with
  logic written into the router. Dynamic Router branches on a destination set
  that is not written into the router. A Content-Based Router that grows a
  new `else if` for every new destination is the exact pressure that should
  push a team toward Dynamic Router instead.
- **Routing Slip.** Complementary at different points in the message
  lifecycle. A Routing Slip decides the whole path once, before the message
  starts moving. The iterative variant of Dynamic Router decides one hop at a
  time, as the message moves. Camel's own `dynamicRouter` implementation is,
  by the framework's own documentation, closer in mechanism to an
  on-demand-computed routing slip than to the book's self-registering
  router, which is exactly the terminology overlap flagged in dimension 1.
- **Recipient List.** Solves fan-out, a message to several destinations at
  once, computed from a resolved list. Dynamic Router solves fan-in of
  routing knowledge, one destination chosen from a set the router does not
  own. The two compose when a Dynamic Router's per-hop decision is itself
  send to all currently registered destinations of this type, making that
  one hop a Recipient List.
- **Publish-Subscribe Channel.** A cheaper answer when the real requirement is
  that every current subscriber gets this message, with no per-message
  routing decision at all. If a Dynamic Router's rule base always resolves
  to every registered destination, the router is a Publish-Subscribe Channel
  wearing extra machinery and should be simplified.
- **Service Locator.** Conceptually adjacent, structurally different, and
  worth distinguishing explicitly per dimension 11. both decouple a caller
  from a concrete destination, but a Service Locator resolves one dependency
  for the caller's own use, while a Dynamic Router forwards an in-flight
  message on the caller's behalf, potentially through several hops.
- **Circuit Breaker.** Composes cleanly and should be paired in production.
  A Dynamic Router that keeps routing to a destination that is failing
  every call is worse than a static router with the same problem, because
  the dynamic router had the information, a registration or a config entry,
  to have removed that destination and did not. Wrapping each destination
  call, or gating registration renewal, with a circuit breaker closes that
  gap.
- **Wire Tap.** Composes for observability. A Wire Tap placed on the router's
  outbound side, recording every actual routing decision, is the practical
  answer to dimension 10's no-longer-visible-from-source weakness, and is
  close to mandatory in production, covered in dimension 16.

## 14. Refactoring path in and out

Introducing the pattern into a Content-Based Router that has outgrown its
fixed branches.

1. Identify the branch condition that keeps growing, most often a switch or
   `if` chain keyed on a destination identifier that a business or
   infrastructure team keeps asking to extend.
2. Extract the branch's condition-to-destination mapping into an external,
   readable store, a table, a config file, or an in-memory map populated at
   startup, while keeping the router's routing logic itself unchanged. This
   step alone, with no registration channel yet, already removes the
   redeploy-per-destination cost and is often sufficient. stop here if it is.
3. If destinations must add themselves without operator involvement, add a
   registration operation, a message channel or an API endpoint, that writes
   into the same store from step 2, so the router's read path does not
   change again.
4. Add a heartbeat or explicit deregistration to the registration protocol
   from the start. do not defer this, the stale-rule-base failure mode in
   dimension 11 is the single most common reason a self-registering router
   causes an incident, and it is far cheaper to build in at introduction than
   to retrofit under production pressure.
5. If the requirement is deciding the next hop based on what just happened
   rather than looking up who can handle this kind of message, the target
   shape is the iterative variant, not the self-registering one. Extract the
   per-hop decision into a single function taking the message and its
   routing history, and replace the fixed pipeline call sequence with a loop
   calling that function until it returns the termination sentinel. Add the
   hop ceiling from dimension 11 in the same change, never after.
6. Add the routing-history recording from dimension 16 before this ships to
   production. A Dynamic Router with no route audit trail is materially
   harder to operate than the Content-Based Router it replaced.

Removing the pattern when the destination set has settled and stopped
changing, or when its indirection cost is no longer paying for itself.

1. Confirm the rule base or registration log has been stable, no additions
   or removals, for a meaningful period, long enough to be confident the
   settling is real and not a lull.
2. Snapshot the current rule base as of that stable point and turn it into
   an explicit, reviewed list, the same shape a Content-Based Router or a
   fixed Routing Table would hold.
3. Replace the router's lookup against the live rule base with the frozen
   list, keeping the same routing decision it was already making.
4. Retire the registration channel or control-plane feed once nothing reads
   from it, and delete the heartbeat and eviction logic that existed only to
   keep that channel healthy.
5. If the iterative variant is being retired, replace the loop with a
   Routing Slip computed once at message creation, since the earlier
   justification for per-hop evaluation, that the next hop could not be
   known up front, no longer holds once the destination set and its
   selection logic have stabilised.

## 15. Testing and verification

Easier because of the pattern.

- The Routing Function in the iterative variant is, in every implementation
  variant shown in dimension 8, a plain function taking a message and
  returning a destination or a termination value. It can be unit tested with
  no messaging infrastructure at all, feeding it a sequence of fake
  histories and asserting the sequence of destinations it returns.
- A self-registering router's rule base can be populated directly in a test,
  bypassing the registration channel entirely, to test routing logic in
  isolation from registration transport concerns.
- Because the destination set is external state rather than compiled logic,
  adding a test case for routing correctly when one destination is
  registered and another is not requires no code change to the router, only
  a different fixture.

Harder because of the pattern.

- End-to-end tests that exercise the actual registration channel, or the
  actual control-plane push mechanism, need that infrastructure running, and
  a flaky or slow control channel in a test environment produces flaky
  routing tests that have nothing to do with routing correctness.
- Non-determinism is intrinsic. two runs of the same integration test suite
  can legitimately route differently if timing causes a registration to land
  before or after the first test message, so tests must either pin the rule
  base explicitly for the duration of the test or accept and assert against
  a set of valid outcomes rather than a single expected one.
- The infinite-loop failure mode from dimension 11 needs its own dedicated
  test, an expression deliberately crafted to never terminate, asserting the
  router's hop ceiling catches it rather than trusting the expression's own
  correctness, because that correctness is exactly what will eventually fail
  in production.

Techniques that apply.

- **Table-driven tests of the Routing Function**, one row per message and
  history pair and its expected next destination or termination, which
  scales cleanly as hop logic grows and reads as living documentation of the
  routing rules.
- **A test double control channel** that lets a test publish a synthetic
  registration and assert the router's rule base updated, without a real
  message broker.
- **Snapshot testing of the routing-history trace** for a representative
  message, catching accidental changes to hop ordering or termination
  behaviour that a narrower unit test on the function alone might miss.
- **Fault-injection testing of registration loss.** deliberately drop a heartbeat or
  deregistration event in a test environment and assert the router's
  eviction policy removes the stale destination within its stated bound,
  directly testing the fix for the stale-rule-base failure mode.

## 16. Observability signals

Because dimension 10 identifies no-longer-visible-from-source as the
pattern's central weakness, observability is not optional polish for a
Dynamic Router, it is the mechanism that makes the pattern operable at all.

What to record.

- Every routing decision, logged or traced with the message identity, the
  destination chosen, the rule or registration entry that matched, and, in
  the iterative variant, the current hop count. This is the single most
  important signal, it is what a Wire Tap on the router's outbound side
  should capture, per dimension 13.
- Every registration and deregistration event, with the destination
  identity, the conditions it claims, and the source of the request,
  because this log is the only record of why the rule base looks the way it
  does at any point in time, and is the primary artefact for investigating
  the split-brain and stale-rule-base failure modes.
- A gauge of current rule base size or current registered-destination count,
  which is the earliest warning for the unbounded rule base growth failure
  mode, since a monotonically climbing gauge with no corresponding
  deregistration events is visible on a dashboard long before it becomes an
  incident.
- A counter of hop-ceiling breaches in the iterative variant, labelled by
  the expression or bean that produced the runaway sequence, so the
  infinite-loop failure mode is caught by an alert rather than by an
  out-of-memory crash.
- A histogram of Routing Function evaluation latency, per destination or per
  rule, essential for the external-decision-service variant of dimension 8
  where that call crosses a network.

A healthy instance on a dashboard. Rule base size tracks the actual expected
population of destinations and moves only on deployments or scaling events
that explain it. Registration and deregistration events roughly balance over
any sustained window. hop-ceiling breaches sit at zero. routing-decision
latency is flat and small relative to the surrounding pipeline.

A failing instance. Rule base size climbs with no matching deregistration
trend, the unbounded growth failure mode in progress. A specific destination
identity appears in the routing log that nobody on the current team
recognises, which is the first observable sign of the trust failure mode
covered in dimension 17. hop-ceiling breach count moves off zero, meaning a
routing expression has, or is about to, run away. registration events cluster
suspiciously around a single source identity claiming many distinct
destination conditions, worth investigating as a possible registration
channel compromise before assuming it is legitimate.

## 17. Security and privacy implications

Unlike Factory Method, this pattern is not close to silent on security. The
self-registering variant, specifically, inverts the normal trust direction
between a router and the things it routes to, and that inversion is the
pattern's single largest security implication.

**Registration channel authorization.** In the self-registering shape, the
router accepts routing instructions from the destinations it will later send
traffic to. Any participant that can write to the registration channel can
claim a routing condition it has no legitimate authority to handle, and
silently receive traffic meant for a genuine destination. The channel needs
authenticated, authorized registration, scoped so a given identity can only
claim conditions within an allowlist it is entitled to, not free-form
patterns. This is not an edge case, it is the pattern's core attack surface,
directly named in the misuse list in dimension 11.

**Denial of service via registration flooding.** Because registering is
cheap by design, so the router can absorb legitimate churn efficiently, an
attacker who reaches the registration channel can flood it with a large
number of bogus registrations, growing the rule base past any operationally
sane bound and degrading match performance for every legitimate message. Rate
limit registration per identity, and cap total rule base size with an
eviction policy that favours recently active, verified destinations over
older unverified ones.

**Message content exposure via routing decisions.** In the iterative
variant, the Routing Function receives the full message, or enough of it to
decide, at every hop, including hops it may not ultimately be responsible
for. A routing function implemented as an external decision service, per the
external-decision-service variant of dimension 8, means message content, or
at minimum message metadata sufficient to route it, is now sent to a service
whose data-handling and retention policy may not match the message's actual
sensitivity classification. Treat that external call the same as any other
network egress carrying customer or regulated data, and scope what the
function receives to the minimum needed to route, not the full payload by
default.

**Loop and history injection.** If routing history is carried on the
message itself rather than held server-side by the router, per the
implementation detail in dimension 5, a sender able to forge or replay a
message with a doctored history can potentially cause the router to skip
hops that were meant to be mandatory, such as a compliance or audit hop
inserted between two business hops. Where any hop in the sequence is
security-relevant rather than purely functional, hold and verify the
routing history server-side, keyed by a message identity the sender cannot
forge, rather than trusting a client-supplied history field.

On privacy, the routing decision log recommended in dimension 16 is itself
data that deserves the same handling rigour as any other audit log holding
message identifiers and destination identities. where a destination
identity or a rule condition encodes something about a customer, a tenant,
or a data-residency requirement, the routing-decision log inherits that
sensitivity and needs the matching retention and access controls, not a
default operational-logs-keep-forever policy.

## Code examples

Three languages, each showing the iterative-expression variant, which is the
one that translates cleanly across languages with first-class functions and
is the shape most production frameworks, Camel and Spring Integration, ship
under this pattern's name. TypeScript and Python show the router as a small
reusable engine parameterised by a routing function. Go shows the same shape
using an interface, since Go has no closures-as-a-first-class-citizen
convention as strong as TypeScript's or Python's for this kind of code, and
an interface reads more idiomatically in a Go codebase for a pluggable
decision point.

### TypeScript

```typescript
type RoutingHistory = string[];
type RoutingFn = (payload: string, history: RoutingHistory) => string | null;

class DynamicRouter {
  private readonly maxHops = 10;

  constructor(private readonly route: RoutingFn) {}

  send(payload: string): RoutingHistory {
    const history: RoutingHistory = [];
    while (history.length < this.maxHops) {
      const next = this.route(payload, history);
      if (next === null) return history;
      history.push(next);
    }
    throw new Error(`hop ceiling of ${this.maxHops} reached, possible loop`);
  }
}

const approvalRouter = new DynamicRouter((payload, history) => {
  const amount = Number(payload);
  if (history.length === 0) return "manager-approval";
  if (history.length === 1 && amount > 10000) return "finance-approval";
  return null;
});

console.log(approvalRouter.send("500"));
console.log(approvalRouter.send("50000"));
```

### Python

```python
from typing import Callable, Optional

RoutingFn = Callable[[str, list[str]], Optional[str]]


class DynamicRouter:
    def __init__(self, route: RoutingFn, max_hops: int = 10) -> None:
        self._route = route
        self._max_hops = max_hops

    def send(self, payload: str) -> list[str]:
        history: list[str] = []
        while len(history) < self._max_hops:
            next_hop = self._route(payload, history)
            if next_hop is None:
                return history
            history.append(next_hop)
        raise RuntimeError(f"hop ceiling of {self._max_hops} reached, possible loop")


def approval_route(payload: str, history: list[str]) -> Optional[str]:
    amount = float(payload)
    if not history:
        return "manager-approval"
    if len(history) == 1 and amount > 10000:
        return "finance-approval"
    return None


if __name__ == "__main__":
    router = DynamicRouter(approval_route)
    print(router.send("500"))
    print(router.send("50000"))
```

### Go

```go
package main

import (
	"errors"
	"fmt"
)

type RoutingFn interface {
	Route(payload string, history []string) (string, bool)
}

type approvalRoute struct{}

func (approvalRoute) Route(payload string, history []string) (string, bool) {
	if len(history) == 0 {
		return "manager-approval", true
	}
	if len(history) == 1 && payload == "50000" {
		return "finance-approval", true
	}
	return "", false
}

type DynamicRouter struct {
	route   RoutingFn
	maxHops int
}

func NewDynamicRouter(route RoutingFn) *DynamicRouter {
	return &DynamicRouter{route: route, maxHops: 10}
}

func (r *DynamicRouter) Send(payload string) ([]string, error) {
	history := []string{}
	for len(history) < r.maxHops {
		next, ok := r.route.Route(payload, history)
		if !ok {
			return history, nil
		}
		history = append(history, next)
	}
	return nil, errors.New("hop ceiling reached, possible loop")
}

func main() {
	router := NewDynamicRouter(approvalRoute{})
	h1, _ := router.Send("500")
	fmt.Println(h1)
	h2, _ := router.Send("50000")
	fmt.Println(h2)
}
```

## 18. References

1. Gregor Hohpe, Bobby Woolf. *Enterprise Integration Patterns. Designing,
   Building, and Deploying Messaging Solutions*. Addison-Wesley, 2003.
   ISBN 0-321-20068-3. Message Router chapter, Dynamic Router. Source of the
   pattern name, the original problem and solution statement, and the
   self-registering shape.
2. Enterprise Integration Patterns companion site. "Dynamic Router".
   https://www.enterpriseintegrationpatterns.com/patterns/messaging/DynamicRouter.html
   Verified 2026-08-02. Source of the exact problem statement quoted in
   dimension 1 and the differentiation from Content-Based Router and
   Routing Slip in dimension 1.
3. Enterprise Integration Patterns companion site. "Message Router".
   https://www.enterpriseintegrationpatterns.com/patterns/messaging/MessageRouter.html
   Verified 2026-08-02. Confirms Dynamic Router's placement as a variation
   within the broader Message Router family.
4. Apache Software Foundation. Apache Camel documentation, "Dynamic Router
   EIP". https://camel.apache.org/components/latest/eips/dynamicRouter-eip.html
   Verified 2026-08-02. Source of the iterative expression variant, the
   null-termination requirement, and the Exchange-scoped state guidance
   quoted in dimensions 1, 7, and 8.
5. VMware Tanzu. Spring Integration reference documentation, Router
   documentation index. https://docs.spring.io/spring-integration/reference/router.html
   Verified 2026-08-02. Confirms Dynamic Router as a distinct, named router
   type in Spring Integration's routing family, cited in dimensions 1 and 9.
6. Envoy Proxy project. "Dynamic configuration (xDS)", architecture
   overview. https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/operations/dynamic_configuration
   Verified 2026-08-02. Source of the Route Discovery Service description
   quoted in dimensions 1 and 9.
7. Istio project. "Istio architecture, deployment model".
   https://istio.io/latest/docs/ops/deployment/architecture/
   Verified 2026-08-02. Source of the istiod-to-Envoy xDS propagation
   description cited as a named production use in dimension 9.
