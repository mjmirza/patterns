---
name: Derived Value
slug: derived-value
family: 14-testing
category: Test Data
aliases: [Computed Test Value, Context-Derived Value]
first_described: "Meszaros 2007"
maturity: canonical
related: [literal-value, generated-value, test-data-builder, fresh-fixture, dummy]
incompatible_with: []
verified: 2026-08-02
---

# Derived Value

## 1. Name, aliases, and lineage

The canonical name in this catalog is Derived Value, taken directly from
Gerard Meszaros, *xUnit Test Patterns. Refactoring Test Code*,
Addison-Wesley, 2007, in the chapter that classifies how test data gets
into a test. Meszaros treats data-provision decisions as a small family of
sibling choices a test author makes for every field of every fixture object.
a Literal Value is typed in by hand because its exact content matters to the
test, a Generated Value is produced by some rule so the author does not have
to invent one, and a Derived Value is a value computed from something else
already present in the test, most often a counter, the test's own name, or
another field on the same object, so that the value is both unique within
the test run and traceable back to where it came from. The book places these
three on one line running from most meaningful and most expensive to write,
at the Literal Value end, to least meaningful and cheapest to write, toward
the Generated Value end, with Derived Value sitting between them because it
costs a little more than a bare random generator but still avoids the author
hand-typing a value for every field of every object the test needs (Gerard
Meszaros, *xUnit Test Patterns*, Addison-Wesley, 2007, chapter 11).

The pattern predates the book's naming. Every test suite that ever built a
helper such as `makeUniqueEmail()` or `nextId()` was already applying Derived
Value, Meszaros gave the technique a name distinct from its neighbors so a
team could talk about which one a given field should use, rather than
lumping all non-literal data under one vague label. No later author has
proposed a competing name for exactly this concept, and the term shows up
unchanged in the secondary literature that cites Meszaros's taxonomy, for
example in discussions of the Object Mother and Test Data Builder patterns,
which both explain themselves partly in terms of which of Meszaros's three
data-provision strategies they apply to which field (Nat Pryce, "Test Data
Builders. an alternative to the Object Mother pattern", published 2007,
verified 2026-08-02). This entry treats Derived Value strictly as Meszaros
defined it, a value computed from other data already in scope inside the
test, and keeps it distinct from the broader, looser use of the word derived
that shows up in everyday testing talk to mean almost any value a human did
not type in literally.

## 2. Problem and context

A test needs data. Every object under test, and every collaborator it talks
to, has fields that must be filled in before the test can run, and the
overwhelming majority of those fields do not matter to the specific behavior
being verified. A test asserting that a shopping cart correctly sums line
items does not care what the customer's email address is, only that one
exists and is syntactically acceptable to whatever validation the fixture
setup runs. If the author types a literal value for every such field, two
problems compound as the suite grows. First, the literal reads as though it
matters, because a reader has no way to tell an incidental literal from a
load-bearing one just by looking at it, so every test becomes harder to read
than it needs to be, because the reader has to hold every literal in mind
until they can rule it out as irrelevant. Second, and more mechanically
damaging, literal values collide. Two tests that both hard-code the email
`test@example.com` will interfere with each other the moment the system
under test enforces uniqueness on that field, whether through a database
unique constraint, an in-memory set, or a business rule, and the failure
shows up as a flaky, order-dependent test that fails only when run alongside
its sibling, which is one of the hardest classes of failure to diagnose
because the individual test passes every time it is run alone.

The context in which Derived Value earns its place is exactly this situation,
a field whose content is genuinely incidental to the behavior under test but
whose value still needs some property, almost always uniqueness, sometimes a
particular length or shape, to avoid breaking either the fixture setup or a
sibling test. The pattern does not apply, and should not be reached for, when
the value is load-bearing, when the test is specifically about what happens
with a customer named exactly "O'Brien" or a price of exactly zero, because
computing that value from something else buries the one fact the reader
actually needs to see in plain sight.

