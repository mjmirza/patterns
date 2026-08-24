---
name: Indirection
slug: indirection
family: 04-principles-and-laws
category: Principle
aliases: [Layer of Indirection, Level of Indirection, Indirection Layer]
first_described: "Larman, Applying UML and Patterns, 1997 (GRASP formulation); the general computing aphorism is older and its exact origin is contested, see dimension 1"
maturity: canonical
related: [proxy, facade, adapter, dependency-inversion-principle, low-coupling, mediator, protected-variations]
incompatible_with: []
verified: 2026-08-02
---

## 1. Name, aliases, and lineage

The canonical name is Indirection. It denotes referring to something through a
name, a handle, or an intermediary object rather than through the thing itself.
The word is used at two distinct levels in software engineering literature, and
conflating them is the single most common source of confusion when someone says
"add a layer of indirection" without saying which one they mean.

The first level is the general computing principle. An indirection is any
mechanism that lets a caller reach a value without holding the value's identity
directly, so the mapping between the name and the value can change without the
caller changing. A pointer, a symbolic link, a DNS name, a database foreign key,
and a function pointer are all indirections in this sense. This usage predates
object-oriented design entirely and belongs to computer science as a whole,
covering memory addressing, file systems, networking, and compilers alike.

The most quoted sentence about it is an aphorism usually rendered as "All
problems in computer science can be solved by another level of indirection."
Wikipedia's article on indirection states the line is commonly attributed to
David Wheeler, an early developer of the subroutine at Cambridge in the 1950s,
but notes the attribution is not settled and the same words are also credited
to Butler Lampson, who himself attributed a version of it to Wheeler (Wikipedia
contributors, "Indirection," https://en.wikipedia.org/wiki/Indirection, verified
2026-08-02). The article also records the corollary that is usually left off
when the aphorism is quoted approvingly, "except for the problem of too many
layers of indirection." That corollary is not a throwaway joke, it is the
entire content of dimension 3 and dimension 11 below, and an entry on
Indirection that omits it has missed the point of the principle. A frequent
distortion swaps "level of indirection" for "abstraction layer," which changes
the claim, because not every abstraction is an indirection and not every
indirection is abstract, see dimension 4.

The second level is the specific, named design principle codified by Craig
Larman inside his catalog of nine GRASP patterns, General Responsibility
Assignment Software Patterns, first published in *Applying UML and Patterns. An
Introduction to Object-Oriented Analysis and Design and Iterative Development*,
Prentice Hall, 1997, with the material substantially unchanged through the
third edition in 2004. GRASP is not a single pattern in the Gang of Four sense,
it is Larman's teaching framework for assigning a responsibility to a class
during object design, and Indirection is the member of that framework that
answers the question "who should mediate between two things that should not
know about each other directly." In Larman's formulation the responsibility is
assigned to an intermediate object, so the two original parties are decoupled
and neither is forced to change when the other does. The GRASP catalog groups
Indirection alongside Low Coupling, High Cohesion, Controller, Creator,
Information Expert, Polymorphism, Protected Variations, and Pure Fabrication,
and Larman himself notes that Indirection, together with Polymorphism, is the
usual mechanism by which Protected Variations is achieved in practice, because
an intermediary that hides a volatile thing behind a stable interface protects
the rest of the system from that thing's changes.

This entry treats the general computing principle as the frame and the GRASP
formulation as its most disciplined statement inside object-oriented design,
because the GRASP version is the one with a citable definition, a clear
participant model, and a place in a design methodology that a reader can act on
directly. Every worked example in this entry, whether it is a pointer, a proxy
object, a service name, or a database key, is an instance of the same idea.
something is not held directly, it is held through a name that can be
re-pointed.

## 2. Problem and context

Two parts of a system need to interact, but binding them together directly
creates a cost that shows up later rather than now. The concrete situations
recur across every layer of a stack.

At the memory layer, code holds the address of a value directly. Moving the
value, for instance during garbage collection compaction or when a data
structure resizes, breaks every holder of that address unless every holder is
found and updated in lockstep. At the file system layer, a program opens a file
by its literal path. Moving the file, renaming a directory above it, or
replacing it with a newer version on a different volume breaks every caller
that stored the path. At the network layer, a client connects to a literal IP
address. The machine behind that address is retired, its load grows past
capacity, or the service moves to another data center, and every client with
the address burned into a config file breaks at once. At the object design
layer, one class calls a concrete method on a concrete class of another
object. The called class ships a breaking change, is replaced by a competing
implementation, or needs to be mocked in a test, and the calling class must
change too, even though its own logic never moved.

The problem, stated once for all four situations, is that a direct reference
couples the lifetime and the identity of the referrer to the lifetime and
identity of the referent. Any of five events forces the reference to become
invalid or wrong. The referent moves, the referent is replaced, the referent
needs to vary by context, the referent must be observed or audited without its
own knowledge, or the referent must be substituted in a test. A codebase that
never anticipates any of these five events does not need indirection. A
codebase that will face at least one of them, and every codebase of nontrivial
lifetime faces several, needs a name it can re-bind instead of a value it must
track by hand.

The context that makes indirection the right answer, rather than premature
architecture, has a specific shape. The two parties genuinely have different
rates of change, different owners, or different lifetimes, and the cost of
updating every direct reference by hand when one of them changes is higher than
the cost of maintaining the intermediary. When both parties change together, at
the same time, by the same author, the intermediary adds pure overhead, see
dimension 4.

## 3. Forces

The competing pressures Indirection balances, stated honestly rather than as a
pure win.

- **Coupling.** Favoured, and this is the entire reason the principle exists. A
  caller depends on a stable name or interface instead of a volatile concrete
  identity, so change on one side does not propagate to the other.
- **Latency and directness.** Sacrificed. Every hop through a name, a table, a
  proxy, or a resolver costs a lookup or a dispatch that a direct reference
  would not pay. A DNS resolution, a virtual dispatch, a network hop through a
  gateway, or a pointer dereference through one extra level of handle is all
  real, measurable cost, even when it is usually small enough to ignore.
