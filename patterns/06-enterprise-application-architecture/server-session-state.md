---
name: Server Session State
slug: server-session-state
family: 06-enterprise-application-architecture
category: Session State
aliases: [Server-Side Session, HttpSession Pattern, Distributed Session Store]
first_described: "Fowler 2002"
maturity: canonical
related: [client-session-state, database-session-state, remote-facade, identity-field, coarse-grained-lock]
incompatible_with: []
verified: 2026-08-02
---

# Server Session State

## 1. Name, aliases, and lineage

The canonical name is Server Session State. It is one of three named session
state strategies in Martin Fowler, *Patterns of Enterprise Application
Architecture*, Addison-Wesley, 2002, chapter 17, "Distribution Strategies",
alongside Client Session State and Database Session State. The catalog entry
for it defines the pattern in one line as a mechanism that "keeps the session
state on a server system in a serialized form"
([martinfowler.com/eaaCatalog/serverSessionState.html](https://martinfowler.com/eaaCatalog/serverSessionState.html),
verified 2026-08-02). The book chapter itself expands this into the trade-off
against the other two strategies, which is the substance most people actually
mean when they invoke the pattern name.

Fowler did not invent the underlying mechanism. He named and catalogued a
practice that predates the book by several years, most visibly the
`HttpSession` object in the Java Servlet specification, which shipped in
Servlet 2.0 in 1999. The pattern's practical vocabulary comes largely from
that specification, terms such as session ID, session cookie, session
timeout, and session invalidation. Every later platform, ASP.NET Session
State, PHP's `$_SESSION` superglobal, Rails' `ActionDispatch::Session`, and
Express's `express-session` middleware, uses the same vocabulary because they
are all independent implementations of the identical idea Fowler catalogued.
A token handed to the client that resolves, on the server, to a chunk of
per-user state kept in memory or in a shared store between requests.

Two aliases are worth naming because they point at two different
implementation shapes people conflate. **HttpSession Pattern** refers to the
in-process variant, where the session data lives in the memory of the
application server that handled the request, keyed by session ID, and does
not automatically survive a restart or become visible to a sibling server.
**Distributed Session Store** refers to the externalised variant, where the
session data lives in a shared store, most commonly Redis or Memcached,
reachable by every application server in a cluster, so any server can service
any request for a given session ID. Both are Server Session State by
Fowler's definition, because in both cases the state lives on a server system
rather than being round-tripped to the client on every request. The
distinction between them is an implementation variant covered in dimension
8, not a difference in which pattern is in use.

The pattern is sometimes described loosely as "sticky sessions", but this
conflates the state-storage strategy with a load-balancing strategy. Sticky
sessions, also called session affinity, is a load balancer configuration
that routes every request from one client to the same backend instance for
the life of the session
([AWS Elastic Load Balancing sticky sessions documentation](https://docs.aws.amazon.com/elasticloadbalancing/latest/classic/elb-sticky-sessions.html),
verified 2026-08-02). Sticky sessions is one way to make in-process Server
Session State work in a cluster, but it is not the pattern itself, and a
distributed session store makes sticky sessions unnecessary because any
server can resolve the session ID against the shared store.

## 2. Problem and context

HTTP is stateless. Each request arrives at the server with no memory of the
request before it, and the connection that carried it may already be closed
by the time the response goes out. A shopping cart, a partially filled
multi-step form, an authenticated identity, the current page of a paginated
search result, all of these are conversations that span more than one
request, and HTTP gives the application nothing to hang that conversation on.

The concrete situation that creates the need looks like this in a running
system. A user logs in on request one. On request two, three requests later,
the application needs to know who this user is without asking them to
re-authenticate, and it needs to know it cheaply, on every single request,
including static asset requests, API calls made from client-side JavaScript,
and background polling. The naive fix, re-sending the full identity and cart
contents as request parameters on every call, works for a toy application and
breaks down the moment the state gets larger than a few fields or the moment
any of it must not be trusted to a client that could tamper with it, such as
an admin flag or a price that was validated once and must not be
re-validated from a value the browser supplies.

The context in which Server Session State is the right answer has three
parts, and each one narrows the applicability further. First, the
conversation genuinely spans multiple HTTP requests from the same client
identity, meaning the state is per-user or per-visit, not global. Second, the
data being held is either too large, too sensitive, or too likely to be
tampered with to be sent to the client and trusted back verbatim, which rules
out simply storing the entire state in a signed or encrypted cookie. Third,
the deployment has, or can add, a mechanism for a request to find the right
server-side state regardless of which physical server instance receives the
request, because the pattern only works cleanly when session lookup is
possible from any request-handling process. When that third condition is
absent, teams reach for sticky sessions as a workaround, which is itself a
symptom that the pattern's assumptions have started to strain against a
horizontally scaled deployment, a tension explored in dimension 11.

## 3. Forces

Server Session State sits at the intersection of several forces that pull in
different directions, and the pattern's shape is a specific resolution of
that tension, not a free lunch.

**Latency versus statelessness.** Storing session data server-side means
every request that needs it must perform a lookup, whether that lookup is an
in-process hash map read, taking microseconds, or a network round trip to a
distributed cache, taking low single-digit milliseconds. Client Session
State avoids this lookup entirely by shipping the state in the request
itself, at the cost of larger request and response payloads on every call.
For state accessed on nearly every request, such as an authenticated
identity, the server-side lookup usually wins on latency because the payload
avoided is larger than the lookup cost, but for state accessed rarely the
balance can flip.

**Scalability versus simplicity.** In-process session storage is the
simplest possible implementation, a hash map keyed by session ID living in
the same process as the request handler. It has zero additional
infrastructure and zero additional network hops. It also does not scale
horizontally without either sticky routing, which creates hot spots and
fragile failover, or a shared store, which reintroduces the network hop the
in-process design was trying to avoid and adds an entire additional system
that must itself be available, monitored, and capacity-planned.

**Consistency versus availability.** When session state lives in a single
shared store, every application server sees a consistent view of it, which
matters when a user's requests can land on any server, as they do behind a
typical load balancer with no session affinity. That consistency has a
price. The shared store becomes a dependency whose outage now takes down
every application server's ability to serve authenticated traffic, exactly
the coarse-grained-lock and single-point-of-failure risk that a purely
stateless request-handling tier was designed to avoid. Some deployments
choose eventual consistency, tolerating a stale read of session data
immediately after a write for the sake of availability, which is a real
trade a team must consciously choose, not one the pattern makes for them.

**Cost versus data locality.** Every megabyte of session data multiplied by
every concurrent user is memory or storage the operator pays for
continuously, whether that user is actively making requests or has simply
left a browser tab open. Session data has a natural expiry, unlike a
customer record, and the forces here favour aggressive timeouts and small
per-session payloads, which pushes teams toward storing only an identity
token and a small set of frequently needed flags in the session, with the
bulk of durable state in the primary database instead.

**Team topology and operability.** A shared session store is a piece of
shared infrastructure that every service touching authenticated requests now
depends on, which raises the operational bar. Someone owns its capacity,
its failover, its patching, and its on-call rotation. A team without the
operational maturity to run that infrastructure reliably will find that the
session store becomes the least reliable part of an otherwise reliable
system, a failure mode observed often enough that it is treated below as a
named failure mode rather than a hypothetical.

The pattern favours correctness and small per-request payloads at the cost of
adding server-side infrastructure and a hard dependency on that
infrastructure's availability. It sacrifices the simplicity of a fully
stateless request-handling tier, which is the price Client Session State
does not pay, at the benefit of never trusting sensitive or bulky state back
from a client that could tamper with it, which is the price Client Session
State does pay.

## 4. Applicability and non-applicability

### When to reach for it

- The session payload contains data that must not be exposed to or trusted
  from the client, such as authorization decisions, cart pricing already
  validated server-side, or a step-by-step wizard's internal validation
  state.
- The session payload is large enough, commonly beyond a few kilobytes once
  serialized, that repeating it on every request or response would
  meaningfully inflate bandwidth, which matters most on mobile clients and
  high-request-volume APIs.
- The deployment already has, or is prepared to operate, a mechanism for any
  server instance to resolve a session ID to the same state, whether that is
  a shared cache, a database, or sticky routing accepted as an explicit
  trade.
- The application needs to invalidate a session instantly and centrally, for
  example forcing a logout across every device on a password change, which
  is straightforward with server-held state and requires an additional
  revocation list when the state instead lives entirely with the client.
- Regulatory or security requirements demand that sensitive session data
  never leave the server's trust boundary in any form, even encrypted,
  because an encrypted client-held token that is copied still lets a
  replay attack succeed until expiry, whereas a server-held session can be
  revoked the instant the theft is discovered.

### When not to reach for it

- The application is deployed as a set of independently scaling, horizontally
  replicated stateless functions, such as a serverless request handler with
  no persistent process and no colocated cache, where adding a session store
  reintroduces exactly the state coordination the stateless deployment model
  exists to avoid. Client Session State, most often a signed JWT, is the
  better fit here because verification needs no round trip.
- The session payload is small, non-sensitive, and safe to trust back from
  the client when signed, such as a UI preference like a collapsed sidebar
  state or a locale choice. Server Session State for data this cheap and
  this low-stakes is added infrastructure paying for a threat model that
  does not exist.
- The system must survive a total outage of every application server and
  resume sessions without loss, and the team is unwilling to also make the
  session store itself durable and highly available, because at that point
  the session store inherits every reliability requirement of the primary
  database without necessarily getting the operational investment a primary
  database receives.
- The interaction is a single request with no follow-up, such as a one-shot
  webhook receiver or a public read-only API with no per-caller state,
  where there is no conversation to hold state for in the first place.
- Extremely high read and write session churn at a scale where even a fast
  in-memory store like Redis becomes the throughput bottleneck of the whole
  system, a scale at which teams typically shift some session fields into
  the request's own signed token and keep only the minimum in the shared
  store, a hybrid covered under implementation variants.

## 5. Structure

The participants in Server Session State are consistent across every
platform implementation, even though the class and interface names differ.

- **Session identifier.** An opaque, high-entropy token that names a
  session without revealing or encoding any of its content. It is the only
  piece of session-related data the client ever holds. Its confidentiality
  and unguessability are the entire security boundary of the pattern, a
  point returned to in dimension 17.
- **Session store.** The place the identifier resolves to actual data. This
  can be a hash map in the memory of the process handling the request, a
  distributed cache such as Redis or Memcached shared by every process, or a
  row in a relational or document database. The store is responsible for
  create, read, update, delete, and expire operations keyed by the session
  identifier.
- **Session object or context.** The in-request representation the
  application code actually interacts with, typically a key-value bag
  scoped to the current request, backed transparently by the session store.
  This is `HttpSession` in Java, `ISession` in ASP.NET Core, `req.session`
  in Express, `$_SESSION` in PHP, and `session` in Rails controllers.
- **Session transport mechanism.** How the identifier travels between client
  and server. A cookie set with `HttpOnly`, `Secure`, and `SameSite`
  attributes is the dominant mechanism today. URL rewriting, where the
  identifier is appended as a query parameter or path segment, is a legacy
  fallback used when cookies are unavailable, still specified as an
  alternative in the Jakarta Servlet specification
  ([Jakarta Servlet 6.1 specification, section 7](https://jakarta.ee/specifications/servlet/6.1/jakarta-servlet-spec-6.1.html),
  verified 2026-08-02).
- **Session lifecycle manager.** The component, usually built into the
  framework, that creates a new session and identifier on first contact,
  extends the session's expiry on activity, and invalidates or expires the
  session on explicit logout or on a configured idle timeout. The Jakarta
  Servlet specification documents a default 30-minute idle timeout as the
  container-managed default, with `HttpSession.invalidate()` for explicit
  termination
  ([Jakarta Servlet 6.1 specification, section 7](https://jakarta.ee/specifications/servlet/6.1/jakarta-servlet-spec-6.1.html),
  verified 2026-08-02).

The relationships. The client holds only the session identifier, transported
via cookie or URL parameter on every request. The application server, on
receiving a request, extracts the identifier and asks the session store to
resolve it into a session object. The application code reads from and writes
to that session object during request handling. At the end of the request,
the lifecycle manager persists any changes back to the store, if the
mutation was not already written through immediately, and refreshes the
session's expiry clock.

## 6. ASCII structure diagram

```
+-----------+        session id only         +-------------------+
|  Browser  |  (cookie: SESSIONID=abc123)     |  App Server A      |
|  or API   |-------------------------------->|                    |
|  Client   |                                 |  request handler   |
+-----------+                                 |        |           |
                                               |        v           |
                                               |  session lifecycle |
                                               |  manager           |
                                               +--------+-----------+
                                                        |
                                              resolve(abc123)
                                                        |
                                                        v
                                             +----------------------+
                                             |   Session Store       |
                                             |  (Redis / Memcached /  |
                                             |   in-process map /     |
                                             |   database table)      |
                                             |                        |
                                             |  abc123 -> {           |
                                             |    userId: 42,         |
                                             |    cartId: "c-91",     |
                                             |    role: "admin"       |
                                             |  }                     |
                                             +----------+-------------+
                                                        ^
                                             resolve(abc123)
                                                        |
                                               +--------+-----------+
+-----------+                                 |  App Server B      |
|  Browser  |  same cookie, next request      |                    |
|  or API   |-------------------------------->|  request handler   |
|  Client   |                                 +--------------------+
+-----------+
```

The diagram makes the load-balancing implication explicit. Server A and
Server B are different processes, possibly on different physical hosts,
handling two consecutive requests for the same browser session. Because the
session data lives in the shared store and not inside either process, both
servers resolve the identical session state, and the load balancer is free
to route the second request to either server without any affinity
requirement. This is the horizontally scalable variant. The in-process
variant collapses the store into Server A's own memory, which then requires
either sticky routing back to Server A specifically or accepts that Server B
will not see the session at all.

## 7. Dynamics

```
Client            LoadBalancer        AppServer          SessionStore

  |  POST /login        |                  |                    |
  |--------------------->|                  |                    |
  |                      |  route request   |                    |
  |                      |----------------->|                    |
  |                      |                  |  authenticate      |
  |                      |                  |  generate SID      |
  |                      |                  |------------------->|  CREATE
  |                      |                  |                    |  sid -> {userId}
  |                      |                  |<-------------------|  ack
  |                      |  Set-Cookie: SID |                    |
  |                      |<-----------------|                    |
  |  Set-Cookie: SID     |                  |                    |
  |<---------------------|                  |                    |
  |                      |                  |                    |
  |  GET /cart           |                  |                    |
  |  Cookie: SID         |                  |                    |
  |--------------------->|                  |                    |
  |                      |  route request   |                    |
  |                      |  (any instance)  |                    |
  |                      |----------------->|                    |
  |                      |                  |  READ sid          |
  |                      |                  |------------------->|
  |                      |                  |<-------------------|
  |                      |                  |  {userId, cartId}  |
  |                      |                  |  render response   |
  |                      |<-----------------|                    |
  |  200 OK, cart HTML   |                  |                    |
  |<---------------------|                  |                    |
  |                      |                  |                    |
  |  POST /logout        |                  |                    |
  |--------------------->|----------------->|                    |
  |                      |                  |  invalidate sid    |
  |                      |                  |------------------->|  DELETE sid
  |                      |                  |<-------------------|
  |  Set-Cookie: SID=;   |                  |                    |
  |  Max-Age=0           |                  |                    |
  |<---------------------|------------------|                    |
  |                      |                  |                    |
  |  ... idle 30 min ... |                  |                    |
  |                      |                  |                    |  TTL expiry
  |                      |                  |                    |  auto-DELETE
```

Three lifecycle transitions are worth naming precisely because they are
where most bugs live. Creation happens exactly once, on the first request
that calls the framework's "get or create session" entry point, and it must
generate the identifier with a cryptographically secure random source, not
an incrementing counter or a predictable hash, a point returned to in
dimension 17. Read-and-refresh happens on every subsequent request and
typically also slides the store entry's time-to-live forward, which is why
this is called a sliding expiration in most documentation, distinct from an
absolute expiration that counts from creation regardless of activity.
Termination happens either explicitly, through a logout action that deletes
the store entry and clears the client-held cookie, or implicitly, through
the store's own time-to-live mechanism expiring an entry nobody touched
within the idle window. A session that is only cleared client-side, by
deleting the cookie, but never deleted server-side, remains a live,
resolvable session as far as the store is concerned until its own timeout,
which is the single most common mistake in hand-rolled implementations of
this pattern.

## 8. Implementation variants

**In-process, single instance.** The simplest and fastest variant. Session
data lives in a hash map or equivalent structure inside the same process
handling requests. There is no network hop, and read and write latency is
effectively zero. It works correctly only when every request for a given
session is guaranteed to reach the same process, which in practice means a
single-instance deployment, or a load balancer configured for sticky
sessions such as AWS's classic load balancer cookie-based affinity
([AWS ELB sticky sessions documentation](https://docs.aws.amazon.com/elasticloadbalancing/latest/classic/elb-sticky-sessions.html),
verified 2026-08-02). A process restart or crash silently loses every
active session held in that process, forcing every affected user to
re-authenticate.

**Distributed cache-backed.** Session data lives in a shared, network-
addressable store, most commonly Redis, reached by every application
instance in the cluster. This removes the sticky-routing requirement
entirely and survives an individual application server restart, because the
data never lived in that server's memory. The trade is a network round trip
per session access and a new hard dependency. If the cache is unreachable,
sessions become unreadable across the entire fleet simultaneously, not just
on one instance. `express-session`, the dominant session middleware for
Node.js, documents its own default `MemoryStore` as explicitly unfit for
this reason, stating it "will leak memory under most conditions, does not
scale past a single process, and is meant for debugging and developing",
while listing production-grade store adapters such as `connect-redis`,
`connect-mongo`, and `connect-pg-simple`
([expressjs/session README](https://github.com/expressjs/session), verified
2026-08-02).

**Database-backed, distinct from Database Session State.** Session data is
written to a relational or document database table, keyed by session
identifier, with a background job or database-native TTL feature to expire
old rows. This is functionally similar to a distributed cache-backed store
but trades the cache's speed for the database's durability and existing
operational tooling, which is attractive to teams that already run a
reliable database and would rather not add Redis purely for sessions.
Fowler's own catalog distinguishes this database-persisted flavour of the
idea as a related but separately named pattern, Database Session State,
when the session data is treated as durable business state rather than a
disposable cache entry
([martinfowler.com/eaaCatalog/databaseSessionState.html](https://martinfowler.com/eaaCatalog/databaseSessionState.html),
verified 2026-08-02).

**Framework-managed distributed cache, first-party.** ASP.NET Core wires
this variant directly into its dependency injection container. An
`IDistributedCache` implementation, backed by SQL Server, Redis, or an
in-memory cache for development, sits underneath the `ISession` abstraction
the application code actually uses, and the framework handles serialization,
the session cookie, and sliding expiration configuration
([Microsoft Learn, "Session and state management in ASP.NET Core", section on Session state](https://learn.microsoft.com/en-us/aspnet/core/fundamentals/app-state),
verified 2026-08-02). This variant is notable because the application code
is identical regardless of which backend is configured, an example of the
Remote Facade idea applied at the framework level. Callers depend on the
`ISession` interface, never on the storage technology behind it.

**Hybrid, minimal server session plus signed client token.** For systems
under very high session-store load, or serverless deployments where a
persistent connection to a shared cache is expensive to maintain, some
teams keep only a small, frequently invalidated set of fields, most often
an authorization decision or a token version number, in the server-side
store, while the bulk of user context travels in a signed client-held token
such as a JWT. This is not a pure instance of Server Session State, since
part of the state genuinely lives with the client, but it is common enough
in practice to be worth naming, and it is best understood as Server Session
State applied selectively to only the data that actually needs server-side
revocability, with Client Session State handling the rest.

## 9. Known production uses

**Java Servlet containers, `HttpSession`.** Every Java Servlet-compliant
application server, including Apache Tomcat, Eclipse Jetty, and the
application servers underlying Spring Boot's embedded server, implements
`HttpSession` as specified by the Jakarta Servlet specification, giving
every Java web application a built-in server-side session abstraction with
cookie-based tracking, a configurable default idle timeout, and an explicit
`invalidate()` method
([Jakarta Servlet 6.1 specification, section 7](https://jakarta.ee/specifications/servlet/6.1/jakarta-servlet-spec-6.1.html),
verified 2026-08-02).

**ASP.NET Core `ISession` with a distributed cache backend.** Microsoft's
official ASP.NET Core documentation describes session state as
non-durable, in-memory or distributed-cache-backed data tied to a session
cookie, and explicitly recommends configuring a distributed cache such as
Redis or SQL Server for any deployment running more than one server
instance, precisely to satisfy the shared-resolvability requirement named
in dimension 2
([Microsoft Learn, "Session and state management in ASP.NET Core"](https://learn.microsoft.com/en-us/aspnet/core/fundamentals/app-state),
verified 2026-08-02).

**Node.js and Express, `express-session` with `connect-redis`.** The
`express-session` package is the standard middleware for adding
server-side sessions to Express applications, and its own documentation
directs production deployments away from the bundled in-memory store toward
a persistent, shared backend, listing `connect-redis` as one of over fifty
compatible store adapters that satisfy that requirement
([expressjs/session README, "Compatible Session Stores"](https://github.com/expressjs/session),
verified 2026-08-02).

**AWS Elastic Load Balancing, sticky sessions.** While not itself a session
store, AWS documents a first-party cookie-based sticky session feature for
its Classic Load Balancer specifically to support applications built on
in-process Server Session State, binding a user's requests to one backend
instance for the life of a load-balancer-generated `AWSELB` cookie or an
application-controlled cookie, which is direct evidence that in-process
Server Session State is common enough in production to warrant dedicated
load balancer functionality
([AWS ELB sticky sessions documentation](https://docs.aws.amazon.com/elasticloadbalancing/latest/classic/elb-sticky-sessions.html),
verified 2026-08-02).

## 10. Consequences

**Positive.**

- Sensitive or bulky data never crosses the network to the client beyond an
  opaque identifier, closing off an entire class of tampering and payload-
  size problems that Client Session State must otherwise solve with signing
  and encryption.
- Sessions can be revoked instantly and centrally, which is essential for
  security-sensitive flows such as a forced logout after a password reset
  or a detected credential leak, without needing a revocation list layered
  on top of an otherwise self-contained token.
- Application code interacts with a simple, familiar key-value abstraction
  regardless of the underlying storage technology, which keeps request
  handlers readable and lets the storage backend be swapped, from
  in-process memory in development to Redis in production, with no code
  change in frameworks that provide this abstraction, such as ASP.NET
  Core's `ISession`.
- Per-request payload size stays small, since only the identifier travels
  repeatedly, which matters at scale for both bandwidth cost and the
  latency of parsing and validating a large signed token on every request.

**Negative.**

- The session store becomes a new, shared, stateful dependency in what
  might otherwise be a fully stateless, horizontally scalable
  request-handling tier, and its availability now bounds the availability
  of every request that touches a session.
- Horizontal scaling requires either operating a shared, low-latency store
  reachable from every instance, adding real infrastructure and its own
  failure modes, or accepting sticky routing, which creates uneven load
  distribution and awkward failover when the sticky instance dies mid-
  session.
- Memory or storage cost is paid continuously for every logged-in user,
  including idle users who have simply left a tab open, in contrast to
  Client Session State, where the cost of holding state is fully shifted
  to the client.
- Serverless and edge-function deployment models, which favour short-lived,
  stateless invocations with no persistent process and often no colocated
  low-latency cache, are structurally at odds with this pattern, forcing a
  network round trip to an external store on every session touch.

## 11. Failure modes and misuse

**The unstuck instance.** Symptom. Users are randomly logged out or see
another user's cart under load. Cause. An in-process session store deployed
behind a load balancer with no sticky-session configuration, so consecutive
requests from one browser land on different application instances, each
holding its own, different, empty session for that identifier. Fix. Either
configure genuine session affinity at the load balancer, as documented for
AWS's Classic Load Balancer
([AWS ELB sticky sessions documentation](https://docs.aws.amazon.com/elasticloadbalancing/latest/classic/elb-sticky-sessions.html),
verified 2026-08-02), or, the more durable fix, migrate to a shared,
distributed-cache-backed store so any instance resolves the same session.

**The unbounded store.** Symptom. Memory usage on application servers
climbs steadily and never falls, eventually causing out-of-memory restarts.
Cause. The in-process store is being used in production despite an explicit
upstream warning against it, or a custom store implementation never
actually expires entries, only removing them on explicit logout, so every
abandoned session, which is the majority of sessions in most consumer
applications, accumulates forever. `express-session`'s own documentation
names this exact leak as the reason its bundled `MemoryStore` is unfit for
production
([expressjs/session README](https://github.com/expressjs/session), verified
2026-08-02). Fix. Configure a real time-to-live on every session write,
whether via a distributed cache's native TTL feature or a scheduled sweep
job against a database-backed store, and verify with a load test that idle
sessions actually disappear.

**The single point of failure disguised as a cache.** Symptom. An entire
fleet of application servers starts returning authentication errors or 500s
simultaneously, with no code deploy having happened. Cause. The shared
session store, most often Redis, became unreachable or exhausted its
connection pool, and because every application instance depends on the
same store for every authenticated request, the store's outage becomes a
full-application outage rather than a degraded feature. Fix. Treat the
session store with the same operational rigor as the primary database,
meaning monitored capacity, connection pool limits tuned to the actual
instance count, and a documented fallback behaviour, such as degrading to
anonymous access for read-only endpoints, rather than a hard failure, when
the store is briefly unavailable.

**The logout that did not log out.** Symptom. A user who clicked logout on
one device is still authenticated on another device, or a stolen session
token remains valid long after the theft is discovered. Cause. Session
identifiers being treated as long-lived, or "logout" only clearing the
client-side cookie without deleting the corresponding server-side entry,
leaving the identifier fully valid to anyone who has a copy of it until its
natural idle timeout elapses. Fix. Logout must delete the server-side
session entry, not merely clear the client cookie, and any
security-sensitive event, a password change, a role change, a detected
anomaly, should trigger deletion of every session associated with that
user's identity, not just the current one.

**The silently corrupted session.** Symptom. Session data intermittently
appears to belong to the wrong user, specifically after a deployment.
Cause. The session serialization format changed between application
versions, for example a field was renamed or its type changed, and an old
session entry, still live in the shared store from before the deploy, now
deserializes into a different or corrupted shape under the new code, an
instance of the same versioning hazard the Serialized LOB pattern names for
persisted domain objects. Fix. Version the session payload's schema
explicitly, and have the deserialization path treat an unrecognised or
malformed session as invalid rather than partially trusting it, forcing a
clean re-authentication instead of silently propagating corrupted state.

## 12. Trade-off matrix

| Force | Server Session State | Client Session State | Database Session State |
|---|---|---|---|
| Per-request payload size | Small, identifier only | Larger, full state signed and sent each time | Small, identifier only |
| Sensitive data exposure to client | None beyond opaque ID | Full state visible unless encrypted, and encryption keys become critical infrastructure | None beyond opaque ID |
| Horizontal scaling without extra infra | Requires sticky routing or a shared store | Naturally stateless, no server coordination needed | Requires a shared, reachable database |
| Instant central revocation | Native, delete the entry | Requires a separate revocation list layered on top | Native, delete the row |
| New infrastructure dependency | Yes, a cache or in-process store | No, the client carries the state | Yes, but usually infrastructure that already exists |
| Cost per idle logged-in user | Continuous, memory or store cost | Zero on the server | Continuous, storage cost, typically cheaper per byte than a cache |
| Durability across a server restart | Depends on variant, in-process loses state, distributed cache does not | Full, state lives with the client | Full, state is persisted |
| Fit for stateless serverless functions | Poor, forces an external round trip per invocation | Strong, verification needs no round trip | Moderate, still a network round trip but to infrastructure serverless functions already use |

## 13. Related and incompatible patterns

**Client Session State** is the direct alternative named in the same
Fowler chapter, and the two are best understood as opposite resolutions of
the same force, whether the state lives with the server or travels with the
client. They compose in the hybrid variant described in dimension 8, where
a small, revocable core lives server-side and the rest travels signed with
the client.

**Database Session State** is closely related and sometimes conflated with
Server Session State, since both keep data on a server system. Fowler
distinguishes them by durability intent. Database Session State treats the
session as persisted business data surviving indefinitely, most commonly
because the business wants to resume an abandoned shopping cart days later,
while Server Session State treats the session as short-lived, disposable
cache data meant to expire
([martinfowler.com/eaaCatalog/databaseSessionState.html](https://martinfowler.com/eaaCatalog/databaseSessionState.html),
verified 2026-08-02). A cache-backed Server Session State implementation
that never expires entries has, in practice, drifted into being Database
Session State without anyone deciding that on purpose, which is itself a
form of the misuse named in dimension 11.

**Remote Facade** relates through the framework-managed variant in
dimension 8. Session abstractions like ASP.NET Core's `ISession` are
themselves a small facade over a swappable distributed cache
implementation, letting application code depend on a stable interface while
the storage technology behind it changes.

**Identity Field** composes with Server Session State whenever the session
payload references a domain object by its primary key rather than
embedding a full serialized copy of that object, which is the recommended
practice precisely because it avoids the stale-data and serialization-
version hazards named in dimension 11. The session stores a plain user
identifier, and every request re-fetches the current user record from the
database using that identity field, rather than trusting a snapshot that
may be minutes or hours stale.

**Coarse-grained Lock** becomes relevant when session state is used to
coordinate access to a shared resource across multiple requests from the
same user, for example holding a lock reference in the session while a
multi-step wizard is in progress, though this usage is uncommon and
generally discouraged, since a session that never properly expires, per the
failure mode in dimension 11, can leave a coarse-grained lock held
indefinitely.

**Incompatible with a purely stateless serverless request model** in the
strict sense that the two cannot both be true of the same request path
without a compromise. A function invocation with no persistent process and
no colocated cache must reach out over the network to any Server Session
State store on every single invocation, which is exactly the coordination
cost the stateless deployment model is chosen to avoid, so most serverless-
first architectures deliberately choose Client Session State instead, or
accept the round trip as a conscious, priced trade-off.

## 14. Refactoring path in and out

**Introducing Server Session State into code that currently has none.**
Start by identifying every piece of per-user, per-request state currently
being re-derived on each request, most often re-parsed from request
parameters or re-fetched from the database with no caching. Choose the
smallest viable payload. An authenticated user's identifier and role are
almost always the entire justification for the pattern, and everything else
should be re-fetched fresh from the primary data store on each request
using that identifier, per the Identity Field composition in dimension 13,
rather than cached wholesale into the session. Introduce the framework's
built-in session abstraction, `HttpSession`, `ISession`,
`express-session`, rather than hand-rolling a cookie-and-map
implementation, since the built-in versions already handle the identifier
generation entropy, cookie attribute defaults, and expiry semantics
correctly, three areas covered under security implications in dimension 17
that are easy to get subtly wrong by hand. Start in-process during
development, then switch the store's backend to a distributed cache before
the first deployment behind more than one application instance, since
retrofitting that switch after users depend on sticky routing is a much
larger, higher-risk migration than choosing the distributed backend from
day one.

**Removing Server Session State once it stops earning its place.** This
happens most often when a system migrates toward a stateless, horizontally
scaled or serverless architecture, or when the session payload has grown to
contain almost nothing but an identity claim that a signed token could
carry just as well. The safe sequence is to first audit every field
currently stored in the session and classify each one as either safe to
trust back from the client when signed, meaning it moves into a JWT or
equivalent, or genuinely requiring server-side revocability, meaning it
must stay, which in a well-maintained system is usually a very small set,
often just a token version number used to invalidate all of a user's
tokens at once. Ship the client-token path alongside the existing session
path behind a feature flag, verify parity on a subset of traffic, and only
then remove the session store dependency, decommissioning it after
confirming, via the observability signals in dimension 16, that session
store traffic has genuinely dropped to zero rather than merely appearing to
because of a caching layer masking continued reads.

## 15. Testing and verification

Server Session State makes request handler logic that merely reads and
writes session fields trivial to unit test, because the session object in
every mainstream framework can be substituted with an in-memory test double
that requires no network and no real store, isolating the test from
infrastructure entirely. What becomes harder to test is everything that
depends on the session's lifecycle rather than its content. Expiry
behaviour, concurrent-request race conditions on the same session, and
cross-instance resolvability all require either an integration test against
a real store instance, commonly a disposable containerized Redis for the
duration of a test suite run, or a carefully constructed fake store that
deliberately reimplements the store's TTL and concurrency semantics rather
than trivially returning stubbed values.

Three test categories are worth naming explicitly because they catch the
failure modes in dimension 11 before production does. An expiry test
advances a fake clock or configures a very short TTL and asserts that a
session genuinely becomes unresolvable after the configured idle period,
not merely that a timestamp field was set correctly. A cross-instance test,
run against a real shared store rather than an in-process fake, writes a
session from one simulated application instance and reads it back from a
second, independently configured instance, which is the only reliable way
to catch a configuration mistake, such as two instances pointed at
different Redis databases, that a single-instance test suite structurally
cannot detect. A serialization-compatibility test, run whenever the shape
of session data changes, deserializes a session payload written by the
previous application version and asserts the new code either reads it
correctly or rejects it cleanly, rather than corrupting it, directly
targeting the versioning failure mode named in dimension 11.

## 16. Observability signals

A healthy Server Session State deployment shows a session store hit rate
close to one hundred percent for reads, meaning nearly every session lookup
finds an entry rather than falling through to a fresh, unauthenticated
path, with a small, steady background rate of misses attributable only to
genuinely expired or newly created sessions. Store read and write latency,
tracked as a percentile distribution rather than an average, should sit
consistently in the low single-digit milliseconds for an in-memory backend
like Redis. A rising tail latency, especially p99 climbing while p50 stays
flat, is usually the earliest signal of connection pool exhaustion or
store-side memory pressure, well before the store becomes fully
unavailable. Session count over time, both total active sessions and the
rate of new session creation versus the rate of expiry, is worth graphing
directly. A steadily rising total with a flat or falling expiry rate is the
exact signature of the memory-leak failure mode in dimension 11, visible on
a dashboard long before an out-of-memory crash makes it visible in an
incident.

A failing instance looks different depending on the failure mode. Store
unavailability shows as a synchronized spike in error rate and latency
across every application instance simultaneously, in contrast to a single
misbehaving instance, which is the signature of an in-process store with a
sticky-routing misconfiguration rather than a shared-store outage.
Authentication error rate climbing without a corresponding deploy or
credential rotation is the practical, user-facing symptom of both the
random-logout failure mode and the store-outage failure mode named in
dimension 11, and distinguishing between them in an incident requires
exactly the store hit-rate and latency signals described above, which is
why they are worth instrumenting before an incident rather than adding them
during one.

## 17. Security and privacy implications

The session identifier is the entire security boundary of this pattern, and
every implication follows from that single fact. It must be generated with
a cryptographically secure random source and carry enough entropy that
guessing or brute-forcing a valid identifier is computationally infeasible.
A sequential or otherwise predictable identifier turns the pattern into an
open door, since anyone who can guess or observe one valid identifier can
impersonate that session's owner completely, with no further credentials
required. The identifier's transport matters as much as its generation. A
session cookie should carry the `HttpOnly` attribute, preventing client-side
script from reading it and closing off the most common cross-site-scripting
exfiltration path, the `Secure` attribute, which stops it from ever being sent over
plain HTTP, and an appropriate `SameSite` attribute, mitigating cross-site
request forgery by restricting when the browser attaches the cookie to
cross-origin requests.

Because the session object is, by design, a place developers reach for
convenient storage, it accumulates data over time in ways that were never
explicitly reviewed for sensitivity, such as a debugging field, an entire
fetched user record instead of just its identifier, or an internal service
token. Each of these expands the session store's own attack surface and
the blast radius of the store itself being compromised or improperly
accessed by an operator, which argues strongly for the minimal-payload
discipline named in dimension 14, storing an identity reference and
re-fetching the rest, rather than a full cache of everything the
user's requests might touch.

Fixation and hijacking are the two named attack classes specific to this
pattern. Session fixation is an attack where an adversary tricks a victim
into using a session identifier the adversary already knows, most often by
setting it before authentication, then waits for the victim to log in under
that identifier and inherits their authenticated session. The standard
mitigation, implemented by essentially every mainstream framework's login
flow, is to issue a brand-new session identifier at the moment of
successful authentication, discarding whatever pre-login identifier
existed. Session hijacking is the theft of a valid, already-authenticated
identifier, through network interception on an unencrypted connection,
through cross-site scripting reading a cookie that lacks `HttpOnly`, or
through a device left unattended. The mitigations are transport encryption,
the cookie attributes described above, reasonable idle timeouts that bound
the window of usefulness for a stolen identifier, and, for
high-sensitivity applications, binding a session additionally to
characteristics like a device fingerprint or IP range, accepting the
resulting friction for legitimate users on network changes as a deliberate
trade-off rather than an accident.

Finally, session data is personal data under most privacy regimes, since it
routinely contains an identity reference and behavioural context, which
means retention limits matter for compliance, not only for the memory-leak
operability reason named in dimension 11. A session store with no enforced
expiry is also a growing, unaudited store of personal data with no
retention justification, a fact worth stating plainly because the same
technical fix, a correctly configured time-to-live on every entry, serves
both concerns at once.

## 18. References

- Martin Fowler, *Patterns of Enterprise Application Architecture*,
  Addison-Wesley, 2002, chapter 17, "Distribution Strategies". Catalog entry
  for Server Session State at
  [martinfowler.com/eaaCatalog/serverSessionState.html](https://martinfowler.com/eaaCatalog/serverSessionState.html),
  verified 2026-08-02.
- Martin Fowler, *Patterns of Enterprise Application Architecture*,
  Addison-Wesley, 2002, chapter 17. Catalog entry for the related Database
  Session State pattern at
  [martinfowler.com/eaaCatalog/databaseSessionState.html](https://martinfowler.com/eaaCatalog/databaseSessionState.html),
  verified 2026-08-02.
- Jakarta Servlet Specification, version 6.1, section 7, "Sessions",
  [jakarta.ee/specifications/servlet/6.1/jakarta-servlet-spec-6.1.html](https://jakarta.ee/specifications/servlet/6.1/jakarta-servlet-spec-6.1.html),
  verified 2026-08-02. Source for `HttpSession` creation, cookie and URL
  rewriting tracking mechanisms, the default idle timeout, and
  `invalidate()`.
- Microsoft Learn, "Session and state management in ASP.NET Core",
  [learn.microsoft.com/en-us/aspnet/core/fundamentals/app-state](https://learn.microsoft.com/en-us/aspnet/core/fundamentals/app-state),
  verified 2026-08-02. Source for `ISession`, distributed cache backends,
  and the recommendation to use a shared backend for multi-instance
  deployments.
- `expressjs/session` package README,
  [github.com/expressjs/session](https://github.com/expressjs/session),
  verified 2026-08-02. Source for the cookie-plus-server-side-store model,
  the default `MemoryStore` production warning, and the list of compatible
  production store adapters including `connect-redis`.
- Amazon Web Services, "Configure sticky sessions for your Classic Load
  Balancer",
  [docs.aws.amazon.com/elasticloadbalancing/latest/classic/elb-sticky-sessions.html](https://docs.aws.amazon.com/elasticloadbalancing/latest/classic/elb-sticky-sessions.html),
  verified 2026-08-02. Source for the `AWSELB` cookie mechanism, duration-
  based versus application-controlled stickiness, and behaviour on backend
  instance failure.

## Code examples

Three languages are used here because each demonstrates a genuinely
different idiomatic shape of the pattern. TypeScript shows the Express
middleware convention of an implicit `req.session` object backed by a
pluggable store interface. Python shows an explicit, framework-agnostic
session manager class that a WSGI-style handler calls directly, closer to
how the pattern looks before a framework abstracts it away. Go shows a
minimal, dependency-free `net/http` implementation using a cookie for the
identifier and a mutex-guarded in-process map for the store, making the
store's internals, and their single-instance limitation named in dimension
8, fully visible rather than hidden behind a framework.

### TypeScript. An Express-style session middleware over a pluggable store

```typescript
// session.ts
// A minimal Express-style session middleware. The store interface is the
// swappable part, an in-memory map here, Redis in production, matching the
// "session store" participant from dimension 5.

import * as crypto from "crypto";

interface SessionStore {
  get(id: string): Record<string, unknown> | undefined;
  set(id: string, data: Record<string, unknown>, ttlMs: number): void;
  destroy(id: string): void;
}

class InMemorySessionStore implements SessionStore {
  private data = new Map<string, { value: Record<string, unknown>; expiresAt: number }>();

  get(id: string): Record<string, unknown> | undefined {
    const entry = this.data.get(id);
    if (!entry) return undefined;
    if (Date.now() > entry.expiresAt) {
      this.data.delete(id);
      return undefined;
    }
    return entry.value;
  }

  set(id: string, value: Record<string, unknown>, ttlMs: number): void {
    this.data.set(id, { value, expiresAt: Date.now() + ttlMs });
  }

  destroy(id: string): void {
    this.data.delete(id);
  }
}

interface Req {
  headers: Record<string, string | undefined>;
  session: Record<string, unknown>;
  sessionId: string;
}

interface Res {
  cookies: Record<string, string>;
  setCookie(name: string, value: string): void;
}

function sessionMiddleware(store: SessionStore, ttlMs: number) {
  return (req: Req, res: Res): void => {
    const cookie = req.headers["cookie"] || "";
    const match = cookie.match(/SID=([a-f0-9]{32})/);
    let sid = match ? match[1] : undefined;

    let data = sid ? store.get(sid) : undefined;
    if (!data) {
      sid = crypto.randomBytes(16).toString("hex");
      data = {};
      res.setCookie("SID", sid);
    }

    req.sessionId = sid!;
    req.session = data;
  };
}

function login(req: Req, res: Res, store: SessionStore, ttlMs: number): void {
  sessionMiddleware(store, ttlMs)(req, res);
  req.session.userId = 42;
  req.session.role = "admin";
  store.set(req.sessionId, req.session, ttlMs);
}

function logout(req: Req, store: SessionStore): void {
  store.destroy(req.sessionId);
}

function readCart(req: Req, res: Res, store: SessionStore): Record<string, unknown> | null {
  sessionMiddleware(store, 30 * 60 * 1000)(req, res);
  if (!req.session.userId) return null;
  return { userId: req.session.userId, role: req.session.role };
}

function makeRes(): Res {
  const cookies: Record<string, string> = {};
  return {
    cookies,
    setCookie(name: string, value: string) {
      cookies[name] = value;
    },
  };
}

function run(): void {
  const store = new InMemorySessionStore();
  const ttl = 30 * 60 * 1000;

  const req1: Req = { headers: {}, session: {}, sessionId: "" };
  const res1 = makeRes();
  login(req1, res1, store, ttl);
  const sid = res1.cookies["SID"];
  console.log("login issued session id length:", sid.length);

  const req2: Req = { headers: { cookie: `SID=${sid}` }, session: {}, sessionId: "" };
  const res2 = makeRes();
  const cart = readCart(req2, res2, store);
  console.log("second request resolved session:", cart);

  logout(req2, store);
  const req3: Req = { headers: { cookie: `SID=${sid}` }, session: {}, sessionId: "" };
  const res3 = makeRes();
  const afterLogout = readCart(req3, res3, store);
  console.log("after logout, session found:", afterLogout !== null, "new session issued:", res3.cookies["SID"] !== undefined);
}

run();
```

Compiled and run with `npx tsc --strict --target es2020 --module commonjs
session.ts` followed by `node session.js`. Output confirmed a 32-character
hex session id issued at login, the second request resolving
`{ userId: 42, role: 'admin' }` from that id, and after logout the session
correctly no longer resolving while a fresh session id was issued on the
next request, the create, read, invalidate cycle described in dimension 7.

### Python. An explicit session manager, framework-agnostic

```python
"""session_manager.py

A framework-agnostic Server Session State implementation. The manager is
called explicitly rather than injected as middleware, which is closer to
how the pattern looks in a hand-rolled WSGI application or a test harness,
and makes every step in dimension 7's dynamics diagram a visible method
call rather than something a framework hides.
"""

from __future__ import annotations

import secrets
import time
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class SessionEntry:
    data: dict[str, Any] = field(default_factory=dict)
    expires_at: float = 0.0


class SessionStore:
    """An in-process store. Swappable for a Redis-backed implementation
    that satisfies the same three methods, matching the store participant
    described in dimension 5 and the distributed variant in dimension 8."""

    def __init__(self) -> None:
        self._entries: dict[str, SessionEntry] = {}

    def get(self, session_id: str) -> Optional[dict[str, Any]]:
        entry = self._entries.get(session_id)
        if entry is None:
            return None
        if time.time() > entry.expires_at:
            del self._entries[session_id]
            return None
        return entry.data

    def set(self, session_id: str, data: dict[str, Any], ttl_seconds: float) -> None:
        self._entries[session_id] = SessionEntry(data=data, expires_at=time.time() + ttl_seconds)

    def destroy(self, session_id: str) -> None:
        self._entries.pop(session_id, None)

    def count(self) -> int:
        return len(self._entries)


class SessionManager:
    def __init__(self, store: SessionStore, ttl_seconds: float = 1800) -> None:
        self._store = store
        self._ttl = ttl_seconds

    def new_session(self) -> str:
        return secrets.token_hex(16)

    def resolve(self, session_id: Optional[str]) -> tuple[str, dict[str, Any], bool]:
        if session_id:
            data = self._store.get(session_id)
            if data is not None:
                self._store.set(session_id, data, self._ttl)
                return session_id, data, False
        new_id = self.new_session()
        data = {}
        self._store.set(new_id, data, self._ttl)
        return new_id, data, True

    def save(self, session_id: str, data: dict[str, Any]) -> None:
        self._store.set(session_id, data, self._ttl)

    def invalidate(self, session_id: str) -> None:
        self._store.destroy(session_id)


def demo() -> None:
    store = SessionStore()
    manager = SessionManager(store, ttl_seconds=1800)

    sid, data, is_new = manager.resolve(None)
    assert is_new
    data["user_id"] = 42
    data["role"] = "admin"
    manager.save(sid, data)
    print(f"login. session {sid[:8]}... created, is_new={is_new}")

    sid2, data2, is_new2 = manager.resolve(sid)
    assert sid2 == sid
    assert not is_new2
    print(f"second request resolved. user_id={data2.get('user_id')}, role={data2.get('role')}")

    manager.invalidate(sid)
    print(f"active sessions after logout. {store.count()}")

    sid3, data3, is_new3 = manager.resolve(sid)
    assert is_new3, "a destroyed session must not resolve, a new one is issued instead"
    print(f"post-logout request got fresh session={sid3[:8]}..., is_new={is_new3}, data={data3}")

    short_manager = SessionManager(store, ttl_seconds=0.05)
    esid, edata, _ = short_manager.resolve(None)
    time.sleep(0.1)
    resolved_after_expiry = store.get(esid)
    print(f"session after TTL elapsed, resolvable. {resolved_after_expiry is not None}")


if __name__ == "__main__":
    demo()
```

Run with `python3 session_manager.py`. Output confirmed the login sequence
creates a new session, the second request resolves the same identifier with
`user_id=42` and `role=admin`, logout drops the active session count to
zero, a subsequent request with the now-invalid cookie correctly receives a
brand-new session rather than resurrecting the old one, and a session
configured with a fifty-millisecond TTL is genuinely unresolvable after a
one-hundred-millisecond sleep, confirming the sliding-expiration mechanism
from dimension 7 actually expires entries rather than merely tracking a
timestamp nobody checks.

### Go. A minimal net/http implementation, store internals fully visible

```go
// session.go
// A dependency-free Server Session State implementation using only the
// standard library. The mutex-guarded map makes the in-process variant's
// single-instance limitation, named in dimension 8, structurally obvious
// rather than hidden behind an abstraction.

package main

import (
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"net/http"
	"sync"
	"time"
)

type sessionEntry struct {
	data      map[string]any
	expiresAt time.Time
}

type SessionStore struct {
	mu      sync.Mutex
	entries map[string]*sessionEntry
	ttl     time.Duration
}

func NewSessionStore(ttl time.Duration) *SessionStore {
	return &SessionStore{entries: make(map[string]*sessionEntry), ttl: ttl}
}

func newSessionID() string {
	b := make([]byte, 16)
	_, _ = rand.Read(b)
	return hex.EncodeToString(b)
}

func (s *SessionStore) Resolve(existingID string) (id string, data map[string]any, isNew bool) {
	s.mu.Lock()
	defer s.mu.Unlock()

	if existingID != "" {
		if entry, ok := s.entries[existingID]; ok {
			if time.Now().Before(entry.expiresAt) {
				entry.expiresAt = time.Now().Add(s.ttl)
				return existingID, entry.data, false
			}
			delete(s.entries, existingID)
		}
	}

	id = newSessionID()
	data = make(map[string]any)
	s.entries[id] = &sessionEntry{data: data, expiresAt: time.Now().Add(s.ttl)}
	return id, data, true
}

func (s *SessionStore) Destroy(id string) {
	s.mu.Lock()
	defer s.mu.Unlock()
	delete(s.entries, id)
}

func (s *SessionStore) Count() int {
	s.mu.Lock()
	defer s.mu.Unlock()
	return len(s.entries)
}

func sessionIDFromCookie(r *http.Request) string {
	c, err := r.Cookie("SID")
	if err != nil {
		return ""
	}
	return c.Value
}

func writeSessionCookie(w http.ResponseWriter, id string) {
	http.SetCookie(w, &http.Cookie{
		Name:     "SID",
		Value:    id,
		HttpOnly: true,
		Secure:   true,
		SameSite: http.SameSiteLaxMode,
		Path:     "/",
	})
}

func main() {
	store := NewSessionStore(30 * time.Minute)

	loginReq, _ := http.NewRequest("POST", "/login", nil)
	loginRec := &fakeResponseWriter{header: http.Header{}}
	id, data, isNew := store.Resolve(sessionIDFromCookie(loginReq))
	writeSessionCookie(loginRec, id)
	data["userId"] = 42
	data["role"] = "admin"
	fmt.Printf("login. issued session, is_new=%v, id_len=%d\n", isNew, len(id))

	cartReq, _ := http.NewRequest("GET", "/cart", nil)
	cartReq.AddCookie(&http.Cookie{Name: "SID", Value: id})
	id2, data2, isNew2 := store.Resolve(sessionIDFromCookie(cartReq))
	fmt.Printf("second request. same id=%v, is_new=%v, userId=%v, role=%v\n",
		id2 == id, isNew2, data2["userId"], data2["role"])

	store.Destroy(id)
	fmt.Printf("active sessions after logout. %d\n", store.Count())

	afterReq, _ := http.NewRequest("GET", "/cart", nil)
	afterReq.AddCookie(&http.Cookie{Name: "SID", Value: id})
	id3, data3, isNew3 := store.Resolve(sessionIDFromCookie(afterReq))
	fmt.Printf("post-logout request. new session issued=%v, id_changed=%v, empty_data=%v\n",
		isNew3, id3 != id, len(data3) == 0)
}

type fakeResponseWriter struct {
	header http.Header
}

func (f *fakeResponseWriter) Header() http.Header       { return f.header }
func (f *fakeResponseWriter) Write(b []byte) (int, error) { return len(b), nil }
func (f *fakeResponseWriter) WriteHeader(statusCode int) {}
```

Run with `go run session.go`. Output confirmed a new session issued at
login with a thirty-two character hex identifier, the second request
resolving the same session with `userId=42` and `role=admin`, the active
session count dropping to zero immediately after `Destroy`, and the
post-logout request correctly receiving a new, empty session rather than
the deleted one. The `fakeResponseWriter` exists only so `writeSessionCookie`
can be exercised without starting a real HTTP server, which is the same
in-memory-double technique described for unit testing in dimension 15.

Java and Rust were not used here in favour of Go, because the pattern's
in-process variant is most instructively shown with an explicit,
manually-locked map, and Go's standard library `net/http.Cookie` type maps
directly onto the session transport participant from dimension 5 with no
framework in between. Swift was not used because server-side Swift session
handling is a thin wrapper over the same store-and-cookie shape already
covered by the three languages above, and would not add a genuinely
different idiom to the entry.
