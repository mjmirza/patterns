---
name: Data Transfer Object
slug: data-transfer-object
family: 06-enterprise-application-architecture
category: Structural
aliases: [DTO, Transfer Object, Value Object (legacy J2EE usage)]
first_described: "Sun J2EE patterns catalog, popularized by Alur, Crupi, Malks 2001; consolidated by Martin Fowler, Patterns of Enterprise Application Architecture, 2002"
maturity: canonical
related: [assembler, remote-facade, repository, domain-model, table-module, service-layer, adapter]
incompatible_with: []
verified: 2026-08-02
---

# Data Transfer Object

## 1. Name, aliases, and lineage

The canonical name is Data Transfer Object, almost always abbreviated DTO. Martin
Fowler defines it plainly in his Patterns of Enterprise Application Architecture
catalog as "an object that carries data between processes in order to reduce the
number of method calls" ([Fowler, Data Transfer Object](https://martinfowler.com/eaaCatalog/dataTransferObject.html),
verified 2026-08-02). Fowler's catalog entry credits the pattern to a design idea
that predates his own book, common in remote-procedure and distributed-object
systems of the 1990s, and formalizes the name and the accompanying Assembler
collaborator.

The pattern reached its widest early audience through the Sun/J2EE community's own
patterns catalog, published as the book Deepak Alur, John Crupi, and Dan Malks,
Core J2EE Patterns, Prentice Hall, chapter on
the presentation and business tiers, Transfer Object pattern. That catalog is the
reason the pattern is inseparable from remote Enterprise JavaBeans (EJB) calls in
older Java literature. an EJB remote interface call over RMI was expensive per
call, and batching data into one transfer object amortized that cost across a
single network round trip.

A naming collision runs through the whole history and it is the single most
common source of confusion when reading J2EE-era sources. The Java community of
that period frequently called this pattern a "Value Object", which collides with
the separate, older Value Object pattern (an immutable object compared by its
attributes rather than by identity, the concept behind currency amounts, dates,
and money classes). Wikipedia's article on the pattern states this directly. "A
value object is not a DTO. The two terms have been conflated by Sun/Java
community in the past" ([Wikipedia, Data transfer object](https://en.wikipedia.org/wiki/Data_transfer_object),
verified 2026-08-02). The two concepts are genuinely different axes. Value Object
is about identity semantics (compared by content, immutable). Data Transfer
Object is about a boundary-crossing role (a flat data carrier moved across a
process or serialization boundary). An object can be both at once, an immutable
record shipped across an HTTP boundary is a Value Object playing the DTO role,
but the terms name different concerns and neither implies the other.

Alias note. "Transfer Object" is the exact name used inside the Core J2EE
Patterns catalog itself, and some Java shops still use that shorter form in
internal naming conventions (a class named `OrderTransferObject` rather than
`OrderDto`) as a direct descendant of that catalog's vocabulary.

## 2. Problem and context

Two processes, or two tiers within the same process boundary that are treated as
independently deployable, need to exchange structured data, and the cost or the
coupling of exchanging that data naively is unacceptable.

The concrete situation shows up in three recurring shapes.

