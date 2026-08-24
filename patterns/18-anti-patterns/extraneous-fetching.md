---
name: Extraneous Fetching
slug: extraneous-fetching
family: 18-anti-patterns
category: Anti-pattern
aliases: [Overfetching, Fetching Too Much Data, SELECT star anti-pattern]
first_described: "Microsoft Azure Architecture Center performance antipattern collection, 2017"
maturity: established
related: [n+1-query, chatty-i-o, cqrs, backends-for-frontends]
incompatible_with: []
verified: 2026-08-02
---

# Extraneous Fetching

## 1. Name, aliases, and lineage

The canonical name in the software architecture literature is Extraneous
Fetching. It names the mistake of retrieving more data from a store, a
service, or a database than the calling code actually consumes. The term
appears as one of the named cloud application performance antipatterns
documented by Microsoft's patterns and practices group and later folded into
the Azure Architecture Center's antipattern catalog, alongside siblings such
as the Chatty I/O antipattern and the No Caching antipattern. That catalog
frames the problem generically, across relational databases, document stores,
and remote services, rather than tying it to one storage technology.

The most common alias in day to day conversation is **overfetching**, a word
that entered wide circulation through the GraphQL community's own framing of
the problem it was built to solve. The GraphQL project positions itself
against two related but distinct failures, overfetching (the response carries
fields nobody asked for) and underfetching (a single screen needs several
round trips to assemble). Extraneous Fetching, as this entry treats it, is the
overfetching half of that pair, generalized past GraphQL to every data access
layer, not only HTTP APIs. **SELECT star anti-pattern** is the SQL flavoured
name practitioners use for the narrowest case, a wide select where three of
twelve columns are read.

A closely related but distinct failure is the **N+1 queries problem**, where
a single logical fetch is issued as one query per row instead of one query
for the whole batch, and this repository carries that as its own entry under
`n+1-query`, cross referenced throughout this entry rather than merged into
it, because the fix, the diagnosis, and the failure signature differ.
Extraneous Fetching, narrowly, is about the SHAPE of a single fetch carrying
more than it should. N+1 is about the COUNT of fetches multiplying by rows. A
system can have either without the other, and a bad ORM configuration
commonly produces both at once, which is why they are so often confused in
casual writing.

This entry's judgement, stated plainly rather than dressed as a citation. The
literature has never settled on one crisp technical term the way it settled on
Singleton or Observer. The pattern is old enough to predate the internet era,
a mainframe program reading an entire wide record to print three fields is
the same mistake, and it re-earns a name in every generation of data access
technology, from ODBC cursors to ORMs to GraphQL to gRPC field masks, because
each generation's tooling makes the lazy default look free at the call site
while it is expensive at the wire and at the disk.

## 2. Problem and context

A piece of code needs three fields from a record, a page needs the title and
the thumbnail of a hundred articles, a mobile screen needs a user's display
name and avatar. The code that fetches the data does not ask for those three
fields, that title and thumbnail, that name and avatar. It asks for the whole
record, the whole article body plus its full comment thread, the whole user
profile with every preference and every historical order. The unneeded data
is read from disk, deserialized, sent across the network, and then discarded
by the caller a few lines later.

The context in which this problem arises has a recognizable shape. There is
a data access layer, whether that is a raw SQL client, an object relational
mapper, a document database driver, or an HTTP client calling a remote
service, and there is a consumer of that layer's output that needs a strict
subset of what the layer's default call returns. The layer's ergonomic
default is almost always to give back the whole thing, because that is the
simplest API to design and the simplest one to reason about at the call site.
`GetUser(id)` returns a `User`, not a projection the caller has to construct
by hand. That ergonomic convenience is exactly what makes the antipattern so
persistent. The code that overfetches reads cleanly and looks correct, and it
IS correct, in the sense that it returns the right answer. It is merely
wasteful, and waste at a single call site is invisible until the call site is
exercised at production volume, behind a slow network link, against a table
that has grown from ten thousand rows to ten million.

Two contextual variables decide how much the waste matters. First, the ratio
of consumed fields to fetched fields. A record with four columns, three of
which are used, is a rounding error. A record with sixty columns including
three large text or binary fields, of which two integers are used, is a real
cost. Second, the multiplier. A single overfetch executed once per user
session is nothing. The identical overfetch executed inside a loop over a
result set, or on every request to a hot endpoint, or across a slow
cross region network hop, turns a rounding error into the dominant cost of
the request. Extraneous Fetching is, above everything else, a pattern that is
invisible in a unit test against a five row fixture table and glaring in
production against the real data volume, which is precisely why it survives
code review so often.

## 3. Forces

Judgement. The weighting below reflects engineering practice and profiling
experience rather than a single citable source, and is presented as such.

- **Developer ergonomics versus efficiency.** A method that returns the
  whole thing is trivial to write, trivial to call, and trivial to extend
  later without a signature change. A method that returns exactly what is
  needed requires the author to think about every caller's actual needs, and
  a new caller with different needs either gets a new method or reuses the
  narrow one and pays for a second round trip. Extraneous Fetching is what
  happens when ergonomics wins by default and nobody revisits the trade.
- **I/O cost versus CPU cost.** Fetching extra fields costs disk read time,
  network bytes, deserialization CPU, and, for a remote call, serialization
  CPU on the far side. Fetching exactly what is needed costs a small amount
  of additional query authoring or projection logic. On a fast local
  database this trade tends to favour the wide fetch, over a WAN, a mobile
  connection, or a metered cloud egress link, it tends to favour the narrow
  one, sharply.
