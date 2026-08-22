---
name: Proxy
slug: proxy
family: 01-design-patterns-gof
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

## 8. Implementation variants

**Handwritten static proxy.** One class per proxied interface, forwarding each
method explicitly. Readable, debuggable, and the stack trace names the proxy.
The cost is that every method added to the Subject must be added to the proxy,
and a forgotten method silently means an unproxied call path. Suitable when the
interface is small and stable.

**Generated proxy at build time.** A code generator or annotation processor
emits the forwarding class from the interface. gRPC stubs work this way. Keeps
the static form's debuggability and removes the drift risk, at the cost of a
build step and generated code in the tree.

**JDK dynamic proxy.** `java.lang.reflect.Proxy.newProxyInstance` builds a class
at runtime implementing a given list of interfaces, dispatching every call to an
`InvocationHandler.invoke(proxy, method, args)`. The Javadoc is explicit that
every entry in the interfaces array must be an interface and not a class,
https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/reflect/Proxy.html
verified 2026-08-02. One handler covers every method, so nothing drifts, and the
price is reflective dispatch, boxed arguments, and stack traces naming a
generated type such as `$Proxy17`.

**Subclass proxy through bytecode generation, the CGLIB style.** When the subject
has no interface, a subclass is generated at runtime and every non-final method
is overridden to route through an interceptor. Spring documents the split
plainly. If the target implements at least one interface a JDK dynamic proxy is
used and all implemented interfaces are proxied, otherwise a CGLIB proxy is
created as a runtime-generated subclass of the target type,
https://docs.spring.io/spring-framework/reference/core/aop/proxying.html
verified 2026-08-02. The subclass form works on classes but inherits three hard
limits. A `final` class cannot be subclassed, a `final` method cannot be
overridden and therefore silently escapes interception, and the generated
subclass runs the target's constructor. Those limits produce failure modes that
look like the advice was never applied, because it was not.

**Interception facility in the standard library.** .NET offers
`DispatchProxy.Create<T, TProxy>()`, which produces an instance implementing an
interface and routes every call to a single `Invoke(MethodInfo, object[])`
(source in dimension 4, verified 2026-08-02). Same trade as the JDK dynamic
proxy, meaning uniform coverage and reflective cost, on interfaces only.

**Language-level metaobject proxy.** JavaScript's `Proxy` intercepts fundamental
object operations rather than method calls, with traps for `get`, `set`, `has`,
`deleteProperty`, `ownKeys`, `apply`, `construct` and more,
https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Proxy
verified 2026-08-02. This is more powerful than method interception because it
covers property access, which is what makes reactivity systems possible. Python
reaches similar ground with `__getattr__` and `__getattribute__`, though
`__getattr__` fires only for attributes not found normally, so a wrapper that
predefines an attribute stops proxying it.

**Smart pointer as proxy.** In C++ and Rust, operator overloading and `Deref` let
a value behave like the thing it points at while doing reference counting or
borrow tracking. This is the smart-reference variant with no separate interface
and no virtual dispatch, and it is why Rust code rarely names the pattern even
while using it constantly.

**Out-of-process proxy.** The sidecar. The proxy is not an object but a process
on localhost, and the interface is the wire protocol. Envoy is the reference
implementation of this shape (source in dimension 1, verified 2026-08-02). The
trade is that it is language-agnostic and independently deployable, in exchange
for a network hop and a second thing to operate.

**Lazy value holder rather than a full proxy.** Wrap the subject in a
single-method supplier and let the caller see the laziness. Cheapest form, and
the one to prefer when the caller can be changed. It is not the pattern, and
saying so is more useful than pretending it is.

## 9. Known production uses

**Java standard library, `java.lang.reflect.Proxy`.** The runtime creates a class
implementing a supplied list of interfaces, with every invocation dispatched to
an `InvocationHandler`. This is the foundation under most Java interception
libraries, including Spring's interface-based AOP and many JDBC and JPA
wrappers. Java SE 21 API documentation,
https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/reflect/Proxy.html
verified 2026-08-02.

**Spring AOP.** Spring creates a proxy per advised bean, using a JDK dynamic
proxy when the target implements an interface and a CGLIB subclass otherwise,
and routes matched method calls through the configured advice. The proxying
mechanisms page describes both paths and the self-invocation consequence in
detail,
https://docs.spring.io/spring-framework/reference/core/aop/proxying.html
verified 2026-08-02.

**Hibernate ORM lazy associations.** A lazy many-to-one association is
represented by a proxy that carries the identifier and loads the rest on first
access to any other property. `Session.getReference` returns such a reference
without hitting the database, and access outside an open session raises
`LazyInitializationException`. Hibernate ORM 6.6 Javadoc,
https://docs.hibernate.org/orm/6.6/javadocs/org/hibernate/LazyInitializationException.html
verified 2026-08-02, and the Hibernate ORM 5.2 Fetching chapter,
https://docs.hibernate.org/orm/5.2/userguide/html_single/chapters/fetching/Fetching.html
verified 2026-08-02.

**Vue 3 reactivity.** `reactive()` returns a JavaScript `Proxy` whose `get` trap
records a dependency and whose `set` trap triggers effects. The reactivity in
depth page states that proxies are used for reactive objects and shows the
`track` and `trigger` skeleton,
https://vuejs.org/guide/extras/reactivity-in-depth.html verified 2026-08-02.

