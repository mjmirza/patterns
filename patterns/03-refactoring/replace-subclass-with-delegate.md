---
name: Replace Subclass with Delegate
slug: replace-subclass-with-delegate
family: 03-refactoring
category: Dealing with Inheritance
aliases: [Replace Inheritance with Delegation, Replace Type Code with State or Strategy]
first_described: "Fowler 2018"
maturity: canonical
related: [replace-superclass-with-delegate, replace-conditional-with-polymorphism, remove-subclass, strategy, state, decorator]
incompatible_with: [collapse-hierarchy]
verified: 2026-08-02
---

# Replace Subclass with Delegate

## 1. Name, aliases, and lineage

The canonical name is Replace Subclass with Delegate. Martin Fowler's online
catalog lists the refactoring under that name in the refactoring catalog for
the second edition of *Refactoring* (https://refactoring.com/catalog/replaceSubclassWithDelegate.html,
verified 2026-08-02). The catalog index includes it in the delegation and
dealing-with-inheritance area (https://refactoring.com/catalog/index.html,
verified 2026-08-02). Fowler's book lineage is Martin Fowler, *Refactoring.
Improving the Design of Existing Code*, 2nd edition, Addison-Wesley, 2018,
chapter 12, "Dealing with Inheritance."

The older, broader name is Replace Inheritance with Delegation. JetBrains uses
that name for an IntelliJ IDEA refactoring that removes a class from an
inheritance hierarchy and routes selected parent members through a delegate
object (https://www.jetbrains.com/help/idea/replace-inheritance-with-delegation.html,
verified 2026-08-02). That tool name is broader because it covers replacing a
superclass link too. This entry is narrower. It covers the case where a base
class has subclasses representing a variation, and that variation is moved into
one or more delegate objects held by the base class.

The related GoF pattern names are Strategy and State. The Gang of Four catalog
describes Strategy as encapsulating interchangeable algorithms and State as
letting an object alter behavior when its internal state changes, in Erich
Gamma, Richard Helm, Ralph Johnson, and John Vlissides, *Design Patterns.
Elements of Reusable Object-Oriented Software*, Addison-Wesley, 1994, chapter
5, "Behavioral Patterns." Replace Subclass with Delegate is the refactoring
path. Strategy or State is often the destination shape.

Judgement. In review, the most useful phrase is often "move this axis out of
the subclass hierarchy." The catalog name is useful when recording the change
in a design note or pull request because it points to a known sequence of small
edits.

## 2. Problem and context

A class hierarchy has started to carry more variation than inheritance can
represent cleanly. The early version looked natural. `Order` had
`PriorityOrder`. `Account` had `BusinessAccount`. `Report` had
`CsvReport`. The subclass held the special behavior and the rest stayed in the
base class. That design can work while there is one stable axis of variation.

The pressure changes when another independent axis arrives. Priority orders now
also vary by shipping region. Business accounts now also vary by tax treatment.
Reports now vary by output format and by access policy. Inheritance can pick
one parent chain. If the hierarchy tries to represent every combination, the
type count grows by multiplication: `PriorityInternationalOrder`,
`PriorityDomesticOrder`, `StandardInternationalOrder`, and so on. If the team
chooses one axis for subclasses and leaves the others as conditionals, the
class becomes half hierarchy and half branch table. Both shapes are hard to
extend.

The code smell is not inheritance by itself. The smell is a subclass whose
identity is one policy choice, one mode, one temporary state, one pricing plan,
or one customer rule. A reader sees methods that override a small part of the
base algorithm while most behavior remains identical. Tests often mirror the
same shape, with one test class per subclass and repeated setup. Operations
teams may see a different symptom: a new plan, region, or mode requires a new
release because behavior is locked into classes rather than selected from data.

Replace Subclass with Delegate changes the ownership of variation. The base
class becomes a regular class with a field that points at an object representing
the variable behavior. Calls that used to dispatch to an override now dispatch
to that delegate. The client can still ask the main object for the same public
operation, but the reason for variation is no longer encoded in the object's
runtime class.

The context that makes this refactoring fit has four parts. First, the subclass
differs from the base along an axis that can be named as a role, plan, policy,
state, renderer, or calculator. Second, callers should keep thinking in terms
of the main object, not in terms of the variant object. Third, the variation
may need to change over the object's lifetime or combine with another axis.
Fourth, the base class can survive as a concrete type without losing the domain
model.

A useful diagnosis is to ask what would happen if tomorrow's requirement added
one more axis. If the answer is "add another sibling subclass," the hierarchy
may still be fine. If the answer is "add a subclass for every old subclass
times the new option," the hierarchy is modeling a grid as a tree. A tree can
represent taxonomy. It is poor at representing independent choices. Delegation
turns each choice back into a field with a contract.

