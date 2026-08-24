---
name: Characterization Test
slug: characterization-test
family: 14-testing
category: Testing
aliases: [Golden Master Test, Approval Test, Pinning Test]
first_described: "Michael Feathers, Working Effectively with Legacy Code, Prentice Hall, 2004"
maturity: canonical
related: [golden-master, mock, stub, fake, spy]
incompatible_with: []
verified: 2026-08-04
---

# Characterization Test

## 1. Name, aliases, and lineage

The canonical name is Characterization Test. Michael Feathers coined the term
in his book "Working Effectively with Legacy Code" (Prentice Hall, 2004),
chapter 13, titled "I Need to Make a Change, But I Don't Know What Tests to
Write." The term describes a test written to pin down, not to specify, the
current behavior of a piece of code the author does not fully understand.
Wikipedia's entry on the pattern confirms the coinage and the book source,
stating that a characterization test is "a means to describe the actual
behavior of an existing piece of software, and therefore protect existing
behavior of legacy code against unintended changes via automated testing"
(https://en.wikipedia.org/wiki/Characterization_test, verified 2026-08-04).

The most common alias is Golden Master Test, used interchangeably by many
teams and tool authors for the same idea, sometimes with a narrower meaning
that emphasizes a large, stored reference output rather than a handful of
assertions. The ApprovalTests family of libraries markets itself under a
third name, Approval Test, and its C++ implementation states plainly in its
own README that it is "also known as Golden Master Tests or Snapshot
Testing" (https://github.com/approvals/ApprovalTests.cpp, verified
2026-08-04). Some teams also call the technique a Pinning Test, a name that
leans on the verb Feathers himself uses throughout the book, that of pinning
behavior down before touching it. This entry treats Golden Master as a name
for the same underlying idea, and cross-references the separate Golden
Master entry in this repository, which goes deeper on the single-artifact,
whole-output variant of the technique. Characterization Test is the broader
umbrella term and the one that appears in the academic and practitioner
literature on legacy code first, so it is the name used throughout this
entry.

There is no committee-standardized definition beyond Feathers' own. The
pattern is not one of the twenty-three Gang of Four design patterns, it is
a testing pattern that emerged from the practice of maintaining code that
predates any test suite, and its lineage sits alongside other techniques in
the refactoring and legacy-code literature rather than in the object-oriented
design pattern literature. It shares intellectual ancestry with
snapshot-based approval testing, which many teams reached independently
before or without reading Feathers, and with regression testing generally,
of which it is a deliberately unopinionated special case.

## 2. Problem and context

A team inherits a module, a service, or a whole codebase with no tests, or
with tests too sparse to trust. The code has been running in production for
years. Nobody currently on the team wrote all of it, and the people who did
write parts of it may be unavailable or may not remember the reasoning
behind a given branch of logic. A change is now required, whether a bug
fix, a performance improvement, an extraction into a smaller module, a
language or framework migration, or simply moving the code into a form that
a modern test suite can exercise at all.

The obvious response, "write tests first," runs into a wall immediately.
Writing a specification-style test requires knowing what the code is
supposed to do. In legacy code the only reliable authority on what the
code is supposed to do is what the code currently does, because the
original requirements document, if it ever existed, is stale, missing, or
contradicted by production behavior that users now depend on. A developer
who tries to write "correct" tests from first principles will frequently
discover, mid-refactor, that the code does something subtly different from
what they assumed, and that some downstream consumer relies on exactly that
subtlety. The classic example from Feathers' book is a tax calculation
routine with a branch nobody can explain, one that might be a bug baked
into behavior a customer's own downstream system now compensates for, or
might be dead code that has never executed, and there is no way to tell
without asking the code itself.

The context this pattern targets specifically is code changed under time
pressure, code with unclear or contested requirements, code whose original
authors are gone, and code that must keep functioning identically for
users while its internals are altered. It is not a substitute for
requirements-driven testing on new code, and it is explicitly a technique
for the moment before a refactor, not a permanent testing philosophy for a
codebase in good health.

## 3. Forces

