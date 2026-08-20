---
name: Replace Conditional with Polymorphism
slug: replace-conditional-with-polymorphism
family: 03-refactoring
category: Refactoring
aliases: [Replace Switch with Strategy]
first_described: "Fowler 1999"
maturity: established
related: [consolidate-conditional-expression, decompose-conditional, introduce-special-case, remove-subclass, replace-command-with-function, strategy, state, template-method]
incompatible_with: [remove-subclass]
verified: 2026-08-02
---

# Replace Conditional with Polymorphism

## 1. Name, aliases, and lineage

The canonical name is Replace Conditional with Polymorphism. Martin Fowler's
catalog records it under that name in the refactoring catalog
(https://refactoring.com/catalog/replaceConditionalWithPolymorphism.html,
verified 2026-08-02). Fowler also lists it as a refactoring kept from the first
edition to the second edition of *Refactoring* in his public change log for the
second edition, where the first edition entry is listed at page 255
(https://martinfowler.com/articles/refactoring-2nd-changes.html, verified
2026-08-02). The book citation for the catalog entry is Martin Fowler,
*Refactoring. Improving the Design of Existing Code*, first edition,
Addison-Wesley, 1999, chapter "Simplifying Conditional Expressions"; and Martin
Fowler, with Kent Beck, *Refactoring. Improving the Design of Existing Code*,
second edition, Addison-Wesley, 2018, catalog entry "Replace Conditional with
Polymorphism."

The name is precise but narrow. The refactoring is not "use inheritance." It is
the act of moving variant behavior out of a conditional expression and into
separate implementations of a common operation. The dispatch decision moves
from `if`, `else if`, `switch`, `match`, or a type-code lookup into the runtime
choice of an object, subclass, strategy, enum method, trait object, or
function-valued implementation.

A related but distinct catalog entry is Replace Type Code with Subclasses, which
Fowler lists separately in the second edition. that refactoring creates the
subtype-per-value hierarchy from a plain type-code field. Replace Conditional
with Polymorphism is the step that follows it, removing the conditional now that
the subtypes exist to dispatch on. Teams often chain the two, but they are not
the same move and should not be cited as aliases of one another. "Replace
Switch with Strategy" is a genuine alias, common when the final design has a
Strategy object rather than a subtype hierarchy. "Push Branches Down" is a local
phrase some teams use for the same move, but it is less exact because it hides
the condition that the branches must represent stable variants.

Engineering judgement. Treat these aliases as clues, not proof. A switch can be
bad because it is large, because it mixes policy with plumbing, because it
duplicates another switch, or because it is in the wrong module. Polymorphism is
only the right target when the branches name different kinds of the same
concept and each kind owns different behavior under the same question.

## 2. Problem and context

The problem begins with a conditional that asks the same object, value, or type
code what kind it is, then runs different behavior for each answer. At first the
conditional is small. A billing rule checks whether a customer is trial, paid,
or enterprise. A renderer checks whether a block is a paragraph, table, or
image. A workflow checks whether an event is approved, rejected, or pending.
The code works, and the branch reads naturally.

The design pressure appears when that branch becomes a family rather than a
local exception. The same type code is checked in pricing, validation,
formatting, persistence, export, logging, and permission code. Every new variant
demands edits in several places. A developer adding a new branch must search for
all matching conditionals and remember which ones must change. One missed branch
becomes a runtime bug that no compiler can see, because the compiler sees a
legal default branch or a legal fallthrough path.

Replace Conditional with Polymorphism changes the axis of extension. Instead of
one owner asking "which kind are you?" and deciding all behavior in a central
conditional, each kind implements the behavior under a shared operation. The
caller sends the same message to every variant. The runtime implementation
answers according to its type.

Context matters. The pattern fits when the conditional selects behavior, not
data. It fits when the set of variants has names that domain experts recognize.
It fits when the behavior belongs with the variant and is likely to grow there.
It fits when several call sites repeat the same kind check. It does not fit a
single guard clause, a range check, a feature flag, a data table, or a business
rule that users edit at runtime.

The smell is not the mere presence of `if`. Conditional logic is a core
language feature. The smell is a conditional that repeats a taxonomy and makes
one module act as a switchboard for behavior owned by several variants.

A good working test is the "same question" test. If every branch can be
rewritten as an answer to one sentence, the refactoring has a fair target. "How
much shipping does this option charge?" fits. "What should the checkout process
do next?" may fit after the workflow states are named. "What random work is
needed for this code path?" does not fit. The first two can become methods on
variants. The last one is a sign that responsibilities are mixed and the branch
body needs decomposition before any hierarchy appears.