**gRPC client stubs.** The generated stub implements the same methods as the
service, so a caller invokes a local object and the stub performs marshalling
and transport. gRPC core concepts,
https://grpc.io/docs/what-is-grpc/core-concepts/ verified 2026-08-02.

**Envoy as a sidecar.** A separate process running beside every application
server, taking over routing, retries, TLS and observability so the application
sees only localhost. Envoy documentation, What is Envoy,
https://www.envoyproxy.io/docs/envoy/latest/intro/what_is_envoy verified
2026-08-02.

**Java Collections unmodifiable views.** `Collections.unmodifiableList` returns a
view whose queries read through to the backing list and whose mutations raise
`UnsupportedOperationException`. That is a protection proxy with a constant
policy. Java SE 21 API documentation, `java.util.Collections`,
https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Collections.html
verified 2026-08-02.

**Python `weakref.proxy`.** Returns a proxy that behaves like the referent in
most contexts while holding only a weak reference, and raises `ReferenceError`
when an attribute is accessed after the referent has been collected. Python 3
standard library documentation, `weakref`,
https://docs.python.org/3/library/weakref.html verified 2026-08-02.

**Django `SimpleLazyObject` for `request.user`.** Django's `LazyObject` is
documented in source as a wrapper that delays instantiation of the wrapped
class, and `SimpleLazyObject` builds one from any callable. The authentication
middleware uses it so that a request which never touches the user performs no
user query. Django source documentation for `django.utils.functional`,
https://docs.djangoproject.com/en/4.2/_modules/django/utils/functional/ verified
2026-08-02.

**.NET `System.Reflection.DispatchProxy`.** A standard-library facility for
instantiating proxy objects and handling their method dispatch, with every call
on the generated type routed to `Invoke`. Microsoft .NET API documentation,
https://learn.microsoft.com/en-us/dotnet/api/system.reflection.dispatchproxy
verified 2026-08-02.

## 10. Consequences

Positive.

- The subject stays free of concerns it does not own. Transport, authorisation,
  caching and instrumentation live outside the domain object, which keeps the
  domain object small and testable in isolation.
- The client is untouched. Introducing a proxy into a running system requires a
  change at the wiring site and nowhere else, which is why the pattern is the
  standard retrofit for adding a cross-cutting concern to code you cannot edit.
- Expensive work becomes optional. Objects nobody touches are never built, which
  turns startup cost into per-use cost and often into no cost at all.
- Access control cannot be forgotten, because there is one path to the subject
  and it goes through the check.
- Every call passes one place, which makes the proxy the correct home for
  metrics, tracing and rate limiting.
- The pattern gives a stable seam between teams and between processes. The
  interface is the contract, and either side can be replaced behind it.

Negative.

- Cost becomes invisible at the call site. A property read that performs a query
  or a network round trip is the leading cause of accidental N+1 behaviour, and
  the source line gives no warning.
- Identity breaks. The proxy is not the subject by reference, the runtime type is
  a generated one, and reference equality, identity hashing, locking and type
  tests against a concrete class all behave differently from the unproxied case.
- Stack traces and debugging get worse. Generated frames such as a `$Proxy` class
  or a CGLIB subclass appear between the caller and the real method, and a
  breakpoint in the subject is reached through machinery nobody wrote.
- Interception is partial by construction. Anything the interface does not
  declare escapes the proxy. Field access, `final` methods, private calls, and
  self-invocation all bypass it silently, which is worse than failing loudly.
- Latency becomes bimodal rather than uniform, which defeats naive alerting.
- There is one more object per subject, with its own lifecycle bugs, and it is
  now possible for the proxy to outlive the resources the subject needs.
- Serialisation is a trap. Serialising a proxy either serialises the machinery or
  forces initialisation of a subject the caller never wanted, and both outcomes
  surprise people.

## 11. Failure modes and misuse

**Spring AOP self-invocation silently skips the proxy.** Symptom. A method
annotated `@Transactional` or `@Cacheable` behaves as if the annotation is not
there. No exception, no warning, no log line. Writes commit individually instead
of rolling back together, the cache never fills, and the retry advice never
fires. The behaviour appears only when the method is reached from another method
of the same class, so a controller calling it directly works and an internal call
does not, which makes the bug look intermittent and environment-dependent. Cause.
The container hands the caller a proxy, not the target. The proxy delegates to
the target, and from that moment the target's own reference points at the target,
so an internal call is an ordinary virtual call that never touches the proxy.
Spring documents this directly, stating that once the call reaches the target
object, any method calls it makes on itself are invoked against the `this`
reference and not the proxy, with the consequence that self invocation does not
give the advice a chance to run
(https://docs.spring.io/spring-framework/reference/core/aop/proxying.html
verified 2026-08-02). The transaction chapter repeats it for `@Transactional`,
stating that in proxy mode only external method calls coming in through the
proxy are intercepted, so self-invocation does not lead to an actual transaction
at runtime even if the invoked method is marked
(https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/annotations.html
verified 2026-08-02). Fix, in order of preference. Move the annotated method into
a separate bean and inject it, so the call crosses a proxy boundary. Or
restructure so the entry point carries the annotation rather than an inner
helper. Or switch to AspectJ mode, where the target class is woven and there is
no proxy at all, which the same page recommends when self-invocations must be
advised. As a last resort Spring documents `AopContext.currentProxy()` and
describes it as highly discouraged, since it couples the class to Spring AOP and
makes the class aware that it is being advised. Detection. Write one integration
test per advised method that exercises the internal call path, and assert the
observable effect such as a rollback or a cache hit count, rather than asserting
that the annotation is present.

