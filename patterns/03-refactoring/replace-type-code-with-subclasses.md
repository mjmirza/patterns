---
name: Replace Type Code with Subclasses
slug: replace-type-code-with-subclasses
family: 03-refactoring
category: Simplifying Conditional Logic
aliases: [Replace Type Code with Class Hierarchy, Replace Type Code with State or Strategy]
first_described: "Fowler 1999"
maturity: canonical
related: [replace-conditional-with-polymorphism, replace-primitive-with-object, replace-subclass-with-delegate, replace-constructor-with-factory-function, state, strategy]
incompatible_with: [replace-subclass-with-delegate, remove-subclass]
verified: 2026-08-02
---

# Replace Type Code with Subclasses

## 1. Name, aliases, and lineage

The canonical name is Replace Type Code with Subclasses. Martin Fowler's online
catalog lists the refactoring under that name and says to use subclasses in
place of direct checks on a type code when the type code controls behavior
(https://refactoring.com/catalog/replaceTypeCodeWithSubclasses.html, verified
2026-08-02). Fowler's catalog also places it beside Replace Type Code with State
or Strategy, which is the related move for cases where subclassing the host
object is not the right shape
(https://refactoring.com/catalog/replaceTypeCodeWithStateStrategy.html,
verified 2026-08-02).

The lineage is Fowler's refactoring catalog. Martin Fowler, Kent Beck, John
Brant, William Opdyke and Don Roberts describe the first edition form in
*Refactoring. Improving the Design of Existing Code*, Addison-Wesley, 1999,
chapter 8, "Organizing Data." Fowler's second edition keeps the same catalog
name in the online catalog and moves the surrounding material into the modern
JavaScript examples in Martin Fowler, *Refactoring. Improving the Design of
Existing Code*, 2nd edition, Addison-Wesley, 2018, chapter 12, "Dealing with
Inheritance."

The alias Replace Type Code with Class Hierarchy is common in code review, but
it is less precise. The goal is not to create a hierarchy for its own sake. The
goal is to move behavior that varies by type from conditional statements into
overridden methods. Replace Type Code with State or Strategy is not an alias in
the strict sense. It is the sibling refactoring for the same smell when changing
the object's own class is blocked by existing inheritance, persistence mapping,
or lifecycle rules.

Judgement. The name is easy to misread because the refactoring does not replace
every type code. Many systems need stable external codes in JSON, database
columns, event names, metrics labels, or protocol fields. The refactoring
replaces internal behavioral branching on those codes. A code can remain at the
boundary while the domain model stops asking `if kind == ...` in the middle of
business logic.

## 2. Problem and context

A field, enum, string, integer, or symbolic constant says what kind of thing an
object is. Many methods then inspect that value and choose behavior. The first
branch looks harmless. A second branch appears in another method. A third branch
appears in a report, a validator, or a batch job. After enough growth, adding a
new kind means hunting through the codebase for every condition that mentions
the code. Missing one branch produces a runtime defect, because the compiler
does not know that all branches over the type code must be updated together.

The smell is not the existence of a code. The smell is behavior scattered
behind repeated code tests. A type column in a table may be required by a
storage format. A message type in an event stream may be part of a published
contract. An enum used as a metric label may be the right representation for
telemetry. The problem begins when the object that holds the code also has
methods such as `price`, `riskWeight`, `requiresApproval`, `label`, `limits`,
or `validate`, and each method branches on the same code.

The context is an object whose variants are real domain concepts with behavior.
Examples include employee kinds with different pay rules, subscription plans
with different limits, loan products with different eligibility checks, tax
line items with different calculations, and document nodes with different
rendering. The type code starts as data. Over time it becomes a proxy for a
missing subtype.

The cost is most visible during change. A new type code is accepted by parsing
code and stored correctly, yet one old conditional falls through to a default
case. Tests that focus on the new feature pass, while a rarely used report now
misclassifies the new variant. The type code gave the team a single field, but
it did not give the team a single place to put variant behavior.

Replace Type Code with Subclasses changes the internal model. The base type
keeps the stable operations that all variants share. Each variant becomes a
subclass that overrides the operations that differ. Clients ask the object to
do the work. They stop reading the code and deciding from outside.

## 3. Forces

Judgement. These are engineering trade-offs. Their weight changes with the
language, the team, and the release model.

- **Coupling.** The refactoring lowers coupling between clients and the list of
  variants. Clients depend on a base type and call behavior. It raises coupling
  between each variant and the base class contract, because every subclass must
  honor the same public operations.
