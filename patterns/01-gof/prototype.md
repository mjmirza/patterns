---
name: Prototype
slug: prototype
family: 01-gof
category: Creational
aliases: [Clone, Copy Constructor Pattern, Exemplar, Prototypal Instantiation]
first_described: "Gamma, Helm, Johnson, Vlissides 1994"
maturity: canonical
related: [abstract-factory, factory-method, builder, singleton, memento, composite, decorator, flyweight]
incompatible_with: []
verified: 2026-08-02
---

# Prototype

## 1. Name, aliases, and lineage

The canonical name is Prototype. It was catalogued as one of the five creational
patterns by Erich Gamma, Richard Helm, Ralph Johnson, and John Vlissides in
*Design Patterns. Elements of Reusable Object-Oriented Software*, Addison-Wesley
1994, Chapter 3, Creational Patterns, where the intent is stated as specifying
the kinds of objects to create using a prototypical instance and creating new
objects by copying that prototype.

In real use the pattern travels under several names.

- Clone, when the API surface is a single `clone` operation.
- Copy Constructor Pattern, in C++ and Java communities where the copying
  operation is a constructor taking an instance of its own type. Joshua Bloch
  argues for exactly this shape over the Java `Cloneable` mechanism in
  *Effective Java*, 3rd edition, Addison-Wesley 2018, Item 13, "Override clone
  judiciously".
- Exemplar, an older Smalltalk-community term for an instance used as the model
  for further instances.
- Prototypal instantiation, in the JavaScript community, where the language
  itself carries a delegation-based version of the idea.

The name is contested in one specific way that matters. In the GoF sense a
prototype is an object that produces an independent copy of itself. In the
ECMAScript sense a prototype is an object that other objects **delegate to** at
property-lookup time, with no copying at all. `Object.create(proto)` creates a
new object whose `[[Prototype]]` is the supplied object, so the created object
reads through to the prototype rather than owning a copy of its state, per
ECMAScript 2027 Language Specification, `Object.create`, section 7.3.32,
https://tc39.es/ecma262/multipage/fundamental-objects.html#sec-object.create
verified 2026-08-02, and the MDN reference for `Object.create`,
https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/create
verified 2026-08-02. The two ideas share a word and a motivation, object
creation driven by an existing exemplar rather than by a class, and they differ
completely in memory behaviour and in mutation semantics. Section 8 treats the
distinction as a first-class variant rather than a footnote.

## 2. Problem and context

You have an object whose configuration is expensive, awkward, or impossible to
reconstruct from a constructor call. You need many objects like it, differing in
a handful of fields. The recognisable symptoms in a codebase are these.

- A constructor with fifteen parameters, and every call site passes near
  identical values that were themselves loaded from somewhere else.
- A factory that reads a configuration file, walks a database, or performs
  network calls to assemble one object, and now needs to hand out a hundred of
  them per second.
- An object graph assembled interactively by a user, in a level editor or a
  diagram tool, that the user now wants to duplicate. There is no class to
  instantiate because the configuration was authored, not coded.
- A branching operation. Take the current state, fork it, mutate the fork, keep
  the original intact for comparison or rollback.
- A class hierarchy whose concrete types are not known to the creating code, but
  which must be reproduced exactly. The creator holds an instance and needs
  another of the same dynamic type without a `switch` over type tags.

The context is object creation where the *state* of an existing instance, rather
than the *class* of a future instance, is the thing worth reusing. Outside that
context Prototype is an anti-pattern, because it replaces a readable constructor
with an opaque copy operation whose depth semantics nobody can see at the call
site.

## 3. Forces

- **Latency.** Copying an in-memory object graph is usually far cheaper than
  re-running the work that produced it. That is the pattern's main pull. The
  counter-force is that a deep copy of a large graph is itself expensive and
  scales with graph size, not with the number of fields the caller cared about.
- **Coupling.** Prototype removes the creator's compile-time dependency on
  concrete classes. The creator holds a `Cloneable`-shaped reference and never
  names a subclass. In exchange the creator gains a dependency on a copy
  contract whose semantics are not expressible in the type system.
- **Consistency.** A shallow copy shares mutable substructure with its source, so
  writing through one clone is visible from the other. This is the single
  largest source of defects in this pattern and it is silent at compile time.
- **Operability.** A copy operation that skips a field, or copies a live socket,
  or duplicates a supposedly unique identifier, produces failures far from the
  clone site. Prototype trades a loud constructor failure for a quiet state
  failure later.
- **Cost.** Memory grows linearly in the number of live clones for a deep copy,
  and stays flat for delegation-based prototypes, which is why JavaScript chose
  delegation.
- **Team topology.** The copy contract is a cross-team invariant. Any team adding
  a field to a prototyped class must remember to copy it. Nothing in a compiler
  reminds them. Copy constructors and generated copy code push this back into
  the type system where a reviewer can see it.
- **Cognitive load.** `new Order(customer, items, currency)` states what an order
  needs. `template.clone()` states nothing. The reader must find the prototype's
  registration site and the copy implementation before understanding the result.

Prototype favours latency and decoupling from concrete types. It sacrifices
explicitness at the call site and it sacrifices compile-time safety around
completeness and depth of the copy.

## 4. Applicability and non-applicability

Reach for Prototype when all of these hold.

- Constructing the object from scratch costs far more than copying it, and you
  have measured that rather than assumed it.
- The instances you need differ from an existing instance in a small number of
  fields.
- The set of configurations is decided at runtime, by a user, a config file, or a
  registry, so a class per configuration is not available.
- The creating code must reproduce the dynamic type of an object it holds without
  knowing that type.
- The object is a value-like aggregate whose full state is worth copying.

Do NOT reach for Prototype when any of these hold. This list is the one that
saves the reader time.

