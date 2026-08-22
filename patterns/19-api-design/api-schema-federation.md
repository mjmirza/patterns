---
name: API and Schema Federation
slug: api-schema-federation
family: 19-api-design
category: API Composition
aliases: [Schema Federation, GraphQL Federation, Federated GraphQL, Composite Schemas]
first_described: "Apollo GraphQL, 2019, Apollo Federation announcement blog post"
maturity: established
related: [api-gateway, api-composition, graphql-resolver-pattern, graphql-dataloader]
incompatible_with: []
verified: 2026-08-22
---

# API and Schema Federation

## 1. Name, aliases, and lineage

The canonical name is Schema Federation, most often called GraphQL Federation
or, informally, simply Federation. Apollo GraphQL introduced the pattern in a
2019 blog post titled "Apollo Federation," stating the goal plainly. "expose
one graph for all of our organization's data without experiencing the
pitfalls of a monolith," aiming for "the best of both worlds, a complete
schema to connect all of our data with a distributed architecture." (Apollo
GraphQL Blog, see reference 1.)

This pattern is still moving toward a settled, vendor-neutral form, and the
entry states that plainly rather than smoothing it over. In 2023 the GraphQL
Foundation formed the Composite Schemas Working Group, a subcommittee of the
official GraphQL Working Group, with the stated mission. "To build a
specification that covers many of the shared concerns when building a larger
GraphQL schema as a composite of many smaller GraphQL schemas." (GraphQL
Foundation, composite-schemas-wg, see reference 5.) The founding RFC names
the reason a shared specification is needed. "the wide variety of options can
make it challenging to design schemas in a way that will be easy to compose
later," and the contributor list spans direct competitors in the composition
space, Apollo, Hasura, The Guild, WunderGraph, Netflix, and more, alongside
Apollo. (GraphQL Working Group RFC, see reference 6.) So this catalogue
records the maturity as established rather than canonical, real and widely
adopted in production, with its formal specification still an active
standards effort rather than a finished one.

## 2. Problem and context

An organization with many teams, each owning a distinct part of the domain,
faces two bad choices for its API layer without this pattern. A single
monolithic schema owned by one team forces every other team to route changes
through that team, and forces a person's understanding of a User or a
Product type to live in one place even when no single team actually
controls every aspect of it. Apollo names this directly. "no single team
controls every aspect of an important type like a User or Product, so the
definition of these types should be distributed across teams and codebases,
rather than centralized." (Apollo GraphQL Blog, see reference 1.)

The other bad choice is a plain API gateway that fans out to several
backend services and stitches the responses together by hand, in gateway
code. This keeps ownership distributed, but the composition logic itself,
deciding how a User from one service links to an Order from another, sits
centrally in the gateway, so every cross-team relationship still routes
through one team's code. Apollo's own migration guide from the earlier
"schema stitching" approach names this precisely. "When using a
schema-stitching gateway, your linking logic typically resides in the
gateway itself." (Apollo Federation Docs, see reference 2.)

Schema federation is meant to give both properties at once, one unified
schema for consumers, with the definition of that schema, and the logic
that links its pieces together, distributed across the teams that actually
own each piece.

## 3. Forces

- Team autonomy against gateway complexity. Federation lets each team own
  and deploy its own subgraph independently. Apollo names the benefit
  directly. "Each team can work independently without needing to maintain
  multiple API layers," and consumers "interact with the federated schema
  as if it were a monolith." (Apollo GraphOS Docs, see reference 8.) The
  cost is a real piece of infrastructure, the router, that must plan and
  merge every cross-subgraph query, and a schema-composition process every
  team's change now has to pass.
- Decentralized ownership against decentralized governance. In the
  federation model, "linking logic resides in each subgraph," (Apollo
  Federation Docs, see reference 2) rather than in one central gateway.
  That is exactly what buys the autonomy, and exactly what removes the
  single team that used to enforce cross-cutting concerns. The trade-off is
  real. a person working across the supergraph now has to reason about
  data models owned by several different teams to fully understand one
  query's path, rather than reading one team's own code end to end.
