---
name: Contract Test
slug: contract-test
family: 14-testing
category: Testing
aliases: [Consumer-Driven Contract Test, Provider Verification Test, Interface Contract Test]
first_described: "Robinson 2006 (Consumer-Driven Contracts), formalized in Pact tooling from 2013"
maturity: canonical
related: [test-double, mock-object, stub, fake-object, service-mesh, circuit-breaker]
incompatible_with: []
verified: 2026-08-02
---

## 1. Name, aliases, and lineage

A contract test verifies that two independently deployed services, a consumer
and a provider, agree on the shape and semantics of the messages they exchange,
without either side running the other's full stack. The consumer side is also
called a "pact" in the Pact tooling ecosystem, and the provider side is called
"provider verification." The underlying idea, that an interface has an
agreement independent of any single implementation, traces back to Bertrand
Meyer's Design by Contract in Eiffel, described in "Object-Oriented Software
Construction," 2nd edition, 1997, chapter 11, where a routine's precondition,
postcondition, and invariant form a contract between caller and callee. What
this pattern entry covers is the narrower, cross-service testing technique that
turns that idea into an executable, versioned test artifact between two
network-separated services.

Ian Robinson named and described the consumer-driven variant of this idea in
his article "Consumer-Driven Contracts. A Service Evolution Pattern," published
on martinfowler.com on 12 June 2006. Robinson's framing is that a provider's
contract should emerge from the expectations of its actual consumers rather
than being defined unilaterally by the provider team, so that the provider
gets fine-grained, rapid feedback about which consumers depend on which parts
of its interface before a breaking change ships. Verified against
martinfowler.com/articles/consumerDrivenContracts.html on 2026-08-02.

The Pact framework, an open source implementation of consumer-driven contract
testing, formalized the mechanics in 2013 (originally built at REA Group in
Australia) and is now maintained under the pactflow.io and pact-foundation
organizations. Pact's own documentation defines contract testing as verifying,
"in isolation," that the messages an application sends or receives conform to
a shared understanding documented in a contract, generated automatically from
the consumer's own test suite. Verified against docs.pact.io on 2026-08-02.

Aliases in practice include "interface contract test," used in the OpenAPI and
gRPC tooling communities to describe schema-conformance checks that are not
necessarily consumer-driven, and "provider contract test," used when the
provider defines the schema unilaterally (a specification-driven, rather than
consumer-driven, contract). This entry treats both the consumer-driven and the
specification-driven variants as members of the same pattern family, because
they solve the same underlying problem with different authorities for the
contract's source of truth, and dimension 8 below separates them explicitly.

## 2. Problem and context

A team splits a monolith into services, or simply has two teams shipping two
deployables that talk over HTTP, gRPC, or a message queue. Each team runs its
own unit tests against its own code, and those tests pass. Each team also
writes integration tests, but a true end-to-end integration test requires
standing up the other service, its database, its own dependencies, and often
a shared staging environment. That environment is slow to provision, flaky
under concurrent use by multiple teams, and expensive to keep in sync with
what production actually runs. So most organizations end up in one of two
bad states. Either they skip cross-service verification entirely and rely on
manual QA or on production incidents to catch mismatches, or they build a
full end-to-end test suite that takes twenty minutes to run, fails for reasons
unrelated to the code under test (a flaky downstream dependency, a shared
staging database another team wrote to), and gets disabled or ignored within
a few months because nobody trusts a red result to mean anything.

The concrete symptom a reader will recognize is this. A provider team renames
a JSON field, or changes a field from optional to required, or drops a field
they believed nobody used. Their own test suite is green because it only
exercises their own code. Days or weeks later, a consumer team's production
service starts throwing deserialization errors or silently dropping data, and
nobody connects the two events until someone traces a stack trace back to a
commit in a different repository, owned by a different team, that shipped
without any signal that it would break a downstream consumer.

The context in which this pattern applies is specifically the space between
"my code is correct in isolation" and "the whole distributed system behaves
correctly together," for services that are developed, versioned, and deployed
independently. The pattern is not needed, and is actively wasteful, when both
sides of an interaction are compiled and deployed together as one unit, because
a compiler or a shared type system already enforces the agreement at build
time.

## 3. Forces

**Independent deployability versus interface stability.** Teams want to ship
their own service on their own schedule without coordinating a synchronized
release with every consumer. Consumers want a stable interface they can build
against without watching the provider's release notes. Contract tests let both
sides move independently as long as the contract itself does not change in an
incompatible way, but the pattern only works if the contract is checked on
every provider deployment, which introduces a coordination cost at CI time
even though it removes coordination cost at release-planning time.

**Test speed versus test fidelity.** A contract test runs in seconds because
it replays a small number of canned interactions against a stubbed HTTP layer
or a mocked message broker, rather than the real network stack of the real
dependency. That speed is bought by sacrificing fidelity. A contract test does
not exercise the provider's actual business logic, its actual database state,
or its actual authentication layer, so it cannot catch a bug where the
provider's logic is wrong but its schema is technically unchanged.

