---
name: Fuzz Testing
slug: fuzz-testing
family: 14-testing
category: Testing
aliases: [Fuzzing, Random Testing, Grammar-Based Testing, Coverage-Guided Fuzzing]
first_described: "Miller, Fredriksen, So 1990"
maturity: canonical
related: [property-based-test, mutation-test, fault-injection, golden-master, contract-test]
incompatible_with: []
verified: 2026-08-02
---

# Fuzz Testing

## 1. Name, aliases, and lineage

The canonical name is fuzz testing, usually shortened to fuzzing. The technique
was first described in Barton P. Miller, Lars Fredriksen and Bryan So, "An
Empirical Study of the Reliability of UNIX Utilities", published in
*Communications of the ACM*, volume 33, issue 12, December 1990. The paper grew
out of a 1988 graduate class project Miller ran at the University of
Wisconsin-Madison, in which students fed random character streams into
standard UNIX command-line utilities during a thunderstorm-disrupted dial-up
session and found that a large fraction of the tested programs crashed or
hung on garbage input. Miller has described choosing the word himself, saying
he wanted a name that would evoke random, unstructured data, and settled on
fuzz (University of Wisconsin-Madison history summarized in the Wikipedia
article "Fuzzing", https://en.wikipedia.org/wiki/Fuzzing, verified
2026-08-02, which cites the original paper). The paper reported that between
25 and 33 percent of the tested UNIX utilities could be crashed or hung with
purely random byte streams, a result that is still cited as the founding
observation of the field.

Random testing existed informally before Miller's paper under other names,
including monkey testing, but the 1990 paper is the first to name the
technique, measure it systematically across a large program population, and
publish reproducible results, which is why the pattern catalogs and the
academic literature both treat it as the origin point.

Aliases in real use, each carrying a slightly different emphasis.

- **Fuzzing.** The universal short form, used identically to fuzz testing in
  practice.
- **Random testing.** An older, broader term. Fuzzing is a specific,
  feedback-driven descendant of random testing, not a synonym for it, once the
  coverage-guided variant is in play, see the taxonomy below.
- **Grammar-based testing.** Used specifically for generation-based fuzzers
  that build inputs from a formal grammar rather than by mutating existing
  samples, see dimension 8.
- **Coverage-guided fuzzing.** Names the modern, dominant sub-family in which
  the fuzzer observes which code paths an input exercised and prefers inputs
  that reach new paths. This is the shape almost everyone means today when
  they say fuzzing without qualification, and it is the shape this entry
  spends most of its depth on.

The field has three widely recognised axes that any specific fuzzer sits on,
and confusing them is the most common source of miscommunication about what a
given tool actually does.

- **Mutation-based versus generation-based.** A mutation-based fuzzer starts
  from a corpus of real, valid inputs and applies small random changes, bit
  flips, byte splices, length changes. A generation-based fuzzer builds inputs
  from a model of the input format, a grammar or a protocol specification, with
  no seed corpus required. Some tools, including AFL and libFuzzer, are
  mutation-based by default but accept a hand-written or grammar-derived
  corpus, which blurs the line in practice.
- **Black-box, grey-box, white-box.** A black-box fuzzer has no visibility into
  the program under test beyond its output and exit status. A grey-box fuzzer
  observes lightweight signals, most often code coverage, through
  compiler-inserted instrumentation, without doing full program analysis. A
  white-box fuzzer uses symbolic execution or constraint solving to derive
  inputs that reach specific branches. AFL and libFuzzer are the canonical
  grey-box tools and are responsible for most of the field's practical impact
  since 2013 (Wikipedia, "Fuzzing", verified 2026-08-02, describing grey-box
  fuzzers as extremely efficient because they avoid full program analysis
  while still using feedback).
- **In-process versus out-of-process.** An in-process fuzzer links directly
  into the library under test and calls a single entry function millions of
  times per second inside one process, restoring state between calls with no
  fork or exec. An out-of-process fuzzer launches a fresh process, or a forked
  copy of one, per input. In-process fuzzing is dramatically faster and is what
  libFuzzer, cargo-fuzz, Atheris, Jazzer and Go's native fuzzing all do, and it
  also means a state leak between iterations, memory corruption that does not
  immediately crash, or a lingering global, can produce misleading results,
  which is a genuine engineering hazard covered in dimension 11.

## 2. Problem and context

A function, parser, decoder or protocol handler accepts input from outside the
program's control, and the person who wrote it can only imagine a finite set
of test cases by hand. The set of inputs an attacker, a corrupted file, a
misbehaving upstream service or an unusual user can actually produce is not
finite and is not enumerable by a human sitting at a keyboard.

This shows up in a codebase in a specific, recognisable way. There is a
function whose job is to take untrusted bytes and turn them into a structured
value, a JSON parser, an image decoder, a URL router, a binary protocol
deserializer, a compression routine, a regular expression engine, a
certificate parser. The function's own unit tests cover the happy path and a
handful of edge cases the author remembered to think of, an empty string, a
null byte, a very long string. What the author's imagination reliably misses
is the combinatorial interior of the format, a length field that lies about
the length of the data that follows, a UTF-8 sequence that is one byte short
of valid, an integer that overflows during an intermediate calculation before
the final bounds check runs, a recursive structure nested exactly deep enough
to blow the stack but not deep enough to trip an obvious depth guard. Miller's
original finding, that roughly a third of a large population of trusted UNIX
utilities crashed on nothing more adversarial than uniformly random bytes,
demonstrates that even experienced systems programmers systematically miss
this interior (Miller, Fredriksen, So, 1990).

The context in which fuzzing earns its cost has three parts.

- There is a real function boundary that consumes untrusted or externally
  produced bytes, structured data, or a sequence of API calls, and the
  boundary is reachable without full end-to-end setup, meaning it can be
  called directly with a byte string or a small set of typed arguments.
- The function has a checkable property beyond simply not crashing, most
  commonly memory safety in a language without automatic bounds checking, a
  round-trip invariant, or an explicit precondition and postcondition, though
  crash-freedom alone is already valuable when the language does not guarantee
  it.
- The cost of a defect at this boundary in production is high enough to
  justify machine time spent searching for it, a parser that runs on
  attacker-controlled input, a codec embedded in a browser or a mobile OS, a
  cryptographic primitive, a file format handled by a desktop application.

Outside that context, notably where the input space is small and enumerable,
or where the function under test does substantial and slow external I/O per
call, fuzzing is the wrong tool, and dimension 4 states the reasons in detail.

## 3. Forces

- **Coverage of the input space.** Strongly favoured. A coverage-guided fuzzer
  running for hours explores far more of a parser's input space than a human
  author will write example tests for, because it is driven by feedback from
  the binary itself rather than by what the author happened to imagine.
- **Cost of finding versus cost of writing.** Favoured once amortised. Setting
  up a fuzz target and a CI job is more work up front than adding two more
  unit tests, but the marginal cost of finding the next bug drops to zero CPU
  cycles of human time once the target exists, and the target keeps paying
  off on every future code change to the same function.