**Final method or final class defeats the subclass proxy.** Symptom. Advice
works on some methods of a class and not others, with no pattern the reader can
see, or bean creation fails at startup with a message about being unable to
subclass a final class. Cause. CGLIB style proxies override methods, and a
`final` method cannot be overridden, so the generated subclass inherits it
unchanged and calls go straight to the original. Kotlin makes this common by
default, since Kotlin classes and members are final unless declared `open`. Fix.
Remove `final`, or extract an interface so the JDK dynamic proxy path is used,
or apply the Kotlin all-open compiler plugin for the annotated classes.
Detection. A startup-time assertion that every bean carrying the annotation is
actually proxied, plus a test that calls each advised method.

**The N+1 query storm from lazy proxies.** Symptom. A page that renders a list of
one hundred orders issues one hundred and one database queries. Latency is fine
in development against ten rows and unacceptable in production, and the
application logs show a burst of near-identical single-row selects that differ
only by identifier. Cause. Each element of the collection holds a lazy proxy for
its associated entity, and the render loop touches one property on each, which
initialises each proxy with its own query. The Hibernate Fetching chapter names
this directly, warning that `FetchMode.SELECT` can lead to N+1 query issues and
that forgetting to join-fetch eager associations produces a secondary select for
each one
(https://docs.hibernate.org/orm/5.2/userguide/html_single/chapters/fetching/Fetching.html
verified 2026-08-02). Fix. Fetch what the view needs in one query with a join
fetch or a projection into a data-transfer object, which the same page calls the
better alternative most of the time. Where the access pattern genuinely cannot be
known in advance, batch the initialisation. Hibernate's `@BatchSize` specifies a
maximum batch size for batch fetching of the annotated entity or collection, so
uninitialised proxies are loaded in groups with an `IN` list rather than one at a
time,
https://docs.hibernate.org/orm/6.6/javadocs/org/hibernate/annotations/BatchSize.html
verified 2026-08-02. Detection. Assert a query count around the request in an
integration test, and alert on queries-per-request in production. A latency
alert will not catch this until it is already bad.

**Access after the proxy's context is gone.** Symptom. A template or serialiser
throws while rendering, with a stack trace pointing at the view layer and not at
the code that caused it. In Hibernate this is `LazyInitializationException`, and
in Python it is `ReferenceError` from a `weakref.proxy` whose referent has been
collected (Python documentation, source in dimension 9, verified 2026-08-02).
Cause. The proxy was handed across a boundary that outlived the resource it needs
to initialise, which is the session, the request scope, or the strong reference.
Fix. Initialise before crossing the boundary, or do not cross it. Map to a
transfer object at the edge of the session, or keep a strong reference for the
lifetime of the use. The general repair is to make the boundary explicit rather
than to widen the resource's lifetime, since widening it converts an exception
into a connection leak.

**Reference identity assumptions break.** Symptom. An object put into a hash set
cannot be found again, an equality comparison against a freshly loaded entity
returns false, or a synchronized block fails to exclude because two callers lock
two different wrappers. Cause. The proxy is a distinct object with a distinct
identity, and identity-based operations see the wrapper. Vue's documentation
states the same property for its proxies, that the returned object behaves like
the original but has a different identity under strict equality (source in
dimension 4, verified 2026-08-02). Fix. Give the Subject a value-based equality
and hash keyed on the domain identifier and make the proxy delegate them. Never
lock on an object that might be proxied, lock on a private final field or a
dedicated lock object.

**Thread-unsafe lazy initialisation.** Symptom. Duplicate rows, two open
connections, or a doubled counter under load, which never reproduces in a
single-threaded test. Cause. Two threads find the subject field null at the same
time and both construct. Fix. Guard the construction with a lock or a
compare-and-set, and make construction idempotent where it can be. Detection. A
concurrency test that hammers first access from many threads and asserts the
construction count is one.

**The proxy grew a brain.** Symptom. A bug is reported against business
behaviour and the code that decides it turns out to live in a class named
`SomethingProxy`, which also caches, retries and rewrites arguments. Cause.
Incremental additions, each locally reasonable, to a class whose job was
forwarding. Fix. Split it. One proxy per concern, composed, or move the domain
logic back into the subject where it belongs. A proxy that changes results rather
than controlling access has become a Decorator, and calling it by the right name
makes the next change easier.

**Unbounded caching inside a proxy.** Symptom. Heap grows monotonically in a
long-running process, and a heap dump shows the retention path running through a
map inside a proxy. Cause. A caching proxy added without an eviction policy or a
size bound. Fix. Bound the cache, set a time to live, and export hit rate and
entry count as metrics.

