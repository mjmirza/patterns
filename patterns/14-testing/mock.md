---
name: Mock
slug: mock
family: 14-testing
category: Test Double
aliases: [Mock Object, Behavior Verification Double]
first_described: "Mackinnon, Freeman, Craig 2000; Meszaros 2007"
maturity: canonical
related: [stub, fake-object, spy, dummy, dependency-injection, test-doubles]
incompatible_with: []
verified: 2026-08-02
---

# Mock

## 1. Name, aliases, and lineage

The canonical name is Mock, or Mock Object when the full noun phrase is wanted
to distinguish the pattern from the everyday verb "to mock". The technique
traces to Tim Mackinnon, Steve Freeman, and Philip Craig, who described it in
their paper "Endo-Testing. Unit Testing with Mock Objects," presented at the
XP2000 conference, where they proposed replacing a collaborator with an object
that is pre-loaded with expected calls and that fails the test itself the
moment an unexpected call arrives. Gerard Meszaros later placed Mock as one of
five distinct test double roles in his catalog book, *xUnit Test Patterns.
Refactoring Test Code*, Addison-Wesley, 2007, and it is Meszaros's five-role
vocabulary, Dummy, Stub, Spy, Mock, Fake, that most testing writing since 2007
now uses to keep the roles apart.

Martin Fowler drew the sharpest line in "Mocks Aren't Stubs," published on his
site 2 January 2007, where he defines a mock as an object "pre-programmed with
expectations which form a specification of the calls they are expected to
receive," and states plainly that mocks are verified by checking that the
right calls were made, which he calls behavior verification, in contrast to a
stub, which is checked only by reading the state it leaves behind after the
call, which he calls state verification (Martin Fowler, "Mocks Aren't Stubs,"
https://martinfowler.com/articles/mocksArentStubs.html, published 2 January
2007, verified 2026-08-02). This is the one distinction every serious source
insists on and every casual conversation blurs. a stub answers questions, a
mock answers the question of whether it was asked the right questions in the
first place.

A second, wider sense of the word has become common in practice and deserves
naming rather than pretending it does not exist. Popular libraries such as
Python's `unittest.mock` and Sinon.js ship one flexible class, commonly named
`Mock`, that can be configured to stub return values, spy on calls, and verify
interactions, all through the same object. The Python standard library
describes its own `Mock` class as "intended to replace the use of stubs and
test doubles throughout your code" and states plainly that "mocks record how
you use them, allowing you to make assertions about what your code has done to
them" (Python Software Foundation, "unittest.mock, mock object library,"
https://docs.python.org/3/library/unittest.mock.html, verified 2026-08-02).
This entry treats "Mock" as the framework's proper noun for a flexible object
and "mock" the pattern as the narrower Meszaros/Mackinnon behavior-verification
role, and calls out the shift explicitly wherever the two could be confused,
because the industry never fully separated the two meanings and a reader who
does not know this will misread half the literature.

## 2. Problem and context

A unit of code under test calls a method on a collaborator, and the whole
reason the test exists is to prove that call happens, with the right
arguments, in the right circumstances, the right number of times. The
collaborator's own return value may not matter at all to the test, or the
collaborator may have no return value, because its entire job is a side
effect, sending an email, publishing an event, writing an audit log entry,
charging a credit card, calling a webhook. In every one of these cases there
is no state inside the system under test that a state-based assertion could
inspect after the fact, because the observable effect of the call happened
somewhere external, in a system the test correctly does not want to touch.

Consider an `OrderService.cancel(orderId)` method whose contract is that it
verifies the order exists, notifies the customer through a
`NotificationSender` collaborator, then marks the order cancelled. A test for
the notification behavior cannot read `orderId` back out of
`NotificationSender` and compare it to an expected value, because a real
`NotificationSender` sends an email or a push notification and returns
nothing useful to inspect. Nor can the test spy after the fact and manually
read a list of calls, because the whole point of this specific test is to
fail loudly, at the exact point of mismatch, the moment the wrong
notification is sent or none is sent at all, with a message that names
exactly what was expected and what happened instead.

The context in which Mock earns its place is any test whose specification is
genuinely about an interaction rather than a resulting value, dispatching an
event, calling exactly one of several strategies depending on a condition,
sending exactly one email rather than zero or two, calling an external API
with a specific payload shape, or committing a transaction only after every
required step succeeded. Freeman and Pryce, in *Growing Object-Oriented
Software, Guided by Tests*, Addison-Wesley, 2009, frame this as designing the
object's collaborators through the lens of the messages it sends them, which
they call "listening to the tests," and Mock is the tool that makes that
message-sending observable and checkable in an automated test.

