---
name: Replace Primitive with Object
slug: replace-primitive-with-object
family: 03-refactoring
category: Data Organization
aliases: [Replace Data Value with Object, Replace Type Code with Class, Introduce Value Object]
first_described: "Fowler 1999"
maturity: canonical
related: [primitive-obsession, value-object, domain-primitive, introduce-parameter-object, change-reference-to-value]
incompatible_with: [inline-class]
verified: 2026-08-02
---

# Replace Primitive with Object

## 1. Name, aliases, and lineage

The canonical name is Replace Primitive with Object. Martin Fowler's online
catalog lists the refactoring under that name and records the aliases Replace
Data Value with Object and Replace Type Code with Class
(https://refactoring.com/catalog/replacePrimitiveWithObject.html, verified
2026-08-02). The refactoring belongs to the data organization part of Fowler's
catalog, and it is the direct treatment for the Primitive Obsession smell named
in Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
edition, Addison-Wesley, 2018, chapter 3, "Bad Smells in Code," and chapter
7, "Encapsulation."

The older alias matters because many teams still say "replace data value with
object" when they mean the single-value form, for example changing a customer
rating string into a `Rating` class. The type-code alias matters because an
integer or string category can first become a small object before the design
moves further toward an enum, State, Strategy, or polymorphic hierarchy.

This refactoring is not the same thing as the Value Object pattern, although it
often creates one. Fowler describes value objects as objects whose equality is
based on their stored values rather than on object identity, and says common
primitives such as strings are often better represented as suitable value
objects (https://martinfowler.com/bliki/ValueObject.html, verified
2026-08-02). Replace Primitive with Object is the change operation. Value
Object is one common destination shape. A replacement object may later gain
identity, persistence, or lifecycle concerns, but that is a later modeling
choice, not part of the refactoring itself.

Judgement. The most useful name in code review is often the concrete domain
name, not the catalog name. Say "replace `string` with `EmailAddress`" or
"replace `int` with `Quantity`" when directing the work. Use the catalog name
when linking the change to a known refactoring path.

## 2. Problem and context

A primitive has started to carry a domain concept that the language type cannot
express. A `string` is not an email address. An `int` is not a quantity. A
`float` is not a percentage. A bare `long` epoch day is not a local calendar
date. The primitive stores the bits, but the meaning lives in parameter names,
comments, repeated validation checks, and the memory of developers who have
worked in the code long enough to know which strings are safe and which are
raw input.

The problem becomes visible when the same primitive appears in more than one
place with the same hidden rule. A controller rejects an invalid email address.
A batch import forgets to do the same. A repository receives the string and
stores it. A notification service lower in the call graph assumes any string
named `email` was already checked. The rule exists, but no type records that
the rule has been applied.

Another common shape is same-type confusion. `createSession(userId, tenantId)`
looks readable until both parameters are strings and a call site passes them in
the opposite order. The compiler accepts the call because it sees two strings.
The bug is a modeling failure that no unit test can cover in full, because
every future call site can repeat the swap.

A third shape is behavior drift. Formatting a phone number, comparing a
priority, rounding a money amount, checking a percentage range, or deciding
whether two date ranges overlap is written as helper functions around a
primitive. The helpers multiply. One accepts blank input, another trims it,
another lowercases it, another treats `HIGH` and `high` differently. The
domain rule has no owner.

The context that calls for this refactoring is a codebase that already has a
named concept, a repeated primitive representation, and a rule or behavior that
belongs to the concept rather than to any one caller. If the primitive is still
local, technical, and rule-free, the refactoring adds weight without buying
safety.

## 3. Forces

Judgement. These forces are engineering trade-offs. They are not universal
facts about every language or runtime.

- **Type safety.** The refactoring favours type safety. Once a function accepts
  `EmailAddress`, a caller cannot pass a `DisplayName` by accident in a
  nominally typed language. In a structural language, branded or opaque forms
  can recover part of the same protection.
- **Coupling.** The refactoring reduces coupling to primitive representation.
  Code outside the object stops knowing whether the value is stored as a
  string, an integer, a decimal, or a parsed structure. It increases coupling
  to the new type's public contract.
- **Consistency.** It favours consistency by moving parsing, validation,
  formatting, comparison, and normalization to one named place. It sacrifices
  the freedom of each caller to make its own local interpretation.
- **Latency and allocation cost.** It may sacrifice raw speed. In runtimes
  where small objects allocate on the heap, every wrapper instance has a cost.
  In Rust newtypes, Java records after escape analysis, Swift structs, and
  similar value forms, that cost can be small or optimized away, but it should
  be measured before applying the refactoring inside hot loops.
