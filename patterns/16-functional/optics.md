---
name: Optics
slug: optics
family: 16-functional
category: Functional
aliases: [Functional Optics, Composable Data Accessors, Profunctor Optics]
first_described: "J. N. F., Greenwald, Moore, Pierce, Schmitt 2007"
maturity: established
related: [lens, prism, traversal, optional, iso, functor, profunctor]
incompatible_with: [stringly-typed-paths, mutating-accessors, effectful-getters]
verified: 2026-08-02
---

# Optics

## 1. Name, aliases, and lineage

The canonical family name is Optics. In software, an optic is a first-class
description of a focus inside a larger value, together with operations that
read, build, replace, modify, or collect that focus depending on the optic kind.
The name covers lenses, prisms, traversals, optionals, isomorphisms, folds, and
related accessors. Pickering, Gibbons, and Wu describe fields of records,
variants of unions, and elements of containers as data accessors that are
collectively known as optics, and present a profunctor treatment of the family
in "Profunctor Optics. Modular Data Accessors", *The Art, Science, and
Engineering of Programming*, volume 1, issue 2, article 7, 2017
(https://programming-journal.org/2017/1/7/, verified 2026-08-02).

The older lineage is bidirectional programming. J. Nathan F., Michael B.
Greenwald, Jonathan T. Moore, Benjamin C. Pierce, and Alan Schmitt published
"Combinators for Bidirectional Tree Transformations. A Linguistic Approach to
the View-Update Problem" in *ACM Transactions on Programming Languages and
Systems*, volume 29, issue 3, article 17, 2007. dblp records the title,
authors, journal, volume, article number, year, and DOI for that publication
(https://dblp.org/rec/journals/toplas/FosterGMPS07, verified 2026-08-02).
ResearchGate's publication page exposes the abstract and metadata for the same
paper (https://www.researchgate.net/publication/43921655_Combinators_for_bidirectional_tree_transformations_A_linguistic_approach_to_the_view-update_problem,
verified 2026-08-02). This entry covers the application programming pattern
that grew from that lineage, not the whole tree-transformation calculus.

Common aliases are **functional optics**, **composable data accessors**,
**profunctor optics**, and, in narrower contexts, **lenses**. The last alias is
imprecise. A lens is one optic for an always-present field-like focus. An optic
family also includes prisms for one branch of a sum, traversals for zero or
many focuses, optionals for zero or one focus, and isomorphisms for reversible
shape changes. Monocle documents Lens, Prism, Optional, Traversal, Iso, Getter,
Setter, Fold, and other optic types as a family under the Monocle project
(https://www.optics.dev/Monocle/, verified 2026-08-02). optics-ts describes
optics as values that compose, with different optic kinds tracking how many
focuses they may have and which operations they support
(https://akheron.github.io/optics-ts/reference-intro/, verified 2026-08-02).

The lineage matters because "optic" is not a synonym for "path string". A path
string says where something might be. An optic carries a typed contract about
what kind of focus exists, whether absence is possible, how modification
behaves, and how it composes with other focuses. The Haskell `lens` package
exports many optics and optic operations through modules such as
`Control.Lens.Type`, `Control.Lens.Prism`, and `Control.Lens.Traversal`
(https://hackage.haskell.org/package/lens/docs, verified 2026-08-02). Partial
Lenses describes its JavaScript library as
offering composable, partially applicable lenses and related optics for nested
data (https://calmm-js.github.io/partial.lenses/, verified 2026-08-02).

Engineering judgement. In daily engineering speech, use "Optics" only when the
code depends on the family property. If the code uses one total record field,
call it a lens. If it handles one variant, call it a prism. The family name is
earned when composition across several optic kinds is central to the design.

## 2. Problem and context

A program owns nested, value-oriented data and must repeatedly access parts of
it without turning every access into hand-written plumbing. At first the code
uses a direct field read or a local pattern match. Then the same focus appears
in a reducer, a serializer, a validation rule, a user-interface adapter, and a
migration routine. Some places read it. Some replace it. Some modify it only
when it is present. Some collect many matching values. Some build a variant
from a smaller value. The structure of the data leaks into many unrelated
operations.

The pressure grows when the data is immutable. Updating a nested field means
rebuilding every enclosing value on the path. A manual update states the same
path twice, once on the read side and once in the copy expression. If the field
moves, every call site becomes suspect. If a missing branch is treated like a
present field, the program may throw at runtime. If a many-focus traversal is
treated like a single-focus update, business logic may silently touch too much
or too little data.

Optics solve the structural part of that problem by turning access into values.
A lens from `Order` to `Customer`, composed with a lens from `Customer` to
`Address`, composed with a lens from `Address` to `City`, is an optic from
`Order` to `City`. If the path crosses an optional field, a prism, or a list,
the resulting optic kind changes so the supported operations reflect the path.
Monocle documents composition between optic types and shows optics as ordinary
values that can be chained with methods such as `andThen`
(https://www.optics.dev/Monocle/docs/optics/lens, verified 2026-08-02;
https://www.optics.dev/Monocle/docs/optics/prism, verified 2026-08-02).
optics-ts describes optic composition and the way a composed optic keeps track
of focus cardinality and supported operations
(https://akheron.github.io/optics-ts/reference-intro/, verified 2026-08-02).

The pattern fits value objects, persistent data structures, typed configuration
trees, compiler abstract syntax trees, domain events, reducers, protocol
messages, data migration adapters, and nested JSON at a boundary. It fits less
well when the domain operation is behavior rather than structural access. If a
payment transitions from authorized to captured, a domain transition method may
be clearer than an optic to the status field. If a route handler authorizes a
user, an optic to `request.user.role` is not an authorization model. The optic
should remove repeated structural code. It should not hide a domain decision.

There is a second context: library boundaries. A model owner may want to expose
a stable focus while keeping constructors, storage layout, and field order
private. The public optic becomes a compatibility promise. That is powerful and
costly. It lets downstream code compose against a named focus, but it also
turns that focus into API surface. Engineering judgement: publish optics for
concepts the domain team is willing to support across releases. Keep internal
implementation paths private.

Optics are also useful at typed boundaries over weakly typed data. A parser may
convert JSON to a typed domain tree, then optics over the typed tree can be
lawful and checked. By contrast, optics directly over raw maps and arrays need
care. They can become stringly typed paths with a functional vocabulary. RFC
9535 standardizes JSONPath as a query language for JSON values, including
selectors and nodelists (https://www.rfc-editor.org/rfc/rfc9535.html, verified
2026-08-02). JSONPath is a query tool, not the same pattern as typed optics,
because it does not by itself supply the same typed modify and composition
contract.

## 3. Forces

This dimension is engineering judgement except where a cited source describes a
library or formal relationship.

- **Coupling.** Favoured. Code depends on a named focus rather than repeated
  field paths, copy expressions, and branch tests.
- **Consistency.** Favoured when custom optics obey their laws. Monocle states
  laws for lenses and prisms, while monocle-ts states lens and prism laws in
  its module documentation
  (https://www.optics.dev/Monocle/docs/optics/lens, verified 2026-08-02;
  https://www.optics.dev/Monocle/docs/optics/prism, verified 2026-08-02;
  https://gcanti.github.io/monocle-ts/modules/Lens.ts.html, verified
  2026-08-02; https://gcanti.github.io/monocle-ts/modules/Prism.ts.html,
  verified 2026-08-02).
- **Latency.** Mixed. An optic adds function calls and composition layers. A
  hand-written path may be faster in a tight loop. In ordinary reducer and
  configuration code, the readability and reuse can outweigh the call cost.
- **Allocation cost.** Mixed. Immutable updates allocate rebuilt outer values.
  Optics centralize that allocation pattern but do not remove it.
- **Consistency of absence.** Favoured. A prism or optional represents absence
  in the operation shape instead of hiding it behind a null check or exception.
- **Operability.** Favoured if optics have domain names that appear in logs and
  traces. Sacrificed if production diagnostics show only anonymous composed
  functions.
- **Team topology.** Favoured when model teams publish tested optics and
  feature teams compose them. Sacrificed when every team invents local optics
  over the same model and the law burden scatters.
- **Cognitive load.** Sacrificed. Readers must learn lens, prism, traversal,
  optional, iso, fold, and composition rules. This cost is real.
- **Cost of change.** Favoured when internal shape changes behind stable
  optics. Sacrificed when optics are exported too early and freeze field-level
  API surface.
- **Security and privacy.** Mixed. A named optic can centralize a permitted
  access path. It can also make sensitive fields too easy to read or copy if
  module boundaries are loose.

The pattern favours composable structural access. It sacrifices direct local
code, some type simplicity, and some runtime transparency.

## 4. Applicability and non-applicability

Reach for Optics when the following hold.

- The same nested focus appears in several reads, updates, previews, or
  collections.
- The data is immutable or treated as a value by convention.
- Different path segments have different focus kinds, such as an always-present
  field followed by an optional branch followed by many children.
- The team wants accessors to compose as values.
- A library boundary needs to expose focused access without exposing full
  representation.
- The host language or library can carry focus type, absence, and cardinality
  without collapsing to unchecked dynamic access.
- Custom optics can be tested against their laws.
- The focused operation is structural access, not domain workflow.

Do NOT reach for Optics in these cases.

- **The operation appears once.** A local field read, match expression, or copy
  expression may be easier to read and delete.
- **The focus is mutable state with intended identity.** A pointer, reference,
  setter method, or transaction object may state side effects more clearly.
- **The selection is a query over unknown shape.** JSONPath, SQL, XPath, or a
  domain query language may fit better than typed optics over untyped data. RFC
  9535 defines JSONPath as a query language for JSON values
  (https://www.rfc-editor.org/rfc/rfc9535.html, verified 2026-08-02).
- **The update changes unrelated domain invariants.** If setting a city must
  recalculate tax, verify shipping restrictions, and emit a domain event, use a
  domain function.
- **The getter or setter performs I/O.** An optic should be a structural
  accessor. Database reads, network calls, metrics writes, and cache mutation
  belong outside it.
- **The setter cannot obey the relevant laws.** Clamping, normalization,
  logging side effects, and sibling rewrites can make an accessor useful, but
  they make it a poor optic unless the type encodes that policy.
- **The team will encode every path as a string.** That loses most of the value
  of typed composition and raises runtime failure risk.
- **The public API is not ready to promise field-level access.** Exporting an
  optic can freeze internals before the model is stable.
- **The language makes the abstraction unreadable.** If generic types become
  harder to understand than manual code, the pattern is not earning its place.
- **The focus carries authority.** A child component receiving an optic to a
  state slice should not gain permission to coordinate parent-level business
  rules.

The non-applicability list is part of the pattern. Optics are for reusable,
lawful structural access. They are not a replacement for validation,
authorization, query planning, side-effect control, or domain workflow.

## 5. Structure

The participants depend on the optic kind, but the family has a common shape.

- **Whole.** The larger value being inspected, rebuilt, matched, or traversed.
  Many libraries write this type as `S`.
- **Focus.** The smaller value or values reached by the optic. Many libraries
  write this type as `A`.
- **Optic kind.** The contract that says what focus cardinality and operations
  are valid. Lens means one present focus. Prism means zero or one branch, with
  a way to build the branch. Traversal means zero or many focuses. Iso means a
  reversible mapping. Optional means zero or one focus without the build
  promise of a prism.
- **Interpreter operation.** A generic operation such as view, preview, set,
  over, review, fold, or collect. The operation is legal only for optic kinds
  that support it.
- **Composition rule.** The rule that combines two optics and returns an optic
  whose kind reflects both segments. A lens followed by a prism is no longer a
  total lens, because the composed focus may be absent.
- **Law contract.** The behavioral contract that keeps access and update
  coherent. Lens laws, prism round-trip laws, traversal laws, and iso laws are
  checked in tests for hand-written optics.
- **Data owner.** The module or team that owns the data representation and
  exports selected optics.
- **Client operation.** The code that uses an optic value to perform a read,
  update, preview, or collection without restating the path.

The simplest implementation stores getter and setter functions for a lens.
Richer libraries use higher-order encodings. Ramda documents `lens` as a
constructor from getter and setter functions and gives the Van Laarhoven type
shape in its docs (https://ramdajs.com/docs/#lens, verified 2026-08-02).
Pickering, Gibbons, and Wu present profunctor optics as a modular encoding for
data accessors (https://programming-journal.org/2017/1/7/, verified
2026-08-02). The engineering structure is the same from the client viewpoint:
access paths become typed, composable values.

## 6. ASCII structure diagram

```text
 +-----------------+      exports       +--------------------------+
 |   Data Owner    | -----------------> |      Named Optics        |
 |-----------------|                    |--------------------------|
 | Order           |                    | orderCustomer : Lens     |
 | Customer        |                    | customerAddress : Lens   |
 | Address         |                    | paymentFailure : Prism   |
 | Payment         |                    | orderLines : Traversal   |
 +-----------------+                    +--------------------------+
                                                  |
                                                  | compose
                                                  v
                                      +--------------------------+
                                      |      Composed Optic      |
                                      |--------------------------|
                                      | Whole type: Order        |
                                      | Focus type: String       |
                                      | Kind: Optional or Lens   |
                                      +--------------------------+
                                                  |
                                                  | interpret
                                                  v
 +-----------------+       input        +--------------------------+
 |  Client Code    | -----------------> | view, preview, over, set |
 |-----------------|                    | collect, review, fold    |
 | reducer         | <----------------- | result or rebuilt whole  |
 | serializer      |      output        +--------------------------+
 | validator       |
 +-----------------+
```

## 7. Dynamics

At runtime, an optic is inert until an operation interprets it. Composition
builds a larger focus description. The operation then walks the path according
to the optic kinds in that description, applies the read or update, and rebuilds
the affected outer values if needed.

```text
Client             Optic A          Optic B          Operation        Whole
  |                  |                |                  |              |
  | compose(A, B)    |                |                  |              |
  |----------------->|                |                  |              |
  |                  |-- combine ---->|                  |              |
  |<--------- composed optic ----------------------------|              |
  |                                                     |              |
  | over(composed, f, whole)                            |              |
  |---------------------------------------------------->|              |
  |                                                     |-- read A --->|
  |                                                     |<-- part A ---|
  |                                                     |-- read B --->|
  |                                                     |<-- focus ----|
  |                                                     |-- f(focus)   |
  |                                                     |-- rebuild B |
  |                                                     |-- rebuild A |
  |<----------------------------------------- rebuilt whole            |
  |                                                                    |
```

When a segment may miss, the dynamic path changes. A prism that fails to match
does not call the focus-changing function. A traversal with zero matches calls
the function zero times. A traversal with three matches calls it three times
and rebuilds each changed branch. This is the reason the optic kind must travel
with the value. The client operation cannot treat all focus paths as one total
field.

Consider a reducer that uppercases every city in all shipping addresses for
orders that are still editable. The composed optic might start with a traversal
over orders, pass through a prism for editable status, pass through a lens for
customer, pass through an optional for shipping address, and end with a lens for
city. The operation is one `over`, but the dynamics are not one field write.
They are a controlled walk through many branches, with no action on missing or
non-matching branches.

Engineering judgement. Keep such composed paths named. A name such as
`editableShippingCities` gives logs, tests, and reviews a domain handle. An
anonymous chain inside a large reducer can be as hard to understand as the
manual update code it replaced.

## 8. Implementation variants

**Getter and setter pairs.** A lens can be stored as two functions, one from
whole to focus and one from focus plus whole to rebuilt whole. This is simple
and works in TypeScript, Python, Go, Java, Swift, and many other languages. The
tradeoff is that the representation does not scale to the full optic family
without adding more cases and more operation-specific APIs.

```typescript
type Lens<S, A> = {
  view: (source: S) => A;
  set: (value: A, source: S) => S;
};

const lens = <S, A>(
  view: (source: S) => A,
  set: (value: A, source: S) => S,
): Lens<S, A> => ({ view, set });

const compose = <S, A, B>(
  outer: Lens<S, A>,
  inner: Lens<A, B>,
): Lens<S, B> =>
  lens(
    source => inner.view(outer.view(source)),
    (value, source) => outer.set(inner.set(value, outer.view(source)), source),
  );

const over = <S, A>(
  optic: Lens<S, A>,
  change: (value: A) => A,
  source: S,
): S => optic.set(change(optic.view(source)), source);

type Address = { city: string; zip: string };
type Customer = { name: string; address: Address };
type Order = { id: string; customer: Customer; total: number };

const customer = lens<Order, Customer>(
  o => o.customer,
  (c, o) => ({ ...o, customer: c }),
);
const address = lens<Customer, Address>(
  c => c.address,
  (a, c) => ({ ...c, address: a }),
);
const city = lens<Address, string>(
  a => a.city,
  (value, a) => ({ ...a, city: value }),
);

const orderCity = compose(compose(customer, address), city);
const order: Order = {
  id: "A-1",
  customer: { name: "Nia", address: { city: "Paris", zip: "75001" } },
  total: 41,
};
const updated = over(orderCity, value => value.toUpperCase(), order);
console.log(order.customer.address.city);
console.log(updated.customer.address.city);
```

The TypeScript sample was compiled with `npx tsc --target ES2020 --module
commonjs --strict` and run with `node` on 2026-08-21.

```python
from dataclasses import dataclass, replace
from typing import Callable, Generic, TypeVar

S = TypeVar("S")
A = TypeVar("A")
B = TypeVar("B")

@dataclass(frozen=True)
class Lens(Generic[S, A]):
    view: Callable[[S], A]
    set: Callable[[A, S], S]

    def over(self, change: Callable[[A], A], source: S) -> S:
        return self.set(change(self.view(source)), source)

    def then(self, inner: "Lens[A, B]") -> "Lens[S, B]":
        return Lens(
            lambda source: inner.view(self.view(source)),
            lambda value, source: self.set(
                inner.set(value, self.view(source)), source
            ),
        )

@dataclass(frozen=True)
class Address:
    city: str
    zip_code: str

@dataclass(frozen=True)
class Customer:
    name: str
    address: Address

@dataclass(frozen=True)
class Order:
    id: str
    customer: Customer
    total: int

customer = Lens(lambda o: o.customer, lambda c, o: replace(o, customer=c))
address = Lens(lambda c: c.address, lambda a, c: replace(c, address=a))
city = Lens(lambda a: a.city, lambda value, a: replace(a, city=value))
order_city = customer.then(address).then(city)

order = Order("A-1", Customer("Nia", Address("Paris", "75001")), 41)
updated = order_city.over(str.upper, order)
print(order.customer.address.city)
print(updated.customer.address.city)
```

The Python sample was run with `python3` on 2026-08-21.

```go
package main

import (
	"fmt"
	"strings"
)

type Lens[S any, A any] struct {
	View func(S) A
	Set  func(A, S) S
}

func Compose[S any, A any, B any](outer Lens[S, A], inner Lens[A, B]) Lens[S, B] {
	return Lens[S, B]{
		View: func(source S) B { return inner.View(outer.View(source)) },
		Set: func(value B, source S) S {
			inside := inner.Set(value, outer.View(source))
			return outer.Set(inside, source)
		},
	}
}

func Over[S any, A any](optic Lens[S, A], change func(A) A, source S) S {
	return optic.Set(change(optic.View(source)), source)
}

type Address struct{ City, Zip string }
type Customer struct {
	Name    string
	Address Address
}
type Order struct {
	ID       string
	Customer Customer
	Total    int
}

func main() {
	customer := Lens[Order, Customer]{
		View: func(o Order) Customer { return o.Customer },
		Set: func(c Customer, o Order) Order { o.Customer = c; return o },
	}
	address := Lens[Customer, Address]{
		View: func(c Customer) Address { return c.Address },
		Set: func(a Address, c Customer) Customer { c.Address = a; return c },
	}
	city := Lens[Address, string]{
		View: func(a Address) string { return a.City },
		Set: func(value string, a Address) Address { a.City = value; return a },
	}
	orderCity := Compose(Compose(customer, address), city)
	order := Order{"A-1", Customer{"Nia", Address{"Paris", "75001"}}, 41}
	updated := Over(orderCity, strings.ToUpper, order)
	fmt.Println(order.Customer.Address.City)
	fmt.Println(updated.Customer.Address.City)
}
```

The Go sample was run with `go run` on 2026-08-21.

**Van Laarhoven encoding.** A Van Laarhoven lens represents access through a
function under a functor. Ramda documents this shape for JavaScript lenses
(https://ramdajs.com/docs/#lens, verified 2026-08-02). The tradeoff is high
compositional power with a type shape that many readers find less direct.

**Profunctor encoding.** Profunctor optics use abstractions such as
`Strong`, `Choice`, and related constraints to express the optic family in a
modular way. Pickering, Gibbons, and Wu present this as the paper's core model
(https://programming-journal.org/2017/1/7/, verified 2026-08-02). The tradeoff
is a stronger unifying theory at the price of more advanced type machinery.

**Generated optics.** Scala Monocle documents macro support for generating
optics from case class fields (https://www.optics.dev/Monocle/docs/focus,
verified 2026-08-02). Generated optics reduce hand-written boilerplate. Their
cost is build-tool dependence and public names that may follow data shape too
closely.

**Language-native key paths.** Swift has key path types such as `KeyPath` and
`WritableKeyPath` for property access paths, documented in the Swift standard
library reference (https://developer.apple.com/documentation/swift/keypath,
verified 2026-08-02). Key paths cover property-like access well. They do not,
by themselves, model prisms, traversals, or optic law tests.

**Dynamic path tools.** Python's glom documents declarative access and
assignment over nested data, including `Assign` and path-oriented operations
(https://glom.readthedocs.io/en/latest/, verified 2026-08-02). Such tools are
practical at dynamic data boundaries. The tradeoff is weaker static checking
than typed optics.

## 9. Known production uses

**Haskell `lens`.** The Haskell `lens` package is a named library that exposes a
large optics API across modules such as `Control.Lens.Type` and documents optic
types and operations on Hackage
(https://hackage.haskell.org/package/lens/docs, verified 2026-08-02). Treat
this as a production library use of the Optics pattern, not as evidence that
every Haskell codebase should use it.

**Monocle.** Monocle is a Scala optics library. Its site documents lenses,
prisms, optionals, traversals, isomorphisms, getters, setters, and folds under
the Monocle project (https://www.optics.dev/Monocle/, verified 2026-08-02).
It is a production library expression of typed optics in Scala.

**optics-ts.** optics-ts is a TypeScript optics library. Its reference
introduces optics, optic kinds, composition, and operations such as `get`,
`preview`, `set`, and `modify`
(https://akheron.github.io/optics-ts/reference-intro/, verified 2026-08-02).
It is a production library expression of the pattern for TypeScript programs.

**Partial Lenses.** Partial Lenses is a JavaScript library for composable
lenses and related optics over nested data
(https://calmm-js.github.io/partial.lenses/, verified 2026-08-02). It is a
production library use in a dynamic language ecosystem.

**Ramda lenses.** Ramda documents `lens`, `lensProp`, `lensPath`, `view`, `set`,
and `over` as part of its public API (https://ramdajs.com/docs/#lens, verified
2026-08-02). Ramda's API is lens-centered rather than a full statically typed
optic family, but it is a named library use of optic-style data access.

## 10. Consequences

Positive consequences.

- Repeated structural access gets a stable name.
- Read, update, preview, collect, and build operations can reuse the same focus.
- Nested immutable updates become less noisy at call sites.
- Missing focus and many-focus behavior can be reflected in the optic kind.
- Model owners can publish tested access paths instead of exposing all
  constructors.
- Composition lets small accessors scale to larger paths without copy-paste.
- Law tests catch accessors that read one location and write another.
- A composed optic can become a reusable domain term.

Negative consequences.

- Readers must learn a vocabulary that is larger than getter and setter.
- Error messages in strongly typed languages can become hard to parse.
- Deep composition can hide allocation and traversal cost.
- Public optics can freeze representation details.
- Dynamic optics over raw maps can fail at runtime in ways typed code would
  have caught.
- Debug logs can become vague if optics are anonymous.
- Law-breaking custom optics can be worse than manual code because they look
  reusable.
- A team may use optics for domain authority rather than structural access.

Engineering judgement. The main cost is not syntax. The main cost is that a
structural path becomes an API object. That is valuable only when the path has
enough reuse, stability, and conceptual weight.

## 11. Failure modes and misuse

This dimension is engineering judgement.

- **Symptom.** A `set` followed by `view` does not return the value that was
  set. **Cause.** The lens setter writes a different field than the getter
  reads, normalizes the value, or updates a sibling field. **Fix.** Add lens law
  tests. Split normalization into a domain function before or after the optic
  update.
- **Symptom.** Updating through a composed optic changes no data and does not
  report an error. **Cause.** A prism or optional segment did not match. The
  caller expected upsert behavior. **Fix.** Use an explicit upsert function, or
  have the operation return a count or option so the miss is observable.
- **Symptom.** A reducer is slow after replacing manual updates with optics.
  **Cause.** A traversal walks more nodes than the old code, or composition
  allocates many intermediate values. **Fix.** Measure path cardinality, name
  the hot optic, and replace the hot path with a hand-written update if needed.
- **Symptom.** A public field cannot be renamed without breaking downstream
  users. **Cause.** The team exported a generated optic for a field that was
  still internal. **Fix.** Export domain-level optics only. Keep generated
  optics private or behind a facade.
- **Symptom.** Logs say `modify` failed, but nobody can tell which path was
  modified. **Cause.** Anonymous composed optics are built inline. **Fix.** Name
  optics at module scope and add an operation label to logs or traces.
- **Symptom.** Runtime exceptions mention missing keys inside path code.
  **Cause.** A string path was treated as a typed optic over unvalidated JSON.
  **Fix.** Parse or validate the boundary data first, then use typed optics over
  the parsed structure. For ad hoc JSON selection, use a query tool with clear
  miss handling.
- **Symptom.** A security review finds sensitive fields copied into many logs.
  **Cause.** A convenient optic made access easy and no module boundary limited
  use. **Fix.** Keep sensitive optics in restricted modules. Add redaction
  operations that return safe views.
- **Symptom.** Developers avoid a module because type errors mention profunctor
  constraints nobody recognizes. **Cause.** The abstraction is more advanced
  than the team needs. **Fix.** Expose simpler named operations, or use lens
  pairs for common paths and reserve profunctor encodings for library internals.

## 12. Trade-off matrix

| Force | Optics | Manual copy and match | JSONPath or XPath | Visitor | Domain method |
|---|---|---|---|---|---|
| Coupling | Low when optics are stable | High to concrete shape | Low to typed model, high to path strings | Low for variant behavior | Low to structure |
| Consistency | High with law tests | Varies by call site | Query semantics, not optic laws | High for behavior dispatch | High for domain invariants |
| Latency | Medium overhead | Often lowest | Depends on query engine | Medium dispatch cost | Depends on method body |
| Allocation | Rebuilds immutable path | Rebuilds immutable path | Usually selection first | Depends on implementation | Depends on implementation |
| Absence handling | Encoded by optic kind | Ad hoc | Query result shape | Encoded by object hierarchy | Domain-specific |
| Operability | Good with named optics | Clear locally, noisy globally | Good if query strings are logged | Good by class or variant | Good by operation name |
| Team topology | Model team can publish focuses | Every caller knows shape | Query authors need path knowledge | Type owners own behavior | Domain team owns workflow |
| Cognitive load | High at first | Low locally | Medium query language cost | Medium pattern cost | Low if domain language is clear |
| Change cost | Low behind stable optics | High across callers | High if paths are public | Medium when variants change | Low for representation changes |
| Best fit | Reusable structural access | One local access | Ad hoc data selection | Variant behavior | Business transition |

Manual copy and match is the baseline for local code. JSONPath or XPath is the
named alternative for query-shaped selection over document data. Visitor is the
named alternative when behavior varies by variant. Domain Method is the named
alternative when the operation is a business rule rather than structural focus.

## 13. Related and incompatible patterns

**Lens** is the total, one-focus member of the family. It composes well with
other optics and is the right name when every whole has exactly one focus.

**Prism** targets one branch of a sum type. It composes with lenses when a
variant payload has fields. It replaces a lens when the focus may be absent
because the whole is in a different case.

**Traversal** targets zero or many focuses. It replaces a lens or prism when the
path can reach many children, such as all line items in an order.

**Optional** targets zero or one focus without the branch construction guarantee
of a prism. It fits nullable fields, missing map keys, or lookup-like paths.

**Iso** represents a reversible mapping. It composes with other optics when a
representation change is lossless in both directions.

**Functor** and **Applicative** often appear in implementations. Van Laarhoven
lenses rely on functorial structure, and traversals use applicative structure.
This is an implementation relationship, not a requirement for every client.

**Visitor** is related through variant handling. Visitor is better when each
variant owns a behavior. Prism is better when code needs reusable access to one
variant's payload.

**Repository** and **Query Object** are related at persistence boundaries.
Optics should not become database query planners. A query object can fetch
candidate data, then optics can focus inside the loaded values.

Incompatible patterns and practices.

- **Stringly typed paths** conflict with typed optics when they bypass the type
  checker and law tests.
- **Mutating accessors** conflict with optic expectations in value-oriented
  code unless the mutation is explicit in the type and API.
- **Effectful getters** conflict with optics because composition assumes access
  is structural, not a hidden operation with I/O.
- **Anemic domain models** can be made worse by optics if all business behavior
  moves into external field updates.

## 14. Refactoring path in and out

To introduce Optics.

1. Find two or more call sites that repeat the same nested structural path.
2. Classify the path. Always present means Lens. One branch means Prism. Zero or
   one without construction means Optional. Zero or many means Traversal. A
   reversible representation change means Iso.
3. Write the smallest optic for the innermost stable focus.
4. Add law tests for custom optics before broad use.
5. Replace one call site with `view`, `preview`, `over`, `set`, `collect`, or
   the library's equivalent operation.
6. Name composed optics only when the composition has domain meaning or appears
   more than once.
7. Keep generated or field-level optics private until the data owner is willing
   to support them as API.
8. Add observability labels for optics used in production workflows.

Named refactorings from the refactoring family help. **Extract Function**
turns repeated field access into one named operation before introducing an
optic. **Replace Temp with Query** can clarify a repeated read path. **Move
Method** may show that the operation belongs on the domain type rather than in
an optic. **Encapsulate Record** can be a precursor when raw data shape is
leaking across modules.

To remove Optics.

1. Find optics with one call site or no meaningful composition.
2. Inline the optic into the local read, match, or copy expression.
3. Replace domain updates with named domain methods if the optic was carrying
   business rules.
4. Remove public generated optics only through a deprecation period if
   downstream code may import them.
5. Keep tests that describe behavior, but delete law tests for removed custom
   optics.
6. Re-run performance checks if the removal touches hot reducer, parser, or
   serializer loops.

Engineering judgement. Refactor in through repetition. Refactor out through
ownership. If a structural path no longer has reuse or should no longer be
public, the optic has stopped paying rent.

## 15. Testing and verification

This dimension is engineering judgement, with named law claims cited where they
come from library docs.

Test optics at two levels. First, test custom optic laws. Monocle documents
laws for Lens and Prism, and monocle-ts documents laws for its Lens and Prism
interfaces (https://www.optics.dev/Monocle/docs/optics/lens, verified
2026-08-02; https://www.optics.dev/Monocle/docs/optics/prism, verified
2026-08-02; https://gcanti.github.io/monocle-ts/modules/Lens.ts.html, verified
2026-08-02; https://gcanti.github.io/monocle-ts/modules/Prism.ts.html,
verified 2026-08-02). For a lens, useful checks include get after set, set
after get, and last set wins. For a prism, useful checks include reviewing a
focus then previewing it, and preserving non-matching values under modify.

Second, test domain operations that use optics without testing the library
again. A reducer test should assert that the right state changed and the
unrelated state did not. A serializer test should assert output. A migration
test should assert before and after data. Do not mock the optic unless the code
explicitly accepts one as a dependency. The optic is a value, and testing with a
real one is usually cheap.

Property-based testing works well for law checks. Generate whole values and
focus values, then check the laws across many cases. Keep generators valid. If
the generator creates impossible domain states, a lawful optic may appear to
fail because the test data violates the model.

Golden tests can help for data-boundary optics over JSON-like structures. Store
sample input and expected output after `over` or `set`. Use them sparingly
because golden files can obscure the rule being tested. Pair a golden test with
one small example that names the behavior in code.

Performance verification matters for traversals. Count visited nodes or track
input size against runtime in a benchmark. A traversal that was fine for ten
items may be poor for one hundred thousand. For hot paths, compare the optic
implementation against a hand-written loop and make the tradeoff visible.

Compile or run examples. The samples in dimension 8 were executed on
2026-08-21 with `npx tsc` plus `node`, `python3`, and `go run`. If a future
entry adds Rust, Java, or Swift examples, the same rule applies: run the exact
sample or state that the tool was unavailable.

## 16. Observability signals

This dimension is engineering judgement.

Log optic use only at meaningful boundaries. Do not log every field read. Do
log a named update in a reducer, migration, batch repair, or API adapter when
the operation can change user-visible state. Use fields such as `optic_name`,
`optic_kind`, `operation`, `matched_count`, `changed_count`, `miss_count`, and
`duration_ms`.

A healthy dashboard for optics-heavy code shows stable match rates, low miss
rates for paths expected to exist, bounded traversal counts, and duration that
scales with input size in the expected way. A failing dashboard shows a sudden
rise in misses after a schema change, traversal counts far above input size,
or many updates that report zero changes while the caller expected a match.

Tracing helps when a composed optic crosses several concerns. A trace span can
record `operation=over`, `optic=editableShippingCities`, `kind=traversal`, and
`changed_count=12`. For privacy, avoid recording raw focus values by default.
Record types, counts, and redacted summaries.

Metrics for migrations and batch jobs should include source schema version,
optic name, match count, no-match count, invalid input count, and write count.
That makes it possible to see whether a migration skipped data because a prism
did not match or because the input was absent.

Static observability also matters. Public optics should be searchable by name.
Generated optics should be grouped or namespaced by model. A reviewer should be
able to answer "who can access this field" by searching imports of the optic,
not by scanning arbitrary string paths.

## 17. Security and privacy implications

This dimension is engineering judgement, except where standards or libraries
are cited.

Optics are access tools, so the primary security question is who receives the
accessor. A public optic to `user.passwordHash`, `accessToken`, `ssn`, or
`billingAddress` makes sensitive access easier to repeat. That does not make
the pattern unsafe by itself. It means sensitive optics need the same module
boundary and review discipline as sensitive fields.

Privacy risks increase when optics are composed with generic logging,
serialization, or audit helpers. A helper that can `view` any supplied optic may
copy private values into logs if callers pass sensitive focuses. Prefer
redacted optics or safe view types for logging paths. Do not log focus values
unless the data classification permits it.

Authorization should not be encoded as an optic. A prism that selects "admin
user" from a request is not a permission check unless the surrounding code
performs authentication, authorization, and audit. Keep authority in policy
objects or domain services, then use optics for structural access inside the
authorized operation.

Dynamic optics over JSON-like data can become injection surfaces when path
strings come from users. RFC 9535 specifies JSONPath syntax and semantics for
queries over JSON data (https://www.rfc-editor.org/rfc/rfc9535.html, verified
2026-08-02). If a service accepts user-supplied paths, treat them as queries
with their own validation, resource limits, and authorization model. Do not
confuse that with internal typed optics.

Side effects are another risk. An accessor that reads from a database or
rewrites a cache during `view` breaks the expectation that optics are structural
values. It also hides security-relevant work in code reviewers may skim past.
Keep I/O outside the optic and name it as an operation.

Optics can reduce risk when used well. A module can export a redacted view
optic, a public profile optic, or an audit-safe traversal while keeping raw
fields private. That gives callers a narrow access path and gives reviewers a
single import to inspect. The pattern is silent on encryption, storage policy,
and consent. Those concerns must be handled by the surrounding system.

## 18. References

- J. Nathan F., Michael B. Greenwald, Jonathan T. Moore, Benjamin C.
  Pierce, Alan Schmitt. "Combinators for Bidirectional Tree Transformations. A
  Linguistic Approach to the View-Update Problem." *ACM Transactions on
  Programming Languages and Systems*, volume 29, issue 3, article 17, 2007.
  https://dblp.org/rec/journals/toplas/FosterGMPS07, verified 2026-08-02.
  https://www.researchgate.net/publication/43921655_Combinators_for_bidirectional_tree_transformations_A_linguistic_approach_to_the_view-update_problem,
  verified 2026-08-02.
- Matthew Pickering, Jeremy Gibbons, Nicolas Wu. "Profunctor Optics. Modular
  Data Accessors." *The Art, Science, and Engineering of Programming*, volume
  1, issue 2, article 7, 2017. https://programming-journal.org/2017/1/7/,
  verified 2026-08-02.
- Monocle documentation. Project overview. https://www.optics.dev/Monocle/,
  verified 2026-08-02.
- Monocle documentation. Lens. https://www.optics.dev/Monocle/docs/optics/lens,
  verified 2026-08-02.
- Monocle documentation. Prism.
  https://www.optics.dev/Monocle/docs/optics/prism, verified 2026-08-02.
- Monocle documentation. Focus macro.
  https://www.optics.dev/Monocle/docs/focus, verified 2026-08-02.
- optics-ts documentation. Reference introduction.
  https://akheron.github.io/optics-ts/reference-intro/, verified 2026-08-02.
- Hackage. `lens-5.3.6` documentation directory.
  https://hackage.haskell.org/package/lens/docs, verified 2026-08-02.
- gcanti. monocle-ts Lens module.
  https://gcanti.github.io/monocle-ts/modules/Lens.ts.html, verified
  2026-08-02.
- gcanti. monocle-ts Prism module.
  https://gcanti.github.io/monocle-ts/modules/Prism.ts.html, verified
  2026-08-02.
- Partial Lenses documentation. https://calmm-js.github.io/partial.lenses/,
  verified 2026-08-02.
- Ramda documentation. `lens`, `view`, `set`, and `over`.
  https://ramdajs.com/docs/#lens, verified 2026-08-02.
- IETF RFC 9535. JSONPath. https://www.rfc-editor.org/rfc/rfc9535.html,
  verified 2026-08-02.
- Apple Developer Documentation. Swift `KeyPath`.
  https://developer.apple.com/documentation/swift/keypath, verified 2026-08-02.
- glom documentation. https://glom.readthedocs.io/en/latest/, verified
  2026-08-02.