- A statically validated composed schema against a naive request-time
  aggregation layer. A plain gateway or the API Composition pattern joins
  results at request time, in code, with no shared schema contract to
  validate against. Federation instead composes subgraph schemas into one
  supergraph schema before any request runs, and rejects an incompatible
  change at composition time. "It's like a compiler error that prevents
  you from running invalid code." (Apollo GraphOS Docs, see reference 13.)
- Scale against operational overhead. The router and the composition
  pipeline are a fixed operational cost that pays off as the number of
  teams and subgraphs grows, and is a needless expense for a small,
  single-team system. Dimension 4 covers exactly where that line sits.

## 4. Applicability and non-applicability

Reach for schema federation when many teams each own a distinct part of the
domain, when consumers need one unified API rather than many separate ones,
and when the number of independently-owned services is large enough that a
hand-written, centrally-maintained gateway becomes the bottleneck. Netflix
is a documented example at this scale, running a federated graph large
enough that a single cross-subgraph search became its own dedicated
engineering problem, described directly in Netflix's own engineering
writing. (Netflix TechBlog, see reference 11.)

Do not reach for it in a small or medium organization with only a handful of
data providers. An independent engineering source frames the boundary in
terms of scale directly, describing federation's case as strengthening as
the provider count grows into the tens or hundreds, while a smaller number
of providers is served well by a simpler composition approach that "slots
more easily into an existing REST backend architecture." (Hao, see reference
9.) A second independent source makes an even more pointed version of the
same point, arguing that for a genuinely single-team system, the case for
GraphQL at all, federated or not, may not exist, since "federation is
solving an organizational problem, not a technical one," and a lighter
weight, type-safe alternative can capture the same benefit with none of the
machinery. (WunderGraph, see reference 10.) Do not reach for it either when
the team adopting it has not budgeted for the real operational cost of
running a router and a schema-composition pipeline, since that cost is paid
whether or not the organization is large enough to need the autonomy
federation buys.

## 5. Structure

The participants are the subgraph, an independently owned and deployed
GraphQL service that defines part of the overall schema and declares, via
directives, which types it can resolve and which fields of a type owned
elsewhere it depends on; the supergraph schema, the single composed schema
produced by combining every subgraph's schema, the one contract consumers
see; the router, the component that receives a client's query against the
supergraph, plans how to satisfy it across subgraphs, issues the resulting
subgraph queries, and merges their responses into one; and the schema
registry or composition pipeline, the process that validates a proposed
subgraph schema change composes cleanly with every other subgraph before it
is allowed to reach the router.

## 6. ASCII structure diagram

```
                       Client
                         |
                         v
                +------------------+
                |      Router       |   plans + executes the query,
                |  (supergraph)     |   merges subgraph responses
                +---+-----------+---+
                    |           |
        Fetch       |           |      Fetch
     +--------------+           +--------------+
     v                                          v
+-----------+                            +--------------+
| Subgraph A |  --- @key, @external ---> |  Subgraph B   |
| (owns User)|                           | (owns Orders) |
+-----------+                            +--------------+

Composition pipeline (before any request ever runs)

  Subgraph A schema  --+
  Subgraph B schema  --+--> compose --> Supergraph schema --> Router config
  Subgraph C schema  --+       |
                                v
                     fails loudly here if any
                     subgraph schema conflicts
```

## 7. Dynamics

Before any client query runs, every subgraph's schema is checked against
every other subgraph's schema and composed into one supergraph schema.
Apollo's own docs describe this precisely. "composition is the process of
combining a set of subgraph schemas into a supergraph schema," which
includes "all of the type and field definitions from your subgraph schemas"
plus "metadata that enables your router to intelligently route incoming
GraphQL operations." (Apollo GraphOS Docs, see reference 13.) If two
subgraphs conflict, "that conflict won't affect your router, because
composition fails to generate a new supergraph schema." (Same source.)

