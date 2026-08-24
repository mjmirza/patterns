---
name: Immutability
slug: immutability
family: 16-functional
category: Data and State
aliases: [Immutable Data, Persistent Data, Value-Oriented State]
first_described: "McCarthy 1960, Lisp symbolic expressions"
maturity: canonical
related: [persistent-data-structures, pure-functions, value-object, event-sourcing, memoization]
incompatible_with: [shared-mutable-state, active-record]
verified: 2026-08-02
---

# Immutability

## 1. Name, aliases, and lineage

The canonical name is Immutability. In software design it means that a value
does not change after it is made. Later work creates another value rather than
editing the old one. The same idea appears under several names, each with a
slightly different emphasis.

- **Immutable data.** The broad name used by language manuals and application
  frameworks. Oracle's Java SE 21 documentation says `String` instances cannot
  change after creation and may be shared because of that property
  (https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/String.html,
  verified 2026-08-02).
- **Persistent data.** The name used for immutable collections whose update
  operations keep prior versions available while sharing unchanged structure.
  Clojure documents its collections as immutable and persistent, with modified
  versions created through structural sharing
  (https://clojure.org/reference/data_structures, verified 2026-08-02).
- **Value-oriented state.** The application design name. A state transition
  yields a new value and leaves the previous state available for comparison,
  replay, undo, audit, or retry. React's documentation tells authors to treat
  objects stored in state as read-only and to replace them rather than mutate
  them (https://react.dev/learn/updating-objects-in-state, verified
  2026-08-02).
- **Copy on write.** A lower level implementation technique. A write path copies
  only the representation it is about to change and then returns a new owner or
  handle. Copy on write can implement immutability, but it can also hide mutable
  sharing behind an API, so it is not the same pattern.

Lineage is older than the phrase "design pattern." John McCarthy's 1960 Lisp
paper is the usual historical anchor for symbolic list processing, recursive
functions, and symbolic expression data. The author-hosted Stanford copy says
the paper appeared in *Communications of the ACM* in April 1960 and was the
original paper on Lisp (https://www-formal.stanford.edu/jmc/recursive.html,
verified 2026-08-02). Christopher Okasaki later gave the modern algorithmic
treatment of persistent collections in *Purely Functional Data Structures*,
Cambridge University Press, 1998, chapters 2 through 5. Cambridge University
Press lists the book contents, including chapter 2, "Persistence"
(https://www.cambridge.org/core/books/abs/purely-functional-data-structures/contents/9DA321DB54345B01758FE0107B9824E2,
verified 2026-08-02). This entry uses Okasaki for the book source and the
Clojure documentation for a production language source rather than quoting
algorithm details from either.

The name is sometimes contested in dynamic languages because an object can be
called immutable while it still contains a reference to mutable data. Python's
dataclass documentation is explicit that `frozen=True` emulates read-only
instances and that true immutability is not available for all Python objects
(https://docs.python.org/3/library/dataclasses.html, verified 2026-08-02).
This entry treats immutability as a contract at an ownership boundary, not as a
magical bit attached to every reachable byte.

## 2. Problem and context

A program needs to share data across time, calls, threads, retries, or users,
but ordinary in-place mutation makes it unclear which version a reader sees.
The defect usually appears after the code has grown past one function.

A service receives a request and loads a customer record. Validation reads the
record. Pricing annotates it. Authorization reads it again. A cache keeps a
pointer to it for the next request. A later function mutates one nested field.
The mutation may be harmless in the local function, yet it can alter what the
cache, logger, retry code, validator, or caller believes it already observed.
Nothing in the type of a normal object records "this is version 3." The
reference is the same reference. The mental model becomes time-dependent.

Immutability changes the rule. A value is a fact. A transition from one fact to
the next is expressed as a function, constructor, copy operation, builder, or
persistent collection update. Old readers keep old facts. New readers receive
new facts. The cost is paid when creating the next value and in the discipline
of making updates explicit.

The context that makes the pattern earn its place has at least one of these
properties.

- The same data crosses threads, tasks, callbacks, or async boundaries.
- Prior versions matter for undo, audit, comparison, caching, event replay, or
  optimistic concurrency.
- Equality, hashing, memoization, or change detection must be dependable.
- Business logic should read like transformations from input values to output
  values.
- A framework depends on reference changes to detect state changes, as React
  does when state is replaced with a new object
  (https://react.dev/learn/updating-objects-in-state, verified 2026-08-02).

Outside that context, in-place mutation can be clearer and cheaper. The pattern
is not a moral preference for copying. It is a design response to aliasing and
time.

## 3. Forces

Engineering judgement. The forces below are the pressures this pattern usually
balances. The cited references prove named systems and APIs, while the weighing
of pressures is design judgement.

- **Consistency.** Favoured. A reader that holds an immutable value cannot see
  it drift while work is in progress. This is the main payoff.
- **Coupling.** Favoured at boundaries. Callers no longer need to know whether
  callees retain references, because the value cannot be edited by the callee.
- **Latency.** Sacrificed on write paths. Every transition allocates a new
  wrapper, object, path, or tree node. Persistent structures reduce the cost
  through sharing, but they do not make updates free. Clojure documents vectors
  and maps with logarithmic access over wide trees
  (https://clojure.org/reference/data_structures, verified 2026-08-02).
- **Memory.** Mixed. Naive copying multiplies storage. Structural sharing keeps
  unchanged parts once, as documented by Immutable.js for its JavaScript
  collections (https://immutable-js.com/, verified 2026-08-02). Retaining many
  versions still consumes memory.
- **Operability.** Favoured. Old and new values can be compared, logged, hashed,
  replayed, and tested. Git's object database is content-addressed, which makes
  stored object identity derive from content rather than from a mutable row id
  (https://git-scm.com/book/en/v2/Git-Internals-Git-Objects, verified
  2026-08-02).
- **Cost.** Mixed. Development cost falls for reasoning about readers and tests,
  but rises for modeling, constructors, update helpers, and allocation control.
- **Team topology.** Favoured across module boundaries. A platform team can
  publish value types without exposing mutation hooks that product teams must
  coordinate around.
- **Cognitive load.** Mixed. Local reasoning improves because values are stable.
  Update code can become noisier, especially for deeply nested records. Redux
  documents the need to copy every level of nested state when writing immutable
  updates by hand (https://redux.js.org/usage/structuring-reducers/immutable-update-patterns,
  verified 2026-08-02).

The pattern favours readers, concurrency, replay, equality, and change
detection. It sacrifices cheap local writes, some object identity shortcuts, and
the habit of "patching the thing I already have."

## 4. Applicability and non-applicability

Reach for Immutability when the following hold.

- **Shared read paths outnumber writes.** Configuration, routing tables,
  product catalogs, permissions snapshots, feature flag snapshots, and compiled
  query plans are common fits. Many readers can use the same value without
  locking.
- **A version must mean something.** If an order, invoice, policy, AST, syntax
  tree, query plan, commit, or state snapshot might be compared with an earlier
  version, make each version a value.
- **The value will be hashed or used as a key.** Mutable keys corrupt hashed
  collections when fields that contribute to equality change after insertion.
  Python dataclasses tie generated hash behavior to the `eq` and `frozen`
  settings because hashability implies an immutability promise
  (https://docs.python.org/3/library/dataclasses.html, verified 2026-08-02).
- **A framework depends on replacement.** React state and Redux reducers are
  designed around replacing state values rather than mutating prior values
  (https://react.dev/learn/updating-objects-in-state and
  https://redux.js.org/usage/structuring-reducers/immutable-update-patterns,
  verified 2026-08-02).
- **You need snapshots for optimistic concurrency.** A compare step can ask
  whether the value it read is still current. If it is not, the next value can
  be recalculated from a fresh snapshot.
- **You need undo, redo, audit, or time travel.** Keeping prior values is the
  natural representation. Redux names undo history as one of its reducer
  patterns in the same documentation set as immutable updates
  (https://redux.js.org/usage/structuring-reducers/immutable-update-patterns,
  verified 2026-08-02).
- **The object is a domain value.** Money, coordinates, dates, identifiers,
  postal addresses, dimensions, permissions, and commands usually read better
  as values than as mutable entities.

Do NOT reach for Immutability in these cases.

- **A tight numeric kernel mutates a local buffer.** Matrix multiplication,
  audio processing, compression, parsing hot loops, and graphics code often
  need carefully controlled mutation inside one owner. Use a mutable local
  representation and publish an immutable result at the boundary.
- **The object models a long-lived identity whose fields change independently.**
  A live socket, actor mailbox, UI input control, database connection, file
  handle, or process has identity and lifecycle. Wrap its public state in
  snapshots, but do not pretend the handle itself is immutable.
- **Only a shallow shell is frozen.** Freezing a record that contains a mutable
  list does not make the list safe. Python documents `frozen=True` as an
  emulation of immutability rather than a guarantee for all reachable objects
  (https://docs.python.org/3/library/dataclasses.html, verified 2026-08-02).
- **The state is huge and every update touches most of it.** A full copy on each
  transition will dominate runtime. Use a mutable work buffer, chunking,
  persistent structures, or append-only deltas.
- **The team lacks update helpers for nested data.** Manual copying of deep
  trees is error-prone. Redux calls out repeated copying of every nested level
  as difficult and mistake-prone (https://redux.js.org/usage/structuring-reducers/immutable-update-patterns,
  verified 2026-08-02).
- **External APIs require mutation.** Some serializers, ORMs, UI toolkits, and
  native bindings populate objects by setting fields. Keep a mutable adapter at
  the edge and translate to values inside.
- **Object identity carries the domain meaning.** If two objects with equal
  fields must still be distinct entities, value equality may hide a domain
  distinction. Use entity references plus immutable snapshots of their state.
- **Mutation is confined and proved local.** A private builder or accumulator
  used inside one function can be the right implementation. The boundary should
  still return a value.

## 5. Structure

Five participants appear in a sound immutable design.

- **Value.** The stable data object, collection, or snapshot. It exposes readers
  and value equality. It does not expose mutators that alter its observable
  state after creation.
- **Transition.** The function, method, reducer, builder `build`, or persistent
  collection operation that accepts an old value plus a change and returns the
  new value.
- **Change.** The input to a transition. It can be a command, event, patch,
  field value, callback, or operation name. It is often immutable as well.
- **Owner.** The component, store, atom, actor, database row, or reference that
  decides which value is current. Immutability does not remove state. It moves
  mutation from the value into the owner reference.
- **Observer.** Code that reads values, compares versions, renders UI, computes
  cache keys, or emits telemetry. Observers may hold an old value without fear
  that it will drift.

The relationship is subtle. The value is immutable, but the binding to the
current value can be mutable. A React component replaces a state object through
its setter. A Redux store replaces the current state with a reducer result. Git
references can move while the objects they point at remain content-addressed
objects. The owner is the place where time is represented. The value is the
place where facts are represented.

Persistent collections add two internal participants.

- **Path node.** A tree node, list cell, chunk, or trie node that can be shared
  by more than one version.
- **Root pointer.** A small value pointing at the root of a version. Updating a
  nested value usually creates a new root plus the nodes along the changed path,
  while unchanged branches are shared.

## 6. ASCII structure diagram

```
                 reads
        +==================+
        |     Observer     |
        +==================+
                  |
                  v
        +==================+       current points to
        |      Owner       |==============================+
        |==================|                              |
        | current: Value   |                              v
        +==================+                    +================+
                  ^                             |     Value V1   |
                  | replaces                    |================|
                  |                             | fields, nodes  |
                  |                             +================+
                  |                                      |
                  |                                      | shares
                  |                                      v
        +==================+       returns       +================+
        |    Transition    |===================>|     Value V2   |
        |==================|                    |================|
        | old + change     |<===================| changed path   |
        +==================+       consumes      +================+
                  ^
                  |
        +==================+
        |      Change      |
        +==================+

The values do not change. The owner changes which value is current.
```

## 7. Dynamics

The runtime flow separates observation from transition. Readers see a complete
value. Writers compute a replacement. Publication swaps the current reference,
stores the new root, sends the new value, or appends a new object.

```
Client        Owner/Store        Transition        Old Value        New Value
  |               |                  |                 |                |
  |=> read() ====>|                  |                 |                |
  |<== V1 ========|                  |                 |                |
  |               |                  |                 |                |
  |-- change C -->|                  |                 |                |
  |               |-- apply(V1,C) -->|                 |                |
  |               |                  |-- read fields -->|                |
  |               |                  |<== stable V1 ====|                |
  |               |                  |=> allocate changed path ========>|
  |               |                  |<== V2 ===========================|
  |               |=> publish V2 ======================================>|
  |<== ack V2 ====|                  |                 |                |
  |               |                  |                 |                |
  |=> old V1 still valid ===========>|                 |                |
```

For a persistent tree the middle of the flow is more specific.

```
Before update of key K:

  root A
    |
    +-- node B -- unchanged branch
    |
    +-- node C -- path to K
          |
          +-- leaf old

After update:

  root A                         root A'
    |                              |
    +== node B  <==================+   shared
    |
    +-- node C                     +-- node C'
          |                              |
          +-- leaf old                   +-- leaf new

Only the root and nodes on the path to K are new.
```

The old and new versions can coexist. That is the core runtime behavior. The
system may later collect old versions when no observer, cache, audit trail, or
reference can reach them.

## 8. Implementation variants

**Primitive immutability.** Many languages have primitives or library types
whose values do not change. Java `String` is a named example in the Java SE API
documentation (https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/String.html,
verified 2026-08-02). This variant is low ceremony and good for leaf values.

**Shallow immutable records.** A class or struct exposes read-only fields and
returns a new instance from `with` methods or copy functions. TypeScript
`readonly` prevents writes during type checking but does not alter runtime
behavior (https://www.typescriptlang.org/docs/handbook/2/objects.html,
verified 2026-08-02). Python `@dataclass(frozen=True)` raises
`FrozenInstanceError` when generated assignment hooks are invoked
(https://docs.python.org/3/library/dataclasses.html, verified 2026-08-02).
This variant fits small domain values.

**Deep immutable value graph.** Every reachable object is immutable or is
treated as private. This is the correct contract for hash keys, cache entries,
messages, and security-sensitive policy snapshots. It costs more modeling work
because one mutable child can violate the whole promise.

**Persistent collections.** Lists, maps, sets, and vectors return new versions
that share unchanged structure. Clojure documents collections as immutable,
persistent, structurally shared, and inherently thread-safe
(https://clojure.org/reference/data_structures, verified 2026-08-02).
Immutable.js documents JavaScript collections where new versions reuse
unchanged parts (https://immutable-js.com/, verified 2026-08-02). This variant
fits large state where most updates touch a small path.

**Reducer style.** A function accepts state and an action, then returns the next
state. Redux teaches this style and its immutable update rules
(https://redux.js.org/usage/structuring-reducers/immutable-update-patterns,
verified 2026-08-02). The benefit is testable transition logic. The cost is
verbose nested copying unless the state shape is flat or helper libraries are
used.

**Draft mutation over immutable output.** Immer's `produce` accepts a base state
and a recipe that mutates a draft, then returns a next state while leaving the
base state untouched (https://immerjs.github.io/immer/produce/, verified
2026-08-02). This variant preserves the local syntax of mutation while
publishing immutable results. The risk is that readers may copy the recipe into
plain reducer code where it becomes real mutation.

**Builder then freeze.** A mutable builder accumulates fields, validates them,
and returns an immutable value. This fits objects with many optional fields or
normalization work. The builder must not escape while partially filled.

**Append-only log.** Instead of replacing a current value directly, the system
records immutable events or objects and derives current state. Git stores
content in an object database keyed by checksums of content plus headers, and
keeps multiple versions as separate objects
(https://git-scm.com/book/en/v2/Git-Internals-Git-Objects, verified
2026-08-02). Event Sourcing is the architectural variant of this idea.

**Copy on write owner.** A shared representation is copied only when a writer
appears. This can reduce copies for read-heavy values, but it requires careful
ownership checks. The public API must still make the old value behave as stable.

## 9. Known production uses

**Java platform, `java.lang.String`.** The Java SE 21 API specifies `String` as
the class used for string literals, says strings cannot change after creation,
and says they may be shared because they are immutable
(https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/String.html,
verified 2026-08-02). This is a production use in one of the most widely
deployed runtime libraries.

**Clojure core collections.** Clojure's reference documentation states that its
data structures are immutable, support persistent manipulation, and that its
collections create modified versions through structural sharing
(https://clojure.org/reference/data_structures, verified 2026-08-02). This is a
production language design where immutable persistent collections are the
default application data model.

**React state.** React's learning documentation tells authors to treat objects
stored in state as read-only and to replace state objects so React knows to
render again (https://react.dev/learn/updating-objects-in-state, verified
2026-08-02). This is a production UI framework use where immutability is part of
the state update contract.

**Redux reducers and Redux Toolkit.** Redux documents immutable update patterns
for reducers and notes that Redux Toolkit uses Immer internally so reducer code
can appear to mutate a draft while updates are applied immutably
(https://redux.js.org/usage/structuring-reducers/immutable-update-patterns,
verified 2026-08-02). This is a production application state pattern used by
Redux applications.

**Git object database.** Pro Git describes Git as a content-addressable
filesystem that writes content to an object database and returns a key derived
from the content. The same chapter demonstrates storing two versions of a file
as separate blob objects
(https://git-scm.com/book/en/v2/Git-Internals-Git-Objects, verified
2026-08-02). This is a production source control use where old content remains
available under its content identity.

## 10. Consequences

Engineering judgement. Consequences depend on object size, update rate, runtime,
and team discipline.

Positive.

- Readers get stable values. A function can inspect a value without defending
  against another function changing it during the read.
- Equality, hashing, memoization, and cache keys become safer because the
  compared fields do not drift after insertion or memoization.
- Concurrency can avoid many locks. Immutable values can be shared freely while
  owners coordinate replacement of current references.
- Tests become smaller. A transition can be tested by asserting old value, input
  change, and new value.
- Undo, redo, audit, replay, and diffing use ordinary values rather than custom
  inverse operations.
- Observability improves because old and new values can be compared at the
  boundary where a transition occurs.
- APIs communicate ownership. A caller that receives a value knows it may keep
  it.

Negative.

- Write paths allocate. Naive copies allocate too much, and persistent
  structures still allocate the changed path.
- Deep updates can become verbose. Redux documents this pain for nested state
  (https://redux.js.org/usage/structuring-reducers/immutable-update-patterns,
  verified 2026-08-02).
- Retained versions can hold memory. Undo stacks, caches, snapshots, and traces
  need retention limits.
- Shallow immutability can mislead. A frozen outer record with a mutable child
  is not safe as a deep value.
- Object identity loses meaning. Two values with equal fields may be
  interchangeable even when an entity model wanted separate identity.
- Interop with mutable frameworks needs adapters, copies, or builders.
- Debuggers can show many similar objects, which can confuse incident review
  unless versions are labelled.

## 11. Failure modes and misuse

Engineering judgement. The triples below are failure patterns seen in code
review and production debugging. Observable symptoms are included because the
mistake is often invisible in source until state crosses a boundary.

**Symptom.** A UI component does not re-render after a field assignment, but it
does re-render after a state setter receives a copied object.
**Cause.** State was mutated in place, so the framework did not receive a new
state value. React documents this failure mode with object state and a pointer
movement example (https://react.dev/learn/updating-objects-in-state, verified
2026-08-02).
**Fix.** Replace the state value through the framework setter, or use a reducer
or Immer draft that returns a new value.

**Symptom.** A Redux selector returns stale data or undo history corrupts
itself after a reducer runs.
**Cause.** A nested object was copied at the top level but a lower nested object
was edited through an alias. Redux warns that each nested level must be copied
and that new variables can still point at the same object
(https://redux.js.org/usage/structuring-reducers/immutable-update-patterns,
verified 2026-08-02).
**Fix.** Copy every changed path level, flatten state, split reducers, or use
Redux Toolkit with Immer.

**Symptom.** A map or set cannot find a key that was inserted earlier, or a
cache contains duplicate-looking keys.
**Cause.** A field that contributes to equality or hash was changed after the
object became a key.
**Fix.** Make key objects deeply immutable, store a stable identifier as the
key, or remove and reinsert after mutation if a mutable key cannot be avoided.

**Symptom.** Memory rises during normal use even though each state object seems
small.
**Cause.** Old immutable versions are retained by undo stacks, subscriptions,
memoization tables, traces, closures, or caches.
**Fix.** Add retention windows, weak references where the language permits, and
metrics for live snapshot count and retained bytes.

**Symptom.** A "frozen" object changes when a nested array is edited.
**Cause.** Only the outer object was frozen or generated as read-only. Python
documents frozen dataclasses as an emulation and TypeScript documents
`readonly` as a type-checking rule with no runtime behavior
(https://docs.python.org/3/library/dataclasses.html and
https://www.typescriptlang.org/docs/handbook/2/objects.html, verified
2026-08-02).
**Fix.** Convert mutable children to immutable values, clone on input, expose
read-only views, or enforce deep freezing in tests for the boundary.

**Symptom.** Latency spikes on a request that updates a large state object.
**Cause.** The implementation copies the full graph on each transition instead
of copying only the changed path or using a work buffer.
**Fix.** Flatten the state, use persistent collections, batch updates, or mutate
a private builder and publish one immutable result.

**Symptom.** A team avoids adding fields because each update needs long spread
expressions or copy constructors.
**Cause.** The value shape is deeper than the update tools can handle.
**Fix.** Add named `with` methods, lenses, generated copy helpers, reducers per
subtree, or an Immer-style draft boundary.

**Symptom.** Security review finds a policy snapshot that can be edited by a
caller after validation.
**Cause.** The service stores caller-owned mutable objects rather than copying
or converting them to immutable internal values.
**Fix.** Defensively copy at trust boundaries and publish read-only internal
types.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

<table>
<thead>
<tr>
<th>Force</th>
<th>Immutability</th>
<th>Shared Mutable State</th>
<th>Builder</th>
<th>Copy on Write</th>
<th>Event Sourcing</th>
<th>Actor Model</th>
</tr>
</thead>
<tbody>
<tr>
<td>Consistency for readers</td>
<td>Strong. Values do not drift</td>
<td>Weak without locks</td>
<td>Strong after build</td>
<td>Strong if ownership is correct</td>
<td>Strong for recorded facts</td>
<td>Strong per actor mailbox</td>
</tr>
<tr>
<td>Write latency</td>
<td>Medium to poor</td>
<td>Strong for local writes</td>
<td>Strong during build</td>
<td>Medium, first write copies</td>
<td>Medium, append plus projection</td>
<td>Medium, message hop</td>
</tr>
<tr>
<td>Memory use</td>
<td>Medium, depends on retention</td>
<td>Low for one version</td>
<td>Low after build</td>
<td>Good for read-heavy data</td>
<td>High if log retention is long</td>
<td>Medium</td>
</tr>
<tr>
<td>Coupling at boundaries</td>
<td>Low</td>
<td>High, callers share aliases</td>
<td>Low after publish</td>
<td>Medium, hidden sharing</td>
<td>Low for facts, high for projections</td>
<td>Low between actors</td>
</tr>
<tr>
<td>Change detection</td>
<td>Strong by reference or value</td>
<td>Weak, needs dirty flags</td>
<td>Strong after publish</td>
<td>Strong after publish</td>
<td>Strong by event order</td>
<td>Message based</td>
</tr>
<tr>
<td>Undo and audit</td>
<td>Strong with retained values</td>
<td>Poor, needs inverse ops</td>
<td>Poor unless versions kept</td>
<td>Medium</td>
<td>Strong</td>
<td>Medium</td>
</tr>
<tr>
<td>Cognitive load</td>
<td>Medium</td>
<td>Low locally, high globally</td>
<td>Medium</td>
<td>High internally</td>
<td>High</td>
<td>Medium</td>
</tr>
<tr>
<td>Concurrency</td>
<td>Strong for reads</td>
<td>Lock-heavy</td>
<td>Strong after publish</td>
<td>Good with care</td>
<td>Good for append path</td>
<td>Good by isolation</td>
</tr>
<tr>
<td>Fit for entity lifecycle</td>
<td>Medium</td>
<td>Strong</td>
<td>Medium</td>
<td>Medium</td>
<td>Strong</td>
<td>Strong</td>
</tr>
<tr>
<td>Interop with mutable APIs</td>
<td>Needs adapter</td>
<td>Natural</td>
<td>Natural during build</td>
<td>Usually hidden</td>
<td>Needs projection</td>
<td>Needs messages</td>
</tr>
</tbody>
</table>

Reading of the table. Immutability wins for stable facts, readers, comparison,
and replay. Shared Mutable State wins for tightly scoped local mutation.
Builder wins for construction of one value. Copy on Write wins when many readers
and rare writers share a representation. Event Sourcing wins when the domain
needs an audit log of changes, not only current values. Actor Model wins when
identity and serial message processing matter more than value comparison.

## 13. Related and incompatible patterns

- **Persistent Data Structures.** The main implementation partner. Persistent
  structures make immutable updates practical for larger collections by sharing
  unchanged nodes. Clojure and Immutable.js are the cited production examples
  for this relationship (https://clojure.org/reference/data_structures and
  https://immutable-js.com/, verified 2026-08-02).
- **Pure Functions.** Immutability makes pure functions easier to write because
  inputs can be read without defensive copying. Pure functions, in turn, make
  transitions easier to test.
- **Value Object.** A Value Object is usually immutable because its identity is
  its value. Immutability is the broader rule. Value Object is the domain
  modeling pattern.
- **Memoization.** Composes well. Stable inputs make cache keys meaningful.
  Mutable inputs require defensive hashing or copies.
- **Event Sourcing.** Often replaces snapshot-only immutability when the
  transition history itself is the source of truth. Immutable snapshots can
  still be used as projections.
- **Builder.** Complements the pattern. A builder is mutable during assembly and
  returns an immutable value at the end.
- **Memento.** Uses immutable snapshots to capture state for undo. Without
  immutable snapshots, a memento can change behind the caller's back.
- **Flyweight.** Composes well with immutable values because shared flyweights
  cannot be edited by one caller and observed by another.
- **Active Record.** Often conflicts. Active Record instances usually combine
  identity, persistence methods, and mutable fields. Use immutable DTOs or
  snapshots around them when crossing service or thread boundaries.
- **Shared Mutable State.** Actively conflicts at the same boundary. You can use
  local mutation inside a transition, but publishing the mutable object as the
  value defeats the pattern.
- **Object Pool.** Usually conflicts for values. Reusing object instances by
  overwriting fields breaks the guarantee that a retained value stays stable.
  Pools can still manage internal buffers used to construct immutable outputs.

## 14. Refactoring path in and out

Introducing immutability into a mutable design.

1. Pick one boundary, not the whole codebase. Good first targets are request
   DTOs, cache keys, configuration snapshots, UI state, and domain value
   objects.
2. Write a characterization test around the current observable behavior. Capture
   the old value before a transition and assert whether it should remain
   unchanged after the transition.
3. Hide direct field writes behind a transition function, `with` method, copy
   constructor, reducer, or builder.
4. Change the transition to return a new value. Leave the old value untouched in
   tests.
5. Make fields read-only where the language supports it. In TypeScript that is
   `readonly` at type-check time
   (https://www.typescriptlang.org/docs/handbook/2/objects.html, verified
   2026-08-02). In Python dataclasses that can be `frozen=True`
   (https://docs.python.org/3/library/dataclasses.html, verified 2026-08-02).
6. Convert mutable children or copy them on input. A shallow freeze is not
   enough for a deep value contract.
7. Add tests that attempt to mutate the old value after transition and prove the
   new value is not affected, and the reverse.
8. Replace ad hoc nested copies with named helpers once two update sites repeat.
9. Add telemetry around transition count, allocation-sensitive paths, and
   retained snapshot count before expanding the pattern to larger values.

Named refactorings from the refactoring family that often apply are Encapsulate
Variable, Replace Temp with Query, Split Phase, Introduce Parameter Object, and
Replace Derived Variable with Query. The exact path depends on where mutation is
hidden.

Removing immutability when it stops paying.

1. Find the boundary where allocation or copy cost is measured, not guessed.
2. Preserve the public contract first. If callers depend on stable values,
   create a mutable internal builder and still publish an immutable result.
3. If only internal code needs speed, introduce a private mutable accumulator
   inside the transition. Keep it unreachable from observers.
4. If most updates touch the entire graph, replace persistent collections with a
   mutable work buffer plus a final snapshot.
5. If value equality hides entity identity, split the model into an immutable
   snapshot and a separate entity reference.
6. Delete old snapshot retention if undo, audit, and comparison no longer need
   it. Add tests that prove no caller can observe a recycled instance.

## 15. Testing and verification

Engineering judgement. Testing immutable code is less about mocking and more
about proving old and new values are independent.

What becomes easier.

- Transition functions can be tested as input value, change, expected output.
- Old value preservation is directly assertable.
- Equality-based assertions become useful because value equality carries domain
  meaning.
- Property tests can generate sequences of changes and assert invariants over
  every resulting value.
- Memoization and caching can be tested with stable keys.

What becomes harder.

- Allocation behavior needs performance tests or counters. Unit tests rarely
  reveal excessive copying.
- Deep immutability needs mutation probes or type-system support. A shallow
  read-only annotation can pass compile checks while a nested list still mutates.
- Draft libraries need tests that prove the base value is untouched and that the
  result contains every intended change.

Useful techniques.

- **Old value assertion.** Save a reference to the value before transition.
  Apply the change. Assert the old value is equal to its original copy.
- **Reference sharing assertion.** When using persistent structures, assert that
  unchanged branches retain identity where the API exposes that safely. Do not
  assert private node identity from third-party libraries.
- **Mutation probe.** Attempt field assignment in tests where the language
  raises at runtime, such as a Python frozen dataclass. Python documents
  `FrozenInstanceError` for generated setters on frozen dataclasses
  (https://docs.python.org/3/library/dataclasses.html, verified 2026-08-02).
- **Reducer table test.** For reducer style, maintain a table of old state,
  action, new state, and old-state-afterward.
- **Property test over change sequences.** Generate a random sequence of
  changes, keep every intermediate value, and assert invariants over all of
  them. For example, total quantity is never negative and older versions remain
  unchanged.
- **Hash stability test.** Insert a value into a set or map, run available
  operations, and assert lookup still succeeds.
- **Concurrency smoke test.** Share one value across readers while a writer
  publishes replacements. Readers should never observe a partially updated
  value.

The code examples below were compiled or run with local tools before this entry
was completed.

## 16. Observability signals

Engineering judgement. Immutability is visible at transition and publication
points, not inside passive values.

Record these signals.

- A counter of transitions by value type and change type.
- A histogram of transition duration, especially for large values.
- A counter of copied or allocated nodes where the implementation can expose it.
- A gauge of retained versions per owner, cache, undo stack, or subscriber.
- A gauge or estimate of retained bytes for snapshots.
- A counter of rejected mutation attempts in runtime-enforced models.
- A counter of stale-write retries for optimistic concurrency.
- A trace attribute with old version id and new version id. Use hashes or
  monotonic versions, not raw personal data.
- A diff size metric. Count fields, keys, or nodes changed by each transition.

A healthy instance. Transition latency is a small part of request latency.
Retained version counts are bounded by configured windows. Diff sizes match the
business operation. Stale-write retries are rare and explained by concurrent
edits. Cache hit rates improve for memoized reads.

A failing instance. Retained snapshot count climbs without bound. Transition
latency grows with total state size rather than changed path size. Diff size is
small but allocated bytes are large, which points at full-graph copying. A
mutation rejection counter rises after a deployment, which points at code still
using old in-place writes. React or Redux applications show UI stale-state bugs
while logs show reducers returning the same top-level object.

Privacy note. Do not log whole old and new values by default. Log version ids,
type names, counts, and small redacted diffs. Full diffs belong behind explicit
debug controls with retention limits.

## 17. Security and privacy implications

Engineering judgement. Immutability is not a security product, but it changes
where data can be tampered with and how evidence can be preserved.

Security benefits.

- Immutable policy snapshots reduce time-of-check to time-of-use bugs inside a
  process. Authorization can evaluate one policy value without another routine
  changing it halfway through.
- Immutable inputs at trust boundaries prevent callers from changing data after
  validation by retaining an alias.
- Content-addressed immutable objects give tamper evidence because identity
  depends on content. Git's object keys are derived from stored content plus a
  header in the object database
  (https://git-scm.com/book/en/v2/Git-Internals-Git-Objects, verified
  2026-08-02).
- Immutable audit events are easier to retain and replay than mutable status
  rows, though storage controls still decide whether they are trustworthy.

Security risks.

- Retaining old versions can retain old secrets. A password, token, personal
  data field, or policy exception may remain reachable in history after the
  current value is redacted.
- Full-value logging leaks more data because old and new values are often both
  available at the transition boundary.
- Shallow immutability can create false confidence. A caller may mutate a nested
  collection inside a supposedly read-only object unless the boundary copies or
  converts it.
- Draft libraries can hide mutation syntax. Reviewers must know whether a
  mutable-looking block is inside a safe draft boundary such as Immer's
  `produce` (https://immerjs.github.io/immer/produce/, verified 2026-08-02).

Privacy handling.

- Apply retention policy to every old version store, including undo, audit,
  traces, caches, message replay, and debugging snapshots.
- Redact or tokenize before values become immutable history, not after.
- Treat version ids derived from content as sensitive when the content space is
  small enough for guessing.
- Do not store raw before-and-after diffs for personal data unless there is a
  legal and product reason to keep both.

Where the pattern is silent. It does not authenticate data, authorize access,
encrypt storage, or validate business rules. It only makes a value stable after
the moment it is accepted.

## 18. References

1. John McCarthy. "Recursive Functions of Symbolic Expressions and Their
   Computation by Machine, Part I." *Communications of the ACM*, 1960. Source
   for early Lisp lineage around symbolic expression data and recursive
   functions.
   https://www-formal.stanford.edu/jmc/recursive.html
   Verified 2026-08-02.
2. Chris Okasaki. *Purely Functional Data Structures*. Cambridge University
   Press, 1998. Chapters 2 through 5. Source for the algorithmic lineage of
   persistent data structures.
   https://www.cambridge.org/core/books/abs/purely-functional-data-structures/contents/9DA321DB54345B01758FE0107B9824E2
   Verified 2026-08-02.
3. Oracle. *Java SE 21 API Specification*, `java.lang.String`.
   https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/String.html
   Verified 2026-08-02. Source for Java `String` immutability and sharing.
4. Clojure. "Data Structures."
   https://clojure.org/reference/data_structures
   Verified 2026-08-02. Source for Clojure immutable persistent collections,
   structural sharing, and collection operation notes.
5. Meta Open Source. React documentation, "Updating Objects in State."
   https://react.dev/learn/updating-objects-in-state
   Verified 2026-08-02. Source for React state replacement guidance.
6. Redux documentation. "Immutable Update Patterns."
   https://redux.js.org/usage/structuring-reducers/immutable-update-patterns
   Verified 2026-08-02. Source for nested copy rules, common immutable update
   mistakes, and Redux Toolkit with Immer.
7. Immer documentation. "Using produce."
   https://immerjs.github.io/immer/produce/
   Verified 2026-08-02. Source for draft mutation with untouched base state and
   produced next state.
8. Immutable.js documentation. "Persistent, immutable data structures for
   JavaScript / TypeScript."
   https://immutable-js.com/
   Verified 2026-08-02. Source for JavaScript persistent collections and
   structural sharing claims.
9. Python Software Foundation. Python 3 documentation, `dataclasses`.
   https://docs.python.org/3/library/dataclasses.html
   Verified 2026-08-02. Source for `frozen=True`, `FrozenInstanceError`, and
   hash behavior tied to frozen dataclasses.
10. TypeScript documentation. "Object Types", `readonly` properties.
    https://www.typescriptlang.org/docs/handbook/2/objects.html
    Verified 2026-08-02. Source for `readonly` as a type-checking property
    modifier with no runtime behavior change.
11. Scott Chacon and Ben Straub. *Pro Git*, 2nd edition, chapter 10.2, "Git
    Objects."
    https://git-scm.com/book/en/v2/Git-Internals-Git-Objects
    Verified 2026-08-02. Source for Git content-addressed object storage and
    separate stored file versions.

## Code examples

Three languages are used because they express different parts of the pattern.
TypeScript shows read-only boundaries and replacement for UI-style state.
Python shows frozen dataclasses and a tuple-backed update. Rust shows owned
values and structural sharing through `Arc`. Java, Go, and Swift are omitted to
keep the examples focused on three runnable shapes rather than repeating the
same copy method.

### TypeScript

```typescript
type Line = Readonly<{
  sku: string;
  quantity: number;
}>;

type Cart = Readonly<{
  id: string;
  lines: readonly Line[];
}>;

function addLine(cart: Cart, line: Line): Cart {
  return {
    ...cart,
    lines: [...cart.lines, line],
  };
}

function changeQuantity(cart: Cart, sku: string, quantity: number): Cart {
  return {
    ...cart,
    lines: cart.lines.map((line) =>
      line.sku === sku ? { ...line, quantity } : line
    ),
  };
}

const first: Cart = { id: "C-1", lines: [] };
const second = addLine(first, { sku: "book", quantity: 1 });
const third = changeQuantity(second, "book", 3);

console.log(first.lines.length);
console.log(second.lines[0].quantity);
console.log(third.lines[0].quantity);
```

### Python

```python
from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Line:
    sku: str
    quantity: int


@dataclass(frozen=True)
class Cart:
    id: str
    lines: tuple[Line, ...] = ()

    def add_line(self, line: Line) -> "Cart":
        return replace(self, lines=self.lines + (line,))

    def change_quantity(self, sku: str, quantity: int) -> "Cart":
        return replace(
            self,
            lines=tuple(
                replace(line, quantity=quantity) if line.sku == sku else line
                for line in self.lines
            ),
        )


first = Cart("C-1")
second = first.add_line(Line("book", 1))
third = second.change_quantity("book", 3)

print(len(first.lines))
print(second.lines[0].quantity)
print(third.lines[0].quantity)
```

### Rust

```rust
use std::sync::Arc;

#[derive(Clone, Debug, PartialEq, Eq)]
struct Line {
    sku: String,
    quantity: u32,
}

#[derive(Clone, Debug, PartialEq, Eq)]
struct Cart {
    id: String,
    lines: Arc<Vec<Line>>,
}

impl Cart {
    fn new(id: &str) -> Self {
        Self {
            id: id.to_string(),
            lines: Arc::new(Vec::new()),
        }
    }

    fn add_line(&self, line: Line) -> Self {
        let mut lines = Vec::with_capacity(self.lines.len() + 1);
        lines.extend(self.lines.iter().cloned());
        lines.push(line);
        Self {
            id: self.id.clone(),
            lines: Arc::new(lines),
        }
    }

    fn change_quantity(&self, sku: &str, quantity: u32) -> Self {
        let lines = self
            .lines
            .iter()
            .map(|line| {
                if line.sku == sku {
                    Line {
                        sku: line.sku.clone(),
                        quantity,
                    }
                } else {
                    line.clone()
                }
            })
            .collect();
        Self {
            id: self.id.clone(),
            lines: Arc::new(lines),
        }
    }
}

fn main() {
    let first = Cart::new("C-1");
    let second = first.add_line(Line {
        sku: "book".to_string(),
        quantity: 1,
    });
    let third = second.change_quantity("book", 3);

    println!("{}", first.lines.len());
    println!("{}", second.lines[0].quantity);
    println!("{}", third.lines[0].quantity);
}
```