- **Traceability and debuggability.** Sacrificed. A reader or a debugger
  following a direct reference sees the destination immediately. A reader
  following an indirection must resolve the name first, and when the resolution
  is dynamic, runtime state determines the destination, so a static read of the
  source is not enough to know where control actually goes.
- **Flexibility to change the referent.** Favoured. The name can be re-bound to
  a different concrete thing, at build time, at deploy time, or at runtime,
  without touching the code that uses the name.
- **Consistency during transition.** Favoured for coordinated cutover. A single
  point of re-binding lets an operator move every consumer to a new
  implementation atomically, rather than chasing every call site.
- **Failure surface.** Sacrificed. The intermediary is a new component that can
  itself fail, become stale, become a bottleneck, or become a single point of
  failure that neither original party had.
- **Cognitive load for the simple case.** Sacrificed. When there is exactly one
  referent and it will never have a second, the intermediary is a name for a
  name, and a reader must learn the indirection layer's own concepts before
  reaching the actual logic.
- **Extensibility across the axis of variation.** Favoured, when the
  intermediary sits at the point where new implementations are expected to
  arrive. A new implementation is added behind the existing name without
  touching any consumer.

Wheeler's corollary from dimension 1 is the honest summary of this table. Every
one of the "favoured" rows is purchased by paying into one or more of the
"sacrificed" rows, and stacking indirections multiplies the sacrificed costs
while the favoured benefit typically does not compound the same way, because
one well-placed level of decoupling already captures most of the flexibility a
system needs.

## 4. Applicability and non-applicability

Reach for Indirection when the following hold.

- Two components genuinely vary at different rates or are owned by different
  teams, so binding them directly would force one to release in lockstep with
  the other.
- The concrete referent is expected to change in a way the caller should not
  need to know about, for example a database moving hosts, a service migrating
  providers, an object needing to be swapped for a test double, or an
  implementation needing runtime configuration.
- A caller must be able to observe or intercept an interaction without the
  interacting parties being aware of the observation, for example logging,
  caching, authorization, or rate limiting inserted between a client and a
  service.
- Several equally valid implementations of the same responsibility exist or
  will exist, and the calling code should not need a branch to select between
  them.
- A resource must survive being physically relocated while every reference to
  it stays valid, which is the definition of a handle table, a symlink, or a
  DNS record.

Do NOT reach for Indirection in these cases, and the reason in each case
matters more than the rule.

- **There is exactly one implementation and no credible second.** An
  intermediary built for a variation that never arrives is speculative
  generality dressed as good practice. A direct call reads better, is faster,
  and is trivially deletable when the assumption changes, whereas an unused
  interface with one implementor has to be found and removed later. Cross
  reference the code smell family entry on speculative generality.
- **The two parties are inherently coupled by the domain, not by
  accident.** Some relationships are not incidental, they are the actual model.
  Forcing an interface between a bank account and its ledger entry when the two
  will always change together and always mean the same thing adds a name with
  no decoupling value.
- **The added hop violates a real-time or hot-path latency budget.** A trading
  system's matching engine, an audio callback, or a kernel interrupt handler
  frequently cannot absorb an extra dereference, virtual call, or network hop.
  In these contexts the indirection is inlined away by the compiler where
  possible, or removed by design, and the flexibility is bought some other way,
  for example by code generation ahead of time.
- **The indirection would hide a failure mode a caller genuinely needs to
  see.** A proxy that silently retries and swallows an error, or a DNS layer
  that masks which physical host actually served a request during an incident,
  is not abstraction, it is loss of information that operators will need.
  Indirection that removes observability rather than adding a seam for it is
  applied wrongly, see dimension 16.
- **The problem is really about naming or discoverability, not
  substitutability.** If nothing will ever be substituted for the referent and
  the only goal is a friendlier name, a simple alias or a well-named constant
  solves it without a resolvable, re-bindable layer.
- **The "indirection" is actually indirection through a mutable global.** A
  singleton, a service locator, or a global registry that any code can silently
  reach into and reconfigure trades explicit dependency for implicit,
  hard-to-trace coupling. This is discussed as a direct conflict in dimension
  13.
- **You are compensating for a design that should not need substitution at
  all.** Adding a factory, an interface, and a dependency-injection binding for
  a value object that will never have a second representation, such as a
  `Money` type or a `UserId`, is indirection applied to something that gains
  nothing from it and loses value-type simplicity.

## 5. Structure

The participants, named by the role they play, generalised across the concrete
forms in dimension 8.

- **Client.** The party that needs to use the referent but should not, or
  cannot, depend on its concrete identity directly.
- **Name, or Handle.** The stable token the Client holds instead of the
  referent. It can be a string, an integer key, a pointer to a pointer, a
  symbolic path, a DNS name, or an interface reference. Its defining property
  is that it outlives, or at least can outlive, any single binding to a
  concrete Referent.
- **Resolver, or Intermediary.** The component that maps a Name to a current
  Referent. This is the seam where the actual indirection happens, whether it
  is a symbol table, a DNS resolver, a dependency-injection container, a proxy
  object, a routing table, or a page table in an operating system's virtual
  memory subsystem.
- **Referent, or Real Subject.** The concrete thing the Client ultimately wants
  to use. It is free to change identity, move, or be replaced, as long as the
  Resolver's mapping is updated to match.

The relationship that defines the pattern is this. The Client's only static
dependency is on the Name and, where one is expressed as a type, on the
interface the Referent must satisfy. The Client has no static dependency on any
specific Referent. The Resolver is the only component that depends on both the
Name space and the concrete Referent space, and it is therefore the one place
in the system where re-binding is a local, single-owner change.

## 6. ASCII structure diagram

