---
name: Dummy
slug: dummy
family: 14-testing
category: Test Double
aliases: [Dummy Object, Placeholder Object, Null Argument]
first_described: "Meszaros 2007"
maturity: canonical
related: [stub, fake-object, mock-object, spy, dependency-injection, null-object]
incompatible_with: []
verified: 2026-08-02
---

# Dummy

## 1. Name, aliases, and lineage

The canonical name is Dummy, sometimes written Dummy Object. It is one of five
test double roles catalogued by Gerard Meszaros in *xUnit Test Patterns.
Refactoring Test Code*, Addison-Wesley, 2007. Meszaros coined the umbrella term
Test Double for any object that stands in for a real dependency during a test,
and split the umbrella into five specific roles by what the object does once it
is standing in. Dummy is the simplest of the five.

Martin Fowler summarized Meszaros's taxonomy in his widely cited article on the
topic, and gives the plainest one line definition available online. "Dummy
objects are passed around but never actually used," he writes, adding that in
practice they exist to fill out a parameter list nothing else. Fowler also
credits Meszaros directly for developing this vocabulary while writing a book
that captured patterns across many xUnit frameworks, precisely because the
testing community before that point used "mock" as a catch all term for every
kind of test double, which made technical conversation about tests imprecise
(Martin Fowler, "TestDouble", https://martinfowler.com/bliki/TestDouble.html,
verified 2026-08-02).

The alias Placeholder Object appears in code review discussion and in some
testing guides as a plain English restatement of the same idea, an object whose
only job is to occupy a slot. Null Argument is used informally when the dummy's
sole purpose is to satisfy a non-nullable or non-optional parameter type, most
often in statically typed languages where passing an actual null would either
fail to compile or trigger a null-check exception the test does not care about.
Neither alias appears in Meszaros's own vocabulary, they are community
shorthand, and this entry treats them as synonyms of Dummy rather than as
separate patterns.

It is worth being precise about what Dummy is not, because the five Meszaros
roles are frequently used interchangeably in casual conversation and that
imprecision causes real design mistakes, covered in dimension 11 below. A Dummy
carries no logic and no state that the test inspects. The moment a test double
starts returning canned values that the code under test reads and branches on,
it has become a Stub. The moment the test double records calls so the test can
assert on them, it has become a Spy or a Mock. The moment the test double
contains a working, simplified implementation of the real dependency's
behavior, it has become a Fake. Dummy is the null hypothesis of test doubles,
present only because the method signature demands an argument.

## 2. Problem and context

A constructor, a factory function, or a method signature requires an argument
of a particular type, but the code path being exercised by a specific test does
not use that argument at all. This happens constantly in object-oriented code
with multi-parameter constructors, in dependency-injection containers that wire
every collaborator regardless of which ones a given test scenario touches, and
in language communities where nullable types are either disallowed or actively
discouraged.

The concrete situation looks like this. A class `OrderProcessor` takes a
`PaymentGateway`, an `InventoryService`, an `AuditLogger`, and a
`NotificationService` in its constructor. A test wants to verify that
`OrderProcessor.validate(order)` rejects an order with a negative quantity.
That single assertion never touches payment, inventory, the audit log, or
notifications. Without some object to satisfy each of those four constructor
parameters, the test cannot even construct the object under test, regardless of
whether the test logic needs those collaborators.

The context in which this problem arises is any codebase where object
construction is coupled to a full set of dependencies rather than to only the
dependencies a particular operation exercises. It is amplified by strict typing,
because a language that rejects `null` for a non-optional reference type forces
the caller to supply something real, and it is amplified by constructor
injection style dependency injection, where the container assembles every
collaborator up front rather than lazily. It is diminished, but not eliminated,
by languages and frameworks that support optional or default parameters,
because a default value is itself frequently a Dummy in disguise.

## 3. Forces

This dimension is largely engineering judgement about which pressures a
Dummy trades against which, drawn from the practice literature and from the
design of the mocking frameworks cited in dimension 9, not a single sourced
claim.

Test isolation pulls toward supplying every dependency, even unused ones, so
the constructor's real shape is exercised and the test does not silently
depend on an unusual construction path that production code never takes.
Test readability pulls the opposite direction, toward supplying as little as
possible, because every unused parameter that appears in a test's arrange
section is a piece of noise the reader must mentally discard while looking for
the parameters that actually matter to the assertion.

