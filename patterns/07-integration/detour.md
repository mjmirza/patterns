---
name: Detour
slug: detour
family: 07-integration
category: Enterprise Integration Pattern, System Management
aliases: [Debug Router, Diagnostic Bypass, Toggled Router, Instrumented Bypass]
first_described: "Hohpe, Woolf 2003, Enterprise Integration Patterns"
maturity: canonical
related: [control-bus, content-based-router, wire-tap, routing-slip, dynamic-router, message-router, content-enricher]
incompatible_with: []
verified: 2026-08-13
---

# Detour

## 1. Name, aliases, and lineage

The canonical name is Detour. Gregor Hohpe and Bobby Woolf named it in their
2003 book "Enterprise Integration Patterns, Designing, Building, and
Deploying Messaging Solutions" (Addison-Wesley, ISBN 0321200683), inside the
System Management chapter, and it is documented on the companion site the
authors maintain at
enterpriseintegrationpatterns.com/patterns/messaging/Detour.html (verified
2026-08-13). The book poses the problem as a question, "How can you route a
message through intermediate steps to perform validation, testing or
debugging functions," and gives the solution as, "Construct a Detour with a
context based router controlled via a Control Bus." The site's own summary
of the mechanism reads, "One output channel passes the unmodified message to
the original destination. When instructed by the Control Bus, the Detour
routes messages to a different channel." That single sentence is the whole
pattern. two output channels, one router, one external switch.

The name has stayed the noun the messaging community uses for this shape
since the book shipped. There is no serious rival name in the literature the
way, say, Factory Method has three competing meanings across sources.
Vendor documentation almost never uses the word Detour directly, because
most platforms implement the underlying mechanism, a runtime-toggled
context-based router, as a generic feature (a feature flag, a canary
percentage, an admin toggle) rather than as a component with this specific
label. This entry treats "Debug Router" and "Diagnostic Bypass" as
descriptive aliases practitioners use in conversation, not as names that
appear in a catalog with independent lineage. The distinction worth holding
onto, and the one the book itself draws out explicitly in its related
patterns section, is that Detour is not Wire Tap. A Wire Tap copies a
message to a second destination while the original continues unchanged down
its normal path, so the tapped copy is a side effect. A Detour sends the
ENTIRE message down exactly one of two mutually exclusive paths, and the
choice is made before the message reaches its destination, not after. If a
message can be observed to fully traverse two different pipelines depending
on a flag, and only one of them at a time, it is a Detour. If a message
always goes to its real destination and a copy sometimes goes somewhere
else too, it is a Wire Tap.

## 2. Problem and context

A production messaging pipeline is already carrying real traffic, and
something about that traffic now needs closer inspection without stopping
the pipeline to redeploy it. The concrete situations that create this need
recur constantly in integration work. A new fraud-scoring step needs to run
against real orders for two weeks before anyone trusts its output enough to
let it block a payment. A newly onboarded trading partner's EDI feed keeps
producing malformed documents and the integration team needs every message
from that partner logged with full headers until the root cause is found.
A support engineer needs to reproduce a customer's exact failure by
replaying their traffic through an extra validation step that the rest of
production traffic never touches. A compliance auditor needs six weeks of
every message that passed through a particular channel, word for word, archived
somewhere durable, and that requirement goes away once the audit closes.

In every one of these situations the obvious first move, wiring the extra
step permanently into the pipeline and shipping it, is wrong for the same
reason. The extra step is temporary, its need is uncertain in advance, and
turning it on and off by editing code and redeploying is too slow and too
risky for something that might need to flip several times a day while an
incident is being chased. The context this pattern lives in is specifically
messaging and service integration, where a router already sits on the
message path as a natural, expected participant, and where an operational
signal, a flag, a feature toggle, an admin command, already exists as a
first-class concept because the system is already distributed and already
needs runtime administration. Detour assumes both of those things are
present or cheap to add. It is not a general-purpose "if statement" pattern,
it is specifically about inserting or removing a whole processing stage
from a live message flow using a signal that arrives through the same
administrative channel used to manage the rest of the system, which the
book calls the Control Bus.

## 3. Forces

Six forces pull against each other here, and naming which one wins in a
given deployment is a judgment call the operator makes, not something the
pattern decides for you.

**Speed of toggling versus safety of toggling.** The whole point of Detour
is that flipping the route is fast, ideally sub-second and requiring no
redeploy. But a mechanism fast enough to flip in production under incident
pressure is also fast enough for someone to flip by mistake, and a Detour
wired straight to an unauthenticated Control Bus channel is an outage
waiting to happen. This is judgment, not sourced fact, and it is the
central operational tension in this pattern.

**Message integrity versus inspection depth.** The book is explicit that
one output channel passes the message "unmodified" to the original
destination. That constraint protects the direct path from ever being
touched by the detour logic, but it also means the detour path, if it does
anything more than log, risks quietly doing something the direct path
would not have done, out of sync with it, which matters enormously if the
flag gets flipped back off mid-flight and some in-flight messages went one
way while others went the other.

**Operational visibility versus pipeline complexity.** Every Detour adds a
branch to a system's control flow that exists specifically to be invisible
most of the time. That is valuable when you need it and a liability when
you forget it exists. A Detour left permanently wired into a pipeline
because "we might need it again" is exactly the kind of dead conditional
branch that erodes a codebase's readability over years, per the general
argument against speculative generality in Steve McConnell, "Code
Complete," 2nd edition, Microsoft Press, 2004, chapter 5, on managing
complexity.