**Everything is proxied.** Symptom. Startup time grows steadily as the
application ages, thousands of generated classes appear in the metaspace or its
equivalent, and stack traces are unreadable. Cause. A blanket pointcut such as
"all public methods in the service package", applied for one concern and then
never narrowed. Fix. Narrow the pointcut to the methods that genuinely need the
advice, and prefer explicit annotation over a package-wide expression, so the
proxied set is visible in the source.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Proxy | Decorator | Adapter | Facade | Explicit Lazy or Future type | Sidecar process |
|---|---|---|---|---|---|---|
| Interface seen by client | Identical to subject | Identical to component | Different by design | New, narrower | Different, laziness visible | Wire protocol |
| Primary intent | Control access | Add responsibility | Convert interface | Simplify a subsystem | Defer a value, visibly | Offload network concerns |
| Client awareness | None, that is the point | Usually deliberate composition | Aware, the shapes differ | Aware, calls the facade | Fully aware | None at the code level |
| Lifetime of the wrapped object | Often owned by the proxy | Supplied by the client | Supplied by the client | Owned by the facade | Owned by the holder | Separate process |
| Coupling to concrete types | Low. Interface only | Low. Interface only | Medium. Knows both sides | Medium. Knows the subsystem | Low | None. Protocol only |
| Cost transparency | Poor. Hides cost | Fair. Adds visible behaviour | Good | Fair | Strong. Type states the cost | Poor in code, good on the wire |
| Latency added | One indirect call, or a round trip | One indirect call per layer | One indirect call | Usually none | None until forced | Network hop plus process |
| Stacking | Works, and gets confusing | Designed for it | Rarely stacked | Not stacked | Composes as values | Rarely stacked |
| Operability | Strong. One interception point | Fair | Weak | Weak | Fair | Strongest. Owns telemetry |
| Cognitive load | Medium to high. Invisible machinery | Medium. Visible composition | Low | Low | Low. Explicit | High. Two runtimes to operate |
| Testability of the wrapped object | Strong. Stays clean | Strong | Strong | Medium | Strong | Strong |
| Fits data-driven policy | Strong. Policy inside the proxy | Weak | Not applicable | Not applicable | Weak | Strong. Config-driven |

Reading of the table. Proxy wins when the caller must not change and the concern
must apply without exception. Decorator wins when the caller is composing
behaviour on purpose and wants to see it in the wiring. Adapter wins when the two
interfaces genuinely differ and no amount of forwarding hides that. Facade wins
when the problem is that a subsystem is hard to use rather than that access to it
needs control. An explicit lazy or future type wins whenever the caller can be
changed, because honesty about cost beats compatibility with a signature. A
sidecar wins when the concern is network-shaped and several languages are in
play, and it loses when the extra process is more operational weight than the
problem justifies.

## 13. Related and incompatible patterns

- **Decorator.** The closest neighbour and the one most often confused with it.
  The structures are indistinguishable on a class diagram. Both implement the
  component interface and both hold a reference to it. Three things separate
  them in practice. Intent, since Decorator adds behaviour the caller wants and
  Proxy controls access the caller may not know about. Lifetime, since a
  decorator is handed an already-built component by a client that chose to wrap
  it, while a proxy frequently creates, finds, or connects to its subject and
  therefore owns it. Composition, since decorators are designed to stack and the
  order is part of the design, while a proxy is normally singular and stacking
  proxies is an emergent property rather than an intent. A practical test. If the
  client wrote the wrapping expression on purpose and could remove it to get less
  behaviour, it is a Decorator. If the client received the wrapper from a
  container, a mapper, or a factory and cannot tell it apart from the real
  object, it is a Proxy.
- **Adapter.** Different problem. Adapter changes the interface because the two
  sides do not fit. Proxy keeps the interface identical because the whole value
  is that the client is unaffected. A class doing both is common and should be
  named for whichever concern is the larger one.
- **Facade.** Facade offers a new, smaller interface over several objects. Proxy
  offers the same interface over one. Facade is not required to be substitutable
  for anything, which is the latitude that makes it a different pattern.
- **Flyweight.** Composes well. A flyweight factory hands out shared intrinsic
  state, and a proxy is a natural place to hold the extrinsic state per client
  while forwarding to the shared instance.
- **Composite.** Composes well. A virtual proxy for a subtree lets a large
  composite load incrementally, which is how file browsers and scene graphs
  handle large trees.
- **Chain of Responsibility.** Stacked proxies form a chain, and the two patterns
  meet in interceptor pipelines. When there are more than two or three concerns,
  modelling them as an explicit chain with an ordered list is clearer than
  nesting proxies, because the order becomes data rather than construction
  sequence.
- **Singleton.** Conflicts in practice. A proxy that resolves its subject from a
  process-wide singleton hides the dependency and makes tests order-dependent.
  Inject the subject or a supplier instead.
- **Service Locator.** Actively conflicts for the same reason. A proxy that
  reaches into a global registry to find its subject is harder to reason about
  than one holding a reference, and it defeats the seam the pattern was adopted
  for.
- **Dependency injection containers.** Largely the delivery mechanism for the
  pattern in application code rather than an alternative to it. The container is
  what makes proxying invisible, since it substitutes the proxy for the subject
  at wiring time. That invisibility is what produces the self-invocation failure
  in dimension 11.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. The general shape is
Extract Interface followed by Introduce Wrapper. Ordered steps.

1. Confirm the subject already has, or can be given, an interface covering every
   member the clients use. If clients touch public fields or call methods the
   interface cannot declare, fix that first, since a partial interface produces a
   partial proxy and a partial proxy is the failure in dimension 11.
2. Extract the interface from the concrete class. Start with only the members
   clients call. Run the tests.
