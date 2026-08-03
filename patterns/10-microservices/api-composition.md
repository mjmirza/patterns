---
name: API Composition
slug: api-composition
family: 10-microservices
category: Data Query
aliases: [Composite API, Aggregator Gateway, Query Aggregation Pattern]
first_described: "Chris Richardson, microservices.io, published as part of the microservices pattern language, circa 2017"
maturity: canonical
related: [backend-for-frontend, decompose-by-business-capability, self-contained-service, cqrs, saga, circuit-breaker, retry-with-backoff, api-gateway]
incompatible_with: []
verified: 2026-08-03
---

# API Composition

## 1. Name, aliases, and lineage

The canonical name is API Composition. It is catalogued by Chris Richardson as
part of the microservices pattern language at microservices.io, under the data
patterns for querying, alongside CQRS
([microservices.io, "Pattern. API Composition"](https://microservices.io/patterns/data/api-composition.html),
verified 2026-08-03). Richardson's own framing states the problem directly.
"How to implement queries in a microservice architecture." The solution is
defining an API Composer that retrieves data from multiple services and
performs an in-memory join of the results, commonly implemented by an API
Gateway. That page is also the source of the pattern's two named participants,
the API Composer and the Provider Services, which this entry uses throughout.

The pattern does not have a single canonical inventor the way Factory Method
does. It is a solution that engineering teams converged on independently once
Database per Service made cross-service SQL joins impossible, and Richardson's
catalog entry is the first place it was named and given a fixed vocabulary
rather than being re-derived ad hoc in every write-up of a gateway.

Three aliases appear in practice, and each points at a slightly different
emphasis rather than a different pattern.

- **Composite API.** Used in API-design literature to describe an endpoint that
  is not a one-to-one mapping onto a single resource or service, but a
  purpose-built shape assembled from several. The emphasis is on the shape of
  the response the client receives.
- **Aggregator Gateway.** Used in gateway-product literature (API gateway
  vendors, service mesh vendors) to describe the runtime component that
  performs the composing. The emphasis is on where the composition happens,
  namely at the edge, inside the same process that handles routing and
  authentication.
- **Query Aggregation Pattern.** Used in data-architecture writing to place the
  pattern next to CQRS and event sourcing, emphasising that it is a read-side
  concern, not a write-side one.

A GraphQL server that resolves a query by fanning out to several backing
services and stitching the results into one response tree is the modern,
schema-typed incarnation of the same idea. GraphQL Federation, described in
dimension 9, is API Composition with a formal composition algorithm and a
declarative query language layered on top of the ad hoc in-memory join
Richardson describes. The underlying problem, forces, and failure modes are
identical, which is why this entry treats REST-style hand-written composers
and GraphQL federated gateways as two implementation variants of one pattern
rather than as separate patterns.

## 2. Problem and context

A client, whether a mobile app, a web frontend, or another service, needs a
single response that draws on data owned by more than one microservice, and no
single service holds all of it.

The situation arises directly from the Database per Service pattern. Once each
service owns its own database and nothing else is permitted to read that
database directly, a query that used to be a SQL join across two tables in one
schema becomes impossible to write as SQL at all, because the two tables now
live behind two separate network boundaries, in two separate schemas, possibly
on two separate database engines. The classic worked example, repeated across
the microservices literature and reused in the code examples below, is an
e-commerce order-detail screen that needs the order (owned by an Order
Service), the customer's name and address (owned by a Customer Service), and
each line item's current price and stock level (owned by a Product Service).
Before decomposition this was one query with two joins. After decomposition it
is three independent calls that something has to combine before the screen can
render.

The context that produces this problem has three necessary conditions.

- **The data genuinely lives in separately owned stores.** If the data still
  sits in one shared database, the problem does not exist yet and introducing
  a composer would be solving a problem nobody has, see dimension 4.
- **The query is read-only and does not need to be transactionally consistent
  with the write path.** API Composition assembles a snapshot at read time. It
  is not a mechanism for keeping data consistent, and mistaking it for one is
  the most damaging misuse of the pattern, covered in dimension 11.
- **The client cannot reasonably be asked to make the calls itself.** A mobile
  client on a cellular connection making three sequential round trips to
  assemble one screen pays real, measurable latency and battery cost per extra
  hop. Sam Newman uses exactly this argument for the sibling Backend for
  Frontend pattern, describing a wishlist screen where letting the client
  orchestrate three calls to product, pricing, and inventory services is
  strictly worse than having a server-side component do it in parallel on the
  client's behalf
  ([Sam Newman, "Pattern. Backend for Frontend"](https://samnewman.io/patterns/architectural/bff/),
  verified 2026-08-03).

Outside that context, in particular when the data still lives in one
database, or when the query needs write-path consistency, API Composition is
the wrong tool and the non-applicability list in dimension 4 explains what to
reach for instead.

## 3. Forces

The pattern balances the following competing pressures. None of them is free.

- **Query simplicity for the client.** Strongly favoured. The client issues one
  request and receives one shaped response, regardless of how many services
  backed it.
- **Service autonomy.** Favoured for the provider services, sacrificed for the
  composer. Each provider service keeps its own schema, release cadence, and
  storage technology. The composer absorbs the coupling that a shared database
  would otherwise have imposed, and becomes the one component that must change
  whenever a provider's contract changes.
- **Latency.** Sacrificed relative to a single-database join, favoured relative
  to the client orchestrating the calls itself. A composer call fans out N
  requests and the response time is bounded below by the slowest of the N,
  plus the composer's own join and serialization cost. A single-database join
  a decade ago cost single-digit milliseconds. A three-way fan-out over a
  network commonly costs tens to low hundreds of milliseconds even with
  parallel calls, and the tail is set by whichever provider is currently
  slowest, not by the average.
- **Availability.** Sacrificed, and this is the force most teams underestimate.
  A single-database query fails when the database is down. A composed query
  that requires all N providers to answer fails whenever any one of the N is
  down, which by the standard availability-multiplication argument makes the
  composed endpoint's theoretical availability the product of the providers'
  individual availabilities, strictly lower than any one of them alone. Three
  services each at 99.9 percent multiply to roughly 99.7 percent for the
  composed call, before accounting for the composer's own uptime. Partial
  response strategies, covered in dimension 8, exist specifically to buy this
  force back.
- **Data freshness and consistency.** Sacrificed, because each provider call
  returns its own latest state at a slightly different instant. A composed
  response is therefore not a transactionally consistent snapshot. It is an
  approximation assembled from N independently-read snapshots, and the gap
  between them, however small, is real and can be observed under load. This is
  the same force CQRS and event sourcing are built to manage differently, and
  the trade-off matrix in dimension 12 compares the two head to head.
- **Cost.** Sacrificed in aggregate compute and network, favoured in
  development cost for any single client. The composer multiplies request
  volume against the provider services, and every field the client asks for
  that the composer over-fetches to be safe is wasted work paid on every call.
- **Operability and blast radius.** Sacrificed. The composer becomes a single
  component whose failure or degraded performance affects every query that
  touches any of the services behind it, which concentrates operational risk
  precisely at the seam that used to be a database join nobody thought about.

A pattern that gave up nothing here would mean the data was never really
distributed to begin with. The price paid is latency, availability, and
freshness, in exchange for keeping each service's storage genuinely private.

## 4. Applicability and non-applicability

Reach for API Composition when the following hold.

- Data needed by one client-facing query is owned by two or more services, each
  with Database per Service already in force, so no direct SQL join is
  possible.
- The query is read-only, and an eventually-consistent, best-effort snapshot of
  the underlying data is acceptable to the business.
- The number of providers involved in any one composed query is small, roughly
  two to five in practice, because both latency and availability degrade with
  every additional provider in the fan-out.
- The client is resource-constrained, latency-sensitive, or simply should not
  be trusted with orchestration logic, so a server-side component doing the
  fan-out on the client's behalf is strictly better than the client doing it.
- The join, once the raw data is fetched, is simple. Grouping by a shared key,
  attaching a lookup field, filtering, and light reformatting are all cheap
  in-memory operations. This is the load-bearing qualifier and the reason the
  non-applicability list below leads with query complexity.

Do NOT reach for API Composition in these cases, and the reason matters more
than the rule.

- **The join is large, or filters and sorts across the joined result.** An
  in-memory join across services cannot push a `WHERE` clause or an `ORDER BY`
  down into a provider's own database the way a real database join can.
  Fetching every row from every provider so the composer can filter or sort in
  application memory is the mechanism behind the pattern's own stated
  drawback, "inefficient in-memory joins" for large datasets
  ([microservices.io, "Pattern. API Composition"](https://microservices.io/patterns/data/api-composition.html),
  verified 2026-08-03). Richardson's own catalog names CQRS as the escape
  hatch for exactly this case, maintaining a pre-joined, pre-filtered,
  pre-sorted read model updated asynchronously from domain events, so the
  expensive join happens once at write time rather than on every read.
- **The endpoint needs transactional, read-your-writes consistency across the
  providers.** API Composition reads each provider independently and cannot
  guarantee the reads happened at the same logical instant. If the business
  requirement is that the customer must never see a stale total, that is a
  consistency guarantee this pattern cannot provide by its nature, and
  reaching for it anyway produces the silent staleness bug covered in
  dimension 11.
- **The data still lives in one shared database.** If the services have not
  actually been split at the storage layer, a composer is solving a problem
  that does not exist yet, and a plain SQL join, or a single service boundary
  that legitimately owns both pieces of data, is simpler and faster.
- **The client already needs a bespoke, screen-specific shape and the
  composition logic is entangled with UI concerns.** At that point the honest
  pattern is Backend for Frontend, which is API Composition plus an explicit
  ownership boundary per client type. Building one shared, generic composer
  and asking every client team to shoehorn their screen into it produces the
  BFF-versus-shared-gateway tension covered in dimension 13.
- **The number of providers in the fan-out is large or unbounded, especially if
  it is data-dependent (fetch a list from service A, then call service B once
  per item returned).** This is the N+1 query problem transplanted to the
  network, covered as a named failure mode in dimension 11, and it turns a
  bounded two or three-call composition into a request whose cost scales with
  the size of an upstream result the composer does not control.
- **A write operation is involved.** API Composition is a read pattern. A
  request that must write to two services and keep them consistent needs Saga,
  not a composer, and bolting write orchestration onto a composer produces a
  component doing two structurally different jobs with two different failure
  semantics.

## 5. Structure

Two participant roles, following Richardson's vocabulary, plus one supporting
role this entry adds because it recurs in every production implementation and
deserves a name of its own.

- **API Composer.** The single component the client calls. It accepts one
  client request, determines which Provider Services must be called and with
  what arguments, issues those calls (in parallel wherever the calls are
  independent of each other), and performs the in-memory join, projection, and
  reformatting needed to produce the client's response shape. It owns no
  domain data of its own. Everything it returns is either pass-through or a
  recombination of data owned elsewhere. It is commonly, but not necessarily,
  implemented inside an API Gateway, and the trade-off between the two
  placements is covered in dimension 8.
- **Provider Service.** A microservice that owns a slice of the data needed by
  the composed query, and exposes it through its own API. A Provider Service
  has no awareness that it is being composed. From its own point of view it
  answers a normal request from a caller, exactly as it would for any other
  caller. This is what keeps the pattern compatible with service autonomy, the
  composer adapts to the providers, never the other way round.
- **Result Combiner** (implementation detail, not named separately by
  Richardson, but universal enough in real systems to name here). The specific
  piece of logic inside the composer that performs the join key matching,
  handles a provider that returned nothing for a key, and decides what a
  partial result looks like when one provider fails while the others succeed.
  Naming it separately matters because it is the piece of the composer that
  needs its own unit tests, independent of the network calls, see dimension
  15.

Relationships. The API Composer depends on the public contract of every
Provider Service it calls, but no Provider Service depends on the Composer or
on any other Provider Service. The dependency direction therefore fans out
from one component to many, the mirror image of Factory Method's dependency
inversion, and it is this fan-out that both makes the pattern easy to reason
about (one place to look for the composition logic) and concentrates its
operational risk (one place that can be slow or down for reasons entirely
outside its own code).

## 6. ASCII structure diagram

```
                         +---------------------+
                         |       Client        |
                         +----------+-----------+
                                    |  one request
                                    v
                         +---------------------+
                         |    API Composer     |
                         |----------------------|
                         | + handle(request)    |
                         | - resultCombiner     |
                         +----------------------+
                          /          |          \
                fan out  /           |           \  fan out
                        /            |            \
                       v             v             v
          +------------------+ +------------------+ +------------------+
          |  Order Service   | | Customer Service | |  Product Service |
          |  (owns orders)   | | (owns customers) | |  (owns products) |
          |------------------| |------------------| |------------------|
          | + getOrder(id)   | | + getCustomer(id)| | + getPrices(ids) |
          +------------------+ +------------------+ +------------------+
                   |                     |                     |
                   v                     v                     v
          +------------------+ +------------------+ +------------------+
          |  Order Database  | |Customer Database | | Product Database |
          +------------------+ +------------------+ +------------------+

    No provider service knows the Composer exists. No provider service
    calls another provider service. Every arrow into a database is
    private to that one service.
```

## 7. Dynamics

The runtime flow has two properties worth stating plainly. First, calls to
providers that do not depend on each other's output run in parallel, never in
sequence, or the pattern silently degrades into stacking every provider's
latency on top of every other's. Second, the Result Combiner step happens only
after every parallel call has settled, whether that settling is success,
failure, or timeout, and the combiner's job is to decide what the client sees
in each of those cases, not merely in the happy path.

```
Client        API Composer      Order Svc      Customer Svc     Product Svc
  |                 |                |                |                |
  |-- GET /orders/42 --------------->|                |                |
  |                 |                |                |                |
  |                 |-- getOrder(42) --------------->|                |
  |                 |                |<-- order { customerId, items }  |
  |                 |                |                |                |
  |                 |-- getCustomer(cid) ------------------------------>
  |                 |-- getPrices([itemIds]) ----------------------------->
  |                 |   (both fire only after the order response       |
  |                 |    reveals customerId and itemIds, so this       |
  |                 |    step is sequential-then-parallel, not a       |
  |                 |    single flat fan-out of three calls)           |
  |                 |                |                |                |
  |                 |<-------------- customer { name, address } -------|
  |                 |<----------------------------------- prices[] ----|
  |                 |                |                |                |
  |                 | -- resultCombiner.join(order, customer, prices)  |
  |                 |    builds OrderDetailView                        |
  |                 |                |                |                |
  |<-- 200 OrderDetailView ----------|                |                |
  |                 |                |                |                |
```

The diagram deliberately shows the realistic two-wave shape. The first call
must complete before the composer even knows which customer and which items
to ask about, so the second wave of two calls is what actually runs in
parallel, not all three calls at once. A composed query with a genuine
dependency chain like this is common, and treating the whole thing as merely
fanning out N calls without tracing which calls actually depend on which
others' output is a frequent source of avoidable latency, covered again in
dimension 11.

## 8. Implementation variants

**Hand-written composer service.** A small, purpose-built service whose only
job is composition for one specific client need. Clear ownership, easy to
reason about, and the honest default when only one client needs the composed
shape. Costs one more deployable service per composed endpoint if teams are
not disciplined about reuse.

**Composer embedded in an API Gateway.** The composition logic lives as a
route handler or plugin inside the same edge process that already handles
authentication, rate limiting, and routing. Richardson names this as the
common placement in his own catalog entry. It avoids one extra network hop
between the client and the composer, and it reuses infrastructure the gateway
already has for retries, circuit breaking, and observability. The cost is
that the gateway, a piece of shared infrastructure many teams depend on,
starts accumulating business-specific composition logic that belongs to one
product team, which is the seam that eventually forces a split into
per-client BFFs, see dimension 13.

**Backend for Frontend as a composer.** A composer scoped to exactly one
client type, owned by the team that owns that client, per Sam Newman's
description of the pattern
([Sam Newman, "Pattern. Backend for Frontend"](https://samnewman.io/patterns/architectural/bff/),
verified 2026-08-03). This is API Composition plus an explicit ownership and
scoping decision. It is the variant to prefer once more than one client type
needs meaningfully different composed shapes from the same underlying
providers.

**GraphQL resolver-based composition.** Each field in a GraphQL schema is
backed by a resolver function, and a query that spans multiple types triggers
resolvers that individually call whichever provider owns that type. The
GraphQL execution engine itself performs the fan-out and the tree assembly, so
the composer's logic is distributed across many small resolver functions
instead of living in one hand-written join. This is a strictly more
declarative and more automated version of the same pattern, and it inherits
the N+1 failure mode in an especially sharp form because a naive resolver
written per-item, rather than batched, produces exactly the data-dependent
fan-out warned about in dimension 4. DataLoader-style batching, see dimension
11, exists specifically to fix this.

**GraphQL Federation.** Multiple independently deployed GraphQL servers, one
per domain, each declaring the types and fields it owns, composed at query
time (or, in Apollo's implementation, pre-composed into a single supergraph
schema by an offline composition step) into one federated graph served behind
a router. Apollo Federation is the best-documented implementation of this
variant, and Netflix's Domain Graph Service architecture is a real production
instance of the same idea, running at the size described in dimension 9. This
is the industrial-strength version of the pattern, with a formal
specification for how types declare foreign keys across service boundaries
(the `@key` directive, per dimension 9) rather than an ad hoc join written by
hand in application code.

**Partial-response composition.** The Result Combiner is written to return
whatever providers answered successfully within a timeout, mark the missing
fields as absent or degraded, and still return a 200 rather than failing the
whole request because one of several providers was slow or down. This is the
implementation choice that buys back the availability force sacrificed in
dimension 3, at the cost of pushing the question of what a client does with a
partially filled response onto every consumer of the composed endpoint.

**Fail-fast composition.** The opposite choice. If any required provider
fails, the composer fails the whole request. Simpler to reason about and to
test, and appropriate when a partial answer would be actively misleading, for
example a payment confirmation screen where a missing price field is worse
than no screen at all.

## 9. Known production uses

**Netflix, GraphQL Federation for the Studio domain.** Netflix built a
federated GraphQL layer, described publicly as the Domain Graph Service
architecture, where individual domain teams each own and operate their own
GraphQL schema as a Domain Graph Service, a schema registry validates and
composes those schemas, and a federated GraphQL Gateway fragments an
incoming client query into sub-queries routed to the appropriate Domain Graph
Services before merging the results back into one response tree, using the
`@key` directive and an `_entities` query to join federated types such as
Movie across service boundaries. The Netflix Technology Blog states the
gateway's fan-out and merge step adds roughly ten milliseconds of overhead in
the worst case, and that Netflix was operating more than seventy active
Domain Graph Services on this architecture
([Netflix Technology Blog, "How Netflix Scales its API with GraphQL Federation (Part 1)"](https://netflixtechblog.com/how-netflix-scales-its-api-with-graphql-federation-part-1-ae3557c187e2),
verified 2026-08-03). This is API Composition in its GraphQL Federation
variant, at a size where the composer role itself has become a distributed
system with its own schema registry.

**Shopify, the Storefront API.** Shopify's Storefront API is exposed
exclusively as GraphQL, with no REST equivalent, at a single endpoint per
store, and it lets a client retrieve products, collections, carts, checkout
state, customer information, and content such as pages and blog articles in
one request rather than through separate calls to separate resource
endpoints. Shopify's own documentation states plainly that the Storefront API
provides "a full range of commerce options" reachable through single GraphQL
queries that would otherwise require multiple calls to separate services
([Shopify, "Storefront API"](https://shopify.dev/docs/api/storefront),
verified 2026-08-03). This is API Composition delivered as a public,
externally-consumed product surface rather than an internal implementation
detail, which is a useful data point on how far the pattern scales when the
provider services are commerce domains (catalog, inventory, checkout) that
plainly cannot share one database.

**GitHub, the GraphQL API.** GitHub's public GraphQL API lets a client
traverse a single hierarchical query across what would otherwise be separate
REST resources, repositories, issues, pull requests, and users, and GitHub's
own documentation states this directly as a design goal, that nested fields
let a client "receive only the data you specify in a single round trip" and
that GraphQL is offered specifically to "replace multiple REST requests with
a single call"
([GitHub Docs, "About the GraphQL API"](https://docs.github.com/en/graphql/overview/about-the-graphql-api),
verified 2026-08-03). GitHub's REST API remains the older, resource-per-call
surface. The GraphQL API is the composed alternative sitting in front of the
same underlying domain services, which mirrors the strangler-style
introduction path most teams follow when they adopt the pattern, see
dimension 14.

**Chris Richardson's own microservices pattern catalog.** Beyond being the
citation for the pattern's name and definition, the catalog entry is itself
evidence that the pattern is a recognised, named, load-bearing part of the
standard microservices architecture vocabulary, cross-referenced from
Richardson's Database per Service and CQRS entries as the direct consequence
of, and the direct alternative to, those two patterns respectively
([microservices.io, "Pattern. API Composition"](https://microservices.io/patterns/data/api-composition.html),
verified 2026-08-03).

## 10. Consequences

Positive.

- A client issues one request instead of orchestrating several, which removes
  fan-out logic, retry logic, and partial-failure handling from every client
  that would otherwise have to duplicate it.
- Each provider service keeps full ownership of its own storage technology,
  schema, and release cadence, preserving the autonomy that Database per
  Service was adopted to buy in the first place.
- The response shape can be shaped to exactly what a client needs, which
  reduces over-fetching compared to the client hitting each provider's own
  generic resource endpoint and discarding unused fields itself.
- Composition logic lives in one place, which is easier to test, cache, and
  reason about than the same logic duplicated across every client that needs
  it.
- The composer is a natural place to add cross-cutting concerns once, timeout
  budgets, circuit breakers, response caching, and authorization checks that
  span more than one provider's data.

Negative.

- Latency is bounded below by the slowest provider in the fan-out, plus the
  composer's own join and serialization time, and every additional provider
  adds another point of failure to the latency budget.
- Availability of the composed endpoint is, by construction, lower than the
  availability of any single provider it depends on, unless partial-response
  handling explicitly buys that back, at the cost of pushing complexity onto
  every client that consumes a partial answer.
- The composed response is never a transactionally consistent snapshot. Each
  provider is read independently and can be milliseconds to seconds out of
  step with the others under load.
- In-memory joins do not scale the way database joins do. A composer that
  fetches full result sets from two providers and joins them in application
  memory pays a real cost that grows with data volume in a way a proper
  indexed database join does not.
- The composer accumulates knowledge of every provider's contract, which makes
  it a shared component that many things depend on and that changes whenever
  any provider's contract changes, concentrating coordination cost exactly
  where the pattern was meant to remove it.

## 11. Failure modes and misuse

**Using the composer as if it were a transaction.** Symptom. A customer
reports seeing a total that does not match the line items on the same screen,
and the discrepancy cannot be reproduced by replaying the same request twice.
Cause. The order total was read from one provider a few milliseconds before a
price update landed in a different provider, and the two reads, each
individually correct at the instant they happened, never agreed with each
other because API Composition never promised they would. Fix. State the
consistency guarantee explicitly in the endpoint's contract as eventual, not
strong, and if strong consistency across the fields is a genuine requirement,
this is a signal the fields should not have been split across services in the
first place, or that a Saga, not a composer, is needed for the write path
that produced the mismatch.

**The N+1 fan-out.** Symptom. A composed endpoint that returns a list of ten
items takes roughly ten times longer than one that returns a single item, and
the provider service the composer calls per item shows a proportional spike
in request volume. Cause. The composer fetches a list from one provider, then
loops over the list issuing one call per item to a second provider instead of
one batched call for all items at once. This is the classic N+1 query problem
transplanted from the database layer to the network layer, and it is the
sharpest form of the fan-out-size concern raised in dimension 4. Fix. Batch
the second call, most providers that are called this way should expose a
`getMany(ids)` endpoint precisely so composers can call it once per composed
request rather than once per item, and in GraphQL resolver implementations
this is the exact problem DataLoader-style request batching and de-duplication
exists to solve.

**No timeout budget, so one slow provider stalls the whole response.**
Symptom. p99 latency for the composed endpoint occasionally spikes to several
seconds with no corresponding spike in any single provider's own p99, and the
spike correlates with a different provider being slow each time. Cause. The
composer waits on every provider call with no explicit per-call timeout, so
whichever provider happens to be slow on a given request becomes the
composer's own latency for that request. Fix. Give every provider call an
explicit timeout scoped to the composed endpoint's own latency budget, and
decide in advance, per the partial-response variant in dimension 8, what the
composer does when a provider misses its timeout.

**Treating a missing or failed provider as a hard failure by accident.**
Symptom. A composed endpoint that shows product recommendations alongside an
order confirmation goes fully unavailable whenever the recommendations
service, a genuinely optional enhancement, is having a bad day. Cause. The
Result Combiner was written with the same all-or-nothing logic for every
provider, without distinguishing a provider whose data is essential to the
response from one whose data is a nice-to-have. Fix. Classify each provider
call as required or optional at design time, not as an afterthought during an
incident, and let optional-provider failures degrade the response rather than
fail it.

**Over-fetching because the composer does not know what the client actually
needs.** Symptom. The composer's own outbound request volume and payload size
to each provider is consistently larger than what the client-facing response
actually uses, visible by diffing the composer's provider-call payloads
against its own response payload. Cause. A REST-shaped composer commonly
calls each provider's full `GET` endpoint and then discards fields, because it
has no cheap way to ask a provider for a subset of fields. Fix. Either give
providers field-selection support, or move to the GraphQL resolver variant
where the client's own query shape naturally limits what each resolver needs
to fetch, which is precisely the efficiency argument GitHub's documentation
makes for GraphQL over REST in dimension 9.

**A shared gateway composer that silently becomes several teams' business
logic.** Symptom. A change to one product team's composed endpoint requires a
deploy of the shared API Gateway, and that deploy is on a release train
another, unrelated team also depends on, so unrelated teams start blocking
each other's releases. Cause. Composition logic for several unrelated client
needs was added to one shared gateway process instead of being split by
client ownership. Fix. Split into per-client-type Backend for Frontend
composers, each independently deployable and owned by the team that owns that
client, covered in dimension 13.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | API Composition | CQRS (materialized read model) | Backend for Frontend | Client-side orchestration (no server composer) | Database per Service with shared read replica |
|---|---|---|---|---|---|
| Read latency, simple query | Medium. Bounded by slowest provider in the fan-out | Low. One indexed read against a pre-joined store | Medium, same mechanics as API Composition, scoped to one client | High. Client pays every round trip sequentially or manages its own concurrency | Low, but only where the shared replica remains legal to use |
| Read latency, large or filtered query | Poor. In-memory filter and join do not scale | Good. Filtering and sorting happen once, in the read model, at write time | Same limits as API Composition | Poor, and now duplicated per client | Good, ordinary indexed query |
| Data freshness guarantee | Eventual, assembled per request from independent reads | Eventual, but the staleness window is explicit and bounded by the event pipeline's own lag | Eventual, same as API Composition | Eventual, and now the client must reason about which call is stale | Can be near-real-time depending on replication lag |
| Write-path coupling | None. Read-only pattern | None on the read side, the read model is built asynchronously from events already published for other reasons | None | None | High. A shared replica quietly recreates a hidden dependency on another service's schema |
| Implementation cost to introduce | Low to medium, one new component | High. Requires an event pipeline, a projection, and its own storage | Medium, one component per client type instead of one shared component | Effectively zero server-side cost, all cost lands on the client | Low if the replica infrastructure already exists |
| Ongoing operational cost | Medium. One more component to run, monitor, and scale | Medium to high. An extra storage engine and an event-processing pipeline to keep healthy | Medium, multiplied by the number of client types | None server-side, but support burden multiplies across every client implementation | Low, but couples two services' deploy and schema evolution |
| Availability of the composed query | Lower than any single provider's availability, unless mitigated with partial response | Higher once built, the read model answers even if a provider service is briefly down, because it was already materialized | Same as API Composition | Depends entirely on the client's own retry logic | Depends on replica health, decoupled from the owning service's own uptime |
| Fits a client-specific response shape | Yes, that is the point | Only if the read model itself was designed for that shape | Yes, and better, because it is scoped to exactly one client | Yes, entirely client-controlled | No, the replica exposes the owning service's own schema |

Reading of the table. API Composition wins for small, simple, read-only
queries where introducing a whole materialized read model would be excessive.
CQRS wins once the query is large, filtered, sorted, or needs to answer fast
and often regardless of provider health. Backend for Frontend wins once more
than one client type needs a genuinely different composed shape from the
same providers. Client-side orchestration is rarely the right default but is
occasionally correct for a thin, trusted, well-connected internal tool where
a server-side hop buys nothing. A shared read replica is a trap dressed as a
shortcut, and it is included here specifically because teams under time
pressure reach for it as a substitute for a composer and end up with a worse
form of the exact coupling Database per Service was adopted to remove.

## 13. Related and incompatible patterns

- **Decompose by Business Capability / Decompose by Subdomain.** The
  upstream cause. These decomposition patterns are what split the data
  across services in the first place, and API Composition is the direct
  consequence, the pattern that makes cross-service reads possible again
  after that split.
- **Self-Contained Service.** Composes cleanly. A well-formed Self-Contained
  Service is exactly what a Provider Service in this pattern's structure
  should be, one that can answer requests without synchronously calling any
  other service.
- **Backend for Frontend.** The scoped, client-owned specialisation of this
  pattern. Every BFF is an API Composer. Not every API Composer is scoped
  narrowly enough to be called a BFF. Reach for a BFF the moment more than
  one client type needs meaningfully different composed shapes, per the
  failure mode in dimension 11.
- **CQRS.** The named alternative for the case this pattern handles badly,
  large or filtered queries. Richardson's own catalog draws this line
  directly, and the trade-off matrix in dimension 12 expands on it. The two
  are not mutually exclusive within one system, a large system commonly uses
  API Composition for its simple cross-service reads and CQRS for its
  expensive ones.
- **Saga.** The write-side analogue that API Composition is sometimes
  mistaken for. A Saga coordinates a sequence of local transactions across
  services to keep a write consistent. API Composition coordinates a
  sequence of reads to answer a query. Confusing the two, using a composer to
  paper over a write that should have been a Saga, is the transactional
  misuse named in dimension 11.
- **Circuit Breaker and Retry with Backoff.** Necessary companions rather
  than alternatives. A composer that calls several providers without a
  circuit breaker per provider will happily keep hammering a provider that is
  already failing, and one without a bounded retry policy will happily
  compound a slow provider's latency into the composer's own p99. Neither
  pattern is optional in a production composer, they are the mechanism that
  makes the failure modes in dimension 11 survivable rather than catastrophic.
- **API Gateway.** A frequent host, not a required one. Many production
  composers live inside an API Gateway process, as Richardson notes, but the
  two are conceptually separate, a gateway that only routes and
  authenticates, with no composition logic, is not doing this pattern at all.
- **GraphQL Federation.** A formalised, declarative implementation variant of
  this pattern rather than a separate pattern, covered in dimension 8 and
  demonstrated in production at Netflix in dimension 9.
- **Shared database access.** Actively incompatible. A composer that quietly
  reads a second service's database directly instead of calling its API is
  not this pattern, it is the exact coupling Database per Service exists to
  prevent, wearing the composer's name. See the shared read replica trap
  called out explicitly in dimension 12.

## 14. Refactoring path in and out

Introducing the pattern into a system that currently either shares a database
or asks clients to orchestrate calls themselves.

1. Identify one concrete client-facing query that currently either joins
   across a shared database, or requires the client to make more than one
   call and stitch the results itself. Confirm the query is read-only.
2. Confirm the data genuinely lives, or is about to live, behind separate
   service boundaries. If it does not yet, this step is premature and the
   decomposition pattern should land first.
3. Introduce the composer as a thin pass-through first, calling only the
   provider whose data the client already gets today, with no join logic yet.
   This proves the wiring and the deployment path before any real complexity
   is added.
4. Add the second provider call, run it in parallel with the first wherever
   the two do not depend on each other's output, and write the Result
   Combiner as its own testable function, not inline in the request handler.
5. Add an explicit per-provider timeout and classify each provider as
   required or optional, per dimension 11, before this reaches production
   traffic, not after the first incident.
6. Point the client at the new composed endpoint and retire its own
   client-side orchestration, or the direct multi-table query, once the
   composed endpoint's behaviour has been verified against the old path,
   ideally by running both in parallel for a period and diffing the results,
   the same strangler-style verification the Strangler Application pattern
   describes for the wider migration this composer usually sits inside.
7. Delete the shared-database access path, or the client-side orchestration
   code, once nothing depends on it. Leaving it in place as a fallback is how
   a shared read replica trap, dimension 12, quietly survives a migration
   that was meant to remove it.

Removing the pattern when it stops earning its place. The signal is almost
always the same, the query the composer answers has grown past what an
in-memory join can do efficiently.

1. Measure the composer's own latency and payload size against its providers'
   latency and payload size. A composer whose join step, not its network
   calls, is the larger share of its own latency has outgrown the pattern.
2. Introduce a materialized read model fed by the same domain events the
   providers already publish for other reasons, following CQRS.
3. Point the composed endpoint at the new read model instead of at the live
   providers, keeping the same external contract so clients notice nothing.
4. Retire the composer's fan-out and join logic once the read model has been
   running in parallel long enough to trust its freshness characteristics
   under real load.

## 15. Testing and verification

Easier because of the pattern.

- The Result Combiner, once separated from the network calls as recommended
  in dimension 5, is pure data-in data-out logic and can be unit tested with
  hand-built fixture responses for every provider, with no network, no test
  containers, and no mocking framework beyond simple stand-in values.
- Each provider integration can be tested against a contract test rather than
  a live service, so the composer's test suite runs fast and does not become
  flaky because a dependency's staging environment is down.
- Partial-response and required-versus-optional provider behaviour, the
  hardest part of this pattern to get right in production, is exactly the
  kind of branching logic that is cheap to enumerate and assert against in a
  unit test, every combination of which providers succeeded, failed, or timed
  out, once the combiner is a pure function.

Harder because of the pattern.

- Correctness of the whole call depends on the real behaviour of every
  provider under real network conditions, which a unit-tested combiner alone
  cannot prove, so an integration or contract-test layer against real or
  containerised providers is still necessary before trusting the composer in
  production.
- Load testing has to account for the fan-out multiplier, a load test that
  drives N requests per second at the composer is actually driving up to N
  times the number of providers requests per second at the backend, and a
  naive load test that forgets this under-provisions the providers relative
  to what production traffic will actually do.
- Consistency-window bugs, the transactional misuse in dimension 11, are
  timing-dependent and notoriously hard to reproduce in a deterministic test.
  They are better caught by an explicit test that writes to two providers at
  slightly staggered times and asserts the composer's documented eventual
  consistency behaviour, rather than by hoping a flaky integration test
  happens to catch the race.

Techniques that apply.

- **Contract tests per provider**, in the Consumer-Driven Contracts sense, so
  the composer's assumptions about each provider's response shape are
  verified independently of whether the provider's own test suite passes,
  catching a breaking provider change before it reaches the composer in
  production rather than after.
- **Fixture-driven combiner tests**, enumerating success, failure, timeout,
  and empty-result cases for every provider combination the combiner's logic
  actually branches on, which for a two or three-provider composer is a
  small, fully enumerable set.
- **Fault-injection testing against a real provider**, deliberately killing
  or slowing one provider in a staging environment and asserting the composed
  endpoint degrades the way the design intended, rather than hard failing
  when a design intended a partial response, or vice versa.
- **Shadow or dark-launch comparison**, running the new composed endpoint
  alongside the path it is replacing and diffing the two outputs on real
  traffic before cutting clients over, the verification technique named in
  step 6 of the refactoring path above.

## 16. Observability signals

A composer's own health can look perfectly fine while it is silently
returning degraded responses, so what gets measured matters more here than
in most patterns.

What to record.

- Per-provider call latency and error rate, labelled by provider name, so a
  slow or failing provider is visible immediately rather than only showing up
  as a vague increase in the composer's own overall latency.
- Per-provider timeout rate, distinct from error rate, since a provider that
  is technically healthy but consistently misses its allotted budget is a
  capacity problem, not an outage.
- A counter of composed responses labelled by completeness, full, partial (one
  or more optional providers missing), and failed (a required provider
  missing), so partial-response degradation is a first-class, dashboarded
  signal rather than something only discovered by reading logs after a
  complaint.
- Fan-out size per request, the number of provider calls one client request
  actually triggered, to catch the N+1 failure mode from dimension 11 the
  moment it starts happening rather than after it has been in production for
  months.
- The composer's total request latency alongside the maximum of its own
  provider-call latencies for the same request, so the composer's own join
  and serialization overhead is visible separately from network time it does
  not control.

A healthy instance on a dashboard. Per-provider error and timeout rates track
each provider's own published SLO. The partial-response counter sits near
zero and only moves in step with a known provider incident. Fan-out size per
request is flat and matches the number of providers the composed endpoint was
designed to call, not a number that grows with the size of any single
provider's result set.

A failing instance. One provider's error-rate line climbs while the others
stay flat, immediately naming which dependency needs attention without
reading a single log line. The partial-response counter climbs steadily with
no corresponding incident, which usually means a required provider was
silently reclassified as optional, or an optional provider quietly became
load-bearing for a client nobody told the platform team about. Fan-out size
per request grows in step with the size of a list a provider returned, which
is the N+1 fan-out visible on a graph before it shows up as a latency
complaint.

## 17. Security and privacy implications

The composer sits at a genuine trust boundary and a genuine data-aggregation
point, and both of those properties carry real security weight beyond the
availability and latency concerns already covered.

**Authorization has to be checked once per provider, not once for the whole
request.** A client authorized to see its own order is not automatically
authorized to see every field the Customer Service and Product Service would
return for the identifiers involved. A composer that forwards a single
coarse-grained authorization check and then blindly assembles whatever every
provider returns can leak a field the requesting client was never entitled
to, an authorization gap that is invisible in a single-provider system
because a single service naturally scopes its own responses to its own
authorization model, and only becomes visible once a composer starts
combining several providers' outputs into one response.

**Aggregation itself is a privacy risk independent of any single field's
sensitivity.** A field-by-field review of what each provider exposes can
individually pass a privacy review while the composed combination, a name
plus a location plus a purchase history plus a device identifier assembled
into one response, becomes meaningfully more re-identifying or more sensitive
than any of its parts. This is a standard concern across privacy engineering,
and it applies with particular force to a component whose entire job is
combining data other components deliberately kept separate. Any composed
endpoint that touches personal data should be reviewed as a whole, not by
checking each provider call against its own privacy policy in isolation.

**A single composer is a natural place for credential and rate-limit
concentration to become an attack surface.** Because the composer calls
several internal services on the client's behalf, it commonly holds, or is
trusted to forward, broader internal network access and broader service
credentials than any one client would otherwise have. A vulnerability in the
composer, for example a request-forgery flaw that lets an attacker control
which provider identifiers it queries, can be used to reach data across
every provider it is trusted to call, which is a strictly larger blast radius
than compromising any single provider directly, and the composer's own
authentication and input validation deserve security review proportional to
that broader reach rather than to the composer's own comparatively small
codebase.

On denial of service, the same fan-out multiplier that shows up as a
performance concern in dimensions 3 and 11 is also a security concern. A
composer that lets client-supplied input control the size of its fan-out, for
example accepting an unbounded list of item identifiers and issuing one call
per identifier, converts a single cheap client request into an expensive
multi-service request, which is an amplification vector an attacker can use
against the providers behind the composer without ever touching them
directly. Bounding and validating fan-out size at the composer, not only at
each individual provider, is the mitigation.

## Code examples

Three languages where the pattern is genuinely idiomatic in different ways.
TypeScript shows the concurrent-fetch shape most JavaScript backend teams
reach for first, using `Promise.allSettled` specifically because it is the
mechanism that makes partial-response composition, dimension 8, natural
rather than bolted on. Go shows the same shape using goroutines and channels,
the idiomatic Go concurrency primitives, with an explicit per-call timeout
via `context`, the mechanism dimension 11 names as the fix for an unbounded
provider stall. Python shows an `asyncio`-based composer, the shape most
Python backend frameworks use for this kind of I/O-bound fan-out, with
`asyncio.gather` and `return_exceptions=True` performing the same
partial-failure-tolerant role as TypeScript's `allSettled`.

### TypeScript

```typescript
interface Order {
  id: string;
  customerId: string;
  items: { productId: string; quantity: number }[];
}
interface Customer {
  id: string;
  name: string;
  address: string;
}
interface Price {
  productId: string;
  amountCents: number;
}

interface Providers {
  getOrder(id: string): Promise<Order>;
  getCustomer(id: string): Promise<Customer>;
  getPrices(productIds: string[]): Promise<Price[]>;
}

interface OrderDetailView {
  orderId: string;
  customerName: string | null;
  customerAddress: string | null;
  lineItems: { productId: string; quantity: number; amountCents: number | null }[];
  degraded: boolean;
}

async function composeOrderDetail(
  orderId: string,
  providers: Providers,
): Promise<OrderDetailView> {
  const order = await providers.getOrder(orderId);
  const productIds = order.items.map((i) => i.productId);

  const [customerResult, pricesResult] = await Promise.allSettled([
    providers.getCustomer(order.customerId),
    providers.getPrices(productIds),
  ]);

  const customer = customerResult.status === "fulfilled" ? customerResult.value : null;
  const prices = pricesResult.status === "fulfilled" ? pricesResult.value : [];
  const priceByProduct = new Map(prices.map((p) => [p.productId, p.amountCents]));

  return {
    orderId: order.id,
    customerName: customer?.name ?? null,
    customerAddress: customer?.address ?? null,
    lineItems: order.items.map((item) => ({
      productId: item.productId,
      quantity: item.quantity,
      amountCents: priceByProduct.get(item.productId) ?? null,
    })),
    degraded: customerResult.status === "rejected" || pricesResult.status === "rejected",
  };
}

// A fixture-driven test of the combiner logic, no real network.
async function demo(): Promise<void> {
  const providers: Providers = {
    getOrder: async () => ({
      id: "42",
      customerId: "c1",
      items: [{ productId: "p1", quantity: 2 }],
    }),
    getCustomer: async () => ({ id: "c1", name: "Ada Lovelace", address: "London" }),
    getPrices: async () => [{ productId: "p1", amountCents: 1999 }],
  };
  const view = await composeOrderDetail("42", providers);
  console.log(JSON.stringify(view));
}

demo();
```

### Go

```go
package main

import (
	"context"
	"fmt"
	"time"
)

type Order struct {
	ID         string
	CustomerID string
	Items      []LineItem
}

type LineItem struct {
	ProductID string
	Quantity  int
}

type Customer struct {
	ID      string
	Name    string
	Address string
}

type Price struct {
	ProductID   string
	AmountCents int
}

type Providers interface {
	GetOrder(ctx context.Context, id string) (Order, error)
	GetCustomer(ctx context.Context, id string) (Customer, error)
	GetPrices(ctx context.Context, productIDs []string) ([]Price, error)
}

type ViewLineItem struct {
	ProductID   string
	Quantity    int
	AmountCents *int
}

type OrderDetailView struct {
	OrderID         string
	CustomerName    string
	CustomerAddress string
	LineItems       []ViewLineItem
	Degraded        bool
}

type customerResult struct {
	customer Customer
	err      error
}

type pricesResult struct {
	prices []Price
	err    error
}

func ComposeOrderDetail(ctx context.Context, p Providers, orderID string) (OrderDetailView, error) {
	order, err := p.GetOrder(ctx, orderID)
	if err != nil {
		return OrderDetailView{}, fmt.Errorf("order lookup failed. %w", err)
	}

	productIDs := make([]string, len(order.Items))
	for i, item := range order.Items {
		productIDs[i] = item.ProductID
	}

	fanCtx, cancel := context.WithTimeout(ctx, 300*time.Millisecond)
	defer cancel()

	custCh := make(chan customerResult, 1)
	priceCh := make(chan pricesResult, 1)

	go func() {
		c, err := p.GetCustomer(fanCtx, order.CustomerID)
		custCh <- customerResult{c, err}
	}()
	go func() {
		pr, err := p.GetPrices(fanCtx, productIDs)
		priceCh <- pricesResult{pr, err}
	}()

	cr := <-custCh
	pr := <-priceCh

	priceByProduct := map[string]int{}
	for _, price := range pr.prices {
		priceByProduct[price.ProductID] = price.AmountCents
	}

	view := OrderDetailView{
		OrderID:  order.ID,
		Degraded: cr.err != nil || pr.err != nil,
	}
	if cr.err == nil {
		view.CustomerName = cr.customer.Name
		view.CustomerAddress = cr.customer.Address
	}
	for _, item := range order.Items {
		var amount *int
		if v, ok := priceByProduct[item.ProductID]; ok {
			amount = &v
		}
		view.LineItems = append(view.LineItems, ViewLineItem{
			ProductID: item.ProductID, Quantity: item.Quantity, AmountCents: amount,
		})
	}
	return view, nil
}

type fakeProviders struct{}

func (fakeProviders) GetOrder(ctx context.Context, id string) (Order, error) {
	return Order{ID: id, CustomerID: "c1", Items: []LineItem{{ProductID: "p1", Quantity: 2}}}, nil
}
func (fakeProviders) GetCustomer(ctx context.Context, id string) (Customer, error) {
	return Customer{ID: id, Name: "Ada Lovelace", Address: "London"}, nil
}
func (fakeProviders) GetPrices(ctx context.Context, ids []string) ([]Price, error) {
	return []Price{{ProductID: "p1", AmountCents: 1999}}, nil
}

func main() {
	view, err := ComposeOrderDetail(context.Background(), fakeProviders{}, "42")
	if err != nil {
		panic(err)
	}
	fmt.Printf("%+v\n", view)
}
```

### Python

```python
import asyncio
from dataclasses import dataclass, field


@dataclass
class Order:
    id: str
    customer_id: str
    items: list[tuple[str, int]]


@dataclass
class Customer:
    id: str
    name: str
    address: str


@dataclass
class Price:
    product_id: str
    amount_cents: int


@dataclass
class ViewLineItem:
    product_id: str
    quantity: int
    amount_cents: int | None


@dataclass
class OrderDetailView:
    order_id: str
    customer_name: str | None
    customer_address: str | None
    line_items: list[ViewLineItem] = field(default_factory=list)
    degraded: bool = False


class Providers:
    async def get_order(self, order_id: str) -> Order: ...
    async def get_customer(self, customer_id: str) -> Customer: ...
    async def get_prices(self, product_ids: list[str]) -> list[Price]: ...


async def compose_order_detail(providers: Providers, order_id: str) -> OrderDetailView:
    order = await providers.get_order(order_id)
    product_ids = [product_id for product_id, _ in order.items]

    customer_result, prices_result = await asyncio.gather(
        providers.get_customer(order.customer_id),
        providers.get_prices(product_ids),
        return_exceptions=True,
    )

    degraded = isinstance(customer_result, Exception) or isinstance(prices_result, Exception)
    customer = customer_result if not isinstance(customer_result, Exception) else None
    prices = prices_result if not isinstance(prices_result, Exception) else []
    price_by_product = {p.product_id: p.amount_cents for p in prices}

    line_items = [
        ViewLineItem(product_id, quantity, price_by_product.get(product_id))
        for product_id, quantity in order.items
    ]

    return OrderDetailView(
        order_id=order.id,
        customer_name=customer.name if customer else None,
        customer_address=customer.address if customer else None,
        line_items=line_items,
        degraded=degraded,
    )


class FakeProviders(Providers):
    async def get_order(self, order_id: str) -> Order:
        return Order(id=order_id, customer_id="c1", items=[("p1", 2)])

    async def get_customer(self, customer_id: str) -> Customer:
        return Customer(id=customer_id, name="Ada Lovelace", address="London")

    async def get_prices(self, product_ids: list[str]) -> list[Price]:
        return [Price(product_id="p1", amount_cents=1999)]


async def main() -> None:
    view = await compose_order_detail(FakeProviders(), "42")
    print(view)


if __name__ == "__main__":
    asyncio.run(main())
```

## 18. References

1. Chris Richardson. microservices.io pattern catalog, "Pattern. API
   Composition". https://microservices.io/patterns/data/api-composition.html
   Verified 2026-08-03. Source of the pattern's name, the API Composer and
   Provider Services vocabulary, the stated problem and solution, and the
   named relationship to Database per Service and CQRS used throughout
   dimensions 1, 2, 4, 5, 12, and 13.
2. Sam Newman. "Pattern. Backend for Frontend".
   https://samnewman.io/patterns/architectural/bff/
   Verified 2026-08-03. Source of the Backend for Frontend definition, the
   SoundCloud and Phil Calcado attribution, and the wishlist parallel-call
   example used in dimensions 2, 8, and 13.
3. Netflix Technology Blog. "How Netflix Scales its API with GraphQL
   Federation (Part 1)".
   https://netflixtechblog.com/how-netflix-scales-its-api-with-graphql-federation-part-1-ae3557c187e2
   Verified 2026-08-03. Source of the Domain Graph Service, schema registry,
   federated gateway, `@key` directive, `_entities` query, the ten
   millisecond overhead figure, and the seventy-plus Domain Graph Service
   scale figure used in dimensions 8 and 9.
4. Shopify. "Storefront API". https://shopify.dev/docs/api/storefront
   Verified 2026-08-03. Source of the GraphQL-only, single-endpoint,
   multi-domain commerce composition claims used in dimension 9.
5. GitHub. "About the GraphQL API".
   https://docs.github.com/en/graphql/overview/about-the-graphql-api
   Verified 2026-08-03. Source of the single-round-trip, multi-resource
   composition claim used in dimension 9.

One claim could not be independently verified in this session and is
recorded here rather than silently dropped. An attempt to fetch Apollo
GraphQL's Federation documentation, for the general terms subgraph,
supergraph, and router named in dimension 8, returned HTTP 404 on both
candidate URLs tried. No specific figure or quotation attributed to Apollo
appears anywhere in this entry. The general terms themselves are also
independently attested by the Netflix Domain Graph Service architecture
citation above, which uses the equivalent federated-gateway vocabulary.