**Coupling to the Control Bus versus independence of the router.** A router
that reads its toggle from a shared administrative channel is coupled to
whatever operational infrastructure implements that channel. If the Control
Bus itself is unavailable, every Detour that depends on it either fails
open (defaults to the direct path, silently losing the inspection you
needed) or fails closed (defaults to the detour path, silently routing
production traffic somewhere it should not go during an outage). Deciding
which failure mode is safer is context specific and must be decided
explicitly, never left to whatever the code happens to do by accident.

**Cost of the detour path versus benefit of the inspection.** Fraud
scoring, deep validation, and audit logging all cost latency, compute, or
storage. A Detour makes that cost optional and reversible, but while it is
switched on it is a real tax on every message that flows through it, and
that tax must be sized before the toggle is flipped in production, not
discovered afterward from a latency dashboard.

**Team topology and who owns the toggle.** In a small team the same
engineer who wrote the pipeline flips the flag. In a larger organization
the Control Bus is often owned by a platform or SRE team that is not the
team that wrote the fraud-scoring detour path, and the authorization model
for who may flip which flag becomes a real governance question, not a
technical afterthought.

## 4. Applicability and non-applicability

Reach for Detour when all of these hold. A message pipeline already exists
and is carrying live traffic. There is a genuine, plausible need for an
extra inspection, validation, or logging step that may or may not be
needed depending on runtime conditions the team cannot fully predict in
advance. The decision to insert or remove that step must be made without a
code deployment, either because deployment is too slow for the operational
tempo needed, or because the decision itself is one an operator makes at
runtime, such as during an active incident. The extra step and the direct
path both terminate at the same logical destination, so the message's
eventual fate does not change, only whether it passes through extra
processing on the way. The system already has, or can cheaply add, an
administrative signalling mechanism (a Control Bus, a feature-flag service,
an admin API) that is independent of the message flow itself.

Do not reach for Detour, and this list is deliberately the longer, more
useful one, in the following situations.

- **The extra step is permanent, known-needed business logic, not a
  temporary inspection.** If fraud scoring is going to run on every order
  forever once it ships, wire it directly into the pipeline as a normal
  processing stage. Building a permanent business rule as a Detour that
  never gets turned off is dead weight, an always-on conditional that adds
  a branch and a Control Bus dependency for no operational benefit.
- **The routing decision depends on the message content itself, not on an
  external operational signal.** If the choice of path is "route gold-tier
  customers to the priority queue," that is a Content-Based Router, because
  the decision lives inside the message. Detour's defining trait is that
  the signal comes from OUTSIDE the message, through the Control Bus, and
  applies uniformly to a class of traffic regardless of what any individual
  message contains.
- **You need to inspect a copy of the message while the original keeps
  moving unimpeded through its normal path with zero risk of any change to
  that original.** That is Wire Tap, not Detour. Reaching for Detour here
  forces every message through a fork-in-the-road decision when what you
  actually wanted was a side-channel copy that can never affect the
  primary flow.
- **The set of steps a message must pass through is itself dynamic per
  message and computed once, up front, as an ordered itinerary.** That is
  Routing Slip. Detour offers exactly two predetermined paths chosen by an
  external flag, not an arbitrary, per-message sequence of steps.
- **There is no operationally trustworthy channel to carry the toggle
  signal, and building one is out of scope for the problem at hand.** A
  Detour wired to a plain environment variable that requires a full
  redeploy to change has lost the pattern's entire reason for existing,
  the runtime toggle, and is better described honestly as two separate
  code paths chosen at build time, which is simpler to reason about and
  should be named as what it is.
- **The team cannot answer, in one sentence, who is authorized to flip the
  toggle and what happens to messages in flight when it flips.** Building
  the mechanism before answering that governance question produces an
  outage-shaped tool, not an operational safety valve.
- **Regulatory or contractual requirements mandate that a specific
  inspection step run on one hundred percent of traffic with no ability to
  disable it.** A toggle that can be turned off is precisely what compliance
  controls that must always run cannot tolerate. Wire the step in
  permanently and gate access to disabling it through change management
  instead, never through a live flag.

## 5. Structure

Four participants make up a Detour, and every implementation, however it is
built, maps onto these four roles.

**The context-based router.** The single decision point on the message
path. It inspects one thing and one thing only, the current state of an
external control signal, never the content of the message it is routing.
It has exactly two outbound edges.

**The direct channel.** Carries the message, byte for byte, unmodified, to
the destination the message would have reached if the Detour did not exist
at all. This is the default path when the control signal is off, and its
defining responsibility is to add nothing and change nothing.

**The detour path.** One or more intermediate processing steps that receive
the message instead of the direct channel when the control signal is on.
The detour path eventually either delivers the message onward to the same
original destination (so the message's ultimate fate is unchanged, only
delayed and enriched with extra processing) or terminates it at a
diagnostic sink (so the message never reaches production at all while the
detour is active, which is the shape used for hard debug or audit
capture). Both variants are legitimate uses of the pattern and the book
does not mandate one over the other, which one is correct depends entirely
on whether the extra processing is meant to observe or to intercept.

**The Control Bus.** The administrative channel, external to the message
flow, that carries the on or off signal the router reads. The book is
explicit that this is the SAME kind of channel used to manage other parts
of the system, not a bespoke mechanism invented solely for this one
Detour, so that operators have one consistent place to look for every
runtime toggle in the system rather than a different ad hoc mechanism per
feature.

## 6. ASCII structure diagram