- **Serialization simplicity.** It sacrifices some boundary simplicity. JSON,
  SQL drivers, and message formats usually speak primitives. A value object
  needs explicit conversion at the edge.
- **Operability.** It favours operability when invalid input is rejected at
  construction and counted in one place. It can hurt operability if errors
  lose the raw value, the failed rule, or the source system that supplied it.
- **Team topology.** It favours larger and rotating teams. The new type makes
  the domain concept discoverable in search, ownership, tests, and review. It
  may slow a small team writing short-lived glue code.
- **Cognitive load.** It shifts cognitive load from call sites to the type
  definition. A reader pays one visit to `EmailAddress` and then trusts the
  name at call sites. This is a net gain only when the type has real rules.

The pattern gives up primitive convenience in order to make meaning explicit.
When there is no meaning beyond storage, the exchange is poor.

## 4. Applicability and non-applicability

Reach for Replace Primitive with Object when these conditions hold.

- A primitive parameter, field, or return value represents a named domain
  concept, not a technical scratch value.
- The concept has an invariant the primitive cannot state, such as non-empty,
  non-zero, positive, bounded, normalized, well-formed, or one member of a
  closed set.
- The same validation, parsing, formatting, unit conversion, or comparison rule
  appears in more than one caller.
- Two values with the same primitive type are easy to swap, for example
  `accountId` and `customerId`, `width` and `height`, or `amount` and
  `discount`.
- A primitive enters from an untrusted boundary and downstream code treats it
  as if it had already been checked.
- A primitive type blocks a later refactoring because behavior has no natural
  home. Examples include moving comparison logic onto `Priority`, arithmetic
  onto `Money`, or overlap checks onto `DateRange`.
- A group of tests repeats the same setup and assertion around a primitive's
  validity, which is evidence that the validity rule needs a single owner.

Non-applicability. Do not apply the refactoring in these cases.

- **Loop counters, indexes, and local accumulators.** The value is technical
  and local. A wrapper gives no extra domain protection and can obscure simple
  control flow.
- **A value with no invariant and no behavior.** A single `string` description
  passed through one layer and never confused with another string does not
  need a type of its own.
- **One-off migration or throwaway script.** The object will not live long
  enough to repay its construction, tests, and mapping code.
- **Measured hot path in a runtime with expensive allocation.** If a primitive
  is processed millions of times per request and profiling shows allocation
  pressure from wrappers, keep the primitive in the inner loop and convert at
  the boundary around the loop.
- **Wire format or database schema surface.** External contracts often need
  strings and numbers for compatibility. Keep the object inside the domain
  layer and unwrap only at the boundary.
- **The concept needs identity, not value semantics.** A `Customer` represented
  by a database identity should become an Entity or reference object, not a
  small value wrapper.
- **The concept is a group of fields rather than one primitive.** Use Introduce
  Parameter Object, Extract Class, or Value Object first when the real concept
  is a date range, address, geographic point, or money amount with currency.
- **A language-native enum already states the whole rule.** If the primitive is
  a small closed set and no extra behavior or parsing is needed, an enum can be
  enough.
- **The wrapper would expose the primitive to every caller again.** A class
  whose only public use is `.value` at every call site has moved ceremony into
  the design without moving behavior.
- **The name is weaker than the primitive.** `StringValue`, `NumberWrapper`,
  and `DataValue` do not name domain concepts. They are code smell cover.

## 5. Structure

The structure is deliberately small.

- **Primitive value.** The existing storage type. It may be a scalar such as
  `string`, `int`, `float`, or `boolean`, or a language library primitive such
  as `Date` where the problem is still that the type says too little.
- **Domain object.** The new type. It owns the primitive value, prevents direct
  mutation, validates construction, and exposes behavior using domain
  language. Most replacements should be immutable.
- **Construction gate.** A constructor, factory function, parser, or smart
  constructor that turns raw input into the domain object. It is the only place
  raw invalid input is allowed to become a candidate value.
- **Domain operations.** Methods or functions that belong to the concept,
  moved from scattered helpers onto or near the object.
- **Unwrap boundary.** The narrow set of places where the primitive is still
  required, such as database writes, JSON serialization, log redaction, or calls
  into libraries that cannot accept the object.
- **Consumers.** Existing functions, methods, and objects that used to accept
  the primitive and now accept the domain object.

The important relationship is direction. Raw input flows inward through the
construction gate. Domain code sees the object. Primitive unwrapping flows
outward only at system edges. When raw primitives leak deep into the model, the
refactoring is unfinished.

## 6. ASCII structure diagram

