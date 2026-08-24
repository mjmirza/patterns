---
name: Fresh Fixture
slug: fresh-fixture
family: 14-testing
category: Testing
aliases: [Per-Test Fixture, Test-Local Fixture]
first_described: "Meszaros 2007"
maturity: canonical
related: [shared-fixture, test-data-builder, object-mother, four-phase-test]
incompatible_with: [shared-fixture]
verified: 2026-08-02
---

# Fresh Fixture

## 1. Name, aliases, and lineage

The canonical name is Fresh Fixture, catalogued by Gerard Meszaros in *xUnit Test
Patterns. Refactoring Test Code*, Addison-Wesley, 2007, ISBN 978-0131495050,
in the fixture design chapter of the book's pattern catalog. Meszaros's catalog
groups test fixture strategies into two opposing families, Fresh Fixture and
Shared Fixture, and Fresh Fixture is the one where every test constructs the
objects it needs from nothing, rather than reusing state left behind by another
test or set up once for a whole run.

The pattern predates the name. Kent Beck's original SUnit design for Smalltalk,
carried into every xUnit-family framework since (JUnit, PyUnit, NUnit, and the
rest), builds a fresh instance of the test class for every test method, and each
instance runs its own setup hook before the test body. That per-instance
construction is exactly what later got the label Fresh Fixture once Meszaros
wrote it down as a named, deliberate choice with a name for its opposite. This
is not a case of one author's invention displacing an older term. It is a case
of an implicit default becoming an explicit, nameable decision once someone
wrote down what the alternative would look like.

Two aliases circulate informally. **Per-Test Fixture** describes the same idea
by its scope rather than by Meszaros's metaphor of freshness. **Test-Local
Fixture** appears in discussions contrasting it with fixtures shared across a
whole test class or a whole suite. Neither alias appears in a citable primary
source with the frequency of Fresh Fixture itself, so this entry uses
Meszaros's term throughout.

A useful test for whether a given piece of test code is using Fresh Fixture.
Delete every other test in the file and run only this one. If it still passes
with the same result, the fixture was fresh. If it now fails, or passes for the
wrong reason, some other test's leftover state was doing part of the work, and
the fixture was shared, not fresh, no matter what the code intended.

## 2. Problem and context

A test needs an environment in which to run its assertions, objects to act on,
data in a database, files on disk, a running process. Building that environment
from scratch, every time, for every test, has an obvious cost, it takes code,
and if the environment involves I/O such as a database write, it takes time.

The situation reads like this in a test suite that has grown under time
pressure. A first test creates a customer row and asserts something about
customer creation. A second test, added later, needs a customer to act on, and
someone notices the row from the first test is still sitting in the database
after that test ran. They write the second test to look for that row rather
than creating their own. It passes. A third test does the same thing. Within a
few months the suite is a web of tests that only pass in a specific order,
because each one depends on state a previous one happened to leave behind, and
nobody remembers which test created the fixture that another test consumes.

The context in which Fresh Fixture is the right default is almost every
context, any test where correctness matters more than shaving milliseconds off
the suite, any test that will be read and modified by someone other than its
author, and any test that must survive being run alone, in a different order,
or in parallel with other tests. The pattern earns its keep precisely because
those conditions describe nearly all test suites that live longer than a
sprint.

## 3. Forces

The pattern balances the following competing pressures.

- **Isolation.** Favoured, strongly. Because each test builds its own objects
  or its own transactionally-scoped rows, one test's mutation cannot leak into
  another test's assertions. This is the pattern's whole reason to exist.
- **Determinism and order-independence.** Favoured. A suite built from fresh
  fixtures produces the same pass or fail result no matter what order the tests
  run in, and can be shuffled, parallelised, or run as a single test with
  identical outcomes.
- **Readability and locality.** Favoured. Everything a reader needs to
  understand what state the test starts from is visible in the test itself or
  in an obviously-named setup method scoped to it, not scattered across a suite
  in files the reader has not opened.
- **Execution time.** Sacrificed, specifically for tests whose fixture involves
  I/O, creating a database row, hitting a filesystem, or spinning up a process
  per test costs real wall-clock time, and that cost is paid on every single
  test rather than amortised once.
- **Setup code volume.** Sacrificed at the naive extreme. Writing every field
  of every object inline in every test produces enormous duplication. The
  pattern does not by itself solve this, it depends on companion patterns,
  Test Data Builder and Object Mother, to keep the fresh-construction code
  short, see dimension 8 and dimension 13.
- **Debuggability of a failing test.** Favoured. When a fresh-fixture test
  fails, the cause is confined to that test's own setup and its own body. A
  shared-fixture failure can be caused by a different test that ran earlier in
  the same process, which the failure message gives no hint of.
- **Resource contention under parallel execution.** Mixed. Fresh Fixture makes
  parallel test execution safe, because tests do not step on each other's
  state, but a naive implementation that hits a real shared database can still
  contend on the same physical resource even though the data itself is
  isolated by row. The isolation techniques in dimension 8 exist to solve this.

Fresh Fixture pays for isolation with time and setup volume. That is the entire
trade, and every implementation variant in this entry is an attempt to buy back
some of the time without giving back the isolation.

## 4. Applicability and non-applicability