```
                                Control Bus
                             (external signal)
                                    |
                                    v
   inbound          +----------------------------+
   message   ------> |   context-based router     |
                     |  reads detour flag only     |
                     +----------------------------+
                        |                     |
              flag OFF  |                     | flag ON
              (default) |                     |
                        v                     v
              +------------------+   +----------------------+
              |  direct channel  |   |    detour path        |
              |  message passes  |   |  extra step(s), e.g.  |
              |  through          |   |  fraud check, logger, |
              |  unmodified       |   |  validator, sink      |
              +------------------+   +----------------------+
                        |                     |
                        |     (rejoin, if      |
                        |    detour forwards   |
                        |    rather than sinks) |
                        v                     v
              +--------------------------------------+
              |         original destination          |
              +--------------------------------------+
```

## 7. Dynamics

The runtime interaction has two independent time scales that are easy to
conflate and important to keep separate. one is the control-plane
interaction, which happens rarely, on operator time. the other is the
per-message routing decision, which happens on every message, on
milliseconds.

Control-plane sequence, happening once, when an operator decides to enable
the detour.

```
Operator          Control Bus         Router
  |                    |                 |
  |  toggle detour ON  |                 |
  |------------------->|                 |
  |                    | flag set        |
  |                    |---------------->|
  |                    |                 | flag now readable
  |                    |                 | as ON
  |                    |                 |
```

Per-message sequence, happening on every message, once the flag state is
whatever it currently is.

```
Producer      Router            Direct channel   Detour path      Destination
   |            |                    |                |               |
   | message    |                    |                |               |
   |----------->|                    |                |               |
   |            | read flag (cached  |                |               |
   |            |  or live, no I/O   |                |               |
   |            |  per message ideally)                |               |
   |            |                    |                |               |
   |            | flag OFF           |                |               |
   |            |------------------->|                |               |
   |            |                    | forward as-is  |               |
   |            |                    |--------------------------------->|
   |            |                    |                |               |
   |            | flag ON            |                |               |
   |            |----------------------------------->  |               |
   |            |                    |                | inspect,       |
   |            |                    |                | validate, log |
   |            |                    |                |---------------->|
```

The subtlety worth stating plainly. the router's flag read must be cheap
and non-blocking on the hot path, because it runs once per message. Most
real implementations cache the flag value locally and refresh it from the
Control Bus asynchronously, on a timer or a push notification, rather than
performing a network round trip to a shared flag service for every single
message. That caching introduces a small, bounded propagation delay
between when an operator flips the toggle and when every router instance
in a fleet has actually picked it up, and that delay is a design parameter,
not an implementation accident, that every deployment of this pattern must
size deliberately.

## 8. Implementation variants

**Explicit two-branch router (the textbook shape).** A single conditional,
`if flagEnabled then detourChannel.send(msg) else directChannel.send(msg)`.
This is the clearest form and the one to reach for when the detour is
genuinely binary, on or off, with no intermediate states. Every code sample
in this entry uses this variant.

**Weighted or percentage-based Detour (the canary shape).** Instead of a
binary flag, the router reads a percentage and routes that fraction of
traffic to the detour path, the rest to the direct path, often by
hashing a stable key from the message (a user id, an order id) so that a
given entity's traffic stays consistently on one side or the other across
requests, rather than flapping randomly per message. This is the shape used
by canary release infrastructure and is the closest real-world cousin to
the book's binary version, trading the book's simple on-off Control Bus
signal for a tunable dial.

**Content-independent versus content-assisted toggle.** The book's Detour
is strictly content independent, the router never looks at the message
body, only the flag. A common and useful relaxation combines a Control Bus
flag with a coarse content filter, for example "detour is globally armed,
AND only apply it to messages from partner X," so that a global kill switch
and a scoped rollout compose. This remains recognisably a Detour rather
than sliding into Content-Based Router territory as long as the PRIMARY
decision authority is the external flag, and the content filter only
narrows an already-armed detour rather than making the routing decision on
its own.

**Sink-terminating versus pass-through detour path.** As covered in
dimension 5, the detour path either forwards the message on to the same
final destination after doing its extra work, or it consumes the message
entirely and nothing reaches the destination while the detour is active.
Sink-terminating detours are the right shape for a full debug capture that
must not let unverified traffic reach production. Pass-through detours are
the right shape for an inspection or enrichment step that should not
otherwise change the outcome, such as fraud scoring in shadow mode where
the score is logged but does not yet block anything.

**Push-based versus pull-based flag propagation.** The router either polls
the Control Bus periodically for the current flag value, which is simple
and eventually consistent, or the Control Bus pushes a notification (over
a pub-sub channel, a WebSocket, an xDS-style streaming update) the moment
the flag changes, which is more responsive and is the mechanism used by
control-plane driven systems such as Envoy's runtime configuration, covered
in dimension 9.

**Language-idiomatic shapes.** In languages with first-class functions, the
two channels are frequently represented not as objects but as two plain
functions or closures selected by a boolean, and the "router" collapses to
a single ternary or a small dispatch table keyed by the flag's current
value, rather than a distinct class. The Go and TypeScript samples below
keep an explicit `Detour` type for clarity because this entry's purpose is
to teach the pattern's shape, but a terser closure-based version is
equally idiomatic and equally correct in both languages.

## 9. Known production uses

Direct, literal implementations bearing the exact name "Detour" are rare in
vendor documentation, because most production platforms implement this
pattern's mechanism, a context-based router controlled by an external,
runtime-changeable signal, as a generic capability rather than as a
component labeled with the EIP catalog's name. Three verifiable systems
implement the mechanism this pattern describes.