Fidelity to actual behavior pulls against fidelity to intended behavior.
The whole point of the technique is to capture what the system does, bugs
included, which means a characterization test can encode and thereby
preserve a defect. This is in direct tension with the instinct every
careful engineer has to fix a bug the moment they see it.

Speed of coverage pulls against precision of coverage. A characterization
test can be written extremely fast, often by running the code once, capturing
whatever it produced, and asserting that output going forward. This speed is
the pattern's main selling point, but it means the resulting test says
nothing about whether the captured behavior is correct, only that it
matches what happened at capture time on one particular input.

Understanding pulls against safety. The pattern trades a deep read of the
code, which is slow and error-prone on a large legacy system, for an
empirical capture of observed behavior, which is fast but shallow. A
characterization test does not explain why the code behaves as it does, it
only records that it does.

Test brittleness pulls against refactoring confidence. A characterization
test written at too fine a grain, pinning internal call sequences or
private field values rather than externally observable outputs, will break
on every refactor even when the observable behavior is unchanged, which
defeats the purpose of writing it in the first place.

Coverage breadth pulls against effort invested. Characterization tests are
usually written to cover the paths a specific refactor will touch, not the
entire system, because full behavioral coverage of a large undocumented
system is often infeasible in the time available. This means the safety
net has holes by design, and those holes are exactly the parts of the
system nobody is about to change today, which is a reasonable bet but a bet
nonetheless.

The pattern favors speed, empirical grounding, and refactoring safety at
the expense of correctness verification, explanatory power, and complete
coverage. It sacrifices the normal testing goal of proving the system does
the right thing in exchange for the narrower and more immediately useful
goal of proving the system still does the same thing.

## 4. Applicability and non-applicability

Reach for a characterization test when the code under change has no
adequate existing tests and the team cannot afford, or does not yet have
enough understanding, to write specification-based tests. Reach for it
before extracting a function, class, or service out of a monolith, so the
extraction can be verified against the pre-extraction behavior. Reach for
it before a language or framework migration, where the goal is behavioral
parity between the old and new implementation rather than a redesign. Reach
for it when a bug report references behavior nobody can currently explain
and the immediate need is to stop the behavior from silently drifting
further while it is investigated. Reach for it when onboarding into an
unfamiliar codebase, because writing characterization tests is itself a
technique for building understanding, since the surprises the tests reveal
are exactly the parts of the system that need closer reading. Reach for it
as the first step of the "sprout method" and "wrap method" techniques
Feathers describes for making changes to legacy code safely, since both
rely on knowing the seam's current behavior before altering anything around
it.

Do not reach for it as a substitute for specification-based tests on new
code, because a characterization test of newly written code is redundant
with the implementation and will not catch a logic error that is consistent
between the implementation and the test, since both were derived from the
same flawed reasoning at the same time. Do not reach for it as a way to
avoid understanding the code at all, because the pattern is meant to build
understanding incrementally, not to permanently substitute for it, and a
team that ships characterization tests and never revisits the behavior they
encode is choosing to freeze bugs in place indefinitely. Do not reach for
it when the system's requirements are well understood and stable, because
specification tests are cheaper to maintain and communicate intent more
clearly than an opaque snapshot. Do not reach for it as the mechanism for
verifying a genuine behavior change, because a characterization test that
starts failing because you intentionally changed behavior is not a bug in
the test, it is the test doing its job, and the correct response is to
update the reference, but if updating references becomes routine on a
given test, that test has stopped functioning as a safety net and started
functioning as friction. Do not reach for it on code with side effects that
are expensive, non-idempotent, or non-deterministic without first isolating
those side effects, because a characterization test that calls a live
payment gateway or sends real email on every run will be too slow, too
risky, or too flaky to survive as a permanent fixture, and the correct move
there is to introduce a seam (see the Humble Object and Wrap Method
techniques) before capturing behavior.

## 5. Structure

The pattern has four participants. The System Under Characterization is the
existing code whose behavior is unknown or only partially known, treated
for the duration of the exercise as a black box or gray box. The Test
Driver is the piece of test infrastructure that runs the system with a
chosen set of inputs and captures whatever output, side effect, or thrown
exception results. The Captured Reference is the recorded output from a run
of the system, either embedded directly as literal assertions in the test
code or stored externally as a golden file the test driver diffs against
on every subsequent run. The Comparator is the mechanism, often as simple as
an equality assertion, sometimes a structural diff for complex objects, that
decides whether a later run matches the Captured Reference and fails the
test if it does not.