Reach for Fresh Fixture when any of these hold.

- The test suite will be read, extended, and reordered by people other than the
  original author, which is true of essentially every suite that outlives one
  sprint.
- Tests must be safe to run in any order, including a single test run in
  isolation, and safe to run in parallel across workers.
- A test failure must localise to the test that failed, without requiring the
  reader to trace back through earlier tests in the same run to find the state
  that caused it.
- The fixture is cheap to build, either because it is in-memory objects with no
  I/O, or because the environment (see dimension 8) makes per-test I/O cheap
  through transactional rollback or an in-memory substitute.
- Mutation testing or property-based testing will run the same test body
  against many generated inputs, which requires the fixture to reset cleanly
  between runs with no accumulated state.

Do NOT reach for Fresh Fixture, or reach for it only with real qualification,
in these cases, and the reason matters more than the rule.

- **The fixture is a genuinely expensive, read-only resource that many tests
  need in exactly the same shape.** A large reference dataset loaded once and
  never mutated by any test is the textbook case for Shared Fixture instead, and
  Meszaros gives this exact trade-off as the justification for Shared Fixture's
  existence. Rebuilding it per test buys isolation nobody needed, because
  nothing was going to mutate it anyway.
- **The system under test is an external, slow, or costly integration you do
  not own,** such as a third-party payment gateway sandbox with rate limits.
  Constructing a brand-new fixture state against it per test can exhaust quota
  or make the suite too slow to run on every commit. A hybrid, fresh
  in-process objects paired with a small number of shared external fixtures, is
  usually the honest answer here, not a blanket rejection of freshness.
- **The test is deliberately verifying behaviour that depends on accumulated
  state across a realistic sequence of operations,** such as a soak test or a
  migration test that must run in the actual order production would run in.
  Forcing that into isolated fresh fixtures would test something other than
  what the test is meant to test, this is a case where Fresh Fixture is simply
  the wrong tool, not a case of misuse.
- **The fixture setup cost, multiplied by test count, would make the suite too
  slow to run before every commit,** and no cheaper fresh-fixture technique
  from dimension 8 closes the gap. At that point the honest trade is either
  Shared Fixture with careful cleanup, or splitting the suite into a fast tier
  run on every commit and a slower tier run less often.
- **You are testing a Singleton or other genuinely process-global state you
  cannot construct fresh without also rewriting the code under test.** Forcing
  freshness here often means adding test-only reset hooks to production code
  purely to serve the test, which is a design smell in its own right, see
  dimension 11.

## 5. Structure

Fresh Fixture is a testing pattern, not a structural design pattern, so it has
no polymorphic participants in the GoF sense. Its structure is a discipline
applied at three points in a test's lifecycle, corresponding to the Four-Phase
Test shape (setup, exercise, verify, teardown), see dimension 13.

- **Setup phase.** Every object, row, file, or process the test needs is
  constructed inside this test's own setup, never read from a location another
  test wrote to. In xUnit-family frameworks this is the per-test hook, `setUp`
  in classic xUnit and `unittest.TestCase`, a `@BeforeEach`-annotated method in
  JUnit 5, or the constructor of the test class itself in xUnit.net, which the
  framework instantiates once per test method rather than once per class.
- **Exercise phase.** The test acts on the fresh objects built moments earlier, in setup. Because
  nothing else could have touched them yet, the state entering this phase is
  fully known.
- **Verify phase.** Assertions read only the state this test created and
  mutated, so a failing assertion has exactly one possible cause, this test's
  own logic.
- **Teardown phase.** Whatever was created is discarded or rolled back so the
  next test, whichever test that turns out to be, starts from the same known
  baseline this test started from. For in-memory objects teardown is often
  implicit, garbage collection frees them. For anything involving external
  state, explicit or transactional teardown is what turns "fresh at the start"
  into "fresh for the next test too," see dimension 8.

The key structural claim, and the one that separates Fresh Fixture from Shared
Fixture, is where construction happens, inside the boundary of a single test's
setup, versus outside it, in a suite-level or class-level hook that runs once
and is then read by many tests.

## 6. ASCII structure diagram

```
   FRESH FIXTURE                          SHARED FIXTURE (for contrast)

   +------------------+                   +------------------+
   |    Test Suite     |                   |    Test Suite     |
   +--------+---------+                   +--------+---------+
            |                                       |
            |                              +--------v---------+
            |                              |  Suite-level      |
            |                              |  setup (once)     |
            |                              +--------+---------+
            |                                       |
   +--------v---------+   +------------------+      |  (shared reference)
   |     Test A         |   |     Test B        |      |
   |--------------------|   |--------------------|      |
   | setup: build own   |   | setup: build own   |  +---v----+---+
   |   fixture A'       |   |   fixture B'       |  |Test A|Test B|
   | exercise fixture A'|   | exercise fixture B'|  |------|------|
   | verify   fixture A'|   | verify   fixture B'|  |read/mutate  |
   | teardown A'        |   | teardown B'        |  |shared state |
   +--------------------+   +--------------------+  +-------------+

   A' and B' never touch                  A and B both read and
   each other. Order and                  mutate the SAME object,
   parallelism are safe.                  so order and isolation
                                           are no longer guaranteed.
```