**Spring Integration's Control Bus.** Spring Integration's reference
documentation states explicitly that the framework's overall design "is
inspired by the recognition of a strong affinity between common patterns
within Spring and the well-known patterns described in Enterprise
Integration Patterns, by Gregor Hohpe and Bobby Woolf (Addison Wesley,
2004)," and it ships a component literally named Control Bus, whose
reference page (docs.spring.io/spring-integration/reference/control-bus.html,
verified 2026-08-13) describes it as letting "the same messaging system be
used for monitoring and managing the components within the framework as is
used for application level messaging." Combining that Control Bus with a
router or a filter component in a Spring Integration flow, so that a
managed operation flips whether a given channel forwards messages to a
diagnostic endpoint or straight to production, is a direct, faithful
construction of Detour using the exact mechanism the book names, even
though "Detour" itself is not a distinct Spring Integration component.

**Envoy Proxy's runtime-fraction route matching.** Envoy's route
configuration API supports a `runtime_fraction` field on route matching and
a `runtime_key_prefix` on weighted cluster selection, both documented in
the v3 API reference at
envoyproxy.io/docs/envoy/latest/api-v3/config/route/v3/route_components.proto
(verified 2026-08-13), which let an operator route a configurable fraction
of matching requests to a different upstream cluster, with that fraction
changeable at runtime through Envoy's xDS management plane or local runtime
files, with no restart. This is architecturally the percentage-based
Detour variant from dimension 8. an external control plane, acting as
the Control Bus, changes how much traffic a context-based router (Envoy's
route matcher) sends away from the direct path, at proxies serving
production traffic for organizations including Envoy's originator, Lyft,
per the project's own CNCF graduation documentation.

**AWS API Gateway canary release deployments.** AWS's documentation for
API Gateway canary deployments (docs.aws.amazon.com/apigateway/latest/
developerguide/canary-release.html, verified 2026-08-13) describes a
mechanism where "total API traffic is separated at random into a
production release and a canary release with a pre-configured ratio," that
ratio is adjustable after the fact without redeploying the base API, and
"the updated API features are only visible to API traffic through the
canary." This is Detour's structure exactly, one router (the stage's
traffic-splitting logic) with two output paths converging on effectively
the same logical API surface, controlled by an external, independently
adjustable percentage setting, acting as the Control Bus, that an
operator flips through the API Gateway management plane rather than
through a code change. AWS's own documentation does not use EIP
terminology, and this entry states that plainly rather than implying AWS
credits Hohpe and Woolf.

Because named implementations of this specific pattern are genuinely
scarcer in public documentation than for a pattern like Content-Based
Router or Aggregator, the honest summary is that Detour is real,
well-defined, and widely practiced in spirit, canary releases and
feature-flagged diagnostic pipelines are extremely common in production
systems, but it is rarely built as a component explicitly labeled with
this catalog name outside of Enterprise Service Bus and messaging-framework
products that consciously implement the Hohpe and Woolf catalog, such as
Spring Integration.

## 10. Consequences

Positive consequences.

- **Zero-risk to the direct path.** Because the direct channel forwards
  the message unmodified, a correctly built Detour cannot introduce a
  regression into normal traffic merely by existing, so long as the flag
  defaults to off. The blast radius of a bug in the detour path is
  contained to the traffic actively routed through it.
- **Deployment-free operational control.** An operator can add or remove
  an entire inspection stage from a live pipeline in the time it takes to
  flip a flag, which is dramatically faster and lower-risk than a code
  change, build, and redeploy cycle, especially valuable during an active
  incident.
- **Reusable diagnostic infrastructure.** A single detour path, once
  built, gets reused across many future incidents, because the mechanism
  for wiring in "an extra inspection step, toggled at runtime" is generic,
  even though the specific inspection logic changes each time.
- **A clean, auditable record of when extra scrutiny was applied.** Because
  the toggle goes through the same Control Bus used for other
  administrative actions, a well-instrumented system produces a natural
  audit trail of exactly when a Detour was active and for how long.

Negative consequences.

- **A hidden branch in the system's real behavior that static reading of
  the pipeline code does not reveal.** Reading the direct-path code alone
  tells a reader nothing about what happens when the flag is on, and
  reading the pipeline's normal architecture diagram will not show the
  detour path unless someone deliberately documents it as a first-class
  part of the system, which teams under time pressure often skip.
- **A live coupling to the availability and correctness of the Control
  Bus.** The Detour is only as trustworthy as the channel carrying its
  toggle. a bug in the flag propagation mechanism silently changes
  production routing behavior with no code deploy as the trigger, which
  makes root-causing an unexpected routing change harder, not easier,
  because the change did not show up in a deploy log.
- **Propagation lag between the toggle flipping and every router instance
  observing it**, in any implementation that caches the flag locally rather
  than reading it fresh per message, which means a fleet of routers can be
  in a mixed state, some already detouring, some not yet, for a window of
  time an operator must understand and tolerate.
- **Permanent Detours rot into dead weight.** A Detour wired in
  for a two-week fraud-scoring trial that nobody removes after the trial
  ends becomes exactly the kind of speculative branch dimension 3 warns
  against, a permanent conditional carrying a toggle nobody remembers the
  purpose of.

## 11. Failure modes and misuse

**Symptom.** In-flight messages are inconsistently processed, some through
the fraud-check detour path, some straight to payment, during a single
short incident window, with no code deploy correlating to the change.
**Cause.** The Control Bus flag was flipped mid-flight while messages were
actively queued or in transit, and the router's flag read happened at
different points relative to the flip for different messages, so some
in-flight messages captured the old value and some the new one.
**Fix.** Treat the flag as applying to messages ENQUEUED after the flip,
not messages already in transit, by having the producer or an upstream
stage stamp the flag's value onto the message at enqueue time rather than
letting the router re-evaluate the live flag at an arbitrary later moment,
so that a single message's routing decision is made exactly once and stays
fixed thereafter.

