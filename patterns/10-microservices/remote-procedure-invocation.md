---
name: Remote Procedure Invocation
slug: remote-procedure-invocation
family: 10-microservices
category: Communication
aliases: [RPI, RPC, Request Reply Communication]
first_described: "Richardson, microservices.io, Remote Procedure Invocation pattern"
maturity: canonical
related: [api-gateway, service-registry, circuit-breaker, self-contained-service, transactional-outbox]
incompatible_with: []
verified: 2026-08-02
---

# Remote Procedure Invocation

## 1. Name, aliases, and lineage

The canonical name in the microservices pattern catalog is Remote Procedure
Invocation, abbreviated RPI. Chris Richardson describes it on microservices.io
as a pattern where a client makes a request to a service "using a
request/reply-based protocol" ([microservices.io, Remote Procedure Invocation
pattern](https://microservices.io/patterns/communication-style/rpi.html),
verified 2026-08-02). Richardson's catalog is the reference most microservices
literature cites for this family of communication patterns, alongside his book
*Microservices Patterns*, Manning, 2018.

The older and more widely known name for the same idea is Remote Procedure
Call, RPC, a term that predates microservices by decades. Andrew Birrell and
Bruce Nelson coined the phrase in their 1984 ACM Transactions on Computer
Systems paper "Implementing Remote Procedure Calls," describing a mechanism
that lets a program call a procedure whose body executes on a different
machine, with the calling convention made to look as close as possible to a
local call. Richardson's RPI is a restatement of that idea scoped to service
to service communication inside a microservice architecture, and it
deliberately folds in synchronous HTTP based styles, plain REST calls, that a
strict academic reading of RPC would treat as a distinct thing.