## 7. Dynamics

The runtime flow for a single test under Fresh Fixture, using the xUnit-family
lifecycle common to JUnit 5, NUnit, and Python's `unittest`.

```
Test Runner        Test Instance (fresh)       Fixture Objects       Assertions
     |                      |                          |                  |
     |-- new Test() ------->|                          |                  |
     |   (framework builds a fresh instance             |                  |
     |    for THIS test only)                          |                  |
     |                      |                          |                  |
     |-- setUp() ---------->|                          |                  |
     |                      |-- construct fixture ---->|                  |
     |                      |   (no read of prior      |                  |
     |                      |    test's state)         |                  |
     |                      |<-- fixture ready ---------|                  |
     |                      |                          |                  |
     |-- run test body ---->|                          |                  |
     |                      |-- exercise system ------>|                  |
     |                      |                          |-- mutate ------->|
     |                      |<-- result -----------------------------------|
     |                      |-- assert -------------------------------------->|
     |                      |                          |                  |
     |-- tearDown() ------->|                          |                  |
     |                      |-- discard / rollback --->|                  |
     |                      |                          |                  |
     |-- (instance discarded, next test gets a         |                  |
     |    brand new instance and repeats from the top) |                  |
```

The property worth stating plainly, the arrow from "new Test()" at the top
happens for every single test, and the fixture-construction step that follows
it never reads anything left behind by a previous iteration of this same loop.
When a database is involved, the "discard / rollback" step is what makes the
next iteration's "no read of prior state" claim actually true rather than
merely intended, which is why transactional test isolation (dimension 8) is
not an optional nicety, it is the mechanism that makes the promise hold for
anything touching durable storage.

## 8. Implementation variants

**Plain in-memory construction.** The test builds ordinary objects with `new`
or a constructor call, no I/O involved. This is the cheapest and most common
form, and the one that needs no special infrastructure at all. Cost scales with
how many fields must be set to reach a valid object, which is the exact problem
Test Data Builder and Object Mother solve, see dimension 13.

**Per-test setup hook.** The framework calls a method before every test, JUnit
5's `@BeforeEach`
(https://docs.junit.org/current/api/org.junit.jupiter.api/org/junit/jupiter/api/BeforeEach.html,
verified 2026-08-02, states the annotated method should be executed before
each test method), `unittest.TestCase.setUp` in Python, or `[SetUp]` in
NUnit. The setup method's only job under Fresh Fixture discipline is to build
this test's fixture, never to read a fixture another test's setup produced.

**Constructor-as-fixture.** xUnit.net for .NET builds a new instance of the
test class for every test method and treats the constructor as the setup hook.
xUnit.net's own documentation states this directly. "xUnit.net creates a new
instance of the test class for every test that is run, so any code which is
placed into the constructor of the test class will be run for every single
test" (https://xunit.net/docs/shared-context, verified 2026-08-02). This
variant makes Fresh Fixture the framework's unavoidable default rather than a
discipline the author has to maintain by hand, because there is no
class-level, once-per-suite construction hook to reach for by mistake in the
first place.

**Function-scoped fixtures (pytest).** pytest's fixture system defaults every
fixture to `function` scope. pytest's own documentation describes this
default scope as the one where "the fixture is destroyed at the end of the
test" (https://docs.pytest.org/en/stable/how-to/fixtures.html, verified
2026-08-02). Two tests that both request the same named fixture each receive
their own result from it, not a shared reference, which is Fresh Fixture
expressed as a dependency-injection mechanism rather than as inheritance from
a base test class.

**Memoized-per-example values (RSpec).** RSpec's `let` caches a computed value
for the duration of one example and discards it afterward. RSpec's
documentation is explicit. "The value will be cached across multiple calls in
the same example but not across examples"
(https://rspec.info/features/3-12/rspec-core/helper-methods/let/, verified
2026-08-02). This gives the ergonomics of a shared-looking helper method while
preserving fresh, per-test construction underneath.

**Transactional rollback around real database rows.** When the fixture must
live in an actual relational database, wrapping each test in a transaction
that is rolled back at the end gives the illusion of a fresh, empty database
for every test while paying only the cost of a transaction rather than a full
schema rebuild. Django's `TestCase` implements exactly this, its documentation
states that it "encloses the test code in a database transaction that is
rolled back at the end of the test. This guarantees that the rollback at the
end of the test restores the database to its initial state," and each test
method is wrapped in its own nested `atomic()` block
(https://docs.djangoproject.com/en/5.2/topics/testing/tools/, verified
2026-08-02). This variant is the mechanism that makes I/O-bound fresh fixtures
affordable at scale, and its cost model is closer to plain in-memory
construction than to a full per-test database rebuild.

**Container-per-suite, row-per-test.** A related hybrid used with tools such as
Testcontainers. One real database container is started once for the whole test
run to amortise the (large) startup cost, but every individual test still gets
a fresh transaction or a fresh schema inside it, so isolation between tests is
preserved even though the underlying process is shared. This is a case where
the expensive, process-level resource is shared (correctly, per dimension 4's
non-applicability guidance) while the data-level fixture stays fresh per test.