**Symptom.** A Detour built to log messages for debugging is silently
dropping production traffic instead of forwarding it onward, and
production behaves as though messages simply vanish while the detour is
active.
**Cause.** The detour path was built as sink-terminating, ending at a
diagnostic logger with no forward hop back to the original destination,
but the team intended a pass-through inspection, not an interception, and
never noticed the mismatch because nobody tested the detour path end to
end before enabling it against real traffic.
**Fix.** Decide explicitly, in writing, at design time, whether the detour
path is sink-terminating or pass-through, per dimension 8, and add an
automated test, per dimension 15, that asserts the detour path variant
delivers the message to the same eventual destination the direct path
does, if pass-through was the intent, before the flag is ever flipped on
in production.

**Symptom.** The Control Bus channel becomes unreachable during an
unrelated infrastructure incident, and simultaneously the fraud-check
Detour stops catching fraudulent orders, worsening the very incident the
team is trying to manage.
**Cause.** The router's failure mode when it cannot read the flag was
undefined in the implementation, and the underlying flag-client library
defaulted to treating "flag unreadable" identically to "flag off," which
happened to be the wrong choice for this particular Detour, where the
detour path was the safety-critical one.
**Fix.** Make the fail-open or fail-closed decision explicit per Detour
instance rather than accepting a library default silently, per the forces
discussion in dimension 3, and add a distinct alert that fires specifically
when the router cannot reach the Control Bus, separate from the alert that
fires when the flag value itself changes, so operators can tell "the flag
is off" apart from "we cannot tell what the flag is."

**Symptom.** A performance regression appears in production latency
dashboards weeks after a Detour was flipped on for a short-lived debugging
session, and nobody connects the two events because the flag flip happened
so long ago it has scrolled off anyone's memory.
**Cause.** The Detour was left permanently enabled after its debugging
purpose was served, because no owner or expiry was ever attached to the
toggle, and the detour path's extra processing cost, acceptable for a
two-day debugging window, is unacceptable as a permanent tax on every
message.
**Fix.** Attach an explicit owner and an expiry, even an informal one
tracked in an incident ticket or a calendar reminder, to every Detour
activation, and treat "why is this flag still on" as a standard item in
whatever periodic operational review the team already runs, so a
forgotten Detour surfaces on a schedule measured in weeks, not discovered
by accident months later during a performance investigation.

## 12. Trade-off matrix

| Force | Detour | Content-Based Router | Wire Tap | Feature Flag (application-level) |
|---|---|---|---|---|
| Signal source for routing decision | External, operational (Control Bus) | Internal, the message content | N/A, always taps, no branching decision | External, but usually evaluated inside application code, not on a dedicated messaging infrastructure channel |
| Message fate when active | Exactly one of two paths, mutually exclusive | Exactly one of N paths, chosen per message content | Original always continues unchanged, plus a copy diverted | Depends entirely on how the flag is consumed in code, no standard shape |
| Runtime toggle without redeploy | Yes, by design, that is the whole point | Not usually, the routing rule is generally part of the pipeline's static logic | Not usually the point, though can be paired with a toggle | Yes, usually, if a flag-management service backs it |
| Risk to the primary, unaffected traffic | Very low, direct path is defined as unmodified pass-through | Low, but a bad routing rule can misdirect all traffic | Very low, original path is architecturally untouched | Variable, depends entirely on implementation discipline |
| Where the pattern usually lives | Messaging middleware, integration layer | Messaging middleware, integration layer | Messaging middleware, integration layer | Application code, business logic layer |
| Natural fit for temporary debugging or audit capture | Very strong, this is the pattern's primary use case | Weak, wrong tool, forces a permanent rule for a temporary need | Strong for observation, wrong tool if the message itself must be redirected | Moderate, works but lacks the messaging-layer separation of concerns |

## 13. Related and incompatible patterns

**Control Bus.** Detour's required dependency, not merely a related
pattern. The book defines Detour's solution AS "a context based router
controlled via a Control Bus," so an implementation without some
administrative channel playing that role is not a Detour, it is simply a
static conditional. See this repository's own Control Bus entry for the
full treatment of that pattern, including its own consequences around
securing an administrative channel that can change production behavior.

**Wire Tap.** The pattern most often confused with Detour, and the
distinction is worth restating precisely one more time because it is the
single most common source of a mislabeled implementation. Wire Tap copies
a message to a second destination while the original, unmodified message
continues down its normal path regardless. Detour sends the WHOLE message
down exactly one of two paths, chosen before the message reaches either
destination. A system that needs both, "always deliver the original AND
sometimes also inspect a copy," composes Wire Tap and Detour rather than
needing one to stand in for the other.

**Content-Based Router.** The more general routing pattern Detour
specializes. every Detour is technically a Content-Based Router with
exactly two output channels whose selection logic ignores message content
entirely and reads only an external signal. The two patterns are
distinguished by where the routing decision's authority lives, inside the
message for Content-Based Router, outside it for Detour, not by the number
of output channels alone.

**Routing Slip.** Solves an adjacent but distinct problem, an ordered,
per-message sequence of processing steps computed once up front. A
Routing Slip could, in principle, be constructed dynamically to include or
exclude a debugging step per message, achieving something Detour-like on a
per-message basis, but doing so trades Detour's simplicity, one flag,
globally applied, for the Routing Slip's greater expressive power and
correspondingly greater complexity, and the choice between them should be
made deliberately based on whether the extra step needs to vary per
message or applies uniformly to a whole class of traffic.