The remote-call shape, the pattern's original motivation. A client needs several
pieces of related data from a remote service, an account's balance, its recent
transactions, and its holder's name. Fetching each field with its own remote
method call means paying network latency, connection overhead, and serialization
cost once per field. Fowler's own worked example in the PoEAA catalog is exactly
this. an album's title, artist, and track list fetched as three separate remote
calls versus one call that returns an `AlbumDTO` carrying all three
([Fowler, Data Transfer Object](https://martinfowler.com/eaaCatalog/dataTransferObject.html),
verified 2026-08-02).

The boundary-shaping shape, the most common modern motivation. A web API's
public JSON contract and the shape of the underlying domain model or database
row are not the same thing, and coupling them is a liability. The domain model
carries fields the client should never see (a password hash, an internal audit
flag, a foreign-key column used only for a join), it carries lazy-loaded
associations that would trigger an N+1 query storm if serialized naively, and its
shape changes on a different schedule than the API contract the client depends
on. A DTO interposes a stable, purpose-built shape between the two, so a column
rename in the database does not break every client overnight and a client-visible
field addition does not require touching the persistence model.

The versioning and evolution shape. A public API commits to a contract that
outlives any one implementation of the service behind it. DTOs are the mechanism
by which that contract is versioned independently. a `UserV1Dto` and a
`UserV2Dto` can coexist, each mapped from the same current domain model by a
different Assembler, while the domain model itself has exactly one shape.

Across all three shapes the context that makes DTO the right answer is the same.
there is a genuine boundary, meaning a place where the cost, coupling, or
contract-stability of crossing it is materially different from an ordinary
in-process method call. Fowler is explicit that reaching for a DTO where no such
boundary exists is not a smaller version of the pattern, it is a misapplication,
covered in dimension 11.

## 3. Forces

Round trips versus payload size. Fewer, larger calls reduce round-trip
latency, which is the larger cost on a high-latency link (a public internet API,
a cross-region service call). The same choice increases the bytes moved per call
and the memory held per in-flight request. The pattern favors round-trip
reduction, and accepts the payload cost, because round-trip latency is usually
the more expensive resource on the paths where DTOs earn their keep.

Coupling to the domain model versus duplication. Serializing domain entities
directly saves the code and the discipline of maintaining a second, parallel set
of classes. It couples every external consumer to the internal shape of the
domain model, so a refactor of the domain model becomes a breaking API change.
DTOs trade the no-duplication ideal for that decoupling. This is the
central trade of the whole pattern and every other force is downstream of it.

Discoverability versus indirection. A DTO plus an Assembler is an extra hop a
reader must trace to understand what actually reaches the wire. that indirection
costs cognitive load on a small system. On a system where the domain model
churns independently of the API contract, the indirection is what keeps the two
from becoming accidentally coupled, and the cost is worth paying.

Security surface versus development speed. Serializing an entity directly is
faster to write today and is also how sensitive fields leak, a hashed password, an
internal note field, a soft-delete flag, because a field added to the entity for
an unrelated reason is now visible on every response that serializes that entity.
A DTO is an explicit allowlist. only what is put on the DTO is exposed. This
force is asymmetric, the cost of the leak is usually far larger than the cost of
the extra class, which is why security-conscious teams treat DTOs as
non-negotiable at any public boundary regardless of the size of the system.

Consistency of validation versus layering purity. Input DTOs are a natural
place to attach shape-level and format-level validation (required fields, string
lengths, numeric ranges) before that data ever reaches domain logic, which keeps
malformed input from ever constructing a domain object in an invalid state. Doing
so means validation logic exists in two places, the DTO's shape rules and the
domain model's invariant rules, and the two must be kept from silently
contradicting each other.

## 4. Applicability and non-applicability

Reach for a Data Transfer Object when a real process, network, or serialization
boundary is being crossed and at least one of these holds.

- A remote call is measurably expensive per call (RPC, cross-service HTTP,
  cross-region latency), and multiple related pieces of data are fetched
  together often enough that batching them into one call pays for the extra
  class.
- The public contract (a REST or GraphQL API, an event schema, a message queue
  payload) must be stable and independently versioned from the internal
  persistence or domain model.
- Sensitive or internal-only fields exist on the domain model or database row
  that must never reach the far side of the boundary.
- Multiple client shapes are needed from one underlying model (a summary DTO for
  a list view, a detail DTO for a single-record view), and returning the full
  domain graph every time would be wasteful or would leak fields the summary
  view has no business seeing.
- Serialization concerns (JSON shape, date formatting, enum representation) need
  to be decided independently of how the domain model represents the same data
  internally.

Do not reach for a Data Transfer Object, and this list is the one most catalogs
skip, when any of these hold.

- The call is a local, in-process method call with no serialization boundary.
  Fowler's own follow-up bliki entry states this as the core mistake to avoid.
  "DTOs are called Data Transfer Objects because their whole purpose is to shift
  data in expensive remote calls", and warns that using them locally produces "a
  more cumbersome programming model" for no benefit. He quotes Randy Stafford
  describing the mapping cost as considerable, comparable in pain to
  object-relational mapping ([Fowler, LocalDTO](https://martinfowler.com/bliki/LocalDTO.html),
  verified 2026-08-02). Passing the domain object, or an interface narrowed to
  what the caller needs, is the right call inside a single process.
- The domain model already has exactly one shape that every consumer needs, and
  there is no versioning pressure, no security boundary, and no serialization
  concern distinct from the persistence shape. Introducing a DTO here is pure
  duplication with no offsetting benefit.
- The system is small enough, and has few enough consumers, that the coupling
  DTOs exist to prevent is not actually a live risk yet, and the team would
  rather accept that risk than pay the mapping tax today. This is a real,
  defensible trade for an early-stage system, provided the team revisits it once
  a second consumer or a public contract appears.
- The object being moved has real behavior that the receiving side needs
  to invoke, not only data to read. a DTO with no behavior forces that logic to
  live somewhere else, often duplicated at every call site. If the receiver
  genuinely needs behavior, consider passing the richer object, or, if a
  boundary genuinely must be crossed, look at Remote Facade plus the domain
  object rather than flattening the behavior away.

## 5. Structure

DTO. A plain, serializable data holder. Fields, constructors, and
accessors only, or in modern language idiom an immutable record, struct, or
data class. No business rules, no persistence calls, no reference back to the
domain model that would defeat the point of decoupling.

Domain Object or Entity. The internal model the DTO is derived from, or is
converted into on the receiving side. Carries the actual business behavior and
invariants. Never serialized directly across the boundary the DTO exists to
protect.

Assembler (also called Mapper or Converter). The collaborator responsible
for converting a Domain Object into a DTO on the way out, and a DTO back into a
Domain Object, or into a command directed at the domain, on the way in. Fowler's
catalog entry treats the Assembler as part of the pattern, not an optional
extra. "an assembler is used on the server side to transfer data between the DTO
and any domain objects" ([Fowler, Data Transfer Object](https://martinfowler.com/eaaCatalog/dataTransferObject.html),
verified 2026-08-02). Keeping this conversion logic named and isolated, rather
than scattered inline at every call site, is what keeps the pattern from rotting
into ad hoc field copying.

Boundary caller and boundary callee. The two sides of the process,
network, or serialization edge. In a client-server shape these are the client
and the server. In an event-driven shape these are the producer and the
consumer of a message. The DTO's shape is a contract owned jointly by both
sides, which is why changing it is a compatibility decision, not a private
refactor.

Remote Facade (frequent collaborator, not required). A coarse-grained
service interface that groups several related operations behind one remote
call, so that DTOs move in bulk rather than the client making one remote call
per field. Fowler presents Data Transfer Object and Remote Facade as usually
appearing together, because a fine-grained remote interface defeats the purpose
of batching data into a DTO in the first place.

## 6. ASCII structure diagram

```
   BOUNDARY (network, process, or serialization edge)
   ------------------------------------------------->

   +----------------+        DTO         +----------------+
   |   Client /     |  <---------------  |  Remote Facade /|
   |   Consumer     |                    |  Service Layer  |
   |                |  ---------------->  |                |
   +----------------+     DTO (input)    +--------+--------+
                                                   |
                                                   | uses
                                                   v
                                          +------------------+
                                          |    Assembler     |
                                          | toDto() / toDomain() |
                                          +---------+--------+
                                                     |
                                          reads/writes
                                                     v
                                          +------------------+
                                          |  Domain Object /  |
                                          |  Entity           |
                                          |  (business rules,  |
                                          |   invariants)      |
                                          +------------------+

   DTO:            fields + accessors only, no behavior
   Domain Object:   behavior + invariants, never crosses the boundary
   Assembler:       the only class that knows both shapes
```

## 7. Dynamics

Outbound flow, domain data leaving the process across the boundary.

```
   Client                 Service Layer          Assembler         Domain Object
     |                          |                    |                   |
     |  1. request(id)          |                    |                   |
     |------------------------->|                    |                   |
     |                          | 2. load(id)         |                   |
     |                          |------------------------------------->  |
     |                          |                    |     (entity, with |
     |                          |                    |      internal-only|
     |                          |                    |      fields)      |
     |                          |  3. toDto(entity)   |                   |
     |                          |------------------->|                   |
     |                          |                    | 4. copy allowed   |
     |                          |                    |    fields only    |
     |                          |  5. return DTO      |                   |
     |                          |<-------------------|                   |
     |  6. serialized DTO       |                    |                   |
     |<-------------------------|                    |                   |
```

Inbound flow, external data entering the process across the boundary.

```
   Client                 Service Layer          Assembler         Domain Object
     |                          |                    |                   |
     |  1. submit(DTO)          |                    |                   |
     |------------------------->|                    |                   |
     |                          | 2. validate(DTO)    |                   |
     |                          |   (shape-level only)|                   |
     |                          | 3. toDomain(DTO)     |                   |
     |                          |------------------->|                   |
     |                          |                    | 4. construct or   |
     |                          |                    |    apply changes, |
     |                          |                    |    domain enforces|
     |                          |                    |    invariants     |
     |                          |                    |------------------>|
     |                          |  5. result DTO       |                   |
     |                          |<-----------------------------------|
     |  6. response             |                    |                   |
     |<-------------------------|                    |                   |
```

The key dynamic to notice on the inbound path is step 4. shape-level validation
(is the field present, is it the right type) happens on the DTO before
conversion, but domain-level validation (is this a legal state transition, does
this order total match its line items) happens only once the data reaches the
domain object, because only the domain object owns those invariants. Skipping
this split and trusting DTO-level validation as a proxy for domain validity is a
common failure mode, covered in dimension 11.

## 8. Implementation variants

Symmetric DTO, one class both directions. The same DTO type is used for both
the read (outbound) and write (inbound) shape of a resource. Simplest to write,
but it forces every field to be either always-writable or awkwardly ignored on
write, and it makes it easy to accidentally accept a field on input that was only
ever meant to be read (a classic mass-assignment vulnerability, see dimension
17). Reasonable only when the read and write shapes genuinely coincide and the
resource has no sensitive server-only fields.

Asymmetric request and response DTOs. Two distinct types, a
`CreateOrderRequest` and an `OrderResponse`, each carrying only the fields
legitimate for its direction. The most common modern shape for any DTO with
security or evolution concerns, because the type system itself prevents a
client from setting a field it was never meant to set.

Nested versus flat DTOs. A flat DTO denormalizes a whole object graph into
one class with prefixed or dotted field names (an old J2EE-era technique aimed
at minimizing the number of remote objects created per call). A nested DTO
mirrors the domain graph's shape with nested DTO types. Modern JSON-based APIs
overwhelmingly favor nested DTOs, because the cost that motivated flattening
(one network round trip and one serialized object per level of nesting in
RMI-style remoting) does not apply to a single JSON document; the whole nested
structure serializes in one pass regardless of depth.

Language-idiomatic variants. In Java, a `record` (since Java 16) is a
common modern DTO, replacing the older getter/setter POJO with Lombok `@Data`
annotations. In C#, a `record` type or an init-only property class serves the
same role, and in ASP.NET Core reference architectures a command DTO is
described directly as "a special kind of Data Transfer Object (DTO), one that is
specifically used to request changes or transactions"
([Microsoft, .NET Microservices architecture, application layer implementation](https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/microservice-application-layer-implementation-web-api),
verified 2026-08-02). In TypeScript, a DTO is often a plain interface for
compile-time-only shape checking, or a class when a runtime validation library
needs a real constructor and decorators to attach to. In Go, a DTO is an
exported struct with JSON struct tags controlling the wire shape independently
of the internal field names. In Rust, a DTO is commonly a struct deriving
`serde::Serialize` and `serde::Deserialize`, with `#[serde(rename = "...")]`
performing the same wire-shape decoupling Go achieves with struct tags. In
Swift, a `Codable` struct plays the identical role, with `CodingKeys` doing the
field-name decoupling.

Generated DTOs from a schema. Protocol Buffers, GraphQL SDL, OpenAPI, and
Avro all generate DTO-shaped classes from a schema-first definition rather than
having a developer hand-write the class. The generated protobuf message class is
described in its own specification as containing "simple accessors for each
field and methods to serialize and parse the whole structure to and from raw
bytes" ([Google, Protocol Buffers overview](https://protobuf.dev/overview/),
verified 2026-08-02), a description that matches a textbook DTO shape produced
mechanically rather than by hand.

