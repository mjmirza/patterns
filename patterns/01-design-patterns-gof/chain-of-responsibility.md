---
name: Chain of Responsibility
slug: chain-of-responsibility
family: 01-design-patterns-gof
category: Behavioral
aliases: [Chain of Command, Responsibility Chain, Intercepting Filter, Middleware Pipeline]
first_described: "Gamma, Helm, Johnson, Vlissides 1994"
maturity: canonical
related: [command, composite, decorator, mediator, observer, strategy, interpreter]
incompatible_with: []
verified: 2026-08-02
---

# Chain of Responsibility

## 1. Name, aliases, and lineage

The canonical name is Chain of Responsibility. It is one of the eleven behavioral
patterns in the Gang of Four catalog, described in Erich Gamma, Richard Helm,
Ralph Johnson and John Vlissides, *Design Patterns. Elements of Reusable
Object-Oriented Software*, Addison-Wesley, 1994, chapter 5 (Behavioral
Patterns). The book states the intent as avoiding the coupling of a request's
sender to its receiver by giving more than one object a chance to handle the
request, chaining the receiving objects and passing the request along that chain
until one of them handles it (authorized book excerpt at
https://www.informit.com/articles/article.aspx?p=1398601, verified 2026-08-02).

Four names circulate for shapes that are the same idea, and telling them apart
matters because they carry different assumptions about how many handlers act.

- **Chain of Responsibility (GoF).** A request travels along a linear sequence
  of candidate handlers. Each one decides whether to act. The classical reading
  is that exactly one handler acts and the traversal stops there.
- **Chain of Command.** A colloquial alias borrowed from organisational
  language, used interchangeably in codebases and interview questions. It has no
  separate technical meaning, and the overlap with the Command pattern makes it
  the alias most likely to confuse a reader.
- **Intercepting Filter.** The name used in the enterprise Java pattern
  literature and adopted by framework authors for the request-processing
  variant, where every handler in the sequence normally acts and then forwards.
  Netty's own API documentation states that its pipeline implements an advanced
  form of the Intercepting Filter pattern
  (https://netty.io/4.1/api/io/netty/channel/ChannelPipeline.html, verified
  2026-08-02).
- **Middleware pipeline.** The name that won in the web-server world. Express,
  Koa, ASP.NET Core and their descendants describe the same structure. The
  Express documentation defines a middleware function as one with access to the
  request, the response, and the next middleware function in the request and
  response cycle (https://expressjs.com/en/guide/using-middleware.html, verified
  2026-08-02).

The distinction that carries real weight is not between the names but between
two dialects of the pattern, and a reader who conflates them will misread half
the code they meet.

- **Pure Chain of Responsibility.** The traversal exists to find one handler.
  Handlers that decline pass the request on untouched. Success means one handler
  claimed the request. This is the GoF reading and the shape of an event
  responder chain or an approval hierarchy.
- **Pipeline Chain of Responsibility.** The traversal exists so every handler
  contributes. Each handler acts, forwards, and often acts again on the way
  back. Success means the request reached the end and a response came back.
  This is the shape of servlet filters and web middleware. Declining to forward
  is the exception, and it is called short-circuiting.

Both are the same structure. They differ in whether forwarding is the default or
the exception, and that inversion changes the failure modes, the ordering
sensitivity and the observability advice for each. Every dimension below states
which dialect it is describing when the two diverge.

## 2. Problem and context

A request arrives and there are several plausible things that might deal with
it, the correct one depends on the request itself, and the code raising the
request has no business knowing which of them will act.

The situation reads like this in a real codebase. A support ticket enters a
system and has to reach an approver whose spending limit covers it. A keypress
lands on a text field inside a form inside a window and something has to decide
whom it belongs to. An HTTP request needs authentication, then rate limiting,
then request logging, then compression, then the actual handler, and each of
those steps was written by a different team at a different time. A log record is
emitted by a library and has to reach whichever sinks the application has
configured, which the library cannot know.

Without the pattern, code that has this shape drifts toward one of three
outcomes, all bad in different ways.

The first is a conditional that grows without bound. A single dispatch function
accumulates a branch for every case, and every new case edits a file that every
team depends on. The branch order becomes load-bearing without anyone recording
that it is, because the cases stopped being mutually exclusive two years ago.

The second is a sender that knows every receiver. The code raising the request
imports each candidate handler, holds a reference to each, and calls them in
order with its own logic for deciding who gets it. Adding a handler means
editing the sender. Removing one means editing the sender. Testing the sender
means constructing every handler.

The third is duplication. Each entry point re-implements the same sequence of
preliminary steps, and after a few releases the sequences have quietly diverged.
One endpoint checks authentication before rate limiting, another checks it
after, and the difference is a security hole nobody wrote down.

The context that makes Chain of Responsibility the right answer has four parts.

- More than one object could handle the request, and which one should is a
  runtime property of the request rather than a compile-time property of the
  call site.
- The sender is content to have the request handled by somebody, without a
  handle on whom. The GoF applicability list phrases this as issuing a request to
  one of several objects without specifying the receiver explicitly (InformIT
  excerpt, verified 2026-08-02).
- The set of candidates should be configurable, and often assembled at startup
  from configuration rather than fixed in source.
- The handlers are genuinely independent of each other. A handler that has to
  know what the previous one decided is a sign the problem is a workflow, not a
  chain.

Where those four hold, the pattern converts a branching decision into a data
structure. Where they do not hold, see dimension 4, because a chain applied to
the wrong problem is one of the harder structures to debug.

## 3. Forces

The pattern balances the following competing pressures, and the balance differs
between the two dialects named in dimension 1.

- **Coupling between sender and receiver.** Strongly favoured. The sender holds
  one reference, to the head of the chain, and knows nothing about who acts. This
  is the whole point and the reason the pattern survives.
- **Coupling between handlers.** Favoured but not eliminated. Each handler knows
  only the next link, never the whole sequence. What remains is an implicit
  coupling through order, which is the pattern's most under-documented cost. See
  the ordering discussion below and in dimension 11.
- **Determinism and traceability.** Sacrificed. In a conditional, the source
  states which branch runs. In a chain, the answer depends on runtime
  composition, so no reading of the source alone can say what will happen. This
  is the single largest cognitive cost, and the reason dimension 16 treats
  telemetry as part of the pattern rather than an accessory to it.
- **Guaranteed receipt.** Sacrificed, and the GoF are explicit about it. Their
  consequences list states that receipt is not guaranteed, that because a request
  has no explicit receiver there is no guarantee it will be handled, and that the
  request can fall off the end of the chain without ever being handled (InformIT
  excerpt, verified 2026-08-02). Every serious deployment of this pattern has to
  decide what happens at the end of the chain, and the ones that skipped that
  decision are the ones with silent-drop incidents.
- **Latency.** Mildly sacrificed and usually irrelevant, with one exception. A
  chain of ten handlers costs ten indirect calls and ten stack frames. That is
  noise against any input or output. It stops being noise when the chain is
  traversed per item in a hot loop, or when a recursive pipeline implementation
  builds deep stacks that defeat inlining and hurt cache locality.
- **Operability.** Mixed. The chain is easy to change without a deployment,
  because the composition can live in configuration. The same property makes
  incidents harder, because the running composition is not in the source and has
  to be dumped from the process.
- **Cost of change.** Strongly favoured for adding, removing or reordering a
  behaviour. Strongly sacrificed for changing the contract that all handlers
  share, since every handler in every downstream repository implements it.
- **Team topology.** Strongly favoured. A platform team owns the chain runner and
  the handler contract, and product teams contribute handlers on their own
  release schedule without touching shared code. This is why the pattern is the
  default extension mechanism in nearly every server framework.
- **Cognitive load.** Sacrificed. A reader tracing a request has to find the
  composition site, read the order, and hold ten handler behaviours in mind at
  once. In the pipeline dialect where handlers act both before and after
  forwarding, the reader also has to hold the unwinding order, which is the
  reverse.
- **Consistency of cross-cutting behaviour.** Strongly favoured. One chain
  applied to every request gives every request the same treatment, which is the
  argument that beats the duplication outcome in dimension 2.

Ordering deserves its own note because it is the force most often ignored. The
chain is order-dependent, and in almost every production system the order lives
in configuration rather than in code. The Jakarta EE tutorial states that filters
are invoked in the order in which filter mappings appear in the filter mapping
list of a WAR, and that the order of the filters in the chain is the same as the
order in which filter mappings appear in the deployment descriptor
(https://jakarta.ee/learn/docs/jakartaee-tutorial/current/web/servlets/servlets.html,
verified 2026-08-02). The ASP.NET Core documentation puts it more bluntly,
stating that the order in which middleware components are added defines the
order in which they are invoked on requests and the reverse order for the
response, and that the order is critical for security, performance and
functionality
(https://learn.microsoft.com/en-us/aspnet/core/fundamentals/middleware/,
verified 2026-08-02). A correctness property of the system therefore lives in an
XML file, a startup method or a YAML document, where no type checker inspects it
and no compiler complains when somebody moves a line. That is the trade the
pattern asks for, and it is worth taking with the eyes open.

## 4. Applicability and non-applicability

Reach for Chain of Responsibility when the following hold.

- More than one object may handle a request and the handler is not known in
  advance, which is the first item on the GoF applicability list (InformIT
  excerpt, verified 2026-08-02).
- The request should be issued to one of several objects without naming the
  receiver, so that the sender depends on the chain rather than on any handler.
- The set of objects that can handle the request should be specifiable
  dynamically, so that composition happens at startup or at runtime rather than
  at compile time.
- Cross-cutting behaviour has to apply uniformly to many requests, and the
  behaviours are independent enough to be listed rather than sequenced.
- A framework must publish an extension point that third parties contribute to
  without the framework knowing what they will contribute.
- A hierarchy already exists in the domain, for example a view tree or an
  approval ladder, and escalation up that hierarchy is the natural fallback.

Do NOT reach for Chain of Responsibility in these cases. This
non-applicability list matters more than the list above, because the pattern is
easy to add and hard to remove.

- **Exactly one handler can ever apply and the mapping is a lookup.** If the
  handler is chosen by a key with no ambiguity, a map from key to handler is
  correct, is order-independent, and answers in constant time. A chain turns an
  O(1) dispatch into an O(n) scan and adds an ordering hazard for nothing. Web
  routers that match on an exact path use a map or a trie inside for exactly this
  reason.
- **Every handler must act and the order is a fixed algorithm.** That is a
  sequence, not a chain. Write it as a sequence of statements, or as Template
  Method if variation is needed. Encoding a fixed algorithm as a chain hides the
  algorithm inside a configuration file and buys no flexibility, because
  reordering the chain would break the program.
- **The sender needs the identity of the handler or a typed result.** The pattern
  deliberately hides the receiver. A sender that has to know who acted, or that
  needs a return value whose type depends on the handler, is fighting the
  pattern. Use a Strategy selected by an explicit rule, or a Visitor if the
  dispatch is by type.
- **Handlers depend on each other's decisions.** Once handler four needs to know
  what handler two concluded, the request object grows into a shared mutable
  bag, and the chain has become an undeclared workflow. Model it as a workflow or
  a state machine where the dependencies are visible.
- **Silent non-handling is not acceptable and no terminal handler is possible.**
  The GoF liability is real. If dropping a request is a correctness failure and
  the design cannot supply a default handler at the end of the chain, the pattern
  is a poor fit, or it needs the guaranteed-terminal variant from dimension 8.
- **The chain would be traversed in a hot inner loop.** Per-element traversal of
  a long chain of virtual calls in a tight loop is measurable in systems
  languages and in high-throughput data paths. Prefer a compiled dispatch table
  or a match expression when the profile says so, and only then.
- **The set of handlers is small, closed and stable.** Two handlers that have not
  changed in three years do not need an extension mechanism. A conditional
  expresses two cases better than a chain does, and deletes cleanly.
- **The pattern is being reached for to avoid a long method.** A long method is a
  code smell with cheaper cures, such as extracting functions. Converting it to a
  chain distributes the logic across files and adds runtime indirection while
  leaving the same amount of logic, which trades a readable problem for an
  unreadable one.
- **Exception handling is the actual need in a language with exceptions.** A
  language runtime already implements the pattern for exceptions, walking the
  stack until a handler claims the throw. Rebuilding that by hand for error
  routing duplicates a mechanism the runtime does better.

## 5. Structure

Four participants, named by the role each plays.

- **Handler.** The interface that declares the request-handling operation and,
  in most implementations, holds the link to the successor. It is the only
  handler-side type the client knows. Its contract has to state one thing
  precisely, which is what a handler must do when it declines. In the pure
  dialect that means calling the successor. In the pipeline dialect the contract
  is a two-argument shape, the request and a continuation, and declining to call
  the continuation is a deliberate act called short-circuiting.
- **ConcreteHandler.** An implementation that examines the request, decides
  whether it is responsible, acts if it is, and otherwise forwards to its
  successor. A ConcreteHandler knows its successor and nothing else about the
  chain. It does not know its own position, how many handlers follow, or whether
  anybody will act if it declines.
- **Client.** Assembles the chain and sends the request to its head. The client
  is the only participant that knows the full composition, and in a framework the
  client role is normally played by startup configuration rather than by
  application code. This is where the ordering lives, and therefore where the
  ordering has to be reviewed.
- **Terminal.** Not in the classical catalog by that name, and worth naming
  because its absence is the pattern's headline failure. Something has to occupy
  the position after the last handler. It is a null successor that silently ends
  traversal, a default handler that always acts, or a sentinel that raises an
  error. Choosing between those three is a design decision, and leaving it
  implicit chooses the first one by accident.

Relationships. Handler declares an association to Handler, which is the
self-reference that makes the chain. Each ConcreteHandler inherits or implements
Handler and holds one successor of the same abstract type. The client holds a
reference to the head only. No handler holds a reference to the client, and no
handler holds a reference to any handler other than its immediate successor.

Two variants of the structure change the shape without changing the idea. The
first replaces the successor field with a runner that owns an ordered list and
calls each element in turn, which is how most middleware implementations work
and which makes the composition inspectable in one place. The second lets a
handler have several successors, which turns the chain into a tree of
responsibility. A node then acts as a dispatcher, choosing a branch or
forwarding upward. The Wikipedia treatment records this tree variant as an
established variation of the pattern
(https://en.wikipedia.org/wiki/Chain-of-responsibility_pattern, verified
2026-08-02).

## 6. ASCII structure diagram

```
   +-------------+   sends request    +--------------------------+
   |   Client    | -----------------> |        Handler           |
   |-------------|                    |--------------------------|
   | + start()   |                    | + handle(req)            |
   +-------------+                    | # successor: Handler     |
                                      +--------------------------+
                                         ^      ^      ^     |
                                         |      |      |     | successor
              implements ----------------+      |      |     | (self link)
                                                |      |     v
   +--------------------------+   +--------------------------+
   |    ConcreteHandlerA      |   |    ConcreteHandlerB      |
   |--------------------------|   |--------------------------|
   | + handle(req)            |   | + handle(req)            |
   |   if canHandle -> act    |   |   if canHandle -> act    |
   |   else successor.handle  |   |   else successor.handle  |
   +--------------------------+   +--------------------------+

   +--------------------------+   +--------------------------+
   |    ConcreteHandlerC      |   |   Terminal (default)     |
   |--------------------------|   |--------------------------|
   | + handle(req)            |   | + handle(req)            |
   +--------------------------+   |   always acts, or raises |
                                  +--------------------------+

   Composition, assembled by the Client at startup:

     head                                                   tail
      |                                                       |
      v                                                       v
   [ A ] --> [ B ] --> [ C ] --> [ Terminal ] --> (end, no successor)

   Only the Client sees the whole line. Each handler sees one arrow.
   Removing Terminal is what lets a request fall off the right edge.
```

## 7. Dynamics

Two runtime flows, one per dialect. The difference between them is where control
returns to, and it is the difference that decides how the code reads.

The pure dialect first. The request travels forward until somebody claims it, and
the return unwinds straight back to the client without further work.

```
Client        HandlerA        HandlerB        HandlerC       Terminal
  |               |               |               |              |
  |-- handle(r) ->|               |               |              |
  |               |- canHandle? no|               |              |
  |               |-- handle(r) ->|               |              |
  |               |               |- canHandle? no|              |
  |               |               |-- handle(r) ->|              |
  |               |               |               |- canHandle?  |
  |               |               |               |     yes      |
  |               |               |               |- act         |
  |               |               |<-- result ----|              |
  |               |<-- result ----|               |              |
  |<-- result ----|               |               |              |
  |               |               |               |              |
  |  If C also declined, Terminal decides the fate of r.         |
  |  With no Terminal, the call returns having done nothing,     |
  |  which is the GoF unhandled-request liability.               |
```

The pipeline dialect second. Every handler acts on the way down, forwards, and
acts again on the way back up. The Koa documentation names these the capture
phase and the bubble phase, with code before the continuation running downstream
and code after it running upstream
(https://github.com/koajs/koa/blob/master/docs/guide.md, verified 2026-08-02).

```
Client        Auth          RateLimit       Compress        Endpoint
  |             |               |               |               |
  |-- req ----->|               |               |               |
  |             |- verify token |               |               |
  |             |-- next() ---->|               |               |
  |             |               |- take token   |               |
  |             |               |-- next() ---->|               |
  |             |               |               |- note accept  |
  |             |               |               |-- next() ---->|
  |             |               |               |               |- build
  |             |               |               |<-- response --|
  |             |               |               |- gzip body    |
  |             |               |<-- response --|               |
  |             |               |- add headers  |               |
  |             |<-- response --|               |               |
  |             |- audit log    |               |               |
  |<-- response |               |               |               |
  |             |               |               |               |
  Downstream order:  Auth, RateLimit, Compress, Endpoint
  Upstream order:    Endpoint, Compress, RateLimit, Auth
```

Three timing notes that decide whether an implementation is correct.

First, short-circuiting. Any handler may decline to forward and answer directly.
The ASP.NET Core documentation states that each middleware is responsible for
invoking the next one or short-circuiting the pipeline, and that a middleware
which short-circuits is called terminal middleware because it prevents further
middleware from processing the request
(https://learn.microsoft.com/en-us/aspnet/core/fundamentals/middleware/, verified
2026-08-02). Handlers earlier in the chain still run their upstream code, which
is why a short-circuit does not skip the audit log placed at the front.

Second, forgetting to forward. In the pipeline dialect, omitting the
continuation is the same syntax as short-circuiting and a completely different
intent. The Express documentation states that if the current middleware function
does not end the request and response cycle it must call the continuation, and
that otherwise the request will be left hanging
(https://expressjs.com/en/guide/using-middleware.html, verified 2026-08-02). The
observable result is a client timeout with no server error, which is covered in
dimension 11.

Third, asynchrony. A chain whose handlers perform input or output has to
propagate the asynchronous result through every link, or the upstream phase runs
before the downstream work finishes. Koa's design exists because the earlier
callback style made the upstream phase awkward to express, and its guide frames
the continuation as something to await so that later code observes the completed
downstream result (Koa guide, verified 2026-08-02).

## 8. Implementation variants

**Linked successor field.** The classical form. Each handler holds a reference to
the next one and forwards explicitly. Cheapest to describe and the form in the
GoF text. Its weakness is that the chain has no single owner, so no code can
enumerate it, print it, or validate it, which makes the composition invisible to
tooling and to incident response.

**Owned ordered list with a runner.** A collection object holds the handlers in
order and the runner calls each one. The composition becomes a value that can be
logged, tested, reordered and diffed. It also removes the risk of a handler being
placed in two chains at once with conflicting successors. This is the form nearly
every modern framework uses, and it is the one to prefer for new code. Spring
Security's architecture is built this way, with a proxy filter delegating to
security filter chain instances that determine which filters apply to the current
request (https://docs.spring.io/spring-security/reference/servlet/architecture.html,
verified 2026-08-02).

**Continuation-passing middleware.** Each handler receives the request and a
function representing the rest of the chain, rather than a reference to the next
handler. The rest of the chain is built by folding the handler list from the tail
forward. This is the shape of Express, Koa and ASP.NET Core, and it is what makes
the upstream phase possible without any handler knowing its neighbours. The cost
is stack depth proportional to chain length and stack traces that are harder to
read, since every frame belongs to the runner rather than to a named handler.

**Decorator-style wrapping.** Each handler is a function that takes the next
handler and returns a new handler. Composition is function composition, and the
resulting object is a single callable with the whole chain baked in. This is the
idiomatic Go form, where a middleware has the type of a function from handler to
handler. It gives the best performance characteristics of the variants here,
because the composition is done once at startup rather than per request, and it
gives the worst introspection, because after composition the individual handlers
are no longer distinguishable.

**Parent-link traversal over an existing hierarchy.** No separate chain is built.
The chain is read off a structure that exists for another reason, most often a
tree, by following a parent pointer until somebody acts. Apple's responder chain
works this way, forwarding an unhandled event to the next responder up the view
hierarchy toward the window and then the application object
(https://developer.apple.com/library/archive/documentation/General/Conceptual/Devpedia-CocoaApp/Responder.html,
verified 2026-08-02). Python's logging hierarchy works the same way through the
logger name, passing a record to the handlers of ancestor loggers as long as the
propagate attribute stays true
(https://docs.python.org/3/library/logging.html, verified 2026-08-02). This
variant costs nothing to build and cannot be reordered, which is either its main
strength or its main limitation depending on the problem.

**Guaranteed-terminal chain.** The composition step appends a terminal handler
that always acts, so falling off the end becomes impossible by construction. The
terminal either supplies a default, raises a typed error, or records a metric and
returns a rejection. This is the single highest-value variant for anybody who has
been paged for a silently dropped request, and it costs one class. Python's
logging module effectively does this at the library level with a handler of last
resort, described as a stream handler writing to standard error at warning level,
used when no handler is attached to the logger or its ancestors (Python logging
documentation, verified 2026-08-02).

**Priority-ordered registration.** Handlers declare a numeric or symbolic
priority and the runner sorts them. This turns ordering from an accident of
registration order into a declared property, which helps when handlers come from
independent plugins that cannot see each other. The cost is a new coordination
problem, because priority numbers become a shared namespace that nobody owns, and
teams start choosing large round numbers to win.

**Broadcast chain.** Traversal continues past the first handler that acts, so
several handlers contribute. It is a small edit and a large semantic change,
because the pattern no longer answers who handled the request. When several
handlers must always act on the same event and none of them declines, Observer
is the honest pattern and expresses the intent better.

**Language note on languages without inheritance.** Go and Rust have no class
hierarchy, so the classical participant diagram does not translate directly. In
Go the pattern is a function type composed by wrapping, shown in the code
examples below. In Rust the closest idiomatic forms are a vector of boxed trait
objects iterated by a runner, or the tower crate's service and layer abstraction,
which is the wrapping variant expressed through traits. Both express the pattern
without any of the classical class structure.

## 9. Known production uses

**Jakarta Servlet filter chains.** The specification's `FilterChain` type is
described as an object provided by the servlet container giving a view into the
invocation chain of a filtered request for a resource, and its `doFilter` method
is described as causing the next filter in the chain to be invoked, or if the
calling filter is the last one, causing the resource at the end of the chain to
be invoked. Jakarta Servlet 6.1 API documentation,
https://jakarta.ee/specifications/servlet/6.1/apidocs/jakarta.servlet/jakarta/servlet/filterchain
verified 2026-08-02. The `Filter` interface documentation lists authentication,
logging and auditing, image conversion, data compression, encryption,
tokenizing, resource access events, XSL/T transformation and mime-type chaining
as the intended uses, which is a catalog of cross-cutting concerns,
https://jakarta.ee/specifications/servlet/6.1/apidocs/jakarta.servlet/jakarta/servlet/filter
verified 2026-08-02. Filtering is covered by chapter 6 of the specification,
https://jakarta.ee/specifications/servlet/6.1/jakarta-servlet-spec-6.1 verified
2026-08-02.

**Express middleware.** The framework defines a middleware function as one with
access to the request object, the response object, and the next middleware
function in the request and response cycle, and states that a middleware which
does not end the cycle must call the next function or the request will be left
hanging. Express documentation, "Using middleware",
https://expressjs.com/en/guide/using-middleware.html verified 2026-08-02. This is
the pipeline dialect in its most widely deployed form, and the hanging-request
sentence is the pattern's unhandled-request liability restated for the web.

**Koa middleware.** Koa middleware are functions taking a context and a
continuation, and the guide describes code before the continuation as the capture
phase and code after it as the bubble phase, with the explicit statement that
omitting the continuation means downstream middleware are ignored. Koa guide,
https://github.com/koajs/koa/blob/master/docs/guide.md verified 2026-08-02. Koa
is the reference implementation of the two-phase pipeline, and its documentation
is the clearest primary source for the upstream half of dimension 7.

**ASP.NET Core middleware.** The documentation states that each middleware in the
request pipeline is responsible for invoking the next middleware or
short-circuiting the pipeline, that a middleware which short-circuits is called
terminal middleware, and that the order in which middleware appears defines the
order of invocation on requests and the reverse order on responses, with that
order described as critical for security, performance and functionality.
Microsoft Learn, "ASP.NET Core Middleware",
https://learn.microsoft.com/en-us/aspnet/core/fundamentals/middleware/ verified
2026-08-02. This is the strongest primary source for the ordering-fragility
argument in dimension 3.

**Netty's channel pipeline.** The API documentation describes a
`ChannelPipeline` as a list of channel handlers that handle or intercept inbound
events and outbound operations of a channel, states that it implements an
advanced form of the Intercepting Filter pattern, and states that an inbound
event which reaches the end of the pipeline without being intercepted is
discarded silently, or logged if it needs attention. Netty 4.1 API
documentation, https://netty.io/4.1/api/io/netty/channel/ChannelPipeline.html
verified 2026-08-02. That last sentence is the unhandled-request liability
documented by a production framework in its own reference pages, and it doubles
as evidence for the bidirectional traversal described in dimension 7.

**Python's logging hierarchy.** A record logged to a logger is passed to the
handlers of ancestor loggers when the propagate attribute is true, and
propagation stops at the first ancestor whose propagate attribute is false. When
no handler is found on the logger or any ancestor, the record goes to a handler
of last resort that writes to standard error at warning level. Python 3
documentation, `logging` module,
https://docs.python.org/3/library/logging.html verified 2026-08-02. This is the
parent-link variant plus an explicit terminal, and it is the cleanest production
example of the guaranteed-terminal design from dimension 8.

**Apple's responder chain.** An object that cannot handle an event or action
message forwards it to the next responder in a linked series called the responder
chain, the message travels toward higher-level objects until it is handled, and
if it is not handled the application discards it. Apple Developer documentation
archive, "Responder",
https://developer.apple.com/library/archive/documentation/General/Conceptual/Devpedia-CocoaApp/Responder.html
verified 2026-08-02. The discard sentence is a third independent primary source
for the same liability, and the fact that three unrelated frameworks each
document their own end-of-chain behaviour is the argument for treating the
terminal as a design decision rather than an afterthought.

**Spring Security's filter chain.** A proxy filter delegates to security filter
chain instances, each holding an ordered list of filters, and the documentation
states that filters are executed in a specific order to guarantee they are
invoked at the right time, giving authentication before authorization as the
example, and that a filter can prevent downstream filters and the servlet from
being invoked by not calling the chain. Spring Security reference documentation,
"Architecture",
https://docs.spring.io/spring-security/reference/servlet/architecture.html
verified 2026-08-02. This is the owned-list variant applied to a security
boundary, where ordering is a correctness property rather than a preference.

## 10. Consequences

Positive.

- Sender and receiver are decoupled. The sender holds one reference and gains no
  knowledge when handlers are added, removed or reordered. The GoF list this
  reduced coupling as the pattern's first benefit (InformIT excerpt, verified
  2026-08-02).
- Responsibilities can be assigned flexibly, at runtime, from configuration. A
  behaviour can be inserted into a running system's next startup without editing
  any code that produces or consumes requests.
- Each handler stays small and single-purpose. A filter that compresses a
  response has no reason to know about authentication, and the structure makes
  that separation the path of least resistance rather than a discipline.
- Cross-cutting concerns are applied uniformly. One chain in front of every
  endpoint gives every endpoint identical treatment, which removes the class of
  bug where one route forgot a check.
- The extension point is publishable and versionable. A framework can document
  the handler contract and let third parties implement it without the framework
  ever naming their types.
- Both traversal directions are available in the pipeline dialect. Behaviour that
  needs to wrap a request, such as timing, transaction scoping or response
  rewriting, is expressible in one handler rather than two coordinated ones.

Negative.

- Receipt is not guaranteed. The request can fall off the end of the chain
  without being handled, and the GoF state this plainly as a liability (InformIT
  excerpt, verified 2026-08-02). Netty documents silent discard and Apple
  documents discard by the application, so this is not theoretical.
- Behaviour depends on composition, which lives outside the source. Reading every
  handler tells a reader what could happen but not what will, and the ordering
  that decides it is usually in a configuration file.
- Debugging is harder than for a conditional. A stack trace through a
  continuation-passing pipeline is a wall of runner frames, and the handler that
  matters is somewhere in the middle.
- Performance degrades linearly with chain length, and every request pays for
  every handler that inspects it, including the ones that decline.
- The shared request contract becomes rigid. Once dozens of external handlers
  implement it, changing the handler signature is a breaking change across every
  consumer.
- Partial mutation on failure is possible. In the pipeline dialect, handlers
  before the failure point have already run their downstream half, and undoing
  their effects is the caller's problem unless the design accounted for it.
- Over-application is common and hard to reverse. A chain added for two handlers
  and grown to forty becomes a system whose behaviour nobody can state, and
  removing a handler is risky because nothing records what depends on it.

## 11. Failure modes and misuse

Each entry gives the observable symptom first, because the abstract mistake alone
is not enough to recognise the problem at three in the morning.

**Request falls off the end of the chain.** Symptom. A request returns success
with an empty body, or a queued message disappears with no error, no log line and
no metric, and the count of processed items is lower than the count of received
items with nothing to explain the gap. Cause. No terminal handler, and every
handler declined. This is the GoF liability directly (InformIT excerpt, verified
2026-08-02), and it is the failure that Netty documents as silent discard
(Netty 4.1 documentation, verified 2026-08-02). Fix. Append a terminal handler
during composition that always acts, and have it increment an unhandled counter
and log at warning level with the request identifier. Make the composition
function refuse to build a chain that has no terminal, so the mistake is
unrepresentable rather than merely discouraged.

**The hanging request.** Symptom. A client times out after thirty seconds. The
server shows no error, no exception in the logs, and a request-started log line
with no matching request-finished line. Connection counts climb. Cause. A
middleware in the pipeline dialect neither ended the response nor called the
continuation, which the Express documentation names directly as leaving the
request hanging (Express documentation, verified 2026-08-02). Usually an early
return inside a conditional branch that the author forgot to terminate. Fix. Add
a watchdog in the runner that flags any request exceeding a time budget with the
identity of the last handler entered. In review, treat every early return inside
a handler as a defect until the author proves the response was written.

**Ordering regression after a refactor.** Symptom. Authentication stops running
for one route class, or compression produces a body that a later handler then
modifies, or a rate limiter counts requests that authentication should have
rejected. The change that caused it touched no handler, only the composition
file. Cause. Reordering during a merge, a plugin registering at a new priority,
or the addition of a handler in the wrong position. ASP.NET Core's documentation
calls the order critical for security, performance and functionality (Microsoft
Learn, verified 2026-08-02), and Spring Security gives authentication before
authorization as the canonical example (Spring Security documentation, verified
2026-08-02). Fix. Write an assertion test over the composed chain that pins the
expected order by handler name, so a reorder fails the build rather than
production. Treat the composition file as security-relevant code in review.

**Short-circuit hidden inside a handler.** Symptom. A handler far down the chain
never executes in one environment and always executes in another, and no
configuration difference explains it. Cause. An earlier handler short-circuits on
a condition that holds only in one environment, for example a cache hit or a
feature flag, and the short-circuit is not logged. Fix. Emit a structured event
whenever a handler terminates traversal, carrying the handler name and the
reason. Short-circuiting is a legitimate act, and it has to be visible.

**The request object as a shared mutable bag.** Symptom. Handler nine reads a
field that handler three set, handler three is deleted as unused, and handler
nine fails with a missing key in production but not in the test that constructs
the request directly. Cause. Handlers began communicating through the request,
which converts an unordered chain into an undeclared workflow with implicit
dependencies. Fix. Make the dependency explicit. Either give the dependent
handler its own source for the value, or model the sequence as a workflow where
the ordering constraint is declared and checked.

**Chain used as a lookup table.** Symptom. A directory of forty handler classes,
each of which tests one string value and forwards otherwise, and a profile
showing measurable time in the dispatch. Cause. Chain of Responsibility applied
where the mapping from request to handler is a total function of one key. Fix.
Replace with a map from key to handler. Keep a chain only for the residual cases
where the decision genuinely depends on more than the key.

**Recursion depth exhaustion.** Symptom. A stack overflow under load and not in
testing, or a stack trace hundreds of frames deep consisting of alternating
runner and handler frames. Cause. A continuation-passing implementation whose
depth grows with chain length, combined with a chain that grew as plugins were
added, or a cycle in the successor links. Fix. Bound the chain length at
composition time. Detect cycles when building. Convert the recursive runner to an
iterative loop over an owned list where the language does not eliminate tail
calls.

**Exception swallowed mid-chain.** Symptom. A subset of requests returns a
generic error, and the underlying cause never appears in any log. Cause. A
handler catching broadly, logging at debug, and forwarding as though nothing
happened, so the failure is attributed to whatever ran next. Fix. Forbid catching
without either rethrowing or recording a typed failure on the request. Give the
runner one place that classifies and records failures, and let handlers throw.

**Handler with a side effect that runs twice.** Symptom. Duplicate audit rows or
double-charged operations that correlate with retries. Cause. A handler performs
a non-idempotent effect on the downstream pass, and a retry re-enters the chain
from the head. Fix. Move non-idempotent effects behind an idempotency key, or
place them after the point where the chain commits to handling the request.

**Chain composition differs between environments.** Symptom. A bug reproduces in
staging and not locally, or the reverse, with identical code. Cause. Composition
comes from configuration and the environments have drifted. Fix. Log the composed
chain, in order, at startup. This one line has resolved more incidents than any
other advice in this entry, and it costs nothing.

## 12. Trade-off matrix

Compared against named alternatives across the forces from dimension 3.

| Force | Chain of Responsibility | Decorator | Observer | Strategy with an explicit selector | Map or table dispatch | Mediator | Pipes and Filters |
|---|---|---|---|---|---|---|---|
| Sender knows the receiver | No, that is the point | No, but the wrapped object is fixed | No, but all subscribers act | Yes, the selector names it | Yes, the key names it | No, the mediator does | No, the pipeline is fixed |
| Number of participants that act | One, by the classical reading | All of them, always | All subscribers | Exactly one | Exactly one | Coordinated set | All stages |
| Can a participant stop the flow | Yes, that is handling | No, delegation always happens | No, notification is broadcast | Not applicable | Not applicable | Yes, the mediator decides | Rarely, stages transform |
| Order sensitivity | High, and usually in configuration | High, wrapping order matters | Low, order is unspecified | None | None | Medium, mediator logic | High, stages are a sequence |
| Guaranteed handling | No, this is the GoF liability | Yes, the core object always runs | Not applicable | Yes | Yes, or an explicit miss | Yes, mediator is present | Yes, output always produced |
| Adding a behaviour | New handler, edit composition | New wrapper, edit wrapping | New subscriber, no edits | Edit the selector | Add a key | Edit the mediator | New stage, edit pipeline |
| Latency | O(n) traversal, n indirect calls | O(n) wrappers, all executed | O(n) subscribers | One call | O(1) lookup | Central hop | O(n) stages |
| Traceability | Poor, composition is runtime | Poor, wrapping is runtime | Poor, subscribers are runtime | Good, source names it | Good, key is visible | Medium, one place to read | Good, pipeline declared |
| Team topology | Strong, independent contribution | Strong for wrapping concerns | Strong for fan-out | Weak, shared selector | Weak, shared table | Weak, mediator is a hotspot | Medium |
| Cognitive load | High, order plus n behaviours | Medium, one axis of wrapping | Medium, unknown listeners | Low | Low | High, mediator grows | Medium |
| Fit for cross-cutting concerns | Strong, its main use today | Strong, per-object rather than per-request | Weak, no request flow | Weak | Weak | Weak | Medium, data transforms |

Reading of the table. Chain of Responsibility wins where the identity of the
handler is a runtime property and the set of candidates must stay open. Decorator
wins where every wrapper must contribute and the object being wrapped is fixed.
Observer wins where the answer is fan-out with no notion of one owner. A map wins
whenever the mapping is total and keyed, which is more often than the pattern
gets used for. Mediator wins where participants must coordinate rather than
merely take turns. Pipes and Filters wins where the flow transforms data rather
than routing a request, and where every stage always runs.

## 13. Related and incompatible patterns

- **Decorator.** The closest neighbour in shape, and the comparison worth getting
  right, because both build a linear composition where each element holds the
  next. The difference is intent and obligation. A decorator adds behaviour
  around an object and always delegates, because the object it wraps is the thing
  the client asked for and skipping it would break the contract. A chain handler
  may decline to delegate, and declining is not a failure but the act of handling.
  Put differently, Decorator answers how to add behaviour to one known receiver,
  Chain of Responsibility answers who the receiver is. The Wikipedia treatment
  states the same distinction, that a chain lets exactly one handler process the
  request while decorators involve all of them
  (https://en.wikipedia.org/wiki/Chain-of-responsibility_pattern, verified
  2026-08-02). The pipeline dialect blurs this deliberately, because a middleware
  that always forwards and adds behaviour on both sides is a decorator in
  everything but name, which is why framework documentation uses the Intercepting
  Filter name rather than either GoF name.
- **Composite.** Composes naturally. The GoF pair them because a composite's
  parent link is a ready-made chain, and forwarding an unhandled request to the
  parent turns a tree into a chain for free. Apple's responder chain is this
  combination applied to a view hierarchy.
- **Command.** Composes cleanly. The request travelling the chain is often a
  command object, which gives it a uniform type, makes it queueable and
  loggable, and lets handlers inspect it without a growing parameter list. The
  alias Chain of Command invites confusion between the two, and they solve
  unrelated problems.
- **Mediator.** An alternative with the opposite topology. A chain distributes the
  routing decision across the handlers, each of which knows only its successor. A
  mediator centralises it in one object that knows every participant. Choose the
  chain when the set of participants should stay open, and the mediator when the
  coordination logic is the thing that matters and should be readable in one
  place.
- **Observer.** Frequently substituted for it by mistake. Observer notifies every
  subscriber, with no notion of one of them taking ownership and no ordering
  contract. When the requirement is that everybody hears about an event, use
  Observer. When the requirement is that somebody deals with it, use a chain.
- **Strategy.** A replacement when the selection rule is simple and knowable. A
  chain whose handlers each test one condition and forward is a linear search over
  a decision table, and a Strategy chosen by an explicit rule states the same
  thing without the traversal.
- **Template Method.** Composes as the internal shape of a handler. A base handler
  can implement the forwarding logic once and expose a hook for the acceptance
  test and the action, which removes the most common source of bugs, namely a
  handler that forgets to forward.
- **Interpreter and Visitor.** Both are better answers when dispatch is by the
  type or structure of the request rather than by a runtime predicate. A chain
  that tests the concrete type of the request in every handler is performing
  dispatch by hand, and a Visitor does that with the compiler checking coverage.
- **Null Object.** The natural terminal. A null handler that accepts everything
  and does nothing removes the end-of-chain conditional from every handler and
  makes the fall-off case an explicit participant rather than an absence.
- **Special Case and Circuit Breaker.** Both appear inside handlers rather than
  as alternatives. A circuit breaker placed as a handler is one of the cleanest
  uses of the pattern, because the breaker's open state is a short-circuit and the
  structure already supports it.

Nothing in this list is incompatible with the pattern in principle. The practical
conflicts are two. First, a chain combined with an implicit global request
context defeats the pattern's decoupling, because handlers begin depending on
each other through the global rather than through a declared contract. Second, a
chain used inside a transaction boundary conflicts with partial short-circuiting
unless the runner owns the transaction, since a handler that short-circuits after
another has written leaves the write half-done.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. The starting point is
normally a long conditional, a sequence of duplicated preliminary steps, or a
sender that holds references to several receivers.

1. Name the request. Extract the parameters the conditional tests into one
   object, or confirm one already exists. Handlers cannot share a signature until
   the request is a single value. Run the tests.
2. Extract each branch into its own function or class with an identical
   signature, still called from the original conditional in the original order.
   Nothing has changed in the design yet, and the tests still cover the same
   paths.
3. Split each extracted branch into two named parts, the predicate that decides
   whether it applies and the action that runs when it does. This step is what
   makes the branch relocatable, because the ordering constraint becomes visible
   as the overlap between predicates.
4. Introduce the handler contract. Declare the interface, make each extracted
   class implement it, and keep the original conditional calling them explicitly.
   The tests still pass and the pattern is not yet in place.
5. Replace the conditional with a runner over an ordered list built in the same
   order the conditional used. This is the moment the pattern exists. Prefer the
   owned-list variant from dimension 8 over the linked-successor variant, so the
   composition is a value from the start.
6. Add the terminal handler and give it a behaviour, whether default, error or
   metric. Do this in the same commit as step 5, not later, because the window
   between them is where the silent-drop failure gets shipped.
7. Add the ordering assertion test from dimension 11 and the startup log line
   from dimension 16. The pattern is now readable in production, which it was not
   at step 5.
8. Only now move handlers into their own modules if separate ownership is the
   goal. Doing this earlier makes every preceding step a cross-repository change.

The named refactoring closest to steps 2 through 5 is Replace Conditional with
Polymorphism, applied to a list rather than to a type hierarchy. See the
refactoring family entries for that and for Extract Class.

Removing the pattern when it stops earning its place. The signals are a chain
whose handlers all test one key, a chain that has had no new handler in two
years, or a chain of two.

1. Log the composition and the acted-handler identity in production for a full
   traffic cycle. Do not reason about which handlers matter, measure it. Handlers
   with zero acts across the cycle are the first candidates for deletion, after
   checking they are not rare-path safety handlers.
2. Determine whether the predicates are mutually exclusive. If they are, the chain
   is a lookup and the ordering carries no information, which makes the rest of
   the removal safe. If they overlap, the order encodes a priority that has to be
   preserved explicitly, and that priority needs writing down before anything
   moves.
3. For the mutually exclusive case, replace the chain with a map from the
   discriminating key to the handler, keeping the handler classes. Run the tests.
   The terminal becomes the miss branch of the lookup.
4. For the overlapping case, keep the ordered structure and stop here. The chain
   is doing real work that a map cannot express.
5. Inline handlers that have a single call site and no independent test, using
   Inline Class. Delete the interface once fewer than two implementations remain.
6. If the whole structure collapses to two cases, write the conditional. A
   two-branch conditional is more readable than any indirection, and the pattern
   can be reintroduced by following the steps above if a third case ever appears.

## 15. Testing and verification

Easier because of the pattern.

- Each handler is testable in isolation with no chain present. Construct the
  handler, hand it a request and a recording successor, and assert both the
  action and whether it forwarded. This is the pattern's main testability payoff,
  and it is the reason a chain beats a long conditional for test coverage.
- The forwarding decision is directly observable. A test double in the successor
  position records whether it was called, which turns the acceptance predicate
  into an assertion rather than an inference from side effects.
- Composition is testable separately from behaviour, provided the owned-list
  variant is used. A test can build the production chain and assert its order and
  membership without executing a single request.
- Fault injection is trivial. Inserting a handler that throws, delays or
  short-circuits at a chosen position tests the runner's error handling and the
  upstream half of every earlier handler.

Harder because of the pattern.

- Whole-system behaviour is a property of the composition, so unit coverage of
  every handler proves nothing about the system. A chain of individually correct
  handlers in the wrong order is a correct-looking test suite over a broken
  system.
- The unhandled path is easy to forget to test, because writing that test means
  constructing a request that every handler declines, which nobody does by
  accident.
- Interaction effects between handlers are combinatorial. A chain of ten handlers
  has more reachable orderings than any suite will cover, which is the argument
  for pinning one order rather than testing many.

Techniques that apply.

- **Recording successor as a test double.** A stub in the successor position that
  records invocation is a spy, and it is enough for nearly every handler test. It
  is preferable to a mocking framework here, because the contract is one method.
- **Composition assertion test.** One test that builds the production chain and
  asserts the ordered list of handler names. Cheap, and it converts the ordering
  regression from dimension 11 into a build failure.
- **Fall-off test per chain.** One test per chain that sends a request every
  handler declines and asserts the terminal behaviour. This is the single test
  most often missing, and it is the one that covers the GoF liability.
- **Contract test over the handler interface.** One abstract test class per
  contract, subclassed once per handler, asserting shared invariants such as
  forwarding when the predicate is false and not mutating the request when
  declining. This catches the handler that quietly rewrites a field before
  deciding it is not responsible.
- **Property test over permutations for order independence.** Where handlers are
  believed to be order independent, assert it by running a sample of permutations
  and comparing outcomes. Where the property fails, the failing permutation names
  the two handlers that actually depend on each other.
- **Golden path integration test through the real composition.** One test per
  route class that runs the real chain, so that unit coverage of handlers is
  backed by at least one execution of the thing that ships.

## 16. Observability signals

The pattern hides which handler acted, so if that fact does not appear in
telemetry, nobody can answer the first question of any incident.

What to record.

- At startup, one log line per chain listing the composed handlers in order. This
  is the highest-value signal in this entry relative to its cost, because it makes
  the invisible composition visible and it turns environment drift from a mystery
  into a diff.
- Per request, the identity of the handler that acted, as a structured field
  rather than free text. In the pipeline dialect record the handler that
  short-circuited instead, since that is the equivalent fact.
- A counter of handled requests labelled by acting handler. The label distribution
  is the shape of the traffic, and a change in the shape without a deployment is
  a routing incident.
- A counter of unhandled requests, incremented by the terminal handler. This
  counter should be zero in a healthy system, which makes it the cleanest alert
  in the pattern.
- A counter of short-circuits labelled by handler and reason, so that a rate
  limiter rejecting traffic and an authentication filter rejecting traffic are
  distinguishable without reading logs.
- Per-handler duration, as a span per handler in a trace where tracing exists, or
  a histogram labelled by handler name where it does not. A trace whose spans
  nest according to the chain is the clearest possible rendering of the pattern,
  because the nesting is the chain.
- Chain depth reached, as a histogram. In the pure dialect this says how far the
  average request travels before somebody claims it, which is the input to any
  reordering decision.
- Errors labelled by the handler that raised them and by position, so that a
  failure in a plugin is attributable to that plugin rather than to the runner.

A healthy instance on a dashboard. The startup composition matches the expected
list in every environment. The unhandled counter is flat at zero. The acting
handler distribution matches the traffic mix and moves only when a deployment
explains it. Chain depth is concentrated near the front for the common cases,
which is what a well-ordered chain looks like. Per-handler duration is flat, and
the sum of handler durations accounts for most of the request duration with no
unexplained gap.

A failing instance. The unhandled counter becomes non-zero, which means requests
are falling off the end and the terminal is doing its job of making that visible.
Or one handler's short-circuit counter climbs while total throughput is flat,
which points at a predicate that has started matching more than it should. Or
chain depth shifts to the tail across the board, which means the early handlers
stopped matching and the cause is upstream of the chain. Or the composition log
at startup differs from the previous deployment in a way the change log does not
explain, which is a configuration drift and should be treated as one. Or the
per-handler duration histogram develops a long tail on one label, which localises
a slow plugin without any code reading. Or request duration exceeds the sum of
handler durations by a growing margin, which is the hanging-request failure from
dimension 11 showing up as a gap rather than as an error.

## 17. Security and privacy implications

The pattern has a real security surface, and it comes from two properties. The
order is a correctness property that lives in configuration, and any handler can
stop the traversal.

**Ordering as a security control.** When authentication, authorization, input
validation or rate limiting are chain handlers, their position is the control.
Spring Security's documentation states that filters are executed in a specific
order to guarantee they are invoked at the right time, giving authentication
before authorization as the example (Spring Security documentation, verified
2026-08-02), and ASP.NET Core's documentation calls the ordering critical for
security (Microsoft Learn, verified 2026-08-02). A reordering therefore has the
same blast radius as deleting a check, and it is far less visible in review
because the diff touches one configuration line. Treat the composition file as
security-relevant code, require review from whoever owns the controls, and pin
the order with the assertion test from dimension 15.

**Short-circuit as an authorization bypass.** Any handler can end traversal, which
means any handler placed before a security check can bypass it. The ASP.NET Core
documentation gives the ordinary version of this, warning that static file
middleware serves files without authorization checks and that files it serves are
publicly available (Microsoft Learn, verified 2026-08-02). A caching handler, a
health check, a maintenance-mode handler and a debugging shim are all capable of
the same thing. The rule that follows is that anything placed before the security
handlers is part of the security boundary and has to be reviewed as such.

**Third-party handlers run with the chain's privileges.** A published handler
contract is an extension point that external code implements and the framework
then invokes with full access to the request, which routinely carries credentials,
tokens, session identifiers and personal data. A malicious or compromised plugin
can read all of it, rewrite the request before the security handlers see it, or
short-circuit and answer on the application's behalf. Where handlers are loaded
from a package registry or from disk, the chain is part of the supply-chain attack
surface. Pin the handler set at build time where the set is known, refuse
unexpected registrations, and place plugin handlers after the security handlers
rather than before, so that a plugin never sees an unauthenticated request.

**Registration order as an injection vector.** In systems where handlers register
themselves by scanning the classpath or a plugin directory, whoever controls load
order controls the chain. An attacker who can add a module or influence ordering
can place a handler at the front. Fix by making the composition explicit and
declared rather than discovered, or by failing loudly when the discovered set
differs from a recorded manifest.

**Denial of service through chain traversal.** Every request pays for every
handler, including declines. A long chain multiplies the cost of any request an
attacker can send, and a handler doing input or output per request turns a cheap
request into an expensive one. Bound chain length, put cheap and highly selective
handlers first so that rejections happen early, and place rate limiting before
anything expensive rather than after it.

**Silent discard as a security-relevant event.** The unhandled case is not only a
correctness problem. A request that falls off the end may be a probe for an
endpoint that does not exist, and discarding it silently, as Netty documents for
unhandled inbound events (Netty 4.1 documentation, verified 2026-08-02), removes
the signal. Record unhandled requests with enough context to feed intrusion
detection, while applying the privacy rules below.

On privacy the pattern is close to neutral in itself, with two practical caveats
worth stating rather than inventing further concerns. The first is that the
request object travels through every handler, so the least-privileged handler in
the chain sees the same data as the most privileged one. Where the request carries
regulated data, either redact before the general handlers or keep sensitive
fields in a side channel that only the handlers that need them can read. The
second is that the observability advice in dimension 16 records handler identity
per request, and handler names can encode a tenant, a region or a data-residency
tier. Where they do, treat that field as attributable data with the same retention
and access rules as any other identifier.

## 18. References

1. Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides. *Design Patterns.
   Elements of Reusable Object-Oriented Software*. Addison-Wesley, 1994.
   ISBN 0-201-63361-2. Chapter 5, Behavioral Patterns, section Chain of
   Responsibility. Source of the intent, the applicability list, the participants,
   and the consequence that receipt is not guaranteed and a request can fall off
   the end of the chain. Authorized publisher excerpt of the chapter at
   https://www.informit.com/articles/article.aspx?p=1398601 verified 2026-08-02.
2. Eclipse Foundation. *Jakarta Servlet Specification 6.1*, chapter 6, Filtering.
   https://jakarta.ee/specifications/servlet/6.1/jakarta-servlet-spec-6.1
   Verified 2026-08-02. Source for the location of the filtering chapter.
3. Eclipse Foundation. *Jakarta Servlet 6.1 API documentation*,
   `jakarta.servlet.FilterChain`.
   https://jakarta.ee/specifications/servlet/6.1/apidocs/jakarta.servlet/jakarta/servlet/filterchain
   Verified 2026-08-02. Source for the quoted description of the invocation chain
   and the doFilter contract.
4. Eclipse Foundation. *Jakarta Servlet 6.1 API documentation*,
   `jakarta.servlet.Filter`.
   https://jakarta.ee/specifications/servlet/6.1/apidocs/jakarta.servlet/jakarta/servlet/filter
   Verified 2026-08-02. Source for the list of intended filter uses.
5. Eclipse Foundation. *Jakarta EE Tutorial*, Jakarta Servlet chapter.
   https://jakarta.ee/learn/docs/jakartaee-tutorial/current/web/servlets/servlets.html
   Verified 2026-08-02. Source for the statement that filters are invoked in the
   order in which filter mappings appear in the deployment descriptor.
6. OpenJS Foundation. *Express documentation*, "Using middleware".
   https://expressjs.com/en/guide/using-middleware.html
   Verified 2026-08-02. Source for the middleware definition, the continuation
   contract, and the statement that a request will be left hanging when the
   continuation is not called.
7. Koa contributors. *Koa guide*.
   https://github.com/koajs/koa/blob/master/docs/guide.md
   Verified 2026-08-02. Source for the capture and bubble phases and the effect of
   omitting the continuation.
8. Microsoft. *ASP.NET Core Middleware*, Microsoft Learn.
   https://learn.microsoft.com/en-us/aspnet/core/fundamentals/middleware/
   Verified 2026-08-02. Source for short-circuiting, terminal middleware, the
   ordering statement, and the static-file authorization warning.
9. Netty project. *Netty 4.1 API documentation*, `io.netty.channel.ChannelPipeline`.
   https://netty.io/4.1/api/io/netty/channel/ChannelPipeline.html
   Verified 2026-08-02. Source for the Intercepting Filter attribution,
   bidirectional event flow, and silent discard of unhandled inbound events.
10. Python Software Foundation. *Python 3 documentation*, `logging` module.
    https://docs.python.org/3/library/logging.html
    Verified 2026-08-02. Source for logger propagation through ancestors and the
    handler of last resort.
11. Apple Inc. *Apple Developer documentation archive*, "Responder".
    https://developer.apple.com/library/archive/documentation/General/Conceptual/Devpedia-CocoaApp/Responder.html
    Verified 2026-08-02. Source for the responder chain, the next responder, and
    the discard of an unhandled event.
12. Broadcom. *Spring Security reference documentation*, "Architecture".
    https://docs.spring.io/spring-security/reference/servlet/architecture.html
    Verified 2026-08-02. Source for the filter chain proxy, the ordering
    requirement between authentication and authorization, and prevention of
    downstream invocation.
13. Wikipedia contributors. "Chain-of-responsibility pattern".
    https://en.wikipedia.org/wiki/Chain-of-responsibility_pattern
    Verified 2026-08-02. Used only to confirm the tree-of-responsibility variant
    and the wording of the Decorator contrast, not as a source of explanation.

## Code examples

Four languages, chosen because each shows a different shape the pattern takes.
Python shows the classical pure dialect with an explicit successor and a terminal
handler. TypeScript shows the continuation-passing pipeline with both traversal
directions. Go shows the wrapping variant that composes once at startup, which is
the idiomatic form in a language without inheritance. Java shows the owned-list
runner in the shape of a servlet filter chain. C# is omitted because its
idiomatic form is the same continuation-passing pipeline already shown in
TypeScript, and Rust is omitted because its two idiomatic forms are the boxed
trait-object list and the wrapping variant, both of which take the same shape as
the Java and Go examples here.

### Python

Classical pure dialect. Each handler decides, and a terminal handler makes the
fall-off case impossible.

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Request:
    kind: str
    amount: int


class Handler(ABC):
    def __init__(self) -> None:
        self._next: "Handler | None" = None

    def then(self, nxt: "Handler") -> "Handler":
        self._next = nxt
        return nxt

    def handle(self, req: Request) -> str:
        if self.accepts(req):
            return self.act(req)
        if self._next is None:
            raise RuntimeError(f"request fell off the chain: {req}")
        return self._next.handle(req)

    @abstractmethod
    def accepts(self, req: Request) -> bool: ...

    @abstractmethod
    def act(self, req: Request) -> str: ...


class TeamLead(Handler):
    def accepts(self, req: Request) -> bool:
        return req.amount <= 500

    def act(self, req: Request) -> str:
        return f"team lead approved {req.amount}"


class Director(Handler):
    def accepts(self, req: Request) -> bool:
        return req.amount <= 5000

    def act(self, req: Request) -> str:
        return f"director approved {req.amount}"


class Terminal(Handler):
    def accepts(self, req: Request) -> bool:
        return True

    def act(self, req: Request) -> str:
        return f"escalated to the board: {req.amount}"


def build() -> Handler:
    head = TeamLead()
    head.then(Director()).then(Terminal())
    return head


if __name__ == "__main__":
    chain = build()
    for amount in (100, 2000, 90000):
        print(chain.handle(Request("expense", amount)))
```

### TypeScript

Continuation-passing pipeline. Every handler may act before and after forwarding,
and any handler may short-circuit by not calling the continuation.

```typescript
type Ctx = { path: string; status: number; body: string; user?: string };
type Next = () => Promise<void>;
type Middleware = (ctx: Ctx, next: Next) => Promise<void>;

function compose(stack: Middleware[]): (ctx: Ctx) => Promise<void> {
  return function run(ctx: Ctx): Promise<void> {
    let index = -1;
    function dispatch(i: number): Promise<void> {
      if (i <= index) return Promise.reject(new Error("next called twice"));
      index = i;
      const fn = stack[i];
      if (!fn) return Promise.resolve();
      return fn(ctx, () => dispatch(i + 1));
    }
    return dispatch(0);
  };
}

const timing: Middleware = async (ctx, next) => {
  const started = Date.now();
  await next();
  ctx.body += ` [${Date.now() - started}ms]`;
};

const auth: Middleware = async (ctx, next) => {
  if (ctx.path.startsWith("/admin") && !ctx.user) {
    ctx.status = 401;
    ctx.body = "unauthorized";
    return;
  }
  await next();
};

const endpoint: Middleware = async (ctx) => {
  ctx.status = 200;
  ctx.body = `served ${ctx.path}`;
};

const app = compose([timing, auth, endpoint]);

async function demo(): Promise<void> {
  const open: Ctx = { path: "/home", status: 0, body: "" };
  await app(open);
  console.log(open.status, open.body);

  const denied: Ctx = { path: "/admin", status: 0, body: "" };
  await app(denied);
  console.log(denied.status, denied.body);
}

void demo();
```

### Go

The wrapping variant. Composition happens once at startup, and after composition
the chain is a single function.

```go
package main

import (
	"fmt"
	"strings"
)

type Request struct {
	Path string
	User string
}

type Response struct {
	Status int
	Body   string
}

type Handler func(Request) Response

type Middleware func(Handler) Handler

func Chain(h Handler, mw ...Middleware) Handler {
	for i := len(mw) - 1; i >= 0; i-- {
		h = mw[i](h)
	}
	return h
}

func Auth(next Handler) Handler {
	return func(r Request) Response {
		if strings.HasPrefix(r.Path, "/admin") && r.User == "" {
			return Response{Status: 401, Body: "unauthorized"}
		}
		return next(r)
	}
}

func Trace(next Handler) Handler {
	return func(r Request) Response {
		resp := next(r)
		resp.Body = resp.Body + " |traced"
		return resp
	}
}

func endpoint(r Request) Response {
	return Response{Status: 200, Body: "served " + r.Path}
}

func main() {
	app := Chain(endpoint, Trace, Auth)
	fmt.Println(app(Request{Path: "/home"}))
	fmt.Println(app(Request{Path: "/admin"}))
}
```

### Java

The owned-list runner, in the shape a servlet filter chain takes. The runner owns
the order, which makes the composition inspectable and testable.

```java
import java.util.List;

interface Filter {
    void doFilter(Message msg, FilterChain chain);
}

final class Message {
    String body;
    boolean committed;

    Message(String body) {
        this.body = body;
    }
}

final class FilterChain {
    private final List<Filter> filters;
    private int index = 0;

    FilterChain(List<Filter> filters) {
        this.filters = filters;
    }

    void proceed(Message msg) {
        if (index >= filters.size()) {
            if (!msg.committed) {
                msg.body = "unhandled: " + msg.body;
            }
            return;
        }
        Filter current = filters.get(index++);
        current.doFilter(msg, this);
    }
}

final class UpperCaseFilter implements Filter {
    public void doFilter(Message msg, FilterChain chain) {
        msg.body = msg.body.toUpperCase();
        chain.proceed(msg);
    }
}

final class RejectEmptyFilter implements Filter {
    public void doFilter(Message msg, FilterChain chain) {
        if (msg.body.isBlank()) {
            msg.body = "rejected";
            msg.committed = true;
            return;
        }
        chain.proceed(msg);
    }
}

final class TerminalFilter implements Filter {
    public void doFilter(Message msg, FilterChain chain) {
        msg.body = msg.body + " [done]";
        msg.committed = true;
    }
}

public final class Demo {
    public static void main(String[] args) {
        List<Filter> stack = List.of(
                new RejectEmptyFilter(), new UpperCaseFilter(), new TerminalFilter());
        Message ok = new Message("hello");
        new FilterChain(stack).proceed(ok);
        System.out.println(ok.body);

        Message empty = new Message("  ");
        new FilterChain(stack).proceed(empty);
        System.out.println(empty.body);
    }
}
```
