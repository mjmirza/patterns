---
name: Improper Instantiation
slug: improper-instantiation
family: 18-anti-patterns
category: Anti-pattern
aliases: [Object Churn, Instantiation Abuse, Repeated Construction Anti-pattern]
first_described: "Practitioner literature, no single origin, terminology stabilized in performance-tuning and API-design guides through the 2000s and 2010s"
maturity: established
related: [singleton-abuse, flyweight, object-pool, dependency-injection, factory-method, abstract-factory, golden-hammer]
incompatible_with: [flyweight, object-pool]
verified: 2026-08-02
---

# Improper Instantiation

## 1. Name, aliases, and lineage

The canonical name used in this catalog is Improper Instantiation. Unlike the
patterns in the Gang of Four catalog, this anti-pattern has no single named
author and no single publication that coined the term. It is a convergent
observation, arrived at independently by API designers, garbage collector
authors and performance engineers once managed runtimes made object allocation
cheap enough to hide, but not cheap enough to be free.

The clearest single-sentence statement of the underlying mechanism, applied to
regular expression objects, comes from Microsoft's .NET documentation. "Defining
a regular expression involves tightly coupling the regular expression engine
with a regular expression pattern. That coupling process is expensive, whether
it involves instantiating a Regex object by passing its constructor a regular
expression pattern or calling a static method by passing it the regular
expression pattern and the string to be analyzed" (Microsoft, .NET documentation on regular expression performance, learn.microsoft.com, verified 2026-08-02).
The phrase "coupling process is expensive" names exactly the failure this entry
covers. An object whose construction does real, repeatable work is treated as
if construction were free, and that construction is re-run every time the
object is needed rather than once.

The name is used in several communities under different words, and each alias
points at a slightly different slice of the same failure.

- **Object Churn.** Used in garbage-collector and JVM performance writing to
  describe a high allocation rate of short-lived objects that forces frequent
  minor collections. The term describes the symptom, GC pressure, more than the
  cause, avoidable repeated construction, and the two are used almost
  interchangeably in practice.
- **Instantiation Abuse.** Seen in static-analysis rule catalogs (SonarQube-style
  rule descriptions, ESLint community rules, Android Lint) as the label for a
  linter finding. A constructor call sits inside a loop, a hot method, or a
  frequently invoked callback, where a cached or shared instance would do.
- **Repeated Construction Anti-pattern.** A more formal, less common phrasing
  used in a handful of academic and industrial performance-engineering papers
  to distinguish this failure from the closely related but distinct failure of
  creating too many distinct instances of stateful, shareable data. That
  related failure is the province of Flyweight and Object Pool as the
  corrective patterns.

This entry treats Improper Instantiation as the general anti-pattern, and
treats "God Object doing its own object management" or "no dependency
injection anywhere" as adjacent but separate failures covered by other entries
in this family (`golden-hammer`, `singleton-abuse`, `service-locator`). The
scope here is narrower and more mechanical. It is a specific, identifiable,
avoidable act of construction, repeated where it did not need to be, at a cost
the author did not account for.

## 2. Problem and context

A type in the codebase is expensive, or moderately expensive, or genuinely
expensive, to construct. The exact cost varies by what the constructor does.
Parsing a pattern into a matching automaton, opening a socket, acquiring a file
handle, reading and parsing a configuration file, computing a hash table of
static data, registering itself with a runtime subsystem, or simply allocating
enough memory that a garbage collector notices, all count. None of that cost is
visible at the call site. A constructor call, `new Foo(...)` or `Foo()` or
`Foo::new(...)`, looks identical whether `Foo` is a two-field value object with
a body that runs in nanoseconds, or a regular-expression engine, an HTTP client
with a connection pool, or a JDBC connection that opens a TCP socket and
performs a TLS handshake.

This uniformity of syntax is the entire root of the problem. Object-oriented
and functional languages alike were deliberately designed so that construction
reads the same regardless of cost, because that uniformity is what lets a
constructor be swapped for a different implementation without changing call
sites. The cost, however, is real and does not disappear because the syntax
hides it. A developer writing a loop, a request handler, a render method, or a
hot path inside a library sees `new Something(...)` and, absent specific
domain knowledge about `Something`, assumes it is cheap, because most
constructors in most languages are in fact cheap. The failure occurs precisely
when that assumption is wrong and nobody paid attention to the exception.

The context in which this becomes a real defect, not a matter of taste, has a
recognizable shape. A path in the program executes repeatedly. A request
handler invoked per HTTP request, a render or draw callback invoked per frame
or per list item, a loop body invoked per row of a result set, a hot function
called deep inside a library with no visibility into how often callers invoke
it, all qualify. Somewhere inside that repeatedly executed path, a constructor
for an object whose real cost is genuinely high is called anew each time, when the
constructed value, or an equivalent value, could have been built once outside
the repeated path and reused, shared, cached, or drawn from a pool.

The anti-pattern is not "using `new`". It is "using `new` inside a hot path for
a type whose construction cost is genuinely high and whose result did not need to
be freshly constructed on this particular execution." A one-off construction
of an expensive object, executed once at startup or once per user action, is
not this anti-pattern. It is normal, correct code. The defect is repetition
without benefit. The same work, or work with the same shape and the same
result, is redone every single time through a path that runs often.

Two closely related but distinct sub-problems fall under the same name because
they share the same root cause and the same fix, even though the observable
symptom differs.

- **Redundant work.** The constructed object does the same expensive
  computation every time (parsing the same regular expression pattern, opening
  a connection to the same host, reading the same configuration file), and the
  result would be identical, or effectively identical, on every call. This is
  pure waste. CPU or I/O is spent recomputing a value that has not changed.
- **Allocation pressure.** The constructed object is genuinely different each
  time in its data (a new small value object per iteration), but the sheer rate
  of allocation, deallocation and collection swamps a managed runtime's garbage
  collector, causing pause time, cache-line churn, or scheduling jitter that
  degrades throughput and tail latency even though no single allocation is
  individually expensive.

Both sub-problems are visible in this entry's known production uses (dimension
9). The .NET `Regex` and Java `Pattern` cases are redundant work, the same
pattern parsed over and over, and the Android rendering-loop case is
allocation pressure, many small, distinct objects allocated per frame,
overwhelming the collector even though each one is cheap in isolation.

## 3. Forces

Improper Instantiation is not a pattern balancing forces on purpose, it is a
failure to notice a real force. But naming the forces at play explains why the
mistake is so easy to make and so persistent once made.

- **Cognitive load versus performance visibility.** Sacrificed at the point of
  writing the code, in favor of readability. `new Foo(x)` is trivially readable
  and requires no knowledge of `Foo`'s internals. Making construction cost
  visible at the call site, an explicit `pool.acquire()`, a factory that
  returns a cached value, an injected dependency, is more legible about cost
  but demands the reader already know, or look up, why the indirection exists.
  This is the single dominant force. Uniform syntax for non-uniform cost is a
  deliberate language design trade-off, and this anti-pattern is the recurring
  bill for that trade-off coming due.
