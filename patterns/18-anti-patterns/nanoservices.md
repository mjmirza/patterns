---
name: Nanoservices
slug: nanoservices
family: 18-anti-patterns
category: Architectural (Distributed Systems)
aliases: [Lambda Pinball, Fine-Grained Service Explosion, Function-per-Endpoint Antipattern, Over-Decomposition]
first_described: "Community usage circa 2014, e.g. Arnon Rotem-Gal-Oz, 'Services, Microservices, Nanoservices - oh my!', 2014"
maturity: contested
related: [decompose-by-business-capability, decompose-by-subdomain, service-per-team, api-composition, database-per-service, saga, big-ball-of-mud]
incompatible_with: []
verified: 2026-08-02
---

# Nanoservices

## 1. Name, aliases, and lineage

Nanoservices names a service that is decomposed past the point where the cost
of running it as a separate process, with its own deployment pipeline,
network boundary and data store, is repaid by the isolation it buys. The word
follows the metric prefix joke already in play with microservice. If a
microservice is small, a nanoservice is smaller still, and the joke carries a
real warning inside it. below a certain grain size the unit of decomposition
stops being a service and becomes a function call wearing a service costume.

The earliest widely cited use is Arnon Rotem-Gal-Oz's 2014 post "Services,
Microservices, Nanoservices, oh my!", which places nanoservice at the bottom
of a size ladder running monolith, service, microservice, nanoservice, and
frames it as the point where "the overhead (communications, maintenance etc.)
outweighs its utility" (Rotem-Gal-Oz, "Services, Microservices, Nanoservices,
oh my!", 2014, https://arnon.me/2014/03/services-microservices-nanoservices/
verified 2026-08-02). The phrase was picked up and repeated the following
year in a DZone piece that names it directly as an SOA anti-pattern and
restates the same overhead framing, coupling and maintenance cost outweighing
the service's usefulness (DZone, "SOA Anti-pattern. Nanoservices",
https://dzone.com/articles/soa-anti-pattern-nanoservices, title and framing
confirmed via search index, verified 2026-08-02). No canonical book chapter
defines nanoservices the way Gamma, Helm, Johnson and Vlissides define
Factory Method. the term lives in blog posts, conference talks and
engineering postmortems, and its boundary is drawn differently by different
authors, which is exactly why this entry marks its maturity as contested
rather than canonical.

A second lineage runs through serverless computing. When AWS Lambda made it
cheap to deploy a single function as an independently invocable unit, some
practitioners adopted nanoservice as a neutral, even positive, label for one
function per API endpoint, arguing that Lambda functions are naturally
nanoservice-shaped and that the antipattern framing no longer applies once
the deployment unit is a function rather than a container, a position
summarised across serverless architecture commentary and verified via
independent secondary sources 2026-08-02. Independent serverless
practitioners push back on that reframing under a different name. Yan Cui,
an AWS Serverless Hero, and others describe the failure mode of chaining
many single-purpose Lambda functions through ad hoc invocation as **Lambda
Pinball**, where "logic jumps around from function to function like a
pinball in a machine" and state, retries and error handling become invisible
without a workflow engine (Haiko van der Schaaf, "Dodging the Lambda Pinball
with DDD",
https://serverlesscorner.com/dodging-the-lambda-pinball-with-ddd-9a5ed216c7e8
verified 2026-08-02). Lambda Pinball is the serverless dialect of the same
underlying complaint that nanoservices raises against containerised
microservices, too many independently deployed units chained together to do
one coherent piece of work.

## 2. Problem and context

A team adopts microservices with the correct instinct that a monolith with
too many concerns bundled into one deployable is hard to change safely, and
the guidance they read tells them smaller is safer. Taken literally, "smaller
is safer" has no natural stopping point, so a team without a grounded
decomposition heuristic keeps splitting. A service that authenticates a user,
looks up their profile and returns their preferences becomes three services.
a login service, a profile service and a preferences service, each with its
own repository, its own CI pipeline, its own container image, and its own
network address. None of the three has a reason to scale, fail or deploy on
a different schedule from the other two. They always change together,
because a login flow that needs the user's preferences will always need the
profile record that names which preferences apply.

The context in which this happens has a recognisable shape. A greenfield
project is scaffolded with a microservices template that generates one
service per resource type, so a data model with fifteen tables produces
fifteen services before a single business capability has been implemented.
Or an existing service is broken up under time pressure to unblock two teams
who each want ownership of half a file, and the split follows the org chart
rather than the actual seams in the domain. Or a serverless platform is
adopted and every route in an API definition becomes its own function by
default, because the tooling makes that the path of least resistance rather
than a deliberate choice. In every version of the story the deciding factor
was never asked. does this boundary correspond to an independent axis of
change, ownership, or scale. The service was drawn along a data field or an
HTTP verb instead, and the system now pays a network hop, a serialization
cycle, a separate deploy pipeline and a separate on-call rotation for a
decision that used to be a function call inside one process.

Eric Evans's bounded context, from domain-driven design, is the missing
heuristic in most of these stories. a service boundary should track a
boundary in the domain model where a term's meaning genuinely changes, not
an arbitrary technical seam (Eric Evans, *Domain-Driven Design. Tackling
Complexity in the Heart of Software*, Addison-Wesley, 2003, part IV,
chapters 14 to 15). Nanoservices are what happens when decomposition is
driven by size alone, with no reference to that kind of seam.

## 3. Forces

Judgement, drawn from the postmortems in dimension 9 and from the general
literature on service granularity rather than from a single citable source.

- **Independent deployability.** Sacrificed in the direction people least
  expect. the whole justification for splitting a service is usually
  independent deployment, but two nanoservices that always change together
  cannot actually deploy independently in practice, so the team pays the
  deployment overhead without receiving the benefit it was meant to buy.
