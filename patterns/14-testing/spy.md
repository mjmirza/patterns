---
name: Spy
slug: spy
family: 14-testing
category: Testing
aliases: [Test Spy, Recording Stub]
first_described: "Meszaros 2007"
maturity: canonical
related: [stub, mock-object, fake-object, dummy-object, dependency-injection]
incompatible_with: []
verified: 2026-08-02
---

# Spy

## 1. Name, aliases, and lineage

The canonical name is Spy, more precisely Test Spy to distinguish it from
surveillance software or the Observer-adjacent sense of "spying on" an object
informally. It is one of five test double roles catalogued by Gerard Meszaros
in *xUnit Test Patterns. Refactoring Test Code*, Addison-Wesley, 2007. Meszaros
groups Dummy, Fake, Stub, Spy, and Mock under the umbrella term Test Double, a
term he coined by analogy to a film stunt double, someone who stands in for an
actor in a dangerous scene. A test double stands in for a real collaborator
that is unavailable, slow, expensive, or nondeterministic in a test.

Martin Fowler summarized Meszaros's taxonomy in his widely cited 2007 article
"Mocks Aren't Stubs", stating it directly. "Spies are stubs that also record
some information based on how they were called. One form of this might be an
email service that records how many messages it was sent"
([martinfowler.com, Mocks Aren't Stubs](https://martinfowler.com/articles/mocksArentStubs.html),
verified 2026-08-02). Fowler's article is a widely cited secondary source for
this vocabulary alongside Meszaros's own book, and it is the source most
engineers actually read, so both are cited here because the community's
working definition traces through Fowler's restatement as much as through the
original text.

The alias Recording Stub appears in some testing literature and in early Ruby
and Python mocking library discussions, because a spy is mechanically a stub
(it returns a canned or a pass-through answer) with a recording capability
layered on top. The two names describe the same construct from two angles, one
from the vantage point of what it returns, the other from what it remembers.
There is no contested naming here in the way there is for, say, Factory versus
Simple Factory. The community converged on the term "spy" in Sinon.js, Jest,
Jasmine, Mockito, NSubstitute, and RSpec, all discussed in dimension 9, which
fixed the vocabulary in practice well beyond the academic source.

A spy is not a design pattern in the Gamma, Helm, Johnson, Vlissides sense. It
does not describe a recurring structure inside production object collaboration.
It describes a recurring structure inside TEST code, specifically the shape a
test double takes when a test needs to verify HOW a collaborator was used
rather than only what it returned. This entry treats it as a first class
pattern because the distinction between a Spy and its sibling doubles, Stub,
Fake, Mock, and Dummy, is exactly the kind of decision that benefits from a
structured entry. Engineers reach for "mock" as a catch-all term for every test
double, and the resulting tests either verify too much, verify too little, or
verify the wrong thing entirely, a failure mode dimension 11 covers directly.

## 2. Problem and context

A unit under test collaborates with something outside itself, a payment
gateway, an email service, a logger, an event bus, a cache. Two different
questions can be asked about that collaboration.

- What did the collaborator return, and did the unit under test do the right
  thing with that return value? This is a question about STATE, answerable by
  inspecting the unit's resulting state or its own return value.
- Did the unit under test actually CALL the collaborator, with what
  arguments, how many times, and in what order relative to other calls? This
  is a question about BEHAVIOR, unanswerable by inspecting state alone,
  because the collaborator's side effect (the email that was sent, the log
  line that was written, the webhook that fired) may not be observable
  through the unit's own return value at all.

The second question is the one a Spy exists to answer. Consider a
`registerUser` function that, on success, must send a welcome email through an
`EmailService`. The function's return value might simply be the newly created
user record. Nothing about that return value tells a test whether the email
was actually requested. Calling the real `EmailService` in a test is
undesirable for the reasons every test double exists. It is slow, a real SMTP
round trip. It has an external side effect that should not run once per test
suite execution, a real person receiving a test email. And it can fail for
reasons unrelated to the code under test, an expired SMTP credential, a
network partition. The context that creates the need for a Spy specifically,
as opposed to a Stub, is the shift from "what value came back" to "was this
called, and how".

The context also includes a governance dimension. A Spy is usually built by
wrapping a REAL implementation, or a working fake, and recording invocations
transparently on top, rather than replacing the implementation's behavior
entirely the way a Stub or a Mock typically does. This preserves realistic
pass-through behavior (dimension 8 covers both the wrapping variant and the
pure-recording variant) while adding the missing observability. That is why
Sinon.js can spy on an ALREADY EXISTING function without replacing it, and why
Python's `unittest.mock.Mock(wraps=real_object)` explicitly documents this
pass-through behavior, verified in dimension 9.

## 3. Forces

- **Behavior visibility versus implementation coupling.** A Spy makes the fact
  that "the unit called the collaborator with these arguments" observable to
  the test, which is exactly what is needed to verify a fire-and-forget side
  effect. The cost is that the test now depends on the shape of the
  collaboration itself, the method name, its argument order, how many times it
  is invoked, so a refactor that preserves the observable OUTCOME but changes
  the INTERNAL sequence of calls can break tests that were never wrong. This
  is the core tension of behavior verification generally, and a Spy sits on
  the more coupled end of the double spectrum, less coupled than a strict Mock
  with pre-set expectations, more coupled than a pure state-based Stub.