- **Consistency.** It favors consistency for variant behavior. The pay rule,
  validation rule, or rendering rule for one variant sits in one subclass
  instead of being copied across conditionals.
- **Cognitive load.** It lowers load for readers who work inside one variant,
  because all behavior for that variant is close together. It raises load for a
  reader who wants a cross-variant comparison, because the behavior is spread
  over several classes.
- **Latency.** It is usually neutral. Dynamic dispatch replaces a branch. In a
  hot loop where branch prediction, allocation, or virtual call inlining matters,
  measure before and after rather than arguing from the catalog.
- **Operability.** It can improve diagnostics when logs and traces include the
  concrete subtype. It can make incidents harder when telemetry records only the
  base type and the source no longer shows the branch taken.
- **Cost of change.** It favors adding behavior that belongs to one variant. It
  sacrifices cheap global changes to the base protocol, because a new abstract
  operation touches every subclass.
- **Persistence and serialization.** It may add mapping cost. Databases and
  wire formats often store a discriminator code, so the system needs a clear
  translation point from external code to internal subtype.
- **Team topology.** It favors teams that own variants separately. Each team can
  change its subclass without editing a shared switch. It can hurt small teams
  when the number of classes becomes larger than the domain warrants.

The exchange is simple. The refactoring trades a compact data representation
and visible branches for localized behavior and compiler-backed variant
coverage. It is a good exchange when behavior is growing. It is a poor exchange
when the code is data with no behavior.

## 4. Applicability and non-applicability

Reach for Replace Type Code with Subclasses when the following conditions hold.

- Several methods branch on the same type code, and those branches implement
  business behavior rather than parsing, storage, or display names.
- Each code value represents a stable domain kind with a meaningful name, such
  as `PermanentEmployee`, `HourlyEmployee`, `TrialPlan`, or `InvoiceCredit`.
- The object can have different concrete classes without breaking identity,
  persistence, equality, or lifecycle expectations.
- New variants are expected, and a missed branch would be a real defect.
- The current default case hides errors by returning a fallback behavior for an
  unknown code.
- Tests already duplicate the same matrix of code values against several
  operations.
- Callers ask for the type code and then make decisions that would read better
  as polymorphic calls.

Non-applicability. Do not apply the refactoring in these cases.

- **The code is a stable external discriminator.** Database rows, JSON payloads,
  event streams, and protocol messages may need the code. Keep it at the edge
  and translate inward. Do not make the stored format depend on language class
  names.
- **There is no behavior attached to the code.** A code used for filtering,
  grouping, sorting, analytics labels, or display can stay as an enum or value
  object.
- **The code changes during the object's lifetime.** If an order moves from
  draft to paid to shipped, a State object often fits better than changing the
  object's class or rebuilding it on every transition.
- **The object already uses inheritance for another axis.** A class cannot
  usually extend both `EmployeeByRegion` and `EmployeeByPayType`. Use State,
  Strategy, or delegation for the new axis.
- **The number of combinations is the product of several independent axes.**
  `Plan x Region x Currency x Channel` should not become one subclass per
  combination. Model each axis separately.
- **The type code is selected from user configuration at runtime.** A registry,
  lookup table, or constructor function map is clearer than a generated subclass
  per configured value.
- **The behavior is a small closed mapping.** A tiny enum with one table of
  constants may beat a hierarchy when the mapping is stable and has no logic.
- **The hierarchy would mirror a relational schema without domain behavior.**
  Object subclasses that only expose fields from different tables are an
  expensive way to spell data transfer objects.
- **The language favors algebraic data types for this shape.** In Rust, Swift
  enums with associated values, F# discriminated unions, and sealed Kotlin
  classes can express closed variants without an open inheritance hierarchy.
- **The team cannot name the variants in domain language.** If names are
  `Type1`, `Type2`, and `Type3`, the model is not understood well enough.

## 5. Structure

The structure has six participants.

- **Coded record.** The existing class or data record that owns the type code.
  It has fields common to all variants and methods that branch on the code.
- **Type code.** The enum, integer, string, tag, or constant that currently
  chooses behavior. It may remain at system boundaries, but it stops being the
  main behavioral dispatch mechanism inside the domain model.
- **Base domain type.** The abstract class, interface plus abstract base, or
  sealed parent that represents the shared protocol. It declares operations
  that clients call without asking which variant they have.