## 3. Forces

Readability pulls toward Literal Value, because a reader parsing a test wants
to see the exact input and the exact expected output sitting in the test
body, not reconstruct them by tracing a helper function. Maintainability and
collision-avoidance pull toward Derived Value or Generated Value, because a
suite with hundreds of tests cannot survive hundreds of hand-typed unique
strings without eventually producing a duplicate that a merge or a copy-paste
introduces unnoticed. Traceability is the force that specifically favors
Derived Value over a bare Generated Value, a value derived from the test's
own name or from a running counter can be traced back to its origin when a
failure report shows it, whereas a value pulled from a random-number
generator with no seed value recorded in the failure output gives the reader
nothing to search for. Determinism is in real tension with uniqueness inside
Derived Value itself, a counter that increments across the whole suite run
gives uniqueness but is not deterministic across reruns unless the counter
itself is reset or fixed at a known start value, and a naive implementation
that starts from wall-clock time trades one problem, collision, for another,
unreproducibility, discussed at length in dimension 11. Cost of authorship
favors Derived Value over Literal Value at scale, one small helper function
pays for itself across every test that calls it, but the pattern gives up
the reader's ability to see the exact value without running the helper
mentally or in a debugger, a genuine, not merely stylistic, cost recorded in
dimension 10.

## 4. Applicability and non-applicability

Reach for Derived Value when a field must be unique across test runs or
across fixtures created within one run, and its exact content carries no
meaning for the assertion being made, the textbook case being an email
address, a username, or an external identifier that a fixture-building
helper needs to hand to a factory function on every call. Reach for it when
several related fields need to stay internally consistent with each other,
for example a slug that must match a title after the title is lower-cased
and hyphenated, because deriving the slug from the title inside the fixture
helper keeps the two from silently drifting apart as the test evolves. Reach
for it when a test intentionally builds many similar objects that differ only
in one dimension, a loop that creates ten orders differing only by amount,
where deriving each amount from the loop index both guarantees the ten values
are distinct and lets a failure message name which iteration failed.

Do not reach for it when the value is the subject of the assertion itself,
the test that checks a discount calculation must show the exact numbers the
calculation runs on and the exact number it expects back, computing either
side from the other or from a shared formula risks the coincidental
correctness misuse named in dimension 11, where the test and the production
code both compute the same wrong answer the same way and the test passes for
the wrong reason. Do not reach for it when a reader needs to recognize the
value on sight to understand the test's intent, a test titled "rejects an
email with no @ sign" should show the literal broken string, not a derived
one, because the entire point of the test is that specific, inspectable
shape. Do not reach for it as a substitute for a Fake or a Test Data Builder
when the object being constructed has many required fields, Derived Value
answers the question of what one field's content should be, it does not
answer how to assemble a whole object, that job belongs to the Test Data
Builder or the fixture factory the derived values are plugged into (Nat
Pryce, "Test Data Builders. an alternative to the Object Mother pattern",
published 2007, verified 2026-08-02). Do not reach for it in a
property-based test's generator definitions, where the generator itself is
responsible for producing the full range of inputs under a strategy, that
is a different, broader technique discussed as an implementation variant in
dimension 8, not an instance of Derived Value in Meszaros's narrower sense.

## 5. Structure

The pattern has three participants. The Seed is the piece of data already in
scope that the derived value is computed from, most often a monotonic
counter maintained by the test process, the current test's own name or ID as
supplied by the test runner, or a sibling field on the object being built.
The Derivation Function is the small, deterministic piece of logic that maps
the seed to the final value, typically string concatenation with a fixed
prefix, a modulo operation to keep a numeric value inside a valid range, or a
transformation such as lower-casing and hyphenating a title to produce a
slug. The Derived Value itself is the output, the field that ends up on the
fixture object and that the rest of the test consumes exactly as it would
consume a hand-typed literal, the caller of the derivation function should
never need to know, and should not depend on, how the value was produced.

