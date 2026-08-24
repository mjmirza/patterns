---
name: Stub
slug: stub
family: 14-testing
category: Test Double
aliases: [Test Stub]
first_described: "Meszaros 2007, popularized by Fowler 2007"
maturity: canonical
related: [fake, mock-object, spy, dummy, dependency-injection, test-data-builder]
incompatible_with: []
verified: 2026-08-02
---

# Stub

## 1. Name, aliases, and lineage

The canonical name in this catalog is Stub, and the literature that distinguishes
it from other testing vocabulary usually writes it as Test Stub, precisely
because the bare word stub already had an older, broader meaning in software
engineering before automated unit testing existed. A method stub, in the older
sense, is a short, minimal placeholder for a method or module that has not been
written yet, just enough of a declaration to let the pieces around it be built
and integrated before the real implementation exists, the shape most commonly
associated with top-down incremental integration, where a caller is exercised
against a chain of stand-in stubs before its real dependencies are ready
(Wikipedia contributors, "Method stub", verified 2026-08-02).
That older meaning still shows up in phrases such as "stub out this function"
and is a fair use of the word, but it names a placeholder for missing
production code, not the narrower testing pattern this entry describes.

The narrower, testing-pattern sense of Stub was catalogued by Gerard Meszaros
in *xUnit Test Patterns. Refactoring Test Code*, Addison-Wesley, 2007, as one
of five kinds of test double, alongside Dummy, Fake, Spy, and Mock Object.
Ahead of the book's own publication, Martin Fowler summarised Meszaros's
taxonomy for a wide audience in an article dated 2 January 2007, and the
article's wording is the most widely cited definition in the field, so it is
quoted directly here. Fowler quotes Meszaros as writing that "Stubs provide
canned answers to calls made during the test, usually not responding at all to
anything outside what's programmed in for the test" (Martin Fowler, "Mocks
Aren't Stubs", published 2 January 2007, verified 2026-08-02). The same
article gives the sibling definitions this entry leans on throughout to keep
Stub distinct from its neighbours. a Dummy is "passed around but never
actually used", a Fake "actually have working implementations, but usually
take some shortcut which makes them not suitable for production", a Spy is a
stub "that also record some information based on how they were called", and a
Mock is "pre-programmed with expectations which form a specification of the
calls they are expected to receive" (same source). Wikipedia's own article on
test doubles corroborates the attribution to Meszaros and the 2007
Addison-Wesley publication, and records that Microsoft's engineering
documentation later adopted the same five-way vocabulary (Wikipedia
contributors, "Test double", verified 2026-08-02).

A detail worth naming plainly, because it causes real confusion in code
review and is revisited in dimension 11, is that popular libraries do not
name their classes after this taxonomy consistently. Sinon.js ships a
dedicated function called `sinon.stub()`, distinct from `sinon.spy()` and
`sinon.mock()`, so its vocabulary lines up with Meszaros directly (Sinon.JS
documentation, "Stubs", verified 2026-08-02). Python's standard library takes
a different path. its single `unittest.mock.Mock` class is used to build
stubs, spies, and mocks depending on how a test configures and inspects it,
and the standard library's own documentation describes the class as removing
"the need to create a host of stubs throughout your test suite", using the
word stub to describe what the single Mock class replaces rather than naming
a distinct Stub type (Python Software Foundation, "unittest.mock", verified
2026-08-02). Jest goes further still and calls the same underlying object a
"mock function" in its own documentation, even describing mock functions as
"also known as spies", with the word stub appearing nowhere on its mock
function API page (Jest documentation, "Mock Functions", verified
2026-08-02), even though a `jest.fn().mockReturnValue(value)` used without
any later assertion on the mock function itself is, by Meszaros's definition,
functioning purely as a Stub. The conclusion this entry draws from all three
sources together, stated as engineering judgement rather than a sourced
claim, is that Stub names a ROLE a test double plays in a given test, decided
by whether the test later asserts on the double, not a class name any
particular library happens to use, and a team that wants the vocabulary to
mean something in code review has to agree on that distinction explicitly
rather than infer it from a library's own naming.

## 2. Problem and context

Code under test frequently depends on something the test cannot, or should
not, use as it really behaves. A payment gateway that would actually charge a
card. A clock that returns a different value every time it is read. A
third-party HTTP API that is slow, rate limited, or simply unavailable from a
CI runner. A random number generator. A filesystem that may or may not have
the expected file present depending on which machine the suite runs on. In
every one of these cases the test's actual goal has nothing to do with the
collaborator itself, the collaborator is only in the way, and the test wants
a single, predictable answer from it so the test can watch what the code
under test does with that answer.

A Stub is a substitute implementation of the collaborator's interface, built
or configured by the test, that answers each call the code under test is
expected to make with a value decided in advance, and does nothing else. It
performs no real logic, keeps no real state beyond what it was told to
return, and, this is the part that separates it from its closest relatives,
it is never itself the subject of an assertion. The test does not later ask
the stub whether it was called, and with what arguments. If a test finds
itself asking that question, the double it is holding has quietly become a
Mock or a Spy, which is a legitimate and different pattern with a different
job, distinguished carefully in dimension 1 above and covered by its own
entry in this catalog.

The context in which this specific pattern, rather than one of its
neighbours, is the right tool has three recognisable parts. First, the
test's interest is in feeding a specific input into the code under test
through the collaborator's return value, an approved charge, a declined
charge, a timeout, an empty result set, a particular date. Second, the test
does not need the collaborator to behave correctly in general, only to
answer the handful of calls this one scenario will actually make, so a full
working reimplementation would be wasted effort. Third, the test does not
care how the code under test called the collaborator, only what the code
under test does as a result, which keeps the resulting assertion focused on
the system under test's own observable output or state rather than on the
shape of an internal call.

## 3. Forces

- **Determinism versus realism.** Strongly favoured toward determinism. A
  stub answers the same canned value every time regardless of the clock, the
  network, or the collaborator's real current state, at the direct cost of
  ever resembling how the real collaborator would behave outside exactly the
  cases the test author anticipated.
- **Speed versus fidelity.** Favoured toward speed. A stub is an in-process
  return statement, effectively free compared to a network round trip, a
  database write, or a filesystem read, and that speed is what makes a large
  unit-test suite runnable in seconds rather than minutes.