- **Cache friendliness.** A narrow, stable projection is a smaller, more
  cacheable unit than a whole entity that changes on every unrelated field
  update. A wide fetch invalidates its cache entry whenever any field
  changes, even one the consumer never reads, so overfetching quietly
  degrades cache hit rate as a second order effect beyond the direct
  transfer cost.
- **API surface size versus reuse.** Returning the whole entity from one
  general purpose accessor keeps the API surface small, one method serves
  every caller. Returning exactly what each caller needs multiplies the
  number of accessors, or pushes the caller toward a query language, such as
  GraphQL, OData, or a fields query parameter, that can express an
  arbitrary projection without multiplying methods, at the cost of that
  query language's own complexity and attack surface, covered in
  dimension 17.
- **Consistency of the read.** Fetching the whole row in one query gives a
  point in time consistent view of every field. Fetching narrow projections
  from several sources, or joining a wide table down after the fact, can
  introduce read skew if the underlying data changes between fetches. This
  favours wide fetches in contexts where cross field consistency at read
  time genuinely matters, which is uncommon for display purposes and common
  for financial or inventory reads.
- **Change propagation cost.** A narrow, hand projected query names every
  column it wants, so when the caller's needs grow, the projection must be
  edited at every call site that constructed it independently, unless the
  fetch is centralized. A wide fetch never needs editing when a caller's
  needs grow, because it already returns everything. This is the strongest
  argument in favour of overfetching that is not merely developer laziness,
  and it is the reason the correct fix in dimension 14 centralizes the
  projection rather than inlining it everywhere.

## 4. Applicability and non-applicability

This is an antipattern entry, which inverts the usual applicability
question. There is no context in which extraneous fetching itself should be
adopted on purpose. What belongs here instead is when the SYMPTOM is worth
fixing, and, equally importantly, when it is not.

Fix it when the following hold.

- Profiling, an APM trace, or a query log shows a hot code path transferring
  far more bytes or columns than the caller consumes, and that path runs
  often enough for the waste to show up in latency or infrastructure cost.
- The unused fields are expensive relative to the used ones. Large text,
  binary, JSON, or array columns fetched and discarded cost far more than an
  unused integer or boolean sitting in the same row.
- The fetch crosses an expensive boundary. A local process reading an unused
  integer column from an in memory cache is not the same problem as a mobile
  client downloading an unused two megabyte photo URL blob field over a
  cellular connection, or a service calling another service across a region
  boundary for a field it discards.
- The fetch runs inside a loop, so a small per item waste is multiplied by
  the collection size, which is the shape that turns a negligible cost into
  the dominant cost of a request.

Do NOT chase this antipattern in these cases, and the reason is the point.

- **The measured cost is negligible.** A four column row with one unused
  boolean flag is not worth a bespoke projection, a new method, or a schema
  change. Premature narrowing here trades a real readability and reuse cost
  for an imaginary performance win, which is itself a form of the
  optimization antipattern this repository's premature optimization entry
  covers. Measure before narrowing, every time.
- **The unused fields will be needed soon, provably.** A profile fetch that
  returns three unused fields today because the next sprint's feature reads
  them next month is not waste, it is a stable contract a second consumer is
  about to join. Narrowing it now only to widen it again in four weeks is
  churn, not correctness.
- **The fetch is already the batched, correct shape and the extra data is
  the batching itself.** A paginated list endpoint that returns twenty rows
  when the UI shows ten because the eleventh through twentieth are prefetched
  for a fast next page click is not extraneous fetching, it is a deliberate
  read ahead trade, and removing it to satisfy a narrow reading of this
  antipattern would make the UI slower, not faster.
- **The projection would break a consistency guarantee the caller actually
  relies on.** If a financial reconciliation job reads a wide row
  specifically so every derived total is computed against one consistent
  snapshot, splitting that into narrow, independently timed queries can
  introduce the exact class of bug the wide read was preventing. The forces
  in dimension 3 name this trade explicitly.
- **The access pattern is not stable enough to justify a bespoke
  projection.** Ad hoc, one off, or exploratory queries, a data analyst
  running an unbounded select in a notebook, an internal admin tool used by
  three people, are not worth optimizing. Extraneous fetching is a
  production hot path problem, not a blanket ban on ever reading more than
  you need.
- **The framework already batches the wide fetch efficiently and the wide
  shape is genuinely reused.** An ORM's default eager load of a small,
  frequently reused association is not automatically extraneous fetching
  merely because one particular caller does not use one particular field of
  it, if most callers do.

## 5. Structure

Extraneous Fetching is a behavioural, cross cutting antipattern rather than a
class diagram of collaborating objects, so its structure is best described as
the shape of the call and the actors around it.

- **Consumer.** The code that ultimately uses a strict subset of the data
  returned by a fetch. It may be a UI component, an API handler assembling a
  response, a batch job, or another service.
- **Data access layer.** The ORM, query builder, HTTP client, or driver that
  executes the fetch. It exposes an ergonomic default, return the whole
  entity, the whole response body, the whole row, that is easy to call and
  wide by construction.
- **Data source.** The database, document store, cache, or remote service
  that holds more fields, columns, or nested structures than any single
  consumer needs. It has no opinion about which subset any given caller
  wants, unless the caller tells it.
- **Wire or storage boundary.** The place where the waste is actually paid
  for. Disk I/O and buffer cache pressure on the database side.
  Serialization CPU on the source side. Network bytes in flight.
  Deserialization CPU and heap allocation on the consumer side. The
  antipattern's true cost is always paid at this boundary, never at the
  point where the code looks wasteful.