- **The object owns a non-copyable resource.** File handles, sockets, database
  connections, OS threads, mutexes, GPU buffers, and hardware handles have
  identity. Copying the field copies a reference to one live resource into two
  owners, and the second close is a double free or a use-after-close. Use a
  factory that opens a fresh resource.
- **The object has an identity that must be unique.** Primary keys, aggregate
  root identifiers, idempotency keys, and correlation identifiers must be
  regenerated, not copied. A clone that carries the source's identifier will pass
  every unit test and corrupt production data.
- **A constructor already expresses the object cheaply.** If the object is three
  fields and a constructor, a copy operation adds an indirection and removes the
  reader's ability to see what an instance requires.
- **The object graph is large and you need only a small mutation.** Prefer a
  persistent data structure with shared substructure, or the Memento pattern for
  snapshot and restore, over a full deep copy per edit.
- **The object is immutable.** There is nothing to protect. Return the same
  reference. Cloning an immutable value burns memory for no benefit and defeats
  interning, which is why the Flyweight pattern exists in opposition here.
- **The copy must cross a process or machine boundary.** That is serialisation,
  with a versioned wire format and an explicit schema, not cloning. Reusing a
  serialiser to implement in-process cloning is a known variant, see section 8,
  and it carries the serialiser's constraints with it.
- **You are on the JVM and are tempted by `Cloneable`.** See section 9 and
  section 11 for why the specific Java mechanism is a trap even where the
  underlying pattern is sound.

## 5. Structure

- **Prototype.** The abstraction that declares the copy operation. Names a single
  method, conventionally `clone`, `copy`, or `duplicate`, that returns a new
  instance of the same dynamic type. In Go and Rust it is an interface or trait.
  In TypeScript it is an interface. In Java the community-preferred form is a
  copy constructor plus a covariant `copy` method rather than the built-in
  `Cloneable` marker.
- **ConcretePrototype.** A class that implements the copy operation for its own
  state. Owns the decision about which fields are copied deeply, which are
  shared, and which are regenerated. This class is where the pattern's
  correctness lives.
- **Client.** Holds a reference typed as Prototype and asks for a copy. Never
  names a ConcretePrototype. Applies the small per-instance differences after
  copying.
- **PrototypeRegistry.** Optional but common in practice. A keyed store of
  pre-configured exemplars, so the Client can ask for a copy of "invoice
  template EU-B2B" by name. This is where Prototype most often becomes an
  Abstract Factory replacement, because the registry can be populated at runtime.
- **Cloner.** Optional. A separate collaborator that performs the copy on behalf
  of a ConcretePrototype that cannot or should not implement copying itself.
  Serialisation-based cloning and reflection-based cloning both put the copy
  logic here. This decouples the copy contract from the type, at the price of
  making the contract invisible to the type system.

The relationships are these. Client depends on Prototype only. Each
ConcretePrototype implements Prototype and returns its own type. The
PrototypeRegistry aggregates Prototype instances and returns copies rather than
the stored exemplars, which is the invariant that keeps the registry safe from
client mutation.

## 6. ASCII structure diagram

```
        +----------------------+
        |       Client         |
        |----------------------|
        | - proto : Prototype  |
        | + operation()        |
        +----------+-----------+
                   |
                   | asks for a copy, never names a concrete type
                   v
        +----------------------+          +---------------------------+
        |   <<interface>>      |<>--------|    PrototypeRegistry      |
        |     Prototype        |  stores  |---------------------------|
        |----------------------|  many    | - exemplars : Map<K,Proto>|
        | + clone() : Prototype|          | + register(k, p)          |
        +----------+-----------+          | + get(k) : Prototype      |
                   ^                      +---------------------------+
                   |                        get() returns p.clone(),
        +----------+-----------+            never the stored exemplar
        |                      |
+-------+-----------+  +-------+-----------+
| ConcretePrototypeA|  | ConcretePrototypeB|
|-------------------|  |-------------------|
| - value : int     |  | - parts : List    |
| - shared : Cache  |  | - owned : Buffer  |
| + clone()         |  | + clone()         |
+-------------------+  +-------------------+
   copies value,          deep copies parts
   SHARES cache           and owned buffer
   (deliberate)           (must, they are mutable)
```

## 7. Dynamics

Two flows matter. The first is a copy through a registry. The second is the
depth decision inside a single `clone` call, which is where the pattern usually
fails.

```
Client            Registry          Exemplar(P)        Copy(P')
  |                  |                  |                 |
  |-- get("eu-b2b")->|                  |                 |
  |                  |-- clone() ------>|                 |
  |                  |                  |-- allocate ---->|
  |                  |                  |   new P'        |
  |                  |                  |                 |
  |                  |                  |-- copy scalars->|  by value
  |                  |                  |-- deep copy --->|  owned mutables
  |                  |                  |-- share ------->|  immutables, caches
  |                  |                  |-- regenerate -->|  identity, timestamps
  |                  |<-- P' -----------|                 |
  |<-- P' -----------|                  |                 |
  |                                                       |
  |-- P'.setCustomer("ACME") ---------------------------->|
  |                                                       |
  | exemplar P is unchanged. This is the invariant that
  | makes the registry reusable across concurrent clients.
```

The field-by-field decision inside `clone` is a four-way classification, and
naming it explicitly is the difference between a correct copy and a latent bug.

```
for each field f in the object:

   is f an immutable value ?              -> share the reference
        (int, string, frozen record)         cost 0, safe by definition

   is f a mutable object this object OWNS ?  -> deep copy it
        (list, map, buffer, child node)          cost O(size of f)

   is f a mutable object this object BORROWS ? -> share the reference
        (injected logger, connection pool,          document it, or the
         shared cache, parent back-pointer)         reader will assume deep

   is f an identity or a live resource ?     -> regenerate, or refuse to clone
        (uuid, socket, file handle, lock)         cost of a fresh acquisition
```