```text
Before

  +------------------+        string/int/etc.        +------------------+
  | Boundary input   | ----------------------------> | Domain consumer  |
  +------------------+                               +------------------+
          |                                                   |
          | validate?                                         | validate?
          v                                                   v
  +------------------+                               +------------------+
  | helper function  |                               | helper function  |
  +------------------+                               +------------------+

After

  +------------------+        raw primitive          +------------------+
  | Boundary input   | ----------------------------> | Construction gate|
  +------------------+                               +------------------+
                                                            |
                                                            | valid object
                                                            v
                                                     +------------------+
                                                     | Domain object    |
                                                     | value + rules    |
                                                     +------------------+
                                                            |
                                                            | typed value
                                                            v
                                                     +------------------+
                                                     | Domain consumer  |
                                                     +------------------+
                                                            |
                                                            | unwrap only
                                                            v
                                                     +------------------+
                                                     | Wire/db/library  |
                                                     +------------------+
```

## 7. Dynamics

At runtime the refactoring changes where invalid data can travel. Before the
change, raw data can pass through several layers and fail late. After the
change, construction succeeds once or fails early, and downstream code treats
the object as a proof that the invariant already holds.

```text
Boundary      Parser/Gate        Domain Object       Service       Storage
   |              |                    |                |             |
   | raw value    |                    |                |             |
   |------------->|                    |                |             |
   |              | validate, normalize|                |             |
   |              |------------------->|                |             |
   |              |       ok           |                |             |
   |              |<-------------------|                |             |
   | typed value  |                    |                |             |
   |<-------------|                    |                |             |
   |              | typed value        |                |             |
   |---------------------------------->|                |             |
   |              |                    | domain action  |             |
   |              |                    |--------------->|             |
   |              |                    |                | primitive   |
   |              |                    |                | unwrap      |
   |              |                    |                |------------>|

Failure path

Boundary      Parser/Gate        Metrics/Logs
   |              |                    |
   | raw value    |                    |
   |------------->|                    |
   |              | reject             |
   |              |------------------->| count by rule and source
   | error        |                    |
   |<-------------|                    |
```

The dynamics are safest when construction happens close to the first trust
boundary. If a raw primitive is accepted by a service method and then wrapped
three calls later, all code before the wrapping point still carries the old
risk. The change is complete only when a raw value has a short, visible path
from input to construction.

## 8. Implementation variants

**Class-based value object.** A class owns a private primitive field and exposes
methods. This is common in Java, TypeScript, Python, and older object-oriented
codebases. The gain is a clear place for invariants and behavior. The cost is
more code, and sometimes allocation.

**Record or data-class value object.** Java records, Python frozen dataclasses,
Swift structs, and similar constructs reduce boilerplate for immutable data.
They are a good fit when the object mostly needs validation, equality, and a
small number of pure operations. Guard against generated constructors that
accept invalid state unless validation is added.

**Smart constructor with private raw field.** The public entry point returns
either a valid object or an explicit error. This form is strong in TypeScript,
Rust, Go, and Python code that prefers result values over exceptions. It makes
invalid construction hard to miss in callers.

**Rust newtype.** A tuple struct such as `struct UserId(String);` creates a
distinct type with little runtime ceremony. It is idiomatic when the main goal
is preventing same-type confusion. A public field weakens the pattern because
any caller can rebuild or inspect the raw value without using the type's API.

**Opaque or branded type.** TypeScript can simulate nominal types with a brand
property that callers cannot produce accidentally. This helps distinguish
`UserId` from `OrderId` while emitting a string at runtime. It does not move
behavior into an object unless paired with functions that accept the branded
type.

**Enum replacement for closed sets.** When the primitive is a small type code,
an enum may be the right target. Use it when the legal set is closed and each
member has little behavior. Move to State, Strategy, or polymorphism when each
member grows different behavior.

**Composite value object.** Sometimes the primitive should not become a
single-field object. A money amount may need amount plus currency. A date range
needs start plus end. A postal address has several fields. The refactoring can
start with one primitive, but the correct destination may be Extract Class or
Introduce Parameter Object.

**Boundary adapter only.** In services with strict external schemas, keep the
wire DTO primitive and convert immediately into the domain object. Convert back
only when leaving the domain. This preserves compatibility without spreading
raw primitives through domain code.

**Validation library wrapper.** Some teams centralize validation with schema
libraries. That can be sound at boundaries, but it is not a full replacement
when domain code still accepts primitives. The schema validates one input
event. The object carries the proof afterward.

**Migrating object with temporary dual API.** A legacy codebase may need a
short-lived period where a function accepts both the primitive and the new
object. Use this form only as a migration bridge. Keep the primitive overload
deprecated, make it construct the object immediately, and remove it once callers
have moved. A permanent dual API trains new code to bypass the type.