Coupling to the constructor signature is a real cost. A Dummy exists because
the signature requires it, not because the test cares about it, so every time
the signature changes, every test file that constructed a Dummy for that
parameter must change too, even though nothing about the test's actual
behavior changed. This is the most common complaint raised against
constructor-heavy dependency injection in large test suites, and it is the
direct motivation for the object mother and test data builder patterns that
frequently sit next to Dummy usage in mature test suites, discussed further in
dimension 13.

Safety against accidental use is another force. A Dummy that happens to behave
plausibly if it is accidentally invoked can mask a bug where the test exercises
a code path it did not intend to exercise. A Dummy that throws or crashes
loudly on any interaction converts a silent correctness gap into a visible test
failure, at the cost of a slightly more elaborate dummy implementation than the
simplest possible one. Cost of authorship favors the cheapest possible object,
often the language's own `null`, a zero value, or an auto-generated mock with
no configuration, because hand rolling a purpose-built dummy class for every
unused dependency does not scale across a large suite.

Operability and cognitive load matter at the suite level rather than the single
test level. A codebase with a consistent, named convention for its dummies,
whether that is a shared `DummyLogger` type or a single call to a mocking
framework's default constructor, is easier for a new contributor to read than a
codebase where every test author invents their own ad hoc placeholder.

## 4. Applicability and non-applicability

Reach for Dummy when a required parameter is genuinely irrelevant to the
behavior a specific test verifies, and the only reason it exists in the call is
that the signature demands it. Reach for it when constructing the object under
test would otherwise be impossible, most commonly with constructor injection in
statically typed languages that reject null for non-nullable references. Reach
for it when the test's readability benefits from a name that signals "this
argument does not matter here", which a well-named dummy variable does far
better than a real, correctly behaving collaborator would.

Reach for it as the default choice whenever a mocking framework's plain
`mock()` or `Mock()` call with zero configuration is available and idiomatic in
the language, because in that case a Dummy costs one line and carries no
maintenance burden of its own, only the maintenance burden shared by every
caller of the constructor.

Do not reach for it when the test does exercise the collaborator's behavior,
even indirectly. If the code under test calls a method on the dependency and
the return value influences a branch the test cares about, the object needed is
a Stub, not a Dummy, and calling it a Dummy while quietly relying on its return
value is the most common misuse covered in dimension 11.

Do not reach for it when the test needs to assert that the collaborator was
called, with what arguments, or how many times. That need calls for a Spy or a
Mock in the Meszaros sense, an object that records interaction so the test can
verify it, and using a bare Dummy there produces a test that looks like it
verifies behavior but actually verifies nothing, because nobody inspects the
dummy afterward.

Do not reach for it when the dependency has real invariants that the
system under test relies on holding, such as a repository that must actually
persist and retrieve an entity across two calls within the same test. That
calls for a Fake, an in-memory but functionally correct implementation, because
a Dummy that returns garbage or throws on every call will break the test the
moment the code under test tries to use it for anything beyond satisfying the
type checker.

Do not reach for it as a substitute for redesigning a constructor that has
grown too many parameters. If nearly every test for a class needs to supply
three or four dummy dependencies only to construct the object, that volume of
dummies is itself a signal, covered further in dimension 11, that the class
violates the single responsibility principle or that the constructor should
accept a smaller cohesive interface rather than the full set of concrete
collaborators.

## 5. Structure

The participants in Dummy usage are minimal, which is the entire point of the
pattern.

Test participant. The test method that constructs the system under test,
supplying the dummy for the parameter it does not care about and a real value,
a Stub, or a Fake for whichever parameter the assertion actually depends on.

System under test. The class, function, or module being exercised by the
test, whose constructor or method signature declares a parameter of a
dependency type that the specific test scenario does not exercise.

Dummy object. An instance of the dependency's type, interface, or
protocol, whose implementation is either entirely empty, throws on any
interaction, or is an unconfigured instance of a general purpose test double
library object. The dummy satisfies the type system and the runtime
construction requirement, and nothing else.

There is no fourth participant. Unlike a Mock or a Spy there is no verification
step against the dummy at the end of the test, and unlike a Fake there is no
internal state the dummy maintains across calls. The relationship between the
system under test and the dummy is purely structural, satisfying the type
contract, never behavioral.

## 6. ASCII structure diagram