A shallow copy applies rule one to every field, including the second category.
A naive deep copy applies rule two to every field, including the third and
fourth, which duplicates connection pools and detonates on cyclic back-pointers
unless the algorithm tracks visited nodes. Python's `copy.deepcopy` addresses
the cycle problem by keeping a memo dictionary of objects already copied in the
current pass, per the Python 3 standard library documentation for `copy`,
https://docs.python.org/3/library/copy.html verified 2026-08-02.

## 8. Implementation variants

### 8a. Copy constructor

The copying operation is a constructor taking an instance of the same type.
Compile-time typed, no marker interfaces, no reflection, and every field
assignment is visible to a reviewer. The weakness is that it is statically
dispatched, so a variable of a base type calling `new Base(x)` where `x` is a
derived instance silently slices. Java and C# recover polymorphism by pairing
the copy constructor with a virtual `copy` method that each subclass overrides
to call its own copy constructor. This is the shape Bloch recommends over
`Cloneable` in *Effective Java*, 3rd edition, Item 13.

### 8b. Virtual clone method returning the concrete type

The classic GoF shape. Covariant return types, available in Java since 5 and in
C++ since the standard's covariant return rule, let `Circle.clone()` return
`Circle` while satisfying `Shape.clone()`. Preserves the dynamic type through a
base-typed reference. Requires every subclass author to remember to override,
and forgetting produces a copy of the wrong type with no compile error.

### 8c. The Java `Cloneable` mechanism

`Object.clone` produces a field-by-field copy without calling any constructor,
and throws `CloneNotSupportedException` unless the class implements `Cloneable`.
The javadoc states plainly that the contents of the fields are not themselves
cloned, so the built-in behaviour is a shallow copy, per the Java SE 21 API
documentation for `java.lang.Object`,
https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Object.html
verified 2026-08-02. The `Cloneable` interface itself declares no method, and
its own javadoc says that it does not contain the `clone` method and that it is
therefore not possible to clone an object merely because it implements the
interface, per
https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Cloneable.html
verified 2026-08-02. Section 11 treats this as a failure mode rather than a
recommendation.

### 8d. Registry of exemplars

A map from key to pre-configured prototype, handing out copies. Lets new
"types" be added at runtime by registering a new exemplar, which is the property
that makes Prototype a runtime-configurable substitute for Abstract Factory.
The registry must return copies, never the stored instance, or one client's
mutation poisons every later request.

### 8e. Serialisation round trip

Serialise the object and immediately deserialise it. Produces a deep copy with
no per-class copy code. In the browser this is a platform primitive.
`structuredClone(value)` runs `StructuredSerializeWithTransfer` and then
`StructuredDeserializeWithTransfer`, preserving object identity and circular
references, per the WHATWG HTML Standard, structured data section,
https://html.spec.whatwg.org/multipage/structured-data.html#structuredclone
verified 2026-08-02. Its limits are the serialiser's limits. The specification
throws a `DataCloneError` `DOMException` when the value is callable, and MDN
records the same outcome for DOM nodes, per
https://developer.mozilla.org/en-US/docs/Web/API/Window/structuredClone
verified 2026-08-02. The general trade-off holds outside the browser too.
Cheap to adopt, slow relative to hand-written copies, and silently lossy for
anything the serialiser does not model, including functions, class identity,
and transient fields.

### 8f. Reflection-based generic cloner

A library walks fields and copies them. Zero per-class code, and it is the
variant most likely to duplicate a connection pool or blow the stack on a cyclic
graph. Acceptable for plain data holders under test, hazardous for domain
objects.

### 8g. Shared substructure instead of copying

Persistent data structures share the untouched portion of the graph between the
original and the modified version, so a logical copy costs O(log n) rather than
O(n). Where the motivation for Prototype was branch-then-mutate, this variant
removes the copy entirely and is usually the better answer.

### 8h. Prototypal delegation, the JavaScript language-level realisation

This is a different mechanism with the same motivation, and conflating the two
is the most common error in writing about this pattern.
`Object.create(proto)` creates an object whose prototype is the supplied object,
per ECMAScript 2027, section 7.3.32, verified 2026-08-02 at the URL in section 1.
No state is copied. Property reads that miss on the created object walk up the
prototype chain to the exemplar, and property writes land on the created object,
shadowing the exemplar. MDN's own example demonstrates this precisely, with
`Object.create(person)` producing an object that inherits `isHuman` and then
overwrites it locally, verified 2026-08-02.

The consequences differ sharply from GoF cloning.

- Memory is O(1) per derived object rather than O(size of state), which is why a
  million objects sharing one prototype is routine in JavaScript engines.
- Later mutation of the exemplar is visible through every object that delegates
  to it and has not shadowed the field. In a copying prototype the exemplar is
  frozen at copy time. This is a semantic difference, not an optimisation
  detail, and it is the reason mutating a shared prototype in production is
  treated as a hazard.
- There is no depth question, because there is no copy, so the shallow-versus-deep
  problem is replaced by a shadowing-versus-inheriting problem.

When a JavaScript program genuinely needs the GoF semantics of an independent
copy, `structuredClone` in variant 8e, or an explicit copy method, is the tool.
`Object.create` is not a deep-copy mechanism and using it as one is a defect.

### 8i. Language notes

Go has no inheritance, so the pattern reduces to an interface with a `Clone`
method and a struct literal copy inside it. Assigning a struct copies it by
value already, which handles the scalar fields and leaves slices, maps, and
pointers to be copied explicitly. Rust splits the idea in the type system.
`Copy` is a bitwise duplicate for types with no ownership, and `Clone` is the
explicit, possibly expensive duplicate, which makes the shallow-versus-deep
decision a visible property of the type rather than a comment.

## 9. Known production uses