Another diagnosis is to inspect construction. If every subclass is built in a
single factory switch from a code such as plan, tier, country, or workflow
state, inheritance is already being driven by data. The class name is not the
source of truth. The source of truth is the value that selected the class. In
that situation, moving the selected behavior into a delegate tends to make the
model more honest because the value can be persisted, logged, validated, and
changed without pretending it is a subtype.

## 3. Forces

Judgement. These forces are engineering trade-offs. Their weight depends on
language, runtime, module ownership, and how often the axis changes.

- **Coupling.** The refactoring reduces coupling between clients and subclass
  names. Clients can construct the base type with a delegate or receive it from
  a factory. It increases coupling between the base type and a delegate
  protocol, and between each delegate and the base context it reads.
- **Consistency.** It favours consistency when the delegate interface names the
  whole policy contract. All variants must answer the same questions. It can
  sacrifice consistency if each delegate is handed too much access to the base
  object and starts making private interpretations of shared state.
- **Latency.** It usually adds one extra method call and one extra object
  reference. That cost is small in request or UI code. It can matter inside
  per-item loops, parsers, rendering pipelines, and allocation-heavy paths, so
  measure before moving hot code behind boxed protocols or heap delegates.
- **Memory cost.** It may add one object per host object. A shared stateless
  delegate or enum-like singleton can remove most of that cost. A stateful
  delegate can add memory pressure if millions of host objects each carry a
  separate strategy.
- **Operability.** It favours operability when variant selection becomes data
  that can be logged, traced, counted, and changed by configuration. It hurts
  operability if the selected delegate is invisible and the object's class name
  no longer tells an operator which behavior ran.
- **Team topology.** It favours teams that own separate policy modules. A
  platform team can own the host type and delegate interface while feature
  teams add delegates. It can hurt small teams when a simple one-file subclass
  becomes three files and a factory.
- **Cognitive load.** It lowers cognitive load when subclass multiplication was
  hiding a simple matrix of policy choices. It raises cognitive load for
  readers who must now follow an object graph rather than a class hierarchy.
- **Change cost.** It favours adding and recombining variants. It sacrifices
  the ease of changing the delegate interface after many delegates exist.

The exchange is simple. You give up the apparent neatness of a hierarchy in
return for explicit policy objects that can be selected, combined, tested, and
observed.

## 4. Applicability and non-applicability

Reach for Replace Subclass with Delegate when these conditions hold.

- A subclass represents a role, policy, plan, mode, or state rather than a true
  subtype with durable identity.
- The hierarchy is growing by combinations, such as region times plan, channel
  times price rule, or format times access rule.
- A variant needs to change after construction. An object can change its
  delegate safely; it cannot change its class in mainstream object-oriented
  languages.
- The subclass overrides a small set of methods and inherits almost everything
  else unchanged.
- Callers are testing or branching on subclass type to recover information that
  could be represented as a named delegate.
- The same variation should be reused by more than one host class.
- You need to select behavior from configuration, tenant data, feature flags,
  or runtime state.
- The current subclass hierarchy blocks a second refactoring such as extracting
  a policy module, introducing a plugin point, or replacing a conditional with
  polymorphism.

Non-applicability. Do not apply this refactoring in these cases.

- **The subclass is a true subtype.** If every instance of the subclass can
  stand wherever the base class is expected and it adds a stable domain concept,
  keep the inheritance. A `SavingsAccount` may be a real account type in the
  domain, not a replaceable interest policy.
- **The hierarchy has one axis, two or three stable leaves, and no pressure to
  combine them.** The delegate adds objects, wiring, and naming work without
  buying change capacity.
- **The subclass changes representation, not behavior.** If fields moved down
  because only one subtype needs them, Push Down Field or Extract Class may be
  enough.
- **The variation is a closed, tiny value choice.** An enum or Replace Subclass
  with Fields can be clearer when behavior is one or two expressions and no
  future plug-in is expected.
- **The base class cannot expose a stable delegate contract.** If each variant
  needs random access to private base internals, extract a smaller object first
  or keep the subclass until the model is clearer.
- **The host object is already too broad.** Moving one branch into a delegate
  can hide the need for Extract Class. If the host owns unrelated data,
  splitting the host may be the better first move.
- **The language favours algebraic data types for this shape.** In Rust,
  Swift, and modern TypeScript, a closed variant set may be better as a tagged
  union or enum with pattern matching.
- **The delegate would be selected through a global service locator.** That
  hides dependencies and makes tests order-dependent. Constructor injection or
  an explicit factory is cleaner.
- **The refactoring is driven by a rule that says composition is always better
  than inheritance.** That rule is too blunt. Inheritance is sound when the
  subtype relation is true and stable.
