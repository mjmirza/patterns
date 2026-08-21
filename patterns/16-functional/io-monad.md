---
name: IO Monad
slug: io-monad
family: 16-functional
category: Effects
aliases: [IO Action, Effect Type, World-Passing IO]
first_described: "Peyton Jones and Wadler 1993"
maturity: canonical
related: [monad, functor, applicative, algebraic-effects, free-monad]
incompatible_with: [unrestricted-side-effects-in-pure-functions]
verified: 2026-08-21
---

# IO Monad

## 1. Name, aliases, and lineage

The canonical name is IO Monad, sometimes written IO Action when the
focus is on one particular value rather than the type constructor. The
pattern traces to Simon Peyton Jones and Philip Wadler's "Imperative
Functional Programming", 20th ACM Symposium on Principles of
Programming Languages, POPL 1993
(https://www.microsoft.com/en-us/research/publication/imperative-functional-programming/,
verified 2026-08-21), which showed how a purely functional language
could express input and output as ordinary values while keeping every
function outside the IO type free of side effects. The paper won the
POPL ten-year most-influential paper award in 2003.

The alias **Effect Type** names the same idea in a language-neutral way,
used when discussing the concept across languages that call it IO,
Task, or Effect. **World-Passing IO** names the specific low-level
encoding described in dimension 8, where an IO action is modelled as a
function threading a token representing the state of the outside world.

## 2. Problem and context

A purely functional language gives every function a strong guarantee.
calling it twice with the same arguments produces the same result, and
calling it produces no observable change anywhere else. That guarantee
is what makes equational reasoning, safe reordering, and referential
transparency possible.

Reading a file, printing to a console, or sending a network request
breaks that guarantee outright. the result depends on the state of the
world outside the program, and performing the action changes that
state. A language that wants both the reasoning benefits of purity and
the ability to actually talk to the outside world needs some way to
express effectful actions as ordinary values, so the type system can
tell a pure function from an effectful one, and so effects can be
built up, passed around, and composed before anything actually runs.

## 3. Forces

The pattern balances the following competing pressures.

- **Purity.** Favoured. Every function outside the IO type remains
  pure, so the compiler and the reader can rely on referential
  transparency everywhere else in the program.
- **Expressiveness for effects.** Favoured, at a cost. Because an IO
  value only describes an effect rather than performing it, sequencing
  and composing effects needs the Monad interface, bind and return,
  rather than ordinary function application.
- **Runtime enforcement.** Favoured. The type system, not a convention
  or a linter, is what prevents an effect from leaking into a context
  that expects a pure value, since a function that returns an ordinary
  value cannot secretly also perform IO.
- **Familiarity for imperative-style code.** Sacrificed, then partly
  recovered. Do-notation and its equivalents in other languages let an
  IO-heavy program read close to an ordinary imperative script, while
  the underlying value remains a description rather than an executed
  sequence of statements.
- **Deferred execution semantics.** Favoured, at the cost of a real
  conceptual jump for newcomers. Building an IO value does nothing.
  only running it, through the language's designated entry point,
  actually performs the effect, which surprises anyone who expects a
  function call to run immediately.

## 4. Applicability and non-applicability

Reach for the IO Monad pattern when the following hold.

- The language or the codebase already commits to keeping ordinary
  functions pure, and effects need an explicit, type-checked escape
  hatch.
- Effects genuinely need to be sequenced, composed, retried, or passed
  around as values before they run, which the Monad interface supports
  directly.
- The team benefits from the type signature itself declaring which
  functions can perform effects and which cannot.

Do NOT reach for the IO Monad pattern in these cases, and the reason
matters more than the rule.

- **The language has no enforced purity to protect**, an ordinary
  imperative or object-oriented language where every function can
  already perform a side effect freely. wrapping every effect in an IO
  type there adds ceremony without the compile-time guarantee that
  makes the pattern worth its cost in Haskell or a similarly disciplined
  language.
- **A lighter effect boundary already covers the need**, a simple async
  or Promise-style future is enough when the goal is only sequencing
  asynchronous work, and the codebase has no broader commitment to
  purity elsewhere.
- **The effect is trivial and local**, logging one line inside an
  otherwise pure function in a language without enforced purity gains
  nothing from an IO wrapper and adds a layer the reader has to unwrap.

## 5. Structure

An IO Monad has one type constructor and a small, fixed interface.

- **IO a**, a value describing an effectful computation that, when
  performed, produces a result of type a. Building this value performs
  no effect.
- **return** (or pure), lifting an ordinary value into IO a with no
  effect attached, the effect-free case.