- **Latency and throughput.** The direct cost. Every redundant or excessive
  construction spends CPU cycles, and in the I/O-bound case (sockets, file
  handles, database connections) spends wall-clock time waiting on external
  systems, that a cached or shared instance would not spend.
- **Memory and garbage-collector health.** In managed runtimes (JVM, CLR,
  Android's ART, JavaScript engines, Go's runtime), excessive allocation raises
  the frequency and, in some collector designs, the pause duration of garbage
  collection cycles, competing for CPU with the application's own work. See the
  Android documentation cited in dimension 9 for a concrete quantified example.
- **Correctness and thread safety, sometimes accidentally protected.**
  Counterintuitively, one variant of this anti-pattern, constructing a new
  instance of a type each time it is used rather than sharing one across
  threads, can accidentally sidestep a thread-safety bug, because each thread
  gets its own private, mutable instance. Removing the redundant construction
  without checking whether the underlying type is safe to share across threads
  can trade a performance problem for a correctness problem. This is why the
  refactor documented in dimension 14 insists on checking documented thread
  safety before introducing sharing.
- **Coupling and testability.** Constructing a concrete dependency inline,
  `new PostgresConnection(...)` deep inside business logic, both causes
  repeated-construction waste and independently couples the caller to a
  concrete implementation, making the caller hard to test in isolation. The two
  problems, performance and testability, often travel together because the
  same code smell, a constructor call embedded where it should not be, causes
  both, but they are logically separable. A class can be improperly
  instantiated, repeatedly, wastefully, while still being perfectly injectable
  and mockable, and vice versa.
- **Premature caching risk.** Pulling too hard in the corrective direction
  introduces its own force. Over-eager caching or pooling of objects that are
  in fact cheap to build, or that carry per-call state that must not leak
  between calls, trades a performance problem nobody measured for a
  correctness or memory-leak problem that is much harder to find. The fix has
  to be evidence-driven, not reflexive.

## 4. Applicability and non-applicability

This anti-pattern is genuinely present, and worth fixing, when the following
hold together.

- The constructed type's initializer does measurable, genuinely costly work.
  Regular expression compilation, socket or file-handle acquisition, TLS
  handshake, parsing of a document or configuration source, computation over
  static or slowly changing data, or registration with a shared runtime
  subsystem all qualify.
- The construction happens inside a path that executes with real
  frequency. A request handler, a rendering or layout callback, a tight loop
  over a data set, a function called from many call sites whose aggregate call
  volume the author of the function cannot see from any single call site, all
  qualify.
- The value produced by construction is the same, or effectively the same,
  across the repeated calls, or the type is documented as safe to share
  (thread safety, immutability, or explicit pooling support), so hoisting or
  reusing the instance is actually correct, not merely faster.
- A profiler, allocation tracer, or garbage-collector log has shown, or would
  plausibly show, that this specific construction is a measurable contributor
  to the cost of the path, not merely a theoretical inefficiency.

Do not treat ordinary object construction as this anti-pattern under any of
the following conditions. Each is a real case where flagging it would be a
false positive and "fixing" it would make the code worse.

- **The constructed object is genuinely cheap.** A small value object, a
  struct, a plain data holder with two or three fields and no I/O, no parsing
  and no registration in its constructor, costs nanoseconds to allocate on a
  modern managed runtime. Hoisting such an object out of a loop for
  "performance" adds indirection and mutable shared state for a saving too
  small to measure. This is premature optimization, and it is a distinct
  anti-pattern from the one this entry describes, not an instance of it.
- **The object legitimately carries per-call, per-request or per-iteration
  state that must not be shared.** A `StringBuilder` accumulating one row's
  output, a per-request context object, a new small event record pushed onto a
  queue, are correctly constructed fresh every time, because sharing them
  would be a correctness bug, data from one call leaking into another, not a
  performance win. See dimension 11 for the specific failure mode of sharing an
  object that was never meant to be shared.
- **The type is explicitly documented as cheap by design, or as intentionally
  ephemeral.** Some frameworks deliberately design a type to be constructed
  fresh per use as part of the API contract, a builder object, a fluent query
  step, a short-lived DTO. Treating these as instances of this anti-pattern
  fights the framework's own design.
- **The path executes rarely.** A constructor call inside application startup
  code, a one-time migration script, a CLI tool invoked by a human once per
  session, or an admin action triggered a handful of times a day carries no
  real aggregate cost no matter how expensive the individual
  construction is. Frequency, not absolute per-call cost, is what turns
  construction cost into a defect.
- **The fix would require introducing shared mutable state into a type that
  is not documented as thread safe.** If the "cure" for repeated construction
  is to promote a mutable, non-thread-safe object to a shared field or
  singleton without also fixing its internal state management, the cure
  introduces a concurrency bug worse than the performance problem it solves.
  Non-applicability here is conditional. The anti-pattern is real, but the
  naive fix is not applicable until the type's thread safety is established or
  added.
- **Dependency injection or a factory already owns the lifecycle correctly.**
  A framework-managed singleton or scoped bean, see the Spring Framework
  example in dimension 9, that is constructed once by the container and
  injected everywhere it is needed is the corrected state, not the anti-pattern.
  Do not flag a well-scoped, container-managed bean as improperly instantiated
  merely because its class also has a public constructor. The presence of a
  constructor is not the defect, the frequency and location of its invocation
  is.

## 5. Structure

Because this is an anti-pattern rather than a design pattern, "structure" here
means the recognizable shape of the defective code and the roles played by
each part of it, rather than a set of cooperating classes meant to be built on
purpose.

- **Hot path.** The code region that executes repeatedly. An HTTP handler
  method, a `render`/`draw`/`onDraw` callback, a loop body, a hot function
  called from many places all qualify. This is where the improper construction
  lives. It is the frequency amplifier. A single line of wasteful code inside
  it is multiplied by however many times the path runs.
- **Expensive constructible.** The type whose constructor, factory function, or
  initializer performs genuinely costly work, parsing, I/O, computation over
  static data, registration. This is the object being mismanaged. It is
  usually a perfectly well-designed class in its own right, the defect is
  external to it, in how callers use it.
- **Construction call site.** The exact `new`, factory call, or literal
  initializer expression inside the hot path that creates a fresh instance
  each time. This is the point of failure, and the point a linter rule or a
  profiler flame graph will point to.
- **Missing hoisting point.** The scope, one level up from the hot path, a
  class field, a module-level constant, a container-managed singleton bean, a
  memoization cache, a connection pool, where the expensive constructible
  should have been created once and then referenced from the hot path. In the
  defective code, this scope is empty, in the corrected code it holds the
  single shared or pooled instance.
- **Consumer inside the hot path.** The code that uses the freshly
  constructed instance immediately after creating it, typically discarding it
  at the end of the iteration or call. In the corrected version, these
  consumers are unchanged, only the source of the instance moves.

## 6. ASCII structure diagram