- **External callers depend on subclass names as a public API.** You may still
  migrate internally, but you need an adapter or compatibility layer before
  deleting the subclasses.

## 5. Structure

The structure has five participants.

- **Host.** The former base class, now concrete. It owns the stable data and
  public operations that clients should continue to call. It holds one or more
  delegate fields.
- **Delegate interface.** The protocol, interface, abstract class, function
  type, or enum contract that captures the variation formerly expressed by
  subclass overrides.
- **Concrete delegate.** One implementation of the variant behavior. It may be
  stateless and shared, or stateful and owned by one host.
- **Context object.** The data the delegate needs in order to answer. Sometimes
  the host passes itself. More often it passes a narrow read-only context to
  avoid giving the delegate full access to host internals.
- **Construction boundary.** The factory, parser, dependency injection binding,
  or migration adapter that chooses which delegate to install.

The key relationship is direction. Client code talks to Host. Host talks to the
delegate interface. Concrete delegates know the interface and any context they
are handed. Clients do not need to know which concrete delegate is present
unless the application exposes that choice as a feature.

The old subclass may remain temporarily as a compatibility wrapper. During the
transition, `PriorityOrder` can extend `Order` while its constructor installs a
`PriorityShippingPolicy`. That wrapper has no behavior of its own. Once callers
stop constructing the subclass, the wrapper can be removed.

## 6. ASCII structure diagram

```text
Before

  +-------------------------------+
  |            Order              |
  |-------------------------------|
  | customerId                    |
  | warehouse                     |
  | +daysToShip()                 |
  | +shippingCharge()             |
  +-------------------------------+
        ^                  ^
        | extends          | extends
        |                  |
  +----------------+  +-------------------+
  | PriorityOrder  |  | InternationalOrder|
  |----------------|  |-------------------|
  | +daysToShip()  |  | +shippingCharge() |
  +----------------+  +-------------------+

After

  +-------------------------------+
  |            Order              |
  |-------------------------------|
  | customerId                    |
  | warehouse                     |
  | shipping: ShippingDelegate    |
  | +daysToShip()                 |
  | +shippingCharge()             |
  +-------------------------------+
          | calls
          v
  +-------------------------------+
  |       ShippingDelegate        |
  |-------------------------------|
  | +daysToShip(ctx): int         |
  | +shippingCharge(ctx): Money   |
  +-------------------------------+
        ^                  ^
        | implements       | implements
        |                  |
  +----------------+  +-------------------+
  | PriorityShip   |  | InternationalShip |
  +----------------+  +-------------------+
```

## 7. Dynamics

At runtime, the client still asks the host object for domain behavior. The host
delegates only the variable part. The host remains responsible for stable
invariants, persistence identity, and transaction boundaries.

```text
Client          Order             ShippingDelegate        Warehouse
  |              |                       |                    |
  | daysToShip() |                       |                    |
  |------------->|                       |                    |
  |              | build narrow context  |                    |
  |              |---------------------->|                    |
  |              |                       | lookup cutoff      |
  |              |                       |------------------->|
  |              |                       |<-------------------|
  |              |<----------------------|                    |
  |<-------------|                       |                    |
  |              |                       |                    |
  | setShippingDelegate(newDelegate)     |                    |
  |------------->|                       |                    |
  |              | future calls use the new policy            |
```

The dynamic benefit is visible when behavior changes without replacing the host.
An order can move from standard shipping to priority shipping after payment. A
workflow can move from draft policy to approval policy after submission. A UI
component can receive a different renderer for a row type without changing the
component's class.

Judgement. The host should not delegate every method. Delegate the axis that
varies. Keep stable identity, validation, persistence mapping, and audit data
in the host unless those concerns are the variation being extracted.

## 8. Implementation variants

**Interface delegate.** The common Java, TypeScript, Go, and Swift shape is a
host with a field typed as an interface or protocol. Each concrete delegate
implements that contract. This is the closest destination when the old
subclasses had several methods.

```typescript
interface ShippingDelegate {
  daysToShip(country: string): number;
  label(): string;
}

class StandardShipping implements ShippingDelegate {
  daysToShip(country: string): number {
    return country === "US" ? 3 : 8;
  }
  label(): string {
    return "standard";
  }
}

class PriorityShipping implements ShippingDelegate {
  daysToShip(country: string): number {
    return country === "US" ? 1 : 4;
  }
  label(): string {
    return "priority";
  }
}

class Order {
  constructor(
    private readonly country: string,
    private shipping: ShippingDelegate,
  ) {}

  daysToShip(): number {
    return this.shipping.daysToShip(this.country);
  }

  shippingLabel(): string {
    return this.shipping.label();
  }
}

const order = new Order("DE", new PriorityShipping());
console.log(`${order.shippingLabel()}:${order.daysToShip()}`);
```

