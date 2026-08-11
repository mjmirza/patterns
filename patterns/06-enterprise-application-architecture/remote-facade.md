---
name: Remote Facade
slug: remote-facade
family: 06-enterprise-application-architecture
category: Distribution
aliases: [Session Facade, Service Facade, Coarse-Grained Interface]
first_described: "Fowler 2002"
maturity: canonical
related: [data-transfer-object, facade, dto-assembler, gateway]
incompatible_with: []
verified: 2026-08-02
---

# Remote Facade

## 1. Name, aliases, and lineage

The canonical name is Remote Facade, catalogued by Martin Fowler in *Patterns
of Enterprise Application Architecture*, Addison-Wesley, 2002, in the
Distribution Strategies section of chapter 18 alongside its companion, Data
Transfer Object. Fowler states the intent directly. "Provides a coarse-grained
facade on fine-grained objects to improve efficiency over a network"
(martinfowler.com, "Remote Facade", https://martinfowler.com/eaaCatalog/remoteFacade.html,
verified 2026-08-02). The pattern's shape is a facade in the Gang of Four sense,
one object standing in front of many, but its purpose is narrower than the GoF
Facade. it exists specifically to reduce the number of network round trips a
client must make, not merely to simplify a subsystem's API for local callers.

The most common alias in industry practice is Session Facade, the name Sun
used for the equivalent pattern in the J2EE world. Deepak Alur, John Crupi and
Dan Malks, *Core J2EE Patterns. Best Practices and Design Strategies*, 2nd
edition, Prentice Hall, 2003, describe Session Facade as a stateless or
stateful session bean placed in front of a graph of fine-grained entity beans,
so a remote client calls one session-bean method instead of many entity-bean
methods across the network. The book's stated problem statement is that direct
remote access to fine-grained business objects causes tight coupling and a
high volume of network calls, and its solution is to hide those objects behind
a coarser session-level interface. Service Facade is the same idea again under
a Spring- and later microservices-era name, used for a service-layer type that
wraps several repositories or domain objects and exposes one operation per use
case rather than one method per field.

Fowler is careful to separate Remote Facade from plain Facade. a Facade
simplifies a subsystem for any caller, in-process or not, and typically adds no
new methods, it only regroups existing ones behind a simpler surface. A Remote
Facade specifically answers the cost of a network call, and it usually does add
new coarse-grained methods that did not exist before, because the fine-grained
domain methods were never designed to be called once each per use case. Fowler
also stresses that a Remote Facade should carry no domain logic of its own.
"you shouldn't have any domain logic in the remote facade" is his own framing,
because the facade's only job is translation and aggregation, and putting
business rules there duplicates them outside the domain model where they were
already correctly expressed (martinfowler.com, "Remote Facade", verified
2026-08-02).

## 2. Problem and context

A well-factored domain model in a single process is built from many small,
single-purpose objects. an Order that holds a list of LineItem objects, each
LineItem referencing a Product, a Customer with an Address, a series of getter
and setter calls that read naturally as `order.getCustomer().getAddress().getCity()`.
Inside one process this granularity is a virtue. small objects with narrow
responsibilities are easy to test, easy to compose, and each method call costs
a handful of nanoseconds, so nobody thinks twice about calling five of them to
answer one question.

The moment a caller lives in a different process from that domain model,
whether across a network to another host, across a service boundary in the
same data center, or even across an in-process boundary that happens to be
remoted via RPC, every one of those calls stops being nearly free. A local
method call is a few nanoseconds. A same-datacenter network round trip is
commonly one hundred microseconds to a low single-digit number of milliseconds
depending on hop count, serialization, and the presence of TLS, several orders
of magnitude slower before a single byte of business logic runs. Ross Fisher
and Jeff Dean's widely circulated latency figures for typical 2020s data center
hardware put a single round trip within the same rack in roughly the ten to
five hundred microsecond band and a round trip across an availability zone or
region in the low milliseconds to tens of milliseconds ("Latency Numbers Every
Programmer Should Know", https://gist.github.com/hellerbarde/2843375, a widely
mirrored transcription of a talk originally given by Jeff Dean, this specific
gist verified 2026-08-02 as a live, commonly cited source, not as the original
primary publication). The exact numbers vary by hardware generation and
network topology, and no single citation nails a universal figure. the durable
point, which Fowler makes independently of any specific benchmark, is that the
gap between a local call and a remote call is measured in orders of magnitude,
not in a constant factor, and that gap does not shrink as networks get faster
because payload marshaling, security context propagation, and serialization
overhead scale with call count, not merely with distance.

Two remoting failure modes follow directly from ignoring this gap. A team ships
a fine-grained domain object across a remote boundary unchanged, so a client
that used to call `order.getLineItems().get(i).getProduct().getName()` in
process now makes that same chain of calls as a chain of RPC round trips, one
per hop, and a page that used to render in single-digit milliseconds now takes
seconds because it silently issued dozens of round trips. This shape has a
name of its own, the Chatty API or N+1 remote calls antipattern, and it is the
single most common reason a distributed system that "worked fine locally"
falls over the moment it crosses a real network. The opposite failure is
premature aggregation. a team, having learned to fear chattiness, collapses
every remote operation into one enormous god method that returns everything a
client could conceivably want, whether or not the current caller needs most of
it, producing an interface that is efficient for one caller and wasteful, hard
to version, and hard to reason about for every other caller.

Remote Facade exists to give a design a deliberate seam at exactly this
boundary. it does not ask a team to abandon a fine-grained domain model, and it
does not ask them to flatten that model into one giant remote type either. It
asks for a distinct, thin layer whose only job is to sit at the process
boundary, expose a small number of coarse operations shaped around real use
cases, and translate each coarse call into whatever fine-grained calls the
already-correct domain model needs, all inside the same process where those
calls are still nearly free.

## 3. Forces

**Latency and throughput versus flexibility.** Fewer, larger remote calls
reduce round-trip latency and improve throughput under load, because each call
carries fixed per-request overhead (connection setup or reuse, TLS handshake
amortization, serialization, authentication checks) that a fine-grained
interface pays repeatedly. That efficiency is bought by giving up the
flexibility of composing arbitrary fine-grained operations from the client
side. a client that only needs one field of a large aggregate still pays to
fetch the whole coarse response, unless the facade is deliberately shaped with
narrower variants for that case.