- **Fault isolation.** Nominally favoured, actually often reversed. a crash
  in a nanoservice on the critical path of every request takes down every
  caller exactly as a crash in a monolith would, and now the operator has to
  trace the failure across a network boundary to find that out.
- **Latency and throughput.** Sacrificed, directly and measurably. every
  service boundary that used to be a function call becomes a network round
  trip with serialization and deserialization on both sides. this is the
  cost the code examples in this entry demonstrate directly.
- **Consistency.** Sacrificed. work that used to be one local transaction
  across in-process objects becomes a distributed operation across
  independently failing services, usually solved with a saga or with
  eventual consistency that the original monolith never needed.
- **Cognitive load per change.** Sacrificed. a change that touches a coherent
  piece of business logic now means opening several repositories, tracing a
  request across several network calls, and reasoning about partial failure
  at every hop, where before it meant reading one file.
- **Operational surface.** Sacrificed, and this is the force that shows up
  hardest in the production postmortems. each nanoservice needs its own
  build pipeline, its own health check, its own alerting rule, its own
  dashboard, its own on-call runbook entry, and its own dependency upgrade
  cadence, multiplying operational toil by the count of services rather than
  by the count of independently varying concerns.
- **Team autonomy.** Favoured only when a nanoservice genuinely maps to a
  team boundary that wants to own a small, coherent surface. this is the one
  force that can go the pattern's way, and only when team topology, not data
  shape, drove the split.
- **Reuse.** Nominally favoured, rarely realised. the promise is that a tiny
  service is easy to reuse from a second caller, but in practice the tiny
  service was carved out of one caller's needs and its contract does not
  generalise, so reuse stays theoretical while the coupling cost is real.

## 4. Applicability and non-applicability

There is no context in which drawing a service boundary purely by size is
correct, so this dimension is a single non-applicability list rather than a
paired list, per the instruction to make the non-applicability side explicit
for an anti-pattern.

Never split a service, or accept an existing split, on these grounds alone.

- **The current service file feels large.** File size measured in lines is
  not a signal about network boundaries. a large file inside one bounded
  context is a code organisation problem, addressed by the refactoring
  family, not a distributed systems problem.
- **Each field in the data model got a resource, and each resource got a
  service.** A one-to-one mapping between a database table and a network
  service produces exactly the login, profile and preferences example from
  dimension 2, three services that always change together and never scale
  independently.
- **Each HTTP verb or CRUD operation is its own deployable function by
  default of the platform's scaffolding.** Serverless tooling that
  auto-generates one function per route optimises for how easy it is to
  wire up routing, not for whether the route is an independent unit of
  change.
- **The team wants smaller pull requests.** A smaller pull request is a code
  review problem, solved by smaller commits and better review discipline
  inside one service, not by moving the boundary across a network.
- **A single method or function is reused from two call sites inside the
  same process.** That is extraction into a shared library or module, not
  service decomposition. crossing a network for code reuse pays a latency
  and availability tax that a function import never does.
- **The team wants to use a different programming language for one small
  piece of logic.** A language boundary is a real reason to consider a
  service boundary, but only when that piece of logic is also independently
  deployable and independently scaled. language choice alone, without those
  other axes, produces a nanoservice sized purely to fit the polyglot desire.
- **Two operations are always called together by every known caller, in a
  fixed order, with no caller that needs only one of them.** If nothing ever
  calls A without immediately calling B, A and B belong in the same
  deployable regardless of how conceptually distinct they feel while reading
  the code.
- **The split is driven by wanting a smaller test suite to run per commit.**
  Test suite runtime is addressed by parallelising or partitioning tests
  inside one service, per the testing family, not by fragmenting the service
  boundary. Segment's own postmortem names this exact mistake, splitting
  destinations into 140 separate services specifically to isolate flaky
  tests, and reports that the isolation produced a worse testing experience,
  not a better one, once cross-service dependency drift set in (see
  dimension 9).

Reach instead for `decompose-by-business-capability` or
`decompose-by-subdomain` (family 10-microservices), both of which start from
a bounded context and only draw a network boundary where the domain model
itself changes meaning, and check the result against `service-per-team`
(family 10-microservices) so that ownership and the network boundary agree.

## 5. Structure

Nanoservices has no useful "correct" structure diagram, because it is a
failure mode of a structure rather than a structure with participants that
cooperate correctly. The structure worth drawing is the shape the failure
takes, contrasted with the coherent decomposition it was meant to replace.

- **Fine-grained service.** A deployable unit, typically one process or one
  cloud function, that performs a single narrow operation, holds at most a
  sliver of state, and exposes that operation over a network protocol such
  as HTTP or a message queue.
- **Orchestrator or caller.** The upstream code, itself often a service, a
  Lambda function, or an API gateway route, that must invoke several
  fine-grained services in sequence or in parallel to complete one coherent
  piece of business work.
- **Wire boundary.** The serialization, deserialization, authentication and
  transport layer that every hop crosses, present as pure overhead in a
  version of the same logic kept inside one process.
- **Shared data record.** The record, such as the cart in the code examples,
  that must be marshalled across every hop even though only one field of it
  changes at each step.

## 6. ASCII structure diagram