```
+------------------------------+
| Test method                  |
| constructs SUT with          |
|   realArg  (matters)         |
|   dummyArg (does not matter) |
+------------------------------+
     | passes both args
     v
+------------------------------------+
| System under test (OrderProcessor) |
+------------------------------------+
     | calls realArg
     v
+--------------------------------------+
| Real / Stub / Fake, behavior matters |
+--------------------------------------+

The same SUT also calls dummyArg on its constructor
interface, but this test path never actually invokes it:

+---------------------------------------+
| Dummy, no behavior, or throws if used |
+---------------------------------------+

Both Real / Stub / Fake and Dummy implement the same
Dependency interface, e.g. PaymentGateway or Logger.
```

## 7. Dynamics

```
Test setup
  1. Test constructs dummyArg
        - either  new DummyLogger()        (hand written, no-op or throwing)
        - or      mock(Logger.class)        (framework default, unconfigured)
  2. Test constructs realArg (a real object, a Stub, or a Fake, per the case)
  3. Test constructs SUT, passing dummyArg and realArg to the constructor

Exercise
  4. Test calls the method under test on SUT
  5. SUT's internal code path for this scenario reads/branches on realArg
  6. SUT's internal code path for this scenario never invokes dummyArg
        (if it did, the test has picked the wrong double, see dimension 11)

Verify
  7. Test asserts on the return value or observable state produced via realArg
  8. Test does NOT assert anything about dummyArg
        (there is nothing to assert, a Dummy records no interaction)

Teardown
  9. No special teardown, the dummy holds no resources and no state
```

The defining property visible in this trace is step 6. A correctly used Dummy
is never invoked during the exercise phase of the specific test that supplied
it. If a code review or a later refactor causes the system under test to start
calling the dummy, the right response is to change the double supplied at that
call site to a Stub, Fake, Spy, or Mock as appropriate, not to add behavior to
the Dummy itself, because adding behavior to a Dummy quietly turns it into a
different pattern under the same name, which then misleads every other reader
who sees "dummy" in the variable name and assumes it is inert.

## 8. Implementation variants

Language null, where the type system allows it. In dynamically typed
languages, and in statically typed languages with genuinely optional or
nullable reference parameters, passing the language's own null or None value is
the cheapest possible Dummy. Python's `None`, JavaScript's `null` or
`undefined`, and Go's untyped `nil` for an interface parameter all serve this
role directly with zero additional code, provided the code under test truly
never dereferences that parameter along the tested path.

Hand written empty class or struct. In statically typed languages that
reject null for non-nullable types, or where the team wants a self-documenting
name in stack traces, a small dedicated type such as `DummyPaymentGateway`
implementing the required interface with empty method bodies, or bodies that
throw `NotImplementedException` or its language equivalent, is the traditional
approach. The throwing variant is strictly safer, covered further in dimension
11, because a silent empty body can mask an accidental invocation, while a
throwing body converts that accidental invocation into an immediate, loud test
failure.

Framework auto-generated mock, unconfigured. In languages with a mature
reflection-based or interface-based mocking library, calling the library's
plain construction function with zero stubbing, for example Mockito's
`mock(PaymentGateway.class)` in Java, `unittest.mock.Mock()` in Python with no
`side_effect` or `return_value` set, or gMock's `NiceMock<MockFoo>` in C++,
produces an object that satisfies the type and returns default or null-like
values from any method that happens to be called, without the test author
writing a bespoke class. This is by far the most common variant in modern test
suites because the library already exists in the project for other test
doubles, so reusing it for the Dummy role costs nothing extra.

Zero value of a value type. In languages where the dependency parameter is
a struct or value type rather than an interface, the language's zero value,
Go's zero-valued struct, Rust's `Default::default()`, or a record with every
field set to its type's default, plays the Dummy role, provided the code under
test on the tested path never reads a field that would need a real value.

Named constant sentinel for primitive parameters. When the unused parameter
is a primitive rather than a collaborator object, for example an unused
`correlationId` string parameter, teams frequently use an obviously fake
literal such as `"unused"`, `"n/a"`, or a magic number like `-1`, chosen
specifically so that if the value does leak into an assertion failure message
or a log line, the reader immediately recognizes it as a placeholder rather
than mistaking it for real data.

## 9. Known production uses