When a client sends a query against the running supergraph, the router
builds a query plan, a structured, ordered set of steps describing which
subgraphs to call and in what order. Apollo's own reference walks a concrete
example. a client asks for a list of hotels with their address and reviews.
The hotels subgraph owns `Hotel.address`, the reviews subgraph owns
`Hotel.reviews`, and `Hotel` is declared an entity via `@key(fields: "id")`
in both. The resulting plan runs as a `Sequence`, first a `Fetch` to the
hotels subgraph for `id`, `address`, and the entity's `__typename`, then a
`Flatten` step that takes each returned hotel's `id` and issues a second
`Fetch` to the reviews subgraph for that hotel's reviews, merging the result
back onto the same object. (Apollo GraphOS Docs, Query Plans, see reference
15.) The client receives one response, with no indication that two separate
services answered it.

## 8. Implementation variants

- Entity resolution via `@key`. A type that more than one subgraph
  contributes fields to is declared an entity in each subgraph that touches
  it, with `@key` naming the field or fields that identify a specific
  instance across subgraphs. Apollo's own reference defines it plainly.
  "Designates an object type as an entity and specifies its key fields."
  (Apollo GraphOS Docs, Directives, see reference 3.)
- Field ownership across subgraph boundaries, `@external` and `@requires`.
  A subgraph can reference a field it does not itself resolve using
  `@external`, defined as indicating "that this subgraph usually can't
  resolve a particular object field, but it still needs to define that
  field for other purposes," and can depend on another subgraph's field
  value with `@requires`, defined as indicating "that the resolver for a
  particular entity field depends on the values of other entity fields
  that are resolved by other subgraphs." (Same source.)
- Router-enforced authorization. `@authenticated`, `@requiresScopes`, and
  `@policy` mark fields and types as restricted, enforced at the router
  before any subgraph is called, so an unauthorized field never reaches a
  subgraph at all. "If no field of a subgraph query passes its
  authorization policies, the router stops further processing of the query
  and precludes unauthorized subgraph requests." (Apollo GraphOS Docs,
  Router Authorization, see reference 16.) Identity is then propagated
  down to subgraphs that need it, most often as claims extracted from a
  JWT and forwarded as headers, so "subgraphs can independently apply
  additional authorization using the identity context the router already
  resolved." (Apollo GraphOS Docs, Router Authentication, see reference
  17.)
- Older, superseded variant, schema stitching. The predecessor approach,
  where a gateway holds delegating resolver functions that call out to
  each underlying schema and stitch their results together in gateway
  code. Composition logic lives centrally rather than in each service,
  dimension 2's non-federated failure mode.
- The non-GraphQL analog, API Composition. Chris Richardson's microservices
  pattern language names the REST-world sibling of this idea. an API
  Composer invokes several owning services and performs an in-memory join
  of their results at request time. The distinction from federation is
  real and worth stating precisely. an API Composer, and a plain API
  Gateway that does the same job, run this join as hand-written
  orchestration code with no shared schema contract, while federation
  validates a statically composed schema before any request runs at all.
  (microservices.io, API Composition, see reference 18; API Gateway, see
  reference 19.)

## 9. Known production uses

- Netflix operates a federated GraphQL graph in production, described
  directly in Netflix's own engineering writing. Netflix's account is
  candid that federation did not solve every problem for free, describing
  a new cross-subgraph search problem it created, since "the Movie service
  would need to provide an endpoint that accepts a query and filters that
  may apply to data the service does not own," which they solved with a
  separate, purpose-built search platform rather than a single subgraph
  trying to reach across ownership boundaries. (Netflix TechBlog, see
  reference 11.)
- Apollo's own GraphOS Router and its predecessor, Apollo Gateway, are the
  reference implementation of the pattern, running the composition and
  query-planning process described in dimensions 6 and 7 in production for
  a wide range of companies beyond Netflix. (Apollo GraphOS Docs, About the
  Router, see reference 14.)

## 10. Consequences

Positive. Each team owns and deploys its own subgraph without waiting on a
central team to merge its changes into one shared schema file. Consumers
still get one unified API, and never need to know how many services answer
a given query. A subgraph schema change that would break composition, or
that would break a real client's existing query, is caught before it ships,
not discovered by a person after the fact.

