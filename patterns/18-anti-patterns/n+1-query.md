---
name: N+1 Query
slug: n+1-query
family: 18-anti-patterns
category: Anti-Pattern
aliases: [N+1 Selects Problem, N+1 Query Problem, Select N+1]
first_described: "Community-documented ORM anti-pattern, term in widespread use in Hibernate and Ruby on Rails documentation and tooling by the mid-2000s; no single originating paper is attributable, see dimension 1"
maturity: canonical
related: [lazy-load, eager-loading, identity-map, unit-of-work, repository, data-mapper, batch-method, facade]
incompatible_with: []
verified: 2026-08-02
---

# N+1 Query

## 1. Name, aliases, and lineage

The canonical name in almost every object-relational mapping and API
community is N+1 Query, with N+1 Selects Problem and Select N+1 in
near-universal use as synonyms. All three names describe the identical
shape, one query to fetch a collection of N parent records followed by one
further query per parent to fetch each parent's related data, for a total
of N+1 round trips where a single query, or a small fixed number of
queries, would suffice.

Unlike a Gang of Four pattern or a catalogued anti-pattern such as The Blob,
this name has no single originating publication that a reader can point to
as the first use. It is honest to say so plainly rather than inventing an
attribution. The term is documented as being in active, assumed-familiar
use inside Ruby on Rails' own official guide, in a section titled "N + 1
Queries Problem" that treats the phrase as already established vocabulary
rather than one it is introducing (Ruby on Rails Guides, "Active Record
Query Interface", section 13.1, verified 2026-08-02). The Hibernate
project's user guide documents the equivalent shape under the heading
"Fetching", covering the same failure through its discussion of fetch
strategies, batch fetching, and entity graphs (Hibernate ORM 6.4 User
Guide, Chapter 12, Fetching, sections 12.5 through 12.12, verified
2026-08-02). Both communities independently converged on identical
tooling built specifically to detect this one shape, which is itself
evidence that the vocabulary and the underlying pattern predate any single
paper. The Bullet gem for Ruby on Rails states its purpose as watching an
application's queries during development and notifying the developer
"when you should add eager loading (N+1 queries)" (flyerhzm/bullet, GitHub
README, verified 2026-08-02).

The pattern this anti-pattern misuses is Lazy Load, catalogued by Martin
Fowler in *Patterns of Enterprise Application Architecture*,
Addison-Wesley, 2002, as "an object that doesn't contain all of the data
you need but knows how to get it" (Fowler, martinfowler.com, "Lazy Load",
verified 2026-08-02). Fowler's own catalog page notes that lazy loading a
single object is unremarkable but that loading one object can trigger the
loading of "a huge number of related objects", which is the general
warning that N+1 Query names precisely, in the specific case where the
huge number arrives one query at a time inside a loop rather than in a
single request. N+1 Query is therefore best understood as the failure mode
of Lazy Load under iteration, given a name of its own because the failure
recurs constantly and independently across every language and every ORM
that offers lazy association loading, from Hibernate in Java, to Active
Record in Ruby, to Entity Framework Core in .NET, to Django's ORM in
Python.