3. Change every client declaration to the interface, leaving construction alone
   for now. Run the tests. At this point nothing has been proxied and the code is
   already better, which is a reasonable place to stop if the proxy turns out to
   be unnecessary.
4. Move construction to a single place, a factory or a container registration.
   This is the site the proxy will later be inserted at, and consolidating it is
   the step that makes the change small.
5. Write the proxy implementing the interface and forwarding every method with no
   added behaviour. Run the tests. A pure forwarding proxy should be invisible,
   and if any test fails now, the failure is an identity or serialisation
   assumption and it is better to find it here than after the concern is added.
6. Insert the proxy at the single construction site. Run the tests again.
7. Add the one concern the proxy exists for. One concern. If a second is needed,
   write a second proxy and compose them.
8. Add the observability from dimension 16 in the same change, since a proxy
   without telemetry is a place where cost hides.

Removing the pattern when it stops earning its place. Signals include a proxy
whose concern is now handled elsewhere (a gateway that moved to a sidecar, a
lazy load that is now always needed), a proxy that forwards everything and adds
nothing, and a proxy that has accumulated domain logic.

1. Establish what the proxy actually does today by reading it, not by trusting
   its name. A proxy that adds behaviour is a Decorator and removing it changes
   results.
2. If the concern is genuinely dead, delete the proxy at the construction site
   and run the tests. The interface can stay, since it is useful on its own.
3. If the concern moved elsewhere, verify the new home covers every path the
   proxy covered before deleting, including the paths the proxy covered by
   accident.
4. If the proxy grew domain logic, move that logic into the subject first, as a
   separate commit with its own tests, then delete the forwarding shell.
5. If the laziness is no longer worth it, replace the lazy field with eager
   construction and measure. Latency should get worse at startup and better at
   the first access, and if neither moves, the laziness was never paying.
6. Delete the interface last, and only if nothing else uses it. Interfaces
   extracted for a proxy usually turn out to be useful for tests, so removing
   them is rarely the win it appears to be.

## 15. Testing and verification

Easier because of the pattern.

- The subject can be tested with no infrastructure at all, since the transport,
  authorisation and caching live outside it. This is the main payoff and it
  should be visible as a fast, dependency-free unit test suite for the domain.
- The proxy can be tested against a hand-written fake subject that records calls,
  which gives a precise assertion on forwarding without a mocking library.
- Policy is testable in isolation, because a protection proxy's decision is a
  pure function of the caller and the operation.
- Laziness is directly assertable. Construct the proxy, assert the subject was
  not built, touch it, assert it was built exactly once.

Harder because of the pattern.

- The composed system needs its own tests, because a fault can live in the proxy,
  in the subject, or in the interaction. Passing unit tests on both sides prove
  less than they appear to.
- Anything that bypasses the proxy is invisible to a test written against the
  proxy. The self-invocation failure passes every unit test of the target class
  and every unit test of the advice.
- Identity-dependent behaviour has to be tested against a proxied instance
  specifically, since the unproxied instance behaves correctly and the proxied
  one does not.

Techniques that apply.

- **Transparency contract test.** Run the same test suite twice, once against the
  bare subject and once against the proxy wrapping it, and assert identical
  observable behaviour for every method that the proxy is not supposed to change.
  This is the highest-value test for a proxy and it catches forgotten methods,
  wrong exception translation, and accidental behaviour changes in one go.
- **Query-count assertion.** Wrap the unit of work in a counter over the data
  source and assert an exact number. This is the only reliable defence against
  the N+1 failure, because latency assertions pass on small fixtures.
- **Construction-count spy.** A test-only subject factory that increments a
  counter, asserted to be zero before first use and one after, including under
  concurrent access.
- **Proxied-path integration test.** For container-managed proxies, test through
  the container rather than by constructing the bean directly, since constructing
  it directly removes the proxy and tests a configuration that never runs in
  production.
- **Advice-coverage assertion at startup.** For annotation-driven proxying, a
  startup check that every type carrying the annotation is actually proxied
  turns the final-method and missing-interface failures into a boot failure
  rather than a silent one.
- **Fault injection at the proxy.** Because the proxy is the one place the
  transport is visible, it is the correct place to inject timeouts and errors for
  testing the caller's degradation behaviour.

## 16. Observability signals

The pattern hides work behind an ordinary-looking call, so that work has to
appear in telemetry or it is undiagnosable.

What to record.

- A counter of calls through the proxy, labelled by method and by outcome. This
  is the base measurement and everything else is derived from it.
- For virtual proxies, a counter of initialisations and a counter of accesses.
  The ratio is the value the laziness is delivering. A ratio near one means every
  proxy is being touched and the laziness is paying nothing but complexity.
- For virtual proxies again, initialisations per unit of work. This is the N+1
  detector, and it is far more useful than a latency alert.
- For protection proxies, a counter of denials labelled by policy reason and by
  principal class, never by principal identifier unless that identifier is
  already treated as attributable data.
- For remote proxies, a duration histogram per method, a counter of retries, a
  counter of timeouts, and the circuit breaker state as a gauge. Propagate a
  trace context and make the proxy a span boundary, since it is the only place
  that knows a network hop is happening.
- For caching proxies, hit and miss counters, entry count as a gauge, and
  eviction count. A cache with no eviction counter is a leak waiting to be found
  by a heap dump.
- For smart references, the count of live referents, so a leak in the wrapper
  shows as a gauge climbing with no matching release.

