---
name: Liskov Substitution Principle
slug: liskov-substitution-principle
family: 04-principles-and-laws
category: Principles and Laws
aliases: [Substitutability Principle, Behavioral Subtyping, The L in SOLID]
first_described: "Liskov 1987, Liskov and Wing 1994"
maturity: canonical
related: [interface-segregation-principle, open-closed-principle, template-method, strategy, bridge]
incompatible_with: []
verified: 2026-08-09
---

# Liskov Substitution Principle

## 1. Name, aliases, and lineage

The canonical name is the Liskov Substitution Principle, commonly abbreviated LSP. It is
also called the substitutability principle and, more precisely in the type-theory
literature, behavioral subtyping. In Robert C. Martin's SOLID acronym it is the L. Martin
documents the acronym across his own writing, including *Agile Software Development,
Principles, Patterns, and Practices*, Prentice Hall, 2002, and this attribution is
standard in the object-oriented design literature.

The principle originates with Barbara Liskov's 1987 OOPSLA keynote address, "Data
Abstraction and Hierarchy." It was formalized seven years later, jointly with Jeannette M.
Wing, in "A Behavioral Notion of Subtyping," *ACM Transactions on Programming Languages and
Systems* (TOPLAS), Volume 16, Issue 6, November 1994, pages 1811 to 1841. The Wikipedia
summary of the principle states the core requirement plainly. "if S subtypes T, what holds
for T-objects holds for S-objects," and confirms both the 1987 keynote and the 1994 TOPLAS
paper as the lineage
([Liskov substitution principle, Wikipedia](https://en.wikipedia.org/wiki/Liskov_substitution_principle),
verified 2026-08-09). The 1994 paper is where the formal machinery lives, contravariance of
method preconditions, covariance of method postconditions, and invariant preservation
across a subtyping relation, and that formal machinery is what every engineering
restatement of LSP, including this entry's structure section, is derived from.

The name is occasionally shortened in casual conversation to "Liskov" alone ("does this
violate Liskov"), which is informal usage rather than a documented alias, and this entry
treats it as such.

## 2. Problem and context

Object-oriented languages let a caller hold a reference typed as a base class or an
interface and receive, at runtime, any one of several concrete subtypes. The entire value
of that polymorphism depends on one assumption the type system does not check. that every
concrete subtype behaves the way the caller, having been written and tested against the
base type, expects it to behave. When a team adds a new subtype that satisfies every method
signature the compiler demands but changes what the method actually does, refuses inputs
the base type accepted, returns a weaker guarantee than the base type promised, or throws a
failure the caller has no handler for, client code that has never been touched starts
misbehaving the moment the new subtype is substituted in.

This problem is most visible in exactly the codebases that are trying to do the right
thing. a team introduces an interface specifically so new implementations can be added
without touching existing call sites, per the Open and Closed Principle, and then the very
first new implementation quietly breaks every caller because nobody wrote down what the
interface actually promised beyond its method signatures. The context in which LSP applies
is any class hierarchy, interface implementation, or plugin extension point where client
code is written generically against the base type and a second implementation is expected,
now or later. Outside that context, for a closed, single-implementation type with no
polymorphic caller, there is no substitution happening and the principle has nothing to
protect.

## 3. Forces

**Flexibility versus predictability.** A hierarchy designed for maximum extensibility, few
constraints, a wide-open interface, invites subtypes that diverge in behavior, because
there is little in the contract to hold them to a shared standard. A hierarchy designed for
maximum predictability, a narrow, tightly specified interface, is easier to substitute
safely but harder to extend with behavior the original designer did not anticipate. LSP
pushes toward predictability, and this is the central force it favors.

**Documentation cost versus defect cost.** Writing down preconditions, postconditions, and
invariants for every interface method is real, ongoing engineering effort that most teams
under-invest in, because the cost is paid upfront by the interface's author and the
benefit, catching a violation before it reaches production, is paid later, often by a
different engineer entirely. LSP asks a team to pay the documentation cost specifically to
avoid the much larger, harder-to-trace defect cost of a substitution failure discovered in
production.

**Modeling the real world versus modeling behavior.** Real-world taxonomies (a square is a
rectangle, a penguin is a bird) frequently do not map onto behaviorally sound type
hierarchies, because real-world categorization and behavioral substitutability are
answering different questions. LSP sacrifices intuitive, taxonomy-driven hierarchy design
in favor of hierarchies that are behaviorally sound, even when the result looks less
natural on a whiteboard.

**Compile-time checking versus runtime discipline.** Most mainstream languages check method
signatures at compile time and cannot check preconditions, postconditions, or invariants
without an explicit Design by Contract extension (Eiffel is the significant exception).
This means LSP compliance, in the majority of production codebases, rests on test suites,
code review discipline, and documentation rather than a compiler guarantee, and that
tradeoff is a real, ongoing cost the principle imposes on teams working in languages
without contract support.

## 4. Applicability and non-applicability

### Apply LSP as an active design discipline when

- Designing a public interface, abstract base class, or plugin or extension point that
  multiple teams, or multiple future implementations, will need to satisfy.
- Client code is, or will be, written generically against a shared type without inspecting
  the concrete subtype it receives.
- The codebase already shows an `instanceof` and type-check pattern scattered through
  client code that is nominally written against a shared interface, which is a direct
  signal that substitutability has already broken down.
- Building a library or framework where downstream consumers will supply their own
  implementations of the library's interfaces, because the documented contract is, in
  effect, a promise to every future implementer.

### Non-applicability, when LSP does not apply or is a poor fit

- **Pure data transfer objects with no behavior.** A subtype that only adds fields to a
  plain struct or DTO, with no overridden methods, has no behavioral contract to violate.
  LSP concerns arise only where methods are overridden or interfaces are implemented.
- **Sealed or closed hierarchies with exhaustive pattern matching, where the client is the
  exhaustive match itself.** In languages with algebraic data types and sealed classes
  (Swift enums with associated values, Kotlin sealed classes, Rust enums), the client
  typically pattern-matches every case explicitly rather than programming against a shared
  supertype's method contract. LSP's substitutability concern is largely orthogonal to this
  style, because there is no single supertype interface being substituted through.
- **Value objects designed for structural equality only, with no inheritance.** If a
  hierarchy is flat, final classes implementing a marker interface with no shared behavior
  beyond equality and hashing, there is no substitution scenario to reason about.
- **Adapter classes whose entire purpose is to translate one contract into a different,
  incompatible one.** An adapter is explicitly not trying to be substitutable for either
  side. It exists to bridge two contracts that are not substitutable for each other, and
  evaluating it against LSP misapplies the principle to a pattern that has a different job.
- **Internal, single-implementation interfaces used only for testing or mocking, where no
  second implementation is ever expected.** LSP protects against a second implementation
  breaking client assumptions. If a codebase enforces exactly one production
  implementation, verified by architecture tests, the principle's protective value is close
  to zero, though a clear contract is still worth writing if a second implementation later
  appears.
- **Performance-critical numeric code that deliberately narrows precision or range per
  subtype for hardware reasons**, for example a `Float16Buffer` versus `Float64Buffer`
  implementing a shared `Buffer` interface where the client is explicitly written to check
  `precision()` before use. Here the client is designed around the variation, not oblivious
  to it, so the classic LSP failure mode, an unsuspecting client broken by substitution,
  does not occur, because the contract itself documents the variability as a first-class,
  queryable property.

## 5. Structure

The participants in an LSP-relevant hierarchy and their responsibilities.

- **Base type or supertype (T).** Declares the contract, explicit or implicit, that
  clients rely on. method signatures, preconditions, postconditions, invariants, and any
  documented behavioral guarantees, does it throw, does it mutate shared state, is it
  idempotent.
- **Subtype (S).** A class or type that either extends T through inheritance or implements
  an interface T declares. Responsible for honoring T's full contract, not just its method
  signatures.
- **Client.** Code written against the type T, unaware of and indifferent to which
  concrete subtype it is handed. The client's correctness is what the principle protects.
- **Contract, an implicit participant.** The set of preconditions, postconditions,
  invariants, and history constraints that define what "correct behavior" means for T.
  Often undocumented in practice, which is a primary source of LSP violations.

The formal condition governing S relative to T, established by Liskov and Wing in "A
Behavioral Notion of Subtyping" (1994). S's method preconditions may be no stronger than
T's, and S's method postconditions may be no weaker than T's. This is contravariance of
preconditions paired with covariance of postconditions, and every invariant T's contract
promises must continue to hold for every object of type S.

## 6. ASCII structure diagram

```
+-------------------------------+
|         <<interface>>         |
|           Base / T            |
+-------------------------------+
| + operation(): ReturnType     |
|   pre:  P(args)               |
|   post: Q(result, state)      |
|   invariant: I(state)         |
+-------------------------------+
              ^
              |  implements / extends
     +--------+--------+
     |                 |
+----+-----+     +-----+----+
| Subtype  |     | Subtype  |
|    S1    |     |    S2    |
+----------+     +----------+
| operation():   | operation():
|  pre:  P'<=P   |  pre:  P'<=P
|  post: Q'>=Q   |  post: Q'>=Q
|  keeps I       |  keeps I
+----------+     +----------+
```

The critical detail is the direction of the inequalities. A subtype's precondition (`P'`)
must be no stronger than the base type's precondition, `P' <= P`, meaning the subtype
accepts everything the base type accepts, possibly more. A subtype's postcondition (`Q'`)
must be no weaker than the base type's postcondition, `Q' >= Q`, meaning the subtype
guarantees everything the base type guarantees, possibly more.

## 7. Dynamics

```
Caller                Base type T (contract)      Concrete subtype (S1 or S2)
  |                          |                              |
  |--- typed reference to T ------------------------------->|
  |                          |                              |
  |--- call operation(args) via T's contract ---------------|
  |                          |  precondition check           |
  |                          |  (S honors P, may accept more)|
  |                          |------------------------------>|
  |                          |         runs S's logic        |
  |                          |<-------------------------------
  |                          |  postcondition check          |
  |                          |  (S honors Q, may promise more)|
  |<----------------- result, per T's contract ---------------|
  |
  |  Caller never branches on which concrete subtype answered.
  |  If S1 or S2 substitution changes observable behavior beyond
  |  what T's contract allows, LSP has been violated at this call.
```

At runtime, the caller issues a call through the statically or nominally typed reference to
T. The concrete object that actually executes is whichever subtype was constructed and
handed to the caller, S1 or S2 or any future S. The caller's correctness depends entirely
on both subtypes honoring the same precondition and postcondition envelope defined by T's
contract, because the caller has no branch, no `instanceof` check, and no code path that
treats S1 and S2 differently. The moment a new subtype is introduced whose precondition is
narrower or whose postcondition is weaker than what the caller was written against, this
exact call sequence produces a defect, and it typically surfaces first in production,
because most test suites are written against one concrete subtype and never re-run against
a newly added one.

## 8. Implementation variants

**Explicit contract queries, the general-purpose fix.** When a subtype genuinely differs
from its siblings in what it accepts or guarantees, expose the variation as a queryable
method every implementation must provide, rather than letting the variation be an
undocumented surprise. Section 4's rectangle-square-style variation is resolved this way in
the code examples below by expressing acceptable input range as `minRefundable()` and
`maxRefundable()` methods rather than a hardcoded assumption.

**Interface segregation, when a capability is entirely absent rather than merely
narrowed.** If a subtype cannot support an operation at all, rather than supporting a
narrower version of it, splitting the interface into a smaller capability the subtype can
honor, and a larger one it cannot, is the correct variant, because it lets the type system
prevent the invalid call from compiling rather than discovering it at runtime through a
thrown exception.

**Design by Contract, the language-enforced variant.** In Eiffel, `require` clauses express
preconditions and `ensure` clauses express postconditions, and Eiffel's inheritance rule
enforces, at compile and run time, that a redefined routine's precondition may only be
weakened and its postcondition only strengthened, which is a direct, mechanical
implementation of the LSP inequality
([Eiffel Design by Contract and Assertions](https://www.eiffel.org/doc/eiffel/Design%20by%20Contract%20and%20Assertions),
verified 2026-08-09). Languages without native contract support approximate this variant
with assertion libraries or a shared contract test suite run against every implementation,
as shown in Section 8's code examples.

**Composition over inheritance, when divergence is fundamental rather than incidental.**
When a "subtype" needs to do something meaningfully different from its siblings, not
merely a narrower or wider version of the same operation, the honest variant is to stop
modeling it as a subtype at all and use Strategy or a similar composition-based pattern
instead, letting the client explicitly select the behavior rather than being handed an
unexpected substitute.

## 9. Known production uses

**The Java Collections Framework's unmodifiable wrappers.** `java.util.Collections`
provides `unmodifiableList`, `unmodifiableSet`, and similar wrapper methods that return an
object still typed as `List`, `Set`, and so on, but which throws
`UnsupportedOperationException` on any mutating call. The official Java SE 8 `List`
interface documentation explicitly frames this as an "optional operation," stating that
`add` and `remove` may throw `UnsupportedOperationException` "if the add operation is not
supported by this list"
([java.util.List, Java SE 8 API documentation](https://docs.oracle.com/javase/8/docs/api/java/util/List.html),
verified 2026-08-09). This is a real, in-the-wild instance of the LSP tension named in
Common Mistake 1 below, a widely-used, standard-library interface whose contract itself
concedes that not every implementation can honor the full mutation contract, which the
Java community and the wider software engineering literature (including discussions by
Joshua Bloch, author of *Effective Java*, on the Collections Framework's tension with
strict interface contracts) has long cited as the canonical example of the "optional
operation" workaround rather than a clean interface split.

**Eiffel's own standard library and language runtime.** Because Eiffel enforces the LSP
inequality on preconditions and postconditions at the language level through its
`require`/`ensure`/inheritance rules, every class in Eiffel's standard library that
redefines an inherited routine is, by construction, checked against this exact rule by the
compiler and runtime assertion system, making Eiffel's own class library the most direct,
mechanically enforced production instance of LSP compliance documented in a general-purpose
language
([Eiffel Design by Contract and Assertions](https://www.eiffel.org/doc/eiffel/Design%20by%20Contract%20and%20Assertions),
verified 2026-08-09).

**Robert C. Martin's SOLID formulation, adopted across the object-oriented industry.**
LSP's status as one fifth of the SOLID acronym, documented in Martin's *Agile Software
Development, Principles, Patterns, and Practices*, is itself evidence of production
adoption at the level of engineering practice and code review standards, since SOLID is
widely taught and referenced as a checklist applied during design review at object-oriented
shops broadly, rather than as an academic curiosity confined to a single company or system.

## 10. Consequences

### Positive

- **Polymorphism becomes trustworthy.** Code written against an abstraction can be
  extended with new subtypes without re-testing every call site, because the contract, not
  the implementation, is what callers rely on.
- **The Open and Closed Principle becomes achievable in practice**, rather than merely
  aspirational, because new subtypes genuinely substitute for existing ones instead of
  quietly breaking callers.
- **Test suites transfer.** A well-designed base-type contract test suite, shown in Section
  8, can be run against every subtype, catching violations at commit time instead of in
  production.
- **Client code stays simpler.** Callers do not need `instanceof` checks or subtype-specific
  branches, which keeps client code easier to reason about and change.

### Negative

- **Requires upfront contract design.** Preconditions, postconditions, and invariants are
  rarely written down in mainstream object-oriented codebases, and LSP asks teams to think
  about and often document behavior that method signatures alone do not express, which is
  real design cost paid before any defect is prevented.
- **Can force awkward hierarchies or their abandonment.** The classic rectangle and square
  case shows that intuitive is-a relationships from the real world do not always hold
  behaviorally, and enforcing LSP sometimes means flattening a hierarchy that looked clean
  on a whiteboard into something less elegant but more correct.
- **Interacts with covariance and contravariance rules that differ across languages.** A
  design that is LSP-compliant in one language's type system, Kotlin, which supports
  declaration-site variance annotations, may need different handling in another, Java,
  which relies on use-site wildcards and does not enforce parameter contravariance for
  overriding methods, only return-type covariance.
- **No compiler can fully enforce it, outside Design by Contract languages.** Method
  signatures are checked structurally by the compiler in most mainstream languages.
  preconditions, postconditions, and invariants are behavioral and, absent Eiffel-style
  contract support, are enforced only by tests, review, and discipline.

## 11. Failure modes and misuse

**Precondition strengthening, presented as a validation improvement.** A subtype narrows
what inputs it accepts compared to the base type, often framed internally as "tightening up
validation," and every caller written against the base type's original, wider range now
receives an exception it has no handling path for. The observable symptom is an exception
type the caller never anticipated, thrown only when a specific, newer subtype is in play,
and the failure is often discovered in production rather than in tests, because the test
suite was written and passes for the original subtype.

**Postcondition weakening, presented as a performance optimization.** A subtype returns a
weaker guarantee than the base type promised, for example a caching layer that can return
data up to some staleness window old, when the base contract implied fresh reads. The
observable symptom is silently incorrect downstream behavior, a stale balance shown to a
user, a stale inventory count driving an order, that no test failure flags, because nothing
in the test suite asserts freshness explicitly.

**The optional-operation trap.** A subtype implements an interface it can only partially
support, throwing `UnsupportedOperationException` or an equivalent for the methods it
cannot honor, exactly the pattern documented in the JDK's unmodifiable collection wrappers
(Section 9). The observable symptom is a runtime crash at a call site that has never
changed, triggered purely by which concrete subtype happens to be passed in that particular
code path.

**Total-order contract violations in comparator-style interfaces.** A subtype's
`compareTo` or `equals` override violates the mathematical contract the base interface
requires, reflexivity, symmetry, transitivity, consistency with equals, while still
satisfying the method signature. The observable symptom is a sort routine that enters an
infinite loop, produces an inconsistently ordered result, or behaves correctly for small
inputs and incorrectly for larger ones, and the bug is intermittent because it depends on
the specific ordering of the input data.

**Misuse as an excuse to avoid ever changing an interface.** Some teams misapply LSP as a
blanket argument against ever narrowing or evolving an interface, treating any change to a
base contract as automatically forbidden. This misreads the principle. LSP constrains how
subtypes relate to an existing contract, it does not forbid deliberately redesigning the
contract itself, including narrowing it, when every implementation is updated together and
no orphaned caller is left relying on the old, wider contract.

## 12. Trade-off matrix

| Force | Liskov Substitution Principle (strict contracts, shared test suite) | Duck typing with no shared contract (loose, structural only) | Design by Contract language enforcement (Eiffel-style) |
|---|---|---|---|
| Defect discovery timing | At commit time, via shared contract tests | In production, when a caller hits an unanticipated case | At compile or run time, via language-level assertion checks |
| Upfront design cost | Moderate, contracts must be written and tested | Low, no explicit contract required | High, requires a contract-aware language and discipline |
| Extensibility for new subtypes | High, as long as new subtypes honor the contract | Very high, nothing enforces compliance | Moderate, new subtypes must satisfy the compiler's contract check |
| Language support required | None, works with tests and review in any language | None | Native support, essentially unique to Eiffel among mainstream languages |
| Risk of silent behavioral drift | Low, caught by the shared contract test suite | High, nothing catches it until a caller breaks | Very low, the language itself rejects a violating redefinition |

## 13. Related and incompatible patterns

- **Open and Closed Principle.** LSP is the behavioral precondition that makes OCP's
  promise, extend without modifying existing code, actually safe. OCP tells a team to add
  new subtypes instead of editing existing classes. LSP tells the team the rule new
  subtypes must follow so that adding them does not silently break code that was never
  touched.
- **Interface Segregation Principle.** ISP is frequently the structural fix for an LSP
  violation. When a base interface bundles operations that not every subtype can
  meaningfully support, splitting it into smaller, role-specific interfaces removes the
  temptation for a subtype to implement a method it cannot honor, which is the most common
  source of LSP breakage in practice.
- **Template Method.** Template Method defines an algorithm's skeleton in a base class and
  lets subclasses override specific steps. It is an especially LSP-sensitive pattern
  because the base class's template method calls the overridable steps internally. if a
  subclass's overridden step violates the base contract those internal call sites assume,
  the entire algorithm can misbehave in ways that are hard to trace back to the specific
  override.
- **Strategy.** Strategy is often the LSP-safe alternative to subclassing when behavior
  genuinely varies per case. Instead of forcing divergent behavior into subtypes of one
  hierarchy, which risks LSP violations when the behaviors are not truly substitutable,
  Strategy models the variation as an interchangeable, explicitly selected object,
  sidestepping the substitutability question because the client explicitly chooses the
  strategy rather than being handed an unexpected subtype.
- **Bridge.** Bridge separates an abstraction from its implementation so both can vary
  independently. It relates to LSP in that Bridge deliberately avoids the substitutability
  question altogether for the implementation hierarchy, because the implementor hierarchy
  is never handed to client code as a substitute for the abstraction, which is one way of
  sidestepping LSP concerns entirely rather than solving them.

## 14. Refactoring path in and out

**Introducing LSP discipline into an existing hierarchy.** Start by identifying every
public method on the base type and writing down, in one line each, what inputs are valid,
what the method guarantees on success, and what must remain true across calls. Next, write
a single shared contract test suite that exercises those statements, boundary-valid input
succeeds, one step past the boundary is rejected, a successful call's postcondition holds.
Run that suite against every existing implementation before changing anything, since this
step alone often surfaces violations that have been silently present for a long time.
Where a violation is found, prefer narrowing the shared contract to what every existing
implementation can genuinely honor over forcing implementations to fake compliance, and
where a genuine capability gap exists, split the interface per the Interface Segregation
Principle rather than leave the mismatch as a runtime exception. Finally, wire the shared
contract test suite into continuous integration so any newly added subtype is checked
automatically before merge.

**Removing an over-constrained hierarchy that no longer earns its place.** When a hierarchy
has only ever had one production implementation for an extended period and no second
implementation is realistically anticipated, per the non-applicability guidance in Section
4, the interface and its contract testing overhead can be collapsed back into a single
concrete class. This is the inverse of introducing a Strategy or extracting an interface,
and the "Replace Superclass with Delegate" and "Collapse Hierarchy" refactorings, as
described in the refactoring literature this catalog's family 03 entries cover, are the
concrete mechanics for that removal.

## 15. Testing and verification

The single most effective testing technique for LSP is a shared contract test suite,
written once against the base type's documented behavior and run against every concrete
implementation, exactly as shown in the code examples in Section 8. This converts an
easily forgotten design discipline into an automated, repeatable gate, and it is what
distinguishes catching a violation at commit time from discovering it in production.

What becomes easier to test because of LSP discipline. once a shared contract test suite
exists, adding a new subtype requires running one existing suite rather than writing an
entirely new set of behavioral assertions from scratch, and a reviewer can verify LSP
compliance mechanically rather than by manual inspection of the diff.

What becomes harder. writing the initial contract test suite requires the author to make
explicit decisions about ambiguous or previously undocumented behavior, which can surface
disagreement between team members about what the "correct" contract actually is, and that
disagreement is real, useful design work that is easy to skip when no test forces it.

Property-based testing complements the shared contract test suite well for interfaces with
mathematical contracts, the total-ordering laws for `Comparable` implementations described
in Common Mistake 4 of the failure modes section being the clearest example, because a
property test can generate a large, varied set of inputs and check the law holds across all
of them rather than relying on a handful of hand-picked examples.

## 16. Observability signals

In production, an LSP violation rarely announces itself as a labeled error. it surfaces as
an exception type that correlates with a specific concrete subtype rather than with a
specific input value. The most useful observability signal is tagging exceptions and error
logs with the concrete class name of the object that threw or returned an unexpected
result, not just the interface type the caller believed it was working with, because
without that tag, an on-call engineer sees "Refundable.refund() threw RangeError" and has
no fast way to discover that the failure only occurs for `GiftCardRefund` instances and
never for `CreditCardRefund` instances.

A healthy instance of an LSP-compliant hierarchy in a dashboard shows error rates for a
given operation staying flat across a deployment that introduces a new subtype, because the
new subtype, by construction, honors the same contract every existing subtype does. A
failing instance shows a sudden, subtype-correlated spike in a specific exception type
immediately following a deployment that adds or changes a subtype, which is the signal to
check that new subtype's behavior against the shared contract test suite described in
Section 15 before doing anything else.

## 17. Security and privacy implications

LSP violations are not typically a direct attack surface in the way an injection
vulnerability is, but they create an indirect risk worth naming. a subtype that weakens a
postcondition around data freshness or authorization scope, for example a caching layer
that silently serves data captured before a permission was revoked, can produce a
security-relevant behavior change that is invisible at the interface level, because the
method signature and return type are unchanged, only the freshness or scope guarantee is
weaker. Any subtype introduced into a hierarchy that mediates access control, financial
authorization, or personal data retrieval deserves explicit review of its precondition and
postcondition claims against the base contract specifically because a silent, undetected
weakening in exactly this class of interface has real security and privacy consequences,
even though the general LSP literature discusses the principle primarily as a correctness
and maintainability concern rather than a security control.

## 18. References

1. Barbara Liskov, "Data Abstraction and Hierarchy," OOPSLA 1987 addendum, *ACM SIGPLAN
   Notices*. The originating keynote for the principle, per the lineage summarized at
   [Liskov substitution principle, Wikipedia](https://en.wikipedia.org/wiki/Liskov_substitution_principle),
   verified 2026-08-09.
2. Barbara H. Liskov and Jeannette M. Wing, "A Behavioral Notion of Subtyping," *ACM
   Transactions on Programming Languages and Systems* (TOPLAS), Volume 16, Issue 6,
   November 1994, pages 1811 to 1841. The formal paper establishing the precondition and
   postcondition inequality and the history-constraint concept, per
   [Liskov substitution principle, Wikipedia](https://en.wikipedia.org/wiki/Liskov_substitution_principle),
   verified 2026-08-09.
3. Robert C. Martin, *Agile Software Development, Principles, Patterns, and Practices*,
   Prentice Hall, 2002. Source of the SOLID acronym in which LSP is the L.
4. Oracle, *Java SE 8 API Specification*, `java.util.List` interface documentation,
   [docs.oracle.com/javase/8/docs/api/java/util/List.html](https://docs.oracle.com/javase/8/docs/api/java/util/List.html),
   verified 2026-08-09. Source for the "optional operations" characterization discussed in
   Sections 9 and 11.
5. Eiffel Software, "Design by Contract and Assertions,"
   [eiffel.org/doc/eiffel/Design%20by%20Contract%20and%20Assertions](https://www.eiffel.org/doc/eiffel/Design%20by%20Contract%20and%20Assertions),
   verified 2026-08-09. Source for Eiffel's `require`/`ensure` inheritance rule discussed
   in Sections 8 and 9.
6. Bertrand Meyer, *Object-Oriented Software Construction*, 2nd edition, Prentice Hall,
   1997. Source of the Design by Contract methodology referenced throughout this entry.
7. Joshua Bloch, *Effective Java*, 3rd edition, Addison-Wesley, 2018. Referenced for the
   Collections Framework's documented tension with strict interface contracts, discussed
   in Section 9.

### Verification notes

The three code examples above were executed locally in this session. the TypeScript
example via `npx tsx notification.ts`, cross-checked by transpiling with `tsc` and running
the output with `node`. the Python example via `python3 collections_lsp.py`. the Go example
via `go run main.go`. All three produced the exact output blocks shown inline, and none of
the output was edited after the run.

The task instructions for this entry called for a minimum of three named production uses
with individually verifiable sources. Within this session, live verification could confirm
one clear, independently checkable production instance, the JDK Collections Framework's
documented optional-operation behavior in `java.util.List` and its `Collections.unmodifiableList`
family of wrappers, plus Eiffel's language-level enforcement of the LSP inequality as a
second, and SOLID's broad industry adoption as evidenced by Martin's own published work as
a third. distinct, individually sourced, named-company production incident write-ups that
explicitly invoke "Liskov Substitution Principle" by name at three different named
commercial systems could not be located and verified within this session, and no such claim
is made in Section 9. Where this entry states engineering judgement rather than a sourced
claim, that is in the code examples throughout the Code examples section, and in the
Symptom-Cause-Fix narrative style used in Section 11, Failure modes and misuse, both of
which are original synthesis illustrating how LSP violations manifest and are fixed in
practice, rather than citations of a specific documented external incident.

## Code examples

### TypeScript, notification channels, contract-tested across subtypes

This example models a notification system with a `NotificationChannel` base contract and
two subtypes, `EmailChannel` and `SmsChannel`. The shared contract test at the bottom is
run against every implementation and would catch a subtype that narrows the accepted
message length differently than it declares.

```typescript
// notification.ts
interface NotificationChannel {
  /** Maximum message length this channel accepts, in characters. */
  maxLength(): number;
  /**
   * Sends a message. Precondition: message.length > 0 and
   * message.length <= maxLength(). Postcondition: returns a delivery id
   * (non-empty string) on success; never returns an empty string.
   */
  send(message: string): string;
}

class EmailChannel implements NotificationChannel {
  maxLength(): number {
    return 10000;
  }
  send(message: string): string {
    if (message.length === 0 || message.length > this.maxLength()) {
      throw new RangeError(`message length ${message.length} out of bounds`);
    }
    return `email-${message.length}-${Date.now()}`;
  }
}

class SmsChannel implements NotificationChannel {
  maxLength(): number {
    return 160;
  }
  send(message: string): string {
    if (message.length === 0 || message.length > this.maxLength()) {
      throw new RangeError(`message length ${message.length} out of bounds`);
    }
    return `sms-${message.length}-${Date.now()}`;
  }
}

// Shared contract test: run against EVERY implementation of NotificationChannel.
// A subtype that narrows the accepted range beyond maxLength(), or returns an
// empty id on success, fails this test regardless of which channel it is.
function assertHonorsContract(channel: NotificationChannel, name: string): void {
  const max = channel.maxLength();

  const boundaryMessage = "x".repeat(max);
  const id = channel.send(boundaryMessage);
  if (id.length === 0) {
    throw new Error(`${name}: FAIL, send() returned empty id at boundary length`);
  }

  let rejectedOverLimit = false;
  try {
    channel.send("x".repeat(max + 1));
  } catch (e) {
    rejectedOverLimit = true;
  }
  if (!rejectedOverLimit) {
    throw new Error(`${name}: FAIL, accepted a message longer than declared maxLength()`);
  }

  console.log(`${name}: PASS`);
}

assertHonorsContract(new EmailChannel(), "EmailChannel");
assertHonorsContract(new SmsChannel(), "SmsChannel");
```

Run with `npx tsx notification.ts`, and separately transpiled with `tsc` then executed with
`node`. Both paths produced.

```
EmailChannel: PASS
SmsChannel: PASS
```

confirming both subtypes are substitutable under the declared contract, since each channel
enforces its own `maxLength()` consistently rather than one silently allowing overlength
messages the other rejects.

### Python, read-only versus mutable collections, the interface-segregation fix

This models the fix for the optional-operation trap described in Section 11. rather than
having an immutable subtype implement a mutable interface and throw at runtime, the
hierarchy is split so the type system prevents the invalid call.

```python
# collections_lsp.py
from abc import ABC, abstractmethod
from typing import Generic, Iterator, TypeVar

T = TypeVar("T")


class ReadableCollection(ABC, Generic[T]):
    """Contract: iteration always yields every element currently present.
    len() always matches the number of items yielded by __iter__."""

    @abstractmethod
    def __iter__(self) -> Iterator[T]:
        ...

    @abstractmethod
    def __len__(self) -> int:
        ...


class MutableCollection(ReadableCollection[T]):
    """Adds a mutation contract on top of ReadableCollection.
    Precondition on add: item is not None. Postcondition: len() increases
    by exactly one after a successful add()."""

    @abstractmethod
    def add(self, item: T) -> None:
        ...


class FrozenList(ReadableCollection[T]):
    """An immutable collection. It implements ONLY ReadableCollection,
    so it is structurally impossible for client code to call add() on it."""

    def __init__(self, items: list[T]):
        self._items = list(items)

    def __iter__(self) -> Iterator[T]:
        return iter(self._items)

    def __len__(self) -> int:
        return len(self._items)


class GrowableList(MutableCollection[T]):
    def __init__(self):
        self._items: list[T] = []

    def __iter__(self) -> Iterator[T]:
        return iter(self._items)

    def __len__(self) -> int:
        return len(self._items)

    def add(self, item: T) -> None:
        if item is None:
            raise ValueError("item must not be None")
        self._items.append(item)


def contract_test_readable(c: ReadableCollection[int], expected: list[int], name: str) -> None:
    actual = list(c)
    assert actual == expected, f"{name}: FAIL iteration mismatch {actual} != {expected}"
    assert len(c) == len(expected), f"{name}: FAIL len() mismatch"
    print(f"{name}: PASS (ReadableCollection contract)")


def contract_test_mutable(c: MutableCollection[int], name: str) -> None:
    before = len(c)
    c.add(42)
    after = len(c)
    assert after == before + 1, f"{name}: FAIL len() did not increase by exactly one after add()"
    try:
        c.add(None)  # type: ignore[arg-type]
        raise AssertionError(f"{name}: FAIL accepted None despite documented precondition")
    except ValueError:
        pass
    print(f"{name}: PASS (MutableCollection contract)")


frozen = FrozenList([1, 2, 3])
contract_test_readable(frozen, [1, 2, 3], "FrozenList")

growable = GrowableList()
growable.add(1)
growable.add(2)
contract_test_readable(growable, [1, 2], "GrowableList")
contract_test_mutable(growable, "GrowableList")

# frozen.add(4) is intentionally omitted: FrozenList has no add() method,
# so a type checker rejects the call at analysis time.
print("All contract tests passed. FrozenList cannot be misused as mutable (structurally enforced).")
```

Run with `python3 collections_lsp.py`. Output.

```
FrozenList: PASS (ReadableCollection contract)
GrowableList: PASS (ReadableCollection contract)
GrowableList: PASS (MutableCollection contract)
All contract tests passed. FrozenList cannot be misused as mutable (structurally enforced).
```

### Go, interface satisfaction without inheritance

Go has no class inheritance, only interface satisfaction, which makes it a useful language
for demonstrating that LSP is a property of behavioral contracts, not of an `extends`
keyword. This example models a `Store` interface, a key-value contract, with two
implementations, an in-memory map-backed store and a store with a maximum-size eviction
policy, and a shared contract checker.

```go
// main.go
package main

import "fmt"

// Store contract:
//  - Get returns (value, true) if key exists, ("", false) otherwise. Never panics.
//  - Put(key, value) makes an immediately subsequent Get(key) return (value, true).
type Store interface {
	Get(key string) (string, bool)
	Put(key string, value string)
}

type MapStore struct {
	data map[string]string
}

func NewMapStore() *MapStore {
	return &MapStore{data: make(map[string]string)}
}

func (m *MapStore) Get(key string) (string, bool) {
	v, ok := m.data[key]
	return v, ok
}

func (m *MapStore) Put(key string, value string) {
	m.data[key] = value
}

// BoundedStore evicts the oldest entry when it exceeds capacity, but it
// still honors the base contract: Put followed by Get on the same key
// returns the value immediately, because eviction only happens for other
// keys, never the key just written. This is the LSP-safe way to add
// eviction, because the base Store interface never promised unbounded
// retention in the first place.
type BoundedStore struct {
	data     map[string]string
	order    []string
	capacity int
}

func NewBoundedStore(capacity int) *BoundedStore {
	return &BoundedStore{data: make(map[string]string), capacity: capacity}
}

func (b *BoundedStore) Get(key string) (string, bool) {
	v, ok := b.data[key]
	return v, ok
}

func (b *BoundedStore) Put(key string, value string) {
	if _, exists := b.data[key]; !exists {
		if len(b.order) >= b.capacity {
			oldest := b.order[0]
			b.order = b.order[1:]
			delete(b.data, oldest)
		}
		b.order = append(b.order, key)
	}
	b.data[key] = value
}

// checkStoreContract must pass for ANY implementation of Store, proving
// the two types are substitutable for the one guarantee the interface
// actually documents.
func checkStoreContract(s Store, name string) {
	s.Put("alpha", "1")
	v, ok := s.Get("alpha")
	if !ok || v != "1" {
		panic(fmt.Sprintf("%s: FAIL, Put then Get on same key did not round-trip", name))
	}

	_, ok = s.Get("does-not-exist")
	if ok {
		panic(fmt.Sprintf("%s: FAIL, Get on missing key returned ok=true", name))
	}

	fmt.Printf("%s: PASS\n", name)
}

func main() {
	checkStoreContract(NewMapStore(), "MapStore")
	checkStoreContract(NewBoundedStore(2), "BoundedStore")
}
```

Run with `go run main.go`. Output.

```
MapStore: PASS
BoundedStore: PASS
```

Both implementations honor the documented `Store` contract. `BoundedStore` is only
substitutable because the base interface never promised unbounded retention. Had the base
`Store` contract explicitly promised that every key ever put remains retrievable
indefinitely, `BoundedStore` would violate LSP by silently evicting old entries, and the
fix would follow the same pattern as the refund example, exposing eviction as a queryable
capability rather than letting it silently violate an assumed but undocumented guarantee.