A closely related but distinct name, cartesian explosion, appears in more
recent ORM documentation and names a different failure that shares a root
cause. Microsoft's Entity Framework Core documentation discusses both
under one heading, "Avoid cartesian explosion when loading related
entities", and explains that a single eager join across a one-to-many
relationship can return a duplicated, multiplied row set rather than the N
separate small queries that define N+1 itself (Microsoft Learn, "Efficient
Querying, EF Core", verified 2026-08-02). The two names are frequently
confused because both arise from loading related data across a
one-to-many relationship poorly, and dimension 11 draws the line between
them precisely, because the fix for one can reintroduce the other.

## 2. Problem and context

The shape appears the moment code needs to display, process, or serialize
a list of parent records together with one piece of data that lives on a
related table or a related service. The list itself is retrieved
correctly, in one query or one call. The related data for each item in the
list is then retrieved by iterating over the list and issuing a separate
fetch per item, because that fetch reads naturally as ordinary,
sequential, object-oriented code.

A reader who has never heard the pattern's name recognizes it immediately
in a codebase that looks like this, independent of language or framework.

```
posts = Post.all
posts.each do |post|
  puts post.author.name   # one query per post, here
end
```

The first line issues one query. The loop body's `post.author` access,
because the association is lazily loaded, issues one additional query
every single time it runs, once per post. For ten posts that is eleven
total queries. For ten thousand posts, in a report generation job or a
data export, it is ten thousand and one. Nothing in this code is wrong at
the level of a single line, which is exactly what makes the pattern so
persistent, every individual statement is correct, and the defect exists
only in the aggregate behaviour of the loop.

The context in which this becomes a real production problem, rather than a
theoretical one, has three parts.

- **A collection is fetched first**, and the code that follows needs a
  piece of related data for every member of that collection, not for one
  member selected in isolation.
- **The related data is fetched through an abstraction that hides the
  cost of the fetch**, most often an ORM's lazy-loaded association
  property, a GraphQL resolver field, or a helper method that internally
  performs a network call, so the code at the call site looks identical
  whether the value is already in memory or requires a full round trip.
- **The collection size is not fixed at development time.** The bug is
  invisible against a development database seeded with three rows and
  becomes visible, sometimes catastrophically, only once production data
  grows the collection into the hundreds or thousands. This delayed onset
  is why the pattern survives code review so often, the reviewer sees ten
  test rows behave fine.

This exact three-part context recurs outside relational databases too. A
GraphQL resolver for a list field that calls a separate downstream
microservice, once per item, to resolve a nested field exhibits the
identical shape and the identical fix, which is why GraphQL server
tooling, most visibly the DataLoader library, exists specifically to solve
it (graphql/dataloader, GitHub README, verified 2026-08-02). A REST API
client that lists resources and then calls a details endpoint once per
resource in a loop is the network-call variant of the same problem. The
underlying context, one round trip that returns N identifiers followed by
N further round trips, is identical whether the round trip talks to
Postgres, to a GraphQL field resolver, or to another team's HTTP service.

## 3. Forces

The forces below explain why the naive shape gets written in the first
place, and why it is genuinely costly once written.

- **Code readability at the call site, favoured by the naive shape.** A
  loop that writes `post.author.name` reads as ordinary object
  navigation. The alternative, an explicit join or a batch call, requires
  the author to think about data access strategy before writing the loop,
  which the naive shape lets them defer.
- **Round trip cost, sacrificed by the naive shape.** Each additional
  query pays the full cost of a network round trip to the database or
  service, independent of how small the actual row it returns is. On a
  local development database with sub-millisecond latency this cost is
  nearly free. On a production database reached over a network, or a
  managed database service with connection pooling overhead, each round
  trip commonly costs one to several milliseconds even for a trivial
  query, and the cost compounds linearly with N.
- **Connection and thread pool pressure, sacrificed by the naive shape.**
  A request that opens and closes N+1 short-lived queries holds a
  database connection, or a connection-pool slot, for the full duration of
  the loop rather than for one query's duration, which reduces the
  effective concurrency the connection pool can serve under load.
- **Coupling to the exact data actually needed, favoured by the naive
  shape in the small.** Lazy loading, the mechanism the naive shape
  depends on, only fetches an association when the code actually touches
  it, so a code path that conditionally skips the loop body never pays
  the N extra queries at all. An eager join fetches the related data
  unconditionally, which can waste work when the association turns out to
  be unused on some code paths.
- **Predictability of query count, sacrificed by the naive shape.** The
  number of queries a request issues under the naive shape is a function
  of the data, not of the code, so the same endpoint issues a different,
  growing number of queries as the underlying table grows, which is the
  opposite of the fixed, small, reviewable query count that a join or
  batch fetch guarantees regardless of row count.
- **Developer velocity in the first pass, favoured by the naive shape.**
  Writing the loop with a lazy association is faster to type and requires
  no upfront schema or query-shape decision, which is why the pattern is
  so often the first thing written and only later identified as a defect
  once it is measured.

The trade this anti-pattern makes, in one sentence, is that it buys
short-term code simplicity and defers a data-access-strategy decision, at
the cost of a query count that grows linearly with the size of the data
the code will eventually be asked to handle, which is precisely the axis
software is expected to scale along.

## 4. Applicability and non-applicability

This entry is an anti-pattern, so there is no case in which deliberately
writing the N+1 shape into a system meant to grow is the correct
engineering choice. What follows describes when the shape is tolerable in
practice, and the non-applicability list, describing when it must never be
left in place, is the more important half.

When the N+1 shape is tolerable, provisionally.

- In a one-off script or a bounded administrative task where the
  collection size is known in advance to be small, in the tens of rows at
  most, and the script is run rarely by a person rather than triggered
  repeatedly by user traffic, so the fixed per-query round-trip cost never
  compounds against real load.
- During the earliest exploratory pass over a new feature, before the
  correct eager-loading shape is even known, where writing the lazy,
  naive version first and then profiling it before shipping is a
  legitimate way to discover which associations actually need to be
  batched, provided the profiling step genuinely happens before the code
  reaches production traffic.
- Inside test fixtures and seed scripts that run once against a small,
  fixed dataset, where the clarity of the naive loop for a human reading
  the fixture outweighs a query-count concern that will never be
  measured under load.

When the N+1 shape should never be reached for, or left in place once
found.

- On any code path that serves a paginated list to a user or to another
  service, because the whole purpose of pagination is to bound the visible
  page size, and the N+1 shape defeats that bound by growing the query
  count with the page size on every single page load, forever, as traffic
  and data both grow.
- Inside any loop whose iteration count is derived from live production
  data rather than from a constant, because the query count is then
  unbounded by construction, and the shape that was fine in development
  against ten seeded rows is a production incident waiting for the day the
  underlying table crosses a threshold nobody chose.
- In any report, export, or batch job that processes an entire table or a
  large filtered subset of one, because these are exactly the jobs where N
  is largest and where a job that used to finish in seconds silently
  degrades to minutes or hours as the table grows, often without anyone
  noticing until a downstream deadline is missed.
- Inside a GraphQL resolver for a field on a list type, because GraphQL's
  own execution model calls that resolver once per item in the parent
  list by design, which makes the N+1 shape the default behaviour of a
  naive resolver rather than a mistake a developer has to actively write,
  and the fix, a request-scoped batching loader, is close to mandatory for
  any list field that touches a database or a downstream service.
- Anywhere the fix is already a single line away, because most ORMs
  expose eager loading through one additional method call on the exact
  same query, which means the excuse that fixing it is expensive rarely
  holds once the pattern has been correctly identified.

## 5. Structure

The N+1 shape has a small, fixed structure independent of language or
framework, built from three roles.

- **The driving query.** A single query, or a single request, that
  returns a collection of N parent records. This part of the shape is
  correct in isolation, it costs exactly one round trip regardless of N.
- **The per-item fetch.** A second query, request, or resolver
  invocation that is triggered once for every member of the collection
  returned by the driving query, to obtain a piece of data related to
  that specific member. This is the part of the shape that is defective,
  because its cost scales with N rather than staying constant.
- **The hiding abstraction.** The mechanism that makes the per-item fetch
  invisible at the call site, most commonly a lazily loaded ORM
  association property, a GraphQL field resolver, or a wrapper method
  around an HTTP client call. This role is what separates N+1 Query from
  an obviously bad, hand-written double loop over two explicit query
  calls, the defect is disguised as ordinary property access or method
  invocation, and that disguise is exactly why the pattern survives code
  review as often as it does.

What should exist instead, and does not, is a fourth role, **the batching
layer**, a single point through which every per-item request for the same
kind of related data passes before it reaches the database or the
downstream service, so that N individual requests collapse into one join,
one `IN` clause, or one batched call. Naming this missing role is what
makes the refactoring path in dimension 14 concrete, the fix is always
some form of introducing this fourth role between the driving query and
the per-item fetches, whether that role is an ORM's eager-loading
directive, a hand-written batch query, or a request-scoped DataLoader.

## 6. ASCII structure diagram

```
   Driving query (1 round trip)
   +------------------------------------------+
   |  SELECT * FROM posts                      |
   +------------------------------------------+
                       |
                       v  returns N parent rows
   +------------------------------------------+
   |  posts = [post_1, post_2, ..., post_N]    |
   +------------------------------------------+
                       |
        for each post in posts (the hiding abstraction)
                       |
        +--------------+--------------+--- ... ---+
        v              v              v            v
   +---------+   +---------+    +---------+   +---------+
   | SELECT  |   | SELECT  |    | SELECT  |   | SELECT  |
   | author  |   | author  |    | author  |   | author  |
   | WHERE   |   | WHERE   |    | WHERE   |   | WHERE   |
   | id = 1  |   | id = 2  |    | id = 3  |   | id = N  |
   +---------+   +---------+    +---------+   +---------+
     round        round          round          round
     trip 2        trip 3        trip 4          trip N+1

   Total cost. 1 + N round trips, growing linearly with the row count.

   What should exist instead, the missing batching layer.

   +------------------------------------------+
   |  SELECT * FROM authors WHERE id IN (1..N) |     one round trip,
   +------------------------------------------+     any N
```

## 7. Dynamics

The dynamics below trace the same request through the naive shape and
through the batched fix, so the difference in round trips is visible step
by step rather than asserted.

```
Naive N+1 shape, N = 3

Client        App code                   Database
  |               |                           |
  |-- GET /posts->|                           |
  |               |-- SELECT * FROM posts --->|
  |               |<-- 3 rows -----------------|
  |               |                           |
  |               | for post in [p1, p2, p3]:  |
  |               |-- SELECT author WHERE 1 -->|
  |               |<-- row --------------------|
  |               |-- SELECT author WHERE 2 -->|
  |               |<-- row --------------------|
  |               |-- SELECT author WHERE 3 -->|
  |               |<-- row --------------------|
  |               |                           |
  |<-- response --|                           |

  Round trips issued. 4 (1 + N). Grows to 1 + N for any N.


Batched fix, N = 3

Client        App code                   Database
  |               |                           |
  |-- GET /posts->|                           |
  |               |-- SELECT * FROM posts --->|
  |               |<-- 3 rows -----------------|
  |               |                           |
  |               | collect author_ids = {1,2,3}
  |               |-- SELECT authors           |
  |               |   WHERE id IN (1,2,3) ---->|
  |               |<-- 3 rows -----------------|
  |               |                           |
  |               | join in memory by id       |
  |               |                           |
  |<-- response --|                           |

  Round trips issued. 2, fixed regardless of N.
```

Two timing details matter beyond the raw count. First, in the naive
shape, the N per-item queries in most single-threaded ORM clients run
strictly sequentially, each waiting on the previous round trip to
complete, so the wall-clock cost is close to N times the average
round-trip latency, not amortized by any concurrency the application
server might otherwise offer. Second, in the batched fix, the join step
that matches authors back onto posts by identifier happens entirely in
application memory after the second query returns, which is why the
batching layer in dimension 5 is described as introducing exactly one new
step, a lookup by identifier, rather than any new network activity.

## 8. Implementation variants

The N+1 shape recurs in several distinct technical settings, each with its
own idiomatic fix, and conflating them is a common source of applying the
wrong fix to the wrong variant.

**ORM lazy-association traversal.** The variant described throughout this
entry so far. A collection query followed by a loop that touches a lazily
loaded association. The idiomatic fix is the ORM's own eager-loading
directive, called `includes` in Ruby on Rails' Active Record, `Include` in
Entity Framework Core, `select_related` or `prefetch_related` in Django,
and expressed through `JOIN FETCH`, a named entity graph, or `@BatchSize`
in Hibernate.

**GraphQL nested resolver fan-out.** A query for a list field followed by
a per-item resolver call for a nested field on every element of that
list, driven by GraphQL's own field-at-a-time execution model rather than
by a hand-written loop in application code. The idiomatic fix is a
request-scoped batching and caching loader, most commonly the DataLoader
library or a language-specific equivalent such as Shopify's `graphql-batch`
gem for Ruby, which coalesces every individual load call issued within one
tick of the event loop, or one execution phase, into a single batch
function invocation (graphql/dataloader README; Shopify/graphql-batch
README, both verified 2026-08-02).

**REST client fan-out.** A call to a list endpoint followed by a loop
that calls a details endpoint once per item returned by the list call.
Because this variant crosses process and often organizational
boundaries, it cannot be fixed by a database join, the idiomatic fix is
either a batch or bulk endpoint accepting a list of identifiers on the
downstream service, or an embed or expand query parameter that lets the
list endpoint itself return the nested data in one response.

**Microservice-to-microservice fan-out.** The distributed-systems
generalization of the REST client variant, where the per-item fetch
crosses a service boundary and pays network latency, serialization cost,
and often authentication overhead on every one of the N calls. This
variant is the most expensive per unit, because each of the N calls can
individually cost tens of milliseconds, and it is also the variant most
likely to trigger cascading timeouts and circuit breaker trips under load,
since N slow calls compound into one very slow aggregate request.

**Template or serializer traversal.** A view template or an API
serializer that iterates a collection and, for each item, calls a helper
method or accesses a computed property that itself performs a query.
This variant is the hardest to spot in code review because the query
sits several call frames away from the loop that drives it, hidden inside
a helper that looks pure. The idiomatic fix is to pre-fetch the same data
the helper would have queried, in bulk, before the template ever runs, and
pass it in as an already-populated lookup structure.

**Batch job or report generation traversal.** The same shape as ORM
lazy-association traversal, but run against the largest N a system has,
an entire table or a full day's transaction log, inside an offline job
rather than a user-facing request. The cost here is measured in job
duration and, cumulatively, in database load sustained for the job's
entire run, rather than in single-request latency, which is why this
variant is the one most likely to eventually saturate a shared production
database and degrade unrelated, concurrent user-facing traffic.

## 9. Known production uses

Naming a production use of an anti-pattern means naming a real, checkable
instance where the tooling, documentation, or measured research confirms
the shape is common enough in real systems to justify building dedicated
detection or prevention machinery for it, a different and stronger bar
than naming a use of a design pattern.

**The Bullet gem in Ruby on Rails applications.** Bullet is a
purpose-built development-time monitor whose entire stated function is
watching an application's real query traffic and notifying the developer
"when you should add eager loading (N+1 queries)" (flyerhzm/bullet,
GitHub README, verified 2026-08-02). A tool built and maintained
specifically to detect one anti-pattern, adopted widely enough across
Rails applications to remain a standard part of many teams' development
environment, is itself strong evidence of the shape's prevalence in real
Rails codebases, because the tool would not exist, and would not have the
adoption it has, against a problem that was rare.

**The `graphql-batch` gem at Shopify.** Shopify maintains and ships
`graphql-batch`, a library providing "an executor for the graphql gem
which allows queries to be batched" for the Ruby GraphQL server library,
explicitly to let resolver authors write batching loaders that coalesce
per-item field resolution into single batched fetches (Shopify/graphql-batch,
GitHub README, verified 2026-08-02). Shopify's GraphQL API serves storefront
and admin traffic at very high volume, and the existence of a
company-maintained, general-purpose batching library in that stack is a
direct, sourced confirmation that the GraphQL nested-resolver variant of
N+1 Query is a real, ongoing concern in a large-scale production GraphQL
deployment.

**Hibernate's fetch-strategy machinery in Java applications.** The
Hibernate ORM User Guide devotes an entire chapter to fetching, with
dedicated sections on dynamic fetching via entity graphs, batch fetching,
and the `@Fetch` annotation mapping across `SELECT`, `SUBSELECT`, and
`JOIN` fetch modes (Hibernate ORM 6.4 User Guide, Chapter 12, sections
12.5 through 12.12, verified 2026-08-02). The breadth of this
machinery, several distinct, independently documented mechanisms for
controlling exactly when and how related data is fetched, exists because
Hibernate's default lazy-loading behaviour is precisely the mechanism
that produces N+1 Query when traversed inside a loop, and the framework's
own maintainers judged the problem important enough to build multiple
alternative fetch strategies around it rather than one.

**Entity Framework Core's own documentation naming the problem
explicitly.** Microsoft's official EF Core performance guide contains a
worked example, with real generated SQL and real statement-logging
output, under the heading "Beware of lazy loading", that names the
resulting failure by name, stating plainly that the pattern "is sometimes
called the N+1 problem, and it can cause very significant performance
issues" (Microsoft Learn, "Efficient Querying, EF Core", verified
2026-08-02). The same page carries an explicit warning that lazy loading
is recommended against specifically because it makes this problem easy to
trigger by accident, which is a framework vendor's own documentation
independently confirming both the name and the severity assessment given
throughout this entry.

