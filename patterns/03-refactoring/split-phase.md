---
name: Split Phase
slug: split-phase
family: 03-refactoring
category: Refactoring
aliases: [Phase Split, Two Phase Computation, Introduce Intermediate Record]
first_described: "Fowler 2018"
maturity: established
related: [extract-function, slide-statements, split-loop, combine-functions-into-transform, introduce-parameter-object, separate-query-from-modifier]
incompatible_with: [inline-function, replace-loop-with-pipeline]
verified: 2026-08-02
---

# Split Phase

## 1. Name, aliases, and lineage

The canonical name is Split Phase. Martin Fowler includes it in the second
edition catalog of *Refactoring. Improving the Design of Existing Code*,
Addison-Wesley, 2nd edition, 2018, chapter 6, "A First Set of Refactorings."
The public refactoring catalog lists Split Phase as one of the refactorings in
the second edition, with a sketch that changes a mixed parse-and-price
calculation into `parseOrder` followed by `price`
(https://refactoring.com/catalog/splitPhase.html, verified 2026-08-02).
Fowler also wrote about the idea before the book release in his 2015 article
on module dependencies, crediting Kent Beck with naming an older recognized
refactoring and giving compilers as a large-scale example
(https://martinfowler.com/articles/refactoring-dependencies.html, verified
2026-08-02).

Common aliases in code review are **phase split**, **two phase computation**,
and **introduce intermediate record**. The last phrase is not a catalog name.
It describes the mechanical move that often makes the refactoring hold: first
create a record carrying the output of phase one, then move phase two behind a
function that consumes that record. The pattern is not the same as a pipeline.
A pipeline is an execution style with many compatible stages. Split Phase is a
refactoring move that finds one overloaded computation, gives its first concern
an explicit output, and gives the second concern an explicit input.

The word "phase" has a broader history in compiler construction and build
systems. TypeScript documentation describes a compiler flow that includes
preprocessing, parsing into source files, binding symbols, creating a program,
checking types, and emitting output
(https://github.com/microsoft/TypeScript/wiki/Architectural-Overview/1afea54fbb7a4af15d613708ac0d1951f73aca14,
verified 2026-08-02). CPython internal documentation describes source
compilation as tokenization, parsing into an AST, transformation into an
instruction sequence, construction and optimization of a control flow graph,
and bytecode emission
(https://github.com/python/cpython/blob/main/InternalDocs/compiler.md,
verified 2026-08-02). Those systems are not examples of Fowler refactoring a
single function in place. They are production proof that phase boundaries and
intermediate representations are a durable design shape.

## 2. Problem and context

A single block of code does two jobs in a fixed order, and the local variables
from the first job leak through the second job. The code often began as a short
calculation. It reads an input string, decodes it, validates a few values,
computes a result, and returns. Later the input format grows, business rules
grow, and error handling grows. Soon a reader cannot tell which lines are about
understanding the input and which lines are about applying policy to the input.

The problem has a common shape. Phase one discovers facts. Phase two acts on
those facts. In an order workflow, phase one may parse a text line into a
product id, quantity, currency, and channel. Phase two prices the order. In a
command line tool, phase one may parse flags and environment into a settings
record. Phase two runs the requested operation. In a compiler, phase one may
turn characters into a syntax tree. Later phases bind names, check types,
rewrite representations, and emit code.

The refactoring matters when the two jobs change for different reasons. Input
parsing changes when a file format changes. Pricing changes when a commercial
rule changes. If both are trapped inside one function, a format change forces a
reader to scan pricing logic, and a pricing change risks breaking parsing
state. The damage is not only length. It is the false local intimacy between
values whose lifetimes should differ.

The smell often appears in local variable names. The first group of variables
has names tied to syntax, transport, or acquisition: `fields`, `parts`,
`header`, `row`, `rawAmount`, `flagText`, `requestBody`. The second group has
names tied to decisions: `discount`, `route`, `permission`, `charge`,
`compiled`, `plan`, `result`. When both groups live in one scope, the reader
must remember which variables are raw, which are normalized, and which have
already passed validation. The compiler usually cannot help because every value
has a legal type. The problem is semantic lifetime, not syntax.

A second signal is test setup. If a unit test for a business rule begins by
constructing a string in a private file format, or if a parser test must include
pricing tables, the test is paying for the missing boundary. Tests should set
up the concern they exercise. Split Phase gives the tests a smaller object to
name. Phase one tests can talk in raw inputs. Phase two tests can talk in domain
facts.

Split Phase introduces a named intermediate result between the jobs. The first
phase returns that result. The second phase accepts it. This turns hidden local
coupling into an explicit data contract. After the split, phase one can be
tested with input examples and expected intermediate records. Phase two can be
tested with hand-built intermediate records and expected decisions. The original
outer function remains as the coordinator until the call sites are ready for a
larger move.

Context matters. Split Phase is not a formatting move for any long function. It
fits code whose internal order already says "before" and "after." If statements
from the two concerns are interleaved because they truly depend on each other
step by step, the split may need Slide Statements, Split Variable, or a smaller
Extract Function before it becomes honest. If the order is artificial, a
different refactoring may be better.

The coordinator should remain boring. It exists so the outside behavior can be
held steady while the inside gets a better shape. A good coordinator after this
refactoring is often two or three lines: prepare, apply, return. If the
coordinator starts making decisions about the intermediate record, the split is
incomplete. Either the decision belongs in phase one because it is validation,
or it belongs in phase two because it is policy.

## 3. Forces

Judgement. The forces below are engineering trade-offs rather than universal
facts. The right balance depends on the cost of allocating the intermediate
record, the stability of its shape, and the team boundaries around the code.

- **Coupling.** Favoured. Phase two depends on an intermediate contract rather
  than the entire parsing or preparation procedure.
- **Cognitive load.** Favoured when the phase names are concrete. A reader can
  inspect `parseOrder` or `priceOrder` separately. Sacrificed when the
  intermediate record is called `Context`, `Data`, or `Info` and becomes a bag.
- **Latency.** Usually close to neutral for request or batch code. Sacrificed in
  tight loops when the split allocates an object per item or forces materialized
  collections where streaming was enough.
- **Consistency.** Favoured when phase one performs validation and phase two
  can assume a normalized record. Sacrificed if the intermediate record can be
  partially initialized or mutated between phases.
- **Operability.** Favoured. The intermediate record gives logs, traces, and
  failure reports a natural object to name. Sacrificed if it carries sensitive
  raw input into places that previously saw only derived values.
- **Cost of change.** Favoured when the two phases change for different reasons.
  Sacrificed when every change crosses both phases and the record churns on each
  patch.
- **Team topology.** Favoured when separate teams own input adapters and domain
  policy. The boundary gives them a contract. Sacrificed when ownership is
  unified and the boundary becomes ceremony.
- **Memory pressure.** Sacrificed if a large intermediate result is retained for
  too long. Favoured when the record lets phase one discard raw input early.

The pattern favours clarity, testability, and change isolation. It pays with
one more named type or record, one more function call, and a new contract that
must be kept meaningful.

## 4. Applicability and non-applicability

Reach for Split Phase when these signals are present.

- A function first interprets input and then applies rules to the interpreted
  form.
- The first half has local variables that are used by the second half but not by
  the caller.
- The two halves need different tests. One wants malformed input examples. The
  other wants business rule examples.
- The first half changes when an external format, API, flag list, or schema
  changes, while the second half changes when domain policy changes.
- A later refactoring needs a stable intermediate shape, such as Combine
  Functions into Transform, Introduce Parameter Object, or moving one phase to a
  different module.
- The code already has comments such as "parse", "validate", "calculate", or
  "emit" dividing sections. Those comments may be names waiting to become
  functions.

Non-applicability list.

- **The work is one indivisible algorithm.** Some algorithms update state in a
  tight recurrence where each step must read the result of the previous step.
  Splitting by appearance can hide the algorithm rather than clarify it.
- **A streaming boundary is required.** If phase two can consume one prepared
  item at a time, materializing every item into a list may harm latency and
  memory. Prefer an iterator, generator, lazy sequence, or transducer shape.
- **The intermediate value has no stable meaning.** If the record would contain
  `a`, `b`, `tmp1`, and `tmp2`, the boundary has not been found. Use Extract
  Variable, Rename Variable, or Slide Statements first.
- **The caller needs only a named subcalculation.** Extract Function is smaller
  and may be enough.
- **The two concerns are alternatives, not phases.** If a flag chooses between
  workflows, use Decompose Conditional, Replace Conditional with Polymorphism,
  Strategy, or a command dispatch table.
- **The split exposes private data too widely.** A record that carries secrets,
  raw tokens, or unredacted customer data across a broad call graph may expand
  the privacy surface. Keep the phase local or redact the contract.
- **The target language already has a cheap parse type in the library.** If a
  standard parser returns the exact representation phase two needs, adding a new
  wrapper type may only rename it.
- **Performance evidence points at allocation.** In a parser, codec, renderer,
  or math kernel, measure before inserting a record in a hot path.

## 5. Structure

Five participants appear in the common form.

- **Original coordinator.** The old function or method. During the refactoring
  it remains as the public entry point. After the split, it calls phase one,
  passes the intermediate result to phase two, and returns the final output.
- **Phase one.** A function that accepts the original input and returns a named
  intermediate result. It may parse, gather, validate, normalize, bind, or
  enrich data. It should not make final policy decisions unless validation is
  the domain of phase one.
- **Intermediate result.** A record, struct, class, tuple with names, AST,
  symbol table, command object, or other representation. Its fields describe
  what phase two is allowed to know. Immutability is preferred when the language
  makes it cheap.
- **Phase two.** A function that accepts the intermediate result and any true
  external collaborators. It produces the final value or performs the final
  effect.
- **Caller.** Code that keeps calling the original coordinator while the split
  is local. Later, some callers may consume the phases directly, but that is a
  second design choice.

The structure becomes more valuable when the intermediate result receives a
domain name. `ParsedOrder`, `BoundProgram`, `ValidatedCommand`, and
`CheckoutRequest` tell readers what is true after phase one. Names such as
`PhaseData` and `ResultInfo` say little and invite unrelated fields.

## 6. ASCII structure diagram

```text
        before Split Phase

        +---------------------------------------------+
        | calculate(input, rules)                     |
        |---------------------------------------------|
        | read and decode input                       |
        | validate shape                              |
        | derive local values                         |
        | apply rules using derived values            |
        | return final output                         |
        +---------------------------------------------+

        after Split Phase

        +-----------------------+
        | Caller                |
        +-----------+-----------+
                    |
                    v
        +-----------------------+
        | calculate(input,rules)|
        |-----------------------|
        | prepared = prepare()  |
        | return apply()        |
        +-----------+-----------+
                    |
          +---------+----------+
          |                    |
          v                    v
 +------------------+   +-----------------------+
 | prepare(input)   |   | apply(prepared,rules) |
 |------------------|   |-----------------------|
 | parse             |   | price, emit, execute |
 | validate          |   | or decide            |
 | normalize         |   +-----------+-----------+
 +--------+---------+               ^
          |                         |
          v                         |
 +------------------+               |
 | PreparedInput    |---------------+
 |------------------|
 | named fields     |
 | validated facts  |
 +------------------+
```

## 7. Dynamics

The runtime flow is deliberately plain. The value returned by phase one is the
boundary object. If phase one fails, phase two does not run. If phase two fails,
the failure can report the already prepared record id, hash, or field summary.

```text
Client          Coordinator        Phase one          Intermediate       Phase two
  |                 |                  |                    |                |
  |-- calculate() ->|                  |                    |                |
  |                 |-- prepare() ---->|                    |                |
  |                 |                  |-- parse input ---> |                |
  |                 |                  |-- validate ------> |                |
  |                 |                  |<-- record ---------|                |
  |                 |<-- record -------|                    |                |
  |                 |-- apply(record, rules) ------------------------------>|
  |                 |                  |                    |-- read fields  |
  |                 |                  |                    |-- decide       |
  |                 |<------------------------------------------------ result|
  |<-- result ------|                  |                    |                |
```

There are two common timing variants. In the eager variant, phase one constructs
the whole intermediate result before phase two starts. This fits validation,
diagnostics, and replay. In the lazy variant, phase one returns an iterator or
generator of prepared records and phase two consumes it as it runs. This fits
large inputs and request streams. The lazy variant still counts as Split Phase
when the boundary type and phase responsibilities are explicit.

## 8. Implementation variants

**Local record split.** The smallest form keeps both new functions near the old
function and introduces a local record type. It is the safest first move because
callers do not change. Use it when the goal is readability and unit tests.

**Named immutable value.** The intermediate result is immutable after phase one.
In TypeScript, that may be a `Readonly` object. In Python, a frozen dataclass.
In Go, a struct passed by value or by pointer with no mutation after creation.
This variant reduces temporal coupling between phases.

**Streaming phase split.** Phase one yields prepared items, and phase two
consumes them. This keeps memory bounded for large inputs. It weakens the
debugging benefit because the whole intermediate result is not available at
once.

**Compiler style multi-phase split.** Many compilers use several intermediate
representations. Go compiler documentation describes syntax parsing, type
checking, generic IR, walking, SSA, machine-specific SSA, and object writing as
separate areas in `cmd/compile`
(https://github.com/golang/go/blob/master/src/cmd/compile/README.md, verified
2026-08-02). This is the same design pressure at larger scale: each phase works
on a representation tailored to its job.

**Validation gate split.** Phase one validates and normalizes untrusted input.
Phase two accepts only the trusted representation. This is useful at API
boundaries. The cost is that validation rules can become detached from business
rules if the record is treated as final truth in contexts it was not designed
for.

**Effect isolation split.** Phase one plans work without side effects. Phase
two executes the plan. This variant is common in deployment tools and payment
flows. It makes dry-run tests easy, but the plan can become stale if the world
changes between the two phases.

**Class or module split.** After the local split has proven stable, move one
phase into a separate module. This should be a later move, not the first move,
because premature module boundaries harden a record shape before the team has
learned it.

**Error accumulation split.** Phase one may collect all input errors into an
error list instead of failing at the first bad field. Phase two then runs only
when phase one returns a valid record. This fits import tools, form validation,
configuration loading, and compilers. The trade-off is that phase one becomes a
small diagnostics engine, with source locations and field names as part of its
contract.

**Canonicalization split.** Phase one maps many equivalent inputs to one
canonical representation. Examples include trimming whitespace, resolving
aliases, normalizing currency codes, expanding defaults, or sorting map keys.
Phase two then has fewer cases. The risk is that phase one may erase detail
that later policy needed. Keep provenance fields when a later phase must report
the original spelling or location.

**Plan and commit split.** Phase one creates a plan: SQL statements to run,
files to write, resources to create, or payments to capture. Phase two commits
the plan. This variant helps with dry runs and approval flows. It also creates
a staleness problem. A plan made against one world state may be wrong seconds
later. Include version checks, etags, balances, locks, or revalidation in phase
two when the outside world can move.

**Parser combinator split.** In functional languages, phase one may be a parser
that returns an algebraic data type, and phase two may be an evaluator over that
type. The same shape works in TypeScript discriminated unions, Rust enums, Swift
enums with associated values, and Python classes. The intermediate result is not
only storage. It is the grammar of acceptable input after parsing.

**Database read model split.** A service may first query and join data into a
read model, then apply a rule to that read model. This can clarify ownership:
phase one knows database schema and query tuning, phase two knows domain
policy. The cost is freshness. The read model is a snapshot, so phase two must
not pretend it is live state.

**Boundary object inside a transaction.** Sometimes both phases must run inside
one transaction. The split can still help if the intermediate record is local to
the transaction and does not escape. The team gains test and review clarity
without introducing a distributed handoff.

## 9. Known production uses

**TypeScript compiler.** TypeScript documentation names core compiler layers:
parser, binder, type resolver or checker, emitter, preprocessor, and program.
It describes the parser generating AST `Node`s, the binder creating and binding
`Symbol`s, `Program` building a global view of source files, `TypeChecker`
answering type questions, and `Emitter` producing JavaScript, declaration
files, or source maps
(https://github.com/microsoft/TypeScript/wiki/Architectural-Overview/1afea54fbb7a4af15d613708ac0d1951f73aca14,
verified 2026-08-02). This is a named production use of phased processing with
intermediate program representations.

**Go compiler.** The Go `cmd/compile` README documents a sequence of phases and
packages, including syntax parsing, type checking, generic IR, walk, generic
SSA, machine-specific SSA, and object file writing. It also describes walk as
decomposing complex statements and desugaring higher-level constructs before
SSA work
(https://github.com/golang/go/blob/master/src/cmd/compile/README.md, verified
2026-08-02). The production use is the Go toolchain's own compiler.

**CPython compiler.** CPython internal documentation describes compilation from
source code to bytecode as several steps: tokenize source, parse tokens into an
AST, transform AST into an instruction sequence, construct a control flow graph
and optimize it, then emit bytecode
(https://github.com/python/cpython/blob/main/InternalDocs/compiler.md,
verified 2026-08-02). It also names the symbol table build and code object
creation path. This is a production interpreter using phase boundaries and
intermediate forms.

**LLVM and Clang.** LLVM documentation describes LLVM as containing tools,
libraries, and headers used to process intermediate representations and convert
them into object files, and says C-like languages use Clang to compile source
into LLVM bitcode and then object files
(https://llvm.org/docs/GettingStarted.html, verified 2026-08-02). Clang user
documentation names frontend, middle-end, and backend areas, with the frontend
including lexer, preprocessor, parser, semantic analysis, and LLVM IR code
generation, and the backend running after LLVM IR generation
(https://clang.llvm.org/docs/UsersManual.html, verified 2026-08-02). This is a
large production family using explicit phase boundaries.

## 10. Consequences

Positive consequences.

- The code gains a named checkpoint. A reader can ask what is true after phase
  one without reading phase two.
- Tests become narrower. Malformed input tests target phase one. Policy tests
  can create intermediate records directly.
- Diagnostics improve. Errors can report whether failure occurred during
  preparation, validation, transformation, or final execution.
- Later movement becomes cheaper. Once a phase boundary exists, moving one side
  into another module is a smaller step.
- Data ownership improves when the intermediate result is immutable. Phase two
  cannot accidentally depend on the mutation schedule of phase one.

Negative consequences.

- There is one more abstraction to name and maintain.
- The intermediate record can become a dumping ground for unrelated locals.
- The split can allocate extra objects or materialize data that could have been
  streamed.
- The boundary can freeze a representation too early. Callers may start
  depending on fields that should have remained private.
- Error handling may duplicate if both phases validate the same invariant in
  different words.
- Debugging may require stepping across more functions.

There is also a social consequence. A named phase boundary invites ownership.
That can be useful, but it can also create a false wall inside a small team.
Judgement. Do not assign different owners to phase one and phase two until the
intermediate contract has survived real change. Otherwise each owner will
defend a boundary whose shape was guessed from one refactoring session.

The most common positive surprise is better naming. Once phase one has to
return a value, the team must decide what the value is. That conversation often
finds missing domain words. A vague `payload` becomes `ParsedOrder`. A vague
`state` becomes `BoundModule`. A vague `options` becomes `ValidatedCommand`.
The code improves because the team now has a noun for a state that already
existed.

The most common negative surprise is boundary creep. The first record contains
three fields. A month later it contains raw input, normalized input, policy
flags, a logger, a database handle, and a cache. At that point the record is no
longer an intermediate result. It is shared mutable workspace. Split it again or
move collaborators back to parameters.

Judgement. The pattern pays off when the intermediate result has a natural name
and a testable contract. If the only name available is vague, the split is not
ready.

## 11. Failure modes and misuse

Judgement. The failures below are phrased as observable triples so a reviewer
can spot them in code, tests, logs, or performance profiles.

- **Symptom.** `PreparedData` gains fields on every unrelated feature branch.
  **Cause.** The team split the function but did not find a domain concept.
  **Fix.** Rename the record around the strongest invariant, then split or
  remove fields that do not fit that invariant.

- **Symptom.** Phase two tests require copying a large object fixture with many
  irrelevant fields. **Cause.** The intermediate result is too broad. **Fix.**
  Introduce a smaller record for the second phase, or split phase one into
  parse and normalize subphases.

- **Symptom.** A production latency dashboard shows a new allocation or garbage
  collection spike after the refactoring. **Cause.** The split materialized a
  large collection in a hot path. **Fix.** Change the intermediate result to an
  iterator, slice view, arena-backed object, or batch record, then measure.

- **Symptom.** Logs say phase two failed, but the input that caused the failure
  cannot be reconstructed. **Cause.** Phase one discarded all identity and
  provenance. **Fix.** Carry a safe input id, source offset, row number, or
  trace id in the intermediate result.

- **Symptom.** Business rules disagree between parse-time validation and
  apply-time validation. **Cause.** The split duplicated ownership of an
  invariant. **Fix.** Move format checks to phase one, policy checks to phase
  two, and write boundary tests for the handoff.

- **Symptom.** A caller bypasses the coordinator and calls phase two with a
  hand-built record that could never come from phase one. **Cause.** The phase
  API escaped before the contract was stable. **Fix.** Keep phase functions
  private until external use is required, or make construction enforce the
  invariant.

- **Symptom.** Error messages become worse after the split. **Cause.** The new
  record stores normalized values but loses raw spans or field names. **Fix.**
  Carry source locations or field labels where diagnostics need them, without
  carrying whole raw payloads.

## 12. Trade-off matrix

| Force | Split Phase | Extract Function | Introduce Parameter Object | Replace Loop with Pipeline |
|---|---|---|---|---|
| Coupling | Creates a named handoff contract | Reduces local detail, may keep hidden locals | Groups parameters, may not separate time order | Couples stages through collection operations |
| Cognitive load | Lower when the record is named well | Lower for a single subtask | Lower at call sites, higher inside object | Lower for collection transforms |
| Latency | Neutral unless it materializes data | Usually neutral | Usually neutral | Can allocate intermediate collections |
| Consistency | Phase two can assume phase one invariants | Depends on extracted function contract | Object may enforce grouped invariants | Depends on pipeline stage purity |
| Operability | Natural phase metrics and logs | Function-level logs only | Object can be logged or inspected | Stage metrics possible but often absent |
| Team topology | Good for adapter and domain split | Good inside one owner area | Good for API cleanup | Good for data transform owners |
| Cost of change | Low when phases change separately | Low for local readability changes | Low when parameter set changes together | Low for ordered collection transforms |
| Main risk | Vague intermediate bag | Too many tiny functions | Object with no behavior | Debugging lazy chains |

## 13. Related and incompatible patterns

**Extract Function** often starts the move. If a section already has a clear
purpose and needs few inputs, extract it directly. Split Phase is larger because
it creates an explicit result from the first section.

**Slide Statements** prepares the ground. Statements belonging to phase one
must be gathered before they can become a function. If statements cannot slide
without changing behavior, the phase boundary is not yet real.

**Split Loop** is a sibling refactoring. Split Loop separates two accumulations
that happen during one traversal. Split Phase separates two conceptual jobs in a
larger computation. A Split Loop result can become phase one of Split Phase.

**Introduce Parameter Object** can be the form taken by the intermediate
record. The difference is direction. Introduce Parameter Object starts from a
parameter list seen at call sites. Split Phase starts from locals hidden inside
a computation.

**Combine Functions into Transform** composes well after the split. A transform
can own phase one when several later operations need the enriched record.

**Separate Query from Modifier** composes with effect isolation. A planning
phase should usually be a query, and an execution phase may be the modifier.

**Replace Loop with Pipeline** may replace Split Phase when the whole problem is
an ordered collection transformation. It conflicts when the pipeline obscures a
real validation or domain boundary.

**Inline Function** is the removal path when the split no longer earns its
place. If phase names are noise and tests do not use the boundary, inline one
phase and delete the record.

## 14. Refactoring path in and out

Refactoring in.

1. Add characterization tests around the original coordinator. Include both
   normal input and at least one invalid input if the code validates.
2. Mark the two concerns in comments or temporary blank lines. Do not commit the
   comments as the final design.
3. Use Slide Statements until the first concern appears before the second
   concern with minimal interleaving.
4. Use Split Variable where one variable is assigned in phase one and reused for
   a different meaning in phase two.
5. Create an intermediate record at the boundary. Start with the fields phase
   two already reads.
6. Replace direct local reads in phase two with reads from the record.
7. Extract phase two into a function that accepts the record.
8. Extract phase one into a function that returns the record.
9. Rename the record and phase functions to domain names.
10. Make the record immutable if the language and callers allow it.
11. Add unit tests at the phase boundary.
12. Remove temporary comments and re-run the original characterization tests.

During the move, keep the coordinator as the only public API unless there is a
clear reason to expose the phases. This reduces blast radius. It also lets you
rename the record and reshape fields while learning. In many codebases the best
final form is still private: a public `calculateOrder` or `compileFile` with
private `parse` and `apply` helpers.

If the original function has side effects in both sections, split with extra
care. Move reads, parsing, and validation first. Leave writes and external calls
in phase two until the boundary is clear. When a write must occur in phase one,
name that fact in the phase name, such as `reserveInventory`, rather than
pretending the phase is preparation only.

If the original function has error handling wrapped around the whole body, move
error boundaries last. First preserve behavior by letting exceptions or error
values flow as before. Then decide whether phase one errors and phase two errors
need different types or messages. Changing error shape during the same edit as
the phase split makes regressions harder to isolate.

Refactoring out.

1. Confirm the boundary has no independent tests, no separate owner, and no
   observability value.
2. Inline phase two into the coordinator.
3. Inline phase one, replacing record fields with local variables.
4. Delete the record type.
5. Re-run the characterization tests and performance checks that justified the
   removal.

The move should be reversible. If it cannot be reversed without changing public
APIs, the team has moved beyond local refactoring into module design.

Sometimes the right path is sideways rather than out. A two-phase function may
grow into three phases: parse, validate, apply. That can be right when each
phase has a stable contract. It can also be avoidance of hard naming. Prefer two
phases until a third has its own tests, its own failure messages, or its own
owner.

## 15. Testing and verification

Split Phase changes the test surface.

- **Coordinator tests.** Keep a small set of end-to-end tests through the old
  public function. They protect the refactoring.
- **Phase one tests.** Feed raw inputs and assert intermediate records or parse
  errors. These tests should cover malformed input, defaults, normalization, and
  provenance fields.
- **Phase two tests.** Build intermediate records directly and assert final
  outputs or effects. These tests should avoid raw input strings unless the raw
  string is part of the record contract.
- **Property tests.** Useful when phase one normalizes values. For example,
  equivalent whitespace or case variants should produce equal records.
- **Mutation tests or branch coverage.** Useful when phase one validates and
  phase two assumes validation. If a removed validation branch leaves tests
  green, the boundary contract is underspecified.
- **Golden tests.** Useful for compiler, formatter, and code generation phases.
  Store the intermediate form only if it is stable enough for readable diffs.

What becomes easier: malformed input tests no longer need to know pricing,
emission, or execution rules. Domain tests no longer need to build raw strings
or files. What becomes harder: if the intermediate record is broad, test
fixtures can become large. Use builders or named factory helpers for test data,
but keep them close to tests so they do not hide invalid states.

Verification should include a small performance check when the original code is
in a hot path. It should also include a review of privacy fields in the
intermediate record.

A useful test pattern is the round trip between phase one and phase two
fixtures. Build a table of raw inputs and expected intermediate records. Build a
second table of intermediate records and expected outputs. Then keep one or two
coordinator tests that connect the tables. This avoids a wide end-to-end matrix
while still proving the phases compose.

For typed languages, add compile-time pressure to the boundary. Prefer
non-nullable fields, enums instead of strings for closed sets, and constructors
or builders that reject invalid records. For dynamic languages, add runtime
assertions at the boundary if invalid records are expensive to debug. The
assertion belongs near the phase entry, not scattered through phase two.

For migration work, compare old and new behavior with shadow execution. Run the
old coordinator and the split coordinator on the same inputs in a test rig
or non-production batch, then compare outputs and error categories. This is
useful when the original function was poorly tested and the input space is
large.

## 16. Observability signals

Expose the phase boundary in production only where it helps diagnosis.

- Count phase one failures separately from phase two failures.
- Record phase durations: preparation time, application time, total time.
- Log a stable input id, record id, source offset, or row number. Avoid logging
  whole raw payloads by default.
- Measure intermediate record size or item count when it may grow with input.
- Trace the phase names as spans in request, batch, or compilation work.
- Track the ratio of phase one rejects to phase two rejects. A sudden rise in
  phase one rejects may mean an upstream format change. A rise in phase two
  rejects may mean a policy rollout, bad configuration, or data drift.

A healthy instance shows stable phase duration ratios, bounded intermediate
sizes, and failure counts that match known input quality. A failing instance
shows phase one accepting records that phase two later rejects, record sizes
growing without input growth, or phase one duration dominating after a format
change.

Choose cardinality with care. It is useful to label a trace with phase name,
input source, schema version, and error category. It is dangerous to label a
metric with product id, user id, raw filename, or full command text if those
values have high cardinality or privacy risk. Logs can carry more detail than
metrics, but logs still need redaction.

For batch systems, record checkpoint counts: number of raw items read, number
of intermediate records produced, number rejected by phase one, number accepted
by phase two, and number committed. The ratios reveal where work is being lost.
For request systems, record phase latency percentiles and error categories. For
compilers and generators, record source size, intermediate node count, pass
count, and output size.

Observability should not force the record to expose every field. A small summary
method can emit safe diagnostics: count, source id, version, and validation
state. Keep raw payload printing behind local debug tooling, not production
logs.

## 17. Security and privacy implications

Judgement. Split Phase is security-relevant at boundaries where phase one
validates or normalizes untrusted input. It is otherwise mostly silent on
security.

Positive effects.

- The handoff record can make trust state explicit. Phase two can accept a
  `ValidatedCommand` rather than raw input.
- Centralized phase one validation reduces duplicated parsing checks.
- Audit logs can record which phase rejected input.
- Planning and execution can be separated, allowing dry-run review before an
  effectful phase.

Risks.

- The intermediate record may carry raw secrets farther than before. Tokens,
  credentials, customer text, and headers need redaction or exclusion.
- A public constructor for a "validated" record can let callers forge trusted
  state. Use private constructors, smart constructors, sealed variants, or
  module-private fields where the language supports them.
- Normalization can erase data needed for forensic review, such as source
  offsets. Carry safe provenance rather than whole sensitive payloads.
- If phase two treats phase one as an authorization gate, the boundary must be
  protected by tests and API visibility. A phase split is not an access control
  system by itself.

## 18. References

- Martin Fowler, *Refactoring. Improving the Design of Existing Code*,
  Addison-Wesley, 2nd edition, 2018, chapter 6, "A First Set of Refactorings,"
  Split Phase.
- Martin Fowler, "Split Phase," Refactoring catalog,
  https://refactoring.com/catalog/splitPhase.html, verified 2026-08-02.
- Martin Fowler, "Refactoring Module Dependencies,"
  https://martinfowler.com/articles/refactoring-dependencies.html, verified
  2026-08-02.
- Martin Fowler, "Changes for the 2nd Edition of Refactoring,"
  https://martinfowler.com/articles/refactoring-2nd-changes.html, verified
  2026-08-02.
- Microsoft TypeScript Wiki, "Architectural Overview,"
  https://github.com/microsoft/TypeScript/wiki/Architectural-Overview/1afea54fbb7a4af15d613708ac0d1951f73aca14,
  verified 2026-08-02.
- Go project, "`cmd/compile` README,"
  https://github.com/golang/go/blob/master/src/cmd/compile/README.md,
  verified 2026-08-02.
- Python Software Foundation, "Compiler design," CPython internal
  documentation, https://github.com/python/cpython/blob/main/InternalDocs/compiler.md,
  verified 2026-08-02.
- LLVM Project, "Getting Started with the LLVM System,"
  https://llvm.org/docs/GettingStarted.html, verified 2026-08-02.
- Clang project, "Clang Compiler User's Manual,"
  https://clang.llvm.org/docs/UsersManual.html, verified 2026-08-02.
- LLVM Project, "LLVM's Analysis and Transform Passes,"
  https://www.llvm.org/docs/Passes.html, verified 2026-08-02.
- LLVM Project, "The LLVM Target-Independent Code Generator,"
  https://llvm.org/docs/CodeGenerator.html, verified 2026-08-02.

## Code examples

### TypeScript

```typescript
type PriceList = Readonly<Record<string, number>>;

type ParsedOrder = Readonly<{
  productId: string;
  quantity: number;
}>;

function parseOrder(line: string): ParsedOrder {
  const [sku, quantityText] = line.trim().split(/\s+/);
  const [, productId] = sku.split(":");
  const quantity = Number.parseInt(quantityText, 10);
  if (!productId || !Number.isInteger(quantity) || quantity <= 0) {
    throw new Error("invalid order");
  }
  return { productId, quantity };
}

function priceOrder(order: ParsedOrder, prices: PriceList): number {
  const unitPrice = prices[order.productId];
  if (unitPrice === undefined) {
    throw new Error("missing price");
  }
  return order.quantity * unitPrice;
}

export function calculateOrder(line: string, prices: PriceList): number {
  return priceOrder(parseOrder(line), prices);
}

console.log(calculateOrder("sku:tea 3", { tea: 4 }));
```

### Python

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class ParsedOrder:
    product_id: str
    quantity: int


def parse_order(line: str) -> ParsedOrder:
    sku, quantity_text = line.strip().split()
    _, product_id = sku.split(":", 1)
    quantity = int(quantity_text)
    if not product_id or quantity <= 0:
        raise ValueError("invalid order")
    return ParsedOrder(product_id, quantity)


def price_order(order: ParsedOrder, prices: dict[str, int]) -> int:
    try:
        return order.quantity * prices[order.product_id]
    except KeyError as exc:
        raise ValueError("missing price") from exc


def calculate_order(line: str, prices: dict[str, int]) -> int:
    return price_order(parse_order(line), prices)


print(calculate_order("sku:tea 3", {"tea": 4}))
```

### Go

```go
package main

import (
	"fmt"
	"strconv"
	"strings"
)

type ParsedOrder struct {
	ProductID string
	Quantity  int
}

func parseOrder(line string) (ParsedOrder, error) {
	fields := strings.Fields(line)
	if len(fields) != 2 {
		return ParsedOrder{}, fmt.Errorf("invalid order")
	}
	parts := strings.SplitN(fields[0], ":", 2)
	quantity, err := strconv.Atoi(fields[1])
	if len(parts) != 2 || parts[1] == "" || err != nil || quantity <= 0 {
		return ParsedOrder{}, fmt.Errorf("invalid order")
	}
	return ParsedOrder{ProductID: parts[1], Quantity: quantity}, nil
}

func priceOrder(order ParsedOrder, prices map[string]int) (int, error) {
	unitPrice, ok := prices[order.ProductID]
	if !ok {
		return 0, fmt.Errorf("missing price")
	}
	return order.Quantity * unitPrice, nil
}

func calculateOrder(line string, prices map[string]int) (int, error) {
	order, err := parseOrder(line)
	if err != nil {
		return 0, err
	}
	return priceOrder(order, prices)
}

func main() {
	total, err := calculateOrder("sku:tea 3", map[string]int{"tea": 4})
	if err != nil {
		panic(err)
	}
	fmt.Println(total)
}
```