- **The missing participant, a projection contract.** The structural fix,
  covered in dimension 14, introduces a fourth thing that a naive design
  lacks, an explicit, named shape, a DTO, a GraphQL selection set, a SQL
  column list, a field mask, that sits between the consumer and the data
  access layer and states exactly what is needed. Its absence is the
  structural signature of the antipattern.

## 6. ASCII structure diagram

```
THE ANTIPATTERN (no projection contract)

+----------------------+
| Consumer, needs: {a} |
+----------------------+
           | default wide call
           v
+-------------------+
| Data Access Layer |
+-------------------+
           | SELECT * / GET /entity
           v
+---------------------------+
| Data Source (a..f + more) |
+---------------------------+
           |
           | full entity {a, b, c, d, e, f}
           v
(back to Consumer, b..f discarded after use of a)

THE FIX (explicit projection contract)

+----------------------+
| Consumer, needs: {a} |
+----------------------+
           | request naming needs {a}
           v
+-------------------+
| Data Access Layer |
+-------------------+
           | SELECT a / GET /entity?fields=a
           v
+---------------------------+
| Data Source (a..f + more) |
+---------------------------+
           |
           | {a} only
           v
(back to Consumer, nothing discarded)
```

## 7. Dynamics

The runtime flow of the antipattern is unremarkable, which is exactly the
point, nothing looks wrong while it is happening.

```
Consumer          DataAccessLayer         DataSource
  |                     |                      |
  |-- getEntity(id) --->|                      |
  |                     |-- SELECT * / GET --->|
  |                     |                      |-- reads a..f, serializes all
  |                     |<-- {a,b,c,d,e,f} ----|
  |<-- {a,b,c,d,e,f} ---|                      |
  |                     |                      |
  |-- reads field a --->|                      |
  |   (b..f discarded, cost already paid)      |
  |                     |                      |
```

Compare the fixed dynamics, where the cost at the data source is
proportionally smaller because the source never materializes the unused
fields in the first place, not merely because the consumer ignores them
after the fact.

```
Consumer          DataAccessLayer         DataSource
  |                     |                      |
  |-- getEntity(id, --->|                      |
  |     fields=[a])     |                      |
  |                     |-- SELECT a / --------|
  |                     |   GET ?fields=a       |
  |                     |                      |-- reads only a, serializes a
  |                     |<-- {a} --------------|
  |<-- {a} -------------|                      |
  |                     |                      |
  |-- reads field a --->|                      |
  |   (nothing discarded)                      |
```

The N+1 variant compounds this dynamic across a collection, which is worth
showing because it is the shape most engineers actually encounter first.

```
Consumer                 DataAccessLayer            DataSource
  |-- getBooks(limit=10) --------------------------->|
  |<-- 10 book rows (no author data) ----------------|
  |
  |  for each book:
  |    |-- getAuthor(book.authorId) ------------------->|
  |    |<-- author row --------------------------------|
  |    (repeated 10 times, one round trip per book)
```

## 8. Implementation variants

**Explicit column or field projection.** The caller states the exact column
list, or the exact field set in an ORM's projection API, such as EF Core's
`Select`, Django's `only` or `values`, JPA's constructor expression, or
ActiveRecord's `pluck`. This is the cheapest, most direct fix and the one
demonstrated in dimension 14, at the cost of one named shape per distinct
consumer need.

**Query language selection sets.** GraphQL, and similarly OData's field
selection syntax and gRPC field masks, let the caller specify the desired
fields as part of the request itself, so the server side resolver or query
executor can translate that into a narrow underlying fetch. This
generalizes the projection idea to a network boundary and to callers the
server author has never seen, at the cost of a more complex request contract
and the query depth and selection abuse risks covered in dimension 17.

**Data transfer objects shaped per use case.** Rather than a single
projection reused everywhere, a dedicated, named type per screen or per
endpoint, an article list item type versus an article detail type, makes the
exact contract explicit in the type system and in the API documentation, and
lets the compiler catch a consumer that starts needing a field the type does
not carry. This is the shape most commonly seen at a REST or GraphQL API
boundary rather than inside a single service's internal data layer.

**Backend for Frontend.** When several client types, a web app, a mobile
app, a partner integration, each need a different narrow slice of the same
underlying wide entities, a dedicated backend layer per frontend composes
and narrows the fetch on the server side, so no single client downloads
fields shaped for a different client. This is a structural, service level
answer to extraneous fetching across many callers rather than a per query
fix, and is its own entry under `backends-for-frontends`.

**Batching plus narrow selection together.** DataLoader style batched
loaders, widely used behind GraphQL resolvers, solve the N+1 sibling
problem, collapsing per item fetches into one batched call, and are commonly
combined with an explicit field selection so the batched call itself is also
narrow. The two techniques are complementary, not substitutes for each
other.

**Lazy fetching with an explicit trigger.** Rather than eagerly fetching a
wide entity, expose an accessor that fetches a specific related piece only
when the consumer asks for it, an ORM's lazy loaded association, a paged
load more details API. This trades an eager wide fetch for a possible extra
round trip, which is only a net win when most consumers do not need the
lazy piece, and is a net loss, reintroducing the antipattern's sibling, when
most consumers eventually touch it anyway inside a loop, see the beware of
lazy loading warning cited in dimension 9.