**Coupling to use cases versus coupling to the domain shape.** A well-designed
Remote Facade method is named and shaped after a use case ("place an order",
"get order summary for display") rather than after the domain object's
internal structure. This decouples the remote contract from domain refactors,
because the domain model can change its object graph freely as long as the
facade continues to answer the same use-case questions. The cost is that the
facade's shape drifts away from a one-to-one mirror of the domain, which makes
it a second thing to keep mentally synchronized with the domain, and a second
thing that can silently rot if a domain change is not reflected in the
use-case-shaped operation.

**Operability and versioning versus internal simplicity.** Concentrating all
remote entry points in one facade layer gives operators a single place to
apply authentication, authorization, rate limiting, request logging, and API
versioning, which is a genuine operational win over scattering those concerns
across every fine-grained remotable object. The cost is that this layer
becomes a mandatory hop for every remote interaction, so its own availability,
scaling characteristics, and deployment cadence now gate every client, and a
bug or an outage in the facade takes down every use case that flows through
it, not just one.

**Team topology.** A Remote Facade formalizes an ownership boundary. the team
that owns the domain model can evolve its internal object graph without
coordinating with every remote consumer, as long as the facade's contract is
honored. This is close to Fowler's own framing that a Remote Facade is what
makes a domain model safe to keep fine-grained even when it must be reached
remotely. the cost, named plainly by Sam Newman in the microservices
literature that descends from this idea, is that the facade or gateway becomes
a shared artifact between the team that owns it and every client team, and
poorly managed shared artifacts are a classic source of cross-team friction
and release-train coupling (Sam Newman, *Building Microservices*, 2nd edition,
O'Reilly, 2021, chapter 5, on API gateways and the coupling they can
reintroduce if treated as a place to put business logic).

**Cognitive load.** For a developer working purely inside the domain model,
Remote Facade adds nothing to think about, the domain stays exactly as
fine-grained and readable as it would be without remoting at all. For a
developer working on the facade layer itself, or debugging a production issue
that spans the boundary, there is now a second vocabulary (the coarse-grained,
DTO-shaped contract) layered on top of the first (the domain model), and
understanding a bug may require holding both mental models at once and
tracing the translation between them.

Remote Facade openly favors network efficiency, operational centralization,
and domain-model stability, and it openly sacrifices client-side query
flexibility and the simplicity of having exactly one vocabulary in the
system.

## 4. Applicability and non-applicability

Apply Remote Facade when a domain model or service is genuinely accessed
across a process boundary where round-trip cost is non-trivial, and multiple
related pieces of information or multiple related operations are naturally
needed together for a given client use case. It is the right tool whenever a
team is designing the boundary of a service that will be called by a client
in a different process, whether that is a browser calling a backend, a mobile
app calling an API, one microservice calling another, or a desktop client
calling an application server. It is also the right tool when an existing
fine-grained domain model already works well in process and the team wants to
expose it remotely without redesigning the domain itself, because the facade
absorbs the remoting concern without forcing the domain to become coarse.

Do not apply Remote Facade inside a single process. If two objects live in the
same address space and the same deployment unit, wrapping them in a
coarse-grained facade only to avoid "too many calls" adds an indirection layer
that pays no latency dividend at all, because in-process calls do not carry
the network's marshaling and round-trip cost that the pattern exists to
amortize. Fowler is explicit that a plain Facade is the correct tool for that
job, not a Remote Facade, and conflating the two produces an unnecessary layer
that only adds a second vocabulary for no efficiency gain.

Do not apply it to a boundary where calls are genuinely rare or where the
per-call cost is already amortized by the transport. a small internal admin
tool that makes one API call per page load to a service in the same
data-center rack, with no chattiness problem, does not need a purpose-built
coarse facade on top of an already-reasonable REST or RPC endpoint. Adding one
preemptively is speculative generality, and it produces exactly the "flat,
huge interface" antipattern Fowler warns against when the facade tries to
serve hypothetical future callers instead of the actual current use cases.

Do not use Remote Facade as a place to put business logic. If the temptation
is to compute a discount, validate a business rule, or make a state-transition
decision inside the facade method because "that's where the request lands",
that logic belongs in the domain model behind the facade, and the facade
degenerates into an undisciplined second copy of the domain the moment
business rules leak into it. This is the single most common misuse Fowler
calls out by name.

Do not reach for it as a substitute for proper API design when the real
problem is a poorly modeled domain. a facade cannot fix an underlying domain
model whose objects do not correspond to real use cases, it can only make the
symptom of chattiness less visible while the underlying modeling problem
persists.

## 5. Structure

**Client.** A process on the other side of the remote boundary from the
domain model. Never touches the fine-grained domain objects directly. Sees
only the Remote Facade's coarse operations and the Data Transfer Objects they
exchange.

**Remote Facade.** The boundary object itself. Exposes a small, use-case
shaped set of coarse-grained operations. Holds no domain state and enforces no
business rules of its own. Its only responsibilities are, in order, accept a
request (often already deserialized into a request DTO by the transport
layer), delegate to one or more fine-grained domain objects to perform the
actual work, assemble the results into a response DTO, and return that DTO
across the boundary. Frequently stateless per call, even when it wraps a
stateful domain model, because statelessness at the facade lets the transport
layer scale and route calls freely.

**Domain Model (fine-grained objects).** The existing, unchanged, richly
factored object graph. entities, value objects, aggregates, and the services
or repositories that operate on them. These objects continue to expose small,
well-named methods to each other exactly as they would in a purely local
application, because the Remote Facade is the only thing that ever crosses the
process boundary. No fine-grained domain object is itself remotable.

**Data Transfer Object (DTO).** A serializable data-holder shaped specifically
for one facade operation's request or response, carrying no behavior beyond
basic accessors and, sometimes, self-contained validation. The DTO is the
payload that actually travels the wire, decoupling the wire format from the
domain object graph so the domain can be refactored without breaking every
client's contract. Remote Facade and DTO are described by Fowler as a pair
that is "almost always used together" (martinfowler.com, "Remote Facade",
verified 2026-08-02), and the DTO Assembler, a small helper object or function
that converts between domain objects and DTOs, is the piece that keeps the
translation logic out of both the domain and the facade method bodies.

**Transport.** The actual remoting mechanism, gRPC, a JSON-over-HTTP REST
endpoint, a message queue with request-reply semantics, or a language-specific
RPC framework. Remote Facade is transport-agnostic in principle. its contract
is defined by its operations and DTOs, not by the wire protocol carrying them,
though in practice the transport heavily influences how coarse-grained a
"reasonable" operation needs to be, because a transport with high per-call
overhead pushes toward coarser operations than one with cheap calls.

## 6. ASCII structure diagram

