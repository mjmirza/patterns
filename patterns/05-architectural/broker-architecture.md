---
name: Broker
slug: broker-architecture
family: 05-architectural
category: Architectural
aliases: [Object Request Broker, Message Broker, Broker Pattern, Mediator Infrastructure]
first_described: "Buschmann, Meunier, Rohnert, Sommerlad, Stal 1996"
maturity: canonical
related: [mediator, facade, proxy, publish-subscribe, service-locator, adapter]
incompatible_with: []
verified: 2026-08-02
---

# Broker

## 1. Name, aliases, and lineage

The canonical name is Broker. It is documented as an architectural pattern in
Frank Buschmann, Regine Meunier, Hans Rohnert, Peter Sommerlad, and Michael
Stal, *Pattern-Oriented Software Architecture, Volume 1. A System of Patterns*,
Wiley, 1996, in the chapter on distributed systems patterns, where it is
presented as the structuring pattern for decoupled distributed software
systems with interacting components. The book, commonly abbreviated POSA1,
treats Broker as an architectural-level pattern, one layer above the design
patterns catalogued by Gamma, Helm, Johnson, and Vlissides the same decade,
because it concerns how whole processes and machines find and talk to each
other, not how two objects inside one process collaborate.

The dominant alias in industry usage is Object Request Broker, abbreviated
ORB, which is the exact term the Object Management Group standardized in the
Common Object Request Broker Architecture specification. The OMG's own text
states plainly that "the ORB is the basic mechanism by which objects
transparently make requests to, and receive responses from, each other on
the same machine or across a network" (Object Management Group, CORBA
specification landing page, https://www.omg.org/spec/CORBA/, verified
2026-08-02). CORBA is the pattern's most literal and most historically
influential example, to the point that many engineers who never opened
POSA1 still say "broker" and mean "something CORBA-shaped."

A second common alias, Message Broker, names a variant built around
asynchronous message passing rather than synchronous remote procedure calls.
RabbitMQ's own documentation frames this directly. "Messaging brokers receive
messages from publishers, also known as producers, and route them to
consumers, applications that process them" (RabbitMQ AMQP concepts guide,
https://www.rabbitmq.com/tutorials/amqp-concepts, verified 2026-08-02). The
Wikipedia entry on the pattern narrows the vocabulary further by naming three
roles, broker, server as publisher, and client as consumer, and by drawing an
explicit line between Broker and Publish-Subscribe. it describes Broker as a
"many to one to many" shape rather than the "many to many" shape of
Publish-Subscribe (Wikipedia, Broker pattern,
https://en.wikipedia.org/wiki/Broker_pattern, verified 2026-08-02). That
distinction matters and is developed in dimension 13.

No serious source disputes the pattern's name or its POSA1 origin. What
varies across the literature is emphasis. some texts foreground the
synchronous RPC-style broker embodied by CORBA and Java RMI, others foreground
the asynchronous message-queue broker built around RabbitMQ and Kafka-adjacent
systems. Both are the same structural idea, an intermediary that decouples
who is asking from who answers, applied to two different interaction styles.
This entry treats both, because a reader searching for "broker pattern" in
2026 is more likely to land on a message queue than on CORBA, and conflating
the two without saying so produces confused advice.

## 2. Problem and context

A distributed system is made of components running in separate processes,
often on separate machines, that need to call on each other's services. Left
to grow without structure, every component that needs a service from another
component ends up holding a direct, hardcoded reference to it. an IP address
and port, a hostname baked into configuration, a client library pinned to one
specific server's location and protocol version. This produces a system where
every component knows the network topology of every other component it talks
to. Moving a service to a new host breaks every caller. Adding a new
implementation of an existing service means updating every client that could
plausibly want to route to it. Testing a component in isolation means
standing up the real network dependencies it was hardcoded to reach, because
there is no seam at which a test double can be substituted.

The context in which this problem becomes acute is any system where
components are deployed independently, where the set of available service
implementations changes over the system's lifetime (a new server version
rolls out, a service moves to a different data center, a service is
horizontally scaled to multiple instances), or where components written in
different languages or running on different platforms need to interoperate.
In a single-process monolith, the analogous problem is solved by an object
reference or a dependency-injection container. Across a process boundary, an
object reference cannot cross a network, so the problem needs an
infrastructure-level answer rather than a language-level one.

Broker's context is specifically the moment a system moves from objects
calling objects to processes calling processes. The pattern exists because
remote calls have failure modes, marshaling costs, and location concerns that
local calls do not, and because a naive direct-reference approach to remote
calls reproduces every coupling problem that dependency inversion solves
locally, at a scale where the cost of that coupling is far higher.

## 3. Forces

Location transparency pulls toward an intermediary. a client should be able
to invoke a service without knowing, at the call site, which host or process
implements it, so that implementations can move, scale, or be replaced
without touching every caller. This is Broker's central promise and the
force it optimizes hardest.

Performance and latency pull the opposite direction. Every hop through an
intermediary is a hop the message did not need to take if the client already
knew where the server was. A broker that sits in the data path for every
single call adds a network round trip, a marshaling and unmarshaling cost,
and, if the broker itself is a shared process, a possible queueing delay
under load. Systems with hard latency budgets, high-frequency trading being
the extreme case, frequently reject brokered RPC precisely because of this
force, in favor of direct connections established once and cached.

Availability and single points of failure pull toward decentralization. A
broker that is itself one process becomes a component every other component
now depends on transitively. If the broker goes down, no client can locate
any server, even servers that are themselves healthy. This is why production
broker deployments almost always run the broker itself as a replicated,
highly available cluster (a RabbitMQ cluster, a set of CORBA naming service
replicas, a fleet of Binder-equivalent processes), which reintroduces
operational complexity the pattern was partly meant to hide.