Three distinct technologies are commonly grouped under this pattern name, and
telling them apart matters for the rest of this entry. Plain HTTP with a REST
style API, where the request and response are ordinary HTTP verbs and a JSON
or similar body. gRPC, Google's binary RPC framework built on HTTP/2 and
Protocol Buffers, open sourced in August 2016 ([Wikipedia, gRPC, Release
information section](https://en.wikipedia.org/wiki/GRPC), verified
2026-08-02). And Apache Thrift, an interface definition language and binary
protocol originally built inside Facebook and donated to the Apache Software
Foundation in 2008 ([Wikipedia, Apache Thrift, History
section](https://en.wikipedia.org/wiki/Apache_Thrift), verified 2026-08-02).
Richardson's own page names all three as the representative RPI technologies
([microservices.io, Remote Procedure Invocation
pattern](https://microservices.io/patterns/communication-style/rpi.html),
verified 2026-08-02).

## 2. Problem and context

A microservice architecture splits a system into many independently deployable
services, and almost every non-trivial request touches more than one of them.
An order placement might need the inventory service to check stock, the
pricing service to compute a total, and the payments service to authorize a
charge. Something has to carry that request across the process boundary that
separates each service, because the services no longer share memory, no longer
share a transaction, and often run on different hosts.

The most direct answer available to an engineer coming from a monolith is to
make the cross-service call look and feel as much like an ordinary in-process
method call as the platform will allow. Define an interface. Generate or hand
write a client stub that implements that interface. Have the stub serialize
the arguments, send them over the network to the service that owns the real
implementation, wait for the reply, deserialize it, and hand it back to the
caller as if nothing had crossed a wire. That is Remote Procedure Invocation.
It is the default first reach in a new microservice system precisely because
it costs the caller almost nothing conceptually. The calling code reads like
an ordinary function call, `inventoryClient.checkStock(sku)`, not like a
message published onto a queue with no return value.

The pattern belongs specifically to the request driven, synchronous corner of
inter-service communication. It sits opposite the messaging based patterns,
Domain Event, publish and subscribe over a broker, that decouple the caller
from the callee in time as well as in space. RPI is the right frame whenever
the caller genuinely needs an answer before it can proceed, and genuinely needs
that answer synchronously, in the same logical operation. It is the wrong
frame whenever the caller does not need to wait, because waiting is exactly
what RPI forces the caller to do.

## 3. Forces

**Latency and coupling in time.** RPI gives the caller an answer immediately,
which is what most request handling logic wants, but it also chains the
caller's own response time to the callee's response time, and if the call
fans out to several downstream services in sequence, the latencies stack.

**Availability.** Richardson states the underlying force plainly, RPI needs
"the client and the service to both be available for the duration of the
interaction" ([microservices.io, Remote Procedure Invocation
pattern](https://microservices.io/patterns/communication-style/rpi.html),
verified 2026-08-02). A message broker based pattern can accept a message even
while the consumer is down. A synchronous RPI call cannot. The callee has to be
up, reachable, and fast enough, right now, or the caller fails right now too.

**Coupling in contract.** The caller must know the exact shape of the
callee's interface, whether that shape is expressed as a Protocol Buffers
schema, a Thrift IDL file, or an OpenAPI document. A change to that shape is
felt by every caller, immediately, which is a much tighter coupling than a
message schema that a consumer can choose to ignore fields on.

**Discoverability.** The caller has to find a live network address for an
instance of the callee before it can even attempt the call, which is the
service discovery force this pattern composes with directly.

**Familiarity and tooling.** Against all of the above, RPI wins because
engineers already understand it. Code generation from an IDL produces
strongly typed clients, IDE autocomplete works, and stack traces read like
ordinary call stacks up to the point where the network boundary is crossed.
This is a real force, not a minor one, because it determines how quickly a
team can build correct software.

The pattern trades availability and temporal decoupling for low latency, on
the happy path, and developer familiarity. Any team choosing RPI over a
messaging pattern is making that trade, whether they name it or not.

## 4. Applicability and non-applicability

Use Remote Procedure Invocation when the caller needs a synchronous answer
before it can continue its own logic, for example an authorization check
before allowing a payment. Use it for internal, low fan-out calls where the
downstream service is inside the same trust boundary and its availability is
comparable to the caller's own availability target. Use it when the operation
is naturally read-like or a single-step command with an immediate result, and
when strong typing and IDE tooling materially reduce the rate of integration
bugs, which is gRPC and Thrift's strongest selling point over hand-rolled
JSON contracts.

Do not use RPI as the default communication style for a workflow that spans
many services and must survive any one of them being briefly unavailable. A
synchronous call chain of five services multiplies the combined availability
down toward the product of each individual service's availability, and every
extra synchronous hop adds to the worst case latency. Domain Event or a
message broker decouples that chain in time. Do not use it for fire and
forget notifications, because RPI is a request and reply protocol and does
not model a caller that does not want to wait for a response
([microservices.io, Remote Procedure Invocation
pattern](https://microservices.io/patterns/communication-style/rpi.html),
verified 2026-08-02). Do not use it to update state in two services as part
of one business transaction without a distributed transaction protocol or
without falling back to a saga, because a partial failure mid chain of RPI
calls leaves the system in an inconsistent state that RPI itself has no
mechanism to detect or repair. Do not use it across an organizational
boundary where you do not control the callee's release cadence, because a
tightly coupled generated client breaks the moment the callee changes its
schema in a way the client did not anticipate, and a looser, versioned
contract or an API Gateway in front of it usually serves better there. Do not
reach for it purely because it is familiar. That familiarity is a real force
in favour of RPI, listed in dimension 3, but it is not by itself a reason the
pattern fits a workflow that is inherently asynchronous.

## 5. Structure

**Client.** The code that wants to invoke behaviour owned by another service.
It calls a method on a locally present stub or proxy and blocks, or awaits in
an async runtime, for a result.

**Client Stub, or generated client.** A piece of code, usually generated from
an interface definition, that implements the same interface the client
expects, serializes the method arguments into a wire format, sends the request
over the network, waits for and deserializes the response, and translates any
transport level failure into an exception or error value the client's language
already understands.

**Wire protocol and serialization format.** The agreed byte level contract for
the request and the response, for example HTTP/1.1 with a JSON body, HTTP/2
framing with a Protocol Buffers encoded message for gRPC, or the Thrift binary
or compact protocol.

**Server Stub, or generated server skeleton.** The mirror image of the client
stub, living inside the service that owns the real implementation. It
deserializes the incoming request, calls the real method, serializes the
result, and sends the response back.

**Service implementation.** The actual business logic, unaware in principle
of the network boundary in front of it, though in practice it must still
implement idempotency, timeouts, and error handling because the boundary
leaks in ways described in dimension 11.

**Interface Definition Language, IDL.** The schema, whether a `.proto` file
for gRPC, a `.thrift` file for Thrift, or an OpenAPI document for REST, that
both the client stub and the server stub are generated from, or that both
sides agree to by convention. The IDL is the actual contract. The generated
code is a derived artifact of it.

**Service Registry, composed pattern, not part of RPI itself.** The
component the client stub, or an intermediary, consults to resolve a logical
service name into one or more live network addresses before the call can be
dispatched. RPI does not define this piece. It is described separately in the
Service Registry pattern and is a hard prerequisite in any system with more
than one instance per service.

## 6. ASCII structure diagram

```
+-----------------------+
| Client (calling code) |
+-----------------------+
     | in-process call
     v
+-------------------------------+
| Client Stub (generated proxy) |
+-------------------------------+
     | serialize request (protobuf, thrift, JSON)
     v
+-------------------------+
| Network I/O (transport) |
+-------------------------+
     | wire protocol, HTTP/1.1, HTTP/2, TCP, TLS
     v
+-------------------------+
| Network I/O (transport) |
+-------------------------+
     | deserialize request
     v
+----------------------------------+
| Server Stub (generated skeleton) |
+----------------------------------+
     | in-process call
     v
+---------------------------------+
| Server (service implementation) |
+---------------------------------+

The response returns serialized back through the same
chain in reverse.

+-----------------------------------------------+
| Service Registry                              |
| resolves logical name to live network address |
+-----------------------------------------------+

Consulted by Client Stub before each call. Server
registers itself on start.
```

## 7. Dynamics

```
Client         Client Stub      Service Registry    Network        Server Stub      Service
  |                 |                   |               |               |             |
  |--call(args)---->|                   |               |               |             |
  |                 |--resolve(name)--->|               |               |             |
  |                 |<--address---------|               |               |             |
  |                 |--serialize(args)--------------------------------->|             |
  |                 |----------------------------- request ------------>|             |
  |                 |                   |               |--deserialize->|             |
  |                 |                   |               |               |--invoke---->|
  |                 |                   |               |               |             |--(work)--
  |                 |                   |               |               |<--result----|
  |                 |                   |               |<--serialize---|             |
  |                 |<---------------------------- response ------------|             |
  |                 |--deserialize------|               |               |             |
  |<--return value--|                   |               |               |             |
  |                 |                   |               |               |             |

Failure branch, callee unavailable or times out:

  |--call(args)---->|                   |               |               |             |
  |                 |--send request------------------------------------>|   X (down)  |
  |                 |          (no response within deadline)            |             |
  |                 |--raise deadline-exceeded / connection error       |             |
  |<--exception-----|                   |               |               |             |
```

The dynamics above show the happy path and the single most consequential
failure branch, the callee is unreachable or too slow. Everything a
well-engineered RPI client does beyond the happy path, dimension 8, 11, and
16, exists to make that failure branch survivable for the caller rather than
silently hanging or crashing.

## 8. Implementation variants

**Plain synchronous HTTP, REST style.** The caller issues an HTTP request with
a JSON or similar body against a resource oriented URL and blocks on the
response. No code generation is required, though OpenAPI based generators
exist. This variant has the lowest tooling investment and the widest
interoperability, at the cost of weaker typing at the wire boundary. A field
rename or type change is caught only at runtime unless both sides run
contract tests.

**gRPC.** The caller and callee share a `.proto` schema, from which the
protocol compiler `protoc` generates strongly typed client and server code in
each target language. Calls run over HTTP/2, which multiplexes many logical
requests over one TCP connection and permits binary framing, header
compression, and streaming. gRPC supports four call shapes, unary, one
request and one response, the classic RPC shape, server streaming, one
request and a stream of responses, client streaming, a stream of requests and
one response, and bidirectional streaming, where both sides stream
independently. The streaming shapes stretch the pattern past pure request and
reply into something closer to a long lived channel, which is a meaningful
departure from the plain RPI definition and is worth naming explicitly when a
team picks gRPC specifically for its streaming rather than its unary calls.

**Apache Thrift.** Conceptually close to gRPC, an IDL compiled into client
and server code in many languages, but predates gRPC by roughly eight years
and offers a choice of transport, raw sockets or HTTP, and a choice of
protocol encoding, binary, compact, or JSON, that the developer selects
independently of the service definition ([Wikipedia, Apache Thrift, overview
section](https://en.wikipedia.org/wiki/Apache_Thrift), verified 2026-08-02).

**Language native RPC frameworks.** Java RMI, .NET Remoting, and CORBA are
earlier, largely superseded implementations of the same request and reply
idea, distinguished mainly by trying harder to hide the network boundary,
passing object references remotely, for instance, than the newer,
deliberately more explicit frameworks attempt to.

**Synchronous client wrapped in an async facade.** In languages with
first-class asynchronous I/O, a team often keeps the RPI call itself
synchronous in structure, one request maps to one response, resolved through
a future or a promise, while making the calling code non-blocking at the
event loop level. This does not change the pattern. It changes only how the
waiting is implemented, and it matters because a synchronous-looking RPI call
inside an async runtime still occupies a logical unit of concurrency for its
full duration, which the capacity planning in dimension 16 has to account
for.

## 9. Known production uses

gRPC, originally developed inside Google and open sourced in 2016, is used in
production by Uber, Square, Netflix, IBM, CoreOS, Docker, CockroachDB, Cisco,
Juniper Networks, Spotify, Zalando, and Dropbox, in addition to Google itself
([Wikipedia, gRPC, Notable users
section](https://en.wikipedia.org/wiki/GRPC), verified 2026-08-02). Docker
uses gRPC as the wire protocol for its containerd runtime's internal client
and plugin communication, and CockroachDB uses gRPC for inter-node
communication in its distributed SQL layer, both documented in the same
Wikipedia notable-users listing cited above, which draws on each project's own
public documentation.

Apache Thrift was originally built inside Facebook to let its many internally
authored services, written in a mix of languages, call one another with a
shared interface definition and a compact binary wire format, and Facebook
donated it to the Apache Software Foundation as an open source incubator
project in 2008 ([Wikipedia, Apache Thrift, History
section](https://en.wikipedia.org/wiki/Apache_Thrift), verified 2026-08-02).
The project remains in active use for cross language RPC at organizations
that adopted it during and after that period, and its design, a shared IDL
compiled to native stubs in each target language over a choice of transport
and encoding, is the direct architectural ancestor gRPC's own designers
studied and improved on.

Plain HTTP based RPI, REST style request and reply, is, by a wide margin, the
most common instance of this pattern in practice, forming the default
communication style of nearly every public and internal web API described
with an OpenAPI document. Richardson's own catalog names it as the first of
the three representative RPI technologies precisely because of how pervasive
it already is before a team ever adopts gRPC or Thrift
([microservices.io, Remote Procedure Invocation
pattern](https://microservices.io/patterns/communication-style/rpi.html),
verified 2026-08-02).

## 10. Consequences

**Benefits.**

- The calling code reads close to an ordinary method call, which shortens the
  ramp for engineers moving from a monolith into a service oriented system.
- Strongly typed variants, gRPC, Thrift, catch a whole class of integration
  bugs, mismatched field names and types, at compile time on the client side
  rather than at runtime in production.
- The client receives an answer, or a definitive failure, before its own
  request handling has to decide what to do next, which keeps request
  handling logic linear and easy to reason about on the happy path.
- Binary variants, gRPC over HTTP/2, Thrift binary protocol, are compact on
  the wire and support multiplexing, which reduces connection overhead
  compared with opening a fresh HTTP/1.1 connection per call.
- Tooling maturity is high across all three representative technologies.
  Generated clients, IDE integration, and contract documentation come
  largely for free once the IDL exists.

**Costs.**

- The caller's availability is now capped by the callee's availability for
  the duration of every call, and a chain of RPI calls compounds that cap
  across every hop ([microservices.io, Remote Procedure Invocation
  pattern](https://microservices.io/patterns/communication-style/rpi.html),
  verified 2026-08-02).
- The interaction model is a request and reply model. Notifications, fire
  and forget, publish and subscribe, and async response patterns are not
  naturally expressible without layering something else on top, dimension 4,
  dimension 13.
- The caller must locate a live instance of the callee before dispatching a
  call, which means a service registry, or an equivalent discovery
  mechanism, is a hard dependency rather than an optional add-on.
- The generated client and server code creates a tight coupling to the exact
  shape of the IDL. Evolving that shape without breaking existing clients
  requires deliberate schema evolution discipline, dimension 14.
- A synchronous call chain across several services multiplies worst case
  latency and turns a single slow or failed downstream service into a
  failure visible to every caller up the chain, unless timeouts, retries,
  and circuit breaking are deliberately engineered in, dimension 11.

## 11. Failure modes and misuse

**Hung caller under downstream load.** Symptom. A request handler hangs for
the full request timeout, then the whole service becomes unresponsive under
load. Cause. An RPI client with no explicit timeout, or a timeout inherited
from a default far longer than the caller's own SLA, ties up a thread or
connection slot for every in-flight call to a slow downstream service. Fix.
Set an explicit, short timeout on every outbound RPI call, tuned below the
caller's own SLA, and pair it with a circuit breaker so repeated timeouts
against the same downstream stop being attempted at all for a cool down
period, per the Circuit Breaker pattern.

**Compounding chain availability.** Symptom. A distributed call chain of five
or six services has an availability noticeably lower than any single service
in the chain, and nobody can point to a specific outage that explains it.
Cause. Chained synchronous RPI calls multiply rather than average, so a chain
of services each individually available 99.9 percent of the time compounds
toward a combined availability below any one of them individually, exactly
the force named in dimension 3. Fix. Shorten the synchronous chain by pushing
non-essential steps to an asynchronous, message based pattern such as Domain
Event, or by pre-computing and caching data the chain currently fetches
synchronously on every request.

**Duplicate side effect on retry.** Symptom. The client silently receives the
same side effect twice, for example a payment charged twice, after what
looked like a single failed request. Cause. The caller retried an RPI call
after a timeout, assuming the original request never reached the server, when
in fact the server received it, processed it, and only the response was lost
on the way back. A plain RPC call has no built in guarantee against this
because the network cannot distinguish request never arrived from response
never arrived. Fix. Make the operation idempotent, typically by having the
caller generate and attach an idempotency key that the server deduplicates
against before retries are ever allowed to run against it.

**Treating the network as reliable.** Symptom. A code review, or an incident
postmortem, reveals that a client stub call is treated exactly like calling a
local method, with no error handling path distinct from a local method's
exceptions. Cause. This is the location transparency fallacy in its purest
form. It was named among the original eight fallacies of distributed
computing attributed to L. Peter Deutsch and colleagues at Sun Microsystems in
1994, which include the network is reliable, latency is zero, and bandwidth
is infinite ([Wikipedia, Fallacies of distributed
computing](https://en.wikipedia.org/wiki/Fallacies_of_distributed_computing),
verified 2026-08-02). An RPC style client stub is precisely the abstraction
that tempts an engineer into believing all three. Fix. Treat every RPI call
site as a place where a network partition, partial failure, or degraded
latency can and will occur, and write explicit handling, timeout, retry
policy, fallback, or a clear propagated failure, rather than letting the
exception type alone decide the behaviour by accident.

**Schema drift breaking a live caller.** Symptom. A schema change to a widely
called service breaks a subset of its callers on deploy, even though the
change looked backward compatible in review. Cause. A field was removed, or a
required field was added, in the IDL, and at least one caller's generated
client was not regenerated and redeployed before the callee's new version
went live. RPI's tight, generated coupling between client and server means
this is a live risk on every schema change, not an edge case. Fix. Follow
strict schema evolution rules, only ever add optional fields, never renumber
or remove a field a live client still reads, and enforce those rules with a
contract or compatibility check in continuous integration.

## 12. Trade-off matrix

| Force | Remote Procedure Invocation | Domain Event, async messaging | API Composition |
|---|---|---|---|
| Coupling in time | Tight, caller and callee must both be up for the call to succeed | Loose, publisher and consumer need not be up at the same moment | Tight for the composing call, same as plain RPI per downstream |
| Latency, happy path | Low, single round trip per call | Higher end to end, message is queued and later consumed | Sum of the slowest fan out call, since results are joined |
| Failure isolation | A downstream failure is immediately visible to the caller | A downstream failure delays processing, does not block the publisher | A downstream failure can be partial, some results present and some missing |
| Contract coupling | Tight, generated stubs bound to an exact schema | Looser, consumers can ignore unknown fields in an event | Tight per downstream, same as RPI |
| Best fit | A single synchronous decision the caller must have before proceeding | Notifying other services something happened, with no immediate answer needed | Reading and joining data from several services for one client facing query |
| Typical technology | gRPC, Thrift, REST over HTTP | Kafka, RabbitMQ, cloud pub/sub, transactional outbox | Any RPI technology used as the transport under an aggregating layer |

API Composition, described elsewhere in this catalog, is itself usually built
out of several RPI calls fanned out from an aggregator. It is listed here as
an alternative in the sense that a team choosing how to serve a read that
spans services must decide between composing several RPI calls at query time
versus materializing a read model ahead of time through Domain Event driven
projections, see the CQRS and Domain Event entries.

## 13. Related and incompatible patterns

**Service Registry.** A hard dependency, not merely a related pattern. RPI's
client stub, or an intermediary in front of it, must resolve a logical
service name to a live network address before it can dispatch a call, and
that resolution is exactly the job Service Registry describes.

**Circuit Breaker.** Directly composes with RPI to contain the availability
cost named in dimension 3 and dimension 11. Without a circuit breaker, a
struggling downstream service degrades every caller that keeps retrying
against it, and with one, the caller fails fast and stops adding load to an
already struggling downstream.

**API Gateway.** Frequently sits in front of a set of RPI calls made on
behalf of an external client, translating one external request into one or
more internal RPI calls and aggregating the results, which is the same
composition idea described more fully under API Composition.

**Self-contained Service.** Trades against RPI at the architecture level. A
Self-contained Service deliberately avoids synchronous calls to other
services at request time specifically to sidestep the availability cost RPI
imposes, preferring local replicas or asynchronously updated data instead.

**Domain Event, transactional outbox.** The asynchronous alternative
described throughout this entry. A system rarely picks one exclusively. It
is common, and often correct, to use RPI for the synchronous, read-like
calls a request handler cannot proceed without, and Domain Event for the
notifications and cross-service state propagation that do not need an
immediate answer. Transactional Outbox specifically solves the problem of
reliably publishing a Domain Event from a service that also just completed a
local database transaction, a concern orthogonal to, but often paired
alongside, a service that also makes RPI calls.

**Saga.** Where a business transaction must span multiple services and RPI
alone cannot provide atomicity across them, Saga coordinates a sequence of
local transactions with compensating actions, frequently implemented as a
sequence of RPI calls, orchestration, or a sequence of published and
consumed events, choreography.

No pattern in this catalog is strictly incompatible with RPI at the
architecture level. The meaningful conflict is a judgement call about scope,
described in dimension 4, not a structural incompatibility.

## 14. Refactoring path in and out

**Introducing RPI into a system that currently shares a database, or calls
another module in process.** First, extract the target module behind an
explicit interface inside the same process, so every caller already goes
through a single seam, an application of the Extract Interface refactoring.
Second, stand up the extracted module as its own deployable service and
define its public surface as an IDL, whether an OpenAPI document, a `.proto`
file, or a `.thrift` file, deliberately smaller than the in-process
interface, because not every internal method should become a network
call. Third, generate or hand write a client stub that implements the
original in-process interface but delegates to the network call underneath,
so existing callers do not need to change at the call site. Fourth, cut over
callers to the new service one at a time behind that stub, using the
Strangler Application pattern for the surrounding migration, verifying each
cutover under production traffic before removing the in-process
implementation.

**Removing RPI once it stops earning its place.** The clearest signal is
dimension 11's chained-latency symptom, an availability or latency budget
that a synchronous call chain can no longer meet. Start by identifying which
of the chained calls the caller does not actually need an immediate answer
from, and replace those specific calls with a Domain Event published after
the fact, letting the downstream consumer update its own state
asynchronously instead of being queried synchronously on every request. Where
an immediate answer really is required but the data changes rarely,
introduce a cache in front of the RPI call rather than removing the call
outright, which preserves correctness while reducing the number of live
network round trips per request. Only remove the RPI call and its generated
client entirely once no caller depends on the synchronous guarantee it
provided. Removing it while a caller still needs the immediate answer is
itself the misuse pattern, converting a correctness bug into a hidden race
condition.

## 15. Testing and verification

Unit testing the caller's business logic becomes easy specifically because
RPI is expressed as an interface with a generated or hand written stub.
Mocking or stubbing that interface in a test isolates the caller's logic
from the network entirely, which is a genuine testing benefit of the
pattern's structure. What becomes harder is verifying that the mock actually
reflects the real callee's contract. A mock that silently drifts from the
real service's schema passes every unit test while the production
integration is already broken.

Contract testing closes that gap directly. A consumer driven contract tool,
such as Pact, lets the caller record the exact requests and responses it
depends on, and lets the callee's own test suite replay those recorded
interactions against its real implementation in continuous integration,
catching a schema drift before either side deploys, rather than after.

For gRPC and Thrift specifically, generating the client and server stubs
from the same IDL file inside the build, rather than checking generated code
into source control by hand, guarantees the test doubles used in unit tests
are built from the identical schema the production server runs, removing an
entire class of stale-mock failures.

Integration and end to end tests should exercise the failure branch shown in
dimension 7, not only the happy path. A test rig that can inject a
timeout, a connection refusal, or a slow response from the callee, a test
double running behind an artificial delay, or a fault injection proxy in
front of the real service, is the only reliable way to verify a timeout,
retry, and circuit breaker are actually wired correctly rather than merely
present in the code.

## 16. Observability signals

A healthy RPI client emits, at minimum, a request count, an error count
broken down by failure class, timeout, connection refused, application level
error response, and a latency histogram per downstream service and per
method, because a single averaged latency number hides the tail latency
spikes that a slow downstream service actually produces. A circuit breaker
sitting in front of the call should expose its own state, closed, open, or
half open, as a metric, since an open circuit breaker is a directly
actionable signal that a downstream dependency has degraded past the
caller's tolerance.

Distributed tracing is close to mandatory once RPI calls chain across more
than two services. Propagating a trace context, a trace id and span id,
through every outbound call header lets an operator reconstruct the full
call graph for one logical request and see exactly which hop cost the most
latency, which is otherwise invisible from any single service's own logs.

A healthy instance, on a dashboard, shows steady, low tail latency, an error
rate near the baseline the downstream service normally exhibits, and a
closed circuit breaker. A failing instance shows a rising p99 latency well
before the average latency moves, since queuing delay shows up in the tail
first, followed by a rising timeout count, followed by the circuit breaker
tripping open, which is itself the system correctly protecting the caller
from a downstream that is already unhealthy.

## 17. Security and privacy implications

Every RPI call crosses a network boundary that a purely in-process call
never did, and that boundary is where an attacker, or a misconfigured
network, gets a chance to intercept, tamper with, or spoof the traffic that
an in-process call never exposed. Transport encryption, TLS for HTTP based
RPI, and TLS underneath gRPC's HTTP/2 transport, is the baseline defence
against interception on any network the service does not fully control,
including most internal cloud networks, which should not be assumed
trusted purely because they are internal.

Authentication and authorization decisions that used to be implicit inside a
monolith's single process boundary must now be made explicit at every RPI
call site, service to service, not only at the system's external edge.
Mutual TLS, or a token propagated on every call and verified by the
receiving service rather than merely trusted because it arrived from an
internal network, are the two common mechanisms.

The IDL itself, a `.proto` file, a `.thrift` file, or an OpenAPI document,
frequently ends up describing the shape of sensitive data, personally
identifiable fields included, in a document that is often checked into a
shared repository or a schema registry with broader read access than the
data it describes should have. Treating the schema file with the same
sensitivity classification as the data it names is a discipline that is
easy to skip and consequential to skip.

Finally, generous, unbounded RPI clients, no timeout, no rate limit, no
payload size cap, are themselves a denial of service risk against the
callee, and every RPI client should be built defensively enough that a
misbehaving or compromised caller cannot exhaust a shared downstream
service's capacity through nothing more than an ordinary, syntactically
valid stream of calls.

## 18. References

- Chris Richardson, "Remote Procedure Invocation," microservices.io,
  https://microservices.io/patterns/communication-style/rpi.html, verified
  2026-08-02.
- Chris Richardson, *Microservices Patterns. With Examples in Java*,
  Manning, 2018.
- Andrew D. Birrell and Bruce Jay Nelson, "Implementing Remote Procedure
  Calls," *ACM Transactions on Computer Systems*, Volume 2, Issue 1,
  February 1984.
- Wikipedia, "gRPC," https://en.wikipedia.org/wiki/GRPC, verified
  2026-08-02.
- Wikipedia, "Apache Thrift," https://en.wikipedia.org/wiki/Apache_Thrift,
  verified 2026-08-02.
- Wikipedia, "Fallacies of distributed computing,"
  https://en.wikipedia.org/wiki/Fallacies_of_distributed_computing, verified
  2026-08-02.
- Joshua Bloch, *Effective Java*, 3rd edition, Addison-Wesley, 2018.

## Code examples

### TypeScript, plain HTTP RPI client with a timeout and a typed interface

```typescript
interface InventoryService {
  checkStock(sku: string): Promise<{ sku: string; available: number }>;
}

class RemoteInventoryClient implements InventoryService {
  constructor(private baseUrl: string, private timeoutMs: number) {}

  async checkStock(sku: string): Promise<{ sku: string; available: number }> {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeoutMs);
    try {
      const response = await fetch(`${this.baseUrl}/stock/${sku}`, {
        signal: controller.signal,
      });
      if (!response.ok) {
        throw new Error(`inventory service returned ${response.status}`);
      }
      return (await response.json()) as { sku: string; available: number };
    } catch (err) {
      if (controller.signal.aborted) {
        throw new Error(`inventory service call timed out after ${this.timeoutMs}ms`);
      }
      throw err;
    } finally {
      clearTimeout(timer);
    }
  }
}

async function main(): Promise<void> {
  const client = new RemoteInventoryClient("http://unreachable.invalid", 50);
  try {
    const result = await client.checkStock("SKU-1");
    console.log("stock", result);
  } catch (err) {
    console.log("handled failure branch", (err as Error).message);
  }
}

main();
```

### Python, a client stub with a circuit breaker composed in front of the RPI call

```python
import time
from dataclasses import dataclass
from enum import Enum, auto


class CircuitState(Enum):
    CLOSED = auto()
    OPEN = auto()
    HALF_OPEN = auto()


class CircuitOpenError(Exception):
    pass


class CircuitBreaker:
    def __init__(self, failure_threshold: int, reset_after_seconds: float):
        self.failure_threshold = failure_threshold
        self.reset_after_seconds = reset_after_seconds
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.opened_at = 0.0

    def before_call(self) -> None:
        if self.state == CircuitState.OPEN:
            if time.monotonic() - self.opened_at >= self.reset_after_seconds:
                self.state = CircuitState.HALF_OPEN
            else:
                raise CircuitOpenError("downstream circuit is open")

    def record_success(self) -> None:
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def record_failure(self) -> None:
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self.opened_at = time.monotonic()


@dataclass
class StockResult:
    sku: str
    available: int


class InventoryRpcStub:
    def __init__(self, breaker: CircuitBreaker, always_fail: bool = False):
        self.breaker = breaker
        self.always_fail = always_fail

    def check_stock(self, sku: str) -> StockResult:
        self.breaker.before_call()
        try:
            if self.always_fail:
                raise TimeoutError("downstream did not respond")
            self.breaker.record_success()
            return StockResult(sku=sku, available=42)
        except TimeoutError:
            self.breaker.record_failure()
            raise


def demo() -> None:
    breaker = CircuitBreaker(failure_threshold=2, reset_after_seconds=5.0)
    stub = InventoryRpcStub(breaker, always_fail=True)
    for attempt in range(4):
        try:
            result = stub.check_stock("SKU-1")
            print("ok", result)
        except (TimeoutError, CircuitOpenError) as err:
            print(f"attempt {attempt} {type(err).__name__} {err}")


if __name__ == "__main__":
    demo()
```

### Go, a request and reply RPC client with an explicit context deadline

```go
package main

import (
	"context"
	"errors"
	"fmt"
	"time"
)

type StockResult struct {
	SKU       string
	Available int
}

type InventoryClient struct {
	simulateSlow bool
}

func (c *InventoryClient) CheckStock(ctx context.Context, sku string) (StockResult, error) {
	resultCh := make(chan StockResult, 1)
	go func() {
		if c.simulateSlow {
			time.Sleep(200 * time.Millisecond)
		}
		resultCh <- StockResult{SKU: sku, Available: 7}
	}()

	select {
	case r := <-resultCh:
		return r, nil
	case <-ctx.Done():
		return StockResult{}, fmt.Errorf("rpc call deadline exceeded, %w", ctx.Err())
	}
}

func main() {
	client := &InventoryClient{simulateSlow: true}
	ctx, cancel := context.WithTimeout(context.Background(), 50*time.Millisecond)
	defer cancel()

	result, err := client.CheckStock(ctx, "SKU-1")
	if err != nil {
		if errors.Is(err, context.DeadlineExceeded) {
			fmt.Println("handled failure branch, deadline exceeded")
		} else {
			fmt.Println("handled failure branch", err)
		}
		return
	}
	fmt.Println("stock result", result)
}
```
