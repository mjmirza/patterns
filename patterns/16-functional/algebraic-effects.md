---
name: Algebraic Effects
slug: algebraic-effects
family: 16-functional
category: Effects
aliases: [Effect Handlers, Algebraic Effects and Handlers, Resumable Exceptions]
first_described: "Plotkin and Pretnar 2009"
maturity: emerging
related: [io-monad, monad, free-monad, continuation-passing-style, exception-handling]
incompatible_with: [deeply-nested-monad-transformer-stacks]
verified: 2026-08-21
---

# Algebraic Effects

## 1. Name, aliases, and lineage

The canonical name is Algebraic Effects, often paired with the word
Handlers since the pattern is genuinely two halves, an effect that a
piece of code performs and a handler that decides what happens when
that effect is performed. The pattern traces to Gordon Plotkin and
Matija Pretnar's "Handlers of Algebraic Effects", 18th European
Symposium on Programming, ESOP 2009, part of ETAPS 2009
(https://www.research.ed.ac.uk/en/publications/handlers-of-algebraic-effects,
verified 2026-08-21), which gave exception-style handlers a general
algebraic treatment covering far more than exceptions. an effect can
be resumed, not only aborted, and a single computation can be handled
differently by different handlers around it.

The alias **Effect Handlers** names the runtime half of the pattern
directly. **Resumable Exceptions** is the intuition many newcomers
reach for first. an algebraic effect behaves like an exception that,
instead of unwinding the stack permanently, can hand control back to
the exact point it was raised from, with a value supplied by the
handler.

## 2. Problem and context

A program built from the IO Monad or a stack of monad transformers
gets real benefits, effects are visible in the type, and composition
follows well-understood laws. But combining several effects, error
handling, state, non-determinism, async, into one computation usually
means nesting monad transformers, and each new effect added to the
stack means touching every layer already there. The resulting type
signatures grow long, and adding one new effect can mean rewriting
the lifting code through every existing layer.

There is also a genuine expressiveness gap. A monadic exception can
abort a computation, but it cannot easily resume it with a value and
continue from the exact point the exception was raised, the way a
generator's yield or a lightweight cooperative thread needs to.
Algebraic effects solve both problems at once. an effect is performed
as an ordinary operation, a handler installed somewhere up the call
stack decides how to respond, and the handler can choose to resume the
computation with a value, run it again, run it zero times, or abandon
it entirely, all without the caller needing to know which handler, if
any, is listening.

## 3. Forces

The pattern balances the following competing pressures.

- **Composability of multiple effects.** Favoured. New effects can be
  added to a program by defining a new effect and its handler, without
  restructuring the type signatures of every function that might
  eventually need it, unlike stacking another monad transformer.
- **Resumability.** Favoured. A handler can resume the computation that
  performed the effect, passing a value back to the exact point of
  performance, a capability an ordinary exception mechanism does not
  offer.
- **Separation of effect and interpretation.** Favoured. The code that
  performs an effect names only what it needs, an operation and its
  arguments, and stays entirely unaware of how the effect will actually
  be handled, which handler is installed, or whether it is being tested
  with a fake handler.
- **Runtime and implementation cost.** Sacrificed, in exchange for the
  above. A built-in implementation needs first-class continuations or
  an equivalent mechanism, and a library-level implementation without
  language support typically needs to encode continuations by hand,
  which carries a real performance and complexity cost.
- **Tooling and ecosystem maturity.** Sacrificed, honestly. The pattern
  is younger and less widely deployed than the Monad-based alternatives
  it competes with, so error messages, debugging tools, and community
  familiarity lag behind more established approaches in most language
  ecosystems.

## 4. Applicability and non-applicability

Reach for Algebraic Effects when the following hold.

- The program genuinely needs several effects combined, and the
  language or library gives built-in or well-supported effect
  handlers, so the composability benefit is real rather than
  theoretical.
- A computation genuinely needs to be resumed with a value after
  performing an effect, a generator-like yield, a cooperative
  scheduler, or a computation that can be paused and later continued
  from exactly where it stopped.
- The team wants to swap a real handler for a test handler without
  changing the code that performs the effect, which the pattern
  supports directly.

Do NOT reach for Algebraic Effects in these cases, and the reason
matters more than the rule.

- **The language has no built-in or well-supported effect system**,
  using a hand-rolled continuation-passing encoding purely to get
  algebraic effects in a language that was not designed for them
  usually costs more in complexity and performance than the
  composability gained is worth.
