---
name: Service-Oriented Architecture
slug: service-oriented-architecture
family: 05-architectural
category: Architectural
aliases: [SOA, Enterprise SOA, WS-* SOA]
first_described: "IBM and industry consortia, late 1990s, popularized through W3C Web Services Architecture, 2004"
maturity: contested
related: [microservices, api-gateway, service-registry, message-bus, esb, saga]
incompatible_with: [big-ball-of-mud]
verified: 2026-08-02
---

# Service-Oriented Architecture

## 1. Name, aliases, and lineage

The canonical name is Service-Oriented Architecture, almost always shortened to
SOA. The term entered wide industry use in the late 1990s and became a
standards-body concern in the early 2000s, when the W3C Web Services
Architecture Working Group published its Working Group Note defining a
service as "a software system designed to support interoperable
machine-to-machine interaction over a network," interacting through a
machine-processable interface description (World Wide Web Consortium, Web
Services Architecture, W3C Working Group Note, 11 February 2004,
https://www.w3.org/TR/ws-arch/, verified 2026-08-02). That note treats SOA as
an architectural approach in which distributed applications interoperate
through standardized services, described by an interface, bound by a
contract, and reachable independently of the platform that implements them.

Thomas Erl wrote the two books most cited as SOA's popular canon. *Service-
Oriented Architecture. Concepts, Technology, and Design*, Prentice Hall, 2005,
and *SOA. Principles of Service Design*, Prentice Hall, 2007. Erl's books
codified eight design principles that SOA practitioners still quote from
memory. In order, they are standardized service contract, service loose
coupling, service abstraction, service reusability, service autonomy,
service statelessness, service discoverability, and service composability.

Martin Fowler's bliki entry "Service Oriented Ambiguity" argues that by the
mid-2000s the term had split into at least four incompatible meanings in
practice. Exposing functionality through web services regardless of internal
design. Replacing applications entirely with a set of core services plus UI
aggregators. Any system-to-system communication over a standard structure
such as XML over HTTP. And asynchronous document-oriented messaging as a
cheaper alternative to enterprise application integration suites. Fowler
concludes that "SOA has turned into a semantics-free concept," on a par with
"components" and "architecture" as words that stopped doing useful work
(Martin Fowler, "Service Oriented Ambiguity,"
https://martinfowler.com/bliki/ServiceOrientedAmbiguity.html, verified
2026-08-02). This entry's maturity field is set to contested for exactly
that reason. The pattern is real, widely deployed, and still underneath most
large distributed systems, but the label attached to it has never had one
agreed meaning, and any two engineers using the word SOA in the same
sentence may be describing different architectures.

A working definition that survives the ambiguity, and the one this entry
uses throughout, follows. SOA is an architectural style in which business
capability is exposed as a set of independently deployable services, each
with a published, versioned interface, each reachable over a network
protocol, composed together to build applications rather than linked as
libraries inside one process. What varies across implementations is how the
interface is described (WSDL and SOAP, or a REST contract, or an IDL such as
Thrift or Protocol Buffers), how services find each other (a registry, DNS,
a service mesh, hardcoded configuration), and how much shared infrastructure
sits between them (a heavyweight enterprise service bus, a thin API
gateway, or nothing at all).

## 2. Problem and context

A monolithic application starts as the fastest way to ship. One codebase,
one deployment, one database, one team can move a feature from idea to
production without coordinating with anyone else. That model breaks down
along three axes as an organization and its software both grow.

The first axis is team scaling. When ten engineers work in one codebase,
code review and shared understanding keep everyone roughly in sync. When two
hundred engineers work in the same codebase, every deploy risks breaking
someone else's unrelated feature, the build takes longer than a coffee
break, and any two teams touching the same module become a source of merge
conflicts and cross-team meetings that exist only to negotiate who changes
what. Randy Shoup, describing eBay's growth, put it as related pieces of
functionality belonging together and unrelated pieces belonging apart, then
scaling each concern on its own resources (Randy Shoup, "The eBay
Architecture," InfoQ, 27 May 2008,
https://www.infoq.com/articles/ebay-scalability-best-practices/, verified
2026-08-02, describing roughly sixteen thousand application servers
organized into 220 pools by business function, and roughly a thousand
logical databases across four hundred physical hosts, each partitioned by
data domain such as user data, item data, and purchase data).

The second axis is deployment and blast radius. In a monolith, a bug in the
recommendations module can crash the checkout module, because they share one
process and one failure domain. Uber described exactly this failure mode
after its own transition away from a small number of monolithic services
around 2012 to 2013. A single regression could bring down the whole system,
and every deployment was slow, painful, and often rolled back, which forced
the company toward independently deployable services as its engineering
headcount grew from tens to hundreds (Uber Engineering, "Rethinking
Microservice Architecture as Uber Grows," uber.com blog,
https://www.uber.com/blog/microservice-architecture/, verified 2026-08-02).
By the time that article was written, Uber ran roughly 2,200 critical
services and had begun grouping them into domains to fight a different
problem SOA and its later cousin microservices both create, diagnosing an
incident that spans fifty services across a dozen teams.

The third axis is heterogeneous technology and organizational ownership. A
payments team may need the transactional guarantees of a relational database
and a JVM runtime tuned for low-latency numeric work, while a
recommendations team wants a Python or Go service running against a
document store, and a search team wants an entirely separate indexing
pipeline. A monolith forces every team onto one language, one release
schedule, and one release train. SOA's context is exactly the situation where
that forcing function has become the bottleneck, business capability maps
cleanly onto separable units of ownership, and the cost of network calls
between those units is worth paying to get independent deployment,
independent scaling, and independent technology choice back.

SOA is not a fix for a system that is simply badly organized inside one
process. Splitting a poorly modularized monolith across a network does not
improve its modularity, it adds latency, partial failure, and distributed
debugging on top of the same tangled dependencies, a failure mode this entry
returns to in dimension 11.

## 3. Forces

- **Coupling versus coordination cost.** Splitting a system into services
  reduces code-level coupling between teams, at the direct cost of runtime
  coupling through network calls, and the indirect cost of coordinating
  contract changes across team boundaries. A monolith trades this the other
  way. Near-zero coordination cost for changing an internal function
  signature, at the cost of every team sharing one deployment.
- **Latency and reliability versus independent scaling.** An in-process
  function call takes nanoseconds and fails only if the whole process fails.
  A service call over a network takes milliseconds at best, can time out,
  can partially fail, and needs its own retry, circuit-breaker, and
  observability story. In exchange, each service can be scaled, deployed,
  and operated on its own schedule, which a monolith cannot offer regardless
  of how well factored its internal modules are.
- **Consistency versus availability under partition.** Inside one process
  and one database, a transaction can span every table with ACID
  guarantees. Once business capability crosses a service boundary, a single
  ACID transaction across two services' databases is either unavailable in
  practice, two-phase commit across services is slow and fragile once transaction volume grows,
  or abandoned entirely in favour of eventual consistency, compensating
  actions, and the saga pattern. SOA does not resolve this tension, it
  exposes it, because the service boundary is drawn at the point where a
  shared database stops being an option.
- **Operability and cognitive load versus capability isolation.** Every
  additional service is another thing to deploy, monitor, secure, version,
  and keep alive on a pager rotation. A set of two hundred fine-grained
  services multiplies operational surface area even when it reduces
  per-service cognitive load, which is precisely the paradox Uber names
  when it describes tracing an incident across fifty services and a dozen
  teams.
- **Cost.** Running N services means N sets of infrastructure, N sets of
  health checks, N TLS certificates, and often N times the idle-capacity
  overhead compared to one process, unless the platform amortizes that cost
  with shared infrastructure such as a service mesh or a platform team. SOA
  favours organizational advantage and technology flexibility over
  infrastructure cost efficiency, and that trade only pays off once
  team-scaling pain exceeds the added operational bill.
- **Team topology.** SOA's benefits are largest when a service boundary maps
  onto a team boundary, so that the team owning the service also owns its
  data, its interface, and its on-call rotation end to end. When a service
  boundary cuts across a team, or when one team owns twenty services, the
  supposed autonomy gain collapses into cross-team coordination again, only
  rerouted through network calls instead of code review.

This entry treats coupling reduction, independent deployability, and
technology and team autonomy as the forces SOA favours, and it treats
latency, partial failure, and operational multiplication as the forces it
knowingly sacrifices.

## 4. Applicability and non-applicability

Reach for a service-oriented architecture when the following hold together,
not individually.

- The organization has grown past the size at which one team can safely own
  the whole codebase, and business capability can be partitioned along
  domain lines that map to team ownership.
- Different parts of the system have genuinely different scaling profiles,
  for example a read-heavy catalog service and a write-heavy order service,
  so that scaling them independently saves real infrastructure cost.
- Different parts of the system have genuinely different technology needs,
  a machine learning inference service in Python next to a low-latency
  matching engine in Go or Rust, and forcing one runtime onto both is a real
  constraint, not a hypothetical one.
- The organization can afford, or already has, the operational platform a
  set of services requires. Service lookup, centralized logging and
  tracing, a deployment pipeline per service, and an on-call structure that
  can support many independently failing components.
- Regulatory, security, or data-residency requirements demand that certain
  capabilities run in isolated processes, address spaces, or even
  jurisdictions, which a monolith cannot express.

Do NOT reach for SOA in these situations, and the reason matters as much as
the rule.

- **A small team, or a system with one owner.** The coordination problem SOA
  solves does not exist yet. Splitting a two-person team's codebase into
  five services multiplies deployment and monitoring work for zero
  organizational benefit, and the team pays network latency for calls that
  used to be free.
- **A system whose modules are tightly coupled by data.** If two supposed
  services need to read and write the same rows in the same transaction to
  stay correct, drawing a network boundary between them does not remove the
  coupling, it removes the transaction that used to keep them correct and
  replaces it with distributed consistency work the team has not yet prepared to
  build. Fix the internal modularity first.
- **A performance-critical hot path measured in microseconds or single-digit
  milliseconds.** Network calls add latency a function call does not, and
  no amount of architecture discipline removes the physics of a round trip.
- **When the team has not first tried modularizing within one process.** A
  well-factored monolith with clean internal module boundaries, sometimes
  called a modular monolith, gets most of the code-organization benefit of
  SOA with none of the distributed-systems cost, and it is the correct
  intermediate step for most teams before crossing a process boundary.
- **When SOA is being adopted because it is fashionable rather than because
  a named force above is actually present.** This is the most common
  real-world misuse, covered in depth in dimension 11.
- **When the organization cannot yet operate one service reliably**, because
  it lacks monitoring, alerting, or an incident process. Adding N services
  on top of that gap multiplies the blast radius of the gap rather than
  fixing it.

## 5. Structure

- **Service Provider.** The autonomous unit that implements a piece of
  business capability, owns its own data store, and exposes that capability
  only through its published interface. It never allows another service to
  reach directly into its database.
- **Service Contract (Interface).** The machine-readable description of what
  the service offers. Its operations, the shape of its inputs and outputs,
  and the semantics it promises. In WS-\* SOA this is a WSDL document. In
  REST or gRPC based SOA it is an OpenAPI document or a Protocol Buffers
  schema. The contract is the only thing a consumer is allowed to depend on.
- **Service Consumer.** Any component, another service, a client
  application, or a batch job, that invokes a service strictly through its
  published contract, without any knowledge of the provider's internal
  implementation, language, or data model.
- **Service Registry (Lookup Mechanism).** Where a consumer finds a
  provider's current network location and contract version. This can be a
  formal UDDI registry in classic WS-\* SOA, a DNS-based service directory,
  or a runtime lookup mechanism inside a service mesh.
- **Enterprise Service Bus, or a lighter API gateway.** Optional shared
  infrastructure sitting between consumers and providers that can perform
  message routing, protocol translation, orchestration, and policy
  enforcement such as authentication and rate limiting. Classic
  vendor-driven SOA of the 2000s made the ESB mandatory and often
  overloaded it with business logic. Modern service-oriented systems
  commonly replace the heavyweight ESB with a thin API gateway plus
  point-to-point or event-based communication, which is exactly the
  distinction the microservices movement drew against 2000s-era SOA.
- **Orchestrator, or a choreography of events.** The component, or the
  absence of one, that coordinates a business process spanning multiple
  services. Orchestration centralizes the sequence of calls in one
  controlling service. Choreography distributes it as a chain of events
  each service reacts to independently, with no single component holding
  the whole sequence.

## 6. ASCII structure diagram

```
                         +----------------------+
                         |   Service Registry    |
                         |  (contracts, versions, |
                         |   network locations)   |
                         +-----------+------------+
                                     ^
                        register /   |   discover
                        publish  |   |
                                 v   v
+----------------+      +--------------------+      +------------------+
| Service         |----->|   API Gateway /    |<-----| Service          |
| Consumer         |      |   Enterprise       |      | Consumer          |
| (client app,     |      |   Service Bus       |      | (another service) |
|  batch job)       |<-----|   (routing, auth,   |----->|                  |
+----------------+      |   policy, optional) |      +------------------+
                         +----------+---------+
                                    |
                +-------------------+-------------------+
                |                   |                    |
                v                   v                    v
     +--------------------+ +--------------------+ +--------------------+
     | Service Provider A  | | Service Provider B  | | Service Provider C  |
     | (e.g. Orders)        | | (e.g. Inventory)     | | (e.g. Payments)      |
     |  Contract. OrderAPI  | |  Contract. StockAPI  | |  Contract. PayAPI    |
     |  Owns. orders DB     | |  Owns. stock DB      | |  Owns. ledger DB     |
     +--------------------+ +--------------------+ +--------------------+
```

## 7. Dynamics

Two runtime shapes cover almost every real SOA. Orchestrated request flow,
and event-driven choreography. Both are shown below for the same example, a
consumer places an order that must check inventory and charge a payment
method.

```
Orchestrated flow (an Order service coordinates the whole process):

Consumer         Order Service       Inventory Svc      Payment Svc
   |                   |                    |                 |
   |--place order----->|                    |                 |
   |                   |--reserve stock---->|                 |
   |                   |<--reserved---------|                 |
   |                   |--charge card------------------------>|
   |                   |<--charged-----------------------------|
   |                   |--confirm order (writes own DB)        |
   |<--order confirmed-|                                       |
   |                   |                                       |
   | on failure, Order Service issues compensating calls:      |
   |                   |--release stock---->|                 |
   |                   |--refund------------------------------>|
```

```
Choreographed flow (each service reacts to events, no central coordinator):

Order Service      Event Bus       Inventory Svc      Payment Svc
     |                  |                 |                  |
     |--OrderPlaced---->|                 |                  |
     |                  |--OrderPlaced--->|                  |
     |                  |                 |--reserve stock   |
     |                  |<--StockReserved-|                  |
     |                  |--StockReserved----------------->   |
     |                  |                 |     charge card  |
     |                  |<--PaymentCharged-----------------|
     |<--PaymentCharged-|                 |                  |
     | Order Service marks order confirmed on PaymentCharged  |
```

Orchestration keeps the sequence of a business process visible in one place
at the cost of a coordinating service becoming a bottleneck and a single
point of coupling to every downstream service's contract. Choreography
removes that coordinator and lets services evolve independently, at the
cost of the overall process sequence existing nowhere as readable code,
which makes debugging a stuck order a matter of reconstructing history from
distributed logs and correlation identifiers.

## 8. Implementation variants

- **WS-\* SOA (SOAP, WSDL, UDDI).** The 2000s enterprise variant. Contracts
  are WSDL documents, messages are XML SOAP envelopes, and lookup is
  formally UDDI-based. Strongly typed, heavily tooled by vendors such as
  IBM WebSphere and Oracle SOA Suite, and the primary target of Fowler's
  ambiguity critique because vendors marketed the ESB and the WS-\* stack as
  synonymous with SOA itself, when SOA is the architectural idea and WS-\*
  is one, now largely legacy, way to implement it.
- **REST-based SOA.** Services expose resources over HTTP with an OpenAPI or
  similar contract, JSON payloads, and standard HTTP semantics for caching,
  idempotency, and status codes. This is the dominant style for
  internet-facing and greenfield internal services since roughly the early
  2010s, and it is what most engineers mean today when they say
  "service-oriented" without qualification.
- **RPC-based SOA (gRPC, Thrift, Avro RPC).** Services expose typed
  procedure calls over a binary protocol with a schema-defined interface
  description language, favoring low latency and strong typing over
  REST's resource semantics. Common inside an organization's own network
  where every consumer is also a service the organization controls.
- **Event-driven / message-oriented SOA.** Services communicate primarily
  through asynchronous events on a broker such as Kafka or RabbitMQ rather
  than synchronous request and response. This variant favours availability
  and decoupling in time, at the cost of the orchestration visibility
  described in dimension 7, and it is the natural implementation for the
  choreography dynamic.
- **Microservices.** Often presented as SOA's successor rather than a
  variant, but the two share the same underlying structure from dimension
  5. James Lewis and Martin Fowler describe microservices as an approach to
  developing an application as a suite of small services, each running in
  its own process and communicating with lightweight mechanisms, built
  around business capabilities and independently deployable (James Lewis
  and Martin Fowler, "Microservices," martinfowler.com, 25 March 2014,
  https://martinfowler.com/articles/microservices.html, verified
  2026-08-02). The practical distinction the industry settled on is scale
  and governance, not structure. Microservices push toward smaller service
  granularity, per-service databases as a hard rule rather than a
  guideline, decentralized data management, and "smart endpoints, dumb
  pipes" in place of the heavyweight, business-logic-carrying ESB that
  characterized 2000s vendor SOA.

## 9. Known production uses

- **eBay**, described by Distinguished Architect Randy Shoup. Roughly
  sixteen thousand application servers partitioned into 220 pools by
  business function such as selling, bidding, and search, each scaled
  independently, backed by roughly a thousand logical databases across four
  hundred physical hosts partitioned by data domain (Randy Shoup, "The eBay
  Architecture," InfoQ, 27 May 2008,
  https://www.infoq.com/articles/ebay-scalability-best-practices/, verified
  2026-08-02).
- **Uber**, which moved off two monolithic services around 2012 to 2013
  toward independently deployable services as engineering headcount grew,
  reaching roughly 2,200 critical services by 2020, then layering a
  domain-oriented grouping on top to manage cross-service incident
  complexity (Uber Engineering, "Rethinking Microservice Architecture as
  Uber Grows," uber.com blog,
  https://www.uber.com/blog/microservice-architecture/, verified
  2026-08-02).
- **The wider W3C-standardized web services stack**, in which SOAP,
  WSDL, and the Web Services Architecture note formed the basis of banking,
  insurance, and government integration platforms through the 2000s and
  2010s, still running in large financial institutions today as the
  interoperability layer between legacy mainframe systems and newer
  services (World Wide Web Consortium, Web Services Architecture, W3C
  Working Group Note, 11 February 2004, https://www.w3.org/TR/ws-arch/,
  verified 2026-08-02).
- **Amazon**, widely documented across the industry, beginning in the early
  2000s, as having mandated that every internal team expose its
  functionality only through service interfaces rather than direct data
  access, a decision credited as a precursor to both AWS and the broader
  industry shift toward service-oriented systems. This entry marks this
  claim as widely reported rather than independently primary-sourced here,
  because the original internal mandate is not itself a published document
  and the most commonly cited retelling, Steve Yegge's internal Google
  memo republished publicly in 2011, could not be re-verified against a
  live source in this pass. Treat the Amazon example as strong secondary
  agreement, not a directly cited primary claim.

## 10. Consequences

Positive.

- Teams can deploy, scale, and choose runtime technology for their own
  service without waiting on, or coordinating a release train with, every
  other team.
- A failure in one service does not automatically crash the whole system,
  provided consumers implement timeouts and fallback behaviour, which turns
  an all-or-nothing failure mode into a partial-degradation one.
- Business capability becomes independently testable and independently
  able to scale, so a read-heavy catalog service can run on ten cheap replicas
  while a write-heavy ledger service runs on two expensive, carefully
  guarded instances.
- New capability can often be added as a new service with its own data
  store, without a schema migration on a shared database used by
  unrelated features.

Negative.

- Every call across a service boundary becomes a network call, with the
  latency, timeout handling, and partial-failure handling that a function
  call never needed, and this cost compounds across a request that fans out
  to several services.
- Distributed transactions across services either require heavyweight
  coordination protocols the industry has largely abandoned, or force the
  team to design compensating actions and eventual consistency into every
  cross-service business process, work a single-database monolith never
  required.
- Operational surface area multiplies. N services require N deployment
  pipelines, N sets of health checks and dashboards, N places a
  misconfigured retry policy can create a failure that spreads to every downstream caller, and a shared
  platform team or heavy automation investment to keep that from becoming
  unmanageable.
- Debugging a single business transaction now means correlating logs,
  traces, and timestamps across every service the request touched, which
  is qualitatively harder than reading a stack trace in one process.
- A poorly drawn service boundary produces the worst of both worlds,
  network latency and partial failure, with none of the loose coupling SOA
  is supposed to deliver, because two services still change together on
  every release.

## 11. Failure modes and misuse

Judgement note. This dimension draws on widely reported industry experience
rather than a single citable source for each symptom. The pattern of these
failures is well established in practice even where no individual incident
is named here.

- **The distributed monolith.** Symptom observed. Every service must be
  deployed in lockstep, and a single feature routinely requires
  coordinated releases of four or five services on the same day. Cause.
  The service boundary was drawn along technical lines, such as splitting
  a create-read-update-delete flow into a "read service" and a "write
  service," rather than along a business capability line that keeps
  related change together. Fix. Redraw the boundary around a cohesive
  business capability, and if that means merging two services back into
  one, do it. A smaller number of correctly bounded services beats a
  larger number of falsely independent ones.
- **The shared database anti-pattern.** Symptom observed. Two or more
  services read and write the same tables, and a schema change in one team
  breaks a query in another team's service with no compile-time warning.
  Cause. Services were split at the process level while the data model
  stayed centralized, usually to avoid the real work of deciding which
  service owns which data. Fix. Assign single ownership of each table or
  collection to exactly one service, and require every other service to go
  through that owner's published interface, even for reads.
- **The god ESB.** Symptom observed. The enterprise service bus contains
  business logic, such as data transformation rules specific to one
  domain, and a change to that one domain requires redeploying the shared
  bus that every other service depends on. An outage in one team's logic
  becomes an outage for every team. Cause. The bus was treated as a place
  to put shared behaviour rather than pure routing and protocol
  translation. Fix. Push business logic back into the owning service, and
  restrict the bus, or its modern replacement, an API gateway, to
  cross-cutting infrastructure concerns such as authentication, rate
  limiting, and routing.
- **SOA by decree without operational readiness.** Symptom observed. An
  organization adopts a service-per-team mandate before it has centralized
  logging, tracing, or an on-call process, and incidents that used to take
  an hour to diagnose in a single log file now take a day of cross-team
  Slack threads to reconstruct. Cause. The organizational decision to
  split services outran the platform investment needed to operate many of
  them. Fix. Build the observability and deployment platform first, or in
  lockstep, never after.
- **Chatty services.** Symptom observed. A single user-facing request
  triggers a synchronous fan-out of ten or more downstream service calls,
  and a small increase in traffic causes tail latency to spike far faster
  than throughput would predict. Cause. A capability that should have
  lived inside one service was split too finely, so that satisfying one
  logical operation now requires several round trips that used to be one
  in-process call. Fix. Consider coarser-grained service boundaries, batch
  or aggregate calls at a gateway layer, or move the capability back
  behind one boundary.
- **Versioning by breaking change.** Symptom observed. A provider ships a
  contract change that removes or renames a field, and every consumer
  that had not yet updated starts failing in production with no warning.
  Cause. The service contract was treated as an internal implementation
  detail rather than a public, versioned promise. Fix. Version the
  contract explicitly, support the previous version for a defined
  deprecation window, and treat a breaking contract change with the same
  discipline as a database migration.

## 12. Trade-off matrix

| Force | Service-Oriented Architecture | Monolith (single deployable) | Microservices |
|---|---|---|---|
| Deployment independence | High. Each service ships on its own schedule | None. One deploy for the whole system | Highest. Fine-grained, per-service deploys |
| Typical granularity | Coarse to medium, aligned to a business domain | N/A, one unit | Fine, often one capability per service |
| Data ownership | Usually one database per service, sometimes shared legacy stores | One shared database | Strict, one database per service by convention |
| Cross-cutting infrastructure | Often a heavyweight ESB carrying orchestration and transformation | None needed | Thin API gateway, smart endpoints and dumb pipes |
| Transaction model | Distributed, sagas or compensation common | Local ACID transactions | Distributed, sagas the default expectation |
| Team autonomy | Medium to high, depends on governance model | Low, shared codebase and release train | High, explicitly organized around independent teams |
| Operational cost | Medium to high | Lowest | Highest, many small moving parts |
| Best fit | Medium to large organizations with an existing platform investment | Small teams, early-stage products, tight latency budgets | Large organizations that need fine-grained independent scaling and deployment |

## 13. Related and incompatible patterns

- **Microservices.** A stricter, finer-grained descendant of SOA that
  hardens two of SOA's optional practices into hard rules, one database per
  service, and thin, mostly business-logic-free infrastructure between
  services rather than a heavyweight ESB. Every microservices system is a
  service-oriented architecture, not every service-oriented architecture is
  fine-grained enough, or disciplined enough about data ownership, to be
  called microservices.
- **API Gateway.** The lightweight modern replacement for the classic
  ESB's routing responsibilities, sitting at the edge of a set of services
  to handle authentication, rate limiting, and request routing without
  absorbing business logic. Composes directly with SOA as the entry point
  consumers actually talk to.
- **Service Registry / Service Lookup.** The mechanism, whether a formal
  UDDI registry, DNS-based lookup, or a service mesh's control plane,
  that lets a consumer find a provider's current network location. Without
  it, service locations must be hardcoded, which defeats independent
  deployability.
- **Saga.** The pattern that replaces a distributed transaction across
  services with a sequence of local transactions plus compensating actions
  for rollback, directly addressing the consistency force named in
  dimension 3. Any SOA whose business processes span multiple services'
  data almost always needs a saga somewhere.
- **Enterprise Service Bus (as a component, not the architecture).** A
  specific, often over-scoped implementation choice for the shared
  infrastructure box in dimension 5, and the component most responsible for
  the "god ESB" failure mode when it accumulates business logic it should
  never have held.
- **Big Ball of Mud.** Listed as incompatible because it is SOA's failure
  state under dimension 11's shared-database and chatty-service misuses. A
  set of services that has lost boundary discipline degrades into a
  distributed version of a big ball of mud, with the added cost of network
  calls on top of the tangled dependencies.

## 14. Refactoring path in and out

Introducing SOA into a monolith, step by step.

1. First modularize inside the existing process. Identify a cohesive
   business capability, such as inventory management, and enforce that
   only its own module's code touches its own tables, even while
   everything still runs in one deployable. This is the modular monolith
   step, and it should reveal most of the coupling problems a network
   boundary would later expose, while they are still cheap to fix.
2. Pick the module with the clearest independent scaling or ownership need,
   not simply the easiest one to extract, and define its public contract
   first. What operations does it expose, and to whom. Write that contract
   down before writing the extraction code.
3. Stand up the new service behind the existing monolith, initially calling
   it internally through the same contract that will later be exposed over
   the network, using a strangler-fig approach so that traffic migrates
   gradually rather than in one cutover.
4. Give the new service its own datastore, and migrate its data out of the
   shared database, updating every remaining caller to go through the
   service's interface rather than the old shared tables. This step is
   usually the hardest and most time-consuming part of the whole
   extraction, and it is also the step most teams are tempted to skip,
   which produces the shared-database anti-pattern from dimension 11.
5. Add the operational scaffolding the new service needs before it takes
   production traffic on its own. Health checks, structured logging,
   distributed tracing correlation, and a deployment pipeline separate
   from the monolith's.
6. Repeat for the next capability, only when the organizational or
   technical force from dimension 3 that justifies the extraction is
   actually present for that capability, not on a fixed schedule.

Removing SOA, or merging services back, when the split has stopped earning
its place.

1. Identify services that always deploy together, always fail together, or
   are owned by the same team with no independent scaling need. These are
   the distributed-monolith symptom from dimension 11 and the strongest
   signal that a merge will help.
2. Consolidate their datastores first if they were only nominally separate,
   or plan the data migration carefully if they hold genuinely independent
   data that a merged service will now own together.
3. Fold the services' code into one deployable, replacing what used to be
   network calls between them with direct function calls, and delete the
   now-redundant serialization, retry, and timeout handling that existed
   only because of the network boundary.
4. Update consumers of the old, separate contracts to call the merged
   service's contract instead, maintaining the old routes as a thin
   compatibility shim during a deprecation window if external consumers
   exist.

## 15. Testing and verification

Judgement note. Testing practice below reflects common industry technique
rather than a single citable source for each item.

What becomes easier because of SOA. Each service can be tested in complete
isolation with a fast, focused test suite, because its boundaries are
already explicit contracts rather than implicit internal function calls. A
team can run its own service's full test suite on every commit without
needing the rest of the system running at all.

What becomes harder. Verifying that the system as a whole behaves correctly
requires testing across service boundaries, and a full full-system
environment with every service running is often slow, flaky, and expensive
to maintain.

- **Contract testing** (for example Pact-style consumer-driven contracts)
  verifies that a provider's interface still satisfies what its consumers
  actually depend on, without needing every consumer and provider running
  together, and it is the most effective testing technique for a set of
  services because it catches the versioning failure from dimension 11
  before a breaking change reaches production.
- **Service virtualization and test doubles** let a consumer's test suite
  run against a stub or mock of a downstream provider rather than the real
  network dependency, keeping unit and integration tests fast and
  deterministic.
- **Component tests** exercise one service's real code against a real or
  in-memory version of its own datastore, with every external dependency
  stubbed, verifying the service's behaviour without the cost of a full
  full-system environment.
- **A small number of full-system tests**, deliberately kept few, cover the
  handful of business-critical flows that genuinely span multiple
  services, accepting that these tests are slower and more brittle in
  exchange for catching integration problems contract tests alone cannot.
- **Fault-injection testing** verifies that a consumer degrades
  gracefully, rather than spreading a failure to its callers, when a downstream service
  times out or returns an error, which is the direct test for the
  reliability force traded away in dimension 3.

## 16. Observability signals

A healthy set of services shows, per service, low and stable p50, p95, and
p99 latency for its own operations, a request success rate close to one
hundred percent with errors attributable to genuine client mistakes rather
than internal failures, and a deployment frequency the team controls
independently of any other team's release schedule.

Distributed tracing, propagating a correlation identifier through every
service a single request touches, is the signal that most directly answers
the question a monolith's stack trace used to answer for free. Which
service, in which call, caused this failure or this latency spike. Without
it, diagnosing a cross-service problem degenerates into manually
correlating timestamps across separate log stores, which is exactly the
operational cost Uber's engineering team named when describing incidents
spanning fifty services.

Warning signs of the failure modes in dimension 11 are directly visible in
these same signals. A cluster of services whose deploy timestamps are
always within minutes of each other is the distributed-monolith symptom.
A service whose call graph fans out to ten or more synchronous downstream
calls for a single incoming request is the chatty-services symptom. A
sudden spike in one service's error rate that appears, delayed by seconds
or minutes, as an error spike in a completely unrelated service is a strong
signal of either a shared datastore being written by both, or an
undocumented synchronous dependency between them that the architecture
diagram does not show.

## 17. Security and privacy implications

Every service boundary is also a network-reachable attack exposure that did
not exist inside a monolith's single process, and the security model has
to shift from trusting anything inside the process to authenticating and
authorizing every service-to-service call, commonly with mutual TLS and a
service identity system, because an internal network can no longer be
assumed to be a trusted perimeter once dozens of services and their
operators share it.

Data that used to live behind one access-control layer, the monolith's own
authorization code, now needs that access control enforced independently
at each service boundary, because a consumer service calling a provider
service is effectively a new principal that must be authorized on its own
terms, not implicitly trusted because it lives in the same organization.

A published, versioned service contract is also a documented map of what
data and capability exist, which is useful to a legitimate integrator and
equally useful to an attacker performing reconnaissance. API gateways and
service registries are common places to enforce that only authenticated,
authorized callers can even discover a service's existence, not only its
data.

Distributing personal data across many services' independent datastores,
one of SOA's structural consequences from dimension 5, complicates data
subject rights such as deletion or export requests under regimes like GDPR,
because satisfying such a request now means coordinating a change across
every service that holds a copy of the relevant data, rather than a single
delete statement against one shared database. This entry treats this last
point as engineering judgement rather than a sourced legal claim. Consult
counsel for the specific compliance obligations of any given deployment.

## Code examples

Three languages, each showing a different real shape SOA takes in practice.
TypeScript shows a service consumer calling a provider over a typed HTTP
contract, the REST-based variant from dimension 8. Python shows the same
contract expressed as a small provider implementation with input validation
at the boundary, the shape a Service Provider from dimension 5 takes when it
enforces its own contract. Go shows an orchestrator coordinating two
downstream services with a timeout and a compensating action on failure, the
orchestrated dynamic from dimension 7. Java and Rust are omitted here because
the pattern is architectural rather than language-level. Its idiomatic shape
in any language is the same three pieces, a contract, a provider, and a
consumer, connected over a network protocol, and three languages are enough
to show that shape without repeating it five times over.

### TypeScript, a typed service consumer

```typescript
interface OrderContract {
  id: string;
  status: "pending" | "confirmed" | "failed";
}

interface OrderServiceClient {
  placeOrder(items: string[]): Promise<OrderContract>;
}

class HttpOrderServiceClient implements OrderServiceClient {
  constructor(private baseUrl: string) {}

  async placeOrder(items: string[]): Promise<OrderContract> {
    const response = await fetch(`${this.baseUrl}/orders`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ items }),
    });
    if (!response.ok) {
      throw new Error(`order service returned ${response.status}`);
    }
    const body = (await response.json()) as OrderContract;
    return body;
  }
}

async function main(): Promise<void> {
  const client: OrderServiceClient = new HttpOrderServiceClient(
    "https://orders.internal.example",
  );
  try {
    const order = await client.placeOrder(["sku-1", "sku-2"]);
    console.log(`order ${order.id} is ${order.status}`);
  } catch (err) {
    console.log(`placing the order failed. ${(err as Error).message}`);
  }
}

main();
```

### Python, a service provider enforcing its own contract

```python
from dataclasses import dataclass
from typing import Literal

OrderStatus = Literal["pending", "confirmed", "failed"]


@dataclass(frozen=True)
class Order:
    order_id: str
    status: OrderStatus


class InventoryUnavailableError(Exception):
    pass


class OrderService:
    """A Service Provider. It owns its own data and exposes one contract."""

    def __init__(self) -> None:
        self._orders: dict[str, Order] = {}
        self._next_id = 1

    def place_order(self, items: list[str]) -> Order:
        if not items:
            raise ValueError("an order must contain at least one item")
        order_id = f"order-{self._next_id}"
        self._next_id += 1
        order = Order(order_id=order_id, status="confirmed")
        self._orders[order_id] = order
        return order

    def get_order(self, order_id: str) -> Order:
        if order_id not in self._orders:
            raise KeyError(f"no such order. {order_id}")
        return self._orders[order_id]


if __name__ == "__main__":
    service = OrderService()
    placed = service.place_order(["sku-1", "sku-2"])
    print(f"placed {placed.order_id} with status {placed.status}")
    fetched = service.get_order(placed.order_id)
    print(f"fetched {fetched.order_id} with status {fetched.status}")
```

### Go, an orchestrator with a timeout and a compensating action

```go
package main

import (
	"context"
	"errors"
	"fmt"
	"time"
)

type InventoryService interface {
	Reserve(ctx context.Context, sku string) error
	Release(ctx context.Context, sku string) error
}

type PaymentService interface {
	Charge(ctx context.Context, amount int) error
}

type stubInventory struct{}

func (stubInventory) Reserve(ctx context.Context, sku string) error { return nil }
func (stubInventory) Release(ctx context.Context, sku string) error { return nil }

type failingPayment struct{}

func (failingPayment) Charge(ctx context.Context, amount int) error {
	return errors.New("payment provider declined the charge")
}

// OrderOrchestrator coordinates two downstream services and compensates
// the inventory reservation if the payment step fails.
type OrderOrchestrator struct {
	Inventory InventoryService
	Payment   PaymentService
}

func (o *OrderOrchestrator) PlaceOrder(ctx context.Context, sku string, amount int) error {
	ctx, cancel := context.WithTimeout(ctx, 2*time.Second)
	defer cancel()

	if err := o.Inventory.Reserve(ctx, sku); err != nil {
		return fmt.Errorf("reserve failed. %w", err)
	}

	if err := o.Payment.Charge(ctx, amount); err != nil {
		if releaseErr := o.Inventory.Release(ctx, sku); releaseErr != nil {
			return fmt.Errorf("charge failed (%v) and release also failed. %w", err, releaseErr)
		}
		return fmt.Errorf("charge failed, reservation released. %w", err)
	}

	return nil
}

func main() {
	orch := &OrderOrchestrator{
		Inventory: stubInventory{},
		Payment:   failingPayment{},
	}
	if err := orch.PlaceOrder(context.Background(), "sku-1", 1999); err != nil {
		fmt.Println("order failed as expected.", err)
		return
	}
	fmt.Println("order placed")
}
```

## 18. References

1. World Wide Web Consortium, Web Services Architecture, W3C Working Group
   Note, 11 February 2004. https://www.w3.org/TR/ws-arch/. Verified
   2026-08-02.
2. Martin Fowler, "Service Oriented Ambiguity," martinfowler.com bliki.
   https://martinfowler.com/bliki/ServiceOrientedAmbiguity.html. Verified
   2026-08-02.
3. James Lewis and Martin Fowler, "Microservices," martinfowler.com, 25
   March 2014. https://martinfowler.com/articles/microservices.html.
   Verified 2026-08-02.
4. Randy Shoup, "The eBay Architecture," InfoQ, 27 May 2008.
   https://www.infoq.com/articles/ebay-scalability-best-practices/.
   Verified 2026-08-02.
5. Uber Engineering, "Rethinking Microservice Architecture as Uber Grows,"
   uber.com engineering blog. https://www.uber.com/blog/microservice-architecture/.
   Verified 2026-08-02.
6. Thomas Erl, *Service-Oriented Architecture. Concepts, Technology, and
   Design*, Prentice Hall, 2005.
7. Thomas Erl, *SOA. Principles of Service Design*, Prentice Hall, 2007.
