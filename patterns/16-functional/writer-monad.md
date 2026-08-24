---
name: Writer Monad
slug: writer-monad
family: 16-functional
category: Functional
aliases: [Writer, WriterT, MonadWriter, Accumulating Output Monad]
first_described: "Jones 1995"
maturity: established
related: [monad, monoid, applicative, reader-monad, state-monad, result-either]
incompatible_with: [mutable-global-logger, unbounded-log-accumulation, effectful-logging-only]
verified: 2026-08-02
---

# Writer Monad

## 1. Name, aliases, and lineage

The canonical name is Writer Monad. The name used in Haskell libraries is
usually `Writer`, `WriterT`, or `MonadWriter`. GHC `mtl` documentation names
`Control.Monad.Writer.Strict`, lists a `MonadWriter` class, a `Writer` monad,
and a `WriterT` monad transformer, and records the core operations `writer`,
`tell`, `listen`, and `pass`
(https://downloads.haskell.org/ghc/8.6.3/docs/html/libraries/mtl-2.2.2/Control-Monad-Writer-Strict.html,
verified 2026-08-02). The Hackage `transformers` documentation describes
`WriterT` as a transformer that adds collection of outputs, such as a count or
string output, to another monad, and states that the strict version builds its
output strictly
(https://hackage-content.haskell.org/package/transformers-0.6.3.0/docs/Control-Monad-Trans-Writer-Strict.html,
verified 2026-08-02).