## 6. ASCII structure diagram

```
+---------------------+     +------------------------+     +----------------+
|        Seed          |     |   Derivation Function   |     | Derived Value  |
|-----------------------|---->|--------------------------|---->|----------------|
| counter, test name,   |     | prefix + seed            |     | "user-0007"    |
| or a sibling field     |     | hash(seed) mod range      |     | (unique, or    |
|                        |     | slugify(title)            |     |  consistent    |
+---------------------+     +------------------------+     |  with sibling) |
                                                             +----------------+
                                                                     |
                                                                     v
                                                             +----------------+
                                                             | Fixture Object |
                                                             | under test     |
                                                             +----------------+
```

## 7. Dynamics

At the start of a test, or at the start of a test suite's run, the Seed is
established, a global counter is either initialized once and incremented on
every call, or the test runner's own identifier for the current test is read
from the framework, both approaches make the seed differ across tests
without any coordination between test authors. When the test's setup code
needs a value for a field it does not care about, it calls the derivation
helper, passing the seed either implicitly, because the helper reads a
module-level counter itself, or explicitly, because the test passes its own
name in as an argument. The derivation function runs its deterministic
transformation and returns the Derived Value. The test's setup code assigns
that value to the fixture object's field exactly as it would assign a
literal, and the object is then handed to the system under test or persisted
through whatever fixture strategy the suite uses, most commonly the Fresh
Fixture strategy where each test builds its own objects from scratch. If the
test fails, a well-built derivation function includes enough of the seed in
the output, the counter value or the test name, that the failure message
naming the derived value also names which test produced it, closing the loop
back to the seed without the reader needing to read the helper's source.

## 8. Implementation variants

The counter variant keeps a single incrementing integer, usually a module
level or class level static field, and appends it to a fixed prefix on every
call, `f"user-{next(counter)}@example.com"`, which is simple, fast, and fully
deterministic across a single process run, but the counter must be reset
between test runs or scoped correctly per test file to avoid cross-file
collisions in a parallel test runner, a concrete misuse covered in
dimension 11.

The test-name variant reads the current test's own identifier from the
framework and derives the value from it, for example JUnit 5's
`TestInfo.getDisplayName()` or pytest's `request.node.name` fixture, both of
which expose the running test's name to code inside the test itself
(JUnit 5 User Guide, "Dependency Injection for Constructors and Methods",
verified 2026-08-02; pytest documentation, "How to use fixtures", the
`request` fixture section, verified 2026-08-02). This variant costs a
little more setup complexity for the strongest traceability, a derived value
that literally contains the name of the test that produced it needs no
further lookup when it shows up in a failure log or a database row during
debugging.

The sibling-field variant derives one field from another already set on the
same object, a slug from a title, a total from a list of line items, a
full name from separately supplied first and last names. This variant is the
one Meszaros's own book warns needs the most care, because if the derivation
function inside the test fixture uses the exact same logic as the production
code under test, the test stops testing anything, both sides compute the
same answer the same way and a bug in that shared logic is invisible to the
test, discussed in dimension 11 as coincidental correctness (Gerard
Meszaros, *xUnit Test Patterns*, Addison-Wesley, 2007, chapter 18, "Test
Logic in Production").

A related but distinct family, worth naming so it is not confused with
Derived Value, is the generator strategy used by property-based testing
tools, where a whole class of inputs is described declaratively and the
framework itself derives concrete instances from that description across
many runs, for example Hypothesis's `st.builds()` and `st.text()` strategies
in Python or QuickCheck's `Arbitrary` type class in Haskell (Hypothesis
documentation, "Writing custom strategies", verified 2026-08-02). These
produce a distribution of inputs rather than a single traceable value tied
to one test's seed, and they serve a different purpose, exploring the input
space to find a counterexample, rather than avoiding a hand-typed literal
for one incidental field, so this entry treats them as a neighboring
technique rather than a variant of Derived Value proper.