- **A single effect, or effects that never need resuming, is all the
  program needs**, plain exceptions, a plain IO type, or a single monad
  transformer already cover the need without the added conceptual
  weight of a general effect-handling mechanism.
- **The team has no experience with the pattern and the deadline does
  not allow for the learning curve**, algebraic effects are still
  genuinely unfamiliar to most working programmers, and introducing
  them under time pressure trades a real but modest composability gain
  for a real onboarding cost.

## 5. Structure

An algebraic effect system has three parts.

- **An effect signature**, declaring the operations a piece of code can
  perform, each with its argument and result type, without saying
  anything about how those operations will be carried out.
- **A perform site**, the point in ordinary code where one of those
  operations is invoked, written as an ordinary function call from the
  performing code's point of view.
- **A handler**, installed around a block of code, that intercepts a
  performed operation and decides what happens next. it can return a
  value directly, perform its own further effects, or call a resume
  function to hand a value back to the exact point the operation was
  performed and continue running the original computation from there.

Because a handler can call resume more than once, or not at all, the
same performed operation can, depending entirely on which handler is
installed, produce one result, several results, or none.

## 6. ASCII structure diagram

```
    Effect signature, declared once

    effect Ask a where
        ask :: a

    Perform site, inside ordinary-looking code

    greet () =
        name <- perform ask
        print ("hello " ++ name)

    Two different handlers around the same perform site

    handler A:
        ask -> resume "Ada"          (returns a fixed value, resumes once)

    handler B:
        ask -> resume "Grace"; resume "Barbara"
                                      (resumes twice, greet runs twice)

    handler C:
        ask -> abort "no name given" (never resumes, greet never
                                       reaches the print call)
```

## 7. Dynamics

The trace below shows one perform site handled two different ways, once
by a handler that supplies a value and resumes, and once by a handler
that resumes twice.

```
Single-resume handler

greet performs ask
   |-- control transfers to the installed handler ------->|
   |                                                       |-- handler
   |                                                       |   calls
   |                                                       |   resume "Ada"
   |<-- control returns to the perform site with "Ada" ----|
greet continues, prints "hello Ada"
handler's own code continues after resume returns

Double-resume handler

greet performs ask
   |-- control transfers to the installed handler ------->|
   |                                                       |-- handler calls
   |                                                       |   resume "Grace"
   |<-- greet runs to completion with "Grace" -------------|
   |    prints "hello Grace", handler's resume call returns
   |                                                       |-- handler calls
   |                                                       |   resume "Barbara"
   |<-- greet runs AGAIN, this time with "Barbara" --------|
   |    prints "hello Barbara"
```

## 8. Implementation variants

**Built-in language support with first-class continuations.** OCaml
5's effect handlers and Koka's effect types compile perform and resume
directly against the runtime's own continuation support, so resuming a
computation is a genuine, efficient jump back into a suspended stack
rather than a simulated construct.

**Free monad or freer monad encoding.** In a language without built-in
effect handlers, the same shape can be encoded as a free monad over a
functor describing the available operations, interpreted by a handler
function that walks the resulting tree. This is the most common way to
bring an algebraic-effects style API into a language such as Haskell or
Scala without waiting for built-in runtime support.

**Generator or coroutine-based encoding.** A language with generators
or coroutines can encode a restricted, single-resume form of the
pattern by treating a perform as a yield and a handler as the code
driving the generator, trading full multi-resume generality for using
a mechanism the host language already has.

**Effect rows and typed effect tracking.** Beyond the runtime mechanism
itself, some implementations, Koka in particular, track which effects a
function can perform directly in its type as an effect row, so the
type signature states not only the return type but the exact set of
effects the function is permitted to reach for, giving a compile-time
guarantee closer to the IO Monad's purity discipline while keeping the
composability algebraic effects add.

## 9. Known production uses

**OCaml 5's built-in effect handlers.** OCaml's language manual
documents effect handlers as. "a mechanism for modular programming with
user-defined effects", introduced as a built-in language feature in
OCaml 5.0, with additional handler syntax added in a later minor
release. OCaml manual, Effect handlers,
https://ocaml.org/manual/effects.html, verified 2026-08-21.

**Koka.** Daan Leijen's Koka language, from Microsoft Research, is
built around the pattern directly, describing itself as. "a strongly
typed functional-style language with effect types and handlers", with
effect types and effect handlers as core, first-class parts of the
language rather than a library addition. Koka language documentation,
https://koka-lang.github.io/koka/doc/book.html, verified 2026-08-21.

## 10. Consequences

Positive.

- Adding a new effect to a program means defining the effect and its
  handler, not restructuring the type signature of every function that
  might eventually reach for it, the way a new monad transformer layer
  would.
