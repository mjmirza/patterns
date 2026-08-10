---
name: Predictable
slug: predictable
family: 04-principles-and-laws
category: Design Principle
aliases: [Predictability, Behavioral Predictability, Deterministic Behavior]
first_described: "Convergent principle with no single coined origin. Earliest formal reification is Bertrand Meyer, Design by Contract, IEEE Computer, October 1992 (contracts as a predictability guarantee); the idempotency reification traces to HTTP method semantics formalized in RFC 2616, 1999, later RFC 7231, 2014"
maturity: canonical
related: [principle-of-least-astonishment, fail-fast, single-source-of-truth, liskov-substitution-principle, postel-law, idempotent-consumer, state, command]
incompatible_with: []
verified: 2026-08-02
---

# Predictable

## 1. Name, aliases, and lineage

Predictable, or Predictability, names a quality a piece of software can have.
it is not a single technique with one inventor and one publication date, and
this entry says so plainly rather than manufacturing an origin story. What
counts as the property is this. given a stated contract and a fixed set of
inputs and environmental conditions, the behavior of the system can be
forecast in advance, by a reader who has never run it, and that forecast
holds every time the same conditions recur. The word appears constantly in
software engineering prose as an adjective, "a predictable API", "predictable
performance", "predictable failure modes", long before it appears anywhere as
a named principle with a citation of its own. This entry treats it as a
convergent principle. several independent lines of engineering practice
arrived at the same underlying demand from different directions, and each
line left its own citable formalization behind.

The oldest of these formalizations is Design by Contract, introduced by
Bertrand Meyer as part of the Eiffel programming language and given its
canonical statement in Bertrand Meyer, "Applying 'Design by Contract'", IEEE
Computer, vol. 25, no. 10, October 1992, pages 40 to 51, DOI
10.1109/2.161279 (verified 2026-08-02 via the ACM Digital Library abstract
record at https://dl.acm.org/doi/10.1109/2.161279). Meyer's proposal was that
a routine states, in a form the compiler and the reader can both check, what
it requires of its caller before it runs, a precondition, and what it
guarantees to the caller once it finishes, a postcondition, together with an
invariant the enclosing object holds between calls. A caller who reads the
contract can forecast the routine's behavior without reading its
implementation. that forecastability is exactly the property this entry is
named for, stated as an engineering discipline rather than left as a loose
expectation.

A second, independent formalization comes from network protocol design. The
HTTP specification defines a subset of its methods as idempotent, meaning a
request repeated any number of times has the same effect on server state as
sending it once. This guarantee is what lets a client forecast the outcome
of a retry without knowing whether an earlier attempt actually reached the
server. The definition is stated precisely in RFC 7231, section 4.2.2, June
2014 (R. Fielding and J. Reschke, editors, Internet Engineering Task Force,
https://datatracker.ietf.org/doc/html/rfc7231#section-4.2.2, verified
2026-08-02). "A request method is considered 'idempotent' if the intended
effect on the server of multiple identical requests with that method is the
same as the effect for a single such request", and the specification names
PUT, DELETE, and the safe methods as idempotent by definition. The earlier
RFC 2616 from 1999 carried the same guarantee in less formal language, which
is why this entry credits the concept to the protocol tradition rather than
to the 2014 document alone.

A third, more recent strand names the property directly at the level of a
build artifact rather than at the level of a single call. the Reproducible
Builds project states its goal as a build being reproducible "if given the
same source code, build environment and build instructions, any party can
recreate bit-by-bit identical copies of all specified artifacts" (Reproducible
Builds project, "Definition", https://reproducible-builds.org/docs/definition/,
verified 2026-08-02). This framing generalizes the idea past a single
function call to an entire compilation and packaging pipeline, and it is the
strand most directly concerned with a stranger, someone who was never in the
room, being able to verify the forecast independently.

A fourth strand is declarative infrastructure. Kubernetes describes every
object it manages as carrying a `spec`, the desired state a person declared,
and a `status`, the actual observed state, with a control loop whose entire
job is reconciling the second toward the first. "The Kubernetes control plane
continually and actively manages every object's actual state to match the
desired state you supplied" (Kubernetes documentation, "Understanding
Kubernetes Objects", https://kubernetes.io/docs/concepts/overview/working-with-objects/,
verified 2026-08-02). The predictability claim here is different in shape
from the other three. it is not "the same call always does the same thing",
it is "the system always converges to the same declared shape, regardless of
the path it took to get there or what perturbed it along the way".

None of these four strands cites the others as an ancestor. They are treated
here as one principle because they share the same test. can a reader, who
knows the contract and the inputs but has not watched the system run, state
in advance what will happen, and will that statement still be true on the
next run, on someone else's machine, a year from now. Aliases in common use
include Predictability, the noun form used interchangeably with the
adjective in most engineering writing, Deterministic Behavior, which is used
more narrowly for the specific case of identical execution given identical
inputs (see the non-applicability note in dimension 4 for where determinism
and predictability part ways), and Behavioral Predictability, used in some
API design literature to distinguish it from the schedule-and-cost sense of
"predictable" used in project management, which this entry does not cover.

This entry is a close relative of, and is easy to confuse with, the
[Principle of Least Astonishment](principle-of-least-astonishment.md), and
the difference is worth stating precisely rather than left implicit. Least
astonishment is a claim about matching an observer's prior mental model, and
Yukihiro Matsumoto's own clarification of the phrase, that it means "least
MY surprise" once the observer already knows the system, makes clear the
standard is inherently relative to who is looking and what they already
know. Predictability, as formalized in contracts, idempotency, reproducible
builds, and reconciliation loops, makes no reference to any observer's prior
knowledge at all. it is a claim that the forecast is derivable from the
stated contract alone, true for a first-time reader exactly as much as for a
veteran. A system can therefore be highly predictable and still astonish a
newcomer who has not read the contract, and a system can match every
convention a community expects and still be unpredictable at the level of a
single call, if that call touches an unpinned clock, an unseeded random
source, or hidden mutable state. The two principles reinforce each other in
practice far more often than they diverge, but they are not the same claim
and a reader should not treat this entry as a restatement of the other.

## 2. Problem and context

A caller who invokes an operation, reads an API's documentation, or pulls a
dependency's published version needs to know, before acting, what is going
to happen. When that forecast cannot be made reliably, the caller is forced
into defensive strategies that cost real engineering time and introduce
their own new failure modes. Four concrete situations make the problem
tangible.