Another useful test is the "forgotten branch" test. Ask what happens when a new
variant is added. If the answer is "search for all switches over this code,"
the design is asking developers to maintain a manual index. If the answer is
"add one implementation and the compiler points at missing operations," the
polymorphic form is likely to lower risk. If the answer is "edit one table,"
the table may already be the better design.

## 3. Forces

Engineering judgement. This dimension weighs trade-offs. It is not a sourced
claim about one named system.

- **Coupling.** Favoured. Callers depend on a common operation instead of on
  every concrete branch. A module that adds a new variant can often own its own
  behavior.
- **Consistency.** Favoured when the common operation is well named. Every
  variant must answer the same question. The compiler or test suite can reveal a
  missing method earlier than a forgotten branch in a distant switch.
- **Cognitive load.** Sacrificed at first read. A reader no longer sees every
  branch in one function. They must navigate to the concrete implementation
  selected at runtime.
- **Latency.** Usually neutral. Dynamic dispatch, trait dispatch, or a function
  call is rarely visible next to the work inside the branch. In a tight inner
  loop, the lost inlining and branch prediction profile can matter.
- **Operability.** Mixed. The branch name may disappear from the source path, so
  logs and traces need the concrete type or strategy name. Once that label is
  present, per-variant metrics become clearer than a monolithic branch counter.
- **Cost of change.** Favoured when adding a new variant. Sacrificed when
  changing the common operation, because every variant implementation must move
  together.
- **Team topology.** Favoured when separate teams own separate variants. Harmed
  when one team owns all variants and the indirection scatters related edits
  across many files.
- **Local reasoning.** Sacrificed for global extensibility. The old conditional
  is easy to inspect in one place. The polymorphic form is easier to extend
  without editing that place.
- **Data evolution.** Sacrificed when variants are stored as raw strings in a
  database or controlled by user configuration. Polymorphism wants code-owned
  variants. Data-owned variants often want a table, rule engine, lookup map, or
  interpreter.

The pattern favours extension by adding a type or implementation. It sacrifices
the ability to see all outcomes in one procedure. That is the central bargain.

## 4. Applicability and non-applicability

Reach for Replace Conditional with Polymorphism when the following conditions
hold.

- A conditional branches on a stable kind, type code, status, class, role,
  command, event type, or protocol variant.
- The same branch shape appears in more than one place, or one branch body has
  grown large enough to deserve a named home.
- Each branch answers the same operation in a different way, such as `price`,
  `validate`, `render`, `apply`, `advance`, or `authorize`.
- A new variant should be added without opening a shared switch owned by another
  team.
- The variant has enough behavior to deserve an object, enum member with
  methods, trait implementation, protocol conformer, or strategy function.
- Tests would become clearer if each variant could be exercised through the
  same contract.
- The existing conditional keeps pairing data and behavior by convention, and
  bugs come from adding one without the other.

Do not apply it in these cases.

- **One branch is a guard clause.** A guard rejects invalid input or exits early.
  It is not a taxonomy. Leave it as a guard or extract a predicate.
- **The condition is a numeric range.** Taxes, discounts, grades, and rate bands
  often change by threshold. A table or range object reads better than one class
  per threshold.
- **The rule is business-editable data.** If operations, analysts, or customers
  change the rule without a deploy, use a rule table, decision table, workflow
  engine, policy object fed by data, or interpreter.
- **There is one use and no second use in sight.** A single clear conditional is
  cheaper than a new hierarchy. Wait until change proves the axis matters.
- **Branches do not share the same question.** If one branch sends email, one
  branch calculates price, and one branch audits security, the conditional is
  mixing responsibilities. Decompose the conditional first.
- **The set is closed and tiny, and the language has exhaustive matching.** Rust
  `match` over an enum, Swift `switch` over an enum, and TypeScript discriminated
  unions can give stronger compile-time coverage than subtype dispatch.
- **The branch is selecting data, not behavior.** A map from code to label, URL,
  color, or threshold should stay data.
- **The variant identity crosses a persistence boundary as a string.** Do not
  build a class hierarchy until parsing, validation, migration, and unknown
  values are handled. A type object or registry may be a better interim shape.
- **The variant behavior is security-sensitive and third-party code can provide
  variants.** A plugin strategy may be right, but it needs trust boundaries,
  capability checks, and sandboxing. The refactoring alone does not supply them.
- **The conditional is already the clearest audit artifact.** Compliance code
  sometimes benefits from a single explicit decision table reviewed by non-code
  stakeholders. Polymorphism can hide the policy across files.

## 5. Structure

The participants are roles, not mandatory class names.

