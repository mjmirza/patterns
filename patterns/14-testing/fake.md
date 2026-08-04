---
name: Fake
slug: fake
family: 14-testing
category: Test Double
aliases: [Fake Object, In-Memory Implementation]
first_described: "Meszaros 2007, popularized by Fowler 2007"
maturity: canonical
related: [stub, dummy, mock-object, spy, dependency-injection, test-data-builder, adapter, repository]
incompatible_with: []
verified: 2026-08-02
---

# Fake

## 1. Name, aliases, and lineage

The canonical name in this catalog is Fake, and it names the fourth of five
kinds of test double in Gerard Meszaros's taxonomy from *xUnit Test Patterns.
Refactoring Test Code*, Addison-Wesley, 2007, sitting alongside Dummy, Stub,
Spy, and Mock Object. Martin Fowler summarised the taxonomy for a broad
audience in an article published 2 January 2007 that remains the most cited
short definition in the field. Fowler quotes Meszaros as writing that fakes
"actually have working implementations, but usually take some shortcut which
makes them not suitable for production" (Martin Fowler, "Mocks Aren't Stubs",
published 2 January 2007, verified 2026-08-02). That one sentence carries the
whole lineage of the name, a Fake is not an inert placeholder and not a
programmed-answer machine, it is a genuine, working, alternative
implementation of an interface, chosen because the real implementation is too
slow, too heavy, too networked, or too stateful to run inside a test.

The word is sometimes used loosely in conversation to mean any test double at
all, which is exactly the confusion Fowler's article set out to end by giving
each of the five words a distinct technical meaning. In this catalog Fake
keeps its narrow sense throughout, an object that really does the work,
through a shortcut. The most common concrete example, and the one this entry
returns to repeatedly, is an in-memory implementation of a repository or a
data-access interface, standing in for a networked database. The pattern
predates Meszaros's naming of it by a long way, an in-memory substitute
database used purely for test speed and isolation is a natural idea the
moment automated tests exist, and the practice is visible in the design of
SQLite's own `:memory:` special filename, whose purpose the SQLite
documentation frames around exactly this kind of throwaway, isolated
instance (SQLite documentation, "In-Memory Databases", verified 2026-08-02).
Meszaros's contribution was not inventing the practice, it was giving the
practice a name distinct from Stub and Mock so that engineers arguing about
test doubles could mean the same thing by the words they used.

## 2. Problem and context

A piece of code depends on a collaborator that is real, correct, and slow, or
real, correct, and hard to set up. A repository that talks to Postgres. A
payment gateway that talks to a card network over HTTPS. A file store backed
by S3. The code under test needs that collaborator to behave like the real
thing, closely enough that a passing test is evidence the code is correct,
but the test suite cannot afford to pay the cost of the real thing on every
run. Cost here is several things at once, wall-clock time, since a Postgres
round trip is milliseconds and a thousand of them add up, environmental
setup, since a CI runner needs a running database server, credentials, and
network access before a single assertion runs, and flakiness, since a real
network call can fail for reasons that have nothing to do with the code being
tested, a timeout, a transient DNS failure, a rate limit.

The context in which this problem is sharpest is exactly the layer boundary
where an application talks to infrastructure it does not control. A
`UserRepository` interface with a Postgres-backed implementation and no other
implementation forces every test that exercises a service using that
repository to either run against a real database or to double the interface
somehow. A Stub or a Mock can answer one or two specific calls, but as soon
as the test needs the collaborator to behave statefully across several calls,
add a row, then find it by a different key, then delete it, then confirm it
is gone, a Stub's canned single answers and a Mock's call-expectation
checking both become awkward. What the test actually wants is a second real
implementation of the same interface, one that keeps its rows in a plain
in-process map or list instead of a database file, obeys the same contract
the real implementation obeys, and disappears when the test process exits.
That second implementation is the Fake.

## 3. Forces

Fidelity to production behaviour pulls against speed and isolation, and a
Fake is a deliberate, visible compromise between them, not a free lunch.
Every Fake is a second implementation of the interface's contract, written
and maintained by hand, and every divergence between the Fake's behaviour and
the real implementation's behaviour is a place where a passing test can lie.
A Fake that permits two rows with the same primary key when the real
database would reject the second insert with a uniqueness violation gives
the test suite false confidence, and the failure only shows up in production,
where the discipline of dimension 3 says the cost of the pattern must be
named honestly rather than hidden.

