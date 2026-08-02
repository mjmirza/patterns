---
name: Proxy
slug: proxy
family: 01-gof
category: Structural
aliases: [Surrogate, Stub, Ambassador, Placeholder]
first_described: "Gamma, Helm, Johnson, Vlissides 1994"
maturity: canonical
related: [decorator, adapter, facade, composite, flyweight, chain-of-responsibility]
incompatible_with: []
verified: 2026-08-02
---

# Proxy

## 1. Name, aliases, and lineage

The canonical name is Proxy. It appears in the Gang of Four catalog as one of the
seven structural patterns, described in Erich Gamma, Richard Helm, Ralph Johnson
and John Vlissides, *Design Patterns. Elements of Reusable Object-Oriented
Software*, Addison-Wesley, 1994, chapter 4 (Structural Patterns), section Proxy.
The book records **Surrogate** as the alias and states the intent as supplying a
stand-in for another object so that access to it can be controlled. A public
summary of that intent and of the remote, virtual and protection variants is at
[the Wikipedia article on the proxy pattern](https://en.wikipedia.org/wiki/Proxy_pattern),
verified 2026-08-02. That article lists three kinds and omits the smart
reference, so the four-way division below is taken from the book itself rather
than from the summary.

Several other names circulate for the same shape, and each carries a hint about
which variant is meant.

- **Stub.** The distributed-systems name for a remote proxy. gRPC uses it
  directly. The gRPC core concepts page describes a local object on the client
  that implements the same methods as the service, so the caller invokes what
  looks like a local method,
  https://grpc.io/docs/what-is-grpc/core-concepts/ verified 2026-08-02. Java RMI
  uses the same word and even has a `StubNotFoundException` for the case where
  no stub class can be located for an exported remote object, Java SE 21 API
  documentation, `java.rmi` package summary,
  https://docs.oracle.com/en/java/javase/21/docs/api/java.rmi/java/rmi/package-summary.html
  verified 2026-08-02.
- **Ambassador.** The cloud-infrastructure name for an out-of-process proxy that
  handles network concerns for a colocated application. Envoy describes itself
  as a self-contained process running alongside every application server, built
  on the position that the network should be transparent to applications,
  https://www.envoyproxy.io/docs/envoy/latest/intro/what_is_envoy verified
  2026-08-02.
- **Placeholder.** Informal, used for the virtual variant where the proxy holds
  an identity before the expensive object behind it exists.

A naming caution worth stating early. The word proxy in web infrastructure
(forward proxy, reverse proxy, HTTP proxy) and the word proxy in the GoF sense
are the same idea applied at two different scales. A reverse proxy is a network
process standing in for an origin server, and an object proxy is a language-level
object standing in for another object. The forces are close cousins and the
vocabulary transfers, but the implementation techniques share nothing. This entry
covers the object-level pattern and reaches into the infrastructure sense only
where the two genuinely inform each other.

## 2. Problem and context

Some object is expensive, remote, dangerous, or shared, and the code that wants
to use it should not have to know that.

The problem shows up in a codebase in a handful of recognisable shapes.

A document editor holds a page of text and a full-resolution photograph. Opening
the document expands every image into pixels, so opening takes four seconds and
most images are never scrolled into view. The obvious repair is to add a
`loadIfNeeded()` call before every use of the image, which means every call site
now carries loading logic, and one forgotten call site is a null dereference in
production.

A service calls another service over the network. The call site is written as
`inventory.reserve(sku, qty)` because that reads well, but underneath it needs a
timeout, a retry budget, a circuit breaker, tracing headers, and serialisation.
Putting those into the caller couples business logic to transport concerns and
repeats them at every call site.

An administrative object exposes `delete()` and `export()`. Some callers are
allowed to call them and some are not. The check can go inside `delete()`, but
then the domain object knows about roles and sessions, and the check has to be
repeated in every method the same way, forever, including in methods added next
year by somebody who forgets.

A large immutable configuration table is loaded once and shared by a thousand
request handlers. Any handler that mutates it corrupts every other handler. The
type system offers no way to hand out a read-only view of a mutable type without
copying it.

The unifying context is this. There is a well-defined interface, there is a real
object that implements it, and there is a concern that has to sit between the
caller and that object without either of them being rewritten. The caller must
keep believing it holds the real object, because rewriting every caller is the
cost the pattern exists to avoid. That belief is what makes the pattern work and
also what makes its failure modes surprising, since a proxy that behaves
differently from the subject in some corner breaks an assumption nobody wrote
down.

## 3. Forces

The pattern balances the following competing pressures.

- **Coupling.** Favoured strongly. The caller depends only on the shared
  interface. The concern the proxy implements (loading, access control,
  transport, counting) is invisible to the caller and can change without
  touching it.
- **Latency.** Mixed, and the direction depends on the variant. A virtual proxy
  moves cost off the critical path at startup and onto the first access, which
  improves perceived latency and worsens tail latency for the unlucky first
  caller. A remote proxy converts a nanosecond call into a millisecond one while
  keeping the syntax of a nanosecond call, which is the single most dangerous
  property of the pattern. A caching proxy improves latency after the first hit.
- **Cognitive load.** Sacrificed. The source line `user.getName()` no longer
  tells the reader whether that touches memory, a database, or a data centre on
  another continent. A reader has to know the wiring to know the cost.
- **Consistency.** Favoured for protection and smart-reference variants, since
  every access funnels through one place that cannot be bypassed by a forgetful
  caller. Sacrificed for identity, because a proxy is not equal by reference to
  its subject and any code relying on reference equality breaks.
- **Operability.** Favoured. A proxy is the natural home for logging, metrics,
  and tracing, because it sees every call and owns no domain logic.
- **Cost.** Favoured for memory in the virtual variant, since objects that are
  never touched are never built. Sacrificed for total object count, because
  every subject now has a companion.
- **Team topology.** Favoured. Platform teams own proxies (transport, auth,
  caching) while product teams own subjects, and the interface is the contract
  between them. This is exactly why the sidecar deployment model exists at the
  infrastructure scale.
- **Testability.** Favoured for the subject, which stays free of cross-cutting
  concerns, and sacrificed for the composed system, since a bug can now live in
  the proxy, in the subject, or in the interaction between them.

The pattern gives up transparency of cost and transparency of identity. Those two
sacrifices explain most of dimension 11.

## 4. Applicability and non-applicability

Reach for Proxy when the following hold. The GoF book organises the applicability
around four named variants, and each answers a different question.

- **Remote proxy.** The subject lives in another address space and the caller
  should be written as though it does not. The proxy owns marshalling, transport,
  retries, and the mapping of transport failures onto the interface's error
  model. gRPC stubs and Java RMI stubs are this variant, generated rather than
  handwritten.
- **Virtual proxy.** The subject is expensive to create and often not used. The
  proxy holds identity and metadata cheaply, and materialises the subject on
  first real access. Hibernate lazy associations and Django's `SimpleLazyObject`
  are this variant.
- **Protection proxy.** Different callers deserve different access to the same
  subject. The proxy holds the policy so the subject holds none.
  `Collections.unmodifiableList` is a degenerate but honest instance, where the
  policy is the constant "no writes".
- **Smart reference.** Something extra has to happen on every access. Reference
  counting, lock acquisition, first-use loading of a persistent object, usage
  metering, or invalidation of a weak referent. Python's `weakref.proxy` is this
  variant, and so is every method-level metrics wrapper that calls itself a
  proxy.

Two further cases earn the pattern in modern practice, both descendants of the
above.

- **Cross-cutting concern injection at the boundary.** Transactions, caching,
  authorisation and retry applied uniformly to a service interface without
  editing the service. This is what Spring AOP builds, and what
  `System.Reflection.DispatchProxy` exists for on .NET,
  https://learn.microsoft.com/en-us/dotnet/api/system.reflection.dispatchproxy
  verified 2026-08-02.
- **Interception for reactivity or observation.** The proxy reports reads and
  writes to a dependency tracker. Vue 3 builds its reactivity on the JavaScript
  `Proxy` object for exactly this,
  https://vuejs.org/guide/extras/reactivity-in-depth.html verified 2026-08-02.

Non-applicability. Do NOT reach for Proxy in these cases, and the reason matters
more than the rule.

- **The caller can be told the truth.** If the caller can reasonably be handed a
  `Future`, a `Lazy<T>`, an `Optional`, or an explicit `load()` step, do that.
  Making an expensive or fallible operation look like a field read hides
  information the caller needs to make good decisions about batching, timeouts
  and error handling. An explicit type is the honest design and a proxy is the
  compatible one, and the choice between them is a real trade, not a formality.
- **The subject's interface leaks its locality.** A remote proxy over an
  interface with a chatty, fine-grained API produces a call per property. The
  interface has to be redesigned coarse-grained before a remote proxy is safe,
  otherwise the proxy silently converts one logical operation into forty round
  trips.
- **Reference identity is part of the contract.** If callers compare with
  reference equality, use the object as a map key, take a lock on it, or rely on
  a runtime type test against a concrete class, a proxy breaks them. Vue's
  documentation states plainly that the proxy returned by `reactive()` has a
  different identity from the original under strict equality (source above,
  verified 2026-08-02).
- **The concern belongs to the subject.** Validation of the subject's own
  invariants is not a cross-cutting concern. Moving it into a proxy means an
  unproxied construction path violates the invariant, and there is always an
  unproxied construction path eventually.
- **There is exactly one caller.** One caller means the concern can live at the
  call site, plainly visible, with no new type. A proxy earns its place when the
  concern must apply uniformly across many callers who cannot be trusted to
  remember it.
- **The language already gives you the hook.** In Python a descriptor or
  `__getattr__` on the class itself is often cheaper than a wrapper object. In
  Rust, `Deref` plus a smart pointer type covers most smart-reference uses
  without a parallel type. Building a wrapper class where the language has a
  first-class facility is extra machinery for the same behaviour.
- **You need to add behaviour, not control access.** That is Decorator, and the
  distinction is developed in dimension 13.
- **The subject is a value.** Proxying an immutable value object buys nothing,
  because none of the four motivating concerns apply to something with no
  identity, no cost and no mutation.

## 5. Structure

Three participants, named by the role each plays.

- **Subject.** The interface both the real object and the proxy implement. It is
  the only type the client names. Its design decides whether the pattern is
  viable, because the proxy can only intercept what the interface declares. A
  Subject with public fields or final methods cannot be fully proxied.
- **RealSubject.** The object that does the actual work. It is written with no
  knowledge that a proxy exists, and that ignorance is the payoff. If RealSubject
  has to cooperate with the proxy, the design has drifted toward Decorator or
  toward an ordinary collaborator.
- **Proxy.** Implements Subject, holds a reference to RealSubject, and controls
  access to it. The reference may be direct, lazy, remote, or absent until first
  use. The proxy forwards, and around the forwarding it does its one job.

Relationships. The client holds a Subject. The proxy holds a Subject reference
too, or a means of producing one. RealSubject holds nothing. The composition is
one deep in the classical form, though nothing stops several proxies stacking,
and in practice they do. A Spring bean can carry a transaction proxy over a
caching proxy over a security proxy, each unaware of the others.

The variant that changes the shape is who owns the RealSubject's lifetime. In a
virtual proxy, the proxy creates the RealSubject and therefore owns it. In a
protection proxy, the RealSubject is normally handed in from outside and the
proxy owns nothing. That difference is the clearest structural line between
Proxy and Decorator, and dimension 13 develops it.

## 6. ASCII structure diagram

```
                       +-----------------------+
        client ------->|       Subject         |   the only type
        holds this     |-----------------------|   the client names
                       | + request()           |
                       +-----------------------+
                            ^             ^
                            |             |
                 implements |             | implements
                            |             |
   +--------------------------+       +-----------------------+
   |          Proxy           |       |     RealSubject       |
   |--------------------------|       |-----------------------|
   | - subject                |------>| + request()           |
   | + request()              | holds | (knows nothing of the |
   |   preCheck()             |  or   |  proxy, by design)    |
   |   subject.request()      | makes +-----------------------+
   |   postAction()           |
   +--------------------------+

   Virtual proxy.     subject is null until the first request().
   Protection proxy.  subject is injected, preCheck() may throw.
   Remote proxy.      subject is a channel, request() is a round trip.
   Smart reference.   postAction() counts, releases a lock, invalidates.
```

## 7. Dynamics

The runtime behaviour that matters is not the forwarding, which is trivial. It is
what happens on the first call and what happens when the proxy declines. The
sequence below shows a virtual proxy that also enforces access, which is the
common composed case.

```
Client            Proxy              Policy         RealSubject
  |                 |                  |                 |
  |-- request() --->|                  |                 |
  |                 |-- allowed()? --->|                 |
  |                 |<-- false --------|                 |
  |<-- DENIED ------|                  |                 |
  |                 |   (RealSubject never constructed)  |
  |                 |                  |                 |
  |-- request() --->|                  |                 |
  |                 |-- allowed()? --->|                 |
  |                 |<-- true ---------|                 |
  |                 |                                    |
  |                 |-- subject is null, so construct -->|
  |                 |        (expensive, one time)       |
  |                 |<-- instance -----------------------|
  |                 |-- request() ---------------------->|
  |                 |<-- result -------------------------|
  |<-- result ------|                                    |
  |                 |                                    |
  |-- request() --->|   second call, subject cached      |
  |                 |-- request() ---------------------->|
  |<-- result ------|<-- result -------------------------|
```

Three timing properties are worth stating because each is a production incident
in waiting.

First, the first call pays for construction and every later call does not. On a
latency histogram that produces a bimodal distribution, not a long tail, and
percentile alerts tuned on the mean will not see it.

Second, when several threads reach an uninitialised virtual proxy at once, the
naive implementation constructs the subject several times. If construction is
pure that is waste. If construction opens a connection or writes a row, it is a
correctness bug. The repair is a lock or a compare-and-set on the field, and the
cost of that lock is paid on every access unless the field is read first without
it.

Third, the proxy's lifetime and the subject's lifetime can diverge. A lazy
database proxy that outlives the session that could have loaded it fails on
access rather than at construction, which is precisely what Hibernate's
`LazyInitializationException` reports. Its Javadoc describes it as an attempt to
access unfetched data outside the context of an open stateful session,
https://docs.hibernate.org/orm/6.6/javadocs/org/hibernate/LazyInitializationException.html
verified 2026-08-02. The failure surfaces in the view layer, far from the code
that closed the session.

<!-- BODY -->
