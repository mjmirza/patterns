---
name: Law of Demeter
slug: law-of-demeter
family: 04-principles-and-laws
category: Principle
aliases: [Principle of Least Knowledge, Only Talk to Your Immediate Friends, One Dot Rule]
first_described: "Lieberherr and Holland, Northeastern University, 1987 to 1988"
maturity: canonical
related: [information-expert, low-coupling, high-cohesion, single-responsibility-principle, tell-dont-ask, hide-delegate, encapsulation]
incompatible_with: []
verified: 2026-08-02
---

# Law of Demeter

## 1. Name, aliases, and lineage

The canonical name is the Law of Demeter, abbreviated LoD. It is also called the
Principle of Least Knowledge, and its working motto, quoted in nearly every
later treatment, is "only talk to your immediate friends." A shorthand version
that circulates in code review comments is the "one dot rule," which is an
oversimplification covered in dimension 11.

The guideline was discovered, not designed, at Northeastern University in the
fall of 1987 by Ian Holland, a member of Karl Lieberherr's Demeter research
group. The group was building an adaptive, aspect-oriented programming system
named Demeter, after the Greek goddess of agriculture, chosen to represent a
bottom-up style of growing software from small, loosely coupled parts (Wikipedia
contributors, "Law of Demeter,"
https://en.wikipedia.org/wiki/Law_of_Demeter, verified 2026-08-02). The first
written formulation appears in Karl J. Lieberherr and Ian M. Holland,
"Formulations of the Law of Demeter," Technical Report NU-CCS-88-11 (also
referenced as Demeter-2), Northeastern University College of Computer Science,
June 1988. The idea reached a wide audience the same year through Karl J.
Lieberherr, Ian M. Holland, and Arthur J. Riel, "Object-Oriented Programming.
An Objective Sense of Style," published in ACM SIGPLAN Notices, OOPSLA '88
proceedings (dl.acm.org/doi/10.1145/62084.62113, verified 2026-08-02).

The name itself is a small joke inside a serious paper. The rule is not a law
of nature and it does not enforce itself, in the way the actual laws named
after other Greek figures in the group's other work did not either. The
authors wanted an aphorism that a working programmer could carry in their
head, and "only talk to your immediate friends" does that job better than
"minimize transitive coupling between method bodies and internal state of
collaborators," which is what the rule actually says.

Two things get conflated under this one name, and separating them matters more
than for most entries in this family.

- **The object-oriented formulation.** A method of an object may only send
  messages to a short, enumerable list of other objects. itself, its own
  fields, its arguments, and objects it creates locally. This is the version
  almost everyone means when they say Law of Demeter, and it is the subject of
  this entry.
- **The general software-engineering formulation.** "Each unit should have
  only limited knowledge about other units, only units closely related to the
  current unit," stated on the project's own reference page (Northeastern
  University, "Law of Demeter, General Formulation,"
  https://www2.ccs.neu.edu/research/demeter/demeter-method/LawOfDemeter/general-formulation.html,
  verified 2026-08-02). This wider statement predates classes as the unit of
  concern and applies to modules, functions, and even organizational units. It
  is the more defensible claim and the harder one to violate cleanly, because
  it is closer to a definition of coupling than to a checkable syntax rule.

## 2. Problem and context

A method reaches through an object it was handed to get at a second object,
then calls a method on that second object. The code compiles, the immediate
type checks are satisfied, and the method now silently depends on the internal
shape of a collaborator two or three hops away that it was never given a
direct reference to.

The failure this causes is not a runtime crash, it is a maintenance trap that
detonates later. Picture an order-processing method that receives a customer
object and needs to know the customer's postal code for a shipping
calculation. The path of least resistance is
`customer.getAddress().getPostalCode()`. That line works today. Eighteen
months later a colleague adds a billing address distinct from the shipping
address, or changes `Address` from a value object to an interface with two
implementations, or moves postal code validation into a new method on
`Address` that the order method now has to duplicate. None of those are
changes to `Customer`. All of them break the order method, because the order
method's contract with `Customer` was never really "give me a postal code," it
was "let me freely explore your entire object graph and I will decide for
myself what I need." The order method's true dependency surface is invisible
in its signature and only visible by reading its body.

The context in which this becomes expensive is any codebase with more than a
handful of collaborating types and more than one person changing them
independently. A single file with one author rarely pays this cost, because
the author holds the whole call graph in their head and updates every reach-
through in the same edit. The cost shows up exactly where object-oriented
design is supposed to earn its keep. a large system, several teams, types that
change on independent schedules, and a compiler that cannot tell you which of
the thousand call sites reaching into `Address` will break when `Address`
changes shape.

The Law of Demeter names the discipline that keeps that dependency surface
honest. A method should ask its direct collaborators to do things, not walk
across them to reach a third object and do the thing itself.

## 3. Forces

The rule trades one set of pressures for another, and pretending it is free is
the fastest way to apply it badly.

- **Coupling.** Strongly favoured. This is the entire point. A method that
  obeys the rule depends only on the interfaces of its immediate collaborators,
  never on the internal structure those collaborators expose through their own
  return values.
- **Encapsulation.** Favoured, and this is the deeper force behind the rule.
  Reaching through `a.getB().getC()` treats `B`'s internal reference to `C` as
  public information, even when `B` never declared it that way. The rule is a
  proxy for a stricter version of encapsulation than "make the field private"
  achieves on its own.