```
  ANTIPATTERN SHAPE, five nanoservices for one coherent operation

  +----------+  network  +-----------+ network +----------------+
  | Caller / |---------->| validate- |-------->| apply-discount |
  | Gateway  |  hop 1    |   cart    |  hop 2  |   service      |
  +----------+           +-----------+         +----------------+
                                                        |
                                                network  v
                                              +----------------+
                                              | calculate-tax  |
                                              |   service      |
                                              +----------------+
                                                        |
                                                network  v
                                              +----------------+
                                              |reserve-inventory|
                                              |   service      |
                                              +----------------+
                                                        |
                                                network  v
                                              +----------------+
                                              |charge-payment  |
                                              |   service      |
                                              +----------------+

  Five processes, five deploy pipelines, five on-call rotations,
  four network hops, for one checkout that never runs its steps
  independently of each other.

  CONSOLIDATED SHAPE, same coherent operation, one bounded context

  +----------+  network  +-----------------------------------+
  | Caller / |---------->|         checkout service           |
  | Gateway  |  hop 1    |  validate -> discount -> tax ->    |
  +----------+           |  reserve -> charge, in-process     |
                          +-----------------------------------+

  One process, one deploy pipeline, one network hop.
```

## 7. Dynamics

The sequence below traces a single checkout request through the
nanoservice-decomposed shape. Every arrow that crosses a service boundary
also crosses a process boundary, and therefore pays connection setup,
authentication, serialization, network transit, deserialization, and
(usually) a retry policy on failure, on top of the actual work.

```
Client   Gateway   validate-cart  apply-discount  calc-tax  reserve-inv  charge-pay
  |         |            |              |            |          |            |
  |-req---->|            |              |            |          |            |
  |         |--RPC1----->|              |            |          |            |
  |         |            |-- 8ms wire+work -->|       |          |            |
  |         |<--cart-----|              |            |          |            |
  |         |--RPC2--------------------->|            |          |            |
  |         |                            |-- 8ms wire+work -->|  |            |
  |         |<--cart+discount------------|            |          |            |
  |         |--RPC3------------------------------------->|       |            |
  |         |                                            |-- 8ms wire+work -->|
  |         |<--cart+tax---------------------------------|       |            |
  |         |--RPC4--------------------------------------------->|            |
  |         |                                                    |-8ms wire+work->
  |         |<--cart+reserved------------------------------------|            |
  |         |--RPC5-------------------------------------------------------->|
  |         |                                                                |-8ms
  |         |<--cart+charged---------------------------------------------------|
  |<-resp---|            |              |            |          |            |

  Total wall time = sum of five wire-plus-work hops, sequential
  because each step needs the previous step's output. Any single hop
  timing out, retrying, or failing partially requires compensating
  logic (a saga) that the equivalent single-process call never needed.
```

Two consequences worth naming explicitly because they recur across dimension
9's postmortems. First, the steps here are sequential because each depends
on the previous one's result, so the latency of every hop is additive, not
overlapped by concurrency, and the total user-facing latency grows linearly
with the number of nanoservices on the path. Second, a partial failure after
`reserve-inventory` but before `charge-payment` leaves the system in a state
a single in-process transaction would never have permitted, forcing either a
saga with compensating actions (`saga`, family 08-cloud-distributed) or an
idempotent retry contract (`idempotent-consumer`, family 10-microservices)
that a coherent single service does not need at all.

## 8. Implementation variants

Nanoservices is not a pattern to implement, so this dimension catalogs the
recognisable variants of how teams arrive at it, because the entry point
determines the correct fix.

**Resource-per-service scaffolding.** A code generator or project template
produces one service per database table or per REST resource. The fix is
usually mechanical, merge the generated services that share a bounded
context back into one deployable before the first commit, and keep the
generator for scaffolding internal modules instead of network services.

**Verb-per-function serverless sprawl.** Each HTTP method on each route
becomes its own cloud function, because that is the default unit the
platform's routing configuration expects. The Lambda Pinball framing applies
here directly. the fix is to group functions that share a request lifecycle
behind one function with internal branching, or to introduce an explicit
orchestration layer such as a state machine (`saga`,
`scheduler-agent-supervisor`, family 08-cloud-distributed) so the
coordination logic is visible in one place rather than implicit in a chain
of independent invocations.

**Team-driven micro-carving.** Two engineers on the same feature want
separate ownership and separate deploy cadences for pieces of logic that in
fact always change together, and they carve a service boundary to get
organisational independence rather than technical independence. The fix is
social, not technical, merge the code and negotiate a shared ownership model,
or accept that true independent cadence requires the pieces to also be
independently correct without each other, which they currently are not.

**Cargo-culted microservices adoption.** A team reads that microservices
enable independent scaling and independent deployment, and applies fine
granularity uniformly across the whole system without checking whether any
given piece actually needs to scale or deploy independently. The fix is
`strangler-fig` (family 08-cloud-distributed) applied in reverse, consolidate
services that never diverge in their change or scaling profile back toward
one deployable, keeping the split only where a measured, not assumed, need
exists.

**Accidental nanoservices via aggressive DDD sub-domain splitting.** A team
correctly applies bounded contexts but draws the boundary at every
sub-domain rather than every domain, producing services that map to
DDD-flavoured jargon but are still too fine-grained to be independently
useful. The fix is to re-run the bounded context exercise at the level of
the domain model's actual ubiquitous language shifts, which is usually
coarser than the sub-domain diagram suggests, per Evans's own guidance that
a bounded context should be as large as the language inside it stays
consistent, not as small as possible.

## 9. Known production uses

Framed honestly for an anti-pattern entry, these are not endorsements. they
are real, sourced, publicly documented cases where an organisation ran into
the nanoservices failure mode in production and then paid the cost of
consolidating back.

**Twilio Segment, 140-plus destination services, 2018.** Segment's data
pipeline routed customer events to third-party marketing and analytics
tools, and the team gave each destination integration its own
microservice, eventually running more than 140 of them. The company's own
engineering blog describes the resulting failures directly. operational
overhead increased "linearly with each added destination", a single broken
test in one destination's suite blocked deploys unrelated to it, and
on-call engineers were repeatedly paged for load-spike issues localised to
one destination's queue. Segment consolidated all destinations into a
single monolithic service backed by a new internal queuing layer named
Centrifuge, and reports the shared-library improvement rate rose from 32 to
46 per year after consolidation, with individual destination test suites
that previously took minutes now completing in milliseconds as part of one
suite. Source, Twilio Segment engineering, "Goodbye Microservices, from
100s of problem children to 1 superstar",
https://www.twilio.com/en-us/blog/developers/best-practices/goodbye-microservices
verified 2026-08-02.