The System Under Characterization plays no active role beyond being
callable, and it does not need to know it is being tested. In most cases it
should not be modified at all to accommodate the test, aside from the
minimal seam-introduction techniques used when the code is genuinely
untestable as written (constructor side effects, hidden singletons, static
state). The Test Driver owns the decision of what inputs to exercise,
which is itself a design choice discussed further in dimension 8. The
Captured Reference is deliberately not hand-derived from a specification;
it comes from actually running the code, which is what distinguishes this
pattern from ordinary example-based unit testing. The Comparator's
precision determines the test's sensitivity. An exact string match on a
large serialized object will catch every difference but will also be
extremely noisy on cosmetic changes, while a comparator that only checks a
few key fields is more stable but leaves more of the system's behavior
unprotected.

## 6. ASCII structure diagram

```
+----------------------------------+
| Test Driver (owns chosen inputs) |
+----------------------------------+
     | drives
     v
+------------------------------------------------------+
| System Under Characterization (existing legacy code) |
+------------------------------------------------------+
     | observed output
     v
(back to Test Driver)

+-------------------------------+
| Comparator (equality or diff) |
+-------------------------------+
     | compares against
     v
+-----------------------------------------+
| Captured Reference                      |
| inline literal, or a stored golden file |
+-----------------------------------------+
     |
     v
pass / fail signal
```

## 7. Dynamics

The first run of the process is a discovery run, not a verification run.
The developer writes a test that calls the System Under Characterization
with a chosen input and asserts something deliberately wrong, often a
placeholder value guaranteed to fail, or in tools built for this purpose, an
assertion against an empty or nonexistent reference file. Running the test
fails, and the failure message reveals the actual output the system
produced. The developer copies that actual output into the assertion, or in
tool-supported approval testing, approves the generated reference file by
moving it from a "received" state into an "approved" state. The test is run
a second time and now passes, because the assertion matches the system's
most recent output.

```
Discovery run
  developer writes assertion (dummy/failing) -> run system -> test FAILS
    -> failure output reveals actual behavior
    -> developer copies actual output into the assertion (or approves the
       generated reference file)

Verification run (repeated on every future change)
  run system -> compare actual output to Captured Reference -> PASS or FAIL
    PASS, behavior unchanged, refactor is safe so far
    FAIL, behavior changed
      -> if the change was intentional, review the diff, then update the
         reference, re-run, PASS
      -> if the change was NOT intentional, the refactor introduced a
         regression, fix the code, re-run
```

From this point forward the test behaves like any regression test. Every
time the refactor is exercised, the driver reruns the system and the
comparator checks the new output against the frozen reference. A failure at
this stage carries genuine ambiguity that the developer must resolve by
judgment, not by the test itself, since either the refactor broke something
that should not have changed, in which case the fix is to the code, or the
refactor deliberately changed the behavior, in which case the fix is to
update the reference and move on. This is the one place where the dynamics
of a characterization test diverge sharply from a specification test. A
specification test failing always means the code is wrong. A
characterization test failing means the code is different, and only the
developer, using their own knowledge of what the refactor was supposed to
do, can say whether different is bad.

## 8. Implementation variants

The inline literal variant embeds the captured value directly as a
hardcoded expected value in the test source, using the language's ordinary
assertion mechanism. This is the lightest-weight variant, requires no extra
tooling, and is the natural first reach in any language with a standard
testing library. It works well when the output is small, such as a return
value, a short string, or a small object with few fields.

The golden file variant stores the captured reference as an external file
next to the test, and the comparator diffs the live output against the
file's contents on every run. This is the natural choice when the output is
large, such as a rendered page, a generated report, a serialized data
structure with many fields, or a whole log of interactions. This is the
variant most closely associated with the name Golden Master, and it is the
subject of the separate Golden Master entry in this repository, which
covers file-format choices, diff tooling, and update workflows in depth.