- **Real behavior versus test isolation.** Because a Spy commonly wraps a real
  or a working-fake implementation rather than replacing it outright, it
  preserves realistic behavior (the wrapped email service still validates the
  recipient address format, still throws on a malformed address) while adding
  recording. The forfeited force is isolation. A test using a wrapping Spy can
  still be affected by a bug in the wrapped collaborator, which a pure Stub
  that returns a fixed canned value would never expose.
- **Assertion timing versus setup ceremony.** A Spy defers its assertions to
  the end of the test, after the action under test has run, the same way a
  Stub does. This is lighter ceremony than a strict Mock, which typically
  wants its expectations declared BEFORE the action runs, `when(...).thenCall`
  followed later by `verify(...)`. It reads closer to how most engineers
  naturally think about a test, arrange, act, assert. The force sacrificed is
  the earlier failure signal a pre-declared Mock can give when an unexpected
  call happens mid-test. A Spy only tells you afterward.
- **Cognitive load versus fidelity of intent.** "Spy on this function" is an
  easy mental model, wrap it, remember what happened, ask about it later. This
  keeps the cognitive load of writing the test low. The cost is that a Spy
  answers "was this called correctly" without answering "was this the RIGHT
  thing to call given the domain rules", a distinction dimension 11 explores
  under the false-confidence failure mode.

## 4. Applicability and non-applicability

When to reach for a Spy.

- The behavior under test has a side effect on a collaborator that produces no
  directly observable return value the test can assert on, sending a message,
  writing a log line, publishing an event, calling an analytics tracker,
  invalidating a cache entry.
- You need to verify the ARGUMENTS a collaborator was called with, not merely
  that it was called, for example asserting an audit log call carried the
  correct actor ID and timestamp field.
- You need to verify call COUNT or call ORDER, for example that a retry
  wrapper called the underlying operation exactly three times before giving
  up, or that a transaction's `commit` was called after its `prepare`.
- You want the real implementation, or a faithful working fake of it, to still
  run during the test, because part of what you are verifying is that the
  real behavior was triggered at all, not merely that some call happened. A
  wrapping Spy over a real in-memory cache is the natural fit. A pure Stub
  that fakes the cache's return value cannot answer "was the cache actually
  invalidated".
- You are retrofitting tests onto legacy code with no seams for dependency
  injection, and monkey-patching a method to both record calls and delegate to
  the original is the lowest-friction way to add characterization coverage
  before a refactor, the technique Michael Feathers describes generally in
  *Working Effectively with Legacy Code*, Prentice Hall, 2004, chapter 4, "The
  Seam Model", as the class of tests that observe existing behavior before it
  is changed.

When NOT to reach for a Spy.

- The question the test needs answered is purely "what value came back",
  answerable from the return value or the resulting state of the unit under
  test. Reaching for a Spy here adds a behavior-verification dependency the
  test does not need. A plain Stub, or no double at all, is simpler and less
  brittle. This is the single most common misuse this entry documents, covered
  further in dimension 11.
- The collaborator is a pure, side-effect-free function with a deterministic
  return value for a given input, for example a currency formatter or a hash
  function. Calling the real thing is cheap, fast, and adds no test fragility.
  Wrapping it in a Spy only to assert it was called adds ceremony with no
  payoff, because the return value already proves the call happened
  correctly.
- You are about to assert an EXACT sequence of low-level calls into a
  third-party library you do not own, for example asserting an ORM issued
  exactly this SQL string in this order. That test is now coupled to the
  library's internal implementation, not to your code's contract with it, and
  it will break on a library upgrade that changes nothing observable to a
  caller. Assert on the outcome, the row exists, the row does not exist,
  instead, or spy at the boundary you actually own (your repository interface)
  rather than the library's internals.
- The system under test genuinely needs a full behavioral CONTRACT enforced
  before the action runs, meaning the test should fail immediately and loudly
  if an unexpected interaction happens during the action, not merely be
  silently recorded for a later assertion. That stricter contract is what a
  Mock (dimension 13) is for. Using a Spy here weakens the test's ability to
  catch the defect at the moment it happens.
- You find yourself spying on three, four, or five collaborators inside one
  test to reconstruct an entire internal call graph. That is usually a signal
  the unit under test has too many responsibilities, and the fix is to split
  it, not to add more spies.

## 5. Structure

- **Subject Under Test (SUT).** The unit whose behavior is being verified. It
  holds a reference to a collaborator, typically through a constructor
  parameter, a method parameter, or a property, obtained via dependency
  injection or a seam introduced specifically for testability.
- **Collaborator Interface.** The contract the SUT depends on, expressed as an
  interface, a protocol, an abstract base class, or in a dynamically typed
  language simply the expected method surface. The SUT is coded against this
  contract, never against a concrete implementation directly, which is what
  makes substitution possible.
- **Spy.** An object that implements the Collaborator Interface (or, in
  languages that permit runtime monkey-patching, wraps an existing concrete
  instance without needing a matching interface at all). Internally it holds a
  Call Log and, optionally, a reference to a Delegate.
- **Call Log.** The recorded history of invocations. For each call, the method
  name, the arguments, the call order relative to other calls, and optionally
  the return value produced. This is what dimension 7 shows populated at
  runtime and what the test inspects during the assert phase.