**Function delegate.** When the variation is one operation, a function field is
clearer than a class. Python, Go, TypeScript, Rust, and Swift all support this
shape. The trade-off is weaker naming when the function grows more than one
responsibility.

```python
from dataclasses import dataclass
from typing import Callable

PriceRule = Callable[[int], int]


def regular_price(cents: int) -> int:
    return cents


def loyalty_price(cents: int) -> int:
    return cents - min(500, cents // 10)


@dataclass
class Invoice:
    subtotal_cents: int
    price_rule: PriceRule

    def total_cents(self) -> int:
        return self.price_rule(self.subtotal_cents)


invoice = Invoice(3400, loyalty_price)
print(invoice.total_cents())
```

**Struct delegate in Go.** Go has no implementation inheritance, so this
refactoring is often the entry point from a pseudo hierarchy built with
embedding into an explicit interface field. The host keeps the stable data and
the delegate supplies the variable policy.

```go
package main

import "fmt"

type RenewalPolicy interface {
	NextTermMonths(currentMonths int) int
	Name() string
}

type MonthlyPolicy struct{}

func (MonthlyPolicy) NextTermMonths(currentMonths int) int {
	return 1
}

func (MonthlyPolicy) Name() string {
	return "monthly"
}

type AnnualPolicy struct{}

func (AnnualPolicy) NextTermMonths(currentMonths int) int {
	if currentMonths >= 12 {
		return 12
	}
	return 6
}

func (AnnualPolicy) Name() string {
	return "annual"
}

type Subscription struct {
	currentMonths int
	policy        RenewalPolicy
}

func (s Subscription) NextTermMonths() int {
	return s.policy.NextTermMonths(s.currentMonths)
}

func main() {
	sub := Subscription{currentMonths: 3, policy: AnnualPolicy{}}
	fmt.Printf("%s:%d\n", sub.policy.Name(), sub.NextTermMonths())
}
```

**State delegate.** If the former subclass represented an object state such as
draft, submitted, approved, or cancelled, the delegate should normally be named
as state and be replaceable during a valid transition. That destination is the
State pattern.

**Strategy delegate.** If the former subclass represented an algorithm choice
such as pricing, routing, scoring, rendering, or retry policy, the destination
is Strategy. The delegate should be selected at construction or at a clear
configuration boundary.

**Role object.** A host may have several delegate fields, one per independent
role. For example, `Order` may have `shippingPolicy`, `taxPolicy`, and
`discountPolicy`. This avoids class multiplication, but it creates a new risk:
delegates can disagree. The construction boundary should validate combinations
that the domain forbids.

**Compatibility subclass.** Keep the old subclass name while its constructor
installs the new delegate. This is useful when external callers construct the
subclass. It should be a migration step, not the final design, because a
subclass that exists only to pass one delegate is a thin alias.

**Enum-backed delegate.** A closed variant set can be represented by an enum
with methods. This is compact in Java, Swift, Rust, and TypeScript union code.
It fits small closed sets. It does not fit plug-in systems or tenant-defined
rules.

**Delegate factory.** If selection is data-driven, place the switch or map at
the boundary and return a delegate. Do not spread the selection across the host
methods. The factory is still a branch, but it is one branch at the edge rather
than many branches in the domain object.

**Null or default delegate.** A host may install a standard delegate when no
special behavior applies. This can simplify host methods because they always
call a delegate and never branch on missing state. The cost is silent fallback.
Use a default delegate only when default behavior is a valid domain choice, and
give it a visible key such as `standard` or `none`. Do not use it to hide a
failed lookup.

**Serialized delegate key.** Long-lived hosts need a stable way to rebuild the
delegate after loading from storage. Persist a key or state value, not the
delegate class name. Class names change during refactors and vary by language
or package layout. A versioned domain key lets old records map to new delegate
implementations through a migration table.

**Composite delegate.** Sometimes the old subclass mixed several roles because
the hierarchy forced them together. After extraction, a small composite can
coordinate two delegates behind one interface. Use this when callers need one
policy contract but implementation naturally has smaller parts. Avoid it when
the composite becomes a second host object with hidden state and broad access.

## 9. Known production uses

**UIKit table views, `UITableViewDelegate`.** UIKit's table view class keeps
selection, row height, editing, and display decisions outside the table view
class through the `UITableViewDelegate` protocol. Apple documents that protocol
as managing selections, section headers and footers, deleting and reordering
cells, and other table view actions (https://developer.apple.com/documentation/uikit/uitableviewdelegate/,
verified 2026-08-02). This is a production framework instance of moving
per-screen behavior into a delegate object rather than requiring a distinct
table view subclass for every screen.