**Istio service mesh control plane, Pilot, Galley, Citadel, Mixer, and the
sidecar injector, 2018 to 2020.** Istio's control plane originally split
service discovery (Pilot), configuration validation (Galley), certificate
issuance (Citadel), policy and telemetry (Mixer) and the webhook-based
sidecar injector into separate deployable components, following the general
microservices convention. Istio's own project blog reports the components
delivered none of the benefits that separation is meant to buy. every
component was already written in Go, eliminating the language-diversity
argument. in nearly every real installation a single team operated all of
the components together, eliminating the independent-ownership argument.
releases were always synchronised across components, eliminating the
independent-deployment argument. and the components held equivalent
permissions, so the process boundary provided negligible security
isolation. The project consolidated Pilot, Galley, Citadel and the sidecar
injector into a single binary named istiod starting with Istio 1.5,
explicitly to eliminate cross-component version dependency and startup
ordering problems, cut resource footprint through shared in-memory caching,
and remove gRPC payload-size limits that existed only because components
talked to each other over the network. Source, Istio project blog,
"Introducing istiod, simplifying the control plane",
https://istio.io/latest/blog/2020/istiod/ verified 2026-08-02. The Mixer
component was separately removed as part of a concurrent redesign that
moved policy enforcement and telemetry reporting directly into the Envoy
proxies, further reducing the network-hop count per request.

**Amazon Prime Video, audio and video quality monitoring service, 2023.**
Prime Video's Video Quality Analysis team built a stream-monitoring
pipeline as a set of components orchestrated by AWS Step Functions, with
video frame detectors as separately scaling units and intermediate frame
data passed between stages through Amazon S3. The team's own account,
corroborated across multiple independent technology publications after the
original post's engineering-blog URL was retired and now redirects, reports
that the orchestration layer's per-state-transition billing and the S3
round trips for every intermediate frame became the two most expensive
parts of the pipeline, and that the architecture hit a hard scaling
ceiling well before the team's target load. The team re-architected the
monitoring service as a single process with in-memory data passing between
stages, scaling the whole service vertically and horizontally by cloning
the process rather than by adding orchestrated components, and reports a
90 percent reduction in infrastructure cost alongside headroom to keep
scaling further. Coverage corroborating the architecture, the cost drivers
and the 90 percent figure, source one, DevClass, "Reduce costs by 90% by
moving from microservices to monolith, Amazon internal case study raises
eyebrows",
https://www.devclass.com/ci-cd/2023/05/05/reduce-costs-by-90-by-moving-from-microservices-to-monolith-amazon-internal-case-study-raises-eyebrows/1621790
verified 2026-08-02, source two, The New Stack, "Amazon Prime Video's
Microservices Move Doesn't Lead to a Monolith after All",
https://thenewstack.io/amazon-prime-videos-microservices-move-doesnt-lead-to-a-monolith-after-all/
verified 2026-08-02. The original primevideotech.com post could not be
retrieved directly at verification time, its URL now redirects to a
general Amazon Entertainment landing page, so this account rests on the
two independent secondary sources above rather than on the primary post.

## 10. Consequences

Positive, and genuinely available only when the fine grain matches a real
axis of independent change, scale, or ownership rather than being applied
uniformly.

- A service that truly does need to scale, fail, or deploy independently of
  its neighbours gets to do so cleanly when it is carved out correctly, and
  the fine-grained cases in dimension 9, before consolidation, did offer
  this for the small number of components that genuinely varied.
- A narrow, single-purpose deployable is easy to understand in isolation,
  read start to finish in one sitting, and reason about without the rest of
  the system in view.
- Where a language or runtime boundary is genuinely required, for example a
  machine learning inference step needing a different runtime from the rest
  of the pipeline, a small dedicated service is the correct answer and looks
  identical in shape to a nanoservice from the outside.

Negative, and these are the consequences the postmortems in dimension 9
converge on independently of each other.

- Latency grows with every hop that used to be a function call, and the
  growth is additive across a sequential chain, as shown concretely in
  dimension 7 and in the code examples.
- Operational toil multiplies by the count of services rather than by the
  count of independently varying concerns, each with its own pipeline,
  health check, alert, dashboard and dependency upgrade schedule.
- A coherent unit of business logic becomes distributed transaction logic,
  requiring sagas, compensating actions, and idempotency contracts that a
  single-process implementation of the same logic never needed.
- Test isolation, ironically often the stated reason for splitting, gets
  worse rather than better once services drift out of version lock, exactly
  as Segment reports.
- Independent deployability, the headline justification, frequently fails
  to materialise, because services that were split by data shape rather
  than by change axis still change together in practice and must still be
  deployed together to stay correct.
- The organisation accrues a permanent tax of cross-service version
  compatibility, contract testing, and network security surface, all of
  which the equivalent in-process design would not have needed at all.

## 11. Failure modes and misuse

**Chatty checkout, order, or signup flow.** Symptom. A single user-facing
action produces five, ten, or more internal service calls visible in a
distributed trace, and p95 latency for the action tracks the sum of the
individual service latencies rather than the slowest one. Cause. The flow
was decomposed by data field or by CRUD verb instead of by bounded context,
so no step can proceed without the previous step's result, forcing a
sequential chain. Fix. Merge steps that are always invoked together, in the
same order, by every known caller, back into one deployable, per the
non-applicability list in dimension 4.