```
Defective shape.

  +--------------------------------------------------------+
  |  Hot path (loop / request handler / render callback)   |
  |                                                         |
  |   for each iteration / call:                            |
  |     +-------------------------------------------+       |
  |     |  new ExpensiveConstructible(args)          |       |
  |     |  (parses / opens socket / allocates table) |       |
  |     +-------------------+-----------------------+        |
  |                         |                               |
  |                         v                               |
  |     +-------------------------------------------+       |
  |     |  consumer uses instance, then discards it  |       |
  |     +---------------------------------------------+     |
  +---------------------------------------------------------+
        repeated N times -> N times construction cost paid


Corrected shape.

  +---------------------------+
  |  Hoisting point           |
  |  (field / module const /  |
  |   DI container / pool)    |
  |                            |
  |  single ExpensiveConstr-  |
  |  uctible instance          |
  +-------------+--------------+
                |
                | reference, shared or borrowed
                v
  +--------------------------------------------------------+
  |  Hot path (loop / request handler / render callback)   |
  |                                                         |
  |   for each iteration / call:                            |
  |     +-------------------------------------------+       |
  |     |  use shared / pooled instance directly     |       |
  |     +---------------------------------------------+     |
  +---------------------------------------------------------+
        repeated N times -> construction cost paid once
```

## 7. Dynamics

The defective run-time behavior and the corrected run-time behavior differ only
in when construction happens relative to the loop, but the difference in
aggregate cost is proportional to the loop count. That is exactly why the
anti-pattern is invisible in a quick manual test, loop count one or two, and
severe in production, loop count in the thousands or millions per second.

```
Defective sequence, N calls to hot path.

  caller          hot path            expensive constructible
    |                 |                          |
    | call 1          |                          |
    |---------------->| new Expensive(...)       |
    |                 |------------------------->| (parse / open / alloc)
    |                 |<-------------------------| instance_1
    |                 | use instance_1            |
    |<----------------| result                    |
    |                 |                          |
    | call 2          |                          |
    |---------------->| new Expensive(...)       |
    |                 |------------------------->| (parse / open / alloc AGAIN)
    |                 |<-------------------------| instance_2
    |                 | use instance_2            |
    |<----------------| result                    |
    |                 |                          |
    ...  (repeated N times, N times construction cost paid)


Corrected sequence, N calls to hot path, one-time construction.

  caller          hot path            hoisting point       expensive constructible
    |                 |                     |                       |
    |  (startup)      |                     |                       |
    |                 |    new Expensive(...)                        |
    |                 |-------------------->|---------------------->| (parse / open / alloc, once)
    |                 |                     |<-----------------------| shared_instance
    |                 |                     |
    | call 1          |                     |
    |---------------->| use shared_instance |
    |<----------------| result              |
    |                 |
    | call 2          |
    |---------------->| use shared_instance |
    |<----------------| result              |
    ...  (repeated N times, construction cost paid exactly once)
```

The corrected sequence introduces one new concern absent from the defective
one. The hoisting point now holds mutable or reference state that outlives any
single call, so its lifecycle, who creates it, who owns disposing it, whether
it must be thread safe for concurrent callers, becomes part of the design in a
way it never was when every call got a private, throwaway instance. This is
the trade-off named in dimension 3 and elaborated in dimension 11.

## 8. Implementation variants

The corrective move is always some form of "construct once, use many times",
but the mechanism by which that is achieved varies by language, by whether the
shared value must be mutable, and by whether sharing must be safe across
concurrent callers.

- **Module-level constant or static field (single-threaded or read-only
  case).** The simplest fix. In Python, a compiled `re.Pattern` object or a
  configuration dictionary is built once at module import time and referenced
  from functions. In Go, a `regexp.MustCompile` call is placed as a package
  level `var` so it runs once at program initialization rather than on every
  function invocation. This variant requires that the value never needs to
  change per call and, if the runtime is multi-threaded, that concurrent reads
  of the finished value are safe, true for immutable values, false for a
  mutable cache updated after construction without synchronization.
- **Dependency injection with container-managed lifecycle.** A DI container
  (Spring, .NET's built-in DI, Dagger, Wire) is told the scope of a type,
  singleton (one instance for the application's lifetime), request or session
  scoped (one instance per unit of work), or prototype/transient (a fresh
  instance every time it is requested, which is the correct scope for
  genuinely cheap or per-call-state objects, see dimension 4). The container,
  not hand-written code, decides when construction happens, which turns an
  implicit, easy-to-miss decision into an explicit, reviewable configuration
  value. This is the variant used by the Spring Framework example cited in
  dimension 9.
- **Object pool.** For instances that are expensive to construct, safe to reuse
  after a reset, but not safe to hold as a single shared instance across
  concurrent users at once, a database connection, a byte buffer, a thread, an
  object pool hands out a borrowed instance and takes it back when the caller
  is done. This trades construction cost for pool-management cost, checkout,
  reset, checkin, and adds the operational burden of sizing the pool
  correctly. See the `object-pool` entry in this catalog for the full
  treatment. The connection-pooling production examples in dimension 9 are
  this variant applied to database connections.
- **Memoization or result cache.** Where the expensive part is not the object
  itself but a pure computation the object performs, parsing a template,
  computing a hash of static content, a memoization cache keyed on the input
  avoids reconstruction for repeated identical inputs while still allowing
  distinct inputs to produce distinct, freshly computed results. This is
  narrower than the previous two variants, it fixes redundant work but not
  allocation pressure from genuinely varying inputs.
- **Compile-once, reuse-many API shape, a framework-level fix.** Some standard
  libraries fix this anti-pattern at the API design level rather than leaving
  it to caller discipline. .NET's static `Regex.IsMatch` methods internally
  cache the last several compiled patterns so that even code which appears to
  reinstantiate a pattern on every call benefits from an internal cache.
  Microsoft's documentation states that by default the last fifteen most
  recently used static regular expression patterns are cached, and the cache
  size can be adjusted through `Regex.CacheSize` (Microsoft, .NET documentation
  on regular expression performance, verified 2026-08-02). This variant shows
  that the anti-pattern can sometimes be mitigated by the library rather than
  by every caller, though relying on an undocumented or adjustable internal
  cache is fragile compared to an explicit hoist.
- **Lazy-once-then-cache, a language-idiomatic form.** Kotlin's `by lazy {}`
  delegate, Swift's `lazy var`, and Rust's `std::sync::OnceLock` (or
  `once_cell::sync::Lazy`) each provide a language-level idiom for "construct
  exactly once, on first use, then reuse forever", which removes the need to
  hand-write a null check and a manual initialization guard, and in the Rust
  case does so with thread safety built into the primitive.

## 9. Known production uses

- **The Java `java.util.regex.Pattern` API.** The official Oracle Java SE 21
  API documentation for `Pattern` states, "Instances of this class are
  immutable and are safe for use by multiple concurrent threads. Instances of
  the Matcher class are not safe for such use", and separately recommends,
  regarding the convenience `matches` static method, "If a pattern is to be
  used multiple times, compiling it once and reusing it will be more efficient
  than invoking this method each time" (Oracle, `java.util.regex.Pattern`
  Javadoc, Java SE 21, docs.oracle.com, verified 2026-08-02). The entire API
  shape, a heavyweight, thread-safe, immutable `Pattern` object produced by
  `Pattern.compile`, separate from a lightweight, per-call, stateful `Matcher`
  produced by `pattern.matcher(input)`, exists specifically so that
  application code has an explicit, documented place to hoist the expensive
  part, compilation, out of a hot path while still creating a fresh matcher
  per input string. Code that calls `Pattern.compile(regex).matcher(input)`
  inside a loop, rather than compiling once outside the loop, is a textbook
  instance of this anti-pattern against an API that was explicitly designed to
  make the correct usage possible and the incorrect usage easy to write by
  accident.
- **Android rendering and layout passes.** Google's official Android developer
  documentation on rendering performance states, "It's fine to allocate in
  response to a rare event that doesn't happen many times per second, like a
  user tapping a button, but remember that each allocation comes with a cost.
  If it's in a tight loop that's called frequently, consider avoiding the
  allocation to lighten the load on the GC," and describes a measured 94
  millisecond garbage collection pause traced to allocation inside a
  frequently invoked code path (Google, "Reduce, reuse, recycle. Diagnosing
  render performance", developer.android.com/topic/performance/vitals/render,
  verified 2026-08-02). This is the canonical allocation-pressure sub-variant
  named in dimension 2. `onDraw`, `onBindViewHolder` and similar callbacks are
  invoked many times per second during a scroll or an animation, and
  constructing a new `Paint`, `Rect`, `Bitmap`, or formatted `String` inside
  one of those callbacks, instead of reusing a field allocated once, is a
  widely documented and specifically named cause of dropped frames on
  Android, serious enough that Android Lint ships a dedicated
  `DrawAllocation` check for exactly this call pattern inside `onDraw` and
  related methods.
- **Spring Framework bean scopes.** The official Spring Framework reference
  documentation distinguishes the default `singleton` scope, "Only one shared
  instance of a singleton bean is managed, and all requests for beans with an
  ID or IDs that match that bean definition result in that one specific bean
  instance being returned by the Spring container," from the `prototype`
  scope, "The non-singleton prototype scope of bean deployment results in the
  creation of a new bean instance every time a request for that specific bean
  is made," and gives the explicit rule of thumb, "As a rule, you should use
  the prototype scope for all stateful beans and the singleton scope for
  stateless beans" (Spring Framework reference documentation, "Bean Scopes",
  docs.spring.io, verified 2026-08-02). The entire concept of a bean scope in
  a dependency injection container exists to make the construction-frequency
  decision an explicit, per-type configuration choice rather than a fact
  buried in whichever code happens to call `new` first. Application code that
  bypasses the container and calls `new` directly on a class the container
  manages as a singleton reintroduces exactly this anti-pattern underneath a
  framework that was built to prevent it.