## 3. Forces

The strongest force is observability of behavior that leaves no local state.
When the effect of a call is external, side-effecting, or simply not
representable as a return value the test can read, a mock is often the only
way to write an automated assertion about it at all, short of standing up the
real external system, which trades a fast unit test for a slow, flaky
integration test.

Against that sits coupling to implementation. A mock encodes more than what
the collaborator should return, it also encodes exactly how the collaborator
should be called, in what order, and how many times. Fowler's own follow-up
caution in the same article is that mock-heavy tests couple the test tightly
to the implementation of the method under test, so a refactor that preserves
behavior but changes the call sequence to a collaborator breaks tests that
never should have cared about the sequence. This is the classic overspecified
test failure mode, covered in depth in dimension 11.

Readability and diagnostic clarity favor mocks over hand-rolled fakes for
one-shot assertions, because a mock framework's failure message says precisely
which expected call never happened or which unexpected call did, whereas a
hand-rolled fake usually fails downstream, several lines later, with a message
that does not point at the real cause.

Test speed and determinism favor mocks heavily, since a mock never opens a
socket, never waits on a real clock, and never depends on network
availability, which is why mock-based unit tests can run in milliseconds and
in parallel with no shared external state.

Cognitive load and setup cost cut the other way at scale. A test with five
mocked collaborators, each carrying several expect-and-verify pairs, is
genuinely harder to read than a state-based test against a simple fake, and
the setup boilerplate for strict interaction expectations grows faster than
the assertion it protects, a cost Freeman and Pryce spend a full chapter
managing by insisting on small, single-responsibility interfaces so any one
mock has few things to expect.

## 4. Applicability and non-applicability

Use a mock when the test's specification is genuinely about an interaction. a
command was sent, an event was published, a specific method was called with a
specific argument, and the collaborator itself either has no observable return
value or the return value is irrelevant to what this particular test checks.
Use a mock when the collaborator represents a side effect you must prove
happened exactly once and would be expensive, slow, or destructive to trigger
for real inside a unit test, for example sending an email, charging a card, or
calling a paid third-party API. Use a mock when you are practicing outside-in,
mock-first test-driven development in the London school style described by
Freeman and Pryce, where mocking the not-yet-written collaborator's interface
is how the design of that interface gets discovered.

Do not use a mock to verify a value-producing computation. If the collaborator
returns a value and the test's job is to check what the system under test does
with that value, a stub is the correct tool, because the test cares about
state, not about the fact that the call happened at all, and mocking here adds
interaction assertions that are irrelevant noise and make the test brittle for
no benefit (dimension 12 expands the comparison against Stub). Do not use a
mock for a pure function with no side effects and no collaborators, since
there is nothing to intercept and a plain example-based assertion is both
simpler and more informative. Do not mock a type you do not own, meaning a
third-party library's class or interface, unless you have wrapped it behind
your own narrow interface first, a rule Freeman and Pryce state directly,
because mocking a library type couples your tests to that library's exact API
surface and any upgrade that changes the surface breaks every test that mocked
it, even when your own code did not change. Do not use a mock where an
integration or contract test is what the risk actually calls for, since mocks
verify that your code called the collaborator the way you believe the real
system wants to be called, and that belief itself is never checked by the
mock, so a wrong belief produces a suite of green mocked tests against a
system that is actually broken in production, the failure mode covered under
dimension 11.

## 5. Structure

The pattern has four participants. The System Under Test is the unit of
production code being exercised, which holds a reference to a collaborator
through an injected interface or function type rather than constructing the
real collaborator itself. The Collaborator Interface is the seam, an
abstraction the System Under Test depends on and that both the real
implementation and the mock implement or satisfy, whether through an explicit
interface, a duck-typed protocol, or a function signature. The Mock Object
implements that interface, is pre-loaded before the test runs with the set of
calls it should expect to receive, including argument matchers, call counts,
and ordering constraints where relevant, and it records every actual call it
receives during the run. The Test Code constructs the mock, injects it into
the System Under Test, drives the exercised behavior, and finally asks the
mock to verify itself, either explicitly by calling a verify method, or
implicitly because the mock library raises an exception the instant an
unexpected call arrives, the fail-fast style Mackinnon, Freeman, and Craig
originally described.

## 6. ASCII structure diagram