Coupling is the second force. A hand-written Fake couples the test suite to
the shape of the interface it doubles, which is a good coupling, since it
forces the interface to be a genuine seam rather than a leaky abstraction
that only the real implementation can satisfy. But it also couples the test
suite to the Fake's own correctness. When the interface gains a method, the
Fake must gain an implementation of that method too, by hand, or the tests
that exercise the new method either fail to compile in a statically typed
language or silently exercise a Fake that does not actually support the new
behaviour.

Cost and effort is the third force, and it runs the opposite direction from
the previous two. Writing a correct in-memory Fake of a stateful interface,
one that honours ordering, uniqueness, foreign-key-like relationships, and
concurrent access where the real system enforces those things, is real
engineering work, sometimes as much work as a thin wrapper around the real
thing. A team under time pressure is tempted to write a Fake that is
convenient rather than faithful, and that temptation is precisely dimension
11's most common failure mode. Operability and team topology matter too, a
Fake that lives inside the same repository as the interface it doubles, kept
in the same pull request that changes the interface, stays honest, whereas a
Fake maintained by a different team, or vendored from a library the
interface's owner does not control, drifts.

## 4. Applicability and non-applicability

Reach for a Fake when the collaborator being doubled is stateful across
multiple calls within a single test, when the real collaborator is slow,
networked, or hard to provision in CI, when more than a handful of tests
need the same double so the cost of writing it once is amortised, and when
the interface being doubled is narrow and stable enough that a hand-written
second implementation is not chasing a moving target. The canonical case is
an in-memory repository standing in for a database-backed one behind a
narrow port, or an in-memory message queue standing in for a real broker
behind a narrow publish and consume interface.

Do not reach for a Fake in these situations.

- When a single canned answer or a single recorded call is all the test
  needs, reach for a Stub or a Spy instead, both of which are cheaper to
  write and read (Martin Fowler, "Mocks Aren't Stubs", verified 2026-08-02).
- When the exact interaction between the code under test and the
  collaborator, which methods are called, in what order, with what
  arguments, is itself the thing being verified. that is the Mock Object's
  job, and a Fake's working implementation obscures interaction
  verification rather than expressing it.
- When the collaborator's contract is complex enough, transactional
  semantics, exact concurrency behaviour, exact error codes, that a
  hand-written Fake cannot practically stay faithful to it. In that
  situation the better tool is often a real instance run in an isolated
  throwaway container, which is the express reason Testcontainers exists,
  described as providing "throwaway, lightweight instances of databases,
  message brokers, web browsers, or just about anything that can run in a
  Docker container" so a team can "test your data access layer code for
  complete compatibility, without requiring a complex setup on developer
  machines" (Testcontainers, project homepage, verified 2026-08-02).
- When only one or two tests will ever exercise the collaborator, the fixed
  cost of writing and maintaining a second implementation is not repaid.
- When the interface is unstable and still changing shape week to week, a
  Fake built against a moving interface becomes a maintenance tax that
  exceeds the time it saves.

## 5. Structure

Three participants recur in every instance of this pattern.

Subject Under Test. The code that depends on the collaborator through an
interface, and that has no idea, and should have no way to know, whether it
is talking to the real implementation or the Fake.

Port, or Collaborator Interface. The seam, an interface, protocol, or
abstract base defining the contract both the real implementation and the
Fake must satisfy. In a repository context this is often literally named a
port, following the Ports and Adapters vocabulary, or it is simply the
interface the concrete database class implements alongside the Fake.

Fake Implementation. A second, working, in-process implementation of the
Port, backed by a plain in-memory data structure, a map, a list, a set,
rather than by the real infrastructure the production implementation
depends on. It genuinely performs the operations the interface promises, add
a row, look it up, remove it, it simply performs them against memory instead
of against a network service.

A fourth, optional participant appears whenever object construction is not
already parameterised, a Composition Root or test setup function that
decides which implementation of the Port, real or Fake, is wired into the
Subject Under Test for a given run, which is the connective tissue between
this pattern and Dependency Injection.

## 6. ASCII structure diagram

```
+----------------------+
|  Subject Under Test  |
|  (e.g. UserService)  |
+-----------+----------+
            | depends on
            v
+----------------------+
|   UserRepository      |  <-- Port / Collaborator Interface
|   (interface)         |
+-----------+-----------+
            ^
            |  both implement
    +-------+--------+
    |                 |
+---+----------+  +---+------------------+
| Postgres     |  | InMemoryUser         |
| UserRepository|  | Repository (Fake)   |
| (production) |  |  - map<id, Row>      |
+--------------+  |  - genuinely stores, |
                   |    finds, deletes   |
                   +----------------------+

  Composition Root wires the Fake in for tests,
  the Postgres implementation in for production.
```