**UIKit scene life cycle delegates.** Apple documents the migration from the
app-delegate life cycle to scene-based life cycles as a separation of process
life cycle from UI life cycle, with `UISceneDelegate` and
`UIWindowSceneDelegate` coordinating scene events (https://developer.apple.com/documentation/uikit/transitioning-to-the-uikit-scene-based-life-cycle,
verified 2026-08-02). This is not the Fowler refactoring applied line by line.
It is a production example of extracting a varying responsibility from one
central application object into delegate objects that can exist per scene.

**AndroidX RecyclerView, adapters and layout managers.** AndroidX documents
`RecyclerView.Adapter` as the base class that binds an app-specific data set to
views shown by a `RecyclerView`, and `RecyclerView.setAdapter` as setting an
adapter that provides child views on demand (https://developer.android.google.cn/reference/kotlin/androidx/recyclerview/widget/RecyclerView.Adapter,
verified 2026-08-02; https://developer.android.google.cn/reference/kotlin/androidx/recyclerview/widget/RecyclerView,
verified 2026-08-02). RecyclerView also accepts separate layout manager
objects. The widget therefore delegates data binding and layout policy rather
than encoding each screen shape as a RecyclerView subclass.

**React function components replacing class components.** React documents
`Component` as the base class for class components, states that class
components remain supported, and recommends defining components as functions
for new code (https://react.dev/reference/react/Component, verified
2026-08-02). React's modern API is not a textbook delegate object. It is a
production move away from subclass-based component variation toward functions
and hooks that compose behavior without inheriting from `Component`.

## 10. Consequences

Positive.

- The host type stops multiplying across combinations of independent variation.
- A behavior choice can change at runtime by replacing a delegate.
- The variant can be named, tested, measured, and released in a smaller module.
- Client code can keep using the host's public API while the internal variation
  model changes.
- A delegate can be shared by several host types when the policy is genuinely
  cross-cutting.
- The construction boundary becomes the single place where variant selection is
  tied to tenant data, configuration, feature flags, or persisted state.
- The refactoring often exposes a missing domain word, such as shipping policy,
  tax rule, review state, or rendering adapter.

Negative.

- The object graph becomes less obvious than a class hierarchy in an IDE tree.
- A host can become a bag of delegates if every small branch is extracted.
- The delegate interface becomes a new shared contract. Changing it can touch
  every concrete delegate.
- Delegates that receive the whole host can form tight two-way coupling.
- Debugging by class name becomes weaker because every object may now have the
  same host class.
- Serialization and persistence may need a new field that records which
  delegate should be rebuilt.
- If the old subclasses were public API, the migration needs wrappers or a
  deprecation window.

Judgement. The best outcome is not "no inheritance." The best outcome is one
stable host type and a small number of cohesive delegate contracts, each named
after a real axis of change.

## 11. Failure modes and misuse

Judgement. These are production failure patterns and repair moves. They should
be tested against the local codebase rather than treated as universal law.

**Delegate chosen but not persisted.** Symptom. An object behaves correctly
inside the request that created it, then reverts to default behavior after
reload or worker restart. Cause. The refactoring moved behavior from subclass
type to delegate field, but persistence still stores only host data. Fix. Store
an explicit delegate key, version it, and rebuild the delegate at the repository
or factory boundary.

**Host handed wholesale to every delegate.** Symptom. Delegate code reads and
writes host fields unrelated to the policy, and a small host change breaks many
delegates. Cause. Passing `this` was faster than defining a narrow context.
Fix. Pass a read-only context object or the exact values each delegate needs.

**Delegate explosion.** Symptom. A directory contains dozens of one-method
delegates with names matching config values, and a factory switch as long as
the old subclass list. Cause. The variation is data, not behavior. Fix. Replace
the delegate set with a data table, rule object, or parameterized delegate.

**Anemic host.** Symptom. The host's public methods do nothing except forward
to delegates, and domain invariants are scattered across delegate classes.
Cause. The refactoring moved stable responsibilities out with the variable
ones. Fix. Move identity, invariants, and transaction decisions back into the
host, or Inline Class if the host has no remaining reason to exist.

**Incompatible delegates installed together.** Symptom. A tenant receives a
combination such as "free shipping" plus "remote island surcharge," and totals
differ between preview and checkout. Cause. Several axes were extracted but no
boundary validates legal combinations. Fix. Add a construction policy that
validates the delegate set before the host is created.

**Hidden global lookup.** Symptom. Tests pass alone but fail in a suite because
one test changes a global delegate registry used by another. Cause. The host
fetches delegates from a service locator or mutable module global. Fix. Inject
the delegate or factory through the constructor and reset registries behind a
test fixture where a registry is unavoidable.