- **.NET's `Regex` class and the parallel `HttpClient` lesson.** Microsoft's
  official .NET documentation states plainly that constructing a `Regex`
  object is an expensive coupling operation and shows the corrected,
  idiomatic pattern of holding a compiled instance in a `static readonly`
  field rather than constructing one per call (Microsoft, .NET documentation on
  regular expression performance, learn.microsoft.com, verified 2026-08-02).
  The same document's example code demonstrates the equivalent, widely known
  .NET convention for `HttpClient`, declared as `static readonly HttpClient
  s_client = new();` and reused across every call rather than constructed per
  request, which reflects the broader, independently documented .NET
  guidance that repeatedly constructing and disposing `HttpClient` instances
  under load can exhaust available sockets. Both examples, in the same
  reference documentation, are the same anti-pattern, an expensive, reusable
  object constructed anew per call, applied to two different subsystems,
  regular expression engines and HTTP connections, and both are corrected
  with the same idiom, a `static readonly` field constructed once.

## 10. Consequences

### Positive consequences

Listed for honesty, not endorsement. Every one of these is a reason the
mistake is easy to make, not a reason to keep it.

- Locality. The object is constructed exactly where it is used, so a reader
  never has to trace where a shared instance came from, and the code has no
  hidden dependency on initialization order or on a field being populated
  before use.
- No shared mutable state to reason about. A freshly constructed instance
  every time trivially avoids any bug caused by one caller's use of the object
  leaking into another caller's use, because there is no sharing at all.
- Zero setup cost for the author. Writing `new Foo(...)` at the point of use
  requires no knowledge of `Foo`'s internal cost, no decision about scope or
  lifecycle, and no coordination with a DI container or a pool.

### Negative consequences

- Wasted CPU or I/O proportional to call frequency, which in a hot path can
  outweigh the total cost of the operation the path is meant to perform,
  turning an operation that should be I/O-bound or algorithm-bound into one
  that is largely spent on avoidable setup cost.
- Increased garbage collection frequency and, in some collector designs,
  pause duration, in managed runtimes, which degrades throughput and tail
  latency for the whole process, not merely for the code path doing the
  improper instantiation, because collection is typically a process-wide
  event.
- Resource exhaustion in the I/O-bound variant. Repeatedly opening sockets,
  file handles, or database connections without pooling can exhaust the
  operating system's file descriptor table or a remote server's connection
  limit under load, a failure mode invisible at low traffic and catastrophic
  at high traffic.
- Obscured intent. A reader cannot tell, from a bare `new Foo(...)` inside a
  loop, whether the author considered the cost and accepted it, or never
  thought about it at all, which makes the defect invisible to code review
  unless the reviewer independently knows the cost of constructing `Foo`.
- Delayed discovery. Because the per-call cost of a single improper
  instantiation is frequently below any threshold a developer notices during
  manual testing, one request, one loop iteration, one frame, the defect
  typically survives code review and manual QA and is discovered only under
  production load or during a dedicated performance investigation, which is
  the most expensive time to find and fix it.

## 11. Failure modes and misuse

This section presents each failure as an observable symptom, its underlying
cause, and the fix, because "the code does `new` in a loop" is too abstract to
recognize during an actual incident. The symptoms below are what an engineer
actually sees on a dashboard, in a profiler, or in a bug report.

- **Symptom.** API response latency degrades under load in a way that scales
  worse than linearly with request rate, and CPU profiling shows a large
  fraction of time inside a constructor, a `compile`, or a `parse` call that
  intuitively should not be a large fraction of anything.
  **Cause.** A per-request handler constructs an expensive object, a
  compiled regular expression, a JSON schema validator, a templating engine
  instance, a cryptographic key derivation, fresh on every request instead of
  once at startup or once per unique input.
  **Fix.** Hoist the construction to application startup, a module-level
  constant, or a DI container singleton scope, per the variants in dimension 8
  and the refactor in dimension 14.
- **Symptom.** Frame rate drops or visible jank occurs specifically during
  scrolling, animation, or list rendering on a mobile or desktop UI, and a
  memory profiler shows a sawtooth allocation pattern synchronized with each
  frame or each list item bound.
  **Cause.** A `draw`, `layout`, `render`, or `bind` callback allocates a new
  paint object, formatter, rectangle, color, or similarly small object on
  every invocation rather than reusing a field allocated once.
  **Fix.** Move the allocation to a class field initialized once, in a
  constructor or an `init` block, or lazily on first use, and reset or reuse
  the same instance across invocations. See the Android production example in
  dimension 9 and the corrected sequence in dimension 7.