## 7. Dynamics

```
Test setup
  fake := NewInMemoryUserRepository()
  service := NewUserService(fake)      # Fake injected via the Port

Test body, exercising real behaviour across calls
  service.Register("Ada", "ada@example.com")
      |
      v
  UserService.Register
      |
      v
  fake.Add("Ada", "ada@example.com")   # genuinely stores the row
      |
      v
  returns generated id

  service.FindUser("ada@example.com")
      |
      v
  fake.FindByEmail("ada@example.com")  # genuinely searches stored rows
      |
      v
  returns the row added above          # state persisted across calls,
                                        # unlike a Stub's single canned answer

Test teardown
  fake goes out of scope, no cleanup step, no external process to stop
```

The defining dynamic, visible in the trace above, is that the second call
depends on the effect of the first call, because the Fake genuinely holds
state between invocations. A Stub cannot express this without becoming
stateful itself, at which point it has quietly turned into a Fake by
another name, a boundary case dimension 13 returns to.

## 8. Implementation variants

In-memory collection Fake. The default shape, described throughout this
entry, state lives in a map, list, or set inside the process, and the
implementation is written by hand against the same interface the real
implementation satisfies.

Embedded real engine as a Fake. Rather than reimplementing a database's
semantics by hand, run the real database engine in an embedded, in-memory
mode. SQLite's `:memory:` connection string is the most common instance of
this. "The most common way to force an SQLite database to exist purely in
memory is to open the database using the special filename ':memory:'", after
which "no disk file is opened. Instead, a new database is created purely in
memory. The database ceases to exist as soon as the database connection is
closed" (SQLite documentation, "In-Memory Databases", verified 2026-08-02).
H2, the Java embeddable database, is used the same way in the Java
ecosystem, supporting "embedded and server modes; disk-based or in-memory
databases" (H2 Database Engine, GitHub repository README, verified
2026-08-02). This variant is worth naming separately from the hand-rolled
collection Fake because it trades hand-written fidelity risk for a
different risk, drift between the embedded engine's SQL dialect and the
production engine's SQL dialect, which is a real and commonly cited
limitation.

Language-idiomatic closures over a captured collection. In languages where
interfaces can be satisfied by closures or function values rather than
classes, a Fake often collapses to a factory function returning a struct of
closures that close over a shared, mutable, in-process collection, rather
than a named class implementing a named interface. The Go example in
dimension 9 shows the class-shaped version explicitly for portability across
languages, but idiomatic Go often prefers a function-valued Port instead.

Fake as a thin adapter over a shared library's own in-memory mode. Message
queues, caches, and search indexes frequently ship an official in-memory or
embedded mode intended for exactly this use, for example `fakeredis` in the
Python ecosystem. These are Fakes maintained by a third party rather than
by the team, which shifts the maintenance-cost force in dimension 3 but
does not remove the fidelity-drift risk.

Faked clock, faked filesystem. Not every Fake models a database. A fake
clock that implements a `Now` method against a value the test can set and
advance, or a fake filesystem backed by an in-memory tree of files, are the
same pattern applied to a non-persistence collaborator, and they are common
enough in production codebases to be worth naming as a distinct, frequent
variant rather than an edge case.

## 9. Known production uses

- SQLite's `:memory:` special filename, used throughout the SQLite
  ecosystem and by countless applications embedding SQLite specifically to
  give each test process an isolated, disposable database, is documented by
  SQLite itself as creating a database that "ceases to exist as soon as the
  database connection is closed" and where "every :memory: database is
  distinct from every other" (SQLite documentation, "In-Memory Databases",
  verified 2026-08-02).
- H2 Database Engine, widely used in the Java and Spring ecosystems as an
  in-memory stand-in for a production relational database during tests,
  supporting "embedded and server modes; disk-based or in-memory databases"
  (H2 Database Engine, GitHub repository README, verified 2026-08-02).
- `fakeredis`, a Python library that implements Redis's own command
  protocol against an in-process data structure rather than a real Redis
  server, letting code written against a Redis client be exercised in tests
  with no Redis server running, is a maintained, named, widely depended-on
  package on the Python Package Index whose stated purpose is exactly the
  Fake pattern applied to a cache and pub/sub server.