## 9. Known production uses

The Ruby on Rails testing world's `FactoryBot` gem, one of the most widely
adopted fixture-building libraries for Rails applications, ships a built-in
`sequence` mechanism for exactly this purpose, a factory declares
`sequence(:email) { |n| "person#{n}@example.com" }` and every object the
factory builds receives a distinct, traceable derived value without the
test author typing a new literal for every call (FactoryBot documentation,
"Sequences", verified 2026-08-02). This is Derived Value implemented as a
named feature of a mainstream library rather than a pattern a team
reinvents by hand.

Python's `factory_boy` library, an explicit port of FactoryBot's design to
Python and used across a large number of Django and Flask projects, provides
the identical `factory.Sequence` construct for the same reason, with its own
documentation describing sequences as producing values "that are guaranteed
to be different for each instance created", the same problem statement this
entry opens with (factory_boy documentation, "Sequences", verified
2026-08-02).

JUnit 5's `@TestInfo` injection, part of the framework's dependency
injection support for test methods, lets test authors derive values,
including unique identifiers and log labels, from the currently executing
test's own display name and tags without any external counter, and the
framework's own user guide documents this as one of the supported injection
targets alongside `TestReporter` (JUnit 5 User Guide, "Dependency Injection
for Constructors and Methods", verified 2026-08-02).

## 10. Consequences

The pattern removes a whole category of intermittent, order-dependent test
failure caused by literal-value collisions, and it does so with a single
small helper rather than requiring every test author to remember to
hand-craft a unique value on every call, which is a real and durable
maintenance win once a suite passes a few hundred tests. It also improves
readability at the point of consumption, a fixture-building call site such as
`build_user()` reads cleanly because the reader does not need to see, and
does not need to know, the exact email the helper produced.

The cost is a layer of indirection a reader must trust or trace. A test
failure that names a derived value such as `user-0417@example.com` does not,
by itself, tell the reader what made that particular test run fail, the
reader has to know, or look up, that the number is a sequence counter before
the value means anything, which is a genuinely worse debugging experience
than a literal for the small minority of failures where the exact value
does turn out to matter. The pattern also carries the coincidental
correctness risk named in dimension 8 and detailed in dimension 11, where
computing an expected value with the same formula the production code uses
silently defeats the test, a risk that a Literal Value never carries because
a hand-typed expected value cannot accidentally share a bug with the code it
is supposed to check.

## 11. Failure modes and misuse

**Symptom.** A test suite passes reliably when run one test at a time and
fails intermittently, and only in certain orders, when run as a full suite
or in parallel. **Cause.** The derivation function's seed is not actually
scoped correctly, a module-level counter that is meant to be reset per test
file is instead shared process-wide, or a wall-clock-based value collides
because two tests started within the same millisecond, a real risk once a
suite runs on a fast CI runner with dozens of parallel workers. **Fix.**
Scope the counter explicitly, reset it in a setup or teardown hook
recognized by the test framework, or switch the seed source to something
the framework already guarantees is unique per test, such as the test's own
display name, rather than a value the test author has to manage by hand.

**Symptom.** A test that is supposed to catch a real calculation bug keeps
passing even after the bug is deliberately reintroduced during a mutation
testing run or a manual sabotage check. **Cause.** Coincidental correctness,
the test's expected value was computed using the identical formula the
production code uses, so both sides compute the same wrong answer the same
way whenever that formula is wrong, and the assertion never has a chance to
fail. This is the single most damaging misuse of the pattern because it
produces a test that looks complete on a coverage report while checking
nothing. **Fix.** For any field that is the actual subject of the assertion,
switch to a Literal Value computed independently, by hand, by a second
person, or against a reference table, never by calling the same function or
copying the same arithmetic the system under test uses internally.

**Symptom.** A failure log shows a derived value such as `req-88213` and the
engineer debugging the failure has no way to find which test, which run, or
which environment produced it. **Cause.** The derivation function was built
purely for uniqueness and dropped traceability, a random UUID or a hash
with no readable structure satisfies the uniqueness requirement but throws
away the debugging benefit that motivated using Derived Value instead of a
bare Generated Value in the first place. **Fix.** Include a stable,
greppable fragment in the derived value, a prefix naming the test file, the
test name itself when the framework exposes it, or a fixed literal prefix
per fixture type, so the value that appears in a log or a database row can
be traced back to its origin without additional tooling.

## 12. Trade-off matrix

| Force | Literal Value | Generated Value | Derived Value |
|---|---|---|---|
| Readability at call site | Highest, exact content visible | Low, content is opaque and arbitrary | Medium, content is predictable if the reader knows the rule |
| Guaranteed uniqueness across tests | None, author must manage it by hand | High, if the generator is set up for uniqueness | High, by construction from a counter or test name |
| Traceability from a failure back to origin | Trivial, the literal is the failure message | Low, unless the generator logs its seed | High, if the derivation includes a readable seed fragment |
| Risk of coincidental correctness | None | Low, values are arbitrary, not computed from production logic | Present, if the derivation reuses production-code logic |
| Authoring cost across a large suite | High, scales linearly with number of fields | Low, one generator call per field | Low, one helper call per field, plus one-time helper cost |
| Determinism across repeated runs | Total | Depends entirely on the generator's own setup | Total, if the seed source itself is deterministic |

## 13. Related and incompatible patterns

Derived Value is one of three siblings Meszaros names for supplying test
data, the other two being Literal Value, used when the exact content of a
field is load-bearing for the assertion, and Generated Value, used when a
field's content is entirely arbitrary and only needs to satisfy a type or a
loose validation rule, with no requirement that it be traceable back to
anything. Derived Value pairs naturally with the Test Data Builder pattern,
where a builder's default field values are frequently supplied as Derived
Values so that calling `.build()` without customizing every field still
produces a valid, unique object, and the builder pattern is what supplies
the "assemble a whole object" capability that Derived Value alone does not
provide, as noted in dimension 4 (Nat Pryce, "Test Data Builders. an
alternative to the Object Mother pattern", published 2007, verified
2026-08-02). It also pairs with the Fresh Fixture strategy, where every test
builds its own objects from scratch, because a fresh set of derived values
per test is what keeps fresh fixtures from colliding with each other, in
contrast to a Shared Fixture strategy, where a persistent, reused fixture
often needs Literal Values precisely because its content is meant to be
stable and known across the whole suite that reuses it. Derived Value does
not conflict with any named pattern in this catalog, but it sits in tension
with the Dummy pattern for the same field, a Dummy exists specifically
because the field is never read by the code under test at all, in which
case computing a value for it, rather than passing a fixed placeholder,
spends effort producing something that will never be inspected.

## 14. Refactoring path in and out

To introduce Derived Value into a fixture that currently hand-types literal
strings for incidental fields, first identify which fields the code under
test actually reads, the surest way is to delete a suspect field's literal
and rerun the test, if it still passes the field was never load-bearing.
Extract a small helper function, or a fixture factory method, that computes
that field from a seed already available in the test context, a counter, the
test's name, or the framework's built-in test-info injection. Replace the
hand-typed literal at every call site with a call to the new helper, and
confirm the whole file's tests still pass, since the derived values must
still satisfy whatever validation or uniqueness constraint the original
literals happened to satisfy by luck of not colliding yet. Watch specifically
for the coincidental-correctness trap while doing this refactor, if the field
being converted is on the expected-output side of an assertion rather than
the input side, stop, that field is a candidate for staying a Literal Value,
not for becoming derived.

To remove Derived Value from a fixture, most often because a test's intent
has shifted and the exact value of a previously incidental field is now the
point of the test, replace the helper call with a hand-typed literal chosen
specifically to exercise the new behavior, and delete the now-unused seed
plumbing, the counter increment or the test-name lookup, if nothing else in
the file still depends on it. This direction is rarer than the introduction
direction, most refactors move from hand-typed literals toward derived
values as a suite grows, not the other way, but it is the correct move
whenever a test is rewritten to specifically check an edge case that used to
live in a field nobody looked at closely.

## 15. Testing and verification

The derivation function itself is small, pure, and deterministic given its
seed, which makes it trivial to unit test directly, call it twice with the
same seed and assert the outputs are equal, call it with two different
seeds and assert the outputs differ, and if the function keeps a range
constraint, such as keeping a derived numeric value inside a valid database
column width, assert the boundary is respected at the seed values nearest
the wraparound point. What becomes harder to check, precisely because of
the indirection dimension 10 names as the pattern's cost, is confirming by
reading that a given test's assertions do not accidentally depend on the
specific derived value produced for that run, a test that only passes
because a counter happened to produce an even number is a hidden bug the
same shape as the classic Mystery Guest problem from the fixture
literature, and the only reliable way to catch it is deliberately rerunning
the suite with the counter starting from a different value, or running the
suite with test order randomized, both of which turn an accidental
dependency on a specific derived value into a visible flake rather than
leaving it hidden. Mutation testing is the most reliable verification tool
for the specific coincidental-correctness misuse named in dimension 11,
deliberately changing the production formula and confirming the test that
uses a derived expected value actually fails is the only direct evidence
that the derivation was not silently copying the code it is meant to check.

## 16. Observability signals

This pattern is a build-time and test-time technique, it produces no
production telemetry of its own because none of its code ships to
production, so there is nothing to log, trace, or alert on in a live system.
What is worth treating as a real observability concern is the test run's
own output, a well-built derivation function should make its seed visible in
whatever the test framework reports on failure, either because the derived
value itself contains a readable fragment of the seed, as recommended in
dimension 11's third failure mode, or because the test framework's own
structured output, JUnit XML's test name field or pytest's node ID, already
carries the seed information a reader would need. A CI dashboard that
tracks flaky-test reports is the closest thing to a health check for this
pattern in practice, a rising rate of intermittent failures localized to
tests that build fixtures through a shared derivation helper is the
practical early warning that the seed scoping described in dimension 11's
first failure mode has drifted.

## 17. Security and privacy implications

Where this pattern touches a genuine, non-hypothetical concern is data
generated for tests that run against a shared, non-isolated environment,
most often a staging database that multiple developers or CI jobs point at
concurrently. A derivation function built for local uniqueness alone, a
counter that resets to zero every process start, can produce values that
collide with rows another team's test run already inserted into that shared
environment, which is functionally a small-scale, accidental denial of
service against the shared resource rather than a security defect in the
usual sense. Teams that generate derived values resembling real personal
data, an email address pattern, a phone number pattern, or a name, in an
environment connected to a real email relay, a real SMS gateway, or a real
third-party API, should keep the derived values confined to a reserved,
clearly non-real space, for example a fixed domain suffix that the
organization's own mail and SMS infrastructure is set up to reject or
sandbox, so a derived test value can never accidentally reach a real
person. Beyond these two operational concerns this pattern has no bearing on
authentication, authorization, or cryptography, it is silent on those
surfaces because it is a data-provisioning technique for tests, not a
runtime mechanism.

## Code examples

Each example builds a small, deterministic derivation function from an
in-process counter and checks two things, that two calls in a row produce
different values, and that the output carries a readable fragment tying it
back to the caller. All three were compiled or run directly, TypeScript via
`tsc` plus `node`, Python via `python3`, and Go via `go run`.

### TypeScript

```typescript
// Derived Value: compute a unique, traceable test value from a counter.
let counter = 0;

function nextEmail(prefix: string): string {
  counter += 1;
  return `${prefix}-${counter}@example.com`;
}

function assertEqual(actual: unknown, expected: unknown, label: string): void {
  if (actual !== expected) {
    throw new Error(`${label} failed: expected ${expected}, got ${actual}`);
  }
}

function assertNotEqual(a: unknown, b: unknown, label: string): void {
  if (a === b) {
    throw new Error(`${label} failed: expected values to differ, both were ${a}`);
  }
}

function testDerivationIsUniquePerCall(): void {
  const first = nextEmail("user");
  const second = nextEmail("user");
  assertNotEqual(first, second, "derived emails must differ");
}

function testDerivationEmbedsTraceableFragment(): void {
  const value = nextEmail("order");
  assertEqual(value.startsWith("order-"), true, "derived value must carry its origin prefix");
}

testDerivationIsUniquePerCall();
testDerivationEmbedsTraceableFragment();
console.log("TypeScript derived-value tests passed");
```

### Python

```python
"""Derived Value: compute a unique, traceable test value from a counter."""
import itertools

_counter = itertools.count(1)


def next_email(prefix: str) -> str:
    n = next(_counter)
    return f"{prefix}-{n}@example.com"


def test_derivation_is_unique_per_call() -> None:
    first = next_email("user")
    second = next_email("user")
    assert first != second, "derived emails must differ"


def test_derivation_embeds_traceable_fragment() -> None:
    value = next_email("order")
    assert value.startswith("order-"), "derived value must carry its origin prefix"


if __name__ == "__main__":
    test_derivation_is_unique_per_call()
    test_derivation_embeds_traceable_fragment()
    print("Python derived-value tests passed")
```

### Go

```go
package main

import "fmt"

var counter = 0

func nextEmail(prefix string) string {
	counter++
	return fmt.Sprintf("%s-%d@example.com", prefix, counter)
}

func main() {
	first := nextEmail("user")
	second := nextEmail("user")
	if first == second {
		panic("derived emails must differ")
	}

	order := nextEmail("order")
	if len(order) < 6 || order[:6] != "order-" {
		panic("derived value must carry its origin prefix")
	}

	fmt.Println("Go derived-value tests passed")
}
```

## 18. References

1. Gerard Meszaros, *xUnit Test Patterns. Refactoring Test Code*,
   Addison-Wesley, 2007, chapter 11 (test data provision strategies,
   Literal Value, Generated Value, Derived Value) and chapter 18 (Test
   Logic in Production, the coincidental correctness discussion).
2. Nat Pryce, "Test Data Builders. an alternative to the Object Mother
   pattern", published 2007. The live site is unreachable (connection
   refused domain-wide), archived copy verified 2026-08-04.
   http://web.archive.org/web/20260801032913/http://www.natpryce.com/articles/000714.html
3. Martin Fowler, "Mocks Aren't Stubs", published 2 January 2007, verified
   2026-08-02. https://martinfowler.com/articles/mocksArentStubs.html
4. FactoryBot documentation, "Sequences", verified 2026-08-04.
   https://thoughtbot.github.io/factory_bot/sequences/summary.html
5. factory_boy documentation, "Sequences", verified 2026-08-02.
   https://factoryboy.readthedocs.io/en/stable/reference.html
6. JUnit 5 User Guide, "Dependency Injection for Constructors and Methods",
   verified 2026-08-02. https://docs.junit.org/current/user-guide/
7. pytest documentation, "How to use fixtures", the `request` fixture
   section, verified 2026-08-02.
   https://docs.pytest.org/en/stable/how-to/fixtures.html
8. Hypothesis documentation, "Writing custom strategies", verified
   2026-08-02. https://hypothesis.readthedocs.io/en/latest/data.html
9. Wikipedia contributors, "Test double", verified 2026-08-02.
   https://en.wikipedia.org/wiki/Test_double