- **Client.** The code that needs a result such as a price, rendered fragment,
  migration effect, workflow transition, or authorization decision. In the final
  design it calls one operation and does not branch on the variant.
- **Variant abstraction.** The interface, abstract class, protocol, base class,
  trait, or function type that names the operation all variants must answer.
- **Concrete variant.** One implementation for one domain kind. It owns the code
  that used to live in the matching conditional branch.
- **Variant selector.** The code that creates, parses, loads, or receives the
  correct concrete variant. This participant may be a constructor, parser,
  dependency injection container, registry, ORM materializer, or factory. The
  refactoring does not remove selection. It moves selection to the edge.
- **Common data.** Data every variant needs. It belongs on the abstraction or in
  a context object passed to the operation.
- **Variant data.** Data only one variant needs. It belongs on that concrete
  variant, not in nullable fields on a shared record.

The key relationship is inversion of the old dependency. Before the refactoring
the client knew every variant name. After the refactoring the client knows the
abstraction. Each variant knows its own behavior. The selector may still know
all concrete variants, but that knowledge is isolated at construction or parse
time rather than repeated across business operations.

Do not confuse this with removing all conditionals. Most systems still have one
conditional at the boundary where an external value becomes an internal variant.
That boundary branch is acceptable when it is the only branch and all later
behavior dispatches polymorphically.

## 6. ASCII structure diagram

```text
Before

  +===============================+
  |          Client               |
  |===============================|
  | + amountFor(account)          |
  |                               |
  | if account.kind == "trial"    |
  | if account.kind == "paid"     |
  | if account.kind == "enterprise"|
  +===============================+
                  |
                  v
  +===============================+
  | Account record                |
  | kind, seats, usage, discount  |
  +===============================+

After

  +===============================+
  |          Client               |
  |===============================|
  | + amountFor(plan: Plan)       |
  |     return plan.amount(ctx)   |
  +===============+===============+
                  |
                  v
  +===============================+
  |       Plan abstraction        |
  |===============================|
  | + amount(ctx): Money          |
  +===============+===============+
                  ^
                  |
        +=========+==========+================+
        |                    |                |
  +=============+     +=============+   +=============+
  | TrialPlan   |     | PaidPlan    |   |EnterprisePlan|
  | amount(ctx) |     | amount(ctx) |   | amount(ctx)  |
  +=============+     +=============+   +=============+

  +===============================+
  | Variant selector              |
  | parse kind, create Plan       |
  +===============================+
```

## 7. Dynamics

At runtime the client no longer asks for the variant and then chooses behavior.
It receives an object already shaped as the variant and calls the common
operation. The only place that still branches is the selector at the input edge.

```text
Parser           Variant selector       Client              Concrete variant
  |                     |                   |                       |
  |=> raw kind ========>|                   |                       |
  |                     |=> choose class ==>|                       |
  |                     |=> new PaidPlan ==========================>|
  |                     |<================== plan ==================|
  |<==================== plan =============|                       |
  |                                         |                       |
  |==================== run use case ======>|                       |
  |                                         |=> amount(context) ===>|
  |                                         |<= Money =============|
  |<==================== result ============|                       |
```

The selector can be explicit, as in a parser with a `switch` over a wire code.
It can also be implicit, as in a dependency injection container, ORM type map,
plugin loader, or language runtime that dispatches a method call by concrete
type. The health of the design depends on where the selection sits. Selection at
the edge is normal. Selection repeated in the middle of many workflows is the
smell this refactoring removes.

A second dynamic appears when the variant changes state. A workflow may start as
`Draft`, then become `Submitted`, then `Approved`. In that form the operation
returns the next variant rather than mutating a type code in place. That is a
bridge from this refactoring to the State pattern.

```text
Workflow         Draft state          Submitted state       Approved state
  |                  |                     |                     |
  |=> submit() =====>|                     |                     |
  |<= Submitted =====|                     |                     |
  |                                        |                     |
  |=> approve() ==========================>|                     |
  |<= Approved ============================|                     |
  |                                                              |
  |=> archive() ================================================>|
  |<= archived result ===========================================|
```

## 8. Implementation variants

**Subclass per variant.** The classical object-oriented form. A base class or
interface declares the operation and each subtype supplies one branch. It suits
Java, C#, Kotlin, Swift class hierarchies, and older frameworks that publish
extension points through inheritance. It gives a visible API contract, but it
can create many small classes.

**Strategy object.** The owning data stays in one class, and the variable
behavior moves to a separate object. Use this when the variant is one policy
among several properties rather than the identity of the whole object. It
composes better than inheritance and is easier to swap in tests.