- **Concrete subtype.** One class per behavioral variant. Each subtype gives a
  domain name to one code value and overrides the operations that differ.
- **Creation translator.** A factory function, parser, repository mapper, or
  migration point that turns the external code into the internal subtype. This
  is where unknown codes fail loudly.
- **Clients.** Existing callers that used to read the code and branch. After the
  refactoring they call operations on the base domain type.

The important relationship is one-way translation. Codes may enter from the
outside, then the creation translator builds a subtype. Domain clients do not
pull the code back out to decide behavior. If they do, the refactoring is
unfinished.

## 6. ASCII structure diagram

```text
Before

  +------------------------------+
  |          Employee            |
  |------------------------------|
  | type_code: "engineer"|"sales"|
  | salary: Money                |
  | commission_rate: Percent     |
  |------------------------------|
  | pay()                        |
  |   if type_code == "sales"    |
  |   if type_code == "engineer" |
  | benefits()                   |
  |   if type_code == "sales"    |
  +------------------------------+
              ^
              |
       clients read type_code
       and repeat decisions

After

  +-----------------------------+
  |        Employee             |
  |-----------------------------|
  | salary: Money               |
  |-----------------------------|
  | pay()                       |
  | benefits()                  |
  +-----------------------------+
        ^                 ^
        | extends         | extends
        |                 |
  +-------------+   +----------------+
  | Engineer    |   | SalesEmployee  |
  |-------------|   |----------------|
  | pay()       |   | commission     |
  | benefits()  |   | pay()          |
  +-------------+   | benefits()     |
                    +----------------+

  +-----------------------------+
  | EmployeeMapper              |
  |-----------------------------|
  | from_row(type_code, fields) |
  +-----------------------------+
        | "engineer" -> Engineer
        | "sales"    -> SalesEmployee
```

## 7. Dynamics

At runtime, the translation from code to subtype should happen once near the
boundary. After that, normal dispatch chooses behavior. The client does not see
the code and does not own the variant table.

```text
Repository        EmployeeMapper        SalesEmployee        PayrollJob
    |                   |                     |                  |
    |-- row ------------>|                     |                  |
    |   type="sales"    |                     |                  |
    |                   |-- new SalesEmployee(fields) ---------->|
    |                   |<----------- employee ------------------|
    |<-- employee ------|                     |                  |
    |                                                          |
    |------------------------- employee ----------------------->|
    |                                                          |
    |                                      pay() -------------->|
    |                                      (dynamic dispatch)   |
    |                                      commission included  |
    |                                      <--------------------|
    |<------------------------ payroll result ------------------|

Unknown type code path

Repository -> EmployeeMapper -> UnknownEmployeeType("contractor")
```

Two dynamics matter in production. First, the unknown-code path must be
observable and should fail at the translation point. A default base object with
generic behavior can mask data drift. Second, the external code may need to be
preserved for round-trip storage, audit, or metrics. Preserve it as boundary
data or a read-only attribute, but do not let it regain control over behavior.

## 8. Implementation variants

**Direct subclass hierarchy.** The base class declares operations and each
subclass overrides them. This is the classical form. It works well in Java,
Python, TypeScript, Swift classes, and C# when the object can change concrete
class at construction. It is weak when the object is persisted by a mapper that
expects one table and one class.

**Factory-backed translation.** External rows or payloads still contain a code,
and a factory maps codes to subclasses. This is the most common migration
shape, because public data formats rarely change at the same time as domain
code. The factory should reject unknown codes and should have a test for every
supported code.

**Subclass for invariant, Strategy for volatile behavior.** A subtype may
represent stable identity, while a Strategy object represents a policy that
changes often. For example, `PremiumAccount` can be a subtype and its fraud
check can be a supplied strategy. This avoids rebuilding the hierarchy every
time a policy changes.

**State object instead of subclass.** When the type code represents a lifecycle
state, such as draft, approved, paid, or cancelled, the host object can keep its
identity while delegating state-specific behavior to a state object. This is
Replace Type Code with State or Strategy, not the subclass refactoring.

**Sealed hierarchy.** Languages with sealed classes or sealed interfaces let
the author keep the variant set closed. Java's sealed classes are specified in
the Java Language Specification, section 8.1.1.2, and restrict which classes may
extend a sealed class
(https://docs.oracle.com/javase/specs/jls/se21/html/jls-8.html#jls-8.1.1.2,
verified 2026-08-02). This variant is useful when the team wants polymorphism
and compiler help for exhaustive handling in the few places that still compare
variants.