- **Compute cost.** Sacrificed. A useful fuzzing campaign runs continuously,
  for hours to weeks, and OSS-Fuzz's own description of its architecture is
  built around exactly this, a distributed fleet running fuzzers around the
  clock rather than a one-shot CI step (google.github.io/oss-fuzz, verified
  2026-08-02).
- **Determinism and debuggability.** Sacrificed at discovery time, regained
  afterward. A crash surfaces from an essentially random search, so the first
  report is often a large, ugly input. Every mainstream engine, libFuzzer, AFL,
  Go's native fuzzer, responds by minimising the failing input to the smallest
  reproducer before handing it back, which converts a one-off random event
  into a deterministic, replayable regression test.
- **False confidence.** A genuine risk the pattern must be described honestly
  against. A fuzz campaign that finds nothing proves only that the fuzzer did
  not find anything in the time it ran, never that the function is correct.
  Absence of a crash is not a proof of absence of a bug, and treating a clean
  fuzzing run as a correctness certificate is a category error covered again
  in dimension 11.
- **Signal quality versus example-based tests.** Favoured for crash classes
  such as memory corruption, panics, infinite loops and unhandled exceptions,
  where the fuzzer needs no specification of correct output, only whether the
  program survived. Sacrificed for semantic correctness, where the fuzzer
  needs an oracle, an assertion of what the right answer is, and without one
  it can run forever without ever flagging a function that runs to completion
  and simply returns the wrong number.
- **Engineering ownership.** Favoured for library and platform teams who own a
  parsing or decoding boundary once and want it hardened continuously.
  Sacrificed for application teams whose business logic has no natural
  byte-level or structured-argument entry point, where the setup cost per
  target rarely pays for itself.

## 4. Applicability and non-applicability

Reach for fuzz testing when the following hold.

- The unit under test parses, decodes, deserializes or otherwise transforms
  untrusted bytes or structured input, and a direct call into that unit is
  reachable without booting the whole application.
- The implementation language does not guarantee memory safety, C, C++, or
  unsafe blocks in otherwise safe languages, so the crash class the fuzzer is
  best at, memory corruption, is a real and severe risk category rather than
  merely a caught exception.
- The function has an explicit, checkable property, it must not panic, it
  must round-trip, its output must satisfy an invariant, or two
  implementations of the same specification must agree, see the property-test
  pairing in dimension 8.
- The format or protocol is complex enough that hand-written example tests
  provably miss cases, evidenced by a history of parser bugs, a specification
  with many optional or interacting fields, or third-party or historical data
  that already contains malformed instances.
- The target can run fast, ideally thousands of executions per second in an
  in-process target, because fuzzing effectiveness scales with the number of
  inputs tried per unit of wall-clock time.
- Continuous execution is realistic, either in CI as a short time-boxed job on
  every change, or as an always-on service such as OSS-Fuzz or the equivalent
  in-house infrastructure.

Do NOT reach for fuzz testing in these cases, and the reason matters more than
the rule.

- **The function's entire input space is small and enumerable.** A function
  taking a boolean and a three-value enum has eight total input combinations.
  Enumerate all eight in a table-driven test. A fuzzer searching that space is
  a slower, noisier way to reach a coverage figure a human can compute by
  hand in one minute.
- **The unit under test does slow or expensive I/O per call.** A fuzzer that
  can only try ten inputs a second because each call opens a real database
  connection or makes a real network request will not find anything useful in
  a practical time budget. Extract the pure, in-memory parsing or decision
  logic and fuzz that instead, leaving the I/O wrapper covered by ordinary
  integration tests.
- **There is no cheap, mechanical way to tell success from failure.** A
  crash-only oracle, did it throw, is nearly free. A semantic oracle, is this
  the mathematically correct answer, may require an independent reference
  implementation or a differential comparison. Without either, the fuzzer
  produces enormous volumes of inputs that are useless because nothing is
  watching for wrong answers, only for crashes.
- **The business logic under test has no natural structured-argument
  boundary.** A checkout workflow spanning inventory, pricing and a payment
  provider is not a fuzz target, it is a system test concern. Fuzzing shines
  at a function boundary, not at an end-to-end user flow.
- **The team cannot triage what the fuzzer finds.** A fuzzer running unwatched
  that accumulates crash reports nobody reads is worse than no fuzzer, because
  it creates the appearance of safety without the substance. Fuzzing needs an
  owner who reads and fixes findings, the same discipline the mutation-test
  entry requires for surviving mutants.
- **The property under test is really about behaviour under load or
  concurrency.** Fuzzing varies input data, not timing or thread interleaving.
  Race conditions and load-dependent failures need a different technique,
  stress testing or a concurrency-aware tool, not a data fuzzer.
- **A property-based test already exists and is sufficient.** When the domain
  under test is a pure function over structured values a language's own type
  system already constrains, for example sorting a list is idempotent, a
  property-based testing library that generates typed values and shrinks
  failures, see the property-based-test entry, is usually the better fit than
  a byte-level fuzzer. The two techniques overlap and increasingly share
  engines, but property testing starts from typed generators and fuzzing
  starts from raw bytes, see dimension 13.

## 5. Structure

Fuzz testing is not an object-oriented structural pattern with classes and
interfaces, it is a testing architecture with five participants.

- **Fuzz target, also called a target.** The function the fuzzer actually
  calls. It takes a byte string, or in typed engines a small set of typed
  arguments, and forwards them into the real code under test. A well-written
  target does the minimum work needed to reach the interesting logic, no
  unrelated setup, no unrelated I/O, and ideally no state carried between
  calls beyond what the code under test itself would carry in production.
- **Seed corpus.** A starting set of inputs the fuzzer begins from and mutates.
  Well-chosen seeds, real, valid examples of the format, dramatically shorten
  the time to first interesting coverage, because mutation starts from
  something already deep inside the parser's logic rather than from an empty
  or all-zero buffer.
- **Instrumentation.** Compiler or runtime-inserted code that reports which
  branches or basic blocks an execution touched, back to the fuzzing engine.
  This is what turns blind random testing into coverage-guided search.
  SanitizerCoverage in LLVM, Go's built-in coverage counters, and JaCoCo-backed
  bytecode instrumentation in Jazzer are three concrete implementations of the
  same idea in three different toolchains.
- **Mutation engine.** The component that takes an input from the corpus and
  produces a new candidate, bit flips, byte insertions and deletions, splicing
  two corpus entries together, dictionary-guided token substitution, or
  arithmetic mutations on integers found in the input. AFL's own description
  calls this an exceedingly simple but rock-solid instrumentation-guided
  genetic algorithm (github.com/google/AFL, verified 2026-08-02).
- **Oracle.** The check that decides whether an execution is a failure.
  Minimally this is whether the process is still alive and did not hang,
  which every engine gives for free. Beyond that, a target can add explicit
  assertions, a sanitizer such as AddressSanitizer to catch memory corruption
  that would otherwise silently continue, or a differential check against a
  second, trusted implementation.