A payment request times out. The client does not know whether the charge
went through before the connection dropped. Without a guarantee that
resending the exact same request is safe, the client faces two bad choices
only. Resend and risk charging the customer twice, or do not resend and risk
never completing a legitimate purchase, with a human support ticket the only
way to resolve the ambiguity afterward. This is the everyday shape of the
idempotency strand from dimension 1, and Stripe's own documentation
describes the exact mechanism built to close this gap. "The API supports
idempotency for safely retrying requests without accidentally performing the
same operation twice" (Stripe, "Idempotent requests",
https://docs.stripe.com/api/idempotent_requests, verified 2026-08-02).

A production incident is traced to a specific build artifact, and an
engineer wants to reproduce the exact binary that is running in production
on their own machine to attach a debugger. If the build pipeline embeds a
build timestamp, pulls whichever version of a system library happens to be
installed on the build server that day, or is influenced by the build
machine's locale or file ordering, the artifact the engineer produces
locally is not provably the same artifact running in production, and the
debugging session starts from a position of doubt about whether the bug is
even present in what was just rebuilt.

A test suite reports a failure on a pull request, and rerunning the exact
same commit ten minutes later reports success with no code change in
between. The team now has to decide, for every future red build, whether it
represents a real regression or another instance of the same flake, and
every wrong guess either blocks a legitimate merge or lets a real bug
through. The failure is not that a test failed. it is that the test's
outcome could not be forecast from the code under test, because it silently
depended on something else, wall clock time, thread scheduling order, an
unseeded random number generator, or state left behind by a previous test.

A team ships what they believe is a minor patch release of a library. A
downstream consumer's build breaks the same day, because the "patch" quietly
changed a function's return type. The consumer had relied on the version
number to forecast, without reading the diff, whether the update was safe to
pull automatically, and the forecast was wrong because the publisher did not
honor the contract the version scheme promises.

In every one of these four situations, the underlying problem is identical
in shape even though the domain differs. someone had to act on a forecast
about a system's behavior, the forecast was not backed by an honored
contract, and the gap between the forecast and reality produced real cost,
a duplicate charge, a wasted debugging session, a blocked merge, a broken
downstream build. The context in which this principle matters is any
boundary where one party acts on a claim about another party's future
behavior without being able to observe that behavior directly at the moment
of acting. an API caller acting on documentation, a build consumer acting on
a checksum, a downstream dependency acting on a version number, an on-call
engineer acting on a runbook.

## 3. Forces

Predictability is not free, and stating the tension honestly is more useful
than presenting the principle as a pure good with no cost, which is
engineering judgment rather than a sourced claim from this point through the
end of this dimension.