**Response compression and field masking at the transport layer.** Where
the underlying query cannot easily be narrowed, a third party API with a
fixed response shape, gzip or Brotli compression and, where the API
supports it, a partial response field mask query parameter reduce the wire
cost of an otherwise wide response without touching the query itself. This
treats the symptom at the transport boundary rather than the cause at the
data access layer, and is a legitimate mitigation when the data access layer
is out of the caller's control.

## 9. Known production uses

**Entity Framework Core, projection guidance and the N+1 lazy loading
warning.** Microsoft's own EF Core performance documentation carries a
dedicated section titled "Project only properties you need", which
demonstrates exactly this antipattern. Iterating `context.Blogs` and
printing only `blog.Url` still executes a select of `BlogId`, `CreationDate`,
`Name`, `Rating`, and `Url`, fetching four unused columns per row, and the
fix, `context.Blogs.Select(b => b.Url)`, produces a select of `Url` alone.
The same page's "Beware of lazy loading" section documents the closely
related N+1 sibling by name, showing one query for all blogs followed by one
additional query per blog to lazily load its posts. Microsoft, EF Core
documentation, Efficient Querying, sections Project only properties you need
and Beware of lazy loading,
https://learn.microsoft.com/en-us/ef/core/performance/efficient-querying
verified 2026-08-02.

**Django ORM, `select_related` and the deluge of database queries it exists
to prevent.** Django's queryset documentation states that `select_related()`
is a performance booster which results in a single more complex query but
means later use of foreign key relationships will not require database
queries, and demonstrates the naive case, fetching an entry then fetching its
related blog, executing two separate queries against the database, collapsed
to one query with a SQL join once `select_related("blog")` is applied.
Django Software Foundation, Django 5.2 documentation, QuerySet API
reference, `select_related()`,
https://docs.djangoproject.com/en/5.2/ref/models/querysets/#select-related
verified 2026-08-02.

**Ruby on Rails Active Record, `includes` and the documented N+1 query
count.** The Rails guides walk through loading ten books and their authors
in a loop, stating plainly that the code executes one query to find ten
books plus ten queries, one per each book, to load the author, eleven
queries in total, then show that adding `includes(:author)` reduces the
same operation to exactly two queries, the ten book select and a single
select of every needed author at once. Ruby on Rails, Active Record Query
Interface guide, section Eager Loading Associations,
https://guides.rubyonrails.org/active_record_querying.html#eager-loading-associations
verified 2026-08-02.

## 10. Consequences

Positive consequences of recognizing and fixing the antipattern.

- Lower query and response latency, because less data is read from disk,
  serialized, transmitted, and deserialized per call.
- Reduced infrastructure cost, most visibly on metered cloud egress and
  managed database compute, where bytes scanned and bytes transferred are
  billed line items.
- Better cache hit rates, since a narrow, stable projection changes less
  often than the wide entity it was carved from.
- A more legible contract at each call site, because the projection names
  exactly what the caller depends on, which also makes future schema
  changes safer, a field the projection does not name can be renamed or
  removed without breaking that caller.
- Lower memory pressure under load, since fewer discarded bytes are
  allocated, copied, and garbage collected per request.

Negative consequences of the fix itself, honestly stated, since a pattern
description that only lists upside for the cure is dishonest about the
cost.

- More named types or query variants to maintain, one per distinct consumer
  shape, which raises the total surface area even as it lowers the per call
  cost.
- A caller whose needs grow now requires either widening an existing narrow
  projection everywhere it is used, or adding a second, slightly different
  projection, both of which are a real maintenance tax the wide default did
  not impose.
- Over application, narrowing every fetch regardless of measured cost,
  produces exactly the premature optimization failure this entry's non
  applicability list warns against, trading readability for an imaginary
  win.
- A caller specified selection set, GraphQL, OData, or an arbitrary fields
  query parameter, reopens a class of query shape and depth abuse risk that
  a fixed, server defined response shape does not have, covered in
  dimension 17.

## 11. Failure modes and misuse

**The dashboard that got slow as the table grew.** Symptom. A list endpoint
was fast in staging against a thousand rows and became the slowest endpoint
in the system once the production table passed a million rows, with no code
change in between. Cause. The endpoint selects every column of a wide table
to populate a list view that renders three of them, and the per row
overhead that was invisible at low volume becomes the dominant cost as row
count and concurrent request count both grow. Fix. Add an explicit column
projection or a dedicated list DTO, and add a row count scaled load test to
catch the next instance before it reaches production.

**The mobile client burning a user's data plan.** Symptom. Users on a
cellular connection report the app feeling slow or eating data, while the
same screen feels instant on office wifi. Cause. A profile or feed endpoint
returns full resolution image URLs, full biography text, and nested objects
the screen never renders, and the extra bytes are proportionally much more
expensive over a metered, high latency mobile link than over a wired
connection. Fix. A screen specific DTO or a GraphQL query naming only the
rendered fields, plus, for images specifically, a sized thumbnail rather
than a link to the original asset.

**The N+1 that only shows up under real data.** Symptom. A feature page
that renders a list with related data, books and authors, orders and line
items, posts and comments, works fine in a demo with three items and times
out or produces a burst of database connections in production with three
hundred. Cause. A lazy loaded association or a hand written loop issues one
additional query per item instead of one batched query for the whole
collection, exactly the pattern documented in the Rails and EF Core sources
in dimension 9. Fix. Eager load the association, `includes`, `Select`
combined with a join, or `Include` in EF Core, or introduce a batched
loader, and add a test asserting a fixed, small query count for the
operation, since a raw correctness test cannot catch this.

