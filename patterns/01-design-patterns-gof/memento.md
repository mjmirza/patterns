---
name: Memento
slug: memento
family: 01-design-patterns-gof
category: Behavioral
aliases: [Token, Snapshot, Cookie]
first_described: "Gamma, Helm, Johnson, Vlissides 1994"
maturity: canonical
related: [command, prototype, iterator, state, observer, builder]
incompatible_with: []
verified: 2026-08-02
---

# Memento

## 1. Name, aliases, and lineage

The canonical name is Memento. It appears in the Gang of Four catalog among the
eleven behavioral patterns, described in Erich Gamma, Richard Helm, Ralph
Johnson and John Vlissides, *Design Patterns. Elements of Reusable
Object-Oriented Software*, Addison-Wesley, 1994, chapter 5 (Behavioral
Patterns), Memento. The stated purpose is to capture and externalize an
object's internal state so that the object can be restored to that state later,
without exposing the internals to whoever holds the captured state
([Wikipedia summary of the pattern and its participants](https://en.wikipedia.org/wiki/Memento_pattern),
verified 2026-08-02).

The book records **Token** as the alias, which comes from the way the captured
state is handed to a client as an opaque ticket that can only be redeemed by
the object that issued it. Two further names occur widely enough in practice to
be worth recognising.

- **Snapshot.** The usual word outside the patterns literature. Databases,
  stream processors, virtual machine hypervisors and version control systems
  all say snapshot when they mean the same idea at a larger granularity. Apache
  Flink documents a savepoint as "a consistent image of the execution state of a
  streaming job"
  ([Apache Flink savepoints documentation](https://nightlies.apache.org/flink/flink-docs-stable/docs/ops/state/savepoints/),
  verified 2026-08-02), which is Memento applied to a distributed dataflow.
- **Cookie.** An older term from user interface toolkits, where a widget
  returned an opaque cookie that the framework stored and handed back on
  restore. The word survives in web protocols with a different meaning and
  should be avoided in new writing because it now misleads more than it helps.

Three things are routinely called a Memento and only one of them is the
pattern. Separating them early prevents most of the bad implementations
described in dimension 11.

- **Memento proper (GoF).** A capture of another object's private state, held
  by a third party that cannot read it, and handed back to the originating
  object to reverse a change. The defining property is asymmetric access. The
  holder can store, order, discard and pass the object around. The holder
  cannot interpret it.
- **A serialized copy.** A byte array or JSON document produced by a generic
  serializer. It captures state, so it satisfies the mechanical half of the
  pattern, and it violates the encapsulation half completely, because anyone
  holding the bytes can parse them. It is a legitimate implementation strategy
  with a named cost, discussed in dimension 8.
- **A value object copy.** In a language with immutable records, keeping the
  previous value of a field is often written up as Memento in blog posts. It is
  not. If the previous value is already a public, readable, independently
  useful type, no encapsulation is being protected and the pattern's
  distinguishing property is absent. Copying an immutable value is copying an
  immutable value.

A useful test. Hand the captured object to a class that is not the originator
and ask whether that class can make a decision from its contents. If it can,
the design is a state copy with extra ceremony. If the compiler stops it, the
design is Memento.

## 2. Problem and context

An object holds state that changes over time, and something outside that object
needs the ability to put the state back the way it was. The object's fields are
private for good reasons, and the code that will trigger the restore has no
business knowing what those fields are.

The situation reads like this in a codebase. There is an editor, a form, a
diagram tool, a game session, a wizard, a configuration screen, or a
long-running calculation. A user action mutates it. The product then asks for
one of four things that all reduce to the same requirement.

- Undo, so the last action can be reversed.
- A checkpoint, so a long operation can be retried from a known point rather
  than from the beginning.
- A transaction boundary, so a group of mutations either all take effect or
  none do.
- A named save state, so the user can branch and come back.

The first implementation attempt is almost always the same. The code that wants
to restore reaches into the object, reads the fields it thinks matter, keeps
copies, and writes them back later. That works exactly once. It fails the
moment a new field is added and nobody updates the copying code, and it fails
permanently the moment the object's invariants involve more than one field,
because a partial restore leaves an object that compiles and is wrong. Making
the fields public to enable the copy is the second attempt, and it converts a
local problem into a global one, because every other caller now sees the
internals too.

The next attempt is a `clone()` or a copy constructor returning the object
itself. This preserves the invariants but hands out a fully functional live
object. The undo stack now holds a hundred usable editors rather than a hundred
inert records, and any bug that treats one of them as the current editor
produces state that is very hard to reason about.

The context that makes Memento the right answer has four parts.

- The state to capture is genuinely private, and exposing it would let callers
  build logic on internals that are meant to change.
- Restoration must be atomic. Either the whole prior state comes back or none
  of it does.
- The party that decides *when* to save and restore is a different party from
  the one that knows *what* the state is. Separation of those two
  responsibilities is the entire point.
- The state is small enough, or the save frequency low enough, that copying it
  is affordable. Where that fails, the pattern is replaced rather than tuned,
  see dimension 4 and the command-based alternative in dimension 8.

Outside that context the pattern is overhead at best and a memory leak at
worst.

## 3. Forces

The pattern balances the following competing pressures.

- **Encapsulation.** Strongly favoured. This is the force the pattern exists to
  serve, and every other property is subordinate to it. State leaves the object
  in a form no other object can read.
- **Memory.** Sacrificed, sometimes severely. A snapshot of size S taken N times
  costs N times S until something evicts it. The cost is proportional to state
  size rather than to change size, which is the wrong proportionality for most
  editing workloads and is the single most common reason implementations are
  ripped out.
- **Latency.** Sacrificed at capture time, favoured at restore time. Capture
  copies the whole state, so its cost grows with state size. Restore is a
  single assignment of an already-built object, so it is fast and its cost does
  not vary with how much history exists. That is the opposite profile from a
  command-based undo, where restore cost grows with how far back you go.
- **Coupling.** Favoured between caretaker and originator. The caretaker needs
  no knowledge of the state's shape, so a generic undo stack can serve any
  originator. Sacrificed inside the originator, because the originator now owns
  both the capture and the restore logic and those two must stay in step.
- **Consistency.** Strongly favoured. A snapshot taken at one instant restores
  as a unit, so multi-field invariants survive. This is the property that
  separates Memento from a field-by-field rollback, which can produce
  combinations that never existed.
- **Operability.** Mixed. Snapshots make a system explainable, because an
  operator can see how far back recovery reaches. They also make it opaque,
  because the snapshot contents cannot be inspected without the originator, so
  a corrupt snapshot is hard to diagnose from the outside.
- **Cognitive load.** Mildly sacrificed. Three collaborating roles replace one
  mutable object, and the narrow-versus-wide interface trick that protects the
  memento is unfamiliar to most readers on first encounter.
- **Cost of change.** Sacrificed when the state shape changes. Every new field
  needs to be added to capture and restore, and if snapshots are persisted, old
  snapshots must still load. That is the versioning problem in dimension 8.
- **Team topology.** Favoured. The team owning the originator owns the state
  shape and can change it freely as long as capture and restore stay
  consistent. The team owning the history stack never has to be consulted.

The pattern trades memory and change cost for encapsulation and atomic
restore. A description that does not name the memory cost is describing
something else.

## 4. Applicability and non-applicability

Reach for Memento when the following hold.

- A snapshot of an object's state must be taken so it can be restored later,
  and the object's internals must stay private.
- The state is small relative to available memory, or the number of retained
  snapshots is bounded by an explicit policy.
- Restoration must be all or nothing, because the state has invariants spanning
  several fields.
- A direct interface exposing enough state to allow external copying would
  widen the object's public surface in ways the design does not want to commit
  to.
- The originator is the only party qualified to decide what "state" means,
  including which caches, derived values and transient handles to exclude.
- Restore latency matters more than capture latency, for example an editor
  where undo must feel instant but typing already costs a repaint.

Do NOT reach for Memento in these cases. The non-applicability list is the
half most catalogs omit, and the reasons matter more than the rules.

- **The state is large and changes are small.** A word processor holding a
  fifty megabyte document and snapshotting on every keystroke will exhaust
  memory within a page of typing. The correct shape is Command with inverse
  operations, or an incremental snapshot that stores only what changed. Redis
  documents exactly this trade for a whole datastore, contrasting point-in-time
  RDB snapshots against an append-only log of write operations replayed at
  restart, and notes that a snapshot every five minutes means being "prepared
  to lose the latest minutes of data" while the log costs more disk and more
  write amplification
  ([Redis persistence documentation](https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/),
  verified 2026-08-02).
- **The state contains handles that cannot be copied.** Open sockets, file
  descriptors, GPU textures, database connections and thread references do not
  survive a snapshot. A Memento containing them is a snapshot that restores a
  dead object. Either exclude them and rebuild on restore, which Python's
  pickle protocol supports through `__getstate__` and `__setstate__`, or accept
  that this object is not snapshottable.
- **The object is already immutable.** Keeping the previous value of an
  immutable object is a variable assignment. Building a Memento role around it
  adds three types and protects nothing.
- **Restoration must be selective.** If the requirement is to undo one field
  while keeping later changes to another, a whole-state snapshot cannot express
  it. That requirement calls for per-field change records, or the merge layer
  that collaborative editors use, and forcing Memento onto it produces the
  lost-update bug described in dimension 11.
- **The history must be inspected, queried or audited.** An opaque memento
  cannot answer "which user changed the discount". A change log with typed,
  readable entries can. Where both audit and rollback are needed, event
  sourcing subsumes the pattern and the memento becomes a cached projection
  rather than the record of truth.
- **The snapshot must cross a process or version boundary and stay valid.**
  Persisting mementos turns an in-memory concern into a schema evolution
  problem with all the usual costs, see dimension 8.
- **The language has no way to restrict access to the memento's contents.** In
  Python, Ruby and pre-2022 JavaScript the encapsulation half of the pattern
  cannot be enforced, only documented. That does not make the pattern useless
  there, but it does mean the reviewer should stop calling the discipline a
  guarantee, see dimension 5.
- **A single global undo across many objects is the actual requirement.**
  Snapshotting every participating object on every action multiplies the memory
  cost by the object count. A command stack recording one reversible operation
  per user action costs one small record regardless of how many objects that
  action touched.

## 5. Structure

Three participants, named by the role each plays, plus the access rule that
distinguishes the pattern from a state copy.

- **Originator.** The object whose state is being captured. It creates the
  memento, choosing what belongs in it, and it is the only participant that can
  read a memento back. It exposes two operations to the outside world, one that
  produces a memento and one that consumes a memento to restore itself. It
  exposes nothing else about its state.
- **Memento.** The captured state. It has two conceptual interfaces. A **wide
  interface** giving full read access to the stored fields, visible only to the
  originator. A **narrow interface** giving close to nothing, visible to
  everyone else, often only an identity, a timestamp and a human-readable
  label. The memento should be immutable after construction, because a
  caretaker that can mutate a memento can corrupt history without ever reading
  it.
- **Caretaker.** The object that decides when a snapshot is taken, keeps the
  snapshots, orders them, bounds their number, and hands one back on request.
  An undo stack, a checkpoint manager, a transaction scope. It only ever sees
  the narrow interface. It never creates a memento itself and never modifies
  one.

The relationships. The Caretaker holds an aggregation of Mementos and a
reference to the Originator, or receives the Originator per call. The
Originator has a creation dependency on Memento and a read dependency that no
other type possesses. The Memento depends on nothing, which is what allows it
to be stored anywhere.

**The encapsulation rule, stated plainly.** Only the Originator may read a
Memento's state. The Caretaker's contract is to hold and return, not to
interpret. Any code path where a non-originator reads a memento field breaks
the pattern, and the break is usually silent, because the code still works. It
stops working when the originator's state shape changes and the outside reader
was not updated.

Whether that rule is a compiler guarantee or a code review convention depends
entirely on the language. This is the practical fact most treatments skip.

Languages that can enforce it mechanically.

- **C++.** The classical answer from the GoF era. The Memento declares the
  Originator a friend, so the Originator alone reaches the private members while
  every other translation unit sees an empty public interface. This is the only
  mainstream mechanism that grants access to one named type and no other.
- **Java.** Two workable forms. A private static nested class inside the
  Originator, exposed publicly through a marker interface or `Object`, gives
  full enforcement, because the nested type's members are reachable from the
  enclosing class and nowhere else. Alternatively a package-private memento in
  the same package as the originator restricts access to the package, which is
  weaker but survives having several collaborating classes. Sealed interfaces
  and records added since Java 17 make the nested form terse without weakening
  it.
- **C#.** The same nested-private-class technique works, and the memento is
  usually surfaced as a public marker interface with no readable members. The
  originator casts back to the concrete type on restore. Access is enforced by
  the compiler.
- **Kotlin.** `internal` restricts to the compilation module, and a `private`
  nested class inside the originator restricts to the enclosing class, matching
  the Java forms.
- **Swift.** `private` at file scope restricts to the enclosing declaration, and
  `fileprivate` restricts to the file. Placing originator and memento in one
  file with `private` stored properties enforces the rule without any nesting.
- **Go.** There is no class-level access control, only package-level. An
  unexported struct with unexported fields, placed in the same package as the
  originator and returned through an exported empty interface, gives
  package-scoped enforcement. Anything in the same package can still read it, so
  the package must be kept small for the guarantee to mean much.
- **Rust.** Module privacy is the mechanism. A struct with private fields
  declared in the same module as the originator, exposed to the outside as an
  opaque type, cannot be read from another module. Rust also gives the strongest
  available answer to the mutability half, because an owned, non-`Clone` memento
  cannot be aliased at all.

Languages that cannot enforce it.

- **Python.** Attribute privacy is a naming convention. A leading `_` documents
  intent, and the name mangling triggered by a leading `__` obstructs casual
  access without preventing it, since the mangled name remains reachable and
  `__dict__` exposes everything regardless. The rule is a review convention.
- **JavaScript and TypeScript.** TypeScript's `private` keyword is erased at
  compile time and provides no runtime protection whatsoever. ECMAScript
  `#private` fields are genuinely inaccessible at runtime, but they are private
  to the declaring class, so a memento with `#private` fields cannot be read by
  the originator either. The workable form is a closure capturing the state and
  returning a restore function, which enforces the rule properly at the cost of
  making the memento a function rather than a record.
- **Ruby.** `private` can be defeated with `send`, so the same convention-level
  status applies.

The honest summary. In C++, Java, C#, Kotlin, Swift, Rust and, at package
granularity, Go, the encapsulation rule is a compiler guarantee. In Python,
Ruby and idiomatic TypeScript it is a promise, and treating a promise as a
guarantee is how the leak in dimension 11 happens.

## 6. ASCII structure diagram

```
   +---------------------------+                 +-------------------------+
   |        Caretaker          |    stores       |        Memento          |
   |---------------------------|  ------------>  |-------------------------|
   | - history: List<Memento>  |    (narrow      |  narrow interface:      |
   | + save(o: Originator)     |     interface   |   + label(): String     |
   | + undo(o: Originator)     |     only)       |   + takenAt(): Instant  |
   +---------------------------+                 |-------------------------|
                 |                                |  wide interface:        |
                 | calls save()/restore()         |   ~ getState(): State   |
                 v                                |   (visible ONLY to      |
   +---------------------------+                  |    Originator)          |
   |        Originator         |   creates        +-------------------------+
   |---------------------------|  -------------------------^
   | - state: State (private)  |                            |
   | + save(): Memento         |   reads back               |
   | + restore(m: Memento)     |  <-------------------------+
   | + businessOperation()     |
   +---------------------------+

   The Caretaker never crosses the wide interface. That single restriction
   is the pattern. Remove it and this is a state copy with three classes.
```

## 7. Dynamics

The runtime flow has two properties worth stating plainly. First, the Caretaker
initiates capture but never performs it. Second, the Memento travels through
the Caretaker untouched, which is why the Caretaker can be entirely generic.

```
Client            Caretaker            Originator            Memento
  |                   |                     |                    |
  |-- edit() -------->|                     |                    |
  |                   |-- save() ---------->|                    |
  |                   |                     |-- new Memento(state) -->|
  |                   |                     |<-- memento --------|    |
  |                   |<-- memento ---------|                    |
  |                   |  push onto history  |                    |
  |                   |  (narrow view only) |                    |
  |                   |                     |                    |
  |-- apply change -->|                     |                    |
  |                   |-- mutate() -------->|                    |
  |                   |                     |  state changes     |
  |                   |                     |                    |
  |-- undo() -------->|                     |                    |
  |                   |  pop from history   |                    |
  |                   |-- restore(memento) ->|                    |
  |                   |                     |-- read wide iface ->|
  |                   |                     |<-- state ----------|
  |                   |                     |  state replaced    |
  |<-- ok ------------|                     |                    |
  |                   |                     |                    |
```

Three ordering rules govern correctness and are the source of most bugs.

**Capture happens before the mutation, not after.** An undo stack that pushes a
snapshot after applying the change restores the state the user already sees, so
the first undo appears to do nothing and every subsequent undo is off by one.
The rule is to snapshot the pre-change state at the moment the command is
accepted.

**Redo requires a second stack, and the redo stack is cleared by any new
edit.** After an undo, the popped snapshot moves to a redo stack. When the user
performs a fresh edit instead of a redo, every entry on the redo stack is now
unreachable and must be discarded, otherwise a later redo grafts an alternate
timeline onto the current one and produces a state the user never created.

**Capture must be atomic with respect to concurrent mutation.** If another
thread mutates the originator while the memento is being built, the snapshot
records a state that never existed as a whole. Either take the snapshot under
the same lock that guards mutation, or make the originator's state an immutable
value so the snapshot is a reference copy that cannot tear.

## 8. Implementation variants

**Full state copy.** The memento holds a deep copy of everything. Simplest to
write, simplest to reason about, and the memory profile that kills the naive
implementation. Suitable when state is small and bounded, for example a form
with twenty fields or a game entity's position and health.

**Immutable state object.** The originator keeps its state in one immutable
value, and the memento holds a reference to it rather than a copy. Capture
becomes a pointer copy and costs nothing. This is the strongest variant
available in any language with cheap immutable structures, and it converts the
pattern's worst force, capture latency, into a non-issue. Persistent data
structures extend the same trick to large states, because two consecutive
versions of a large map share every unchanged subtree.

**Incremental or differential snapshot.** The memento holds only the delta
against the previous memento, and restore walks backwards applying deltas.
Memory drops from N times S to N times the average change size. The cost is
that restoring to an arbitrary point is now linear in the distance rather than
constant, and that a corrupt delta invalidates every snapshot after it. The
standard mitigation is a periodic full snapshot acting as a base, with deltas
between. Apache Flink applies exactly this structure to a distributed job,
distinguishing periodic checkpoints from operator savepoints and warning that
operator identity must be pinned with `uid(String)` so state maps back to the
right operator when the job graph changes
([Apache Flink savepoints documentation](https://nightlies.apache.org/flink/flink-docs-stable/docs/ops/state/savepoints/),
verified 2026-08-02).

**Command-based alternative, which replaces the pattern rather than varying
it.** Instead of storing what the state was, store what was done, together with
enough information to reverse it. Undo becomes an inverse operation rather than
a restore. Memory drops to the size of the operation record, which is usually
constant regardless of document size. The costs are real and should be stated.
Every command must have a correct inverse, which is a per-command proof
obligation rather than a single generic mechanism. Non-invertible operations,
for example a lossy conversion or an operation whose result depends on external
state, need a snapshot anyway. And undo cost now grows with how far back the
user goes, because each step must be replayed. Redis frames the same trade for
persistence, describing the append-only file as a log of "every write operation
received by the server" that can "be replayed again at server startup,
reconstructing the original dataset", against RDB's "point-in-time snapshots of
your dataset at specified intervals"
([Redis persistence documentation](https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/),
verified 2026-08-02).

**Hybrid, which is what production systems actually ship.** Commands for the
common small edits, snapshots for the operations that are expensive or
impossible to invert, and a periodic snapshot to bound replay depth. Redis
documents the combined mode for the same reason, and its multi-part
append-only format since version 7 is literally a base snapshot plus
incremental logs tracked by a manifest. The rule of thumb that follows. Use a
command when the inverse is cheap and provable. Use a memento when it is not.

**Memento plus Command for undo stacks.** This is the standard composition and
deserves its own treatment. The Command object owns the reversal
responsibility, and the memento becomes its private field, captured during
execution and consumed during undo. The caretaker degenerates into the command
stack, which is a structure the application already needs for other reasons.
Java Swing ships this shape directly. `UndoManager` "manages a list of
`UndoableEdits`, providing a way to undo or redo the appropriate edits", edits
arrive through `addEdit` or through an `UndoableEditListener` registration, and
`undo` invokes `undo()` on the edits between the current index and the last
edit the manager counts as a full step
([Java SE 8 API, javax.swing.undo.UndoManager](https://docs.oracle.com/javase/8/docs/api/javax/swing/undo/UndoManager.html),
verified 2026-08-02). Each `UndoableEdit` decides for itself whether it reverses
by inverse operation or by restoring captured state, which is exactly the hybrid
above expressed as a type hierarchy. The composition has three concrete
benefits over Memento alone. A command carries a name, so the user interface
can display "Undo Delete Paragraph" rather than "Undo". Commands can be merged,
so twenty consecutive keystrokes collapse into one undoable edit and the
snapshot count drops by a factor of twenty. And a command can be transmitted
over a network for collaborative editing, whereas an opaque memento cannot,
because the receiving process has a different originator instance.

**Serialization as the memento mechanism.** Rather than a hand-written memento
type, the originator serializes itself and returns the bytes. Python supports
this directly through the pickle protocol, where a class "can further influence
how their instances are pickled by overriding the method `__getstate__()`" and,
"upon unpickling, if the class defines `__setstate__()`, it is called with the
unpickled state"
([Python 3 pickle documentation](https://docs.python.org/3/library/pickle.html),
verified 2026-08-02). The documented example excludes an open file handle from
the captured state and reopens it on restore, which is the non-copyable-handle
problem from dimension 4 solved inside the pattern.

The attraction is that one mechanism handles arbitrary state with no per-field
maintenance. Four costs come with it, and the third is the one that causes
production incidents.

- Encapsulation is lost at the byte level. Anyone holding the payload can parse
  it. The caretaker is no longer prevented from reading, only discouraged.
  Where the memento never leaves the process this is a small loss. Where it is
  written to disk or sent over a wire, it is the whole loss.
- Cost. Serialization is not free and it usually runs on the thread that
  triggered the save. Android's own guidance says saved instance state is
  "limited by storage and speed, because the different APIs serialize data",
  that serialization "happens on the main thread during configuration changes,
  which can cause dropped frames and visual stutter", and directs developers to
  store "only primitive types and simple, small objects such as `String`"
  ([Android Developers, Save UI states with Views](https://developer.android.com/topic/libraries/architecture/views/saving-states-views),
  verified 2026-08-02).
- **Versioning.** A serialized memento written by one version of the class must
  be read by another. The moment mementos outlive a deployment, whether on
  disk, in a session store, in a cache, or in a queue, the memento format is a
  published schema and every schema rule applies. Java makes the failure mode
  explicit. The runtime "associates with each serializable class a version
  number, called a serialVersionUID, which is used during deserialization to
  verify that the sender and receiver of a serialized object have loaded
  classes for that object that are compatible", and "if the receiver has loaded
  a class for the object that has a different serialVersionUID than that of the
  corresponding sender's class, then deserialization will result in an
  `InvalidClassException`"
  ([Java SE 21 API, java.io.Serializable](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/io/Serializable.html),
  verified 2026-08-02). The serialization specification classifies deleting a
  field, changing a primitive field's declared type, and making a field static
  or transient as incompatible changes
  ([Java Object Serialization Specification, Java SE 8 platform, chapter on versioning](https://docs.oracle.com/javase/8/docs/platform/serialization/spec/version.html),
  verified 2026-08-02). The practical consequences. Snapshots must carry an
  explicit version number that the originator writes and reads. Restore must
  handle a version it does not recognise by refusing rather than by guessing.
  Removing a field is a breaking change for every stored snapshot, so the
  migration path is to keep reading the old field and ignore it for at least
  one release. And the default identity computed from class structure must
  never be relied on, because it changes with details the author did not
  intend to change.
- Security. A deserializer that instantiates arbitrary types from attacker
  controlled bytes is a remote code execution primitive, see dimension 17.

**Opaque handle with server-side storage.** The memento returned to the
caretaker is an identifier, and the state lives in a store the originator
controls. Encapsulation becomes total, because the caretaker holds a number.
Memory moves out of the process, which is what makes very long histories
affordable. The cost is a lifecycle problem, since nothing now automatically
collects the state when the handle is dropped, so the store needs explicit
expiry.

**Snapshot at a system boundary rather than an object.** Transaction savepoints
are Memento with the database as originator. PostgreSQL describes a savepoint
as "a special mark inside a transaction that allows all commands that are
executed after it was established to be rolled back, restoring the transaction
state to what it was at the time of the savepoint"
([PostgreSQL SAVEPOINT documentation](https://www.postgresql.org/docs/current/sql-savepoint.html),
verified 2026-08-02). The caretaker is application code holding a name it
cannot interpret. The originator is the engine. The encapsulation is absolute,
because no client can read what a savepoint contains.

## 9. Known production uses

**ASP.NET Web Forms view state, `Control.SaveViewState` and
`Control.LoadViewState`.** A server control overrides `SaveViewState` to return
an object holding its accumulated property values, and the framework persists
that object across the request boundary in a hidden form field, handing it back
to `LoadViewState` on the next postback. The Microsoft documentation states
that the method "saves any server control view-state changes that have occurred
since the time the page was posted back to the server" and that "when you
author a custom server control with a custom view state, the view state can be
managed explicitly with the SaveViewState and LoadViewState methods". The
returned type is `object`, which is the narrow interface taken to its limit,
since the page framework transporting it can do nothing with it but store it.
Microsoft .NET API documentation, `System.Web.UI.Control.SaveViewState`,
https://learn.microsoft.com/en-us/dotnet/api/system.web.ui.control.saveviewstate
verified 2026-08-02.

**Android activity and fragment instance state.** The system asks a UI
controller to write its state into a `Bundle` before the controller may be
destroyed, then hands the same `Bundle` back when it is recreated. The
framework is a pure caretaker. It orders, transports and returns the bundle
without interpreting the application's keys. The documentation describes the
callback as being used "to store data needed to reload the state of a UI
controller (activity or fragment) if the system destroys and later recreates
that controller", and it carries the memory warning that makes this a textbook
case of the pattern's central cost. Android Developers, "Save UI states"
(Views), https://developer.android.com/topic/libraries/architecture/views/saving-states-views
verified 2026-08-02.

**PostgreSQL transaction savepoints.** `SAVEPOINT name` captures the
transaction's state, `ROLLBACK TO SAVEPOINT name` restores it, and `RELEASE
SAVEPOINT` discards it. The application holds only the name. The engine holds
everything else and is the sole reader. PostgreSQL notes one documented
difference from the SQL standard, that a duplicate savepoint name does not
destroy the earlier savepoint, though only the most recent is used on rollback,
which is a caretaker-ordering detail rather than a semantic one. PostgreSQL
documentation, SQL Commands, SAVEPOINT,
https://www.postgresql.org/docs/current/sql-savepoint.html
verified 2026-08-02.

**Apache Flink savepoints and checkpoints.** A savepoint is described as "a
consistent image of the execution state of a streaming job, created via Flink's
checkpointing mechanism", stored as binary files on stable storage plus a
metadata file of relative pointers, and used to "stop-and-resume, fork, or
update your Flink jobs". This is Memento for a distributed system, and the
documentation's insistence on stable operator identifiers is the versioning
problem from dimension 8 stated in operational terms. Apache Flink
documentation, State and Fault Tolerance, Savepoints,
https://nightlies.apache.org/flink/flink-docs-stable/docs/ops/state/savepoints/
verified 2026-08-02.

**Java Swing undo support, `javax.swing.undo.UndoManager`.** The manager keeps
an ordered list of `UndoableEdit` objects and replays their `undo` and `redo`
operations, with edits added directly through `addEdit` or automatically by
registering the manager as an `UndoableEditListener` on a document. This is the
Memento plus Command composition in the standard library of a mainstream
platform, with the manager filling the caretaker role and each edit deciding
privately how it reverses itself. Oracle, Java SE 8 API Specification,
`javax.swing.undo.UndoManager`,
https://docs.oracle.com/javase/8/docs/api/javax/swing/undo/UndoManager.html
verified 2026-08-02.

**Python object serialization hooks, `__getstate__` and `__setstate__`.** The
pickle protocol lets a class decide what its captured state contains and how
that state is turned back into a live object, which is precisely the
originator's two responsibilities. The documented example removes an open file
object before capture and reopens the file at the recorded line number on
restore. Python Software Foundation, Python 3 documentation, `pickle`, section
on `__getstate__` and `__setstate__`,
https://docs.python.org/3/library/pickle.html
verified 2026-08-02.

**Redis RDB snapshots.** The dataset is written to `dump.rdb` as "a very compact
single-file point-in-time representation", produced by forking a child that
writes while the parent keeps serving. The originator is the server, the
caretaker is the operator's backup policy, and no client can read the snapshot
through the Redis protocol. Redis documentation, Redis persistence,
https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/
verified 2026-08-02.

## 10. Consequences

Positive.

- Encapsulation survives. The originator's fields stay private while an
  external party gains the ability to reverse changes to them.
- Restoration is atomic, so multi-field invariants cannot be violated by a
  partial rollback. This is the property that makes the pattern correct rather
  than merely convenient.
- The caretaker is fully generic. One undo stack, checkpoint manager or
  transaction scope serves every originator in the system, because it never
  looks inside what it holds.
- The originator's public interface stays narrow. No accessor is added purely to
  enable copying, which prevents the accessor from being used for other
  purposes later.
- Restore latency is constant and does not vary with history depth, because it
  assigns an already-built state rather than replaying work.
- The originator retains full control over what counts as state, so caches,
  derived values, timers and connection handles can be excluded deliberately
  rather than accidentally included.

Negative.

- Memory cost scales with state size times snapshot count. Without an eviction
  policy this is an unbounded growth path, and the growth is invisible in code
  review because no allocation looks large in isolation.
- Capture cost scales with state size. On a user-interface thread this shows up
  as input latency at exactly the moment the user is typing.
- The originator gains a second responsibility. Capture and restore must stay
  in step with every field added, and nothing enforces that they do.
- Persisted mementos become a schema with compatibility obligations, and the
  obligation is easy to miss because the type looks internal.
- The caretaker cannot tell how expensive its history is, since it cannot
  measure what it cannot read. Budgeting has to be done by the originator or
  by an explicit size reported alongside the memento.
- Debugging is harder. A stack of opaque objects tells an investigator nothing
  without originator cooperation, which is a deliberate trade rather than an
  oversight, but it is still a cost.
- In dynamic languages the central guarantee is not a guarantee, so the design
  documents an intent the runtime does not defend.

## 11. Failure modes and misuse

**The caretaker that reads the memento.** Symptom. A change to a private field
name inside the originator breaks a class that was never supposed to know the
field existed, and the compiler error appears in the undo stack rather than in
the object being edited. Cause. The memento was given public accessors for
convenience, usually so a list view could display something about each history
entry. Fix. Move the display value into the narrow interface as a computed
label produced by the originator at capture time, and remove the accessors.

**Unbounded history growth.** Symptom. Resident memory climbs steadily across a
long editing session and never falls, garbage collection pause times grow, and
a heap dump shows one collection retaining thousands of similar objects. Cause.
An undo stack with no depth limit and no eviction. Fix. Bound the stack by
count and by total bytes, where the byte figure is reported by the originator
because the caretaker cannot compute it, and discard the oldest entries first.
Bounding by count alone fails when snapshot sizes vary by three orders of
magnitude between documents.

**The shallow copy that is not a snapshot.** Symptom. Undo appears to succeed
and changes nothing, or restores some fields but not others, and the failure
depends on which fields the last edit touched. Cause. The memento captured
references to mutable collections rather than copies, so the memento's contents
change along with the live object. Fix. Deep copy at capture, or move the state
to immutable structures so the reference copy is safe by construction. The
second option is preferable because it cannot be forgotten on the next field.

**Off-by-one undo.** Symptom. The first press of undo does nothing visible, and
every subsequent press undoes one action too few, so the user must press undo
once more than they expect to reach any given state. Cause. The snapshot was
taken after applying the change rather than before. Fix. Capture at command
acceptance, before mutation, per the ordering rule in dimension 7.

**The stale redo branch.** Symptom. A user undoes several steps, makes a
different edit, presses redo, and the document jumps to a state that mixes both
timelines and never existed. Cause. The redo stack was not cleared when a new
edit arrived after an undo. Fix. Clear redo on every fresh edit, and add a
regression test that performs undo, edit, redo and asserts redo was rejected.

**The restore that leaves dead handles.** Symptom. After restoring a snapshot,
the object throws on the first operation that touches input or output, with an
error about a closed file, an invalid socket or a disposed context. Cause. The
memento captured a handle that did not survive, or the restore replaced the
whole state including a handle that the live object had since replaced. Fix.
Exclude non-copyable resources from the captured state and rebuild them during
restore, following the pattern the pickle protocol documents for file objects.

**The snapshot that tears under concurrency.** Symptom. A restored state fails
an invariant that the originator enforces on every setter, and it cannot be
reproduced under a debugger. Cause. A mutation ran on another thread partway
through building the memento, so the snapshot recorded field A from before the
change and field B from after. Fix. Capture under the same lock that guards
mutation, or make state immutable so capture is a single reference read.

**Version drift on persisted mementos.** Symptom. After a deployment, restore
fails for sessions that started before the deploy, with a deserialization error
or a field silently arriving as null or zero. Cause. The state shape changed
and old payloads no longer match, which in Java surfaces as
`InvalidClassException` on a `serialVersionUID` mismatch. Fix. Write an explicit
schema version into every memento, refuse unknown versions loudly rather than
best-effort parsing them, keep reading removed fields for at least one release
cycle, and add a test that loads a checked-in payload captured from the
previous version.

**Sensitive data captured by accident.** Symptom. A password, an access token or
a card number appears in a crash report, a session store dump, or a support
export, in a field nobody remembers writing there. Cause. A generic serializer
captured every field including the ones that were only supposed to live in
memory for one request. Fix. Make capture an explicit allowlist rather than a
denylist, mark secret fields transient at the language level, and add a test
that asserts the serialized form contains none of a set of known secret values.

**Memento used where Command was needed.** Symptom. Editing a large document
becomes progressively slower, memory grows in proportion to the number of
keystrokes, and undo latency is fine while typing latency is not. Cause.
Full-state snapshotting on every small edit. Fix. Move to reversible commands
for the small edits and keep snapshots for operations whose inverse is not
available, merging consecutive keystrokes into one undoable edit.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Memento (full snapshot) | Command with inverse | Event Sourcing | Prototype (clone) | Copy-on-write immutable state | Transaction savepoint |
|---|---|---|---|---|---|---|
| Encapsulation of internals | Strong. Only the originator reads | Strong. Command owns its own data | Weak by design. Events are public contracts | Weak. Clone is a fully usable object | Medium. The value type is public | Total. The engine is the only reader |
| Memory per retained step | State size. The largest cost | Operation size. Usually constant | Event size, plus a growing log | State size, same as Memento | Changed nodes only, via sharing | Engine managed, undo log |
| Capture latency | Proportional to state size | Constant, one record appended | Constant, one event appended | Proportional to state size | Constant, a reference copy | Constant, a mark |
| Restore latency | Constant. One assignment | Linear in steps replayed | Linear in events, unless snapshotted | Constant | Constant | Sub-linear, engine tuned |
| Atomic multi-field restore | Strong. That is its purpose | Depends on the inverse being correct | Strong if events are transactional | Strong | Strong | Strong |
| Selective or partial undo | Not supported | Supported per command | Supported by replaying a subset | Not supported | Not supported | Not supported |
| Auditability of history | None. Opaque by design | Good. Named operations | Strong. That is its purpose | None | None | Operator visible only |
| Works for non-invertible operations | Yes. That is its advantage | No. Needs a snapshot fallback | Yes, by replay from a base | Yes | Yes | Yes |
| Cross-process or collaborative use | Poor. Opaque to other processes | Good. Commands are transmittable | Strong. Events are the wire format | Poor | Medium, needs serialization | Not applicable |
| Schema evolution burden | High once persisted | Medium. Command payloads evolve | High. Events are permanent | High once persisted | Medium | None for the application |
| Cognitive load | Medium. Three roles, one access rule | Medium. One inverse proof per command | High. Projections and replay | Low | Low in a language that supports it | Low |

Reading of the table. Memento wins where state is small, encapsulation matters,
restore must be instant, and operations are not reliably invertible. Command
wins where changes are small relative to state and each operation has a
provable inverse. Event sourcing wins where the history itself is a product
requirement rather than a mechanism. Prototype wins only when a live copy is
what was actually wanted. Copy-on-write immutable state wins in any language
that offers persistent structures, and in that setting it is best understood as
the cheapest possible implementation of Memento rather than as a rival.
Savepoints win when the state lives in an engine that already tracks it.

## 13. Related and incompatible patterns

- **Command.** The most productive composition, treated in detail in dimension
  8. Command answers "what to reverse" and Memento answers "how to reverse when
  no inverse exists". A command holding a memento as a private field is the
  standard shape of an undo stack, and `javax.swing.undo` ships it as a public
  interface hierarchy. Reach for Command first and add Memento only for the
  operations Command cannot invert.
- **Prototype.** Frequently confused with it, and the confusion is worth naming.
  Both produce a copy of an object's state. Prototype produces a live, usable
  object intended to be operated on. Memento produces an inert record intended
  only to be handed back. Using a clone as a memento hands the caretaker a
  second working instance, which is the source of some of the hardest aliasing
  bugs in this space.
- **Iterator.** The GoF catalog pairs them because an iterator's position is
  state that a client may want to capture and restore without learning how
  traversal is implemented, which is the same asymmetric-access requirement in
  miniature.
- **State.** Composes cleanly and is often confused by name alone. A State
  object says which behaviour is active now. A Memento records what everything
  was at a past instant. An originator implementing State captures the current
  state object as part of its memento, so restoring puts the behaviour back as
  well as the data.
- **Observer.** Interacts badly if not handled. Restoring a snapshot mutates the
  originator, which fires change notifications, which can cause observers to
  issue further edits and push more snapshots. The fix is to suppress
  notification during restore and fire one composite change afterwards.
- **Builder.** Useful alongside it when the memento is not a simple field copy.
  A builder assembles the captured state, which keeps the memento immutable
  while allowing the capture to happen in stages.
- **Singleton.** Actively conflicts. A memento capturing a reference to
  process-wide mutable state captures nothing, because that state will have
  changed by the time restore runs, and the snapshot restores a stale pointer to
  a live object. Global mutable state and snapshotting cannot both be correct.
- **Event Sourcing.** Largely subsumes the pattern where it applies. When the
  event log is the record of truth, a memento becomes a cached projection used
  to bound replay cost rather than the mechanism of restoration itself. Adopting
  both without deciding which one is authoritative produces two sources of truth
  that disagree after a partial failure.
- **Flyweight.** Conflicts in a specific way that surprises people. Shared
  flyweight objects referenced from a memento are not part of the snapshot, so
  a change to shared internal state seen through a flyweight will appear to
  survive an undo. Confirm that everything reachable from a memento is either
  immutable or copied.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. The starting position
is usually external code reading and writing the originator's fields to fake a
rollback.

1. Find every place that copies the object's state out and writes it back.
   Catalogue which fields each one touches. The union of those fields is the
   candidate state, and the differences between them are almost certainly bugs
   already present.
2. Introduce a state-holding type inside the originator that groups those
   fields. Change the originator to hold one instance of it. Nothing external
   changes yet, so the tests should pass unchanged. This is Extract Class
   applied to the originator's own fields, see the refactoring family entry.
3. Make that state type immutable if the language allows it. Every mutation
   becomes a replacement of the whole state value. This step is optional for
   correctness and is the single highest-return change available, because it
   makes every later step cheaper and removes the tearing and shallow-copy
   failures from dimension 11 by construction.
4. Add `save()` returning a memento wrapping the state, and `restore(memento)`
   assigning it back. Make the memento's accessors visible only to the
   originator, using the mechanism from dimension 5 that the language actually
   provides. Do not settle for a comment saying the field is private if the
   language offers nesting or module privacy.
5. Rewrite one external caller to call `save()` and `restore()` instead of
   touching fields. Run the tests. Repeat per caller rather than all at once,
   so a failure localises.
6. Delete the accessors that existed only to support the external copying. This
   is the step that pays for the work, and skipping it leaves the old path open
   so the next author will use it.
7. Extract the caretaker. Move the storage, ordering and bounding of snapshots
   into a type that holds nothing but mementos. Give it an explicit depth limit
   and an explicit byte budget from the first commit rather than later.
8. Add the encapsulation test from dimension 15, which asserts that the memento
   type exposes no readable state to a non-originator.

Removing the pattern when it stops earning its place. The signals are a
caretaker that never holds more than one snapshot, a memento whose fields are
all public anyway, or a memory profile in which history is the largest
consumer.

1. Confirm which of the three exit conditions applies, because each has a
   different destination. One snapshot means a local variable. Public fields
   mean a value copy. Memory pressure means Command.
2. If the history depth is one, inline the memento into a local variable at the
   call site that needs it and delete the caretaker. This is Inline Class, see
   the refactoring family entry.
3. If the state was already public, replace the memento with the state value
   itself and keep the caretaker. The undo stack still works and three types
   become one.
4. If memory is the driver, do not delete the pattern first. Add commands
   alongside it, migrate operations one at a time from snapshot to inverse, and
   keep the snapshot path for the operations that resist inversion. Measure
   after each migration, since the memory win comes from the high-frequency
   operations and migrating a rare one gains nothing.
5. Once the remaining snapshot-based operations are rare, bound the history to
   those alone and confirm the memory profile is flat over a long session
   before removing anything.
6. Delete the caretaker only after nothing pushes to it. A caretaker that is
   still written to but never read is a leak wearing the pattern's name.

## 15. Testing and verification

Easier because of the pattern.

- Round-trip testing is direct and cheap. Capture, mutate arbitrarily, restore,
  and assert the object is observably identical to its pre-mutation self. This
  single test catches the majority of the failures in dimension 11 and should
  be the first test written.
- The caretaker is testable in complete isolation with a fake memento type,
  because it never inspects what it holds. Undo depth, ordering, redo clearing
  and eviction can all be verified with no originator present at all.
- Snapshot count is directly assertable, so memory policy becomes a unit test
  rather than a production observation.

Harder because of the pattern.

- Verifying that a memento captured everything relevant is not possible from
  outside, because outside code cannot read it. The test has to go through
  restore and compare behaviour, which means the assertion is only as good as
  the originator's public surface.
- A field added to the originator but forgotten in capture produces a test that
  still passes, since nothing enumerates the fields. This is the highest-value
  target for a reflective or property-based test.
- Snapshot corruption is invisible until restore, so the failure surfaces far
  from its cause.

Techniques that apply.

- **Round-trip property test.** Generate a random sequence of operations,
  snapshot at a random point, continue, restore, and assert equivalence against
  a reference model that replays the operations up to the snapshot point. This
  finds forgotten fields, which example-based tests do not, because the
  generator will eventually touch the field the author forgot.
- **Reflective completeness test.** Enumerate the originator's fields by
  reflection and assert that each one is either present in the captured state
  or explicitly listed in a documented exclusion set. When a developer adds a
  field and forgets capture, this test fails at build time. Keep the exclusion
  set in the test rather than in the production class so that adding to it is a
  visible review decision.
- **Encapsulation test.** Assert that the memento type exposes no public
  readable member beyond the narrow interface, by reflection over its public
  members. This is the only automated defence in languages where the compiler
  does not enforce the rule, and it is the reason the pattern remains usable in
  Python and TypeScript despite the caveat in dimension 5.
- **Golden payload test for persisted mementos.** Check a serialized memento
  produced by the previous release into the test resources and assert that the
  current code loads it correctly. Add a new golden file each release and never
  delete the old ones. Without this, the version drift failure is found by
  users rather than by the build.
- **Aliasing test.** Capture a snapshot, mutate every mutable collection
  reachable from the originator, restore, and assert the collections match
  their captured contents. This catches the shallow copy directly rather than
  waiting for it to surface as a partial restore.
- **Concurrency test with deterministic interleaving.** Run capture on one
  thread while mutation runs on another, restore, and assert the originator's
  own invariant checks pass. A torn snapshot fails an invariant even when no
  field is individually wrong.
- **Memory bound test.** Perform a fixed number of operations against a bounded
  caretaker and assert retained snapshot count and total reported bytes stay
  within the configured budget.

## 16. Observability signals

The pattern hides state by design, so nothing about it is visible in production
unless it is deliberately measured. The signals below are the ones that turn an
opaque history into an operable one without breaking the encapsulation rule,
because every one of them is produced by the originator or counted by the
caretaker rather than read from a memento.

What to record.

- A gauge of retained snapshots per caretaker instance, labelled by originator
  type. This is the first place unbounded growth appears, and it appears well
  before memory pressure does.
- A gauge of total retained snapshot bytes, reported by the originator at
  capture time and summed by the caretaker. Count alone is misleading when
  snapshot sizes vary widely between documents or tenants.
- A histogram of capture duration, labelled by originator type. On an
  interactive path this is directly the user-visible cost, and a rising tail
  here is the earliest signal that state has grown past what full snapshotting
  can carry.
- A histogram of snapshot size at capture, which makes the distribution visible
  rather than only the mean. Snapshot size distributions in editing workloads
  are strongly skewed and a mean hides the cases that matter.
- Counters for capture, restore, eviction and rejected restore, labelled by
  reason for the rejection. Version mismatch deserves its own label because it
  is a deployment signal, not a user signal.
- A histogram of restore duration. Under the full-snapshot variant this should
  be flat and small. A rising restore duration means somebody has quietly
  introduced deltas or replay.
- For persisted mementos, a counter of loads by schema version. This is how a
  deployment learns that old payloads are still in circulation and that the
  compatibility shim cannot be removed yet.

A healthy instance on a dashboard. Retained snapshot count sits at or below the
configured depth and oscillates as users edit and the eviction policy trims.
Retained bytes are flat over a long session rather than trending. Capture
duration is well under the surrounding user operation and its tail is stable.
Restore latency is flat. The eviction counter increases steadily, which is
correct and is the sign the bound is doing its job. For persisted mementos, the
load-by-version counter shows the current version accounting for nearly all
loads within a few days of a deployment.

A failing instance. Retained bytes climb monotonically across a session with an
eviction counter at zero, which is the unbounded history from dimension 11 and
is the single most common production failure of this pattern. Or capture
duration develops a long tail on one originator label only, which localises a
state object that has grown past its design. Or the rejected-restore counter
rises with a version-mismatch label immediately after a deployment, which means
old payloads are in circulation and the compatibility path is missing. Or
restore latency starts to correlate with undo depth, which means the
implementation is replaying rather than restoring and somebody's memory change
altered the cost model without anyone updating the expectations. Or snapshot
count stays flat while bytes climb, which is a single originator whose state is
growing rather than a history that is too long, and the fix belongs in the
originator rather than in the caretaker.

## 17. Security and privacy implications

The pattern has genuine security consequences, and they cluster in two places.
Where it is silent, this section says so rather than inventing a concern.

**Captured secrets.** A snapshot takes everything the originator decides is
state. When capture is written by hand, secrets are excluded by an author who
thought about it. When capture is delegated to a generic serializer, secrets are
included by default. Access tokens, session keys, decrypted payloads, card
numbers and personal data that were meant to exist only for the duration of one
request now live in a history structure with a lifetime nobody analysed. The
defences are concrete. Make the captured field set an explicit allowlist rather
than everything-minus-exclusions, because the denylist form fails open when a
field is added. Mark secret fields with the language's own exclusion mechanism
so a generic serializer skips them. And add the secret-leak test from dimension
15 so the guarantee is checked rather than remembered.

**Deserialization of untrusted mementos.** The moment a memento is persisted or
transmitted, its restore path becomes a deserializer, and a deserializer that
instantiates arbitrary types from bytes an attacker can influence is a remote
code execution primitive rather than a parsing bug. The ASP.NET view state case
is instructive precisely because the memento is round-tripped through the
client in a hidden form field, which means the client holds it and can attempt
to modify it. Any memento that leaves the process must be integrity protected
with a keyed message authentication code, must be restored through a restricted
type resolver rather than a general one, and must be rejected rather than
best-effort repaired when it fails validation. A memento that never leaves the
process does not carry this risk, and conflating the two cases leads teams to
either over-engineer in-memory undo or under-engineer persisted state.

**Memory disclosure through retained history.** Snapshots hold data in memory
long after the live object has moved on, which extends the window in which a
core dump, a heap dump, a crash report or a debugger attach exposes it. For a
system handling regulated data this changes the retention analysis, because the
data's true lifetime is now the history depth rather than the request. Where
that matters, zero out sensitive buffers at eviction rather than relying on
garbage collection, and treat the history depth as a retention setting subject
to the same policy as any other store.

**Denial of service through snapshot growth.** An attacker who can drive the
originator's state size and the capture frequency independently can multiply
them. A request path that appends to a collection and snapshots per append
turns a linear input into quadratic memory. Bound both the state size and the
history depth, and reject the operation rather than degrading, because
degrading silently is what turns this into an outage.

**Where the pattern is silent.** In its classical in-process form, with a
hand-written memento that never crosses a trust boundary, the pattern neither
opens nor closes an attack surface. It changes no authorization decision, adds
no parsing, and creates no new communication path. The encapsulation rule it
enforces is a design property rather than a security control, and describing it
as a security boundary would overstate it, because a process that can read the
originator's memory can read the memento regardless of what the compiler
allows.

On privacy, one practical caveat applies to the advice in dimension 16. Labels
on snapshot metrics frequently carry originator type names, and those names can
encode a tenant, a document class or a data-residency tier. Where they do, treat
the label as attributable data under the same retention and access rules as any
other identifier, and prefer a stable opaque identifier over a descriptive class
name in the metric.

## 18. References

1. Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides. *Design Patterns.
   Elements of Reusable Object-Oriented Software*. Addison-Wesley, 1994.
   ISBN 0-201-63361-2. Chapter 5, Behavioral Patterns, section Memento. Source
   of the intent, the Token alias, the three participants, the wide and narrow
   interface distinction, and the pairing with Command and Iterator.
2. Wikipedia contributors. "Memento pattern".
   https://en.wikipedia.org/wiki/Memento_pattern
   Verified 2026-08-02. Used only to confirm the wording of the stated intent
   and the three participant names, not as a source of explanation.
3. Microsoft. *.NET API documentation*, `System.Web.UI.Control.SaveViewState`
   and `System.Web.UI.Control.LoadViewState`.
   https://learn.microsoft.com/en-us/dotnet/api/system.web.ui.control.saveviewstate
   Verified 2026-08-02. Source for the ASP.NET view state production use and the
   quoted description of explicit view state management.
4. Google. *Android Developers documentation*, "Save UI states" (Views).
   https://developer.android.com/topic/libraries/architecture/views/saving-states-views
   Verified 2026-08-02. Source for the Android instance state production use and
   for the quoted warnings on serialization cost, main-thread stutter, and
   restricting captured state to primitives and small objects.
5. The PostgreSQL Global Development Group. *PostgreSQL documentation*, SQL
   Commands, `SAVEPOINT`.
   https://www.postgresql.org/docs/current/sql-savepoint.html
   Verified 2026-08-02. Source for the transaction savepoint production use, the
   quoted definition, and the documented difference from the SQL standard on
   duplicate savepoint names.
6. The Apache Software Foundation. *Apache Flink documentation*, State and Fault
   Tolerance, Savepoints.
   https://nightlies.apache.org/flink/flink-docs-stable/docs/ops/state/savepoints/
   Verified 2026-08-02. Source for the distributed snapshot production use, the
   quoted definition of a savepoint, and the operator identifier requirement
   cited in the incremental snapshot variant.
7. Oracle. *Java SE 8 API Specification*, `javax.swing.undo.UndoManager`.
   https://docs.oracle.com/javase/8/docs/api/javax/swing/undo/UndoManager.html
   Verified 2026-08-02. Source for the Memento plus Command undo stack
   production use and the quoted class description.
8. Python Software Foundation. *Python 3 documentation*, `pickle`, sections on
   `object.__getstate__` and `object.__setstate__`.
   https://docs.python.org/3/library/pickle.html
   Verified 2026-08-02. Source for the serialization mechanism, the quoted hook
   descriptions, and the documented file-handle exclusion example.
9. Oracle. *Java SE 21 API Specification*, `java.io.Serializable`.
   https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/io/Serializable.html
   Verified 2026-08-02. Source for the quoted `serialVersionUID` description and
   the `InvalidClassException` behaviour on mismatch, cited in the versioning
   discussion.
10. Oracle. *Java Object Serialization Specification*, Java SE 8 platform, chapter on
    versioning of serializable objects.
    https://docs.oracle.com/javase/8/docs/platform/serialization/spec/version.html
    Verified 2026-08-02. Source for the stream unique identifier description and
    the list of incompatible changes cited in the versioning discussion.
11. Redis Ltd. *Redis documentation*, Redis persistence.
    https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/
    Verified 2026-08-02. Source for the RDB snapshot production use and for the
    quoted snapshot against append-only-log trade used in the memory cost and
    command-based alternative discussion.

## Code examples

Four languages chosen for what each shows about the encapsulation rule. Java
shows full compiler enforcement through a private nested class exposed by a
marker interface. C# shows the same enforcement with an explicit narrow
interface carrying display metadata, which is the form most production undo
stacks need. TypeScript shows the closure form, which is the only shape that
enforces the rule in a language where the `private` keyword is erased at
compile time. Python shows the convention form and states its limits honestly,
plus the serialization variant with an explicit schema version. Go and Rust are
omitted from the code because their forms take the same shape as the C# example
with module or package privacy substituted for nesting, and repeating one shape
adds length without adding information.

Each example was run where a toolchain was available, and the two that were not
run are named here rather than implied to have passed. Both Python blocks were
executed with `python3`, including a pickle round trip of the serialization
variant. The TypeScript example was type-checked under `--strict` with
TypeScript 5 and executed with `node`. Type-checking it caught a real defect
worth keeping in view, since a class named `History` collides with the DOM
global of the same name in a non-module script, which is why the example uses
`SnapshotHistory`. The Java and C# examples were not executed, because neither
a JDK nor a .NET SDK was present in the authoring environment. Both are written
against the standard library only, and their enforcement claim rests on the
nested-private-class access rule rather than on a run.

### Java

Full enforcement. `Snapshot` is private to `TextBuffer`, so no other class can
read its fields, while `Memento` is a public marker carrying only a label.

```java
import java.util.ArrayDeque;
import java.util.Deque;

public final class MementoDemo {

    public interface Memento {
        String label();
    }

    static final class TextBuffer {
        private StringBuilder text = new StringBuilder();
        private int cursor = 0;

        // Private nested type. Only TextBuffer can read these fields.
        private static final class Snapshot implements Memento {
            private final String text;
            private final int cursor;
            private final String label;

            private Snapshot(String text, int cursor, String label) {
                this.text = text;
                this.cursor = cursor;
                this.label = label;
            }

            public String label() {
                return label;
            }
        }

        Memento save(String label) {
            return new Snapshot(text.toString(), cursor, label);
        }

        void restore(Memento m) {
            if (!(m instanceof Snapshot s)) {
                throw new IllegalArgumentException("foreign memento");
            }
            this.text = new StringBuilder(s.text);
            this.cursor = s.cursor;
        }

        void insert(String s) {
            text.insert(cursor, s);
            cursor += s.length();
        }

        @Override
        public String toString() {
            return text + " @" + cursor;
        }
    }

    static final class History {
        private final Deque<Memento> stack = new ArrayDeque<>();
        private final int depth;

        History(int depth) {
            this.depth = depth;
        }

        void push(Memento m) {
            if (stack.size() == depth) {
                stack.removeLast();
            }
            stack.push(m);
        }

        Memento pop() {
            return stack.pop();
        }
    }

    public static void main(String[] args) {
        TextBuffer buffer = new TextBuffer();
        History history = new History(16);

        history.push(buffer.save("before hello"));
        buffer.insert("hello");
        history.push(buffer.save("before world"));
        buffer.insert(" world");

        System.out.println(buffer);
        Memento m = history.pop();
        System.out.println("undoing: " + m.label());
        buffer.restore(m);
        System.out.println(buffer);
    }
}
```

### C#

The same enforcement, with the narrow interface carrying the metadata a history
list needs to render itself without reading state.

```csharp
using System;
using System.Collections.Generic;

public interface IMemento
{
    string Label { get; }
    DateTimeOffset TakenAt { get; }
    int ApproximateBytes { get; }
}

public sealed class Sketch
{
    private List<string> shapes = new List<string>();
    private string tool = "select";

    private sealed class Snapshot : IMemento
    {
        internal readonly string[] Shapes;
        internal readonly string Tool;

        public string Label { get; }
        public DateTimeOffset TakenAt { get; }
        public int ApproximateBytes { get; }

        internal Snapshot(string[] shapes, string tool, string label)
        {
            Shapes = shapes;
            Tool = tool;
            Label = label;
            TakenAt = DateTimeOffset.UtcNow;
            ApproximateBytes = tool.Length * 2;
            foreach (var s in shapes) ApproximateBytes += s.Length * 2;
        }
    }

    public IMemento Save(string label) =>
        new Snapshot(shapes.ToArray(), tool, label);

    public void Restore(IMemento memento)
    {
        if (memento is not Snapshot s)
            throw new ArgumentException("foreign memento", nameof(memento));
        shapes = new List<string>(s.Shapes);
        tool = s.Tool;
    }

    public void Draw(string shape) => shapes.Add(shape);
    public void SelectTool(string t) => tool = t;
    public override string ToString() => $"[{string.Join(",", shapes)}] tool={tool}";
}

public sealed class UndoStack
{
    private readonly List<IMemento> entries = new List<IMemento>();
    private readonly int maxBytes;
    private int bytes;

    public UndoStack(int maxBytes) => this.maxBytes = maxBytes;

    public void Push(IMemento m)
    {
        entries.Add(m);
        bytes += m.ApproximateBytes;
        while (bytes > maxBytes && entries.Count > 1)
        {
            bytes -= entries[0].ApproximateBytes;
            entries.RemoveAt(0);
        }
    }

    public IMemento Pop()
    {
        var last = entries[^1];
        entries.RemoveAt(entries.Count - 1);
        bytes -= last.ApproximateBytes;
        return last;
    }
}

public static class Program
{
    public static void Main()
    {
        var sketch = new Sketch();
        var undo = new UndoStack(4096);

        undo.Push(sketch.Save("empty"));
        sketch.Draw("circle");
        undo.Push(sketch.Save("one shape"));
        sketch.Draw("square");
        sketch.SelectTool("brush");

        Console.WriteLine(sketch);
        var m = undo.Pop();
        Console.WriteLine($"undoing to: {m.Label}");
        sketch.Restore(m);
        Console.WriteLine(sketch);
    }
}
```

### TypeScript

The `private` keyword is erased at compile time and gives no runtime protection,
so the closure form is used. The memento is a restore function that holds the
captured state in its closure, which no caller can reach by any means.

```typescript
interface Memento {
  readonly label: string;
  readonly takenAt: number;
}

interface RestorableMemento extends Memento {
  readonly apply: () => void;
}

class Counter {
  #value = 0;
  #step = 1;

  save(label: string): Memento {
    const value = this.#value;
    const step = this.#step;
    const restore = () => {
      this.#value = value;
      this.#step = step;
    };
    const m: RestorableMemento = { label, takenAt: Date.now(), apply: restore };
    return m;
  }

  restore(m: Memento): void {
    const candidate = m as RestorableMemento;
    if (typeof candidate.apply !== "function") {
      throw new Error("foreign memento");
    }
    candidate.apply();
  }

  bump(): void {
    this.#value += this.#step;
  }

  setStep(s: number): void {
    this.#step = s;
  }

  toString(): string {
    return `value=${this.#value} step=${this.#step}`;
  }
}

class SnapshotHistory {
  private readonly entries: Memento[] = [];
  constructor(private readonly depth: number) {}

  push(m: Memento): void {
    this.entries.push(m);
    if (this.entries.length > this.depth) this.entries.shift();
  }

  pop(): Memento | undefined {
    return this.entries.pop();
  }
}

const counter = new Counter();
const undoHistory = new SnapshotHistory(8);

undoHistory.push(counter.save("start"));
counter.bump();
undoHistory.push(counter.save("after one bump"));
counter.setStep(10);
counter.bump();

console.log(counter.toString());
const previous = undoHistory.pop();
if (previous) {
  console.log(`undoing: ${previous.label}`);
  counter.restore(previous);
}
console.log(counter.toString());
```

### Python

Python cannot enforce the access rule, so the example states that plainly and
adds the two defences that remain available. An explicit allowlist of captured
fields, and a schema version that restore refuses to guess at.

```python
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Memento:
    label: str
    version: int
    _state: dict[str, Any]


class Session:
    SCHEMA = 2
    CAPTURED = ("user", "cart", "currency")
    SECRET = ("auth_token",)

    def __init__(self, user: str) -> None:
        self.user = user
        self.cart: list[str] = []
        self.currency = "EUR"
        self.auth_token = "never-captured"

    def save(self, label: str) -> Memento:
        state = {name: getattr(self, name) for name in self.CAPTURED}
        state["cart"] = list(state["cart"])
        return Memento(label=label, version=self.SCHEMA, _state=state)

    def restore(self, memento: Memento) -> None:
        if memento.version != self.SCHEMA:
            raise ValueError(f"unsupported memento version {memento.version}")
        for name in self.CAPTURED:
            setattr(self, name, memento._state[name])
        self.cart = list(self.cart)

    def add(self, item: str) -> None:
        self.cart.append(item)

    def __repr__(self) -> str:
        return f"Session(user={self.user!r}, cart={self.cart}, currency={self.currency!r})"


class History:
    def __init__(self, depth: int) -> None:
        self._depth = depth
        self._entries: list[Memento] = []

    def push(self, memento: Memento) -> None:
        self._entries.append(memento)
        del self._entries[: max(0, len(self._entries) - self._depth)]

    def pop(self) -> Memento:
        return self._entries.pop()


if __name__ == "__main__":
    session = Session("mirza")
    history = History(depth=8)

    history.push(session.save("empty cart"))
    session.add("keyboard")
    history.push(session.save("one item"))
    session.add("monitor")
    session.currency = "USD"

    print(session)
    previous = history.pop()
    print("undoing:", previous.label)
    session.restore(previous)
    print(session)
    assert "auth_token" not in previous._state
```

The serialization variant, using the pickle hooks documented by CPython. This
deliberately drops a non-copyable handle and rebuilds it on restore, and writes
the version into the captured state so a future release can refuse or migrate
an old payload rather than misreading it.

```python
class Connection:
    VERSION = 1

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn
        self.retries = 0
        self.socket = object()

    def __getstate__(self) -> dict[str, Any]:
        state = self.__dict__.copy()
        del state["socket"]
        state["__version__"] = self.VERSION
        return state

    def __setstate__(self, state: dict[str, Any]) -> None:
        version = state.pop("__version__", 0)
        if version != self.VERSION:
            raise ValueError(f"cannot restore version {version}")
        self.__dict__.update(state)
        self.socket = object()
```