- **Interface size.** Sacrificed. The honest fix for a chain is usually a new,
  narrow method on the intermediate object, `customer.shippingPostalCode()`
  instead of two hops. Every chain removed this way adds one method to some
  class's public surface. Applied uncritically across a large codebase this
  produces classes with dozens of thin forwarding methods, discussed as
  interface bloat in dimension 11.
- **Indirection and readability at the call site.** Mixed. The call site gets
  shorter and its dependency becomes obvious from the signature, which helps
  readability locally. But the reader who wants to know where the postal code
  actually lives now has to follow one more hop through the wrapper method,
  which costs readability globally. This trade is exactly the one Fowler
  discusses under indirection in general, see the indirection entry in this
  family.
- **Performance.** Close to neutral in most managed runtimes, where an extra
  method call is inlined or costs nanoseconds against the surrounding work.
  This is engineering judgement, not a sourced fact. In a tight loop in a
  systems language, or across a network or process boundary where each hop is
  a real round trip rather than a local call, wrapping a chain into a single
  remote call can matter, and applying delegation the naive way can instead
  multiply round trips if each wrapper method itself becomes a remote call.
  The rule says nothing about which side of that boundary a wrapper sits on,
  and applying it without noticing the boundary is a real failure mode,
  covered in dimension 11.
- **Testability.** Favoured. A method with a short, declared list of
  collaborators is easy to give a test double for. A method that reaches three
  objects deep needs a test double whose own return values are themselves
  correctly configured test doubles, which is where fragile, over-specified
  mock setups come from.
- **Cost of change for the intermediate object.** Sacrificed in one narrow
  sense. Every forwarding method added to satisfy the rule is a new piece of
  the intermediate class's contract that must be kept working. If the
  intermediate class changes its own internal shape, it now has to update its
  forwarding methods too, but that update is local to one class instead of
  scattered across every caller that used to reach through it, which is the
  trade the rule is designed to make.

The rule favours coupling and encapsulation at the cost of interface size and
some indirection. That is a good trade when the reaching-through crosses a
real abstraction boundary between subsystems or teams. It is a bad trade
inside a single tight cluster of value objects that change together, covered
next.

## 4. Applicability and non-applicability

Reach for the Law of Demeter, meaning actively refactor a chain into a
message, when the following hold.

- The chain crosses a genuine module, layer, or team boundary. A service
  reaching into a domain object's internals is the case the rule was built for.
- The intermediate object's internal structure is a real implementation detail
  that is likely to change independently of the caller, for example an
  `Address` that might later become polymorphic, or a data-access object
  whose internal collection representation is not part of its contract.
- The method doing the reaching is business logic that should not need to know
  the shape of a data structure two levels down to do its job.
- The chain is genuinely load bearing for behaviour, not for pure data
  transfer. A method that decides something based on a nested value is exactly
  where Feature Envy and Law of Demeter violations coincide, see dimension 11.
- You are writing a public library or framework API. Every chain a caller must
  write against your types is now part of your API's stability surface, and a
  future internal restructuring on your side breaks every caller who wrote a
  chain.

Do NOT apply the Law of Demeter in these cases, and the reason matters more
than the rule itself.

- **Plain data structures, DTOs, and value objects with no behaviour.** A
  chain such as `order.customer.address.postalCode` in Python, or the
  equivalent field access in a record type, is not a Law of Demeter violation
  in any useful sense when `Order`, `Customer`, and `Address` are immutable
  data with public fields and no independent behaviour of their own. Wrapping
  every field access in a forwarding method to satisfy a syntactic reading of
  the rule buys nothing, because there is no encapsulated behaviour being
  bypassed, only a nested shape being read. This exact carve-out is why the
  rule reads differently in a language built around records, tuples, or
  dataclasses than in one built around encapsulated objects, and treating them
  the same is the most common over-application, discussed further in
  dimension 11.
- **Fluent interfaces and builders.** `StringBuilder.append("a").append("b")`
  and `queryBuilder.where(x).orderBy(y).limit(10)` chain many calls on one
  line and look identical in syntax to a violation. They are not violations,
  because every call in the chain returns the same receiver, or a builder
  still under construction, not a different collaborator whose internals are
  being reached into. The distinction is what each dot returns, not how many
  dots there are, which is why the syntactic "one dot rule" mentioned in
  dimension 1 is a bad proxy for the actual principle. The term "fluent
  interface" for this pattern was coined by Eric Evans and Martin Fowler in
  2005 specifically to name and legitimize the style (Wikipedia contributors,
  "Fluent interface," https://en.wikipedia.org/wiki/Fluent_interface, verified
  2026-08-02).
- **Standard library iterator and stream chains.** `list.stream().filter(...)
  .map(...).collect(...)` in Java, or `xs.iter().map(...).collect()` in Rust,
  chain through intermediate iterator objects that exist only to be chained
  through. Applying Law of Demeter here means not writing streams at all,
  which throws away one of the language's own idioms to satisfy a rule that
  was never aimed at it.
- **Navigating a well-known, stable domain hierarchy inside the domain's own
  code.** Code inside the `Address` module reaching into its own
  `PostalCode` value is not a violation, because the module boundary the rule
  cares about has not been crossed. The rule is about a caller reaching past
  a collaborator's boundary, not about internal structure that a single
  cohesive unit legitimately owns end to end.
- **When the fix would be a forwarding method that only ever has one caller.**
  A wrapper added to satisfy the letter of the rule, used exactly once, adds a
  permanent maintenance cost to remove a call site's transient one. This is
  the interface bloat force from dimension 3 tipping the trade the wrong way.
- **Hot paths where the extra indirection is measured to matter.** This is
  also engineering judgement, not a sourced fact. In code profiled to be
  latency critical, the rule yields to the measurement, the same way every
  stylistic guideline does.

