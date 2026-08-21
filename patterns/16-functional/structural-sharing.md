---
name: Structural Sharing
slug: structural-sharing
family: 16-functional
category: Data and State
aliases: [Path Copying, Node Sharing, Shared Representation]
first_described: "Okasaki 1998, persistence through copying and sharing"
maturity: canonical
related: [persistent-data-structures, immutability, copy-on-write, lens, memoization]
incompatible_with: [shared-mutable-state, destructive-update, object-pooling]
verified: 2026-08-02
---

# Structural Sharing

## 1. Name, aliases, and lineage

The canonical name is Structural Sharing. In software design it means that a
new value reuses unchanged representation from an earlier value. An update does
not duplicate the whole aggregate. It copies the nodes on the edited path and
points the rest of the new aggregate at nodes that the old aggregate still owns.
Chris Okasaki describes this copying and sharing rule in *Purely Functional Data
Structures*, Cambridge University Press, 1998, chapter 2, "Persistence", pages
7-16. Cambridge University Press summarizes chapter 2 as update by copying
affected nodes while unchanged nodes are shared between versions
(https://www.cambridge.org/core/books/abs/purely-functional-data-structures/persistence/BEB36D6BF24898A7CA3A188DA5C35ED1,
verified 2026-08-02).

Common aliases are **path copying**, **node sharing**, **representation
sharing**, and **shared tails**. Path copying is the algorithmic name. A tree
update allocates each node from the root to the edited leaf and links untouched
children from the old tree. Shared tails is the list name. Prepending to a list
allocates one head node and reuses the old list as the tail. Representation
sharing is the broader systems name, used when two values share storage without
promising that the public API is a purely functional collection.

The lineage runs through persistent data structures. Driscoll, Sarnak, Sleator,
and Tarjan gave the classic definition of persistence in "Making Data
Structures Persistent", *Journal of Computer and System Sciences*, volume 38,
issue 1, 1989, pages 86-124. ScienceDirect lists the paper and its abstract
says a persistent structure allows access to old and new versions at any time
(https://www.sciencedirect.com/science/article/pii/0022000089900342, verified
2026-08-02). Okasaki then gave the functional programming treatment for lists,
trees, queues, heaps, and related structures in *Purely Functional Data
Structures*, 1998, chapters 2 through 6, with chapter 2 centered on persistence.

