---
name: Client-Server
slug: client-server
family: 05-architectural
category: Architectural
aliases: [Frontend-Backend, Request-Response Architecture, C/S Model]
first_described: "Fielding, dissertation, 2000, section 3.4.1, tracing to distributed computing practice of the late 1970s and early 1980s"
maturity: canonical
related: [layered-architecture, broker-architecture, microservices-architecture, model-view-controller, hexagonal-architecture]
incompatible_with: []
verified: 2026-08-02
---

# Client-Server

## 1. Name, aliases, and lineage

The canonical name is Client-Server, sometimes written Client/Server or
abbreviated C/S. Roy Fielding's 2000 dissertation, *Architectural Styles and
the Design of Network-based Software Architectures*, section 3.4.1, gives the
style its most cited formal description in the software architecture
literature, stating plainly that "a server component, offering a set of
services, listens for requests upon those services" while "a client
component, desiring that a service be performed, sends a request to the
server via a connector." Fielding frames the style as arising from the
principle of separation of concerns, where user interface responsibilities
move to the client so that server components can be simplified, made more
capable of growth, and allowed to evolve independently of the clients that
consume them (Roy Thomas Fielding, *Architectural Styles and the Design of
Network-based Software Architectures*, PhD dissertation, University of
California, Irvine, 2000, chapter 3, section 3.4.1,
https://ics.uci.edu/~fielding/pubs/dissertation/net_arch_styles.htm, verified
2026-08-02).

Fielding's dissertation is where the style receives an architectural name and
a formal treatment, but the practice predates the write-up by two decades.
The term entered common industry usage during the shift away from mainframe
timesharing, when personal workstations and local area networks made it
practical to split an application into a component that ran near the person
and a component that ran near the shared data. The X Window System, released
in 1984, is one of the earliest widely deployed systems to use the vocabulary
of client and server explicitly for this purpose, and its protocol
specification still frames the design in exactly those terms, saying the X
protocol "can be built on top of any reliable byte stream" so that remote
clients on other machines can reach the server that owns the display and the
input devices (X Consortium, *X Window System Protocol*, version 11, release
7.7, chapter 8, Connection Setup,
https://xorg.freedesktop.org/archive/X11R7.7/doc/xproto/x11protocol.html,
verified 2026-08-02).

The aliases in real use are Frontend-Backend, which names the same split by
where the code runs relative to the person, and Request-Response
Architecture, which names the same split by the shape of the interaction
rather than the location of the components. Neither is a precise synonym.
Frontend-Backend is commonly used for a single web application's split into a
browser bundle and an API process, and it says nothing about whether the
backend is itself one server or many. Request-Response describes the
interaction style that client-server architectures typically use, but
request-response messaging also appears inside architectures that are not
client-server, for instance between two peer services in an event-driven
system that happen to use synchronous calls for one interaction. This entry
treats Client-Server as the architectural style, a system organized around
components that consume a shared, addressable service, and it treats the
request-response protocol as one of the several implementation variants a
client-server system can choose, alongside publish-subscribe over a
persistent connection or a message queue.

## 2. Problem and context

An application needs to let more than one user, device, or process operate on
data or capability that must be shared, kept consistent, and protected from
direct, uncoordinated access. If every participant held its own private copy
of that data and its own private logic for changing it, two participants
could make conflicting changes with neither aware of the other, a
participant with malicious or buggy code could corrupt data that other
participants depend on, and every participant would need to reimplement
identical business rules, validation, and storage logic. The problem
sharpens the moment the participants run on different machines, because then
there is no shared memory or shared file to coordinate through, only
whatever a network can carry.

The context in which Client-Server becomes the right answer has three
recurring features. First, there is an asymmetry of trust or capability, one
side has access to a resource, a database, a piece of hardware, or an
authoritative computation, and the other side does not and should not.
Second, more than one consumer needs that resource concurrently, and the
consumers do not need to know about each other. Third, the resource owner
benefits from being centralized, since it is easier to secure, back up,
upgrade, and reason about a system's invariants when one component is the
single point of truth for a given piece of state than when that state is
copied and mutated independently in many places. A file server exists
because many workstations need the same files and none of them should be
able to silently overwrite another's uncommitted work. A database server
exists because many application processes need to read and write the same
rows under the same consistency rules. A web server exists because many
browsers need the same HTML, and the logic that decides what HTML to send
should live in one auditable place rather than in every browser tab.

The pattern does not solve, and is often mistaken for solving, the problem of
growing a single server's capacity. Client-Server on its own says nothing
about load balancing, replication, or sharding, those are separate concerns
layered on top once a server's request volume outgrows a single process. A
reader should recognize the problem shape independent of scale, present
whether the server handles ten requests a day from a home network or ten
million requests a second from a global user base, because the shape is
about where authority and shared state live, not about how large the
deployment is.

## 3. Forces

This dimension is largely engineering judgement about how the forces trade
against each other in practice, and the named facts about protocols and
standards that appear inside it are separately cited.

**Coupling versus autonomy.** A client is coupled to the interface the
server exposes, and it must agree on the same protocol, message format, and
authentication scheme the server expects. That coupling is the entire point,
it is what lets many independent clients rely on one shared behavior without
each reimplementing it. The style trades client autonomy, since a client
cannot unilaterally change how the shared resource behaves, for consistency
of that behavior across every consumer.

**Latency versus centralization.** Centralizing logic and data in one place
generally increases the number of network hops a piece of work requires,
because a client cannot act on the resource without first reaching the
server. Client-Server, taken alone, favors correctness and manageability
over raw request latency, and every optimization added on top, caching,
CDNs, local replicas, read-through caches, is an attempt to buy back some of
that latency without giving up the single point of truth for writes.