- A handler can resume a computation zero, one, or many times, a
  genuine capability beyond what an ordinary exception or a Monad-based
  effect gives, useful for backtracking, cooperative scheduling, and
  generator-style code.
- Code that performs an effect stays entirely unaware of how it will be
  handled, which makes substituting a test handler for a real one a
  first-class, structural operation rather than a separate mocking
  layer.
- In implementations with typed effect rows, a function's type can
  state exactly which effects it may perform, closing much of the gap
  with the IO Monad's compile-time purity guarantee.

Negative.

- Built-in support needs first-class continuations or an equivalent
  runtime mechanism, which most mainstream languages do not have, so
  the pattern is only available directly in a small set of languages
  and research-adjacent runtimes.
- A library-level encoding without built-in support, most often a free
  monad, carries real performance overhead and a steeper implementation
  burden than the languages with built-in support offer.
- The pattern is younger and less broadly deployed than Monad-based
  effect handling, so debugging tools, community familiarity, and
  battle-tested libraries lag behind the more established alternatives.
- Multi-resume handlers, while powerful, can produce genuinely
  surprising control flow, the same perform site's surrounding code
  running more than once, which needs real care to reason about
  correctly.

## 11. Failure modes and misuse

**Assuming every handler resumes exactly once.** Symptom. Code written
around a perform site behaves correctly under one handler and produces
duplicated side effects, or none at all, under another. Cause. The
code performing the effect was written assuming single-resume
semantics, unaware that a different handler installed elsewhere might
resume zero or several times. Fix. Treat any code following a perform
site as code that could run any number of times, and avoid placing a
genuinely non-idempotent side effect directly after a perform unless
the specific handler's resume behaviour is a documented, enforced
contract.

**Reaching for a hand-rolled continuation-passing encoding purely to
get the pattern in a language without built-in support.** Symptom. A
codebase carries a bespoke effect system built from callback chains or
manual continuation passing, adding real complexity, and the team
struggles to onboard new contributors to the encoding itself before
they can even work on the effects it carries. Cause. Wanting the
composability benefit of algebraic effects without the language or
runtime support that makes the pattern cheap to use. Fix. Prefer a
maintained free-monad or freer-monad library for the target language
over a bespoke encoding, or reconsider whether a simpler Monad-based
approach actually serves the program's real needs.

**Losing track of which handler is installed at a given perform
site.** Symptom. A perform call's behaviour is genuinely hard to
predict by reading the local code, because the answer depends entirely
on which handler happens to be installed somewhere up an invisible
call stack. Cause. Handlers installed far from the perform sites they
affect, with no local documentation of which handler is expected to be
active. Fix. Keep the handler installation close to the code it
governs where practical, and document, at each perform site, which
handler contract the surrounding code assumes.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Algebraic Effects | IO Monad plus transformer stack | Plain exceptions | Callback-based continuation-passing style |
|---|---|---|---|---|
| Adding a new effect without restructuring existing code | Yes | No, touches every transformer layer | Not applicable, one effect only | No, callback signatures ripple outward |
| Resuming with a value after the effect | Yes, built into the mechanism | No | No | Yes, but manually threaded |
| Swapping a test handler for a real one | Yes, structural | Possible via a typeclass or interface, more boilerplate | No | Possible, but invasive |
| Built-in runtime support needed | Yes, in most implementations | No, works in any language with Monad support | No | No |
| Learning cost for a team new to the pattern | High | Moderate, if the team knows Monad already | Low | Moderate to high, depending on nesting depth |

Reading of the table. Algebraic Effects win when a program genuinely
needs several composable, resumable effects and the language gives
built-in or well-supported handlers. The IO Monad plus a transformer
stack wins in languages without effect-handler support, where the
Monad discipline is already the team's shared vocabulary. Plain
exceptions win for the simple, single, abort-only case. Callback-based
continuation-passing style wins only when neither of the structured
alternatives is available and resumability is genuinely needed, though
it pays for that resumability with signatures that ripple outward
through every caller.

## 13. Related and incompatible patterns

- **IO Monad.** The Monad-based sibling pattern for the same underlying
  problem, effectful computation as a value. IO Monad favours
  compile-time purity enforcement and broad language support.
  Algebraic Effects favour composability and resumability at the cost
  of needing built-in runtime support.
- **Monad.** Effect handlers are sometimes explained as a
  generalisation of the Monad interface, but the two are genuinely
  distinct mechanisms, not one built directly on the other, and a
  language can offer either without the other.
