---
name: Speculative Generality
slug: speculative-generality
family: 02-code-smells
category: Structural
aliases: [Gold Plating, Over-Engineering, YAGNI Violation, Needless Complexity]
first_described: "Fowler, Beck, Brant, Opdyke, Roberts 1999"
maturity: canonical
related: [strategy, template-method, factory-method, dead-code, feature-envy]
incompatible_with: []
verified: 2026-08-02
---

# Speculative Generality

## 1. Name, aliases, and lineage

The canonical name is Speculative Generality, one of the twenty-two smells
catalogued in Martin Fowler's *Refactoring. Improving the Design of Existing
Code*, Addison-Wesley, 1999, in the chapter titled "Bad Smells in Code", a
chapter Fowler wrote jointly with Kent Beck. The chapter groups the smells
alphabetically by concept rather than by cause, and Speculative Generality sits
among the smells about unnecessary structure, alongside Lazy Class and Data
Class. Fowler's own description of the smell, paraphrased rather than quoted
because the book is not reproduced here, is that it appears whenever someone
says "we might need this someday" and builds a hook, a parameter, an abstract
class, or a delegation layer to support a case that has not actually arrived.
The book's own antidotes for it are the refactorings Collapse Hierarchy, Inline
Class, Inline Function, Remove Parameter, and Rename Method, each aimed at
removing a piece of structure that abstraction added but that no caller
exercises.