**The wide internal API leaking into a public one.** Symptom. A public API
response accidentally includes internal fields, an audit timestamp, an
internal risk score, a soft delete flag, that a client never asked for and
that were never meant to be public. Cause. The public handler returns the
internal domain entity directly instead of mapping it through an explicit
response DTO, so every internal field the ORM happens to load is exposed by
default. Fix. Introduce an explicit outbound DTO at the API boundary,
treated as a security control in addition to a performance one, see
dimension 17.

**The premature narrowing that nobody asked for.** Symptom. A code review
introduces a bespoke, narrow query for a code path that runs once per user
session against a four column table, adding a new method, a new DTO, and a
new test, for a saving too small to register on any profiler. Cause.
Treating this antipattern as a rule to apply everywhere rather than a
symptom to fix where measured. Fix. Revert to the simple wide accessor,
document why the cost is negligible and measured, and reserve the narrow
projection technique for the hot paths named in dimension 4.

**The cache stampede masquerading as an extraneous fetching fix.** Symptom.
After splitting one wide, well cached entity fetch into several narrow ones
to reduce overfetching, overall load on the data source goes up, not down.
Cause. The wide fetch was a single cache key with a high hit rate. The
narrow fetches are several cache keys, each with its own, lower hit rate
and its own invalidation timing, and the sum of several partial cache
misses can exceed the cost of one whole entity cache hit. Fix. Measure
cache hit rate before and after the split, and prefer narrowing the source
query while keeping a single cache key when the entity is genuinely reused
as a unit.

## 12. Trade-off matrix

Compared against named alternatives across the forces from dimension 3.

| Force | Extraneous fetching (do nothing) | Explicit column projection | GraphQL / selection-set query | Backend for Frontend | DataLoader-style batching |
|---|---|---|---|---|---|
| Developer ergonomics at the call site | Best. One method, no thought required | Medium. One projection per distinct need | Medium to low. Client authors a query per screen | Best for the client, worst for the BFF author | Medium. Loader wiring is one-time cost |
| I/O and transfer cost | Worst. Pays for every unused byte | Low. Pays only for named fields | Low. Pays only for the requested selection | Low. Narrowed once per BFF response | Addresses count of round trips, not byte width |
| Cache friendliness | Poor. Wide entity invalidates on any field change | Good. Narrow, stable shape | Depends on resolver-level caching | Good. One cache-friendly shape per client | Neutral to this force |
| API surface size | Smallest | Grows with each distinct projection | Smallest server surface, richest client expressiveness | One extra service layer per client type | No change to surface, adds a batching layer |
| Solves N+1 specifically | No | No, unless the projection also joins | Only with a batched resolver underneath it | No, unless the BFF itself batches | Yes, this is its specific job |
| Consistency of the read | Strongest, one wide read is one snapshot | Same as source query's isolation | Depends on resolver composition | Depends on BFF composition | Weaker if batched calls span transactions |
| Attack surface at a public boundary | Widest, every field is exposed by default | Narrower, only named fields leave the boundary | Requires depth and complexity limits, see dimension 17 | Narrow by construction per client | Not directly relevant to this force |
| Best fit | Low-traffic, low-volume reads | A known, small set of stable consumer shapes | Many heterogeneous clients with evolving needs | A small number of very different client types | Any collection fetch inside a loop |

Reading of the table. Doing nothing is the right choice until the cost is
measured and worth acting on, per dimension 4. Explicit projection is the
cheapest fix for a known, small set of call sites. GraphQL earns its
complexity when the number of distinct client shapes is large and changes
often, not for a single internal service with one caller. A Backend for
Frontend earns its extra service when a handful of genuinely different
client types exist, not when there is only one client. DataLoader style
batching answers the N+1 sibling specifically and should be paired with,
not substituted for, an explicit projection when both problems are present
at once.

## 13. Related and incompatible patterns

- **N+1 Queries Problem.** The closest sibling, and the one most often
  confused with this entry. Extraneous Fetching is about a single fetch
  carrying more data than needed. N+1 is about one fetch multiplying into
  many. They compose, an ORM that lazily loads a wide entity per item in a
  loop exhibits both at once, and the fixes, projection and batching, are
  complementary rather than interchangeable. See dimension 12 for how the
  two problems interact, and the dedicated `n+1-query` entry in this family.
- **Lazy Loading.** A double edged relationship. Lazy loading is one
  legitimate mitigation for extraneous fetching, deferring a wide fetch
  until a consumer actually asks for it, and it is simultaneously the
  single most common cause of the N+1 sibling once that lazy access happens
  inside a loop. Whether lazy loading helps or hurts in a given codebase
  depends entirely on whether the deferred data is accessed by most
  consumers, favouring eager loading, or by few, favouring lazy loading,
  see dimension 8's discussion of the beware of lazy loading trade.
- **CQRS, Command Query Responsibility Segregation.** Composes cleanly. A
  dedicated, denormalized read model built specifically for a query's needs
  is close to the strongest possible fix for extraneous fetching, because
  the read side never carries fields the write side needed but the query
  side does not. The cost is the same one CQRS always pays, eventual
  consistency between the write model and the read model, and the
  operational overhead of maintaining two models.
- **Backends for Frontends.** Composes at the service level. A BFF is
  structurally the mechanism by which one team can maintain a narrow, per
  client fetch shape without pushing that responsibility onto every
  downstream internal service, so it is a common home for the fix described
  in dimension 8 and dimension 14.