- **Delegate (optional).** The real implementation, or a working fake, that
  the Spy forwards calls to after recording them. Present in the wrapping
  variant of a Spy. Absent in the pure-recording variant, where the Spy
  returns a fixed or default value itself, behaving like a Stub with a
  memory.
- **Test.** The test method itself, which plays three roles in sequence.
  Arranger constructs the SUT with the Spy installed as its collaborator.
  Actor invokes the behavior under test. Asserter inspects the Spy's Call Log
  after the action completes, using assertions such as "was called once",
  "was called with these arguments", or "was called after that other call".

## 6. ASCII structure diagram

```
+----------------------+          +--------------------------+
|   Test (Arrange/      |          |   Collaborator Interface |
|   Act/Assert)         |          |   (e.g. EmailService)    |
+-----------+-----------+          +-------------+------------+
            |                                    ^
            | constructs, installs               | implements
            v                                    |
+----------------------+          +--------------+------------+
|   Subject Under Test  |--------->|          Spy              |
|   (e.g. UserRegistrar)|  calls   |  +---------------------+  |
+----------------------+          |  |     Call Log         |  |
            ^                     |  | [ (send, args, t0) ]  |  |
            | inspects            |  +---------------------+  |
            | Call Log after act  |  optional forward to     |
            +---------------------+   Delegate below --------+ |
                                   +--------------------------+ |
                                                                 |
                                                                 v
                                                    +-------------------+
                                                    | Delegate (real or |
                                                    | working fake)     |
                                                    +-------------------+
```

## 7. Dynamics

```
Test           SUT              Spy              Call Log        Delegate
 |  construct   |                |                  |               |
 |------------->|                |                  |               |
 |  install Spy as collaborator  |                  |               |
 |------------------------------>|                  |               |
 |                                |                  |               |
 |  act call SUT.registerUser()  |                  |               |
 |------------->|                |                  |               |
 |               |  call send(to, subject)           |               |
 |               |------------------------------->  |               |
 |               |                | record(call)     |               |
 |               |                |----------------->|               |
 |               |                | forward if wrapping variant       |
 |               |                |----------------------------------->|
 |               |                |                  |     execute    |
 |               |                |  <---------------------------------|
 |               |  <---------- return                |               |
 |  <---------- return (user record)                  |               |
 |                                |                  |               |
 |  assert was send() called with (to, subject)?       |               |
 |------------------------------------------------->  |               |
 |  <------------------------------------------------ answer          |
```

The two moments that matter are marked in the sequence. The record step
happens INSIDE the Spy's implementation of the collaborator method, before any
forwarding, so the Call Log is populated even if the delegate throws. The
assert step happens strictly AFTER the act step returns to the test, which is
what separates a Spy's deferred, post-hoc verification style from a Mock's
typically pre-declared, fail-fast style discussed in dimension 13.

## 8. Implementation variants

