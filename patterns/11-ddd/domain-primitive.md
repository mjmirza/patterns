---
name: Domain Primitive
slug: domain-primitive
family: 11-ddd
category: Tactical Modeling
aliases: [Tiny Type, Wrapper Type, Strong Type, Notification-Aware Value Object]
first_described: "Fowler and Yegor Bugayenko, popularized by Dan Bergh Johnsson and Daniel Deogun 2019"
maturity: canonical
related: [value-object, entity, specification, factory, null-object]
incompatible_with: []
verified: 2026-08-02
---

# Domain Primitive

## 1. Name, aliases, and lineage

A Domain Primitive is a small, immutable type that replaces a language
primitive, a `String`, an `int`, a `float`, a `List<String>`, at any point in a
codebase where that primitive is standing in for a concept from the problem
domain. An `EmailAddress` class instead of a `String`. A `PositiveInt`
instead of an `int`. A `Money` instead of a `BigDecimal` paired with a
currency string passed separately.

The name comes from Dan Bergh Johnsson and Daniel Deogun, who coined "Domain
Primitives" as the central idea of their book *Secure by Design*, Manning
Publications, 2019, chapter 5, "Domain primitives". Deogun, Johnsson and Daniel
Sawano describe the pattern as the mechanism that lets a codebase reject
invalid state at the boundary rather than defending against it everywhere
downstream (Deogun, Johnsson, Sawano, *Secure by Design*, Manning, 2019,
chapter 5, section 5.1, "What is a domain primitive").