- Firebase's Local Emulator Suite, which runs local, in-process versions of
  Firestore, Realtime Database, Authentication, and Cloud Functions so that
  application code written against the real Firebase client SDKs can be
  exercised in automated tests and local development without touching
  Google's production infrastructure, is Google's own named, shipped
  instance of the Fake pattern applied at the platform level, distinct from
  the collection-in-a-map shape but serving the identical purpose, a
  working, shortcut implementation unsuitable for production traffic.
- Testcontainers, while not itself a Fake, exists specifically as the named
  alternative teams reach for once a hand-written Fake's fidelity becomes
  the limiting factor, described as letting a team "define your test
  dependencies as code, then simply run your tests and containers will be
  created and then deleted" against real database and broker images
  (Testcontainers, project homepage, verified 2026-08-02). its existence and
  popularity is itself evidence of how common the Fake pattern's fidelity
  trade-off is felt to be in production engineering organisations.

## 10. Consequences

Positive.

- Tests that exercise stateful, multi-call interactions with a collaborator
  run in the same process, with no network, no external service to start,
  and typically an order of magnitude or more faster than the equivalent
  test against a real database or a containerised one.
- Because the Fake genuinely implements the contract rather than returning
  canned answers, tests read naturally, add a thing, then look it up,
  rather than reading like a list of pre-arranged responses, which keeps
  the test close to how a reader would describe the behaviour in plain
  language.
- A single well-written Fake is reused across every test that needs the
  collaborator, amortising the cost of writing it once across the whole
  suite, and the Fake itself becomes a place where the team's shared
  understanding of the interface's contract lives in executable form.
- CI pipelines that use only Fakes for their unit-test tier can run without
  provisioning any external services, keeping the unit tier's infrastructure
  footprint at zero.

Negative.

- A Fake is a second implementation that must be kept in sync with the real
  implementation's contract by hand, it does not update itself when the
  real implementation's behaviour changes, and there is no compiler or type
  system that enforces behavioural, as opposed to signature-level,
  equivalence between the two.
- A passing test against a Fake is evidence about the code under test's
  logic, not evidence that the code under test will behave correctly
  against the real collaborator. teams that treat a Fake-backed test suite
  as sufficient proof of production readiness are trusting an assumption
  that nothing in the pattern itself guarantees.
- Writing a faithful Fake for a collaborator with rich constraints,
  uniqueness, referential integrity, transactional isolation, ordering
  guarantees under concurrency, is real engineering effort, and an
  under-resourced Fake tends to silently drop the constraints that are
  hardest to implement, which are frequently the exact constraints most
  worth testing against.
- A Fake can leak internal shortcuts into test expectations. tests
  unconsciously start asserting against the Fake's own incidental
  behaviour, for example iteration order of a map, rather than against
  behaviour the real collaborator actually guarantees, producing tests that
  pass against the Fake and fail against production for reasons the test
  author never intended to depend on.

## 11. Failure modes and misuse

Symptom. A test suite is entirely green, the feature is deployed, and it
fails in production on the very first real database call, with an error the
test suite never surfaced.
Cause. The Fake silently omits a constraint the real database enforces,
most commonly a uniqueness constraint, a foreign-key relationship, or a
NOT NULL column, so code paths that depend on the real database rejecting
an invalid write are never exercised, because the Fake happily accepts the
write the test author expected to be rejected.
Fix. Encode the same invariants the real schema enforces directly into the
Fake's implementation, verified once against the real schema, and add a
contract test, described in dimension 15, that runs the identical test
suite against both the Fake and a real or containerised instance of the
collaborator to catch behavioural drift automatically.

Symptom. Two tests that run in the same test binary but in different
methods start interfering with each other, one test's data shows up in
another test's assertions, or a test that passes alone fails when run as
part of the full suite.
Cause. The Fake was written as a package-level or class-level singleton,
sharing one in-memory collection across every test in the process instead
of constructing a fresh, isolated instance per test.
Fix. Construct a new Fake instance in each test's setup step, exactly as
shown in dimension 7's trace, so state never crosses test boundaries, this
is the same isolation discipline the real infrastructure would need to
provide through a fresh database schema or a fresh container per test, and
the Fake must not be sloppier about isolation than the thing it replaces.

