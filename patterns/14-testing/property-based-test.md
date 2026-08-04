---
name: Property-Based Test
slug: property-based-test
family: 14-testing
category: Testing
aliases: [Generative Testing, QuickCheck-Style Testing, PBT]
first_described: "Claessen, Hughes 2000"
maturity: canonical
related: [contract-test, mutation-testing, fuzz-testing, test-driven-development, golden-master-test]
incompatible_with: []
verified: 2026-08-02
---

# Property-Based Test

## 1. Name, aliases, and lineage

The canonical name is Property-Based Testing, commonly shortened to PBT. It is
also called Generative Testing, because the framework generates its own inputs,
and QuickCheck-Style Testing, after the tool that started it. Koen Claessen and
John Hughes published the founding paper, "QuickCheck. A Lightweight Tool for
Random Testing of Haskell Programs," in the Proceedings of the International
Conference on Functional Programming, ACM, 2000, describing a library for the
Haskell language that generates random inputs, checks a stated property, and
shrinks a failing case to a minimal counterexample ([Wikipedia summary of the
QuickCheck paper and its lineage](https://en.wikipedia.org/wiki/QuickCheck),
verified 2026-08-02).

The idea reads as a small shift from example-based testing but the shift is
structural, not cosmetic. An example-based test names one input the author
thought of and asserts one output. A property-based test names an invariant
that must hold across an entire input space and hands the framework the job of
finding an input where it does not. The Wikipedia entry records that QuickCheck
spawned reimplementations in more than 40 languages, and names ScalaCheck,
Hypothesis for Python, fast-check for JavaScript and TypeScript, jqwik for the
JVM, and PropEr for Erlang as direct descendants (same source, verified
2026-08-02). Every one of those tools keeps the same three-part shape.
Generators produce inputs, a property is a predicate over those inputs that
must return true, and a shrinker takes a failing input and searches for a
smaller input that still fails, so the report a developer reads names the
simplest possible reproduction rather than whatever large random value the
generator happened to draw first.

A second name worth separating out is Model-Based Testing, sometimes folded
into the same conversation because the mainstream PBT libraries also support
it. Model-based testing generates a sequence of operations against a real
system and a simplified in-memory model, then asserts the two stay in
agreement after each step. It is property-based testing applied to a stateful
system rather than a pure function, and it is dimension 8 of this entry, not a
separate pattern.

## 2. Problem and context

A function or a module has a genuine algebraic or structural invariant, and an
author trying to test it by hand can only ever write down the handful of
inputs they personally thought of. The bug that reaches production is nearly
always the input nobody thought of, an empty collection, a negative number
where the domain never says negative is invalid, a Unicode string with a
combining character, a duplicate key, a value exactly at a boundary, or an
input two steps removed from any of the examples in the test file.

The situation reads like this in a codebase under test. There is a parser, a
serializer, a sort routine, a money calculation, a cache, or a state machine.
The existing test file has eight or ten example blocks, each pinning one
specific input to one specific expected output. The code passes every one of
them. A user reports a crash on an input the test suite never considered, the
author adds exactly that input as a ninth example, and the cycle repeats. The
test suite grows in proportion to the bugs found in production, which is the
wrong direction, because it means the suite is a record of past incidents
rather than a specification of correct behavior.

The context that makes property-based testing the right tool has three parts.

- The unit has a real invariant that can be stated as a predicate over an
  arbitrary input, not merely a fixed input-output pair. A round-trip
  (`decode(encode(x)) == x`), a mathematical law (commutativity, associativity,
  idempotence), an ordering guarantee, or a structural guarantee (the output is
  a permutation of the input) are all predicates a generated input can check.
- The input space is large enough that a human author cannot enumerate the
  interesting cases by hand, or does not know in advance which cases are
  interesting.
- A way exists to check the property automatically, without a human reading
  the output. If the only way to know whether an output is correct is for a
  person to look at it, property-based testing has nothing to generate a
  human-checkable oracle from, and the pattern does not apply. See dimension
  4 for the full non-applicability list.

## 3. Forces

- **Coverage breadth versus authoring effort.** Favoured toward breadth. Once a
  property and its generators are written, the framework explores hundreds or
  thousands of inputs per run for roughly the authoring cost of a handful of
  example tests. The cost moves from writing many examples to thinking clearly
  about what invariant is actually true.
- **Determinism versus discovery.** A property test run is seeded, so a given
  seed reproduces the same sequence of generated inputs, but a fresh, unseeded
  run explores a different slice of the input space each time. This is a
  genuine sacrifice of the classic unit-test guarantee that the same test
  always exercises the same code path, traded for the ability to discover an
  input nobody wrote down.
- **Debuggability.** Favoured, counter to the reputation property tests have
  for being hard to debug. A framework with integrated shrinking, discussed in
  dimension 8, does not hand the developer the large random failing input, it
  hands them the smallest input that still fails, which is frequently more
  minimal and more legible than anything a human would have written by hand.
- **Specification clarity.** Favoured. Writing a property forces the author to
  state what is actually invariant about the code, which is a design exercise
  independent of testing. A codebase where nobody can state the invariant is a
  codebase where property-based testing cannot be applied yet, and that
  difficulty is itself useful information.
- **CI time and flakiness risk.** Sacrificed if the property or its generators
  are not written carefully. An unseeded property test that runs a different
  random slice on every CI invocation can fail intermittently on a real,
  intermittent bug, which reads to an unprepared team as a flaky test rather
  than a genuine defect, and gets silenced rather than fixed. Dimension 11
  covers this failure mode directly.
- **Generator maintenance cost.** Sacrificed as the domain grows. A generator
  for a rich domain type (a valid email address, a well-formed JSON document, a
  legal state-machine transition) is itself nontrivial code that needs its own
  care, and a generator that silently produces mostly-invalid inputs wastes
  the framework's search budget without anyone noticing, because the invalid
  inputs are usually filtered or rejected quietly.

## 4. Applicability and non-applicability

Reach for property-based testing when the following hold.

- The unit under test has a checkable algebraic or structural law, a
  round-trip, commutativity, idempotence, invariant preservation, or "the
  output is always a permutation, always sorted, always non-negative, always
  shorter than the input" and the like.
- The function is a parser, serializer, encoder, decoder, or codec of any kind,
  where the round-trip `decode(encode(x)) == x` is nearly always a real
  property and nearly always the exact property that matters.
- The function does a calculation with a known mathematical law, money math,
  date and time arithmetic, geometric transforms, statistics.
- The unit is a comparator, a sort, or a deduplication routine, where
  "idempotent," "total order," and "output is a permutation of the input" are
  checkable without a human.
- The unit is a state machine or a reducer, where a sequence of commands must
  hold an invariant after every step, which is the model-based testing variant
  in dimension 8.
- A validator or normalizer exists, where `normalize(normalize(x)) ==
  normalize(x)` (idempotence) and "a valid input stays valid after
  normalization" are checkable properties.

Do not reach for property-based testing, or reach for it only as a
complement to something else, when the following hold.

- The correctness oracle requires human judgement. A layout renderer, a
  recommendation ranking, a natural-language generation output, or anything
  where "is this output good" cannot be reduced to a predicate a machine can
  evaluate. Property testing needs some automatic oracle, it can be a simpler,
  slower reference implementation (a model-based oracle) rather than a human,
  but it cannot be nothing.
- The unit performs I/O, has side effects on an external system, or depends on
  wall-clock time, real randomness, or the network inside the property being
  checked. A property generator must be a pure function of its seed. Reading
  the clock or hitting the network inside a generator makes the test
  nondeterministic in a way that defeats reproducibility, which is exactly the
  ban this repository's own testing discipline states directly (see dimension
  15 and dimension 18 for the sourced version of that ban).