- **Free Monad.** The most common way to encode algebraic-effects-style
  composability in a language without built-in handler support, per
  dimension 8's free monad implementation variant.
- **Continuation-Passing Style.** The lower-level mechanism a built-in
  effect-handler runtime is typically built on, and the manual
  fallback a language without built-in support has to reach for instead.
- **Exception Handling.** The closest familiar analogue, and the
  intuition most newcomers start from, an effect performs like a
  raised exception and a handler catches like a catch block, except a
  handler can also resume, which an ordinary exception mechanism
  cannot.
- **Deeply nested monad transformer stacks.** Conflicts by
  substitution rather than by direct contradiction. once a codebase has
  reached for algebraic effects to solve the composability problem,
  reintroducing a deep transformer stack alongside it defeats the
  reason the pattern was adopted in the first place.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. Ordered steps,
most relevant to a codebase whose transformer stack has become
unwieldy, or that needs genuine resumability.

1. Confirm the target language or runtime offers built-in or
   well-supported effect handlers, or identify a maintained free-monad
   library as the encoding to adopt instead.
2. Identify the effects currently threaded through a monad transformer
   stack, or through manual continuation passing, and define an effect
   signature for each.
3. Replace each effectful call site with a perform of the corresponding
   operation, leaving the calling code otherwise unaware of how the
   effect will be handled.
4. Install a handler for each effect at the appropriate boundary,
   starting with a handler whose behaviour matches the current
   transformer-based or exception-based implementation exactly, so the
   refactor is behaviour-preserving before any new capability is added.
5. Add a test substituting a test handler for the real one at a
   representative perform site, confirming the substitution changes
   only the handling, never the code that performs the effect.

Removing the pattern when it stops earning its place. Signals that it
should go include a codebase where only a single effect is ever
performed, where no handler ever resumes more than once, or where the
team's unfamiliarity with the pattern is costing more in onboarding
time than the composability is saving.

1. Confirm whether any handler in the codebase genuinely resumes more
   than once. if none does, the resumability the pattern offers is
   unused, and a simpler abort-only mechanism suffices.
2. Confirm whether more than one effect is genuinely composed at any
   perform site. if the codebase only ever performs one effect, a
   Monad-based or exception-based approach serves the same need with a
   smaller conceptual footprint.
3. Replace each perform and handler pair with the ordinary equivalent
   the confirmed usage pattern calls for, exceptions for the abort-only
   case, a single Monad for the single-effect case, one call site at a
   time, keeping tests green after each site.
4. Remove the effect signatures and handler installation code only
   after no call site depends on them.

## 15. Testing and verification

Easier because of the pattern.

- A perform site can be tested under a purpose-built test handler that
  records every operation it receives without ever touching the real
  effect, which is a structural substitution rather than a separate
  mocking framework.
- Resumability itself is directly testable, a test handler can assert
  the exact sequence of values a computation is resumed with, and
  confirm the surrounding code runs the correct number of times for
  each resume.
- Because the effect signature declares exactly which operations a
  piece of code can perform, a reviewer or a test can enumerate every
  possible effect a function might trigger directly from its
  declaration.

Harder because of the pattern.

- A multi-resume handler's control flow is genuinely harder to trace
  through ordinary step-by-step debugging than a single-pass
  Monad-based computation, since the same source location can execute
  more than once with different results each time.
- Testing the interaction of several handlers installed around the same
  computation needs a test that constructs the correct nesting order,
  and a bug in that nesting is easy to miss without a test specifically
  targeting handler composition.

Techniques that apply.

- **Recording handler substitution.** Install a test handler that
  records every performed operation and its arguments in order, and
  assert the recorded sequence matches what the code under test should
  have performed, independent of what a real handler would have done
  with each operation.
- **Resume-count assertion.** For a handler expected to resume more
  than once, assert the exact number of times the surrounding
  computation actually ran, and the exact value it was resumed with
  each time.
- **Handler-composition test.** For a computation nested inside more
  than one handler, assert operations reach the correct handler in the
  correct order, particularly when an inner handler is expected to
  intercept some operations while letting others propagate to an outer
  handler.
- **Behaviour-preservation test during migration.** When refactoring an
  existing transformer-based or exception-based implementation toward
  algebraic effects, per dimension 14, keep the original implementation's
  test suite passing against the new handler-based implementation
  before adding any new capability.

## 16. Observability signals

Algebraic effects are, like the IO Monad, primarily a language and
runtime discipline rather than an independent runtime component with
its own natural metrics, and inventing a dedicated production signal
purely for the type itself would be dishonest. Two things are worth
watching in a codebase that relies on it.

