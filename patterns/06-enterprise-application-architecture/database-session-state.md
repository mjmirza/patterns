---
name: Database Session State
slug: database-session-state
family: 06-enterprise-application-architecture
category: Base Patterns
aliases: [Session Table, Persistent Session Store, Server-Side Database Session, Shared Session Store]
first_described: "Fowler, Patterns of Enterprise Application Architecture, 2002"
maturity: canonical
related: [server-session-state, client-session-state, serialized-lob, optimistic-offline-lock, pessimistic-offline-lock, identity-field, remote-facade, data-transfer-object]
incompatible_with: []
verified: 2026-08-11
---

# Database Session State

## 1. Name, aliases, and lineage

The canonical name is Database Session State, the third of the three sibling
Base Patterns that Martin Fowler grouped in *Patterns of Enterprise
Application Architecture*, Addison-Wesley, 2002, alongside Client Session
State and Server Session State. The book's own catalog page states the
intent in one line, "Stores session data as committed data in the database,"
and notes the pattern is detailed in Chapter 17 of the online edition
([Fowler's summary page for the pattern](https://martinfowler.com/eaaCatalog/databaseSessionState.html),
verified 2026-08-11). Fowler frames all three patterns as three answers to
one question, where does a web application keep the data it gathers across a
sequence of requests from one user, given that HTTP treats every request as
if it were the first.

In practice the pattern goes by several names that describe the same
architectural decision from a different angle. Session Table is the name
used when a team talks about the schema object itself rather than the
behavior, because the pattern's defining artifact is a table (or a small set
of tables) keyed by a session identifier. Persistent Session Store is the
name used in framework documentation, for example Spring's own reference
documentation for its JDBC-backed session implementation, which calls the
underlying idea a store rather than a table, because the store's storage
engine is an implementation detail behind an interface
([Spring Session HTTP Session reference](https://docs.spring.io/spring-session/reference/http-session.html),
verified 2026-08-11). Server-Side Database Session distinguishes it from
Server Session State, which also keeps the data on the server but in
process memory rather than in a durable, transactional store.

The distinction that matters most, and the one loose usage of "database
session" tends to blur, is between a store that is *committed*, meaning it
survives a full restart of every application server and the database itself
in the ordinary case, and a store that merely lives outside a single
process, such as a pure in-memory replicated cache with no write-ahead log
or persistence configured. Fowler's original naming assumes a relational
database with the ACID guarantees the term implies. A distributed cache
configured for durability, for example Redis with AOF persistence enabled or
a managed cache service backed by disk, sits close enough to the same
architectural role that this entry treats it as an implementation variant
(dimension 8) rather than a different pattern, while a purely volatile
distributed cache with no persistence is better understood as a distributed
form of Server Session State. This is an engineering distinction, not one
Fowler draws explicitly in the source, and it is stated as judgement here
because the boundary is a matter of the operator's configuration choice
rather than a fact about any one product.

## 2. Problem and context

A web application needs to remember something about a user across more than
one HTTP request, a shopping cart, an authenticated identity, a wizard's
partial answers, a rate-limit counter, and HTTP itself supplies no place to
put it. The three sibling patterns in this family exist because that gap has
to be filled somewhere, and the three obvious somewheres are the client, one
server's memory, or a store every server can reach.

The concrete situation that pushes a team toward Database Session State
looks like this. The application started on one server, holding sessions in
that server's process memory, which worked. Traffic grew, and a second
server joined behind a load balancer. Sessions now had to be pinned to the
server that created them, sticky sessions, so the load balancer had to
inspect a cookie or a source IP and route every request from one user back
to the same instance. That works until the instance restarts for a
deployment, at which point every session that instance was holding vanishes
and every one of those users is logged out or loses a cart mid-checkout.
Sticky routing also fights against autoscaling, because a scale-down event
has to drain sessions rather than simply stopping a process, and it fights
against rolling deploys, because a server being replaced has to finish or
migrate its live sessions first.

The context has three parts that together make an externally held,
durable store the right answer rather than a workaround.

- More than one application server instance must be able to service any
  request from a given user, without the load balancer needing to remember
  which instance served that user last.
- Session data must survive an individual server crashing, restarting for a
  deploy, or being scaled down, without every affected user losing their
  session.
- The team already operates, or is willing to operate, a durable data store
  reachable from every application server, and is willing to accept the
  latency of a network round trip on session access in exchange for that
  durability and that shared visibility.

The Database Session State answer is to put the session's data in that
shared, durable store, keyed by an opaque session identifier the client
carries (usually in a cookie), and to have every application server read
that row at the start of a request that needs the session and write it back
at the end, so no server instance holds session state that only it knows
about.

## 3. Forces

Durability against latency. A database write that is part of a committed
transaction survives a crash the instant it commits. That durability is
purchased with a network round trip and, in most relational databases, a
disk fsync on commit, both of which cost single-digit to double-digit
milliseconds that an in-process memory read or write does not pay.

Consistency against availability. A single relational database, or a
primary-replica pair used for strict reads, gives every application server
the same view of a session at every moment, at the cost that a database
outage or partition now takes session access down for the whole
application, an availability trade a purely in-memory, per-instance store
does not make, because that store has no shared dependency to lose.

Operability against new failure surface. Reusing a database the team
already runs, already backs up, already monitors, and already has an
on-call runbook for is a genuine operability win over introducing a new
piece of infrastructure, such as a Redis cluster, purely to hold sessions.
The trade is that session traffic now shares the database's connection
pool, its IOPS budget, and its blast radius with the application's core
transactional workload, so a spike in session churn can degrade unrelated
business transactions and vice versa.

Cost against reuse. Storage and IOPS on a relational database are usually
priced and provisioned for durable, structured business data, and session
rows, which are numerous, small, and short-lived, are a different traffic
shape, high write volume, low value per row, than the rest of the schema.
Reusing the same database avoids the cost of standing up a second store, but
that reuse can under-price the actual IOPS cost of session churn if nobody
accounts for it separately.

Cognitive load and team topology. A team that already has database
expertise, migration tooling, and monitoring built around its relational
database pays a lower cognitive cost adding a sessions table to that
database than learning the operational quirks of a new caching layer. A
platform team that owns the database separately from the application teams
using it may see the opposite trade, because session traffic is now a
shared-resource contention problem between teams rather than a
self-contained concern of the application team alone.

## 4. Applicability and non-applicability

Reach for Database Session State when the following hold.

- The application runs more than one server instance behind a load balancer
  and the team wants to remove sticky-session routing so that any instance
  can serve any request, simplifying rolling deploys and autoscaling.
- Session data must survive a full application-server restart or crash
  without the affected users losing their session, a guarantee a pure
  in-memory store cannot make on its own.
- The organization operates a database with high availability, backups, and
  monitoring already in place, and does not want to introduce a separate
  caching tier solely to hold sessions.
- Session state needs to be centrally queryable or revocable, for example an
  operator needs to see which users are currently active, or a security team
  needs to instantly invalidate a specific user's sessions by deleting rows,
  something a self-contained signed client token cannot do without a
  separate revocation list.
- Session data occasionally needs to be written in the same database
  transaction as a piece of business data, for example marking a session's
  checkout as complete at the exact instant the order row commits, so both
  either happen or neither does.
- Session payloads are larger than comfortably fits in a cookie, or the
  application does not want session data readable by the client at all.

Do not reach for it, and prefer Server Session State backed by a pure cache,
or Client Session State, when the following hold.

- The request path is latency-sensitive enough that a network round trip to
  the database on every request materially affects the user-visible
  latency budget, and the session data does not need database-grade
  durability, for example a per-request feature flag cache or a UI
  preference that is fine to lose on a crash.
- Session writes happen on a very large fraction of requests, for example a
  "last seen" heartbeat updated on every page view across millions of
  concurrent users, in which case the write volume alone can overwhelm a
  primary transactional database's IOPS budget, and a purpose-built cache
  or a write-behind buffer fits the shape better.
- The application genuinely has no persistent, shared data store reachable
  from every instance, and introducing one solely for sessions is a larger
  operational commitment than the problem justifies, for example a small
  internal tool running on a single server where Server Session State is
  sufficient.
- The service is a stateless, cacheable public API with no notion of a
  user session at all, in which case no session-state pattern applies and
  adding one is unnecessary machinery.
- Regulatory or architectural constraints forbid coupling authentication
  availability to the primary business database's availability, in which
  case a separate, independently scaled session store, whether that store
  is itself relational or not, is the better fit, and pure Database Session
  State against the shared primary database is the wrong choice even though
  the pattern's shape, an external durable store, is still correct in
  spirit.

## 5. Structure

- **Session Identifier.** An opaque, high-entropy token issued to the
  client, usually in a cookie, that has no meaning of its own beyond acting
  as the primary key that finds one row in the session store. It carries no
  session data itself, unlike the token in Client Session State.
- **Session Store (sessions table).** A relational table, or a small set of
  related tables, holding one row per active session, usually with
  columns for the identifier, the payload (either normalized columns or a
  single serialized blob, dimension 8), a version or last-modified marker
  for concurrency control, and an expiry timestamp.
- **Session Repository.** The piece of server-side code, often a filter,
  middleware, or a framework's session-handling layer, that reads the
  session row at the start of a request, exposes it to application code
  through an in-memory representation for the duration of that request, and
  writes any changes back at the end of the request.
- **Application Server.** Any one of a fleet of otherwise stateless server
  processes. Because the session lives outside the process, any instance
  can service any request for any session, removing the need for the load
  balancer to route by session affinity.
- **Load Balancer.** Distributes requests across the fleet without needing
  to track which instance last served a given session, in contrast to the
  sticky routing that Server Session State usually requires.
- **Expiry Reaper.** A scheduled background process that deletes rows whose
  expiry timestamp has passed. Relational databases have no built-in
  per-row time-to-live the way some key-value stores do, so this
  responsibility has to be built and run explicitly, or the sessions table
  grows without bound.

## 6. ASCII structure diagram

```
                     +-----------------------------+
   Browser  ------>  |  Load balancer               |
                     |  (no session affinity)       |
                     +-----------------------------+
                        /            |            \
                       /             |             \
              +--------+       +--------+      +--------+
              | App A  |       | App B  |      | App C  |
              | (no local     | (no local     | (no local
              |  session)     |  session)     |  session)
              +--------+       +--------+      +--------+
                       \             |             /
                        \            |            /
                         v           v           v
              +---------------------------------------+
              |  Relational database, system of record |
              |  +-----------------------------------+ |
              |  | sessions                           | |
              |  | id | payload | version | expires_at| |
              |  +-----------------------------------+ |
              +---------------------------------------+
                                 ^
                                 |
                       +-------------------+
                       | Expiry reaper job |
                       +-------------------+
```

## 7. Dynamics

The interesting part of this pattern's runtime behavior is that a session's
lifetime is a sequence of independent read-modify-write cycles against one
row, made by whichever server instance happens to handle each request, with
no guarantee the same instance handles two requests in a row.

```
Browser         App server A       App server B       sessions table
   |                  |                   |                  |
   | POST /login      |                   |                  |
   |----------------->|                   |                  |
   |                  | INSERT id=S1,     |                  |
   |                  | version=1         |                  |
   |                  |------------------------------------->|
   |                  |                   |                  |
   |  Set-Cookie: S1  |                   |                  |
   |<-----------------|                   |                  |
   |                                                          |
   | GET /cart  (routed to a different instance, no affinity) |
   |------------------------------------->|                  |
   |                  |                   | SELECT id=S1     |
   |                  |                   |----------------->|
   |                  |                   |  row v1          |
   |                  |                   |<-----------------|
   |                  |                   | add item, then   |
   |                  |                   | UPDATE ... WHERE |
   |                  |                   | id=S1 AND        |
   |                  |                   | version=1        |
   |                  |                   |----------------->|
   |                  |                   |  1 row affected, |
   |                  |                   |  now version=2   |
   |  200 OK          |                   |<-----------------|
   |<--------------------------------------|                 |
   |                                                          |
   | (idle past expiry)                                       |
   |                                       reaper: DELETE     |
   |                                       WHERE expires_at   |
   |                                       < now()            |
   |                                       ------------------>|
```

The version check on the `UPDATE` is what makes this safe when two requests
for the same session race, which happens routinely when a browser fires
several requests for the same page concurrently, or when a user has two
tabs open. Whichever request's `UPDATE` runs first advances the version and
wins; the second request's `UPDATE` matches zero rows because the version it
read no longer matches, and the session repository can retry it, re-reading
the fresh row and reapplying its change, or surface the conflict, depending
on the implementation variant chosen (dimension 8). Without that check, the
second `UPDATE` would silently overwrite the first request's change, the
classic lost update problem discussed further in dimension 11.

## 8. Implementation variants

**Serialized payload versus normalized columns.** The session's data can be
stored as a single serialized blob, most often JSON or a binary format, in
one column, which is fast to write, simple to evolve at the application
layer, and matches the shape of the closely related Serialized LOB
technique for persisting a whole object graph as one field rather than a
set of joined tables. Or it can be stored as normalized columns, one per
piece of session data, which lets the database enforce types and lets the
application update a single field without deserializing and reserializing
the whole payload, at the cost of a schema migration every time a new piece
of session data is added.

**Sliding versus absolute expiration.** A sliding-expiration implementation
extends the `expires_at` column on every read, so an active session never
times out and only an idle one does. An absolute-expiration implementation
sets `expires_at` once, at creation, so even an active session is forced to
re-authenticate after a fixed window, favoring security over convenience
for sensitive applications.

**Optimistic versus pessimistic concurrency control.** The version-checked
`UPDATE` shown in dimension 7 is Optimistic Offline Lock applied to a
session row, cheap under low contention and the usual default. A
high-contention session, for example one multiple concurrent background
jobs write to on behalf of one user, can instead take a row lock with
`SELECT ... FOR UPDATE` before modifying it, Pessimistic Offline Lock's
shape, trading throughput for the certainty that no concurrent writer can
even begin a conflicting change while the lock is held.

**Framework-provided implementations.** Spring Session's JDBC module wires
a servlet filter that transparently replaces the standard `HttpSession`
implementation with one backed by a relational table, configured with a
single `@EnableJdbcHttpSession` annotation
([Spring Session JDBC configuration](https://docs.spring.io/spring-session/reference/http-session.html),
verified 2026-08-11). Apache Tomcat ships a `PersistentManager` whose
`DataSourceStore` implementation "saves swapped out sessions in individual
rows of a preconfigured table in a database that is accessed via a data
source"
([Apache Tomcat 9 Manager configuration reference](https://tomcat.apache.org/tomcat-9.0-doc/config/manager.html),
verified 2026-08-11). PHP's `session_set_save_handler` function exists
specifically to let a developer swap the default file-based session
handler for a custom one, and the official manual's own description gives
"storing the session data in a local database" as the example use case
([PHP manual, session_set_save_handler](https://www.php.net/manual/en/function.session-set-save-handler.php),
verified 2026-08-11).

**Split-payload hybrid.** A small, non-sensitive identity claim can travel
in a signed client-side cookie, Client Session State's shape, while a
reference id in that same cookie points at the bulk of the session data,
kept in the database. This keeps the cookie small and cacheable while
retaining server-side revocability for the parts that matter.

**Cache-in-front-of-database.** A distributed cache, for example Redis, can
sit in front of the sessions table as a read-through cache, with the
database remaining the durable source of truth and the cache absorbing the
bulk of read traffic. This is a distinct architecture from a pure Server
Session State cache, because the database, not the cache, is what a
restart or an eviction falls back to, and it is worth naming as its own
variant because teams often reach for it once database read latency
becomes the bottleneck identified in dimension 11.

## 9. Known production uses

Spring Session's JDBC session repository is a widely deployed, officially
maintained implementation of this exact pattern for the Java Servlet
`HttpSession` API, replacing the container's in-memory session with rows in
a relational database through a servlet filter, configured declaratively
([Spring Session reference, HTTP Session support](https://docs.spring.io/spring-session/reference/http-session.html),
verified 2026-08-11).

Apache Tomcat, the reference servlet container for the Java servlet
specification, ships
`org.apache.catalina.session.PersistentManager` paired with
`org.apache.catalina.session.DataSourceStore` specifically to persist idle
or all sessions to a database table accessed through a configured
`DataSource`, described in Tomcat's own manager configuration documentation
([Apache Tomcat 9 Manager configuration reference](https://tomcat.apache.org/tomcat-9.0-doc/config/manager.html),
verified 2026-08-11).

PHP's core session extension is explicitly designed to be extensible for
this purpose. `session_set_save_handler` lets an application override the
default file-based storage, and the PHP manual states plainly that this
mechanism is "most useful when a storage method other than those supplied
by PHP sessions is preferred, e.g. storing the session data in a local
database," a pattern documented with a full user-contributed example
against a relational schema on the same manual page
([PHP manual, session_set_save_handler](https://www.php.net/manual/en/function.session-set-save-handler.php),
verified 2026-08-11).

ASP.NET Core's session middleware is built on the framework's
`IDistributedCache` abstraction, and Microsoft's own guidance recommends a
"Redis, SQL Server, or Azure Postgres distributed cache" specifically
because such a store "doesn't require sticky sessions," naming SQL Server
as a first-class supported backing store for session state in a
multi-instance deployment
([ASP.NET Core session and app state documentation](https://learn.microsoft.com/en-us/aspnet/core/fundamentals/app-state),
verified 2026-08-11).

## 10. Consequences

Positive. Session data survives an application server crashing, restarting
for a deploy, or being scaled to zero and back, because the data never
lived in that server's memory to begin with. No load-balancer session
affinity is required, which simplifies rolling deploys, blue-green
releases, and autoscaling, because any instance can serve any request for
any session. A session can be revoked instantly and centrally by deleting
its row, a capability a purely stateless, self-contained client token
cannot offer without a separate revocation store. The store can reuse the
database's existing high-availability, backup, and monitoring
infrastructure rather than standing up a new one. Payload size is bounded
by the database's practical row and column limits, not by a cookie's
few-kilobyte cap. Session writes can, when needed, participate in the
same transaction as a business write, giving a strong consistency
guarantee that a cache-backed store, eventually consistent by nature in
most deployments, cannot give as directly.

Negative. Every session access costs at least one network round trip to
the database, and often a write transaction, which is materially slower
than an in-process memory access and adds latency to every request that
touches the session. The database becomes a shared point of contention
between session traffic and the application's core business traffic, so a
spike in one can degrade the other, a coupling that a separate,
independently scaled session store avoids. Relational databases have no
native per-row expiration, so the pattern requires building and operating
an explicit reaper job, and forgetting to do so leads directly to the
unbounded table growth described in dimension 11. A database outage now
takes down session access, and often authentication, for the entire
application, an availability coupling a team must consciously accept or
mitigate. The session payload, if stored as a single serialized blob, adds
serialization cost on every read and write and creates a schema-evolution
burden for that column that normalized columns do not have.

## 11. Failure modes and misuse

Symptom, request latency spikes under load and the connection pool
monitoring dashboard shows exhausted or near-exhausted database
connections. Cause, session reads and writes on every request share the
same connection pool as the application's core business queries, and that
pool was sized for business traffic alone. Fix, size a dedicated connection
pool for session traffic, or route session reads to a database replica
independent of the pool serving business transactions.

Symptom, the sessions table grows without bound, storage and backup costs
climb month over month, and index scans against the table slow down over
time even for active sessions. Cause, no expiry reaper was implemented, so
expired rows accumulate forever, since the relational database itself has
no notion of a row time-to-live. Fix, run a scheduled, batched `DELETE`
job against `expires_at`, indexed on that column, during off-peak hours, or
partition the table by creation date and drop old partitions outright.

Symptom, a user reports that changes made in one browser tab silently
vanish after switching to another tab of the same application. Cause, the
session repository performs a naive `UPDATE sessions SET payload = ?
WHERE id = ?` with no version check, so two concurrent requests for the
same session each read the row, and whichever request's write commits
second overwrites the first request's change entirely, the classic lost
update. Fix, add a version or timestamp column checked in the `WHERE`
clause of the update, the Optimistic Offline Lock shape shown in dimension
7, and treat a zero-row update result as a conflict to retry rather than a
silent no-op.

Symptom, during a planned database maintenance window or an unplanned
database outage, every logged-in user is logged out or the application
returns intermittent server errors on any authenticated page. Cause, the
session store shares the exact availability profile of the primary
business database, a coupling this pattern introduces by design, and no
fallback path exists for the session-read path specifically. Fix, either
accept the coupling explicitly as a stated trade-off given the
consistency guarantee it buys, or add a fallback path, such as a
short-lived read-through cache that can serve recently read sessions
during a brief outage, understanding that this reintroduces a form of the
Server Session State cache Database Session State was chosen to avoid.

Symptom, a security review finds that a session cookie stolen hours
earlier is still usable even though the affected user clicked "log out on
all devices." Cause, the "log out everywhere" action deleted only the
session row matching the identifier the request presented, not every row
belonging to that user, so any other still-live session for the same user
remained valid. Fix, key the revocation query by the user's identity, not
by a single session identifier, and delete or flag every row for that
user, and check expiry at read time as well as relying on the reaper, so a
reaper delay is never the only thing standing between an attacker and a
supposedly revoked session.

Symptom, a routine deploy that adds one new field to the session payload
causes a wave of deserialization errors in production immediately after
release, affecting only users whose sessions were created before the
deploy. Cause, the Serialized LOB variant of the payload column has no
tolerance for older rows that predate the new field, and the
deserialization code assumes every field is always present. Fix, make the
payload deserializer tolerant of missing fields with sensible defaults, or
require re-authentication across a breaking payload-shape change instead
of assuming forward compatibility that was never built.

## 12. Trade-off matrix

| Force | Database Session State | Server Session State | Client Session State |
|---|---|---|---|
| Access latency per request | Highest, a network round trip, often a write transaction, on session touch. | Lowest, an in-process memory read or write. | Low to moderate, no server round trip for reads, but the client must transmit the full payload with every request. |
| Durability across a server crash | High, a committed row survives any single server's crash or restart. | Low, unless the memory store is itself externally replicated. | High, the client, not the server, holds the data, so a server crash loses nothing session-related. |
| Requires load-balancer session affinity | No, any instance can read any row. | Usually yes, unless paired with an external replicated cache. | No, the client carries everything needed on every request. |
| Central, instant revocation | High, delete the row and it is gone everywhere immediately. | Moderate, requires reaching every instance holding the session, or a shared store. | Low, without a separate revocation list; a self-contained signed token is valid until it expires on its own. |
| Payload size cap | High, bounded by database row and column limits. | High, bounded by process memory. | Low, bounded by practical cookie and header size limits, RFC 6265 documents around 4096 bytes as the size a client should support ([RFC 6265, section 6.1](https://datatracker.ietf.org/doc/html/rfc6265#section-6.1), verified 2026-08-11). |
| Availability coupling | Coupled to the shared database's availability. | Coupled only to the one instance holding the session, unless clustered. | None beyond the client itself. |
| Operational surface added | Low, if an existing database is reused; a reaper job must still be built. | Low for a single instance; a new clustering or replication concern for many. | Low, a signing key to manage, no store to run at all. |

## 13. Related and incompatible patterns

Server Session State and Client Session State are this pattern's two direct
siblings, all three answering the same question, where does session data
live between requests, and Fowler presents them as options to choose
between per field of session data rather than as mutually exclusive choices
for a whole application. An authentication claim held on the client, a
shopping cart held in the database, and a short-lived feature flag cache
held in server memory can all coexist in one system, each chosen for the
force that matters most for that particular piece of data.

Serialized LOB is the natural implementation technique for the payload
column when a team chooses the single-blob variant from dimension 8 over
normalized columns; it is the general-purpose pattern for persisting a
complex object graph as one large field rather than a set of joined
tables, described in the same catalog
([Fowler's summary page for Serialized LOB](https://martinfowler.com/eaaCatalog/serializedLOB.html),
verified 2026-08-11). This entry treats the connection between the two
patterns as a matter of common engineering practice rather than a link
Fowler states outright about session state specifically, since the
Serialized LOB catalog page itself makes no mention of sessions.

Optimistic Offline Lock and Pessimistic Offline Lock are the two
concurrency-control techniques available for the read-modify-write cycle
described in dimension 7, and the choice between them is exactly the
choice described in dimension 8 between a version-checked update and a
row-level lock. Identity Field is present at the structural level, because
the session identifier that is this pattern's primary key is itself an
ordinary instance of that pattern applied to a session row rather than a
domain entity. Remote Facade and Data Transfer Object become relevant when
session data crosses a service boundary, for example a session lookup
exposed to other internal services, in which case the row read from the
database is shaped into a transport-friendly DTO before it leaves the
service that owns the sessions table.

No pattern is strictly incompatible with this one in the sense of the two
being unable to coexist in the same system, but combining Database Session
State and Client Session State for the *same* piece of data, storing the
authoritative copy in both a database row and a signed client token, is a
design smell rather than a sound hybrid, because it creates two sources of
truth that can silently disagree once either is updated independently,
undermining the durability and revocability that were the reason to choose
a database store in the first place.

## 14. Refactoring path in and out

Introducing Database Session State into an application currently using
Server Session State, in-process memory sessions.

1. Create the sessions table, or adopt a framework-provided one, with an
   identifier column, a payload column or normalized columns, a version
   column, and an expiry column.
2. Introduce a session repository behind the same interface the application
   already uses to read and write session data, so application code does
   not change, only the implementation behind that interface does. Spring
   Session's servlet filter and Tomcat's `PersistentManager` are examples
   of frameworks that do exactly this transparently.
3. Deploy the change behind a feature flag or to one instance in the fleet
   first, monitoring session-read and session-write latency specifically,
   since this is the metric most likely to reveal a connection-pool sizing
   problem before it reaches every instance.
4. Add the expiry reaper job before, not after, the change reaches
   production traffic, since a sessions table with no reaper starts
   accumulating rows from the moment traffic hits it.
5. Remove the sticky-session configuration on the load balancer only after
   the database-backed store has run under full production traffic for
   long enough to build confidence, since removing affinity early, while
   old in-memory sessions from before the migration still exist on some
   instances, can strand users mid-session.

Refactoring away from Database Session State when database latency or
contention becomes the bottleneck.

1. Introduce a read-through cache in front of the sessions table, keeping
   the database as the durable system of record, which addresses read
   latency without giving up durability or central revocability.
2. If write volume, not read volume, is the bottleneck, for example a
   heartbeat field updated on nearly every request, split that
   high-frequency, low-value field out of the transactional row entirely
   into a purpose-built store, keeping the durable, security-relevant parts
   of the session in the database and only the noisy field elsewhere.
3. For a full move to Client Session State, introduce token signing, most
   often JSON Web Tokens, decide an explicit revocation strategy since a
   self-contained token cannot be revoked the way a database row can, and
   confirm the payload actually fits the size and sensitivity constraints
   a client-held token implies before committing to the migration.

## 15. Testing and verification

Test the session repository against a real database engine, not a mock,
because the entire value of this pattern lives in transactional and
concurrency behavior that a mock, by construction, cannot exhibit; an
in-memory or containerized instance of the real database engine gives
confidence a mocked repository cannot. Write a concurrency regression test
that opens two logical readers of the same session row, has each attempt an
update using the version each of them read, and asserts that exactly one
update succeeds and the other is rejected, directly exercising the lost
update prevention described in dimension 7 and dimension 11. Write a
boundary test for the expiry reaper that inserts rows exactly at,
immediately before, and immediately after the expiry cutoff, and asserts the reaper deletes
only the rows it should, since off-by-one errors here either leak live
sessions past their intended lifetime or delete sessions early. Add a
fault-injection test that severs the database connection mid-request and
asserts the application degrades in the way the team intended, whether
that is a clean error response or a fallback path, rather than an
unhandled exception, since a happy-path test alone cannot reveal how the
availability coupling described in dimension 10 actually behaves under
failure. Load test with a realistic ratio of session reads to session
writes against the actual connection pool configuration before shipping to
production, because pool sizing problems, the most common failure mode in
dimension 11, are invisible at low concurrency and only appear once
traffic is representative.

What becomes easy because of this pattern is testing business logic in
isolation from any particular HTTP session mechanism, since a session
repository with a narrow read and write interface is simple to substitute
with a deterministic test double for tests that are not themselves testing
the session store. What becomes harder is reproducing true multi-instance
race conditions realistically, since a single test process naturally
serializes what production would run as genuinely concurrent requests
across separate server processes, and a test suite has to deliberately
construct the race rather than rely on incidentally observing one.

## 16. Observability signals

Track the sessions table's row count over time; a healthy system shows a
count that tracks the number of active users and stays roughly flat under
steady traffic, while a monotonically climbing count with no corresponding
growth in active users is the clearest signal that the expiry reaper has
stopped running or is falling behind. Track session-read and session-write
latency as their own metric, separate from overall request latency, at
p50, p95, and p99, since these two numbers isolate the specific cost this
pattern adds and make a degrading database directly visible before it
shows up as generalized application slowness. Track database connection
pool utilization attributable specifically to session traffic, separated
from business-query traffic if the pool is shared, since connection
exhaustion, the leading cause in dimension 11's first failure mode, is
otherwise invisible until it has already started rejecting connections.
Track the rate of optimistic-lock version conflicts, meaning updates that
matched zero rows because the version had already moved; a low, steady
rate under normal traffic is expected, and a spike correlates directly with
either a genuine burst of concurrent activity for the same sessions or a
client retry storm worth investigating. Track session creation rate against
session deletion rate; under steady state these should roughly balance,
and a sustained gap between them, more creations than deletions, is an
earlier warning of reaper failure than the raw row count alone, because it
shows the trend before the absolute number becomes alarming. Track the
error rate specifically on payload deserialization, which functions as an
early warning canary for the schema-drift failure mode in dimension 11,
surfacing the very first request that hits an old row shaped differently
from what the newly deployed code expects.

## 17. Security and privacy implications

The sessions table is a high-value target, because a successful SQL
injection or an over-broad query against it does not leak only one
record, it can expose or forge session identifiers for many users at
once, so every query against it must be parameterized with the same
discipline applied to any table holding authentication-adjacent data, no
exceptions carved out because "it is only session data."

Session payloads routinely carry personally identifiable information, a
user's name, cart contents, sometimes short-lived tokens for third-party
APIs made on the user's behalf, and that data must sit behind the same
encryption-at-rest, access control, and least-privilege database
permissions as any other table holding personal data, not a lighter
standard because sessions feel transient. That transience is itself a
compliance concern in the other direction, because a reaper that is slow
or broken (dimension 11) means expired session data, including personal
information, persists in the database and in its backups longer than the
application's stated retention policy allows, which is directly relevant
under data-protection regimes that grant a right to erasure.

Central revocability is this pattern's clearest security advantage over a
self-contained client token. An operator, an automated fraud detection
system, or the affected user themselves can invalidate a specific session,
or every session belonging to a specific user, immediately, by deleting or
flagging rows, a capability a stateless signed token does not have without
maintaining a separate denylist, which itself becomes an external store
with its own availability and consistency questions. This makes Database
Session State, or a variant of it, a defensible default for applications
handling sensitive actions specifically because of this revocation
property, stated here as a judgement call weighing security posture
against the latency cost documented in dimension 3, not as a universal
rule that every application should follow.

Session fixation remains a concern independent of storage tier and is worth
restating here because durable storage can tempt a team to reuse the same
session identifier and row across the authentication boundary "since we
already have somewhere durable to keep it." The identifier should be
regenerated at the moment a session's privilege level changes, most
commonly at login, so that a session identifier an attacker fixed before
authentication cannot be hijacked to inherit the authenticated user's
privileges after the fact.

Finally, because session rows can carry sensitive data, routine database
backups now carry that same sensitive data with the same retention window
as the backups themselves, which must be folded into the organization's
existing backup encryption and retention policy rather than treated as an
oversight specific to the sessions table.

## 18. References

- Martin Fowler, *Patterns of Enterprise Application Architecture*,
  Addison-Wesley, 2002, Chapter 17, Session State Patterns, Database
  Session State.
- [Fowler's summary page for Database Session State](https://martinfowler.com/eaaCatalog/databaseSessionState.html), verified 2026-08-11.
- [Fowler's summary page for Client Session State](https://martinfowler.com/eaaCatalog/clientSessionState.html), verified 2026-08-02, referenced by the sibling entry for this pattern family.
- [Fowler's summary page for Serialized LOB](https://martinfowler.com/eaaCatalog/serializedLOB.html), verified 2026-08-11.
- [Spring Session reference documentation, HTTP Session support](https://docs.spring.io/spring-session/reference/http-session.html), verified 2026-08-11.
- [Apache Tomcat 9 Manager configuration reference (PersistentManager, DataSourceStore)](https://tomcat.apache.org/tomcat-9.0-doc/config/manager.html), verified 2026-08-11.
- [PHP manual, session_set_save_handler](https://www.php.net/manual/en/function.session-set-save-handler.php), verified 2026-08-11.
- [ASP.NET Core fundamentals, session and app state](https://learn.microsoft.com/en-us/aspnet/core/fundamentals/app-state), verified 2026-08-11.
- Jones, Bradley, and Sakimura, RFC 7519, *JSON Web Token (JWT)*, https://datatracker.ietf.org/doc/html/rfc7519, referenced by the sibling Client Session State entry for the token-based alternative discussed in dimension 12.
- [RFC 6265, HTTP State Management Mechanism, section 6.1](https://datatracker.ietf.org/doc/html/rfc6265#section-6.1), verified 2026-08-11.

## Code examples

Each example models the pattern's core mechanic, a session table keyed by
identifier with an optimistic-lock version column, standing in for a real
SQL table so the sample runs with no external database dependency. Two
concurrent readers of the same session attempt to write; the version check
lets the first commit succeed and rejects the second as stale, the
mechanism from dimension 7 that prevents the lost-update failure in
dimension 11.

### TypeScript (in-memory stand-in for a sessions table with optimistic locking)

```typescript
interface SessionRow {
  id: string;
  data: string;
  version: number;
  expiresAt: number;
}

class SessionTable {
  private rows = new Map<string, SessionRow>();

  insert(row: SessionRow): void {
    if (this.rows.has(row.id)) {
      throw new Error(`duplicate session id: ${row.id}`);
    }
    this.rows.set(row.id, { ...row });
  }

  selectById(id: string): SessionRow | undefined {
    const row = this.rows.get(id);
    return row ? { ...row } : undefined;
  }

  updateWithVersionCheck(
    id: string,
    newData: string,
    expectedVersion: number,
    newExpiresAt: number,
  ): boolean {
    const current = this.rows.get(id);
    if (!current || current.version !== expectedVersion) {
      return false;
    }
    this.rows.set(id, {
      id,
      data: newData,
      version: current.version + 1,
      expiresAt: newExpiresAt,
    });
    return true;
  }

  deleteExpired(now: number): number {
    let deleted = 0;
    for (const [id, row] of this.rows) {
      if (row.expiresAt < now) {
        this.rows.delete(id);
        deleted += 1;
      }
    }
    return deleted;
  }

  size(): number {
    return this.rows.size;
  }
}

function main(): void {
  const table = new SessionTable();
  const now = Date.now();
  const oneHour = 60 * 60 * 1000;

  table.insert({
    id: "sess-1001",
    data: JSON.stringify({ userId: "user-42", cart: [] }),
    version: 1,
    expiresAt: now + oneHour,
  });

  const readerA = table.selectById("sess-1001");
  const readerB = table.selectById("sess-1001");
  if (!readerA || !readerB) {
    throw new Error("session should exist");
  }

  const requestAOk = table.updateWithVersionCheck(
    "sess-1001",
    JSON.stringify({ userId: "user-42", cart: ["sku-7"] }),
    readerA.version,
    now + oneHour,
  );
  console.log("request A committed:", requestAOk);

  const requestBOk = table.updateWithVersionCheck(
    "sess-1001",
    JSON.stringify({ userId: "user-42", cart: ["sku-9"] }),
    readerB.version,
    now + oneHour,
  );
  console.log("request B rejected, stale version:", !requestBOk);

  const finalRow = table.selectById("sess-1001");
  console.log("final row version:", finalRow?.version, "data:", finalRow?.data);

  const expired = table.deleteExpired(now + 2 * oneHour);
  console.log("reaper deleted expired rows:", expired, "remaining:", table.size());
}

main();
```

### Python (in-memory stand-in for a sessions table with optimistic locking)

```python
import json
import time
from dataclasses import dataclass, replace


@dataclass
class SessionRow:
    id: str
    data: str
    version: int
    expires_at: float


class SessionTable:
    def __init__(self) -> None:
        self._rows: dict[str, SessionRow] = {}

    def insert(self, row: SessionRow) -> None:
        if row.id in self._rows:
            raise ValueError(f"duplicate session id: {row.id}")
        self._rows[row.id] = replace(row)

    def select_by_id(self, session_id: str) -> SessionRow | None:
        row = self._rows.get(session_id)
        return replace(row) if row is not None else None

    def update_with_version_check(
        self, session_id: str, new_data: str, expected_version: int, new_expires_at: float
    ) -> bool:
        current = self._rows.get(session_id)
        if current is None or current.version != expected_version:
            return False
        self._rows[session_id] = SessionRow(
            id=session_id,
            data=new_data,
            version=current.version + 1,
            expires_at=new_expires_at,
        )
        return True

    def delete_expired(self, now: float) -> int:
        expired = [sid for sid, row in self._rows.items() if row.expires_at < now]
        for sid in expired:
            del self._rows[sid]
        return len(expired)

    def size(self) -> int:
        return len(self._rows)


def main() -> None:
    table = SessionTable()
    now = time.time()
    one_hour = 60 * 60

    table.insert(
        SessionRow(
            id="sess-1001",
            data=json.dumps({"user_id": "user-42", "cart": []}),
            version=1,
            expires_at=now + one_hour,
        )
    )

    reader_a = table.select_by_id("sess-1001")
    reader_b = table.select_by_id("sess-1001")
    assert reader_a is not None and reader_b is not None

    request_a_ok = table.update_with_version_check(
        "sess-1001",
        json.dumps({"user_id": "user-42", "cart": ["sku-7"]}),
        reader_a.version,
        now + one_hour,
    )
    print("request A committed:", request_a_ok)

    request_b_ok = table.update_with_version_check(
        "sess-1001",
        json.dumps({"user_id": "user-42", "cart": ["sku-9"]}),
        reader_b.version,
        now + one_hour,
    )
    print("request B rejected, stale version:", not request_b_ok)

    final_row = table.select_by_id("sess-1001")
    print("final row version:", final_row.version if final_row else None)
    print("final row data:", final_row.data if final_row else None)

    expired = table.delete_expired(now + 2 * one_hour)
    print("reaper deleted expired rows:", expired, "remaining:", table.size())


if __name__ == "__main__":
    main()
```

### Go (in-memory stand-in for a sessions table with optimistic locking)

```go
package main

import (
	"encoding/json"
	"fmt"
	"time"
)

type SessionRow struct {
	ID        string
	Data      string
	Version   int
	ExpiresAt time.Time
}

type SessionTable struct {
	rows map[string]SessionRow
}

func NewSessionTable() *SessionTable {
	return &SessionTable{rows: make(map[string]SessionRow)}
}

func (t *SessionTable) Insert(row SessionRow) error {
	if _, exists := t.rows[row.ID]; exists {
		return fmt.Errorf("duplicate session id: %s", row.ID)
	}
	t.rows[row.ID] = row
	return nil
}

func (t *SessionTable) SelectByID(id string) (SessionRow, bool) {
	row, ok := t.rows[id]
	return row, ok
}

func (t *SessionTable) UpdateWithVersionCheck(id, newData string, expectedVersion int, newExpiresAt time.Time) bool {
	current, ok := t.rows[id]
	if !ok || current.Version != expectedVersion {
		return false
	}
	t.rows[id] = SessionRow{
		ID:        id,
		Data:      newData,
		Version:   current.Version + 1,
		ExpiresAt: newExpiresAt,
	}
	return true
}

func (t *SessionTable) DeleteExpired(now time.Time) int {
	deleted := 0
	for id, row := range t.rows {
		if row.ExpiresAt.Before(now) {
			delete(t.rows, id)
			deleted++
		}
	}
	return deleted
}

func (t *SessionTable) Size() int {
	return len(t.rows)
}

func main() {
	table := NewSessionTable()
	now := time.Now()
	oneHour := time.Hour

	type payload struct {
		UserID string   `json:"user_id"`
		Cart   []string `json:"cart"`
	}

	initial, _ := json.Marshal(payload{UserID: "user-42", Cart: []string{}})
	if err := table.Insert(SessionRow{
		ID:        "sess-1001",
		Data:      string(initial),
		Version:   1,
		ExpiresAt: now.Add(oneHour),
	}); err != nil {
		panic(err)
	}

	readerA, _ := table.SelectByID("sess-1001")
	readerB, _ := table.SelectByID("sess-1001")

	dataA, _ := json.Marshal(payload{UserID: "user-42", Cart: []string{"sku-7"}})
	requestAOk := table.UpdateWithVersionCheck("sess-1001", string(dataA), readerA.Version, now.Add(oneHour))
	fmt.Println("request A committed:", requestAOk)

	dataB, _ := json.Marshal(payload{UserID: "user-42", Cart: []string{"sku-9"}})
	requestBOk := table.UpdateWithVersionCheck("sess-1001", string(dataB), readerB.Version, now.Add(oneHour))
	fmt.Println("request B rejected, stale version:", !requestBOk)

	final, _ := table.SelectByID("sess-1001")
	fmt.Println("final row version:", final.Version, "data:", final.Data)

	expired := table.DeleteExpired(now.Add(2 * oneHour))
	fmt.Println("reaper deleted expired rows:", expired, "remaining:", table.Size())
}
```