## 10. Consequences

Positive, in the narrow sense of what the naive shape appears to buy
before its cost is measured.

- The code at the point of use reads as ordinary, sequential object
  navigation, with no visible branching for a data-fetching strategy.
- Only the associations a given code path actually touches are ever
  fetched, so a conditional branch that skips the loop body also skips
  every one of the N extra queries, which a blanket eager join cannot do.
- Writing the naive version requires no upfront analysis of which
  associations will be needed, which makes it the fastest code to produce
  on a first pass through a new feature.

Negative, once the shape is measured under realistic data volume.

- Query count scales linearly with the size of the collection being
  iterated, so total latency and total database load both grow with the
  data rather than staying bounded by the request's own shape.
- Each of the N extra round trips holds a database connection or
  connection-pool slot for its duration, so the pattern reduces the
  concurrent request throughput a fixed-size connection pool can sustain
  under load, independent of how fast any individual query runs.
- The defect is invisible against small development or staging datasets
  and becomes visible only once production data crosses a size threshold
  nobody explicitly chose, which means it is frequently discovered as a
  live incident rather than caught in review or in a load test that used
  unrepresentative data.
- The fix, once identified, is almost always small, a single additional
  method call or directive at the driving query, which means the ratio of
  production cost to fix cost for this specific anti-pattern is unusually
  poor, a large, growing, recurring cost is routinely being paid to avoid
  a change that is often one line.