**Lambda pinball.** Symptom. A production incident review cannot answer
"which function actually failed" without manually correlating logs across
a dozen separately deployed functions, because no single trace or workflow
definition shows the full path. Cause. Serverless routing scaffolding
generated one function per endpoint and per verb with no explicit
orchestration layer coordinating them. Fix. Introduce an explicit state
machine or saga orchestrator (`saga`, family 08-cloud-distributed) so the
coordination logic is visible in one artifact, or consolidate functions
that share a request lifecycle into one function with internal branching.

**Distributed monolith masquerading as microservices.** Symptom. Every
deploy of any one service requires deploying several others in a fixed
order to avoid breaking contract compatibility, so the team has already
lost independent deployability while still paying every network and
operational cost of separation. Cause. Services were split along a data or
resource boundary that does not correspond to a real seam in the domain,
so their contracts change in lockstep. Fix. Either genuinely decouple the
contracts so each service can evolve independently, using consumer-driven
contract tests (`consumer-driven-contract-test`, family 10-microservices) to
verify that independence, or consolidate the services that cannot actually
be deployed independently.

**Test suite isolation used as the sole justification for a split.**
Symptom. Post-hoc, the team discovers that per-service test suites now
depend on cross-service integration fixtures that drift out of sync,
producing more flaky failures than the original monolithic suite had.
Cause. Service boundaries drawn to isolate one flaky test class rather than
to isolate a real domain boundary. Fix. Solve test flakiness inside one
codebase, with better test isolation and parallel test execution, per the
testing family, rather than by moving the code across a network boundary.
This is precisely what Segment names as a driver of its own 140-service
sprawl.

**Cost surprise from per-invocation billing at fine grain.** Symptom. A
cloud bill line item for an orchestration or state-transition service, for
example AWS Step Functions state transitions, or an API gateway's
per-request charge, grows disproportionately relative to the compute cost
of the actual business logic. Cause. Coordination overhead between many
fine-grained units is metered and billed per hop, and a fine decomposition
multiplies the number of billed hops for the same unit of work. Fix.
Collapse tightly coupled steps into fewer, coarser units before they reach
an orchestration layer, reserving the orchestrator for genuinely
long-running or genuinely parallel work, matching the fix Amazon Prime
Video's team applied in dimension 9.

**Onboarding collapse.** Symptom. A new engineer needs several weeks and
guidance from three different team leads to trace a single user-facing
feature across its constituent services, where the same trace inside one
codebase would take an afternoon with a debugger. Cause. The number of
deployables a single feature touches has grown past what any one engineer
can hold in working memory at once. Fix. Draw the boundary map explicitly,
using `decompose-by-business-capability`, and merge services whose
combined responsibility maps to one coherent capability a single engineer
should be able to own end to end.

## 12. Trade-off matrix

Compared against the named alternatives that address the same underlying
motivations, monolithic architecture, a correctly bounded microservice, and
a serverless function grouped by request lifecycle rather than by route.

| Force | Nanoservices | Monolithic architecture | Correctly bounded microservice (decompose-by-business-capability) | Grouped serverless function |
|---|---|---|---|---|
| Per-request network hops for one coherent action | High, one per fine-grained step | Zero, in-process calls | Low, only where the domain genuinely crosses a boundary | Low to zero, one function handles the whole lifecycle |
| Independent deployability actually achieved | Rarely, contracts change in lockstep | Not applicable, one deployable | Yes, by construction, service boundary tracks change axis | Yes, function boundary tracks lifecycle, not route |
| Operational surface, pipelines, alerts, dashboards | Multiplies with service count | One surface for the whole system | Scales with the number of real bounded contexts | Scales with the number of real workflows |
| Fault isolation on the critical path | Illusory, a chain fails together | None, a crash affects everything | Real, isolated to the owning context | Real, isolated to the owning function |
| Consistency model | Distributed, needs sagas for what used to be a local transaction | Local ACID transactions available | Distributed at real boundaries, local inside a context | Distributed only where the domain requires it |
| Team ownership clarity | Blurred, split does not track ownership | Requires strong internal module discipline | Clear, boundary tracks team and capability | Clear, boundary tracks workflow ownership |
| Cost per unit of coordination, orchestration billing, gateway fees | High, billed per hop | None | Moderate, only at real boundaries | Low, orchestration reserved for genuine async work |
| Cognitive load to trace one feature | High, crosses many repos and processes | Low, one codebase | Moderate, crosses only real boundaries | Low to moderate |

Reading of the table. nanoservices lose on every force that a correctly
bounded decomposition wins on, because the fine grain is applied uniformly
rather than at the seams the domain and the team actually need. A monolith
is not the universal answer either, it trades every one of those forces
back for the absence of any isolation at all, which is why `big-ball-of-mud`
(family 18-anti-patterns) is the opposite failure mode on the same axis,
too little decomposition rather than too much.

## 13. Related and incompatible patterns

- **big-ball-of-mud.** The opposite extreme on the same granularity axis.
  where nanoservices decompose too finely with no regard for real seams, a
  big ball of mud has no decomposition at all. Both share the same root
  cause, the absence of a domain-driven boundary heuristic, applied in
  opposite directions.
- **decompose-by-business-capability, decompose-by-subdomain.** The
  corrective patterns. both start decomposition from the domain model or
  the org's business capabilities rather than from data shape or HTTP
  verbs, and both are the direct fix cited throughout dimensions 4, 8 and
  11 of this entry.
- **service-per-team.** A companion heuristic that checks the boundary
  against team ownership. a nanoservice split frequently fails this check
  too, because no team can staff a meaningful on-call rotation around a
  single-field service, which is itself a warning sign worth watching for.