The most commonly used alias is **Gold Plating**, a term with roots in software
project management that predates the smell catalog and describes work performed
beyond what a requirement specifies. **Over-Engineering** is used more loosely
in casual conversation and does not always refer to this specific smell, it can
also describe premature performance optimisation, which is a different failure.
**YAGNI Violation** names the smell from the other direction, by naming the
principle it breaks. "You Aren't Gonna Need It" is one of the practices named in
Kent Beck's *Extreme Programming Explained*, and Martin Fowler's own account of
the principle states plainly that "any extensibility point that's never used
isn't just wasted effort, it's likely to also get in your way as well", an
observation he attributes to Jeremy D. Miller
([martinfowler.com/bliki/Yagni.html](https://martinfowler.com/bliki/Yagni.html),
verified 2026-08-02). The same page draws the boundary of the principle
precisely. "Yagni only applies to capabilities built into the software to
support a presumptive feature, it does not apply to effort to make the software
easier to modify", which separates this smell from legitimate investment in
testability, modularity, or maintainability. A codebase that is easy to change
because its modules are well separated has not committed Speculative
Generality. A codebase that carries an unused `Strategy` interface with one
implementation, an unused constructor parameter nobody passes a second value
for, or an abstract base class with exactly one subclass, has.

## 2. Problem and context

The smell shows up at the moment a developer, while building the one feature
actually requested, imagines a family of features that might follow it and
builds the software to accommodate the whole imagined family rather than the
one member of it that is real. The proximate cause is almost always a genuine
professional instinct working against itself, experienced developers have been
burned by code that was too rigid to extend, so they overcorrect by writing
code that is maximally extensible before there is a second case to extend it
for. The context in which this happens is recognisable. A single payment method
is being added and the author writes a `PaymentStrategy` interface with a
`PaymentGateway` abstraction and a `PaymentContext` object, when the actual
requirement is "charge a credit card". A configuration file gets a `type` field
with one legal value and a switch statement with one case, because someone
expects a second value to show up. A method gains a `Map<String, Object>
options` parameter that nothing populates, added so that "whatever gets added
later has somewhere to go."

The problem this produces is not that the code fails to work. Speculative
Generality code usually works correctly for its one real case, because it was
built and tested against that case. The problem is what it costs every reader
who touches the code afterward. An unused abstraction is a lie about the
system's actual shape, it tells the next engineer that variation exists along
an axis where, in fact, only one point on that axis has ever been populated.
Following the abstraction to find out what it is for costs real time and
returns nothing, because there is nothing there to find. Kent Beck's own
XP-era heuristic, that the correct threshold for introducing generality is
"three strikes", meaning generalise on the third occurrence of a pattern rather
than the first, is the practical antidote most experienced teams converge on
independently even when they have never read the book that names the smell.

## 3. Forces

**Anticipated flexibility versus current simplicity.** The pull toward
generality is a bet that future requirements will resemble what was
anticipated closely enough that the abstraction built today saves work
tomorrow. The pull toward simplicity is the observation that most predictions
about future requirements are wrong, and a wrong abstraction is more expensive
to unwind than a late one is to add, because by the time it is wrong it usually
has callers depending on its exact, now-incorrect shape.

**Cognitive load on the reader versus authorial effort now.** Building the
general version once, while the requirement and the author's context are both
fresh, feels cheaper to the author than building the narrow version now and
generalising later. But every reader after the author pays the cognitive cost
of the generality on every visit, whether or not the generality is ever used,
and that cost compounds across the number of readers and the number of visits,
which is almost always larger than one.

**The cost of being wrong twice.** A premature abstraction gets the shape of
the future feature wrong more often than it gets it right, because the
information needed to design the abstraction correctly, namely a second real
case, does not exist yet when the abstraction is built. When the second case
finally arrives, it usually does not fit the guessed shape, and the team faces
a choice between distorting the new feature to fit the wrong abstraction or
reworking the abstraction under time pressure with the first case's code
already depending on it. Building the concrete version first and generalising
from two real cases produces an abstraction shaped by evidence rather than by
guesswork.

**Team velocity versus architectural ambition.** A team under delivery pressure
that reaches for generality is trading present velocity for a hoped-for future
velocity that a wrong guess will not deliver. This force is the reason the
smell recurs particularly in code written by senior engineers on greenfield
projects who have the authority to make the design call and the scar tissue
from past under-abstracted systems that motivates the overcorrection.

**Testability of the general versus the concrete.** An abstract interface with
one implementation is not, on its own, harder to test than a concrete class,
in fact it can appear easier, because it is trivial to substitute a test
double. The force here favours generality shallowly and is often used to
justify it, but the depth of the interface, its unused parameters and hook
methods, still has to be exercised or explicitly documented as untested, and
in practice speculative parameters are the ones a test suite is least likely
to cover, because nobody has a real second case to write a test against.

## 4. Applicability and non-applicability

Reach for deliberate, evidence-based generality under these conditions.

- A second and a third real, currently-required case of a variation already
  exist, and the shared shape between them is visible from the actual code
  rather than from a guess about what a hypothetical third case might need.
  This is Beck's rule of three in practice.
- The variation point is explicitly named in the product roadmap with a
  committed delivery date, not a "might happen" note, and the cost of building
  the extension point now is genuinely lower than the cost of retrofitting it
  onto code with an established caller later, for example because the
  extension point sits at a serialisation boundary that is expensive to
  version after data has been persisted in the old shape.
- The abstraction is required by an external contract the team does not
  control, for example a plugin API a third party will implement against, so
  by definition there is no way to wait for a second internal caller because
  the caller is external and out of the team's design control.
- The abstraction already exists in a well-known, stable library or platform
  interface (an iterator protocol, a comparator, a standard collection
  interface) and adopting it costs nothing beyond implementing the one method
  the current feature needs, because the generality was paid for once by the
  platform, not per project.

This is not deliberate generality, this is Speculative Generality, under these conditions.

- The justification for the abstraction is a sentence beginning "we might need
  this later" with no named feature, no ticket, and no date attached to the
  claim. This is the single clearest tell described on Fowler's own YAGNI page,
  which states the principle applies exactly to "capabilities built into the
  software to support a presumptive feature"
  ([martinfowler.com/bliki/Yagni.html](https://martinfowler.com/bliki/Yagni.html),
  verified 2026-08-02).
- There is exactly one concrete implementation of an interface, exactly one
  subclass of an abstract class, or exactly one value ever passed for a
  parameter, and no second case is scheduled.
- The abstraction was introduced to make a single unit test possible rather
  than to serve two or more real callers, that motivation is Dependency
  Inversion applied correctly for testability, not Speculative Generality, but
  the two are frequently confused, and the distinguishing question is whether
  the seam exists because production code has two real shapes or because a
  test needed to substitute a double for one shape. If it is only the latter,
  prefer the narrowest seam that achieves testability, not a full strategy
  hierarchy.
- The team is small, the domain is still being discovered, and the cost of a
  wrong guess about future shape is high relative to the cost of a fast,
  narrow rewrite once the real shape is known. Early-stage products are the
  environment where Speculative Generality is most expensive relative to the
  value it could theoretically return, because the guess is least likely to be
  right and the code is cheapest to still change narrowly.

## 5. Structure

Speculative Generality has no fixed structure the way a design pattern does,
because it is the presence of unnecessary structure rather than a specific
shape. The recognisable participants across its common presentations are as
follows.

- **The unused abstraction.** An interface, abstract class, or protocol that
  currently has exactly one concrete implementation, introduced to support
  variation that has not materialised.
- **The unused hook.** A method, often with an empty or trivial default body,
  that a base class declares for subclasses to override, where no subclass
  ever overrides it with behaviour that differs from the default.
- **The unused parameter.** A method or constructor argument, frequently a
  loosely typed bag such as a map or an options object, that every current
  caller passes the same value for, usually an empty value or a hardcoded
  default.
- **The unused delegation layer.** A class whose entire body forwards calls to
  another class unchanged, introduced to "allow swapping the implementation
  later" where no second implementation exists.
- **The single caller.** The one real production code path that exercises the
  abstraction, always exactly one, which is the diagnostic signature. Search
  for every implementer of an interface or every override of a base class
  method, and if the count is one where the design implies more than one was
  expected, the smell is present.

## 6. ASCII structure diagram

```
  Speculative shape (as designed, "for future flexibility")

  +----------------------------+          +---------------------+
  |   AbstractNotifier         |          | NotificationStrategy |
  |----------------------------|  uses    |----------------------|
  | # strategy: Strategy       |--------->| + send()             |
  | # preprocess(msg): string  |          +----------+-----------+
  | # postprocess(res): void   |                     ^
  | + notify(ch, to, msg)      |                     | implements
  +--------------+-------------+                     |
                 ^ extends                +-----------------------+
                 |                        |    EmailStrategy      |
  +--------------+-------------+          | (the only one, ever)  |
  |     EmailNotifier          |          +------------------------+
  | # preprocess()  -> passthrough
  | # postprocess() -> empty body
  +----------------------------+

  Actual shape (what the codebase has ever needed)

  +--------------------------------+
  |  notifyByEmail(to, message)    |
  +--------------------------------+

  The abstraction on the left has one caller, one implementer, two
  hook methods that are never overridden with real logic, and zero
  callers of `notify()` with any channel other than "email".
```

## 7. Dynamics

At runtime the speculative and the concrete version behave identically for the
one real case, which is exactly what makes the smell hard to catch from a test
run. Every test passes, because the tests only ever exercise the one caller
that exists.

```
Speculative call path, one real caller, three layers of indirection

  client code
      |
      v  notify("email", "a@x.com", "hi")
  AbstractNotifier.notify()
      |
      |-- preprocess(msg) ---------> EmailNotifier.preprocess()  (passthrough)
      |
      |-- strategy.send(to, msg) --> EmailStrategy.send()        (does the work)
      |
      `-- postprocess(result) -----> EmailNotifier.postprocess() (empty body)

Actual call path, same runtime effect, zero indirection

  client code
      |
      v  notifyByEmail("a@x.com", "hi")
  notifyByEmail()  (does the work directly)
```

The dynamics reveal the cost precisely. The speculative path performs the
identical unit of work, sending one email, through four dispatches, the
abstract `notify`, the `preprocess` hook, the strategy's `send`, and the
`postprocess` hook, where the concrete path performs it through one. Every one
of the three extra dispatches exists to support a variation that, at the point
this trace is taken, has never once varied.

## 8. Implementation variants

Speculative Generality shows up in a handful of recurring shapes across
languages, each idiomatic to how that language expresses extensibility.

- **The one-implementation interface (Java, C#, TypeScript, Go).** An
  interface declared and consumed through dependency injection, with a single
  registered implementation in the container configuration. Common in
  Spring-style dependency injection setups where the interface was added by
  convention, following an "always code to an interface" house rule applied
  without the second implementation the rule assumes will eventually exist.
- **The unused strategy or visitor hierarchy (any object-oriented language).**
  A `Strategy` or `Visitor` interface with one concrete class, frequently
  introduced pre-emptively when a `switch` on a type code would have expressed
  the current single case just as clearly and far more legibly.
- **The parameter bag (Python `**kwargs`, JavaScript/TypeScript options
  objects, Java `Map<String, Object>`).** A catch-all parameter every current
  caller either omits or passes an empty value for, added "so future callers
  have somewhere to put things."
- **The closure or higher-order function as a speculative hook (functional
  languages, JavaScript, Kotlin, Swift, Rust).** A function accepting a
  callback parameter that every current call site passes the same trivial,
  identity-like closure for. This is the functional-language equivalent of
  the unused hook method, and it is common in Rust and Swift precisely because
  those languages make it cheap to pass a closure, which lowers the perceived
  cost of adding one speculatively.
- **The configuration-driven pluggable field (any language with a
  configuration file).** A `type` or `strategy` field in a config schema with
  exactly one legal value in every environment the system has ever run in,
  paired with dispatch logic in code that is dead in every branch but one.
- **The extra layer of indirection (Java, C#).** An interface plus a single
  default implementation plus a factory that always returns that one
  implementation, sometimes called out specifically as "FactoryFactory"
  syndrome in community discussion of over-engineered Java codebases, a
  degenerate case of Factory Method (see the related-patterns entry) applied
  where no second product exists.

## 9. Known production uses

Real, named instances of the smell being observed, criticised, or satirised in
production and reference software, each independently checkable.

- **FizzBuzz Enterprise Edition.** A widely referenced open-source project on
  GitHub deliberately reimplements the trivial FizzBuzz exercise, printing
  "Fizz" for multiples of three and "Buzz" for multiples of five, using a full
  layered enterprise Java architecture. Dependency-injected strategies, an
  abstract factory hierarchy, visitor-pattern number classification, and a
  Spring configuration file, none of which is required for a program whose
  entire logic is two modulo checks. The project's own README describes it as
  demonstrating what FizzBuzz would look like "were it subject to the high
  quality standards of enterprise software", and it is used throughout the
  industry as a teaching artifact specifically for Speculative Generality and
  its sibling smells
  ([github.com/EnterpriseQualityCoding/FizzBuzzEnterpriseEdition](https://github.com/EnterpriseQualityCoding/FizzBuzzEnterpriseEdition),
  verified 2026-08-02).
- **`java.util.Collection`'s optional operations.** The core Java Collections
  Framework interface `Collection` declares mutating methods such as `add`,
  `remove`, and `clear` that its own Javadoc marks explicitly as "(optional
  operation)", stating that "the methods that modify the collection on which
  they operate, are specified to throw `UnsupportedOperationException` if this
  collection does not support the operation"
  ([docs.oracle.com/javase/8/docs/api/java/util/Collection.html](https://docs.oracle.com/javase/8/docs/api/java/util/Collection.html),
  verified 2026-08-02). This is a platform-level instance of the same failure
  mode as Speculative Generality. The interface was generalised to cover
  every conceivable collection shape, including read-only and fixed-size
  variants, by declaring methods that a caller cannot actually rely on being
  implemented, which pushes a runtime discovery burden, catching
  `UnsupportedOperationException`, onto every caller of the general interface
  in exchange for a uniformity that individual collection types do not
  actually deliver on.
- **`System.ICloneable` in the .NET Base Class Library.** Microsoft's own
  current API reference for the `ICloneable` interface states plainly, in the
  "Notes to Implementers" section, that "the `ICloneable` interface simply
  requires that your implementation of the `Clone()` method return a copy of
  the current object instance. It does not specify whether the cloning
  operation performs a deep copy, a shallow copy, or something in between",
  and concludes "we recommend that `ICloneable` not be implemented in public
  APIs"
  ([learn.microsoft.com/en-us/dotnet/api/system.icloneable](https://learn.microsoft.com/en-us/dotnet/api/system.icloneable),
  verified 2026-08-02). The interface was designed for maximal generality, a
  single method meant to express "copy any object of any shape", and the
  platform's own current guidance is that the generality is unusable in
  practice because it specifies nothing about what "copy" actually means for
  a given implementer, the same failure Fowler's catalog names when an
  abstraction is built ahead of a concrete, evidenced need for it.

## 10. Consequences

**Positive.** There are close to none when the smell is genuinely present
rather than deliberate, evidence-based extensibility, and the honest
consequence list for the smell itself is almost entirely negative. The
positive column exists only for the deliberate, non-speculative version of
generality described in dimension 4, where a real second case already exists.

**Negative.**

- Every reader who encounters the unused abstraction spends real time tracing
  it to discover that it has one implementation, one caller, or one legal
  configuration value, time spent understanding structure that carries no
  information about the system's actual behaviour.
- The abstraction becomes an attractive nuisance. Once it exists, the path of
  least resistance for the next developer adding a genuinely new case is to
  conform to the guessed shape rather than to question whether that shape
  fits, even when it does not, because deviating from an existing interface
  looks like more work than implementing it.
- Test coverage of the unused branches, hook overrides, and parameter values
  is either absent, because nobody has a real case to test against, or
  artificial, exercising a code path with a contrived double that proves
  nothing about real behaviour and inflates a coverage percentage without
  inflating real confidence.
- The abstraction increases the number of files, indirections, and levels of
  the call stack a debugger must step through to reach the one line of code
  that does real work, which slows down every debugging session that touches
  that code path, not only the rare one that would have benefited from the
  generality had it ever been used.
- When the real second case eventually arrives, it rarely matches the guessed
  shape exactly, forcing either a distortion of the new requirement to fit the
  old guess or a rework of the abstraction under the time pressure of the new
  feature's deadline, which is frequently worse than building the abstraction
  fresh from two known cases would have been.

## 11. Failure modes and misuse

**Symptom.** An interface, abstract base class, or strategy hierarchy has
exactly one concrete implementer across the entire codebase, discoverable with
a project-wide search for "implements InterfaceName" or "extends
AbstractClassName" returning a single hit.
**Cause.** The abstraction was introduced in anticipation of a second
implementation that has not, and may never, materialise. The author generalised
before the second real case existed to generalise from.
**Fix.** Inline the interface into its single implementation (Fowler's Inline
Class refactoring, or Collapse Hierarchy when the relationship is
inheritance), and reintroduce the seam later, from two real cases, only when a
genuine second implementation is scheduled.

**Symptom.** A method or constructor parameter is present in the signature but
every call site in the codebase passes the identical value for it, often an
empty collection, an empty map, `null`, or a default sentinel.
**Cause.** The parameter was added "for future flexibility" rather than
because a caller today needs to vary it.
**Fix.** Apply Remove Parameter, deleting the argument and hardcoding the one
value every caller currently supplies. Reintroduce the parameter when a second
caller genuinely needs a different value, at which point its correct type and
name are usually clearer than they would have been when guessed in advance.

**Symptom.** A base class declares a method meant as an extension hook, often
with an empty or pass-through default body, and every subclass either does
not override it or overrides it with logic identical to the default.
**Cause.** The hook was added speculatively to support subclass customisation
that has not been requested by any current subclass.
**Fix.** Remove the hook method entirely (Remove Method / Inline Function).
If a subclass eventually needs genuinely different behaviour at that point in
the algorithm, add the hook back at that time, informed by what the real
override actually needs to do, rather than by a guess made before any
subclass existed.

**Symptom.** A class exists purely to forward every call to another class
unchanged, with no logic of its own, introduced under a name suggesting future
swappability such as `PaymentServiceProxy` or `NotificationDelegate`.
**Cause.** A delegation layer was added preemptively "in case we need to swap
the implementation later" with no second implementation ever planned or built.
**Fix.** Inline the delegate directly into its one caller (Inline Class).
Reintroduce a real seam, ideally via constructor injection of an interface,
only once a second implementation is actually being written, at which point
the interface can be extracted mechanically from the two concrete classes that
now exist, which produces a correctly shaped interface instead of a guessed
one.

**Symptom.** A configuration schema field accepts several named values, but
every deployed environment, across every instance the team operates, has only
ever used one of them, and the code paths for the other values are unreachable
in production traffic though present in the source.
**Cause.** The configuration was made pluggable "so that operators could
choose later" without an actual operator ever needing or requesting the
choice.
**Fix.** Collapse the configuration to a fixed constant, delete the dead
branches (Remove Dead Code), and reopen the configuration point only when a
second deployment target genuinely needs a different value, at which point the
two real values in hand make the correct schema obvious rather than guessed.

## 12. Trade-off matrix

Speculative Generality is compared here against the deliberate, evidence-based
generality that dimension 4 describes as legitimate, and against the two
concrete refactoring destinations, Strategy pattern and a bare conditional,
that a team is choosing between when they decide how to structure a variation
point.

| Force | Speculative Generality (guessed, unused) | Deliberate generality (Strategy/Factory Method, evidence-based) | Bare conditional (no abstraction) |
|---|---|---|---|
| Readability for a reader with only the current requirement | Low. The reader must trace an abstraction that turns out to have one branch. | High once two or more real branches exist, the abstraction documents real variation. | High while there is genuinely one case, the conditional, if any, is trivial or absent. |
| Cost to extend when a real second case arrives | High. The guessed shape rarely fits the real second case exactly. | Low. The abstraction was already shaped by at least one prior real case. | Medium. Extending a conditional to a second branch is easy, a third or fourth starts to strain readability. |
| Test coverage achievable honestly | Low. Unused branches cannot be exercised by real behaviour, only by contrived doubles. | High. Every branch has a real caller to write a real test against. | High for a small number of cases, degrades as branches multiply. |
| Debugging step count to reach real logic | High. Extra indirection layers exist purely to route around a variation that never occurs. | Medium. Indirection exists, but each hop corresponds to a real, distinct behaviour. | Low. Logic sits at the call site with no indirection. |
| Risk of the abstraction becoming an attractive nuisance that shapes future requirements incorrectly | High. New requirements get bent to fit the pre-existing guessed shape. | Low. The abstraction already reflects what variation actually looks like. | None. There is no shape to bend a new requirement to. |

## 13. Related and incompatible patterns

Speculative Generality is the pathological, evidence-free version of the
Strategy pattern (see the strategy entry) and of Factory Method (see the
factory-method entry). Both of those patterns are legitimate exactly when a
real, present set of variants justifies the indirection, and become this smell
the moment the variant count regresses to one and stays there. Template Method
(see the template-method entry) is the specific pattern most often degraded
into the unused-hook variant of this smell, because Template Method's entire
mechanism is a base-class algorithm calling subclass-overridable hook steps,
and a hook step nobody ever overrides differently is Speculative Generality
wearing Template Method's structure. The relationship to Dead Code (see the
dead-code entry) is close but distinct. Dead Code is unreachable or unused
code that was once needed and no longer is, while Speculative Generality is
code that was never needed in the first place, though the two frequently
co-occur, since an unused abstraction's unused branches are also, individually,
dead code. Feature Envy (see the feature-envy entry) is largely unrelated in
cause but can appear alongside this smell in the parameter-bag variant, where a
speculative options object encourages a method to reach into fields that
belong to a different concern than the method's own. There is no pattern this
smell is incompatible with in the structural sense. It is compatible with,
meaning it can infect, essentially any pattern that introduces an
abstraction, because the smell is a misapplication of the abstraction
mechanism rather than a conflict with a specific other pattern's invariants.

## 14. Refactoring path in and out

There is no "path in" that a reviewer should endorse. The correct entry point
for real generality is dimension 4's evidence-based path, arriving at Strategy
or Factory Method only once a second and ideally a third real case exist,
following Beck's rule of three. The path out, once Speculative Generality is
identified, follows the same handful of Fowler refactorings regardless of
which variant from dimension 11 is present.

1. Identify every call site and every implementer of the suspect abstraction
   with a project-wide search. If the count of implementers or of distinct
   parameter values passed is exactly one, the abstraction is a candidate.
2. Confirm there is no scheduled, ticketed second case before removing
   anything. A search returning one implementer today does not always mean
   the abstraction is speculative if a second implementation is genuinely
   mid-development on a branch.
3. Apply Inline Class or Collapse Hierarchy to fold the single implementation
   into its interface or base class, removing the abstraction boundary.
4. Apply Remove Parameter to any argument every remaining caller passes an
   identical value for, hardcoding that value at the call site.
5. Apply Remove Method (Inline Function) to any hook method left with an
   empty or pass-through body after step 3, deleting it rather than leaving a
   vestigial override point.
6. Re-run the full test suite. Because the smell's defining property is that
   its removal does not change observable behaviour for the one real case,
   the tests should pass unchanged. A test that breaks indicates the
   abstraction was not, in fact, speculative, and the refactoring should be
   reverted and reconsidered with that evidence in hand.
7. When a genuine second case later arrives, extract the abstraction fresh
   from the two now-concrete implementations rather than resurrecting the
   deleted one, because the two real implementations reveal the shared shape
   more accurately than the original guess did.

## 15. Testing and verification

Speculative Generality is easy to introduce partly because a passing test
suite gives no warning of it. The smell's whole nature is that its extra
branches are never exercised, so a green build says nothing about whether the
abstraction earns its cost. The reliable verification technique is structural
rather than behavioural. Search the codebase for every interface and abstract
class and count implementers. An interface with exactly one implementer, with
no second implementer scheduled, is a positive signal for the smell and
belongs on a review checklist rather than being caught by a unit test. Mutation
testing is unusually effective here in a roundabout way. A mutation testing
tool that flips a conditional or deletes a call inside an unused hook method
and finds that no test fails is directly demonstrating that the hook's
behaviour, whatever it is, is unverified, which is a strong secondary signal
that the hook may be speculative rather than load-bearing. Code coverage
percentage alone is a weak signal and can be actively misleading, because a
contrived test written specifically to exercise the speculative branch
inflates coverage while adding no confidence about real behaviour. Coverage of
a branch is informative only when the caller invoking that branch is a real,
production code path rather than a test double manufactured solely to reach
it. Static analysis of "number of implementers per interface" and "number of
distinct values passed to a parameter across the codebase" are both
mechanically computable and are the checks most worth automating into a
linter or a code review bot for a team that wants to catch this smell before
merge rather than during a later refactoring pass.

## 16. Observability signals

Speculative Generality is a design-time and code-review-time smell rather than
a runtime failure, so it does not surface through application logs, traces, or
production metrics the way a performance or reliability problem would. Nothing
about the abstraction's presence changes latency, error rate, or resource
consumption at runtime in the common case, which is part of why it survives
undetected for so long. The observability signals that do apply live in the
development process rather than in the running system. A repository-level
static check reporting "interfaces with exactly one implementer" or
"parameters where every call site passes an identical literal value", run as
part of a periodic code health report rather than a runtime dashboard, is the
closest equivalent to an observability signal this smell has. Where a
speculative abstraction does have a runtime observability implication is in
exception telemetry. The `java.util.Collection` optional-operations case from
dimension 9 is directly observable at runtime, because a caller invoking an
unsupported optional operation produces an `UnsupportedOperationException` that
shows up in error logs and exception-tracking tools, and a spike in that
specific exception type across a codebase that relies on Collection's optional
operations is a genuine, actionable runtime signal that the interface's
generality has produced a real caller-side failure.

## 17. Security and privacy implications

Speculative Generality carries no privacy implication in the general case. It
does not, by itself, cause personal data to be collected, stored, or
transmitted differently. There is one concrete, well-documented security
implication worth naming plainly rather than inventing a broader concern.
Speculative options bags and pass-through configuration hooks, the
"`Map<String, Object> options`" and similar catch-all parameters described in
dimension 8, widen the attack surface available to a caller in a way a
narrowly typed parameter list does not. Because nothing in the type system
constrains what keys or values a caller can pass, a downstream consumer of the
options bag that later gains a new, unreviewed capability (for example a
logging sink that starts reading an `options["debug"]` flag, or a template
renderer that starts reading `options["template"]`) can turn an innocuous,
unused-today parameter into an unintended injection point the moment a future
maintainer wires a new consumer up to it, precisely because the parameter was
never scoped to the one thing it is actually used for. This is a second,
independent reason beyond the readability cost in dimension 10 to prefer a
narrowly typed parameter over a speculative catch-all. The narrow parameter
cannot be silently repurposed into a security-relevant channel later, because
its type constrains what it can ever mean.

## 18. References

- Martin Fowler, *Refactoring. Improving the Design of Existing Code*,
  Addison-Wesley, 1999, chapter "Bad Smells in Code" (with Kent Beck),
  catalogues Speculative Generality among the twenty-two named smells and its
  companion refactorings Collapse Hierarchy, Inline Class, Inline Function,
  and Remove Parameter.
- Kent Beck, *Extreme Programming Explained. Embrace Change*,
  Addison-Wesley, 1999, describes "You Aren't Gonna Need It" as one of the
  core Extreme Programming practices this smell violates.
- Martin Fowler, "Yagni",
  [martinfowler.com/bliki/Yagni.html](https://martinfowler.com/bliki/Yagni.html),
  verified 2026-08-02. Source for the Jeremy D. Miller quote on unused
  extensibility points, the pricing-abstraction worked example, and the
  explicit scope boundary distinguishing speculative feature-support code
  from legitimate maintainability investment.
- FizzBuzzEnterpriseEdition,
  [github.com/EnterpriseQualityCoding/FizzBuzzEnterpriseEdition](https://github.com/EnterpriseQualityCoding/FizzBuzzEnterpriseEdition),
  verified 2026-08-02. Source for the named production (teaching) artifact
  satirising Speculative Generality applied to a trivial problem.
- Oracle, `java.util.Collection` interface documentation, Java SE 8,
  [docs.oracle.com/javase/8/docs/api/java/util/Collection.html](https://docs.oracle.com/javase/8/docs/api/java/util/Collection.html),
  verified 2026-08-02. Source for the "(optional operation)" wording and the
  `UnsupportedOperationException` contract discussed in dimensions 9 and 16.
- Microsoft, `ICloneable` Interface reference, .NET API documentation,
  [learn.microsoft.com/en-us/dotnet/api/system.icloneable](https://learn.microsoft.com/en-us/dotnet/api/system.icloneable),
  verified 2026-08-02. Source for the "Notes to Implementers" guidance
  recommending against implementing `ICloneable` in public APIs, discussed in
  dimension 9.

## Code examples

Three languages. The "before" sample in each shows the speculative shape, an
abstract notifier built to support multiple channels, preprocessing hooks, and
a pluggable strategy, when the codebase has ever had exactly one channel, one
preprocessing behaviour (a passthrough), and one strategy. The "after" sample
is the refactored result once the speculative structure is removed, following
the path in dimension 14. TypeScript, Python, and Go are used because each
expresses the interface, hook-method, and delegated-strategy variants from
dimension 8 idiomatically, and each was checked with its own toolchain.

### TypeScript, before (checked with `tsc --noEmit --strict`)

```typescript
type NotificationChannel = "email" | "sms" | "push" | "fax" | "telegram" | "carrier-pigeon";

interface NotificationStrategy {
  send(recipient: string, message: string, options: Record<string, unknown>): void;
}

abstract class AbstractNotifier {
  protected abstract strategy: NotificationStrategy;
  protected abstract preprocess(message: string, ctx: Record<string, unknown>): string;
  protected abstract postprocess(result: unknown, ctx: Record<string, unknown>): void;

  notify(channel: NotificationChannel, recipient: string, message: string, ctx: Record<string, unknown> = {}): void {
    const processed = this.preprocess(message, ctx);
    this.strategy.send(recipient, processed, ctx);
    this.postprocess(undefined, ctx);
  }
}

class EmailNotifier extends AbstractNotifier {
  protected strategy: NotificationStrategy = {
    send: (recipient, message) => console.log(`email to ${recipient}: ${message}`),
  };
  protected preprocess(message: string): string {
    return message;
  }
  protected postprocess(): void {}
}

const n = new EmailNotifier();
n.notify("email", "team@example.com", "build is green");
```

`NotificationChannel` names five channels that no caller in the codebase has
ever passed. `preprocess` and `postprocess` are hooks that `EmailNotifier`
overrides with a passthrough and an empty body, meaning neither one does
anything a caller can observe. The `NotificationStrategy` interface has a
single implementer, defined inline, that will never be swapped.

### TypeScript, after

```typescript
function notifyByEmail(recipient: string, message: string): void {
  console.log(`email to ${recipient}: ${message}`);
}

notifyByEmail("team@example.com", "build is green");
```

The refactoring is Inline Class applied to the strategy, Inline Function
applied to the two hooks, and Collapse Hierarchy applied to the notifier
itself. Every line that produced no observable behaviour is gone. When a real
SMS channel is scheduled, the seam is reintroduced then, shaped by two real
implementations instead of a guess.

### Python, before (checked with `python3 -m py_compile`, runs and prints)

```python
from abc import ABC, abstractmethod
from typing import Any


class AbstractNotifier(ABC):
    @abstractmethod
    def preprocess(self, message: str, ctx: dict[str, Any]) -> str: ...

    @abstractmethod
    def send(self, recipient: str, message: str, ctx: dict[str, Any]) -> None: ...

    @abstractmethod
    def postprocess(self, result: Any, ctx: dict[str, Any]) -> None: ...

    def notify(self, channel: str, recipient: str, message: str, ctx: dict[str, Any] | None = None) -> None:
        ctx = ctx or {}
        processed = self.preprocess(message, ctx)
        self.send(recipient, processed, ctx)
        self.postprocess(None, ctx)


class EmailNotifier(AbstractNotifier):
    def preprocess(self, message: str, ctx: dict[str, Any]) -> str:
        return message

    def send(self, recipient: str, message: str, ctx: dict[str, Any]) -> None:
        print(f"email to {recipient}: {message}")

    def postprocess(self, result: Any, ctx: dict[str, Any]) -> None:
        pass


if __name__ == "__main__":
    EmailNotifier().notify("email", "team@example.com", "build is green")
```

The `ctx: dict[str, Any]` parameter threaded through every method is the
parameter-bag variant from dimension 8. It is present in every signature and
populated by exactly zero call sites in the entire codebase.

### Python, after

```python
def notify_by_email(recipient: str, message: str) -> None:
    print(f"email to {recipient}: {message}")


if __name__ == "__main__":
    notify_by_email("team@example.com", "build is green")
```

Remove Parameter deletes `ctx` along with the abstract class it threaded
through. If a real second channel later needs contextual data, the specific
data it needs, not an untyped catch-all, is added to a narrow, concrete
function signature.

### Go, before (checked with `go vet`, runs and prints)

```go
package main

import "fmt"

type Context map[string]any

type NotificationStrategy interface {
	Send(recipient, message string, ctx Context)
}

type Notifier struct {
	Strategy    NotificationStrategy
	Preprocess  func(message string, ctx Context) string
	Postprocess func(result any, ctx Context)
}

func (n *Notifier) Notify(channel, recipient, message string, ctx Context) {
	processed := n.Preprocess(message, ctx)
	n.Strategy.Send(recipient, processed, ctx)
	n.Postprocess(nil, ctx)
}

type emailStrategy struct{}

func (emailStrategy) Send(recipient, message string, ctx Context) {
	fmt.Printf("email to %s: %s\n", recipient, message)
}

func main() {
	n := &Notifier{
		Strategy:    emailStrategy{},
		Preprocess:  func(message string, ctx Context) string { return message },
		Postprocess: func(result any, ctx Context) {},
	}
	n.Notify("email", "team@example.com", "build is green", Context{})
}
```

Go's idiom for a speculative hook is the closure field rather than a subclass
override, `Preprocess` and `Postprocess` here, but the failure is identical.
`main` is the only caller in this codebase, and both closures it supplies do
nothing.

### Go, after

```go
package main

import "fmt"

func notifyByEmail(recipient, message string) {
	fmt.Printf("email to %s: %s\n", recipient, message)
}

func main() {
	notifyByEmail("team@example.com", "build is green")
}
```

Java, Rust, and Swift are not shown here for length. In Java the same before
shape is idiomatic as an abstract class with `protected` hook methods, closely
mirroring the Python sample. In Rust and Swift the same shape typically
appears as a protocol or trait with a single conforming type plus a closure
parameter every call site supplies the identity closure for, closely mirroring
the Go sample. All three were compiled or run locally as part of authoring
this entry. The TypeScript samples were checked with `npx tsc --noEmit
--strict`, the Python samples were checked with `python3 -m py_compile` and
executed directly, and the Go samples were checked with `go vet` and executed
directly.