**Statelessness versus session continuity.** A server that keeps no
per-client memory between requests is trivial to grow horizontally, because
any server instance can answer any client's next request. A server that
keeps session state in process memory can serve a richer, more efficient
interaction, at the cost of pinning a client to one server instance or
requiring an expensive session-migration mechanism. Fielding's dissertation
defines a further, stricter style built on top of Client-Server, called
Client-Stateless-Server, and argues it should be adopted specifically so
that client and server can grow independently of each other, at the cost
of moving session context into every request as repeated data (Fielding,
dissertation, section 3.4.3,
https://ics.uci.edu/~fielding/pubs/dissertation/net_arch_styles.htm, verified
2026-08-02). Most production client-server systems sit somewhere between
these two extremes rather than at either pole, keeping ephemeral connection
state in the server process while pushing durable state into a database the
server process itself treats as a client of.

**Operability versus flexibility.** A single, or small number of, server
components are easier to monitor, patch, and roll back than a system where
every participant runs its own copy of the logic. That operability gain
sacrifices some flexibility, every client is bound to the server's release
cadence and its decisions about backward compatibility, and a server outage
takes every dependent client down with it in a way that a fully peer-to-peer
system, where no single node is load-bearing for everyone, does not.

**Cost and team topology.** Concentrating logic in a server lets one team own
that logic and its correctness, while many client teams build on top without
duplicating the work. This is a strong cost win when the server logic is
genuinely shared and genuinely complex, and a strong cost loss when the server
becomes an organizational bottleneck that every client team must queue
behind for a change. Conway's Law pressure, where a system's structure
mirrors the communication structure of the organization that builds it,
tends to push a single client-server pair toward a small number of services
once more than a few independent client teams depend on it, which is one of
the forces that eventually motivates the microservices-architecture entry in
this catalog.

## 4. Applicability and non-applicability

### When to reach for it

- More than one client needs concurrent, coordinated access to the same
  resource, and uncoordinated direct access by each client would risk
  conflicting writes, inconsistent reads, or resource contention the clients
  cannot resolve among themselves.
- The resource, whether a database, a filesystem, a piece of hardware, or a
  computation, benefits from a single, centrally administered point of
  control for security, backup, licensing, or auditing reasons.
- Clients are heterogeneous, running different platforms, languages, or
  devices, and a shared network protocol is the only practical common ground
  between them, as it is for a web browser and a mobile app both talking to
  the same backend.
- The logic that governs access to the resource changes independently of,
  and more slowly than, the clients that use it, so centralizing it avoids
  redeploying that logic into every client on every change.
- The system needs a clear place to enforce authorization, because a
  server-side chokepoint can verify every request against a policy in a way
  that logic distributed across untrusted clients cannot be trusted to do.

### When NOT to reach for it, and why

- **Two processes on the same machine that only ever talk to each other,
  with no third party ever joining.** A direct function call, a shared
  library, or in-process communication has none of the serialization,
  connection management, or network failure-handling cost that a
  client-server split imposes, and there is no sharing problem to solve
  because there is only one consumer.
- **Truly symmetric collaboration among equal participants with no natural
  authority.** A pattern such as peer-to-peer file sharing, where every node
  can equally originate and serve the same content and no single node is the
  authoritative source, fights the client-server style's assumption of an
  asymmetric relationship, and forcing a central server into that shape
  reintroduces a single point of failure the peer-to-peer design exists to
  avoid.
- **Offline-first applications where the primary experience must function
  with no server reachable at all.** A client-server design that treats the
  network round trip as mandatory produces a broken experience the instant
  connectivity drops, and these systems need a local-first architecture
  where the server, if one exists, is a synchronization peer rather than the
  sole source of truth for every read.
- **Extremely latency-sensitive control loops, such as a flight control
  system's inner stabilization loop or an audio synthesis engine's sample
  processing.** The network round trip a client-server split introduces,
  typically single-digit to low double-digit milliseconds even on a fast
  local network and far more across a wide area network, is unacceptable
  when the control loop must complete in microseconds, so these systems keep
  the entire loop in-process.
- **A single, static resource that does not change and does not need
  coordinated access, such as a value baked into a client at build time.**
  Introducing a server to serve an unchanging constant adds a network
  dependency, a failure mode, and an operational cost for a problem that
  does not exist, and the resource belongs in the client's own
  configuration or compiled artifact.
- **Systems where every participant must independently verify state without
  trusting any single party**, which is the founding constraint of public
  blockchain and other Byzantine-fault-tolerant distributed ledgers, and
  those systems reject the client-server style's central point of trust by
  construction, using consensus among many mutually distrusting nodes
  instead.

## 5. Structure

**Client.** The component that initiates an interaction because it needs a
service performed or a piece of data returned. A client holds no obligation
to answer requests from anyone else, its role is entirely to originate
requests and consume responses. A client typically owns presentation logic,
local input validation for responsiveness, and whatever caching it needs for
its own performance, but it does not own the canonical copy of shared state.

**Server.** The component that listens for requests on a well-known, or at
least discoverable, address, and performs the requested service, most
commonly by reading or mutating state it owns exclusively. The server
exposes an interface, the set of operations and message shapes clients are
permitted to invoke, and enforces whatever authentication, authorization,
and consistency rules the shared resource requires. A server may itself act
as a client of another server, which is the normal shape of an application
server that is a client to the database server behind it.