```
   +-----------+   holds name    +-----------------+
   |  Client   |----------------->  Name / Handle  |
   +-----------+                 +-----------------+
        |                                 |
        | asks the resolver               | is looked up by
        | to resolve the name             |
        v                                 v
   +---------------------------------------------+
   |             Resolver / Intermediary          |
   |  (symbol table, DNS, DI container, proxy,    |
   |   routing table, page table, registry)       |
   +---------------------------------------------+
        |                     |                    |
        | binds to            | binds to           | binds to
        v                     v                    v
   +-----------+      +-----------+          +-----------+
   | Referent A|      | Referent B|          | Referent C|
   +-----------+      +-----------+          +-----------+

   The Client's compile-time dependency stops at the dashed
   boundary drawn by the Resolver. Which Referent answers a
   given Name can change without recompiling or redeploying
   the Client.
```

## 7. Dynamics

The runtime flow has one property worth calling out explicitly. The binding
between Name and Referent is looked up on every access, or cached and
invalidated, but it is never fixed at the moment the Client was written. That
is the whole difference between this and a direct reference, which is bound
once, at compile or link time, and never revisited.

```
Client                Resolver                 Referent (v1)      Referent (v2)
  |                       |                          |                    |
  |-- use(Name) --------->|                          |                    |
  |                       |-- lookup(Name) --------->|                    |
  |                       |<-- currently v1 ---------|                    |
  |                       |                          |                    |
  |<-- delegate call -----|-------------------------->|                    |
  |                       |<-- result -----------------|                    |
  |<-- result ------------|                          |                    |
  |                       |                          |                    |
  |   ... operator or system re-binds Name to v2 ...  |                    |
  |                       |                          |                    |
  |-- use(Name) --------->|                          |                    |
  |                       |-- lookup(Name) --------------------------------->|
  |                       |<-- currently v2 -------------------------------- |
  |<-- delegate call ----------------------------------------------------->|
  |<-- result --------------------------------------------------------------|
```

The re-binding step in the middle is the entire point. Nothing about the two
calls from the Client differs syntactically. Everything about which Referent
actually did the work differs. Two properties of the Resolver decide the
correctness and cost of this flow in practice. Whether resolution is eager and
cached, which is cheap and fast but risks serving a stale binding, or lazy and
uncached, which is always current but pays a lookup cost on every access.
Dimension 11 covers what happens when either of these assumptions is violated
without anyone noticing.

## 8. Implementation variants

**Pointer, or reference, indirection.** The oldest and cheapest form. A memory
address stands in for a value. Adding a second pointer to that address, a
pointer to a pointer, is the mechanism C and C++ programmers use to let a
callee reassign what the caller's variable points to, and it is also how a
garbage collector relocates objects during compaction without breaking live
references, by updating one table of roots rather than every pointer in the
heap.

**Symbolic naming, filesystem and network.** A symbolic link, a mount point, or
a DNS name is a Name resolved by an operating system or a naming service into a
concrete inode, device, or IP address. RFC 1034 describes the Domain Name
System as providing exactly this facility for the internet, letting a host name
be re-pointed to a different machine without every client that uses the host
name needing to change (P. Mockapetris, RFC 1034, "Domain Names, Concepts and
Facilities," November 1987, https://www.rfc-editor.org/rfc/rfc1034, verified
2026-08-02).