- **Test isolation versus integration confidence.** Strongly favoured toward
  isolation. Every collaborator a test stubs is a boundary the test has
  deliberately stopped verifying, which is exactly the property that makes
  the test fast and focused, and exactly the property that later produces
  the central failure mode of this pattern, a green suite next to a broken
  integration, covered in dimension 11.
- **Interface coupling.** A stub still couples the test to the shape of the
  collaborator's interface, its method names and parameter and return types,
  even though it is decoupled from the collaborator's real behaviour. A
  renamed method or a changed return shape breaks every stub built against
  the old shape, which is a maintenance cost rather than a design flaw, and
  is softer when the stub is bound to the real interface type by the
  language's own type system or by a spec-aware mocking library.
- **Verification style.** Classical, state-based testing style is naturally
  served by stubs, because the assertion lives on the observable output of
  the system under test. Interaction-based, so-called mockist testing style,
  reaches instead for Mock and Spy, because its assertions live on the
  collaborator's call history. Fowler's article names this exact split as
  the classical school against the mockist school and observes that the two
  schools produce genuinely different test suites for the same code (Martin
  Fowler, "Mocks Aren't Stubs", verified 2026-08-02). This entry treats the
  split as a real, sourced distinction in the literature and leaves the
  choice between the two schools as a team decision rather than a universal
  answer.
- **Authoring cost versus maintenance cost.** A hand-written stub class costs
  a handful of lines up front and is maximally explicit to a reader, but a
  suite with many hand-written stub classes for the same interface pays that
  cost again on every interface change. A stub generated or configured
  through a mocking library trades some of that per-test explicitness for a
  single point of maintenance when the interface changes, at the cost of an
  added dependency and a slightly less obvious reading path for someone new
  to the codebase.

## 4. Applicability and non-applicability

Reach for a Stub when the following hold.

- The collaborator is slow, unavailable in the test environment, or
  nondeterministic, a clock, a random source, a third-party network call, a
  collaborator with real side effects such as sending an email or charging a
  card that the test must not trigger.
- The test's actual goal is to drive the system under test down a specific
  branch by controlling exactly what the collaborator returns, including an
  edge case or an error condition that would be difficult or slow to trigger
  against the real collaborator.
- The collaborator's interface is narrow enough that a canned
  implementation, hand-written or configured through a library, is cheap to
  build and read.
- The test has nothing to assert about how the collaborator was called, only
  about what the system under test produced as a result.

Do NOT reach for a Stub in the following cases, and the reasoning matters as
much as the rule, because each case names a different pattern that is the
better fit.

- **The test needs to verify the call itself happened, with particular
  arguments, or a particular number of times.** That is the job of a Mock
  Object or a Spy, not a Stub. Attaching an assertion to a double that is
  otherwise built and used as a stub blurs the two patterns together and
  produces a test double a later reader cannot classify at a glance, the
  exact failure mode named in dimension 11.
- **The collaborator's real behaviour, not merely its shape, matters to the
  correctness the test is protecting.** An in-memory repository that must
  actually filter, sort, and enforce a uniqueness constraint the way the
  real database would is a Fake, because a stub answers only the exact calls
  the author anticipated and leaves every other call undefined.
- **No seam exists yet for a substitute to be injected into.** A stub
  requires an interface, a function reference, or a constructor or setter
  parameter the test can swap. Introducing that seam is a prerequisite
  refactor, described in dimension 14, not something the pattern performs on
  its own, and a codebase with concrete, directly-constructed dependencies
  everywhere cannot adopt this pattern without that step first.
- **The true concern under test is integration correctness across a real
  boundary,** whether the code correctly parses the collaborator's actual
  response shape, handles its actual error codes, or survives its actual
  latency. A stub, by construction, cannot detect that the real
  collaborator's contract has drifted away from what the stub assumes,
  which is why a suite that stubs a boundary everywhere and never exercises
  the real boundary anywhere is systematically blind to exactly the
  failures that matter most in production, discussed at length in dimension
  11.
- **A single canned value is reused across dozens of unrelated tests and has
  started to encode business rules of its own,** for example a shared stub
  that must be kept consistent with a tax calculation, a discount rule, or a
  multi-step workflow. At that point the stub has quietly become a second,
  parallel implementation of the collaborator that itself needs correctness
  and its own maintenance, a signal to promote it honestly to a Fake,
  covered in dimension 14, rather than keep patching an aging stub.
- **The real collaborator is already cheap, fast, and deterministic to run
  in a test,** for example an actual in-process SQLite database standing in
  for a production database, or a pure, side-effect-free function. Stubbing
  something you could simply run adds an extra layer of indirection for the
  reader without buying speed or determinism you did not already have.

## 5. Structure

Four participants, named by the role each plays rather than by a fixed class
name, since, as dimension 1 established, the same library object frequently
plays more than one of these roles across different tests.

- **System Under Test (SUT).** The code the test actually exists to
  exercise. It is written against an abstraction of its collaborator, never
  against a concrete implementation, so that the abstraction is the seam a
  test can substitute at.
- **Collaborator interface.** The abstraction the SUT depends on, for
  example a `PaymentGateway` interface, a `Clock` interface, or a
  `Repository` interface. It is intentionally narrow, declaring only the
  operations the SUT actually calls, rather than the full surface a real
  implementation might expose.
- **Test Stub.** A concrete implementation of the Collaborator interface,
  constructed or configured by the test, holding one or more canned answers
  the test decided on in advance. Meszaros's own vocabulary calls the values
  a stub supplies "indirect inputs", because they enter the SUT indirectly,
  through a call to the collaborator, rather than directly through the SUT's
  own method parameters (the term is used consistently throughout
  Meszaros's taxonomy as described in Fowler's summary of it, Martin
  Fowler, "Mocks Aren't Stubs", verified 2026-08-02). Critically, the Test
  Stub is never itself queried or asserted upon after the test runs, only
  constructed and handed to the SUT.
- **Test Case.** Constructs the Test Stub with its canned answers in an
  arrange step, injects it into the SUT through whatever seam the SUT
  exposes, constructor injection, setter injection, or a factory override,
  exercises one method on the SUT, and then asserts entirely on the SUT's
  own return value or observable state.

