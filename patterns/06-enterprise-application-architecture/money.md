---
name: Money
slug: money
family: 06-enterprise-application-architecture
category: Base Pattern
aliases: [Monetary Value Object, Amount and Currency, Cents Pattern]
first_described: "Fowler 2002"
maturity: canonical
related: [value-object, embedded-value, active-record, data-transfer-object, specification]
incompatible_with: []
verified: 2026-08-02
---

# Money

## 1. Name, aliases, and lineage

The canonical name is Money, catalogued as a Base Pattern in Martin Fowler,
*Patterns of Enterprise Application Architecture*, Addison-Wesley, 2002,
chapter 18. Fowler's own summary of the pattern, published on his companion
site, opens with the intent stated plainly. "Represents a monetary value"
([Martin Fowler, Money pattern catalog page](https://martinfowler.com/eaaCatalog/money.html),
verified 2026-08-02). That page points the reader to chapter 18 of the book for
the full write-up, and it explicitly stops short of describing the allocation
algorithm on the web page itself, reserving the mechanical detail for the book.

Practitioners refer to the same idea under several working names, none of them
formal aliases from a second catalog the way GoF patterns often accumulate
Smalltalk-era synonyms. "Monetary Value Object" is the description used when a
team wants to stress that Money is one specific application of the broader
Value Object pattern (see dimension 13), and it is common in domain-driven
design vocabulary. "Amount and Currency" is a descriptive label used in API
design discussions, naming the two fields the type wraps rather than the type
itself. "Cents Pattern" is informal engineering slang for the narrower
practice of storing the amount as an integer count of the smallest currency
unit, which is the representation strategy Money almost always uses but which
is, strictly, an implementation choice inside the pattern rather than the
pattern's full definition.

Money predates its formal write-up as a named enterprise pattern. The problem
it solves, a language's numeric primitives being unsuited to currency
arithmetic, is old enough that most general-purpose object-oriented languages
ship no monetary type in their standard library at all. What Fowler's catalog
entry did was give the recurring fix a name and place it in a shared
vocabulary next to other Base Patterns such as Value Object, Special Case, and
Layer Supertype, so that a team could say "this needs a Money" and be
understood without re-deriving the design from scratch. This entry treats
Fowler's 2002 catalog description as the canonical reference point and does
not assert an earlier named source, because no earlier formal publication
under the name Money could be verified for this entry.

## 2. Problem and context

A system that touches prices, balances, fees, taxes, discounts, refunds, or
payroll needs to represent a quantity of currency and do arithmetic on it. The
obvious first move in most codebases is to reach for the language's built-in
floating point type, a `double` or a `float`, because it already knows how to
add, subtract, multiply, and print a number with a decimal point.

That obvious move is wrong for two independent reasons, and both reasons show
up eventually in every codebase that makes it.

The first reason is representation. IEEE 754 binary floating point cannot
represent most decimal fractions exactly, because the format is base two and a
value like 0.10 has no finite binary expansion. Ten cents stored as a `double`
is actually stored as the nearest representable binary approximation of 0.10,
and repeated addition of that approximation accumulates error. The classic
demonstration, reproducible in any language with IEEE 754 floats, is that
`0.1 + 0.2` does not equal `0.3` bit for bit. In a shopping cart that sums line
items across thousands of orders a day, that drift is not cosmetic, it is
pennies that silently vanish or silently appear, and it does not average out
to zero because rounding at output time is itself biased by whatever rounding
mode the runtime happens to use. The PostgreSQL project states the underlying
reason directly in its own type documentation. "If you require exact storage
and calculations (such as for monetary amounts), use the `numeric` type
instead" of a floating point type, because `real` and `double precision` are
"inexact, variable-precision numeric types" whose values are frequently stored
only as approximations
([PostgreSQL 17 Documentation, section 8.1.3, Floating-Point Types](https://www.postgresql.org/docs/current/datatype-numeric.html),
verified 2026-08-02).

The second reason is meaning. A raw number, whether it is a float, a decimal,
or an integer, does not say what currency it is denominated in. A ledger that
stores a column of numbers labelled "amount" and a separate column labelled
"currency code" can be added across rows without the compiler, the type
checker, or the database noticing that ten euros plus ten dollars is not
twenty of anything. Fowler frames this half of the problem the same way. "If
all your calculations are done in a single currency, this isn't a huge
problem, but once you involve multiple currencies you want to avoid adding
your dollars to your yen without taking the currency differences into account"
([Martin Fowler, Money pattern catalog page](https://martinfowler.com/eaaCatalog/money.html),
verified 2026-08-02). A single-currency system that never expects to expand
can defer this half of the problem, but the moment a second currency enters
the picture, whether through internationalisation, a foreign supplier, or a
multi-currency wallet, an unlabelled number becomes a correctness bug waiting
for a customer to notice it in their statement.

The context in which Money earns its place has three concrete markers, and a
reader can check for all three in an existing codebase without knowing the
pattern's name in advance. There are arithmetic operations on prices, totals,
fees, or balances scattered across more than one class or module. There is, or
will plausibly be, more than one currency in play, whether concurrently
(a marketplace paying suppliers in several currencies) or sequentially (a
product that starts in one market and expands). And there is a real
regulatory or reputational cost to a rounding discrepancy, which is the case
for essentially every system that touches an invoice, a payslip, a tax
calculation, or a customer-facing balance.

## 3. Forces

- **Correctness of arithmetic.** Favoured, and the pattern's entire reason for
  existing. Money forces every addition, subtraction, and allocation to go
  through code that knows the base-two floating point trap and avoids it by
  construction, as a rule by never letting a fractional cent exist as a stored
  value.
- **Currency safety.** Favoured. A Money value carries its currency alongside
  its amount, so an attempt to add two Money values in different currencies is
  a programming error the type system, or at minimum a runtime guard inside
  the type, can catch at the point of the mistake rather than three reports
  downstream in a reconciliation job.
- **Precision versus storage cost.** In tension. Storing an integer count of
  minor units (cents, pence, ore) is cheap, exact for addition and subtraction,
  and matches how payment networks and card processors already represent
  amounts, but it pushes multiplication and division into explicit rounding
  decisions the caller must make deliberately rather than by accident.
- **Ergonomics versus safety.** In tension. A Money type that overloads
  arithmetic operators reads naturally in calling code, `total = total.add(item.price)`
  or `total + item.price` in languages that support operator overloading, but
  the moment a caller needs a percentage discount or a currency conversion,
  the ergonomic operator syntax has to yield to an explicit, harder-to-misuse
  method, because multiplying money by a ratio and rounding is exactly the
  step where silent precision loss re-enters if the API is careless.
- **Fairness of allocation.** Sacrificed by naive rounding, deliberately
  recovered by Money's allocation algorithm (dimension 8). Splitting a stored
  monetary total into shares by simple division and truncation systematically
  loses pennies; a correct allocation must distribute the leftover minor units
  somewhere, and deciding where is itself a policy choice with fairness
  implications for whoever receives, or does not receive, the extra penny.
- **Interoperability with external systems.** A pull toward the pattern.
  Payment processors, banking rails, and accounting systems standardise on
  integer minor units and ISO currency codes at their boundary, so a Money
  type that mirrors that representation internally reduces the translation
  work at every integration point rather than concentrating unit-conversion
  bugs at each boundary crossing.
- **Team unfamiliarity and mixed adoption.** Sacrificed. Introducing Money
  part way through a codebase that has used raw numeric types for years means
  every boundary between "already migrated" and "not yet migrated" code is a
  place where a Money value gets unwrapped into a float or a float gets
  wrapped into a Money value without validation, and both directions can
  silently reintroduce the exact bug the pattern exists to remove.

## 4. Applicability and non-applicability

Reach for Money when any of the following hold.

- The system performs more than an isolated, one-off arithmetic operation on
  currency values, across more than a single function or a single screen.
- More than one currency exists in the domain, now or as a realistic
  near-term expansion, including a system that reports revenue in a reporting
  currency different from the transaction currency.
- Amounts must be split among parties, taxed, discounted, or otherwise divided
  in a way that can produce a fractional minor unit that has to go somewhere.
- The system persists financial values that will be reconciled against an
  external statement, invoice, or bank record, where a rounding discrepancy of
  even one cent is a defect that a human or an automated reconciliation job
  will surface.
- The codebase already has, or is accumulating, more than one place that
  formats, parses, or compares currency amounts, which is a sign that the
  currency-and-amount pairing deserves to be a first-class type rather than a
  convention repeated at each call site.

Do not reach for Money in the following situations, and treat each as a
genuine reason rather than a shortcut.

- **A single, isolated numeric quantity that is not currency**, such as a
  weight, a temperature, a percentage, or a count. Money is specifically about
  currency-denominated amounts; applying its machinery, and especially its
  currency-mismatch guard, to a quantity that has no currency is a category
  error that adds ceremony without adding safety.
- **A prototype or a genuinely single-use script** whose output nobody will
  reconcile against a real financial record, where introducing a full Money
  type and its supporting currency table is more setup cost than the task
  will ever repay. A one-off script that sums a CSV of already-cent-precise
  integers for a throwaway report does not need a Money class; it needs to
  avoid floating point, which integer arithmetic alone already achieves.
- **A system whose currency values are always sourced from and immediately
  handed back to an external system without any local arithmetic**, for
  example a thin proxy that only forwards an opaque amount string to a
  downstream payment API and never adds, compares, or displays it. There is
  nothing for Money's arithmetic safety to protect if no arithmetic happens.
- **A domain where "money" is not really currency at all**, such as an
  internal points or credits system with no real-world exchange rate and no
  regulatory reporting obligation. Such a system may still benefit from an
  integer-based Value Object for the same representation reasons, but calling
  it Money and wiring in ISO currency codes and allocation semantics designed
  for real-world currency is unwarranted extra design weight for a domain
  that does not have the multi-currency problem Money exists to solve.
- **A high-frequency numerical or scientific computation path** where the
  values being manipulated are not discrete monetary amounts but continuous
  quantities such as interest-rate curves, option-pricing models, or Monte
  Carlo simulation intermediates. Those domains have their own numerical
  stability concerns, use floating point deliberately for its dynamic range,
  and as a rule convert to a Money-shaped exact value only at the point where
  a result is booked to a ledger, not throughout the computation.

## 5. Structure

Money's structure is intentionally small, and the smallness is part of the
design. The pattern names three participants.

- **Amount.** The numeric quantity, represented so that it cannot silently
  lose precision. The two representation strategies in real use are an integer
  count of the currency's smallest unit (an `int64` or arbitrary-precision
  integer number of cents, pence, or the equivalent) and a fixed-point decimal
  type with a defined scale (a `BigDecimal` with `RoundingMode` fixed at
  construction, or a language-native decimal type). Both strategies exclude
  binary floating point from the representation entirely.
- **Currency.** An identifier for which currency the amount is denominated in,
  almost always an ISO 4217 three-letter alphabetic code together with the
  minor-unit exponent that code implies. ISO 4217 "defines alpha codes and
  numeric codes for the representation of currencies" and "provides
  information about the relationships between currencies and their minor
  units," recording, for example, that most currencies use two decimal
  places, the Japanese yen and several others use zero, and a handful,
  including the Bahraini dinar and the Kuwaiti dinar, use three
  ([Wikipedia, ISO 4217](https://en.wikipedia.org/wiki/ISO_4217), verified
  2026-08-02). The Currency participant is what makes the mismatch guard in
  dimension 8 possible, because every arithmetic operation can compare the
  currency of its operands before touching the amount.
- **Money itself.** The immutable value type that pairs an Amount with a
  Currency and exposes the operations a caller needs, addition, subtraction,
  comparison, multiplication by a scalar with an explicit rounding rule, and
  allocation across a set of ratios. Money is immutable in every mainstream
  implementation this entry could verify; every operation returns a new Money
  rather than mutating the receiver, which is the same immutability
  discipline the broader Value Object pattern requires (see dimension 13).

A fourth, optional participant appears in systems that convert between
currencies. a **Currency Exchange Rate** or **Converter**, which supplies the
ratio used to translate an amount in one currency into an amount in another at
a stated point in time. Fowler's catalog treats conversion as a related but
separate concern from the core Money type, and this entry follows that
separation, because a conversion rate is time-varying and externally sourced
in a way that the Amount and Currency of a single Money value are not.

## 6. ASCII structure diagram

```
+--------------------------------------------------+
|                       Money                       |
+--------------------------------------------------+
| - amountMinorUnits: int64 (or fixed-scale decimal)|
| - currency: Currency                              |
+--------------------------------------------------+
| + add(other: Money): Money                        |
| + subtract(other: Money): Money                    |
| + multiply(ratio, RoundingMode): Money             |
| + allocate(ratios: int[]): Money[]                 |
| + compareTo(other: Money): int                     |
| + isZero(), isPositive(), isNegative(): bool       |
+--------------------------------------------------+
                 |  denominated in
                 v
        +-------------------+
        |     Currency       |
        +-------------------+
        | - isoCode: String  |   e.g. "USD", "JPY", "BHD"
        | - minorUnitExponent |   e.g. 2, 0, 3
        +-------------------+

  optional, external to Money itself:

        +---------------------------+
        |   CurrencyExchangeRate    |
        +---------------------------+
        | - from: Currency          |
        | - to: Currency             |
        | - rate: decimal            |
        | - asOf: timestamp          |
        +---------------------------+
        | + convert(m: Money): Money |
        +---------------------------+
```

## 7. Dynamics

Two runtime flows matter most in practice. a same-currency arithmetic
operation, where the currency guard is the whole story, and an allocation,
where the rounding remainder has to go somewhere fair.

```
Same-currency addition, guarded
--------------------------------
caller               Money(a)              Money(b)
  |  add(b) ------------->  |                       |
  |                          |-- a.currency == b.currency? --|
  |                          |            yes                 |
  |                          |-- amountMinorUnits(a) + (b) -->|
  |  <---- new Money(sum, a.currency) ------------------------|
  |

Mismatched-currency addition, rejected
---------------------------------------
caller               Money(USD 10.00)      Money(EUR 10.00)
  |  add(eurAmount) --------->  |                     |
  |                              |-- currency mismatch |
  |  <---- throws / returns Result::Err ---------------|
  |  (never silently coerces or truncates one currency)

Allocation of a stored total across N shares (largest-remainder rounding)
---------------------------------------------------------------------------
caller           Money(total)                    allocate([ratio1..ratioN])
  |  allocate(ratios) ---------->  |                                       |
  |                                 |-- for each i. base[i] = int div(     |
  |                                 |      total * ratio[i] / sum(ratios)) |
  |                                 |-- remainder = total - sum(base)      |
  |                                 |-- sort indices by descending         |
  |                                 |   fractional part of the unrounded   |
  |                                 |   share                              |
  |                                 |-- distribute 1 minor unit to each of |
  |                                 |   the top remainder indices          |
  |  <---- Money[] shares, sum(shares) == total ---------------------------|
```

The allocation flow is the dynamic that most catalog descriptions of Money
gloss over or omit; Fowler's own web summary of the pattern does not spell out
the algorithm and points the reader to the book instead
([Martin Fowler, Money pattern catalog page](https://martinfowler.com/eaaCatalog/money.html),
verified 2026-08-02). The important invariant, stated explicitly because it is
easy to lose sight of while implementing the loop, is that the sum of the
allocated shares must equal the original total exactly, to the last minor
unit, every time. Any implementation that allocates by naive division and
truncation of each share independently will violate that invariant whenever
the total does not divide evenly by the ratio sum, and the missing minor units
disappear from the ledger.

## 8. Implementation variants

**Integer minor units.** The amount is stored as a signed integer count of the
smallest denomination the currency defines, ten dollars stored as the integer
`1000` alongside the currency `USD` with a known exponent of two. Addition and
subtraction are then ordinary integer arithmetic, which is exact by
construction and cannot introduce rounding error on its own. This is the
representation the payment industry itself uses at its API boundary; Stripe's
documentation states plainly that "all API requests expect amounts to be
provided in a currency's smallest unit" and gives the concrete example that a
value of `1000` charges ten units of a two-decimal currency such as USD, while
a value of `10` charges ten units of a zero-decimal currency such as JPY
([Stripe, Supported currencies](https://docs.stripe.com/currencies), verified
2026-08-02). An integer-minor-unit Money type that mirrors this convention
minimises the translation code needed at every payment integration boundary,
because the internal representation already matches the external contract.
The variant's weakness is that it needs an explicit, currency-aware exponent
lookup at every point where a human-readable decimal value crosses the
boundary, both on input (parsing "$10.00" into the integer `1000`) and on
output (formatting the integer `1000` back into "$10.00"), and a bug in that
lookup for a non-two-decimal currency, most commonly the Japanese yen or a
three-decimal currency such as the Bahraini dinar, silently produces an amount
that is one hundred or one thousand times too large or too small.

**Fixed-scale decimal.** The amount is stored using a language's
arbitrary-precision or fixed-point decimal type, `BigDecimal` in Java or C#,
`Decimal` in Python, with the scale fixed to the currency's minor-unit
exponent and every arithmetic operation carrying an explicit `RoundingMode`.
This variant reads more naturally in code that also needs to display or
compute with sub-cent intermediate precision, for example a tax calculation
that computes a rate against a large base before rounding down to the minor
unit at the end. Its weakness is that decimal types in most languages are
mutable-feeling in API shape even when the underlying value is immutable, and
a careless caller can construct a `BigDecimal` with the wrong scale or
rounding mode and never notice until a downstream comparison against a
minor-unit integer fails.

**Value Object library, borrowed rather than hand-rolled.** Several mature,
narrowly-scoped libraries exist specifically to be the Money type a team does
not have to design from scratch. Joda-Money is one such library for the JVM,
and its own documentation frames its scope deliberately narrowly. it states
that it provides "a library of classes to store amounts of money" through
three types, `CurrencyUnit`, a fixed-precision `Money`, and a variable-
precision `BigMoney`, while explicitly declining to implement broader
financial algorithms because "the requirements for these algorithms vary
widely between domains," positioning itself as "the base layer, providing
classes that should be in the JDK" rather than a full accounting engine
([Joda-Money, project home page](https://www.joda.org/joda-money/), verified
2026-08-02). JSR 354, the Java Money and Currency API, formalises the same
idea as a language-level specification rather than a single library, offering
"a portable and extensible API for handling of Money and Currency models,"
with Moneta as its reference implementation
([JavaMoney, JSR 354 project site](https://javamoney.github.io/), verified
2026-08-02). Choosing a library variant over a hand-rolled Money class trades
a small dependency for avoiding the accumulation of small, independently
introduced bugs that tend to appear across several hand-rolled
implementations inside one organisation over time.

**Language-idiomatic variants.** In languages with strong value-type support
and operator overloading, Money is commonly implemented as a struct or a
record with overloaded arithmetic operators, so that `price + tax` reads as
ordinary arithmetic while the compiler still enforces immutability and, where
the language supports it, the currency-mismatch guard is expressed as a
runtime check inside the overloaded operator rather than as a separately
named method. In languages without operator overloading, the same design
degrades gracefully to named methods, `price.add(tax)`, without losing any of
the safety properties, only the syntactic convenience.

## 9. Known production uses

- **Stripe's Payment Intents and Charges APIs** represent every monetary
  amount as an integer in the currency's smallest unit at the API boundary,
  explicitly to avoid the ambiguity and rounding risk of decimal amounts
  crossing a JSON API. The documentation states this as a hard rule for every
  request. "Enter 1099 to charge 10.99 USD... Enter 10 to charge 10 JPY," and
  separately enumerates the zero-decimal currencies for which the amount and
  the smallest-unit value are identical
  ([Stripe, Supported currencies](https://docs.stripe.com/currencies),
  verified 2026-08-02). This is the integer-minor-unit variant from dimension
  8, applied at true internet payment-processing scale.
- **Joda-Money**, the widely used JVM library described above, ships exactly
  the Amount-and-Currency structure this pattern describes as three public
  types, `CurrencyUnit`, `Money`, and `BigMoney`, and is packaged and consumed
  as a dependency by other JVM projects rather than being reimplemented per
  project ([Joda-Money, project home page](https://www.joda.org/joda-money/),
  verified 2026-08-02).
- **JSR 354, the Money and Currency API for the Java Platform**, standardises
  the same shape at the language-specification level rather than the single-
  library level, with `Moneta` as its stable reference
  implementation, so that a monetary type with this pattern's structure is
  available as a portable contract across independently written Java
  libraries rather than as one vendor's private class hierarchy
  ([JavaMoney, JSR 354 project site](https://javamoney.github.io/), verified
  2026-08-02).
- **PostgreSQL's `numeric` type as the documented, official recommendation for
  monetary storage.** While `numeric` is a general exact-arithmetic type
  rather than a Money type specifically, the PostgreSQL project's own
  documentation names monetary amounts as the leading example of a value that
  must use `numeric` instead of a floating point column, precisely because
  "some values cannot be converted exactly to the internal format" of `real`
  or `double precision`
  ([PostgreSQL 17 Documentation, section 8.1.3](https://www.postgresql.org/docs/current/datatype-numeric.html),
  verified 2026-08-02). Systems built on PostgreSQL that implement a Money
  pattern in application code back that type with a `numeric` column at the
  storage layer specifically because of this documented guidance, keeping the
  exactness Money's arithmetic promises intact all the way to disk.

## 10. Consequences

Positive.

- Arithmetic on monetary values becomes exact by construction, because the
  representation excludes binary floating point entirely, eliminating an
  entire class of drift bugs that would otherwise surface unpredictably and
  intermittently, often long after the code that caused them shipped.
- Currency mismatches become a caught error at the point of the mistaken
  operation rather than a silent miscalculation discovered during
  reconciliation, moving the cost of the bug from a customer-facing incident
  to a failed unit test or a caught exception in development.
- Formatting, parsing, comparison, and allocation logic are centralised in one
  type rather than duplicated, with subtly different bugs, at every call site
  that touches a price or a balance.
- The type becomes a natural place to attach currency-aware business rules,
  such as minimum chargeable amounts per currency or per-currency rounding
  conventions, that would otherwise be scattered as magic numbers across the
  codebase.

Negative.

- Every numeric literal and every external input that represents a price now
  has to pass through explicit construction and parsing rather than an
  implicit numeric conversion, which is a real increase in code volume at
  every boundary, particularly in a large codebase migrated from raw numeric
  types incrementally.
- A poorly designed Money type can become a leaky abstraction if it exposes
  its internal representation, for example a public getter that returns the
  raw minor-unit integer without the caller also having to acknowledge the
  currency, which reintroduces the exact currency-blindness bug the pattern
  exists to prevent.
- Multiplication by a non-integer ratio, most commonly applying a percentage
  discount or a tax rate, forces an explicit rounding decision at the call
  site every single time, which is more code than an implicit float multiply
  but is also the exact point where the pattern's safety guarantee actually
  does its work; treating this as pure overhead misunderstands what the
  overhead buys.
- Serialisation across a system boundary, to JSON, to a database column, or to
  a message queue payload, has to carry both the amount and the currency
  together and be interpreted consistently on both ends, which is an
  additional coordination cost compared to serialising a bare number.

## 11. Failure modes and misuse

**Symptom.** A shopping cart or invoice total is off by one or two cents from
the sum a customer computes by hand, intermittently and not on every order.
**Cause.** The Money type, or the code around it, still performs an
intermediate calculation, most often a percentage discount or a per-unit tax,
using a binary floating point type before converting the result into the
Money type, so the floating point drift happens upstream of the type that was
supposed to prevent it. **Fix.** Push the Money type's construction to the
earliest possible point, ideally at parse time from the request or the price
catalog, and perform every subsequent operation, including percentage
calculations, using the Money type's own rounding-aware methods rather than
converting to a float for the calculation and back.

**Symptom.** An allocation of a stored total across line items, invoice
splits, or payroll deductions sums to one or two cents less than the original
total when the individual shares are added back up. **Cause.** The allocation
was implemented as independent division and truncation of each share, rather
than the largest-remainder distribution described in dimension 7, so the
truncated fractional cents from each share are simply discarded instead of
being redistributed. **Fix.** Replace the per-share truncation with an
allocation method that computes the remainder explicitly and distributes it
one minor unit at a time to the shares with the largest truncated remainder,
verified by a test asserting that the sum of the returned shares equals the
original total for every ratio combination the domain can produce.

**Symptom.** A currency-mismatch bug reaches production despite the Money
type having a guard for it, usually surfacing as a customer statement that
mixes currencies in a way support cannot explain from the application logs
alone. **Cause.** A boundary in the codebase, commonly a legacy module that
predates the Money type's introduction, still passes a raw numeric amount
without a currency, and a later adapter wraps that raw number into a Money
value using an assumed default currency rather than the currency actually
associated with the transaction. **Fix.** Audit every construction site of the
Money type for an assumed or defaulted currency argument, and change any
default-currency construction path to require the currency explicitly, even
in single-currency systems, so that expanding to a second currency later
cannot silently reuse a wrong default.

**Symptom.** A report that aggregates amounts across currencies, for example a
dashboard total of revenue from customers in different countries, shows a
number that is technically the sum of the stored figures but is meaningless
as a business quantity. **Cause.** Someone unwrapped several Money values to
their raw amount and summed the raw numbers directly, bypassing the type's
currency guard entirely by reaching for the underlying primitive instead of
the type's own `add` method, which is possible whenever the Money type exposes
its raw amount as a public accessor with no accompanying warning. **Fix.**
Route every cross-currency aggregation through an explicit, named conversion
step that produces a single reporting currency using a stated exchange rate
and timestamp, and audit the codebase for any place that reads the raw amount
field of a Money value outside the type's own implementation.

**Symptom.** A monetary amount displayed to a user in Japan or another
zero-decimal currency shows a value one hundred times too large or too small,
while the same code path is correct for two-decimal currencies. **Cause.**
The formatting or parsing logic hardcodes a two-decimal assumption, dividing
or multiplying by one hundred without checking the currency, instead of looking up the
currency's actual minor-unit exponent, which ISO 4217 defines per currency
and which is zero for the Japanese yen and several other currencies rather
than the two decimal places that hold for most of the currencies a
Western-market engineering team encounters first
([Wikipedia, ISO 4217](https://en.wikipedia.org/wiki/ISO_4217), verified
2026-08-02). **Fix.** Replace the hardcoded scale factor with a lookup against
the Currency participant's stored exponent for every format and parse
operation, and add a regression test that exercises at least one zero-decimal
currency and one three-decimal currency alongside the default two-decimal
case.

## 12. Trade-off matrix

| Concern | Money | Raw float/double | Raw decimal, no currency field |
|---|---|---|---|
| Exact arithmetic | Yes, by construction | No, IEEE 754 rounding drift | Yes, for the amount alone |
| Currency-mismatch detection | Caught at the operation | Not possible, no currency concept | Not possible, currency lives elsewhere |
| Fair remainder allocation | Explicit, testable method | Left to ad hoc code at each call site | Left to ad hoc code at each call site |
| Boundary interop with payment APIs | Matches integer-minor-unit convention directly | Requires ad hoc conversion, error-prone | Requires currency to be threaded through separately |
| Call-site verbosity | Higher, explicit construction and methods | Lower, implicit numeric literals | Medium, decimal literals still implicit currency |
| Risk of silent currency-blind aggregation | Prevented by the type, if raw accessors are not exposed | Structural, cannot be prevented by the type system | Structural, the amount alone carries no currency |
| Fit for a single-currency, low-stakes prototype | Overkill | Adequate short term, risky if it grows | Adequate, cheaper setup than Money |

The comparison against Value Object generally, rather than raw numeric types,
is a different axis and is covered in dimension 13, because Money is not an
alternative to Value Object, it is Value Object specialised to currency.

## 13. Related and incompatible patterns

**Value Object.** Money is the textbook example of a Value Object applied to a
specific domain concept, currency amounts, and every property Value Object
requires, immutability, equality by value rather than identity, and no
independent lifecycle, applies to Money without modification
(see [Value Object](../11-domain-driven-design/value-object.md)). A team that
already has a general Value Object convention in its codebase should implement
Money as an instance of that convention rather than as a special case with its
own separate rules.

**Embedded Value.** When a Money value is persisted, the two fields it
carries, amount and currency, are almost always stored as two columns on the
owning row's table rather than as a foreign key to a separate table, which is
exactly the object-relational mapping pattern Embedded Value describes (see
[Embedded Value](embedded-value.md)). Money is frequently the worked example
used to introduce Embedded Value in the first place, because the two-field,
no-independent-identity shape of a currency amount is such a clean fit for
that mapping technique.

**Active Record and Data Mapper.** Money composes with either persistence
pattern without conflict; whichever technique an entity uses to load and save
itself, a Money-valued field on that entity is mapped using Embedded Value as
described above, and neither Active Record's self-persisting style nor Data
Mapper's separation of domain object from persistence logic changes how Money
itself behaves (see
[Data Transfer Object](data-transfer-object.md) for the related concern of how
Money crosses a process or API boundary, commonly serialised as an amount
string or integer alongside an explicit currency code field, mirroring the
same two-field shape at the wire level that Embedded Value uses at the storage
level).

**Specification.** A business rule that depends on a monetary threshold, for
example "eligible for free shipping if the order total exceeds fifty euros,"
is naturally expressed as a Specification object that takes a Money value as
input and returns a boolean, keeping the comparison logic, including the
currency check, out of the calling code (see
[Specification](../11-domain-driven-design/specification.md)).

**Incompatibilities.** Money is not incompatible with any other cataloged
pattern in a structural sense, but it is functionally redundant with, and
should not be combined with, a parallel ad hoc currency-handling convention
in the same codebase, such as a set of free functions that also format and
compare raw numeric amounts alongside a separately maintained currency
string. Running both approaches side by side in the same system reintroduces
the exact currency-blindness and rounding risk Money exists to close, at
whichever boundary the two conventions meet.

## 14. Refactoring path in and out

**Introducing Money into existing code.** Start at the boundary where
currency values enter the system, request parsing, price catalog loading, or
a payment webhook, and wrap the raw numeric value into a Money instance as
early as possible, rather than starting from the arithmetic in the middle of
the codebase. Once construction is wrapped, replace one arithmetic call site
at a time, converting a raw-float addition into a Money `add` call and running
the existing test suite after each change, so that any newly introduced
currency-mismatch error surfaces immediately as a caught exception rather than
as a silent behaviour change. Leave the raw numeric type in place at
downstream consumers until each one has been migrated in turn; a temporary
accessor that exposes the raw amount for not-yet-migrated callers is
acceptable as a transitional measure, provided it is clearly marked and
tracked for removal, because the goal state has no code path that reads a
Money value's amount without also handling its currency. This is close to the
general shape of Fowler's own refactoring vocabulary for introducing a Value
Object around a primitive, applied here to the specific case of an amount and
a currency travelling together.

**Removing Money, when the pattern has stopped earning its place.** This is
rare in practice, because the conditions that justify Money, multi-currency
risk and rounding-sensitive arithmetic, tend to persist or grow rather than
disappear once a system reaches production. The one legitimate removal path
is collapsing Money back to a bare integer minor-unit column when a bounded
subsystem is provably and permanently single-currency and never performs
allocation, for example an internal metering counter that happens to be
denominated in a currency for historical reasons but will never be compared
against, added to, or converted from another currency. Even then, the safer
move is usually to keep the Money type as the field's declared type at the
subsystem's public interface and let its internal implementation be a thin
wrapper over the integer, so that the removal is invisible to any caller and
reversible without a second migration if the assumption of permanence turns
out to be wrong.

## 15. Testing and verification

Testing Money-typed code is, in one specific and important sense, easier than
testing raw numeric arithmetic, because the invariant a test needs to check is
exact equality rather than equality within a floating point epsilon; a correct
Money implementation never needs an approximate-equality assertion in a test
suite, and the presence of one in code that touches Money is itself a signal
that something upstream still leaks a floating point value into the type.

The properties worth testing directly, beyond ordinary unit coverage of each
method, are the following. First, that addition and subtraction of same-
currency Money values are exact for values that are adversarial to binary
floating point, such as repeated additions of amounts like 0.10 and 0.20 that
famously fail to sum cleanly under IEEE 754; a Money implementation should
pass a test that performs such a sum a large number of times and asserts the
exact expected total. Second, that any operation combining two Money values in
different currencies fails loudly, whether by exception or by a typed error
result, rather than by silently choosing one currency or coercing one amount;
this is best tested as a dedicated negative test per public arithmetic method
rather than assumed to be covered incidentally by other tests. Third, that
allocation is total-preserving, expressed as a property-based test that
generates a random total and a random set of positive integer ratios and
asserts that the sum of the returned shares equals the original total exactly,
for every generated case rather than a handful of hand-picked examples, since
the largest-remainder algorithm's correctness is precisely the kind of
property that a small set of example-based tests can pass while still hiding
an off-by-one bug in the remainder distribution loop. Fourth, that formatting
and parsing round-trip correctly for at least one zero-decimal currency and
one three-decimal currency in addition to the common two-decimal case, since
the failure mode in dimension 11 involving a hardcoded decimal-place
assumption is specifically invisible to a test suite that only ever exercises
two-decimal currencies.

Money's immutability also simplifies test setup in a way worth calling out
explicitly. because every operation returns a new value rather than mutating
its receiver, tests can freely reuse a single constructed Money instance as a
fixture across many test cases without any risk of one test's mutation
leaking into another test's assertions, a class of test-isolation bug that is
common with mutable value-holding objects and impossible by construction with a
correctly implemented Money type.

## 16. Observability signals

The signal most worth tracking in a running system is a reconciliation
mismatch, the gap between a sum computed from Money-typed values inside the
application and the corresponding total reported by an external source of
truth, most commonly a payment processor's settlement report or a bank
statement. A healthy Money implementation produces a mismatch count of exactly
zero across a reconciliation window; any non-zero count is not noise to be
smoothed over statistically, it is evidence that a specific transaction's
arithmetic path bypassed the type's guarantees somewhere, and each occurrence
is worth tracing to its originating code path individually rather than
aggregated away.

A second useful signal is a count of caught currency-mismatch errors at
runtime, distinct from a test-time assertion. In a well-migrated codebase this
count should also sit at or near zero in steady state; a nonzero and
persistent rate indicates either a genuine latent bug at a specific call site
or, in a system mid-migration, a boundary that has not yet been converted to
construct Money values with the correct currency and is instead falling back
to a default that occasionally does not match the transaction's actual
currency.

A third signal, useful specifically during and after an allocation-heavy
operation such as a payroll run or a multi-party payout split, is an
assertion, ideally enforced in code rather than only observed, that the sum of
every batch of allocated shares equals the pre-allocation total for that
batch; logging and alerting on any batch where that equality does not hold
turns the invariant from dimension 7 into an operational guarantee rather than
a property that only unit tests check.

Finally, for a system spanning multiple currencies, tracking the age of the
exchange rate used in any cross-currency conversion or reporting rollup is
worth surfacing as a dashboard metric, because a stale rate silently used past
its intended validity window produces figures that are internally consistent,
in the sense that no exception fires and no reconciliation mismatch appears
against the same stale rate used elsewhere, while still being wrong relative
to the market rate a human reader would expect.

## 17. Security and privacy implications

Money itself, as a value type wrapping an amount and a currency code, carries
no inherent secret or personally identifying information, and the pattern's
security surface is smaller than most patterns in this catalog. The
implications that do exist are indirect, arising from where Money values are
used rather than from the type itself.

A Money value attached to a specific customer, transaction, or account is
financial data, and the row or record it lives on is subject to whatever data
protection and retention obligations apply to financial records in the
relevant jurisdiction; this is a property of the surrounding record, not of
the Money type, but it means access controls and audit logging on the tables
or aggregates that hold Money-typed fields deserve the same care as any other
financially sensitive column.

Precision and rounding decisions have a narrow but real integrity dimension.
Because Money's arithmetic is exact and its allocation is total-preserving by
design (dimension 7), a system that correctly implements the pattern removes
one avenue by which a rounding discrepancy could be exploited or could mask a
deliberate skimming attack, sometimes called a salami-slicing attack in the
security literature, where fractional remainders from many transactions are
diverted to an unauthorised account rather than distributed fairly. This
entry could not verify a specific, named, currently reachable incident report
describing such an attack for inclusion here, so the connection is recorded as
a structural observation about what correct total-preserving allocation
closes off, not as a claim about a documented historical exploit.

Serialisation of Money across a network boundary should avoid transmitting
currency amounts as untyped, unauthenticated numeric values wherever the
receiving system will act on them financially, for the ordinary reason that
any financially consequential field crossing a trust boundary benefits from
the same integrity protections, transport encryption and, where applicable,
message signing, as any other financially consequential field; Money's
two-field shape does not change this requirement, it only means both fields,
amount and currency, need that protection together rather than the amount
alone.

## 18. References

- Martin Fowler, *Patterns of Enterprise Application Architecture*,
  Addison-Wesley, 2002, chapter 18, Base Patterns, Money.
- [Martin Fowler, Money pattern catalog page](https://martinfowler.com/eaaCatalog/money.html), verified 2026-08-02.
- [PostgreSQL 17 Documentation, section 8.1.3, Floating-Point Types](https://www.postgresql.org/docs/current/datatype-numeric.html), verified 2026-08-02.
- [Stripe, Supported currencies](https://docs.stripe.com/currencies), verified 2026-08-02.
- [Joda-Money, project home page](https://www.joda.org/joda-money/), verified 2026-08-02.
- [JavaMoney, JSR 354 project site](https://javamoney.github.io/), verified 2026-08-02.
- [Wikipedia, ISO 4217](https://en.wikipedia.org/wiki/ISO_4217), verified 2026-08-02.
- [Wikipedia, Largest remainder method](https://en.wikipedia.org/wiki/Largest_remainder_method), verified 2026-08-02, background on the general apportionment technique that Money's allocation algorithm applies to currency shares.

## Code examples

### TypeScript

```typescript
type CurrencyCode = "USD" | "EUR" | "JPY";

const MINOR_UNIT_EXPONENT: Record<CurrencyCode, number> = {
  USD: 2,
  EUR: 2,
  JPY: 0,
};

class CurrencyMismatchError extends Error {
  constructor(a: CurrencyCode, b: CurrencyCode) {
    super(`cannot combine ${a} with ${b}`);
  }
}

class Money {
  private constructor(
    private readonly minorUnits: bigint,
    private readonly currency: CurrencyCode
  ) {}

  static ofMinorUnits(minorUnits: bigint, currency: CurrencyCode): Money {
    return new Money(minorUnits, currency);
  }

  add(other: Money): Money {
    this.assertSameCurrency(other);
    return new Money(this.minorUnits + other.minorUnits, this.currency);
  }

  subtract(other: Money): Money {
    this.assertSameCurrency(other);
    return new Money(this.minorUnits - other.minorUnits, this.currency);
  }

  allocate(ratios: number[]): Money[] {
    const totalRatio = ratios.reduce((a, b) => a + b, 0);
    const raw = ratios.map((r) => (this.minorUnits * BigInt(r)) / BigInt(totalRatio));
    const allocated = raw.reduce((a, b) => a + b, 0n);
    const remainder = this.minorUnits - allocated;

    const remainders = ratios.map((r, i) => ({
      i,
      frac: Number((this.minorUnits * BigInt(r)) % BigInt(totalRatio)),
    }));
    remainders.sort((a, b) => b.frac - a.frac);

    const shares = raw.slice();
    for (let k = 0; k < Number(remainder); k++) {
      shares[remainders[k].i] += 1n;
    }
    return shares.map((s) => new Money(s, this.currency));
  }

  toDecimalString(): string {
    const exp = MINOR_UNIT_EXPONENT[this.currency];
    const divisor = 10n ** BigInt(exp);
    const whole = this.minorUnits / divisor;
    const frac = (this.minorUnits % divisor).toString().padStart(exp, "0");
    return exp === 0 ? `${whole} ${this.currency}` : `${whole}.${frac} ${this.currency}`;
  }

  private assertSameCurrency(other: Money): void {
    if (this.currency !== other.currency) {
      throw new CurrencyMismatchError(this.currency, other.currency);
    }
  }
}

const price = Money.ofMinorUnits(1099n, "USD");
const tax = Money.ofMinorUnits(88n, "USD");
console.log(price.add(tax).toDecimalString());

const total = Money.ofMinorUnits(1000n, "USD");
const shares = total.allocate([1, 1, 1]);
console.log(shares.map((s) => s.toDecimalString()));
```

### Python

```python
from __future__ import annotations
from dataclasses import dataclass


MINOR_UNIT_EXPONENT = {"USD": 2, "EUR": 2, "JPY": 0}


class CurrencyMismatchError(Exception):
    pass


@dataclass(frozen=True)
class Money:
    minor_units: int
    currency: str

    def _assert_same_currency(self, other: "Money") -> None:
        if self.currency != other.currency:
            raise CurrencyMismatchError(f"cannot combine {self.currency} with {other.currency}")

    def add(self, other: "Money") -> "Money":
        self._assert_same_currency(other)
        return Money(self.minor_units + other.minor_units, self.currency)

    def subtract(self, other: "Money") -> "Money":
        self._assert_same_currency(other)
        return Money(self.minor_units - other.minor_units, self.currency)

    def allocate(self, ratios: list[int]) -> list["Money"]:
        total_ratio = sum(ratios)
        raw = [(self.minor_units * r) // total_ratio for r in ratios]
        remainder = self.minor_units - sum(raw)
        fracs = [(i, (self.minor_units * r) % total_ratio) for i, r in enumerate(ratios)]
        fracs.sort(key=lambda pair: pair[1], reverse=True)
        shares = list(raw)
        for k in range(remainder):
            shares[fracs[k][0]] += 1
        return [Money(s, self.currency) for s in shares]

    def to_decimal_string(self) -> str:
        exp = MINOR_UNIT_EXPONENT[self.currency]
        if exp == 0:
            return f"{self.minor_units} {self.currency}"
        divisor = 10 ** exp
        whole, frac = divmod(self.minor_units, divisor)
        return f"{whole}.{str(frac).rjust(exp, '0')} {self.currency}"


if __name__ == "__main__":
    price = Money(1099, "USD")
    tax = Money(88, "USD")
    print(price.add(tax).to_decimal_string())

    total = Money(1000, "USD")
    for share in total.allocate([1, 1, 1]):
        print(share.to_decimal_string())
```

### Java

```java
import java.util.*;

final class CurrencyMismatchException extends RuntimeException {
    CurrencyMismatchException(String a, String b) {
        super("cannot combine " + a + " with " + b);
    }
}

public final class Money {
    private static final Map<String, Integer> MINOR_UNIT_EXPONENT = Map.of(
            "USD", 2, "EUR", 2, "JPY", 0
    );

    private final long minorUnits;
    private final String currency;

    private Money(long minorUnits, String currency) {
        this.minorUnits = minorUnits;
        this.currency = currency;
    }

    public static Money ofMinorUnits(long minorUnits, String currency) {
        return new Money(minorUnits, currency);
    }

    public Money add(Money other) {
        assertSameCurrency(other);
        return new Money(this.minorUnits + other.minorUnits, this.currency);
    }

    public Money subtract(Money other) {
        assertSameCurrency(other);
        return new Money(this.minorUnits - other.minorUnits, this.currency);
    }

    public Money[] allocate(int[] ratios) {
        int totalRatio = Arrays.stream(ratios).sum();
        long[] raw = new long[ratios.length];
        long[] fracs = new long[ratios.length];
        for (int i = 0; i < ratios.length; i++) {
            raw[i] = (minorUnits * ratios[i]) / totalRatio;
            fracs[i] = (minorUnits * ratios[i]) % totalRatio;
        }
        long allocated = Arrays.stream(raw).sum();
        long remainder = minorUnits - allocated;

        Integer[] order = new Integer[ratios.length];
        for (int i = 0; i < ratios.length; i++) order[i] = i;
        Arrays.sort(order, (a, b) -> Long.compare(fracs[b], fracs[a]));

        for (int k = 0; k < remainder; k++) {
            raw[order[k]] += 1;
        }

        Money[] shares = new Money[ratios.length];
        for (int i = 0; i < ratios.length; i++) {
            shares[i] = new Money(raw[i], currency);
        }
        return shares;
    }

    public String toDecimalString() {
        int exp = MINOR_UNIT_EXPONENT.get(currency);
        if (exp == 0) return minorUnits + " " + currency;
        long divisor = (long) Math.pow(10, exp);
        long whole = minorUnits / divisor;
        long frac = Math.abs(minorUnits % divisor);
        return whole + "." + String.format("%0" + exp + "d", frac) + " " + currency;
    }

    private void assertSameCurrency(Money other) {
        if (!this.currency.equals(other.currency)) {
            throw new CurrencyMismatchException(this.currency, other.currency);
        }
    }

    public static void main(String[] args) {
        Money price = Money.ofMinorUnits(1099, "USD");
        Money tax = Money.ofMinorUnits(88, "USD");
        System.out.println(price.add(tax).toDecimalString());

        Money total = Money.ofMinorUnits(1000, "USD");
        for (Money share : total.allocate(new int[]{1, 1, 1})) {
            System.out.println(share.toDecimalString());
        }
    }
}
```

### Go

```go
package main

import (
	"fmt"
	"sort"
)

var minorUnitExponent = map[string]int{"USD": 2, "EUR": 2, "JPY": 0}

type currencyMismatchError struct {
	a, b string
}

func (e *currencyMismatchError) Error() string {
	return fmt.Sprintf("cannot combine %s with %s", e.a, e.b)
}

type Money struct {
	minorUnits int64
	currency   string
}

func NewMoney(minorUnits int64, currency string) Money {
	return Money{minorUnits: minorUnits, currency: currency}
}

func (m Money) assertSameCurrency(other Money) error {
	if m.currency != other.currency {
		return &currencyMismatchError{m.currency, other.currency}
	}
	return nil
}

func (m Money) Add(other Money) (Money, error) {
	if err := m.assertSameCurrency(other); err != nil {
		return Money{}, err
	}
	return NewMoney(m.minorUnits+other.minorUnits, m.currency), nil
}

func (m Money) Allocate(ratios []int64) []Money {
	var totalRatio int64
	for _, r := range ratios {
		totalRatio += r
	}
	raw := make([]int64, len(ratios))
	fracs := make([]int64, len(ratios))
	var allocated int64
	for i, r := range ratios {
		raw[i] = (m.minorUnits * r) / totalRatio
		fracs[i] = (m.minorUnits * r) % totalRatio
		allocated += raw[i]
	}
	remainder := m.minorUnits - allocated

	order := make([]int, len(ratios))
	for i := range order {
		order[i] = i
	}
	sort.Slice(order, func(a, b int) bool { return fracs[order[a]] > fracs[order[b]] })

	for k := int64(0); k < remainder; k++ {
		raw[order[k]]++
	}

	shares := make([]Money, len(ratios))
	for i, v := range raw {
		shares[i] = NewMoney(v, m.currency)
	}
	return shares
}

func (m Money) DecimalString() string {
	exp := minorUnitExponent[m.currency]
	if exp == 0 {
		return fmt.Sprintf("%d %s", m.minorUnits, m.currency)
	}
	divisor := int64(1)
	for i := 0; i < exp; i++ {
		divisor *= 10
	}
	whole := m.minorUnits / divisor
	frac := m.minorUnits % divisor
	return fmt.Sprintf("%d.%0*d %s", whole, exp, frac, m.currency)
}

func main() {
	price := NewMoney(1099, "USD")
	tax := NewMoney(88, "USD")
	total, err := price.Add(tax)
	if err != nil {
		panic(err)
	}
	fmt.Println(total.DecimalString())

	pool := NewMoney(1000, "USD")
	for _, share := range pool.Allocate([]int64{1, 1, 1}) {
		fmt.Println(share.DecimalString())
	}
}
```

### Rust

```rust
use std::fmt;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum Currency {
    Usd,
    Eur,
    Jpy,
}

impl Currency {
    fn minor_unit_exponent(self) -> u32 {
        match self {
            Currency::Usd | Currency::Eur => 2,
            Currency::Jpy => 0,
        }
    }

    fn code(self) -> &'static str {
        match self {
            Currency::Usd => "USD",
            Currency::Eur => "EUR",
            Currency::Jpy => "JPY",
        }
    }
}

#[derive(Debug)]
struct CurrencyMismatch(Currency, Currency);

impl fmt::Display for CurrencyMismatch {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "cannot combine {} with {}", self.0.code(), self.1.code())
    }
}

#[derive(Debug, Clone, Copy)]
struct Money {
    minor_units: i64,
    currency: Currency,
}

impl Money {
    fn of_minor_units(minor_units: i64, currency: Currency) -> Self {
        Money { minor_units, currency }
    }

    fn add(self, other: Money) -> Result<Money, CurrencyMismatch> {
        if self.currency != other.currency {
            return Err(CurrencyMismatch(self.currency, other.currency));
        }
        Ok(Money::of_minor_units(self.minor_units + other.minor_units, self.currency))
    }

    fn allocate(self, ratios: &[i64]) -> Vec<Money> {
        let total_ratio: i64 = ratios.iter().sum();
        let mut raw: Vec<i64> = ratios.iter().map(|r| (self.minor_units * r) / total_ratio).collect();
        let allocated: i64 = raw.iter().sum();
        let remainder = self.minor_units - allocated;

        let mut order: Vec<usize> = (0..ratios.len()).collect();
        let fracs: Vec<i64> = ratios.iter().map(|r| (self.minor_units * r) % total_ratio).collect();
        order.sort_by(|&a, &b| fracs[b].cmp(&fracs[a]));

        for k in 0..remainder as usize {
            raw[order[k]] += 1;
        }

        raw.into_iter().map(|v| Money::of_minor_units(v, self.currency)).collect()
    }

    fn decimal_string(self) -> String {
        let exp = self.currency.minor_unit_exponent();
        if exp == 0 {
            return format!("{} {}", self.minor_units, self.currency.code());
        }
        let divisor = 10_i64.pow(exp);
        let whole = self.minor_units / divisor;
        let frac = (self.minor_units % divisor).abs();
        format!("{}.{:0width$} {}", whole, frac, self.currency.code(), width = exp as usize)
    }
}

fn main() {
    let price = Money::of_minor_units(1099, Currency::Usd);
    let tax = Money::of_minor_units(88, Currency::Usd);
    let total = price.add(tax).expect("same currency");
    println!("{}", total.decimal_string());

    let pool = Money::of_minor_units(1000, Currency::Usd);
    for share in pool.allocate(&[1, 1, 1]) {
        println!("{}", share.decimal_string());
    }
}
```

### Swift

```swift
enum Currency: String {
    case usd = "USD"
    case eur = "EUR"
    case jpy = "JPY"

    var minorUnitExponent: Int {
        switch self {
        case .usd, .eur: return 2
        case .jpy: return 0
        }
    }
}

enum MoneyError: Error {
    case currencyMismatch(Currency, Currency)
}

struct Money {
    let minorUnits: Int64
    let currency: Currency

    func add(_ other: Money) throws -> Money {
        guard currency == other.currency else {
            throw MoneyError.currencyMismatch(currency, other.currency)
        }
        return Money(minorUnits: minorUnits + other.minorUnits, currency: currency)
    }

    func allocate(_ ratios: [Int]) -> [Money] {
        let totalRatio = ratios.reduce(0, +)
        var raw = ratios.map { Int64($0) * minorUnits / Int64(totalRatio) }
        let allocated = raw.reduce(0, +)
        let remainder = minorUnits - allocated

        let fracs = ratios.map { Int64($0) * minorUnits % Int64(totalRatio) }
        let order = (0..<ratios.count).sorted { fracs[$0] > fracs[$1] }

        for k in 0..<Int(remainder) {
            raw[order[k]] += 1
        }
        return raw.map { Money(minorUnits: $0, currency: currency) }
    }

    func decimalString() -> String {
        let exp = currency.minorUnitExponent
        if exp == 0 {
            return "\(minorUnits) \(currency.rawValue)"
        }
        let divisor = Int64(pow(10.0, Double(exp)))
        let whole = minorUnits / divisor
        let frac = abs(minorUnits % divisor)
        let fracStr = String(format: "%0\(exp)d", frac)
        return "\(whole).\(fracStr) \(currency.rawValue)"
    }
}

let price = Money(minorUnits: 1099, currency: .usd)
let tax = Money(minorUnits: 88, currency: .usd)
if let total = try? price.add(tax) {
    print(total.decimalString())
}

let pool = Money(minorUnits: 1000, currency: .usd)
for share in pool.allocate([1, 1, 1]) {
    print(share.decimalString())
}
```

All six samples implement the same shape, an immutable amount-plus-currency
value with a currency-guarded `add`, a total-preserving `allocate` using
largest-remainder rounding, and a currency-aware decimal formatter that
respects a per-currency minor-unit exponent rather than assuming two decimal
places everywhere.