**Algebraic data type.** Rust enums, Swift enums with associated values, and F#
discriminated unions place the variants in one type rather than a subtype
tree. This can be a better closed-world destination. It replaces conditionals
with pattern matching, so it does not have the same extension behavior as
subclasses. It is a cousin, not the classical refactoring.

**Table-driven variant.** When each code maps to constants and no method body,
an enum with fields or a lookup table may be the better refactoring. This keeps
cross-variant comparison easy and avoids classes that hold no behavior.

**Persistence discriminator with domain subclasses.** Object relational mappers
often store a discriminator column while hydrating different subclasses. The
domain model can still benefit from polymorphism, but the schema and mapper
configuration become part of the refactoring. Treat that mapper as the creation
translator.

**Strangler migration.** Large systems rarely replace every branch in one
patch. A practical route is to introduce subclasses for one operation, leave
the old code visible for storage, and then move branch bodies one at a time.
During the migration, the base type may still expose a read-only external code
for adapters and reports. Mark that member as boundary data in naming and
documentation. The member is allowed to exist, but domain clients should not
use it to select behavior. This variant works well when release trains,
database migrations, and partner contracts move at different speeds.
The migration is complete only when a search for old code checks returns
boundary adapters, mapper tests, and telemetry labels rather than domain
decision logic.

## 9. Known production uses

These are production designs that show the destination shape. The sources prove
the named systems expose subtype families for behavior. The claim that they
once performed this exact refactoring would require project history, so that is
not claimed.