Negative. The router and the composition pipeline are real, standing
infrastructure that must be run, versioned, and understood by every team
that owns a subgraph, a cost paid even on a quiet day. Decentralizing
ownership removes the one team that used to hold cross-cutting concerns in
its head, and a person now has to work across data models owned by several
different teams to understand one query's full path, a real rise in
cognitive load compared to a single owned codebase. A federated query that
fans out across many subgraphs pays the latency of the slowest subgraph on
that query's critical path, and a query plan that must run steps in
sequence because one subgraph depends on another's result cannot be sped up
by adding more subgraphs.

## 11. Failure modes and misuse

Treating the router as a plain reverse proxy. A reverse proxy forwards a
request unchanged to one backend. The router instead composes a schema,
plans a query across possibly many subgraphs, and merges their responses,
and teams that build for it as if it only forwards requests miss the real
cost of that planning and the real value it buys them. Apollo names this
distinction in its own description of the component. "The router
intelligently calls all the APIs it needs to complete requests rather than
simply forwarding them." (Apollo Federation Docs, see reference 20.)

Skipping composition checks before merging a subgraph change. Apollo's own
schema-checks tooling exists specifically because "certain changes to your
graph's schema, such as removing a field or type, might break one of your
application's clients." (Apollo GraphOS Docs, Schema Checks, see reference
12.) A team that merges a subgraph change without running this check learns
about a breaking change from a production incident instead of from a
pre-merge failure.

Over-relying on field-level authorization directives without also
propagating identity to subgraphs that need finer-grained checks. The
router's own authorization directives prune unauthorized fields before any
subgraph is called, which is real protection, but a subgraph that also
needs to make its own authorization decision, for example a row-level
check a router directive cannot express, needs the identity context
forwarded down to it, and a team that assumes the router's own checks are
the only authorization layer needed will build a subgraph that trusts an
unverified caller.

Adopting federation before the organization is large enough to need it.
Dimension 4 names this directly. the router and composition pipeline are a
fixed cost, and a small team pays that cost with no autonomy benefit to
offset it, since there is no second team's subgraph to decouple from in the
first place.

## 12. Trade-off matrix

| Approach | Ownership | Schema contract | Composition-time validation | Operational cost |
|---|---|---|---|---|
| Monolithic single schema | One team, or one shared file | One schema, centrally maintained | Not applicable, one schema | Low |
| Plain API Gateway or API Composition | Distributed across owning services | None, joined at request time in code | None, a bad join is a runtime failure | Low to moderate |
| Schema stitching | Distributed services, centralized linking logic | One schema, composed at the gateway | Partial, the gateway's own delegating resolvers | Moderate |
| Schema federation | Fully distributed, linking logic in each subgraph | One supergraph schema, composed before requests run | Full, a conflicting change fails to compose | Higher, a router plus a composition pipeline |

## 13. Related and incompatible patterns

API Gateway (see `api-gateway.md` in family 10) is the simpler,
request-time-only ancestor this pattern is often compared against. a plain
gateway is "the single entry point for all clients," handling requests
"simply proxied or routed to the appropriate service," or by "fanning out
to multiple services," with no composed schema and no composition-time
validation. (microservices.io, see reference 19.) Federation adds exactly
what a plain gateway lacks, a single statically composed schema and a
query planner that reasons over it, rather than hand-written fan-out code.

API Composition (see `api-composition.md` in family 10) is the REST-world,
request-time analog, an API Composer joining several owning services'
results in memory at query time. It is a genuinely related idea, both
compose data from several independently owned services into one response,
but it carries none of federation's composition-time schema validation.

Backend for Frontend answers a different question than federation does.
where federation keeps one shared schema for every consumer, a
Backend-for-Frontend deploys "a separate API gateway for each kind of
client," (microservices.io, see reference 19) "one backend per user
experience," (Newman, see reference 22) owned by the same team as that
specific client. The two ideas compose rather than conflict. a
Backend-for-Frontend can itself be one more consumer of a federated
supergraph.

GraphQL Resolver Pattern and GraphQL DataLoader (see
`graphql-resolver-pattern.md` and `graphql-dataloader.md` in this family)
are the object-level mechanics a federated subgraph still needs. federation
governs how many independently owned schemas compose into one, resolvers
and data loaders govern how any single one of those schemas, federated or
not, actually resolves a field efficiently.

## 14. Refactoring path in and out