Coupling and evolvability pull toward the broker. Client and server code that
never share a direct reference can evolve independently, be deployed on
independent schedules, and be written in unrelated languages, as long as both
sides honor the interface contract the broker mediates. This is the force
CORBA optimized for explicitly, cross-language, cross-platform
interoperability, at the cost of a heavyweight Interface Definition Language
and a marshaling layer that many teams found expensive to maintain.

Operability and observability pull in Broker's favor once the broker exists,
because a single mediation point is also a single point at which to log,
trace, rate-limit, and authenticate every call, and pull against it because
that same single point becomes the thing every incident review has to reason
about. A message broker's queue depth, consumer lag, and connection count
become first-class operational signals that did not exist in a direct-call
architecture, for better and for worse.

Buschmann and coauthors frame the pattern as favoring location transparency,
loose coupling, and interoperability at an accepted cost in latency,
operational surface area, and a new dependency every client now shares. A
Broker system that pretends it did not accept that trade is one that has not
yet had an incident caused by the broker itself.

## 4. Applicability and non-applicability

Reach for Broker when.

- Components must be locatable and callable without hardcoding network
  addresses, because deployment topology changes over the system's life, for
  example services that move between hosts, scale horizontally, or are
  replaced by new implementations without client changes.
- Clients and servers are written in different languages or run on different
  platforms and need a shared, language-neutral contract for calls, which is
  exactly the case CORBA's Interface Definition Language exists to solve.
- Producers of work and consumers of work should be decoupled in time as well
  as in location, so a message broker that buffers and redelivers work is
  appropriate, for example background job processing, event-driven
  integration between independently deployed services, or workloads where a
  consumer being temporarily down should not fail the producer's call.
- Cross-cutting concerns such as authentication, authorization, routing,
  retry, and observability should live in one place rather than being
  reimplemented by every service pair, and centralizing them in a mediating
  process is an acceptable operational trade.
- The system genuinely spans process or machine boundaries. Broker is a
  distributed-systems pattern, it answers a problem that does not exist
  inside a single process.

Do NOT reach for Broker when.

- The components in question live inside the same process. A broker
  mediating between two objects that could simply hold a reference to each
  other is solving a problem that does not exist and adding marshaling
  overhead and indirection for no benefit, use direct references, dependency
  injection, or a Mediator (design pattern) if in-process coordination is
  genuinely complex.
- Latency budgets are tight enough that an extra network hop through an
  intermediary is unacceptable, and the set of communicating parties is
  small and stable enough that direct point-to-point connections, established
  once at startup, are simpler and faster. gRPC's channel model, used
  point-to-point rather than through a shared broker process, is a common
  choice specifically to avoid this cost while keeping location abstraction
  at the client stub level.
- The team cannot operate a highly available broker cluster. A broker that is
  a single unreplicated process is a new single point of failure for the
  entire system, and if the organization lacks the operational maturity to
  run message broker clustering, quorum, or failover correctly, a simpler
  direct-call architecture with client-side load balancing and
  a lightweight service registry queried once per connection rather than
  per call is a safer starting point.
- The interoperability CORBA-style Brokers were built to solve, cross-vendor,
  cross-language binary interoperability with a shared IDL, is not actually
  needed because every component is written in one language and deployed
  from one codebase. In that situation the marshaling and IDL machinery is
  pure cost with no corresponding benefit, and a lighter RPC framework, or
  no broker at all, fits better.
- Strict message ordering across independent producers is required and the
  chosen broker does not provide it as a first-class guarantee for the
  relevant topic or queue shape. treating a general-purpose broker as an
  ordering guarantee without verifying the specific delivery semantics it
  offers is a frequent and costly mistake, covered further in dimension 11.

## 5. Structure

The classic POSA1 Broker structure names six participant roles. Client, the
component initiating a request for a service, unaware at the call site of the
concrete server that will fulfill it. Server, the component implementing one
or more services and registering them with a broker so they can be located
and invoked. Broker, the mediating component that holds the registry of
available servers and their locations, receives requests from clients,
routes them to the appropriate server, and returns responses back to the
originating client. Client-side proxy, a local stub that presents the remote
service's interface to the client as if it were a local object, hiding
marshaling, transport, and location from the caller. Server-side proxy, the
analogous stub on the server side that unmarshals incoming requests, invokes
the real server implementation, and marshals the response. Bridge, an
optional participant that translates between brokers built on incompatible
wire protocols, allowing two otherwise separate broker infrastructures to
interoperate.

Concretely mapped onto CORBA, the client-side proxy is the CORBA stub
generated from an IDL interface, the server-side proxy is the CORBA skeleton,
and the Broker itself is the Object Request Broker runtime plus, in most
deployments, a Naming Service or Trading Service that holds the registry of
available object references. The OMG's own description of the ORB is that "a
client need not be aware of the mechanisms used to communicate with or
activate an object, how the object is implemented, or where the object is
located" (Object Management Group, CORBA specification,
https://www.omg.org/spec/CORBA/, verified 2026-08-02), which is precisely the
client-side proxy's job in the POSA1 structure.

Mapped onto Java RMI, the client-side proxy is the stub obtained from a
lookup, the registry acts as a narrower broker whose only job is name
resolution rather than call routing, and each remote call after that lookup
goes directly between the client's stub and the server's exported object
rather than continuing to pass through the registry. Oracle's own RMI
documentation is explicit about this narrower scope. "A Java RMI registry is
a simplified name service that allows clients to get a reference, a stub, to
a remote object. In general, a registry is used, if at all, only to locate
the first remote object a client needs to use" (Oracle, Java RMI Hello World
tutorial, https://docs.oracle.com/javase/8/docs/technotes/guides/rmi/hello/hello-world.html,
verified 2026-08-02). RMI is a useful contrast case precisely because the
registry only brokers the initial lookup, then steps out of the data path,
which is a materially different structural choice from CORBA's ORB, which
mediates every call.

