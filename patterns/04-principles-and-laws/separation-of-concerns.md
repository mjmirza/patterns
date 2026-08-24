---
name: Separation of Concerns
slug: separation-of-concerns
family: 04-principles-and-laws
category: Principle
aliases: [SoC, Concern Separation, Divide and Conquer for Software Structure]
first_described: "Dijkstra 1974"
maturity: canonical
related: [single-responsibility-principle, model-view-controller, layered-architecture, dependency-inversion-principle, hexagonal-architecture, cqrs, information-hiding]
incompatible_with: []
verified: 2026-08-02
---

# Separation of Concerns

## 1. Name, aliases, and lineage

The canonical name is Separation of Concerns, commonly abbreviated SoC. The phrase was
coined by Edsger W. Dijkstra in a 1974 essay circulated as EWD447, titled "On the Role
of Scientific Thought," archived at the University of Texas at Austin's Dijkstra
transcription project (https://www.cs.utexas.edu/~EWD/transcriptions/EWD04xx/EWD447.html,
verified 2026-08-02). The essay was later collected in Dijkstra's book *Selected Writings
on Computing. A Personal Perspective*, Springer-Verlag, 1982. In it Dijkstra wrote that he
sometimes called the discipline "the separation of concerns," describing it as, in his
words, the only available technique for effective ordering of one's thoughts, even when
perfect separation is not achievable. He illustrated the idea with program correctness. a
programmer should be able to reason about whether a program is correct without
simultaneously reasoning about how fast it runs, treating correctness and efficiency as
two concerns studied one at a time rather than as one tangled question.

Separation of Concerns is a principle, not a pattern with fixed participants, and this
matters for how the rest of this entry reads. A design pattern names a recurring
structural shape. A principle names a goal that many different structural shapes can
satisfy. Model-View-Controller, layered architecture, hexagonal architecture, the
Dependency Inversion Principle, and even the Unix pipe are all mechanisms that pursue
Separation of Concerns, but none of them is the principle itself. This entry treats SoC as
the parent goal and treats those mechanisms as dimension 8's implementation variants, the
concrete techniques a team reaches for on a given day.