Relationships. The engine drives the target in a tight loop entirely inside
its own process for in-process fuzzers. The target's only job is to call the
real code, it must not itself decide what counts as a bug beyond forwarding
crashes and assertion failures upward. The corpus is shared, mutable state,
every input that expands coverage is added back to it, so the corpus grows
over the life of a campaign and effectively becomes a second, larger
regression suite that the engine curates automatically.

## 6. ASCII structure diagram

```
+-----------------------+
| Seed Corpus           |
| (real valid examples) |
+-----------------------+
           | provides seeds
           v
+---------------------------------+
| Fuzzing Engine                  |
| (AFL, libFuzzer, go test -fuzz, |
| Atheris, Jazzer)                |
+---------------------------------+
           | mutates candidate, executes candidate
           v
+-------------------------+
| Fuzz Target             |
| (thin wrapper function) |
+-------------------------+
           | calls into
           v
+--------------------------+
| Code Under Test          |
| (parser, decoder, codec) |
+--------------------------+
           | crash, panic, assertion failure,
           | sanitizer trap
           v
+--------------------------------------------+
| Oracle                                     |
| process alive check | explicit assertion | |
| sanitizer trap | diff check                |
+--------------------------------------------+
           | on failure
           v
+---------------------------------------+
| Minimised, saved crash input          |
| (becomes a permanent regression test) |
+---------------------------------------+

Two feedback loops close this diagram, not drawn as
arrows to keep it readable:

  Instrumentation (SanitizerCoverage, Go coverage
  counters, JaCoCo for Jazzer) watches Code Under Test,
  the edges hit this execution, and feeds that coverage
  signal back to the Fuzzing Engine.

  An interesting input found during a run is added back
  into a Generated Corpus (grown during the run), which
  the engine draws on the same way it draws on the Seed
  Corpus.
```

## 7. Dynamics

The dominant modern flow is coverage-guided mutation fuzzing, shown below for
an in-process engine, which is the shape libFuzzer, cargo-fuzz, Go's native
fuzzer, Atheris and Jazzer all share.

```
Engine                    Fuzz Target              Code Under Test
  |                            |                            |
  |-- load seed corpus ------->|                            |
  |-- for each seed, execute ->|-- forwards bytes --------->|
  |                            |                            |-- runs, records
  |<-- coverage bitmap --------|<---------------------------|   which edges fired
  |                            |                            |
  |-- pick input from corpus   |                            |
  |   weighted by "interesting"|                            |
  |-- mutate. flip bits,       |                            |
  |   splice, insert, delete   |                            |
  |-- execute mutated input -->|-- forwards bytes --------->|
  |                            |                            |-- runs
  |<-- coverage bitmap --------|<---------------------------|
  |                            |                            |
  |-- compare bitmap to        |                            |
  |   corpus-wide coverage     |                            |
  |                            |                            |
  |-- new edge reached? ------>|                            |
  |     yes. add input to      |                            |
  |     corpus, repeat loop    |                            |
  |     no. discard, repeat    |                            |
  |                            |                            |
  |-- crash, hang, sanitizer   |                            |
  |   trap, or assertion ----->|                            |-- process aborts
  |   failure detected         |                            |   or throws
  |                            |                            |
  |-- minimise failing input   |                            |
  |   by repeatedly trimming   |                            |
  |   and re-testing for the   |                            |
  |   same failure signature   |                            |
  |                            |                            |
  |-- write minimised input to |                            |
  |   disk as a regression     |                            |
  |   seed for future runs     |                            |
```

Two timing properties are worth stating plainly because they explain most of
the surprising behaviour people run into.

First, the loop above executes the target function directly inside the
fuzzer's own process, often hundreds of thousands or millions of times per
second for a cheap target, with no process fork between iterations in the
common libFuzzer and Go-native cases. This is what makes coverage-guided
fuzzing tractable at all, an out-of-process fuzzer paying full process launch
cost per input would be orders of magnitude slower. It is also exactly why
global or static state that is not reset between calls, a cache, a
singleton, a mutable module-level list, corrupts results across iterations
in ways an out-of-process design would never expose, see dimension 11.

Second, minimisation happens after discovery, not during the search. The
engine does not try to find small failing inputs, it tries to find any
failing input as fast as possible, then spends a separate, bounded pass
shrinking that specific input while re-confirming the same crash signature at
each step. Go's fuzzer documents this explicitly with a dedicated
`-fuzzminimizetime` budget and a default of 60 seconds per minimisation
attempt (go.dev/security/fuzz, verified 2026-08-02).

## 8. Implementation variants

**Coverage-guided, in-process, mutation-based.** The mainstream shape,
libFuzzer, AFL and AFL++, Go's native fuzzer, cargo-fuzz, Atheris, Jazzer. All
five instrument the binary or bytecode, run in a tight loop inside one
process, and prioritise inputs that expand observed coverage. This is the
default choice absent a specific reason for something else.

**Black-box, out-of-process, mutation-based.** No instrumentation, a fresh
process per candidate input, purely random mutation of a seed corpus with no
feedback. Simpler to set up against a target the fuzzer author cannot
recompile, for example a closed-source binary or a remote network service,
but dramatically less effective per CPU-hour because it wastes effort on
inputs that retread already-explored code. Historically the original,
pre-2013 style of fuzzer.

**Grammar-based, generation fuzzing.** Inputs are synthesised from a formal
model of the format, a context-free grammar, an ABNF specification, or a
protocol state machine, rather than mutated from examples. This is the right
choice when a valid seed corpus barely exists, for example a brand-new binary
protocol, or when the format's validity is dominated by structural rules a
byte-level mutator will almost never stumble into by chance, such as a
balanced-parenthesis or checksummed format. The cost is that building and
maintaining the grammar model is itself real engineering work, and a wrong or
incomplete grammar silently narrows what the fuzzer can ever find.

**Structure-aware fuzzing via a derive macro or reflection.** Rather than
handing the target raw bytes, the target uses a helper, the `arbitrary` crate
in Rust or `FuzzedDataProvider` in libFuzzer-based C++ and in Atheris, to
consume the raw byte stream into strongly typed values, an integer in a
range, an enum variant, a vector of a given element type. This lets a
mutation-based, byte-level engine effectively fuzz a typed API without a
hand-written grammar, and it is the shape cargo-fuzz recommends for anything
beyond a flat byte string (rust-fuzz.github.io/book/cargo-fuzz.html, verified
2026-08-02, describing structure-aware fuzzing as a supported topic).

**Property-based testing as a typed sibling.** Property-based testing
libraries, Hypothesis in Python, fast-check in TypeScript, QuickCheck-family
tools, generate typed values directly rather than mutating byte streams, and
they shrink a failing case toward a minimal reproducer the same way a fuzzer
minimises. The overlap is real enough that some tools now blend both, Go's
native fuzzer stores each discovered failing input as a literal seed corpus
file usable exactly like a property-test example, and several property
libraries can consume a coverage signal. Treat the two as points on one
spectrum, byte-oriented and untyped at one end, value-oriented and typed at
the other, rather than as unrelated techniques. See the property-based-test
entry for the value-generator side of this spectrum.