Symptom. A code review flags a bug that turns out to already be described,
by name, in an old comment inside the Fake, and nobody had noticed the
Fake's behaviour diverged from the real implementation months earlier.
Cause. The Fake is owned informally, by whoever happened to write it first,
rather than being treated as production code with the same review and
ownership discipline as the interface it implements, so drift accumulates
silently as the real implementation evolves and the Fake does not.
Fix. Put the Fake in the same package or module as the Port it implements,
require any pull request that changes the Port's contract to touch the Fake
in the same diff, and name a specific owner or reviewer for that file the
same way any other production code has one.

Symptom. A new engineer, asked to write a unit test for code that depends
on a repository, reaches for a heavyweight mocking library and writes forty
lines of call-expectation setup for what should be a three-line test, then
the test breaks every time an unrelated method call order changes.
Cause. The team has no established Fake for the interface, so every
engineer independently reaches for the interaction-verification tool, Mock,
that dimension 4 explicitly says is the wrong tool when what the test
actually needs is a working, stateful stand-in.
Fix. Invest in one well-maintained Fake per frequently-doubled interface,
in the same repository, discoverable the same way the real implementation
is discoverable, so the easy path for the next engineer is also the
correct one.

## 12. Trade-off matrix

| Force | Fake | Stub | Mock Object | Real instance via Testcontainers |
|---|---|---|---|---|
| Speed per test run | Fast, in-process | Fastest, no real logic at all | Fast, no real logic | Slow, container startup cost per run or per suite |
| Fidelity to production behaviour | Medium, only as faithful as the hand-written implementation | Low, single canned answer only | Low, verifies calls, not behaviour | Highest, the real engine |
| Supports multi-call stateful interaction | Yes, naturally | Awkward, needs to become stateful, which turns it into a Fake | No, verifies interaction shape, not resulting state | Yes, naturally |
| Setup and maintenance cost | Medium, one hand-written implementation to keep in sync | Low, one canned answer per test | Low per test, but brittle across refactors | Medium to high, Docker required, container images to manage |
| CI infrastructure requirement | None, pure in-process | None | None | Docker daemon required |
| Best suited to | Repository-shaped, stateful collaborators reused across many tests | A single external call whose only relevant output is one value | Verifying that a specific interaction happened, in a specific order | Verifying compatibility with the real engine's exact semantics |

Sources for the Stub and Mock definitions used in this comparison are the
same as dimension 1 (Martin Fowler, "Mocks Aren't Stubs", verified
2026-08-02). The Testcontainers row is sourced to the project's own
homepage description, verified 2026-08-02, as cited in dimension 4.

## 13. Related and incompatible patterns

Stub. The closest sibling and the one most often confused with Fake in
casual conversation. A Stub answers one call with one canned value and has
no memory of prior calls, the moment a Stub is asked to remember state
between calls to satisfy a test, it has become a Fake in practice even if
the code still calls itself a Stub, which is exactly the boundary case
described at the end of dimension 7. The distinction matters because it
changes what the test double is claiming to prove, a Stub claims nothing
about multi-call behaviour, a Fake does.

Dummy. A Dummy is passed around purely to satisfy a parameter list and is
never actually invoked (Martin Fowler, "Mocks Aren't Stubs", verified
2026-08-02). A Fake is the opposite extreme on the same spectrum, it is
invoked repeatedly and its behaviour genuinely matters to the outcome of
the test.

Mock Object. A Mock is pre-programmed with expectations about which calls
it will receive, and a test using a Mock asserts on the interaction itself
(Martin Fowler, "Mocks Aren't Stubs", verified 2026-08-02). A test using a
Fake asserts on the resulting state instead, by calling other query
methods on the same Fake after the action under test. The two approaches
to verification, interaction-based and state-based, are frequently
discussed as a named methodological split in the testing literature, and a
Fake is the natural collaborator for the state-based side of that split.

Spy. A Spy is a Stub that also records how it was called (Martin Fowler,
"Mocks Aren't Stubs", verified 2026-08-02). A Fake can incidentally record
call counts too, but recording calls is not its defining purpose the way
it is a Spy's, a Fake's defining purpose is genuinely performing the
operation.

Dependency Injection. A Fake is only useful if the Subject Under Test
receives its collaborator from outside itself rather than constructing the
real implementation internally. Dependency Injection, whether via
constructor parameters, a service locator, or a framework's container, is
the structural precondition that makes swapping in a Fake possible at all,
and is why dimension 5 lists a Composition Root as a participant.