The approval testing variant is a tooling-supported version of the golden
file approach, where a dedicated library manages the received-versus-approved
file lifecycle, launches a diff tool automatically on mismatch, and
integrates the approve step into the developer's normal workflow rather
than requiring a manual file copy. The ApprovalTests family of libraries,
spanning C#, Java, C++, Ruby, Python, TypeScript, Dart, and LabVIEW, is the
best known implementation of this variant (https://github.com/approvals,
verified 2026-08-04), and each of these implementations frames itself
explicitly around the same golden master and snapshot testing vocabulary.

The snapshot testing variant, popularized by JavaScript testing tools for
UI components, automates the capture step so heavily that the developer
rarely writes an assertion by hand at all. A single call renders the
component, serializes its output, and either creates a new snapshot file or
compares against an existing one. Jest's own documentation frames the
purpose of a snapshot test as guarding a rendered UI against unexpected
change, and states that a failing comparison means "either the change is
unexpected, or the reference snapshot needs to be updated"
(https://jestjs.io/docs/snapshot-testing, verified 2026-08-04), which is the
identical dynamics described in dimension 7 above, applied specifically to
rendered UI trees. This variant trades even more manual effort for even
less precision about what exactly is being pinned, since a full component
render snapshot captures far more than the property under test.

The live comparison variant, sometimes called a parallel run or a
scientist-style experiment, does not store a reference at all. Instead, the
old and new implementations are run side by side against real production
traffic, and their outputs are compared on every request, with the old
implementation's result always being the one returned to the user while the
new implementation's result is only logged and diffed. GitHub's own
Scientist library implements exactly this pattern, describing itself as "a
Ruby library for carefully refactoring critical paths" that lets a
developer "wrap both original and new code behavior" and have the library
"execute both code paths, measure performance, compare results, and publish
findings, while always returning the control value to users"
(https://github.com/github/scientist, verified 2026-08-04). This is a
characterization test extended into production. Instead of a fixed
reference captured once, the reference is the currently running old code,
recomputed on every real request, which is far more expensive but catches
behavioral drift across the entire input distribution the system actually
sees rather than only the inputs a developer thought to test.

Language idiom changes the shape of the test driver more than the shape of
the pattern. In dynamically typed languages the captured reference is
often a loosely structured literal, a dictionary or hash compared for deep
equality. In statically typed languages the captured reference is usually
a concrete value of the return type, and serialization-based comparators
are common when the type itself is complex, since hand-writing a full
struct or record literal for every field is tedious and obscures which
fields the test actually cares about.

## 9. Known production uses

The ApprovalTests library family is the most direct and widely used
implementation of this pattern as a first-class testing tool, spanning
eight separate language implementations maintained under the approvals
GitHub organization, with the C++ implementation alone describing itself as
an alternative to plain asserts specifically suited to "testing objects
with lots of fields, or lists of objects" (https://github.com/approvals/ApprovalTests.cpp,
verified 2026-08-04).

GitHub's own engineering team built and open-sourced the Scientist library
specifically to carry out large-scale refactors of critical production code
paths, describing the library's purpose as letting a team run both an old
and a new implementation, compare their results in production, and continue
serving user traffic from the old implementation until confidence in the
new one is established (https://github.com/github/scientist, verified
2026-08-04). This is the pattern applied at the scale of an entire company's
production refactoring practice rather than as a unit-test-time technique.

Jest, maintained by the OpenJS Foundation and used across most JavaScript
and TypeScript projects, ships snapshot testing as a built-in feature whose
documentation explicitly frames its purpose as detecting unintended change
against a stored reference, the same dynamic Feathers describes for
characterization tests, applied specifically to rendered component output
(https://jestjs.io/docs/snapshot-testing, verified 2026-08-04).

## 10. Consequences

Positive. A characterization test can be written in minutes against code
the author does not understand, because it requires no specification, only
an ability to run the code and observe its output. It provides an
immediate, concrete safety net before any refactor, catching accidental
behavior changes that would otherwise surface as a production incident.
Writing one is itself a discovery process, since surprising captured values
are a direct signal of behavior worth investigating before touching the
code around it. It requires no upfront agreement about what the code is
supposed to do, which sidesteps stalled conversations about unclear
requirements that would otherwise block progress indefinitely. It composes
naturally with incremental refactoring techniques, since each small step
can be re-verified against the same fixed reference cheaply.

Negative. A characterization test faithfully preserves whatever bugs
existed in the code at the moment it was written, and unless someone
revisits the reference deliberately, that bug becomes effectively locked in
as the specification. It provides no explanation of why the code behaves as
captured, so a future reader gains a safety net but not understanding. Its
coverage is exactly as broad as the inputs chosen at capture time and no
broader, which means large, complex systems retain substantial unprotected
surface area even after wide characterization effort. It can become a
source of false confidence, since a passing suite of characterization tests
proves the observable behavior on the tested inputs is unchanged, not that
the refactor is correct, safe, or free of new bugs on untested inputs.
Golden-file and snapshot variants in particular are prone to a failure mode
where developers habitually approve every diff without reading it, at which
point the test stops protecting anything and becomes pure overhead. Tests
pinned at too fine a grain, capturing internal structure rather than
externally observable behavior, actively fight refactoring rather than
enabling it, breaking on every internal reshuffle even when nothing a
caller can observe has changed.

## 11. Failure modes and misuse

Symptom. The test suite is green after a refactor, but a bug the team knew
about before the refactor is still present and now appears in a new
location. Cause. The characterization test captured the buggy behavior
faithfully and nobody flagged it during the capture step as a known defect
to fix separately. Fix. Before locking in a captured reference, briefly
review it against any known bug reports for that code path, and if a known
bug is present in the captured output, either fix the bug first in a
separate, deliberate change with its own specification test, or record the
bug explicitly in a comment next to the assertion so a future reader knows
the captured value is not aspirational.

Symptom. The characterization test suite fails constantly on unrelated
changes, and developers start approving every failure without reading the
diff. Cause. The reference was captured at too fine a grain, often by
snapshotting an entire large object graph, log, or rendered structure
instead of the specific field or behavior the refactor actually needs to
protect. Fix. Narrow the comparator to the properties that matter for the
refactor at hand, or restructure the captured output to exclude volatile,
irrelevant fields such as timestamps, random identifiers, or ordering that
was never a contract in the first place.

Symptom. The characterization test passes locally but is flaky in CI, or is
so slow that developers skip running it. Cause. The System Under
Characterization has hidden non-determinism, an unstabilized dependency on
wall-clock time, random number generation, iteration order over an
unordered collection, or a live network call to an external service. Fix.
Introduce a seam around the non-deterministic dependency using the
techniques from dimensions 5 and 8, most commonly the Humble Object or Wrap
Method patterns, so the test can inject a fixed value in place of the
non-deterministic one, and only then capture the reference.

Symptom. A large batch of characterization tests were written all at once
before a big migration, and six months later nobody on the team can explain
what any individual test is actually protecting. Cause. Characterization
tests were treated as a permanent testing strategy rather than a temporary
scaffold, with no follow-up work to replace the most important ones with
readable, intention-revealing specification tests once the behavior was
understood. Fix. Treat the characterization suite as a transitional asset.
As understanding of the legacy code deepens, deliberately convert the
highest-value characterization tests into named, documented specification
tests that state the intended behavior in the test name and body, and let
lower-value ones expire once the refactor they protected has shipped and
stabilized.

Symptom. A characterization test written against a code path that calls a
paid third-party API or sends a real notification fires on every CI run,
racking up cost or spamming a real inbox. Cause. The test driver was
pointed directly at the live System Under Characterization without
isolating its external side effects first. Fix. Introduce a Fake, Stub, or
Mock (see the related entries in this repository) at the system's
boundary before capturing behavior, so the characterization test exercises
the business logic while the expensive or irreversible side effect is
intercepted and recorded instead of actually performed.

## 12. Trade-off matrix

| Property | Characterization Test | Specification-Based Unit Test | Live Traffic Comparison (Scientist-style) |
|---|---|---|---|
| Requires understanding requirements upfront | No | Yes | No |
| Speed to write initial coverage | Fast | Slow, proportional to specification effort | Slow, requires production plumbing |
| Detects that a refactor changed behavior | Yes, on the captured inputs only | Yes, on any behavior the spec covers | Yes, across the real input distribution |
| Detects that the original behavior was correct | No | Yes, by construction | No |
| Coverage breadth | Limited to captured inputs | As broad as the specification effort invested | As broad as production traffic, over time |
| Readability for a future maintainer | Low, an opaque frozen value | High, intent is explicit in assertion and test name | Low, results live in dashboards, not test code |
| Risk of locking in a known bug | High if uninspected | Low, since intent is specified deliberately | Low, since old behavior is intentionally kept as the control |
| Suitable for greenfield code | No | Yes | No |
| Operational cost | Low, runs in the normal test suite | Low, runs in the normal test suite | High, requires production infrastructure and monitoring |

## 13. Related and incompatible patterns

Golden Master is the closest sibling and is treated as a specific
implementation shape of this pattern in this entry's terminology, one that
emphasizes a single large stored reference artifact over a set of smaller
inline assertions. See the separate Golden Master entry in this repository
for file-format and diff-tooling depth that this entry does not repeat.

Mock, Stub, and Fake compose directly with this pattern rather than
competing with it. When the System Under Characterization has an external
dependency that is slow, expensive, or non-deterministic, a Stub or Fake is
introduced at that boundary before the reference is captured, so the
resulting characterization test is fast and repeatable. See the related
entries for each of these test double patterns in this repository.

Spy composes with this pattern when the goal of characterization is not
only the return value of the system but also the sequence and arguments of
calls it makes outward, letting the test driver capture and later verify
that interaction sequence as part of the reference.

The Sprout Method and Wrap Method techniques from Feathers' book rely on
characterization tests as their prerequisite step. Both techniques describe
how to make a change to legacy code by adding new, well-tested code around
or beside the existing untested code, and both depend on first pinning the
existing code's behavior so the new code's integration point can be
verified not to have disturbed it.

Characterization Test is philosophically incompatible with Test-Driven
Development in the strict red-green-refactor sense on the same piece of
code at the same time, because TDD's red step requires a specification of
intended behavior written before the implementation exists, while a
characterization test's entire premise is that the implementation already
exists and the specification is unknown. The two are not incompatible
across a codebase's lifecycle, however. A common and productive workflow is
to characterize legacy code first, then apply TDD to the new code that
replaces or extends it once its behavior is understood well enough to
specify deliberately.

## 14. Refactoring path in and out

Introducing this pattern into code that has none starts with identifying
the specific seam a planned change will touch, since attempting to
characterize an entire large system before making any change at all is
usually infeasible and delays the actual work indefinitely. The developer
picks a small number of representative inputs, including edge cases already
known to be tricky from prior bug reports if any exist, writes a failing
placeholder assertion for each, runs the system, and copies the actual
output into the assertion or approves the generated golden file. If the
System Under Characterization has hidden dependencies that make it
difficult to invoke in a test at all, such as static state, a constructor
that performs I/O, or a singleton that reaches out to a live service, the
developer first applies a minimally invasive seam-introduction technique,
such as extracting an interface at the dependency boundary and injecting a
Fake in its place, taking care that this seam-introducing change is itself
small enough to review confidently without a test, since there is by
definition no test yet to protect it. Once the characterization tests are
in place and green, the planned refactor proceeds behind that safety net,
rerunning the tests after every incremental step.

Removing this pattern, or more precisely retiring an individual
characterization test, happens once the behavior it protects has become
understood well enough to specify intentionally, or once the refactor it
was protecting has shipped, stabilized in production, and no longer carries
increased risk of regression. At that point the team has a choice. Leave the
characterization test in place indefinitely as an ordinary regression test,
which is often the right call for tests that continue to protect a stable
piece of business logic, or replace it with a hand-written specification
test whose name and body state the intended behavior explicitly, which is
the right call for the small number of characterization tests that turned
out to protect genuinely important, frequently discussed logic where
future maintainers will benefit from reading a stated intent rather than
reverse-engineering one from a frozen literal. A characterization test
should rarely be deleted outright without replacement, since doing so
reintroduces exactly the coverage gap the pattern exists to close.

## 15. Testing and verification

Characterization tests are, definitionally, themselves a testing technique,
so this dimension addresses how to verify that a given characterization
test suite is doing its job well rather than how to test using the
pattern generally, which the rest of this entry already covers.

Verify that the captured reference was actually reviewed at capture time,
not blindly accepted, by checking for a comment, commit message, or code
review note stating what the developer expected versus what was captured,
particularly when the two differed. Verify that the chosen inputs span the
edge cases relevant to the upcoming refactor, not only a single happy path,
since a characterization suite with one input per function provides much
weaker protection than one that includes boundary values, empty
collections, and known historically troublesome cases. Verify that the
comparator's granularity matches intent, by interrogating whether every
field a full object graph assertion captures is actually load-bearing for
the refactor, or whether narrowing the assertion to fewer fields would
reduce false-positive churn without reducing real protection. Verify that
any non-determinism has genuinely been eliminated by running the same
characterization test repeatedly in a loop locally before trusting it in
CI, since a test that occasionally produces a different captured value on
an unmodified system indicates a leaked dependency on time, randomness, or
unordered iteration that will eventually produce a flaky failure at an
inconvenient moment. Verify, once the refactor is complete, that the
characterization tests were not weakened during the refactor itself to
make them pass, for example by loosening an equality assertion to a
substring match or deleting an inconvenient input case, since this defeats
the purpose retroactively, and code review of the test changes alongside
the implementation changes is the practical mechanism for catching this.

## 16. Observability signals

In CI, the signal to watch is the ratio of characterization test failures
that get fixed in the implementation versus failures that get resolved by
simply updating the reference. A team where references are updated far more
often than implementations are fixed in response to a characterization
test failure is a team that has stopped treating the test as a safety net
and started treating it as a rubber stamp, and that ratio, tracked over
time from commit history or CI logs, is a useful early warning.

For the live-comparison variant of this pattern, such as GitHub's Scientist
library, the relevant observability signal is a published mismatch rate
between the control and candidate code paths, which the library is
explicitly designed to report so a team can decide when confidence in the
new implementation is high enough to promote it to the sole implementation
(https://github.com/github/scientist, verified 2026-08-04). A healthy
rollout shows the mismatch rate trending toward zero as edge cases surface
and get addressed; a mismatch rate that stays flat or climbs indicates the
new implementation has a systematic behavioral difference from the old one
that has not yet been identified.

At the individual test level, the most useful signal in a test report is
not simply pass or fail but the size and shape of the diff on failure. A
one-line diff on a captured value is quick to review and decide on. A
sprawling diff across an entire large golden file is a sign the captured
reference is too coarse-grained to review, and that signal should prompt
narrowing the captured output rather than habitually accepting large
diffs.

## 17. Security and privacy implications

Captured references, whether inline literals or golden files, are static
text stored in the repository, and if the System Under Characterization is
run against production-like data during capture, sensitive values can be
inadvertently baked into the reference and committed to version control,
including customer names, account identifiers, tokens embedded in a
serialized response, or personally identifiable information present in a
legacy system's default test fixtures. This risk is specific to this
pattern because its entire premise is capturing real output from real code
paths, which is a materially different risk profile from a specification
test where every input and expected output is chosen deliberately by the
author. The practical mitigation is to run characterization capture against
synthetic or scrubbed data wherever the system allows it, and to review a
captured reference for sensitive content before committing it, the same
way any other change is reviewed before merge.

The live-comparison variant carries an additional operational risk worth
naming. Because the candidate implementation runs against real production
traffic to generate its comparison data, any bug in the candidate that
causes it to log, forward, or otherwise leak request data outside the
system's normal trust boundary is a genuine data exposure incident, not a
theoretical one, even though the candidate's result is never actually
served back to the user. Teams adopting the Scientist-style pattern
typically restrict what the experiment's published results are permitted
to contain and where those results are permitted to be stored, for exactly
this reason.

## 18. References

1. Michael Feathers, "Working Effectively with Legacy Code," Prentice Hall, 2004, Chapter 13, "I Need to Make a Change, But I Don't Know What Tests to Write." ISBN 978-0131177055.
2. "Characterization test," Wikipedia, https://en.wikipedia.org/wiki/Characterization_test, verified 2026-08-04.
3. ApprovalTests.cpp README, https://github.com/approvals/ApprovalTests.cpp, verified 2026-08-04.
4. Approvals organization, GitHub, https://github.com/approvals, verified 2026-08-04.
5. Scientist, GitHub, https://github.com/github/scientist, verified 2026-08-04.
6. "Snapshot Testing," Jest documentation, OpenJS Foundation, https://jestjs.io/docs/snapshot-testing, verified 2026-08-04.

## Code examples

### TypeScript

A characterization test written against an undocumented pricing function,
each expected value captured from an actual run rather than derived from a
specification. Self-contained here with a minimal inline assertion helper
in place of an external test runner such as Vitest or Jest, which a real
project would use for the same pinning.

```typescript
function legacyDiscount(total: number, isMember: boolean): number {
  if (total > 100 && isMember) return total * 0.85;
  if (total > 100) return total * 0.95;
  if (isMember) return total * 0.9;
  return total;
}

function pin(label: string, actual: number, captured: number): void {
  if (actual !== captured) {
    throw new Error(`${label}: got ${actual}, captured reference was ${captured}`);
  }
  console.log(`PASS ${label}`);
}

// Each captured value below came from one real run of legacyDiscount, not
// from a specification. This is what makes it a characterization test.
pin("total 150, member", legacyDiscount(150, true), 127.5);
pin("total 150, non-member", legacyDiscount(150, false), 142.5);
pin("total 50, member", legacyDiscount(50, true), 45);
pin("total 50, non-member", legacyDiscount(50, false), 50);
pin("boundary at exactly 100", legacyDiscount(100, true), 90);
```

Run. `npx tsc --noEmit` compiled cleanly against this block, and running the
transpiled output under Node printed five `PASS` lines with no thrown error,
confirming every captured value matches the function's actual output.

### Python

```python
def legacy_discount(total: float, is_member: bool) -> float:
    if total > 100 and is_member:
        return total * 0.85
    if total > 100:
        return total * 0.95
    if is_member:
        return total * 0.9
    return total


def pin(label: str, actual: float, captured: float) -> None:
    assert actual == captured, f"{label}: got {actual}, captured reference was {captured}"
    print(f"PASS {label}")


# Captured, not specified. Each expected value came from running the
# function once and recording what it produced.
pin("total 150, member", legacy_discount(150, True), 127.5)
pin("total 150, non-member", legacy_discount(150, False), 142.5)
pin("total 50, member", legacy_discount(50, True), 45)
pin("boundary at 100", legacy_discount(100, True), 90)
```

Run. `python3 legacy_characterization.py` executed with no assertion error;
all four `PASS` lines printed, confirming the captured values still match.

### Go

```go
package main

import "fmt"

func legacyDiscount(total float64, isMember bool) float64 {
	if total > 100 && isMember {
		return total * 0.85
	}
	if total > 100 {
		return total * 0.95
	}
	if isMember {
		return total * 0.9
	}
	return total
}

func pin(label string, actual, captured float64) {
	if actual != captured {
		panic(fmt.Sprintf("%s: got %v, captured reference was %v", label, actual, captured))
	}
	fmt.Println("PASS", label)
}

// Values below were captured from a real run, not derived from a spec.
func main() {
	pin("total 150, member", legacyDiscount(150, true), 127.5)
	pin("total 150, non-member", legacyDiscount(150, false), 142.5)
	pin("total 50, member", legacyDiscount(50, true), 45)
	pin("boundary at 100", legacyDiscount(100, true), 90)
}
```

Run. `go vet` reported no issues, and `go run` executed the program to
completion, printing four `PASS` lines with no panic, confirming the
captured values still match.

Java and Rust were not exercised for this entry; the pattern translates
directly (a plain assertion-based test method or `#[test]` function against
literal captured values), and the omission here is a budget choice, not a
claim that the pattern does not apply to those languages.