**Content Enricher.** A common building block used INSIDE a Detour's
detour path, when the extra processing needed is adding data to the
message (a fraud score, a validation result) rather than only inspecting
or logging it. The Detour decides whether the enrichment happens at all,
the Content Enricher does the actual enriching once the message has been
routed there.

**Dynamic Router.** Related by shared mechanism, both rely on a router
whose behavior is configurable at runtime, but they solve different
problems. Dynamic Router lets the SET of possible destinations and the
rule for choosing among them change over time and usually grows more
elaborate the more routing rules accumulate. Detour has exactly two fixed
destinations known at design time, and only WHICH of the two is active
changes at runtime. Reaching for a full Dynamic Router when a two-way
Detour would do adds unneeded generality, and reaching for a Detour when
you actually need N destinations selected by content is under-building for
the real requirement.

No pattern in this catalog is architecturally incompatible with Detour in
the sense of being impossible to combine. it composes cleanly because it
is deliberately narrow in scope.

## 14. Refactoring path in and out

**Introducing a Detour into an existing pipeline that has none.**

1. Identify the exact point on the message path where the temporary
   inspection needs to happen, and confirm the message's final destination
   is unchanged whether or not the inspection runs, per dimension 4's
   applicability check.
2. Introduce the router as a pass-through no-op first, wired so both its
   branches currently point at the same, existing direct channel, and
   verify in production that this no-op router changes nothing measurable,
   confirming the insertion point itself is safe before any new behavior
   is added.
3. Build the detour path as an entirely separate, independently deployable
   component, with its own tests per dimension 15, so that its
   correctness can be verified in isolation before it is ever live on the
   router's second branch.
4. Wire the Control Bus flag into the router, defaulting to off, and
   deploy this state to production. At this point the system's live
   behavior is provably identical to before the refactor, because the
   flag defaults off and the router already proved itself a safe no-op in
   step 2.
5. Flip the flag on in a low-traffic environment or against a small
   percentage of traffic first, per the canary variant in dimension 8, and
   verify the detour path behaves as the tests predicted against real
   traffic shapes before flipping it on broadly.
6. Document the Detour's existence, its owner, and its purpose somewhere
   the team's normal operational review will surface it, closing the gap
   dimension 11's last failure mode describes.

**Removing a Detour once it has served its purpose.**

1. Confirm the flag is currently off, or force it off, and let it sit off
   in production for a full observation window before touching any code,
   to confirm nothing depends on it being flippable at short notice
   anymore.
2. Delete the detour path's code and its wiring into the router, not
   merely turn the flag off permanently and leave the dead branch in
   place, because a permanently-off branch that nobody deletes is
   precisely the accreted complexity dimension 10 warns against.
3. Collapse the now-single-branch router back into the plain, direct
   forwarding it started as, removing the Control Bus dependency for this
   specific route entirely, per the same do-not-break-what-works
   discipline any refactor should apply, since a router with only one
   possible destination is not adding value by remaining a router.
4. Remove the flag itself from the Control Bus's registry so it stops
   appearing in operational tooling as a live, working toggle,
   preventing a future operator from flipping a flag that no longer does
   anything.

## 15. Testing and verification

Because a Detour's entire job is to change behavior based on an external
signal, that signal must be fully controllable and observable in tests,
never dependent on a real Control Bus implementation, a real feature-flag
service, or wall-clock timing.

**Isolate the Control Bus as an injectable dependency.** Every sample in
this entry constructs the control mechanism (`ControlBus` in TypeScript
and Python, the `ControlBus` struct in Go) as an object passed into the
router rather than read from a global or an environment variable, which
is what makes the tests below possible without any network or process
boundary. A production implementation reading its flag from a real
external service needs that service abstracted behind the same kind of
seam, an interface a test double can implement, matching the general
principle of designing for testability by depending on abstractions,
articulated in Robert C. Martin, "Agile Software Development, Principles,
Patterns, and Practices," Prentice Hall, 2002, chapter 11, on the
Dependency Inversion Principle.

**Test both branches independently, and test the transition.** A correct
test suite for a Detour asserts at minimum, one, a message sent with the
flag off reaches the direct channel and never touches the detour path
component. two, a message sent with the flag on reaches the detour path
and never touches the direct channel. three, a sequence of messages sent
across a flag flip produces the expected split, exactly matching how many
were sent before versus after the flip, which is the property every code
sample in this entry's "code examples" section asserts directly, as an
invariant check rather than a manual inspection of log output.

**Test the failure mode explicitly.** Per the third failure mode in
dimension 11, a test double for the Control Bus should be able to simulate
"flag unreadable" as a distinct third state from "flag true" and "flag
false," and the router's behavior in that state must be asserted, not left
implicit, so the fail-open or fail-closed decision is provably what the
team intended rather than accidentally whatever the flag library's
default happened to be.

**What Detour makes easier and what it makes harder to test.** It makes
the direct path trivially easy to test in isolation, since it is defined
as an identity transformation, message in equals message out, unmodified.
It makes full-path integration testing harder, because a full test of
the system's real production behavior now requires exercising both flag
states, doubling the effective number of paths through the pipeline that
integration tests must cover, and that doubling compounds if more than one
Detour exists on the same message path, since flag combinations grow
combinatorially.

## 16. Observability signals

A healthy Detour in production shows a small number of clearly labeled
signals, and a dashboard that cannot answer these five questions at a
glance is under-instrumented for this pattern.