Mapped onto a message broker such as RabbitMQ, the client and server roles
become producer and consumer, the client-side and server-side proxies become
the publisher's channel and the consumer's channel respectively, and the
Broker is the broker process itself plus its internal routing structures.
RabbitMQ names these routing structures explicitly. "Messages are published
to exchanges, which are often compared to post offices or mailboxes.
Exchanges then distribute message copies to queues using rules called
bindings" (RabbitMQ AMQP concepts guide,
https://www.rabbitmq.com/tutorials/amqp-concepts, verified 2026-08-02). The
exchange plus binding plus queue triad is the message-broker world's answer
to the same routing responsibility CORBA's ORB performs synchronously.

## 6. ASCII structure diagram

```
                         SYNCHRONOUS (RPC-style) BROKER
                         -------------------------------

  +----------+    interface call    +----------------+
  |  Client  | --------------------> | Client-side    |
  |          |                       | Proxy (stub)   |
  +----------+                       +--------+-------+
                                              |
                                     marshaled request
                                              |
                                              v
                                    +--------------------+
                                    |       Broker       |
                                    |  (routing table /  |
                                    |   naming service)  |
                                    +---------+----------+
                                              |
                                     routed request
                                              |
                                              v
                                   +-----------------------+
                                   | Server-side Proxy     |
                                   | (skeleton)             |
                                   +-----------+-----------+
                                               |
                                       unmarshaled call
                                               |
                                               v
                                        +-------------+
                                        |   Server    |
                                        | (real impl) |
                                        +-------------+


                         ASYNCHRONOUS (message) BROKER
                         ------------------------------

  +-----------+  publish   +-----------------------------+
  | Producer  | ---------> |          BROKER              |
  | (Client)  |            |  +----------+   +--------+   |
  +-----------+            |  | Exchange | ->| Queue A|--------> Consumer 1
                            |  +----------+   +--------+   |
                            |       |          +--------+   |
                            |       +--------->| Queue B|--------> Consumer 2
                            |                  +--------+   |
                            +-----------------------------+

  Producer never holds a reference to Consumer 1 or Consumer 2.
  Routing is decided entirely by broker-side bindings.
```

## 7. Dynamics

The synchronous, CORBA-style sequence runs as follows. First, at startup, each
server registers its implementation with the broker's naming or trading
service, associating a well-known name or interface type with a concrete
object reference. Second, a client that wants to use the service looks up
that name through the broker, receiving back a client-side proxy that
implements the same interface the server exposes but contains, internally,
only the information needed to reach the broker or the resolved server
location. Third, the client invokes a method on the proxy exactly as it
would on a local object. Fourth, the proxy marshals the method name and
arguments into a wire format and sends the request, either directly to the
resolved server (as in RMI after the initial lookup) or through the broker
itself (as in a CORBA deployment where the ORB continues to mediate). Fifth,
on the server side a matching server-side proxy unmarshals the request,
invokes the real implementation, and marshals the return value or exception
back across the wire. Sixth, the client-side proxy receives the response,
unmarshals it, and returns it to the calling code as if the whole round trip
had been an ordinary local method return.

The asynchronous, message-broker sequence differs in a way that matters for
reasoning about failure. First, a producer opens a connection and a channel
to the broker, then publishes a message to a named exchange, tagging it with
a routing key. Second, the exchange evaluates its bindings, the rules that
say which queues should receive a copy of messages matching this routing key,
and copies the message into each matching queue. Third, the producer's
publish call returns as soon as the broker has accepted the message, without
waiting for any consumer to process it. this is the decoupling in time that
the synchronous broker does not provide. Fourth, independently and on their
own schedule, each consumer bound to a queue either has messages pushed to it
by the broker or pulls messages from the queue, processes each one, and
acknowledges successful processing back to the broker. Fifth, if a consumer
disconnects or fails to acknowledge, the broker redelivers the unacknowledged
message, either to the same consumer on reconnect or to another consumer
bound to the same queue, depending on configuration. RabbitMQ's own framing
of this is that the broker supports "push API, recommended, and pull API,"
letting consumers process messages on their own schedule rather than in real
time lockstep with producers (RabbitMQ AMQP concepts guide,
https://www.rabbitmq.com/tutorials/amqp-concepts, verified 2026-08-02).

## 8. Implementation variants

The full ORB variant, seen in CORBA, is the heaviest and most literal
reading of POSA1. it defines an Interface Definition Language independent of
any programming language, generates stubs and skeletons from that IDL for
each target language, and routes every single call through the broker
runtime, which resolves object references and can apply interceptors for
cross-cutting concerns on every invocation. The cost is a nontrivial build
toolchain (an IDL compiler per language) and, historically, interoperability
friction between different vendors' ORB implementations before the
General Inter-ORB Protocol standardized the wire format.

The lookup-once, call-direct variant, seen in Java RMI, uses the
broker, the RMI registry, only to resolve an initial name to a stub, after
which the stub talks directly to the exported remote object without the
registry remaining in the data path. This trades away some of the pattern's
promise, a server that changes location after a client has already looked it
up is not transparently rerouted, in exchange for lower per-call latency and
a much simpler broker, the registry does one thing, name to stub resolution.

The kernel-mediated IPC variant, seen in Android's Binder driver and
its accompanying servicemanager process, moves the broker into the operating
system kernel for the transport layer while keeping a userspace registry
process for service lookup. Android's own documentation on this describes
servicemanager as historically the place where "binder services were
registered ... where they could be retrieved by other processes" (Android
Open Source Project, Binder IPC documentation,
https://source.android.com/docs/core/architecture/hidl/binder-ipc, verified
2026-08-02), and documents a later split into a framework-only
servicemanager and a separate vndservicemanager for vendor processes,
demonstrating that even within one variant a broker's registry can itself be
partitioned for isolation reasons.

