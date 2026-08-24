---
name: Chatty I/O
slug: chatty-i-o
family: 18-anti-patterns
category: Architectural
aliases: [Chatty Interface, Chattiness, N+1 Query Problem (specific case), Excessive Round Tripping]
first_described: "Microsoft patterns and practices, Azure Architecture Center, 2017"
maturity: established
related: [distributed-monolith, extraneous-fetching, boat-anchor, entity-service]
incompatible_with: []
verified: 2026-08-04
---

# Chatty I/O

## 1. Name, aliases, and lineage

The canonical name for this anti-pattern is Chatty I/O, and the fullest written
description of it under that exact name lives in the Microsoft Azure
Architecture Center's antipatterns catalog, "Chatty I/O antipattern"
([learn.microsoft.com](https://learn.microsoft.com/en-us/azure/architecture/antipatterns/chatty-io/),
verified 2026-08-04). That page opens with the framing that matters. "The
cumulative effect of a large number of I/O requests can have a significant
impact on performance and responsiveness." The page is dated 2017-06-05 in its
metadata and is still maintained by Microsoft as of the verification date, with
worked examples in a relational-database client, a REST client, and a file
writer.

The idea itself is older than that one page. Two much older sources describe
the same failure by different names. Martin Fowler's Patterns of Enterprise
Application Architecture catalog entry for Data Transfer Object states the
underlying reasoning directly. when a call crosses a process or network
boundary, "each call to it is expensive. As a result you need to reduce the
number of calls, and that means that you need to transfer more data with each
call" (Martin Fowler, "Data Transfer Object,"
[martinfowler.com/eaaCatalog/dataTransferObject.html](https://martinfowler.com/eaaCatalog/dataTransferObject.html),
verified 2026-08-04). Fowler's book, Patterns of Enterprise Application
Architecture, Addison-Wesley, 2002, gives that same reasoning as the design
force behind the Remote Facade and Data Transfer Object patterns, both built
specifically to counter a chatty remote interface.

At the database layer the same failure has its own long-standing folk name,
the N+1 query problem, which the Microsoft page names explicitly in its
first worked example. "sometimes an O/RM can mask the problem, if it
implicitly fetches child records one at a time. This is known as the N+1
problem." N+1 describes one specific, extremely common cause of chatty I/O,
querying a parent row once and then querying a child table once per parent
row returned, rather than one specific pattern of its own, and this entry
treats it as a named instance of Chatty I/O rather than a separate anti-pattern.

Chattiness is also the everyday word engineers use in conversation before they
know the formal catalog name, "this API is chatty," "that ORM is chatty," and
the catalog name simply gives that word a documented shape with a documented
fix. Some teams also call the specific REST-API instance of it Excessive Round
Tripping or a Chatty Interface, both descriptive rather than formally
catalogued names for the same failure.

## 2. Problem and context

Chatty I/O appears the moment a piece of code that used to run against
in-process memory starts running against something on the far side of a
boundary that has real per-call cost. a network socket, a database
connection, a disk file, an interprocess pipe. The code was written the way
you would naturally write it against an in-memory object graph. iterate over
a parent, walk into each child, ask a question, move to the next child. That
shape is free in memory. Across a boundary, every one of those questions
becomes a full round trip carrying its own connection setup, its own
serialization, its own network latency, and its own server-side dispatch cost,
even when the actual payload being asked for is a handful of bytes.

The Microsoft catalog entry frames the mechanism plainly. "Network calls and
other I/O operations are inherently slow compared to compute tasks. Each I/O
request typically has significant overhead, and the cumulative effect of
numerous I/O operations can slow down the system." The overhead is not the
payload, it is everything that has to happen once per call regardless of
payload size, and that per-call tax is what a naive loop pays over and over.

The context in which this becomes a real production problem, rather than a
theoretical inefficiency, has three recognizable shapes, and each one shows
up in the Microsoft page's worked examples verbatim.

The first shape is an object-relational mapper walking a graph one edge at a
time. Fetch the parent row with one query, then for every child collection on
that parent, fire a second query per parent instance, and if that child has
its own children, fire a third query per child instance. This is the N+1
case, and the ORM's job of hiding SQL from the developer is exactly what
hides the multiplying query count too.

The second shape is a remote API that was designed the way you would design a
class's public interface, with one method per property, because that
mirrors object-oriented instinct even though the interface is remote. Every
property read that would be a free field access in memory becomes its own
HTTP request when the object lives on a server. Fowler names this instinct
directly as the trap that Remote Facade and Data Transfer Object exist to
correct, treating a remote object as if it were a local one.

The third shape is disk file I/O done as many small opens, writes, and closes
instead of one buffered pass. Opening a file, seeking, and closing it carries
operating-system overhead that is trivial once and expensive thousands of
times, and small repeated writes additionally fragment the file on disk,
degrading later reads too.

All three shapes share one root context. the code that generates the calls is
written with no visibility into, and often no interest in, how many round
trips it is producing, because the loop that generates the calls and the cost
of a single call are conceptually separate concerns to the person writing the
loop.

## 3. Forces

Chatty I/O sits at a genuine tension point between several pressures, and it
is worth being honest that fixing chattiness is not free. It trades one set
of costs for another, and the pattern this entry describes is what happens
when that trade is made badly, or is never made at all.

Round-trip latency versus payload size. Every round trip pays a fixed
cost, TCP or TLS handshake amortization, connection pool acquisition, request
serialization, server dispatch, response deserialization, before a single
byte of the actual answer is transmitted. Bundling many small requests into
one larger request replaces N fixed costs with one fixed cost plus a larger
but still bounded payload. The Microsoft catalog page states the trade
outright in its Considerations section. "The first two examples make fewer
I/O calls, but each one retrieves more information. You must consider the
tradeoff between these two factors." Fewer calls is not automatically better
if each call now returns far more data than any single caller actually needs,
which is the sibling anti-pattern Extraneous Fetching, also catalogued by
Microsoft, waiting on the other side of an overcorrected fix.

Freshness versus batching. Batching several logical writes into one
physical write, or several logical reads into one physical read, means the
individual items inside that batch are read or written together rather than
independently. A write buffered in memory and flushed periodically is
vulnerable to loss if the process dies before the flush, which the Microsoft
page notes directly. "If you buffer data in memory before writing it, the
data is vulnerable if the process crashes." Any fix for chattiness on the
write side has to reckon with this durability cost.

Coupling and interface shape. A chatty interface with one method per
field is, in one sense, a loosely coupled interface, a caller can ask for
exactly the one thing it wants and nothing else. Collapsing that into one
coarse call that returns everything couples every caller to a single larger
contract and to the cost of transmitting fields it may never read. This is
the same tension GraphQL was built to resolve on the web, letting a client
declare the exact shape of data it wants inside a single request rather than
choosing between many narrow REST endpoints and one wide one, described on
Wikipedia's GraphQL page as letting a GraphQL query define the exact shape
of the data needed by the client, with GraphQL returning only the data
that's explicitly requested
([en.wikipedia.org/wiki/GraphQL](https://en.wikipedia.org/wiki/GraphQL),
verified 2026-08-04).

Operability and diagnosability. Many small, uniform, individually cheap
requests are, ironically, easier to reason about one at a time in a debugger
or a log line than a small number of large batched requests whose failure
modes are aggregate and partial. A batched call can partially succeed,
carrying both successes and failures in one response, and the caller has to
be written to expect and unwind that partial state, which the DynamoDB
BatchGetItem contract makes explicit through its UnprocessedKeys field,
discussed under production uses below. Chattiness trades this partial-
failure complexity away in exchange for the volume-of-calls problem, and
removing chattiness reintroduces partial failure as a first-class concern the
caller must now handle.

Team topology and ownership. A chatty client-server relationship where the
server exposes many fine-grained endpoints often reflects an org boundary,
one team owns the data source and exposes it generically, another team owns
the consuming application and cannot change the server's contract. The fix
for chattiness frequently requires either the server team to add a new
coarse-grained endpoint tailored to a caller's actual need, or the client team
to introduce an aggregation layer of its own, and which side absorbs that
work is as much an organizational decision as a technical one.

This entry's judgment. of these forces, round-trip latency versus payload
size is almost always the dominant one in practice, because the fixed
per-call overhead compounds multiplicatively with scale, more concurrent
users, more rows, in a way that raw payload size, which grows only linearly
with the amount of real data, does not.

## 4. Applicability and non-applicability

Recognizing Chatty I/O as the diagnosis, and recognizing when a fix for it
does not apply, are both required. Reaching for batching everywhere is its
own anti-pattern, covered under Extraneous Fetching and under this entry's
failure modes below.

Chatty I/O is present, and worth fixing, when.

- A single logical operation issued by a caller is implemented as an
  unbounded or data-dependent number of physical I/O calls, most visibly a
  loop that issues one query, request, or file operation per item in a
  collection whose size the caller does not control.
- Profiling or an APM trace shows a small number of logical user operations
  producing tens or hundreds of physical calls to the same downstream
  resource, the exact symptom the Microsoft page's diagnosis walkthrough
  demonstrates, where one GetProductsInSubCategoryAsync call issued 45 SQL
  SELECT statements.
- The I/O target is remote or crosses a real boundary, network, disk,
  another process, so the per-call overhead is measured in single-digit
  milliseconds or worse, not nanoseconds. The pattern's cost model assumes a
  boundary with real fixed overhead; it does not apply to in-process function
  calls.
- The number of calls scales with the size of the caller's input, N rows,
  N fields, N files, rather than being a small, bounded constant regardless
  of input size.

Chatty I/O does not apply, and batching would be the wrong move, when.

- The calls are already bounded and small in count, for example a UI screen
  that legitimately needs three or four independent pieces of data from three
  or four independently cacheable, independently rate-limited services.
  Combining them into one artificial aggregate call couples three unrelated
  concerns for no latency win worth the coupling.
- The caller genuinely needs only a small subset of a large record's fields
  most of the time. Microsoft's own Considerations section names this
  directly. "it might turn out that clients often need just the user name. In
  that case, it might make sense to expose it as a separate API call." Fixing
  a real chattiness problem by fetching an entire wide record on every call
  produces Extraneous Fetching, a distinct, related anti-pattern.
- The operation is inherently a streaming or incremental one, where the
  caller wants to begin acting on the first result before the last result has
  arrived, for example an interactive autocomplete or a live tail of a log.
  Forcing a single batched call here trades interactivity for a marginal
  reduction in call count, which is the wrong trade for that use case.
- Batching would require holding a write lock, a transaction, or a large
  buffer open for materially longer than the individual small operations
  would have held it, especially across multiple independent data stores
  where Microsoft's own guidance is to prefer eventual consistency over one
  long-held cross-store transaction.
- The system already sits behind a boundary with negligible per-call cost,
  most notably a same-process function call or a same-host Unix domain
  socket with connection reuse, where the fixed overhead this pattern exists
  to amortize is small enough that batching adds real complexity for
  negligible measured benefit.

## 5. Structure

Chatty I/O is a behavioral, cross-cutting anti-pattern rather than a
structural one built from named classes, so its participants are roles in a
call graph rather than fixed types.

- The Caller. The code that owns a single logical intent, for example
  "show me this product subcategory with pricing," and that translates that
  one intent into physical I/O calls. In the anti-pattern, the caller is also
  the place where the translation from one intent to many calls happens, most
  often inside a loop.
- The Boundary. The real interface with non-trivial fixed per-call cost.
  a database connection and query planner, an HTTP endpoint and its network
  path, a filesystem handle. The boundary is what turns an otherwise free
  iteration into an expensive one; it is not itself part of the anti-pattern,
  it is the resource the anti-pattern abuses.
- The Data Source. The system on the far side of the boundary that
  actually answers each call, a relational database, a remote service, a
  file on disk. In a healthy design this is exactly one call away from
  answering the caller's whole intent; in the chatty version it is called
  once per item the caller is iterating over.
- The fix's participant, a Batching or Aggregation Point. Whichever
  component absorbs the translation from many small requests into one larger
  one, an ORM eager-load directive, a purpose-
  built coarse endpoint, a Backend for Frontend layer, a Data Transfer
  Object assembler, or a client-side request coalescer. This participant
  does not exist in the anti-pattern itself; it is what dimension 14,
  refactoring path, introduces to remove the anti-pattern.
- The Consistency and Failure Boundary. Wherever the batched or original
  chatty operation's partial-failure semantics are decided, whether one
  failed item aborts the whole call, is retried individually, or is silently
  skipped. In the anti-pattern's naive form this boundary is implicit,
  usually "the whole loop throws on the first failed call." A correct fix
  makes this boundary explicit, as DynamoDB's UnprocessedKeys response
  field does.

## 6. ASCII structure diagram

```
CHATTY, the anti-pattern

Caller       Boundary       Data Source
------       --------       -----------
 |
 | for each of N items
 |------------>|-- call 1 -->  [ answer 1 ]
 |             |<- reply 1 --
 |             |-- call 2 -->  [ answer 2 ]
 |             |<- reply 2 --
 |             |     ...
 |             |-- call N -->  [ answer N ]
 |<------------|<- reply N --
 |
 N round trips, N x fixed overhead paid,
 payload scales with N.


CHUNKY, after the fix

Caller    Aggregation Point    Boundary    Data Source
------    -----------------    --------    -----------
 |               |
 | one intent -->|
 |               |-- single batched
 |               |   or joined call -->  [ all N answers ]
 |               |<---- single reply ---
 |<--------------|
 |
 1 round trip, 1 x fixed overhead paid,
 payload scales with N, round trip count
 no longer scales with N.
```

## 7. Dynamics

The runtime dynamics of the anti-pattern are exactly the sequence Microsoft's
worked example walks through. one call establishes a parent context, then a
loop over the results of that call issues one further call per element.

```text
Chatty sequence, N products in a subcategory

Caller                    ORM or HTTP client            Data source
  |                              |                             |
  |-- get subcategory ---------->|--- SELECT subcategory ----->|
  |<------------------------------|<---------- 1 row -----------|
  |                              |
  |-- get products in it ------->|--- SELECT products --------->|
  |<------------------------------|<---------- N rows ----------|
  |                              |
  |  for product in products     |
  |    get price history ------->|--- SELECT price history ---->|
  |<------------------------------|<---------- rows ------------|
  |    repeated N times          |
  |                              |
  Total calls, 2 plus N          (Microsoft's traced example measured N = 45
                                  SELECT statements for a real subcategory)
```

The fixed dynamic, after applying the refactoring path in dimension 14.

```text
Chunky sequence, same intent

Caller                    ORM or HTTP client            Data source
  |                              |                             |
  |-- get subcategory,           |                             |
  |   eager loaded with          |                             |
  |   products and price         |--- one JOIN query --------->|
  |   history --------------------|                             |
  |<------------------------------|<---- 1 result set ----------|
  |                              |
  Total calls, 1
```

Under load, this dynamic difference is not linear, it is the difference
between latency that grows with the number of concurrent callers times N
round trips each, versus latency that grows with the number of concurrent
callers times one round trip each. Microsoft's own load test numbers make
this concrete. the chatty version processed an average of 410 requests per
minute with a response time in the tens of seconds at 1,000 concurrent users;
the fixed version, tested against the identical deployment and load profile,
processed an average of 3,970 requests per minute with response times of 5
to 6 seconds at the same 1,000 users.

## 8. Implementation variants

The concrete shape of the fix depends on which boundary is chattering, and
each boundary has its own idiomatic aggregation mechanism.

ORM eager loading. Most O/RM layers offer a directive that turns an
implicit per-row lazy fetch into one query with a join or a second batched
query, expressed as `.Include(...)` in Entity Framework, shown directly in
Microsoft's fixed example as `Include("Product.ProductListPriceHistory")`,
as `JOIN FETCH` in JPQL for Hibernate and JPA, or as `select_related` and
`prefetch_related` in Django's ORM. The trade-off across these variants is
identical. a JOIN-based eager load returns one flat, possibly duplicated
result set in one round trip; a batched second-query eager load, fetching
all children for all parents already loaded in one extra query keyed by the
parent IDs, avoids row duplication at the cost of a second, still single,
round trip. Both variants beat N+1; choosing between them is a payload-size
versus row-duplication trade, not a chattiness trade.

Coarse-grained REST endpoints. Where the chatty caller is a client of an
HTTP API with one endpoint per field or per sub-resource, the fix is to add
an endpoint shaped around what the caller actually needs in one request,
exactly Microsoft's fixed `UserController.GetUser(id)` example. This
sacrifices some of the granular cacheability of the narrow endpoints for the
round-trip win, and is the origin of the Backend for Frontend pattern, a
purpose-built aggregation service per class of client, when different
callers of the same underlying data genuinely need different shapes.

Query languages that let the client declare shape. GraphQL is the
industry's most widely adopted general answer to exactly this trade-off,
letting one HTTP request carry a client-declared shape spanning what would
otherwise be several REST calls, described on its Wikipedia entry as
enabling clients to declare the exact shape of data they need in a single
query. The implementation cost is a schema and resolver layer the server
team must build and maintain, and, notoriously, a fresh N+1 problem inside
resolvers unless the server uses a batching mechanism such as Facebook's
DataLoader to coalesce resolver calls for the same field across sibling
nodes in one GraphQL query into one underlying batched fetch.

Bulk or batch write and read APIs at the data-store level. Where the
boundary is a managed data store's own network API, the store itself
typically exposes an explicit batch primitive, `BatchGetItem` and
`BatchWriteItem` in Amazon DynamoDB, detailed in dimension 9, multi-row
`INSERT ... VALUES (...), (...), (...)` in SQL databases, or pipelining in
Redis. The implementation variant here is purely a client-side change,
replace a loop of N single-item calls with one call carrying an array of N
keys or N rows, using whatever batch shape the store's SDK exposes.

Binary RPC with multiplexed connections. gRPC uses Protocol Buffers for
request and response serialization and lets a client application call a
method on a server application on a different machine as if it were a local
object, per its own introduction docs
([grpc.io/docs/what-is-grpc/introduction/](https://grpc.io/docs/what-is-grpc/introduction/),
verified 2026-08-04). Its streaming RPC modes, client-streaming,
server-streaming, and bidirectional-streaming, all part of the gRPC service
definition surface, let a single logical operation send or receive many
individual messages over one already-open connection rather than opening a
fresh connection per message, addressing the connection-setup portion of the
chattiness overhead independently of whether the payload itself is batched.

In-memory buffering with a durable flush. For file and queue writes,
Microsoft's fixed example buffers a list of objects in memory and writes the
whole list in one pass, noting the durability trade explicitly and
recommending an external durable queue, naming Azure Event Hubs, when the
write rate is bursty or the in-memory buffer's crash exposure is
unacceptable.

TCP-level coalescing, independent of the application. Nagle's algorithm
operates one layer below all of the above, inside the TCP stack itself,
coalescing small outgoing segments so that new outgoing data is buffered
rather than sent immediately whenever any previously transmitted data on
the connection remains unacknowledged
([en.wikipedia.org/wiki/Nagle%27s_algorithm](https://en.wikipedia.org/wiki/Nagle%27s_algorithm),
verified 2026-08-04). This variant fixes small-packet overhead transparently
to the application, at the cost of added latency, which is why latency-
sensitive protocols disable it with the `TCP_NODELAY` socket option rather
than rely on it.

## 9. Known production uses

Amazon DynamoDB's BatchGetItem and BatchWriteItem APIs. DynamoDB's own
API reference documents `BatchGetItem` as an operation that returns the
attributes of one or more items from one or more tables, accepting up to
100 keys and up to 16 MB of data in a single call, explicitly to replace a
loop of individual `GetItem` calls
([docs.aws.amazon.com, API_BatchGetItem](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_BatchGetItem.html),
verified 2026-08-04). The response contract also documents the partial
failure boundary named in dimension 5. it returns an `UnprocessedKeys` map
in the same form as `RequestItems`, so the value can be provided directly to
a subsequent `BatchGetItem` operation, which is the API's own answer to the
partial-failure force under dimension 3.

GraphQL at Meta, formerly Facebook. Facebook began developing GraphQL
internally in 2012 and released a draft specification and open-source
reference implementation in 2015, according to Wikipedia's GraphQL entry,
with the explicit design goal of letting a client's query define the exact
shape of the data needed in one request rather than issuing one REST call
per resource. It has since been adopted widely enough that it is maintained
by the GraphQL Foundation as an independent specification, not solely a
Facebook-internal tool, and is used as the query layer for numerous public
APIs, GitHub's v4 API and Shopify's Admin API among the most cited public
adopters, precisely to let mobile and web clients collapse several REST
round trips into one.

gRPC, originally Google, now a CNCF graduated project. gRPC's own
documentation states that it lets a client application directly call a
method on a server application on a different machine as if it were a local
object, using Protocol Buffers to define the service contract
([grpc.io/docs/what-is-grpc/introduction/](https://grpc.io/docs/what-is-grpc/introduction/),
verified 2026-08-04). Its streaming modes are used in production
specifically to avoid repeated connection setup for chains of related calls,
for example a client streaming many small update messages, or a server
streaming a long result set incrementally, over one already-negotiated
connection rather than one connection per message.

Nagle's algorithm in the Berkeley sockets TCP/IP stack. Nagle's
algorithm, described in RFC 896 and named for John Nagle, is implemented as
a default behavior inside the TCP stack that ships with essentially every
general-purpose operating system's Berkeley-sockets-derived networking
implementation, and is the reason small, frequent application-level writes
to a TCP socket, one keystroke per Telnet packet in the algorithm's original
motivating example, do not each produce a separate 40-byte-overhead packet
on the wire by default. Its ubiquity, and the corresponding ubiquity of the
`TCP_NODELAY` socket option every major networking library exposes to
disable it, is itself the evidence that chattiness at the packet level is a
universally recognized, universally mitigated production concern rather
than a niche one.

## 10. Consequences

Positive consequences of recognizing and fixing Chatty I/O, drawn directly
from Microsoft's own measured before-and-after.

- Substantially reduced end-to-end latency for the caller. Microsoft's load
  test measured a drop from near-a-minute response times at 1,000 concurrent
  users down to 5 to 6 seconds for the identical logical operation after the
  fix.
- Substantially higher throughput for the same infrastructure. the same
  test measured roughly a 9.7x increase in requests served per minute, 410
  to 3,970, on the identical deployment.
- Lower connection and resource pressure on the shared downstream resource,
  since each connection or file handle now serves one larger unit of work
  instead of being acquired and released once per item.
- A single point where the aggregation happens, which becomes a natural
  place to add caching, since one coarse call is easier to key a cache entry
  on than N narrow ones.

Negative consequences, both of leaving the anti-pattern in place and of an
overcorrected fix, are equally real and belong in the same list because a
reader deciding whether to act needs both.

- Left in place, chattiness degrades non-linearly under load rather than
  gracefully, because the fixed per-call overhead multiplies against both N
  items and concurrent-caller count simultaneously, which is exactly why the
  symptom often first appears in production under real traffic rather than
  in a developer's local, single-user testing.
- A batched or joined fix increases the payload size of each individual
  call, and a caller that only ever needed a fraction of that payload now
  pays for the rest of it every time, the Extraneous Fetching trade named
  explicitly in Microsoft's Considerations section.
- Batched writes introduce a data-loss window between when data is accepted
  into a buffer and when that buffer is actually flushed to durable storage,
  a real risk this entry's Microsoft source names directly.
- Batched calls introduce partial-failure semantics, some items in the batch
  succeed while others fail, that a fully independent, individually called
  loop never had to express, and callers written against the old chatty
  contract will not correctly handle a new batched contract's partial
  results without new code.
- An aggregation layer, whether a Backend for Frontend, a DTO assembler, or
  a GraphQL resolver graph, is new code with its own bugs, its own tests,
  and its own deployment lifecycle that did not exist before the fix.

## 11. Failure modes and misuse

Symptom. A user-facing operation feels instant with one item of test
data locally but times out or degrades sharply in production. Cause. The
number of physical calls the operation issues scales with the size of a
collection, rows, users, or files, that is small in development and large in
production, so the fixed-overhead multiplication that dimension 3 describes
only becomes visible once N is large. Fix. Load test with production-
representative data volumes before shipping, and specifically trace the
number of downstream calls per logical operation, not just its wall-clock
time on a small dataset, exactly the sequence Microsoft's own how-to-detect
section walks through, monitor for poor response times in production, then
load test, then gather telemetry on the data-access calls made per operation.

Symptom. An ORM's lazy-loading proxy throws a lazy-initialization
exception, or its equivalent, once code that touched a lazy relationship has
left the transactional or session scope it was loaded in. Cause. A
developer disabled or worked around eager loading to fix what looked like a
performance problem, without realizing lazy loading inside the correct
session scope was never the chatty part, the missing eager-load directive on
the specific access path was. Fix. Diagnose with the ORM's own SQL logging
first, count the actual queries issued for the operation, and add the join
or batched fetch on precisely the access path the trace shows firing
repeatedly, rather than blanket-disabling lazy loading everywhere, which
trades chattiness for the opposite failure, Extraneous Fetching on every
operation whether it needed the extra data or not.

Symptom. After fixing chattiness by introducing one enormous aggregate
endpoint that returns everything every caller might ever want, p95 latency
on the simplest, most frequent caller of that endpoint gets worse, not
better, even though total round trips across the system went down. Cause.
This is Extraneous Fetching, the named sibling anti-pattern Microsoft's own
page points to directly, over-correcting for chattiness by building one
endpoint so coarse that its typical caller now transmits and deserializes a
large payload it never reads most of. Fix. Microsoft's own guidance applies
here directly. partition the information for an object into two chunks,
frequently accessed data and less frequently accessed data, keeping the
frequent path narrow and the infrequent, expensive path separate, rather
than one endpoint that serves every caller identically.

Symptom. A batched write API call succeeds with an HTTP 200 or a
successful SDK return, but some of the items the caller thought it wrote are
missing on the next read. Cause. The caller ignored the batch API's
partial-failure signal, DynamoDB's `UnprocessedKeys`, and treated the whole
batch call as an atomic all-or-nothing operation, which its own reference
documentation explicitly says it is not, stating that if at least one of the
items is successfully processed, `BatchGetItem` completes successfully,
while returning the keys of the unread items in `UnprocessedKeys`. Fix.
Always check the batch response's partial-failure field and retry, with
exponential backoff as DynamoDB's own documentation recommends rather than
an immediate retry, until it is empty, or surface the unprocessed subset to
the caller explicitly rather than silently discarding it.

Symptom. A GraphQL API, adopted specifically to eliminate REST
chattiness, is now itself producing an N+1 storm of database queries per
request, one per resolved field per returned node. Cause. GraphQL resolves
each field of each node independently by default, so a query that returns a
list of N parent nodes and asks for one child field on each re-creates the
exact N+1 shape at the resolver layer that the schema change was meant to
remove at the HTTP layer, the recognized failure mode that motivated
Facebook's DataLoader utility in the first place. Fix. Batch and cache
resolver-level data fetches within the scope of a single incoming request,
coalescing sibling resolver calls asking for the same underlying data source
into one batched fetch, rather than assuming the API's transport-layer fix,
one HTTP request, automatically implies the storage layer beneath it is no
longer chatty.

## 12. Trade-off matrix

Compared against the two named alternatives that most often get chosen when
a team decides to act on Chatty I/O, and against doing nothing.

| Force | Leave it chatty | Eager-load or bulk-batch API | GraphQL or Backend for Frontend |
|---|---|---|---|
| Round trips per operation | Scales with N | 1, or a small constant | 1 |
| Payload per round trip | Small per call, N calls total | Larger, sized to real need | Larger, sized to client's declared shape |
| Implementation cost | None, status quo | Low, usually a one-line ORM or SDK change | Higher, a new schema, resolver, or aggregation service |
| Risk of over-fetching | None, each call is minimal by construction | Moderate, if the join or batch grabs unneeded columns | Low by design, but only if resolvers are individually correct |
| Partial-failure handling | Simplest, one item fails, one call fails | Must handle a batch's partial success explicitly | Must handle per-field resolver errors within one response |
| Coupling introduced | Lowest, each caller asks for exactly what it wants | Moderate, callers now share one join or batch shape | Server owns a schema every client is coupled to |
| Best fit | Genuinely bounded, small, independent calls | Data-store-local aggregation, ORM graphs, batch write and read APIs | Multiple heterogeneous clients needing different shapes of the same data |

## 13. Related and incompatible patterns

Extraneous Fetching, anti-pattern, Microsoft catalog, closely related,
opposite direction. This is the failure mode a naive fix for Chatty I/O
lands in when it over-corrects, retrieving more data per call than the
caller needs. The two anti-patterns are best understood as opposite ends of
one dial, calls-per-operation on one end, bytes-per-call on the other, and
the correct fix for chattiness is to move along that dial toward the
caller's actual need, not to slam it to the opposite extreme.

Data Transfer Object and Remote Facade, Fowler, PoEAA, composes with,
fixes. DTO is the structural shape most eager-loading and REST-endpoint
fixes for Chatty I/O actually produce, one object carrying every field a
caller needs for one operation, assembled once server-side and transmitted
once. Remote Facade is the coarse-grained interface DTOs are typically
returned from. Applying Chatty I/O's fix without naming it usually means you
have independently arrived at a Data Transfer Object.

Distributed Monolith, anti-pattern, this repository, family 18-anti-
patterns, composes with, worsens. A distributed monolith's services call
each other synchronously and frequently to complete what is really one
logical unit of work, and Chatty I/O is very often the specific symptom by
which a distributed monolith is first noticed in a trace, many small,
synchronous, tightly coupled calls between services that should either be
one service or should communicate asynchronously rather than through a
chatty synchronous chain.

Circuit Breaker, resilience family, composes with, mitigates a
symptom. A circuit breaker does not fix chattiness, but a chatty caller that
generates N calls per operation multiplies the blast radius of a single
downstream failure by N, so a circuit breaker around the chatty boundary is
frequently deployed as a stopgap resilience measure while the underlying
chattiness is fixed.

Bulkhead and connection pool sizing, composes with, mitigates a
symptom. Pool exhaustion is one of the most common ways Chatty I/O surfaces
as an outage rather than a slow response, N concurrent callers each opening
N-per-operation connections exhaust a shared connection pool sized for far
fewer simultaneous connections. Sizing a bulkhead or a pool correctly buys
time; it does not reduce the number of calls the chatty code is actually
issuing.

Incompatible with nothing directly, but in tension with Cache-Aside,
this repository, tension, not conflict. Caching an already-batched response
is straightforward, one key, one cached value. Caching the result of a
chatty loop's individual small calls independently is also possible, but it
does not remove the round-trip count on a cache miss, and a cold cache under
Chatty I/O still pays the full N-round-trip cost, so caching alone should
not be treated as a substitute fix for chattiness, only as a complement to
it.

## 14. Refactoring path in and out

Refactoring code into Chatty I/O happens gradually and almost always
without anyone intending it, which is why the entering direction is worth
naming explicitly rather than only describing the fix.

1. A developer writes a loop over a collection returned by one earlier call,
   and inside that loop makes what looks, at the code-review level, like an
   innocuous single extra call, a single row fetch by id, a single small
   HTTP get, a single small file write.
2. The collection being iterated is small or empty in every environment the
   code is exercised in before release, local development, a unit test
   fixture, a demo dataset, so the loop's true call count is never observed
   under realistic N.
3. In production, the same collection routinely has tens or hundreds of
   elements, and the innocuous single extra call is now firing tens or
   hundreds of times per logical operation, exactly the shape Microsoft's
   traced example exhibits with its measured 45 SELECT statements for one
   product-subcategory call.

Refactoring out of Chatty I/O once it is diagnosed follows the sequence
Microsoft's own detection section lays out, and this entry adds the
concrete mechanical steps for each of the three shapes named in dimension 2.

1. Confirm the diagnosis with a trace, not a guess. Enable the ORM's or
   HTTP client's own request logging for the specific operation under
   suspicion and count the actual calls issued for one logical invocation
   under realistic data volume. Microsoft's own worked example did exactly
   this and found the count, 45 queries, before writing any fix.
2. Identify the single access path generating the multiplication. In an
   ORM case this is almost always one specific navigation property being
   walked inside a loop. In a REST-client case it is the set of narrow
   endpoints one caller is chaining together for one logical screen or
   report.
3. Replace the per-item call with the boundary's own batching mechanism.
   Add the ORM's eager-load directive on that one access path, or replace N
   individual single-item calls with the boundary's batch primitive, a
   multi-row select filtered by a list of ids, or a single new
   coarse-grained endpoint shaped for this exact caller.
4. Re-measure under the same realistic load, not just correctness.
   Confirm the call count for one logical operation is now a small constant
   rather than scaling with N, and confirm the new payload size and latency
   under concurrent load, not merely that the feature still returns the
   correct data for one manual test.
5. Add the new partial-failure handling the batch primitive requires,
   retrying or surfacing an unprocessed-items style result, before removing
   the old per-item error handling that assumed each item either succeeded
   or failed independently.

The reverse refactoring, deliberately splitting one coarse batched call back
into several narrow ones, is rare but legitimate when the batched call has
drifted into Extraneous Fetching, most of its callers now need only a small,
stable subset of what it returns, at which point the correct move is to
follow the same steps in reverse, tracing which fields are actually consumed
by which caller class, and splitting the interface along that boundary
rather than along the original narrow-endpoints-per-field shape that caused
the chattiness in the first place.

## 15. Testing and verification

Chatty I/O is largely invisible to correctness tests, because a chatty
implementation and a fixed one return identical data, only the number of
underlying calls differs, and this is exactly why it survives code review
and unit testing so often. Verification has to specifically assert on call
count, not on output correctness alone.

- Assert call count, not just output. Where the boundary is mockable,
  the test double should count invocations, and the test should assert an
  upper bound on that count, for example that fetching a subcategory with N
  products issues at most 2 downstream queries regardless of N, not merely
  that the returned data matches the expected shape. A test written this way
  fails loudly the moment someone reintroduces a per-item call inside a loop,
  which a purely output-based test never would.
- Vary N across test data sizes. A fixture with one product and a
  fixture with fifty products should both pass the same call-count
  assertion; if the assertion only holds at N equal to 1, the code is chatty
  and the test with N equal to 1 alone would never have caught it,
  mirroring exactly why the anti-pattern survives in development and only
  surfaces in production.
- Use the ORM's own query-logging or a SQL-capturing test double to
  count actual statements issued during an integration test, which is a
  stronger signal than counting method calls on a mock, because it also
  catches the case where an eager-load directive was added at the wrong
  layer and the ORM still silently falls back to lazy per-row fetches.
- Load test with production-representative data volume before shipping,
  the explicit first recommendation in Microsoft's own detection guidance,
  because a functional test suite proves correctness at whatever N the test
  fixtures happen to use, and chattiness is a property that only becomes
  visible, and only becomes expensive, at production N under concurrent
  load.
- For batch-write paths, explicitly test the partial-failure branch, by
  forcing the mock or test double for the batch boundary to return a
  simulated unprocessed-items result and asserting the caller correctly
  retries or surfaces exactly that unprocessed subset, since this branch has
  no equivalent in the original chatty implementation and is therefore the
  one most likely to be missing test coverage entirely after a fix ships.

## 16. Observability signals

The Microsoft catalog page's own how-to-detect section is, in effect, a
short observability runbook for this anti-pattern, and this entry's
guidance follows it directly, with the specific metrics named.

A healthy instance of an operation that touches a boundary shows a call
count to that boundary that stays flat as the logical input size grows, and
a per-operation latency that is dominated by one or two round trips' worth
of constant overhead plus payload transfer time proportional to the real
amount of data moved.

A failing, chatty instance shows the following.

- High latency paired with low throughput at the application level, the
  two symptoms named directly on the Microsoft page as the headline signal
  of Chatty I/O, together with end users reporting extended response times
  or outright timeouts under load.
- A large number of small, uniform, repeated calls to the same downstream
  resource in an APM trace for a single logical operation, visible as a
  long, flat run of near-identical short spans nested under one parent span,
  exactly what Microsoft's own trace screenshots for the traced example
  show, 45 near-identical SELECT spans under one API call's parent span.
- A database's own query-count or query-frequency metric spiking in
  proportion to a specific application-level operation's traffic, rather
  than in proportion to raw data volume, a signal that ties the
  multiplication specifically to call pattern rather than to data growth.
- Connection pool exhaustion or connection wait-time metrics rising
  under moderate concurrent load, since N-per-operation calls consume N
  pooled connections, or the same connection N times in serial, holding it
  open longer, for work that could have been one connection acquisition.
- A widening gap between p50 and p99 or p95 latency as concurrency rises,
  because the fixed per-call overhead compounds with contention for the
  shared boundary resource in a way a single-round-trip operation's latency
  does not.

The observability fix mirrors the code fix. once batching is in place, the
same dashboards should show a flat, bounded call count per logical operation
regardless of load, which is the concrete, measurable definition of no
longer chatty that this entry recommends alerting on going forward, a
static threshold on calls-per-operation-type, not merely on aggregate
request volume.

## 17. Security and privacy implications

This dimension is largely engineering judgment rather than a set of sourced,
independently verifiable claims, because the security surface of Chatty I/O
is analytical, reasoned from the mechanics described above, rather than
documented as a named vulnerability class in the sources this entry cites.

- Amplified denial-of-service surface. Because chattiness means one
  logical caller request generates N downstream calls, an attacker who can
  control or inflate N, for example by controlling the size of a collection
  the code iterates over, gets an N-times multiplier on the downstream
  resource from a single request of their own, an amplification effect that a
  correctly batched implementation, bounded to one or a small constant
  number of calls regardless of N, does not have. Rate limiting and request
  quotas applied only at the logical-request layer, without also bounding
  the downstream call count per request, will under-protect against this
  specific amplification.
- Broader logging and audit surface. N separate calls typically produce
  N separate audit log entries, database query log entries, and network
  flow records for what is, semantically, one user action, which can both
  bloat retention costs for sensitive audit data and, more subtly, make it
  harder to correlate exactly what one user action actually touched during
  an incident investigation, since the evidence is spread across many
  discrete log lines rather than one.
- Partial-failure states as a new data-consistency risk after the fix.
  As dimension 11 describes for DynamoDB's `UnprocessedKeys`, once a fix
  introduces batching, a batch can now partially succeed, which is a new
  state that did not exist in the chatty original, where each item's
  success or failure was independent and unambiguous. If that partial-
  success state is not surfaced correctly to callers or audited, sensitive
  writes can silently and invisibly fail for a subset of a batch while the
  caller believes the whole operation succeeded, a data-integrity risk with
  real privacy consequences if the missing writes were, for example, consent
  records or access-revocation entries.
- No direct implication for encryption in transit or at rest. Chattiness
  is orthogonal to whether individual calls or a batched call are encrypted;
  fixing chattiness does not by itself change a system's exposure on that
  axis, and this entry deliberately does not claim otherwise.

## 18. References

1. Microsoft, "Chatty I/O antipattern," Azure Architecture Center,
   https://learn.microsoft.com/en-us/azure/architecture/antipatterns/chatty-io/,
   verified 2026-08-04. Primary source for the anti-pattern's name, the three
   worked examples (ORM and N+1, REST, file I/O), the measured
   before-and-after load test numbers, 410 versus 3,970 requests per minute,
   near-a-minute versus 5 to 6 second response times, and the detection
   methodology.
2. Martin Fowler, "Data Transfer Object," Patterns of Enterprise Application
   Architecture catalog,
   https://martinfowler.com/eaaCatalog/dataTransferObject.html, verified
   2026-08-04. Source for the each-call-is-expensive framing and the
   historical Value Object naming note.
3. Martin Fowler, Patterns of Enterprise Application Architecture,
   Addison-Wesley, 2002, catalog entries "Data Transfer Object" and "Remote
   Facade." Print source for the same pattern reasoning cited in reference 2.
4. Wikipedia, "Nagle's algorithm,"
   https://en.wikipedia.org/wiki/Nagle%27s_algorithm, verified 2026-08-04.
   Source for the small-packet problem description, the algorithm's
   buffering rule, and the `TCP_NODELAY` mitigation option.
5. Amazon Web Services, "BatchGetItem," Amazon DynamoDB API Reference,
   https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_BatchGetItem.html,
   verified 2026-08-04. Source for the 100-item and 16 MB batch limits, the
   `UnprocessedKeys` partial-failure contract, and the exponential-backoff
   retry recommendation.
6. Wikipedia, "GraphQL," https://en.wikipedia.org/wiki/GraphQL, verified
   2026-08-04. Source for GraphQL's 2012 origin at Facebook, its 2015
   open-source release, and its exact-shape-of-data-needed design goal.
7. Google and the gRPC Authors, "Introduction to gRPC,"
   https://grpc.io/docs/what-is-grpc/introduction/, verified 2026-08-04.
   Source for the RPC-as-local-object framing and Protocol Buffers as the
   default serialization mechanism.

## Code examples

### TypeScript. N+1 fetch versus one batched fetch

```typescript
interface Product {
  id: number;
  name: string;
  priceHistoryIds: number[];
}
interface PricePoint {
  id: number;
  productId: number;
  price: number;
}

const products: Product[] = [
  { id: 1, name: "Widget", priceHistoryIds: [10, 11] },
  { id: 2, name: "Gadget", priceHistoryIds: [12] },
];
const priceStore: Record<number, PricePoint> = {
  10: { id: 10, productId: 1, price: 9.99 },
  11: { id: 11, productId: 1, price: 8.49 },
  12: { id: 12, productId: 2, price: 19.99 },
};

// Chatty. one lookup per price id, N calls for N ids.
function chattyFetchPrices(items: Product[]): number {
  let calls = 0;
  for (const item of items) {
    for (const priceId of item.priceHistoryIds) {
      calls += 1;
      const found = priceStore[priceId];
      if (!found) throw new Error("missing price " + priceId);
    }
  }
  return calls;
}

// Chunky. one batched lookup call for the whole request.
function batchedFetchPrices(items: Product[]): { calls: number; prices: PricePoint[] } {
  const allIds = items.flatMap((item) => item.priceHistoryIds);
  const prices = allIds.map((id) => {
    const found = priceStore[id];
    if (!found) throw new Error("missing price " + id);
    return found;
  });
  return { calls: 1, prices };
}

const chattyCalls = chattyFetchPrices(products);
const chunkyResult = batchedFetchPrices(products);
console.log("chatty calls", chattyCalls);
console.log("chunky calls", chunkyResult.calls, "prices fetched", chunkyResult.prices.length);
if (chattyCalls !== 3 || chunkyResult.calls !== 1 || chunkyResult.prices.length !== 3) {
  throw new Error("unexpected result");
}
console.log("ok");
```

### Python. simulated N+1 database access versus a joined batch access

```python
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class Product:
    id: int
    name: str


@dataclass
class PriceHistory:
    id: int
    product_id: int
    price: float


class FakeDb:
    def __init__(self) -> None:
        self.calls = 0
        self.products: Dict[int, Product] = {
            1: Product(1, "Widget"),
            2: Product(2, "Gadget"),
            3: Product(3, "Gizmo"),
        }
        self.prices: List[PriceHistory] = [
            PriceHistory(10, 1, 9.99),
            PriceHistory(11, 1, 8.49),
            PriceHistory(12, 2, 19.99),
            PriceHistory(13, 3, 4.25),
        ]

    def get_products(self) -> List[Product]:
        self.calls += 1
        return list(self.products.values())

    def get_prices_for_product(self, product_id: int) -> List[PriceHistory]:
        self.calls += 1
        return [p for p in self.prices if p.product_id == product_id]

    def get_products_with_prices_joined(self):
        self.calls += 1
        result = {}
        for p in self.products.values():
            result[p.id] = (p, [pr for pr in self.prices if pr.product_id == p.id])
        return result


def chatty_load(db: FakeDb) -> int:
    products = db.get_products()
    for product in products:
        db.get_prices_for_product(product.id)
    return db.calls


def chunky_load(db: FakeDb) -> int:
    db.get_products_with_prices_joined()
    return db.calls


chatty_db = FakeDb()
chatty_calls = chatty_load(chatty_db)

chunky_db = FakeDb()
chunky_calls = chunky_load(chunky_db)

print("chatty calls", chatty_calls)
print("chunky calls", chunky_calls)

assert chatty_calls == 4, "expected 1 plus 3 product-price calls"
assert chunky_calls == 1, "expected exactly one joined call"
print("ok")
```

### Go. simulated batch API, BatchGetItem style, versus a per-key loop

```go
package main

import "fmt"

type Item struct {
	Key   string
	Value string
}

type Store struct {
	Calls int
	Data  map[string]string
}

func NewStore() *Store {
	return &Store{
		Data: map[string]string{
			"a": "apple",
			"b": "banana",
			"c": "cherry",
		},
	}
}

// GetItem is one round trip per key, the chatty shape.
func (s *Store) GetItem(key string) (string, bool) {
	s.Calls++
	v, ok := s.Data[key]
	return v, ok
}

// BatchGetItem is one round trip for many keys, the chunky shape.
func (s *Store) BatchGetItem(keys []string) ([]Item, []string) {
	s.Calls++
	var found []Item
	var unprocessed []string
	for _, k := range keys {
		if v, ok := s.Data[k]; ok {
			found = append(found, Item{Key: k, Value: v})
		} else {
			unprocessed = append(unprocessed, k)
		}
	}
	return found, unprocessed
}

func chattyFetch(s *Store, keys []string) int {
	for _, k := range keys {
		s.GetItem(k)
	}
	return s.Calls
}

func chunkyFetch(s *Store, keys []string) (int, []Item, []string) {
	found, unprocessed := s.BatchGetItem(keys)
	return s.Calls, found, unprocessed
}

func main() {
	keys := []string{"a", "b", "c", "missing"}

	chattyStore := NewStore()
	chattyCalls := chattyFetch(chattyStore, keys)

	chunkyStore := NewStore()
	chunkyCalls, found, unprocessed := chunkyFetch(chunkyStore, keys)

	fmt.Println("chatty calls", chattyCalls)
	fmt.Println("chunky calls", chunkyCalls, "found", len(found), "unprocessed", unprocessed)

	if chattyCalls != 4 {
		panic("expected 4 chatty calls")
	}
	if chunkyCalls != 1 || len(found) != 3 || len(unprocessed) != 1 {
		panic("expected 1 batched call, 3 found, 1 unprocessed")
	}
	fmt.Println("ok")
}
```