- **Symptom.** The application intermittently fails with a resource-exhaustion
  error under sustained load, "too many open files", "connection refused",
  "connection pool exhausted", or a socket-related exception that does not
  reproduce at low traffic.
  **Cause.** Code opens a new database connection, file handle, or socket per
  operation instead of drawing from a pool, and under sustained load the
  operating system or the remote server's connection limit is exceeded before
  the previous connections are closed, or connections are closed slowly enough
  that the rate of new-connection creation outpaces the rate of cleanup.
  **Fix.** Introduce, or correctly configure, a connection or resource pool,
  see the object-pool variant in dimension 8, and confirm that connections
  are always returned to the pool, including on error paths, via a
  try-finally, a `using`/`with` block, or the language's equivalent
  deterministic cleanup construct.
- **Symptom.** A subtle data-corruption or cross-request data leak bug appears
  under concurrent load. One user occasionally sees data that belongs to a
  different user, or a value computed for one request appears in the response
  of a different, concurrent request.
  **Cause.** This is the inverse misuse. An engineer, aware of this
  anti-pattern in the abstract, "fixes" a genuinely expensive-looking
  construction by promoting it to a shared singleton or a static field
  without checking whether the underlying type is safe to share across
  concurrent requests. A per-request context object, a `SimpleDateFormat`-style
  mutable formatter, or any object that accumulates per-call state is
  correctly constructed fresh per call, sharing it introduces a race
  condition where concurrent callers mutate the same instance's internal
  state simultaneously. This is a well-known historical trap in Java, where
  `java.text.SimpleDateFormat` is documented as not thread safe, and caching a
  single shared instance to "fix" its construction cost is a frequently
  repeated mistake corrected by switching to the immutable, thread-safe
  `java.time.format.DateTimeFormatter` introduced in Java 8, rather than by
  sharing the older, mutable type.
  **Fix.** Before hoisting or sharing any instance, confirm its documented
  thread safety. If the type is not documented as immutable or thread safe,
  either use a thread-local instance per caller, use an object pool that hands
  out exclusive, reset instances, or switch to a documented-safe alternative
  type rather than sharing the unsafe one.
- **Symptom.** A code review or static-analysis tool repeatedly flags
  constructor calls inside loops across an entire codebase, and developers
  begin blanket-hoisting every flagged construction regardless of the
  constructed type's actual cost, adding fields and shared state for objects
  that were genuinely cheap to construct fresh.
  **Cause.** Treating the linter or the pattern name as a rule to satisfy
  rather than a signal to investigate, applying the fix mechanically without
  first measuring whether the flagged construction is actually expensive
  relative to the surrounding work.
  **Fix.** Gate any hoisting or pooling change behind an actual measurement, a
  profiler sample, an allocation trace, or at minimum a documented, reasoned
  judgment about the constructed type's cost, per dimension 15's testing
  guidance, so the fix does not trade code clarity for an unmeasured and
  possibly imaginary performance gain.

## 12. Trade-off matrix

The comparison below is between the corrective mechanisms an engineer chooses
from once Improper Instantiation is confirmed, evaluated against the forces
named in dimension 3, because the anti-pattern itself has no trade-offs worth
tabulating, only its fixes do.

| Approach | Latency and throughput | Thread safety burden | Memory footprint | Operability | Implementation cost |
|---|---|---|---|---|---|
| Leave as-is, do nothing | Worst. Pays full construction cost every call. | None added. | Lowest steady-state, no long-lived shared state. | Hard to diagnose without a profiler, looks like generic slowness. | Zero. |
| Module-level constant or static field | Best for the read-only case. One-time cost, then near-zero overhead per call. | Must confirm immutability or that concurrent reads are safe, the value itself does no locking. | One long-lived instance instead of N short-lived ones, net reduction. | Easy to reason about, visible in source as a single, named, top-level declaration. | Low for stateless or immutable types. |
| Dependency injection, singleton scope | Very good, container amortizes construction the same as a static field, with the added cost of one indirection per resolution, usually negligible. | Container documents the scope contract, developer still must confirm the type itself is safe for that scope. | Same as static field, plus the container's own bookkeeping. | Best operability of the group, scope is explicit, centrally configured, and consistent across the codebase. | Moderate, requires an existing DI setup or the cost of introducing one. |
| Object pool | Good, avoids reconstruction cost but adds checkout and checkin overhead and pool-sizing tuning. | Highest burden, must guarantee exclusive access to a borrowed instance and correct reset between uses. | Bounded by pool size, can be tuned, but a mis-sized pool either wastes memory (too large) or serializes callers waiting for a free instance (too small). | Requires monitoring pool utilization and wait time, a common source of subtle production incidents when misconfigured. | Highest of the group, correct pooling is genuinely hard to get right, see the `object-pool` entry. |
| Memoization or result cache | Good for repeated identical inputs, no benefit for genuinely varying inputs. | Cache itself must be thread safe if shared across concurrent callers, for example a concurrent hash map, independent of the cached value's own thread safety. | Grows with the number of distinct inputs seen, needs an eviction policy, LRU, TTL, or bounded size, or it becomes an unbounded memory leak. | Cache hit rate becomes a useful, monitorable metric, a low hit rate signals the cache is not earning its complexity. | Moderate, eviction policy design is the main cost. |
| Lazy-once idiom (`lazy`, `OnceLock`, `by lazy`) | Same steady-state benefit as a static field, with a small one-time branch check on every access after the first. | Language-provided primitives handle the concurrency correctly by construction, for example Rust's `OnceLock` or Kotlin's default synchronized lazy mode. | Same as static field. | Very good, the idiom is self-documenting about intent, lazy, once. | Low, where the language ships the primitive as a built-in. |

## 13. Related and incompatible patterns

- **Flyweight (GoF, Structural).** The design pattern most directly aimed at
  the redundant-work sub-variant of this anti-pattern. It separates an
  object's intrinsic, shareable state from its extrinsic, per-use state, and
  hands out a shared instance of the intrinsic part. Where Flyweight is
  correctly applied ahead of time, this anti-pattern cannot occur for that
  type, because the API itself never offers a way to construct a fresh,
  redundant copy of the shareable state. See this catalog's `flyweight` entry
  for the pattern's own full, independently sourced treatment.
- **Object Pool (this catalog's `object-pool` entry, Structural and
  concurrency).** The design pattern aimed at the allocation-pressure and
  resource-exhaustion sub-variants, specifically for objects that are
  expensive, reusable after a reset, but not safely shareable as a single
  concurrent instance. Object Pool is the corrective pattern applied in
  dimension 8 for connections, threads, and similar resources. See that
  entry's own dimension 11 for pool-specific failure modes, pool exhaustion,
  leaked borrows, that are distinct from, but often confused with, this entry.
- **Dependency Injection (this catalog's `dependency-injection` entry,
  Architectural).** The broader architectural discipline that, when properly
  adopted, removes the opportunity for this anti-pattern to occur inside
  business logic, because business logic never calls a constructor directly
  for its collaborators, it receives already-constructed instances whose
  lifecycle is owned by a container. This entry's Spring Framework example in
  dimension 9 demonstrates a DI container's scope mechanism as the fix.