Repository pattern. In practice the single most common host for a Fake in
application codebases is a Repository interface, precisely because a
Repository's contract, add, find, delete, is narrow, stable, and stateful
in exactly the way dimension 4 describes as the ideal case for this
pattern.

Adapter. A Fake and an Adapter both implement a target interface, but for
opposite reasons. an Adapter exists to make an incompatible real
implementation fit an interface it was not written against, a Fake exists
to provide an intentionally shortcut implementation of an interface it was
written against from the start. They are not incompatible and often appear
side by side, the production Adapter and the test Fake, both implementing
the same Port.

No pattern in this catalog is flagged incompatible with Fake at the time of
writing.

## 14. Refactoring path in and out

Introducing a Fake into code that has none. Begin by confirming a real seam
exists, an interface or protocol the Subject Under Test depends on rather
than a concrete class it constructs directly. If no such seam exists, the
prerequisite refactor is Extract Interface, pulling the methods the Subject
Under Test actually calls into a narrow interface the concrete, production
implementation then satisfies. Once the seam exists, write the Fake as a
second implementation of that same interface, starting from the narrowest
set of methods the current test suite needs rather than attempting to model
the full production contract on day one. Wire the Fake into the Subject
Under Test's constructor or factory in the test's setup step, replacing
whatever Mock- or Stub-based setup previously stood in for the
collaborator, and migrate tests one at a time, confirming each migrated
test still expresses the same behavioural intent it did before, now as an
assertion against the Fake's resulting state rather than against a Mock's
recorded call log.

Removing a Fake that has stopped earning its place. A Fake is a candidate
for removal when the interface it doubles has shrunk to one or two trivial
methods where a Stub would now be simpler and equally faithful, or when the
team has adopted a containerised real instance, via Testcontainers or an
equivalent, for the same tests and no longer needs the speed the Fake
bought, or when the Fake's fidelity has drifted so far from the real
implementation that keeping it is actively harmful, per dimension 11's
first failure mode. Removal proceeds by first adding a small number of
contract tests, described in dimension 15, that run against both the Fake
and the real implementation to establish exactly where the divergence lies,
fixing or accepting that divergence deliberately, and then either narrowing
the Fake down to a Stub or replacing its call sites with the chosen real or
containerised alternative one test file at a time, never in one large
change that makes a regression hard to attribute.

## 15. Testing and verification

Code that depends on an interface rather than a concrete implementation is,
by construction, easy to test with a Fake substituted in, which is the
entire practical payoff of this pattern, and the technique needs no special
test-double library, only the Port from dimension 5 and a plain in-memory
implementation of it.

What becomes harder is verifying that the Fake itself is correct, meaning
faithful to the real implementation's contract, since nothing in a static
type system checks behavioural equivalence between two implementations of
the same interface, only signature equivalence. The standard technique for
closing that gap is a contract test, sometimes called a compliance test
suite, a single, shared set of test cases written entirely against the
Port's interface, with no knowledge of which implementation backs it,
parameterised or run twice, once instantiated with the real implementation
and once instantiated with the Fake. When both runs pass, the Fake's
observable behaviour matches the real implementation's observable
behaviour for every case the contract test covers, and any future drift,
someone adds a uniqueness constraint to the real database but forgets the
Fake, is caught the moment the contract test suite runs against both. This
technique composes directly with the failure mode named first in dimension
11 and is the concrete fix that entry recommends.

A second useful technique is to run the contract test suite against the
Fake on every commit, cheaply, and against the real or containerised
implementation on a slower schedule, nightly or pre-release, trading some
detection latency for keeping the fast feedback loop fast while still
catching drift before it reaches production.

## 16. Observability signals

A Fake itself typically runs inside a test process and is torn down at the
end of that process, so it is not something monitored in a running
production system the way a real service is, and any entry claiming
otherwise would be describing a different pattern. The observability
concerns that do apply are about the health of the pattern's use, not
about a running instance.

Watch the test suite's own signal quality. a rising rate of tests that pass
locally against the Fake but fail in a staging or integration environment
against the real collaborator is the leading indicator that the Fake has
drifted from the real implementation's contract, described in dimension
11. Track the contract test suite from dimension 15 as its own named CI
job, and treat any failure in the real-implementation run of that suite,
when the Fake-backed run passed, as a signal requiring immediate attention
rather than a flaky test to retry, since by construction it means the two
implementations disagree.

