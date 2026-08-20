---
name: Replace Superclass with Delegate
slug: replace-superclass-with-delegate
family: 03-refactoring
category: Dealing with Inheritance
aliases: [Replace Inheritance with Delegation, Replace Superclass with Delegation]
first_described: "Fowler 2018"
maturity: canonical
related: [replace-subclass-with-delegate, extract-class, move-function, inline-class, adapter, decorator, composition-over-inheritance]
incompatible_with: [extract-superclass, pull-up-method, collapse-hierarchy]
verified: 2026-08-02
---

# Replace Superclass with Delegate

## 1. Name, aliases, and lineage

The canonical name is Replace Superclass with Delegate. Martin Fowler's online
catalog lists the refactoring under that name and gives Replace Inheritance
with Delegation as an alias (https://refactoring.com/catalog/replaceSuperclassWithDelegate.html,
verified 2026-08-02). The catalog index also lists the entry with that alias
among the refactorings for *Refactoring*, 2nd edition
(https://refactoring.com/catalog/index.html, verified 2026-08-02). The book
lineage is Martin Fowler, *Refactoring. Improving the Design of Existing Code*,
2nd edition, Addison-Wesley, 2018, chapter 12, "Dealing with Inheritance."

JetBrains uses the broader tool name Replace Inheritance With Delegation for an
IntelliJ IDEA refactoring that removes a class from an inheritance hierarchy
while forwarding chosen parent members to a held object
(https://www.jetbrains.com/help/idea/replace-inheritance-with-delegation.html,
verified 2026-08-02). That product name is broader than Fowler's catalog name
because it can cover either direction of the inheritance link. This entry is the
superclass case. A class stops extending its former parent and instead stores an
object that supplies the parent behavior it still wants.

The pattern family around this refactoring is old. The Gang of Four catalog
describes Adapter and Decorator as structural patterns that forward work to a
wrapped object, although neither is the same refactoring operation. Adapter
changes the interface seen by clients. Decorator keeps the interface and adds
behavior around a component. Replace Superclass with Delegate is the edit path
that can produce a wrapper, adapter, small component, or domain collaborator,
depending on what the former superclass supplied. Source for the GoF pattern
lineage: Erich Gamma, Richard Helm, Ralph Johnson, and John Vlissides, *Design
Patterns. Elements of Reusable Object-Oriented Software*, Addison-Wesley, 1994,
chapter 4, "Structural Patterns."

Judgement. In code review, the direct phrase often carries more weight than the
catalog name: "this class wants list services, not list identity" or "this
service wants retry behavior, not an HTTP client as its parent." The catalog
name matters when recording the change because it says which direction the
inheritance link is being removed.

## 2. Problem and context

A class extends a superclass to reuse behavior, but the subclass is not truly a
special case of that superclass. The inherited API leaks through the child, the
child can be used where the parent is expected, and clients start relying on
operations that were inherited by accident. The code compiles, tests pass, and
the early version may even feel economical. The design debt appears later when
the child must guard inherited methods, override parent behavior it never
wanted, or explain in documentation that callers should not treat it as the
parent.

The common form is a domain object that extends a collection, a stack that
extends a list, a cache that extends a map, a business service that extends an
HTTP client, or a parser that extends a tokenizer. The child wanted storage,
transport, parsing, validation, or a small reusable algorithm. Inheritance gave
it all public and protected members of the parent. The child now has two public
stories. One is the story the team meant to publish. The other is the inherited
story, which can be called by any client that can see the type.

The problem is not that inheritance is always wrong. A class can extend a
superclass when the subtype relation is part of the model and the inherited
contract is true for every instance of the child. The problem is inheritance
used as a code reuse shortcut. That shortcut binds three things at once:
implementation reuse, substitutability, and public surface area. Replace
Superclass with Delegate splits them. The child keeps the reusable behavior by
holding an instance of the former parent. It stops promising that it is a valid
parent. It exposes only the operations that fit its own contract.

The context that calls for this refactoring is often discovered through
defensive overrides. A child extends a mutable list but throws from `add` for
some states. A class extends a map but wants to hide `clear`. A subclass
inherits equality, iteration, locking, lifecycle, or serialization behavior that
does not match its domain. A bug report arrives because a caller used an
inherited method that was never part of the intended interface. That report is a
strong signal that the public type boundary is wrong, not that one more override
is needed.

## 3. Forces

Judgement. The force balance below is engineering analysis of the refactoring,
not a sourced claim about one named implementation.

- **Coupling.** Favoured. The child stops depending on the full parent contract
  and depends on a narrower field, interface, or helper object.
- **Public API control.** Favoured. The child can expose only its own language
  and can hide methods that came from the parent by accident.
- **Substitutability.** Sacrificed by design. Code that passed the child to an
  API expecting the old parent must change, unless an adapter is kept.
- **Cognitive load.** Mixed. The inheritance graph becomes simpler, but a
  reader must now follow forwarding methods and decide which ones are part of
  the child contract.
- **Consistency.** Favoured when the old parent contract was false. The child no
  longer has to pretend that inherited operations are safe.
- **Latency.** Usually neutral. A direct delegate call adds one method call,
  which is lost in the noise for domain, collection, I/O, and service code.
  Tight numeric loops need measurement.
- **Operability.** Favoured. Composition makes the collaborator visible as a
  named field that can be logged, replaced, decorated, or measured.
- **Cost of change.** Mixed. Removing the superclass can break clients that used
  inherited methods. Future changes are cheaper because the child owns a smaller
  surface.
- **Team topology.** Favoured when separate teams own the child and the reused
  behavior. The child team no longer inherits every release-time decision made
  by the parent team.

The pattern favours explicit ownership over inherited reach. The cost is a
migration where callers may lose access to parent methods they had been using,
even if those calls were never intended by the child type.

Another force is upgrade pressure. With inheritance, the child receives every
new parent method, default behavior, and protected-state assumption as soon as
the parent library changes. That can be useful when the parent is a true
platform abstraction. It is risky when the child borrowed the parent as a helper.
Delegation lets the child upgrade the helper behind a smaller boundary. The team
can then decide which new helper behavior becomes part of the child contract and
which behavior remains private. The trade is that the team must write that
boundary down in code. Inheritance gives the boundary for free, but the free
boundary is often the wrong one.

## 4. Applicability and non-applicability

Reach for Replace Superclass with Delegate when the following hold.

- The subclass uses the parent mainly for implementation reuse, not because it
  is a valid subtype in the domain.
- The subclass's intended public API is smaller than the inherited public API.
- The subclass overrides parent methods only to block, narrow, or repair
  behavior inherited from the parent.
- The superclass changes for reasons unrelated to the subclass, and those
  changes keep forcing updates in the child.
- Tests need to replace the inherited behavior with a fake, but inheritance
  makes that behavior hard to swap.
- A second implementation of the parent behavior is needed, such as a different
  storage object, transport, parser, retry policy, or clock.
- The child needs more than one reusable service, and single inheritance has
  already forced an arbitrary parent choice.

Do NOT reach for it in these cases.

- **The subtype relation is part of the contract.** If every child instance
  truly must be accepted by APIs that require the parent, removing inheritance
  breaks the model. Keep inheritance, or introduce a shared interface if the
  parent class itself is too heavy.
- **The inherited API is the child API.** A domain-specific name wrapped around a
  full list, map, reader, or client may add no value. Rename the type or keep the
  parent if callers need all parent operations.
- **The parent owns protected extension hooks.** Some frameworks require
  subclassing because the framework calls protected methods at specific points.
  Delegation cannot receive those calls unless the framework offers a component
  interface.
- **The child uses most parent state directly through protected fields.** Moving
  to delegation would first require encapsulating the parent. Do that smaller
  refactoring before attempting the larger one.
- **The migration would break a published binary contract without an adapter
  window.** Public libraries may need a deprecated subclass facade that forwards
  to the new composed implementation for one or more releases.
- **The parent is a tiny abstract base class that exists only to define a
  stable protocol.** Replacing it with a field can add noise. Prefer keeping the
  protocol, or move to an interface when the language supports that.
- **The real issue is duplicated behavior across siblings.** Extract Superclass
  or Pull Up Method may be the right direction when siblings share a true common
  model.
- **The problem is child variation, not parent misuse.** If subclasses represent
  modes or policies of one base class, Replace Subclass with Delegate is the
  closer match.

Applicability also depends on ownership. The refactoring is easiest when the
team owns the child and all direct clients. It is harder, but still possible,
when the child is published as a library type. In the library case, treat the
old superclass relation as a compatibility promise until usage data proves
otherwise. Deprecate inherited-style calls, publish a replacement path, and keep
a small adapter if callers need time to move.

## 5. Structure

The refactoring has five participants.

- **FormerChild.** The class that currently extends the superclass. It owns the
  public contract that should survive. After the refactoring this is often the
  same named class, no longer a subclass.
- **FormerSuperclass.** The class formerly used for inherited behavior. It may
  remain unchanged, become a private helper, or be hidden behind a smaller
  interface.
- **DelegateField.** A field inside FormerChild that stores the reused behavior.
  Its declared type should be as narrow as the child needs. That type may be the
  former superclass, an interface extracted from it, or a new component.
- **ForwardingMethods.** Public methods on FormerChild that choose which former
  parent operations remain part of the child contract. Each forwarding method is
  a deliberate API decision.
- **Clients.** Callers of FormerChild. Some use the intended child methods and
  should not notice the change. Others use inherited parent methods and must be
  migrated, blocked, or served through a compatibility adapter.

The core structural change is from an `extends` edge to a field edge. Before the
refactoring, the child inherits implementation and type identity from the
parent. After the refactoring, the child owns its identity and borrows behavior
through a collaborator. The former superclass may stay public because other code
still uses it. It should no longer be the superclass of the child.

Forwarding is not a mechanical "copy every method" exercise. If every inherited
method is forwarded, the refactoring may have moved syntax without changing the
contract problem. The work is to decide which operations belong to the child and
which were accidental exposure.

Two boundary choices decide whether the structure ages well. First, the delegate
field should be named for the role it plays in the child, not for the old class
hierarchy. A field named `list` often says little. A field named `lineItems`,
`buffer`, `clock`, `transport`, or `storage` tells reviewers what the child owns
and why delegation exists. Second, the child should not leak the delegate as a
general escape hatch. A method such as `asList()` or `rawClient()` can be a
valid migration aid, but it is also a way for callers to rebuild the old parent
dependency outside the class. Prefer named child operations, and add a view only
when a caller has a real read need that the child does not yet model.

## 6. ASCII structure diagram

```
Before

  +--------------------------+
  |     FormerSuperclass     |
  |--------------------------|
  | + inheritedRead()        |
  | + inheritedWrite()       |
  | + inheritedClear()       |
  +--------------------------+
              ^
              |
              | extends
              |
  +--------------------------+
  |       FormerChild        |
  |--------------------------|
  | + childOperation()       |
  | + inheritedRead()        |
  | + inheritedWrite()       |
  | + inheritedClear()       |
  +--------------------------+

After

  +--------------------------+      has       +----------------------+
  |       FormerChild        | -------------> |     DelegateField    |
  |--------------------------|                |----------------------|
  | - delegate               |                | + read()             |
  | + childOperation()       |                | + write()            |
  | + readOnlyView()         |                +----------------------+
  +--------------------------+

  FormerChild exposes child language.
  DelegateField supplies reused behavior.
  inheritedClear() is not forwarded unless it belongs to the child contract.
```

## 7. Dynamics

At runtime, client calls still arrive at the child. The child now decides
whether a call is handled locally, forwarded to the delegate, or rejected
because it was never part of the intended API. The delegate is a collaborator,
not an ancestor, so it can be swapped in tests or chosen at construction.

```
Client          FormerChild             DelegateField
  |                  |                         |
  |-- childOp() ---->|                         |
  |                  |-- validate input        |
  |                  |-- read() -------------->|
  |                  |<-- stored value --------|
  |                  |-- apply child rule      |
  |<-- result -------|                         |
  |                  |                         |
  |-- oldParentOp()? |                         |
  |                  |-- not on public API     |
  |<-- compile error |                         |
  |                  |                         |
```

During migration there may be a compatibility shape.

```
OldClient       DeprecatedChildAsParent       NewChild        Delegate
  |                     |                         |              |
  |-- parentOp() ------>|                         |              |
  |                     |-- forward ------------->|              |
  |                     |                         |-- call ----->|
  |                     |                         |<-- result ===|
  |<-- result ----------|                         |              |
```

That adapter should be temporary. If it lives forever, clients still see the old
parent story and the team has gained little beyond a private rewrite.

## 8. Implementation variants

**Direct delegate field.** The child stores an instance of the former
superclass and forwards selected calls. This is the smallest edit when the
parent class is stable and the child still needs much of its behavior. The
drawback is that the child still depends on the full parent type internally.

**Extracted delegate interface.** The team first extracts the small protocol the
child needs, then stores that interface. This gives stronger decoupling and
testability. It costs a new type and one more design decision: where the
interface belongs.

**Inner adapter delegate.** JetBrains documents a tool variant where the class
receives a private inner class that extends the former superclass and selected
parent calls are delegated through it
(https://www.jetbrains.com/help/idea/replace-inheritance-with-delegation.html,
verified 2026-08-02). This is useful when the former superclass has abstract
methods or protected hooks that still need an implementation. It can also hide a
half-step migration inside one file.

**Facade around a delegate.** The child becomes a narrow facade with domain
names. For example, `InvoiceLines.total()` may delegate to a list internally but
never expose arbitrary list mutation. This variant has the clearest API, but
callers that used inherited collection methods need edits.

**Adapter for old clients.** The old subclass shape is kept as a deprecated
adapter that forwards to the new child. This is a public-library migration
technique. It costs duplicate API surface for a release window and should have
a removal date.

**Decorator destination.** If the child used inheritance to add behavior around
all parent operations, the destination may be Decorator rather than a narrow
domain class. Java's collection wrappers are a standard-library example of
wrappers backed by specified collections, documented by Oracle for
`Collections` (https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Collections.html,
verified 2026-08-02).

**Language without inheritance.** Go and Rust do not use class inheritance for
this shape. The same design choice appears as a struct holding an interface or
trait object. Go's `io.LimitReader` returns an `io.Reader` that reads from a
supplied reader and stops after a byte limit (https://pkg.go.dev/io#LimitReader,
verified 2026-08-02). Rust commonly uses trait objects for shared behavior, as
shown in *The Rust Programming Language*, chapter 18.2
(https://doc.rust-lang.org/book/ch18-02-trait-objects.html, verified
2026-08-02).

## 9. Known production uses

**Java Collections Framework, synchronized and unmodifiable wrappers.** Oracle's
Java SE 21 documentation describes `java.util.Collections` as containing
wrappers that return new collections backed by specified collections, and lists
`synchronizedList` and `unmodifiableList` as returning views backed by supplied
lists (https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Collections.html,
verified 2026-08-02). These wrappers are named production uses of the
delegation destination: behavior is supplied by a contained collection rather
than by claiming to be a specific concrete collection subclass.

**Python standard library, `collections.UserList`.** The Python 3 documentation
states that `UserList` acts as a wrapper around list objects and stores its
contents in a regular list available through the `data` attribute
(https://docs.python.org/3/library/collections.html, verified 2026-08-02).
This is a named standard-library delegation shape for list-like classes. It is
especially relevant to this refactoring because it offers list behavior through
a contained list rather than forcing direct inheritance from the built-in list.

**Go standard library, `io.LimitReader`.** The Go documentation defines
`LimitReader` as returning a `Reader` that reads from a supplied reader and
stops with EOF after a byte count, with `*LimitedReader` as the underlying
implementation (https://pkg.go.dev/io#LimitReader, verified 2026-08-02). This
is a production wrapper over a delegate reader. Go has no class superclass, but
the design pressure is the same: reuse and constrain another object's behavior
through composition.

**JetBrains IntelliJ IDEA, automated refactoring support.** IntelliJ IDEA
documents Replace Inheritance With Delegation as a refactoring command that
removes a class from an inheritance hierarchy while preserving parent
functionality through delegated members
(https://www.jetbrains.com/help/idea/replace-inheritance-with-delegation.html,
verified 2026-08-02). Tool support is not an application of the runtime pattern,
but it is production evidence that the refactoring is common enough to automate
in a mainstream IDE.

## 10. Consequences

Positive.

- The child publishes a smaller, truer API. Inherited methods that never fit the
  domain disappear from ordinary call sites.
- The child can vary the reused behavior by constructor parameter, factory, test
  fake, runtime configuration, or feature flag.
- Parent changes stop leaking into the child unless the child forwards or uses
  the changed member.
- Tests can replace the delegate without building a subclass of the child.
- The child can combine several collaborators, which single inheritance could
  not express.
- The refactoring often exposes a missing domain name. A vague subclass becomes
  a class with a field such as `lineItems`, `storage`, `transport`, or
  `clock`.

Negative.

- Clients that relied on parent substitutability break. Some were wrong to do
  so, but the migration still costs time.
- Boilerplate forwarding can grow if the child truly needs many parent methods.
- Equality, hashing, ordering, serialization, locking, and lifecycle rules may
  change when parent behavior is no longer inherited automatically.
- Protected parent state becomes inaccessible. That is often good design, but
  the transition can require several small preparatory refactorings.
- A poorly chosen delegate type can preserve the coupling while hiding it in a
  field.
- If the child forwards too much, the new design becomes a middle man with less
  type compatibility than before.

## 11. Failure modes and misuse

Judgement. These are recurring production symptoms and fixes drawn from the
mechanics of the refactoring.

**Forwarding everything.** Symptom. The new child has dozens of methods whose
bodies contain one call to the delegate, and reviewers still cannot name the
child's own contract. Cause. The team translated inheritance mechanically
instead of deciding which inherited operations belonged in the child. Fix. Keep
only domain operations, expose a read-only view when needed, or leave
inheritance in place if the full parent API is the real contract.

**Broken substitutability discovered late.** Symptom. A downstream module no
longer accepts the child where the former superclass was required. Cause. A
client used the child through the old parent type. Fix. Add a temporary adapter,
change that API to consume the narrower protocol, or keep the subclass facade
for one release window.

**Delegate aliasing leak.** Symptom. External code mutates the delegate and the
child's invariants change without any child method running. Cause. The child
stores or returns a mutable delegate supplied by caller code. Fix. Copy the
delegate on input, wrap it in a read-only view, or document shared ownership and
guard all access.

**Lost parent lifecycle.** Symptom. Files, sockets, locks, or transactions stay
open after the child is disposed. Cause. Parent cleanup used to run through
inherited lifecycle methods, and the new child forgot to forward close or
release. Fix. Make the child own lifecycle explicitly and add tests that call
close twice and use the child after close.

**Equality drift.** Symptom. Objects that used to compare equal no longer do, or
hash-based collections lose entries after migration. Cause. The child stopped
inheriting parent equality or hashing, or now includes the delegate object
identity instead of its value. Fix. Define equality in child terms and add
before-and-after characterization tests.

**Protected-field trap.** Symptom. The refactoring stalls because the child read
five protected fields from the parent and cannot compile once inheritance is
removed. Cause. The superclass exposed state to subclasses instead of behavior.
Fix. Encapsulate the parent first, then move one use at a time behind methods.

**Middle man regression.** Symptom. Call stacks and traces gain a layer, but
defect rate and API confusion do not improve. Cause. The child has become a
pass-through wrapper with no domain rule of its own. Fix. Inline the child into
its callers, or make the delegate the public object if that is the true model.

**Serialization incompatibility.** Symptom. Stored objects or wire payloads from
the old version cannot be read after deployment. Cause. The serialized shape
changed when the parent field layout was replaced by a contained delegate. Fix.
Provide a migration reader, keep old field names for the persistence boundary,
or version the serialized form.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

<table>
<thead>
<tr>
<th>Force</th>
<th>Replace Superclass with Delegate</th>
<th>Keep Inheritance</th>
<th>Extract Interface</th>
<th>Adapter</th>
<th>Decorator</th>
<th>Inline Class</th>
</tr>
</thead>
<tbody>
<tr>
<td>Coupling</td>
<td>Lower, if the delegate type is narrow</td>
<td>High, the child inherits the parent contract</td>
<td>Lower for callers, parent code may remain</td>
<td>Lower across an interface boundary</td>
<td>Lower for behavior around a component</td>
<td>Lowest type count, highest caller coupling</td>
</tr>
<tr>
<td>Public API control</td>
<td>Strong, the child chooses forwarded methods</td>
<td>Weak, parent public members leak through</td>
<td>Strong for clients typed to the interface</td>
<td>Strong, but can create two names for one idea</td>
<td>Strong when interface stays the same</td>
<td>No separate child API remains</td>
</tr>
<tr>
<td>Substitutability</td>
<td>Removed unless an adapter remains</td>
<td>Preserved</td>
<td>Preserved at the interface level</td>
<td>Preserved for the adapted interface</td>
<td>Preserved for the component interface</td>
<td>Removed with the child type</td>
</tr>
<tr>
<td>Cognitive load</td>
<td>Medium, forwarding must be read</td>
<td>Medium, hierarchy rules must be known</td>
<td>Medium, one more type exists</td>
<td>Medium to high, two interfaces are mapped</td>
<td>Medium, wrapping order matters</td>
<td>Low, fewer types</td>
</tr>
<tr>
<td>Latency</td>
<td>One delegate call</td>
<td>Direct inherited call or virtual dispatch</td>
<td>No direct runtime cost by itself</td>
<td>One adapter call</td>
<td>One or more wrapper calls</td>
<td>No wrapper call</td>
</tr>
<tr>
<td>Operability</td>
<td>Good, delegate can be named in telemetry</td>
<td>Weak, inherited behavior is implicit</td>
<td>Good if implementation is logged</td>
<td>Good when adapter labels are explicit</td>
<td>Good when wrapper stack is recorded</td>
<td>Mixed, less indirection but fewer boundaries</td>
</tr>
<tr>
<td>Cost of change</td>
<td>Migration cost now, lower surface later</td>
<td>Low now, parent changes keep leaking</td>
<td>Moderate, call sites need new type</td>
<td>Moderate, two contracts must be maintained</td>
<td>Low if component interface is stable</td>
<td>Low if the class was empty</td>
</tr>
</tbody>
</table>

Reading of the matrix. Replace Superclass with Delegate wins when inherited
identity is the source of wrong behavior. Extract Interface wins when the subtype
promise is still true but clients should depend on a smaller protocol. Adapter
wins when the target API is different. Decorator wins when the child adds
behavior around all operations of the component. Inline Class wins when the child
was a name with no behavior or rule.

## 13. Related and incompatible patterns

- **Replace Subclass with Delegate.** The sibling refactoring. It moves child
  variation into a field. Replace Superclass with Delegate moves parent reuse
  into a field. Both remove inheritance, but they repair different links.
- **Extract Class.** Often a preparatory move. If the child uses only part of
  the superclass, extract that part into a small collaborator before replacing
  the superclass link.
- **Move Function and Move Field.** The small edits inside the larger
  refactoring. Behavior that belongs to the child moves out of the parent, and
  behavior that remains reusable sits on the delegate.
- **Adapter.** A common destination when clients still need the old parent
  interface. The adapter keeps an old shape alive while the new child owns the
  real implementation.
- **Decorator.** A destination when the former child added behavior around the
  former parent while keeping the same interface. Collection wrappers are a
  common example of this style.
- **Facade.** A destination when the child should expose a smaller domain API
  over a larger delegate.
- **Extract Interface.** A lighter option when inheritance is too heavy but
  substitutability must remain. It may be used before or instead of this
  refactoring.
- **Extract Superclass and Pull Up Method.** Directional opposites. They move
  toward inheritance to share common behavior. Use them when the subtype model
  is true.
- **Collapse Hierarchy.** Incompatible as a simultaneous change. Collapse
  Hierarchy removes a distinction between parent and child. Replace Superclass
  with Delegate preserves the child as a separate owner and changes how it
  reuses behavior.
- **Service Locator.** A poor substitute. Fetching the former superclass from a
  global registry hides the dependency that delegation should make visible.

## 14. Refactoring path in and out

Introducing the refactoring.

1. Characterize current behavior with tests around the child, including inherited
   methods that callers use today. These tests separate intended compatibility
   from accidental exposure.
2. List every inherited method visible on the child. Mark each as keep, replace
   with a child-named method, migrate away, or block.
3. Add a private field to the child holding an instance of the former
   superclass or a smaller extracted interface. Keep the `extends` link for the
   first step.
4. Change one child method at a time to use the field rather than inherited
   state or inherited calls. Run tests after each group.
5. For protected field access, add parent accessors or move the needed behavior
   onto the delegate. Avoid reaching into delegate internals from the child.
6. Add forwarding methods only for operations that belong in the child contract.
   Give child-domain names where the old parent name was too broad.
7. Change call sites that used the child as the parent. Prefer a narrow
   interface. Use a temporary adapter only when compatibility requires it.
8. Remove the `extends` clause. Fix compile errors by either forwarding,
   migrating, or deleting the inherited operation from the child surface.
9. Delete unused overrides that existed only to repair the superclass contract.
10. Record the compatibility decision in release notes if public clients lose
   inherited methods.

A small commit sequence keeps risk low. First, add the delegate field while the
class still extends the parent. Second, route one method at a time through the
field and run tests. Third, migrate call sites that mention the parent type.
Fourth, remove the inheritance link. This order separates behavior movement from
API breakage. If the edit removes `extends` first, every compiler error looks
equally urgent and reviewers lose the ability to see which calls were intended.

When the old parent is a collection, create a stricter migration ledger. Record
whether clients use construction, indexing, iteration, mutation, clearing,
sorting, equality, hashing, and serialization. Collection parents bring many
small contracts that application classes inherit by accident. Missing one of
those contracts can be harmless, or it can be a release blocker. The ledger
turns that into an explicit compatibility decision.

Refactoring out when delegation stops earning its place.

1. If every public method forwards unchanged to the delegate, consider Remove
   Middle Man or Inline Class.
2. If callers need the full delegate API, expose the delegate type directly and
   delete the wrapper after a migration window.
3. If the child and delegate now change for the same reason and share the same
   invariant, inheritance may be valid again. Use Extract Superclass or Pull Up
   Method only after the subtype relation is written down and tested.
4. If the delegate has become a set of unrelated services, split it into
   smaller collaborators before deciding whether the child should stay.
5. If compatibility adapters remain after their migration date, delete them or
   make the date explicit. A permanent adapter may be a pattern. A forgotten
   adapter is dead weight.

## 15. Testing and verification

Judgement. Testing focuses on preserving intended child behavior while making
accidental parent behavior visible.

Start with characterization tests. Before removing inheritance, write tests for
the operations clients use and for the parent operations the child should not
support. The first group guards migration. The second group prevents accidental
republication through forwarding.

Add contract tests for the delegate. If the delegate type is an extracted
interface, write one shared test suite that every delegate implementation must
pass. The child tests should not re-test every delegate detail. They should
verify that the child calls the delegate at the right boundary and applies its
own invariant.

Use fakes rather than partial mocks. A fake delegate with counters can show that
`InvoiceLines.total()` reads the stored lines once, that `LimitedReader` stops
after the limit, or that a service closes its transport. Partial mocks of the
old superclass keep too much of the old inheritance shape alive in the tests.

Check compatibility deliberately. In a statically typed language, compilation
will reveal callers that still expect the old parent type. In a dynamic language,
add integration tests or static analysis around call paths that were known to
use inherited members. For public libraries, run old client examples against the
adapter layer.

Verify lifecycle. If the former superclass owned resources, tests should cover
close, double close, use after close, and failure during close. This catches the
most common delegation migration bug: the child stops inheriting cleanup but
forgets to own cleanup itself.

Verify equality and serialization when they matter. Capture old behavior, decide
which parts remain contract, and test that exact decision. Do not assume the
old parent rules were correct for the child.

## 16. Observability signals

Judgement. Delegation makes a hidden dependency explicit, so telemetry should
name that dependency without exposing private data.

Record the delegate type, role, or implementation label at construction time.
For high-cardinality systems, use a bounded label such as `delegate_kind` rather
than a raw class name. Log when a compatibility adapter path is used, with the
caller or route if available. That signal tells the team whether old inherited
surface is still active.

Measure delegate call counts and failure counts for operations that cross
process, disk, database, or lock boundaries. A healthy instance shows a stable
delegate mix, low failure rate, and no traffic through deprecated adapter paths
after migration. A failing instance shows one delegate type producing most
errors, old adapter calls remaining after the planned cutoff, or unexpected
mutation of a delegate that should be private to the child.

Trace the child operation and the delegate operation as separate spans when the
delegate can block. The child span should carry the domain operation. The
delegate span should carry the mechanism, such as collection, reader, transport,
cache, or parser. That split lets operators see whether time is spent in the
domain rule or in the reused component.

For mutable delegates, record invariant failures at the child boundary. If the
child expects sorted items, nonnegative totals, monotonic offsets, or closed
resource state, log the first violation with the delegate label and reject the
operation. Silent repair hides aliasing bugs.

## 17. Security and privacy implications

Judgement. The refactoring is not a security feature by itself. It changes which
operations are exposed and which object owns state, so it can either reduce or
increase attack surface.

The main security gain is surface reduction. A child that no longer extends a
mutable collection, map, client, or parser no longer publishes every parent
mutator. That can remove accidental ways to clear data, bypass validation,
change ordering, reset a connection, or reach raw input. The gain exists only if
the child does not forward those operations back out.

The main security risk is delegate escape. If untrusted code receives the
delegate, it can call methods that bypass child validation. Treat the delegate
as private state unless the design has an explicit shared-ownership contract.
When the delegate must be exposed, return a read-only view or an interface that
omits mutators.

A second risk is confused authority. The child may enforce authorization while
the delegate owns the raw operation. If another path can call the delegate
directly, the authorization rule has moved from inherited method override to a
convention. Put the check at the delegate boundary, or keep the delegate
unreachable outside the child.

Privacy concerns are similar. The child may redact, filter, or aggregate data
while the delegate stores raw records. Logs and traces should identify the
delegate by bounded role, not by tenant-specific class names or raw storage
keys. If serialization changes, confirm that new payloads do not expose the
delegate's internal fields.

## Code examples

Three languages are used because they show the refactoring in different type
systems. TypeScript shows the class migration and a narrow delegate interface.
Python shows the collection case, using a contained list. Go shows the same
destination shape in a language without class inheritance.

### TypeScript

```typescript
interface LineStore {
  add(line: string): void;
  values(): readonly string[];
}

class ArrayLineStore implements LineStore {
  private readonly lines: string[] = [];

  add(line: string): void {
    this.lines.push(line);
  }

  values(): readonly string[] {
    return this.lines;
  }
}

class InvoiceLines {
  constructor(private readonly store: LineStore = new ArrayLineStore()) {}

  addLine(line: string): void {
    if (line.trim() === "") {
      throw new Error("blank line");
    }
    this.store.add(line);
  }

  totalCharacters(): number {
    return this.store.values().reduce((sum, line) => sum + line.length, 0);
  }
}

const invoice = new InvoiceLines();
invoice.addLine("labor");
invoice.addLine("parts");
console.log(invoice.totalCharacters());
```

### Python

```python
class InvoiceLines:
    def __init__(self, lines=None):
        self._lines = list(lines or [])

    def add_line(self, line: str) -> None:
        if not line.strip():
            raise ValueError("blank line")
        self._lines.append(line)

    def total_characters(self) -> int:
        return sum(len(line) for line in self._lines)

    def as_tuple(self) -> tuple[str, ...]:
        return tuple(self._lines)


if __name__ == "__main__":
    invoice = InvoiceLines()
    invoice.add_line("labor")
    invoice.add_line("parts")
    print(invoice.total_characters())
```

### Go

```go
package main

import "fmt"

type LineStore interface {
	Add(line string)
	Values() []string
}

type SliceLineStore struct {
	lines []string
}

func (s *SliceLineStore) Add(line string) {
	s.lines = append(s.lines, line)
}

func (s *SliceLineStore) Values() []string {
	out := make([]string, len(s.lines))
	copy(out, s.lines)
	return out
}

type InvoiceLines struct {
	store LineStore
}

func NewInvoiceLines(store LineStore) *InvoiceLines {
	if store == nil {
		store = &SliceLineStore{}
	}
	return &InvoiceLines{store: store}
}

func (i *InvoiceLines) AddLine(line string) error {
	if line == "" {
		return fmt.Errorf("blank line")
	}
	i.store.Add(line)
	return nil
}

func (i *InvoiceLines) TotalCharacters() int {
	total := 0
	for _, line := range i.store.Values() {
		total += len(line)
	}
	return total
}

func main() {
	invoice := NewInvoiceLines(nil)
	_ = invoice.AddLine("labor")
	_ = invoice.AddLine("parts")
	fmt.Println(invoice.TotalCharacters())
}
```

## 18. References

1. Martin Fowler. *Refactoring. Improving the Design of Existing Code*, 2nd
   edition. Addison-Wesley, 2018. Chapter 12, "Dealing with Inheritance."
   Source for the catalog lineage and placement of the refactoring.
2. Martin Fowler. "Replace Superclass with Delegate."
   https://refactoring.com/catalog/replaceSuperclassWithDelegate.html
   Verified 2026-08-02. Source for the canonical name and alias.
3. Martin Fowler. "Catalog of Refactorings."
   https://refactoring.com/catalog/index.html
   Verified 2026-08-02. Source for catalog membership and index alias.
4. JetBrains. "Replace inheritance with delegation." IntelliJ IDEA 2026.2 Help.
   https://www.jetbrains.com/help/idea/replace-inheritance-with-delegation.html
   Verified 2026-08-02. Source for IDE refactoring support and tool behavior.
5. Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides. *Design Patterns.
   Elements of Reusable Object-Oriented Software*. Addison-Wesley, 1994.
   Chapter 4, "Structural Patterns." Source for Adapter and Decorator lineage.
6. Oracle. *Java SE 21 API Specification*, `java.util.Collections`.
   https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Collections.html
   Verified 2026-08-02. Source for collection wrappers backed by supplied
   collections.
7. Python Software Foundation. *Python 3.14 documentation*, `collections`,
   section "`UserList` objects."
   https://docs.python.org/3/library/collections.html
   Verified 2026-08-02. Source for the `UserList` wrapper production use.
8. The Go Authors. *Go package documentation*, `io`, `LimitReader`.
   https://pkg.go.dev/io#LimitReader
   Verified 2026-08-02. Source for the `LimitReader` wrapper production use.
9. Steve Klabnik, Carol Nichols, and Rust community contributors. *The Rust
   Programming Language*, chapter 18.2, "Using Trait Objects to Abstract over
   Shared Behavior."
   https://doc.rust-lang.org/book/ch18-02-trait-objects.html
   Verified 2026-08-02. Source for the Rust trait-object language note.