The relationship that matters is that the SUT's compile-time dependency
targets the Collaborator interface alone, never the concrete Test Stub type,
and the Test Case is the only participant that knows the Test Stub exists.
This is the same reversal of the naive dependency direction that dependency
inversion produces in production designs generally, and it is why
introducing a Stub into a codebase that lacks one is, mechanically, the same
refactor as introducing dependency inversion at that seam, covered in
dimension 14.

## 6. ASCII structure diagram

```
+--------------------------------+
| Test Case                      |
| arrange canned values in setup |
+--------------------------------+
     | constructs
     v
+------------------------------------------------+
| Test Stub                                      |
| - canned answer(s), set by the test in arrange |
| + charge(amount): Result                       |
+------------------------------------------------+
     ^ implemented by, only during this test run
     |
Test Case also constructs and injects the stub into:

+-------------------------------------+
| System Under Test                   |
| depends on Collaborator (interface) |
+-------------------------------------+

+-------------------------------------------------------+
| Test asserts only on the SUT's own return value or    |
| observable state, never on the Test Stub itself. The  |
| Test Stub is never queried or asserted upon directly. |
+-------------------------------------------------------+
```

## 7. Dynamics

The runtime sequence has one property worth stating plainly, because it is
the one most often missed by someone new to the pattern, the call into the
collaborator originates from inside the SUT's own code, not from the test
directly. The test never calls `charge()` on the stub itself, it only builds
the stub and calls a method on the SUT.

```
Test Case          System Under Test         Test Stub
    |                      |                       |
    |-- new StubGateway(   |                       |
    |     canned=approved) |                       |
    |------------------------------------------->  |
    |                      |                       |
    |-- new OrderService(  |                       |
    |     gateway=stub)    |                       |
    |--------------------->|                       |
    |                      |                       |
    |-- placeOrder(1999) ->|                       |
    |                      |-- charge(1999) ------>|
    |                      |                       |-- looks up
    |                      |                       |   canned answer,
    |                      |                       |   no logic beyond
    |                      |                       |   that lookup
    |                      |<-- returns canned  ---|
    |                      |   ChargeResult        |
    |                      |                       |
    |                      |-- computes its own    |
    |                      |   result from the     |
    |                      |   canned value        |
    |                      |                       |
    |<-- returns SUT's own result -----------------|
    |                      |                       |
    |-- assert on the      |                       |
    |   SUT's result only  |                       |
```

Two timing notes carry over from general test-double practice and are worth
naming here. First, when a stub is generated by a spec-aware mocking library
bound to the real collaborator type, that binding happens once, at
construction, and any call to a method the real type does not declare fails
immediately rather than silently returning an undefined value, which is the
mechanism behind the fix for misuse case two in dimension 11. Second, a stub
built as a plain literal object rather than a class, common in languages with
structural typing, has no construction step distinct from its literal value,
so the construct arrow in the diagram above collapses to the moment the
literal is written in the test's arrange section.

## 8. Implementation variants

**Hand-written stub class.** A small class implementing the Collaborator
interface directly, returning a fixed literal from each method. The simplest
and most explicit form, and the one that reads most plainly to someone
unfamiliar with any mocking library, at the cost of one class per distinct
scenario unless it is made configurable.

**Parameterised, configurable stub.** A single stub class whose constructor
or setter accepts the canned value or values as an argument, so one class is
reused across many tests with different configuration rather than one class
per scenario. This is the shape most general-purpose mocking libraries expose
directly, `sinon.stub().returns(value)`, `jest.fn().mockReturnValue(value)`,
Mockito's `when(gateway.charge(anyInt())).thenReturn(result)`, and Python's
`unittest.mock.Mock(return_value=value)`, all configure one flexible object
per test rather than defining a new named class per scenario.

**Framework-generated stub used purely for its return-value programming.**
The same library object listed above can, later in the same test, be handed
to a `.verify()` call or an assertion on its call history, at which point it
has become a Mock rather than a Stub. What keeps it a Stub is a discipline
the test author holds, never the API surface of the library, which is the
naming confusion described in dimension 1 and revisited as a concrete misuse
case in dimension 11.

**Anonymous or inline stub via a closure.** In a language with first-class
functions, a single-method Collaborator interface can be satisfied directly
by a lambda or arrow function assigned to a correctly typed variable, with no
named class at all. TypeScript's `type ChargeFn = (amount) => Result` paired
with a plain arrow function is this variant, shown in the code examples
below, and it is the idiomatic shape wherever the language treats functions
as values.

**HTTP-level stub server.** Rather than stubbing the client-side interface
inside the process, a real, lightweight HTTP server is started for the
duration of the test and configured to answer specific request patterns with
canned HTTP responses. WireMock is a dedicated library built around exactly
this idea, and its documentation describes its core primitive as returning
"canned HTTP responses for requests matching criteria" (WireMock
documentation, "Stubbing", verified 2026-08-02). Go's standard library offers
the same shape natively through `net/http/httptest.NewServer`, described in
its own documentation as "an HTTP server listening on a system-chosen port on
the local loopback interface, for use in end-to-end HTTP tests" (Go
documentation, `net/http/httptest`, verified 2026-08-02). This variant is
worth reaching for specifically when the SUT's own HTTP client code, header
construction, serialization, and connection handling, is itself part of what
the test needs to exercise, since an in-process interface stub would bypass
that code entirely.

**Record and replay.** A real response is captured once, typically against a
sandbox or a recorded fixture, and replayed verbatim as the canned answer on
every subsequent run. This starts as a Stub, a single fixed answer, and
drifts toward a Fake the moment the replay logic grows enough to vary its
answer by request shape rather than always returning the one recorded
payload.

**Auto-generated stub from an interface's type signature.** Tools such as
Mockito's `mock()`, Go's `mockgen`, and Jest's automock generate an
implementation of an interface at build or run time purely from its declared
shape, returning a zero value, `undefined`, or `nil` for every method until a
test explicitly configures one. Every unconfigured method on such an object
is, by the taxonomy in dimension 1, functioning as a Dummy, and it only
becomes a Stub for the specific method a given test configures a return
value on.

**Language note, Go's structural typing.** Because Go interfaces are
satisfied structurally rather than by explicit declaration, a common idiom
skips a named stub type entirely in favour of a small struct whose fields
are themselves functions, set per test case, an idiom sometimes called a
stub via function field. It is shown alongside the more conventional
struct-based stub in the Go code examples below.