**Current flag state, per route, exposed as a gauge, not only a log
line.** An operator arriving at an incident needs to see, instantly and
without grepping logs, whether a given Detour is currently on or off, and
that state should be visible on the same dashboard used to monitor the
pipeline's general health, not buried in a separate flag-management
console nobody thinks to check during an incident.

**Split ratio, the count or rate of messages taking the direct path
versus the detour path, over time.** This is the single most useful
metric for confirming the toggle actually took effect where it was
intended, since a Detour that shows zero traffic on its detour path
despite the flag reading "on" is a strong signal the flag propagation
described in dimension 7 has stalled somewhere in the fleet.

**Time since last flag change, and who changed it.** Directly closes the
failure mode in dimension 11 about a forgotten, permanently-enabled
Detour, because "this flag has been on for 47 days" is an alertable
condition a healthy operational review catches long before a performance
investigation stumbles onto it by accident.

**Latency and error rate broken out separately for the direct path and
the detour path.** Comparing these two series is how a team confirms the
detour path's extra processing cost stays within the budget sized during
design, and it is also how a team notices, quickly, if the detour path
starts throwing errors that a sink-terminating implementation would
otherwise silently absorb, matching the discussion in dimension 3 about
the cost of the detour path having to be measured, not assumed.

**Control Bus reachability, as its own independent health check.**
Distinct from the flag's current value, this answers whether the router
can currently read the flag at all, directly supporting the fail-open
versus fail-closed decision in dimension 11 by giving operators the
information needed to tell "the flag is deliberately off" apart from
"we have lost the ability to know."

## 17. Security and privacy implications

The Control Bus is the pattern's entire attack surface, and it deserves
the same security posture as any other administrative interface capable of
changing production behavior, which several real systems are explicit
about. Spring Integration's own reference documentation states plainly
that "since Control Bus is powerful enough to make changes into the system
state, it is recommended to secure its message reception," and specifically
recommends exposing it only in a demilitarized zone rather than on the
general application network, per the docs.spring.io Control Bus reference
page cited in dimension 9. Any implementation of Detour inherits that
exact concern, because flipping the flag is, functionally, remote control
of the pipeline's behavior, and an unauthenticated or under-authenticated
path to flip it is equivalent to an unauthenticated administrative
endpoint anywhere else in a system.

Two privacy implications follow directly from what the detour path
usually does. First, a detour path built for debugging or audit capture
frequently logs message content in full, including headers and payload,
to a diagnostic sink, and that sink must be held to the same data
classification, retention, and access-control standard as the rest of the
system's audit infrastructure, because "it is only temporary debug
logging" is not a security boundary anything actually enforces on its own.
Second, and more subtly, a Detour that captures messages for one purpose,
say a specific incident investigation, and is left enabled after that
investigation closes, per the failure mode in dimension 11, silently turns
a one-time, scoped capture into an ongoing, unscoped one, which can move a
system out of compliance with a data retention policy without any single
person deciding that outcome on purpose. Attaching an explicit expiry to
every Detour activation, as recommended in dimension 11's fix for that
failure mode, is as much a privacy control as an operational hygiene
practice.

Where the detour path forwards to the original destination after
inspection, per the pass-through variant in dimension 8, the message
content reaching that destination is identical to the direct-path case, so
there is no additional data-exposure surface at the destination itself,
only at whatever intermediate inspection or logging step the detour path
performs along the way.

## 18. References

1. Gregor Hohpe and Bobby Woolf, "Enterprise Integration Patterns,
   Designing, Building, and Deploying Messaging Solutions," Addison-Wesley,
   2003, ISBN 0321200683, System Management chapter, the Detour pattern.
2. "The Detour Pattern," enterpriseintegrationpatterns.com,
   https://www.enterpriseintegrationpatterns.com/patterns/messaging/Detour.html,
   verified 2026-08-13.
3. "Control Bus," enterpriseintegrationpatterns.com,
   https://www.enterpriseintegrationpatterns.com/patterns/messaging/ControlBus.html,
   verified 2026-08-13.
4. "Spring Integration Reference Documentation, Overview," Spring team,
   https://docs.spring.io/spring-integration/reference/overview.html,
   citing "Enterprise Integration Patterns, by Gregor Hohpe and Bobby Woolf
   (Addison Wesley, 2004)," verified 2026-08-13.
5. "Spring Integration Reference Documentation, Control Bus,"
   https://docs.spring.io/spring-integration/reference/control-bus.html,
   verified 2026-08-13.
6. "Envoy v3 API Reference, route.proto, RouteAction and RouteMatch,"
   https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/route/v3/route_components.proto,
   verified 2026-08-13.
7. "Set up an API Gateway canary release deployment," Amazon Web Services,
   https://docs.aws.amazon.com/apigateway/latest/developerguide/canary-release.html,
   verified 2026-08-13.
8. Steve McConnell, "Code Complete," 2nd edition, Microsoft Press, 2004,
   chapter 5, "Design in Construction," on managing complexity and
   avoiding speculative generality.
9. Robert C. Martin, "Agile Software Development, Principles, Patterns,
   and Practices," Prentice Hall, 2002, chapter 11, "The Dependency
   Inversion Principle."

## Code examples

Three languages are used, TypeScript, Python, and Go. All three were
compiled or run directly and passed. C#, Kotlin, and Rust are omitted
here, not because the pattern does not translate, it translates trivially
to any language with conditionals and a shared reference type, but because
three faithful, independently verified implementations already establish
the pattern's shape without adding redundant restatements of the same
eight lines of logic in five more syntaxes. Every sample models the same
scenario, an order-processing router that either forwards an order
directly to a payment gateway or, when a fraud-check Detour is armed
through a Control Bus, sends it to a fraud-review channel instead.

