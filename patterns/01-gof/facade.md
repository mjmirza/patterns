---
name: Facade
slug: facade
family: 01-gof
category: Structural
aliases: [Subsystem Facade, Coarse-Grained Interface, Convenience API, Shortcut]
first_described: "Gamma, Helm, Johnson, Vlissides 1994"
maturity: canonical
related: [adapter, mediator, abstract-factory, proxy, service-layer, remote-facade, anti-corruption-layer]
incompatible_with: []
verified: 2026-08-02
---

# Facade

## 1. Name, aliases, and lineage

The canonical name is Facade. It is one of the seven structural patterns in the
Gang of Four catalog, described in Erich Gamma, Richard Helm, Ralph Johnson and
John Vlissides, *Design Patterns. Elements of Reusable Object-Oriented
Software*, Addison-Wesley, 1994, chapter 4, Structural Patterns, section Facade.
The chapter grouping is confirmed by the standard listing of the book's
structural patterns as Adapter, Bridge, Composite, Decorator, Facade, Flyweight
and Proxy ([Wikipedia article on Design Patterns](https://en.wikipedia.org/wiki/Design_Patterns),
verified 2026-08-02). The intent recorded there is to provide a unified
higher-level interface to a set of interfaces in a subsystem, so that the
subsystem becomes easier to use. I have paraphrased the intent rather than
quoted it, because I could not verify a verbatim transcription of the book's
intent line against an authoritative online source on 2026-08-02, and an
approximate quotation attributed as exact would be worse than a paraphrase.

The name is an architectural metaphor. A building facade is the face presented
to the street. It is not the building. It does not hold the building up, it does
not contain the plumbing, and nobody confuses the two. That reading of the
metaphor is the discipline the pattern needs, and losing it is the origin of the
failure mode described in dimension 11.

Several aliases circulate, none of them promoted by the book.

- **Subsystem Facade.** Used in layered-architecture writing to distinguish a
  facade over a whole subsystem from a facade over a single awkward class.
- **Coarse-Grained Interface.** Used in distributed-systems writing, where the
  motivation is round-trip reduction rather than readability. Martin Fowler's
  Remote Facade names exactly this specialisation, defined as providing a
  coarse-grained facade on fine-grained objects to improve efficiency over a
  network ([martinfowler.com Remote Facade catalog entry](https://martinfowler.com/eaaCatalog/remoteFacade.html),
  verified 2026-08-02).
- **Convenience API** and **Shortcut.** The names library authors actually use.
  Django ships a module literally called `django.shortcuts` whose `render`
  function combines a template with a context dictionary and returns an
  `HttpResponse` object with the rendered text ([Django 5.2 documentation, Built-in
  shortcut functions](https://docs.djangoproject.com/en/5.2/topics/http/shortcuts/),
  verified 2026-08-02). That is a facade under a different word.
- **Logging facade** is a term of art in the Java community, fixed by the name
  of the SLF4J project, which describes itself as a simple facade or abstraction
  for various logging frameworks such as `java.util.logging`, log4j 1.x, reload4j
  and logback ([SLF4J user manual](https://www.slf4j.org/manual.html), verified
  2026-08-02). Note that SLF4J is a facade in the loose, everyday sense and an
  Adapter in the strict GoF sense, a distinction dimension 13 takes apart.

Three terms are commonly used as synonyms for Facade and are not synonyms.
Wrapper is a superset covering Adapter, Decorator and Proxy as well. Gateway, in
Fowler's usage, is an object that encapsulates access to an external system or
resource, which is a narrower job with a specific target. Anti-Corruption Layer,
from Domain-Driven Design, is a facade plus a translation of one domain model
into another, and the translation is the part that matters. Calling all four
Facade erases the difference between simplifying, converting and defending.

## 2. Problem and context

A caller needs a small, ordinary result from a subsystem that is large, correct
and unpleasant to talk to.

The situation reads like this in a real codebase. A team wants to send one
transactional email. The mail subsystem is well built. It has a transport, a
connection factory, a credential resolver, a MIME part builder, a content-type
negotiator, a header canonicaliser, a retry policy, a bounce classifier and a
delivery receipt store. Every one of those types exists for a reason and none of
them is redundant. Sending one email involves creating six of them in a
particular order, wiring three of them together, calling a method on the fourth,
catching two checked exceptions and closing one resource in a `finally` block.
The correct sequence is twenty-five lines long, and it is copied into eleven call
sites, each copy diverging slightly from the others over three years.

The observable symptoms are the diagnostic, not the abstract description.

- The same import block, six or eight lines of it, appears at the top of files
  that have nothing else in common.
- A new engineer's first task involving that subsystem takes a day, and the
  finished diff is a copy of an existing call site with two identifiers changed.
- A bug fix in the sequence, for example remembering to set the encoding before
  attaching the body, has to be applied in eleven places, and the eleventh is
  found six months later by a customer.
- A pull request that upgrades the subsystem's minor version touches two hundred
  files across the repository, none of which are the subsystem itself.
- Static analysis reports a cyclic dependency between two modules that ought not
  to know about each other, and the cycle runs through a shared subsystem type
  that both modules imported to build a request object.

The context that makes Facade the right answer has four parts, and each part
should be checked before adopting it.

- **The subsystem is genuinely complicated, and the complication is warranted.**
  If the subsystem is complicated by accident, fixing the subsystem is the better
  move and a facade only hides the mess from view while preserving it.
- **A recognisable majority of callers want the same small subset of the
  subsystem's capability.** Facade is a bet that the eighty-percent case exists
  and is stable. Where every caller wants something different, the facade grows
  one method per caller and stops being a simplification.
- **The subsystem's full surface must remain reachable.** Facade does not remove
  access, it adds a shorter path. The advanced caller keeps the option of
  dropping to the subsystem directly. A layer that forbids the direct path is
  not a facade, it is an encapsulation boundary with different rules and
  different costs.
- **The dependency direction matters to somebody.** The strongest argument for
  Facade in a large codebase is not readability, it is that the compile-time
  dependency graph collapses from many-to-many into many-to-one-to-many.

Outside that context the pattern is a liability, and dimension 4 lists the
specific cases.

## 3. Forces

The pattern balances the following competing pressures.

- **Coupling.** Favoured, strongly, and this is the main reason to adopt it. The
  count of edges in the dependency graph drops from the product of callers and
  subsystem types to the sum of callers plus subsystem types. Every caller now
  names one type. Everything the facade hides becomes free to change.
- **Cognitive load for the common case.** Favoured. The reader of a call site
  sees one method name that states the outcome instead of a recipe that states
  the mechanism.
- **Cognitive load for the uncommon case.** Sacrificed. A reader who needs to
  know what actually happens now has two files to read instead of one, and the
  facade's own body is often the least interesting code in the repository while
  being the code every trace passes through.
- **Expressive power.** Sacrificed by construction. The facade offers less than
  the subsystem. That loss is the point. It becomes a problem the moment a
  caller needs something the facade did not anticipate, and the pressure to add
  a parameter is immediate and constant.
- **Latency.** Close to neutral in-process, one extra call frame that most
  runtimes inline away. Favoured strongly across a network, which is the entire
  argument of the Remote Facade specialisation, where one coarse call replaces
  many fine-grained round trips.
- **Consistency.** Favoured. A single code path performs the sequence, so the
  ordering bug is fixed once. This is the argument that usually wins the review,
  and it is a stronger argument than readability.
- **Operability.** Favoured for instrumentation, since every use of the
  subsystem now passes one chokepoint where a metric, a timeout and a circuit
  breaker can live. Sacrificed for diagnosis, because a stack trace from inside
  the subsystem no longer tells the operator which business operation triggered
  it without a correlation identifier the facade must add.
- **Cost.** Favoured for build time in compiled languages, since incremental
  builds stop rebuilding two hundred files when a subsystem header changes.
  Sacrificed slightly in maintenance, since the facade is one more artifact that
  needs tests, documentation and a version.
- **Team topology.** Favoured, and this is underrated. The facade is a published
  contract between the team that owns the subsystem and the teams that consume
  it. The subsystem team becomes free to refactor behind it. The consuming teams
  gain a small surface to learn. The contract is where the negotiation happens,
  which is a social benefit encoded in a type.
- **Testability of callers.** Favoured. A caller that depends on one narrow
  interface is trivial to fake. A caller that depends on nine subsystem types
  needs nine fakes, or a container, or an integration test.
- **Testability of the whole.** Sacrificed mildly. The facade itself needs an
  integration test, because unit-testing a facade against mocks of the subsystem
  asserts the sequence the author wrote rather than the sequence the subsystem
  requires, which is a test that passes while production fails.

A pattern that sacrificed nothing would be a language feature. Facade pays in
expressive power and in one more layer that every trace crosses.

## 4. Applicability and non-applicability

Reach for Facade when the following hold.

- A subsystem is used by many callers who all want the same small outcome, and
  the sequence to reach it is long enough to be copied and long enough to be
  copied wrongly.
- The compile-time or link-time dependency from callers to subsystem internals
  is causing real pain, measured as build times, cyclic dependencies, or the
  blast radius of a version upgrade.
- A layered architecture needs a named entry point per layer, so that the layer
  boundary is a type a reviewer can point at rather than a convention in a
  document.
- The subsystem is third-party, and the codebase should own a small surface
  against it so that swapping or upgrading the library is a bounded change.
- The calls are remote, and collapsing many fine-grained calls into one
  coarse-grained call removes round trips, which is the Remote Facade case.
- A legacy subsystem is being strangled, and a facade is needed as the seam
  through which traffic is redirected incrementally to a replacement.
- The subsystem must be instrumented uniformly, and the facade is the one place
  where a timeout, a retry, a metric and a trace span can be applied to every
  use.

Non-applicability. Do NOT reach for Facade in these cases, and the reason is
worth more than the rule.

- **There is one caller.** A facade with one client is a private method with
  extra ceremony. Extract the method, keep it beside the caller, and revisit the
  decision when the second caller appears. The presence of a second caller is
  the cheapest available evidence that the abstraction is real.
- **The subsystem is already small and pleasant.** Wrapping a two-method
  interface in a two-method facade adds a hop and a file and removes nothing.
  The test is whether the facade's methods have a different shape from the
  subsystem's. If the facade is a pass-through, delete it.
- **Callers need different subsets, and the subsets do not overlap.** The facade
  becomes a union of every caller's needs, which is larger than the subsystem it
  was meant to shrink. Give each caller its own narrow interface instead. This is
  the Interface Segregation Principle arguing against a single facade, and it is
  the correct argument.
- **You need to make an incompatible interface fit an expected one.** That is
  Adapter. Facade does not convert, see dimension 13. If the caller already has
  a target interface it must satisfy, and the subsystem's shape does not match
  it, the driving force is conversion and the pattern is Adapter even when the
  result also happens to be simpler.
- **You need peers to stop referring to each other.** That is Mediator. Facade
  points one way, from caller into subsystem. Mediator sits between colleagues
  that would otherwise be mutually aware and routes between them in both
  directions.
- **You want to control access, add lazy loading, or enforce permissions on the
  same interface.** That is Proxy, which keeps the subject's interface identical
  and intercepts. A facade deliberately has a different interface.
- **The simplification is only a naming preference.** A facade added because a
  method name reads badly is a rename in disguise. Rename the method.
- **The language already gives you the shortcut cheaply.** A module-level
  function in Python, a package-level function in Go, or a top-level function in
  Kotlin gives the whole benefit with no type. The facade class exists in the
  book because C++ and Smalltalk of 1994 made a free function awkward or
  impossible to group. Do not import a 1994 packaging constraint into a language
  that does not have it. See dimension 8.
- **You cannot decide what the facade should not do.** If nobody on the team can
  state a capability that belongs in the subsystem and must never appear on the
  facade, the facade has no boundary and will become the god facade of dimension
  11. Write that exclusion list before writing the class.
- **The subsystem is complicated because it is badly designed.** A facade over a
  bad design freezes the bad design, because the facade now depends on its
  internals and every future clean-up has to preserve the facade's assumptions.
  Fix the subsystem first when you own it. Use a facade over a bad design only
  when you do not own it, which is the third-party case above.

## 5. Structure

Four participants, named by the role each plays.

- **Facade.** Knows which subsystem types are responsible for which part of a
  request, and delegates client requests to them in the right order. It owns the
  sequencing and the defaulting. It should own no domain rules, no persistence
  and no policy that could change independently of the subsystem. Its methods
  are named for outcomes in the caller's vocabulary, not for steps in the
  subsystem's vocabulary. It is normally stateless, or holds only the
  collaborators it was constructed with.
- **Subsystem classes.** Do the actual work. They implement the subsystem's
  functionality, they handle requests assigned to them by the Facade, and they
  hold no reference to the Facade. That last property is the structural
  invariant of the pattern and the single most useful thing to check in review.
  The moment a subsystem class imports the facade, the dependency graph has a
  cycle and the layering claim is false.
- **Client.** Uses the Facade for the common case. A client is not forbidden
  from using the subsystem directly, and the pattern is weaker, not stronger,
  when that path is closed off by force.
- **Facade interface, optional.** An abstract type the Facade implements, so
  that callers depend on an abstraction and the concrete facade can be
  substituted. Adding it converts the facade into a substitutable seam, which is
  what makes caller-side testing cheap and what makes the strangler-fig
  refactoring of dimension 14 possible. Omitting it is common and acceptable in
  a codebase with a single deployment and a fast test suite.

Relationships. The Facade holds references to subsystem classes, by
construction-time injection or by direct instantiation. The dependency arrows
run Client to Facade to Subsystem, and never back. Where the facade needs a
subsystem type in a public signature, that type becomes part of the facade's
published contract, which quietly defeats the decoupling, so a facade that is
serious about the boundary defines its own small parameter and result types.

Two structural variants change the shape enough to name.

- **Facade with subsystem-typed parameters.** Simpler to write, leaks the
  subsystem into every caller's imports. Suitable inside one module, wrong at a
  published boundary.
- **Facade with owned data-transfer types.** The facade defines the types that
  cross its boundary. Costs a mapping layer, buys a boundary that actually
  holds. This is the shape Remote Facade requires, because the fine-grained
  objects must not travel.

## 6. ASCII structure diagram

```
   +---------+   +---------+   +---------+   +---------+
   | Client  |   | Client  |   | Client  |   | Client  |
   |    A    |   |    B    |   |    C    |   |    D    |
   +----+----+   +----+----+   +----+----+   +----+----+
        |             |             |             |
        +------+------+------+------+-------------+
                      |
                      v
            +---------------------+
            |       Facade        |    one type the callers name
            |---------------------|
            | + send(msg)         |
            | + status(id)        |
            +----------+----------+
                       |
      +----------+-----+-----+----------+
      |          |           |          |
      v          v           v          v
  +---------+ +--------+ +---------+ +---------+
  |Transport| |Encoder | | Retry   | | Receipt |
  |         | |        | | Policy  | | Store   |
  +---------+ +--------+ +---------+ +---------+
        the subsystem. No arrow points back up.

  Escape hatch: a client MAY still reach a subsystem class
  directly. Facade adds a short path, it does not remove the
  long one.
```

Before the facade the picture is the same set of boxes with an edge from each
client to each subsystem class it happens to need. Sixteen edges become eight.
That arithmetic is the whole argument, and it is worth drawing on a whiteboard
before the class is written, because when the arithmetic does not improve the
facade is not earning its place.

## 7. Dynamics

The runtime flow has one property worth stating plainly. Control enters the
facade, fans out into the subsystem in a fixed order, and returns. The subsystem
never calls back into the facade. Any callback into the facade is either a bug
or a sign that the design is really a Mediator.

```
Client            Facade          Encoder      Transport      Receipts
  |                 |                |             |              |
  |-- send(msg) --->|                |             |              |
  |                 |                |             |              |
  |                 |-- encode(msg) ->|            |              |
  |                 |<-- payload ----|             |              |
  |                 |                |             |              |
  |                 |-- open() ------------------->|              |
  |                 |<-- conn --------------------|               |
  |                 |                |             |              |
  |                 |-- write(payload) ----------->|              |
  |                 |<-- ack ---------------------|               |
  |                 |                |             |              |
  |                 |-- record(ack) ----------------------------->|
  |                 |<-- id -------------------------------------|
  |                 |                |             |              |
  |                 |-- close() ------------------>|              |
  |<-- Receipt -----|                |             |              |
  |                 |                |             |              |
```

Three timing notes that decide whether the facade is correct.

First, resource lifetime. The facade opened the connection, so the facade closes
it, on every path including the error path. A facade that acquires a resource
and returns before releasing it has moved a cleanup obligation onto a caller who
cannot see the resource. This is the most common correctness defect in facade
code and it does not show up under light load.

Second, partial failure. The sequence above has four steps that can fail
independently. If `record` fails after `write` succeeded, the message was sent
and the receipt was lost. The facade must decide what that means and say so in
its contract, because the caller has no way to reason about it. A facade that
propagates a raw subsystem exception from step three has handed the caller a
puzzle whose pieces are hidden behind the facade.

Third, the error-translation boundary. If the facade lets subsystem exception
types escape, callers must import subsystem types to catch them, and the
decoupling is undone by the exception signature. Spring's `JdbcTemplate` handles
this explicitly, catching JDBC exceptions and translating them to the common
`org.springframework.dao` exception hierarchy ([Spring Framework Javadoc,
JdbcTemplate](https://docs.spring.io/spring-framework/docs/current/javadoc-api/org/springframework/jdbc/core/JdbcTemplate.html),
verified 2026-08-02). Facades that skip this step are decoupled on the happy
path only.

## 8. Implementation variants

**Class with injected collaborators.** The facade takes its subsystem
collaborators as constructor parameters. Most testable form, and the one to
prefer at a published boundary, because a test can supply fakes and a deployment
can supply a different transport. Costs a wiring site, which a dependency
injection container usually already provides.

**Class that constructs its own collaborators.** The facade hides the wiring as
well as the sequencing, which is the maximal convenience form. It is the right
call for a one-line convenience API where the caller has no wiring context, and
the wrong call at a boundary that needs substitution, because the collaborators
are now unreachable from a test.

**Module of free functions.** In Python, Go, Kotlin, JavaScript, Rust and C the
facade is a module or package exposing a handful of functions over private
internals. There is no class and no object. This is by far the most common real
shape of the pattern outside Java and C#, and treating the class form as
canonical misreads the book's C++ and Smalltalk context. Rust's
`std::fs::read_to_string` is documented as a convenience function for using
`File::open` and `read_to_string` with fewer imports and without an intermediate
variable ([Rust standard library documentation](https://doc.rust-lang.org/std/fs/fn.read_to_string.html),
verified 2026-08-02), which is the pattern with no type at all.

**Interface plus implementation.** The facade is declared as an interface and
implemented once. Buys substitutability and a stated contract. Pays one more
file, and pays an ongoing tax if the interface is never implemented twice, which
is the speculative-generality objection. A defensible middle position is to
introduce the interface at the moment a second implementation, a test double
that must be a real type, or a strangler migration actually needs it.

**Static or singleton facade.** A globally reachable facade, reached without
wiring. Cheapest to call, hardest to test, and it makes the subsystem a global
dependency of everything that calls it. SLF4J's `LoggerFactory` is the
respectable version of this shape, and logging is close to the only domain where
the trade is usually worth making, because logging is genuinely ambient and
genuinely cross-cutting.

**Facade over a facade.** Layered systems stack them, one per layer boundary.
Legitimate when each layer is a real boundary with its own vocabulary. A smell
when each layer adds a method that forwards to the layer below without changing
shape, which produces the pass-through stack that dimension 11 describes.

**Parameter object on the facade.** Where the facade method would take nine
arguments, it takes one request object it owns. Keeps the boundary stable when
new options arrive, at the cost of a type and a mapping step. This is close to
mandatory for a Remote Facade, because the boundary crosses a wire and the wire
format is versioned.

**Facade with an explicit escape hatch.** The facade exposes an accessor
returning the underlying subsystem object for the caller who has outgrown it.
Documented and used well, this defuses the pressure that otherwise grows the
facade into a god object. Used carelessly it makes the boundary decorative,
because every caller reaches through it. The workable compromise is to make the
escape hatch obvious in name, for example `underlyingConnection`, so that its
use is visible in review.

**Instrumented facade.** The facade wraps each delegation in a timer, a span and
an error counter. This is the operability payoff of the chokepoint and it costs
almost nothing to add at construction time. Retrofitting it later is harder,
because by then callers have found reasons to bypass the facade.

**Generated facade.** In distributed systems the coarse-grained facade is often
generated from an interface definition, for example a gRPC service stub or an
OpenAPI client. The generated code is a facade in every respect except that
nobody hand-writes it. Recognising it as one matters, because the same failure
modes apply, particularly the god facade when the service definition accretes
operations without a boundary.

## 9. Known production uses

**SLF4J, the Simple Logging Facade for Java.** The project describes itself as a
simple facade or abstraction for various logging frameworks such as
`java.util.logging`, log4j 1.x, reload4j and logback, and states that it allows
the end user to plug in the desired logging framework at deployment time. SLF4J
user manual, https://www.slf4j.org/manual.html verified 2026-08-02. This is the
clearest named-in-the-wild use of the word, and it is also the clearest example
of the Adapter overlap discussed in dimension 13, since the per-backend bindings
convert one interface into another while the `LoggerFactory` entry point
simplifies.

**Spring Framework, `JdbcTemplate`.** The Javadoc states that the class
simplifies the use of JDBC and helps to avoid common errors, that it executes
core JDBC workflow leaving application code to provide SQL and extract results,
and that it catches JDBC exceptions and translates them to the common
`org.springframework.dao` exception hierarchy. It is described as the central
delegate in the JDBC core package. Spring Framework Javadoc,
https://docs.spring.io/spring-framework/docs/current/javadoc-api/org/springframework/jdbc/core/JdbcTemplate.html
verified 2026-08-02. A caller writes one method call where raw JDBC needs a
connection, a statement, a result set, three close calls and a checked
exception, which is the sequencing-plus-cleanup-plus-error-translation shape in
full.

**Python `requests`.** The documentation states that Requests allows you to send
HTTP/1.1 requests extremely easily, that there is no need to manually add query
strings to URLs or to form-encode POST data, and that keep-alive and HTTP
connection pooling are automatic thanks to urllib3. Requests documentation,
https://requests.readthedocs.io/en/latest/ verified 2026-08-02. The subsystem is
urllib3 plus the standard library's HTTP and TLS machinery, the facade is the
top-level `requests` module, and the escape hatch is explicit in the
documentation's own section headings for lower-level classes and transport
adapters.

**Rust standard library, `std::fs::read_to_string`.** The documentation states
that the function reads the entire contents of a file into a string, and that it
is a convenience function for using `File::open` and `read_to_string` with fewer
imports and without an intermediate variable. Rust standard library
documentation, https://doc.rust-lang.org/std/fs/fn.read_to_string.html verified
2026-08-02. It is a free function, it names no type, and the underlying types
remain fully available, which makes it a good demonstration that the pattern
does not require a class.

**Django, `django.shortcuts.render`.** The documentation states that `render`
combines a given template with a given context dictionary and returns an
`HttpResponse` object with that rendered text, and shows the equivalent
three-step version using `loader.get_template`, `Template.render` and an explicit
`HttpResponse` construction. Django 5.2 documentation, Built-in shortcut
functions, https://docs.djangoproject.com/en/5.2/topics/http/shortcuts/ verified
2026-08-02. The module name, `shortcuts`, is an honest statement of what a
facade is for, and the documentation's habit of showing the long form beside the
short form is a practice worth copying.

## 10. Consequences

Positive.

- Callers are shielded from subsystem types, so the subsystem can be
  restructured, upgraded or replaced without editing call sites. This is the
  consequence that pays for the pattern in a large codebase.
- The correct sequence exists once. Ordering bugs, missing cleanup and forgotten
  defaults are fixed in one file rather than in every copy.
- The dependency graph gets smaller and more layered, which shortens incremental
  builds in compiled languages and removes whole classes of import cycle.
- A single chokepoint appears where cross-cutting behaviour can be applied,
  covering timeouts, retries, metrics, tracing, caching, authorisation checks and
  rate limits.
- The learning curve for a new team member drops sharply, because the surface
  they must understand to be productive is one small type rather than a
  subsystem.
- The boundary becomes a negotiable contract between teams, which converts an
  implicit social dependency into an explicit technical one that can be
  versioned and deprecated.
- Caller-side tests get cheaper, since one narrow collaborator is easy to fake.

Negative.

- The facade can hide capability that a caller legitimately needs, and the
  pressure to add one more parameter never stops. Left unmanaged this produces
  the god facade of dimension 11.
- One more indirection layer for every reader and every stack trace. In a system
  with several stacked facades the trace becomes tall and uninformative.
- The facade is a coupling point of its own. Every caller now depends on it, so
  changing its signature is expensive in exactly the way changing the subsystem
  used to be. The facade has concentrated the coupling rather than removed it,
  and concentration helps only while the facade stays small.
- A facade that hides cost invites misuse. A method that looks like a field
  access but opens a network connection will be called inside a loop, because
  nothing at the call site says otherwise.
- Duplicate abstraction risk. If the subsystem later grows its own convenience
  API, the codebase has two facades and neither is authoritative.
- Testing the facade well requires an integration test against the real
  subsystem. A unit test with mocked collaborators asserts the sequence the
  author intended and cannot detect that the subsystem requires a different one.
- Versioning becomes a real obligation once the facade is published outside the
  team, because it is now an API with external implementors and external
  callers.

## 11. Failure modes and misuse

**The god facade.** Symptom. The file is four thousand lines. It has ninety
public methods. Its test file is the slowest in the suite. Every feature branch
touches it, so it is the merge-conflict hotspot of the repository, and the team
has begun to say "put it in the service class" as a reflex. Its imports include
the persistence layer, the HTTP layer, the domain model and two other facades.
New engineers read it to learn how the system works, which is the tell that it
has stopped being a face and become the building. Cause. Every new requirement
was cheaper to add as one more method on the existing facade than to place
correctly, and no exclusion list ever existed, so the facade had no definition of
what did not belong in it. The accretion is invisible per commit and obvious per
quarter. Fix. Split by client use case rather than by subsystem, since the
clients are what actually vary. Take the method-usage matrix of callers against
facade methods, find the blocks, and each block becomes its own narrow facade.
Move any logic that is neither sequencing nor defaulting down into the subsystem
where it belongs, because logic on a facade is the thing that made it heavy.
Write the exclusion list before the split so the new facades do not repeat the
history. Guard it with a size budget in review, for example a method count that
requires a conversation to exceed, since the failure is gradual and gradual
failures need mechanical limits rather than intentions.

**The pass-through facade.** Symptom. Every method on the facade forwards one
call to one subsystem method with the same name and the same arguments, and code
review keeps producing the comment that it is unclear what this class adds.
Cause. The pattern was applied as ritual rather than to solve a stated problem,
often because a style guide said each layer needs a facade. Fix. Delete it and
let callers use the subsystem, unless the facade exists specifically to reverse
a dependency direction, in which case keep it and document that single reason at
the top of the file so the next reviewer does not delete it.

**Leaked subsystem types.** Symptom. Callers still import subsystem packages
even though the facade exists, because a facade method takes or returns a
subsystem type. The upgrade that the facade was meant to contain still touches
two hundred files. Cause. The facade's signature was written for convenience
rather than for the boundary. Fix. Define the facade's own parameter and result
types and map at the boundary. Verify mechanically with an architecture test
that fails the build when a caller package imports a subsystem package.

**Leaked exceptions.** Symptom. A `catch` for a subsystem exception type appears
in a caller, or worse, an unhandled subsystem exception reaches the top-level
handler and produces an error message written in the subsystem's vocabulary that
a support engineer cannot map to a business operation. Cause. Error translation
was skipped because the happy path worked. Fix. Translate at the facade, as
`JdbcTemplate` does, and add a test that asserts a subsystem failure arrives at
the caller as a facade-level error type.

**Hidden cost invites the N plus one.** Symptom. A page that renders one hundred
rows makes one hundred and one database queries or HTTP calls, found on a
latency graph rather than in a code review. The facade method looks like a
cheap accessor at the call site. Cause. Facade removed the visual weight that
used to signal expense. Fix. Name the method so the cost is visible, for example
`fetchOrder` rather than `order`, add a batch method for the collection case, and
put a per-request call counter on the facade so the loop shows up in telemetry
rather than in an incident.

**Resource leak on the error path.** Symptom. Connection pool exhaustion or file
descriptor exhaustion under load, with a healthy system at low traffic and a
failure that only appears when the error rate rises. Cause. The facade acquires
a resource, and the release is on the happy path only, so every failure leaks
one. Fix. Use the language's scoped-cleanup construct, try-with-resources, a
context manager, `defer`, `Drop`, and add a test that injects a failure at each
step and asserts the resource count returns to its starting value.

**The facade that grew a database.** Symptom. The facade holds a mutable cache,
a counter, or a piece of session state, and two tests interfere with each other
depending on execution order. Cause. State was added to a stateless
collaborator because the facade was the convenient place to put it. Fix. Move
the state into an explicit collaborator with its own lifecycle and inject it, so
the state has an owner and a test can reset it.

**Bypass drift.** Symptom. The facade exists, and half the codebase does not use
it, so the ordering bug the facade was meant to fix still occurs in the half that
bypassed it. Cause. The facade did not cover a case that a caller needed, and
rather than extending it the caller went around it, quietly. Fix. Find the
bypasses with a dependency rule that flags direct subsystem imports outside an
allowlist, then treat each one as a requirement the facade is missing rather than
as a discipline problem.

**Facade misidentified as Adapter.** Symptom. The class implements an interface
owned by the caller's side, and the team calls it a facade, so nobody notices
that the conversion has an assumption baked in, for example that null means
absent. Cause. The words are used loosely. Fix. Name it for its driving force.
Conversion means Adapter, and Adapter has its own review checklist about
semantic mismatch, which is the checklist that catches the null assumption.

## 12. Trade-off matrix

Compared against named alternatives across the forces from dimension 3.

| Force | Facade | Adapter | Mediator | Proxy | Anti-Corruption Layer | Service Layer (Fowler) | Direct subsystem use |
|---|---|---|---|---|---|---|---|
| Driving intent | Simplify a subsystem's surface | Convert one interface into another | Coordinate mutually aware peers | Control access to one subject | Translate a foreign model into ours | Define the application boundary and its operations | None, callers use what exists |
| Interface relative to the subject | Deliberately different and smaller | Different, fixed by the target | New, replaces peer-to-peer wiring | Identical to the subject | Different, expressed in our domain | New, expressed in use cases | Identical |
| Direction of knowledge | One way, caller into subsystem | One way, client into adaptee | Two way, hub to and from colleagues | One way, client into subject | One way, our side into theirs | One way, presentation into domain | Many to many |
| Coupling reduction | High. Many-to-many becomes many-to-one | Low. One pairing at a time | High between peers | None. Same interface | High, plus model isolation | High at the layer boundary | None |
| Cognitive load added | One hop | One hop plus a mapping to reason about | A hub whose rules must be read | One hop, usually invisible | A mapping plus two vocabularies | One layer of use-case types | None |
| Latency | One call, neutral in process, better remotely | One call plus conversion | Hub dispatch per interaction | One call plus the control check | Conversion cost per crossing | One call, plus transaction control | Lowest |
| Operability | Strong chokepoint for metrics | Weak, per pairing | Strong, all interaction visible at the hub | Strong for access decisions | Strong at the integration seam | Strong for transactions and audit | None, scattered |
| Team topology fit | Platform team publishes it, product teams consume | Whoever owns the mismatch | One owner of the interaction rules | Infrastructure concern | The team defending its model | Application team owns the boundary | No seam to own |
| Failure when overgrown | God facade, dimension 11 | Adapter with hidden semantic drift | God mediator, all logic in the hub | Proxy that changes behaviour silently | Translation layer nobody understands | Anemic domain with logic in services | Copy-paste drift across call sites |
| Cost to remove later | Medium. Inline into callers | Low. One pairing | High. Peers must relearn each other | Low | High | High | Not applicable |

Reading of the table. Facade wins when the problem is that the surface is too
large for the common case and the callers all want roughly the same thing.
Adapter wins when a fixed target interface must be satisfied. Mediator wins when
the problem is peers knowing about peers rather than a caller knowing about a
subsystem. Proxy wins when the interface must stay the same and something must
happen around the call. Anti-Corruption Layer wins when the foreign model would
corrupt ours if it crossed. Service Layer wins when the boundary being drawn is
the application's own, not a subsystem's. Direct use wins when there are few
callers, which is more often than pattern catalogs admit.

## 13. Related and incompatible patterns

**Adapter.** The most frequently confused neighbour, and the distinction is by
driving force rather than by shape. Adapter converts an existing interface into
the one a client already expects, so the target interface is fixed by something
outside the adapter's control and the adapter has no latitude over its own
signature. Facade defines a new interface that did not previously exist, chosen
freely to suit the common case, so the facade's signature is the designer's
decision. Adapter usually fronts one adaptee, Facade usually fronts several
subsystem types, though the counts are a heuristic rather than the rule. A
practical test. Ask whether an interface that the wrapper must satisfy already
existed before the wrapper was written. Yes means Adapter. No means Facade. A
second test. Would the wrapper's signature change if the thing behind it were
replaced by an equivalent from another vendor. Facade, no. Adapter, quite
possibly, because the conversion is specific to the adaptee. SLF4J is
instructive precisely because it is both at once. The `LoggerFactory` and
`Logger` types callers see are a facade, since they are a new simplified surface
designed by SLF4J. Each backend binding is an Adapter, since it converts SLF4J's
interface into the fixed interface of logback or `java.util.logging`, and the
manual's own description of plugging in the desired framework at deployment time
is a description of the adapter layer ([SLF4J user manual](https://www.slf4j.org/manual.html),
verified 2026-08-02).

**Mediator.** Also confused with Facade, and the distinction is the direction of
knowledge. Facade is unidirectional. Callers know the facade, the subsystem does
not know the facade exists, and control always flows inward. Mediator is
bidirectional. The colleagues know the mediator and send it messages, and the
mediator sends messages back to colleagues. Where Facade abstracts a subsystem
to make it easier to consume, Mediator centralises communication between peers
that would otherwise reference each other. The consequence for design is
concrete. Removing a facade leaves the subsystem working, since nothing in it
referred to the facade. Removing a mediator breaks every colleague, since each
depended on the hub for its interactions. Both share the god-object failure
mode, and for the same reason, that a hub is the path of least resistance for
new logic.

**Service Layer, from Fowler's *Patterns of Enterprise Application
Architecture*.** Defined as establishing an application's boundary with a layer
of services that sets out a set of available operations and coordinates the
application's response in each operation ([martinfowler.com Service Layer catalog
entry](https://martinfowler.com/eaaCatalog/serviceLayer.html), verified
2026-08-02). The relationship to Facade is that a Service Layer is a facade over
the domain, with additional obligations that a plain facade does not carry.
Transaction demarcation, security enforcement and use-case naming belong to a
Service Layer and do not belong to a generic facade. Fowler places the pattern
in chapter 9 of the book, per the same catalog page. The practical consequence
is a warning. Building a Service Layer and calling it a facade tends to produce
a facade with transaction annotations scattered through it, which is how the god
facade starts in enterprise codebases. Name it Service Layer, accept the extra
obligations, and hold the domain logic below it.

**Remote Facade, same book.** Defined as providing a coarse-grained facade on
fine-grained objects to improve efficiency over a network ([martinfowler.com
Remote Facade catalog entry](https://martinfowler.com/eaaCatalog/remoteFacade.html),
verified 2026-08-02), and placed in chapter 15 per the same page. This is Facade
with the force set to latency rather than to readability, and it changes two
design decisions. Parameters and results must be data transfer objects rather
than fine-grained domain objects, because the fine-grained objects would produce
the round trips the pattern exists to remove. And the facade must be as
coarse-grained as the use case allows, which is the opposite of the
in-process advice to keep methods small. A team that carries in-process facade
habits across a network boundary produces a chatty remote interface, and a team
that carries Remote Facade habits into an in-process facade produces methods
with fifteen parameters.

**Layered and hexagonal architecture.** In a layered architecture the facade is
the natural implementation of a layer boundary, one facade per layer, and it is
what makes the claim that layer B talks only to layer C checkable rather than
aspirational. In hexagonal architecture, also called ports and adapters, the
mapping is more careful and easy to get wrong. A driving port, the interface the
application exposes inbound, is a facade over the application's use cases, and
this is the same object a Service Layer describes. A driven port, the interface
the application requires outbound, is not a facade, because the application
defines it for its own needs and the infrastructure implements it, which makes
the infrastructure side an Adapter by both name and force. Confusing the two
produces the common error of writing outbound interfaces in the vocabulary of
the database rather than of the application, which leaves the hexagon pointing
the wrong way and gives none of the isolation the shape was adopted for.

**Anti-Corruption Layer, from Eric Evans's Domain-Driven Design.** A facade plus
a translation. Where a plain facade simplifies a subsystem while keeping its
concepts, an anti-corruption layer replaces the foreign subsystem's concepts
with the local domain's concepts specifically so that the foreign model cannot
propagate inward. Reach for it at an integration boundary with a system whose
model differs from yours. Reach for a plain facade when the models agree and only
the ergonomics are wrong.

**Abstract Factory.** Composes with Facade rather than competing. A facade often
needs a family of consistent subsystem objects, and an Abstract Factory is how it
obtains them without naming concrete types, which keeps the facade itself
substitutable across implementations of the subsystem.

**Proxy.** Different intent, and the interface is the discriminator. A proxy
presents the same interface as its subject and intercepts calls to add access
control, laziness, caching or remoting. A facade presents a different interface.
When a wrapper both simplifies and intercepts, name it for whichever property a
caller would notice first, and be aware that a facade with caching inside it is a
facade that has quietly acquired state, which is one of the failure modes above.

**Singleton.** Conflicts in practice. A facade exposed as a process-wide
singleton removes substitutability at exactly the seam that made caller testing
cheap, and makes test execution order matter. Where ambient access is genuinely
wanted, as in logging, prefer a single well-known accessor over a private
constructor plus static state, so a test retains a way to substitute.

**Decorator.** Not a competitor but a frequent companion. Decorating the facade,
rather than adding behaviour inside it, is the correct way to add retries,
caching or tracing without growing the facade's body, and it keeps the god-facade
pressure off the original class.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. The named refactorings
are Extract Function, Move Function and Extract Class from Martin Fowler,
*Refactoring. Improving the Design of Existing Code*, 2nd edition,
Addison-Wesley, 2018. Cross reference the refactoring family entries for those.
Ordered steps.

1. Find the duplicated sequence. Search for the subsystem's most distinctive type
   name across the repository and read every hit. Do not start writing until you
   have counted the call sites, because the count decides whether the pattern is
   warranted at all.
2. Write down the differences between the copies. This list becomes the facade's
   parameters, and anything not on the list becomes a default. Doing this before
   coding is what keeps the parameter list small later.
3. Write down the exclusion list. State what the facade will not do, in one line
   each. This is the step teams skip and it is the step that prevents the god
   facade, because a boundary that was never stated cannot be defended in a
   review two years later.
4. Extract the sequence into a function beside the first caller, unchanged in
   behaviour, and have that caller use it. Run the tests. Nothing has moved yet.
5. Move the function into a new module or class at the boundary you intend. Run
   the tests. The pattern now exists in skeleton.
6. Migrate the second call site. This is where the parameter list gets its real
   shape, because the second caller is the first honest test of the abstraction.
   Migrate the third only after the second is clean.
7. Replace subsystem types in the facade's signature with types the facade owns,
   if the boundary is meant to hold. Map at the edge. Skipping this leaves the
   leaked-types failure from dimension 11.
8. Add error translation, so subsystem exception types do not escape.
9. Add the architecture test that forbids callers from importing subsystem
   packages, with an allowlist for the deliberate escape-hatch cases. Without
   this the boundary decays quietly.
10. Migrate the remaining call sites, then delete the duplicated sequences.

For a legacy subsystem being replaced rather than wrapped, the same seam carries
the strangler-fig migration. Put the facade in front of the old subsystem with no
behaviour change, redirect one operation at a time to the new implementation
behind the facade, compare outputs in production where the operation is
idempotent, and retire the old path per operation rather than in one cutover.

Removing the pattern when it stops earning its place. Signs that it should go
include a facade whose every method forwards one call unchanged, a facade with
one remaining caller after the others were deleted, and a subsystem that has
grown its own convenience API that is better than yours.

1. Confirm the facade holds no logic of its own. If it holds sequencing,
   defaulting or error translation, that behaviour needs a home before the class
   can go, and the honest home is usually the subsystem.
2. Inline the facade into its callers one at a time, using Inline Function, and
   run the tests after each.
3. Delete the facade's own parameter and result types if nothing else uses them,
   and let the subsystem's types travel again. Accept that the boundary is gone.
4. Remove the architecture test that guarded the boundary, in the same commit,
   so a stale rule does not fail a later build for a boundary that no longer
   exists.
5. If the facade held real logic that has no home, do not delete it. Rename it
   for what it actually does and stop calling it a facade, because a thing with
   behaviour and a name that denies having behaviour is worse than either.

## 15. Testing and verification

Easier because of the pattern.

- Caller tests get much cheaper. A caller depends on one narrow interface, so a
  handwritten fake replaces a container, a database and a network. This is the
  main testability payoff and it is usually the argument that carries the design
  review.
- The subsystem sequence has one place to test. A single integration test
  against the real subsystem covers behaviour that would otherwise need a test
  per call site, or more commonly would go untested at every call site.
- Contract clarity. Because the facade's surface is small, an exhaustive test of
  it is achievable, which is rarely true of the subsystem it fronts.
- Cross-cutting behaviour becomes testable in one place. A timeout, a retry
  policy or an authorisation check applied at the facade has one test rather than
  a test per caller.

Harder because of the pattern.

- Unit-testing the facade with mocked subsystem collaborators is close to
  worthless on its own. Such a test asserts that the facade calls the methods the
  author decided to call, in the order the author decided, which is the
  implementation restated as an expectation. It passes when the real subsystem
  requires a different order. Treat mock-based facade tests as change detectors
  and rely on an integration test for correctness.
- Failure-path coverage grows. The facade collapses several failure sources into
  one method, so the number of distinct failures behind one call goes up while
  the number of visible signatures goes down. Each hidden failure needs a
  deliberate test.
- Diagnosing a failing test gets slower, because a red facade test could be the
  facade, any collaborator, or the wiring between them.

Techniques that apply.

- **Integration test as the primary test of the facade.** Run against the real
  subsystem where feasible, or against a high-fidelity substitute such as a
  container-hosted database or a recorded HTTP transport. The point is to
  exercise the sequencing against something that enforces the subsystem's real
  rules.
- **Fake facade for caller tests.** Prefer a small handwritten implementation of
  the facade interface over a mocking framework. It is readable, it can carry
  simple state for assertions, and it does not encode call-order expectations
  that make refactoring expensive.
- **Contract test shared between real and fake.** Write one test suite against
  the facade interface and run it against both the real implementation and the
  fake. This catches the drift where a fake stays permissive after the real
  implementation adds validation, which is the failure that makes caller tests
  green while production rejects the same input.
- **Fault injection per step.** Inject a failure at each subsystem step in turn
  and assert two properties. The caller sees a facade-level error type, and every
  acquired resource is released. Assert the second one by counting live
  connections or descriptors before and after, since this is the resource-leak
  failure of dimension 11 and it is invisible to an assertion on the return value.
- **Architecture test on imports.** Assert mechanically that no package outside
  the allowlist imports the subsystem. Tools for this exist in most language
  toolchains, and without one the boundary is a convention that erodes at a
  steady rate.
- **Call-count assertion for the hidden-cost failure.** In a test that exercises
  a collection path, assert an upper bound on subsystem calls. This catches the
  N plus one before it reaches a latency graph.
- **Characterisation test before a strangler migration.** Record the facade's
  observable outputs for a representative input set before redirecting anything
  behind it, then hold those outputs fixed while the implementation moves.

## 16. Observability signals

The pattern hides which subsystem work was performed, so that work has to appear
in telemetry or an operator cannot reason about it. The compensating advantage is
that the facade is a single chokepoint, which makes the instrumentation cheap to
add and uniform once added.

What to record.

- A span per facade method, named for the business outcome rather than the
  subsystem step, with child spans for each subsystem call. This single change
  turns the facade from an obstacle to diagnosis into the best summary view in
  the trace, because the parent span reads as the intent and the children read as
  the mechanism.
- A request-scoped correlation identifier, attached by the facade to every
  downstream call, so a subsystem log line can be tied back to the business
  operation that caused it. Without this the subsystem's logs are unattributable,
  which is the operability cost of the pattern in its rawest form.
- A counter of facade invocations labelled by method, and a matching counter of
  failures labelled by method and by translated error type. The ratio between
  them is the health indicator for the boundary.
- A latency histogram per facade method, and a second histogram per subsystem
  step underneath it. Having both is what lets an operator answer whether a slow
  facade call is slow because of one step or because of the number of steps.
- A per-request counter of subsystem calls made through the facade, exported as a
  histogram. A bimodal distribution with a long tail is the fingerprint of the N
  plus one failure, and it is visible here long before it is visible in latency.
- Resource gauges for anything the facade acquires, connections held, files open,
  and a counter of acquisitions against a counter of releases. The difference
  between those two counters over a window is the leak detector.
- A counter of subsystem-direct calls that bypass the facade, where the runtime
  permits instrumenting the subsystem. Bypass drift is otherwise invisible until
  the bug it causes appears.

A healthy instance on a dashboard. Facade invocation counts track the business
event rate, with a stable ratio between them. The per-method latency histogram is
tight and its ninety-fifth percentile sits close to the sum of its child spans,
which shows the facade is adding sequencing and not waiting. Subsystem calls per
request are flat and small, and the distribution has no second mode. Acquisition
and release counters track each other exactly, and the resource gauge returns to
its resting value between traffic peaks. The failure counter is near zero and the
errors that do appear carry translated types, meaning no raw subsystem type
escaped.

A failing instance. Subsystem calls per request develop a second mode
proportional to a collection size, which is the N plus one and localises to one
facade method by label. Or the facade latency histogram grows a tail that no
child span accounts for, which points at contention or resource waiting inside
the facade rather than at the subsystem. Or the acquisition counter outruns the
release counter by a steady rate that correlates with the error rate, which is
the error-path resource leak, and the resource gauge climbing monotonically
across a quiet period confirms it. Or an untranslated subsystem error type
appears in the error-label distribution, which means a path exists that skipped
the translation step. Or the bypass counter becomes non-zero after a release,
which means a new caller went around the boundary and the facade is now missing
a capability somebody needed.

## 17. Security and privacy implications

The pattern is close to neutral on security in its plain in-process form, and
saying otherwise would be inventing a concern. Four real implications appear
once the facade sits at a boundary that matters.

**Chokepoint for authorisation, in both directions.** A facade is a natural place
to apply an authorisation check to every subsystem use, and where it is used that
way the security property becomes checkable by inspecting one file. The same
property is the risk. If callers can reach the subsystem directly, the check is
advisory rather than enforced, and the system looks safer in review than it is.
A facade whose security value depends on nobody bypassing it needs a mechanical
guard, either a module-visibility restriction that makes the subsystem
unreachable, or the architecture test from dimension 15 running in the build.

**Confused deputy.** The facade acts on behalf of its callers and often holds
credentials or a connection that the caller does not itself possess. A facade
method that accepts an identifier and returns the object it names, without
checking that the caller may see that object, has turned the facade into a
deputy that will fetch anything for anyone. This is the standard shape of an
insecure direct object reference, and the facade makes it likelier because the
method reads as a lookup rather than as a privileged operation. The rule is that
authority travels with the request, so pass the caller's identity into the
facade and check it there, rather than letting the facade's own privileges stand
in for the caller's.

**Error translation as an information-disclosure control, and as a hazard.**
Translating subsystem errors at the facade is a security benefit when it strips
stack traces, connection strings, file paths, SQL fragments and internal
hostnames out of what reaches the caller. It is a hazard when the translated
message is constructed by concatenating the original message, which reintroduces
the disclosure while looking like it was handled. Translate to a fixed set of
error types with fixed messages, log the original at the boundary with the
correlation identifier, and let the operator join the two.

**Denial of service through hidden amplification.** Because the facade hides how
much work one call performs, a request path that calls a facade method once per
item in an attacker-controlled list turns a cheap request into an expensive one,
and the call site gives no hint of the ratio. Bound the number of facade
invocations per request at the caller, and put a rate limit or a concurrency
limit on the expensive facade methods themselves so the bound holds even when a
new caller forgets it.

On privacy the pattern is neutral in itself, with two practical caveats. First,
the facade's own parameter and result types are where data minimisation is
cheapest to apply. A facade that returns the subsystem's full record when the
caller needs two fields has spread personal data across every caller and every
log that touches them, whereas a facade that returns a narrow result confines it.
Second, the correlation identifier recommended in dimension 16 must not be a
user identifier, an email address or an account number, because it is attached to
every downstream log line by design and inherits the longest retention of any of
them. Use an opaque request identifier and join to the subject elsewhere under
the access controls that apply to identifiers.

## Code examples

Three languages chosen to show three genuinely different shapes rather than the
same class translated three times. Python shows the module-of-functions form,
which is how the pattern actually appears in Python libraries. TypeScript shows
the class with injected collaborators plus an interface, which is the form that
buys substitutability at a boundary. Go shows the interface-owned-by-the-consumer
form, where the facade's contract is declared by the package that uses it. Rust
is omitted from the worked examples not because the pattern fails there, since
`std::fs::read_to_string` in dimension 9 is a facade, but because the idiomatic
Rust version is a free function over private items, which is what the Python
example already demonstrates, so a Rust listing would repeat rather than add.

All three examples model the same subsystem from dimension 2. An encoder, a
transport and a receipt store, sequenced behind one operation, with cleanup on
every path and error translation at the boundary.

### Python

The module is the facade. There is no class, and the subsystem types stay
importable for the caller who needs them.

```python
class MailError(Exception):
    pass


class Encoder:
    def encode(self, subject: str, body: str) -> bytes:
        return f"Subject: {subject}\n\n{body}".encode("utf-8")


class Transport:
    def __init__(self) -> None:
        self.open_count = 0

    def open(self) -> "Transport":
        self.open_count += 1
        return self

    def write(self, payload: bytes) -> str:
        if not payload:
            raise ValueError("empty payload")
        return f"ack-{len(payload)}"

    def close(self) -> None:
        self.open_count -= 1


class ReceiptStore:
    def __init__(self) -> None:
        self.records: list[str] = []

    def record(self, ack: str) -> str:
        self.records.append(ack)
        return f"receipt-{len(self.records)}"


_encoder = Encoder()
_transport = Transport()
_receipts = ReceiptStore()


def send(subject: str, body: str) -> str:
    # Sequencing, defaulting, cleanup and error translation. Nothing else.
    payload = _encoder.encode(subject, body)
    conn = _transport.open()
    try:
        ack = conn.write(payload)
    except ValueError as exc:
        raise MailError(str(exc)) from exc
    finally:
        conn.close()
    return _receipts.record(ack)


if __name__ == "__main__":
    print(send("hello", "first message"))
    print(send("hello", "second message"))
    print("leaked connections:", _transport.open_count)
```

### TypeScript

The interface is what callers depend on, so a test supplies a fake without
touching the subsystem.

```typescript
class MailError extends Error {}

interface Mailer {
  send(subject: string, body: string): string;
}

class Encoder {
  encode(subject: string, body: string): string {
    return `Subject: ${subject}\n\n${body}`;
  }
}

class Transport {
  openCount = 0;
  open(): void {
    this.openCount += 1;
  }
  write(payload: string): string {
    if (payload.length === 0) throw new Error("empty payload");
    return `ack-${payload.length}`;
  }
  close(): void {
    this.openCount -= 1;
  }
}

class ReceiptStore {
  private n = 0;
  record(_ack: string): string {
    this.n += 1;
    return `receipt-${this.n}`;
  }
}

class MailFacade implements Mailer {
  constructor(
    private readonly encoder: Encoder,
    private readonly transport: Transport,
    private readonly receipts: ReceiptStore,
  ) {}

  send(subject: string, body: string): string {
    const payload = this.encoder.encode(subject, body);
    this.transport.open();
    try {
      const ack = this.transport.write(payload);
      return this.receipts.record(ack);
    } catch (e) {
      throw new MailError((e as Error).message);
    } finally {
      this.transport.close();
    }
  }
}

const transport = new Transport();
const mailer: Mailer = new MailFacade(new Encoder(), transport, new ReceiptStore());
console.log(mailer.send("hello", "first message"));
console.log("leaked connections:", transport.openCount);
```

A caller test needs no subsystem at all.

```typescript
class FakeMailer implements Mailer {
  sent: string[] = [];
  send(subject: string, _body: string): string {
    this.sent.push(subject);
    return "receipt-fake";
  }
}
```

### Go

The consuming package declares the interface it needs, so the facade package does
not have to publish one. Cleanup runs through `defer` on every path.

```go
package main

import (
	"errors"
	"fmt"
)

var ErrMail = errors.New("mail failed")

type encoder struct{}

func (encoder) encode(subject, body string) string {
	return "Subject: " + subject + "\n\n" + body
}

type transport struct{ openCount int }

func (t *transport) open()  { t.openCount++ }
func (t *transport) close() { t.openCount-- }

func (t *transport) write(payload string) (string, error) {
	if payload == "" {
		return "", errors.New("empty payload")
	}
	return fmt.Sprintf("ack-%d", len(payload)), nil
}

type receipts struct{ n int }

func (r *receipts) record(string) string {
	r.n++
	return fmt.Sprintf("receipt-%d", r.n)
}

type Mail struct {
	enc  encoder
	tr   *transport
	rcpt *receipts
}

func NewMail() *Mail {
	return &Mail{tr: &transport{}, rcpt: &receipts{}}
}

func (m *Mail) Send(subject, body string) (string, error) {
	payload := m.enc.encode(subject, body)
	m.tr.open()
	defer m.tr.close()

	ack, err := m.tr.write(payload)
	if err != nil {
		return "", fmt.Errorf("%w: %v", ErrMail, err)
	}
	return m.rcpt.record(ack), nil
}

func main() {
	m := NewMail()
	id, err := m.Send("hello", "first message")
	fmt.Println(id, err)
	_, err = m.Send("", "")
	fmt.Println("translated:", errors.Is(err, ErrMail))
	fmt.Println("leaked connections:", m.tr.openCount)
}
```

All three listings deliberately print the connection counter, because the
error-path resource leak of dimension 11 is the defect these examples exist to
demonstrate the absence of. The run status of each listing is recorded in the
verification note at the end of this entry rather than assumed.

## 18. References

1. Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides. *Design Patterns.
   Elements of Reusable Object-Oriented Software*. Addison-Wesley, 1994.
   ISBN 0-201-63361-2. Chapter 4, Structural Patterns, section Facade. Source of
   the pattern's intent, the Facade and subsystem-classes participants, and the
   placement among the structural patterns. Page numbers are not cited because I
   could not verify a specific pagination against an authoritative source on
   2026-08-02.
2. Wikipedia contributors. "Design Patterns".
   https://en.wikipedia.org/wiki/Design_Patterns
   Verified 2026-08-02. Used only to confirm that Facade sits in the structural
   group alongside Adapter, Bridge, Composite, Decorator, Flyweight and Proxy,
   and to confirm the book's authorship and year. Not used as a source of
   explanation.
3. Martin Fowler. *Patterns of Enterprise Application Architecture*.
   Addison-Wesley, 2003. Catalog entry for Remote Facade, chapter 15 per the
   online catalog page. https://martinfowler.com/eaaCatalog/remoteFacade.html
   Verified 2026-08-02. Source of the coarse-grained-facade definition used in
   dimensions 1 and 13.
4. Martin Fowler. *Patterns of Enterprise Application Architecture*.
   Addison-Wesley, 2003. Catalog entry for Service Layer, chapter 9 per the
   online catalog page. https://martinfowler.com/eaaCatalog/serviceLayer.html
   Verified 2026-08-02. Source of the Service Layer definition used in dimension
   13.
5. QOS.ch. *SLF4J user manual*. https://www.slf4j.org/manual.html
   Verified 2026-08-02. Source of the self-description as a simple facade or
   abstraction for various logging frameworks, and of the deployment-time
   plug-in claim used in dimensions 9 and 13.
6. Broadcom. *Spring Framework API documentation*,
   `org.springframework.jdbc.core.JdbcTemplate`.
   https://docs.spring.io/spring-framework/docs/current/javadoc-api/org/springframework/jdbc/core/JdbcTemplate.html
   Verified 2026-08-02. Source of the simplification claim and of the exception
   translation to the `org.springframework.dao` hierarchy used in dimensions 7
   and 9.
7. Kenneth Reitz and contributors. *Requests documentation*, release v2.34.2.
   https://requests.readthedocs.io/en/latest/
   Verified 2026-08-02. Source of the claim that Requests sends HTTP/1.1
   requests without manual query-string or form encoding, and that connection
   pooling comes from urllib3, used in dimension 9.
8. Rust project. *Rust standard library documentation*, `std::fs::read_to_string`.
   https://doc.rust-lang.org/std/fs/fn.read_to_string.html
   Verified 2026-08-02. Source of the convenience-function description used in
   dimensions 8 and 9.
9. Django Software Foundation. *Django 5.2 documentation*, "Built-in shortcut
   functions", `django.shortcuts.render`.
   https://docs.djangoproject.com/en/5.2/topics/http/shortcuts/
   Verified 2026-08-02. Source of the `render` description and of the long-form
   equivalent shown beside it, used in dimensions 1 and 9.
10. Martin Fowler. *Refactoring. Improving the Design of Existing Code*, 2nd
    edition. Addison-Wesley, 2018. ISBN 978-0-13-475759-9. Named refactorings
    Extract Function, Move Function, Extract Class and Inline Function,
    referenced by name in dimension 14. Page numbers are not cited because I did
    not verify a pagination for this edition on 2026-08-02.
11. Eric Evans. *Domain-Driven Design. Tackling Complexity in the Heart of
    Software*. Addison-Wesley, 2003. ISBN 0-321-12521-5. Source of the
    Anti-Corruption Layer concept referenced in dimensions 1 and 13. Page
    numbers are not cited for the same reason.

## Verification note on the code listings

Recorded after running the listings rather than asserted from reading them. See
the report at the end of the authoring session for the exact commands and
outputs.