The message-broker variant, seen in RabbitMQ, ActiveMQ, and similar
AMQP or STOMP implementations, foregoes synchronous request-response
entirely in favor of publish and consume against named exchanges and queues,
with the broker owning durable storage of in-flight messages, acknowledgment
tracking, and redelivery. This variant is the one most engineers encounter
first in 2026, because it underlies the majority of background job systems
and event-driven service integration in production web systems.

The kernel-adjacent shared-bus variant, seen in D-Bus on Linux
desktop and embedded systems, runs a userspace daemon, the message bus, that
"accepts connections from multiple other applications, and forwards messages
among them," using header fields such as a destination name to decide
routing (freedesktop.org, D-Bus specification,
https://dbus.freedesktop.org/doc/dbus-specification.html, verified
2026-08-02). D-Bus explicitly transforms an underlying one-to-one protocol
into a many-to-many system purely through the bus daemon acting as broker,
which is a clean illustration of the pattern's core trick. the protocol
between any two parties can stay simple if a third party is willing to
relay for everyone.

The client-stub, channel-based RPC variant, seen in gRPC, keeps the
client-side proxy concept, "the client has a stub that provides the same
methods as the server" (Google, gRPC introduction,
https://grpc.io/docs/what-is-grpc/introduction/, verified 2026-08-02), but
usually establishes a direct channel between one client and one known
server address rather than routing every call through a separate shared
broker process. gRPC is frequently paired with an external service registry
or a sidecar proxy (in a service mesh) to regain the location-transparency
benefit of a full broker, illustrating that the broker's registry and
routing responsibilities can be decomposed and relocated rather than
bundled into one process, a variation not explicitly named in POSA1 but
common in 2020s microservice architectures.

## 9. Known production uses

CORBA's Object Request Broker is the pattern's namesake production use. the
OMG's own specification describes the ORB as the mechanism by which "objects
transparently make requests to, and receive responses from, each other on
the same machine or across a network" (Object Management Group, CORBA
specification, https://www.omg.org/spec/CORBA/, verified 2026-08-02), and
CORBA implementations were deployed widely in telecommunications and
enterprise middleware through the late 1990s and 2000s.

Java RMI's registry, part of the standard Java class library since JDK 1.1,
brokers the initial resolution of a service name to a remote stub, as
documented directly by Oracle. "Once a remote object is registered on the
server, callers can look up the object by name, obtain a remote object
reference, and then invoke remote methods on the object" (Oracle, Java RMI
Hello World tutorial,
https://docs.oracle.com/javase/8/docs/technotes/guides/rmi/hello/hello-world.html,
verified 2026-08-02).

Android's Binder IPC mechanism, the transport underlying essentially every
inter-process call on the Android platform, from an app calling into a
system service to two system services calling each other, uses
servicemanager as a broker-style registry. the Android Open Source Project
documents that "binder services were registered with servicemanager, where
they could be retrieved by other processes," and that this was later
partitioned into separate framework and vendor registries for isolation
(Android Open Source Project, Binder IPC documentation,
https://source.android.com/docs/core/architecture/hidl/binder-ipc, verified
2026-08-02).

RabbitMQ, one of the most widely deployed open source message brokers,
implements the AMQP model of exchanges, bindings, and queues as its
broker-side routing structure, and its own documentation describes its core
job directly. "Messaging brokers receive messages from publishers ... and
route them to consumers" (RabbitMQ AMQP concepts guide,
https://www.rabbitmq.com/tutorials/amqp-concepts, verified 2026-08-02).
RabbitMQ underlies background job processing and service-to-service
integration in a very large number of production web systems.

D-Bus is the standard inter-process communication broker on Linux desktop
environments (GNOME and KDE both depend on it) and in embedded Linux
systems, where its message bus daemon "accepts connections from multiple
other applications, and forwards messages among them" (freedesktop.org,
D-Bus specification,
https://dbus.freedesktop.org/doc/dbus-specification.html, verified
2026-08-02), turning point-to-point connections into a shared many-to-many
messaging fabric for the whole desktop session.

## 10. Consequences

Positive consequences. Clients gain location transparency, meaning a service
implementation can move, be replaced, or be scaled without every caller
being touched, because the caller only ever addresses a name or interface
that the broker resolves. Cross-language and cross-platform interoperability
becomes achievable through a shared, broker-mediated contract rather than
requiring every pair of components to agree on a bespoke wire format, which
is precisely the problem CORBA's IDL was built to solve. Cross-cutting
concerns, authentication, authorization, rate limiting, logging, and tracing
of every remote call, gain a single natural implementation point at the
broker rather than needing to be reimplemented in every service. Producers
and consumers in the asynchronous variant gain temporal decoupling. a
producer can publish work and continue immediately even if every consumer is
currently offline, and the broker's durable queue absorbs the gap, which is
the property background job systems depend on.

Negative consequences. The broker becomes a new dependency shared by every
component in the system, and if it is not itself made highly available, it
is a single point of failure that can take down communication between
otherwise healthy components. Every call routed through a synchronous
broker pays a real latency cost, usually an additional network hop plus
marshaling and unmarshaling overhead, compared to a direct call between
components that already know each other's location. Operational complexity
increases, because the broker itself now needs monitoring, capacity
planning, upgrade procedures, and disaster recovery, and a message broker
specifically introduces new failure modes around queue depth, consumer lag,
and message redelivery that a direct-call system never had to reason about.
Debugging becomes harder in the synchronous variant because a call's
execution now spans at least three processes, client, broker, server, rather
than one, and a stack trace on the server side no longer shows the client's
call site without additional distributed tracing infrastructure. In the
CORBA-style full-ORB variant specifically, the IDL toolchain and code
generation step adds build complexity and a class of stub-out-of-date bugs,
where a generated client stub silently drifts from the server's real
interface, that a same-language, same-process call could never produce.