**Virtual memory.** An operating system's page table is a Resolver mapping a
process's virtual addresses to physical page frames, letting the kernel move,
swap, or share physical memory without the process's own pointers ever
changing. The Linux `mmap` system call is the userspace-facing instance of this
same mechanism, mapping a file or a device into a process's virtual address
space so the process can address file content as memory rather than through
read and write calls (Linux man-pages project, `mmap(2)`,
https://man7.org/linux/man-pages/man2/mmap.2.html, verified 2026-08-02).

**Interface, or polymorphic, indirection.** A statically typed language
expresses the Name as an interface or an abstract base type, and the Resolver
is whichever mechanism supplies the concrete implementor, a constructor
argument, a dependency-injection container, or, per the Factory Method entry in
this catalog, a virtual creation method. This is the form GRASP's Indirection
pattern most directly targets in object design, and Larman treats it as the
usual companion to Protected Variations.

**Proxy and stand-in objects.** A Proxy object implements the same interface as
a Real Subject and forwards calls to it, adding a seam for lazy loading, remote
access, access control, or caching. See the Proxy entry in this catalog for the
full treatment, including the four canonical proxy varieties. Every Proxy is an
instance of Indirection, but not every Indirection is a Proxy, because a
Resolver that returns a different concrete object each time, rather than
forwarding to a fixed one, is a broader mechanism.

**Function or closure indirection.** In a language with first-class functions,
the Name becomes a variable holding a function value, and re-binding the
variable is the entire indirection. A callback registered with an event system,
a strategy held in a field, or a middleware chain built from an array of
functions are all this form. It has none of the ceremony of an interface plus
implementors, at the cost of the substitution being visible only at the wiring
site rather than as a named, documented extension point.

**Registry and lookup-table indirection.** A Name is a key, most often a
string or an enum value, and the Resolver is a map populated at startup or at
plugin registration time. This is the mechanism behind a dependency-injection
container's binding table, a plugin system's command registry, and a database
foreign key, which is a Name, the key value, resolved by the database's own
index into the actual row.

**API Gateway, reverse proxy, and service mesh indirection.** At the
distributed-systems scale, an API Gateway sits between client applications and
a set of microservices, giving clients a single, stable endpoint while the
internal service topology changes freely behind it. Microsoft's own
architecture guidance for containerized .NET applications states plainly that
without this intermediate tier "the client apps are coupled to the internal
microservices," and names this an "intermediate level or tier of indirection"
explicitly (Microsoft, ".NET Microservices Architecture for Containerized .NET
Applications," "The API Gateway pattern versus the direct client-to-microservice
communication,"
https://learn.microsoft.com/en-us/dotnet/standard/microservices-architecture/architect-microservice-container-applications/direct-client-to-microservice-communication-versus-the-api-gateway-pattern,
verified 2026-08-02). A Kubernetes Service is the cluster-internal instance of
the same idea, a stable virtual IP and DNS name in front of a set of Pods whose
individual IP addresses change constantly as Pods are created and destroyed
(Kubernetes documentation, "Service,"
https://kubernetes.io/docs/concepts/services-networking/service/, verified
2026-08-02).

## 9. Known production uses

**The Domain Name System.** Every hostname on the public internet is a Name
resolved through a distributed hierarchy of resolvers into an IP address, so a
site can change hosting providers, add capacity, or fail over a data center
without a single client needing a new bookmark. RFC 1034, "Domain Names,
Concepts and Facilities," https://www.rfc-editor.org/rfc/rfc1034, verified
2026-08-02.

**The Linux virtual memory subsystem, `mmap(2)` and the kernel page table.**
Every user-space process addresses memory through virtual addresses that the
kernel's page tables resolve to physical frames, letting the kernel relocate,
swap, or copy-on-write physical pages transparently. Linux man-pages project,
`mmap(2)`, https://man7.org/linux/man-pages/man2/mmap.2.html, verified
2026-08-02.

**Kubernetes Services.** Every Kubernetes Service provides a stable ClusterIP
and DNS name resolved to whichever set of Pod IP addresses currently matches
its label selector, decoupling every client of a workload from that workload's
constantly changing physical placement. Kubernetes documentation, "Service,"
https://kubernetes.io/docs/concepts/services-networking/service/, verified
2026-08-02.

**API Gateways in microservice architectures, for example Ocelot and Azure
API Management as documented for the eShopOnContainers reference
architecture.** Client applications call a single gateway endpoint that
resolves and routes each request to the current internal microservice
topology, so internal services can be split, merged, or relocated without a
client release. Microsoft, ".NET Microservices Architecture for Containerized
.NET Applications," https://learn.microsoft.com/en-us/dotnet/standard/microservices-architecture/architect-microservice-container-applications/direct-client-to-microservice-communication-versus-the-api-gateway-pattern,
verified 2026-08-02.

**Craig Larman's GRASP catalog itself, adopted as design guidance across the
object-oriented design curriculum.** Larman codifies Indirection as one of nine
named responsibility-assignment patterns in *Applying UML and Patterns*,
explicitly pairing it with Polymorphism as the standard mechanism for achieving
Protected Variations, and it is taught this way in university object-design
courses and referenced directly by the GRASP summary on Wikipedia. Wikipedia
contributors, "GRASP (object-oriented design),"
https://en.wikipedia.org/wiki/GRASP_(object-oriented_design), verified
2026-08-02.

## 10. Consequences

Positive.

- A caller depends on a stable, narrow Name or interface rather than on the
  full surface and identity of a concrete Referent, which is the core idea
  behind low coupling.
- The concrete Referent can be relocated, replaced, versioned, or substituted
  for a test double without any change to the caller.
- A single, well-owned point exists where cross-cutting behaviour, logging,
  caching, access control, rate limiting, can be inserted without touching
  either original party.
- Multiple equally valid implementations can coexist behind one Name,
  supporting gradual migration, canary rollout, or multi-tenant variation.
- The Resolver becomes a natural place to observe, instrument, and audit an
  interaction that would otherwise be invisible if the parties spoke directly.

Negative.

- Every access pays the cost of resolution, whether that is a pointer
  dereference, a hash lookup, a network round trip, or a virtual dispatch, and
  this cost is real even when it is usually negligible.
- Debugging requires resolving the Name to find out what actually ran, which
  means a static read of the source is no longer sufficient, and tooling such
  as a debugger, a trace, or a log line becomes necessary to answer "what code
  executed here."
- The Resolver is a new component with its own failure modes. It can be a
  single point of failure, it can serve a stale binding, and it can itself
  become a bottleneck if every access to every Referent funnels through it.
- Wheeler's corollary applies literally. Stacking indirections, a gateway in
  front of a service mesh in front of a load balancer in front of a proxy,
  compounds the cost of every negative row above while the marginal decoupling
  benefit of each additional layer shrinks.
- An unnecessary indirection, applied where dimension 4's non-applicability
  conditions hold, adds a name, a lookup, and a mental model for no
  corresponding benefit, and it is a maintenance liability precisely because it
  looks intentional and disciplined rather than looking like the dead weight it
  is.

## 11. Failure modes and misuse

**Stale binding.** Symptom. A client keeps talking to a Referent that was
supposed to be retired, or DNS keeps resolving to an old IP long after a
migration, and traffic silently splits between the old and new destination.
Cause. A cache in the Resolver, a DNS time-to-live, or a connection pool that
holds a resolved Referent past the point where the binding changed. Fix. Bound
cache lifetimes to the actual volatility of the binding, respect and set
sensible time-to-live values, and prefer re-resolving on a schedule the
operator controls rather than resolving once and holding forever.

**The indirection that hides the real failure.** Symptom. An incident where
requests are failing, but every dashboard shows the gateway or the load
balancer as healthy, because the gateway is healthy, it is what sits behind
the gateway that is not. Cause. Aggregated, per-tier health checks that stop at
the Resolver instead of propagating the health of the actual Referent through
to observability. Fix. Emit which concrete Referent served each request as a
label or an attribute, per dimension 16, so an operator can distinguish "the
gateway is down" from "the gateway is fine and the thing behind it is not."

**Indirection stacking, sometimes called the lasagna anti-pattern in
architecture discussions.** Symptom. Tracing a single request requires reading
through six layers, each of which adds one hop and forwards almost everything
unchanged, and a one-line bug fix touches five files across five services.
Cause. Each layer was added for a genuine reason at the time, but nobody
retired the layers whose reason later disappeared, or new layers were added
by convention rather than by need. Fix. Periodically ask, for each existing
layer, whether the variation it protects against still occurs. Collapse layers
whose variation has not happened in practice and is not credibly coming.

**Service locator disguised as dependency injection.** Symptom. A class
constructs correctly in production but throws a null-reference or
"not registered" error only in certain test configurations, and the actual
dependency the class needs is nowhere visible in its constructor or its type
signature. Cause. The class reaches into a global Resolver at the point of use
rather than declaring its dependency up front, so the coupling to the Resolver
is real but hidden. Fix. Push the resolution to the boundary of the
application, construction time, and pass the resolved Referent in explicitly,
which is the difference between Dependency Injection and Service Locator
covered in dimension 13.

**Unbounded fan-out through a registry.** Symptom. Adding one new implementor
to a plugin registry silently changes behaviour for every existing caller of
the registry, because the registry iterates all registered entries rather than
resolving a single Name to a single Referent. Cause. Conflating "a Resolver
that answers one Name with one Referent" with "a Resolver that broadcasts to
every registered Referent," which are different responsibilities that got
merged into one lookup table. Fix. Keep resolution and broadcast as separate
operations, or name the broadcast explicitly as an Observer relationship rather
than as Indirection.

**Resolving too early and freezing the wrong binding.** Symptom. A worker
process started before a configuration change never picks it up, and restarting
the process is the only fix, even though the system was designed to be
reconfigurable without a restart. Cause. The Resolver was consulted once at
process startup and the result was stored in a field for the lifetime of the
process, defeating the entire purpose of the indirection. Fix. Re-resolve on
every access, or on an explicit signal such as a configuration watch, rather
than once at startup, unless the deployment model genuinely intends a restart
per binding change.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Indirection (Name resolved by an Intermediary) | Direct reference (no intermediary) | Service Locator (global, implicit Resolver) | Dependency Injection (Resolver applied once, at the boundary) | Facade (one simplified entry point, single Referent set) |
|---|---|---|---|---|---|
| Coupling to concrete identity | Low. Client depends on the Name only | High. Client depends on the concrete type or address | Low on paper, high in practice, the locator call site hides the real dependency | Low. Dependency is declared and visible in the constructor or signature | Low to the subsystem behind the facade, but the facade itself is a fixed dependency |
| Substitutability at runtime | High. Re-bind the Name at any time | None. Requires recompiling or redeploying the caller | High, but silently, from any code, at any time | Fixed for the lifetime of the constructed object, changed only by reconstructing it | Fixed. The facade decides internally, the caller cannot substitute |
| Debuggability | Lower. Must resolve the Name to know the destination | Highest. The destination is visible in the source | Lowest. The dependency is invisible until the locator call executes | High. Visible at construction time even though the concrete type is abstracted | High for the facade's own behaviour, opaque for what is behind it |
| Testability | High. Substitute a test double behind the same Name | Low. Requires patching, subclassing, or a test-only build | Low. Tests must configure the global locator and clean it up, which risks test order dependence | Highest. Pass a test double directly into the constructor | Medium. Tests exercise the facade's simplified surface, not the parts behind it |
| Added latency per access | Present, size depends on the mechanism, from a pointer dereference to a network hop | None | Present, plus a hidden global lookup | None after construction | Present only for the facade's own logic, not for a resolution step |
| Explicitness of the dependency | Medium. Declared as a Name or interface | High. Declared as a concrete type | Low. Hidden inside method bodies | High. Declared in the constructor or factory signature | Medium. The facade's surface is explicit, its internals are not |
| Coordinated cutover of many callers at once | Strong. Re-bind the Name once, every caller follows | None. Every call site must be found and changed | Strong, but with no audit trail of who changed what | Requires re-wiring the composition root, but that is a single, reviewable place | Strong for behaviour behind the facade, weak for the facade's own contract |

Reading of the table. Indirection through an explicit Name is the general
mechanism. Direct reference is the right choice when nothing above dimension 4
applies. Service Locator looks like Indirection but trades away
testability and explicitness for global convenience, which is why it is
treated as a near-conflict in dimension 13 rather than as a peer. Dependency
Injection is Indirection with the resolution step deliberately pushed to one
place and one time, trading runtime re-bindability for compile-time visibility
of the dependency. Facade solves a different problem, simplifying a surface
rather than making the underlying identity substitutable, and the two combine
cleanly when the facade itself is reached through an indirection.

## 13. Related and incompatible patterns

- **Proxy.** A specialisation. Every Proxy is a form of Indirection where the
  Resolver forwards to a single, specific Real Subject and matches its
  interface exactly, rather than choosing among several possible Referents.
  See the Proxy entry in this catalog for the remote, virtual, protection, and
  smart-reference varieties.
- **Facade.** A complementary, different-shaped pattern. Facade simplifies a
  wide or awkward surface into a narrow one, it does not by itself make the
  thing behind it substitutable. A Facade is frequently reached through an
  Indirection, for example a service interface resolved by a
  dependency-injection container, but the two solve different problems and
  compose rather than overlap.
- **Adapter.** A related but distinct idea. Adapter changes the shape of an
  interface so two incompatible parties can talk, Indirection changes who a
  party talks to. An Adapter can sit behind an Indirection's Name just as
  easily as a native implementation can, and doing so is common in practice.
- **Dependency Inversion Principle.** The design-level justification for using
  Indirection in object design. The principle states that high-level modules
  should not depend on low-level modules, both should depend on abstractions,
  which is exactly the Client-depends-on-Name-not-Referent structure this entry
  describes, generalised from a single mechanism to a rule for an entire
  codebase's dependency direction.
- **Low Coupling and Protected Variations, GRASP.** Indirection is one of the
  primary mechanisms by which both are achieved in Larman's catalog. Protected
  Variations in particular is explicitly built from Indirection plus
  Polymorphism, wrapping a point of predicted variation behind a stable
  interface.
- **Mediator.** A specific pattern shape where the Intermediary's job is
  specifically to coordinate a set of peer objects that would otherwise
  reference each other directly, replacing many-to-many direct references with
  many-to-one references through the Mediator. It is Indirection applied
  specifically to collapse peer coupling, rather than to make one Referent
  substitutable.
- **Dependency Injection.** A disciplined restriction of Indirection.
  Resolution happens once, at construction, at a single composition root, and
  the resolved dependency is then held directly for the object's lifetime. It
  keeps the substitutability and testability benefits of Indirection while
  giving up runtime re-binding in exchange for static visibility of what
  depends on what.
- **Service Locator.** Conflicts with the spirit of Indirection even though it
  is mechanically an instance of it. A Service Locator is a global, implicit
  Resolver that any code can call from anywhere, which hides the dependency
  from the type signature and from the reader, and makes tests fragile because
  global state must be configured and reset around each test. Where
  Dependency Injection makes the Resolver's use visible and singular, Service
  Locator makes it invisible and pervasive. Martin Fowler's well-known
  discussion of dependency injection contrasts the two along exactly this
  line, favouring injection for the clarity it preserves.
- **Premature abstraction, speculative generality.** A direct anti-pattern
  relationship. Building the Name, the Resolver, and an interface for a
  Referent that will never have a second implementation is Indirection applied
  where dimension 4 says not to, and it is one of the most common causes of
  unnecessary complexity flagged in code review.

## 14. Refactoring path in and out

Introducing indirection into code that currently holds a direct reference.

1. Identify the concrete type or address the caller holds directly, and
   confirm at least one of the applicability conditions in dimension 4 holds,
   not merely that indirection sounds like good practice.
2. Extract the narrowest interface the caller actually uses from the concrete
   type. Do not extract the concrete type's entire public surface, extract only
   the members the caller calls, which keeps the Name small and the future
   substitution honest. This is the object-design instance of Extract
   Interface, see the refactoring family entry.
3. Introduce the Resolver at the smallest possible scope first, a constructor
   parameter, a single factory call, or a single configuration entry. Do not
   reach for a global registry or a dependency-injection container on the
   first pass.
4. Change the caller to depend on the interface, supplying the concrete
   instance through the new Resolver. Run the tests after this step alone,
   before adding a second implementation, so any regression is attributable to
   the mechanical change rather than to new behaviour.
5. Only once a second, genuinely different Referent exists, or a test double is
   genuinely needed, add the second binding. Adding the second binding is the
   moment the indirection starts paying for itself, and adding it
   speculatively before a second Referent exists is the premature-abstraction
   failure from dimension 4.
6. Add the observability signal from dimension 16 at the same time the
   Resolver is introduced, not afterward, so the seam is never opaque from day
   one.

Removing indirection when it stops earning its place. Signals that removal is
warranted include a Resolver with exactly one binding that has never changed
across several release cycles, a Name that every caller in the codebase
resolves to the same Referent, or a Service Locator call site that could be
replaced by a constructor parameter with no loss of flexibility anyone
actually uses.

1. Confirm, across the whole codebase and not just the one call site under
   review, that only one Referent is ever bound to the Name. A search across
   configuration, tests, and feature flags is required here, not a single grep
   of production code.
2. Inline the Resolver's single binding at each call site, replacing
   `resolve(Name)` with the concrete construction or reference directly. This
   is Inline Method or Inline Class from the refactoring family, applied to
   the Resolver.
3. Delete the interface if nothing else in the codebase implements it or
   depends on it polymorphically. Delete the Resolver's registration code for
   that Name.
4. Re-run the full test suite, since removing an indirection removes a seam
   that tests may have relied on for substituting a double, and those tests
   need to be revisited rather than silently left red or silently deleted.

## 15. Testing and verification

Easier because of the pattern.

- A test can substitute a test double behind the same Name the production code
  resolves, without touching the code under test at all, which is the
  foundational reason dependency injection and mocking frameworks both exist.
- Behaviour that depends on which Referent currently answers a Name can be
  tested by re-binding the Name in the test's setup and asserting on the
  resulting behaviour change, rather than by constructing elaborate production
  scenarios.
- A contract test written once against the interface, and run once per
  concrete implementor, verifies every Referent honours the same guarantees the
  Client relies on, catching an implementor that technically compiles but
  violates an unstated assumption.

Harder because of the pattern.

- An end-to-end test exercising the real Resolver, real DNS, a real
  dependency-injection container, or a real routing table, is now testing an
  extra component that a direct reference would not have required at all, and
  that component can itself be a source of test flakiness, particularly for
  network-based resolvers such as DNS or service discovery.
- A regression caused by a stale binding, per dimension 11, is difficult to
  reproduce in a test environment where caches and time-to-live values are
  typically shorter than production, so the failure mode can be entirely
  invisible until it appears live.

Techniques that apply.

- **Fake or in-memory Resolver for unit tests.** Replace the real
  dependency-injection container, DNS resolver, or registry with a minimal
  in-memory map for unit-level tests, so resolution is instant, deterministic,
  and does not touch the network or the filesystem.
- **Contract test against the interface.** One suite written against the Name's
  interface, run once per registered Referent, the same technique described
  for Factory Method's Product abstraction in this catalog, applied here to
  verify every implementor honours the contract the Client depends on.
- **Explicit re-binding assertions.** A test that resolves the Name, re-binds
  it to a different Referent, resolves it again, and asserts the second
  resolution reflects the change, directly verifies that the Resolver is not
  accidentally caching the first binding forever, the failure mode from
  dimension 11.
- **Chaos or fault injection at the Resolver boundary.** For a network-based
  Resolver such as DNS or a service mesh, inject a resolution failure, a
  timeout, or a stale response in an integration test, and assert the Client's
  fallback or error handling behaves correctly, rather than assuming the
  Resolver always succeeds.

## 16. Observability signals

The pattern hides the concrete Referent from the source, exactly as designed,
which means the concrete Referent has to appear in telemetry or an operator
diagnosing an incident cannot answer "what actually served this request."

What to record.

- On every resolution, the Name requested and the concrete Referent identity
  returned, at debug level for high-frequency resolutions and at info level for
  resolutions with real operational weight, such as a DNS lookup for a
  production dependency or a dependency-injection binding chosen by feature
  flag.
- A counter of resolutions labelled by the Name and by the concrete Referent
  returned. The label distribution over time is the single most useful signal
  for spotting a stuck or stale binding, because a healthy rolling migration
  shows the distribution shifting, and a stuck migration shows it flat when it
  should be moving.
- A histogram of resolution latency, labelled by the Resolver mechanism, since
  a DNS lookup, a network hop through a gateway, and an in-process map lookup
  have wildly different acceptable latency budgets and a regression in one
  should not be masked by averaging with the others.
- A gauge or event for every re-binding of a Name to a new Referent, including
  who or what triggered the change, so an incident review can immediately see
  "the binding for this Name changed at this timestamp" as a candidate cause.
- A counter of resolution failures, labelled by Name and by failure class,
  timeout, not-found, or refused, distinct from failures inside whatever the
  resolved Referent does afterward.

A healthy instance on a dashboard. The per-Referent resolution counter shows a
distribution matching the intended rollout or configuration, and it only
changes when a deployment, a feature flag, or an operator action explains the
change. Resolution latency is flat and small relative to the operation the
Client is performing. Re-binding events are rare, deliberate, and always
correlate with a known change. Resolution failures sit near zero.

A failing instance. Resolution latency develops a long tail while direct-call
latency elsewhere in the system stays flat, which localises a slow Resolver
without reading any application code. The per-Referent distribution stops
moving during a rollout that was supposed to shift traffic gradually, which is
the stuck-migration signature. A resolution failure counter climbs while the
Referent's own error rate stays flat, which tells an operator the fault is in
the naming or routing layer, not in the destination, saving an entire class of
misdirected debugging.

## 17. Security and privacy implications

Indirection is not neutral on security the way a purely local design pattern
can be, because the Resolver is, by definition, a decision point that
determines where a request or a piece of data actually goes, and a decision
point is exactly what an attacker targets.

**Name spoofing and cache poisoning.** Whenever the Resolver caches or trusts
an externally supplied mapping from Name to Referent, an attacker who can
influence that mapping redirects every subsequent Client to a Referent they
control. DNS cache poisoning is the textbook instance of this at internet
scale, and the same class of attack applies at smaller scope to any
dependency-injection container, plugin registry, or service-discovery system
that accepts registration from a source that is not fully trusted. The
mitigation is to authenticate and validate the source of any binding before
accepting it, and to prefer signed or otherwise verifiable bindings over
implicit last-writer-wins registration.

**Confused deputy through an over-privileged intermediary.** A Resolver or a
gateway that holds broad credentials on behalf of every Client it serves, and
forwards a request without re-checking the original caller's authorization
against the specific Referent being reached, can be tricked into acting with
more privilege than the original requester actually holds. This is precisely
why an API Gateway that centralises authentication, as described in dimension
8, must also re-propagate or re-check authorization per downstream call rather
than assuming a single perimeter check at the gateway is sufficient for every
service behind it.

**Loss of end-to-end visibility for audit.** Adding an intermediary between two
parties, whether it is a proxy, a gateway, or a name-resolution layer, is
exactly the kind of interception point compliance regimes require to be
logged, because the intermediary is now a place where data transits that
neither the original client nor the original server directly controls. Where
the data crossing the boundary includes personal data, the Resolver's own
logs, caches, and telemetry become part of the data's exposure surface and
must be governed by the same retention and access rules as the data itself,
rather than being treated as mere infrastructure metadata.

**Denial of service through the Resolver as a single point of failure.**
Because every Client of a Name funnels through one Resolver, an attacker who
can exhaust that Resolver's capacity, through a flood of novel Name lookups, a
cache-busting pattern, or simple volume, denies service to every Client of
every Name it serves, not merely to one target. Rate limiting, per-Client
quotas, and a documented fallback behaviour for when resolution itself is
unavailable, rather than assuming resolution always succeeds, are the standard
mitigations, and they belong in the design of the Resolver, not as an
afterthought bolted on after an incident.

On privacy specifically, the pattern is otherwise close to neutral, with one
caveat already stated in dimension 16. Logging the concrete Referent for
observability can itself leak identifying or sensitive information, for
example when a Referent's name encodes a tenant, a region, or a person, and
that log field needs the same handling as any other identifying field rather
than being assumed safe because it looks like infrastructure metadata.

## 18. References

1. Wikipedia contributors. "Indirection." https://en.wikipedia.org/wiki/Indirection
   Verified 2026-08-02. Source for the general definition, the Wheeler and
   Lampson attribution and its contested status, and the "too many layers of
   indirection" corollary in dimension 1.
2. Wikipedia contributors. "GRASP (object-oriented design)."
   https://en.wikipedia.org/wiki/GRASP_(object-oriented_design) Verified
   2026-08-02. Used to confirm the nine-pattern GRASP catalog and Indirection's
   place within it alongside Protected Variations, referenced in dimension 1,
   dimension 9, and dimension 13.
3. Craig Larman. *Applying UML and Patterns. An Introduction to
   Object-Oriented Analysis and Design and Iterative Development*, 3rd
   edition. Prentice Hall, 2004. ISBN 0-13-148906-2. Source of the original
   GRASP formulation of Indirection first published in the 1997 first
   edition, and of its pairing with Polymorphism to achieve Protected
   Variations, cited in dimension 1 and dimension 13. Cited from the
   published catalog description rather than a specific page, since a page
   number for the 1997 first edition could not be independently confirmed
   through a live source at time of writing.
4. P. Mockapetris. RFC 1034, "Domain Names, Concepts and Facilities."
   Internet Engineering Task Force, November 1987.
   https://www.rfc-editor.org/rfc/rfc1034 Verified 2026-08-02. Source for the
   DNS production use in dimension 8 and dimension 9.
5. Linux man-pages project. `mmap(2)` manual page.
   https://man7.org/linux/man-pages/man2/mmap.2.html Verified 2026-08-02.
   Source for the virtual memory production use in dimension 8 and dimension
   9.
6. Kubernetes documentation. "Service."
   https://kubernetes.io/docs/concepts/services-networking/service/ Verified
   2026-08-02. Source for the Kubernetes Service production use in dimension
   8 and dimension 9.
7. Microsoft. ".NET Microservices Architecture for Containerized .NET
   Applications," "The API gateway pattern versus the direct
   client-to-microservice communication."
   https://learn.microsoft.com/en-us/dotnet/standard/microservices-architecture/architect-microservice-container-applications/direct-client-to-microservice-communication-versus-the-api-gateway-pattern
   Verified 2026-08-02. Source for the API Gateway production use, the
   explicit "tier of indirection" language quoted in dimension 8, and the
   Ocelot and Azure API Management examples in dimension 9.

## Code examples

Three languages chosen for genuinely different idiomatic shapes. Go shows
indirection through an interface plus an explicit, swappable binding held in a
struct field, the classic Dependency Injection shape. Python shows indirection
through a name-keyed registry, the shape behind a plugin system or a
dependency-injection container's binding table. TypeScript shows indirection
through a mutable reference cell that can be re-pointed at runtime, the
closest in-process analogue to a DNS record or a page-table entry. Rust and
Java are omitted here in favour of depth on the three above, both would
express the same interface-and-binding shape as Go with no idiomatic
difference worth a fourth listing.

### Go

```go
package main

import "fmt"

// PriceSource is the Name. Callers depend on this, never on a concrete type.
type PriceSource interface {
	Price(sku string) (float64, bool)
}

// Two concrete Referents.
type StaticCatalog struct{ prices map[string]float64 }

func (c StaticCatalog) Price(sku string) (float64, bool) {
	p, ok := c.prices[sku]
	return p, ok
}

type DiscountedCatalog struct {
	inner    PriceSource
	discount float64
}

func (c DiscountedCatalog) Price(sku string) (float64, bool) {
	p, ok := c.inner.Price(sku)
	if !ok {
		return 0, false
	}
	return p * (1 - c.discount), true
}

// Checkout is the Client. It holds the Name, never a concrete catalog.
type Checkout struct {
	source PriceSource
}

func (c *Checkout) Total(skus []string) (float64, error) {
	var total float64
	for _, sku := range skus {
		p, ok := c.source.Price(sku)
		if !ok {
			return 0, fmt.Errorf("unknown sku %s", sku)
		}
		total += p
	}
	return total, nil
}

func main() {
	base := StaticCatalog{prices: map[string]float64{"WIDGET": 9.99, "GADGET": 19.99}}

	// Bind the Name to Referent A.
	checkout := &Checkout{source: base}
	total, _ := checkout.Total([]string{"WIDGET", "GADGET"})
	fmt.Printf("full price %.2f\n", total)

	// Re-bind the Name to Referent B at runtime. Checkout never changes.
	checkout.source = DiscountedCatalog{inner: base, discount: 0.10}
	total, _ = checkout.Total([]string{"WIDGET", "GADGET"})
	fmt.Printf("discounted %.2f\n", total)
}
```

### Python

```python
from typing import Callable, Protocol


class PriceSource(Protocol):
    def price(self, sku: str) -> float | None: ...


class StaticCatalog:
    def __init__(self, prices: dict[str, float]) -> None:
        self._prices = prices

    def price(self, sku: str) -> float | None:
        return self._prices.get(sku)


# The Resolver. a name-keyed registry, the shape behind most plugin systems
# and dependency-injection containers.
_registry: dict[str, Callable[[], PriceSource]] = {}


def register(name: str, factory: Callable[[], PriceSource]) -> None:
    _registry[name] = factory


def resolve(name: str) -> PriceSource:
    if name not in _registry:
        raise LookupError(f"no catalog registered under {name!r}")
    return _registry[name]()


class Checkout:
    def __init__(self, catalog_name: str) -> None:
        # The Client holds a Name, not a concrete catalog.
        self._catalog_name = catalog_name

    def total(self, skus: list[str]) -> float:
        source = resolve(self._catalog_name)
        subtotal = 0.0
        for sku in skus:
            price = source.price(sku)
            if price is None:
                raise ValueError(f"unknown sku {sku}")
            subtotal += price
        return subtotal


if __name__ == "__main__":
    base = StaticCatalog({"WIDGET": 9.99, "GADGET": 19.99})
    register("primary", lambda: base)

    checkout = Checkout("primary")
    print(f"full price {checkout.total(['WIDGET', 'GADGET']):.2f}")

    # Re-bind the name to a different Referent. Checkout is unchanged.
    register("primary", lambda: StaticCatalog({"WIDGET": 8.99, "GADGET": 17.99}))
    print(f"repriced {checkout.total(['WIDGET', 'GADGET']):.2f}")
```

### TypeScript

```typescript
interface PriceSource {
  price(sku: string): number | undefined;
}

class StaticCatalog implements PriceSource {
  constructor(private readonly prices: Map<string, number>) {}
  price(sku: string): number | undefined {
    return this.prices.get(sku);
  }
}

// The Resolver. a mutable cell holding the current binding. This is the
// in-process analogue of a DNS record or a page-table entry, one place that
// re-points every reader at once when it changes.
class Binding<T> {
  constructor(private current: T) {}
  get(): T {
    return this.current;
  }
  rebind(next: T): void {
    this.current = next;
  }
}

// The Client holds the Binding (the Name), never the concrete catalog.
class Checkout {
  constructor(private readonly source: Binding<PriceSource>) {}

  total(skus: string[]): number {
    const catalog = this.source.get();
    let subtotal = 0;
    for (const sku of skus) {
      const price = catalog.price(sku);
      if (price === undefined) {
        throw new Error(`unknown sku ${sku}`);
      }
      subtotal += price;
    }
    return subtotal;
  }
}

const base = new StaticCatalog(new Map([["WIDGET", 9.99], ["GADGET", 19.99]]));
const binding = new Binding<PriceSource>(base);
const checkout = new Checkout(binding);

console.log("full price", checkout.total(["WIDGET", "GADGET"]).toFixed(2));

// Re-bind the Name. Checkout was never touched or reconstructed.
binding.rebind(new StaticCatalog(new Map([["WIDGET", 8.99], ["GADGET", 17.99]])));
console.log("repriced", checkout.total(["WIDGET", "GADGET"]).toFixed(2));
```