In, from a monolithic schema or a hand-stitched gateway. Identify the
boundaries where ownership already splits across teams, and extract each
team's portion of the schema into its own subgraph, declaring shared types
as entities with `@key`. Stand up a router, register every subgraph's
schema with a composition pipeline, and confirm the supergraph composes
cleanly and every existing client query still resolves before cutting
traffic over. Apollo's own migration guidance for teams coming specifically
from schema stitching frames this as moving the linking logic that used to
live in the gateway's delegating resolvers into each subgraph's own `@key`
and `@external` declarations instead.

Out. When an organization consolidates around one team owning the whole
domain, or when the number of subgraphs shrinks to a point where the
router and composition pipeline cost more to run than the autonomy is
worth, the subgraphs can be merged back into one schema, the router
retired, and the composition pipeline removed. This is rare in practice,
because the organizational split that motivated federation in the first
place, many teams, many domains, rarely reverses.

## 15. Testing and verification

The mechanism that proves a proposed subgraph change is safe is composition
checking, run in CI before merge. Apollo's own guidance is direct.
"Add the `rover subgraph check` command in your CI pipeline to run on every
commit," and "add the `rover subgraph publish` command in your CD pipeline
to push changes after they are deployed." (Apollo GraphOS Docs, CI/CD, see
reference 21.) This check does two things at once, it confirms the proposed
schema still composes with every other subgraph's current schema, and,
using "your graph's historical client operation data," it confirms no real
client's existing query would break. (Apollo GraphOS Docs, Schema Checks, see
reference 12.) This is the pattern's own version of contract testing
between independently owned services, run automatically against the actual
composed contract rather than hand-written per-pair contracts.

The router's own query-planning behavior can be tested in isolation too,
independent of Apollo's own tooling, using a community command-line tool
built specifically because, as its authors put it, generating and
inspecting a real query plan outside of a live router is otherwise the only
way to catch a query-plan regression before it reaches production.
(apollosolutions, generate-query-plan, see reference 7.)

## 16. Observability signals

The healthy signal is a single trace per client query that shows a clean
fan-out across every subgraph that query touched, with each subgraph call
represented as its own span. Apollo's own router telemetry names this span
directly, a span "that wraps a request to a subgraph," propagated using
"the W3C Trace Context specification" so one trace ID follows the request
across every hop. (Apollo GraphOS Docs, Router Telemetry, see reference 23.)
At the aggregate level, the healthy signal is stable per-subgraph request
volume, latency, and error rate, tracked so a team can "compare subgraphs
by request volume, latency, and error rates" and watch p95 service time
directly. (Apollo GraphOS Docs, Insights, see reference 24.)

The failing signal is a trace that shows one subgraph taking most of the
total response time on a query that should be fast, a rising error rate
isolated to one subgraph while the rest of the supergraph stays healthy, or
a composition check failing repeatedly in CI, which signals a team is
proposing changes that conflict with the rest of the supergraph faster than
the schema is being cleaned up.

## 17. Security and privacy implications

Authorization in a federated system is a two-layer concern, not a single
gate. The router's own directives, `@authenticated`, `@requiresScopes`, and
`@policy`, prune unauthorized fields out of the query plan before any
subgraph request is sent, which is real protection at the boundary. But a
subgraph that needs a finer-grained check the router's directives cannot
express, a row-level rule, an ownership check, needs the caller's identity
forwarded down to it, most often as claims extracted from a JWT and passed
as headers, so it can apply that check itself rather than trusting the
router's coarser gate as the only line of defense.

Where it is silent. federation itself adds no new data-handling behavior
beyond what each subgraph already does with the data it owns. it changes
how requests are composed and routed, not what a subgraph does once it
receives a request. The genuine new surface is the router and the
composition pipeline themselves, which now see, and must be trusted with,
every field of every subgraph's schema in order to compose and route
correctly.

## 18. References

1. Apollo GraphQL Blog, "Apollo Federation."
   https://www.apollographql.com/blog/apollo-federation-f260cf525d21,
   verified 2026-08-22.
2. Apollo Federation v1 Docs, "Migrating from schema stitching."
   https://www.apollographql.com/docs/federation/v1/migrating-from-stitching,
   verified 2026-08-22.