## 11. Failure modes and misuse

Symptom. every request across the whole system slows down or times out at
once, with no single service showing unusually high CPU or memory use.
Cause. the broker itself, being shared infrastructure, is saturated or is
experiencing a garbage collection pause, a full connection pool, or a
network partition, and because every service routes through it, its
degradation looks like a system-wide outage rather than a single service's
outage. Fix. monitor the broker's own resource usage and connection counts
as a first-class signal separate from any individual service's metrics, and
size the broker cluster for peak aggregate load across all services rather
than for any one service's typical load.

Symptom. messages appear to vanish, or the same message is processed twice
by different consumers, with no application-level bug visible in the
consumer code. Cause. the team assumed the broker guarantees exactly-once
delivery and strict ordering by default, when the actual delivery semantics
configured (at-most-once, at-least-once, or a specific ordering guarantee
scoped to a single queue or partition) do not match that assumption. this is
one of the most common production incidents attributed to message brokers,
and it is a misuse of the pattern's assumptions rather than a bug in the
broker. Fix. read and explicitly test the delivery guarantee the broker
provides for the specific topology in use (a single queue behind one
consumer behaves very differently from a fan-out to multiple competing
consumers), and build idempotent consumers if at-least-once delivery is what
is actually offered.

Symptom. a service that has been redeployed to a new host continues to
receive zero traffic, or clients continue calling a stale, now-dead
instance, well after the redeploy. Cause. the broker's registry entry was
never updated, either because the deploy process forgot to re-register, or
because a lookup-once client (as in the RMI variant) cached a stale stub and
never re-resolves it. Fix. make registration and deregistration part of the
deploy and shutdown lifecycle explicitly, with a health check or lease
mechanism so a crashed server's stale registration expires rather than
lingering, and prefer client patterns that re-resolve periodically or on
connection failure rather than caching a resolved reference forever.

Symptom. the broker becomes, functionally, a shared mutable god object that
every team is afraid to touch, and every incident review ends the same way,
naming the broker as the cause again. Cause. teams treated the broker as
free infrastructure and progressively piled cross-cutting logic, business
rules, transformation steps, and orchestration into broker-side
configuration (custom exchange plugins, elaborate routing rules, message
transformation middleware) rather than keeping the broker's job limited to
routing and delegating business logic to the services on either end. This is
the well-documented smart-pipes, dumb-endpoints failure mode that later
drove the industry shift toward the opposite philosophy in lightweight
service-to-service architectures. Fix. keep the broker's responsibility to
routing, delivery, and the cross-cutting concerns genuinely common to every
call (auth, tracing, rate limiting), and push business logic and
transformation into the producing or consuming services.

Symptom. local integration tests pass reliably but the same code fails
intermittently in the deployed environment. Cause. tests were written
against an in-process fake or a co-located single-node broker with no
network latency or partition behavior, so the tests never exercised the
failure modes (dropped connections, redelivery, out-of-order arrival under
load) that a real network-separated broker exhibits. Fix. include a
contract-level test against a real broker instance, even a locally run one
over an actual network socket rather than an in-process substitute, and
explicitly test consumer behavior under redelivery and duplicate messages.

## 12. Trade-off matrix

| Force | Broker (mediated) | Direct point-to-point RPC (e.g. plain gRPC channel) | Service Locator (client-side registry lookup, direct call after) | Publish-Subscribe (topic-based, many-to-many) |
|---|---|---|---|---|
| Location transparency | Strong, broker resolves location on every call or on lookup | Weak, client must already know or be given the address | Moderate, resolved once via locator, then cached, can go stale | Strong for topic membership, weak for point identity |
| Per-call latency | Higher, extra hop through broker in the full-ORB variant | Lowest, single hop once connected | Low after initial lookup, matches direct RPC after that | Moderate, broker-mediated fan-out per message |
| Single point of failure risk | Real, mitigated only by clustering the broker | None from an intermediary, but no location abstraction either | Real for the locator itself, though it is off the data path after lookup | Real, same as message broker |
| Cross-language interoperability | Strong when the broker defines a language-neutral contract (CORBA IDL) | Depends entirely on the RPC framework's own cross-language support | Depends on the locator's protocol, not inherent to the pattern | Strong when the wire format (AMQP, protobuf) is shared |
| Temporal decoupling of caller and callee | Strong in the asynchronous message-broker variant, none in the synchronous ORB variant | None, caller blocks or fails if callee is unreachable | None, same as direct RPC once resolved | Strong, publishers do not need any subscriber present |
| Operational burden | High, broker needs its own HA, monitoring, capacity planning | Low, no shared infrastructure to operate beyond the endpoints themselves | Moderate, locator needs HA but carries less traffic than a data-path broker | High, same class of burden as message broker |

## 13. Related and incompatible patterns

Mediator, the design-pattern-level cousin, solves the same fundamental
problem, many-to-many coupling replaced by many-to-one-to-many coupling,
inside a single process between objects rather than across process
boundaries between distributed components. Reading Broker as "Mediator, but
for a distributed system, with the added concerns of marshaling, network
failure, and locating a service across a machine boundary that a single process never has" is an
accurate and useful mental shortcut, and the two patterns are frequently
described side by side in architecture texts for exactly this reason.

Facade composes naturally on top of a Broker. a client-side proxy generated
for a broker call is, in shape, a facade that presents a simple,
local-looking interface in front of the marshaling, transport, and location
resolution machinery underneath. The two are not redundant. Facade
simplifies an interface, Broker relocates where an implementation lives, and
a well-built broker client stub does both at once.

