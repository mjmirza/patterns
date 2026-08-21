---
name: Lens
slug: lens
family: 16-functional
category: Functional
aliases: [Functional Reference, Optic, Total Lens, Van Laarhoven Lens]
first_described: "N. F., Greenwald, Moore, Pierce, Schmitt 2007"
maturity: established
related: [functor, profunctor, traversal, prism, optional, getter, setter]
incompatible_with: [partial-focus-as-total-lens, mutating-setter, shape-changing-update]
verified: 2026-08-02
---

# Lens

## 1. Name, aliases, and lineage

The canonical software name is Lens. In functional programming, a lens is a
first-class description of one focused part inside a larger value. The focus can
be read, replaced, or modified while the rest of the value is rebuilt according
to the same rule. Monocle describes `Lens[S, A]` as an optic used to zoom inside
a product, where `S` is the product and `A` is an element inside it
(https://www.optics.dev/Monocle/docs/optics/lens, verified 2026-08-02). Ramda
documents `lens` as a constructor from getter and setter functions and gives the
Van Laarhoven shape `Functor f => (a -> f a) -> s -> f s`
(https://ramdajs.com/docs/#lens, verified 2026-08-02).

The term has older roots in bidirectional programming. N. F., Michael B.
Greenwald, Jonathan T. Moore, Benjamin C. Pierce, and Alan Schmitt published the
2007 paper "Combinators for Bidirectional Tree Transformations. A Linguistic
Approach to the View Update Problem" in *ACM Transactions on Programming
Languages and Systems*, volume 29, issue 3, article 17. The abstract names
bidirectional transformations "lenses" and describes one direction that maps a
concrete tree to a view and another direction that maps an edited view plus the
original tree back to an updated concrete tree
(https://www.researchgate.net/publication/43921655_Combinators_for_bidirectional_tree_transformations_A_linguistic_approach_to_the_view-update_problem,
verified 2026-08-02). This entry covers the data-access lens common in
functional application code, not the full domain-specific language from that
paper.

The modern optics account was made explicit by Matthew Pickering, Jeremy
Gibbons, and Nicolas Wu in "Profunctor Optics. Modular Data Accessors", *The Art,
Science, and Engineering of Programming*, volume 1, issue 2, article 7, 2017.
The arXiv record says data accessors for record fields, union variants, and
container elements are collectively known as optics, and that the paper presents
a profunctor-based framework for composing them
(https://arxiv.org/abs/1703.10857, verified 2026-08-02).

Common aliases are **functional reference**, **optic**, **total lens**, and
**Van Laarhoven lens**. "Optic" is broader than lens. It includes lenses,
prisms, traversals, isomorphisms, and related accessors. Monocle, Ramda,
monocle-ts, and Partial Lenses all use the optics vocabulary in their public
documentation
(https://www.optics.dev/Monocle/, verified 2026-08-02;
https://ramdajs.com/docs/#lens, verified 2026-08-02;
https://gcanti.github.io/monocle-ts/modules/Lens.ts.html, verified 2026-08-02;
https://calmm-js.github.io/partial.lenses/, verified 2026-08-02).

The word "lens" is overloaded outside this context. A database view, a UI
selector, or a monitoring view may be called a lens in ordinary English. Those
uses are not this pattern unless they define a reusable read and write focus
with lawful composition.

## 2. Problem and context

A program owns nested immutable data and needs to update a small part without
losing the larger value. The code starts with a plain record, then grows a
second level, then a third. Soon a change such as "rename the shipping city" or
"increase the retry delay" turns into a copy cascade. The business operation is
small, but the structural plumbing is large.

The same problem appears on the read side. Many call sites need the same nested
field. One helper reads it. Another helper updates it. A third helper modifies
it. A fourth helper reads a neighboring field. The helper names start to encode
paths through data rather than domain decisions. If a field moves, the path must
be edited in many places.

Lens solves the narrow form of that problem. It names a path to exactly one
focus in a product-like structure and makes that path a value. Once the path is
a value, code can compose it with another path, pass it to generic operations,
test its laws, and choose between `view`, `set`, and `over` without rewriting
the path. Monocle documents the operations as `get`, `replace`, and `modify`
for a `Lens[S, A]` (https://www.optics.dev/Monocle/docs/optics/lens, verified
2026-08-02). Ramda exposes the same usage family through `view`, `set`, and
`over` (https://ramdajs.com/docs/#lens, verified 2026-08-02).

The context is immutable or value-oriented data. In a mutable object graph,
`customer.address.city = "Berlin"` already names a place and changes it in
place. A lens may still help if the team wants a reusable focus, but it is no
longer paying for immutable rebuilding. In persistent data structures, value
objects, state reducers, configuration trees, protocol payloads, and compiler
ASTs, the rebuild is the core cost.

There is also a compositional context. A single getter and setter pair can be
clear. The pattern becomes useful when the same path is composed with other
paths. A lens from `Order` to `Customer`, composed with a lens from `Customer`
to `Address`, composed with a lens from `Address` to `City`, becomes a lens from
`Order` to `City`. Pickering, Gibbons, and Wu state the general issue as making
data accessors first-class and combinable for compound structures
(https://arxiv.org/abs/1703.10857, verified 2026-08-02).

Lens is not a general query language. A total lens focuses one part that is
always present. If a path can be absent, can match zero or many values, can
select a union branch, or can fail validation, the code is asking for another
optic. The common replacements are Optional, Prism, Traversal, or a domain query
function. The name "lens" should stay narrow, because the laws depend on the
focus being stable.

The pattern also appears when state is split by ownership. A UI reducer may own a
large state record, while a child component should know only about its small
state slice. Passing a lens to the child gives it a way to read and propose
updates for that slice without receiving the full state representation.
Engineering judgement: this is useful when the child is a reusable component and
dangerous when the child starts to coordinate parent-level invariants. The lens
should move access, not business authority.

Another context is schema migration. A service may expose a stable settings
model while storing several versions of the data. A lens can focus the stable
field after the compatibility layer has decoded the stored shape. Engineering
judgement: keep version repair outside the lens. A lens over a decoded value is
easy to reason about. A lens that silently repairs old schema shapes during
`set` is a migration routine disguised as an accessor.

## 3. Forces

This dimension is engineering judgement, except where a named source is cited.

- **Coupling.** Favoured. Code that modifies a field depends on a focus value,
  not on every constructor and copy expression along the path.
- **Consistency.** Favoured when the lens is lawful. Monocle states
  `getReplace` and `replaceGet` laws for `Lens`, and monocle-ts documents
  three laws: get after set returns the set value, set after get returns the
  original structure, and setting twice is the same as the final set
  (https://www.optics.dev/Monocle/docs/optics/lens, verified 2026-08-02;
  https://gcanti.github.io/monocle-ts/modules/Lens.ts.html, verified
  2026-08-02).
- **Latency.** Mixed. A lens adds function calls around access. For immutable
  updates, the main cost is rebuilding the path from the root to the focus.
  That cost already exists in manual copy code.
- **Allocation cost.** Mixed. Updating immutable records usually allocates a new
  value for each level on the path. A lens centralizes the work but does not
  erase it.
- **Operability.** Sacrificed if the focus is anonymous. Stack traces and logs
  may show `over` or `modify` without a domain path name.
- **Team topology.** Favoured when a platform team owns shared domain types and
  exports lenses. Product teams can update nested fields without learning each
  constructor.
- **Cognitive load.** Sacrificed. A reader must know the difference between
  Lens, Optional, Prism, and Traversal, and must understand lens laws.
- **Cost of change.** Favoured when the internal structure changes but the
  exported focus remains. Sacrificed when a public lens escapes too early and
  freezes a field-level API that should have stayed private.
- **Security and privacy.** Mixed. A lens can centralize approved access to a
  sensitive field, but it can also make that field easier to read or copy.

Lens favours composable local updates. It sacrifices directness and, in some
languages, type simplicity.

## 4. Applicability and non-applicability

Reach for Lens when the following hold.

- A value has a stable, always-present part that callers need to read and
  update.
- The data is immutable, persistent, or treated as a value even if the host
  language permits mutation.
- The same nested path appears in several read, set, or modify operations.
- The focus path composes with other focus paths.
- The team can test the lens laws for custom lenses.
- A library API wants to expose focused access without exposing all constructors
  or internal field order.
- Reducer-style code needs many small, isolated state updates.
- Generated lenses are available for records and the generation output is part
  of the build contract.

Do NOT reach for Lens in these cases.

- **The focus may be absent.** A total lens promises a target. Use Optional,
  Prism, `Option`, `Maybe`, or a domain lookup that returns absence.
- **The focus may select many values.** Use Traversal. A lens that points at
  "all matching items" will break get and set laws.
- **The update changes shape.** Filtering, sorting, inserting siblings, or
  deleting a node is not a one-focus replacement.
- **The operation depends on sibling values in a complex way.** A domain
  function is clearer when the rule is "if status is active, normalize city and
  recompute tax zone."
- **The field is private for a reason.** Exporting a lens can turn an internal
  representation into a public compatibility promise.
- **A mutable reference is the intended abstraction.** In low-level code, a
  pointer, reference, or setter method may express the cost and side effects
  more honestly.
- **The path is used once.** Manual copy code may be shorter and easier to
  delete.
- **The language lacks enough type support and the team will encode optics with
  `any` or reflection.** That loses the main benefit: checked access.
- **The setter cannot obey the laws.** If setting the focus also increments a
  counter, rewrites another field, triggers I/O, or clamps the value without the
  type saying so, it is not a lawful lens.

## 5. Structure

Five participants define the pattern.

- **Whole.** The larger value being inspected or rebuilt. In type notation this
  is often `S`.
- **Focus.** The part inside the whole. In type notation this is often `A`.
- **Getter.** A pure function from whole to focus.
- **Updater.** A pure function that takes a replacement or focus-transforming
  function and returns a rebuilt whole.
- **Lens value.** The composed abstraction that holds the getter and updater, or
  an equivalent higher-order representation.

The simplest representation is a pair of functions. Monocle shows construction
of a `Lens[Address, Int]` from `get: Address => Int` and
`replace: Int => Address => Address`
(https://www.optics.dev/Monocle/docs/optics/lens, verified 2026-08-02). Ramda
constructs a lens from a getter and a setter and says the setter should not
mutate the data structure (https://ramdajs.com/docs/#lens, verified
2026-08-02).

The Van Laarhoven representation stores less visible machinery. It represents a
lens as a function that can map an effectful change over the focus and rebuild
the whole. Ramda documents this type shape in JavaScript notation, and the
Haskell `lens` source documentation describes `Lens s t a b` as
`forall f. Functor f => (a -> f b) -> s -> f t`
(https://ramdajs.com/docs/#lens, verified 2026-08-02;
https://hackage.haskell.org/package/lens/docs, verified 2026-08-02).

The profunctor representation changes the internal encoding again. Pickering,
Gibbons, and Wu describe a profunctor framework that makes different optics
compose through the same representation
(https://arxiv.org/abs/1703.10857, verified 2026-08-02). That form matters more
for library authors than for most application code.

## 6. ASCII structure diagram

```text
  +-------------------+       contains        +------------------+
  |       Whole S     |---------------------->|      Focus A     |
  |-------------------|                       +------------------+
  | other fields      |                                ^
  | focus field       |                                |
  +-------------------+                                |
           ^                                           |
           | rebuilds                                  | reads
           |                                           |
  +-------------------+       packages        +------------------+
  |      Updater      |<----------------------|      Getter      |
  |-------------------|                       |------------------|
  | set A in S -> S   |                       | get S -> A       |
  | over A -> A       |                       +------------------+
  +-------------------+                                ^
           ^                                           |
           |                                           |
           +-------------------+-----------------------+
                               |
                       +---------------+
                       |   Lens S A    |
                       |---------------|
                       | view          |
                       | set           |
                       | over          |
                       +---------------+

  The lens is the reusable focus. It does not own the whole or the focus value.
```

## 7. Dynamics

A lens operation has two paths. Reading takes the getter path. Updating takes the
getter path to find the old focus, applies a replacement or modification, then
takes the updater path to rebuild the whole.

```text
Client             Lens<Order, City>       Getter chain       Updater chain
  |                       |                     |                    |
  |-- view(order) ------->|                     |                    |
  |                       |-- get order ------->|                    |
  |                       |<-- city ------------|                    |
  |<-- city --------------|                     |                    |
  |                       |                     |                    |
  |-- over(upcase, order)>|                     |                    |
  |                       |-- get order ------->|                    |
  |                       |<-- old city --------|                    |
  |                       |-- upcase(old city)                       |
  |                       |-- rebuild order ----------------------->|
  |                       |<-- updated order -----------------------|
  |<-- updated order -----|                     |                    |

  Composition nests these steps. Each small lens rebuilds its own level.
```

The dynamic rule is ordinary and strict: `view` observes the current focus,
`set` replaces it, and `over` transforms it. The pattern becomes powerful
because the same composed focus drives all three operations. In Ramda,
`R.view`, `R.set`, and `R.over` accept a lens argument
(https://ramdajs.com/docs/#view, verified 2026-08-02;
https://ramdajs.com/docs/#set, verified 2026-08-02;
https://ramdajs.com/docs/#over, verified 2026-08-02).

## 8. Implementation variants

**Getter and setter record.** The direct encoding stores two functions. It is
easy to implement in TypeScript, Python, Java, Go, Rust, and Swift. The trade is
that composition must be written by the library, and advanced optic composition
does not fall out of the encoding.

```python
from dataclasses import dataclass, replace
from typing import Callable, Generic, TypeVar

S = TypeVar("S")
A = TypeVar("A")
B = TypeVar("B")

@dataclass(frozen=True)
class Lens(Generic[S, A]):
    get: Callable[[S], A]
    set: Callable[[A, S], S]

    def over(self, f: Callable[[A], A], s: S) -> S:
        return self.set(f(self.get(s)), s)

    def compose(self, other: "Lens[A, B]") -> "Lens[S, B]":
        return Lens(
            lambda s: other.get(self.get(s)),
            lambda b, s: self.over(lambda a: other.set(b, a), s),
        )

@dataclass(frozen=True)
class Address:
    city: str

@dataclass(frozen=True)
class Customer:
    address: Address

address = Lens(lambda c: c.address, lambda a, c: replace(c, address=a))
city = Lens(lambda a: a.city, lambda v, a: replace(a, city=v))
customer_city = address.compose(city)

original = Customer(Address("berlin"))
updated = customer_city.over(str.title, original)
assert customer_city.get(updated) == "Berlin"
assert original.address.city == "berlin"
print(updated)
```

**Plain functions and closures.** TypeScript and JavaScript often use a closure
that returns `view`, `set`, and `over` functions. Ramda uses functional
arguments and documents `lensProp`, `lensPath`, and `lensIndex` helpers for
common object and array focuses (https://ramdajs.com/docs/#lensProp, verified
2026-08-02; https://ramdajs.com/docs/#lensPath, verified 2026-08-02;
https://ramdajs.com/docs/#lensIndex, verified 2026-08-02).

```typescript
type Lens<S, A> = {
  view: (s: S) => A;
  set: (a: A, s: S) => S;
  over: (f: (a: A) => A, s: S) => S;
};

function lens<S, A>(view: (s: S) => A, set: (a: A, s: S) => S): Lens<S, A> {
  return { view, set, over: (f, s) => set(f(view(s)), s) };
}

function compose<S, A, B>(outer: Lens<S, A>, inner: Lens<A, B>): Lens<S, B> {
  return lens(
    (s) => inner.view(outer.view(s)),
    (b, s) => outer.over((a) => inner.set(b, a), s),
  );
}

type Address = Readonly<{ city: string }>;
type Customer = Readonly<{ address: Address }>;

const address = lens<Customer, Address>(
  (c) => c.address,
  (a, c) => ({ ...c, address: a }),
);
const city = lens<Address, string>(
  (a) => a.city,
  (v, a) => ({ ...a, city: v }),
);

const customerCity = compose(address, city);
const original = { address: { city: "berlin" } } as const;
const updated = customerCity.over((s) => s.toUpperCase(), original);
console.log(customerCity.view(updated));
```

**Language-specific immutable update helper.** Go has no higher-kinded types,
so a typed pair of functions is the honest application-level form. The trade is
that each focus type usually needs a concrete instantiation or a generic helper.

```go
package main

import (
	"fmt"
	"strings"
)

type Lens[S any, A any] struct {
	Get func(S) A
	Set func(A, S) S
}

func (l Lens[S, A]) Over(f func(A) A, s S) S {
	return l.Set(f(l.Get(s)), s)
}

func Compose[S any, A any, B any](outer Lens[S, A], inner Lens[A, B]) Lens[S, B] {
	return Lens[S, B]{
		Get: func(s S) B { return inner.Get(outer.Get(s)) },
		Set: func(b B, s S) S {
			return outer.Over(func(a A) A { return inner.Set(b, a) }, s)
		},
	}
}

type Address struct{ City string }
type Customer struct{ Address Address }

func main() {
	address := Lens[Customer, Address]{
		Get: func(c Customer) Address { return c.Address },
		Set: func(a Address, c Customer) Customer { c.Address = a; return c },
	}
	city := Lens[Address, string]{
		Get: func(a Address) string { return a.City },
		Set: func(v string, a Address) Address { a.City = v; return a },
	}
	customerCity := Compose(address, city)
	updated := customerCity.Over(strings.ToUpper, Customer{Address{"berlin"}})
	fmt.Println(customerCity.Get(updated))
}
```

**Ownership-aware value update.** Rust can encode a small lens over owned values.
The trade is verbosity, but the ownership model makes accidental mutation of the
old value visible.

```rust
#[derive(Clone)]
struct Lens<S, A> {
    get: fn(&S) -> A,
    set: fn(A, S) -> S,
}

impl<S, A> Lens<S, A> {
    fn over<F>(&self, f: F, s: S) -> S
    where
        F: FnOnce(A) -> A,
    {
        (self.set)(f((self.get)(&s)), s)
    }
}

#[derive(Clone)]
struct Address {
    city: String,
}

#[derive(Clone)]
struct Customer {
    address: Address,
}

fn upcase(s: String) -> String {
    s.to_uppercase()
}

fn main() {
    let address = Lens {
        get: |c: &Customer| c.address.clone(),
        set: |a: Address, mut c: Customer| {
            c.address = a;
            c
        },
    };
    let city = Lens {
        get: |a: &Address| a.city.clone(),
        set: |v: String, mut a: Address| {
            a.city = v;
            a
        },
    };
    let c = Customer { address: Address { city: "berlin".into() } };
    let updated_address = address.over(
        |a| city.over(upcase, a),
        c,
    );
    println!("{}", updated_address.address.city);
}
```

**Generated record lenses.** Monocle documents macro generation through
`GenLens` and `@Lenses` for Scala case classes
(https://www.optics.dev/Monocle/docs/optics/lens, verified 2026-08-02). The
trade is build-time machinery. Generation reduces boilerplate, but a generated
public lens is still a public API.

Generated lenses work best when the generated names stay internal to the module
that owns the record. The owner can then bind a smaller set of domain names to
the generated field lenses. For example, an internal `_billingAddress` lens may
back a public `invoiceDestination` focus. When the record changes, the internal
binding changes and public callers keep their domain name. Engineering
judgement: this is the difference between using generation as an authoring aid
and letting generation publish the data layout.

**Van Laarhoven lens.** This is common in Haskell and libraries that mimic it.
The trade is that the type is harder to explain, while `view`, `set`, `over`,
and composition become highly uniform. Haskell `lens` and Ramda both document
the functor-based shape (https://hackage.haskell.org/package/lens/docs,
verified 2026-08-02; https://ramdajs.com/docs/#lens, verified 2026-08-02).

This variant is attractive when many optic operations share one encoding. The
same lens can be consumed by operations that read, replace, modify, or embed the
focus in a larger traversal. The cost is that error messages can mention
functors, ranks, or type aliases far from the domain field the programmer meant
to update. Engineering judgement: library authors can pay that cost once;
application teams should hide it behind names that match the domain.

**Profunctor optic.** This is the library-author form for composing multiple
optic kinds. The trade is abstraction cost. It can give a cleaner lattice of
optic capabilities, but most application teams should consume it through named
operations rather than implementing it directly. Pickering, Gibbons, and Wu
present this representation for modular data access
(https://arxiv.org/abs/1703.10857, verified 2026-08-02).

Profunctor optics matter when a library wants one composition story across lens,
prism, traversal, and isomorphism. The application symptom is that a path moves
from product fields into a sum branch or list element and ordinary lens
composition stops being the right type. A profunctor-based library can often
compose the more precise pieces and return the least capable optic that still
describes the path. Engineering judgement: that precision is valuable in shared
libraries, but can overwhelm a codebase that only needed field updates.

## 9. Known production uses

**Haskell `lens`.** The Hackage package `lens` publishes modules such as
`Control.Lens`, `Control.Lens.Lens`, `Control.Lens.Traversal`, and data-type
specific lens modules. Its documentation describes lenses, folds, traversals,
getters, setters, prisms, and related optics
(https://hackage.haskell.org/package/lens/docs, verified 2026-08-02). This is a
named production library in the Haskell ecosystem.

**Monocle.** Monocle is a Scala optics library. Its home page says it offers an
API to access and transform immutable data, and its lens documentation gives
`Lens[S, A]`, `get`, `replace`, `modify`, composition, generation, and laws
(https://www.optics.dev/Monocle/, verified 2026-08-02;
https://www.optics.dev/Monocle/docs/optics/lens, verified 2026-08-02). The
Scala index page identifies `optics-dev / monocle` as an optics library for
Scala and lists Scala 2.13 and Scala 3 artifacts
(https://index.scala-lang.org/optics-dev/monocle, verified 2026-08-02).

**Ramda.** Ramda is a JavaScript functional library whose documentation exposes
`lens`, `lensIndex`, `lensPath`, `lensProp`, `view`, `set`, and `over`.
Ramda's `lens` page gives the functor-based lens type and says the setter
should not mutate the data structure (https://ramdajs.com/docs/#lens, verified
2026-08-02).

**monocle-ts.** monocle-ts is a TypeScript optics library. Its `Lens` module
states that a lens is an optic used to zoom inside a product, documents
`Lens<S, A>`, and publishes lens laws
(https://gcanti.github.io/monocle-ts/modules/Lens.ts.html, verified
2026-08-02).

**Partial Lenses.** Partial Lenses is a JavaScript optics library for querying
and updating immutable data. Its documentation says lenses specify operations to
query and update immutable data structures and lists optics operations including
`get`, `set`, `modify`, `remove`, and `traverse`
(https://calmm-js.github.io/partial.lenses/, verified 2026-08-02).

## 10. Consequences

This dimension is engineering judgement.

Positive consequences.

- A nested path becomes a named value.
- Reads and updates share one path definition.
- Composition is local. Small lenses build larger lenses.
- Immutable update code loses repeated copy cascades.
- Custom lenses can be law-tested.
- A module can expose focused access without exposing all constructors.
- Refactoring can move the internal field while preserving the exported lens.
- Generic operations such as `view`, `set`, and `over` reduce API surface.

Negative consequences.

- The type signatures can be dense in languages that expose the full optic
  encoding.
- Debugging an anonymous composed lens can be harder than debugging direct field
  access.
- Generated lenses can leak internal structure into public API.
- Rebuilding through immutable structures still allocates.
- Law violations are easy to write with an invalid setter.
- A total lens can be misused for absent or multi-target data.
- Teams may import a full optics library for a small amount of copy reduction.
- Deep chains can hide domain rules that deserve named functions.

## 11. Failure modes and misuse

This dimension is engineering judgement, with library law references cited
where applicable.

- **Symptom.** After setting a value, reading through the same lens returns a
  different value. **Cause.** The setter writes another place, normalizes the
  value, or applies validation not visible in the focus type. **Fix.** Change
  the focus type to represent the normalized value, or replace the lens with a
  domain command. Monocle and monocle-ts both publish get after set laws
  (https://www.optics.dev/Monocle/docs/optics/lens, verified 2026-08-02;
  https://gcanti.github.io/monocle-ts/modules/Lens.ts.html, verified
  2026-08-02).
- **Symptom.** Setting the currently viewed value still changes the whole.
  **Cause.** The setter updates timestamps, counters, caches, or unrelated
  fields. **Fix.** Move that behavior out of the lens. A lens setter must rebuild
  the focus, not run a domain workflow.
- **Symptom.** Updating through a lens sometimes does nothing because the path
  is missing. **Cause.** The code used a total lens for optional data. **Fix.**
  Use Optional, Prism, or a function returning absence.
- **Symptom.** Two calls to set produce order-dependent data. **Cause.** The
  focus selection depends on the current value, such as "the first item matching
  this predicate." **Fix.** Use a stable key lookup with a lawful partial optic,
  or use a domain function. Partial Lenses documents that `L.find` alone does
  not obey all lens laws and explains how a broader composition can restrict
  writes enough to obey them (https://calmm-js.github.io/partial.lenses/,
  verified 2026-08-02).
- **Symptom.** A simple state update is unreadable because it is a long chain of
  symbols. **Cause.** The path is anonymous and the team is reading library
  vocabulary instead of domain vocabulary. **Fix.** Bind the composed lens to a
  domain name, or use a named function.
- **Symptom.** A public package cannot change its data layout without breaking
  downstream code. **Cause.** Generated lenses were exported for every field.
  **Fix.** Export only lenses that are part of the public model.
- **Symptom.** Production logs show a state update failed, but not which field
  changed. **Cause.** Lens operations were not labeled at the domain boundary.
  **Fix.** Name lenses and attach the name to reducer logs or traces.

## 12. Trade-off matrix

| Force | Lens | Manual copy/update | Mutable setter | Optional | Traversal |
|---|---|---|---|---|---|
| Coupling | Low coupling to layout when exported carefully | High coupling to constructors and paths | High coupling to object identity | Low for absent focus | Low for many focuses |
| Consistency | High if laws hold | Varies by call site | Varies by side effects | Models absence directly | Models zero or many focuses |
| Latency | Function calls plus immutable rebuild | Direct code, same rebuild cost | Usually lowest local cost | Similar to lens with absence branch | Higher for many targets |
| Allocation | Rebuilds path | Rebuilds path | Often no new whole value | Rebuilds when present | Rebuilds many positions |
| Operability | Needs names for traces | Path visible in code | Side effects need tracing | Absence is visible in type | Counts and failures need tracing |
| Team topology | Good for shared model libraries | Good for small local modules | Good for owners of mutable objects | Good for partial domains | Good for batch transforms |
| Cognitive load | Medium to high | Low | Low | Medium | Medium to high |
| Best fit | Stable single focus | One-off update | Intentional mutation | Maybe-present focus | Multiple focuses |
| Main failure | Lawless setter or wrong optic | Duplication and drift | Hidden aliasing | Treating absence as success | Accidental shape change |

## 13. Related and incompatible patterns

**Functor** underlies the Van Laarhoven encoding. Ramda documents the lens type
with a `Functor` constraint, and Haskell `lens` documentation uses the same
kind of type for `Lens` (https://ramdajs.com/docs/#lens, verified 2026-08-02;
https://hackage.haskell.org/package/lens/docs, verified 2026-08-02).

**Getter and Setter** are weaker optics. A getter only reads. A setter only
updates. A lens gives both operations with laws tying them together. Ramda lists
`view`, `set`, and `over` as related operations for a lens
(https://ramdajs.com/docs/#lens, verified 2026-08-02).

**Optional** replaces Lens when the focus may be missing. Engineering judgement:
using a total lens for a missing focus creates surprising no-ops or fabricated
default values.

**Prism** replaces Lens when focusing one case of a sum type. Pickering,
Gibbons, and Wu discuss lenses and prisms as different data accessors inside the
optics family (https://arxiv.org/abs/1703.10857, verified 2026-08-02).

**Traversal** replaces Lens when there may be zero, one, or many focuses. Haskell
`lens` publishes `Control.Lens.Traversal` beside `Control.Lens.Lens`
(https://hackage.haskell.org/package/lens/docs, verified 2026-08-02).

**Composite** pairs naturally with Lens for tree-shaped structures. Engineering
judgement: a tree node can expose lenses for child fields, but recursive
selection over many descendants is a traversal or fold.

**Command** conflicts when the operation is a domain action. If updating a field
must validate permissions, emit events, or coordinate services, a command is the
honest pattern and a lens is too small.

**Repository** conflicts when the focus crosses persistence boundaries. A lens
should not hide database reads or writes inside a setter.

## 14. Refactoring path in and out

To introduce Lens.

1. Find repeated immutable copy code for the same path.
2. Extract a named getter for the target field.
3. Extract a named pure setter that rebuilds only the path to that field.
4. Add tests for the three laws: set after get returns the original whole, get
   after set returns the set value, and the later set wins.
5. Package the getter and setter as a lens value.
6. Replace one call site with `view`, `set`, or `over`.
7. Compose only after the single-level lenses are tested.
8. Export the composed lens only if callers should depend on that focus.

The first extraction should be intentionally boring. Do not begin by installing
the largest optics library or generating lenses for every field. Start with one
manual lens whose law tests are easy to read. After that lens replaces real
duplication, compose it with one neighboring lens. If the composed name reads
like a domain concept, keep going. If the composed name reads like a structural
path, pause and ask whether a domain function would express the intent better.

When introducing Lens into an existing team, add the smallest vocabulary set:
`view`, `set`, `over`, and `compose`. Defer Prism, Traversal, indexed optics,
and profunctor terms until a real missing-focus or many-focus case appears.
Engineering judgement: optics fail socially before they fail technically. A team
that cannot read the first four operations will not be helped by a full lattice
of optic kinds.

Named refactorings that fit are Extract Function for the getter and setter,
Replace Temp with Query when manual local path variables clutter the call site,
and Encapsulate Record when the exported lens becomes the stable access point.
Those names refer to the refactoring family in this repository.

To remove Lens.

1. List the public and private call sites of the lens.
2. Inline private uses where direct field access is clearer.
3. Replace lawless or effectful setters with named domain functions.
4. Replace absent-focus uses with Optional, Prism, or a domain query.
5. Keep a compatibility wrapper for public lenses until downstream users move.
6. Delete generated lenses for fields that should no longer be public.
7. Re-run law tests for remaining optics because removal can change composition.

Engineering judgement: removal is often the right move when a model stabilizes
and only one local update remains. A lens should earn its abstraction cost every
time the path is reused or composed.

The exit path is also important during performance work. If profiling shows a
hot update rebuilding broad objects, first check whether the lens is forcing a
wide copy where a narrower persistent structure, a batched reducer, or a local
mutable builder would be more honest. Removing the lens is not a defeat. It is a
recognition that the old force balance has changed.

## 15. Testing and verification

This dimension is engineering judgement, except for cited laws.

Test a lens as a small algebra, not only through example updates.

- **Get after set.** If the lens sets value `a` into whole `s`, viewing the
  result returns `a`. Monocle calls this `replaceGet`, and monocle-ts states the
  same law as `get(set(a)(s)) = a`
  (https://www.optics.dev/Monocle/docs/optics/lens, verified 2026-08-02;
  https://gcanti.github.io/monocle-ts/modules/Lens.ts.html, verified
  2026-08-02).
- **Set after get.** If the lens reads its current focus and sets it back, the
  whole is unchanged. Monocle calls this `getReplace`
  (https://www.optics.dev/Monocle/docs/optics/lens, verified 2026-08-02).
- **Set set.** Setting twice is equivalent to the final set. monocle-ts lists
  this as a lens law (https://gcanti.github.io/monocle-ts/modules/Lens.ts.html,
  verified 2026-08-02).
- **Composition law checks.** Test composed lenses against direct access for
  representative nested values.
- **No mutation checks.** In mutable host languages, assert that the original
  whole still has the old value after `set` or `over`. Ramda says a lens setter
  should not mutate the data structure (https://ramdajs.com/docs/#lens,
  verified 2026-08-02).
- **Property tests.** Generate whole values and focus values when the domain has
  compact generators. Lens laws are well-suited to property testing because the
  expected relation is compact.
- **Boundary tests.** For generated lenses, compile examples that use each
  exported focus. This catches renamed fields and macro configuration drift.

Test doubles rarely matter for Lens itself because a lens should be pure. If a
test needs a mock database, clock, or network client to test a setter, the code
is not testing a lens. It is testing a command hidden behind lens-shaped syntax.

Verification run for this entry. The Python, TypeScript, Go, and Rust examples
were run locally with `python3`, `npx tsc` plus `node`, `go run`, and `rustc`.

## 16. Observability signals

This dimension is engineering judgement.

Pure lenses do not create production events by themselves. Observe the workflow
that uses them.

- Log the domain name of the focus at reducer or command boundaries, for
  example `customer_city_changed`, not the library operation name `over`.
- Count update attempts by focus name.
- Count no-op updates where the new whole equals the old whole.
- Track validation failures before lens use, not inside the lens.
- For generated public lenses, track downstream compile failures or deprecation
  warnings during schema migration.
- In performance traces, measure the size of the updated value and the depth of
  the rebuilt path for hot reducers.
- In JavaScript, watch allocation and garbage collection around large object
  updates, because spread-based rebuilding can copy broad structures.
- In Rust, Swift, Go, and Java, watch clone or copy counts where the lens helper
  takes owned values.

A healthy dashboard shows named state updates with low no-op rates, bounded
allocation cost, and no unexpected mutation of prior values in invariant checks.
A failing dashboard shows large object churn, many anonymous updates, repeated
no-op updates on missing paths, or law-test failures after model changes.

In event-sourced systems, record the domain event that caused the update, not
the lens path alone. A path such as `account.profile.email` tells an operator
where data moved, but not why it moved. The event name `email_verified` or
`customer_contact_corrected` carries intent. The lens name can be attached as a
low-cardinality attribute when it helps group state-update code paths.

In privacy-sensitive systems, add redaction checks to any generic diff or audit
tool that accepts a lens. The tool should know whether the focused value is safe
to print. Engineering judgement: the safest default is to require an explicit
display policy next to the lens when the value leaves memory for logs, traces,
metrics, or audit records.

## 17. Security and privacy implications

This dimension is engineering judgement.

Lens is mostly silent about security. It is an access pattern, not an
authorization pattern. It neither proves that a caller may read a field nor
proves that a caller may update it.

The main risks are exposure and copying. Exporting a lens for a sensitive field
can make that field easy to read from generic code. A composed lens can cross
from a broad object, such as an account, into a narrow secret, such as a token.
If that lens is passed to generic logging, diffing, or serialization helpers,
the helper may copy sensitive data into logs. The fix is policy outside the
lens: do not export lenses for secrets, keep redaction at the boundary, and type
secret fields so they do not format by accident.

The second risk is law-breaking validation. A setter that clamps, encrypts,
hashes, or rejects a value may be secure in intent but is not a lawful lens
unless the focus type represents the stored form. Use a domain command such as
`changePassword` or `rotateToken` for operations with authorization, audit, or
cryptographic behavior.

The pattern can close a small privacy gap when used carefully. A module can
export a lens for a permitted non-secret field while keeping the rest of the
record constructor private. That is an access-control aid at the API level, not
a runtime security boundary.

Capability passing deserves care. A lens value can be treated like a small
capability: whoever receives it can focus that part of the structure. This is
not a cryptographic capability, but it still shapes code authority. Passing a
`shippingCity` lens to a formatter is narrow. Passing an `accountToken` lens to
a generic state editor is broad and risky. Engineering judgement: review
exported lenses with the same attention given to public getters, because a lens
is both a getter and a writer.

## 18. References

- N. F., Michael B. Greenwald, Jonathan T. Moore, Benjamin C. Pierce, and Alan
  Schmitt, "Combinators for Bidirectional Tree Transformations. A
  Linguistic Approach to the View Update Problem", *ACM Transactions on
  Programming Languages and Systems*, volume 29, issue 3, article 17, 2007,
  DOI 10.1145/1232420.1232424. URL verified through ResearchGate abstract:
  https://www.researchgate.net/publication/43921655_Combinators_for_bidirectional_tree_transformations_A_linguistic_approach_to_the_view-update_problem,
  verified 2026-08-02.
- Matthew Pickering, Jeremy Gibbons, and Nicolas Wu, "Profunctor Optics.
  Modular Data Accessors", *The Art, Science, and Engineering of Programming*,
  volume 1, issue 2, article 7, 2017. https://arxiv.org/abs/1703.10857,
  verified 2026-08-02.
- Edward Kmett and contributors, `lens` package documentation, Hackage.
  https://hackage.haskell.org/package/lens/docs, verified 2026-08-02.
- Monocle maintainers, "Lens", Monocle documentation.
  https://www.optics.dev/Monocle/docs/optics/lens, verified 2026-08-02.
- Monocle maintainers, "Monocle. Access and transform immutable data."
  https://www.optics.dev/Monocle/, verified 2026-08-02.
- Scala Index, `optics-dev / monocle`.
  https://index.scala-lang.org/optics-dev/monocle, verified 2026-08-02.
- Ramda maintainers, Ramda documentation for `lens`, `lensIndex`, `lensPath`,
  `lensProp`, `view`, `set`, and `over`. https://ramdajs.com/docs/, verified
  2026-08-02.
- Giulio Canti and contributors, monocle-ts `Lens` module documentation.
  https://gcanti.github.io/monocle-ts/modules/Lens.ts.html, verified
  2026-08-02.
- Calvin Metcalf, Joonas Javanainen, and contributors, Partial Lenses
  documentation. https://calmm-js.github.io/partial.lenses/, verified
  2026-08-02.