**Language note, spec-bound stubs in Python.** `unittest.mock.Mock(spec=RealClass)`
binds the mock's allowed attribute and method names to the real class's
actual shape, so a call to a method the real class does not have raises
`AttributeError` immediately rather than silently returning a fresh, useless
Mock instance, a distinction demonstrated directly in the Python code
example below and discussed further as a fix for a specific misuse case in
dimension 11.

## 9. Known production uses

**Sinon.js, `sinon.stub()`.** Sinon ships Stub as a first-class, separately
named API from Spy and Mock, and its own documentation defines stubs as
"functions, like spies, with pre-programmed behavior" that, when wrapping an
existing method, prevent the original function from running, explicitly
recommending stubs to "control a method's behavior from a test, to force the
code down a specific path" and to "prevent a specific method from being
called directly" (Sinon.JS documentation, "Stubs",
https://sinonjs.org/concepts/stubs, verified 2026-08-02).

**Python standard library, `unittest.mock`.** Shipped in CPython's own
standard library rather than a third-party package, `unittest.mock.Mock` is
configured with `return_value` or `side_effect` to answer calls with canned
data, and the standard library's documentation uses the word stub directly
to describe the class's purpose, stating that it removes "the need to create
a host of stubs throughout your test suite" (Python Software Foundation,
"unittest.mock", https://docs.python.org/3/library/unittest.mock.html,
verified 2026-08-02).