The idea itself predates that name by more than a decade. Martin Fowler's
catalog names the general shape a Value Object (Martin Fowler, *Patterns of
Enterprise Application Architecture*, Addison-Wesley, 2002, page 486, "Value
Object"), and Eric Evans places Value Object as one of the two tactical
building blocks of a domain model alongside Entity (Eric Evans, *Domain-Driven
Design*, Addison-Wesley, 2003, chapter 5, "A Model Expressed in Software",
"Value Objects"). What Johnsson and Deogun add on top of Fowler and Evans is
not a new structural idea, it is a naming and a discipline. Every primitive
that carries domain meaning is wrapped, with no exceptions, and the wrapper's
constructor is the single place the domain's validity rules are enforced.

The community-preferred alternate name is Tiny Type, popularized independently
by Yegor Bugayenko's blog writing on object thinking around 2015 to 2016 and
used widely in the Kotlin and Rust communities to describe the same
single-field wrapper class used purely to distinguish two values of the same
underlying representation (Bugayenko's own coinage is not tied to a single
dated publication that could be cited to a page, so this entry treats "Tiny
Type" as a community term rather than a first-description citation). "Wrapper
Type" and "Strong Type" are informal synonyms used in code review discussion
and are not attributable to a single source.

A Domain Primitive is best understood as a strict, opinionated subset of Value
Object rather than a fully separate pattern. Every Domain Primitive is a Value
Object. Not every Value Object is a Domain Primitive, because a Value Object
can wrap several fields into a composite, an `Address` with street, city, and
postal code, while a Domain Primitive, in the strict Johnsson and Deogun
sense, typically wraps a single conceptual value and layers validation,
parsing, and self-description onto it. This entry treats the distinction as
one of intent and discipline, and dimension 4 below draws the line precisely.

## 2. Problem and context

A codebase accretes validation logic at the edges and loses track of where the
truth lives. An `EmailAddress` arrives as a `String` from an HTTP request body.
It is checked for a valid shape in the controller. It travels through three
service methods and two repository calls. A fourth service, added eighteen
months later by someone who never read the controller code, receives the same
`String` and, having no reason to distrust it, uses it directly in an outbound
SMTP call without re-checking it. The email came from a batch import job this
time, not the web form, and the import job skipped validation. The SMTP
library throws on the malformed address, or worse, silently accepts it and the
message disappears.

This is the central problem the pattern answers, a primitive type carries no
memory of whether it has been validated. `String` cannot distinguish "this
came from a form the controller validated" from "this came from anywhere at
all." Every function that receives a `String` parameter named `email` has two
choices, trust it or re-validate it, and a large codebase reliably chooses
both inconsistently across its call sites. Deogun, Johnsson, and Sawano frame
this directly as a security problem, not merely a hygiene one, injection
attacks, business-logic errors, and data corruption share a root cause, that
untyped data crosses a trust boundary with no enforcement at the boundary
(Deogun, Johnsson, Sawano, *Secure by Design*, Manning, 2019, chapter 5,
section 5.2, "The need for domain primitives").

The context that produces this problem has three recognizable shapes in a real
codebase.

- **A concept has rules the language type cannot express.** An age is an
  `int`, but a negative age or an age of four hundred is nonsense, and `int`
  permits both. A quantity ordered is an `int`, but zero or negative is
  invalid for most order lines, and `int` permits both.
- **A concept is confusable with another concept of the same underlying
  type.** A `String` holding a user ID and a `String` holding a tenant ID are
  interchangeable to the compiler, and swapping them at a call site produces a
  bug the type system cannot catch. Two `int` parameters, `width` and
  `height`, can be passed in the wrong order and every call site compiles.
- **A concept requires parsing, normalization, or formatting logic that would
  otherwise be duplicated.** An IBAN needs its check digits validated, a phone
  number needs a country-code-aware format, a currency amount needs its
  minor-unit rounding rule. Without a Domain Primitive this logic is written
  once, then copy-pasted the second time it is needed, then drifts.

Nickolas Means and others discussing this pattern in Go and other languages
without inheritance or classical wrapper ergonomics describe the same problem
under the heading "primitive obsession," a term from Martin Fowler and Kent
Beck's refactoring catalog naming exactly this smell (Martin Fowler,
*Refactoring*, 2nd edition, Addison-Wesley, 2018, chapter 3, "Bad Smells in
Code," "Primitive Obsession"). Domain Primitive is the named cure Johnsson and
Deogun give to the smell Fowler and Beck named.

## 3. Forces

- **Type safety versus allocation and boxing cost.** Wrapping a primitive in a
  class or struct trades a raw stack-friendly value for a heap-allocated or
  boxed object in languages without zero-cost newtypes. Rust, Kotlin's inline
  value classes, and C#'s `readonly struct` largely eliminate this cost. Java
  before value types, Project Valhalla, still in preview as of the JDK
  releases through 2026, and TypeScript at runtime do not, so every Domain
  Primitive is a real object allocation in those languages. The pattern
  favours correctness enforced by the type system over raw throughput at the
  micro-allocation level, and this is the trade the pattern openly accepts
  rather than hides.
- **Validation locality versus validation redundancy.** Concentrating every
  validation rule for a concept in one constructor means the rule is written
  once. It also means every caller that wants to construct the value must go
  through that constructor, which is friction the pattern intends as a
  feature. Code that resists constructing a Domain Primitive because the
  input is not yet known to be valid is doing exactly what the pattern wants,
  forcing the validation to happen before the value exists at all.
- **Explicitness versus verbosity.** A function signature reading
  `send(EmailAddress to, EmailAddress from, Subject subject, Body body)` is
  self-documenting in a way `send(String, String, String, String)` never can
  be, and it is also visibly longer to write and to read at every call site
  and every constructor. Teams that reach for Domain Primitives inconsistently,
  wrapping some concepts and not others, tend to produce codebases that look
  more chaotic than either extreme, because the reader cannot tell whether an
  unwrapped `String` is unwrapped by omission or by design.
- **Boundary enforcement versus boundary friction.** The pattern is strongest
  exactly at a trust boundary, an HTTP handler, a message deserializer, a
  database read. Constructing the Domain Primitive there and passing it
  inward means the rest of the codebase never re-checks the rule. This
  requires discipline at every boundary, and a single boundary that
  deserializes directly into a raw primitive and passes it inward unwrapped
  reintroduces the exact vulnerability the pattern exists to close.
- **Consistency across a team versus onboarding cost.** A codebase that wraps
  every domain concept consistently is easier to navigate once a developer
  understands the convention, and confusing to a developer who does not yet
  know it, because a `PositiveInt` where a plain number was expected can read
  as unnecessary ceremony until its purpose is understood.

## 4. Applicability and non-applicability

Reach for a Domain Primitive when a value, at the point it enters the system
or is computed, satisfies at least one of these.

- The domain places a validity rule on the value that a bare language
  primitive cannot express, a range, a format, a required non-emptiness, a
  checksum.
- Two values of the same underlying primitive type are semantically distinct
  and confusable at a call site, a `UserId` and an `OrderId` both being a
  `String` or a `long`.
- The value requires non-trivial parsing, canonicalization, or formatting
  logic that is used in more than one place, or is likely to be.
- The value crosses a trust boundary, network input, file input, a message
  queue payload, and its validity at that boundary determines whether
  everything downstream can treat it as safe.
- The value participates in domain logic where its type communicates intent
  to a reader better than its underlying representation would, `Money`
  communicating "this is currency, do not use floating point equality on it"
  more clearly than `BigDecimal`.

### Non-applicability

Do not reach for a Domain Primitive in any of these situations. This list is
the more important half of the dimension and the one most catalogs skip.

- **A purely technical, non-domain value with no validity rule.** A page-size
  parameter for pagination, a retry-count counter, a loop index, a byte
  offset into a buffer. Wrapping these adds ceremony with no corresponding
  gain, because there is no domain rule to enforce and no confusion risk
  worth guarding against. Deogun, Johnsson, and Sawano are explicit that
  Domain Primitives model the domain, and a value with no domain meaning is
  out of scope by definition (Deogun, Johnsson, Sawano, *Secure by Design*,
  Manning, 2019, chapter 5, section 5.1).
- **A value used exactly once, in one function, with no risk of being
  confused with anything else and no validity rule beyond what the caller
  already guarantees.** The overhead of a class, a constructor, and equality
  and hashing implementations for a value that lives for three lines inside
  one method is pure cost.
- **A hot inner loop in a language without zero-cost wrapper types**, where
  profiling has shown the allocation or boxing cost of the wrapper is
  measurable and material. This is a narrow, evidence-driven exception, not a
  blanket exemption for performance-sensitive code, and it should be revisited
  once the language or runtime gains value types.
- **A value whose validity genuinely depends on context that is not available
  at construction time.** A `DiscountedPrice` that is only valid in
  conjunction with a specific `Order` and a specific `Promotion` is closer to
  a Specification or a computed property of an Entity than to a standalone
  Domain Primitive, because its validity is not a property of the raw number
  alone. Forcing it into a self-validating wrapper hides that the rule is
  actually relational.
- **Framework or ORM boundary types the framework itself owns and validates**,
  where introducing a parallel domain wrapper produces two competing sources
  of truth instead of one. When a framework's own type already encodes the
  domain rule faithfully and the codebase has no reason to be independent of
  that framework, an additional wrapper is redundant ceremony rather than a
  safety gain.
- **A composite value with several independently meaningful fields and no
  single scalar identity.** A full postal address is more naturally a
  multi-field Value Object than a single-field Domain Primitive, even though
  the two patterns share a base. Forcing a composite concept into a
  single-field wrapper by concatenating fields into one string loses the
  structure the composite Value Object would have preserved.

## 5. Structure

- **Domain Primitive.** The wrapper type itself. Holds exactly the underlying
  representation, plus enough state to make that representation valid and
  meaningful, no more. Its constructor, or an explicit static factory in
  languages that discourage failable constructors, is the only route to
  producing an instance, and that route validates every invariant before the
  instance exists. Once constructed, the instance is immutable for its entire
  lifetime, so no code path can observe it in an invalid intermediate state.
- **Validation rule set.** The specific checks the constructor runs, encoded
  either inline in the constructor body or delegated to a Specification
  object when the rule is reused across several primitives or needs to be
  composed, see dimension 13. The rule set is the domain expert's knowledge
  made executable, and Evans frames exactly this move, capturing a domain
  rule as code rather than as a comment or a convention, as the purpose of
  tactical patterns generally (Eric Evans, *Domain-Driven Design*,
  Addison-Wesley, 2003, chapter 5).
- **Underlying representation.** The primitive, or small set of primitives,
  the Domain Primitive is built from. A `Money` typically wraps a minor-unit
  integer and a currency code, not a `float`, because floating-point
  arithmetic on currency introduces representation error that a domain rule
  about money cannot tolerate.
- **Consumer.** Any code, an application service, another Domain Primitive, an
  Entity, that accepts the wrapped type as a parameter or field type instead
  of the raw primitive. The consumer's own code becomes simpler because it no
  longer needs to re-validate, and its signature becomes self-documenting.
- **Boundary translator.** The code at the system's edge, a controller, a
  deserializer, a repository's row-mapping code, responsible for constructing
  the Domain Primitive from raw external input and for surfacing a
  translated, domain-meaningful error when construction fails. This
  participant is often the exact point a Factory pattern is used to isolate
  fallible construction from the wrapper's own constructor, see dimension 13.

## 6. ASCII structure diagram

```
                     +-----------------------------+
                     |  Domain Primitive             |
                     |  (e.g. EmailAddress)          |
                     +-------------------------------+
                     | - value: String  (private)    |
                     +-------------------------------+
                     | + of(raw: String): Result      |<-- validates, never throws
                     | + toString(): String            |     across a trust boundary
                     | + equals(other): boolean         |
                     | + hashCode(): int                 |
                     +-------------------------------+
                              ^ constructed by
                              |
        +---------------------+---------------------+
        |                                             |
+---------------+                          +----------------------+
| Boundary       |  raw String, int, etc.  | Validation rule set   |
| translator     |------------------------->| (inline or delegated |
| (controller,   |                          |  to a Specification) |
| deserializer)  |                          +----------------------+
+---------------+
        |
        | constructs, on success
        v
+----------------------------------------------+
| Consumer (application service, Entity field,  |
| another Domain Primitive)                     |
+----------------------------------------------+
        never receives the raw, unvalidated
        primitive once this boundary is crossed
```

## 7. Dynamics

The runtime shape of a Domain Primitive is deliberately narrow. Most of the
interesting behaviour happens once, at construction, and never again for the
life of the object.

```
Untrusted input arrives
   |
   v
Boundary translator calls EmailAddress.of(rawString)
   |
   v
Constructor / factory runs the validation rule set
   |
   +-- rule fails ------> return a typed failure
   |                       (Result, Either, or a thrown
   |                        domain-specific exception,
   |                        never a raw string message)
   |                                |
   |                                v
   |                       Boundary translator turns the
   |                       failure into an HTTP 400, a
   |                       rejected message, or an error
   |                       accumulated with others for a
   |                       validation-summary response
   |
   +-- rule passes -----> EmailAddress instance created
                            |
                            v
                    Instance is immutable from here on
                            |
                            v
              Passed by reference through every layer
              that follows, service, domain logic,
              repository, outbound integration
                            |
                            v
              No layer downstream re-validates, because
              the type itself is the proof of validity
                            |
                            v
              Equality, hashing, and comparison, when
              needed, delegate to the wrapped value's
              own equality, so two EmailAddress instances
              wrapping the same normalized string are
              interchangeable
```

The one recurring runtime wrinkle is normalization order. If the constructor
lower-cases an email's domain part, or trims whitespace, before validating,
two syntactically different raw strings can produce equal instances, and
equality must be defined on the normalized form, not the original input,
or the type's own equals implementation becomes inconsistent with what a
human would call "the same email address."

## 8. Implementation variants

- **Failable factory returning a Result or Either, never a throwing
  constructor, at the domain layer.** The constructor is private, a static
  `of` or `create` method runs validation and returns a success or a typed
  failure. This is the variant Johnsson, Deogun, and Sawano favour explicitly
  in *Secure by Design*, because it forces every call site to handle the
  possibility of invalid input at the point of construction rather than
  discovering it via an exception thrown somewhere downstream (Deogun,
  Johnsson, Sawano, *Secure by Design*, Manning, 2019, chapter 5, section
  5.4, "Implementing domain primitives").
- **Throwing constructor.** Simpler to write and read in languages and teams
  comfortable with exceptions as control flow for invalid construction. Loses
  the compile-time visibility of the failure path that a Result type gives,
  and pushes the responsibility onto the caller to know which constructors
  can throw. Common in Java codebases predating widespread Either or Result
  libraries.
- **Language-native newtype or inline value class.** Rust's newtype pattern,
  a tuple struct wrapping one field, `struct Email(String)`, Kotlin's
  `value class`, and Haskell's `newtype` give the compiler-level guarantee
  that a Domain Primitive is a distinct type with zero runtime representation
  cost, the wrapper disappears entirely after compilation. This is the
  closest implementation to the pattern's intent with the fewest
  compromises, where the language supports it.
- **Branded or opaque type in a structurally-typed language.** TypeScript has
  no nominal typing, so a plain `type EmailAddress = string` is
  indistinguishable from `string` to the compiler. The idiomatic workaround
  is a "branded type," intersecting the base type with a unique symbol or
  literal tag the compiler treats as distinguishing, `type EmailAddress =
  string & { readonly __brand: "EmailAddress" }`, combined with a smart
  constructor function that is the only place the brand can legally be
  attached.
- **Struct with `Comparable` or operator overloading for numeric Domain
  Primitives.** A `PositiveInt` or `Money` type commonly overloads addition,
  comparison, or ordering so arithmetic on the wrapped concept reads
  naturally while still enforcing the domain rule, addition of two `Money`
  values of different currencies raising a domain error rather than silently
  producing a nonsensical sum.
- **Validation delegated to an injected Specification.** When several Domain
  Primitives share a rule, an age range used by both `Age` and
  `LegalDrivingAge`, the rule is factored into a Specification object the
  constructor consults, rather than duplicating the check, see dimension 13
  for the composition relationship.

## 9. Known production uses

- **Rust's `std::net::Ipv4Addr` and `Ipv6Addr`.** These are Domain Primitives
  in every sense relevant to this entry. An IP address is not a bare `u32` or
  a bare `[u8; 4]`, it is a distinct type constructed through parsing that
  validates the input shape, with its own `Display`, `FromStr`, and equality
  implementations, shipped as part of the Rust standard library
  (`std::net::Ipv4Addr` documentation, Rust standard library,
  https://doc.rust-lang.org/std/net/struct.Ipv4Addr.html, verified
  2026-08-02).
- **Java's `java.time` package, specifically `LocalDate`, `Duration`, and
  `Instant`.** Introduced in JDK 8 as a deliberate replacement for the
  primitive-obsessed `java.util.Date` and raw `long` millisecond timestamps
  that preceded it, each of these types wraps a numeric representation
  behind validated construction and rich, self-describing operations (Oracle,
  "Date Time," the Java Tutorials, https://docs.oracle.com/javase/tutorial/datetime/
  verified 2026-08-02, and JSR 310, the specification that introduced
  `java.time`, https://jcp.org/en/jsr/detail?id=310 verified 2026-08-02).
- **Stripe's public API client libraries model amounts as integer minor
  units accompanied by a currency code, never as a bare float**, and Stripe's
  own API reference states this explicitly as a design rule for every
  currency amount field, "All API requests expect amounts to be provided in
  a currency's smallest unit" (Stripe API reference, "Working with amounts,"
  https://docs.stripe.com/currencies#zero-decimal, verified 2026-08-02). The
  pattern of wrapping an amount as a minor-unit integer plus a currency code,
  rather than a float, is the textbook Domain Primitive shape for money that
  Fowler's Money pattern and Johnsson and Deogun's own `Money` example both
  describe (Martin Fowler, *Patterns of Enterprise Application Architecture*,
  Addison-Wesley, 2002, page 488, "Money").
- **The Kotlin standard library's `Duration` inline value class**, introduced
  as a stable API in Kotlin 1.6, wraps a raw `Long` nanosecond count behind
  a zero-overhead `value class`, exposing typed arithmetic and comparison
  operators instead of exposing the raw number, explicitly to prevent the
  unit-confusion bugs that raw millisecond or second longs caused in earlier
  Kotlin and Java code (Kotlin standard library reference, "Duration,"
  https://kotlinlang.org/api/latest/jvm/stdlib/kotlin.time/-duration/
  verified 2026-08-02).
- **The Deogun, Johnsson, Sawano book itself documents production adoption at
  their own consultancy engagements** as the origin of the pattern's naming,
  describing repeated security incidents traced to unvalidated primitives
  crossing trust boundaries in client codebases as the motivating case for
  writing *Secure by Design* (Deogun, Johnsson, Sawano, *Secure by Design*,
  Manning, 2019, Preface and chapter 1, section 1.1).

## 10. Consequences

Positive.

- Invalid domain state becomes structurally unrepresentable past the
  construction boundary, moving a class of bug from possible, must be
  guarded against everywhere, to impossible, checked once.
- Function and method signatures become self-documenting. A parameter typed
  `EmailAddress` tells the reader what it is and that it has already been
  validated, without a comment.
- Validation, parsing, and formatting logic for a concept lives in exactly
  one place, closing the copy-paste drift that recurs when the same regex or
  range check is written independently at every call site.
- Refactoring the validation rule for a concept, tightening an email regex,
  adding a new currency to a supported list, touches one file instead of an
  unknown number of scattered checks.
- Equality and comparison for the concept are defined once and correctly,
  eliminating the class of bug where one code path compares two email strings
  case-sensitively and another compares them case-insensitively.

Negative.

- More types to declare, more files or classes in a codebase, and more
  boilerplate for equality, hashing, string conversion, and serialization
  unless the language or a library reduces that ceremony automatically.
- Serialization and deserialization frameworks, an ORM, a JSON library, often
  need explicit adapters registered for each Domain Primitive, adding setup
  work that a bare primitive would not have required.
- In languages without zero-cost wrapper types, an allocation or boxing cost
  is paid at every construction, which can matter in a genuinely hot path.
- Inconsistent adoption across a codebase, some concepts wrapped, others not,
  can be more confusing to a new reader than a codebase that uses raw
  primitives everywhere, because the wrapping now carries an implied but
  unstated signal about trust.
- Over-application to values with no domain meaning produces needless
  ceremony and slows development without a corresponding safety gain, which
  is exactly the failure mode dimension 4's non-applicability list exists to
  prevent.

## 11. Failure modes and misuse

- **Anemic wrapper, no validation.** Symptom, a `class EmailAddress { String
  value; }` with a public constructor and no validation logic at all. Cause,
  the team adopted the pattern's name and shape without its purpose,
  treating "wrap it in a class" as the whole job. Fix, move every validity
  check the domain actually cares about into the constructor or factory, and
  make the constructor the only way to obtain an instance, per dimension 5.
- **Leaky escape hatch.** Symptom, the wrapper exposes a public getter
  returning the raw underlying primitive, and code elsewhere in the base
  extracts that raw value, mutates or recombines it, and passes the raw
  value onward instead of a new validated Domain Primitive. Cause, an escape
  hatch was added for a legitimate-seeming reason, logging, a third-party
  library needing a raw string, and the codebase never closed it back off.
  Fix, keep the raw-value accessor but audit every call site of it, and
  prefer returning a value only at genuine system boundaries where the
  Domain Primitive's job is already done.
- **Trust boundary skipped for one call path.** Symptom, most controllers
  construct the Domain Primitive at the edge, but a batch job, an admin
  script, or a message consumer added later deserializes directly into a
  raw type and passes it into the same downstream code, which now silently
  receives an unvalidated value it assumes is safe. Cause, the discipline of
  wrapping at every boundary was not enforced structurally, only by
  convention, and a new boundary was added without anyone re-reading the
  convention. Fix, change every downstream function's signature to require
  the Domain Primitive type rather than the raw primitive, so the compiler
  or type checker itself rejects the unvalidated path, converting a
  convention into a structural guarantee.
- **Validation duplicated instead of shared.** Symptom, `Age` and
  `LegalDrivingAge` each independently implement a range check that happens
  to overlap, and a rule change to one is not applied to the other. Cause,
  the team did not recognize the shared rule and factor it into a common
  Specification or base validation routine. Fix, extract the shared rule
  into a Specification object both Domain Primitives compose, see dimension
  13, so a rule change is made once.
- **Equality defined on the wrong representation.** Symptom, two
  `EmailAddress` instances constructed from `"User@Example.com"` and
  `"user@example.com"` compare as unequal, causing a duplicate-account bug or
  a failed lookup that a human would call obviously wrong. Cause, equality
  delegates directly to the underlying raw string's equality instead of to
  the domain's own notion of sameness, which for email addresses is
  case-insensitive on the domain part per RFC 5321. Fix, normalize at
  construction, before validation and before storage, so equality on the
  stored normalized form is always correct, and never compare on
  un-normalized raw input.
- **Overwrapping a purely technical value.** Symptom, a codebase has a
  `PageNumber` and `PageSize` Domain Primitive for pagination parameters with
  no actual domain rule beyond "must be positive," reviewed and re-reviewed
  in every PR touching pagination, adding friction with no corresponding
  safety gain the team can point to. Cause, the pattern was applied
  mechanically to every primitive rather than to primitives that carry
  genuine domain meaning or confusion risk. Fix, apply the non-applicability
  checklist in dimension 4 before wrapping, and unwrap a value that fails
  every criterion on that list.

## 12. Trade-off matrix

Compared against the two named alternatives that most often compete for the
same code, a plain language primitive with no wrapper, and a general-purpose
multi-field Value Object used even for single-scalar concepts.

| Force | Domain Primitive | Plain primitive (String, int) | General Value Object for everything |
|---|---|---|---|
| Invalid state representable after construction | No, validated once at the boundary | Yes, always, at every call site | Depends, only as disciplined as the team's convention |
| Call-site confusion between two same-typed concepts | Prevented by the compiler or type checker | Common, UserId and OrderId both String | Prevented, but at the cost of a class for even trivial single-scalar values |
| Ceremony for a value with no domain rule | Unwarranted, wastes construction and review effort | None, matches the value's actual simplicity | Unwarranted, same as Domain Primitive misapplied |
| Ceremony for a composite concept, address, coordinates | Awkward, forces a multi-field concept into a single-scalar shape | None at the type level, but no structure either | Correct fit, this is what general Value Object is for |
| Validation rule reuse across concepts | Explicit, factored into a shared Specification when needed | Ad hoc, duplicated per call site | Possible but not the pattern's specific focus |
| Runtime cost in a language without zero-cost wrappers | One allocation per construction | Zero, native representation | One allocation per construction, same as Domain Primitive |
| Serialization and ORM mapping effort | Extra adapter per wrapped type | None, native primitive mapping | Extra adapter per wrapped type, same as Domain Primitive |

## 13. Related and incompatible patterns

- **Value Object.** Domain Primitive is a Value Object, specifically the
  narrow, single-scalar, boundary-enforcing subset of it that Johnsson and
  Deogun named for the security and validation discipline it enforces. Every
  claim about immutability, structural equality, and no independent identity
  that applies to Value Object applies to Domain Primitive unchanged. This
  entry adds the specific discipline of wrapping every primitive that
  crosses a trust boundary, not merely composite concepts.
- **Entity.** Where an Entity's identity persists across state changes, a
  Domain Primitive has no identity at all, only its value, exactly the
  Value Object versus Entity distinction Evans draws (Eric Evans,
  *Domain-Driven Design*, Addison-Wesley, 2003, chapter 5). Entities
  routinely hold fields typed as Domain Primitives, an `Order` Entity's
  `total` field typed as `Money`, its `customerEmail` field typed as
  `EmailAddress`.
- **Specification.** When a validation rule is complex, reused across
  multiple Domain Primitives, or needs to be composed with other rules using
  boolean logic, the rule is factored out into a Specification object the
  Domain Primitive's constructor consults, rather than duplicated inline.
  Eric Evans describes Specification as exactly this kind of explicit,
  reusable predicate object (Eric Evans, *Domain-Driven Design*,
  Addison-Wesley, 2003, chapter 9, "Specification"). The two compose
  cleanly, a Domain Primitive owns its identity as a type, a Specification
  owns a reusable rule the type's constructor applies.
- **Factory.** In languages or team conventions that discourage failable
  constructors, or where construction genuinely needs several steps, a
  dedicated Factory takes over the job of producing a validated Domain
  Primitive, keeping the wrapper type's own API minimal. This is a
  composition relationship, not a replacement. The Factory produces
  instances of the Domain Primitive rather than being an alternative to it.
- **Null Object.** A Domain Primitive that must represent an explicit
  absent state without falling back to a nullable reference sometimes pairs
  with Null Object, an `EmptyEmailAddress` singleton implementing the same
  interface as a real `EmailAddress` but representing the deliberate absence
  of one, rather than every consumer checking for null. This pairing is
  optional and only warranted when absence is itself a meaningful domain
  state rather than an error.
- **No documented incompatibility.** Domain Primitive does not conflict
  structurally with any other pattern in this catalog. Its narrowness, one
  type per concept, immutable, validated at construction, means it composes
  as a field type inside almost any other structural pattern rather than
  competing with one.

## 14. Refactoring path in and out

Introducing a Domain Primitive into code that currently passes a raw
primitive follows Fowler's own "Replace Primitive with Object" refactoring,
described as exactly this move (Martin Fowler, *Refactoring*, 2nd edition,
Addison-Wesley, 2018, chapter 3, "Bad Smells in Code," "Primitive Obsession,"
and the corresponding catalog entry "Replace Primitive with Object").

1. Identify a primitive parameter, field, or return type that carries a
   validity rule, a confusion risk, or reused parsing logic, using the
   applicability checklist in dimension 4.
2. Create the wrapper type with a private or restricted constructor and a
   public failable factory, or a throwing constructor if the team's
   convention favours exceptions. Move every scattered validation check for
   this concept, found by searching for the concept's name near a
   `String`-typed or numeric parameter, into this one constructor.
3. Change the type of the field or parameter from the raw primitive to the
   new Domain Primitive, one call site at a time, letting the compiler or
   type checker surface every place that still passes a raw value. This is
   the step that turns the convention into a structural guarantee.
4. At each surfaced call site, either construct the Domain Primitive from
   already-validated data the caller already has, or push the construction
   further back toward the actual trust boundary, the controller, the
   deserializer, until the raw primitive never travels further than
   necessary.
5. Delete the now-redundant scattered validation checks discovered in step
   2, since the constructor is now the single source of truth.
6. Repeat for the next primitive, rather than attempting a big-bang rewrite
   of an entire codebase, which is rarely tractable and risks a long-lived
   half-migrated state that is more confusing than either extreme.

Removing a Domain Primitive is warranted when a concept it wraps has been
reduced, by a change in the domain itself, to a value with no remaining
validity rule and no remaining confusion risk, matching one of the
non-applicability criteria in dimension 4. The reverse of the same steps
applies, inline the constructor's now-trivial logic at call sites, widen the
field and parameter types back to the raw primitive one call site at a time,
and delete the wrapper type once nothing references it. This direction is
rare in practice, because a concept that once had a domain rule rarely loses
it entirely, but it does happen when a feature the rule protected is removed
from the product.

## 15. Testing and verification

Domain Primitives are, by construction, some of the easiest units in a
codebase to test exhaustively, because their entire behaviour is the
constructor plus a small number of pure methods, with no collaborators to
mock.

- **Boundary and property testing of the constructor.** Test every documented
  valid input produces a successful instance, and every documented invalid
  input, malformed, empty, out of range, produces the specific failure the
  domain expects, not merely "some error." For numeric Domain Primitives,
  property-based testing, feeding the constructor a wide range of generated
  inputs and asserting the invariant, negative numbers always rejected by
  `PositiveInt`, is well suited here precisely because the constructor's
  contract is a small, checkable predicate.
- **Equality and normalization tests.** Verify that two differently-formatted
  but semantically identical raw inputs, different email address casing,
  different whitespace around a trimmed string, produce equal instances, and
  that two semantically different inputs never do. This is the test category
  that catches the equality-defined-on-the-wrong-representation failure mode
  from dimension 11.
- **Serialization round-trip tests.** For any Domain Primitive that crosses a
  process boundary, JSON, a database column, a message queue payload, assert
  that serializing and then deserializing produces an equal instance, and
  that deserializing malformed external data produces the same validation
  failure the constructor would produce for the same raw input, never a
  silent pass-through.
- **What becomes easier because of the pattern.** Downstream code that
  consumes the Domain Primitive no longer needs its own tests for invalid
  input handling of that concept, because invalid instances cannot exist.
  This shrinks the test surface of every consumer, at the cost of
  concentrating responsibility, and therefore test importance, onto the
  wrapper's own constructor tests.
- **What becomes harder.** Testing a consumer with a range of "almost valid"
  inputs to see how gracefully it degrades is no longer meaningful, because
  the consumer will never see such inputs. The test intent shifts entirely
  onto the Domain Primitive's own boundary tests. Teams accustomed to
  integration-style tests that push malformed data through an entire request
  pipeline sometimes find this shift disorienting until they trust the
  unit-level boundary tests are sufficient.

## 16. Observability signals

A Domain Primitive is largely invisible at runtime in a healthy system, which
is itself the signal to look for. Its job is to make a category of failure
not happen, so the useful observability is around construction failures, not
around the type's ordinary operation.

- **Log and count construction failures at the boundary, with the specific
  rule that failed.** A rising rate of `EmailAddress` construction failures
  from one particular ingestion path is a leading indicator of an upstream
  data-quality regression, a partner API that changed its output format, a
  new client that skips its own validation, well before that bad data would
  otherwise surface as a downstream error.
- **Distinguish construction failures by source system or endpoint** in
  metrics or structured logs, not only by concept, since the same
  `EmailAddress` failure rate spiking from one specific batch import job
  versus spiking evenly across all ingestion paths points to very different
  root causes.
- **A healthy system shows construction failures clustering at the true
  system edges**, public API handlers, external message consumers, file
  importers, and essentially never occurring deep inside application or
  domain logic, because by that point every Domain Primitive already
  existing in memory is, by construction, valid. A construction failure
  observed deep inside business logic, rather than at an edge, is itself
  the signal that a boundary was skipped somewhere upstream, matching the
  trust-boundary-skipped failure mode from dimension 11.
- **Watch for an unusually high rate of the raw-accessor escape hatch being
  called**, if the codebase instruments it, as a leading indicator that the
  leaky-escape-hatch failure mode from dimension 11 is spreading rather than
  being contained to its original legitimate use.

## 17. Security and privacy implications

Security is the pattern's stated motivating concern, not an incidental
side effect. Deogun, Johnsson, and Sawano's central argument is that
injection attacks, business-logic bypasses, and a large share of data
corruption incidents share a single root cause, untyped or unvalidated
primitives crossing a trust boundary and being trusted downstream without
re-verification, and that Domain Primitives close this class of
vulnerability structurally rather than through code review vigilance alone
(Deogun, Johnsson, Sawano, *Secure by Design*, Manning, 2019, chapter 5,
sections 5.1 through 5.3). Concretely, a `SqlIdentifier` Domain Primitive
that only accepts a validated set of characters at construction, used
everywhere a column or table name is interpolated into a query, closes an
entire class of SQL injection risk at the type level rather than relying on
every call site individually remembering to escape or parameterize
correctly.

The pattern's privacy implication is more analytical than the security one.
A Domain Primitive that wraps personally identifiable data, an
`EmailAddress`, a `NationalIdNumber`, a `PhoneNumber`, is a natural single
place to attach handling policy, masking in logs, redaction in error
messages, encryption at rest, because every instance of that concept in the
codebase flows through the same type. Overriding the type's own `toString`
or logging representation to mask sensitive portions of the value, showing
`u***@example.com` rather than the full address in a log line, is a
practical, low-cost privacy control that becomes trivial to apply
consistently once the concept is centralized in one type, and easy to miss
entirely when the same value is scattered across the codebase as bare
strings.

## 18. References

- Daniel Deogun, Dan Bergh Johnsson, and Daniel Sawano, *Secure by Design*,
  Manning Publications, 2019, chapter 5, "Domain primitives."
- Eric Evans, *Domain-Driven Design. Tackling Complexity in the Heart of
  Software*, Addison-Wesley, 2003, chapter 5, "A Model Expressed in
  Software," "Value Objects," and chapter 9, "Specification."
- Martin Fowler, *Patterns of Enterprise Application Architecture*,
  Addison-Wesley, 2002, page 486, "Value Object," and page 488, "Money."
- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
  edition, Addison-Wesley, 2018, chapter 3, "Bad Smells in Code," "Primitive
  Obsession," and the "Replace Primitive with Object" catalog entry.
- Rust standard library, `std::net::Ipv4Addr`,
  https://doc.rust-lang.org/std/net/struct.Ipv4Addr.html, verified
  2026-08-02.
- Oracle, "Date Time," the Java Tutorials,
  https://docs.oracle.com/javase/tutorial/datetime/, verified 2026-08-02.
- JSR 310, Date and Time API specification, Java Community Process,
  https://jcp.org/en/jsr/detail?id=310, verified 2026-08-02.
- Stripe API reference, "Working with amounts," zero-decimal currencies,
  https://docs.stripe.com/currencies#zero-decimal, verified 2026-08-02.
- Kotlin standard library reference, "Duration,"
  https://kotlinlang.org/api/latest/jvm/stdlib/kotlin.time/-duration/,
  verified 2026-08-02.
- Wikipedia, "Value object," https://en.wikipedia.org/wiki/Value_object,
  verified 2026-08-02, used only as a cross-check of the Fowler and Evans
  framing, not as a primary source for any claim in this entry.

## Code examples

### TypeScript, a branded Domain Primitive with a smart constructor

TypeScript has no nominal typing, so this uses the branded-type idiom from
dimension 8, an intersection with a unique tag that only the module's own
constructor function can produce.

```typescript
type EmailAddress = string & { readonly __brand: "EmailAddress" };

type Result<T, E> =
  | { readonly ok: true; readonly value: T }
  | { readonly ok: false; readonly error: E };

const EMAIL_SHAPE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function makeEmailAddress(raw: string): Result<EmailAddress, string> {
  const trimmed = raw.trim().toLowerCase();
  if (trimmed.length === 0) {
    return { ok: false, error: "email must not be empty" };
  }
  if (!EMAIL_SHAPE.test(trimmed)) {
    return { ok: false, error: `not a valid email shape: ${raw}` };
  }
  return { ok: true, value: trimmed as EmailAddress };
}

function sendWelcome(to: EmailAddress): string {
  return `welcome message queued for ${to}`;
}

const parsed = makeEmailAddress("  User@Example.com  ");
if (parsed.ok) {
  console.log(sendWelcome(parsed.value));
} else {
  console.error(parsed.error);
}
```

### Python, a frozen dataclass Domain Primitive with post-init validation

```python
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class PositiveInt:
    value: int

    def __post_init__(self) -> None:
        if self.value <= 0:
            raise ValueError(f"PositiveInt must be > 0, got {self.value}")

    def __add__(self, other: "PositiveInt") -> "PositiveInt":
        return PositiveInt(self.value + other.value)

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class OrderQuantity:
    amount: PositiveInt

    @classmethod
    def of(cls, raw: int) -> "OrderQuantity":
        return cls(PositiveInt(raw))


def reorder(quantity: OrderQuantity) -> str:
    return f"reordering {quantity.amount} units"


if __name__ == "__main__":
    print(reorder(OrderQuantity.of(12)))
    try:
        OrderQuantity.of(-3)
    except ValueError as exc:
        print(f"rejected: {exc}")
```

### Rust, a zero-cost newtype Domain Primitive

```rust
use std::fmt;

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct EmailAddress(String);

impl EmailAddress {
    pub fn parse(raw: &str) -> Result<Self, String> {
        let trimmed = raw.trim().to_lowercase();
        if trimmed.is_empty() {
            return Err("email must not be empty".to_string());
        }
        if !trimmed.contains('@') || !trimmed.contains('.') {
            return Err(format!("not a valid email shape: {}", raw));
        }
        Ok(EmailAddress(trimmed))
    }
}

impl fmt::Display for EmailAddress {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.0)
    }
}

fn send_welcome(to: &EmailAddress) -> String {
    format!("welcome message queued for {}", to)
}

fn main() {
    match EmailAddress::parse("  User@Example.com  ") {
        Ok(email) => println!("{}", send_welcome(&email)),
        Err(e) => eprintln!("rejected: {}", e),
    }
    assert!(EmailAddress::parse("").is_err());
}
```

### Java, a validated Domain Primitive with a static factory

```java
import java.util.Objects;
import java.util.regex.Pattern;

public final class EmailAddress {
    private static final Pattern SHAPE = Pattern.compile("^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$");
    private final String value;

    private EmailAddress(String value) {
        this.value = value;
    }

    public static EmailAddress of(String raw) {
        if (raw == null) {
            throw new IllegalArgumentException("email must not be null");
        }
        String trimmed = raw.trim().toLowerCase();
        if (trimmed.isEmpty()) {
            throw new IllegalArgumentException("email must not be empty");
        }
        if (!SHAPE.matcher(trimmed).matches()) {
            throw new IllegalArgumentException("not a valid email shape: " + raw);
        }
        return new EmailAddress(trimmed);
    }

    @Override
    public String toString() {
        return value;
    }

    @Override
    public boolean equals(Object other) {
        if (this == other) return true;
        if (!(other instanceof EmailAddress that)) return false;
        return value.equals(that.value);
    }

    @Override
    public int hashCode() {
        return Objects.hash(value);
    }

    public static void main(String[] args) {
        EmailAddress a = EmailAddress.of("  User@Example.com  ");
        System.out.println("welcome message queued for " + a);
        try {
            EmailAddress.of("not-an-email");
        } catch (IllegalArgumentException e) {
            System.out.println("rejected: " + e.getMessage());
        }
    }
}
```

### Go, a validated Domain Primitive without generics or classical inheritance

Go has no classes and no constructors in the classical sense, so the idiomatic
shape is an unexported struct field plus an exported constructor function that
is the only way to obtain a valid instance from outside the package.

```go
package main

import (
	"errors"
	"fmt"
	"regexp"
	"strings"
)

var emailShape = regexp.MustCompile(`^[^\s@]+@[^\s@]+\.[^\s@]+$`)

type EmailAddress struct {
	value string
}

func NewEmailAddress(raw string) (EmailAddress, error) {
	trimmed := strings.ToLower(strings.TrimSpace(raw))
	if trimmed == "" {
		return EmailAddress{}, errors.New("email must not be empty")
	}
	if !emailShape.MatchString(trimmed) {
		return EmailAddress{}, fmt.Errorf("not a valid email shape: %s", raw)
	}
	return EmailAddress{value: trimmed}, nil
}

func (e EmailAddress) String() string {
	return e.value
}

func sendWelcome(to EmailAddress) string {
	return fmt.Sprintf("welcome message queued for %s", to)
}

func main() {
	addr, err := NewEmailAddress("  User@Example.com  ")
	if err != nil {
		fmt.Println("rejected:", err)
		return
	}
	fmt.Println(sendWelcome(addr))

	if _, err := NewEmailAddress(""); err != nil {
		fmt.Println("rejected:", err)
	}
}
```

Swift and Kotlin were not written for this entry. Both languages support the
pattern natively and idiomatically, Swift via a struct with a failable
initializer and Kotlin via an inline value class, and neither adds a distinct
implementation concern beyond what the Rust newtype and Java static factory
examples already demonstrate. This entry omits them to keep the runnable set
focused on the languages where the toolchain was verified available in this
environment.
