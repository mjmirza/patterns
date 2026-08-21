---
name: Persistent Data Structures
slug: persistent-data-structures
family: 16-functional
category: Data and State
aliases: [Persistent Collections, Functional Data Structures, Immutable Collections]
first_described: "Driscoll, Sarnak, Sleator, Tarjan 1989"
maturity: canonical
related: [immutability, value-object, lens, event-sourcing, copy-on-write]
incompatible_with: [shared-mutable-state, in-place-aggregate-mutation]
verified: 2026-08-02
---

# Persistent Data Structures

## 1. Name, aliases, and lineage

The canonical name is Persistent Data Structures. In this pattern, persistence
means that update operations keep older versions available. It does not mean
durability on disk. James R. Driscoll, Neil Sarnak, Daniel D. Sleator, and
Robert E. Tarjan gave the classic algorithmic definition in "Making Data
Structures Persistent", *Journal of Computer and System Sciences*, volume 38,
issue 1, 1989. DBLP lists the paper as *Journal of Computer and System
Sciences*, volume 38, issue 1, pages 86-124, 1989
(https://dblp.org/rec/journals/jcss/DriscollSST89, verified 2026-08-02).

Common aliases are **persistent collections**, **functional data structures**,
and **structural sharing**. These names are close but not identical.

- **Persistent collection** names a list, vector, map, set, tree, or queue whose
  update operation returns a new collection and leaves the prior collection
  usable.
- **Functional data structure** is the phrase Chris Okasaki uses in *Purely
  Functional Data Structures*, Cambridge University Press, 1998, chapters 1
  through 3. Cambridge lists chapter 2 as "Persistence"
  (https://www.cambridge.org/core/books/purely-functional-data-structures/persistence/BEB36D6BF24898A7CA3A188DA5C35ED1,
  verified 2026-08-02).
- **Structural sharing** is the implementation idea. A new version points at
  unchanged nodes from the old version and allocates only the path or fringe
  needed to represent the edit. Clojure documents its persistent collections as
  creating modified versions through structural sharing
  (https://clojure.org/reference/data_structures, verified 2026-08-02).

The pattern also has subtypes. A **partially persistent** structure allows
queries against old versions but updates only at the newest version. A **fully
persistent** structure allows both queries and updates from any version. A
**confluently persistent** structure can combine branches of history. The NIST
Dictionary of Algorithms and Data Structures lists partially persistent, fully
persistent, and confluently persistent data structures as specializations of the
term (https://xlinux.nist.gov/dads/HTML/persistentDataStructure.html, verified
2026-08-02).

In production programming, the name often narrows to immutable collections with
efficient updates. Clojure says all collections are immutable and persistent,
with vectors and hash maps using wide tree paths for access
(https://clojure.org/reference/data_structures, verified 2026-08-02). Scala's
documentation explains immutable `Vector` as a high branching factor tree, with
functional updates that copy only the affected node path
(https://docs.scala-lang.org/overviews/collections-2.13/concrete-immutable-collection-classes.html,
verified 2026-08-02). Immutable.js says its JavaScript collections use
structural sharing through hash map tries and vector tries
(https://github.com/immutable-js/immutable-js, verified 2026-08-02).

This entry uses the production meaning. A persistent data structure is an
immutable structure with update operations that produce a new version while
retaining old versions, normally by sharing unchanged representation.

## 2. Problem and context

A program needs snapshots of data across time, but a normal mutable collection
has one current shape. When code changes that shape in place, any holder of the
old reference silently observes the new state. The defect is not that mutation
exists. The defect is that the program has two time meanings and one reference.

The problem appears in ordinary application code. A reducer receives a state
tree and an action. A validation stage reads a map and starts a background task.
An undo stack keeps a previous document version. A compiler pass wants the
original syntax tree for diagnostics and a transformed tree for optimization. A
service wants a routing table snapshot while a control plane publishes a new
route. A database or version-control system names prior states and needs those
states to remain recoverable. In each case, copying the whole structure on
every edit is simple but too costly, while in-place mutation is cheap but loses
the old version.

Persistent data structures split those costs. The public operation behaves as a
value transition. The old value remains valid. The new value records the edit.
The implementation shares all representation that did not change. For a linked
list, prepending one item allocates one node and points its tail at the old
list. For a search tree, updating one key allocates the nodes along the search
path and reuses untouched subtrees. For a wide vector trie or hash array mapped
trie, updating one index or key copies a small path through arrays and reuses
the rest. Scala's immutable `Vector` documentation describes this path-copy
model and says a middle update copies the node that contains the element plus
the nodes that point to it
(https://docs.scala-lang.org/overviews/collections-2.13/concrete-immutable-collection-classes.html,
verified 2026-08-02).

The context that makes the pattern fit has three parts.

- More than one version has business or operational meaning.
- Most edits affect a small part of a larger structure.
- The cost of lost snapshots, aliasing bugs, or coarse locks is higher than the
  cost of allocated path nodes and indirection.

Outside that context, a mutable array, mutable hash table, or mutable builder
may be the clearer design. Persistent data structures are not a ban on
mutation. They are a versioning strategy for values.

## 3. Forces

Engineering judgement. The cited sources prove named algorithms, APIs, and
systems. The trade between forces is design judgement drawn from how the
pattern behaves in programs.

- **Consistency.** Favoured. A reference to version `v1` keeps meaning `v1`
  after version `v2` is made. This directly addresses aliasing and time.
- **Coupling.** Favoured across module boundaries. A caller can pass a
  collection to another module without giving that module authority to edit the
  caller's version.
- **Latency.** Mixed. Reads often add one or more pointer hops compared with a
  flat mutable array or table. Writes avoid full copies but still allocate path
  nodes. Clojure vectors document access in `log32N` hops
  (https://clojure.org/reference/data_structures, verified 2026-08-02).
- **Memory.** Mixed. One update can allocate far less than a full copy, because
  old and new versions share most nodes. Retaining many roots can also retain
  old paths and values longer than a mutable design would.
- **Operability.** Favoured. Version roots can be logged, counted, compared,
  kept in undo stacks, or exposed as snapshots. Git's data model documents
  immutable objects named by content and commits that point to trees and parent
  commits (https://git-scm.com/docs/gitdatamodel.html, verified 2026-08-02).
- **Cost.** Mixed. A library implementation is harder than a mutable collection.
  Application code using a mature library is often simpler because update
  contracts are explicit.
- **Team topology.** Favoured when platform code publishes values to product
  teams. Consumers receive snapshots rather than shared write access.
- **Cognitive load.** Mixed. Reasoning about versions is easier. Reasoning
  about structural sharing, stale roots, and performance cliffs can be harder.

The pattern favours version identity, safe sharing, undo, replay, concurrent
readers, and pure transformation APIs. It sacrifices the raw speed and spatial
locality of specialised mutable structures.

One practical force deserves separate treatment: **publication granularity**.
Persistent data structures make many private edits appear as one public root
change when the code batches them behind a builder or transient. That favours
systems where readers care about complete snapshots rather than half-applied
steps. The cost is that a writer must decide where a batch begins and ends.
Publishing too often wastes allocation. Publishing too late can hide progress
from readers that need fresh state.

Another force is **history shape**. A plain mutable collection has one line of
time. A persistent structure can have many roots, which means many branches.
That branch shape is useful for editors, speculative compilers, search
algorithms, and retry logic. It can be confusing in ordinary services when
callers assume there is one current truth. The owner reference must say which
root is current, and older roots must be labelled as snapshots rather than
silently mixed into current business decisions.

## 4. Applicability and non-applicability

Reach for Persistent Data Structures when the following hold.

- **Snapshots are a core use case.** Undo, redo, audit, optimistic concurrency,
  time-travel debugging, editor history, query-plan history, and compiler
  intermediate forms all benefit from old versions remaining valid.
- **Read sharing is broad.** A routing table, permission graph, feature flag
  map, syntax tree, configuration value, or catalog can be read by many threads
  while one writer prepares the next version.
- **Updates are small relative to the structure.** Path copying pays off when
  an edit changes one key, one index, one subtree, or a narrow slice.
- **The language or framework expects immutable state.** Redux explains that
  immutable updates let shallow equality checks detect state changes, and its
  docs warn against direct state mutation
  (https://redux.js.org/faq/immutable-data, verified 2026-08-02).
- **Concurrent readers matter more than write throughput.** Publishing a new
  root can be cheaper and simpler than coordinating readers through locks.
- **Equality, hashing, memoization, or caching depend on stable values.**
  Immutable roots and subtrees can safely participate in these mechanisms when
  their element values are also stable.
- **The domain wants values, not locations.** ASTs, maps of settings, form
  states, search indexes, game-state snapshots, and document models often want
  named versions rather than mutable places.

Do NOT reach for Persistent Data Structures in these cases.

- **Non-applicability. Single-owner hot mutation.** A parser scratch buffer,
  compression window, numeric vector, graphics buffer, or packet assembly area
  with one owner and no version need should use mutable storage.
- **Non-applicability. Whole-structure rewrites dominate.** If every operation
  replaces most nodes, sharing gives little benefit and can add pointer-chasing
  cost.
- **Non-applicability. External APIs require stable identity and in-place
  callbacks.** Some native libraries, UI widgets, ORMs, and serialization
  frameworks expect mutation through object identity. Use an adapter and convert
  at the boundary.
- **Non-applicability. Retained versions would leak sensitive data.** Keeping
  old roots can keep old secrets reachable. A mutable buffer that is wiped, or
  a purpose-built secret store, is safer for keys and credentials.
- **Non-applicability. The team lacks a mature implementation.** Hand-writing a
  HAMT or vector trie inside business code is riskier than using a library or a
  simpler mutable representation.
- **Non-applicability. Deterministic iteration order is required but the chosen
  structure does not provide it.** Hash tries can have library-specific order.
  Use an ordered tree or ordered map when order is part of the contract.
- **Non-applicability. You need cache-friendly linear scans above all else.** A
  packed array can beat a tree of nodes by wide margins in tight loops because
  CPU caches reward contiguous memory.
- **Non-applicability. All versions must be physically independent.** Some
  isolation or erasure regimes require no shared representation between copies.
  Structural sharing would violate that policy.

## 5. Structure

The pattern has six participants.

- **Version root.** The handle a client stores. It can be a pointer to a list
  node, tree root, vector root, map root, or commit object. The root identifies
  one logical version.
- **Shared node.** An internal representation node whose contents are never
  changed after publication. Many version roots can point at the same node.
- **Update operation.** A function such as `assoc`, `set`, `updated`, `insert`,
  `push`, or `delete`. It accepts a root plus a change and returns a new root.
- **Path-copy engine.** The internal algorithm that allocates only the nodes
  that differ between old and new versions, then wires untouched children back
  into the new path.
- **Owner reference.** The mutable place, if any, that names the current root.
  In application code this can be an atom, store, variable, actor state, branch
  ref, or database pointer. The value is persistent. The owner reference can
  still move from one root to another.
- **Transient builder or mutable batch.** An optional private editing mode used
  to build many changes before publishing one persistent result. Clojure
  documents transient vectors, hash maps, and hash sets as an optimization that
  starts from a persistent structure and returns to a persistent structure with
  `persistent!` (https://clojure.org/reference/transients, verified
  2026-08-02).

The important boundary is publication. Internal mutation inside a path-copy
operation can be valid when no outside code can observe the mutable node.
Clojure's transient documentation says its persistent structures use mutation
inside newly allocated arrays before those arrays are returned for immutable
use (https://clojure.org/reference/transients, verified 2026-08-02). The public
contract remains that existing roots keep their old logical value.

## 6. ASCII structure diagram

```text
Before update of key k:

  root A
    |
    v
  +---------+
  | node r  |
  +----+----+
       |
       +------------------+------------------+
       v                  v                  v
  +---------+        +---------+        +---------+
  | node x  |        | node y  |        | node z  |
  +----+----+        +---------+        +---------+
       |
       v
  +---------+
  | leaf k  |  value = old
  +---------+

After update of key k:

  root A                                  root B
    |                                       |
    v                                       v
  +---------+                         +---------+
  | node r  |                         | node r' |
  +----+----+                         +----+----+
       |                                   |
       +-------------+-------------+       +-------------+-------------+
       v             v             v       v             v             v
  +---------+   +---------+   +---------+ +---------+ +---------+ +---------+
  | node x  |   | node y  |   | node z  | | node x' | | node y  | | node z  |
  +----+----+   +---------+   +---------+ +----+----+ +---------+ +---------+
       |                                   |
       v                                   v
  +---------+                         +---------+
  | leaf k  | old value               | leaf k' | new value
  +---------+                         +---------+

Unchanged nodes y and z are shared. The edited path is copied.
```

## 7. Dynamics

At runtime, a client does not edit a node it already holds. It asks for a new
root. The update walks to the affected position, allocates a replacement path,
reuses untouched children, and returns the new root.

```text
Client          Owner Ref        Persistent Map        Path-Copy Engine
  |                |                    |                       |
  | read current   |                    |                       |
  |--------------->|                    |                       |
  |<---------------| root A             |                       |
  |                |                    |                       |
  | assoc(A,k,v)   |                    |                       |
  |------------------------------------>|                       |
  |                |                    | find path for k       |
  |                |                    |---------------------->|
  |                |                    |                       |
  |                |                    | allocate leaf k'      |
  |                |                    | allocate copied path  |
  |                |                    | reuse other children  |
  |                |                    |<----------------------|
  |                |                    | root B                |
  |<------------------------------------|                       |
  |                |                    |                       |
  | compare/swap   |                    |                       |
  |--------------->| root A -> root B   |                       |
  |<---------------| success or retry   |                       |
```

Two timing details shape production behavior. First, stale roots are expected.
If a caller keeps root A while root B is current, that is not a race by itself.
It is a deliberate snapshot. Second, an owner reference can still have races.
Two writers that both read root A and publish different root B values need
compare-and-swap, a transaction, a lock, or domain-level conflict handling.
Clojure atoms document `swap!` as applying a function to the old value and
retrying when another thread changes the value first
(https://clojure.org/reference/atoms, verified 2026-08-02).

## 8. Implementation variants

**Cons list.** The smallest persistent structure is a singly linked list. A
prepend allocates one node whose tail points to the old list. This gives O(1)
prepend and O(1) old-version retention. Random access and append are linear, so
the list fits stacks, streams, and recursive algorithms better than indexed
sequences.

The cons list is useful as a teaching model because every part of the sharing
is visible. It is less useful as a default application collection. A team that
uses persistent lists for workloads that need random access will blame the
pattern for a poor collection choice. Engineering judgement. Lists fit last-in,
first-out flow, recursive decomposition, and small front-biased sequences. They
do not fit general-purpose indexed state.

**Path-copy search tree.** A binary search tree, red-black tree, B-tree, or
ordered map can update by copying nodes along the search path. Untouched
subtrees are shared. This fits sorted maps and sets. The costs are balancing
logic, allocator pressure, and pointer chasing.

This variant is a good fit when iteration order is contractual. Ordered maps
are often easier to reason about in tests, snapshots, replication streams, and
deterministic builds because the traversal order comes from key order rather
than from hash buckets. The trade is that comparisons now sit on the hot path.
Keys must have stable ordering, and the ordering must match the domain. A path
string, locale-aware label, version tuple, and numeric id can all produce
different order semantics.

**Persistent vector trie.** A vector trie uses chunks, often width 32, to make
index operations shallow. Clojure vectors document `log32N` access
(https://clojure.org/reference/data_structures, verified 2026-08-02). Scala's
immutable `Vector` documentation describes a high branching factor tree and
functional updates that copy a small number of nodes
(https://docs.scala-lang.org/overviews/collections-2.13/concrete-immutable-collection-classes.html,
verified 2026-08-02). This variant fits application state, AST child lists,
editor buffers, and queues of moderate size.

The vector trie is the common answer when developers want an immutable
collection that feels close to an array. Engineering judgement. It should still
be treated as a tree. Iteration, indexing, appending, and slicing can each have
different constants. For a state tree with many small vectors, the constants
are usually acceptable. For a numeric buffer scanned millions of times per
second, the same constants are likely too high. The design review should ask
what operation dominates before choosing it.

**Hash array mapped trie.** A HAMT indexes by chunks of the key hash. It gives
immutable hash maps and hash sets with wide branching and structural sharing.
Phil Bagwell's "Ideal Hash Trees" describes hash array mapped tries as the
basis for hash trees
(https://www.researchgate.net/publication/2378571_Ideal_Hash_Trees, verified
2026-08-02). Immutable.js says its maps and sets use hash map tries
(https://github.com/immutable-js/immutable-js, verified 2026-08-02).

HAMTs are the workhorse for persistent maps because one key update usually
touches a shallow path determined by hash chunks. They also inherit the normal
hash-map concerns: key equality, hash quality, collision behavior, and
iteration order. The implementation must handle collisions without breaking the
version contract. Application code should avoid treating traversal order as
meaningful unless the library documents that order.

**Relaxed radix balanced tree.** RRB trees adapt vector tries for faster
concatenation and slicing. The Rust `im_rc` crate documents vectors based on
RRB trees and hash maps based on HAMTs (https://docs.rs/im-rc, verified
2026-08-02). Use this when vector concatenation and slicing are first-class
operations.

**Owner reference plus persistent value.** Clojure atoms, refs, and agents use
stable values behind changing references. Clojure refs documentation says
persistent collections have free copies because the original cannot be changed,
and modifications share structure efficiently
(https://clojure.org/reference/refs, verified 2026-08-02).

**Transient or builder-backed batch.** A batch update can use a private mutable
editing window, then publish a persistent result. Clojure transients support
this shape for vectors, hash maps, and hash sets
(https://clojure.org/reference/transients, verified 2026-08-02). Immutable.js
has a `withMutations` API for selected operations
(https://github.com/immutable-js/immutable-js, verified 2026-08-02). The risk is
leaking the mutable phase or assuming all operations are safe in that phase.

The builder variant is often the difference between a pattern that works in a
demo and a pattern that works under production volume. A reducer that updates
three fields can call three persistent operations without concern. A loader
that inserts five million rows should not do that if the library offers a bulk
constructor. Engineering judgement. Prefer persistent single updates for small
domain transitions, and prefer builders for import, reindexing, parsing, and
large derived views.

**Content-addressed persistent graph.** Git stores immutable objects and commits
that point to trees and parent commits. A new commit names a new root while
unchanged blobs and trees can be reused by identity. Git's data model documents
objects that never change after creation and commits that point to a tree plus
parent commits (https://git-scm.com/docs/gitdatamodel.html, verified
2026-08-02). Engineering judgement. Git is not an in-memory functional
collection library, but its object graph is a production example of persistent
versioned structure.

## 9. Known production uses

**Clojure persistent collections.** Clojure documents lists, vectors, maps, and
sets as immutable and persistent. The same page states that modified versions
are created through structural sharing and that collections support persistent
manipulation (https://clojure.org/reference/data_structures, verified
2026-08-02). This is a direct language-level use.

**Scala immutable collections.** Scala's collection guide documents immutable
`Vector` as a tree with branching factor 32 and explains that functional vector
updates copy the changed node and the nodes pointing to it rather than copying
the whole vector
(https://docs.scala-lang.org/overviews/collections-2.13/concrete-immutable-collection-classes.html,
verified 2026-08-02). The Scala API page describes `Vector` as an immutable
data structure with random access and updates in O(log n) time
(https://www.scala-lang.org/api/current/scala/collection/immutable/Vector.html,
verified 2026-08-02).

**Immutable.js.** Immutable.js is a JavaScript library whose README describes
`List`, `Stack`, `Map`, `OrderedMap`, `Set`, `OrderedSet`, and `Record` as
persistent immutable data structures. It says the structures use structural
sharing via hash map tries and vector tries, following Clojure and Scala
(https://github.com/immutable-js/immutable-js, verified 2026-08-02).

**Vavr.** Vavr is a functional library for Java 8 and later. Its user guide says
Vavr provides persistent data types and functional control structures, and its
section on persistent data structures defines them as preserving previous
versions when modified (https://docs.vavr.io/, verified 2026-08-02).

**Git object database.** Git's documented data model stores immutable objects,
names objects by hashes, and represents history through commits pointing to
trees and parent commits (https://git-scm.com/docs/gitdatamodel.html, verified
2026-08-02). Engineering judgement. This is a storage-system form of the same
version-root idea, not the same API shape as a Clojure vector or HAMT.

## 10. Consequences

Positive.

- Old versions remain valid without defensive copying at every call boundary.
- Readers can share a value without locks when the element values are also
  immutable or treated as immutable.
- Undo, redo, time travel, optimistic retry, branch history, and snapshot
  comparison become ordinary data operations.
- Change detection can use root identity or shallow equality when every update
  returns a new root. Redux documents this style for shallow equality checks
  (https://redux.js.org/faq/immutable-data, verified 2026-08-02).
- Tests can keep before and after values and assert both, which exposes hidden
  mutation quickly.
- Ownership is clearer. The mutable part of the system is the reference that
  names the current root, not every node inside the value.
- Batching APIs can recover much of the performance of local mutation without
  changing the published contract, as Clojure transients demonstrate
  (https://clojure.org/reference/transients, verified 2026-08-02).

Negative.

- Writes allocate. A path-copy update is cheaper than a full copy but more
  expensive than overwriting one cell in a mutable array.
- Reads can pay extra indirection and branch cost. A persistent vector is not a
  flat array.
- Old roots can keep old data alive. This is useful for history and dangerous
  for memory pressure or sensitive values.
- Profiling can be less obvious because the allocation site is an innocent
  update call rather than an explicit constructor for every internal node.
- Bulk edits need a builder, transient mode, or algorithmic care. Repeated
  single updates can allocate many paths.
- Interop with mutable frameworks can create boundary bugs when a persistent
  value contains mutable elements.
- Developers may mistake persistence for durability and assume values survive
  process exit. They do not unless stored somewhere durable.

## 11. Failure modes and misuse

Engineering judgement. These failure modes are phrased as observable triples so
a reviewer can diagnose them in a live codebase.

- **Symptom. Memory grows with every user action and does not fall after garbage
  collection. Cause. An undo stack, cache, closure, or observer keeps old roots
  forever. Fix. Put a retention policy on roots, store deltas or checkpoints
  deliberately, and expose version counts in telemetry.**
- **Symptom. A value from an old snapshot changes anyway. Cause. The persistent
  collection stores mutable elements, and code mutated an element in place. Fix.
  Make element values immutable, deep-freeze at boundaries in development, or
  copy mutable elements before insertion.**
- **Symptom. A loop that builds a large map becomes allocation-heavy. Cause.
  The code performs thousands of independent persistent updates instead of a
  batched edit. Fix. Use a transient, builder, mutable local accumulator, or
  bulk constructor, then publish one persistent result.**
- **Symptom. React, Redux, or another shallow-change system misses an update.
  Cause. A reducer or helper mutated a nested object and returned the same root.
  Fix. Return a new root on every logical change, use development mutation
  checks, or use a proven immutable update helper. Redux documents direct
  mutation as a common source of views not updating
  (https://redux.js.org/faq/immutable-data, verified 2026-08-02).**
- **Symptom. CPU profiles show many cache misses during linear scans. Cause. A
  tree-shaped persistent vector or map replaced a packed array in a scan-heavy
  hot path. Fix. Keep a packed representation for the hot path and convert at
  the boundary, or use a mutable local work array.**
- **Symptom. Two writers lose each other's updates. Cause. The values are
  persistent, but the owner reference was overwritten without compare-and-swap,
  transaction, or merge. Fix. Treat root publication as mutable state and guard
  it with the same concurrency discipline as any other shared reference.**
- **Symptom. Secret values remain visible in heap dumps after rotation. Cause.
  Old roots still reference old secret nodes. Fix. Do not store secrets in
  retained persistent structures, or isolate them behind handles that support
  explicit erasure.**
- **Symptom. Tests pass with small maps but production performance collapses
  with adversarial keys. Cause. Hash-trie behavior depends on hash quality and
  collision handling. Fix. Use a trusted implementation, verify hash behavior
  for key types, and consider ordered trees for untrusted key domains.**

## 12. Trade-off matrix

| Force | Persistent Data Structures | Mutable Collections | Copy on Write Arrays | Event Sourcing | Database MVCC |
|---|---|---|---|---|---|
| Version access | Old roots stay usable | Old state is gone unless copied | Prior array survives if copied | Rebuild from event log | Transaction snapshots |
| Write latency | Path allocation per edit | Usually lowest | Full or chunk copy on write | Append event, projection later | Depends on engine |
| Read latency | Pointer hops, often shallow | Direct storage, cache friendly | Direct array reads | Projection read depends on model | Query engine cost |
| Memory | Shares unchanged nodes, retains old paths | One current copy | Can copy large regions | Event log plus projections | Engine-managed versions |
| Coupling | Callers share values safely | Callers share write authority | Safe when copy boundary is clear | State derives from events | State owned by database |
| Consistency | Snapshot consistency by root | Requires locks or ownership | Snapshot per copied array | Consistency in replay rules | Transaction isolation |
| Operability | Roots and versions are inspectable | Need manual snapshots | Copy points are inspectable | Strong audit trail | Strong DB tooling |
| Cognitive load | Version roots plus sharing model | Familiar but alias-prone | Simple for arrays, weak for graphs | Requires event design | Requires DB semantics |
| Best fit | App state, ASTs, maps, undo | Local buffers, hot loops | Medium arrays, mostly reads | Domain audit and replay | Shared transactional data |

The alternatives are not inferior forms of the same idea. Mutable collections
are best for confined mutation. Copy on write arrays are best when the shape is
flat. Event Sourcing records facts and derives state. Database MVCC gives
transactional snapshots under a storage engine. Persistent data structures are
the in-memory value version of the snapshot problem.

## 13. Related and incompatible patterns

**Immutability** is the parent idea. Persistent data structures are immutable
structures designed so updates are efficient enough for daily use. An immutable
record made by full copying is immutable, but it is not necessarily a persistent
data structure in the algorithmic sense.

**Value Object** composes with this pattern. A persistent map of mutable entity
objects is weak because old versions can still drift through element mutation.
A persistent map of value objects keeps the version contract throughout the
reachable graph.

**Lens and optics** compose with persistent nested data. A lens names the path
to update. The persistent structure supplies the sharing behavior that makes
the update affordable.

**Event Sourcing** can replace or complement this pattern. Event Sourcing keeps
the history as events and derives current state. Persistent structures keep
state versions directly. Many systems use both: an event log for audit and a
persistent structure for fast in-memory snapshots.

**Copy on write** is an implementation technique and a neighboring pattern. It
can implement persistent data structures, but a copy-on-write buffer with one
logical current owner may not preserve all old versions.

**Snapshot Isolation and MVCC** are storage-level relatives. They preserve
transaction views inside a database. Persistent data structures offer a similar
root-version concept in application memory, without database transactions.

**Shared Mutable State** conflicts with this pattern when mutable aliases can
change data reachable from old roots. A persistent outer map does not save a
mutable inner object.

**Object Pool** often conflicts. Pooling nodes whose identity is visible can
break the promise that old roots keep their values. Internal allocation pooling
is possible only when reused nodes are never observed as part of a published
version.

## 14. Refactoring path in and out

To introduce the pattern into existing mutable code:

1. Identify one boundary where version stability matters: reducer state,
   compiler AST, configuration map, permission graph, editor document, or
   route table.
2. Add tests that capture the old value, run an update, and assert that the old
   value still reads the old data.
3. Replace direct mutators with transition functions that return a new value.
   Keep names domain-focused, such as `addRoute`, `renameField`, or
   `recordPayment`.
4. Move the mutable current pointer into one owner reference. The rest of the
   code receives roots as values.
5. Use a mature persistent collection for maps, sets, or vectors. Do not begin
   by writing a HAMT unless the project is a collection library.
6. Convert hot batch updates to builders or transients after correctness is in
   place.
7. Add telemetry for root counts, retained versions, update size, and publish
   retries.
8. Delete mutating APIs or mark them private. Leaving both update styles public
   invites split-brain state.

The migration should start at a boundary, not in the middle of an arbitrary
helper. A boundary gives the team a clear rule: values crossing this line are
snapshots. Inside the boundary, code can still use mutable locals where they
are private. Outside the boundary, callers receive roots and transitions. This
keeps the first change reviewable. It also lets tests focus on one promise:
after a transition, the old value still reads the old data.

For nested state, introduce narrow transition functions before introducing
generic update machinery. A function named `renameColumn` or `grantPermission`
is easier to audit than a path update that accepts any string path. Once the
domain transitions are visible, a lens, optic, or update helper can remove
repeated structural code. Reversing that order often creates a powerful generic
setter before the team has decided which updates are legal.

For concurrency, migrate the value and the owner reference separately. First
make the value persistent under one writer. Then replace the owner publication
with compare-and-swap, a transaction, or a message-loop handoff if more than
one writer exists. Treating persistence as a replacement for write
coordination is a common mistake. It protects old roots. It does not choose the
winning new root.

Refactorings that often apply are Replace Temp with Query when deriving values
from snapshots, Encapsulate Collection when hiding a mutable collection behind
a persistent API, and Replace Data Value with Object when a raw map needs a
named value type. Engineering judgement. The named refactoring depends on the
host language and the repository's refactoring catalog.

To remove the pattern when it stops earning its cost:

1. Prove that old versions are not observed. Search for undo stacks, caches,
   closures, async tasks, and equality checks that depend on root identity.
2. Replace persistent updates behind the same transition API with a mutable
   builder or mutable collection. Keep the public API returning values until
   callers are migrated.
3. Collapse the owner reference and value if there is only one owner and no
   snapshot boundary.
4. Remove retention telemetry after memory and correctness tests pass.
5. Keep immutability at module boundaries if callers still benefit from stable
   values.

The safest path out is not to expose mutation everywhere. It is to localize
mutation where profiling shows it matters and keep value boundaries around it.

One exit path is a hybrid. Keep persistent roots for public snapshots, but store
large internal payloads in immutable chunks or external blobs. The root then
changes by replacing chunk references, while the heavy data is managed by a
storage layer tuned for scans, compression, or deletion. Engineering judgement.
This hybrid is often better than forcing all bytes into a general-purpose
persistent map.

## 15. Testing and verification

Engineering judgement. Testing should verify the version contract, not only the
new value.

- **Old-version preservation tests.** Hold root A, derive root B, then assert
  root A still reads the old value and root B reads the new value.
- **Structural sharing tests.** When the implementation exposes node identity
  for tests, assert unchanged subtrees are shared and changed paths are not. Do
  not expose this in public APIs unless the library contract includes it.
- **Property tests.** For maps and sets, compare results with a simple mutable
  model after each operation. For vectors, compare indexing, length, append,
  update, slice, and iteration with a plain array model.
- **Persistence depth tests.** Update from an old root, not only the newest
  root, when the structure claims full persistence.
- **Concurrency tests.** Put the persistent value behind the intended owner
  reference and test concurrent publish, retry, and conflict behavior. The
  collection being persistent does not make root publication atomic.
- **Mutation leak tests.** Insert a mutable element, mutate it, and decide
  whether the API forbids that element type, copies it, freezes it, or documents
  the hazard.
- **Performance tests.** Measure single updates, bulk construction, iteration,
  lookup, retained versions, and garbage collection. Compare against named
  alternatives from dimension 12 rather than against no baseline.
- **Serialization tests.** If roots cross process boundaries, verify that the
  serialized form preserves logical value and does not accidentally serialize
  shared nodes in a way that explodes size.

For a collection-library implementation, add invariant tests for internal node
shape. A vector trie should maintain its width and depth rules. A balanced tree
should maintain ordering and balance. A HAMT should preserve lookup behavior
under collisions. These tests are different from application tests. They belong
near the implementation, and they should run against generated operation
sequences.

For application use, add regression tests around old bugs. If a view once
missed an update because a nested object was mutated, write a test that fails
when the root identity is reused after a logical change. If memory once grew
because old roots were retained, write a test or integration check that bounds
history length. The pattern's promise is simple enough that tests should encode
the promise directly.

Test doubles are rarely needed for the data structure itself. A fake owner
reference can help test retry behavior, and a reference mutable model can help
property tests. The central assertion is simple: updating one version must not
change another version.

## 16. Observability signals

Engineering judgement. A healthy persistent-data-structure deployment is
visible as a stable relation between updates, retained roots, memory, and
latency.

Measure these signals.

- **Current root version.** A monotonically increasing number, content hash, or
  generation id helps connect logs to snapshots.
- **Retained root count.** Track roots held by undo stacks, caches, subscribers,
  snapshots, and in-flight requests.
- **Update operation counts.** Count inserts, deletes, updates, appends, slices,
  and bulk builds separately because they stress different paths.
- **Nodes allocated per update.** A sudden rise can mean a batch path lost its
  transient or builder mode.
- **Shared-node ratio.** In libraries that can expose it, track how much of a
  new root reuses old structure.
- **Publish retry count.** Owner references using compare-and-swap should expose
  retry rates. High retry rates indicate writer contention, not a collection
  bug.
- **Old-root age.** Long-lived roots explain retained memory. Track maximum and
  percentile age.
- **Garbage collection pressure.** Path copying creates short-lived objects.
  Track allocation rate and pause time.
- **Fallback conversions.** Count conversions to mutable arrays, JSON, database
  rows, or foreign-library objects, because those often dominate cost.

A healthy dashboard shows bounded retained roots, stable update latency,
predictable allocation per operation, and low publish retry rates. A failing
dashboard shows root counts growing without bound, old-root age rising, batch
updates allocating like repeated single updates, or conversion cost dwarfing
collection work.

Logs should avoid dumping whole structures. Log root ids, operation type,
logical size, changed-key counts, publish outcome, and elapsed time. Traces
should place root publication and bulk build spans around the owner reference,
not around every small node allocation.

## 17. Security and privacy implications

Engineering judgement. The pattern changes data lifetime and aliasing. It does
not encrypt data, authenticate callers, or enforce authorization by itself.

Positive security effects:

- Stable snapshots reduce time-of-check to time-of-use bugs inside a request
  because validation and execution can refer to the same root.
- Read-only sharing narrows accidental write authority. A component that has a
  root cannot mutate another component's root.
- Audit and incident analysis are easier when version roots can be retained and
  compared deliberately.
- Content-addressed roots, when used, can detect accidental corruption of stored
  structure. Git documents object names as hashes of object content and type
  (https://git-scm.com/docs/gitdatamodel.html, verified 2026-08-02).

Security risks:

- Old roots can retain old secrets, deleted personal data, revoked tokens,
  session material, or regulated records. This is the main privacy hazard.
- Structural sharing can make physical erasure harder. Wiping one visible
  version does not wipe bytes shared with another version.
- Snapshot retention policies can conflict with data deletion duties. Treat
  retained roots as records with retention rules.
- Mutable elements can bypass the apparent read-only boundary and create
  confused authorization decisions.
- Hash-trie maps depend on hash behavior. For untrusted keys, use a library
  with collision defenses or use ordered structures with well-understood
  comparison costs.
- Serialization can reveal sharing structure, content hashes, or historical
  paths if exported carelessly.

Practical controls:

- Do not store raw secrets in long-lived persistent structures. Store handles or
  encrypted references with independent lifetime control.
- Bound history by count, age, or domain rule.
- Add deletion tests that prove old roots are gone when policy says they must
  be gone.
- Keep owner references behind authorization checks. A persistent value prevents
  in-place mutation, not unauthorized replacement of the current root.
- Document whether element values must be immutable and reject known mutable
  types where the language permits that.

## Code examples

Python. Persistent binary search tree using path copying.

```python
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class Node:
    key: str
    value: int
    left: "Node | None" = None
    right: "Node | None" = None


def get(node: Node | None, key: str) -> int | None:
    while node is not None:
        if key == node.key:
            return node.value
        node = node.left if key < node.key else node.right
    return None


def put(node: Node | None, key: str, value: int) -> Node:
    if node is None:
        return Node(key, value)
    if key == node.key:
        return Node(key, value, node.left, node.right)
    if key < node.key:
        return Node(node.key, node.value, put(node.left, key, value), node.right)
    return Node(node.key, node.value, node.left, put(node.right, key, value))


root1 = put(None, "b", 2)
root2 = put(root1, "a", 1)
root3 = put(root2, "b", 20)

assert get(root1, "b") == 2
assert get(root3, "b") == 20
assert root2.left is root3.left
print("python persistent tree ok")
```

Go. Persistent stack with shared tails.

```go
package main

import "fmt"

type Stack[T any] struct {
	head *node[T]
	size int
}

type node[T any] struct {
	value T
	next  *node[T]
}

func (s Stack[T]) Push(value T) Stack[T] {
	return Stack[T]{head: &node[T]{value: value, next: s.head}, size: s.size + 1}
}

func (s Stack[T]) Pop() (T, Stack[T], bool) {
	if s.head == nil {
		var zero T
		return zero, s, false
	}
	return s.head.value, Stack[T]{head: s.head.next, size: s.size - 1}, true
}

func main() {
	empty := Stack[int]{}
	one := empty.Push(1)
	two := one.Push(2)
	top, rest, ok := two.Pop()
	if !ok || top != 2 || rest.size != 1 || one.size != 1 {
		panic("bad persistent stack")
	}
	fmt.Println("go persistent stack ok")
}
```

Rust. Persistent stack with reference-counted shared tails.

```rust
use std::rc::Rc;

#[derive(Clone)]
struct Stack<T> {
    head: Option<Rc<Node<T>>>,
}

struct Node<T> {
    value: T,
    next: Option<Rc<Node<T>>>,
}

impl<T: Clone> Stack<T> {
    fn new() -> Self {
        Self { head: None }
    }

    fn push(&self, value: T) -> Self {
        Self {
            head: Some(Rc::new(Node {
                value,
                next: self.head.clone(),
            })),
        }
    }

    fn pop(&self) -> Option<(T, Self)> {
        self.head.as_ref().map(|node| {
            (
                node.value.clone(),
                Self {
                    head: node.next.clone(),
                },
            )
        })
    }
}

fn main() {
    let empty = Stack::new();
    let one = empty.push(1);
    let two = one.push(2);
    let (top, rest) = two.pop().unwrap();
    assert_eq!(top, 2);
    assert!(one.pop().is_some());
    assert_eq!(rest.pop().unwrap().0, 1);
    println!("rust persistent stack ok");
}
```

These examples use small structures to make the sharing visible. Production
vectors and maps use wider nodes, balancing, collision handling, and batched
editing APIs.

## 18. References

- James R. Driscoll, Neil Sarnak, Daniel D. Sleator, Robert E. Tarjan, "Making
  Data Structures Persistent", *Journal of Computer and System Sciences*,
  volume 38, issue 1, 1989, pages 86-124.
  https://dblp.org/rec/journals/jcss/DriscollSST89, verified 2026-08-02.
- CRC Press LLC, "persistent data structure", in Paul E. Black, editor,
  *Dictionary of Algorithms and Data Structures*, NIST-hosted page.
  https://xlinux.nist.gov/dads/HTML/persistentDataStructure.html, verified
  2026-08-02.
- Chris Okasaki, *Purely Functional Data Structures*, Cambridge University
  Press, 1998, chapters 1 through 3. Cambridge Core contents page:
  https://www.cambridge.org/core/books/purely-functional-data-structures/persistence/BEB36D6BF24898A7CA3A188DA5C35ED1,
  verified 2026-08-02.
- Phil Bagwell, "Ideal Hash Trees", 2001.
  https://www.researchgate.net/publication/2378571_Ideal_Hash_Trees,
  verified 2026-08-02.
- Clojure Reference, "Data Structures".
  https://clojure.org/reference/data_structures, verified 2026-08-02.
- Clojure Reference, "Transient Data Structures".
  https://clojure.org/reference/transients, verified 2026-08-02.
- Clojure Reference, "Atoms". https://clojure.org/reference/atoms,
  verified 2026-08-02.
- Clojure Reference, "Refs and Transactions".
  https://clojure.org/reference/refs, verified 2026-08-02.
- Scala Documentation, "Concrete Immutable Collection Classes".
  https://docs.scala-lang.org/overviews/collections-2.13/concrete-immutable-collection-classes.html,
  verified 2026-08-02.
- Scala API, `scala.collection.immutable.Vector`.
  https://www.scala-lang.org/api/current/scala/collection/immutable/Vector.html,
  verified 2026-08-02.
- Immutable.js README, "Immutable collections for JavaScript".
  https://github.com/immutable-js/immutable-js, verified 2026-08-02.
- Vavr User Guide, version 0.11.0. https://docs.vavr.io/, verified
  2026-08-02.
- Redux FAQ, "Immutable Data". https://redux.js.org/faq/immutable-data,
  verified 2026-08-02.
- Git documentation, `gitdatamodel`. https://git-scm.com/docs/gitdatamodel.html,
  verified 2026-08-02.
- Git Book, "Git Internals. Git Objects".
  https://git-scm.com/book/en/v2/Git-Internals-Git-Objects.html, verified
  2026-08-02.
- Rust crate documentation, `im_rc`. https://docs.rs/im-rc, verified
  2026-08-02.