- **Kubernetes PodTemplate.** Workload resources such as Deployment, Job, and
  DaemonSet embed a `PodTemplate`, and the Kubernetes documentation states that
  each controller for a workload resource uses the `PodTemplate` inside the
  workload object to make actual Pods. This is a registry of exemplars driving
  runtime instantiation, with the template held as desired state rather than as
  a class. Source, Kubernetes documentation, Pods concept, Pod templates
  section, https://kubernetes.io/docs/concepts/workloads/pods/ verified
  2026-08-02.
- **Unity prefabs.** The Unity manual describes the prefab system as storing a
  GameObject with all its components, property values, and child GameObjects as
  a reusable asset that acts as a template, from which prefab instances are
  created in scenes. This is the interactive-authoring case from section 2, made
  a product feature. Source, Unity 6 Manual, Prefabs,
  https://docs.unity3d.com/6000.0/Documentation/Manual/Prefabs.html verified
  2026-08-02.
- **The web platform `structuredClone` API.** A deep-copy primitive standardised
  in the WHATWG HTML Standard, preserving circular references and object
  identity, and throwing `DataCloneError` on non-serialisable input. This is the
  serialisation variant promoted to a platform primitive. Source, WHATWG HTML
  Standard, https://html.spec.whatwg.org/multipage/structured-data.html#structuredclone
  verified 2026-08-02.
- **Django QuerySet refinement.** The Django documentation states that each time
  you refine a QuerySet you get a brand-new QuerySet that is in no way bound to
  the previous one, and that each refinement creates a separate and distinct
  QuerySet that can be stored, used, and reused. A base query is therefore an
  exemplar, and every `.filter()` produces a copy carrying the accumulated state.
  Source, Django 5.2 documentation, Making queries, Filtered QuerySets are
  unique, https://docs.djangoproject.com/en/5.2/topics/db/queries/ verified
  2026-08-02.
- **.NET `System.ICloneable`.** Present in the base class library since .NET
  Framework 1.1 and implemented by `System.Array`, `System.String`,
  `System.Collections.ArrayList`, `System.Globalization.CultureInfo`,
  `System.Xml.XmlNode`, and many more. Microsoft's own guidance now recommends
  against it in public APIs, which makes it a named production use and a cautionary
  one at the same time, see section 11. Source, Microsoft Learn, `ICloneable`
  Interface, https://learn.microsoft.com/en-us/dotnet/api/system.icloneable
  verified 2026-08-02.
- **JavaScript prototypal inheritance.** Every object literal, every constructor
  function, and every `class` in ECMAScript resolves property lookups through a
  prototype chain rooted in an exemplar object, with `Object.create` as the
  direct API. Source, ECMAScript 2027 Language Specification, section 7.3.32,
  https://tc39.es/ecma262/multipage/fundamental-objects.html#sec-object.create
  verified 2026-08-02.

## 10. Consequences

Positive.

- Creation cost drops to the cost of a copy, which for an object assembled from
  I/O is orders of magnitude cheaper.
- The client is decoupled from concrete classes. Adding a configuration means
  registering an exemplar, not writing and wiring a subclass.
- New "kinds" of object can be introduced at runtime, from user input or
  configuration, which no class-based factory can do without code generation.
- The class hierarchy stays flat. Prototype removes the parallel factory
  hierarchy that Factory Method tends to grow.
- The dynamic type is preserved through a base-typed reference, so heterogeneous
  collections can be duplicated correctly without a type switch.
- It composes with Composite naturally. A composite's clone recursively clones
  its children, giving whole-subtree duplication for free.

Negative.

- Every ConcretePrototype must implement its own copy correctly, and correctness
  is unverifiable by the compiler. Adding a field is a silent correctness change.
- Deep copying a graph with cycles requires a visited set. Without one the copy
  recurses until the stack dies.
- The copy operation bypasses constructors in some mechanisms, so constructor
  invariants and validation do not run on the clone.
- `final` and `readonly` fields resist assignment during copying, which forces
  either constructor-based copying or reflective writes.
- The call site loses information. `p.clone()` does not say what the object is or
  what it requires, so reading the code requires finding the registration.
- Memory grows with the number of clones for the copying variants, and cache
  locality degrades as the graph fragments across the heap.

## 11. Failure modes and misuse

- **The shallow copy that shares a mutable list.** The classic. `clone` copies
  the reference to an `ArrayList`, so appending to the clone's list mutates the
  original's. Observable symptom, an order acquires line items belonging to a
  different order, and the bug only reproduces when two orders are created from
  the same template within one request. The javadoc for `Object.clone` states
  that this shallow behaviour is the default, per the Java SE 21 documentation
  cited in section 8c.
- **The `Cloneable` contract nobody can honour.** `Cloneable` declares no method
  and `Object.clone` is `protected`, so a reference typed as `Cloneable` cannot
  be cloned at all. Bloch's assessment in *Effective Java*, 3rd edition, Item 13
  is that the interface fails at its stated purpose, that the mechanism requires
  a complex, unenforceable, thinly documented protocol from a class and all its
  superclasses, and that the result is fragile and creates objects without
  calling a constructor. His recommendation is a copy constructor or a copy
  factory instead. Observable symptom, a `CloneNotSupportedException` from a
  class three levels up in a hierarchy nobody on the team wrote, or a subclass
  whose `clone` returns a superclass instance because an intermediate class
  called `new` rather than `super.clone()`.
- **The unspecified `ICloneable`.** Microsoft's own remarks state that
  `ICloneable` does not specify whether the cloning operation performs a deep
  copy, a shallow copy, or something in between, nor does it require all
  property values to be copied, and that because callers cannot depend on the
  method performing a consistent cloning operation, they recommend that
  `ICloneable` not be implemented in public APIs. Source verified 2026-08-02 at
  the URL in section 9. Observable symptom, two libraries in one process
  disagree on the depth of `Clone()` and a shared configuration object is
  mutated across a boundary.