## 11. Failure modes and misuse

**The disguised loop.** Symptom. A profiler or a query log shows dozens
or hundreds of near-identical queries differing only in a single bound
parameter, fired in a tight burst, for a single logical request. Cause.
A lazily loaded association, or a resolver, is touched inside a loop over
a collection, and the fetch that produces each query is hidden behind
ordinary property access. Fix. Replace the lazy touch with the ORM or
framework's eager-loading directive at the point where the driving
collection is queried, so the related data arrives with the first query
or with one second batched query.

**Eager loading applied to the wrong association.** Symptom. Query count
drops as intended, but response payload size or memory usage climbs
sharply, or an unrelated, deeply nested association that was never
actually used by this code path now loads unconditionally on every
request. Cause. An eager-loading directive was added broadly, to every
association reachable from the driving query, rather than narrowly, to
only the association the code path actually reads. Fix. Scope the eager
load to exactly the associations the current code path touches, verified
by reading the code, not by guessing from the schema.

**Cartesian explosion from a naive join fix.** Symptom. Fixing an N+1
warning by adding a single eager join across a one-to-many relationship
makes the query itself faster to write but the returned row count
balloons, and total data transferred and memory used to materialize
results goes up rather than down. Cause. A join across a one-to-many
relationship duplicates every column of the "one" side once per matching
row on the "many" side, so joining a parent with, for example, five
average child rows multiplies the parent's row data by five in the wire
format, before the application even begins deduplicating it back into
objects, a failure mode Entity Framework Core's own documentation names
explicitly under "avoid cartesian explosion when loading related
entities" (Microsoft Learn, "Efficient Querying, EF Core", verified
2026-08-02). Fix. Prefer a second, separate batched query, an `IN` clause
keyed by the parent identifiers, over a join, whenever the one-to-many
relationship has more than a small, bounded number of children per
parent, or use a framework's split-query feature where one exists.

**Fixed in one place, reintroduced in a helper.** Symptom. The obvious
driving query is correctly eager-loaded, the N+1 warning disappears from
the top-level query log, and yet total query count for the request is
still high. Cause. A nested helper method, a computed property, or a
serializer field, called once per item further down the call stack,
touches a second, different lazy association that the eager load never
covered. Fix. Trace every method called inside the loop body, not only
the loop's own direct property accesses, and eager-load every association
any of them reaches, or restructure the helper to accept pre-fetched data
as a parameter instead of fetching it itself.