A healthy state looks like a contract test suite that passes identically
against both implementations on every commit, and a unit test suite that
runs to completion in seconds using only Fakes, with no external network
calls observed in the test process, which most CI systems can verify
directly by denying outbound network access during the unit-test job and
watching for the job to fail if it is attempted.

## 17. Security and privacy implications

A Fake's own in-memory state normally holds only synthetic test data,
constructed inside the test itself, and disappears when the test process
exits, so a correctly used Fake reduces the surface area for a real
security or privacy concern that a real database connection in a test
environment would otherwise create, credentials for a real system sitting
in a CI configuration, or real customer data being copied into a lower
environment for testing convenience. Because a Fake needs neither a
connection string nor a credential, its use is frequently a net privacy
improvement in a test suite compared with pointing tests at a shared real
database.

The implication runs the other way when a Fake is seeded with data copied
from a real system rather than constructed synthetically. a Fake that has
been populated by dumping a snapshot of real production rows into its
in-memory collection carries the same privacy and data-handling
obligations the real data carried, and the fact that it lives in memory
inside a test process rather than in a persistent database does not remove
those obligations, since the data is still present, still readable by
anyone with access to the test logs or a debugger attached to the test
process, and still subject to whatever data-protection rules governed it
before it was copied. Where this entry has an opinion rather than a
sourced fact, it is this, seed Fakes only with synthetic data generated
for the test, never with a copy of real production records, precisely
because the speed and convenience that make a Fake attractive also make it
an easy, low-visibility place for real data to end up somewhere nobody
intended it to persist.

## Code examples

Four languages, chosen because each shows a genuinely different idiomatic
shape for the same pattern rather than a mechanical translation. Python
shows the shape most readers reach for first, a plain class holding a dict.
TypeScript shows the same shape with an explicit interface the Fake and a
hypothetical production class both satisfy, closest to the Java or C#
class-based form. Go shows the pattern against a Go interface, satisfied
implicitly, no `implements` keyword required, which changes how the
Composition Root from dimension 5 looks in practice. Swift shows a value
type, a `struct` rather than a `class`, conforming to a `protocol`, with
mutation expressed through `mutating` methods and failure expressed through
Swift's typed `throws` rather than an exception, both idiomatic choices a
Swift codebase would actually make. Java, Rust, and Kotlin are omitted
because each would be materially the same class-and-interface shape already
shown in TypeScript and Go, once translated into that language's own
generics and error-handling syntax.

### Python

```python
class InMemoryUserRepository:
    def __init__(self):
        self._rows = {}
        self._next_id = 1

    def add(self, name, email):
        user_id = self._next_id
        self._rows[user_id] = {"id": user_id, "name": name, "email": email}
        self._next_id += 1
        return user_id

    def find_by_email(self, email):
        for row in self._rows.values():
            if row["email"] == email:
                return row
        return None

    def delete(self, user_id):
        if user_id not in self._rows:
            raise KeyError(user_id)
        del self._rows[user_id]


def test_find_by_email_returns_none_when_absent():
    repo = InMemoryUserRepository()
    assert repo.find_by_email("nobody@example.com") is None


def test_add_then_find_by_email_round_trips():
    repo = InMemoryUserRepository()
    repo.add("Ada", "ada@example.com")
    found = repo.find_by_email("ada@example.com")
    assert found is not None
    assert found["name"] == "Ada"


def test_delete_missing_raises():
    repo = InMemoryUserRepository()
    try:
        repo.delete(999)
        assert False, "expected KeyError"
    except KeyError:
        pass
```

The three functions above are ordinary test functions, runnable under
`pytest` with no extra fixture required, each constructing its own fresh
`InMemoryUserRepository`, which is the isolation discipline named in
dimension 11's second failure mode.

### TypeScript

```typescript
interface UserRow {
  id: number;
  name: string;
  email: string;
}

interface UserRepository {
  add(name: string, email: string): number;
  findByEmail(email: string): UserRow | undefined;
  delete(id: number): void;
}

class InMemoryUserRepository implements UserRepository {
  private rows = new Map<number, UserRow>();
  private nextId = 1;

  add(name: string, email: string): number {
    const id = this.nextId++;
    this.rows.set(id, { id, name, email });
    return id;
  }

  findByEmail(email: string): UserRow | undefined {
    for (const row of this.rows.values()) {
      if (row.email === email) return row;
    }
    return undefined;
  }

  delete(id: number): void {
    if (!this.rows.has(id)) throw new Error(`no such id ${id}`);
    this.rows.delete(id);
  }
}

const repo: UserRepository = new InMemoryUserRepository();
repo.add("Ada", "ada@example.com");
const found = repo.findByEmail("ada@example.com");
if (found === undefined || found.name !== "Ada") {
  throw new Error("round trip failed");
}
```

