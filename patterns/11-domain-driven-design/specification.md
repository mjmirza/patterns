---
name: Specification
slug: specification
family: 11-domain-driven-design
category: Domain-Driven Design
aliases: [Specification Pattern, Query Object composed with predicates, Business Rule Object]
first_described: "Evans and Fowler 2002 (Specifications paper), Evans 2004"
maturity: canonical
related: [entity, value-object, repository, domain-service, factory, ubiquitous-language]
incompatible_with: []
verified: 2026-08-02
---

# Specification

## 1. Name, aliases, and lineage

The canonical name is Specification. It was described jointly by Eric Evans and
Martin Fowler in a short paper titled "Specifications", circulated in 2002 and
still hosted at Fowler's site
(<https://martinfowler.com/apsupp/spec.pdf>, verified 2026-08-02). The pattern
was folded into Evans' book as a named building block of tactical design, Eric
Evans, *Domain-Driven Design. Tackling Complexity in the Heart of Software*,
Addison-Wesley, 2004, page 224, in the chapter on making implicit concepts
explicit. Wikipedia's summary of the pattern corroborates both the joint
authorship and the book placement
(<https://en.wikipedia.org/wiki/Specification_pattern>, verified 2026-08-02).

The paper's own framing, paraphrased rather than quoted because the source PDF
did not resolve to extractable text during this review and is cited here by
title and venue only, is that a Specification states a business rule as a
predicate over a candidate object, gives that predicate a name drawn from the
domain, and makes the predicate combinable with other predicates using boolean
operators. Fowler's own site groups the paper under "Additional papers and
supplements", meaning it is treated as a companion contribution rather than
part of the core Patterns of Enterprise Application Architecture catalog, which
is why some catalogs list Specification as a DDD building block and others list
it as a general object oriented design idiom.

No serious source disputes the name. The pattern is occasionally called a
Business Rule Object, describing the same intent from the rules engine angle,
and a Query Object composed with predicates, describing it from the
persistence angle. Both are descriptive labels rather than competing proper
names, and this entry treats Specification as canonical because that is the
name Evans and Fowler gave it and the name every mainstream implementation
uses in its type or interface name, including Spring Data JPA's
`Specification<T>` interface
(<https://docs.spring.io/spring-data/jpa/reference/jpa/specifications.html>,
verified 2026-08-02) and the .NET `Ardalis.Specification` library
(<https://github.com/ardalis/Specification>, verified 2026-08-02).

## 2. Problem and context

A domain accumulates rules that decide whether an object qualifies for
something. A customer qualifies for free shipping. An order is eligible for
same day fulfillment. A candidate is eligible to interview for a role. Each of
these is a small piece of business knowledge, and each has three separate jobs
pulling at it from different directions, validating a single in memory object,
selecting a set of matching objects from a large collection or a database, and
building a new object that must satisfy the rule by construction.

Left unnamed, this rule tends to end up in one of three unhealthy shapes. It
gets buried as an `if` statement inside an application service method, where it
is invisible to anyone who is not reading that exact method and where it
duplicates silently the moment a second workflow needs the same check. It gets
buried inside a repository as a hand built query method, `findEligibleFor
SameDayShipping`, where the rule is now expressed twice, once as SQL or ORM
criteria and once, implicitly, wherever the equivalent in memory validation is
re derived by a different author who did not know the query existed. Or it gets
buried as a boolean method on the entity itself, `isEligibleForSameDayShipping
()`, which is fine while the rule is simple and entity local, and stops being
fine the moment the rule needs data the entity does not own, such as the
current inventory level of a warehouse it has never heard of, or the moment the
same rule needs to run as a database predicate for a report of ten thousand
rows rather than a boolean check on one loaded object.

The Specification pattern exists to give this recurring rule a home. It is a
value object, per the value object pattern, whose entire responsibility is
answering one question, does this candidate satisfy the rule, and,
secondarily, offering itself as a description of the rule that a repository or
query layer can translate into a native filter. The context in which the
pattern earns its keep is domain driven design specifically, because the
pattern's value is proportional to how many places the same rule needs to be
evaluated and how much the rule matters as a piece of ubiquitous language the
business actually uses. A rule nobody outside engineering cares about, and
that is checked in exactly one place, does not need a Specification. A rule
with a business name, evaluated both in memory and as a database filter, and
that recurs across two or more use cases, is exactly the situation the pattern
targets.

## 3. Forces

Judgement. The weighting below reflects engineering experience applying the
pattern rather than a cited source, because the relative importance of these
forces is a design call, not a fact about the pattern.

Testability against reuse. A Specification isolated as its own class is
trivially unit tested with no database and no framework, which pulls hard
toward extracting it. Pulling the other way, every extraction is a new file
and a new name to maintain, so a rule that is genuinely used once, in one
place, does not earn the overhead.

In memory correctness against database performance. The pattern's most
attractive promise, write the rule once and run it both in memory and as a
query, is also its sharpest failure mode when abandoned halfway. A
Specification whose `isSatisfiedBy` is trustworthy but whose ORM translation is
approximate produces a system that behaves correctly for objects already
loaded and incorrectly for objects filtered at the database boundary, which is
a silent correctness bug rather than a loud one.

Composability against readability. Boolean combinators, and, or, not, let
complex eligibility rules be built from small named parts, which is a real win
for expressing rules the way a domain expert would describe them, rule A and
not rule B. The same combinators, nested three or four deep, produce a tree of
anonymous composite objects that is harder to step through in a debugger than
the single conditional it replaced, which is a genuine cost for a team whose
members are not fluent in the pattern.

Coupling to persistence technology. A Specification that only ever evaluates
against an in memory candidate is persistence agnostic and portable. The
moment a Specification is asked to also produce a SQL predicate, an ORM
criteria object, or an OData filter string, the abstraction now has to know
about the target technology, which either couples the domain layer to
infrastructure or forces a translation layer, dimension 8 covers both shapes.

Team topology and cognitive load. In a small team where everyone knows the
handful of eligibility rules by heart, naming and extracting them can feel
like ceremony. In a larger team, or a domain with regulatory rules that change
on a schedule independent of the rest of the code, giving each rule a name, a
file, and a test is exactly the kind of explicit modeling that keeps the rule
from drifting out of sync with what the business actually intends, because
Evans' own argument for the pattern, made implicit concepts explicit, page
224, is precisely a cognitive load argument, not a performance argument.

## 4. Applicability and non-applicability

When to reach for it.

- The same eligibility, selection, or validation rule needs to run in more
  than one place, for example as an in memory check and as a query filter,
  and today those two places can silently drift apart.
- The rule has a name a domain expert already uses in conversation, gold
  tier, overdue, past the cooling off period, and expressing that name as a
  type makes the ubiquitous language visible in code, which is the pattern's
  own stated purpose in Evans, page 224.
- Complex eligibility needs to be built from smaller named rules combined
  with boolean logic, and the combination itself changes over time or per
  configuration, for example a discount engine that composes region rules
  with loyalty tier rules with seasonal rules.
- A collection needs to be filtered by a caller supplied criterion that is
  not known in advance, so a fixed set of repository query methods cannot
  enumerate every combination, which is the exact justification Spring Data
  JPA's own documentation gives for its `Specification<T>` interface
  (<https://docs.spring.io/spring-data/jpa/reference/jpa/specifications.html>,
  verified 2026-08-02).
- The rule needs to double as a factory precondition, that is, an object must
  be constructed only when it already satisfies the rule, which the original
  Evans and Fowler paper names as one of the three canonical uses alongside
  validation and selection.

When not to.

- The rule is checked in exactly one place and is unlikely to be reused. A
  single `if` statement or a single boolean method on the entity communicates
  the same intent with less indirection, and extracting a class here is
  ceremony without payoff, judgement.
- The rule is fundamentally a database side aggregation or a report, sum,
  count, group by, rank, rather than a per object predicate. Specifications
  answer "does this one candidate qualify", not "compute this summary over
  the set", and forcing an aggregation through a predicate shaped abstraction
  produces awkward code that fights the pattern, judgement.
- The rule requires side effects, sending a notification, writing an audit
  log, as part of evaluating it. A Specification is a pure predicate by
  contract, `isSatisfiedBy` returning a boolean with no observable effect,
  and a rule that must do work belongs in a domain service, per the domain
  service pattern, not a Specification.
- The team has no ORM or query layer that can consume a composed predicate
  object, and building a full expression to SQL translator solely to support
  the pattern costs more than the direct query code it would replace,
  judgement grounded in the coupling force above.
- The rule is unlikely to ever change independently and is core to a single
  entity's own invariants, for example an order must have at least one line
  item. That invariant belongs inside the Entity's constructor or a guard
  clause, per the entity pattern, because it is not an external eligibility
  rule, it is the object's own definition of validity.

## 5. Structure

Specification. An interface or abstract type with a single evaluation method,
conventionally named `isSatisfiedBy(candidate)`, that returns a boolean and
has no side effects. This is the sole required member of the pattern.

Concrete Specification. A class implementing the Specification interface for
one named business rule, carrying whatever parameters the rule needs as
constructor arguments, and nothing else. It is a value object per the value
object pattern, immutable and compared by its parameters rather than by
identity.

Composite Specification. A concrete Specification that wraps one or two other
Specifications and implements `isSatisfiedBy` by combining their results with
a boolean operator, and, or, or not. This is what makes Specifications
composable rather than merely named predicates.

Candidate. The object the Specification evaluates, typically an Entity or a
Value Object from the same bounded context. The Specification does not mutate
the candidate.

Repository, or query translator. An optional collaborator that accepts a
Specification and either filters an in memory collection by calling
`isSatisfiedBy` on each element, or translates the Specification into a
native query predicate, SQL, a criteria object, or an equivalent, so the same
rule can run at the database boundary rather than after loading every row.
Dimension 8 details the two shapes this collaborator takes.

Client. The application service, domain service, or factory that constructs
a Specification, optionally composes it with others, and hands it either to
a candidate directly or to a repository.

## 6. ASCII structure diagram

```
+----------------------+
|     Specification     |<---------------------------+
|  <<interface>>        |                             |
|  + isSatisfiedBy(c)   |                             |
+-----------+-----------+                             |
            ^                                          |
   +--------+--------+-----------------+               |
   |                 |                 |               |
+--+---------+  +----+--------+  +-----+------+        |
| GoldTier   |  | OverdueSpec |  | AndSpec    |--------+
| Customer   |  |             |  | (left,     |  wraps two
| Spec       |  |             |  |  right)    |  Specifications
+------------+  +-------------+  +------------+

                +----------------+
                |   Repository   |
                | findAll(spec)  |----> translates spec into
                +--------+-------+      a query predicate,
                         |               dimension 8
                         v
                +----------------+
                |   Candidate    |  (Entity or Value Object)
                +----------------+
```

## 7. Dynamics

Two runtime flows matter, and they diverge at the point where the
Specification is either applied directly to an already loaded object, or
handed to a repository for translation into a query.

```
In-memory evaluation, single candidate

Client            Specification         Candidate
  |                    |                    |
  |-- isSatisfiedBy -->|                    |
  |                    |-- read fields ---->|
  |                    |<-- values ---------|
  |<-- boolean --------|                    |
  |                    |                    |
```

```
Composed evaluation, two rules combined with AND

Client       AndSpecification    LeftSpec       RightSpec
  |                |                |               |
  |--isSatisfiedBy>|                |               |
  |                |--isSatisfiedBy>|               |
  |                |<-- false ------|               |
  |                | (short circuit, right           |
  |                |  never evaluated)                |
  |<-- false ------|                |               |
  |                |                |               |
```

```
Repository-side translation, collection filtering

Client         Repository        SpecToQueryVisitor    Database
  |                |                     |                 |
  |--findAll(spec)>|                     |                 |
  |                |--translate(spec)--->|                 |
  |                |<--WHERE clause -----|                 |
  |                |--execute query------------------------>|
  |                |<--matching rows ------------------------|
  |<--candidates --|                     |                 |
  |                |                     |                 |
```

The short circuit behaviour shown in the composed evaluation diagram is a
deliberate implementation choice, not a requirement of the pattern itself. It
matters in practice because a right hand Specification that performs an
expensive lookup, a second database round trip inside `isSatisfiedBy`, should
not run when the left hand Specification already failed, and most production
implementations, including Ardalis.Specification's expression based
composition, rely on the host language's native boolean short circuiting by
compiling to an expression tree rather than by manually invoking each side.

## 8. Implementation variants

Pure predicate, no translation. The simplest and oldest form. The
Specification exposes only `isSatisfiedBy(candidate)`, implemented as ordinary
code, field comparisons, arithmetic, calls to other Specifications. It works
against any in memory collection via a filter or a stream, and it has no
opinion about persistence. This is the shape the original Evans and Fowler
paper describes, and it is the correct default when the rule never needs to
run as a database query.

Expression tree Specification, for LINQ style hosts. In languages with a
first class expression type, C# `Expression<Func<T,bool>>` being the
canonical example, a Specification stores a lambda expression tree rather
than compiled code. The same expression can then either be compiled to a
delegate and evaluated in memory, or handed unmodified to an ORM's query
provider, Entity Framework Core or NHibernate, which walks the tree and emits
SQL. This is the shape Ardalis.Specification builds on
(<https://github.com/ardalis/Specification>, verified 2026-08-02), and it
solves the dual evaluation problem from dimension 3 by construction, because
there is only one representation of the rule, not two.

Visitor translated Specification, for typed criteria APIs. In languages
without portable expression trees, Java being the canonical example, a
Specification is a functional interface that receives the query builder's
own context objects and returns a native predicate built from them. Spring
Data JPA's `Specification<T>` interface takes exactly this shape, its single
method is `toPredicate(Root<T> root, CriteriaQuery<?> query, CriteriaBuilder
builder)`, returning a JPA `Predicate`
(<https://docs.spring.io/spring-data/jpa/reference/jpa/specifications.html>,
verified 2026-08-02). Here the Specification is not persistence agnostic, it
is written against the Criteria API directly, which trades the in memory and
database duality of the expression tree variant for simplicity, at the cost
of coupling the Specification class to JPA.

Composite with explicit AND, OR, NOT wrapper types. Regardless of which of
the above two shapes a codebase uses for leaf Specifications, composition is
almost always implemented as a small family of composite types,
`AndSpecification`, `OrSpecification`, `NotSpecification`, each holding one
or two child Specifications and implementing the same interface by
delegating to them. Ardalis.Specification, Spring Data JPA's `Specification`
via its default `and` and `or` methods, and hand rolled implementations in
every language surveyed all converge on this shape, because it is the direct
application of the Composite pattern to Specification, and the two patterns
are explicitly meant to be combined, see dimension 13.

Closure based Specification, for functional leaning languages. In
TypeScript, Python, and similarly flexible languages, a Specification can be
represented as a plain function of type `Candidate -> boolean` rather than an
object implementing an interface, with combinators implemented as higher
order functions that take one or two predicate functions and return a new
one. This drops the ceremony of a class hierarchy for the pure predicate
variant while keeping the same composability, at the cost of losing a place
to attach a human readable name or a query translation method, unless the
function is wrapped in a small named object anyway, which most production
codebases end up doing once a Specification needs to describe itself for
logging or for a UI filter builder.

## 9. Known production uses

Spring Data JPA, `Specification<T>` interface. Ships as a core part of the
Spring Data JPA module, letting repository callers pass composable predicate
objects into `findAll(Specification<T> spec)` rather than declaring a new
repository method for every combination of filters, described in the
official reference documentation
(<https://docs.spring.io/spring-data/jpa/reference/jpa/specifications.html>,
verified 2026-08-02). Spring Data JPA is one of the most widely deployed Java
persistence layers, part of the broader Spring family of projects.

Ardalis.Specification, used in Microsoft's eShopOnWeb reference application
and the Clean Architecture solution template. A .NET library that formalises
the Specification pattern for Entity Framework Core, with a GitHub reported
2.3k stars at time of verification, explicitly built to eliminate repeated
`Where`, `Include`, and `Select` query logic scattered across an application
by consolidating it into named, reusable Specification classes
(<https://github.com/ardalis/Specification>, verified 2026-08-02). Its
author, Steve Smith, also authored the Microsoft eShopOnWeb reference
architecture that the library ships inside of, which the repository's own
README states directly.

Doctrine's community Specification bundles for PHP, Happyr Doctrine
Specification. Referenced by Wikipedia's Specification pattern article as a
PHP implementation targeting Doctrine ORM, letting business rules be
recombined and translated into Doctrine query builder criteria
(<https://en.wikipedia.org/wiki/Specification_pattern>, verified 2026-08-02),
mirroring the same repository side translation role that Spring Data JPA and
Ardalis.Specification fill in their own platforms.

Eric Evans, Domain-Driven Design, itself, as a described pattern rather than
a shipped library. The pattern's inclusion as a named building block in
Evans' book, page 224 in the chapter on making implicit concepts explicit
(Evans, *Domain-Driven Design*, Addison-Wesley, 2004), is why every
mainstream DDD oriented tactical pattern catalog, and every ORM extension
named above, treats Specification as a standard tool rather than a one off
convenience, even where the concrete implementations diverge in shape as
described in dimension 8.

## 10. Consequences

Positive.

- The eligibility rule is named once, in the language the business already
  uses, which is the explicit goal Evans states for making implicit concepts
  explicit, and that name shows up in code review, in logs, and in test names
  rather than being reconstructed from an anonymous conditional every time.
- The same rule, evaluated as a Specification, does not silently drift
  between its in memory form and its query form the way two independently
  maintained `if` blocks and `WHERE` clauses tend to, provided the
  implementation is one of the expression tree or visitor translated
  variants from dimension 8 rather than two parallel hand written copies.
- Complex eligibility can be assembled from small, independently testable
  rules using boolean combinators, which turns what would otherwise be one
  large conditional into several short, named, unit tested classes or
  functions.
- Specifications are natural inputs to configuration driven or user driven
  filtering, letting an application expose build your own filter behaviour,
  a saved search, an ad hoc report, without hard coding every combination as
  a separate repository method.

Negative.

- A composed tree of Specifications, three or four levels of AND, OR, and
  NOT, is harder to read in a debugger and harder to reason about at a
  glance than the single conditional it replaced, because the logic is now
  spread across several small objects connected by composition rather than
  laid out linearly, judgement.
- The expression tree and visitor translated variants couple the domain
  layer to a specific persistence technology, C# expression trees to a LINQ
  provider, or JPA Criteria types directly, which works against the usual
  DDD goal of keeping the domain model persistence ignorant, unless the
  coupling is deliberately isolated behind an anti corruption boundary.
- A pure predicate Specification that is never wired into the query layer
  gives a false sense of dual evaluation, teams sometimes assume it is a
  Specification so it must run efficiently at the database, when in fact
  every candidate is still being loaded and checked in memory, which
  silently reintroduces the N plus one and full table scan problems the
  pattern is often adopted to avoid, judgement.
- Extra indirection and extra files for rules that are genuinely single use
  adds cognitive overhead without a corresponding reuse benefit, which is
  exactly the non applicability case in dimension 4.

## 11. Failure modes and misuse

Judgement, drawn from patterns observed in production ORM integrated
codebases rather than from a single cited source.

Two implementations, one truth. Symptom. A filter that behaves correctly in
unit tests, which construct in memory candidates and call `isSatisfiedBy`
directly, but returns wrong or incomplete results once wired into the
repository's `findAll`. Cause. The Specification has two independent
implementations of the same rule, one hand written `isSatisfiedBy` method for
in memory use and one hand written SQL or criteria fragment for the query
path, and the two were not kept in sync when the rule changed. Fix. Migrate
to an expression tree or visitor translated variant, dimension 8, so there is
exactly one representation of the rule, and add an integration test that runs
the same Specification instance against both an in memory list and the real
repository, asserting identical results, which converts the drift risk into a
test failure rather than a silent bug.

Composed queries that overwhelm the planner. Symptom. A query built from a
deeply composed Specification runs orders of magnitude slower than the
equivalent hand written SQL, or the database query planner produces a poor
execution plan for it. Cause. The composite tree translates into a deeply
nested `WHERE` clause with redundant subqueries or joins the ORM cannot
flatten, especially when Specifications capturing unrelated concerns are
combined with AND across multiple joined tables. Fix. Inspect the generated
SQL for the composed Specification under realistic data volume before
shipping it, and, where the planner struggles, either simplify the
composition, add the missing index the composed predicate actually needs, or
fall back to a hand written query for that specific report shaped case, which
dimension 4's non applicability list already flags as outside the pattern's
sweet spot.

Stale business rule behind a live sounding name. Symptom. A Specification
named after a business concept, `isEligibleForDiscount`, silently stops
matching the business's actual current definition of eligibility after a
policy change, while the code still compiles and every existing test still
passes. Cause. The rule was hard coded as literal comparisons at the time it
was written, and nobody updated the Specification when the business rule
changed, because nothing forced a review, the Specification looks the same
as any other passing test to a code reviewer who does not already know the
current policy. Fix. Treat a change to a named Specification's business
meaning as a domain event worth its own changelog entry and its own reviewer
sign off from whoever owns that policy, not merely a code diff, and keep the
test names phrased as the business rule, gold tier customers get free
shipping over fifty euros, so a stale test reads as obviously wrong to a
non engineer reviewer, not just to the author.

Duplicate rules with silently different thresholds. Symptom. Two
Specifications that look identical in a code review, same class shape, same
constructor signature, quietly encode two different thresholds for what
should be one business concept, and callers pick whichever one they find
first. Cause. No single owner or single file groups the domain's named
Specifications, so a second Specification for overdue gets written from
scratch by someone who did not find the first one, using a different grace
period. Fix. Keep all Specifications for one bounded context under one
namespace or folder next to the aggregate they qualify, and require a
repository wide search for the rule's name before a new Specification with a
similar name is added, the same discipline recommended for avoiding
duplicate ubiquitous language terms generally.

## 12. Trade-off matrix

| Force | Specification | Hand-written repository query method per case | Entity-embedded boolean method | Rules engine, e.g. Drools |
|---|---|---|---|---|
| Reusability across in-memory and query paths | High, single rule reused both ways when translated per dimension 8 | Low, each repository method is a one-off, duplicated if the same filter is needed in memory | Low, tied to one entity's own data, cannot run as a query filter over a collection it is not part of | High, rules are centrally registered and reused, but the engine itself is a separate runtime dependency |
| Composability with boolean logic | High, native AND, OR, NOT combinators | Low, combining two query methods means writing a third method | Very low, combining two entity methods requires a caller-side conditional | High, most rule engines support rule composition and priority |
| Coupling to persistence technology | Medium to high, depends on variant chosen in dimension 8 | High, the method is written directly against the query language | None, pure domain code | Medium, engine has its own rule language or DSL, separate from persistence |
| Learning curve and team cognitive load | Medium, requires understanding the pattern and its combinators | Low, an ordinary repository method any developer already knows how to write | Very low, an ordinary method on a class | High, a new DSL, tooling, and often a new deployment component |
| Fit for a rule used exactly once | Poor, adds indirection with no reuse benefit, per dimension 4 | Good, direct and simple | Good, if the rule is genuinely entity-local | Poor, massive overkill for a single rule |
| Fit for user-configurable or ad hoc filters | Good, Specifications compose naturally into a filter builder | Poor, cannot enumerate every combination in advance | Poor, same limitation | Good, this is the rules engine's core use case |

## 13. Related and incompatible patterns

Composite. Every mainstream Specification implementation surveyed in
dimension 9 relies on the Composite pattern to build AND, OR, and NOT wrapper
types over child Specifications, treating a composed Specification and a
leaf Specification identically through the same interface. Specification is
best understood as a domain flavoured, boolean combining application of
Composite, not as an unrelated idea that happens to share a UML shape.

Value Object. A concrete Specification is itself a value object, per the
value object pattern, immutable, defined by its parameters rather than an
identity, and safely shareable and cacheable. Two Specification instances
constructed with the same parameters should be treated as interchangeable.

Repository. The repository pattern's `findAll` or `findMatching` style method
is the most common integration point for Specifications, accepting one as an
argument and either filtering in memory or translating it into a native
query, as covered in dimension 8 and demonstrated by Spring Data JPA's own
`Specification<T>` parameter.

Factory. Evans' original description names factory precondition checking as
one of the three canonical uses of a Specification, a Factory can ask a
Specification whether the object it is about to build already satisfies the
rule the factory exists to enforce, rejecting construction rather than
producing an invalid object, which composes cleanly with the factory
pattern's own responsibility for guarding invariants at creation time.

Domain Service. Where evaluating a rule requires an operation with side
effects, or coordination across more than one aggregate that cannot be
reduced to a pure predicate over a single candidate, the correct pattern is a
domain service, not a Specification stretched past its pure predicate
contract. The two are complementary, a domain service may use a
Specification internally as one of its pure decision steps.

Strategy. Both patterns wrap a piece of behaviour in an object so it can be
swapped or composed. They diverge in intent, Strategy typically wraps an
algorithm choice with no expectation of boolean composition, while
Specification specifically models a business predicate meant to be combined
with AND, OR, and NOT and, ideally, translated into a query. A Specification
can be implemented using the Strategy pattern's mechanics, but not every
Strategy is a Specification.

Interpreter. A composed Specification tree, at runtime, is structurally an
abstract syntax tree of boolean expressions, and evaluating `isSatisfiedBy`
on the root walks the tree exactly the way the Interpreter pattern's
`interpret` method does. Specification can be read as a narrow, domain
specific application of Interpreter, restricted to boolean predicates over
one candidate rather than a general expression language, judgement.

No pattern in this catalog is fundamentally incompatible with Specification.
The closest tension is with hand rolled query methods, dimension 12, which
solve the same narrow problem more simply for a fixed, small set of filters
and should not be replaced by Specifications wholesale once that set of
filters is genuinely stable and small.

## 14. Refactoring path in and out

Introducing a Specification into code that does not have one.

1. Find the duplicated or scattered conditional. Search the codebase for the
   business concept by name, overdue, eligible, gold tier, across
   application services, repository query methods, and entity boolean
   methods, and list every place the same underlying rule is expressed.
2. Extract the first occurrence into a small class or function implementing
   a single `isSatisfiedBy(candidate)` method, keeping the exact same logic,
   no behaviour change, which is the same discipline as Martin Fowler's
   Extract Class refactoring applied to a predicate rather than a whole
   responsibility.
3. Replace the original conditional's call site with a call to the new
   Specification's `isSatisfiedBy`, and run the existing test suite
   unchanged to confirm no behaviour shifted.
4. Replace the remaining duplicated occurrences found in step 1 with the
   same Specification instance or type, deleting the duplicated logic rather
   than leaving it as dead code, per the failure mode in dimension 11 that
   warns against a parallel implementation.
5. If the rule also needs to run as a database filter, add the query
   translation, dimension 8, as a second, explicitly tested capability of
   the same Specification, and add the dual evaluation integration test
   described in dimension 11's first failure mode before removing any hand
   written query method it replaces.
6. Only introduce AND, OR, NOT composite wrapper types once a second rule
   actually needs to be combined with the first, following the general
   refactoring discipline of building the abstraction the moment a second
   real use case demands it, not before, judgement grounded in the
   applicability guidance in dimension 4.

Removing a Specification that has stopped earning its place.

1. Confirm the Specification is used in exactly one place today, by the same
   codebase search used in step 1 above, and confirm no other rule is
   currently composed with it via AND, OR, or NOT.
2. Inline its `isSatisfiedBy` body back into the single call site as an
   ordinary conditional or a private helper method, preserving the exact
   logic, then delete the Specification class or function.
3. If the Specification had a repository side query translation, per
   dimension 8, inline that translation into the repository method that
   used it, or, if the query itself is no longer needed, delete it.
4. Re run the full test suite for the affected module to confirm behaviour
   is unchanged, since this refactor is a pure simplification and must not
   alter observable results.

## 15. Testing and verification

A Specification's pure predicate contract, no side effects, one boolean
result, makes it one of the easiest domain constructs to unit test, and this
is one of the pattern's genuine, non judgement based wins, no database, no
mocked repository, and no test double beyond a plain in memory candidate
object are required to exercise the rule.

- Test each concrete Specification directly against hand built in memory
  candidates, covering the boundary of the rule explicitly, a candidate that
  exactly meets the threshold, one just below it, and one just above it,
  rather than only an obviously true and an obviously false example.
- Test composite Specifications, AND, OR, NOT, with candidates chosen to
  exercise every branch of the boolean table, not only the case where all
  children agree, since a composition bug most often shows up in the case
  where children disagree, one true and one false into an AND.
- Where a Specification also translates into a query, per dimension 8, add
  an integration test that persists a small, deliberately mixed fixture
  set, some rows that satisfy the rule and some that do not, then asserts
  that `repository.findAll(spec)` returns exactly the matching rows and
  that `isSatisfiedBy` agrees with the persisted result for every fixture
  row, which is the direct test for the dual evaluation drift failure mode
  in dimension 11.
- Name tests using the domain language the Specification itself is named
  after, a customer with three or more orders in the last ninety days is
  gold tier, so a failing test reads as a business rule regression to a
  reviewer who is not fluent in the implementation, rather than as an
  implementation detail failing.
- For property based test frameworks, a natural property to check is that
  `spec.and(other).isSatisfiedBy(candidate)` equals `spec.isSatisfiedBy(
  candidate) && other.isSatisfiedBy(candidate)` for a generated range of
  candidates and Specification pairs, which directly verifies the composite
  layer's boolean algebra rather than any single business rule.

## 16. Observability signals

Judgement, this dimension is practice derived rather than sourced.

- When a Specification is used to gate an expensive or user visible
  decision, log which named Specification, or which composed expression of
  named Specifications, produced a rejection, including the candidate's
  identifying key, so a support engineer can answer why an order was not
  eligible for same day shipping without re deriving the rule from source.
- For Specifications translated into a database query, per dimension 8, log
  or trace the generated query, or at minimum its shape, on first use in a
  new environment, so a slow query alert can be traced back to the specific
  named Specification, or composed tree of Specifications, that produced
  it, rather than to an opaque, generated `WHERE` clause.
- Track how often each named Specification is evaluated and what fraction
  of candidates satisfy it, over time, as a lightweight signal that a
  business rule's real world hit rate matches what the business expects, a
  rule that suddenly starts matching everyone, or no one, after a
  deployment is a strong early indicator of the stale rule failure mode
  described in dimension 11.
- If Specifications are user composable, an ad hoc filter builder, log the
  composed expression a user actually submitted, not just the final query
  result, so that a why did my search return nothing support ticket can be
  answered by inspecting exactly which combination of named rules the user
  built, rather than by guessing.

## 17. Security and privacy implications

Judgement, analytical rather than sourced.

- A Specification exposed to end users as a self serve filter builder is,
  in effect, an interpreter over a small domain specific query language,
  and it must be scoped to only the fields and operators the domain intends
  to expose, the same discipline that applies to any interpreter or query
  builder accepting external input, otherwise a composed Specification can
  be used to probe for fields or relationships the user should not be able
  to filter on, an information disclosure risk rather than an injection
  risk in the SQL sense, since the pattern itself does not concatenate
  strings.
- Where a Specification's query translation, per dimension 8, is built by
  walking user supplied structure, an expression tree deserialized from a
  request body, or a filter DSL parsed from a query string, the translator
  must validate that structure before handing it to the ORM's criteria API,
  because an unbounded or maliciously deep composed tree, thousands of
  nested AND and OR nodes, can produce a denial of service risk in query
  planning time even though no SQL is being hand assembled.
- Specifications that embed personally identifiable data as constructor
  parameters, an exact email address or a national identifier used as an
  equality filter, should be treated the same as any other place that data
  is handled, avoided in logs per the observability guidance in dimension
  16 unless the logging path is already covered by the system's existing
  PII handling policy.
- The pattern itself introduces no new authentication or authorization
  surface, and does not, by itself, enforce that a caller is permitted to
  evaluate a given rule against a given candidate, that check remains the
  responsibility of the calling application or domain service, a
  Specification answers whether a candidate satisfies the rule, never
  whether the caller is allowed to ask.

## 18. References

1. Eric Evans and Martin Fowler, "Specifications", 2002, hosted at
   <https://martinfowler.com/apsupp/spec.pdf>, verified 2026-08-02. The
   original paper describing the pattern. Cited here by title, authorship,
   and hosting venue, the source PDF could not be reliably extracted to
   plain text during this review, so no direct quotation is drawn from it.
2. Eric Evans, *Domain-Driven Design. Tackling Complexity in the Heart of
   Software*, Addison-Wesley, 2004, page 224. The book placement of
   Specification as a named tactical pattern, in the chapter on making
   implicit concepts explicit.
3. Wikipedia, "Specification pattern",
   <https://en.wikipedia.org/wiki/Specification_pattern>, verified
   2026-08-02. Used to corroborate the pattern's origin, its book placement,
   and the list of named cross-language implementations cited in
   dimension 9.
4. Spring Data JPA reference documentation, "Specifications",
   <https://docs.spring.io/spring-data/jpa/reference/jpa/specifications.html>,
   verified 2026-08-02. Source for the `Specification<T>` interface
   signature and its `toPredicate` method, and the composability example
   using `.or()`.
5. Ardalis.Specification, GitHub repository,
   <https://github.com/ardalis/Specification>, verified 2026-08-02. Source
   for the library's purpose, its use inside Microsoft's eShopOnWeb
   reference application and Clean Architecture template, and its star
   count at time of verification.

## Code examples

Three languages are shown, TypeScript, Python, and Java. TypeScript and
Python both demonstrate the closure based, pure predicate variant from
dimension 8, since both languages make functions first class and this is the
idiomatic shape a working developer reaches for first in either language.
Java demonstrates the visitor translated variant, mirroring the real shape
used by Spring Data JPA's own `Specification<T>` interface, cited in
dimension 9, so the sample is directly comparable to a production
implementation rather than an invented toy shape. Go and Rust are omitted,
not because the pattern translates poorly to either, but because the two
variants shown already cover the pattern's two structurally distinct
implementation families, dimension 8, and a fourth or fifth sample would
repeat one of those two shapes rather than demonstrate a new one.

### TypeScript

```typescript
interface Specification<T> {
  isSatisfiedBy(candidate: T): boolean;
  and(other: Specification<T>): Specification<T>;
  or(other: Specification<T>): Specification<T>;
  not(): Specification<T>;
}

abstract class BaseSpecification<T> implements Specification<T> {
  abstract isSatisfiedBy(candidate: T): boolean;

  and(other: Specification<T>): Specification<T> {
    return new AndSpecification(this, other);
  }

  or(other: Specification<T>): Specification<T> {
    return new OrSpecification(this, other);
  }

  not(): Specification<T> {
    return new NotSpecification(this);
  }
}

class AndSpecification<T> extends BaseSpecification<T> {
  constructor(private left: Specification<T>, private right: Specification<T>) {
    super();
  }
  isSatisfiedBy(candidate: T): boolean {
    return this.left.isSatisfiedBy(candidate) && this.right.isSatisfiedBy(candidate);
  }
}

class OrSpecification<T> extends BaseSpecification<T> {
  constructor(private left: Specification<T>, private right: Specification<T>) {
    super();
  }
  isSatisfiedBy(candidate: T): boolean {
    return this.left.isSatisfiedBy(candidate) || this.right.isSatisfiedBy(candidate);
  }
}

class NotSpecification<T> extends BaseSpecification<T> {
  constructor(private wrapped: Specification<T>) {
    super();
  }
  isSatisfiedBy(candidate: T): boolean {
    return !this.wrapped.isSatisfiedBy(candidate);
  }
}

interface Customer {
  ordersLastNinetyDays: number;
  accountAgeMonths: number;
}

class GoldTierCustomerSpec extends BaseSpecification<Customer> {
  isSatisfiedBy(candidate: Customer): boolean {
    return candidate.ordersLastNinetyDays >= 3;
  }
}

class EstablishedAccountSpec extends BaseSpecification<Customer> {
  constructor(private minimumMonths: number) {
    super();
  }
  isSatisfiedBy(candidate: Customer): boolean {
    return candidate.accountAgeMonths >= this.minimumMonths;
  }
}

const goldAndEstablished = new GoldTierCustomerSpec().and(new EstablishedAccountSpec(6));

const newGoldCustomer: Customer = { ordersLastNinetyDays: 4, accountAgeMonths: 2 };
const loyalRegularCustomer: Customer = { ordersLastNinetyDays: 1, accountAgeMonths: 24 };
const loyalGoldCustomer: Customer = { ordersLastNinetyDays: 5, accountAgeMonths: 18 };

console.log(goldAndEstablished.isSatisfiedBy(newGoldCustomer));
console.log(goldAndEstablished.isSatisfiedBy(loyalRegularCustomer));
console.log(goldAndEstablished.isSatisfiedBy(loyalGoldCustomer));
```

### Python

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass


class Specification(ABC):
    @abstractmethod
    def is_satisfied_by(self, candidate) -> bool:
        raise NotImplementedError

    def and_(self, other: "Specification") -> "Specification":
        return AndSpecification(self, other)

    def or_(self, other: "Specification") -> "Specification":
        return OrSpecification(self, other)

    def not_(self) -> "Specification":
        return NotSpecification(self)


class AndSpecification(Specification):
    def __init__(self, left: Specification, right: Specification):
        self.left = left
        self.right = right

    def is_satisfied_by(self, candidate) -> bool:
        return self.left.is_satisfied_by(candidate) and self.right.is_satisfied_by(candidate)


class OrSpecification(Specification):
    def __init__(self, left: Specification, right: Specification):
        self.left = left
        self.right = right

    def is_satisfied_by(self, candidate) -> bool:
        return self.left.is_satisfied_by(candidate) or self.right.is_satisfied_by(candidate)


class NotSpecification(Specification):
    def __init__(self, wrapped: Specification):
        self.wrapped = wrapped

    def is_satisfied_by(self, candidate) -> bool:
        return not self.wrapped.is_satisfied_by(candidate)


@dataclass
class Order:
    total_amount: float
    is_perishable: bool


class LargeOrderSpec(Specification):
    def __init__(self, threshold: float):
        self.threshold = threshold

    def is_satisfied_by(self, candidate: Order) -> bool:
        return candidate.total_amount >= self.threshold


class NonPerishableSpec(Specification):
    def is_satisfied_by(self, candidate: Order) -> bool:
        return not candidate.is_perishable


eligible_for_free_shipping = LargeOrderSpec(50.0).and_(NonPerishableSpec())

orders = [
    Order(total_amount=75.0, is_perishable=False),
    Order(total_amount=75.0, is_perishable=True),
    Order(total_amount=10.0, is_perishable=False),
]

matching = [o for o in orders if eligible_for_free_shipping.is_satisfied_by(o)]
print(len(matching))
for o in matching:
    print(o)
```

### Java

This sample mirrors Spring Data JPA's real `Specification<T>` interface
shape, a method that receives query building context and returns a native
predicate, without depending on the Spring or JPA libraries themselves,
using small stand in types so the sample compiles and runs standalone while
still demonstrating the visitor translated variant from dimension 8
accurately.

```java
import java.util.ArrayList;
import java.util.List;
import java.util.function.Predicate;

interface Specification<T> {
    Predicate<T> toPredicate();

    default Specification<T> and(Specification<T> other) {
        return () -> candidate -> this.toPredicate().test(candidate) && other.toPredicate().test(candidate);
    }

    default Specification<T> or(Specification<T> other) {
        return () -> candidate -> this.toPredicate().test(candidate) || other.toPredicate().test(candidate);
    }
}

class Product {
    final String category;
    final double price;

    Product(String category, double price) {
        this.category = category;
        this.price = price;
    }

    @Override
    public String toString() {
        return category + " at " + price;
    }
}

class InCategorySpec implements Specification<Product> {
    private final String category;

    InCategorySpec(String category) {
        this.category = category;
    }

    @Override
    public Predicate<Product> toPredicate() {
        return p -> p.category.equals(category);
    }
}

class PriceUnderSpec implements Specification<Product> {
    private final double maxPrice;

    PriceUnderSpec(double maxPrice) {
        this.maxPrice = maxPrice;
    }

    @Override
    public Predicate<Product> toPredicate() {
        return p -> p.price < maxPrice;
    }
}

public class SpecificationDemo {
    public static void main(String[] args) {
        Specification<Product> affordableElectronics =
            new InCategorySpec("electronics").and(new PriceUnderSpec(100.0));

        List<Product> catalog = new ArrayList<>();
        catalog.add(new Product("electronics", 79.99));
        catalog.add(new Product("electronics", 249.99));
        catalog.add(new Product("groceries", 12.50));

        List<Product> matches = new ArrayList<>();
        for (Product p : catalog) {
            if (affordableElectronics.toPredicate().test(p)) {
                matches.add(p);
            }
        }

        System.out.println(matches.size());
        for (Product p : matches) {
            System.out.println(p);
        }
    }
}
```