**The N+1 that only appears under real data.** Symptom. Local development
and the automated test suite both pass with acceptable performance, and a
production incident or a slow-query alert surfaces the pattern only
after a table has grown past some threshold. Cause. Test fixtures and
seed data are small enough that the linear cost of N+1 stays below any
alerting threshold, so the defect ships and lies dormant. Fix. Seed
development and load-testing datasets at a size representative of
expected production scale, and add an automated query-count assertion,
described in dimension 15, that fails independent of dataset size.

**Batching loader with an unbounded batch size.** Symptom. A GraphQL or
DataLoader-based fix removes the per-item round trips as intended, but a
single request that returns an unusually large list still generates one
enormous `IN` clause or batch call with thousands of identifiers, which
itself becomes slow or hits a database parameter limit. Cause. The
batching layer removed the linear round-trip cost but did not bound the
batch size, so the linear cost simply moved from round trips to the size
of a single query. Fix. Chunk very large identifier sets into
fixed-size batches within the batching layer itself, rather than assuming
the fix is complete once round trips are down to a small, fixed count.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Naive N+1 loop | Eager join (single query, single-valued or bounded association) | Second batched query (IN clause) | Request-scoped batching loader (DataLoader-style) | Denormalization or materialized view | Application-level cache |
|---|---|---|---|---|---|---|
| Total round trips for N items | N+1, grows with N | 1 | 2, fixed regardless of N | 2, fixed regardless of N, per unique key set | 1, no join needed at read time | 1 on a cache miss, 0 on a hit |
| Risk of cartesian row duplication | None, no join issued | High, on one-to-many relationships with many children per parent | None, results matched in memory | None, results matched in memory | None, data is pre-flattened | Depends on what is cached |
| Fetches only what the code path uses | Yes, by construction | No, fetched unconditionally with the driving query | No, fetched unconditionally once the batch runs | Yes, only keys actually requested during execution are batched | No, materialized ahead of any specific request | Yes, only what was previously requested and retained |
| Data freshness | Always current | Always current | Always current | Always current | Stale until the next refresh | Stale until invalidation or expiry |
| Implementation cost | None, the default shape | Low, usually one additional method call | Low to medium, sometimes hand-written | Medium, a loader class plus wiring into the resolver layer | High, a schema and refresh pipeline | Medium, a cache layer plus invalidation strategy |
| Cross-service applicability | Works within a single data source only | Not applicable, joins require a single relational source | Works across a single data source's batch endpoint | Works across process and service boundaries | Not applicable across services | Works across service boundaries |
| Best fit | Never, in production, at scale | Single-valued or small-cardinality one-to-many associations | Large or unbounded one-to-many associations | GraphQL resolvers and cross-service fan-out | Read-heavy aggregates that tolerate staleness | Hot, repeatedly requested, slow-changing related data |

Reading of the table. An eager join wins when the related data is
single-valued or has a small, known upper bound of children per parent, a
case where the join's row duplication cost stays small. A second batched
query wins whenever that bound does not hold, because it avoids
cartesian explosion entirely at the cost of one extra round trip.
A request-scoped batching loader is the only option in the set that
naturally crosses process and service boundaries, which is why it is the
default fix for the GraphQL and microservice-fan-out variants from
dimension 8 rather than for the plain ORM variant, where a join or a
batched query is usually simpler. Denormalization and caching solve a
different problem, read latency and read load in the aggregate, and are
appropriate once the query shape itself is already fixed and the
remaining cost is inherent read volume rather than an accidental N+1.

## 13. Related and incompatible patterns

- **Lazy Load.** The pattern this anti-pattern misuses. Fowler's Lazy
  Load, catalogued in *Patterns of Enterprise Application Architecture*,
  is correct and valuable in isolation, deferring the cost of loading an
  association until it is actually needed. N+1 Query is what happens when
  a lazily loaded association is touched inside a loop over many objects
  rather than for one object in isolation, so the two are not opposites,
  Lazy Load is the mechanism, N+1 Query is its misuse under iteration.
- **Eager Loading.** The most direct antidote, and the one most ORMs
  expose as a single additional call, `includes` in Active Record,
  `Include` in Entity Framework Core, `select_related` and
  `prefetch_related` in Django, and `JOIN FETCH` or an entity graph in
  Hibernate. Eager Loading trades the conditional-fetch benefit of Lazy
  Load for a fixed, predictable query count, and dimension 12 above is the
  guide to when that trade is worth making.
- **Identity Map.** Fowler's Identity Map, which keeps each loaded object
  backed by exactly one in-memory instance per request or per unit of
  work, composes naturally with the batched-fetch fixes for
  N+1 Query, because a batched query that returns the same related
  parent for many child rows benefits from being deduplicated into one
  shared instance rather than one instance per row, which is precisely
  what tracking-enabled ORM contexts, including Entity Framework Core's
  default tracking behaviour, provide automatically.
- **Unit of Work.** A Unit of Work that tracks all objects read within a
  single logical operation is a natural place to implement request-scoped
  batching, because it already has visibility into every object load
  that has occurred so far in the current operation, which is the same
  visibility a DataLoader-style batching layer needs to coalesce
  requests.
- **Repository and Data Mapper.** Both patterns place a data-access
  abstraction between domain code and the underlying store. N+1 Query
  can hide equally well behind either, a Repository method or a Data
  Mapper's `find` method called in a loop is exactly the disguised-loop
  failure mode from dimension 11, which is why both patterns should
  expose a batch-oriented finder, accepting a collection of identifiers
  and returning a collection of results, alongside their single-item
  finder.
- **Batch Method.** The design idiom of accepting many inputs and
  returning many outputs from a single call, rather than one input and
  one output per call, is the structural fix underlying nearly every
  remedy in dimension 8, the eager join, the `IN`-clause batched query,
  and the DataLoader-style batching layer are all instances of Batch
  Method applied to data access specifically.