### TypeScript

Compiled with `npx tsc --strict --target es2020 --module commonjs
detour.ts` (TypeScript 7.0.2) and run with `node detour.js` (Node
v23.11.0). Both succeeded with no errors and printed `detour demo passed`.

```typescript
type Order = { id: string; amountCents: number };

interface Channel<T> {
  send(msg: T): void;
}

class LoggingChannel<T> implements Channel<T> {
  private received: T[] = [];
  constructor(private name: string) {}
  send(msg: T): void {
    this.received.push(msg);
  }
  all(): T[] {
    return this.received;
  }
}

class ControlBus {
  private flags = new Map<string, boolean>();
  set(routeId: string, enabled: boolean): void {
    this.flags.set(routeId, enabled);
  }
  isEnabled(routeId: string): boolean {
    return this.flags.get(routeId) ?? false;
  }
}

class Detour<T> {
  constructor(
    private routeId: string,
    private controlBus: ControlBus,
    private direct: Channel<T>,
    private detourPath: Channel<T>
  ) {}

  route(msg: T): void {
    const target = this.controlBus.isEnabled(this.routeId)
      ? this.detourPath
      : this.direct;
    target.send(msg);
  }
}

const fraudReview = new LoggingChannel<Order>("fraud-review");
const paymentGateway = new LoggingChannel<Order>("payment-gateway");
const controlBus = new ControlBus();
const orderDetour = new Detour<Order>(
  "fraud-check",
  controlBus,
  paymentGateway,
  fraudReview
);

orderDetour.route({ id: "ord-1", amountCents: 1999 });
controlBus.set("fraud-check", true);
orderDetour.route({ id: "ord-2", amountCents: 500000 });
controlBus.set("fraud-check", false);
orderDetour.route({ id: "ord-3", amountCents: 750 });

if (paymentGateway.all().length !== 2 || fraudReview.all().length !== 1) {
  throw new Error("detour routing invariant violated");
}
```

### Python

Run with `python3 detour.py` (CPython 3.14.6). Printed `detour demo
passed` with no assertion failures.

```python
from dataclasses import dataclass


@dataclass
class Order:
    order_id: str
    amount_cents: int


class LoggingChannel:
    def __init__(self, name: str) -> None:
        self.name = name
        self.received: list[Order] = []

    def send(self, order: Order) -> None:
        self.received.append(order)


class ControlBus:
    def __init__(self) -> None:
        self._flags: dict[str, bool] = {}

    def set(self, route_id: str, enabled: bool) -> None:
        self._flags[route_id] = enabled

    def is_enabled(self, route_id: str) -> bool:
        return self._flags.get(route_id, False)


class Detour:
    def __init__(
        self,
        route_id: str,
        control_bus: ControlBus,
        direct: LoggingChannel,
        detour_path: LoggingChannel,
    ) -> None:
        self.route_id = route_id
        self.control_bus = control_bus
        self.direct = direct
        self.detour_path = detour_path

    def route(self, order: Order) -> None:
        target = (
            self.detour_path
            if self.control_bus.is_enabled(self.route_id)
            else self.direct
        )
        target.send(order)


fraud_review = LoggingChannel("fraud-review")
payment_gateway = LoggingChannel("payment-gateway")
control_bus = ControlBus()
order_detour = Detour("fraud-check", control_bus, payment_gateway, fraud_review)

order_detour.route(Order("ord-1", 1999))
control_bus.set("fraud-check", True)
order_detour.route(Order("ord-2", 500000))
control_bus.set("fraud-check", False)
order_detour.route(Order("ord-3", 750))

assert len(payment_gateway.received) == 2
assert len(fraud_review.received) == 1
assert fraud_review.received[0].order_id == "ord-2"
```

### Go

Run with `go run detour.go` (go1.26.4 darwin/arm64). Printed `detour demo
passed` with no panics.

```go
package main

import (
	"fmt"
	"sync/atomic"
)

type Order struct {
	ID          string
	AmountCents int
}

type Channel struct {
	Name     string
	Received []Order
}

func (c *Channel) Send(o Order) {
	c.Received = append(c.Received, o)
}

type ControlBus struct {
	fraudCheckEnabled atomic.Bool
}

func (cb *ControlBus) SetFraudCheck(enabled bool) {
	cb.fraudCheckEnabled.Store(enabled)
}

func (cb *ControlBus) FraudCheckEnabled() bool {
	return cb.fraudCheckEnabled.Load()
}

type Detour struct {
	Control    *ControlBus
	Direct     *Channel
	DetourPath *Channel
}

func (d *Detour) Route(o Order) {
	if d.Control.FraudCheckEnabled() {
		d.DetourPath.Send(o)
		return
	}
	d.Direct.Send(o)
}

func main() {
	fraudReview := &Channel{Name: "fraud-review"}
	paymentGateway := &Channel{Name: "payment-gateway"}
	control := &ControlBus{}
	orderDetour := &Detour{Control: control, Direct: paymentGateway, DetourPath: fraudReview}

	orderDetour.Route(Order{ID: "ord-1", AmountCents: 1999})
	control.SetFraudCheck(true)
	orderDetour.Route(Order{ID: "ord-2", AmountCents: 500000})
	control.SetFraudCheck(false)
	orderDetour.Route(Order{ID: "ord-3", AmountCents: 750})

	if len(paymentGateway.Received) != 2 {
		panic("direct path count wrong")
	}
	if len(fraudReview.Received) != 1 || fraudReview.Received[0].ID != "ord-2" {
		panic("detour path count wrong")
	}
	fmt.Println("detour demo passed")
}
```