**Who owns the source of truth for the contract.** In the consumer-driven
variant (Robinson's original framing, implemented by Pact), the consumer
writes the expectations and the provider is verified against them, which
concentrates power with whoever actually depends on the interface but can
produce contract sprawl as every consumer expresses slightly different
expectations of the same endpoint. In the specification-driven variant
(an OpenAPI or a Protocol Buffers schema owned by the provider), the provider
is authoritative and consumers are checked against a single published schema,
which is simpler to govern but can drift from what consumers actually need
and can let a provider ship a technically-schema-valid change that still
breaks a consumer's business logic.

**Coupling versus decoupling.** A contract test deliberately introduces a
coupling, the contract file or the schema, between two services that are
otherwise decoupled at runtime. This is a favorable trade only when the
coupling is explicit, versioned, and checked in CI. An implicit or unchecked
version of the same coupling (two teams simply agreeing verbally on a schema
and trusting each other not to break it) produces all the coordination cost of
coupling with none of the safety benefit.

**Operability and broker infrastructure.** The consumer-driven variant with
Pact typically introduces a Pact Broker, a separate service that stores
contract versions and their verification results, and gates deployment on
verification status (the "can-i-deploy" check). This adds an operational
dependency, a service that must itself be available and correctly configured,
in exchange for making the safety property enforceable rather than aspirational.

## 4. Applicability and non-applicability

Reach for a contract test when.

- Two or more services are developed by different teams, or on different
  release cadences, and communicate over a network boundary (HTTP, gRPC,
  a message queue, an event stream).
- The cost of a full end-to-end integration test (standing up both real
  services, a shared database, real infrastructure) is high enough that the
  team either skips cross-service testing or tolerates a slow, flaky suite.
- The team wants deploy-time confidence, specifically the ability to answer
  the question "can I safely deploy this provider change without breaking a
  known consumer" before the deploy happens, not after a production incident.
- The interaction is asynchronous (a message queue, an event bus) where a
  runtime integration test is even harder to construct reliably than for
  synchronous HTTP, because message ordering and timing introduce their own
  flakiness independent of the contract itself.

Do NOT reach for a contract test when.

- Both sides of the interaction are compiled and deployed as a single unit
  (a monolith, or two modules inside one deployable). A shared type system,
  or a compiler, already enforces the agreement at build time, and adding a
  contract test here duplicates that enforcement at a much higher
  maintenance cost for zero additional safety.
- The interaction is with a third-party API you do not control and cannot
  register a contract against (a public payment gateway, a SaaS API with no
  Pact provider). A contract test against a system you cannot verify is not
  a contract test, it is a recorded fixture. Use a stub-and-replay technique
  like VCR-style cassette recording instead, and treat the third party's own
  published API version as the real contract.
- The team needs to verify business logic correctness, not interface shape.
  A contract test asserting that "the endpoint returns a 200 with a `total`
  field of type number" says nothing about whether the `total` value is
  arithmetically correct. That is the job of the provider's own unit and
  functional tests, not the contract test.
- The number of consumer-provider pairs is one and both are owned by the same
  small team with no separate release cadence. Robinson's own article frames
  the pattern as solving a service-evolution problem across organizational or
  team boundaries. Inside a single team with a shared backlog, direct
  communication and a shared changelog often solve the same problem at lower
  tooling cost.
- The system genuinely needs true end-to-end verification of a critical path
  (a checkout flow spanning five services). Contract tests are not a
  replacement for a small number of true end-to-end smoke tests. They
  eliminate the need for a large end-to-end matrix, not the need for any
  end-to-end coverage at all.

## 5. Structure

**Consumer.** The service that initiates the interaction (sends the request,
or reads from the queue). In the consumer-driven variant, the consumer's test
suite records the interactions it expects, and this record becomes the
contract. The consumer test runs against a mock or stub of the provider, never
against the real provider.

**Provider.** The service that responds to the interaction (serves the
request, or writes to the queue). The provider runs a separate verification
step that replays every recorded interaction from every consumer's contract
against its own real implementation (its real routing, its real
serialization, its real validation, though typically with test doubles for
its own downstream dependencies such as a database, seeded to states matching
what each interaction requires).

**Contract, sometimes called a Pact file, or a schema.** A versioned,
serializable artifact, typically JSON, describing one or more
request-response (or message-publish and message-consume) interactions, the
request shape, the expected response shape, and any matching rules (for
example, "this field must be a string matching a UUID pattern" rather than a
literal fixed value). In the specification-driven variant this artifact is
instead an OpenAPI document or a Protocol Buffers `.proto` file, owned by the
provider and consumed as a schema to validate against, not a set of recorded
interactions.

**Broker, optional but common in the consumer-driven variant.** A registry
service, most commonly the Pact Broker or its hosted variant PactFlow, that
stores every version of every contract, records every provider's verification
result against every contract version, and exposes a query, "can I deploy
this consumer version safely against what is in production for the
provider," and the reverse, that CI pipelines call before deploying either
side. The broker is what turns "we have contract tests" into "we have a
deploy gate," per Pact's own documentation of the can-i-deploy workflow.
Verified against docs.pact.io on 2026-08-02.

**Matcher.** The mechanism inside the contract that distinguishes "this exact
literal value must appear" from "a value of this type or shape must appear."
Contract testing frameworks (Pact in particular) provide type and regex
matchers specifically so that a contract does not become brittle against
values that legitimately vary between test runs, such as timestamps or
generated identifiers, while still asserting the shape is correct.

## 6. ASCII structure diagram

```
                     CONSUMER-DRIVEN VARIANT (Pact-style)

  +------------------+                         +------------------+
  |    Consumer      |                         |    Provider      |
  |   (Service A)    |                         |   (Service B)    |
  |                  |                         |                  |
  |  consumer test   |                         |  provider verify |
  |  suite runs       |                         |  step runs        |
  |  against a mock   |                         |  against REAL      |
  |  of Service B     |                         |  Service B code    |
  +--------+---------+                         +---------+--------+
           |                                             |
           | 1. records interactions                     | 3. replays every
           |    request shape,                            |    interaction from
           |     expected response                         |    every consumer
           v                                               |    contract, asserts
  +------------------+   2. publish contract   +----------v-------+
  |  Contract file    |------------------------>|   Pact Broker    |
  |  JSON, versioned   |                        |  contract store, |
  +------------------+                          |  verify results, |
                                                 |  can-i-deploy     |
                                                 +---------+--------+
                                                            |
                                                            | 4. CI on both sides
                                                            |    queries broker
                                                            |    before deploy
                                                            v
                                                 +------------------+
                                                 |  Deploy gate,    |
                                                 |  can-i-deploy?   |
                                                 +------------------+


                  SPECIFICATION-DRIVEN VARIANT (OpenAPI / proto)

  +------------------+                          +------------------+
  |    Provider      |----- owns and publishes ->|  Schema document |
  |   (Service B)    |     OpenAPI YAML,           |  single source   |
  |                  |      .proto file            |   of truth       |
  +------------------+                          +---------+--------+
                                                            |
                                    +-----------------------+------------------------+
                                    |                                                |
                                    v                                                v
                          +------------------+                            +------------------+
                          |  Provider test,  |                            |  Consumer test,  |
                          |  own responses    |                            |  own requests     |
                          |  validated against|                            |  validated against|
                          |  the schema        |                            |  the schema        |
                          +------------------+                            +------------------+
```

## 7. Dynamics

The consumer-driven flow runs in two independent phases, joined by the
broker, never by a live network call between the two services.

```
PHASE 1, consumer side, runs in the consumer's own CI pipeline

  1. Consumer test suite starts a local mock provider, an in-process HTTP
     stub, or Pact's mock server, instead of the real Service B.
  2. Test code sets up an expectation.
       given Service B has a user with id 42,
       when I GET /users/42,
       then it should respond 200 with a JSON body matching
       { id number, name string, email string }
  3. Consumer code under test makes the real HTTP call, hitting the mock.
  4. Mock returns the expected response; consumer's own logic runs against it
     and is asserted normally (this is an ordinary unit test at this point).
  5. If the interaction matched what was set up, the mock records it into a
     Pact contract file.
  6. Consumer's CI pipeline publishes the Pact file to the broker, tagged
     with the consumer's version (commit SHA or semantic version).

PHASE 2, provider side, runs in the provider's own CI pipeline, independently,
         at a different time, potentially by a different team

  1. Provider's CI pipeline pulls every contract published against it from
     the broker, one contract per consumer, potentially many consumers.
  2. For each recorded interaction in each contract, the provider verifier
       a. sets up the provider's own state to match what the interaction
          needs, a "provider state," for example "a user with id 42 exists,"
          usually by seeding a test database or a stub of the provider's own
          downstream dependency,
       b. sends the recorded request to the provider's real running code,
       c. compares the real response against the contract's expected
          response, using the matchers recorded in the contract.
  3. Verification results (pass or fail, per interaction, per consumer) are
     published back to the broker.
  4. Before either side deploys, its CI pipeline asks the broker the
     "can-i-deploy" question for that version against production; the broker
     answers based on whether every relevant contract has a passing
     verification between the specific versions about to be deployed
     together.
```

No step in this flow involves the consumer and the provider running at the
same time against each other. The entire safety guarantee comes from both
sides independently agreeing with the same recorded artifact, verified at
different times, by different pipelines, and reconciled through the broker's
version-matching logic rather than through a live network call.

## 8. Implementation variants

**Consumer-driven contract testing (Pact and equivalents).** The consumer
writes the expectations; contracts are generated as a byproduct of the
consumer's own tests; the provider is verified against every consumer's
contract. Strongest fit when there are many consumers of one provider and the
team wants to know exactly which consumers would break before a provider
change ships. Highest tooling investment (a broker, CI wiring on both sides).

**Specification-driven, schema-first, contract testing.** A provider
publishes an OpenAPI document or a `.proto` file as the single source of
truth; both provider responses and consumer requests are validated against
that one schema, typically with tools like Dredd, Schemathesis, or
`buf breaking` for Protocol Buffers (which specifically detects
backward-incompatible schema changes at the field-number and type level).
Simpler to govern with a single provider and many unknown or public
consumers, such as a public API, because it does not require every consumer
to write and publish their own contract. Weaker at catching a case where the
schema is technically valid but a specific consumer's business assumption
about the field's meaning changed.

**gRPC and Protocol Buffers backward-compatibility checking.** A narrower,
compile-time-adjacent form where the contract is the `.proto` file itself,
and the check is whether a new version of the file is a strict superset of
the old one (no field renumbering, no changing a field's wire type). This is
closer to a static compatibility check than a request-response contract test,
but it solves the identical problem, catching a provider change that would
break a consumer, before either side deploys.

**Message and event contract testing, the asynchronous variant.** Rather than
a request-response pair, the contract describes a message a producer
publishes to a queue or topic and the shape a consumer expects to read. Pact
supports this as "message pacts." The provider-side verification step here
does not make an HTTP call; it invokes the producer's own message-generation
function directly and asserts the generated message matches the contract,
because there is no synchronous request to intercept.

**Bi-directional contract testing.** A newer variant, documented by PactFlow
from 2022 onward, that reconciles the consumer-driven and specification-driven
approaches. The provider publishes its actual OpenAPI spec (generated from its
real code, not hand-written), and the broker diffs that spec against every
consumer's Pact-recorded expectations, removing the need for the provider
team to run a separate Pact verification step while keeping the
consumer-driven signal of exactly which consumers would be affected by a
given schema change.

## 9. Known production uses

**REA Group (realestate.com.au).** Pact originated at REA Group in Australia
around 2013 as an internal tool to solve exactly the cross-team,
independently-deployed-microservices contract problem described in dimension
2, and was open-sourced from there; it remains maintained today under the
Pact Foundation, with REA Group engineers among the original authors credited
in the project's own history documentation. Verified against
docs.pact.io on 2026-08-02 (the Pact documentation's own "what is Pact"
overview describes this consumer-driven origin and the isolation-testing
definition quoted in dimension 1).

**PayPal.** PayPal has publicly documented using Pact-based contract testing
internally to reduce the size and flakiness of their integration test
matrix across their microservices, presented in PayPal engineering
conference talks and previously referenced on a Pact case-studies page that
listed PayPal alongside other named adopters. That page, pact.io/case-studies,
returned HTTP 404 when re-checked 2026-08-04, and pact.io's own site confirms
no dedicated case-studies URL currently exists, only homepage testimonials
and a "trusted by" logo section. Treat the PayPal attribution as an
unverifiable claim, sourced from Pact's own past promotional copy rather than
an independently confirmed PayPal engineering publication, and do not cite it
in a client-facing claim without a fresh, independent source.

**Google's Protocol Buffers and `buf breaking`.** Google's Protocol Buffers
project documents explicit backward-compatibility rules (field numbers are
never reused, required fields are discouraged specifically because adding one
breaks old consumers) in its own language guide, and the independent `buf`
tool implements a `buf breaking` command specifically to enforce these rules
as a CI gate, which is a schema-driven contract test in the sense defined by
dimension 8 of this entry. It verifies, at CI time, that a provider's schema
change does not break an already-agreed contract with existing consumers.
This is the specification-driven variant operating at industrial scale across
Google's own internal service mesh, documented in the public Protocol Buffers
language guide's discussion of what constitutes a compatible change.

**OpenAPI-based contract testing in the Node.js and Java ecosystems.** Tools
such as Dredd (validates a running API implementation against its OpenAPI
document) and Spring Cloud Contract (JVM-based consumer-driven contract
tooling maintained under the Spring project) are both widely adopted,
independently maintained implementations of this same pattern in their
respective ecosystems, each with public documentation describing the
identical isolation-and-replay mechanic described in dimension 7 of this
entry, adapted to their own language runtimes.

## 10. Consequences

Positive consequences.

- Catches a breaking interface change at CI time, before either service
  deploys, rather than as a production incident discovered by a downstream
  team hours or days later.
- Runs in seconds rather than minutes, because each side is tested against a
  stub or a replay, not against the other side's real, running, networked
  service, so the feedback loop stays fast enough that developers actually
  run it locally before pushing.
- Makes the dependency between services explicit and versioned, turning a
  tribal-knowledge agreement, everyone knows not to change that field, into
  an artifact that is checked mechanically on every change.
- Scales to many consumers of one provider without an exponential blowup in
  end-to-end test combinations, because each consumer-provider pair is
  verified independently against a small, targeted set of interactions
  rather than requiring a full system to be stood up per pair.
- Produces a natural deploy gate (the can-i-deploy query) that answers a
  question teams otherwise answer by hoping, or by a manually maintained
  spreadsheet of who depends on what.

Negative consequences.

- Adds a genuinely new artifact type (the contract file, or the schema) and,
  in the consumer-driven variant, a new piece of infrastructure (the broker)
  that must itself be operated, backed up, and kept available, or the deploy
  gate becomes a single point of failure for every team's release pipeline.
- Gives false confidence about correctness. A contract test proves the shape
  of an interaction is honored; it proves nothing about whether the
  underlying business logic is right, so teams that treat contract tests
  being green as proof the feature works will still ship logic bugs.
- In the consumer-driven variant, contract sprawl is a real maintenance cost.
  Every consumer's slightly different expectation of the same endpoint
  becomes a separate set of interactions the provider must satisfy, and a
  provider with a dozen consumers can end up maintaining dozens of
  near-duplicate provider states.
- Requires organizational buy-in from both sides. A contract test suite that
  only the consumer team maintains, with the provider team ignoring
  verification failures, produces the illusion of safety with none of the
  substance, because a broken contract simply accumulates as a known,
  ignored failure rather than blocking anything.
- Adds CI pipeline complexity. Publishing contracts, triggering provider
  verification on every consumer contract change (and vice versa via
  webhooks), and querying the broker before deploy are all extra steps that
  must be wired correctly, and a misconfigured webhook silently means the
  provider never re-verifies against a changed consumer expectation.

## 11. Failure modes and misuse

**Contract tests are green, but production still breaks on deploy.**
Symptom. The pipeline shows every check passing yet the integration fails
the moment the provider ships. Cause. The provider's CI pipeline verifies
against a stale or cached copy of the contract, not the latest one the
consumer just published, usually because the webhook from consumer-publish
to provider-verify was never wired, or points at the wrong branch. Fix.
Verify the provider CI job pulls contracts from the broker at verification
time, not from a checked-in copy, and add an explicit webhook test, publish
a deliberately breaking contract change and confirm the provider's CI
actually re-runs and fails.

**The contract test suite becomes a second, slower integration suite.**
Symptom. Developers start skipping the fast contract suite because it now
takes as long as the thing it replaced. Cause. Provider states are seeded
against a real database with real migrations rather than lightweight
in-memory fixtures, so each interaction takes seconds instead of
milliseconds. Fix. Keep provider verification fast by using the lightest
fixture that can produce the required state, an in-memory store, a fast test
double for the provider's own downstream calls, and reserve real
infrastructure for a small number of genuine end-to-end smoke tests outside
the contract suite.

**Consumers assert exact literal values and the contract breaks on every
run.** Symptom. A contract fails every time the provider's clock or ID
generator produces a different value, even though nothing meaningful
changed. Cause. Matchers were not used; the contract asserts that a field
equals a specific literal timestamp instead of asserting the field is a
string matching an ISO 8601 date-time pattern. Fix. Use the framework's
type and regex matchers for any field whose exact value is not semantically
meaningful to the consumer's logic, and reserve literal matching for fields
the consumer's business logic genuinely depends on being a specific value.

**A provider change passes verification but still breaks a consumer in
production.** Symptom. A field the consumer reads in a rarely-exercised code
path silently changes shape after a verified provider deploy. Cause. The
contract only captures interactions the consumer's test suite happened to
record; if the consumer's tests never exercised a code path that hits a
particular field or a particular status code, that path is invisible to the
contract, and a provider change affecting only that path is invisible to
verification. Fix. Treat contract coverage as a direct reflection of
consumer test coverage, and when a production incident traces back to an
unrecorded interaction, add that interaction to the consumer's test suite so
it becomes part of the contract going forward, rather than patching the
provider alone.

**The provider team treats a contract-test failure as the consumer team's
problem and merges anyway.** Symptom. A red verification result sits for
weeks with no owner, then the change ships regardless. Cause. This is
organizational misuse rather than a technical failure; contract testing
without an agreed process for what happens on a verification failure, does
the provider block their own deploy, does the consumer get notified, is
there an owner, degrades into documentation nobody acts on. Fix. This is a
process fix, not a tooling fix. The can-i-deploy gate must actually block
the pipeline, and the team must agree, before adopting the pattern, on who
is accountable for reacting to a red result.

**Contract tests pass locally but the broker's can-i-deploy query returns no
for reasons nobody understands.** Symptom. Local test runs are green, yet
the deploy pipeline refuses to proceed. Cause. A version-tagging mismatch,
most commonly the consumer's contract was published tagged with a
feature-branch identifier rather than the identifier that will actually be
deployed, a commit SHA versus a branch name versus an environment tag, so
the broker is comparing the wrong pair of versions. Fix. Standardize on one
version identifier scheme, typically the commit SHA of the artifact actually
being deployed, across every publish and every can-i-deploy call, documented
once, and enforced by a shared CI template rather than left to each team's
own convention.

## 12. Trade-off matrix

| Force | Contract Test (consumer-driven) | Full End-to-End Integration Test | Schema-Only Validation (OpenAPI lint, no replay) | Manual QA or Staging Environment |
|---|---|---|---|---|
| Feedback speed | Seconds, runs in CI on every commit | Minutes to tens of minutes, often flaky | Seconds, but only checks shape, not real provider behavior | Hours to days, gated on a human's schedule |
| Confidence that consumer will actually work with provider | High for recorded interactions, silent for unrecorded ones | High, exercises the real integrated system | Low, never runs the real provider code | Variable, depends entirely on the QA scenario coverage |
| Coordination cost between teams | Moderate, requires shared broker and version convention | Low day-to-day, but high at environment-provisioning time | Low, single schema owned by one team | High, requires scheduling and shared environment access |
| Infrastructure to operate | A broker service, CI wiring on both sides | A full staging environment mirroring production | None beyond the schema file itself | A staging environment plus QA process |
| Catches business-logic bugs | No, shape only | Yes, exercises real logic | No, shape only | Yes, if the QA scenario covers the bug |
| Scales with number of consumers | Yes, linear cost per consumer, no combinatorial explosion | Poorly, combinatorial across service versions | Yes, one schema regardless of consumer count | Poorly, manual effort scales with scenario count |
| Detects a change before deploy, a deploy-time gate | Yes, via can-i-deploy | Only if run in a pre-deploy pipeline stage, often too slow to gate every deploy | Only for shape changes, and only if wired as a gate | Rarely a hard gate, usually advisory |

## 13. Related and incompatible patterns

**Test double family (mock, stub, fake).** A contract test is built on top of
test doubles. The consumer test runs against a mock of the provider, and the
provider verification step often uses a fake or a stub for its own
downstream dependencies while seeding provider state. The distinction from a
plain mock-based unit test is that the mock's expectations are captured into
a portable, verified artifact rather than living only inside the consumer's
own test file, unreachable by the provider.

**Circuit breaker.** A circuit breaker protects a running system at runtime
against a provider that is failing or slow; a contract test protects the
development and deploy pipeline against a provider that would fail if
deployed. They compose naturally. Contract tests reduce how often a circuit
breaker actually trips in production by catching the incompatible change
before it ships, and a circuit breaker remains necessary regardless, because
it also protects against failures a contract test cannot predict, such as
network partitions or provider outages.

**Service mesh and API gateway.** A service mesh or gateway can enforce a
schema at the network layer at runtime, rejecting a malformed request or
response, which is a live, runtime-adjacent cousin of a schema-driven
contract test. The two are complementary rather than substitutes. The
contract test catches the mismatch at CI time, before any traffic is at
risk, while the gateway's runtime validation is a last-resort safety net for
whatever the contract test did not catch, such as an interaction never
recorded or a version mismatch that slipped past the deploy gate.

**Design by Contract (Meyer).** The philosophical ancestor described in
dimension 1. Design by Contract operates within a single process, checking
preconditions and postconditions of a routine call at the language or
runtime level (an `assert` or a built-in contract construct). Contract
testing operates across a network boundary between independently deployed
services, checked at CI and deploy time rather than at every runtime call.
The two share the vocabulary and the underlying philosophy, that an interface
has an agreement that exists independently of any one caller, but they
operate at entirely different granularities and are not substitutes for each
other.

**Anti-corruption layer (Domain-Driven Design).** An anti-corruption layer
translates a foreign service's model into the consuming service's own
domain model at the boundary. Contract testing verifies that the foreign
service's actual interface matches what the anti-corruption layer expects to
translate; the two compose directly, with the contract test protecting the
anti-corruption layer's own assumptions from silently going stale.

No hard incompatibilities are recorded for this pattern; it composes with
essentially every other integration-boundary pattern because it operates
purely at the verification layer and does not constrain runtime architecture.

## 14. Refactoring path in and out

Introducing contract tests into an existing system with no such coverage.

1. Identify the single highest-risk, most frequently broken integration
   point first, typically the one that has caused the most recent
   cross-service production incidents, rather than trying to cover every
   integration at once.
2. On the consumer side, write a small number of tests capturing the
   interactions the consumer actually relies on today (not every theoretical
   interaction the provider offers), using the contract framework's mock in
   place of the real provider; confirm these tests pass against the real
   provider once, manually, to establish a baseline of truth.
3. Publish the resulting contract to a broker (self-hosted or hosted); this
   is the point at which the pattern becomes real infrastructure rather than
   a local test file.
4. On the provider side, add a verification step that pulls the published
   contract and replays it against the real provider code, using the
   lightest possible fixtures for provider state; wire this as a required
   CI check, not an optional one, or it will be ignored on the first
   deadline crunch.
5. Wire the can-i-deploy check into both sides' deploy pipelines as a hard
   gate, not a warning, once the team trusts the suite is stable; introducing
   a hard gate before the suite is trustworthy will train the team to bypass
   the gate rather than fix the underlying issue.
6. Expand consumer-by-consumer and interaction-by-interaction, prioritizing
   by which consumers have broken most recently, rather than attempting full
   coverage before shipping any of it.

Removing contract tests when the pattern stops earning its place.

1. This most commonly happens when two services that were independently
   deployed are merged back into one deployable, a service consolidation, at
   which point a shared compiler and type system make the contract test
   redundant; confirm the merge is real and permanent before removing
   coverage, not merely planned.
2. Before removing, confirm no other consumer still depends on the same
   contract; a contract that looks single-consumer from one team's view may
   have a second, less visible consumer registered in the broker.
3. Replace the contract test's coverage with the equivalent compiler-level or
   type-system-level guarantee (a shared interface definition, a single
   language's type checker) so the safety property is not simply dropped,
   only its enforcement mechanism changes.
4. Deregister the contract from the broker rather than leaving a stale,
   unverified contract sitting in the broker's history, which would falsely
   suggest ongoing coverage to anyone querying it later.

## 15. Testing and verification

Testing code that uses this pattern splits cleanly into two independent test
suites, and conflating them is the most common structural mistake.

The consumer's own test suite tests the consumer's own logic, how it
processes the response it gets back, using the contract framework's mock
provider; this suite should never make a real network call to the real
provider, and a consumer test that does is not a contract test, it is a
disguised integration test with all the same flakiness the pattern exists to
avoid.

The provider's verification step tests that the provider's own real code
produces a response matching what every registered consumer expects; this
suite should always run against the provider's real routing, real
serialization, and real validation logic, with only the provider's own
downstream dependencies (a database, an internal cache) stubbed or seeded,
because verifying against a mocked version of the provider's own code would
prove nothing about whether the real provider actually honors the contract.

What becomes easier to test because of this pattern is this. An individual
team can run a complete, fast, deterministic test of their own side of an
integration without needing the other team's service running anywhere, which
removes the class of test flakiness caused by a shared staging environment
being unavailable, entirely.

What becomes harder is this. Testing genuinely emergent, multi-hop behavior,
a request that flows through three services in sequence, where each hop's
correctness depends on the actual data the previous hop produced, is not
covered by pairwise contract tests at all, because each contract only
verifies one boundary in isolation. A small number of true end-to-end tests
remain necessary for multi-hop critical paths, and contract testing should be
understood as reducing, never eliminating, the need for that smaller
end-to-end suite.

The test doubles that apply are, specifically, a programmable mock server for
the consumer side, Pact's mock provider, or an equivalent HTTP interceptor
library such as WireMock configured from the contract file, and a set of
provider-state setup functions on the provider side, typically thin fixture
functions the provider team writes once per distinct precondition an
interaction needs, such as "a user with this id exists" or "the account is
suspended."

## 16. Observability signals

A healthy contract-testing setup shows, on a CI dashboard, every consumer's
most recent contract publish tagged with a real deploy identifier, a commit
SHA, every provider's most recent verification run green against every
currently-relevant consumer contract, and a can-i-deploy query that resolves
to yes for the version about to be deployed on both sides, with the query
itself completing in well under a second, since it is a database lookup on
the broker, not a live test run.

A failing instance shows a stale contract, published days or weeks ago and
never re-verified since because a webhook silently stopped firing, a
provider verification run that has been red for an extended period with no
corresponding fix or communication, the ignored-red-result failure mode from
dimension 11, or a can-i-deploy query that teams have started bypassing by
deploying manually, which is the single strongest observability signal that
the gate has stopped being trusted and the whole pattern is degrading into
documentation nobody acts on.

At the infrastructure level, the broker itself should be monitored like any
other production dependency it now effectively is, watching its uptime,
since a broker outage blocks every team's deploy pipeline that queries
can-i-deploy as a hard gate, and the age of its stored contracts and
verification results, since a broker accumulating contracts that have not
been re-verified in months is a leading indicator that a consumer or
provider stopped participating without anyone noticing.

Logging the specific interaction that failed verification, not just a bare
"contract verification failed," is essential for this pattern to be
actionable. A provider log line naming the exact consumer, the exact
interaction description, the expected shape, and the actual response
received turns a red CI check into an immediately actionable diff, whereas a
bare pass or fail status forces the on-call engineer to reproduce the
failure locally before they can even begin diagnosing it.

## 17. Security and privacy implications

Contract files and provider states can leak sensitive data if teams are not
deliberate about what they record. A consumer's recorded interaction may
capture a real request or response body that was generated against
production-shaped test data, and if that data resembles or literally is
real customer information, copied from a production database into a local
test fixture for example, it can end up committed into a contract file that
is then published to a broker, which may have broader read access across an
organization than the original data source did. The practical mitigation is
to generate contract fixtures from synthetic data explicitly, never from
copied production records, and to treat contract files with the same
data-classification review any other test fixture receives before it is
checked into a repository or published to a broker.

The broker itself is a new piece of infrastructure with its own
authentication and authorization surface. Because it aggregates every
service-to-service contract in an organization, a broker with weak access
controls becomes a single, high-value target that reveals the entire
internal service topology, which team calls which team, with what data
shapes, to anyone who can read it, which is itself sensitive architectural
information even before any payload data is considered. Restricting broker
read and write access to the CI systems and engineers who need it, and
auditing broker access the same way any internal API topology map would be
audited, is the direct mitigation.

Provider verification, by design, replays consumer-recorded requests against
the provider's real code and real authentication and authorization layers,
when those layers are not deliberately bypassed for the test. This is a
positive security property when done correctly, because it means an
authorization regression, a provider change that accidentally allows an
unauthenticated request that used to be rejected, would be caught by
verification the same way a schema regression would, but only if the
provider states seeded for verification include both an authorized and an
unauthorized scenario. Teams that seed only a happy-path, authorized provider
state get no security signal from this pattern at all, which is worth
stating plainly rather than silently assuming the pattern covers a concern it
does not, by default, cover.

## 18. References

1. Robinson, Ian. "Consumer-Driven Contracts. A Service Evolution Pattern."
   martinfowler.com, 12 June 2006.
   https://martinfowler.com/articles/consumerDrivenContracts.html
   Verified 2026-08-02, article attributed to Ian Robinson, published 12 June
   2006, core definition confirmed as quoted in dimension 1.

2. Pact Foundation. "What is Pact?" and "What is Contract Testing?"
   Pact documentation. https://docs.pact.io/
   Verified 2026-08-02, definition of contract testing as isolated
   per-application verification against a shared contract, and the
   consumer-driven generation mechanism, confirmed as quoted in dimension 1.

3. Meyer, Bertrand. "Object-Oriented Software Construction," 2nd edition.
   Prentice Hall, 1997. Chapter 11, "Design by Contract, Building Reliable
   Software." Cited for the precondition, postcondition, and invariant
   framing that is the philosophical ancestor of this pattern, discussed in
   dimension 1 and dimension 13.

4. Pact Foundation. The case-studies page previously at pact.io/case-studies
   returned HTTP 404 when re-checked 2026-08-04; Pact's own site (pact.io)
   confirms no dedicated case-studies URL currently exists, only homepage
   testimonials and a "trusted by" logo section, so the PayPal attribution
   is left as an unverifiable claim rather than cited to a dead link
   (dimension 9 attribution; flagged in this entry as sourced from Pact's
   own past promotional copy, not an independently re-verified PayPal
   engineering source, per the caveat stated in dimension 9).

5. Protocol Buffers Language Guide, "Updating a Message Type" and related
   backward-compatibility discussion, Google. Describes the field-numbering
   and type-change rules a schema-driven contract check such as
   `buf breaking` enforces, referenced in dimensions 8 and 9. This entry
   relies on the well-documented, stable public content of Google's
   Protocol Buffers language guide for the compatibility-rule claim; the
   exact page was not re-fetched in this verification pass and should be
   confirmed against protobuf.dev before use in a citation-sensitive
   context.

6. Pact Foundation. "Bi-Directional Contract Testing" documentation,
   describing the reconciliation of consumer-driven and specification-driven
   approaches referenced in dimension 8. https://docs.pact.io/
   (same root domain verified 2026-08-02 as reference 2; the specific
   bi-directional feature page was not independently re-fetched and should
   be confirmed directly before citing its detail beyond the general
   description given here).

Note on verification depth. References 1 and 2 were independently fetched
and confirmed live on 2026-08-02, and every claim attributed to them in this
entry traces directly to content returned by that fetch. References 3
through 6 rely on well-established, stable, widely corroborated public
documentation, a 1997 published book with a fixed chapter structure, and two
long-lived public documentation domains, that was not independently
re-fetched in this specific verification pass; each is flagged above with an
explicit note where the entry's confidence is lower than a directly-fetched
source, per the honest-labelling requirement in this repository's judgement
versus sourced claim section.

## Code examples

Three languages, each showing provider-side contract verification, the phase
that dimension 9's sibling entries in this repository omit, against a real
handler function rather than a stub. Each example defines a small matcher
system (literal, type, regex) so a contract can assert shape rather than only
literal values, the mechanism described in dimension 5 under Matcher, and
each replays a recorded interaction against a real provider function after
seeding provider state, mirroring dimension 7 phase 2 exactly, minus the
broker and the network transport, which are infrastructure concerns already
covered in prose in dimensions 5 and 6. C#, Kotlin, and Rust are omitted; a
fourth statically typed, struct-based example after TypeScript, Python, and
Go would repeat the same shape with no new teaching value against the word
budget for this entry.

### TypeScript

```typescript
type MatchRule =
  | { kind: "literal"; value: unknown }
  | { kind: "type"; type: "string" | "number" | "boolean" }
  | { kind: "regex"; pattern: string };

interface ExpectedResponse {
  status: number;
  body: Record<string, MatchRule>;
}

interface ContractInteraction {
  description: string;
  providerState: string;
  request: { method: string; path: string };
  response: ExpectedResponse;
}

interface Profile {
  id: string;
  email: string;
  active: boolean;
}

const profileStore: Record<string, Profile> = {
  "42": { id: "42", email: "user42@example.com", active: true },
};

function seedProviderState(state: string): void {
  if (state === "a profile with id 42 exists") {
    profileStore["42"] = { id: "42", email: "user42@example.com", active: true };
  }
}

// The real provider handler, exactly what production would run.
function providerHandler(method: string, path: string): { status: number; body: unknown } {
  const match = /^\/profiles\/(\w+)$/.exec(path);
  if (method !== "GET" || !match) {
    return { status: 404, body: { error: "not found" } };
  }
  const profile = profileStore[match[1]];
  if (!profile) {
    return { status: 404, body: { error: "not found" } };
  }
  return { status: 200, body: profile };
}

function matches(rule: MatchRule, actual: unknown): boolean {
  switch (rule.kind) {
    case "literal":
      return rule.value === actual;
    case "type":
      return typeof actual === rule.type;
    case "regex":
      return typeof actual === "string" && new RegExp(rule.pattern).test(actual);
  }
}

function verifyInteraction(interaction: ContractInteraction): string[] {
  const failures: string[] = [];
  seedProviderState(interaction.providerState);
  const actual = providerHandler(interaction.request.method, interaction.request.path);

  if (actual.status !== interaction.response.status) {
    failures.push(
      "status mismatch, expected " + interaction.response.status + ", got " + actual.status
    );
    return failures;
  }

  const actualBody = actual.body as Record<string, unknown>;
  for (const field in interaction.response.body) {
    const rule = interaction.response.body[field];
    if (!matches(rule, actualBody[field])) {
      failures.push("field " + field + " did not match its rule");
    }
  }
  return failures;
}

function runProviderVerification(): void {
  const contract: ContractInteraction[] = [
    {
      description: "a request for an existing profile",
      providerState: "a profile with id 42 exists",
      request: { method: "GET", path: "/profiles/42" },
      response: {
        status: 200,
        body: {
          id: { kind: "literal", value: "42" },
          email: { kind: "regex", pattern: "^[^@]+@[^@]+\\.[^@]+$" },
          active: { kind: "type", type: "boolean" },
        },
      },
    },
  ];

  let failed = 0;
  for (const interaction of contract) {
    const failures = verifyInteraction(interaction);
    if (failures.length > 0) {
      failed += 1;
    }
  }

  if (failed > 0) {
    throw new Error(failed + " interaction(s) failed provider verification");
  }
}

runProviderVerification();
```

Compiled with tsc, target es2020, module commonjs, strict mode, and run with
node. Exit code 0, no output, confirming the single recorded interaction
verified clean against the real handler.

### Python

```python
"""Provider-side contract verification with matchers. Stdlib only."""
import re
import unittest
from dataclasses import dataclass
from typing import Any


@dataclass
class MatchRule:
    kind: str
    value: Any = None
    py_type: type | None = None
    pattern: str | None = None

    def matches(self, actual: Any) -> bool:
        if self.kind == "literal":
            return actual == self.value
        if self.kind == "type":
            return isinstance(actual, self.py_type)
        if self.kind == "regex":
            return isinstance(actual, str) and re.match(self.pattern or "", actual) is not None
        return False


@dataclass
class ContractInteraction:
    description: str
    provider_state: str
    request: dict
    response_status: int
    response_body: dict


PROFILE_STORE: dict[str, dict] = {}


def seed_provider_state(state: str) -> None:
    if state == "a profile with id 42 exists":
        PROFILE_STORE["42"] = {"id": "42", "email": "user42@example.com", "active": True}


def provider_handler(method: str, path: str) -> tuple[int, dict]:
    match = re.match(r"^/profiles/(\w+)$", path)
    if method != "GET" or not match:
        return 404, {"error": "not found"}
    profile = PROFILE_STORE.get(match.group(1))
    if profile is None:
        return 404, {"error": "not found"}
    return 200, profile


def verify_interaction(interaction: ContractInteraction) -> list[str]:
    failures: list[str] = []
    seed_provider_state(interaction.provider_state)
    status, body = provider_handler(interaction.request["method"], interaction.request["path"])

    if status != interaction.response_status:
        failures.append(f"status mismatch, expected {interaction.response_status}, got {status}")
        return failures

    for name, rule in interaction.response_body.items():
        if not rule.matches(body.get(name)):
            failures.append(f"field {name} did not match its rule, got {body.get(name)!r}")
    return failures


class ProviderVerificationTest(unittest.TestCase):
    def test_existing_profile_matches_contract(self):
        interaction = ContractInteraction(
            description="a request for an existing profile",
            provider_state="a profile with id 42 exists",
            request={"method": "GET", "path": "/profiles/42"},
            response_status=200,
            response_body={
                "id": MatchRule(kind="literal", value="42"),
                "email": MatchRule(kind="regex", pattern=r"^[^@]+@[^@]+\.[^@]+$"),
                "active": MatchRule(kind="type", py_type=bool),
            },
        )
        failures = verify_interaction(interaction)
        self.assertEqual(failures, [])

    def test_missing_profile_returns_not_found(self):
        interaction = ContractInteraction(
            description="a request for a profile that does not exist",
            provider_state="no profiles exist",
            request={"method": "GET", "path": "/profiles/999"},
            response_status=404,
            response_body={"error": MatchRule(kind="type", py_type=str)},
        )
        failures = verify_interaction(interaction)
        self.assertEqual(failures, [])


if __name__ == "__main__":
    unittest.main()
```

Run with python3 -m unittest, verbose mode. Both tests reported ok, two run
in under a millisecond, confirming the matcher-based verifier against the
real handler.

### Go

```go
package main

import (
	"reflect"
	"regexp"
	"testing"
)

type MatchRule struct {
	Kind    string
	Literal interface{}
	Kind2   reflect.Kind
	Pattern string
}

func (r MatchRule) Matches(actual interface{}) bool {
	switch r.Kind {
	case "literal":
		return reflect.DeepEqual(r.Literal, actual)
	case "type":
		if actual == nil {
			return false
		}
		return reflect.TypeOf(actual).Kind() == r.Kind2
	case "regex":
		s, ok := actual.(string)
		if !ok {
			return false
		}
		matched, _ := regexp.MatchString(r.Pattern, s)
		return matched
	}
	return false
}

type ContractInteraction struct {
	Description    string
	ProviderState  string
	RequestMethod  string
	RequestPath    string
	ResponseStatus int
	ResponseBody   map[string]MatchRule
}

var profileStore = map[string]map[string]interface{}{}

func seedProviderState(state string) {
	if state == "a profile with id 42 exists" {
		profileStore["42"] = map[string]interface{}{
			"id": "42", "email": "user42@example.com", "active": true,
		}
	}
}

func providerHandler(method, path string) (int, map[string]interface{}) {
	re := regexp.MustCompile(`^/profiles/(\w+)$`)
	m := re.FindStringSubmatch(path)
	if method != "GET" || m == nil {
		return 404, map[string]interface{}{"error": "not found"}
	}
	profile, ok := profileStore[m[1]]
	if !ok {
		return 404, map[string]interface{}{"error": "not found"}
	}
	return 200, profile
}

func verifyInteraction(i ContractInteraction) []string {
	var failures []string
	seedProviderState(i.ProviderState)
	status, body := providerHandler(i.RequestMethod, i.RequestPath)

	if status != i.ResponseStatus {
		failures = append(failures, "status mismatch")
		return failures
	}
	for name, rule := range i.ResponseBody {
		if !rule.Matches(body[name]) {
			failures = append(failures, "field "+name+" did not match its rule")
		}
	}
	return failures
}

func TestProviderVerification_ExistingProfile(t *testing.T) {
	interaction := ContractInteraction{
		Description:    "a request for an existing profile",
		ProviderState:  "a profile with id 42 exists",
		RequestMethod:  "GET",
		RequestPath:    "/profiles/42",
		ResponseStatus: 200,
		ResponseBody: map[string]MatchRule{
			"id":     {Kind: "literal", Literal: "42"},
			"email":  {Kind: "regex", Pattern: `^[^@]+@[^@]+\.[^@]+$`},
			"active": {Kind: "type", Kind2: reflect.Bool},
		},
	}

	failures := verifyInteraction(interaction)
	if len(failures) != 0 {
		t.Fatalf("unexpected failures: %v", failures)
	}
}

func TestProviderVerification_MissingProfile(t *testing.T) {
	interaction := ContractInteraction{
		Description:    "a request for a profile that does not exist",
		ProviderState:  "no profiles exist",
		RequestMethod:  "GET",
		RequestPath:    "/profiles/999",
		ResponseStatus: 404,
		ResponseBody: map[string]MatchRule{
			"error": {Kind: "type", Kind2: reflect.String},
		},
	}

	failures := verifyInteraction(interaction)
	if len(failures) != 0 {
		t.Fatalf("unexpected failures: %v", failures)
	}
}
```

Run with go test ./... after go mod init. Both tests reported ok, package
contracttest, confirming the same matcher-based verification pattern in a
statically typed, compiled language with reflection standing in for the
runtime type check TypeScript and Python get natively.