- **Facade.** A Facade that wraps several related fetches behind one
  coarse-grained call is a related idea at a different layer, it hides
  complexity behind an interface rather than reducing round-trip count
  by itself, and a Facade implemented naively, by internally calling N
  fine-grained operations in a loop, is itself a common place for N+1
  Query to hide.
- **Incompatibilities.** N+1 Query has no incompatible relationship with
  another named pattern in the sense of an active design conflict,
  because it is not a design choice anyone makes deliberately, it is a
  failure mode that arises from applying Lazy Load without also applying
  one of the batching patterns above.

## 14. Refactoring path in and out

How the shape is typically introduced, unintentionally, since nobody sets
out to write N+1 Query on purpose.

1. A feature is built against a lazily loaded ORM association or a
   GraphQL resolver field, and the developer writes the natural,
   sequential loop that touches that association once per item, because
   it is the shortest path to a working feature.
2. Local development and the test suite run against a small seed dataset,
   so the linear query cost stays low enough that nobody notices it,
   which is the delayed-onset property named in dimension 2.
3. The feature ships. The collection the loop iterates grows over weeks
   or months as real data accumulates, and the per-request query count
   grows with it, silently, until either a slow-query alert fires, a
   database connection pool starts saturating under peak load, or a
   profiling pass or a tool like Bullet flags the pattern directly.

The path out, once the shape has been found.

1. Identify the exact association or per-item fetch responsible, using
   the observability signals in dimension 16, a query log or a
   development-time detector such as Bullet is normally sufficient to
   name the offending line precisely.
2. Confirm the cardinality of the relationship being fetched. A
   single-valued or small, bounded one-to-many association is a
   candidate for an eager join at the driving query. A large or unbounded
   one-to-many association is a candidate for a second, separate batched
   query instead, to avoid the cartesian explosion failure mode from
   dimension 11.
3. Apply the framework's own eager-loading directive at the point the
   driving collection is queried, not deeper in the call stack where the
   loop lives, so the fix is visible at the query's origin rather than
   buried inside a helper.
4. Re-trace every helper method, computed property, or serializer field
   invoked inside the loop body, not only the loop's own direct property
   access, because a second, unrelated lazy touch further down the call
   stack reintroduces the pattern even after the obvious one is fixed,
   the exact failure mode named in dimension 11.
5. Add the automated query-count assertion from dimension 15 against a
   fixture sized to more than one row, so the fix, once made, cannot
   silently regress the next time someone edits the same code path.
6. For the GraphQL and cross-service variants from dimension 8, where no
   single join is available because the data crosses a process boundary,
   introduce a request-scoped batching loader at the resolver or
   client-call layer instead, so that every individual request for the
   same kind of related data made during one logical operation is
   coalesced before it leaves the process.

Removing the fix later, when the code has evolved past needing it, is
rarely relevant for this anti-pattern, because the fixes described above,
an eager-loading directive or a batching loader, cost nothing when the
association turns out to be unused on a given code path, an eager join
still runs a single query even if the fetched association is never read,
and a batching loader coalesces zero calls into zero batches when
nothing requests a key. Removing a correctly applied fix is therefore
almost never warranted on performance grounds, the only legitimate reason
to remove one is that the code path it served was itself deleted.

## 15. Testing and verification

Easier because of naming and fixing the pattern.

- Once a batching layer exists at a stable boundary, a request-scoped
  DataLoader or an eager-loading directive at a driving query, that
  boundary becomes a single, well-defined place to assert query count
  from a test, rather than needing to reason about every call site
  individually.
- A fixed, batched query shape is simpler to assert against in a test
  than a variable, data-dependent one, because the expected query count
  no longer depends on how many rows the test fixture happens to contain.

Harder because of the pattern.

- The defect is, by definition, invisible in any test that runs against a
  fixture of one or two rows, because one or two rows produce one or two
  extra queries, a difference too small to notice without deliberately
  asserting on the count. A regression test for this anti-pattern must
  therefore be written with more than one row in its fixture on purpose,
  which is easy to forget.
- Standard assertion styles that check only the final returned value, not
  the number of queries issued to produce it, pass identically whether
  the code issued one query or one hundred, so a correctness-only test
  suite provides no protection against this class of regression at all.

Techniques that apply.

- **Query-count assertion.** Wrap the code under test in the framework's
  own query-counting or query-capturing facility, most ORMs expose one,
  Active Record's `assert_queries_count`, Django's
  `assertNumQueries`, or a raw SQL logging capture for frameworks without
  a built-in helper, run the code against a fixture of at least three
  rows, and assert the query count stays at a small, fixed number
  independent of fixture size. This is the single most direct and most
  commonly used technique for this specific anti-pattern.
- **Fixture-size parameterization.** Run the same test twice, once
  against a fixture of two rows and once against a fixture of twenty, and
  assert the query count is identical between the two runs. A query
  count that grows with fixture size, even when both individual runs
  pass some fixed absolute threshold, is the signature of N+1 Query and
  is a stronger, more portable assertion than a fixed absolute count,
  which can rot as the codebase's baseline query count changes for
  unrelated reasons.
- **Development-time monitoring in the integration environment.** Tools
  built specifically for this, such as the Bullet gem for Rails, run
  continuously in a development or staging environment and surface a
  warning the moment a request triggers the pattern, which catches
  regressions introduced through code paths a hand-written test suite
  did not anticipate.
- **Contract test on a batching layer's public shape.** Where a
  DataLoader-style batching layer exists, test its batch function
  directly with a set of keys larger than one, asserting it is called
  exactly once per distinct set of keys collected during a single
  execution tick, rather than once per key, which verifies the
  coalescing behaviour the layer exists to provide, independent of
  whatever resolver code happens to call it.

## 16. Observability signals

The pattern's whole signature is a count and a shape, so the most useful
signals are counting and pattern-matching ones rather than duration ones
alone, though duration matters too.

What to record.

- A per-request or per-transaction count of queries issued, tagged with
  the request or resolver name, either from database driver
  instrumentation or from an ORM's own query-logging hook. This single
  number, tracked over time, is the primary early-warning signal, a
  steady climb in average query count per request for one endpoint,
  uncorrelated with a feature change to that endpoint, is close to
  diagnostic of a growing collection driving a latent N+1.