**In-memory substitute for an external system.** A fresh, empty in-memory
implementation of a database or a message queue, constructed per test, gives
Fresh Fixture's isolation guarantees without any of Shared Fixture's cross-test
risk and without transactional-rollback machinery, at the cost of testing
against an approximation of the real system rather than the real system
itself.

## 9. Known production uses

**xUnit.net (.NET).** The framework's fundamental execution model constructs a
new instance of the test class per test method, with the constructor acting as
the fixture builder. Documented directly in the framework's own shared-context
guide. "xUnit.net creates a new instance of the test class for every test that
is run" (https://xunit.net/docs/shared-context, verified 2026-08-02). This is
not a convention layered on top of the framework, it is the framework's
default execution model, and reaching for shared state requires opting in via
a separate fixture-sharing mechanism.

**pytest (Python).** The `function` scope, pytest's documented default for
every fixture that does not explicitly request a wider scope, tears the
fixture down at the end of each test
(https://docs.pytest.org/en/stable/how-to/fixtures.html, verified 2026-08-02).
Every Python project using pytest with unqualified `@pytest.fixture`
decorators is using Fresh Fixture by default, and must deliberately widen the
scope to `class`, `module`, or `session` to opt out.

**Django's test framework (Python/Django).** `django.test.TestCase` wraps each
test method in its own nested database transaction and rolls it back
afterward, documented as restoring "the database to its initial state" after
every test (https://docs.djangoproject.com/en/5.2/topics/testing/tools/,
verified 2026-08-02). This is the transactional-rollback variant from
dimension 8, shipped as the framework's recommended default test base class
for any test that touches the ORM.

**RSpec (Ruby).** The `let` helper, one of the most-used constructs in RSpec
test suites, is explicitly scoped to a single example and re-evaluated fresh
for the next one, per RSpec's own documentation
(https://rspec.info/features/3-12/rspec-core/helper-methods/let/, verified
2026-08-02). Its popularity in the Ruby testing community is itself evidence of
how normalised the pattern has become, expressed here as a memoization
primitive rather than as an inheritance hook.

**JUnit 5 (Java).** `@BeforeEach` runs its annotated method before each test
method by specification
(https://docs.junit.org/current/api/org.junit.jupiter.api/org/junit/jupiter/api/BeforeEach.html,
verified 2026-08-02), and combined with JUnit 5's default `PER_METHOD` test
instance lifecycle, in which the framework constructs a new test-class instance
for every test method unless `@TestInstance(Lifecycle.PER_CLASS)` is explicitly
requested, this makes Fresh Fixture the framework's out-of-the-box behaviour
for every Java test suite built on JUnit 5.

## 10. Consequences

Positive.

- Tests are independent of run order, any subset can be run alone, reordered,
  or shuffled, and the result does not change, which is a direct consequence of
  no test being able to read state another test left behind.
- Tests are safe to parallelise across workers or processes, because there is
  no shared mutable state for two workers to race on, provided the underlying
  resource-sharing choices (dimension 8) hold up under concurrent access.
- A failing test's cause is confined to that test, the reader never needs to
  trace backward through the suite to find which earlier test corrupted the
  state.
- Deleting or disabling any single test never breaks another test, which makes
  the suite itself safe to refactor.
- The fixture-construction code doubles as living documentation of what a valid
  object looks like, read right next to the test that uses it.

Negative.

- Per-test construction cost is paid on every test, and for I/O-bound fixtures
  this is real wall-clock time multiplied by test count, this is the direct
  price paid for the isolation above.
- Naive, unfactored fixture code duplicates heavily across a large suite,
  producing long, repetitive setup blocks unless Test Data Builder or Object
  Mother is adopted alongside it.
- A genuinely expensive, read-only shared resource (a large reference dataset,
  a warmed cache) gets rebuilt needlessly if Fresh Fixture is applied
  dogmatically where Shared Fixture was the honest answer, see dimension 4.
- Achieving true freshness against durable external state (a real database, a
  real filesystem) requires infrastructure of its own, transactional rollback,
  container-per-suite isolation, or an in-memory substitute, and getting that
  infrastructure wrong reintroduces the exact cross-test leakage the pattern
  exists to prevent.

## 11. Failure modes and misuse

**The rollback that silently does not run.** Symptom. A suite passes reliably
in CI but a developer running a single test locally sees it fail, or a test
passes the first time and fails the second time it is run in the same session.
Cause. A transaction-based fresh-fixture mechanism (dimension 8) is bypassed
because the code under test opens its own connection outside the test's
transaction, so the "rollback" never touches what was actually written. Fix.
Making the code under test and the test's transaction share the same
connection or connection pool, and add an explicit assertion in the test setup
that the table is empty before proceeding, which turns a silent leak into a
loud, immediate failure at the point it actually happened.

**Fixture reuse disguised as a helper method.** Symptom. A `createTestUser()`
helper is called by many tests, and it looks like Fresh Fixture because each
call returns a "new" object, but the helper is backed by a module-level cache
or a database insert-if-absent statement that silently returns the same row on
the second and later calls. Cause. The helper's author optimised for speed
without checking whether repeated calls actually produce independent state.
Fix. Assert on the returned identifier or object identity in a dedicated test
for the helper itself, confirming two calls produce two distinct results.

**Order-dependent test suite masquerading as fresh.** Symptom. The full suite
passes, but a single test file run alone fails. Cause. Test C relies on setup
performed as a side effect of test A or test B running first, most often
because all three share a module-scoped or session-scoped fixture that one of
them mutates. Fix. Run each test file, and ideally each individual test, in
isolation as a CI gate, not merely the full suite in its usual order, this
exposes hidden ordering dependencies that a full, in-order run will never
reveal.

**Fresh fixture, stale environment.** Symptom. Tests pass locally and fail
intermittently in CI, or the reverse, with no code difference. Cause. The
fixture itself is fresh, but it is being exercised against a shared external
resource, a shared staging database, a shared queue, a shared file on a
network mount, that a different test suite or a concurrent CI job is also
touching. Fix. Confirm the isolation boundary matches the actual resource
being shared, per-test freshness of data does not help if the underlying
resource is contended, see the container-per-suite variant in dimension 8.

**Over-application to a genuinely expensive, immutable resource.** Symptom.
Suite runtime climbs steadily as the suite grows, and profiling shows most of
the time is spent rebuilding an identical, never-mutated reference dataset for
every test that touches it. Cause. Fresh Fixture applied where the
non-applicability guidance in dimension 4 said not to. Fix. Move the
read-only, unmutated portion of the fixture to a Shared Fixture built once per
class or per session, and keep only the parts that are actually created or
mutated per test as fresh.

**Test-only reset hooks bolted onto production code.** Symptom. A method such
as `resetState()` exists on a production class purely so tests can force
freshness against a Singleton or other process-global state. Cause. The
pattern was applied to code that was never designed to support per-test
construction, most often a genuine Singleton. Fix. Treat this as a signal to
either replace the Singleton with dependency-injected, per-test instances, or
accept that this particular piece of state is a legitimate exception under
dimension 4 and document the exception rather than quietly patching around it.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Fresh Fixture | Shared Fixture | Lazy Setup | Prebuilt Fixture (seed data loaded once, read-only) |
|---|---|---|---|---|
| Isolation between tests | Strong. No test can see another's mutation | Weak. All tests share and can mutate the same state | Strong for the object built, but relies on discipline elsewhere | Strong, provided nothing ever mutates the shared data |
| Order independence | Full. Any order, any subset | Poor. Often depends on suite run order | Full, for the lazily-built object | Full, as long as read-only holds |
| Setup execution time | Paid per test | Paid once per suite or class | Paid only when the object is first used per test | Paid once, amortised across the whole suite |
| Setup code duplication | High unless paired with Test Data Builder or Object Mother | Low, one setup written once | Low to medium, depends on how many lazy accessors exist | Low, one seeding step |
| Debuggability of a failing test | High, cause is local to the failing test | Low, cause may be an earlier test in the same run | High, same reasoning as Fresh Fixture | High, provided the read-only invariant genuinely holds |
| Safe for parallel execution | Yes, by construction | No, without extra locking or partitioning | Yes, same as Fresh Fixture | Yes, since nothing writes to it |
| Risk from a broken invariant | Low, the isolation is the mechanism | High, one test's bug corrupts every later test in that run | Low | Catastrophic if the read-only assumption is ever violated by one careless test |
| Best fit | The general default for most test suites | A large, genuinely expensive, rarely-changing resource | Fresh Fixture with construction deferred to first use inside the test | A big reference dataset every test reads but none should ever write |

Reading of the table. Fresh Fixture is the correct default because it wins on
every axis except raw setup time and, without companion patterns, setup code
volume. Shared Fixture wins only when the resource is genuinely expensive AND
genuinely read-only for every test that touches it, and it loses hard the
moment either of those two conditions stops being true, which is precisely why
Meszaros frames Shared Fixture as the pattern that needs the stronger
justification, not Fresh Fixture.

## 13. Related and incompatible patterns

- **Shared Fixture.** The direct, named opposite in Meszaros's own catalog.
  Where Fresh Fixture rebuilds state per test, Shared Fixture constructs it
  once and lets many tests read it. The two are mutually exclusive for a given
  piece of state, but a single suite legitimately mixes them, fresh per-test
  data alongside a shared, read-only reference dataset, provided the boundary
  between the two is explicit and the shared portion is never mutated by any
  test.
- **Test Data Builder.** Solves Fresh Fixture's setup-volume cost directly. A
  builder with sensible defaults and a fluent API lets a test construct a
  complex, valid object in one or two lines instead of setting every field by
  hand, which is what makes rebuilding an object per test affordable in
  practice rather than only in principle.
- **Object Mother.** A related, competing solution to the same setup-volume
  problem, offering named factory methods for common fixture shapes rather
  than a fluent builder. Both patterns exist specifically to make Fresh
  Fixture cheap to write, and a codebase typically settles on one or the other
  rather than mixing both for the same entity type.
- **Four-Phase Test.** The structural shape, setup, exercise, verify, teardown,
  that Fresh Fixture's setup and teardown phases live inside. Fresh Fixture
  answers where the setup phase's data comes from. Four-Phase Test answers
  what the phases of a well-formed test look like in general.
- **Transaction Rollback Teardown.** The specific teardown technique, wrapping
  a test in a database transaction and rolling it back, that makes Fresh
  Fixture affordable against a real relational database rather than only
  against in-memory objects, see the Django and container-per-suite variants
  in dimension 8.
- **Singleton.** Actively in tension with it, not strictly incompatible.
  Testing code that depends on a true process-global Singleton resists Fresh
  Fixture, because there is exactly one instance to construct, not one per
  test, which is the scenario named explicitly in dimension 4's
  non-applicability list.
- **Test Double (Stub, Mock, Fake).** Complementary rather than competing. Test
  doubles replace a collaborator the system under test depends on. Fresh
  Fixture governs how the fixture for the object under test itself is built,
  a test frequently uses both, a freshly built object under test collaborating
  with a freshly built fake.

## 14. Refactoring path in and out

Introducing the pattern into a suite that currently relies on Shared Fixture or
on undocumented cross-test ordering. Ordered steps.

1. Identify the smallest test that currently depends on state created by a
   different test or by a suite-level setup hook. Run it alone. Confirm it
   fails, which proves the dependency is real rather than assumed.
2. Move the minimum state that test needs into its own setup, whether that is
   a per-test setup block, a pytest fixture requested by that test alone, or
   inline construction in the test body. Run the test alone again. Confirm it
   now passes in isolation.
3. Repeat test by test. Resist the urge to refactor the whole suite in one
   pass, since each test's hidden dependency is usually different from the
   next test's.
4. Once every test in a file passes when run alone, run the whole file's tests
   in a randomised order, not the file's declared order. Any failure at this
   point names a remaining hidden dependency to fix with step 2's technique.
5. Delete the suite-level or class-level shared setup only after every test
   that used to depend on it has its own fresh construction. Deleting it
   earlier will produce a wave of failures that at least confirms the earlier
   steps were incomplete, which is a safe, if noisy, way to double-check.
6. Where the resulting per-test setup code is now heavily duplicated across
   tests, extract a Test Data Builder or Object Mother, see dimension 13,
   rather than reintroducing a shared fixture to cut the duplication back
   down. The duplication is the cost of the isolation, pay it back with a
   builder, not by giving the isolation back.
7. Where per-test construction now touches a real database and the suite has
   become slow, introduce transactional rollback (dimension 8) rather than
   reverting to Shared Fixture, this recovers most of the lost speed while
   keeping the isolation guarantee intact.

Moving away from Fresh Fixture, when dimension 4's non-applicability
conditions genuinely apply to a specific, expensive, read-only resource.

1. Confirm, by reading every test that touches the candidate resource, that
   none of them mutate it. A single mutating test disqualifies the resource
   from this refactor entirely.
2. Extract the resource's construction into a class-level or session-level
   setup hook, `@BeforeAll` in JUnit 5, a `session`-scoped fixture in pytest,
   or `setUpTestData()` in Django.
3. Add a runtime assertion, not merely a code review comment, that fails loudly
   if any test attempts to mutate the shared resource, so a future test that
   violates the read-only assumption fails immediately rather than corrupting
   every test that runs after it in the same session.
4. Keep everything else the individual test constructs, which is not the
   candidate resource, on Fresh Fixture, this is a partial move for one
   specific piece of state, not a wholesale reversion of the suite's testing
   philosophy.

## 15. Testing and verification

This dimension is unusually self-referential, since Fresh Fixture is itself a
testing pattern, what follows is how to verify a suite is actually applying it
correctly, not how to test code that merely uses it.

Easier because of the pattern.

- Any individual test can be run alone, and a correctly fresh test behaves
  identically whether run alone or as part of the full suite. Running every
  test alone at least once, as a CI job separate from the normal full-suite
  run, is the single most direct verification technique available.
- Randomising test order between CI runs, which pytest supports via the
  `pytest-randomly` plugin and which several CI runners for other languages
  support natively, exposes hidden shared-state dependencies that a
  fixed-order run will never reveal, because a fixed order can accidentally
  satisfy a hidden dependency every single time.
- Running the suite with parallel workers, such as `pytest-xdist`'s worker
  distribution or the parallel test runner built into most CI platforms, is
  both a performance optimisation and a correctness check, a suite that only
  passes single-threaded despite claiming to use Fresh Fixture is a suite with
  a hidden shared-state leak.

Harder because of the pattern.

- Verifying that a transactional-rollback or container-per-suite isolation
  mechanism (dimension 8) is actually working, rather than silently
  short-circuited, requires a dedicated meta-test. Write a test that inserts a
  row, then a second, unrelated test that asserts the table is empty at its
  own start.
- A test-suite-level flaky-test detector is worth running specifically to
  catch order-dependent tests, since a single random-seeded run has a real
  chance of happening to pass even when a hidden dependency exists.

Techniques that apply.

- **Isolation smoke test.** A CI stage that runs the full suite three times,
  once in declared order, once in reverse order, once in a random order with a
  logged seed. Any test that passes in one ordering and fails in another is a
  concrete, reproducible finding, not a suspicion.
- **Single-test CI matrix (spot check, not exhaustive).** Periodically running
  a sample of individual tests in complete isolation, each as its own CI job,
  catches the case where an entire test file happens to establish enough
  shared state via its own module-level fixtures that every test in that one
  file passes together but none of them would pass truly alone.
- **Fixture-purity assertion.** Where a fixture factory or builder is shared
  across many tests (Test Data Builder, Object Mother), add a unit test for
  the factory itself asserting that two successive calls produce objects that
  are equal in value but distinct in identity, or that carry different
  generated identifiers. This catches the fixture-reuse-disguised-as-a-helper
  failure mode from dimension 11 at its source.

## 16. Observability signals

Fresh Fixture is a design-time and CI-time property more than a runtime one,
so the signals worth tracking live in the test-execution pipeline rather than
in a production dashboard.

What to record.

- Per-test setup duration, reported by the test runner's own timing output. A
  steady climb in the aggregate setup time as the suite grows is the direct,
  measurable cost of Fresh Fixture from dimension 3, and is the signal that
  should trigger a deliberate look at dimension 4's non-applicability
  conditions rather than a silent slide toward ad hoc shared state.
- Pass or fail results from the same suite run in three configurations,
  declared order, reversed order, randomised order, tracked as three separate
  CI checks. A difference between any two of them is the single strongest
  observable signal that Fresh Fixture is being violated somewhere in the
  suite.
- Pass or fail results from single-worker versus parallel-worker runs of the
  same suite, tracked as two separate CI checks. A suite that only passes
  single-threaded is exhibiting the resource-contention failure mode named in
  dimension 11.
- A count of tests skipped or excluded from the randomised-order and
  parallel-worker checks above, because that count is itself a debt tracker,
  every test carved out with a known-order-dependent marker is a specific,
  named instance of the pattern not yet fully applied.

A healthy suite on a dashboard. Setup duration per test stays roughly flat as
the suite grows in test count, rather than climbing per-test, meaning growth in
suite size is not making individual tests slower. The declared-order,
reversed-order, and randomised-order CI checks agree on pass or fail for every
test, every run. The single-worker and parallel-worker checks agree.

A failing instance. A test that passes in declared order but fails when the
suite is reversed or randomised names a hidden Shared Fixture dependency
directly, by CI job and by test name, with no further investigation needed to
locate which test is affected, only to find why. A test that only fails under
parallel execution names a resource-contention issue rather than a data-level
leak, pointing investigation at dimension 8's isolation techniques rather than
at the test's own logic.

## 17. Security and privacy implications

The pattern is close to silent on security in the classical, purely in-memory
case, where fresh objects never leave the test process. Two genuine
implications appear once fresh fixtures involve real, durable, or shared
infrastructure.

**Test data resembling real personal data.** A fresh fixture that generates
realistic-looking names, email addresses, or payment details, built to make
assertions read naturally, can be mistaken for or accidentally seeded into a
staging environment that other systems treat as containing real records. Where
fixture data is generated to resemble production data, it should be visibly
and unambiguously synthetic, using a reserved domain such as example.com for
emails and clearly fictional names, so a fixture leak into a shared
environment is immediately recognisable as test data rather than assumed to be
a real customer record.

**Credential and secret handling in fixture setup.** A fresh fixture that
constructs an authenticated client, an API key, a signed token, or a database
connection string, often does so by reading a real secret from the test
environment so the fixture is realistic. If that fixture-construction code is
logged verbosely during test failures, which many test runners do by default
when a setup step throws, a real secret can end up in CI logs. Fixture
construction code that handles a genuine credential should redact it before
any logging path, exactly as production code handling the same credential
would be expected to.

**Isolation as a genuine security property, not merely a correctness one.** In
a suite that tests authorization or multi-tenant boundaries, Fresh Fixture's
per-test isolation is doing double duty. A test that verifies tenant A cannot
read tenant B's data only proves what it claims to prove if tenant A's and
tenant B's fixtures are genuinely fresh and disjoint for that specific test.
A Shared Fixture reused across several authorization tests can accidentally
make a real vulnerability invisible, because the shared setup happens to grant
broader access than a fresh, minimal fixture would have, and the test never
exercises the narrower, correct boundary at all.

On privacy the pattern is neutral beyond the two points above. It neither
collects nor retains data on its own, and any retention concern belongs to
whatever storage mechanism a fresh fixture happens to be built against, not to
the pattern itself.

## 18. References

1. Gerard Meszaros. *xUnit Test Patterns. Refactoring Test Code*.
   Addison-Wesley, 2007. ISBN 978-0131495050. Fixture design pattern catalog.
   Source of the Fresh Fixture and Shared Fixture names and their opposing
   trade-offs described throughout this entry.
2. JUnit Team. *JUnit 5 User Guide API*, `org.junit.jupiter.api.BeforeEach`.
   https://docs.junit.org/current/api/org.junit.jupiter.api/org/junit/jupiter/api/BeforeEach.html
   Verified 2026-08-02. Source for the "executed before each" timing claim and
   the annotation's requirements.
3. .NET Foundation. *xUnit.net documentation*, "Shared Context between Tests".
   https://xunit.net/docs/shared-context
   Verified 2026-08-02. Source for the per-test-method instance construction
   claim and the constructor-as-fixture variant.
4. pytest development team. *pytest documentation*, "How to use fixtures",
   "Fixture scopes" section.
   https://docs.pytest.org/en/stable/how-to/fixtures.html
   Verified 2026-08-02. Source for the default function scope and its
   per-test teardown behaviour.
5. RSpec Core Team. *RSpec documentation*, "let and let!".
   https://rspec.info/features/3-12/rspec-core/helper-methods/let/
   Verified 2026-08-02. Source for the per-example caching and cross-example
   isolation behaviour of `let`.
6. Django Software Foundation. *Django 5.2 documentation*, "Testing tools",
   `django.test.TestCase` section.
   https://docs.djangoproject.com/en/5.2/topics/testing/tools/
   Verified 2026-08-02. Source for the transaction-wrap-and-rollback teardown
   variant and the nested per-test `atomic()` block behaviour.
7. Martin Fowler. "UnitTest". Bliki, martinfowler.com.
   https://martinfowler.com/bliki/UnitTest.html
   Verified 2026-08-02. Consulted for background on solitary versus sociable
   unit tests, referenced only for the test-double relationship in dimension
   13, and confirmed to not contain a direct discussion of cross-test fixture
   sharing, so it is cited narrowly rather than as a source for this entry's
   central claims.

## Code examples

Three languages where the pattern is idiomatic in genuinely different ways.
TypeScript shows the manual, explicit form with a small builder, the shape
most JavaScript and TypeScript test suites actually use since Vitest and Jest
do not enforce freshness by default the way pytest and xUnit.net do. Python
shows pytest's function-scoped fixture, the framework enforcing freshness by
default. Java shows JUnit 5's `@BeforeEach` alongside the framework's default
per-method test instance lifecycle. All three were checked against the
toolchain available on this machine.

### TypeScript

```typescript
interface Account {
  id: string;
  balance: number;
}

function freshAccount(overrides: Partial<Account> = {}): Account {
  // A tiny Test Data Builder. Every call returns a brand-new object.
  return { id: `acct-${Math.random().toString(36).slice(2)}`, balance: 0, ...overrides };
}

function deposit(account: Account, amount: number): Account {
  return { ...account, balance: account.balance + amount };
}

function testDepositIncreasesBalance(): void {
  const account = freshAccount({ balance: 100 });
  const after = deposit(account, 50);
  if (after.balance !== 150) throw new Error(`expected 150, got ${after.balance}`);
}

function testSecondTestNeverSeesFirstTestBalance(): void {
  // A fresh account starts at zero regardless of what the previous test did.
  const account = freshAccount();
  if (account.balance !== 0) throw new Error(`expected 0, got ${account.balance}`);
}

testDepositIncreasesBalance();
testSecondTestNeverSeesFirstTestBalance();
console.log("all tests passed");
```

### Python

```python
import pytest


class Account:
    def __init__(self, balance: int = 0) -> None:
        self.balance = balance

    def deposit(self, amount: int) -> None:
        self.balance += amount


@pytest.fixture
def account() -> Account:
    # function scope is pytest's default: a brand new Account per test.
    return Account(balance=100)


def test_deposit_increases_balance(account: Account) -> None:
    account.deposit(50)
    assert account.balance == 150


def test_second_test_never_sees_first_test_balance(account: Account) -> None:
    # Even though the previous test deposited 50, this fixture call
    # constructs a fresh Account, so balance starts at 100 again.
    assert account.balance == 100
```

### Java

```java
final class Account {
    int balance;

    Account(int balance) {
        this.balance = balance;
    }

    void deposit(int amount) {
        balance += amount;
    }
}

// A minimal, dependency-free stand-in for a real JUnit 5 test class,
// so the sample compiles and runs without a build tool. The shape of
// freshFixture() mirrors a real @BeforeEach method: it runs before every
// test and rebuilds `account` from nothing each time. In production code
// this method would carry the @BeforeEach annotation from
// org.junit.jupiter.api, and JUnit's runner would call it once per test
// method rather than the two explicit calls made in main() below.
final class AccountTest {
    private Account account;

    void freshFixture() {
        account = new Account(100);
    }

    void depositIncreasesBalance() {
        account.deposit(50);
        if (account.balance != 150) {
            throw new AssertionError("expected 150, got " + account.balance);
        }
    }

    void secondTestNeverSeesFirstTestBalance() {
        if (account.balance != 100) {
            throw new AssertionError("expected 100, got " + account.balance);
        }
    }
}

public final class Main {
    public static void main(String[] args) {
        AccountTest t1 = new AccountTest();
        t1.freshFixture();
        t1.depositIncreasesBalance();

        AccountTest t2 = new AccountTest();
        t2.freshFixture();
        t2.secondTestNeverSeesFirstTestBalance();

        System.out.println("all tests passed");
    }
}
```

Ran with `npx tsc --strict --target es2020 --module commonjs fresh-fixture.ts`
followed by `node fresh-fixture.js`, output "all tests passed". Ran with
`python3 -m pytest fresh_fixture_test.py -v`, both tests passed. The Java
sample compiled with `javac Main.java` and ran with `java Main`, output
"all tests passed". It deliberately avoids the real `org.junit.jupiter.api`
dependency so it compiles standalone with no build tool, per the note in the
code comment; the real annotation and lifecycle claims for JUnit 5 are backed
separately by the citation in dimension 9.