Mapper-generated Assemblers. Rather than hand-writing the field-by-field
copy inside an Assembler, annotation-processor tools generate that code at
compile time. MapStruct, for Java, states its own purpose directly. "Multi-
layered applications often require to map between different object models (e.g.
entities and DTOs)" ([MapStruct](https://mapstruct.org/), verified 2026-08-02).
AutoMapper plays the equivalent role in .NET, describing itself as a tool to
"automatically map from complex models to simple, flattened destinations"
([AutoMapper](https://automapper.io/), verified 2026-08-02), a direct
description of the domain-model-to-DTO conversion step.

## 9. Known production uses

MapStruct, a Java annotation processor whose entire purpose is generating
the Assembler code between entity and DTO types at compile time, explicitly
naming that pairing on its own homepage ([mapstruct.org](https://mapstruct.org/),
verified 2026-08-02).

AutoMapper, the equivalent convention-based object-to-object mapper in the
.NET stack, used across a large share of production ASP.NET applications to
convert domain and persistence models into API-facing DTOs
([automapper.io](https://automapper.io/), verified 2026-08-02).

Protocol Buffers, Google's language-neutral serialization format, generates
message classes per the `.proto` schema that are, by the format's own
specification, plain field accessors plus serialize and parse methods and
nothing else, used across gRPC service boundaries at Google and in countless
open-source and enterprise systems as the literal wire-level DTO
([protobuf.dev/overview](https://protobuf.dev/overview/), verified 2026-08-02).

Microsoft's eShopOnContainers reference architecture, the canonical .NET
microservices sample used to teach DDD, CQRS, and event-driven patterns on
.NET, defines its CQRS commands explicitly as "a special kind of Data Transfer
Object (DTO)" moved from the API controller into the command handler, and
separately defines `OrderItemDTO` and equivalent classes as the read-side
projection shape returned from queries ([Microsoft .NET Docs, Implementing the
microservice application layer using the Web API](https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/microservice-application-layer-implementation-web-api),
verified 2026-08-02).

The original J2EE Transfer Object pattern, applied across Enterprise
JavaBeans-based systems of the early 2000s to batch entity bean state into a
single remote-callable object, as cataloged in Deepak Alur, John Crupi, and Dan
Malks, Core J2EE Patterns, Prentice Hall,
Transfer Object pattern chapter, the pattern that gave the wider industry the
name and the paired Transfer Object Assembler collaborator that later catalogs,
including Fowler's, carried forward.

## 10. Consequences

Positive.

- Decouples the wire or remote-call contract from the internal domain and
  persistence shape, so either side can change independently as long as the
  Assembler is updated to bridge them.
- Reduces round trips on any boundary where a round trip is expensive, by
  batching related data into one payload instead of one call per field.
- Acts as an explicit allowlist for what crosses a boundary, closing off the
  accidental exposure of internal-only or sensitive fields that direct
  serialization of a domain object would otherwise leak.
- Gives the contract a stable place to attach shape-level validation,
  serialization annotations, and API versioning independent of domain logic.
- Makes the public contract of a service discoverable and self-documenting.
  reading the DTO types tells a new team member exactly what a client can send
  and receive, without reading the domain model.

Negative.

- Doubles the number of classes for every concept that crosses the boundary,
  one domain shape and at least one DTO shape, and the Assembler code that
  bridges them is real, ongoing maintenance surface.
- Introduces a mapping tax on every change. adding a field to the domain model
  that a client should see requires touching the domain object, the DTO, and
  the Assembler, in that order, and forgetting the last step is a silent bug
  where the feature works internally but never reaches the client.
- Applied where no real boundary exists, it produces exactly the anti-pattern
  Fowler warns against, a more cumbersome local programming model for no
  offsetting benefit ([Fowler, LocalDTO](https://martinfowler.com/bliki/LocalDTO.html),
  verified 2026-08-02).
- Because a DTO by definition carries no behavior, business logic that would
  naturally belong on the object being transferred has to live somewhere else,
  usually a service class, and if that service class accumulates all of a
  domain's logic while every model becomes a flat data bag, the system drifts
  toward the anemic domain model anti-pattern Fowler separately identifies.
  objects "connected with rich relationships and structure" that turn out to
  have "hardly any behavior on these objects, making them little more than bags
  of getters and setters" ([Fowler, AnemicDomainModel](https://martinfowler.com/bliki/AnemicDomainModel.html),
  verified 2026-08-02).

## 11. Failure modes and misuse

Symptom. Every internal service call in a monolith passes DTOs instead of
domain objects, and a simple field addition takes three pull requests across
three classes to ship.
Cause. The team adopted DTOs as a blanket convention rather than in
response to a real boundary, most commonly by copying a pattern learned from a
remote-service codebase into a codebase with no remote calls at all.
Fix. Pass the domain object, or a narrow read-only interface derived from
it, for any call that stays inside one process. Reserve the DTO for the actual
process, network, or serialization boundary, per Fowler's explicit guidance
([Fowler, LocalDTO](https://martinfowler.com/bliki/LocalDTO.html), verified
2026-08-02).

Symptom. A client sends a JSON body updating their display name, and their
account's `isAdmin` flag silently flips to true.
Cause. Mass assignment. the inbound DTO used the same shape as the entity,
including fields the entity has but a client should never be trusted to set,
and the Assembler or the framework's model binder copied every present field
onto the domain object without an allowlist.
Fix. Give the inbound DTO only the fields a client is legitimately allowed
to write, never reuse the outbound (read) DTO shape for input, and have the
Assembler apply an explicit, named allowlist of settable fields rather than a
generic reflective copy.

Symptom. A report generation endpoint that used to be fast now times out
under load, and profiling shows most of the time inside the mapping layer, not
the database.
Cause. The Assembler converts an entire domain object graph, including
associations the DTO never actually surfaces, before selecting the handful of
fields the DTO needs, which either triggers eager loading of unused
associations or performs an expensive deep copy for data that is immediately
discarded.
Fix. Project directly from the query (a database-level projection, or a
GraphQL-style field selection) into the DTO shape where the query layer
supports it, rather than materializing the full domain graph first and mapping
second.

Symptom. Two teams, two microservices, and every deploy of one silently
breaks the other's parsing of a shared payload.
Cause. The DTO's shape changed (a field renamed, a field removed, a type
narrowed) without a versioning strategy, because the DTO was treated as an
internal implementation detail rather than as the public contract it actually
is once a second consumer exists.
Fix. Version the DTO explicitly (a new type, a schema version field, or an
API version segment), keep the old shape servable until every known consumer
has migrated, and treat any change to a shared DTO's shape with the same review
rigor as a database schema migration.

Symptom. A DTO class has grown a `calculateTotal()` method, an
`isEligibleForDiscount()` method, and half a dozen other pieces of business
logic, and nobody can say anymore whether the domain model or the DTO is the
source of truth for a given rule.
Cause. Behavior crept onto the DTO because it was the object already in
scope at the point someone needed to compute something, and adding a method to
an existing class felt cheaper than routing the calculation through the domain
model or a service.
Fix. Treat any method appearing on a DTO beyond trivial derived-field
accessors as a signal that the logic belongs on the domain model or in a
dedicated service, and move it there. a DTO with business methods is no longer
performing the role the pattern exists to fill.

## 12. Trade-off matrix

| Force | Data Transfer Object | Direct domain serialization | Remote Facade alone (no DTO) | GraphQL field-level resolution |
|---|---|---|---|---|
| Coupling of contract to internal model | Low. DTO shape is independent | High. every internal field is exposed by default | Medium. depends what the facade returns | Low, but per-field, not per-object |
| Round trips for related data | One call for a whole related set | One call, same as DTO, if the entity itself is graph-shaped | One call, DTO not required for this benefit alone | One call, client controls exact shape requested |
| Risk of leaking sensitive internal fields | Low, DTO is an explicit allowlist | High, every serializable field is exposed unless manually excluded | Depends entirely on facade discipline | Low, schema defines exposable fields explicitly |
| Mapping and maintenance cost | Real, ongoing, Assembler code to maintain | None, nothing to map | Some, facade still shapes what it returns | Resolver code plays the Assembler role instead |
| Fit for a single-process, no-boundary call | Poor, adds cost with no benefit | Good, this is the natural default in-process | N/A, facade concept does not apply in-process | N/A |
| Fit for a public, multi-consumer API | Strong, this is the pattern's home ground | Poor, couples every consumer to internal shape | Strong when paired with a DTO, weak alone | Strong, and reduces over-fetching further |

## 13. Related and incompatible patterns

Assembler. Not merely related, effectively a required collaborator. the DTO
without an Assembler is only a class, and the Assembler is what makes the
pattern function as a boundary rather than a duplicate model maintained by hand
at every call site.

Remote Facade. Frequently paired. a coarse-grained remote interface is what
lets a DTO actually reduce round trips, because a fine-grained interface
returning DTOs one field at a time defeats the purpose. Fowler presents the two
together in the same catalog entry.

Repository. A Repository typically returns domain objects, and the
Assembler sits between a Repository's output and a DTO returned to the caller
across a boundary. The two patterns compose cleanly, Repository owns fetching
the domain shape, DTO plus Assembler owns exposing a boundary-safe shape from
it.

Domain Model. DTO exists specifically to avoid exposing the Domain Model
directly across a boundary. the two patterns are complementary by design, one
protects the other.

Table Module and Transaction Script. In simpler architectural styles that
use a Table Module or a Transaction Script instead of a rich Domain Model, a
DTO is still useful for the same boundary reasons, but the Assembler's job
shrinks, because there is less of an object graph to selectively flatten in the
first place. dimension 4 non-applicability still applies unchanged. the
boundary, not the internal architecture style, is what warrants the DTO.

Service Layer. The Service Layer is the usual home for the Assembler call,
the layer that receives inbound DTOs, converts them, invokes domain logic, and
converts the result back into outbound DTOs. DTO without a Service Layer
(or an equivalent boundary-owning layer) tends to scatter Assembler calls
across controllers, which is workable at small scale but loses the pattern's
discoverability benefit.

Value Object. Related only by historical naming collision, not by design.
see dimension 1. the two patterns are orthogonal. an object can be a Value
Object (immutable, compared by content) and also serve the DTO role at a
boundary, but neither pattern implies the other, and conflating the names, as
the early J2EE community did, causes real confusion when reading older
sources.

Anti-Corruption Layer (Domain-Driven Design). Where DTOs cross a boundary
between two systems with genuinely different domain models (not only different
tiers of the same system), the Assembler's role expands into a full
Anti-Corruption Layer, translating not only field shape but domain concepts
between the two models. DTO is the data-carrying half of that larger pattern
when the two sides disagree on more than serialization shape.

## 14. Refactoring path in and out

Introducing a DTO into code that serializes domain objects directly.
Identify the actual boundary being crossed (a controller action, an RPC method,
an event publisher) and confirm dimension 4's applicability criteria genuinely
hold for it before proceeding, since introducing a DTO where no boundary exists
is the misuse this dimension exists to prevent. Define the DTO type with only
the fields the far side legitimately needs, deliberately excluding anything
sensitive or internal-only. Write the Assembler's outbound conversion first,
covered by a test asserting the DTO's fields against a known domain object.
Swap the boundary's return type from the domain object to the DTO, running the
Assembler at that single seam. Repeat with the inbound direction once outbound
is stable, this time defining the allowlist of writable fields explicitly
rather than mirroring the outbound shape. This ordering matches the general
Introduce Parameter Object and Extract Class refactoring moves in Martin
Fowler, Refactoring, 2nd edition, Addison-Wesley, 2018, chapter 6 and chapter
7, applied specifically at a process boundary rather than inside a single
class.

Removing a DTO once the boundary it protected is gone. This happens most
often when two services are merged back into one, or when an internal-only DTO
that never actually had a second consumer is discovered during a dependency
audit. Confirm no external consumer still depends on the DTO's shape by
checking API version usage or event schema consumers. Inline the Assembler's
conversion at each of its call sites, one at a time, verifying with a test at
each step that the resulting behavior is identical to going through the DTO.
Delete the DTO type and the Assembler once every call site passes the domain
object or interface directly. Treat this as the mirror image of the
introduction path, and apply the same caution about verifying the boundary is
genuinely gone before removing the protection the DTO provided.

## 15. Testing and verification

DTOs themselves are close to free to test, because they hold no behavior beyond
trivial derived accessors, and a test suite that spends real effort unit
testing a DTO's getters is testing the language's own field access, not the
system. The real testing surface is the Assembler and the boundary.

Test the Assembler's outbound conversion by constructing a known domain object,
including edge cases (a null optional association, an empty collection, a
boundary date value), and asserting the resulting DTO's fields match
field-for-field, with particular attention to fields that must be absent, a
test that fails if a sensitive field ever appears on the DTO is the highest-
value test in this pattern's whole surface area.

Test the Assembler's inbound conversion the same way in reverse, and add an
explicit test asserting that a field present on the inbound DTO but not on the
writable allowlist has no effect on the resulting domain object, which is the
regression test for the mass-assignment failure mode in dimension 11.

Test the boundary itself, not only the Assembler in isolation, with a contract
test (serialize a DTO to JSON or protobuf bytes, deserialize it back, assert
equality) whenever the DTO crosses a real serialization boundary, since
serialization format quirks (a date losing its timezone, a large integer
losing precision in JSON) are a class of bug that unit-testing the Assembler
alone will never catch.

Where two independently deployed services share a DTO's schema, a consumer-
driven contract test (the consuming service asserts the shape it depends on
against the producing service's actual output, run in CI on both sides)
catches the compatibility failure mode from dimension 11 before it reaches
production, rather than after a deploy has already broken the other team.

## 16. Observability signals

Log or trace the boundary crossing itself, not the internal domain call,
because the DTO is the artifact that actually travels the network. a trace
span around serialization plus network transmission plus deserialization
surfaces payload-size regressions (a DTO that quietly grew because a field was
added without considering whether every consumer needs it) before they show up
as latency complaints.

Track payload size distribution per DTO type over time. a DTO whose median
serialized size grows steadily is usually a symptom of the flat-DTO-as-junk-
drawer failure mode, fields accumulating on a shared DTO because it was
convenient rather than because every consumer needs them.

Track Assembler execution time separately from the rest of the request path
when a service handles high request volume, because the failure mode in
dimension 11 where an Assembler eagerly materializes an unused association
graph shows up as time spent inside the mapping layer, not inside the database
query, and that distinction is invisible unless the mapping step has its own
timing signal.

For versioned DTOs, track request volume broken down by which DTO version was
served, so a decision to retire an old DTO version can be made from real usage
data rather than from an assumption that nobody uses it anymore.

## 17. Security and privacy implications

The DTO's allowlist property is itself a security control, and the most
important discipline covered in this entry is keeping that allowlist explicit
rather than accidental. A DTO built by reflectively copying every field off a
domain object, or by reusing an outbound (read) DTO's shape as the inbound
(write) DTO, reopens exactly the field-leakage and mass-assignment risks the
pattern exists to close. The symptom in dimension 11, an unauthorized field
silently accepted on write, is a real, historically common vulnerability class
in web frameworks that bind request bodies directly onto domain or persistence
model types rather than onto a purpose-built inbound DTO.

Because a DTO is the shape that actually crosses a trust boundary, it is the
natural place to apply and enforce input validation before that data reaches
any domain logic, format checks, length limits, and type coercion on the DTO
layer reduce the attack surface presented to the domain model. This validation
is necessary but not sufficient. shape-level validation on a DTO (a string is
present and under 200 characters) says nothing about domain-level validity (a
username is not already taken), and treating DTO validation as a substitute for
domain invariant enforcement is a distinct failure mode from the one already
covered in dimension 11's inbound-flow discussion.

Logging a DTO wholesale for debugging is a common, quiet way sensitive data
ends up in application logs, since a DTO built for one purpose (an internal
audit event, say) can be reused for logging without anyone reconsidering
whether every field it carries is safe to write to a log aggregator that a
wider set of engineers can read. Treat DTO logging with the same field-level
care as DTO serialization to a client.

Where a DTO crosses an organizational trust boundary, not only a technical
process boundary, for example a payload shared with a third-party integration
partner, the DTO's shape is also the contractual definition of what data
leaves the organization, and changes to it should go through the same data-
governance review as any other outbound data-sharing decision, independent of
whether the change is technically backward compatible.

## 18. References

- Martin Fowler, Data Transfer Object, Patterns of Enterprise Application
  Architecture catalog. https://martinfowler.com/eaaCatalog/dataTransferObject.html
  verified 2026-08-02.
- Martin Fowler, LocalDTO, bliki. https://martinfowler.com/bliki/LocalDTO.html
  verified 2026-08-02.
- Martin Fowler, AnemicDomainModel, bliki.
  https://martinfowler.com/bliki/AnemicDomainModel.html verified 2026-08-02.
- Martin Fowler, Refactoring. Improving the Design of Existing Code, 2nd
  edition, Addison-Wesley, 2018, chapter 6 (A First Set of Refactorings) and
  chapter 7 (Encapsulation).
- Wikipedia, Data transfer object.
  https://en.wikipedia.org/wiki/Data_transfer_object verified 2026-08-02.
- Deepak Alur, John Crupi, Dan Malks, Core J2EE Patterns, Prentice Hall,
  Transfer Object pattern chapter.
- MapStruct, Java bean mapping library homepage.
  https://mapstruct.org/ verified 2026-08-02.
- AutoMapper, .NET object-to-object mapper homepage.
  https://automapper.io/ verified 2026-08-02.
- Google, Protocol Buffers overview.
  https://protobuf.dev/overview/ verified 2026-08-02.
- Microsoft .NET Docs, Implementing the microservice application layer using
  the Web API, .NET Microservices architecture reference (eShopOnContainers).
  https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/microservice-application-layer-implementation-web-api
  verified 2026-08-02.

## Code

### TypeScript

```typescript
interface CreateOrderRequestDto {
  customerId: string;
  items: { sku: string; quantity: number }[];
}

interface OrderResponseDto {
  orderId: string;
  customerId: string;
  totalCents: number;
  itemCount: number;
}

class Order {
  private readonly lines: { sku: string; quantity: number; unitPriceCents: number }[] = [];

  constructor(private readonly id: string, private readonly customerId: string) {}

  addLine(sku: string, quantity: number, unitPriceCents: number): void {
    if (quantity <= 0) throw new Error("quantity must be positive");
    this.lines.push({ sku, quantity, unitPriceCents });
  }

  totalCents(): number {
    return this.lines.reduce((sum, l) => sum + l.unitPriceCents * l.quantity, 0);
  }

  itemCount(): number {
    return this.lines.reduce((sum, l) => sum + l.quantity, 0);
  }

  get orderId(): string {
    return this.id;
  }

  get customer(): string {
    return this.customerId;
  }
}

const priceCatalog: Record<string, number> = { "SKU-1": 500, "SKU-2": 1200 };

function assembleFromRequest(dto: CreateOrderRequestDto): Order {
  const order = new Order("ord-1", dto.customerId);
  for (const item of dto.items) {
    const price = priceCatalog[item.sku];
    if (price === undefined) throw new Error(`unknown sku ${item.sku}`);
    order.addLine(item.sku, item.quantity, price);
  }
  return order;
}

function assembleResponse(order: Order): OrderResponseDto {
  return {
    orderId: order.orderId,
    customerId: order.customer,
    totalCents: order.totalCents(),
    itemCount: order.itemCount(),
  };
}

const request: CreateOrderRequestDto = {
  customerId: "cust-42",
  items: [
    { sku: "SKU-1", quantity: 2 },
    { sku: "SKU-2", quantity: 1 },
  ],
};

const order = assembleFromRequest(request);
const response = assembleResponse(order);

console.log(JSON.stringify(response));
if (response.totalCents !== 2200) throw new Error("assembler produced wrong total");
if (response.itemCount !== 3) throw new Error("assembler produced wrong item count");
console.log("ok");
```

### Python

```python
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class CreateOrderRequestDto:
    customer_id: str
    items: List[dict]


@dataclass(frozen=True)
class OrderResponseDto:
    order_id: str
    customer_id: str
    total_cents: int
    item_count: int


class OrderLine:
    def __init__(self, sku: str, quantity: int, unit_price_cents: int):
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        self.sku = sku
        self.quantity = quantity
        self.unit_price_cents = unit_price_cents


class Order:
    def __init__(self, order_id: str, customer_id: str):
        self.order_id = order_id
        self.customer_id = customer_id
        self.lines: List[OrderLine] = []

    def add_line(self, sku: str, quantity: int, unit_price_cents: int) -> None:
        self.lines.append(OrderLine(sku, quantity, unit_price_cents))

    def total_cents(self) -> int:
        return sum(l.unit_price_cents * l.quantity for l in self.lines)

    def item_count(self) -> int:
        return sum(l.quantity for l in self.lines)


PRICE_CATALOG = {"SKU-1": 500, "SKU-2": 1200}


def assemble_from_request(dto: CreateOrderRequestDto) -> Order:
    order = Order(order_id="ord-1", customer_id=dto.customer_id)
    for item in dto.items:
        price = PRICE_CATALOG.get(item["sku"])
        if price is None:
            raise ValueError(f"unknown sku {item['sku']}")
        order.add_line(item["sku"], item["quantity"], price)
    return order


def assemble_response(order: Order) -> OrderResponseDto:
    return OrderResponseDto(
        order_id=order.order_id,
        customer_id=order.customer_id,
        total_cents=order.total_cents(),
        item_count=order.item_count(),
    )


if __name__ == "__main__":
    request = CreateOrderRequestDto(
        customer_id="cust-42",
        items=[{"sku": "SKU-1", "quantity": 2}, {"sku": "SKU-2", "quantity": 1}],
    )
    order = assemble_from_request(request)
    response = assemble_response(order)
    print(response)
    assert response.total_cents == 2200, "assembler produced wrong total"
    assert response.item_count == 3, "assembler produced wrong item count"
    print("ok")
```

### Java

```java
import java.util.List;
import java.util.Map;
import java.util.ArrayList;

record CreateOrderItemDto(String sku, int quantity) {}

record CreateOrderRequestDto(String customerId, List<CreateOrderItemDto> items) {}

record OrderResponseDto(String orderId, String customerId, int totalCents, int itemCount) {}

class OrderLine {
    final String sku;
    final int quantity;
    final int unitPriceCents;

    OrderLine(String sku, int quantity, int unitPriceCents) {
        if (quantity <= 0) throw new IllegalArgumentException("quantity must be positive");
        this.sku = sku;
        this.quantity = quantity;
        this.unitPriceCents = unitPriceCents;
    }
}

class Order {
    private final String orderId;
    private final String customerId;
    private final List<OrderLine> lines = new ArrayList<>();

    Order(String orderId, String customerId) {
        this.orderId = orderId;
        this.customerId = customerId;
    }

    void addLine(String sku, int quantity, int unitPriceCents) {
        lines.add(new OrderLine(sku, quantity, unitPriceCents));
    }

    int totalCents() {
        return lines.stream().mapToInt(l -> l.unitPriceCents * l.quantity).sum();
    }

    int itemCount() {
        return lines.stream().mapToInt(l -> l.quantity).sum();
    }

    String getOrderId() {
        return orderId;
    }

    String getCustomerId() {
        return customerId;
    }
}

class OrderAssembler {
    private static final Map<String, Integer> PRICE_CATALOG = Map.of("SKU-1", 500, "SKU-2", 1200);

    static Order fromRequest(CreateOrderRequestDto dto) {
        Order order = new Order("ord-1", dto.customerId());
        for (CreateOrderItemDto item : dto.items()) {
            Integer price = PRICE_CATALOG.get(item.sku());
            if (price == null) throw new IllegalArgumentException("unknown sku " + item.sku());
            order.addLine(item.sku(), item.quantity(), price);
        }
        return order;
    }

    static OrderResponseDto toResponse(Order order) {
        return new OrderResponseDto(order.getOrderId(), order.getCustomerId(), order.totalCents(), order.itemCount());
    }
}

public class DataTransferObjectDemo {
    public static void main(String[] args) {
        CreateOrderRequestDto request = new CreateOrderRequestDto(
            "cust-42",
            List.of(new CreateOrderItemDto("SKU-1", 2), new CreateOrderItemDto("SKU-2", 1))
        );
        Order order = OrderAssembler.fromRequest(request);
        OrderResponseDto response = OrderAssembler.toResponse(order);
        System.out.println(response);
        if (response.totalCents() != 2200) throw new AssertionError("wrong total");
        if (response.itemCount() != 3) throw new AssertionError("wrong item count");
        System.out.println("ok");
    }
}
```

### Go

```go
package main

import (
	"encoding/json"
	"errors"
	"fmt"
)

type CreateOrderItemDto struct {
	Sku      string `json:"sku"`
	Quantity int    `json:"quantity"`
}

type CreateOrderRequestDto struct {
	CustomerID string               `json:"customerId"`
	Items      []CreateOrderItemDto `json:"items"`
}

type OrderResponseDto struct {
	OrderID    string `json:"orderId"`
	CustomerID string `json:"customerId"`
	TotalCents int    `json:"totalCents"`
	ItemCount  int    `json:"itemCount"`
}

type orderLine struct {
	sku            string
	quantity       int
	unitPriceCents int
}

type order struct {
	id         string
	customerID string
	lines      []orderLine
}

func newOrder(id, customerID string) *order {
	return &order{id: id, customerID: customerID}
}

func (o *order) addLine(sku string, quantity, unitPriceCents int) error {
	if quantity <= 0 {
		return errors.New("quantity must be positive")
	}
	o.lines = append(o.lines, orderLine{sku, quantity, unitPriceCents})
	return nil
}

func (o *order) totalCents() int {
	total := 0
	for _, l := range o.lines {
		total += l.unitPriceCents * l.quantity
	}
	return total
}

func (o *order) itemCount() int {
	count := 0
	for _, l := range o.lines {
		count += l.quantity
	}
	return count
}

var priceCatalog = map[string]int{"SKU-1": 500, "SKU-2": 1200}

func assembleFromRequest(dto CreateOrderRequestDto) (*order, error) {
	o := newOrder("ord-1", dto.CustomerID)
	for _, item := range dto.Items {
		price, ok := priceCatalog[item.Sku]
		if !ok {
			return nil, fmt.Errorf("unknown sku %s", item.Sku)
		}
		if err := o.addLine(item.Sku, item.Quantity, price); err != nil {
			return nil, err
		}
	}
	return o, nil
}

func assembleResponse(o *order) OrderResponseDto {
	return OrderResponseDto{
		OrderID:    o.id,
		CustomerID: o.customerID,
		TotalCents: o.totalCents(),
		ItemCount:  o.itemCount(),
	}
}

func main() {
	request := CreateOrderRequestDto{
		CustomerID: "cust-42",
		Items: []CreateOrderItemDto{
			{Sku: "SKU-1", Quantity: 2},
			{Sku: "SKU-2", Quantity: 1},
		},
	}
	o, err := assembleFromRequest(request)
	if err != nil {
		panic(err)
	}
	response := assembleResponse(o)
	out, _ := json.Marshal(response)
	fmt.Println(string(out))
	if response.TotalCents != 2200 {
		panic("wrong total")
	}
	if response.ItemCount != 3 {
		panic("wrong item count")
	}
	fmt.Println("ok")
}
```

### Rust

```rust
use std::collections::HashMap;
use std::fmt;

#[derive(Debug)]
struct CreateOrderItemDto {
    sku: String,
    quantity: i32,
}

#[derive(Debug)]
struct CreateOrderRequestDto {
    customer_id: String,
    items: Vec<CreateOrderItemDto>,
}

#[derive(Debug)]
struct OrderResponseDto {
    order_id: String,
    customer_id: String,
    total_cents: i32,
    item_count: i32,
}

impl fmt::Display for OrderResponseDto {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(
            f,
            "{{orderId: {}, customerId: {}, totalCents: {}, itemCount: {}}}",
            self.order_id, self.customer_id, self.total_cents, self.item_count
        )
    }
}

struct OrderLine {
    #[allow(dead_code)]
    sku: String,
    quantity: i32,
    unit_price_cents: i32,
}

struct Order {
    id: String,
    customer_id: String,
    lines: Vec<OrderLine>,
}

impl Order {
    fn new(id: &str, customer_id: &str) -> Self {
        Order { id: id.to_string(), customer_id: customer_id.to_string(), lines: Vec::new() }
    }

    fn add_line(&mut self, sku: &str, quantity: i32, unit_price_cents: i32) -> Result<(), String> {
        if quantity <= 0 {
            return Err("quantity must be positive".to_string());
        }
        self.lines.push(OrderLine { sku: sku.to_string(), quantity, unit_price_cents });
        Ok(())
    }

    fn total_cents(&self) -> i32 {
        self.lines.iter().map(|l| l.unit_price_cents * l.quantity).sum()
    }

    fn item_count(&self) -> i32 {
        self.lines.iter().map(|l| l.quantity).sum()
    }
}

fn assemble_from_request(dto: &CreateOrderRequestDto, catalog: &HashMap<&str, i32>) -> Result<Order, String> {
    let mut order = Order::new("ord-1", &dto.customer_id);
    for item in &dto.items {
        let price = catalog.get(item.sku.as_str()).ok_or_else(|| format!("unknown sku {}", item.sku))?;
        order.add_line(&item.sku, item.quantity, *price)?;
    }
    Ok(order)
}

fn assemble_response(order: &Order) -> OrderResponseDto {
    OrderResponseDto {
        order_id: order.id.clone(),
        customer_id: order.customer_id.clone(),
        total_cents: order.total_cents(),
        item_count: order.item_count(),
    }
}

fn main() {
    let mut catalog: HashMap<&str, i32> = HashMap::new();
    catalog.insert("SKU-1", 500);
    catalog.insert("SKU-2", 1200);

    let request = CreateOrderRequestDto {
        customer_id: "cust-42".to_string(),
        items: vec![
            CreateOrderItemDto { sku: "SKU-1".to_string(), quantity: 2 },
            CreateOrderItemDto { sku: "SKU-2".to_string(), quantity: 1 },
        ],
    };

    let order = assemble_from_request(&request, &catalog).expect("assembly failed");
    let response = assemble_response(&order);
    println!("{}", response);
    assert_eq!(response.total_cents, 2200, "wrong total");
    assert_eq!(response.item_count, 3, "wrong item count");
    println!("ok");
}
```

### Swift

```swift
import Foundation

struct CreateOrderItemDto: Codable {
    let sku: String
    let quantity: Int
}

struct CreateOrderRequestDto: Codable {
    let customerId: String
    let items: [CreateOrderItemDto]
}

struct OrderResponseDto: Codable, CustomStringConvertible {
    let orderId: String
    let customerId: String
    let totalCents: Int
    let itemCount: Int

    var description: String {
        "{orderId: \(orderId), customerId: \(customerId), totalCents: \(totalCents), itemCount: \(itemCount)}"
    }
}

struct OrderLine {
    let sku: String
    let quantity: Int
    let unitPriceCents: Int
}

final class Order {
    let orderId: String
    let customerId: String
    private(set) var lines: [OrderLine] = []

    init(orderId: String, customerId: String) {
        self.orderId = orderId
        self.customerId = customerId
    }

    func addLine(sku: String, quantity: Int, unitPriceCents: Int) throws {
        guard quantity > 0 else {
            throw NSError(domain: "Order", code: 1, userInfo: [NSLocalizedDescriptionKey: "quantity must be positive"])
        }
        lines.append(OrderLine(sku: sku, quantity: quantity, unitPriceCents: unitPriceCents))
    }

    func totalCents() -> Int {
        lines.reduce(0) { $0 + $1.unitPriceCents * $1.quantity }
    }

    func itemCount() -> Int {
        lines.reduce(0) { $0 + $1.quantity }
    }
}

enum OrderAssembler {
    static let priceCatalog: [String: Int] = ["SKU-1": 500, "SKU-2": 1200]

    static func fromRequest(_ dto: CreateOrderRequestDto) throws -> Order {
        let order = Order(orderId: "ord-1", customerId: dto.customerId)
        for item in dto.items {
            guard let price = priceCatalog[item.sku] else {
                throw NSError(domain: "Order", code: 2, userInfo: [NSLocalizedDescriptionKey: "unknown sku \(item.sku)"])
            }
            try order.addLine(sku: item.sku, quantity: item.quantity, unitPriceCents: price)
        }
        return order
    }

    static func toResponse(_ order: Order) -> OrderResponseDto {
        OrderResponseDto(
            orderId: order.orderId,
            customerId: order.customerId,
            totalCents: order.totalCents(),
            itemCount: order.itemCount()
        )
    }
}

let request = CreateOrderRequestDto(
    customerId: "cust-42",
    items: [
        CreateOrderItemDto(sku: "SKU-1", quantity: 2),
        CreateOrderItemDto(sku: "SKU-2", quantity: 1),
    ]
)

do {
    let order = try OrderAssembler.fromRequest(request)
    let response = OrderAssembler.toResponse(order)
    print(response)
    precondition(response.totalCents == 2200, "wrong total")
    precondition(response.itemCount == 3, "wrong item count")
    print("ok")
} catch {
    fatalError("assembly failed: \(error)")
}
```