A healthy instance on a dashboard. Call volume tracks request volume. For a
virtual proxy the initialisation-to-access ratio is well below one and stable,
and initialisations per request sit in single digits regardless of result-set
size. Remote proxy duration is flat with a modest tail, retries are a small
fraction of calls, and the breaker is closed. Cache hit rate is high and entry
count is flat once warm. Denials are non-zero, which is the evidence that the
policy is actually being exercised rather than misconfigured to allow everything.

A failing instance. Initialisations per request scaling with the size of a
collection, which is the N+1 storm and it appears as a step change after a
seemingly harmless view change. Or a latency histogram that is bimodal rather
than long-tailed, which points at first-access construction rather than at a slow
dependency. Or a denial counter that drops to zero after a deployment, which
almost always means a proxy stopped being applied rather than that everyone
became authorised. Or cache entry count climbing without bound. Or retries
climbing while duration stays flat, which means the dependency is failing fast
and the proxy is absorbing it, and that absorption is worth an alert before the
retry budget is exhausted.

One further measurement is specific to this pattern. Record the fact that a call
was proxied, as a boolean attribute or a distinct metric label. Because
interception can silently fail to apply, the absence of proxied calls for a
component that should have them is the only direct evidence of the
self-invocation and final-method failures, and nothing else reports them.

## 17. Security and privacy implications

Proxy is one of the few structural patterns with a first-class security role,
because the protection variant exists specifically to control access. That makes
both its correctness and its bypass paths security-relevant.

**A protection proxy is only as good as its unbypassable-ness.** The pattern
provides a checkpoint, and the checkpoint is worth nothing if a second reference
to the subject exists. Every path that can obtain the raw subject is a bypass.
Common leaks include a getter on the proxy returning the wrapped object, a
factory that returns the subject to some callers and the proxy to others, an
object graph where the subject is reachable through another entity, and
deserialisation that reconstructs the subject directly. The design rule is that
the subject should be unreachable except through the proxy, enforced by module
visibility or package privacy rather than by convention.

**Silent interception failure is a security failure.** Everything in dimension 11
about self-invocation and final methods applies to authorisation advice exactly
as it applies to transactions, and the consequence is worse. An unadvised
transactional method commits early. An unadvised authorisation method lets
everyone through, and it does so with no error and no log line. Any authorisation
implemented as an intercepting proxy needs the startup assertion from dimension
15 and a negative test proving that an unauthorised caller is refused on each
protected path, including internal call paths.

**Time-of-check to time-of-use.** A protection proxy checks a policy and then
forwards. If the policy input can change between the check and the call, or if
the subject re-reads mutable state that the check evaluated, the window is
exploitable. Keep the checked value and the used value the same object, and
prefer decisions evaluated at call time over decisions cached in the proxy for
the life of a session.

**Argument mutation across the check.** A proxy that validates arguments and
forwards the same mutable object gives a concurrent caller a window to change it
after validation. Where arguments are attacker-influenced and mutable, copy at
the boundary or use immutable types.

**Remote proxies carry the transport attack surface.** A remote proxy performs
deserialisation of data from another process, and deserialisation of untrusted
input is a well-known remote code execution vector. Java RMI's use of Java
serialisation is the historical example. Treat any response passing through a
remote proxy as untrusted input, validate it against the interface's contract
rather than assuming the declared type implies safe content, and prefer a
schema-checked encoding.

**Error messages leak through the seam.** A proxy translating a backend failure
into an interface-level exception frequently carries the backend's message with
it, which can expose hostnames, query fragments, and stack structure to a caller
that should not see them. Map failures onto the interface's error model
deliberately and log the detail rather than returning it.

**Dynamic proxies expand the trusted computing base.** Runtime bytecode
generation means a library is emitting classes into the running process. That
library, and whatever supplies its interception handlers, has the privileges of
the process. Where interception handlers can be contributed by plugins, treat
the handler set as supply-chain surface, pin it at build time where the plugin
set is known, and fail loudly rather than silently on a duplicate registration
for the same target.

On privacy the pattern is close to neutral in itself, with two practical
caveats. The first is that a proxy is the most convenient place to log every
call, and convenience produces over-logging. Arguments passing through a proxy
routinely include personal data, credentials and tokens, and a generic
log-the-invocation interceptor captures all of it by default. Redact by
allowlist rather than by denylist, since a denylist misses the field added next
quarter. The second is that a caching proxy holding personal data extends the
retention of that data past the request that fetched it, which may exceed what
the data's retention policy allows. A cache with personal data in it needs a time
to live chosen against that policy, not against performance alone, and it needs
an invalidation path for deletion requests.

## Code examples

Four languages, chosen because each shows a different shape of the pattern. Java
shows the runtime dynamic proxy, which is the form most production Java actually
uses. TypeScript shows the metaobject proxy, which intercepts property access
rather than method calls and is therefore capable of things the classical form is
not. Python shows the virtual proxy through attribute interception, which is how
lazy objects are built in that language. Go shows the handwritten static proxy
over an interface, which is the only form the language offers and the one its
lack of inheritance makes natural. C++ and Rust are omitted because their
idiomatic answer is a smart pointer with operator overloading or `Deref` rather
than a separate proxy type, so the pattern dissolves into a language facility and
stops being recognisable as this pattern.

### Java

