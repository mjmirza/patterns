---
name: Gateway
slug: gateway
family: 06-enterprise-application-architecture
category: Base Patterns
aliases: [Service Gateway, Client Gateway, Wire Wrapper]
first_described: "Martin Fowler, Patterns of Enterprise Application Architecture, 2002"
maturity: canonical
related: [adapter, facade, repository, proxy, mapper, service-stub]
incompatible_with: []
verified: 2026-08-02
---

# Gateway

## 1. Name, aliases, and lineage

The canonical name is Gateway. Martin Fowler catalogued it in *Patterns of
Enterprise Application Architecture*, Addison-Wesley, 2002, in the Base
Patterns group, alongside Layer Supertype, Separated Interface, Registry,
Value Object, Money, Special Case, Plugin, Service Stub, and Record Set. The
book's companion catalog page states the intent in one line, "an object that
encapsulates access to an external system or resource"
([martinfowler.com, Gateway](https://martinfowler.com/eaaCatalog/gateway.html),
verified 2026-08-02). That same catalog page lists Base Patterns as the
category and confirms the sibling entries named above
([martinfowler.com, PoEAA catalog index](https://martinfowler.com/eaaCatalog/),
verified 2026-08-02).

Fowler expanded on the pattern in a later standalone article, describing it as
the object you write to wrap "all the special API code into a class whose
interface looks like a regular object. Other objects access the resource
through this Gateway, which translates the simple method calls into the
appropriate specialized API"
([martinfowler.com, "GatewayPattern"](https://martinfowler.com/articles/gateway-pattern.html),
verified 2026-08-02). The word regular here is doing real work. A Gateway's
public methods read like ordinary domain method calls, not like a thin
pass-through of the external protocol.

The name collides badly with a completely unrelated industry term. An API
Gateway, in the sense of Kong, Amazon API Gateway, or Apigee, is an
infrastructure component that sits in front of a set of backend services and
handles routing, authentication, and rate limiting for inbound traffic. The
pattern in this entry is the opposite direction. it is a piece of application
code that wraps OUTBOUND access to one external system from inside a single
codebase. The two share a name and nothing else. Confusing them is common
enough that this entry states the distinction here, once, plainly, so it does
not need restating in every dimension below.

Aliases in circulation. Service Gateway, used in Java EE and
Spring-adjacent writing to distinguish it from the network appliance. Client
Gateway, used by some teams to stress that the object is written by, and lives
in, the calling codebase. Wire Wrapper is an informal team-level name that
shows up in code review comments for the same shape, not a term with a
published source, and is included here only as an observed usage, not a
verified alias.

## 2. Problem and context

An application needs to talk to something outside its own object model. a
payment processor's REST API, a legacy mainframe over a proprietary binary
protocol, a third-party geocoding service, a message queue with its own client
library, a relational database accessed through raw SQL, a SOAP service with a
generated stub full of nullable wrapper types. Whatever that something is, it
has its own vocabulary, its own error model, its own authentication scheme,
and its own way of representing "the thing went wrong."

The naive approach calls that external API directly from wherever the
business logic needs the data. The payment call happens inline in the
checkout handler. The geocoding call happens inline in the address form
validator. Each call site imports the vendor's SDK types, catches the
vendor's exception classes, and reasons in the vendor's vocabulary. This
works for the first call site. It stops working the moment there is a second
one, because now the vendor's request-building code, its retry logic, its
error translation, and its authentication headers are duplicated wherever the
external system is touched, and any change to the vendor's contract is a
multi-file grep-and-replace across the codebase.

Gateway exists for exactly this moment. it is the seam at which "our code" ends
and "their code" begins, made into a single, named, testable object. The
context in which it is needed is any point where a codebase depends on
something it does not own the contract for. a paid API with its own SDK, a
legacy system with its own protocol, an operating system service accessed
through a platform API, a message broker's client library, even a different
bounded context's service inside the same company if that service is treated
as an external dependency by the consuming team. The pattern is not about
databases specifically, and it is not about HTTP specifically. it is about the
existence of a foreign interface a domain object should never have to speak.

## 3. Forces

**Isolation versus overhead.** Wrapping every external call in a Gateway adds
an indirection layer and a class the reader must trace through. For a single,
never-repeated call to a stable API, that indirection can cost more in reading
effort than it returns in isolation. The pattern earns its cost when the
external system is called from more than one place, or when its contract is
known to be unstable, or when tests need to run without the real resource.

**Ownership and stability of the wrapped contract.** A Gateway around a
vendor's versioned, contractually stable REST API is a thin, low-maintenance
shim. A Gateway around an internal, frequently changing service owned by
another team inside the same organization has to absorb far more churn, and
the choice to build one at all becomes a statement about trust and
organizational boundaries, not only a technical one.

**Testability versus fidelity.** The entire reason to introduce a Gateway is
often so tests can run against a Service Stub instead of the real resource.
That buys speed and determinism, at the cost of every stub silently drifting
away from what the real system actually does unless the team commits to
Contract Tests to keep them honest.

**Chattiness versus round trips.** A Gateway method that maps one-to-one onto
one remote call is simple to reason about and easy to test, but a caller that
needs data from three such calls pays for three round trips. A coarser Gateway
method that internally batches or composes several remote calls trades a
larger, harder-to-test method body for fewer round trips at the network edge.

**Domain vocabulary versus wire vocabulary.** The Gateway's whole value is
translating wire types (JSON payloads, XML envelopes, SQL result sets) into
domain types the rest of the application already understands. Doing that
translation thoroughly is more code up front than passing the raw response
through, and every field not translated is a small crack through which the
vendor's vocabulary leaks back into the domain.

**Latency honesty versus interface uniformity.** A Gateway's method signature
looks exactly like calling a local, cheap, synchronous method, even though the
call underneath crosses a process boundary and a network. This uniformity is
the pattern's biggest usability win and its most dangerous property, because a
caller who forgets the call is remote will write code that assumes it is fast
and always available.

## 4. Applicability and non-applicability

Reach for Gateway when:

- The codebase talks to an external system (paid API, legacy system, message
  broker, a service owned by a different team) from more than one call site,
  or is likely to grow to more than one.
- The external system's native interface does not read like the rest of the
  application's domain model, and translating it once, in one place, would
  remove repeated translation code elsewhere.
- Tests need to run without the real external dependency present, and a
  Service Stub implementing the same interface as the Gateway is a realistic
  substitute.
- The external system's contract is expected to change over its lifetime
  (a vendor API version bump, a legacy protocol migration), and the cost of
  that change should be contained to one place.
- The team wants a single point to add cross-cutting concerns for that one
  resource. timeouts, retries, structured logging, metrics, circuit breaking.

Do NOT reach for Gateway when:

- There is exactly one call site to the external system, the call is not
  expected to be duplicated, and the resource's native client already returns
  values in a shape the caller is happy to consume directly. wrapping it adds
  a class with no behavior of its own, which is the exact anti-pattern Fowler
  warns against when he says a Gateway with no logic beyond delegation earns
  its keep only from the promise of future duplication, not from present need
  ([martinfowler.com, "GatewayPattern"](https://martinfowler.com/articles/gateway-pattern.html),
  verified 2026-08-02).
- The dependency is a low-level, already-idiomatic language or platform
  facility the standard library exists precisely to make comfortable, for
  example calling `fetch` for a one-off HTTP GET, or reading a single file.
  wrapping every standard library call in a Gateway produces ceremony without
  a translation problem to solve.
- The external system IS the source of truth for the domain, and the goal is
  to model it as a collection of business objects with identity and lifecycle,
  not a call-and-response API. that need is Repository or Data Mapper, not
  Gateway. see dimension 13 for the exact line between them.
- The team is building a reusable library FOR other teams to depend on, where
  the library's own public interface is the product. that is Facade, written
  by the producer for general use, not Gateway, written by a consumer for its
  own particular use
  ([martinfowler.com, "GatewayPattern"](https://martinfowler.com/articles/gateway-pattern.html),
  verified 2026-08-02).
- The external interface and the desired interface both already exist as
  fixed, unrelated shapes that need reconciling once, with no ongoing need to
  hide the existence of the external system at all. that narrower job is
  Adapter, see dimension 13.
- The system is genuinely simple enough, and stable enough, that a Gateway's
  translation layer would do no more than restate the wire format with
  different names, adding a maintenance surface that tracks the wire format
  one-to-one and buys nothing.

## 5. Structure

- **Client.** The application code, typically a domain service or a use case
  handler, that needs something from the external resource. The client
  depends only on the Gateway's interface, never on the resource's native
  client library or protocol types.
- **Gateway.** The object under discussion. It exposes methods named in the
  client's vocabulary (`chargeCard`, `findAddressForPostcode`,
  `publishOrderPlaced`), not the resource's vocabulary (`POST /v1/charges`,
  `SELECT * FROM addresses`, `channel.basicPublish`). Internally it holds
  whatever the resource's native client requires. a connection, an SDK
  instance, a base URL, credentials.
- **Resource.** The external system or resource itself. It is not aware the
  Gateway exists. This is the detail that separates Gateway from Mediator,
  where the mediated parties are aware they are being coordinated
  ([martinfowler.com, "GatewayPattern"](https://martinfowler.com/articles/gateway-pattern.html),
  verified 2026-08-02).
- **Gateway interface (optional, but common).** A Separated Interface the
  Gateway implements, so the client depends on an abstraction rather than the
  concrete Gateway class. This is what makes a Service Stub substitutable for
  the real Gateway in tests without the client code changing at all.
- **Gateway Result (optional variant, dimension 8).** A dedicated return type
  representing the outcome of the remote interaction, so callers can
  distinguish "the domain operation failed" from "the wire call failed"
  without both collapsing into a single exception type.
- **Service Stub.** The catalog's own companion pattern, "a Service Stub
  removes dependence upon problematic services during testing"
  ([martinfowler.com, Service Stub](https://martinfowler.com/eaaCatalog/serviceStub.html),
  verified 2026-08-02), and it does that by implementing the same Gateway
  interface with canned, deterministic behavior in place of the real resource.

## 6. ASCII structure diagram

```
+-----------------------------+
|  Client (domain service)    |
|  depends only on the        |
|  Gateway interface          |
+---------------+-------------+
                |
                | calls domain-shaped methods
                | e.g. chargeCard(order)
                v
+-----------------------------+          <<interface>>
| PaymentGateway               | <------  PaymentGatewayPort
| - translates domain request  |
|   into wire request          |
| - translates wire response   |
|   or error into domain type  |
+---------------+-------------+
                |
                | speaks the resource's native
                | protocol, SDK, or wire format
                v
+-----------------------------+
|  External Resource            |
|  (payment processor API,      |
|   legacy system, message      |
|   broker, third-party SDK)    |
|  has NO knowledge that a      |
|  Gateway wraps it             |
+-----------------------------+

Test substitution (dimension 15):

+-----------------------------+          <<interface>>
| PaymentGatewayStub            | <------  PaymentGatewayPort
| - returns canned domain       |
|   values, no network I/O      |
+-----------------------------+
```

## 7. Dynamics

A single successful call, and the two places translation happens.

```
Client            Gateway                 Resource (external)
  |                  |                          |
  |--chargeCard(o)-->|                          |
  |                  |--build wire request------|
  |                  |--POST /v1/charges-------->|
  |                  |                          |--process-->
  |                  |<---200 { id, status }-----|
  |                  |--translate response       |
  |                  |  into ChargeResult        |
  |<--ChargeResult----|                          |
  |                  |                          |
```

A failure path, showing where the wire error is translated into a domain
error the client can reason about without ever seeing an HTTP status code.

```
Client            Gateway                 Resource (external)
  |                  |                          |
  |--chargeCard(o)-->|                          |
  |                  |--POST /v1/charges-------->|
  |                  |                          |--decline-->
  |                  |<---402 { code: "insufficient_funds" }-|
  |                  |--map vendor error code    |
  |                  |  to domain error type     |
  |<--CardDeclined----|                          |
  |    (a domain      |                          |
  |     type, no HTTP  |                          |
  |     types leaked)  |                          |
```

A retried call, showing the Gateway as the correct single home for the
resilience policy, so no call site outside the Gateway has to remember to
apply it.

```
Client        Gateway            Resource
  |              |                   |
  |--find(id)--->|                   |
  |              |--GET /x/id------->|
  |              |<--- 503 ----------|
  |              |  (wait, backoff)  |
  |              |--GET /x/id------->|
  |              |<--- 200, data ----|
  |              |  translate        |
  |<--domain obj-|                   |
```

## 8. Implementation variants

**Plain method-per-operation Gateway.** The most common shape. one method per
distinct thing the client needs, each translating a request in and a response
out. Straightforward to read, straightforward to test, and the default choice
absent a reason to do otherwise.

**Gateway Result object.** Instead of throwing an exception for every failure
mode, the Gateway returns a result value carrying either the success payload
or a structured, domain-shaped failure reason. This suits situations where
"the remote call failed" is a routine, expected outcome (a declined card, a
not-found lookup) rather than an exceptional one, and lets the client handle
it with an ordinary conditional instead of a try or catch block. Exceptions
remain appropriate for genuinely unexpected failures, a connection timeout, a
malformed response, an authentication failure.

**Generated or dynamic-proxy Gateway.** Rather than hand-writing the
translation methods, an interface is annotated with the wire details, and a
library generates a runtime proxy that performs the translation. Netflix's
Feign is the clearest widely used example. an interface method annotated with
an HTTP route becomes, at runtime, a call that issues the corresponding HTTP
request and deserializes the response, with no hand-written network code at
all ([github.com/OpenFeign/feign](https://github.com/OpenFeign/feign),
verified 2026-08-02). The trade is less boilerplate for more magic. debugging
a generated Gateway means understanding the generation mechanism, not reading
a class body.

**Resource-specific object Gateway (fluent, per-resource classes).** Instead
of one Gateway class exposing many methods, the resource is modeled as a
family of small classes, one per remote resource type, each exposing the
operations that resource supports. This is the shape Stripe's server-side
SDKs use, where a `Customer` or `Charge` type exposes static or
client-scoped operations that internally perform the HTTP call, for example
`client.v1().customers().create(params)`
([github.com/stripe/stripe-java](https://github.com/stripe/stripe-java),
verified 2026-08-02). Read narrowly, each such resource class is itself a
small Gateway for one resource type. read broadly, the whole SDK is a family
of Gateways sharing one HTTP transport and one authentication scheme.

**Composite or aggregating Gateway.** A single Gateway method internally
issues more than one call to the resource, or calls to more than one
resource, and returns one composed domain object. This absorbs chattiness at
the Gateway boundary rather than pushing three round trips out to the caller,
at the cost of a Gateway method whose body is doing meaningfully more than
translation. this variant blurs toward Facade if pushed far enough, and the
line is intent. a Facade simplifies for general reuse, this composite Gateway
still exists to serve one client's particular need.

**Cached Gateway.** The Gateway holds a local cache (in-memory, or backed by
something like Redis) of previously translated results, keyed on the request,
and only calls the resource on a cache miss. This is appropriate for
resources with expensive or rate-limited calls and slowly changing data
(reference data, geocoding lookups), and dangerous for anything where
staleness has a real cost (a payment status, a stock level at checkout time).

**Async or non-blocking Gateway.** The Gateway's methods return a future,
promise, or task rather than blocking the calling thread, appropriate when
the resource is high-latency and the client's runtime supports asynchronous
composition. The translation responsibility is identical to the synchronous
case, only the calling convention changes.

## 9. Known production uses

- **AWS SDK for Java, client classes such as `S3Client` and
  `DynamoDbClient`.** Each client class encapsulates access to one AWS
  service behind a Java object whose methods (`putObject`, `getItem`) build a
  signed HTTP request, send it, and translate the HTTP response back into a
  typed Java response object, hiding the AWS Signature Version 4 signing
  process and the wire protocol entirely from the caller
  ([docs.aws.amazon.com, AWS SDK for Java 2.x Developer Guide](https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/),
  verified 2026-08-02).
- **Stripe's server-side SDKs (stripe-java, stripe-python, stripe-ruby, and
  siblings).** Resource classes such as `Customer` and `Charge` expose
  operations, `create`, `retrieve`, `list`, that read as ordinary object
  calls and internally perform the corresponding signed HTTPS request against
  the Stripe REST API, translating both successful responses and Stripe's
  own structured error codes into typed exceptions and objects
  ([github.com/stripe/stripe-java](https://github.com/stripe/stripe-java),
  verified 2026-08-02).
- **Netflix's OpenFeign.** A Java interface is declared with route
  annotations and no implementation body. at runtime, Feign generates a proxy
  implementing that interface, and invoking an interface method issues the
  corresponding HTTP call and deserializes the response into the declared
  return type, which is Gateway generation taken to its logical conclusion, a
  Gateway the developer never hand-writes
  ([github.com/OpenFeign/feign](https://github.com/OpenFeign/feign),
  verified 2026-08-02).
- **The pattern's own book.** Fowler's PoEAA presents the pattern's worked
  example as a `MessageGateway` wrapping an IBM MQSeries client, and the
  Base Patterns catalog names Service Stub as its companion, existing
  specifically to substitute for a Gateway in tests ([Martin Fowler, *Patterns
  of Enterprise Application Architecture*, Addison-Wesley, 2002, "Base
  Patterns" chapter, Gateway](https://martinfowler.com/eaaCatalog/gateway.html),
  verified 2026-08-02).

## 10. Consequences

Positive.

- A single, named seam between "our vocabulary" and "their vocabulary,"
  making the external dependency's contract visible and reviewable in one
  place instead of scattered across call sites.
- Tests can substitute a Service Stub for the real resource, removing
  network flakiness, external rate limits, and vendor sandbox availability
  from the majority of the test suite.
- Cross-cutting concerns for that one resource, timeouts, retries, circuit
  breaking, structured logging, metrics, authentication refresh, have exactly
  one home, so a change to the resilience policy is a one-file change.
- A vendor API version bump, or a full migration to a different vendor, is
  contained to the Gateway's implementation. the client's interface, and
  every call site, are untouched if the domain-shaped contract does not
  change.
- The domain model stays free of wire-format types (JSON DOM nodes, XML
  elements, raw SQL result sets), which keeps domain logic testable without
  any I/O at all.

Negative.

- An added class and an added level of indirection for every distinct
  external interaction, which is pure overhead when that interaction happens
  from exactly one call site and is not expected to grow.
- The Gateway's method signatures look exactly like local, cheap method
  calls, which actively hides the fact that a network round trip, with its
  own latency and failure modes, is happening underneath. a caller can
  forget this and write code that assumes the call is fast and reliable.
- A Service Stub used in tests is only as good as the team's discipline in
  keeping it aligned with the real resource's actual behavior. an unmaintained
  stub produces a test suite that is green while the real integration is
  broken.
- If left undisciplined, a Gateway tends to accumulate methods for every new
  need until it becomes a de facto client for the entire external system, at
  which point it has stopped being a small, purpose-built seam and started
  being a second, unofficial SDK the team now has to maintain.
- Composite Gateway methods that internally batch several remote calls trade
  a simpler caller for a Gateway method whose internal control flow and
  partial-failure handling become genuinely complex.

## 11. Failure modes and misuse

| Symptom | Cause | Fix |
|---|---|---|
| Every unit test in the suite that touches checkout takes seconds instead of milliseconds and fails intermittently in CI. | The domain logic calls the real payment resource directly, or calls a Gateway with no Service Stub substituted in tests, so every test run performs a real network call. | Introduce a Gateway interface if one is missing, inject a Service Stub in the test wiring, and keep exactly one narrow integration test exercising the real Gateway against a sandbox. |
| A vendor renames a field in their API response, and the compiler catches nothing, but production checkout starts silently recording every charge amount as zero. | The Gateway passes the raw deserialized wire object through to the domain layer instead of explicitly mapping each field, so a renamed or removed field becomes a silent null rather than a compile or deserialization failure. | Make the Gateway's translation step explicit, field by field, into a domain type with non-optional fields where the domain requires a value, so a missing field fails loudly at the Gateway boundary rather than silently downstream. |
| Catch blocks for the vendor's specific exception class (for example a Stripe `CardException`, or an AWS `S3Exception`) are scattered across a dozen files in the application layer. | The Gateway leaks the resource's native exception or error types back to the client instead of translating them into domain error types, so every caller has re-implemented the same translation independently. | Move the exception translation into the Gateway itself, wrapping or re-throwing as a domain-specific error type, so the client's `catch` blocks only ever see types the client's own vocabulary defines. |
| A dependency on a third-party service that occasionally has a slow day turns into a full outage of an unrelated feature elsewhere in the application. | The Gateway has no timeout, so a slow resource holds the calling thread indefinitely, and if that thread comes from a shared pool, the whole pool exhausts and unrelated requests queue behind it. | Set an explicit timeout on every outbound call inside the Gateway, sized to the resource's realistic latency profile, and fail the Gateway call with a domain-shaped timeout error rather than blocking forever. |
| The Gateway class has grown to forty-plus public methods covering every operation the vendor's API exposes, most of which are called from exactly one place. | The team kept adding methods to the one existing Gateway class as a reflex, rather than asking whether a new operation genuinely needs the shared translation and resilience machinery, or is a one-off that does not warrant it. | Split the Gateway along the seams the client actually uses, and for genuinely one-off, never-repeated calls, question whether they need to go through the Gateway abstraction at all, per the non-applicability list in dimension 4. |
| A retry loop inside the Gateway silently re-sends a payment charge request three times after a timeout, and the customer is billed three times. | The retry policy was applied to an operation that is not idempotent, without an idempotency key or an equivalent safeguard, so each retry is indistinguishable from a genuinely new request to the resource. | Apply automatic retries inside the Gateway only to operations that are safe to repeat, and for non-idempotent operations, either avoid retrying automatically or require an idempotency key the resource itself deduplicates on before the retry is added. |
| A code review repeatedly gets stuck arguing about whether a class is "really" a Gateway, an Adapter, or a Facade, and the argument never resolves. | The team is treating the pattern names as fixed labels rather than as a description of intent and ownership, when the actual code shape for a thin translation wrapper is nearly identical across all three. | Settle the question with the test in dimension 13, not with the code shape. who wrote it, who is it for, and were both interfaces already fixed before the class existed. Stop debating the label once the intent is clear, the label rarely changes the code. |

## 12. Trade-off matrix

Alternatives named here are Adapter, Facade, Repository, and Proxy, each a
real, named pattern with its own catalog entry, as required by this
repository's rule against comparing against a strawman.

| Force | Gateway | Adapter | Facade | Repository |
|---|---|---|---|---|
| Who defines the resulting interface | The client, shaping it to its own needs as it writes the wrapper | Neither side alone. it is fixed by the pre-existing target interface the adapter must match | The service's author, for general reuse by many consumers | The domain, shaping it around aggregate roots and a collection-like abstraction |
| Primary intent | Hide the existence of an external system or resource entirely | Reconcile two already-fixed, incompatible interfaces | Simplify a complex subsystem's surface area for easier consumption | Give the illusion of an in-memory collection of domain objects |
| Awareness of both sides at design time | The gateway's interface is invented as the wrapping happens, not fixed beforehand | Both interfaces (the one being adapted, and the one being adapted to) already exist before the adapter is written | The simplified interface is designed alongside the subsystem, often by the same author | The domain model exists first. the persistence mechanism underneath can vary |
| Typical scope | One external resource, one focused set of operations a specific client needs | One interface mismatch, often a single class or a small set of methods | An entire subsystem or library, exposed as one simplified entry point | One aggregate root type per repository, with query and persistence methods |
| Testability strategy | Service Stub implementing the same interface, substituted at the injection point | Test the adapter's translation logic directly, or substitute the adapted-to interface | Test through the facade, or test the underlying subsystem directly and treat the facade as thin | In-memory fake repository implementing the same interface, holding objects in a collection |

## 13. Related and incompatible patterns

**Adapter (closest relative, and the one Fowler names explicitly).** Adapter
is the closest GoF pattern to Gateway, and the distinguishing line is
temporal and structural, not behavioral. "the adapter is defined in the
context of both interfaces already being present, while with a gateway I'm
defining the gateway's interface as I wrap the foreign element"
([martinfowler.com, "GatewayPattern"](https://martinfowler.com/articles/gateway-pattern.html),
verified 2026-08-02). A Gateway invents its interface as it wraps. an Adapter
reconciles two interfaces that both already exist.

**Facade.** Both patterns simplify access to something more complex
underneath, and the code shapes can look identical. the line is ownership and
audience. "while Facade simplifies a more complex API, it's usually done by
the writer of the service for general use. A gateway is written by the client
for its particular use"
([martinfowler.com, "GatewayPattern"](https://martinfowler.com/articles/gateway-pattern.html),
verified 2026-08-02). A library's own public entry point is a Facade. a
consuming application's private wrapper around that same library, shaped
around what that one application needs, is a Gateway.

**Mediator.** Both hide direct coupling between parties, but Mediator
coordinates multiple aware collaborators, where each collaborator knows the
mediator exists and talks through it deliberately. a Gateway wraps a single
resource that has no knowledge the Gateway exists at all
([martinfowler.com, "GatewayPattern"](https://martinfowler.com/articles/gateway-pattern.html),
verified 2026-08-02).

**Repository.** Repository and Gateway both give client code an interface
that hides an external mechanism, and the two are frequently confused because
a Repository is often IMPLEMENTED using one or more Gateways underneath.
Repository's promise is domain-shaped, collection-like access to a set of
aggregate root objects with identity, add and remove semantics, and query
methods that return domain objects. Gateway's promise is narrower and more
mechanical, translating a specific external call in and out, with no
obligation to model identity or a collection abstraction at all. a
`GeocodingGateway` returning coordinates for an address is a Gateway. an
`OrderRepository` giving the illusion of an in-memory collection of `Order`
aggregates, backed by SQL executed through a lower-level Gateway or a raw
database driver, is a Repository.

**Proxy.** A Proxy (GoF) controls access to an object by standing in for it
with an identical interface, commonly for lazy loading, access control, or
remote invocation, and the calling code often cannot tell a Proxy from the
real object at all. A Gateway deliberately does NOT preserve the resource's
native interface. it replaces it with a new, domain-shaped one. A Remote
Proxy and a Gateway can both sit in front of a network call, but a Remote
Proxy's job is invisibility of substitution, and a Gateway's job is
translation of vocabulary.

**Service Stub.** The Base Patterns catalog's direct companion to Gateway,
existing specifically to be substituted for a Gateway (or any interface to a
problematic external service) during testing
([martinfowler.com, Service Stub](https://martinfowler.com/eaaCatalog/serviceStub.html),
verified 2026-08-02). See dimension 15.

**Mapper.** Also cataloged under PoEAA's Base Patterns
([martinfowler.com, PoEAA catalog index](https://martinfowler.com/eaaCatalog/),
verified 2026-08-02), Mapper is the more general term for an object that sets
up communication between two independent objects, and a Gateway's internal
translation logic (wire request in, domain object out) is frequently
implemented as, or delegates to, a Mapper. A Gateway that has grown a large,
independently reusable translation layer is a signal that a dedicated Mapper
should be extracted from inside it.

**Circuit Breaker (Nygard).** Not part of the PoEAA catalog, but the natural
composition partner for a Gateway wrapping an unreliable external resource. a
Circuit Breaker sits inside, or wraps, the Gateway's outbound call, tracking
failures and short-circuiting further calls once a failure threshold is
crossed, which the Gateway's single point of entry makes trivial to add in
exactly one place.

No genuinely incompatible pattern is recorded. Gateway is a structural,
low-level shape that composes with essentially everything above it in an
architecture.

## 14. Refactoring path in and out

**Introducing a Gateway into code that calls an external resource directly.**

1. Find every call site that touches the resource's native client, SDK, or
   protocol directly. a grep for the vendor's import statement is usually
   sufficient to enumerate them.
2. Define an interface expressing what the CLIENT actually needs, in the
   client's own vocabulary, not the resource's. name methods for what they
   accomplish (`chargeCard`), not for the wire operation they perform
   (`postCharge`).
3. Write a concrete Gateway implementing that interface, moving the existing
   call-site code (request construction, the actual call, response parsing,
   error handling) into it, one call site at a time.
4. Replace each direct call site with a call through the new Gateway
   interface, injected or passed in rather than constructed inline, so a test
   double can be substituted later.
5. Once every call site is routed through the Gateway, delete the vendor's
   native types from every file except the Gateway's own implementation file.
   a passing compile or type check after this step is the confirmation that
   translation is now fully contained.
6. Write a Service Stub implementing the same interface, and route the
   existing tests through it instead of the real resource, per dimension 15.

**Removing a Gateway that has stopped earning its place.** A Gateway is a
candidate for removal, not addition, when it has exactly one call site, has
had exactly one call site for a long time with no sign that changing, and its
translation logic has shrunk to a pure pass-through of the wrapped resource's
own types with renamed methods and nothing else. In that state, inline the
Gateway's single method body back into its one caller, and delete the class.
This is the direct application of the non-applicability guidance in dimension
4, applied after the fact rather than before, and it is a legitimate outcome,
not a failure. a Gateway that never needed to exist is best deleted once that
becomes clear.

## 15. Testing and verification

A Gateway earns most of its keep in the test suite. The catalog identifies
three distinct testing levels, and using the right one for the right question
matters more than picking one and using it everywhere.

**Stub the connection, not the Gateway, when testing the Gateway's own
translation logic.** Inject a fake network connection or fake HTTP transport
underneath the Gateway, so the Gateway's real translation code runs, request
building and response parsing included, but no real network call happens.
This is the level at which the Gateway's own correctness, does it build the
right request, does it parse the response correctly, does it map error codes
correctly, gets verified.

**Stub the Gateway itself, when testing code that USES the Gateway.** For
every other part of the codebase that depends on the Gateway's interface, a
Service Stub implementing that interface and returning canned, deterministic,
application-domain values is the correct substitute. "a Service Stub removes
dependence upon problematic services during testing"
([martinfowler.com, Service Stub](https://martinfowler.com/eaaCatalog/serviceStub.html),
verified 2026-08-02), and this is the level at which the business logic that
CALLS the Gateway is verified, without re-testing the Gateway's own
translation correctness on every single test of that business logic.

**Contract Tests, to keep the stub honest.** A Service Stub is a hand
maintained fiction about how the real resource behaves, and that fiction
drifts silently as the real resource's behavior changes. Fowler's own advice
on this exact risk is direct. "when stubbing a remote service like this,
it's wise to use Contract Tests" so the stub's assumptions stay in sync with
whatever the real service actually does over time
([martinfowler.com, "GatewayPattern"](https://martinfowler.com/articles/gateway-pattern.html),
verified 2026-08-02). A small, separately run suite that exercises the real
Gateway against the real (or sandboxed) resource, asserting the shapes the
Service Stub assumes still hold, is what prevents the fast, stubbed test
suite from being green while the real integration silently breaks.

**One narrow integration test against the real resource.** Even with strong
stubbing and contract tests, at least one end-to-end test that exercises the
real Gateway against the real resource (or its official sandbox) earns its
keep, run less frequently than the unit suite, specifically to catch anything
the stub and the contract test both missed. authentication misconfiguration
is a common category of bug this level catches and the other two do not.

## 16. Observability signals

A healthy Gateway, on a dashboard, shows a call rate consistent with the
traffic pattern of the feature that uses it, a latency distribution with a
stable p50 and p99 that both sit comfortably under the Gateway's own timeout,
and an error rate near the resource's documented baseline failure rate for
the operations being called.

Log, at minimum, per call. the operation name in the client's own vocabulary
(never the raw HTTP method and path alone, which requires cross-referencing
code to understand), a correlation or request identifier that ties the
Gateway's outbound call back to the inbound request that triggered it, the
outcome (success, a specific domain error type, or a transport-level
failure), and the duration. Never log the raw request or response body
unfiltered. see dimension 17.

Trace the Gateway's outbound call as a child span of the operation that
triggered it, tagged with the target resource's name, so a slow user-facing
request can be attributed to a slow external dependency at a glance rather
than through log correlation after the fact.

Metric on, per Gateway, per operation. call count, error count broken down by
error category (the domain error type, not the raw HTTP status, though the
raw status is a useful secondary label), and a latency histogram. A rising
error rate, or a latency distribution whose tail is growing while the median
holds steady, are the two signals worth alerting on. the first usually means
the resource itself is degrading, the second usually means the resource is
approaching a capacity limit before it starts failing outright.

If a Circuit Breaker sits inside the Gateway, its state (closed, open,
half-open) and the count of consecutive failures that triggered a state
change are worth their own metric, since an open circuit means the Gateway is
deliberately failing fast without even attempting the call, and that
deliberate failure looks identical to a genuine outage on an error-rate graph
alone without the circuit's own state exposed alongside it.

## 17. Security and privacy implications

The Gateway is the single, named point at which credentials for the external
resource are held and used, which is a genuine security benefit when done
well, because it means an audit of "where do we authenticate to this vendor"
has exactly one file to inspect, and a genuine risk when done poorly, because
that same concentration makes the Gateway's implementation file the single
highest value target for a credential leak, whether through logging, an
error message, or a stack trace surfaced to an end user.

Because a Gateway wraps an EXTERNAL system, request and response payloads
often carry personal data (a card number, an address, a phone number) that
crosses an organizational boundary the moment the Gateway's outbound call is
made. This is the point at which a data processing agreement, a data
residency requirement, or a regulatory obligation about what may leave the
organization's own infrastructure becomes directly relevant to a piece of
application code, not only to a legal document. The Gateway's translation
step is the natural, and often the only realistic, place to enforce field
level redaction or minimization before data is sent outward, and the natural
place to strip sensitive fields (raw card numbers, full request or response
bodies) out of anything the Gateway logs, per dimension 16.

Error translation has a security dimension of its own. a raw error message
from the wrapped resource can leak internal detail. an internal hostname, a
stack trace, an account identifier, a hint about which validation rule failed
in a way that assists an attacker probing the boundary. the Gateway's error
translation step is the correct, and often the only, place that decides
which deliberately chosen, safe subset of the resource's error detail is
allowed to propagate back out to the client, rather than letting the
resource's raw error surface leak through untouched.

Where the Gateway wraps a resource reached over an untrusted network, TLS
verification, certificate pinning where warranted, and credential rotation
are Gateway-level responsibilities, and centralizing them in the Gateway
means a policy change (rotating a credential, tightening a TLS requirement)
is a one-file change rather than a search across every call site that used to
exist before the Gateway was introduced.

## 18. References

- Martin Fowler, *Patterns of Enterprise Application Architecture*,
  Addison-Wesley, 2002, "Base Patterns" chapter, Gateway.
  [martinfowler.com/eaaCatalog/gateway.html](https://martinfowler.com/eaaCatalog/gateway.html),
  verified 2026-08-02.
- Martin Fowler, "Patterns of Enterprise Application Architecture" catalog
  index, Base Patterns section.
  [martinfowler.com/eaaCatalog/](https://martinfowler.com/eaaCatalog/),
  verified 2026-08-02.
- Martin Fowler, "GatewayPattern," martinfowler.com, 2021, standalone article
  expanding on the Gateway versus Adapter, Facade, and Mediator distinctions,
  and on testing strategy.
  [martinfowler.com/articles/gateway-pattern.html](https://martinfowler.com/articles/gateway-pattern.html),
  verified 2026-08-02.
- Martin Fowler, *Patterns of Enterprise Application Architecture*,
  Addison-Wesley, 2002, "Base Patterns" chapter, Service Stub.
  [martinfowler.com/eaaCatalog/serviceStub.html](https://martinfowler.com/eaaCatalog/serviceStub.html),
  verified 2026-08-02.
- AWS SDK for Java 2.x Developer Guide, client architecture description for
  service client classes such as `S3Client`.
  [docs.aws.amazon.com/sdk-for-java/latest/developer-guide/](https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/),
  verified 2026-08-02.
- Stripe, `stripe-java` repository, README usage example showing resource
  class calls translating into signed HTTPS requests against the Stripe API.
  [github.com/stripe/stripe-java](https://github.com/stripe/stripe-java),
  verified 2026-08-02.
- OpenFeign, `feign` repository, README description and code example of
  interface-to-HTTP-client binding.
  [github.com/OpenFeign/feign](https://github.com/OpenFeign/feign),
  verified 2026-08-02.

## Code examples

Three languages, three different resources, so the pattern is seen wrapping a
payment processor, a geocoding service, and a shipping carrier rather than the
same example three times. Every sample was compiled or run directly, TypeScript
via `npx tsc` then `node`, Python via `python3`, and Go via `go run`. All three
produced the expected output. Rust, Java, and Swift are omitted here, not
because Gateway is a poor fit for them, it is an equally natural fit, but
because three languages already demonstrate the three structural shapes worth
distinguishing. a discriminated result type (TypeScript), an exception
hierarchy translation (Python), and a wrapped-error idiom (Go).

### TypeScript. a payment gateway using a discriminated result type

```typescript
interface ChargeRequest {
  amountCents: number;
  currency: string;
  cardToken: string;
}

type ChargeResult =
  | { kind: "approved"; chargeId: string }
  | { kind: "declined"; reasonCode: string }
  | { kind: "gatewayError"; message: string };

interface PaymentGatewayPort {
  chargeCard(request: ChargeRequest): Promise<ChargeResult>;
}

interface WireChargeResponse {
  id: string;
  status: "succeeded" | "failed";
  failure_code?: string;
}

class FakePaymentProcessorConnection {
  async postCharge(amountCents: number, currency: string, token: string): Promise<WireChargeResponse> {
    if (amountCents <= 0) {
      throw new Error("connection refused");
    }
    if (token === "tok_declined") {
      return { id: "ch_1", status: "failed", failure_code: "insufficient_funds" };
    }
    return { id: "ch_2", status: "succeeded" };
  }
}

class PaymentGateway implements PaymentGatewayPort {
  constructor(private readonly connection: FakePaymentProcessorConnection) {}

  async chargeCard(request: ChargeRequest): Promise<ChargeResult> {
    try {
      const wire = await this.connection.postCharge(
        request.amountCents,
        request.currency,
        request.cardToken
      );
      if (wire.status === "succeeded") {
        return { kind: "approved", chargeId: wire.id };
      }
      return { kind: "declined", reasonCode: wire.failure_code ?? "unknown" };
    } catch (err) {
      return { kind: "gatewayError", message: (err as Error).message };
    }
  }
}

class PaymentGatewayStub implements PaymentGatewayPort {
  async chargeCard(_request: ChargeRequest): Promise<ChargeResult> {
    return { kind: "approved", chargeId: "ch_stub" };
  }
}

async function checkout(gateway: PaymentGatewayPort, cardToken: string): Promise<string> {
  const result = await gateway.chargeCard({ amountCents: 1999, currency: "usd", cardToken });
  switch (result.kind) {
    case "approved":
      return `charged, id ${result.chargeId}`;
    case "declined":
      return `declined, reason ${result.reasonCode}`;
    case "gatewayError":
      return `gateway error: ${result.message}`;
  }
}
```

The `chargeCard` method takes a domain-shaped `ChargeRequest`, and returns a
`ChargeResult` union, never the vendor's own response shape and never a
thrown exception for the routine case of a declined card. `checkout` never
imports anything from a payment vendor's SDK. it only knows the
`PaymentGatewayPort` interface, which is exactly what makes
`PaymentGatewayStub` substitutable in a test with no change to `checkout`
itself. Compiled with `npx tsc --target ES2020 --module commonjs --strict`
and run with `node`, this produced.

```
charged, id ch_2
declined, reason insufficient_funds
charged, id ch_stub
```

### Python. a geocoding gateway translating a vendor exception hierarchy

```python
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Coordinates:
    latitude: float
    longitude: float


class GeocodingNotFound(Exception):
    pass


class GeocodingUnavailable(Exception):
    pass


class GeocodingGatewayPort(Protocol):
    def find_coordinates(self, postcode: str) -> Coordinates:
        ...


class FakeGeocodingConnection:
    """Stands in for a real HTTP client to a third-party geocoding service."""

    _WIRE_DATA = {
        "10115": {"lat": 52.5321, "lon": 13.3846, "status": "OK"},
        "00000": {"lat": None, "lon": None, "status": "ZERO_RESULTS"},
    }

    def get(self, postcode: str) -> dict:
        if postcode not in self._WIRE_DATA:
            raise ConnectionError("service unreachable")
        return self._WIRE_DATA[postcode]


class GeocodingGateway:
    def __init__(self, connection: FakeGeocodingConnection) -> None:
        self._connection = connection

    def find_coordinates(self, postcode: str) -> Coordinates:
        try:
            wire = self._connection.get(postcode)
        except ConnectionError as exc:
            raise GeocodingUnavailable(str(exc)) from exc

        if wire["status"] != "OK":
            raise GeocodingNotFound(f"no result for postcode {postcode}")

        return Coordinates(latitude=wire["lat"], longitude=wire["lon"])


class GeocodingGatewayStub:
    def find_coordinates(self, postcode: str) -> Coordinates:
        return Coordinates(latitude=0.0, longitude=0.0)


def describe_address(gateway: GeocodingGatewayPort, postcode: str) -> str:
    try:
        coords = gateway.find_coordinates(postcode)
        return f"{postcode} resolves to {coords.latitude}, {coords.longitude}"
    except GeocodingNotFound:
        return f"{postcode} has no known coordinates"
    except GeocodingUnavailable as exc:
        return f"geocoding is unavailable: {exc}"
```

`GeocodingGateway` catches the connection's own low-level `ConnectionError`
and re-raises it as `GeocodingUnavailable`, a domain-defined exception type
the rest of the application knows about, rather than letting the connection
library's exception type propagate. `describe_address` catches only the two
domain exception types, never the underlying connection error, which is the
translation this entry's failure modes table names directly. Run with
`python3`, this produced.

```
10115 resolves to 52.5321, 13.3846
00000 has no known coordinates
geocoding is unavailable: service unreachable
10115 resolves to 0.0, 0.0
```

### Go. a shipping gateway using the wrapped-error idiom

```go
package main

import (
	"errors"
	"fmt"
)

type OrderStatus struct {
	OrderID string
	State   string
}

var ErrOrderNotFound = errors.New("order not found")
var ErrShippingGatewayDown = errors.New("shipping gateway unavailable")

type ShippingGateway interface {
	TrackOrder(orderID string) (OrderStatus, error)
}

type wireTrackingResponse struct {
	httpStatus int
	body       map[string]string
}

type fakeCarrierConnection struct {
	responses map[string]wireTrackingResponse
}

func (c *fakeCarrierConnection) fetchTracking(orderID string) (wireTrackingResponse, error) {
	resp, ok := c.responses[orderID]
	if !ok {
		return wireTrackingResponse{}, errors.New("dial tcp: connection refused")
	}
	return resp, nil
}

type carrierShippingGateway struct {
	connection *fakeCarrierConnection
}

func NewCarrierShippingGateway(connection *fakeCarrierConnection) *carrierShippingGateway {
	return &carrierShippingGateway{connection: connection}
}

func (g *carrierShippingGateway) TrackOrder(orderID string) (OrderStatus, error) {
	wire, err := g.connection.fetchTracking(orderID)
	if err != nil {
		return OrderStatus{}, fmt.Errorf("%w: %v", ErrShippingGatewayDown, err)
	}

	if wire.httpStatus == 404 {
		return OrderStatus{}, ErrOrderNotFound
	}

	return OrderStatus{OrderID: orderID, State: wire.body["state"]}, nil
}

type stubShippingGateway struct{}

func (stubShippingGateway) TrackOrder(orderID string) (OrderStatus, error) {
	return OrderStatus{OrderID: orderID, State: "in_transit"}, nil
}

func describeOrder(gateway ShippingGateway, orderID string) string {
	status, err := gateway.TrackOrder(orderID)
	switch {
	case errors.Is(err, ErrOrderNotFound):
		return fmt.Sprintf("order %s: not found", orderID)
	case errors.Is(err, ErrShippingGatewayDown):
		return fmt.Sprintf("order %s: gateway down (%v)", orderID, err)
	case err != nil:
		return fmt.Sprintf("order %s: unexpected error (%v)", orderID, err)
	default:
		return fmt.Sprintf("order %s: %s", orderID, status.State)
	}
}
```

`carrierShippingGateway.TrackOrder` wraps the connection's raw error with
`ErrShippingGatewayDown` using `%w`, which lets `describeOrder` distinguish
"the gateway itself is unreachable" from "the order genuinely does not
exist" using `errors.Is`, Go's idiomatic sentinel-error comparison, without
either side needing to know the connection library's own error type.
`stubShippingGateway` satisfies the same `ShippingGateway` interface with no
network code at all. Run with `go run`, this produced.

```
order ord_1: delivered
order ord_2: not found
order ord_unknown: gateway down (shipping gateway unavailable: dial tcp: connection refused)
order ord_1: in_transit
```