3. Apollo GraphOS Docs, "Apollo Federation Directives."
   https://www.apollographql.com/docs/graphos/schema-design/federated-schemas/reference/directives,
   verified 2026-08-22.
4. Hao, "GraphQL at scale, schema stitching versus schema federation."
   https://blog.hao.dev/graphql-at-scale-schema-stitching-v-s-schema-federation/,
   verified 2026-08-22.
5. GraphQL Foundation, composite-schemas-wg repository README.
   https://github.com/graphql/composite-schemas-wg, verified 2026-08-22.
6. GraphQL Working Group, RFC "CompositeSchemas.md."
   https://raw.githubusercontent.com/graphql/graphql-wg/main/rfcs/CompositeSchemas.md,
   verified 2026-08-22.
7. apollosolutions, generate-query-plan.
   https://github.com/apollosolutions/generate-query-plan, verified
   2026-08-22.
8. Apollo GraphOS Docs, "Federated Schemas."
   https://www.apollographql.com/docs/graphos/schema-design/federated-schemas/federation,
   verified 2026-08-22.
9. Hao, same source as reference 4, applicability section, verified
   2026-08-22.
10. WunderGraph, "I was wrong about GraphQL."
    https://medium.com/@wundergraph/i-was-wrong-about-graphql-84fd293bb204,
    verified 2026-08-22.
11. Netflix TechBlog, "How Netflix Content Engineering makes a federated
    graph searchable."
    https://netflixtechblog.com/how-netflix-content-engineering-makes-a-federated-graph-searchable-5c0c1c7d7eaf,
    verified 2026-08-22.
12. Apollo GraphOS Docs, "Schema Checks."
    https://www.apollographql.com/docs/graphos/platform/schema-management/checks,
    verified 2026-08-22.
13. Apollo GraphOS Docs, "Schema Composition."
    https://www.apollographql.com/docs/graphos/schema-design/federated-schemas/composition,
    verified 2026-08-22.
14. Apollo GraphOS Docs, "Supergraph Routing with GraphOS Router."
    https://www.apollographql.com/docs/graphos/routing/v1/about-router,
    verified 2026-08-22.
15. Apollo GraphOS Docs, "Query Plans."
    https://www.apollographql.com/docs/graphos/reference/federation/query-plans,
    verified 2026-08-22.
16. Apollo GraphOS Docs, "Authorization in the GraphOS Router."
    https://www.apollographql.com/docs/graphos/routing/security/authorization,
    verified 2026-08-22.
17. Apollo GraphOS Docs, "Authenticating Requests with the GraphOS
    Router."
    https://www.apollographql.com/docs/graphos/routing/security/router-authentication,
    verified 2026-08-22.
18. microservices.io, "Pattern, API Composition."
    https://microservices.io/patterns/data/api-composition.html, verified
    2026-08-22.
19. microservices.io, "Pattern, API Gateway."
    https://microservices.io/patterns/apigateway.html, verified
    2026-08-22.
20. Apollo Federation Docs, introduction page.
    https://www.apollographql.com/docs/federation, verified 2026-08-22.
21. Apollo GraphOS Docs, "Set Up CI/CD."
    https://www.apollographql.com/docs/graphos/resources/guides/onboarding/set-up-pipelines,
    verified 2026-08-22.
22. Sam Newman, "Backends For Frontends."
    https://samnewman.io/patterns/architectural/bff/, verified
    2026-08-22.
23. Apollo GraphOS Docs, "Router Telemetry."
    https://www.apollographql.com/docs/graphos/routing/observability/telemetry,
    verified 2026-08-22.
24. Apollo GraphOS Docs, "GraphOS Insights."
    https://www.apollographql.com/docs/graphos/platform/insights,
    verified 2026-08-22.

**Evidence grade.** high

**Most solid findings.** The query-planning mechanics in dimensions 7 and 8
are sourced directly from Apollo's own reference documentation, including a
full concrete worked example (schemas, client query, and the resulting
query plan) reproduced exactly as published, not paraphrased. The claim
that Composite Schemas is becoming a genuinely vendor-neutral specification,
not an Apollo-only relabeling, is confirmed by the founding RFC's own
contributor list, which spans Apollo's direct competitors in the
composition space.