A protection proxy and a call counter built on `java.lang.reflect.Proxy`. One
handler covers every method on the interface, so no method can be forgotten.

```java
import java.lang.reflect.*;
import java.util.*;

interface Vault {
    String read(String key);
    void write(String key, String value);
}

final class RealVault implements Vault {
    private final Map<String, String> data = new HashMap<>();
    public String read(String key) { return data.get(key); }
    public void write(String key, String value) { data.put(key, value); }
}

final class GuardHandler implements InvocationHandler {
    private final Vault subject;
    private final boolean canWrite;
    int calls = 0;

    GuardHandler(Vault subject, boolean canWrite) {
        this.subject = subject;
        this.canWrite = canWrite;
    }

    public Object invoke(Object proxy, Method m, Object[] args) throws Throwable {
        calls++;
        if (m.getName().equals("write") && !canWrite) {
            throw new SecurityException("write denied");
        }
        try {
            return m.invoke(subject, args);
        } catch (InvocationTargetException e) {
            throw e.getCause();
        }
    }
}

public final class Demo {
    static Vault guard(Vault real, boolean canWrite) {
        GuardHandler h = new GuardHandler(real, canWrite);
        return (Vault) Proxy.newProxyInstance(
            Vault.class.getClassLoader(), new Class<?>[]{Vault.class}, h);
    }

    public static void main(String[] args) {
        Vault real = new RealVault();
        Vault writer = guard(real, true);
        Vault reader = guard(real, false);

        writer.write("token", "abc");
        System.out.println(reader.read("token"));
        try {
            reader.write("token", "hacked");
        } catch (SecurityException e) {
            System.out.println("blocked, " + e.getMessage());
        }
    }
}
```

### TypeScript

The metaobject form. This intercepts property reads and writes rather than
method calls, which is what makes reactivity and audit logging possible without
naming every member.

```typescript
type Listener = (key: string, value: unknown) => void;

function observed<T extends object>(target: T, onSet: Listener): T {
  return new Proxy(target, {
    get(obj, prop, recv) {
      return Reflect.get(obj, prop, recv);
    },
    set(obj, prop, value, recv) {
      const ok = Reflect.set(obj, prop, value, recv);
      if (ok && typeof prop === "string") onSet(prop, value);
      return ok;
    },
    deleteProperty(obj, prop) {
      throw new Error(`delete of ${String(prop)} is not permitted`);
    },
  });
}

const settings = observed({ theme: "light", retries: 3 }, (k, v) =>
  console.log(`changed ${k} to ${String(v)}`),
);

settings.theme = "dark";
console.log(settings.retries);
```

A virtual proxy in the same language, building an expensive subject on first use
and keeping it afterwards.

```typescript
interface Report {
  render(): string;
}

function lazyReport(build: () => Report): Report {
  let real: Report | null = null;
  return {
    render(): string {
      if (real === null) {
        console.log("building the real report now");
        real = build();
      }
      return real.render();
    },
  };
}

const r = lazyReport(() => ({ render: () => "expensive output" }));
console.log("nothing built yet");
console.log(r.render());
console.log(r.render());
```

### Python

The virtual proxy through `__getattr__`, which is how Django's `LazyObject` and
similar wrappers work. The subject is built once, on the first attribute that the
proxy does not define itself.

```python
class Catalog:
    def __init__(self) -> None:
        print("loading catalog from disk")
        self.items = ["a", "b", "c"]

    def find(self, name: str) -> bool:
        return name in self.items


class LazyProxy:
    __slots__ = ("_factory", "_subject")

    def __init__(self, factory):
        object.__setattr__(self, "_factory", factory)
        object.__setattr__(self, "_subject", None)

    def _resolve(self):
        if object.__getattribute__(self, "_subject") is None:
            factory = object.__getattribute__(self, "_factory")
            object.__setattr__(self, "_subject", factory())
        return object.__getattribute__(self, "_subject")

    def __getattr__(self, name):
        return getattr(self._resolve(), name)

    def __repr__(self) -> str:
        built = object.__getattribute__(self, "_subject")
        return "<LazyProxy unresolved>" if built is None else repr(built)


if __name__ == "__main__":
    catalog = LazyProxy(Catalog)
    print(catalog)
    print(catalog.find("b"))
    print(catalog.find("z"))
```

### Go

The handwritten static form over an interface. Go has no inheritance and no
runtime class generation in the standard library, so this is the idiomatic shape,
and its explicitness is a feature rather than a limitation.

```go
package main

import (
	"errors"
	"fmt"
)

type Store interface {
	Get(key string) (string, error)
	Put(key, value string) error
}

type memStore struct{ data map[string]string }

func (m *memStore) Get(key string) (string, error) {
	v, ok := m.data[key]
	if !ok {
		return "", errors.New("missing key")
	}
	return v, nil
}

func (m *memStore) Put(key, value string) error {
	m.data[key] = value
	return nil
}

type readOnlyProxy struct {
	subject Store
	reads   int
}

func (p *readOnlyProxy) Get(key string) (string, error) {
	p.reads++
	return p.subject.Get(key)
}

func (p *readOnlyProxy) Put(key, value string) error {
	return errors.New("writes are not permitted through this reference")
}

func main() {
	real := &memStore{data: map[string]string{}}
	_ = real.Put("region", "eu-central")

	var s Store = &readOnlyProxy{subject: real}
	v, _ := s.Get("region")
	fmt.Println(v)
	fmt.Println(s.Put("region", "us-east"))
}
```