The one-sentence test that resolves most of these cases is this. Does the
chain expose behaviour the intermediate object was meant to encapsulate, or
does it read a value the intermediate object was never meant to hide. The rule
protects the first case and has nothing useful to say about the second.

## 5. Structure

The Law of Demeter is not a structural pattern with participants that appear
in a class diagram, unlike a GoF pattern. Its structure is a rule about which
edges in the call graph are allowed to exist, stated as four permitted sources
for a message send inside a method `M` of a class `C`.

- **`C` itself.** `M` may call any other method on the object it belongs to,
  including private helpers. This is ordinary self-delegation.
- **`M`'s own parameters.** Anything passed directly into `M` is a declared,
  visible collaborator, and calling methods on it is fine. The dependency is
  documented in the method signature, which is the whole point.
- **`C`'s own fields, meaning `C`'s direct parts.** An object `C` composes,
  aggregates, or holds a reference to as one of its own attributes is a direct
  friend, and `M` may call methods on it.
- **Objects `M` creates locally.** Anything `M` instantiates with `new`, or
  the local equivalent, inside its own body is a friend for the duration of
  that call, because `M` fully controls its lifecycle and shape.
- **Global or class-level state accessible to `C`.** Named separately in the
  formal statement, and controversial in modern object-oriented style, since
  reliance on globals is itself usually a separate violation of low coupling,
  covered in that entry.

What is explicitly excluded, and this is the part that matters in practice,
is the return value of a call to any of the above, one level further out. If
`M` calls `this.getEngine()` and receives an `Engine`, `Engine` is not on the
friend list. `M` may not then call `engine.getSparkPlug().spark()`. `Engine`
was returned by a friend, it is not itself a friend, and its internal parts
are two hops removed and off limits.

The "participants" in this entry's dimension are therefore roles a method's
call graph is checked against, not classes in a diagram. the acting object,
its direct parts, its parameters, its locally-created objects, and the
forbidden category of an indirect object, meaning anything reached only
through the return value of a prior call.

## 6. ASCII structure diagram

```
                         +-------------------------------+
                         |     OrderProcessor (C)         |
                         |---------------------------------|
                         | - warehouse: Warehouse  (part)  |
                         | + ship(customer: Customer,      |
                         |        rules: ShippingRules)    |
                         +-------------------------------+
                                     |
              ---------- allowed call targets from ship() ----------
              |                     |                     |
              v                     v                     v
     +----------------+   +------------------+   +------------------+
     | this (C)       |   | customer         |   | rules            |
     | self methods   |   | (a parameter)    |   | (a parameter)    |
     +----------------+   +------------------+   +------------------+
              |
              v
     +----------------+
     | warehouse      |
     | (a direct part)|
     +----------------+

     FORBIDDEN, one hop further out:

     customer.getAddress()              --- allowed, customer is a friend
                    |
                    v
     .getPostalCode()  <-- NOT allowed, Address was returned by a call,
                            not passed to ship() and not a field of C.

     The rule draws the boundary at the first return value.
     Anything reachable only by calling a method ON a return value
     of a prior call is out of bounds, regardless of how useful
     that value looks from where you are standing.
```

## 7. Dynamics

The rule has no runtime behaviour of its own. It constrains which messages a
method is allowed to send while it executes, so its "dynamics" are best shown
as the difference between a call graph that satisfies it and one that does
not, walked through as a sequence.

```
VIOLATING sequence, ship() reaches through Customer into Address:

  ship(customer, rules)
      |
      |-- customer.getAddress() ------------------> Customer
      |                                                 |
      |<-- returns Address instance --------------------|
      |
      |-- address.getPostalCode() -----------------> Address
      |                                                 |
      |<-- returns "94107" -----------------------------|
      |
      |-- rules.costFor("94107") ------------------> ShippingRules
      |
      |   ship() now depends on the fact that Customer HAS an
      |   Address, AND that Address HAS a postal code accessor,
      |   AND the exact method name and return type of each.
      |   Two intermediate contracts leaked into one caller.


COMPLIANT sequence, ship() asks its direct friend for the answer:

  ship(customer, rules)
      |
      |-- customer.shippingPostalCode() -----------> Customer
      |         |
      |         |-- this.address.getPostalCode() --> Address
      |         |<-- returns "94107" ----------------|
      |<-- returns "94107" -----------------------------|
      |
      |-- rules.costFor("94107") ------------------> ShippingRules
      |
      |   ship() now depends on ONE contract. Customer knows its own
      |   shipping postal code. Customer's internal choice to store
      |   an Address, and Address's own internal shape, can both
      |   change without touching ship() at all.
```

The second sequence has the same number of underlying calls, in fact one more,
because `Customer.shippingPostalCode()` itself now performs the reach that
`ship()` used to perform directly. Nothing was eliminated. What changed is
which unit owns the knowledge of how to get from a `Customer` to a postal
code, and therefore which unit has to change when that path changes.

## 8. Implementation variants

**Manual forwarding method.** The direct fix from dimension 7. The
intermediate class gains a small method that performs the reach internally
and returns the final value. This is the shape of Martin Fowler's Hide
Delegate refactoring, discussed in dimension 14.