- A structural fingerprint of each query, normalized by replacing literal
  parameter values with placeholders, so that repeated near-identical
  queries differing only in a bound identifier can be grouped and
  counted as one logical pattern rather than as unrelated distinct
  queries, which is exactly how development-time detectors such as
  Bullet identify the pattern in the first place.
- Query duration, both per query and summed per request, because the
  N+1 shape often shows a healthy per-query duration alongside an
  unhealthy summed duration, a distinction that is invisible unless both
  numbers are recorded and compared, a slow-query alert tuned only to
  individual query duration will never fire for this anti-pattern.
- For GraphQL specifically, a per-field resolver call count, so that a
  list field's nested resolver can be seen firing once per item in the
  parent list, which is the direct GraphQL analogue of the ORM query
  count above.
- Database connection pool utilization and wait time, because the
  connection-pool-pressure force from dimension 3 shows up here first,
  often before any individual request's latency looks alarming on its
  own.

A healthy instance on a dashboard. Query count per request stays flat
across time for a given endpoint, independent of how much data has
accumulated in the tables that endpoint reads, and the flat count is
small, typically in the single digits for a page or resource that returns
a bounded page size. Summed query duration per request tracks closely
with individual query duration times the flat query count, with no
divergence.

A failing instance. Query count per request for one endpoint climbs
steadily over weeks, tracking the growth of an underlying table rather
than tracking any deploy or feature change, which is the delayed-onset
signature from dimension 2 made visible on a chart. Or a normalized query
fingerprint shows one query shape repeated dozens or hundreds of times
within a single request trace, each instance differing only in a bound
identifier, which is the pattern's structural signature appearing
directly. Or connection pool wait time rises during traffic spikes on an
endpoint whose individual query latency has not itself changed, which
points at the round-trip count, not any single query's cost, as the root
cause.

## 17. Security and privacy implications

The pattern is largely silent on confidentiality and integrity in its own
right, it changes how many round trips a request makes, not what data a
request is authorized to see or write, and it would be inventing a
concern to claim otherwise for the core shape. Three genuine implications
follow once the pattern's cost characteristics are considered.

**Denial of service through data growth.** Because the pattern's cost
scales linearly with a collection size that is often influenced or
directly controlled by user-supplied input, for example the number of
items a user has added to an order, uploaded to a folder, or posted to a
feed, an attacker who can grow that collection arbitrarily can turn an
otherwise ordinary request into an expensive one purely by inflating N,
without needing any other vulnerability. A list endpoint that lacks
pagination and also carries an N+1 shape compounds this risk directly,
since both the returned payload size and the query count scale together
with whatever N the attacker chooses. The mitigation is not specific to
this anti-pattern, bound page sizes and per-request rate limits, but the
pattern makes an unbounded endpoint materially more dangerous than the
same endpoint with a fixed, small query count would be.

**Connection pool exhaustion as an availability risk.** The pool-pressure
force from dimension 3 is, at sufficient scale, an availability
vulnerability rather than only a performance one, a small number of
concurrent requests each triggering a large N+1 fan-out can exhaust a
shared database connection pool faster than an equivalent number of
requests each issuing one bounded, batched query would, degrading or
denying database access to every other, unrelated request sharing that
pool. This is worth naming explicitly because it means fixing N+1 Query
on a small number of high-traffic or attacker-reachable endpoints can be
a meaningful availability hardening step, not only a latency
optimization.

**Batched fixes changing the authorization surface.** This is a caution
about the fix rather than about the original pattern. Replacing N
individually authorized per-item fetches with one batched, unfiltered
query, an `IN` clause across identifiers collected from the driving
collection, must preserve whatever row-level authorization check each
individual fetch used to perform, because a naive batch rewrite that
drops a per-tenant or per-owner filter present in the original per-item
query can silently widen what data a batched result returns compared to
what the N individual, correctly filtered queries would have returned.
Any refactor from the naive shape to a batched one should therefore
re-verify, explicitly, that the batched query's `WHERE` clause carries
every authorization condition the per-item version carried, not only its
join key.

On privacy specifically the pattern is neutral, with the same caveat
raised in dimension 16 for observability, normalized query fingerprints
and per-request logs are useful debugging data, and where the identifiers
they capture are themselves personally identifying, for example a user
or customer identifier appearing in a logged query parameter, the same
retention and access controls that apply to any other log containing
identifiers should apply here too.

## 18. References

1. Ruby on Rails Guides. "Active Record Query Interface", section 13.1,
   "N + 1 Queries Problem".
   https://guides.rubyonrails.org/active_record_querying.html
   Verified 2026-08-02. Source for the canonical name, the eleven-query
   worked example, and the `includes`, `preload`, and `eager_load`
   methods.
2. Django Software Foundation. *Django 5.2 documentation*,
   `QuerySet.select_related()` and `QuerySet.prefetch_related()`.
   https://docs.djangoproject.com/en/5.2/ref/models/querysets/#select-related
   Verified 2026-08-02. Source for the Django ORM fix pair, the
   join-based single-valued fix and the separate-lookup many-valued fix.
3. Lee Byron and the GraphQL Foundation. `graphql/dataloader`, README.
   https://github.com/graphql/dataloader
   Verified 2026-08-02. Source for the batching-and-caching definition
   and the thirteen-to-four request reduction example used to motivate
   the GraphQL resolver variant.
4. Shopify. `Shopify/graphql-batch`, README.
   https://github.com/Shopify/graphql-batch
   Verified 2026-08-02. Source for the Ruby GraphQL batching executor
   used as the production-use example in dimension 9.
5. Red Hat and the Hibernate community. *Hibernate ORM 6.4 User Guide*,
   Chapter 12, "Fetching", sections 12.5 through 12.12.
   https://docs.hibernate.org/orm/6.4/userguide/html_single/Hibernate_User_Guide.html
   Verified 2026-08-02. Source for the fetch-strategy machinery, entity
   graphs, batch fetching, and the `@Fetch` annotation cited in
   dimensions 1 and 9.
6. Richard Huang (flyerhzm). `flyerhzm/bullet`, README.
   https://github.com/flyerhzm/bullet
   Verified 2026-08-02. Source for the Bullet gem's stated purpose and
   the direct quotation naming N+1 queries.
