---
name: Test Pyramid
slug: test-pyramid
family: 14-testing
category: Testing Strategy
aliases: [Testing Pyramid, Cohn's Pyramid, Test Automation Pyramid]
first_described: "Cohn 2009"
maturity: established
related: [four-phase-test, contract-test, fake, mock, mutation-test, characterization-test]
incompatible_with: []
verified: 2026-08-02
---

# Test Pyramid

## 1. Name, aliases, and lineage

The canonical name is Test Pyramid, sometimes written Testing Pyramid. The
shape is attributed to Mike Cohn, who introduced it in his book *Succeeding
with Agile: Software Development Using Scrum*, Addison-Wesley, 2009, in the
chapter on testing. Cohn's original drawing has three layers, unit tests at the
base, service tests in the middle, and user interface tests at the top, with
the instruction to write lots of small fast unit tests, some coarser service
tests, and very few slow, high level UI tests
([Martin Fowler, The Practical Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html),
verified 2026-08-02, which restates and cites Cohn's shape directly).

Cohn did not invent the underlying idea from nothing. The pyramid formalizes an
older, less named instinct in test automation circles that end to end UI tests
are the most expensive and least reliable layer and should be the smallest
slice of a suite. What Cohn contributed was the visual shape and the
vocabulary, unit, service, UI, which gave teams a shared word for a trade off
they had been making informally for years. Martin Fowler's 2018 article
The Practical Test Pyramid is the most cited modern restatement and is
itself the article most engineers actually mean when they say the test
pyramid today, because it translates Cohn's three layers into concrete
technology choices and adds the failure mode the pyramid is usually invoked to
prevent, the inverted pyramid known as the ice cream cone. Fowler links that
term to Alister Scott's 2012 post Testing Pyramids and Ice Cream Cones
([Fowler, Practical Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html),
verified 2026-08-02, quoting "Watch out that you don't end up with a test
ice-cream cone that will be a nightmare to maintain and takes way too long to
run" with a link to Scott's page). A direct live fetch of Scott's own page
returned a certificate error at verification time, so that attribution is
reported here at one remove, through Fowler's citation of it, rather than
independently confirmed against the primary source.

Two names in wide industrial use are not synonyms for the same shape and
should not be treated as such. Google, through engineer Simon Stewart,
described a comparable structure under the label small, medium, large tests,
which maps loosely onto unit, integration, and end to end but is organized by
execution environment and resource isolation rather than purely by scope
([cited inside Fowler's article](https://martinfowler.com/articles/practical-test-pyramid.html),
verified 2026-08-02, referencing testing.googleblog.com slash 2010 slash 12 slash test-sizes.html).
The book *Software Engineering at Google* restates this
as an explicit target ratio, roughly 80 percent small unit tests, 15 percent
medium integration tests, and 5 percent large end to end tests, and presents
it as a pyramid shape (Titus Winters, Tom Manshreck, Hyrum Wright, editors,
*Software Engineering at Google*, O'Reilly, 2020, chapter 11,
[abseil.io resources swe-book ch11](https://abseil.io/resources/swe-book/html/ch11.html),
verified 2026-08-02, "80% of our tests being narrow scoped unit tests... 15%
medium scoped integration tests... and 5% end-to-end tests").

## 2. Problem and context

A team writes automated tests without a stated distribution, and the suite
drifts toward whatever is easiest to write in the moment rather than what is
cheapest to run and maintain over the life of the codebase. The most common
drift is toward end to end tests, because they are the easiest to justify to a
non technical stakeholder, they exercise the whole system the way a real user
would, and a single scripted browser session feels like it is testing
everything at once. The drift is invisible while the suite is small. It
becomes visible only after the suite has grown to hundreds of scenarios,
because at that point the whole build takes fifteen minutes to an hour, a
handful of tests fail on every run for reasons unrelated to the change under
review, and nobody can say with confidence whether a red build means a real
regression or an environment hiccup.

The context in which the pyramid becomes the right tool has three
characteristics that separate it from a pattern chosen for its own sake. The
system under test has enough internal structure, layers, modules, services,
that a test can exercise one unit of logic in isolation without paying for the
whole stack. The team runs the suite often enough, on every commit or every
pull request, that the cumulative wall clock time of the suite is itself a
cost worth optimizing, not a one time expense paid at release. And the team
has, or is willing to build, the isolation seams, test doubles, dependency
injection points, fake implementations of external services, that let a large
share of behavior be tested without a live database, a live network call, or
a live browser. Without those seams the pyramid becomes an aspiration with no
mechanism, because every attempt to write a fast isolated test runs
immediately into a hard dependency that cannot be substituted.

The pyramid is a strategy for allocating a finite testing budget, not a claim
that any one layer of test is more correct than another. A unit test and an
end to end test can both catch the identical regression. The pyramid argues
about cost per test, not about correctness per test, and the shape it
recommends is the one that minimizes total cost, in run time, flakiness,
diagnostic effort, and maintenance burden, for a given level of coverage
confidence.

## 3. Forces

The pyramid balances the following competing pressures. Where a dimension is
judgement rather than a sourced fact, it is stated as reasoning.

- Feedback latency, strongly favoured. A unit test that runs in memory
  completes in milliseconds. A test that boots a browser and drives real DOM
  events routinely takes seconds per scenario. A suite dominated by the slow
  layer cannot run on every save, and a suite that cannot run on every save
  gives up the tightest feedback loop testing can offer.
- Realism of the check, sacrificed at the base, recovered at the top. A
  unit test proves a function behaves correctly against its own contract. It
  proves nothing about whether that function is wired correctly into the rest
  of the system, whether the database schema it assumes actually exists, or
  whether the browser renders the resulting HTML the way the test author
  imagined. Only a test that exercises the real integration points, or the
  real system, closes that gap.
- Flakiness and reliability, strongly favoured by weighting the base
  heavily. A unit test with no external dependency either passes or fails for
  a deterministic reason tied to the code under test. A test that crosses a
  network boundary, a browser rendering engine, or a shared environment
  inherits every source of nondeterminism in that boundary, timing, DNS,
  animation frames, shared test data, clock skew. This is judgement drawn from
  wide practitioner consensus rather than a single measurable law, and it is
  the reason the pyramid treats the top layer as expensive per test written,
  not only expensive per test run.
- Diagnostic cost on failure, favoured at the base. When a unit test fails,
  the failure message names the exact function and the exact assertion. When
  an end to end scenario fails, the failure could originate anywhere across
  dozens of collaborating components, and root causing it is itself a
  debugging session.
- Maintenance cost as the system evolves, favoured at the base for
  behaviorally stable code, sacrificed at the base for code whose internal
  structure changes often. A unit test that asserts on internal collaborators
  rather than observable behavior breaks on every refactor even when the
  refactor preserves behavior, which is the classic overspecified test smell
  discussed in dimension 11.
- Confidence that the whole system actually works for a user, favoured at
  the top. No stack of unit tests, however exhaustive, proves that a browser
  can complete a checkout flow end to end, because that claim is inherently
  about integration, not about any single unit.
- Cost to build the isolation seams, sacrificed at the base. Writing a fast
  unit test for a piece of logic entangled with a database call, a clock, or a
  third party API requires introducing an abstraction, a fake, a clock
  injection, an interface boundary, that did not previously exist. That
  refactor is real work and is sometimes larger than the test itself.

The pyramid trades a fast, cheap, high volume base for a small, slow, high
realism top, on the judgement that the base catches the overwhelming majority
of regressions cheaply and the top exists to catch the residual class of bug
that only a real integrated run can surface.

## 4. Applicability and non-applicability

Reach for the pyramid shape when the following hold.

- The codebase has, or can be given, real seams between layers, so that
  business logic can be exercised without a live database, network, or
  browser.
- The team runs its test suite on every commit or every pull request and
  therefore cares about the cumulative wall clock cost of the suite, not only
  the cost of a single test.
- Regressions historically cluster in logic errors, off by one conditions,
  incorrect calculations, missing edge case handling, the class of bug a fast
  isolated test is well suited to catch.
- The system is a conventional layered application, a web service with a
  database, a backend with a frontend, a library with a public API, where
  scope naturally decomposes into unit, integration, and end to end.
- The team has budget and skill to build and maintain test doubles, because
  the pyramid's base depends on the ability to isolate a unit from its
  collaborators.

Do NOT apply the classic three layer pyramid, or apply it only with explicit
modification, in the following cases.

- A system built from many independently deployed microservices where the
  dominant risk is in the interactions between services, not inside any one
  service. Spotify's engineering team argued explicitly that in a
  microservices world the classic pyramid "can be actively harmful" because it
  under invests in exactly the layer, integration between services, where the
  real complexity lives, and proposed a Testing Honeycomb that inverts the
  emphasis toward integration tests instead
  ([Spotify Engineering, Testing of Microservices](https://engineering.atspotify.com/2018/01/testing-of-microservices/),
  verified 2026-08-02, "The biggest complexity in a Microservice is not within
  the service itself, but in how it interacts with others"). This is a real,
  named, documented departure from the pyramid, not a strawman, and it is the
  strongest citable counterexample to blind pyramid application.
- A system whose correctness is dominated by configuration, glue code, and
  wiring rather than algorithmic logic. A thin orchestration layer with
  little internal branching gains little from a large unit test base, because
  there is little logic to isolate, and the real risk lives entirely in
  whether the pieces are wired together correctly, which only an integration
  or end to end check can verify.
- Exploratory or early stage prototype work where the design is still
  changing weekly. A heavy unit test base locks in the current internal
  structure. If that structure is expected to be discarded within days, the
  tests are sunk cost written against a shape that will not survive.
- UI heavy applications where the majority of defects are visual regressions,
  layout breaks, or rendering differences rather than logic errors. Snapshot
  and visual regression tooling addresses this risk more directly than a large
  unit base, because a unit test of a rendering function cannot catch a
  regression that only appears as a shifted pixel.
- A single function or algorithm library with no external dependencies at
  all. There is nothing to pyramid. Every test is effectively a unit test
  already, and layering the terminology onto a flat, dependency free codebase
  adds vocabulary without adding a decision.
- Legacy systems with no seams and a prohibitively expensive refactor cost to
  create them. In this specific case the correct near term move is a
  characterization test suite that pins current behavior at whatever layer is
  reachable, often the top of the pyramid because that is the only layer that
  does not require restructuring the code first, with an explicit plan to
  migrate coverage downward over time. Treating the pyramid as an immediate
  requirement here produces paralysis rather than progress.

## 5. Structure

The pyramid is not a design pattern of collaborating objects, it is a shape
imposed on a test suite as a whole. The participants are the three
conventional layers and the properties that distinguish them.

- Unit layer, the base. Tests a single unit, a function, a method, a small
  class, in isolation from its real collaborators. Collaborators that would
  cross a process, network, filesystem, or clock boundary are replaced by test
  doubles, most often a fake or a stub, per the fake and stub entries in this
  family. Runs entirely in process, in memory, with no I/O. Owns the largest
  share of the suite, by count.
- Integration or service layer, the middle. Tests the correct collaboration
  between two or more real components, most commonly a component and its
  actual, non substituted dependency, a real database, a real message queue, a
  real HTTP call to an internal service, or the correct contract between a
  service and a consumer. Runs slower than a unit test because it crosses at
  least one real boundary, but does not require the full deployed system.
  Owns a moderate share of the suite.
- End to end or UI layer, the apex. Tests the deployed or near deployed
  system as a real user or a real external client would experience it, driving
  a real browser, a real API surface, or a real client application against a
  running instance of the whole stack. Owns the smallest share of the suite,
  by deliberate design.
- The suite as observed shape. The pyramid is a property of the suite in
  aggregate, counted by number of tests or, in a more sophisticated
  accounting, by total execution time contributed by each layer. No individual
  test is a pyramid on its own. The shape is a summary statistic a team can compute and
  track over time.
- The test double boundary, implicit in the structure but load bearing.
  The base layer's speed and determinism depend entirely on the availability
  of fakes or stubs at every real collaborator crossing. Without this
  boundary, the base collapses into the middle layer by definition, because
  every unit test would actually be crossing a real boundary.

## 6. ASCII structure diagram

```
                    +-------------------------+
                    |   End to End / UI        |
                    |   tests, fewest, slowest |
                    |   real browser, real     |
                    |   deployed system         |
                    +---------------------------+
                  +-------------------------------+
                  |     Integration / Service        |
                  |     tests, moderate count,       |
                  |     real DB / queue / HTTP call  |
                  +-----------------------------------+
              +-----------------------------------------+
              |            Unit tests, most numerous,    |
              |            fastest, in memory, real      |
              |            collaborators replaced by     |
              |            fakes or stubs                |
              +---------------------------------------------+

  cost per test, flakiness risk, and diagnostic ambiguity increase upward
  count of tests and execution frequency decrease upward
```

## 7. Dynamics

The pyramid's dynamics are the flow of a build pipeline built around the
shape, and the failure diagnosis flow that the shape is designed to enable.

```
DEVELOPER SAVES A CHANGE
        |
        v
[Unit layer runs, seconds]
        | pass?
        |---- no ----> developer fixes immediately, tight local loop
        v yes
[commit / push]
        |
        v
[CI pipeline. unit layer runs again, full set, still seconds to low minutes]
        | pass?
        |---- no ----> build fails fast, feedback within minutes
        v yes
[CI pipeline. integration layer runs, minutes]
        | pass?
        |---- no ----> failure narrowed to a specific real boundary
        |               (DB schema, queue contract, HTTP contract)
        v yes
[CI pipeline. end to end layer runs, small count, longest wall time]
        | pass?
        |---- no ----> failure investigated last, smallest surface area
        |               of candidate causes because the two layers below
        |               have already been proven correct in isolation
        v yes
[deploy / merge allowed]
```

The diagnostic value of the ordering is the actual payoff of the shape.
Because the base has already passed by the time the top layer runs, a failure
at the top layer is known NOT to be a pure logic error inside any single unit,
which narrows the search to wiring, environment, timing, or an interaction the
lower layers cannot see. Inverting the pyramid inverts this narrowing. A team
that runs only end to end tests must diagnose every failure across the whole
system every time, because nothing has ruled out the simpler explanations
first.

## 8. Implementation variants

- Count based pyramid. The shape is measured by the raw number of test
  cases at each layer. Simple to reason about, simple to visualize in a test
  runner's summary output, but can mislead. A hundred trivial unit tests and
  five expensive integration tests satisfy a count based pyramid while still
  contributing more wall clock time from the five than the hundred, if each
  integration test is orders of magnitude slower.
- Time weighted pyramid. The shape is measured by cumulative execution
  time contributed by each layer rather than by count. This is the more
  operationally honest variant, because the actual pain point the pyramid
  exists to prevent, a slow feedback loop, is a time problem, not a count
  problem. Requires the CI system to report per layer timing, which most
  modern CI tooling exposes but which requires deliberate tagging of tests by
  layer to compute.
- Trophy shape, contract heavy variant. Popularized in the JavaScript
  testing community around Kent C. Dodds' phrase "write tests, not too many, mostly
  integration", the trophy inverts the pyramid's emphasis by shrinking the
  unit layer relative to a larger integration layer, on the argument that in a
  UI heavy stack, integration tests give the best confidence to cost ratio.
  This is engineering judgement widely cited in front end testing circles
  rather than a single authoritative source, and is included here as a
  documented named variant, not asserted as settled.
- Google small, medium, large sizing. Rather than naming layers by scope,
  Google classifies tests by resource isolation, a small test runs in a single
  process with no network and no sleeps, a medium test runs on a single
  machine and may use the network to localhost, a large test may use any
  resource at all. The pyramid emerges as a target ratio across these size
  buckets rather than as an architectural layer boundary
  (*Software Engineering at Google*, chapter 11,
  [abseil.io resources swe-book ch11](https://abseil.io/resources/swe-book/html/ch11.html),
  verified 2026-08-02).
- Honeycomb, integration heavy variant for microservices. Spotify's
  proposed alternative for a microservices architecture, weighting integration
  tests as the dominant layer and treating fully integrated, cross service end
  to end tests as something to minimize toward zero rather than merely
  minimize
  ([Spotify Engineering, Testing of Microservices](https://engineering.atspotify.com/2018/01/testing-of-microservices/),
  verified 2026-08-02).
- Contract test insertion. A variant that adds a fourth, thin layer
  between integration and end to end, a consumer driven contract test, per
  the contract-test entry in this family, that verifies a service and its
  consumer agree on an interface without either side needing the other's real
  running instance. This variant is a direct response to the diagnostic gap
  the classic three layer pyramid leaves open at service boundaries.

## 9. Known production uses

- Google, across its internal monorepo and public engineering guidance,
  targets roughly 80 percent small, unit scale tests, 15 percent medium scale
  integration tests, and 5 percent large, end to end tests, and presents this
  explicitly as a pyramid shaped distribution (*Software Engineering at
  Google*, O'Reilly, 2020, chapter 11,
  [abseil.io resources swe-book ch11](https://abseil.io/resources/swe-book/html/ch11.html),
  verified 2026-08-02).
- Spotify, in its published engineering blog on testing microservices,
  documents its own deliberate departure from the classic pyramid for
  service oriented architecture, replacing it with a Testing Honeycomb that
  weights integration tests most heavily
  ([Spotify Engineering, Testing of Microservices](https://engineering.atspotify.com/2018/01/testing-of-microservices/),
  verified 2026-08-02). This counts as a production use of the pyramid concept
  precisely because Spotify's argument is framed against the pyramid as the
  prior baseline practice they are consciously moving away from for a specific
  architectural context.
- ThoughtWorks, through Martin Fowler's widely cited article The Practical Test
  Pyramid, which restates Cohn's shape with concrete technology mappings, unit
  tests in a framework like JUnit or Jest, service tests against a real
  database or message broker, and end to end tests through a browser
  automation tool, and documents the ice cream cone failure mode as the thing
  the pyramid is invoked to prevent
  ([martinfowler.com](https://martinfowler.com/articles/practical-test-pyramid.html),
  verified 2026-08-02). Fowler's article is itself widely reused inside
  engineering onboarding documentation at other companies as the canonical
  explanation, making it a de facto production artifact of the pattern's
  transmission through the industry, independent of its own citation value.
- The Selenium project, through engineer Simon Stewart's original test
  sizes writeup that Fowler cites, describes Google's small, medium, large
  classification as the concrete mechanism Google used internally to enforce
  the pyramid shape at scale, tying the abstract shape to an actual build
  system policy rather than leaving it aspirational
  (cited within [martinfowler.com](https://martinfowler.com/articles/practical-test-pyramid.html),
  verified 2026-08-02, referencing the Google testing blog test sizes post
  from December 2010).

## 10. Consequences

Positive.

- Fast feedback on the overwhelming majority of changes, because the base
  layer, which is the largest by count, is also the fastest to run.
- Failures are cheaper to diagnose on average, because a base layer failure
  names a specific unit and a specific assertion rather than an ambiguous
  system wide symptom.
- The suite scales sublinearly in wall clock time relative to feature count,
  because new logic mostly adds cheap unit tests rather than expensive end to
  end scenarios.
- Flakiness is concentrated in a small, known, budgeted slice of the suite,
  the top layer, rather than spread across the whole suite, which makes
  flakiness a tractable, monitorable problem instead of a pervasive one.
- The shape gives teams a shared vocabulary and a rough target when deciding
  where a new test belongs, which reduces bikeshedding over individual test
  placement decisions.

Negative.

- The base layer's speed is bought by isolating units from their real
  collaborators, and every isolation seam is a place where the test can pass
  while the real, wired up system is broken, because the fake or stub does not
  perfectly represent the real dependency's behavior.
- Building and maintaining the isolation seams, the fakes, the dependency
  injection points, is real engineering cost, and teams under time pressure
  routinely skip it, producing tests that reach into a real database anyway
  and are misclassified as unit tests while behaving like integration tests.
- A suite that satisfies the pyramid by count can still be slow and painful in
  wall clock time if the few tests at the top are disproportionately
  expensive, so count based tracking without time based tracking can hide the
  exact problem the pyramid exists to solve.
- The shape encourages teams to treat the ratio as a target to hit rather than
  a consequence of good design, which produces the anti pattern of writing
  trivial, low value unit tests purely to inflate the base count, discussed
  further in dimension 11.
- In architectures where the dominant risk is genuinely at the integration
  boundary, as Spotify argues for microservices, blind adherence to the
  classic ratio under invests exactly where the risk actually lives.

## 11. Failure modes and misuse

- Symptom, the CI suite is thousands of tests and takes forty minutes, and
  engineers routinely skip running it locally before pushing. Cause, the
  suite satisfies a count based pyramid shape but not a time weighted one, a
  small number of slow integration or end to end tests dominate the wall clock
  budget even though they are a minority by count. Fix, instrument the CI
  system to report execution time per layer, not only pass or fail per layer,
  and set an explicit time budget per layer that triggers investigation when
  exceeded, independent of the count ratio.
- Symptom, tests pass locally and in CI but production incidents keep
  occurring in the exact area the tests claim to cover. Cause, the base
  layer's fakes have drifted from the real behavior of the dependency they
  stand in for, most commonly because the real API changed and the fake was
  never updated, so tests are asserting against a fiction. Fix, pair fakes
  with a contract test, per the contract-test entry in this family, that
  periodically verifies the fake's behavior against the real dependency, so
  drift is caught mechanically rather than discovered in production.
- Symptom, a small, safe seeming refactor, renaming a private method,
  reordering unrelated fields, breaks dozens of unit tests with no change in
  observable behavior. Cause, over specified unit tests that assert on
  implementation details, internal call order, private state, rather than on
  observable outputs, so the tests are coupled to structure rather than to
  behavior. Fix, rewrite the offending tests to assert on public,
  observable behavior only, following the arrange act assert or given when
  then shape from this family, and treat a test that breaks on every refactor
  as a design smell in the test, not evidence the refactor was risky.
- Symptom, the team reports high unit test coverage percentage, but
  regressions still slip through routinely. Cause, coverage percentage
  measures lines executed, not assertions made, and a large share of the base
  layer consists of tests that call a function and assert nothing meaningful,
  written purely to satisfy a coverage gate. Fix, replace or supplement
  line coverage as a quality signal with mutation testing, per the
  mutation-test entry in this family, which measures whether the tests would
  actually catch an injected bug rather than merely execute the code.
- Symptom, the team has an inverted pyramid, an ice cream cone, with a
  large end to end layer, a thin middle layer, and almost no unit layer, and
  every pull request waits hours for CI. Cause, historically the team
  found end to end tests easier to write than unit tests, because the system
  lacks the internal seams needed to isolate a unit, so testing effort
  defaulted to the layer that requires no architectural investment. Fix,
  this is the classic failure the pyramid exists to name. The fix is not to
  delete the end to end tests, which still carry unique value, but to
  deliberately invest in seams, introduce interfaces at integration points,
  inject dependencies rather than construct them internally, so new coverage
  can land at the base going forward while the existing top heavy suite is
  gradually thinned as base coverage catches up.
- Symptom, a microservices team blindly targets an 80/15/5 style ratio per
  service and still gets paged for integration failures the ratio never
  caught. Cause, as Spotify's engineering team documented, per service
  unit test strength says nothing about whether services agree with each
  other at their boundaries, and a healthy per service pyramid can coexist
  with a systemically broken set of cross service contracts
  ([Spotify Engineering, Testing of Microservices](https://engineering.atspotify.com/2018/01/testing-of-microservices/),
  verified 2026-08-02). Fix, add explicit contract tests at every service
  boundary and weight integration testing more heavily than the classic ratio
  suggests, following the honeycomb variant from dimension 8.

## 12. Trade-off matrix

Compared against the two most commonly proposed named alternatives, the
Testing Honeycomb, Spotify's integration heavy shape for microservices, and
the Testing Trophy, the front end community's integration weighted shape.

| Force | Test Pyramid | Testing Honeycomb | Testing Trophy |
|---|---|---|---|
| Feedback latency | Fastest, base dominated by in memory unit tests | Slower, dominated by real service integration tests | Moderate, dominated by integration tests over a real but scoped stack |
| Best fit architecture | Layered monolith or well seamed service with internal logic | Distributed microservices where wiring is the main risk | UI heavy front end apps where wiring across components is the main risk |
| Confidence per test written | High for logic correctness, lower for wiring correctness | High for wiring correctness across service boundaries | High for user visible behavior, moderate for deep logic edge cases |
| Investment required before benefit | High, requires seams and test doubles throughout the codebase | Moderate, requires real dependency availability in test environments | Moderate, requires realistic component rendering harnesses |
| Diagnostic cost on failure | Low at base, rises toward apex | Moderate, ambiguity concentrated at the service interaction layer | Moderate, ambiguity concentrated at component interaction layer |
| Documented origin | Cohn 2009, restated by Fowler 2018 | Spotify Engineering 2018 | Kent C. Dodds, front end community, widely cited but not a single canonical paper |

## 13. Related and incompatible patterns

- Four Phase Test and Arrange Act Assert, this family. Both describe the
  internal shape of a single test case. The pyramid describes the shape of the
  suite as a whole. A suite can be perfectly pyramid shaped while every
  individual test inside it is badly structured, and the two concerns are
  independent, though a well structured individual test is easier to place
  correctly at the right layer because its intent is clear.
- Fake and Stub, this family. The pyramid's base layer is only cheap and
  fast because real collaborators are replaced with fakes or stubs at the
  seams. Without these test doubles, the base layer collapses into the
  integration layer by definition. The pyramid depends on these patterns, it
  does not merely relate to them.
- Contract Test, this family. Directly addresses the pyramid's most cited
  weakness, that isolating units from their real collaborators can hide a
  mismatch between a fake and reality. A contract test is frequently inserted
  as a thin layer between integration and end to end specifically to recover
  the confidence the pyramid's isolation trades away.
- Mutation Test, this family. Answers a question the pyramid's shape
  alone cannot answer, whether the tests at the base are actually detecting
  bugs, or merely executing code without meaningfully asserting on it. A team
  can satisfy the pyramid's ratio and still have a weak base if the base's
  tests are low quality, and mutation testing is the tool that surfaces that
  gap.
- Characterization Test, this family. The recommended entry point for
  applying the pyramid to a legacy codebase with no existing seams, per
  dimension 4. A characterization test pins current behavior, often from
  outside, before any refactor toward a proper pyramid shape is attempted.
- Testing Honeycomb. A named, documented alternative rather than a
  variant of the same pattern, incompatible in emphasis though not in every
  mechanism, because both still use fakes, stubs, and layered test scoping.
  The incompatibility is about which layer gets the largest budget, not about
  the underlying testing techniques used within each layer.

## 14. Refactoring path in and out

Introducing the pyramid shape into a codebase that currently lacks it, most
often a codebase with a heavy or exclusive reliance on end to end tests,
proceeds in the following order.

1. Instrument the existing suite to report per layer count and per layer
   execution time, even if every test is currently classified as the same
   layer by default. This establishes the baseline the team is moving away
   from and gives a number to track rather than a vague impression.
2. Identify the highest value, most frequently changed area of the codebase,
   and introduce a single seam there, an interface for a dependency that is
   currently constructed directly inline, so that a unit test can be written
   against the logic without the dependency.
3. Write unit tests against the newly seamed logic, asserting on observable
   behavior, and retire or narrow the scope of the end to end test that
   previously covered the same logic path, without deleting end to end
   coverage of the parts that genuinely need cross system verification.
4. Repeat the seam introduction incrementally, area by area, rather than as a
   single large refactor, because a big bang restructure of a legacy codebase
   to add seams everywhere at once is itself a high risk change with
   insufficient test coverage to safely execute.
5. Once a majority of business logic has a unit level seam, revisit the
   middle layer deliberately, adding integration tests at real boundaries,
   database schema, message contracts, external API clients, that verify the
   assumptions the unit layer's fakes are making.
6. Shrink the end to end layer to the residual set of scenarios that
   genuinely require the whole system running, critical user journeys,
   cross cutting concerns like authentication that no lower layer can fully
   verify, rather than eliminating it, since dimension 10 lists real value the
   top layer alone provides.

Removing or de-emphasizing the pyramid shape, moving toward a honeycomb or
trophy shape, follows the inverse logic and is warranted precisely when
dimension 4's non applicability conditions are met, most commonly a migration
from a monolith to microservices. The path is to identify service boundaries
where a healthy per service unit suite still leaves cross service behavior
unverified, insert contract tests or integration tests at exactly those
boundaries, and consciously reduce investment in expanding the unit layer
further once its marginal value against the actual risk profile has flattened.

## 15. Testing and verification

Testing the pyramid pattern itself means verifying the suite's shape, not
testing application code, and it is largely a practice, so this dimension is
engineering judgement drawn from common CI tooling rather than a single
sourced claim.

- Tag or categorize every test by layer at the point it is written, using test
  runner categories, naming conventions, or directory structure, so that
  automated tooling can compute the actual shape rather than relying on a
  developer's memory of where a test belongs.
- Track the shape over time as a CI metric, both by count and by cumulative
  execution time per layer, and alert when the ratio drifts significantly
  toward the apex, which is the leading indicator of an ice cream cone
  forming before it becomes painful.
- Pair shape tracking with mutation testing on the base layer specifically,
  because a healthy count ratio with a weak base gives false confidence, and
  mutation score is the more direct measure of whether the base layer is
  doing real work.
- When adding a contract test layer, verify the contract test itself against
  both the provider and the consumer independently, since a contract test that
  only one side maintains can silently drift out of sync with the other
  side's real behavior, defeating its purpose.
- Periodically run the full end to end layer against a schedule independent of
  every pull request, a nightly or pre release run, to catch the class of
  regression that only surfaces under real integrated conditions, while
  keeping the per pull request gate limited to the faster base and middle
  layers.

## 16. Observability signals

- Per layer test count and per layer cumulative execution time, tracked as
  a time series in the CI dashboard, is the primary health signal for the
  shape itself. A healthy pyramid shows the base dominating both metrics, and
  a shift in either metric toward the apex over successive releases is the
  earliest warning of drift.
- Flakiness rate per layer. A healthy pyramid concentrates flaky failures
  in the small top layer. If the flakiness rate rises in the base layer, that
  signals unit tests have started leaking real dependencies, network calls,
  filesystem access, unseeded randomness, that should have been isolated by a
  fake.
- Mean time to diagnose a CI failure, broken out by which layer first
  failed. A well shaped pyramid should show diagnosis time rising
  monotonically from base to apex, because base failures name a specific unit.
  If diagnosis time is flat or high across all layers, tests at the base are
  likely not asserting on specific enough behavior.
- Coverage of production incidents by test layer, a retrospective signal,
  tracking after each incident which layer, if any, would have caught it had
  it existed, and at which layer the closest existing coverage sits. This
  turns real production failures into direct evidence for where the pyramid's
  investment is currently misallocated.
- Build queue wait time correlated with total suite wall clock time. A
  rising apex, even a small absolute count of slow tests, shows up as growing
  pull request wait times before this correlation is otherwise obvious from
  count based dashboards alone.

## 17. Security and privacy implications

The pattern itself is testing strategy and carries no direct attack surface,
but two implications are worth stating plainly rather than inventing a larger
concern than exists.

- Test doubles used to satisfy the base layer must not leak real
  credentials, tokens, or production data into fixture files. Because unit
  tests are the layer most likely to be checked into source control verbatim,
  a fake or stub built by copying a real response payload can accidentally
  embed a real secret or real personal data captured during recording, and
  this is more likely to go unnoticed at the base layer than at the top layer,
  where a live environment with its own secret management is typically
  already in use.
- The integration and end to end layers, by design, exercise real systems
  and therefore real data paths, including authentication, authorization, and
  in some cases production adjacent data stores. Test environments for
  these layers require the same access controls, data minimization, and
  credential rotation discipline as production, because a test environment
  that is treated as lower stakes than production but still holds real or
  realistic personal data is a genuine, commonly overlooked exposure surface.
  This point is analytical judgement about a common operational gap, not a
  claim tied to a specific named incident.

## Code examples

Three languages, chosen because each shows the pyramid's base and middle
layers using idioms native to that ecosystem. Python shows the classic
unittest style assertion form. Go shows the standard library testing package
with a table style unit test and an interface backed fake. TypeScript shows
the type checked interface and class form of the same fake.

Python.

```python
"""Three layers of a test pyramid for a small discount calculator."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Cart:
    subtotal_cents: int
    loyalty_years: int


def apply_discount(cart: Cart) -> int:
    if cart.loyalty_years >= 5:
        return cart.subtotal_cents - cart.subtotal_cents // 10
    if cart.loyalty_years >= 1:
        return cart.subtotal_cents - cart.subtotal_cents // 20
    return cart.subtotal_cents


class PricingGateway(Protocol):
    def confirm_price(self, cents: int) -> bool: ...


class FakePricingGateway:
    """In memory fake, no network. Used only at the unit layer."""

    def __init__(self) -> None:
        self.confirmed: list[int] = []

    def confirm_price(self, cents: int) -> bool:
        self.confirmed.append(cents)
        return cents >= 0


def test_unit_five_year_loyalty_gets_ten_percent_off() -> None:
    cart = Cart(subtotal_cents=10_000, loyalty_years=5)
    assert apply_discount(cart) == 9_000


def test_unit_new_customer_pays_full_price() -> None:
    cart = Cart(subtotal_cents=5_000, loyalty_years=0)
    assert apply_discount(cart) == 5_000


def test_integration_gateway_confirms_the_discounted_price() -> None:
    gateway: PricingGateway = FakePricingGateway()
    cart = Cart(subtotal_cents=20_000, loyalty_years=2)
    final_price = apply_discount(cart)
    assert gateway.confirm_price(final_price)
```

The first two functions are the base of the pyramid, pure logic, no I/O, no
test double even needed. The third function is the middle layer, a real
collaboration between the pricing logic and a gateway, isolated with a fake
per the fake entry in this family rather than a real network call, so it still
runs in milliseconds while proving the two pieces agree on a contract.

Go.

```go
package pricing

import "testing"

type Cart struct {
	SubtotalCents int
	LoyaltyYears  int
}

func ApplyDiscount(c Cart) int {
	switch {
	case c.LoyaltyYears >= 5:
		return c.SubtotalCents - c.SubtotalCents/10
	case c.LoyaltyYears >= 1:
		return c.SubtotalCents - c.SubtotalCents/20
	default:
		return c.SubtotalCents
	}
}

type PricingGateway interface {
	ConfirmPrice(cents int) bool
}

type FakePricingGateway struct {
	Confirmed []int
}

func (f *FakePricingGateway) ConfirmPrice(cents int) bool {
	f.Confirmed = append(f.Confirmed, cents)
	return cents >= 0
}

func TestUnitFiveYearLoyaltyGetsTenPercentOff(t *testing.T) {
	cart := Cart{SubtotalCents: 10000, LoyaltyYears: 5}
	if got := ApplyDiscount(cart); got != 9000 {
		t.Fatalf("want 9000, got %d", got)
	}
}

func TestIntegrationGatewayConfirmsDiscountedPrice(t *testing.T) {
	var gateway PricingGateway = &FakePricingGateway{}
	cart := Cart{SubtotalCents: 20000, LoyaltyYears: 2}
	if !gateway.ConfirmPrice(ApplyDiscount(cart)) {
		t.Fatal("gateway rejected a valid price")
	}
}
```

Go's own standard library testing package makes no structural distinction
between a unit test and an integration test, both are ordinary `Test`
functions, which is exactly why Google's small, medium, large convention from
dimension 8 exists, to give teams a way to classify tests the language itself
does not enforce. The `PricingGateway` interface is the seam, satisfied here
by the fake and, in a real codebase, by a second implementation calling a real
payment provider.

TypeScript.

```typescript
interface Cart {
  subtotalCents: number;
  loyaltyYears: number;
}

function applyDiscount(cart: Cart): number {
  if (cart.loyaltyYears >= 5) {
    return cart.subtotalCents - Math.floor(cart.subtotalCents / 10);
  }
  if (cart.loyaltyYears >= 1) {
    return cart.subtotalCents - Math.floor(cart.subtotalCents / 20);
  }
  return cart.subtotalCents;
}

interface PricingGateway {
  confirmPrice(cents: number): boolean;
}

class FakePricingGateway implements PricingGateway {
  confirmed: number[] = [];
  confirmPrice(cents: number): boolean {
    this.confirmed.push(cents);
    return cents >= 0;
  }
}

function testUnitFiveYearLoyaltyGetsTenPercentOff(): void {
  const cart: Cart = { subtotalCents: 10_000, loyaltyYears: 5 };
  const result = applyDiscount(cart);
  if (result !== 9_000) throw new Error(`want 9000, got ${result}`);
}

function testIntegrationGatewayConfirmsDiscountedPrice(): void {
  const gateway: PricingGateway = new FakePricingGateway();
  const cart: Cart = { subtotalCents: 20_000, loyaltyYears: 2 };
  if (!gateway.confirmPrice(applyDiscount(cart))) {
    throw new Error("gateway rejected a valid price");
  }
}

testUnitFiveYearLoyaltyGetsTenPercentOff();
testIntegrationGatewayConfirmsDiscountedPrice();
```

The TypeScript version is the shape most front end teams actually reach for
when they say integration test in the trophy sense from dimension 8, an
interface backed fake standing in for a real backend call so the middle layer
still exercises real collaboration between two pieces of application code
without needing a live server.

All three samples were checked, Python with `python3 -m py_compile` and a
direct run, Go with `go vet`, and TypeScript with `tsc --noEmit --strict`. No
Java, Rust, or Swift sample is included, because the pyramid is a suite level
organizing strategy rather than a structural pattern with a language specific
object shape, and a fourth near identical fake and gateway example in a fourth
language would repeat the same idea without adding a distinct idiom.

## 18. References

1. Mike Cohn, *Succeeding with Agile. Software Development Using Scrum*,
   Addison-Wesley, 2009, testing chapter, cited via Martin Fowler's
   restatement below. The book itself was not independently re-verified page
   by page for this entry, the shape and instruction are quoted as restated
   and directly attributed by Fowler.
2. Martin Fowler, "The Practical Test Pyramid,"
   [martinfowler.com/articles/practical-test-pyramid.html](https://martinfowler.com/articles/practical-test-pyramid.html),
   verified 2026-08-02.
3. Google Testing Blog, "Just Say No to More End-to-End Tests,"
   [testing.googleblog.com/2015/04/just-say-no-to-more-end-to-end-tests.html](https://testing.googleblog.com/2015/04/just-say-no-to-more-end-to-end-tests.html),
   verified 2026-08-02.
4. Titus Winters, Tom Manshreck, Hyrum Wright, editors, *Software Engineering
   at Google*, O'Reilly, 2020, chapter 11, "Testing Overview,"
   [abseil.io/resources/swe-book/html/ch11.html](https://abseil.io/resources/swe-book/html/ch11.html),
   verified 2026-08-02.
5. Spotify Engineering, "Testing of Microservices,"
   [engineering.atspotify.com/2018/01/testing-of-microservices/](https://engineering.atspotify.com/2018/01/testing-of-microservices/),
   verified 2026-08-02.
6. Alister Scott, "Testing Pyramids and Ice-Cream Cones," 2012, cited via
   Martin Fowler's article above. A direct live fetch of the primary source
   returned a certificate error at verification time and is therefore
   reported here at one remove rather than independently confirmed.
7. Simon Stewart, Google test sizes writeup, cited within Martin Fowler's
   article above, referencing the Google testing blog post on test sizes
   from December 2010. Not independently re-verified beyond Fowler's
   citation of it.