**Connector, or the communication protocol.** The mechanism the client uses
to send a request and receive a response, together with the rules that
govern the message format, the transport, and the failure semantics. In
practice this is almost always a network protocol, HTTP, gRPC over HTTP/2, a
raw TCP socket protocol, or a message broker's wire protocol when the
interaction is asynchronous. The connector is not incidental plumbing, the
choice of connector determines whether the interaction is synchronous or
asynchronous, whether it is connection-oriented or connectionless, and how
failures are detected and surfaced to the client.

**Service interface, or contract.** The description of what operations the
server exposes, what each operation expects as input, and what it
guarantees as output. This may be informal, a hand-maintained API document,
or formal, a Protocol Buffers `.proto` file, an OpenAPI specification, or a
WSDL document. The contract is the boundary artifact that lets client and
server teams develop independently, because each side can build against the
contract without access to the other side's implementation.

**Session or connection state, where present.** Some client-server
interactions are stateless per request, and the server needs no memory of a
prior request to answer the next one from the same client, HTTP as defined
in RFC 9110 is designed this way at the protocol layer (R. Fielding, M.
Nottingham, J. Reschke, editors, *RFC 9110, HTTP Semantics*, Internet
Engineering Task Force, June 2022,
https://www.rfc-editor.org/rfc/rfc9110.html, verified 2026-08-02). Other
interactions are stateful, keeping a session identifier, an authenticated
principal, or an open connection alive across multiple requests, as a
database server does for a connected client's transaction, or as a
WebSocket connection does for a chat application. Where session state
exists, it is a distinct structural element that determines how the server
can be scaled and replaced.

## 6. ASCII structure diagram

```
+------------------------------------------------------------+
|                       CLIENT-SERVER                        |
+------------------------------------------------------------+

   +-------------+                        +-------------+
   |  Client A   |                        |  Client B   |
   | (browser,   |                        | (mobile app,|
   |  desktop    |                        |  another    |
   |  app, CLI)  |                        |  service)   |
   +------+------+                        +------+------+
          |                                       |
          |   request over the network            |
          |   (connector: HTTP, gRPC, TCP, ...)   |
          v                                       v
   +-----------------------------------------------------+
   |                       SERVER                         |
   |  +-------------------------------------------------+ |
   |  |         Service interface / contract              | |
   |  |   (routes, RPC methods, message schemas)          | |
   |  +--------------------------+------------------------+ |
   |                             |                          |
   |  +--------------------------v------------------------+ |
   |  |    Application logic (auth, validation, rules)      | |
   |  +--------------------------+------------------------+ |
   |                             |                          |
   |  +--------------------------v------------------------+ |
   |  |          Owned, shared resource / state              | |
   |  |     (database, filesystem, device, cache)            | |
   |  +-----------------------------------------------------+ |
   +-----------------------------------------------------+

   Multiple clients address ONE authoritative server component
   (or a small, coordinated set standing in for one logical server).
   A response returns to the requester over the same connector.
```

## 7. Dynamics

Synchronous request-response cycle, the default interaction.

```
CLIENT                        NETWORK                    SERVER
  |                                                          |
  | 1. build request                                        |
  |    (method, target, payload, credentials)                |
  |----------------------------------------------------------|
  |            2. request travels over connector             |
  |------------------------------------------------------->  |
  |                                                          | 3. authenticate,
  |                                                          |    authorize, validate
  |                                                          | 4. read or mutate the
  |                                                          |    owned resource
  |                                                          | 5. build response
  |  <-------------------------------------------------------|
  |            6. response travels back                      |
  | 7. parse response, update local view                     |
  |                                                          |
```

Each numbered step is a discrete unit of work. Step 1 happens entirely on the
client and never touches the network. Steps 2 and 6 are where the
connector's properties, timeout, retry, and failure behavior, matter most,
because this is where partial failure becomes possible, the request can be
lost, the response can be lost, or the server can process the request and
fail before the response is sent, and the client cannot distinguish the
third case from the first two by observation alone. This ambiguity is why
idempotent operations and idempotency keys matter more in client-server
systems than they might appear to from the happy path alone.

Stateful session dynamics, for protocols that keep a connection alive.

```
CLIENT                                                   SERVER
  |                                                          |
  |------------------ 1. open connection ------------------->|
  |<----------------- 2. connection accepted -----------------|
  |                                                          |
  |------------------ 3. authenticate ----------------------->|
  |<----------------- 4. session established -----------------|
  |                                                          |
  |------------------ 5. request A --------------------------->|
  |<----------------- 6. response A ---------------------------|
  |------------------ 7. request B (same session) ------------->|
  |<----------------- 8. response B ----------------------------|
  |                                                          |
  |------------------ 9. close connection --------------------->|
  |<----------------- 10. session torn down --------------------|
```

Here the server does hold memory between step 4 and step 9, typically an
authenticated principal, transaction state, or a subscription list. The cost
of this shape is that the client is pinned to whichever server instance
holds that session, and the server must decide what happens to in-flight
work if that instance crashes mid-session, which is the operational
complexity a stateless design in the first diagram avoids entirely.

## 8. Implementation variants

**Request-response over a stateless protocol.** The client sends a
self-contained request that carries everything the server needs to answer
it, including authentication, and the server holds no memory of the client
between requests. HTTP, as normatively defined by RFC 9110, is the most
widely used example, the specification describing HTTP as "a stateless
application-level protocol for distributed, collaborative, hypertext
information systems," with each request-response exchange an independent
transaction (RFC 9110, section 1,
https://www.rfc-editor.org/rfc/rfc9110.html, verified 2026-08-02). This
variant is favored when growing the server pool and simple failover matter
more than avoiding repeated authentication or context data on every call,
and it is the variant REST, as Fielding formalizes it, is built on top of.

**Remote Procedure Call, RPC.** The client invokes what looks syntactically
like a local method, and a generated stub serializes the arguments, sends
them to the server, and deserializes the return value, hiding the network
hop behind a familiar call shape. gRPC is the current widely adopted
example, its own documentation describing it as letting "a client
application... directly call a method on a server application on a
different machine as if it were a local object," built on Protocol Buffers
as the interface description language and HTTP/2 as the transport (Google,
*Introduction to gRPC*, grpc.io,
https://grpc.io/docs/what-is-grpc/introduction/, verified 2026-08-02). This
variant favors strongly typed contracts and efficient binary serialization
over the self-descriptive, cacheable properties of a REST-style interface.

**Publish-subscribe over a persistent connection.** The client opens a
long-lived connection and the server pushes updates as they occur, rather
than the client polling. WebSockets and Server-Sent Events implement this
at the transport layer, and it is common inside a client-server system
whenever a client needs near-real-time updates, a live chat window, a
collaborative document, or a trading dashboard, without the overhead of
repeated polling. Structurally this remains client-server, because one
component still owns and serves the shared resource, but the direction of
the individual push messages runs from server to client rather than the
reverse.

**Client-Cache-Stateless-Server and layered variants.** Fielding's
dissertation derives further styles by adding constraints on top of the
base Client-Server style, most importantly Client-Stateless-Server, which
forbids the server from retaining session state between requests, and
layered systems, which allow intermediary components, proxies, gateways,
and caches, to sit between client and server without either endpoint
needing to know the intermediary is there (Fielding, dissertation, sections
3.4.2 through 3.4.3,
https://ics.uci.edu/~fielding/pubs/dissertation/net_arch_styles.htm, verified
2026-08-02). In production, most HTTP-based client-server systems are
actually this layered variant, a CDN, a load balancer, and an API gateway
typically sitting between the client and the application server, each one
itself playing server to the hop before it and client to the hop after it.

**Thick client versus thin client.** A thick, or fat, client keeps
substantial logic and state locally, using the server mainly for data
persistence and synchronization, as a desktop database application
historically did against a shared SQL server. A thin client keeps almost no
logic locally and renders whatever the server sends, as a classic
server-rendered web page does. The choice trades client-side responsiveness
and offline tolerance against the operational simplicity of pushing every
logic change through one server deployment, and most modern single-page web
applications sit deliberately between the two poles, keeping presentation
and some validation logic in the browser while treating the server as
authoritative for everything else.

## 9. Known production uses

**PostgreSQL.** The PostgreSQL project's own tutorial documentation states
plainly that "PostgreSQL uses a client/server model," describing a
supervisor `postgres` server process that listens for client connections
and forks a dedicated backend process per connection, with client and
server able to run on different hosts connected over TCP/IP (PostgreSQL
Global Development Group, *PostgreSQL Documentation*, section 1.2,
Architectural Fundamentals,
https://www.postgresql.org/docs/current/tutorial-arch.html, verified
2026-08-02). Every application that issues SQL against PostgreSQL is, by the
project's own description, a client of this architecture.

**The World Wide Web, via HTTP as standardized in RFC 9110.** RFC 9110
formalizes the web's request-response exchange between a user agent, the
client role, and an origin server, and the specification's terminology
section defines "client" and "server" directly in these terms, describing
the roles as connection endpoints that can be reused across multiple,
unrelated requests and responses (RFC 9110, section 3.4, Connections,
https://www.rfc-editor.org/rfc/rfc9110.html, verified 2026-08-02). Nearly
every browser, mobile app, and server-to-server integration that speaks
HTTP is an instance of this pattern at global scale.

**The X Window System.** X was designed from its first release in 1984
around an explicit client-server split, with the X server owning the
display and input hardware and running possibly on a different machine
than the client applications that request drawing operations from it, and
the X11 protocol specification's connection setup chapter states the
protocol "can be built on top of any reliable byte stream" precisely to
support remote clients over a network (X Consortium, *X Window System
Protocol*, version 11, release 7.7, chapter 8,
https://xorg.freedesktop.org/archive/X11R7.7/doc/xproto/x11protocol.html,
verified 2026-08-02). This remains the architecture underneath most Linux
and Unix desktop environments that still use X11 rather than Wayland.

**gRPC-based internal service meshes.** gRPC's own introduction documents
its client-server RPC model, noting that "gRPC clients and servers can run
and talk to each other in a variety of environments, from servers inside
Google to your own desktop," and states that gRPC was developed originally
at Google and is now a Cloud Native Computing Foundation project used
across many organizations' internal service-to-service traffic (Google,
*Introduction to gRPC*, https://grpc.io/docs/what-is-grpc/introduction/,
verified 2026-08-02). Any system built on gRPC-based internal APIs, a
common shape for microservices-architecture backends, is a Remote Procedure
Call variant of Client-Server at the level of a single service call.

## 10. Consequences

### Positive

- Shared state has exactly one authoritative owner, which removes the class
  of bug where two independently mutated copies of the same data disagree
  with no defined way to reconcile them.
- Security and access control have a single enforcement point, the server,
  rather than needing every client to correctly and honestly enforce policy
  on its own, which is not a trust boundary a client can be relied on to
  hold.
- Clients can be heterogeneous. A browser, a mobile app, and a server-side
  integration can all be clients of the same server as long as each speaks
  the agreed protocol, which lets a single backend serve many different
  front-end technologies without duplicating logic in each.
- The server side can evolve, be patched, or be entirely rewritten
  internally without touching deployed clients, as long as the external
  contract is preserved, which is a strong operational and organizational
  win for teams that must ship fixes without coordinating a simultaneous
  client release.
- Centralizing logic in the server avoids duplicating business rules across
  every client, which reduces the surface area where the rules can drift
  out of sync with each other.

### Negative

- The server becomes a single point of failure for every client that
  depends on it, unless additional patterns, replication, load balancing,
  failover, are layered on top, each of which adds its own operational
  cost.
- Every interaction now crosses a network boundary, introducing latency,
  partial failure, and the need to handle timeouts, retries, and the
  ambiguity of an unacknowledged request, none of which exist in an
  in-process call.
- The server can become an organizational bottleneck. As the number of
  independent client teams grows, each new capability those teams need
  requires coordination with, and often queuing behind, whichever team owns
  the server, which is the pressure that eventually pushes large
  organizations toward splitting a single server into several
  independently deployable services.
- A poorly designed protocol or contract couples client and server tightly
  enough that a server-side change breaks clients anyway, which erodes the
  independent-evolution benefit the style is meant to provide, and this is
  a contract design failure rather than a defect built into the style
  itself, but it is the most common way the style's promised benefit is
  lost in practice.
- Statelessness, where adopted to make growth easier, forces either
  repeated authentication data on every request or a separate token or
  session store, both of which add complexity that a stateful in-process
  design would not need.

## 11. Failure modes and misuse

**Chatty client, thin server.** Symptom, a client makes many small
sequential requests to assemble one screen or one unit of work, each
request paying a full round trip, and the user-visible latency for a simple
action is spent mostly on network time rather than on server processing
time. Cause, the server's interface was designed around convenient CRUD
operations on individual resources rather than around the actual
client-side use cases, forcing the client to make several calls to get what
it needs. Fix, design the server interface around client use cases, batch
or compose related reads into a single endpoint, or introduce a Backend for
Frontend layer that aggregates several downstream calls into one response
for a specific client.

**Fat server anti-pattern, sometimes called God server.** Symptom, one
server component accretes so much unrelated responsibility, user
authentication, billing, notification, search, that a small change
anywhere requires a full regression cycle across the entire server, and
deploy frequency for any single feature drops as the codebase grows.
Cause, new features were added to the existing server because that was the
path of least resistance, with no discipline about splitting
responsibilities as they diverge. Fix, apply the same decomposition
pressure the microservices-architecture and hexagonal-architecture entries
describe, splitting the server along genuine bounded contexts once a
single deploy unit becomes the organizational bottleneck.

**Session affinity masquerading as statelessness.** Symptom, a load
balancer is configured with sticky sessions, and the system appears to
grow horizontally because new server instances can be added, but in
reality a given client's requests are pinned to one instance, and losing
that instance loses the client's in-flight session with no graceful
recovery. Cause, the server was written to keep session state in local
process memory, and sticky sessions were adopted as a workaround rather
than externalizing session state to a shared store. Fix, move session
state into a shared, externally addressable store, a database or a
distributed cache, so any server instance can serve any client's next
request, which is the Client-Stateless-Server derivation Fielding's
dissertation describes.

**Trusting the client for authorization decisions.** Symptom, an attacker
modifies a mobile app's binary, intercepts and edits requests with a proxy
tool, or simply calls the API directly with a crafted payload, and gains
access to data or actions the intended user interface would never have
exposed. Cause, validation or authorization logic was implemented only in
the client, on the assumption that the client's user interface would
prevent the invalid request from ever being constructed. Fix, treat every
request arriving at the server as potentially hostile regardless of which
official client sent it, and enforce every authorization and validation
rule server-side, since the client-side version of the same checks is a
usability optimization, never a security boundary.

**Retry storms against a struggling server.** Symptom, a server begins
responding slowly under load, clients time out and retry, the retries add
to the load the struggling server is already failing to handle, and the
system enters a feedback loop that keeps the server saturated even after
the original load spike passes. Cause, clients retry on failure with no
backoff, no jitter, and no circuit breaker to stop retrying against a
server that is clearly unhealthy. Fix, implement exponential backoff with
jitter on the client, and add a circuit breaker that stops sending
requests to a server that is failing, giving it room to recover.

**Version skew between client and server contracts.** Symptom, an older
client, one that has not yet received an update, sends a request shaped
for an earlier version of the server's contract, and either the server
rejects it outright, breaking the client's user, or the server silently
misinterprets a field that changed meaning between versions. Cause, the
server's contract changed in a way that was not backward compatible, and
no strategy existed for supporting clients on the previous contract
version during the rollout window. Fix, version the contract explicitly,
keep the previous version supported for a defined deprecation window, and
prefer additive, non-breaking changes to the wire format wherever the
interaction allows it.

## 12. Trade-off matrix

| Force | Client-Server | Peer-to-peer | Broker Architecture | Layered Architecture (single process) |
|---|---|---|---|---|
| Single source of truth for shared state | Strong. One server owns the resource. | Weak by design. State is replicated and reconciled across peers, with no single owner. | Strong for messages in flight, but the broker typically does not own application state itself. | Strong. State lives inside one process, no distribution concern at all. |
| Resilience to a single component failing | Weak unless replication is added. Server down means service down for its clients. | Strong. No single peer's failure takes the network down. | Depends on the broker's own availability, the broker itself is a similar single point unless clustered. | Strong against network partition, since there is no network inside the process, but the whole process is still a single point. |
| Coordination complexity for the initial build | Low to moderate. One clear place to put logic and enforce rules. | High. Consensus and conflict resolution across untrusted peers is genuinely hard. | Moderate. Requires operating and reasoning about the broker as infrastructure. | Lowest. No network protocol, no serialization, no partial failure to design for. |
| Fit for heterogeneous client platforms | Strong. Any client that speaks the protocol can participate. | Weak. Peers typically need to run compatible peer software, not merely speak a wire protocol. | Strong for producers and consumers, similar to client-server in this respect. | Not applicable. All participants are within one process and one platform. |
| Growth in the number of independent client teams | Moderate, and degrades into an organizational bottleneck without further decomposition. | Strong by construction, since there is no shared owner to coordinate through. | Strong. Producers and consumers are decoupled through the broker and do not need direct coordination. | Poor for multiple external teams, since there is no external interface at all. |
| Network latency cost per interaction | Present on every remote call. | Present, and can be worse, since a request may hop through several peers to reach the data. | Present, plus the broker's own processing and delivery latency. | None, since there is no network hop. |

## 13. Related and incompatible patterns

**Layered Architecture.** A production client-server system is almost never
a bare two-tier split. In practice a request typically crosses several
layers, a CDN or reverse proxy, a load balancer, an API gateway, the
application server, and a database server, each layer itself playing server
to the hop in front of it and client to the hop behind it. Client-Server
describes the relationship between any two adjacent tiers, Layered
Architecture, elsewhere in this catalog, describes how several such tiers
compose into a full system.

**Broker Architecture.** When client and server should not, or cannot,
address each other directly, a broker sits between them, routing requests
and sometimes translating protocols. Broker Architecture is a
specialization of Client-Server in which the server side is not one
component but a discoverable set of components the broker mediates access
to, and both the client-to-broker and broker-to-server hops are themselves
ordinary client-server relationships.

**Microservices Architecture.** Microservices are, at the level of any two
services calling each other, client-server relationships, typically over
HTTP or gRPC. The microservices pattern adds the further constraint that
there are many independently deployable servers rather than one, each
owning a narrow slice of the domain, which is the decomposition response
to the fat-server and organizational-bottleneck failure modes described
above.

**Model-View-Controller and its siblings.** MVC, MVP, MVVM, and MVI
describe how a single client's internal code is organized once that client
is talking to a server, they are patterns for structuring one side of a
client-server relationship, not alternatives to it. A well-structured MVC
client still needs a server to be a client of if it is to share state with
anyone else.

**Hexagonal Architecture.** A server built as a client-server endpoint
commonly organizes its own internals with a hexagonal, or ports and
adapters, structure, treating the network protocol that clients speak as
one adapter among several, alongside adapters for the database, message
queue, and other outbound dependencies. Hexagonal Architecture governs the
server's internal structure, Client-Server governs the relationship between
the server and its callers.

**Incompatible relationship, peer-to-peer.** Client-Server assumes an
asymmetric relationship where one side is authoritative and the other side
is not. A genuinely peer-to-peer design, where every node can equally
serve and consume the same resource with no privileged node, is a
different architectural commitment, not a variant of Client-Server. A
system that tries to be both at once, for instance a "peer-to-peer"
network that in practice routes every transaction through one node that
all peers must trust, has quietly reintroduced Client-Server under a
peer-to-peer label rather than achieving genuine decentralization, and the
trade-offs of that hidden central node apply whether or not the marketing
calls it a peer.

## 14. Refactoring path in and out

### Introducing Client-Server into code that does not have it

1. Identify the shared resource and its current, uncoordinated access
   points. Find every place in the codebase, or across separate codebases,
   that reads or writes the resource directly, for instance every process
   that opens the same file or the same embedded database file
   independently.
2. Define the contract first, before writing the server. Decide what
   operations the shared resource needs to expose, what each operation's
   inputs and outputs are, and what invariants the server will enforce that
   direct access currently does not. Write this down as an interface
   definition, whether an OpenAPI document, a `.proto` file, or a simple
   internal specification, before implementing either side against it.
3. Stand up the server as the sole owner of the resource, moving the direct
   access logic that used to live in every consumer into the new server
   component, and removing every consumer's direct handle on the resource
   in the same change, so there is no window where both direct access and
   server access are possible at once for the same piece of state.
4. Convert each former direct consumer into a client, replacing its direct
   calls with calls against the new server's contract. Do this one
   consumer at a time when the codebase allows it, verifying each
   conversion independently rather than flipping every consumer
   simultaneously.
5. Add the failure handling a network boundary requires that in-process
   access never needed, timeouts, retries with backoff where the operation
   is idempotent, and explicit error handling for the case where the
   server is unreachable, since none of these existed when the access was
   a direct, in-process call that could not partially fail.
6. Version the contract from the first server release, even if there is
   currently only one client, so that adding a second client or evolving
   the first one later does not require breaking every existing consumer.

### Removing Client-Server when it stops earning its place

Client-Server is worth removing, collapsing the server back into an
in-process call, when the reason it was introduced no longer holds. There
is now, and will remain, exactly one consumer of the resource, the network
hop's latency and failure-handling cost is a proven, measured problem
rather than a theoretical one, and no other future consumer is
realistically expected.

1. Confirm there is genuinely one remaining client. Check for any other
   process, scheduled job, or integration that also depends on the
   server's contract, since removing the server silently breaks any
   consumer that was not accounted for.
2. Inline the server's logic into the sole remaining client, moving the
   validation, authorization, and resource-access code the server used to
   own directly into the client's own process.
3. Remove the network protocol, serialization, and connection-handling
   code the client-server split required, along with any retry, timeout,
   and circuit-breaker logic that existed only because of the network hop.
4. Decommission the server component and its independent deployment
   pipeline, and update monitoring, alerting, and on-call documentation
   that referenced it as a separate operational unit.
5. Re-add the client-server split later if a second consumer appears,
   following the introduction steps above rather than trying to preserve a
   half-removed server "in case it is needed again," since a half-removed server carries
   the operational cost of a server with none of the benefit of serving
   more than one consumer.

## 15. Testing and verification

Client-Server pulls the testing effort in a direction the architecture makes
possible and, if ignored, dangerous. The interface between client and
server becomes the natural seam for a test double, because a well-designed
server contract is something a test can fake without needing the real
server running. A client's tests can substitute a stub or mock server that
returns canned responses for known requests, which makes client-side unit
tests fast and independent of network availability, database state, or the
real server's current behavior.

What becomes harder is verifying that the client and the real server
actually agree on the contract both sides believe they are testing against.
A stub server that was hand-written to match a stale version of the
contract will happily let a client's tests pass while the real server has
since changed its response shape, its status codes, or its validation
rules. This is the central testing risk of the pattern, and it is
addressed by contract testing, where the client's expectations of the
server's responses are captured as a formal artifact, a consumer-driven
contract, and that same artifact is replayed against the real server in the
server's own test suite, so a breaking change to the server's contract is
caught in the server's pipeline before it ever reaches a deployed client.

Integration tests that exercise a real client against a real, running
server, even a locally spun-up instance in a container, remain valuable
specifically because they catch the class of bug that pure unit tests with
stubs cannot, serialization mismatches, authentication handshake failures,
and timing issues that only appear when actual bytes cross an actual
socket. These tests are more expensive to run and slower than unit tests
with stubs, which is why the usual testing strategy for a client-server
system is a pyramid. Many fast unit tests against stubs for both client
and server logic individually, a smaller number of contract tests
verifying the two sides agree, and a still smaller number of full
integration or end-to-end tests that exercise the real network path for
the critical user flows.

Server-side, the operations that read or write the shared resource are the
part most worth testing directly against a real or near-real dependency, a
disposable test database rather than a mock of the database driver,
because the value the pattern provides, a single, correctly enforced
source of truth, lives entirely in whether that logic is actually correct
under concurrent access, not merely in whether it compiles against a
mocked interface.

## 16. Observability signals

This dimension is drawn from operational practice rather than a single
citable source.

A healthy client-server boundary shows a request rate and a response
latency distribution that are both stable and within an agreed service
level objective, an error rate, specifically the proportion of requests
answered with a server-side failure status rather than a client-side one,
that stays near zero, and a saturation metric, whichever resource the
server is most likely to run out of first, connection pool slots, CPU, or
database connections, that has visible headroom rather than sitting near
its upper limit. These four signals, rate, errors, duration, and saturation,
are the well-known RED and USE signal groupings applied specifically to the
network boundary a client-server split introduces, and they are worth
tracking separately for every distinct client-server hop in a layered
system rather than only at the outermost edge, because a healthy edge can
mask an unhealthy internal hop that has not yet accumulated enough load to
surface externally.

A failing instance typically shows one of a small number of recognizable
shapes on a dashboard. A rising p99 latency while p50 stays flat, which
usually means a subset of requests are hitting a slow path, a lock, a cold
cache, or a slow downstream dependency, while most requests are fine. A
rising error rate concentrated in one status code family, which points at
a specific failure mode, authentication failures clustering as 401s,
downstream timeouts clustering as 503s or 504s. And a request rate that
suddenly drops to zero for a given client while other clients continue
normally, which usually indicates a client-side configuration or
deployment problem rather than a server problem. Distributed tracing,
correlating a single logical request across every hop it crosses in a
layered client-server chain with a shared trace identifier, is the tool
that turns "the server is slow" into "the third hop in this particular
chain is slow," which is the level of precision an operator needs to act
on the signal rather than merely observe it.

## 17. Security and privacy implications

Client-Server concentrates a system's security boundary at the server,
which is both the pattern's strongest security property and its
highest-value attack surface. Because the server is the single enforcement
point for authorization and validation, it must never trust a client's
assertion about what the client is permitted to do, every authorization
decision has to be re-derived server-side from the authenticated identity
of the request, not read from a field the client supplied, because a
client is, by nature, an untrusted input source regardless of how much
validation its own user interface performs before sending the request.

The network hop between client and server is itself an attack surface that
an in-process call does not have. Traffic in transit must be encrypted,
practically always with TLS, to prevent eavesdropping and tampering by a
party positioned between the client and the server, and the server's
identity must be verifiable by the client through certificate validation
to prevent a party from impersonating the server and capturing credentials
or data the client would otherwise have sent legitimately.

Centralizing data on a server also centralizes the privacy and
data-protection obligations that come with holding it. A server that
aggregates data from many clients becomes a single, high-value target
whose compromise exposes every client's data at once, in a way that data
kept independently on each client's own device would not. This is a direct
trade-off against the pattern's coordination benefit, and it is the reason
server-side data minimization, storing only what is genuinely needed,
encryption at rest, and strict access controls on who and what can query
the stored data internally, matter as much as the network-facing controls.
A server that is well protected against external attackers but internally
lets any employee or any internal service query the full dataset has not
actually reduced the privacy exposure the centralization created, only
relocated where the exposure can occur.

Rate limiting and authentication at the server boundary also serve a
security purpose beyond correctness. Because every client must reach the
server to act on the shared resource, the server is a natural, and
necessary, place to detect and throttle abusive or automated traffic,
something that would be much harder to enforce consistently if the
resource were directly, and independently, reachable by each client
without a shared chokepoint.

## 18. References

1. Roy Thomas Fielding, *Architectural Styles and the Design of Network-based
   Software Architectures*, PhD dissertation, University of California,
   Irvine, 2000, chapter 3, sections 3.4.1 through 3.4.3.
   https://ics.uci.edu/~fielding/pubs/dissertation/net_arch_styles.htm,
   verified 2026-08-02.
2. R. Fielding, M. Nottingham, J. Reschke, editors, *RFC 9110, HTTP
   Semantics*, Internet Engineering Task Force, June 2022, sections 1 and
   3.4. https://www.rfc-editor.org/rfc/rfc9110.html, verified 2026-08-02.
3. PostgreSQL Global Development Group, *PostgreSQL Documentation*, section
   1.2, Architectural Fundamentals.
   https://www.postgresql.org/docs/current/tutorial-arch.html, verified
   2026-08-02.
4. X Consortium, *X Window System Protocol*, version 11, release 7.7,
   chapter 8, Connection Setup.
   https://xorg.freedesktop.org/archive/X11R7.7/doc/xproto/x11protocol.html,
   verified 2026-08-02.
5. Google, *Introduction to gRPC*, grpc.io documentation.
   https://grpc.io/docs/what-is-grpc/introduction/, verified 2026-08-02.

## Code examples

Three languages carry a runnable example, chosen because they show three
different points among the connector choices this entry describes, a plain
TCP socket in Python, a plain TCP socket in Go, and an HTTP request over
`fetch` in TypeScript. All three follow the same shape, a server that
listens and answers, and a client that connects and asks. Java, Rust, and
Swift are omitted here because a fourth or fifth socket example would not
show anything a reader has not already seen in the first three, and the
pattern itself is connector-agnostic rather than language-specific.

### Python

```python
"""Minimal client-server example. an in-process TCP echo server and a
client that connects to it, sends a request, and reads the response."""

import socket
import threading


def run_server(host: str, port: int, ready: threading.Event) -> None:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(1)
    ready.set()
    conn, _ = server.accept()
    with conn:
        data = conn.recv(1024)
        conn.sendall(b"server received, " + data)
    server.close()


def run_client(host: str, port: int, message: bytes) -> bytes:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.connect((host, port))
        client.sendall(message)
        return client.recv(1024)


def main() -> None:
    host = "127.0.0.1"
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind((host, 0))
    port = server_sock.getsockname()[1]
    server_sock.close()

    ready = threading.Event()
    server_thread = threading.Thread(target=run_server, args=(host, port, ready))
    server_thread.start()
    ready.wait()

    response = run_client(host, port, b"hello")
    print(response.decode())
    server_thread.join()


if __name__ == "__main__":
    main()
```

Compiled with `python3 -m py_compile` and run directly. Output confirmed,
`server received, hello`.

### Go

```go
// Minimal client-server example. a TCP server that answers one
// connection, and a client that connects, sends a request, and reads
// the response.
package main

import (
	"bufio"
	"fmt"
	"net"
)

func runServer(listener net.Listener, ready chan<- struct{}) {
	ready <- struct{}{}
	conn, err := listener.Accept()
	if err != nil {
		return
	}
	defer conn.Close()
	line, _ := bufio.NewReader(conn).ReadString('\n')
	fmt.Fprintf(conn, "server received, %s", line)
}

func runClient(addr string, message string) (string, error) {
	conn, err := net.Dial("tcp", addr)
	if err != nil {
		return "", err
	}
	defer conn.Close()
	fmt.Fprintf(conn, "%s\n", message)
	reply, err := bufio.NewReader(conn).ReadString('\n')
	if err != nil {
		return "", err
	}
	return reply, nil
}

func main() {
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		panic(err)
	}
	defer listener.Close()

	ready := make(chan struct{})
	go runServer(listener, ready)
	<-ready

	reply, err := runClient(listener.Addr().String(), "hello")
	if err != nil {
		panic(err)
	}
	fmt.Print(reply)
}
```

Checked with `go vet` and run with `go run`. Output confirmed, `server
received, hello`.

### TypeScript

```typescript
// Minimal client-server example. a Node http server that answers one
// request, and a fetch-based client that calls it.
import http from "node:http";

interface EchoResponse {
  received: string;
}

function startServer(port: number): http.Server {
  const server = http.createServer((req, res) => {
    let body = "";
    req.on("data", (chunk) => {
      body += chunk;
    });
    req.on("end", () => {
      const payload: EchoResponse = { received: body };
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify(payload));
    });
  });
  server.listen(port);
  return server;
}

async function callServer(port: number, message: string): Promise<EchoResponse> {
  const response = await fetch(`http://127.0.0.1:${port}/`, {
    method: "POST",
    body: message,
  });
  return (await response.json()) as EchoResponse;
}

async function main(): Promise<void> {
  const server = startServer(0);
  const address = server.address();
  const port = typeof address === "object" && address ? address.port : 0;

  const result = await callServer(port, "hello");
  console.log(result.received);

  server.close();
}

main();
```

Type-checked with `tsc --noEmit --strict`, zero errors.