```
+---------------------+
| Test Code           |
| 1. build mock       |
| 2. set expectations |
| 3. inject mock      |
| 4. exercise SUT     |
| 5. verify mock      |
+---------------------+
     | depends on (constructs, injects)
     v
+-----------------------------------+
| Collaborator Interface (the seam) |
+-----------------------------------+
     ^ implemented by two classes

+-----------------------+
| System Under Test     |
| uses Collaborator via |
| injected reference    |
+-----------------------+
+----------------+
| Mock Object    |
| expected calls |
| actual calls   |
| verify()       |
+----------------+

Test Code exercises the SUT (step 4) and later verifies
the Mock (step 5). The SUT reaches the Mock only through
the Collaborator Interface, never a concrete reference.
```

## 7. Dynamics

```
Test Code         Mock Object              System Under Test    Real World
     |                  |                          |                  |
     | new Mock()       |                          |                  |
     |----------------->|                          |                  |
     | expect(call X,   |                          |                  |
     |   args, times=1) |                          |                  |
     |----------------->|                          |                  |
     | new SUT(mock)    |                          |                  |
     |------------------------------------------->  |                  |
     | sut.doWork()     |                          |                  |
     |------------------------------------------->  |                  |
     |                  |   call X(args)           |                  |
     |                  |<-------------------------|                  |
     |                  | record actual call       |                  |
     |                  | match against expected   |                  |
     |                  | (fail now if mismatched, |                  |
     |                  |  fail-fast strict mocks) |                  |
     |                  | return configured value  |                  |
     |                  | (if any)                 |                  |
     |                  |-------------------------->|                  |
     |                  |                          |  (never reaches  |
     |                  |                          |   the real world) |
     | verify(mock)     |                          |                  |
     |----------------->|                          |                  |
     | pass/fail with   |                          |                  |
     | expected vs      |                          |                  |
     | actual diff      |                          |                  |
     |<-----------------|                          |                  |
```

## 8. Implementation variants

The strict, fail-fast expectation style is the original Mackinnon, Freeman,
and Craig approach and survives in Java frameworks such as jMock and in the
Google C++ mock framework, gMock, where an unexpected call fails the test at
the moment it happens rather than at teardown, and the mock replays the
expectations in the order they were declared unless the API explicitly marks
them unordered. This is the strictest, most behavior-verification-pure
variant, and it produces the earliest, most localized failures.

The record-replay style, used by classic EasyMock and by Moq for .NET,
separates the test into a recording phase, where calls made on the mock are
captured as the expectation set, and a replay phase, where the mock switches
into checking mode and the same calls, made by the real code under test, are
matched against what was recorded. This reads more like ordinary method calls
during setup at the cost of a mode switch the reader must track.

The one-object-does-everything style, used by Python's `unittest.mock.Mock`
and `MagicMock` and by Sinon.js's spy, stub, and mock family, provides a
single flexible object that can be configured as a pure spy that only
records, as a stub that only returns canned values, or as a strict mock whose
expectations are asserted with `assert_called_with` or a Sinon `verify()`
call. This is the loosest of the variants, and it places the burden of
staying disciplined about which role a given usage plays on the person
writing the test, since the library itself does not enforce the Meszaros
distinction.