**WireMock.** An HTTP-level stubbing server whose entire purpose, as its own
documentation states, is to "return canned HTTP responses for requests
matching criteria" through a request matcher paired with a response
definition, the stub mapping (WireMock documentation, "Stubbing",
https://wiremock.org/docs/stubbing/, verified 2026-08-02). WireMock is
widely used across the Java and polyglot HTTP-service testing ecosystem
specifically for this pattern applied at the network boundary rather than
the in-process interface boundary.

**Go standard library, `net/http/httptest`.** Part of Go's own standard
library, `httptest.NewServer` starts a real local HTTP server that a test
configures to answer with a canned response, described in the package
documentation as existing "for use in end-to-end HTTP tests" (Go
documentation, `net/http/httptest`, https://pkg.go.dev/net/http/httptest,
verified 2026-08-02), and is the idiomatic way the Go ecosystem stubs an
HTTP-based collaborator without a third-party dependency.

**Jest, `jest.fn().mockReturnValue()`.** Jest is one of the most widely used
JavaScript testing frameworks and provides `mockReturnValue` and
`mockImplementation` specifically to configure a canned return from a mock
function (Jest documentation, "Mock Functions",
https://jestjs.io/docs/mock-function-api, verified 2026-08-02). Used without
any later assertion on the function's call history, this is a Stub in every
sense Meszaros's taxonomy describes, even though Jest's own documentation
calls the mechanism a mock function, and never uses the word stub on that
page, the exact naming gap named in dimension 1.

## 10. Consequences

Positive.

- Tests become fast and deterministic, independent of network availability,
  clock behaviour, or the current state of an external service, which is
  what makes a large unit-test suite practical to run on every commit.
- The requirement to stub a collaborator forces that collaborator to be
  expressed behind an explicit seam, an interface, a function type, an
  injected dependency, which is a design pressure toward dependency
  inversion that frequently improves the production code's structure as a
  side effect of making it testable.
- Otherwise rare or hard-to-trigger scenarios, a specific declined-payment
  error code, a malformed response, an empty result set, become one line of
  configuration rather than an elaborate setup against a real system.
- Removing slow or costly external calls from the fast test tier keeps
  continuous integration feedback quick, which keeps the whole team's
  iteration loop short.
- A stub's canned configuration, read alongside the test that constructs it,
  states the scenario's premise explicitly, a reader does not need to
  reconstruct a specific external system's state to understand what input
  produced the assertion.

Negative.

- A stub cannot notice that the real collaborator's contract has changed.
  The suite stays green while production breaks, which is the single most
  cited criticism of stub-heavy testing and the direct motivation for the
  drift-detection fixes in dimension 11.
- Where the collaborator's real behaviour genuinely matters to correctness,
  stubbing it means the test is validating the test author's assumptions
  about the world rather than the world itself.
- Hand-written stubs multiply across a suite and accumulate maintenance
  debt, every interface change requires editing every affected stub
  implementation by hand, unless the stub is bound to the real interface
  type in a way the compiler or the mocking library can check
  automatically.
- A stub answers only the calls its author anticipated. An unanticipated
  call path returns an undefined, `None`, or zero value by default, which
  produces a confusing failure some distance from its actual cause rather
  than an immediate, clear one.
- Overuse quietly pushes a test suite's assertions toward checking internal
  call shape rather than genuine observable behaviour, which is the same
  drift toward Mock misuse named as a specific failure mode next.

## 11. Failure modes and misuse

**Green suite, broken production because the real collaborator's shape
changed.** Symptom. Every automated test passes, and a production incident
traces back to the third-party API returning a field renamed or a status
code no test anticipated. Cause. Every test touching that collaborator stubs
it, and no test in the suite ever exercises the real HTTP boundary, so the
stub's canned shape silently diverged from reality. Fix. Add a small,
deliberately scoped tier of contract tests, whether a Pact-style consumer
contract or a periodic scheduled test against the real or a certified
sandbox endpoint, and periodically refresh the stub's canned payload from a
genuinely captured real response rather than from an assumption typed by
hand.

**Failure deep inside the system under test, far from the assertion line.**
Symptom. The test throws a null reference, `AttributeError`, or `undefined
is not a function` error somewhere inside the code under test, not at the
assertion. Cause. The system under test called a method on the collaborator
the stub was never configured to answer, so the stub's default fallback,
`None`, `undefined`, or a zero value, leaked silently into the calculation.
Fix. Build the stub from a spec-aware or interface-bound construction, for
example `Mock(spec=RealClass)` in Python or a stub typed against the real
interface in TypeScript, Go, or Java, so an unconfigured or unknown method
call raises loudly and immediately, at the point of the mistake rather than
at some unrelated downstream calculation.

**A behaviour-preserving refactor breaks dozens of unrelated tests.**
Symptom. A change that alters no observable behaviour still fails many
tests across the suite. Cause. Stubs were configured with strict argument
matching, or a hand-rolled stub asserts internally on the exact arguments or
call order it received, turning what was written as a Stub into an
accidental Mock coupled to an implementation detail that was never meant to
be part of the contract. Fix. Relax the stub to answer any call to that
method with the same canned value unless the argument genuinely changes the
correct answer, and move any real need to verify a call's arguments or count
into an explicitly named, separate Mock or Spy so the two concerns, canned
input and interaction verification, are not tangled inside one object.

**A magic literal appears copy-pasted across two hundred tests.** Symptom.
The string `"test@example.com"`, the number `42`, or the date
`"2024-01-01"` shows up verbatim in stub configuration throughout the suite,
and no one can say why that particular value was chosen. Cause. Canned
values were typed ad hoc at each call site rather than built from a shared,
named source. Fix. Introduce a Test Data Builder or an Object Mother for the
canned values, so the stub's configuration reads as intent, "a customer with
an expired card", rather than an opaque literal, and the meaning of the
literal is defined exactly once.

**A "unit" test suspiciously takes eight seconds.** Symptom. A test file
that supposedly stubs a database repository takes noticeably longer to run
than comparable files. Cause. The object called a stub is actually a mocking
framework proxy performing heavy reflection or dynamic-proxy generation on
every call, or, worse, it wraps a real client pointed at a genuinely running
local service rather than being an in-memory canned answer at all. Fix.
Confirm the stub never crosses a real process boundary, and if behavioural
fidelity genuinely requires a heavier double, name it honestly as a Fake and
place it in the test tier whose time budget accounts for that cost, rather
than letting it masquerade as a fast unit test.

**A pull-request review stalls over whether a double is a mock or a
stub.** Symptom. Two engineers disagree in code review about whether the
payment gateway double in a test mocks or stubs the collaborator, and the
disagreement blocks the review. Cause. Popular libraries, Jest most
visibly, name their single test-double object mock regardless of whether
the test later asserts on it, so the library's own vocabulary does not
track the pattern literature's vocabulary, as established with citations in
dimension 1. Fix. Settle the team's own convention once, following Meszaros
and Fowler, a double is a Stub for as long as nothing in the test asserts
on the double itself, and becomes a Mock the moment a `.verify()`,
`expect(mock).toHaveBeenCalledWith(...)`, or equivalent assertion is added,
write that rule down in the team's testing guide, and stop relitigating it
on every review.

**A shared helper file grows into a single stub answering hundreds of
scenarios.** Symptom. A widely imported test-helper module holds one giant
stub configured with method-and-return-value pairs for every scenario any
test in the suite might ever need. Cause. Convenience, adding one more entry
to the shared stub felt cheaper than constructing a small, scenario-specific
one. Fix. Build the stub locally, inside the failing test's own arrange step
or a very narrowly shared helper covering only closely related tests, so a
failing assertion's cause is visible without cross-referencing an unrelated
file, and so a change to one scenario's canned answer cannot silently affect
an unrelated test that happens to import the same shared object.

## 12. Trade-off matrix

Compared against its five named neighbours from the same taxonomy, plus the
real collaborator exercised directly in an integration test, across the
forces named in dimension 3.

| Force | Stub | Fake | Mock Object | Spy | Dummy | Real collaborator (integration test) |
|---|---|---|---|---|---|---|
| Determinism and speed | High, canned and in-process | High, still in-process, some real logic runs | High, canned like a stub | High, canned plus recording | Highest, never actually invoked | Low to medium, depends on the network, database, or clock |
| Behavioural fidelity to production | Low, only what was configured answers | Medium to high, a working simplified implementation | Low, only what was configured answers | Low, only what was configured answers | None, exists only to satisfy a signature | High, it is the real thing |
| Verifies the interaction itself | No, by definition | No | Yes, that is its purpose | Yes, after the fact | No | Only indirectly, through side effects |
| Maintenance cost as the interface evolves | Medium, every hand-written stub needs an edit | Medium to high, real logic must stay faithful | Medium, expectations must be edited | Medium | Low, trivial to update | Low for the test itself, higher for keeping the environment usable |
| Failure locality when misused | Poor, an unconfigured path can fail silently | Good, real logic tends to fail loudly on a real bug | Good, an unmet expectation fails loudly | Good, a missing recorded call fails loudly | Not applicable | Excellent, a real error surfaces at its true source |
| Coupling to implementation detail | Low, when configured by return value rather than call shape | Low | High, easy to over-specify exact calls | Medium | None | None |
| Confidence the real integration still works | None | Some, only if actively kept faithful | None | None | None | High, the only entry that directly measures this |

Reading the table together. Stub wins on speed, determinism, and staying
decoupled from how the system under test calls the collaborator, which is
exactly why it dominates the fast, high-volume unit-test tier of a healthy
suite. Fake trades some of that speed for behavioural fidelity when the
collaborator's actual logic, not merely its shape, matters to correctness.
Mock and Spy exist for the smaller set of tests where the interaction
itself, not just its result, is the thing genuinely under test. Dummy is
the lightest-weight entry, useful precisely where a value is never
exercised at all. The real collaborator, exercised deliberately in a
smaller, separately budgeted integration or contract tier, is the only row
that can actually detect drift between what every stub in the suite assumes
and what production truly does, which is why the healthiest suites use Stub
heavily but never exclusively, the exact conclusion dimension 11's first
misuse case argues for.

## 13. Related and incompatible patterns

- **Fake.** A natural upgrade path. A stub whose canned logic has grown
  real branching behaviour, answering differently depending on its input
  rather than always returning one fixed value, has, in practice if not in
  name, become a Fake, and the decision of when to make that promotion
  explicit is covered as a specific refactoring step in dimension 14.
- **Mock Object.** The most frequently confused sibling, and the one
  dimension 11's naming-confusion misuse case is built around. A Stub
  answers calls and is never itself verified. A Mock is pre-programmed with
  expectations and IS verified, typically through an explicit `.verify()`
  call or an assertion on its recorded call history. The same underlying
  library object can play either role in different tests depending purely
  on whether a later assertion is placed on the double itself.
- **Spy.** Sits between Stub and Mock. Fowler's summary of Meszaros
  describes a Spy directly as "stubs that also record some information
  based on how they were called" (Martin Fowler, "Mocks Aren't Stubs",
  verified 2026-08-02), so a Spy is best understood as a Stub with an added,
  separate recording responsibility, canned answers up front, plus
  after-the-fact inspection, rather than Mock Object's up-front
  expectations.
- **Dummy.** The degenerate case a Stub can collapse into. Every method on
  an auto-generated stub that a given test leaves unconfigured is
  functioning as a Dummy for that method, a value that satisfies a required
  parameter or return type but is never meaningfully exercised by the
  scenario under test.
- **Test Data Builder and Object Mother.** Compose cleanly with Stub,
  supplying the actual canned values a stub returns so that the meaning of
  a literal is named once and reused, the fix for the magic-literal misuse
  case in dimension 11 rather than a competing pattern.
- **Dependency Injection.** A prerequisite, not a substitute. A stub can
  only be substituted into the system under test through a seam, and
  constructor or setter injection is the most common way that seam is
  provided in practice, the mechanics of introducing it are covered in
  dimension 14.
- **Contract testing (Pact and similar approaches).** Complements the
  pattern directly rather than replacing it, by independently verifying
  that the canned shape every stub in a suite assumes still matches what
  the real collaborator actually returns, which is the concrete answer to
  the drift risk named as the first and most serious misuse case in
  dimension 11.
- **Service Locator.** In mild, practical tension rather than outright
  incompatible. A Service Locator that resolves a collaborator internally,
  rather than accepting it as a parameter, hides the seam a stub needs to
  be injected through, so codebases built around a Service Locator
  typically need an additional mechanism, a locator override registered
  for the duration of a test, a thread-local test hook, just to make
  substitution possible, an extra step constructor injection avoids by
  design.

## 14. Refactoring path in and out

Introducing a Stub into code that has none, step by step.

1. Identify the concrete, hard-to-control collaborator the code under test
   currently constructs or calls directly, `new StripeClient(...)`,
   `time.Now()`, `os.ReadFile(...)`.
2. Extract an interface, or a function type in a language with first-class
   functions, that names only the operations the system under test actually
   calls, following interface segregation rather than copying the
   collaborator's entire real surface.
3. Introduce that interface as a constructor or setter parameter on the
   system under test, defaulting to the real implementation wherever the
   production code wires things together, so no production caller's
   behaviour changes.
4. In the test, write the smallest hand-written stub implementing the
   interface, or configure a mocking library's stub API, returning the
   exact canned value the scenario needs and nothing more.
5. Inject the stub during the test's arrange step, exercise one method on
   the system under test, and assert only on the system under test's own
   return value or observable state, never on the stub.
6. Repeat for the next scenario using a fresh, minimally configured stub
   rather than reaching for an existing shared one, resisting the pull
   toward the shared-mega-stub misuse case named in dimension 11.
7. Once several tests genuinely need the same canned shape, extract a
   small, named builder function for that value so the intent behind it, an
   expired card, a rate-limited response, is named once rather than
   repeated as a bare literal, the fix for the magic-literal misuse case.

Removing or promoting a Stub once it stops earning its place, step by step.
The signal to act is either the stub's canned logic quietly growing real
branches, or the team discovering, more than once, that stubbed tests pass
while the actual integration is broken.

1. If the stub has genuinely grown branching logic that behaves differently
   for different inputs, rename it explicitly to a Fake and give it its own
   focused correctness tests, an honest rename rather than a silent one, so
   a future reader is not misled by a class still called `StubGateway` that
   no longer behaves like one.
2. If the stub exists but no contract or integration test exists anywhere
   for that boundary, add a small, deliberately budgeted tier of
   real-collaborator tests rather than deleting the stub, the fast unit
   tests built around the stub still earn their keep, they simply need a
   real-boundary backstop alongside them.
3. If a hand-rolled stub class has accreted so many configuration knobs
   that it is effectively a second implementation of the collaborator,
   delete it and replace it with a library-generated, interface-bound stub
   so a future interface change fails the test suite immediately rather
   than being silently absorbed by a stale hand-written class.
4. If assertions have crept onto the stub itself, checking call arguments
   or counts, split the responsibility, keep a plain stub answering the
   canned value, and introduce a separate, explicitly named Mock or Spy
   for the interaction check, restoring one responsibility per test
   double.

## 15. Testing and verification

This dimension is largely engineering judgement, drawn from practice rather
than from a single citable source, stated here up front.

Easier because of the pattern.

- Edge cases that are rare or difficult to trigger against a real
  collaborator, a specific declined-payment error code, an API responding
  with a fractional currency amount, a timeout, become a single line of
  stub configuration rather than an elaborate real-world setup.
- Tests run without network, filesystem, or clock access, which makes them
  safe to run in parallel and in any order, a property most real
  integrations cannot offer as cheaply.
- A failing test's arrange section is, in effect, the specification of the
  scenario. A reader does not need to reproduce a specific external
  system's state to understand what input produced the observed assertion.

Harder because of the pattern.

- A stub cannot tell a test it is wrong. There is no automatic check that a
  canned answer still matches what the real collaborator would actually
  return, which is the drift risk covered in dimension 11's first misuse
  case.
- Debugging a failure that traces back to an unconfigured stub method
  requires stepping into the stub itself, an extra layer of indirection
  most step-through debugging sessions do not expect to encounter.

Techniques that apply.

- Spec-bound or interface-bound stub construction, `Mock(spec=RealClass)`
  in Python, a stub typed directly against the real interface in
  TypeScript, Go, or Java, so a rename or a signature change on the real
  collaborator fails at stub construction time rather than at some
  unrelated later assertion, demonstrated directly in the Python code
  example below.
- A small, deliberately scoped tier of contract tests, whether Pact-style
  or a periodic scheduled test against a real sandbox endpoint, asserting
  that the real collaborator's response shape still matches what every
  stub in the suite assumes, run on its own budget rather than on every
  commit necessarily.
- Mutation testing applied to the system under test with the stub in
  place, to confirm the stub's canned values genuinely exercise the branch
  the test claims to cover, rather than accidentally taking the same code
  path a happy-path stub would take regardless of the mutation.
- Periodic, deliberate refresh of any canned payload that was originally
  seeded from a captured real response, diffed against a freshly captured
  one, so the stub's data has a known provenance rather than being
  invented once and never revisited.
- Keeping a stub's construction local to the test that needs it, or to a
  very narrowly shared helper covering closely related tests, rather than
  a broad shared fixture, so a failing test's configuration is visible
  without cross-referencing an unrelated file, directly addressing the
  shared mega-stub misuse case in dimension 11.

## 16. Observability signals

A judgement-heavy dimension, said plainly here. A Stub exists purely inside
the test process and produces no production telemetry of its own. What can
be observed is the health of the test suite around it, and the boundary the
stub is standing in for, not a running production system.

What to record or watch.

- A ratio, tracked in continuous integration, of test cases per
  collaborator that stub it against test cases that exercise it for real in
  a contract or integration tier. A boundary with a rising stub count and a
  flat or zero real-test count is a growing blind spot, worth a dashboard
  panel or a simple lint rule that flags a collaborator with no
  corresponding real test anywhere in the repository.
- The age of any recorded or golden payload a stub's canned answer was
  originally seeded from. A payload left untouched for a long time against
  a collaborator whose real API is known to change frequently is a
  concrete signal to schedule a refresh.
- The location of test failures relative to the assertion line. A rising
  count of `AttributeError`, `undefined is not a function`, or a similar
  error surfacing inside the system under test rather than at the
  assertion is a proxy for the unconfigured-stub-method failure named in
  dimension 11, and suggests moving toward spec-bound stub construction.
- Time-to-green for the fast unit tier compared against the slower
  integration or contract tier, tracked over time. A unit tier that stays
  fast while an integration tier grows is the healthy shape this pattern
  is meant to produce. A unit tier that gradually slows down usually means
  a double still called a stub has quietly started doing real network or
  disk work.
- A count of assertions made directly against test-double objects,
  `.calledWith`, `.mock.calls`, an explicit `verify()`, inside test files
  whose doubles are named or documented as stubs. A nonzero count there is
  the naming-confusion smell named in dimension 11, and it is checkable
  with a simple, codebase-specific lint rule in most languages.

A healthy picture, stated as engineering judgement. a large, fast, reliably
passing unit tier built around narrowly configured stubs, a small,
deliberately slower and separately budgeted contract or integration tier
exercising the real boundaries those stubs stand in for, and near-zero
verification calls against any object the codebase itself labels a stub. An
unhealthy picture. a suite that stubs every external boundary with no
real-boundary tier anywhere at all, a stub payload that has clearly not been
touched in a long time next to a collaborator whose real documentation shows
frequent breaking changes, or a steadily rising count of assertions creeping
onto objects everyone still calls stubs.

## 17. Security and privacy implications

The pattern is close to silent on security in its classical, in-process,
test-only form, and it would be inventing a concern to claim otherwise. Two
genuine exposure points appear once a Stub is used carelessly, and are
named here because they recur in real codebases.

**Canned payloads carrying real data.** The most common real-world lapse is
not conceptual, it is a habit. an engineer captures a real response from a
staging or, worse, a production system, a real customer's record, a real
authentication token, a card number's last four digits, to seed a stub's
canned payload, and then commits that captured response directly into the
test suite's source tree, which is typically readable far more widely than
the production data store the payload came from in the first place. The fix
is to generate synthetic canned data, through a fixture library or a
faker-style generator, rather than sampling a real production response, and
where a genuinely captured real response is needed for shape fidelity, to
scrub every field that is not strictly required to exercise the code path
before it is committed.

**Stubs that quietly remove a real security check from coverage.** Stubbing
a collaborator responsible for authentication, authorization, or input
validation removes that check from the specific test entirely, which is
correct and expected for a unit test isolating unrelated business logic,
but becomes a real gap the moment the only tests covering that code path
are unit tests with the security-relevant collaborator stubbed out, and no
test anywhere exercises the real check. This is a specific instance of the
drift risk named in dimension 11, worth naming separately here because its
consequence is a security regression rather than a merely functional one,
and the fix is identical in shape, a deliberately scoped contract or
integration test that includes the security-relevant boundary at least
once.

On privacy the pattern itself is neutral, with one boundary worth stating
clearly. it has no runtime footprint and no network egress by definition,
unless the stub in question is the HTTP-level server variant from
dimension 8 and that server has been pointed at a real external endpoint
rather than answering entirely locally, in which case the ordinary
data-handling and endpoint-trust rules for that real endpoint apply
exactly as they would in production code, and the double should never be
assumed exempt from them merely because it lives inside a test file.

## Code examples

Three languages where the pattern is idiomatic in genuinely different ways.
TypeScript shows both the classical, class-based stub form and the
function-valued variant that first-class functions make available. Python
shows a hand-written stub alongside the standard library's `unittest.mock`
configured as a spec-bound stub, demonstrating the fail-fast property named
in dimension 11. Go shows a hand-written struct-based stub against a Go
interface, then the HTTP-level stub server variant using the standard
library's own `httptest` package. Java is omitted here because the
pattern's classical, class-based shape in Java is materially identical to
the TypeScript form already shown, and Rust and Swift are omitted because
neither adds an idiomatic variant beyond what the Go and TypeScript
examples already demonstrate for this particular pattern.

### TypeScript

The classical, class-based form.

```typescript
interface PaymentGateway {
  charge(amountCents: number): { approved: boolean; reference: string };
}

class StubPaymentGateway implements PaymentGateway {
  constructor(private readonly canned: { approved: boolean; reference: string }) {}
  charge(_amountCents: number): { approved: boolean; reference: string } {
    return this.canned;
  }
}

class OrderService {
  constructor(private readonly gateway: PaymentGateway) {}
  placeOrder(amountCents: number): string {
    const result = this.gateway.charge(amountCents);
    if (!result.approved) {
      throw new Error("payment declined");
    }
    return `order confirmed, ref ${result.reference}`;
  }
}

const stub = new StubPaymentGateway({ approved: true, reference: "ref-001" });
const service = new OrderService(stub);
console.log(service.placeOrder(1999));
```

The function-valued variant, no stub class at all, only a typed value.

```typescript
type ChargeFn = (amountCents: number) => { approved: boolean; reference: string };

class ParameterisedOrderService {
  constructor(private readonly charge: ChargeFn) {}
  placeOrder(amountCents: number): string {
    const result = this.charge(amountCents);
    if (!result.approved) {
      throw new Error("payment declined");
    }
    return `order confirmed, ref ${result.reference}`;
  }
}

const declined: ChargeFn = () => ({ approved: false, reference: "" });
const svc = new ParameterisedOrderService(declined);
try {
  svc.placeOrder(500);
} catch (e) {
  console.log((e as Error).message);
}
```

### Python

A hand-written stub next to a spec-bound `unittest.mock.Mock`, showing that
a call to a misspelled method fails immediately when the stub is bound to
the real interface's shape, rather than silently returning a fresh, useless
Mock.

```python
from dataclasses import dataclass
from unittest.mock import Mock


@dataclass
class ChargeResult:
    approved: bool
    reference: str


class PaymentGateway:
    def charge(self, amount_cents: int) -> ChargeResult:
        raise NotImplementedError


class StubPaymentGateway(PaymentGateway):
    def __init__(self, canned: ChargeResult) -> None:
        self._canned = canned

    def charge(self, amount_cents: int) -> ChargeResult:
        return self._canned


class OrderService:
    def __init__(self, gateway: PaymentGateway) -> None:
        self._gateway = gateway

    def place_order(self, amount_cents: int) -> str:
        result = self._gateway.charge(amount_cents)
        if not result.approved:
            raise ValueError("payment declined")
        return f"order confirmed, ref {result.reference}"


if __name__ == "__main__":
    stub = StubPaymentGateway(ChargeResult(approved=True, reference="ref-001"))
    service = OrderService(stub)
    print(service.place_order(1999))

    gateway_mock = Mock(spec=PaymentGateway)
    gateway_mock.charge.return_value = ChargeResult(approved=True, reference="ref-002")
    service2 = OrderService(gateway_mock)
    print(service2.place_order(2500))

    try:
        gateway_mock.chrage(100)
    except AttributeError as exc:
        print(f"caught typo early: {exc}")
```

### Go

A hand-written struct implementing a Go interface directly.

```go
package main

import "fmt"

type ChargeResult struct {
	Approved  bool
	Reference string
}

type PaymentGateway interface {
	Charge(amountCents int) ChargeResult
}

type StubPaymentGateway struct {
	Canned ChargeResult
}

func (s StubPaymentGateway) Charge(amountCents int) ChargeResult {
	return s.Canned
}

type OrderService struct {
	Gateway PaymentGateway
}

func (o OrderService) PlaceOrder(amountCents int) (string, error) {
	result := o.Gateway.Charge(amountCents)
	if !result.Approved {
		return "", fmt.Errorf("payment declined")
	}
	return fmt.Sprintf("order confirmed, ref %s", result.Reference), nil
}

func main() {
	stub := StubPaymentGateway{Canned: ChargeResult{Approved: true, Reference: "ref-001"}}
	service := OrderService{Gateway: stub}
	msg, err := service.PlaceOrder(1999)
	if err != nil {
		panic(err)
	}
	fmt.Println(msg)
}
```

The HTTP-level stub server variant, using the standard library directly, no
third-party dependency needed.

```go
package main

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
)

type apiResult struct {
	Approved  bool   `json:"approved"`
	Reference string `json:"reference"`
}

func chargeViaHTTP(url string, amountCents int) (apiResult, error) {
	resp, err := http.Get(fmt.Sprintf("%s/charge?amount=%d", url, amountCents))
	if err != nil {
		return apiResult{}, err
	}
	defer resp.Body.Close()
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return apiResult{}, err
	}
	var out apiResult
	if err := json.Unmarshal(body, &out); err != nil {
		return apiResult{}, err
	}
	return out, nil
}

func main() {
	stubServer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(apiResult{Approved: true, Reference: "ref-http-001"})
	}))
	defer stubServer.Close()

	result, err := chargeViaHTTP(stubServer.URL, 1999)
	if err != nil {
		panic(err)
	}
	fmt.Printf("approved=%v reference=%s\n", result.Approved, result.Reference)
}
```

## 18. References

1. Gerard Meszaros. *xUnit Test Patterns. Refactoring Test Code*.
   Addison-Wesley, 2007. The catalog source of the five-way test double
   taxonomy, Dummy, Fake, Stub, Spy, Mock Object, cited here through Martin
   Fowler's article and Wikipedia's corroborating attribution, since the
   book's own companion site could not be reached to verify a page number
   directly, so no page or chapter number is claimed.
2. Martin Fowler. "Mocks Aren't Stubs". Published 2 January 2007.
   https://martinfowler.com/articles/mocksArentStubs.html
   Verified 2026-08-02. Primary source for the direct quotations of
   Meszaros's Dummy, Fake, Stub, Spy, and Mock definitions, and for the
   classical versus mockist testing distinction used in dimension 3.
3. Wikipedia contributors. "Test double".
   https://en.wikipedia.org/wiki/Test_double
   Verified 2026-08-02. Corroborates the attribution of the five-way
   taxonomy to Meszaros and the 2007 Addison-Wesley publication.
4. Wikipedia contributors. "Method stub".
   https://en.wikipedia.org/wiki/Method_stub
   Verified 2026-08-02. Source for the older, broader software-engineering
   meaning of stub distinguished from the testing-pattern meaning in
   dimension 1.
5. Sinon.JS project. "Stubs".
   https://sinonjs.org/concepts/stubs
   Verified 2026-08-02. Source for the Sinon.js production use in
   dimension 9 and the stub definition quoted in dimension 1.
6. Python Software Foundation. Python 3 documentation, `unittest.mock`.
   https://docs.python.org/3/library/unittest.mock.html
   Verified 2026-08-02. Source for the standard library production use in
   dimension 9 and the `return_value` and `side_effect` configuration
   shown in the code example.
7. WireMock project. "Stubbing".
   https://wiremock.org/docs/stubbing/
   Verified 2026-08-02. Source for the HTTP-level stub server variant in
   dimension 8 and the WireMock production use in dimension 9.
8. The Go Authors. Go documentation, package `net/http/httptest`.
   https://pkg.go.dev/net/http/httptest
   Verified 2026-08-02. Source for the `httptest.NewServer` production use
   in dimension 9 and the HTTP-level code example.
9. OpenJS Foundation. Jest documentation, "Mock Functions".
   https://jestjs.io/docs/mock-function-api
   Verified 2026-08-02. Source for the Jest production use in dimension 9
   and the naming-confusion point made in dimension 1, where the page
   describes the mechanism as a mock function or spy and never uses the
   word stub.