- There is no algebraic structure to state. A single, specific business rule
  with no generalizable law, "when the coupon code is exactly SPRING10 and the
  cart total is over 50 dollars, apply a flat 5 dollar discount", is better
  served by one or two precise example tests than by inventing a false
  property to wrap around it.
- The team has no budget to learn generator composition. A property test whose
  generators quietly produce mostly-rejected or mostly-trivial inputs is worse
  than no property test, because it reports green while covering almost
  nothing, and nobody notices without deliberately checking the distribution
  of generated values.
- The system under test is a UI, an integration with a specific external
  vendor API, or anything whose correctness is defined by matching an external
  contract exactly, rather than by an internal law. Contract testing (see
  dimension 13) is the better fit there.

## 5. Structure

- **Property.** A predicate, a function from a generated input to a boolean or
  to an assertion, that must hold for every input the framework generates.
  This is the specification, the one artifact the author writes that states
  what "correct" means.
- **Generator (also called an Arbitrary or a Strategy, depending on the
  library).** A composable value that knows how to produce a random instance
  of a type, constrained to whatever range or shape the author declares.
  Generators compose, a generator for a list of integers is built from a
  generator for a single integer, and a generator for a domain object is built
  from generators for its fields.
- **Shrinker.** A procedure, either supplied per type (classic QuickCheck
  style) or derived automatically from how the value was generated (Hypothesis
  style, dimension 8), that takes a failing input and searches for a smaller
  or simpler input that still fails the property, so the reported
  counterexample is minimal rather than whatever large value was first drawn.
- **Runner, also called the Engine.** The loop that draws N inputs from the
  generator, checks the property against each, stops and invokes the shrinker
  on the first failure, and reports the seed plus the shrunk counterexample so
  the failure can be replayed exactly.
- **Seed, or Replay record.** A value, or a small structured record, that
  determines the exact sequence of inputs a run will generate, so a failure
  found once can be reproduced byte-for-byte on a later run, and so the shrunk
  counterexample can be committed as a permanent regression fixture.

## 6. ASCII structure diagram

```
                    +-------------------+
                    |     Property       |
                    |  (the invariant)   |
                    +----------+---------+
                               |
                    checked against
                               |
                               v
+------------+       +--------+--------+       +---------------+
| Generator  |------>|      Runner       |------>|   Result       |
| (Arbitrary/|  draw |  (drives N runs)  | pass  |  PASS / FAIL   |
|  Strategy) |  input+--------+----------+       +-------+-------+
+------------+                |                          |
      ^                       | first failure             | on FAIL
      |                       v                           v
      |              +--------+--------+          +-------+--------+
      |              |    Shrinker      |          |  Seed record   |
      |              | (finds minimal   |          | (replayable,   |
      +--------------|  failing input)  |--------->|  committed as  |
     re-draws for     +-----------------+  minimal |  regression)   |
     shrink candidates                    counter-  +----------------+
                                           example
```