- **Factory Method and Abstract Factory (GoF, Creational).** These patterns
  centralize the decision of what type to construct, not how often to
  construct it. A factory can be misused to call `new` on every invocation
  as easily as inline code can, centralizing construction behind a
  factory method does not, by itself, fix this anti-pattern. It is a common
  and understandable confusion, because both concern where construction
  happens in the code, but Factory Method solves polymorphic type selection
  while Improper Instantiation is a lifecycle and frequency problem,
  addressing one does not automatically address the other.
- **Singleton (GoF, Creational) and this catalog's `singleton-abuse` entry.**
  Singleton is one legitimate way to guarantee a type is constructed exactly
  once, which directly fixes redundant-work instances of this anti-pattern.
  But `singleton-abuse` documents the opposite failure, using a global
  singleton as a substitute for proper dependency management, which trades
  the performance problem this entry describes for testability and coupling
  problems. The two entries describe adjacent but distinct failure zones. A
  hand-rolled global singleton used correctly, to solve a real repeated
  construction cost, is a legitimate fix for this entry's problem, the same
  global singleton used to avoid threading a dependency through a call chain,
  regardless of construction cost, is the failure `singleton-abuse` names.
- **Golden Hammer (this catalog's `golden-hammer` entry, General).**
  Indirectly related. A codebase that reaches for "wrap it in a singleton" or
  "cache everything" as a reflexive, uninvestigated response to any
  performance complaint is applying a golden hammer to this entry's problem,
  which is exactly the failure mode described in dimension 11's final
  symptom-cause-fix triple.
- **Incompatible with Flyweight and Object Pool**, in the specific sense that a
  correctly implemented instance of either pattern makes an instance of this
  anti-pattern for the same type impossible by construction, because the API
  itself no longer exposes an easy path to redundant instantiation. This is
  why both appear in this entry's frontmatter `incompatible_with` field. They
  are not merely related, they are the structural cure that, once applied,
  removes the anti-pattern's precondition entirely for that type.

## 14. Refactoring path in and out

### Introducing the fix

Steps to introduce the fix into code that currently has the anti-pattern.

1. Confirm the defect with evidence before changing anything. Use a CPU
   profiler, a flame graph or a sampling profiler, or an allocation tracer to
   confirm that the suspected constructor call is a measurable contributor to
   the cost of the hot path, per dimension 15's testing guidance. Skipping
   this step risks the premature-optimization failure named in dimension 4's
   non-applicability list.
2. Identify the exact scope boundary of the hot path, the loop, the request
   handler, the render callback, and the exact call site of the improper
   construction inside it.
3. Determine whether the constructed value is identical, effectively
   identical, or genuinely varies across invocations of the hot path.
   Identical or slowly changing values point toward the static field, DI
   singleton, or memoization variants in dimension 8. Genuinely varying values
   that are still expensive to construct point toward Object Pool.
4. Confirm the constructed type's documented thread safety before sharing an
   instance across concurrent callers. If undocumented, either read the
   source, test explicitly for thread safety, or default to a safer
   corrective mechanism, thread-local storage or a pool that hands out
   exclusive instances, rather than assuming safety.
5. Introduce the hoisting point, a field initialized in a constructor or an
   `init` block, a module-level constant, a DI container registration with
   the correct scope, or a pool with an explicit size and acquisition
   timeout.
6. Update the hot path to reference the shared or pooled instance instead of
   constructing a new one, and if a pool is used, add the corresponding
   release or return call in a `finally`, `using`, `defer`, or `with` block so
   the instance is returned even on an exception path.
7. Re-run the profiler or allocation trace from step 1 and confirm the
   measured cost dropped, per the same before-and-after methodology named in
   dimension 15. This closes the loop between the claim, this construction was
   expensive, and the fix, it no longer runs redundantly.
8. Add a regression test that would fail if the construction were
   accidentally reintroduced inside the hot path. Dimension 15 gives concrete
   technique options, an allocation-count assertion, a mock-based call-count
   assertion, or a benchmark with an asserted budget.

### Removing the fix

A corrective mechanism from dimension 8, a cache, a pool, a singleton scope,
should itself be removed or simplified when the type it manages has genuinely
become cheap to construct, for instance after a dependency upgrade changed the
type's internal implementation to lazily defer its own expensive work, or when
the call frequency of the hot path has dropped enough, a feature was
deprecated, traffic moved elsewhere, that the amortized savings no longer
justify the added complexity of shared state, pool management, or cache
eviction logic. The removal path mirrors the introduction path. Measure first,
confirm the corrective mechanism is no longer paying for itself, then revert
the hoisting and let the type construct normally at its call site, re-running
the same profiler-based verification to confirm the simplification did not
reintroduce a measurable regression.

## 15. Testing and verification

Testing for this anti-pattern splits into two genuinely different activities,
confirming the defect exists before fixing it, and confirming the fix works
and stays fixed after fixing it, and permanently thereafter via regression
tests.

### Confirming the defect

- CPU sampling profilers, Java Flight Recorder or async-profiler for the JVM,
  `perf` combined with flame graphs on Linux, Instruments on Apple platforms,
  Chrome DevTools' CPU profiler for JavaScript, `pprof` for Go, attributed
  time spent inside a constructor, `compile`, or `parse` call is the primary
  signal. A flame graph with a wide, flat frame for a constructor called from
  many distinct call sites inside a hot path is the visual signature.
- Allocation profilers or heap analysis tools, the JVM's async-profiler in
  allocation mode, Android Studio's Memory Profiler cited directly in
  dimension 9's production example, `dotnet-trace` with the GC collect
  provider for .NET, Go's `runtime/pprof` in allocation-objects mode, surface
  the allocation-pressure sub-variant, showing allocation rate and garbage
  collector pause frequency correlated with the hot path's invocation rate.
- A targeted micro-benchmark, JMH for Java, BenchmarkDotNet for .NET, Go's
  built-in `testing.B`, `pytest-benchmark` for Python, that isolates the
  suspected constructor call and measures its wall-clock cost per invocation,
  multiplied by the hot path's known or estimated call frequency, turns "this
  feels expensive" into a specific number that justifies or disqualifies the
  fix, directly addressing dimension 11's final failure mode of applying the
  fix without evidence.

### Confirming and preserving the fix

- A construction-count assertion. Instrument the expensive type's
  constructor, via a spy, a mock framework's call-count tracking, or a manual
  counter in test code, and assert it was invoked exactly once, or exactly
  once per genuinely distinct input, across N invocations of the hot path in
  a test. This is a strong, precise, and cheap regression test once the fix
  is in place, because it fails immediately and specifically if the
  redundant construction is ever reintroduced, rather than failing only as a
  slow, statistically noisy performance regression.
- Where a mocking framework is already in use for the type in question,
  common for database connections, HTTP clients, and similar heavyweight
  collaborators, asserting the mock factory or mock constructor was called
  the expected number of times is the most direct expression of this test and
  requires no additional instrumentation.
- Where a pool is the corrective mechanism, tests should additionally assert
  that every borrowed instance is returned to the pool even on the exception
  path, this is the specific defect the `object-pool` entry's own dimension
  11 covers as pool leakage, and that concurrent borrowers never receive the
  same instance simultaneously, typically via a stress test that borrows and
  releases from many threads or coroutines concurrently and asserts no two
  callers ever observed the same instance identity at the same time.
- A before-and-after benchmark, run in CI on a stable, dedicated benchmark
  runner rather than a shared, noisy CI worker, with an asserted regression
  budget, fail the build if the hot path's measured throughput or allocation
  rate exceeds a documented threshold, turns the fix from a one-time
  improvement into an enforced, ongoing property of the codebase.

## 16. Observability signals

- **Garbage collector metrics.** Minor or young-generation collection
  frequency and pause duration, exposed by the JVM's GC logging or JFR events,
  .NET's `dotnet-counters` GC counters, or the Android Memory Profiler's GC
  event timeline, the exact tool cited by name in dimension 9's Android
  example. A healthy service under steady load shows a roughly constant,
  predictable minor-GC cadence, a service suffering from this anti-pattern
  typically shows a GC cadence that scales with request or frame rate rather
  than staying flat, and the GC's own attributed CPU time, visible as a
  separate thread or a distinct flame-graph region, climbing as a share of
  total CPU.
- **Allocation rate.** Bytes allocated per second or per request, exposed
  directly by most managed runtimes' built-in metrics, the JVM's
  `ObjectAllocationSample` JFR event, Go's `runtime.MemStats.Mallocs`, .NET's
  allocation-rate performance counter. A sudden step change in allocation
  rate correlated with a specific deploy is one of the fastest, cheapest
  signals available for catching a newly introduced instance of this
  anti-pattern before it reaches a customer-visible latency complaint.
- **Constructor or factory call counters.** For the highest-value, most
  expensive types in a codebase, a regular expression engine, a database
  connection factory, a template compiler, an explicit application-level
  metric, a counter incremented inside the constructor or the factory
  function, directly measures construction frequency and is the single most
  precise, purpose-built signal for this specific anti-pattern, because it
  measures the exact quantity the anti-pattern is about, rather than a proxy
  like general allocation rate or GC pause time.
- **Connection or resource pool metrics.** For the pooled variant, standard
  pool implementations, HikariCP for JDBC, most language-standard HTTP client
  connection pools, expose active-connection count, idle-connection count,
  wait-for-connection time, and connection-creation count. A steadily rising
  connection-creation counter, rather than a stable one after warm-up, is the
  specific signature of a pool that is not actually being reused, either
  because pooling was configured incorrectly or because a code path bypasses
  the pool entirely and constructs raw connections directly, which is this
  anti-pattern occurring silently underneath an otherwise correctly
  configured pool.
- **Healthy versus unhealthy dashboard shape.** A healthy instance of a type
  managed correctly under the fixes in dimension 8 shows a construction or
  cache-miss counter that rises briefly during startup or during a cache
  warm-up window and then flattens to near zero under steady traffic. An
  unhealthy instance shows that same counter rising in lockstep with request
  or frame rate indefinitely, which is the clearest dashboard-level tell that
  the anti-pattern, or a regression reintroducing it, is present.

## 17. Security and privacy implications

This dimension is largely engineering judgement rather than a set of sourced
facts, because the security implications of Improper Instantiation are
indirect, arising from resource exhaustion and availability risk rather than
from a data-confidentiality or integrity mechanism the anti-pattern itself
defeats.

- **Denial of service via resource exhaustion.** The clearest security-adjacent
  consequence. A code path that constructs a new socket, file handle, or
  database connection per request, without pooling or a hard upper bound, is
  an amplification vector. A relatively modest volume of legitimate or
  attacker-driven traffic can exhaust file descriptors, database connection
  limits, or memory faster than the equivalent, correctly pooled
  implementation would, turning an ordinary availability weakness into an
  effective, low-cost denial-of-service surface. This is the same mechanism
  named in dimension 11's connection-exhaustion failure mode, viewed from a
  threat-model perspective rather than a purely operational one.
- **Accidental cross-request state leakage from the wrong fix, not the
  anti-pattern itself.** As documented in dimension 11's inverse-misuse
  failure mode, the corrective instinct, sharing an instance to avoid
  reconstruction cost, is the source of an actual confidentiality risk when
  applied to a type that carries per-request or per-user state and is not
  safe to share, the historical `SimpleDateFormat` sharing bug being the
  canonical, widely repeated example in Java's standard library history. Where the shared
  state includes anything derived from one user's request, a session token, a
  parsed value from a request body, a partially built response, an
  incorrectly shared instance can leak one user's data into a concurrently
  processed, different user's response. The anti-pattern this entry describes
  does not cause this, the naive fix for it, applied without checking thread
  safety, does. This is judgement, drawn from the well-documented history of
  the `SimpleDateFormat` sharing bug rather than from a single citable
  security advisory specific to this anti-pattern.
- **No direct implication for cryptographic secrets.** One narrow exception
  worth naming explicitly, because it runs the opposite direction from the
  general performance advice in this entry. Cryptographically sensitive
  ephemeral values, nonces, initialization vectors, and per-session keys, must
  generally be constructed fresh per use precisely because reuse is the
  security defect, not the performance win. An engineer applying this entry's
  general advice mechanically, "hoist expensive construction out of hot
  paths", without domain-specific judgement, to a nonce or IV generator would
  introduce a serious cryptographic weakness rather than a performance
  improvement. This is the security dimension's own instance of dimension 4's
  non-applicability principle. Know what the constructed object's freshness
  actually guarantees before "fixing" its construction frequency.
- **No inherent data-at-rest or data-in-transit implication.** Beyond the two
  points above, this anti-pattern carries no direct implication for
  encryption, access control, or data classification. It is a
  performance-and-availability concern whose only security-relevant edge
  cases are the resource-exhaustion amplification vector and the
  shared-mutable-state leakage risk documented above.

## 18. References

1. Microsoft, .NET documentation on regular expression performance guidance,
   https://learn.microsoft.com/en-us/dotnet/standard/base-types/best-practices-regex,
   verified 2026-08-02. Source for the "coupling process is expensive"
   quotation, the static-cache size default of fifteen patterns adjustable via
   `Regex.CacheSize`, and the `static readonly HttpClient s_client = new();`
   example code demonstrating the same fix idiom applied to `HttpClient`.
2. Oracle, `java.util.regex.Pattern` class documentation, Java SE 21 API
   specification,
   https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/regex/Pattern.html,
   verified 2026-08-02. Source for the immutability and thread-safety
   statement and the recommendation to compile once and reuse rather than
   invoking `Pattern.matches` repeatedly.
3. Google, "Reduce, reuse, recycle. Diagnosing render performance", Android
   Developers documentation,
   https://developer.android.com/topic/performance/vitals/render, verified
   2026-08-02. Source for the allocation-in-tight-loop guidance, the Android
   Memory Profiler reference, and the measured garbage collection pause
   example described in that document.
4. Spring Framework reference documentation, "Bean Scopes",
   https://docs.spring.io/spring-framework/reference/core/beans/factory-scopes.html,
   verified 2026-08-02. Source for the definitions of singleton and prototype
   bean scope and the rule of thumb distinguishing stateful and stateless
   bean lifecycle management.
5. Gamma, Erich, Richard Helm, Ralph Johnson, and John Vlissides, *Design
   Patterns. Elements of Reusable Object-Oriented Software*, Addison-Wesley,
   1994, chapter 3, Flyweight. Judgement citation for the structural
   relationship between Flyweight and the redundant-work sub-variant of this
   anti-pattern, referenced in dimension 13. Consult this catalog's own
   `flyweight` entry for the pattern's full, independently sourced treatment.
6. Oracle, `java.text.SimpleDateFormat` class documentation, Java SE API
   specification. Referenced from memory of the widely and independently
   documented fact that `SimpleDateFormat` instances are not thread safe,
   used in dimension 11 and dimension 17 as a well-known historical example
   of the inverse-misuse failure mode. This specific claim is treated in this
   entry as established community knowledge about a long-standing,
   extensively documented Java API limitation rather than as requiring a
   fresh live citation, and a reader should independently confirm the current
   Javadoc wording before citing it elsewhere.

## Code examples

Working code in four languages, each demonstrating the defective and corrected
forms of the same failure and, where the toolchain allows, compiled or run to
confirm the corrected form behaves as claimed.

### Java. `Pattern.compile` inside a loop versus hoisted once

```java
import java.util.regex.Pattern;
import java.util.regex.Matcher;

public class ImproperInstantiationDemo {

    // Defective. compiles the same pattern on every call.
    static int countMatchesDefective(String[] lines, String regex) {
        int total = 0;
        for (String line : lines) {
            Pattern p = Pattern.compile(regex);
            Matcher m = p.matcher(line);
            if (m.find()) {
                total++;
            }
        }
        return total;
    }

    // Corrected. the Pattern is compiled once, outside the loop,
    // and each iteration creates only the lightweight Matcher.
    static final Pattern DIGIT_PATTERN = Pattern.compile("\\d+");

    static int countMatchesCorrected(String[] lines) {
        int total = 0;
        for (String line : lines) {
            Matcher m = DIGIT_PATTERN.matcher(line);
            if (m.find()) {
                total++;
            }
        }
        return total;
    }

    public static void main(String[] args) {
        String[] lines = {"order 42", "no digits here", "id 7 qty 3"};
        int defective = countMatchesDefective(lines, "\\d+");
        int corrected = countMatchesCorrected(lines);
        System.out.println("defective result = " + defective);
        System.out.println("corrected result = " + corrected);
        if (defective != corrected) {
            throw new IllegalStateException("results diverged, refactor is not behavior-preserving");
        }
        System.out.println("both paths agree, only construction frequency differs");
    }
}
```

### Go. `regexp.MustCompile` inside a function versus a package-level var

```go
package main

import (
	"fmt"
	"regexp"
)

// Defective. every call to matchesDefective recompiles the pattern.
func matchesDefective(input string) bool {
	re := regexp.MustCompile(`^\d{3}-\d{4}$`)
	return re.MatchString(input)
}

// Corrected. the pattern is compiled exactly once, at package
// initialization, and reused by every call to matchesCorrected.
var phoneSuffixPattern = regexp.MustCompile(`^\d{3}-\d{4}$`)

func matchesCorrected(input string) bool {
	return phoneSuffixPattern.MatchString(input)
}

func main() {
	inputs := []string{"555-1234", "not-a-number", "000-0000"}
	for _, in := range inputs {
		d := matchesDefective(in)
		c := matchesCorrected(in)
		fmt.Printf("input=%-14s defective=%v corrected=%v\n", in, d, c)
		if d != c {
			panic("results diverged, refactor is not behavior-preserving")
		}
	}
	fmt.Println("both paths agree, only construction frequency differs")
}
```

### Python. a per-call configuration parser versus a module-level singleton

```python
import json
import time


_RAW_CONFIG = json.dumps({"retries": 3, "timeout_ms": 250, "region": "eu-central"})


class ExpensiveConfig:
    """Stands in for a type whose construction does real parsing work."""

    def __init__(self, raw: str):
        # A trivial sleep stands in for real, genuinely costly parse cost
        # (schema validation, cross-field checks) that a config
        # object's constructor might legitimately perform.
        time.sleep(0.001)
        self.data = json.loads(raw)


def handle_request_defective(raw_config: str) -> int:
    # Defective. constructs a fresh, fully-parsed config on every call.
    config = ExpensiveConfig(raw_config)
    return config.data["retries"]


# Corrected. constructed once at module load time, reused by every call.
_SHARED_CONFIG = ExpensiveConfig(_RAW_CONFIG)


def handle_request_corrected() -> int:
    return _SHARED_CONFIG.data["retries"]


if __name__ == "__main__":
    start = time.perf_counter()
    for _ in range(20):
        handle_request_defective(_RAW_CONFIG)
    defective_elapsed = time.perf_counter() - start

    start = time.perf_counter()
    for _ in range(20):
        handle_request_corrected()
    corrected_elapsed = time.perf_counter() - start

    print(f"defective path,  20 calls, {defective_elapsed:.4f}s")
    print(f"corrected path,  20 calls, {corrected_elapsed:.4f}s")
    assert handle_request_defective(_RAW_CONFIG) == handle_request_corrected()
    assert corrected_elapsed < defective_elapsed
    print("corrected path is measurably faster, same result")
```

### TypeScript. a per-render `RegExp` and formatter versus fields constructed once

```typescript
class DefectiveFormatter {
  format(rows: string[]): string[] {
    return rows.map((row) => {
      // Defective. a new RegExp and a new Intl.NumberFormat are
      // constructed on every single row, inside the hot loop.
      const numberPattern = /\d+(\.\d+)?/;
      const currency = new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
      });
      const match = row.match(numberPattern);
      if (!match) return row;
      return currency.format(Number(match[0]));
    });
  }
}

class CorrectedFormatter {
  // Corrected. both the RegExp and the Intl.NumberFormat are
  // constructed exactly once, as instance fields, and reused
  // across every row the formatter processes.
  private readonly numberPattern = /\d+(\.\d+)?/;
  private readonly currency = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  });

  format(rows: string[]): string[] {
    return rows.map((row) => {
      const match = row.match(this.numberPattern);
      if (!match) return row;
      return this.currency.format(Number(match[0]));
    });
  }
}

const rows = ["item 12.5", "item 3", "no number here", "item 199.99"];

const defective = new DefectiveFormatter().format(rows);
const corrected = new CorrectedFormatter().format(rows);

console.log("defective:", defective);
console.log("corrected:", corrected);

const agree = defective.every((v, i) => v === corrected[i]);
if (!agree) {
  throw new Error("results diverged, refactor is not behavior-preserving");
}
console.log("both paths agree, only construction frequency differs");
```