What to record.

- The nesting depth of installed handlers around a hot code path, since
  a deeply nested handler stack can carry a real per-perform overhead
  in implementations without highly optimised built-in support, and a
  growing depth is a signal worth tracking over time.
- The count of distinct effect signatures a single function's type
  declares it can perform, in implementations with typed effect
  tracking, since a function whose effect row keeps growing is often a
  function that has taken on too many responsibilities.

A healthy state. Handler nesting stays shallow and stable at the hot
paths that matter for latency, and a function's declared effect set
stays small and matches its stated responsibility.

A failing state. Handler nesting depth grows over releases with no
review catching it, a profiler shows perform-and-resume overhead
showing up in a latency-sensitive path, or a function's effect row has
grown to cover concerns unrelated to what its name and its callers
expect it to do.

## 17. Security and privacy implications

Algebraic effects' explicit perform-and-handle structure is, like the
IO Monad's type discipline, generally a security positive, since it
makes every place a piece of code can reach outside itself visible as
a named operation rather than an implicit side effect. Two practical
implications are worth naming.

**An unexpected or malicious handler can intercept an operation
silently.** Because a perform site has no visibility into which
handler is actually installed above it, code that trusts a specific
handler's contract, a logging handler that never touches sensitive
data, for example, needs that trust to be enforced structurally, not
merely assumed, since a differently behaving handler installed by
mistake or by a change elsewhere in the call stack can intercept the
same operation with entirely different behaviour.

**Multi-resume handlers can duplicate a sensitive side effect.**
Because a handler can resume a computation more than once, any code
following a perform site that performs a genuinely sensitive,
non-idempotent action, sending a payment confirmation, writing an audit
log entry exactly once, needs an explicit guarantee from its handler
contract that it will be resumed at most once, rather than an assumption
carried over from single-resume intuition.

## Code examples

Three languages where the pattern is genuinely idiomatic in different
ways. TypeScript models a small algebraic-effects-style API using
generator functions, where yield stands in for perform and the driving
loop around the generator stands in for the handler, the closest
approximation available without built-in effect-handler support. Python
shows the same generator-driven encoding, since Python's generators
offer the same send-based resume mechanism TypeScript's do. Swift shows
a simplified, single-resume encoding using a closure-based handler
protocol, since Swift has neither built-in effect handlers nor a
generator-with-send mechanism to lean on. Java and Go are omitted,
because neither language's generator or coroutine support gives a
send-based resume mechanism clean enough to demonstrate the pattern
without a large supporting library. Rust is omitted for the same
reason noted elsewhere in this family, and because Rust's own async
and Result types, plus its lack of built-in effect handlers as of this
writing, make a faithful minimal example require more supporting code
than this entry has room for.

### TypeScript

```typescript
type Perform = { op: "ask" };

function* greet(): Generator<Perform, void, string> {
  const name: string = yield { op: "ask" };
  console.log("hello " + name);
}

function runWithHandler(program: Generator<Perform, void, string>, answer: string): void {
  let result = program.next();
  while (!result.done) {
    result = program.next(answer);
  }
}

runWithHandler(greet(), "Ada");
```

### Python

```python
from typing import Generator


def greet() -> Generator[str, str, None]:
    name = yield "ask"
    print("hello " + name)


def run_with_handler(program: Generator[str, str, None], answer: str) -> None:
    op = next(program)
    try:
        program.send(answer)
    except StopIteration:
        pass


if __name__ == "__main__":
    run_with_handler(greet(), "Ada")
```

### Swift

```swift
struct Effect<A> {
    let perform: (@escaping (String) -> A) -> A
}

func greet(handler: (String) -> Void) {
    let ask = Effect<Void> { resume in resume("Ada") }
    ask.perform { name in
        print("hello " + name)
    }
}

greet { _ in }
```

## 18. References

1. Gordon Plotkin and Matija Pretnar. "Handlers of Algebraic Effects".
   18th European Symposium on Programming, ESOP 2009, part of ETAPS
   2009, York, UK.
   https://www.research.ed.ac.uk/en/publications/handlers-of-algebraic-effects
   Verified 2026-08-21. Source of the first_described lineage claim.
2. OCaml manual. Effect handlers.
   https://ocaml.org/manual/effects.html
   Verified 2026-08-21. Source for the OCaml production use in
   dimension 9 and the quoted definition there.
3. Koka language documentation.
   https://koka-lang.github.io/koka/doc/book.html
   Verified 2026-08-21. Source for the Koka production use in
   dimension 9.