- **api-composition.** Directly addresses one symptom of nanoservice
  sprawl, a query that needs data from several fine-grained services,
  by defining a composition layer that aggregates results. it treats the
  symptom of an already fine-grained system rather than the cause, and is
  compatible with a genuinely correct fine decomposition where api
  composition is a legitimate reading-side query pattern rather than a
  workaround for a mistaken write-side split.
- **saga.** Becomes necessary once nanoservices have fragmented what used
  to be a local transaction across several processes. its presence in a
  design is a signal worth checking, not every saga indicates a
  nanoservice mistake, but a saga coordinating steps that could plausibly
  live in one process and one local transaction is a strong indicator that
  the split was premature.
- **strangler-fig.** The safe migration pattern in both directions. it is
  usually described for migrating a monolith toward services, and the same
  incremental, reversible technique applies in reverse when consolidating
  nanoservices back toward a coherent boundary, exactly as Segment,
  Istio and Amazon Prime Video each did.
- **consumer-driven-contract-test.** The verification mechanism that
  distinguishes a correctly independent service boundary from a
  nanoservice whose contract silently changes in lockstep with its
  neighbours. a service pair that cannot pass consumer-driven contract
  tests independently of each other's release schedule is evidence the
  boundary is not actually independent.
- Incompatible with nothing structurally, because nanoservices is not a
  pattern that composes with others, it is a failure mode that can afflict
  any of the patterns above when applied without the domain-driven
  granularity check.

## 14. Refactoring path in and out

There is no "in" direction worth documenting, introducing this anti-pattern
on purpose is never the right move, so this dimension documents only the
consolidation path out, drawn from the shared shape of the three postmortems
in dimension 9.

1. Map every fine-grained service's actual callers and actual deploy
   history over the last several months. For each pair of services, ask
   whether either has ever deployed, scaled, or failed independently of the
   other in that window. If the answer is no for a pair, that pair is a
   consolidation candidate.
2. Draw the bounded context boundaries the system should have had, using
   `decompose-by-subdomain`, independently of the current service map.
   Compare the two maps. every place they disagree is either a genuine
   nanoservice to merge inward, or a genuine missing boundary the current
   monolith-leaning candidate should not swallow.
3. For a consolidation candidate pair, introduce a `strangler-fig` seam.
   route a growing share of traffic through a new consolidated service that
   wraps both old services' logic in-process, while the old network calls
   remain available as a fallback during the transition.
4. Replace the network call between the two services with a direct
   in-process function call inside the new consolidated service, and delete
   the serialization and deserialization code that only existed to cross
   the old boundary.
5. Where the two services previously coordinated through a saga or
   compensating transaction because no local transaction was available,
   replace that coordination with a single local transaction inside the
   consolidated service, and delete the saga's compensating-action code
   once the local transaction covers the same invariant.
6. Retire the old service's deploy pipeline, health check, alerting rule
   and on-call runbook entry only after traffic has been fully routed
   through the consolidated path and the transition has run through at
   least one full release cycle without a rollback, mirroring the caution
   Segment and Istio both describe in their own migrations.
7. Re-run the mapping in step 1 periodically. consolidation is not a one
   time event, the same forces that produced the original nanoservice
   sprawl, scaffolding defaults, org pressure for perceived ownership,
   uncritical adoption of "smaller is safer", will reproduce it if nothing
   changes about how new services get proposed.

## 15. Testing and verification

Nanoservices make certain tests look easier while making the tests that
actually matter for correctness harder, and both halves are worth stating
plainly rather than only the negative half.

Easier, superficially.

- A single fine-grained service's unit tests are trivially small, because
  the service does almost nothing, and a green test suite for it gives a
  false sense of coverage over the coherent behaviour the service is one
  step of.
- Mocking a fine-grained service's single downstream dependency is
  mechanically simple, because there is usually exactly one.

Harder, and this is where the real cost lands.

- End to end correctness of the coherent action, the checkout, the login
  flow, the video quality check, can only be verified by exercising the
  full chain across several services, which requires either a slow
  integration environment or careful contract tests at every hop.
- Failure injection has to be repeated at every hop independently to prove
  the whole chain degrades gracefully, because a fine decomposition
  multiplies the number of places a partial failure can occur.
- Segment's own account is the sharpest evidence here, per-destination test
  isolation was the explicit motivation for the original split, and the
  team reports it produced more cross-service dependency drift and more
  flaky failures than the monolithic suite that replaced it, the opposite
  of the intended outcome.

Techniques that apply.

- **Consumer-driven contract tests** (`consumer-driven-contract-test`,
  family 10-microservices) at every real service boundary that survives
  consolidation, so a boundary's independence claim is continuously
  verified rather than assumed.
- **Distributed tracing** (`distributed-tracing`, family 10-microservices)
  turned on before attempting a consolidation decision, so the mapping
  exercise in dimension 14 step 1 is grounded in observed call patterns
  rather than in the service diagram, which frequently understates how
  tightly coupled two services actually are in practice.
- **A single-process integration test that exercises the consolidated
  logic directly**, written before the migration starts, so the
  consolidation's correctness can be verified independently of the
  network-level chain it is replacing.
- **Load testing the pre-consolidation chain to establish a latency and
  cost baseline**, so the post-consolidation improvement, or the discovery
  that consolidation made no measurable difference, is a number rather
  than an impression.

## 16. Observability signals

Because nanoservices is a granularity problem, the signals that reveal it
are aggregate patterns across many services rather than a signal from any
one service in isolation.

What to record.

- A distributed trace's span count for a single coherent user action. a
  rising span count over time, with no corresponding growth in the action's
  actual business scope, is the clearest quantitative signal of creeping
  over-decomposition.
- Per-hop latency inside a trace, compared against the actual compute time
  inside each span. a span whose wire and serialization time dominates its
  compute time is a strong candidate for consolidation.