- **bind** (>>= or its equivalent), sequencing two IO actions so the
  second can use the result of the first, threading the description of
  one effect into the description of the next without running either.

Composed IO values remain descriptions until they reach the language's
one designated entry point, most often called main, where the runtime
actually performs the sequence of effects the value describes.

## 6. ASCII structure diagram

```
    IO a, a description of an effect producing a value of type a

    return x        ->  IO a, no effect, wraps x
    action >>= f    ->  IO b, run action, feed its result a into f,
                        which produces the next IO b to run

    Building a program (no effect yet)

    readLine  :: IO String
    greet name = putStrLn ("hello " ++ name)
    putStrLn  :: String -> IO ()

    program = readLine >>= greet
                            ^^^^^
                            built, not run, still only a value

    Running the program (the one moment effects happen)

    main = program
            |
            v
       runtime performs readLine   -> reads "Ada" from the console
            |
            v
       runtime performs putStrLn "hello Ada"  -> prints to the console
```

## 7. Dynamics

The trace below shows the same two-step program from dimension 6, first
built as a value with no effect, then performed once at the program's
entry point.

```
Build phase (pure, no I/O happens)

greet name  =  putStrLn ("hello " ++ name)
program     =  readLine >>= greet
            =  an IO () value, entirely inert until run

Run phase (the runtime performs the described sequence)

runtime reaches main
   |-- perform readLine ------------------> reads "Ada" from stdin
   |<-- IO String result: "Ada" -----------|
   |
   |-- apply greet to "Ada" ---------------> produces putStrLn "hello Ada"
   |
   |-- perform putStrLn "hello Ada" -------> writes "hello Ada" to stdout
   |<-- IO () result: () -------------------|
```

## 8. Implementation variants

**World-passing token encoding.** The historical GHC implementation
represents `IO a` as a function from a token standing for the state of
the real world to a pair of a new token and a result,
`State# RealWorld -> (# State# RealWorld, a #)`. Each IO action
consumes and produces a fresh world token, so the type system's linear
threading of that token is what stops two IO actions from being
silently reordered or duplicated by the optimiser.

**Free monad encoding.** Rather than a primitive built into the
runtime, IO can be built as a Free monad over a functor describing the
available effect operations, interpreted by a separate evaluator that
performs the actual effect. This variant makes the effect description
and the effect execution two entirely separate pieces of code, useful
when a program needs more than one interpreter for the same
description, a real interpreter and a test interpreter that records
calls instead of performing them.

**Direct effect type in a strict language.** Scala's cats-effect `IO`
and similar effect types in strict, non-lazy languages wrap a
computation as a lazily evaluated, composable value using the host
language's own laziness primitives, since the language does not have
Haskell's call-by-need evaluation to lean on for the deferred-execution
guarantee.

**Unsafe escape hatches, used deliberately and sparingly.** Every
production IO implementation ships an operation, `unsafePerformIO` in
Haskell and its equivalents elsewhere, that runs an IO action and
returns its result as an ordinary pure value, breaking the purity
guarantee on purpose. It exists for foreign-function interop and for a
small number of genuinely justified cases, and every serious codebase
treats its presence as something to search for and review, never as an
ordinary tool.

## 9. Known production uses

**GHC's `System.IO`, part of the `base` package.** The Glasgow Haskell
Compiler's standard library defines the `IO` type used by every Haskell
program that performs input or output, documented as. "A value of type
`IO a` is a computation which, when performed, does some I/O before
returning a value of type `a`." Hackage package documentation,
`System.IO`,
https://hackage.haskell.org/package/base/docs/System-IO.html, verified
2026-08-21.

**Typelevel Cats Effect `IO`.** The cats-effect library brings the same
value-based, composable effect model to Scala, describing a program as
a value that can be reused and composed before it runs, rather than as
a sequence of statements executed immediately. Typelevel Cats Effect
documentation, Getting Started,
https://typelevel.org/cats-effect/docs/getting-started, verified
2026-08-21.

## 10. Consequences

Positive.

- Every function outside the IO type stays pure, so the type signature
  itself tells the reader which functions can perform an effect and
  which cannot.
- Effects become ordinary values, so they can be built, stored, passed
  as arguments, composed with generic combinators, and, in the free
  monad variant, given more than one interpreter.
- Testing a function that returns an IO value can inspect the built
  description without running any real effect, when the implementation
  supports introspecting the value.
- The single designated entry point where effects actually run gives a
  program exactly one place where the real world is touched, which
  narrows where a reader looks for actual observable behaviour.

Negative.