**Public constructor versus named parser.** A public constructor is concise
when invalid input is a programmer error. A named parser such as
`EmailAddress.parse` or `Quantity.tryCreate` is clearer when invalid input is
expected from users, files, or partners. The choice affects caller ergonomics
more than object structure. Judgement. Prefer result-returning parse functions
at trust boundaries and throwing constructors in tests and code that already
holds trusted data.

**Canonical storage versus original storage.** Some objects preserve the
original primitive, while others store a canonical form. An email object may
keep lowercased domain text but preserve local-part case for display. A path
object may preserve spelling while computing normalized comparisons elsewhere.
Pick this deliberately. If equality is based on canonical form but logging uses
original form, tests need to cover both. If only canonical form is kept, error
messages may lose what the caller actually supplied.

## 9. Known production uses

**Python standard library, `pathlib.Path`.** Python's `pathlib` module is
documented as object-oriented filesystem paths, with classes representing file
system paths and methods for path operations. It exists beside `os.path`, which
is documented for lower-level path manipulation on strings
(https://docs.python.org/3/library/pathlib.html, verified 2026-08-02). This is
a production library example of replacing path strings with an object that
names path semantics and owns path behavior.

**Python standard library, `uuid.UUID`.** The `uuid` module provides immutable
`UUID` objects and functions for generating UUIDs, with construction from
hex, bytes, fields, integer, or other representations. Its documentation also
states that UUID object comparisons are made through their integer attribute
and that comparison with a non-UUID object raises `TypeError`
(https://docs.python.org/3/library/uuid.html, verified 2026-08-02). That is a
named object replacing a raw identifier string, bytes, or integer while keeping
UUID semantics in one type.

**Java SE, `java.time.LocalDate`.** Java SE 21 documents `LocalDate` as a final
class for a date without time zone in the ISO-8601 calendar system, an immutable
date-time object that represents a date and does not represent a time, time
zone, or instant. The same page documents factory methods such as `of` and
`parse`, and states that invalid day values cause an exception
(https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/time/LocalDate.html,
verified 2026-08-02). This is a production library example of replacing raw
year, month, day, epoch-day, or string forms with an object that owns date
rules.

**Rust standard library, `std::num::NonZero`.** Rust documents `NonZero<T>` as
a value known not to equal zero. The documentation states that `NonZero<T>` has
the same layout and bit validity as `T` except that the all-zero bit pattern is
invalid, and that `Option<NonZero<T>>` is compatible with `T` in FFI
(https://doc.rust-lang.org/std/num/struct.NonZero.html, verified
2026-08-02). This is a production library example where an integer invariant is
captured as a type without paying the usual option-size cost.

**Python standard library, `ipaddress`.** The `ipaddress` module provides
objects for IPv4 and IPv6 addresses, networks, and interfaces, and its factory
functions raise `ValueError` when input does not represent a valid address or
network (https://docs.python.org/3/library/ipaddress.html, verified
2026-08-02). This is a named library example of turning strings or integers
that happen to look like network addresses into objects with address behavior.

## 10. Consequences

Positive.

- The concept gets a searchable name in the codebase.
- Invalid states can be rejected at construction instead of defended against at
  every use.
- Same-type parameter swaps become compile-time errors in nominal languages and
  detectable type errors in branded or opaque variants.
- Validation, parsing, normalization, formatting, and comparison rules move to
  one place.
- The primitive representation can change behind the object without rewriting
  all consumers.
- Test suites shrink around consumers because they can accept an already valid
  object rather than retesting raw input rules.
- Security and privacy policy for sensitive values can be attached to a type,
  for example redacted string conversion for tokens.

Negative.

- The codebase gains more types, more files, and more import edges.
- Serialization and persistence need mapping code that a primitive did not
  need.
- Equality, hashing, ordering, and string conversion become contracts the team
  must get right.
- In some runtimes, wrappers add allocations or boxing on paths where raw
  primitives were cheap.
- Overuse creates wrapper noise around values that have no domain rule.
- A half-migrated codebase can be worse than either end state, because some
  paths accept the object and others still accept the raw primitive.
- Poorly designed escape hatches can make every caller unwrap the value, which
  keeps the smell while adding ceremony.

## 11. Failure modes and misuse

Judgement. The following triples name observable failure patterns seen in code
review and production diagnosis.

**Forgotten boundary conversion.** Symptom. Invalid input is rejected by one API
endpoint but accepted by a batch import, message consumer, or admin tool. Cause.
The new object was introduced inside one request path rather than at every
trust boundary. Fix. Search all constructors, deserializers, and repository
hydration paths for the raw primitive and force conversion at the edge.

**Leaky raw accessor.** Symptom. Most call sites immediately call `.value`,
`.raw`, or `.toString()` and continue using helper functions around the
primitive. Cause. The object was created before behavior moved onto it. Fix.
Move the most repeated operation into the object, then delete the helper or
restrict it to boundary adapters.

**Validation split between object and caller.** Symptom. A caller checks length
or range before constructing the object, while the object checks a different
version of the same rule. Cause. The team kept defensive validation at callers
after introducing the construction gate. Fix. Make the object the rule owner
and change callers to handle construction failure.

**Mutable value object.** Symptom. A value used as a dictionary, map, or set key
vanishes after a field changes, or equality results change during a request.
Cause. The replacement object allows mutation of fields used for equality or
hashing. Fix. Make the object immutable, or stop using it as a value object and
model identity explicitly.

**Equality by identity.** Symptom. Two instances that print the same raw value
miss a cache, fail a set lookup, or compare unequal in tests. Cause. The class
did not define equality and hashing by value in a language where objects
default to reference equality. Fix. Implement equality and hashing from the
canonical fields, then add a contract test.

**Representation chosen too early.** Symptom. `Money` wraps a decimal amount,
then currency checks appear beside it at every call site. Cause. The primitive
was replaced with a single-field object when the true concept needed multiple
fields. Fix. Expand the object to include the missing field, or replace it with
a composite Value Object.

**Wrapper flood.** Symptom. A code review contains new classes named
`Description`, `Count`, `Text`, and `Number`, each with one getter and no rule.
Cause. The team applied the catalog move mechanically to every primitive. Fix.
Delete wrappers that do not meet dimension 4, or inline them with Inline Class.

**Exception-only construction in bulk imports.** Symptom. A large import emits
millions of stack traces for expected bad rows and spends more time handling
exceptions than parsing data. Cause. The construction gate uses exceptions for
routine negative cases in a high-volume path. Fix. Add a result-returning parse
API for bulk validation and keep throwing constructors for programmer errors.

**Deserialization bypass.** Symptom. An object exists in memory with a raw value
that its constructor would reject. Cause. Reflection, ORM hydration, JSON
binding, or test fixtures wrote fields directly. Fix. Route deserialization
through the same construction gate, or add post-load validation that calls the
gate.

## 12. Trade-off matrix

| Force | Replace Primitive with Object | Keep primitive with helper functions | Introduce Parameter Object | Enum | Type alias |
|---|---|---|---|---|---|
| Type safety | Strong when the type is nominal or branded | Weak, same primitive still accepted | Strong for grouped fields | Strong for closed sets | Weak in most languages |
| Validation locality | One construction gate | Repeated or convention-based | One constructor for the group | One parser for enum values | None by itself |
| Behavior location | On the object or close to it | In scattered helpers | On the parameter object | On enum methods or match arms | In helpers |
| Serialization friction | Medium, needs mapping | Low | Medium, maps several fields | Low to medium | Low |
| Runtime cost | Medium in heap-object runtimes, low in value forms | Low | Medium | Low | Low |
| Best problem fit | One concept hidden inside one primitive | Local technical values | Several values that travel together | Small closed category | Documentation-only naming |
| Refactoring cost | Medium, touches type signatures | Low | Medium to high | Low to medium | Low |
| Risk of overuse | Medium | Low | Medium | Low | Medium, may give false safety |
| Later model growth | Good, object can gain behavior | Poor, helpers keep spreading | Good for multi-field behavior | Limited when variants need state | Poor |

Reading of the table. Replace Primitive with Object wins when one primitive
stands for one domain concept with rules. Introduce Parameter Object wins when
several primitives form one concept. Enum wins when the legal values are closed
and behavior is small. A type alias improves readability, but it rarely stops a
wrong value from being passed.

## 13. Related and incompatible patterns

**Primitive Obsession.** This refactoring is the principal treatment for that
smell. The smell names the absence of a domain type. The refactoring creates
one and then moves rules onto it.

**Value Object.** The normal destination. If the replacement object has no
conceptual identity, is immutable, and compares by value, it is a Value Object.
Fowler's Value Object note gives the equality and immutability framing cited in
dimension 1 (https://martinfowler.com/bliki/ValueObject.html, verified
2026-08-02).

**Domain Primitive.** A stricter domain-driven variant. Domain Primitive treats
the replacement object as a boundary security device, validated at creation and
used everywhere past the boundary.

**Introduce Parameter Object.** Composes when several primitives are passed
together. A `DateRange` parameter object may contain two date objects, or may be
the correct object to introduce instead of wrapping each date separately.

**Change Reference to Value.** Composes when the replacement begins as a mutable
reference object and later needs value equality and immutability. That
refactoring tightens the object after the primitive has been removed.

**Encapsulate Variable.** Often comes first. If a primitive field is public or
widely written, encapsulate it so construction and assignment pass through one
place before changing its type.

**Replace Conditional with Polymorphism.** Often follows the type-code variant.
First replace the raw code with a named object or enum. Then move per-code
behavior into variants if branches keep growing.

**Inline Class.** The direct exit path and an incompatible end state. If the new
object has no invariant, behavior, or type-safety value, Inline Class removes
it and restores the primitive.

**Data Class.** A misuse destination. A wrapper with fields and accessors but no
owned behavior may become a Data Class. That is acceptable for some DTOs, but it
is not a finished treatment for Primitive Obsession inside the domain model.

## 14. Refactoring path in and out

Introducing the refactoring.

1. Pick one primitive concept. Do not start with every string in the project.
   Choose a value with a clear rule, repeated behavior, or same-type confusion.
2. Name the object from the domain vocabulary. Prefer `EmailAddress`,
   `Quantity`, `Priority`, or `CustomerId` over `StringWrapper`.
3. Add the type with one private raw field and a construction gate. For legacy
   code, let it accept every value currently present in production data before
   tightening rules.
4. Add tests for valid construction, invalid construction, equality, hashing,
   and the first behavior moved onto the type.
5. Change the narrowest field or parameter from primitive to object. Let the
   compiler, type checker, or failing tests list the call sites.
6. At each call site, decide whether it is a boundary or domain code. Boundary
   code constructs or serializes. Domain code should receive and pass the
   object without unwrapping.
7. Move one repeated helper into the object. Delete or deprecate the helper so
   future code cannot keep the old shape alive.
8. Repeat across nearby call sites until raw primitives appear only at
   boundaries.
9. Tighten visibility. Make the raw field private, keep constructors narrow,
   and avoid general-purpose raw accessors except where mapping code requires
   them.
10. Once the object is established, consider richer moves such as introducing a
   composite Value Object, replacing conditionals with polymorphism, or turning
   a type code into an enum.

Granularity matters. A good first slice changes one vertical path from boundary
to storage, not one horizontal layer across the whole product. For example,
change checkout quantity through the HTTP handler, command object, pricing
service, and repository mapping before changing catalog quantity, inventory
quantity, and analytics quantity. That produces one complete path where raw
input is short-lived. It also gives the team one real example to copy.

Compatibility also matters. If a public API or plugin interface currently
accepts a primitive, changing the signature is a breaking change. In library
code, add the object-accepting overload first, route the primitive overload
through it, mark the primitive overload deprecated, and document the removal
version. In application code with no external callers, prefer a direct change
and let the compiler identify every internal call site.

Data cleanup can block the refactoring. A stricter constructor may reject rows
that already exist. In that case, add an audit query or script before changing
the type, classify bad rows, and decide whether to repair, quarantine, or
temporarily grandfather them. Do not weaken the object forever to accommodate
historic data unless the domain truly accepts that data now.

Moving out of the refactoring.

1. Confirm the object has no invariant, no behavior, no same-type safety value,
   and no security or privacy policy.
2. Move any remaining behavior to the one consumer that still needs it, or
   delete it if it is dead.
3. Change consumers from object to primitive one at a time, keeping conversion
   at the old object's boundary until the last consumer is changed.
4. Inline the raw field into each caller using Inline Class.
5. Delete construction tests that only tested the removed wrapper, and keep
   tests for any remaining rule at its new owner.
6. Run a search for the old type name, the old helper names, and the raw field
   accessor to catch stale references.

Judgement. Moving out should be uncommon. When a wrapper feels annoying, first
check whether behavior was never moved onto it. The fix may be to finish the
refactoring rather than undo it.

## 15. Testing and verification

Test the construction gate first. Use table tests for valid and invalid values,
including empty input, boundary numbers, malformed strings, normalization cases,
and values copied from production incidents. The test should assert the exact
failure category where callers act on it.

Test equality and hashing next. Two objects constructed from equivalent raw
input should compare equal and behave correctly as map or set keys. Two objects
from different concepts should not be comparable unless the domain explicitly
allows it.

Test moved behavior on the object, not through every consumer. If `Priority`
owns `higherThan`, test priority ordering once. Consumers that accept a
`Priority` then need tests for their own decisions, not for parsing priority
strings again.

Test the boundary adapters. JSON, database rows, message payloads, CLI flags,
and third-party API responses still start as primitives. Round-trip tests should
prove that serialization and deserialization preserve the canonical value, and
negative tests should prove malformed external input cannot bypass the gate.

Use mutation testing or focused fault injection for high-risk validators. Delete
one check, weaken one range, or skip one normalization step and confirm a test
fails. A value object with incomplete validation can spread false confidence
through the codebase.

Use compile-time tests where the language supports them. TypeScript can use
`tsc --noEmit` with an expected error file. Rust can use compile-fail tests in
larger crates. Java and Swift can rely on ordinary compilation to catch wrong
parameter types when the replacement is nominal.

Add characterization tests before touching high-traffic legacy code. Capture
the current accepted and rejected values from logs, fixtures, or production
samples, then run the same set through the new construction gate. This does not
mean the old behavior is correct. It tells reviewers exactly which behavior is
being preserved and which behavior is being changed.

Add persistence tests for both directions. Hydration should reject invalid
stored data or route it through an explicit legacy repair path. Serialization
should write the primitive shape expected by the schema, not an accidental
object dump with private fields or brand tags. This is especially important in
TypeScript and Python, where JSON conversion can quietly emit whatever object
shape happens to exist at runtime.

For sensitive values, test display output. A secret wrapper should print a
redacted value in debug logs, errors, and normal string formatting unless a
narrow API asks for the secret form. This test prevents a later convenience
method from turning the object back into a logging hazard.

What became easier. Downstream domain services can construct known-good objects
in fixtures and stop testing invalid primitives in every consumer. Mocks become
less necessary because the object is pure and small.

What became harder. Boundary tests matter more. Persistence mappings and JSON
converters become part of the correctness surface. Test data builders may need
factory methods for valid objects, otherwise tests will bypass construction and
recreate the old problem.

## 16. Observability signals

Judgement. A healthy replacement object should be boring in production. The
signals live at construction, conversion, and escape points.

Record construction failures at boundaries. Count them by type name, failed
rule, endpoint or source system, and release version. A spike in
`EmailAddress.invalid_format` from one importer points to upstream data drift.
A spike across all entry points after a deploy points to a rule change or a
parser bug.

Record normalization changes when they matter. If a constructor trims,
lowercases, rounds, or canonicalizes input, count how often the canonical value
differs from the raw value. A sudden change in that rate can reveal a client
that changed formatting before it causes domain errors.

Track raw unwrap use at boundaries if the language makes it easy. A rising
count of raw access from domain packages is a warning that the object is not
owning enough behavior. Keep this signal coarse. Do not log sensitive raw
values.

Track equality-sensitive caches. If the object becomes a cache key, hit rate is
a useful indirect check of equality and hashing. A drop to near zero after the
refactoring suggests identity equality, missing canonicalization, or separate
types being mixed.

Watch deserialization rejects after schema changes. If a deployment changes
JSON shape, database mapping, or a message contract, malformed-value metrics
should stay stable or move in an explained way. Deep domain construction
failures are a bad sign. They mean raw data crossed too far before wrapping.

Track adapter coverage during migration. A temporary metric can count calls to
deprecated primitive overloads by caller, endpoint, or package. The healthy
shape is a steady decline to zero, followed by deleting the overload. A flat
line means migration has stalled. A rise means new code is using the old path
and the refactoring needs enforcement through lint, type ownership, or review.

Keep high-cardinality values out of labels. The type name, failed rule, and
source system are useful dimensions. The raw email address, full path, token,
or account identifier usually is not. Log a sampled, redacted example only when
diagnosis requires it and policy allows it.

A healthy dashboard shows boundary rejection rates that match expected user or
partner error rates, low or zero construction failures inside domain packages,
stable normalization rates, and no unexplained growth in raw accessor use. A
failing one shows invalid construction away from boundaries, sudden spikes by
source, or cache behavior that changes after equality code changed.

## 17. Security and privacy implications

This refactoring can reduce security risk when the primitive carries a
security-sensitive concept. Tokens, password hashes, tenant IDs, account IDs,
SQL identifiers, file paths, email addresses, and authorization scopes are poor
bare strings because a general string API does not know which operations are
allowed. A dedicated type can make the safe operations explicit.

The main security gain is boundary validation. Raw input becomes either a valid
domain object or a rejected value before it reaches business logic. That helps
with injection defenses only when the object's methods expose safe operations.
For example, a `SqlIdentifier` that validates against an allowlist and only
renders through a quoted identifier function is useful. A wrapper that exposes
the raw string and lets callers concatenate it into SQL is not.

The second gain is redaction. A `SessionToken` or `ApiKey` object can define
debug and string conversion to return a redacted form. A plain string cannot
protect itself from accidental logging. The object should still provide a
deliberate, narrowly named method for the few places that need the secret
bytes.

The privacy angle is similar. A type named `EmailAddress` or `NationalId`
creates one place to attach masking, retention tags, audit rules, or encrypted
serialization. It also makes code search for sensitive data much more reliable
than searching every string parameter named by convention.

There are risks. A replacement object may make reviewers think a value is safe
when its constructor is weak. A raw accessor may leak sensitive data faster
because the type now moves through more layers. Equality methods for secrets
can leak timing information if they use ordinary string comparison. Serialization
frameworks may bypass constructors and hydrate invalid or unredacted values.

Where the refactoring is silent, say so. It does not encrypt data. It does not
authenticate callers. It does not sanitize every possible sink. It gives a
concept one owner. Security still depends on the owner enforcing the correct
policy.

## 18. References

1. Martin Fowler. *Refactoring. Improving the Design of Existing Code*. 2nd
   edition. Addison-Wesley, 2018. Chapter 3, "Bad Smells in Code," and chapter
   7, "Encapsulation." Source for Primitive Obsession and the refactoring
   catalog family.
2. Martin Fowler. "Replace Primitive with Object." Refactoring Catalog.
   https://refactoring.com/catalog/replacePrimitiveWithObject.html. Verified
   2026-08-02. Source for the canonical name and aliases.
3. Martin Fowler. "Value Object." Bliki.
   https://martinfowler.com/bliki/ValueObject.html. Verified 2026-08-02.
   Source for the equality and immutability framing used to distinguish the
   destination pattern from the refactoring.
4. Eric Evans. *Domain-Driven Design. Tackling Complexity in the Heart of
   Software*. Addison-Wesley, 2003. Chapter 5, "A Model Expressed in
   Software," section "Value Objects." Source for the domain modeling relation.
5. Python Software Foundation. "`pathlib`. Object-oriented filesystem paths."
   Python 3.14 documentation. https://docs.python.org/3/library/pathlib.html.
   Verified 2026-08-02. Source for the `pathlib.Path` production use.
6. Python Software Foundation. "`uuid`. UUID objects according to RFC 9562."
   Python 3.14 documentation. https://docs.python.org/3/library/uuid.html.
   Verified 2026-08-02. Source for the `uuid.UUID` production use.
7. Oracle. "Class LocalDate." Java SE 21 API Specification.
   https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/time/LocalDate.html.
   Verified 2026-08-02. Source for the `java.time.LocalDate` production use.
8. Rust Project Developers. "Struct NonZero." Rust standard library.
   https://doc.rust-lang.org/std/num/struct.NonZero.html. Verified
   2026-08-02. Source for the `std::num::NonZero` production use.
9. Python Software Foundation. "`ipaddress`. IPv4/IPv6 manipulation library."
   Python 3.14 documentation. https://docs.python.org/3/library/ipaddress.html.
   Verified 2026-08-02. Source for the `ipaddress` production use.

## Code examples

The examples use TypeScript, Python, and Rust because the refactoring appears
often in service code written in those languages and each compiler or runtime
can check a different part of the shape.

### TypeScript

```typescript
type EmailAddress = {
  readonly value: string;
  readonly kind: "EmailAddress";
};

function parseEmailAddress(input: string): EmailAddress {
  const value = input.trim().toLowerCase();
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(value)) {
    throw new Error(`invalid email: ${input}`);
  }
  return { value, kind: "EmailAddress" };
}

function domainOf(email: EmailAddress): string {
  return email.value.slice(email.value.indexOf("@") + 1);
}

const email = parseEmailAddress(" Ada@Example.COM ");
console.log(domainOf(email));
```

### Python

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Quantity:
    value: int

    def __post_init__(self) -> None:
        if self.value <= 0:
            raise ValueError("quantity must be positive")

    def total_cents(self, unit_price_cents: int) -> int:
        return self.value * unit_price_cents


def line_total(quantity: Quantity, unit_price_cents: int) -> int:
    return quantity.total_cents(unit_price_cents)


if __name__ == "__main__":
    print(line_total(Quantity(3), 499))
```

### Rust

```rust
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
struct Percentage {
    basis_points: u16,
}

impl Percentage {
    fn new(basis_points: u16) -> Result<Self, String> {
        if basis_points > 10_000 {
            return Err("basis points out of range".to_string());
        }
        Ok(Self { basis_points })
    }

    fn apply_to_cents(self, cents: u32) -> u32 {
        cents * u32::from(self.basis_points) / 10_000
    }
}

fn discount_cents(subtotal_cents: u32, rate: Percentage) -> u32 {
    rate.apply_to_cents(subtotal_cents)
}

fn main() {
    let rate = Percentage::new(1_500).expect("valid rate");
    println!("{}", discount_cents(2_500, rate));
}
```