- **Chatty I/O antipattern.** A related but distinct sibling failure in the
  same family of performance antipatterns, covered in this repository's
  `chatty-i-o` entry. Chatty I/O is too many round trips for too little
  data each. Extraneous Fetching is too much data per round trip. A poorly
  designed fix for one can create the other, splitting one wide call into
  many narrow ones trades extraneous fetching for chatty I/O if the split
  goes too far, which is the cache stampede failure mode in dimension 11
  wearing a network hat instead of a cache hat.
- **Caching patterns, cache-aside and read-through.** Interact rather than
  strictly compose or conflict. A well cached wide entity can outperform a
  set of poorly cached narrow ones, per the trade off in dimension 12, so a
  fix for extraneous fetching should always be evaluated against the
  existing cache topology, not designed in isolation from it.
- **Premature Optimization.** Actively conflicts when applied without
  measurement. Treating every wide fetch as a bug to fix regardless of its
  actual cost reproduces the premature optimization failure, adding
  complexity, projections, and DTOs for a saving too small to matter,
  covered explicitly in dimension 4's non-applicability list.

## 14. Refactoring path in and out

Introducing a fix into code that currently overfetches. Ordered steps.

1. Measure first. Identify the actual hot path with a profiler, an APM
   trace, a query log with row and byte counts, or a load test at
   production-like data volume. Do not guess which fetch is expensive.
2. For the identified fetch, list every field the consumer actually reads,
   by reading the consuming code, not by guessing from the entity's shape.
3. Introduce an explicit, named projection, a SQL column list, an ORM
   `select`, `only`, or `values` call, a constructor projection, or a DTO,
   that returns exactly that field list. Do this as a new method or query
   alongside the existing wide one, do not edit the wide accessor in place
   yet, so existing callers keep working while the change is validated.
4. Redirect the identified hot call site to the new narrow accessor. Run
   the test suite, and re-measure the same profiler or trace to confirm the
   byte, row, or query count actually dropped.
5. Check the wide accessor's remaining callers. If every caller has now
   migrated to a narrow projection, the wide accessor can be deleted, which
   is the moment the fix stops being additive and starts reducing the
   surface again. If callers remain that genuinely need the wide shape,
   leave it in place, both accessors coexisting is a correct, stable end
   state, not a code smell.
6. If more than two or three distinct narrow shapes accumulate for the same
   underlying entity, consider whether a query language selection set,
   dimension 8, or a dedicated read model, CQRS, dimension 13, would serve
   the growing set of shapes better than an ever multiplying set of hand
   written DTOs.
7. Add a regression check. For the SQL and ORM case, a test asserting the
   expected column list or a bounded query count. For the N+1 sibling
   specifically, a test asserting a fixed, small number of queries for a
   fixed size input collection, since a correctness only test cannot catch
   a count regression.

Removing the fix when it has stopped earning its place. Signals include a
narrow projection whose consumer's needs have grown to match the wide
entity anyway, or a projection introduced pre-emptively that never became a
genuine hot path.

1. Confirm, by the same measurement discipline as step 1 above, that the
   projection no longer saves enough to matter, either because the
   consumer now needs most of the fields, or because the call site's
   volume never became large enough to matter.
2. Redirect the call site back to the wide accessor.
3. Delete the now unused narrow projection and its dedicated test, this is
   Inline Method applied to a query, see the refactoring family entry.
4. If several projections converge back to the same shape as the wide
   entity, this is also the moment to reconsider whether a dedicated read
   model or query language layer was the wrong tool for a problem that a
   single entity fetch already solved.

## 15. Testing and verification

Extraneous fetching is unusual among antipatterns in that a purely
functional, correctness focused test suite cannot detect it. A test that
asserts the right title and thumbnail were returned passes identically
whether the underlying query fetched two columns or thirty. Verification
requires a second, shape focused axis of testing alongside correctness.

- **Query shape assertions.** Where the ORM or query builder exposes the
  generated SQL, assert on the column list or the row shape directly, for
  example asserting that a generated query's select clause matches an
  expected, minimal column set, or that a projection type carries exactly
  the expected fields and no others.
- **Query count assertions.** For the N+1 sibling specifically, assert a
  fixed, small query count for a fixed size input, using the ORM's own
  query logging or counting middleware, EF Core's interceptor, Django's
  query capture context, or a Rails query assertion helper. A test that
  asserts exactly two queries for ten books and their authors catches a
  regression that a functional test never will.
- **Byte or row count budget tests.** For a network boundary, capture the
  response payload size for a representative fixture and assert it stays
  under a budget, or under a small multiple of the theoretical minimum size
  for the fields actually rendered. This is coarser than a query shape
  assertion but works even when the underlying query engine offers no
  introspection API.
- **Contract tests at an API boundary.** When a DTO is the fix, a contract
  test, a JSON schema check, or a typed client generated from the same
  schema the server publishes, keeps the server's actual response shape and
  the documented, narrow contract from drifting apart over time, which
  matters more here than for most patterns because the whole point of the
  fix is a precise, minimal shape.
- **Load or volume tests at realistic data scale.** Because the antipattern
  is invisible against a small fixture and glaring at production volume,
  per dimension 2 and the first failure mode in dimension 11, a load test
  populated with a production representative row count is the only
  reliable way to surface a regression before it reaches production, and is
  arguably more valuable here than the narrower unit level assertions
  above.

Easier because of a correct fix. Once a narrow DTO or projection exists, a
consumer's test fixtures shrink to exactly the fields under test, and the
mapping between the data layer and the consumer becomes an explicit,
independently testable seam rather than an implicit whatever the entity
happens to carry contract.