**Tell, Don't Ask.** A companion discipline, not the same rule, often applied
alongside Law of Demeter. Where Law of Demeter restricts which objects a
method may query, Tell Don't Ask restricts how a method uses the objects it
is allowed to query, favouring "tell this object what to do" over "ask this
object for its state and then decide for it." Andrew Hunt and David Thomas
discuss the closely related idea under encapsulating behaviour with data in
*The Pragmatic Programmer*, 2nd edition, Addison-Wesley, 2019. Applying Tell
Don't Ask on top of Law of Demeter is usually what turns
`shipping.costFor(customer.shippingPostalCode())` into
`customer.shipVia(shipping)`, pushing the decision itself into the object that
holds the relevant state rather than merely relocating the data access.

**Extension methods and free functions over a narrow interface.** In
languages that support extension methods or free functions, such as C#
extension methods or Kotlin extension functions, a Demeter-compliant helper
can live outside the class entirely, operating only on that class's already
public, minimal interface, rather than being added as a member. This keeps
the intermediate class's own surface smaller while still avoiding a chain at
the call site.

**Automatic delegation macros or generators.** Some languages and frameworks
generate forwarding methods rather than requiring them to be hand-written.
Ruby's `Forwardable` module and its `def_delegator`, and Rails'
`Module#delegate`, generate a method that internally performs exactly the reach a
strict reading of the rule forbids at the call site, and expose it as a single
message. This does not eliminate the reach, it relocates it to a place the
class itself owns and can change in one location, which is the actual goal.

**Functional composition instead of chaining through objects.** In functional
or functional-leaning code, the equivalent discipline is passing a narrow,
purpose-built function rather than an object whose internals get walked. A
function `customer -> postalCode` supplied at the call site, or a lens or
optic in languages that support them, achieves the same narrowing of what the
caller depends on without requiring an object-oriented forwarding method at
all. This is the natural translation of the rule into a language like Haskell
or a functional core in TypeScript, where the "friend list" concept maps onto
which values a function closes over or receives as arguments rather than
onto class membership.

**Read-only projection or DTO at a boundary.** At a genuine architectural
boundary, for example between a domain layer and a presentation layer, a
common variant is to have the domain object expose a flat, purpose-built
projection type containing exactly the fields a caller on the other side of
the boundary needs, rather than either a chain or a pile of individual
forwarding methods. This is the dimension-4 exception for plain data
structures applied deliberately. behaviour stays behind the Law of Demeter
boundary, and only inert data crosses it.

## 9. Known production uses