**Enum with behavior.** Java and Swift enums can attach behavior to each case;
Rust enums can use exhaustive `match` inside methods. This keeps a closed set in
one file while still moving the branch behind a named operation. It is strong
when the set is closed and small. It is weak when downstream packages need to
add variants.

**Discriminated union plus exhaustive function.** TypeScript and Rust often
prefer a closed union with exhaustive matching. Strictly, this is not
polymorphism, but it is a competitor that solves the same missed-branch problem
for closed sets. Choose it when adding variants requires editing central code
anyway and compile-time exhaustiveness matters more than open extension.

**Function table.** A map from variant code to function replaces a switch. It is
polymorphism in a small functional form. It suits simple operations where a full
object would carry no state. It does not suit variants that need several related
operations unless each table is kept in sync.

**Type object.** A row, config object, or metadata object represents the variant
and supplies behavior by composing smaller functions. This is useful when the
variant set is partly data-driven but still needs guarded behavior.

**Visitor.** Visitor is the opposite axis. It keeps variants stable and lets new
operations be added outside the variant classes. Replace Conditional with
Polymorphism favours adding variants; Visitor favours adding operations. When
both axes change often, neither is free.

**State pattern.** State applies the same move to conditionals over lifecycle
state, with the extra rule that operations may return or install the next state.
Use State when the type code changes during the object's life.

**Null object or special case.** A branch that exists only to handle absence can
move into a Special Case object. Fowler's catalog names Introduce Special Case
for this move (https://refactoring.com/catalog/introduceSpecialCase.html,
verified 2026-08-02). It is a narrower refactoring than replacing a whole
taxonomy.

## 9. Known production uses

**Spring MVC, `HandlerAdapter`.** Spring Framework documents `HandlerAdapter` as
an SPI that allows `DispatcherServlet` to access installed handlers through an
interface without code specific to any handler type
(https://docs.spring.io/spring-framework/docs/current/javadoc-api/org/springframework/web/servlet/HandlerAdapter.html,
verified 2026-08-02). The Spring reference manual says the adapter helps
`DispatcherServlet` invoke a mapped handler regardless of how that handler is
actually invoked
(https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-servlet/special-bean-types.html,
verified 2026-08-02). This is a production framework use of polymorphism to
avoid a central servlet branch for every controller style.

**Django migrations, `Operation`.** Django's migration documentation says
migration files are composed of `Operation` objects and lists built-in operation
classes such as `CreateModel`, `AlterField`, `RenameField`, and `RunPython`
(https://docs.djangoproject.com/en/6.1/ref/migration-operations/, verified
2026-08-02). Django's source defines a base `Operation` with methods such as
`state_forwards`, `database_forwards`, and `database_backwards`, each requiring
subclasses to provide the behavior
(https://github.com/django/django/blob/main/django/db/migrations/operations/base.py,
verified 2026-08-02). The migration executor can process a list of operations
through this contract rather than branching on every operation class.

