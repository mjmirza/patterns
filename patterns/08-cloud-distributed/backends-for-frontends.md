---
name: Backends for Frontends
slug: backends-for-frontends
family: 08-cloud-distributed
category: Cloud and Distributed
aliases: [BFF, Backend for Frontend, Backend-for-Frontend]
first_described: "Calçado 2013, catalogued by Newman 2015"
maturity: established
related: [gateway-aggregation, anti-corruption-layer, facade, adapter, circuit-breaker, retry, bulkhead, materialized-view, api-gateway]
incompatible_with: []
verified: 2026-08-02
---

# Backends for Frontends

## 1. Name, aliases, and lineage

The canonical name is Backends for Frontends, almost always abbreviated to
BFF in conversation, tickets, and diagrams. The abbreviation is written as
one BFF service or one BFF layer, and a codebase with more than one of them
usually names each instance after the client it serves, for example
`mobile-bff` and `web-bff`.

The pattern's origin traces to SoundCloud's mobile engineering work around
2013. Sam Newman, who catalogued and popularised the pattern in its current
written form, credits the naming to Phil Calçado, at the time an engineer at
SoundCloud, writing that the pattern's name and its first public description
"is generally credited to Phil Calçado" during his time at SoundCloud
(Sam Newman, ["Pattern. Backends For Frontends"](https://samnewman.io/patterns/architectural/bff/),
verified 2026-08-02). Newman's page is the closest thing the pattern has to a
canonical definition, and it states the core move in one sentence, that
instead of building one general purpose backend for all the various
interfaces that might want to consume it, you build a backend per user
experience, tightly coupled to that one experience and owned by the same
team that owns the experience (same source, verified 2026-08-02). Newman
names two organisations that had shipped the pattern by the time he wrote
the piece, SoundCloud and REA, the Australian real estate company (same
source, verified 2026-08-02).

Microsoft's Azure Architecture Center later catalogued the same shape under
the identical name, Backends for Frontends, and its page opens by crediting
Newman directly, stating the pattern is "based on the Backends for Frontends
pattern by Sam Newman"
([Microsoft Learn, Backends for Frontends pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/backends-for-frontends),
verified 2026-08-02). Chris Richardson's independent microservices pattern
catalog, built out of his book *Microservices Patterns*, files the same
mechanic as a variant of API Gateway rather than as a pattern in its own
right, describing it as the case where "instead of a single API gateway
there are multiple API gateways, one for each kind of client,"
and points a reader specifically toward "the backends for frontends pattern"
by name for that variant
([microservices.io, API Gateway pattern](https://microservices.io/patterns/apigateway.html),
verified 2026-08-02). That difference in filing matters more than it looks.
Newman treats BFF as an independent pattern about team ownership and product
shaping. Richardson treats it as a deployment topology choice layered on top
of the more general API Gateway pattern. Both readings are defensible and a
reader will meet both in the wild, so this entry treats BFF as its own
pattern while being explicit, in dimension 13 below, about exactly how it
specialises Gateway Aggregation and API Gateway.

No single-author book chapter equivalent to the Gang of Four catalog or to
Evans' Domain-Driven Design exists for BFF. The pattern lives in blog posts,
vendor architecture guides, and conference talks rather than in a bound
catalog, which is why this entry marks its maturity as established rather
than canonical. established here means the pattern is settled in practice
and widely named the same way across the industry, but it has not passed
through the kind of single authoritative text that fixes a pattern's
boundaries the way the GoF book fixed Factory Method's.

## 2. Problem and context

A product ships to more than one kind of client. A web single page app, a
native iOS app, a native Android app, a smart TV app, a partner integration
consuming the same data over an API. Early on, one backend service answers
all of them, because writing one API is cheaper than writing several and the
clients start out asking for roughly the same data.

The clients do not stay similar. Newman's own framing of the origin case is
exactly this shift, a mobile client added on top of an existing web backend,
where mobile has a slower and less reliable network, a smaller screen that
wants fewer fields per response, and a release schedule gated by app store
review rather than by a simple deploy
([Sam Newman, Backends For Frontends](https://samnewman.io/patterns/architectural/bff/),
verified 2026-08-02). Microsoft's framing of the same context problem states
it as a general shape. an application "initially designed with a desktop web
UI and a corresponding backend service" grows a second interface later, and
"the capabilities of a mobile device differ significantly from a desktop
browser in terms of screen size, performance, and display limitations"
([Microsoft Learn, Backends for Frontends pattern, Context and problem section](https://learn.microsoft.com/en-us/azure/architecture/patterns/backends-for-frontends),
verified 2026-08-02).

The shared backend absorbs the difference by growing. A `platform` query
parameter appears on an endpoint, then a second one, then a third. Response
shaping logic for one client's field list sits next to shaping logic for
another's. A change one team needs, a smaller payload for a slow network, a
merged field two mobile screens need in one round trip, has to be reviewed
and accepted by whichever team owns the shared backend, and validated
against every other client that same endpoint serves, because a shared
resource cannot be changed for one consumer without a chance of breaking
another. Microsoft's own statement of the resulting friction is direct. a
"backend service frequently encounters competing demands from multiple
frontend systems," which "result in frequent updates" and slow delivery for every
consumer, and a team split between backend owners and
frontend owners produces a disconnect where "changes requested by one
frontend team must be validated with other frontend teams before
integration"
([Microsoft Learn, Backends for Frontends pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/backends-for-frontends),
verified 2026-08-02).

The pattern applies specifically in the case where a product genuinely has
more than one distinct kind of frontend, each with its own team, its own
release schedule, and its own real difference in what it needs from the data
layer. It is a response to organisational friction as much as to technical
shape, which is why dimension 3 below treats team topology as one of the
named forces rather than a footnote.

## 3. Forces

The following weighing is engineering judgement drawn from the sources
above and from how the pattern is discussed in practice, not a sourced
measurement.

Coupling versus reuse pulls in one direction. A shared backend concentrates
reuse of query and aggregation logic, one implementation serves every
client. Splitting into per client BFFs trades that reuse for tight coupling
between each BFF and its one frontend, which is a deliberate trade, not an
accident, because the entire point of the pattern is letting that coupling
happen safely instead of fighting it inside a shared service.

Team autonomy versus platform consistency pulls the other way. When a
frontend team owns its BFF end to end, it can pick its own release schedule,
its own response shapes, and in some organisations its own implementation
language, without coordinating a shared backend's release plan. Azure's guidance
names this directly, stating that with a BFF "frontend teams independently
manage their own BFF service, which gives them control over language
selection" as well as their own release schedule, workload priorities, and
feature integration timing
([Microsoft Learn, Backends for Frontends pattern, Solution section](https://learn.microsoft.com/en-us/azure/architecture/patterns/backends-for-frontends),
verified 2026-08-02). The cost of that independence is platform inconsistency, N
teams solving the same authentication check, the same retry policy, the same
logging format, N slightly different ways, unless those cross cutting
concerns are deliberately factored out, which is exactly the caution Azure's
own considerations list raises, that "the BFF service should only handle
client specific logic related to a specific user experience," while
cross cutting features "should be abstracted" into separate concerns such
as gatekeeping and rate limiting (same source, Problems and considerations
section, verified 2026-08-02).

Operational cost versus tailored performance is the third force. Each BFF is
its own deployable, its own on call surface, its own dependency set to patch.
Azure's guidance is explicit that this is a real cost to weigh, telling a
reader to "evaluate your optimal number of services depending on the
associated costs," because "maintaining and deploying more services means
increased operational overhead" with its own lifecycle, deployment,
maintenance, and security needs (same source, verified 2026-08-02). Against
that cost sits the payoff, a response shaped for one client's exact needs,
fewer fields sent to a mobile client on a slow connection, fewer round trips
for a desktop client that wants everything on one screen at once.

Latency is a genuine but usually small cost, not a dominant one. Every BFF
adds a network hop between client and downstream services, and Azure's
guidance flags this plainly, warning to "review the service level objectives
when you add a new service" because "increased latency might occur" from
the extra hop (same source, verified 2026-08-02). Richardson's parallel
guidance on the closely related API Composition mechanic judges the added
latency as usually acceptable in practice, writing that the extra network
round trip an aggregating layer introduces "is usually not a problem"
([microservices.io, API Composition pattern](https://microservices.io/patterns/data/api-composition.html),
verified 2026-08-02). That is Richardson's stated judgement about API
Composition specifically, carried here as a reasonable expectation for BFF's
similar aggregation step, not a measured claim about BFF itself.

Security surface is a force the pattern can shrink rather than grow, when
used for its most concentrated modern purpose. Section 17 covers this in
depth, but it belongs in the forces list here because it changes how a team
should weigh the cost of standing up a BFF at all. A BFF that terminates
OAuth tokens on the server side removes an entire class of browser side
token theft that a purely client side single page app cannot avoid, which
the relevant IETF specification states directly and is quoted in full in
dimension 17.

## 4. Applicability and non-applicability

Reach for Backends for Frontends when the following hold together, not
individually.

- More than one genuinely different kind of client consumes the same
  underlying services, and the differences are real, not cosmetic. Screen
  size, network reliability, data volume needed per screen, or release
  schedule differ enough that a shared response shape forces compromise on
  at least one client.
- Each client type is owned by, or can be owned by, a distinct team, and
  that team wants to move at its own pace without staging changes through a
  shared backend team's queue. Azure's own "when to use this pattern"
  guidance lists exactly this, that a "shared or general purpose backend
  service requires substantial development overhead to maintain," and that
  a team wants to "optimize the backend for the requirements of specific
  client interfaces"
  ([Microsoft Learn, Backends for Frontends pattern, When to use this pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/backends-for-frontends),
  verified 2026-08-02).
- A shared backend has grown branching logic keyed on a platform or client
  type parameter, which is the concrete, observable symptom that a single
  general purpose API has already outgrown its own shape.
- Security posture benefits from moving credentials and tokens out of the
  browser or the mobile client entirely, discussed fully in dimension 17.

Do not reach for it, and Azure's guidance states this plainly rather than
leaving it implicit, when either of these hold.

- "Interfaces make the same or similar requests to the backend," in which
  case a single shared API, or a single Gateway Aggregation layer, serves
  every client without the duplication cost a second or third BFF adds
  ([Microsoft Learn, Backends for Frontends pattern, When to use this pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/backends-for-frontends),
  verified 2026-08-02).
- "Only one interface interacts with the backend," in which case there is
  nothing to differentiate a BFF from the backend it would sit in front of,
  and the extra layer is pure overhead with no offsetting benefit (same
  source, same section, verified 2026-08-02).

Two further non-applicability cases follow from how the pattern is actually
used in the field, stated here as engineering judgement rather than as a
sourced rule.

- A small team building a single product with one client type has no forces
  for the pattern to resolve. There is one frontend, one team, one release
  schedule. The BFF's entire value proposition, letting per client concerns
  diverge safely, has nothing to act on.
- A team already running a federated GraphQL layer with client aware
  resolvers or persisted queries has, in effect, solved the same problem a
  different way. Azure's own considerations list names this trade-off
  directly, noting that "if your organization uses GraphQL with frontend
  specific resolvers, BFF services might not add value to your
  applications" (same source, Problems and considerations section, verified
  2026-08-02). Dimension 12 below expands this comparison.

## 5. Structure

- **Frontend client.** The web app, mobile app, or other interface that
  makes requests. Exactly one client type talks to exactly one BFF.
- **BFF service.** A deployable service, owned by the same team as its
  client, that receives requests shaped the way that client's screens want
  them, and returns responses shaped the same way. It has no data of its own.
- **Downstream service or services.** The domain services, an orders
  service, a shipping service, a catalog service, that own the actual data
  and business logic. A BFF calls one or several of these per incoming
  request.
- **Aggregation and shaping logic, inside the BFF.** The part of the BFF
  that fans out to the downstream services it needs for a given screen,
  waits for their responses, and assembles a single response shaped exactly
  for that screen. This is the part of the pattern that overlaps most
  directly with Gateway Aggregation, covered in dimension 13.
- **Cross cutting layer, outside the BFF.** Authentication, rate limiting,
  and routing, ideally factored into a shared entry point in front of every
  BFF rather than duplicated inside each one. Azure's reference architecture
  places this responsibility on Azure API Management sitting in front of
  the per client BFFs, handling "authorization," "monitoring," "request
  caching," and "routing and aggregation" before a request ever reaches a
  specific BFF
  ([Microsoft Learn, Backends for Frontends pattern, Example section](https://learn.microsoft.com/en-us/azure/architecture/patterns/backends-for-frontends),
  verified 2026-08-02).

Two structural relationships carry the pattern's actual claim. First, one
BFF per client type, never one BFF shared across two different client types
with different needs, because sharing reintroduces the exact coupling
problem the pattern exists to remove. Second, a BFF is owned end to end by
the team that owns its one client, not by a separate backend team, which is
an organisational relationship as much as a code relationship, and is the
piece of the structure most catalogs describe least precisely.

## 6. ASCII structure diagram

```
                          +----------------------------+
                          |   Downstream domain layer  |
                          |----------------------------|
                          |  Orders  Service            |
                          |  Shipping Service            |
                          |  Catalog Service              |
                          +--------------^---------------+
                                         |
                     +-------------------+-------------------+
                     |                                       |
           +---------+----------+                +-----------+----------+
           |   Mobile BFF        |                |    Web BFF            |
           |  (owned by mobile   |                |  (owned by web team)  |
           |   team)             |                |                        |
           |  - fewer fields     |                |  - fuller payload     |
           |  - one round trip   |                |  - richer aggregation |
           +---------+----------+                +-----------+----------+
                     |                                       |
                     v                                       v
           +---------+----------+                +-----------+----------+
           |   Mobile client     |                |     Web client        |
           +---------------------+                +------------------------+
```

Each BFF sits between exactly one client and the shared downstream services.
The downstream layer is shared. The BFFs are not.

## 7. Dynamics

The runtime flow for one incoming request follows the same shape in every
BFF, only the number and choice of downstream calls differs by client.

```
Mobile client                Mobile BFF          Orders Svc   Shipping Svc
     |                             |                   |            |
     | GET /order-summary/ord_123 |                   |            |
     |---------------------------->|                   |            |
     |                             | GET /orders/ord_123           |
     |                             |------------------->|            |
     |                             | GET /shipments/ord_123        |
     |                             |------------------------------->|
     |                             |<-------------------|            |
     |                             |<------------------------------|
     |                             | (join + shrink fields)         |
     |<----------------------------|                   |            |
     |  { id, total, status }      |                   |            |
```

The two downstream calls can run in parallel, because neither depends on
the other's result, which is exactly what the TypeScript example in
dimension 8 does with `Promise.all`. When one downstream call genuinely
depends on data from another, the BFF sequences them instead, calling the
first, reading a field from its response, and using that field to shape the
second call. A well built BFF applies its own timeout and retry policy per
downstream call rather than one blanket timeout for the whole request,
because a slow shipping service should not silently block an order total
the mobile client could otherwise show immediately, an application of the
Circuit Breaker and Retry patterns described in dimension 13.

The failure path matters as much as the happy path. When one downstream
call fails or times out, the BFF has to decide, per field, whether to return
a partial response with that field omitted or defaulted, or to fail the
whole request. That decision belongs in the BFF because only the BFF's owning
team knows which fields its one screen can tolerate missing, which is one of
the concrete reasons the pattern places aggregation logic here instead of in
a shared, client agnostic layer that cannot make that judgment call.

## 8. Implementation variants

- **REST fan out and join, the default shape.** The BFF exposes a small
  number of REST endpoints, each shaped for one screen, and internally calls
  several downstream REST or gRPC services, joins their responses, and
  returns one payload. This is the shape shown in every code example in
  this entry and the shape both Newman's and Microsoft's descriptions
  assume by default.
- **GraphQL BFF.** The BFF exposes a single GraphQL endpoint instead of
  several REST routes, letting the client itself choose which fields it
  needs per query rather than the BFF hard coding a response shape per
  route. Azure's guidance notes this shift explicitly, that "many BFF
  services traditionally relied on REST APIs, but GraphQL implementations
  are emerging as an alternative," adding that with GraphQL "the querying
  mechanism eliminates the need for a separate BFF layer because it allows
  clients to request the data that they need without relying on predefined
  endpoints"
  ([Microsoft Learn, Backends for Frontends pattern, Solution section](https://learn.microsoft.com/en-us/azure/architecture/patterns/backends-for-frontends),
  verified 2026-08-02). Note the tension inside that same sentence, a
  GraphQL layer with client aware resolvers is itself doing BFF like work,
  it is only doing it inside a shared schema rather than inside per client
  services. Dimension 12 treats this as a real alternative, not a variant,
  because the operational model differs enough to matter.
- **Serverless per route BFF.** Each BFF endpoint is implemented as an
  individual serverless function rather than a long lived service process,
  scaling and billing per request. Azure's own worked example uses exactly
  this shape, hosting each client's BFF logic "as an Azure function"
  behind API Management (same source, Example section, verified
  2026-08-02). This variant trades operational simplicity, no server to
  keep warm, for per invocation cold start latency, which matters more for
  a mobile client on an already slow connection than for a desktop client.
- **BFF as an OAuth token handling boundary.** The BFF's primary job in
  this variant is not data shaping at all, it is holding the client's
  session and OAuth tokens server side and issuing the client a session
  cookie instead, so no bearer token ever reaches JavaScript running in a
  browser. This is the specific configuration the IETF draft quoted in
  dimension 17 recommends, and it can be layered on top of any of the three
  variants above.
- **Shared BFF platform with per client configuration.** Rather than N
  fully independent BFF codebases, a single BFF framework or service
  template is shared across client teams, with per client configuration for
  field selection and aggregation rules layered on top. This reduces the
  duplicated boilerplate cost Newman is explicit about accepting in the
  canonical version of the pattern, at the cost of reintroducing some of
  the shared ownership coordination the pattern exists to avoid. This
  variant is engineering judgement, drawn from how larger organisations
  are observed handling the pattern in larger deployments, not a sourced claim from a
  named catalog.

## 9. Known production uses

- **SoundCloud**, the pattern's origin case. Sam Newman's catalog entry
  states the naming and the first public description of the pattern trace
  to SoundCloud's mobile engineering work, credited to Phil Calçado, when
  the company needed a backend layer shaped for its mobile clients that
  its existing general purpose backend could not serve well
  ([Sam Newman, Backends For Frontends](https://samnewman.io/patterns/architectural/bff/),
  verified 2026-08-02).
- **REA Group**, the Australian real estate classifieds company. Newman's
  same catalog entry names REA alongside SoundCloud as an organisation that
  had implemented the pattern by the time he wrote his description (same
  source, verified 2026-08-02).
- **The OAuth 2.0 for Browser-Based Applications working group draft.** The
  IETF's own draft specification for securing browser based apps recommends
  the BFF architecture by name as the strongly preferred pattern for
  "business applications, sensitive applications, and applications that
  handle personal data"
  ([IETF, OAuth 2.0 for Browser-Based Applications, draft-ietf-oauth-browser-based-apps](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-browser-based-apps),
  verified 2026-08-02). This is a standards body recommendation rather than
  a single company's engineering blog, and it is included here because it
  demonstrates the pattern has moved from one company's internal practice
  into cross industry security guidance, a stronger form of "production use"
  than any one deployment.
- **Microsoft's own Azure reference architecture.** Microsoft's Azure
  Architecture Center ships a full worked reference implementation of the
  pattern, using Azure API Management as the shared entry point and Azure
  Functions as the per client BFF implementations for a mobile client and a
  desktop client, described in detail in the Example section of its pattern
  page
  ([Microsoft Learn, Backends for Frontends pattern, Example section](https://learn.microsoft.com/en-us/azure/architecture/patterns/backends-for-frontends),
  verified 2026-08-02). A vendor reference architecture is weaker evidence
  than an independent company's production deployment, and this entry
  labels it as such, but it is documented in enough operational detail,
  named services, a described request flow, and named cross cutting
  concerns, to count as a genuine, checkable implementation rather than a
  marketing diagram.

## 10. Consequences

Positive.

- Each client gets a response shaped exactly for its own constraints,
  fewer fields for a slow mobile connection, richer aggregation for a
  desktop screen that wants everything at once, without either client
  compromising for the other's sake.
- A frontend team can change its BFF, its release schedule, and in many
  organisations its implementation language, without coordinating that
  change through a shared backend team's release plan, which Azure's guidance
  names directly as a benefit of the pattern
  ([Microsoft Learn, Backends for Frontends pattern, Solution section](https://learn.microsoft.com/en-us/azure/architecture/patterns/backends-for-frontends),
  verified 2026-08-02).
- Client side attack surface shrinks when the BFF also serves as the OAuth
  token handling boundary, because there are, in the words of the relevant
  IETF draft, "simply no tokens available to extract from the browser"
  ([IETF, OAuth 2.0 for Browser-Based Applications](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-browser-based-apps),
  verified 2026-08-02), covered fully in dimension 17.
- A shared backend service is smaller and simpler once client specific
  shaping logic moves out of it, which Azure's guidance also states as a
  direct benefit, that a BFF service, being smaller and less complex than a
  shared backend, "can make the application easier to manage"
  ([Microsoft Learn, Backends for Frontends pattern, Solution section](https://learn.microsoft.com/en-us/azure/architecture/patterns/backends-for-frontends),
  verified 2026-08-02).

Negative.

- Operational overhead grows with every additional BFF, each one its own
  deployable with its own on call rotation, its own dependency patching,
  its own lifecycle, which Azure's guidance names as a cost to weigh before
  adding a service
  ([Microsoft Learn, Backends for Frontends pattern, Problems and considerations](https://learn.microsoft.com/en-us/azure/architecture/patterns/backends-for-frontends),
  verified 2026-08-02).
- Duplicated logic across BFFs is a near certain outcome, not an edge case.
  Two BFFs that both need an order summary will both write aggregation code
  for it, and the pattern offers no built in mechanism to prevent that.
  Azure's own guidance names this directly, stating "code duplication is a
  probable outcome of this pattern," and framing the decision as a trade-off
  between duplication and a better tailored experience per client (same
  source, verified 2026-08-02).
- Cross cutting concerns can leak into individual BFFs if a team is not
  disciplined about factoring them out, producing N slightly different
  implementations of the same authentication check or the same rate limit,
  which Azure's guidance flags as something to actively guard against by
  keeping the BFF focused only on "client specific logic related to a
  specific user experience" (same source, verified 2026-08-02).
- An extra network hop adds latency versus a client calling downstream
  services directly, which Azure's guidance flags as something to check
  against service level objectives when adding a new BFF (same source,
  verified 2026-08-02).

## 11. Failure modes and misuse

Symptom. A single BFF grows a branch for `if (clientType === "tablet")`
inside what was supposed to be one client's dedicated service.
Cause. Two genuinely different client experiences were merged into one
BFF for expediency, usually because the second client type was assumed at
first to be close enough to the first to share a service.
Fix. Split the BFF along the same line the pattern's own applicability
test draws, one BFF per client type whose needs genuinely diverge, per the
guidance in dimension 4. If the two clients truly make the same requests,
per Azure's own non-applicability case, merge them back into one service
deliberately rather than leaving a half merged branch inside a nominally
per client BFF.

Symptom. Every BFF in the system implements its own slightly different
JWT validation, its own slightly different rate limiting, its own slightly
different request logging format, and a security audit finds three
different bugs in three different implementations of the same check.
Cause. Cross cutting concerns that Azure's guidance explicitly calls
out as things to abstract out of the BFF layer were instead copied into
each BFF independently, because standing up a shared gateway felt like more
work up front than repeating a small auth check.
Fix. Move authentication, rate limiting, and routing into a shared
entry point in front of every BFF, the role Azure's own reference
architecture assigns to Azure API Management sitting in front of the per
client Azure Functions
([Microsoft Learn, Backends for Frontends pattern, Example section](https://learn.microsoft.com/en-us/azure/architecture/patterns/backends-for-frontends),
verified 2026-08-02), and leave each BFF holding only the logic specific
to its one client's data shape.

Symptom. A single downstream service outage takes down every client at
once, defeating the isolation the pattern was supposed to provide.
Cause. A shared downstream dependency was called without a timeout,
retry policy, or circuit breaker inside any BFF, so a slow or failing
downstream call blocks every BFF that calls it, and by extension every
client, at the same time.
Fix. Apply Circuit Breaker and Retry at the boundary between each BFF
and its downstream calls, per client, so a mobile BFF can degrade
gracefully, returning cached or partial data, while a web BFF facing the
same downstream outage makes its own independent decision about how to
degrade. This is engineering judgement drawn from how the closely related
Gateway Aggregation pattern's own failure mode guidance is framed, applied
here because a BFF performs the same fan out and join step internally.

Symptom. A team stands up a BFF for a single, unremarkable web client
and finds it has added a deploy pipeline, an on call rotation, and a whole
service's worth of operational surface for no measurable benefit over
calling the shared backend directly.
Cause. The pattern was reached for out of habit or out of following a
platform convention, rather than because any of the forces in dimension 3
were actually present, most commonly in the specific non-applicability
case Azure's own guidance names, "only one interface interacts with the
backend"
([Microsoft Learn, Backends for Frontends pattern, When to use this pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/backends-for-frontends),
verified 2026-08-02).
Fix. Remove the BFF and let the single client call the shared backend,
or the shared Gateway Aggregation layer, directly. Reintroduce a BFF later
if and when a genuinely different second client type actually appears.

Symptom. A frontend developer opens a browser's network tab and finds a
long lived OAuth access token sitting in `localStorage`, readable by any
script that manages to execute on the page.
Cause. The team built a BFF for data shaping but never moved OAuth
token handling into it, leaving the browser to hold and send bearer tokens
directly, which is precisely the exposure the relevant IETF draft warns
against.
Fix. Move the OAuth authorization code flow and token storage entirely
into the BFF, issuing the browser a same site session cookie instead of a
bearer token, per the architecture the IETF draft describes and dimension
17 quotes in full.

## 12. Trade-off matrix

| Force | Backends for Frontends | Gateway Aggregation, single shared gateway | GraphQL Gateway, federated, client aware resolvers |
|---|---|---|---|
| Number of client-facing services | One per client type | One, shared by all clients | One, shared by all clients |
| Who owns response shape | The client's own team, per BFF | A shared platform team | A shared platform team, though clients self-select fields per query |
| Duplication risk | High. Azure names it a "probable outcome" of the pattern, verified 2026-08-02 | Low. One implementation serves every client | Low to moderate. Shared schema, but client-specific resolvers can still diverge |
| Operational surface | N services, N deploy pipelines, N on-call rotations | One service | One service, though a federated GraphQL gateway adds its own composition layer |
| Best fit per Azure's guidance | Clients have genuinely different needs and separate teams | Clients make "the same or similar requests" | Organization already runs GraphQL with per-client resolvers |
| Team autonomy | High, each team ships its own BFF on its own schedule | Low, changes go through the shared gateway's owning team | Moderate, resolvers can be owned per team inside one schema |
| Cross-cutting concern handling | Must be deliberately factored out of each BFF, or it duplicates | Naturally centralised, one place to add auth and rate limiting | Naturally centralised at the gateway, per-field authorization is possible but adds complexity |

Richardson's catalog entry on the closely related API Composition mechanic,
the join step every one of the three columns above performs internally in
some form, states the general cost of that join step plainly, that fetching
from several services and joining in memory "increases the overhead of
network calls," which every column here inherits to some degree, and that
this overhead "is usually not a problem"
([microservices.io, API Composition pattern](https://microservices.io/patterns/data/api-composition.html),
verified 2026-08-02).

The honest summary, and this line is engineering judgement rather than a
sourced claim, is that the choice between these three usually turns on team
topology before it turns on technology. An organisation with strong, separate
teams per client platform tends toward BFF because it matches how the teams
already work. An organisation with one platform team serving several thin
clients tends toward Gateway Aggregation because there is no team boundary
for a BFF's ownership model to exploit. An organisation already committed to
a federated GraphQL schema across its services tends to let client aware
resolvers absorb the BFF's job rather than standing up parallel REST
services, which is the exact tension Azure's own guidance names when it says
GraphQL with frontend specific resolvers can make a separate BFF layer
redundant.

## 13. Related and incompatible patterns

- **Gateway Aggregation.** The pattern this entry's own related list opens
  with. Gateway Aggregation is the general mechanic, a gateway that
  "dispatches requests to the various back-end systems, and aggregates the
  results before it sends them back to the client"
  ([Microsoft Learn, Gateway Aggregation pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/gateway-aggregation),
  verified 2026-08-02). BFF specialises that mechanic by giving each client
  type its own dedicated gateway instance instead of sharing one gateway
  across every client, which is exactly how Richardson's own catalog files
  it, as the case where "instead of a single API gateway there are multiple
  API gateways, one for each kind of client"
  ([microservices.io, API Gateway pattern](https://microservices.io/patterns/apigateway.html),
  verified 2026-08-02). Every BFF internally performs a Gateway Aggregation
  style fan out and join, dimension 7's dynamics diagram is that join step
  in miniature.
- **API Gateway.** The broader family both BFF and Gateway Aggregation sit
  inside. An API Gateway can proxy requests through without aggregation, a
  behaviour a BFF rarely needs because a BFF's whole reason to exist is
  shaping and combining, not passthrough.
- **Anti-Corruption Layer.** A related but distinct defensive pattern. An
  Anti-Corruption Layer translates an external or legacy model into a
  cleaner internal one to protect a system's own domain model from
  contamination. A BFF translates an internal model outward, into the shape
  a specific client needs, which is close to the opposite direction of
  translation, even though both patterns place a translating layer between
  two models that should not directly touch.
- **Adapter.** The GoF structural pattern that makes one interface conform
  to another that a caller expects. A BFF is, at the level of a single
  downstream call, doing adapter-shaped work, translating a downstream
  service's response shape into what the client expects, repeated and
  aggregated across every call the BFF makes for one request.
- **Facade.** The GoF structural pattern that presents a simplified
  interface over a more complex subsystem. A BFF is a Facade specialised
  for exactly one client, over exactly the subset of downstream services
  that one client needs, with the simplification decisions made by that
  client's own team rather than by a subsystem's original authors.
- **Circuit Breaker and Retry.** Applied inside a BFF at the boundary of
  each downstream call it makes, so a slow or failing downstream dependency
  degrades gracefully for one client instead of taking down every BFF that
  depends on it, per the failure mode discussed in dimension 11.
- **Materialized View.** A pattern a BFF sometimes leans on rather than
  composes with directly. If a BFF's aggregation work is expensive and its
  underlying data changes slowly relative to how often it is read, a
  materialized view precomputed from the downstream services can replace
  the BFF's live fan out for that one endpoint, trading freshness for
  latency.

No pattern in this repository's family is genuinely incompatible with BFF in
the way Anti-Corruption Layer is incompatible with Shared Kernel. The
closest tension is architectural rather than a hard conflict, a federated
GraphQL Gateway and a fleet of REST BFFs solve the same problem in
different ways, and running both at once for the same client type is
redundant rather than incompatible, which is why this entry's frontmatter
lists no incompatible patterns.

## 14. Refactoring path in and out

Introducing a BFF into an existing shared backend.

1. Identify which endpoints and fields exist only to serve one specific
   client, the tell-tale sign being a `platform` or `client` parameter that
   branches response shaping logic.
2. Stand up a new, empty BFF service for that one client, sitting between
   the client and the existing shared backend.
3. Move the client-specific branches out of the shared backend and into
   the new BFF, one endpoint at a time, having the BFF call the now-simpler
   shared backend to get the data it aggregates and reshapes.
4. Point the one client at its new BFF, verify parity with the old shared
   endpoint's behaviour, then retire the client-specific branch from the
   shared backend.
5. Repeat for the next client type only when that client's own forces from
   dimension 3 justify it, never all at once, and never for a client whose
   needs still genuinely match the shared backend's existing shape.

Removing a BFF that has stopped earning its place.

1. Confirm the non-applicability case actually holds now, per dimension 4,
   most often because the client's needs converged with another client's
   needs, or because the client itself was retired.
2. Merge the BFF's remaining client-specific logic back into a shared
   Gateway Aggregation layer or directly into the downstream services it
   called, whichever destination keeps the logic closest to where it is
   still used.
3. Point the client at the merged destination, verify parity, then retire
   the now-redundant BFF deployment.
4. Recover the BFF's operational surface, its deploy pipeline, its on-call
   rotation, its dependency patching, explicitly, since that recovered cost
   is the entire benefit of having removed it.

## 15. Testing and verification

Most of this dimension is engineering practice rather than a single sourced
claim, stated plainly here as judgement.

A BFF's own aggregation and shaping logic is straightforward to unit test in
isolation, because its downstream dependencies are simple interfaces to
fake. Each of the three code examples in dimension 8 constructs its BFF with
its two downstream clients passed in explicitly, which is what makes a fake
`OrdersClient` and a fake `ShippingClient` trivial to substitute in a test
without touching any network. What is easy to test because of the pattern
is exactly this, per client response shaping logic sitting in one small,
dependency-injected place instead of scattered across branches inside a
shared backend.

What became harder is testing the full request path end to end, because a
BFF's behaviour under a real downstream failure, a timeout, a partial
response, a retry exhausting, only shows up when its downstream calls are
exercised against something that actually behaves like the real service
under stress, not a fake that always returns instantly. Contract tests
between a BFF and each downstream service it calls catch a real class of
bug a unit test with a hand-written fake cannot, a downstream service
silently changing its response shape in a way the BFF's fake never
reflected. Running the BFF against a downstream service's published schema,
or against a recorded and replayed set of real downstream responses, closes
that gap.

Per-client BFF ownership creates one specific testing responsibility that
shared backends do not have. Because each BFF's owning team decides, per
field, how to degrade when a downstream call fails, per dimension 7, that
degradation decision needs its own explicit test, asserting the BFF returns
a sensible partial response, or fails cleanly, when a specific downstream
dependency is unavailable, not merely that the happy path returns the right
shape.

## 16. Observability signals

Per-BFF request latency, broken out by which downstream calls a given
endpoint makes, is the most useful single signal, because it is the fastest
way to see whether a slow response is the BFF's own aggregation logic or a
slow downstream dependency it is waiting on. Tracing each downstream call a
BFF makes as its own span, tagged with the BFF's name and the client type it
serves, turns dimension 7's dynamics diagram into something an observability
platform can actually render for a real, slow request.

Per-downstream-call error rate, tagged by which BFF made the call, surfaces
the failure mode named in dimension 11 early, a single downstream outage
taking down every BFF that depends on it looks, on a dashboard, like the
same error rate spiking simultaneously across every BFF that calls that one
downstream service, which is the pattern a team should alert on before a
customer notices every client degrading at once.

A healthy BFF, on a dashboard, shows request latency mostly explained by
its slowest downstream call rather than by its own aggregation logic, a low
and stable error rate that tracks its downstream dependencies' own error
rates rather than exceeding them, and a response payload size that stays
close to what its one client actually needs, which is the metric most
directly tied to the pattern's stated purpose. A failing BFF shows the
opposite, latency inflating beyond what any single downstream call
explains, meaning the BFF's own logic has become the bottleneck, or an
error rate that exceeds every downstream dependency's own error rate,
meaning the BFF itself is introducing failures its downstream services are
not responsible for.

Operational overhead itself is worth measuring directly, not only inferring.
Tracking the count of active BFF services against a target headcount and
alerting when that count grows without a corresponding new client type
appearing is a direct, mechanical check against the exact drift the failure
mode in dimension 11 describes, a BFF standing up for a client whose forces
never actually justified one.

## 17. Security and privacy implications

This is the dimension where BFF earns its strongest, most concentrated
modern justification, and it is sourced directly rather than left to
judgement.

The IETF's own working draft for securing browser-based applications states
the core problem with handling OAuth tokens directly inside a browser
plainly. malicious JavaScript that manages to execute on a page runs with
"the same privileges as the legitimate application code," which lets it
"steal tokens directly" from wherever the browser stores them, obtain fresh
tokens "by injecting hidden iframes" to initiate new OAuth flows, and
intercept legitimate tokens "before legitimate use"
([IETF, OAuth 2.0 for Browser-Based Applications, draft-ietf-oauth-browser-based-apps](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-browser-based-apps),
verified 2026-08-02). No amount of careful client-side coding removes this
exposure, because the attack does not exploit a bug in the application's
own code, it exploits the fact that any script running on the same page
shares the same privileges as that code.

The draft's recommended fix is the BFF pattern applied specifically to
authentication, and it states the mechanism directly, that with a BFF
architecture, tokens "are only available to the BFF," the server side
component, meaning "there are simply no tokens available to extract from
the browser" at all (same source, verified 2026-08-02). The browser holds
only a session cookie, ideally scoped `HttpOnly` and `SameSite`, which a
script running on the page cannot read even if it compromises the page
entirely, because the cookie is never exposed to JavaScript in the first
place. The draft's own conclusion states the resulting security posture
directly, that with this architecture "the application's attack surface
does not increase by using OAuth" (same source, verified 2026-08-02),
strongly recommending it "for business applications, sensitive
applications, and applications that handle personal data" (same source,
verified 2026-08-02).

This has a direct privacy implication beyond token theft specifically.
Because the BFF, not the browser, holds the token needed to call downstream
services, personal data returned by those downstream calls also never has
to transit through client-side JavaScript's reach in the same way a
purely client-side single page app calling downstream APIs directly would
expose it, narrowing the set of code that ever handles a person's data in
the clear on the client side.

A BFF that aggregates fields from several downstream services also creates
a specific, easy-to-miss over-exposure risk of its own, and this next point
is engineering judgement rather than a sourced claim. A BFF built by copying
a downstream service's full response and trimming only the fields a
specific client's UI happens to render risks silently forwarding fields the
UI does not render but a determined caller can still read directly from the
network response, for example a field never shown on screen but still
present in the JSON payload. The discipline the pattern rewards here is
explicit allow-listing of fields inside the BFF's shaping logic, returning
exactly what a client needs and nothing else, rather than filtering only at
the presentation layer above the network boundary.

## 18. References

- Sam Newman, ["Pattern. Backends For Frontends"](https://samnewman.io/patterns/architectural/bff/),
  personal site, verified 2026-08-02.
- Microsoft, ["Backends for Frontends pattern"](https://learn.microsoft.com/en-us/azure/architecture/patterns/backends-for-frontends),
  Azure Architecture Center, updated 2025-03-19, verified 2026-08-02.
- Microsoft, ["Gateway Aggregation pattern"](https://learn.microsoft.com/en-us/azure/architecture/patterns/gateway-aggregation),
  Azure Architecture Center, verified 2026-08-02.
- Chris Richardson, ["API Gateway pattern"](https://microservices.io/patterns/apigateway.html),
  microservices.io, verified 2026-08-02.
- Chris Richardson, ["API Composition pattern"](https://microservices.io/patterns/data/api-composition.html),
  microservices.io, verified 2026-08-02.
- Chris Richardson, *Microservices Patterns*, Manning, 2018, chapter 7.
- IETF, ["OAuth 2.0 for Browser-Based Applications"](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-browser-based-apps),
  draft-ietf-oauth-browser-based-apps, verified 2026-08-02.

## Code examples

Every example below implements the same scenario, an order-summary BFF for
a mobile client that fans out to two downstream services, an orders service
and a shipping service, joins their responses, and returns a payload shaped
for a mobile screen. Each was executed at authoring time.

### TypeScript

Compiled with `npx tsc --strict --target es2020 --module commonjs bff.ts`
and run with `node bff.js`. The run printed an order with id ord_123, a
formatted total of $45.99, and a status of in_transit, matching the fake
data the two client stand-ins above return.

```typescript
interface Order { id: string; totalCents: number; }
interface Shipment { orderId: string; status: string; }

class OrdersClient {
  async getOrder(id: string): Promise<Order> {
    return { id, totalCents: 4599 };
  }
}

class ShippingClient {
  async getShipment(orderId: string): Promise<Shipment> {
    return { orderId, status: "in_transit" };
  }
}

interface OrderSummary { id: string; total: string; status: string; }

class MobileOrderBFF {
  constructor(private orders: OrdersClient, private shipping: ShippingClient) {}

  async getOrderSummary(orderId: string): Promise<OrderSummary> {
    const [order, shipment] = await Promise.all([
      this.orders.getOrder(orderId),
      this.shipping.getShipment(orderId),
    ]);
    return {
      id: order.id,
      total: `$${(order.totalCents / 100).toFixed(2)}`,
      status: shipment.status,
    };
  }
}

async function main() {
  const bff = new MobileOrderBFF(new OrdersClient(), new ShippingClient());
  const summary = await bff.getOrderSummary("ord_123");
  console.log(summary);
}

main();
```

The `Promise.all` call is the dynamics diagram's parallel fan out from
dimension 7 made literal. Neither downstream call depends on the other, so
both fire at once and the BFF waits for the slower of the two rather than
paying their combined latency.

### Python

Run with `python3 bff.py`. The run printed the same shape as the
TypeScript example, id ord_123, total $45.99, status in_transit.

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class Order:
    id: str
    total_cents: int

@dataclass
class Shipment:
    order_id: str
    status: str

class OrdersClient:
    def get_order(self, order_id: str) -> Order:
        return Order(id=order_id, total_cents=4599)

class ShippingClient:
    def get_shipment(self, order_id: str) -> Optional[Shipment]:
        return Shipment(order_id=order_id, status="in_transit")

class MobileOrderBFF:
    def __init__(self, orders: OrdersClient, shipping: ShippingClient):
        self.orders = orders
        self.shipping = shipping

    def get_order_summary(self, order_id: str) -> dict:
        order = self.orders.get_order(order_id)
        shipment = self.shipping.get_shipment(order_id)
        return {
            "id": order.id,
            "total": f"${order.total_cents / 100:.2f}",
            "status": shipment.status if shipment else "unknown",
        }

if __name__ == "__main__":
    bff = MobileOrderBFF(OrdersClient(), ShippingClient())
    print(bff.get_order_summary("ord_123"))
```

This version calls each downstream client sequentially rather than
concurrently, which is a fair default for a script this small, and is the
shape a real Python BFF would replace with `asyncio.gather` over two
`async def` client methods once the two calls are genuinely independent and
worth parallelising, the same trade-off the TypeScript example already
makes explicit.

### Go

Run with `go run main.go` inside its own module directory. The run
printed the same order id, total, and status as the two examples above.

```go
package main

import "fmt"

type Order struct {
	ID         string
	TotalCents int
}

type Shipment struct {
	OrderID string
	Status  string
}

type OrdersClient struct{}

func (c OrdersClient) GetOrder(id string) Order {
	return Order{ID: id, TotalCents: 4599}
}

type ShippingClient struct{}

func (c ShippingClient) GetShipment(orderID string) Shipment {
	return Shipment{OrderID: orderID, Status: "in_transit"}
}

type OrderSummary struct {
	ID     string  `json:"id"`
	Total  float64 `json:"total"`
	Status string  `json:"status"`
}

type MobileOrderBFF struct {
	orders   OrdersClient
	shipping ShippingClient
}

func (b MobileOrderBFF) GetOrderSummary(orderID string) OrderSummary {
	order := b.orders.GetOrder(orderID)
	shipment := b.shipping.GetShipment(orderID)
	return OrderSummary{
		ID:     order.ID,
		Total:  float64(order.TotalCents) / 100,
		Status: shipment.Status,
	}
}

func main() {
	bff := MobileOrderBFF{orders: OrdersClient{}, shipping: ShippingClient{}}
	summary := bff.GetOrderSummary("ord_123")
	fmt.Printf("%+v\n", summary)
}
```

Go's example calls both downstream methods sequentially on purpose, in the
struct's `GetOrderSummary` method, mirroring how a real Go BFF would instead
run them inside two goroutines joined with a `sync.WaitGroup` or an
`errgroup.Group` once real network calls replace the in-memory stand-ins
above, the same concurrency point the TypeScript and Python examples each
make in their own idiom.

Java and Rust were considered and set aside for this entry, not because the
pattern does not translate, it does, but because the same fan out and join
shape is already shown fully in three languages above without adding a
fourth idiom that would only restate it. A Java version would most
naturally use `CompletableFuture.allOf` for the parallel fan out, the same
role `Promise.all` plays in the TypeScript example above.