**Differential fuzzing.** The same input is fed to two or more independent
implementations of the same specification, and a mismatch in output, rather
than a crash, is the failure signal. This is the strongest oracle available
short of a formal specification, because it needs no explicit invariant to be
written by hand, only a second implementation that is trusted to be at least
mostly correct. It is expensive to set up, since it needs the second
implementation to exist and be callable from the same target, and it can
produce false positives when the two implementations disagree on genuinely
unspecified behaviour rather than on a real bug.

**Snapshot or corpus replay fuzzing in CI.** Rather than running an open-ended
search on every commit, CI runs only the accumulated corpus, including every
previously minimised crash, as a fast regression check, while the open-ended,
long-running search happens separately on dedicated infrastructure or as a
scheduled job. This is the shape most teams actually adopt for day-to-day CI,
because an unbounded fuzz run does not fit a pull-request feedback loop, while
replaying a saved corpus in a few seconds does.

## 9. Known production uses

**OSS-Fuzz.** Google's continuous fuzzing service for open source software,
launched in 2016 in direct response to the Heartbleed vulnerability in
OpenSSL, which demonstrated that a widely used, security-critical library had
gone years with a bug fuzzing was well suited to find. As of the documented
figures the project reports, OSS-Fuzz has found and helped fix over 10,000
security vulnerabilities and 36,000 functional bugs across roughly 1,000
integrated open source projects, running libFuzzer, AFL++, Honggfuzz and
Centipede in combination with sanitizers on a distributed execution and
reporting system called ClusterFuzz (google.github.io/oss-fuzz, verified
2026-08-02).

**LLVM's libFuzzer, in Clang.** LibFuzzer is an in-process, coverage-guided
fuzzing engine built into the LLVM toolchain and shipped with Clang since
version 6.0, invoked with the `-fsanitize=fuzzer` compiler flag, and typically
combined with AddressSanitizer or the other LLVM sanitizers in the same
compilation. It is documented as having found thousands of bugs across
projects including OpenSSL, SQLite, FreeType, HarfBuzz, Python and the Linux
kernel (llvm.org/docs/LibFuzzer.html, verified 2026-08-02).