7. Martin Fowler. *Patterns of Enterprise Application Architecture*,
   Addison-Wesley, 2002. "Lazy Load".
   https://martinfowler.com/eaaCatalog/lazyLoad.html
   Verified 2026-08-02. Source for the Lazy Load pattern definition and
   the general warning that loading one object can trigger loading many
   related objects, cited in dimensions 1 and 13.
8. Microsoft. *Entity Framework Core documentation*, "Efficient
   Querying", sections "Avoid cartesian explosion when loading related
   entities" and "Beware of lazy loading".
   https://learn.microsoft.com/en-us/ef/core/performance/efficient-querying
   Verified 2026-08-02. Source for the explicit "N+1" naming in EF Core's
   own documentation, the cartesian explosion distinction in dimension
   1 and dimension 11, and the worked lazy-loading log example in
   dimension 9.

## Code examples

Three languages, each demonstrating the naive N+1 shape against a small
in-memory simulated data store that counts round trips, and then the
batched fix against the identical data, so the round-trip count difference
is a number the program itself prints rather than an assertion made in
prose. All three were executed to produce the shown output.

### Python

```python
class Db:
    def __init__(self):
        self.posts = [{"id": i, "author_id": i % 3} for i in range(1, 11)]
        self.authors = {0: "Ada", 1: "Grace", 2: "Barbara"}
        self.round_trips = 0

    def fetch_posts(self):
        self.round_trips += 1
        return list(self.posts)

    def fetch_author(self, author_id):
        self.round_trips += 1
        return self.authors[author_id]

    def fetch_authors_by_ids(self, author_ids):
        self.round_trips += 1
        return {aid: self.authors[aid] for aid in set(author_ids)}


def naive(db: Db):
    posts = db.fetch_posts()
    for post in posts:
        db.fetch_author(post["author_id"])  # one round trip per post
    return db.round_trips


def batched(db: Db):
    posts = db.fetch_posts()
    author_ids = [p["author_id"] for p in posts]
    authors = db.fetch_authors_by_ids(author_ids)
    for post in posts:
        _ = authors[post["author_id"]]  # no round trip, in-memory lookup
    return db.round_trips


naive_db = Db()
naive_count = naive(naive_db)

batched_db = Db()
batched_count = batched(batched_db)

print(f"naive round trips.   {naive_count}")
print(f"batched round trips. {batched_count}")
assert naive_count == 11
assert batched_count == 2
```

### TypeScript

```typescript
interface Post {
  id: number;
  authorId: number;
}

class Db {
  posts: Post[] = Array.from({ length: 10 }, (_, i) => ({
    id: i + 1,
    authorId: i % 3,
  }));
  authors: Record<number, string> = { 0: "Ada", 1: "Grace", 2: "Barbara" };
  roundTrips = 0;

  fetchPosts(): Post[] {
    this.roundTrips += 1;
    return [...this.posts];
  }

  fetchAuthor(authorId: number): string {
    this.roundTrips += 1;
    return this.authors[authorId];
  }

  fetchAuthorsByIds(authorIds: number[]): Map<number, string> {
    this.roundTrips += 1;
    const unique = [...new Set(authorIds)];
    return new Map(unique.map((id) => [id, this.authors[id]]));
  }
}

function naive(db: Db): number {
  const posts = db.fetchPosts();
  for (const post of posts) {
    db.fetchAuthor(post.authorId); // one round trip per post
  }
  return db.roundTrips;
}

function batched(db: Db): number {
  const posts = db.fetchPosts();
  const authors = db.fetchAuthorsByIds(posts.map((p) => p.authorId));
  for (const post of posts) {
    authors.get(post.authorId); // no round trip, in-memory lookup
  }
  return db.roundTrips;
}

const naiveDb = new Db();
const naiveCount = naive(naiveDb);

const batchedDb = new Db();
const batchedCount = batched(batchedDb);

console.log(`naive round trips.   ${naiveCount}`);
console.log(`batched round trips. ${batchedCount}`);
if (naiveCount !== 11 || batchedCount !== 2) {
  throw new Error("unexpected round trip count");
}
```

### Go

```go
package main

import "fmt"

type Post struct {
	ID       int
	AuthorID int
}

type Db struct {
	posts      []Post
	authors    map[int]string
	roundTrips int
}

func newDb() *Db {
	posts := make([]Post, 10)
	for i := range posts {
		posts[i] = Post{ID: i + 1, AuthorID: i % 3}
	}
	return &Db{
		posts:   posts,
		authors: map[int]string{0: "Ada", 1: "Grace", 2: "Barbara"},
	}
}

func (d *Db) fetchPosts() []Post {
	d.roundTrips++
	out := make([]Post, len(d.posts))
	copy(out, d.posts)
	return out
}

func (d *Db) fetchAuthor(authorID int) string {
	d.roundTrips++
	return d.authors[authorID]
}

func (d *Db) fetchAuthorsByIDs(authorIDs []int) map[int]string {
	d.roundTrips++
	seen := map[int]bool{}
	out := map[int]string{}
	for _, id := range authorIDs {
		if !seen[id] {
			seen[id] = true
			out[id] = d.authors[id]
		}
	}
	return out
}

func naive(d *Db) int {
	posts := d.fetchPosts()
	for _, post := range posts {
		d.fetchAuthor(post.AuthorID) // one round trip per post
	}
	return d.roundTrips
}

func batched(d *Db) int {
	posts := d.fetchPosts()
	ids := make([]int, len(posts))
	for i, p := range posts {
		ids[i] = p.AuthorID
	}
	authors := d.fetchAuthorsByIDs(ids)
	for _, post := range posts {
		_ = authors[post.AuthorID] // no round trip, in-memory lookup
	}
	return d.roundTrips
}

func main() {
	naiveDb := newDb()
	naiveCount := naive(naiveDb)

	batchedDb := newDb()
	batchedCount := batched(batchedDb)

	fmt.Printf("naive round trips.   %d\n", naiveCount)
	fmt.Printf("batched round trips. %d\n", batchedCount)
	if naiveCount != 11 || batchedCount != 2 {
		panic("unexpected round trip count")
	}
}
```