- Sequencing IO actions needs the Monad interface, bind and do-notation
  or their equivalents, which is a real conceptual jump for anyone
  arriving from an ordinary imperative language.
- An escape hatch like `unsafePerformIO` exists in every production
  implementation, and its presence in a codebase needs active review,
  since it can reintroduce the exact impurity the pattern exists to
  prevent.
- Combining IO with other effects, error handling, reader-style
  configuration, logging, needs monad transformers or an equivalent
  effect-stacking mechanism, adding its own learning cost.
- In a language without enforced purity, adopting an IO wrapper without
  the compiler backing it up produces ceremony with none of the
  guarantee that justifies the ceremony elsewhere.

## 11. Failure modes and misuse

**Reaching for `unsafePerformIO` to avoid restructuring a function
signature.** Symptom. A function that looks pure from its signature
secretly performs an effect, and calling it twice can silently produce
different results or duplicate a real-world action. Cause. Using the
escape hatch as a shortcut around threading IO through a call chain,
rather than restructuring the chain to carry IO honestly. Fix.
Restructure the call chain so the IO type flows through every function
that genuinely needs to perform an effect, and reserve the escape hatch
for foreign-function interop or a case reviewed and justified on its
own.

**Treating IO composition as ordinary sequential statements.** Symptom.
A newcomer writes code expecting an IO action defined earlier in a
do-block to have already run by the time a later line executes, and is
surprised when nothing happened until the whole block reached the
entry point. Cause. Confusing building an IO value, which does nothing,
with performing it, which only happens at the one designated entry
point or an explicit run call. Fix. Teach the build-versus-run
distinction directly, and, where the language allows it, keep the
smallest possible number of places in a codebase where IO values are
actually run.

**Stacking IO with other effects through nested transformers until the
type signatures become unreadable.** Symptom. A function's type
signature grows several layers of nested effect wrappers, error
handling wrapped around configuration wrapped around IO, and every call
site needs boilerplate to unwrap and rewrap the stack. Cause. Reaching
for monad transformers as the default answer to every additional
effect, without stepping back to ask whether a flatter effect type or a
smaller set of composed effects would serve the same need. Fix.
Consolidate the effect stack to the smallest set the codebase actually
needs, and consider a single unified effect type, such as the concrete
effect types shipped by cats-effect or ZIO, over an open-ended tower of
transformers.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | IO Monad | Direct side effects, no wrapper | Free monad over an effect functor | A single concrete effect type (cats-effect IO, ZIO) |
|---|---|---|---|---|
| Keeps ordinary functions pure | Yes, enforced by the type system | No | Yes | Yes |
| Composable as an ordinary value | Yes | No | Yes | Yes |
| Supports more than one interpreter for the same description | No, one built-in runtime | No | Yes | No, one runtime |
| Learning cost for an imperative-language team | Real, Monad and do-notation | Lowest | Highest, needs a functor algebra too | Moderate, a single concrete API |
| Needs an escape hatch for interop | Yes, `unsafePerformIO` or equivalent | Not applicable | Depends on the interpreter | Yes, an unsafe run method |

Reading of the table. The IO Monad wins whenever the surrounding
language already commits to enforced purity and the team wants that
guarantee backed by the compiler. Direct side effects win in a language
with no purity discipline to protect, where the wrapper only adds
ceremony. A free monad over an effect functor wins when a program
genuinely needs more than one interpreter for the same description, a
real one and a test one. A single concrete effect type wins when a
team wants IO's composability without building and maintaining a
tower of monad transformers by hand.

## 13. Related and incompatible patterns

- **Monad.** The interface the IO type is built on. return and bind are
  exactly the Monad operations, specialised to an effectful description
  rather than a container or a computation shape.
- **Functor.** The IO type's covariant mapping over its result value is
  an ordinary Functor instance, the simpler capability Monad builds on
  top of.
- **Applicative.** IO also has an Applicative instance, letting
  independent effectful computations combine without the full
  sequencing power of Monad when that sequencing is not actually
  needed.
- **Algebraic Effects.** A newer, generally more flexible approach to
  the same underlying problem, effects as first-class, interpretable
  values, without committing to the specific Monad-transformer
  composition story that IO and its stacked variants rely on.
- **Free Monad.** One of the implementation variants of IO from
  dimension 8, and a related but distinct pattern in its own right,
  separating an effect's description from its interpretation more
  generally than the built-in IO type does.
- **Unrestricted side effects in pure functions.** Conflicts directly.
  a function that claims purity through its signature while secretly
  performing an effect through an escape hatch defeats the entire
  reason to adopt the IO Monad, per the first failure mode in
  dimension 11.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. Ordered steps,
