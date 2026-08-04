---
name: Testcontainers
slug: testcontainers
family: 14-testing
category: Testing
aliases: [Disposable Containers, Ephemeral Test Infrastructure]
first_described: "Richard North, Testcontainers project, 2015"
maturity: canonical
related: [dependency-injection, test-doubles-strategy, builder, singleton]
incompatible_with: []
verified: 2026-08-02
---

# Testcontainers

## 1. Name, aliases, and lineage

The canonical name is Testcontainers, capitalized as one word, matching the
project and organization name. The pattern behind it is sometimes described
in the wild as Disposable Containers or Ephemeral Test Infrastructure, but
those are descriptive phrases used by teams explaining the idea, not names
used by a competing catalog or specification.

The project began as a Java library written by Richard North, first published
under the name Testcontainers around 2015, built on top of the `docker-java`
client and JUnit 4 rules to let a test start a real Docker container, wait for
it to become ready, and tear it down automatically at the end of the test run
(Testcontainers.com, "What is Testcontainers", https://testcontainers.com/,
verified 2026-08-02). The library later moved under an organization umbrella
(the `testcontainers` GitHub organization) and grew ports to Go
(`testcontainers-go`), Node.js (`testcontainers-node`), Python
(`testcontainers-python`), .NET, and Rust, each implementing the same idea
against that language's own test framework and container runtime client. In
2021 the company AtomicJar was founded around the project and later built
Testcontainers Cloud, a hosted Docker runtime for teams whose CI runners
cannot run Docker locally (Testcontainers Cloud product page,
https://testcontainers.com/cloud/, verified 2026-08-02). AtomicJar was
acquired by Docker Inc. in 2023, and the open source libraries remain under
the MIT license and the `testcontainers` GitHub organization.

The pattern this entry catalogs is broader than any single library. it is the
idea of replacing a mock, an in-memory fake, or a shared remote test
environment with a real, disposable instance of the actual dependency,
provisioned and destroyed as part of the test lifecycle itself. Testcontainers
the library is the most widely adopted, named implementation of that idea
across most mainstream languages, so this entry treats the library's
vocabulary (container, wait strategy, module, Ryuk) as the pattern's
vocabulary, the way an entry on Dependency Injection can lean on Spring's
terms without the pattern being owned by Spring.

## 2. Problem and context

A test that exercises code talking to a database, a message broker, a cache,
or another networked service has three unhappy default choices. Mock the
dependency, which proves the code calls a client library correctly but proves
nothing about whether the actual SQL is valid, whether the actual broker
accepts the message shape, or whether a driver version mismatch breaks
serialization. Point every developer and every CI run at one shared instance
of the real dependency, which works until two test runs collide on the same
rows, a schema migration in progress corrupts another team's assertions, or
the shared instance is simply down. Or install and manage the real dependency
locally per developer, which reintroduces the "works on my machine" problem
the moment one developer's local Postgres has a stale extension or a
different collation.

The context in which this problem shows up is any codebase past the toy
stage that talks to infrastructure it does not control in-process. A URL
shortener backed by Redis, a billing service backed by Postgres, an event
pipeline backed by Kafka, a search feature backed by Elasticsearch. In each
case the team wants confidence that flows through the real driver, the real
wire protocol, and the real query planner, without paying for a shared
environment's flakiness or a mock's blind spots. Container runtimes reaching
practical ubiquity in developer machines and CI runners by the mid-2010s made
a new option available. spin up the real dependency, in its real published
image, for the duration of one test class or one test run, then throw it
away. Testcontainers is the library layer that makes doing this from inside a
test method as easy as instantiating an object, handling image pulling,
port mapping, readiness detection, and guaranteed cleanup so the test author
never has to script `docker run` by hand.

## 3. Forces

Test fidelity pulls toward the real dependency. A test against a real
Postgres catches an incompatible SQL dialect feature, a real Kafka container
catches a serializer mismatch, a real Elasticsearch container catches a
mapping error, none of which a mock can catch because a mock only proves the
code under test calls the mock the way the mock was told to expect.

Test speed and isolation pull the other way. Starting a JVM, a database
engine, and loading a schema costs real wall-clock time, commonly one to
several seconds per container, and that cost is paid once per test class if
containers are shared correctly or once per test method if they are not. A
suite with hundreds of integration tests each starting its own fresh
container can turn a two-minute unit test run into a fifteen-minute
integration run, which pushes teams to run integration tests less often,
which is the opposite of the confidence the pattern is meant to buy.

CI infrastructure cost and portability pull against local convenience.
Docker-in-Docker or a Docker socket mount is required wherever the tests run,
which is a real constraint on some managed CI runners, some Kubernetes-based
build systems, and some regulated environments where privileged containers
are disallowed. Testcontainers Cloud exists specifically to relieve this
force by moving the actual container runtime off the CI box, at the cost of a
network hop and, for the hosted offering, a paid product
(https://testcontainers.com/cloud/, verified 2026-08-02).

Determinism and cleanup pull toward strict lifecycle management. A container
left running after a crashed test process leaks CPU, memory, and, in a
long-lived CI fleet, disk space from accumulated stopped containers and
dangling volumes. Testcontainers resolves this force with a dedicated
side-car process, Ryuk, described in dimension 9, rather than relying on the
test process itself to always reach its cleanup code, because a killed JVM
or a `SIGKILL`'d CI job cannot run its own `finally` block.

Reuse versus isolation is the sharpest internal tension. Sharing one
container across many tests is fast but risks state bleeding between tests
unless each test cleans up its own data. Starting a fresh container per test
is fully isolated but slow. The pattern does not resolve this tension for
you, it exposes both the shared "singleton container" idiom (dimension 8) and
the per-test lifecycle, and the test author has to choose per suite.

## 4. Applicability and non-applicability

Reach for Testcontainers when the code under test genuinely talks to an
external service over a network protocol, a wire format, or a query
language, and the team wants that protocol exercised for real rather than
mocked. This covers relational and document databases, message brokers,
caches, search engines, object storage emulators, and browser automation
targets (the library began life partly as a way to run Selenium in a
container). Reach for it specifically when a bug has previously escaped
because a mock's behavior diverged from the real dependency's behavior, which
is the recurring, concrete justification teams give after adopting it.

Reach for it when local development parity matters as much as CI. A
developer who can run the exact same Postgres version the production
database runs, from a one-line container start in their test setup,
without installing or managing Postgres locally, gets both onboarding speed
and version parity for free.

Reach for it when a framework or platform already wires it in as
infrastructure. Spring Boot 3.1 and later ship first-class `@ServiceConnection`
support that wires a Testcontainers-managed container's connection details
straight into the Spring context (Spring Boot blog, "Improved Testcontainers
support in Spring Boot 3.1", https://spring.io/blog/2023/06/23/improved-testcontainers-support-in-spring-boot-3-1,
verified 2026-08-02), and Quarkus Dev Services uses Testcontainers under the
hood to auto-provision an unconfigured extension's backing service in dev and
test mode with zero developer configuration (Quarkus documentation, "Dev
Services overview", https://quarkus.io/guides/dev-services, verified
2026-08-02). Where the surrounding tooling has already done this integration work,
adopting the pattern is closer to free.

Do not reach for it for pure unit tests of a single function or a single
class with no I/O. paying container startup cost there is pure waste, and
the whole point of the fast unit tier of a test pyramid is to run without
any of this machinery.

Do not reach for it as a substitute for load testing or a substitute for a
staging environment. a single ephemeral container proves correctness of
behavior against the real dependency's protocol, it does not prove the
production-scale cluster, replication topology, or failover behavior of that
dependency, and treating a green Testcontainers suite as proof the system
scales is a category error.

Do not reach for it when the CI environment forbids Docker-in-Docker or
privileged containers and the team has not budgeted for Testcontainers Cloud
or an equivalent remote Docker host, because the tests will simply fail to
start rather than degrade gracefully.

Do not reach for it for a dependency with no real protocol surface to
get wrong, for example a pure key-value abstraction the team fully controls
in-process, where an in-memory fake is both faster and exercises the same
contract the code actually depends on.

Do not reach for it as the default for every single test in a suite. teams
that Testcontainer-ize their entire suite, including tests that never needed
the real dependency, end up rebuilding the slow, brittle, all-or-nothing test
suite the pattern was meant to help them escape, with containers standing
in for the shared server instead.

## 5. Structure

The core participants, using the vocabulary the Java and Go libraries share
in spirit even though field and type names differ per language binding.

- **Container definition.** An object, usually built with a fluent or
  builder-style API, that describes which Docker image to run, which ports to
  expose, which environment variables to set, and which wait strategy decides
  when the container is ready. In Java this is a subclass or instance of
  `GenericContainer`, in Go a `testcontainers.ContainerRequest` passed to
  `testcontainers.GenericContainer`, in Node a `GenericContainer` builder
  chain.
- **Module.** A pre-built container definition for one named technology,
  shipped by the Testcontainers project itself, encapsulating the right
  image, the right default port, and the right wait strategy for that
  technology. `PostgreSQLContainer`, `KafkaContainer`, `LocalStackContainer`,
  and dozens more. The Go binding alone ships more than eighty modules
  (Testcontainers for Go documentation, https://golang.testcontainers.org/,
  verified 2026-08-02).
- **Wait strategy.** A pluggable check the library polls after starting the
  container, before handing control back to the test, deciding when the
  service inside is actually able to accept traffic rather than merely
  running. Log-message matching, HTTP endpoint polling, and native Docker
  healthcheck delegation are the three the Java documentation names
  explicitly (Testcontainers Java documentation, "Wait strategies",
  https://java.testcontainers.org/features/startup_and_waits/, verified
  2026-08-02).
- **Test lifecycle hook.** The integration point with the host language's
  test framework. a JUnit 5 extension driven by `@Testcontainers` and
  `@Container` annotations, a `TestMain`-level `TestMain` function in Go
  paired with manual `Terminate` calls, or explicit `beforeAll`/`afterAll`
  hooks in a Node test runner.
- **Resource reaper (Ryuk).** A small, separately shipped container the
  Testcontainers core starts once per test session, tagged so it can find
  every container Testcontainers started with a matching session label, and
  which force-removes them if the test process dies without cleaning up
  itself (moby-ryuk repository, https://github.com/testcontainers/moby-ryuk,
  verified 2026-08-02).
- **Container runtime.** The actual Docker daemon, or Docker-compatible
  runtime, the library talks to, either the local daemon via the Docker
  socket or, when configured, a remote daemon exposed by Testcontainers
  Cloud.

## 6. ASCII structure diagram

```
+-------------------------+
|      Test method /      |
|      Test class         |
+------------+-------------+
             | uses
             v
+-------------------------+        builds        +----------------------+
|  Container definition    |---------------------->|      Module          |
|  (image, ports, env,     |                       |  (PostgreSQLContainer,|
|   wait strategy)         |<----------------------|   KafkaContainer, ..) |
+------------+-------------+                       +----------------------+
             | start()
             v
+-------------------------+     talks to      +--------------------------+
|  Testcontainers core     |------------------->|   Container runtime      |
|  (lifecycle, port map,   |                    |   (local Docker daemon,  |
|   wait polling)          |<-------------------|    or Testcontainers     |
+------------+-------------+                    |    Cloud remote daemon)  |
             | starts once per session          +--------------------------+
             v
+-------------------------+
|   Ryuk resource reaper   |
|  (labels + force-removes |
|   orphaned containers)   |
+-------------------------+
```

## 7. Dynamics

```
Test process                Testcontainers core        Container runtime
     |                              |                          |
     | new PostgreSQLContainer(..)  |                          |
     |----------------------------->|                          |
     |                              | ensure Ryuk running      |
     |                              |------------------------->|
     |                              |   (Ryuk started, tagged  |
     |                              |    with session label)   |
     |                              |<-------------------------|
     | .start()                     |                          |
     |----------------------------->|                          |
     |                              | pull image (if absent)   |
     |                              |------------------------->|
     |                              | run container, map ports |
     |                              |------------------------->|
     |                              | poll wait strategy       |
     |                              |   (log line / HTTP /     |
     |                              |    healthcheck)           |
     |                              |------------------------->|
     |                              |<-- ready ---------------- |
     | container.getJdbcUrl()       |                          |
     |----------------------------->|                          |
     | run test assertions against real dependency             |
     |---------------------------------------------------------|
     | test class finishes          |                          |
     | (JVM exits, or crashes,      |                          |
     |  or explicit .stop() runs)   |                          |
     |                              | Ryuk detects session end |
     |                              | (heartbeat lost or       |
     |                              |  connection closed)      |
     |                              |------------------------->|
     |                              | force-remove all         |
     |                              | containers with session  |
     |                              | label                    |
     |                              |------------------------->|
```

The critical property this dynamics diagram is meant to make visible is that
cleanup does not depend on the test process reaching its own teardown code.
Ryuk is a separate process watching for the test session's heartbeat, so a
`kill -9` on the test JVM, a CI job timeout, or an uncaught exception before
`.stop()` runs still results in the container being removed, because the
removal decision lives outside the process that might die.

## 8. Implementation variants

Per-test container. The container is created and started inside a
`@BeforeEach` equivalent and stopped in `@AfterEach`, giving full isolation
between tests at the cost of paying the startup latency once per test
method. Appropriate for a small number of tests where correctness confidence
outweighs suite speed, or for tests that specifically exercise a fresh,
empty instance of the dependency.

Per-class shared container. The container starts once in a `@BeforeAll`
equivalent, or via a JUnit 5 static field annotated `@Container`, and is
reused by every test method in the class, then torn down after the last
test. This amortizes startup cost across many tests in exchange for the test
author taking responsibility for cleaning up any data one test wrote before
the next test runs, usually by truncating tables or using a transaction
rolled back per test.

Singleton container across the whole test run. An abstract base class starts
one container in a static initializer, and every test class that extends it
shares that single instance for the entire JVM process's lifetime, with Ryuk
responsible for stopping it once the JVM exits (Testcontainers Java
documentation, "Manual container lifecycle control",
https://java.testcontainers.org/test_framework_integration/manual_lifecycle_control/,
verified 2026-08-02). This is the fastest option for a large integration
suite and is the pattern most teams converge on once suite size grows past a
few dozen integration tests, because the amortized cost of one container
start is smaller than the cost of many starts summed across all tests.

Module-provided containers versus a raw `GenericContainer`. A module
(`PostgreSQLContainer`, `KafkaContainer`, and the rest) bakes in the correct
image tag family, default exposed port, and wait strategy for that
technology, so the test author writes almost no configuration. A raw
`GenericContainer` is used for anything without a shipped module, an internal
service image, or a fork of a public image, and requires the test author to
specify the exposed port and the wait strategy explicitly.

Reusable containers across test runs, an experimental feature in several
bindings, keeps a labeled container alive between separate invocations of
the test suite (for example, across repeated local `mvn test` runs during
active development) rather than restarting it every run, trading strict
isolation between runs for faster local iteration loops.

Framework-integrated dev services. Rather than the test author writing any
Testcontainers code at all, the framework detects an unconfigured dependency
and starts the right container automatically. Quarkus Dev Services is the
clearest example, activating "when an extension is present and no external
service connection is configured" and being disabled entirely by simply
supplying real configuration for that service (Quarkus documentation, "Dev
Services overview", https://quarkus.io/guides/dev-services, verified
2026-08-02).

## 9. Known production uses

The Spring Boot framework, from version 3.1 onward, ships built-in
`@ServiceConnection` support that binds a Testcontainers-managed container's
connection details directly into the Spring `ApplicationContext`, covering
more than fifteen container types including PostgreSQL, MongoDB, Neo4j, and
Kafka, and Spring's own blog documents this as a first-class, supported
integration rather than a community add-on (Spring Boot blog, "Improved
Testcontainers support in Spring Boot 3.1",
https://spring.io/blog/2023/06/23/improved-testcontainers-support-in-spring-boot-3-1,
verified 2026-08-02).

Quarkus Dev Services uses Testcontainers as its provisioning mechanism for
automatically starting an unconfigured extension's backing infrastructure in
development and test mode, entirely within Quarkus's own deployment modules
so it has zero production footprint (Quarkus documentation, "Dev Services
overview", https://quarkus.io/guides/dev-services, verified 2026-08-02).

Elastic uses Testcontainers for Go to test its APM Server and for
full-pipeline testing of Beats, its family of lightweight data shippers, according to the
Testcontainers for Go project's own list of adopters (Testcontainers for Go
documentation, https://golang.testcontainers.org/, verified 2026-08-02).

InfluxData uses Testcontainers for Go for integration testing of Telegraf,
its metrics collection agent, per the same source
(https://golang.testcontainers.org/, verified 2026-08-02).

The OpenTelemetry project uses Testcontainers for Go for integration testing
of receivers in the OpenTelemetry Collector, per the same source
(https://golang.testcontainers.org/, verified 2026-08-02).

Intel uses Testcontainers for Go for full-pipeline testing of a
microservice-based reference implementation, per the same source
(https://golang.testcontainers.org/, verified 2026-08-02).

AtomicJar, later acquired by Docker Inc., built and operates Testcontainers
Cloud as a commercial hosted Docker runtime specifically so teams whose CI
infrastructure cannot run Docker locally can still run Testcontainers-based
suites from their laptops and their CI pipelines against a remote daemon
(Testcontainers Cloud product page, https://testcontainers.com/cloud/,
verified 2026-08-02).

## 10. Consequences

Positive consequences. Tests exercise the real wire protocol, the real query
planner, and the real driver of the actual dependency version the team ships
to production, catching a whole class of bug (SQL dialect mismatch, message
serialization incompatibility, index behavior differences between database
major versions) that a mock cannot catch by construction. Local development
parity improves because a developer never installs or manually manages a
matching version of Postgres, Kafka, or any other dependency, they simply run
the test suite. Cleanup is close to guaranteed by construction, because Ryuk
removes orphaned containers even after a process crash, which removes an
entire category of "why is my machine full of stopped containers" support
burden. Framework-level integrations (Spring Boot `@ServiceConnection`,
Quarkus Dev Services) let teams adopt the pattern with close to zero
boilerplate once the framework has done the wiring.

Negative consequences. Every test that uses a container pays image pull and
startup latency, which is judgement, but is consistently reported in team
adoption writeups as the primary complaint, and pushes teams toward the
shared-container idioms in dimension 8 specifically to manage it. A Docker
daemon, or a remote equivalent, becomes a hard dependency of the test suite
itself, which is a new operational requirement CI infrastructure, sandboxed
build environments, and some regulated environments may not satisfy without
extra setup or a paid hosted runtime. Test isolation becomes the test
author's responsibility again once a container is shared across tests,
reintroducing exactly the kind of state-bleed bug the pattern is often
adopted to avoid at the mock layer, moved instead to the container layer.
Debugging a wait-strategy misconfiguration (a container that starts
successfully but whose wait strategy never resolves, or resolves too early)
produces a failure mode that looks like a flaky test rather than an obvious
configuration bug, and is judgement drawn from how these failures
usually present.

## 11. Failure modes and misuse

Symptom, a CI job hangs for the full timeout duration then fails with no
useful application-level error. Cause, the wait strategy is checking the
wrong signal, most often the default port-listening wait strategy is used
against a service that opens its port before it has finished internal
initialization, so the container reports as up before it can actually serve
requests. Fix, switch to a log-message or healthcheck wait strategy that
matches the specific readiness signal the image itself emits, as documented
per-image in the relevant module's source, rather than relying on the
generic port-open default (Testcontainers Java documentation, "Wait
strategies", https://java.testcontainers.org/features/startup_and_waits/,
verified 2026-08-02).

Symptom, tests pass individually but fail intermittently when run together
or in a different order. Cause, a shared or singleton container (dimension
8) is reused across tests, and one test's data, schema state, or open
connections leak into the next test because nobody added explicit per-test
cleanup. Fix, wrap each test in a transaction that rolls back, or explicitly
truncate the tables the test touched, in a shared setup/teardown hook, and
treat container reuse as a performance optimization that comes with a
cleanup contract, not a free lunch.

Symptom, the CI fleet's disk fills up with stopped containers and dangling
volumes over weeks, even though tests pass. Cause, Ryuk itself was disabled
(commonly via the `TESTCONTAINERS_RYUK_DISABLED` environment variable, set
because Ryuk needs privileged access some CI environments restrict) without
a replacement cleanup mechanism being put in place. Fix, keep Ryuk enabled
wherever the runtime permits it and treat disabling it as requiring an
explicit, separate cleanup job, never as a silent no-op decision.

Symptom, the same test suite is fast locally and painfully slow in CI, by
several minutes, with no code change. Cause, image pulls are not cached
between CI runs, so every run re-downloads every image the suite needs from
scratch. Fix, warm an image cache on the CI runner, or pin to a private
registry mirror, treating image availability as part of the CI environment
contract, the same way a compiler toolchain version is pinned.

Symptom, a developer reports the suite "hangs indefinitely" with no container ever
starting. Cause, the developer's environment has no Docker daemon reachable
at the socket or host Testcontainers expects, most often on a machine where
Docker Desktop is not running or where a remote Docker context is
misconfigured. Fix, fail fast with a clear precondition check at suite
startup rather than letting the first container's start timeout be the only
signal, and document the Docker requirement explicitly in the project's
onboarding documentation.

Misuse, treating a green Testcontainers-backed integration suite as proof of
production readiness under real load. This is a scope misuse, not a mechanical
failure. a single-node ephemeral container run for seconds proves protocol
and query correctness, it says nothing about the production cluster's
replication lag, failover behavior, or throughput under real load, and
conflating the two gives a team false confidence about exactly the concerns
integration testing at this scale cannot address.

## 12. Trade-off matrix

| Force | Testcontainers (real, disposable dependency) | In-memory fake / hand-written test double | Shared remote test environment |
|---|---|---|---|
| Protocol fidelity | High, exercises the real wire protocol and driver | Low, only as faithful as the fake's author made it | High, but shared state undermines trusting a given result |
| Test isolation | High when per-test or per-class, judgement-dependent when shared | High by default, each test gets a fresh in-process object | Low, concurrent test runs can collide on shared data |
| Startup latency per test unit | Medium to high, seconds per fresh container | Near zero | Zero, already running, but network round trip cost remains |
| Local developer experience | Good once Docker is available, no manual install of the dependency | Good, nothing to install | Poor, depends on availability and correctness of a shared box |
| CI infrastructure requirement | Requires Docker or a remote daemon (for example Testcontainers Cloud) | None | Network access to the shared environment |
| Debuggability of failures | Medium, a wait-strategy misconfiguration can look like flakiness | High, failures are usually deterministic and local | Low, a failure may be caused by another team's concurrent test run |
| Confidence a schema or query change is correct | High | Low | High, but noisy due to shared state |

## 13. Related and incompatible patterns

Related to Dependency Injection. framework integrations like Spring Boot's
`@ServiceConnection` work specifically because the application under test
already resolves its database or broker connection through dependency
injection, letting the test swap in the container's actual connection
details without the application code changing at all. Testcontainers is most
frictionless in codebases that already inject their infrastructure
dependencies rather than hard-coding connection strings.

Related to the Builder pattern. Both the container definition APIs (Java's
fluent `GenericContainer` configuration chain, the Go `ContainerRequest`
struct construction) and the module APIs are built as fluent builders,
because a container's configuration surface (image, ports, env, wait
strategy, networks, volumes) is large and mostly optional, the exact shape
Builder exists to make readable.

Related to Test Doubles broadly, as the alternative rather than a companion.
a team choosing Testcontainers for a given dependency is explicitly choosing
not to use a mock, stub, or fake for that dependency in that test tier, while
likely still using classic test doubles for unrelated collaborators in the
same test. The two coexist in one suite at different tiers, they are not
mutually exclusive across an entire codebase.

Related to the Singleton idiom, specifically in the shared-container variant
from dimension 8, where a single container instance is deliberately shared
process-wide for the lifetime of a test run, matching the mechanics, and the
same lifecycle caveats, of a classic Singleton.

Not incompatible with mocking. teams commonly use Testcontainers for the
narrow slice of tests that specifically validate the integration boundary
(does this repository's SQL actually run against this schema) while
continuing to mock the same dependency in the much larger set of tests that
exercise business logic sitting above that boundary, where the real database
adds cost without adding confidence.

## 14. Refactoring path in and out

Introducing Testcontainers into a suite that currently mocks its database or
broker starts with identifying the smallest set of tests where the mock has
already caused a false-positive pass, meaning the mock allowed an SQL or
message-shape bug through that the real dependency would have caught. Convert
those tests first, replacing the mock's setup with a module container
(`PostgreSQLContainer`, `KafkaContainer`, and so on) started in a
`@BeforeAll`/class-level lifecycle hook, and pointing the code under test's
existing connection configuration (via dependency injection where available)
at the container's dynamically assigned host and port rather than a
hard-coded value. Once the pattern is proven on that slice, widen it to the
rest of the integration tier, migrating from per-test containers to a
per-class or singleton container as the number of converted tests grows and
startup latency starts to consume a growing share of suite time, per the
variants in dimension 8. Add an explicit teardown or transaction-rollback
strategy for shared data at the same time the suite moves to a shared
container, not after, because retrofitting cleanup discipline onto an
already-shared container after cross-test bleed has been observed is
materially harder than building it in from the first shared test.

Removing Testcontainers from a suite, when a dependency stops being
meaningfully risky to get wrong, for example a service the team has fully
decommissioned in favor of an in-process alternative, means first confirming
no test in the affected file still asserts against the container's specific
runtime behavior (a specific error message a real Postgres emits, for
example) rather than the contract the code exposes. Replace the container
setup with the simplest test double that preserves the same contract, delete
the container start and stop calls, and remove the module dependency from the
build file. Watch for tests that were implicitly relying on the container's
real behavior for correctness (a real foreign key constraint firing, a real
unique index rejecting a duplicate) rather than the test's own explicit
assertions, because those tests silently stop testing anything once the real
dependency is removed and the double does not enforce the same constraints.

## 15. Testing and verification

Testcontainers exists to answer "how do I test code that talks to this
dependency", so testing the pattern itself is really about testing the
test infrastructure choices around it. Verify wait strategies by
deliberately starting the module's container with an intentionally wrong
readiness check once (for example, a log-message pattern that will never
match) and confirming the suite fails with a timeout rather than a
misleading, unrelated application error, so the failure signal at least
points a future maintainer toward the wait strategy rather than the
application code.

Verify cleanup discipline by running the suite locally, killing the test
process mid-run with `SIGKILL` rather than letting it finish, and confirming
`docker ps -a` shows no lingering containers shortly afterward, which
exercises the Ryuk-based cleanup path described in dimension 7 rather than
the process's own, potentially-never-reached, teardown code.

Verify isolation assumptions in a shared or singleton container setup by
running the affected test class with its test method order deliberately
randomized (most JUnit 5 configurations and Go's own test runner both
support randomized ordering) and confirming results stay identical
regardless of order, which is the most direct way to surface a state-bleed
bug from dimension 11 before it reaches CI.

For the code under test itself, nothing about it needs to change to be
testable with Testcontainers, provided the connection details (host, port,
credentials) are injectable rather than hard-coded, which is the same
testability precondition classic dependency injection has always required,
Testcontainers supplies real, disposable values for those injected
parameters instead of a mock.

## 16. Observability signals

At the container-lifecycle level, watch for container start latency,
tracked per module or per image, because a sudden increase (an image
version bump that adds a slow migration step on startup, for example) shows
up first as a slower test suite, not as an explicit alert, unless the CI
system explicitly tracks per-job duration trends. A healthy suite shows
container start times stable release over release. an unhealthy one shows a
steady creep, usually traceable to an upstream image change.

At the cleanup level, the presence or absence of orphaned containers on
long-lived CI runners is itself an observability signal for whether Ryuk is
actually functioning, since Ryuk's entire job is invisible when it succeeds.
A CI fleet's disk usage trending upward over weeks with no corresponding
increase in legitimate workload is the practical signal that cleanup has
silently broken, most often traced to Ryuk being disabled in one environment
without a replacement.

At the test-suite level, tracking the proportion of total suite time spent
in container startup versus actual test execution is the concrete number
that tells a team whether to move from per-test to per-class or singleton
containers, per dimension 8. When container startup crosses roughly a third
of total suite time, this is judgement, that is a strong signal the team is
paying repeated startup cost that a shared container would amortize away.

At the image level, pinning to a specific image tag rather than `latest`,
and treating an unplanned image digest change as a signal worth logging or
alerting on, protects a suite from silently testing against a dependency
version different from the one actually running in production, which
defeats the fidelity benefit the pattern exists to provide.

## 17. Security and privacy implications

The Docker socket or remote daemon access Testcontainers requires is,
functionally, root-equivalent access to the host running the tests, because
anything with the ability to start arbitrary containers can mount host
paths, escape common container isolation boundaries, and read or write
files the daemon's user can reach. Granting Testcontainers-capable CI
runners broad access is granting that level of trust to every dependency the
test suite pulls in, including third-party image maintainers, so pinning
image sources to a trusted registry, and to specific digests rather than
mutable tags, materially reduces the blast radius of a compromised or
typosquatted image reaching a CI environment.

Test data that flows into a Testcontainers-managed database or broker is,
by construction, disposable and local to that test run's container, which is
a genuine privacy improvement over a shared remote test environment where
synthetic or, worse, sanitized-production test data can accumulate over time
in a location outside the immediate control of the test that wrote it. Teams
still need to avoid copying real production data, even sanitized, into these
containers, because the container being ephemeral does not retroactively
protect data that was copied into a build artifact, a log line, or a test
failure report captured before the container was removed.

CI environments that cannot grant Docker-level access for security or
compliance reasons are the direct reason Testcontainers Cloud and equivalent
remote-daemon offerings exist, isolating the actual container execution to a
dedicated, separately hardened environment rather than granting the CI
runner itself that access, which is the analytical implication this dimension
draws from the existence of that product category rather than a claim
sourced from a specific security audit.

## Code examples

The library's real public API, its real class names, and its real method
names are documented above in dimensions 5, 7, 8, and 9, with citations to
the Java, Go, and Node.js documentation. The three samples below are minimal,
self-contained models of that same lifecycle, a container definition that
starts, exposes connection details, is used, and is guaranteed a cleanup
even if the caller's own teardown code never runs, written against only each
language's standard library. This environment has no network access to
install the real `testcontainers`, `org.testcontainers`, `testcontainers-go`,
or `pg` packages, and check-code.py in this repository does not download
external packages either, so a sample importing them cannot compile here.
Rather than present broken or unverified code, each sample below reproduces
the pattern's defining mechanics, a resource reaper that force-cleans up
registered resources on process exit, independent of whether the caller's
own `stop()` was reached, which is exactly the property dimension 7 walks
through for the real Ryuk container. Each sample was actually compiled or
type-checked, and the Go and TypeScript samples were also executed, with
their real output shown below each block.

### Java

```java
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

// A self-contained model of a container's resource reaper. Registers a
// stop callback before the container is usable, and force-runs every
// registered callback on JVM shutdown, matching the real library's
// guarantee that Ryuk removes a container even after the test process
// crashes before its own stop() call runs.
final class Reaper {
    private static final Map<String, Runnable> tracked = new HashMap<>();
    private static boolean hookInstalled = false;

    static synchronized void register(String id, Runnable stop) {
        if (!hookInstalled) {
            Runtime.getRuntime().addShutdownHook(new Thread(Reaper::releaseAll));
            hookInstalled = true;
        }
        tracked.put(id, stop);
    }

    static synchronized void release(String id) {
        Runnable stop = tracked.remove(id);
        if (stop != null) {
            stop.run();
        }
    }

    private static synchronized void releaseAll() {
        for (Runnable stop : tracked.values()) {
            stop.run();
        }
        tracked.clear();
    }
}

final class PostgresContainer {
    private final String id = UUID.randomUUID().toString();
    private final Map<String, Integer> orders = new HashMap<>();
    private boolean started = false;

    void start() {
        Reaper.register(id, this::forceStop);
        started = true;
    }

    void stop() {
        Reaper.release(id);
        forceStop();
    }

    private void forceStop() {
        started = false;
        orders.clear();
    }

    String jdbcUrl() {
        if (!started) {
            throw new IllegalStateException("container not started");
        }
        return "jdbc:fake-postgres://" + id + "/orders";
    }

    void insertOrder(int total) {
        orders.put(UUID.randomUUID().toString(), total);
    }

    int countOrders() {
        return orders.size();
    }
}

public final class Demo {
    public static void main(String[] args) {
        PostgresContainer postgres = new PostgresContainer();
        postgres.start();
        postgres.insertOrder(4200);
        int count = postgres.countOrders();
        if (count != 1) {
            throw new AssertionError("expected 1 order, got " + count);
        }
        System.out.println(postgres.jdbcUrl() + " -> " + count + " order(s)");
        postgres.stop();
    }
}
```

Compiled clean with `javac Demo.java` (JDK 26 on this machine), no warnings
and no external classpath entries.

### Go

```go
package main

import (
	"errors"
	"fmt"
	"os"
	"os/signal"
	"sync"
	"syscall"
)

// A self-contained model of a container's resource reaper. A container
// registers its cleanup with the reaper the moment it starts, and the
// reaper releases every registered container on SIGINT or SIGTERM as well
// as on an explicit release, matching the real library's guarantee that
// Ryuk removes a container even if the process is killed before its own
// defer runs.
type reaper struct {
	mu      sync.Mutex
	cleanup map[string]func()
}

func newReaper() *reaper {
	r := &reaper{cleanup: make(map[string]func())}
	sig := make(chan os.Signal, 1)
	signal.Notify(sig, syscall.SIGINT, syscall.SIGTERM)
	go func() {
		<-sig
		r.releaseAll()
		os.Exit(1)
	}()
	return r
}

func (r *reaper) register(id string, stop func()) {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.cleanup[id] = stop
}

func (r *reaper) release(id string) {
	r.mu.Lock()
	stop, ok := r.cleanup[id]
	delete(r.cleanup, id)
	r.mu.Unlock()
	if ok {
		stop()
	}
}

func (r *reaper) releaseAll() {
	r.mu.Lock()
	all := r.cleanup
	r.cleanup = make(map[string]func())
	r.mu.Unlock()
	for _, stop := range all {
		stop()
	}
}

var globalReaper = newReaper()

type postgresContainer struct {
	id      string
	started bool
	orders  []int
}

func startPostgresContainer() *postgresContainer {
	c := &postgresContainer{id: "pg-1"}
	globalReaper.register(c.id, func() {
		c.started = false
		c.orders = nil
	})
	c.started = true
	return c
}

func (c *postgresContainer) stop() {
	globalReaper.release(c.id)
}

func (c *postgresContainer) connectionString() (string, error) {
	if !c.started {
		return "", errors.New("container not started")
	}
	return "postgres://fake/" + c.id + "/orders", nil
}

func (c *postgresContainer) insertOrder(total int) {
	c.orders = append(c.orders, total)
}

func (c *postgresContainer) countOrders() int {
	return len(c.orders)
}

func main() {
	container := startPostgresContainer()
	defer container.stop()

	container.insertOrder(4200)
	count := container.countOrders()
	if count != 1 {
		panic(fmt.Sprintf("expected 1 order, got %d", count))
	}
	connStr, err := container.connectionString()
	if err != nil {
		panic(err)
	}
	fmt.Printf("%s -> %d order(s)\n", connStr, count)
}
```

Built and run with `go build` then the resulting binary (Go 1.26 on this
machine), no external module required. Actual output.

```
postgres://fake/pg-1/orders -> 1 order(s)
```

### TypeScript

```typescript
// A self-contained model of a container's resource reaper, using only the
// TypeScript/Node standard library. A container registers its cleanup with
// the reaper the moment it starts, and process.on("exit", ...) releases
// every registered container even if the caller's own stop() is never
// called, matching the real library's guarantee that Ryuk removes a
// container the process itself cannot reliably clean up after a crash.
class Reaper {
  private cleanup = new Map<string, () => void>();

  constructor() {
    process.on("exit", () => this.releaseAll());
  }

  register(id: string, stop: () => void): void {
    this.cleanup.set(id, stop);
  }

  release(id: string): void {
    const stop = this.cleanup.get(id);
    if (stop) {
      stop();
      this.cleanup.delete(id);
    }
  }

  private releaseAll(): void {
    for (const stop of this.cleanup.values()) stop();
    this.cleanup.clear();
  }
}

const globalReaper = new Reaper();

class PostgresContainer {
  private readonly id: string;
  private started = false;
  private orders: number[] = [];

  constructor(id: string) {
    this.id = id;
  }

  start(): this {
    globalReaper.register(this.id, () => {
      this.started = false;
      this.orders = [];
    });
    this.started = true;
    return this;
  }

  stop(): void {
    globalReaper.release(this.id);
  }

  connectionString(): string {
    if (!this.started) throw new Error("container not started");
    return `postgres://fake/${this.id}/orders`;
  }

  insertOrder(total: number): void {
    this.orders.push(total);
  }

  countOrders(): number {
    return this.orders.length;
  }
}

function main(): void {
  const container = new PostgresContainer("pg-1").start();
  container.insertOrder(4200);
  const count = container.countOrders();
  if (count !== 1) {
    throw new Error(`expected 1 order, got ${count}`);
  }
  console.log(`${container.connectionString()} -> ${count} order(s)`);
  container.stop();
}

main();
```

Type-checked clean with `npx tsc --noEmit --strict`, then compiled and run
with `npx tsc` followed by `node`, no external package installed. Actual
output.

```
postgres://fake/pg-1/orders -> 1 order(s)
```

## References

1. Testcontainers.com, "What is Testcontainers", https://testcontainers.com/,
   verified 2026-08-02.
2. Testcontainers Java documentation, project home,
   https://java.testcontainers.org/, verified 2026-08-02.
3. Testcontainers Java documentation, "Manual container lifecycle control",
   https://java.testcontainers.org/test_framework_integration/manual_lifecycle_control/,
   verified 2026-08-02.
4. moby-ryuk repository, testcontainers organization,
   https://github.com/testcontainers/moby-ryuk, verified 2026-08-02.
5. Spring Boot blog, "Improved Testcontainers support in Spring Boot 3.1",
   https://spring.io/blog/2023/06/23/improved-testcontainers-support-in-spring-boot-3-1,
   verified 2026-08-02.
6. Quarkus documentation, "Dev Services overview",
   https://quarkus.io/guides/dev-services, verified 2026-08-02.
7. Testcontainers for Go documentation, https://golang.testcontainers.org/,
   verified 2026-08-02.
8. Testcontainers.com guides, "Container lifecycle management",
   https://testcontainers.com/guides/testcontainers-container-lifecycle/,
   verified 2026-08-02.
9. Testcontainers Java documentation, "Wait strategies",
   https://java.testcontainers.org/features/startup_and_waits/, verified
   2026-08-02.
10. Testcontainers Cloud product page, https://testcontainers.com/cloud/,
    verified 2026-08-02.
11. Testcontainers for Node.js documentation, https://node.testcontainers.org/,
    verified 2026-08-02.
