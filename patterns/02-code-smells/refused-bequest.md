---
name: Refused Bequest
slug: refused-bequest
family: 02-code-smells
category: Object-Orientation Abusers
aliases: []
first_described: "Fowler, Beck, Brant, Opdyke, Roberts 1999, Refactoring, Improving the Design of Existing Code"
maturity: canonical
related: [large-class, feature-envy, incomplete-library-class, parallel-inheritance-hierarchies, data-class]
incompatible_with: []
verified: 2026-08-02
---

# Refused Bequest

## 1. Name, aliases, and lineage

The canonical name is Refused Bequest. It comes from Martin Fowler, Kent Beck,
John Brant, William Opdyke, and Don Roberts, *Refactoring, Improving the Design
of Existing Code*, Addison-Wesley, 1999, chapter 3, "Bad Smells in Code". The
1999 catalog entry is a short paragraph, in keeping with the rest of that
chapter's entries, and it names the paired refactorings Push Down Method and
Push Down Field as the standard first response. The second edition of the same
book, Addison-Wesley, 2018, keeps the smell under the identical name in the
"Refused Bequest" section of the same chapter and pairs it with a wider set of
refactorings, including Replace Superclass with Delegate and Extract
Superclass, which is discussed in dimension 14 below.

"Bequest" is a deliberate word choice rather than a plain synonym for
inheritance. A bequest, in ordinary English, is what a person leaves to an
heir in a will. Object-oriented inheritance borrows exactly that metaphor, a
superclass "bequeaths" its fields and methods to a subclass, and the subclass
is conventionally expected to accept the whole of what it inherits. Fowler and
Beck's name for the smell names the failure mode precisely, the heir accepts
the estate but refuses part of what came with it, keeping the parts that are
convenient and rejecting or subverting the rest. The term "code smell" itself,
used across this whole family, is attributed by Fowler to Kent Beck, coined
during the work on the Refactoring book (Martin Fowler, "CodeSmell",
https://martinfowler.com/bliki/CodeSmell.html, verified 2026-08-02).

No other name for this smell has independent, widely attested currency in the
literature this entry could verify. Some blog and forum discussions use
informal phrases such as "broken inheritance" or "partial implementation" when
describing the same shape in conversation, but none of those has the kind of
canonical, citable status that "Data Class" or "Feature Envy" carry elsewhere
in this family, so no alias is listed in the frontmatter above rather than
inventing one. The closest formal relative is not a synonym at all but a
principle, the Liskov Substitution Principle. Barbara Liskov first stated the
underlying idea in a 1987 OOPSLA keynote, "Data Abstraction and Hierarchy",
later published as an addendum in *ACM SIGPLAN Notices* 23(5), 1988, and she
and Jeannette Wing gave it a formal statement in "A Behavioral Notion of
Subtyping", *ACM Transactions on Programming Languages and Systems* 16(6),
1994. A Refused Bequest is, structurally, a concrete instance of a Liskov
Substitution Principle violation, but the two are not the same kind of thing.
The principle is a rule about what a well-formed type hierarchy must satisfy.
Refused Bequest is the code smell, the observable shape in a real codebase,
that signals a specific and common way that rule gets broken. This entry
treats the smell, the thing a reader can point at in a diff or a class
browser, and cites the principle only where it explains why the smell matters.

## 2. Problem and context

The smell shows up the moment someone writes a subclass that extends a base
class not because the subclass genuinely wants to honor the base class's
whole public contract, but because the base class already contains a large
fraction of the state and behavior the new class needs, and inheritance is the
fastest way to grab it. The base class exposes some number of public methods.
The new class needs most of them, or most of the underlying storage, but not
all of the behavior. Two paths open at that point. The author can go back and
redesign the hierarchy so the shared part lives somewhere both classes
genuinely fit, which costs time now. Or the author can extend the base class
as it stands and patch the handful of methods that do not fit, by overriding
them to throw, to do nothing, or to return a value that quietly contradicts
what the method promised. The second path is Refused Bequest, and it is
almost always chosen because it compiles immediately and the tests that
exist at the time do not exercise the refused methods.

The context in which this recurs is inheritance chosen for implementation
convenience rather than for behavioral substitutability. A textbook framing
uses a biology-flavored taxonomy, a `Bird` base class carries `eat` and `fly`
because most birds fly, and a `Penguin` subclass is added later because a
penguin genuinely is a bird in every sense a domain modeler cares about
except locomotion. The taxonomy is correct. The inheritance relationship is
not, because `Penguin` cannot honor `fly` the way every existing caller of
`Bird.fly` was written to expect. The same shape recurs constantly in
production code that has nothing to do with animals. A read-only collection
class extends a mutable one because 90 percent of the mutable class's
behavior, storage layout, and iteration logic is exactly what the read-only
class needs, and only `add`, `remove`, and `clear` do not belong. A
specialized cache extends a general purpose map class for the same reason. A
narrow, single purpose subclass extends a broad, general purpose framework
base class because the framework only offers one extension point, and that
extension point happens to be a big class with many methods the narrow
subclass has no use for. In every one of these, the subclass is being asked,
by the type system and by every caller who holds a reference typed at the
base class, to be a full and interchangeable member of the base class's
family, and it declines part of that membership while keeping the type
label.

## 3. Forces

- **Reuse speed against contract honesty.** Inheriting an existing
  implementation is close to free the moment it compiles. Honestly modeling
  only the shared behavior, by extracting a narrower type first, costs real
  design time before any feature work can start. Refused Bequest is what
  happens when the first force wins by default.
- **Interface breadth against interface fitness.** A wide base class gives a
  subclass access to a lot of ready-made behavior in one step, but the wider
  the base class, the less likely any single subclass genuinely needs every
  member of it, so width and fitness pull in opposite directions as a
  hierarchy grows.
- **Coupling against duplication.** The alternative to inheriting an unwanted
  method is usually to duplicate the small amount of logic the subclass
  actually needs, in a class of its own. Refused Bequest favors avoiding that
  duplication at the price of coupling the subclass to the base class's
  entire evolution, including future members the base class has not added
  yet.
- **Team topology and ownership.** When the base class is owned by a
  different team, a library, or a framework, that team's freedom to add
  members to the base class is constrained by every downstream subclass,
  including ones that already refuse part of the current contract. The
  subclass author who introduced the refusal usually does not feel this
  cost, because it lands on whoever maintains the base class later, which is
  a large part of why the smell is easy to introduce and hard to notice at
  the point of introduction.
- **Readability against local convenience.** A reader who sees a type
  extending `Bird` reasonably expects it can `fly`. Every override that
  throws or silently no-ops is a small tax paid by every future reader who
  has to discover, by reading the override or by hitting the exception at
  runtime, that the type's real contract is narrower than its declared type
  suggests.
- **Fail loud against fail silent.** Among the ways to refuse a method,
  throwing is far cheaper to detect than silently doing nothing, but a
  thrown exception in a codepath nobody planned for is still a production
  incident waiting for the right caller, so even the "safer" refusal
  variant only reduces the cost, it does not remove it.

Refused Bequest, taken as a whole, favors the forces of reuse speed and
avoided duplication, and it sacrifices contract honesty, substitutability,
and the reader's ability to trust a type's declared interface. That trade is
sometimes acceptable for a short period in a fast-moving prototype, but it
compounds badly the longer the hierarchy lives and the more callers come to
depend on the base class's declared contract, which is exactly the argument
dimension 10 develops further.

## 4. Applicability and non-applicability

Reach for the Refused Bequest label, and consider it worth fixing, when a
subclass does one or more of the following against a method it inherited from
a public base class.

- Overrides an inherited method to throw an exception whose message says, in
  effect, "this operation is not supported here" (`UnsupportedOperationException`,
  `NotImplementedError`, `NotSupportedException`, and their equivalents in
  other languages).
- Overrides an inherited method to be a silent no-op, where every caller of
  the base type reasonably expects the call to have an effect.
- Overrides an inherited method to return a sentinel value, `null`, `None`,
  an empty collection, or `-1`, that contradicts what the method's
  documented contract promises for a normal instance of the base type.
- Simply never uses, and in code review or documentation actively warns
  against using, a large fraction of the base class's public surface, even
  without a formal override, because calling those members on this
  particular subclass produces wrong results.

Do not apply the label, this is the deliberately explicit non-applicability
list the template requires, in any of these situations.

1. **Template Method usage.** A subclass that overrides only the small,
   designated hook methods of a Template Method base class, while continuing
   to rely on the rest of the base class's public API exactly as documented,
   is doing exactly what the pattern asks of it. Nothing is refused, the
   base class was designed from the start to have those specific methods
   overridden, and the remaining methods are meant to be reused unchanged.
   The distinguishing question is whether the base class's own
   documentation names the override points in advance. If it does, the
   subclass is fulfilling the contract, not refusing it.
2. **Abstract methods implemented as required.** A subclass that supplies a
   real implementation for every abstract method its base class declares is
   not refusing anything, it is doing the ordinary work of polymorphism.
   Refused Bequest is about rejecting something that was already offered as
   a working default, not about being required to supply new behavior for a
   placeholder.
3. **Covariant strengthening.** A subclass that narrows a return type, adds
   extra validation on input, or otherwise strengthens what it promises
   while continuing to honor everything the base type's callers relied on,
   is specializing correctly. The Liskov Substitution Principle explicitly
   permits a subtype to accept a wider range of inputs or promise a
   narrower, more specific range of outputs, so long as every existing
   caller of the supertype still gets what it was promised.
4. **Full, unmodified inheritance.** A subclass that overrides nothing and
   simply uses the base class's behavior as given is, by definition, not
   refusing any part of it. There has to be an actual gap between the
   declared contract and the honored contract for the smell to apply.
5. **Unused non-public members.** If the only unused inherited members are
   private or protected implementation details that no external caller can
   observe through the base type, the situation is dead code or an
   over-broad base class, not Refused Bequest. The smell specifically
   concerns the *public*, caller-visible contract, because that is the part
   a caller relies on for substitutability. An unused protected helper
   misleads nobody outside the hierarchy.

## 5. Structure

Three participants are involved, and the smell lives in the gap between two
of them rather than in any single participant on its own.

- **The Bequeather**, the base class or interface, whose public contract
  defines what any caller holding a reference of that type is entitled to
  expect. In the running example this is `Bird`, offering `eat` and `fly`.
- **The Legatee**, the subclass that extends the Bequeather and inherits its
  full public contract by the ordinary rules of the language, whether or not
  every member of that contract makes sense for this particular subclass.
  In the running example this is `Penguin`.
- **The client**, any code that receives an object typed at the Bequeather
  and, following the ordinary rule of polymorphism, calls members of that
  contract without checking the concrete runtime type first. The client is
  the party actually harmed by the smell, because it did nothing wrong, it
  simply trusted the type it was handed.

The defining structural fact is that the Legatee's *declared* type, the
Bequeather, promises more than the Legatee's *actual* behavior delivers, and
nothing in the type system of a conventional class-based language surfaces
that gap to the client at compile time. The gap is invisible until a specific
call happens to land on the specific refused member.

## 6. ASCII structure diagram

```
                +-------------------+
                |   Bird (base)     |
                |-------------------|
                | + eat(): String   |
                | + fly(): String   |
                +---------+---------+
                          ^
             +------------+------------+
             |                         |
  +----------+---------+   +-----------+----------+
  |     Sparrow          |   |       Penguin         |
  |-----------------------|   |------------------------|
  | + eat(): String       |   | + eat(): String        |
  |   (uses inherited     |   | + fly(): String        |
  |    fly() as is)       |   |   overridden, throws   |
  +-----------------------+   |   "cannot fly"          |
                               +------------------------+

  Client code:
    Bird b = pickAnyBird();     // declared type promises fly()
    b.fly();                    // works for Sparrow, crashes for Penguin
```

## 7. Dynamics

The interaction that exposes the smell always has the same three-step shape,
regardless of which language or which member is involved. First, some piece
of code, often far from where the Penguin was ever constructed, obtains a
reference typed at the base class. This step is frequently a factory, a
dependency injection container, a deserializer, or simply a collection typed
at the base class that mixes several concrete subtypes, because that is
exactly the situation where a caller has no local, syntactic reason to
suspect it is holding anything other than an ordinary member of the base
type. Second, the caller invokes the member the base class's contract
promised, in good faith, the same way it would for any other instance of
that declared type. Third, and only at this point, the concrete subtype's
refusal fires. If the refusal is an exception, the program crashes at a call
site the exception's stack trace does not, by itself, explain, because the
real defect is not in the code that threw, it is in the earlier decision to
model this subtype as a subclass at all. If the refusal is a silent no-op,
nothing crashes, and the caller proceeds believing an operation succeeded
that did not happen.

The dynamic that makes this smell more dangerous than most is the distance
between step one and step three. A missing method, or a type error, is
caught by the compiler at the call site in a statically typed language, at
the moment the mismatch is introduced. A refused method is only caught, if
it is caught at all, at the moment a specific caller happens to invoke it on
a specific concrete instance that happens to be the refusing one, which can
be days, releases, or years after the subclass was written, and can depend
on runtime data the original author never saw. This is also why the smell
tends to survive code review far more easily than most, the reviewer sees a
subclass that compiles cleanly and passes the tests that were written for
it, and the missing negative case, "what happens when a caller who only
knows the base type invokes this," is exactly the case that requires
imagining a future caller who does not yet exist.

## 8. Implementation variants

- **Total refusal.** The subclass overrides nearly every behavioral member
  of the base class, and what it actually inherits and reuses is closer to
  field layout and a handful of private helpers than to any meaningful
  slice of the base class's public contract. This is the most visible
  variant, because the subclass's own source file is made up mostly of
  overrides, and it is usually the easiest to fix because the case for
  extracting a proper shared base or switching to composition is
  unmistakable on sight.
- **Partial refusal**, the shape Fowler and Beck's original catalog entry
  describes. Most of the base class's contract is genuinely reused, and a
  small number of specific members are overridden to refuse. This is the
  most common variant encountered in real systems, and the most dangerous
  precisely because it is the hardest to notice, the subclass looks, at a
  glance, like an ordinary, well-behaved member of the hierarchy.
- **Silent partial refusal.** The subclass does not override the offending
  member at all, and instead the team relies on a comment, a piece of
  external documentation, or tribal knowledge to warn that calling it on
  this subtype is unsupported. There is no runtime defense whatsoever. This
  is strictly worse than an overridden throw, because a caller who never
  read the warning gets whatever the inherited implementation happens to do
  with this subtype's state, which is frequently a subtler and harder to
  diagnose failure than a clean exception.
- **Refusal by exception**, the fail fast variant, `UnsupportedOperationException`
  in Java, `NotImplementedError` in Python, `NotSupportedException` in C
  sharp. The caller finds out immediately, at the exact call that violated
  the narrower contract, which is the least harmful of the concrete
  refusal mechanisms because the failure is loud and its cause is local to
  the call that triggered it.
- **Refusal by no-op.** The overridden method does nothing and returns
  normally, or returns a default value indistinguishable from success. This
  is the most harmful variant, because the caller has no signal at all that
  anything went wrong, and the true consequence of the refusal surfaces
  later, somewhere else in the system, as data that never got written or a
  side effect that never happened.
- **Refusal by sentinel return.** The method returns `null`, `None`, an
  empty collection, or a numeric sentinel like `-1` where a normal instance
  of the base type would never do so. Callers who trust the base type's
  documented contract and skip a null check propagate the sentinel further
  into the system before it is finally noticed, often as a `NullPointerException`
  or an `IndexError` at a third, unrelated location.
- **Cross-language variation in visibility.** Statically typed, class-based
  languages, Java, C sharp, Swift, TypeScript with classes, make the base
  class's full contract visible in the source of the subclass declaration,
  which at least gives a careful reviewer a fighting chance to notice a
  suspiciously wide `extends` clause. Dynamically typed languages that rely
  on duck typing, Python and Ruby in particular, make the smell quieter
  still, because nothing forces the interpreter to check, at class
  definition time or even at most call sites, that the subclass actually
  honors every member of what it inherits, the mismatch is discoverable
  only by exercising the specific refused call path at runtime, whether in
  a test or in production. Languages built entirely around composition and
  structural interfaces rather than class inheritance, Go chief among them,
  do not have this exact failure mode for ordinary interface satisfaction,
  because a Go type only claims to satisfy an interface it genuinely
  implements every method of. Go can still reproduce the same shape through
  struct embedding, however, because an embedded struct's methods are
  promoted onto the embedding struct whether or not every one of them fits
  the embedding type's own invariants, which is demonstrated in the Go code
  sample below and is structurally the same failure as class based
  inheritance's refusal, arrived at through a different language feature.

## 9. Known production uses

- **`java.util.Stack` extending `java.util.Vector`.** The Java Platform SE 8
  API documentation declares the class as `public class Stack<E> extends
  Vector<E>` (Oracle, "Class Stack", https://docs.oracle.com/javase/8/docs/api/java/util/Stack.html,
  verified 2026-08-02). A `Stack` is meant to guarantee last-in-first-out
  access through `push`, `pop`, and `peek`, but because it extends `Vector`,
  every `Stack` instance also inherits `Vector`'s general purpose list
  operations, including `insertElementAt` and `removeElementAt`, which let
  any caller holding a `Stack` reference mutate an arbitrary position in the
  middle of what is supposed to be a strictly ordered stack, breaking the
  very invariant the class exists to guarantee. The class does not refuse
  these methods by overriding them to throw, it inherits and exposes them
  fully, which is the silent partial refusal variant from dimension 8, the
  contract is broken by omission rather than by an explicit override. The
  same official documentation now steers new code away from the class
  entirely, stating "A more complete and consistent set of LIFO stack
  operations is provided by the Deque interface and its implementations,
  which should be used in preference to this class," a rare case of a
  standard library's own reference documentation naming its historical
  design choice as one to avoid.
- **`java.util.Properties` extending `java.util.Hashtable<Object,Object>`.**
  The same Java Platform SE 8 API documentation declares `public class
  Properties extends Hashtable<Object,Object>` (Oracle, "Class Properties",
  https://docs.oracle.com/javase/8/docs/api/java/util/Properties.html, verified
  2026-08-02). `Properties` exists specifically to represent a persistent
  set of string-to-string key-value pairs that can be loaded from and saved
  to a `.properties` file through `getProperty`, `setProperty`, `load`, and
  `store`. Because it extends `Hashtable`, every `Properties` instance also
  inherits the generic `put` and `putAll` methods, which accept any
  `Object` as a key or value, not only `String`. The documentation states
  plainly that use of the inherited methods "is strongly discouraged as
  they allow the caller to insert entries whose keys or values are not
  Strings," and warns that "If the store or save method is called on a
  compromised Properties object that contains a non-String key or value,
  the call will fail." This is the partial refusal variant in spirit,
  though again enforced only by documentation and not by an override, the
  class's own maintainers had to add a permanent warning note to the public
  API reference because the inheritance relationship exposes a wider
  contract than the class can actually honor.
- **`System.Array` implementing `System.Collections.IList`.** The .NET API
  documentation states that "Single-dimensional arrays implement the
  System.Collections.Generic.IList, ICollection, IEnumerable" interfaces
  and the non-generic `System.Collections.IList` interface, and that "The
  key thing to be aware of when you cast an array to one of these
  interfaces is that members that add, insert, or remove elements throw
  NotSupportedException" (Microsoft, "Array Class (System)",
  https://learn.microsoft.com/en-us/dotnet/api/system.array, verified 2026-08-02).
  The same reference page documents the explicit interface implementation
  `IList.Add(Object)` with the remark "Calling this method always throws a
  NotSupportedException exception." This is the clearest example of
  refusal by exception among the three production uses cited here, because
  a .NET array claims, through its declared interfaces, to be a fully
  general, mutable, insertable, removable list, and the framework's own
  documentation confirms that half of that claimed contract exists only to
  reject every call made against it, a fixed size array can never honestly
  support insertion or removal, and the interface it implements was not
  designed with a fixed size collection in mind.

Each of these is a documented, first-party admission from the maintaining
organization, Oracle for the two Java classes and Microsoft for the .NET
type, that the inheritance or interface relationship promises more than the
type can deliver, rather than a third party's opinion about the design.

## 10. Consequences

**Positive**, and genuinely rare in practice. A Refused Bequest can be a
reasonable, deliberate, and short-lived engineering trade in a fast-moving
prototype or an internal tool with a single, known set of callers, where the
team can be certain in the moment that no caller will ever invoke the
refused member, and the alternative, a proper Extract Superclass pass, would
cost more design time than the prototype's lifespan justifies. Reusing a
close-enough base class can also reduce a genuine, otherwise real amount of
duplicated storage layout and boilerplate when the taxonomy really is almost
entirely shared, provided the refused fraction is small, well isolated, and
loudly guarded rather than silently accepted.

**Negative**, and this is the far longer list, which is itself evidence of
how the trade tends to play out over a codebase's real lifetime.

- It is a concrete instance of a Liskov Substitution Principle violation,
  which means every piece of code written against the base type, including
  code that has not been written yet, can no longer be reasoned about
  correctly by reading only the base type's declared contract.
- It converts what would be a compile-time or type-level guarantee into a
  runtime landmine, because the type system of a conventional language has
  no mechanism to say "this subclass satisfies the base type except for
  these three members."
- It increases the cognitive load carried by every future reader and
  reviewer of the hierarchy, who now has to hold, in their head or in a
  comment, the exception list of members that do not actually work the way
  the declared type promises.
- It makes generic testing awkward, a shared contract test suite written
  once against the base type's documented behavior, the single most
  effective automated defense described in dimension 15, has to carve out
  an exception for every refusing subclass, which both weakens the test
  suite's guarantee and signals, every time a new carve-out is added, that
  the hierarchy is drifting further from a genuine substitutable family.
- It worsens the fragile base class problem. Because the subclass already
  depends on only a fraction of the base class's contract while claiming
  all of it, a change to the base class that seems safe from the base
  class's own perspective, adding a new method, changing an existing
  method's documented behavior, can silently interact badly with a
  subclass that was already stretching the relationship thin, and the
  interaction is discovered far from the change that caused it.
- It damages encapsulation in the other direction as well. The subclass
  author has to know, in intimate detail, exactly which parts of the base
  class's internals and contract are safe to accept and which must be
  fought against, which is a level of coupling to the base class's
  implementation that a well-designed inheritance relationship is supposed
  to avoid.
- It compounds. A hierarchy that already contains one refusing subclass is
  a hierarchy where the next engineer, following the existing precedent in
  the codebase, is more likely to add a second one, because the pattern
  "extend and override the parts that do not fit" is now visibly the
  established local convention.

## 11. Failure modes and misuse

Each triple below states an observable symptom first, in the words a person
debugging a real incident would actually use, then the underlying cause, then
the concrete fix.

**Triple 1.**
Symptom, a production crash surfaces an `UnsupportedOperationException`, a
`NotImplementedError`, or a `NotSupportedException`, thrown from deep inside a
generic algorithm that was written against a broad interface, a
`Collection<T>`, an `IList`, an abstract iterator, and that calls a mutating
member like `remove` or `insert` as an ordinary part of its work.
Cause, the concrete object that generic algorithm was handed is actually a
fixed size, read-only, or otherwise restricted subtype that only pretends,
through its declared type, to support the full mutable contract.
Fix, stop modeling the restricted type as a subclass or implementer of the
wider mutable interface. Either implement only the narrower interface the
type genuinely supports, following the Extract Interface refactoring
described in dimension 14, or wrap the underlying data in a language's own
"read-only view" or "unmodifiable wrapper" facility instead of hand-rolling
overrides that throw.

**Triple 2.**
Symptom, data goes missing, or a configuration change silently fails to take
effect, with no exception, no log line, and no obvious failure anywhere near
the call that should have applied it.
Cause, somewhere in the object's actual concrete type, a setter or mutator
inherited from a base type was overridden as a silent no-op refusal instead
of a thrown exception, trading a loud, debuggable failure for a quiet one
that can only be tracked down by comparing expected state against actual
state well after the fact.
Fix, replace the silent no-op with a fail fast exception during active
development so the mismatch surfaces immediately in tests or in early manual
use, and treat that exception as a forcing function to remove the inheritance
relationship rather than as a permanent solution, because a thrown exception
in production is still an incident, only a cheaper one to diagnose than a
silent failure.

**Triple 3.**
Symptom, a code reviewer, or a new team member during onboarding, says some
version of "I am not sure I can call this method on this object" and starts
grepping the codebase for every override before making a change, rather than
trusting the declared type of the variable in front of them.
Cause, the type's actual, honored contract is smaller than the type's
declared, inherited contract, and the only way to know the real boundary is
tribal knowledge, a comment, or a manual search through override
declarations, none of which the type system itself communicates.
Fix, apply Extract Interface so the type's real, honest contract becomes a
named, minimal interface of its own, and retype the call sites that only
ever needed that minimal contract against the new interface, so the
question "what can I safely call on this" becomes answerable by reading a
type signature again instead of by archaeology.

**Triple 4.**
Symptom, a routine addition of a new method to a widely used base class
breaks a distant, unrelated subclass, discovered weeks later, either as a
compile failure in a statically typed language or, worse, as a runtime
failure in a dynamically typed one, in code nobody working on the base class
change was aware of or intended to touch.
Cause, the fragile base class problem compounding with an existing Refused
Bequest, a subclass that was already only partially honoring the base
class's contract had no slack left to absorb further growth of that
contract, so any expansion of the base class's responsibilities ripples
unpredictably into every subclass that was already stretching the
relationship thin.
Fix, before adding new members to a base class with any known refusing
subclasses, narrow the base class's contract first, using Extract
Superclass to carve out the genuinely shared subset, then add the new
member to the appropriate level of the now-narrower hierarchy, or invert
the relationship into composition entirely so that future growth of one
type's responsibilities cannot silently reach into another type that never
asked to inherit it.

## 12. Trade-off matrix

The comparison is between Refused Bequest, treated here as the default,
unexamined outcome of choosing implementation inheritance where the
subclass does not genuinely fit the base contract, and four named
alternatives that each solve the same underlying reuse problem in a
different way. The forces are drawn from dimension 3.

| Approach | Substitutability | Reuse effort now | Coupling to base's future growth | Testability with a shared contract suite | Evolvability of the base type |
|---|---|---|---|---|---|
| Refused Bequest (unexamined inheritance) | Broken, LSP violated at the refusing members | Lowest, one `extends` clause | High, every future base member risks a new refusal | Weak, needs per-subclass carve-outs | Poor, fragile base class risk on every addition |
| Template Method (used as designed) | Preserved, hooks are the only override points | Moderate, base class must be authored with hooks in mind | Moderate, subclasses only depend on the documented hook contract | Strong, the non-hook contract is shared and testable as one | Good, new non-hook members are safe by construction |
| Strategy | Preserved, no inheritance of an unwanted contract at all | Moderate, requires defining a small behavior interface | Low, the strategy interface is independently versioned | Strong, strategy implementations are tested in isolation | Very good, base type and strategy evolve independently |
| Extract Superclass | Preserved for the new, narrower supertype | Moderate, one-time refactor cost | Low, the narrower supertype grows only with genuine agreement across all subclasses | Strong, the narrow contract is exactly what the shared test suite should assert | Good, the wide original class's growth no longer forces subclass changes |
| Delegation, Replace Superclass with Delegate | Preserved, only forwarded methods are exposed | Moderate, one-time refactor cost, ongoing small forwarding boilerplate | Lowest, the delegate is a private implementation detail, not a public supertype | Strong, the wrapper's own narrow contract is directly testable | Very good, the delegate can change freely without breaking the wrapper's callers |

Refused Bequest wins only on immediate reuse effort, and loses on every other
force in the table, which is the concrete, comparable evidence behind the
consequences described in dimension 10.

## 13. Related and incompatible patterns

- **Template Method.** This is the pattern Refused Bequest is most often
  mistaken for, or defended as, in code review, because both involve a
  subclass overriding part of what it inherits. The distinction is intent
  and documentation. In a genuine Template Method, the base class author
  designed specific hook methods to be overridden and documented them as
  such, and the rest of the base class's contract is meant to be reused
  unmodified, so overriding a hook honors the contract rather than
  refusing it. In Refused Bequest, the override exists because the
  subclass does not fit, not because the base class invited that exact
  override.
- **Strategy.** Frequently the correct destination when a Refused Bequest is
  fixed, because Strategy extracts precisely the varying piece of behavior,
  the part a naive inheritance hierarchy was trying and failing to
  specialize, into a small interface that is injected rather than
  inherited, which removes the pressure to force every variant into a
  single class hierarchy at all.
- **Composite.** Directly at risk of degenerating into Refused Bequest if
  applied carelessly, because the Composite pattern asks every leaf and
  every branch type to honestly support one uniform component interface,
  and a leaf that cannot meaningfully support a child-management operation
  like `add` or `remove` is forced into the same refusal shape described in
  this entry unless the component interface is deliberately kept narrow
  enough that leaves can honor it in full.
- **Bridge.** Exists specifically to prevent one hierarchy's contract from
  being forced onto a second, differently varying hierarchy, by separating
  an abstraction hierarchy from an implementation hierarchy so that neither
  side has to inherit members that only make sense for the other side's
  variation, which makes Bridge a structural preventive measure against the
  conditions that produce Refused Bequest in systems with two independent
  axes of variation.
- **Decorator.** Wraps an object rather than inheriting from a common base,
  so a Decorator never has to accept a wider contract than it intends to
  honor in the first place, sidestepping the entire problem this smell
  describes rather than curing it after the fact.
- **Extract Superclass, Replace Superclass with Delegate, Replace Subclass
  with Delegate, Push Down Method, Push Down Field, Collapse Hierarchy.**
  The concrete refactorings that resolve an existing Refused Bequest once
  it is identified in real code, developed further in dimension 14.
- **Parallel Inheritance Hierarchies.** A sibling smell in this same family,
  and both stem from over-applying inheritance as the default reuse
  mechanism, but they are not the same shape. Parallel Inheritance
  Hierarchies concerns two or more hierarchies that must grow in lockstep,
  a new subclass in one forces a matching new subclass in another. Refused
  Bequest concerns a single hierarchy where one member does not honestly
  fit the shared contract at all. A codebase can exhibit either smell
  without the other.

**Incompatible with.** The Liskov Substitution Principle, by definition. A
type hierarchy cannot simultaneously satisfy the Liskov Substitution
Principle for a given member and exhibit a true Refused Bequest on that same
member, because the smell is, structurally, exactly what an LSP violation
looks like when read out of source code rather than out of a formal proof.

## 14. Refactoring path in and out

**How it typically enters a codebase.** The pattern is consistent enough
across languages and teams to describe as a single narrative. Two classes,
or a class and a new requirement, turn out to share a large majority of
their fields and methods. Someone notices the overlap and reaches for
`extends`, because inheriting the shared 80 percent is the fastest available
way to avoid retyping it. The remaining fraction that does not fit gets
patched with an override that throws, that does nothing, or that is left
alone with a warning comment. The code compiles, the tests that exist at
that moment pass, because those tests were written against the call paths
the author already had in mind, and the decision is never revisited, because
nothing forces a revisit until a caller the original author did not
anticipate exercises the refused path.

**Getting out**, step by step.

1. **Map the honored contract against the declared contract.** For the
   subclass under review, list every public member of the base class and
   mark each one as genuinely honored, refused by exception, refused by
   no-op, or refused by sentinel. This map is the concrete evidence for
   every step that follows, and writing it down, rather than reasoning
   about it in the abstract, is usually what convinces a skeptical
   reviewer that the smell is real.
2. **Add characterization tests before changing anything.** Write tests
   that pin down the exact current behavior of every member on the map,
   including the refusing overrides, so the refactor that follows can be
   checked mechanically for accidental behavior change rather than relying
   on manual review alone. These tests are explicitly temporary, they exist
   to protect the refactor, and some of them are meant to be deleted or
   rewritten once the refusal itself is legitimately removed.
3. **Choose Push Down Method and Push Down Field when the wide contract is
   still correct for most of the hierarchy.** If the refusing subclass is
   an outlier and its siblings genuinely need the full base class contract,
   move the specific refused members down out of the shared base class and
   into whichever sibling subclasses actually want them. The outlier
   subclass then simply no longer inherits members it never honored, and
   its declared type finally matches its real behavior.
4. **Choose Replace Superclass with Delegate when the subclass needs almost
   none of the base class's contract.** This refactoring, named "Replace
   Inheritance with Delegation" in the 1999 first edition of Fowler and
   Beck's catalog and renamed in the 2018 second edition and in the
   maintained online catalog at refactoring.com/catalog, converts the
   "is-a" relationship into a "has-a" relationship. The former subclass
   holds a private reference to an instance of the former base class and
   forwards only the specific calls it genuinely wants to reuse, exposing
   nothing else. Every member the subclass used to refuse simply
   disappears from its own public surface, because it was never truly part
   of the new class's contract to begin with.
5. **Choose Extract Superclass, or Extract Interface, when callers rely on
   polymorphism across the whole family.** When client code genuinely needs
   to treat several sibling types uniformly through one shared type, and
   that is the reason the hierarchy exists at all, carve out a new,
   narrower supertype that contains only the members every sibling can
   honestly honor, then retype the polymorphic call sites against that
   narrower supertype instead of the original, wider one. This is the
   concrete mechanism by which the Interface Segregation Principle gets
   restored in a codebase that already committed to one wide, shared type.
6. **Choose Collapse Hierarchy for a hierarchy that should never have been
   built on inheritance at all.** When the "is mostly a kind of" reasoning
   that originally justified the hierarchy turns out, on reflection, to
   have been a reasonable domain observation but a poor implementation
   choice, flatten the hierarchy entirely and rebuild the shared behavior
   as a small set of independent interfaces implemented separately by each
   type, which removes any single class from being forced to answer for a
   contract wider than what it actually does.
7. **Verify against the characterization tests from step 2, then delete the
   tests that were only pinning down the removed refusal**, keeping any
   test that still documents genuine, intended behavior of the resulting
   design.

## 15. Testing and verification

This dimension is drawn from practice and professional judgement rather than
from a single citable source, stated here plainly as the template requires.

The most direct automated defense against Refused Bequest is a shared
contract test suite, sometimes called an abstract test case or a contract
test, written once against the base type's documented behavior and run
against every concrete subtype in the hierarchy. JUnit's pattern of an
abstract test class extended by one concrete test class per subtype, and the
equivalent pattern using a shared mixin base class in Python's `unittest`,
both implement this idea directly. When such a suite exists and is run
against a refusing subclass, the smell surfaces as a normal, visible test
failure, at the point where the shared suite exercises the refused member,
rather than as a surprise discovered later at runtime. If a team is already
carving exceptions or skips into a shared contract test suite for one
specific subclass, that carve-out is itself a reliable, automatable signal
that a Refused Bequest is present and worth investigating, independent of
whether anyone has manually flagged it as a code smell.

While the refactor described in dimension 14 is still being planned, and the
refusal has not yet been removed, a temporary negative test asserting that
the refused method actually does throw, or actually does behave as the
current override documents, is a reasonable stopgap. It prevents a well
meaning future edit from silently changing the refusal's behavior in a way
that makes an already bad situation worse, and it should carry a comment
pointing at the tracked refactor rather than being mistaken for permanent,
intended coverage.

Property based testing, distinct from example based unit testing, is
unusually effective at surfacing this smell because a property based test
does not know, or care, which members a human author considers "the ones a
caller would actually use." A property based test that generates arbitrary
sequences of calls against the base type's declared contract and asserts the
base type's stated invariants will happily call the refused members exactly
as often as the honored ones, and will fail the moment it does, without
anyone having to think to write that specific negative case by hand.

What gets harder once a Refused Bequest exists is reuse of generic test
helpers. A helper written once to assert "this object behaves like a
well-formed instance of the base type," intended to be reusable across every
subtype, can no longer be applied unmodified to the refusing subclass
without adding exceptions for the refused members, and that growing list of
exceptions inside what was meant to be a generic helper is, again, a
reliable, mechanically observable diagnostic for the smell in its own right.

## 16. Observability signals

This dimension is also practice and professional judgement, stated plainly.

Refused Bequest is one of the few smells in this family where the failure
event itself, correctly logged, is close to the best possible telemetry a
team could design on purpose. Every time a refusing override actually fires
in a running system, whether through the exception path or, if the team has
not yet converted a silent refusal into a loud one, through a deliberately
added log call at the site of the no-op, that event is direct, unambiguous
evidence that some caller believed the wider, declared contract and was
wrong. Logging the calling context at that point, ideally with a full stack
trace and enough state to identify which factory, container, or
deserialization path produced the reference, turns an otherwise mysterious
production incident into an actionable one, because the log line names both
the surprised caller and the refusing type in one event.

A healthy instance of a system that once had, or still tolerates, a known
Refused Bequest looks like a dashboard counter for "refused member
invocation count" sitting at exactly zero across the service's normal
traffic. A team that has already identified a refusal, decided the risk is
acceptable in the near term, and added this counter as a safety net, gets a
concrete, falsifiable answer to the question "is anyone actually hitting
this" instead of an assumption. A failing instance looks like a nonzero and
climbing count on that same counter, or a spike in the specific exception
type, `UnsupportedOperationException`, `NotImplementedError`,
`NotSupportedException`, correlated in time with a recent change to any
code path that constructs objects generically, a factory, a dependency
injection container, or a deserializer, because generic construction is
exactly the situation, described in dimension 7, where a caller most easily
loses track of which concrete subtype it actually received.

## 17. Security and privacy implications

This dimension is analytical, drawn from reasoning about the smell's
mechanics rather than from a documented security advisory, stated plainly
because it would be dishonest to invent a broader claim than the mechanics
actually support.

For the ordinary case, a hierarchy with no security or access control
sensitive members among the refused set, Refused Bequest is a correctness
and maintainability concern and nothing more, and it would overstate the
smell to claim otherwise. There is one specific and genuinely security
relevant case worth naming directly. If the refused member is a security
sensitive mutator, a method named something like `revokeAccess`,
`clearCredential`, `setPermission`, or `invalidateSession`, and the chosen
refusal variant is the silent no-op described in dimension 8 rather than a
thrown exception, the consequence is not merely a bug, it is a caller
reasonably believing that a security relevant state change took effect when
it did not. A caller that calls `revokeAccess` and receives a normal,
successful looking return has every reason to believe the access was
revoked. If the concrete type silently refused that call, the access
persists, and the gap between believed state and actual state is precisely
the kind of condition that turns an ordinary design smell into an
exploitable one. The specific, actionable conclusion is narrow and
unambiguous, a Refused Bequest on a security or privacy sensitive base type
must never be implemented as a silent no-op. It should always fail loud,
through an immediate thrown exception, precisely because the cost of a
caller wrongly believing a security operation succeeded is categorically
higher than the cost of an exception the caller has to handle.

## 18. References

1. Martin Fowler, Kent Beck, John Brant, William Opdyke, and Don Roberts,
   *Refactoring, Improving the Design of Existing Code*, 1st edition,
   Addison-Wesley, 1999, chapter 3, "Bad Smells in Code", entry "Refused
   Bequest", paired with the refactorings Push Down Method and Push Down
   Field.
2. Martin Fowler, *Refactoring, Improving the Design of Existing Code*, 2nd
   edition, Addison-Wesley, 2018, chapter 3, "Refused Bequest" entry.
3. Martin Fowler, "CodeSmell",
   https://martinfowler.com/bliki/CodeSmell.html, verified 2026-08-02. Source for
   the attribution of the term "code smell" to Kent Beck.
4. Martin Fowler, https://refactoring.com/catalog/, verified 2026-08-02. Source for
   the current names of the associated refactorings, including Push Down
   Method, Push Down Field, Replace Superclass with Delegate, Replace
   Subclass with Delegate, Extract Superclass, and Collapse Hierarchy, and
   for confirming Replace Superclass with Delegate as the current name of
   what the 1999 first edition called Replace Inheritance with Delegation.
5. Barbara Liskov, "Data Abstraction and Hierarchy", OOPSLA 1987 keynote
   address, published as an addendum in *ACM SIGPLAN Notices* 23(5), 1988.
   Original statement of the substitution idea.
6. Barbara H. Liskov and Jeannette M. Wing, "A Behavioral Notion of
   Subtyping", *ACM Transactions on Programming Languages and Systems*
   16(6), 1994. Formal statement of what is now called the Liskov
   Substitution Principle.
7. Oracle, "Class Stack",
   https://docs.oracle.com/javase/8/docs/api/java/util/Stack.html, verified
   2026-08-02. Source for the `Stack extends Vector` production example
   and the documented recommendation to prefer `Deque`.
8. Oracle, "Class Properties",
   https://docs.oracle.com/javase/8/docs/api/java/util/Properties.html, verified
   2026-08-02. Source for the `Properties extends Hashtable` production
   example and the documented warning against the inherited `put` and
   `putAll` methods.
9. Microsoft, "Array Class (System)",
   https://learn.microsoft.com/en-us/dotnet/api/system.array, verified 2026-08-02.
   Source for the `System.Array` implementing `IList` production example
   and the documented `NotSupportedException` behavior of its mutating
   members.

## Code examples

Four languages are used here. TypeScript and Python because class based
inheritance and the fix through an extracted interface or protocol translate
almost directly from the running `Bird` and `Penguin` example used
throughout this entry. Swift for the same reason, and because it is a
statically typed, protocol oriented language whose fix reads differently
from TypeScript's structural typing. Go because it has no class inheritance
at all, and the closest equivalent, struct embedding promoting a method set
onto an embedding type whether or not every promoted method fits, lets the
Go sample map directly onto the `Stack extends Vector` production case from
dimension 9 rather than the biology flavored example used by the other
three, which is a genuinely different and instructive way the same smell
appears. Java and C sharp are not included as code samples even though both
appear in dimension 9's production uses, because the Java runtime was not
actually available on this machine at the time of writing, and it would be
dishonest to present unexecuted Java or C sharp code as verified. Every
sample below was compiled or run on this machine as part of authoring this
entry.

### TypeScript

Compiled with `tsc` targeting ES2020 and run with `node`. Output confirmed.

```typescript
abstract class BirdSmell {
  abstract eat(): string;
  fly(): string {
    return "flying at altitude";
  }
}

class SparrowSmell extends BirdSmell {
  eat(): string {
    return "eating a seed";
  }
}

class PenguinSmell extends BirdSmell {
  eat(): string {
    return "eating a fish";
  }
  fly(): string {
    throw new Error("penguins cannot fly");
  }
}

function sendToSky(bird: BirdSmell): void {
  console.log(bird.fly());
}

const flock: BirdSmell[] = [new SparrowSmell(), new PenguinSmell()];
for (const bird of flock) {
  try {
    sendToSky(bird);
  } catch (err) {
    console.log(`crash: ${(err as Error).message}`);
  }
}

// The fix. Separate the optional capability from the shared contract.
interface Flyable {
  fly(): string;
}

abstract class BirdFixed {
  abstract eat(): string;
}

class SparrowFixed extends BirdFixed implements Flyable {
  eat(): string {
    return "eating a seed";
  }
  fly(): string {
    return "flying at altitude";
  }
}

class PenguinFixed extends BirdFixed {
  eat(): string {
    return "eating a fish";
  }
}

function sendToSkyFixed(bird: Flyable): void {
  console.log(bird.fly());
}

const flockFixed: BirdFixed[] = [new SparrowFixed(), new PenguinFixed()];
for (const bird of flockFixed) {
  if ("fly" in bird) {
    sendToSkyFixed(bird as unknown as Flyable);
  } else {
    console.log(`${bird.eat()}, no flight attempted`);
  }
}
```

Running the smell version prints `flying at altitude` for the sparrow, then
`crash: penguins cannot fly` for the penguin, exactly the runtime landmine
described in dimension 7. Running the fixed version prints `flying at
altitude` for the sparrow and `eating a fish, no flight attempted` for the
penguin, with no exception, because `PenguinFixed` no longer declares a
contract it cannot honor.

### Python

Run with `python3`. Output confirmed.

```python
from abc import ABC, abstractmethod


class BirdSmell(ABC):
    @abstractmethod
    def eat(self):
        ...

    def fly(self):
        return "flying at altitude"


class SparrowSmell(BirdSmell):
    def eat(self):
        return "eating a seed"


class PenguinSmell(BirdSmell):
    def eat(self):
        return "eating a fish"

    def fly(self):
        raise NotImplementedError("penguins cannot fly")


def send_to_sky(bird):
    print(bird.fly())


for bird in (SparrowSmell(), PenguinSmell()):
    try:
        send_to_sky(bird)
    except NotImplementedError as err:
        print(f"crash: {err}")


# The fix. A separate Flyable protocol instead of an inherited method
# every bird is assumed to honor.
class Flyable(ABC):
    @abstractmethod
    def fly(self):
        ...


class BirdFixed(ABC):
    @abstractmethod
    def eat(self):
        ...


class SparrowFixed(BirdFixed, Flyable):
    def eat(self):
        return "eating a seed"

    def fly(self):
        return "flying at altitude"


class PenguinFixed(BirdFixed):
    def eat(self):
        return "eating a fish"


def send_to_sky_fixed(bird):
    print(bird.fly())


for bird in (SparrowFixed(), PenguinFixed()):
    if isinstance(bird, Flyable):
        send_to_sky_fixed(bird)
    else:
        print(f"{bird.eat()}, no flight attempted")
```

This mirrors the TypeScript sample. `PenguinSmell().fly()` raises
`NotImplementedError`, caught and printed as `crash: penguins cannot fly`,
while `PenguinFixed` simply never claims to be `Flyable`, so
`isinstance(bird, Flyable)` correctly steers the caller away from a call
that was never going to work.

### Go

Run with `go run`. Output confirmed. This sample maps directly onto the
`Stack extends Vector` production use from dimension 9, using struct
embedding rather than class inheritance, since Go has no class inheritance.

```go
package main

import "fmt"

type Vector struct {
	items []int
}

func (v *Vector) InsertAt(i int, x int) {
	v.items = append(v.items, 0)
	copy(v.items[i+1:], v.items[i:])
	v.items[i] = x
}

// StackSmell embeds Vector, so InsertAt is promoted whether or not
// it fits a stack's last-in-first-out invariant.
type StackSmell struct {
	Vector
}

func (s *StackSmell) Push(x int) { s.items = append(s.items, x) }

func (s *StackSmell) Pop() int {
	n := len(s.items) - 1
	top := s.items[n]
	s.items = s.items[:n]
	return top
}

// stacker names only the contract a stack actually needs to honor.
type stacker interface {
	Push(int)
	Pop() int
}

type StackFixed struct {
	items []int
}

func (s *StackFixed) Push(x int) { s.items = append(s.items, x) }

func (s *StackFixed) Pop() int {
	n := len(s.items) - 1
	top := s.items[n]
	s.items = s.items[:n]
	return top
}

func main() {
	s := &StackSmell{}
	s.Push(1)
	s.Push(2)
	s.InsertAt(0, 99)
	fmt.Println("stack invariant broken, bottom is now", s.items[0])

	var f stacker = &StackFixed{}
	f.Push(1)
	f.Push(2)
	fmt.Println("popped", f.Pop())
}
```

The embedded `Vector`'s `InsertAt` method is promoted onto `StackSmell`
whether anyone intended a stack to support arbitrary positional insertion or
not, and the program prints `stack invariant broken, bottom is now 99`,
demonstrating the exact same contract violation as `java.util.Stack`
inheriting `Vector`'s `insertElementAt`. `StackFixed` exposes only `Push`
and `Pop` through the narrow `stacker` interface, so no caller of that
interface can reach an operation the type was never meant to support, and
the program prints `popped 2`.

### Swift

Compiled with `swiftc`. Output confirmed.

```swift
class BirdSmell {
    func eat() -> String { fatalError("must override") }
    func fly() -> String { "flying at altitude" }
}

class SparrowSmell: BirdSmell {
    override func eat() -> String { "eating a seed" }
}

class PenguinSmell: BirdSmell {
    override func eat() -> String { "eating a fish" }
    override func fly() -> String {
        fatalError("penguins cannot fly")
    }
}

func sendToSky(_ bird: BirdSmell) -> String {
    bird.fly()
}

print(sendToSky(SparrowSmell()))
// PenguinSmell().fly() would call fatalError and trap the process,
// which is why it is not invoked directly in this sample.

// The fix. Flyable is a protocol, honored only by types that mean it.
protocol Flyable {
    func fly() -> String
}

class BirdFixed {
    func eat() -> String { fatalError("must override") }
}

class SparrowFixed: BirdFixed, Flyable {
    override func eat() -> String { "eating a seed" }
    func fly() -> String { "flying at altitude" }
}

class PenguinFixed: BirdFixed {
    override func eat() -> String { "eating a fish" }
}

func sendToSkyFixed(_ bird: Flyable) -> String {
    bird.fly()
}

let flock: [BirdFixed] = [SparrowFixed(), PenguinFixed()]
for bird in flock {
    if let flyer = bird as? Flyable {
        print(sendToSkyFixed(flyer))
    } else {
        print("\(bird.eat()), no flight attempted")
    }
}
```

Swift's `fatalError` traps the whole process rather than throwing a
catchable error, which is why the smell side of this sample deliberately
does not call `PenguinSmell().fly()` directly, calling it would end the
program rather than let the sample continue and print the fixed section.
The output confirmed on this machine is `flying at altitude` for the
sparrow smell case, the placeholder line noting the trap, then `flying at
altitude` and `eating a fish, no flight attempted` for the fixed section,
where `as? Flyable` on `PenguinFixed` correctly returns `nil` and the
caller never attempts a call the type does not support.