**CPython `ast` module.** Python's standard library exposes an `ast.AST` base
class and concrete node classes such as `FunctionDef`, `ClassDef`, `If`,
`BinOp`, and `Call`. The Python documentation describes the node classes and
their fields in the `ast` module reference
(https://docs.python.org/3/library/ast.html, verified 2026-08-02). Judgement.
This is the destination shape of replacing a single node-kind code with
subclasses: visitors and transformers receive domain-named node objects instead
of decoding one generic record with a tag.

**Jackson Databind tree model.** Jackson's `JsonNode` is the base class for a
tree model, with concrete subclasses in packages such as
`com.fasterxml.jackson.databind.node`, including object, array, numeric, text,
boolean, null, and missing-node forms. The current Javadoc documents `JsonNode`
and its subclass tree
(https://www.javadoc.io/doc/com.fasterxml.jackson.core/jackson-databind/latest/com/fasterxml/jackson/databind/JsonNode.html,
verified 2026-08-02). Judgement. Jackson still exposes node type inspection for
some clients, but much node behavior sits on named subclasses, which is the
hybrid many production tree models use.

**Java NIO file system providers.** Java NIO defines `java.nio.file.FileSystem`
as an abstract class and `FileSystemProvider` as the service provider entry
point. The Java SE 21 API documents provider-created file systems and the
abstract operations on `FileSystem`
(https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/nio/file/FileSystem.html,
verified 2026-08-02). Judgement. A path operation does not switch on a string
such as `zip`, `unix`, or `windows` in client code. It dispatches through the
provider's concrete file system and path implementations.

**Swift Foundation URL loading tasks.** Apple's Foundation documentation lists
`URLSessionTask` as a base class with concrete task forms such as
`URLSessionDataTask`, `URLSessionDownloadTask`, and `URLSessionUploadTask`
(https://developer.apple.com/documentation/foundation/urlsessiontask,
verified 2026-08-02). Judgement. The design gives each task variant a named
type and variant-specific API surface instead of asking every caller to inspect
a task-kind code before using it.

## 10. Consequences

Positive.

- Variant behavior becomes local. A reader can open `SalesEmployee` and find
  the sales pay rule without scanning every branch over `employeeType`.
- Adding a variant becomes a creation and subclass task. Existing clients that
  call the base protocol often need no edits.
- The compiler can help. Abstract methods force each concrete subtype to make a
  choice rather than inheriting a forgotten branch.
- Default branches shrink. Unknown codes can fail at the translator rather than
  falling into generic behavior.
- Tests can move from large type-code matrices toward contract tests over the
  base type plus focused tests per subtype.
- Domain names become searchable. A code such as `"S"` becomes
  `SalariedEmployee`, which carries more meaning in stack traces and logs.

Negative.

- The design gains files and types. If variants have little behavior, the
  hierarchy feels heavier than the problem.
- Cross-variant comparison is less local. A reader comparing all pay formulas
  must open several subclasses.
- Changing the base protocol can be expensive. Every concrete subtype may need
  a new method or a revised invariant.
- Persistence, serialization, and migration need care. The external type code
  may still exist, so the system has two representations to keep aligned.
- Multiple independent type codes can create a subclass explosion if the
  hierarchy tries to model every combination.
- Dynamic dispatch can hide the concrete path from telemetry unless subtype
  names are recorded.

## 11. Failure modes and misuse

Judgement. The following triples describe production symptoms, likely causes,
and corrective moves.

**Symptom.** A new subtype works in the main screen but is absent from one
report or background job. **Cause.** The refactoring stopped halfway, and some
clients still branch on the old code. **Fix.** Search for all reads of the type
code, move those decisions behind base-type operations, and make the code field
private or boundary-only.

**Symptom.** A directory contains dozens of subclasses with one constant method
each. **Cause.** A table of values was converted into a hierarchy even though
there was no variant behavior. **Fix.** Collapse the subclasses into an enum
with fields, a lookup table, or Replace Subclass with Delegate if the objects
need runtime composition.

**Symptom.** A database row with a new discriminator crashes only after a later
method call, far from the repository. **Cause.** The mapper created a generic
base instance or stored an unknown code rather than rejecting it. **Fix.** Make
the creation translator total over known codes and fail loudly on unknown codes
at the boundary.

**Symptom.** A customer changes plan from trial to paid, and stale trial limits
remain in memory. **Cause.** A lifecycle state was modeled as the object's
class, so changing state required replacing the whole object and some references
still point at the old instance. **Fix.** Use State or Strategy for mutable
policy, or rebuild the aggregate through one repository boundary.

**Symptom.** The hierarchy grows as `UsTrialCardPlan`, `EuTrialCardPlan`,
`UsPaidInvoicePlan`, and many more combinations. **Cause.** Several independent
axes were encoded in one inheritance tree. **Fix.** Keep the stable subtype
axis and move the other axes to delegated policy objects or value objects.

**Symptom.** Unit tests pass by asserting subclass names, while behavior still
diverges in production. **Cause.** Tests check mapping but not the base-type
contract. **Fix.** Add contract tests that exercise the public operations for
every subtype, and keep mapping tests small.

**Symptom.** Logs say every failure came from `Employee`, with no clue which
variant ran. **Cause.** Observability retained the old base-class label after
behavior moved into subclasses. **Fix.** Add subtype name, external code, and
translator result to traces and counters, with privacy review for labels.

**Symptom.** A subclass overrides a method and quietly skips validation that
the old conditional applied before every branch. **Cause.** Shared preconditions
were duplicated into branch bodies before the refactoring. **Fix.** Pull common
checks up into a final template method or guard in the base class, and leave
only variant behavior abstract.

## 12. Trade-off matrix

| Force | Replace Type Code with Subclasses | Replace Type Code with State or Strategy | Replace Conditional with Polymorphism | Enum with behavior | Lookup table | Algebraic data type |
|---|---|---|---|---|---|---|
| Coupling to variant list | Low for clients, medium for base class | Low for host, medium for policy interface | Low after polymorphic target exists | Medium, enum owns all variants | Medium, table owns all variants | Medium, callers may pattern match |
| Adding a new variant | New subclass plus mapper entry | New state or strategy plus wiring | Depends on target hierarchy | Edit enum | Add row or entry | Edit closed type |
| Changing one variant | Local to subclass | Local to policy object | Local to subclass or strategy | Local but same file | Local data edit | Local branch in functions |
| Runtime state changes | Poor | Strong | Depends on design | Medium | Strong for data | Medium with new value |
| Multiple independent axes | Poor | Good through composition | Depends on target | Poor to medium | Good for pure data | Poor to medium |
| Persistence mapping | Needs discriminator translation | Host identity stays stable | Depends on target | Simple code field | Simple code field | Needs codec |
| Cognitive load | Medium, many files | Medium, host plus delegate | Medium | Low for small sets | Low for data | Low for closed variants |
| Operability | Needs subtype telemetry | Needs policy telemetry | Same as target | Code label visible | Key label visible | Variant label visible |
| Best fit | Stable behavioral kinds | Mutable or pluggable policy | Existing conditional smell | Closed set with small behavior | Data mappings | Closed variants in ADT language |

Reading of the table. Subclasses are strongest when the variant is part of the
object's identity for its lifetime. State or Strategy is stronger when behavior
changes during the object's life or when another inheritance axis already
exists. An enum or lookup table is stronger when the difference is data, not
behavior. Algebraic data types are often stronger in closed-world functional or
multi-paradigm code, because they keep all variants type checked without
opening an inheritance tree.

## 13. Related and incompatible patterns

- **Replace Conditional with Polymorphism.** This is the broader refactoring
  family. Replace Type Code with Subclasses is a path into polymorphism when
  the conditional key is a field on the object itself.
- **Replace Primitive with Object.** Often comes first. A raw string or integer
  code may become a small type-code object before the team decides whether it
  should become subclasses, State, Strategy, or an enum.
- **Replace Type Code with State or Strategy.** This is the sibling move. Use it
  when the code represents changeable state, when the object already subclasses
  something else, or when policies should be configured at runtime.
- **State.** State replaces conditionals over lifecycle state while keeping the
  host object's identity. It is often incompatible with a subtype per state
  when references to the host must remain stable.
- **Strategy.** Strategy replaces conditionals over an algorithm. It composes
  better than subclassing when several algorithms vary independently.
- **Template Method.** A base class can keep common sequencing while subclasses
  fill variant hooks. Use it carefully, because too many hooks can make the
  base class hard to reason about.
- **Factory Method.** A factory or mapper is usually needed to translate the
  external code into the internal subtype. Factory Method handles creation, not
  the variant behavior itself.
- **Replace Subclass with Delegate.** This is the route out when the hierarchy
  starts modeling too many axes or when variants must change at runtime.
- **Remove Subclass.** Use it when a subtype carries no behavior and no
  invariant. That is evidence that the type code should perhaps have stayed as
  data.
- **Visitor.** Visitor can restore cross-variant operations over a class
  hierarchy, as seen in many tree models. It helps when new operations are more
  common than new variants, but it moves the trade-off away from subclass-local
  behavior.

## 14. Refactoring path in and out

Introducing the refactoring.

1. Pick one type code and one behavior that branches on it. Do not start with
   every code in the system.
2. Make the type code reads visible. Use search, tests, and compiler errors to
   find methods and clients that branch on it.
3. Separate boundary code from domain behavior. Keep parsing, storage, metrics,
   and API representation in a mapper or adapter.
4. Extract a base type if one does not exist. Move common fields and common
   behavior there.
5. Create one subclass per current code value. Give each subclass a domain name,
   not a code-name wrapper.
6. Move one branch body into an overridden method on each subclass. The base
   method becomes abstract or a final template that calls a protected hook.
7. Add a creation translator from code to subtype. Unknown codes should return
   a typed error, not a generic base object.
8. Change clients to call the base operation instead of reading the code.
9. Repeat for the next branch over the same code. Run tests after each moved
   operation.
10. Restrict access to the old code field. It can remain for persistence or
   audit, but domain clients should not use it for decisions.
11. Delete dead branches and defaults once no client reads the code.

Refactoring out.

1. Look for evidence that the hierarchy no longer earns its place: subclasses
   with no behavior, variant counts growing by combinations, or frequent
   runtime state changes.
2. If the difference is data, move constants from subclasses into an enum,
   table, or value object and make the base class concrete again.
3. If the difference is policy, move variant methods into Strategy objects and
   hold a strategy field on the host.
4. If the difference is lifecycle state, introduce State and delegate changing
   behavior to it.
5. Use Replace Subclass with Delegate when the host still has meaningful common
   identity but the variant axis should be composed.
6. Use Remove Subclass when a subclass adds no fields, methods, validation, or
   policy. Inline its creation path into the remaining type.
7. Keep boundary compatibility until external readers no longer need the old
   code. Domain cleanup and storage migration do not have to ship in one patch.

## 15. Testing and verification

Judgement. Good tests for this refactoring prove two things: code-to-subtype
translation is complete, and each subtype honors the base contract.

Easier because of the refactoring.

- Each subtype can be tested in isolation with setup that names the variant.
- Shared behavior can move into an abstract contract test that runs against
  every subtype.
- Unknown codes can be tested at one translator rather than at every branch.
- Clients can be tested with fake base-type instances instead of constructing
  many code combinations.

Harder because of the refactoring.

- A test that used to assert one table of code outcomes may now need one case
  per subclass.
- Serialization tests become more important, because the system has both an
  external code and an internal class.
- Test data builders need to create the right subtype, not set a code field on
  a generic object.

Techniques.

- **Golden mapping test.** For every supported external code, assert that the
  translator returns the expected subtype and preserves the external code if
  round-trip storage needs it.
- **Unknown-code test.** Feed the translator an unsupported code and assert a
  typed failure with the raw code included in the error context.
- **Contract test.** Define the required behavior once against the base type,
  then run it for every concrete subtype.
- **Branch-removal test.** After moving one operation, search or use static
  analysis to confirm that old clients no longer read the type code for that
  operation.
- **Mutation test.** A mutator that changes one subtype mapping or removes one
  override should fail tests. If it does not, the old branch matrix had more
  coverage than the new hierarchy.

For code review, demand a before-and-after call site. If the patch creates
subclasses but clients still ask for the type code, the change created types
without moving behavior.

## 16. Observability signals

Judgement. The refactoring moves the branch from source text to runtime
dispatch, so telemetry must carry the variant name.

Record these signals.

- A counter for created domain objects by external code and internal subtype.
- A counter for unknown type codes at the creation translator, with source
  system and deployment version.
- A trace attribute for subtype on operations whose behavior varies by subtype.
- A metric for fallback or default behavior, if any default remains during a
  migration.
- A log event when a subtype is selected from persisted data, at debug level for
  high-volume paths and info level for low-volume administrative paths.
- A dashboard panel comparing expected and observed subtype mix per tenant,
  region, product, or workload.

A healthy instance shows stable subtype mix for stable input, zero unknown-code
events, and no default-path events after migration. Variant-specific latency
may differ, but each subtype should have a stable range that matches its work.

A failing instance shows one of four shapes. Unknown-code events spike after a
producer deploy. A new subtype appears in storage but not in runtime counters,
which points to a mapper gap. Default-path events remain after the migration
window, which means a client still uses the old code. One subtype's latency or
failure rate separates from the rest, which localizes the incident to that
variant.

Privacy note for observability. External type codes can reveal plan, region,
benefit class, risk tier, or customer segment. Treat those labels as business
data. Prefer stable low-cardinality codes in metrics, and keep raw partner or
customer-provided labels out of high-volume telemetry.

## 17. Security and privacy implications

Judgement. The refactoring is not a security pattern. Its security impact comes
from where codes are accepted, how unknown codes fail, and how much authority a
subtype receives after translation.

Security gains.

- Unknown codes can fail at one boundary. That reduces the chance that an
  attacker or faulty producer reaches an untested default branch.
- Variant-specific validation can live next to variant-specific behavior. A
  `WireTransferPayment` subtype can validate limits and beneficiary rules
  without relying on every caller to remember the same checks.
- The base protocol can hide operations that do not apply to all variants,
  which reduces unsafe casts and unchecked field access.

Security costs.

- A mapper from external code to subtype becomes a trust boundary. If it accepts
  class names or module names from input, it can become unsafe dynamic loading.
  Map external codes to an allowlisted set of constructors.
- Subclasses may run with the privileges of the base workflow. If third-party
  plugins can supply subtypes, treat them as untrusted code and restrict file,
  network, and secret access according to the host runtime.
- A default subtype can become an authorization bug. For example, an unknown
  account type that receives standard permissions may be more dangerous than a
  hard failure.
- Serialization can leak internal class names if the framework writes subtype
  names into JSON or logs. External protocols should use stable public codes,
  not implementation class names.

Privacy implications.

The type code or subtype name may encode sensitive business facts. A benefits
subtype can reveal employment class. A plan subtype can reveal payment tier. A
risk subtype can reveal fraud or credit decisions. Use public codes at the edge,
redact or bucket labels where needed, and avoid logging raw subtype names when
class names contain tenant names or partner names.

## 18. References

- Martin Fowler, Kent Beck, John Brant, William Opdyke and Don Roberts,
  *Refactoring. Improving the Design of Existing Code*, Addison-Wesley, 1999,
  chapter 8, "Organizing Data."
- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
  edition, Addison-Wesley, 2018, chapter 12, "Dealing with Inheritance."
- Martin Fowler, "Replace Type Code with Subclasses,"
  https://refactoring.com/catalog/replaceTypeCodeWithSubclasses.html, verified
  2026-08-02.
- Martin Fowler, "Replace Type Code with State or Strategy,"
  https://refactoring.com/catalog/replaceTypeCodeWithStateStrategy.html,
  verified 2026-08-02.
- Oracle, *Java Language Specification, Java SE 21 Edition*, section 8.1.1.2,
  "sealed Classes and Interfaces,"
  https://docs.oracle.com/javase/specs/jls/se21/html/jls-8.html#jls-8.1.1.2,
  verified 2026-08-02.
- Python Software Foundation, "ast. Abstract Syntax Trees,"
  https://docs.python.org/3/library/ast.html, verified 2026-08-02.
- FasterXML, "JsonNode," Jackson Databind Javadoc,
  https://www.javadoc.io/doc/com.fasterxml.jackson.core/jackson-databind/latest/com/fasterxml/jackson/databind/JsonNode.html,
  verified 2026-08-02.
- Oracle, "FileSystem," Java SE 21 API documentation,
  https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/nio/file/FileSystem.html,
  verified 2026-08-02.
- Apple, "URLSessionTask," Foundation documentation,
  https://developer.apple.com/documentation/foundation/urlsessiontask, verified
  2026-08-02.

## Code examples

The examples use Swift, TypeScript, and Python. Swift shows the classical
subtype form with an abstract-style base class. TypeScript shows the same
refactoring in a structurally typed language. Python shows a small factory
translator that keeps the external code at the boundary. Java would also be a
natural fit, but this workspace could not locate a Java runtime during
verification, so it is omitted from the runnable set.

### Swift

```swift
class Subscription {
    let accountId: String

    init(accountId: String) {
        self.accountId = accountId
    }

    final func renewalNotice() -> String {
        "\(accountId):\(monthlyLimit()):\(supportLabel())"
    }

    func monthlyLimit() -> Int {
        fatalError("subclass must override monthlyLimit")
    }

    func supportLabel() -> String {
        fatalError("subclass must override supportLabel")
    }
}

final class TrialSubscription: Subscription {
    override func monthlyLimit() -> Int {
        3
    }

    override func supportLabel() -> String {
        "community"
    }
}

final class EnterpriseSubscription: Subscription {
    override func monthlyLimit() -> Int {
        500
    }

    override func supportLabel() -> String {
        "named"
    }
}

enum SubscriptionMapper {
    static func fromCode(_ code: String, accountId: String) -> Subscription {
        switch code {
        case "trial":
            return TrialSubscription(accountId: accountId)
        case "enterprise":
            return EnterpriseSubscription(accountId: accountId)
        default:
            fatalError("unknown plan: \(code)")
        }
    }
}

let plan = SubscriptionMapper.fromCode("enterprise", accountId: "acct-7")
print(plan.renewalNotice())
```

### TypeScript

```typescript
abstract class InvoiceLine {
  constructor(readonly description: string, readonly cents: number) {}

  abstract totalCents(): number;
  abstract ledgerAccount(): string;
}

class ProductLine extends InvoiceLine {
  totalCents(): number {
    return this.cents;
  }

  ledgerAccount(): string {
    return "product-sales";
  }
}

class DiscountLine extends InvoiceLine {
  totalCents(): number {
    return -Math.abs(this.cents);
  }

  ledgerAccount(): string {
    return "discounts";
  }
}

function lineFromCode(
  code: string,
  description: string,
  cents: number,
): InvoiceLine {
  if (code === "product") return new ProductLine(description, cents);
  if (code === "discount") return new DiscountLine(description, cents);
  throw new Error(`unknown line type: ${code}`);
}

const lines = [
  lineFromCode("product", "seat", 2000),
  lineFromCode("discount", "launch credit", 500),
];

console.log(lines.map((line) => line.ledgerAccount()).join(","));
console.log(lines.reduce((sum, line) => sum + line.totalCents(), 0));
```

### Python

```python
from __future__ import annotations

from abc import ABC, abstractmethod


class Ticket(ABC):
    def __init__(self, title: str) -> None:
        self.title = title

    def summary(self) -> str:
        return f"{self.queue()}:{self.title}:{self.sla_hours()}"

    @abstractmethod
    def queue(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def sla_hours(self) -> int:
        raise NotImplementedError


class BugTicket(Ticket):
    def queue(self) -> str:
        return "engineering"

    def sla_hours(self) -> int:
        return 24


class BillingTicket(Ticket):
    def queue(self) -> str:
        return "finance"

    def sla_hours(self) -> int:
        return 8


def ticket_from_code(code: str, title: str) -> Ticket:
    if code == "bug":
        return BugTicket(title)
    if code == "billing":
        return BillingTicket(title)
    raise ValueError(f"unknown ticket type: {code}")


if __name__ == "__main__":
    ticket = ticket_from_code("billing", "duplicate charge")
    print(ticket.summary())
```