- **The cloned identity.** The copy carries the source's primary key or
  idempotency key. Observable symptom, a unique-constraint violation on insert,
  or worse, a successful upsert that overwrites the original row.
- **The cloned live resource.** The copy shares a socket, a file handle, or a
  mutex. Observable symptom, a double close, a "bad file descriptor" error, or a
  deadlock where two logically distinct objects contend on one lock they both
  believe they own.
- **Prototype used as a Singleton bypass.** A registry exemplar is handed out
  directly rather than copied, and clients treat it as their own. Observable
  symptom, configuration changes made by one request appear in unrelated
  requests.
- **The mutated shared JavaScript prototype.** Assigning to a prototype object at
  runtime changes behaviour for every object delegating to it, including objects
  created before the assignment. Observable symptom, a method's behaviour changes
  globally after an unrelated module loads, with no call to the affected objects.
- **Serialisation cloning that silently drops state.** Fields excluded from the
  wire format vanish from the copy. Observable symptom, a copied object works in
  every test that checks the fields the test author remembered, and loses a
  cached computation or a callback in production.
- **Cloning as premature optimisation.** The pattern is introduced because
  construction "felt slow", with no measurement, and the deep copy turns out to
  be slower than the constructor it replaced.

## 12. Trade-off matrix

Alternatives are named patterns and named mechanisms, compared across the forces
from section 3.

| Approach | Creation latency | Coupling to concrete types | Runtime extensibility | Consistency risk | Cognitive load |
|---|---|---|---|---|---|
| Prototype, deep copy | Low after the first build, O(graph) per copy | None, client sees one interface | High, register a new exemplar | Medium, cycles and borrowed refs | High, call site says nothing |
| Prototype, shallow copy | Lowest, O(fields) | None | High | High, shared mutable substructure | High, depth is invisible |
| Prototypal delegation, `Object.create` | Lowest, O(1), no state copied | None | Highest, exemplars are plain objects | High, exemplar mutation is visible downstream | Medium, chain lookup must be understood |
| Factory Method | Full construction cost each time | Subclass per product, compile time | Low, needs a new class and a rebuild | Low, constructor invariants run | Low, explicit |
| Abstract Factory | Full construction cost each time | Family of concrete classes behind interfaces | Low, a new family is a new class set | Low | Medium, extra indirection layer |
| Builder | Full construction cost, staged | Client names the builder | Medium, builder can be reconfigured | Low, validation on `build()` | Low, the steps are readable |
| Memento | Not a creation mechanism, restores state | None, opaque token | Not applicable | Low, state is snapshotted whole | Low, narrow purpose |
| Flyweight | Zero, instances are shared not created | None | Medium, keyed by intrinsic state | Zero for immutable state, fatal for mutable | Medium, intrinsic and extrinsic split |
| Persistent structure, shared substructure | O(log n) per logical copy | None | High | Low, immutability by construction | Medium, unfamiliar to many teams |
| Serialisation round trip | Highest per copy | None, no per-class code | High | Medium, lossy for unmodelled fields | Low to write, high to debug |

## 13. Related and incompatible patterns

- **Abstract Factory.** A direct alternative rather than a collaborator, and
  sometimes an implementation of one another. An Abstract Factory can store a set
  of prototypes and clone them to produce a family, which turns a compile-time
  family into a runtime-configurable one. In the other direction, where the set
  of families is fixed and known, Abstract Factory is clearer than a registry of
  exemplars.
- **Factory Method.** Prototype exists partly to avoid the parallel class
  hierarchy Factory Method creates. Choose Factory Method when the variation is
  by type and known at compile time. Choose Prototype when the variation is by
  state and decided at runtime.
- **Builder.** Complementary. A common shape builds a canonical exemplar once
  with a Builder, registers it, and then clones it per request. The Builder pays
  the validation cost once, and Prototype amortises it.
- **Composite.** Strongly complementary. Cloning a composite recursively clones
  its children, which is the whole-subtree duplication a diagram or scene editor
  needs. The recursion is also where cyclic parent back-pointers cause infinite
  descent, so the copy must decide that parent links are borrowed, not owned.
- **Decorator.** Cloning a decorated object must clone the decorator chain, or
  the copy shares its decorators with the original. Where the decorators are
  stateless this sharing is harmless. Where they hold state it is a defect.
- **Memento.** Adjacent and often confused. Memento captures state for later
  restoration into the same object, with an opaque token and an explicit
  originator. Prototype produces a new, independently usable object. Reach for
  Memento for undo, and Prototype for branch.
- **Flyweight.** In tension. Flyweight exists to avoid creating many objects by
  sharing immutable intrinsic state. Prototype exists to create many objects
  cheaply by copying. Applying both to one type is a design error, because the
  copy defeats the sharing that gives Flyweight its purpose.
- **Singleton.** In direct conflict. A Singleton must have exactly one instance,
  and a copy operation on it violates the invariant. If a type is a Singleton, it
  must not implement a public copy operation.
- **Value Object.** Not a conflict, but a replacement in most cases. An immutable
  value object needs no clone, because sharing the reference is already safe.
  A `withX()` returning a modified copy is the value-object idiom that covers the
  branch-then-mutate motivation without the depth question.

## 14. Refactoring path in and out

Introducing Prototype into code that lacks it.

1. Identify the expensive construction. Measure it. If the construction is not
   far more expensive than an equivalent deep copy, stop here.
2. Extract the configuration into a single, fully assembled instance built once
   during startup. This is the exemplar. At this point nothing has been cloned
   and the code still works.
3. Classify every field of the type against the four-way test in section 7,
   writing the classification down as a comment or a test. This step is where the
   correctness of the whole refactoring is decided.