The lineage should be stated with care. The GHC `mtl` page says the module is
inspired by Mark P. Jones, "Functional Programming with Overloading and
Higher-Order Polymorphism", Advanced School of Functional Programming, 1995
(https://downloads.haskell.org/ghc/8.6.3/docs/html/libraries/mtl-2.2.2/Control-Monad-Writer-Strict.html,
verified 2026-08-02). Mark P. Jones's publication page lists that paper as a
1995 Springer Lecture Notes in Computer Science contribution
(https://web.cecs.pdx.edu/~mpj/pubs.html, verified 2026-08-02). DBLP lists the
same paper in *Advanced Functional Programming* 1995, pages 97 to 136
(https://dblp.org/rec/conf/afp/Jones95, verified 2026-08-02). This entry uses
Jones 1995 as the first described source for the library shape, rather than
claiming a single inventor of the mathematical idea.

The common aliases are **Writer**, **WriterT**, **MonadWriter**,
**accumulating output monad**, **logging monad**, and **append-only output
context**. The word "logging" needs care. Writer can model log-like output, but
it is not a replacement for an operational logging system. Its output is a value
returned by the computation. It is not automatically sent to a file, collector,
console, trace backend, or security audit store.

Engineering judgement. This catalog treats Writer Monad as a software pattern
when a computation returns both a result and an append-only output, and when
composition combines those outputs through a monoid. That shape appears in
Haskell `mtl`, Typelevel Cats, fp-ts, and Mathlib documentation
(https://downloads.haskell.org/ghc/8.6.3/docs/html/libraries/mtl-2.2.2/Control-Monad-Writer-Strict.html,
verified 2026-08-02;
https://typelevel.org/cats/datatypes/writer.html, verified 2026-08-02;
https://gcanti.github.io/fp-ts/modules/Writer.ts.html, verified 2026-08-02;
https://leanprover-community.github.io/mathlib4_docs/Mathlib/Control/Monad/Writer,
verified 2026-08-02).

## 2. Problem and context

A computation has a primary result and also produces append-only side output
that should remain available to the caller. The side output may be explanatory
trace steps, validation notes, generated warnings, documentation fragments,
query planning facts, rewrite statistics, accumulated cost, or a list of
decisions. The computation is still best understood as pure or locally
controlled. The output is not the main return value, but it should travel with
that value.

Without this pattern, teams often pick one of four shapes. They return a pair
from every function by hand. They pass a mutable list or builder down the call
graph. They write to a process logger and lose the ability to test the output as
data. Or they ignore the output until a later debugging session asks why the
program made a decision. Each shape solves part of the problem and damages
another part. Manual pairs make every call site unpack and repack output.
Mutable accumulators hide order and make tests sensitive to aliasing.
Operational loggers are good for production visibility, but poor for local
composition and deterministic unit tests. Dropping the output loses information
that may be valuable at the boundary.

Writer Monad gives a single composition rule. A computation of type
`Writer<W, A>` produces an `A` and a `W`. The `W` type must support a neutral
empty value and an append operation. In functional vocabulary, that requirement
is a monoid. The repository has a separate Monoid entry for that contract. In a
Writer chain, `pure` produces the value with empty output. `bind` runs the
first computation, runs the next computation chosen from the first value, and
combines the two outputs in order. `tell` appends output without returning a
useful domain value. `listen` exposes the output of a subcomputation as part of
its value. `pass` lets a computation return a function that edits its own
output.

The context matters. Writer is strongest when the output is bounded,
append-only, and part of the result contract. It is weak when output volume is
unbounded, when output must be flushed during the computation, or when the
consumer needs live streaming. A compiler pass that collects a few warnings can
fit. A server request handler that writes megabytes of security events should
use the service logging and audit pipeline. A parser that emits a small trace
for a failing test can fit. A payment system that must write an audit event even
if later code crashes should not rely on Writer alone.

Engineering judgement. The design center is explainable computation, not
logging infrastructure. Reach for Writer when the output belongs in the return
value. Reach for a logger, event sink, audit service, or stream when the output
must exist outside the returned value.

## 3. Forces

This section is engineering judgement unless a cited source names a concrete
API.

- **Coupling.** Favoured between domain code and the output transport. A
  function can produce notes or warnings without importing a logger, metrics
  client, file handle, or callback.
- **Consistency.** Favoured when every step uses the same monoid. Output order
  follows composition order. Sacrificed when the output type has surprising
  append semantics, such as a set that discards duplicates where order matters.
- **Latency.** Mixed. Writer can defer all output handling until the end, which
  keeps inner code simple. It can also build large intermediate values and delay
  backpressure. The Hackage `transformers` documentation says `WriterT` gives
  limited access to output during computation and points to State for more
  general access
  (https://hackage-content.haskell.org/package/transformers-0.6.3.0/docs/Control-Monad-Trans-Writer-Strict.html,
  verified 2026-08-02).
- **Memory cost.** Sacrificed when logs grow with input size. A long chain that
  appends lists or strings can retain more data than an explicit streaming
  sink. Strict and lazy variants move the cost shape, but neither removes the
  cost.
- **Operability.** Mixed. Writer output is easy to inspect in tests, but
  invisible to production tooling until the runner emits it, summarizes it, or
  converts it to telemetry.
- **Cost of change.** Favoured when adding a new explanatory note to an
  existing pipeline. Sacrificed when changing the output type, because every
  producer and every append operation must agree on the new monoid.
- **Team topology.** Favoured when platform code defines a narrow output value,
  such as `Warnings`, and feature teams add computations that emit those
  warnings. Sacrificed if teams treat the output value as a shared dumping
  ground for unrelated diagnostics.
- **Cognitive load.** Mixed. Readers fluent in `map`, `flatMap`, `tell`, and
  `listen` see the program as a plain computation with accumulated output.
  Readers new to the pattern may look for side effects and miss that the output
  is returned by `run`.
- **Debuggability.** Favoured in deterministic code. A unit test can assert the
  result and the exact explanatory trail without patching a logger.
- **Failure semantics.** Sacrificed when combined with short-circuiting effects.
  Depending on transformer ordering, output from failed branches may be kept or
  discarded. That decision must be explicit.

Writer favours local reasoning, deterministic diagnostics, and pure
composition. It sacrifices streaming behavior, memory predictability, and
operational visibility unless the runner handles those concerns.

## 4. Applicability and non-applicability

Reach for Writer Monad when these conditions hold.

- A computation has a main result plus append-only auxiliary output.
- The auxiliary output is bounded enough to hold in memory for one run.
- The output has a lawful monoid, such as a list of warnings, a sum of costs, a
  product of probabilities, a string builder, or a domain-specific accumulator.
- Output order is tied to computation order and should be tested.
- The caller wants the output as data, not as a side effect already sent to an
  external system.
- A pure pipeline needs instrumentation for tests, previews, explanations, or
  generated reports.
- You need to collect non-fatal warnings while still returning a successful
  value.
- You want a narrow adapter around an existing Writer-like library, such as
  Haskell `MonadWriter`, Cats `Writer`, or fp-ts `Writer`
  (https://downloads.haskell.org/ghc/8.6.3/docs/html/libraries/mtl-2.2.2/Control-Monad-Writer-Strict.html,
  verified 2026-08-02;
  https://typelevel.org/cats/datatypes/writer.html, verified 2026-08-02;
  https://gcanti.github.io/fp-ts/modules/Writer.ts.html, verified 2026-08-02).

Do NOT reach for Writer Monad in these cases.

- **The output must be durable before the function returns.** Use an audit log,
  database write, message bus, or transactional outbox. Writer output can vanish
  if the caller throws it away.
- **The output is unbounded or input-proportional.** Use a stream, iterator,
  callback, file writer, or bounded ring buffer. Writer collects before the
  caller can consume.
- **The output must be observed live.** Use structured logging, tracing, or an
  event sink. Writer gives final output, not live emission.
- **The output type has no honest empty value.** Without a neutral output,
  `pure` must invent data. Use an explicit pair-returning API or a semigroupal
  accumulator at known non-empty points.
- **The next step needs to inspect and change the full output often.** Use
  State or an explicit accumulator. The `transformers` documentation states
  that WriterT has limited access to output during computation and points to
  State for broader access
  (https://hackage-content.haskell.org/package/transformers-0.6.3.0/docs/Control-Monad-Trans-Writer-Strict.html,
  verified 2026-08-02).
- **Output ordering is not meaningful.** A commutative summary, counter, or
  metric may be clearer as a fold or metric aggregation.
- **The team only needs normal production logs.** Use the logging stack already
  connected to retention, redaction, routing, and alerting.
- **Failure must keep some logs and discard others under precise policy.** Use
  a named result type with explicit fields, or choose transformer ordering and
  test it directly.
- **Performance depends on tight loops.** Passing a mutable local builder or
  using an optimized fold can be clearer and faster.
- **The output contains secrets.** Avoid accumulating sensitive text in memory.
  Emit redacted summaries through the security-approved path.

Non-applicability list summary. Avoid Writer when output must be durable,
live, huge, secret, frequently inspected during the run, or governed by failure
policy that the type stack does not make clear.

## 5. Structure

The participants are named by the role they play.

- **Output monoid.** The type of accumulated output. It supplies an empty value
  and an append operation. Examples are `List<Warning>`, `String`, `Sum<Int>`,
  and a domain record whose fields append independently.
- **Writer computation.** A value that, when run, returns a pair of domain
  result and accumulated output. In fp-ts, the `Writer<W, A>` interface is a
  nullary function returning `[A, W]`
  (https://gcanti.github.io/fp-ts/modules/Writer.ts.html, verified
  2026-08-02). In Cats, `Writer[L, A]` is described as a data type that
  produces a tuple containing a log value and a result value
  (https://typelevel.org/cats/datatypes/writer.html, verified 2026-08-02).
- **Emitter.** The operation that contributes output without a domain value.
  Haskell `mtl` names it `tell`, and fp-ts also documents `tell`
  (https://downloads.haskell.org/ghc/8.6.3/docs/html/libraries/mtl-2.2.2/Control-Monad-Writer-Strict.html,
  verified 2026-08-02;
  https://gcanti.github.io/fp-ts/modules/Writer.ts.html, verified
  2026-08-02).
- **Binder.** The operation that sequences dependent computations, extracts the
  first value, feeds it to the next function, and appends both outputs.
- **Runner.** The boundary that executes or unwraps the Writer and decides what
  to do with the output. It may return both fields, return only the value,
  return only the output, log a summary, or fail if warnings exist.
- **Listener.** Optional participant. It exposes a subcomputation's output as
  part of the result while preserving output. Haskell and fp-ts both document
  `listen`
  (https://downloads.haskell.org/ghc/8.6.3/docs/html/libraries/mtl-2.2.2/Control-Monad-Writer-Strict.html,
  verified 2026-08-02;
  https://gcanti.github.io/fp-ts/modules/Writer.ts.html, verified
  2026-08-02).
- **Output editor.** Optional participant. `pass` or `censor` modifies output
  from a subcomputation. fp-ts documents `censor`, `pass`, `evaluate`, and
  `execute`
  (https://gcanti.github.io/fp-ts/modules/Writer.ts.html, verified
  2026-08-02).

The key relationship is that output does not flow through every domain
function as a named parameter. It is carried by the context. The binder owns the
append rule. The runner owns the interpretation of the final output.

## 6. ASCII structure diagram

```text
   +===================+      emits       +=====================+
   | Domain Step A     | ===============> | Output Monoid       |
   |===================|                  |=====================|
   | A -> Writer<W,B>  |                  | empty, append       |
   +===================+                  +=====================+
             |
             | bind passes B
             v
   +===================+      emits       +=====================+
   | Domain Step B     | ===============> | Output Segment      |
   |===================|                  |=====================|
   | B -> Writer<W,C>  |                  | w2                  |
   +===================+                  +=====================+
             |
             | runner unwraps
             v
   +===========================================================+
   | Writer<W,C>                                               |
   |===========================================================|
   | run() -> (value: C, output: append(w1, w2))               |
   +===========================================================+

   The domain result moves through bind. The output segments combine by the
   monoid operation. No mutable logger is passed through the steps.
```

## 7. Dynamics

Writer's runtime flow is easiest to see as pair construction plus pair
combination. A pure value starts with empty output. An emitter creates a unit
value with a non-empty output segment. Bind runs two computations and appends
their outputs.

```text
Client        Runner        Step A          Step B          Output Monoid
  |             |              |               |                  |
  |== run =====>|              |               |                  |
  |             |== call =====>|               |                  |
  |             |<== (b,w1) ===|               |                  |
  |             |== b ========================>|                  |
  |             |<== (c,w2) ===================|                  |
  |             |== append(w1,w2) ===============================>|
  |             |<== w12 =========================================|
  |<== (c,w12)=|              |               |                  |
```

The same idea with `listen` has one more turn. The subcomputation's output is
copied into the domain value while still remaining in the final output.

```text
listen(subprogram)
  |
  | run subprogram -> (value, output)
  |
  v
returns ((value, output), output)
```

With `pass`, the subprogram returns a value and an output-editing function. The
runner applies the function to the subprogram's output and keeps the value.

```text
pass(subprogram)
  |
  | run subprogram -> ((value, edit), output)
  |
  v
returns (value, edit(output))
```

Engineering judgement. The diagrams also show the core hazard. The output is
available only when the runner gets control. If the caller needs live emission,
the pattern is solving the wrong problem.

## 8. Implementation variants

**Pure pair wrapper.** The smallest Writer is a wrapper around a pair. `pure`
returns `(value, empty)`. `flatMap` runs the next function and appends the two
outputs. This form is clear in TypeScript, Python, Java, Go, Rust, and Swift.
It is the best teaching form and a good local pattern when a project does not
already use a functional library.

**Haskell `MonadWriter`.** The `mtl` form defines a type class constrained by
`Monoid w` and `Monad m`, with `writer`, `tell`, `listen`, and `pass`
(https://downloads.haskell.org/ghc/8.6.3/docs/html/libraries/mtl-2.2.2/Control-Monad-Writer-Strict.html,
verified 2026-08-02). This lets code request writer capability without naming
one concrete stack.

**WriterT transformer.** The transformer form adds output collection to another
effect. Hackage documents `WriterT w m a` as a transformer whose runner returns
`m (a, w)`
(https://hackage-content.haskell.org/package/transformers-0.6.3.0/docs/Control-Monad-Trans-Writer-Strict.html,
verified 2026-08-02). This form composes with I/O, errors, async, or state, but
the order of transformers changes failure and output retention behavior.

**Strict Writer.** Strict Writer evaluates the accumulated output more eagerly.
It can reduce deferred thunks in lazy languages. It does not make unbounded
output cheap. It changes when cost is paid, not whether the cost exists.

**Lazy Writer.** Lazy Writer can defer output construction. It can help when
only part of a result is demanded, but it can also retain thunks and surprise a
team that expects memory to be consumed steadily.

**Difference-list output.** When the output is a list and appending to the end
is costly, the monoid can be a difference list or a builder-like function. This
keeps the Writer shape while changing the output representation. Judgement.
This is often better than abandoning the pattern for moderate list output.

**Domain-specific output record.** Instead of raw strings, define
`Warnings`, `Cost`, or `ExplainPlan` with a monoid instance. The append rule
then expresses business meaning. This avoids treating Writer as an untyped log
string.

**Cats `Writer` and `WriterT`.** Cats documents `Writer[L, A]` and says logs
from composed functions are combined using an implicit `Semigroup`, while its
definition section states that `Writer` is a type alias for `WriterT[Id, L, V]`
(https://typelevel.org/cats/datatypes/writer.html, verified 2026-08-02). Cats
`WriterT` wraps `F[(L, V)]`
(https://typelevel.org/cats/datatypes/writert.html, verified 2026-08-02).

**fp-ts function encoding.** fp-ts documents `Writer<W, A>` as an interface
whose call returns `[A, W]`, with `tell`, `listen`, `pass`, `execute`, and
`evaluate`
(https://gcanti.github.io/fp-ts/modules/Writer.ts.html, verified
2026-08-02). This shape is a good fit for TypeScript because a Writer value is
a deferred function.

**Lean Mathlib proof setting.** Mathlib documents Writer monads for immutable,
appendable state and common logging-monad applications, and defines `WriterT`
as adding writable output to a monad
(https://leanprover-community.github.io/mathlib4_docs/Mathlib/Control/Monad/Writer,
verified 2026-08-02). This is production library evidence that the pattern is
useful beyond application logging.

**Manual explicit pair returns.** A team can return `(value, output)` from each
function and append by hand. This is simpler for two functions and worse when
the pattern spreads. Writer earns its place when repeated pair plumbing hides
the domain flow.

**Operational logging bridge.** The runner can translate Writer output into
structured logs or trace attributes. This keeps domain code pure and still
makes output visible in production. The bridge must handle redaction and volume
limits.

## 9. Known production uses

**Haskell `mtl`, `Control.Monad.Writer.Strict`.** GHC documentation includes
`MonadWriter`, the `Writer` monad, and the `WriterT` transformer, with methods
`writer`, `tell`, `listen`, and `pass`
(https://downloads.haskell.org/ghc/8.6.3/docs/html/libraries/mtl-2.2.2/Control-Monad-Writer-Strict.html,
verified 2026-08-02). This is a named, shipped Haskell library API.

**Haskell `transformers`, `Control.Monad.Trans.Writer.Strict`.** Hackage
documents the strict `WriterT` transformer as adding collection of outputs to
another monad and provides `runWriter`, `execWriter`, `runWriterT`, and
`execWriterT`
(https://hackage-content.haskell.org/package/transformers-0.6.3.0/docs/Control-Monad-Trans-Writer-Strict.html,
verified 2026-08-02).

**Typelevel Cats, `Writer` and `WriterT`.** Cats documents the `Writer` data
type, its use of a log value paired with an output value, composition through a
`Semigroup`, and `WriterT` as the transformer behind `Writer`
(https://typelevel.org/cats/datatypes/writer.html, verified 2026-08-02;
https://typelevel.org/cats/datatypes/writert.html, verified 2026-08-02).

**fp-ts, `Writer.ts`.** fp-ts documents a `Writer<W, A>` interface, `tell`,
`getMonad`, `listen`, `pass`, `evaluate`, and `execute`, with the module added
in version 2.0.0
(https://gcanti.github.io/fp-ts/modules/Writer.ts.html, verified 2026-08-02).

**Lean Mathlib, `Mathlib.Control.Monad.Writer`.** Mathlib documents Writer
monads for immutable, appendable state, defines `WriterT` and `Writer`, and
names `tell`, `listen`, and `pass`
(https://leanprover-community.github.io/mathlib4_docs/Mathlib/Control/Monad/Writer,
verified 2026-08-02).

## 10. Consequences

Positive.

- Domain functions can return a value and explanatory output without mutating a
  shared accumulator.
- Tests can assert the exact output of a computation as data.
- Output composition is centralized in the monoid instead of repeated at every
  call site.
- `tell` gives a small local vocabulary for non-fatal warnings, trace steps,
  generated fragments, and cost notes.
- The runner decides how much output to expose, persist, log, redact, or
  ignore.
- A domain-specific output type can make warnings and summaries more precise
  than string logging.
- Pure code can gain explainability without depending on an external logging
  library.

Negative.

- Output is held until the computation is run and consumed. That can create
  memory pressure.
- The output is not durable unless the runner stores or emits it.
- A careless output monoid can make order, duplication, or cost surprising.
- Transformer ordering can change whether output from failed computations is
  retained.
- Long Writer chains can hide where a large output was produced unless entries
  include origin data.
- Teams may misuse Writer as a logging framework and bypass production logging
  policy.
- Output redaction becomes the runner's responsibility unless the output type
  prevents sensitive values at construction.

Engineering judgement. The main benefit is disciplined explanation. The main
cost is accumulated data. If the data is small and valuable to the caller,
Writer is a strong fit. If the data is large or operational, use another path.

## 11. Failure modes and misuse

**Unbounded output growth.** Symptom. A batch job's memory rises with input
size, and heap snapshots show retained warning lists or strings. Cause. Writer
collects one entry per row or token and returns the whole output at the end.
Fix. Replace Writer with a stream, chunked sink, bounded summary, or output
monoid that keeps counts and samples.

**Logger replacement mistake.** Symptom. Production dashboards show no events
for a path, but unit tests show Writer output. Cause. The runner returns or
discards Writer output instead of emitting it to the logging or tracing stack.
Fix. Add a boundary adapter that maps approved Writer entries to structured
events, or use the service logger directly.

**Secret accumulation.** Symptom. Crash dumps, failed test snapshots, or debug
responses contain tokens, addresses, or personal data inside Writer output.
Cause. Domain code used `tell` with raw input values. Fix. Make the output type
accept only redacted fields or approved codes, and scan existing entries for
sensitive data.

**Wrong append order.** Symptom. Explanation steps appear backward or grouped
under the wrong phase. Cause. The Writer implementation appends `new` before
`old`, or uses a set or map where sequence matters. Fix. Test append order with
two visible entries and choose a list-like monoid when order carries meaning.

**Lost output on failure.** Symptom. A failed validation or parse returns an
error without the warnings that were emitted before the failure. Cause. Writer
was placed inside a short-circuiting result effect, so failure discarded the
accumulated output. Fix. Change transformer ordering, return an explicit
`ResultWithWarnings`, or test and document the discard policy.

**Output inspected too often.** Symptom. Code calls `listen` around many small
steps, filters output, then emits more output based on the prior output. Cause.
The design is using Writer as mutable state. Fix. Use State, an explicit
accumulator, or a fold whose accumulator is visible and intentionally changed.

**Stringly diagnostic soup.** Symptom. Callers search for substrings in Writer
output to decide behavior. Cause. Output was modeled as free text even though it
drives logic. Fix. Replace strings with typed warning codes, cost fields, or
domain events, then render text at the boundary.

**Hidden cost in a hot path.** Symptom. Profiling shows allocation around
`flatMap`, list append, or string concatenation in a tight loop. Cause. Writer
was used where a local builder or fold would be cheaper. Fix. Use a builder,
difference-list output, or explicit mutable local data confined to the loop.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Writer Monad | Explicit pair returns | Mutable accumulator parameter | Structured logger | State Monad | Event stream |
|---|---|---|---|---|---|---|
| Coupling | Low. Domain code depends on Writer and output type | Low but noisy at every call | Medium. Functions know mutation shape | Medium. Code depends on logging API | Low to medium. State type visible | Medium. Code depends on stream API |
| Output as return data | Strong | Strong | Medium. Caller reads final object | Weak. Logs live elsewhere | Strong | Medium. Consumer receives events |
| Memory behavior | Risky for large output | Same risk, more visible | Better if mutable builder is bounded | Better. Sink can flush | Risky if state grows | Better with backpressure |
| Live observability | Weak until runner emits | Weak until caller emits | Weak unless accumulator emits | Strong | Weak until runner emits | Strong |
| Testability | Strong. Assert value and output | Strong but repetitive | Medium. Need alias control | Medium. Need log capture | Strong | Medium. Need stream probe |
| Cognitive load | Medium. Requires monad vocabulary | Low | Low to medium | Low for app teams | Medium | Medium |
| Failure policy | Depends on stack order | Fully explicit | Fully explicit | Logger records before failure | Fully explicit in state | Events before failure may persist |
| Team topology | Good with narrow output type | Poor when repeated everywhere | Poor when shared mutable type spreads | Good when platform owns logging | Good with domain state type | Good when platform owns broker |
| Output editing | `listen`, `pass`, `censor` | Manual | Direct mutation | Hard after emit | Direct | Hard after emit |
| Best fit | Bounded explanatory output | Tiny local flows | Hot local loops | Production telemetry | Output-as-changing-state | Live or huge output |

Reading of the table. Writer wins when output is bounded, returned, and
composed with the domain result. Structured logging wins when operators must
see events live. State wins when later steps need to inspect and alter the
accumulator. Streams win when output volume or latency requires consumption
during the run.

## 13. Related and incompatible patterns

- **Monad.** Writer is a specific monad whose context is append-only output.
  The general Monad entry explains bind, laws, and dependent sequencing.
- **Monoid.** Writer depends on a monoid for output. A weak monoid choice makes
  the pattern weak. A good output monoid names the domain meaning of append.
- **Applicative.** Writer often has an applicative form for independent
  computations whose outputs can be combined. Use applicative style when later
  steps do not need earlier values.
- **Reader Monad.** Reader supplies shared input. Writer accumulates output.
  They compose when a computation needs context and also produces warnings.
- **State Monad.** State replaces Writer when the accumulator must be read and
  changed throughout the run. Writer is append-only by intent.
- **Result Either.** Result handles failure. Writer handles auxiliary output.
  Their composition needs a clear policy for whether failed branches keep output.
- **Validation.** Validation with an error accumulator is close in spirit, but
  its output is the error result. Writer can collect warnings while still
  returning success.
- **Decorator.** A decorator around an effectful service can log calls without
  changing return types. Writer is better for pure explanatory output returned
  to the caller.
- **Observer or event stream.** These replace Writer when output must be live,
  fan out to subscribers, or cross process boundaries.
- **Global mutable logger.** This conflicts with Writer when the same event is
  recorded in two places with no contract. Choose the data return path or the
  operational path for each output category.
- **Service Locator.** A Writer that calls a global logging service inside
  `tell` has stopped being Writer. It now hides an effect behind a pure-looking
  type.

## 14. Refactoring path in and out

Introducing Writer into code that does not have it.

1. Identify a pipeline that already returns a value and also builds warnings,
   notes, cost data, or trace text.
2. Define the output type before defining the Writer. Prefer a typed domain
   output such as `WarningLog` over raw strings when callers inspect it.
3. Define the empty output and append operation. Add tests for identity and
   ordering before changing the pipeline.
4. Wrap one leaf function so it returns `Writer<Output, Value>` instead of
   mutating an accumulator or returning a hand-rolled pair.
5. Add `map`, `flatMap`, `tell`, and `run` helpers locally or import the
   project library equivalent.
6. Move one caller from manual unpacking to `flatMap`. Run tests after that
   single move.
7. Convert the remaining steps in order from leaves toward the runner. Do not
   convert unrelated code in the same change.
8. At the runner, decide the interpretation: return both value and output,
   reject on warnings, emit structured telemetry, or render explanations.
9. Add a regression test that proves output order and failure policy.

Removing Writer when it stops earning its place.

1. Measure or inspect why it is failing. Common reasons are output size,
   unclear failure policy, or team unfamiliarity.
2. If only two functions use Writer, inline `run` and return explicit pairs.
   This is Inline Function plus Introduce Explaining Variable in the refactoring
   family vocabulary.
3. If output is large, replace `tell` calls with writes to a stream, iterator,
   or bounded sink. Keep the output entry type if it is useful.
4. If code uses `listen` to branch on accumulated output, move to State or an
   explicit accumulator.
5. If output must be operational, move emission to a structured logger at the
   point of event creation, and delete the Writer output from the return type.
6. If failure policy is unclear, replace the stack with a domain type such as
   `ResultWithWarnings` whose fields state exactly what survives failure.
7. Delete helper combinators only after every call site is moved, then run the
   prose and structure gates if documentation changed.

Engineering judgement. Refactor in or out at the boundary first. A Writer value
is viral once public, so a narrow adapter keeps the cost contained while the
team learns whether the shape pays.

## 15. Testing and verification

Writer improves testing when output is part of the expected result.

- Test the output monoid separately. Assert `append(empty, x) == x`,
  `append(x, empty) == x`, and associativity for representative values.
- Test append order with two unique entries. This catches reversed bind
  implementations.
- Test `tell` by running a computation that emits one entry and returns unit.
- Test `flatMap` with two computations that emit visible entries and return a
  dependent value.
- Test `listen` by asserting the sub-output appears both inside the returned
  value and in the final output.
- Test `pass` or `censor` with a subprogram that emits two entries and removes
  or rewrites one.
- Test the runner's interpretation. If the runner logs warnings, use a log
  capture. If it rejects warnings, assert the exact error. If it returns both
  fields, assert both.
- Test failure policy when combined with Result Either, exceptions, async, or
  other effects.

Harder because of the pattern.

- Output volume bugs may not appear in small unit tests. Add a property or
  scale test for large input counts.
- Stack ordering bugs require tests at the concrete stack, not at an abstract
  type class alone.
- Operational visibility requires testing the runner, because inner Writer code
  has no production side effect.

Useful test doubles and techniques.

- **Fake output monoid.** Use entries such as `["a"]` and `["b"]` so ordering
  mistakes are visible.
- **Property tests.** Generate small output lists and check monoid laws.
- **Golden trace tests.** For parser, compiler, or planner explanations, store
  an approved output sequence and review changes.
- **Volume tests.** Run a large input and assert output count, byte size, or
  truncation behavior.
- **Redaction tests.** Feed sensitive-looking input and assert no output entry
  contains it.

## 16. Observability signals

Writer output is not visible to production systems unless the runner makes it
visible. Treat that boundary as a first-class observability point.

What to record.

- Count of output entries per run, labelled by computation name.
- Total output bytes per run, with a configured cap.
- Count of truncated output entries, if the runner applies a limit.
- Count of warning codes or explanation categories, not free text.
- Runner action: returned, discarded, logged, converted to error, or persisted.
- Failure policy: output kept on failure, output discarded on failure, or output
  unavailable because the computation did not finish.
- Time spent appending output when profiling shows Writer overhead.

A healthy instance on a dashboard. Entry count is stable for a fixed input
class. Output bytes remain below the cap. Warning categories match known
business cases. Truncation is rare and explained by large input. Runner actions
match the contract for the endpoint.

A failing instance. Entry count grows linearly with batch size when only a
summary was expected. Truncation jumps after a deploy. Free-text categories
explode because callers put raw messages into the output. The runner discards
output on a path where support tooling expects explanations. Output bytes carry
sensitive strings in redaction tests.

Engineering judgement. Do not emit every Writer entry as a production log by
default. Emit counts, categories, and sampled or capped detail. Return full
output only where the caller has asked for an explanation and authorization has
been checked.

## 17. Security and privacy implications

Writer is neutral on security in its small pure form. It opens privacy risk when
the output carries sensitive data longer than intended, and it opens audit risk
when teams mistake returned output for durable evidence.

**Sensitive data retention.** Writer stores output in memory until the runner
handles it. If entries include access tokens, customer text, addresses, or raw
requests, that data may appear in debug responses, failed test artifacts, heap
dumps, or crash reports. Prefer typed output constructors that accept codes,
field names, hashes, or redacted summaries rather than raw values.

**Audit durability.** Writer output is not an audit log. A caller can ignore it,
drop it on exception, or lose it when a process dies. If law, finance, abuse
response, or incident review requires durable records, write through the
approved audit mechanism.

**Authorization on explanations.** Explanation output can reveal internal
rules, feature flags, tenant routing, or validation heuristics. When returning
Writer output to users, gate it by role and redact rule internals.

**Injection through rendered output.** Writer often accumulates strings that are
later rendered in HTML, logs, terminals, or markdown. Escape at the rendering
boundary and prefer structured entries over pre-rendered strings.

**Resource exhaustion.** An attacker who controls input length may force the
program to accumulate huge output. Apply per-run entry limits, byte limits, and
summary modes at the runner or in the output monoid.

**Duplicate records.** A runner that both returns Writer output and emits it to
logs can duplicate sensitive or confusing records. Decide which categories are
for callers and which are for operators, then encode that distinction in the
output type.

## 18. References

1. Mark P. Jones. "Functional Programming with Overloading and Higher-Order
   Polymorphism". *Advanced Functional Programming*, Springer Lecture Notes in
   Computer Science 925, 1995, pages 97 to 136 per DBLP.
   https://dblp.org/rec/conf/afp/Jones95
   Verified 2026-08-02. Source for the lineage cited by Haskell Writer
   documentation.
2. Mark P. Jones. Selected Publications.
   https://web.cecs.pdx.edu/~mpj/pubs.html
   Verified 2026-08-02. Source for the 1995 publication listing.
3. GHC. `mtl-2.2.2`, `Control.Monad.Writer.Strict`.
   https://downloads.haskell.org/ghc/8.6.3/docs/html/libraries/mtl-2.2.2/Control-Monad-Writer-Strict.html
   Verified 2026-08-02. Source for `MonadWriter`, `Writer`, `WriterT`,
   `writer`, `tell`, `listen`, and `pass`.
4. Hackage. `transformers-0.6.3.0`,
   `Control.Monad.Trans.Writer.Strict`.
   https://hackage-content.haskell.org/package/transformers-0.6.3.0/docs/Control-Monad-Trans-Writer-Strict.html
   Verified 2026-08-02. Source for strict `WriterT`, limited output access,
   and the transformer runner shape.
5. Typelevel Cats. "Writer".
   https://typelevel.org/cats/datatypes/writer.html
   Verified 2026-08-02. Source for Cats `Writer`, log and value tuple,
   composition through `Semigroup`, and aliasing to `WriterT`.
6. Typelevel Cats. "WriterT".
   https://typelevel.org/cats/datatypes/writert.html
   Verified 2026-08-02. Source for Cats `WriterT` as a wrapper over
   `F[(L, V)]`.
7. fp-ts. `Writer.ts`.
   https://gcanti.github.io/fp-ts/modules/Writer.ts.html
   Verified 2026-08-02. Source for TypeScript `Writer<W, A>`, `tell`,
   `getMonad`, `listen`, `pass`, `execute`, and `evaluate`.
8. Lean community. `Mathlib.Control.Monad.Writer`.
   https://leanprover-community.github.io/mathlib4_docs/Mathlib/Control/Monad/Writer
   Verified 2026-08-02. Source for Mathlib `WriterT`, `Writer`, `MonadWriter`,
   `tell`, `listen`, and `pass`.

## Code examples

Three languages are shown because the pattern translates well into a small
generic wrapper. TypeScript shows the fp-ts-like function shape. Python shows a
dataclass wrapper with list output. Java shows a compact class using
`Function`. Go, Rust, and Swift are omitted here because the requested minimum
is three compiled or run languages and the three below cover dynamic,
structural, and nominal styles.

### TypeScript

```typescript
type Writer<W, A> = () => [A, W];

const arrayMonoid = {
  empty: [] as string[],
  concat: (left: string[], right: string[]) => left.concat(right),
};

function pure<A>(value: A): Writer<string[], A> {
  return () => [value, arrayMonoid.empty];
}

function tell(message: string): Writer<string[], void> {
  return () => [undefined, [message]];
}

function flatMap<A, B>(
  writer: Writer<string[], A>,
  next: (value: A) => Writer<string[], B>,
): Writer<string[], B> {
  return () => {
    const [value, firstLog] = writer();
    const [nextValue, secondLog] = next(value)();
    return [nextValue, arrayMonoid.concat(firstLog, secondLog)];
  };
}

function parsePositive(raw: string): Writer<string[], number> {
  return flatMap(tell(`read ${raw}`), () => {
    const value = Number(raw);
    return value > 0 ? pure(value) : () => [0, [`defaulted ${raw}`]];
  });
}

const program = flatMap(parsePositive("5"), (n) =>
  flatMap(tell(`double ${n}`), () => pure(n * 2)),
);

console.log(program());
```

### Python

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Generic, TypeVar

A = TypeVar("A")
B = TypeVar("B")


@dataclass(frozen=True)
class Writer(Generic[A]):
    value: A
    log: tuple[str, ...]

    @staticmethod
    def pure(value: A) -> "Writer[A]":
        return Writer(value, ())

    @staticmethod
    def tell(message: str) -> "Writer[None]":
        return Writer(None, (message,))

    def flat_map(self, next_step: Callable[[A], "Writer[B]"]) -> "Writer[B]":
        other = next_step(self.value)
        return Writer(other.value, self.log + other.log)


def parse_positive(raw: str) -> Writer[int]:
    def parse(_: None) -> Writer[int]:
        value = int(raw)
        if value > 0:
            return Writer.pure(value)
        return Writer(0, (f"defaulted {raw}",))

    return Writer.tell(f"read {raw}").flat_map(parse)


program = parse_positive("5").flat_map(
    lambda n: Writer.tell(f"double {n}").flat_map(lambda _: Writer.pure(n * 2))
)

print(program)
```

### Java

```java
import java.util.ArrayList;
import java.util.List;
import java.util.function.Function;

final class Writer<A> {
    private final A value;
    private final List<String> log;

    private Writer(A value, List<String> log) {
        this.value = value;
        this.log = List.copyOf(log);
    }

    static <A> Writer<A> pure(A value) {
        return new Writer<>(value, List.of());
    }

    static Writer<Void> tell(String message) {
        return new Writer<>(null, List.of(message));
    }

    static <A> Writer<A> withLog(A value, List<String> log) {
        return new Writer<>(value, log);
    }

    <B> Writer<B> flatMap(Function<A, Writer<B>> next) {
        Writer<B> other = next.apply(value);
        ArrayList<String> combined = new ArrayList<>(log);
        combined.addAll(other.log);
        return new Writer<>(other.value, combined);
    }

    A value() {
        return value;
    }

    List<String> log() {
        return log;
    }
}

public final class WriterMonadDemo {
    static Writer<Integer> parsePositive(String raw) {
        return Writer.tell("read " + raw).flatMap(ignored -> {
            int value = Integer.parseInt(raw);
            if (value > 0) {
                return Writer.pure(value);
            }
            return Writer.withLog(0, List.of("defaulted " + raw));
        });
    }

    public static void main(String[] args) {
        Writer<Integer> program = parsePositive("5").flatMap(n ->
            Writer.tell("double " + n).flatMap(ignored -> Writer.pure(n * 2))
        );
        System.out.println(program.value());
        System.out.println(program.log());
    }
}
```
