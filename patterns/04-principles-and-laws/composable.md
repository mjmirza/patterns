---
name: Composable
slug: composable
family: 04-principles-and-laws
category: Design Principle
aliases: [Composability, Compositionality, Plug Compatibility, Orthogonality of Interface]
first_described: "M. D. McIlroy 1968, formalized as a software design goal in M. D. McIlroy, E. N. Pinson, B. A. Tague, Unix Time-Sharing System Foreword, Bell System Technical Journal, 1978"
maturity: canonical
related: [composition-over-inheritance, single-responsibility-principle, interface-segregation-principle, pipe-and-filter, decorator, strategy, microservices, low-coupling, high-cohesion]
incompatible_with: []
verified: 2026-08-02
---

# Composable

## 1. Name, aliases, and lineage

The canonical name in software engineering is Composable, or the property of
Composability. It names a quality a unit of software can have, not a single
concrete construction technique, which is why it sits in the principles family
rather than the pattern catalogs. A composable unit can be combined with other
units that share its interface contract to build a larger behavior, without
either unit being modified for the combination to work.

The idea has a documented double origin. Douglas McIlroy, then head of the
Computing Techniques Research Department at Bell Labs and the inventor of the
Unix pipe, is credited with the earliest widely cited software formulation.
Peter Salus records McIlroy summarizing the Unix design philosophy as, in
substance, write programs that do one thing well, write programs to work
together, write programs to handle text streams because that is a universal
interface (M. D. McIlroy, quoted and dated to 1978 in Peter H. Salus, *A
Quarter Century of UNIX*, Addison-Wesley, 1994, and corroborated in the
official Unix Time-Sharing System Foreword, M. D. McIlroy, E. N. Pinson, B. A.
Tague, *Bell System Technical Journal*, vol. 57, no. 6, 1978,
[https://en.wikipedia.org/wiki/Unix_philosophy](https://en.wikipedia.org/wiki/Unix_philosophy),
verified 2026-08-02). This is the systems-level lineage. text streams,
processes, and the shell pipe operator as the composition mechanism.

The mathematical lineage is older and separate. Function composition, the
notion that two functions `f` and `g` combine into a third function `g . f`,
is a standard construction in category theory and predates computing by
decades, formalized in the categorical sense by Samuel Eilenberg and Saunders
Mac Lane, *General Theory of Natural Equivalences*, Transactions of the
American Mathematical Society, vol. 58, 1945. Software composability borrows
this vocabulary directly. a composable function, module, or component is one
whose output type matches the next unit's input type closely enough that they
chain without an adapter.

A third, narrower usage appears in component-based software engineering.
George T. Heineman and William T. Councill, *Component-Based Software
Engineering. Putting the Pieces Together*, Addison-Wesley, 2001, chapter 1,
define a software component as a unit of composition with contractually
specified interfaces and explicit context dependencies only, and define
composability as the property that lets independently developed components be
assembled into a system without source-level modification. This is the
platform-architecture reading of the term, and it is the reading that
underlies OSGi, COM, and later container orchestration.

This entry treats Composable as the umbrella principle, and treats
[Composition over Inheritance](composition-over-inheritance.md) as one
specific, narrower application of it inside object-oriented class design. The
two are frequently confused because they share a root word. Composition over
Inheritance answers the question has-a versus is-a inside a single class
hierarchy. Composable answers a broader question that has nothing to do with
classes at all. can this unit be combined with units it has never seen,
through a shared, minimal interface, without either side changing.

## 2. Problem and context

Every system with more than one moving part eventually needs behavior that no single unit
provides on its own. logging plus retry plus caching wrapped around a network
call, three independent validation rules applied to one form, five shell
tools chained into a data pipeline, four Kubernetes controllers reconciling
one desired state. The problem composability answers is how new combinations
of existing units get built without editing the units themselves and without
writing one bespoke integration for every pair.

The failure mode without composability is combinatorial glue code. If a
system has `n` units and every pairing of two units needs its own
hand-written adapter because interfaces do not line up, the number of
integration points grows toward `n` choose `2`, and every new unit added to
the system risks needing a new adapter against every existing one. This is
the same growth shape that motivated the Mediator pattern for object
communication, except here it shows up at the level of module boundaries,
service contracts, and command-line tool interfaces rather than object
references.

The context in which composability becomes the right lens, rather than an
abstract virtue, has three recognizable ingredients.

- There is a small, stable, and genuinely minimal interface that many
  different implementations can satisfy. a byte stream, a single-argument
  pure function, an HTTP request and response pair, a reconciler that reads
  and writes one resource kind.
- The system needs an open-ended, not-fully-known-in-advance set of
  combinations. new pipelines, new middleware chains, new deployment
  topologies, new report formats built from the same underlying steps.
- The cost of a wrong or premature abstraction is high enough that
  hand-crafted, N-squared glue is unacceptable, but the cost of an interface
  that is too large or too specific is also high, because a large interface
  is one that few implementations can satisfy without stub methods that do
  nothing, which quietly breaks composability while appearing to preserve it.

Outside that context, chasing composability produces exactly the kind of
overwrought, plugin-everything architecture the non-applicability list in
dimension 4 describes. a system with two fixed collaborators and no plausible
third does not need a composable interface between them, it needs a direct
call.

## 3. Forces

- **Coupling.** Favored, and this is the whole point. A composable unit
  couples to an interface, never to a concrete peer. Two units that satisfy
  the same interface can be swapped for each other with zero change at any
  call site that only depends on the interface.
- **Reuse.** Favored, strongly. The same filter, middleware, or handler can
  be dropped into a different pipeline unchanged, because it was written
  against the shared contract rather than against the specific pipeline it
  first shipped in.
- **Cognitive load, local.** Favored. A reader who understands one composable
  unit in isolation, its input, its output, its one job, does not need to
  read the rest of the pipeline to reason about that unit's correctness.
- **Cognitive load, global.** Sacrificed. A long chain of small, individually
  simple units can be harder to trace end to end than one larger function
  that does the same work in one place, because the behavior is now
  distributed across N call frames or N pipeline stages instead of one.
  Debugging a composed pipeline means reconstructing the whole chain in your
  head, or in a debugger, before you can see the actual data at any one
  point.
- **Interface design cost.** Sacrificed, and this is the force most catalogs
  underplay. Finding an interface narrow enough that many things satisfy it,
  yet expressive enough that the composition is not lossy, is genuinely hard
  design work, and getting it wrong either strands the composability (an
  interface too specific to be satisfied twice) or produces the widest,
  least useful interface, `Object` or `any`, which composes syntactically but
  not semantically.
- **Latency and throughput.** Sacrificed in the general case, favored in the
  specific case of streaming composition. A chain of N small functions each
  doing a full pass over its input, rather than one fused pass, costs N
  passes over the data and N allocation boundaries in a naive
  implementation. Unix pipes and reactive streams both exist specifically to
  claw this cost back by making the composition lazy and streaming rather
  than eager and building the whole result up front.
- **Testability.** Favored, sharply. A unit with a narrow, explicit interface
  and no hidden dependency on its neighbors is trivially testable in
  isolation, which is a direct consequence of the same property that makes
  it composable.
- **Versioning and evolution.** Sacrificed over the system's lifetime unless
  actively managed. The moment two independently evolving units are combined
  through a shared interface, that interface becomes a contract neither side
  can change unilaterally, which is precisely the coordination cost that
  motivates the microservice "your API is now a public API" discipline
  (see dimension 9).
- **Team topology.** Favored. Composable boundaries are the natural seam
  along which separate teams can own separate units, publish and consume
  each other's units through the interface alone, and release on independent
  schedules, which is the architectural argument Martin Fowler and James
  Lewis make for microservices as componentization via service rather than
  via library
  ([https://martinfowler.com/articles/microservices.html](https://martinfowler.com/articles/microservices.html),
  verified 2026-08-02).

No principle wins on every force at once, and composability's honest price is
paid in interface design effort up front and in start-to-finish traceability
at runtime.

## 4. Applicability and non-applicability

Reach for composability, and invest in a shared minimal interface, when the
following hold.

- The set of combinations that will be needed is genuinely open-ended and not
  known completely at design time. a data pipeline that will grow new stages,
  a middleware stack that will grow new cross-cutting concerns, a validation
  chain that will grow new rules.
- A small number of orthogonal operations recur across many different
  contexts. read bytes, write bytes, transform a value, guard a request,
  reconcile a resource.
- The interface can genuinely be made small. one method, one function
  signature, one message shape, without losing the information the caller
  needs. A composable interface that has grown to fifteen methods has
  stopped being composable and has become a god interface that only one
  implementation can genuinely satisfy, which is the interface-bloat failure
  covered directly by
  [Interface Segregation Principle](interface-segregation-principle.md).
- Independent teams, or an unknown future author, will supply new
  implementations of one side of the interface without coordinating with the
  author of the other side.
- The performance cost of the extra indirection or the extra pass over data
  is smaller than the cost of the N-squared glue code the alternative would
  produce, or the workload is I/O bound so the indirection is not on the
  critical path at all.

Do NOT reach for composability in these cases, and the reason matters more
than the rule.

- **There are exactly two collaborators and no plausible third.** Building a
  general composable interface for a fixed pairing is speculative generality
  wearing an architecture costume. A direct function call, or a direct
  import, is honest and deletes cleanly. This is the same argument against reaching for the pattern
  argument made for
  [Strategy](../01-design-patterns-gof/strategy.md) and
  [Factory Method](../01-design-patterns-gof/factory-method.md) when only one variant exists.
- **The operations genuinely depend on each other's internal state, and not
  only on their input and output.** If step two of a pipeline needs to know
  implementation details of step one, forcing them through a narrow
  interface hides that dependency instead of removing it, and the resulting
  system is coupled in fact while appearing decoupled on paper. This is the
  root cause covered in dimension 11.
- **The domain has a small, fixed, well-understood set of cases that will
  never grow.** A payment method with exactly three fixed types, reviewed
  and re-approved by compliance every time a fourth type is even proposed,
  does not benefit from an open composable plugin interface. a closed `enum`
  and a `switch` say what is true, and, per
  [Open Closed Principle](open-closed-principle.md), openness for extension
  is a cost you pay only when extension is actually expected.
- **The performance budget cannot absorb the indirection.** In a
  latency-critical inner loop, in an embedded system with a fixed memory
  budget, or in a hot path inside a database engine, the extra function call,
  virtual dispatch, or allocation boundary that a general composable
  interface introduces can be the dominant cost. Highly tuned code in this
  position is routinely and correctly monomorphic and non-composable by
  design, trading generality for a predictable, inlinable call graph.
- **The interface would need to be so wide that it stops constraining
  anything.** An interface with a dozen methods, most of which any given
  implementation stubs out with a no-op or a `NotImplementedError`, is not
  composable, it only looks composable. This is the exact anti-pattern this
  principle exists to prevent, and building one under the banner of
  composability is worse than not trying, because it advertises a promise
  the code does not keep.
- **Debuggability in production is the dominant concern and the team is
  small.** A five-stage composed pipeline distributed across five files, five
  test suites, and five deploy units is a genuine operational cost for a team
  of two, even though it would be the right call for a team of fifty. Scale
  the granularity of composition to the size of the team that owns it, per
  the reasoning in
  [https://martinfowler.com/bliki/MicroservicePremium.html](https://martinfowler.com/bliki/MicroservicePremium.html)
  (verified 2026-08-02), where Fowler names the fixed operational overhead a
  distributed, composed architecture pays regardless of scale.

## 5. Structure

Composability is a property of interfaces and the units that implement them,
not a fixed cast of named roles the way a GoF pattern has a Subject and an
Observer. The structural elements that recur across composable designs are
these.

- **The unit.** The smallest piece that does one job. a pure function, a
  middleware, an `io.Reader`, a Unix filter program, a Kubernetes controller,
  a microservice.
- **The interface, or protocol.** The minimal, explicit contract a unit must
  satisfy to participate. defined by an input type and output type for a
  function, a method set for an interface, a wire format for a service, a
  byte stream for a Unix program.
- **The composition operator.** The mechanism that takes two or more units
  satisfying the interface and produces a new unit that also satisfies it, or
  satisfies a related interface. function composition (`g . f`), the shell
  pipe (`|`), interface embedding, middleware chaining
  (`next => handler(next)`), or a reconciliation loop reading and writing
  shared state.
- **Closure of the operator, the property that makes recursion possible.**
  When the composition operator's output also satisfies the same interface
  its inputs did, compositions can nest arbitrarily. this is precisely why
  `Reader` composed with `Reader` yields something that is still a `Reader`,
  and why a `middleware(middleware(handler))` chain is itself indistinguishable
  from a single handler to its caller.
- **The consumer, or driver.** The code that assembles a concrete chain of
  units at a composition root, usually the only place in the system that
  knows the full, concrete list of what is combined. everywhere else in the
  system deals only with the interface.

## 6. ASCII structure diagram

```text
                   +--------------------------+
                   |   shared interface I     |
                   |  (one input shape,       |
                   |   one output shape)      |
                   +------------+-------------+
                                |
              satisfies         |         satisfies
        +----------+------------+------------+----------+
        |          |            |            |          |
   +----v---+  +---v----+  +----v---+   +----v---+  +---v----+
   | Unit A |  | Unit B |  | Unit C |   | Unit D |  | Unit E |
   | (log)  |  | (auth) |  | (cache)|   |(retry) |  |(handler)|
   +----+---+  +---+----+  +---+----+   +---+----+  +---+----+
        |          |            |            |          |
        +----------+---- composition operator +---------+
                                |
                     +----------v-----------+
                     |  composed pipeline    |
                     |  ALSO satisfies I,     |
                     |  so it can compose     |
                     |  again with F, G, ...  |
                     +------------------------+
```

## 7. Dynamics

The runtime behavior of a composable chain follows the same shape regardless
of whether the units are functions, middlewares, or Unix processes. build the
chain once at a composition root, then drive a single value or stream through
every unit in order.

```text
Assembly time (once, at the composition root):

  driver: chain = compose(A, B, C, D)
              A.output type == B.input type
              B.output type == C.input type
              C.output type == D.input type
          -> a single callable "chain" object, itself satisfying I

Runtime, per request or per input value:

  caller -> chain(input)
              |
              v
            A(input) -----> a1
                              |
                              v
                            B(a1) -----> b1
                                          |
                                          v
                                        C(b1) -----> c1
                                                      |
                                                      v
                                                    D(c1) -----> output
              |
              v
  caller <- output

Streaming variant (Unix pipes, reactive streams):

  producer --stream--> A --stream--> B --stream--> C --> consumer
      each stage starts consuming before the previous stage finishes
      producing, so memory stays bounded by one stage's buffer, not by
      the whole dataset
```

The two dynamics differ in one operationally important way. the eager
in-memory chain (a plain function pipeline) builds the full output of
each stage before the next stage starts, which is simple to reason about but
costs memory proportional to the largest intermediate value. the streaming
chain (Unix pipes, `io.Reader` chains, reactive `Observable` pipelines)
interleaves production and consumption stage by stage, which is what lets
`grep pattern huge.log | sort | uniq -c` process a multi-gigabyte file in
bounded memory, because each stage only ever holds a small window of the
stream at a time.

## 8. Implementation variants

- **Function composition.** The purest form. two functions `f: A -> B` and
  `g: B -> C` compose into `h: A -> C` where `h(x) = g(f(x))`. Idiomatic in
  every language with first-class functions, and the direct software
  descendant of the categorical composition operator from dimension 1.
- **The Unix pipeline.** Processes, not functions, are the composable unit,
  and `stdout` piped to `stdin` is the composition operator. Every program in
  the pipeline satisfies exactly one interface, read bytes from `stdin`,
  write bytes to `stdout`, which is precisely McIlroy's "handle text streams,
  because that is a universal interface"
  ([https://en.wikipedia.org/wiki/Unix_philosophy](https://en.wikipedia.org/wiki/Unix_philosophy),
  verified 2026-08-02).
- **Interface embedding, Go.** Small, single-method interfaces (`io.Reader`,
  `io.Writer`, `io.Closer`) combine by embedding into wider interfaces
  (`io.ReadWriteCloser`) that any type satisfying all the embedded methods
  automatically satisfies. Effective Go describes the resulting type as a
  union of the embedded interfaces, able to do what each embedded interface
  can do
  ([https://go.dev/doc/effective_go#interfaces_and_types](https://go.dev/doc/effective_go#interfaces_and_types),
  verified 2026-08-02).
- **Middleware, or the decorator chain applied to request handling.** A
  middleware has the shape `(next Handler) -> Handler`, so composing N
  middlewares around a base handler is repeated function application, and the
  result is itself a `Handler`, closing the loop from dimension 5. This
  variant is the workhorse of Express, Koa, ASP.NET Core, and Go's
  `net/http`.
- **Trait or typeclass composition.** In Rust, a function can be generic over
  any type implementing multiple trait bounds (`fn f<T: Read + Write>(x: T)`),
  which composes capabilities at the type level with zero runtime cost,
  because the compiler monomorphizes each call site. This resolves the
  latency force from dimension 3 in the language's favor, at the cost of
  larger compiled binaries from monomorphization.
- **Higher-order component and hook composition, React.** React explicitly
  frames component reuse as composition, not inheritance. containment, where
  a generic component accepts arbitrary children through the `children` prop,
  and specialization, where a specific component renders and configures a
  more generic one, are the two named variants
  ([https://legacy.reactjs.org/docs/composition-vs-inheritance.html](https://legacy.reactjs.org/docs/composition-vs-inheritance.html),
  verified 2026-08-02).
- **Service composition, microservices and reconciliation controllers.** The
  unit is a whole running process communicating over a network protocol, and
  composition is orchestration or choreography rather than an in-process
  call. Martin Fowler and James Lewis describe the preferred style as "smart
  endpoints and dumb pipes", each service owning its domain logic and
  services being "choreographed using simple RESTish protocols rather than
  complex protocols such as WS-Choreography or BPEL"
  ([https://martinfowler.com/articles/microservices.html](https://martinfowler.com/articles/microservices.html),
  verified 2026-08-02). Kubernetes controllers apply the same idea to cluster
  state, where each controller reconciles one narrow slice of desired state
  toward observed state independently, and the composed behavior of the
  cluster emerges from many small, independently reasoned reconciliation
  loops running against a shared declarative object model
  ([https://kubernetes.io/docs/concepts/overview/working-with-objects/kubernetes-objects/](https://kubernetes.io/docs/concepts/overview/working-with-objects/kubernetes-objects/),
  verified 2026-08-02).
- **Algebraic composition via a monoid or semigroup.** When a type has an
  associative combining operation and an identity element, values of that
  type compose in any grouping and in bulk, via a fold or reduce, without
  special-casing the empty or single-element case. This is the shape behind
  `functools.reduce` chains in Python and `Array.prototype.reduce` pipelines
  in JavaScript, and it is the mathematically strongest form of composability
  because associativity guarantees the result never depends on how the chain
  was parenthesized or batched.

## 9. Known production uses

- **The Unix and POSIX shell pipeline** is the founding, and still the most
  widely taught, production instance of software composability, with the
  pipe operator `|` connecting the standard output of one process to the
  standard input of the next, formalized in the Unix Time-Sharing System
  Foreword (M. D. McIlroy, E. N. Pinson, B. A. Tague, *Bell System Technical
  Journal*, vol. 57, no. 6, 1978) and codified in the POSIX shell command
  language specification.
- **Go's `io` package**, `io.Reader`, `io.Writer`, `io.Closer`, and their
  composed forms `io.ReadWriter` and `io.ReadWriteCloser`, is the standard
  library's own worked example of small-interface composability, documented
  directly in Effective Go's discussion of interface embedding
  ([https://go.dev/doc/effective_go#interfaces_and_types](https://go.dev/doc/effective_go#interfaces_and_types),
  verified 2026-08-02).
- **Express and Koa middleware stacks**, and their descendants in ASP.NET
  Core, ship request handling as a chain of `(next) -> handler` middlewares
  composed at application startup, the production incarnation of the
  middleware variant in dimension 8.
- **Kubernetes' controller architecture**, where independently written and
  independently deployed controllers, the Deployment controller, the
  ReplicaSet controller, custom operators, each reconcile one object kind
  toward its declared `spec`, and the cluster's overall behavior is the
  composed effect of every controller's reconciliation loop running against
  the shared object store, as described in the Kubernetes objects concept
  documentation
  ([https://kubernetes.io/docs/concepts/overview/working-with-objects/kubernetes-objects/](https://kubernetes.io/docs/concepts/overview/working-with-objects/kubernetes-objects/),
  verified 2026-08-02).
- **The npm package registry**, and specifically the widely cited
  `left-pad` incident of March 2016, is production evidence of both the
  benefit and the systemic risk of composability at package scale. an
  eleven-line, single purpose module had been downloaded roughly 2.5 million
  times in the month before it was unpublished, and thousands of projects,
  including build tooling for Babel, failed simultaneously when that one
  composable unit disappeared from the dependency graph, until npm's
  maintainers took the unprecedented step of restoring the package by force
  ([https://www.theregister.com/2016/03/23/npm_left_pad_chaos/](https://www.theregister.com/2016/03/23/npm_left_pad_chaos/),
  verified 2026-08-02).

## 10. Consequences

Positive.

- New behavior is assembled from existing, already-tested units rather than
  written from scratch, which is the direct payoff of reuse being favored in
  dimension 3.
- Each unit is independently testable, because its contract is fully
  specified by its interface and does not depend on which other units it
  will eventually be combined with.
- The system can grow the set of available combinations without touching
  existing units, satisfying the spirit of
  [Open Closed Principle](open-closed-principle.md) at the level of whole
  pipelines rather than single classes.
- Independent teams, or independent third-party authors, can supply new
  implementations of one side of a stable interface without coordinating
  with the owners of the composition itself, which is the structural basis
  for plugin architectures, package registries, and microservice
  organizations.
- A well-chosen composable interface tends to concentrate genuine domain
  complexity into a small number of well-tested combinators, `map`, `filter`,
  `reduce`, `pipe`, rather than letting it leak into every call site that
  needs the behavior.

Negative.

- Tracing a bug through a long composed chain costs a reader every stage's
  worth of mental context, because the failure surface is now the entire
  chain, not one function, and the actual data at any intermediate point is
  frequently invisible without adding explicit logging or a debugger
  breakpoint per stage.
- Finding the right interface is genuinely hard design work with a real
  chance of being wrong, and an interface that is too specific silently fails
  to compose with the next thing that shows up, while an interface that is
  too general composes with everything but constrains nothing and stops
  catching real errors at compile time or at the type-check boundary.
- A composed system distributed across many small units pays a fixed
  operational overhead, deploy pipelines, registry lookups, network hops,
  serialization boundaries, regardless of whether the workload is large
  enough to need the resulting scalability, a cost Martin Fowler names
  directly as the "microservice premium"
  ([https://martinfowler.com/bliki/MicroservicePremium.html](https://martinfowler.com/bliki/MicroservicePremium.html),
  verified 2026-08-02).
- Composability at package-registry scale creates a supply-chain dependency
  risk. a system built from many small, independently maintained composable
  units inherits every one of those units' maintenance status, licensing
  terms, and failure modes, which the `left-pad` incident demonstrates
  concretely (dimension 9).
- Performance is rarely free. eager, in-memory composition builds an
  intermediate value per stage, and even the streaming variants pay a
  per-stage overhead, buffer management, context switches between processes,
  serialization at a network boundary, that a single fused implementation
  would not pay.

## 11. Failure modes and misuse

- **Symptom.** Two units both claim to satisfy the shared interface, are
  wired together, and the composed pipeline produces wrong output silently,
  with no error anywhere.
  **Cause.** The interface specified only the syntactic shape, the method
  signature or the function type, and never specified the semantic contract,
  units, ordering, idempotency, error handling behavior. A cache middleware
  and an authentication middleware can both satisfy `(next) -> Handler`
  while disagreeing about whether the request body has already been
  consumed by the time the next stage runs.
  **Fix.** Document, and where the language allows it encode, the full
  contract, not only the type signature. pre and post conditions, whether
  the unit is idempotent, whether it may be retried, whether it consumes a
  stream exactly once. This is the same lesson Bertrand Meyer's
  Design by Contract applies to individual methods, applied here to the
  seams between composed units.

- **Symptom.** Adding a new stage to an existing pipeline breaks an earlier
  stage that was working correctly before, and the breakage is intermittent
  or order-dependent.
  **Cause.** The units were never truly independent, one relied on a side
  effect, a shared mutable global, an ordering assumption about a
  connection pool, that the composed interface never captured, so the
  composition was coupled in fact while looking decoupled on paper. This is
  the exact scenario the non-applicability list in dimension 4 warns about,
  units that depend on each other's internal state rather than only on
  their declared input and output.
  **Fix.** Make every dependency explicit in the interface, pass state
  through the contract rather than through a shared variable, and prefer
  pure functions or explicitly scoped state over ambient global state
  wherever the composition operator allows it.

- **Symptom.** The interface has grown wide enough that most implementations
  only genuinely implement two or three of its dozen methods, and the rest
  throw, return a default, or silently do nothing.
  **Cause.** Interface bloat, driven by adding one more method every time a
  new use case needed slightly more from the contract, instead of splitting
  the interface. This is a direct and observable violation of
  [Interface Segregation Principle](interface-segregation-principle.md), and
  it defeats composability rather than serving it, because fewer real-world
  units can genuinely satisfy a wide interface.
  **Fix.** Split the interface along the seams the different consumers
  actually use, and let a concrete type satisfy several small interfaces
  instead of one large one, mirroring the way Go's `io` package composes
  `ReadWriter` from `Reader` plus `Writer` rather than defining one
  monolithic `Stream` interface from the start.

- **Symptom.** A composed pipeline runs correctly in a small test but times
  out or exhausts memory once real production volume flows through it.
  **Cause.** The composition was built eagerly, building the full
  intermediate output of every stage, instead of streaming, so memory use
  scales with the size of the largest single value in flight rather than
  with the size of one stage's buffer.
  **Fix.** Switch to a streaming composition where the language and
  workload allow it, `io.Reader` chains in Go, generator or async-iterator
  chains in Python and JavaScript, or genuine Unix-pipe-style processes,
  so each stage begins consuming before the previous stage finishes
  producing.

- **Symptom.** One core dependency, small, single-purpose, and widely
  reused, is removed, deprecated, or changes its behavior, and a large,
  seemingly unrelated set of downstream systems breaks at once.
  **Cause.** Deep, silent composability at package-registry scale means the
  interface was never versioned or contractually stabilized, so downstream
  consumers had no signal that they were relying on a specific behavior of a
  transitive dependency they never directly chose. This is precisely the
  `left-pad` failure mode from dimension 9, and it recurs whenever
  composability is treated as free rather than as a contract that must be
  actively maintained.
  **Fix.** Version composable interfaces explicitly, pin dependency
  versions in production, and treat a widely reused composable unit's public
  contract with the same discipline a public API receives, because past a certain size
  it effectively is one.

## 12. Trade-off matrix

| Force | Composable pipeline | Monolithic single function | Composition over Inheritance | Microservices |
|---|---|---|---|---|
| Coupling | Lowest, coupled only to a shared interface | Highest, all logic in one place, coupled to itself only | Moderate, coupled to peer objects held by reference | Lowest across process boundaries, network contract only |
| Reuse of a single step | High, any unit satisfying the interface reuses everywhere | None, logic is not extractable without a rewrite | High within the object graph, low outside it | High across teams and languages |
| End to end traceability | Lower, failure surface spans every stage | Highest, one call frame to read | Moderate, one object graph to trace | Lowest, spans network hops and processes |
| Interface design cost | High, must find a genuinely narrow, stable contract | None, no interface to design | Moderate, scoped to the object's own collaborators | Highest, contract is now a distributed system boundary |
| Runtime overhead | Low to moderate, extra calls or streaming buffers | Lowest, no indirection | Low, one extra indirection layer per delegate | Highest, network serialization and latency per hop |
| Fit for open ended extension | Best fit, new units plug in without touching others | Worst fit, every new case edits the function | Good fit within one hierarchy of related objects | Best fit across organizational and deploy boundaries |
| Team scaling | Scales well once the interface is stable | Does not scale past one owner without conflict | Scales within one team owning the object model | Scales best across many independent teams |

## 13. Related and incompatible patterns

- **[Composition over Inheritance](composition-over-inheritance.md).** The
  narrower, object-oriented instance of this principle, scoped to a single
  class hierarchy choosing has-a delegation over is-a subclassing.
  Composable is the general principle. Composition over Inheritance is one
  concrete decision that follows from it inside OOP class design.
- **[Single Responsibility Principle](single-responsibility-principle.md).**
  A prerequisite, not a peer. a unit that has more than one reason to change
  is a poor composable unit, because its interface necessarily entangles
  multiple concerns that a composition operator cannot cleanly separate
  again.
- **[Interface Segregation Principle](interface-segregation-principle.md).**
  The direct guardrail against the interface-bloat failure mode in
  dimension 11. keeping interfaces small is what keeps them genuinely
  composable rather than merely labeled as such.
- **Pipe and Filter (architectural pattern).** The direct architectural
  expression of streaming composability, where filters are the composable
  units and pipes are the composition operator, most visible in Unix
  pipelines and in stream-processing frameworks.
- **[Decorator](../01-design-patterns-gof/decorator.md).** A special case of composability
  where every unit satisfies the same interface as the thing it wraps, which
  is precisely why decorators can nest arbitrarily. the middleware chain in
  dimension 8 is Decorator applied to request handlers.
- **[Strategy](../01-design-patterns-gof/strategy.md).** Composable at a single seam rather
  than across a chain. Strategy swaps one interchangeable algorithm into one
  fixed slot, while composability more generally chains or combines several
  interchangeable units into a pipeline.
- **Microservices architecture.** Composability applied at the process and
  network boundary rather than the in-language function or object boundary,
  carrying the same benefits and, per dimension 10, the same operational
  premium at a larger scale.
- **Incompatible in practice, not in theory, with tight coupling to a
  concrete implementation.** Any design where a caller depends on a
  concrete type's specific fields or private behavior, rather than on a
  shared interface, actively resists composability, because the caller can
  no longer be satisfied by a different implementation of the same contract.
  This is not a named pattern so much as the absence of the discipline this
  principle asks for.

## 14. Refactoring path in and out

Introducing composability into code that does not yet have it, step by step.

1. Identify the recurring operation that currently exists as several
   near-duplicate, hand-written variants scattered across the codebase, the
   classic signal being three or more call sites that do almost the same
   thing with small variations.
2. Extract the varying part into its own function, object, or process
   boundary, and name the fixed part around it. this is the same first move
   Martin Fowler documents as Extract Method, Refactoring, Improving the
   Design of Existing Code, 2nd edition, Addison-Wesley, 2018, chapter 6.
3. Define the narrowest interface that captures exactly what the fixed part
   needs from the varying part, resisting the urge to add a method the
   fixed part does not currently call, per
   [Interface Segregation Principle](interface-segregation-principle.md).
4. Rewrite the existing near-duplicate variants as separate implementations
   of that new interface, verifying each one against the tests the
   near-duplicate already had.
5. Replace the direct call at each original call site with a call through
   the interface, injecting the concrete implementation from the outside,
   which is Dependency Injection applied at the composition root.
6. Only once at least two real, independently varying implementations exist
   and are exercised in production, introduce an explicit composition
   operator, a `pipe`, a `compose`, a middleware chain builder, rather than
   inventing one speculatively for a single implementation, which would be
   the exact speculative-generality trap dimension 4 warns against.

Removing composability when it stops earning its place, step by step.

1. Confirm the interface genuinely has one, or at most two, real
   implementations left, and no credible near-term plan for a third. an
   interface kept around for years "in case it is needed" with a single implementer is a
   maintenance cost with no offsetting benefit.
2. Inline the single remaining implementation at each of its call sites,
   removing the interface and the composition operator together, which is
   the direct inverse of Fowler's Inline Method and Inline Class
   refactorings, Refactoring, 2nd edition, Addison-Wesley, 2018, chapters 6
   and 7.
3. Delete the now-unused interface type and any test doubles that existed
   solely to exercise the composition boundary.
4. Re-run the full test suite for the affected call sites to confirm
   behavior is unchanged, since this refactor should be behavior preserving
   by construction.

## 15. Testing and verification

Testing gets genuinely easier for the composable units themselves and
genuinely harder for the assembled chain as a whole, and both halves need
explicit attention.

- **Unit-level testing becomes close to trivial.** Because a well-formed
  composable unit's entire contract is its input and output types, a test
  supplies a value on one side and asserts the value on the other, with no
  need to stand up the rest of the pipeline, a database, or a network. This
  is the direct testability payoff named in dimension 3.
- **Contract tests replace integration tests at each seam.** Rather than
  testing the full assembled chain for every combination, write one
  property-based or table-driven test per interface asserting every
  implementation obeys the semantic contract from dimension 11, not only the
  type signature, idempotency, error propagation, resource cleanup on
  failure.
- **Test the composition operator itself in isolation.** `compose`, `pipe`,
  or a middleware chain builder is code with its own edge cases, an empty
  list of units, a single unit, a unit that throws partway through, and
  deserves direct tests independent of any specific pipeline built with it.
- **Golden-path plus fault-injection tests at the assembled level.** Because
  start-to-finish traceability is the force sacrificed in dimension 3, the
  assembled pipeline needs its own smaller set of tests that exercise the
  full chain with a representative input, and separately, inject a failure
  at each stage to confirm the failure propagates or is handled the way the
  contract promises rather than being silently swallowed.
- **Test doubles at the interface, not at the concrete unit.** A fake, a
  stub, or a mock built against the shared interface can stand in for any
  real unit in a composed chain, which is exactly the technique Gerard
  Meszaros catalogs as a Test Double in
  *xUnit Test Patterns. Refactoring Test Code*, Addison-Wesley, 2007, and it
  is only available at all because the interface is narrow enough to fake
  convincingly.
- **Watch for over-mocking, the composable-testing trap.** A test suite that
  mocks every unit in a chain to test the chain itself risks testing the
  wiring rather than the behavior, and a change to real behavior can pass a
  suite of mock-heavy tests while breaking production. Balance unit-level
  tests against real implementations with a small number of full-chain tests
  using real, not mocked, units wherever the cost of doing so is
  acceptable.

## 16. Observability signals

A healthy composed pipeline is legible stage by stage in telemetry, because
the alternative, a single opaque black box, forfeits the traceability the
architecture already sacrifices per dimension 3.

- **Per-stage timing.** Instrument each unit in the chain with its own span
  or timer, not only the chain's total latency, so a regression in one
  stage is visible without bisecting the whole pipeline by hand. In a
  distributed trace this is the standard parent-and-child span shape every
  major tracing system, OpenTelemetry among them, is built around.
- **Per-stage input and output counts.** For streaming or batch
  pipelines, log or metric the count of items entering and leaving each
  stage, because a stage that silently drops or duplicates items is one of
  the most common composable-pipeline defects and is invisible from total
  total latency alone.
- **Stage identity on every log line.** Every log emitted from within a
  composed unit should carry which unit emitted it, by name or by stage
  index, and ideally a correlation identifier that threads through the
  whole chain, otherwise a log stream from a five-stage pipeline reads as
  an unattributed jumble.
- **Contract violation counters.** A metric incremented whenever a unit
  receives an input outside its documented contract, a nil where a value
  was promised, a negative count, an empty stream where one item was
  required, surfaces the semantic-contract failures from dimension 11
  before they become silent wrong answers.
- **Composition-root health.** Because the composition root is the one place
  that knows the full concrete chain, its own startup logs should assert
  and record exactly which concrete units were wired together and in what
  order, so a production incident review can answer "what was actually
  running" without reading source code from that deploy.
- **A healthy dashboard** shows roughly flat per-stage latency across
  deploys, matching input and output counts at every stage boundary, and a
  contract-violation counter sitting at or near zero. **An unhealthy one**
  shows one stage's latency growing unbounded relative to its neighbors, a
  count mismatch between two adjacent stages, indicating silent drops or
  fan-out the design did not intend, or a rising contract-violation counter,
  indicating a new implementation of the shared interface that does not
  actually honor the semantic contract the other units assume.

## 17. Security and privacy implications

- **Untrusted composition of trusted parts.** The Unix pipeline and its
  descendants make it trivial to combine two individually safe programs into
  an unsafe combination, most classically a program that reads
  attacker-controlled input and passes it unsanitized to a second program
  that interprets it as a command, the same shell-injection risk that
  underlies OWASP's command injection guidance for any pipeline that builds
  a shell command from untrusted input rather than invoking a program
  directly with an argument vector.
- **Supply-chain trust is inherited transitively, and silently, at
  package-registry scale.** Composing a system out of hundreds of small,
  independently maintained composable units, packages, means the system's
  security posture, and its licensing posture, is the union of every one of
  those units' posture, including units several layers removed from any
  code the team actually reviewed. The `left-pad` incident (dimension 9) is
  an availability failure of this kind. a maliciously modified package with
  the same shape is a confidentiality or integrity failure of the same
  kind, and both stem from the same property, that composability lowers the
  cost of depending on code nobody on the team has read.
- **A narrow interface can leak more than it appears to.** A composable
  logging middleware that receives the full request object, rather than the
  specific fields it needs, can accidentally log an authorization header or
  a request body containing personal data, simply because the interface
  handed it more than its contract required. This is a direct argument for
  keeping the interface as narrow as the actual need, both for composability
  and for data minimization, per the purpose-limitation principle behind
  GDPR Article 5(1)(b) style data-minimization requirements.
- **Composed pipelines complicate audit trails.** When a request's handling
  is distributed across many independently deployed units, network
  boundaries, or reconciliation loops, proving after the fact exactly which
  code path handled a given piece of sensitive data requires the
  observability discipline from dimension 16 to already be in place, not
  reconstructed after an incident, because the composed structure itself
  offers no single point where the full history is naturally recorded.
- **Where this principle is silent.** Composability itself does not
  prescribe an authentication or authorization model, and does not by
  itself introduce a cryptographic weakness. the security implications
  above are consequences of how composable interfaces are usually used in
  practice, untrusted input flowing through many hands and many
  independently sourced units, rather than a property of function
  composition or interface embedding in the abstract.

## 18. References

- M. D. McIlroy, E. N. Pinson, B. A. Tague, Unix Time-Sharing System
  Foreword, *Bell System Technical Journal*, vol. 57, no. 6, 1978.
- Peter H. Salus, *A Quarter Century of UNIX*, Addison-Wesley, 1994.
- Unix philosophy, Wikipedia,
  [https://en.wikipedia.org/wiki/Unix_philosophy](https://en.wikipedia.org/wiki/Unix_philosophy),
  verified 2026-08-02.
- Samuel Eilenberg, Saunders Mac Lane, General Theory of Natural
  Equivalences, *Transactions of the American Mathematical Society*,
  vol. 58, 1945.
- George T. Heineman, William T. Councill, *Component-Based Software
  Engineering. Putting the Pieces Together*, Addison-Wesley, 2001, chapter 1.
- Effective Go, interfaces and other types,
  [https://go.dev/doc/effective_go#interfaces_and_types](https://go.dev/doc/effective_go#interfaces_and_types),
  verified 2026-08-02.
- Composition vs Inheritance, React documentation (legacy),
  [https://legacy.reactjs.org/docs/composition-vs-inheritance.html](https://legacy.reactjs.org/docs/composition-vs-inheritance.html),
  verified 2026-08-02.
- Martin Fowler, James Lewis, Microservices,
  [https://martinfowler.com/articles/microservices.html](https://martinfowler.com/articles/microservices.html),
  verified 2026-08-02.
- Martin Fowler, MicroservicePremium,
  [https://martinfowler.com/bliki/MicroservicePremium.html](https://martinfowler.com/bliki/MicroservicePremium.html),
  verified 2026-08-02.
- Kubernetes objects, Kubernetes documentation,
  [https://kubernetes.io/docs/concepts/overview/working-with-objects/kubernetes-objects/](https://kubernetes.io/docs/concepts/overview/working-with-objects/kubernetes-objects/),
  verified 2026-08-02.
- The Register, npm left-pad breakage report, March 2016,
  [https://www.theregister.com/2016/03/23/npm_left_pad_chaos/](https://www.theregister.com/2016/03/23/npm_left_pad_chaos/),
  verified 2026-08-02.
- Martin Fowler, *Refactoring. Improving the Design of Existing Code*,
  2nd edition, Addison-Wesley, 2018, chapters 6 and 7.
- Gerard Meszaros, *xUnit Test Patterns. Refactoring Test Code*,
  Addison-Wesley, 2007.
- Robert C. Martin, Interface Segregation Principle, referenced via
  [Interface Segregation Principle](interface-segregation-principle.md) in
  this repository.

## Code examples

Three languages where composability is directly idiomatic to that
language's own tooling. Go, because interface embedding is a language
feature built explicitly for this. TypeScript, because function pipelines
and middleware chains are the dominant idiom across its server and UI
frameworks. Python, because `Protocol` based structural typing plus
`functools.reduce` give both structural and algebraic composition in one
language. C# and Kotlin are omitted here for space, not because the
principle does not apply, LINQ and Kotlin's extension-function pipelines are
close analogs to the TypeScript and Go examples respectively.

### Go

Compiled and run with `go run` on this machine. Demonstrates interface
embedding, `Reader` plus `Writer` composing into `ReadWriter`, and
middleware composition around `http.Handler`.

```go
package main

import (
	"fmt"
	"io"
	"net/http"
	"strings"
)

type ReadWriter interface {
	io.Reader
	io.Writer
}

type buf struct {
	*strings.Reader
	sink *strings.Builder
}

func (b *buf) Write(p []byte) (int, error) {
	return b.sink.Write(p)
}

func withLogging(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		fmt.Println("request", r.URL.Path)
		next.ServeHTTP(w, r)
	})
}

func withAuth(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Header.Get("X-Token") == "" {
			http.Error(w, "unauthorized", http.StatusUnauthorized)
			return
		}
		next.ServeHTTP(w, r)
	})
}

func main() {
	sink := &strings.Builder{}
	rw := &buf{Reader: strings.NewReader("hello"), sink: sink}
	var _ ReadWriter = rw
	data, _ := io.ReadAll(rw)
	fmt.Println("read", string(data))

	base := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("ok"))
	})
	composed := withLogging(withAuth(base))
	_ = composed
	fmt.Println("composed handler built")
}
```

Verified output.

```text
read hello
composed handler built
```

### TypeScript

Compiled with `tsc --strict` and run with `node` on this machine.
Demonstrates a pure-function pipeline and a middleware composition operator
with an explicit `next` continuation.

```typescript
type Fn<A, B> = (a: A) => B;

function pipeAll<T>(...fns: Array<Fn<T, T>>): Fn<T, T> {
  return (input: T) => fns.reduce((acc, fn) => fn(acc), input);
}

const trim: Fn<string, string> = (s) => s.trim();
const lower: Fn<string, string> = (s) => s.toLowerCase();
const slug: Fn<string, string> = (s) => s.replace(/\s+/g, "-");

const slugify = pipeAll(trim, lower, slug);

interface Middleware<Ctx> {
  (ctx: Ctx, next: () => void): void;
}

function composeMiddleware<Ctx>(
  middlewares: Array<Middleware<Ctx>>
): Middleware<Ctx> {
  return (ctx, next) => {
    let index = -1;
    function dispatch(i: number): void {
      if (i <= index) throw new Error("next() called multiple times");
      index = i;
      const mw = middlewares[i];
      if (!mw) return next();
      mw(ctx, () => dispatch(i + 1));
    }
    dispatch(0);
  };
}

const withLog: Middleware<{ path: string }> = (ctx, next) => {
  console.log("visiting", ctx.path);
  next();
};

const withAuth: Middleware<{ path: string; token?: string }> = (ctx, next) => {
  if (!ctx.token) {
    console.log("blocked, no token");
    return;
  }
  next();
};

const app = composeMiddleware([withLog, withAuth]);

console.log(slugify("  Hello   World  "));
app({ path: "/x", token: "abc" }, () => console.log("handler ran"));
app({ path: "/y" }, () => console.log("handler ran (should not print)"));
```

Verified output.

```text
hello-world
visiting /x
handler ran
visiting /y
blocked, no token
```

### Python

Run with `python3` on this machine. Demonstrates a `Protocol` based
structural interface for `ReadWritable`, algebraic composition of pure
functions with `functools.reduce`, and a decorator style middleware chain.

```python
from __future__ import annotations
import re
from functools import reduce
from typing import Callable, Protocol


def compose(*fns: Callable) -> Callable:
    return reduce(lambda f, g: lambda x: g(f(x)), fns)


trim = str.strip
lower = str.lower
slugify_words = lambda s: re.sub(r"\s+", "-", s)

slugify = compose(trim, lower, slugify_words)


class Readable(Protocol):
    def read(self, n: int = -1) -> bytes: ...


class Writable(Protocol):
    def write(self, data: bytes) -> int: ...


class ReadWritable(Readable, Writable, Protocol):
    pass


class MemoryChannel:
    def __init__(self) -> None:
        self._buf = bytearray()
        self._pos = 0

    def write(self, data: bytes) -> int:
        self._buf.extend(data)
        return len(data)

    def read(self, n: int = -1) -> bytes:
        chunk = bytes(self._buf[self._pos:])
        self._pos = len(self._buf)
        return chunk


def use_channel(ch: ReadWritable) -> None:
    ch.write(b"hi")
    print("read back", ch.read())


def with_logging(handler: Callable[[str], str]) -> Callable[[str], str]:
    def wrapped(path: str) -> str:
        print("visiting", path)
        return handler(path)
    return wrapped


def with_auth(handler: Callable[[str], str]) -> Callable[[str], str]:
    def wrapped(path: str) -> str:
        if path.startswith("/admin"):
            return "blocked"
        return handler(path)
    return wrapped


base_handler = lambda path: f"ok:{path}"
composed_handler = with_logging(with_auth(base_handler))

if __name__ == "__main__":
    print(slugify("  Hello   World  "))
    use_channel(MemoryChannel())
    print(composed_handler("/x"))
    print(composed_handler("/admin"))
```

Verified output.

```text
hello-world
read back b'hi'
visiting /x
ok:/x
visiting /admin
blocked
```