The auto-mocking or auto-specced style constrains a mock to the real
signature of the thing it replaces so a call with the wrong number of
arguments, or a call to a method the real object does not have, fails
immediately rather than silently succeeding against a permissive dynamic mock.
Python's `unittest.mock.create_autospec` is a direct implementation. it builds
mock objects with the same specifications as the objects they replace, and
methods and functions being mocked have their arguments checked, raising a
TypeError if called with the wrong signature (Python Software Foundation,
"unittest.mock, mock object library,"
https://docs.python.org/3/library/unittest.mock.html, verified 2026-08-02).
Mockito's `mock(Class)` achieves the equivalent through reflection over the
real class's declared methods, which is why a rename of a mocked method in the
production interface breaks the compile of every test that mocked the old
name, catching drift the plain dynamic-mock style cannot.

## 9. Known production uses

Mockito is one of the most widely adopted testing libraries in the Java
community. Its own site states an analysis of 30,000 GitHub projects placed it
as a top 10 Java library overall, not only the testing tools, and number four
once related distributions are counted, ahead of libraries such as Guava
(Mockito, "Tasty mocking framework for unit tests in Java,"
https://site.mockito.org/, verified 2026-08-02). Mockito's own verify method,
called as `verify(mock, times(n)).method(args)`, is the direct
behavior-verification idiom this pattern describes.

Python's standard library ships `unittest.mock` as part of core Python since
Python 3.3, with `Mock.assert_called_with` as its canonical interaction
assertion, and the module's own documentation states it exists so a caller can
replace parts of a system under test with mock objects and make assertions
about how they have been used (Python Software Foundation, "unittest.mock,
mock object library," https://docs.python.org/3/library/unittest.mock.html,
verified 2026-08-02).

Sinon.js provides the equivalent capability for JavaScript and TypeScript
projects, and is a declared dependency of a large share of the JavaScript
testing tooling, including projects that build on top of it such as
sinon-chai for assertion syntax, published on npm as sinon, one of the most
downloaded standalone test-double libraries in the Node.js world.

Google's C++ testing framework ships gMock, distributed alongside GoogleTest
in the same repository, google/googletest on GitHub, specifically to give C++
projects an interaction-verification syntax, `EXPECT_CALL(mock_object,
Method(args)).Times(n)`, comparable to what jMock brought to Java, because
C++ lacked a de facto standard mocking approach before gMock's release.

## 10. Consequences

Positive. A mock makes an interaction that produces no local, inspectable
state into a first-class, automatable assertion, closing a category of test
gap that state-based testing cannot reach at all. Failures are localized and
specific, the assertion failure message from a well-built mock names the
expected call and the actual call side by side, which shortens debugging
compared to a downstream symptom several calls later. Mocks make tests fast
and hermetic, since no mocked collaborator opens a real socket, touches a real
disk, or waits on a real clock, which is why a suite built on mocks for its
external boundaries can run in milliseconds and in full parallel. Used in the
outside-in, mock-first style Freeman and Pryce describe, mocking a
not-yet-written collaborator's interface becomes a design tool, forcing the
author to state the collaborator's contract before its implementation exists.

Negative. Mocks couple a test to the implementation detail of exactly which
calls are made, in what order, and how many times, so a refactor that
preserves the method's outward contract but changes its internal call
sequence to a collaborator can break every mock-based test that specified that
sequence, even though nothing observable to a caller actually changed. Fowler
names this directly as the price of behavior verification in "Mocks Aren't
Stubs." Mock-heavy suites are also prone to a false sense of coverage. every
test passes because the mock faithfully returns what it was told to return,
while the belief encoded in that configuration, about what the real
collaborator actually does, silently drifts from reality, an integration risk
covered fully in dimension 11. Setup and maintenance cost scale with the
number of collaborators and the strictness of the expectations, so a
constructor with many dependencies, or a codebase that resists the small,
narrow-interface design Freeman and Pryce recommend, produces mock setup code
that is longer and harder to read than the production logic it is testing.

## 11. Failure modes and misuse

Overspecification, the single most common misuse. A test mocks every call a
collaborator receives, including incidental calls the test's actual
specification does not care about, so any harmless internal refactor that
changes call order, adds a redundant call, or removes one, breaks tests that
were never meant to pin that detail down. Symptom. a large fraction of the
suite turns red after a refactor that changed no externally observable
behavior, and the fix is invariably to loosen the mock's expectations rather
than to revert the refactor. Cause. treating every call a collaborator
happens to receive as part of the specification instead of deliberately
choosing which calls are the specification. Fix. mock only the interactions
the test is actually about, use permissive stub behavior or a real fake for
the rest, and prefer loose argument matchers over exact-value matchers unless
the exact value is the point of the test.

Mock-real drift, sometimes called the fidelity gap. The mock is configured to
return what the author believes the real collaborator returns, but the real
collaborator's actual contract has since changed, or was misunderstood from
the start, and no test in the suite ever calls the real implementation to
check. Symptom. the full test suite is green, deploys pass CI, and the
feature fails the first time it runs against the real collaborator in
staging or production, often with a completely different response shape than
every mock in the suite assumed. Cause. mocks encode a belief about a
contract, not the contract itself, and nothing forces that belief to stay
synchronized with reality unless a separate mechanism checks it. Fix. pair
every mock of an external boundary with a small number of contract tests or
integration tests that exercise the real collaborator, so the mismatch is
caught somewhere in the pipeline even though the fast unit tests stay mocked.
Freeman and Pryce's walking-skeleton practice, where a thin slice of the real
system is wired together and deployed before any feature logic is built,
exists specifically to catch this class of mismatch early in a project's
life.

Mocking a type you do not own. A test mocks a third-party library class or
interface directly rather than wrapping it behind a narrow interface owned by
the codebase. Symptom. a routine dependency upgrade, one that changes nothing
about the library's real runtime behavior for the code's actual usage,
suddenly breaks a wall of unrelated tests because the library's method
signatures or class shape changed in a way the mocks were sensitive to.
Cause. the seam being mocked is owned by an external party, so the test suite
has no control over its stability. Fix. introduce a thin adapter interface
owned by the codebase, mock the adapter, and let the adapter's own small,
focused test suite be the only place that touches the real library type
directly.

Verifying implementation instead of contract, closely related to
overspecification but distinct enough to name separately. A test asserts the
exact private helper method a class calls internally to accomplish a public
behavior, rather than asserting the public behavior itself. Symptom. a
behavior-preserving internal rewrite, for example replacing a for-loop with a
stream pipeline that calls a differently-named helper, breaks tests that
should have been indifferent to that choice. Cause. the mock's expectations
were declared against an implementation detail rather than against a
genuine architectural seam. Fix. mock only at genuine architectural seams,
points where the design already says this is a replaceable collaborator,
never at a call an object makes to itself or to a private helper.

Strict-mode brittleness with unordered or optional calls. A framework
defaults to strict, ordered expectations, and a test author who wants to check
only that a call happened at least once, without caring about order relative
to other calls, still writes a strict, ordered expectation by habit. Symptom.
the test fails intermittently or immediately whenever an unrelated,
order-independent call is reordered, even though the two calls have no actual
dependency on each other. Cause. the author reached for the default strict,
ordered form of the expectation API rather than the explicit unordered or
at-least form. Fix. use the framework's explicit unordered or at-least
matchers, gMock's default-unordered `EXPECT_CALL` behavior combined with
`Times(AtLeast(1))` being the direct example, rather than relying on
strictness by default.

## 12. Trade-off matrix

| Force | Mock | Stub | Fake | Spy |
|---|---|---|---|---|
| What it verifies | The interaction itself, was the right call made | The state the system under test ends in, given a canned answer | Behavior close to the real thing, checked by state or by output | The interaction, checked after the fact rather than pre-specified |
| Failure timing | Immediately at the wrong call, in fail-fast implementations | Only when the test's own assertion runs, after exercising the SUT | Same as a real dependency, whenever the SUT's own logic fails | Only when the test's own assertion runs, after exercising the SUT |
| Coupling to implementation | High, encodes call order, count, and arguments | Low, only encodes what value comes back | Low to medium, encodes the fake's own simplified behavior contract | Medium, encodes which calls were recorded but not upfront expectations |
| Best fit | Side effects with no return value, command-style calls | Value-producing collaborators whose return the SUT branches on | A collaborator too complex or too slow to construct for real, but simple to reimplement in miniature | Interaction checks the author prefers to assert after the exercise phase rather than declare in advance |
| Setup cost | Higher, expectations must be declared before exercising the SUT | Low, a canned return value | Medium to high, an entire working miniature implementation | Low, no expectations needed up front |
| Risk if misused | Overspecified, brittle tests that break on harmless refactors | Silent behavior drift if the stub's canned value stops matching reality | Fake itself has a bug and every test built on it inherits it | Same overspecification risk as Mock if assertions are too exact |

## 13. Related and incompatible patterns

Stub is the sibling role most often confused with Mock, and the two form the
core Fowler distinction. state verification versus behavior verification.
Where a test is genuinely about a returned value, use a Stub, where it is
genuinely about whether a call happened, use a Mock, and conflating the two by
mocking a value-producing collaborator, or stubbing a command-style call and
never checking it happened, is the most common category error in test-double
usage.

Spy composes closely with Mock and is sometimes implemented on the exact same
object in libraries like Sinon.js and `unittest.mock`, the difference being
when the check happens. a Mock declares its expectations before the exercise
phase and can fail fast during it, while a Spy simply records and defers the
assertion to after the exercise phase, an arrange-act-assert ordering that
some authors find easier to read at the cost of losing the early, localized
failure a strict mock gives.

Fake is the pattern to reach for instead of Mock when a collaborator is
genuinely complex enough that faithfully approximating its real behavior, an
in-memory database rather than a real one, for example, is more valuable and
less brittle than pinning down the exact sequence of calls made against it.

Dummy is unrelated in purpose but frequently sits alongside a Mock in the same
constructor call, filling parameters the specific test does not exercise at
all so the object under test can even be constructed.

Dependency Injection is the structural precondition every mock-based test
relies on. a class that constructs its own collaborators internally rather
than receiving them through a constructor, factory, or setter has no seam a
test can substitute a mock into, so Mock as a testing technique presupposes
some form of dependency injection is already in place in the production code.

Mock is incompatible in spirit, though not mechanically forbidden, with pure
functional code that has no side effects and no injected collaborators at
all, since there is nothing to intercept and example-based, state-oriented
assertions are strictly simpler there.

## 14. Refactoring path in and out

Introducing a mock into code that currently constructs its own collaborators
starts with Extract Interface on the collaborator, so the production class
depends on an abstraction rather than a concrete type. Next, apply Introduce
Parameter, or its constructor equivalent, so the collaborator is passed in
from outside rather than instantiated internally, the seam a mock needs to
exist at all. With the seam in place, write the test by constructing a mock
that implements the new interface, declaring only the calls the specific test
is actually about, injecting it, exercising the method under test, then
asserting the mock's expectations were satisfied, either through an explicit
verify call or by relying on the framework's fail-fast behavior during the
exercise itself. Keep the set of expected calls as small as the test's actual
specification demands, resisting the temptation to lock down every call the
collaborator happens to receive, because that temptation is precisely how
overspecification, dimension 11's most common failure, gets introduced at the
moment of authoring rather than discovered later during a refactor.

Removing a mock, or more precisely replacing it with a lighter test double, is
the right move once a test's expectations have grown to encode implementation
detail the test's actual specification does not care about, the smell named
directly in dimension 11 under overspecification and under verifying
implementation instead of contract. The path out is to identify which
expected calls are load-bearing for the specification and which exist only
because the framework demanded a complete script, drop the incidental ones,
and where the collaborator is genuinely value-producing rather than
command-style, replace the mock with a Stub that returns a fixed value and
drop the interaction assertion entirely, letting a state-based assertion on
the system under test's own return value or resulting state carry the test
instead.

## 15. Testing and verification

Testing code that itself uses mocks is, in the strict sense, testing the
System Under Test's collaboration contract rather than testing the mock,
since the mock is test infrastructure, not production code, and it is
correct, not a gap, that a mock has no test suite of its own. What deserves
verification is that the mock's configured expectations accurately model the
real collaborator's actual contract, the mock-real drift risk from dimension
11, and the standard technique for closing that gap is a small number of
contract tests, run against the real collaborator, that assert the exact same
request and response shapes the mocked unit tests assume. When those contract
tests exist and stay green, the mock's fidelity to reality has independent
evidence behind it rather than resting on the original author's memory.
Mocking makes the system under test's own logic easier to test in isolation
and faster to run, since no real collaborator's latency, flakiness, or side
effects enter the test at all, but it makes the wiring between the system
under test and its real collaborators harder to test, since that wiring is
precisely what the mock replaces and therefore what no mock-based test can
ever exercise, which is why an outside-in TDD practice using mocks is usually
paired with a smaller number of tests that exercise the real wiring the whole
way through at least once, the walking skeleton technique Freeman and Pryce
describe for exactly this reason.

## 16. Observability signals

A mock is test infrastructure, not a production artifact, so it produces no
runtime telemetry of its own. The observability signal that matters here is
about the test suite's health rather than about a running system, and the
signal to watch is the ratio of mock-based unit test failures caused by
genuine behavior regressions against failures caused by incidental,
behavior-preserving refactors, since a suite where the second category is the
larger share is exhibiting the overspecification failure mode from dimension
11 and is a maintenance cost sink rather than a safety net. A second useful
signal, where a project maintains contract tests alongside its mocked units,
is contract-test staleness, meaning how long since the contract tests that
validate a given mock's assumed behavior against the real collaborator last
ran and passed, since a contract test that has silently stopped running is
exactly the condition that lets mock-real drift go undetected until
production.

## 17. Security and privacy implications

Mocks themselves carry no runtime attack surface, since they exist only
inside the test process and are never deployed. The concrete risk is indirect
and specific to security-relevant collaborators. a mocked authentication,
authorization, or payment-verification dependency can be configured, whether
deliberately for test convenience or by mistake, to always return success or
authorized, and if that permissive mock configuration is ever reused outside
the unit test boundary, for example copy-pasted into a staging environment
stub server, or left active behind a feature flag meant only for local
development, it becomes a genuine authorization bypass. The standard
mitigation is architectural rather than mock-specific. security-critical
verification logic should never be reimplemented inside a mock's return value
at all, only the calling convention should be mocked, with the actual
decision logic exercised through real, unmocked integration or contract tests
against the genuine authorization component so no test double is ever the
sole thing standing between a request and a security decision in the deployed
system.

## 18. References

- Tim Mackinnon, Steve Freeman, Philip Craig, "Endo-Testing. Unit Testing with
  Mock Objects," XP2000 conference, 2000. Original description of the mock
  object technique and fail-fast expectation checking.
- Gerard Meszaros, *xUnit Test Patterns. Refactoring Test Code*,
  Addison-Wesley, 2007. Catalogs Mock as one of five test double roles
  alongside Dummy, Stub, Spy, and Fake.
- Steve Freeman, Nat Pryce, *Growing Object-Oriented Software, Guided by
  Tests*, Addison-Wesley, 2009. Outside-in, mock-first TDD, the rule against
  mocking types you do not own, and the walking-skeleton practice.
- Martin Fowler, "Mocks Aren't Stubs,"
  https://martinfowler.com/articles/mocksArentStubs.html, published 2 January
  2007, verified 2026-08-02. The mock versus stub, behavior versus state
  verification distinction, and the coupling-to-implementation trade-off.
- Martin Fowler, "TestDouble," https://martinfowler.com/bliki/TestDouble.html,
  verified 2026-08-02. Meszaros's role vocabulary summarized.
- Python Software Foundation, "unittest.mock, mock object library,"
  https://docs.python.org/3/library/unittest.mock.html, verified 2026-08-02.
  `Mock`, `MagicMock`, `assert_called_with`, and `create_autospec` behavior.
- Mockito, "Tasty mocking framework for unit tests in Java,"
  https://site.mockito.org/, verified 2026-08-02. Adoption ranking among Java
  libraries across 30,000 GitHub projects.
- Sinon.js, https://sinonjs.org/, standalone spies, stubs, and mocks for
  JavaScript and TypeScript.
- Google, googletest project including gMock, https://github.com/google/googletest,
  `EXPECT_CALL` interaction verification syntax for C++.

## Code examples

### TypeScript

```typescript
interface PaymentGateway {
  charge(amountCents: number, cardToken: string): void;
}

class OrderService {
  constructor(private gateway: PaymentGateway) {}

  checkout(amountCents: number, cardToken: string): void {
    if (amountCents <= 0) {
      return;
    }
    this.gateway.charge(amountCents, cardToken);
  }
}

class ChargeExpectation {
  private calls: Array<[number, string]> = [];
  private expected: [number, string] | null = null;

  charge(amountCents: number, cardToken: string): void {
    this.calls.push([amountCents, cardToken]);
  }

  expectCharge(amountCents: number, cardToken: string): void {
    this.expected = [amountCents, cardToken];
  }

  verify(): void {
    if (this.expected === null) {
      throw new Error("no expectation was set before verify()");
    }
    if (this.calls.length !== 1) {
      throw new Error(
        `expected exactly 1 call, got ${this.calls.length}`
      );
    }
    const [amount, token] = this.calls[0];
    const [expAmount, expToken] = this.expected;
    if (amount !== expAmount || token !== expToken) {
      throw new Error(
        `expected charge(${expAmount}, ${expToken}), got charge(${amount}, ${token})`
      );
    }
  }
}

function testChargesGatewayOnValidCheckout(): void {
  const mock = new ChargeExpectation();
  mock.expectCharge(2500, "tok_visa");

  const service = new OrderService(mock);
  service.checkout(2500, "tok_visa");

  mock.verify();
  console.log("PASS: testChargesGatewayOnValidCheckout");
}

function testNeverChargesGatewayOnZeroAmount(): void {
  const mock = new ChargeExpectation();
  const service = new OrderService(mock);
  service.checkout(0, "tok_visa");

  try {
    mock.verify();
    console.log("FAIL: expected verify() to throw, it did not");
  } catch (e) {
    if (e instanceof Error && e.message.includes("expected exactly 1 call, got 0")) {
      console.log("PASS: testNeverChargesGatewayOnZeroAmount");
    } else {
      throw e;
    }
  }
}

testChargesGatewayOnValidCheckout();
testNeverChargesGatewayOnZeroAmount();
```

Run with `npx tsc mock.ts --outDir /tmp/mockts && node /tmp/mockts/mock.js`.
Compiled and ran clean, producing both PASS lines.

### Python

```python
from typing import Protocol
from unittest.mock import Mock


class PaymentGateway(Protocol):
    def charge(self, amount_cents: int, card_token: str) -> None: ...


class OrderService:
    def __init__(self, gateway: PaymentGateway) -> None:
        self._gateway = gateway

    def checkout(self, amount_cents: int, card_token: str) -> None:
        if amount_cents <= 0:
            return
        self._gateway.charge(amount_cents, card_token)


def test_charges_gateway_on_valid_checkout() -> None:
    mock_gateway = Mock(spec=PaymentGateway)
    service = OrderService(mock_gateway)

    service.checkout(2500, "tok_visa")

    mock_gateway.charge.assert_called_once_with(2500, "tok_visa")


def test_never_charges_gateway_on_zero_amount() -> None:
    mock_gateway = Mock(spec=PaymentGateway)
    service = OrderService(mock_gateway)

    service.checkout(0, "tok_visa")

    mock_gateway.charge.assert_not_called()


if __name__ == "__main__":
    test_charges_gateway_on_valid_checkout()
    print("PASS: test_charges_gateway_on_valid_checkout")
    test_never_charges_gateway_on_zero_amount()
    print("PASS: test_never_charges_gateway_on_zero_amount")
```

Run with `python3 mock.py`. Executed clean, both PASS lines printed. The
`spec=PaymentGateway` argument is the auto-specced variant from dimension 8,
it raises if the test calls a method that does not exist on the protocol.

### Go

```go
package main

import "fmt"

type PaymentGateway interface {
	Charge(amountCents int, cardToken string)
}

type OrderService struct {
	gateway PaymentGateway
}

func NewOrderService(gateway PaymentGateway) *OrderService {
	return &OrderService{gateway: gateway}
}

func (s *OrderService) Checkout(amountCents int, cardToken string) {
	if amountCents <= 0 {
		return
	}
	s.gateway.Charge(amountCents, cardToken)
}

type chargeCall struct {
	amountCents int
	cardToken   string
}

type mockGateway struct {
	calls []chargeCall
}

func (m *mockGateway) Charge(amountCents int, cardToken string) {
	m.calls = append(m.calls, chargeCall{amountCents, cardToken})
}

func (m *mockGateway) verifyCalledOnceWith(amountCents int, cardToken string) error {
	if len(m.calls) != 1 {
		return fmt.Errorf("expected exactly 1 call, got %d", len(m.calls))
	}
	got := m.calls[0]
	if got.amountCents != amountCents || got.cardToken != cardToken {
		return fmt.Errorf("expected Charge(%d, %q), got Charge(%d, %q)",
			amountCents, cardToken, got.amountCents, got.cardToken)
	}
	return nil
}

func (m *mockGateway) verifyNeverCalled() error {
	if len(m.calls) != 0 {
		return fmt.Errorf("expected 0 calls, got %d", len(m.calls))
	}
	return nil
}

func testChargesGatewayOnValidCheckout() {
	mock := &mockGateway{}
	service := NewOrderService(mock)

	service.Checkout(2500, "tok_visa")

	if err := mock.verifyCalledOnceWith(2500, "tok_visa"); err != nil {
		panic("FAIL: testChargesGatewayOnValidCheckout: " + err.Error())
	}
	fmt.Println("PASS: testChargesGatewayOnValidCheckout")
}

func testNeverChargesGatewayOnZeroAmount() {
	mock := &mockGateway{}
	service := NewOrderService(mock)

	service.Checkout(0, "tok_visa")

	if err := mock.verifyNeverCalled(); err != nil {
		panic("FAIL: testNeverChargesGatewayOnZeroAmount: " + err.Error())
	}
	fmt.Println("PASS: testNeverChargesGatewayOnZeroAmount")
}

func main() {
	testChargesGatewayOnValidCheckout()
	testNeverChargesGatewayOnZeroAmount()
}
```

Run with `go run mock.go`. Executed clean, both PASS lines printed. Go has no
mainstream mocking library in the standard toolchain, so the idiomatic path
here, a small interface plus a hand-written recording double, matches how
most Go codebases actually write mocks rather than reaching for a reflection
heavy framework, though libraries such as golang/mock, known as gomock, and
testify's mock package exist and generate the same shape of code.

Java was not used for this entry despite the toolchain being available,
because Mockito's own idiomatic API, `verify(mock, times(1)).charge(2500,
"tok_visa")`, is already quoted and sourced in dimension 9 and would add a
fourth language without adding a structurally new variant beyond what the
record-replay description in dimension 8 already covers. The three languages
above were chosen because they show three distinct implementation shapes, a
hand-rolled expectation object, a framework-provided auto-specced mock, and a
hand-rolled recording double in a language with no reflection-based mocking
convention.