**Overbroad delegate interface.** Symptom. Most delegate implementations return
default values or throw unsupported-operation errors for several methods. Cause.
Several unrelated variations were forced into one delegate interface. Fix.
Split the delegate by role, then install only the roles the host needs.

**Loss of type-based authorization.** Symptom. A guard that formerly rejected
one subclass now allows the same object after migration because every object is
an `Order`. Cause. Authorization logic depended on runtime class identity. Fix.
Move the authorization attribute to explicit state or delegate metadata, then
test the guard against that value.

## 12. Trade-off matrix

| Force | Replace Subclass with Delegate | Keep subclasses | Replace Conditional with Polymorphism | Replace Subclass with Fields | Strategy | State | Decorator |
|---|---|---|---|---|---|---|---|
| Coupling | Clients couple to host and delegate contract | Clients may couple to each subclass | Clients couple to a polymorphic family | Clients couple to one class and fields | Clients couple to strategy interface | Clients couple to context and state interface | Clients couple to wrapped interface |
| Adding a variant | Add delegate and boundary mapping | Add subclass | Add subclass or implementation | Add field value and branches | Add strategy | Add state | Add wrapper |
| Combining axes | Strong when each axis has its own delegate | Poor, type count multiplies | Poor unless each axis is separate | Medium for small data axes | Strong for algorithms | Strong for transitions | Medium for stacked behavior |
| Runtime switching | Strong | Poor | Medium, depends on holder | Strong | Strong | Strong | Strong |
| Latency | One delegation call | One virtual call | One virtual call | Branch or table lookup | One call | One call plus transition checks | One or more wrapper calls |
| Memory | Host plus delegate reference | One object | One object per variant | One object with fields | Strategy object may be shared | State may be shared or owned | Wrapper per layer |
| Operability | Needs delegate labels in telemetry | Class name is visible | Class name is visible | Field is visible | Needs strategy labels | Needs state transition traces | Needs wrapper stack labels |
| Team topology | Good for separate policy ownership | Good for one owner hierarchy | Good for plug-in variant teams | Good for one team owning data | Good for algorithm teams | Good for workflow teams | Good for optional feature teams |
| Cognitive load | Medium. Object graph plus policy names | Low at first, high with combinations | Medium. Polymorphic dispatch | Low for tiny sets, high as branches grow | Medium | Medium to high | Medium |
| Best fit | Independent axes currently encoded as subclasses | True subtype hierarchy | Branches already dominate logic | Tiny closed variant set | Interchangeable algorithm | Object behavior changes by state | Add behavior around same interface |

Reading of the table. Replace Subclass with Delegate wins when the type
hierarchy is carrying policy rather than identity. Keep subclasses when the
subtype relation is true. Replace Subclass with Fields wins when the variation
is small and data-like. Strategy and State are common destinations. Decorator
fits when behavior wraps another object of the same interface rather than
describing a role inside the host.

## 13. Related and incompatible patterns

- **Strategy.** Replace Subclass with Delegate often produces Strategy. If the
  former subclass chose an algorithm, make the delegate a strategy and keep it
  stateless where possible.
- **State.** If the former subclass represented lifecycle state, make the
  delegate a state object and centralize legal transitions. State differs from
  Strategy because transitions are part of the model.
- **Replace Conditional with Polymorphism.** This is a sibling path. If the code
  already has branches over type code, move each branch to a polymorphic object.
  If the code already has subclasses and they no longer fit, move behavior out
  to delegates.
- **Remove Subclass.** This is a smaller refactoring for a subclass that no
  longer carries behavior. Replace Subclass with Delegate may first move the
  behavior out, then Remove Subclass deletes the empty leaf.
- **Replace Superclass with Delegate.** This handles the opposite inheritance
  mistake: a class inherited implementation from a parent that is not a true
  supertype. The mechanics are similar, but the design diagnosis differs.
- **Decorator.** Decorator composes with this refactoring when the delegate
  itself should be wrapped with logging, caching, authorization, or fallback
  behavior. Do not use Decorator to model mutually exclusive variants; use a
  policy delegate.
- **Template Method.** Template Method conflicts when the base class owns a
  fixed algorithm and subclasses are meant to override hooks. If the hook set
  is stable and one-dimensional, Template Method can be fine. If hooks are
  being combined across axes, delegates are a better target.
- **Collapse Hierarchy.** This is incompatible as a direct destination. Collapse
  Hierarchy deletes a useless distinction. Replace Subclass with Delegate keeps
  the distinction and moves it into a field.