Proxy is the pattern that literally names the client-side and server-side
stub participants in Broker's own structure. A Broker's client-side proxy is
a remote proxy in the classic Gang of Four sense, an object that stands in
for another object that lives elsewhere and is expensive or impossible to
reference directly.

Publish-Subscribe is closely related to the message-broker variant of
Broker and is easy to conflate with it, but the two differ in how many parties are involved
and in what a producer knows. In a Broker-mediated request, per Wikipedia's
framing, the shape is "many to one to many," meaning many clients route
through one broker to reach many possible servers, with the broker usually
still able to identify a specific request-response pairing. In
Publish-Subscribe proper the shape is "many to many," publishers broadcast
to a topic with no awareness of, or response from, any specific subscriber
(Wikipedia, Broker pattern, https://en.wikipedia.org/wiki/Broker_pattern,
verified 2026-08-02). A message broker like RabbitMQ can implement either
shape depending on how exchanges and bindings are configured, which is part
of why the two pattern names get used almost interchangeably in casual
conversation despite naming genuinely different coupling topologies.

Service Locator is a lighter-weight relative that keeps the resolve-a-name-
to-a-concrete-reference responsibility of a broker's registry but
deliberately drops the mediate-every-subsequent-call responsibility, so
that after an initial lookup the client talks directly to the resolved
server. Java RMI's registry, described in dimension 5, sits exactly on this
boundary, arguably closer to Service Locator than to a full ORB.

Adapter is frequently needed at a Broker's boundary, not as a substitute for
it, when two brokers speak incompatible wire protocols and need to
interoperate. this is the role POSA1 assigns to the Bridge participant in
the full six-role structure, and it is functionally an Adapter operating at
the level of an entire messaging protocol rather than a single class
interface.

No pattern in this repository is flatly incompatible with Broker in the
sense of being impossible to combine, but Broker is in active tension with
any design goal that treats minimizing operational surface area as the
highest priority, since introducing a broker is, definitionally, introducing
new shared infrastructure that must be run, monitored, and kept available.

## 14. Refactoring path in and out

Introducing a Broker into a system that currently uses direct, hardcoded
references between components proceeds in stages rather than as a single
cutover. First, introduce a client-side proxy in front of every existing
direct call, even before any broker exists, so that callers stop referencing
concrete network addresses directly and instead call through an interface,
this alone, done first, is the highest-value step because it creates the
seam at which a real broker can later be inserted with zero changes to
calling code. Second, stand up the broker infrastructure itself, whether
that is a naming service, a message broker cluster, or a service registry,
and have it run alongside the existing direct connections without yet being
load-bearing, so its own operational behavior can be observed under real
traffic patterns before anything depends on it. Third, migrate servers to
register themselves with the broker rather than being addressed by a fixed,
hand-maintained configuration entry, one service at a time, verifying after
each migration that lookups resolve correctly and that a server restart or
relocation is transparently picked up. Fourth, migrate the client-side
proxies from their temporary direct-connection implementation to a real
broker-backed implementation, again one caller at a time, so that a
regression in any single migrated caller is isolated and easy to attribute.
Fifth, once every caller and every server has migrated, retire the old
hardcoded configuration entirely and make the broker registry the single
source of truth for service location.

Removing a Broker when it has stopped earning its place, most often because
the system has consolidated onto a small, stable set of services where
location transparency no longer buys anything and the broker's latency and
operational cost has become the larger burden, proceeds in the reverse
order. First, identify caller-server pairs that are stable enough that
direct connection is safe, meaning the server's location genuinely does not
change without a coordinated deploy of both sides. Second, for each such
pair, replace the broker-mediated call with a direct connection while
keeping the same client-side proxy interface, so the calling code does not
need to change even though what is underneath it does, this is the mirror
image of the introduction path's first step and is why keeping that proxy
seam in place, even after the broker is fully removed, remains valuable.
Third, once every caller has been migrated off the broker for a given
service, decommission that service's broker registration, and once every
service has been migrated, decommission the broker infrastructure entirely.
Removing a Broker without first confirming location stability for every
migrated pair is the most common way this refactor causes an outage, because
it silently reintroduces the exact hardcoded-address coupling problem the
broker existed to solve.

## 15. Testing and verification

What becomes easier to test because of Broker. individual client and server
components can be tested in isolation against a fake or stub implementation
of the broker's interface, without standing up the real network
infrastructure, because the client-side proxy is already an interface seam
designed for substitution. A server's business logic can be unit tested
completely independently of the transport and marshaling layer, since the
server-side proxy already isolates that concern.

What becomes harder to test because of Broker. correctness properties that
depend on the broker's real delivery, ordering, and failure behavior, such
as at-least-once delivery producing duplicate messages, or a network
partition causing a temporary inability to resolve a service, cannot be
exercised by an in-process fake, and a test suite that only ever runs
against a fake broker will systematically miss the failure modes described
in dimension 11. Distributed tracing across a broker-mediated call chain is
also harder to reason about in a plain unit test, since the call now spans
process and, in most deployments, machine boundaries.

Recommended technique for the client side, use a test double that implements
the same interface the client-side proxy exposes, returning canned responses
or simulating specific failures (timeout, connection refused, malformed
response), so business logic can be tested without a live broker.
Recommended technique for the server side, similarly stub the server-side
proxy's delivery of an unmarshaled request, so the server's handler logic is
tested without needing the marshaling layer to be exercised on every test
run. Recommended technique for the integration boundary itself, run a real,
local instance of the actual broker technology in use (a real RabbitMQ
container, a real local ORB, a real local D-Bus session bus) in at least a
subset of the test suite, and explicitly script failure injection against
it, disconnecting a consumer mid-processing and asserting the message is
redelivered, publishing faster than a consumer can drain and asserting
backpressure or queueing behaves as expected, so the delivery guarantee
assumptions from dimension 11 are verified rather than assumed.