**Unverified or unclear.** The trade-off between team autonomy and
operational cost is stated more explicitly, in Apollo's own words, on the
benefit side than on the cost side, since Apollo's own documentation pages
did not, in what could be fetched, state the complexity cost as bluntly as
they state the autonomy benefit. An independent essay on the cognitive-load
cost of decentralized governance was found during research but its title
and URL could not be safely reproduced in this file, so dimension 3's
autonomy-versus-governance force is stated here as this catalogue's own
reasoning rather than as a direct outside quote.

## Code examples

### TypeScript, a minimal router-style query planner across two in-memory subgraphs

```typescript
interface Hotel {
  id: string;
  address: string;
}

interface Review {
  hotelId: string;
  rating: number;
}

const hotelSubgraph = {
  hotels: (): Hotel[] => [
    { id: "h1", address: "1 Main St" },
    { id: "h2", address: "2 Oak Ave" },
  ],
};

const reviewSubgraph = {
  reviewsFor: (hotelId: string): Review[] =>
    [
      { hotelId: "h1", rating: 5 },
      { hotelId: "h1", rating: 4 },
      { hotelId: "h2", rating: 3 },
    ].filter((r) => r.hotelId === hotelId),
};

function planAndExecute(): Array<Hotel & { reviews: Review[] }> {
  const hotels = hotelSubgraph.hotels();
  return hotels.map((hotel) => ({
    ...hotel,
    reviews: reviewSubgraph.reviewsFor(hotel.id),
  }));
}

const merged = planAndExecute();
console.log(merged[0].reviews.length === 2);
console.log(merged[1].reviews.length === 1);
```

### Python, entity resolution keyed across two subgraphs

```python
from dataclasses import dataclass, field


@dataclass
class UserSubgraph:
    users: dict = field(default_factory=lambda: {
        "u1": {"id": "u1", "name": "Ada"},
        "u2": {"id": "u2", "name": "Grace"},
    })

    def resolve(self, user_id: str) -> dict:
        return self.users[user_id]


@dataclass
class OrderSubgraph:
    orders: list = field(default_factory=lambda: [
        {"id": "o1", "user_id": "u1", "total": 42},
        {"id": "o2", "user_id": "u1", "total": 17},
        {"id": "o3", "user_id": "u2", "total": 99},
    ])

    def orders_for(self, user_id: str) -> list:
        return [o for o in self.orders if o["user_id"] == user_id]


def compose_query(user_id: str, users: UserSubgraph, orders: OrderSubgraph) -> dict:
    user = users.resolve(user_id)
    return {**user, "orders": orders.orders_for(user_id)}


users = UserSubgraph()
orders = OrderSubgraph()
result = compose_query("u1", users, orders)
assert result["name"] == "Ada"
assert len(result["orders"]) == 2
```

### Go, a composition check that rejects a conflicting subgraph field

```go
package main

import "fmt"

type FieldOwner struct {
	Type      string
	Field     string
	Subgraph  string
}

func compose(owners []FieldOwner) (map[string]string, error) {
	seen := make(map[string]string)
	for _, o := range owners {
		key := o.Type + "." + o.Field
		if existing, ok := seen[key]; ok && existing != o.Subgraph {
			return nil, fmt.Errorf(
				"composition conflict on %s, owned by both %s and %s",
				key, existing, o.Subgraph,
			)
		}
		seen[key] = o.Subgraph
	}
	return seen, nil
}

func main() {
	clean := []FieldOwner{
		{Type: "Hotel", Field: "address", Subgraph: "hotels"},
		{Type: "Hotel", Field: "reviews", Subgraph: "reviews"},
	}
	if _, err := compose(clean); err != nil {
		panic("expected clean composition")
	}

	conflicting := []FieldOwner{
		{Type: "Hotel", Field: "address", Subgraph: "hotels"},
		{Type: "Hotel", Field: "address", Subgraph: "legacy-hotels"},
	}
	if _, err := compose(conflicting); err == nil {
		panic("expected a composition conflict")
	} else {
		fmt.Println("composition correctly rejected:", err)
	}
}
```
