---
name: Algebraic Data Type
slug: algebraic-data-type
family: 16-functional
category: Functional
aliases: [ADT, Sum Type, Product Type, Tagged Union, Variant, Discriminated Union]
first_described: "standard ML and Haskell data declaration practice"
maturity: canonical
related: [pattern-matching, option-maybe, result-either, prism, immutability]
incompatible_with: [flag-argument, stringly-typed-state, nullable-field-bag]
verified: 2026-08-02
---

# Algebraic Data Type

## 1. Name, aliases, and lineage

The canonical name is Algebraic Data Type, commonly shortened to ADT. The name
comes from a simple idea. A type can be built from other types by using product
composition, sum choice, and recursion. Product composition means a value
contains several fields at once. Sum choice means a value is one of several
named alternatives. Recursion means a case can refer back to the type being
defined. The Haskell 2010 Report places algebraic datatypes under user-defined
datatypes and gives the form of a `data` declaration as a type constructor with
zero or more data constructors in section 4.2.1
(https://www.haskell.org/onlinereport/haskell2010/haskellch4.html#x10-620004.2.1,
verified 2026-08-02).

The aliases vary by language family. In ML and Haskell literature, the word
**datatype** or **algebraic datatype** is normal. In OCaml, the public docs call
the sum side **variants** and say variants are also called tagged unions
(https://ocaml.org/docs/basic-data-types, verified 2026-08-02). In F#, the
public term is **discriminated union**, with cases that may carry values
(https://learn.microsoft.com/en-us/dotnet/fsharp/language-reference/discriminated-unions,
verified 2026-08-02). Rust uses **enum**, and its standard documentation says
that Rust enums are commonly known as Algebraic Data Types in functional
programming contexts because variants can carry data
(https://dev-doc.rust-lang.org/std/keyword.enum.html, verified 2026-08-02).
Swift also uses **enumeration** for the sum side, and the Swift book documents
associated values on enumeration cases
(https://docs.swift.org/swift-book/documentation/the-swift-programming-language/enumerations/,
verified 2026-08-02). TypeScript uses structural unions, usually called
**discriminated unions** when every member has a common literal tag
(https://www.typescriptlang.org/docs/handbook/2/narrowing.html, verified
2026-08-02).

This catalog treats Algebraic Data Type as the umbrella pattern. `Option`,
`Result`, domain events, commands, syntax trees, protocol messages, workflow
states, and expression trees are all smaller applications of the same shape.
The pattern is not the presence of an `enum` keyword. The pattern is the act of
modeling a domain so every value is a member of a closed set of meaningful
cases, where each case carries exactly the fields it needs.

Engineering judgement. ADT is a language feature in Haskell, OCaml, F#, Rust,
and Swift. It becomes a software pattern when a team chooses to model domain
state with closed cases instead of nullable fields, flags, inheritance, or
string tags.

## 2. Problem and context

A domain value often has several legitimate shapes, but ordinary object or
record modeling makes those shapes look like one bag of optional fields. A
payment can be pending, authorized, captured, failed, or refunded. A command can
be create, update, delete, or archive. A search result can be loading, empty,
failed, or ready with rows. A parser node can be literal, unary expression,
binary expression, call expression, binding, or block. Each shape needs a
different set of fields.

Without ADTs, teams often encode that variety with weak conventions. One
record contains `status`, `error`, `rows`, `authorizedAt`, `capturedAt`,
`refundId`, and several nullable timestamps. Many combinations are nonsense,
but the type allows them. A failed payment can accidentally carry a capture ID.
A ready search result can lack rows. A caller must remember an informal rule:
when `status == "failed"`, inspect `error`; when `status == "ready"`, inspect
`rows`; when `status == "loading"`, read neither. The compiler cannot defend
that rule because the type does not say it.

The problem grows when the value crosses module boundaries. A producer may add
a new status string. A consumer may have a default branch that treats the new
state as an old state. A serializer may send a payload with both success and
failure fields. Tests may cover the happy path and miss impossible mixtures.
Runtime checks appear everywhere because every consumer must validate the same
shape again.

An ADT moves the rule into the type. The payment value is not one record with
all fields. It is one of five cases. The failed case carries a failure reason.
The captured case carries a capture ID and amount. The pending case carries no
capture data. Pattern matching or a tagged switch then forces the reader to
deal with the cases as cases. In languages with exhaustive matching, adding a
case creates compile errors at every match that must decide what the new case
means. In languages without exhaustive matching, the pattern still reduces
invalid states by concentrating construction behind case functions.

The context matters. ADTs are best when the case set is part of the domain
contract and changes deliberately. They are less useful when the case set is
open to plugins, remote configuration, or third-party subtype extension. A
closed business process, a public protocol schema, a compiler tree, or a
workflow state machine fits. An extension point where unknown callers must add
new behaviors may prefer objects, interfaces, or a registry.

The practical warning is that ADTs reward teams that name the domain before
they name the storage. A table may store one row per payment. A JSON response
may have one top-level object. A cache key may point at one blob. None of that
means the in-process model should be one flat product type. Storage shapes are
often optimized for indexing, migration, and compatibility. Domain shapes are
optimized for making illegal work hard to express. A careful boundary adapter
can keep both sides honest: decode or load the external shape, validate it,
construct one internal case, then let the rest of the program work with the
internal ADT.

## 3. Forces

Engineering judgement. This section weighs trade-offs from software design
practice. Language-specific facts are cited where a cited manual defines the
mechanism.

- **Consistency.** Favoured. Each case carries only the fields valid for that
  case, so impossible mixtures become hard or impossible to construct.
- **Coupling.** Mixed. Producers and consumers share a closed case vocabulary.
  That helps coordination inside a bounded context, but consumers are coupled
  to each case when they match exhaustively.
- **Latency.** Usually neutral. A native enum or union is a value-level control
  structure. Cost comes from allocation strategy and payload size, not from the
  concept. Rust documents enums as a type that can be one of several variants,
  with data attached to variants
  (https://dev-doc.rust-lang.org/std/keyword.enum.html, verified 2026-08-02).
- **Operability.** Favoured when the case tag is logged and counted. A dashboard
  can show how many requests are `ready`, `empty`, `failed`, or `timed_out`.
  Sacrificed when the value is serialized as an opaque object without a stable
  tag.
- **Cost of change.** Favoured when fields move between cases or invalid
  combinations are removed. Sacrificed when a public ADT gains a new case,
  because every exhaustive consumer may need an edit.
- **Team topology.** Favoured inside one owning team or a strongly versioned
  API. Sacrificed across a loose plugin boundary where independent teams must
  add cases without waiting for the owner.
- **Cognitive load.** Mixed. The type captures more truth, but readers must
  learn pattern matching, constructors, and total handling.
- **Serialization.** Mixed. JSON and protobuf can encode tagged alternatives,
  but the schema must name the tag and payload rules. A raw language enum rarely
  crosses the wire unchanged.
- **Extensibility.** Favours adding operations over adding cases. Once the
  cases exist, writing a new interpreter, renderer, validator, or mapper is
  direct. Adding a new case forces every such operation to decide what it does.
- **Reviewability.** Favoured when the case list is short and named in domain
  terms. A reviewer can see the whole state space in one definition. Sacrificed
  when the ADT becomes a dumping ground for unrelated variants.

An ADT favours correctness of state representation and local reasoning. It
sacrifices some openness and can create edit pressure when the domain case set
changes.

The most common force mistake is treating the edit pressure as a defect. When a
new case is a real domain event, the compile errors are information. They show
every place where the new event needs a business decision. The pressure becomes
harmful only when the ADT is owned at the wrong boundary. If a platform package
tries to close over every downstream product event, every product change turns
into a platform release. If a feature module closes over its own workflow
states, the same pressure keeps the feature honest.

## 4. Applicability and non-applicability

Reach for Algebraic Data Type when the following hold.

- A value is exactly one of several named states, commands, events, or node
  kinds.
- Each case has a different payload shape, and a shared optional-field record
  would permit nonsense combinations.
- The case set is closed enough that adding a case should be an explicit design
  event.
- Consumers need to branch by case and should be forced to handle all relevant
  cases.
- You are modeling a domain state machine, syntax tree, protocol message,
  typed error, parser result, command vocabulary, or UI request state.
- You need recursive data, such as an expression tree, menu tree, document
  outline, or workflow graph.
- You want constructors to act as the only path into the state space.

Do NOT reach for Algebraic Data Type in these cases.

- **The case set is owned by outside plugins.** A closed union makes every new
  plugin edit the central type. Prefer an interface, visitor with registration,
  command registry, or message bus.
- **The shape is a plain product.** A customer with `id`, `email`, and `plan`
  is a record, not a sum. Making every field a case hides ordinary data.
- **Only one field varies and no behavior branches on it.** Use a scalar enum,
  literal union, or validation rule. A full tagged payload creates ceremony.
- **The domain state is not settled.** During early discovery, an ADT may make
  the first guess feel more fixed than it is. A looser record can be cheaper
  until real cases emerge.
- **Consumers must tolerate unknown future cases.** Public APIs used by old
  clients need compatibility rules. A catch-all `unknown` case, versioned
  envelope, or object model may be safer than exhaustive matching.
- **The language cannot encode the invariant well.** A pair of nullable fields
  plus a string tag is not a strong ADT unless constructors prevent invalid
  combinations and tests defend decoding.
- **The main variation is behavior, not data.** When each alternative owns many
  methods and few callers inspect fields, polymorphism or Strategy may read
  better.
- **The data is tabular and queried by fields.** Analytics records often need
  optional columns and filters. Encoding every row shape as a case can harm
  storage, query planning, and reporting.
- **The wire format is already fixed by another system.** Map the external
  schema into an ADT at the boundary if useful, but do not pretend the remote
  system promised the same invariant.

Non-applicability summary. Avoid ADTs where the variants are open, unknown
future cases must pass through old clients, or the variation belongs in
behavior rather than data.

## 5. Structure

The participants are few, but the boundaries are strict.

- **Algebraic type.** The named type that defines the full value space. It can
  be a native `data`, `enum`, discriminated union, sealed hierarchy, or a
  disciplined union of records.
- **Product case.** A case that carries several fields at once. A captured
  payment might carry `captureId`, `amount`, and `capturedAt`. The fields form
  a product because the value contains all of them together.
- **Sum choice.** The closed set of cases. A value is one case at a time. The
  sum is the choice among alternatives.
- **Constructor.** The only supported way to create a case. In native ADT
  languages, case names are constructors. In TypeScript or Python, factory
  functions or dataclass constructors play the same role.
- **Discriminator.** The runtime tag used to tell cases apart. Some languages
  hide the tag inside the enum representation. Structural languages expose it
  as a field such as `kind`, `type`, or `state`.
- **Matcher.** A `case`, `match`, `switch`, visitor, fold, or handler table that
  consumes the ADT by case.
- **Exhaustiveness checker.** The compiler or test rule that rejects a consumer
  when a case is ignored. Swift documents that a switch over an enumeration
  must be exhaustive unless a default branch is supplied
  (https://docs.swift.org/swift-book/documentation/the-swift-programming-language/enumerations/,
  verified 2026-08-02).

Relationships. Producers call constructors. Consumers use matchers. The
algebraic type owns the list of cases. Each case owns its payload fields. The
discriminator connects runtime values to the static case names.

## 6. ASCII structure diagram

```text
                   Algebraic Type: Payment
                            |
        +-------------------+-------------------+
        |                   |                   |
        v                   v                   v
   Pending              Authorized           Failed
   product case         product case         product case
   -----------          -------------        ------------
   fields:              fields:              fields:
   requestedAt          authId               code
                        amount               message
                        authorizedAt

   sum choice:
   Payment = Pending | Authorized | Failed

   product payload:
   Authorized = authId * amount * authorizedAt

   constructors:
   pending(time)  authorized(authId, amount, time)  failed(code, msg)

   matcher:
   switch payment.case, match payment, or visit each named case
```

## 7. Dynamics

At runtime, an ADT value moves through the program as one case. A producer picks
the case, attaches only that case's payload, and returns the value through a
type that covers all cases. A consumer inspects the discriminator or pattern
matches on the case, then receives fields narrowed to that case.

```text
Producer              ADT value                  Consumer
   |                      |                          |
   | validate input       |                          |
   |--------------------->|                          |
   |                      |                          |
   | choose one case      |                          |
   | Pending/Auth/Failed  |                          |
   |--------------------->|                          |
   |                      |                          |
   | return Payment       |                          |
   |----------------------------------------------->|
   |                      |                          |
   |                      |      match by case       |
   |                      |<-------------------------|
   |                      |                          |
   |                      |   Authorized branch sees |
   |                      |   authId, amount, time   |
   |                      |------------------------->|
   |                      |                          |
   |                      |   Failed branch sees     |
   |                      |   code and message       |
   |                      |------------------------->|
```

The key dynamic property is narrowing. Before the match, the consumer has a
`Payment`. After the `Authorized` branch starts, the consumer has an
authorized payment payload. The failure fields do not exist in that branch. In
TypeScript, a common literal property lets the compiler narrow a union member
after checking that property
(https://www.typescriptlang.org/docs/handbook/2/narrowing.html, verified
2026-08-02). In Rust, pattern matching on enum variants exposes the payload of
the matched variant; the Rust book covers `match` control flow and enum
patterns in chapter 6 (https://doc.rust-lang.org/book/ch06-02-match.html,
verified 2026-08-02).

Recursive ADTs add one extra dynamic. A consumer usually calls itself on child
values. An expression evaluator matches a binary expression, evaluates the left
expression, evaluates the right expression, then combines the answers. That
recursive traversal is safe when every case is handled and recursive calls move
toward smaller child values.

## 8. Implementation variants

**Native closed sum type.** Haskell `data`, OCaml variants, F# discriminated
unions, Rust enums, and Swift enums are the cleanest form. The language owns
the discriminator and usually supports pattern matching. This variant gives the
strongest local invariant. It can become rigid for public libraries because new
cases break exhaustive consumers.

**Product-only ADT.** Records, structs, tuples, and dataclasses model the
product side. A product type is not a full sum, but ADT design uses product
types inside cases. Use this for ordinary objects with no alternatives.

**Discriminated object union.** TypeScript represents the pattern as a union of
object types with a common literal property. The TypeScript handbook names this
discriminated-union narrowing rule
(https://www.typescriptlang.org/docs/handbook/2/narrowing.html, verified
2026-08-02). This variant is ideal at JavaScript boundaries because the runtime
value is a normal object. The cost is discipline. A badly decoded object can
claim a tag without the matching payload unless validation is present.

**Sealed class hierarchy.** Java, Kotlin, Scala, and some Python code model
cases as subclasses of a sealed or closed base type. This is a good fit when
each case needs methods or when the language lacks native data-carrying enums.
It costs more files and more allocation in some runtimes.

**Visitor over cases.** A visitor turns matching into method dispatch. It can be
useful when the language lacks pattern matching or when adding operations must
be explicit. It makes adding a case expensive because every visitor interface
changes.

**Encoding with private constructors.** In Python or Go, a module can expose
constructors and a `match` or `switch` helper while hiding fields. This is a
pragmatic ADT. It will not be as strong as a native closed sum type, but it can
remove invalid nullable-field combinations.

**Open union with fallback.** Public protocols sometimes add an `Unknown`
case that preserves the raw payload. This weakens exhaustiveness but protects
old clients from crashing when a new server case appears. Use it at versioned
boundaries, then convert to a closed internal ADT when possible.

**Phantom or branded case fields.** Structural languages sometimes add a brand
field that exists only to separate cases at compile time. This is useful when
two cases carry the same runtime fields but have different meaning, such as
`DraftId` and `PublishedId`. It should not replace a real discriminator when
runtime decoding is involved, because the brand may vanish after compilation.

**Table-driven matcher.** A handler map keyed by case can replace a large
switch in TypeScript or Python. This works when each branch has the same input
and output contract. It becomes awkward when branches need different payload
types, because the type checker may lose the relationship between key and
payload. Use a table for simple command dispatch; use a match when payload
narrowing is the main value.

**Code-generated ADT.** Some teams generate unions from protocol schemas. This
is a good fit when server and client must share a case vocabulary. The risk is
that generated names mirror transport wording instead of domain wording. Keep
the generated type at the edge if it reads like wire format, then map into a
hand-authored domain ADT.

## 9. Known production uses

**Rust standard library, `Option` and `Result`.** Rust's `Option<T>` is an enum
with `None` and `Some(T)` variants
(https://doc.rust-lang.org/core/option/enum.Option.html, verified 2026-08-02).
Rust's `Result<T, E>` is an enum with `Ok(T)` and `Err(E)` variants
(https://doc.rust-lang.org/stable/std/result/enum.Result.html, verified
2026-08-02). These are production standard library types used across Rust APIs
for absence and fallible results.

**Swift standard library, `Optional` and `Result`.** Apple documents
`Optional<Wrapped>` as an enum with `none` and `some(Wrapped)` cases
(https://developer.apple.com/documentation/Swift/Optional, verified
2026-08-02). Apple documents `Result<Success, Failure>` as an enum with
`success(Success)` and `failure(Failure)` cases
(https://developer.apple.com/documentation/Swift/Result, verified 2026-08-02).
These standard library ADTs carry absence and asynchronous or stored failure
outcomes through production Swift code.

**TypeScript compiler API, syntax trees.** The TypeScript compiler source
defines `Node` with a readonly `kind: SyntaxKind` property, and many narrower
node interfaces refine that common discriminator
(https://github.com/microsoft/TypeScript/blob/v5.9.3/src/compiler/types.ts,
verified 2026-08-02). The TypeScript compiler API wiki shows traversal code
switching on `node.kind` and handling named `SyntaxKind` cases
(https://github.com/microsoft/TypeScript/wiki/Using-the-Compiler-API,
verified 2026-08-02). This is a production-scale discriminated union style for
abstract syntax tree nodes.

**FSharp.Core, `option`.** Microsoft documents the F# `option` type as a
discriminated union with `Some` and `None` cases
(https://learn.microsoft.com/en-us/dotnet/fsharp/language-reference/discriminated-unions,
verified 2026-08-02). The FSharp.Core option module documents operations over
that type (https://fsharp.github.io/fsharp-core-docs/reference/fsharp-core-optionmodule.html,
verified 2026-08-02). This is a named production library use of the same ADT
shape for absence.

## 10. Consequences

Engineering judgement. These consequences are design outcomes a team should
expect when the pattern is applied with discipline.

Positive consequences.

- Invalid state combinations move from runtime checks into construction rules.
- Case names become part of the domain language, so code reads closer to the
  business process or protocol.
- Exhaustive matching turns new cases into visible work instead of silent
  fallthrough.
- Tests become smaller because fixtures can build the exact case under test
  without filling unrelated nullable fields.
- Serialization rules can become clearer when the external envelope has one
  tag and one payload shape per tag.
- Recursive structures become direct. Trees and expression languages no longer
  need a base class plus casts for every node shape.
- Operations over the data can be ordinary functions, which helps keep domain
  state immutable.

Negative consequences.

- Adding a case can touch many files, especially in systems with many
  interpreters, renderers, or mappers.
- Public closed ADTs can be hard to evolve without versioning or an unknown
  fallback.
- Pattern matching can centralize behavior into large switches if the team does
  not split operations by responsibility.
- Structural encodings can give false confidence unless constructors and
  validators block invalid decoded objects.
- Error messages from exhaustive checking can overwhelm new contributors until
  the project has examples.
- Runtime observability can regress if the tag is not logged in the same way
  across cases.
- Some frameworks bind more easily to flat records than to tagged alternatives,
  so adapters may be needed at the boundary.

Neutral consequences that still need planning.

- Documentation must explain which cases are public contract and which are
  internal implementation detail.
- Linters and code review should discourage catch-all branches in internal
  matches, while still allowing compatibility fallbacks at external boundaries.
- Migration plans must account for stored values that were written before a new
  case existed.
- Shared libraries need release notes that call out new cases because consumers
  may see compile errors by design.

## 11. Failure modes and misuse

Engineering judgement. Each item names an observable symptom, a likely cause,
and a practical fix.

- **Symptom.** Logs show records with `state: "failed"` and a non-empty success
  payload. **Cause.** The team used a string tag and optional fields but did not
  restrict construction. **Fix.** Replace the field bag with case constructors
  or a native ADT, then move decoding through a validator.
- **Symptom.** A new domain case ships and one UI screen renders a blank panel.
  **Cause.** A default branch swallowed the new case. **Fix.** Remove broad
  defaults inside internal matches and use an exhaustiveness helper or compiler
  setting.
- **Symptom.** Every operation has a 200-line switch over the same ADT. **Cause.**
  The type grew into a grab bag that spans several bounded contexts. **Fix.**
  Split the ADT by workflow or module, then move shared operations behind small
  functions.
- **Symptom.** A public client fails to parse server responses after a release.
  **Cause.** The server added a closed case without a wire-compatibility plan.
  **Fix.** Version the schema, add an `unknown` envelope for old clients, or
  negotiate capabilities before sending new cases.
- **Symptom.** Tests require large fixtures with unrelated fields set to dummy
  values. **Cause.** The model is still a product record pretending to be a sum.
  **Fix.** Extract real cases so each fixture carries only the fields its state
  needs.
- **Symptom.** Teams avoid the ADT and pass raw strings through side channels.
  **Cause.** Constructors are hard to import, names are unclear, or the case set
  is too coarse. **Fix.** Rename cases in domain terms, expose simple builders,
  and add boundary adapters.
- **Symptom.** Pattern matches panic on recursive input or overflow the stack.
  **Cause.** Recursive cases are traversed without a depth limit or iterative
  strategy. **Fix.** Add depth budgets for untrusted input, or evaluate with an
  explicit stack.
- **Symptom.** Metrics cannot distinguish business failures from technical
  failures. **Cause.** Both were modeled as one `Error(String)` case. **Fix.**
  Split expected domain cases from infrastructure failure, and map the latter
  to a separate error channel.

## 12. Trade-off matrix

| Force | Algebraic Data Type | Polymorphic Class Hierarchy | Flag Argument | Dynamic Map |
|---|---|---|---|---|
| Consistency | Strong. Cases own fields. | Medium. Constructors can defend invariants. | Weak. Flags combine badly. | Weak unless validated. |
| Adding a case | Expensive when matches are many. | Cheap if callers use virtual methods. | Cheap at first, costly later. | Cheap but unsafe. |
| Adding an operation | Cheap. Write another match. | Expensive. Add method to each class. | Medium. Add another branch. | Medium. Add runtime checks. |
| Coupling | Couples consumers to closed cases. | Couples clients to base behavior. | Couples callers to flag meaning. | Couples consumers to strings. |
| Operability | Good when tags are logged. | Good when class names are logged. | Poor when flags lack payload context. | Poor when keys drift. |
| Cognitive load | Medium. Requires match discipline. | Medium. Requires dispatch tracing. | Low initially, high with growth. | Low initially, high in failure. |
| Serialization | Good with a tagged envelope. | Needs type metadata or mapper. | Easy but ambiguous. | Easy but under-specified. |
| Public API evolution | Needs versioning or fallback. | Allows subtype extension if open. | Adds flags until unclear. | Allows unknown keys, weak contract. |
| Testing | Precise fixtures per case. | Needs subclass fixtures. | Needs combination tests. | Needs decoder and key tests. |

## 13. Related and incompatible patterns

**Pattern Matching** is the natural consumer side of ADTs. The ADT defines the
closed case set. Pattern matching turns that set into behavior while binding the
payload for each case.

**Option Maybe** is a two-case ADT for presence and absence. Use it when the
only question is whether a value exists. Rust `Option<T>` and Swift
`Optional<Wrapped>` are named standard library examples, cited in dimension 9.

**Result Either** is a two-case ADT for success and expected failure. It adds an
error payload and usually carries combinators such as map and bind.

**Prism** is an optic for focusing on one case of a sum. It composes with ADTs
when a caller wants to inspect or update one alternative without writing a full
match at every access point.

**Immutability** pairs well with ADTs because case construction creates a new
value instead of mutating fields across states.

**Visitor** can replace pattern matching in object-oriented languages. It is
useful when the case set is stable and operations are grouped as visitors. It
is painful when new cases are frequent.

**Strategy** and **State** conflict when the variation is mainly behavior. If
each alternative owns its own algorithm and little data is inspected by callers,
an ADT may turn polymorphic behavior into procedural switches.

**Flag Argument** conflicts with ADT modeling. A flag tells one function to
pretend it has several modes. An ADT gives each mode its own value shape and
lets many functions handle it.

**Stringly Typed State** conflicts for the same reason. A string tag without a
closed type, constructor, and payload rule is an honor-system ADT.

## 14. Refactoring path in and out

To introduce an ADT into an existing nullable-field model, start at the
constructors. List every legal state and write down which fields are valid in
that state. Then create one case per legal state. Move fields from the shared
record into the case that owns them. Replace direct record construction with
named constructors. At first, the constructors may still return the old record,
but they should reject invalid combinations.

The safest first refactoring is often parallel modeling. Keep the old record at
the boundary, create the new ADT beside it, and write one conversion function
from old to new. Point one consumer at the ADT. When that consumer becomes
clearer, move the next one. This avoids a wide edit where every caller must
learn the new type at the same time. It also gives the team a single place to
find data quality problems in old records.

Next, move consumers one at a time. Pick one branch-heavy function and replace
conditionals over `status` plus null checks with a match over cases. In
TypeScript, use a literal discriminant and an `assertNever` helper. In Rust or
Swift, let the compiler report missing cases. In Python, centralize `match`
handling and use dataclasses for payloads. Keep a boundary adapter that maps the
old wire shape into the new internal ADT.

After consumers move, delete the old nullable fields or make them private. Add
tests that decoding rejects impossible mixtures. Add one round-trip test for
the public schema if the ADT crosses a wire boundary. Then log the case tag
through the main workflow so operators can see the new model.

When the source model is a type-code switch, use a narrower route. Create a
case for each current type code. Move the payload fields used by that branch
into the case. Replace each switch branch with a pattern match branch that
receives already-narrowed fields. Then remove branch-local null checks that can
no longer fail. The cleanup matters because leaving the checks in place tells
future readers that the invariant is still uncertain.

To remove an ADT, first ask why it no longer earns its place. If every case now
has the same fields and the same behavior, collapse the sum into a product
record. If unknown cases must be accepted, replace the closed union with a
registry or open interface. If switches have grown around behavior, move
behavior into polymorphic types or Strategy objects. Keep the old constructors
as compatibility functions for one release, then remove them after call sites
use the new shape.

Named refactorings that apply include Replace Type Code with Subclasses when
the target language favours classes, Replace Conditional with Polymorphism when
behavior dominates, and Introduce Parameter Object when several case fields
move together into a named payload. Martin Fowler documents these refactorings
in *Refactoring*, second edition, chapters 12 and 11.

## 15. Testing and verification

Engineering judgement. ADTs make invalid-state tests more valuable than broad
fixture tests.

Start with constructor tests. Each constructor should build a valid case with
the expected tag and payload. If construction validates business rules, test the
rejection path there rather than in every consumer. For structural encodings,
add decoder tests for malformed external data: missing tag, unknown tag, tag
with wrong payload, and payload fields from another case.

Then test each consumer with one fixture per case. A renderer should have a
pending fixture, a failed fixture, and a ready fixture. A command handler should
have one command of each kind. A parser should have one syntax node for each
branch it claims to handle. The payoff is small fixtures. A failed result test
does not need dummy success fields.

Use exhaustiveness checks where the language permits them. In TypeScript, a
helper that accepts `never` catches missed union members when `strict` checking
is enabled. In Swift and Rust, prefer explicit cases over broad defaults in
internal code so the compiler can report new cases. In Python, `match` is not a
full static exhaustiveness checker, so pair it with a test that enumerates the
known subclasses or case tags.

Property tests fit recursive ADTs. Generate small trees, evaluate them, pretty
print them, parse them again, and compare the result. Also test depth limits for
untrusted recursive input. Snapshot tests can help for renderers, but they
should not replace case-by-case assertions because snapshots can hide missing
branches behind large diffs.

Test doubles should be values, not mocks, when possible. Instead of mocking a
payment gateway response object with nullable fields, build
`Payment.authorized(...)` or `Payment.failed(...)`. That keeps tests tied to
the same legal state space as production code.

## 16. Observability signals

Engineering judgement. The pattern is visible in production only when the case
tag is exposed as a stable signal.

Log the ADT name and case at decision boundaries. For a payment ADT, log
`payment.case=authorized` or `payment.case=failed`, not the whole value. For
failure cases, log stable reason codes and safe metadata. Avoid dumping payloads
that may contain personal data. For recursive ADTs such as syntax trees, log
node counts, maximum depth, parse error case, and input size rather than full
trees.

Metrics should count cases. A healthy search UI might show request states
distributed across `loading`, `ready`, `empty`, and expected failure cases. A
healthy parser might show a stable ratio of literal, call, binding, and block
nodes for a known workload. A failing instance may show a sudden spike in
`unknown`, `decode_failed`, `timeout`, or `default_branch_used`.

Tracing should attach case names to spans where a case drives different work.
For a command ADT, tag the handler span with `command.kind`. For a workflow ADT,
tag transitions from one case to the next. If an internal match has a defensive
default branch, count it as an alerting event. That branch means the runtime saw
a value outside the consumer's expected model.

Dashboards should separate domain cases from infrastructure failures. A
`Payment.failed(card_declined)` case is business data. A database timeout while
loading the payment is an operational failure. Mixing them under one metric
turns both graphs into noise.

## 17. Security and privacy implications

Engineering judgement. ADTs are not a security control by themselves, but they
can reduce classes of state-confusion bugs.

The main security benefit is making illegal combinations harder to represent.
An authorization token value can be `anonymous`, `authenticated(userId,
scopes)`, or `serviceAccount(serviceId, scopes)`. That shape is safer than a
single record where `userId`, `serviceId`, and `scopes` are all optional and
callers infer meaning from whichever fields happen to be present. The ADT does
not prove the scopes are correct, but it removes ambiguity about which identity
kind is being handled.

The main risk is unsafe decoding. External JSON can claim any tag. A structural
ADT must validate that the tag is known and that the payload belongs to that
tag. Unknown tags should be rejected or preserved in an explicit `unknown` case
according to the API compatibility plan. Do not let a default branch silently
grant access, select a privileged case, or continue with empty permissions.

Privacy depends on payload design. Case tags are usually safe to log when they
are coarse, but payloads may contain personal data, secrets, account IDs, or
free-form user text. Logging an entire failed login ADT can leak the submitted
email or provider token. Log the case and a stable reason code; redact or hash
payload fields according to the data policy.

Recursive ADTs need resource limits when they come from untrusted input. A
deeply nested expression, document tree, or message envelope can cause stack
overflow, high allocation, or slow traversal. Validate maximum depth, maximum
node count, and maximum serialized size before evaluating or rendering.

ADTs are silent on authentication, authorization, encryption, and transport
security. They can model security decisions and make cases explicit, but the
checks themselves still belong in policy code and boundary validation.

Threat modeling should include case confusion. Ask what happens if an attacker
can send a tag from one case with the payload of another case. Ask whether the
decoder rejects duplicate tags, unknown tags, and extra fields that might be
interpreted differently by another service. Ask whether a future case can be
treated as a permissive default by an old client. These are protocol questions,
not type-theory questions, but ADT design makes them visible early.

For privacy reviews, classify each payload by the most sensitive field in that
case. A `failed` case may contain an external reason code, while a
`requires_review` case may contain evidence, account history, or user text. The
tag alone may be low risk, but the payload may be high risk. Logging, tracing,
retention, and analytics should follow the payload classification rather than
the type name.

## Code examples

The samples use four languages where the pattern has different shapes: Rust and
Swift have native data-carrying enums, TypeScript has structural discriminated
unions, and Python can model a closed set with dataclasses plus pattern
matching.

### TypeScript

```typescript
type Payment =
  | { kind: "pending"; requestedAt: string }
  | { kind: "authorized"; authId: string; amountCents: number }
  | { kind: "failed"; code: "declined" | "expired"; message: string };

function assertNever(value: never): never {
  throw new Error(`unhandled case ${JSON.stringify(value)}`);
}

function receiptLine(payment: Payment): string {
  switch (payment.kind) {
    case "pending":
      return `pending since ${payment.requestedAt}`;
    case "authorized":
      return `authorized ${payment.authId} for ${payment.amountCents}`;
    case "failed":
      return `failed ${payment.code}: ${payment.message}`;
    default:
      return assertNever(payment);
  }
}

const sample: Payment = {
  kind: "authorized",
  authId: "auth_123",
  amountCents: 4200,
};

console.log(receiptLine(sample));
```

### Python

```python
from dataclasses import dataclass
from typing import Union


@dataclass(frozen=True)
class Pending:
    requested_at: str


@dataclass(frozen=True)
class Authorized:
    auth_id: str
    amount_cents: int


@dataclass(frozen=True)
class Failed:
    code: str
    message: str


Payment = Union[Pending, Authorized, Failed]


def receipt_line(payment: Payment) -> str:
    match payment:
        case Pending(requested_at=ts):
            return f"pending since {ts}"
        case Authorized(auth_id=auth_id, amount_cents=amount):
            return f"authorized {auth_id} for {amount}"
        case Failed(code=code, message=message):
            return f"failed {code}: {message}"


print(receipt_line(Authorized("auth_123", 4200)))
```

### Rust

```rust
enum Payment {
    Pending { requested_at: &'static str },
    Authorized { auth_id: &'static str, amount_cents: u32 },
    Failed { code: &'static str, message: &'static str },
}

fn receipt_line(payment: Payment) -> String {
    match payment {
        Payment::Pending { requested_at } => {
            format!("pending since {requested_at}")
        }
        Payment::Authorized { auth_id, amount_cents } => {
            format!("authorized {auth_id} for {amount_cents}")
        }
        Payment::Failed { code, message } => {
            format!("failed {code}: {message}")
        }
    }
}

fn main() {
    let payment = Payment::Authorized {
        auth_id: "auth_123",
        amount_cents: 4200,
    };
    println!("{}", receipt_line(payment));
}
```

### Swift

```swift
enum Payment {
    case pending(requestedAt: String)
    case authorized(authId: String, amountCents: Int)
    case failed(code: String, message: String)
}

func receiptLine(_ payment: Payment) -> String {
    switch payment {
    case .pending(let requestedAt):
        return "pending since \(requestedAt)"
    case .authorized(let authId, let amountCents):
        return "authorized \(authId) for \(amountCents)"
    case .failed(let code, let message):
        return "failed \(code): \(message)"
    }
}

let payment = Payment.authorized(authId: "auth_123", amountCents: 4200)
print(receiptLine(payment))
```

Verification performed on 2026-08-21 with `npx tsc`, `node`, `python3`,
`rustc`, and `swiftc`.

## 18. References

- Simon Marlow, editor, *Haskell 2010 Language Report*, section 4.2.1,
  Algebraic Datatype Declarations,
  https://www.haskell.org/onlinereport/haskell2010/haskellch4.html#x10-620004.2.1,
  verified 2026-08-02.
- OCaml documentation, *Basic Data Types and Pattern Matching*, user-defined
  types and variants, https://ocaml.org/docs/basic-data-types, verified
  2026-08-02.
- Microsoft Learn, *Discriminated Unions*, F# language reference,
  https://learn.microsoft.com/en-us/dotnet/fsharp/language-reference/discriminated-unions,
  verified 2026-08-02.
- Rust standard documentation, *Keyword enum*,
  https://dev-doc.rust-lang.org/std/keyword.enum.html, verified 2026-08-02.
- Rust standard documentation, *core::option::Option*,
  https://doc.rust-lang.org/core/option/enum.Option.html, verified
  2026-08-02.
- Rust standard documentation, *std::result::Result*,
  https://doc.rust-lang.org/stable/std/result/enum.Result.html, verified
  2026-08-02.
- Steve Klabnik and Carol Nichols, *The Rust Programming Language*, chapter 6,
  Enums and Pattern Matching, https://doc.rust-lang.org/book/ch06-00-enums.html,
  verified 2026-08-02.
- Apple Developer Documentation, *Optional*,
  https://developer.apple.com/documentation/Swift/Optional, verified
  2026-08-02.
- Apple Developer Documentation, *Result*,
  https://developer.apple.com/documentation/Swift/Result, verified 2026-08-02.
- Swift.org, *The Swift Programming Language*, Enumerations,
  https://docs.swift.org/swift-book/documentation/the-swift-programming-language/enumerations/,
  verified 2026-08-02.
- TypeScript Handbook, *Narrowing*, discriminated unions,
  https://www.typescriptlang.org/docs/handbook/2/narrowing.html, verified
  2026-08-02.
- TypeScript Handbook, *TypeScript for Functional Programmers*, discriminated
  unions, https://www.typescriptlang.org/docs/handbook/typescript-in-5-minutes-func.html,
  verified 2026-08-02.
- Microsoft TypeScript repository, `src/compiler/types.ts`,
  https://github.com/microsoft/TypeScript/blob/v5.9.3/src/compiler/types.ts,
  verified 2026-08-02.
- Microsoft TypeScript wiki, *Using the Compiler API*,
  https://github.com/microsoft/TypeScript/wiki/Using-the-Compiler-API,
  verified 2026-08-02.
- Benjamin C. Pierce, *Types and Programming Languages*, MIT Press, 2002,
  chapter 11, Simple Extensions.
- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, second
  edition, Addison-Wesley, 2018, chapters 11 and 12.