most relevant to a language migrating toward enforced purity or adding
a new effect-typed layer.

1. Identify the functions that genuinely perform an effect, reading
   input, writing output, calling a network service, and mark their
   return type as an IO-wrapped value.
2. Propagate the IO type outward through every caller that needs the
   result of an effectful function, rather than unwrapping early with
   an unsafe escape hatch.
3. Replace ad hoc sequential effect calls with explicit bind or
   do-notation composition, so the ordering of effects is visible in
   the type-level composition, not only in source order.
4. Confirm the codebase has exactly one, or a small, deliberate number
   of places where an IO value is actually run, typically the program's
   entry point.
5. Add a test asserting that building an IO value performs no observable
   effect on its own, distinguishing the build step from the run step.

Removing the pattern when it stops earning its place. Signals that it
should go include a codebase that never had enforced purity to protect
in the first place, or an IO wrapper added around a single, trivial,
local effect that gained the team no real guarantee.

1. Confirm whether the surrounding language actually enforces purity
   outside IO. if it does not, the wrapper is unearned ceremony.
2. Confirm whether any caller actually relies on IO's composability,
   building, storing, or combining effect descriptions before running
   them. if none does, a direct effectful call is simpler.
3. Replace the IO-typed function with a direct effectful call, one call
   site at a time, keeping tests green after each site.
4. Remove the IO wrapper only after no call site depends on the
   type-level guarantee it provided.

## 15. Testing and verification

Easier because of the pattern.

- An IO value can be constructed and inspected, in implementations that
  support it, without ever running the real effect, which lets a test
  assert what a function WOULD do without touching the filesystem, the
  network, or the console.
- Because IO is Monad, Applicative, and Functor, the same generic law
  tests written once for those interfaces elsewhere in a codebase apply
  unchanged to IO.
- The free monad implementation variant makes substituting a test
  interpreter for the real one a first-class operation, rather than a
  separate mocking layer bolted on afterward.

Harder because of the pattern.

- A test that actually needs to observe an effect happening, a file
  genuinely written, a request genuinely sent, still has to run the IO
  value for real, at which point the test inherits every flakiness
  concern any effectful test carries, network timeouts, filesystem
  state, timing.
- Distinguishing correct IO composition from an accidental
  `unsafePerformIO` shortcut is not visible from a passing test unless
  the test specifically checks that a function's purity claim holds,
  calling it twice and confirming identical results with no observable
  side effect from the call itself.

Techniques that apply.

- **Build-without-run assertion.** Construct an IO value and assert no
  observable effect occurred before the value is explicitly run,
  confirming the build and run phases are genuinely separate.
- **Interpreter substitution, for the free monad variant.** Run the
  same effect description through a real interpreter and a recording
  test interpreter, and assert the recording interpreter's log matches
  the expected sequence of operations.
- **Applicative and Monad law tests.** Standard law tests, reused
  unchanged from any other Monad instance in the codebase, applied to
  the IO type where the language and library support introspecting it.
- **Purity regression test on a claimed-pure function.** Call a
  function that should have no IO in its type twice with identical
  arguments and assert identical results and no observable side effect,
  guarding against a future change smuggling in an escape hatch.

## 16. Observability signals

The IO Monad is a compile-time and language-level discipline more than
a runtime component, and inventing a dedicated production signal for
the type itself would be dishonest. Two things are worth watching in a
codebase that relies on it.

What to record.

- A count, tracked over time, of how many uses of an unsafe escape
  hatch, `unsafePerformIO` or its equivalent, exist in the codebase,
  since each one is a place where the purity guarantee the pattern
  exists to provide has been deliberately broken.
- The depth and shape of the effect stack, how many transformers or
  nested effect layers a typical function signature carries, since a
  stack that keeps growing is a signal the effect architecture needs
  consolidation.

A healthy state. The escape-hatch count stays small, each instance
carries a comment explaining why it is justified, and the review
process treats a new one as a decision worth discussing, not a routine
addition.

A failing state. The escape-hatch count grows quietly over time with
no review process catching it, or the effect stack has grown deep
enough that a typical function signature is mostly transformer noise,
with the actual business logic buried underneath it.

## 17. Security and privacy implications

The IO Monad's own type-checking discipline is, if anything, a security
positive. it makes every place a program touches the outside world
visible in the type signature, which is useful when auditing where
untrusted input enters a system or where an output channel could leak
sensitive data. Two practical implications are worth naming.