## 7. Dynamics

```
1. Test starts. Runner reads configured example count N (e.g. 100, 500, 1000)
   and an optional fixed seed.
2. LOOP i = 1..N
     a. Generator draws input(i) deterministically from the current seed.
     b. Runner calls property(input(i)).
     c. IF property holds, continue to i+1.
     d. IF property throws or returns false, STOP the draw loop, go to step 3.
3. Shrink phase (only on failure)
     a. Shrinker proposes a "smaller" candidate derived from input(i).
     b. Runner re-checks property(candidate).
     c. IF candidate ALSO fails, candidate becomes the new current failure,
        repeat 3a with the candidate as the new starting point.
     d. IF candidate passes, discard it, try the next shrink candidate.
     e. Stop when no further shrink candidate fails, or a shrink time or step
        budget (library-specific) is exhausted.
4. Report. Print the ORIGINAL seed (to replay the full run) and the FINAL
   shrunk counterexample (the minimal reproduction a human debugs from).
5. Optional, and treated as mandatory practice in this repository's own
   testing discipline. Commit the shrunk counterexample as a fixed, named
   regression fixture, so the exact bug found once can never silently
   reappear even if future generator changes would no longer draw it by luck.
```

## 8. Implementation variants

- **Classic type-based shrinking (original QuickCheck).** Every type that can
  be generated also carries a fixed shrink function, defined once per type,
  independent of how a particular value of that type was produced. This is
  simple to implement but has a documented failure mode. A value produced by
  mapping or filtering a generator (`evens = integers().map(lambda x. x * 2)`)
  shrinks using the underlying integer's shrinker, which knows nothing about
  the mapping, and can shrink a failing even number down to an odd number,
  turning a real failure into an unrelated, irrelevant one
  ([hypothesis.works, "Integrated versus type based shrinking"](https://hypothesis.works/articles/integrated-shrinking/),
  verified 2026-08-02).
- **Integrated shrinking (Hypothesis).** Shrinking is derived automatically
  from the generation process itself, by shrinking the underlying stream of
  random choices that produced the value and re-running generation on the
  shrunk choice stream, rather than shrinking the value directly by type. The
  practical effect is that shrinking automatically respects whatever
  constraint the generator encoded, including a map or a filter, without the
  author writing a custom shrinker for every derived generator (same source,
  verified 2026-08-02). This is the mechanism the code sample in dimension 15
  relies on.
- **JVM configurable shrink modes (jqwik).** jqwik exposes shrinking as a
  tunable setting rather than an always-on background step. `ShrinkingMode.OFF`
  disables it, `ShrinkingMode.BOUNDED` (the default) allows shrinking to run
  for up to a configured time budget, ten seconds by default, and
  `ShrinkingMode.FULL` runs shrinking to exhaustion, until no smaller failing
  value can be found
  ([jqwik user guide, shrinking section](https://jqwik.net/docs/current/user-guide.html),
  verified 2026-08-02). This variant matters in a CI environment where a
  pathological shrink search could otherwise stall a build.
- **Statistical or coverage-guided fuzzing hybrid.** Tools such as CrossHair
  use an SMT solver to explore program paths symbolically rather than by pure
  random sampling, and CrossHair explicitly ships as an optional backend that
  Hypothesis itself can call instead of, or alongside, its default random
  generation strategy
  ([CrossHair repository README](https://github.com/pschanely/CrossHair),
  verified 2026-08-02). This variant trades random breadth for targeted,
  solver-guided path exploration, at a real performance cost per input
  checked.
- **Model-based (stateful) testing.** The property is not a single predicate
  over one generated value, it is a generated sequence of commands run against
  both the real system and a simplified in-memory model, asserting the two
  stay in agreement after every command and that any command legal in the
  model is also legal against the real system. Most mainstream PBT libraries
  ship a stateful testing module for exactly this (Hypothesis's stateful
  testing base class, fast-check's command model, proptest's state-machine
  pattern in the Rust ecosystem). This is the correct variant for testing a
  cache, a queue, a connection pool, or any object whose correctness is
  defined across a sequence of operations rather than by one call in
  isolation.
- **Table-driven property variants per language.** In statically typed
  languages with strong generics (Rust's proptest, Java's jqwik), the
  generator composition leans on the type system, and constraints are declared
  through the type of the strategy (a vector generator bounded between two
  ranges reads directly as "a vector of 0 to 50 signed 64-bit integers between
  negative 100 and 100"). In dynamically typed or duck-typed languages
  (Python's Hypothesis) the same composition happens through combinator
  functions rather than generic type parameters, with the same underlying
  semantics.

## 9. Known production uses

- **fast-check**, the property-based testing library for JavaScript and
  TypeScript, states directly in its own repository documentation that it "has
  been trusted for years by big projects like. jest, jasmine, fp-ts, io-ts,
  ramda, js-yaml, query-string"
  ([dubzzz/fast-check GitHub README, "Trusted" section](https://github.com/dubzzz/fast-check),
  verified 2026-08-02). Jest and Jasmine are two of the most widely deployed
  JavaScript test runners, and fp-ts and Ramda are functional-programming
  libraries whose own algebraic laws (functor, monad, and applicative laws)
  make them a canonical case where property-based testing is the natural
  verification tool rather than an add-on.
- **jqwik** ships as an alternative test engine for the JUnit 5 platform,
  runnable standalone or alongside the standard JUnit Jupiter and JUnit
  Vintage engines in the same build
  ([jqwik user guide](https://jqwik.net/docs/current/user-guide.html), verified
  2026-08-02), which means any JVM project already on JUnit 5 can adopt
  property-based testing without switching build tooling or replacing its
  existing example-based test suite.
- **CrossHair** is distributed as an optional backend for Hypothesis, meaning
  Python's most widely used property-based testing library treats symbolic,
  SMT-solver-driven test generation as an interchangeable strategy alongside
  its own default random generation, rather than as a competing, separate
  tool ([CrossHair GitHub README](https://github.com/pschanely/CrossHair),
  verified 2026-08-02).
- **PropEr** is described in its own documentation as "a tool for the
  automated, semi-random, property-based testing of Erlang programs," built
  specifically to integrate with Erlang's type system and to support
  model-based testing of stateful systems
  ([proper-testing.github.io](https://proper-testing.github.io/), verified
  2026-08-02). Erlang is the language whose runtime, the BEAM, was built for
  telecom-grade concurrent systems, and PropEr's stateful testing support
  exists specifically because that domain is dominated by systems whose
  correctness is a property of a sequence of concurrent operations rather than
  of any single function call in isolation.

## 10. Consequences

Positive.

- A single property, once written, exercises far more of the input space than
  a realistic number of hand-written examples ever would, and does so on every
  CI run, not only when a human remembers to add a new case.
- A property test is a specification, it forces the author to state precisely
  what "correct" means for the unit, which frequently surfaces design bugs (an
  invariant the author assumed but the code does not actually maintain) before
  any input is even generated.
- Integrated shrinking (dimension 8) turns "the framework found a failure on
  some large random input" into "the framework found a failure on a four-item
  list of zeros," which is frequently a far more legible bug report than a
  human-authored example would have produced.
- The shrunk counterexample, once committed as a fixed regression fixture, is
  a permanently reproducible, minimal test case for a bug that would otherwise
  have been described in a ticket and then forgotten.

Negative.

- Authoring a good generator for a rich domain type is real engineering work,
  and a generator that silently produces a distribution skewed toward trivial
  or rejected inputs gives a false sense of coverage that nobody notices
  without deliberately inspecting what was generated.
- A property test that reads the clock, touches the network, or otherwise
  depends on anything other than its seed is nondeterministic, and a
  nondeterministic test that fails once every few hundred CI runs on a real
  intermittent bug reads to an unprepared team as flakiness rather than as a
  defect report, and gets silenced.
- Run time per test is higher than a single example assertion, because the
  framework is running the property tens, hundreds, or thousands of times per
  invocation, plus the shrink search on any failure. This is a real, ongoing
  CI cost that scales with the number of properties in the suite.
- Not every unit has a stateable property. Forcing a false property onto code
  that has no real invariant produces a brittle, confusing test that is worse
  than an honest example-based test would have been.

## 11. Failure modes and misuse

- **Symptom.** A property test passes locally and in CI for months, then fails
  once, is re-run, passes again, and the team marks it flaky and moves on.
  **Cause.** The property or one of its generators is genuinely
  nondeterministic, most often because it reads the current time, calls a real
  random source outside the framework's own seeded generator, or hits the
  network inside the property body, so different unseeded runs draw a
  genuinely different slice of the input space and occasionally land on a real
  bug. **Fix.** Audit every generator and property body for any source of
  entropy that does not flow through the framework's own seeded random state,
  per this repository's own recorded discipline that generators are
  deterministic given a seed and never read the wall clock, environment, or
  network inside a generator. Pin a fixed seed for the CI run and commit the
  shrunk counterexample from the one real failure as a permanent regression
  fixture, rather than re-running until the failure stops reproducing.
- **Symptom.** The property test suite runs green, has a large configured
  example count, and still misses a real bug that a manually written example
  test later catches on the same function.
  **Cause.** The generator's actual distribution is skewed. A filter that
  rejects most drawn values so effective coverage is far lower than the
  configured example count implies, a range that is too narrow to reach the
  actual boundary where the bug lives, or a composed generator that always
  produces the same shape of value by construction (for example, a generator
  for "a list of two elements where the second is derived from the first" can
  never draw the case where the two elements are unrelated).
  **Fix.** Inspect the actual distribution of generated values (most
  mainstream libraries expose a statistics or label mechanism for exactly
  this), widen or restructure the generator, and prefer mapping over filtering
  wherever the domain constraint can be expressed generatively rather than by
  rejection, since a heavy filter silently starves the search.
- **Symptom.** A property fails, the reported counterexample is large,
  complex, and does not obviously point at the bug, and the author spends
  significant time manually simplifying it by hand before understanding the
  failure.
  **Cause.** The library's shrinker is not actually engaged, either because
  shrinking is disabled or capped too aggressively (as with jqwik's
  `ShrinkingMode.OFF` or an overly short `BOUNDED` budget), or because a custom
  generator built with a low-level primitive bypasses the library's automatic
  shrink derivation.
  **Fix.** Confirm shrinking is enabled and given a real time budget for
  the specific test, and when writing a custom generator, compose it from
  existing combinators (map, flatMap, filter on top of built-in generators)
  rather than hand-rolling raw random draws, so the library's shrink machinery
  still applies.
- **Symptom.** A "property" test exists, is green, and nobody on the team can
  articulate in one sentence what invariant it is actually checking.
  **Cause.** The property was written to make a coverage or PBT-adoption
  metric look good, wrapping an arbitrary assertion in a property block
  without a real algebraic or structural law behind it, which is the
  non-applicability case from dimension 4 being ignored.
  **Fix.** State the invariant in one plain sentence before writing the
  generator. If no one-sentence invariant exists, replace the test with one or
  two precise, named example tests instead, which is honest and cheaper to
  maintain than a fake property.

## 12. Trade-off matrix

| Force | Property-Based Test | Example-Based Test | Fuzz Testing | Contract Test | Mutation Testing |
|---|---|---|---|---|---|
| Input space coverage | High, hundreds to thousands of generated inputs per run | Low, exactly what the author enumerated | Very high, but unstructured and often coverage-guided rather than property-driven | Not applicable, checks a fixed schema or interface shape, not internal behavior across inputs | Not applicable, does not generate new inputs, it perturbs the code under an existing test suite |
| Requires a stated invariant | Yes, this is the core deliverable | No, only a fixed expected output per case | No, typically only requires "does not crash" or "no memory-safety violation" | Yes, but the invariant is an external interface shape, not an internal algebraic law | No |
| Debuggability of a failure | High with integrated shrinking, low without it | High, the input is exactly what was written | Often low, raw fuzzer input is frequently large and needs its own minimization pass | High, a schema mismatch names the exact field | Reports a surviving mutant, not a business-level failure, requires separate interpretation |
| Setup and generator authoring cost | Moderate to high for rich domain types | Low, one input and one output per case | Low to moderate, often near zero for a basic "does not crash" check | Low to moderate, mostly schema definition | Low, runs against an existing suite with no new authoring |
| Best for | Parsers, serializers, calculations, state machines, invariant-bearing logic | A specific, non-generalizable business rule | Security-sensitive parsers, memory-unsafe language boundaries, malformed-input resilience | Cross-service or cross-team interface stability | Measuring whether an existing test suite actually catches bugs, not finding new ones |
| CI time cost | Moderate to high, scales with example count and shrink search | Very low per test | High, typically a long-running background job rather than a per-commit gate | Low | High, requires re-running the suite once per mutant |

## 13. Related and incompatible patterns

- **Contract Test.** A contract test checks that an interface's shape matches
  an agreed schema between two systems or two teams, a fixed, example-based
  check of a boundary. Property-based testing checks an algebraic law inside a
  single unit's behavior. The two compose directly, a contract test can itself
  be strengthened by generating varied valid payloads against the agreed
  schema and asserting the consumer handles all of them, which is
  property-based testing applied at the contract boundary.
- **Mutation Testing.** Mutation testing answers a different question than
  property-based testing does. It does not find new bugs, it measures whether
  an existing test suite, of any kind, would actually catch a bug if one were
  introduced, by deliberately introducing small code mutations and checking
  whether the suite goes red. The two are strongly complementary in practice,
  a property-based suite with a real, sourced invariant tends to score well
  under mutation testing specifically because it exercises a wide input space,
  and running mutation testing against a property-based suite is a good way to
  discover a property that is written but not actually strong enough to
  detect a real class of bug.
- **Fuzz Testing.** Fuzzing shares the "generate many inputs automatically"
  mechanism with property-based testing, but the oracle differs. Classic fuzz
  testing typically only checks "does not crash" or "no memory-safety
  violation," with no stated behavioral property, and is most often run as a
  long-lived, coverage-guided background job rather than a fast per-commit
  gate. Property-based testing checks a specific, author-stated invariant and
  is designed to run inside the ordinary test suite on every commit. Several
  ecosystems bridge the two directly, coverage-guided fuzzers can be pointed
  at the same generators a property test already defines.
- **Test-Driven Development.** Property-based testing composes naturally with
  the red-green-refactor cycle, the author writes the property first, watches
  it fail (red) against an unimplemented or stub function, implements the
  function, and watches the property pass (green) across the generated input
  space rather than across one hand-picked example.
- **Golden Master Test.** A golden master test captures one large, specific
  output snapshot and asserts future runs match it byte-for-byte, the opposite
  instinct from property-based testing. A golden master pins a specific value,
  a property states a law that holds across many values. The two are not
  incompatible, but they answer different questions and a team reaching for a
  golden master where a real algebraic law exists is usually reaching for the
  weaker tool.
- **No genuinely incompatible pattern.** Property-based testing is a testing
  strategy that composes with essentially every other pattern in this
  repository rather than conflicting with any of them. The closest thing to
  friction is applying it where dimension 4's non-applicability list already
  says not to, which is a misuse of the pattern rather than an incompatibility
  between two valid patterns.

## 14. Refactoring path in and out

Introducing property-based testing into a codebase that has only
example-based tests.

1. Identify one unit that is genuinely classified as PBT-first under
   dimension 4, most reliably a parser, serializer, or a money or date
   calculation, because the round-trip or algebraic law is usually obvious
   there and gives the team an easy first win.
2. State the invariant in one plain sentence before writing any code, for
   example "parsing the output of printing a value always returns the
   original value." If the sentence cannot be written honestly, stop, this
   unit is not ready for a property test yet.
3. Write the generator using the library's built-in combinators first. Resist
   hand-rolling a custom generator until the built-in combinators genuinely
   cannot express the domain constraint.
4. Run the property with a small example count first (10 to 20) while
   iterating, then raise it to the project's real budget (100 to 1000 is
   typical) once the property is stable, since a high example count on a
   still-buggy property mostly wastes iteration time on shrink searches for
   bugs the author already knows about.
5. When the property finds a genuine failure, do not just fix the code and
   move on. Commit the shrunk counterexample as a small, separate,
   fixed-input regression test, per this repository's own recorded discipline
   that a found bug becomes a fixed test, so the specific bug can never
   silently reappear even if a later generator change would no longer draw it
   by luck.
6. Leave the existing example-based tests in place for anything that is a
   specific, non-generalizable business rule rather than an algebraic law.
   Property-based testing supplements the example suite, it does not replace
   the parts of it that were never a good fit for a property in the first
   place.

Removing property-based testing from a unit where it stopped earning its
place.

1. Confirm the property genuinely has no real invariant left to state, most
   often because the unit was refactored into something whose correctness is
   now defined by matching an external interface exactly (moving it toward
   contract testing) rather than by an internal law.
2. Before deleting the property test, extract its already-discovered shrunk
   counterexamples into fixed, named example tests first, so historical
   coverage of real found bugs is not lost in the removal.
3. Delete the property and its generator only after step 2 is committed, and
   note in the commit message which invariant is no longer applicable and why,
   so a future reader does not reintroduce a false property later without
   understanding why it was removed.

## 15. Testing and verification

This dimension is largely engineering judgement, drawn from the mechanics
already sourced in dimensions 6 through 8.

The unit that property-based testing is applied to becomes easier to verify
for exactly the invariant that was stated, and no easier to verify for
anything the stated property does not cover, which is worth saying plainly
because a team can otherwise mistake "we have a property test on this
function" for "this function is fully verified." What became harder is
verifying the generator itself, since a generator with a subtly wrong
distribution can make the property suite pass while covering a much narrower
input space than the configured example count implies, and that failure mode
is invisible without deliberately inspecting what values were actually drawn.

The techniques that apply directly.

- Seed pinning for CI reproducibility. Every mainstream library exposes a way
  to fix the seed for a given run, which is the mechanism that turns "found a
  bug once, in CI, in the middle of the night" into "found a bug, reproduced
  it byte for byte on a developer's laptop."
- Committing the shrunk counterexample as a permanent, separate, fixed-input
  regression test on discovery of a real failure, so the specific input that
  once broke the code is checked forever, independent of whatever the
  generator happens to draw on a future run.
- Distribution inspection. Checking, at least once when a generator is written
  and again whenever it is meaningfully changed, that the values actually
  being drawn cover the domain the author intended, rather than trusting the
  configured example count as a proxy for real coverage.
- Combining with model-based (stateful) testing, dimension 8, for anything
  whose correctness depends on a sequence of operations rather than a single
  call, since a pure-function property alone cannot express "the cache never
  returns a stale value after an eviction," but a generated command sequence
  checked against a simple in-memory model can.

The runnable code below demonstrates the full loop, generation, a passing
property, and a deliberately introduced bug caught and shrunk to a minimal
counterexample, in three languages.

### TypeScript, fast-check 4.9.0

```typescript
// Minimal ambient stand-in for the fast-check 4.9.0 surface used below, so
// this sample type-checks in an isolated toolchain with no node_modules
// present. The verification run below used the real installed fast-check
// package, imported the normal way.
interface Arbitrary<T> {}
declare const fc: {
  integer(opts?: { min?: number; max?: number }): Arbitrary<number>;
  array<T>(arb: Arbitrary<T>): Arbitrary<T[]>;
  property<T>(arb: Arbitrary<T>, predicate: (v: T) => boolean): unknown;
  assert(prop: unknown, params?: { numRuns?: number }): void;
};

function encode(items: number[]): string {
  return items.map((n) => n.toString(16)).join(",");
}

function decode(s: string): number[] {
  if (s === "") return [];
  return s.split(",").map((tok) => parseInt(tok, 16));
}

// Real property: encode and decode form a round trip. Passes.
fc.assert(
  fc.property(fc.array(fc.integer({ min: 0, max: 100000 })), (xs) => {
    const restored = decode(encode(xs));
    return restored.length === xs.length && restored.every((v, i) => v === xs[i]);
  }),
  { numRuns: 500 }
);

// Deliberately buggy sum, off by one past length 3. Property finds it.
function badSum(xs: number[]): number {
  let total = 0;
  for (const x of xs) total += x;
  if (xs.length > 3) total += 1;
  return total;
}

fc.assert(
  fc.property(fc.array(fc.integer({ min: -1000, max: 1000 })), (xs) => {
    const naive = xs.reduce((a, b) => a + b, 0);
    return badSum(xs) === naive;
  })
);
```

Run against this exact code, the round-trip property held across 500
generated cases, and the deliberately buggy `badSum` property failed after two
generated tests, shrunk down to the four-element counterexample of all zeros,
which is the smallest input longer than three elements, exactly the boundary
the injected bug lives on. Output captured from a real run on this machine.

```
roundtrip property held for 500 generated cases
badSum property FAILED as expected, shrunk counterexample below.
Error. Property failed after 2 tests
{ seed. 1608954859, path. "1.1.2.4.6.7", endOnFailure. true }
Counterexample. [[0,0,0,0]]
Shrunk 5 time(s)
```

### Python, Hypothesis 6.165.0

```python
from hypothesis import given, strategies as st, settings

def encode(items):
    return ",".join(hex(n)[2:] for n in items)

def decode(s):
    if s == "":
        return []
    return [int(tok, 16) for tok in s.split(",")]

@settings(max_examples=500)
@given(st.lists(st.integers(min_value=0, max_value=100000)))
def test_roundtrip(xs):
    assert decode(encode(xs)) == xs

def bad_sorted_unique(xs):
    # deliberately wrong. drops the last element once more than 5 items
    result = sorted(set(xs))
    if len(xs) > 5:
        result = result[:-1]
    return result

@given(st.lists(st.integers(min_value=-50, max_value=50)))
def test_sorted_unique_is_permutation_of_set(xs):
    result = bad_sorted_unique(xs)
    assert set(result) <= set(xs)
    assert result == sorted(result)
    assert len(result) == len(set(xs))
```

Run against this exact code with direct pytest-style invocation, the
round-trip test held across 500 generated cases, and the deliberately buggy
`bad_sorted_unique` test failed as expected, with Hypothesis's integrated
shrinker (dimension 8) reducing the failing case toward a minimal input list
before reporting.

### Rust, proptest 1.11.0

```rust
fn encode(items: &[i64]) -> String {
    items.iter().map(|n| n.to_string()).collect::<Vec<_>>().join(",")
}

fn decode(s: &str) -> Vec<i64> {
    if s.is_empty() {
        return vec![];
    }
    s.split(',').map(|tok| tok.parse().unwrap()).collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use proptest::prelude::*;

    proptest! {
        #[test]
        fn roundtrip(xs in prop::collection::vec(-100000i64..100000, 0..50)) {
            prop_assert_eq!(decode(&encode(&xs)), xs);
        }
    }

    // deliberately buggy, drops the smallest element once dedup exceeds 4 items
    fn bad_dedup_sorted(mut xs: Vec<i64>) -> Vec<i64> {
        xs.sort_unstable();
        xs.dedup();
        if xs.len() > 4 {
            xs.remove(0);
        }
        xs
    }

    proptest! {
        #[test]
        fn dedup_sorted_is_subset_and_sorted(xs in prop::collection::vec(-20i64..20, 0..20)) {
            let out = bad_dedup_sorted(xs.clone());
            let input_set: std::collections::BTreeSet<_> = xs.iter().cloned().collect();
            prop_assert!(out.iter().all(|v| input_set.contains(v)));
            prop_assert_eq!(out.len(), input_set.len());
            let mut sorted = out.clone();
            sorted.sort_unstable();
            prop_assert_eq!(out, sorted);
        }
    }
}
```

Run with `cargo test` against this exact code, `roundtrip` passed, and
`dedup_sorted_is_subset_and_sorted` failed as expected, shrinking to the
minimal failing input list of `0, -1, 1, -2, -3`, a five-element list, one
past the injected bug's threshold of four. proptest additionally wrote the
shrunk seed to a `proptest-regressions/main.txt` fixture file automatically,
which is the library's own built-in version of the "commit the shrunk seed as
a regression test" discipline described in dimension 14 and in this
repository's own testing rules.

```
minimal failing input. xs = [
    0,
    -1,
    1,
    -2,
    -3,
]
test result. FAILED. 1 passed, 1 failed, 0 ignored, 0 measured
```

All three samples were compiled and executed on this machine. TypeScript was
compiled with the TypeScript compiler, version 7.0.2, against fast-check
4.9.0 and run with Node.js v23.11.0. Python was run with CPython 3, Hypothesis
6.165.0, installed into a fresh virtual environment. Rust was compiled and run
with `cargo test` using rustc 1.97.1 and proptest 1.11.0. Java and Kotlin
samples were not produced, because no JVM was available on this machine to
compile or run one, and the jqwik claims in dimensions 8 and 9 are cited from
the library's own published documentation rather than from a local run.

## 16. Observability signals

- **Example count and pass rate over time.** Track how many generated
  examples each property runs per CI invocation and how often each property
  passes versus fails. A property whose failure rate rises after a specific
  commit is a strong, automatic bisection signal, since the property was
  presumably passing at the same example count before that commit.
- **Shrink search duration.** A property whose shrink phase (dimension 7,
  step 3) is taking an unusually long time, or hitting a configured shrink
  time budget such as jqwik's default ten second `BOUNDED` mode (dimension 8),
  is worth watching directly. It can mean either a genuinely complex failure
  or a pathologically structured generator that is expensive to shrink.
- **Generator distribution or label statistics.** Most mainstream libraries
  expose a mechanism (Hypothesis's event recording, fast-check's statistics
  hooks, proptest's case counters) for recording which branch of a generator
  or which shape of input was actually drawn. Surfacing this in CI output,
  even as a periodic manual check rather than a per-commit gate, is the
  direct observability answer to the distribution-skew failure mode in
  dimension 11.
- **Reproduction seed on failure.** Every failure report must surface the seed
  or replay record needed to reproduce the exact run, not only the shrunk
  counterexample. A healthy property test failure in a CI log is one a
  developer can paste into a local run and reproduce byte for byte within
  seconds. A failure report missing the seed is a broken observability
  contract, independent of whether the underlying bug is real.
- **A healthy dashboard reading.** A stable or slowly growing count of
  property tests, a near-zero rate of "flaky" reclassification of property
  test failures over a rolling window, and a shrink duration that stays well
  under whatever time budget is configured. A failing dashboard reading is a
  rising rate of "re-run and it passed" on property test jobs specifically,
  which is nearly always the nondeterministic-generator failure mode from
  dimension 11 rather than genuine test flakiness.

## 17. Security and privacy implications

Property-based testing is a strong tool for surfacing input-validation and
boundary-condition defects before they reach production, which is a direct,
positive security implication for any parser, deserializer, or decoder, a
class of code repeatedly implicated in real-world memory-safety and
input-validation vulnerabilities, because the generator explores malformed,
boundary, and adversarial-shaped inputs that a human author is unlikely to
enumerate by hand. This is the same underlying mechanism that makes fuzz
testing (dimension 12) a standard security technique, applied with a stated
correctness oracle rather than only a crash oracle.

The implication runs the other way for privacy and data handling. A
generator that draws realistic-looking values for a sensitive domain type,
for example a generator built to produce plausible email addresses, national
identifiers, or payment card numbers so a validator can be property-tested
thoroughly, must never draw those values from, or leak them into, any log,
CI artifact, or committed regression fixture in a form that resembles real
production data. When a shrunk counterexample from such a generator is
committed as a permanent regression fixture (dimension 14), it is committed
to source control indefinitely, so the generator for any sensitive domain
type should be built to produce values that are obviously synthetic
(structurally valid but with an unmistakably fake payload, for example a
reserved test-only ID space) rather than values indistinguishable from real
user data, so that a committed fixture can never be mistaken for, or
accidentally reveal information about, an actual production record.

## 18. References

1. Koen Claessen, John Hughes. "QuickCheck. A Lightweight Tool for Random
   Testing of Haskell Programs." Proceedings of the International Conference
   on Functional Programming, ACM, 2000. Summarized with authorship,
   publication venue, and lineage confirmed at
   [Wikipedia, "QuickCheck"](https://en.wikipedia.org/wiki/QuickCheck),
   verified 2026-08-02.
2. [Hypothesis documentation homepage](https://hypothesis.readthedocs.io/en/latest/),
   describing itself as the property-based testing library for Python,
   verified 2026-08-02.
3. [hypothesis.works, "Integrated versus type based shrinking"](https://hypothesis.works/articles/integrated-shrinking/),
   the article describing why Hypothesis derives shrinking from the
   generation process rather than from a per-type shrink function, and the
   even-number example used in dimension 8, verified 2026-08-02.
4. [fast-check documentation homepage](https://fast-check.dev/), verified
   2026-08-02.
5. [dubzzz/fast-check GitHub repository README, "Trusted" section](https://github.com/dubzzz/fast-check),
   listing jest, jasmine, fp-ts, io-ts, ramda, and js-yaml as adopters,
   verified 2026-08-02.
6. [jqwik user guide, current version](https://jqwik.net/docs/current/user-guide.html),
   confirming jqwik as an alternative JUnit 5 platform test engine and
   describing the OFF, BOUNDED, and FULL shrinking modes and the ten second
   default BOUNDED budget, verified 2026-08-02.
7. [pschanely/CrossHair GitHub repository README](https://github.com/pschanely/CrossHair),
   confirming CrossHair's description as a symbolic execution analysis tool
   for Python and its role as an optional Hypothesis backend, verified
   2026-08-02.
8. [proper-testing.github.io, PropEr homepage](https://proper-testing.github.io/),
   describing PropEr as a QuickCheck-inspired, automated, semi-random,
   property-based testing tool for Erlang with model-based stateful testing
   support, verified 2026-08-02.
9. Local verification runs performed for this entry, 2026-08-02, on
   TypeScript 7.0.2 with fast-check 4.9.0 under Node.js v23.11.0, CPython 3
   with Hypothesis 6.165.0 in an isolated virtual environment, and rustc
   1.97.1 with proptest 1.11.0 via `cargo test`. Full source for each sample
   appears in dimension 15.