4. Add a copy constructor or a copy factory that implements that classification.
   Prefer the constructor form, per *Effective Java*, 3rd edition, Item 13, so a
   reviewer sees each field assignment.
5. Add a test asserting independence. Mutate every mutable field of the copy and
   assert the exemplar is unchanged, then do the reverse. See section 15.
6. Replace the expensive construction at each call site with a copy of the
   exemplar plus the per-call-site field assignments.
7. Only when several exemplars exist, introduce the registry, and make its
   accessor return a copy rather than the stored instance.

Related named refactorings. Replace Constructor with Factory Method, then Replace
Factory Method with Prototype, are the two steps Fowler-style catalogues describe
for the first half of this path.

Removing Prototype when it stops earning its place.

1. Measure again. The usual trigger for removal is that the exemplar became small,
   or the deep copy became larger than the construction it replaced.
2. Inline the exemplar's configuration back into a constructor or a Builder.
3. Replace each `clone()` call site with the explicit construction, one call site
   at a time, keeping the independence test green throughout.
4. Delete the registry, then the copy constructor, then the Prototype interface,
   in that order, so each deletion is a compile error at exactly the remaining
   call sites.
5. If the motivation was branch-then-mutate rather than construction cost, do not
   inline. Convert the type to an immutable value with `withX()` methods, or to a
   persistent structure, and remove the copy operation as a side effect.

## 15. Testing and verification

What becomes easy.

- Substituting test doubles is trivial. Register a stub exemplar in the registry
  and every client receives copies of it, with no factory wiring and no dependency
  injection container.
- Fixture setup is fast. Build one fully populated aggregate in a test helper and
  clone it per test case, which removes per-test construction cost and keeps each
  test isolated.
- Deterministic tests get easier where the exemplar can pin values that a
  constructor would otherwise derive from the clock or a random source.

What becomes harder, and the specific tests that address it.

- **The independence test.** For every mutable field, mutate it on the copy and
  assert the original is unchanged, then mutate it on the original and assert the
  copy is unchanged. This is the test that catches the shallow-copy defect, and
  it must be written per field, not per class.
- **The completeness test.** Assert that the copy equals the original under a
  value comparison immediately after copying. Pair it with a reflection-driven or
  code-generated field enumeration so that adding a field to the class fails the
  test until the copy is updated. Without this, the copy silently rots.
- **The dynamic type test.** For each subclass, assert that copying through a
  base-typed reference returns an instance of the subclass. This catches the
  missing override in variant 8b.
- **The cycle test.** Build a graph containing a cycle and copy it. A correct
  deep copy terminates and reproduces the cycle. An incorrect one overflows the
  stack, which is a loud and useful failure.
- **The identity test.** Assert that identity fields differ between the copy and
  the original where they are supposed to be regenerated, and match where they
  are supposed to be carried.
- **The resource test.** Assert that borrowed resources, a connection pool or a
  logger, are the same reference in the copy, which is the deliberate sharing,
  and that owned resources are distinct.

Applicable techniques. Property-based testing fits this pattern unusually well,
because the invariant "for all objects x, copy(x) is equal to x and mutations of
copy(x) are invisible from x" is expressible directly as a property over
generated instances. A spy on the borrowed collaborator verifies that copying did
not duplicate it. Mutation testing is a good fit for the completeness test,
because a mutant that drops a field assignment from the copy operation should be
killed by it.

## 16. Observability signals

What to record.

- A counter of clone operations, tagged by prototype key. In a registry-backed
  system this is the closest thing to a demand signal per configuration.
- A histogram of clone duration, tagged by prototype key. Deep copies of graphs
  that grow over time show up here before they show up as latency complaints.
- A histogram or gauge of copied graph size, in nodes or in bytes, per prototype
  key. This is the metric that distinguishes a slow copy from a large copy.
- A counter of copy failures, tagged by cause, separating unsupported-type
  failures from resource-acquisition failures.
- A gauge of registered exemplars, which detects registry leaks where dynamic
  registration is exposed to callers.
- A span around the copy when the copy is on a request path, as a child of the
  request span, with the prototype key as an attribute. A copy that is invisible
  in a trace is a copy nobody will find when it becomes the bottleneck.

What healthy looks like. Clone duration is flat over time and small relative to
the request budget. Copied graph size is flat. The ratio of clone operations to
requests is stable and matches the expected fan-out. Registered exemplar count is
constant after startup.

What failing looks like.

- Clone duration and copied graph size both climb together over days. The
  exemplar is accumulating state, usually because something is writing to the
  registry's stored instance rather than to its copy.
- Clone duration climbs while graph size is flat. Contention, most often a lock
  taken during copying, or allocation pressure from copy churn.
- Heap grows in step with the clone counter and does not recover. Clones are
  being retained, often by a cache keyed on something that differs per copy.
- Stack-overflow errors correlated with one prototype key. A cycle reached a copy
  path that has no visited set.
- A rise in unique-constraint violations shortly after a new exemplar is
  registered. An identity field is being copied rather than regenerated.

## 17. Security and privacy implications

- **Copies multiply the number of places sensitive data lives.** Cloning an
  object that holds a credential, a token, a decrypted key, or personal data
  creates a second copy on the heap with its own lifetime. Zeroisation of the
  original does not touch the copy. Where a type holds a secret value, the copy
  operation should either refuse or explicitly exclude the secret field and
  require the caller to re-supply it.
- **Data retention and deletion obligations propagate to copies.** A deletion
  request satisfied against an exemplar is not satisfied against long-lived
  clones. Any system that clones records carrying personal data needs the clones
  to be reachable from the same deletion path, which in practice means clones
  must carry a link back to the subject rather than a detached copy of the data.