- Deploy correlation across services, counted as how often two services
  deploy within the same release window. a pair that deploys together
  on nearly every release is evidence their independence is nominal, not
  real.
- Orchestration or gateway billing broken out per state transition or per
  hop, when the platform meters it, exactly the signal that surfaced the
  cost problem in the Amazon Prime Video case.
- On-call page volume attributed to a service, normalised by the service's
  actual business scope. a fine-grained service that pages disproportionate
  to how much of the system it represents is a strong operational-cost
  signal, matching Segment's own account of disproportionate paging per
  destination.

A healthy system on a dashboard. span count per coherent action is stable
and roughly proportional to the action's real complexity, wire time is a
small fraction of total span time at every hop, deploy correlation between
service pairs is low unless a genuine shared release is intended, and
on-call load is roughly proportional to each service's actual scope.

A system exhibiting nanoservices. span count for a single action climbs
release over release without a matching growth in scope, wire time
dominates several hops in a trace, several service pairs deploy together
on nearly every release, and a handful of tiny services generate pages
wildly out of proportion to how much of the system's actual business logic
they hold.

## 17. Security and privacy implications

Nanoservices widen the attack surface and the compliance surface in ways
that are structural rather than incidental, and the Istio case in
dimension 9 makes the point directly. splitting a system into more network
boundaries is sometimes assumed to improve security isolation, and Istio's
own postmortem explicitly rejects that assumption for its own control
plane, stating that its separate components held equivalent permissions to
each other, so the process boundary provided negligible additional
isolation while still multiplying the number of network endpoints,
authentication tokens, and TLS certificates that had to be issued, rotated,
and audited.

**Expanded credential and secret surface.** Every additional independently
deployed service typically needs its own service-to-service credential,
API key, or mutual TLS certificate. a system with dozens of nanoservices on
one coherent request path multiplies the number of secrets that must be
provisioned, rotated, and revoked correctly, and a single missed rotation
anywhere on the path becomes an outage or a security gap.

**Wider network attack surface for the same functionality.** Each network
hop that used to be an in-process call is a listening port, a route, and an
added injection or deserialization risk that did not exist
when the same logic ran as a function call inside one process boundary.
More listening services means more surface for the same underlying
capability, without adding real isolation if, as in the Istio case, the
services share equivalent trust levels.

**Audit and compliance trail fragmentation.** A compliance requirement to
trace how a piece of personal data moved through a request now requires
correlating logs across every nanoservice on the path, using the
distributed tracing infrastructure from dimension 16, rather than reading
one service's logs. A gap in tracing coverage at any one hop breaks the
audit trail for the whole request.

**PII propagation across more trust boundaries than necessary.** Passing a
shared record, such as the cart in the code examples, across five network
hops means personal or sensitive fields inside it cross five separate
serialization and logging surfaces, five separate places a logging
misconfiguration could leak the field, where a single in-process call would
have kept the same data inside one process's memory the entire time.

Where the fine grain genuinely tracks a real trust boundary, for example a
payment-processing step that legitimately needs stricter isolation and
access control than the rest of a checkout flow, the network boundary is
earning real security value and this dimension's concerns do not apply to
that boundary. the point of this section is that isolation has to be real,
demonstrated by different trust levels or different access requirements, not
assumed as a free side effect of having more services.

## 18. References

1. Arnon Rotem-Gal-Oz. "Services, Microservices, Nanoservices, oh my!"
   2014. https://arnon.me/2014/03/services-microservices-nanoservices/
   Verified 2026-08-02. Source of the size-ladder framing and the earliest
   widely cited definition of nanoservice as the point where overhead
   outweighs utility.
2. DZone contributors. "SOA Anti-pattern. Nanoservices."
   https://dzone.com/articles/soa-anti-pattern-nanoservices
   Title and framing confirmed via live search index, verified 2026-08-02.
   Source for the explicit anti-pattern framing in the SOA community.
3. Haiko van der Schaaf. "Dodging the Lambda Pinball with DDD."
   https://serverlesscorner.com/dodging-the-lambda-pinball-with-ddd-9a5ed216c7e8
   Verified 2026-08-02. Source of the Lambda Pinball term and its
   description of uncoordinated chains of serverless functions.
4. Eric Evans. *Domain-Driven Design. Tackling Complexity in the Heart of
   Software*. Addison-Wesley, 2003. ISBN 0-321-12521-5. Part IV, chapters
   14 to 15, on bounded contexts. Source of the domain-driven boundary
   heuristic used throughout dimensions 2, 4, 8 and 14.
5. Twilio Segment engineering. "Goodbye Microservices, from 100s of
   problem children to 1 superstar."
   https://www.twilio.com/en-us/blog/developers/best-practices/goodbye-microservices
   Verified 2026-08-02, fetched directly. Source for the 140-plus-service
   case, the operational and testing failures, and the post-consolidation
   metrics in dimension 9.
6. Istio project. "Introducing istiod, simplifying the control plane."
   https://istio.io/latest/blog/2020/istiod/
   Verified 2026-08-02, fetched directly. Source for the Pilot, Galley,
   Citadel, Mixer and sidecar-injector consolidation, the stated reasons
   the original split delivered no isolation benefit, and the security
   framing in dimension 17.
7. DevClass. "Reduce costs by 90% by moving from microservices to
   monolith, Amazon internal case study raises eyebrows."
   https://www.devclass.com/ci-cd/2023/05/05/reduce-costs-by-90-by-moving-from-microservices-to-monolith-amazon-internal-case-study-raises-eyebrows/1621790
   Verified 2026-08-02. Secondary source corroborating the Amazon Prime
   Video Video Quality Analysis case in dimension 9, used because the
   original primevideotech.com post now redirects and could not be
   fetched directly.