- **Service Locator.** This conflicts in application code because it hides the
  delegate dependency. A visible constructor parameter or factory keeps the
  variation understandable.

## 14. Refactoring path in and out

Introducing the refactoring.

1. Pick one subclass and list the methods it overrides. Separate true host
   behavior from the variation. If the subclass overrides many unrelated
   methods, split the goal into more than one delegate.
2. Name the variation in domain language. Good names include `ShippingPolicy`,
   `PricingRule`, `ReviewState`, `RenderAdapter`, and `RetrySchedule`. Weak
   names such as `OrderDelegate` usually mean the role is unclear.
3. Extract a delegate interface containing the smallest method set needed by
   the host. Return domain values, not raw flags that force the host to branch.
4. Create a concrete delegate that copies the subclass behavior. Keep the
   algorithm text small enough that a reviewer can compare old and new behavior
   mechanically.
5. Add a delegate field to the base class. Have the old subclass call the base
   constructor with the matching delegate. At this step, behavior should remain
   identical.
6. Change the base methods to call the delegate. Pass a narrow context or
   values instead of the full host where possible.
7. Run the existing subclass tests. Add one new test that constructs the base
   class with the delegate directly and proves the subclass wrapper is no
   longer needed for behavior.
8. Move client construction from the subclass to the base plus delegate. If
   external callers use the subclass, keep the subclass as a deprecated wrapper
   for one release cycle.
9. Remove the empty subclass with Remove Subclass once no callers depend on its
   name.
10. Repeat for the next subclass. Stop when the remaining subclasses are true
    subtypes or when the hierarchy has been fully replaced.

Commit rhythm matters during this migration. A good first commit introduces the
delegate interface and one implementation while leaving public behavior
unchanged. A second commit switches the host to call the delegate. Later commits
move construction sites and remove wrappers. Keeping those edits separate makes
review easier because each diff answers one question: did we preserve behavior,
did we route through the delegate, and did callers move safely?

When subclasses are part of a published API, prefer a two-stage release. In the
first release, keep the subclass names and make them wrappers over delegates.
Mark them as deprecated only after the replacement construction path is
documented and covered by tests. In the second release, delete wrappers if the
project's compatibility policy permits it. Internal code can move faster, but
the same two-stage shape is still useful when many teams own call sites.

Refactoring out when the delegate stops paying rent.

1. If there is only one delegate implementation and no expected second, inline
   the delegate into the host. That is Inline Class followed by removing the
   constructor parameter.
2. If delegates are one-line data differences, replace them with fields or an
   enum. Cross reference Replace Subclass with Fields and Replace Primitive
   with Object depending on the domain shape.
3. If the host forwards almost every method to the delegate and owns no stable
   state, inline the host into the delegate or rename the delegate as the real
   domain type.
4. If the delegate interface has split into many unsupported methods, apply
   Extract Class or split the interface into smaller roles.
5. If callers need the variant as the main object again, promote the delegate
   to a first-class domain object and let the old host become a collaborator.

## 15. Testing and verification

Judgement. The testing goal is behavioral equivalence during migration, then
contract confidence after the subclass is gone.

Easier because of the refactoring.

- The host can be tested with a fake delegate that records the context it
  receives. That verifies the host no longer reads subclass type.
- Each delegate can be tested as a small unit without constructing a full host
  hierarchy.
- Runtime switching can be tested directly by replacing the delegate and
  asserting the next call changes behavior.
- Data-driven selection can be covered with table tests over delegate keys.

Harder because of the refactoring.

- Tests that asserted concrete subclass type must move to explicit delegate
  labels or observable behavior.
- Serialization tests must cover delegate reconstruction.
- Contract tests become more important because a loose delegate interface can
  accept an implementation that returns plausible but wrong answers.

Useful techniques.

- **Characterization test before the move.** Capture current behavior for each
  subclass before extracting the delegate. These tests guard against accidental
  behavior changes while methods are moved.
- **Delegate contract test.** Write a shared suite that every concrete delegate
  must pass. For a shipping policy, that may cover non-negative days, known
  countries, and monotonic price rules.
- **Construction mapping test.** For every persisted key, tenant plan, feature
  flag, or config value, assert the factory returns the expected delegate.
- **Compatibility wrapper test.** While old subclasses remain, assert each
  wrapper installs the same delegate as the new construction path.
- **Property test for combinations.** When the host has several delegate axes,
  generate legal combinations and assert invariants such as total price never
  negative or illegal transition never accepted.

The TypeScript, Python, and Go examples in dimension 8 were compiled or run in
this workspace with `npx tsc`, `python3`, and `go run`.

## 16. Observability signals

Judgement. Delegation makes behavior choice less visible in type names, so
telemetry must name the delegate choice explicitly.