Mockito, the most widely used mocking framework on the JVM, ships exactly this
behavior as its default. Calling `mock()` on a class or interface and never
stubbing a particular method causes that method, if invoked, to return `null`
or a type appropriate default rather than throwing, which the project's own
documentation demonstrates directly with the example that calling an unstubbed
`get(999)` on a mocked list "prints null because get(999) was not stubbed"
(Mockito project site, https://site.mockito.org/, verified 2026-08-02). Java
codebases across the community use exactly this pattern, an unstubbed
`mock(SomeDependency.class)`, as the idiomatic Dummy whenever a constructor
requires a collaborator a given test does not exercise.

Python's standard library `unittest.mock` module documents `Mock` explicitly as
a general purpose replacement object that "creates attributes as new mocks when
you access them" and is designed to be usable anywhere a real object of an
unknown shape is required, including simply as a placeholder argument that a
function or constructor demands but a given test path never touches (Python
documentation, `unittest.mock`,
https://docs.python.org/3/library/unittest.mock.html, verified 2026-08-02). The
module is part of the standard library shipped with CPython since Python 3.3,
and is the de facto standard Dummy and general test double mechanism across
Python test suites, used directly by pytest based suites without any third
party dependency.

Google's C++ mocking framework, googletest's gMock component, provides
`NiceMock<MockFoo>` specifically to suppress the warnings that an unstubbed,
uninteresting method call would otherwise produce, and its cookbook documents
the underlying design directly, stating that "by default, an uninteresting call
is not an error" and recommending `ON_CALL` rather than `EXPECT_CALL` for
collaborators the test is not actually verifying (Google, "gMock Cookbook",
https://google.github.io/googletest/gmock_cook_book.html, verified
2026-08-02). This is the C++ world's equivalent of an unconfigured Java or
Python mock playing the Dummy role, wrapped in a named type specifically so
that a reader of the test can see at the construction site that the object is
present only to avoid noise, not to be verified.

By contrast, Go's widely used `testify/mock` package is documented as panicking
when a method is called without a matching `.On().Return()` expectation having
been registered first, per its own package documentation on the method
`Called()` (`pkg.go.dev/github.com/stretchr/testify/mock`, verified
2026-08-02). This makes `testify/mock` unsuitable, by design, as a source of
Dummy objects on its own, and Go codebases that need a true Dummy typically
either pass an untyped `nil` for an interface parameter, when the interface
permits a nil receiver on the methods actually called, or hand roll a small
struct with empty method bodies implementing the interface, precisely because
Go's most widely used mocking library deliberately favors strict, fail loud
behavior over the silent default-return behavior Mockito and `unittest.mock`
provide.

## 10. Consequences

Positive. A Dummy removes the coupling between a test's assertion and every
collaborator the code under test does not exercise for that scenario, so a
change to an unrelated collaborator's interface or behavior does not force an
unrelated test to change its logic, only, at worst, its dummy construction
line. It keeps constructors and factory functions honest about their real
dependency shape rather than pushing teams toward optional parameters or
service locator patterns purely to avoid supplying test doubles. It is the
cheapest possible test double to author, frequently a single line via a mocking
framework, which keeps arrange sections of tests short for the large fraction
of dependencies a given scenario does not care about. When implemented as a
throwing stand in rather than a silent no-op, it converts an incorrect
assumption about which code path a test exercises into an immediate, specific
test failure rather than a silent pass that happens to be right for the wrong
reason.

Negative. A Dummy that silently accepts any call and returns a default
value, rather than throwing, can mask a real bug where the code under test
unexpectedly does invoke the dependency, producing a green test that verified
less than the author believed. A test suite with heavy constructor coupling and
many unused parameters accumulates a large volume of dummy construction
boilerplate across its test files, and every constructor signature change then
requires updating that boilerplate everywhere, even in tests whose actual
assertions did not change, which is the most frequently cited cost of
constructor injection combined with example based testing rather than
parameterized object mothers. Overuse of Dummy as a lazy default, reaching for
it even when the collaborator's behavior does matter to the scenario, produces
tests that appear to pass while exercising a code path that never runs in
production, because the dummy silently returned a default value the real
dependency would never actually return.

## 11. Failure modes and misuse

Symptom. A test passes, but a later refactor that changes the code under
test to actually call the collaborator that was supplied as a dummy causes a
`NullPointerException`, a `NotImplementedException`, or an unhelpful default
value to flow into an assertion, and the failure message gives no hint that the
root cause is a mismatched test double role. Cause. The test author called
an object a Dummy and treated it as inert, but the code under test's behavior
changed to depend on it, and nothing in the test's structure would have caught
that dependency at the moment it was introduced, because a passive, silently
returning Dummy does not fail differently whether it is called zero times or a
hundred times. Fix. Prefer dummies that throw on any interaction rather
than dummies that silently return a default, whenever the language and
framework make that convenient, specifically so that a future accidental
invocation converts into an immediate, loud, specific failure at the exact call
site rather than a confusing downstream symptom. Where the framework's default
is a silently returning mock, as with Mockito's default answer, consider
switching to `mock(Type.class, RETURNS_SMART_NULLS)` or an equivalent strict
answer strategy for parameters the team wants to guarantee are truly unused.

Symptom. A code reviewer sees a test's arrange section supply four or five
constructor arguments named `dummyX`, and the test's assertion only concerns
one of them, and this shape repeats across dozens of tests for the same class.
Cause. The class under test has a constructor with too many
responsibilities bundled into one type, so almost every unit test for it must
manufacture dummies for the collaborators that scenario does not touch, which
is a design smell in the production code surfacing through the test suite
rather than a problem with the Dummy pattern itself. Fix. Treat a high
density of dummy construction as a signal to split the class along its actual
responsibilities, or to introduce a shared test object mother or builder that
centralizes the boilerplate of constructing a fully wired instance with
sensible defaults, so that individual tests override only the one or two
arguments that matter to that scenario, per dimension 14 below.

Symptom. A test is labeled as verifying that a notification is sent, its
arrange section constructs a `mock(NotificationService.class)`, but the
assertion section never calls `verify()` on it, only asserts on an unrelated
return value, and the test would pass identically whether or not the
notification code was ever called or even deleted entirely. Cause. The test
author reached for a Mock construction call out of habit, or copied it from a
neighboring test, but never actually used the object in either an interaction
verification sense (Mock or Spy) or a state sense (Stub), so despite being
constructed with a mocking library it is functioning exactly as a Dummy while
being presented to the reader, through its variable name and its test's stated
purpose, as if it were verifying real behavior. Fix. Either add the missing
`verify()` call if the notification behavior genuinely matters to this test, or
rename the variable to signal it is an unused Dummy and remove the misleading
implication that this test protects notification behavior, because a
notification bug will ship silently past a test suite that looks like it
covers notifications but structurally does not.

## 12. Trade-off matrix

| Force | Dummy | Stub | Fake | Mock/Spy |
|---|---|---|---|---|
| Authoring cost | Lowest, often one line or the language's null | Low to moderate, must define canned return values | Highest, requires a working simplified implementation | Moderate, requires configuring expectations |
| Test readability signal | Signals it is irrelevant here | Signals this input drives the behavior under test | Signals this dependency's real behavior must stay correct across calls | Signals the interaction itself is what is being verified |
| Safety against silent bugs | Low if silent, high if it throws on use | High, wrong stubbed value fails the assertion directly | High, incorrect internal state surfaces as a wrong observed result | High, missing or extra calls fail verification directly |
| Coupling to collaborator's real behavior | None | Loose, only the specific return value is coupled | Tight, must track the real dependency's contract over time | Loose to moderate, coupled to the call signature only |
| Correct use when interaction matters | Wrong choice, use Mock/Spy | Wrong choice if the caller inspects call count or arguments | Acceptable but heavier than needed | Correct choice |
| Correct use when only a return value matters | Wrong choice, use Stub | Correct choice | Acceptable but heavier than needed | Wrong choice, obscures the real intent behind interaction verification |

## 13. Related and incompatible patterns

Dummy sits beside the other four Meszaros test double roles as the simplest
member of the same family, and the boundary between Dummy and Stub is the one
most frequently crossed by accident, covered in dimension 11. A Dummy that
starts returning a value the code under test reads has become a Stub without
anyone deciding that on purpose, and the fix is either to accept the promotion
explicitly and rename the variable, or to remove the read from the code under
test if it was genuinely unnecessary.

Dummy composes naturally with the Test Data Builder pattern and with the Object
Mother pattern, both of which centralize the construction of a fully wired,
sensible-default instance of a complex object graph so that individual tests
need only override the one or two fields or collaborators their scenario
actually cares about, letting the builder or mother silently supply dummies or
reasonable defaults for everything else. This combination directly addresses
the constructor-boilerplate cost identified as the primary negative
consequence in dimension 10.

Dependency Injection, whether constructor based or setter based, is the
architectural precondition that makes Dummy necessary in the first place. A
system that resolves its own collaborators internally, through a static
service locator, a singleton, or direct instantiation, cannot accept a
test-supplied Dummy at all, because there is no injection point for the test to
use, which is one of the standard arguments in favor of constructor injection
over service location for testability, independent of the Dummy pattern
specifically.

Null Object is a related but distinct pattern from a different catalog family,
described by Bobby Woolf in the Pattern Languages of Program Design series as a
production design pattern, not a testing pattern, where a type implements a
"do nothing" version of an interface so that production callers do not need to
null-check before calling it. A Null Object and a Dummy can look identical in
source code, an empty implementation of an interface, but they exist for
opposite reasons. A Null Object is shipped to production to eliminate null
checks in real code paths. A Dummy exists only inside test code to satisfy a
constructor the test does not otherwise care about, and shipping a
test-oriented Dummy into production code, or reusing a production Null Object
as a test's Dummy without checking that its behavior is actually safe for the
test's code path, is a common source of the silent-bug failure mode in
dimension 11.

Dummy is not incompatible with any other pattern in the sense the schema
defines, because it has no state and no verified interaction to conflict with
anything else in the object graph. It simply stops being useful, and should be
replaced, the moment a test's requirements grow to include reading a return
value, verifying an interaction, or depending on state across calls.

## 14. Refactoring path in and out

Introducing a Dummy. Start from a test that fails to compile, or fails at
construction time, because a constructor or function signature demands an
argument the specific scenario does not use. Identify the smallest object that
satisfies the required type. If the language's null or the type's zero value is
acceptable along the code path under test, use it directly and stop, this is
the cheapest and most transparent option. If null is not acceptable, either
because the type is non-nullable or because a call on the object could occur
unexpectedly, construct the smallest possible stand in, either the project's
existing mocking library called with zero configuration, or a small hand
written type whose methods throw. Name the local variable or parameter with a
`dummy` prefix so a future reader immediately understands its role without
needing to inspect its implementation. If several tests in the same file or
class repeat the same dummy construction, extract it into a shared test helper
or a builder default rather than repeating the construction inline in every
test method.

Removing a Dummy. A Dummy should be removed, or more precisely promoted,
the moment the code under test starts to actually depend on the collaborator
along the tested path. The signal is usually a test failure, most often the
throwing kind described in dimension 8 and 11, immediately after a change to
production code. At that point the correct refactor is to replace the Dummy at
that specific call site with the double whose role actually matches the new
requirement, a Stub if only a return value now matters, a Fake if state across
calls now matters, or a Mock or Spy if the interaction itself now needs
verification, and to leave the Dummy in place at every other call site where
the collaborator genuinely remains unused. A Dummy is also removed, in the
simpler sense of deleted entirely, whenever a constructor is refactored to take
fewer parameters, which is frequently the better long term fix identified in
dimension 11 for a class whose test suite is filled mostly with dummy
construction boilerplate.

## 15. Testing and verification

Testing code that itself supplies a Dummy is, in the ordinary case, no
different from testing any other code, because the whole design intent of a
Dummy is that it plays no active role in the scenario. The one thing worth
verifying, and worth codifying as a lightweight team convention rather than a
formal test, is that a throwing style Dummy actually throws with a clear,
specific message identifying which method was unexpectedly called and on which
type, so that when it does fire during a later refactor the failure is
immediately diagnosable rather than presenting as a generic exception several
stack frames removed from the real cause.

A useful technique specific to Dummy, absent from the other test double roles,
is a periodic or CI-time audit of dummy usage across a suite. The audit
searches for `mock(` or `Mock()` construction calls that are never followed,
anywhere in the same test method, by either a `when`, `stub`, or
`return_value` configuration or a `verify` or `assert_called` check. Any hit is
either a legitimate Dummy, which is fine, or an accidental Dummy standing in
for a Stub or a Mock the author forgot to finish configuring, which is the
misuse pattern described as the third failure mode in dimension 11. This audit
is mechanical enough to script and several teams run it as a lint rule against
their test suite rather than relying on code review alone to catch it.

Property based and mutation testing interact with Dummy usage in one specific
way worth naming. A mutation testing tool that flips a conditional or removes a
call inside the code under test, and finds that no test in the suite fails as a
result, may be revealing that the parameter the mutated code touches was
supplied as a silently returning Dummy across every test that exercises that
code path, rather than revealing a real gap in test coverage of the
assertion logic itself. Distinguishing those two causes when reading a
mutation testing report requires checking whether the mutated line touches a
parameter that was deliberately passed as a Dummy for that scenario.

## 16. Observability signals

This dimension is analytical, reasoned from the pattern's structure rather
than sourced to a specific document, because Dummy is a test-time construct
with no runtime production presence to observe directly.

Dummy itself produces no production observability signal, because by
definition it exists only inside test code and is never deployed. The signal
worth watching lives in the test suite's own metadata rather than in a running
system. A CI pipeline that tracks code coverage per test can flag a test whose
name and stated intent suggest it covers a particular collaborator's behavior,
but whose coverage report shows the collaborator's real implementation was
never on the call stack for that test, because a Dummy or an unconfigured mock
stood in its place. A team that runs mutation testing gets a more direct
signal, described in dimension 15, where surviving mutants inside a
dependency's interaction code correlate strongly with test scenarios that
supplied a Dummy for that dependency rather than a Stub, Fake, Spy, or Mock.
At the review level, the healthiest signal is simply naming discipline, every
dummy variable actually prefixed or suffixed as a dummy, so that a reviewer
scanning a diff can immediately separate the collaborators a test cares about
from the ones it does not, without reading the collaborator's implementation.

## 17. Security and privacy implications

Dummy carries a narrow but real security-adjacent implication worth stating
plainly rather than inventing a larger concern than exists. Because a Dummy is
frequently the fastest way to satisfy a constructor parameter, teams under time
pressure sometimes reach for a Dummy to stand in for a security relevant
collaborator, an authorization checker, a rate limiter, or an audit logger,
specifically because doing so lets a test compile and pass quickly, without the
author consciously deciding that the security behavior does not matter to that
scenario. If that collaborator's real behavior does matter, even indirectly, to
whether the system under test is safe, a Dummy standing in for it means the
test suite provides zero coverage of that safety property, which is a coverage
gap rather than a vulnerability in the pattern itself, but one that is easy to
introduce silently precisely because Dummy is the cheapest and most tempting
choice under deadline pressure. There is no privacy implication distinct from
this general point, because a Dummy holds no state and processes no data by
design, so it cannot itself leak, log, or mishandle anything the test supplies
to it, unless it has been miswritten to do so, at which point it has already
stopped being a true Dummy in the sense this entry defines.

## 18. References

1. Gerard Meszaros, *xUnit Test Patterns. Refactoring Test Code*,
   Addison-Wesley, 2007. Source of the Test Double taxonomy and the Dummy,
   Stub, Fake, Spy, and Mock role split. Cited via secondary summary below, as
   the primary xunitpatterns.com companion site returned a connection error
   during verification on 2026-08-02 and could not be independently confirmed
   at that time.
2. Martin Fowler, "TestDouble",
   https://martinfowler.com/bliki/TestDouble.html, verified 2026-08-02.
   Definition of Dummy quoted in full in dimension 1 above, and attribution
   of the taxonomy to Gerard Meszaros.
3. Mockito project, official site, https://site.mockito.org/, verified
   2026-08-02. Documents the default unstubbed-method behavior used as the
   basis for Mockito's role as a Dummy source in Java test suites.
4. Python Software Foundation, "unittest.mock",
   https://docs.python.org/3/library/unittest.mock.html, verified 2026-08-02.
   Documents `Mock` as a general purpose replacement object suitable as a
   placeholder argument.
5. Google, "gMock Cookbook",
   https://google.github.io/googletest/gmock_cook_book.html, verified
   2026-08-02. Documents `NiceMock` and the "uninteresting call is not an
   error" default, the mechanism C++ test suites use for Dummy-role objects.
6. Stretchr, `testify/mock` package documentation,
   https://pkg.go.dev/github.com/stretchr/testify/mock, verified 2026-08-02.
   Documents the panic-on-unexpected-call behavior that makes `testify/mock`
   unsuitable, by design, as a silent Dummy source, cited by contrast in
   dimension 9.
7. Bobby Woolf, "Null Object", in Robert Martin, Dirk Riehle, Frank Buschmann
   (eds.), *Pattern Languages of Program Design 3*, Addison-Wesley, 1997.
   Source of the Null Object pattern discussed in dimension 13 as a related
   but distinct, production-oriented pattern frequently confused with Dummy.

## Code examples

The three examples below all model the same scenario, an `OrderProcessor`
whose constructor requires a `PaymentGateway`, an `InventoryService`, and an
`AuditLogger`, tested by a single scenario that only cares about quantity
validation and never touches payment or inventory. The `AuditLogger` dummy is
written to throw on use, so an accidental future invocation fails loudly
rather than passing silently, per the fix recommended in dimension 11.

### TypeScript

```typescript
interface PaymentGateway {
  charge(amount: number): boolean;
}
interface InventoryService {
  reserve(sku: string, qty: number): boolean;
}
interface AuditLogger {
  log(event: string): void;
}

class OrderProcessor {
  constructor(
    private payments: PaymentGateway,
    private inventory: InventoryService,
    private audit: AuditLogger
  ) {}

  validate(quantity: number): string | null {
    if (quantity <= 0) {
      return "quantity must be positive";
    }
    return null;
  }
}

class ThrowingDummyLogger implements AuditLogger {
  log(_event: string): void {
    throw new Error("dummyAudit was invoked but validate() should never call it");
  }
}

function testRejectsNegativeQuantity(): void {
  const dummyPayments: PaymentGateway = { charge: () => {
    throw new Error("dummyPayments was invoked unexpectedly");
  }};
  const dummyInventory: InventoryService = { reserve: () => {
    throw new Error("dummyInventory was invoked unexpectedly");
  }};
  const dummyAudit = new ThrowingDummyLogger();

  const processor = new OrderProcessor(dummyPayments, dummyInventory, dummyAudit);
  const result = processor.validate(-3);

  if (result !== "quantity must be positive") {
    throw new Error(`expected rejection message, got ${result}`);
  }
  console.log("PASS - negative quantity rejected without touching any dummy");
}

testRejectsNegativeQuantity();
```

### Python

```python
from dataclasses import dataclass


class PaymentGateway:
    def charge(self, amount: float) -> bool:
        raise NotImplementedError


class InventoryService:
    def reserve(self, sku: str, qty: int) -> bool:
        raise NotImplementedError


class AuditLogger:
    def log(self, event: str) -> None:
        raise NotImplementedError


@dataclass
class OrderProcessor:
    payments: PaymentGateway
    inventory: InventoryService
    audit: AuditLogger

    def validate(self, quantity: int):
        if quantity <= 0:
            return "quantity must be positive"
        return None


class ThrowingDummyPayments(PaymentGateway):
    def charge(self, amount: float) -> bool:
        raise AssertionError("dummy payments gateway was invoked unexpectedly")


class ThrowingDummyInventory(InventoryService):
    def reserve(self, sku: str, qty: int) -> bool:
        raise AssertionError("dummy inventory service was invoked unexpectedly")


class ThrowingDummyAudit(AuditLogger):
    def log(self, event: str) -> None:
        raise AssertionError("dummy audit logger was invoked unexpectedly")


def test_rejects_negative_quantity():
    processor = OrderProcessor(
        payments=ThrowingDummyPayments(),
        inventory=ThrowingDummyInventory(),
        audit=ThrowingDummyAudit(),
    )
    result = processor.validate(-3)
    assert result == "quantity must be positive", f"unexpected result: {result}"
    print("PASS - negative quantity rejected without touching any dummy")


if __name__ == "__main__":
    test_rejects_negative_quantity()
```

### Go

```go
package main

import "fmt"

type PaymentGateway interface {
	Charge(amount float64) bool
}

type InventoryService interface {
	Reserve(sku string, qty int) bool
}

type AuditLogger interface {
	Log(event string)
}

type OrderProcessor struct {
	payments  PaymentGateway
	inventory InventoryService
	audit     AuditLogger
}

func (p *OrderProcessor) Validate(quantity int) string {
	if quantity <= 0 {
		return "quantity must be positive"
	}
	return ""
}

type throwingDummyPayments struct{}

func (throwingDummyPayments) Charge(amount float64) bool {
	panic("dummy payments gateway was invoked unexpectedly")
}

type throwingDummyInventory struct{}

func (throwingDummyInventory) Reserve(sku string, qty int) bool {
	panic("dummy inventory service was invoked unexpectedly")
}

type throwingDummyAudit struct{}

func (throwingDummyAudit) Log(event string) {
	panic("dummy audit logger was invoked unexpectedly")
}

func main() {
	processor := &OrderProcessor{
		payments:  throwingDummyPayments{},
		inventory: throwingDummyInventory{},
		audit:     throwingDummyAudit{},
	}

	result := processor.Validate(-3)
	if result != "quantity must be positive" {
		panic(fmt.Sprintf("unexpected result: %q", result))
	}
	fmt.Println("PASS - negative quantity rejected without touching any dummy")
}
```

A fourth language, Java, is a natural fit for this pattern given Mockito's role
in dimension 9, but is omitted here because the three languages above already
demonstrate the pattern's three real implementation shapes from dimension 8,
a hand written throwing class in TypeScript and Python, and an interface based
throwing struct in Go, and adding a fourth language using the same throwing
hand written shape would not show a new variant, only repeat one already shown.