## 18. References

1. Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides. *Design Patterns.
   Elements of Reusable Object-Oriented Software*. Addison-Wesley, 1994.
   ISBN 0-201-63361-2. Chapter 4, Structural Patterns, section Proxy. Source of
   the intent, the Surrogate alias, the three participants, and the four named
   variants remote, virtual, protection and smart reference.
2. Oracle. *Java SE 21 API Specification*, `java.lang.reflect.Proxy`.
   https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/reflect/Proxy.html
   Verified 2026-08-02. Source for dynamic proxy classes, `newProxyInstance`,
   `InvocationHandler` dispatch, and the interfaces-only restriction.
3. Oracle. *Java SE 21 API Specification*, `java.util.Collections`.
   https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Collections.html
   Verified 2026-08-02. Source for the unmodifiable view as a protection proxy,
   including the read-through and `UnsupportedOperationException` behaviour.
4. Oracle. *Java SE 21 API Specification*, `java.rmi` package summary.
   https://docs.oracle.com/en/java/javase/21/docs/api/java.rmi/java/rmi/package-summary.html
   Verified 2026-08-02. Source for remote objects, marshalling, and the stub
   terminology.
5. Broadcom. *Spring Framework Reference*, Core, AOP, Proxying Mechanisms.
   https://docs.spring.io/spring-framework/reference/core/aop/proxying.html
   Verified 2026-08-02. Source for the JDK dynamic proxy against CGLIB subclass
   choice, the self-invocation behaviour, and the discouraged
   `AopContext.currentProxy()` workaround.
6. Broadcom. *Spring Framework Reference*, Data Access, Declarative Transaction
   Management, Using `@Transactional`.
   https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/annotations.html
   Verified 2026-08-02. Source for the statement that in proxy mode only external
   calls through the proxy are intercepted, and for the AspectJ mode remedy.
7. Red Hat. *Hibernate ORM 6.6 Javadoc*, `org.hibernate.LazyInitializationException`.
   https://docs.hibernate.org/orm/6.6/javadocs/org/hibernate/LazyInitializationException.html
   Verified 2026-08-02. Source for access to unfetched data outside an open
   stateful session.
8. Red Hat. *Hibernate ORM 6.6 Javadoc*, `org.hibernate.annotations.BatchSize`.
   https://docs.hibernate.org/orm/6.6/javadocs/org/hibernate/annotations/BatchSize.html
   Verified 2026-08-02. Source for batch fetching of proxies as the N+1
   mitigation.
9. Red Hat. *Hibernate ORM 5.2 User Guide*, Fetching chapter.
   https://docs.hibernate.org/orm/5.2/userguide/html_single/chapters/fetching/Fetching.html
   Verified 2026-08-02. Source for the N+1 selects problem, the warning about
   `FetchMode.SELECT`, and the preference for a join fetch or a projection over
   `@BatchSize`.
10. Red Hat. *Hibernate ORM 6.6 Javadoc*, `org.hibernate.Session`.
    https://docs.hibernate.org/orm/6.6/javadocs/org/hibernate/Session.html
    Verified 2026-08-02. Source for `getReference` returning a reference without
    initialising the instance.
11. Mozilla. *MDN Web Docs*, `Proxy`.
    https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Proxy
    Verified 2026-08-02. Source for the target and handler terms and the trap
    list used in dimension 8.
12. Vue.js. *Reactivity in Depth*.
    https://vuejs.org/guide/extras/reactivity-in-depth.html
    Verified 2026-08-02. Source for Vue 3 using proxies for reactive objects and
    for the identity difference under strict equality.
13. gRPC Authors. *gRPC Core Concepts, Architecture and Lifecycle*.
    https://grpc.io/docs/what-is-grpc/core-concepts/
    Verified 2026-08-02. Source for the client stub as a local object
    implementing the service methods.
14. Envoy Project. *What is Envoy*.
    https://www.envoyproxy.io/docs/envoy/latest/intro/what_is_envoy
    Verified 2026-08-02. Source for the sidecar deployment model and the
    transparent-network position.
15. Microsoft. *.NET API documentation*, `System.Reflection.DispatchProxy`.
    https://learn.microsoft.com/en-us/dotnet/api/system.reflection.dispatchproxy
    Verified 2026-08-02. Source for the standard-library interception facility
    and its `Invoke` dispatch.
16. Python Software Foundation. *Python 3 Standard Library*, `weakref`.
    https://docs.python.org/3/library/weakref.html
    Verified 2026-08-02. Source for `weakref.proxy`, its non-hashability, and the
    `ReferenceError` raised after collection of the referent.
17. Django Software Foundation. *Django 4.2 source documentation*,
    `django.utils.functional`.
    https://docs.djangoproject.com/en/4.2/_modules/django/utils/functional/
    Verified 2026-08-02. Source for `LazyObject` as a wrapper that delays
    instantiation and for `SimpleLazyObject` built from a callable.
18. Wikipedia contributors. "Proxy pattern".
    https://en.wikipedia.org/wiki/Proxy_pattern
    Verified 2026-08-02. Used only to confirm the wording of the GoF intent and
    the remote, virtual and protection variants. It does not list the smart
    reference variant, which is taken from the book.