## 16. Observability signals

For the synchronous ORB variant, the signals that distinguish a healthy
broker from a struggling one are per-call latency measured specifically at
the broker hop (distinct from end-to-end latency, so the broker's own
contribution is visible), the count of currently open client connections
and whether that count is approaching any configured connection limit, the
rate of lookup or registration failures against the naming service, and the
error rate of calls that fail specifically inside the broker (a marshaling
error, a routing failure to an unregistered name) as distinct from errors
returned by the server's business logic.

For the asynchronous message-broker variant, the primary health signal is
consumer lag, the gap between the newest message published to a queue and
the position of the slowest consumer processing that queue, because a
growing lag is the earliest and most reliable indicator that consumers
cannot keep pace with producers, well before the queue overflows any
configured limit. Alongside lag, queue depth itself, the connection and
channel count per broker node, the message redelivery rate (a high
redelivery rate points at either slow acknowledgment or crashing consumers),
and the rate of messages routed to a dead-letter queue, if one is
configured, are the signals an operator should have on a dashboard before
the broker is trusted with production traffic.

A healthy broker of either variant, on a dashboard, shows stable or
gradually trending resource usage, a lookup or routing error rate near
zero, and, for the message variant, consumer lag that returns to zero
between bursts of activity. A failing broker shows lookup or routing errors
climbing while individual services report no errors of their own, connection
counts climbing toward a limit without a corresponding increase in real
client traffic (often a sign of a client-side connection leak rather than
a broker problem), or consumer lag climbing monotonically with no recovery,
which indicates the system is falling permanently behind rather than
absorbing a transient burst.

## 17. Security and privacy implications

Because every mediated call passes through the broker, the broker is a
natural point at which to enforce authentication and authorization
centrally, which is a genuine security benefit over an architecture where
every service pair has to implement its own auth check. CORBA's security
service and modern message brokers' built-in TLS and per-user access control
lists exist for exactly this reason. This same centrality is also a risk. a
broker that is compromised, or whose access control configuration is
misconfigured, can see, and in the asynchronous variant can persist to
disk, the payload of every message flowing between every pair of services
that use it, making it an attractive single target for an attacker and a
large blast radius for a single misconfiguration.

Message payloads that transit a broker are frequently written to durable
storage as part of the broker's delivery guarantee, meaning any personally
identifiable or otherwise sensitive data included in a message body is at
rest on the broker's disk, not only in transit, for as long as the message
remains unacknowledged or is retained for redelivery purposes. a system
handling regulated data needs to account for the broker's own storage as a
data-at-rest location subject to the same encryption and retention
requirements as any database. Access control at a broker is commonly
implemented per queue, per topic, or per exchange rather than per message,
which means a service granted read access to a queue can read every message
routed to that queue regardless of which originating producer or which
downstream purpose it was intended for, unless the broker's finer-grained
authorization features are explicitly configured and used.

CORBA's own security history is a documented cautionary example. early ORB
implementations frequently shipped with weak or optional authentication
between client and server, relying on network-level trust (a private
network, a firewall) rather than cryptographic identity, and organizations
that later needed to expose CORBA services across untrusted networks had to
retrofit security services that were not part of the original, widely
deployed baseline. The general lesson generalizes past CORBA specifically.
a broker's default configuration frequently favors ease of getting started
over secure-by-default access control, and a team adopting any broker
technology should treat authentication, transport encryption, and
per-resource authorization as explicit requirements to configure rather than
assumptions to make about the default install.

## Code examples