David Parnas is the other name attached to this lineage, though he did not use Dijkstra's
phrase. In "On the Criteria to Be Used in Decomposing Systems into Modules," Communications
of the ACM, volume 15, issue 12, 1972, pages 1053 to 1058
(https://dl.acm.org/doi/10.1145/361598.361623, verified 2026-08-02), Parnas argued that
modules should be decomposed around design decisions likely to change, each module hiding
one such decision behind a stable interface, rather than decomposed by drawing a flowchart
and cutting it into sequential steps. Parnas called this information hiding. Where Dijkstra
gave the discipline its name and its cognitive justification, Parnas gave it its criterion.
a concern is something a module hides, and the right boundary is drawn around a single
reason to change, not around a single processing step. That criterion reappears almost
verbatim decades later as Robert C. Martin's Single Responsibility Principle, which states
that a module should have one, and only one, reason to change, in Robert C. Martin, *Agile
Software Development, Principles, Patterns, and Practices*, Prentice Hall, 2002, chapter 8.
The lineage runs Dijkstra names the goal in 1974, Parnas supplies the operational test in
1972 (published two years earlier, having circulated as a technical report before that),
and Martin restates the test as a class-level rule three decades later. This entry treats
the Single Responsibility Principle as SoC applied at the smallest unit of code, one class
or one function, and treats architectural patterns such as layered architecture as SoC
applied at the scale of an entire system. Both are the same principle at different zoom
levels, and this entry is written at the zoom level that spans both, from a single method
to a distributed system's service boundaries.

## 2. Problem and context

A codebase grows by accretion. A new requirement lands, and the fastest way to satisfy it
is to add a few lines wherever the relevant data already sits in memory. An order total
needs tax calculation, so the tax rate lookup goes into the same function that renders the
receipt, because the receipt function already has the order in scope. A validation rule
needs the current user's timezone, so the timezone lookup goes into the validator, because
the validator already has the request object. Each individual addition is locally
reasonable and locally cheap. The mistake is invisible at the moment it is made, because
nothing breaks and the diff is small.

The problem becomes visible later, when two unrelated changes turn out to require touching
the same function for unrelated reasons. The team wants to add a second tax jurisdiction,
which touches the receipt-rendering function because that is where tax logic lives. The
team also wants to redesign the receipt's visual layout, which touches the same function
for an unrelated reason. Two engineers, working on two unrelated stories, now collide on
one file, and a merge conflict that has nothing to do with either feature blocks both of
them. Worse, the engineer changing the visual layout can accidentally alter tax behavior,
because the two concerns share one function body and neither the compiler nor a quick
read of the diff can tell the reviewer which lines belong to which concern.

The context in which this becomes acute has three ingredients, and naming them matters
because dimension 4 explains where SoC is the wrong answer precisely by inverting these
three conditions. First, the system has more than one axis of change. Tax rules change on
a regulatory calendar, receipt design changes on a marketing calendar, and the two
calendars are independent. Second, more than one person or team touches the code, so a
tangled concern becomes a coordination cost between people who have no reason to talk to
each other. Third, the system is expected to live long enough that the cost of tangled
concerns compounds. a script run once and discarded never reaches the point where its
concerns need separating, because it never needs a second change. Separation of Concerns
is the discipline of drawing boundaries in a codebase so that each of these independent
axes of change lives behind its own interface, and a change along one axis touches code
that a change along another axis does not.

## 3. Forces

Separation of Concerns is a principle that resolves a tension between two costs that pull
in opposite directions, and every mechanism in dimension 8 is a different point on that
tradeoff curve.

- **Cost of change versus cost of indirection.** Favoring separation reduces the cost of a
  future change that falls cleanly within one concern, because that change touches one
  module. It raises the cost of reading the system today, because a reader must now
  traverse an interface boundary, sometimes several, to see the full behavior for a single
  request. A codebase with zero separation is the cheapest possible codebase to read for
  a single, simple task and the most expensive to change safely once two tasks compete for
  the same code.
- **Coupling versus cohesion.** Favored. The stated goal is to lower coupling between
  concerns while raising cohesion within each concern, in the sense both terms carry in
  Edward Yourdon and Larry L. Constantine, *Structured Design*, Yourdon Press, 1979, the
  book that formalized coupling and cohesion as measurable structural properties of a
  design.
- **Team topology.** Favored, and often the deciding force in practice. A concern boundary
  that matches a team boundary lets two teams ship independently. Melvin Conway's
  observation, first published as "How Do Committees Invent?", Datamation, April 1968,
  that a system's structure mirrors the communication structure of the organization that
  built it, means concern boundaries drawn against the org chart tend to survive, and
  concern boundaries drawn against it tend to erode back toward the org chart's actual
  seams.
- **Performance.** Frequently sacrificed, sometimes favored. A separated system typically
  pays for an interface crossing, a virtual call, a network hop, or a serialization step,
  at every concern boundary, which a tangled monolith avoids by keeping everything in one
  call frame with shared memory. The performance force can also favor separation when it
  lets each concern be optimized, scaled, or cached independently, which a tangled design
  cannot do because optimizing one concern risks breaking the others sharing its code path.
- **Testability.** Favored, and this is often the force that tips a borderline decision
  toward separating. A concern behind a narrow interface can be tested by substituting a
  test double for everything on the other side of that interface. A tangled concern can
  only be tested by exercising the whole tangle, because there is no seam to insert a test
  double at.
- **Consistency across concerns.** Sacrificed. When a rule genuinely spans two concerns,
  for example a discount that must be reflected consistently in both the order total and
  the tax calculation, separating the two concerns means that consistency now depends on
  both sides agreeing through their interface, rather than being enforced by both existing
  in one function where a single local variable could not disagree with itself.
- **Cognitive load per concern versus cognitive load of the whole system.** A well
  separated concern is small enough to hold in working memory on its own. The system as a
  whole becomes larger in total surface area, more files, more interfaces, more named
  concepts, so a newcomer's first-week cognitive load can be higher even as an experienced
  engineer's per-task cognitive load is lower.

No mechanism that implements SoC escapes this tradeoff. A pattern that claimed to separate
concerns at zero cost would not be describing a real design, it would be describing a
slogan.

## 4. Applicability and non-applicability

Reach for explicit separation when the following hold, echoing the three ingredients from
dimension 2.

- More than one axis of change touches the same code, and the axes change on different
  schedules or for different reasons. tax rules versus visual design, business rules versus
  storage technology, authentication versus authorization.
- More than one person, team, or organization owns adjacent parts of the behavior, and a
  clean interface would let them ship without coordinating on every change.
- The system's expected lifetime is long enough that the compounding cost of tangled
  concerns will exceed the one-time cost of drawing the boundary. A prototype meant to be
  thrown away after a two-week spike does not clear this bar.
- A concern needs to be tested in isolation, deployed on a different cadence, scaled
  independently, or replaced later, for example swapping a database vendor or a payment
  provider without touching the business rules that use it.
- Regulatory, security, or compliance boundaries require that one concern, for example
  payment card data handling, be demonstrably isolated from another, because an auditor
  needs to reason about the boundary directly rather than trusting that it exists
  somewhere inside a shared function.

Do NOT separate, and the reason matters more than the rule, in the following cases.

- **The code has one reader, one axis of change, and a short expected lifetime.** A data
  migration script run once, a notebook cell exploring a dataset, or a proof of concept
  meant to be deleted after a demo gains nothing from an interface it will never be asked
  to satisfy twice. The cost of the boundary is paid immediately and the benefit is never
  collected.
- **The two things that look like separate concerns actually change together, always,
  for the same reason.** If a validation rule and the persistence write it guards can never
  be correct independently of each other, separating them into two classes that must be
  kept in lockstep by convention introduces a coordination burden with no matching benefit.
  This is the case Parnas's criterion is meant to catch. decompose around independent
  reasons to change, not around every syntactic step in a process.
- **Premature separation before the second use case exists.** Splitting a single, concrete
  implementation into an abstraction with one implementer, in anticipation of a second
  implementer that has not yet been requested, produces speculative generality. The cost is
  paid today for a benefit that may never arrive, and if it does arrive, the shape of the
  eventual second concern is often not the shape the premature abstraction guessed. This
  overlaps with the code smell family entry on speculative generality and with the You
  Aren't Gonna Need It heuristic from extreme programming.
- **The interface crossing costs more than the whole operation is worth.** A hot inner loop
  that separates "compute the next pixel" from "write the pixel" behind virtual dispatch can
  lose an order of magnitude of throughput to a call that a compiler could otherwise inline,
  in a context, for example a real time renderer or an audio processing callback, where that
  order of magnitude is the entire budget.
- **Separation would hide a genuine, tight dependency that the reader needs to see.** Some
  correctness properties depend on two things happening atomically, in one transaction, with
  one lock held. Splitting them across a service boundary to satisfy a Separation of
  Concerns aesthetic, when the real requirement is atomicity, replaces a bug that was easy to
  see in one function with a distributed consistency bug that is hard to see across a
  network call. This is the specific failure named in dimension 11 as the distributed
  monolith.
- **The team is one person, or a small team with full context, and the coordination benefit
  that separation buys does not apply.** Conway's Law cuts both ways. a boundary drawn to
  match a team of one adds ceremony with no matching organizational payoff.

## 5. Structure

Separation of Concerns has no fixed participants, because it is a principle rather than a
pattern, but every concrete mechanism that implements it shares a small vocabulary that is
worth naming once here so the rest of the entry can use it precisely.

- **Concern.** A distinct area of a system's behavior or knowledge that has its own reason
  to change, independent of other concerns. Business rules, data persistence, network
  transport, presentation, authentication, and logging are common concerns in a typical
  application. A concern is defined by the question "who or what causes this to change," not
  by the syntactic shape of the code that implements it.
- **Boundary.** The line drawn between two concerns, realized in code as an interface,
  a function signature, a module boundary, a process boundary, or a network boundary. The
  boundary is where the cost from dimension 3 is paid, an interface crossing, and where the
  benefit is collected, an independently changeable, independently testable unit.
- **Interface.** The stable contract exposed at a boundary. What one concern is allowed to
  assume about another concern, and nothing more. A well drawn interface exposes the
  minimum a caller needs and hides the decision Parnas identified as likely to change.
- **Leaky boundary.** A boundary whose interface fails to hide the underlying decision, so
  a change on one side still forces a change on the other. A repository interface that
  returns a database-specific cursor type, rather than a plain domain object, has a boundary
  that exists on paper but leaks the persistence concern into every caller.
- **Cross-cutting concern.** A concern that, by its nature, touches many other concerns at
  once, rather than sitting cleanly behind one boundary. Logging, authentication,
  transaction management, and caching are the classic examples. cross-cutting concerns are
  the hardest case for SoC, because the natural boundary for the concern itself, "logging,"
  cuts across every other boundary in the system, and dimension 8 covers the specific
  mechanisms, aspect-oriented programming, middleware chains, and decorators, invented to
  address exactly this case.

There is no ASCII diagram of "the" participants for a principle. Dimension 6 instead shows
one common, concrete realization of the principle, a layered architecture, to make the
vocabulary above tangible, and dimension 8 shows several other realizations that use the
same vocabulary in different shapes.

## 6. ASCII structure diagram

```
   +-----------------------------------------------------------------+
   |                      Presentation Concern                       |
   |  HTTP routing, request parsing, response formatting             |
   +-----------------------------------------------------------------+
                         |            ^
                boundary |            | boundary
             (interface: |            | (interface: DTOs,
              use-case   |            |  domain results)
              request)   v            |
   +-----------------------------------------------------------------+
   |                     Application / Use Case Concern               |
   |  Orchestrates a single business operation, no HTTP, no SQL      |
   +-----------------------------------------------------------------+
                         |            ^
                boundary |            | boundary
             (interface: |            | (interface: domain
              domain     |            |  entities, errors)
              behaviour) v            |
   +-----------------------------------------------------------------+
   |                          Domain Concern                          |
   |  Business rules, invariants, no framework, no I/O                |
   +-----------------------------------------------------------------+
                         |            ^
                boundary |            | boundary
             (interface: |            | (interface: persisted
              repository |            |  records mapped back
              contract)  v            |  to domain entities)
   +-----------------------------------------------------------------+
   |                     Infrastructure Concern                       |
   |  Database access, external APIs, filesystem, message queues     |
   +-----------------------------------------------------------------+

   Each box owns one reason to change. A boundary is an interface,
   never a shared mutable object crossed without a contract.
   The arrows crossing a boundary carry data shaped for the receiver,
   never the sender's internal representation.
```

## 7. Dynamics

Because SoC is a principle, its "dynamics" are best shown as what happens when a single
change request enters a system built along the layered realization from dimension 6,
tracing which concern is touched and which concerns are untouched.

```
Change request: "Add a loyalty-points bonus for orders over 100 EUR"

  Presentation Concern    -- untouched. the HTTP request shape for
                             placing an order does not change.
         |
         v  (interface unchanged)
  Application Concern     -- touched. the order-placement use case
                             now also calls a new domain method,
                             AwardLoyaltyPoints, after the order
                             succeeds.
         |
         v  (interface unchanged: still returns an OrderResult)
  Domain Concern          -- touched. a new rule is added. an Order
                             whose total exceeds 100 EUR earns 10
                             loyalty points. This is where the rule
                             LIVES, because "when do we award points"
                             is a business decision, not an HTTP or
                             database decision.
         |
         v  (interface unchanged: repository still saves an Order
             and a LoyaltyAccount, both already-known domain types)
  Infrastructure Concern  -- touched only additively. a new column
                             or table to persist accumulated points,
                             added without altering how an Order is
                             read or written.

Result: two of four concerns changed, and neither of the two
untouched concerns needed a code review from someone who owns them,
because their interfaces did not move.
```

A second dynamic worth showing is what happens under a request-level trace once the
system is running, because this is the shape that a reader actually experiences in a
debugger or a distributed trace.

```
Client        Presentation      Application      Domain          Infrastructure
  |                |                 |              |                   |
  |-- POST /orders->|                 |              |                   |
  |                |-- parse+validate ->              |                   |
  |                |-- PlaceOrder(dto) ------------->|                   |
  |                |                 |-- rules ----->|                   |
  |                |                 |               |-- check invariant|
  |                |                 |               |-- save(order) -->|
  |                |                 |               |                  |-- INSERT
  |                |                 |               |<-- OK -----------|
  |                |                 |<-- Order -----|                   |
  |                |<-- OrderResult -|                                   |
  |<-- 201 JSON ----|                |                                   |
  |                |                 |                                   |
```

Every arrow that crosses a horizontal line in this trace is a boundary from dimension 6.
Nothing about the HTTP verb, the JSON shape, or the SQL dialect is visible once the trace
passes the Application line, and nothing about SQL is visible above the Infrastructure
line. That invisibility, not the number of files, is the actual measure of whether the
separation held.

## 8. Implementation variants

**Layered architecture.** Horizontal slicing by technical responsibility, the shape shown
in dimension 6. Presentation, application, domain, infrastructure, each layer depending
only downward. The classic and still the most widely taught realization, described at
length in Martin Fowler, *Patterns of Enterprise Application Architecture*, Addison-Wesley,
2002, chapter 1, under the name "Layering." Its weakness is that the domain layer, meant to
be the most stable, ends up depending on the layer below it unless the Dependency
Inversion Principle is applied at the layer boundary, which leads to the next variant.

**Hexagonal architecture, also called Ports and Adapters.** Alistair Cockburn's variant,
first published on his own site around 2005 and later formalized, which inverts the
layered dependency arrow so infrastructure depends on the domain rather than the other
way around, by placing an interface, a "port," inside the domain and an "adapter" outside
it that implements that port. The domain concern becomes the center of the system with no
outward dependency at all, and swapping a database or a message broker means writing a new
adapter, not touching the domain. This is the variant to reach for when the concern that
must remain most stable is the business rules, and everything else, including the choice
of framework, is expected to change more than once over the system's life.

**Model-View-Controller and its siblings, Model-View-Presenter and
Model-View-ViewModel.** A specialized, three-way separation for interactive user
interfaces, invented by Trygve Reenskaug in 1979 at Xerox PARC while working on
Smalltalk-76, first documented in his note "THING-MODEL-VIEW-EDITOR, an Example from a
Planning System," 12 May 1979, and refined into the Model-View-Controller name in his
second note, "MODELS-VIEWS-CONTROLLERS," 10 December 1979 (both discussed via the
Reenskaug MVC history summarized at
https://en.wikipedia.org/wiki/Model%E2%80%93view%E2%80%93controller, verified 2026-08-02).
MVC separates the Model, application state and business rules, from the View, presentation
of that state, from the Controller, translation of user input into changes to the Model.
Model-View-Presenter and Model-View-ViewModel are later variants that redraw exactly where
the presentation logic lives relative to the view, motivated by making the presentation
logic independently testable without a running UI framework in the loop.

**Aspect-oriented programming.** A mechanism aimed directly at the cross-cutting concern
problem from dimension 5. Rather than scattering logging, transaction boundaries, or
security checks through every module that needs them, an aspect declares "run this code
before or after any method matching this pattern," and a weaver inserts the behavior at
compile time or load time. AspectJ is the reference implementation for the Java ecosystem.
The cost is that the resulting call graph is no longer fully visible by reading the calling
code, because behavior is injected from outside the call site, which works against
dimension 3's operability force, and is why aspect-oriented programming has seen narrower
adoption than layering or MVC despite solving a real problem.

**Middleware and decorator chains.** The more widely adopted answer to the same
cross-cutting problem. a request passes through an ordered chain of small handlers, each
handling one concern, logging, authentication, rate limiting, before reaching the concern
that does the actual work. Express.js middleware, ASP.NET Core middleware, and the Java
Servlet filter chain are three independent ecosystems that converged on the same shape.
Unlike aspect weaving, the chain is visible in the code that assembles it, trading some of
aspect-oriented programming's brevity for the operability that comes from an explicit,
readable pipeline.

**Bounded contexts, from Domain-Driven Design.** Separation of Concerns applied at the
scale of an entire business domain rather than a single application. Eric Evans, *Domain-
Driven Design, Tackling Complexity in the Heart of Software*, Addison-Wesley, 2003, part
IV, defines a bounded context as an explicit boundary within which a domain model, and its
vocabulary, applies without ambiguity. "Customer" in the billing context and "Customer" in
the support context can carry different attributes and different rules, and DDD's answer
is not to force one shared Customer class, but to separate the two contexts and define an
explicit translation, a context map, where they must communicate. This is SoC applied to
the tangling of business vocabulary itself, a concern that neither layering nor MVC
addresses.

**Microservices.** Process-level, network-boundary separation, where each concern is not
merely a module with an interface but an independently deployable, independently scalable
process communicating over the network. The forces from dimension 3 are sharpened to their
extreme here. every boundary crossing now pays a network round trip and a serialization
cost, and every concern can now be owned, deployed, and scaled by a separate team on a
separate schedule, which is precisely the team topology force from dimension 3 taken to its
logical conclusion. Sam Newman, *Building Microservices*, 2nd edition, O'Reilly, 2021,
chapter 1, frames the entire book around exactly this tradeoff, independent deployability
purchased at the cost of distributed systems complexity.

**Command Query Responsibility Segregation, CQRS.** A narrower, more surgical separation
that splits the read concern from the write concern within what might otherwise be a
single data model. Martin Fowler describes it plainly. at its heart is the notion that a
different model can be used to update information than the model used to read it (Martin
Fowler, "CQRS," martinfowler.com, 14 July 2011,
https://martinfowler.com/bliki/CQRS.html, verified 2026-08-02). Fowler is explicit that this
should be applied to a narrow slice of a system, a specific bounded context under heavy,
asymmetric read and write load, rather than as a system-wide default, because the
consistency force from dimension 3 is sacrificed sharply. the read model and the write
model can disagree for a window of time.

**Language-level variants.** In functional languages, the separation is often expressed as
pure functions computing a decision, kept apart from an outer shell that performs I/O, a
shape informally called "functional core, imperative shell." In languages with strong
support for algebraic effects or monads, such as Haskell, the type system itself enforces
the boundary. a pure function's type signature makes it impossible to smuggle in an I/O
concern, which turns SoC from a convention a reviewer must check into a property the
compiler checks. Go and Rust, with no inheritance, typically implement layering through
small interfaces, an `interface` in Go or a `trait` in Rust, passed as constructor
parameters, the same dependency-inversion shape described above without any class
hierarchy at all.

## 9. Known production uses

**The OSI networking model.** The seven-layer Open Systems Interconnection model,
standardized as ISO/IEC 7498-1, separates the concern of physical bit transmission from
data link framing, from network routing, from transport reliability, from session, from
presentation encoding, from application semantics. Each layer is defined to depend only on
the service contract exposed by the layer below it, and to be replaceable without the
layers above knowing, which is the reason Ethernet, Wi-Fi, and fiber can all sit under the
identical TCP/IP stack that every application on the internet is written against. ISO/IEC
7498-1:1994, "Information technology, Open Systems Interconnection, Basic Reference Model,
The Basic Model."

**Ruby on Rails.** Rails structures every generated application around Model-View-
Controller as its explicit, documented architecture. The Rails Getting Started guide states
that Rails code is organized using the Model-View-Controller architecture, with the Model
managing application data, the View rendering responses, and the Controller handling
request logic (Rails Guides, "Getting Started with Rails,"
https://guides.rubyonrails.org/getting_started.html, verified 2026-08-02). Every Rails
application generated by the `rails new` scaffold inherits this separation as its default
directory structure, `app/models`, `app/views`, `app/controllers`, making it one of the
most widely deployed literal instances of Reenskaug's 1979 pattern in production today.

**Kubernetes' declarative configuration versus imperative automation.** The Kubernetes
documentation states that Kubernetes facilitates both declarative configuration and
automation, letting an operator describe the desired state for deployed containers while
Kubernetes' own control loops change the actual state to match (Kubernetes documentation,
"What is Kubernetes?," https://kubernetes.io/docs/concepts/overview/what-is-kubernetes/,
verified 2026-08-02). This separates the concern of what a cluster should look like, the
concern an operator authors, from the concern of how to reconcile the live cluster toward
that state, the concern the control plane's controllers own, and it is this separation that
lets a single YAML manifest be applied unchanged whether the underlying nodes are on a
laptop, a bare-metal datacenter, or three different public clouds at once.

**Netflix's microservice architecture.** Netflix is one of the most publicly documented
large-scale adopters of process-level Separation of Concerns, decomposing streaming
delivery, recommendation, billing, and content encoding into hundreds of independently
deployable services communicating through the Netflix API gateway, referenced directly in
Sam Newman, *Building Microservices*, 2nd edition, O'Reilly, 2021, chapter 1, as one of the
canonical early industry adopters of the pattern this entry's dimension 8 describes as
microservices, with ongoing detail published in the Netflix Technology Blog's architecture
series (https://web.archive.org/web/2/https://netflixtechblog.com/tagged/architecture,
verified 2026-08-09; the live tag page now returns a bot-block to automated requests,
checked directly against the same probe this catalogue's validator uses, so the Wayback
snapshot is cited in its place).

**The Unix operating system's pipe and filter design.** Doug McIlroy, inventor of the Unix
pipe, articulated the philosophy that shaped every Unix and Unix-derived tool since. write
programs that do one thing and do it well, write programs to work together, write programs
to handle text streams because that is a universal interface, a formulation later collected
in Peter H. Salus, *A Quarter Century of UNIX*, Addison-Wesley, 1994, and traced to
McIlroy's own writing beginning in the Bell System Technical Journal in 1978. `grep`,
`sort`, `wc`, and thousands of other small Unix utilities each own exactly one concern, and
the pipe operator is the boundary mechanism, a shared, minimal interface, a stream of
bytes, that lets any two of them compose without either one knowing the other exists.

## 10. Consequences

Positive.

- A change confined to one concern requires reviewing, testing, and reasoning about one
  module, not the whole system, which is the direct payoff of the coupling and cohesion
  force from dimension 3.
- Each concern can be tested in isolation behind its boundary, substituting a test double
  for the rest of the system, which is the direct payoff of the testability force and is
  covered in depth in dimension 15.
- Teams can own separate concerns and ship on separate schedules, satisfying Conway's Law
  rather than fighting it, which is often the largest real-world payoff even when the
  technical justification cited is something else.
- A concern can be replaced, upgraded, or reimplemented without the rest of the system
  knowing, provided its interface is honored, which is the property that lets a team swap a
  database vendor, a payment provider, or a UI framework years after the original decision.
- Knowledge required to reason correctly about one concern shrinks to what that concern's
  interface and internals actually contain, lowering the working-memory burden for any
  single task, even as the system's total surface area grows.

Negative.

- Every boundary is a cost paid on every request that crosses it, in call overhead,
  serialization, or network latency, and that cost is paid whether or not the flexibility
  the boundary bought is ever used.
- A reader tracing a single behavior across boundaries must now hold more than one file, or
  more than one process, in mind at once, and distributed tracing, log correlation, or a
  debugger that can step across process boundaries becomes a practical necessity rather
  than a nicety, once the separation crosses a network.
- Consistency that used to be free, because two facts lived in the same memory and could
  not disagree, now has to be actively maintained across the boundary, through a contract,
  a shared schema, or eventual consistency, and any drift between the two sides is a new
  class of bug that did not exist before the separation.
- Over-separation, drawing more boundaries than the system's actual axes of change justify,
  produces exactly the opposite of the intended benefit, more files and more indirection to
  change one thing, which is why dimension 4's non-applicability list and dimension 11's
  failure modes matter as much as dimension 8's techniques.
- Separation is not free to draw correctly the first time. finding the right boundary
  requires understanding which things actually change independently, and a boundary drawn
  around the wrong axis, for example by process step rather than by reason to change, costs
  the same indirection while delivering none of the benefit.

## 11. Failure modes and misuse

**The distributed monolith.** Symptom. A system of a dozen microservices that must be
deployed together, in a fixed order, because a change to one service's contract silently
breaks three others that were never given a stable interface to depend on, and there is no
way to test one service without standing up the other eleven. Cause. Separation was drawn at
the process boundary, satisfying the letter of dimension 8's microservices variant, without
first satisfying the interface discipline from dimension 5, so the boundary is a network
call wrapping what is, in behavior, still one tangled concern. Fix. Either restore the
missing interface discipline, versioned contracts, backward compatibility guarantees,
independent test doubles for each service, or admit the services were never actually
independent and fold them back into one deployable unit, which is often the honest and
cheaper repair.

**Anemic domain model.** Symptom. A "domain" layer that consists entirely of data
structures with getters and setters and no behavior, while every actual business rule lives
in a separate "service" layer that operates on those structures from the outside. Cause. A
literal, mechanical application of layering that mistook "put business logic in its own
layer" for "put business logic anywhere except the objects it is about," a distinction
Martin Fowler names directly as the Anemic Domain Model anti-pattern (Martin Fowler,
"AnemicDomainModel," martinfowler.com, https://martinfowler.com/bliki/AnemicDomainModel.html,
verified 2026-08-02). Fix. Move behavior that acts on an entity's own invariants back onto
that entity, reserving the service layer for orchestration across multiple entities, not
for logic that belongs to one.

**The god layer.** Symptom. One layer, usually a "service" or "utils" layer, that grows to
depend on every other layer and be depended on by every other layer, becoming the de facto
place every new feature's logic lands because nobody can agree which of the "real" layers
it belongs to. Cause. The original layer boundaries were drawn by technical category,
"business logic," rather than by an actual, testable criterion for what belongs where, so
ambiguous cases accumulate in whichever layer is easiest to reach from everywhere. Fix.
Redefine each layer's boundary with a concrete test, per Parnas's original criterion, "does
this code encode a decision likely to change independently of the others," and split the
god layer along the axes that answer reveals.

**Premature microservices.** Symptom. A team of five engineers running twenty services, each
one a thin wrapper over a single database table, spending more engineering time on
deployment pipelines, service discovery, and cross-service tracing than on the product
itself. Cause. Process-level separation was adopted for its reputation rather than because
the system had twenty genuinely independent axes of change and twenty teams to own them.
Fix. Consolidate services that share a deployment cadence and a single owning team back into
a modular monolith, a single deployable unit internally organized along the same concern
boundaries, revisiting the microservice split only when an actual, demonstrated need for
independent scaling or independent deployment appears.

**Leaky abstraction at the boundary.** Symptom. A repository interface, meant to hide the
persistence concern, that returns a raw SQL cursor, a database-specific exception type, or a
paging token tied to one storage engine's internals, so every caller ends up importing that
storage engine's library regardless of the interface's stated intent. Cause. The interface
was defined by copying whatever the concrete implementation already exposed, rather than by
asking what the consuming concern actually needs to know. Fix. Redefine the interface in
terms of the domain the caller understands, plain domain objects, a domain-level error type,
an opaque cursor value, and push every storage-specific detail behind the implementation the
caller never sees.

**Shotgun surgery across supposedly separated concerns.** Symptom. A single conceptual
change, for example renaming a field, requires editing a dozen files across layers that were
believed to be independently owned. Cause. Two or more "separated" concerns were, in fact,
sharing an implicit, unenforced dependency, often a data shape duplicated across boundaries
instead of defined once and referenced. Martin Fowler and Kent Beck describe this exact
symptom under the name Shotgun Surgery in Martin Fowler, *Refactoring, Improving the Design
of Existing Code*, 2nd edition, Addison-Wesley, 2018, chapter 3, listing it among the code
smells that indicate a concern was split along the wrong seam. Fix. Identify the shared data
shape or shared rule causing the fan-out, define it once behind a single owning concern, and
have every other concern reference that single definition rather than duplicating it.

## 12. Trade-off matrix

Compared against named alternative approaches to structuring a system's logic, across the
forces from dimension 3.

| Force | Layered architecture | Hexagonal architecture | MVC | Microservices | CQRS | Big Ball of Mud (no separation) |
|---|---|---|---|---|---|---|
| Coupling reduction | High between layers, downward only by convention | Highest. domain has zero outward dependency | High for a single interactive app | Highest, enforced by the network | High, but only between read and write paths | None |
| Cost of a single boundary crossing | One or two in-process calls | One in-process call through an inverted dependency | One or two in-process calls | A network round trip and serialization | An eventual-consistency window | Zero, and that is the whole appeal |
| Testability in isolation | Good, per layer | Best. domain tests need no framework at all | Good for the Model, harder for the View without a running UI framework | Best per service, hardest for the system as a whole | Good, read and write models tested separately | Poor to none |
| Independent team ownership | Weak, layers usually shared by one team | Weak to moderate | Weak, one app usually one team | Strongest, this is its primary justification | Moderate, within one bounded context | None |
| Consistency guarantee | Strong, one process, one transaction | Strong, one process | Strong, one process | Weakest, needs explicit sagas or eventual consistency | Deliberately relaxed between read and write | Strongest, everything shares memory |
| Onboarding cost for a newcomer | Moderate, must learn the layer map | Moderate to high, the port and adapter vocabulary is unfamiliar to newcomers | Low, MVC is broadly taught and recognized | High, must learn service topology and tooling | Moderate, an unfamiliar idea to most engineers on first encounter | Lowest to read one function, highest to change the system safely |
| Best fit | A single deployable app with a stable domain layer that should not depend on frameworks | A domain that must survive multiple, changing external technologies over a long life | An interactive application with a human user directly manipulating state | A large organization with independent teams needing independent deployment and scaling | One bounded context with asymmetric, heavy read and write load | A short-lived script or a true one-shot prototype |

Reading of the table. Every column to the left of Big Ball of Mud buys a reduction in
coupling and an increase in testability at a real, non-zero cost in either crossing
overhead, consistency strength, or onboarding difficulty. No column wins on every row.
choosing among them is choosing which force in dimension 3 the system can least afford to
sacrifice today.

## 13. Related and incompatible patterns

- **Single Responsibility Principle.** The class-level and function-level restatement of
  the same idea. Robert C. Martin's rule that a module should have one reason to change is,
  in this entry's terms, Separation of Concerns applied at the smallest unit of code, and
  Parnas's 1972 criterion is its direct ancestor.
- **Information Hiding.** Parnas's own name for the mechanism, distinct from but tightly
  bound to SoC. Information hiding is about what a module's interface conceals, its internal
  decision. SoC is about how the whole system is carved into modules in the first place. A
  system can be carved into the right concerns and still leak information across the
  boundary, which is dimension 11's leaky abstraction failure.
- **Dependency Inversion Principle.** The mechanism that makes hexagonal architecture and
  layered architecture actually hold their intended dependency direction. domain code
  depends on an abstraction it owns, and infrastructure code depends on that same
  abstraction, rather than the domain depending directly on infrastructure. Without
  dependency inversion, a layered system's "lower" layer ends up depended upon by the layer
  meant to be most independent of it.
- **Facade.** A different, narrower tool that is frequently confused with Separation of
  Concerns. Facade simplifies access to a set of classes that already exist behind one
  entry point. it does not, by itself, decide which concern owns which behavior. A Facade
  can sit in front of a system that has good separation or one that has none.
- **Law of Demeter.** A complementary discipline operating at the level of individual method
  calls rather than module boundaries, restricting an object to talking only to its
  immediate collaborators. A system with clean concern boundaries at the module level can
  still violate the Law of Demeter inside one concern by chaining calls through several
  intermediate objects, so the two disciplines are applied together, not as substitutes.
- **The Big Ball of Mud anti-pattern.** The direct opposite, named by Brian Foote and
  Joseph Yoder in "Big Ball of Mud," presented at the Fourth Conference on Pattern Languages
  of Programs, 1997 (https://www.laputan.org/mud/, verified 2026-08-02), describing a system
  whose structure is dictated by expediency rather than design, with no discernible concern
  boundaries at all. Foote and Yoder's own argument is more nuanced than "always avoid this."
  they observe that a Big Ball of Mud is often the economically rational outcome for
  software under continuous, unpredictable pressure, and that premature, speculative
  separation can itself produce a worse outcome than an honest, working tangle. This is the
  paper's own version of dimension 4's non-applicability warning.
- **Distributed systems and the CAP theorem.** Not a design pattern but a hard constraint
  that any process-level separation, dimension 8's microservices and any boundary crossing a
  network, must respect. once a concern boundary crosses the network, the consistency force
  from dimension 3 is no longer a design choice made freely, it is bounded by the physics of
  distributed consensus, and pretending otherwise is how the distributed monolith failure
  mode in dimension 11 gets built.
- **Aspect-oriented programming and middleware chains.** Both are answers to the specific
  sub-problem of cross-cutting concerns identified in dimension 5, and are treated as
  siblings of each other rather than of the layering or MVC variants, because they solve a
  different shaped problem, a concern that must touch many other concerns, rather than a
  concern that can be cleanly owned by one module.

## 14. Refactoring path in and out

Introducing separation into code that has none. This is the general shape of Martin
Fowler's Extract Class and Move Method refactorings, described in Martin Fowler,
*Refactoring, Improving the Design of Existing Code*, 2nd edition, Addison-Wesley, 2018,
chapter 7, applied deliberately along a concern boundary rather than opportunistically.

1. Identify two changes, real or anticipated from the actual backlog, that would touch the
   same function or class for genuinely unrelated reasons. If no such second change is
   planned, stop, per dimension 4's warning against premature separation.
2. Draw the boundary on paper first. name the interface the two sides will share before
   writing code, using the vocabulary each side already uses to talk about the data, not the
   vocabulary of whichever side is easiest to write first.
3. Extract the concern that is smaller or more stable first, usually the persistence or
   transport concern, into its own module behind the interface from step 2, while the rest
   of the code still calls it in the same tangled way it always did. Run the tests after this
   step, before moving anything else.
4. Extract the remaining concern into its own module, so the original tangled function is
   reduced to wiring, calling the first module's interface and then the second module's
   interface, with no logic of its own left. Run the tests again.
5. Delete the wiring function entirely if the caller can be pointed directly at the second
   module, or keep it as a thin composition root if the two modules genuinely need to be
   assembled in more than one place.
6. Add the interface-level test double described in dimension 15 for each newly drawn
   boundary, so the separation is provably testable in isolation, not merely file-level
   separate while still requiring the whole system to run for any test to pass.

Removing separation when it stops earning its place, following the reverse discipline.
Signals that a boundary should be collapsed include two modules that have not changed
independently of each other in the project's actual history, despite both existing "in
case," or a microservice that has never been deployed on a schedule different from its
sibling services.

1. Confirm from the actual commit history, not from intuition, that the two sides of the
   boundary have changed together in the overwhelming majority of past changes. This is the
   evidence that the boundary was drawn on the wrong axis or never needed at all.
2. Inline the smaller module's implementation into its single caller, the reverse of Extract
   Class, keeping the calling code's structure otherwise unchanged.
3. Delete the interface that separated them, and with it any adapter, factory, or dependency
   injection wiring that existed solely to satisfy that interface.
4. If the boundary was a network boundary, dimension 8's microservices variant, fold the two
   services into one deployable unit and delete the network client, the serialization layer,
   and any service-mesh configuration that existed only to connect them, which is often
   where the larger, hidden cost of the premature separation actually lived.
5. Re-run the full test suite and confirm no test was silently relying on the boundary
   existing, for example a test that substituted a fake for the now-inlined module. delete or
   rewrite such tests to exercise the merged behavior directly.

## 15. Testing and verification

Easier because of the pattern, when the boundary is drawn well.

- Each concern can be tested against its interface alone, substituting a hand-written test
  double, an in-memory fake, or a mock for whatever sits on the other side of the boundary,
  with no framework, no database, and no network required for the majority of test cases.
- A concern's tests do not need to be rewritten when an unrelated concern changes, because
  the interface, not the implementation on the other side, is what the test depends on.
- Contract tests can be written once against an interface and run against every
  implementation of it, the same technique described in the Factory Method entry's
  dimension 15, applied here to any boundary from dimension 5, confirming a persistence
  adapter, a payment provider adapter, or a caching adapter all honor the same contract the
  domain concern depends on.

Harder because of the pattern.

- An end-to-end test that exercises a real user scenario now has to cross every boundary the
  scenario touches, which means standing up more infrastructure, more test doubles, or more
  actual services than a tangled system would have required for the same scenario.
- A bug that only manifests from the interaction of two concerns, for example a timing issue
  that only appears once the persistence concern is genuinely asynchronous rather than an
  in-memory fake, will not be caught by either concern's isolated tests, only by an
  integration test that exercises the real boundary.
- Over-mocking is a specific risk this pattern invites. a test suite where every unit test
  mocks every collaborator can pass completely while the real, wired-together system fails,
  because the mocks silently drifted from what the real collaborator actually does. this is
  why contract tests, not only isolated unit tests, are necessary once real boundaries exist.

Techniques that apply.

- **Boundary-level unit tests with hand-written fakes**, preferred over heavy mocking
  frameworks for the reason above, an in-memory fake that implements the real interface is
  harder to drift silently out of sync with reality than a mock configured per test.
- **Contract tests**, one abstract test suite written against an interface, run once per
  concrete implementation, catching the case where an adapter satisfies the interface's type
  signature but not its actual behavioral contract.
- **A small number of true end-to-end tests**, deliberately kept few because of their cost,
  covering the critical paths that must be proven correct across every boundary the system
  actually has, rather than attempting to cover every path this way.
- **Architecture fitness functions**, automated checks, for example ArchUnit for Java or
  dependency-cruiser for JavaScript and TypeScript, that fail a build when a dependency
  crosses a boundary in the forbidden direction, for instance the domain concern importing
  from the infrastructure concern, turning the separation from a convention a reviewer must
  remember into a rule the build enforces on every commit.

## 16. Observability signals

Separation of Concerns is invisible in a single running process the way it is invisible in
source code once the boundaries hold, and the signals that matter are almost entirely about
detecting when a boundary that was supposed to be clean has, in practice, stopped being one.

What to record.

- A count or histogram of calls crossing each boundary, labelled by the calling concern and
  the called concern, so an unexpected new caller of, for example, the infrastructure
  concern directly from the presentation concern, becomes visible as a labelled data point
  rather than a silent architectural drift.
- Latency broken down per boundary crossing, distinguishing time spent inside a concern from
  time spent waiting on the concern across a boundary, which is the direct observability
  equivalent of the performance force from dimension 3, and is what tells an operator
  whether a slowdown is inside one concern's own logic or in the crossing itself.
- For a network-level boundary, dimension 8's microservices variant, the standard
  distributed-tracing span per service hop, so a single request's path across every service
  it touched is reconstructable after the fact, which is the operational replacement for
  being able to simply step through one process in a debugger.
- A count of interface violations caught by an architecture fitness function, dimension 15,
  tracked over time as a build-time metric, since a rising count is the earliest possible
  signal that a boundary is eroding before it produces a production incident.

A healthy instance on a dashboard. Boundary-crossing counts stay stable and match the set of
callers the architecture intends, latency inside each concern is flat and proportional to
that concern's actual work, and the architecture fitness function's violation count sits at
zero and stays there across deploys.

A failing instance. A boundary-crossing count that appears from a caller that should not
exist, for example the presentation concern suddenly calling the infrastructure concern
directly, which is the observable footprint of the god layer or leaky abstraction failure
modes from dimension 11. A latency histogram where the time spent crossing a boundary grows
disproportionately to the work being done on the other side, which often indicates the
boundary has silently become synchronous and blocking where it was designed to be
asynchronous, or that N calls are crossing the boundary in a loop where one batched call
was intended. A distributed trace, in the microservices variant, whose span count for a
single user-facing request keeps climbing release over release with no matching feature
added, the observable signature of the distributed monolith, where what should be one
concern is scattered across services each making its own round trip to the others.

## 17. Security and privacy implications

Separation of Concerns has a real and largely positive security implication when it is
drawn deliberately around trust and data-sensitivity boundaries, and a real, largely
negative one when it is drawn only around technical categories and assumed, wrongly, to
also be a security boundary.

**Blast radius reduction.** A concern that handles the most sensitive data, for example
payment card data or authentication credentials, benefits directly from being isolated
behind a narrow, well-defined interface with its own access controls, because a
compromise or a bug in an unrelated concern, for example the presentation layer's template
rendering, then has no direct path to that data. This is the architectural precondition for
compliance frameworks such as PCI DSS, which require demonstrable isolation of cardholder
data environments. drawing that isolation along Separation of Concerns lines, rather than
scattering payment handling across every layer that happens to need a price, is what makes
the compliance boundary auditable at all.

**A concern boundary is not automatically a trust boundary.** This is the failure worth
naming plainly. splitting code into a presentation concern and a domain concern says
nothing, by itself, about whether the presentation concern is allowed to send untrusted
user input straight into the domain concern's methods without validation. If input
validation is treated as "the presentation layer's job" and the domain layer trusts
whatever it receives because it assumes the presentation layer already checked, the
separation has created a false sense of safety, because any new caller of the domain
layer, a background job, an internal admin tool, a second API added later, inherits an
unvalidated trust assumption nobody wrote down. The fix is to make each concern responsible
for validating its own preconditions at its own boundary, never to assume the caller
already did it, which is the same discipline security practitioners call defense in depth
applied to internal, not only external, boundaries.

**Cross-cutting security concerns need their own deliberate boundary.** Authentication and
authorization are themselves cross-cutting concerns in the sense from dimension 5, and the
mechanisms in dimension 8 built for cross-cutting concerns, middleware chains in particular,
are the standard, well-tested place to enforce them exactly once, at the boundary every
request must cross, rather than reimplemented inconsistently inside every individual
concern that happens to need it. A system that instead checks authorization ad hoc, inside
whichever concern's code happened to reach the sensitive operation first, reliably produces
the class of vulnerability where one new endpoint, added later by someone unaware of the
convention, forgets the check.

On privacy, the same logic that reduces blast radius for a security breach applies directly
to data minimization. a concern that does not need personally identifiable data should not
receive it across its interface, even if the data happens to be available in the calling
concern's scope. Designing the interface at each boundary to pass only what the receiving
concern actually needs, rather than a convenient full object that happens to include more,
is a direct, practical application of the data minimization principle found in most modern
privacy regulation, and it is a natural byproduct of drawing interfaces well under
Separation of Concerns rather than a separate discipline layered on top.

## 18. References

1. Edsger W. Dijkstra. "On the Role of Scientific Thought," EWD447, August 1974.
   Archived at the E.W. Dijkstra Archive, University of Texas at Austin,
   https://www.cs.utexas.edu/~EWD/transcriptions/EWD04xx/EWD447.html verified 2026-08-02.
   Also collected in *Selected Writings on Computing, A Personal Perspective*,
   Springer-Verlag, 1982. Source for the coining of the phrase "separation of concerns" and
   the correctness-versus-efficiency illustration in dimensions 1 and 2.
2. D.L. Parnas. "On the Criteria to Be Used in Decomposing Systems into Modules,"
   Communications of the ACM, volume 15, issue 12, 1972, pages 1053 to 1058.
   https://dl.acm.org/doi/10.1145/361598.361623 verified 2026-08-02. Source for the
   information-hiding criterion in dimension 1 and the decomposition test in dimension 4.
3. Robert C. Martin. *Agile Software Development, Principles, Patterns, and Practices*.
   Prentice Hall, 2002. ISBN 0-13-597444-5. Chapter 8, the Single Responsibility Principle.
   Source for the class-level restatement of the principle in dimensions 1 and 13.
4. Edward Yourdon and Larry L. Constantine. *Structured Design, Fundamentals of a Discipline
   of Computer Program and Systems Design*. Yourdon Press, 1979. ISBN 0-917072-13-2. Source
   for the definitions of coupling and cohesion used in dimension 3.
5. Melvin E. Conway. "How Do Committees Invent?" Datamation, April 1968. Source for the
   organization-structure observation used in dimension 3.
6. Martin Fowler. *Patterns of Enterprise Application Architecture*. Addison-Wesley, 2002.
   ISBN 0-321-12742-0. Chapter 1, "Layering." Source for the layered architecture variant in
   dimension 8.
7. Alistair Cockburn. "Hexagonal Architecture." Original 2005 description, now hosted at
   https://alistair.cockburn.us/hexagonal-architecture/, verified 2026-08-09 (the older
   alistaircockburn.com path has since moved and 404s; the current cockburn.us URL is the
   live original). Source for the ports and adapters variant in dimension 8.
8. Trygve Reenskaug. "THING-MODEL-VIEW-EDITOR, an Example from a Planning System," 12 May
   1979, and "MODELS-VIEWS-CONTROLLERS," 10 December 1979. Historical summary at
   https://en.wikipedia.org/wiki/Model%E2%80%93view%E2%80%93controller verified 2026-08-02.
   Source for the origin of MVC in dimension 8.
9. Eric Evans. *Domain-Driven Design, Tackling Complexity in the Heart of Software*.
   Addison-Wesley, 2003. ISBN 0-321-12521-5. Part IV, bounded contexts. Source for the
   bounded context variant in dimension 8.
10. Sam Newman. *Building Microservices*, 2nd edition. O'Reilly, 2021. ISBN 978-1-492-03402-5.
    Chapter 1. Source for the microservices variant in dimension 8 and the Netflix
    production use in dimension 9.
11. Martin Fowler. "CQRS." martinfowler.com, 14 July 2011.
    https://martinfowler.com/bliki/CQRS.html verified 2026-08-02. Source for the CQRS
    definition and its narrow-scope warning in dimension 8.
12. ISO/IEC 7498-1:1994. "Information technology, Open Systems Interconnection, Basic
    Reference Model, The Basic Model." Source for the OSI model production use in
    dimension 9.
13. Rails Guides. "Getting Started with Rails," section on Model-View-Controller.
    https://guides.rubyonrails.org/getting_started.html verified 2026-08-02. Source for the
    Rails production use in dimension 9.
14. Kubernetes documentation. "What is Kubernetes?"
    https://kubernetes.io/docs/concepts/overview/what-is-kubernetes/ verified 2026-08-02.
    Source for the declarative-configuration production use in dimension 9.
15. Peter H. Salus. *A Quarter Century of UNIX*. Addison-Wesley, 1994. ISBN 0-201-54777-5.
    Source for Doug McIlroy's Unix philosophy formulation used in dimension 9.
16. Brian Foote and Joseph Yoder. "Big Ball of Mud." Fourth Conference on Pattern Languages
    of Programs, PLoP 1997. https://www.laputan.org/mud/ verified 2026-08-02. Source for
    the anti-pattern in dimension 13 and the economic-rationality caveat used in dimension 4.
17. Martin Fowler. "AnemicDomainModel." martinfowler.com, undated bliki entry.
    https://martinfowler.com/bliki/AnemicDomainModel.html verified 2026-08-02. Source for
    the failure mode in dimension 11.
18. Martin Fowler. *Refactoring, Improving the Design of Existing Code*, 2nd edition.
    Addison-Wesley, 2018. ISBN 978-0-13-475759-9. Chapter 3, code smells including Shotgun
    Surgery, and chapter 7, Extract Class and Move Method. Source for the failure mode and
    refactoring path in dimensions 11 and 14.

## Code examples

Three languages, each showing the same small system, an order-placement handler, separated
along the layered realization from dimension 6, presentation parsing and validating a
request, an application-level use case orchestrating the operation, and a domain rule the
use case calls, with a stubbed infrastructure concern kept intentionally simple so the
example stays runnable without a real database. Go is included because its lack of
inheritance makes the interface-based boundary from dimension 8's language-level variants
explicit and idiomatic, Python and TypeScript because both are common hosts for the layered
and hexagonal variants in real production code.

### TypeScript

```typescript
// Domain concern: business rule, no HTTP, no persistence detail here.
interface Order {
  id: string;
  totalCents: number;
}

function loyaltyPointsFor(order: Order): number {
  return order.totalCents >= 10000 ? 10 : 0;
}

// Infrastructure concern: the interface the domain and application depend on,
// implemented by whatever storage technology is chosen, kept out of sight.
interface OrderRepository {
  save(order: Order): void;
}

class InMemoryOrderRepository implements OrderRepository {
  private orders: Order[] = [];
  save(order: Order): void {
    this.orders.push(order);
  }
}

// Application concern: orchestrates one use case, knows the domain and the
// repository interface, knows nothing about HTTP.
class PlaceOrderUseCase {
  constructor(private readonly repo: OrderRepository) {}

  execute(id: string, totalCents: number): { order: Order; points: number } {
    const order: Order = { id, totalCents };
    this.repo.save(order);
    return { order, points: loyaltyPointsFor(order) };
  }
}

// Presentation concern: parses a plain request shape, calls the use case,
// formats a response. No business rule appears in this function.
function handlePlaceOrder(
  useCase: PlaceOrderUseCase,
  requestBody: { id: string; totalCents: number }
): { status: number; body: unknown } {
  if (!requestBody.id || requestBody.totalCents <= 0) {
    return { status: 400, body: { error: "invalid order" } };
  }
  const result = useCase.execute(requestBody.id, requestBody.totalCents);
  return { status: 201, body: result };
}

const repo = new InMemoryOrderRepository();
const useCase = new PlaceOrderUseCase(repo);
console.log(handlePlaceOrder(useCase, { id: "o-1", totalCents: 15000 }));
console.log(handlePlaceOrder(useCase, { id: "o-2", totalCents: 500 }));
```

### Python

```python
from dataclasses import dataclass
from typing import Protocol


# Domain concern.
@dataclass(frozen=True)
class Order:
    id: str
    total_cents: int


def loyalty_points_for(order: Order) -> int:
    return 10 if order.total_cents >= 10000 else 0


# Infrastructure concern, defined as an interface the domain depends on,
# not the other way around.
class OrderRepository(Protocol):
    def save(self, order: Order) -> None: ...


class InMemoryOrderRepository:
    def __init__(self) -> None:
        self._orders: list[Order] = []

    def save(self, order: Order) -> None:
        self._orders.append(order)


# Application concern.
class PlaceOrderUseCase:
    def __init__(self, repo: OrderRepository) -> None:
        self._repo = repo

    def execute(self, id: str, total_cents: int) -> dict:
        order = Order(id=id, total_cents=total_cents)
        self._repo.save(order)
        return {"order": order, "points": loyalty_points_for(order)}


# Presentation concern.
def handle_place_order(use_case: PlaceOrderUseCase, request_body: dict) -> dict:
    total = request_body.get("total_cents", 0)
    if not request_body.get("id") or total <= 0:
        return {"status": 400, "body": {"error": "invalid order"}}
    result = use_case.execute(request_body["id"], total)
    return {"status": 201, "body": result}


if __name__ == "__main__":
    repo = InMemoryOrderRepository()
    use_case = PlaceOrderUseCase(repo)
    print(handle_place_order(use_case, {"id": "o-1", "total_cents": 15000}))
    print(handle_place_order(use_case, {"id": "o-2", "total_cents": 500}))
```

### Go

```go
package main

import "fmt"

// Domain concern.
type Order struct {
	ID         string
	TotalCents int
}

func loyaltyPointsFor(o Order) int {
	if o.TotalCents >= 10000 {
		return 10
	}
	return 0
}

// Infrastructure concern, expressed as an interface the domain and
// application depend on. no struct here knows about SQL, files, or a
// network client, keeping that decision free to change later.
type OrderRepository interface {
	Save(o Order) error
}

type InMemoryOrderRepository struct {
	orders []Order
}

func (r *InMemoryOrderRepository) Save(o Order) error {
	r.orders = append(r.orders, o)
	return nil
}

// Application concern.
type PlaceOrderUseCase struct {
	repo OrderRepository
}

func (u *PlaceOrderUseCase) Execute(id string, totalCents int) (Order, int, error) {
	order := Order{ID: id, TotalCents: totalCents}
	if err := u.repo.Save(order); err != nil {
		return Order{}, 0, err
	}
	return order, loyaltyPointsFor(order), nil
}

// Presentation concern. plain function standing in for an HTTP handler,
// kept free of storage or business-rule detail.
func handlePlaceOrder(u *PlaceOrderUseCase, id string, totalCents int) (int, string) {
	if id == "" || totalCents <= 0 {
		return 400, "invalid order"
	}
	order, points, err := u.Execute(id, totalCents)
	if err != nil {
		return 500, "internal error"
	}
	return 201, fmt.Sprintf("order %s saved, %d points awarded", order.ID, points)
}

func main() {
	repo := &InMemoryOrderRepository{}
	useCase := &PlaceOrderUseCase{repo: repo}

	status, body := handlePlaceOrder(useCase, "o-1", 15000)
	fmt.Println(status, body)

	status, body = handlePlaceOrder(useCase, "o-2", 500)
	fmt.Println(status, body)
}
```