```text
+------------------+          process / network boundary
|      Client       |------------------------|--------------------------+
+------------------+                          |                          |
                                               v                          |
                                     +-------------------+                |
                                     |   Remote Facade    |                |
                                     |  (coarse-grained)   |                |
                                     +-------------------+                |
                                       | placeOrder(req)  |                |
                                       | getOrderView(id) |                |
                                     +-------------------+                |
                                               |  delegates, no logic      |
                                               v                          |
                          +--------------------------------------+       |
                          |         Domain Model (fine-grained)    |       |
                          |                                        |       |
                          |   Order --- has many ---> LineItem      |       |
                          |     |                        |         |       |
                          |  Customer                 Product       |       |
                          |     |                                   |       |
                          |  Address                                |       |
                          +--------------------------------------+       |
                                               ^                          |
                                               |  assembled by            |
                                     +-------------------+                |
                                     |   DTO Assembler    |----------------+
                                     +-------------------+   returns DTO
                                               |
                                               v
                                     +-------------------+
                                     | Data Transfer Obj  |
                                     |  OrderView (flat)  |
                                     +-------------------+
```

## 7. Dynamics

The sequence below shows the difference between the chatty path a
fine-grained-only interface would force and the single coarse call a Remote
Facade offers instead. it also shows the internal delegation the facade
performs entirely inside the process, at local-call cost.

```text
Client                 RemoteFacade            Order        LineItem[]     Customer
  |                          |                    |               |             |
  |--- getOrderView(id) ---->|                    |               |             |
  |    (one network call)    |                    |               |             |
  |                          |--- findById(id) -->|               |             |
  |                          |<---- order --------|               |             |
  |                          |                    |               |             |
  |                          |--- getLineItems() ------------------------------>|
  |                          |<---- items (local, in-process) ----|             |
  |                          |                    |               |             |
  |                          |--- getCustomer() ----------------------------------|
  |                          |<---- customer (local, in-process) ----------------|
  |                          |                    |               |             |
  |                          |-- assemble DTO from order+items+customer -->     |
  |                          |    (DTO Assembler, still in-process)             |
  |                          |                    |               |             |
  |<--- OrderView DTO -------|                    |               |             |
  |    (one network reply)   |                    |               |             |
  |                          |                    |               |             |
```

Contrast this with what a client without a Remote Facade would have had to do,
issuing one network call per fine-grained method, each paying the full
round-trip cost the diagram above pays exactly once for the whole use case.

```text
Client                                                    Server-side objects
  |--- getOrder(id) ---------------- network call 1 ----->|
  |<-- order --------------------------------------------|
  |--- getLineItems(order.id) ------ network call 2 ----->|
  |<-- items ---------------------------------------------|
  |--- getCustomer(order.customerId) network call 3 ----->|
  |<-- customer -------------------------------------------|
  |--- getAddress(customer.addrId) - network call 4 ----->|
  |<-- address ---------------------------------------------|
  (4 round trips to answer the same question 1 round trip answered above)
```

## 8. Implementation variants

**Stateless per-call facade over a request/response DTO pair.** The dominant
shape in modern HTTP and gRPC services. Each operation takes a request DTO and
returns a response DTO, the facade instance itself (or the function, in a
functional style) holds no conversational state between calls, and any state
the use case needs lives either in the request DTO or is looked up fresh from
the domain model each call. This is the variant shown in the code samples
below and the one Fowler's own PoEAA examples favor for the general case.

**Stateful session facade.** Common in the older EJB Session Facade tradition
and still seen in protocols that model an explicit session, such as a
stateful gRPC bidirectional stream or a SOAP session bound to a server-side
conversational bean. The facade instance is pinned to a client session and can
hold intermediate state (a shopping cart in progress, a multi-step wizard)
between calls, trading the operational simplicity of pure statelessness for a
more natural mapping onto genuinely stateful, multi-step interactions. Alur,
Crupi and Malks distinguish Stateless and Stateful Session Facade explicitly
as two implementation strategies for the same pattern (*Core J2EE Patterns*,
2nd edition, Prentice Hall, 2003, Session Facade, Implementation section).