Modern production use made the term common outside research. Clojure documents
its collections as immutable and persistent, with modified versions made through
structural sharing (https://clojure.org/reference/data_structures, verified
2026-08-02). Immutable.js says its JavaScript collections use structural sharing
through hash map tries and vector tries
(https://github.com/immutable-js/immutable-js, verified 2026-08-02). Immer says
unchanged data produced by `produce` is structurally shared with the base state
(https://immerjs.github.io/immer/produce/, verified 2026-08-02).

This entry treats Structural Sharing as the implementation pattern beneath
persistent data structures, immutable state reducers, undo stacks, snapshotting
indexes, and content-addressed trees. Persistent Data Structures is the larger
pattern. Structural Sharing is the storage move that makes many persistent
structures practical.

## 2. Problem and context

A program wants old and new versions of a large value at the same time. Copying
the entire value on every edit is easy to reason about but expensive. Mutating
the value in place is cheap but changes what every existing reference can see.
Structural Sharing is the middle path. The edited version is a new value, but
most of its memory points at unchanged pieces of the old value.

The problem appears whenever a value has both size and history. A UI state tree
needs a previous value for change detection, undo, or rendering comparison. A
compiler wants a parsed syntax tree and a rewritten syntax tree. A routing
table needs readers to keep using snapshot `v17` while a control plane publishes
snapshot `v18`. A version-control system wants one commit to reuse files and
directories that did not change from its parent. Git documentation says Git
objects do not change after creation and that a commit changing 2 files in a
repository with 1000 files creates 2 new blobs while reusing previous blob IDs
for the other 998 files (https://git-scm.com/docs/gitdatamodel, verified
2026-08-02).

Without this pattern, teams usually choose between two bad local optimizations.
One team copies the whole aggregate because it is safe. That keeps ownership
clear, yet time and memory grow with total size rather than edit size. Another
team mutates in place because it is fast. That works until an old snapshot is
observed after the write, a memoized selector misses a change, or a concurrent
reader sees a half-updated aggregate. The defect is a mismatch between the
semantic model, which has versions, and the storage model, which has one body.

Structural Sharing fits when edits are small relative to the aggregate and when
old versions still have meaning. A single map key changes. One row is appended.
One leaf in a tree is replaced. In those cases the pattern pays by allocating
only the edited path, leaving the rest of the graph shared. Okasaki's chapter 2
uses lists and binary search trees to explain this rule for simple structures
(https://www.cambridge.org/core/books/abs/purely-functional-data-structures/persistence/BEB36D6BF24898A7CA3A188DA5C35ED1,
verified 2026-08-02). Scala's immutable `Vector` documentation describes a
production vector as an immutable tree with width 32 and O(log n) updates
(https://www.scala-lang.org/api/current/scala/collection/immutable/Vector.html,
verified 2026-08-02).

The pattern does not remove allocation. It changes which allocation happens.
The edited path is new. The unchanged branches are reused. That is why it is
most useful for wide or shallow trees, hash array mapped tries, ropes, syntax
trees, document models, immutable UI stores, and file trees. It is less useful
for dense numeric arrays where most operations rewrite many cells.

## 3. Forces

Engineering judgement. The sources establish named systems and data structure
properties. The weighting below is design judgement about consequences in real
code.

- **Latency.** Favoured for small edits to large values because update cost
  follows edited path length rather than total aggregate size. Sacrificed for
  hot linear memory access because extra pointers can hurt cache locality.
- **Memory.** Favoured when many versions differ by a few nodes. Sacrificed
  when long-lived old roots retain large shared subgraphs that would otherwise
  be reclaimed.
- **Consistency.** Favoured. A reference to an old version keeps its meaning
  after a new version exists.
- **Coupling.** Favoured at ownership boundaries. A callee receiving a shared
  immutable value cannot mutate the caller's snapshot.
- **Operability.** Mixed. Version roots are easy to count and label, yet leaks
  can hide behind retained roots that keep whole subgraphs alive.
- **Cost.** Mixed. The pattern reduces full-copy cost but adds implementation
  cost, allocator pressure, and sometimes a library dependency.
- **Team topology.** Favoured when platform teams publish shared immutable
  state APIs and feature teams author local transitions. Sacrificed when teams
  lack a shared rule for which nodes may be shared and which nodes must be
  copied.
- **Cognitive load.** Sacrificed. Readers must understand identity at two
  levels: logical value equality and physical object identity.
- **Debuggability.** Mixed. Old versions are available for comparison, yet a
  debugger can show two values pointing to the same internal object and make
  new readers suspect mutation.
- **Security and privacy.** Mixed. Shared immutable snapshots reduce accidental
  writes across trust boundaries, but retained roots can keep sensitive data in
  memory longer than expected.

The pattern favours versioned reasoning and local edits. It sacrifices simple
memory shape and, in some runtimes, predictable locality.

## 4. Applicability and non-applicability

Reach for Structural Sharing when these conditions hold.

- A large value has multiple live versions, such as undo history, snapshots,
  speculative transforms, branchable editor state, or read-copy-update style
  publishing.
- Most updates touch a small path or a small set of leaves.
- Values cross module, thread, or callback boundaries and the receiver should
  not gain mutation authority over the sender's version.
- Equality, memoization, or render skipping can benefit from unchanged branches
  preserving reference identity. Immer demonstrates this in its `produce`
  example by keeping an unchanged item as the same object reference
  (https://immerjs.github.io/immer/produce/, verified 2026-08-02).
- A domain already has a tree, trie, graph, or directory-like shape, and edits
  can be localized.
- Full copies are too expensive but in-place mutation would make older versions
  invalid.
- A system must publish a new root atomically while readers keep the old root
  until they finish.

Non-applicability. Do not reach for Structural Sharing in these cases.

- **The value is small.** A whole copy of a dozen fields is easier to read than
  a custom shared node graph.
- **Most updates rewrite most of the aggregate.** A numerical simulation step
  that touches every cell pays allocation and pointer overhead without much
  reuse. Use arrays, buffers, or double buffering.
- **The structure contains cycles or many aliases.** Tree-style sharing assumes
  clear ownership paths. Immer explicitly assumes a unidirectional tree and
  rejects cycles or multiple paths to one object
  (https://immerjs.github.io/immer/pitfalls/, verified 2026-08-02).
- **The shared nodes are mutable.** Sharing a mutable child between old and new
  versions makes the old version false as soon as the child changes. Freeze,
  copy, or make the child private.
- **Object identity is the domain contract.** If clients rely on identity rather
  than value, replacing path nodes changes observable behaviour.
- **The runtime punishes pointer-rich data.** Some low-level workloads need
  contiguous arrays for vectorization, prefetching, or GPU transfer.
- **The team cannot maintain representation invariants.** A bespoke HAMT,
  radix tree, or rope with weak tests is riskier than a full copy.
- **Old roots may retain regulated data.** If retention policy requires prompt
  removal of a value from memory, shared history can work against that policy.
- **The collection is built once and discarded.** Use a mutable builder and
  freeze or publish the final value.
- **The update is naturally a log event.** Event Sourcing may be clearer when
  the business artifact is the event history rather than materialized versions.

## 5. Structure

The pattern has seven participants.

- **Version Root.** The public handle to one logical version. It might be a
  list head, a tree root, a map root, a document root, or a commit ID.
- **Shared Node.** An immutable internal node reachable from one or more version
  roots. Once shared, it must not be edited in place.
- **Edited Path.** The chain of nodes from the version root to the changed
  leaf. These nodes are copied for the new version.
- **Changed Leaf.** The value, file, map entry, array chunk, or syntax node that
  differs in the new version.
- **Unchanged Branch.** A subtree or chunk that is reachable from both old and
  new roots.
- **Update Operation.** The function that computes the edited path, allocates
  replacement nodes, and returns the new root.
- **Ownership Boundary.** The rule that prevents mutation of shared nodes. It
  can be a type system, freezing, convention plus tests, content addressing, or
  private constructors.

Relationships. The old version root points at a graph of nodes. The update
operation walks from that root to the target. At each level it allocates a new
node that contains one changed child pointer and several reused child pointers.
The new root points at the top copied node. The old root still points at the old
top node. Both roots can reach the unchanged branches.

The boundary matters more than the data structure. A shared immutable node is
safe. A shared mutable node is a time bomb. In languages with plain mutable
objects, libraries such as Immer create drafts and finalize new immutable state;
the official docs say the base state remains untouched while the next state
reflects draft changes (https://immerjs.github.io/immer/produce/, verified
2026-08-02). In Git, the boundary is content addressing and immutable objects;
Git documentation says objects never change after creation
(https://git-scm.com/docs/gitdatamodel, verified 2026-08-02).

## 6. ASCII structure diagram

```text
Before update at key "b"

                 old root R1
                     |
               +-----+-----+
               | node A    |
               | a | b | c |
               +---+---+---+
                 |   |   |
                 |   |   +----------+
                 |   |              |
              leaf a leaf b      subtree c

After update at key "b"

                 old root R1             new root R2
                     |                       |
               +-----+-----+           +-----+-----+
               | node A    |           | node A'   |
               | a | b | c |           | a | b | c |
               +---+---+---+           +---+---+---+
                 |   |   |               |   |   |
                 |   |   +---------------+   |   |
                 |   |                       |   |
                 |   +---- leaf b old        |   |
                 |                           |   |
                 +---------------------------+   |
                                                 |
                                      leaf b new |
                                                 |
                     subtree c <-----------------+

Only node A' and leaf b new are allocated. Leaf a and subtree c are shared.
```

## 7. Dynamics

At runtime the pattern is a path-copying transaction. The operation reads the
old root, walks to the edit point, allocates a replacement leaf, allocates
parents back toward the root, and publishes the new root. The old root is never
changed.

```text
Client        Update Operation       Allocator        Old Graph       New Graph
  |                  |                    |               |              |
  | update(R1, b, X) |                    |               |              |
  |----------------->|                    |               |              |
  |                  | read root          |               |              |
  |                  |-----------------------------------> |              |
  |                  | walk path a/b/c    |               |              |
  |                  |-----------------------------------> |              |
  |                  | allocate leaf X    |               |              |
  |                  |------------------->|               |              |
  |                  |<-------------------|               |              |
  |                  | allocate node A'   |               |              |
  |                  |------------------->|               |              |
  |                  |<-------------------|               |              |
  |                  | link A'.a to old leaf a            |              |
  |                  | link A'.b to leaf X                |------------->|
  |                  | link A'.c to old subtree c         |              |
  |                  | return R2          |               |              |
  |<-----------------|                    |               |              |
  |                  |                    |               |              |

R1 remains valid. R2 is a new version. Shared branches must be immutable.
```

In a balanced binary tree, the number of copied nodes follows tree height. In a
wide vector trie or hash array mapped trie, the copied path is usually short
because each node branches widely. Clojure documents vector lookup in log32N
hops and hash map lookup in log32N hops for hash maps
(https://clojure.org/reference/data_structures, verified 2026-08-02). Scala's
immutable `Vector` uses width 32 and lists O(log n) update
(https://www.scala-lang.org/api/current/scala/collection/immutable/Vector.html,
verified 2026-08-02).

Two dynamic events decide whether the pattern stays cheap.

First, old root lifetime determines retention. If an undo stack keeps 100 roots,
then every node reachable from any root stays alive. That is the point, but it
must be budgeted. Second, batch size determines allocation shape. Repeating
single persistent updates can allocate one path per edit. Clojure transients are
an official optimization for local multi-step construction. The transient docs
say transient structures are created from persistent structures in O(1), share
structure with their source, and return to persistent form in O(1)
(https://clojure.org/reference/transients, verified 2026-08-02).

## 8. Implementation variants

**Shared-tail list.** Prepend allocates one node whose tail is the prior list.
All prior nodes are shared. This variant is tiny, predictable, and excellent for
stacks and logs read from the front. It is poor for random access and appending.

```python
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class Node:
    value: int
    tail: Optional["Node"] = None

def cons(value: int, tail: Optional[Node]) -> Node:
    return Node(value, tail)

base = cons(2, cons(3, None))
newer = cons(1, base)

assert newer.tail is base
assert base.value == 2
print("python shared tail ok")
```

**Path-copied binary tree.** A search tree update copies each node on the search
path and reuses untouched subtrees. It is easy to teach and useful for syntax
trees, interval trees, and small ordered maps. Its cost follows tree height, so
balance matters.

```typescript
type Tree =
  | null
  | Readonly<{ key: string; value: number; left: Tree; right: Tree }>;

function set(tree: Tree, key: string, value: number): Tree {
  if (tree === null) return { key, value, left: null, right: null };
  if (key === tree.key) return { ...tree, value };
  if (key < tree.key) return { ...tree, left: set(tree.left, key, value) };
  return { ...tree, right: set(tree.right, key, value) };
}

const base = set(set(set(null, "b", 2), "a", 1), "c", 3);
const next = set(base, "a", 10);

if (base === null || next === null) throw new Error("missing tree");
if (base.right !== next.right) throw new Error("right branch was copied");
if (base.left === next.left) throw new Error("edited branch was shared");
console.log("typescript path copy ok");
```

**Chunked vector trie.** Index bits choose a child at each level. Updating one
index copies the arrays along the path and reuses all sibling arrays. This is
the family behind many immutable vectors. Scala documents immutable `Vector` as
width 32 and O(log n) for updates
(https://www.scala-lang.org/api/current/scala/collection/immutable/Vector.html,
verified 2026-08-02).

**Hash array mapped trie.** Hash bits choose a child at each level. Updating one
key copies a short path, reuses other child arrays, and handles collisions in a
collision node or bucket. Immutable.js cites hash map tries as part of its
structural sharing implementation
(https://github.com/immutable-js/immutable-js, verified 2026-08-02).

**Proxy draft with finalization.** A library gives the caller a mutable-looking
draft, records writes, and then builds the next immutable value with shared
unchanged branches. Immer uses this shape. Its docs state that the base state is
untouched, the next state reflects draft changes, and unchanged data is
structurally shared (https://immerjs.github.io/immer/produce/, verified
2026-08-02). This variant gives application authors concise updates but moves
representation rules into the library.

**Content-addressed tree.** A node is named by a digest of its content, so an
unchanged file or directory can be pointed to from many roots. Git is the common
production example. Git documentation says objects never change after creation
and that unchanged file blobs can be reused across commits
(https://git-scm.com/docs/gitdatamodel, verified 2026-08-02).

**Copy-on-write buffer.** A handle shares storage until a write happens, then
copies the storage before editing. This is related but different. Copy-on-write
can hide mutation behind a value-like API. Structural Sharing usually exposes
new roots and old roots at the same time. The copy-on-write entry covers that
variant in more detail.

**Mutable builder or transient.** Batch construction uses temporary local
mutation and then publishes an immutable shared result. Clojure transients are
the named production form and are documented as thread-isolated, O(1) to create
from persistent values, and O(1) to convert back
(https://clojure.org/reference/transients, verified 2026-08-02).

```go
package main

import "fmt"

type Node struct {
	Key   string
	Val   int
	Left  *Node
	Right *Node
}

func Set(n *Node, key string, val int) *Node {
	if n == nil {
		return &Node{Key: key, Val: val}
	}
	if key == n.Key {
		return &Node{Key: key, Val: val, Left: n.Left, Right: n.Right}
	}
	if key < n.Key {
		return &Node{Key: n.Key, Val: n.Val, Left: Set(n.Left, key, val), Right: n.Right}
	}
	return &Node{Key: n.Key, Val: n.Val, Left: n.Left, Right: Set(n.Right, key, val)}
}

func main() {
	base := Set(Set(Set(nil, "b", 2), "a", 1), "c", 3)
	next := Set(base, "a", 10)
	if base.Right != next.Right {
		panic("right branch was copied")
	}
	if base.Left == next.Left {
		panic("edited branch was shared")
	}
	fmt.Println("go path copy ok")
}
```

## 9. Known production uses

**Clojure persistent collections.** Clojure documents its collections as
immutable and persistent and says modified versions are created through
structural sharing. The same reference lists vectors and hash maps with log32N
access properties (https://clojure.org/reference/data_structures, verified
2026-08-02). This is direct production use in a language runtime and standard
library.

**Immutable.js.** Immutable.js provides persistent immutable collections for
JavaScript, including `List`, `Map`, `Set`, and `Record`. Its README says these
collections use structural sharing through hash map tries and vector tries
(https://github.com/immutable-js/immutable-js, verified 2026-08-02). This is a
library-level use for application state, often paired with React and Flux-style
data flow.

**Immer.** Immer's `produce` API accepts a base state and a draft mutation
recipe, then returns the next immutable state. Its docs state that the base
state is left untouched and that unchanged data is structurally shared
(https://immerjs.github.io/immer/produce/, verified 2026-08-02). Its pitfalls
page also documents the tree assumption behind the model
(https://immerjs.github.io/immer/pitfalls/, verified 2026-08-02).

**Scala immutable Vector.** Scala documents `scala.collection.immutable.Vector`
as an immutable data structure with O(log n) random access updates, implemented
with radix-balanced finger trees of width 32
(https://www.scala-lang.org/api/current/scala/collection/immutable/Vector.html,
verified 2026-08-02). Structural sharing is the natural implementation reason
an immutable vector can update without copying all elements. That last sentence
is engineering judgement based on the documented tree shape.

**Git object database.** Git documentation says Git objects never change after
creation, commits point to tree objects, trees point to blobs or subtrees, and a
commit that changes only 2 files in a repository with 1000 files can reuse the
previous blob IDs for the other 998 files
(https://git-scm.com/docs/gitdatamodel, verified 2026-08-02). This is
structural sharing at the content-addressed repository level rather than an
in-memory collection API.

## 10. Consequences

Engineering judgement. The consequences below follow from the storage shape and
from the cited production APIs, but their weight depends on workload and team
practice.

Positive.

- Old versions stay valid. A caller can keep a root and know it will not change
  through a later update.
- Update cost tracks edit shape rather than total aggregate size when edits are
  local.
- Equality and memoization can use reference identity on unchanged branches.
- Undo, redo, speculative transforms, branch comparison, and snapshot readers
  become cheaper to express.
- Concurrency design is simpler when readers hold immutable roots and writers
  publish new roots.
- Serialization and storage can avoid writing unchanged content when nodes are
  named or cached.
- API boundaries become clearer because passing a value does not pass mutation
  authority.

Negative.

- Pointer-heavy structures may have worse cache locality than contiguous arrays.
- Old roots can retain large subgraphs and surprise memory owners.
- Allocation frequency increases compared with in-place mutation.
- Identity becomes subtle because two logical values may share physical nodes.
- Custom implementations need invariants for balance, hash collisions, sharing,
  and retention.
- Deep batch updates can allocate one path per step unless a builder or
  transient variant is used.
- Mutable children break the pattern if they are shared by reference.
- Debuggers and heap dumps are harder to read because sharing is invisible in
  normal value printers.

## 11. Failure modes and misuse

Engineering judgement. These are operational failure patterns seen in designs
with shared immutable representations. They are phrased as observable triples so
they can be converted into tests, logs, and runbooks.

**Shared mutable child.** Symptom. Editing version `v2` changes what a test
observes through version `v1`, or memoized output for `v1` changes without a new
root. Cause. The update path copied parent nodes but reused a mutable child.
Fix. Make shared nodes immutable, freeze at publication, deep-copy mutable
leaves, or store mutable leaves behind private ownership.

**Root retention leak.** Symptom. Heap grows with every edit even after visible
state size stays flat. A heap profile shows old roots, undo frames, closures, or
debug logs retaining the graph. Cause. The program keeps old version roots
longer than the retention budget. Fix. Bound history, drop roots after readers
finish, avoid logging whole roots, and expose a metric for live roots.

**Batch update allocation cliff.** Symptom. Updating 10,000 keys through a loop
allocates many short-lived nodes and triggers frequent garbage collection.
Cause. Each single edit creates a new persistent path. Fix. Use a transient or
builder variant, or group edits under one draft finalization. Clojure transients
exist for this local construction case and are documented as sharing structure
with the source (https://clojure.org/reference/transients, verified
2026-08-02).

**False equality assumption.** Symptom. A render, selector, or cache misses a
real change or recomputes too much. Cause. Code treats root reference equality,
deep equality, and branch reference equality as interchangeable. Fix. Define
the equality rule at the boundary, test no-op updates, and use branch identity
only for branches the update operation promises to preserve.

**Cycle introduced into a tree API.** Symptom. A draft finalizer, serializer, or
diff tool loops, throws, or duplicates data. Cause. A caller put a graph with a
cycle or two paths to the same object into an API designed for trees. Fix.
Reject cycles at ingress or use a graph-aware persistent representation. Immer
documents a unidirectional tree requirement
(https://immerjs.github.io/immer/pitfalls/, verified 2026-08-02).

**Path-copy bug.** Symptom. An update disappears, appears under the wrong key,
or corrupts order only after a particular branch shape. Cause. The copied parent
reused the wrong child pointer or failed to rebuild one ancestor. Fix. Add
property tests that compare the persistent implementation with a simple mutable
model over random update sequences.

**Over-retained secret.** Symptom. A secret removed from current state still
appears in a heap dump or crash artifact. Cause. An old root retains the node
that held the secret. Fix. Do not store secrets in versioned structures, shorten
root lifetime, or encrypt and rotate sensitive leaf payloads outside the shared
graph.

**Unbounded node interning.** Symptom. A process with many distinct historical
values keeps growing even when no user-visible history is held. Cause. A global
cache interns nodes without eviction. Fix. Prefer local sharing through roots,
or bound the intern table with clear ownership and telemetry.

## 12. Trade-off matrix

| Force | Structural Sharing | Full Deep Copy | In-place Mutation | Copy-on-write Buffer | Event Sourcing | Database MVCC |
|---|---|---|---|---|---|---|
| Local update latency | Low to medium, path length | High, total size | Low | Low until write copy | Low append, read needs projection | Medium, storage engine dependent |
| Read locality | Medium, pointer hops | High if contiguous | High if contiguous | High until split | Projection dependent | Engine dependent |
| Memory across versions | Low when edits are small | High | Low, one version | Low until writers split | Log grows by events | Old row versions retained |
| Old version safety | Strong with immutable nodes | Strong | Weak | Strong by handle contract | Strong through event log | Strong under isolation rules |
| Cognitive load | Medium to high | Low | Low locally, high globally | Medium | High domain modelling cost | High operational cost |
| Concurrency | Good for read snapshots | Good but costly | Requires locks or ownership | Good for readers | Good for append workflows | Strong but database-bound |
| Undo and redo | Natural roots | Natural but costly | Manual inverse edits | Natural by handles | Natural by replay | Query old versions if retained |
| Equality and memoization | Strong branch identity signals | Poor, all objects new | Poor, same object changes | Mixed | Projection dependent | Query result dependent |
| Implementation cost | Medium to high | Low | Low | Medium | High | External system cost |
| Failure mode | Retained roots, mutable leaves | Copy cost | Aliasing races | Hidden copy spikes | Bad projections | Vacuum and retention pressure |

Reading of the table. Structural Sharing is strongest when the program needs
many safe snapshots and edits are narrow. Full Deep Copy is better when values
are small or clarity beats cost. In-place Mutation wins in tight loops with one
owner. Copy-on-write Buffer fits APIs that want value handles over large flat
storage. Event Sourcing fits domains where the event is the durable fact.
Database MVCC fits cross-process transactional storage, not local data
structure design.

## 13. Related and incompatible patterns

- **Persistent Data Structures.** Structural Sharing is the implementation move
  beneath many persistent structures. A persistent map or vector is the public
  abstraction; shared nodes are how it avoids whole-structure copies.
- **Immutability.** Immutability is the contract that makes sharing safe. The
  old version can share with the new version because neither version can mutate
  the shared branch.
- **Copy-on-write.** Related but not identical. Copy-on-write usually starts
  from shared mutable storage and copies on a write through one handle.
  Structural Sharing usually returns a new root and keeps old and new roots
  live.
- **Lens and optics.** Compose well. An optic describes where to update inside a
  nested value. Structural Sharing describes how the update can reuse untouched
  context.
- **Memoization.** Compose well. Shared branches preserve reference identity,
  which can make cache invalidation cheaper when the cache key is a branch
  reference.
- **Prototype.** Similar in spirit when cloning an object graph and reusing
  unchanged parts, but Prototype focuses on object creation from exemplars
  rather than versioned value updates.
- **Flyweight.** Shares common representation across many values. Flyweight
  usually shares intrinsic, stateless data. Structural Sharing shares historical
  structure between related versions.
- **Object Pooling.** Often conflicts. Reusing a node object for a different
  value breaks old roots unless ownership is proven unique. Pooled mutable nodes
  need strict linear ownership and should not be visible as shared nodes.
- **Shared Mutable State.** Actively conflicts. A shared mutable child defeats
  the guarantee that old versions keep their meaning.
- **Event Sourcing.** Can replace it. When history matters more than materialized
  snapshots, store events and rebuild projections. Structural Sharing fits when
  many materialized versions need cheap coexistence.

## 14. Refactoring path in and out

Introducing Structural Sharing into code that currently deep-copies or mutates.

1. Identify the aggregate whose old versions matter. Do not start with a helper
   function. Start with a real version boundary such as document state, compiler
   tree, routing table, or reducer state.
2. Define the root type and the operations that create new roots. Hide internal
   node constructors so callers cannot mutate shared nodes.
3. Make leaves and nodes immutable at publication. In TypeScript, use readonly
   types and runtime freezing where tests need it. In Python, use frozen data
   classes or private nodes. In Go, keep fields private or treat nodes as values
   owned by the package.
4. Replace one update path with path copying. Keep all read APIs unchanged.
5. Add tests that assert old roots still read old values and unchanged branches
   are shared where the implementation promises sharing.
6. Add memory and root-count metrics before widening usage.
7. Convert remaining update paths. For batch updates, introduce a builder or
   transient mode before performance work begins.
8. Delete old defensive deep copies after tests prove callers cannot mutate
   shared representation.

Refactoring from deep copy to sharing often uses Extract Class for internal
nodes, Encapsulate Collection for public access, and Replace Temp with Query for
derived reads. Refactoring from in-place mutation often uses Split Phase: first
compute the target path, then build and publish the new root.

Removing Structural Sharing when it stops earning its place.

1. Measure live roots, update size, allocation rate, and read latency. Removal
   should be driven by observed cost, not by discomfort with indirection.
2. If only one version is live, replace persistent updates with a mutable
   builder behind the same public API.
3. If values are small, replace shared nodes with whole-value copy and delete
   node-level invariants.
4. If the real artifact is an audit log, move history to Event Sourcing and keep
   one materialized projection.
5. If cross-process transactions are the issue, move versioning to database MVCC
   and keep local data simple.
6. Remove branch identity dependencies from caches before changing storage.
7. Keep compatibility tests for old root behaviour until the API contract is
   explicitly changed.

## 15. Testing and verification

Engineering judgement. Structural Sharing needs tests for value semantics,
sharing promises, and retention behaviour. Unit tests alone are not enough when
the representation has hidden aliasing.

Test the value contract first.

- Build a base root, make an edit, then assert the base root still returns old
  values and the new root returns new values.
- Exercise insert, replace, remove, append, and no-op updates.
- Compare every operation against a simple mutable model over generated command
  sequences. This catches lost updates and wrong child pointers.
- Test no-op updates. Decide whether they return the same root or an equal new
  root, then lock that rule in tests because memoization may rely on it.

Test sharing where it is part of the contract.

- Assert unchanged branches are the same physical object in narrow examples.
- Assert edited path nodes are different physical objects.
- Add a mutation probe in languages that allow it. Try to mutate a shared child
  through a back door and expect a failure, or keep constructors private enough
  that the probe cannot compile.
- For content-addressed storage, assert unchanged content has the same object
  identifier.

Test memory behaviour.

- Run a bounded history test that creates many versions, drops old roots, forces
  collection when the runtime allows it, and checks that retained memory falls.
- Add a stress test for batch edits. If the test shows allocation cliffs, add a
  builder or transient path.
- For concurrent readers, publish a sequence of roots while readers hold older
  roots and assert no reader observes a mixed version.

The Python, TypeScript, and Go snippets in dimension 8 were run locally for this
entry. They check both the old value contract and branch identity for a small
path-copied tree or list.

## 16. Observability signals

Engineering judgement. Structural Sharing is invisible unless telemetry names
roots, copied nodes, and retained versions.

Record these signals.

- **Live version roots.** Count roots held by undo history, active readers,
  caches, sessions, and debug tools.
- **Nodes copied per update.** A histogram makes path length visible. A sudden
  rise points to an unbalanced tree, many single edits, or a shape change.
- **Shared branch ratio.** Estimate reused nodes divided by reachable nodes in
  the new root. A falling ratio means the workload no longer edits locally.
- **Allocation bytes per update.** Track by operation name, not only globally.
- **Oldest retained root age.** This catches readers or histories that never
  release.
- **History depth.** Needed for undo stacks and snapshot readers.
- **Finalization or draft duration.** Useful for proxy-draft variants such as
  Immer-style producers.
- **Cache hit rate for branch-based memoization.** The pattern should improve
  this when updates are local.

A healthy dashboard shows stable live roots, nodes copied per update close to
expected path depth, a high shared branch ratio, and memory that drops after old
roots expire. A failing dashboard shows roots increasing without bound, copied
nodes rising with total structure size, allocation spikes during batch edits, or
old root age exceeding the retention policy.

Log sparingly. Logging whole roots is a common way to retain the graph through a
debug buffer. Prefer root IDs, version numbers, operation names, path length,
and copied-node counts. For privacy, logs should not print leaf values unless a
domain policy permits it.

## 17. Security and privacy implications

Engineering judgement. The pattern is mostly about state representation, but it
does affect authority, retention, and tamper evidence.

Positive security effects.

- Passing an immutable root across a trust boundary does not give the receiver
  write authority over the sender's version.
- Snapshot roots make time-of-check and time-of-use bugs easier to reason about
  because the checked value can be the same value later consumed.
- Content-addressed sharing can make tampering visible because a changed node
  receives a different identifier. Git's object model is based on object IDs
  derived from type and contents, according to its data model documentation
  (https://git-scm.com/docs/gitdatamodel, verified 2026-08-02).

Security risks.

- Retained roots can keep sensitive leaves alive after the current state removed
  them. Do not put passwords, tokens, or regulated payloads into long-lived
  versioned structures unless retention is approved.
- A shared mutable leaf can become an unintended write channel between old and
  new versions.
- A draft API can let external objects enter the state tree without being owned
  by the draft system. Immer documents that data from outside the base state is
  not drafted when inserted into a draft
  (https://immerjs.github.io/immer/pitfalls/, verified 2026-08-02).
- Hash trie variants depend on hash behaviour. Collision handling must be
  tested, and untrusted keys may need hash-flooding protection from the runtime
  or library.
- Interning or global node caches can cross tenant boundaries if cache keys omit
  tenant or authorization context.

Privacy guidance. Treat every version root as a retention handle. Document who
can create roots, how long they live, what leaves may appear in them, and how
they are cleared from logs and crash dumps. Where erasure is legally required,
prefer external encrypted payloads with key deletion over raw sensitive leaves
inside shared history.

## 18. References

1. Chris Okasaki, *Purely Functional Data Structures*, Cambridge University
   Press, 1998, chapter 2, "Persistence", pages 7-16. Cambridge University
   Press chapter page:
   https://www.cambridge.org/core/books/abs/purely-functional-data-structures/persistence/BEB36D6BF24898A7CA3A188DA5C35ED1,
   verified 2026-08-02.
2. James R. Driscoll, Neil Sarnak, Daniel D. Sleator, Robert E. Tarjan,
   "Making Data Structures Persistent", *Journal of Computer and System
   Sciences*, volume 38, issue 1, 1989, pages 86-124.
   https://www.sciencedirect.com/science/article/pii/0022000089900342,
   verified 2026-08-02.
3. Clojure, "Data Structures", reference documentation. Immutable persistent
   collections, structural sharing, vector and map operation notes.
   https://clojure.org/reference/data_structures, verified 2026-08-02.
4. Clojure, "Transient Data Structures", reference documentation. Transient
   creation from persistent structures, sharing, O(1) conversion, and
   thread-isolation rule. https://clojure.org/reference/transients, verified
   2026-08-02.
5. Immutable.js, project README. Persistent immutable JavaScript collections and
   structural sharing through hash map tries and vector tries.
   https://github.com/immutable-js/immutable-js, verified 2026-08-02.
6. Immer, "Using produce", documentation. Base state, draft recipe, next state,
   and structurally shared unchanged data.
   https://immerjs.github.io/immer/produce/, verified 2026-08-02.
7. Immer, "Pitfalls", documentation. Unidirectional tree requirement, external
   data not drafted, and related producer hazards.
   https://immerjs.github.io/immer/pitfalls/, verified 2026-08-02.
8. Scala standard library API, `scala.collection.immutable.Vector`.
   Immutable vector, O(log n) updates, width 32 radix-balanced finger tree.
   https://www.scala-lang.org/api/current/scala/collection/immutable/Vector.html,
   verified 2026-08-02.
9. Git, `gitdatamodel` documentation. Immutable Git objects, commit and tree
   object model, and reuse of previous blob IDs for unchanged files.
   https://git-scm.com/docs/gitdatamodel, verified 2026-08-02.