Record these signals.

- A stable delegate key on each host event, such as `shipping_policy=priority`
  or `review_state=submitted`.
- A counter for host operations labelled by delegate key.
- A duration histogram for delegate calls when they can perform I/O, call a
  rules engine, parse large data, or allocate heavily.
- A counter for delegate selection failures at the construction boundary.
- A counter for fallback delegate use. Any fallback should have a named reason,
  not a silent default.
- For state delegates, a transition counter labelled by old state, new state,
  caller, and rejection reason.
- For combinations, a gauge or periodic audit log of active delegate tuples so
  illegal or rare combinations are visible.

A healthy dashboard shows a delegate distribution that matches current
configuration and changes only with deployments or controlled config edits.
Delegate call latency is small compared with the surrounding operation.
Fallback usage is zero or explained by known compatibility traffic. State
transition rejection rates are low and stable.

A failing dashboard shows one of these shapes. A default delegate appears after
deployment, which points to a missing mapping. A rare delegate receives most
traffic, which points to a bad feature flag or tenant rule. Delegate latency
has a long tail for one key, which points to a slow policy implementation. A
state transition counter shows impossible moves, which points to a boundary
creating hosts with the wrong state delegate.

## 17. Security and privacy implications

Judgement. The refactoring does not create a security property by itself. The
risk depends on who can provide delegates, what data the delegate receives, and
whether delegate choice affects authorization, billing, or privacy.

Security effects that matter.

- **Authorization drift.** If authorization used `instanceof PriorityOrder` or
  subclass annotations, the migration can remove the checked type. Move the
  security-relevant fact to explicit state, claims, or delegate metadata, and
  test the guard against that value.
- **Policy injection.** A delegate chosen from request data, tenant config, or
  plugin registration can become an attack path. Validate the key, reject
  unknown keys, and fail closed for authorization, pricing, quota, and data
  retention policies.
- **Overexposed host data.** Passing the whole host to a delegate can expose
  private fields to code that only needed a country code or subtotal. Pass a
  narrow context object and redact fields before handing data to external
  policy engines.
- **Untrusted delegate code.** In plugin systems, a delegate is executable code
  called by the host. Treat it as supply-chain surface. Pin versions, restrict
  registration, and run under the least privilege the runtime allows.
- **Audit continuity.** If old audit logs recorded subclass names, keep a
  stable delegate key in new logs so incident review can connect old and new
  behavior.
- **Privacy by policy.** If privacy behavior varies by delegate, such as
  regional retention or redaction rules, do not permit a silent default. Missing
  mapping should fail closed and emit an operator-visible event.

The pattern can improve security review by turning hidden subclass behavior
into named policy objects. It can also weaken review if those objects are wired
from mutable global registries or broad plugin loading.

## 18. References

- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
  edition, Addison-Wesley, 2018, chapter 12, "Dealing with Inheritance."
- Martin Fowler, "Replace Subclass with Delegate," refactoring catalog,
  https://refactoring.com/catalog/replaceSubclassWithDelegate.html, verified
  2026-08-02.
- Martin Fowler, "Catalog of Refactorings," https://refactoring.com/catalog/index.html,
  verified 2026-08-02.
- JetBrains, "Replace inheritance with delegation," IntelliJ IDEA 2026.2 Help,
  https://www.jetbrains.com/help/idea/replace-inheritance-with-delegation.html,
  verified 2026-08-02.
- Erich Gamma, Richard Helm, Ralph Johnson, and John Vlissides, *Design
  Patterns. Elements of Reusable Object-Oriented Software*, Addison-Wesley,
  1994, chapter 5, "Behavioral Patterns."
- The Swift Programming Language, "Protocols," section "Delegation,"
  https://docs.swift.org/swift-book/documentation/the-swift-programming-language/protocols/,
  verified 2026-08-02.
- Apple Developer Documentation, `UITableViewDelegate`,
  https://developer.apple.com/documentation/uikit/uitableviewdelegate/,
  verified 2026-08-02.
- Apple Developer Documentation, "Transitioning to the UIKit scene-based life
  cycle,"
  https://developer.apple.com/documentation/uikit/transitioning-to-the-uikit-scene-based-life-cycle,
  verified 2026-08-02.
- Android Developers, `RecyclerView.Adapter`,
  https://developer.android.google.cn/reference/kotlin/androidx/recyclerview/widget/RecyclerView.Adapter,
  verified 2026-08-02.
- Android Developers, `RecyclerView`,
  https://developer.android.google.cn/reference/kotlin/androidx/recyclerview/widget/RecyclerView,
  verified 2026-08-02.
- React documentation, `Component`, https://react.dev/reference/react/Component,
  verified 2026-08-02.