**The unsafe escape hatch is a real audit target.** Because
`unsafePerformIO` and its equivalents can run arbitrary effectful code
while presenting a pure-looking signature, a security review of a
Haskell or similarly IO-disciplined codebase should specifically search
for and justify every use, the same way a review searches for `eval`
or dynamic code execution in other languages.

**IO composition does not, on its own, sanitise or authorise
anything.** Wrapping a network call or a file read in the IO type
proves the function is honest about performing an effect, it says
nothing about whether the effect is safe, authorised, or operating on
sanitised input. The usual input-validation, authorisation, and
output-encoding discipline still applies inside the IO-typed function,
exactly as it would without the wrapper.

## Code examples

Three languages where the pattern is genuinely idiomatic in different
ways. TypeScript models an IO value as a deferred, zero-argument
function returning a result, the shape libraries such as fp-ts use to
bring the pattern into a strict, eagerly evaluated language. Python
shows the same construction as a small wrapper class holding a thunk,
with an explicit run method, closer to how the pattern reads without a
built-in Monad typeclass. Swift shows a generic struct wrapping a
closure with a map and flatMap method, using Swift's own closure and
generics support to express the build-versus-run separation directly.
Java and Go are omitted, because expressing a reusable, generic IO type
with map and flatMap idiomatically in either language needs more
machinery, functional interfaces or generic method constraints, than
this entry has room for without collapsing into a single hard-coded
case. Rust is omitted for the same reason as the language note
elsewhere in this family, a general Monad-shaped IO type needs more
trait machinery than fits the space here, and Rust's own async and
Result types already cover most of the practical need this pattern
addresses.

### TypeScript

```typescript
class IO<A> {
  constructor(private readonly thunk: () => A) {}

  static of<A>(value: A): IO<A> {
    return new IO(() => value);
  }

  map<B>(f: (a: A) => B): IO<B> {
    return new IO(() => f(this.run()));
  }

  flatMap<B>(f: (a: A) => IO<B>): IO<B> {
    return new IO(() => f(this.run()).run());
  }

  run(): A {
    return this.thunk();
  }
}

const readLine: IO<string> = new IO(() => "Ada");
const printLine = (s: string): IO<void> => new IO(() => console.log(s));

const program: IO<void> = readLine.flatMap((name) => printLine("hello " + name));

program.run();
```

### Python

```python
from dataclasses import dataclass
from typing import Callable, Generic, TypeVar

A = TypeVar("A")
B = TypeVar("B")


@dataclass(frozen=True)
class IO(Generic[A]):
    thunk: Callable[[], A]

    @staticmethod
    def of(value: A) -> "IO[A]":
        return IO(lambda: value)

    def map(self, f: Callable[[A], B]) -> "IO[B]":
        return IO(lambda: f(self.run()))

    def flat_map(self, f: Callable[[A], "IO[B]"]) -> "IO[B]":
        return IO(lambda: f(self.run()).run())

    def run(self) -> A:
        return self.thunk()


read_line: IO[str] = IO(lambda: "Ada")
print_line = lambda s: IO(lambda: print(s))

program = read_line.flat_map(lambda name: print_line("hello " + name))

if __name__ == "__main__":
    program.run()
```

### Swift

```swift
struct IO<A> {
    let run: () -> A

    static func of(_ value: A) -> IO<A> {
        IO { value }
    }

    func map<B>(_ f: @escaping (A) -> B) -> IO<B> {
        IO<B> { f(self.run()) }
    }

    func flatMap<B>(_ f: @escaping (A) -> IO<B>) -> IO<B> {
        IO<B> { f(self.run()).run() }
    }
}

let readLine = IO<String> { "Ada" }
func printLine(_ s: String) -> IO<Void> {
    IO<Void> { print(s) }
}

let program = readLine.flatMap { name in printLine("hello " + name) }

program.run()
```

## 18. References

1. Simon Peyton Jones and Philip Wadler. "Imperative Functional
   Programming". 20th ACM Symposium on Principles of Programming
   Languages, POPL 1993.
   https://www.microsoft.com/en-us/research/publication/imperative-functional-programming/
   Verified 2026-08-21. Source of the first_described lineage claim.
2. GHC base library documentation. `System.IO`.
   https://hackage.haskell.org/package/base/docs/System-IO.html
   Verified 2026-08-21. Source for the GHC production use in dimension
   9 and the type description quoted there.
3. Typelevel Cats Effect documentation. Getting Started.
   https://typelevel.org/cats-effect/docs/getting-started
   Verified 2026-08-21. Source for the Scala production use in
   dimension 9.