Harder because of a correct fix. Every new consumer shape is a new
projection to author, wire, and keep in a fixture, which is a real
authoring cost the wide, one size fits all accessor did not impose, echoing
the change propagation force from dimension 3.

## 16. Observability signals

The antipattern's cost is paid at boundaries that are usually already
instrumented for other reasons, so the observability work is mostly a
question of reading existing signals with this specific failure in mind
rather than adding entirely new instrumentation.

What to record.

- Query row count and, where the driver or ORM exposes it, byte size per
  logical operation, labelled by the query's identity, a named query, a
  route, an endpoint, not aggregated across the whole application.
- Query count per logical request or per unit of work, which is the
  primary signal for the N+1 sibling. A histogram of queries per request
  with a long tail is the clearest production evidence of both extraneous
  fetching and its N+1 cousin at once.
- Response payload size at a service or API boundary, labelled by endpoint
  and, where feasible, by the requested field selection for a GraphQL or
  OData style API, so a shrinking or growing average tells a real story
  about client side usage patterns over time.
- Cache hit rate for the specific cache key or keys involved, before and
  after any change to the fetch's shape, since the cache stampede failure
  mode in dimension 11 is otherwise invisible until it is already degrading
  production.
- Deserialization and mapping time as a distinct span in a trace, separate
  from the raw network or disk I/O span, since a wide row that is cheap to
  read from a warm disk cache can still be expensive to deserialize and map
  into objects, and that cost is easy to miss if only I/O latency is
  traced.

A healthy instance on a dashboard. Query row and byte counts for a given
named query track closely with what the consuming code actually renders or
returns, and stay flat as the underlying table grows, since a correctly
narrow query's cost scales with rows returned, not with the table's total
column width. Queries per request for a list plus detail operation is a
small, fixed number that does not grow with the size of the list.

A failing instance. Bytes or rows fetched for a named query climb steadily
over time with no corresponding change in what the consumer renders, which
usually means new columns were added to the underlying table and the query
was never revisited, a slow, silent form of the antipattern reappearing.
Queries per request scales linearly with the size of a returned collection,
which is the N+1 signature in dimension 9's Rails example, eleven queries
for ten books rather than two. Cache hit rate drops after a fetch was split
into narrower pieces, which is the stampede failure mode. Deserialization
time as a fraction of total request time creeps upward even as raw I/O
latency stays flat, pointing at growing unused payload rather than a
slower disk or network.

## 17. Security and privacy implications

Unlike a purely internal structural pattern, extraneous fetching has a real
and frequently underestimated security dimension, because the fields that
are fetched but not used are, by definition, fields that were exposed
somewhere along the path even though nobody needed them.

**Accidental data exposure at an API boundary.** The most direct
implication. A handler that maps an internal entity straight onto an
outbound response, rather than through an explicit DTO, exposes every field
the entity happens to carry, including fields never meant to leave the
service, an internal risk score, a soft delete flag, a cost basis, an
internal audit column, a password hash column that was fetched incidentally
as part of a wide user row. This is the exact failure mode named in
dimension 11's fourth entry, and it means the fix for this antipattern,
introducing an explicit narrow projection or DTO at the boundary, is
frequently also a genuine security fix, not merely a performance one. This
is engineering judgement grounded in dimension 11's own failure mode,
restated here because the security angle deserves its own explicit callout
rather than being buried as a performance footnote.

**Over-privileged reads widen the blast radius of a compromised credential
or a SQL injection.** A wide select executed through a service account
that only ever needs three columns means any compromise of that account, or
any injection point that manages to widen the query further, has access to
every column the table holds, not only the three actually used. A narrow,
explicit column list is a small but real instance of least privilege
applied at the query level, not only at the database role level.

**Client-specified selection sets widen the attack surface at the GraphQL
or OData layer specifically.** Allowing a caller to name its own
projection, the very mechanism that fixes extraneous fetching at a public
API boundary, reopens two well known abuse classes if left unbounded,
deeply nested queries that multiply server side work far beyond what the
request size suggests, and field level access that bypasses a coarser,
resource level authorization check that assumed a fixed response shape. Any
GraphQL or OData style fix for this antipattern must pair the selection
flexibility with query depth limits, cost based rate limiting, and field
level authorization, or it trades one problem for a worse one. This is
engineering judgement grounded in the well documented existence of these
abuse classes in GraphQL server implementations generally, not a claim
about any single named product.

**Logging and tracing widen the exposure, not only the response.** An APM
trace or a query log that captures full query results for debugging can
itself become the leak, if the wide fetch pulled sensitive fields the
application code never used but the observability pipeline dutifully
recorded anyway. Narrowing the fetch, per this entry's fix, also narrows
what an overly verbose logging or tracing configuration can accidentally
retain.

On raw storage and network encryption the pattern is neutral, narrowing a
fetch does not change whether data at rest or in transit is encrypted, that
is a separate, orthogonal control that should already be in place
regardless of how wide or narrow any given query is.

## 18. References

1. Microsoft. EF Core documentation, Efficient Querying, sections Project
   only properties you need and Beware of lazy loading.
   https://learn.microsoft.com/en-us/ef/core/performance/efficient-querying
   Verified 2026-08-02. Source for the projection example, fetching four
   unused columns to read one, the generated SQL before and after the fix,
   and the named N+1 lazy loading warning in dimensions 1, 9, and 11.
2. Django Software Foundation. Django 5.2 documentation, QuerySet API
   reference, `select_related()`.
   https://docs.djangoproject.com/en/5.2/ref/models/querysets/#select-related
   Verified 2026-08-02. Source for the two query versus one query example
   and the deluge of database queries framing used in dimension 9.