**AFL, and the Heartbleed and Shellshock disclosures.** American Fuzzy Lop,
created by Michal Zalewski, popularised the modern grey-box, coverage-guided,
genetic-algorithm style of fuzzing from around 2013 onward and is credited
with finding the majority of the bugs behind the 2014 Shellshock disclosure in
GNU Bash. Independently, the security researcher Hanno Böck demonstrated in
April 2015 that AFL, run against a suitably instrumented build of OpenSSL,
would have located the Heartbleed vulnerability that had shipped undetected
in production TLS libraries for roughly two years (Wikipedia, "Fuzzing",
verified 2026-08-02, and github.com/google/AFL, verified 2026-08-02, for
AFL's own description of its coverage-guided genetic algorithm).

**Go's standard toolchain, native fuzzing.** Go added first-class,
coverage-guided fuzzing to its standard `testing` package in Go 1.18 via
`testing.F` and the `go test -fuzz` flag, requiring no external dependency.
The Go project uses this facility to fuzz packages in its own standard
library, and any Go module can add a `FuzzXxx` function that runs as an
ordinary seed-corpus test under plain `go test` and as an open-ended search
under `go test -fuzz` (go.dev/security/fuzz, verified 2026-08-02).

**Jazzer, fuzzing the JVM at Code Intelligence.** Jazzer is a coverage-guided,
in-process fuzzer for the JVM built by Code Intelligence, adapting
libFuzzer's instrumentation-driven mutation approach to Java bytecode via
JaCoCo-based edge coverage instrumentation, exposed through a `@FuzzTest`
annotation on ordinary JUnit test classes so that fuzzing integrates directly
into an existing Java test suite rather than requiring a separate toolchain
(github.com/CodeIntelligenceTesting/jazzer, verified 2026-08-02).

## 10. Consequences

Positive.

- Finds the class of bug that human-written example tests are worst at
  finding, the malformed, boundary-adjacent, or adversarially shaped input
  nobody thought to write by hand.
- For memory-unsafe languages, directly catches memory corruption, a defect
  class with severe real-world consequences, before an attacker does.
- Every failure the engine finds is automatically minimised and saved as a
  regression, so the value compounds, a fuzzing campaign that ran once still
  leaves behind a growing, permanent, cheap-to-replay corpus.
- Requires no specification of what the correct output is when the oracle is
  crash-freedom alone, which lowers the setup cost dramatically compared to
  writing exhaustive example-based assertions.
- Scales with machine time rather than with engineer time once a target
  exists, which is a favourable trade against most other testing techniques
  as a codebase and its input surface grow.

Negative.

- Provides no proof of absence. A clean run after a fixed time budget says the
  fuzzer did not find a bug in that budget, nothing stronger, and treating it
  as a correctness guarantee is a documented misuse, see dimension 11.
- Needs continuous or at least substantial compute time to be effective, a
  five-second fuzz run in CI on every pull request finds close to nothing
  compared to hours or days of dedicated search.
- Without an explicit oracle beyond crash-freedom, the technique is blind to
  wrong-but-non-crashing answers, meaning a parser that silently corrupts data
  while never panicking will sail through indefinitely.
- Target quality gates everything. A target that does unrelated setup work,
  fails to reset state between calls, or wraps too much of the surrounding
  system produces slow, noisy, or misleading results, and building a good
  target is a real skill separate from writing the code under test.
- Triage cost is real and ongoing. Fuzzing an actively developed codebase
  produces crashes that need a human to read, deduplicate, and either fix or
  correctly dismiss as a known limitation, and a team without capacity for
  this drowns in unread findings.

## 11. Failure modes and misuse

**Treating a clean fuzz run as proof of correctness.** Symptom. A team ships a
parser after a five-minute fuzz run reported no crashes, and a real
production incident later reveals a bug well within the input space that run
never explored. Cause. Absence of evidence mistaken for evidence of absence,
compounded by an unrealistically short time budget. Fix. State fuzzing
coverage the same way test coverage is stated, as a lower bound with a known
time and corpus size, never as a binary pass or fail on correctness, and run
substantially longer campaigns before a release milestone than in ordinary
CI.

**State leaking across in-process iterations.** Symptom. A crash the engine
reports cannot be reproduced by replaying the single minimised input in
isolation, it only appears after thousands of other iterations have run
first. Cause. The fuzz target, or the code under test, keeps state in a
global, a cache, or a singleton that is not reset between calls, so the
in-process loop's speed advantage becomes a correctness liability, iteration
N's crash actually depended on residue left by iteration N minus one. Fix.
Reset every piece of mutable state the target touches at the start of each
call, or switch that specific target to an out-of-process or forking mode,
accepting the throughput cost, until the state hygiene is fixed.

**The target does too much, or the wrong thing.** Symptom. The fuzzer spends
almost all its time inside unrelated setup code, real file I/O, network
calls, cryptographic key generation, and almost never reaches the parsing
logic that was the actual target. Cause. The target function was wrapped
around a larger entry point instead of being extracted down to the specific
boundary that consumes untrusted bytes. Fix. Refactor so the pure parsing or
decoding logic is callable in isolation, then fuzz that function directly,
leaving the surrounding I/O covered by separate, ordinary tests.

**No oracle beyond survival.** Symptom. A fuzz campaign runs for weeks, finds
zero crashes, and the team concludes the function is correct, while a
completely wrong output for a specific malformed input silently passes every
single iteration. Cause. The target's oracle is implicit, the process
survived, with no explicit assertion, invariant, or differential check. Fix.
Add an invariant assertion to the target wherever one is known, for example a
round-trip check, a bounds check on a decoded length, or a differential
comparison against a second, trusted implementation, per the differential
fuzzing variant in dimension 8.

**Ignoring or bulk-dismissing findings.** Symptom. The fuzzer's crash-reports
directory accumulates hundreds of entries, none triaged, and eventually
somebody deletes the directory to make CI green again. Cause. No owner was
assigned to read and act on findings, so the volume outpaced the team's
attention and the pattern became noise rather than signal. Fix. Deduplicate
by crash signature or stack hash before presenting findings to a human, cap
the number of open findings tracked at once, and treat a growing backlog as a
signal to either allocate triage time or reduce the campaign's scope, never
as a signal to silently discard the corpus.

**Non-deterministic targets producing unreproducible crashes.** Symptom. The
engine reports a crash, but re-running the exact same minimised input locally
does not reproduce it. Cause. The target reads wall-clock time, environment
variables, random number generator state that is not seeded from the fuzz
input, or relies on hash-map iteration order, any of which makes the same
byte input behave differently on different runs. Fix. Make the target a pure
function of its input, inject any clock, RNG, or environment dependency as an
explicit, fuzzer-controlled parameter rather than reading global ambient
state.

**Corpus rot and stale seeds.** Symptom. Coverage plateaus early in every
campaign and never grows further, even after extended run time. Cause. The
seed corpus was never refreshed after the code under test changed
significantly, so the corpus keeps exercising an old code shape and the
mutation engine has nothing recent to build on. Fix. Periodically add real,
current, valid examples of the input format to the seed corpus, and merge in
minimised crash inputs from related targets when the formats overlap.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Fuzz testing | Property-based testing | Table-driven example tests | Mutation testing | Manual code review |
|---|---|---|---|---|---|
| Input space explored | Very large, feedback-guided over time | Large, but bounded by the generator's design and shrink strategy | Small, fixed, whatever the author enumerated | Zero new inputs, it mutates the code instead | Bounded by reviewer attention span |
| Needs an explicit oracle | No, crash-freedom is a free oracle, stronger with an added assertion | Yes, a property must be stated | Yes, each expected output is written by hand | No, it reuses the existing test suite as the oracle for each mutant | No formal oracle, relies on human judgement |
| Best defect class found | Memory corruption, panics, crashes, hangs on malformed or adversarial input | Logical invariant violations over typed domains | Known, anticipated edge cases | Weak or missing assertions in the existing suite | Design flaws, readability, intent mismatches |
| Setup cost | Medium, a target plus a seed corpus | Medium, generators and a stated property | Low, a table and a loop | Low once the test suite exists, the tool does the rest | Low tooling cost, high reviewer time cost |
| Compute cost | High, benefits from hours to days of continuous run time | Low to medium, usually thousands of cases per run | Very low, runs in milliseconds | Medium to high, reruns the suite once per mutant | None, human time only |
| Determinism of the output | Non-deterministic search, but every failure is minimised into a deterministic reproducer | Non-deterministic generation, same minimisation discipline | Fully deterministic by construction | Deterministic given a fixed seed and mutant set | Deterministic in the sense that the same code gets the same review |
| Requires memory-unsafe language to add most value | No, but the highest-value defect class, memory corruption, is specific to unsafe languages | No | No | No | No |
| Produces a permanent regression asset | Yes, every crash becomes a saved seed | Yes, every failure becomes a saved shrunk example | Yes, by construction | No, it measures existing tests rather than adding new ones | No |
| Catches a correct-looking but semantically wrong answer | Only with an explicit or differential oracle added | Yes, directly, that is what a property states | Yes, for the specific cases enumerated | Indirectly, by proving the suite would catch an injected wrong answer | Yes, if the reviewer notices |

Reading of the table. Fuzz testing and property-based testing overlap the most
and are frequently used together on the same codebase for different layers,
byte-level parsers get a fuzzer, typed domain logic gets a property test.
Table-driven tests remain the cheapest and most precise tool for the finite
set of cases a human can already name. Mutation testing answers a different
question entirely, not whether an input breaks the code but whether the
existing tests would notice if the code were subtly wrong, and the two
techniques compose rather than compete, see dimension 13.

## 13. Related and incompatible patterns

- **Property-based testing.** The closest sibling and, in modern engines,
  increasingly the same underlying machinery pointed at typed values instead
  of raw bytes. Reach for property-based testing when the domain is naturally
  typed and a clear invariant can be stated, reach for byte-level fuzzing when
  the boundary genuinely receives raw, untrusted bytes, such as a network
  packet or a file format, before any typed parsing has happened. See the
  property-based-test entry.
- **Mutation testing.** A different technique that shares only a name-root
  with fuzz testing and is frequently confused with it by newcomers. Mutation
  testing mutates the code under test and reuses the existing test suite as
  the oracle, to answer whether the suite would catch an injected bug. Fuzz
  testing mutates the input and needs no pre-existing suite. The two compose
  well in sequence, run a mutation-testing tool to find where the assertions
  inside a fuzz target's oracle are weak, then strengthen those specific
  assertions. See the mutation-test entry.
- **Fault injection.** A related discipline that perturbs the environment, a
  dependency failing, a disk filling up, a network partition, rather than the
  input data. Fuzzing and fault injection are complementary layers of the same
  larger resilience-testing effort and are often run by the same team as
  separate campaigns. See the fault-injection entry.
- **Golden master, or characterization testing.** Frequently used together
  with fuzzing in a differential setup, the golden master, an older trusted
  implementation or a previous version of the same code, becomes the oracle a
  fuzzed input is checked against instead of an explicit hand-written
  assertion. See the golden-master entry.
- **Contract testing.** Conflicts in scope rather than in technique. Contract
  testing verifies that two services agree on an interface's shape and
  semantics at integration boundaries, typically over a small, curated set of
  example interactions. Fuzzing that same boundary with an open-ended input
  search is a different, complementary layer, but the two should not be
  confused as substitutes, a passing contract test says nothing about
  behaviour on malformed input the contract never anticipated. See the
  contract-test entry.
- **Continuous integration and pull-request gating.** Composes carefully, not
  automatically. An unbounded, hours-long fuzz campaign does not fit a
  pull-request feedback loop and must be split into a fast corpus-replay step
  that runs on every change, plus a separately scheduled, long-running
  campaign, exactly the split OSS-Fuzz itself uses at scale.
- **Static analysis and symbolic execution.** Complementary rather than
  competing. Static analysis and white-box symbolic execution can reach code
  paths a random or coverage-guided search may take a long time to stumble
  into, particularly narrow, deeply nested conditions, and several modern
  fuzzing research systems hybridise the two, a grey-box fuzzer alone remains
  the practical default because it needs far less setup and tolerates
  imprecise models of the program.

## 14. Refactoring path in and out

Introducing fuzzing into code that has none. Ordered steps.

1. Identify the specific function that consumes untrusted or externally
   produced input directly, not the module or file it lives in, the single
   function. A parser's top-level `parse(bytes)` entry point is the usual
   candidate, not the class that owns it.
2. Confirm the function can be called in isolation, with no hidden global
   state and no I/O beyond what the input itself represents. If it cannot,
   extract the pure logic first, the same extraction the do-not-do-slow-I/O
   guidance in dimension 4 calls for, before writing a single line of fuzzing
   code.
3. Write the thinnest possible target, accept the engine's native input
   shape, byte slice, `*testing.F` callback, `TestOneInput(data)`, and call
   straight into the extracted function. Add nothing else at this stage.
4. Collect a seed corpus of a handful of real, valid inputs the function is
   known to handle correctly today. Add them via the engine's seeding
   mechanism, `f.Add()` in Go, files under a corpus directory for libFuzzer
   and cargo-fuzz.
5. Run the seed corpus as an ordinary test first, with fuzzing switched off,
   to confirm the target itself is correct and the seeds all pass before any
   mutation begins.
6. Turn on the open-ended search for a short, bounded time locally, watch for
   the first failure, and read it before trusting the setup further. A
   target with a bug in it, for example one that swallows exceptions instead
   of propagating them, will falsely report a clean run forever.
7. Add an explicit oracle beyond crash-freedom where a cheap one exists, a
   round-trip assertion, a bounds invariant, or a differential comparison
   against a second implementation, per dimension 8 and dimension 11.
8. Wire the corpus-replay half into ordinary CI as a fast, deterministic step
   on every change, and schedule the open-ended search separately, on a
   nightly job, a dedicated always-on service, or as part of a release gate,
   never as a blocking step on every pull request.
9. Fix, or explicitly and visibly waive with a stated reason, every finding
   before merging it into a passing state. A finding silently deleted rather
   than fixed or waived defeats the entire investment.

Removing the pattern when it stops earning its place. Signals include the
target function being retired, the input format no longer accepting
untrusted data, for example a decoder that used to face the network now only
ever reads a value the same process just wrote, or a campaign that has run
for a long time with a stable, unchanging corpus and found nothing new for
months against actively changing code.

1. Confirm the boundary genuinely no longer receives untrusted input, do not
   remove fuzzing from a parser merely because it has been quiet, since
   quiet and safe are not the same thing, see dimension 11.
2. If the boundary is retired entirely, delete the fuzz target along with the
   dead code it exercised, and keep the accumulated minimised crash corpus as
   an ordinary regression suite if the underlying logic is being kept in any
   form, since those inputs remain valid tests of whatever code survives.
3. If the campaign is simply being descoped for cost reasons rather than
   retired, downgrade from an always-on service to a scheduled, lower-frequency
   job before removing it outright, and say so explicitly in the target's own
   comment or the CI configuration, so a future reader understands the
   coverage gap was a deliberate trade-off rather than an oversight.

## 15. Testing and verification

This dimension is unusual for this pattern because fuzz testing is itself a
testing technique. What is discussed here is how to verify the fuzzing setup
is doing real work, not how to test unrelated code with it.

Easier because of the pattern, once it exists.

- Every crash the engine finds arrives pre-minimised into a small, readable,
  deterministic reproducer, which is often a better starting example test
  than anything a human would have hand-written, because it is guaranteed to
  actually trigger the specific failure.
- The generated corpus becomes a growing, self-curating regression suite with
  no ongoing authorship cost, each new interesting input the engine finds is
  automatically retained.
- Memory-safety verification in an unsafe language gets dramatically stronger
  for a modest one-time setup cost, compared to relying on manual review
  alone to catch buffer overruns and use-after-free defects.

Harder because of the pattern.

- Verifying the target itself is correct is a genuine extra step, a
  buggy target that swallows an exception, or that never reaches the
  intended code path, produces a false sense of coverage that is worse than
  having no fuzz target at all, because it looks like safety without being
  safety.
- Reproducing a failure outside the fuzzing engine's own environment can be
  awkward when the failure depends on a specific sanitizer build, a specific
  compiler flag set, or engine-internal state, which is why minimisation and
  a saved, replayable input file matter so much.

Techniques that apply.

- **Mutation-testing the fuzz target's own oracle.** Deliberately inject a
  known bug into the code under test and confirm the fuzzer finds it within a
  reasonable time budget. This is the fuzzing equivalent of mutation testing
  applied to the target itself, and it is the only reliable way to know a
  target that has found nothing is actually searching well rather than
  silently broken.
- **Coverage plateau tracking.** Record the coverage percentage or edge count
  over the life of a campaign. A plateau reached quickly and never exceeded
  again, even as the code under test changes, is the practical symptom of the
  corpus-rot failure mode in dimension 11 and should trigger a seed refresh.
- **Sanitizer combination.** Run the same fuzz target under AddressSanitizer,
  UndefinedBehaviorSanitizer, and where available MemorySanitizer, since each
  catches a different, non-overlapping class of memory-safety defect, and
  libFuzzer explicitly supports compiling with any of them alongside the
  fuzzer instrumentation.
- **Differential replay against a second engine or a second version.** After
  fixing a discovered bug, replay the full minimised-crash corpus against the
  patched code as an ordinary regression test, and, where a second trusted
  implementation exists, replay the same corpus against it as a sanity check
  that the fix did not merely relocate the bug.

## 16. Observability signals

What to record for a running or scheduled fuzzing campaign.

- Executions per second, the single most direct signal of target health.
  A sudden drop usually means the target started doing unexpectedly slow
  work, real I/O leaking into the target, an accidental infinite loop that
  the engine is timing out on repeatedly rather than a genuine hang report.
- Coverage percentage or raw edge count over time, ideally as a time series
  rather than a single snapshot, so a plateau is visible as a plateau rather
  than assumed to be a healthy steady state.
- Corpus size, both seed and generated, and its growth rate. A corpus that
  stops growing while the code under test keeps changing is the corpus-rot
  symptom from dimension 11.
- Crash count, deduplicated by stack signature or crash type, never a raw
  count of individual crashing inputs, since a single root cause commonly
  produces hundreds of superficially different crashing inputs before
  minimisation and deduplication collapse them.
- Time since the last new finding, per target. A target that used to find
  bugs regularly and has gone quiet for an unusually long time against an
  actively changing codebase deserves the same suspicion as a metric that
  suddenly flatlines in production monitoring.
- Wall-clock campaign duration actually completed versus the intended budget,
  since a campaign that keeps getting killed early by an infrastructure
  timeout never gets the deep search time the pattern depends on.

A healthy instance on a dashboard. Executions per second stays roughly stable
across runs of the same target. Coverage climbs steadily on a fresh corpus and
then flattens gently as the input space genuinely saturates, rather than
flattening abruptly within seconds of starting. Corpus size grows in step
with code changes to the target. Crash findings, when they occur, are
triaged and closed within a bounded window rather than accumulating.

A failing instance. Executions per second near zero, most often unrelated I/O
or excessive per-call setup inside the target. Coverage flat from the very
first minute of every run, most often a broken target that never actually
reaches the intended code, an oracle that always trivially passes, or a seed
corpus that was never loaded. A crash-report count climbing with no
corresponding decrease over time, meaning triage capacity has been exceeded
and findings are silently piling up rather than being acted on.

## 17. Security and privacy implications

Fuzz testing sits closer to the centre of security engineering than almost
any other pattern in this catalog, and its implications run in both
directions, as a defensive tool and as a genuine operational risk surface in
its own right if handled carelessly.

**The primary defensive value.** Fuzzing is explicitly credited, by the
project's own published account, with a large share of the remote code
execution and privilege escalation bugs found in real software historically
(github.com/google/AFL, verified 2026-08-02, describing fuzzing generally as
responsible for the vast majority of such findings to date). Running a
fuzzer against any code that parses attacker-reachable input, before an
attacker does the equivalent search independently, is one of the highest
return-on-effort security investments available for memory-unsafe code, and a
meaningful, if less dramatic, investment even in memory-safe languages, where
it still finds logic bugs, denial-of-service inputs, and unhandled-exception
paths.

**Corpus and crash-report handling as sensitive data.** A generated fuzzing
corpus, and especially the set of minimised crash inputs, is effectively a
list of exploit primitives for whatever bugs remain unfixed at any given
moment. Storing this corpus in a public repository, or in a CI artifact
readable by anyone with repository access, before the corresponding defects
are patched, discloses working attack material ahead of a fix. Treat an
active, unpatched crash corpus with the same access controls as an unpatched
vulnerability report, and only widen access once the underlying defect is
resolved and released.

**Compute cost as a denial-of-service surface, inward.** A fuzzing campaign
is, by construction, a search for inputs that make the target behave badly,
which sometimes means an input that makes the target consume unbounded
memory or CPU rather than crash outright. If the target under test is a
network-facing service rather than an isolated library call, running that
service's real handler inside a fuzzing loop can itself produce resource
exhaustion on the machine running the campaign, which is a genuine
operational hazard to plan capacity around, not a security finding about the
target.

**False confidence as its own risk.** Because the discipline lends itself so
naturally to a checkbox mentality, treating fuzzing as a compliance box
rather than a genuine search, the single largest security-adjacent risk of
the pattern is organisational rather than technical, a short, token fuzzing
run treated as equivalent to a genuine, sustained campaign, satisfying a
requirement while leaving the actual risk largely unaddressed. This is
engineering judgement rather than a sourced claim, but it follows directly
from the proof-of-absence limitation already established in dimension 3 and
dimension 11, and it is the single most important caveat to communicate to
anyone adopting the pattern for security assurance purposes.

On privacy, the pattern is close to neutral in itself, with one practical
caveat that mirrors dimension 16's logging advice. A crash report or a
minimised failing input can, in some codebases, incidentally contain
fragments of real data if the seed corpus was built from production samples
rather than synthetic ones. Prefer synthetic or clearly anonymised seed
material, and treat any crash artifact derived from a production-sourced seed
with the same handling rules as the production data it was drawn from.

## 18. References

1. Barton P. Miller, Lars Fredriksen, Bryan So. "An Empirical Study of the
   Reliability of UNIX Utilities". *Communications of the ACM*, volume 33,
   issue 12, December 1990. Origin of the term "fuzz" and the founding
   measurement that 25 to 33 percent of tested UNIX utilities crashed or
   hung on random input, summarized and cited via Wikipedia, "Fuzzing",
   https://en.wikipedia.org/wiki/Fuzzing verified 2026-08-02.
2. Wikipedia contributors. "Fuzzing".
   https://en.wikipedia.org/wiki/Fuzzing verified 2026-08-02. Source for the
   Miller history, the mutation-based versus generation-based distinction,
   grey-box fuzzing, and the Shellshock and Heartbleed discovery accounts.
3. LLVM Project. "libFuzzer, a library for coverage-guided fuzz testing".
   https://llvm.org/docs/LibFuzzer.html verified 2026-08-02. Source for
   libFuzzer's in-process design, the `-fsanitize=fuzzer` compiler flag,
   Clang integration since version 6.0, and the named list of projects it
   has found bugs in.
4. Google. "OSS-Fuzz documentation".
   https://google.github.io/oss-fuzz/ verified 2026-08-02. Source for the
   2016 launch following Heartbleed, the reported vulnerability and bug
   counts, the four supported fuzzing engines, ClusterFuzz, and the
   approximately 1,000 integrated projects.
5. Michal Zalewski and contributors. "American Fuzzy Lop (AFL)".
   https://github.com/google/AFL verified 2026-08-02. Source for AFL's
   authorship, its description of itself as an instrumentation-guided
   genetic algorithm, and the claim that fuzzing is responsible for the
   majority of remote code execution and privilege escalation bugs found to
   date.
6. The Go Authors. "Go Fuzzing".
   https://go.dev/security/fuzz/ verified 2026-08-02. Source for the Go
   1.18 native fuzzing addition, `testing.F`, `go test -fuzz`, seed and
   generated corpus behaviour, and automatic minimisation with
   `-fuzzminimizetime`.
7. The Rust Fuzz Project. "cargo-fuzz, The Rust Fuzz Book".
   https://rust-fuzz.github.io/book/cargo-fuzz.html verified 2026-08-02.
   Source for cargo-fuzz being a wrapper around libFuzzer via the
   libfuzzer-sys crate, and for structure-aware fuzzing via the `arbitrary`
   crate.
8. Google. "Atheris, a coverage-guided Python fuzzing engine".
   https://github.com/google/atheris verified 2026-08-02. Source for
   Atheris's libFuzzer basis, `instrument_imports`, `TestOneInput`, and
   `FuzzedDataProvider`.
9. Code Intelligence. "Jazzer, coverage-guided fuzzing for the JVM".
   https://github.com/CodeIntelligenceTesting/jazzer verified 2026-08-02.
   Source for Jazzer's libFuzzer-derived design, JaCoCo-based bytecode
   coverage instrumentation, and the `@FuzzTest` annotation.

## Code examples

Three languages, each verified to actually run. Go and Python demonstrate
complete, live fuzzing runs that found a real, deliberately planted defect in
this session, with the transcripts described exactly as observed. Rust
demonstrates the idiomatic `cargo-fuzz` target shape as it would appear in a
real project, plus a compiled and executed standalone reproduction of the
same defect class, because no libFuzzer-linked nightly toolchain was
available to run `cargo fuzz run` itself in this environment, and that
limitation is stated here rather than implied away.

### Go

Go's native fuzzing needs no external dependency beyond the standard `testing`
package, present since Go 1.18 (go.dev/security/fuzz, verified 2026-08-02).
The target below chunks a string into fixed-width pieces and has a genuine
boundary bug, it panics whenever the string length is not an exact multiple
of the chunk size.

```go
package parseutil

import "testing"

// Chunks splits s into fixed-size pieces. It has a boundary bug when
// len(s) is not a multiple of size, which crashes rather than truncating.
func Chunks(s string, size int) []string {
	var out []string
	for i := 0; i < len(s); i += size {
		out = append(out, s[i:i+size])
	}
	return out
}

func FuzzChunks(f *testing.F) {
	f.Add("abcdef", 3) // divides evenly, passes, hides the real bug
	f.Fuzz(func(t *testing.T, s string, size int) {
		if size <= 0 || size > 64 {
			t.Skip()
		}
		defer func() {
			if r := recover(); r != nil {
				t.Fatalf("Chunks panicked on s=%q size=%d. %v", s, size, r)
			}
		}()
		Chunks(s, size)
	})
}
```

Run with `go test -run xxx -fuzz FuzzChunks -fuzztime 20s .`. The seed corpus
entry, `"abcdef"` with size 3, passes cleanly because six divides evenly by
three, exactly the kind of case a human author would write by hand and trust.
Within a fraction of a second of open-ended mutation the engine found a
genuine failure, minimised it, and wrote it to disk. The actual output from
this run.

```
fuzz. elapsed. 0s, gathering baseline coverage. 1/1 completed, now fuzzing with 12 workers
fuzz. minimizing 41-byte failing input file
--- FAIL. FuzzChunks (0.02s)
    --- FAIL. FuzzChunks (0.00s)
        chunks_test.go.13. Chunks panicked on s="0" size=60.
            runtime error. slice bounds out of range [.60] with length 1
    Failing input written to testdata/fuzz/FuzzChunks/f05f9b20cf675c1e
    To re-run.
    go test -run=FuzzChunks/f05f9b20cf675c1e
```

The minimised reproducer, `s="0"` with `size=60`, is a single-character
string with a chunk size far larger than the string itself, exactly the
boundary case the hand-written seed never exercised. That file under
`testdata/fuzz/` is now a permanent regression test that plain `go test`,
with no `-fuzz` flag, runs on every future build.

### Python

No external fuzzing library was available in this environment (`import
atheris` fails with `ModuleNotFoundError`), so the example below is an
honest, stdlib-only random mutation target rather than a claim about
Atheris, which is the real coverage-guided engine for Python and is
described in dimension 9's implementation variants and referenced in
dimension 8. The target below lacks Atheris's coverage feedback but
demonstrates the same underlying idea of automatically generating many
candidate inputs against an explicit oracle, and it genuinely ran and
genuinely found the bug described below.

```python
def percent_decode(s: str) -> str:
    """Decode a percent-encoded string. Buggy, assumes every '%' is
    followed by two valid hex digits and never checks bounds."""
    out = []
    i = 0
    while i < len(s):
        c = s[i]
        if c == "%":
            hex_pair = s[i + 1:i + 3]
            out.append(chr(int(hex_pair, 16)))
            i += 3
        else:
            out.append(c)
            i += 1
    return "".join(out)
```

```python
import random
import string
import sys

from target import percent_decode

CHARSET = string.ascii_letters + string.digits + "%_- "


def random_input(rng: random.Random, max_len: int = 12) -> str:
    n = rng.randint(0, max_len)
    return "".join(rng.choice(CHARSET) for _ in range(n))


def run(seed: int, iterations: int) -> str | None:
    rng = random.Random(seed)
    for candidate_seed in ("hello", "%20", "a%2fb", ""):
        percent_decode(candidate_seed)  # seed corpus, all pass
    for _ in range(iterations):
        candidate = random_input(rng)
        try:
            percent_decode(candidate)
        except (ValueError, IndexError) as exc:
            return f"crash on {candidate!r}. {type(exc).__name__}. {exc}"
    return None


if __name__ == "__main__":
    for seed in range(2000):
        result = run(seed, iterations=200)
        if result:
            print(f"FOUND (seed={seed}). {result}")
            sys.exit(1)
    print("no crash found in budget")
```

Actual output from running `python3 fuzz_harness.py` against the two files
above.

```
FOUND (seed=0). crash on '1fH %Z'. ValueError. invalid literal for int() with base 16. 'Z'
```

The very first random seed produced a string containing `%Z`, a percent sign
followed by a character that is not valid hexadecimal, which the function
propagates as an unhandled `ValueError` instead of treating as a malformed
input the caller should be told about explicitly. This is exactly the kind
of interior-of-the-format defect dimension 2 describes, the seed corpus of
plausible, well-formed strings never touches it, and a genuinely
coverage-guided engine such as Atheris would find the same class of failure,
almost certainly faster, using SanitizerCoverage-equivalent Python bytecode
instrumentation rather than pure chance.

### Rust

The idiomatic real-world shape, as it would appear in a `fuzz/fuzz_targets/`
directory managed by `cargo fuzz init`, using the `libfuzzer-sys` crate cargo-
fuzz wraps (rust-fuzz.github.io/book/cargo-fuzz.html, verified 2026-08-02).

```
#![no_main]
use libfuzzer_sys::fuzz_target;

fuzz_target!(|data: &[u8]| {
    if let Ok(s) = std::str::from_utf8(data) {
        let _ = chunks(s, 4); // size fixed here, a real target would also
                              // consume size from data via Arbitrary
    }
});
```

That target was not executed, because this environment has no `rustup`
nightly toolchain and no `cargo-fuzz` binary installed (`rustc --version`
succeeds, `rustup toolchain list` and `which cargo-fuzz` both fail). To keep
the demonstration honest rather than merely aspirational, the same boundary
defect was compiled with plain `rustc` and driven by a small, deterministic
stand-in for the mutation loop, which is not a substitute for coverage-guided
fuzzing but does exercise and confirm the identical bug class.

```rust
fn chunks(s: &str, size: usize) -> Vec<&str> {
    let bytes = s.as_bytes();
    let mut out = Vec::new();
    let mut i = 0;
    while i < bytes.len() {
        out.push(std::str::from_utf8(&bytes[i..i + size]).unwrap());
        i += size;
    }
    out
}

fn main() {
    assert_eq!(chunks("abcdef", 3), vec!["abc", "def"]);
    println!("seed corpus ok. {:?}", chunks("abcdef", 3));

    let result = std::panic::catch_unwind(|| chunks("abcdef", 4));
    match result {
        Ok(v) => println!("no crash. {:?}", v),
        Err(_) => println!("FOUND. chunks(\"abcdef\", 4) panics, boundary bug confirmed"),
    }
}
```

Compiled with `rustc -O main.rs -o chunks_demo` and run, the actual output.

```
seed corpus ok. ["abc", "def"]
thread 'main' panicked at main.rs.9.44.
range end index 8 out of range for slice of length 6
FOUND. chunks("abcdef", 4) panics, boundary bug confirmed
```

The same shape of boundary defect that Go's fuzzer discovered through open
search, six characters split into groups of four leaves a two-character
remainder shorter than the requested slice, is reproduced here by direct
construction. A real `cargo fuzz run` session against the `fuzz_target!` above
would be expected to discover an equivalent failing input on its own within
seconds, given how shallow the defect is, but that specific claim was not
verified by execution in this environment and is stated as an expectation,
not as an observed result.