**RPC-framework-generated facade.** In gRPC, Thrift, and similar interface
description language driven stacks, the facade's contract is defined once in
a schema file (a `.proto` file for gRPC), and both the client stub and the
server-side skeleton are code-generated from it. The developer implements the
generated server interface's methods, which is functionally the Remote Facade
implementation, while the DTOs are the generated message types. This variant
gives strong compile-time contract checking on both sides at the cost of a
build-time code generation step and a schema evolution discipline the team
must maintain (grpc.io, "Introduction to gRPC",
https://grpc.io/docs/what-is-grpc/introduction/, verified 2026-08-02, "You
define gRPC services in ordinary proto files, with RPC method parameters and
return types specified as protocol buffer messages").

**REST resource facade.** A resource-oriented HTTP API where each endpoint is
itself the coarse-grained operation, for example a single `GET
/orders/{id}/view` endpoint that returns an aggregate JSON document rather
than requiring the client to call `/orders/{id}`, then
`/orders/{id}/lineitems`, then `/customers/{id}` separately. The facade's
"methods" are HTTP routes, and the DTO is the JSON response body. Google's own
API design guidance recommends exactly this shape for client-facing resources,
distinct from a literal one-to-one mapping of internal storage tables to
endpoints (Google, "API Design Guide, Resource Design",
https://cloud.google.com/apis/design/resources, general resource-orientation
guidance, this is engineering-judgement-level alignment rather than a direct
quote and is not separately verified here beyond the earlier grpc.io and
microservices.io citations).

**Backend for Frontend (BFF).** A specialization where a separate coarse
facade is built per client type (web, iOS, Android) rather than one shared
coarse facade for all clients, because different client types genuinely need
different aggregations and different payload shapes. Sam Newman documents
this as the Backends for Frontends pattern, an evolution of the single
API-gateway-as-facade idea into multiple purpose-built facades (Sam Newman,
*Building Microservices*, 2nd edition, O'Reilly, 2021, chapter 5). This is
still the same Remote Facade shape underneath, applied per client rather than once
globally, and it directly addresses the "one huge interface serving everyone
badly" antipattern named in dimension 11 below.

## 9. Known production uses

**gRPC service definitions across the industry.** Any gRPC service is, by
construction, a Remote Facade. the `.proto` file declares a small set of
coarse RPC methods, each taking one request message and returning one
response message, precisely the shape Fowler describes, and the framework
generates the stub and skeleton code that implements the pattern's mechanics
(grpc.io, "Introduction to gRPC", https://grpc.io/docs/what-is-grpc/introduction/,
verified 2026-08-02).

**Netflix's client-facing API layer.** Netflix's public statements about its
API architecture describe an API gateway layer, historically built on the
Zuul library and later evolved further, that sits in front of many
fine-grained backend microservices and exposes device- and client-specific
coarse endpoints so that a single client request can retrieve aggregated data
without the client itself issuing one call per backend service. This is the
Backend for Frontend variant of Remote Facade described in dimension 8, and it
is documented in Netflix's own public engineering writing on API gateway
evolution (referenced via the general API Gateway / BFF pattern description
at microservices.io, "Pattern, API Gateway",
https://microservices.io/patterns/apigateway.html, verified 2026-08-02, which
names Netflix's Zuul-based gateway as a real-world instance of this pattern
family).

**J2EE and Java EE Session Facade in enterprise applications.** The Session
Facade pattern, Sun's own name for this idea, was the standard, widely taught
way to expose a graph of Enterprise JavaBeans entity beans to remote clients
throughout the J2EE era, documented as one of Sun's Core J2EE Patterns and
used across a generation of enterprise Java applications built on EJB
(Deepak Alur, John Crupi, and Dan Malks, *Core J2EE Patterns. Best Practices
and Design Strategies*, 2nd edition, Prentice Hall, 2003, "Session Facade").

**Amazon and general cloud provider SDK "resource" and "client" layers.**
Cloud provider SDKs (for example the AWS SDK's higher-level resource clients
and the general shape of most cloud provider REST APIs) commonly expose
coarse operations such as "describe instance with its attached volumes and
network interfaces in one call" rather than forcing a caller to issue one
network round trip per related sub-resource, following the same efficiency
reasoning Fowler describes, and this shape is explicitly recommended in
Google's public API design guidance for resource-oriented services
(Google, "API Design Guide", https://cloud.google.com/apis/design, general
resource-orientation and aggregation guidance, verified 2026-08-02 as a live,
current document, cited here at the level of general design stance rather
than as a direct quote).

**GraphQL as an intentional generalization of the same problem.** GraphQL, as
described in its own specification's motivation, exists specifically to let a
client request exactly the fields it needs in a single round trip rather than
either over-fetching from a coarse REST endpoint or under-fetching and
chaining many fine-grained calls. It is worth naming here because it is best
understood as a more flexible descendant of Remote Facade's core motivation,
the network-efficiency problem is the same, and GraphQL's answer is a
query-shaped facade rather than a fixed set of named coarse operations
(GraphQL Foundation, "Introduction to GraphQL", https://graphql.org/learn/,
verified 2026-08-02, general framing, not a direct quote).

## 10. Consequences

**Positive.**

- Reduces the number of network round trips a client needs for a given use
  case from one-per-fine-grained-call down to one, or a small fixed number,
  directly attacking the dominant cost of remote interaction.
- Lets the domain model stay genuinely fine-grained and well-factored, because
  the pressure to coarsen the domain to survive remoting is absorbed entirely
  by the facade layer instead.
- Gives the system exactly one place to apply cross-cutting remote concerns,
  authentication, input validation at the boundary, rate limiting, request
  logging, and API versioning, rather than scattering those concerns across
  many remotable fine-grained endpoints.
- Decouples the wire contract from the domain object graph when paired with
  DTOs, so the domain can be refactored internally without breaking every
  client that depends on the remote contract.
- Creates a natural seam for backward compatibility. a new facade version or
  a new operation can be added alongside an existing one without touching the
  fine-grained domain model at all.

**Negative.**

- Adds an entire extra layer, with its own types (DTOs), its own translation
  code (assemblers), and its own set of operations to design, test, and keep
  in sync with the domain model as it evolves.
- The facade's granularity decision is a permanent commitment that is
  expensive to change later. an operation that turns out too coarse for one
  caller and too fine for another cannot be fixed without a contract change
  that every client must absorb.
- If discipline slips, the facade becomes an attractive place to put business
  logic "just this once", because it already sits at the request-handling
  entry point, and once that starts it duplicates and eventually diverges
  from the logic correctly expressed in the domain model.
- A stateless facade design forces state that would be natural to keep
  conversationally (a multi-step wizard, an in-progress cart) to either be
  re-derived from scratch each call or persisted and re-fetched, adding
  complexity that a stateful in-process design would not have needed.
- Every client of the facade is now coupled to a single deployment unit's
  availability, latency, and scaling characteristics, so an outage or a
  performance regression in the facade layer is felt by every use case that
  flows through it at once, rather than being isolated to whichever
  fine-grained object a client happened to call directly.

## 11. Failure modes and misuse

**Symptom.** The facade exposes a single giant method, or a small number of
enormous methods, each returning a huge DTO with dozens of optional or
usually-empty fields, and most callers only ever need a handful of those
fields on any given call. **Cause.** The team tried to serve every current and
imagined future caller from one operation instead of shaping distinct
operations around distinct use cases, either from a desire to avoid designing
multiple endpoints or from genuine uncertainty about future needs. **Fix.**
Split the facade into use-case-shaped operations, one per distinct caller
need, even if that means several operations share overlapping underlying
domain calls internally. It is normal and correct for two facade methods to
both call `Order.getLineItems()` internally.

**Symptom.** Business rules, discount calculations, validation logic, or
state-transition decisions live inside the facade method bodies rather than
in the domain model, discoverable by grepping the facade implementation file
for `if` statements that reference business concepts (a tax rate, a discount
threshold, an order-status transition rule) rather than pure data assembly.
**Cause.** The facade is the first place a request lands, and it is
convenient to write the check right there instead of pushing it down into the
domain model where it belongs, especially under deadline pressure.
**Fix.** Move every business rule into the domain model, leaving the facade
method to do exactly two things, call the domain, and assemble the DTO from
the result. A useful heuristic is that a Remote Facade method body should be
short enough to read at a glance and should contain no conditional that a
domain expert would recognize as a business rule.

**Symptom.** A page or a batch job that calls the facade shows unexpectedly
high latency, and tracing reveals the client is issuing dozens of calls to the
facade per logical operation, not one. **Cause.** The facade was designed
around the domain's object shape rather than around actual client use cases,
so what looks like a coarse-grained facade from the server's perspective is
still effectively fine-grained from the client's perspective, forcing the
client to loop over facade calls to assemble the data it actually needs.
**Fix.** Design facade operations from the client's use case backward, not
from the domain's object graph forward. If a client screen needs an order
plus its line items plus the customer's shipping address, the facade should
have one operation that returns exactly that, not three operations that mirror
the domain's three separate object types.

**Symptom.** DTOs returned by the facade drift out of sync with the domain
model over time. some fields silently stop being populated, or new domain
fields never make it into the DTO, and nobody notices until a client bug
report arrives. **Cause.** The assembly code that maps domain objects to DTOs
is duplicated ad hoc in multiple facade methods rather than centralized in a
dedicated assembler, so a domain change only gets propagated to whichever
assembly code path a developer happened to remember to update.
**Fix.** Centralize domain-to-DTO conversion in a single assembler function or
type per DTO shape, and cover it with tests that assert every relevant domain
field reaches the DTO, so a forgotten mapping fails a test rather than
shipping silently.

**Symptom.** Adding a field to an existing facade response, or changing an
existing field's type, breaks currently-deployed older clients in production.
**Cause.** The facade's DTOs are treated as an internal implementation detail
that can change freely, the same way a private domain object could, rather
than as a public versioned contract. **Fix.** Treat every facade operation and
its DTOs as an external contract from the moment a second client exists. add
new optional fields rather than repurposing existing ones, and introduce a new
operation or a new API version for a breaking shape change rather than
mutating the existing one in place.

## 12. Trade-off matrix

| Concern | Remote Facade | Plain (GoF) Facade | Direct fine-grained remoting | GraphQL-style query facade |
|---|---|---|---|---|
| Reduces network round trips | Yes, its primary purpose | No, offers no network benefit at all | No, this is the problem it exists to solve | Yes, by letting the client shape one query |
| Adds a translation and DTO layer | Yes, deliberately | No, typically reuses existing types directly | No extra layer, but no protection either | Yes, a schema and resolver layer |
| Client-side query flexibility | Low, fixed set of named operations | Not applicable, not a remoting concern | High in principle, but expensive in practice | High, client picks exact fields |
| Risk of business logic leaking into the boundary layer | Moderate, must be actively guarded against | Low, facade usually has no request/response shape to tempt logic into | Low, no facade layer to leak into | Moderate, resolvers can accumulate logic the same way |
| Operational centralization (auth, rate limiting, versioning) | Strong, one layer for all concerns | Weak, not designed for cross-process concerns | Weak, concerns scattered per endpoint | Strong, but per-field authorization is harder to reason about |
| Appropriate inside a single process | No, adds cost with no benefit | Yes, this is its home ground | Yes, this is simply the normal object graph | No, designed for cross-process query flexibility |

## 13. Related and incompatible patterns

**Data Transfer Object.** The pattern Remote Facade is almost never used
without. the facade defines which coarse operations exist, and DTOs define
the shape of what travels across the boundary for each operation. Fowler
presents them as a pair specifically because a Remote Facade without DTOs
tends to leak fine-grained domain objects across the wire, reintroducing the
chattiness and coupling problem the facade was meant to solve, only one layer
later (martinfowler.com, "Remote Facade", verified 2026-08-02).

**DTO Assembler.** Not always named as its own pattern, but consistently
present in mature implementations as the small piece of code, often a
dedicated function or type, responsible for converting between domain objects
and DTOs in both directions. Keeping this logic out of both the domain model
and the facade method bodies is what prevents the "business logic leaks into
the facade" and "DTOs drift out of sync with the domain" failure modes named
in dimension 11.

**Facade (Gang of Four).** The structural ancestor. Remote Facade is a Facade
specialized for the remote-boundary case, adding the network-efficiency
motivation and the near-mandatory DTO pairing that a plain in-process Facade
does not need. Applying Remote Facade inside a process where a plain Facade
would suffice is a misapplication, covered in dimension 4.

**API Gateway and Backend for Frontend.** A service-level generalization of
the same idea, where the "facade" sits in front of an entire mesh of
microservices rather than in front of one domain model, and where the
Backend-for-Frontend variant deliberately builds multiple purpose-built
facades rather than one shared one (Sam Newman, *Building Microservices*, 2nd
edition, O'Reilly, 2021, chapter 5). Compatible and complementary. a Remote
Facade can sit inside a single service that is itself reached through an
outer API gateway.

**Repository and Service Layer.** These patterns typically sit behind a
Remote Facade rather than beside it. a Service Layer object is frequently what
a Remote Facade method delegates to, and a Repository is frequently what that
service layer or the domain model itself uses to load and persist entities.
Remote Facade does not replace either. it is the outermost seam, with Service
Layer and Repository doing the actual work one layer in.

**Anti-Corruption Layer.** A related idea from Domain-Driven Design that also
sits at a boundary and translates between two models, but for a different
reason. an Anti-Corruption Layer exists to protect a domain model from being
shaped by an external system's model, whereas Remote Facade exists to protect
network efficiency for a domain model's own external consumers. The two can
coexist at the same physical boundary when a service both exposes itself
remotely and consumes an external system it wants to insulate against.

**Incompatible with treating the facade as the domain model itself.** A
design where the "facade" type directly holds business state and enforces
business rules with no separate domain model behind it is not Remote Facade,
it has simply collapsed the two layers Fowler explicitly keeps separate, and
loses the refactoring latitude and reusability that keeping the domain
fine-grained was meant to preserve.

## 14. Refactoring path in and out

**Introducing Remote Facade into code that lacks it.** Start from an
identified chattiness problem, evidence that a client makes several
sequential calls to fine-grained remote objects to accomplish one use case,
visible either in code review or in a distributed trace showing multiple
round trips per logical operation. Pick the single most common or most costly
use case first rather than attempting to design the whole facade surface at
once. Write one new coarse-grained method that performs, inside the same
process as the domain model, exactly the sequence of fine-grained calls the
client used to make remotely, and have that method return a purpose-built DTO
assembled from the results. Redirect the client to call this one new
operation instead of the several old ones, and only once that migration is
verified, remove the client's remote access to the old fine-grained
operations, if the transport allowed direct access to them in the first
place. Repeat per use case, refactoring toward more coarse-grained operations
incrementally rather than as a single big-bang rewrite of the remote
interface. This mirrors Martin Fowler's own general refactoring stance, of
introducing a new element alongside the old one, migrating callers, then
retiring the old element, rather than mutating a live boundary in place.

**Removing Remote Facade when it stops earning its place.** This happens most
often when a genuinely distributed boundary collapses back into a single
process, for example two services that were split apart get merged back into
one deployable unit because the split never earned its operational cost.
Confirm first that the caller and the facade truly now share a process and an
address space, not merely the same data center. Then replace facade calls
with direct calls into the domain model, and either delete the now-pointless
DTOs or, if some external consumer still legitimately needs a stable wire
contract, retain a thinner remaining Remote Facade specifically for that
external consumer while internal callers bypass it entirely. Do not delete a
Remote Facade merely because a given call site looks verbose, if that call
site genuinely still crosses a network boundary, the facade is doing its job
and the fix belongs in operation granularity, not in removing the pattern.

## 15. Testing and verification

Test the domain model exactly as it would be tested with no remoting
concern at all, in-process, with ordinary unit tests against the fine-grained
objects, because the domain model's correctness has nothing to do with the
existence of the facade layered on top of it. This is one of the pattern's
underrated benefits. a correctly implemented Remote Facade adds no new
business-logic surface for domain-level tests to cover.

Test the Remote Facade itself at two distinct levels. First, an in-process
integration test that calls each facade method directly (bypassing the actual
network transport) against a real or in-memory instance of the domain model,
asserting that the returned DTO contains exactly the fields the use case
requires and correctly reflects the underlying domain state, including edge
cases such as an order with zero line items or a customer with no address on
file. Second, a contract test that exercises the facade through its actual
transport, serializing a request, sending it over a real or loopback network
connection, and deserializing the response, to catch serialization bugs,
schema mismatches, and transport-specific issues that an in-process call
would never surface. Consumer-driven contract testing tools, such as Pact,
are commonly used at this second level specifically because a Remote Facade
is, by definition, a contract multiple independently deployed clients depend
on, and a contract test catches a facade change that would break a client
before that change reaches production.

Test the DTO assembler in isolation with focused unit tests that construct a
known domain object graph and assert the resulting DTO's exact field values,
this is where the "field silently stops being populated" failure mode from
dimension 11 is caught cheaply, at unit-test speed, rather than by a client
bug report.

Use a test double for the domain model, not for the facade, when writing
tests for code that calls the facade. Because the facade should contain no
business logic of its own, mocking the facade in a caller's test tends to
verify nothing except that the mock was called correctly, whereas exercising
the real facade against a controlled in-memory domain model verifies the
actual translation logic the facade exists to provide.

## 16. Observability signals

Instrument every Remote Facade operation with a per-operation counter and
latency histogram, tagged by operation name, so a dashboard can show request
rate and p50 or p99 latency per coarse-grained method rather than only an
aggregate for the whole service. A healthy facade shows stable, low
per-operation latency that does not grow with the number of underlying
domain objects a given call happens to touch, because that work is happening
inside the process at near-local-call speed. A failing or degrading facade
typically shows latency growth correlated with response payload size or with
the number of internal domain calls a given operation performs, which is the
signal that a supposedly coarse operation has quietly grown into a hidden
N-plus-one problem internally, for example if the DTO assembler starts making
a database call per line item instead of loading them in one batched query.

Log, at the facade boundary specifically, the incoming request's shape
(operation name, key identifying fields, but never full payload contents if
they may carry sensitive data, see dimension 17) and the outgoing response's
size and status, because this boundary is the natural place to correlate a
client-reported problem with server-side behavior without needing to trace
into domain-internal calls that a client-facing report would never reference.

Track a distinct metric for "facade call count per client session" or "facade
calls per logical page load" where the calling context allows it. this is the
direct, actionable signal for chattiness regression, an increase here over
time, even with individual call latency unchanged, is evidence that a client
has started working around the facade's granularity by making more calls than
the facade was designed to require, which is a design smell worth
investigating before it becomes a performance incident.

Trace propagation across the facade boundary matters specifically here.
because the whole point of the pattern is to hide a fan-out of internal
domain calls behind one external call, a distributed trace that only shows
the single external span, with none of the internal fan-out as child spans,
makes it impossible to tell whether a slow facade call is slow because of one
expensive internal operation or many cheap ones summed together. Internal
domain calls made from within a facade method should still be spanned in the
trace, even though they never leave the process, specifically so this
distinction stays visible.

## 17. Security and privacy implications

The Remote Facade is, by definition, the exposed edge of the domain model, and
that has direct security consequences distinct from the domain model's own
internal correctness. Every input validation and authorization check that
matters for a remote caller belongs at the facade boundary, or at a layer
explicitly in front of it (a gateway, a middleware chain), never assumed to
already be handled somewhere inside the domain model that a remote caller
never directly touches. A domain object designed for trusted in-process
callers frequently omits defensive checks it would need if it were reachable
directly by an untrusted remote party, which is exactly why it should never be
reachable directly by one, and why the facade's translation step is also the
natural place to enforce that only well-formed, authorized requests ever reach
the domain model at all.

Because a Remote Facade's DTOs are explicitly a separate, purpose-built shape
rather than a raw serialization of domain objects, the pattern gives a team a
deliberate opportunity, and a deliberate obligation, to control exactly which
fields leave the process on each response. A common and serious mistake is
building a DTO assembler that maps a domain object to a DTO by reflecting
over all its fields generically, which silently ships any new field added to
the domain object to every remote caller the moment it is added, including
fields that were never meant to be exposed, such as an internal cost basis, a
soft-deleted flag, or another customer's data accidentally referenced through
an association. The discipline of hand-listing exactly which fields a DTO
assembler copies, rather than serializing a domain object generically, is a
direct security control, not merely a style preference.

The facade's coarse-grained shape also affects the blast radius of
authorization bugs. because one facade call can now return data assembled
from several underlying domain objects (an order, its line items, its
customer, that customer's address) in a single response, an authorization
check that only verifies the caller can see the top-level object (the order)
without separately verifying they are entitled to see every nested object the
DTO assembler pulled in (the customer's full address, if that customer is not
the requester) can leak data that a purely fine-grained, per-object-checked
interface would not have leaked in the same way. Authorization at the facade
must be checked against everything the response DTO will actually contain,
not only against the primary entity named in the request.

Rate limiting and abuse prevention are naturally centralized at the facade
layer, which is a genuine security benefit relative to a fine-grained
interface where the same protections would need to be duplicated across many
smaller remotable endpoints, but this centralization also means the facade
layer itself becomes a single, valuable target, and its own availability and
correctness under adversarial load (malformed requests, oversized payloads,
slow-loris style connection abuse) matters more, precisely because every use
case in the system now depends on it.

## 18. References

1. Martin Fowler, *Patterns of Enterprise Application Architecture*,
   Addison-Wesley, 2002, chapter 18, Distribution Strategies, "Remote
   Facade".
2. Martin Fowler, "Remote Facade", martinfowler.com,
   https://martinfowler.com/eaaCatalog/remoteFacade.html, verified 2026-08-02.
3. Deepak Alur, John Crupi, and Dan Malks, *Core J2EE Patterns. Best
   Practices and Design Strategies*, 2nd edition, Prentice Hall, 2003,
   "Session Facade".
4. Sam Newman, *Building Microservices*, 2nd edition, O'Reilly, 2021, chapter
   5, on API gateways and Backends for Frontends.
5. Chris Richardson, "Pattern, API Gateway / Backends for Frontends",
   microservices.io, https://microservices.io/patterns/apigateway.html,
   verified 2026-08-02.
6. gRPC Authors, "Introduction to gRPC", grpc.io,
   https://grpc.io/docs/what-is-grpc/introduction/, verified 2026-08-02.
7. GraphQL Foundation, "Introduction to GraphQL", graphql.org,
   https://graphql.org/learn/, verified 2026-08-02.
8. Google Cloud, "API Design Guide", cloud.google.com,
   https://cloud.google.com/apis/design, verified 2026-08-02.
9. "Latency Numbers Every Programmer Should Know", a widely mirrored
   transcription of figures originally attributed to Jeff Dean,
   https://gist.github.com/hellerbarde/2843375, verified 2026-08-02 as a
   live, commonly cited secondary source, not the original primary talk.

## Code examples

Three languages, each showing the same use case. a coarse-grained
`getOrderView` operation and a `placeOrder` operation, wrapping a fine-grained
domain model of `Order`, `LineItem`, `Customer`, and `Product`. Java was
omitted because no JDK was available in the environment used to write this
entry, and it was not run as a result, though the shape of a Java version
would be nearly identical to the Go and TypeScript versions below, a
class implementing a generated gRPC service interface.

### TypeScript

```typescript
// Fine-grained domain model, unaware of any remoting concern.
class Product {
  constructor(public readonly id: string, public readonly name: string, public readonly priceCents: number) {}
}

class LineItem {
  constructor(public readonly product: Product, public readonly quantity: number) {}
  subtotalCents(): number {
    return this.product.priceCents * this.quantity;
  }
}

class Address {
  constructor(public readonly city: string, public readonly country: string) {}
}

class Customer {
  constructor(public readonly id: string, public readonly name: string, public readonly address: Address) {}
}

class Order {
  private readonly items: LineItem[] = [];
  constructor(public readonly id: string, public readonly customer: Customer) {}
  addItem(item: LineItem): void {
    this.items.push(item);
  }
  getLineItems(): ReadonlyArray<LineItem> {
    return this.items;
  }
  totalCents(): number {
    return this.items.reduce((sum, item) => sum + item.subtotalCents(), 0);
  }
}

// Data Transfer Objects, the shape that actually crosses the wire.
interface LineItemView {
  productName: string;
  quantity: number;
  subtotalCents: number;
}

interface OrderView {
  orderId: string;
  customerName: string;
  customerCity: string;
  items: LineItemView[];
  totalCents: number;
}

interface PlaceOrderRequest {
  customerId: string;
  productId: string;
  quantity: number;
}

interface PlaceOrderResponse {
  orderId: string;
  totalCents: number;
}

// Minimal in-memory repositories standing in for a real persistence layer.
class OrderRepository {
  private readonly orders = new Map<string, Order>();
  private nextId = 1;
  save(order: Order): void {
    this.orders.set(order.id, order);
  }
  findById(id: string): Order | undefined {
    return this.orders.get(id);
  }
  nextOrderId(): string {
    return `order-${this.nextId++}`;
  }
}

// DTO Assembler, the only place domain objects turn into wire-shaped data.
function assembleOrderView(order: Order): OrderView {
  return {
    orderId: order.id,
    customerName: order.customer.name,
    customerCity: order.customer.address.city,
    items: order.getLineItems().map((item) => ({
      productName: item.product.name,
      quantity: item.quantity,
      subtotalCents: item.subtotalCents(),
    })),
    totalCents: order.totalCents(),
  };
}

// The Remote Facade. coarse-grained, no domain logic, only delegation and assembly.
class OrderFacade {
  constructor(
    private readonly orders: OrderRepository,
    private readonly customers: ReadonlyMap<string, Customer>,
    private readonly products: ReadonlyMap<string, Product>,
  ) {}

  getOrderView(orderId: string): OrderView | undefined {
    const order = this.orders.findById(orderId);
    if (!order) {
      return undefined;
    }
    return assembleOrderView(order);
  }

  placeOrder(request: PlaceOrderRequest): PlaceOrderResponse {
    const customer = this.customers.get(request.customerId);
    const product = this.products.get(request.productId);
    if (!customer || !product) {
      throw new Error("unknown customer or product");
    }
    const order = new Order(this.orders.nextOrderId(), customer);
    order.addItem(new LineItem(product, request.quantity));
    this.orders.save(order);
    return { orderId: order.id, totalCents: order.totalCents() };
  }
}

function demo(): void {
  const address = new Address("Munich", "DE");
  const customer = new Customer("cust-1", "Mirza", address);
  const product = new Product("prod-1", "Keyboard", 4999);
  const customers = new Map<string, Customer>([[customer.id, customer]]);
  const products = new Map<string, Product>([[product.id, product]]);
  const facade = new OrderFacade(new OrderRepository(), customers, products);

  const placed = facade.placeOrder({ customerId: customer.id, productId: product.id, quantity: 2 });
  const view = facade.getOrderView(placed.orderId);
  if (view) {
    console.log(`order ${view.orderId} total ${view.totalCents} for ${view.customerName}`);
  }
}

demo();
```

### Go

```go
package remotefacade

import "fmt"

// Fine-grained domain model.
type Product struct {
	ID        string
	Name      string
	PriceCents int
}

type LineItem struct {
	Product  Product
	Quantity int
}

func (li LineItem) SubtotalCents() int {
	return li.Product.PriceCents * li.Quantity
}

type Address struct {
	City    string
	Country string
}

type Customer struct {
	ID      string
	Name    string
	Address Address
}

type Order struct {
	ID       string
	Customer Customer
	items    []LineItem
}

func (o *Order) AddItem(item LineItem) {
	o.items = append(o.items, item)
}

func (o *Order) LineItems() []LineItem {
	return o.items
}

func (o *Order) TotalCents() int {
	total := 0
	for _, item := range o.items {
		total += item.SubtotalCents()
	}
	return total
}

// Data Transfer Objects, the shape that crosses the process boundary.
type LineItemView struct {
	ProductName   string
	Quantity      int
	SubtotalCents int
}

type OrderView struct {
	OrderID      string
	CustomerName string
	CustomerCity string
	Items        []LineItemView
	TotalCents   int
}

type PlaceOrderRequest struct {
	CustomerID string
	ProductID  string
	Quantity   int
}

type PlaceOrderResponse struct {
	OrderID    string
	TotalCents int
}

// Minimal in-memory repository standing in for real persistence.
type OrderRepository struct {
	orders map[string]*Order
	nextID int
}

func NewOrderRepository() *OrderRepository {
	return &OrderRepository{orders: make(map[string]*Order), nextID: 1}
}

func (r *OrderRepository) Save(order *Order) {
	r.orders[order.ID] = order
}

func (r *OrderRepository) FindByID(id string) (*Order, bool) {
	order, ok := r.orders[id]
	return order, ok
}

func (r *OrderRepository) NextOrderID() string {
	id := fmt.Sprintf("order-%d", r.nextID)
	r.nextID++
	return id
}

// assembleOrderView is the DTO Assembler, the only place domain data becomes wire data.
func assembleOrderView(order *Order) OrderView {
	views := make([]LineItemView, 0, len(order.LineItems()))
	for _, item := range order.LineItems() {
		views = append(views, LineItemView{
			ProductName:   item.Product.Name,
			Quantity:      item.Quantity,
			SubtotalCents: item.SubtotalCents(),
		})
	}
	return OrderView{
		OrderID:      order.ID,
		CustomerName: order.Customer.Name,
		CustomerCity: order.Customer.Address.City,
		Items:        views,
		TotalCents:   order.TotalCents(),
	}
}

// OrderFacade is the Remote Facade. coarse-grained, no domain logic of its own.
type OrderFacade struct {
	orders    *OrderRepository
	customers map[string]Customer
	products  map[string]Product
}

func NewOrderFacade(orders *OrderRepository, customers map[string]Customer, products map[string]Product) *OrderFacade {
	return &OrderFacade{orders: orders, customers: customers, products: products}
}

func (f *OrderFacade) GetOrderView(orderID string) (OrderView, bool) {
	order, ok := f.orders.FindByID(orderID)
	if !ok {
		return OrderView{}, false
	}
	return assembleOrderView(order), true
}

func (f *OrderFacade) PlaceOrder(req PlaceOrderRequest) (PlaceOrderResponse, error) {
	customer, ok := f.customers[req.CustomerID]
	if !ok {
		return PlaceOrderResponse{}, fmt.Errorf("unknown customer %s", req.CustomerID)
	}
	product, ok := f.products[req.ProductID]
	if !ok {
		return PlaceOrderResponse{}, fmt.Errorf("unknown product %s", req.ProductID)
	}
	order := &Order{ID: f.orders.NextOrderID(), Customer: customer}
	order.AddItem(LineItem{Product: product, Quantity: req.Quantity})
	f.orders.Save(order)
	return PlaceOrderResponse{OrderID: order.ID, TotalCents: order.TotalCents()}, nil
}
```

### Python

```python
from dataclasses import dataclass, field
from typing import Optional


# Fine-grained domain model.
@dataclass(frozen=True)
class Product:
    id: str
    name: str
    price_cents: int


@dataclass(frozen=True)
class LineItem:
    product: Product
    quantity: int

    def subtotal_cents(self) -> int:
        return self.product.price_cents * self.quantity


@dataclass(frozen=True)
class Address:
    city: str
    country: str


@dataclass(frozen=True)
class Customer:
    id: str
    name: str
    address: Address


@dataclass
class Order:
    id: str
    customer: Customer
    items: list[LineItem] = field(default_factory=list)

    def add_item(self, item: LineItem) -> None:
        self.items.append(item)

    def total_cents(self) -> int:
        return sum(item.subtotal_cents() for item in self.items)


# Data Transfer Objects, the shape exchanged across the boundary.
@dataclass(frozen=True)
class LineItemView:
    product_name: str
    quantity: int
    subtotal_cents: int


@dataclass(frozen=True)
class OrderView:
    order_id: str
    customer_name: str
    customer_city: str
    items: list[LineItemView]
    total_cents: int


@dataclass(frozen=True)
class PlaceOrderRequest:
    customer_id: str
    product_id: str
    quantity: int


@dataclass(frozen=True)
class PlaceOrderResponse:
    order_id: str
    total_cents: int


class OrderRepository:
    def __init__(self) -> None:
        self._orders: dict[str, Order] = {}
        self._next_id = 1

    def save(self, order: Order) -> None:
        self._orders[order.id] = order

    def find_by_id(self, order_id: str) -> Optional[Order]:
        return self._orders.get(order_id)

    def next_order_id(self) -> str:
        order_id = f"order-{self._next_id}"
        self._next_id += 1
        return order_id


def assemble_order_view(order: Order) -> OrderView:
    items = [
        LineItemView(
            product_name=item.product.name,
            quantity=item.quantity,
            subtotal_cents=item.subtotal_cents(),
        )
        for item in order.items
    ]
    return OrderView(
        order_id=order.id,
        customer_name=order.customer.name,
        customer_city=order.customer.address.city,
        items=items,
        total_cents=order.total_cents(),
    )


class OrderFacade:
    """The Remote Facade. coarse-grained, no domain logic of its own."""

    def __init__(
        self,
        orders: OrderRepository,
        customers: dict[str, Customer],
        products: dict[str, Product],
    ) -> None:
        self._orders = orders
        self._customers = customers
        self._products = products

    def get_order_view(self, order_id: str) -> Optional[OrderView]:
        order = self._orders.find_by_id(order_id)
        if order is None:
            return None
        return assemble_order_view(order)

    def place_order(self, request: PlaceOrderRequest) -> PlaceOrderResponse:
        customer = self._customers.get(request.customer_id)
        product = self._products.get(request.product_id)
        if customer is None or product is None:
            raise ValueError("unknown customer or product")
        order = Order(id=self._orders.next_order_id(), customer=customer)
        order.add_item(LineItem(product=product, quantity=request.quantity))
        self._orders.save(order)
        return PlaceOrderResponse(order_id=order.id, total_cents=order.total_cents())


if __name__ == "__main__":
    address = Address(city="Munich", country="DE")
    customer = Customer(id="cust-1", name="Mirza", address=address)
    product = Product(id="prod-1", name="Keyboard", price_cents=4999)
    facade = OrderFacade(
        OrderRepository(),
        {customer.id: customer},
        {product.id: product},
    )
    placed = facade.place_order(
        PlaceOrderRequest(customer_id=customer.id, product_id=product.id, quantity=2)
    )
    view = facade.get_order_view(placed.order_id)
    assert view is not None
    print(f"order {view.order_id} total {view.total_cents} for {view.customer_name}")
```