Predictability versus leniency in what a system accepts. A strict, narrowly
defined contract is the easiest kind to make predictable, because there are
fewer input shapes to reason about and fewer paths through the
implementation. But a system that rejects anything slightly malformed is
also more brittle in the face of a caller who sends a slightly unexpected
but harmless variant, and the broader engineering community has long debated
where to draw this line. This entry is directly adjacent to
[Postel's Law](postel-law.md), which recommends being liberal in what a
system accepts, and the honest framing of that adjacency is that leniency
and predictability pull in opposite directions at the margin. the more a
system silently accepts and normalizes, the harder it becomes for a caller
to forecast exactly which of several plausible interpretations the system
will apply to a borderline input. A predictable system tends toward strict,
narrow, and rejecting rather than lenient, guessing, and accepting, and that
trade-off is a design decision each system has to make deliberately rather
than by default.

Predictability versus flexibility of dispatch. Dynamic dispatch,
reflection, and runtime configuration all let a system adapt its behavior to
context, which is often exactly what a caller wants, but every one of those
mechanisms makes the caller's forecast conditional on facts the caller may
not have, which subtype was actually instantiated, which configuration flag
was set, which plugin was loaded. [Liskov Substitution](liskov-substitution-principle.md)
is the classical answer to keeping dispatch flexible while keeping the
forecast intact. a caller working against a base type can still forecast
behavior as long as every subtype honors the base type's contract, which is
a narrower and more disciplined form of flexibility than dispatch with no
constraint at all.

Predictability versus performance through caching and memoization. Caching
a result and returning it on a later call with different, but supposedly
equivalent, inputs is a common performance technique, and it is safe exactly
to the extent that the equivalence the cache assumes is actually true.
Introducing a cache into a previously uncached path is a common way to
accidentally introduce unpredictability, because the second call now depends
on whether the first call happened to run first and whether the cache key
correctly captured every input the result actually depended on.

Predictability versus deliberate randomness for security and load
distribution. Some behavior is deliberately and correctly unpredictable, and
forcing it to be predictable is itself the defect, not the fix. A
cryptographic nonce, a session token, and a load balancer's jitter before a
retry all depend on an observer, specifically an adversary or a competing
client, being unable to forecast the next value. This is covered explicitly
in dimension 4's non-applicability list and again in dimension 17, because
it is the single most common place engineers wrongly try to apply this
principle where it actively works against the goal.

Predictability versus the cost of pinning an environment. Every technique in
dimension 8, a hermetic build toolchain, a virtual clock, a fixed random
seed, an idempotency key store, costs engineering effort to build and
operating cost to run. A team has to judge, honestly, whether the blast
radius of an unpredictable failure in a given component justifies that
ongoing cost, and a system with no external consumers, no financial
consequence to a duplicate action, and no supply-chain trust requirement may
reasonably choose not to pay it.

## 4. Applicability and non-applicability

Reach for deliberate predictability engineering when any of the following
hold.

A caller may retry a request without knowing whether the first attempt
succeeded, and repeating the effect would cause real harm, a duplicate
charge, a duplicate shipment, a duplicate email. This is the idempotency
case from dimension 1 and 9.

A build artifact needs to be independently verifiable by a party who did not
run the build, for supply-chain trust, regulatory audit, or the ability to
attach a debugger to the exact binary a bug report describes.

A public interface, API, or package version is consumed by code the
publisher does not control, and the consumer needs to forecast compatibility
without reading every line of the change.

A test needs to fail the same way every time a real regression is present,
and pass the same way every time it is not, so that a red build can be
trusted as a genuine signal rather than triaged as noise.

A safety-critical or real-time system has a hard requirement on worst-case
behavior, where an occasional unpredictable delay or an occasional
unpredictable output is itself the failure, independent of the average case.

A state machine, workflow, or orchestration has states where certain
transitions must never silently occur, a shipped order reverting to pending,
a completed payment reopening, and the cost of an illegal transition
happening even once outweighs the cost of rejecting a caller's mistaken
request.

Do not reach for this principle, or actively design against it, in the
following situations.

Generative and creative systems where variation across identical inputs is
the entire point. a text-to-image model, a procedural level generator, or an
LLM sampling from a probability distribution with temperature above zero is
supposed to produce a different plausible output on repeated calls, and
forcing determinism onto the sampling step defeats the reason the system
exists. Determinism in the underlying arithmetic can still be desirable for
debugging, but the product-level output is deliberately not predictable and
should not be described as broken for behaving that way.

Cryptographic key generation, nonces, session tokens, and CSRF tokens, where
predictability by an adversary is the vulnerability, not a missing feature.
See dimension 17 for the specific attack shapes this produces.

Load distribution and backoff jitter, where deliberately randomizing the
exact retry timing across many clients is what prevents a thundering herd
from all retrying in lockstep and re-creating the outage they are trying to
recover from. A predictable, fixed backoff interval is worse here, not
better.

A/B testing and randomized experimentation, where the entire mechanism
depends on assignment to a variant being unpredictable to the person running
the experiment and to the participant, so that the comparison between
variants is not biased by anyone's expectation.

Genuinely exploratory or throwaway code with no external consumer and no
consequence to a re-run producing a different result, where the cost of
pinning a clock, a random seed, and a hermetic build environment is real
engineering time spent buying a guarantee nobody downstream needs yet. This
is a judgment call about scope, not a permanent exemption, since exploratory
code has a habit of quietly becoming load-bearing.

## 5. Structure

A predictable system, in any of its concrete forms, is built from the same
five participants, though a given implementation may name them differently
or fold two into one component.

The Contract is the stated, checkable description of what the system
guarantees. a precondition and postcondition pair in Design by Contract, an
idempotency guarantee in an HTTP method definition, a bit-for-bit
reproducibility promise for a build, a compatibility promise encoded in a
semantic version number, or a declared desired state in a reconciliation
loop. The contract is what makes a forecast possible in the first place, and
a system with behavior but no stated contract cannot meaningfully be called
predictable or unpredictable, only unspecified.

The Producer is the component whose behavior the contract binds. a function,
a service endpoint, a build pipeline, a controller's reconcile loop. The
producer is responsible for honoring the contract given any input the
contract admits, and for rejecting, rather than silently accepting, any
input the contract does not admit.

The Consumer is the party that acts on the forecast the contract makes
possible, without directly observing the producer's internal execution. a
client retrying a request, a downstream package pulling a dependency
version, an operator relying on a runbook, a debugger attaching to a
rebuilt artifact.

The Determinism Boundary is the explicit isolation of every source of
non-determinism the producer would otherwise depend on silently. wall-clock
reads, random number generation, network timing, file system ordering,
floating-point rounding mode, thread and goroutine scheduling order, and any
ambient global mutable state. A predictable producer either eliminates these
sources or pushes them behind an explicit, injectable interface, a Clock, a
seeded random source, a pinned toolchain, so the same logical inputs
genuinely produce the same logical outputs.

The Verifier is the mechanism that confirms, independently of the producer's
own claim, that the contract actually held. a test asserting a retried call
returns the same result as the original, a checksum comparison across
independently produced build artifacts, a reconcile loop's own status field
reporting convergence, a contract test run against a dependency before it is
promoted. Without a verifier, a contract is a promise with no enforcement,
and the difference between an honored contract and an aspirational one is
precisely whether a verifier exists and runs.

## 6. ASCII structure diagram

```
                    +----------------------+
                    |       Contract        |
                    | (pre/post, idempotent,|
                    |  reproducible, semver)|
                    +-----------+----------+
                                |
                     binds behavior of
                                |
                                v
+-----------+          +----------------+          +-----------+
|  Consumer |--calls-->|    Producer     |--emits-->|  Verifier |
| (client,  |          | (function,      |          | (test,    |
|  package  |          |  endpoint,      |          |  checksum |
|  dependent|          |  build pipeline,|          |  compare, |
|  operator)|<--result-|  reconcile loop)|<--claim---|  status)  |
+-----------+          +--------+-------+          +-----------+
                                |
                     isolates behind
                                |
                                v
                    +----------------------+
                    | Determinism Boundary  |
                    | clock, RNG, toolchain,|
                    | scheduling, env vars  |
                    +----------------------+
```

## 7. Dynamics

The dynamics differ by which of the four strands from dimension 1 is
operating, and this section walks through the two most common shapes, an
idempotent retry and a reproducible build verification, because they cover
the request-level and the artifact-level case respectively.

```
Idempotent retry, request-level predictability

Consumer                 Producer                 Idempotency Store
   |                         |                            |
   | request(key=K, body=B)  |                            |
   |------------------------>|                            |
   |                         | lookup(K)                  |
   |                         |--------------------------->|
   |                         |          miss              |
   |                         |<---------------------------|
   |                         | execute effect, produce R  |
   |                         | store(K -> R)               |
   |                         |--------------------------->|
   |         R (created)     |                            |
   |<------------------------|                            |
   |                         |                            |
   |  connection drops before Consumer receives R           |
   |                         |                            |
   | request(key=K, body=B)  |   (Consumer retries, unsure if first landed)
   |------------------------>|                            |
   |                         | lookup(K)                  |
   |                         |--------------------------->|
   |                         |           hit: R           |
   |                         |<---------------------------|
   |                         | do not re-execute effect   |
   |         R (replayed)    |                            |
   |<------------------------|                            |
```

The point of this sequence is that the second arrow into the Producer does
not, and must not, trigger the underlying effect a second time. the
Producer's forecastable behavior is "given key K, the effect happens at most
once, and every request carrying K receives the same result", regardless of
how many times the Consumer, uncertain about network delivery, chooses to
send it.

```
Reproducible build verification, artifact-level predictability

Source + Environment Spec         Independent Builder A     Independent Builder B
          |                                |                          |
          |------ same commit, same -------|                          |
          |         toolchain pin          |                          |
          |------------------------------------------------------------>|
          |                                |                          |
          |                          build()                     build()
          |                                |                          |
          |                          artifact A                 artifact B
          |                                |                          |
          |                          hash(A) ----------- compare ----- hash(B)
          |                                |                |          |
          |                                v                v          |
          |                         match: build is reproducible      |
          |                     mismatch: build is NOT predictable,   |
          |                        something outside the source       |
          |                        or the pinned spec leaked in       |
```

This second sequence has no Consumer waiting on a live response. the
forecast being checked is "anyone, at any later time, who repeats the exact
same inputs will get the exact same artifact", and the verifier here is a
third party who was never involved in the original build at all, which is
the property the Debian project's public reproducibility statistics exist
to demonstrate at scale (see dimension 9).

## 8. Implementation variants

Idempotency keys. A client generates a unique key, typically a random
string with enough entropy to avoid collisions, and attaches it to a
state-changing request. The server persists the key alongside the response
it produced the first time it saw that key, and any later request carrying
the same key returns the stored response without re-executing the
underlying effect. Stripe's own guidance recommends V4 UUIDs and explicitly
warns against deriving the key from sensitive data such as an email address,
because the key itself becomes a lookup token an attacker could otherwise
exploit (Stripe, "Idempotent requests",
https://docs.stripe.com/api/idempotent_requests, verified 2026-08-02, see
also dimension 17 below).

Design by Contract assertions. A routine states its precondition, the
condition its caller must satisfy, and its postcondition, the condition it
guarantees on return, as executable checks rather than as comments. A
violated precondition is a defect in the caller. a violated postcondition is
a defect in the routine itself. This distinction is the mechanism that keeps
the contract enforceable rather than aspirational, and it is the oldest of
the four formalizations in dimension 1.

Deterministic simulation testing. A distributed system's entire cluster is
run inside a single simulated process, with the wall clock, the network, and
every source of scheduling non-determinism replaced by a controlled,
deterministic random source. FoundationDB's own documentation states that
this determinism allows perfect repeatability of a simulated run, which in
turn lets engineers run controlled experiments to home in on an issue
(FoundationDB documentation, "Testing FoundationDB",
https://apple.github.io/foundationdb/testing.html, verified 2026-08-02). A
failing run can be replayed exactly, with the same seed, as many times as
needed to diagnose it, which is not possible against a live cluster whose
network timing differs on every real run.

Hermetic and reproducible build pipelines. The build is denied access to
anything not explicitly declared as an input, no ambient network calls
during compilation, no reliance on whatever compiler version happens to be
installed on the machine, no embedded build timestamps that vary run to run,
and every dependency is pinned to an exact, content-addressed version. The
Reproducible Builds project's definition, quoted in dimension 1, is the
formal statement of what this variant is trying to guarantee, and it is
achieved by removing every input the build result could otherwise depend on
besides the declared source and the declared toolchain.

Declarative desired-state reconciliation. Instead of issuing imperative
commands that must each individually succeed in sequence, the caller states
the desired end state, and a control loop continuously and idempotently
drives the actual state toward it, correcting any drift regardless of its
cause. Kubernetes' object model, with its `spec` and `status` fields and the
control plane's continuous reconciliation, is the reference implementation
of this variant (see the citation in dimension 1). The predictability
guarantee here is not "the same command always does the same thing", it is
"the system always converges to the same declared shape from any starting
point", which is a different and in some ways stronger claim than the
call-level idempotency variant above.

Semantic versioning as a published compatibility contract. A version number
of the shape MAJOR.MINOR.PATCH encodes a promise a consumer can act on
without reading the changelog. patch increments never break compatibility,
minor increments add functionality without breaking it, and major increments
may break it. "In the world of software management there exists a dreaded
place called 'dependency hell'", and the specification exists specifically
to let a consumer forecast the safety of an automatic upgrade from the
version number alone (Semantic Versioning 2.0.0, https://semver.org/,
created by Tom Preston-Werner, verified 2026-08-02).

Pure functions and referential transparency. A function whose output depends
only on its explicit arguments, with no read of external mutable state and
no observable side effect, is predictable by construction, because there is
nothing left for the forecast to depend on besides the arguments the caller
already has in hand. This variant is the functional-programming reification
of the same underlying demand, and it composes cleanly with Design by
Contract, since a pure function's postcondition can be stated purely in
terms of its inputs with no reference to ambient state.

Explicit state machines with a closed transition table. Rather than letting
any code anywhere mutate a status field to any value, every legal transition
is enumerated in one place, and any transition not in the table is rejected
rather than silently allowed. This turns "what can happen to this object
next" into a question answerable by reading one table, instead of a question
answerable only by reading every piece of code that might touch the object.

## 9. Known production uses

The Debian project mandates reproducible builds for its package archive
beginning with the Debian 14 "Forky" release, and reports that for common
architectures such as amd64 and arm64, over 97 percent of packages in that
archive already build to bit-for-bit identical results across independent
builders (Debian Wiki, "ReproducibleBuilds/About",
https://wiki.debian.org/ReproducibleBuilds/About, verified 2026-08-02). This
is the largest publicly measured instance of the reproducible build variant
from dimension 8, and it exists specifically so that no single build server
has to be trusted. anyone can rebuild a package and confirm the result
matches what Debian ships.

Stripe's payment API accepts an `Idempotency-Key` header on state-changing
requests and guarantees that a request repeated with the same key, within a
24 hour retention window, returns the identical stored result rather than
executing the underlying charge, refund, or customer creation a second time
(Stripe, "Idempotent requests", https://docs.stripe.com/api/idempotent_requests,
verified 2026-08-02). This is the direct production instance of the
idempotency-key variant, applied specifically to the case where a duplicate
effect has real financial cost.

FoundationDB is developed and tested primarily against a deterministic
simulation of its own distributed protocol rather than against real
clusters for the bulk of its correctness testing, and the project's own
documentation credits this approach with enabling the discovery of subtle
distributed-systems bugs before they would otherwise surface in production
(FoundationDB documentation, "Testing FoundationDB",
https://apple.github.io/foundationdb/testing.html, verified 2026-08-02).

Kubernetes' entire object model is built on the declarative desired-state
and reconciliation variant from dimension 8, applied at the scale of running
container orchestration for a large share of production cloud workloads
across the industry. every Deployment, StatefulSet, and Service a cluster
operator creates is reconciled continuously by a control loop toward the
declared spec (Kubernetes documentation, "Understanding Kubernetes Objects",
https://kubernetes.io/docs/concepts/overview/working-with-objects/, verified
2026-08-02).

The HTTP method semantics defined in RFC 7231 underlie the retry behavior of
essentially every HTTP client library and load balancer in production use,
since a client or a proxy is only safe to automatically retry a request
without asking a human when the method it is retrying is documented as
idempotent (RFC 7231, section 4.2.2, https://datatracker.ietf.org/doc/html/rfc7231#section-4.2.2,
verified 2026-08-02).

The npm package ecosystem, and the broader JavaScript and Node.js tooling
built on top of it, adopts Semantic Versioning 2.0.0 as its default
compatibility contract, encoding into every published version number a
forecast a downstream package's dependency resolver can act on without
inspecting the code (Semantic Versioning 2.0.0, https://semver.org/, verified
2026-08-02).

Erlang and its OTP framework implement supervision trees, where a supervisor
process monitors a set of worker processes and restarts a failed worker back
into a known-good starting state rather than attempting to preserve or guess
at whatever corrupted state caused the failure. "Supervisors are processes
that monitor workers. A supervisor can restart a worker if something goes
wrong" (Erlang and OTP documentation, "Design Principles",
https://www.erlang.org/doc/system/design_principles.html, verified
2026-08-02). The predictability this buys is at the level of recovery
behavior. after any failure, the operator can forecast exactly what state
the system returns to, rather than having to reason about an unbounded
number of partially corrupted intermediate states.

## 10. Consequences

Positive consequences. Retries become safe to automate, because a caller no
longer has to guess whether repeating an action is harmless, which removes
an entire class of manual intervention from operational runbooks. Builds and
releases become independently verifiable, which is a direct supply-chain
security control rather than only a convenience, since a third party can
confirm that what is running in production matches what the published
source claims to produce. Debugging becomes tractable, because a failure
that can be forecast from a fixed set of conditions can also be reproduced
from those same conditions, turning a one-off production mystery into a
repeatable local test case. Onboarding and code review become cheaper,
because a reader can reason about a contract's guarantees without simulating
the implementation in their head, which is the same benefit Design by
Contract was built to provide. Automated testing becomes trustworthy, since
a red build reliably signals a real regression rather than requiring a human
to first triage whether it is "just flaky".

Negative consequences. Every determinism boundary in dimension 5 costs
engineering effort to build, an injectable clock and random source, a
hermetic build toolchain, an idempotency key store with its own retention
and cleanup policy, and it costs ongoing operating effort to keep pinned as
the surrounding ecosystem changes underneath it. Pursuing predictability
past the point a component genuinely needs it removes flexibility a system
might have legitimately benefited from, an adaptive cache, a randomized load
balancing strategy, a dynamically dispatched extension point, and a team
that treats predictability as an unconditional good rather than a
situational trade-off will pay this cost without the matching benefit.
Predictability at the level of one component's contract does not, by
itself, guarantee predictability of the system the component sits inside,
and a false sense of safety follows from believing it does. a state machine
with a closed transition table is still only as predictable as the caller
who is supposed to route every state change through it, and a single
bypassing code path anywhere in the system reintroduces exactly the
unpredictability the table was meant to prevent.

## 11. Failure modes and misuse

A customer is charged twice for the same order after their client retried a
timed-out request. The observable symptom is a duplicate line item in a
payment ledger with no corresponding duplicate order from the customer's own
action. The cause is a state-changing endpoint with no idempotency key at
all, or a key derived from a value that changes between the original request
and the retry, such as the current timestamp, which defeats deduplication
even though a key is technically present. The fix is a client-generated,
stable idempotency key attached to the original request and every retry of
it, checked against a server-side store before the underlying effect
executes, exactly as described in dimension 8 and 9.

A build that passes every local test fails or behaves differently once
deployed, and rebuilding the exact same commit on a different machine
produces a binary with a different hash. The observable symptom is
"works on my machine" escalated to a production incident that a developer
cannot reproduce locally even from the identical source commit. The cause is
an unpinned build input, an implicit dependency on whatever compiler or
system library version is installed on the build machine, an embedded wall
clock timestamp, or a build step that reaches out to the network and can
silently receive a different artifact version on different days. The fix is
a hermetic build pipeline with every toolchain component and dependency
pinned to an exact, content-addressed version, and no network access during
the build step itself.

A test suite reports a failure on one run and a pass on an identical rerun,
with no code change between them. The observable symptom is a red build that
the team learns, over time, to distrust and re-run rather than investigate,
which is dangerous precisely because it trains people to ignore a signal
that is sometimes real. The cause is almost always a hidden dependency on
something outside the test's declared inputs, an unseeded random number
generator, a read of the real wall clock instead of an injected one, shared
mutable state left behind by a previous test in the same process, or
undefined ordering in concurrent code the test exercises. The fix is to
inject every one of those sources explicitly, a fixed seed, a virtual clock,
isolated per-test state, and where concurrency itself is the thing under
test, a deterministic simulation rig of the kind described in dimension
8 rather than hoping a race condition happens to manifest the same way twice
on a shared CI runner.

A declarative controller enters a reconcile loop that never settles, making
continuous corrections instead of converging and going quiet. The observable
symptom is a steady stream of reconcile events in the controller's logs long
after the desired state was declared, with no external change that should
still be triggering new work. The cause is typically an out-of-band actor
mutating the actual state outside the declarative system's control, an
operator manually editing a resource the controller also manages, which
creates a tug of war the controller loses on every pass because its
correction is immediately undone. The fix is a single source of truth for
the desired state, enforced by an admission control mechanism that rejects
or reverts out-of-band edits, rather than allowing two different paths to
mutate the same state.

An engineer tries to reproduce a production incident locally from the same
inputs described in the bug report, and it will not reproduce, no matter how
many times they retry. The observable symptom is an incident marked "cannot
reproduce" and closed without a confirmed fix, which is a genuine cost since
the underlying bug is still present and will recur. The cause is that the
production execution path depended on a source of non-determinism that was
never logged or captured at the time of the incident, an unrecorded thread
interleaving, an unrecorded random seed, real network timing that cannot be
replayed exactly. The fix, where the system's criticality justifies the
investment, is a deterministic simulation or record-replay rig that logs
enough about the non-deterministic inputs at the moment of failure to
reconstruct the exact run later, the same technique FoundationDB uses
proactively rather than only after an incident.

A downstream package pulls what its dependency manager treats as a safe
automatic update, because the version number only incremented at the patch
level, and the consumer's build breaks the same day. The observable symptom
is a build failure or a runtime type error in code the consuming team did
not touch, immediately following an automated dependency update with no
other change in between. The cause is the publisher shipping a change that
actually breaks compatibility, a changed function signature, a removed
export, a changed default value, while incrementing only the patch version,
which violates the semantic versioning contract the consumer's tooling was
trusting. The fix is enforcing the versioning contract with an automated API
compatibility check in the publisher's own release pipeline, so a breaking
change cannot ship under a patch-level version number in the first place.

## 12. Trade-off matrix

The comparison below weighs Predictable design against three named
alternatives it is most often traded against in practice, using the forces
named in dimension 3. This table reflects engineering judgment about typical
outcomes, not a universal ranking, since the right choice depends on the
specific system.

| Force | Predictable (strict contract, pinned determinism) | Postel's Law leniency | Dynamic dispatch / reflection | Randomized jitter / caching heuristics |
|---|---|---|---|---|
| Caller's forecast confidence | High, forecast follows directly from a stated, checked contract | Lower, the exact normalization applied to a borderline input is often undocumented | Conditional, forecast depends on runtime facts the caller may not have | Low by design, the entire point is to avoid a forecastable, exploitable pattern |
| Coupling to implementation | Low, caller depends only on the contract, not the internals | Low to moderate, caller may come to depend on undocumented lenient behavior | Moderate, caller is coupled to the base contract every subtype must honor | Low, caller should not depend on the specific randomized choice made |
| Consistency across environments | High, same inputs plus pinned environment gives the same output everywhere | Moderate, lenient normalization can differ subtly across implementations | High if every subtype genuinely honors the contract, low if one does not | Not applicable, variation across runs is the intended behavior |
| Operability and debugging | Strong, failures reproduce from the same stated inputs | Weaker, silently accepted malformed input can surface as a mystery much later | Moderate, depends on how disciplined the subtype hierarchy is | Weaker for the randomized component specifically, though often isolated on purpose |
| Cost to build and maintain | Higher, requires explicit determinism boundaries and contract enforcement | Lower up front, higher long-term as undocumented lenient behavior accretes | Moderate, ordinary object-oriented design cost | Lower, often the default behavior of an off-the-shelf cache or scheduler |
| Flexibility for legitimate variation | Lower, a strict contract can reject a caller with a legitimate but unanticipated need | Higher, accommodates more input shapes without a contract change | Higher, new behavior can be added via a new subtype without touching callers | Highest, by design accommodates variation the contract never has to name |

See [Postel's Law](postel-law.md) for the full sourced treatment of the
leniency alternative referenced in this table.

## 13. Related and incompatible patterns

[Principle of Least Astonishment](principle-of-least-astonishment.md) is the
principle most often mistaken for a restatement of this one, and dimension 1
above states the distinction directly. least astonishment is relative to an
observer's prior expectations, predictability is a claim about a stated
contract holding regardless of the observer. In practice the two compose
well, since a system that is both predictable and matches community
convention is the easiest of all to reason about, but a system can satisfy
either one without the other.

[Fail Fast](fail-fast.md) is a close and largely reinforcing relationship.
part of what makes a system predictable is that its failure behavior is
itself forecastable, and a system that fails immediately and loudly on a
contract violation, rather than continuing silently with corrupted state, is
easier to forecast than one whose failures are delayed and diffuse. The
precondition checks described in dimension 8 are a direct instance of
failing fast at a contract boundary.

[Liskov Substitution](liskov-substitution-principle.md) is the mechanism
that lets predictability survive the introduction of dynamic dispatch and
subtyping, which is otherwise one of the forces working against it, as
described in dimension 3. a caller working against a base type can still
forecast behavior across every subtype exactly because Liskov's substitution
rule requires every subtype to honor the base type's contract without
weakening it.

[Single Source of Truth](single-source-of-truth.md) underlies the
reconciliation variant from dimension 8 and directly addresses the reconcile
loop failure mode described in dimension 11. a reconciliation loop can only
converge predictably if the desired state it is converging toward has
exactly one authoritative source, and every out-of-band actor that can also
write to the same state undermines the guarantee.

[Idempotent Consumer](idempotent-consumer.md) is the messaging-system
counterpart of the idempotency key variant described in dimension 8,
applied to the receiving side of an asynchronous message rather than to a
synchronous request, and the two are frequently implemented with the same
underlying deduplication store.

The [State](state.md) pattern and the closed transition table variant from
dimension 8 share the same intent, encoding every legal transition
explicitly so an illegal one is structurally impossible or explicitly
rejected rather than silently allowed to happen through an unconstrained
mutation of a status field.

The [Command](command.md) pattern's support for reversible operations, undo
and redo, depends on predictable, forecastable effects. a command's undo
implementation can only reliably reverse an effect it can predict, which
means a command whose execute step touches unpinned non-determinism is
correspondingly harder to undo correctly.

[Postel's Law](postel-law.md) is the principle most in tension with this
one, as described at length in dimension 3, rather than a pattern this entry
composes cleanly with. it is listed here as a related entry specifically
because the tension between them is a design decision every system-level
interface has to make, not because the two principles reinforce each other.

## 14. Refactoring path in and out

Introducing predictability into an existing component, step by step. First,
identify every source of non-determinism the component currently depends on
without declaring it, a direct call to the system clock, a direct call to a
random number generator, a read of an environment variable or a global
mutable field, a network call whose timing or response can vary. Second,
extract each of these behind an explicit, injectable interface, a `Clock`
parameter instead of a direct clock read, a seeded random source instead of
a global one, so the component's true inputs are now fully visible in its
signature rather than partially hidden inside its body. Third, for a
state-changing operation reachable more than once with the same logical
intent, add an explicit idempotency key parameter and a deduplication store,
following the variant in dimension 8, rather than assuming the caller will
never retry. Fourth, state the component's precondition and postcondition
explicitly, as executable assertions where the language and performance
budget allow it, so a contract violation is caught at the boundary rather
than discovered later as a corrupted downstream state. Fifth, where the
component is a build or release step, pin every dependency and toolchain
component it consumes to an exact version, and remove any network access
that is not an explicitly declared and pinned input. Sixth, add a verifier,
a test that calls the operation twice with the same idempotency key and
asserts a single underlying effect, a checksum comparison across two
independent builds, a contract test run against a dependency before
promotion, so the guarantee is checked continuously rather than only
believed.

Removing predictability engineering when it no longer earns its place. This
direction is less often discussed but equally real. When a component that
was made predictable for a specific consumer's benefit no longer has that
consumer, for example a synchronous idempotent retry path superseded by an
at-least-once event stream with downstream deduplication handled at a
different layer entirely, the local idempotency machinery becomes dead
weight rather than a guarantee anyone still relies on, and it should be
removed along with its test coverage rather than left in place out of
caution. Similarly, if a component was forced into a strict, narrow contract
that now regularly rejects legitimate callers because the surrounding system
has grown more varied than the original contract anticipated, the honest fix
is often to widen the contract deliberately, documented and versioned, rather
than to patch around the rejection at every call site. What should never
happen is a contract that is quietly no longer honored while still being
advertised as a guarantee. that state is worse than never having made the
promise, because a consumer who trusted the label continues acting on a
forecast that has silently gone stale.

## 15. Testing and verification

Property-based testing with a fixed, logged seed is the direct testing
counterpart of a pure function's predictability claim. the test generates
many inputs, but because the random generator itself is seeded, a failure
can be reproduced exactly by rerunning with the same seed, which turns a
one-off flaky-looking failure into a reproducible bug report.

Contract tests for idempotency assert the behavior directly rather than
inferring it. send the same request, carrying the same idempotency key,
some fixed number of times, and assert both that the response is identical
across every call and that the underlying side effect, a row inserted, a
charge created, occurred exactly once, not once per request.

Golden or snapshot testing catches predictability drift over time rather
than within a single run. the current output of a component is compared
against a previously accepted, checked-in reference output, and any
difference forces an explicit decision, either the change is an intentional
update to the golden file, or it is an unintentional regression the test
just caught.

Metamorphic testing is useful where there is no single correct output to
assert against, but a predictable relationship between related inputs is
still expected. for a sort function, reversing the input and reversing the
output should always produce the same result as sorting the reversed input
directly, and a violation of that relationship reveals unpredictable
behavior even without a fixed expected answer for either input on its own.

Reproducibility verification for builds is structural rather than assertion
based. two or more independent build environments run the same declared
build from the same source, and their output artifacts are hashed and
compared. Debian's public reproducibility dashboards are the production
instance of exactly this technique, run continuously and at scale rather
than as a one-off check (Debian Wiki, "ReproducibleBuilds/About",
https://wiki.debian.org/ReproducibleBuilds/About, verified 2026-08-02).

Deterministic simulation, as described in dimension 8 and demonstrated by
FoundationDB, is the testing technique of choice for concurrent and
distributed behavior specifically, because ordinary unit and integration
tests running against real threads and real network sockets cannot force a
specific interleaving to recur on demand, while a simulation with a
controlled, seeded scheduler can replay the exact interleaving that produced
a failure as many times as needed to diagnose it.

## 16. Observability signals

For idempotent endpoints, track the ratio of idempotency-key cache hits to
total requests carrying a key, since a healthy system under normal retry
behavior shows a small but non-zero hit rate that tracks with observed
client-side timeouts, and an unexpected spike can indicate a client
retrying far more aggressively than intended. Track duplicate-effect
incidents directly wherever the underlying system of record allows it, for
example a payment ledger's own duplicate detection, since this is the
ground truth metric the idempotency mechanism exists to drive toward zero.

For build reproducibility, track the percentage of artifacts that verify as
bit-for-bit identical across independent build runs, the way Debian
publishes its per-architecture reproducibility percentage continuously
rather than as a one-time audit. A healthy trend holds steady or improves
over time. a sudden drop after a toolchain upgrade or a new dependency
addition is a signal worth investigating before it accumulates.

For reconciliation controllers, track the reconcile loop's churn rate, how
often it makes a correction on an object that was not just declared or
externally modified. A healthy controller converges quickly after a change
and then goes quiet. a controller making continuous corrections on the same
object over a long period, with no corresponding declared change, is the
observable signature of the out-of-band drift failure mode described in
dimension 11.

For test suites, track the flaky rate over time, the fraction of test runs
whose pass or fail outcome differs from a rerun against the identical
commit. A rising flaky rate is a leading indicator that the suite's
predictability guarantees are eroding, which in turn erodes the team's trust
in every red build the suite produces, independent of whether any individual
flaky test is itself important.

For versioned dependencies, track automated compatibility check results in
the publisher's own release pipeline, specifically whether a proposed patch
or minor release actually preserves the compatibility its version number
promises, before that release reaches any downstream consumer at all.

## 17. Security and privacy implications

Predictability cuts in two directions for security, and conflating them is a
common and costly mistake, which is why dimension 4 lists deliberately
unpredictable values as an explicit non-applicability case rather than
leaving the exception implicit.

Where predictability is the correct goal, it functions as a supply-chain
security control. a reproducible build lets a third party independently
verify that the binary running in production matches what the published
source claims to produce, closing off a class of attack where a compromised
build server injects malicious code that never appears in the source
repository a reviewer actually audits. This is the security rationale
explicitly stated by the Reproducible Builds project's own framing of the
problem, that trust should rest on auditable source rather than on trusting
every machine in the build pipeline (Reproducible Builds project,
https://reproducible-builds.org/docs/definition/, verified 2026-08-02).

Where unpredictability is the correct goal and predictability is mistakenly
imposed instead, the result is a genuine vulnerability rather than merely a
missed optimization. A session token, an authentication nonce, or a
password-reset token that can be forecast from information an attacker
already has, a sequential identifier, a timestamp with insufficient
precision, a weak or improperly seeded random source, allows session
hijacking or account takeover without the attacker ever needing to guess a
secret in the conventional sense, because the value was never secret in
practice, only obscured. This is the well-documented class of session
prediction and insecure direct object reference vulnerabilities, and the
correct engineering response is the opposite of everything in dimension 8.
cryptographically strong randomness, sufficient entropy, and no derivation
from any predictable ambient value.

Idempotency keys sit in an interesting middle position and deserve their own
note. the key itself must be unpredictable enough, or scoped narrowly
enough, per account and session, that an attacker cannot guess or enumerate
another user's key and piggyback on that user's cached, already-authorized
result. Stripe's own guidance to avoid deriving a key from an email address
or other sensitive personal data is a direct instance of this concern, since
a predictable key derivation scheme would let an attacker construct a valid
key for a target user without ever having seen that user's actual request
(Stripe, "Idempotent requests", https://docs.stripe.com/api/idempotent_requests,
verified 2026-08-02). The lesson generalizes. the operation's effect should
be predictable to its legitimate caller, and the token that identifies which
operation to deduplicate should not be predictable to anyone else.

Privacy has a smaller but real intersection with this principle through
reproducible builds and deterministic logging specifically, since a fully
deterministic build or simulation sometimes requires capturing enough
context, an exact random seed, an exact sequence of inputs, to replay a run
later, and that captured context can itself carry sensitive data if it was
sourced from a real production request rather than a synthetic one. A
record-replay or deterministic simulation rig built for the debugging
benefit described in dimension 11 should be reviewed for what it persists,
with the same care applied to any other system that stores request payloads.

## 18. References

Bertrand Meyer, "Applying 'Design by Contract'", IEEE Computer, vol. 25, no.
10, October 1992, pages 40 to 51, DOI 10.1109/2.161279,
https://dl.acm.org/doi/10.1109/2.161279, verified 2026-08-02.

R. Fielding and J. Reschke, editors, "Hypertext Transfer Protocol (HTTP/1.1):
Semantics and Content", RFC 7231, section 4.2.2, Internet Engineering Task
Force, June 2014,
https://datatracker.ietf.org/doc/html/rfc7231#section-4.2.2, verified
2026-08-02.

Reproducible Builds project, "Definition",
https://reproducible-builds.org/docs/definition/, verified 2026-08-02.

Debian Wiki, "ReproducibleBuilds/About",
https://wiki.debian.org/ReproducibleBuilds/About, verified 2026-08-02.

Kubernetes documentation, "Understanding Kubernetes Objects",
https://kubernetes.io/docs/concepts/overview/working-with-objects/, verified
2026-08-02.

Stripe, "Idempotent requests",
https://docs.stripe.com/api/idempotent_requests, verified 2026-08-02.

FoundationDB documentation, "Testing FoundationDB",
https://apple.github.io/foundationdb/testing.html, verified 2026-08-02.

Semantic Versioning 2.0.0, created by Tom Preston-Werner,
https://semver.org/, verified 2026-08-02.

Erlang and OTP documentation, "Design Principles",
https://www.erlang.org/doc/system/design_principles.html, verified
2026-08-02.

Wikipedia contributors, "Principle of least astonishment",
https://en.wikipedia.org/wiki/Principle_of_least_astonishment, verified
2026-08-02, cited here only for the cross-reference to a related but
distinct principle discussed in dimension 1 and 13. see
[principle-of-least-astonishment.md](principle-of-least-astonishment.md)
for the full sourced treatment of that entry.

## Code examples

Three languages are shown, TypeScript, Python, and Go, each demonstrating a
different implementation variant from dimension 8, so the examples cover
request-level idempotency, contract assertions with pure-function
determinism, and a closed state transition table respectively. All three
were compiled or run directly against the toolchain available at authoring
time. Java, Rust, and Swift are omitted for this entry because the three
variants shown are most idiomatically demonstrated with the standard library
alone in these three languages, and adding equivalent examples in the
remaining languages would repeat the same structure without illustrating a
meaningfully different aspect of the principle.

### TypeScript. idempotency key deduplication

Compiled with `npx tsc idem.ts --target es2020 --module commonjs --strict`
and run with `node`, both succeeding with no errors.

```typescript
interface OrderResult {
  orderId: string;
  amountCents: number;
  createdNow: boolean;
}

class IdempotentOrderService {
  private readonly seenKeys = new Map<string, OrderResult>();
  private nextId = 1;

  createOrder(idempotencyKey: string, amountCents: number): OrderResult {
    const cached = this.seenKeys.get(idempotencyKey);
    if (cached) {
      return { ...cached, createdNow: false };
    }
    const result: OrderResult = {
      orderId: `order_${this.nextId++}`,
      amountCents,
      createdNow: true,
    };
    this.seenKeys.set(idempotencyKey, result);
    return result;
  }
}

function main(): void {
  const service = new IdempotentOrderService();
  const key = "client-generated-uuid-8f2a";

  const first = service.createOrder(key, 4599);
  const retryAfterTimeout = service.createOrder(key, 4599);
  const differentClient = service.createOrder("another-uuid-11cc", 4599);

  if (first.orderId !== retryAfterTimeout.orderId) {
    throw new Error("retry must return the same order id, predictability violated");
  }
  if (first.orderId === differentClient.orderId) {
    throw new Error("distinct keys must never collide");
  }
  console.log("PASS: idempotent retries are predictable, distinct requests are not merged");
}

main();
```

Verified run output.

```
PASS: idempotent retries are predictable, distinct requests are not merged
```

### Python. Design by Contract assertions on a pure function

Run directly with `python3 dbc.py`, succeeding with no errors.

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Quote:
    principal_cents: int
    rate_bps: int
    term_months: int


def price_quote(quote: Quote) -> int:
    assert quote.principal_cents > 0, "precondition: principal must be positive"
    assert 0 <= quote.rate_bps <= 10_000, "precondition: rate must be a sane bps value"
    assert quote.term_months > 0, "precondition: term must be positive"

    monthly_rate = quote.rate_bps / 10_000 / 12
    total_cents = round(quote.principal_cents * (1 + monthly_rate * quote.term_months))

    assert total_cents >= quote.principal_cents, "postcondition: interest never negative"
    return total_cents


def main() -> None:
    q = Quote(principal_cents=500_000, rate_bps=750, term_months=12)

    results = [price_quote(q) for _ in range(5)]
    assert len(set(results)) == 1, "same input must always produce the same output"
    print(f"price_quote is deterministic across {len(results)} calls, {results[0]} cents")

    try:
        price_quote(Quote(principal_cents=-1, rate_bps=100, term_months=6))
        raise SystemExit("expected AssertionError for violated precondition")
    except AssertionError as exc:
        print(f"PASS: contract violation rejected predictably, {exc}")


if __name__ == "__main__":
    main()
```

Verified run output.

```
price_quote is deterministic across 5 calls, 537500 cents
PASS: contract violation rejected predictably, precondition: principal must be positive
```

### Go. closed state transition table

Run directly with `go run sm.go`, succeeding with no errors.

```go
package main

import "fmt"

type OrderState string

const (
	StatePending   OrderState = "pending"
	StatePaid      OrderState = "paid"
	StateShipped   OrderState = "shipped"
	StateCancelled OrderState = "cancelled"
)

var allowedTransitions = map[OrderState]map[OrderState]bool{
	StatePending:   {StatePaid: true, StateCancelled: true},
	StatePaid:      {StateShipped: true, StateCancelled: true},
	StateShipped:   {},
	StateCancelled: {},
}

func transition(current OrderState, target OrderState) (OrderState, error) {
	next, known := allowedTransitions[current]
	if !known {
		return current, fmt.Errorf("unknown state %q", current)
	}
	if !next[target] {
		return current, fmt.Errorf("transition %s -> %s is not permitted", current, target)
	}
	return target, nil
}

func main() {
	state := StatePending

	for _, target := range []OrderState{StatePaid, StateShipped} {
		next, err := transition(state, target)
		if err != nil {
			panic(err)
		}
		state = next
		fmt.Printf("ok: now %s\n", state)
	}

	if _, err := transition(state, StatePending); err == nil {
		panic("shipped to pending must be rejected, predictability violated")
	} else {
		fmt.Printf("PASS: illegal transition rejected deterministically, %v\n", err)
	}
}
```

Verified run output.

```
ok: now paid
ok: now shipped
PASS: illegal transition rejected deterministically, transition shipped -> pending is not permitted
```
