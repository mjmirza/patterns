# Family 16. Functional Programming

Origin. Category theory in practice

39 entries, 240,728 words. Every entry carries all 18
dimensions from [the entry contract](../../docs/ENTRY-TEMPLATE.md).

## Composition

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Profunctor](profunctor.md) | canonical | 5,393 | A codebase accumulates two families of type constructors that look unrelated on the surface but are secretly the same shape. |

## Data and State

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Immutability](immutability.md) | canonical | 6,227 | A program needs to share data across time, calls, threads, retries, or users, but ordinary in-place mutation makes it unclear which version a reader sees. |
| [Persistent Data Structures](persistent-data-structures.md) | canonical | 6,890 | A program needs snapshots of data across time, but a normal mutable collection has one current shape. |
| [Structural Sharing](structural-sharing.md) | canonical | 6,098 | A program wants old and new versions of a large value at the same time. |
| [Zipper](zipper.md) | canonical | 7,113 | A program holds an immutable, recursively defined structure, most often a tree but sometimes a list, and it needs to walk to an arbitrary position inside that structure, read or ... |

## Effects

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Algebraic Effects](algebraic-effects.md) | emerging | 4,105 | A program built from the IO Monad or a stack of monad transformers gets real benefits, effects are visible in the type, and composition follows well-understood laws. |
| [IO Monad](io-monad.md) | canonical | 4,053 | A purely functional language gives every function a strong guarantee. |

## Error Handling

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Validation Applicative](validation-applicative.md) | canonical | 4,677 | A form, a configuration file, or an API request body carries several independent fields, and each field has its own validation rule, a required field, a numeric range, a format ... |

## Functional

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Algebraic Data Type](algebraic-data-type.md) | canonical | 6,311 | A domain value often has several legitimate shapes, but ordinary object or record modeling makes those shapes look like one bag of optional fields. |
| [Applicative](applicative.md) | canonical | 6,000 | A program often has several values that are not plain values. |
| [Continuation](continuation.md) | canonical | 6,344 | A computation cannot finish by returning to its immediate caller, because the rest of the work must be selected, stored, resumed, aborted, retried, scheduled, or exposed as a ... |
| [Continuation-Passing Style](continuation-passing-style.md) | canonical | 6,152 | A computation has a next step that matters as much as the value being computed. |
| [Currying](currying.md) | canonical | 6,637 | A codebase has small operations that share some arguments across many calls but vary another argument late in a pipeline. |
| [Foldable](foldable.md) | canonical | 6,486 | A codebase has many structures that contain zero, one, or many values, and many operations ask the same question: how do we collapse this structure to one answer without teaching ... |
| [Free Monad](free-monad.md) | established | 6,053 | A team has a domain language whose operations need to be composed in dependent order, but the team also needs to delay the meaning of those operations. |
| [Function Composition](function-composition.md) | canonical | 7,310 | A program has several small transformations that must run in a fixed order. |
| [Functor](functor.md) | canonical | 6,739 | A codebase has many values that are not plain values. |
| [Lazy Evaluation](lazy-evaluation.md) | canonical | 6,415 | A program has a chain of computations, but early execution would do work that may never be observed. |
| [Lens](lens.md) | established | 6,096 | A program owns nested immutable data and needs to update a small part without losing the larger value. |
| [Memoization](memoization.md) | canonical | 6,478 | A program repeatedly asks the same pure question, and each answer costs more than a map lookup. |
| [Monad](monad.md) | canonical | 6,350 | A program has computations that return values inside a policy, and later computations depend on the successful, present, parsed, or completed result of earlier computations. |
| [Monoid](monoid.md) | canonical | 6,362 | A codebase has many places that reduce many values into one value. |
| [Optics](optics.md) | established | 6,315 | A program owns nested, value-oriented data and must repeatedly access parts of it without turning every access into hand-written plumbing. |
| [Option Maybe](option-maybe.md) | established | 6,033 | A function can legitimately have no value to return. |
| [Partial Application](partial-application.md) | canonical | 6,334 | A program repeatedly calls the same operation with a stable prefix of arguments. |
| [Pattern Matching](pattern-matching.md) | established | 5,354 | A program receives a value whose exact case, shape, or constructor determines the next computation. |
| [Point-free Style](point-free-style.md) | established | 6,347 | A function often mentions an argument only to feed it into another function. |
| [Prism](prism.md) | established | 6,263 | A program models alternatives. A payment can be pending, authorized, captured, or failed. |
| [Railway-Oriented Programming](railway-oriented-programming.md) | established | 6,631 | A program has a sequence of operations where each later operation should run only if earlier operations succeeded. |
| [Reader Monad](reader-monad.md) | established | 6,589 | A program has many functions that need the same read-only context. |
| [Result Either](result-either.md) | established | 6,041 | A program has operations that can fail in expected, meaningful ways. |
| [Semigroup](semigroup.md) | canonical | 6,298 | A codebase needs to combine values that are already present. |
| [State Monad](state-monad.md) | established | 6,386 | A computation needs a current value that changes after each step, and later steps depend on the changed value. |
| [Tagless Final](tagless-final.md) | established | 6,329 | A team has an operation vocabulary that many programs should use, but the team does not want those programs tied to one concrete runtime. |
| [Tail Call Optimization](tail-call-optimization.md) | established | 6,508 | A program has a call that is the last action of a function. |
| [Trampolining](trampolining.md) | established | 6,453 | A program expresses repetition, descent, or mutual recursion through function calls. |
| [Transducer](transducer.md) | established | 6,385 | A codebase has the same element transformations repeated across several data contexts. |
| [Traversable](traversable.md) | canonical | 6,123 | A program has a structure of values and a function that validates, parses, loads, checks, or annotates one value at a time. |
| [Writer Monad](writer-monad.md) | established | 6,046 | A computation has a primary result and also produces append-only side output that should remain available to the caller. |

## Reading order

Entries are independent. Each one names the patterns it composes with and
the patterns it conflicts with in dimension 13, so following those links
gives a better path than reading top to bottom.

Generated by `tools/gen-indexes.py`. Do not edit by hand.