- **Deserialisation-based cloning inherits deserialisation vulnerabilities.**
  Variant 8e reuses a serialiser. Where that serialiser is one that instantiates
  arbitrary types from the payload, in-process cloning is a safe use, because the
  input is trusted, but the same code path must never be pointed at untrusted
  input. Keeping the clone path and the wire path on separate serialiser
  configurations avoids a later refactoring turning a safe clone into an unsafe
  ingest.
- **Shallow copies can widen access unintentionally.** If a permission set, an
  access-control list, or a tenant scope is a mutable collection shared by a
  shallow copy, granting a permission on one object grants it on the other. Where
  the two objects belong to different tenants or different principals, this is a
  privilege-escalation bug rather than an aliasing bug.
- **Reflection-based cloners can read fields the type intended to hide.** Variant
  8f bypasses access modifiers by design, which defeats encapsulation as a
  defence and can copy fields deliberately excluded from the type's public
  surface.
- **Uncapped cloning is a denial-of-service surface.** Where the size of the
  copied graph is attacker-influenced, for example a template a user may nest,
  each clone multiplies the work. Bound the graph depth and size before copying,
  not after.
- **Where the pattern is silent.** Prototype has no bearing on transport
  security, authentication, or authorisation decisions themselves. It neither
  opens nor closes those surfaces, and claiming otherwise would be invention.

## Code examples

### TypeScript

Copy method with an explicit depth decision per field, plus a registry that
hands out copies rather than exemplars.

```typescript
interface Prototype<T> {
  clone(): T;
}

interface Logger {
  log(msg: string): void;
}

class ReportSpec implements Prototype<ReportSpec> {
  constructor(
    readonly id: string,
    readonly title: string,
    readonly columns: string[],
    readonly logger: Logger,
  ) {}

  clone(): ReportSpec {
    return new ReportSpec(
      crypto.randomUUID(),
      this.title,
      [...this.columns],
      this.logger,
    );
  }

  withTitle(title: string): ReportSpec {
    return new ReportSpec(this.id, title, [...this.columns], this.logger);
  }
}

class Registry<T extends Prototype<T>> {
  private readonly exemplars = new Map<string, T>();

  register(key: string, exemplar: T): void {
    this.exemplars.set(key, exemplar);
  }

  create(key: string): T {
    const exemplar = this.exemplars.get(key);
    if (!exemplar) throw new Error(`no exemplar for ${key}`);
    return exemplar.clone();
  }
}

const logger: Logger = { log: (m) => console.log(m) };
const registry = new Registry<ReportSpec>();
registry.register(
  "eu-b2b",
  new ReportSpec("template-0", "EU B2B", ["net", "vat"], logger),
);

const a = registry.create("eu-b2b");
const b = registry.create("eu-b2b");
a.columns.push("gross");
console.log(a.columns.length, b.columns.length);
console.log(a.id !== b.id, a.logger === b.logger);
```

The identity is regenerated, the owned array is copied, and the borrowed logger
is shared on purpose. For a value with no owned mutable state,
`structuredClone` from variant 8e replaces the whole method.

### Python

Hooking the standard library so `copy.copy` and `copy.deepcopy` carry the type's
own rules, including the memo dictionary that makes cyclic graphs terminate.

```python
import copy
import uuid


class Connection:
    def __init__(self, dsn):
        self.dsn = dsn


class Node:
    def __init__(self, label, conn):
        self.id = uuid.uuid4()
        self.label = label
        self.children = []
        self.parent = None
        self.conn = conn

    def add(self, child):
        child.parent = self
        self.children.append(child)
        return self

    def __copy__(self):
        new = Node(self.label, self.conn)
        new.children = self.children
        return new

    def __deepcopy__(self, memo):
        if id(self) in memo:
            return memo[id(self)]
        new = Node.__new__(Node)
        memo[id(self)] = new
        new.id = uuid.uuid4()
        new.label = self.label
        new.conn = self.conn
        new.children = [copy.deepcopy(c, memo) for c in self.children]
        for c in new.children:
            c.parent = new
        new.parent = None
        return new


conn = Connection("postgres://localhost/app")
root = Node("root", conn).add(Node("a", conn)).add(Node("b", conn))

deep = copy.deepcopy(root)
deep.children[0].label = "changed"

print(root.children[0].label, deep.children[0].label)
print(root.id != deep.id, root.conn is deep.conn)
```

The parent back-pointer is rebuilt rather than followed, which is what keeps a
cyclic graph from being duplicated twice. The connection is shared because it is
borrowed, not owned.

### Go

No inheritance, so the pattern is an interface plus a struct-literal copy. Struct
assignment already copies scalars by value, which leaves slices, maps, and
pointers as the explicit work.

```go
package main

import (
	"fmt"
	"maps"
	"slices"
)

type Pool struct{ dsn string }

type Prototype interface {
	Clone() Prototype
}

type Job struct {
	Name    string
	Args    []string
	Env     map[string]string
	Pool    *Pool
	attempt int
}

func (j *Job) Clone() Prototype {
	c := *j
	c.Args = slices.Clone(j.Args)
	c.Env = maps.Clone(j.Env)
	c.attempt = 0
	return &c
}

func main() {
	pool := &Pool{dsn: "postgres://localhost/app"}
	base := &Job{
		Name: "reindex",
		Args: []string{"--full"},
		Env:  map[string]string{"REGION": "eu"},
		Pool: pool,
	}

	a := base.Clone().(*Job)
	b := base.Clone().(*Job)
	a.Args = append(a.Args, "--verbose")
	a.Env["REGION"] = "us"

	fmt.Println(len(a.Args), len(b.Args))
	fmt.Println(a.Env["REGION"], b.Env["REGION"])
	fmt.Println(a.Pool == b.Pool)
}
```

`slices.Clone` and `maps.Clone` copy one level. A nested slice of slices needs a
loop, which is the shallow-versus-deep decision made visible in code.