Three languages, all run and verified. Python and Go, being the target
languages for the broker's registry-heavy structure in modern deployments,
and TypeScript, since Node.js is the most common client-runtime target for
message-broker producers and consumers. Java and Rust are omitted from the
worked examples here for space, not because the pattern does not translate;
both have idiomatic broker-client shapes (Java's own RMI stub generation,
Rust's typed channel-based clients for gRPC via tonic) and either
implementation would follow the identical registry-plus-proxy shape shown
below.

Each example implements the same minimal synchronous Broker. a registry
that maps a service name to a handler function, and a client-side proxy that
looks like an ordinary local call but routes through the broker's registry
to reach the concrete handler. Each example also demonstrates the failure
path, calling a service name the broker has no handler for, to make the
Broker's location-resolution responsibility, and its failure mode when
resolution fails, concrete rather than abstract.

### Python

```python
"""Minimal synchronous Broker. registry plus client-side proxy."""
from __future__ import annotations
from typing import Callable, Dict


class Broker:
    def __init__(self) -> None:
        self._registry: Dict[str, Callable[[str], str]] = {}

    def register(self, name: str, handler: Callable[[str], str]) -> None:
        self._registry[name] = handler

    def dispatch(self, name: str, payload: str) -> str:
        if name not in self._registry:
            raise LookupError(f"no server registered for {name!r}")
        return self._registry[name](payload)


class ClientProxy:
    """Looks like a local call, actually routes through the broker."""

    def __init__(self, broker: Broker, service_name: str) -> None:
        self._broker = broker
        self._service_name = service_name

    def call(self, payload: str) -> str:
        return self._broker.dispatch(self._service_name, payload)


def greet_handler(payload: str) -> str:
    return f"hello, {payload}"


if __name__ == "__main__":
    broker = Broker()
    broker.register("greeter", greet_handler)

    proxy = ClientProxy(broker, "greeter")
    result = proxy.call("world")
    assert result == "hello, world", result
    print(result)

    try:
        ClientProxy(broker, "missing").call("x")
        raise SystemExit("expected LookupError")
    except LookupError as exc:
        print("caught expected failure:", exc)
```

Run with `python3 broker.py`. Verified output.

```
hello, world
caught expected failure: no server registered for 'missing'
```

### TypeScript

```typescript
// Minimal synchronous Broker. registry plus client-side proxy.

type Handler = (payload: string) => string;

class Broker {
  private registry = new Map<string, Handler>();

  register(name: string, handler: Handler): void {
    this.registry.set(name, handler);
  }

  dispatch(name: string, payload: string): string {
    const handler = this.registry.get(name);
    if (!handler) {
      throw new Error(`no server registered for "${name}"`);
    }
    return handler(payload);
  }
}

class ClientProxy {
  constructor(private broker: Broker, private serviceName: string) {}

  call(payload: string): string {
    return this.broker.dispatch(this.serviceName, payload);
  }
}

function main(): void {
  const broker = new Broker();
  broker.register("greeter", (payload) => `hello, ${payload}`);

  const proxy = new ClientProxy(broker, "greeter");
  const result = proxy.call("world");
  if (result !== "hello, world") {
    throw new Error(`unexpected result: ${result}`);
  }
  console.log(result);

  try {
    new ClientProxy(broker, "missing").call("x");
    throw new Error("expected dispatch failure");
  } catch (err) {
    console.log("caught expected failure:", (err as Error).message);
  }
}

main();
```

Compiled with `tsc --target es2020 --module commonjs --strict` (TypeScript
7.0.2) and run with `node`. Verified output.

```
hello, world
caught expected failure: no server registered for "missing"
```

### Go

```go
package main

import "fmt"

// Handler is the signature every registered server implements.
type Handler func(payload string) (string, error)

// Broker holds the registry of servers and dispatches to them.
type Broker struct {
	registry map[string]Handler
}

func NewBroker() *Broker {
	return &Broker{registry: make(map[string]Handler)}
}

func (b *Broker) Register(name string, h Handler) {
	b.registry[name] = h
}

func (b *Broker) Dispatch(name string, payload string) (string, error) {
	h, ok := b.registry[name]
	if !ok {
		return "", fmt.Errorf("no server registered for %q", name)
	}
	return h(payload)
}

// ClientProxy looks like a local call but routes through the broker.
type ClientProxy struct {
	broker      *Broker
	serviceName string
}

func NewClientProxy(b *Broker, serviceName string) *ClientProxy {
	return &ClientProxy{broker: b, serviceName: serviceName}
}

func (p *ClientProxy) Call(payload string) (string, error) {
	return p.broker.Dispatch(p.serviceName, payload)
}

func main() {
	broker := NewBroker()
	broker.Register("greeter", func(payload string) (string, error) {
		return "hello, " + payload, nil
	})

	proxy := NewClientProxy(broker, "greeter")
	result, err := proxy.Call("world")
	if err != nil {
		panic(err)
	}
	if result != "hello, world" {
		panic("unexpected result: " + result)
	}
	fmt.Println(result)

	_, err = NewClientProxy(broker, "missing").Call("x")
	if err == nil {
		panic("expected dispatch failure")
	}
	fmt.Println("caught expected failure:", err)
}
```

Run with `go run broker.go`. Verified output.

```
hello, world
caught expected failure: no server registered for "missing"
```

All three examples model the synchronous-RPC variant from dimension 8
rather than the message-broker variant, because the registry-plus-proxy
shape is the structural core POSA1 names, and it is the shape every other
variant, including the asynchronous ones, specializes from.

## 18. References

1. Buschmann, F., Meunier, R., Rohnert, H., Sommerlad, P., Stal, M.
   *Pattern-Oriented Software Architecture, Volume 1. A System of Patterns*.
   Wiley, 1996. Distributed systems patterns chapter, Broker pattern. This
   book is the original primary source for the six-role structure described
   in dimension 5. it was not directly fetched during this verification pass
   and is cited from the well-established secondary consensus about its
   contents (Wikipedia's Broker pattern entry, reference 8 below, and the
   general software architecture literature), so the exact page numbers are
   not independently confirmed here.

2. Object Management Group. CORBA specification landing page.
   https://www.omg.org/spec/CORBA/. Verified 2026-08-02. Source for the ORB
   definition and location-transparency claim.

3. Oracle. Java RMI Hello World tutorial.
   https://docs.oracle.com/javase/8/docs/technotes/guides/rmi/hello/hello-world.html.
   Verified 2026-08-02. Source for the RMI registry's lookup-once behavior
   and the registry-as-simplified-name-service framing.

4. Android Open Source Project. Binder IPC documentation.
   https://source.android.com/docs/core/architecture/hidl/binder-ipc.
   Verified 2026-08-02. Source for servicemanager as a registry and the
   framework and vendor servicemanager split introduced in Android 8.

5. RabbitMQ. AMQP 0-9-1 concepts guide.
   https://www.rabbitmq.com/tutorials/amqp-concepts. Verified 2026-08-02.
   Source for the broker, exchange, binding, and queue routing model, and
   the push and pull consumption API description.

6. freedesktop.org. D-Bus specification.
   https://dbus.freedesktop.org/doc/dbus-specification.html. Verified
   2026-08-02. Source for the D-Bus message bus daemon's forwarding role and
   destination-header-based routing.

7. Google. gRPC introduction, What is gRPC.
   https://grpc.io/docs/what-is-grpc/introduction/. Verified 2026-08-02.
   Source for the client stub and channel-based RPC framing used as a
   contrast case to a shared broker process.

8. Wikipedia. Broker pattern.
   https://en.wikipedia.org/wiki/Broker_pattern. Verified 2026-08-02.
   Source for the three-role vocabulary (broker, server, client) and the
   many-to-one-to-many versus many-to-many distinction against
   Publish-Subscribe.