**PMD, `LawOfDemeter` rule, `category/java/design.xml`.** PMD, the static
analysis tool for Java and several other languages, ships a rule literally
named `LawOfDemeter` in its design rule category, which flags method chains
that reach past a method's direct collaborators. Release notes for PMD 6.19.0
record a refinement to the rule so that it "ignores now also Builders, that
are not assigned to a local variable, but just directly used within a method
call chain," which is the tool-maintainer version of the fluent-interface
carve-out in dimension 4 (PMD project, "PMD 6.19.0 released,"
https://pmd.github.io/2019/10/31/PMD-6.19.0/, verified 2026-08-02).

**Martin Fowler, "Hide Delegate" refactoring, catalogued in *Refactoring*.**
Fowler's refactoring catalog names the exact operation this entry describes
as a refactoring in its own right, moving a delegated call behind a method on
the object the caller already holds a direct reference to, precisely to avoid
a caller needing to know the delegate exists at all. Martin Fowler,
*Refactoring. Improving the Design of Existing Code*, 2nd edition,
Addison-Wesley, 2018, ISBN 978-0-13-475759-9, catalog entry "Hide Delegate."
The refactoring's own motivation section frames it in terms of encapsulation
and reducing what a client needs to know, the same forces named in dimension
3 of this entry.

**Ruby's `Forwardable` standard library module and Ruby on Rails'
`Module#delegate`.** Both provide a generator for the manual forwarding method
described in dimension 8, and both are widely used specifically to avoid
writing a chain at a call site in favour of a single message on a directly
held object. The Rails API documentation describes `delegate` as exposing "a
contained object's public methods as your own," and calls out Active Record
associations as a particular case where a model commonly delegates to an
association rather than requiring callers to traverse it (Rails API
documentation, `Module#delegate`,
https://api.rubyonrails.org/classes/Module.html#method-i-delegate, verified
2026-08-02). The documentation itself does not use the phrase Law of Demeter,
so the connection to this entry is this entry's own analysis, not a sourced
claim, and is labelled as such here.

## 10. Consequences

Positive.

- A method's true set of collaborators is visible in its signature and its
  own field declarations, rather than hidden inside chains buried in its
  body, which makes the actual dependency graph of a codebase legible from
  outside any single method.
- Changing an intermediate object's internal structure touches only that
  object's own forwarding methods, not every caller who used to reach through
  it, which turns a scattered, multi-file change into a local one.
- Test doubles stay shallow. A caller that only ever talks to its direct
  collaborators needs only those collaborators faked, not a chain of
  correctly configured nested fakes.
- Encapsulation is enforced at the level of behaviour, not merely at the
  level of field visibility, closing a gap that "make every field private"
  alone leaves open whenever a getter returns a mutable or navigable object.

Negative.

- Interfaces of intermediate classes grow. Every reach that gets pushed
  behind a forwarding method is a new method some class now has to declare,
  document, and keep working, and this can genuinely bloat a class that sits
  between many callers and many collaborators.
- An extra layer of indirection sits between the reader and the place a value
  actually lives, which costs a reader who is trying to trace data flow one
  more hop, discussed as the indirection trade-off in dimension 3.
- Mechanically applied without judgement, it produces the exact anti-pattern
  the rule was meant to prevent elsewhere. a class whose entire surface is
  thin, purposeless forwarding methods with no cohesive responsibility of its
  own, sometimes derided as a Middle Man, covered in the design smells family.
- It says nothing about where a call boundary sits physically. Naive
  application across a network or serialization boundary can turn one remote
  call into several, trading a coupling problem for a latency problem.

## 11. Failure modes and misuse

**The syntactic "one dot rule."** Symptom. A linter or a reviewer flags
`a.b().c()` on sight, regardless of what `b()` returns, and flags nothing
about `orderDto.customer.address.postalCode` on a plain record type with five
dots. Cause. Treating dot count as the measure instead of asking whether the
value being reached for is behaviour the intermediate object owns or plain
data it never meant to hide. Fix. Apply the dimension-4 test, does the chain
cross a real encapsulation boundary, and drop chain-counting linters or
configure them to exempt records, DTOs, and known fluent APIs.

**Forwarding-method explosion, the Middle Man smell.** Symptom. A class whose
public interface is fifteen or more one-line methods that each call exactly
one method on exactly one field, and the class itself has no logic of its own.
Cause. Every reach anywhere in the codebase getting mechanically pushed onto
one intermediate class instead of being questioned. Fix. If a class exists
only to forward, most callers should hold a direct reference to what they
actually need instead, or the two classes should be merged. See the Middle
Man entry in the design smells family and the Inline Class refactoring.

**Confusing Law of Demeter with information hiding of data, not behaviour.**
Symptom. A team wraps every nested field access in an immutable value object
in a forwarding method "to follow Demeter," and the codebase fills with
one-line accessors that add indirection but remove no real coupling, because
there was never any behaviour being bypassed. Cause. Missing the distinction
in dimension 4 between reaching into behaviour and reading structure. Fix.
Reserve the rule for objects with real, changeable internal structure and
behaviour, and let plain data structures be navigated directly.

**Hiding a Feature Envy problem instead of fixing it.** Symptom. A method
reaches deep into another object's data to compute something, gets flagged
for a Law of Demeter violation, and the fix applied is a forwarding method
that returns the same raw data one hop closer, after which the original
method still does all the same computation with data that clearly belongs
somewhere else. Cause. Treating the rule as being about call syntax rather
than about where behaviour belongs. Fix. Diagnose Feature Envy first, see the
feature envy entry, and move the computation itself to the object whose data
it needs, which usually removes the chain and the need for a forwarding
method at the same time.

**Blind delegation across a network or process boundary.** Symptom. A
distributed service is refactored so that a client never reaches two hops
into a remote object's response, and each hop is turned into its own remote
call on the server side instead, and overall request latency goes up because
what used to be one network round trip carrying a nested payload is now
several. Cause. Applying an in-process design rule without accounting for
where the actual expensive boundary is. Fix. At a genuine remote boundary,
prefer the read-only projection or DTO variant from dimension 8, sized to
exactly what the caller needs in one call, rather than mechanical forwarding
methods that each individually cross the boundary.

**Confusing the rule with a ban on method chaining in general.** Symptom. A
code review rejects a builder or a stream pipeline because it "has too many
dots." Cause. Not checking what each link in the chain actually returns. Fix.
Apply the fluent-interface and iterator-chain exceptions from dimension 4.

## 12. Trade-off matrix

Compared against named alternative approaches to the same coupling problem,
across the forces from dimension 3.

| Force | Law of Demeter (forwarding methods) | Tell, Don't Ask | Flat DTO or projection at a boundary | Public getters with no restriction | Dependency injection of the narrow value directly |
|---|---|---|---|---|---|
| Coupling to intermediate internals | Low. Caller depends only on the direct collaborator's interface | Low, and also removes the query itself | Low. Caller depends on a flat shape, not a graph | High. Caller may walk the entire object graph | Lowest. Caller never sees the intermediate object at all |
| Interface size of the intermediate class | Grows, one forwarding method per reach | Grows differently, gains behaviour methods instead of accessors | Neutral for the domain object, a mapping method is added once | Neutral, only original accessors exist | Neutral, nothing added to the intermediate class |
| Where behaviour lives | Still in the caller, only the data access moved | In the object that owns the state, which is the point | In the caller, using flat data | In the caller | In the caller, using an injected value |
| Suitability for plain records or DTOs | Poor fit, adds needless indirection, see dimension 4 | Not applicable, DTOs have no behaviour to tell | Strong fit, this is the same shape | Fine as is | Fine as is |
| Suitability across a remote or serialization boundary | Poor if applied per hop, see dimension 11 | Not directly applicable across a boundary | Strong fit, purpose-built payload | Fine but exposes internal shape over the wire | Requires the value already be resolved before the call |
| Readability at the call site | Improves, shorter and named | Improves most, intent is explicit | Improves, flat and predictable | Chain is explicit about the path but exposes structure | Best, the caller states exactly what it needs |
| Testability | Improves, shallow fakes suffice | Improves most, fewer branches to fake | Improves, fake the flat shape | Poor, nested fakes required for deep chains | Best, no object to fake at all |
| Risk of overuse | Middle Man smell, dimension 11 | Can hide genuinely needed queries if overapplied | Payload can drift out of sync with the domain model | Not a risk of overuse, the risk is under-encapsulation | Constructor or parameter list growth if overused broadly |

Reading of the table. Law of Demeter's forwarding-method form is the right
tool when a real behavioural boundary exists and the caller genuinely needs a
computed answer from across it. Tell Don't Ask goes further and is preferable
when the caller was only ever going to use the queried value to make an
immediate decision. A flat DTO wins at true architectural or network
boundaries where the cost of many small forwarding calls would be paid
repeatedly. Plain public getters remain correct for value objects and
records where there is no behaviour to protect. Injecting the narrow value
directly is the strongest option whenever the caller's own construction site
can resolve the value in advance.

## 13. Related and incompatible patterns

- **Tell, Don't Ask.** The closest companion, not a duplicate. Law of Demeter
  restricts which objects a method may query. Tell Don't Ask restricts
  whether a method should be querying at all, versus commanding the object
  that holds the state to act. Applying both together is common and usually
  produces the strongest result, discussed in dimension 8.
- **Information Expert (GRASP).** Complementary and often the actual fix
  behind a Law of Demeter refactor. Information Expert says the method that
  needs data should live on the object that already holds that data. A
  forwarding method that just relocates a getter without moving any logic is
  Law of Demeter without Information Expert, and is the shallow version of
  the fix criticized in dimension 11's Feature Envy failure mode.
- **Low Coupling and High Cohesion (GRASP).** Law of Demeter is a concrete,
  checkable instance of the general Low Coupling principle, applied
  specifically to the shape of method call chains. High Cohesion is the force
  that keeps the forwarding methods added to satisfy Demeter from
  accumulating on a class that has no other reason to hold them, which is
  what prevents the Middle Man smell.
- **Hide Delegate refactoring.** The direct mechanical operation for
  satisfying the rule when a violation is found in existing code, catalogued
  by Fowler and cited in dimension 9. Its inverse, Remove Middle Man, is the
  refactoring used to undo an over-applied instance of this rule, and both
  are covered in the refactoring family.
- **Facade pattern.** A structural cousin at a coarser grain. A Facade
  narrows a whole subsystem's surface down to a small interface for external
  callers, which is Law of Demeter's discipline applied at the level of a
  subsystem boundary rather than a single method's call graph.
- **Fluent interface and Builder.** Not incompatible in the way they first
  appear, and this entry treats getting the distinction right as one of its
  central points. Both intentionally chain calls, and neither violates the
  rule, because every intermediate call returns the same receiver or a value
  the pattern was designed to be chained on, not an unrelated collaborator's
  internal state. See dimension 4.
- **Active Record.** In active tension with a strict reading of the rule.
  Active Record objects typically expose their own associations as
  navigable, chainable properties, `order.customer.address`, precisely so
  application code can read across them, which is the opposite instinct from
  hiding the delegate. Where the rule and Active Record's ergonomics conflict,
  most Active Record-based codebases favour ergonomics for read paths and
  reserve strict Demeter discipline for write paths and cross-boundary
  service code, a judgement call this entry states as such rather than
  sourcing.

## 14. Refactoring path in and out

Introducing the discipline into code that does not have it, using Fowler's
Hide Delegate as the mechanical steps.

1. Find the chain. A call site reaching past a directly held object into a
   value returned by one of that object's own methods.
2. Confirm the case is applicable per dimension 4. Is the reach crossing a
   real behavioural boundary, or is it a plain data structure being read.
   Stop here if it is the latter.
3. On the intermediate class, write a new method that performs the reach
   internally and returns the final value, named for what it returns rather
   than for the path it takes, `shippingPostalCode()` rather than
   `getAddressThenPostalCode()`.
4. Change the original call site to call the new method instead of the
   chain. Run the tests.
5. Repeat step 4 for every other call site in the codebase that performed the
   same chain. This is usually where the value becomes visible, a chain
   repeated in six places becomes one new method and six one-line edits.
6. If the intermediate object exposed the delegate purely so callers could
   reach through it, and nothing external needs the delegate for any other
   reason, consider narrowing or removing the original accessor once every
   caller has moved to the new method, tightening the encapsulation the
   refactor was meant to achieve.

Removing the discipline when it has been over-applied, using Fowler's inverse
refactoring, Remove Middle Man.

1. Identify a class whose interface is mostly one-line forwarding
   methods with no logic of their own, the Middle Man smell from dimension
   11.
2. Confirm none of the forwarding methods are hiding a genuine future
   substitution point, for example a place where the delegate's type is
   expected to vary and callers benefit from not knowing which.
3. For each forwarding method with a small number of callers, have those
   callers obtain the delegate directly instead, and delete the forwarding
   method.
4. For forwarding methods with many callers where full removal is too large a
   change to land safely, mark the method deprecated in favour of direct
   access and remove it once callers have migrated.
5. Re-evaluate cohesion. If the intermediate class had no purpose besides
   forwarding and is now empty, delete it, per the Inline Class refactoring.

## 15. Testing and verification

Easier because of the discipline.

- A method that only ever talks to its declared collaborators can be given
  hand-written test doubles for exactly those collaborators, with no need to
  configure a chain of nested fakes whose own return values must themselves
  be correctly faked.
- A forwarding method added to satisfy the rule is trivially unit testable on
  its own, in isolation from every caller that will eventually use it.
- Contract tests against an intermediate object's new forwarding method are
  cheaper to write and cheaper to keep passing than contract tests that would
  otherwise need to assert about the shape of a nested object two levels down.

Harder because of the discipline.

- Over-mocking risk moves rather than disappears. A test that stubs a
  forwarding method to return a canned value can hide a real integration bug
  between the intermediate object and the object it delegates to, since the
  delegation itself is never exercised by that test.
- A forwarding method that simply passes a call through with no logic of its
  own is low value to unit test on its own merits, and teams that mandate one
  test per public method end up writing tests that assert nothing beyond
  "the mock was called," a pattern this repository's own testing doctrine
  treats as a false positive.

Techniques that apply.

- **Mockist tests at the direct-collaborator boundary.** Because the rule
  keeps a method's collaborator list short and declared, mock or stub
  objects for exactly those collaborators are enough, and there is no
  pressure to build deep object graphs of fakes just to satisfy a chain.
- **A characterization test before Hide Delegate.** Before refactoring a
  chain into a forwarding method, a test asserting the current external
  behaviour of the calling method, written against its existing return
  value, catches an accidental behaviour change during the refactor.
- **Integration test on the forwarding method itself, not just a unit test
  with the delegate mocked.** At least one test should exercise the real
  intermediate object with its real delegate, to close the gap left by
  over-mocking noted above.
- **Static analysis as a verification layer, not the only layer.** Tools such
  as PMD's `LawOfDemeter` rule, cited in dimension 9, can flag new
  violations at review time, but every finding still needs the human
  judgement from dimension 4 applied before acting on it, since the tool
  cannot distinguish a plain-data chain from a behavioural one on its own.

## 16. Observability signals

The Law of Demeter is a design-time discipline with no runtime representation
of its own, so this dimension is largely engineering judgement about what its
absence, or its over-application, look like once code is in production,
rather than a set of metrics the pattern itself emits.

What tends to correlate with a healthy adherence to the discipline.

- Change-coupling metrics, meaning how often two files in a repository are
  edited in the same commit over time, stay low between a domain object's
  internal fields and the many unrelated call sites elsewhere in the
  codebase. A rising change-coupling number between an internal value object
  and dozens of unrelated files is the production-history signature of chains
  that were never hidden.
- Code review turnaround on changes to a well-encapsulated intermediate class
  stays fast, because a change to that class's internal shape only requires
  updating its own forwarding methods, not auditing every caller across the
  codebase.
- Static analysis findings for chain-based coupling rules trend flat or
  downward over time rather than accumulating, when teams treat new findings
  as something to fix rather than to suppress.

What signals over-application, meaning the rule applied mechanically rather
than with judgement.

- A rising count of one-line, zero-logic public methods per class, which is
  the Middle Man smell becoming visible in code metrics rather than only in
  review.
- API surface area for internal classes growing faster than the number of
  genuinely new behaviours the codebase gained, which usually means
  forwarding methods are being added faster than real capability.
- Latency regressions localized to a service boundary shortly after a
  refactor that mechanically applied per-hop delegation across that
  boundary, the failure mode described in dimension 11.

## 17. Security and privacy implications

The Law of Demeter is close to silent on security as most catalogs would
frame it, and inventing a strong claim here would be dishonest. There is one
genuine, if secondary, implication worth stating plainly, and it is
engineering judgement, not a sourced fact.

**Reduced accidental exposure of internal object graphs.** A codebase that
consistently hides delegates behind narrow, purpose-named methods is a
codebase where a serialization bug, a debug log statement, or an API response
built by accident from an internal object is less likely to leak an entire
nested object graph, because far fewer code paths hold a direct reference to
deeply nested internal state in the first place. This is not a security
control and should never be relied on as one. A team that wants to guarantee
sensitive fields never leak needs an explicit serialization allowlist or a
dedicated projection type, the flat-DTO variant from dimension 8, not an
informal coding discipline about method chains.

**No direct implication for authentication, authorization, or input
validation.** The rule constrains which objects a method may call, not what
that method is permitted to do once it has a valid reference, and it says
nothing about trust boundaries between components. A method fully compliant
with the Law of Demeter can still perform an unauthorized action on the
single direct collaborator it was handed. Confusing "this code has narrow,
well-encapsulated dependencies" with "this code is safe" is a mistake this
entry explicitly warns against.

**A privacy-relevant side effect worth naming.** When the discipline is
applied at a genuine external boundary using the flat-projection variant from
dimension 8, that projection becomes the natural, and often the only, place
to decide which fields actually need to cross the boundary at all. Building
that projection deliberately, rather than exposing whatever a chain happens
to reach, is a reasonable place to also apply data minimization for personal
data leaving a service, though the Law of Demeter itself did not ask for
that, it only created the seam where the decision becomes easy to make.

## 18. References

1. Karl J. Lieberherr and Ian M. Holland. "Formulations of the Law of
   Demeter." Technical Report NU-CCS-88-11 (Demeter-2), Northeastern
   University College of Computer Science, June 1988. Source of the first
   written statement of the rule and its origin in Ian Holland's work at
   Northeastern in late 1987.
2. Karl J. Lieberherr, Ian M. Holland, and Arthur J. Riel. "Object-Oriented
   Programming. An Objective Sense of Style." ACM SIGPLAN Notices, OOPSLA '88
   proceedings, 1988. https://dl.acm.org/doi/10.1145/62084.62113 Verified
   2026-08-02. The paper that brought the guideline to a wide OOPSLA
   audience.
3. Northeastern University Demeter Project. "The Law of Demeter, General
   Formulation."
   https://www2.ccs.neu.edu/research/demeter/demeter-method/LawOfDemeter/general-formulation.html
   Verified 2026-08-02. Source for the exact wording of both the general
   formulation and the object-oriented friend list in dimension 5.
4. Wikipedia contributors. "Law of Demeter."
   https://en.wikipedia.org/wiki/Law_of_Demeter Verified 2026-08-02. Used to
   confirm the origin date, the Demeter Project naming, and the standard
   criticisms restated in dimension 3 and dimension 10.
5. Wikipedia contributors. "Fluent interface."
   https://en.wikipedia.org/wiki/Fluent_interface Verified 2026-08-02. Source
   for the 2005 Evans and Fowler coinage cited in dimension 4.
6. Martin Fowler. *Refactoring. Improving the Design of Existing Code*, 2nd
   edition. Addison-Wesley, 2018. ISBN 978-0-13-475759-9. Catalog entries
   "Hide Delegate" and "Remove Middle Man." Source for the refactoring steps
   in dimension 14 and the production use in dimension 9.
7. Andrew Hunt and David Thomas. *The Pragmatic Programmer*, 2nd edition.
   Addison-Wesley, 2019. ISBN 978-0-13-595705-9. Source for the Tell, Don't
   Ask companion discipline referenced in dimension 8.
8. PMD project. "PMD 6.19.0 released."
   https://pmd.github.io/2019/10/31/PMD-6.19.0/ Verified 2026-08-02. Source
   for the `LawOfDemeter` static analysis rule and its builder exception
   cited in dimension 9.
9. Ruby on Rails API documentation. `Module#delegate`.
   https://api.rubyonrails.org/classes/Module.html#method-i-delegate
   Verified 2026-08-02. Source for the delegation-generator production use in
   dimension 9. The connection to the Law of Demeter by name is this entry's
   own analysis, not a claim made by the cited documentation.

## Code examples

Three languages chosen for how differently the discipline shows up in each.
Java demonstrates the classical object-oriented shape the rule was written
for, including the forwarding method from Hide Delegate. TypeScript shows the
same violation and fix, plus the dimension-4 carve-out for a plain data type,
side by side in one language so the contrast is explicit. Python shows the
same distinction using a dataclass for the exempt case, matching the
non-applicability list in dimension 4.

### Java

```java
final class PostalCode {
    private final String value;
    PostalCode(String value) { this.value = value; }
    String value() { return value; }
}

final class Address {
    private final PostalCode postalCode;
    Address(PostalCode postalCode) { this.postalCode = postalCode; }
    PostalCode postalCode() { return postalCode; }
}

final class Customer {
    private final Address address;
    Customer(Address address) { this.address = address; }

    // Hide Delegate: callers no longer need Address at all. See dimension 14.
    PostalCode shippingPostalCode() {
        return address.postalCode();
    }
}

final class ShippingRules {
    String costFor(PostalCode code) {
        return code.value().startsWith("9") ? "express" : "standard";
    }
}

public final class Demo {
    public static void main(String[] args) {
        Customer customer = new Customer(new Address(new PostalCode("94107")));
        ShippingRules rules = new ShippingRules();

        // Compliant: ship() only talks to its parameters, per dimension 5.
        System.out.println(ship(customer, rules));
    }

    static String ship(Customer customer, ShippingRules rules) {
        return rules.costFor(customer.shippingPostalCode());
    }
}
```

### TypeScript

```typescript
// Behavioural side: the discipline applies here.
class PostalCode {
  constructor(private readonly raw: string) {}
  value(): string {
    return this.raw;
  }
}

class Address {
  private readonly _postalCode: PostalCode;
  constructor(postalCode: PostalCode) {
    this._postalCode = postalCode;
  }
  postalCode(): PostalCode {
    return this._postalCode;
  }
}

class Customer {
  constructor(private readonly address: Address) {}

  // Hide Delegate: the caller never needs to know Customer has an Address.
  shippingPostalCode(): PostalCode {
    return this.address.postalCode();
  }
}

function shippingCost(customer: Customer): string {
  const code = customer.shippingPostalCode(); // one hop, a direct friend
  return code.value().startsWith("9") ? "express" : "standard";
}

// A VIOLATING version, kept only for contrast, never call this shape.
function shippingCostViolating(customer: Customer): string {
  // @ts-expect-error - address() is intentionally not exposed on Customer
  const code = customer.address().postalCode(); // reaches past a friend
  return code.value().startsWith("9") ? "express" : "standard";
}

// Plain data, dimension 4 non-applicability: no forwarding method needed.
interface OrderSummary {
  customer: { name: string; address: { city: string; postalCode: string } };
}

function summaryLine(order: OrderSummary): string {
  // Reading nested fields on inert data is not a Law of Demeter violation.
  return `${order.customer.name}, ${order.customer.address.city}`;
}

const customer = new Customer(new Address(new PostalCode("94107")));
console.log(shippingCost(customer));
console.log(
  summaryLine({ customer: { name: "A. Person", address: { city: "SF", postalCode: "94107" } } }),
);
```

### Python

```python
from dataclasses import dataclass


class PostalCode:
    def __init__(self, raw: str) -> None:
        self._raw = raw

    def value(self) -> str:
        return self._raw


class Address:
    def __init__(self, postal_code: PostalCode) -> None:
        self._postal_code = postal_code

    def postal_code(self) -> PostalCode:
        return self._postal_code


class Customer:
    def __init__(self, address: Address) -> None:
        self._address = address

    # Hide Delegate: callers ask Customer directly, never touch Address.
    def shipping_postal_code(self) -> PostalCode:
        return self._address.postal_code()


def shipping_cost(customer: Customer) -> str:
    code = customer.shipping_postal_code()  # one hop, a direct friend
    return "express" if code.value().startswith("9") else "standard"


# Plain data, dimension 4 non-applicability: a dataclass has no
# behaviour to hide, so nested field access is not a violation.
@dataclass
class OrderSummary:
    customer_name: str
    customer_city: str


def summary_line(order: OrderSummary) -> str:
    return f"{order.customer_name}, {order.customer_city}"


if __name__ == "__main__":
    customer = Customer(Address(PostalCode("94107")))
    print(shipping_cost(customer))
    print(summary_line(OrderSummary("A. Person", "SF")))
```