### Java

The copy-constructor form recommended in *Effective Java*, 3rd edition, Item 13,
paired with an overridable `copy` method so the dynamic type survives a
base-typed reference. No `Cloneable`, no `CloneNotSupportedException`.

```java
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

abstract class Shape {
    private final UUID id;
    private final List<String> tags;

    protected Shape(List<String> tags) {
        this.id = UUID.randomUUID();
        this.tags = new ArrayList<>(tags);
    }

    protected Shape(Shape other) {
        this.id = UUID.randomUUID();
        this.tags = new ArrayList<>(other.tags);
    }

    public abstract Shape copy();

    public UUID id() { return id; }
    public List<String> tags() { return tags; }
}

final class Circle extends Shape {
    private final double radius;

    Circle(double radius, List<String> tags) {
        super(tags);
        this.radius = radius;
    }

    private Circle(Circle other) {
        super(other);
        this.radius = other.radius;
    }

    @Override public Circle copy() { return new Circle(this); }

    double radius() { return radius; }
}

public class Demo {
    public static void main(String[] args) {
        Shape base = new Circle(2.0, List.of("ui"));
        Shape dup = base.copy();
        dup.tags().add("copied");

        System.out.println(base.tags().size() + " " + dup.tags().size());
        System.out.println(base.id().equals(dup.id()));
        System.out.println(dup.getClass().getSimpleName());
    }
}
```

`copy` is covariantly typed on `Circle`, so a subclass author who forgets to
override gets a compile error at the abstract method rather than a silently
wrong type at runtime.

### Languages omitted, and why

Rust is omitted from the worked examples because the pattern does not survive
translation as a pattern. The language splits it into two derivable traits,
`Copy` for a bitwise duplicate of types that own nothing and `Clone` for an
explicit duplicate, and the ownership system forbids the aliasing bug that
section 11 lists first. Writing a Prototype interface in Rust reimplements
`Clone` with less type-system support. Swift and Kotlin are omitted for a related
reason. Both make value semantics the default for structs and data classes, and
Kotlin's generated `copy()` on a data class covers the shallow case without a
pattern, leaving only the deep-copy decision, which is the same decision already
shown in the Python and Go examples.

## 18. References

Books.

1. Gamma, Erich; Helm, Richard; Johnson, Ralph; Vlissides, John. *Design
   Patterns. Elements of Reusable Object-Oriented Software*. Addison-Wesley,
   1994. Chapter 3, Creational Patterns, the Prototype pattern. ISBN
   0-201-63361-2.
2. Bloch, Joshua. *Effective Java*, 3rd edition. Addison-Wesley, 2018. Chapter 3,
   Methods Common to All Objects, Item 13, "Override clone judiciously". ISBN
   978-0-13-468599-1. The item title and argument, that `Cloneable` fails as a
   mixin interface because it contains no `clone` method, that the protocol is
   complex and unenforceable, and that a copy constructor or copy factory is the
   better approach, were confirmed by web search on 2026-08-02.

Specifications and standards.

3. ECMA International. *ECMAScript Language Specification*, `Object.create ( O,
   Properties )`, section 7.3.32.
   https://tc39.es/ecma262/multipage/fundamental-objects.html#sec-object.create
   Verified 2026-08-02.
4. WHATWG. *HTML Standard*, Structured data, `structuredClone(value, options)`.
   https://html.spec.whatwg.org/multipage/structured-data.html#structuredclone
   Verified 2026-08-02. Confirms the serialise-then-deserialise algorithm,
   preservation of circular references and object identity, and the
   `DataCloneError` `DOMException` thrown when the value is callable.

Language and platform documentation.

5. Oracle. *Java SE 21 API Documentation*, `java.lang.Object`, `clone()`.
   https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Object.html
   Verified 2026-08-02. Confirms the shallow-copy default and the
   `CloneNotSupportedException` behaviour.
6. Oracle. *Java SE 21 API Documentation*, `java.lang.Cloneable`.
   https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Cloneable.html
   Verified 2026-08-02. Confirms that the interface contains no `clone` method
   and that implementing it alone does not make an object cloneable.
7. Python Software Foundation. *Python 3 Standard Library*, `copy`, Shallow and
   deep copy operations. https://docs.python.org/3/library/copy.html
   Verified 2026-08-02. Confirms the shallow and deep definitions, `__copy__`
   and `__deepcopy__`, and the memo dictionary used to handle recursive objects.
8. Microsoft. *.NET API Documentation*, `System.ICloneable` Interface.
   https://learn.microsoft.com/en-us/dotnet/api/system.icloneable
   Verified 2026-08-02. Confirms that the interface does not specify copy depth
   and that Microsoft recommends it not be implemented in public APIs.
9. Mozilla. *MDN Web Docs*, `Object.create()`.
   https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/create
   Verified 2026-08-02. Confirms delegation semantics and property shadowing.
10. Mozilla. *MDN Web Docs*, `Window.structuredClone()`.
    https://developer.mozilla.org/en-US/docs/Web/API/Window/structuredClone
    Verified 2026-08-02. Confirms circular-reference handling and the
    `DataCloneError` on functions and DOM nodes.

Production systems.

11. The Kubernetes Authors. *Kubernetes Documentation*, Concepts, Workloads,
    Pods, Pod templates section.
    https://kubernetes.io/docs/concepts/workloads/pods/
    Verified 2026-08-02.
12. Unity Technologies. *Unity 6 Manual*, Prefabs.
    https://docs.unity3d.com/6000.0/Documentation/Manual/Prefabs.html
    Verified 2026-08-02.
13. Django Software Foundation. *Django 5.2 Documentation*, Making queries,
    Filtered QuerySets are unique.
    https://docs.djangoproject.com/en/5.2/topics/db/queries/
    Verified 2026-08-02.