**Python standard library, `pathlib`.** Python documents `pathlib` as classes
for filesystem paths with semantics appropriate for different operating systems
(https://docs.python.org/3.14/library/pathlib.html, verified 2026-08-02). The
same page documents `Path` as a class that creates either `PosixPath` or
`WindowsPath`, and documents pure and concrete path subclasses for POSIX and
Windows path semantics. This is production library code using variants to hold
operating-system path behavior rather than forcing each caller to branch on the
platform before path operations.

Engineering judgement. These examples are not claims that the maintainers
performed this exact refactoring step during a recorded commit. They are named
production designs that have the shape produced by the refactoring: a central
workflow calls a common operation and variant-specific behavior lives behind
that operation.

## 10. Consequences

Engineering judgement. These consequences are design effects to weigh in a
codebase, not sourced measurements.

Positive.

- Branch bodies acquire names. `PaidPlan.amount` explains intent better than
  case three inside a pricing switch.
- New variants can often be added by adding a new implementation and updating
  the selector, rather than editing every use case.
- Tests can run the same contract against every variant and reveal missing
  behavior.
- Variant-only data moves nearer to the code that uses it, which removes shared
  records full of nullable fields.
- Callers become simpler because they send one message and stop knowing every
  kind.
- Ownership can follow the domain. A payments team can own payment method
  variants; a storage team can own storage backend variants.
- Observability can improve when the concrete variant name becomes a metric
  label on the common operation.

Negative.

- Reading all behavior for an operation now means visiting several files or enum
  cases.
- Adding a new common operation is expensive. Every variant must implement it,
  and some variants may not have a natural answer.
- A selector still exists. If it is hidden or duplicated, the system has both
  indirection and branching.
- Too many tiny classes can bury the domain model in ceremony.
- Debugging requires knowing the runtime variant. Without logs, traces, or a
  debugger, the source path can be opaque.
- Serialization and database storage become more complex if the variant used to
  be a plain string field.
- Security review may become harder when third-party plugins can supply
  variants.

## 11. Failure modes and misuse

Engineering judgement. The triples below describe symptoms a team can observe.

**Symptom.** A new variant works in one workflow but fails in another with a
default result, skipped validation, or "unknown type" error. **Cause.** The
original conditional was duplicated and only one copy was replaced. **Fix.**
Search for every branch on the discriminator, replace the full family, and add a
contract test that runs all known variants through all common operations.

**Symptom.** A directory fills with one-method classes named after codes, and
developers open five files to read what used to be one clear table. **Cause.**
The condition selected data or constants, not behavior. **Fix.** Collapse the
classes into a lookup table, enum data, or configuration object.

**Symptom.** A variant method throws "not supported" for several operations.
**Cause.** The abstraction is too broad, and not every variant answers the same
question. **Fix.** Split the abstraction by capability, apply Interface
Segregation, or keep the exceptional branch at a higher level.

**Symptom.** Production metrics show a sudden rise in `DefaultPlan` or
`UnknownOperation` after a deploy. **Cause.** The selector has a fallback that
swallows an unknown discriminator. **Fix.** Fail closed during parsing, log the
raw discriminator, and require an explicit migration for new wire values.

**Symptom.** A security incident involves a plugin class whose method ran inside
the host process with broad privileges. **Cause.** The refactoring turned a
branch into an open extension point without a trust model. **Fix.** Treat plugin
implementations as untrusted code, restrict capabilities, verify package
provenance, and validate returned objects.

**Symptom.** A bug fix needs the same edit in twelve variant classes. **Cause.**
Common behavior was pushed down with the branch-specific behavior. **Fix.** Pull
the shared part back into the abstraction, a template method, or a helper used
by all variants.

**Symptom.** A performance profile shows millions of indirect calls in a tight
loop after a refactor. **Cause.** A branch that the compiler previously
optimized became dynamic dispatch on a hot path. **Fix.** Measure first, then
consider sealed classes, enum matching, inlining by generics, or moving dispatch
outside the loop.

**Symptom.** A persisted record cannot be read after a class rename. **Cause.**
The system stored concrete class names as variant identity. **Fix.** Store a
stable wire code, map it to implementations at the boundary, and version the
mapping.

## 12. Trade-off matrix

<table>
<thead>
<tr>
<th>Force</th>
<th>Replace Conditional with Polymorphism</th>
<th>Strategy</th>
<th>State</th>
<th>Visitor</th>
<th>Decision table</th>
<th>Pattern matching</th>
</tr>
</thead>
<tbody>
<tr>
<td>Adding a variant</td>
<td>Strong when extension is open</td>
<td>Strong when wired by config</td>
<td>Strong for lifecycle states</td>
<td>Weak, every visitor changes</td>
<td>Strong if variant is data</td>
<td>Medium, central match changes</td>
</tr>
<tr>
<td>Adding an operation</td>
<td>Weak, every variant changes</td>
<td>Medium, new strategy type</td>
<td>Weak, every state changes</td>
<td>Strong, add a visitor</td>
<td>Medium, add a column or action</td>
<td>Medium, add a function</td>
</tr>
<tr>
<td>Local readability</td>
<td>Medium, behavior is spread out</td>
<td>Medium</td>
<td>Medium</td>
<td>Low at first read</td>
<td>High for tabular rules</td>
<td>High in one function</td>
</tr>
<tr>
<td>Coupling</td>
<td>Low from caller to variant</td>
<td>Low from caller to strategy</td>
<td>Low from context to states</td>
<td>Higher, visitor knows variants</td>
<td>Low to code, higher to data schema</td>
<td>Higher to variant list</td>
</tr>
<tr>
<td>Runtime data changes</td>
<td>Poor unless selector reads data</td>
<td>Medium</td>
<td>Poor</td>
<td>Poor</td>
<td>Strong</td>
<td>Medium</td>
</tr>
<tr>
<td>Exhaustiveness checks</td>
<td>Depends on language</td>
<td>Depends on wiring tests</td>
<td>Depends on state tests</td>
<td>Strong in sealed hierarchies</td>
<td>Data validation needed</td>
<td>Strong in Rust and Swift enums</td>
</tr>
<tr>
<td>Operability</td>
<td>Needs variant labels</td>
<td>Needs strategy labels</td>
<td>Needs state labels</td>
<td>Needs operation labels</td>
<td>Tables are auditable</td>
<td>Branch labels visible</td>
</tr>
<tr>
<td>Team topology</td>
<td>Good for variant owners</td>
<td>Good for policy owners</td>
<td>Good for workflow owners</td>
<td>Good for operation owners</td>
<td>Good for analyst-owned rules</td>
<td>Good for one code owner</td>
</tr>
<tr>
<td>Performance</td>
<td>Usually neutral</td>
<td>Usually neutral</td>
<td>Usually neutral</td>
<td>More calls</td>
<td>Table lookup</td>
<td>Often compiler-friendly</td>
</tr>
<tr>
<td>Best fit</td>
<td>Stable variant behavior</td>
<td>Swappable policy</td>
<td>Object lifecycle</td>
<td>Many operations over stable variants</td>
<td>Business rules as data</td>
<td>Closed algebraic variants</td>
</tr>
</tbody>
</table>

Reading of the table. This refactoring wins when variants change more often
than operations. Visitor wins when operations change more often than variants.
Decision tables win when non-developers own the rule values. Pattern matching
wins when the language can prove exhaustiveness over a closed set.

## 13. Related and incompatible patterns

- **Strategy.** Often the final design. A conditional choosing an algorithm can
  become a Strategy interface with one implementation per branch. Strategy is
  better than subclassing when the behavior is one replaceable policy on a
  larger object.
- **State.** A close relative for conditionals over lifecycle. If the type code
  changes as operations run, the variants are states and transitions need to be
  part of the model.
- **Template Method.** Composes with the refactoring when the common algorithm
  stays in the base class and the variant-specific steps move to hooks.
- **Introduce Special Case.** A branch for null, missing, anonymous, default, or
  guest behavior can become a Special Case object rather than a whole hierarchy.
- **Decompose Conditional.** Often comes first. If the condition is not yet
  understandable, extract predicates and branch bodies before deciding whether
  polymorphism is earned.
- **Consolidate Conditional Expression.** A sibling move in the opposite
  direction. When several checks all lead to the same outcome, combine them
  before creating variants.
- **Remove Subclass.** Incompatible as a final direction. Use Remove Subclass
  when subclasses no longer carry behavior worth preserving.
- **Visitor.** A trade-off partner. Use Visitor when the variant set is stable
  and new operations arrive often.
- **Factory Method or Factory Function.** Commonly used at the selector boundary
  to convert a wire code or configuration value into the right variant.
- **Command.** Useful when each branch represents an action request. Replacing
  a command switch with command objects can be the same refactoring under a more
  specific name.

## 14. Refactoring path in and out

Introducing the refactoring.

1. Identify the discriminator. Name the field, enum, string, status, class
   check, or tag that drives the conditional.
2. Find sibling conditionals over the same discriminator. If there are several,
   choose one operation as the first slice and leave notes for the others.
3. Decompose the conditional so each branch body is already in a named function.
   This reduces risk and gives each future method a name.
4. Create a variant abstraction with the operation represented by the
   conditional. Keep the signature narrow.
5. Create one concrete variant for each branch. Move the branch body into the
   matching implementation.
6. Add a selector that converts existing records or input values into variants.
   Keep this near parsing, loading, or object construction.
7. Replace the original conditional with a call to the common operation.
8. Run the old tests. Then add one contract test that all variants must pass.
9. Remove the old discriminator from inner code. If persistence still needs it,
   keep it at the boundary as a stable wire code.
10. Repeat for the next duplicated conditional only after the first operation is
    stable.

Working in small steps matters. Fowler describes refactoring as a sequence of
small behavior-preserving transformations on his book page
(https://www.martinfowler.com/books/refactoring.html, verified 2026-08-02).
That principle applies here because this refactoring changes structure more
than behavior.

When the old discriminator is persisted, split the work into two tracks. The
storage track keeps the stable code and migration rules. The domain track maps
that code to a variant before business behavior runs. This split avoids a common
mistake: replacing a database column with a concrete class name. The column is a
public compatibility surface. The implementation class is private code. Keeping
those identities separate lets the team rename classes, merge variants, or split
variants later without rewriting old rows.

When several operations branch on the same discriminator, move one operation
first and stop. Review whether the resulting abstraction still feels natural.
If the second operation wants a very different set of variants, the taxonomy was
probably borrowed from storage or reporting rather than from behavior. In that
case, continuing the refactor will create an abstraction that every method has
to fight.

Removing the pattern.

1. Count variants and operations. If only one variant remains, inline the class
   or implementation.
2. If each variant returns constants, replace classes with a table or enum data.
3. If the set is closed and the language has exhaustive matching, migrate to an
   enum or union one operation at a time.
4. If operations change more often than variants, introduce Visitor and move one
   operation out of the variants.
5. If subclassing is the burden, replace subclasses with Strategy objects or
   functions, then remove the hierarchy.
6. Keep the selector tests during the migration. Most regressions happen where
   wire values map to internal variants.

## 15. Testing and verification

Engineering judgement. The testing plan depends on how the variants are loaded
and how much of the set is open to plugins.

Test the behavior before the refactoring with characterization tests. Capture
each branch using inputs that force that branch. These tests should survive the
move and prove behavior did not change.

After the move, add contract tests for the variant abstraction. The test should
describe what every variant must do, with fixture data supplied by each concrete
variant. In object-oriented test suites this is often an abstract test case. In
TypeScript or Python it can be a loop over a list of variant factories.

Add selector tests. Given each stable wire code, database value, or config
value, the selector must produce the expected variant. Also test unknown values.
Unknown values should fail loudly unless there is a documented compatibility
reason to keep an explicit `Unknown` variant.

Add parity tests while migrating. For a short period, run the old conditional
and the new polymorphic operation with the same input, then assert equal output.
Delete the old path once parity is proven. Do not keep dual paths longer than
needed, because they will diverge.

Use mutation testing where available. A useful mutant deletes one variant method
or changes the selector mapping. If tests still pass, the suite is not covering
the polymorphic contract.

Use property tests when branches encode algebraic behavior. For example,
discount variants should never return a negative final price, and workflow
states should reject invalid transitions.

What became easier. Each variant can be tested directly with small fixtures.
The caller can be tested with a fake variant that records the call. The selector
can be tested without running the operation.

What became harder. End-to-end tests must now assert which variant was selected
or which behavior resulted. A debugger or trace may be needed to connect a
runtime object to the implementation file.

## 16. Observability signals

Engineering judgement. The pattern is visible in production only if the variant
is visible in telemetry.

Log the variant at the selector boundary. Include the stable wire code and the
internal variant name. Do not log raw user input after parsing if it can contain
private data.

Add a counter for calls to the common operation labelled by variant. A healthy
system shows the expected distribution for the current customer mix, traffic
shape, and configuration. A sudden new label or a sudden rise in `Unknown`
points to a mapping or rollout fault.

Add an error counter labelled by variant and error class. This localizes faults
that the old switch might have hidden behind one generic operation name.

Add a latency histogram labelled by variant when the operation does input,
output, encryption, database calls, or expensive computation. Variant-specific
latency tells the team where the cost lives.

For workflows, expose a transition counter from one state variant to the next.
A healthy dashboard shows allowed transitions. A failing one shows impossible
transitions, repeated retries from the same state, or a state that never exits.

For plugin variants, record package name, version, and trust tier as deployment
metadata, not as high-cardinality labels on every request. Use a low-cardinality
variant label on hot metrics and keep detailed package identity in logs or
traces sampled at a rate the system can afford.

The main operational smell is an unlabelled polymorphic call. When every variant
shares the same metric name with no variant tag, incidents become harder because
the source no longer contains the branch that would have named the path.

## 17. Security and privacy implications

Engineering judgement. The refactoring is security-neutral when all variants
ship in one trusted binary and process the same data under the same privileges.
Security concerns appear when variant selection crosses a trust boundary.

Treat the discriminator as untrusted input. A request body, database row,
message topic, or plugin manifest that names a variant must be validated before
it selects code. Unknown values should fail closed or map to a deliberately
limited `Unknown` variant.

Do not store concrete class names as public wire values. Class names reveal
implementation details and make refactors compatibility events. Store stable
codes and map them to implementations internally.

Plugin variants expand the supply-chain attack surface. The host application
calls plugin code through a trusted abstraction, but the abstraction does not
make the implementation trustworthy. Restrict file, network, credential, and
process access according to the plugin's job. Verify package provenance where
the ecosystem supports it.

Authorization must stay outside variant code unless the variant is the policy
itself. A dangerous misuse is selecting a variant first and letting it decide
whether it was allowed to run. Check permission before constructing or invoking
high-privilege variants.

Privacy risk often comes from observability. Variant names can encode customer
tier, region, health status, or fraud-review status. If a variant label can be
linked to a person or account, apply the same retention and access policy used
for other attributable operational data.

For deserialization, never instantiate arbitrary classes named by input. Use an
allowlist mapping from stable codes to constructors. This keeps the selector as
a controlled boundary rather than an object creation gadget.

## Code examples

The examples are intentionally small. Go shows the interface form without
inheritance. Python shows abstract base classes with a selector at the edge.
TypeScript shows a strategy interface and a functional alternative.

### Go

```go
package main

import "fmt"

type ShippingQuote interface {
	CentsFor(grams int) int
}

type PostalQuote struct{}

func (PostalQuote) CentsFor(grams int) int {
	return 399 + grams/10
}

type CourierQuote struct{}

func (CourierQuote) CentsFor(grams int) int {
	return 799 + grams/5
}

type PickupQuote struct{}

func (PickupQuote) CentsFor(_ int) int {
	return 0
}

type Checkout struct {
	shipping ShippingQuote
}

func (c Checkout) TotalCents(weights []int, subtotalCents int) int {
	grams := 0
	for _, weight := range weights {
		grams += weight
	}
	return subtotalCents + c.shipping.CentsFor(grams)
}

func main() {
	checkout := Checkout{shipping: CourierQuote{}}
	fmt.Println(checkout.TotalCents([]int{100, 250}, 1200))
}
```

### Python

```python
from abc import ABC, abstractmethod


class ReviewState(ABC):
    @abstractmethod
    def can_publish(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def label(self) -> str:
        raise NotImplementedError


class Draft(ReviewState):
    def can_publish(self) -> bool:
        return False

    def label(self) -> str:
        return "draft"


class Approved(ReviewState):
    def can_publish(self) -> bool:
        return True

    def label(self) -> str:
        return "approved"


def state_from_code(code: str) -> ReviewState:
    states = {
        "draft": Draft,
        "approved": Approved,
    }
    try:
        return states[code]()
    except KeyError as exc:
        raise ValueError(f"unknown review state: {code}") from exc


def publish_button(state: ReviewState) -> str:
    return "enabled" if state.can_publish() else "disabled"


if __name__ == "__main__":
    state = state_from_code("approved")
    print(state.label(), publish_button(state))
```

### TypeScript

```typescript
interface DiscountPolicy {
  amountCents(subtotalCents: number): number;
}

class NoDiscount implements DiscountPolicy {
  amountCents(_subtotalCents: number): number {
    return 0;
  }
}

class LoyaltyDiscount implements DiscountPolicy {
  amountCents(subtotalCents: number): number {
    return Math.floor(subtotalCents * 0.1);
  }
}

class Cart {
  constructor(private readonly discount: DiscountPolicy) {}

  totalCents(subtotalCents: number): number {
    return subtotalCents - this.discount.amountCents(subtotalCents);
  }
}

const cart = new Cart(new LoyaltyDiscount());
console.log(cart.totalCents(5000));

type DiscountFunction = (subtotalCents: number) => number;

const loyalty: DiscountFunction = (subtotalCents) =>
  Math.floor(subtotalCents * 0.1);

console.log(5000 - loyalty(5000));
```

## 18. References

- Martin Fowler. *Refactoring. Improving the Design of Existing Code*. First
  edition. Addison-Wesley, 1999. Chapter "Simplifying Conditional Expressions."
- Martin Fowler, with Kent Beck. *Refactoring. Improving the Design of Existing
  Code*. Second edition. Addison-Wesley, 2018. Catalog entry "Replace
  Conditional with Polymorphism."
- Martin Fowler. "Replace Conditional with Polymorphism." Refactoring catalog.
  https://refactoring.com/catalog/replaceConditionalWithPolymorphism.html.
  Verified 2026-08-02.
- Martin Fowler. "Changes for the 2nd Edition of Refactoring."
  https://martinfowler.com/articles/refactoring-2nd-changes.html. Verified
  2026-08-02.
- Martin Fowler. "Refactoring. Improving the Design of Existing Code."
  https://www.martinfowler.com/books/refactoring.html. Verified 2026-08-02.
- Martin Fowler. "Introduce Special Case." Refactoring catalog.
  https://refactoring.com/catalog/introduceSpecialCase.html. Verified
  2026-08-02.
- Spring Framework API. `org.springframework.web.servlet.HandlerAdapter`.
  https://docs.spring.io/spring-framework/docs/current/javadoc-api/org/springframework/web/servlet/HandlerAdapter.html.
  Verified 2026-08-02.
- Spring Framework Reference. "Special Bean Types."
  https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-servlet/special-bean-types.html.
  Verified 2026-08-02.
- Django documentation. "Migration Operations."
  https://docs.djangoproject.com/en/6.1/ref/migration-operations/. Verified
  2026-08-02.
- Django source. `django/db/migrations/operations/base.py`.
  https://github.com/django/django/blob/main/django/db/migrations/operations/base.py.
  Verified 2026-08-02.
- Python documentation. "`pathlib`. Object-oriented filesystem paths."
  https://docs.python.org/3.14/library/pathlib.html. Verified 2026-08-02.