- **Wrapping spy over a real object.** The Spy holds a reference to the real
  collaborator and forwards every call after recording it. Sinon.js's
  `sinon.spy(object, "method")` and Jest's `jest.spyOn(object, methodName)`
  both default to this shape, calling the original method unless the test
  explicitly overrides the implementation with `mockImplementation`, a
  behavior documented directly in Jest's own reference for `jest.spyOn`
  ([jestjs.io, jest object reference](https://jestjs.io/docs/jest-object#jestspyonobject-methodname),
  verified 2026-08-02). This variant is closest to Fowler's "stub that also
  records" definition when the wrapped object is itself a Stub, and closest to
  a full behavioral pass-through when the wrapped object is the genuine
  production implementation.
- **Pure recording spy, no delegate.** The Spy implements the interface but
  never forwards to anything. It returns a fixed or default value and only
  records. This is the shape you build by hand in languages with structural
  typing when you construct a small class implementing an interface purely
  for a test, with no constructor argument for a real implementation to wrap.
  It behaves exactly like a Stub with an added Call Log.
- **Partial mock, spy with stubbing.** Some or all methods on the spy are
  explicitly given canned return values, stubbed, while the object as a whole
  still records every call for later verification, and unstubbed methods fall
  through to the real implementation. Mockito's `Mockito.spy(realObject)`
  combined with `when(spy.someMethod()).thenReturn(value)` is this exact
  shape. Mockito's own documentation frames `spy()` as "partial mocking, real
  methods are invoked but still can be verified and stubbed"
  ([site.mockito.org](https://site.mockito.org/), verified 2026-08-02).
- **Language-native call tracking.** Python's `unittest.mock.Mock` tracks
  every call automatically through `call_args`, `call_count`, and
  `call_args_list` regardless of whether the mock is standalone or wraps a
  real object, and gains the wrapping spy shape specifically through the
  `wraps=` constructor parameter, which the standard library documentation
  states passes calls through to the wrapped object while keeping the mock's
  full call-tracking API intact
  ([docs.python.org, unittest.mock](https://docs.python.org/3/library/unittest.mock.html),
  verified 2026-08-02). Here the recording capability is a property of every
  Mock instance rather than a separate named construct, which is why Python
  engineers often say "just use a Mock" for what other ecosystems would call
  a Spy specifically. The distinction collapses at the library level and is
  recovered only through how the test uses the object, asserting on calls
  (spy usage) versus pre-programming return values and letting the SUT's
  output carry the assertion (stub usage).
- **Monkey-patch spy for legacy code.** In dynamically typed languages, or in
  languages with method-swizzling facilities, a spy can be installed by
  replacing a method on an existing object or class at runtime, recording
  invocations, and calling the original function saved by closure before the
  patch. This requires no interface and no constructor injection, which is
  precisely why it is the standard tool for adding characterization coverage
  to legacy code that was never built with test seams, the situation Feathers
  addresses at length in *Working Effectively with Legacy Code*, Prentice
  Hall, 2004.
- **Compile-time generated spy.** In statically typed, ahead-of-time compiled
  languages without runtime reflection convenient enough for dynamic proxying,
  Rust and, to a lesser extent, Go, the spy is generated at compile time. A
  struct implementing the collaborator trait or interface, with each method
  appending to an internal vector or slice before returning a
  programmer-supplied canned value. This variant trades runtime flexibility
  for compile-time type safety and zero reflection overhead, at the cost of
  hand-writing, or code-generating via a macro or `go generate` directive, the
  spy type per interface rather than obtaining it generically from a mocking
  framework.

## 9. Known production uses

- **Sinon.js**, the JavaScript standalone test double library, ships
  `sinon.spy()` as one of its three core primitives alongside stubs and mocks,
  documented as wrapping a function to record its calls, arguments, return
  values, and thrown exceptions while still invoking the wrapped function by
  default. Sinon spies are used across the Node.js ecosystem independent of
  any particular test runner. Source. Sinon.js official documentation, spies
  page, https://sinonjs.org/concepts/spies/, verified 2026-08-04.
- **Mockito's `spy()` / `@Spy`**, the dominant Java mocking framework, offers
  partial mocking through `Mockito.spy(realObject)` and the `@Spy` annotation,
  explicitly stated on Mockito's own site as "partial mocking, real methods
  are invoked but still can be verified and stubbed"
  ([site.mockito.org](https://site.mockito.org/), verified 2026-08-02).
  Mockito is the standard mocking library bundled by default with Spring Boot
  Test starters, making its `spy()` construct one of the most widely executed
  test-double implementations in the Java enterprise ecosystem.
- **Jest's `jest.spyOn`**, the built-in test double facility of the Jest
  testing framework maintained under the OpenJS Foundation, creates a mock
  function that tracks calls to an existing object method while by default
  still invoking the real implementation, documented directly in Jest's
  reference documentation for the `jest` global object
  ([jestjs.io, jest object](https://jestjs.io/docs/jest-object#jestspyonobject-methodname),
  verified 2026-08-02). Jest is the default test runner scaffolded by Create
  React App and is bundled or recommended by numerous major JavaScript
  frameworks' testing guides.
- **Python's `unittest.mock.Mock(wraps=...)`**, part of the Python standard
  library since Python 3.3, provides spy behavior natively. Every `Mock`
  instance tracks `call_count`, `call_args`, and `call_args_list`
  automatically, and the `wraps` constructor parameter causes calls to pass
  through to a real wrapped object while retaining full call-tracking,
  documented in the official Python standard library reference
  ([docs.python.org, unittest.mock](https://docs.python.org/3/library/unittest.mock.html),
  verified 2026-08-02). Because `unittest.mock` ships in the standard library,
  this is arguably the single most executed spy implementation in the Python
  ecosystem, with no external dependency required.

## 10. Consequences

Positive.

- Makes side-effecting collaboration observable to a test without requiring
  the collaborator's real infrastructure, a real SMTP server, a real message
  queue, to be present during the test run.
- Preserves realistic behavior when used in the wrapping variant, because the
  real or a faithfully working implementation still executes, catching
  defects a pure Stub's canned return value would hide.
- Lower ceremony than a strict Mock for the common case, because assertions
  are written after the action runs, matching the natural arrange-act-assert
  shape most engineers already use.
- Gives a precise, inspectable record, arguments, count, order, that can
  answer several different questions from a single recorded interaction,
  useful when a test wants to check both "was it called" and "with what" in
  one pass.
- Provides the lowest-friction technique for adding characterization tests to
  legacy code with no dependency-injection seams, through the monkey-patch
  variant, unblocking safe refactoring of code nobody currently dares to
  touch.

Negative.

- Couples the test to the SHAPE of the collaboration, method name, argument
  order, call count, rather than to the outcome, so refactors that preserve
  behavior but change the internal call sequence can break passing tests that
  were never actually wrong, a cost formally named implementation coupling.
- Encourages over-verification. Because recording every call is nearly free
  once a spy is in place, tests accumulate assertions on incidental calls that
  have nothing to do with the behavior under test, producing brittle tests
  that fail on unrelated refactors, covered as a named failure mode in
  dimension 11.
- When used in the wrapping variant against a real collaborator, the test's
  isolation guarantee weakens. A bug or a slow path inside the wrapped
  collaborator can now cause the test to fail or run slowly, defeating one of
  the primary reasons to use a test double in the first place.
- Reads, in ecosystems that collapse spy and mock into one library construct,
  Python's `Mock`, Java's Mockito `mock()` object which can ALSO record calls
  even when used purely for stubbing, as a single undifferentiated tool,
  which erodes the useful conceptual distinction between state verification
  and behavior verification and leads engineers to default to behavior
  verification even when a state-based assertion would be simpler and more
  resilient.

## 11. Failure modes and misuse

Symptom. A passing test suite that still lets a real defect through, where the
defect is a wrong VALUE the collaborator returned, not a wrong CALL.

Cause. The test spies on a collaborator, asserts only that it was called with
the right arguments, and never actually checks what the collaborator returned
or what the SUT did with that return value. The spy answers "did you ask
correctly" but the test never checks "did you do the right thing with the
answer".

Fix. After asserting the call happened, also assert on the SUT's resulting
state or return value that depends on the collaborator's response, or, when
the collaborator's return value genuinely does not affect the outcome being
tested, drop the behavior assertion and rely on a plain Stub instead, since a
Spy that never inspects its own recorded return values is doing unnecessary
work.

Symptom. A test suite where a harmless internal refactor, changing the order
two independent side-effecting calls happen in, or combining two separate
calls to the same collaborator into one batched call, breaks a large number of
unrelated tests, even though the observable outcome for every caller of the
refactored code is identical.

Cause. Spy assertions were written against the exact call sequence or call
count of a collaborator rather than against the eventual observable state or
side effect, effectively pinning the SUT's internal implementation strategy
inside the test. This is the textbook over-specification failure mode
Meszaros describes generally as Overspecified Software under the broader
"Fragile Test" problem in *xUnit Test Patterns*, chapter 16.

Fix. Relax the assertion to what the caller of the SUT actually depends on. If
no external observer can tell the difference between one call and two calls to
the collaborator, do not assert on the count. Assert on cumulative effect,
total email content sent, final cache state, rather than on the literal
sequence of calls that produced it, unless the SEQUENCE ITSELF is the actual
contract being tested, for example when testing a two-phase-commit protocol
where call order genuinely is the specification.

Symptom. A spy that silently and incorrectly reports "not called" for a
method, even though the real code path clearly executes it, most commonly seen
when spying on a method that is called on a DIFFERENT reference than the one
the spy was installed on.

Cause. The collaborator was captured or re-assigned to a local variable, a
closure, or a different object instance BEFORE the spy was installed, or the
spied-on object was replaced by a factory or a dependency-injection container
returning a fresh instance each time, so the spy's Call Log tracks a different
object than the one actually invoked at runtime. Sinon and Jest both document
this precisely. Spying on `object.method` records calls made THROUGH
`object.method`, not calls made through a reference to the original function
captured elsewhere before the spy was attached.

Fix. Verify the spy is installed on the exact object instance the SUT holds a
reference to at call time, install the spy before any code captures a
reference to the original method, and prefer spying through
constructor-injected collaborators over spying on module-level or
statically-referenced functions, which are the most common source of a
reference mismatch.

Symptom. The same collaborator is spied on inside dozens of unrelated tests
across the codebase, and a future engineer changing the collaborator's method
signature must update dozens of test files even though the collaborator's
actual CONTRACT with its callers did not meaningfully change.

Cause. No shared test-double factory or builder exists for the commonly spied
collaborator, so each test author hand-rolls their own spy setup, duplicating
both the construction logic and the coupling to the exact method signature.

Fix. Extract a single, shared spy-construction helper, a Test Data Builder or
an Object Mother, per Meszaros's naming for shared test fixture construction,
for any collaborator spied on in more than a small handful of tests, so a
signature change requires editing one factory function rather than every call
site.

## 12. Trade-off matrix

| Force | Spy | Stub | Mock | Fake |
|---|---|---|---|---|
| Verifies behavior, was it called, with what | Yes, after the fact | No, state only | Yes, pre-declared, fail-fast | No, state only |
| Verifies state or return value | Optional, depends on delegate | Yes, primary purpose | Rare, secondary | Yes, primary purpose |
| Runs real or realistic logic | Often, in wrapping variant | No, canned answers only | No, canned answers only | Yes, working shortcut logic |
| When assertions are written | After the action runs | Rarely asserted on directly | Before the action runs | After the action runs |
| Coupling to collaborator's internal call shape | Moderate to high if over-asserted | Low | High, expectations declared up front | Low |
| Typical cost to build | Low, often one line via a framework | Low | Low to moderate, framework-provided | Moderate to high, hand-written working logic |
| Best suited for | Verifying an otherwise unobservable side effect happened correctly | Supplying a needed but irrelevant return value | Enforcing a strict, known interaction contract | Standing in for a heavy dependency with real, simplified behavior, an in-memory DB |

## 13. Related and incompatible patterns

- **Stub.** A Spy is structurally a Stub with a Call Log added. Every Spy that
  never forwards to a delegate IS a Stub the moment you stop asking it what
  was called, and conversely a Stub becomes a Spy the instant a test starts
  asserting on its recorded calls rather than only consuming its canned
  return value. The two are frequently the same object playing two different
  roles depending on what the test does with it, which is exactly why
  Fowler's definition phrases Spy as "stubs that also record".
- **Mock Object.** Both a Spy and a Mock perform behavior verification, but a
  Mock's expectations are typically declared BEFORE the action under test
  runs, and a violated expectation can fail the test immediately, during the
  action, rather than only when explicitly asserted afterward. A Spy defers
  everything to an explicit assertion call after the action. Some frameworks,
  Mockito, Jest, blur this line by letting the same underlying object be used
  in either style, but the two remain conceptually distinct roles for the
  double, not distinct classes of object.
- **Fake Object.** A Fake provides a working, simplified implementation, an
  in-memory list standing in for a database table, and is usually consumed
  purely for its STATE behavior. A Fake can be wrapped by a Spy when a test
  needs both realistic working behavior AND call-level verification
  simultaneously, making Fake-wrapped-by-Spy a common composite in practice.
- **Dummy Object.** A Dummy is passed only to satisfy a parameter list and is
  never meaningfully called. A test that finds itself asserting on a Dummy's
  calls has almost certainly misclassified it, since a genuinely unused
  parameter should never need a Spy at all.
- **Dependency Injection.** A Spy's applicability depends heavily on the SUT
  obtaining its collaborator through an injectable seam, a constructor
  parameter, a method parameter, or a factory the test can override, rather
  than through a hard-coded concrete instantiation. Dependency Injection is
  the enabling precondition for the cleanest, non-monkey-patched Spy variants.
- **Adapter.** When the collaborator being spied on is a third-party library
  with no natural seam, teams often introduce an Adapter around the library
  first, then spy on the Adapter's narrow, owned interface rather than on the
  library's broad internal surface, which keeps the spy's assertions coupled
  to a contract the team actually controls rather than to the library's
  implementation details, directly addressing the non-applicability point in
  dimension 4 about not asserting on a library's internals.
- **Observer.** Conceptually adjacent, both involve "noticing that something
  happened", but structurally unrelated. Observer is a production
  collaboration pattern where a subject actively notifies registered
  listeners. A Spy is a passive recording substitute installed only for a
  test's lifetime and is never wired into production code.

## 14. Refactoring path in and out

Introducing a Spy into code that currently has no test seam for its
collaborator.

1. Identify the collaborator call whose occurrence, arguments, or count needs
   verifying, and confirm no existing assertion already covers it through a
   simpler state check, per dimension 4's non-applicability list. Do not skip
   this check.
2. If the SUT currently constructs its collaborator internally rather than
   receiving it, introduce a seam. Extract the collaborator's construction
   into a constructor parameter, a method parameter, or a factory function the
   test can override. This is the classic "Extract and Override" or
   "Parameterize Constructor" seam-introduction technique Feathers describes
   for legacy code in *Working Effectively with Legacy Code*, Prentice Hall,
   2004.
3. In the test's arrange phase, construct a Spy, choosing the wrapping variant,
   a spy over a real or fake instance, when the test also needs realistic
   behavior, or the pure-recording variant when only the call itself matters.
4. Install the Spy as the SUT's collaborator through the seam from step 2.
5. Act. Invoke the behavior under test exactly as before.
6. Assert on the Spy's Call Log. Was the expected method called, with what
   arguments, how many times, and, if relevant, in what order relative to
   other recorded calls.
7. Where a monkey-patched spy was used as a stopgap, no seam existed yet, and
   time pressure ruled out step 2 immediately, track it as technical debt and
   schedule the seam-introduction refactor separately once characterization
   coverage from the monkey-patched spy is in place and safely committed.

Removing a Spy once its usefulness has expired, typically because the behavior
it verifies has since become observable through state, or because the
collaboration it recorded was refactored away entirely.

1. Confirm the assertion the Spy currently supports is either redundant with a
   state-based assertion already present elsewhere in the same test, or is
   testing an interaction that no longer exists after a refactor.
2. If redundant, delete the Spy-based assertion and the Spy installation,
   leaving the simpler state-based assertion as the sole check. This directly
   reverses the misuse pattern in dimension 11's first failure mode.
3. If the collaboration itself was refactored away, the SUT no longer calls
   that collaborator at all because the responsibility moved elsewhere, the
   Spy's continued presence in the test is dead weight. Remove it and, if the
   moved responsibility is now tested elsewhere, confirm coverage exists
   there instead of assuming it does.
4. Where a shared spy-construction helper, the fix from dimension 11's fourth
   failure mode, was in use only by the test being cleaned up, remove the
   helper too, rather than leaving an unused factory function behind.

## 15. Testing and verification

Meszaros's own framing is worth stating precisely, because it is the point
most misapplied in practice. A Spy is itself a piece of TEST infrastructure,
and the question "how do I test the Spy" mostly does not arise the way it does
for production code, because the Spy's correctness is exercised implicitly by
every test that uses it. What DOES need attention is verifying that the Spy is
recording the right thing.

A common technique, sometimes called a "self-checking spy", verifying the
spy's own Call Log directly in a small dedicated test, is worth applying when
a spy-construction helper, per the shared-factory fix in dimension 11, is
introduced, because a bug in a widely shared spy helper silently weakens every
test that depends on it. Write one small, direct test asserting that calling
the helper's spy through its collaborator interface correctly appends to the
Call Log with the right shape, before trusting it across the rest of the
suite.

What a Spy makes EASIER to test. Any behavior whose only observable trace is a
side effect on a collaborator, previously untestable without standing up the
real collaborator's infrastructure.

What becomes HARDER. Mutation testing and refactoring confidence specifically,
because spy-based assertions that over-specify call shape, dimension 11's
second failure mode, actively resist safe refactoring, the opposite of what a
good test suite should provide. A test suite heavy on over-specified spies
tends to show a worse score on a mutation-testing run than an equivalent suite
using state-based assertions, because many surviving mutants, code changes
that preserve observable behavior but change internal call shape, will
correctly NOT be caught by state assertions, while an over-specified spy suite
will show FALSE failures on those same harmless mutants, in the opposite
direction from what mutation testing is meant to surface. This observation
about the interaction is engineering judgement drawn from general
mutation-testing practice, not a specific cited study of spy-based suites.

Test doubles that record and verify order specifically, the call-order
assertion variant in dimension 6, benefit from being tested with an explicit
ordering-violation case during the helper's own development. Deliberately
call the spy out of order once, confirm the order assertion correctly fails,
then confirm it correctly passes when called in order. This mirrors the
general test-the-test-infrastructure discipline recommended broadly across
testing literature for any shared assertion helper.

## 16. Observability signals

A Spy exists entirely within the test process and does not itself emit
production telemetry, so "observability" here means what the TEST OUTPUT
should surface, not a production dashboard signal, and what the presence of
excessive spying in a codebase signals about the codebase's health.

- A healthy spy-based test failure message names the exact expected call,
  method, arguments, expected count, alongside the exact recorded calls that
  actually happened, so a developer can diagnose a broken test from the
  failure message alone without re-running the debugger. Most mocking
  frameworks, Sinon, Jest, Mockito, print this automatically. A hand-rolled
  spy that only reports "assertion failed" with no detail is a maintenance
  liability and should be flagged in code review.
- A rising RATIO of spy-based (behavior) assertions to state-based assertions
  across a codebase's test suite over time, tracked as a simple grep-based
  metric, count of `verify(`, `expect(spy`, `assert_called` occurrences versus
  count of plain value assertions, is a useful codebase-health signal. A
  steadily climbing ratio often correlates with the over-specification failure
  mode in dimension 11 becoming systemic rather than occasional, and is worth
  a periodic audit.
- Flaky spy assertions, a spy-based assertion that intermittently fails on
  call ORDER or call COUNT in a codebase involving concurrency or asynchronous
  code, are a strong signal that the spy's assumptions about single-threaded,
  deterministic call sequencing do not hold for the SUT being tested, and that
  either the SUT needs synchronization made explicit in the test, awaiting a
  promise, joining a goroutine, or the assertion needs to tolerate the actual
  concurrent ordering rather than assume one specific sequence.

## 17. Security and privacy implications

A Spy that wraps a REAL collaborator in the pass-through variant will forward
whatever arguments the SUT passes it, including sensitive data, credentials,
personal information, payment details, if the SUT under test happens to
construct them during the test run, and record those arguments verbatim in
its Call Log for the duration of the test process. Where a test suite prints
failing assertion diffs to CI logs, an accidentally sensitive value captured
in a spy's Call Log can end up recorded in CI log output or in a test report
artifact, which is a real, if easily overlooked, data-handling implication.
Test fixtures for spy-based tests involving anything resembling production-
shaped sensitive data should use synthetic values, not values copied from a
real production dataset, the same discipline any test fixture should follow
regardless of whether a Spy is involved.

Where a monkey-patched spy variant, dimension 8, is used against a security-
sensitive method, for example a spy installed over an authentication or
authorization check purely to verify it was called, care is needed that the
patch is fully reverted after the test, because a monkey-patch left installed
across test boundaries, a common bug when a test framework's teardown or
`afterEach` cleanup is skipped or misconfigured, can silently weaken or bypass
that real check for SUBSEQUENT tests running in the same process, producing
false-positive test passes for security-relevant behavior that was, for the
remainder of the test run, no longer actually being exercised.

Beyond these two operational concerns, a Spy introduces no attack surface of
its own. It exists only inside the test process, is never compiled or shipped
into a production artifact in any of the mainstream frameworks discussed in
dimension 9, and carries no network, storage, or execution privileges beyond
what the test process itself already has.

## Code examples

Three languages showing three different mechanical shapes a spy takes. Go
shows the compile-time generated variant, a hand-written struct with a
delegate and a recorded call slice, because Go has no reflection-based mocking
convention in its standard library. TypeScript shows the same wrapping shape
with structural interfaces. Python shows the language-native shape, close to
what `unittest.mock.Mock(wraps=...)` gives for free in the standard library,
written out by hand here so the mechanism stays visible rather than hidden
inside a library call.

### TypeScript

```typescript
interface EmailService {
  send(to: string, subject: string): void;
}

class RealEmailService implements EmailService {
  send(to: string, subject: string): void {
    if (!to.includes("@")) {
      throw new Error("invalid address");
    }
    console.log(`sending "${subject}" to ${to}`);
  }
}

interface Call {
  method: string;
  args: unknown[];
}

class EmailServiceSpy implements EmailService {
  readonly calls: Call[] = [];
  private readonly delegate: EmailService;

  constructor(delegate: EmailService) {
    this.delegate = delegate;
  }

  send(to: string, subject: string): void {
    this.calls.push({ method: "send", args: [to, subject] });
    this.delegate.send(to, subject);
  }

  wasCalledWith(to: string, subject: string): boolean {
    return this.calls.some(
      (c) => c.method === "send" && c.args[0] === to && c.args[1] === subject
    );
  }
}

interface User {
  email: string;
}

function registerUser(email: string, emailService: EmailService): User {
  const user: User = { email };
  emailService.send(email, "Welcome");
  return user;
}

// arrange, act, assert. the spy wraps the real service so the real
// validation path still runs, and it also records what was called.
const spy = new EmailServiceSpy(new RealEmailService());
const user = registerUser("ada@example.com", spy);

if (spy.calls.length !== 1) {
  throw new Error("send should be called exactly once");
}
if (!spy.wasCalledWith("ada@example.com", "Welcome")) {
  throw new Error("send should carry the new user's address and subject");
}
console.log("TypeScript spy test passed for", user.email);
```

### Python

```python
from dataclasses import dataclass


class EmailService:
    def send(self, to: str, subject: str) -> None:
        raise NotImplementedError


class RealEmailService(EmailService):
    def send(self, to: str, subject: str) -> None:
        if "@" not in to:
            raise ValueError("invalid address")
        print(f'sending "{subject}" to {to}')


@dataclass
class Call:
    method: str
    args: tuple


class EmailServiceSpy(EmailService):
    def __init__(self, delegate: EmailService) -> None:
        self._delegate = delegate
        self.calls: list[Call] = []

    def send(self, to: str, subject: str) -> None:
        self.calls.append(Call("send", (to, subject)))
        self._delegate.send(to, subject)

    def was_called_with(self, to: str, subject: str) -> bool:
        return any(
            c.method == "send" and c.args == (to, subject) for c in self.calls
        )


@dataclass
class User:
    email: str


def register_user(email: str, email_service: EmailService) -> User:
    user = User(email=email)
    email_service.send(email, "Welcome")
    return user


spy = EmailServiceSpy(RealEmailService())
user = register_user("ada@example.com", spy)

assert len(spy.calls) == 1, "send should be called exactly once"
assert spy.was_called_with("ada@example.com", "Welcome"), (
    "send should carry the new user's address and subject"
)
print("Python spy test passed for", user.email)
```

### Go

```go
package main

import (
	"errors"
	"fmt"
	"strings"
)

type EmailService interface {
	Send(to, subject string) error
}

type RealEmailService struct{}

func (RealEmailService) Send(to, subject string) error {
	if !strings.Contains(to, "@") {
		return errors.New("invalid address")
	}
	fmt.Printf("sending %q to %s\n", subject, to)
	return nil
}

type call struct {
	method string
	to     string
	subj   string
}

type EmailServiceSpy struct {
	delegate EmailService
	calls    []call
}

func NewEmailServiceSpy(delegate EmailService) *EmailServiceSpy {
	return &EmailServiceSpy{delegate: delegate}
}

func (s *EmailServiceSpy) Send(to, subject string) error {
	s.calls = append(s.calls, call{method: "Send", to: to, subj: subject})
	return s.delegate.Send(to, subject)
}

func (s *EmailServiceSpy) WasCalledWith(to, subject string) bool {
	for _, c := range s.calls {
		if c.method == "Send" && c.to == to && c.subj == subject {
			return true
		}
	}
	return false
}

type User struct {
	Email string
}

func RegisterUser(email string, es EmailService) (User, error) {
	user := User{Email: email}
	if err := es.Send(email, "Welcome"); err != nil {
		return User{}, err
	}
	return user, nil
}

func main() {
	spy := NewEmailServiceSpy(RealEmailService{})
	user, err := RegisterUser("ada@example.com", spy)
	if err != nil {
		panic(err)
	}
	if len(spy.calls) != 1 {
		panic("Send should be called exactly once")
	}
	if !spy.WasCalledWith("ada@example.com", "Welcome") {
		panic("Send should carry the new user's address and subject")
	}
	fmt.Println("Go spy test passed for", user.Email)
}
```

## 18. References

1. Gerard Meszaros, *xUnit Test Patterns. Refactoring Test Code*,
   Addison-Wesley, 2007, chapter 11, "Types of Test Doubles" (introduces
   Dummy, Fake, Stub, Spy, Mock as distinct roles) and chapter 16,
   "Overspecified Software" (the fragile-test failure mode referenced in
   dimension 11).
2. Martin Fowler, "Mocks Aren't Stubs",
   https://martinfowler.com/articles/mocksArentStubs.html, verified
   2026-08-02. Direct quote used, "Spies are stubs that also record some
   information based on how they were called."
3. Sinon.js official documentation, spies reference,
   https://sinonjs.org/concepts/spies/, verified 2026-08-04.
4. Mockito official project site, https://site.mockito.org/, verified
   2026-08-02. Direct quote used, "spy()/@Spy, partial mocking, real methods
   are invoked but still can be verified and stubbed."
5. Jest official documentation, "The Jest Object", `jest.spyOn` section,
   https://jestjs.io/docs/jest-object#jestspyonobject-methodname, verified
   2026-08-02.
6. Python Software Foundation, Python 3 standard library documentation,
   `unittest.mock`, https://docs.python.org/3/library/unittest.mock.html,
   verified 2026-08-02, for call tracking attributes `call_args`,
   `call_count`, `call_args_list`, and the `wraps` parameter for pass-through
   spy behavior.
7. Michael C. Feathers, *Working Effectively with Legacy Code*, Prentice
   Hall, 2004, chapter 4, "The Seam Model", for the seam-introduction
   technique referenced for the legacy-code monkey-patch spy variant in
   dimensions 8 and 14.