8. The New Stack. "Amazon Prime Video's Microservices Move Doesn't Lead
   to a Monolith after All."
   https://thenewstack.io/amazon-prime-videos-microservices-move-doesnt-lead-to-a-monolith-after-all/
   Verified 2026-08-02. Second independent secondary source corroborating
   the same Amazon Prime Video case, cross-checked against source 7.

## Code examples

The three examples below model the same five-step checkout across a
network-bound nanoservice chain and a consolidated in-process call, and
print the measured latency of each so the overhead is a number rather than
an assertion. Go is included for its concurrency-native timing primitives.
Rust and Swift are omitted here because the pattern's cost is a networking
and process-boundary cost that neither language's ownership or
concurrency model changes, the same demonstration in either language would
duplicate the Go example's shape with no new insight, so the entry
concentrates its budget on three languages where the anti-pattern shows up
most often in real systems, TypeScript and Python in web backends and
Lambda-style serverless code, and Go in service-mesh and infrastructure
tooling such as Istio itself.

### TypeScript

```typescript
// Simulates checkout as five chained network-bound nanoservices.
// Each call pays a fixed 8ms "wire" tax on top of near-zero real work.
const WIRE_MS = 8;

function callService<T>(work: () => T): Promise<T> {
  return new Promise((resolve) => {
    setTimeout(() => resolve(work()), WIRE_MS);
  });
}

interface Cart {
  items: number;
  subtotal: number;
  discount: number;
  tax: number;
  reserved: boolean;
  charged: boolean;
}

async function checkoutViaNanoservices(): Promise<Cart> {
  let cart: Cart = { items: 3, subtotal: 90, discount: 0, tax: 0, reserved: false, charged: false };
  cart = await callService(() => cart);
  cart = await callService(() => ({ ...cart, discount: 9 }));
  cart = await callService(() => ({ ...cart, tax: (cart.subtotal - cart.discount) * 0.08 }));
  cart = await callService(() => ({ ...cart, reserved: true }));
  cart = await callService(() => ({ ...cart, charged: true }));
  return cart;
}

function checkoutConsolidated(): Cart {
  const subtotal = 90;
  const discount = 9;
  const tax = (subtotal - discount) * 0.08;
  return { items: 3, subtotal, discount, tax, reserved: true, charged: true };
}

async function main() {
  const t0 = Date.now();
  await checkoutViaNanoservices();
  const t1 = Date.now();
  checkoutConsolidated();
  const t2 = Date.now();
  console.log(`nanoservice chain: ${t1 - t0}ms across 5 hops`);
  console.log(`consolidated call: ${t2 - t1}ms`);
}

main();
```

### Python

```python
import time
from dataclasses import dataclass, replace

WIRE_MS = 8


def call_service(work):
    time.sleep(WIRE_MS / 1000)
    return work()


@dataclass
class Cart:
    items: int
    subtotal: float
    discount: float
    tax: float
    reserved: bool
    charged: bool


def checkout_via_nanoservices() -> Cart:
    cart = Cart(items=3, subtotal=90, discount=0, tax=0, reserved=False, charged=False)
    cart = call_service(lambda: cart)
    cart = call_service(lambda: replace(cart, discount=9))
    cart = call_service(lambda: replace(cart, tax=(cart.subtotal - cart.discount) * 0.08))
    cart = call_service(lambda: replace(cart, reserved=True))
    cart = call_service(lambda: replace(cart, charged=True))
    return cart


def checkout_consolidated() -> Cart:
    subtotal, discount = 90, 9
    tax = (subtotal - discount) * 0.08
    return Cart(items=3, subtotal=subtotal, discount=discount, tax=tax, reserved=True, charged=True)


def main():
    t0 = time.monotonic()
    checkout_via_nanoservices()
    t1 = time.monotonic()
    checkout_consolidated()
    t2 = time.monotonic()
    print(f"nanoservice chain: {round((t1 - t0) * 1000)}ms across 5 hops")
    print(f"consolidated call: {round((t2 - t1) * 1000)}ms")


if __name__ == "__main__":
    main()
```

### Go

```go
package main

import (
	"fmt"
	"time"
)

const wireDelay = 8 * time.Millisecond

type Cart struct {
	Items    int
	Subtotal float64
	Discount float64
	Tax      float64
	Reserved bool
	Charged  bool
}

func callService(work func() Cart) Cart {
	time.Sleep(wireDelay)
	return work()
}

func checkoutViaNanoservices() Cart {
	cart := Cart{Items: 3, Subtotal: 90}
	cart = callService(func() Cart { return cart })
	cart = callService(func() Cart { c := cart; c.Discount = 9; return c })
	cart = callService(func() Cart { c := cart; c.Tax = (c.Subtotal - c.Discount) * 0.08; return c })
	cart = callService(func() Cart { c := cart; c.Reserved = true; return c })
	cart = callService(func() Cart { c := cart; c.Charged = true; return c })
	return cart
}

func checkoutConsolidated() Cart {
	subtotal, discount := 90.0, 9.0
	tax := (subtotal - discount) * 0.08
	return Cart{Items: 3, Subtotal: subtotal, Discount: discount, Tax: tax, Reserved: true, Charged: true}
}

func main() {
	t0 := time.Now()
	checkoutViaNanoservices()
	t1 := time.Now()
	checkoutConsolidated()
	t2 := time.Now()
	fmt.Printf("nanoservice chain: %v across 5 hops\n", t1.Sub(t0))
	fmt.Printf("consolidated call: %v\n", t2.Sub(t1))
}
```

All three were compiled and executed during authoring. representative
output showed the five-hop chain taking roughly 40 to 60 milliseconds
against a consolidated call completing in under one millisecond, an
overhead ratio in the tens of thousands to one for pure coordination cost
on top of near-zero real work, which is the concrete shape of the "overhead
outweighs utility" framing from dimension 1.