The explicit `UserRepository` interface is what a production
`PostgresUserRepository` class would implement alongside this Fake, and is
the Port from dimension 5 written in TypeScript's own vocabulary.

### Go

```go
package repository

import "fmt"

type UserRepository interface {
	Add(name, email string) int
	FindByEmail(email string) (map[string]string, bool)
	Delete(id int) error
}

type InMemoryUserRepository struct {
	rows   map[int]map[string]string
	nextID int
}

func NewInMemoryUserRepository() *InMemoryUserRepository {
	return &InMemoryUserRepository{rows: make(map[int]map[string]string), nextID: 1}
}

func (r *InMemoryUserRepository) Add(name, email string) int {
	id := r.nextID
	r.rows[id] = map[string]string{"name": name, "email": email}
	r.nextID++
	return id
}

func (r *InMemoryUserRepository) FindByEmail(email string) (map[string]string, bool) {
	for _, row := range r.rows {
		if row["email"] == email {
			return row, true
		}
	}
	return nil, false
}

func (r *InMemoryUserRepository) Delete(id int) error {
	if _, ok := r.rows[id]; !ok {
		return fmt.Errorf("no such id %d", id)
	}
	delete(r.rows, id)
	return nil
}
```

`InMemoryUserRepository` satisfies `UserRepository` implicitly, the Go
compiler checks the method set matches with no `implements` declaration
anywhere, which is why a Go Composition Root is usually just an assignment,
`var repo UserRepository = NewInMemoryUserRepository()` in a test, and
`var repo UserRepository = NewPostgresUserRepository(db)` in production.

### Swift

```swift
struct UserRow {
    let id: Int
    let name: String
    let email: String
}

protocol UserRepository {
    mutating func add(name: String, email: String) -> Int
    func findByEmail(_ email: String) -> UserRow?
    mutating func delete(_ id: Int) throws
}

enum RepoError: Error { case notFound(Int) }

struct InMemoryUserRepository: UserRepository {
    private var rows: [Int: UserRow] = [:]
    private var nextId = 1

    mutating func add(name: String, email: String) -> Int {
        let id = nextId
        rows[id] = UserRow(id: id, name: name, email: email)
        nextId += 1
        return id
    }

    func findByEmail(_ email: String) -> UserRow? {
        rows.values.first { $0.email == email }
    }

    mutating func delete(_ id: Int) throws {
        guard rows[id] != nil else { throw RepoError.notFound(id) }
        rows.removeValue(forKey: id)
    }
}
```

The `mutating` keyword on `add` and `delete` is Swift's value-type
discipline made visible, `InMemoryUserRepository` is a `struct`, so any
method that changes its stored state must say so explicitly, and the
`RepoError.notFound` case gives the delete-missing-row failure mode a typed
shape a caller can switch on, rather than the generic runtime exception the
Python and TypeScript versions raise.

## 18. References

- Gerard Meszaros, *xUnit Test Patterns. Refactoring Test Code*,
  Addison-Wesley, 2007. The original taxonomy naming Dummy, Fake, Stub,
  Spy, and Mock Object as five distinct kinds of test double.
- Martin Fowler, "Mocks Aren't Stubs",
  https://martinfowler.com/articles/mocksArentStubs.html, published
  2 January 2007, verified 2026-08-02. The widely cited summary quoting
  Meszaros's definitions of Dummy, Fake, Stub, Spy, and Mock, used
  throughout dimensions 1, 4, 10, 12, and 13 of this entry.
- SQLite Documentation, "In-Memory Databases",
  https://sqlite.org/inmemorydb.html, verified 2026-08-02. Describes the
  `:memory:` special filename and its isolation and lifetime semantics,
  cited in dimensions 1, 8, and 9.
- H2 Database Engine, GitHub repository,
  https://github.com/h2database/h2database, verified 2026-08-02. Describes
  H2's embedded and in-memory modes, cited in dimensions 8 and 9.
- Testcontainers, project homepage, https://testcontainers.com/, verified
  2026-08-02. Describes providing throwaway, containerised real
  dependencies as the named alternative to a hand-written Fake when
  fidelity requirements exceed what a Fake can provide, cited in
  dimensions 4, 9, and 12.