3. Ruby on Rails. Active Record Query Interface guide, section Eager
   Loading Associations.
   https://guides.rubyonrails.org/active_record_querying.html#eager-loading-associations
   Verified 2026-08-02. Source for the eleven queries versus two queries
   worked example cited in dimension 9 and used to illustrate the N+1
   sibling's dynamics in dimension 7.

## Code examples

Three languages, each idiomatic for a different layer where this antipattern
commonly appears. TypeScript shows the fix at an ORM-adjacent, in-memory
data layer, the shape used inside a Node service. Python shows a SQL-facing
fix using explicit column selection, the shape most SQL and ORM code takes.
Go shows the fix applied to an in-process struct-shaped store, since Go has
no ORM in its standard library and the pattern there is usually a
hand-written struct projection rather than a query-builder call. Java and
Rust are omitted from the runnable set for this entry specifically because
the pattern in both is the same struct or record projection idea already
demonstrated in Go and TypeScript, and a third near-identical rendering
would add length without adding a genuinely new technique. The dimension 9
and dimension 12 discussion of EF Core, a .NET rather than Java technology,
and Django already covers the ORM-facing variant these two languages would
otherwise illustrate.

### TypeScript

```typescript
interface UserRecord {
  id: string;
  displayName: string;
  avatarUrl: string;
  email: string;
  billingAddress: string;
  passwordHash: string;
  preferences: Record<string, unknown>;
}

// Antipattern. Fetches the whole record for a list that only renders two fields.
function fetchUserFull(store: Map<string, UserRecord>, id: string): UserRecord {
  const record = store.get(id);
  if (!record) throw new Error("not found");
  return record;
}

// Fix. An explicit, named projection carrying only what a list view renders.
interface UserListItem {
  id: string;
  displayName: string;
  avatarUrl: string;
}

function fetchUserListItem(
  store: Map<string, UserRecord>,
  id: string
): UserListItem {
  const record = store.get(id);
  if (!record) throw new Error("not found");
  return { id: record.id, displayName: record.displayName, avatarUrl: record.avatarUrl };
}

const store = new Map<string, UserRecord>([
  [
    "u1",
    {
      id: "u1",
      displayName: "Ada",
      avatarUrl: "/a.png",
      email: "ada@example.com",
      billingAddress: "1 Analytical Engine Way",
      passwordHash: "opaque",
      preferences: { theme: "dark" },
    },
  ],
]);

const item = fetchUserListItem(store, "u1");
console.log(item);
```

### Python

```python
import sqlite3


def setup(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE articles (
            id INTEGER PRIMARY KEY,
            title TEXT,
            thumbnail_url TEXT,
            body TEXT,
            author_bio TEXT
        )
        """
    )
    conn.execute(
        "INSERT INTO articles VALUES (1, 'Title', '/t.png', 'a very long body ' * 500, 'a long bio ' * 200)"
    )
    conn.commit()


def fetch_full_row(conn: sqlite3.Connection, article_id: int) -> sqlite3.Row:
    # Antipattern. Pulls body and author_bio even though a list view needs neither.
    cur = conn.execute("SELECT * FROM articles WHERE id = ?", (article_id,))
    return cur.fetchone()


def fetch_list_projection(conn: sqlite3.Connection, article_id: int) -> sqlite3.Row:
    # Fix. Names exactly the two columns a list view renders.
    cur = conn.execute(
        "SELECT title, thumbnail_url FROM articles WHERE id = ?", (article_id,)
    )
    return cur.fetchone()


if __name__ == "__main__":
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    setup(conn)

    wide = fetch_full_row(conn, 1)
    narrow = fetch_list_projection(conn, 1)

    print("wide row bytes (approx)", sum(len(str(v)) for v in wide))
    print("narrow row bytes (approx)", sum(len(str(v)) for v in narrow))
    print("narrow columns", narrow.keys())
```

### Go

```go
package main

import "fmt"

type Article struct {
	ID           int
	Title        string
	ThumbnailURL string
	Body         string
	AuthorBio    string
}

// Antipattern. Returns the whole struct for a list view that renders two fields.
func fetchArticleFull(store map[int]Article, id int) Article {
	return store[id]
}

// Fix. A narrow, purpose-built projection type.
type ArticleListItem struct {
	Title        string
	ThumbnailURL string
}

func fetchArticleListItem(store map[int]Article, id int) ArticleListItem {
	a := store[id]
	return ArticleListItem{Title: a.Title, ThumbnailURL: a.ThumbnailURL}
}

func main() {
	store := map[int]Article{
		1: {
			ID:           1,
			Title:        "Title",
			ThumbnailURL: "/t.png",
			Body:         "a very long body repeated many times",
			AuthorBio:    "a long biography repeated many times",
		},
	}

	full := fetchArticleFull(store, 1)
	narrow := fetchArticleListItem(store, 1)

	fmt.Printf("wide struct fields fetched %d\n", 5)
	fmt.Printf("narrow struct fields fetched %d\n", 2)
	fmt.Printf("narrow projection %+v\n", narrow)
	_ = full
}
```

## Toolchain notes

TypeScript was type-checked with `npx tsc --noEmit` against the sample above
and compiles cleanly. Python was run directly with `python3` and produced
the expected output, a smaller byte count and a two-column key list for the
narrow projection versus the five-column wide row. Go was run with `go run`
and produced the expected struct output. Java and Rust samples were not
authored for this entry, per the reasoning given in the Code examples
section, and no claim is made about them beyond that reasoning.
